// Full-screen PyLab: a small multi-file Python project that runs in the
// browser on the shared runtime. input() is answered inline in the console.
//
// Boss mode (?boss=<workbookId>/<exerciseId>) turns the page into a single
// exercise from a workbook: the problem statement sits beside the editor
// (and can be hidden), Check runs the exercise's test cases, and the code is
// saved with that workbook's progress rather than the PyLab project, so each
// boss keeps its own draft and the regular project is untouched.

import { createEditor } from "../runtime/editor.js";
import { Console } from "../runtime/console.js";
import { runner, runInteractive, StoppedError, TimeoutError } from "../runtime/runner.js";
import { initTheme } from "../runtime/theme.js";
import { revealPage } from "../runtime/page.js";
import { decodeBase64, renderOutcome, describeRunFailure, toast } from "../runtime/components.js";
import { Progress } from "../runtime/progress.js";
import { xp } from "../runtime/xp.js";
import { runCases } from "../runtime/grader.js";
import { lectureFor, isOpen, fmtOpens } from "../runtime/schedule.js";
import { isInstructor, initInstructor } from "../runtime/instructor.js";

const STORAGE_KEY = "pylab-workbooks:lab-project";
const LAYOUT_KEY = "pylab-workbooks:lab-layout";
let showConsole = () => {}; // Set by setUpLayout: opens the console when it is folded away.
const LIMITS = { maxFiles: 20, maxFileBytes: 100 * 1024 };
const DEFAULT_PROJECT = { activeFile: "main.py", files: [{ name: "main.py", content: "" }] };

const $ = (selector) => document.querySelector(selector);
const els = {
  status: $("#runtime-status"), run: $("#run"), stop: $("#stop"), theme: $("#theme-toggle"),
  fileList: $("#file-list"), newFile: $("#new-file"), renameFile: $("#rename-file"), deleteFile: $("#delete-file"),
  resetProject: $("#reset-project"), activeName: $("#active-name"), copyFile: $("#copy-file"),
  clearOutput: $("#clear-output"), consolePanel: $(".lab-console-panel"), saveStatus: $("#save-status"),
  consoleSide: $("#console-side"), consoleHide: $("#console-hide"), consoleShow: $("#console-show"),
  workspace: $(".lab-workspace"), problem: $("#problem"), problemKind: $("#problem-kind"), problemBody: $("#problem-body"),
  showProblem: $("#show-problem"), hideProblem: $("#hide-problem"), resetBoss: $("#reset-boss"), answerBoss: $("#answer-boss"),
  check: $("#check"), results: $("#results"), xp: $("#xp"),
  main: $(".lab-main"), consoleGutter: $("#console-gutter"), problemGutter: $("#problem-gutter"),
  toggleComment: $("#toggle-comment"), nextBoss: $("#next-boss"),
  done: $("#done"), doneIcon: $("#done-icon"), doneText: $("#done-text"), doneActions: $("#done-actions"),
};

initTheme();
initInstructor();
els.theme.addEventListener("click", () => document.dispatchEvent(new CustomEvent("wb:toggle-theme")));

const boss = await loadBoss();
let project = loadProject();
let running = false;
let abort = null;
let saveTimer = null;
const out = new Console($("#console"));
const editor = await createEditor($("#editor"), { value: activeFile().content, minLines: 1, maxLines: null, onChange: onEdit });
editor.cm.setOption("extraKeys", { ...editor.cm.getOption("extraKeys"), "Ctrl-Enter": runProject, "Cmd-Enter": runProject });

if (boss) setUpBoss();
else loadFromHash();
renderFiles();
updateControls();
setUpLayout();
revealPage();

runner.onStatus((state, text) => {
  els.status.textContent = state === "ready" ? "Python ready" : text;
  els.status.dataset.state = state;
  updateControls();
});
runner.warmUp();

// ---------------------------------------------------------------- project

function loadProject() {
  if (boss) return bossProject();
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved && Array.isArray(saved.files) && saved.files.length) return saved;
  } catch { /* fall through */ }
  return structuredClone(DEFAULT_PROJECT);
}

