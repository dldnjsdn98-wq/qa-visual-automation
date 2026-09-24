# Domain model — ARCH-001

Revision 2: targeted correction of R08-ARCH-001; existing design retained; independent re-review pending.

Architect contract; independent review pending. SQL tables below use server UUID primary keys named id unless specified. Times are timestamptz, serialized as UTC RFC3339. Columns are NOT NULL unless marked ?. created_at/updated_at are server managed. No screenshot binary columns.

## Phase 1 tables

Database and client encoding must be UTF8. All persisted text/varchar fields and every recursive JSONB string value/object key follow the API persistable Unicode policy: exclude U+0000 and residual U+D800–U+DFFF; supplementary scalars are valid. Validate before DB writes or object publication, with 422 VALIDATION_ERROR rather than trimming/repairing invalid data. Preserve accepted StringEntry text exactly, including empty strings, whitespace and combining sequences. Declared character limits count decoded Unicode scalars. PostgreSQL encoding/type restrictions provide the final boundary; no new column/table is required for R08-ARCH-001.

| Table | Columns | Uniqueness / checks |
| --- | --- | --- |
| projects | id, slug varchar(64), name varchar(120), description text?, created_at, updated_at | unique(slug) |
| builds | id, project_id, label varchar(120), description text?, created_at, updated_at | unique(project_id,label), unique(project_id,id) |
| locales | id, project_id, code varchar(63), name varchar(120), created_at, updated_at | unique(project_id,code), unique(project_id,id) |
| categories | id, project_id, slug varchar(64), name varchar(120), created_at, updated_at | unique(project_id,slug), unique(project_id,id) |
| situations | id, project_id, category_id, slug varchar(64), name varchar(120), description text?, created_at, updated_at | unique(project_id,category_id,slug), unique(project_id,id), unique(project_id,category_id,id) |
| string_keys | id, project_id, string_id varchar(128), description text?, created_at, updated_at | unique(project_id,string_id), unique(project_id,id) |
| string_entries | id, project_id, build_id, string_key_id, locale_id, text text, created_at, updated_at | unique(project_id,build_id,string_key_id,locale_id); text length <=10000 |
| situation_expected_strings | project_id, build_id, situation_id, string_key_id, position integer | PK(project_id,build_id,situation_id,string_key_id); unique(project_id,build_id,situation_id,position); position >=0 |
| screenshots | id, project_id, build_id, locale_id, category_id, situation_id, source varchar(32), original_filename varchar(255), uploaded_at, storage_key text, file_hash char(64), media_type varchar(32), size_bytes bigint, width integer, height integer, metadata_version integer default 1, metadata JSONB default {}, client_upload_id UUID? | unique(storage_key), unique(project_id,id); positive size/width/height; metadata_version=1; metadata is JSON object; hash lowercase SHA-256 hex; Phase 1 source='manual', client_upload_id IS NULL |

API StringEntry.string_id is joined from StringKey, never generated from text or the row UUID. Example: string_id=tutorial_welcome_001, locale=ja-JP, build=1.0.0, text=ようこそ. Build 1.0.1 has separate translation rows. There is no implicit build/locale fallback. Empty text is an existing translation, not missing.

## Relationships and DB enforcement

Every child table has project_id → projects.id. All FKs use ON DELETE RESTRICT; no automatic cascades. In addition:

- Situation (project_id,category_id) → categories(project_id,id).
- StringEntry (project_id,build_id) → builds(project_id,id), (project_id,locale_id) → locales(project_id,id), (project_id,string_key_id) → string_keys(project_id,id).
- SituationExpectedString has composite project/id FKs to Build, Situation and StringKey.
- Screenshot has composite project/id FKs to Build and Locale, and (project_id,category_id,situation_id) → situations(project_id,category_id,id). This enforces Category/Situation agreement even for direct SQL writes.

Project has many Builds, Locales, Categories and StringKeys. Category has many Situations. StringKey has many translations across Builds/Locales. Build + Situation has many StringKeys through SituationExpectedString; keys may appear in many Situations. Screenshot belongs to exactly one Build, Locale and Situation/Category. Screenshot does not require translation rows: incomplete catalogs must still accept images.

Explicit indexes: project_id on every child; entries (project_id,build_id,locale_id,string_key_id); expected mappings (project_id,string_key_id) and (project_id,situation_id); screenshots (project_id,uploaded_at DESC,id DESC), (project_id,build_id,locale_id,situation_id,uploaded_at DESC,id DESC), (project_id,category_id), (project_id,locale_id), (project_id,situation_id). Add entries reverse key/locale indexes for FK checks. Unique indexes cover their left prefixes. Measure before adding JSON indexes. file_hash is not unique: identical pixels can have different legitimate context.

