"use client";
import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { api, ApiError } from "../lib/api";
import type { Page, Resource, Resources } from "../lib/types";

export function useRequest<T>(key: string | null, loader: (signal: AbortSignal) => Promise<T>): { data?: T; error?: unknown; loading: boolean; reload: () => void } {
  const loaderRef = useRef(loader); loaderRef.current = loader;
  const [generation, refresh] = useState(0);
  const identity = key === null ? null : `${key}:${generation}`;
  const [state, setState] = useState<{ identity: string | null; data?: T; error?: unknown; loading: boolean }>({ identity: null, loading: false });
  useEffect(() => {
    if (identity === null) return;
    const controller = new AbortController();
    setState({ identity, loading: true });
    const currentLoader = loaderRef.current;
    void (async () => {
      try { const data = await currentLoader(controller.signal); if (!controller.signal.aborted) setState({ identity, data, loading: false }); }
      catch (error) { if (!controller.signal.aborted) setState({ identity, error, loading: false }); }
    })();
    return () => controller.abort();
  }, [identity]);
  return { ...(state.identity === identity ? state : { loading: identity !== null }), reload: () => refresh(value => value + 1) };
}
export function useLookup<K extends Resource>(resource: K, project: string, revision: number) {
  return useRequest<Resources[K][]>(resource === "projects" || project ? `${resource}/${project}/${revision}` : null, async signal => {
    const items: Resources[K][] = []; let offset = 0;
    do {
      const page = await api.list(resource, project, { limit: 100, offset }, signal);
      items.push(...page.items); offset += page.items.length;
      if (!page.items.length || offset >= page.total) break;
    } while (!signal.aborted);
    return items;
  });
}
export function ErrorBox({ error, retry }: { error?: unknown; retry?: () => void }) {
  if (!error) return null;
  const issue = error instanceof Error ? error : new Error("알 수 없는 오류입니다.");
  return <div role="alert" className="error"><strong>{issue.message}</strong>
    {error instanceof ApiError && <><div>{error.code}{error.requestId && <> · Request ID: <code>{error.requestId}</code></>}</div>
      {error.code === "RESOURCE_IN_USE" && <p>참조 중인 데이터가 있어 삭제할 수 없습니다. 연결된 문자열·매핑을 확인하세요. Screenshot이 참조하는 항목은 PHASE 1에서 삭제할 수 없습니다.</p>}
      {error.details.length > 0 && <ul>{error.details.map((detail, i) => <li key={i}><code>{detail.field || "request"}</code>: {detail.reason}</li>)}</ul>}</>}
    {retry && <button type="button" onClick={retry}>다시 불러오기</button>}
  </div>;
}
export function Loading() { return <p role="status" className="state">불러오는 중…</p>; }
export function Empty({ children = "표시할 데이터가 없습니다." }: { children?: ReactNode }) { return <p className="state">{children}</p>; }
export function Field({ label, name, error, children }: { label: string; name: string; error?: unknown; children: (props: { id: string; "aria-invalid": boolean; "aria-describedby"?: string }) => ReactNode }) {
  const id = useId();
  const messages = error instanceof ApiError ? error.details.filter(detail => [name, `body.${name}`, `metadata.${name}`].includes(detail.field || "")).map(detail => detail.reason) : [];
  return <div className="field"><label htmlFor={id}>{label}</label>{children({ id, "aria-invalid": messages.length > 0, "aria-describedby": messages.length ? `${id}-error` : undefined })}{messages.length > 0 && <span className="field-error" id={`${id}-error`}>{messages.join(" · ")}</span>}</div>;
}
export function Select({ label, value, onChange, items, required = false, disabled = false }: { label: string; value: string; onChange: (value: string) => void; items: { id: string; label: string }[]; required?: boolean; disabled?: boolean }) {
  return <Field label={label} name={label}>{props => <select {...props} value={value} onChange={e => onChange(e.target.value)} required={required} disabled={disabled}>
    <option value="">{required ? "선택하세요" : "전체 / 선택 안 함"}</option>
    {value && !items.some(item => item.id === value) && <option value={value}>{value} (확인 필요)</option>}
    {items.map(item => <option key={item.id} value={item.id}>{item.label}</option>)}
  </select>}</Field>;
}
export function Pager({ page, onChange }: { page: Page<unknown>; onChange: (offset: number) => void }) {
  return <div className="pager"><span>전체 {page.total.toLocaleString()}건 · {page.total ? page.offset + 1 : 0}–{page.offset + page.items.length}</span><button disabled={page.offset === 0} onClick={() => onChange(Math.max(0, page.offset - page.limit))}>이전</button><button disabled={page.offset + page.limit >= page.total} onClick={() => onChange(page.offset + page.limit)}>다음</button></div>;
}
export function TextValue({ text }: { text: string | null }) { return text === null ? <span className="missing">번역 누락</span> : text === "" ? <span className="muted">빈 문자열 (등록됨)</span> : <span className="translation" dir="auto">{text}</span>; }
export function ExpectedTable({ data }: { data: import("../lib/types").ExpectedStrings }) {
  return <section><h2>Expected Strings</h2><p className="muted">현재 Build 카탈로그 · {data.total}개 · 번역 누락 {data.missing_count}개. 업로드 당시의 스냅샷이 아닙니다.</p>
    {!data.items.length ? <Empty>이 Build / Situation에 지정된 String ID가 없습니다.</Empty> : <div className="table-wrap"><table><thead><tr><th>순서</th><th>String ID</th><th>Text</th><th>번역 상태</th></tr></thead><tbody>{data.items.map(item => <tr key={item.string_key_id}><td>{item.position + 1}</td><td><code>{item.string_id}</code></td><td><TextValue text={item.text} /></td><td>{item.translation_status === "missing" ? "누락" : "등록됨"}</td></tr>)}</tbody></table></div>}
  </section>;
}