function saveProject() {
  if (boss) {
    boss.progress.setWork(boss.exerciseId, project.files[0].content);
    els.saveStatus.textContent = "Saved in this browser";
    return;
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(project));
    els.saveStatus.textContent = "Saved in this browser";
  } catch {
    els.saveStatus.textContent = "Could not save (storage unavailable)";
  }
}

function scheduleSave() {
  clearTimeout(saveTimer);
  els.saveStatus.textContent = "Saving…";
  saveTimer = setTimeout(saveProject, 400);
}

function activeFile() {
  return project.files.find((file) => file.name === project.activeFile) ?? project.files[0];
}

function onEdit(value) {
  activeFile().content = value;
  scheduleSave();
}

/** Workbook "Open in PyLab" links pass code as #code=<base64>. */
function loadFromHash() {
  const match = location.hash.match(/^#code=(.+)$/);
  if (!match) return;
  let code;
  try { code = decodeBase64(decodeURIComponent(match[1])); } catch { return; }
  history.replaceState(null, "", location.pathname + location.search);
  const main = project.files.find((file) => file.name === "main.py");
  if (main && main.content.trim() && main.content !== code) {
    if (!window.confirm("Replace the code in main.py with the code from the workbook?")) return;
  }
  if (main) main.content = code;
  else project.files.unshift({ name: "main.py", content: code });
  project.activeFile = "main.py";
  editor.setValue(code);
  saveProject();
}

// ------------------------------------------------------------------ files

function renderFiles() {
  els.fileList.replaceChildren(...project.files.map((file) => {
    const item = document.createElement("li");
    item.classList.toggle("is-active", file.name === project.activeFile);
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = file.name;
    button.addEventListener("click", () => selectFile(file.name));
    item.append(button);
    return item;
  }));
  els.activeName.textContent = project.activeFile;
  els.deleteFile.disabled = project.files.length <= 1;
}

function selectFile(name) {
  if (name === project.activeFile) return;
  project.activeFile = name;
  editor.setValue(activeFile().content);
  renderFiles();
  saveProject();
  editor.focus();
}

function validateFilename(name, currentName = null) {
  if (!name || name.trim() !== name) return "Filenames cannot be empty or start or end with spaces.";
  if (name.length > 80) return "Filenames must be 80 characters or fewer.";
  if (!/^[A-Za-z0-9_.-]+$/.test(name) || name === "." || name === "..") return "Use only letters, numbers, underscores, hyphens and periods.";
  if (project.files.some((file) => file.name === name && file.name !== currentName)) return "A file with that name already exists.";
  return null;
}

function askFilename(message, initial) {
  for (;;) {
    const name = window.prompt(message, initial);
    if (name == null) return null;
    const error = validateFilename(name.trim(), initial);
    if (!error) return name.trim();
    window.alert(error);
  }
}

els.newFile.addEventListener("click", () => {
  if (project.files.length >= LIMITS.maxFiles) return window.alert(`Projects are limited to ${LIMITS.maxFiles} files.`);
  let number = 1, suggestion = "helpers.py";
  while (project.files.some((file) => file.name === suggestion)) suggestion = `module${++number}.py`;
  const name = askFilename("New file name:", suggestion);
  if (!name) return;
  project.files.push({ name, content: "" });
  project.activeFile = name;
  editor.setValue("");
  renderFiles();
  saveProject();
  editor.focus();
});

els.renameFile.addEventListener("click", () => {
  const file = activeFile();
  const name = askFilename("Rename file to:", file.name);
  if (!name || name === file.name) return;
  file.name = name;
  project.activeFile = name;
  renderFiles();
  saveProject();
});

els.deleteFile.addEventListener("click", () => {
  if (project.files.length <= 1) return;
  const file = activeFile();
  if (!window.confirm(`Delete ${file.name}? This cannot be undone.`)) return;
  project.files = project.files.filter((f) => f !== file);
  project.activeFile = project.files[0].name;
  editor.setValue(activeFile().content);
  renderFiles();
  saveProject();
});

els.resetProject.addEventListener("click", () => {
  if (!window.confirm("Delete every file and start again with an empty main.py?")) return;
  project = structuredClone(DEFAULT_PROJECT);
  editor.setValue("");
  out.clear();
  renderFiles();
  saveProject();
});

els.toggleComment.addEventListener("click", () => {
  editor.cm.execCommand("toggleComment");
  editor.focus();
});

els.copyFile.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(editor.getValue());
    els.copyFile.textContent = "Copied";
  } catch {
    els.copyFile.textContent = "Copy failed";
  }
  setTimeout(() => { els.copyFile.textContent = "Copy code"; }, 1200);
});

