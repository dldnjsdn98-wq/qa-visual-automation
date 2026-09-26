"use client";
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { api, ApiError } from "../lib/api";
import { navigationUrl, type Navigation } from "../lib/navigation";
import type { CreateVerificationRun, ExpectedItem, Json, OcrRegion, Page, Run, RunSummary, Screenshot, VerificationItem, VerificationStatus } from "../lib/types";
import type { Options } from "./catalog";
import { Empty, ErrorBox, ExpectedTable, Field, Loading, Pager, useRequest } from "./common";

function sortJson(value: Json): Json {
  if (Array.isArray(value)) return value.map(sortJson);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort((a, b) => a < b ? -1 : a > b ? 1 : 0).map(key => [key, sortJson(value[key])]));
  return value;
}
function formatMetadata(metadata: Screenshot["metadata"]): string { return JSON.stringify(sortJson(metadata as Json), null, 2); }

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

const processingStates = new Set(["PENDING", "RUNNING", "RETRY_WAIT", "SUCCEEDED", "FAILED"]);
const stages = new Set(["QUEUED", "OCR", "VERIFY", "COMPLETE"]);
const qualityStates = new Set(["PASS", "REVIEW", "FAIL", "UNVERIFIED"]);
const matchMethods = new Set(["EXACT", "NORMALIZED", "FUZZY", "NONE"]);
const itemReasons = new Set(["MATCHED", "NO_MATCH", "MISSING_TRANSLATION", "EMPTY_EXPECTED", "NORMALIZED_EMPTY_EXPECTED"]);
const terminalStates = new Set(["SUCCEEDED", "FAILED"]);

