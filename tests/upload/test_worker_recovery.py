from __future__ import annotations

from datetime import datetime, timedelta, timezone
from collections.abc import Mapping

import pytest

from agent.screenshot_upload.client import HttpResult, UploadTransportError
from agent.screenshot_upload.jsonio import dumps_compact
from agent.screenshot_upload.origin import BindingError
from agent.screenshot_upload.producer import Producer
from agent.screenshot_upload.recovery import validate_intent, validate_persisted_ack
from agent.screenshot_upload.requeue import requeue_failed
from agent.screenshot_upload.spool import Spool
from agent.screenshot_upload.state import QueueStatus
from agent.screenshot_upload.state_store import StateStore
from agent.screenshot_upload.worker import UploadWorker

from conftest import CLIENT, ORIGIN, PROJECT, REQUEST_ID, SCREENSHOT


class Clock:
    def __init__(self):
        self.now = datetime(2026, 9, 25, tzinfo=timezone.utc)
        self.mono = 0.0

    def wall(self):
        return self.now

    def monotonic(self):
        return self.mono

    def sleep(self, seconds):
        self.now += timedelta(seconds=seconds)
        self.mono += seconds


def _produce(bound_spool, png_bytes, request_data):
    root, guard = bound_spool
    item = Producer(root, guard).publish(
        png_bytes, project_id=PROJECT, original_filename="synthetic.png", request=request_data,
        client_upload_id=CLIENT,
    )
    return root, guard, item


def _success(item, received_at):
    request = item.request
    body = {
        "id": SCREENSHOT,
        "project_id": item.project_id,
        "client_upload_id": item.client_upload_id,
        "build_id": request["build_id"],
        "locale_id": request["locale_id"],
        "category_id": request["category_id"],
        "situation_id": request["situation_id"],
        "source": request["source"],
        "original_filename": item.original_filename,
        "uploaded_at": "2026-09-25T00:00:00Z",
        "file_hash": item.file_hash,
        "media_type": item.media_type,
        "size_bytes": item.size_bytes,
        "width": item.width,
        "height": item.height,
        "metadata_version": request["metadata_version"],
        "metadata": _thaw(request["metadata"]),
        "content_url": f"/api/v1/projects/{PROJECT}/screenshots/{SCREENSHOT}/content",
    }
    location = f"/api/v1/projects/{PROJECT}/screenshots/{SCREENSHOT}"
    return HttpResult(201, {"Location": location, "Idempotency-Replayed": "false", "X-Request-ID": REQUEST_ID}, dumps_compact(body), received_at)


def _thaw(value):
    if isinstance(value, Mapping):
        return {key: _thaw(member) for key, member in value.items()}
    if isinstance(value, tuple):
        return [_thaw(member) for member in value]
    return value


class SequenceClient:
    def __init__(self, values):
        self.values = list(values)
        self.calls = 0

    def send(self, item):
        value = self.values[min(self.calls, len(self.values) - 1)]
        self.calls += 1
        if isinstance(value, Exception):
            raise value
        return value


def _worker(guard, store, spool, client, clock):
    return UploadWorker(
        guard=guard, state_store=store, spool=spool, client=client,
        validate_intent=validate_intent, validate_persisted_ack=validate_persisted_ack,
        wall_clock=clock.wall, monotonic=clock.monotonic, sleep=clock.sleep,
        uniform=lambda low, high: low,
    )


def test_success_persists_ack_before_move_then_uploaded(bound_spool, png_bytes, request_data):
    root, guard, item = _produce(bound_spool, png_bytes, request_data)
    clock = Clock()
    store = StateStore(guard.check)
    spool = Spool(root, guard)
    state = _worker(guard, store, spool, SequenceClient([_success(item, clock.wall())]), clock).run_item(item)
    assert state.state is QueueStatus.UPLOADED
    assert state.attempt_count == 1
    moved = root / "uploaded" / CLIENT
    assert moved.exists() and not item.item_dir.exists()
    moved_item = spool.find(CLIENT, "uploaded")
    assert store.load(moved_item).state is QueueStatus.UPLOADED
    validate_persisted_ack(moved_item, store.load(moved_item).ack)


def test_unknown_transport_outcome_retries_same_identity(bound_spool, png_bytes, request_data):
    root, guard, item = _produce(bound_spool, png_bytes, request_data)
    clock = Clock()
    client = SequenceClient([UploadTransportError("lost response"), _success(item, clock.wall())])
    state = _worker(guard, StateStore(guard.check), Spool(root, guard), client, clock).run_item(item)
    assert state.state is QueueStatus.UPLOADED
    assert state.attempt_count == 2
    assert client.calls == 2


def test_malformed_success_never_acknowledges_and_exhausts(bound_spool, png_bytes, request_data):
    root, guard, item = _produce(bound_spool, png_bytes, request_data)
    clock = Clock()
    bad = _success(item, clock.wall())
    bad = HttpResult(bad.status_code, {key: value for key, value in bad.headers.items() if key != "Location"}, bad.body, bad.received_at)
    client = SequenceClient([bad])
    state = _worker(guard, StateStore(guard.check), Spool(root, guard), client, clock).run_item(item)
    assert state.state is QueueStatus.FAILED
    assert state.last_error.code == "RETRY_EXHAUSTED"
    assert state.attempt_count == 8
    assert (root / "failed" / CLIENT / item.image_path.name).exists()


