"""Opt-in real OS containment. Parent captures every invocation, including OOM exit."""
import json
import os
from pathlib import Path
import sys
import time

import pytest

from backend.app.workers import ocr_containment as containment
from backend.app.workers.ocr import child_environment


def _native_limit():
    if os.environ.get("QA_OCR_NATIVE_CONTAINMENT_TEST") != "1":
        pytest.skip("native containment not requested; no native enforcement evidence")
    value = int(os.environ["QA_OCR_NATIVE_LIMIT_BYTES"])
    assert 128 * 1024 * 1024 <= value <= 2 * 1024 * 1024 * 1024
    return value


def _launch(script, tmp_path, *args):
    limit = _native_limit()
    handle = containment.launch_contained(
        [sys._base_executable if os.name == "nt" else sys.executable,
         "-I", "-S", "-c", script, *map(str, args)],
        env=child_environment(str(tmp_path)), cwd=str(tmp_path), memory_limit_bytes=limit,
    )
    return handle, limit


def _finish(handle, record_property):
    started = time.monotonic()
    stopped = False
    record_property("containment_info_before_cleanup", json.dumps(
        getattr(handle, "containment_info", {}), sort_keys=True, default=str,
    ))
    try:
        stopped = handle.stop(started + 3)
        assert stopped, "cleanup must be proven; quarantine is not a passing cleanup test"
        assert handle.poll() is not None
    finally:
        record_property("owned_tree_stop_confirmed", stopped)
        record_property("observed_cleanup_seconds", time.monotonic() - started)
        record_property("owned_pid", handle.pid)
        record_property("containment_info_after_cleanup", json.dumps(
            getattr(handle, "containment_info", {}), sort_keys=True, default=str,
        ))
        if stopped:
            handle.close()


@pytest.mark.parametrize("limit", [0, -1, True, 2 * 1024 * 1024 * 1024 + 1])
def test_invalid_native_limit_fails_before_workload(tmp_path, limit):
    marker = tmp_path / "must-not-run"
    with pytest.raises(containment.ContainmentUnavailable):
        containment.launch_contained(
            [sys.executable, "-I", "-c", "import pathlib,sys;pathlib.Path(sys.argv[1]).touch()", str(marker)],
            env=child_environment(str(tmp_path)), cwd=str(tmp_path), memory_limit_bytes=limit,
        )
    assert not marker.exists()


@pytest.mark.parametrize("phase", ["open", "read", "close"])
def test_native_stop_of_actual_blocking_source_reader(tmp_path, phase, record_property):
    from test_ocr_source_read import _spec
    spec = _spec(tmp_path)
    marker = tmp_path / "entered"
    completed = tmp_path / "unexpected-completion"
    source_path = Path(__file__).resolve().parents[2] / "backend/app/workers/ocr_source.py"
    script = '''
import json, os, pathlib, runpy, sys, time
module = runpy.run_path(sys.argv[1], run_name="source_test_module")
spec, phase, marker, completed = json.loads(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
original = pathlib.Path.open
def block():
    temporary = pathlib.Path(marker).with_suffix(".tmp")
    with original(temporary, "w") as out: out.write(phase)
    os.replace(temporary, marker)
    time.sleep(120)
class Stream:
    def __init__(self, stream): self.stream = stream
    def __enter__(self): return self
    def __exit__(self, *args):
        if phase == "close": block()
        self.stream.close()
    def fileno(self): return self.stream.fileno()
    def read(self, n):
        if phase == "read": block()
        return self.stream.read(n)
def patched(path, *args, **kwargs):
    if phase == "open": block()
    return Stream(original(path, *args, **kwargs))
pathlib.Path.open = patched
module["read_source"](spec)
with original(pathlib.Path(completed), "w") as out: out.write("adapter reachable")
'''
    handle, limit = _launch(script, tmp_path, source_path, json.dumps(spec), phase, marker, completed)
    try:
        until = time.monotonic() + 5
        while not marker.exists() and time.monotonic() < until:
            assert handle.poll() is None, "source child exited before block entry"
            time.sleep(0.01)
        assert marker.read_text() == phase
        assert not completed.exists()
        record_property("blocked_phase", phase)
        record_property("configured_memory_limit_bytes", limit)
    finally:
        _finish(handle, record_property)
    assert not completed.exists()


