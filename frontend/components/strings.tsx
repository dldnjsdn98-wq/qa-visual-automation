"use client";
import { useState } from "react";
import { api, ApiError } from "../lib/api";
import type { Navigation } from "../lib/navigation";
import type { ExpectedMapping, StringEntry } from "../lib/types";
import { Catalog, Editor, type Options } from "./catalog";
import { Empty, ErrorBox, ExpectedTable, Field, Loading, TextValue, useRequest } from "./common";

function MappingEditor({ initial, project, changed }: { initial: ExpectedMapping; project: string; changed: () => void }) {
  const [text, setText] = useState(initial.items.map(item => item.string_id).join("\n"));
  const [error, setError] = useState<unknown>(); const [busy, setBusy] = useState(false); const [confirm, setConfirm] = useState(false); const [saved, setSaved] = useState(false);
  async function save() {
    setError(undefined); setBusy(true);
    try {
      const ids = text.split(/\r?\n/).map(id => id.trim()).filter(Boolean);
      if (ids.length > 1000 || new Set(ids).size !== ids.length) throw new ApiError(422, "VALIDATION_ERROR", "중복 없이 최대 1,000개의 String ID를 지정하세요.");
      await api.setMapping(project, initial.situation_id, initial.build_id, ids);
      setConfirm(false); setSaved(true); changed();
    } catch (issue) { setError(issue); } finally { setBusy(false); }
  }
  return <section className="editor"><h2>Expected String ID 지정</h2><p>먼저 String Keys에 ID를 등록하세요. 한 줄에 하나씩 입력한 순서로 이 Build / Situation의 전체 목록을 교체합니다. 빈 목록은 연결을 모두 해제합니다.</p>
    <ErrorBox error={error} /><Field label="String IDs (순서대로)" name="string_ids" error={error}>{props => <textarea {...props} rows={7} value={text} disabled={busy} onChange={e => { setText(e.target.value); setConfirm(false); setSaved(false); }} />}</Field>
    {saved && <p role="status">목록을 저장했습니다.</p>}
    {confirm ? <div className="confirm"><p>이 Build / Situation의 전체 연결을 교체하시겠습니까?</p><button disabled={busy} onClick={save}>{busy ? "저장 중…" : "교체 확인"}</button><button disabled={busy} onClick={() => setConfirm(false)}>취소</button></div> : <button onClick={() => setConfirm(true)}>목록 교체</button>}
  </section>;
}
function SituationTranslations({ state, options, revision, changed }: { state: Navigation; options: Options; revision: number; changed: () => void }) {
  const { project, build, locale, situation } = state;
  const data = useRequest(`${project}/${build}/${locale}/${situation}/${revision}`, signal => api.expected(project, situation, build, locale, signal));
  const [search, setSearch] = useState("");
  const [edit, setEdit] = useState<{ id: string; text: string | null; entry: string | null } | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null); const [busy, setBusy] = useState(false); const [error, setError] = useState<unknown>();
  const label = (key: string, id: string) => options[key]?.find(item => item.id === id)?.label || id;
  async function remove() { if (!deleteId) return; setBusy(true); setError(undefined); try { await api.remove("strings", project, deleteId); setDeleteId(null); changed(); } catch (issue) { setError(issue); } finally { setBusy(false); } }
  const rows = data.data?.items.filter(item => `${item.string_id}\n${item.text ?? ""}`.toLocaleLowerCase().includes(search.toLocaleLowerCase())) || [];
  return <section><p>선택한 Situation의 현재 Expected Strings입니다. 누락된 번역을 등록하거나 기존 번역을 수정할 수 있습니다.</p>
    <Field label="String ID / Text 검색" name="search">{props => <input {...props} type="search" value={search} onChange={e => setSearch(e.target.value)} />}</Field>
    {edit && <Editor key={edit.id} kind="strings" project={project} options={options} defaults={{ build_id: build, locale_id: locale, string_id: edit.id }} row={edit.entry ? { id: edit.entry, build_id: build, locale_id: locale, string_id: edit.id, text: edit.text!, project_id: project, string_key_id: "", created_at: "", updated_at: "" } as StringEntry : undefined} onSaved={() => { setEdit(null); changed(); }} onCancel={() => setEdit(null)} />}
    <ErrorBox error={data.error} retry={data.reload} /><ErrorBox error={error} />
    {deleteId && <div className="confirm" role="alertdialog" aria-label="번역 삭제 확인"><p>번역을 삭제하면 Expected String은 번역 누락으로 표시됩니다.</p><button disabled={busy} onClick={remove}>삭제 확인</button><button disabled={busy} onClick={() => setDeleteId(null)}>취소</button></div>}
    {data.loading ? <Loading /> : data.data && <><p className="muted">현재 카탈로그 · {data.data.total}개 · 번역 누락 {data.data.missing_count}개</p>{rows.length ? <div className="table-wrap"><table><thead><tr><th>String ID</th><th>Situation</th><th>Locale</th><th>Text</th><th>작업</th></tr></thead><tbody>{rows.map(item => <tr key={item.string_key_id}><td><code>{item.string_id}</code></td><td>{label("situation_id", situation)}</td><td>{label("locale_id", locale)}</td><td><TextValue text={item.text} /></td><td><button onClick={() => setEdit({ id: item.string_id, text: item.text, entry: item.entry_id })}>{item.entry_id ? "수정" : "번역 등록"}</button>{item.entry_id && <button onClick={() => setDeleteId(item.entry_id)}>삭제</button>}</td></tr>)}</tbody></table></div> : <Empty>일치하는 Expected String이 없습니다. Expected 설정에서 ID를 지정하세요.</Empty>}</>}
  </section>;
}
export function Strings({ state, options, revision, changed }: { state: Navigation; options: Options; revision: number; changed: () => void }) {
  const [tab, setTab] = useState("translations"); const [stringId, setStringId] = useState(""); const [filter, setFilter] = useState("");
  const { project, build, locale, situation } = state;
  const mapping = useRequest(tab === "expected" && build && situation ? `mapping/${project}/${build}/${situation}/${revision}` : null, signal => api.mapping(project, situation, build, signal));
  const expected = useRequest(tab === "expected" && build && situation && locale ? `expected/${project}/${build}/${situation}/${locale}/${revision}` : null, signal => api.expected(project, situation, build, locale, signal));
  return <><div className="tabs" aria-label="Strings 보기">{[["translations", "Translations"], ["keys", "String Keys"], ["expected", "Expected 설정"]].map(([value, label]) => <button key={value} aria-pressed={tab === value} onClick={() => setTab(value)}>{label}</button>)}</div>
    {tab === "keys" && <><p>프로젝트의 고유 String ID를 등록한 뒤 Build / Locale별 번역을 추가하세요.</p><Catalog key={`keys/${project}`} kind="string-keys" project={project} options={options} revision={revision} onChanged={changed} /></>}
    {tab === "translations" && <>{situation ? (!build || !locale ? <Empty>Situation별 문자열을 보려면 Build와 Locale을 선택하세요.</Empty> : <SituationTranslations key={`${project}/${build}/${locale}/${situation}`} state={state} options={options} revision={revision} changed={changed} />) : <><p className="muted">전체 번역 목록입니다. 상단에서 Situation을 선택하면 해당 Situation의 문자열과 누락 번역을 확인할 수 있습니다.</p><form className="toolbar" onSubmit={e => { e.preventDefault(); setFilter(stringId); }}><Field label="String ID 정확히 검색 (전체 페이지)" name="string_id">{props => <input {...props} value={stringId} onChange={e => setStringId(e.target.value)} />}</Field><button>적용</button><button type="button" onClick={() => { setStringId(""); setFilter(""); }}>초기화</button></form><Catalog key={`${project}/${build}/${locale}/${filter}`} kind="strings" project={project} query={{ build_id: build, locale_id: locale, string_id: filter }} options={options} defaults={{ build_id: build, locale_id: locale }} revision={revision} onChanged={changed} /></>}</>}
    {tab === "expected" && <>{!build || !situation ? <Empty>Build와 Situation을 선택하세요.</Empty> : <><ErrorBox error={mapping.error} retry={mapping.reload} />{mapping.loading && <Loading />}{mapping.data && <MappingEditor key={`${project}/${build}/${situation}`} initial={mapping.data} project={project} changed={changed} />}{!locale ? <Empty>Locale을 선택하면 번역 미리보기를 표시합니다.</Empty> : <><ErrorBox error={expected.error} retry={expected.reload} />{expected.loading && <Loading />}{expected.data && <ExpectedTable data={expected.data} />}</>}</>}</>}
  </>;
}
