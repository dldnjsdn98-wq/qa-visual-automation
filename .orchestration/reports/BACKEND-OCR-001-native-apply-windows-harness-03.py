"""UNEXECUTED startup-only candidate; hook claim and native authorization HOLD.

Requires exact prospective W1 + private suspended-owner sink hook. No package or
model imports, patch application or retry. One owned launch, one stop owner.
Original setup/native return latency is NOT proven bounded. Unresolved owners and
threads remain referenced until harness exit; that exit is not cleanup proof.
Future invocation: pinned Python -I -S THIS_FILE --output NEW_ABSOLUTE_JSON
    --executable ABSOLUTE_TRUSTED_DIRECT_PYTHON
"""
from __future__ import annotations

import argparse
import ctypes as c
from ctypes import wintypes as w
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import sys
import tempfile
import threading
import time
import uuid

HELPER_LF = "f9f41dc9d09f003a857d6e98c3053279b9616a346f0b34aa97309666c14c6302"
QUERIES_LF = "e0650cbc135da408b589c1765bc7aaa67f2db1e2f62174c339f3549426210133"
LIMIT = 256 * 1024 * 1024
_RETAINED = []

CHILD = r'''
import hashlib, json, os, sys, msvcrt
msvcrt.setmode(0, os.O_BINARY)
msvcrt.setmode(1, os.O_BINARY)
def image(p):
    return {'basename': os.path.basename(p), 'path_sha256': hashlib.sha256(os.fsencode(p)).hexdigest()}
if sys.stdin.buffer.read(1) != b'S':
    raise RuntimeError('startup handshake missing')
facts = {'nonce': sys.argv[1], 'pid': os.getpid(), 'ppid': os.getppid(),
         'executable': image(sys.executable), 'base_executable': image(sys._base_executable),
         'isolated': sys.flags.isolated, 'no_site': sys.flags.no_site,
         'phase': 'stdlib-startup-only'}
sys.stdout.buffer.write(json.dumps(facts).encode('ascii') + b'\n')
sys.stdout.buffer.flush()
sys.stdin.buffer.read(1)  # No import grant exists; sole Job termination ends this wait.
'''


def error_info(error):
    return {"type": type(error).__name__, "errno": getattr(error, "errno", None),
            "winerror": getattr(error, "winerror", None)}


def load_exact(path, expected, name):
    raw = path.read_bytes()
    source = raw.decode("utf-8").replace("\r\n", "\n")
    if hashlib.sha256(source.encode()).hexdigest() != expected:
        raise ValueError("Frozen source hash gate failed")
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None))
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)  # Only the bytes just hashed.
    return module, hashlib.sha256(raw).hexdigest()


