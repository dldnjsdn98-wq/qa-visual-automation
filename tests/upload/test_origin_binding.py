from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest

from agent.screenshot_upload.lock import ProcessLock
from agent.screenshot_upload.origin import BindingError, canonicalize_origin, initialize_binding, validate_binding
from agent.screenshot_upload.config import ConfigError, RuntimeConfig, canonical_backend_origin
from agent.screenshot_upload.producer import Producer
from agent.screenshot_upload.runtime import UploadRuntime
from agent.screenshot_upload.spool import Spool
from agent.screenshot_upload.state import AckRecord, QueueState, QueueStatus
from agent.screenshot_upload.state_store import StateStore

from conftest import CLIENT, ORIGIN, PROJECT, REQUEST_ID, SCREENSHOT


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("HTTP://LOCALHOST:80/", "http://localhost"),
        ("https://Example.COM:443", "https://example.com"),
        ("http://[0:0:0:0:0:0:0:1]:8001/", "http://[::1]:8001"),
        ("https://a-b.example:444/", "https://a-b.example:444"),
        ("http://127.0.0.1:8001", "http://127.0.0.1:8001"),
    ],
)
def test_origin_canonical_aliases_have_config_parity(raw, expected):
    assert canonicalize_origin(raw) == expected
    assert canonical_backend_origin(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        " https://host", "https://host ", "https://host/path", "https://host?", "https://host#",
        "https://user@host", "https://host%20", "http://127.1", "http://0177.0.0.1",
        "http://0x7f000001", "http://1.2.3.256", "http://[::ffff:127.0.0.1]",
        "http://0x", "http://0X",
        "http://[fe80::1%25lo0]", "https://xn--bcher-kva.example", "https://host:080",
        "https://host:0", "https://host:65536", "https://host:", "ftp://host", "https://host//",
    ],
)
def test_origin_and_config_reject_repairs_and_ambiguous_forms(raw):
    with pytest.raises(ValueError):
        canonicalize_origin(raw)
    with pytest.raises(ConfigError):
        canonical_backend_origin(raw)


_F29_ACCEPTED = [
    ("HTTP://LOCALHOST:80/", "http://localhost"),
    ("https://Example.COM:443", "https://example.com"),
    ("http://127.0.0.1:8001/", "http://127.0.0.1:8001"),
    ("http://[0:0:0:0:0:0:0:1]:8001/", "http://[::1]:8001"),
    ("http://[2001:0DB8:0:0:1:0:0:1]", "http://[2001:db8::1:0:0:1]"),
    ("http://localhost:65535", "http://localhost:65535"),
    ("https://example.com:80", "https://example.com:80"),
    ("http://[::]", "http://[::]"),
    (f"http://{'a' * 63}.com", f"http://{'a' * 63}.com"),
    (
        f"http://{'a' * 63}.{'b' * 63}.{'c' * 63}.{'d' * 61}",
        f"http://{'a' * 63}.{'b' * 63}.{'c' * 63}.{'d' * 61}",
    ),
]

_F29_REJECTED = [
    " http://host", "http://host ", "http://host\n", "http://host/path", "http://host//",
    "http://host?", "http://host#", "http://user@host", "http://host\\evil", "http://%68ost",
    "http://host:", "http://host:080", "http://host:0", "http://host:65536", "http://127.1",
    "http://0177.0.0.1", "http://2130706433", "http://0x7f000001", "http://host.",
    "http://host..com", "http://host.123", "http://host.0x10", "http://[fe80::1%25eth0]",
    "http://::1", "http://[::ffff:127.0.0.1]", "ftp://host", "http://-host",
    "http://host_1", "http://한.com", "http://xn--bcher-kva.de", "http://a-.example",
    "http://127.0.0.01", "http://256.0.0.1", "http://0X7F", "http://[host]",
    "http://[v1.abc]", "http://host:+80", f"http://{'a' * 64}.com",
    f"http://{'a' * 63}.{'b' * 63}.{'c' * 63}.{'d' * 62}",
    "http://0x", "http://0X",
]


