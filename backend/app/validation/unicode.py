import json
from backend.app.errors import DomainError


def validate_unicode(value, path="body"):
    if isinstance(value, str):
        reason = "U+0000 is not allowed" if "\0" in value else (
            "unpaired Unicode surrogate is not allowed" if any(0xD800 <= ord(c) <= 0xDFFF for c in value) else None)
        if reason:
            raise DomainError(field=path, reason=reason)
    elif isinstance(value, dict):
        for key, item in value.items():
            try:
                validate_unicode(key, path)
            except DomainError as exc:
                exc.details[0]["reason"] = "object key " + exc.details[0]["reason"]
                raise
            validate_unicode(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            validate_unicode(item, f"{path}[{index}]")
    return value


def decode_json(raw, path="body"):
    try:
        decoded = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    except UnicodeDecodeError:
        raise DomainError(field=path, reason="invalid UTF-8") from None
    try:
        value = json.loads(decoded, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, RecursionError):
        raise DomainError(field=path, reason="invalid JSON") from None
    try:
        return validate_unicode(value, path)
    except RecursionError:
        raise DomainError(field=path, reason="nesting limit exceeded") from None


def decode_strict_json(raw, path="body"):
    """Decode a persistable JSON object while rejecting duplicate keys."""
    try:
        decoded = raw.decode("utf-8", "strict") if isinstance(raw, bytes) else raw
    except UnicodeDecodeError:
        raise DomainError(field=path, reason="invalid UTF-8") from None

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise DomainError(field=path, reason="duplicate object keys are not allowed")
            result[key] = value
        return result

    try:
        value = json.loads(
            decoded,
            object_pairs_hook=unique_object,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
    except DomainError:
        raise
    except (ValueError, RecursionError):
        raise DomainError(field=path, reason="invalid JSON") from None
    try:
        return validate_unicode(value, path)
    except RecursionError:
        raise DomainError(field=path, reason="nesting limit exceeded") from None
