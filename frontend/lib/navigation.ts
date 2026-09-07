export const views = ["dashboard", "projects", "builds", "locales", "categories", "situations", "strings", "screenshots", "upload", "detail"] as const;
export type View = typeof views[number];
export interface Navigation { view: View; project: string; build: string; locale: string; category: string; situation: string; id: string }
export const initialNavigation: Navigation = { view: "dashboard", project: "", build: "", locale: "", category: "", situation: "", id: "" };
export function parseNavigation(hash: string): Navigation {
  const [path, query] = hash.replace(/^#\/?/, "").split("?"); const params = new URLSearchParams(query);
  return { view: views.includes(path as View) ? path as View : "dashboard", ...Object.fromEntries(["project", "build", "locale", "category", "situation", "id"].map(key => [key, params.get(key) || ""])) } as Navigation;
}
export function navigationUrl(state: Navigation): string { const params = new URLSearchParams(Object.entries(state).filter(([key, value]) => key !== "view" && value)); return `#/${state.view}${params.size ? `?${params}` : ""}`; }
export function changeSelection(state: Navigation, field: "project" | "build" | "locale" | "category" | "situation", value: string): Navigation {
  if (field === "project") return { ...initialNavigation, view: state.view === "detail" ? "screenshots" : state.view, project: value };
  return { ...state, [field]: value, ...(field === "category" ? { situation: "" } : {}), id: "", view: state.view === "detail" ? "screenshots" : state.view };
}
