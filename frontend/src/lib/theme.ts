export type Theme = "light" | "dark";

/** Applies a theme to the whole document and remembers it so the next page load paints correctly. */
export function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem("theme", theme); } catch { /* storage can be blocked */ }
}