@pytest.mark.parametrize(("raw", "expected"), _F29_ACCEPTED)
def test_f29_full_accepted_corpus_has_one_canonical_result(raw, expected):
    assert canonicalize_origin(raw) == canonical_backend_origin(raw) == expected


@pytest.mark.parametrize("raw", _F29_REJECTED)
def test_f29_full_rejected_corpus_has_matching_public_exceptions(raw):
    with pytest.raises(ValueError):
        canonicalize_origin(raw)
    with pytest.raises(ConfigError):
        canonical_backend_origin(raw)
    with pytest.raises(ConfigError):
        RuntimeConfig.create("captures", raw)


def test_runtime_config_create_uses_shared_origin_canonicalizer(tmp_path):
    config = RuntimeConfig.create(tmp_path, "HTTP://LOCALHOST:80/")
    assert config.backend_origin == "http://localhost"


def test_explicit_init_is_canonical_idempotent_and_never_rebinds(tmp_path):
    root = tmp_path / "captures"
    first = initialize_binding(root, "HTTP://LOCALHOST:80/")
    before = (root / "binding.json").read_bytes()
    second = initialize_binding(root, "http://localhost")
    assert first == second
    assert before == b'{"binding_version":1,"backend_origin":"http://localhost"}'
    assert (root / "binding.json").read_bytes() == before
    with pytest.raises(BindingError) as mismatch:
        initialize_binding(root, "http://127.0.0.1")
    assert mismatch.value.code == "BINDING_MISMATCH"
    assert (root / "binding.json").read_bytes() == before


def test_init_refuses_nonpristine_spool_and_recovers_only_exact_temp(tmp_path):
    dirty = tmp_path / "dirty"
    (dirty / "pending" / "legacy").mkdir(parents=True)
    with pytest.raises(BindingError) as missing:
        initialize_binding(dirty, ORIGIN)
    assert missing.value.code == "BINDING_MISSING"
    assert not (dirty / "binding.json").exists()

    recoverable = tmp_path / "recoverable"
    recoverable.mkdir()
    (recoverable / "binding.json.tmp").write_bytes(b"partial")
    initialize_binding(recoverable, ORIGIN)
    assert validate_binding(recoverable, ORIGIN).backend_origin == ORIGIN
    assert not (recoverable / "binding.json.tmp").exists()


def test_corrupt_or_noncanonical_final_is_never_repaired(tmp_path):
    root = tmp_path / "captures"
    initialize_binding(root, ORIGIN)
    path = root / "binding.json"
    path.write_bytes(b'{"backend_origin":"http://127.0.0.1:8001","binding_version":1}\n')
    with pytest.raises(BindingError) as invalid:
        initialize_binding(root, ORIGIN)
    assert invalid.value.code == "BINDING_INVALID"
    assert path.read_bytes().endswith(b"\n")


def test_valid_binding_does_not_authorize_unknown_root_inventory(tmp_path):
    root = tmp_path / "captures"
    initialize_binding(root, ORIGIN)
    unknown = root / "legacy.db"
    unknown.write_bytes(b"do not adopt")
    with pytest.raises(BindingError) as invalid:
        validate_binding(root, ORIGIN)
    assert invalid.value.code == "BINDING_INVALID"
    assert unknown.read_bytes() == b"do not adopt"


def test_binding_publication_crash_leaves_one_authority_and_matching_init_is_noop(tmp_path):
    root = tmp_path / "captures"

    def stop(point):
        if point == "binding.published":
            raise RuntimeError("synthetic crash")

    with pytest.raises(RuntimeError):
        initialize_binding(root, ORIGIN, barrier=stop)
    final = root / "binding.json"
    temp = root / "binding.json.tmp"
    assert validate_binding(root, ORIGIN).backend_origin == ORIGIN
    assert final.exists() and temp.exists()
    before = (final.read_bytes(), temp.read_bytes())
    initialize_binding(root, ORIGIN)
    assert (final.read_bytes(), temp.read_bytes()) == before