def test_binding_change_after_response_leaves_in_flight_unchanged(bound_spool, png_bytes, request_data):
    root, guard, item = _produce(bound_spool, png_bytes, request_data)
    clock = Clock()
    store = StateStore(guard.check)

    class MutatingClient:
        def send(self, current):
            (root / "binding.json").write_bytes(b'{"binding_version":1,"backend_origin":"http://localhost:8001"}')
            return _success(current, clock.wall())

    with pytest.raises(BindingError):
        _worker(guard, store, Spool(root, guard), MutatingClient(), clock).run_item(item)
    state = store.load(item)
    assert state.state is QueueStatus.IN_FLIGHT
    assert state.attempt_count == 1
    assert item.item_dir.exists()


def test_failed_state_precedes_move_and_explicit_requeue_precedes_move(bound_spool, png_bytes, request_data):
    root, guard, item = _produce(bound_spool, png_bytes, request_data)
    clock = Clock()
    terminal = HttpResult(409, {}, dumps_compact({"error": {"code": "IDEMPOTENCY_CONFLICT"}}), clock.wall())
    store = StateStore(guard.check)
    spool = Spool(root, guard)
    state = _worker(guard, store, spool, SequenceClient([terminal]), clock).run_item(item)
    assert state.state is QueueStatus.FAILED
    failed = spool.find(CLIENT, "failed")

    class StopAfterState:
        def hit(self, point):
            if point == "requeue.pending.durable":
                raise RuntimeError("synthetic crash")

    with pytest.raises(RuntimeError):
        requeue_failed(
            failed, guard=guard, state_store=store, spool=spool,
            validate_intent=validate_intent, faults=StopAfterState(),
        )
    durable = store.load(failed)
    assert durable.state is QueueStatus.PENDING
    assert durable.retry_epoch == 1
    assert failed.item_dir.parent.name == "failed"
    recovered = _worker(guard, store, spool, SequenceClient([_success(failed, clock.wall())]), clock).run_item(failed, location="failed")
    assert recovered.state is QueueStatus.UPLOADED


def test_retry_after_is_minimum_and_invalid_value_is_diagnostic(bound_spool, png_bytes, request_data):
    root, guard, item = _produce(bound_spool, png_bytes, request_data)
    clock = Clock()
    retry = HttpResult(429, {"Retry-After": "20"}, dumps_compact({"error": {"code": "BUSY"}}), clock.wall())
    success = _success(item, clock.wall())
    state = _worker(guard, StateStore(guard.check), Spool(root, guard), SequenceClient([retry, success]), clock).run_item(item)
    assert state.state is QueueStatus.UPLOADED
    assert clock.now >= datetime(2026, 9, 25, tzinfo=timezone.utc) + timedelta(seconds=20)


def test_crash_after_move_recovers_uploaded_without_another_post(bound_spool, png_bytes, request_data):
    root, guard, item = _produce(bound_spool, png_bytes, request_data)
    clock = Clock()
    store = StateStore(guard.check)
    spool = Spool(root, guard)

    class StopAfterMove:
        def hit(self, point):
            if point == "worker.uploaded.moved":
                raise RuntimeError("synthetic crash")

    client = SequenceClient([_success(item, clock.wall())])
    worker = UploadWorker(
        guard=guard, state_store=store, spool=spool, client=client,
        validate_intent=validate_intent, validate_persisted_ack=validate_persisted_ack,
        wall_clock=clock.wall, monotonic=clock.monotonic, sleep=clock.sleep,
        uniform=lambda low, high: low, faults=StopAfterMove(),
    )
    with pytest.raises(RuntimeError):
        worker.run_item(item)
    moved = spool.find(CLIENT, "uploaded")
    assert store.load(moved).state is QueueStatus.ACKED
    no_post = SequenceClient([AssertionError("HTTP must not run during ACKED recovery")])
    recovered = _worker(guard, store, spool, no_post, clock).run_item(moved, location="uploaded")
    assert recovered.state is QueueStatus.UPLOADED
    assert no_post.calls == 0


def test_binding_change_before_acked_recovery_preserves_acked_state(bound_spool, png_bytes, request_data):
    root, guard, item = _produce(bound_spool, png_bytes, request_data)
    clock = Clock()
    store = StateStore(guard.check)
    spool = Spool(root, guard)

    class StopAfterAck:
        def hit(self, point):
            if point == "worker.acked.durable":
                raise RuntimeError("synthetic crash")

    worker = UploadWorker(
        guard=guard, state_store=store, spool=spool,
        client=SequenceClient([_success(item, clock.wall())]),
        validate_intent=validate_intent, validate_persisted_ack=validate_persisted_ack,
        wall_clock=clock.wall, monotonic=clock.monotonic, sleep=clock.sleep,
        uniform=lambda low, high: low, faults=StopAfterAck(),
    )
    with pytest.raises(RuntimeError):
        worker.run_item(item)
    before = (item.item_dir / "state.json").read_bytes()
    assert store.load(item).state is QueueStatus.ACKED
    (root / "binding.json").write_bytes(b'{"binding_version":1,"backend_origin":"http://localhost:8001"}')
    with pytest.raises(BindingError):
        _worker(guard, store, spool, SequenceClient([AssertionError("no HTTP")]), clock).run_item(item)
    assert (item.item_dir / "state.json").read_bytes() == before
    assert item.item_dir.exists()
