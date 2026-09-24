# ARCH-UPLOAD-001 / owner 02

Date: 2026-09-16 KST. Status proposal: READY_FOR_REVIEW after static checks recorded below; no independent approval/product PASS.
Contract P2-UPLOAD-v1, document revision 1 (completes the previously saved sections 1..5 draft, first submission).
Difficulty: highest; cross-process receipt/fingerprint/lease/queue recovery changes persistent identity. Requested gpt-6-astra / medium; actual application unverified (실제 적용 미확인). Branch/commit: null/null; no Commit/Push.

## Task and current evidence

Goal: executable request/response, receipt and producer/queue contract preserving manual semantics.
Dependency: latest PROJECT_STATE/TASKS/ACCEPTANCE/DECISIONS, PHASE-2-activation-01 and PHASE-2-frontend-backend-prep-01 show Phase1 ACCEPTED/DONE, all preparations complete, ARCH-UPLOAD-001 READY, implementation/review still gated. No owner changes to PM YAML/DECISIONS/phase plan.

Changed scope: docs/architecture/phase-2-upload-contract.md; Phase2-only references in api-contract.md/data-flow.md/domain-model.md; this report and ../handoffs/ARCH-UPLOAD-001-02.md. Existing product/user changes retained. Read current backend router/schema/validation/service/storage/reconcile, Frontend/uploader prep and Reviewer root prep. Earlier Phase1 executions remain historical, not rerun Phase2 evidence.
The unfinished draft SHA256 before continuation was 58F7FF56FB3A05A36AC992FF3F882291A7A9E5E761F63B5CA085B0EB75125320.

## Consultation closure

All three preparation reports were read, including proposed failure matrices. Decisions below are contract choices awaiting independent review, not implementation activation.

### Backend03 twelve questions

| Question | Decision / reason / contract section |
| --- | --- |
| B01 ID scope | Adopt project+producer UUIDv4, immutable indefinitely; distinct project scopes and no hash dedup; 2 |
| B02 header/UUID | Reject ANY Idempotency-Key, including duplicate/matching/empty; one JSON-part identity, canonical typed UUIDs; avoids two authorities; 1/3 |
| B03 fingerprint fields | All core context, sanitized filename, source, versions, metadata and server-derived hash/facts; exclude ID key/assertion/headers/server fields; 3 |
| B04 JSON/Unicode | JCS RFC8785 with UTF16 key order and explicit binary64 domain; exact Unicode/no NFC, numeric/default/null semantics and duplicate rejection; 3 |
| B05 filename | Adopt validated sanitized basename identity matching existing Python behavior, never raw path; invalid prefix still rejected; 3 |
| B06 status/headers | 201 own completion, 200 replay, 409 conflict or in-progress distinguished by code, positive remaining-lease Retry-After; 503 remains 5; 1/5 |
| B07 validation/receipt | Invalid request never reserves; existing receipt fingerprint precedes changed-context lookup; final reference loss rolls back/fenced FAILED and 404/422; 4/6 |
| B08 state/lease | Explicit PROCESSING/COMPLETED/FAILED invariants; DB clock, 60s/20s renewal, token+monotonic generation; 5 |
| B09 object reuse/delete | Replace cross-generation deterministic key with per-reserved-generation candidate key; same-generation exact verification only, workers never delete published agent objects, maintenance protects recoverable receipts; 6 |
| B10 retention | Adopt no automatic expiry for all states, restrictive delete, no Screenshot DELETE/new tombstone policy; 5 |
| B11 route | Adopt same route, source-discriminated closed schemas, protocol1 in metadata JSON; manual unchanged; 1 |
| B12 buffering | Permit existing bounded buffering, account for copies/concurrency; no mandatory streaming rewrite; 1 |

Additive 0003, partial Screenshot uniqueness and receipt constraints, migration preservation and targeted fault barriers adopted. A redundant global receipt UUID is unnecessary: composite K is the stable receipt identity. Completed identity FK explicitly includes client_upload_id. Per-attempt candidate keys resolve the activation/proposal mismatch without changing LocalStorage grammar. No circular receipt->Screenshot->receipt dependency.

### Frontend04 seven questions

