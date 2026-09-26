"""Parent authority/deadline scheduling; native containment is tested separately."""
import threading
import time
import json
import io
import os
import queue
import struct
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.app.services.ocr_types import OutcomeUnknown
from backend.app.workers import ocr as runtime
from backend.app.workers.ocr_runtime import OneOperation


def test_child_environment_excludes_database_and_python_injection(monkeypatch, tmp_path):
    for name in ("DATABASE_URL", "DATABASE_HOST", "DATABASE_PASSWORD", "POSTGRES_PASSWORD",
                 "PGPASSWORD", "PGSERVICEFILE", "PYTHONPATH", "PYTHONSTARTUP"):
        monkeypatch.setenv(name, "synthetic-private-sentinel")
    env = runtime.child_environment(str(tmp_path))
    assert "synthetic-private-sentinel" not in repr(env)
    assert env["HOME"] == env["USERPROFILE"] == str(tmp_path)
    assert env["OMP_NUM_THREADS"] == env["MKL_NUM_THREADS"] == env["OPENBLAS_NUM_THREADS"] == "1"


def test_one_operation_retains_settled_identity_until_taken():
    operation = OneOperation()
    token = object()
    operation.start("finalize", lambda: token)
    assert operation.done.wait(2)
    assert not operation.pending
    with pytest.raises(OutcomeUnknown):
        operation.start("fail", lambda: pytest.fail("compensation started"))
    assert operation.take() is token
    assert not operation.occupied


def test_pending_db_operation_cannot_start_compensating_mutation():
    operation = OneOperation()
    entered, release = threading.Event(), threading.Event()
    def wait():
        entered.set()
        release.wait(5)
        raise OutcomeUnknown("lost commit acknowledgement")
    operation.start("finalize", wait)
    try:
        assert entered.wait(2)
        with pytest.raises(OutcomeUnknown):
            operation.start("fail", lambda: pytest.fail("compensation started"))
        with pytest.raises(OutcomeUnknown):
            operation.take()
    finally:
        release.set()
        assert operation.done.wait(2)
    with pytest.raises(OutcomeUnknown, match="lost commit"):
        operation.take()


def _runner():
    runner = runtime.OCRRunner(session_factory=lambda: None)
    calls = []
    runner.jobs = SimpleNamespace(fail=lambda fence, code: calls.append((fence, code)) or "RETRY_WAIT")
    return runner, calls


def test_timeout_fail_only_after_confirmed_stop_preserves_cause(record_property):
    runner, calls = _runner()
    runner.policy.deadline = time.monotonic() - 1
    runner.child_stopped = True
    claim = SimpleNamespace(fence=object())
    runner._record_failure(claim, "ENGINE_TIMEOUT")
    assert calls == [(claim.fence, "ENGINE_TIMEOUT")]
    assert not runner.quarantined
    assert not runner.operation.occupied
    record_property("confirmed_stop_before_fail", runner.child_stopped)
    record_property("timeout_fail_calls", len(calls))


@pytest.mark.parametrize("obstruction", ["unproven_stop", "uncertain_db", "pending_launch"])
def test_uncertain_work_cannot_issue_timeout_fail_or_new_claim(obstruction):
    runner, calls = _runner()
    release = threading.Event()
    active = None
    if obstruction == "unproven_stop":
        runner.child_stopped = False
    else:
        active = runner.operation if obstruction == "uncertain_db" else runner.launch_operation
        active.start("unsettled", lambda: release.wait(5))
    try:
        runner._record_failure(SimpleNamespace(fence=object()), "ENGINE_TIMEOUT")
        assert calls == []
        assert runner.quarantined
        with pytest.raises(OutcomeUnknown):
            runner.run_once()
        assert calls == []
    finally:
        release.set()
        if active is not None:
            assert active.done.wait(2)
            active.take()