def test_native_explicit_environment_has_no_inherited_db_credentials(tmp_path, monkeypatch, record_property):
    monkeypatch.setenv("PGPASSWORD", "synthetic-private-sentinel")
    monkeypatch.setenv("DATABASE_URL", "synthetic-private-sentinel")
    marker = tmp_path / "authority.json"
    script = '''
import json, os, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
    "credential_present": any("synthetic-private-sentinel" in v for v in os.environ.values()),
    "database_modules": [k for k in sys.modules if k.startswith(("sqlalchemy", "psycopg", "backend.app.db"))],
    "isolated": sys.flags.isolated
}))
'''
    handle, _ = _launch(script, tmp_path, marker)
    try:
        until = time.monotonic() + 5
        while handle.poll() is None and time.monotonic() < until:
            time.sleep(0.01)
        assert handle.poll() == 0
        facts = json.loads(marker.read_text())
        assert facts == {"credential_present": False, "database_modules": [], "isolated": 1}
        record_property("child_authority_probe", json.dumps(facts))
    finally:
        _finish(handle, record_property)


def test_native_effective_boundary_is_verified_before_workload_and_after(tmp_path, record_property):
    marker = tmp_path / "gated"
    script = (
        "import os,pathlib,sys; p=pathlib.Path(sys.argv[1]); q=p.with_suffix('.tmp'); "
        "q.write_text('ready'); os.replace(q,p); sys.stdin.buffer.read(1)"
    )
    handle, limit = _launch(script, tmp_path, marker)
    try:
        until = time.monotonic() + 5
        while not marker.exists() and time.monotonic() < until:
            time.sleep(0.01)
        assert marker.read_text() == "ready"
        assert not handle.memory_exceeded()
        info = dict(handle.containment_info)
        if os.name == "nt":
            assert info["active_process_limit"] == 1
            assert info["effective_working_set_flags"] & 4  # HARDWS_MAX_ENABLE
            assert 0 < info["effective_working_set_max"] <= limit
            assert info["effective_working_set_max"] % info["page_size"] == 0
            assert info["job_memory_max"] <= limit
        else:
            assert int(info["memory_max"]) <= limit
        assert handle.poll() is None
        assert not handle.memory_exceeded()
        record_property("containment_info_before_stop", json.dumps(handle.containment_info, sort_keys=True))
    finally:
        _finish(handle, record_property)


_L1_BASELINE = 320 * 1024 * 1024
_L1_INCREMENT = 224 * 1024 * 1024
_L1_CAP = 512 * 1024 * 1024


_L1_CHILD = r'''
import json, os, select, sys
baseline, increment, nonce = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
os.set_blocking(1, False)
def send(kind, **facts):
    data = (json.dumps(dict(kind=kind, pid=os.getpid(), nonce=nonce, **facts)) + "\n").encode()
    if len(data) > 1024 or os.write(1, data) != len(data):
        raise RuntimeError("short diagnostic write")
def gate():
    if not select.select([0], [], [], 10)[0] or os.read(0, 1) != b"G":
        raise RuntimeError("pressure gate missing")
held = bytearray(baseline)
for offset in range(0, baseline, 4096):
    held[offset] = 1
send("ready", touched=baseline, increment=increment)
gate()
send("attempt", requested=increment)
extra = None
try:
    extra = bytearray(increment)
    for offset in range(0, increment, 4096):
        extra[offset] = 1
except MemoryError:
    send("denied", requested=increment, error="MemoryError")
else:
    extra = None
    send("completed", requested=increment)
# Bound even the post-result wait; observer cleanup is the sole stop operation.
select.select([0], [], [], 10)
'''


