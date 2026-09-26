"""DB-free source read and bounded subprocess framing tests."""
import hashlib
import io
import json
import struct
from uuid import uuid4

import pytest
from backend.app.workers import ocr_source as source


def _spec(tmp_path, payload=b"x"):
    key = f"objects/{uuid4()}/{uuid4()}.png"
    path = tmp_path / key
    path.parent.mkdir(parents=True)
    path.write_bytes(payload)
    return {"root": str(tmp_path), "key": key, "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest()}


@pytest.mark.parametrize("size", [1, source.MAX_SOURCE_BYTES])
def test_real_file_source_boundaries(tmp_path, size, record_property):
    payload = b"x" * size
    spec = _spec(tmp_path, payload)
    result = source.read_source(spec)
    assert result == payload
    assert hashlib.sha256(result).hexdigest() == spec["sha256"]
    record_property("observed_source_size_bytes", len(result))


@pytest.mark.parametrize("size", [0, -1, source.MAX_SOURCE_BYTES + 1, True, 1.5, None])
def test_invalid_size_rejected_before_filesystem_access(tmp_path, monkeypatch, size):
    spec = _spec(tmp_path)
    spec["size"] = size
    def forbidden(*_args, **_kwargs):
        pytest.fail("invalid size accessed filesystem")
    monkeypatch.setattr(source.Path, "lstat", forbidden)
    monkeypatch.setattr(source.Path, "open", forbidden)
    with pytest.raises(RuntimeError, match="SNAPSHOT_INTEGRITY_ERROR"):
        source.read_source(spec)


@pytest.mark.parametrize("payload", [b"xx", b"xxxx"])
def test_short_or_long_file_rejected(tmp_path, payload):
    spec = _spec(tmp_path, payload)
    spec["size"] = 3
    with pytest.raises(OSError, match="[Ss]ource size mismatch"):
        source.read_source(spec)


def test_real_file_hash_mismatch(tmp_path):
    spec = _spec(tmp_path)
    spec["sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="INPUT_HASH_MISMATCH"):
        source.read_source(spec)


@pytest.mark.parametrize("phase", ["open", "read"])
def test_source_error_closes_opened_stream(tmp_path, monkeypatch, phase):
    spec = _spec(tmp_path)
    real_open = source.Path.open
    streams = []
    class FaultStream:
        def __init__(self, stream):
            self.stream = stream
        def __enter__(self):
            return self
        def __exit__(self, *_):
            self.stream.close()
        def fileno(self):
            return self.stream.fileno()
        def read(self, _size):
            raise OSError("synthetic read failure")
    def open_fault(path, *args, **kwargs):
        if phase == "open":
            raise OSError("synthetic open failure")
        stream = real_open(path, *args, **kwargs)
        streams.append(stream)
        return FaultStream(stream)
    monkeypatch.setattr(source.Path, "open", open_fault)
    with pytest.raises(OSError, match=f"synthetic {phase} failure"):
        source.read_source(spec)
    assert all(stream.closed for stream in streams)


def test_returned_source_is_hashed_buffer(tmp_path, monkeypatch):
    spec = _spec(tmp_path, b"verified bytes")
    real_hash = hashlib.sha256
    hashed = []
    def observe(data):
        hashed.append(data)
        return real_hash(data)
    monkeypatch.setattr(source.hashlib, "sha256", observe)
    result = source.read_source(spec)
    assert len(hashed) == 1
    assert result is hashed[0]


@pytest.mark.parametrize("data", [b"\x00", struct.pack("!I", 9) + b"abc"])
def test_wire_rejects_truncated_header_or_body(data):
    with pytest.raises(EOFError):
        source.Wire(io.BytesIO(data), io.BytesIO()).recv_bytes()


def test_wire_rejects_oversize_before_body():
    reader = io.BytesIO(struct.pack("!I", source.MAX_MESSAGE_BYTES + 1) + b"not read")
    with pytest.raises(ValueError, match="RESULT_LIMIT_EXCEEDED"):
        source.Wire(reader, io.BytesIO()).recv_bytes()
    assert reader.tell() == 4


def test_wire_reads_fragmented_payload():
    class Fragmented(io.BytesIO):
        def read(self, size=-1):
            return super().read(min(size, 1))
    frame = b"D{}"
    assert source.Wire(Fragmented(struct.pack("!I", len(frame)) + frame), io.BytesIO()).recv_bytes() == frame


def test_child_rejects_authority_field_before_read(monkeypatch):
    def forbidden(_spec):
        pytest.fail("extra authority field reached source")
    monkeypatch.setattr(source, "read_source", forbidden)
    dto = dict(source={}, source_facts={}, profile_manifest={}, expected_snapshot={},
               verification_config={}, database_url="synthetic-sentinel")
    payload = b"I" + json.dumps(dto).encode()
    output = io.BytesIO()
    source.child_main(source.Wire(io.BytesIO(struct.pack("!I", len(payload)) + payload), output))
    output.seek(0)
    error = source.Wire(output, io.BytesIO()).recv_bytes()
    assert error[:1] == b"E"
    assert json.loads(error[1:])["code"] == "SNAPSHOT_INTEGRITY_ERROR"


def test_utf8_snapshot_near_8mib_uses_separate_input_envelope(monkeypatch, record_property):
    text = "한" * ((source.MAX_RESULT_BYTES - 32) // 3)
    snapshot = {"text": text}
    assert len(json.dumps(snapshot, ensure_ascii=False).encode("utf-8")) < source.MAX_RESULT_BYTES
    dto = dict(source={"test": "source gate"}, source_facts={}, profile_manifest={},
               expected_snapshot=snapshot, verification_config={})
    frame = b"I" + json.dumps(dto, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert source.MAX_MESSAGE_BYTES < len(frame) < source.MAX_INPUT_BYTES
    transport = io.BytesIO()
    source.Wire(io.BytesIO(), transport, write_limit=source.MAX_INPUT_BYTES).send_bytes(frame)
    transport.seek(0)
    entered = []
    def read_gate(spec):
        entered.append(spec)
        raise OSError("synthetic source boundary after accepted UTF8 input")
    monkeypatch.setattr(source, "read_source", read_gate)
    output = io.BytesIO()
    source.child_main(source.Wire(transport, output, read_limit=source.MAX_INPUT_BYTES))
    assert entered == [dto["source"]]
    output.seek(0)
    error = source.Wire(output, io.BytesIO()).recv_bytes()
    assert json.loads(error[1:])["code"] == "INPUT_STORAGE_UNAVAILABLE"
    record_property("utf8_input_envelope_bytes", len(frame))


def test_output_cap_not_enlarged_by_input_limit():
    assert source.MAX_RESULT_BYTES == 8 * 1024 * 1024
    allowed = b"D" + b"x" * source.MAX_RESULT_BYTES
    output = io.BytesIO()
    wire = source.Wire(io.BytesIO(), output, read_limit=source.MAX_INPUT_BYTES)
    wire.send_bytes(allowed)
    with pytest.raises(ValueError, match="RESULT_LIMIT_EXCEEDED"):
        wire.send_bytes(allowed + b"x")
    output.seek(0)
    assert source.Wire(output, io.BytesIO()).recv_bytes() == allowed


def test_wire_completes_partial_header_and_payload_writes():
    class ShortWriter(io.BytesIO):
        def write(self, data):
            return super().write(data[:2])
    output = ShortWriter()
    source.Wire(io.BytesIO(), output).send_bytes(b"Ipartial UTF8 \xed\x95\x9c")
    output.seek(0)
    assert source.Wire(output, io.BytesIO()).recv_bytes() == b"Ipartial UTF8 \xed\x95\x9c"


@pytest.mark.parametrize("write_result", [0, None])
def test_wire_nonprogressing_writer_fails_without_spinning(write_result):
    class StalledWriter:
        def write(self, _data):
            return write_result
        def flush(self):
            pytest.fail("failed write flushed incomplete frame")
    with pytest.raises(BrokenPipeError):
        source.Wire(io.BytesIO(), StalledWriter()).send_bytes(b"I{}")
