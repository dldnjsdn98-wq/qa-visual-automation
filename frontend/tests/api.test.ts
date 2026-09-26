// @vitest-environment node
import { describe, expect, it, vi } from "vitest";
import { ApiClient, ApiError, changedPatch, queryString, scalarLength, validateUnicode } from "../lib/api";
import { changeSelection, initialNavigation, navigationUrl, parseNavigation } from "../lib/navigation";
import type { ManualScreenshotUpload, Region, Screenshot, VerificationItem } from "../lib/types";
describe("approved contract client", () => {
  it("preserves multilingual scalars, combining marks and exact whitespace", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(Response.json({}, { status: 201 }));
    const text = "ようこそ 한글 😀 e\u0301\r\n\t  ";
    await new ApiClient("http://127.0.0.1:8001", fetcher).create("strings", "p", { build_id: "b", locale_id: "l", string_id: "welcome", text });
    expect(JSON.parse(fetcher.mock.calls[0][1]!.body as string).text).toBe(text);
    expect(scalarLength("😀")).toBe(1); expect(scalarLength("e\u0301")).toBe(2);
  });
  it.each(["a\0b", "\ud800", "\udfff", "\ude00\ud83d"])("rejects forbidden Unicode before fetching: %j", async text => {
    const fetcher = vi.fn<typeof fetch>();
    await expect(new ApiClient("http://localhost:8001", fetcher).patch("strings", "p", "e", { text })).rejects.toMatchObject({ code: "VALIDATION_ERROR", details: [{ field: "body.text", reason: expect.any(String) }] });
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("rejects nested metadata keys using safe containing paths", () => {
    try { validateUnicode({ steps: [{ ["bad\0key"]: "ok" }] }, "metadata.metadata"); throw new Error("should reject"); }
    catch (error) { expect(error).toBeInstanceOf(ApiError); expect((error as ApiError).details).toEqual([{ field: "metadata.metadata.steps[0]", reason: "object key U+0000 is not allowed" }]); }
  });
  it("distinguishes omission, empty string and null PATCH; accepts 204", async () => {
    expect(changedPatch({ name: "A", description: "B" }, { name: "A", description: null }, ["name", "description"])).toEqual({ description: null });
    expect(changedPatch({ name: "A", description: null }, { name: "B", description: undefined }, ["name", "description"])).toEqual({ name: "B" });
    expect(changedPatch({ text: "A" }, { text: "" }, ["text"])).toEqual({ text: "" });
    await expect(new ApiClient("http://localhost:8001", vi.fn<typeof fetch>().mockResolvedValue(new Response(null, { status: 204 }))).remove("builds", "p", "b")).resolves.toBeUndefined();
  });
  it("sends exactly file + metadata multipart parts, without a manual boundary", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(Response.json({ id: "s" }, { status: 201 }));
    const file = new File([new Uint8Array([1, 2, 3])], "한글.png", { type: "image/png" });
    const metadata = { build_id: "b", locale_id: "l", category_id: "c", situation_id: "s", source: "manual" as const };
    await new ApiClient("http://localhost:8001", fetcher).upload("p", file, metadata);
    const options = fetcher.mock.calls[0][1]!; const body = options.body as FormData;
    expect([...body.keys()]).toEqual(["file", "metadata"]); expect(body.get("file")).toBe(file);
    const sent = JSON.parse(body.get("metadata") as string);
    expect(sent).toEqual(metadata); expect(sent).not.toHaveProperty("client_upload_id"); expect(sent).not.toHaveProperty("upload_protocol_version"); expect(sent).not.toHaveProperty("expected_file_hash"); expect(options.headers).toBeUndefined();
  });
  it("keeps manual upload on 201 while expanded screenshot responses remain read-only", async () => {
    const file = new File([new Uint8Array([1])], "qa.png", { type: "image/png" });
    const metadata: ManualScreenshotUpload = { build_id: "b", locale_id: "l", category_id: "c", situation_id: "s", source: "manual" };
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(Response.json({}, { status: 200 }));
    await expect(new ApiClient("http://localhost:8001", fetcher).upload("p", file, metadata)).rejects.toMatchObject({ code: "CONTRACT_ERROR" });
    const response = {
      id: "shot", project_id: "p", build_id: "b", locale_id: "l", category_id: "c", situation_id: "s", source: "agent", metadata_version: 1,
      metadata: { note: "한글 😀 e\u0301", nested: { empty: "", missing: null } }, original_filename: "qa.png", uploaded_at: "2026-09-25T00:00:00Z",
      file_hash: "a".repeat(64), media_type: "image/png", size_bytes: 1, width: 1, height: 1, client_upload_id: "11111111-1111-4111-8111-111111111111",
      content_url: "/api/v1/projects/p/screenshots/shot/content",
    } satisfies Screenshot;
    expect(response.source).toBe("agent"); expect(response.client_upload_id).not.toBeNull();
    const invalidSource: ManualScreenshotUpload = { build_id: "b", locale_id: "l", category_id: "c", situation_id: "s",
      // @ts-expect-error Browser uploads cannot claim an agent source.
      source: "agent" };
    const invalidIdentity: ManualScreenshotUpload = { build_id: "b", locale_id: "l", category_id: "c", situation_id: "s", source: "manual",
      // @ts-expect-error Browser uploads cannot send a Phase 2 client identity.
      client_upload_id: "11111111-1111-4111-8111-111111111111" };
    expect(invalidSource.source).toBe("agent"); expect(invalidIdentity).toHaveProperty("client_upload_id");
  });
  it("preserves structured field errors and request IDs", async () => {
    const error = { code: "VALIDATION_ERROR", message: "bad field", details: [{ field: "body.text", reason: "invalid" }], request_id: "request-1" };
    const client = new ApiClient("http://localhost:8001", vi.fn<typeof fetch>().mockResolvedValue(Response.json({ error }, { status: 422 })));
    await expect(client.patch("strings", "p", "e", { text: "valid" })).rejects.toMatchObject({ code: error.code, details: error.details, requestId: "request-1" });
  });
  it("uses project path, AND filters and Backend-origin content URLs", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(Response.json({ items: [], total: 0, limit: 50, offset: 0 }));
    const client = new ApiClient("http://localhost:8001", fetcher);
    await client.screenshots("p", { build_id: "b", locale_id: "l", situation_id: "s", category_id: "", offset: 0 });
    expect(String(fetcher.mock.calls[0][0])).toBe("http://localhost:8001/api/v1/projects/p/screenshots?build_id=b&locale_id=l&situation_id=s&offset=0");
    expect(client.contentUrl("/api/v1/projects/p/screenshots/s/content")).toBe("http://localhost:8001/api/v1/projects/p/screenshots/s/content");
    expect(() => client.contentUrl("https://foreign.example/image")).toThrow();
  });
  it("does not retry ambiguous writes or accept a wrong success status", async () => {
    const fetcher = vi.fn<typeof fetch>().mockRejectedValue(new TypeError("offline")); const client = new ApiClient("http://localhost:8001", fetcher);
    await expect(client.request("/api/v1/projects", { method: "POST", body: {} })).rejects.toMatchObject({ code: "NETWORK_ERROR" }); expect(fetcher).toHaveBeenCalledTimes(1);
    fetcher.mockResolvedValue(Response.json({}, { status: 200 }));
    await expect(client.create("projects", "", { slug: "qa", name: "QA" })).rejects.toMatchObject({ code: "CONTRACT_ERROR" });
  });
  it("uses screenshot-scoped OCR profile, run and result routes with selection and paging", async () => {
    const fetcher = vi.fn<typeof fetch>().mockImplementation(async () => Response.json({ items: [], total: 0, limit: 2, offset: 0 }));
    const client = new ApiClient("http://localhost:8001", fetcher);
    await client.ocrProfiles("project /한글");
    await client.verificationRuns("p", "shot /1", { selection: "succeeded", limit: 2, offset: 0 });
    await client.verificationRun("p", "shot", "run /1");
    await client.verificationExpected("p", "shot", "run", { limit: 1, offset: 2 });
    await client.ocrSummary("p", "shot", "run");
    await client.ocrRegions("p", "shot", "run", { limit: 3, offset: 0 });
    await client.verificationSummary("p", "shot", "run");
    await client.verificationItems("p", "shot", "run", { limit: 4, offset: 5 });
    expect(fetcher.mock.calls.map(call => String(call[0]))).toEqual([
      "http://localhost:8001/api/v1/projects/project%20%2F%ED%95%9C%EA%B8%80/ocr-profiles",
      "http://localhost:8001/api/v1/projects/p/screenshots/shot%20%2F1/verification-runs?selection=succeeded&limit=2&offset=0",
      "http://localhost:8001/api/v1/projects/p/screenshots/shot/verification-runs/run%20%2F1",
      "http://localhost:8001/api/v1/projects/p/screenshots/shot/verification-runs/run/expected?limit=1&offset=2",
      "http://localhost:8001/api/v1/projects/p/screenshots/shot/verification-runs/run/ocr",
      "http://localhost:8001/api/v1/projects/p/screenshots/shot/verification-runs/run/ocr/regions?limit=3&offset=0",
      "http://localhost:8001/api/v1/projects/p/screenshots/shot/verification-runs/run/verification",
      "http://localhost:8001/api/v1/projects/p/screenshots/shot/verification-runs/run/verification/items?limit=4&offset=5",
    ]);
  });
  it("accepts new 202 and same-client-id replay 200 while exposing creation headers", async () => {
    const run = { id: "run-1", status: "PENDING" };
    const location = "/api/v1/projects/p/screenshots/s/verification-runs/run-1";
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(Response.json(run, { status: 202, headers: { Location: location, "Retry-After": "2", "Idempotency-Replayed": "false" } }))
      .mockResolvedValueOnce(Response.json(run, { status: 200, headers: { Location: location, "Retry-After": "2", "Idempotency-Replayed": "true" } }));
    const client = new ApiClient("http://localhost:8001", fetcher);
    const request = { protocol_version: 1 as const, client_run_id: "11111111-1111-4111-8111-111111111111", profile_id: "profile-v1", verification: { pass_threshold: 95, review_threshold: 85 } };
    await expect(client.createVerificationRun("p", "s", request)).resolves.toMatchObject({ run, status: 202, location, retryAfter: "2", idempotencyReplayed: false });
    await expect(client.createVerificationRun("p", "s", request)).resolves.toMatchObject({ run, status: 200, location, retryAfter: "2", idempotencyReplayed: true });
    expect(fetcher.mock.calls.map(call => JSON.parse(call[1]!.body as string))).toEqual([request, request]);
  });
  it("exposes Retry-After from selected-run reads for polling", async () => {
    const run = { id: "run-1", status: "RUNNING", attempt_count: 1 };
    const fetcher = vi.fn<typeof fetch>().mockImplementation(async () => Response.json(run, { headers: { "Retry-After": "2" } }));
    const client = new ApiClient("http://localhost:8001", fetcher);
    await expect(client.verificationRunResult("p", "s", "run-1")).resolves.toEqual({ run, retryAfter: "2" });
    await expect(client.verificationRun("p", "s", "run-1")).resolves.toEqual(run);
  });
  it("preserves Retry-After on polling errors", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(Response.json({ error: { code: "DATABASE_UNAVAILABLE", message: "retry", details: [], request_id: "req" } }, { status: 503, headers: { "Retry-After": "5" } }));
    const client = new ApiClient("http://localhost:8001", fetcher);
    await expect(client.verificationRunResult("p", "s", "run-1")).rejects.toMatchObject({ status: 503, retryAfter: "5" });
  });
  it("preserves contract-significant null, zero, empty and unknown response values", async () => {
    const region = {
      region_index: 0, text: "", confidence: 0, confidence_semantics: "future-confidence", detection_confidence: null,
      detection_confidence_unavailable_reason: null, polygon: [[0, 0], [1, 0], [1, 1]], bbox: { x: 0, y: 0, width: 1, height: 1 },
      clipped: false, engine_region_index: 0,
    } satisfies Region;
    const item = {
      expected_position: 0, string_key_id: "key", string_id: "", entry_id: null, expected_text: null, translation_status: "future-translation",
      normalized_expected: null, region_index: null, observed_text: null, normalized_observed: null, match_method: "future-match",
      match_score: 0, score_numerator: 0, score_denominator: 1, verification_status: "future-quality", reason: "future-reason",
    } satisfies VerificationItem;
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(Response.json({ items: [region], total: 1, limit: 50, offset: 0 }))
      .mockResolvedValueOnce(Response.json({ items: [item], total: 1, limit: 50, offset: 0 }));
    const client = new ApiClient("http://localhost:8001", fetcher);
    expect((await client.ocrRegions("p", "s", "r")).items[0]).toEqual(region);
    expect((await client.verificationItems("p", "s", "r")).items[0]).toEqual(item);
  });
  it("resets scoped selection and retains deep links", () => {
    const state = { ...initialNavigation, view: "screenshots" as const, project: "p", build: "b", locale: "l", category: "c", situation: "s" };
    expect(changeSelection(state, "project", "p2")).toEqual({ ...initialNavigation, view: "screenshots", project: "p2" });
    expect(changeSelection(state, "category", "c2").situation).toBe(""); expect(parseNavigation(navigationUrl(state))).toEqual(state);
  });
  it("rejects invalid query Unicode without silently replacing it", () => {
    expect(() => queryString({ string_id: "bad\ud800" })).toThrow(ApiError);
  });
});
