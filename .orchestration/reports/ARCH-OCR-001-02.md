# ARCH-OCR-001 / Architect02 report

Date: 2026-09-25 KST
Status requested: READY_FOR_REVIEW (contract only).
Branch / commit: null / null.
Contract: docs/architecture/phase-3-ocr-contract.md, P3-OCR-v1 revision1.
SHA-256: 46940dd1dd7775422213b2ba422b63650f4e83740e034cf29dc83f23970acb82

## Goal, scope and gates

Finalize Phase3 OCR/verification contract from existing requirements, source facts and four role preparation reports. Phase2 independently ACCEPTED and its four AC PASS are historical inputs; no Phase2 tests were rerun. Phase3 implementation stays BLOCKED until Reviewer08 accepts this exact revision and PM01 grants exact file claims. AC-P3-01..04 remain NOT_RUN.

Only three new files written: docs/architecture/phase-3-ocr-contract.md, this report, and .orchestration/handoffs/ARCH-OCR-001-02.md. No existing architecture/product/PM YAML/DECISIONS/mobile files edited. No branch, commit, push, deployment, data deletion, DB reset, credentials/security changes or IP checks. Read-only sandbox writes used explicit approved escalation, not a bypass. No denied action repeated.

Completion for this task is concrete normative contract, preparation question dispositions, static/reference evidence, exact artifact hashes and PM review submission. This is not implementation completion or independent approval.

## Result and current source evidence

Contract defines explicit idempotent run creation, same-MVCC copied snapshot, append-only results, durable PostgreSQL queue, fenced attempts/renew/finalize/recovery, finite budgets, original-raster geometry, model provenance/qualification, conservative normalization/rational Levenshtein matching, deterministic global one-to-one assignment, error versus quality semantics and paged API/Web history.

Current expected resolver uses a LEFT JOIN without fallback; present empty differs from missing. Mapping replacement is transactional with Build locking. Existing DB default is REPEATABLE READ, while job mutations need explicit READ COMMITTED. Stored width/height are raw Pillow raster without EXIF transpose. Worker/test trees are scaffolding; dependencies and actual inference do not exist. These facts constrain the new contract; they are not OCR test evidence.

All role preparation reports were read; first combined tool output truncated, then targeted reads recovered Frontend, engine/runtime and Reviewer decisions. Report hashes independently matched:
- Backend03: 253d8821fb5111db2e217401be7c1edd60a0d86456ee4ab75b81b18aba5a7105
- Frontend04: 8bbf33936d463f854ee414277ce02db78aadb5bd109ed272c4aeff700ad622f0
- OCR05: 556a29eef0cfb486e44f1896c4b6ff4f720198072215178bad711dc087a0630e
- Reviewer08: 310c2a6bef3a929de7b9fc5293cb53896df9a31ab333f7371ab310d6c6468a8d

## Backend03 question dispositions

| Question | Final decision / contract section |
| --- | --- |
| B01 identity/scope/retention | Project/client UUIDv4, canonical UUID, fingerprint conflict/replay, no TTL; 2/10.1 |
| B02 trigger/outbox | Explicit POST only; PostgreSQL job is queue/outbox; 1/3 |
| B03 states/errors/retries | Five states, fixed allowlist, claims max3, 5/10s delay, 300s budget; 3/4/10.1 |
| B04 lease/time/overflow | DB clock,60s lease,renew<=20s,strict expiry,5s lock/10s statement/idle bound,bigint no wrap; 3/10.2 |
| B05 ambiguity | Durable claim_request_id/token; fresh locked primary recovery for create/claim/renew/finalize; 2/10.2 |
| B06 retry/rerun | Same run immutable retry; new ID/snapshot for rerun, screenshot grouping is lineage; 1/10.1 |
| B07 snapshot instant | First MVCC data query, one REPEATABLE READ transaction; 1 |
| B08 columns/FKs | Ordered exact copied values, no live catalog FK; Screenshot scoped RESTRICT; 1/10.1 |
| B09 missing/empty/no text/error | UNVERIFIED reasons/null score; no candidate FAIL; processing failure null quality; 6 |
| B10 coordinates | Raw original raster, EXIF ignored, explicit inverse matrix, polygon+AABB; 5 |
| B11 versions | Immutable exact profile/dictionary/model/config hashes, required runtime qualification; 4/10.3 |
| B12 boundaries | Rational >=95 PASS, >=85 REVIEW, display rounding afterwards; 6 |
| B13 APIs | Explicit scoped routes/pages,202new/200replay,Location,Retry-After and unknown enum fallback; 2/10.4 |
| B14 retention | Indefinite run evidence; screenshot/project restrictions; copied catalog values retained; 10.1 |
| B15 attempts | STARTED attempt may close once; terminal attempts immutable; 10.1 |
| B16 reaper/cleanup | Expiry recovery and third-attempt failure under lock; no history/original deletion; 3/10.1 |
| B17 ownership |03 durable runner/DB/storage;05 pure supervised adapters; sole pyproject editor03; 3/9/10.3 |
| B18 corrupt snapshot | Fail closed SNAPSHOT_INTEGRITY_ERROR; never live resolver fallback; 4/10.1 |
| Additional | Same-buffer bytes hash/decode prevents second-open race; database append-only triggers; position gaps preserved; copied context display facts; 4/10.1 |