def _l1_oracle(elapsed_ns, attempted, identity, cleaned, outcome, exit_code, delta):
    """Pure evidence oracle; no elapsed-time subtraction or max-only PASS."""
    if not cleaned:
        return "FAIL_CLEANUP"
    if not identity:
        return "FAIL_IDENTITY"
    if not attempted:
        return "UNPROVED_ATTEMPT"
    if elapsed_ns is None or elapsed_ns < 0 or elapsed_ns >= 250_000_000:
        return "UNPROVED_TIMING"
    if outcome == "exit" and exit_code == -9 and delta.get("oom_kill", 0) > 0:
        return "PASS_KILLED_ATTEMPT"
    if outcome == "denied" and delta.get("oom", 0) > 0:
        return "PASS_DENIED_ATTEMPT"
    return "UNPROVED_CAUSE"


@pytest.mark.parametrize("overrides,expected", [
    ({}, "PASS_KILLED_ATTEMPT"),
    ({"outcome": "denied", "exit_code": None, "delta": {"oom": 1}}, "PASS_DENIED_ATTEMPT"),
    ({"elapsed_ns": 250_000_000}, "UNPROVED_TIMING"),
    ({"elapsed_ns": None}, "UNPROVED_TIMING"),
    ({"elapsed_ns": -1}, "UNPROVED_TIMING"),
    ({"attempted": False}, "UNPROVED_ATTEMPT"),
    ({"identity": False}, "FAIL_IDENTITY"),
    ({"cleaned": False}, "FAIL_CLEANUP"),
    ({"delta": {"max": 1}}, "UNPROVED_CAUSE"),
    ({"exit_code": 0}, "UNPROVED_CAUSE"),
    ({"outcome": "completed"}, "UNPROVED_CAUSE"),
    ({"outcome": "denied", "delta": {}}, "UNPROVED_CAUSE"),
])
def test_l1_shortpeak_oracle(overrides, expected):
    facts = dict(elapsed_ns=249_999_999, attempted=True, identity=True,
                 cleaned=True, outcome="exit", exit_code=-9, delta={"oom_kill": 1})
    facts.update(overrides)
    assert _l1_oracle(**facts) == expected


def _l1_events():
    return {key: int(value) for key, value in (
        line.split() for line in Path("/sys/fs/cgroup/memory.events").read_text().splitlines()
    )}


def _l1_identity(pid):
    # Read only the direct owned PID (or self); poll() retains the child PID.
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return dict(pid=pid, start_ticks=int(fields[19]),
                ppid=int(fields[1]), pgrp=int(fields[2]))


def _l1_members():
    return set(map(int, Path("/sys/fs/cgroup/cgroup.procs").read_text().split()))


