# UNAPPLIED prospective source pins; NOT EXECUTION READY. Source-write HOLD.
"""L1 external capture CANDIDATE. No execution until separate PM approval.

One new immutable image, one retained named container, one shortpeak node.
No build, retry, tuning, DB/model/network or source edits. Host mode uses Docker;
inner mode verifies source pins and execs pytest in the SAME container PID1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
from uuid import uuid4
import xml.etree.ElementTree as ET

OWNER = "BACKEND-OCR-001-L1-capture-03"
CAP = 536870912
TEST = "tests/backend/test_ocr_containment.py"
NODE = TEST + "::test_native_pressure_and_owned_tree_cleanup[shortpeak]"
TEST_LF = "2c7a9c03b8b282b6e38ecad95be33deb0ec3d913c979ae43d701c789c0a9c9cb"
RUNNER_LF = "3eecadf757f4ad945f67ff02c7f4347efda342e491ed85250780010d7d55d9f1"
ENVIRONMENT_LF = "06f2ca8428fca1740d77b3b9dd7515eeecbf28d9760cc87b3688f6501fd23c0d"
HELPER_LF = "6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c"
OLD_IMAGES = {
    "sha256:dc9828b1c1984044900b45a2d46e96dd2a2a3fb851f0d1bee631e6e0f271e99e",
    "sha256:56c45fb0dac074888d84484e414107c95342ab325e148c916fe55e454f1df662",
}


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def publish(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    # Windows host directory durability is not claimed.
    if os.name == "posix":
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def source_pins(path, digest):
    raw = path.read_bytes()
    require(sha(raw) == digest, "source-pin input hash mismatch")
    pins = json.loads(raw)
    require(pins.get("schema_version") == 1, "source-pin schema mismatch")
    files = pins.get("files", {})
    require(isinstance(files, dict) and 2 <= len(files) <= 128, "source-pin count invalid")
    required = {"backend/__init__.py", "backend/app/__init__.py",
                "backend/app/workers/__init__.py", "backend/app/workers/ocr_child_environment.py", TEST, "backend/app/workers/ocr_containment.py", "backend/app/workers/ocr.py",
                "backend/app/workers/ocr_source.py", "backend/app/workers/ocr_runtime.py",
                "tests/backend/conftest.py", "backend/requirements.lock", "backend/Dockerfile.test",
                "pyproject.toml"}
    require(required <= files.keys(), "required test/helper/fixture/dependency source pins absent")
    require(files[TEST].get("lf_sha256") == TEST_LF, "L1 candidate identity mismatch")
    require(files["backend/app/workers/ocr_containment.py"].get("lf_sha256") == HELPER_LF,
            "W1 candidate helper identity mismatch")
    require(files["backend/app/workers/ocr.py"].get("lf_sha256") == RUNNER_LF,
            "prospective runner identity mismatch")
    require(files["backend/app/workers/ocr_child_environment.py"].get("lf_sha256") == ENVIRONMENT_LF,
            "prospective environment identity mismatch")
    for name, hashes in files.items():
        part = PurePosixPath(name)
        require(not part.is_absolute() and ".." not in part.parts and "\\" not in name,
                "invalid source path")
        require(part.parts[0] in {"backend", "tests", "worker"} or name == "pyproject.toml",
                "source pin outside approved source scope")
        require(all(not piece.startswith(".") for piece in part.parts), "hidden source input forbidden")
        require(set(hashes) == {"sha256", "lf_sha256"} and all(
            re.fullmatch("[0-9a-f]{64}", value) for value in hashes.values()), "invalid source hashes")
    return raw, files


def verify_sources(root, files):
    actual = {}
    for name, hashes in files.items():
        path = (root / name).resolve()
        require(path.is_relative_to(root.resolve()), "source escapes root")
        require(path.is_file() and path.stat().st_size <= 16 * 1024 * 1024, "source invalid")
        data = path.read_bytes()
        actual[name] = {"sha256": sha(data), "lf_sha256": sha(data.replace(b"\r\n", b"\n"))}
        require(actual[name] == hashes, "source bytes mismatch: " + name)
    return actual


def inner(args):
    require(sys.platform == "linux" and os.getpid() == 1, "inner observer must be Linux PID1")
    require(sha(Path(__file__).read_bytes()) == args.script_sha256, "capture script mismatch")
    _, files = source_pins(Path("/evidence/source-pins.json"), args.pins_sha256)
    actual = verify_sources(Path("/app"), files)
    require(Path("/sys/fs/cgroup/memory.max").read_text().strip() == str(CAP), "cap mismatch")
    require(Path("/sys/fs/cgroup/memory.swap.max").read_text().strip() == "0", "swap mismatch")
    require(not Path("/evidence/result.xml").exists(), "JUnit unexpectedly exists before execution")
    publish(Path("/evidence/inner-inputs.json"), dict(
        source_hashes=actual, observer_pid=os.getpid(), script_sha256=args.script_sha256,
        pins_sha256=args.pins_sha256, node=NODE, observer_death="unproved; no fabricated t1 or JUnit"))
    os.chdir("/app")
    # Exec, not subprocess: the future test observer remains PID1.
    os.execv(sys.executable, [sys.executable, "-m", "pytest", NODE, "-q", "--tb=short", "--noconftest",
        "-p", "no:cacheprovider", "-o", "junit_family=legacy", "--basetemp=/tmp/l1-pytest",
        "--junitxml=/evidence/result.xml"])


def audit_result(evidence, terminal):
    # Natural PID1 exit is independent of child exit and cgroup OOM notifications.
    if terminal["running"] or terminal["exit"] != 0:
        return "UNPROVED_OBSERVER_EXIT"
    path = evidence / "result.xml"
    if not path.is_file():
        return "UNPROVED_NO_JUNIT"
    require(path.stat().st_size <= 2 * 1024 * 1024, "oversized JUnit")
    cases = list(ET.fromstring(path.read_bytes()).iter("testcase"))
    require(len(cases) == 1 and cases[0].get("name") ==
            "test_native_pressure_and_owned_tree_cleanup[shortpeak]", "unexpected test selection")
    case = cases[0]
    if case.find("failure") is not None or case.find("error") is not None:
        return "FAIL_TEST"
    if case.find("skipped") is not None:
        return "UNPROVED_SKIP"
    props = {}
    for prop in case.findall("./properties/property"):
        require(prop.get("name") not in props, "duplicate JUnit property")
        props[prop.get("name")] = prop.get("value")
    require(props.get("owned_tree_stop_confirmed") == "True", "owned child cleanup not proven")
    facts = json.loads(props["l1_evidence"])
    require(facts.get("observer_pid") == 1 and facts.get("attempted") is True
            and facts.get("identity_valid") is True, "pressure identity/attempt missing")
    require((facts.get("baseline_bytes"), facts.get("increment_bytes"), facts.get("memory_limit_bytes"))
            == (335544320, 234881024, CAP), "fixed pressure changed")
    elapsed = facts.get("elapsed_upper_ns")
    require(type(elapsed) is int and 0 <= elapsed < 250_000_000, "timing unproved")
    require(facts.get("t1_ns") - facts.get("t0_ns") == elapsed, "observer endpoints mismatch")
    delta = facts["events_delta"]
    killed = (facts.get("outcome") == "exit" and facts.get("exit_code") == -9
              and delta.get("oom_kill", 0) > 0 and props.get("l1_verdict") == "PASS_KILLED_ATTEMPT")
    denied = (facts.get("outcome") == "denied" and delta.get("oom", 0) > 0
              and props.get("l1_verdict") == "PASS_DENIED_ATTEMPT")
    require(killed or denied, "no causal L1 enforcement witness")
    inputs = json.loads((evidence / "inner-inputs.json").read_text())
    require(inputs["observer_pid"] == 1 and inputs["node"] == NODE, "inner observer mismatch")
    return "PASS_SCOPED_L1"


def host(args):
    root = Path(__file__).resolve().parents[2]
    evidence = args.evidence.resolve()
    require(evidence.parent == (root / ".orchestration/reports").resolve()
            and evidence.name.startswith("BACKEND-OCR-001-native-apply-linux-evidence-03-")
            and not evidence.exists(), "new scoped evidence directory required")
    require(re.fullmatch("sha256:[0-9a-f]{64}", args.image_id)
            and args.image_id not in OLD_IMAGES, "new reviewed immutable image required")
    raw_pins, files = source_pins(args.source_pins, args.pins_sha256)
    before = verify_sources(root, files)  # Refuse if parent source application is blocked/incomplete.
    script = Path(__file__).read_bytes()
    evidence.mkdir()
    (evidence / "source-pins.json").write_bytes(raw_pins)
    (evidence / "capture.py").write_bytes(script)
    nonce = uuid4().hex
    name = "qa-l1-" + nonce
    record = dict(status="UNPROVED", nonce=nonce, container_name=name, image_id=args.image_id,
                  script_sha256=sha(script), source_before=before, pins_sha256=args.pins_sha256,
                  commands=[], launch_uncertain=False, cleanup_confirmed=False,
                  stop_requested=False, node=NODE, host_directory_fsync=False,
                  observer_death="no invented t1/JUnit/pass; external terminal evidence only")
    container_id = None
    terminal = None

    def command(argv, timeout=10):
        item = dict(argv=argv, started_ns=time.monotonic_ns(), timeout_seconds=timeout)
        record["commands"].append(item)
        try:
            result = subprocess.run(argv, text=True, capture_output=True, timeout=timeout, check=False)
            item.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
            require(result.returncode == 0, "Docker command failed")
            return result.stdout.strip()
        finally:
            item["ended_ns"] = time.monotonic_ns()

    def discover():
        # Positive exact-name lookup only; empty result does not resolve a late launch.
        value = command(["docker", "container", "ls", "-a", "--no-trunc", "--filter",
                         "name=^/" + name + "$", "--format", "{{.ID}} {{.Names}}"])
        if not value:
            return None
        rows = value.splitlines()
        require(len(rows) == 1 and rows[0].split() == [rows[0].split()[0], name]
                and re.fullmatch("[0-9a-f]{64}", rows[0].split()[0]), "ambiguous container identity")
        return rows[0].split()[0]

    def inspect(owned_id):
        # Whitelist only; never inspect Config.Env, ambient config, or other containers.
        fields = dict(id=".Id", name=".Name", image=".Image", running=".State.Running",
                      status=".State.Status", exit=".State.ExitCode", oom=".State.OOMKilled",
                      started=".State.StartedAt", finished=".State.FinishedAt",
                      memory=".HostConfig.Memory", swap=".HostConfig.MemorySwap",
                      network=".HostConfig.NetworkMode", owner='(index .Config.Labels "qa.visual.owner")',
                      nonce='(index .Config.Labels "qa.visual.nonce")')
        template = "{" + ",".join(json.dumps(k) + ":{{json " + v + "}}" for k, v in fields.items()) + "}"
        facts = json.loads(command(["docker", "container", "inspect", "--format", template, owned_id]))
        require((facts["id"], facts["name"], facts["owner"], facts["nonce"])
                == (owned_id, "/" + name, OWNER, nonce), "container ownership mismatch")
        require((facts["image"], facts["memory"], facts["swap"], facts["network"])
                == (args.image_id, CAP, CAP, "none"), "container configuration mismatch")
        return facts

    try:
        publish(evidence / "manifest.json", record)
        identity = command(["docker", "image", "inspect", "--format",
                            "{{.Id}} {{.Os}} {{.Architecture}}", args.image_id])
        require(identity == args.image_id + " linux amd64", "image identity/platform mismatch")
        require(discover() is None, "container name already exists")
        argv = ["docker", "create", "--pull=never", "--init=false", "--entrypoint", "python", "--name", name,
                "--label", "qa.visual.owner=" + OWNER, "--label", "qa.visual.nonce=" + nonce,
                "--network", "none", "--memory", str(CAP), "--memory-swap", str(CAP),
                "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m",
                "--mount", "type=bind,source=" + str(evidence) + ",target=/evidence",
                "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
                "-e", "QA_OCR_NATIVE_CONTAINMENT_TEST=1", "-e", "QA_OCR_NATIVE_PRESSURE_TEST=1",
                "-e", "QA_OCR_NATIVE_LIMIT_BYTES=" + str(CAP),
                args.image_id, "-I", "-S", "/evidence/capture.py", "inner",
                "--pins-sha256", args.pins_sha256, "--script-sha256", sha(script)]
        record["launch_uncertain"] = True  # BEFORE daemon may create anything.
        publish(evidence / "manifest.json", record)
        container_id = command(argv, 30)
        require(re.fullmatch("[0-9a-f]{64}", container_id), "invalid created ID")
        record["container_id"] = container_id
        record["created"] = inspect(container_id)
        command(["docker", "start", container_id])  # At most once, even on uncertain reply.
        waited = command(["docker", "wait", container_id], 45)
        require(re.fullmatch("[0-9]+", waited), "unknown natural exit")
        terminal = inspect(container_id)
        require(not terminal["running"] and terminal["status"] == "exited"
                and terminal["exit"] == int(waited), "natural terminal state mismatch")
        record["natural_terminal"] = terminal
        publish(evidence / "terminal.json", terminal)  # BEFORE any stop/removal.
        # Logs are fixed synthetic test output, no env file/DB/model supplied.
        log = command(["docker", "logs", container_id])
        (evidence / "container.log").write_text(log, encoding="utf-8")
        record["status"] = audit_result(evidence, terminal)
    except BaseException as error:
        record["error_type"] = type(error).__name__
        record["status"] = "UNPROVED_CAPTURE_FAILURE"
    finally:
        if record["launch_uncertain"]:
            try:
                if container_id is None or not re.fullmatch("[0-9a-f]{64}", container_id):
                    container_id = discover()
                require(container_id is not None, "late creation unresolved; no false absence proof")
                facts = inspect(container_id)
                record["before_cleanup"] = facts
                if facts["running"]:
                    record["stop_requested"] = True
                    record["status"] = "UNPROVED_FORCED_STOP"
                    command(["docker", "stop", "--time", "2", container_id], 10)
                    facts = inspect(container_id)
                require(not facts["running"], "owned container still running")
                record["terminal_before_remove"] = facts
                command(["docker", "rm", container_id], 10)
                # No --force/--rm and no second start/stop/removal attempt.
                record["cleanup_confirmed"] = True
                record["launch_uncertain"] = False
            except BaseException as error:
                record["cleanup_error_type"] = type(error).__name__
                record["status"] = "UNPROVED_OWNERSHIP_OR_CLEANUP"
        try:
            record["source_after"] = verify_sources(root, files)
            require(sha(Path(__file__).read_bytes()) == sha(script), "author script changed")
            require(sha((evidence / "capture.py").read_bytes()) == sha(script), "snapshot script changed")
            require(sha((evidence / "source-pins.json").read_bytes()) == args.pins_sha256, "snapshot pins changed")
            record["source_unchanged"] = record["source_after"] == before
        except BaseException as error:
            record["source_error_type"] = type(error).__name__
            record["status"] = "UNPROVED_SOURCE_DRIFT"
        record["artifacts"] = {p.name: sha(p.read_bytes()) for p in (
            evidence / "result.xml", evidence / "inner-inputs.json", evidence / "terminal.json",
            evidence / "container.log") if p.is_file()}
        publish(evidence / "manifest.json", record)
    return 0 if record["status"] == "PASS_SCOPED_L1" and record["cleanup_confirmed"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    outer = modes.add_parser("host")
    outer.add_argument("--image-id", required=True)
    outer.add_argument("--source-pins", type=Path, required=True)
    outer.add_argument("--pins-sha256", required=True)
    outer.add_argument("--evidence", type=Path, required=True)
    nested = modes.add_parser("inner")
    nested.add_argument("--pins-sha256", required=True)
    nested.add_argument("--script-sha256", required=True)
    args = parser.parse_args()
    return host(args) if args.mode == "host" else inner(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print("L1_CAPTURE_ERROR:" + type(error).__name__, file=sys.stderr)
        raise SystemExit(2)
