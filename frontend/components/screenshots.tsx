"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError } from "../lib/api";
import { navigationUrl, type Navigation } from "../lib/navigation";
import type { Screenshot } from "../lib/types";
import type { Options } from "./catalog";
import { Empty, ErrorBox, ExpectedTable, Field, Loading, Pager, useRequest } from "./common";

export function Upload({ state, go, changed }: { state: Navigation; go: (state: Navigation) => void; changed: () => void }) {
  const [file, setFile] = useState<File>(); const [error, setError] = useState<unknown>(); const [busy, setBusy] = useState(false); const [ambiguous, setAmbiguous] = useState(false);
  const mounted = useRef(true); useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(undefined); setAmbiguous(false);
    if (!file || !state.build || !state.locale || !state.category || !state.situation) { setError(new Error("Build, Locale, Category, Situation과 파일을 모두 선택하세요.")); return; }
    setBusy(true);
    try {
      const screenshot = await api.upload(state.project, file, { build_id: state.build, locale_id: state.locale, category_id: state.category, situation_id: state.situation, source: "manual", metadata_version: 1, metadata: {} });
      changed(); if (mounted.current) go({ ...state, view: "detail", id: screenshot.id });
    } catch (issue) { setError(issue); setAmbiguous(issue instanceof ApiError && (issue.status === 0 || issue.status >= 500 || issue.code === "CONTRACT_ERROR")); }
    finally { setBusy(false); }
  }
  return <section><p>상단에서 Build, Locale, Category, Situation을 선택한 후 PNG 또는 JPEG 원본 한 장을 업로드하세요.</p>
    <form onSubmit={submit} className="editor" aria-label="Screenshot Upload"><ErrorBox error={error} />
      {ambiguous && <div role="alert" className="notice">서버에 저장되었을 수 있습니다. 먼저 Screenshot List에서 파일명과 시간을 확인하세요. 자동 재시도하지 않습니다. <a href={navigationUrl({ ...state, view: "screenshots", id: "" })}>Screenshot List 확인</a></div>}
      <fieldset disabled={busy}><Field label="Screenshot 파일" name="file" error={error}>{props => <input {...props} type="file" accept="image/png,image/jpeg" required onChange={e => { setFile(e.target.files?.[0]); setError(undefined); setAmbiguous(false); }} />}</Field>
        <p className="muted">PNG / JPEG · 최대 20 MiB · Source: manual</p>{file && <p>{file.name} · {file.size.toLocaleString()} bytes</p>}
        <button className="primary" type="submit" disabled={ambiguous}>{busy ? "업로드 중…" : "업로드"}</button>
        {ambiguous && <button type="button" onClick={() => setAmbiguous(false)}>목록 확인 완료 — 수동 재시도 허용</button>}
      </fieldset>
    </form>
  </section>;
}
export function ScreenshotList({ state, options, revision }: { state: Navigation; options: Options; revision: number }) {
  const [offset, setOffset] = useState(0);
  const data = useRequest(`screenshots/${JSON.stringify(state)}/${offset}/${revision}`, signal => api.screenshots(state.project, { build_id: state.build, locale_id: state.locale, situation_id: state.situation, category_id: state.category, offset, limit: 50 }, signal));
  const label = (key: string, id: string) => options[key]?.find(item => item.id === id)?.label || id;
  return <section><div className="toolbar"><a className="button primary" href={navigationUrl({ ...state, view: "upload", id: "" })}>Screenshot Upload</a><button onClick={data.reload}>새로고침</button><span className="muted">최근 업로드 순 · 선택한 필터 모두 적용</span></div><ErrorBox error={data.error} retry={data.reload} />
    {data.loading ? <Loading /> : data.data && <>{!data.data.items.length ? <Empty>조건에 맞는 Screenshot이 없습니다. 필터를 바꾸거나 파일을 업로드하세요.</Empty> : <div className="table-wrap"><table><thead><tr><th>Screenshot</th><th>Build</th><th>Locale</th><th>Category</th><th>Situation</th><th>Source</th><th>Uploaded Time</th></tr></thead><tbody>{data.data.items.map(item => <tr key={item.id}><td><a href={navigationUrl({ ...state, view: "detail", id: item.id })}>{item.original_filename}</a><small>{item.width} × {item.height}</small></td><td>{label("build_id", item.build_id)}</td><td>{label("locale_id", item.locale_id)}</td><td>{label("category_id", item.category_id)}</td><td>{label("situation_id", item.situation_id)}</td><td>{item.source}</td><td><time dateTime={item.uploaded_at}>{new Date(item.uploaded_at).toLocaleString()}</time></td></tr>)}</tbody></table></div>}<Pager page={data.data} onChange={setOffset} /></>}
  </section>;
}
function ScreenshotImage({ screenshot }: { screenshot: Screenshot }) {
  const [url, setUrl] = useState(""); const [decodeError, setDecodeError] = useState(false);
  const data = useRequest(`image/${screenshot.id}`, async signal => api.request<Blob>(api.contentUrl(screenshot.content_url), { signal, binary: true }));
  useEffect(() => {
    if (!data.data) { setUrl(""); return; }
    const objectUrl = URL.createObjectURL(data.data); setUrl(objectUrl); setDecodeError(false);
    return () => URL.revokeObjectURL(objectUrl);
  }, [data.data]);
  return <section className="image-panel"><ErrorBox error={data.error} retry={data.reload} />{data.loading && <Loading />}{decodeError && <ErrorBox error={new Error("이미지를 표시할 수 없습니다.")} retry={data.reload} />}
    {url && <><a href={api.contentUrl(screenshot.content_url)} target="_blank" rel="noreferrer">원본 크기로 열기</a><img className="screenshot" src={url} alt={screenshot.original_filename} onError={() => setDecodeError(true)} /></>}
  </section>;
}
export function ScreenshotDetail({ state, options }: { state: Navigation; options: Options }) {
  const data = useRequest(`detail/${state.project}/${state.id}`, signal => api.screenshot(state.project, state.id, signal));
  const expected = useRequest(`detail-expected/${state.project}/${state.id}`, signal => api.screenshotExpected(state.project, state.id, signal));
  const label = (key: string, id: string) => options[key]?.find(item => item.id === id)?.label || id;
  return <section><div className="toolbar"><a href={navigationUrl({ ...state, view: "screenshots", id: "" })}>← Screenshot List</a><button onClick={() => { data.reload(); expected.reload(); }}>새로고침</button></div><ErrorBox error={data.error} retry={data.reload} />
    {data.loading && <Loading />}{data.data && <><h2>{data.data.original_filename}</h2><dl className="metadata">{[
      ["Project", label("project_id", data.data.project_id)], ["Build", label("build_id", data.data.build_id)], ["Locale", label("locale_id", data.data.locale_id)], ["Category", label("category_id", data.data.category_id)], ["Situation", label("situation_id", data.data.situation_id)], ["Source", data.data.source], ["Uploaded Time (UTC)", data.data.uploaded_at], ["Size", `${data.data.width} × ${data.data.height} · ${data.data.size_bytes.toLocaleString()} bytes`], ["Screenshot ID", data.data.id],
    ].map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl><ScreenshotImage key={data.data.id} screenshot={data.data} /></>}
    <ErrorBox error={expected.error} retry={expected.reload} />{expected.loading && <Loading />}{expected.data && <ExpectedTable data={expected.data} />}
  </section>;
}
