# API contract — /api/v1 — ARCH-001

Revision 2: targeted correction of R08-ARCH-001; existing design retained; independent re-review pending.

Status: implementation-ready architect specification; independent review pending. These business endpoints are not implemented by ARCH-001. Existing GET /health → {"status":"ok"} and GET /ready → {"status":"ready"} or 503 {"detail":"Database unavailable"} remain outside this contract.

## Common types and behavior

Notation: `?` after a field means it may be omitted in requests; `T|null` allows an explicit null. Response fields shown are always present. Object definitions are closed unless stated otherwise. UUIDs are UUID strings. Timestamp is UTC RFC3339, e.g. 2026-09-05T03:00:00Z. IDs/timestamps are server assigned. All JSON requests use application/json; upload uses multipart/form-data. Respond with application/json except 204 and image content.

- Slug: 1–64 ASCII characters, regex ^[a-z0-9]+(?:-[a-z0-9]+)*$.
- Name and BuildLabel: 1–120 characters after outer whitespace trimming. BuildLabel is case-sensitive.
- StringId: 1–128 ASCII characters, regex ^[A-Za-z0-9][A-Za-z0-9_.-]*$, case-sensitive. Never accept text as identity.
- Description: string <=2000 Unicode scalar values or null; default null. Text: 0–10000 Unicode scalar values excluding U+0000, subject to the shared Unicode policy below; preserve accepted whitespace, line endings and normalization exactly as JSON decoded. No automatic localization normalization. Limits count decoded scalar values, not UTF-8 bytes, UTF-16 code units or grapheme clusters.
- LocaleCode: a deliberately restricted Phase 1 BCP-47 subset: 2–3 ASCII-letter language, optional 4-letter script, optional 2-letter or 3-digit region, hyphen separators only. Canonicalize language lowercase, script Titlecase, alphabetic region uppercase before uniqueness checks (JA-jp → ja-JP). Private-use, extensions and variants are 422 UNSUPPORTED_LOCALE_CODE in Phase 1. This is a product subset, not a claim to support every BCP-47 tag.
- Unknown body/query fields, repeated scalar query parameters, invalid enum/UUID, or empty required strings → 422 VALIDATION_ERROR. PATCH accepts only declared mutable fields, requires at least one field, and null is allowed only for description. No implicit identity changes.
- Resolve parent Project first, then scoped resource. Unknown or out-of-project references → 404 RESOURCE_NOT_FOUND without revealing foreign ownership. Known same-project Category/Situation mismatch → 422 RELATIONSHIP_MISMATCH.
- POST create → 201 with resource and Location header; GET/PATCH/PUT → 200; DELETE → 204 empty. Repeated DELETE of missing resource → 404. Unique identity conflict → 409 DUPLICATE_RESOURCE. Referenced delete → 409 RESOURCE_IN_USE.
- Collections use `limit` integer default 50, 1–100; `offset` integer default 0, >=0. Page<T>={items:T[],total:integer,limit:integer,offset:integer}; total is filtered count before pagination, empty pages are valid. Count/items are read from one consistent statement/snapshot. Offset pages can shift across requests when concurrent writes occur; no cross-request snapshot guarantee.
- Default sort is created_at ASC,id ASC. Screenshot sort is uploaded_at DESC,id DESC. No arbitrary sort parameter. PUT expected mappings has its own ordering.
- Filters combine with AND; no implicit string/locale/build fallback. Valid-shaped but nonexistent scoped filter references → 404. Category/Situation mismatch → 422. Absent filter means all values within Project.

### Persistable Unicode policy — R08-ARCH-001 correction

All decoded request string values and object keys must be Unicode scalar sequences without U+0000. Reject any residual surrogate code point U+D800–U+DFFF (including unpaired high/low surrogates), and reject malformed UTF-8 transport. Apply this rule to every create/patch field, query/path string, multipart filename, reserved metadata field and recursively to all unknown metadata keys/values, including strings inside nested arrays/objects. Run it before field-specific trimming/canonicalization/filename sanitization so forbidden characters are never silently stripped. Valid JSON escaped surrogate pairs decode to their single supplementary-plane scalar and are accepted, as are literal UTF-8 supplementary characters. Do not reject ordinary valid emoji, CJK, combining marks, variation selectors, tabs, newlines or empty Text solely because of this policy; field-specific limits still apply.

