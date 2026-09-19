// Presentation mode: one topic at a time, full screen, driven from the
// keyboard or a clicker. A "topic" is every direct child of <main> from one
// heading (h2 or h3) up to the next; the title block is the first topic.
//
// Keys (ignored while typing in an editor or field):
//   F            start / stop presenting (and toggle full screen)
//   → PageDown   next topic        ← PageUp    previous topic
//   ↑ ↓ Space    scroll within the topic (left to the browser)
//   Home / End   first / last      Esc         stop presenting
//
// Nothing is moved in the DOM: every child of <main> is tagged with its
// topic index and CSS hides all but the current one, so live widgets keep
// their state across topics.

const SCALE_KEY = "pylab-workbooks:present-scale";
// Multiples of the page's normal type size. Even the smallest step is meant to
// be readable from the back of a classroom; there is no "normal size" here.
const SCALES = [1.5, 1.7, 1.9, 2.15, 2.4];
const DEFAULT_SCALE = 1.9;

export function initPresentation() {
  const main = document.querySelector("main");
  if (!main) return;
  sizeDiagramsInRem(main);
  const topics = collectTopics(main);
  if (!topics.length) return;

  const state = { on: false, index: 0, scale: loadScale() };
  const ui = buildUi(topics, state);
  document.body.append(ui.root);
  applyScale(state.scale, ui);

  // Hooks used below.
  const show = (index, { scrollTop = true } = {}) => {
    state.index = Math.max(0, Math.min(topics.length - 1, index));
    topics.forEach((topic, i) => topic.nodes.forEach((node) => node.classList.toggle("wb-slide-on", i === state.index)));
    const topic = topics[state.index];
    ui.counter.textContent = `${state.index + 1} / ${topics.length}`;
    ui.crumb.textContent = topic.crumb;
    ui.prev.disabled = state.index === 0;
    ui.next.disabled = state.index === topics.length - 1;
    ui.bar.style.width = `${(100 * (state.index + 1)) / topics.length}%`;
    for (const item of ui.items) item.classList.toggle("is-current", Number(item.dataset.index) === state.index);
    if (topic.id) history.replaceState(null, "", `#${topic.id}`);
    if (scrollTop) window.scrollTo({ top: 0 });
    // CodeMirror measures itself while hidden; ask the visible editors to re-measure.
    for (const cm of main.querySelectorAll(".wb-slide-on .CodeMirror")) cm.CodeMirror?.refresh();
  };

  const start = async () => {
    if (state.on) return;
    state.on = true;
    const index = topicAtViewport(topics); // measured before the layout changes
    document.documentElement.classList.add("wb-presenting");
    document.body.classList.add("wb-presenting");
    ui.menu.open = false;
    show(index);
    try { await document.documentElement.requestFullscreen?.(); } catch { /* not allowed (e.g. iframe); presenting still works */ }
  };

  const stop = () => {
    if (!state.on) return;
    state.on = false;
    document.documentElement.classList.remove("wb-presenting");
    document.body.classList.remove("wb-presenting");
    ui.menu.open = false;
    const heading = topics[state.index].heading;
    for (const topic of topics) topic.nodes.forEach((node) => node.classList.remove("wb-slide-on"));
    for (const cm of main.querySelectorAll(".CodeMirror")) cm.CodeMirror?.refresh();
    if (document.fullscreenElement) document.exitFullscreen?.().catch(() => {});
    (heading ?? main).scrollIntoView({ block: "start" });
  };

  ui.prev.addEventListener("click", () => show(state.index - 1));
  ui.next.addEventListener("click", () => show(state.index + 1));
  ui.exit.addEventListener("click", stop);
  ui.fullscreen.addEventListener("click", () => {
    if (document.fullscreenElement) document.exitFullscreen?.().catch(() => {});
    else document.documentElement.requestFullscreen?.().catch(() => {});
  });
  ui.theme.addEventListener("click", () => document.dispatchEvent(new CustomEvent("wb:toggle-theme")));
  ui.smaller.addEventListener("click", () => { state.scale = stepScale(state.scale, -1); applyScale(state.scale, ui); show(state.index, { scrollTop: false }); });
  ui.larger.addEventListener("click", () => { state.scale = stepScale(state.scale, +1); applyScale(state.scale, ui); show(state.index, { scrollTop: false }); });
  for (const item of ui.items) item.addEventListener("click", () => { show(Number(item.dataset.index)); ui.menu.open = false; });
  document.addEventListener("click", (e) => { if (!ui.menu.contains(e.target)) ui.menu.open = false; });
  document.addEventListener("wb:present", start);

  // Leaving full screen with the browser's own Esc ends the presentation too.
  document.addEventListener("fullscreenchange", () => { if (!document.fullscreenElement && state.on) stop(); });

  document.addEventListener("keydown", (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey || isTyping(event.target)) return;
    if (!state.on) {
      if (event.key === "f" || event.key === "F") { event.preventDefault(); start(); }
      return;
    }
    if (document.body.classList.contains("wb-has-expanded")) return; // an expanded editor owns Esc
    switch (event.key) {
      case "f": case "F": case "Escape": stop(); break;
      case "ArrowRight": case "PageDown": show(state.index + 1); break;
      case "ArrowLeft": case "PageUp": show(state.index - 1); break;
      case "Home": show(0); break;
      case "End": show(topics.length - 1); break;
      default: return;
    }
    event.preventDefault();
  });
}

// --------------------------------------------------------------- topics