// -------------------------------------------------------------------- run

function updateControls() {
  const ready = runner.state === "ready";
  els.run.disabled = running || !ready || Boolean(boss?.locked);
  els.check.disabled = running || !ready || Boolean(boss?.locked);
  els.stop.disabled = !running;
}

function projectFiles() {
  return project.files.map((file) => ({ name: file.name, content: file.content }));
}

async function runProject() {
  if (running || runner.state !== "ready") return;
  const encoder = new TextEncoder();
  for (const file of project.files) {
    if (encoder.encode(file.content).byteLength > LIMITS.maxFileBytes) return window.alert(`${file.name} is larger than the 100 KB file limit.`);
  }
  const entry = project.files.some((file) => file.name === "main.py") ? "main.py" : project.activeFile;
  if (!entry.endsWith(".py")) return window.alert("Add a main.py, or select a .py file to run.");
  clearTimeout(saveTimer);
  saveProject();

  running = true;
  abort = new AbortController();
  els.consolePanel.classList.add("has-run");
  showConsole();
  showResults(false);
  out.clear();
  editor.clearErrorLine();
  updateControls();
  try {
    const result = await runInteractive({ files: projectFiles(), entry, console: out, signal: abort.signal });
    if (result.status === "error") {
      const line = result.stderr.match(/File "main\.py", line (\d+)/g)?.pop()?.match(/line (\d+)/)?.[1];
      if (line && entry === project.activeFile) editor.markErrorLine(Number(line));
    } else if (out.isEmpty) {
      out.note("(program finished with no output)");
    }
  } catch (error) {
    if (error instanceof StoppedError || error?.name === "AbortError") out.note((out.isEmpty ? "" : "\n") + "■ Stopped.");
    else if (error instanceof TimeoutError) out.error(`\n${error.message}`);
    else out.error(`\n${error.message ?? error}`);
  } finally {
    running = false;
    abort = null;
    updateControls();
  }
}

els.run.addEventListener("click", runProject);
els.check.addEventListener("click", checkBoss);
els.stop.addEventListener("click", () => {
  abort?.abort();
  runner.stop();
});
els.clearOutput.addEventListener("click", () => out.clear());

// ----------------------------------------------------------------- layout

/**
 * The console sits under the editor (or, after "Move right", beside it) and
 * the problem beside both; each has a drag handle. It starts hidden behind a
 * "Show console" tab, and Run and Check open it. Sizes, the side, and whether
 * it is open are kept in localStorage. Dragging never shrinks the console
 * below its CSS minimum, so it cannot vanish by accident.
 */
