"""Owned OCR process containment; no DB, configuration or provider imports.

The public entry point is ``launch_contained``.  The caller supplies an absolute
executable/script, an explicitly allowlisted environment, and a clean cwd.  This
module never merges that environment with ``os.environ`` and never invokes a
shell.  The runner owns productive deadlines and the framed stdin/stdout protocol.

Linux prerequisite: one dedicated runner in an ALREADY restricted, read-only
cgroup-v2 container namespace.  For example the parent may explicitly launch its
isolated runtime with --memory=2g --memory-swap=2g.  Docker defaults do not qualify.
The existing memory.max charges the parent, DB threads, child and descendants:
this is a stronger total-charge bound, not isolated child RSS attribution.  An
OOM may kill the parent itself; recovery then belongs to the durable job lease.
No cgroup, delegation, privilege, host service or security setting is changed.

Windows uses suspended creation, a non-breakaway Job with at most one process,
and a queried hard working-set maximum before resuming the primary thread.  The
Job private-commit limit is defense in depth, NOT the RSS guarantee.  Effective
limits are rechecked by poll()/memory_exceeded(); the caller MUST call the latter
before accepting output.  This is an implementation candidate, not native/profile
qualification.  Job hard-limit completion notifications are best-effort: absence
of a message is not proof that no allocator call was denied.  Native failure
handling and unchanged hard-limit continuity require separate qualification.

stop(deadline) uses an absolute MONOTONIC containment deadline, never a new work
budget.  False means quarantine: keep the object referenced and do not claim tree
cleanup.  close() does not replace stop(), and refuses to discard unproven owned
work.  Launch/read/OS calls themselves have no hard scheduling-time guarantee;
the parent must account for launch-in-progress in its supervision lifecycle.
Linux True proves the direct child was reaped and no non-baseline runnable
cgroup work remains.  cgroup.procs can omit zombies; it does NOT prove that the
container init has reaped every orphaned grandchild zombie.
"""
from __future__ import annotations

import os
import math
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import BinaryIO, Sequence


MAX_MEMORY_BYTES = 2 * 1024 * 1024 * 1024
_CGROUP_ROOT = Path("/sys/fs/cgroup")
_PROC_ROOT = Path("/proc")
_MAX_CONTROL_BYTES = 65_536


class ContainmentUnavailable(RuntimeError):
    """Unavailable does not imply safe cleanup unless explicitly proved.

    cleanup_confirmed only describes workload ownership, never DB settlement.
    workload_started defaults True: unknown must not authorize safe failure.
    The parent must separately consume its launch slot and resolve mutations.
    """

    def __init__(self, message, *, cleanup_confirmed=False, workload_started=True):
        super().__init__(message)
        self.cleanup_confirmed = cleanup_confirmed is True
        self.workload_started = workload_started is not False


def _wrap_unavailable(message, cause):
    error = ContainmentUnavailable(
        message, cleanup_confirmed=getattr(cause, "cleanup_confirmed", False),
        workload_started=getattr(cause, "workload_started", True))
    for name in ("winerror", "cleanup_seconds", "cleanup_accounting"):
        if hasattr(cause, name):
            setattr(error, name, getattr(cause, name))
    return error


def _read_control(path: Path) -> str:
    with path.open("r", encoding="ascii") as stream:
        value = stream.read(_MAX_CONTROL_BYTES + 1)
    if len(value) > _MAX_CONTROL_BYTES:
        raise ContainmentUnavailable("Oversized containment control file")
    return value.strip()


def _process_identity(pid: int) -> tuple[int, int, int, int]:
    """Return (pid, starttime, ppid, pgrp), tolerating ')' in the comm field."""
    raw = _read_control(_PROC_ROOT / str(pid) / "stat")
    fields = raw[raw.rindex(")") + 2:].split()
    return pid, int(fields[19]), int(fields[1]), int(fields[2])


def _members() -> dict[int, tuple[int, int, int, int]]:
    members = {}
    for value in _read_control(_CGROUP_ROOT / "cgroup.procs").splitlines():
        pid = int(value)
        if pid <= 0:
            raise ContainmentUnavailable("Cgroup contains processes outside the PID namespace")
        try:
            members[pid] = _process_identity(pid)
        except FileNotFoundError:
            # Exited between the cgroup snapshot and the /proc read.
            continue
    return members


def _events() -> dict[str, int]:
    values = {}
    for line in _read_control(_CGROUP_ROOT / "memory.events").splitlines():
        key, value = line.split()
        values[key] = int(value)
    if not {"max", "oom", "oom_kill"} <= values.keys() or any(v < 0 for v in values.values()):
        raise ContainmentUnavailable("Missing/invalid cgroup memory events")
    return values


