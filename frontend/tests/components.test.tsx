import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { api, ApiError } from "../lib/api";
import { Catalog, Editor } from "../components/catalog";
import { ExpectedTable, useRequest } from "../components/common";
import { ScreenshotDetail, Upload } from "../components/screenshots";
import Workspace from "../components/workspace";
import { changeScreenshot, changeSelection, initialNavigation, navigationTransition, navigationUrl, parseNavigation } from "../lib/navigation";
import type { ExpectedStrings, Project, Screenshot } from "../lib/types";
const project: Project = { id: "p", slug: "qa", name: "QA", description: "old", created_at: "2026-09-06T00:00:00Z", updated_at: "2026-09-06T00:00:00Z" };
const expected: ExpectedStrings = { project_id: "p", build_id: "b", locale_id: "l", situation_id: "s", catalog_mode: "current", total: 3, missing_count: 1, items: [
  { string_key_id: "k1", string_id: "welcome", position: 0, entry_id: "e", text: "ようこそ 한글 😀", translation_status: "present" },
  { string_key_id: "k2", string_id: "empty", position: 1, entry_id: "e2", text: "", translation_status: "present" },
  { string_key_id: "k3", string_id: "missing", position: 2, entry_id: null, text: null, translation_status: "missing" },
] };
const state = { ...initialNavigation, project: "p", build: "b", locale: "l", category: "c", situation: "s" };
const screenshot: Screenshot = { id: "shot", project_id: "p", build_id: "b", locale_id: "l", category_id: "c", situation_id: "s", source: "manual", metadata_version: 1, metadata: {}, original_filename: "qa.png", uploaded_at: "2026-09-06T01:00:00Z", media_type: "image/png", file_hash: "a".repeat(64), width: 1, height: 1, size_bytes: 68, client_upload_id: null, content_url: "/api/v1/projects/p/screenshots/shot/content" };
const runA = "11111111-1111-4111-8111-111111111111";
const runB = "22222222-2222-4222-8222-222222222222";
describe("QA workflows", () => {
  it("round-trips a selected run in Screenshot Detail deep links", () => {
    const detail = { ...state, view: "detail", id: "shot", run: runA } as const;
    const url = navigationUrl(detail);
    expect(url).toContain(`run=${runA}`);
    expect(parseNavigation(url)).toEqual(detail);
    expect(parseNavigation(`#/screenshots?project=p&run=${runA}`).run).toBe("");
  });
  it("resets a selected run when its project, filter, or screenshot changes", () => {
    const detail = { ...state, view: "detail", id: "shot", run: runA } as const;
    expect(changeSelection(detail, "project", "p2").run).toBe("");
    expect(changeSelection(detail, "locale", "l2").run).toBe("");
    expect(changeScreenshot(detail, "shot-2").run).toBe("");
    expect(navigationTransition(detail, { ...detail, run: runB }).run).toBe(runB);
  });
  it("preserves deep-linked and back-forward selected runs as distinct page identities", async () => {
    window.location.hash = `#/detail?project=p&id=shot&run=${runA}`;
    vi.spyOn(api, "list").mockResolvedValue({ items: [], total: 0, limit: 100, offset: 0 } as never);
    const detail = vi.spyOn(api, "screenshot").mockResolvedValue(screenshot);
    vi.spyOn(api, "screenshotExpected").mockResolvedValue(expected);
    vi.spyOn(api, "request").mockRejectedValue(new ApiError(503, "STORAGE_UNAVAILABLE", "offline"));
    render(<Workspace />);
    await waitFor(() => expect(detail).toHaveBeenCalledTimes(1));
    window.location.hash = `#/detail?project=p&id=shot&run=${runB}`;
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    await waitFor(() => expect(detail).toHaveBeenCalledTimes(2));
    window.location.hash = `#/detail?project=p&id=shot&run=${runA}`;
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    await waitFor(() => expect(detail).toHaveBeenCalledTimes(3));
    expect(window.location.hash).toContain(`run=${runA}`);
  });
  it("keeps an unknown selected run deep link without hiding Screenshot Detail", async () => {
    const unknownRun = "33333333-3333-4333-8333-333333333333";
    window.location.hash = `#/detail?project=p&id=shot&run=${unknownRun}`;
    vi.spyOn(api, "list").mockResolvedValue({ items: [], total: 0, limit: 100, offset: 0 } as never);
    vi.spyOn(api, "screenshot").mockResolvedValue(screenshot);
    vi.spyOn(api, "screenshotExpected").mockResolvedValue(expected);
    vi.spyOn(api, "request").mockRejectedValue(new ApiError(503, "STORAGE_UNAVAILABLE", "offline"));
    render(<Workspace />);
    expect(await screen.findByText("qa.png")).toBeVisible();
    expect(parseNavigation(window.location.hash).run).toBe(unknownRun);
  });
  it("shows field errors, request ID and preserves entered values", async () => {
    vi.spyOn(api, "create").mockRejectedValue(new ApiError(422, "VALIDATION_ERROR", "서버 검증 오류", [{ field: "body.name", reason: "이름을 확인하세요" }], "req-123"));
    render(<Editor kind="projects" project="" options={{}} onSaved={vi.fn()} onCancel={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Slug"), { target: { value: "qa" } }); fireEvent.change(screen.getByLabelText("Name"), { target: { value: "한글 😀" } }); fireEvent.click(screen.getByRole("button", { name: "저장" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("req-123"); expect(screen.getByLabelText("Name")).toHaveValue("한글 😀"); expect(screen.getByLabelText("Name")).toHaveAttribute("aria-invalid", "true");
  });
  it("PATCH only sends changed fields and explicitly clears description", async () => {
    const patch = vi.spyOn(api, "patch").mockResolvedValue(project); const saved = vi.fn(); render(<Editor kind="projects" project="" row={project} options={{}} onSaved={saved} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByRole("checkbox")); fireEvent.click(screen.getByRole("button", { name: "저장" })); await waitFor(() => expect(patch).toHaveBeenCalledWith("projects", "", "p", { description: null })); expect(saved).toHaveBeenCalled();
  });
  it("accepts empty translation and 10000 supplementary scalars", async () => {
    const create = vi.spyOn(api, "create").mockResolvedValue({} as never); render(<Editor kind="strings" project="p" defaults={{ build_id: "b", locale_id: "l", string_id: "welcome" }} options={{}} onSaved={vi.fn()} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "저장" })); await waitFor(() => expect(create).toHaveBeenCalledWith("strings", "p", { build_id: "b", locale_id: "l", string_id: "welcome", text: "" }));
    fireEvent.change(screen.getByLabelText("Text"), { target: { value: "😀".repeat(10000) } }); fireEvent.click(screen.getByRole("button", { name: "저장" })); await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
  });
  it("distinguishes missing, empty and multilingual expectations", () => {
    render(<ExpectedTable data={expected} />); expect(screen.getByText("번역 누락")).toBeVisible(); expect(screen.getByText("빈 문자열 (등록됨)")).toBeVisible(); expect(screen.getByText("ようこそ 한글 😀")).toBeVisible(); expect(screen.getByText(/현재 Build 카탈로그/)).toBeVisible();
  });
  it("shows loading then empty state and explains restrictive deletes", async () => {
    let resolve!: (value: never) => void; vi.spyOn(api, "list").mockImplementation(() => new Promise(done => { resolve = done; }) as never);
    const view = render(<Catalog kind="projects" project="" options={{}} revision={0} onChanged={vi.fn()} />); expect(screen.getByRole("status")).toHaveTextContent("불러오는 중"); await act(async () => resolve({ items: [], total: 0, offset: 0, limit: 50 } as never)); expect(screen.getByText(/데이터가 없습니다/)).toBeVisible(); view.unmount();
    vi.spyOn(api, "list").mockResolvedValue({ items: [project], total: 1, offset: 0, limit: 50 }); vi.spyOn(api, "remove").mockRejectedValue(new ApiError(409, "RESOURCE_IN_USE", "Referenced")); render(<Catalog kind="projects" project="" options={{}} revision={0} onChanged={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "삭제" })); fireEvent.click(screen.getByRole("button", { name: "삭제 확인" })); expect(await screen.findByRole("alert")).toHaveTextContent("참조 중인 데이터"); expect(screen.getByRole("cell", { name: "QA" })).toBeVisible();
  });
  it("ignores late responses after scope changes", async () => {
    const resolvers: Record<string, (value: string) => void> = {}; function Probe({ scope }: { scope: string }) { const request = useRequest(scope, () => new Promise<string>(resolve => { resolvers[scope] = resolve; })); return <div>{request.loading ? "Loading" : request.data}</div>; }
    const view = render(<Probe scope="old" />); await act(async () => {}); view.rerender(<Probe scope="new" />); await act(async () => {}); await act(async () => resolvers.new("new data")); await act(async () => resolvers.old("old data")); expect(screen.getByText("new data")).toBeVisible(); expect(screen.queryByText("old data")).toBeNull();
  });
  it("clears dependent filters when changing Project", async () => {
    window.location.hash = "#/screenshots?project=p&build=b&locale=l&category=c&situation=s";
    vi.spyOn(api, "list").mockImplementation(async kind => ({ items: kind === "projects" ? [project, { ...project, id: "p2", slug: "qa2", name: "QA2" }] : [], total: kind === "projects" ? 2 : 0, limit: 100, offset: 0 }) as never);
    const shots = vi.spyOn(api, "screenshots").mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 }); render(<Workspace />); await waitFor(() => expect(screen.getByLabelText("Project")).not.toBeDisabled()); fireEvent.change(screen.getByLabelText("Project"), { target: { value: "p2" } });
    await waitFor(() => expect(shots).toHaveBeenLastCalledWith("p2", { build_id: "", locale_id: "", category_id: "", situation_id: "", offset: 0, limit: 50 }, expect.any(AbortSignal))); for (const label of ["Build", "Locale", "Category", "Situation"]) expect(screen.getByLabelText(label)).toHaveValue("");
  });
  it("retains upload input and requires list inspection after ambiguous failure", async () => {
    const upload = vi.spyOn(api, "upload").mockRejectedValue(new ApiError(503, "DATABASE_UNAVAILABLE", "unavailable")); const go = vi.fn(); render(<Upload state={state} go={go} changed={vi.fn()} />);
    await userEvent.upload(screen.getByLabelText("Screenshot 파일"), new File(["png"], "qa.png", { type: "image/png" })); fireEvent.submit(screen.getByRole("form", { name: "Screenshot Upload" })); expect(await screen.findByText(/서버에 저장되었을 수 있습니다/)).toBeVisible(); expect(screen.getByRole("button", { name: "업로드" })).toBeDisabled(); expect(upload).toHaveBeenCalledTimes(1); expect(go).not.toHaveBeenCalled(); expect(screen.getByText(/qa.png/)).toBeVisible();
  });
  it("navigates to detail only after successful upload", async () => {
    vi.spyOn(api, "upload").mockResolvedValue(screenshot); const go = vi.fn(); render(<Upload state={state} go={go} changed={vi.fn()} />); await userEvent.upload(screen.getByLabelText("Screenshot 파일"), new File(["png"], "qa.png", { type: "image/png" })); fireEvent.submit(screen.getByRole("form", { name: "Screenshot Upload" })); await waitFor(() => expect(go).toHaveBeenCalledWith({ ...state, view: "detail", id: "shot" }));
  });
  it("loads detail and expectations independently of storage failure", async () => {
    vi.spyOn(api, "screenshot").mockResolvedValue(screenshot); vi.spyOn(api, "screenshotExpected").mockResolvedValue(expected); const content = vi.spyOn(api, "request").mockRejectedValue(new ApiError(503, "STORAGE_UNAVAILABLE", "원본 저장소 오류", [], "image-request")); render(<ScreenshotDetail state={{ ...state, id: "shot" }} options={{ project_id: [{ id: "p", label: "Project QA" }] }} />);
    expect(await screen.findByText("Project QA")).toBeVisible(); expect((await screen.findAllByText("원본 저장소 오류"))[0]).toBeVisible(); expect(screen.getByText("ようこそ 한글 😀")).toBeVisible(); expect(content).toHaveBeenCalledWith("http://127.0.0.1:8001/api/v1/projects/p/screenshots/shot/content", expect.objectContaining({ binary: true }));
  });
  it("shows complete agent metadata and client identity as safe deterministic text", async () => {
    const metadata = { z_unknown: { empty: "", missing: null, values: ["😀", "e\u0301", "<img data-testid=\"metadata-injection\" src=x>"] }, a_first: "한글" };
    const agent: Screenshot = { ...screenshot, source: "agent", client_upload_id: "11111111-1111-4111-8111-111111111111", metadata };
    vi.spyOn(api, "screenshot").mockResolvedValue(agent); vi.spyOn(api, "screenshotExpected").mockResolvedValue(expected); vi.spyOn(api, "request").mockRejectedValue(new ApiError(503, "STORAGE_UNAVAILABLE", "offline"));
    const view = render(<ScreenshotDetail state={{ ...state, id: "shot" }} options={{}} />);
    expect(await screen.findByText("agent")).toBeVisible(); expect(screen.getByText(agent.client_upload_id!)).toBeVisible(); const versionLabel = screen.getByText("Metadata Version"); expect(versionLabel).toBeVisible(); expect(versionLabel.parentElement?.querySelector("dd")).toHaveTextContent("1");
    expect(screen.getByText("Capture Metadata")).toBeVisible();
    expect(view.container.querySelector("pre.metadata-json")?.textContent).toBe(JSON.stringify({ a_first: "한글", z_unknown: { empty: "", missing: null, values: ["😀", "e\u0301", "<img data-testid=\"metadata-injection\" src=x>"] } }, null, 2));
    expect(view.container.querySelector('[data-testid="metadata-injection"]')).toBeNull();
  });
  it("keeps manual null identity absent and renders automation source through the same detail path", async () => {
    vi.spyOn(api, "screenshot").mockResolvedValue(screenshot); vi.spyOn(api, "screenshotExpected").mockResolvedValue(expected); vi.spyOn(api, "request").mockRejectedValue(new ApiError(503, "STORAGE_UNAVAILABLE", "offline"));
    const manual = render(<ScreenshotDetail state={{ ...state, id: "shot" }} options={{}} />);
    expect(await screen.findByText("manual")).toBeVisible(); expect(screen.queryByText("Client Upload ID")).toBeNull(); expect(manual.container.querySelector("pre.metadata-json")?.textContent).toBe("{}");
    manual.unmount();
    vi.mocked(api.screenshot).mockResolvedValue({ ...screenshot, source: "automation", client_upload_id: "22222222-2222-4222-8222-222222222222" });
    render(<ScreenshotDetail state={{ ...state, id: "shot" }} options={{}} />);
    expect(await screen.findByText("automation")).toBeVisible();
  });
  it("renders successful OCR evidence with explicit zero, null, empty and unknown values", async () => {
    const completedRun = {
      id: runA, project_id: "p", screenshot_id: "shot", client_run_id: runB, protocol_version: 1, profile_id: "fixture-v1", profile_digest: "d".repeat(64), status: "SUCCEEDED", stage: "COMPLETE", created_at: "2026-09-25T00:00:00Z", updated_at: "2026-09-25T00:01:00Z", started_at: "2026-09-25T00:00:01Z", completed_at: "2026-09-25T00:01:00Z", attempt_count: 1, next_attempt_at: null, verification_status: "PASS", error: null,
      snapshot: { version: 1, sha256: "a".repeat(64), captured_at: "2026-09-25T00:00:00Z", item_count: 1, missing_count: 0, locale_code: "ko-KR", ocr_language: "ko", screenshot_file_hash: "b".repeat(64), width: 320, height: 180 },
      configuration: { profile_id: "fixture-v1", profile_digest: "d".repeat(64), normalization_version: "norm-v1", matching_version: "match-v1", pass_threshold: 95, review_threshold: 85 }, ocr_result_id: "ocr", verification_result_id: "verification", links: { self: "", expected: "", ocr: "", regions: "", verification: "", items: "" },
    } as const;
    vi.spyOn(api, "screenshot").mockResolvedValue(screenshot); vi.spyOn(api, "screenshotExpected").mockResolvedValue(expected); vi.spyOn(api, "request").mockRejectedValue(new ApiError(503, "STORAGE_UNAVAILABLE", "offline"));
    vi.spyOn(api, "ocrProfiles").mockResolvedValue({ items: [] });
    vi.spyOn(api, "verificationRuns").mockResolvedValue({ items: [completedRun], total: 1, limit: 50, offset: 0 });
    vi.spyOn(api, "verificationRunResult").mockResolvedValue({ run: completedRun, retryAfter: "2" });
    vi.spyOn(api, "ocrSummary").mockResolvedValue({ id: "ocr", run_id: runA, project_id: "p", screenshot_id: "shot", coordinate_space: "original-raster-v1", width: 320, height: 180, region_count: 1, no_text: false, profile_id: "fixture-v1", profile_digest: "d", engine_name: "fixture", engine_version: "1", ocr_language: "ko", runtime_manifest: {}, preprocessing: { exif_policy: "ignored-v1", exif_orientation: 6, pixel_sha256: "e", steps: [], original_to_inference_matrix3x3: [[1,0,0],[0,1,0],[0,0,1]] }, output_sha256: "f", created_at: "2026-09-25T00:01:00Z" });
    vi.spyOn(api, "verificationSummary").mockResolvedValue({ id: "verification", run_id: runA, project_id: "p", screenshot_id: "shot", ocr_result_id: "ocr", snapshot_sha256: "a", configuration_sha256: "c", matching_version: "match-v1", normalization_version: "norm-v1", verification_status: "PASS", evaluation_reason: "EVALUATED", incomplete: false, total_count: 1, evaluated_count: 1, unverified_count: 0, pass_count: 1, review_count: 0, fail_count: 0, unmatched_region_count: 0, pass_threshold: 95, review_threshold: 85, created_at: "2026-09-25T00:01:00Z" });
    vi.spyOn(api, "verificationExpected").mockResolvedValue({ items: [{ position: 0, string_key_id: "key", string_id: "empty", entry_id: "entry", expected_text: "", translation_status: "present" }], total: 1, limit: 50, offset: 0 });
    vi.spyOn(api, "ocrRegions").mockResolvedValue({ items: [{ region_index: 0, text: "", confidence: 0, confidence_semantics: "recognition", detection_confidence: null, detection_confidence_unavailable_reason: "NOT_EXPOSED_BY_PROFILE", polygon: [[0,0],[10,0],[10,5],[0,5]], bbox: { x: 0, y: 0, width: 10, height: 5 }, clipped: false, engine_region_index: 0 }], total: 1, limit: 50, offset: 0 });
    vi.spyOn(api, "verificationItems").mockResolvedValue({ items: [{ expected_position: 0, string_key_id: "key", string_id: "empty", entry_id: "entry", expected_text: "", normalized_expected: "", translation_status: "present", region_index: null, observed_text: null, normalized_observed: null, match_method: "future-method", match_score: null, score_numerator: null, score_denominator: null, verification_status: "future-quality", reason: "future-reason" }], total: 1, limit: 50, offset: 0 });
    render(<ScreenshotDetail state={{ ...state, view: "detail", id: "shot", run: runA }} options={{}} selectedRunId={runA} />);
    expect(await screen.findByText("OCR Regions · Raw Raster Coordinates")).toBeVisible();
    expect(screen.getByText(/오버레이는 표시하지 않습니다/)).toBeVisible();
    expect(await screen.findByText("Unknown: future-method")).toBeVisible(); expect(screen.getByText("Unknown: future-quality")).toBeVisible(); expect(screen.getByText("Unknown: future-reason")).toBeVisible();
    expect(screen.getByText("Not scored")).toBeVisible(); expect(screen.getByText("Not exposed")).toBeVisible(); expect(screen.getAllByText("빈 문자열").length).toBeGreaterThan(0); expect(screen.getAllByRole("cell", { name: "0" }).length).toBeGreaterThan(0);
  });
  it("retries an ambiguous run request with the same persisted client_run_id", async () => {
    sessionStorage.clear();
    vi.spyOn(api, "screenshot").mockResolvedValue(screenshot); vi.spyOn(api, "screenshotExpected").mockResolvedValue(expected); vi.spyOn(api, "request").mockRejectedValue(new ApiError(503, "STORAGE_UNAVAILABLE", "offline"));
    vi.spyOn(api, "ocrProfiles").mockResolvedValue({ items: [{ profile_id: "fixture-v1", profile_digest: "d", engine_name: "fixture", engine_version: "1", model_ids: [], language_tags: ["ko-KR"], coordinate_space: "original-raster-v1", normalization_version: "norm-v1", matching_version: "match-v1", availability: "AVAILABLE", unavailable_code: null }] });
    vi.spyOn(api, "verificationRuns").mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 });
    const create = vi.spyOn(api, "createVerificationRun").mockRejectedValueOnce(new ApiError(503, "DATABASE_UNAVAILABLE", "retry", [], "req", "5")).mockResolvedValueOnce({ run: { id: runA }, status: 200 } as never);
    render(<ScreenshotDetail state={{ ...state, view: "detail", id: "shot", run: "" }} options={{}} />);
    await waitFor(() => expect(screen.getByLabelText("OCR profile")).toHaveValue("fixture-v1"));
    fireEvent.submit(screen.getByRole("form", { name: "Create OCR verification run" }));
    expect(await screen.findByText(/같은 Client Run ID/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "같은 요청 재시도" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(create.mock.calls[1][2]).toEqual(create.mock.calls[0][2]);
    expect(create.mock.calls[0][2].client_run_id).toBeTruthy();
  });
});
