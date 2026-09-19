// CodeMirror 5 loader (CDN with pinned local fallback) and a small wrapper
// that gives every widget the same compact, auto-growing Python editor.

const CODEMIRROR_VERSION = "5.65.16";
const CDN_BASE = `https://cdn.jsdelivr.net/npm/codemirror@${CODEMIRROR_VERSION}/`;
const LOCAL_BASE = new URL("../vendor/codemirror/", import.meta.url).href;
const FORCE_LOCAL = new URLSearchParams(location.search).has("localAssets");

const SCRIPTS = [
  "lib/codemirror.js",
  "mode/python/python.js",
  "addon/edit/matchbrackets.js",
  "addon/edit/closebrackets.js",
  "addon/comment/comment.js",
];
const STYLES = ["lib/codemirror.css"];

let loadPromise = null;

export function loadCodeMirror() {
  if (!loadPromise) {
    loadPromise = (async () => {
      for (const path of STYLES) loadStyleWithFallback(path);
      for (const path of SCRIPTS) await loadWithFallback(path);
      return window.CodeMirror;
    })();
  }
  return loadPromise;
}

function loadStyleWithFallback(path) {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = FORCE_LOCAL ? LOCAL_BASE + path : CDN_BASE + path;
  if (!FORCE_LOCAL) link.onerror = () => { link.onerror = null; link.href = LOCAL_BASE + path; };
  document.head.append(link);
}

async function loadWithFallback(path) {
  if (!FORCE_LOCAL) {
    try {
      await loadScript(CDN_BASE + path);
      return;
    } catch {
      // Continue with the local pinned asset below.
    }
  }
  await loadScript(LOCAL_BASE + path);
}

function loadScript(source) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = source;
    script.onload = resolve;
    script.onerror = () => reject(new Error(`Could not load ${source}`));
    document.head.append(script);
  });
}

/**
 * Create an editor inside `host`. Options: value, readOnly, minLines,
 * maxLines (null = unlimited), onChange(value).
 * Returns { cm, getValue, setValue, setReadOnly, setMaxLines, markErrorLine, clearErrorLine, focus }.
 */
export async function createEditor(host, { value = "", readOnly = false, minLines = 3, maxLines = 16, onChange } = {}) {
  const CodeMirror = await loadCodeMirror();
  host.classList.add("wb-editor");
  const cm = CodeMirror(host, {
    value,
    mode: "python",
    theme: "workbook",
    lineNumbers: true,
    indentUnit: 4,
    tabSize: 4,
    indentWithTabs: false,
    matchBrackets: true,
    autoCloseBrackets: true,
    viewportMargin: Infinity,
    readOnly,
    extraKeys: {
      Tab: (editor) => editor.somethingSelected() ? editor.indentSelection("add") : editor.replaceSelection("    ", "end"),
      "Shift-Tab": (editor) => editor.indentSelection("subtract"),
      // Comment or uncomment the current line, or every selected line.
      "Cmd-/": "toggleComment",
      "Ctrl-/": "toggleComment",
    },
  });
  const api = {
    cm,
    getValue: () => cm.getValue(),
    setValue: (text) => { cm.setValue(text); cm.clearHistory(); },
    setReadOnly: (flag) => cm.setOption("readOnly", flag),
    setMaxLines: (lines) => applySize(host, minLines, lines),
    markErrorLine: (line) => {
      api.clearErrorLine();
      if (line >= 1 && line <= cm.lineCount()) {
        cm.addLineClass(line - 1, "background", "wb-error-line");
        api.errorLine = line - 1;
      }
    },
    clearErrorLine: () => {
      if (api.errorLine != null) cm.removeLineClass(api.errorLine, "background", "wb-error-line");
      api.errorLine = null;
    },
    focus: () => cm.focus(),
    refresh: () => cm.refresh(),
  };
  applySize(host, minLines, maxLines);
  if (onChange) cm.on("change", () => onChange(cm.getValue()));
  cm.on("change", () => api.clearErrorLine());
  return api;
}

function applySize(host, minLines, maxLines) {
  host.style.setProperty("--wb-editor-min-lines", String(minLines));
  host.style.setProperty("--wb-editor-max-lines", maxLines == null ? "9999" : String(maxLines));
}
