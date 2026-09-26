"""PROPOSED owned-Job identity diagnostic; parent/Fermat review before execution.

One launch, one direct owned-Job termination, no pressure or limit changes.
Uses frozen helper ef7d7ffe; deliberately does NOT call helper.stop(), whose
pre-kill observation could block behind a stalled native query. This standalone
stop path is diagnostic-only and requires explicit review. Not qualification.

Parent invocation: pinned Python -I -S THIS_FILE --output NEW_ABSOLUTE_JSON_PATH
Optional --executable ABSOLUTE_DIRECT_BASE_PYTHON (default sys._base_executable).
All artifacts are new files beneath output.parent; scratch evidence is retained.
No process enumeration, PID kills, environment dumps, retries or helper edits.
Startup-only single gate; not the original two-gate pathlib-phase reproduction.
Parent Job membership and post-identity repeated counts are deliberately absent.
Existing synchronous launcher setup is not made time-bounded by this diagnostic.
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


HELPER_SHA256 = "ef7d7ffe6dbc0b8f620ae9416818614cf9aa9dc5ceb822fdee11d4feca76bec5"
MEMORY_LIMIT = 256 * 1024 * 1024
OBSERVE_SECONDS = 5.0
STOP_SECONDS = 2.0
MAX_MEMBERS = 4
MAX_IMAGE_BYTES = 16 * 1024 * 1024
_RETAINED = []  # Unresolved owners/threads remain referenced until harness exit.

CHILD = r'''
import hashlib, json, os, pathlib, sys
def image(p):
    return {'basename': pathlib.Path(p).name,
            'path_sha256': hashlib.sha256(os.fsencode(p)).hexdigest()}
p = pathlib.Path(sys.argv[1]); q = p.with_suffix('.tmp')
q.write_text(json.dumps({'nonce': sys.argv[2], 'pid': os.getpid(),
    'ppid': os.getppid(), 'executable': image(sys.executable),
    'base_executable': image(sys._base_executable), 'isolated': sys.flags.isolated}), encoding='utf-8')
os.replace(q, p)
sys.stdin.buffer.read(1)
'''


def path_identity(path):
    return {"basename": Path(path).name,
            "path_sha256": hashlib.sha256(os.fsencode(path)).hexdigest()}


def error_identity(error):
    # Exception text/args may contain user-system image paths; never serialize them.
    return {"type": type(error).__name__, "errno": getattr(error, "errno", None),
            "winerror": getattr(error, "winerror", None)}


def file_identity(path):
    path = Path(path)
    if not path.is_absolute() or str(path).startswith(("\\\\", "//")):
        raise ValueError("Only an absolute local image file may be hashed")
    before = path.stat()
    if not path.is_file() or not 0 < before.st_size <= MAX_IMAGE_BYTES:
        raise ValueError("Image file is not a bounded regular local file")
    with path.open("rb") as stream:
        data = stream.read(MAX_IMAGE_BYTES + 1)
    after = path.stat()
    stable = ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
              == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns))
    if len(data) > MAX_IMAGE_BYTES or not data.startswith(b"MZ"):
        raise ValueError("Image file is not a bounded PE")
    return {**path_identity(path), "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "stable_file_identity": stable, "hash_subject": "on-disk image, not loaded memory"}


class Queries:
    def __init__(self, owner, events, deadline):
        self.owner, self.events, self.deadline = owner, events, deadline
        self.a, self.k = owner._api, owner._api.kernel
        self.k.GetProcessId.argtypes, self.k.GetProcessId.restype = [w.HANDLE], w.DWORD
        self.k.OpenProcess.argtypes, self.k.OpenProcess.restype = [w.DWORD, w.BOOL, w.DWORD], w.HANDLE
        self.k.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
        self.k.QueryFullProcessImageNameW.restype = w.BOOL
        self.k.GetProcessTimes.argtypes = [w.HANDLE] + [c.POINTER(w.FILETIME)] * 4
        self.k.GetProcessTimes.restype = w.BOOL

        class PBI(c.Structure):
            _fields_ = [("ExitStatus", c.c_int32), ("PebBaseAddress", c.c_void_p),
                        ("AffinityMask", c.c_size_t), ("BasePriority", c.c_int32),
                        ("UniqueProcessId", c.c_size_t), ("InheritedFromUniqueProcessId", c.c_size_t)]

        expected = (48, 40) if c.sizeof(c.c_void_p) == 8 else (24, 20)
        if (c.sizeof(PBI), PBI.InheritedFromUniqueProcessId.offset) != expected:
            raise ValueError("Unexpected PROCESS_BASIC_INFORMATION ABI")
        self.PBI = PBI
        self.nt = c.WinDLL("ntdll", use_last_error=True).NtQueryInformationProcess
        self.nt.argtypes = [w.HANDLE, w.ULONG, c.c_void_p, w.ULONG, c.POINTER(w.ULONG)]
        self.nt.restype = c.c_int32  # signed NTSTATUS, never BOOL/unsigned status

    def call(self, name, action):
        if time.monotonic() >= self.deadline:
            raise TimeoutError("Observation budget expired")
        begin = time.monotonic()
        self.events.put({"operation": name, "begin": begin, "state": "started"})
        try:
            value = action()
        except BaseException as error:
            self.events.put({"operation": name, "begin": begin, "end": time.monotonic(),
                             "state": "unknown", "error": error_identity(error)})
            raise
        self.events.put({"operation": name, "begin": begin, "end": time.monotonic(),
                         "state": "returned", "value": value})
        return value

    def member(self, handle):
        inside = w.BOOL()
        if not self.k.IsProcessInJob(handle, self.owner._job, c.byref(inside)):
            raise OSError(c.get_last_error(), "Exact owned-Job membership query failed")
        return bool(inside.value)

    def times(self, handle):
        values = [w.FILETIME() for _ in range(4)]
        if not self.k.GetProcessTimes(handle, *(c.byref(value) for value in values)):
            raise OSError(c.get_last_error(), "GetProcessTimes failed")
        return {name: (value.dwHighDateTime << 32) | value.dwLowDateTime
                for name, value in zip(("created", "exited", "kernel", "user"), values)}

    def accounting(self):
        value, returned = self.a.Accounting(), w.DWORD()
        ok = self.k.QueryInformationJobObject(self.owner._job, 1, c.byref(value),
                                              c.sizeof(value), c.byref(returned))
        if not ok or returned.value != c.sizeof(value):
            raise OSError(c.get_last_error() if not ok else 0, "Invalid class-1 result length/status")
        return {"returned_bytes": returned.value,
                "raw_hex": c.string_at(c.byref(value), c.sizeof(value)).hex(),
                "values": {name: getattr(value, name) for name, _ in value._fields_}}

    def pids(self):
        class PIDList(c.Structure):
            _fields_ = [("assigned", w.DWORD), ("listed", w.DWORD),
                        ("pids", c.c_size_t * MAX_MEMBERS)]
        value, returned = PIDList(), w.DWORD()
        ok = self.k.QueryInformationJobObject(self.owner._job, 3, c.byref(value),
                                              c.sizeof(value), c.byref(returned))
        needed = 8 + value.listed * c.sizeof(c.c_size_t)
        result = {"assigned": value.assigned, "listed": value.listed,
                  "returned_bytes": returned.value, "capacity": MAX_MEMBERS}
        if (not ok or value.listed > MAX_MEMBERS or value.assigned != value.listed
                or not needed <= returned.value <= c.sizeof(value)):
            self.events.put({"operation": "class3_partial", "state": "unknown", "value": result})
            raise OSError(c.get_last_error() if not ok else 0, "Class-3 truncated/changed/invalid; no retry")
        result["pids"] = list(value.pids)[:value.listed]
        return result

    def identity(self, handle, listed_pid):
        # Membership must succeed BEFORE image or parent inspection.
        if not self.call(f"pid{listed_pid}.membership_before", lambda: self.member(handle)):
            raise ValueError("Listed PID is not confirmed in owned Job; do not inspect")
        actual_pid = self.call(f"pid{listed_pid}.handle_pid", lambda: int(self.k.GetProcessId(handle)))
        if actual_pid != listed_pid:
            raise ValueError("Retained handle PID mismatch")
        before = self.call(f"pid{listed_pid}.times_before", lambda: self.times(handle))

        def image():
            buffer, length = c.create_unicode_buffer(32768), w.DWORD(32768)
            if not self.k.QueryFullProcessImageNameW(handle, 0, buffer, c.byref(length)):
                raise OSError(c.get_last_error(), "QueryFullProcessImageNameW failed")
            return buffer.value

        image_path = []
        def redacted_image():
            path = image()
            image_path.append(path)
            return path_identity(path)
        self.call(f"pid{listed_pid}.image", redacted_image)
        try:
            self.call(f"pid{listed_pid}.image_file", lambda: file_identity(image_path[0]))
        except Exception:
            pass  # Hash unknown is recorded; still collect ancestry/revalidation.

        def parent():
            value, returned = self.PBI(), w.ULONG()
            status = int(self.nt(handle, 0, c.byref(value), c.sizeof(value), c.byref(returned)))
            result = {"ntstatus": status, "returned_bytes": returned.value,
                      "pbi_bytes": c.sizeof(value), "parent_offset": self.PBI.InheritedFromUniqueProcessId.offset}
            if status != 0 or returned.value != c.sizeof(value) or value.UniqueProcessId != listed_pid:
                result["parent_pid"] = None
                result["status"] = "unknown; no access upgrade"
            else:
                result.update(parent_pid=int(value.InheritedFromUniqueProcessId),
                              status="numeric ancestry only; correlate retained Job handles")
            return result

        self.call(f"pid{listed_pid}.parent", parent)
        after = self.call(f"pid{listed_pid}.times_after", lambda: self.times(handle))
        inside = self.call(f"pid{listed_pid}.membership_after", lambda: self.member(handle))
        if before["created"] != after["created"] or not inside:
            raise ValueError("Process identity/membership changed during non-atomic inspection")
        return {"pid": listed_pid, "creation_time": before["created"], "membership_revalidated": True}


def drain(events, report):
    while True:
        try:
            report["observations"].append(events.get_nowait())
        except queue.Empty:
            return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--executable", type=Path, default=Path(getattr(sys, "_base_executable", sys.executable)))
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("Windows-only; no fallback")
    if not args.output.is_absolute() or args.output.exists() or not args.output.parent.is_dir():
        parser.error("Output must be a NEW absolute path in an existing evidence directory")
    root = Path(__file__).resolve().parents[2]
    helper_path = root / "backend/app/workers/ocr_containment.py"
    helper_bytes = helper_path.read_bytes()
    if hashlib.sha256(helper_bytes).hexdigest() != HELPER_SHA256:
        parser.error("Frozen helper hash mismatch; no native launch")
    # Reserve output exclusively before native work; never overwrite prior evidence.
    with args.output.open("x", encoding="utf-8") as output:
        report = {"schema_version": 1, "status": "UNKNOWN", "qualification": "UNAVAILABLE",
                  "native_same_cause_prior_failures": 2, "prior_cleanup_failures": 2,
                  "helper_sha256": HELPER_SHA256, "observations": [], "stop_requests": 0,
                  "scope": "startup-only one gate; no parent-job booleans or post-identity counts",
                  "pre_resume_identity": "unknown; existing accounting_initial only",
                  "snapshots_non_atomic": True}
        owner = observer = confirmer = None
        events = queue.SimpleQueue()
        errors = []
        try:
            report["requested_image"] = file_identity(args.executable)
            scratch = Path(tempfile.mkdtemp(prefix="windows-identity-03-", dir=args.output.parent))
            marker, nonce = scratch / "identity.json", uuid.uuid4().hex
            env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
            env.update(TEMP=str(scratch), TMP=str(scratch), HOME=str(scratch), USERPROFILE=str(scratch))
            argv = [str(args.executable), "-I", "-S", "-c", CHILD, str(marker), nonce]
            report.update(argv=[path_identity(args.executable), "-I", "-S", "-c", "<fixed identity marker workload>",
                                "<scratch marker>", nonce], environment_keys=sorted(env), scratch_basename=scratch.name,
                          memory_limit=MEMORY_LIMIT, observation_seconds=OBSERVE_SECONDS,
                          containment_tail_seconds=STOP_SECONDS)
            spec = importlib.util.spec_from_file_location("frozen_containment", helper_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # No extra pre-ownership native query. Existing launcher setup only.
            owner = module.launch_contained(argv, env=env, cwd=str(scratch), memory_limit_bytes=MEMORY_LIMIT)
            report["owned_pid"] = owner.pid
            report["accounting_initial"] = owner.containment_info.get("accounting_initial")
            report["effective_limits"] = dict(owner.containment_info)
            deadline = time.monotonic() + OBSERVE_SECONDS

            def observe():
                try:
                    queries = Queries(owner, events, deadline)
                    facts = None
                    # Reserve observation time for counts even if startup marker never arrives.
                    marker_deadline = deadline - 2.0
                    try:
                        while not marker.exists() and time.monotonic() < marker_deadline:
                            time.sleep(0.01)
                        if not marker.exists():
                            raise TimeoutError("No child identity marker")
                        with marker.open("rb") as stream:
                            data = stream.read(8193)
                        if len(data) > 8192:
                            raise ValueError("Oversized self-report")
                        facts = json.loads(data)
                        if facts.get("nonce") != nonce:
                            facts = None
                            raise ValueError("Self-report nonce mismatch")
                    except Exception as error:
                        errors.append({"phase": "self_report", **error_identity(error)})
                    # Critical count evidence precedes all optional identity/file queries.
                    try:
                        queries.call("class1_live", queries.accounting)
                    except Exception as error:
                        errors.append({"phase": "class1_live", **error_identity(error)})
                    pids = []
                    try:
                        pids = queries.call("class3_live", queries.pids)["pids"]
                    except Exception as error:
                        errors.append({"phase": "class3_live", **error_identity(error)})
                    try:
                        queries.call("direct_identity", lambda: queries.identity(owner._handle, owner.pid))
                    except Exception as error:
                        errors.append({"phase": "direct_identity", **error_identity(error)})
                    if facts is not None:
                        facts["pid_in_job_snapshot"] = facts.get("pid") in pids
                        events.put({"operation": "child_self_report", "state": "returned", "value": facts})
                    for pid in pids:
                        if pid == owner.pid:
                            continue
                        handle = None
                        try:
                            def open_member():
                                value = queries.k.OpenProcess(0x1000 | 0x00100000, False, pid)
                                if not value:
                                    raise OSError(c.get_last_error(), "Owned member inaccessible; no retry")
                                return value
                            handle = queries.call(f"pid{pid}.open", open_member)
                            queries.call(f"pid{pid}.identity", lambda: queries.identity(handle, pid))
                        except Exception as error:
                            errors.append({"phase": "member_identity", "pid": pid, **error_identity(error)})
                        finally:
                            if handle:
                                queries.k.CloseHandle(handle)
                except BaseException as error:
                    errors.append({"phase": "observation", **error_identity(error)})

            observer = threading.Thread(target=observe, name="owned-job-identity", daemon=True)
            observer.start()
            observer.join(timeout=max(0.0, deadline-time.monotonic()))
        except BaseException as error:
            report["primary_error"] = {**error_identity(error),
                "cleanup_confirmed": getattr(error, "cleanup_confirmed", False),
                "workload_started": getattr(error, "workload_started", True),
                "cleanup_seconds": getattr(error, "cleanup_seconds", None),
                "cleanup_accounting": getattr(error, "cleanup_accounting", None)}
        finally:
            if owner is not None:
                # Sole stop owner. NO helper.stop()/poll()/memory_exceeded() here.
                # Termination does not acquire observer locks or perform pre-kill queries.
                start = time.monotonic()
                tail_deadline = start + STOP_SECONDS
                report["stop_requests"] = 1
                closed = False
                try:
                    issued = bool(owner._api.kernel.TerminateJobObject(owner._job, 1))
                    report["termination_issued"] = issued
                    if not issued:
                        report["termination_winerror"] = c.get_last_error()
                    remaining_ms = max(0, int((tail_deadline-time.monotonic()) * 1000))
                    wait_result = owner._api.kernel.WaitForSingleObject(owner._handle, remaining_ms)
                    direct_stopped = wait_result == 0
                    report.update(direct_process_stopped=direct_stopped, direct_wait_result=wait_result)
                    confirmation = {}
                    if observer is None or not observer.is_alive():
                        def confirm():
                            try:
                                q = Queries(owner, events, tail_deadline)
                                while time.monotonic() < tail_deadline:
                                    confirmation.update(q.call("class1_after_stop", q.accounting))
                                    if confirmation.get("values", {}).get("ActiveProcesses") == 0:
                                        break
                                    time.sleep(min(0.01, max(0.0, tail_deadline-time.monotonic())))
                            except BaseException as error:
                                errors.append({"phase": "stop_confirmation", **error_identity(error)})
                        confirmer = threading.Thread(target=confirm, name="owned-job-empty", daemon=True)
                        confirmer.start()
                        confirmer.join(timeout=max(0.0, tail_deadline-time.monotonic()))
                    query_alive = ((observer is not None and observer.is_alive()) or
                                   (confirmer is not None and confirmer.is_alive()))
                    proven = bool(issued and direct_stopped and not query_alive and
                                  confirmation.get("values", {}).get("ActiveProcesses") == 0)
                    report.update(cleanup_confirmed=proven, query_alive=query_alive)
                    if proven:
                        owner._stopped = True  # Native proof; close() must never stop again.
                        owner.close()
                        closed = True
                except BaseException as error:
                    errors.append({"phase": "cleanup", **error_identity(error)})
                finally:
                    report["containment_elapsed"] = time.monotonic()-start
                    if not closed:
                        _RETAINED.append((owner, observer, confirmer))
                        report["quarantine"] = "handles retained until harness exit; unresolved; no next launch"
            drain(events, report)
            report["errors"] = list(errors)
            identities = [item["value"] for item in report["observations"]
                          if item.get("state") == "returned" and
                          (item["operation"] == "direct_identity" or item["operation"].endswith(".identity"))]
            for item in report["observations"]:
                if item.get("operation") == "child_self_report":
                    item["value"]["pid_matches_retained_verified_identity"] = any(
                        identity["pid"] == item["value"].get("pid") for identity in identities)
            live = [item.get("value", {}) for item in report["observations"]
                    if item.get("operation") == "class1_live" and item.get("state") == "returned"]
            pidlists = [item.get("value", {}) for item in report["observations"]
                        if item.get("operation") == "class3_live" and item.get("state") == "returned"]
            # Successful API return is not necessarily known/stable identity evidence.
            identity_unknown = any(
                item.get("state") == "unknown" or
                (item.get("operation", "").endswith(".parent") and
                 item.get("value", {}).get("parent_pid") is None) or
                (item.get("operation", "").endswith(".image_file") and
                 item.get("value", {}).get("stable_file_identity") is not True)
                for item in report["observations"])
            report["identity_complete"] = bool(identities) and not identity_unknown
            if any(item.get("values", {}).get("ActiveProcesses", 0) > 1 for item in live) or any(
                    item.get("listed", 0) > 1 for item in pidlists):
                report.update(status="FAIL_SAME_CAUSE_PAUSE", native_same_cause_failures=3)
            elif (len(live) == 1 and len(pidlists) == 1
                  and live[0].get("values", {}).get("ActiveProcesses") == 1
                  and pidlists[0].get("listed") == pidlists[0].get("assigned") == 1
                  and pidlists[0].get("pids") == [report.get("owned_pid")]
                  and not errors and "primary_error" not in report
                  and report.get("cleanup_confirmed")
                  and report["identity_complete"]
                  and report.get("requested_image", {}).get("stable_file_identity") is True
                  and any(item.get("operation") == "child_self_report" and
                          item["value"].get("pid_in_job_snapshot") and
                          item["value"].get("pid") == report.get("owned_pid") and
                          item["value"].get("pid_matches_retained_verified_identity")
                          for item in report["observations"])):
                report["status"] = "NONREPRO_NOT_QUALIFIED"
            report["next_action"] = "pause/review; no automatic retry"
            try:
                serialized = json.dumps(report, indent=2)
            except BaseException as error:
                # Preserve primary/cause classification even if optional payload serialization fails.
                serialized = json.dumps({"status": report["status"], "qualification": "UNAVAILABLE",
                    "primary_error": report.get("primary_error"), "errors": list(errors),
                    "serialization_error": error_identity(error), "stop_requests": report["stop_requests"],
                    "cleanup_confirmed": report.get("cleanup_confirmed", False)})
            try:
                output.write(serialized + "\n")
                output.flush()
            except BaseException as error:
                # Disk failure cannot be made durable here; parent capture retains the redacted report.
                print(serialized, file=sys.stderr)
                print(json.dumps({"evidence_write_error": error_identity(error)}), file=sys.stderr)
    return 1 if report["status"] == "FAIL_SAME_CAUSE_PAUSE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
