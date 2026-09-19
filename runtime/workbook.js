// Page bootstrap for a workbook: loads exercises.json, sets up progress and
// the widgets, and builds the sticky top bar (XP, progress, theme, backup)
// and the table of contents from the page's headings, and enables the
// classroom presentation mode (see present.js).
//
// A workbook page calls:
//   import { initWorkbook } from "../../runtime/workbook.js";
//   initWorkbook({ id: "lecture-04", specs: "./exercises.json" });

import { Progress } from "./progress.js";
import { xp } from "./xp.js";
import { runner } from "./runner.js";
import { defineComponents, toast, bossLabUrl } from "./components.js";
import { initTheme } from "./theme.js";
import { initPresentation } from "./present.js";
import { revealPage } from "./page.js";
import { lectureFor, isOpen, fmtOpens, workbookId, bossId } from "./schedule.js";
import { initInstructor, isInstructor, instructorBadge } from "./instructor.js";

const LOGO_URL = new URL("./img/mun-logo.svg", import.meta.url).href;
const HOME_URL = new URL("../index.html", import.meta.url).href;

/** `python: false` skips loading Python on pages with nothing to run (for example the setup guide). */
export async function initWorkbook({ id, specs: specsUrl = "./exercises.json", title, python = true }) {
  initTheme();
  initInstructor();
  const entry = lectureFor(id);
  if (entry && !isOpen(entry) && !isInstructor()) {
    renderLocked(entry);
    revealPage();
    return;
  }
  const response = await fetch(specsUrl);
  if (!response.ok) throw new Error(`Could not load ${specsUrl}: ${response.status}`);
  const data = await response.json();
  const specs = data.exercises ?? {};
  const progress = new Progress(id);
  const exerciseIds = [...document.querySelectorAll("wb-exercise[id], wb-table[id], wb-short[id]")].map((el) => el.id).filter((eid) => specs[eid]);

  defineComponents({ workbookId: id, specs, progress });
  buildTopBar({ id, title: title ?? data.title ?? document.title, short: data.short, subtitle: data.subtitle, progress, exerciseIds });
  buildContents(progress);
  renderBosses(id, entry);
  initPresentation();
  revealPage();
  if (python) runner.warmUp();
  // Widgets grow as they initialise, so a #section link needs a second jump.
  if (location.hash) setTimeout(() => document.getElementById(location.hash.slice(1))?.scrollIntoView(), 300);
}

// ------------------------------------------------------------- top bar

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : value);
  }
  node.append(...children.flat().filter(Boolean));
  return node;
}

/** What the top bar shows instead of the full title on a phone: "L02" for lecture-02; other pages set `short` in their spec file. */
function shortTitle(id, title) {
  const m = /^lecture-(\d+)$/.exec(id ?? "");
  return m ? `L${m[1].padStart(2, "0")}` : title;
}

function titleBlock(title, short, subtitle) {
  return el("div", { class: "wb-topbar-title" },
    el("strong", { class: "wb-topbar-title-full" }, title),
    el("strong", { class: "wb-topbar-title-short", "aria-hidden": "true" }, short),
    subtitle ? el("span", {}, subtitle) : null);
}

function buildTopBar({ id, title, short, subtitle, progress, exerciseIds }) {
  const xpValue = el("span", { class: "wb-topbar-xp-value" }, "0");
  const xpBadge = el("span", { class: "wb-topbar-xp", title: "XP: earn by answering correctly, spend to see answers" }, xpValue, " XP");
  xp.subscribe((balance, change) => {
    xpValue.textContent = String(balance);
    if (change) {
      xpBadge.classList.remove("is-bump");
      void xpBadge.offsetWidth;
      xpBadge.classList.add("is-bump");
    }
  });

  const bar = el("span", { class: "wb-progress-fill" });
  const label = el("span", { class: "wb-progress-label" });
  const progressBox = el("span", { class: "wb-progress", role: "progressbar", "aria-valuemin": "0", "aria-valuemax": String(exerciseIds.length) },
    el("span", { class: "wb-progress-track" }, bar), label);
  progress.subscribe((p) => {
    const { done, total } = p.summary(exerciseIds);
    bar.style.width = total ? `${(100 * done) / total}%` : "0%";
    label.textContent = `${done} / ${total} done`;
    progressBox.setAttribute("aria-valuenow", String(done));
  });

  const status = el("span", { class: "wb-topbar-status" });
  runner.onStatus((state, text) => {
    status.textContent = state === "ready" || state === "idle" ? "" : text;
    status.dataset.state = state;
  });

  const menu = el("details", { class: "wb-menu" },
    el("summary", { class: "wb-btn wb-btn-quiet" }, "⋯"),
    el("div", { class: "wb-menu-items" },
      el("button", { type: "button", class: "wb-menu-item", onclick: () => exportProgress(progress) }, "Export progress…"),
      el("button", { type: "button", class: "wb-menu-item", onclick: () => importProgress(progress) }, "Import progress…"),
      el("button", { type: "button", class: "wb-menu-item", onclick: () => window.open(new URL("../lab/index.html", import.meta.url).href, "_blank") }, "Open PyLab (full screen)"),
      el("button", { type: "button", class: "wb-menu-item", onclick: () => document.dispatchEvent(new CustomEvent("wb:present")) }, "Present in class", el("kbd", {}, "F")),
      el("hr"),
      el("button", { type: "button", class: "wb-menu-item is-danger", onclick: () => resetWorkbook(progress) }, "Reset this workbook…"),
    ));
  document.addEventListener("click", (e) => { if (!menu.contains(e.target)) menu.open = false; });

  const topbar = el("header", { class: "wb-topbar" },
    el("a", { class: "wb-topbar-brand", href: HOME_URL, title: "All workbooks" }, el("img", { src: LOGO_URL, alt: "Memorial University" })),
    titleBlock(title, short ?? shortTitle(id, title), subtitle),
    instructorBadge(),
    el("span", { class: "wb-spacer" }),
    status, exerciseIds.length ? progressBox : null, xpBadge,
    el("button", { type: "button", class: "wb-btn wb-btn-quiet wb-theme-toggle", title: "Toggle light / dark", onclick: () => document.dispatchEvent(new CustomEvent("wb:toggle-theme")) }, "◐"),
    menu,
  );
  document.body.prepend(topbar);
}