| Question | Decision / reason / section |
| --- | --- |
| W01 source | manual/agent/automation, forwarding preserves automation; 1 |
| W02 pairs | manual omits ID/agent protocol fields, agent/automation require non-null v4; invalid 422; 1 |
| W03 wire ID | client_upload_id in metadata JSON part; header forbidden, exactly two multipart parts; 1 |
| W04 replay | Manual stays 201/null; 200 replay and replay header only agent/automation; 1 |
| W05 Web metadata | Entire bounded CaptureMetadata as safe structured JSON/text, version and non-null client ID on detail; no dropping unknown nested values/Unicode; 1.1 |
| W06 response | One expanded Screenshot read schema with required metadata/version and UUID|null; separate manual write type; no private receipt internals; 1 |
| W07 filter | GET enum supports all three, no new UI filter requirement; 1 |

Accept PM's scoped FRONTEND-UPLOAD-001 allocation; list source renderer already works, only evidenced read-type/detail-display work plus targeted regression. No browser queue/replay behavior.

### Uploader06 questions and proposal changes

| Topic | Disposition / reason / section |
| --- | --- |
| Exact readiness files/order | Adopt same-volume marker-last; replace empty marker with ready.json exact-manifest digest; file flush/rename sequence explicit; 7 |
| Windows power loss | Process-restart promise only; directory flush when supported; document Windows limitation, reject unsupported filesystem/locking; 7 |
| Pair without marker | Remains unready indefinitely, producer-only validated recovery, no age heuristic; 7 |
| Manifest schema/normalization | Closed v1, all fields/limits/core IDs/facts fixed; JCS semantic fingerprint separate from raw manifest digest; 3/7 |
| Changed intent | Local validation before every send, changed intent terminal/new explicit UUID; no retry-driven identity change; 2/7 |
| Invalid/traversal/extra files | Quarantine retained evidence, no HTTP, safe bounded diagnostics; 7 |
| SQLite schema/location/rebuild | Replace with per-item atomic state.json + initialized.json, scan is index. No queue DB. Corruption never silently resets attempts/ack; explicit loss boundary; 7 |
| Claims/concurrency | Adopt single process, OS lock handle, no local lease/claim token because concurrent workers disallowed; process death releases handle; 7 |
| Ack/move disagreement | ACKED is durable authority; reconcile each pending/uploaded/failed boundary, validate ack on recovery; 8 |
| Manual requeue | Explicit epoch increment preserves total attempts and immutable ID; crash-safe PENDING then move; 8 |
| Retry classification | Adopt network/408/429/5xx/409 in-progress; 425 terminal (not emitted); replace terminal malformed ack with bounded same-ID retry; 8 |
| Retry defaults | Keep 8 attempts/base1/factor2/connect5/read-write30. Replace cap60/full jitter with cap300/equal jitter to avoid zero-delay loops. Reject proposed 300s server cap: valid Retry-After is a minimum, not truncated; 8 |
| Clock behavior | Persist UTC deadline, monotonic intra-run; rollback conservative, forward jump cannot bypass server lease; overflow handled as invalid header; 8 |
| Success matrix | Strict 201 false/200 true plus required body/header facts, unknown additive fields ignored; 8 |
| Receipt fingerprint response | Replace extra public fingerprint with returned K and all fingerprint component comparison under v1; sufficient to reject unrelated 200/201 without expanding public model; 8 |
| Lost response | Same ID/bytes/context, matching ack before move, exhaustion retains original; 6/8 |

All 25 uploader scenarios traced: P01/P02/P03/P04/P05/P06/P07 -> F02/F03/F04; Q01/Q02/Q03 -> F16/F19 (Q03 uses process lock instead of concurrent claim); R01/R02/R03/R04/R05 -> F01/F17; A01/A02/A03/A04/A05 -> F18/F13/F06/F07; S01/S02/S03 -> F19; I01/I02 -> F13/F22. State corruption/full disk/collision adds F20. These are required future executions, NOT_RUN.

### Ownership/dependencies

Contract section 10 names 03 Backend/migration/tests; 06 producer/queue/actual integration; 04 minimal Web implementation/verification; 02 contract; 08 independent review; PM only state/activation.
Select uploader-local python -m agent.screenshot_upload, no common agent/__main__.py edit. Recommend 06-owned agent/screenshot_upload/requirements.lock; runtime httpx and JCS dependency/package discovery in pyproject.toml need exact PM claim, sequential coordination with 03. Backend lock not repurposed. README uploader runbook needs PM claim and implemented behavior. These are decisions/requests, NOT shared-file edit permissions.

## Validation and limitations

Environment: Windows PowerShell, C:/Dev/qa-visual-automation. Writes used approved escalation because workspace sandbox is read-only; no permissions bypass. Reads/git inventory encountered an unrelated historical temporary directory access warning, not a contract blocker. PM reports its approved project .venv execution succeeded and interpreter exists; 06's earlier restricted launch is not evidence of deletion and not a new Phase1 environment issue.

