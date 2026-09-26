"""Parent-owned OCR authority and independently supervised DB-free subprocess."""
from __future__ import annotations
import json
import os
from pathlib import Path
import queue
import sys
import sysconfig
import tempfile
import threading
import time

from sqlalchemy.exc import DBAPIError
from backend.app.config import get_settings
from backend.app.db import SessionFactory
from backend.app.services.ocr_types import AdapterOutputInvalid, LostFence, OutcomeUnknown
from backend.app.services.verification_jobs import VerificationJobService
from backend.app.services.verification_results import write_adapter_results
from backend.app.storage.local import LocalStorage, ROOT as STORAGE_BASE
from backend.app.workers.ocr_runtime import DeadlinePolicy, OneOperation, load_metadata
from backend.app.workers.ocr_source import MAX_INPUT_BYTES, MAX_MESSAGE_BYTES, SAFE_CODES, Wire

ATTEMPT_SECONDS = 300
HEARTBEAT_SECONDS = 15
POLL_SECONDS = 2
RSS_LIMIT_BYTES = 2 * 1024 * 1024 * 1024
MAX_RESULT_BYTES = MAX_MESSAGE_BYTES - 1
CONTAINMENT_TAIL_SECONDS = 2.0
DB_SETTLEMENT_SECONDS = 15.0
SAFE_ADAPTER_CODES = SAFE_CODES


def child_environment(scratch):
    # Allowlist, never a copy of os.environ. Neither DB credentials, HOME,
    # PYTHONPATH nor .env discovery context is inherited by the child.
    result = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
    result.update(TEMP=scratch, TMP=scratch, HOME=scratch, USERPROFILE=scratch,
                  OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                  PYTHONDONTWRITEBYTECODE="1", PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK="True")
    for key in ("QA_OCR_MODEL_ROOT", "PADDLE_HOME", "PADDLE_PDX_CACHE_HOME"):
        if key in os.environ:
            result[key] = os.path.abspath(os.environ[key])
    return result


