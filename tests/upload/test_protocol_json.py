from __future__ import annotations

import pytest

from agent.screenshot_upload.canonical import canonical_bytes, canonical_equal
from agent.screenshot_upload.jsonio import StrictJSONError, loads_strict
from agent.screenshot_upload.producer import Producer

from conftest import CLIENT, PROJECT


def test_jcs_uses_utf16_key_order_and_binary64_equivalence():
    assert canonical_bytes({"\ue000": 1, "😀": 2}) == '{"😀":2,"\ue000":1}'.encode("utf-8")
    assert canonical_equal({"n": 1, "z": -0.0}, {"z": 0, "n": 1.0})
    assert not canonical_equal({"note": "é"}, {"note": "e\u0301"})


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'{"x":1e-9999}',
        b'{"x":9007199254740992}',
        b'{"x":"\\u0000"}',
        b'\xef\xbb\xbf{}',
    ],
)
def test_strict_json_rejects_ambiguous_protocol_values(raw):
    with pytest.raises(StrictJSONError):
        loads_strict(raw)


@pytest.mark.parametrize(
    "metadata",
    [
        {"device": "x" * 201},
        {"run_id": "not-a-uuid"},
        {"resolution": {"width": 2, "height": 2}},
        {"payload": "x" * 16_385},
    ],
)
def test_invalid_metadata_is_rejected_before_producer_creates_item(bound_spool, png_bytes, request_data, metadata):
    root, guard = bound_spool
    request = dict(request_data)
    request["metadata"] = metadata
    with pytest.raises(ValueError):
        Producer(root, guard).publish(
            png_bytes,
            project_id=PROJECT,
            original_filename="synthetic.png",
            request=request,
            client_upload_id=CLIENT,
        )
    assert not (root / "pending" / CLIENT).exists()