function setUpLayout() {
  let layout = {};
  try { layout = JSON.parse(localStorage.getItem(LAYOUT_KEY)) ?? {}; } catch { /* defaults */ }
  if (layout.consoleH > 0) els.workspace.style.setProperty("--console-h", `${layout.consoleH}px`);
  if (layout.consoleW > 0) els.workspace.style.setProperty("--console-w", `${layout.consoleW}px`);
  if (layout.problemW > 0) els.workspace.style.setProperty("--problem-w", `${layout.problemW}px`);
  const remember = (patch) => {
    Object.assign(layout, patch);
    try { localStorage.setItem(LAYOUT_KEY, JSON.stringify(layout)); } catch { /* not essential */ }
  };

  const onRight = () => els.workspace.classList.contains("console-right");
  const setSide = (side) => {
    const right = side === "right";
    els.workspace.classList.toggle("console-right", right);
    els.consoleGutter.setAttribute("aria-orientation", right ? "vertical" : "horizontal");
    els.consoleSide.textContent = right ? "Bottom" : "Right";
    els.consoleSide.title = right ? "Put the console under the editor" : "Put the console beside the editor";
    els.consoleShow.textContent = right ? "Show console ◂" : "Show console ▴";
    editor.cm.refresh();
  };
  const setOpen = (open) => {
    els.workspace.classList.toggle("console-closed", !open);
    editor.cm.refresh();
  };
  setSide(layout.consoleSide === "right" ? "right" : "bottom");
  setOpen(layout.consoleOpen === true);
  showConsole = () => { if (els.workspace.classList.contains("console-closed")) { setOpen(true); remember({ consoleOpen: true }); } };
  els.consoleSide.addEventListener("click", () => { const side = onRight() ? "bottom" : "right"; setSide(side); remember({ consoleSide: side }); });
  els.consoleHide.addEventListener("click", () => { setOpen(false); remember({ consoleOpen: false }); editor.focus(); });
  els.consoleShow.addEventListener("click", () => { setOpen(true); remember({ consoleOpen: true }); });

  dragGutter(els.consoleGutter, () => (onRight() ? "col" : "row"), (event) => {
    const box = els.main.getBoundingClientRect();
    if (onRight()) {
      const px = Math.round(box.right - event.clientX);
      els.workspace.style.setProperty("--console-w", `${px}px`);
      return { consoleW: px };
    }
    const px = Math.round(box.bottom - event.clientY);
    els.workspace.style.setProperty("--console-h", `${px}px`);
    return { consoleH: px };
  });
  dragGutter(els.problemGutter, "col", (event) => {
    const box = els.workspace.getBoundingClientRect();
    const px = Math.round(event.clientX - box.left);
    els.workspace.style.setProperty("--problem-w", `${px}px`);
    return { problemW: px };
  });

  function dragGutter(gutter, axisOf, apply) {
    gutter.addEventListener("pointerdown", (event) => {
      if (event.button !== 0) return;
      event.preventDefault();
      const axis = typeof axisOf === "function" ? axisOf() : axisOf;
      gutter.setPointerCapture(event.pointerId);
      gutter.classList.add("is-dragging");
      document.body.classList.add("is-dragging");
      document.body.classList.toggle("drag-col", axis === "col");
      let patch = null;
      const move = (e) => { patch = apply(e); editor.cm.refresh(); };
      const stop = () => {
        gutter.removeEventListener("pointermove", move);
        gutter.classList.remove("is-dragging");
        document.body.classList.remove("is-dragging", "drag-col");
        // Store what the panel actually got, after the CSS min and max limits.
        if (patch) {
          if (gutter === els.problemGutter) remember({ problemW: els.problem.offsetWidth });
          else remember(axis === "col" ? { consoleW: els.consolePanel.offsetWidth } : { consoleH: els.consolePanel.offsetHeight });
        }
        editor.cm.refresh();
      };
      gutter.addEventListener("pointermove", move);
      gutter.addEventListener("pointerup", stop, { once: true });
      gutter.addEventListener("pointercancel", stop, { once: true });
    });
  }
}

// ------------------------------------------------------------------- boss

/** Where a workbook's files live relative to this page. */
function workbookFolder(workbookId) {
  const m = /^(lecture-\d+)-boss$/.exec(workbookId);
  return m ? `../workbooks/${m[1]}/boss/` : `../workbooks/${workbookId}/`;
}

/**
 * Read ?boss=<workbookId>/<exerciseId>, fetch the exercise spec and the
 * problem statement (the page section from the exercise's heading up to
 * its widget), and set up progress for that workbook. Null when the page
 * is a plain PyLab session or the boss cannot be found.
 */