function known(value: string | null, values: Set<string>): string {
  if (value === null) return "—";
  return values.has(value) ? value : `Unknown: ${value}`;
}
function StatusBadge({ value, kind }: { value: string | null; kind: "processing" | "quality" }) {
  const allowed = kind === "processing" ? processingStates : qualityStates;
  const label = known(value, allowed);
  const token = allowed.has(value || "") ? value!.toLowerCase() : "unknown";
  return <span className={`status-badge ${kind}-${token}`}>{label}</span>;
}
function RawText({ value }: { value: string | null }) {
  if (value === null) return <span className="muted">null</span>;
  if (value === "") return <span className="muted">빈 문자열</span>;
  return <span className="raw-text" dir="auto">{value}</span>;
}
function PageControls({ page, offset, setOffset }: { page: Page<unknown>; offset: number; setOffset: (value: number) => void }) {
  return <div className="pager"><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - page.limit))}>이전</button><span>{page.total === 0 ? "0개" : `${offset + 1}–${Math.min(offset + page.items.length, page.total)} / ${page.total}`}</span><button disabled={offset + page.items.length >= page.total} onClick={() => setOffset(offset + page.limit)}>다음</button></div>;
}
function PagedResult<T>({ title, load, render }: { title: string; load: (offset: number, signal: AbortSignal) => Promise<Page<T>>; render: (items: T[]) => ReactNode }) {
  const [offset, setOffset] = useState(0);
  const data = useRequest(`${title}/${offset}`, signal => load(offset, signal));
  return <section className="run-result-section"><h3>{title}</h3><ErrorBox error={data.error} retry={data.reload} />{data.loading && <Loading />}{data.data && <>{data.data.items.length ? render(data.data.items) : <Empty>{title} 항목이 없습니다.</Empty>}<PageControls page={data.data} offset={offset} setOffset={setOffset} /></>}</section>;
}
function SuccessfulRunResults({ project, screenshot, run }: { project: string; screenshot: string; run: Run }) {
  const ocr = useRequest(`ocr-summary/${run.id}`, signal => api.ocrSummary(project, screenshot, run.id, signal));
  const verification = useRequest(`verification-summary/${run.id}`, signal => api.verificationSummary(project, screenshot, run.id, signal));
  return <div className="run-results"><section><h3>OCR Summary</h3><ErrorBox error={ocr.error} retry={ocr.reload} />{ocr.loading && <Loading />}{ocr.data && <dl className="metadata"><div><dt>Coordinate space</dt><dd>{known(ocr.data.coordinate_space, new Set(["original-raster-v1"]))}</dd></div><div><dt>Raster</dt><dd>{ocr.data.width} × {ocr.data.height}</dd></div><div><dt>Regions</dt><dd>{ocr.data.region_count}</dd></div><div><dt>No text</dt><dd>{ocr.data.no_text ? "Yes" : "No"}</dd></div><div><dt>Engine</dt><dd>{ocr.data.engine_name} {ocr.data.engine_version}</dd></div></dl>}</section>
    <section><h3>Verification Summary</h3><ErrorBox error={verification.error} retry={verification.reload} />{verification.loading && <Loading />}{verification.data && <><StatusBadge value={verification.data.verification_status} kind="quality" /><dl className="metadata"><div><dt>Evaluation reason</dt><dd>{known(verification.data.evaluation_reason, new Set(["EVALUATED", "PARTIAL_UNVERIFIED", "NO_EVALUABLE_EXPECTATIONS", "NO_EXPECTATIONS"]))}</dd></div><div><dt>Evaluated</dt><dd>{verification.data.evaluated_count} / {verification.data.total_count}</dd></div><div><dt>PASS / REVIEW / FAIL</dt><dd>{verification.data.pass_count} / {verification.data.review_count} / {verification.data.fail_count}</dd></div><div><dt>Unverified</dt><dd>{verification.data.unverified_count}</dd></div><div><dt>Unmatched regions</dt><dd>{verification.data.unmatched_region_count}</dd></div></dl></>}</section>
    <div className="notice">OCR 좌표는 EXIF 방향을 적용하지 않은 original-raster-v1 기준입니다. 브라우저의 원본 방향 매핑을 보장할 수 없어 오버레이는 표시하지 않습니다. 아래 좌표표가 기준입니다.</div>
    <PagedResult<ExpectedItem> title="Run Expected Snapshot" load={(offset, signal) => api.verificationExpected(project, screenshot, run.id, { offset, limit: 50 }, signal)} render={items => <div className="table-wrap"><table><thead><tr><th>Position</th><th>String ID</th><th>Expected raw text</th><th>Translation</th></tr></thead><tbody>{items.map(item => <tr key={`${item.position}/${item.string_key_id}`}><td>{item.position}</td><td>{item.string_id}</td><td><RawText value={item.expected_text} /></td><td>{known(item.translation_status, new Set(["present", "missing"]))}</td></tr>)}</tbody></table></div>} />
    <PagedResult<OcrRegion> title="OCR Regions · Raw Raster Coordinates" load={(offset, signal) => api.ocrRegions(project, screenshot, run.id, { offset, limit: 50 }, signal)} render={items => <div className="table-wrap"><table><thead><tr><th>Index</th><th>Raw text</th><th>Confidence</th><th>Detection</th><th>BBox x, y, width, height</th><th>Polygon</th><th>Clipped</th></tr></thead><tbody>{items.map(region => <tr key={region.region_index}><td>{region.region_index}</td><td><RawText value={region.text} /></td><td>{region.confidence}</td><td>{region.detection_confidence === null ? "Not exposed" : region.detection_confidence}</td><td>{region.bbox.x}, {region.bbox.y}, {region.bbox.width}, {region.bbox.height}</td><td><code>{region.polygon.map(([x, y]) => `(${x}, ${y})`).join(" ")}</code></td><td>{region.clipped ? "Yes" : "No"}</td></tr>)}</tbody></table></div>} />
    <PagedResult<VerificationItem> title="Verification Items" load={(offset, signal) => api.verificationItems(project, screenshot, run.id, { offset, limit: 50 }, signal)} render={items => <div className="table-wrap"><table><thead><tr><th>Position</th><th>String ID</th><th>Expected raw</th><th>Observed raw</th><th>Region</th><th>Method</th><th>Score</th><th>Quality</th><th>Reason</th></tr></thead><tbody>{items.map(item => <tr key={`${item.expected_position}/${item.string_key_id}`}><td>{item.expected_position}</td><td>{item.string_id}</td><td><RawText value={item.expected_text} /></td><td><RawText value={item.observed_text} /></td><td>{item.region_index === null ? "Unassigned" : item.region_index}</td><td>{known(item.match_method, matchMethods)}</td><td>{item.match_score === null ? "Not scored" : item.match_score}</td><td><StatusBadge value={item.verification_status} kind="quality" /></td><td>{known(item.reason, itemReasons)}</td></tr>)}</tbody></table></div>} />
  </div>;
}