def _l1_shortpeak(tmp_path, record_property):
    import select
    from uuid import uuid4

    assert _native_limit() == _L1_CAP, "L1 has a fixed 512MiB cap; no scaling/tuning"
    assert os.getpid() == 1, "observer must be PID1 in a fresh dedicated disposable container"
    assert _l1_members() == {os.getpid()}, "unrelated cgroup participants"
    pre = _l1_events()
    assert all(pre[k] == 0 for k in ("max", "oom", "oom_kill", "oom_group_kill"))
    assert Path("/sys/fs/cgroup/memory.max").read_text().strip() == str(_L1_CAP)
    assert Path("/sys/fs/cgroup/memory.swap.max").read_text().strip() == "0"
    nonce = uuid4().hex
    # One helper launch, unchanged explicit isolated environment, no DB/model.
    handle, _ = _launch(_L1_CHILD, tmp_path, _L1_BASELINE, _L1_INCREMENT, nonce)
    facts = dict(observer_pid=os.getpid(), child_pid=handle.pid,
                 baseline_bytes=_L1_BASELINE, increment_bytes=_L1_INCREMENT,
                 memory_limit_bytes=_L1_CAP, events_before_setup=pre,
                 receiver="synchronous nonblocking pipe; no receiver thread")
    messages = []
    pending = bytearray()
    attempted = False
    outcome = None
    exit_code = None
    elapsed_ns = None
    identity_valid = False
    delta = {}
    terminal_at = None
    try:
        os.set_blocking(handle.stdout.fileno(), False)
        os.set_blocking(handle.stdin.fileno(), False)

        def receive():
            # Total protocol is <=3 lines; fail closed on partial/oversized input.
            try:
                chunk = os.read(handle.stdout.fileno(), 4096)
            except BlockingIOError:
                return []
            pending.extend(chunk)
            if len(pending) > 3072:
                raise AssertionError("oversized L1 protocol")
            result = []
            while b"\n" in pending:
                line, _, rest = pending.partition(b"\n")
                pending[:] = rest
                row = json.loads(line)
                assert row.get("pid") == handle.pid and row.get("nonce") == nonce
                result.append(row)
            messages.extend(result)
            assert len(messages) <= 3, "unexpected L1 protocol repetition"
            return result

        ready_deadline = time.monotonic() + 10
        while not messages and time.monotonic() < ready_deadline:
            select.select([handle.stdout], [], [], min(0.01, max(0, ready_deadline - time.monotonic())))
            receive()
            assert handle.poll() is None, "target exited before baseline readiness"
        assert len(messages) == 1 and messages[0]["kind"] == "ready"
        assert messages[0]["touched"] == _L1_BASELINE
        assert messages[0]["increment"] == _L1_INCREMENT
        owned = _l1_identity(handle.pid)
        assert owned["ppid"] == os.getpid() and owned["pgrp"] == handle.pid
        assert _l1_members() == {os.getpid(), handle.pid}
        membership = Path(f"/proc/{handle.pid}/cgroup").read_text()
        assert membership == Path("/proc/self/cgroup").read_text()
        status = Path(f"/proc/{handle.pid}/status").read_text().splitlines()
        anon_bytes = int(next(row.split()[1] for row in status if row.startswith("RssAnon:"))) * 1024
        assert anon_bytes >= _L1_BASELINE, "baseline must be touched anonymous resident memory"
        current = int(Path("/sys/fs/cgroup/memory.current").read_text())
        headroom = _L1_CAP - current
        assert 64 * 1024 * 1024 <= headroom <= 160 * 1024 * 1024, "fixed headroom precondition"
        before_gate = _l1_events()
        assert before_gate == pre, "setup events invalidate pressure attribution"
        assert _l1_identity(handle.pid) == owned
        assert handle.poll() is None
        identity_valid = True
        facts.update(identity=owned, cgroup_membership=membership,
                     cgroup_inode=Path("/sys/fs/cgroup").stat().st_ino,
                     baseline_rss_anon_bytes=anon_bytes, memory_current_before_gate=current,
                     headroom_before_gate=headroom, events_before_gate=before_gate)
        # Both endpoints use THIS surviving observer's monotonic_ns clock.
        t0 = time.monotonic_ns()
        assert os.write(handle.stdin.fileno(), b"G") == 1
        terminal_deadline = time.monotonic() + 2
        while time.monotonic() < terminal_deadline:
            rows = receive()
            for row in rows:
                kind = row["kind"]
                assert row.get("requested") == _L1_INCREMENT
                if kind == "attempt":
                    assert not attempted and outcome is None
                    attempted = True
                else:
                    assert attempted and outcome is None and kind in {"denied", "completed"}
                    if kind == "denied":
                        assert row.get("error") == "MemoryError"
                    outcome = kind
                    terminal_at = time.monotonic_ns()
            if outcome is not None:
                identity_valid = _l1_identity(handle.pid) == owned
                break
            exit_code = handle.poll()  # WNOWAIT: same retained direct process, no PID reopen.
            if exit_code is not None:
                terminal_at = time.monotonic_ns()
                outcome = "exit"
                identity_valid = True
                # Child could die between read and poll; recover queued attempt
                # bytes without changing the earlier conservative exit endpoint.
                for row in receive():
                    assert row["kind"] == "attempt" and not attempted
                    assert row.get("requested") == _L1_INCREMENT
                    attempted = True
                break
            select.select([handle.stdout], [], [], 0.001)
        if terminal_at is not None:
            elapsed_ns = terminal_at - t0
        after = _l1_events()
        delta = {key: after[key] - value for key, value in before_gate.items()}
        assert all(value >= 0 for value in delta.values()), "cgroup event counters reset"
        assert _l1_members() <= {os.getpid(), handle.pid}, "unexpected pressure participant"
        assert Path("/sys/fs/cgroup/memory.max").read_text().strip() == str(_L1_CAP)
        assert Path("/sys/fs/cgroup/memory.swap.max").read_text().strip() == "0"
        assert not pending, "truncated L1 protocol"
        facts.update(t0_ns=t0, t1_ns=terminal_at, elapsed_upper_ns=elapsed_ns,
                     attempted=attempted, outcome=outcome, exit_code=exit_code,
                     events_after=after, events_delta=delta, identity_valid=identity_valid)
    finally:
        facts["messages"] = messages
        try:
            record_property("l1_evidence", json.dumps(facts, sort_keys=True))
        finally:
            # One existing bounded owned-tree stop; no retry or new observer thread.
            _finish(handle, record_property)
    verdict = _l1_oracle(elapsed_ns, attempted, identity_valid, True, outcome, exit_code, delta)
    record_property("l1_verdict", verdict)
    record_property("evidence_scope", "fixed short attempted allocation; not completed over-limit RSS or production qualification")
    if verdict.startswith("FAIL"):
        pytest.fail(verdict)
    if not verdict.startswith("PASS"):
        pytest.skip(verdict + "; no unchanged retry")