async function loadBoss() {
  const param = new URLSearchParams(location.search).get("boss");
  const m = /^([a-z0-9-]+)\/([a-z0-9-]+)$/i.exec(param ?? "");
  if (!m) return null;
  const [, workbookId, exerciseId] = m;
  const folder = workbookFolder(workbookId);
  let data, spec, statement = null, title = "";
  try {
    data = await (await fetch(`${folder}exercises.json`)).json();
    spec = data.exercises?.[exerciseId];
    if (!spec || spec.type !== "code") throw new Error("no such exercise");
  } catch {
    return null;
  }
  try {
    const html = await (await fetch(`${folder}index.html`)).text();
    const doc = new DOMParser().parseFromString(html, "text/html");
    const heading = doc.getElementById(exerciseId);
    if (heading && /^H[1-6]$/.test(heading.tagName)) {
      const frag = document.createDocumentFragment();
      title = heading.textContent.trim();
      for (let node = heading; node; node = node.nextElementSibling) {
        if (node.tagName === "WB-EXERCISE" || (node !== heading && /^H[1-2]$/.test(node.tagName))) break;
        frag.append(document.importNode(node, true));
      }
      statement = frag;
    }
  } catch { /* the editor still works without the statement */ }
  const entry = lectureFor(workbookId);
  const locked = Boolean(entry) && !isOpen(entry) && !isInstructor();
  // The bosses of this workbook in page order, so "next" means the one after this.
  const order = Object.entries(data.exercises).filter(([, s]) => s.type === "code").map(([id, s]) => ({ id, emoji: s.boss ?? "" }));
  return { workbookId, exerciseId, spec, statement, title, entry, locked, order, progress: new Progress(workbookId), workbookTitle: data.title ?? "" };
}

/** The next boss still standing, looking forward from this one and wrapping around; null once every boss is defeated. */
function nextBoss() {
  const index = boss.order.findIndex((b) => b.id === boss.exerciseId);
  const after = [...boss.order.slice(index + 1), ...boss.order.slice(0, index)];
  return after.find((b) => !boss.progress.get(b.id).passed) ?? null;
}

/** The lecture workbook a boss workbook belongs to, relative to this page. */
function lectureUrl(workbookId) {
  const m = /^(lecture-\d+)-boss$/.exec(workbookId);
  return m ? `../workbooks/${m[1]}/index.html` : `../workbooks/${workbookId}/index.html`;
}

function bossUrl(exerciseId) {
  return `./index.html?boss=${boss.workbookId}/${exerciseId}`;
}

function bossProject() {
  const record = boss.progress.get(boss.exerciseId);
  const work = boss.locked ? "" : (typeof record.work === "string" ? record.work : boss.spec.starter ?? "");
  return { activeFile: "main.py", files: [{ name: "main.py", content: work }, ...(boss.spec.files ?? []).filter((f) => f.name !== "main.py")] };
}

function setUpBoss() {
  const { spec, statement, title, locked } = boss;
  document.title = `${title || "Boss problem"} · PyLab`;
  els.workspace.classList.add("is-boss");
  els.problem.hidden = false;
  els.problemGutter.hidden = false;
  els.check.hidden = false;
  setProblemHidden(false);
  els.problemKind.textContent = boss.workbookTitle || "Boss problem";
  els.saveStatus.textContent = "Saved in this browser";

  els.hideProblem.addEventListener("click", () => setProblemHidden(true));
  els.showProblem.addEventListener("click", () => setProblemHidden(false));

  if (locked) {
    els.problemBody.replaceChildren(h("p", { class: "wb-locked-note" }, `This boss opens ${fmtOpens(boss.entry)}.`), h("p", {}, "Come back after the lecture before it has ended."));
    editor.setValue("");
    editor.setReadOnly(true);
    els.resetBoss.disabled = true;
    return;
  }
  if (statement) els.problemBody.replaceChildren(statement);
  else els.problemBody.replaceChildren(h("p", {}, "Solve the exercise in the editor, then press ✓ Check."));

  refreshBossState();
  boss.progress.subscribe(refreshBossState);
  xp.subscribe(refreshBossState);

  const replaceCode = (code) => {
    editor.setValue(code);
    project.files[0].content = code;
    saveProject();
    showResults(false);
    out.clear();
    editor.focus();
  };
  els.resetBoss.addEventListener("click", () => {
    if (!window.confirm("Put the starter code back? Your current code will be lost.")) return;
    replaceCode(spec.starter ?? "");
  });
  // Instructor mode: one click drops the model answer into the editor so the checker can be tried against it.
  if (isInstructor() && spec.answer) {
    els.answerBoss.hidden = false;
    els.answerBoss.addEventListener("click", () => replaceCode(decodeBase64(spec.answer)));
  }
}