function RunDetail({ project, screenshot, runId }: { project: string; screenshot: string; runId: string }) {
  const [run, setRun] = useState<Run>();
  const [error, setError] = useState<unknown>();
  const [loading, setLoading] = useState(true);
  const [retryTick, setRetryTick] = useState(0);
  useEffect(() => {
    let stopped = false; let done = false; let timer: ReturnType<typeof setTimeout> | undefined; let failures = 0; let controller: AbortController | undefined;
    const load = async () => {
      timer = undefined;
      controller?.abort(); const current = new AbortController(); controller = current;
      try {
        const result = await api.verificationRunResult(project, screenshot, runId, current.signal);
        const next = result.run;
        if (stopped) return; setRun(next); setError(undefined); setLoading(false); failures = 0; done = terminalStates.has(next.status);
        const retrySeconds = Number(result.retryAfter);
        const delay = Number.isFinite(retrySeconds) && retrySeconds >= 0 ? retrySeconds * 1000 : 2000;
        if (!terminalStates.has(next.status) && document.visibilityState !== "hidden") timer = setTimeout(load, delay);
      } catch (issue) {
        if (stopped || current.signal.aborted) return; setError(issue); setLoading(false); failures += 1;
        const retrySeconds = issue instanceof ApiError ? Number(issue.retryAfter) : Number.NaN;
        const delay = Number.isFinite(retrySeconds) && retrySeconds >= 0 ? retrySeconds * 1000 : [5000, 10000, 20000, 30000][Math.min(failures - 1, 3)];
        if (document.visibilityState !== "hidden") timer = setTimeout(load, delay);
      }
    };
    const visible = () => {
      if (document.visibilityState === "hidden") { if (timer) clearTimeout(timer); timer = undefined; controller?.abort(); return; }
      if (!timer && !done) load();
    };
    load(); document.addEventListener("visibilitychange", visible);
    return () => { stopped = true; if (timer) clearTimeout(timer); controller?.abort(); document.removeEventListener("visibilitychange", visible); };
  }, [project, screenshot, runId, retryTick]);
  return <section className="selected-run" aria-labelledby="selected-run-heading"><h3 id="selected-run-heading">Selected Run</h3><ErrorBox error={error} retry={() => { setLoading(true); setRun(undefined); setRetryTick(value => value + 1); }} />{loading && <Loading />}{run && <><div className="run-status-line"><StatusBadge value={run.status} kind="processing" /><span>Stage: {known(run.stage, stages)}</span><span>Quality: <StatusBadge value={run.verification_status} kind="quality" /></span></div><dl className="metadata"><div><dt>Run ID</dt><dd>{run.id}</dd></div><div><dt>Client Run ID</dt><dd>{run.client_run_id}</dd></div><div><dt>Profile</dt><dd>{run.profile_id}</dd></div><div><dt>Requested</dt><dd>{run.created_at}</dd></div><div><dt>Completed</dt><dd>{run.completed_at || "Not completed"}</dd></div><div><dt>Attempts</dt><dd>{run.attempt_count}</dd></div>{run.next_attempt_at && <div><dt>Next attempt</dt><dd>{run.next_attempt_at}</dd></div>}<div><dt>Pass / review thresholds</dt><dd>{run.configuration.pass_threshold} / {run.configuration.review_threshold}</dd></div><div><dt>Normalization / matching</dt><dd>{run.configuration.normalization_version} / {run.configuration.matching_version}</dd></div></dl><section><h3>Immutable Expected Snapshot</h3><dl className="metadata"><div><dt>Captured</dt><dd>{run.snapshot.captured_at}</dd></div><div><dt>SHA-256</dt><dd><code>{run.snapshot.sha256}</code></dd></div><div><dt>Items / missing</dt><dd>{run.snapshot.item_count} / {run.snapshot.missing_count}</dd></div><div><dt>Locale / OCR language</dt><dd>{run.snapshot.locale_code} / {run.snapshot.ocr_language}</dd></div><div><dt>Source screenshot hash</dt><dd><code>{run.snapshot.screenshot_file_hash}</code></dd></div></dl></section>{run.error && <div role="alert" className="error"><strong>Persisted processing error: {run.error.code}</strong><p>{run.error.message}</p><small>Stage {known(run.error.stage, stages)} · attempt {run.error.attempt} · retryable {run.error.retryable ? "yes" : "no"} · correlation {run.error.correlation_id}</small></div>}{run.status === "SUCCEEDED" && <SuccessfulRunResults project={project} screenshot={screenshot} run={run} />}{run.status === "FAILED" && <Empty>처리가 실패했습니다. 품질 FAIL로 해석하지 않습니다. 새 실행은 별도로 요청하세요.</Empty>}</>}</section>;
}

