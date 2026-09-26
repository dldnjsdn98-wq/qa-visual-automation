export const views = ["dashboard", "projects", "builds", "locales", "categories", "situations", "strings", "screenshots", "upload", "detail"] as const;
export type View = typeof views[number];
export interface Navigation {
  view: View;
  project: string;
  build: string;
  locale: string;
  category: string;
  situation: string;
  id: string;
  run: string;
}
export const initialNavigation: Navigation = { view: "dashboard", project: "", build: "", locale: "", category: "", situation: "", id: "", run: "" };
const parentSelectionKeys = ["project", "build", "locale", "category", "situation", "id"] as const;

export function parseNavigation(hash: string): Navigation {
  const [path, query] = hash.replace(/^#\/?/, "").split("?");
  const params = new URLSearchParams(query);
  const view = views.includes(path as View) ? path as View : "dashboard";
  const state = { view, ...Object.fromEntries([...parentSelectionKeys, "run"].map(key => [key, params.get(key) || ""])) } as Navigation;
  if (state.view !== "detail" || !state.project || !state.id) state.run = "";
  return state;
}
export function navigationUrl(state: Navigation): string {
  const entries = Object.entries(state).filter(([key, value]) => key !== "view" && value && (key !== "run" || (state.view === "detail" && state.project && state.id)));
  const params = new URLSearchParams(entries);
  return `#/${state.view}${params.size ? `?${params}` : ""}`;
}
export function navigationTransition(current: Navigation, next: Navigation): Navigation {
  return parentSelectionKeys.some(key => current[key] !== next[key]) ? { ...next, run: "" } : next;
}
export function changeSelection(state: Navigation, field: "project" | "build" | "locale" | "category" | "situation", value: string): Navigation {
  if (field === "project") return navigationTransition(state, { ...initialNavigation, view: state.view === "detail" ? "screenshots" : state.view, project: value });
  return navigationTransition(state, { ...state, [field]: value, ...(field === "category" ? { situation: "" } : {}), id: "", view: state.view === "detail" ? "screenshots" : state.view });
}
export function changeScreenshot(state: Navigation, id: string): Navigation { return navigationTransition(state, { ...state, view: "detail", id }); }