_PRESSURE_CHILD = r'''
import json, mmap, os, pathlib, subprocess, sys, threading, time
mode, limit, marker = sys.argv[1], int(sys.argv[2]), pathlib.Path(sys.argv[3])
facts = {"mode": mode, "allocation_denied": False, "descendant_denied": False}
def publish(path, value):
    temporary = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    temporary.write_text(json.dumps(value))
    os.replace(temporary, path)
held = []
started = time.monotonic()
try:
    if mode == "shortpeak":
        publish(marker.with_suffix(".start"), {"before_allocation_monotonic": time.monotonic()})
        held.append(bytearray(limit + 8 * 1024 * 1024))
        held.clear()
    elif mode == "mapped_threads":
        path = marker.with_suffix(".map")
        with path.open("w+b") as backing:
            backing.truncate(limit * 2)
            with mmap.mmap(backing.fileno(), limit * 2) as mapped:
                completed = [False] * 4
                errors = [None] * 4
                def touch(index):
                    try:
                        for offset in range(index * 4096, len(mapped), 4 * 4096): mapped[offset] = 1
                        completed[index] = True
                    except BaseException as error:
                        errors[index] = type(error).__name__
                workers = [threading.Thread(target=touch, args=(i,)) for i in range(4)]
                for worker in workers: worker.start()
                for worker in workers: worker.join()
                facts["native_threads"] = len(workers)
                facts["native_thread_completed"] = completed
                facts["native_thread_errors"] = errors
    elif mode == "descendant":
        ready = marker.with_suffix(".descendant-ready")
        amount = limit * 3 // 5
        try:
            child = subprocess.Popen([sys.executable, "-I", "-S", "-c",
                "import os,pathlib,sys,time; n=int(sys.argv[1]); x=bytearray(n); "
                "x[::4096]=b'x'*len(x[::4096]); p=pathlib.Path(sys.argv[2]); "
                "q=p.with_suffix('.tmp'); q.write_text(str(n)); os.replace(q,p); time.sleep(120)",
                str(amount), str(ready)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            facts["descendant_pid"] = child.pid
            deadline = time.monotonic() + 8
            while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.005)
            if not ready.exists():
                facts["phase"] = "descendant_not_ready"
            else:
                facts["descendant_touched_bytes"] = int(ready.read_text())
                facts["parent_requested_bytes"] = amount
                facts["phase"] = "aggregate_pressure_start"
                publish(marker.with_suffix(".stage"), facts)
                # Supervisor snapshots counters after confirmed descendant
                # residency, before permitting the parent's aggregate attempt.
                if sys.stdin.buffer.read(1) != b"G":
                    raise RuntimeError("aggregate gate was not released")
                held.append(bytearray(amount))
                held[-1][::4096] = b'x' * len(held[-1][::4096])
                facts["parent_touched_bytes"] = amount
        except OSError:
            facts["descendant_denied"] = True
except (MemoryError, OSError):
    facts["allocation_denied"] = True
facts["pressure_elapsed_seconds"] = time.monotonic() - started
publish(marker, facts)
sys.stdin.buffer.read(1)
'''