def _validate_cgroup(limit: int) -> None:
    # Deliberately support only the qualified namespace-root container layout.
    # Do not guess host paths from untrusted paths or try alternate mounts.
    if _read_control(_PROC_ROOT / "self" / "cgroup") != "0::/":
        raise ContainmentUnavailable("Dedicated cgroup-v2 namespace root required")
    mounts = _read_control(_PROC_ROOT / "self" / "mountinfo").splitlines()
    mount = next((line.split() for line in mounts
                  if len(line.split()) > 6 and line.split()[4] == str(_CGROUP_ROOT)), None)
    if mount is None or "-" not in mount:
        raise ContainmentUnavailable("No cgroup-v2 containment mount")
    separator = mount.index("-")
    if mount[separator + 1] != "cgroup2" or "ro" not in mount[5].split(","):
        raise ContainmentUnavailable("An existing read-only cgroup-v2 mount is required")
    if _read_control(_CGROUP_ROOT / "cgroup.type") != "domain":
        raise ContainmentUnavailable("A domain memory cgroup is required")
    maximum = _read_control(_CGROUP_ROOT / "memory.max")
    if maximum == "max" or not 0 < int(maximum) <= limit:
        raise ContainmentUnavailable("Existing cgroup memory.max exceeds requested bound")
    # No delegated descendants/alternative writable hierarchy for this narrow
    # supported layout.  Ordinary process descendants inherit the same boundary.
    if any(entry.is_dir() for entry in _CGROUP_ROOT.iterdir()):
        raise ContainmentUnavailable("Dedicated leaf cgroup required")


def _dedicated_baseline() -> dict[int, tuple[int, int, int, int]]:
    baseline = _members()
    ancestors = set()
    pid = os.getpid()
    while pid > 0 and pid not in ancestors:
        ancestors.add(pid)
        pid = _process_identity(pid)[2]
    if os.getpid() not in baseline or set(baseline) - ancestors:
        raise ContainmentUnavailable("Dedicated runner cgroup contains unrelated workloads")
    return baseline