def test_different_configured_origin_halts_before_existing_item_state_mutation(
    bound_spool, png_bytes, request_data
):
    root, guard = bound_spool
    item = Producer(root, guard).publish(
        png_bytes, project_id=PROJECT, original_filename="x.png", request=request_data,
        client_upload_id=CLIENT,
    )
    StateStore(guard.check).initialize(item)
    state_path = item.item_dir / "state.json"
    before = state_path.read_bytes()
    with pytest.raises(BindingError):
        UploadRuntime(RuntimeConfig.create(root, "http://localhost:8001")).run()
    assert state_path.read_bytes() == before
    assert item.item_dir.exists()


@pytest.mark.parametrize(
    ("status", "location"),
    [
        (QueueStatus.PENDING, "pending"),
        (QueueStatus.RETRY_WAIT, "pending"),
        (QueueStatus.IN_FLIGHT, "pending"),
        (QueueStatus.ACKED, "pending"),
        (QueueStatus.UPLOADED, "uploaded"),
    ],
)
def test_a_to_b_restart_preserves_every_durable_progress_state(
    bound_spool, png_bytes, request_data, status, location
):
    root, guard = bound_spool
    item = Producer(root, guard).publish(
        png_bytes, project_id=PROJECT, original_filename="x.png", request=request_data,
        client_upload_id=CLIENT,
    )
    store = StateStore(guard.check)
    initial = store.initialize(item)
    now = datetime(2026, 9, 25, tzinfo=timezone.utc)
    ack = AckRecord(
        screenshot={}, status=201,
        location=f"/api/v1/projects/{PROJECT}/screenshots/{SCREENSHOT}",
        idempotency_replayed=False, x_request_id=REQUEST_ID, received_at=now,
    )
    if status is QueueStatus.PENDING:
        durable = initial
    else:
        durable = QueueState(
            queue_state_version=1,
            client_upload_id=CLIENT,
            manifest_sha256=item.manifest_sha256,
            state=status,
            state_revision=2,
            attempt_count=1,
            retry_epoch=0,
            epoch_attempt_count=1,
            last_attempt_at=now,
            next_attempt_at=(now + timedelta(seconds=1)) if status in {QueueStatus.RETRY_WAIT, QueueStatus.IN_FLIGHT} else None,
            last_error=None,
            ack=ack if status in {QueueStatus.ACKED, QueueStatus.UPLOADED} else None,
        )
    if location == "uploaded":
        item = Spool(root, guard).move(item, "uploaded")
    state_path = item.item_dir / "state.json"
    state_path.write_bytes(durable.to_bytes())
    before = state_path.read_bytes()
    with pytest.raises(BindingError):
        UploadRuntime(RuntimeConfig.create(root, "http://localhost:8001")).run()
    assert state_path.read_bytes() == before
    assert item.item_dir.exists()


def test_concurrent_explicit_init_never_overwrites_authority(tmp_path):
    root = tmp_path / "captures"
    command = [
        sys.executable, "-m", "agent.screenshot_upload", "init",
        "--spool", str(root), "--backend-origin", ORIGIN,
    ]
    first = subprocess.Popen(command, cwd=Path.cwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    second = subprocess.Popen(command, cwd=Path.cwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    first.communicate(timeout=20)
    second.communicate(timeout=20)
    assert 0 in {first.returncode, second.returncode}
    assert {first.returncode, second.returncode} <= {0, 2}
    assert validate_binding(root, ORIGIN).backend_origin == ORIGIN


def test_second_process_cannot_acquire_live_spool_lock(tmp_path):
    root = tmp_path / "captures"
    root.mkdir()
    script = (
        "from agent.screenshot_upload.lock import ProcessLock,LockUnavailable;"
        "import pathlib,sys;"
        "p=pathlib.Path(sys.argv[1]);"
        "\ntry:\n with ProcessLock(p): raise SystemExit(0)"
        "\nexcept LockUnavailable: raise SystemExit(23)"
    )
    with ProcessLock(root):
        result = subprocess.run([sys.executable, "-c", script, str(root)], cwd=Path.cwd(), check=False)
    assert result.returncode == 23