class StageEvents:
    def __init__(self, events, stage):
        self.events, self.stage = events, stage

    def put(self, item):
        self.events.put({**item, "stage": self.stage})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--executable", required=True, type=Path)
    args = parser.parse_args()
    if sys.platform != "win32" or not args.executable.is_absolute():
        parser.error("Windows and an absolute trusted direct executable required")
    if not args.output.is_absolute() or not args.output.parent.is_dir():
        parser.error("New absolute output in existing evidence directory required")
    root = Path(__file__).resolve().parents[2]
    report = {"status": "UNKNOWN", "qualification": "UNAVAILABLE", "scope": "stdlib-startup-only",
              "prior_native_failures": 3, "prior_cleanup_failures": 2, "observations": [], "errors": [],
              "launch_requests": 0, "import_phase": "NOT_IMPLEMENTED_NOT_AUTHORIZED",
              "cleanup_confirmed": False, "handles_closed": False, "snapshots_non_atomic": True}
    events, sink, workers = queue.SimpleQueue(), [], []
    launched = threading.Event()
    stop_deadline = None

    def emit(stage, name, value=None, error=None):
        events.put({"stage": stage, "operation": name, "end": time.monotonic(),
                    "state": "unknown" if error is not None else "returned",
                    "value": value, "error": error})

    def spawn(name, action):
        def guarded():
            try:
                action()
            except BaseException as error:
                emit(name, "worker_error", error=error_info(error))
        thread = threading.Thread(target=guarded, name=name, daemon=True)
        workers.append(thread)
        thread.start()
        return thread

    def collect():
        while True:
            try:
                report["observations"].append(events.get_nowait())
            except queue.Empty:
                break

    def values(stage, deadline):
        collect()
        items = [x for x in report["observations"] if x["stage"] == stage]
        returned = {x["operation"]: x["value"] for x in items
                    if x["state"] == "returned" and x.get("end", float("inf")) <= deadline}
        unknown = any(x["state"] == "unknown" or x.get("end", 0) > deadline for x in items)
        return returned, unknown

    with args.output.open("x", encoding="utf-8") as output:
        try:
            helper, raw_hash = load_exact(root / "backend/app/workers/ocr_containment.py", HELPER_LF, "w1_helper")
            previous, query_hash = load_exact(Path(__file__).with_name(
                "BACKEND-OCR-001-native-diagnostic-windows-03.py"), QUERIES_LF, "frozen_queries")
            report.update(helper_lf_sha256=HELPER_LF, helper_raw_sha256=raw_hash,
                          query_lf_sha256=QUERIES_LF, query_raw_sha256=query_hash)
            if helper._FAILED_WINDOWS_LAUNCHES:
                raise RuntimeError("Prior unresolved helper ownership")
            requested = previous.file_identity(args.executable)
            if requested["stable_file_identity"] is not True:
                raise ValueError("Unstable requested executable")
            report["requested_image"] = requested
            scratch = Path(tempfile.mkdtemp(prefix="windows-w1-startup-", dir=args.output.parent))
            report["scratch_basename"] = scratch.name
            nonce = uuid.uuid4().hex
            env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
            env.update(TEMP=str(scratch), TMP=str(scratch), HOME=str(scratch), USERPROFILE=str(scratch))
            report["environment_keys"] = sorted(env)
            argv = [str(args.executable), "-I", "-S", "-c", CHILD, nonce]
            t0 = time.monotonic()
            pre_deadline, marker_deadline, startup_deadline, total_deadline = t0+5, t0+9, t0+10, t0+30
            report.update(t0=t0, pre_deadline=pre_deadline, marker_deadline=marker_deadline,
                          startup_deadline=startup_deadline, total_deadline=total_deadline, configured_limit=LIMIT)

            def launch():
                try:
                    owner = helper._launch_windows(argv, env, str(scratch), LIMIT, _diagnostic_owner_sink=sink)
                    if len(sink) != 1 or sink[0] is not owner:
                        raise RuntimeError("Owner handoff mismatch")
                    emit("launch", "complete", {"pid": owner.pid})
                except BaseException as error:
                    emit("launch", "failure", {"cleanup_confirmed": getattr(error, "cleanup_confirmed", False),
                        "workload_started": getattr(error, "workload_started", True),
                        "cleanup_accounting": getattr(error, "cleanup_accounting", None)}, error_info(error))
                finally:
                    launched.set()

            def observe(stage, deadline, counts_only=False):
                owner = sink[0]
                q = previous.Queries(owner, StageEvents(events, stage), deadline)
                for name, action in (("class1", q.accounting), ("class3", q.pids)):
                    try:
                        q.call(name, action)
                    except BaseException:
                        pass  # Preserve one central result if the other is unavailable.
                if counts_only:
                    emit(stage, "failure_counts_complete")
                    return
                def effective():
                    minimum, maximum, flags = c.c_size_t(), c.c_size_t(), w.DWORD()
                    owner._api.require(owner._api.kernel.GetProcessWorkingSetSizeEx(owner._handle,
                        c.byref(minimum), c.byref(maximum), c.byref(flags)), "Read working set")
                    limits, returned = owner._api.ExtendedLimits(), w.DWORD()
                    owner._api.require(owner._api.kernel.QueryInformationJobObject(owner._job, 9,
                        c.byref(limits), c.sizeof(limits), c.byref(returned)), "Read Job limits")
                    if returned.value != c.sizeof(limits):
                        raise ValueError("Extended limits length")
                    return {"ws_max": maximum.value, "ws_flags": flags.value, "page": owner._page,
                            "job_flags": limits.BasicLimitInformation.LimitFlags,
                            "active_limit": limits.BasicLimitInformation.ActiveProcessLimit,
                            "job_memory": limits.JobMemoryLimit}
                q.call("effective", effective)
                q.call("identity", lambda: q.identity(owner._handle, owner.pid))
                try:
                    q.call("helper_check", owner._check_limits)
                finally:
                    anomaly = owner.containment_info.get("accounting_first_anomaly")
                    if anomaly is not None:
                        emit(stage, "helper_accounting_anomaly", anomaly)
                emit(stage, "complete")

            def valid(stage, deadline):
                v, unknown = values(stage, deadline)
                pid, page = sink[0].pid, sink[0]._page
                identity, image = v.get("identity", {}), v.get(f"pid{pid}.image_file", {})
                limit = LIMIT - LIMIT % page
                good = (not unknown and "complete" in v and "helper_check" in v and
                        v.get("class1", {}).get("values", {}).get("ActiveProcesses") == 1 and
                        v.get("class1", {}).get("values", {}).get("TotalProcesses") == 1 and
                        v.get("class3", {}).get("assigned") == 1 and v.get("class3", {}).get("listed") == 1 and
                        v.get("class3", {}).get("pids") == [pid] and identity.get("pid") == pid and
                        identity.get("membership_revalidated") is True and
                        v.get(f"pid{pid}.parent", {}).get("parent_pid") is not None and
                        image.get("stable_file_identity") is True and image.get("sha256") == requested["sha256"] and
                        image.get("path_sha256") == requested["path_sha256"] and
                        v.get("effective") == {"ws_max": limit, "ws_flags": 6, "page": page,
                            "job_flags": 0x2208, "active_limit": 1, "job_memory": limit})
                return bool(good), identity

            def receive_startup():
                owner = sink[0]
                q = previous.Queries(owner, StageEvents(events, "receiver"), marker_deadline)
                count = q.call("resume", lambda: int(owner._api.kernel.ResumeThread(owner._diagnostic_primary_thread)))
                if count != 1:
                    raise ValueError("Unexpected prior suspend count; no handshake allowed")
                def handshake():
                    if owner.stdin.write(b"S") != 1:
                        raise ValueError("Handshake write failed")
                    owner.stdin.flush()
                    frame = owner.stdout.readline(8193)
                    if len(frame) > 8192 or not frame.endswith(b"\n"):
                        raise ValueError("Invalid bounded startup frame")
                    facts = json.loads(frame)
                    if (facts.get("nonce") != nonce or facts.get("pid") != owner.pid or facts.get("isolated") != 1
                            or facts.get("no_site") != 1 or facts.get("phase") != "stdlib-startup-only"):
                        raise ValueError("Startup identity mismatch")
                    return facts
                q.call("self_report", handshake)

            def stop(deadline):
                # Sole stop owner, independent of launch unwind/observers/pipe reader.
                # Late publication still requests termination, but can never earn timely proof.
                while not sink:
                    if launched.is_set():
                        emit("stop", "no_handoff", {"helper_owns_failed_setup_cleanup": True})
                        return
                    launched.wait(0.01)
                owner = sink[0]
                emit("stop", "termination_requested")
                ok = bool(owner._api.kernel.TerminateJobObject(owner._job, 1))
                emit("stop", "termination_result", {"ok": ok, "winerror": 0 if ok else c.get_last_error()})
                if not ok or time.monotonic() >= deadline:
                    return
                q = previous.Queries(owner, StageEvents(events, "stop"), deadline)
                while time.monotonic() < deadline:
                    direct = owner._api.kernel.WaitForSingleObject(owner._handle, 0)
                    count = q.call("class1", q.accounting)
                    finished = time.monotonic()
                    if direct == 0 and count["values"]["ActiveProcesses"] == 0 and finished <= deadline:
                        emit("stop", "proof", {"direct_signaled": True, "active": 0, "observed_at": finished})
                        return
                    if direct not in (0, 0x102):
                        raise ValueError("Unexpected retained process wait result")
                    time.sleep(min(0.01, max(0, deadline-time.monotonic())))

            report["launch_requests"] = 1
            early_stop_time = None
            try:
                launch_thread = spawn("launcher", launch)
                launch_thread.join(max(0, pre_deadline-time.monotonic()))
                lv, bad_launch = values("launch", pre_deadline)
                if launch_thread.is_alive() or bad_launch or "complete" not in lv or len(sink) != 1:
                    raise RuntimeError("Launch ownership/completion unproved; no resume")
                report["owned_pid"] = sink[0].pid
                pre = spawn("pre", lambda: observe("pre", pre_deadline))
                pre.join(max(0, pre_deadline-time.monotonic()))
                pre_ok, pre_identity = valid("pre", pre_deadline)
                if pre.is_alive() or time.monotonic() > pre_deadline or not pre_ok:
                    raise RuntimeError("Pre-resume evidence incomplete; no resume")
                receiver = spawn("receiver", receive_startup)
                receiver.join(max(0, marker_deadline-time.monotonic()))
                rv, receiver_unknown = values("receiver", marker_deadline)
                if receiver.is_alive() or receiver_unknown or rv.get("resume") != 1 or "self_report" not in rv:
                    # No optional audit or useful-work delay on readiness failure.
                    early_stop_time = time.monotonic()
                    failure_counts_deadline = min(startup_deadline, early_stop_time + 1)
                    spawn("startup", lambda: observe("startup", failure_counts_deadline, True))
                    raise RuntimeError("Startup receiver unproved; immediate owned stop")
                startup = spawn("startup", lambda: observe("startup", startup_deadline))
                startup.join(max(0, startup_deadline-time.monotonic()))
                startup_ok, startup_identity = valid("startup", startup_deadline)
                rv, receiver_unknown = values("receiver", marker_deadline)
                facts = rv.get("self_report", {})
                sv, _ = values("startup", startup_deadline)
                report["startup_complete"] = bool(not receiver.is_alive() and not startup.is_alive()
                    and time.monotonic() <= startup_deadline and startup_ok and not receiver_unknown
                    and rv.get("resume") == 1 and facts.get("pid") == sink[0].pid
                    and facts.get("executable") == sv.get(f"pid{sink[0].pid}.image")
                    and pre_identity.get("creation_time") == startup_identity.get("creation_time"))
            finally:
                stop_time = early_stop_time if early_stop_time is not None else time.monotonic()
                stop_deadline = min(stop_time + 2, total_deadline)
                report.update(stop_requested_at=stop_time, cleanup_deadline=stop_deadline)
                stopper = spawn("stop", lambda: stop(stop_deadline))
                stopper.join(max(0, stop_deadline-time.monotonic()))
                # Termination may unblock the bounded reader; all joins share the same tail.
                for worker in workers:
                    worker.join(max(0, stop_deadline-time.monotonic()))
                proof, unknown = values("stop", stop_deadline)
                report["cleanup_confirmed"] = "proof" in proof and not unknown and not stopper.is_alive()
                if report["cleanup_confirmed"] and not any(t.is_alive() for t in workers) and time.monotonic() < stop_deadline:
                    def close():
                        if time.monotonic() >= stop_deadline:
                            return
                        owner = sink[0]
                        owner._api.require(owner._api.kernel.CloseHandle(owner._diagnostic_primary_thread), "Close primary thread")
                        owner._diagnostic_primary_thread = None
                        owner._stopped = True
                        owner.close()
                        emit("close", "complete")
                    closer = spawn("close", close)
                    closer.join(max(0, stop_deadline-time.monotonic()))
                    closed, close_unknown = values("close", stop_deadline)
                    report["handles_closed"] = "complete" in closed and not close_unknown and not closer.is_alive()
        except BaseException as error:
            report["errors"].append(error_info(error))
        finally:
            collect()
            # Workers only append immutable events; none writes this final report or its proof booleans.
            report["workers_alive"] = [t.name for t in workers if t.is_alive()]
            if report["workers_alive"] or (sink and not report["handles_closed"]):
                _RETAINED.append((sink, workers, events, locals().get("helper")))
                report["quarantine"] = "retained until harness exit; no cleanup inference from exit; no next launch"
            seen = report["observations"]
            report["termination_requests"] = sum(x["operation"] == "termination_requested" for x in seen)
            extra = any(x["state"] == "returned" and x["stage"] in ("pre", "startup") and (
                (x["operation"] == "class1" and (x["value"]["values"]["ActiveProcesses"] > 1 or
                                                  x["value"]["values"]["TotalProcesses"] > 1)) or
                (x["operation"] == "class3" and (x["value"]["listed"] > 1 or x["value"]["assigned"] > 1)) or
                (x["operation"] == "helper_accounting_anomaly" and
                 x["value"].get("query_succeeded") is True and
                 x["value"].get("query_class") == 1 and
                 x["value"].get("returned_bytes") == x["value"].get("buffer_bytes") == 48 and
                 x["value"]["values"]["ActiveProcesses"] > 1)) for x in seen)
            if extra:
                report.update(status="FAIL_SAME_CAUSE_PAUSE", native_same_cause_failures=4)
            elif (report.get("startup_complete") and report["cleanup_confirmed"] and report["handles_closed"]
                  and not report["workers_alive"] and not report["errors"]):
                report["status"] = "STARTUP_NONREPRO_NOT_QUALIFIED"
            report["snapshot_at"] = time.monotonic()
            report["next_action"] = "parent review; imports/retry not authorized"
            try:
                serialized = json.dumps(report, indent=2)
            except BaseException as error:
                serialized = json.dumps({"status": report["status"], "qualification": "UNAVAILABLE",
                    "serialization_error": error_info(error), "cleanup_confirmed": report["cleanup_confirmed"]})
            try:
                output.write(serialized + "\n")
                output.flush()
            except BaseException as error:
                print(serialized, file=sys.stderr)
                print(json.dumps({"evidence_write_error": error_info(error)}), file=sys.stderr)
    return 1 if report["status"] == "FAIL_SAME_CAUSE_PAUSE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
