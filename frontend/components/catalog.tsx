"use client";
import { useState, type FormEvent } from "react";
import { api, ApiError, changedPatch, scalarLength, validateUnicode } from "../lib/api";
import type { Creates, Patches, Query, Resource, Resources } from "../lib/types";
import { Empty, ErrorBox, Field, Loading, Pager, TextValue, useRequest } from "./common";

interface FieldDefinition { key: string; label: string; immutable?: boolean; optional?: boolean; multiline?: boolean; max?: number; pattern?: string }
const slug = { key: "slug", label: "Slug", immutable: true, pattern: "[a-z0-9]+(?:-[a-z0-9]+)*", max: 64 };
const name = { key: "name", label: "Name", max: 120 };
const description = { key: "description", label: "Description", optional: true, multiline: true, max: 2000 };
const stringId = { key: "string_id", label: "String ID", immutable: true, pattern: "[A-Za-z0-9][A-Za-z0-9_.-]*", max: 128 };
export const definitions: Record<Resource, FieldDefinition[]> = {
  projects: [slug, name, description], builds: [{ key: "label", label: "Build Label", immutable: true, max: 120 }, description],
  locales: [{ key: "code", label: "Locale Code", immutable: true, max: 63 }, name], categories: [slug, name],
  situations: [{ key: "category_id", label: "Category", immutable: true }, slug, name, description],
  "string-keys": [stringId, description], strings: [{ key: "build_id", label: "Build", immutable: true }, { key: "locale_id", label: "Locale", immutable: true }, stringId, { key: "text", label: "Text", multiline: true, max: 10000 }],
};
export type Options = Record<string, { id: string; label: string }[]>;
export function Editor({ kind, project, row, defaults = {}, options, onSaved, onCancel }: { kind: Resource; project: string; row?: Resources[Resource]; defaults?: Record<string, string>; options: Options; onSaved: () => void; onCancel: () => void }) {
  const original = row ? { ...row } as Record<string, unknown> : {};
  const [values, setValues] = useState<Record<string, string | null>>(() => Object.fromEntries(definitions[kind].map(field => [field.key, (original[field.key] as string | null | undefined) ?? defaults[field.key] ?? (field.optional ? null : "")])));
  const [error, setError] = useState<unknown>(); const [busy, setBusy] = useState(false);
  const update = (key: string, value: string | null) => setValues(previous => ({ ...previous, [key]: value }));
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(undefined);
    try {
      validateUnicode(values);
      for (const field of definitions[kind]) {
        if (row && field.immutable) continue;
        const value = values[field.key];
        const problem = value !== null && field.max && scalarLength(field.key === "name" || field.key === "label" ? value.trim() : value) > field.max ? `${field.max} Unicode 문자 이하여야 합니다.` : !field.optional && field.key !== "text" && !value?.trim() ? "필수 입력입니다." : null;
        if (problem) throw new ApiError(422, "VALIDATION_ERROR", "입력값을 확인해 주세요.", [{ field: `body.${field.key}`, reason: problem }]);
      }
      const body = row ? changedPatch(original, values, definitions[kind].filter(field => !field.immutable).map(field => field.key)) : Object.fromEntries(Object.entries(values).filter(([, value]) => value !== null));
      if (row && !Object.keys(body).length) { onCancel(); return; }
      setBusy(true);
      if (row) await api.patch(kind, project, row.id, body as Patches[Resource]);
      else await api.create(kind, project, body as Creates[Resource]);
      onSaved();
    } catch (issue) { setError(issue); } finally { setBusy(false); }
  }
  return <form onSubmit={submit} className="editor" aria-label={row ? "항목 수정" : "항목 생성"}>
    <h2>{row ? "항목 수정" : "새 항목"}</h2><ErrorBox error={error} />
    <fieldset disabled={busy}><div className="form-grid">{definitions[kind].map(field => <div key={field.key}>
      <Field label={field.label + (row && field.immutable ? " (변경 불가)" : "")} name={field.key} error={error}>{props =>
        options[field.key] ? <select {...props} disabled={!!row && field.immutable} value={values[field.key] || ""} required onChange={e => update(field.key, e.target.value)}><option value="">선택하세요</option>{values[field.key] && !options[field.key].some(option => option.id === values[field.key]) && <option value={values[field.key]!}>{values[field.key]}</option>}{options[field.key].map(option => <option key={option.id} value={option.id}>{option.label}</option>)}</select>
        : field.multiline ? <textarea {...props} dir="auto" value={values[field.key] ?? ""} disabled={values[field.key] === null} rows={field.key === "text" ? 6 : 3} onChange={e => update(field.key, e.target.value)} />
        : <input {...props} value={values[field.key] ?? ""} readOnly={!!row && field.immutable} required={!field.optional} pattern={field.pattern} onChange={e => update(field.key, e.target.value)} />
      }</Field>
      {field.optional && <label className="check"><input type="checkbox" checked={values[field.key] === null} onChange={e => update(field.key, e.target.checked ? null : "")} />{row ? "설명 없음으로 변경 (null)" : "설명 없음"}</label>}
      {field.key === "text" && <small>공백·줄바꿈을 그대로 저장합니다. 빈 문자열도 등록할 수 있습니다.</small>}
    </div>)}</div><div className="actions"><button className="primary" type="submit">{busy ? "저장 중…" : "저장"}</button><button type="button" onClick={onCancel}>취소</button></div></fieldset>
  </form>;
}
export function Catalog({ kind, project, query = {}, options, revision, onChanged, onSelectProject, defaults = {} }: { kind: Resource; project: string; query?: Query; options: Options; revision: number; onChanged: () => void; onSelectProject?: (id: string) => void; defaults?: Record<string, string> }) {
  const [offset, setOffset] = useState(0); const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Resources[Resource] | "new" | null>(null);
  const [mutationError, setMutationError] = useState<unknown>(); const [deleting, setDeleting] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Resources[Resource] | null>(null);
  const [saved, setSaved] = useState(false);
  const data = useRequest(`${kind}/${project}/${JSON.stringify(query)}/${offset}/${revision}`, signal => api.list(kind, project, { ...query, offset, limit: 50 }, signal));
  const rows = data.data?.items.filter(row => Object.values(row).some(value => typeof value === "string" && value.toLocaleLowerCase().includes(search.toLocaleLowerCase()))) || [];
  async function remove() {
    if (!pendingDelete) return; setDeleting(true); setMutationError(undefined);
    try { await api.remove(kind, project, pendingDelete.id); setPendingDelete(null); setOffset(0); onChanged(); }
    catch (error) { setMutationError(error); } finally { setDeleting(false); }
  }
  const columns = definitions[kind];
  return <section><div className="toolbar"><Field label="현재 페이지 검색" name="search">{props => <input {...props} type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="이름 / ID / 텍스트" />}</Field><button className="primary" onClick={() => { setEditing("new"); setSaved(false); }}>새 항목</button><button onClick={data.reload}>새로고침</button></div>
    {saved && <p role="status">저장했습니다.</p>}
    {editing && <Editor key={editing === "new" ? "new" : editing.id} kind={kind} project={project} row={editing === "new" ? undefined : editing} defaults={defaults} options={options} onSaved={() => { setEditing(null); setSaved(true); onChanged(); }} onCancel={() => setEditing(null)} />}
    <ErrorBox error={data.error} retry={data.reload} /><ErrorBox error={mutationError} />
    {pendingDelete && <div className="confirm" role="alertdialog" aria-label="삭제 확인"><p><code>{pendingDelete.id}</code> 항목을 삭제하시겠습니까?</p><button disabled={deleting} onClick={remove}>{deleting ? "삭제 중…" : "삭제 확인"}</button><button disabled={deleting} onClick={() => { setPendingDelete(null); setMutationError(undefined); }}>취소</button></div>}
    {data.loading ? <Loading /> : data.data && <>{!rows.length ? <Empty>{search ? "현재 페이지에서 일치하는 항목이 없습니다. 다른 페이지도 확인하세요." : "데이터가 없습니다. 새 항목을 등록하세요."}</Empty> : <div className="table-wrap"><table><thead><tr>{columns.map(field => <th key={field.key}>{field.label}</th>)}<th>작업</th></tr></thead><tbody>{rows.map(row => <tr key={row.id}>{columns.map(field => { const value = (row as unknown as Record<string, string | null>)[field.key]; return <td key={field.key}>{field.key === "text" ? <TextValue text={value} /> : options[field.key]?.find(option => option.id === value)?.label || value || "—"}</td>; })}<td className="row-actions">{kind === "projects" && <button onClick={() => onSelectProject?.(row.id)}>선택</button>}<button onClick={() => setEditing(row)}>수정</button><button onClick={() => { setPendingDelete(row); setMutationError(undefined); }}>삭제</button></td></tr>)}</tbody></table></div>}<Pager page={data.data} onChange={setOffset} /></>}
  </section>;
}