## Frontend04 question dispositions

| Question | Final decision / section |
| --- | --- |
| F01 routes/schema | Scoped run/expected/OCR/verification pages and summaries; 2/6/10.4 |
| F02 states | PENDING/RUNNING/RETRY_WAIT/SUCCEEDED/FAILED with mutual field constraints; 10.1 |
| F03 geometry | Original-raster polygon3..8 clipped vertices, retained raw quad audit,integer bbox; 5 |
| F04 precision | Recognition binary64[0,1],match six-decimal display plus rational; 6/10.3 |
| F05 snapshot | Creation first MVCC query, not upload/worker time; 1 |
| F06 semantic cases | Missing/empty/normalized-empty UNVERIFIED; no OCR FAIL for nonempty; error quality null; 6 |
| F07 empty assertion | Not an absence assertion; explicit UNVERIFIED; 6 |
| F08 aggregate | FAIL then REVIEW then UNVERIFIED then PASS; counts/incomplete; 6 |
| F09 latest | selection=all/succeeded before page; newest requested vs newest successful processing incl UNVERIFIED; 10.4 |
| F10 ambiguous submit | Session-persist same request/client ID;200/202 supported;409 conflict; 2/10.4 |
| F11 poll/history |2s visible active polling,error backoff,terminal stop,Retry-After,selected run deep link and immutable history; 10.4 |
| F12 safe error | Safe fixed text/code/stage/attempt/correlation/cause;retryable authoritative for automatic run retry; 2/10.1 |

Raw browser EXIF mismatch requires a proven display transform before optional overlay. Mandatory table remains usable. Independent child loading/error/page state and safe multilingual text are required. Ten-file Frontend claim is a future PM proposal only.

## OCR05 eight-question dispositions

| Question | Final decision / section |
| --- | --- |
| E01 locales | Initial qualification en/ko/ja/zh-Hans/zh-Hant with explicit aliases; other tags fail; 10.3 |
| E02 Korean pair | Separate candidate v6 medium detector/v5 Korean recognizer; real mixed-pipeline qualification required, failure requires reviewed alternative; 10.3 |
| E03 locale identity | Snapshot project locale UUID and raw code plus explicit resolved family; 1/10.1 |
| E04 CPU medium | Candidate medium CPU FP32 with fixed budgets; actual Windows/Linux resource proof required; 10.2/10.3 |
| E05 confidence | Recognition mandatory; separately nullable detection with explicit unavailable reason; 5/10.3 |
| E06 polygon | Clockwise canonical vertices,6-decimal display geometry,raw audit retained,explicit clip; 5 |
| E07 transforms | Public original raw raster only; every preprocessing inverse recorded and tested; 5 |
| E08 orientation |0/180 qualification;90/270/vertical capability probes with visible coverage limit;numeric transform tests required regardless; 10.3 |

PaddleOCR3.7.0/PaddlePaddle3.3.1/RapidFuzz3.14.6 are Owner05 research candidates, not compatibility acceptance. Transitive lock/OpenCV/model hashes and licenses remain concrete post-gate qualification work. No placeholder hash permits AVAILABLE. No install/model download/inference or denied Docker inventory repeat performed.

## Reviewer08 and independent sidecar dispositions

All critical recommendations adopted: copied snapshot, source integrity, fence on error/terminal paths, fresh-primary ambiguity recovery, immutable retry vs new rerun, additive post0003 migration, mutually constrained processing/quality, real evidence separated from deterministic fixtures. O01..O22 and all four AC mapped.

Explicit alternative choices:
- Reviewer NFC-only preference: norm-v1 additionally collapses the exact Unicode White_Space set and trims; raw text and method remain visible. No casefold/NFKC/punctuation deletion.
- Reviewer null-quality missing item suggestion: successful missing/empty item uses UNVERIFIED with null score; nonterminal/processing-failed run quality remains null.
- Reviewer reject out-of-bounds preference: geometric clipping is explicit with retained raw polygon and clipped flag, never silent point clamping. Fully outside/degenerate/malformed polygons fail.
- Empty raw region is retained as unmatchable diagnostic; no_text covers no eligible normalized texts, not merely zero arrays.
- Candidate global assignment maximizes exact/normalized evidence before cardinality; adversarial100/90,90/80 chooses exact+unmatched intentionally.
- Initial unsupported Arabic OCR is explicit; Arabic/RTL raw rendering and deterministic matching fixtures remain required. No mock or unsupported locale claims actual OCR AC PASS.