Static verification results will be recorded after execution. Existing check_contract.py embeds obsolete Phase1 READY_FOR_REVIEW/blocked-state assertions; do not run or modify it to force current Phase2 state into that historical gate. Product HTTP/DB/migrations/crash/queue/browser/build suites NOT_RUN: implementation explicitly gated. JCS implementation interoperability and numeric PostgreSQL roundtrip remain mandatory implementation tests, not inferred from prose.

Remaining risks: independent review pending; JCS dependency/platform equivalence, actual PostgreSQL concurrency/ambiguous commit, Windows lock/rename durability, bounded memory and real Web metadata evidence require later implementation tests. No unresolved author-side policy choice intentionally deferred; PM file claims are an activation gate, not a protocol ambiguity.

## Submission

Exact final SHA256 and command results follow. Request PM record READY_FOR_REVIEW and activate REVIEW-ARCH-UPLOAD-001 on this revision/hash; do not activate implementation until independent ACCEPTED plus PM READY. AC-P2-01..04 remain NOT_RUN. Next owner PM01 -> Reviewer08.

## Executed static evidence / 2026-09-16

Cwd C:/Dev/qa-visual-automation, Windows PowerShell, Node v24.19.0.
- node --version: PASS, v24.19.0.
- git diff --check -- docs/architecture .orchestration/reports/ARCH-UPLOAD-001-02.md .orchestration/handoffs/ARCH-UPLOAD-001-02.md: PASS, exit 0/no whitespace errors.
- git diff --stat -- docs/architecture: three existing files, 5 insertions/9 deletions, only Phase2 outlines replaced. New contract is untracked, included by the explicit checker below.
- Get-FileHash on all four architecture files: PASS; exact snapshot below.
- PowerShell assigns the following JavaScript to a single-quoted here-string named $script and executes node -e $script: PASS, exit 0.
- Checker output: 4 documents, 11 local links, 5 JSON examples, sections 1..10, F01..F24, preserved Phase1 prefix/suffix compared to HEAD.
- Bounded canonical examples PASS: order/default numeric representation, exact Unicode/null/array/bool distinctions, UTF16 key order, 5 fingerprint component mutations and reordered-payload equality.
- Synthetic illustrative fingerprint: 911d4eddba24b24d437c2e7b5fe7a467865c0f82cce6299f9af1b7953a82caba. Input uses an illustrative image hash; this is NOT an image upload/product result.
- Manual semantic review: matrix F01..F24 covers every PM required failure boundary and all 25 uploader preparation cases as mapped above. This is author reasoning, not independent review.
- NOT_RUN: full RFC8785 conformance, product tests/migrations/API/DB/storage/queue crash/Web/typecheck/build and independent review. These require implementation/PM activation.

| File | SHA256 |
| --- | --- |
| docs/architecture/phase-2-upload-contract.md | ab53b327517e6fd24bbff4b08c56a4d64f6dbda1a25f34a436e575858854ea4d |
| docs/architecture/api-contract.md | f494bfbfec6de2742312e1bc22e5aec7f93a714e37171965580e14ea81aa7443 |
| docs/architecture/data-flow.md | d11a9ae800c9b8f5edd6ecb88c3e71638b918993abbd47798ac4fe7a6db02b18 |
| docs/architecture/domain-model.md | 6365a75c80b3ed8fc7b812d1b79100dca7239552dfeea6eaf563ffc23c7d1065 |

