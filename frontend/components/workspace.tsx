"use client";
import { useEffect, useState } from "react";
import { changeSelection, initialNavigation, navigationUrl, parseNavigation, type Navigation, type View } from "../lib/navigation";
import { Catalog, type Options } from "./catalog";
import { Empty, ErrorBox, Loading, Select, useLookup } from "./common";
import { Strings } from "./strings";
import { ScreenshotDetail, ScreenshotList, Upload } from "./screenshots";

const titles: Record<View, string> = { dashboard: "Dashboard", projects: "Projects", builds: "Builds", locales: "Locales", categories: "Categories", situations: "Situations", strings: "Strings", screenshots: "Screenshots", upload: "Screenshot Upload", detail: "Screenshot Detail" };
export default function Workspace() {
  const [state, setState] = useState<Navigation>(initialNavigation); const [revision, setRevision] = useState(0);
  useEffect(() => { const read = () => { if (window.location.hash !== "#main-content") setState(parseNavigation(window.location.hash)); }; read(); window.addEventListener("hashchange", read); return () => window.removeEventListener("hashchange", read); }, []);
  function go(next: Navigation) { setState(next); window.location.hash = navigationUrl(next); }
  const changed = () => setRevision(value => value + 1);
  const projects = useLookup("projects", "", revision); const builds = useLookup("builds", state.project, revision);
  const locales = useLookup("locales", state.project, revision); const categories = useLookup("categories", state.project, revision); const situations = useLookup("situations", state.project, revision);
  const options: Options = {
    project_id: projects.data?.map(item => ({ id: item.id, label: `${item.name} · ${item.slug}` })) || [],
    build_id: builds.data?.map(item => ({ id: item.id, label: item.label })) || [],
    locale_id: locales.data?.map(item => ({ id: item.id, label: `${item.code} · ${item.name}` })) || [],
    category_id: categories.data?.map(item => ({ id: item.id, label: `${item.name} · ${item.slug}` })) || [],
    situation_id: situations.data?.filter(item => !state.category || item.category_id === state.category).map(item => ({ id: item.id, label: `${item.name} · ${item.slug}` })) || [],
  };
  const scoped = !["dashboard", "projects"].includes(state.view);
  const needsFilters = ["strings", "screenshots", "upload"].includes(state.view);
  const selection = (key: "project" | "build" | "locale" | "category" | "situation", value: string) => go(changeSelection(state, key, value));
  const pageKey = `${state.view}/${state.project}/${state.build}/${state.locale}/${state.category}/${state.situation}/${state.id}`;
  const lookups = [builds, locales, categories, situations];
  return <div className="workspace"><a className="skip" href="#main-content">본문 바로가기</a><aside><div className="brand">GAME QA<span>Multilingual workspace</span></div><nav aria-label="주 메뉴">{(Object.keys(titles) as View[]).filter(view => view !== "detail").map(view => <a key={view} href={navigationUrl({ ...state, view, id: "" })} aria-current={state.view === view ? "page" : undefined}>{titles[view]}</a>)}</nav><p className="sidebar-note">PHASE 1 · 수동 검수</p></aside>
    <div className="content"><header><div><span className="eyebrow">GAME MULTILINGUAL QA</span><h1>{titles[state.view]}</h1></div><Select label="Project" value={state.project} onChange={value => selection("project", value)} items={options.project_id} disabled={projects.loading} /></header>
      <ErrorBox error={projects.error} retry={projects.reload} />{projects.loading && <Loading />}
      {state.project && <>{lookups.map((lookup, index) => <ErrorBox key={index} error={lookup.error} retry={lookup.reload} />)}{lookups.some(lookup => lookup.loading) && <p role="status" className="muted">프로젝트 선택 항목을 불러오는 중…</p>}</>}
      <main id="main-content" tabIndex={-1}>
        {needsFilters && state.project && <section className="filters" aria-label="데이터 필터">{(["build", "locale", "category", "situation"] as const).map(key => <Select key={key} label={key[0].toUpperCase() + key.slice(1)} value={state[key]} onChange={value => selection(key, value)} items={options[`${key}_id`]} required={state.view === "upload"} disabled={lookups.some(lookup => lookup.loading)} />)}<button onClick={() => go({ ...initialNavigation, view: state.view, project: state.project })}>필터 초기화</button></section>}
        {scoped && !state.project ? <Empty>상단에서 Project를 선택하거나 Projects에서 새로 만드세요.</Empty> : <div key={pageKey}>
          {state.view === "dashboard" && <><p>프로젝트별 다국어 문자열과 Screenshot을 한곳에서 검수합니다.</p><div className="dashboard-grid">{[["projects", "01", "Project 생성", "검수 대상 프로젝트를 선택합니다."], ["builds", "02", "카탈로그 준비", "Build, Locale, Category, Situation을 관리합니다."], ["strings", "03", "다국어 문자열", "String ID와 번역, Expected 목록을 등록합니다."], ["upload", "04", "Screenshot Upload", "원본 이미지와 검수 맥락을 연결합니다."], ["screenshots", "05", "Screenshot 검수", "필터로 찾고 이미지와 Expected Strings를 확인합니다."]].map(([view, step, title, text]) => <a key={view} href={navigationUrl({ ...state, view: view as View, id: "" })}><span className="step">{step}</span><h2>{title}</h2><p>{text}</p></a>)}</div>{projects.data && <p>등록된 프로젝트 {projects.data.length}개</p>}</>}
          {state.view === "projects" && <Catalog kind="projects" project="" options={options} revision={revision} onChanged={changed} onSelectProject={id => go({ ...initialNavigation, project: id, view: "builds" })} />}
          {(["builds", "locales", "categories", "situations"] as string[]).includes(state.view) && <Catalog kind={state.view as "builds" | "locales" | "categories" | "situations"} project={state.project} options={options} defaults={{ category_id: state.category }} revision={revision} onChanged={changed} />}
          {state.view === "strings" && <Strings state={state} options={options} revision={revision} changed={changed} />}
          {state.view === "screenshots" && <ScreenshotList state={state} options={options} revision={revision} />}
          {state.view === "upload" && <Upload state={state} go={go} changed={changed} />}
          {state.view === "detail" && <ScreenshotDetail state={state} options={{ ...options, situation_id: situations.data?.map(item => ({ id: item.id, label: `${item.name} · ${item.slug}` })) || [] }} />}
        </div>}
      </main>
    </div></div>;
}