Two prior read-only sidecars closed after completion: Franklin01a0d64b-f08c-7f12-97d0-f3d81262ea49 matching; Hubble01a0d64b-f187-7c31-985a-c3bea9305d35 coordinates. Both high, requested Sol/high, actual unverified. Adopted deterministic tie concerns, conservative raw preservation, inverse transforms and clipping degeneracy checks. Rejected sidecar NFKC/casefold, empty PASS, rounded-threshold decisions and cardinality-first objective for reasons above. Parent integrated and checked findings; sidecars did not approve contract.

Main task highest, requested Astra/medium; actual unverified. No auditable model telemetry claimed. Two initial JavaScript tool syntax failures executed nothing and were corrected; not product or model-compatibility failures.

## Actual validation

Environment: Windows PowerShell, C:/Dev/qa-visual-automation, Node v24.19.0, Node Unicode17.0. Node normalization probes below use representative common codepoints only; they do not validate Python Unicode15.0.0 or pinned RapidFuzz.

- Read-only Get-Content/Node fs UTF8 and focused rg source/role/gate inspection: completed.
- SHA256 of preparation artifacts and existing architecture: matched.
- Reference Node script below: exit0,35 assertions PASS (numeric boundaries, scalar Levenshtein, common NFC/whitespace examples, global assignment duplicates/ties/adversarial objective, inverse transforms/AABB, simple fence/snapshot model).
- Saved-document Node check below: exit0,6 links resolved,10 sections,22 matrix rows,4 AC markers,JSON fence parses,old architecture3 hashes unchanged.
- git diff --check -- docs/architecture/phase-3-ocr-contract.md: exit0; untracked file is not covered by tracked diff, so separate saved-file checks are authoritative.
- Final artifact encoding/fence check initially returned exit1 because its unanchored fence counter counted literal triple backticks inside the embedded checker program. Corrected to line-start fence delimiters; this is a checker false positive, not a document/product failure.
- git status --short -- three owned paths: new contract observed; report/handoff created afterwards.
- pytest, real RapidFuzz, Python15 normalization conformance, OCR models, Windows/Linux parity, PostgreSQL concurrency/migrations, generated OpenAPI, Frontend tests/typecheck/build/browser: NOT_RUN. Reference state simulation is not DB durability evidence.

Existing architecture hashes unchanged:
- api-contract.md abcab2109becbe6938628aa3810bc547a33a8b2cc23348c71d8688bf6e7a0e70
- domain-model.md 4147fde8c52e084b974f2fbc0f9cde14d493bd1442d234f01be9bdfb51680c1a
- data-flow.md 08cb9119712d4731830d6b5513b6c38a1857f04360c9595f9c6eddb8be4f6f86

