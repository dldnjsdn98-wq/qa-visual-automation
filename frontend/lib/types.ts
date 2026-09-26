/** ARCH-001 revision 2. Reconcile with Backend OpenAPI before integration acceptance. */
export type UUID = string;
export type ExtensibleString<Known extends string> = Known | (string & {});
export interface Audit { created_at: string; updated_at: string }
export interface Project extends Audit { id: UUID; slug: string; name: string; description: string | null }
export interface Build extends Audit { id: UUID; project_id: UUID; label: string; description: string | null }
export interface Locale extends Audit { id: UUID; project_id: UUID; code: string; name: string }
export interface Category extends Audit { id: UUID; project_id: UUID; slug: string; name: string }
export interface Situation extends Category { category_id: UUID; description: string | null }
export interface StringKey extends Audit { id: UUID; project_id: UUID; string_id: string; description: string | null }
export interface StringEntry extends Audit { id: UUID; project_id: UUID; build_id: UUID; locale_id: UUID; string_key_id: UUID; string_id: string; text: string }
export interface Page<T> { items: T[]; total: number; limit: number; offset: number }
export interface ErrorDetail { field: string | null; reason: string }
export interface ErrorEnvelope { error: { code: string; message: string; details: ErrorDetail[]; request_id: UUID } }
export type Json = string | number | boolean | null | Json[] | { [key: string]: Json };
export interface CaptureMetadata { [key: string]: Json | undefined; run_id?: string; device?: string; resolution?: { width: number; height: number }; scenario?: string; checkpoint?: string; screen_state?: string }
export interface ManualScreenshotUpload { build_id: UUID; locale_id: UUID; category_id: UUID; situation_id: UUID; source: "manual"; metadata_version?: 1; metadata?: CaptureMetadata }
export type ScreenshotSource = "manual" | "agent" | "automation";
export interface Screenshot { id: UUID; project_id: UUID; build_id: UUID; locale_id: UUID; category_id: UUID; situation_id: UUID; source: ScreenshotSource; metadata_version: 1; metadata: CaptureMetadata; original_filename: string; uploaded_at: string; file_hash: string; media_type: "image/png" | "image/jpeg"; size_bytes: number; width: number; height: number; client_upload_id: UUID | null; content_url: string }
export interface ExpectedKey { string_key_id: UUID; string_id: string; position: number }
export interface ExpectedMapping { project_id: UUID; build_id: UUID; situation_id: UUID; items: ExpectedKey[] }
export interface ExpectedString extends ExpectedKey { entry_id: UUID | null; text: string | null; translation_status: "present" | "missing" }
export interface ExpectedStrings { project_id: UUID; build_id: UUID; locale_id: UUID; situation_id: UUID; catalog_mode: "current"; items: ExpectedString[]; total: number; missing_count: number }
export type CoordinateSpace = ExtensibleString<"original-raster-v1">;
export type ProfileAvailability = ExtensibleString<"AVAILABLE" | "UNAVAILABLE">;
export type RunStatus = ExtensibleString<"PENDING" | "RUNNING" | "RETRY_WAIT" | "SUCCEEDED" | "FAILED">;
export type RunStage = ExtensibleString<"QUEUED" | "OCR" | "VERIFY" | "COMPLETE">;
export type VerificationStatus = ExtensibleString<"PASS" | "REVIEW" | "FAIL" | "UNVERIFIED">;
export interface ProfileSummary {
  profile_id: string;
  profile_digest: string;
  engine_name: string;
  engine_version: string;
  model_ids: string[];
  language_tags: string[];
  coordinate_space: CoordinateSpace;
  normalization_version: string;
  matching_version: string;
  availability: ProfileAvailability;
  unavailable_code: string | null;
}
export interface ProfileList { items: ProfileSummary[] }
export type ProfilePage = ProfileList;
export interface RunError {
  code: string;
  correlation_id: UUID;
  cause_code: string | null;
  stage: ExtensibleString<"QUEUED" | "OCR" | "VERIFY">;
  retryable: boolean;
  message: string;
  attempt: number;
}
export interface RunSummary extends Audit {
  id: UUID;
  project_id: UUID;
  screenshot_id: UUID;
  client_run_id: UUID;
  protocol_version: 1;
  profile_id: string;
  profile_digest: string;
  status: RunStatus;
  stage: RunStage;
  started_at: string | null;
  completed_at: string | null;
  attempt_count: number;
  next_attempt_at: string | null;
  verification_status: VerificationStatus | null;
  error: RunError | null;
}
export interface RunSnapshot {
  version: 1;
  sha256: string;
  captured_at: string;
  item_count: number;
  missing_count: number;
  locale_code: string;
  ocr_language: string;
  screenshot_file_hash: string;
  width: number;
  height: number;
}
export interface RunConfiguration {
  profile_id: string;
  profile_digest: string;
  normalization_version: string;
  matching_version: string;
  pass_threshold: number;
  review_threshold: number;
}
export interface RunLinks { self: string; expected: string; ocr: string; regions: string; verification: string; items: string }
export interface Run extends RunSummary {
  snapshot: RunSnapshot;
  configuration: RunConfiguration;
  ocr_result_id: UUID | null;
  verification_result_id: UUID | null;
  links: RunLinks;
}
export interface CreateVerificationRun {
  protocol_version: 1;
  client_run_id: UUID;
  profile_id: string;
  verification?: { pass_threshold?: number; review_threshold?: number };
}
export interface RunCreationResult {
  run: Run;
  status: 200 | 202;
  location: string | null;
  retryAfter: string | null;
  idempotencyReplayed: boolean | null;
}
export interface RunReadResult { run: Run; retryAfter: string | null }
export interface ExpectedItem {
  position: number;
  string_key_id: UUID;
  string_id: string;
  entry_id: UUID | null;
  expected_text: string | null;
  translation_status: ExtensibleString<"present" | "missing">;
}
export type Matrix3x3 = [[number, number, number], [number, number, number], [number, number, number]];
export interface OcrPreprocessingStep { kind: string; input_width: number; input_height: number; output_width: number; output_height: number; matrix3x3: Matrix3x3 }
export interface OcrSummary {
  id: UUID;
  run_id: UUID;
  project_id: UUID;
  screenshot_id: UUID;
  coordinate_space: CoordinateSpace;
  width: number;
  height: number;
  region_count: number;
  no_text: boolean;
  profile_id: string;
  profile_digest: string;
  engine_name: string;
  engine_version: string;
  ocr_language: string;
  runtime_manifest: { [key: string]: Json };
  preprocessing: { exif_policy: ExtensibleString<"ignored-v1">; exif_orientation: number | null; pixel_sha256: string; steps: OcrPreprocessingStep[]; original_to_inference_matrix3x3: Matrix3x3 };
  output_sha256: string;
  created_at: string;
}
export interface Region {
  region_index: number;
  text: string;
  confidence: number;
  confidence_semantics: ExtensibleString<"recognition">;
  detection_confidence: number | null;
  detection_confidence_unavailable_reason: ExtensibleString<"NOT_EXPOSED_BY_PROFILE"> | null;
  polygon: [number, number][];
  bbox: { x: number; y: number; width: number; height: number };
  clipped: boolean;
  engine_region_index: number;
}
export type OcrRegion = Region;
export type EvaluationReason = ExtensibleString<"EVALUATED" | "PARTIAL_UNVERIFIED" | "NO_EVALUABLE_EXPECTATIONS" | "NO_EXPECTATIONS">;
export interface VerificationSummary {
  id: UUID;
  run_id: UUID;
  project_id: UUID;
  screenshot_id: UUID;
  ocr_result_id: UUID;
  snapshot_sha256: string;
  configuration_sha256: string;
  matching_version: string;
  normalization_version: string;
  verification_status: VerificationStatus;
  evaluation_reason: EvaluationReason;
  incomplete: boolean;
  total_count: number;
  evaluated_count: number;
  unverified_count: number;
  pass_count: number;
  review_count: number;
  fail_count: number;
  unmatched_region_count: number;
  pass_threshold: number;
  review_threshold: number;
  created_at: string;
}
export interface VerificationItem {
  expected_position: number;
  string_key_id: UUID;
  string_id: string;
  entry_id: UUID | null;
  expected_text: string | null;
  normalized_expected: string | null;
  translation_status: ExtensibleString<"present" | "missing">;
  region_index: number | null;
  observed_text: string | null;
  normalized_observed: string | null;
  match_method: ExtensibleString<"EXACT" | "NORMALIZED" | "FUZZY" | "NONE"> | null;
  match_score: number | null;
  score_numerator: number | null;
  score_denominator: number | null;
  verification_status: VerificationStatus;
  reason: ExtensibleString<"MATCHED" | "NO_MATCH" | "MISSING_TRANSLATION" | "EMPTY_EXPECTED" | "NORMALIZED_EMPTY_EXPECTED">;
}
export interface RunListQuery { selection?: "all" | "succeeded"; limit?: number; offset?: number }
export interface PageQuery { limit?: number; offset?: number }
export interface Resources { projects: Project; builds: Build; locales: Locale; categories: Category; situations: Situation; "string-keys": StringKey; strings: StringEntry }
export interface Creates {
  projects: { slug: string; name: string; description?: string | null };
  builds: { label: string; description?: string | null };
  locales: { code: string; name: string };
  categories: { slug: string; name: string };
  situations: { category_id: UUID; slug: string; name: string; description?: string | null };
  "string-keys": { string_id: string; description?: string | null };
  strings: { build_id: UUID; locale_id: UUID; string_id: string; text: string };
}
export interface Patches {
  projects: { name?: string; description?: string | null };
  builds: { description: string | null };
  locales: { name: string };
  categories: { name: string };
  situations: { name?: string; description?: string | null };
  "string-keys": { description: string | null };
  strings: { text: string };
}
export type Resource = keyof Resources;
export type Query = Record<string, string | number | undefined>;
