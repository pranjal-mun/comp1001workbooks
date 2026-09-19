// Light / dark theme: dark until the student picks one with the toggle, then
// the choice is remembered for every page on the site.

const KEY = "pylab-workbooks:theme";
const DEFAULT = "dark";

export function initTheme() {
  apply(saved() ?? DEFAULT);
  document.addEventListener("wb:toggle-theme", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    try { localStorage.setItem(KEY, next); } catch { /* ignore */ }
    apply(next);
  });
}

function saved() {
  try { return localStorage.getItem(KEY); } catch { return null; }
}

function apply(theme) {
  document.documentElement.dataset.theme = theme;
}