Exact reference program executed via PowerShell node -e with single-quote escaping; it creates no file:
```javascript
const assert=require('node:assert/strict');
let checks=0;
function eq(a,b){assert.deepEqual(a,b);checks++;}
function lev(a,b){a=Array.from(a);b=Array.from(b);let row=Array.from({length:b.length+1},(_,i)=>i);for(let i=0;i<a.length;i++){let next=[i+1];for(let j=0;j<b.length;j++)next.push(Math.min(next[j]+1,row[j+1]+1,row[j]+(a[i]!==b[j])));row=next;}return row[b.length];}
function cls(n,d){return n>=95*d?'PASS':n>=85*d?'REVIEW':'FAIL';}
for(const [n,d,w] of [[100,1,'PASS'],[95,1,'PASS'],[94999999,1000000,'REVIEW'],[85,1,'REVIEW'],[84999999,1000000,'FAIL'],[0,1,'FAIL']])eq(cls(n,d),w);
for(const [k,w] of [[0,'PASS'],[1,'PASS'],[2,'REVIEW'],[3,'REVIEW'],[4,'FAIL']]){const d=lev('a'.repeat(20),'b'.repeat(k)+'a'.repeat(20-k));eq(d,k);eq(cls(100*(20-d),20),w);}
const norm=s=>s.normalize('NFC').replace(/\r\n?/g,'\n').replace(/[\u0009-\u000d\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+/gu,' ').replace(/^ +| +$/g,'');
eq(norm('e\u0301'),'é');eq(norm(' \tA\u00a0 B\r\n'),'A B');eq(norm('Ａ'),'Ａ');eq(norm('A')===norm('a'),false);eq(norm('\u200b\ufeff'),'\u200b\ufeff');eq(norm(' \n'),'');eq(lev('😀','😁'),1);
function assignment(m){let best=null;function walk(i,used,v,obj){if(i===m.length){let score=[...obj,...v.map(x=>-x)];if(!best||score.some((x,j)=>x!==best.score[j]&&score.slice(0,j).every((y,k)=>y===best.score[k])&&x>best.score[j]))best={score,v};return;}for(let j=0;j<=m[i].length;j++){if(j<m[i].length){let e=m[i][j];if(used.has(j)||!e||e.score<85)continue;walk(i+1,new Set([...used,j]),[...v,j],[obj[0]+(e.method==='E'),obj[1]+(e.method==='N'),obj[2]+1,obj[3]+Math.floor(e.score*1e6)]);}else walk(i+1,used,[...v,j],obj);}}walk(0,new Set(),[],[0,0,0,0]);return best.v;}
const E={score:100,method:'E'},F={score:90,method:'F'};
eq(assignment([[E],[E]]),[0,1]);eq(assignment([[E,E],[E,E]]),[0,1]);eq(assignment([[E,F],[F,{score:80,method:'F'}]]),[0,2]);eq(assignment([[F,F],[F,F]]),[0,1]);
const inv=([u,v])=>[(u-10)/.5,(v-20)/.5];
const points=[[60,70],[160,70],[160,95],[60,95]].map(inv);
eq(points,[[100,100],[300,100],[300,150],[100,150]]);
function bbox(p){let x=Math.floor(Math.min(...p.map(q=>q[0]))),y=Math.floor(Math.min(...p.map(q=>q[1])));return[x,y,Math.ceil(Math.max(...p.map(q=>q[0])))-x,Math.ceil(Math.max(...p.map(q=>q[1])))-y];}
eq(bbox(points),[100,100,200,50]);eq(points.map(([x,y])=>[600-y,x]).map(([u,v])=>[v,600-u]),points);
function fenced(state,gen,token,now){return state.status==='RUNNING'&&state.generation===gen&&state.token===token&&state.lease>now;}
const state={status:'RUNNING',generation:2,token:'new',lease:60};
eq(fenced(state,2,'new',59),true);eq(fenced(state,2,'new',60),false);eq(fenced(state,1,'old',59),false);eq(fenced({...state,status:'SUCCEEDED'},2,'new',59),false);
const catalog={text:'old'},snapshot=structuredClone(catalog);catalog.text='new';eq(snapshot.text,'old');
console.log(JSON.stringify({reference_checks:checks,result:'PASS',node:process.version,unicode:process.versions.unicode,scope:'reference only; not RapidFuzz, Python Unicode15, PostgreSQL or real OCR'}));
```

Exact saved-document program executed with the same node -e transport:
```javascript
const f=require('fs'),p=require('path'),c=require('crypto'),a=require('assert/strict');
const file='docs/architecture/phase-3-ocr-contract.md',s=f.readFileSync(file,'utf8');
const links=[...s.matchAll(/\]\(([^)]+)\)/g)].map(m=>m[1]);for(const link of links)a.ok(f.existsSync(p.resolve(p.dirname(file),link)),link);
a.equal((s.match(/^## /gm)||[]).length,10);a.equal((s.match(/^\| O\d\d \|/gm)||[]).length,22);
for(let i=1;i<=4;i++)a.ok(s.includes('AC-P3-0'+i));
for(const m of s.matchAll(/```json\n([\s\S]*?)```/g))JSON.parse(m[1]);
a.equal((s.match(/```/g)||[]).length%2,0);
a.ok(!s.includes('SOURCE_INTEGRITY_ERROR'));
const baselines={'docs/architecture/api-contract.md':'abcab2109becbe6938628aa3810bc547a33a8b2cc23348c71d8688bf6e7a0e70','docs/architecture/domain-model.md':'4147fde8c52e084b974f2fbc0f9cde14d493bd1442d234f01be9bdfb51680c1a','docs/architecture/data-flow.md':'08cb9119712d4731830d6b5513b6c38a1857f04360c9595f9c6eddb8be4f6f86'};
for(const [name,hash] of Object.entries(baselines))a.equal(c.createHash('sha256').update(f.readFileSync(name)).digest('hex'),hash);
console.log(JSON.stringify({result:'PASS',links:links.length,sections:10,matrix:22,acs:4,old_architecture_hashes_unchanged:3,bytes:Buffer.byteLength(s),contract_sha256:c.createHash('sha256').update(s).digest('hex')}));
```

## Remaining gates and handoff

No known unanswered preparation decision remains; runtime manifests/compatibility/accuracy/resource/license evidence intentionally remain implementation qualification gates, not author proof. Reviewer08 must independently review exact contract semantics, especially assignment priority, empty/UNVERIFIED aggregation, clipped geometry and durable ambiguity handling. PM alone activates review and implementation claims. This submission does not authorize implementation, later phases or package/model installation. Same-cause3 correction-review pause rule remains; no contract correction-review cycles have occurred for revision1.