function LatestCompleted({ state, run }: { state: Navigation; run: RunSummary }) {
  const summary = useRequest(`latest-completed-summary/${run.id}`, signal => api.verificationSummary(state.project, state.id, run.id, signal));
  return <div><p><a href={navigationUrl({ ...state, view: "detail", run: run.id })}>{run.id}</a> · <StatusBadge value={run.verification_status} kind="quality" /> · evaluated {summary.data ? `${summary.data.evaluated_count}/${summary.data.total_count}` : summary.loading ? "loading…" : "unavailable"}</p><ErrorBox error={summary.error} retry={summary.reload} /></div>;
}

function VerificationRuns({ state, selectedRunId }: { state: Navigation; selectedRunId: string }) {
  const profiles = useRequest(`ocr-profiles/${state.project}`, signal => api.ocrProfiles(state.project, signal));
  const [historyOffset, setHistoryOffset] = useState(0);
  const history = useRequest(`verification-runs/${state.project}/${state.id}/${historyOffset}`, signal => api.verificationRuns(state.project, state.id, { selection: "all", limit: 50, offset: historyOffset }, signal));
  const completed = useRequest(`verification-runs-completed/${state.project}/${state.id}`, signal => api.verificationRuns(state.project, state.id, { selection: "succeeded", limit: 1, offset: 0 }, signal));
  const [profileId, setProfileId] = useState(""); const [passThreshold, setPassThreshold] = useState(""); const [reviewThreshold, setReviewThreshold] = useState("");
  const [createError, setCreateError] = useState<unknown>(); const [creating, setCreating] = useState(false); const [pending, setPending] = useState<CreateVerificationRun>();
  const storageKey = `ocr-run-request/${state.project}/${state.id}`;
  useEffect(() => { try { const raw = sessionStorage.getItem(storageKey); if (raw) setPending(JSON.parse(raw) as CreateVerificationRun); } catch { sessionStorage.removeItem(storageKey); } }, [storageKey]);
  useEffect(() => { if (!profileId) { const available = profiles.data?.items.find(item => item.availability === "AVAILABLE"); if (available) setProfileId(available.profile_id); } }, [profiles.data, profileId]);
  useEffect(() => { if (!selectedRunId && history.data?.items[0] && state.view === "detail") window.location.hash = navigationUrl({ ...state, run: history.data.items[0].id }).slice(1); }, [history.data, selectedRunId, state]);
  const selected = selectedRunId || history.data?.items[0]?.id || "";
  const availableProfiles = profiles.data?.items.filter(item => item.availability === "AVAILABLE") || [];
  async function submit(event: FormEvent, retry = false) {
    event.preventDefault(); setCreateError(undefined);
    const request = retry && pending ? pending : { protocol_version: 1 as const, client_run_id: crypto.randomUUID(), profile_id: profileId, ...(passThreshold || reviewThreshold ? { verification: { ...(passThreshold ? { pass_threshold: Number(passThreshold) } : {}), ...(reviewThreshold ? { review_threshold: Number(reviewThreshold) } : {}) } } : {}) };
    if (!request.profile_id) { setCreateError(new Error("사용 가능한 OCR profile을 선택하세요.")); return; }
    setPending(request); sessionStorage.setItem(storageKey, JSON.stringify(request)); setCreating(true);
    try {
      const result = await api.createVerificationRun(state.project, state.id, request);
      sessionStorage.removeItem(storageKey); setPending(undefined); history.reload(); completed.reload();
      window.location.hash = navigationUrl({ ...state, view: "detail", run: result.run.id }).slice(1);
    } catch (issue) {
      setCreateError(issue);
      if (!(issue instanceof ApiError) || (issue.status > 0 && issue.status < 500 && issue.code !== "CONTRACT_ERROR")) { sessionStorage.removeItem(storageKey); setPending(undefined); }
    } finally { setCreating(false); }
  }
  return <section className="verification-panel" aria-labelledby="verification-heading"><h2 id="verification-heading">OCR &amp; Verification Runs</h2><p className="muted">실행할 때 현재 Expected Strings를 immutable snapshot으로 캡처합니다. 실행 이력은 이전 결과를 유지합니다.</p>
    <form className="editor run-form" aria-label="Create OCR verification run" onSubmit={event => submit(event)}><ErrorBox error={createError} /><fieldset disabled={creating || !!pending}><Field label="OCR profile" name="profile_id" error={createError}>{props => <select {...props} value={profileId} onChange={event => setProfileId(event.target.value)} required><option value="">선택</option>{profiles.data?.items.map(profile => <option key={profile.profile_id} value={profile.profile_id} disabled={profile.availability !== "AVAILABLE"}>{profile.profile_id} · {profile.availability === "AVAILABLE" ? profile.engine_name : `Unavailable (${profile.unavailable_code || "unknown"})`}</option>)}</select>}</Field><div className="threshold-grid"><Field label="Pass threshold (optional)" name="pass_threshold" error={createError}>{props => <input {...props} type="number" min="0" max="100" step="0.01" value={passThreshold} onChange={event => setPassThreshold(event.target.value)} placeholder="95" />}</Field><Field label="Review threshold (optional)" name="review_threshold" error={createError}>{props => <input {...props} type="number" min="0" max="100" step="0.01" value={reviewThreshold} onChange={event => setReviewThreshold(event.target.value)} placeholder="85" />}</Field></div><button className="primary" type="submit" disabled={!availableProfiles.length}>{creating ? "요청 중…" : "새 OCR 실행"}</button></fieldset>
      {pending && <div className="notice" role="alert"><p>결과가 확정되지 않은 요청이 저장되어 있습니다. 같은 Client Run ID로만 재시도합니다.</p><code>{pending.client_run_id}</code><button type="button" disabled={creating} onClick={event => submit(event as unknown as FormEvent, true)}>같은 요청 재시도</button></div>}
    </form>
    <ErrorBox error={profiles.error} retry={profiles.reload} />{profiles.loading && <Loading />}{profiles.data && !profiles.data.items.length && <Empty>등록된 OCR profile이 없습니다.</Empty>}
    <section><h3>Latest Completed Run</h3><ErrorBox error={completed.error} retry={completed.reload} />{completed.loading && <Loading />}{completed.data && (completed.data.items[0] ? <LatestCompleted state={state} run={completed.data.items[0]} /> : <Empty>완료된 실행이 없습니다.</Empty>)}</section>
    <section><h3>Run History</h3><ErrorBox error={history.error} retry={history.reload} />{history.loading && <Loading />}{history.data && <>{history.data.items.length ? <div className="table-wrap"><table><thead><tr><th>Requested</th><th>Run</th><th>Processing</th><th>Stage</th><th>Quality</th><th>Profile</th></tr></thead><tbody>{history.data.items.map((run: RunSummary) => <tr key={run.id} aria-current={run.id === selected ? "true" : undefined}><td>{run.created_at}</td><td><a href={navigationUrl({ ...state, view: "detail", run: run.id })}>{run.id}</a></td><td><StatusBadge value={run.status} kind="processing" /></td><td>{known(run.stage, stages)}</td><td><StatusBadge value={run.verification_status} kind="quality" /></td><td>{run.profile_id}</td></tr>)}</tbody></table></div> : <Empty>요청된 실행이 없습니다.</Empty>}<PageControls page={history.data} offset={historyOffset} setOffset={setHistoryOffset} /></>}</section>
    {selected && <RunDetail key={selected} project={state.project} screenshot={state.id} runId={selected} />}
  </section>;
}
export function ScreenshotDetail({ state, options, selectedRunId = state.run }: { state: Navigation; options: Options; selectedRunId?: string }) {
  const data = useRequest(`detail/${state.project}/${state.id}`, signal => api.screenshot(state.project, state.id, signal));
  const expected = useRequest(`detail-expected/${state.project}/${state.id}`, signal => api.screenshotExpected(state.project, state.id, signal));
  const label = (key: string, id: string) => options[key]?.find(item => item.id === id)?.label || id;
  return <section><div className="toolbar"><a href={navigationUrl({ ...state, view: "screenshots", id: "" })}>← Screenshot List</a><button onClick={() => { data.reload(); expected.reload(); }}>새로고침</button></div><ErrorBox error={data.error} retry={data.reload} />
    {data.loading && <Loading />}{data.data && <><h2>{data.data.original_filename}</h2><dl className="metadata">{[
      ["Project", label("project_id", data.data.project_id)], ["Build", label("build_id", data.data.build_id)], ["Locale", label("locale_id", data.data.locale_id)], ["Category", label("category_id", data.data.category_id)], ["Situation", label("situation_id", data.data.situation_id)], ["Source", data.data.source], ["Uploaded Time (UTC)", data.data.uploaded_at], ["Size", `${data.data.width} × ${data.data.height} · ${data.data.size_bytes.toLocaleString()} bytes`], ["Screenshot ID", data.data.id],
    ].map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl><dl className="metadata upload-metadata">{data.data.client_upload_id !== null && <div><dt>Client Upload ID</dt><dd>{data.data.client_upload_id}</dd></div>}<div><dt>Metadata Version</dt><dd>{data.data.metadata_version}</dd></div></dl><section className="metadata-json-panel" aria-labelledby="capture-metadata-heading"><h3 id="capture-metadata-heading">Capture Metadata</h3><pre className="metadata-json"><code>{formatMetadata(data.data.metadata)}</code></pre></section><ScreenshotImage key={data.data.id} screenshot={data.data} /></>}
    <section aria-labelledby="current-expected-heading"><h2 id="current-expected-heading">Current Expected Strings</h2><p className="muted">현재 카탈로그입니다. 아래의 실행별 immutable snapshot과 별개입니다.</p><ErrorBox error={expected.error} retry={expected.reload} />{expected.loading && <Loading />}{expected.data && <ExpectedTable data={expected.data} />}</section>
    <VerificationRuns state={state} selectedRunId={selectedRunId} />
  </section>;
}
