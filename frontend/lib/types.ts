/** ARCH-001 revision 2. Reconcile with Backend OpenAPI before integration acceptance. */
export type UUID = string;
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
export interface ScreenshotUpload { build_id: UUID; locale_id: UUID; category_id: UUID; situation_id: UUID; source: "manual"; metadata_version?: 1; metadata?: CaptureMetadata }
export interface Screenshot extends Required<ScreenshotUpload> { id: UUID; project_id: UUID; original_filename: string; uploaded_at: string; file_hash: string; media_type: "image/png" | "image/jpeg"; size_bytes: number; width: number; height: number; client_upload_id: null; content_url: string }
export interface ExpectedKey { string_key_id: UUID; string_id: string; position: number }
export interface ExpectedMapping { project_id: UUID; build_id: UUID; situation_id: UUID; items: ExpectedKey[] }
export interface ExpectedString extends ExpectedKey { entry_id: UUID | null; text: string | null; translation_status: "present" | "missing" }
export interface ExpectedStrings { project_id: UUID; build_id: UUID; locale_id: UUID; situation_id: UUID; catalog_mode: "current"; items: ExpectedString[]; total: number; missing_count: number }
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
