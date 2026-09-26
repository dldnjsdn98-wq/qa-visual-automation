import type { CreateVerificationRun, Creates, ErrorDetail, ErrorEnvelope, ExpectedItem, ExpectedMapping, ExpectedStrings, ManualScreenshotUpload, OcrRegion, OcrSummary, Page, PageQuery, Patches, ProfileList, Query, Resource, Resources, Run, RunCreationResult, RunListQuery, RunReadResult, RunSummary, Screenshot, VerificationItem, VerificationSummary } from "./types";

interface RequestOptions { method?: string; body?: unknown; signal?: AbortSignal; expectedStatus?: number | readonly number[]; binary?: boolean }

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details: ErrorDetail[] = [], public requestId: string | null = null, public retryAfter: string | null = null) { super(message); this.name = "ApiError"; }
}
export function validateUnicode(value: unknown, field = "body"): void {
  if (typeof value === "string") {
    for (const scalar of value) {
      const point = scalar.codePointAt(0)!;
      const reason = point === 0 ? "U+0000 is not allowed" : point >= 0xd800 && point <= 0xdfff ? "unpaired Unicode surrogate is not allowed" : null;
      if (reason) throw new ApiError(422, "VALIDATION_ERROR", "입력 문자를 확인해 주세요.", [{ field, reason }]);
    }
  } else if (Array.isArray(value)) value.forEach((item, index) => validateUnicode(item, `${field}[${index}]`));
  else if (value && typeof value === "object") {
    for (const [key, item] of Object.entries(value)) {
      try { validateUnicode(key, field); } catch (error) {
        if (error instanceof ApiError) error.details = error.details.map(detail => ({ field, reason: `object key ${detail.reason}` }));
        throw error;
      }
      validateUnicode(item, `${field}.${key}`);
    }
  }
}
export function scalarLength(value: string): number { validateUnicode(value); return Array.from(value).length; }
export function queryString<T extends object>(query: T = {} as T): string {
  validateUnicode(query, "query");
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => { if (value !== undefined && value !== "") params.set(key, String(value)); });
  return params.size ? `?${params}` : "";
}
export function resourcePath(resource: Resource | "screenshots", project = ""): string {
  if (resource === "projects") return "/api/v1/projects";
  if (!project) throw new Error("Project를 선택해 주세요.");
  return `/api/v1/projects/${encodeURIComponent(project)}/${resource}`;
}
export function changedPatch(original: Record<string, unknown>, values: Record<string, unknown>, mutable: string[]): Record<string, unknown> {
  return Object.fromEntries(mutable.filter(key => values[key] !== undefined && values[key] !== original[key]).map(key => [key, values[key]]));
}
export class ApiClient {
  readonly origin: string;
  constructor(origin = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8001", private fetcher: typeof fetch = (...args) => fetch(...args)) { this.origin = new URL(origin).origin; }
  contentUrl(path: string): string {
    const url = new URL(path, this.origin);
    if (url.origin !== this.origin || !url.pathname.startsWith("/api/v1/projects/")) throw new Error("잘못된 Screenshot content URL입니다.");
    return url.href;
  }
  private async requestResponse<T>(path: string, options: RequestOptions = {}): Promise<{ data: T; response: Response }> {
    const { method = "GET", body, signal, expectedStatus, binary } = options;
    const multipart = body instanceof FormData;
    if (body !== undefined && !multipart) validateUnicode(body);
    let response: Response;
    try {
      response = await this.fetcher(new URL(path, this.origin), {
        method, credentials: "omit", cache: "no-store", signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(60000)]) : AbortSignal.timeout(60000),
        headers: body !== undefined && !multipart ? { "Content-Type": "application/json" } : undefined,
        body: body === undefined ? undefined : multipart ? body : JSON.stringify(body),
      });
    } catch (error) {
      if (signal?.aborted) throw error;
      throw new ApiError(0, "NETWORK_ERROR", "서버 응답을 받지 못했습니다. 연결과 Backend 주소를 확인해 주세요.");
    }
    if (!response.ok) {
      let envelope: ErrorEnvelope | undefined;
      try { envelope = await response.json(); } catch { /* Non-contract proxy errors still have an explicit state. */ }
      const error = envelope?.error;
      throw new ApiError(response.status, error?.code || "CONTRACT_ERROR", error?.message || `HTTP ${response.status}: API 오류 형식이 계약과 다릅니다.`, Array.isArray(error?.details) ? error.details : [], error?.request_id || response.headers.get("X-Request-ID"), response.headers.get("Retry-After"));
    }
    const expectedStatuses = typeof expectedStatus === "number" ? [expectedStatus] : expectedStatus;
    if (expectedStatuses && !expectedStatuses.includes(response.status)) throw new ApiError(response.status, "CONTRACT_ERROR", `예상 HTTP ${expectedStatuses.join(" 또는 ")}, 실제 ${response.status}. 저장 여부를 확인해 주세요.`);
    if (response.status === 204) return { data: undefined as T, response };
    try { return { data: (binary ? await response.blob() : await response.json()) as T, response }; }
    catch { throw new ApiError(response.status, "CONTRACT_ERROR", "응답을 읽을 수 없습니다. 저장 여부를 확인해 주세요."); }
  }
  async request<T>(path: string, options: RequestOptions = {}): Promise<T> { return (await this.requestResponse<T>(path, options)).data; }
  list<K extends Resource>(kind: K, project: string, query: Query = {}, signal?: AbortSignal) { return this.request<Page<Resources[K]>>(resourcePath(kind, project) + queryString(query), { signal }); }
  create<K extends Resource>(kind: K, project: string, body: Creates[K]) { return this.request<Resources[K]>(resourcePath(kind, project), { method: "POST", body, expectedStatus: 201 }); }
  patch<K extends Resource>(kind: K, project: string, id: string, body: Patches[K]) { return this.request<Resources[K]>(`${resourcePath(kind, project)}/${encodeURIComponent(id)}`, { method: "PATCH", body, expectedStatus: 200 }); }
  remove(kind: Resource, project: string, id: string) { return this.request<void>(`${resourcePath(kind, project)}/${encodeURIComponent(id)}`, { method: "DELETE", expectedStatus: 204 }); }
  mapping(project: string, situation: string, build: string, signal?: AbortSignal) { return this.request<ExpectedMapping>(`${resourcePath("situations", project)}/${encodeURIComponent(situation)}/expected-string-keys${queryString({ build_id: build })}`, { signal }); }
  setMapping(project: string, situation: string, build: string, stringIds: string[]) { return this.request<ExpectedMapping>(`${resourcePath("situations", project)}/${encodeURIComponent(situation)}/expected-string-keys${queryString({ build_id: build })}`, { method: "PUT", body: { string_ids: stringIds }, expectedStatus: 200 }); }
  expected(project: string, situation: string, build: string, locale: string, signal?: AbortSignal) { return this.request<ExpectedStrings>(`${resourcePath("situations", project)}/${encodeURIComponent(situation)}/expected-strings${queryString({ build_id: build, locale_id: locale })}`, { signal }); }
  screenshots(project: string, query: Query, signal?: AbortSignal) { return this.request<Page<Screenshot>>(resourcePath("screenshots", project) + queryString(query), { signal }); }
  screenshot(project: string, id: string, signal?: AbortSignal) { return this.request<Screenshot>(`${resourcePath("screenshots", project)}/${encodeURIComponent(id)}`, { signal }); }
  screenshotExpected(project: string, id: string, signal?: AbortSignal) { return this.request<ExpectedStrings>(`${resourcePath("screenshots", project)}/${encodeURIComponent(id)}/expected-strings`, { signal }); }
  ocrProfiles(project: string, signal?: AbortSignal) { return this.request<ProfileList>(`${resourcePath("projects")}/${encodeURIComponent(project)}/ocr-profiles`, { signal }); }
  verificationRuns(project: string, screenshot: string, query: RunListQuery = {}, signal?: AbortSignal) { return this.request<Page<RunSummary>>(`${this.verificationRunsPath(project, screenshot)}${queryString(query)}`, { signal }); }
  async verificationRun(project: string, screenshot: string, run: string, signal?: AbortSignal) { return (await this.verificationRunResult(project, screenshot, run, signal)).run; }
  async verificationRunResult(project: string, screenshot: string, run: string, signal?: AbortSignal): Promise<RunReadResult> {
    const { data, response } = await this.requestResponse<Run>(this.verificationRunPath(project, screenshot, run), { signal });
    return { run: data, retryAfter: response.headers.get("Retry-After") };
  }
  async createVerificationRun(project: string, screenshot: string, body: CreateVerificationRun): Promise<RunCreationResult> {
    const { data: run, response } = await this.requestResponse<Run>(this.verificationRunsPath(project, screenshot), { method: "POST", body, expectedStatus: [200, 202] });
    const replayed = response.headers.get("Idempotency-Replayed");
    const replayedValue = replayed?.toLowerCase();
    return { run, status: response.status as 200 | 202, location: response.headers.get("Location"), retryAfter: response.headers.get("Retry-After"), idempotencyReplayed: replayedValue === "true" ? true : replayedValue === "false" ? false : null };
  }
  verificationExpected(project: string, screenshot: string, run: string, query: PageQuery = {}, signal?: AbortSignal) { return this.request<Page<ExpectedItem>>(`${this.verificationRunPath(project, screenshot, run)}/expected${queryString(query)}`, { signal }); }
  ocrSummary(project: string, screenshot: string, run: string, signal?: AbortSignal) { return this.request<OcrSummary>(`${this.verificationRunPath(project, screenshot, run)}/ocr`, { signal }); }
  ocrRegions(project: string, screenshot: string, run: string, query: PageQuery = {}, signal?: AbortSignal) { return this.request<Page<OcrRegion>>(`${this.verificationRunPath(project, screenshot, run)}/ocr/regions${queryString(query)}`, { signal }); }
  verificationSummary(project: string, screenshot: string, run: string, signal?: AbortSignal) { return this.request<VerificationSummary>(`${this.verificationRunPath(project, screenshot, run)}/verification`, { signal }); }
  verificationItems(project: string, screenshot: string, run: string, query: PageQuery = {}, signal?: AbortSignal) { return this.request<Page<VerificationItem>>(`${this.verificationRunPath(project, screenshot, run)}/verification/items${queryString(query)}`, { signal }); }
  upload(project: string, file: File, metadata: ManualScreenshotUpload) {
    validateUnicode(file.name, "file.filename"); validateUnicode(metadata, "metadata");
    if (!file.size || file.size > 20971520) throw new ApiError(422, "VALIDATION_ERROR", "파일 크기를 확인해 주세요.", [{ field: "file", reason: "1 byte–20 MiB 파일이 필요합니다." }]);
    if (!["image/png", "image/jpeg"].includes(file.type)) throw new ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "PNG 또는 JPEG 파일이 필요합니다.");
    const body = new FormData(); body.append("file", file); body.append("metadata", JSON.stringify(metadata));
    return this.request<Screenshot>(resourcePath("screenshots", project), { method: "POST", body, expectedStatus: 201 });
  }
  private verificationRunsPath(project: string, screenshot: string) { return `${resourcePath("screenshots", project)}/${encodeURIComponent(screenshot)}/verification-runs`; }
  private verificationRunPath(project: string, screenshot: string, run: string) { return `${this.verificationRunsPath(project, screenshot)}/${encodeURIComponent(run)}`; }
}
export const api = new ApiClient();
