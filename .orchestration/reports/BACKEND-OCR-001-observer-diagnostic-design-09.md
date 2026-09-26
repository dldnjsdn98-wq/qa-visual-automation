# Observer diagnostics09 — UNAPPLIED source proposal

Source writes HOLD following Fermat's denied first CreateNew of the shared environment module. This lane made no product/test writes. Readback test SHA256 e72c2fb79a9bc3b0c0e08f155b5c78f16173d8e02ecc9f8349f2ecab3674af45; shared module absent. No retry, alternative writer or escalation. This report is evidence-only preparation, not an executable candidate or approval.

## Proposed helper definitions

Insert immediately before _l1_shortpeak only after source disposition. Existing module imports suffice. Fixed fields and bounded reads prevent arbitrary proc/config capture. Read/parse failures are explicit null plus exception TYPE, never raw exception messages. Byte bounds are not a proof of kernel/filesystem read latency. Snapshots are sequential/non-atomic; selected accounting fields overlap and must not be summed.

```python
def _l1_read_text(path, limit=65536):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("diagnostic input exceeds bound")
    return raw.decode("ascii")


def _l1_snapshot(phase, observer_pid, child_pid=None):
    result = dict(phase=phase, started_ns=time.monotonic_ns(),
                  atomic=False, cgroup={}, processes={}, errors={})

    def sample(key, read):
        try:
            return read()
        except (OSError, ValueError, IndexError, KeyError) as error:
            result["errors"][key] = type(error).__name__
            return None

    def number(value):
        parsed = int(value)
        if parsed < 0:
            raise ValueError("negative counter")
        return parsed

    def table(path, keys, prefix):
        rows = sample(prefix, lambda: dict(
            line.split() for line in _l1_read_text(path).splitlines()))
        return {key: sample(prefix + "." + key, lambda key=key:
                           number(rows[key])) if rows is not None else None
                for key in keys}

    cg = result["cgroup"]
    for name in ("memory.current", "memory.max", "memory.swap.max"):
        cg[name] = sample(name, lambda name=name: number(
            _l1_read_text("/sys/fs/cgroup/" + name).strip()))
    cg["memory.stat"] = table("/sys/fs/cgroup/memory.stat",
        ("anon", "file", "kernel", "shmem", "pagetables", "slab", "sock", "file_mapped"),
        "memory.stat")
    cg["memory.events"] = table("/sys/fs/cgroup/memory.events",
        ("low", "high", "max", "oom", "oom_kill", "oom_group_kill"), "memory.events")
    for role, pid in (("observer", observer_pid), ("child", child_pid)):
        if pid is None:
            result["processes"][role] = None
            continue
        row = dict(pid=pid)
        fields = sample(role + ".stat", lambda: _l1_read_text(
            f"/proc/{pid}/stat").rsplit(")", 1)[1].split())
        for name, index in (("ppid", 1), ("pgrp", 2), ("start_ticks", 19)):
            row[name] = sample(role + "." + name, lambda index=index:
                               number(fields[index])) if fields is not None else None
        status = sample(role + ".status", lambda: dict(
            line.split(":", 1) for line in _l1_read_text(
                f"/proc/{pid}/status").splitlines()))
        def rss(key):
            value, unit = status[key].split()
            if unit != "kB":
                raise ValueError("unexpected RSS unit")
            return number(value) * 1024
        for key in ("VmRSS", "RssAnon", "RssFile", "RssShmem"):
            row[key + "_bytes"] = sample(role + "." + key, lambda key=key:
                rss(key)) if status is not None else None
        result["processes"][role] = row
    result["finished_ns"] = time.monotonic_ns()
    return result


def _l1_persist_snapshot(path, snapshot):
    raw = json.dumps(snapshot, sort_keys=True).encode("ascii")
    if len(raw) > 32768:
        raise ValueError("diagnostic output exceeds bound")
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
```

## Exact integration proposal (NOT APPLIED)

