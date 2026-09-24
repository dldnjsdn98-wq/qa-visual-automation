import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { api, ApiError } from "../lib/api";
import { Catalog, Editor } from "../components/catalog";
import { ExpectedTable, useRequest } from "../components/common";
import { ScreenshotDetail, Upload } from "../components/screenshots";
import Workspace from "../components/workspace";
import { initialNavigation } from "../lib/navigation";
import type { ExpectedStrings, Project, Screenshot } from "../lib/types";
const project: Project = { id: "p", slug: "qa", name: "QA", description: "old", created_at: "2026-09-06T00:00:00Z", updated_at: "2026-09-06T00:00:00Z" };
const expected: ExpectedStrings = { project_id: "p", build_id: "b", locale_id: "l", situation_id: "s", catalog_mode: "current", total: 3, missing_count: 1, items: [
  { string_key_id: "k1", string_id: "welcome", position: 0, entry_id: "e", text: "ようこそ 한글 😀", translation_status: "present" },
  { string_key_id: "k2", string_id: "empty", position: 1, entry_id: "e2", text: "", translation_status: "present" },
  { string_key_id: "k3", string_id: "missing", position: 2, entry_id: null, text: null, translation_status: "missing" },
] };
const state = { ...initialNavigation, project: "p", build: "b", locale: "l", category: "c", situation: "s" };
const screenshot: Screenshot = { id: "shot", project_id: "p", build_id: "b", locale_id: "l", category_id: "c", situation_id: "s", source: "manual", metadata_version: 1, metadata: {}, original_filename: "qa.png", uploaded_at: "2026-09-06T01:00:00Z", media_type: "image/png", file_hash: "a".repeat(64), width: 1, height: 1, size_bytes: 68, client_upload_id: null, content_url: "/api/v1/projects/p/screenshots/shot/content" };
describe("QA workflows", () => {
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
    expect(await screen.findByText("Project QA")).toBeVisible(); expect(await screen.findByText("원본 저장소 오류")).toBeVisible(); expect(screen.getByText("ようこそ 한글 😀")).toBeVisible(); expect(content).toHaveBeenCalledWith("http://127.0.0.1:8001/api/v1/projects/p/screenshots/shot/content", expect.objectContaining({ binary: true }));
  });
});