Validation order: strict UTF-8/JSON decode → recursive Unicode check → declared field types, length/shape and bounded metadata checks → scope checks → persistence. Multipart parsing may create private staging, but rejected Unicode must cause **no published storage object and no application DB write**; discard any staging. No replacement character insertion, NUL removal or surrogate repair. Invalid input returns 422 VALIDATION_ERROR, never an input-caused 500/503 from a DB adapter. Raw undecodable input uses field `body` (JSON), `metadata` (metadata part) or `file.filename`; decoded StringEntry failures use `body.text`. Metadata value paths start `metadata.metadata`, e.g. `metadata.metadata.steps[0].note`. For an invalid object key report its containing object path, not the offending key. Reasons are fixed safe messages: `U+0000 is not allowed`, `unpaired Unicode surrogate is not allowed`, `invalid UTF-8`, or the corresponding `object key ...` reason. Error serialization/logging must not embed rejected payloads or unsafe keys.

PostgreSQL text cannot hold NUL and JSONB rejects NUL and invalid surrogate escapes. Use UTF8 database and client encoding. These constraints motivate the shared boundary policy; they do not require a schema redesign. References: [PostgreSQL 17 character types](https://www.postgresql.org/docs/17/datatype-character.html), [PostgreSQL 17 JSON types](https://www.postgresql.org/docs/17/datatype-json.html).

| Boundary fixture (JSON escape notation) | Required behavior |
| --- | --- |
| Text `"hello\u0000world"` in create or patch | 422 body.text; no DB write; original stored text unchanged on failed patch |
| Metadata value, nested array value, or object key containing `\u0000` | 422 at safe value/container path; no publication/row |
| Text or metadata key/value with `\ud800` or `\udfff` alone, or reversed pair | 422, no repair |
| Text `"\ud83d\ude00"` and literal `"😀"` | Both accepted as the same scalar; scalar length 1 |
| Text `"ようこそ 한글 e\u0301\r\n\t"` | Accepted and preserved including combining sequence and whitespace |
| Text `""` | Accepted, remains present translation |
| Filename containing NUL before otherwise valid basename | 422 file.filename before basename/control sanitization |

Thread 03 must implement HTTP tests for these cases in StringEntryCreate/Patch and ScreenshotUpload, plus representative name/description and nested-key cases. Verify accepted values through PostgreSQL-backed readback; rejected values must not reach repository writes or Storage.publish. The architecture-only fixtures in `unicode-cases.json` and checker validate the specified Unicode boundary independently of production code; they do not constitute API/DB tests. Thread 04 should mirror the scalar-length rule (`Array.from(value).length` after surrogate validation), retain valid input exactly and show server field errors without silent repair. Server remains authoritative.

### Error model

Every /api/v1 failure, including request parsing/validation, uses:

```json
{"error":{"code":"VALIDATION_ERROR","message":"Request validation failed","details":[{"field":"body.name","reason":"must not be empty"}],"request_id":"a22be0d1-32b1-4542-b1eb-c9eb6e9fc080"}}
```

Error={error:{code:string,message:string,details:ErrorDetail[],request_id:UUID}}. ErrorDetail={field:string|null,reason:string}. Details defaults to []. Field paths use body.*, query.*, path.*, metadata.*, file. All responses include X-Request-ID generated by server (ignore untrusted incoming value). Do not echo file contents, secrets or SQL in errors. HTTP error statuses retain normal semantics, including 405 METHOD_NOT_ALLOWED and 404 for unknown business routes.

| Status | code | Meaning |
| --- | --- | --- |
| 400 | INVALID_MULTIPART | Malformed multipart framing |
| 404 | RESOURCE_NOT_FOUND | Unknown/scoped resource or filter |
| 409 | DUPLICATE_RESOURCE / RESOURCE_IN_USE | Unique conflict / restrictive delete |
| 413 | UPLOAD_TOO_LARGE | File or complete request limit exceeded |
| 415 | UNSUPPORTED_MEDIA_TYPE | Unsupported body/file media format |
| 422 | VALIDATION_ERROR / RELATIONSHIP_MISMATCH / INVALID_IMAGE / UNSUPPORTED_LOCALE_CODE | Field, relation, corrupt image, unsupported locale subset |
| 503 | STORAGE_UNAVAILABLE / DATABASE_UNAVAILABLE | Transient infrastructure failure; Retry-After: 5 |
| 500 | INTERNAL_ERROR | Unexpected server fault |

A 503/timeout does not guarantee no upload committed; automatic upload retry is out of scope in Phase 1. Generic malformed JSON is 422 VALIDATION_ERROR. API framework handlers must convert default error bodies to this envelope.

## Resource request / response models

Audit={created_at:Timestamp,updated_at:Timestamp}. Names below include all fields; `+ Audit` means these two required fields are flattened.

| Model | Fields |
| --- | --- |
| ProjectCreate | slug:Slug, name:Name, description?:Description |
| ProjectPatch | name?:Name, description?:Description |
| Project | id:UUID, slug:Slug, name:Name, description:Description + Audit |
| BuildCreate | label:BuildLabel, description?:Description |
| BuildPatch | description:Description |
| Build | id:UUID, project_id:UUID, label:BuildLabel, description:Description + Audit |
| LocaleCreate | code:LocaleCode, name:Name |
| LocalePatch | name:Name |
| Locale | id:UUID, project_id:UUID, code:LocaleCode, name:Name + Audit |
| CategoryCreate | slug:Slug, name:Name |
| CategoryPatch | name:Name |
| Category | id:UUID, project_id:UUID, slug:Slug, name:Name + Audit |
| SituationCreate | category_id:UUID, slug:Slug, name:Name, description?:Description |
| SituationPatch | name?:Name, description?:Description |
| Situation | id:UUID, project_id:UUID, category_id:UUID, slug:Slug, name:Name, description:Description + Audit |
| StringKeyCreate | string_id:StringId, description?:Description |
| StringKeyPatch | description:Description |
| StringKey | id:UUID, project_id:UUID, string_id:StringId, description:Description + Audit |
| StringEntryCreate | build_id:UUID, locale_id:UUID, string_id:StringId, text:Text |
| StringEntryPatch | text:Text |
| StringEntry | id:UUID, project_id:UUID, build_id:UUID, locale_id:UUID, string_key_id:UUID, string_id:StringId, text:Text + Audit |

StringEntryCreate requires an existing StringKey in the Project. No implicit creation or upsert; repeated translation tuple is 409. StringKeyCreate is the explicit stable identity workflow. Delete translation by entry UUID, delete semantic key by key UUID. Paths do not use translated text.

## Route inventory

P = /api/v1/projects/{project_id}. All brace identifiers are UUIDs. GET collections have limit/offset in addition to listed filters. All item GET/PATCH/DELETE have no query fields. All DELETE operations follow the restrictive policy in domain-model.md.

| Collection path | POST body → 201 | GET → 200 / extra filters | Item path: GET → 200; PATCH body → 200; DELETE → 204 |
| --- | --- | --- | --- |
| /api/v1/projects | ProjectCreate → Project | Page<Project>; no extra filters | /api/v1/projects/{project_id}: Project; ProjectPatch → Project; DELETE |
| P/builds | BuildCreate → Build | Page<Build>; no extra filters | P/builds/{build_id}: Build; BuildPatch → Build; DELETE |
| P/locales | LocaleCreate → Locale | Page<Locale>; no extra filters | P/locales/{locale_id}: Locale; LocalePatch → Locale; DELETE |
| P/categories | CategoryCreate → Category | Page<Category>; no extra filters | P/categories/{category_id}: Category; CategoryPatch → Category; DELETE |
| P/situations | SituationCreate → Situation | Page<Situation>; category_id?:UUID | P/situations/{situation_id}: Situation; SituationPatch → Situation; DELETE |
| P/string-keys | StringKeyCreate → StringKey | Page<StringKey>; string_id?:StringId exact | P/string-keys/{string_key_id}: StringKey; StringKeyPatch → StringKey; DELETE |
| P/strings | StringEntryCreate → StringEntry | Page<StringEntry>; build_id?:UUID, locale_id?:UUID, string_id?:StringId exact | P/strings/{entry_id}: StringEntry; StringEntryPatch → StringEntry; DELETE |
| P/screenshots | Upload multipart → Screenshot | Page<Screenshot>; filters below | P/screenshots/{screenshot_id}: GET → Screenshot only |

An exact string_id filter whose key does not exist is 404; an existing key with no translations is an empty page. Frontend may list StringKeys first to distinguish absent translations. No extra full-text search or batch upload in Phase 1.

### Situation Expected Strings assignment and resolution

- GET P/situations/{situation_id}/expected-string-keys?build_id=UUID → ExpectedMapping.
- PUT P/situations/{situation_id}/expected-string-keys?build_id=UUID with ExpectedMappingReplace → ExpectedMapping. Replaces the entire list in one DB transaction. Empty list clears it. Lock Build row during replacement so concurrent mapping writes serialize; validate Situation and keys in that transaction. Duplicate string_id or >1000 items → 422. Position is derived from list order; no partial update.
- GET P/situations/{situation_id}/expected-strings?build_id=UUID&locale_id=UUID → ExpectedStrings.
- GET P/screenshots/{screenshot_id}/expected-strings → ExpectedStrings, using Screenshot's stored Build/Locale/Situation. No query parameters. Same resolution as Situation endpoint, and current catalog (no upload-time snapshot).

ExpectedMappingReplace={string_ids:StringId[]}.
ExpectedMapping={project_id:UUID,build_id:UUID,situation_id:UUID,items:ExpectedKey[]}.
ExpectedKey={string_key_id:UUID,string_id:StringId,position:integer}.
ExpectedStrings={project_id:UUID,build_id:UUID,locale_id:UUID,situation_id:UUID,catalog_mode:"current",items:ExpectedString[],total:integer,missing_count:integer}.
ExpectedString={string_key_id:UUID,string_id:StringId,position:integer,entry_id:UUID|null,text:Text|null,translation_status:"present"|"missing"}.

These endpoints return the complete capped mapping, without pagination. Sort position ASC. LEFT JOIN mapping → key → entry constrained by both Build and Locale. Missing entry returns null entry_id/text and missing status. Existing text="" returns present. An unconfigured Situation returns items=[],total=0,missing_count=0, not 404. Fetch in a consistent statement/snapshot. All required query parameters must be supplied even for an empty mapping.

```json
{"project_id":"11111111-1111-4111-8111-111111111111","build_id":"22222222-2222-4222-8222-222222222222","locale_id":"33333333-3333-4333-8333-333333333333","situation_id":"55555555-5555-4555-8555-555555555555","catalog_mode":"current","items":[{"string_key_id":"66666666-6666-4666-8666-666666666666","string_id":"tutorial_welcome_001","position":0,"entry_id":"77777777-7777-4777-8777-777777777777","text":"ようこそ","translation_status":"present"},{"string_key_id":"88888888-8888-4888-8888-888888888888","string_id":"tutorial_next_001","position":1,"entry_id":null,"text":null,"translation_status":"missing"}],"total":2,"missing_count":1}
```

## Screenshot upload, list, detail and content

POST P/screenshots has exactly two multipart parts:

1. `file`: one binary PNG or JPEG, Content-Type image/png or image/jpeg; filename provides original_filename.
2. `metadata`: UTF-8 JSON string form field (application/json part type is also accepted), decoded into ScreenshotUpload. This is not a nested set of individual form fields.

ScreenshotUpload={build_id:UUID,locale_id:UUID,category_id:UUID,situation_id:UUID,source:"manual",metadata_version?:1,metadata?:CaptureMetadata}. Defaults: metadata_version=1, metadata={}. Project comes from path. uploaded_at, hash, dimensions, original_filename and storage key are server derived. client_upload_id and Idempotency-Key header are rejected with 422 in Phase 1; neither is silently ignored. Metadata JSON decoding failure is 422.

CaptureMetadata is the bounded open JSON object defined in domain-model.md. Reserved keys run_id/device/resolution/scenario/checkpoint/screen_state use its exact types. Accepted optional context is stored/returned without implying automation functionality.

Limits: original file 1–20,971,520 bytes (20 MiB), complete request <=22,020,096 bytes (21 MiB), metadata form part <=32 KiB. Stream-count the complete request and file independently; do not rely on Content-Length. Exactly one image frame, width/height <=16384, total pixels <=40,000,000. Decode fully with explicit decompression-bomb limits; reject malformed, truncated or animated images. Require MIME and signature to agree. Do not trust extension or re-encode the original. Decoder dependencies/patches are Backend implementation work.

original_filename first passes the shared Unicode check on the full decoded incoming filename (NUL/surrogate is 422 file.filename). Then take the basename after interpreting both / and backslash separators, strip remaining control characters, trim outer whitespace and reject empty or >255 scalar values. Never use it in a storage path or unsanitized header. uploaded_at is server UTC assigned during insert after the file is durable. SHA-256 covers exact original bytes. No deduplication by hash in Phase 1; identical uploads create distinct UUIDs.

Screenshot={id:UUID,project_id:UUID,build_id:UUID,locale_id:UUID,category_id:UUID,situation_id:UUID,source:"manual",original_filename:string,uploaded_at:Timestamp,file_hash:string,media_type:"image/png"|"image/jpeg",size_bytes:integer,width:integer,height:integer,metadata_version:1,metadata:CaptureMetadata,client_upload_id:null,content_url:string}.

content_url is the relative same-API-origin path /api/v1/projects/{project_id}/screenshots/{id}/content. Frontend resolves it against its Backend origin, not its own origin. List and detail return this same model; no unbounded base64 image or expanded Expected Strings in list. No storage_key in response.

GET P/screenshots filters: build_id?, locale_id?, category_id?, situation_id? (UUID), source? (manual), uploaded_from?, uploaded_to? (Timestamp with timezone), plus limit/offset. Time range is half-open [from,to); from >= to is 422. UTC normalization precedes comparison. Project filter is the path, not an additional project_id query. No JSON metadata filter. When both category and situation are provided their relationship must agree.

GET P/screenshots/{screenshot_id}/content → 200 binary image with authoritative Content-Type, Content-Length, X-Content-Type-Options:nosniff, Cache-Control:private,max-age=3600, Content-Disposition:inline using a generated safe UUID filename and validated extension. Phase 1 does not implement Range/conditional GET (full 200 allowed). Scope the DB lookup before storage access. Missing DB row → 404; existing row with missing/unreadable storage → 503 STORAGE_UNAVAILABLE and operational alert, not a phantom 404. No public static storage mount.

Example metadata part:

```json
{"build_id":"22222222-2222-4222-8222-222222222222","locale_id":"33333333-3333-4333-8333-333333333333","category_id":"44444444-4444-4444-8444-444444444444","situation_id":"55555555-5555-4555-8555-555555555555","source":"manual","metadata_version":1,"metadata":{}}
```

Example 201 response (hash is an illustrative shape, not verification evidence):

```json
{"id":"99999999-9999-4999-8999-999999999999","project_id":"11111111-1111-4111-8111-111111111111","build_id":"22222222-2222-4222-8222-222222222222","locale_id":"33333333-3333-4333-8333-333333333333","category_id":"44444444-4444-4444-8444-444444444444","situation_id":"55555555-5555-4555-8555-555555555555","source":"manual","original_filename":"tutorial-ja.png","uploaded_at":"2026-09-05T03:00:00Z","file_hash":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","media_type":"image/png","size_bytes":2048,"width":1280,"height":720,"metadata_version":1,"metadata":{},"client_upload_id":null,"content_url":"/api/v1/projects/11111111-1111-4111-8111-111111111111/screenshots/99999999-9999-4999-8999-999999999999/content"}
```

## Future compatibility, not Phase 1 endpoints

Phase 2 adds optional client_upload_id to upload JSON and agent/automation source values. Agent must supply a stable UUID per queue item. Server computes file_hash; optional client expected hash is validated, never trusted. Persist receipt uniqueness/fingerprint and return original resource on completed replay (200 with Idempotency-Replayed:true); first creation stays 201. Reused ID with changed payload → 409 IDEMPOTENCY_CONFLICT; active lease → 409 UPLOAD_IN_PROGRESS with Retry-After. Manual clients may continue without IDs. These semantics require Phase 2 review and failure tests before activation.

Phase 3 adds separate scoped result resources rather than repurposing StringEntry or embedding changing arrays into Screenshot. Phase 4 reserved metadata works without a large Screenshot migration. Future enum members require Frontend fallback rendering; consumers should ignore new response fields. Breaking identity/semantics changes require a reviewed contract revision/API version.
