// @vitest-environment node
import { describe, expect, it, vi } from "vitest";
import { ApiClient, ApiError, changedPatch, scalarLength, validateUnicode } from "../lib/api";
import { changeSelection, initialNavigation, navigationUrl, parseNavigation } from "../lib/navigation";
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
    expect(JSON.parse(body.get("metadata") as string)).toEqual(metadata); expect(options.headers).toBeUndefined();
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
  it("resets scoped selection and retains deep links", () => {
    const state = { ...initialNavigation, view: "screenshots" as const, project: "p", build: "b", locale: "l", category: "c", situation: "s" };
    expect(changeSelection(state, "project", "p2")).toEqual({ ...initialNavigation, view: "screenshots", project: "p2" });
    expect(changeSelection(state, "category", "c2").situation).toBe(""); expect(parseNavigation(navigationUrl(state))).toEqual(state);
  });
});
