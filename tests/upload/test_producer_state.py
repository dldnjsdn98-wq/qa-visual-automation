from __future__ import annotations

from dataclasses import replace

import pytest

from agent.screenshot_upload.producer import Producer
from agent.screenshot_upload.spool import Spool, SpoolError
from agent.screenshot_upload.state import QueueStatus
from agent.screenshot_upload.state_store import StateStore, StateStoreError

from conftest import CLIENT, PROJECT


def _produce(bound_spool, png_bytes, request_data):
    root, guard = bound_spool
    return Producer(root, guard).publish(
        png_bytes,
        project_id=PROJECT,
        original_filename=r"C:\captures\synthetic.png",
        request=request_data,
        client_upload_id=CLIENT,
    )


def test_marker_is_published_last_and_partial_artifacts_are_not_discovered(bound_spool, png_bytes, request_data):
    root, guard = bound_spool
    producer = Producer(root, guard)

    def stop(point):
        if point == "producer.manifest.renamed":
            raise RuntimeError("synthetic crash")

    with pytest.raises(RuntimeError):
        producer.publish(
            png_bytes, project_id=PROJECT, original_filename="x.png", request=request_data,
            client_upload_id=CLIENT, barrier=stop,
        )
    item_dir = root / "pending" / CLIENT
    assert (item_dir / "original.png").exists()
    assert (item_dir / "manifest.json").exists()
    assert not (item_dir / "ready.json").exists()
    assert Spool(root, guard).discover() == []


def test_crash_after_ready_publication_remains_eligible(bound_spool, png_bytes, request_data):
    root, guard = bound_spool

    def stop(point):
        if point == "producer.ready.renamed":
            raise RuntimeError("synthetic crash")

    with pytest.raises(RuntimeError):
        Producer(root, guard).publish(
            png_bytes, project_id=PROJECT, original_filename="x.png", request=request_data,
            client_upload_id=CLIENT, barrier=stop,
        )
    assert (root / "pending" / CLIENT / "ready.json.tmp").exists()
    discovered = Spool(root, guard).discover()
    assert len(discovered) == 1
    assert discovered[0][0].client_upload_id == CLIENT


def test_state_precedes_initialized_and_missing_marker_repairs_without_reset(bound_spool, png_bytes, request_data):
    root, guard = bound_spool
    item = _produce(bound_spool, png_bytes, request_data)
    store = StateStore(guard.check)
    state = store.initialize(item)
    assert state.state is QueueStatus.PENDING
    marker = item.item_dir / "initialized.json"
    marker.unlink()
    repaired = store.load(item)
    assert repaired == state
    assert marker.exists()


def test_marker_without_state_and_corrupt_state_are_never_reinitialized(bound_spool, png_bytes, request_data):
    root, guard = bound_spool
    item = _produce(bound_spool, png_bytes, request_data)
    store = StateStore(guard.check)
    store.initialize(item)
    state_path = item.item_dir / "state.json"
    state_path.unlink()
    with pytest.raises(StateStoreError):
        store.load(item)
    state_path.write_bytes(b"{")
    with pytest.raises(StateStoreError):
        store.load(item)
    assert (item.item_dir / "initialized.json").exists()
    assert state_path.read_bytes() == b"{"


def test_state_transition_enforces_revision_and_monotonic_counts(bound_spool, png_bytes, request_data):
    _, guard = bound_spool
    item = _produce(bound_spool, png_bytes, request_data)
    store = StateStore(guard.check)
    state = store.initialize(item)
    with pytest.raises(ValueError):
        replace(state, state_revision=2, attempt_count=-1)


def test_duplicate_identity_across_queue_roots_halts_without_overwrite(bound_spool, png_bytes, request_data):
    root, guard = bound_spool
    item = _produce(bound_spool, png_bytes, request_data)
    duplicate = root / "failed" / CLIENT
    duplicate.mkdir()
    with pytest.raises(SpoolError):
        Spool(root, guard).discover()
    assert item.item_dir.exists() and duplicate.exists()
