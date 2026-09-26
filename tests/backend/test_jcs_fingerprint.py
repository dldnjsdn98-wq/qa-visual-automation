import json
from pathlib import Path

import pytest

from backend.app.errors import DomainError
from backend.app.validation.jcs import canonicalize_fingerprint, decode_agent_json, decode_upload_json


FIXTURE = Path(__file__).parent / "jcs_f23_vectors.json"


def test_f23_full_fingerprint_fixture_has_exact_bytes_and_hash():
    vector = json.loads(FIXTURE.read_text(encoding="utf-8"))
    canonical, digest = canonicalize_fingerprint(vector["fingerprint_payload"])
    assert canonical == vector["expected_canonical"].encode("utf-8")
    assert len(canonical) == 582
    assert digest == vector["expected_sha256"]


def test_f23_utf16_order_numbers_and_exact_unicode():
    value = {"\ue000": 2, "😀": 1, "n": [1, 1.0, -0.0], "c": "é", "d": "e\u0301"}
    canonical, _ = canonicalize_fingerprint(value)
    assert canonical == '{"c":"é","d":"é","n":[1,1,0],"😀":1,"":2}'.encode()


@pytest.mark.parametrize(
    "raw",
    [
        b'{"a":1,"a":2}',
        b'{"x":{"a":1,"a":2}}',
        b'{"a":1,"\\u0061":2}',
        b'NaN',
        b'Infinity',
        b'1e309',
        b'1e-4000',
        b'9007199254740992',
        b'9007199254740992.0',
        b'"\\u0000"',
        b'"\\ud800"',
    ],
)
def test_strict_agent_parser_rejects_duplicate_numeric_and_unicode_domain(raw):
    with pytest.raises(DomainError):
        decode_agent_json(raw)


def test_strict_agent_parser_preserves_equivalence_and_boundaries():
    values = [decode_agent_json(raw) for raw in (b"1", b"1.0", b"1e0")]
    assert [canonicalize_fingerprint({"v": value})[0] for value in values] == [b'{"v":1}'] * 3
    assert decode_agent_json(b"-0.0") == 0.0
    assert decode_agent_json(b"5e-324") == 5e-324
    assert decode_agent_json(b"9007199254740991") == 9007199254740991


def test_manual_keeps_phase1_last_key_behavior_but_agent_is_strict():
    assert decode_upload_json(b'{"source":"manual","metadata":{"a":1,"a":2}}')["metadata"] == {"a": 2}
    with pytest.raises(DomainError):
        decode_upload_json(b'{"source":"agent","metadata":{"a":1,"a":2}}')