function collectTopics(main) {
  const topics = [];
  let section = null; // the enclosing h2 title, for the breadcrumb of h3 topics
  for (const node of main.children) {
    const heading = node.matches("h2, h3") ? node : node.querySelector(":scope > h2, :scope > h3");
    if (heading || !topics.length) {
      const level = heading?.tagName === "H3" ? 3 : 2;
      const title = heading ? (heading.dataset.tocTitle ?? heading.textContent.trim()) : (main.querySelector("h1")?.textContent.trim() ?? "Title");
      if (heading && level === 2) section = title;
      topics.push({
        heading, level, title, nodes: [],
        id: heading?.id || null,
        crumb: heading && level === 3 && section ? `${section}  ›  ${title}` : title,
      });
    }
    topics[topics.length - 1].nodes.push(node);
  }
  return topics;
}

/** Index of the topic whose heading is nearest above the current scroll position. */
function topicAtViewport(topics) {
  const hash = location.hash.slice(1);
  const byHash = hash ? topics.findIndex((t) => t.id === hash) : -1;
  const line = window.scrollY + window.innerHeight * 0.25;
  let best = 0;
  topics.forEach((topic, i) => {
    const top = topic.nodes[0].getBoundingClientRect().top + window.scrollY;
    if (top <= line) best = i;
  });
  return byHash >= 0 && best === 0 ? byHash : best;
}

function isTyping(target) {
  return Boolean(target?.closest?.("input, textarea, select, [contenteditable], .CodeMirror"));
}

// ------------------------------------------------------------------- ui

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else node.setAttribute(key, value === true ? "" : value);
  }
  node.append(...children.flat().filter(Boolean));
  return node;
}

function buildUi(topics, state) {
  const items = topics.map((topic, i) =>
    el("button", { type: "button", class: `wb-menu-item wb-present-item is-level-${topic.level}`, "data-index": String(i) },
      el("span", { class: "wb-present-item-n" }, String(i + 1)), topic.title));
  const smaller = el("button", { type: "button", class: "wb-btn wb-btn-quiet", title: "Smaller text" }, "A−");
  const larger = el("button", { type: "button", class: "wb-btn wb-btn-quiet", title: "Larger text" }, "A+");
  const scaleLabel = el("span", { class: "wb-present-scale" });
  const theme = el("button", { type: "button", class: "wb-menu-item" }, "Toggle light / dark");
  const fullscreen = el("button", { type: "button", class: "wb-menu-item" }, "Toggle full screen");
  const exit = el("button", { type: "button", class: "wb-menu-item is-danger" }, "Exit presentation", el("kbd", {}, "Esc"));
  const menu = el("details", { class: "wb-menu wb-present-menu" },
    el("summary", { class: "wb-btn wb-btn-quiet wb-btn-icon", title: "Presentation menu" }, "☰"),
    el("div", { class: "wb-menu-items" },
      el("div", { class: "wb-present-menu-title" }, "Topics"),
      el("div", { class: "wb-present-list" }, items),
      el("hr"),
      el("div", { class: "wb-present-row" }, el("span", {}, "Text size"), el("span", { class: "wb-spacer" }), smaller, scaleLabel, larger),
      theme, fullscreen,
      el("hr"),
      exit,
      el("div", { class: "wb-present-hint" }, "← → move between topics · F or Esc to stop")));
  const prev = el("button", { type: "button", class: "wb-btn wb-btn-quiet wb-btn-icon", title: "Previous topic (←)" }, "‹");
  const next = el("button", { type: "button", class: "wb-btn wb-btn-quiet wb-btn-icon", title: "Next topic (→)" }, "›");
  const counter = el("span", { class: "wb-present-counter" });
  const crumb = el("span", { class: "wb-present-crumb" });
  const bar = el("span", { class: "wb-present-bar" });
  const root = el("div", { class: "wb-present-ui" },
    menu,
    el("div", { class: "wb-present-nav" }, crumb, prev, counter, next),
    el("span", { class: "wb-present-track" }, bar));
  return { root, menu, items, prev, next, counter, crumb, bar, exit, fullscreen, theme, smaller, larger, scaleLabel };
}

function loadScale() {
  try { const v = Number(localStorage.getItem(SCALE_KEY)); return SCALES.includes(v) ? v : DEFAULT_SCALE; } catch { return DEFAULT_SCALE; }
}

function stepScale(current, dir) {
  const i = Math.max(0, Math.min(SCALES.length - 1, SCALES.indexOf(current) + dir));
  const next = SCALES[i];
  try { localStorage.setItem(SCALE_KEY, String(next)); } catch { /* ignore */ }
  return next;
}

/** Inline SVGs sized with a pixel width attribute would stay small while the text grows in
 *  presentation mode; the same width in rem scales with everything else (text inside an SVG
 *  with a viewBox scales with the drawing). */
function sizeDiagramsInRem(main) {
  for (const svg of main.querySelectorAll("svg[viewBox][width]")) {
    const width = Number(svg.getAttribute("width"));
    if (!width || svg.style.width) continue;
    svg.style.width = `${width / 16}rem`;
    svg.style.maxWidth = "100%";
    svg.style.height = "auto";
  }
}

function applyScale(scale, ui) {
  document.documentElement.style.setProperty("--wb-present-scale", String(scale));
  ui.scaleLabel.textContent = `${Math.round(scale * 100)}%`;
  ui.smaller.disabled = scale === SCALES[0];
  ui.larger.disabled = scale === SCALES[SCALES.length - 1];
}