@pytest.mark.parametrize("mode", ["shortpeak", "mapped_threads", "descendant"])
def test_native_pressure_and_owned_tree_cleanup(tmp_path, mode, record_property):
    if os.name == "nt":
        pytest.skip("NOT_RUN: Windows native lane unavailable after diagnostic02; no third probe")
    if os.environ.get("QA_OCR_NATIVE_PRESSURE_TEST") != "1":
        pytest.skip("NOT_RUN: destructive-to-disposable-runtime pressure slice requires parent opt-in")
    if mode == "shortpeak":
        return _l1_shortpeak(tmp_path, record_property)

    marker = tmp_path / "pressure.json"
    limit = _native_limit()
    # Parent must select ONE parameter per fresh disposable container. Do not
    # reset counters/drop caches or reuse a preceding pressure case's cgroup.
    initial_events = dict(
        (key, int(value)) for key, value in (
            line.split() for line in Path("/sys/fs/cgroup/memory.events").read_text().splitlines()
        )
    )
    record_property("pressure_cgroup_initial_events", json.dumps(initial_events, sort_keys=True))
    assert all(initial_events[key] == 0 for key in ("max", "oom", "oom_kill")), (
        "pressure case requires a fresh disposable cgroup; select one parameter per container"
    )
    handle, _ = _launch(_PRESSURE_CHILD, tmp_path, mode, limit, marker)
    try:
        until = time.monotonic() + 10
        breached = False
        stage_path = marker.with_suffix(".stage")
        stage = {}
        stage_events = None
        stage_delta = {}
        gate_released_at = None
        observed_exit_at = None
        observed_exit_code = None
        while time.monotonic() < until:
            breached = handle.memory_exceeded() or breached
            current_events = dict(handle.containment_info["events_current"])
            if mode == "descendant" and stage_events is None and stage_path.exists():
                stage = json.loads(stage_path.read_text())
                assert stage.get("phase") == "aggregate_pressure_start"
                assert 0 < stage["descendant_touched_bytes"] < limit
                assert 0 < stage["parent_requested_bytes"] < limit
                breached = handle.memory_exceeded() or breached
                stage_events = dict(handle.containment_info["events_current"])
                gate_released_at = time.monotonic()
                assert handle.stdin.write(b"G") == 1
                handle.stdin.flush()
            elif stage_events is not None:
                stage_delta = {key: current_events[key] - value for key, value in stage_events.items()}
                assert all(value >= 0 for value in stage_delta.values()), "cgroup counters reset"
            # max events before descendant readiness may be cache reclaim.
            # Never let those sticky helper events truncate the handshake.
            aggregate_event = any(stage_delta.get(key, 0) > 0 for key in ("oom", "oom_kill"))
            observed_exit_code = handle.poll()
            if observed_exit_code is not None:
                observed_exit_at = time.monotonic()
            if marker.exists() or observed_exit_at is not None or aggregate_event:
                break
            time.sleep(0.01)
        breached = handle.memory_exceeded() or breached
        if stage_events is not None:
            stage_delta = {
                key: handle.containment_info["events_current"][key] - value
                for key, value in stage_events.items()
            }
            assert all(value >= 0 for value in stage_delta.values()), "cgroup counters reset"
        facts = json.loads(marker.read_text()) if marker.exists() else {}
        stage = json.loads(stage_path.read_text()) if stage_path.exists() else {}
        info = dict(handle.containment_info)
        record_property("native_pressure_facts", json.dumps(facts, sort_keys=True))
        record_property("native_pressure_stage", json.dumps(stage, sort_keys=True))
        record_property("aggregate_events_before_gate", json.dumps(stage_events, sort_keys=True))
        record_property("aggregate_events_delta", json.dumps(stage_delta, sort_keys=True))
        record_property("aggregate_gate_monotonic", gate_released_at)
        start_path = marker.with_suffix(".start")
        shortpeak_start = json.loads(start_path.read_text()) if start_path.exists() else {}
        record_property("shortpeak_start", json.dumps(shortpeak_start, sort_keys=True))
        record_property("observed_child_exit_monotonic", observed_exit_at)
        record_property("observed_child_exit_code", observed_exit_code)
        record_property("pressure_direct_pid", handle.pid)
        record_property("pressure_descendant_pid", stage.get("descendant_pid", facts.get("descendant_pid")))
        if shortpeak_start and observed_exit_at is not None:
            # Shared Linux monotonic clock gives an upper bound to observed
            # exit, not proof that the requested peak allocation completed.
            record_property("shortpeak_start_to_observed_exit_upper_seconds", (
                observed_exit_at - shortpeak_start["before_allocation_monotonic"]
            ))
        record_property("native_limit_event_observed", breached)
        record_property("containment_info", json.dumps(info, sort_keys=True))
        record_property("configured_memory_limit_bytes", limit)
        if mode == "mapped_threads":
            # File-backed pages can be reclaimed: completion without a limit
            # event is valid paging, not proof of continuous RSS qualification.
            assert int(info["memory_max"]) <= limit
            assert facts.get("allocation_denied") or (
                facts.get("native_threads") == 4
                and facts.get("native_thread_completed") == [True] * 4
                and facts.get("native_thread_errors") == [None] * 4
            ), (
                "mapped completion/explicit denial missing; max/reclaim event alone is insufficient"
            )
            record_property("evidence_scope", "mapped pressure under existing cgroup; not standalone RSS qualification")
        elif mode == "descendant":
            assert stage.get("phase") == "aggregate_pressure_start", "descendant never confirmed touched subthreshold memory"
            assert 0 < stage["descendant_touched_bytes"] < limit
            assert 0 < stage["parent_requested_bytes"] < limit
            assert stage["descendant_touched_bytes"] + stage["parent_requested_bytes"] > limit
            assert stage_events is not None, "aggregate gate was never released"
            assert any(stage_delta.get(key, 0) > 0 for key in ("oom", "oom_kill")) or facts.get("allocation_denied"), (
                "no OOM/kill or explicit denial after aggregate gate; max/reclaim alone is insufficient"
            )
            record_property("evidence_scope", "aggregate-phase cgroup OOM/denial; event not attributable to a specific participant")
        elif mode == "shortpeak":
            if "pressure_elapsed_seconds" not in facts:
                pytest.skip("NOT_RUN sub-poll timing: child stopped/killed before duration evidence; event alone insufficient")
            if facts["pressure_elapsed_seconds"] >= 0.25:
                pytest.skip("NOT_RUN sub-poll timing: measured allocation interval >=250ms")
            assert any(info["events_delta"].get(key, 0) > 0 for key in ("oom", "oom_kill")) or facts.get("allocation_denied"), (
                "pressure produced neither OOM/kill nor explicit denial; max/reclaim alone is insufficient"
            )
    finally:
        _finish(handle, record_property)