1. Change only child_environment import to backend.app.workers.ocr_child_environment after that module exists and is independently reviewed. Never install this unresolved import now.
2. After existing cap/swap assertions and before nonce/launch, obtain observer_snapshot = _l1_snapshot("observer_only", os.getpid()); persist to tmp_path / "l1-observer.json". Failure here has no child. No extra launch/thread.
3. Add observer_snapshot=observer_snapshot to the existing facts dictionary. Do not add postlaunch diagnostic operations outside the existing try/finally.
4. Inside existing try, immediately after obtaining anon_bytes, retain facts["baseline_rss_anon_bytes"] = anon_bytes before its existing residency assertion. After that assertion, assign facts["baseline_ready_snapshot"] = _l1_snapshot("baseline_ready", os.getpid(), handle.pid), then persist that same object to tmp_path / "l1-baseline.json". Identity, membership, original residency and readiness checks remain unchanged.
5. Immediately after existing current/headroom calculation, before unchanged headroom assertion, facts.update(memory_current_before_gate=current, headroom_before_gate=headroom). This scalar sample is AFTER snapshot persistence; later existing facts.update is retained. Existing before_gate events/identity/liveness checks remain. No new diagnostic operation between t0 and terminal_at/t1.
6. Existing finally remains byte-for-byte: messages then record_property l1_evidence within try, and _finish in nested finally. Read failures handled as null do not replace an authority assertion; unexpected snapshot exceptions, serialization/write/fsync failures, final scalar read failure or assertion failure propagate and still reach the same _finish exactly once. A failure in JUnit serialization may prevent evidence serialization, but cannot skip that nested cleanup. No second cleanup is added.

Temporary snapshots are ancillary persistence before assertion; existing JUnit finally is the capture channel. Final authoritative scalars are retained in facts, not retroactively written into earlier snapshots. Persistence may itself increase charged memory. No promise of satisfying 64..160MiB.

## Synthetic test seams for Descartes

Proposal only: load the eventual test module through ordinary importlib file loading after shared module exists; no source-text exec or module stubs in qualifying runtime. Module top level contains definitions/pytest marks; do not call native tests during collection. For snapshot unit tests, replace _l1_read_text with a finite path->text fake, and monotonic_ns if deterministic stamps needed. Cover missing selected stat/status fields, malformed/negative values, input oversize, missing process; assert null and type-only errors, no raw input/path exceptions serialized. Persistence tests use tmp_path, inject json.dumps/os.fsync failures; oversize output rejected before file creation.

Control-flow tests of eventual _l1_shortpeak must fake _native_limit, os.getpid, _l1_members/_l1_events/_l1_identity, Path reads/stat, _launch retained fake pipes, os.set_blocking, select.select, os.read and monotonic readiness. Feed exactly one nonce-matched ready message through fake launch arguments (capture nonce); preserve fixed cap/baseline/increment. Fake _finish records calls and record_property collects facts. Inject snapshot/persist/final-current failure after ready, or make headroom fail; assert same handle receives exactly one _finish, G never written, final scalars retained when sampled. Observer-only persistence failure must assert no _launch and no _finish. A JUnit serializer/record_property failure must also leave cleanup count one. No /proc, native API or real subprocess access is permitted. These tests are NOT_RUN and not yet source-ready.

## Immutable capture candidate preparation

Derive only from candidate07 SHA256 e669d74fc1f683ad57cf3792860910f65198cbed3f6d0dee91232c36e36d082c, retaining all lifecycle, numeric, ownership, source validation and oracle gates. Add --noconftest to exact selected-node pytest argv, keeping plugin autoload disabled. Require backend/__init__.py, backend/app/__init__.py, backend/app/workers/__init__.py and new ocr_child_environment.py in source closure in addition to current required entries. Add fixed LF equality gates for changed runner AND environment helper AND test; containment LF6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c stays fixed. Retain raw+LF verification for every source. Old image cannot represent new source.

New test/runner/environment applied hashes are UNRESOLVED. No executable headroom candidate is frozen or created with placeholders, baseline identities masquerading as changed source, or loosened checks. Candidate preparation remains this precise change specification until PM disposition and exact independently reviewed source identities exist. No actual-source pin manifest, build or capture is activated.

## Status

Only this report written. Product/test/helper/candidate07 unchanged by this lane. No imports, tests, collection, native/API probes, Docker, model/DB, build or dependency execution. Independent review and synthetic validation remain pending. Existing08 FAIL, Windows3/historicalcleanup2 and all admission gates unchanged. Requested Astra/medium identity unverified.