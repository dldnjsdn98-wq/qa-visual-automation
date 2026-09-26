from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from agent.screenshot_upload.origin import BindingGuard, initialize_binding


ORIGIN = "http://127.0.0.1:8001"
PROJECT = "11111111-1111-4111-8111-111111111111"
CLIENT = "66666666-6666-4666-8666-666666666666"
BUILD = "22222222-2222-4222-8222-222222222222"
LOCALE = "33333333-3333-4333-8333-333333333333"
CATEGORY = "44444444-4444-4444-8444-444444444444"
SITUATION = "55555555-5555-4555-8555-555555555555"
SCREENSHOT = "99999999-9999-4999-8999-999999999999"
REQUEST_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def pytest_addoption(parser):
    parser.addoption(
        "--run-live-upload",
        action="store_true",
        default=False,
        help="run disposable PostgreSQL/uvicorn uploader integration tests",
    )


@pytest.fixture
def png_bytes() -> bytes:
    stream = BytesIO()
    Image.new("RGB", (2, 3), (12, 34, 56)).save(stream, format="PNG")
    return stream.getvalue()


@pytest.fixture
def request_data() -> dict:
    return {
        "build_id": BUILD,
        "locale_id": LOCALE,
        "category_id": CATEGORY,
        "situation_id": SITUATION,
        "source": "agent",
        "metadata_version": 1,
        "metadata": {"note": "한글 e\u0301", "nested": {"kept": None}},
    }


@pytest.fixture
def bound_spool(tmp_path):
    root = tmp_path / "captures"
    initialize_binding(root, ORIGIN)
    return root, BindingGuard(root, ORIGIN)
