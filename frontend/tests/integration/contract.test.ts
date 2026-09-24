// @vitest-environment node
import { expect, it } from "vitest";
import { ApiClient, resourcePath } from "../../lib/api";
import type { Resource } from "../../lib/types";

const origin = process.env.QA_API_BASE_URL;
if (!origin) throw new Error("Use tests/frontend/run_integration.py to allocate an isolated test database.");
const client = new ApiClient(origin);
it("matches generated OpenAPI routes, response fields, PATCH nullability and multipart contract", async () => {
  const spec = await client.request<any>("/openapi.json");
  for (const [kind, model, identity] of [["projects", "Project", "project_id"], ["builds", "Build", "build_id"], ["locales", "Locale", "locale_id"], ["categories", "Category", "category_id"], ["situations", "Situation", "situation_id"], ["string-keys", "StringKey", "string_key_id"], ["strings", "StringEntry", "entry_id"]]) {
    const path = kind === "projects" ? "/api/v1/projects" : `/api/v1/projects/{project_id}/${kind}`;
    expect(spec.paths[path].post.responses[201].content["application/json"].schema.$ref).toBe(`#/components/schemas/${model}`);
    const itemPath = `${path}/{${identity}}`;
    expect(spec.paths[itemPath]).toHaveProperty("get"); expect(spec.paths[itemPath]).toHaveProperty("patch"); expect(spec.paths[itemPath].delete.responses).toHaveProperty("204");
    expect(spec.components.schemas[model].required).toContain("id");
  }
  const schemas = spec.components.schemas;
  const fields: Record<string, string[]> = {
    Project: ["id", "slug", "name", "description", "created_at", "updated_at"],
    StringEntry: ["id", "project_id", "build_id", "locale_id", "string_key_id", "string_id", "text", "created_at", "updated_at"],
    Screenshot: ["id", "project_id", "build_id", "locale_id", "category_id", "situation_id", "source", "original_filename", "uploaded_at", "file_hash", "media_type", "size_bytes", "width", "height", "metadata_version", "metadata", "client_upload_id", "content_url"],
    ExpectedStrings: ["project_id", "build_id", "locale_id", "situation_id", "catalog_mode", "items", "total", "missing_count"],
  };
  for (const [model, keys] of Object.entries(fields)) expect(Object.keys(schemas[model].properties).sort()).toEqual(keys.sort());
  expect(schemas.ProjectPatch.required || []).not.toContain("name"); expect(schemas.ProjectPatch.properties.description.anyOf).toContainEqual({ type: "null" });
  const upload = spec.paths["/api/v1/projects/{project_id}/screenshots"].post.requestBody.content["multipart/form-data"].schema;
  expect(upload.required.sort()).toEqual(["file", "metadata"]); expect(upload.properties.metadata.type).toBe("string");
});

it("runs real catalog → translations → expectations → FormData upload → filters/detail/content flow", async () => {
  const project = await client.create("projects", "", { slug: `frontend-${Date.now()}`, name: "한글 😀 QA", description: "original" });
  const p = project.id;
  const patched = await client.patch("projects", "", p, { name: "日本語 QA" }); expect(patched.description).toBe("original");
  expect((await client.patch("projects", "", p, { description: null })).description).toBeNull();
  const build = await client.create("builds", p, { label: "1.0" });
  const locale = await client.create("locales", p, { code: "JA-jp", name: "日本語" }); expect(locale.code).toBe("ja-JP");
  const category = await client.create("categories", p, { slug: "tutorial", name: "Tutorial" });
  const situation = await client.create("situations", p, { category_id: category.id, slug: "welcome", name: "Welcome" });
  for (const string_id of ["welcome", "empty", "missing"]) await client.create("string-keys", p, { string_id });
  const text = "ようこそ 한글 😀 e\u0301\r\n\t  ";
  const entry = await client.create("strings", p, { build_id: build.id, locale_id: locale.id, string_id: "welcome", text }); expect(entry.text).toBe(text);
  await client.create("strings", p, { build_id: build.id, locale_id: locale.id, string_id: "empty", text: "" });
  await client.setMapping(p, situation.id, build.id, ["missing", "welcome", "empty"]);
  const resolved = await client.expected(p, situation.id, build.id, locale.id); expect(resolved.items.map(item => [item.string_id, item.text, item.translation_status])).toEqual([["missing", null, "missing"], ["welcome", text, "present"], ["empty", "", "present"]]);
  expect((await client.list("strings", p, { build_id: build.id, locale_id: locale.id, string_id: "welcome" })).items[0].text).toBe(text);
  // Synthetic 1x1 PNG; no actual game/QA data is used or committed.
  const bytes = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=", "base64");
  const shot = await client.upload(p, new File([bytes], "테스트.png", { type: "image/png" }), { build_id: build.id, locale_id: locale.id, category_id: category.id, situation_id: situation.id, source: "manual" });
  expect(shot.original_filename).toBe("테스트.png"); expect(shot.client_upload_id).toBeNull();
  expect((await client.screenshots(p, { build_id: build.id, locale_id: locale.id, situation_id: situation.id })).items[0].id).toBe(shot.id);
  expect((await client.screenshot(p, shot.id)).content_url).toBe(shot.content_url); expect((await client.screenshotExpected(p, shot.id)).items).toEqual(resolved.items);
  const content = await client.request<Blob>(client.contentUrl(shot.content_url), { binary: true }); expect(Buffer.from(await content.arrayBuffer())).toEqual(bytes);
  await expect(client.remove("builds", p, build.id)).rejects.toMatchObject({ status: 409, code: "RESOURCE_IN_USE", requestId: expect.any(String) });
  await client.patch("strings", p, entry.id, { text: "" }); expect((await client.screenshotExpected(p, shot.id)).items[1].text).toBe("");
  await client.remove("strings", p, entry.id); expect((await client.screenshotExpected(p, shot.id)).missing_count).toBe(2);
  // Raw invalid request bypasses client validation to verify authoritative server field errors.
  await expect(client.request(resourcePath("strings", p), { method: "POST", body: { build_id: build.id, locale_id: locale.id, string_id: "empty", text: 7 } })).rejects.toMatchObject({ status: 422, details: expect.arrayContaining([expect.objectContaining({ field: "body.text" })]), requestId: expect.any(String) });
  for (const kind of ["builds", "locales", "categories", "situations", "string-keys", "strings"] as Resource[]) expect((await client.list(kind, p)).total).toBeGreaterThan(0);
  const cors = await fetch(origin + "/api/v1/projects", { method: "OPTIONS", headers: { Origin: "http://127.0.0.1:3001", "Access-Control-Request-Method": "PATCH", "Access-Control-Request-Headers": "content-type" } });
  expect(cors.headers.get("Access-Control-Allow-Origin")).toBe("http://127.0.0.1:3001");
}, 30000);