class OCRRunner:
    def __init__(self, session_factory=SessionFactory, storage=None):
        self.session_factory = session_factory
        self.storage = storage
        self.policy = DeadlinePolicy()
        self.operation = OneOperation()
        self.launch_operation = OneOperation()
        self.jobs = VerificationJobService(session_factory, result_writer=write_adapter_results,
                                          mutation_guard=lambda op, retry: self.policy.guard(op, retry))
        self.quarantined = False
        self.last_process = None
        self.last_receiver = None
        self.child_stopped = True
        self._stop_attempted = False
        self.last_error_code = None
        self.containment_unavailable = False
        self.containment_elapsed = 0.0
        self._scratch = None
        self._transport_stop = threading.Event()

    def _quarantine(self):
        self.quarantined = True
        self.policy.suspended = True

    def _wait_operation(self, operation, deadline):
        while not operation.done.wait(timeout=min(0.025, max(0.0, deadline-time.monotonic()))):
            if time.monotonic() >= deadline:
                raise RuntimeError("ENGINE_TIMEOUT")
        return operation.take()

    def _db(self, name, action, deadline):
        self.operation.start(name, action)
        return self._wait_operation(self.operation, deadline)

    def _storage_root(self):
        if self.storage is not None:
            if type(self.storage) is not LocalStorage:
                raise RuntimeError("INPUT_STORAGE_UNAVAILABLE")
            return str(self.storage.root)
        # Lexical only: provider construction and filesystem access stay child-side.
        return os.path.abspath(STORAGE_BASE / get_settings().storage_root)

    def _launch(self, deadline):
        from backend.app.workers.ocr_containment import ContainmentUnavailable
        def launch():
            from backend.app.workers.ocr_containment import launch_contained, ContainmentUnavailable
            scratch = tempfile.TemporaryDirectory(prefix="qa-ocr-child-")
            self._scratch = scratch
            try:
                interpreter = getattr(sys, "_base_executable", sys.executable) if os.name == "nt" else sys.executable
                argv = [interpreter, "-I", "-S", str(Path(__file__).with_name("ocr_source.py"))]
                for directory in dict.fromkeys((sysconfig.get_path("purelib"), sysconfig.get_path("platlib"))):
                    argv.extend(("--site-packages", directory))
                handle = launch_contained(
                    argv,
                    env=child_environment(scratch.name), cwd=scratch.name,
                    memory_limit_bytes=RSS_LIMIT_BYTES)
            except BaseException as exc:
                if isinstance(exc, ContainmentUnavailable):
                    self.containment_unavailable = True
                    self.last_error_code = "ENGINE_UNAVAILABLE"
                # Native setup can fail with ownership still unresolved. Keep
                # its scratch resources until containment is actually proven.
                if getattr(exc, "cleanup_confirmed", False) is True:
                    scratch.cleanup()
                    self._scratch = None
                raise
            self.last_process = handle
            self.child_stopped = False
            self._stop_attempted = False
            # Process creation itself can block in the OS. A late handle receives
            # no DTO and is contained/stopped; the supervisor remains quarantined.
            if self.quarantined or time.monotonic() >= deadline:
                self._stop_attempted = True
                self.child_stopped = handle.stop(time.monotonic()+CONTAINMENT_TAIL_SECONDS)
                if self.child_stopped:
                    handle.close()
                    scratch.cleanup()
                    self._scratch = None
                raise OutcomeUnknown("Launch completed outside productive budget")
            return handle
        self.launch_operation.start("launch", launch)
        try:
            return self._wait_operation(self.launch_operation, deadline)
        except ContainmentUnavailable as exc:
            if (getattr(exc, "cleanup_confirmed", False)
                    and getattr(exc, "workload_started", True) is False
                    and not self.launch_operation.occupied and self.last_process is None):
                raise RuntimeError("ENGINE_UNAVAILABLE") from exc
            self.child_stopped = False
            self._quarantine()
            raise
        except BaseException:
            # An arbitrary launcher exception carries no proof of native
            # ownership cleanup, even when no handle was returned to Python.
            self.child_stopped = False
            self._quarantine()
            raise

    def _stop_child(self, productive_deadline):
        started = time.monotonic()
        self._transport_stop.set()
        if self.launch_operation.pending:
            self._quarantine()
            return False
        handle = self.last_process
        if handle is None or self.child_stopped:
            return True
        if self._stop_attempted:
            return self.child_stopped
        self._stop_attempted = True
        # stop() requests termination immediately. One separately measured tail
        # permits only owned-process/transport reaping, never productive work.
        tail_deadline = started+CONTAINMENT_TAIL_SECONDS
        try:
            stopped = handle.stop(tail_deadline)
            if self.last_receiver is not None:
                self.last_receiver.join(timeout=max(0.0, tail_deadline-time.monotonic()))
            stopped = stopped and (self.last_receiver is None or not self.last_receiver.is_alive())
            self.child_stopped = stopped
            self.containment_elapsed = time.monotonic()-started
            if not stopped:
                self._quarantine()
                return False
            return True
        except BaseException:
            self._quarantine()
            return False

    def _release_child(self):
        # A timed-out native launch still owns its scratch directory and may
        # publish a handle later. Its thread performs that late cleanup itself.
        if self.launch_operation.occupied or not self.child_stopped:
            return
        if self.last_process is not None:
            self.last_process.close()
        if self._scratch is not None:
            self._scratch.cleanup()
            self._scratch = None

    def _execute(self, claim, dto, deadline):
        payload = b"I" + json.dumps(dto, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(payload) > MAX_INPUT_BYTES:
            raise RuntimeError("SNAPSHOT_INTEGRITY_ERROR")
        handle = self._launch(deadline)
        if time.monotonic() >= deadline:
            self._stop_child(deadline)
            raise RuntimeError("ENGINE_TIMEOUT")
        messages, commands = queue.Queue(maxsize=2), queue.Queue(maxsize=1)
        self._transport_stop.clear()
        wire = Wire(handle.stdout, handle.stdin, write_limit=MAX_INPUT_BYTES)

        def publish(item):
            while not self._transport_stop.is_set():
                try:
                    messages.put(item, timeout=0.025)
                    return
                except queue.Full:
                    continue

        def transport():
            try:
                if self._transport_stop.is_set() or time.monotonic() >= deadline:
                    return
                wire.send_bytes(payload)
                while not self._transport_stop.is_set():
                    frame = wire.recv_bytes()
                    publish(("frame", frame))
                    if frame != b"O":
                        return
                    while not self._transport_stop.is_set():
                        try:
                            command = commands.get(timeout=0.025)
                            if self._transport_stop.is_set() or time.monotonic() >= deadline:
                                return
                            wire.send_bytes(command)
                            break
                        except queue.Empty:
                            continue
            except BaseException as exc:
                publish(("error", exc))
        self.last_receiver = threading.Thread(target=transport, name="ocr-child-transport", daemon=True)
        self.last_receiver.start()
        next_heartbeat = time.monotonic()+HEARTBEAT_SECONDS
        phase, stage_requested, output = "ocr", False, None
        try:
            while time.monotonic() < deadline:
                if handle.memory_exceeded():
                    raise RuntimeError("ENGINE_RESOURCE_LIMIT")
                if self.operation.occupied and self.operation.done.is_set():
                    name = self.operation.name
                    try:
                        self.operation.take()
                    except (OutcomeUnknown, LostFence, DBAPIError):
                        # take() consumes the completed slot. Keep uncertainty
                        # sticky before cleanup can observe a secondary error.
                        self._quarantine()
                        raise
                    if name == "stage":
                        if time.monotonic() >= deadline:
                            raise RuntimeError("ENGINE_TIMEOUT")
                        commands.put_nowait(b"V")
                        phase = "verify"
                if not self.operation.occupied:
                    if output is not None:
                        if time.monotonic() >= deadline or handle.memory_exceeded():
                            raise RuntimeError("ENGINE_TIMEOUT" if time.monotonic() >= deadline else "ENGINE_RESOURCE_LIMIT")
                        return output
                    if stage_requested:
                        self.operation.start("stage", lambda: self.jobs.stage(claim.fence))
                        stage_requested = False
                    elif time.monotonic() >= next_heartbeat:
                        self.operation.start("renew", lambda: self.jobs.renew(claim.fence))
                        next_heartbeat = time.monotonic()+HEARTBEAT_SECONDS
                try:
                    kind, frame = messages.get(timeout=min(0.025, max(0.0, deadline-time.monotonic())))
                except queue.Empty:
                    continue
                if time.monotonic() >= deadline:
                    raise RuntimeError("ENGINE_TIMEOUT")
                if kind == "error":
                    code = "RESULT_LIMIT_EXCEEDED" if isinstance(frame, ValueError) and str(frame) == "RESULT_LIMIT_EXCEEDED" else "ENGINE_PROCESS_CRASH"
                    raise RuntimeError(code)
                if frame[:1] == b"E":
                    code = json.loads(frame[1:]).get("code", "ENGINE_INTERNAL_ERROR")
                    raise RuntimeError(code if code in SAFE_CODES else "ENGINE_INTERNAL_ERROR")
                if frame == b"O" and phase == "ocr":
                    phase, stage_requested = "stage", True
                elif frame[:1] == b"D" and phase == "verify":
                    output = json.loads(frame[1:])
                    if not isinstance(output, dict):
                        raise RuntimeError("ENGINE_OUTPUT_INVALID")
                else:
                    raise RuntimeError("ENGINE_OUTPUT_INVALID")
            raise RuntimeError("ENGINE_TIMEOUT")
        finally:
            if not self._stop_child(deadline):
                raise OutcomeUnknown("Contained workload termination unproven")
            # Requery after shutdown before publication; never trust sampled RSS.
            if not self.quarantined and handle.memory_exceeded():
                raise RuntimeError("ENGINE_RESOURCE_LIMIT")

    def _record_failure(self, claim, code):
        if self.quarantined or not self.child_stopped or self.operation.occupied or self.launch_operation.pending:
            self._quarantine()
            return
        self.last_error_code = code
        if time.monotonic() >= self.policy.deadline:
            if code != "ENGINE_TIMEOUT":
                # Only timeout bookkeeping is authorized after expiry. Preserve
                # the observed cause instead of misreporting memory/input errors.
                self._quarantine()
                return
            self.policy.allow_timeout_failure()
        try:
            self._db("fail", lambda: self.jobs.fail(claim.fence, code),
                     time.monotonic()+DB_SETTLEMENT_SECONDS)
        except BaseException:
            self._quarantine()

    def run_once(self):
        if self.quarantined or self.operation.occupied or self.launch_operation.occupied:
            raise OutcomeUnknown("Runner quarantined or parent operation unsettled")
        self.policy = DeadlinePolicy()
        self.last_process = None
        self.last_receiver = None
        self.child_stopped = True
        self._stop_attempted = False
        self.last_error_code = None
        self.containment_unavailable = False
        claim = None
        try:
            def claim_action():
                # Conservatively include claim/ACK/recovery latency. Never mint
                # a new 300 seconds after recovering an uncertain claim ACK.
                self.policy.deadline = time.monotonic()+ATTEMPT_SECONDS
                return self.jobs.claim()
            claim = self._db("claim", claim_action, time.monotonic()+DB_SETTLEMENT_SECONDS)
            if claim is None:
                return False
            deadline = self.policy.deadline
            dto = self._db("metadata", lambda: load_metadata(self.session_factory, self._storage_root(), claim), deadline)
            if time.monotonic() >= deadline:
                raise RuntimeError("ENGINE_TIMEOUT")
            output = self._execute(claim, dto, deadline)
            if time.monotonic() >= deadline:
                raise RuntimeError("ENGINE_TIMEOUT")
            if self.last_process.memory_exceeded():
                raise RuntimeError("ENGINE_RESOURCE_LIMIT")
            result = self._db("finalize", lambda: self.jobs.finalize(claim.fence, output),
                              time.monotonic()+DB_SETTLEMENT_SECONDS)
            if result is None:
                raise OutcomeUnknown("Finalize did not resolve durable results")
        except (LostFence, OutcomeUnknown, DBAPIError):
            self._quarantine()
        except BaseException as exc:
            # A pending DB operation is allowed to settle, but no compensating
            # mutation is launched until its authoritative result is available.
            if self.operation.occupied:
                name = self.operation.name
                try:
                    settled = self._wait_operation(self.operation, time.monotonic()+DB_SETTLEMENT_SECONDS)
                    if name == "finalize" and settled is not None:
                        return True
                except BaseException:
                    self._quarantine()
            if claim is None:
                self._quarantine()
            elif not self.quarantined:
                code = "ENGINE_OUTPUT_INVALID" if isinstance(exc, AdapterOutputInvalid) else str(exc)
                if code not in SAFE_CODES | {"ENGINE_PROCESS_CRASH"}:
                    code = "ENGINE_INTERNAL_ERROR"
                self._record_failure(claim, code)
        finally:
            if self.last_process is not None and not self.child_stopped:
                self._stop_child(self.policy.deadline)
            if self.child_stopped:
                self._release_child()
        return True

    def run_forever(self):
        while not self.quarantined:
            if not self.run_once():
                time.sleep(POLL_SECONDS)
        raise OutcomeUnknown("Runner quarantined; primary settlement/recovery required")


def main():
    OCRRunner().run_forever()


if __name__ == "__main__":
    main()