def test_uncertain_timeout_failure_is_not_reissued():
    runner, calls = _runner()
    runner.policy.deadline = time.monotonic() - 1
    def fail(fence, code):
        calls.append((fence, code))
        raise OutcomeUnknown("failure commit unknown")
    runner.jobs.fail = fail
    claim = SimpleNamespace(fence=object())
    runner._record_failure(claim, "ENGINE_TIMEOUT")
    runner._record_failure(claim, "ENGINE_TIMEOUT")
    assert calls == [(claim.fence, "ENGINE_TIMEOUT")]
    assert runner.quarantined


def test_confirmed_stop_remains_success_not_quarantine(monkeypatch, record_property):
    runner, _ = _runner()
    deadlines = []
    runner.child_stopped = False
    runner.last_process = SimpleNamespace(stop=lambda deadline: deadlines.append(deadline) or True)
    started = time.monotonic()
    assert runner._stop_child(started - 0.01)
    assert runner.child_stopped
    assert not runner.quarantined
    assert deadlines[0] <= started + runtime.CONTAINMENT_TAIL_SECONDS + 0.05
    record_property("observed_containment_elapsed_seconds", runner.containment_elapsed)


def test_unproven_stop_keeps_runner_quarantined():
    runner, _ = _runner()
    runner.child_stopped = False
    runner.last_process = SimpleNamespace(stop=lambda _deadline: False)
    assert not runner._stop_child(time.monotonic())
    assert not runner.child_stopped
    assert runner.quarantined


