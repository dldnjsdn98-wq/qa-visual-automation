from io import BytesIO
import unicodedata
from python_multipart import MultipartParser
from python_multipart.multipart import parse_options_header
from backend.app.errors import DomainError
from .unicode import decode_json, validate_unicode


def parse_upload(content_type, body):
    media_type, options = parse_options_header(content_type)
    if media_type != b"multipart/form-data":
        raise DomainError(415, "UNSUPPORTED_MEDIA_TYPE", "Use multipart/form-data")
    if b"boundary" not in options:
        raise DomainError(400, "INVALID_MULTIPART", "Multipart boundary is required")
    parts, current, ended = [], {}, False
    def begin():
        current.clear()
        current.update(headers={}, field=bytearray(), value=bytearray(), data=bytearray())
    def header_field(data, start, end):
        current["field"].extend(data[start:end])
    def header_value(data, start, end):
        current["value"].extend(data[start:end])
    def header_end():
        key = bytes(current["field"]).lower()
        if key in current["headers"]:
            raise DomainError(400, "INVALID_MULTIPART", "Duplicate part header")
        current["headers"][key] = bytes(current["value"])
        current["field"].clear()
        current["value"].clear()
    def data_part(data, start, end):
        _, fields = parse_options_header(current["headers"].get(b"content-disposition", b""))
        maximum = 32768 if fields.get(b"name") == b"metadata" else 20_971_520
        if len(current["data"]) + end - start > maximum:
            raise DomainError(413, "UPLOAD_TOO_LARGE", "Multipart part exceeds its byte limit")
        current["data"].extend(data[start:end])
    def finish_part():
        parts.append(dict(headers=current["headers"], data=bytes(current["data"])))
        if len(parts) > 2:
            raise DomainError(field="body", reason="exactly file and metadata parts are required")
    def finish():
        nonlocal ended
        ended = True
    try:
        parser = MultipartParser(options[b"boundary"], callbacks={"on_part_begin": begin, "on_header_field": header_field, "on_header_value": header_value, "on_header_end": header_end, "on_part_data": data_part, "on_part_end": finish_part, "on_end": finish})
        for offset in range(0, len(body), 65536):
            parser.write(body[offset:offset + 65536])
        parser.finalize()
    except DomainError:
        raise
    except Exception:
        raise DomainError(400, "INVALID_MULTIPART", "Malformed multipart body") from None
    if not ended:
        raise DomainError(400, "INVALID_MULTIPART", "Incomplete multipart body")
    mapped = {}
    for part in parts:
        # The library strips legacy Windows paths; validate the unmodified
        # disposition first so invalid prefix characters cannot disappear.
        raw_disposition = part["headers"].get(b"content-disposition", b"")
        try:
            validate_unicode(raw_disposition.decode("utf-8", "strict"), "file.filename")
        except UnicodeDecodeError:
            raise DomainError(field="file.filename", reason="invalid UTF-8") from None
        disposition, fields = parse_options_header(part["headers"].get(b"content-disposition", b""))
        if disposition != b"form-data" or fields.get(b"name") not in (b"file", b"metadata"):
            raise DomainError(field="body", reason="exactly file and metadata parts are required")
        name = fields[b"name"]
        if name in mapped:
            raise DomainError(field="body", reason="duplicate multipart part")
        mapped[name] = part, fields
    if set(mapped) != {b"file", b"metadata"}:
        raise DomainError(field="body", reason="exactly file and metadata parts are required")
    file, fields = mapped[b"file"]
    try:
        filename = fields.get(b"filename", b"").decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise DomainError(field="file.filename", reason="invalid UTF-8") from None
    validate_unicode(filename, "file.filename")
    filename = filename.replace("\\", "/").split("/")[-1]
    filename = "".join(c for c in filename if unicodedata.category(c) != "Cc").strip()
    if not filename or len(filename) > 255:
        raise DomainError(field="file.filename", reason="filename must contain 1 to 255 scalars")
    raw_metadata = mapped[b"metadata"][0]["data"]
    if len(raw_metadata) > 32768:
        raise DomainError(413, "UPLOAD_TOO_LARGE", "Metadata part exceeds 32 KiB")
    if len(file["data"]) > 20_971_520:
        raise DomainError(413, "UPLOAD_TOO_LARGE", "File exceeds 20 MiB")
    return decode_json(raw_metadata, "metadata"), BytesIO(file["data"]), filename, file["headers"].get(b"content-type", b"").decode("ascii", errors="replace")
