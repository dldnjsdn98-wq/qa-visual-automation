"""DB-free standalone source/OCR child. Run with python -I <this file>.

Only standard-library imports occur before the immutable input gate. This module
must never import backend configuration, models, sessions or mutation services.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import sys

MAX_SOURCE_BYTES = 20_971_520
MAX_RESULT_BYTES = 8 * 1024 * 1024
MAX_MESSAGE_BYTES = MAX_RESULT_BYTES + 1
# The input envelope includes an up-to-8MiB UTF-8 snapshot plus immutable
# profile/configuration/source metadata. It is independent of the output cap.
MAX_INPUT_BYTES = 16 * 1024 * 1024
SAFE_CODES = {
    "SOURCE_DECODE_ERROR", "ENGINE_UNAVAILABLE", "MODEL_UNAVAILABLE", "ENGINE_TIMEOUT",
    "ENGINE_OUTPUT_INVALID", "RESULT_LIMIT_EXCEEDED", "INPUT_HASH_MISMATCH",
    "PROFILE_DIGEST_MISMATCH", "SNAPSHOT_INTEGRITY_ERROR", "NORMALIZATION_ERROR",
    "ENGINE_INTERNAL_ERROR", "INPUT_STORAGE_UNAVAILABLE", "ENGINE_RESOURCE_LIMIT",
}
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_KEY = re.compile(rf"objects/{_UUID}/{_UUID}\.(?:png|jpg)")


class Wire:
    """Four-byte network-order length, then bounded opaque bytes; no pickle."""
    def __init__(self, reader, writer, *, read_limit=MAX_MESSAGE_BYTES, write_limit=MAX_MESSAGE_BYTES):
        self.reader, self.writer = reader, writer
        self.read_limit, self.write_limit = read_limit, write_limit

    def _read_exact(self, count):
        chunks = bytearray()
        while len(chunks) < count:
            chunk = self.reader.read(count - len(chunks))
            if not chunk:
                raise EOFError("Truncated child frame")
            chunks.extend(chunk)
        return bytes(chunks)

    def recv_bytes(self, maximum=None):
        length = struct.unpack("!I", self._read_exact(4))[0]
        if length > (self.read_limit if maximum is None else min(maximum, self.read_limit)):
            raise ValueError("RESULT_LIMIT_EXCEEDED")
        return self._read_exact(length)

    def send_bytes(self, frame):
        if len(frame) > self.write_limit:
            raise ValueError("RESULT_LIMIT_EXCEEDED")
        for part in (struct.pack("!I", len(frame)), frame):
            remaining = memoryview(part)
            while remaining:
                written = self.writer.write(remaining)
                if written is None or written <= 0:
                    raise BrokenPipeError("Child protocol write failed")
                remaining = remaining[written:]
        self.writer.flush()


def read_source(spec):
    size = spec["size"]
    if type(size) is not int or not 1 <= size <= MAX_SOURCE_BYTES:
        raise RuntimeError("SNAPSHOT_INTEGRITY_ERROR")
    root = Path(spec["root"])
    key = spec["key"]
    if not root.is_absolute() or not isinstance(key, str) or not _KEY.fullmatch(key):
        raise RuntimeError("SNAPSHOT_INTEGRITY_ERROR")
    path = root / key
    # Match the provider's refusal of symlinks and Windows reparse components.
    for component in (*reversed(path.parents), path):
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise OSError("Storage links are forbidden")
    with path.open("rb") as stream:
        declared = os.fstat(stream.fileno()).st_size
        source = stream.read(size + 1)
    if declared != size or len(source) != size:
        raise OSError("Source size mismatch")
    if hashlib.sha256(source).hexdigest() != spec["sha256"]:
        raise RuntimeError("INPUT_HASH_MISMATCH")
    return source


def child_main(connection, package_paths=()):
    try:
        frame = connection.recv_bytes()
        if frame[:1] != b"I":
            raise RuntimeError("ENGINE_OUTPUT_INVALID")
        dto = json.loads(frame[1:])
        if set(dto) != {"source", "source_facts", "profile_manifest", "expected_snapshot", "verification_config"}:
            raise RuntimeError("SNAPSHOT_INTEGRITY_ERROR")
        source = read_source(dto["source"])
        if (dto["source_facts"]["source_sha256"] != dto["source"]["sha256"] or
                dto["source_facts"]["size"] != len(source)):
            raise RuntimeError("SNAPSHOT_INTEGRITY_ERROR")
        # Explicit trusted code root works in both the source checkout and /app.
        # -I -S disables site discovery; only explicit trusted package paths are
        # added below. cwd/PYTHONPATH and .pth startup hooks are never used.
        for directory in reversed(package_paths):
            if not Path(directory).is_absolute():
                raise RuntimeError("ENGINE_UNAVAILABLE")
            sys.path.insert(0, directory)
        sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
        from worker.ocr import ocr_execute
        from worker.verification import verify_execute
        import rfc8785
        ocr = ocr_execute(source, dto["source_facts"], dto["profile_manifest"])
        connection.send_bytes(b"O")
        if connection.recv_bytes(1) != b"V":
            raise RuntimeError("ENGINE_OUTPUT_INVALID")
        verification = verify_execute(dto["expected_snapshot"], ocr.get("regions", []),
                                      dto["verification_config"])
        connection.send_bytes(b"D" + rfc8785.dumps({"ocr": ocr, "verification": verification}))
        # Remain alive for the parent's final effective-containment requery.
        # Production terminates/reaps the owned process rather than granting
        # another useful phase; a Q is available for protocol-only harnesses.
        if connection.recv_bytes(1) != b"Q":
            raise RuntimeError("ENGINE_OUTPUT_INVALID")
    except BaseException as exc:
        code = ("ENGINE_RESOURCE_LIMIT" if isinstance(exc, MemoryError) else
                "INPUT_STORAGE_UNAVAILABLE" if isinstance(exc, OSError) else
                getattr(exc, "code", str(exc)))
        if code not in SAFE_CODES:
            code = "ENGINE_INTERNAL_ERROR"
        try:
            connection.send_bytes(b"E" + json.dumps({"code": code}).encode("ascii"))
        except BaseException:
            pass


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-packages", action="append", default=[])
    arguments = parser.parse_args()
    if os.name == "nt":
        import msvcrt
        msvcrt.setmode(0, os.O_BINARY)
        msvcrt.setmode(1, os.O_BINARY)
    # Preserve a dedicated protocol descriptor; native printf and Python stdout
    # thereafter cannot corrupt frames or leak diagnostic/configuration strings.
    protocol = os.fdopen(os.dup(1), "wb", buffering=0)
    with open(os.devnull, "wb", buffering=0) as sink:
        os.dup2(sink.fileno(), 1)
        os.dup2(sink.fileno(), 2)
        child_main(Wire(sys.stdin.buffer, protocol, read_limit=MAX_INPUT_BYTES), tuple(arguments.site_packages))
    protocol.close()


if __name__ == "__main__":
    main()