def _scheduling_runner(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(runtime, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    runner, calls = _runner()
    runner._storage_root = lambda: "unused-storage-spec"
    monkeypatch.setattr(runtime, "load_metadata", lambda *_: {"bounded": "dto"})
    claim = SimpleNamespace(fence=object())
    runner.jobs.claim = lambda: claim
    runner.jobs.finalize = lambda *_: object()
    runner._release_child = lambda: None
    return runner, calls, claim, clock


def test_delayed_claim_ack_does_not_reset_productive_budget(monkeypatch):
    runner, calls, claim, clock = _scheduling_runner(monkeypatch)
    def delayed_claim():
        clock[0] += runtime.ATTEMPT_SECONDS + 1
        return claim
    runner.jobs.claim = delayed_claim
    runner._execute = lambda *_: pytest.fail("expired claim acknowledgement launched productive work")
    assert runner.run_once()
    assert runner.policy.deadline == 1000 + runtime.ATTEMPT_SECONDS
    assert calls == [(claim.fence, "ENGINE_TIMEOUT")]
    assert not runner.quarantined


@pytest.mark.parametrize("uncertain", [False, True])
def test_late_finalize_settlement_never_compensates(monkeypatch, uncertain):
    runner, calls, claim, clock = _scheduling_runner(monkeypatch)
    finalized = []
    def execute(_claim, dto, deadline):
        assert deadline == 1000 + runtime.ATTEMPT_SECONDS
        runner.last_process = SimpleNamespace(memory_exceeded=lambda: False)
        runner.child_stopped = True
        clock[0] = deadline - 0.1
        return {"complete": True}
    def finalize(fence, output):
        finalized.append((fence, output))
        clock[0] += 2
        if uncertain:
            raise OutcomeUnknown("finalize settlement unresolved")
        return object()
    runner._execute = execute
    runner.jobs.finalize = finalize
    assert runner.run_once()
    assert len(finalized) == 1
    assert calls == []
    assert runner.quarantined is uncertain
    if uncertain:
        with pytest.raises(OutcomeUnknown):
            runner.run_once()
        assert len(finalized) == 1


def test_claim_uncertainty_does_not_launch_child_or_compensate(monkeypatch):
    runner, calls, _claim, _clock = _scheduling_runner(monkeypatch)
    def unknown_claim():
        raise OutcomeUnknown("claim acknowledgement unresolved")
    runner.jobs.claim = unknown_claim
    runner._execute = lambda *_: pytest.fail("unresolved claim launched child")
    assert runner.run_once()
    assert runner.quarantined
    assert calls == []


def test_resource_error_after_deadline_is_not_relabelled_timeout():
    runner, calls = _runner()
    runner.policy.deadline = time.monotonic() - 1
    runner._record_failure(SimpleNamespace(fence=object()), "ENGINE_RESOURCE_LIMIT")
    assert calls == []
    assert runner.last_error_code == "ENGINE_RESOURCE_LIMIT"
    assert runner.quarantined


class _ProtocolHandle:
    """Protocol scheduling double; never claimed as native cleanup evidence."""
    def __init__(self, *, memory_on_stop=False):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(struct.pack("!I", 1) + b"O")
        self.stopped = False
        self.memory_on_stop = memory_on_stop

    def stop(self, _deadline):
        self.stopped = True
        return True

    def memory_exceeded(self):
        return self.stopped and self.memory_on_stop


def _protocol_runner(handle):
    runner, failures = _runner()
    def launch(_deadline):
        runner.last_process = handle
        runner.child_stopped = False
        return handle
    runner._launch = launch
    return runner, failures


def test_unknown_stage_then_stop_memory_event_keeps_quarantine_without_fail():
    handle = _ProtocolHandle(memory_on_stop=True)
    runner, failures = _protocol_runner(handle)
    stage_calls = []
    def stage(fence):
        stage_calls.append(fence)
        raise OutcomeUnknown("stage commit acknowledgement uncertain")
    runner.jobs.stage = stage
    claim = SimpleNamespace(fence=object())
    with pytest.raises(OutcomeUnknown, match="stage commit acknowledgement uncertain"):
        runner._execute(claim, {}, time.monotonic() + 3)
    assert stage_calls == [claim.fence]
    assert handle.memory_exceeded()  # Secondary cleanup event must not mask uncertainty.
    assert runner.quarantined
    assert runner.child_stopped
    assert not runner.last_receiver.is_alive()
    assert not runner.operation.occupied
    runner._record_failure(claim, "ENGINE_RESOURCE_LIMIT")
    assert failures == []
    with pytest.raises(OutcomeUnknown):
        runner.run_once()


@pytest.mark.parametrize("boundary", ["launch_return", "before_initial_write", "verify_dequeue"])
def test_transport_rechecks_deadline_before_productive_command(monkeypatch, boundary):
    clock = [1000.0]
    deadline = 1003.0
    monkeypatch.setattr(runtime, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    handle = _ProtocolHandle()
    runner, failures = _protocol_runner(handle)
    runner.jobs.stage = lambda _fence: "VERIFY"
    if boundary == "launch_return":
        launch = runner._launch
        def expired_launch(value):
            result = launch(value)
            clock[0] = deadline + 0.01
            return result
        runner._launch = expired_launch
    elif boundary == "before_initial_write":
        wire = runtime.Wire
        def expired_wire(*args, **kwargs):
            clock[0] = deadline + 0.01
            return wire(*args, **kwargs)
        monkeypatch.setattr(runtime, "Wire", expired_wire)
    else:
        class ExpiringCommandQueue(queue.Queue):
            def get(self, *args, **kwargs):
                item = super().get(*args, **kwargs)
                clock[0] = deadline + 0.01
                return item
        def queues(maxsize):
            return ExpiringCommandQueue(maxsize) if maxsize == 1 else queue.Queue(maxsize)
        monkeypatch.setattr(runtime, "queue", SimpleNamespace(Queue=queues, Empty=queue.Empty, Full=queue.Full))
    with pytest.raises(RuntimeError, match="^ENGINE_TIMEOUT$"):
        runner._execute(SimpleNamespace(fence=object()), {}, deadline)
    wire_bytes = handle.stdin.getvalue()
    if boundary == "verify_dequeue":
        assert wire_bytes == struct.pack("!I", 3) + b"I{}", "no V after deadline"
    else:
        assert wire_bytes == b"", "no initial DTO after deadline"
    assert runner.child_stopped
    assert not runner.quarantined
    assert runner.last_receiver is None or not runner.last_receiver.is_alive()
    assert failures == []


def test_runner_serializes_large_unicode_input_as_utf8_not_ascii_escapes():
    error = b'E{"code":"INPUT_STORAGE_UNAVAILABLE"}'
    handle = _ProtocolHandle()
    handle.stdout = io.BytesIO(struct.pack("!I", len(error)) + error)
    runner, failures = _protocol_runner(handle)
    dto = {"expected_snapshot": {"text": "한" * ((runtime.MAX_RESULT_BYTES - 32) // 3)},
           "profile_manifest": {"metadata": "fixed" * 32}}
    with pytest.raises(RuntimeError, match="^INPUT_STORAGE_UNAVAILABLE$"):
        runner._execute(SimpleNamespace(fence=object()), dto, time.monotonic() + 5)
    written = handle.stdin.getvalue()
    size = struct.unpack("!I", written[:4])[0]
    payload = written[4:]
    assert len(payload) == size
    assert runtime.MAX_MESSAGE_BYTES < size < runtime.MAX_INPUT_BYTES
    assert "한".encode("utf-8") in payload
    assert b"\\ud55c" not in payload
    assert json.loads(payload[1:]) == dto
    assert runner.child_stopped and not runner.quarantined
    assert not runner.last_receiver.is_alive()
    assert failures == []


_CONTROLLED_CHILD = r'''
import json, os, pathlib, runpy, struct, sys, time
if os.name == "nt":
    import msvcrt
    msvcrt.setmode(0, os.O_BINARY)
    msvcrt.setmode(1, os.O_BINARY)
source_file, mode, marker, afterload, authority = sys.argv[1:]
module = runpy.run_path(source_file, run_name="supervised_source_fixture")
wire = module["Wire"](sys.stdin.buffer, sys.stdout.buffer)
frame = wire.recv_bytes()
assert frame[:1] == b"I"
dto = json.loads(frame[1:])
original = pathlib.Path.open
with original(pathlib.Path(authority), "w") as stream:
    json.dump({"credential_present": any("synthetic-private-sentinel" in v for v in os.environ.values()),
        "db_modules": [k for k in sys.modules if k.startswith(("sqlalchemy", "psycopg", "backend.app.db", "backend.app.config"))],
        "isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
        "dto_keys": sorted(dto)}, stream)
def mark():
    with original(pathlib.Path(marker), "w") as stream: stream.write(mode)
if mode in {"open", "read"}:
    class Stream:
        def __init__(self, stream): self.stream = stream
        def __enter__(self): return self
        def __exit__(self, *args): self.stream.close()
        def fileno(self): return self.stream.fileno()
        def read(self, size):
            mark()
            time.sleep(120)
    def patched(path, *args, **kwargs):
        if mode == "open":
            mark()
            time.sleep(120)
        return Stream(original(path, *args, **kwargs))
    pathlib.Path.open = patched
    module["read_source"](dto["source"])
    with original(pathlib.Path(afterload), "w") as stream: stream.write("late source output")
elif mode in {"partial", "truncated"}:
    mark()
    sys.stdout.buffer.write(struct.pack("!I", 100) + b"D{")
    sys.stdout.buffer.flush()
    if mode == "partial": time.sleep(120)
elif mode == "remaining":
    module["read_source"](dto["source"])
    time.sleep(0.7)
    wire.send_bytes(b"O")
    assert wire.recv_bytes(1) == b"V"
    mark()
    time.sleep(120)
'''


@pytest.mark.parametrize("mode", ["open", "read", "partial", "truncated", "remaining"])
def test_native_real_runner_deadline_and_transport_cleanup(
    mode, tmp_path, monkeypatch, record_property
):
    from test_ocr_containment import _native_limit
    from test_ocr_source_read import _spec
    from backend.app.workers import ocr_containment

    limit = _native_limit()
    source_file = Path(runtime.__file__).with_name("ocr_source.py")
    marker, afterload, authority = (tmp_path / name for name in ("entered", "postload", "authority.json"))
    real_launch = ocr_containment.launch_contained
    launches = []

    def launch(argv, *, env, cwd, memory_limit_bytes):
        assert memory_limit_bytes == 2 * 1024 * 1024 * 1024
        assert "-I" in argv and "-S" in argv
        assert "synthetic-private-sentinel" not in repr((argv, env))
        launches.append(1)
        return real_launch(
            [argv[0], "-I", "-S", "-c", _CONTROLLED_CHILD,
             str(source_file), mode, str(marker), str(afterload), str(authority)],
            env=env, cwd=cwd, memory_limit_bytes=limit,
        )

    monkeypatch.setenv("DATABASE_URL", "synthetic-private-sentinel")
    monkeypatch.setenv("PGPASSWORD", "synthetic-private-sentinel")
    monkeypatch.setattr(ocr_containment, "launch_contained", launch)
    runner, mutations = _runner()
    stages = []
    runner.jobs.stage = lambda fence: stages.append(fence) or "VERIFY"
    runner.jobs.renew = lambda *_: pytest.fail("unexpected renewal in short attempt")
    claim = SimpleNamespace(fence=object())
    dto = dict(source=_spec(tmp_path), source_facts={}, profile_manifest={},
               expected_snapshot={}, verification_config={})
    started = time.monotonic()
    deadline = started + 3
    runner.policy.deadline = deadline
    expected = "ENGINE_PROCESS_CRASH" if mode == "truncated" else "ENGINE_TIMEOUT"
    try:
        with pytest.raises(RuntimeError, match=f"^{expected}$"):
            runner._execute(claim, dto, deadline)
        elapsed = time.monotonic() - started
        assert marker.read_text() == mode, "child must enter intended fault before timeout"
        assert not afterload.exists()
        assert runner.child_stopped
        assert runner.last_process.poll() is not None
        assert not runner.last_receiver.is_alive()
        assert not runner.quarantined, "proven cleanup must not be weakened to quarantine"
        assert not runner.operation.occupied
        assert launches == [1]
        assert mutations == []
        assert stages == ([claim.fence] if mode == "remaining" else [])
        if mode != "truncated":
            assert elapsed - runner.containment_elapsed <= 3.25
        assert elapsed <= 3 + runtime.CONTAINMENT_TAIL_SECONDS + 0.5
        facts = json.loads(authority.read_text())
        assert facts["credential_present"] is False
        assert facts["db_modules"] == []
        assert facts["isolated"] == facts["no_site"] == 1
        assert facts["dto_keys"] == sorted(dto)
        record_property("observed_elapsed_seconds", elapsed)
        record_property("observed_containment_tail_seconds", runner.containment_elapsed)
        record_property("owned_tree_stop_confirmed", runner.child_stopped)
        record_property("transport_alive_after_stop", runner.last_receiver.is_alive())
        record_property("observed_error_code", expected)
        record_property("source_import_authority", json.dumps(facts))
    finally:
        # Product supervision owns the single stop attempt. Do not retry an
        # unproven stop here; preserve quarantine for disposable-runtime teardown.
        record_property("final_owned_tree_stop_confirmed", runner.child_stopped)
        record_property("final_containment_tail_seconds", runner.containment_elapsed)
        record_property("final_runner_quarantined", runner.quarantined)
        record_property("final_transport_alive", bool(
            runner.last_receiver is not None and runner.last_receiver.is_alive()))
        if runner.last_process is not None:
            record_property("final_containment_info", json.dumps(
                getattr(runner.last_process, "containment_info", {}), default=str, sort_keys=True))
        if runner.child_stopped:
            runner._release_child()