## Identity, edits and deletion

Project slug, Build label, Locale code, Category slug, Situation category/slug, StringKey string_id and ownership IDs are immutable. Names/descriptions and StringEntry text are mutable. Correct identity mistakes by replacement after explicit unlinking. Build catalogs remain editable; Expected Strings are current catalog values, not upload-time evidence. PATCH and full mapping replacement are last-write-wins; no optimistic concurrency guarantee in Phase 1.

DELETE on referenced Project/Build/Locale/Category/Situation/StringKey returns 409 RESOURCE_IN_USE. StringEntry can be deleted while its key remains expected, producing a missing translation. PUT an empty expected list to unlink a Build/Situation. Screenshots block parent deletion; Phase 1 has no screenshot DELETE, so such parents cannot be removed through the API. No hidden cascade.

## Extensible screenshot metadata

Relational immutable core: project/build/locale/category/situation/source/original_filename/uploaded_at. Server-derived operational fields: storage key, hash, MIME, bytes and decoded dimensions. metadata_version=1 describes capture context, not DB migration version.

metadata optionally accepts run_id (UUID string), device (string <=200), resolution ({width,height}, positive integers <=16384), scenario/checkpoint/screen_state (strings <=128). Present reserved fields cannot be null; omission means unknown. Supplied resolution must equal decoded image dimensions. Unknown keys accept JSON values subject to the shared Unicode policy on all keys and nested string values. Maximum serialized UTF-8 size 16 KiB, nesting depth 5, at most 100 object keys total, no NaN/Infinity. Validate Unicode before UTF-8 size calculation; use compact JSON with literal Unicode (Python equivalent ensure_ascii=False, separators=(',', ':'), allow_nan=False) for the decoded object's size. Root object has container depth 1; each nested object/array adds 1; scalar leaves add none. Future context identifiers are not Phase 1 FKs and cannot override relational fields. Arbitrary metadata filtering is out of scope.

## Phase 2 additions - contract pending independent review

[P2-UPLOAD-v1 revision 2](phase-2-upload-contract.md) specifies additive upload_receipts, Screenshot source/client-ID constraints and partial uniqueness, canonical fingerprint version, state/lease/fence invariants, retention and restrictive identity FKs. It supersedes this former outline only; existing manual rows and accepted Phase 1 relationships remain unchanged.

## Phase 3 additions — not implemented

OCRResult has a project-scoped Screenshot FK (many reruns), engine/version, processing status, error?, timestamp and image dimensions/orientation. OCRRegion belongs to OCRResult, with text, bounding_box={x,y,width,height} in original decoded pixel coordinates, confidence [0,1] and reading order. Boxes stay within image bounds; resized/rotated worker coordinates must be transformed back.

VerificationResult links Screenshot and OCRResult with algorithm/version, configuration snapshot, expected catalog snapshot, aggregate verification_status and timestamps. VerificationItem links StringKey, optional StringEntry and OCRRegion, preserving expected/observed text snapshots, match method, match_score [0,100] and verification_status PASS|REVIEW|FAIL. Missing expected translation is explicitly unverified, with no fabricated score. Processing status PENDING|RUNNING|SUCCEEDED|FAILED is separate from language quality status. Composite project FKs prevent cross-project links. Configurable candidate thresholds: >=95 PASS; >=85 and <95 REVIEW; <85 FAIL. Aggregation and calibration are Phase 3 work; no Phase 1 verification fields.

## Phase 4–6 boundary — not implemented

| Domain | Responsibility / future relationships |
| --- | --- |
| ScreenState | Project-owned state identity, versioned visual definition |
| VisualAnchor | Template/region/threshold; required/optional/forbidden state membership |
| Action | Typed allowed ADB input with bounded parameters, separate from detection |
| Transition | Directed edge: id, project_id, from_state, to_state, action, nonnegative finite cost, timeout/retry limits; FKs to states/Action |
| Scenario | Versioned steps/targets and recovery policy; transitions/checkpoints |
| Checkpoint | Capture intent and project/build/locale/category/situation mapping |
| AutomationRun | Scenario version execution, device context, timestamps/outcome; optional later relation to screenshot metadata.run_id |

Multiple edges between the same states are allowed; no unique(from_state,to_state). Costs cannot be negative/nonfinite. Recording stores before/after images, input action, timestamp and detected states/confidence; inferred edges remain review candidates. Every executed transition requires bounded next-state verification/recovery. Visual Automation → captures/pending → Screenshot Upload Agent → Backend. No automation tables or execution in Phase 1.