function setProblemHidden(hidden) {
  els.workspace.classList.toggle("problem-hidden", hidden);
  els.showProblem.hidden = !hidden;
  els.showProblem.setAttribute("aria-expanded", String(!hidden));
  editor.cm.refresh();
}

function refreshBossState() {
  const record = boss.progress.get(boss.exerciseId);
  els.xp.hidden = false;
  els.xp.textContent = record.passed ? `Defeated · ${xp.balance} XP` : `${xp.balance} XP`;
  els.xp.classList.toggle("is-beaten", Boolean(record.passed));
  // Once this boss is defeated the top bar always offers the way on.
  els.nextBoss.hidden = !record.passed;
  const next = nextBoss();
  if (next) {
    els.nextBoss.href = bossUrl(next.id);
    els.nextBoss.textContent = `Next boss ${next.emoji} ▸`;
    els.nextBoss.title = "Open the next boss problem";
  } else {
    els.nextBoss.href = lectureUrl(boss.workbookId);
    els.nextBoss.textContent = "Back to the workbook ▸";
    els.nextBoss.title = "Every boss here is defeated: back to the lecture workbook";
  }
}

/** After a pass: say well done and offer the next boss, the workbook, or the landing page. */
function showDone(added) {
  const next = nextBoss();
  const defeated = boss.order.filter((b) => boss.progress.get(b.id).passed).length;
  const text = [];
  if (added) text.push(`+${added} XP.`);
  if (boss.order.length > 1) text.push(defeated === boss.order.length ? "Every boss in this workbook is defeated." : `Defeated ${defeated} of ${boss.order.length} bosses in this workbook.`);
  else text.push("Boss defeated.");
  els.doneIcon.textContent = boss.spec.boss ?? "🏆";
  els.doneText.textContent = text.join(" ");
  const link = (href, label, primary) => h("a", { class: `wb-btn ${primary ? "wb-btn-primary" : "wb-btn-quiet"}`, href }, ...[].concat(label));
  const stay = h("button", { class: "wb-btn wb-btn-quiet", type: "button" }, "Stay on this problem");
  stay.addEventListener("click", () => els.done.close());
  els.doneActions.replaceChildren(
    ...(next ? [link(bossUrl(next.id), ["Next boss ", h("span", { class: "lab-done-emoji" }, next.emoji), " ▸"], true)] : []),
    link(lectureUrl(boss.workbookId), "Back to the workbook", !next),
    link("../index.html", "All workbooks", false),
    stay,
  );
  els.done.showModal();
}

/** Show the test results in place of the console, or the console again. */
function showResults(on) {
  els.consolePanel.classList.toggle("is-checking", on);
  els.results.hidden = !on;
}

async function checkBoss() {
  if (!boss || running || runner.state !== "ready" || boss.locked) return;
  clearTimeout(saveTimer);
  saveProject();
  running = true;
  updateControls();
  editor.clearErrorLine();
  els.consolePanel.classList.add("has-run");
  showConsole();
  showResults(true);
  els.results.replaceChildren(h("div", { class: "wb-result-pending" }, "Checking…"));
  try {
    const outcome = await runCases(boss.spec, editor.getValue(), boss.spec.files ?? []);
    els.results.replaceChildren(...renderOutcome(outcome, { markErrorLine: (line) => editor.markErrorLine(line) }));
    if (outcome.pass) {
      const first = !boss.progress.get(boss.exerciseId).passed;
      boss.progress.markPassed(boss.exerciseId);
      const added = boss.progress.award(boss.exerciseId, boss.spec.xp ?? 5);
      if (added) toast(`+${added} XP`, "good");
      else if (first) toast("Boss defeated!", "good");
      showDone(added);
    }
  } catch (error) {
    els.results.replaceChildren(h("div", { class: "wb-result-case is-bad" }, h("div", { class: "wb-result-case-title" }, "✗ Could not check"), h("pre", { class: "wb-result-text" }, describeRunFailure(error))));
  } finally {
    running = false;
    updateControls();
  }
}

function h(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) if (value != null) node.setAttribute(key, value);
  node.append(...children);
  return node;
}