class ContainedProcess:
    """Public subprocess-like handle; construct only through launch_contained.

    memory_exceeded() is sticky cgroup pressure/denial evidence, NOT proof that
    this child caused it.  Parent allocation is charged to the same boundary.
    The max counter catches limit pressure even when allocation is denied or
    reclaim succeeds without an OOM kill.  A read/configuration failure raises
    ContainmentUnavailable, never returns a falsely reassuring False.

    poll() deliberately leaves the direct child unreaped until stop().  Keeping
    its PID reserved prevents a recycled process-group ID from being signalled.
    No other code may waitpid/reap this child.  Session-escaping descendants are
    detected as residual cgroup members: they cause False/quarantine, not an
    unsafe signal to a guessed PID or to the runner's own cgroup/process group.
    """

    stdin: BinaryIO
    stdout: BinaryIO
    pid: int

    def __init__(self, process: subprocess.Popen, baseline, events, limit, identity):
        self._process = process
        self.stdin = process.stdin
        self.stdout = process.stdout
        self.pid = process.pid
        self._baseline = baseline
        self._events_before = events
        self._limit = limit
        self._exceeded = False
        self._stopped = False
        self._closed = False
        self._kill_sent = False
        self._exit_code = None
        self.containment_info = {
            "kind": "linux-cgroup-v2", "scope": "dedicated-runner-container",
            **identity,
            "requested_limit": limit, "child_attribution": False,
            "cgroup_membership": "0::/", "cgroup_mount": str(_CGROUP_ROOT),
            "events_before": dict(events), "events_current": dict(events),
            "cleanup_scope": "direct-child-reaped; no residual runnable cgroup work",
        }

    def poll(self) -> int | None:
        if self._stopped or self._exit_code is not None:
            return self._exit_code
        try:
            status = os.waitid(os.P_PID, self.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        except ChildProcessError as exc:
            raise ContainmentUnavailable("Owned process was reaped outside containment") from exc
        if status is not None:
            self._exit_code = status.si_status if status.si_code == os.CLD_EXITED else -status.si_status
        return self._exit_code

    def memory_exceeded(self) -> bool:
        if self._closed:
            raise ContainmentUnavailable("Containment observation was closed")
        try:
            _validate_cgroup(self._limit)
            current = _events()
            self.containment_info["events_current"] = dict(current)
            self.containment_info["events_delta"] = {
                key: current[key] - self._events_before.get(key, 0) for key in current
            }
            for key in ("max", "oom", "oom_kill"):
                if current[key] < self._events_before[key]:
                    raise ContainmentUnavailable("Containment memory counters reset")
                if current[key] > self._events_before[key]:
                    self._exceeded = True
        except (OSError, ValueError, IndexError) as exc:
            raise ContainmentUnavailable("Cannot observe existing memory containment") from exc
        return self._exceeded

    def stop(self, deadline: float) -> bool:
        if not isinstance(deadline, (int, float)) or not math.isfinite(deadline):
            return False
        if self._stopped:
            return True
        if self._closed:
            return False
        try:
            if not self._kill_sent:
                # waitid(WNOWAIT), even after normal exit, keeps this owned PID
                # reserved.  A third-party reaper invalidates our signalling proof.
                os.waitid(os.P_PID, self.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                if os.getpgid(self.pid) != self.pid or self.pid == os.getpgrp():
                    return False
                os.killpg(self.pid, signal.SIGKILL)
                self._kill_sent = True
            while True:
                try:
                    self._exit_code = self._process.wait(timeout=0)
                except subprocess.TimeoutExpired:
                    pass
                remaining = _members()
                residual = {
                    pid for pid, identity in remaining.items()
                    if self._baseline.get(pid) != identity
                }
                if self._process.returncode is not None and not residual:
                    self._stopped = True
                    return True
                delay = deadline - time.monotonic()
                if delay <= 0:
                    return False
                time.sleep(min(0.01, delay))
        except (OSError, ValueError, IndexError, ContainmentUnavailable):
            return False

    def close(self) -> None:
        if self._closed:
            return
        if not self._stopped:
            raise ContainmentUnavailable("Unproven tree cleanup; retain handle and quarantine")
        # Runner must join its receiver before closing the stream it owns.
        self.stdin.close()
        self.stdout.close()
        self._closed = True


class _WindowsAPI:
    """Explicit pointer-sized signatures; loaded only on Windows."""

    def __init__(self):
        import ctypes as c
        from ctypes import wintypes as w

        self.c, self.w = c, w
        self.kernel = c.WinDLL("kernel32", use_last_error=True)
        size = c.c_size_t

        class BasicLimits(c.Structure):
            _fields_ = [("PerProcessUserTimeLimit", c.c_longlong),
                        ("PerJobUserTimeLimit", c.c_longlong), ("LimitFlags", w.DWORD),
                        ("MinimumWorkingSetSize", size), ("MaximumWorkingSetSize", size),
                        ("ActiveProcessLimit", w.DWORD), ("Affinity", size),
                        ("PriorityClass", w.DWORD), ("SchedulingClass", w.DWORD)]

        class IOCounters(c.Structure):
            _fields_ = [(name, c.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class ExtendedLimits(c.Structure):
            _fields_ = [("BasicLimitInformation", BasicLimits), ("IoInfo", IOCounters),
                        ("ProcessMemoryLimit", size), ("JobMemoryLimit", size),
                        ("PeakProcessMemoryUsed", size), ("PeakJobMemoryUsed", size)]

        class CompletionPort(c.Structure):
            _fields_ = [("CompletionKey", c.c_void_p), ("CompletionPort", w.HANDLE)]

        class Accounting(c.Structure):
            _fields_ = [(name, c.c_longlong) for name in (
                "TotalUserTime", "TotalKernelTime", "ThisPeriodTotalUserTime",
                "ThisPeriodTotalKernelTime")] + [(name, w.DWORD) for name in (
                "TotalPageFaultCount", "TotalProcesses", "ActiveProcesses",
                "TotalTerminatedProcesses")]

        class StartupInfo(c.Structure):
            _fields_ = [("cb", w.DWORD), ("lpReserved", w.LPWSTR),
                        ("lpDesktop", w.LPWSTR), ("lpTitle", w.LPWSTR)] + [
                (name, w.DWORD) for name in (
                    "dwX", "dwY", "dwXSize", "dwYSize", "dwXCountChars",
                    "dwYCountChars", "dwFillAttribute", "dwFlags")] + [
                ("wShowWindow", w.WORD), ("cbReserved2", w.WORD),
                ("lpReserved2", c.POINTER(w.BYTE)), ("hStdInput", w.HANDLE),
                ("hStdOutput", w.HANDLE), ("hStdError", w.HANDLE)]

        class StartupInfoEx(c.Structure):
            _fields_ = [("StartupInfo", StartupInfo), ("lpAttributeList", c.c_void_p)]

        class ProcessInfo(c.Structure):
            _fields_ = [("hProcess", w.HANDLE), ("hThread", w.HANDLE),
                        ("dwProcessId", w.DWORD), ("dwThreadId", w.DWORD)]

        self.ExtendedLimits = ExtendedLimits
        self.CompletionPort = CompletionPort
        self.Accounting = Accounting
        if (c.sizeof(w.DWORD) != 4 or c.sizeof(Accounting) != 48
                or Accounting.ActiveProcesses.offset != 40):
            raise ContainmentUnavailable("Windows basic accounting ABI layout mismatch")
        self.StartupInfoEx = StartupInfoEx
        self.ProcessInfo = ProcessInfo
        self.layouts = {
            "basic_accounting_bytes": c.sizeof(Accounting),
            "basic_limits_bytes": c.sizeof(BasicLimits),
            "extended_limits_bytes": c.sizeof(ExtendedLimits),
            "startup_info_bytes": c.sizeof(StartupInfo),
            "startup_info_ex_bytes": c.sizeof(StartupInfoEx),
            "process_info_bytes": c.sizeof(ProcessInfo),
            "pointer_bytes": c.sizeof(c.c_void_p), "dword_bytes": c.sizeof(w.DWORD),
        }
        signatures = {
            "CreateJobObjectW": ([c.c_void_p, w.LPCWSTR], w.HANDLE),
            "SetInformationJobObject": ([w.HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL),
            "QueryInformationJobObject": (
                [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)], w.BOOL),
            "AssignProcessToJobObject": ([w.HANDLE, w.HANDLE], w.BOOL),
            "IsProcessInJob": ([w.HANDLE, w.HANDLE, c.POINTER(w.BOOL)], w.BOOL),
            "TerminateJobObject": ([w.HANDLE, w.UINT], w.BOOL),
            "CreateIoCompletionPort": ([w.HANDLE, w.HANDLE, size, w.DWORD], w.HANDLE),
            "GetQueuedCompletionStatus": (
                [w.HANDLE, c.POINTER(w.DWORD), c.POINTER(size),
                 c.POINTER(c.c_void_p), w.DWORD], w.BOOL),
            "InitializeProcThreadAttributeList": (
                [c.c_void_p, w.DWORD, w.DWORD, c.POINTER(size)], w.BOOL),
            "UpdateProcThreadAttribute": (
                [c.c_void_p, w.DWORD, size, c.c_void_p, size,
                 c.c_void_p, c.POINTER(size)], w.BOOL),
            "DeleteProcThreadAttributeList": ([c.c_void_p], None),
            "CreateProcessW": (
                [w.LPCWSTR, w.LPWSTR, c.c_void_p, c.c_void_p, w.BOOL, w.DWORD,
                 c.c_void_p, w.LPCWSTR, c.POINTER(StartupInfoEx),
                 c.POINTER(ProcessInfo)], w.BOOL),
            "SetProcessWorkingSetSizeEx": ([w.HANDLE, size, size, w.DWORD], w.BOOL),
            "GetProcessWorkingSetSizeEx": (
                [w.HANDLE, c.POINTER(size), c.POINTER(size), c.POINTER(w.DWORD)], w.BOOL),
            "ResumeThread": ([w.HANDLE], w.DWORD),
            "WaitForSingleObject": ([w.HANDLE, w.DWORD], w.DWORD),
            "GetExitCodeProcess": ([w.HANDLE, c.POINTER(w.DWORD)], w.BOOL),
            "TerminateProcess": ([w.HANDLE, w.UINT], w.BOOL),
            "CloseHandle": ([w.HANDLE], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = args, result

    def require(self, success, operation):
        if not success:
            # No argv/environment/credentials in diagnostic messages.
            code = self.c.get_last_error()
            error = ContainmentUnavailable(f"{operation} failed (Windows error {code})")
            error.winerror = code
            raise error


class _WindowsContainedProcess(ContainedProcess):
    _FLAGS = 0x00000008 | 0x00000200 | 0x00002000  # active-process, job-memory, kill-on-close
    _HARDWS_MAX = 0x00000004
    _BREAKAWAY = 0x00000800 | 0x00001000

    def __init__(self, api, job, port, process_handle, pid, stdin, stdout, limit, page):
        self._api, self._job, self._port = api, job, port
        self._handle = process_handle
        self.pid, self.stdin, self.stdout = pid, stdin, stdout
        self._limit, self._page = limit, page
        self._exceeded = False
        self._stopped = self._closed = self._kill_sent = False
        self._exit_code = None
        self._validated = False
        self._live_validations = 0
        version = sys.getwindowsversion()
        self.containment_info = {
            "kind": "windows-job-hard-working-set", "scope": "one-process-no-descendants",
            "requested_limit": limit, "page_size": page,
            "allocation_notifications": "best-effort; absence is not denial-proof",
            "qualification": "candidate; native continuity and failure-path evidence required",
            "os_facts": {"major": version.major, "minor": version.minor,
                         "build": version.build, "platform": version.platform,
                         "platform_version": list(version.platform_version)},
            "python_version": sys.version, "ctypes_layouts": dict(api.layouts),
        }

    def _accounting(self):
        a = self._api
        result = a.Accounting()
        returned = a.w.DWORD()
        success = a.kernel.QueryInformationJobObject(
            self._job, 1, a.c.byref(result), a.c.sizeof(result), a.c.byref(returned))
        error_code = a.c.get_last_error() if not success else 0
        snapshot = {
            "observed_monotonic": time.monotonic(),
            "query_class": 1, "buffer_bytes": a.c.sizeof(result),
            "returned_bytes": returned.value, "query_succeeded": bool(success),
            "winerror": error_code, "pointer_bytes": a.c.sizeof(a.c.c_void_p),
            "dword_bytes": a.c.sizeof(a.w.DWORD),
            "field_offsets": {name: getattr(a.Accounting, name).offset
                              for name, _ in a.Accounting._fields_},
            "values": {name: getattr(result, name) for name, _ in a.Accounting._fields_},
            "raw_hex": a.c.string_at(a.c.byref(result), a.c.sizeof(result)).hex(),
            "owned_pid": self.pid,
        }
        self.containment_info["accounting_last"] = snapshot
        self.containment_info.setdefault("accounting_initial", snapshot)
        if not success or returned.value != a.c.sizeof(result) or result.ActiveProcesses > 1:
            self.containment_info.setdefault("accounting_first_anomaly", snapshot)
        if not success:
            raise ContainmentUnavailable(f"Query job accounting failed (Windows error {error_code})")
        if returned.value != a.c.sizeof(result):
            raise ContainmentUnavailable("Unexpected basic accounting query length")
        return result

    def _diagnostic_job_pids(self):
        """Independent, bounded class-3 corroboration; never authorizes killing."""
        a = self._api

        class ProcessIds(a.c.Structure):
            _fields_ = [("NumberOfAssignedProcesses", a.w.DWORD),
                        ("NumberOfProcessIdsInList", a.w.DWORD),
                        ("ProcessIdList", a.c.c_size_t * 16)]

        result, returned = ProcessIds(), a.w.DWORD()
        success = a.kernel.QueryInformationJobObject(
            self._job, 3, a.c.byref(result), a.c.sizeof(result), a.c.byref(returned))
        return {
            "query_class": 3, "query_succeeded": bool(success),
            "winerror": a.c.get_last_error() if not success else 0,
            "returned_bytes": returned.value,
            "assigned_processes": result.NumberOfAssignedProcesses,
            "listed_processes": result.NumberOfProcessIdsInList,
            "pids": list(result.ProcessIdList)[:min(16, result.NumberOfProcessIdsInList)],
        }

    def _check_limits(self):
        a = self._api
        limits = a.ExtendedLimits()
        a.require(a.kernel.QueryInformationJobObject(
            self._job, 9, a.c.byref(limits), a.c.sizeof(limits), None), "Query job limits")
        flags = limits.BasicLimitInformation.LimitFlags
        if (flags & self._FLAGS != self._FLAGS or flags & self._BREAKAWAY
                or limits.BasicLimitInformation.ActiveProcessLimit != 1
                or not 0 < limits.JobMemoryLimit <= self._limit):
            raise ContainmentUnavailable("Effective Windows job containment changed")
        active = self._accounting().ActiveProcesses
        if active > 1:
            self.containment_info.setdefault("unexpected_active_process_ids", self._diagnostic_job_pids())
            raise ContainmentUnavailable(
                f"Unexpected active-process count in single-process job: {active}; "
                "see containment_info.accounting_first_anomaly and unexpected_active_process_ids")
        wait = a.kernel.WaitForSingleObject(self._handle, 0)
        if wait == 0:  # Already terminated: the final live query is no longer possible.
            if not self._validated:
                raise ContainmentUnavailable("Process ended before effective-limit validation")
            self.containment_info["live_revalidation_available"] = False
            return
        if wait != 0x00000102:  # WAIT_TIMEOUT means still alive.
            raise ContainmentUnavailable("Cannot query owned process liveness")
        inside = a.w.BOOL()
        a.require(a.kernel.IsProcessInJob(self._handle, self._job, a.c.byref(inside)), "Query job membership")
        minimum, maximum, ws_flags = a.c.c_size_t(), a.c.c_size_t(), a.w.DWORD()
        a.require(a.kernel.GetProcessWorkingSetSizeEx(
            self._handle, a.c.byref(minimum), a.c.byref(maximum), a.c.byref(ws_flags)),
            "Query hard working-set limit")
        if (not inside.value or not ws_flags.value & self._HARDWS_MAX
                or ws_flags.value & 0x8  # HARDWS_MAX_DISABLE
                or not 0 < maximum.value <= self._limit
                or maximum.value % self._page):
            raise ContainmentUnavailable("Effective hard working-set maximum is unavailable/changed")
        self._validated = True
        self._live_validations += 1
        self.containment_info.update(
            effective_working_set_max=maximum.value, effective_working_set_min=minimum.value,
            effective_working_set_flags=ws_flags.value, job_memory_max=limits.JobMemoryLimit,
            job_limit_flags=flags, active_process_limit=1,
            live_revalidation_available=True, live_validation_count=self._live_validations,
        )

    def memory_exceeded(self) -> bool:
        if self.containment_info.get("observation_uncertain"):
            raise ContainmentUnavailable("Previous Windows containment observation is uncertain")
        try:
            return self._observe_memory()
        except ContainmentUnavailable:
            self.containment_info["observation_uncertain"] = True
            raise

    def _observe_memory(self) -> bool:
        if self._closed:
            raise ContainmentUnavailable("Containment observation was closed")
        self._check_limits()
        a = self._api
        # These messages preserve a detected denial after a short allocation has
        # been freed.  They supplement the kernel caps, never establish them.
        for _ in range(1024):
            code, key, overlapped = a.w.DWORD(), a.c.c_size_t(), a.c.c_void_p()
            success = a.kernel.GetQueuedCompletionStatus(
                self._port, a.c.byref(code), a.c.byref(key), a.c.byref(overlapped), 0)
            if not success:
                if a.c.get_last_error() == 258 and not overlapped.value:  # WAIT_TIMEOUT
                    return self._exceeded
                raise ContainmentUnavailable("Windows job notification observation failed")
            if key.value != 1:
                raise ContainmentUnavailable("Unexpected Windows completion identity")
            # ACTIVE_PROCESS_LIMIT, PROCESS_MEMORY_LIMIT, JOB_MEMORY_LIMIT.
            if code.value in {3, 9, 10}:
                self._exceeded = True
        raise ContainmentUnavailable("Windows job notification queue did not drain")

    def poll(self) -> int | None:
        if self._exit_code is not None:
            return self._exit_code
        self.memory_exceeded()
        a = self._api
        state = a.kernel.WaitForSingleObject(self._handle, 0)
        if state == 0x00000102:
            return None
        if state != 0:
            raise ContainmentUnavailable("Cannot observe owned process exit")
        code = a.w.DWORD()
        a.require(a.kernel.GetExitCodeProcess(self._handle, a.c.byref(code)), "Read owned exit code")
        self._exit_code = code.value
        return self._exit_code

    def stop(self, deadline: float) -> bool:
        if not isinstance(deadline, (int, float)) or not math.isfinite(deadline):
            return False
        if self._stopped:
            return True
        if self._closed:
            return False
        a = self._api
        try:
            if not self._kill_sent:
                # Capture effective settings immediately before intentionally
                # terminating the process.  Observation failures must NOT stop
                # the kill; they remain sticky and block result acceptance.
                try:
                    self.memory_exceeded()
                    self.containment_info["validated_before_stop"] = bool(
                        self.containment_info.get("live_revalidation_available"))
                except ContainmentUnavailable:
                    self.containment_info["observation_uncertain"] = True
                a.require(a.kernel.TerminateJobObject(self._job, 1), "Terminate owned job")
                self._kill_sent = True
            while True:
                state = a.kernel.WaitForSingleObject(self._handle, 0)
                if state == 0 and self._accounting().ActiveProcesses == 0:
                    code = a.w.DWORD()
                    a.require(a.kernel.GetExitCodeProcess(self._handle, a.c.byref(code)), "Read stopped exit code")
                    self._exit_code = code.value
                    self._stopped = True
                    return True
                if state not in {0, 0x00000102}:
                    return False
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                time.sleep(min(0.01, remaining))
        except ContainmentUnavailable:
            return False

    def close(self) -> None:
        if self._closed:
            return
        if not self._stopped:
            raise ContainmentUnavailable("Unproven job cleanup; retain handle and quarantine")
        self.stdin.close()
        self.stdout.close()
        for name in ("_handle", "_job", "_port"):
            handle = getattr(self, name)
            if handle:
                self._api.require(self._api.kernel.CloseHandle(handle), "Close owned containment handle")
                setattr(self, name, None)
        self._closed = True


# Failed native setup retains ownership if termination cannot be proved.  This
# never authorizes another launch; callers must quarantine ContainmentUnavailable.
_FAILED_WINDOWS_LAUNCHES = []


def _launch_windows(argv, env, cwd, limit):
    import mmap
    import msvcrt

    try:
        a = _WindowsAPI()
    except (ContainmentUnavailable, OSError, ValueError) as error:
        error.cleanup_confirmed = True  # No native process creation attempted.
        error.workload_started = False
        raise
    c = a.c
    page = mmap.PAGESIZE
    effective = limit - limit % page  # Round DOWN, never above the requested bound.
    if effective < 20 * page:
        raise ContainmentUnavailable("Requested working set is below the Windows minimum",
                                     cleanup_confirmed=True, workload_started=False)
    job = port = None
    info = a.ProcessInfo()
    attrs = None
    initialized = False
    fds = []
    owner = None
    assigned = False
    resume_attempted = False
    parent_in = parent_out = None
    try:
        job = a.kernel.CreateJobObjectW(None, None)  # unnamed, non-inheritable
        a.require(job, "Create owned job")
        limits = a.ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = _WindowsContainedProcess._FLAGS
        limits.BasicLimitInformation.ActiveProcessLimit = 1
        limits.JobMemoryLimit = effective
        a.require(a.kernel.SetInformationJobObject(job, 9, c.byref(limits), c.sizeof(limits)), "Set owned job limits")
        port = a.kernel.CreateIoCompletionPort(a.w.HANDLE(-1), None, 0, 1)
        a.require(port, "Create owned job notification port")
        associate = a.CompletionPort(c.c_void_p(1), port)
        a.require(a.kernel.SetInformationJobObject(job, 7, c.byref(associate), c.sizeof(associate)), "Attach job notifications")

        child_in, parent_in_fd = os.pipe()
        fds.extend((child_in, parent_in_fd))
        parent_out_fd, child_out = os.pipe()
        fds.extend((parent_out_fd, child_out))
        null_fd = os.open(os.devnull, os.O_WRONLY)
        fds.append(null_fd)
        child_fds = (child_in, child_out, null_fd)
        handles = (a.w.HANDLE * 3)(*(msvcrt.get_osfhandle(fd) for fd in child_fds))
        for fd in child_fds:
            os.set_inheritable(fd, True)
        size = c.c_size_t()
        a.kernel.InitializeProcThreadAttributeList(None, 1, 0, c.byref(size))
        if not size.value:
            raise ContainmentUnavailable("Cannot size inherited-handle whitelist")
        attrs = c.create_string_buffer(size.value)
        a.require(a.kernel.InitializeProcThreadAttributeList(attrs, 1, 0, c.byref(size)), "Initialize handle whitelist")
        initialized = True
        a.require(a.kernel.UpdateProcThreadAttribute(
            attrs, 0, 0x00020002, c.cast(handles, c.c_void_p), c.sizeof(handles), None, None),
            "Restrict inherited handles")
        startup = a.StartupInfoEx()
        startup.StartupInfo.cb = c.sizeof(startup)
        startup.StartupInfo.dwFlags = 0x00000100  # STARTF_USESTDHANDLES
        startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = handles
        startup.lpAttributeList = c.cast(attrs, c.c_void_p)
        command = c.create_unicode_buffer(subprocess.list2cmdline(list(argv)))
        environment = c.create_unicode_buffer(
            "\0".join(f"{key}={value}" for key, value in sorted(env.items(), key=lambda item: item[0].upper())) + "\0\0")
        # CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT | DETACHED_PROCESS |
        # EXTENDED_STARTUPINFO_PRESENT.  No BREAKAWAY_FROM_JOB privilege request.
        flags = 0x4 | 0x400 | 0x8 | 0x00080000
        a.require(a.kernel.CreateProcessW(
            argv[0], command, None, None, True, flags, c.cast(environment, c.c_void_p),
            cwd, c.byref(startup), c.byref(info)), "Create suspended owned process")
        for fd in child_fds:
            os.close(fd)
            fds.remove(fd)
        a.require(a.kernel.AssignProcessToJobObject(job, info.hProcess), "Assign suspended process to job")
        assigned = True
        # MAX_ENABLE plus MIN_DISABLE: do not pin a minimum resident allocation.
        a.require(a.kernel.SetProcessWorkingSetSizeEx(
            info.hProcess, 20 * page, effective, 0x4 | 0x2), "Set hard working-set maximum")
        parent_in = os.fdopen(parent_in_fd, "wb", buffering=0)
        fds.remove(parent_in_fd)
        parent_out = os.fdopen(parent_out_fd, "rb", buffering=0)
        fds.remove(parent_out_fd)
        owner = _WindowsContainedProcess(
            a, job, port, info.hProcess, info.dwProcessId, parent_in, parent_out, limit, page)
        owner._check_limits()  # Must prove effective cap and ownership BEFORE work.
        # Once resume is attempted we conservatively assume useful work could
        # have run, even if its return value or later setup fails.
        resume_attempted = True
        if a.kernel.ResumeThread(info.hThread) != 1:
            raise ContainmentUnavailable("Primary thread did not have exactly one suspended count")
        a.require(a.kernel.CloseHandle(info.hThread), "Close owned primary thread handle")
        info.hThread = None
        return owner
    except BaseException as error:
        # No productive execution unless every cap was installed.  Cleanup is
        # bounded; any unproven native ownership remains referenced for quarantine.
        error.cleanup_confirmed = not bool(info.hProcess)
        error.workload_started = resume_attempted
        if info.hProcess:
            cleanup_started = time.monotonic()
            cleanup_deadline = cleanup_started + 2.0
            if assigned:
                a.kernel.TerminateJobObject(job, 1)
            else:
                a.kernel.TerminateProcess(info.hProcess, 1)
            # One bounded containment-only tail, not a retry of launch/native
            # setup and not useful execution. Preserve the original exception
            # and its already captured Windows error before doing cleanup.
            terminated = False
            while True:
                direct_stopped = a.kernel.WaitForSingleObject(info.hProcess, 0) == 0
                if assigned:
                    accounting, returned = a.Accounting(), a.w.DWORD()
                    queried = a.kernel.QueryInformationJobObject(
                        job, 1, c.byref(accounting), c.sizeof(accounting), c.byref(returned))
                    error.cleanup_accounting = {
                        "query_succeeded": bool(queried), "returned_bytes": returned.value,
                        "active_processes": accounting.ActiveProcesses,
                        "direct_process_stopped": direct_stopped,
                    }
                    whole_job_stopped = bool(queried and returned.value == c.sizeof(accounting)
                                             and accounting.ActiveProcesses == 0)
                else:
                    # No successful Job assignment means there is no whole-Job
                    # proof. Even a stopped suspended direct process is not
                    # promoted to the stronger cleanup-confirmed assertion.
                    whole_job_stopped = False
                if direct_stopped and whole_job_stopped:
                    terminated = True
                    break
                if direct_stopped and not assigned:
                    break
                remaining = cleanup_deadline - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(0.01, remaining))
            error.cleanup_confirmed = terminated
            error.cleanup_seconds = time.monotonic() - cleanup_started
            if not terminated:
                _FAILED_WINDOWS_LAUNCHES.append((a, job, port, info.hProcess, info.hThread, owner))
                job = port = info.hProcess = info.hThread = None
        if parent_in is not None:
            parent_in.close()
        if parent_out is not None:
            parent_out.close()
        for handle in (info.hThread, info.hProcess, job, port):
            if handle:
                a.kernel.CloseHandle(handle)
        raise
    finally:
        if initialized:
            a.kernel.DeleteProcThreadAttributeList(attrs)
        for fd in fds:
            os.close(fd)


def launch_contained(
    argv: Sequence[str], *, env: dict[str, str], cwd: str, memory_limit_bytes: int,
) -> ContainedProcess:
    """Launch only under pre-existing continuous containment or raise.

    There is deliberately no platform fallback, shell, inherited environment,
    process sampler qualification, new limit/delegation write or hidden privilege
    acquisition. Linux preflight precedes creation; Windows effective-limit
    checks precede resuming the suspended process.  On Windows argv[0] must be
    the trusted REAL executable, not a venv redirector which creates a second
    process.  The caller supplies explicitly trusted package paths separately.
    """
    if sys.platform == "win32" and _FAILED_WINDOWS_LAUNCHES:
        # Must precede even harmless argument validation: an earlier workload
        # still has unproven ownership regardless of this call's arguments.
        raise ContainmentUnavailable("Prior Windows launch cleanup is unproven; runner quarantined")
    if type(memory_limit_bytes) is not int or not 0 < memory_limit_bytes <= MAX_MEMORY_BYTES:
        raise ContainmentUnavailable("Memory limit must be an integer in 1..2GiB", cleanup_confirmed=True, workload_started=False)
    if (isinstance(argv, (str, bytes)) or not argv
            or any(not isinstance(arg, str) or "\0" in arg for arg in argv)
            or not os.path.isabs(argv[0])):
        raise ContainmentUnavailable("An absolute executable and explicit argv are required", cleanup_confirmed=True, workload_started=False)
    if (type(env) is not dict or any(not isinstance(k, str) or not isinstance(v, str)
                                   or not k or "=" in k or "\0" in k or "\0" in v
                                   for k, v in env.items())):
        raise ContainmentUnavailable("An explicit string environment is required", cleanup_confirmed=True, workload_started=False)
    if not isinstance(cwd, str) or not os.path.isabs(cwd):
        raise ContainmentUnavailable("An absolute clean working directory is required", cleanup_confirmed=True, workload_started=False)
    if sys.platform == "win32":
        if len({name.upper() for name in env}) != len(env):
            raise ContainmentUnavailable("Duplicate case-insensitive environment keys", cleanup_confirmed=True, workload_started=False)
        try:
            return _launch_windows(argv, env, cwd, memory_limit_bytes)
        except (OSError, ValueError) as exc:
            raise _wrap_unavailable("Windows native containment setup failed", exc) from exc
    if sys.platform != "linux" or not hasattr(os, "WNOWAIT"):
        raise ContainmentUnavailable("No qualified containment on this platform", cleanup_confirmed=True, workload_started=False)
    try:
        _validate_cgroup(memory_limit_bytes)
        baseline = _dedicated_baseline()
        before = _events()
        identity = {
            "memory_max": int(_read_control(_CGROUP_ROOT / "memory.max")),
            "memory_swap_max": _read_control(_CGROUP_ROOT / "memory.swap.max"),
        }
    except ContainmentUnavailable as exc:
        exc.cleanup_confirmed = True  # Prelaunch-only call site, not observation.
        exc.workload_started = False
        raise
    except (OSError, ValueError, IndexError) as exc:
        raise ContainmentUnavailable("Existing isolated memory containment is unavailable", cleanup_confirmed=True, workload_started=False) from exc
    try:
        process = subprocess.Popen(
            list(argv), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, cwd=cwd, env=dict(env), shell=False,
            close_fds=True, start_new_session=True, bufsize=0,
        )
    except OSError as exc:
        # CPython Popen cleans up/reaps failed exec children before raising here.
        raise ContainmentUnavailable("Contained process creation failed", cleanup_confirmed=True, workload_started=False) from exc
    return ContainedProcess(process, baseline, before, memory_limit_bytes, identity)