function exportProgress(progress) {
  const blob = new Blob([progress.exportJSON()], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = el("a", { href: url, download: `${progress.workbookId}-progress.json` });
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function importProgress(progress) {
  const picker = el("input", { type: "file", accept: "application/json,.json" });
  picker.addEventListener("change", async () => {
    const file = picker.files?.[0];
    if (!file) return;
    try {
      progress.importJSON(await file.text());
      toast("Progress imported. Reloading…", "good");
      setTimeout(() => location.reload(), 800);
    } catch (error) {
      window.alert(`Import failed: ${error.message}`);
    }
  });
  picker.click();
}

function resetWorkbook(progress) {
  if (!window.confirm("Clear all saved work and check marks for this workbook? Your XP balance is kept.")) return;
  progress.resetAll();
  location.reload();
}

// -------------------------------------------------------------- locked

/** Replace the page with a notice until the lecture's workbook opens. */
function renderLocked(entry) {
  document.title = `COMP 1001 – Lecture ${entry.n} Workbook`;
  const main = document.querySelector("main");
  if (main) main.hidden = true;
  const notice = el("main", { class: "wb-locked" },
    el("div", { class: "wb-course" }, "COMP 1001: Introduction to Programming"),
    el("h1", {}, `Lecture ${entry.n} Workbook`),
    el("p", { class: "wb-locked-when" }, `Opens ${fmtOpens(entry)}`),
    el("p", {}, "Each workbook unlocks when the lecture before it ends, so you can always read one lecture ahead. Until then, keep working on the earlier ones."),
    el("a", { class: "wb-btn", href: HOME_URL }, "All workbooks"),
  );
  document.body.append(notice);
  document.body.prepend(el("header", { class: "wb-topbar" },
    el("a", { class: "wb-topbar-brand", href: HOME_URL, title: "All workbooks" }, el("img", { src: LOGO_URL, alt: "Memorial University" })),
    titleBlock(`Lecture ${entry.n} Workbook`, `L${String(entry.n).padStart(2, "0")}`, "Not open yet"),
    el("span", { class: "wb-spacer" }),
    el("button", { class: "wb-btn wb-btn-quiet wb-theme-toggle", type: "button", title: "Toggle light / dark", onclick: () => document.dispatchEvent(new CustomEvent("wb:toggle-theme")) }, "◐"),
  ));
}

// -------------------------------------------------------------- bosses

/**
 * Draw the lecture's boss problems on the page: one marker per boss, each
 * linking to that problem in PyLab, in the page's <wb-bosses> tag (if any)
 * and as a row under the contents. The boss set lives in
 * ./boss/exercises.json next to the workbook, and its progress record says
 * which bosses are already defeated.
 */
const WORDS = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"];

async function renderBosses(id, entry) {
  const host = document.querySelector("wb-bosses");
  const toc = document.querySelector(".wb-toc");
  if ((!host && !toc) || !entry?.bosses || id !== workbookId(entry.n)) return;
  let specs;
  try { specs = (await (await fetch("./boss/exercises.json")).json()).exercises ?? {}; } catch { return; }
  const saved = new Progress(bossId(entry.n));
  const bosses = Object.entries(specs).filter(([, spec]) => spec.boss);
  if (!bosses.length) return;
  const marker = ([eid, spec], i) => {
    const beaten = Boolean(saved.get(eid).passed);
    const label = `Boss ${i + 1}${beaten ? ", defeated" : ""}${spec.xp ? ` (${spec.xp} XP)` : ""}`;
    return el("a", { class: `wb-boss${beaten ? " is-beaten" : ""}`, href: bossLabUrl(bossId(entry.n), eid), title: label, "aria-label": label },
      el("span", { class: "wb-boss-icon", "aria-hidden": "true" }, spec.boss));
  };
  const done = bosses.filter(([eid]) => saved.get(eid).passed).length;
  if (toc) {
    const mark = el("span", { class: "wb-toc-mark" }, done === bosses.length ? "✓" : `${done}/${bosses.length}`);
    mark.classList.toggle("is-done", done === bosses.length);
    toc.append(el("div", { class: "wb-toc-bosses", "aria-label": "Boss problems" }, mark, ...bosses.map(marker)));
  }
  if (!host) return;
  const strip = el("div", { class: "wb-boss-strip" }, ...bosses.map(marker));
  host.replaceChildren(el("div", { class: "wb-block wb-boss-block" },
    el("div", { class: "wb-block-title" }, "Boss problems"),
    el("p", {}, `${bosses.length === 1 ? "A bigger problem" : `${WORDS[bosses.length] ?? bosses.length} bigger problems`} that use only what this lecture and the earlier ones covered. Click a boss to open it in PyLab with its statement beside the editor. Term tests and the final exam ask questions like these, and you write the code in PyLab there too. ${done ? `Defeated so far: ${done} of ${bosses.length}.` : "Defeated bosses are knocked on their backs."}`),
    strip,
  ));
}

// ------------------------------------------------------------ contents

function buildContents(progress) {
  const main = document.querySelector("main");
  if (!main) return;
  const headings = [...main.querySelectorAll("h2[id]")];
  if (!headings.length) return;
  const list = el("ol", { class: "wb-toc-list" });
  const entries = [];
  for (const heading of headings) {
    const ids = sectionExerciseIds(heading);
    const mark = el("span", { class: "wb-toc-mark" });
    const link = el("a", { href: `#${heading.id}` }, mark, heading.dataset.tocTitle ?? heading.textContent);
    list.append(el("li", {}, link));
    entries.push({ heading, ids, mark, link });
  }
  // A page with no graded widgets has nothing to count, so it gets no marks column.
  const plain = entries.every((entry) => !entry.ids.length);
  const nav = el("nav", { class: `wb-toc${plain ? " is-plain" : ""}`, "aria-label": "Contents" }, el("div", { class: "wb-toc-title" }, "Contents"), list);
  main.parentNode.insertBefore(nav, main);
  document.body.classList.add("wb-has-toc");
  addContentsToggle(nav, list);

  progress.subscribe((p) => {
    for (const entry of entries) {
      if (!entry.ids.length) { entry.mark.textContent = ""; continue; }
      const { done, total } = p.summary(entry.ids);
      entry.mark.textContent = done === total ? "✓" : `${done}/${total}`;
      entry.mark.classList.toggle("is-done", done === total);
    }
  });

  // Highlight the section in view.
  const observer = new IntersectionObserver((records) => {
    for (const record of records) {
      if (!record.isIntersecting) continue;
      for (const entry of entries) entry.link.classList.toggle("is-current", entry.heading === record.target);
    }
  }, { rootMargin: "-10% 0px -80% 0px" });
  for (const entry of entries) observer.observe(entry.heading);
}

/** On narrow screens the contents list is a drop-down under a ☰ button in the top bar. */
function addContentsToggle(nav, list) {
  const topbar = document.querySelector(".wb-topbar");
  if (!topbar) return;
  const toggle = el("button", { type: "button", class: "wb-btn wb-btn-quiet wb-toc-toggle", title: "Contents", "aria-label": "Contents", "aria-expanded": "false" }, "☰");
  const setOpen = (open) => {
    document.body.classList.toggle("wb-toc-open", open);
    toggle.setAttribute("aria-expanded", String(open));
  };
  toggle.addEventListener("click", () => setOpen(!document.body.classList.contains("wb-toc-open")));
  list.addEventListener("click", (e) => { if (e.target.closest("a")) setOpen(false); });
  document.addEventListener("click", (e) => { if (!nav.contains(e.target) && !toggle.contains(e.target)) setOpen(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
  topbar.querySelector(".wb-theme-toggle").before(toggle);
  // The drop-down hangs from the bottom edge of the top bar, whose height depends on the viewport.
  const measure = () => document.documentElement.style.setProperty("--wb-topbar-h", `${topbar.offsetHeight}px`);
  new ResizeObserver(measure).observe(topbar);
  measure();
}

/** Exercise ids between this h2 and the next one. */
function sectionExerciseIds(heading) {
  const ids = [];
  let node = heading.nextElementSibling;
  while (node && node.tagName !== "H2") {
    if (node.matches("wb-exercise[id], wb-table[id], wb-short[id]")) ids.push(node.id);
    ids.push(...[...node.querySelectorAll("wb-exercise[id], wb-table[id], wb-short[id]")].map((n) => n.id));
    node = node.nextElementSibling;
  }
  return ids;
}