Reproducible static checker (read-only, no files or services changed):
```javascript
const fs=require('fs'),path=require('path'),crypto=require('crypto'),cp=require('child_process'),assert=require('assert');
const root=process.cwd(), dir=path.join(root,'docs/architecture');
const names=['phase-2-upload-contract.md','api-contract.md','data-flow.md','domain-model.md'];
const docs=Object.fromEntries(names.map(n=>[n,fs.readFileSync(path.join(dir,n),'utf8')]));
let links=0,examples=0;
for(const [name,s] of Object.entries(docs)){
 assert.equal((s.match(/\x60\x60\x60/g)||[]).length%2,0,name+' fences');
 for(const m of s.matchAll(/\]\(([^)]+)\)/g)){
  if(!m[1].includes('://')&&!m[1].startsWith('#')){assert(fs.existsSync(path.resolve(dir,m[1].split('#')[0])),name+' link '+m[1]);links++;}
 }
 for(const m of s.matchAll(/\x60\x60\x60json\s*\n([\s\S]*?)\n\x60\x60\x60/g)){JSON.parse(m[1]);examples++;}
}
const c=docs[names[0]];
for(let i=1;i<=10;i++)assert(c.includes('## '+i+'.'),'section '+i);
for(let i=1;i<=24;i++)assert(c.includes('| F'+String(i).padStart(2,'0')+' |'),'failure '+i);
for(const m of c.matchAll(/section (\d+)/gi))assert(+m[1]>=1&&+m[1]<=10,'dangling section');
assert(!c.includes('\ufffd'),'replacement character');
assert(c.includes('\ud14c\uc2a4\ud2b8')&&c.includes('\ud55c\uae00'),'literal Unicode examples intact');
const spans=[
 ['api-contract.md','Phase 2 adds optional client_upload_id','Phase 2 is specified by','Phase 3 adds separate'],
 ['data-flow.md','## Phase 2 durable upload agent','## Phase 2 durable upload agent','## Phase 3 processing'],
 ['domain-model.md','## Phase 2 additions','## Phase 2 additions','## Phase 3 additions']];
const norm=s=>s.replace(/^\ufeff/,'').replace(/\r\n/g,'\n');
for(const [n,startOld,startNew,end] of spans){
 const old=norm(cp.execFileSync('git',['show','HEAD:docs/architecture/'+n],{encoding:'utf8'})),cur=norm(docs[n]);
 assert.equal(old.slice(0,old.indexOf(startOld)),cur.slice(0,cur.indexOf(startNew)),n+' preserved prefix');
 assert.equal(old.slice(old.indexOf(end)),cur.slice(cur.indexOf(end)),n+' preserved suffix');
 assert(cur.includes('(phase-2-upload-contract.md)'),n+' cross reference');
}
const wire=JSON.parse([...c.matchAll(/\x60\x60\x60json\s*\n([\s\S]*?)\n\x60\x60\x60/g)][0][1]);
assert.equal(wire.source,'agent');assert.equal(wire.upload_protocol_version,1);
assert(/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/.test(wire.client_upload_id));
assert.equal(wire.metadata_version,1);assert(/^[a-f0-9]{64}$/.test(wire.expected_file_hash));
// Bounded reference for these examples only: ECMAScript number/escaping and UTF-16 key sort.
// Not a general RFC8785 conformance suite or production implementation.
const j=v=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?'['+v.map(j).join(',')+']':'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+j(v[k])).join(',')+'}';
const h=v=>crypto.createHash('sha256').update(j(v),'utf8').digest('hex');
assert.equal(j({b:1.0,a:'\ud55c\uae00'}),j({a:'\ud55c\uae00',b:1}));
assert.notEqual(h({note:'\u00e9'}),h({note:'e\u0301'}));
assert.notEqual(h({note:null}),h({}));assert.notEqual(h([1,2]),h([2,1]));assert.notEqual(h(true),h(1));
assert.equal(j(-0),'0');assert.equal(j(JSON.parse('1e0')),j(1));
assert.equal(j({'\ue000':2,'\ud83d\ude00':1}),'{"\ud83d\ude00":1,"\ue000":2}');
const base={fingerprint_version:1,upload_protocol_version:1,project_id:'11111111-1111-4111-8111-111111111111',...wire,original_filename:'tutorial-ja.png',file_hash:wire.expected_file_hash,media_type:'image/png',size_bytes:2048,width:1280,height:720};
delete base.client_upload_id;delete base.expected_file_hash;
for(const [key,value] of [['source','automation'],['original_filename','other.png'],['file_hash','b'.repeat(64)],['situation_id','77777777-7777-4777-8777-777777777777'],['metadata',{note:null}]]){
 assert.notEqual(h(base),h({...base,[key]:value}),key+' must distinguish intent');
}
assert.equal(h(base),h(Object.fromEntries(Object.entries(base).reverse())));
console.log('PASS static: 4 documents, '+links+' links, '+examples+' JSON examples, sections 1..10, F01..F24, Phase1 prefix/suffix preserved.');
console.log('PASS bounded canonical examples: ordering/numbers/Unicode/null/array/bool distinctions; 5 payload mutations; reordered payload identical.');
console.log('Synthetic fingerprint (illustrative image hash, not a real upload): '+h(base));
for(const n of names)console.log(n+' SHA256 '+crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,n))).digest('hex'));
console.log('NOT_RUN: full RFC8785 conformance, production HTTP/DB/queue/crash/Web tests and independent review.');

```
