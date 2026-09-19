// Workbook widgets. Each tag looks up its spec by id in the workbook's
// exercises.json (handed over by workbook.js through defineComponents).
//
//   <wb-example id="…">   editable teaching code with ▶ Run and "Restore original"
//   <wb-exercise id="…">  coding task: editor, Run, Check, XP, model answer
//   <wb-table id="…">     an HTML table whose [data-blank] cells become inputs
//   <wb-short id="…">     written answer compared against a model answer
//
// All widgets render into the light DOM so workbook.css styles them.

import { createEditor } from "./editor.js";
import { Console } from "./console.js";
import { runner, runInteractive, StoppedError, TimeoutError } from "./runner.js";
import { runCases, matchAnswer } from "./grader.js";
import { xp } from "./xp.js";
import { isInstructor } from "./instructor.js";

const LAB_URL = new URL("../lab/index.html", import.meta.url).href;

let context = null;

/** Register the custom elements once the workbook's specs and progress exist. */
export function defineComponents({ workbookId, specs, progress }) {
  context = { workbookId, specs, progress };
  if (!customElements.get("wb-example")) {
    customElements.define("wb-example", ExampleElement);
    customElements.define("wb-exercise", ExerciseElement);
    customElements.define("wb-table", TableElement);
    customElements.define("wb-short", ShortElement);
  }
}

// ---------------------------------------------------------------- helpers

export function encodeBase64(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

export function decodeBase64(text) {
  const binary = atob(String(text ?? "").replace(/\s+/g, ""));
  const bytes = Uint8Array.from(binary, (ch) => ch.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === "class") el.className = value;
    else if (key === "hidden") el.hidden = Boolean(value);
    else if (key.startsWith("on")) el.addEventListener(key.slice(2), value);
    else if (key === "html") el.innerHTML = value;
    else el.setAttribute(key, value === true ? "" : value);
  }
  el.append(...children.flat().filter((c) => c != null && c !== false));
  return el;
}

function button(label, onclick, extra = {}) {
  return h("button", { type: "button", class: "wb-btn " + (extra.class ?? ""), onclick, title: extra.title, hidden: extra.hidden }, label);
}

/** Small transient message in the corner (e.g. "+5 XP"). */
export function toast(text, kind = "info") {
  let stack = document.querySelector(".wb-toasts");
  if (!stack) {
    stack = h("div", { class: "wb-toasts", "aria-live": "polite" });
    document.body.append(stack);
  }
  const item = h("div", { class: `wb-toast wb-toast-${kind}` }, text);
  stack.append(item);
  requestAnimationFrame(() => item.classList.add("is-shown"));
  setTimeout(() => {
    item.classList.remove("is-shown");
    setTimeout(() => item.remove(), 400);
  }, 2600);
}

function labUrl(code) {
  return `${LAB_URL}#code=${encodeURIComponent(encodeBase64(code))}`;
}

/** PyLab's boss mode: the problem statement beside the editor, with Check. */
export function bossLabUrl(workbookId, exerciseId) {
  return `${LAB_URL}?boss=${encodeURIComponent(`${workbookId}/${exerciseId}`)}`;
}

export function describeRunFailure(error) {
  if (error instanceof TimeoutError) return error.message;
  if (error instanceof StoppedError) return "Stopped.";
  return error?.message || String(error);
}

/**
 * The result of `runCases` as a list of case boxes for a `.wb-result` panel.
 * `markErrorLine(line)` is called for the first failing traceback.
 */
export function renderOutcome(outcome, { markErrorLine } = {}) {
  const single = outcome.cases.length === 1;
  const nodes = [h("div", { class: "wb-result-summary " + (outcome.pass ? "is-good" : "is-bad") },
    outcome.pass ? "✓ Correct!" : single ? "✗ Not yet" : `✗ ${outcome.cases.filter((c) => c.pass).length} of ${outcome.cases.length} cases pass`)];
  for (const c of outcome.cases) {
    const box = h("div", { class: "wb-result-case " + (c.pass ? "is-good" : "is-bad") });
    if (!single) box.append(h("div", { class: "wb-result-case-title" }, (c.pass ? "✓ " : "✗ ") + c.name));
    if (c.inputs?.length) {
      box.append(h("div", { class: "wb-result-label" }, "Typed at the prompts: "), h("code", {}, c.inputs.map((v) => JSON.stringify(v)).join(", ")));
    }
    if (c.error) {
      box.append(h("p", { class: "wb-result-text" }, c.error));
      if (c.stderr) {
        box.append(h("pre", { class: "wb-result-stderr" }, c.stderr));
        const line = errorLineFromTraceback(c.stderr);
        if (line && !c.pass) markErrorLine?.(line);
      }
      if (c.stdout) box.append(h("div", { class: "wb-result-label" }, "Printed before the error:"), h("pre", { class: "wb-result-stdout" }, c.stdout));
    } else if (!c.pass) {
      if (c.comparison && !c.comparison.pass) box.append(renderDiff(c.comparison));
      if (c.checkMessage) box.append(h("p", { class: "wb-result-text" }, c.checkMessage));
    }
    nodes.push(box);
  }
  return nodes;
}

function renderDiff(comparison) {
  const table = h("table", { class: "wb-diff" }, h("thead", {}, h("tr", {}, h("th", {}, "Expected"), h("th", {}, "Your output"))));
  const body = h("tbody");
  for (const line of comparison.lines) {
    body.append(h("tr", { class: line.ok ? "is-ok" : "is-diff" },
      h("td", {}, cell(line.expected)), h("td", {}, cell(line.actual))));
  }
  table.append(body);
  return table;
  function cell(text) {
    if (text == null) return h("span", { class: "wb-diff-missing" }, "(no line)");
    if (text === "") return h("span", { class: "wb-diff-missing" }, "(blank line)");
    return h("code", {}, text);
  }
}

/** True when the program reads from the keyboard, so Python Tutor needs the answers up front. */
function usesInput(code) {
  return /\binput\s*\(/.test(code);
}

/** Python Tutor's embeddable visualizer, with the program (and any input() answers) in the URL fragment. */
function tutorUrl(code, inputs = []) {
  const codeDivHeight = Math.min(400, Math.max(60, 22 * code.split("\n").length + 20));
  // Without rawInputLstJSON the embed stops at the first input() and sends the student to pythontutor.com.
  const answers = inputs.length ? `&rawInputLstJSON=${encodeURIComponent(JSON.stringify(inputs))}` : "";
  return `https://pythontutor.com/iframe-embed.html#code=${encodeURIComponent(code)}&codeDivHeight=${codeDivHeight}&codeDivWidth=350&curInstr=0&origin=opt-frontend.js&py=311${answers}`;
}

/** Starting height of the Python Tutor frame: short programs get a short frame. */
function tutorHeight(code) {
  return Math.min(600, Math.max(380, 22 * code.split("\n").length + 300));
}

/** Last "main.py" line number mentioned in a traceback, or null. */
function errorLineFromTraceback(stderr) {
  const matches = [...String(stderr).matchAll(/File "main\.py", line (\d+)/g)];
  return matches.length ? Number(matches.at(-1)[1]) : null;
}

function xpBadge(amount, record) {
  const badge = h("span", { class: "wb-xp-badge" });
  const refresh = () => {
    badge.classList.toggle("is-earned", Boolean(record().earned));
    badge.classList.toggle("is-revealed", Boolean(record().revealed));
    badge.textContent = record().revealed ? `${amount} XP · answer shown` : record().earned ? `+${amount} XP earned` : `${amount} XP`;
  };
  refresh();
  badge.refresh = refresh;
  return badge;
}

/** Ask before spending XP; returns true if the reveal went through. */
function confirmReveal(id, cost) {
  const { progress } = context;
  if (progress.get(id).revealed) return true;
  if (isInstructor()) return progress.reveal(id, 0);
  if (cost > 0 && !xp.canAfford(cost)) {
    toast(`You need ${cost} XP to see this answer (you have ${xp.balance}).`, "warn");
    return false;
  }
  const message = cost > 0
    ? `Spend ${cost} XP to see the answer? You won't be able to earn XP from this exercise afterwards.`
    : "Show the answer? You won't be able to earn XP from this exercise afterwards.";
  if (!window.confirm(message)) return false;
  if (!progress.reveal(id, cost)) return false;
  if (cost > 0) toast(`−${cost} XP`, "warn");
  return true;
}

// ------------------------------------------------------------ base class

class WorkbookElement extends HTMLElement {
  connectedCallback() {
    if (this.rendered) return;
    this.rendered = true;
    if (!context) {
      this.append(h("p", { class: "wb-widget-error" }, "This workbook's exercises did not load."));
      return;
    }
    this.exerciseId = this.getAttribute("id");
    this.spec = context.specs[this.exerciseId];
    if (!this.spec) {
      this.append(h("p", { class: "wb-widget-error" }, `No exercise named "${this.exerciseId}" in exercises.json.`));
      return;
    }
    this.progress = context.progress;
    this.classList.add("wb-widget");
    this.render();
  }

  get record() {
    return this.progress.get(this.exerciseId);
  }
}

// ------------------------------------------------------- runnable widgets

/** Shared editor + console + Run / Visualize plumbing for examples and exercises. */
class RunnableElement extends WorkbookElement {
  buildRunner({ code, readOnly, minLines, maxLines, onChange }) {
    this.editorHost = h("div");
    this.runButton = button("▶ Run", () => this.runInteractive(), { class: "wb-btn-primary" });
    // Python Tutor cannot see extra modules, so single-file programs only.
    this.tutorButton = button("Visualize", () => this.visualize(), { class: "wb-btn-quiet", title: "Step through this program on pythontutor.com", hidden: (this.spec.files ?? []).length > 0 });
    this.tutorPanel = h("div", { class: "wb-tutor", hidden: true });
    this.statusLabel = h("span", { class: "wb-runner-status" });
    this.consoleTitle = h("div", { class: "wb-console-title" }, "Output");
    this.consoleHost = h("div");
    this.console = new Console(this.consoleHost);
    this.consoleWrap = h("div", { class: "wb-console-wrap" }, this.consoleTitle, this.consoleHost);
    this.editorReady = createEditor(this.editorHost, { value: code, readOnly, minLines, maxLines, onChange });
    this.editorReady.then((editor) => { this.editor = editor; });
    runner.onStatus((state, text) => {
      this.statusLabel.textContent = state === "ready" || state === "idle" ? "" : text;
      this.statusLabel.dataset.state = state;
    });
  }

  get files() {
    const extra = this.spec.files ?? [];
    return [{ name: "main.py", content: this.editor.getValue() }, ...extra.filter((f) => f.name !== "main.py")];
  }

  setBusy(flag) {
    this.busy = flag;
    this.classList.toggle("is-running", flag);
    this.runButton.title = flag ? "Start the program again from the top" : "";
    for (const b of this.querySelectorAll("[data-disable-while-running]")) b.disabled = flag;
  }

  /** Run the program; pressing Run while it is still going (for example at an input() prompt) starts it over. */
  async runInteractive() {
    if (this.busy) {
      this.stopRun();
      await this.running;
    }
    await this.editorReady;
    this.setBusy(true);
    this.editor.clearErrorLine();
    this.console.clear();
    this.consoleTitle.textContent = "Output";
    this.abort = new AbortController();
    this.running = (async () => {
      try {
        const result = await runInteractive({ files: this.files, entry: "main.py", console: this.console, signal: this.abort.signal });
        if (result.status === "error") {
          const line = errorLineFromTraceback(result.stderr);
          if (line) this.editor.markErrorLine(line);
        } else if (this.console.isEmpty) {
          this.console.note("(The program finished without printing anything.)");
        }
      } catch (error) {
        if (error.name === "AbortError" || error instanceof StoppedError) this.console.note("\nStopped.");
        else this.console.error("\n" + describeRunFailure(error));
      } finally {
        this.abort = null;
        this.running = null;
        this.setBusy(false);
      }
    })();
    await this.running;
  }

  stopRun() {
    this.abort?.abort();
    runner.stop();
  }

  /** Show the whole program in an embedded Python Tutor below the console. The toolbar button toggles it. */
  async visualize() {
    if (!this.tutorPanel.hidden) { this.closeVisualizer(); return; }
    await this.editorReady;
    this.tutorPanel.hidden = false;
    this.tutorButton.textContent = "Hide visualizer";
    this.loadVisualizer();
    this.tutorPanel.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  /** Fill the panel from the current editor contents: a form for the input() answers first when the program needs them. */
  loadVisualizer() {
    const code = this.editor.getValue();
    if (usesInput(code)) this.askTutorInputs(code);
    else this.showTutorFrame(code, []);
  }

  /** Python Tutor cannot pause at input(), so the answers are typed here, one per line, before the trace is made. */
  askTutorInputs(code) {
    const previous = this.tutorInputs ?? (this.spec.cases ?? []).find((c) => c.inputs?.length)?.inputs ?? [];
    const field = h("textarea", { class: "wb-tutor-inputs", rows: Math.max(2, previous.length + 1), spellcheck: "false", "aria-label": "Answers for input(), one per line" });
    field.value = previous.join("\n");
    const go = () => {
      const lines = field.value.split("\n");
      while (lines.length && lines.at(-1) === "") lines.pop();
      this.tutorInputs = lines;
      this.showTutorFrame(code, lines);
    };
    field.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); go(); } });
    this.tutorPanel.replaceChildren(
      this.tutorHead("This program reads input, and Python Tutor needs every answer before it starts. Type what you would answer at each prompt, one answer per line.",
        button("✕ Close", () => this.closeVisualizer(), { class: "wb-btn-quiet" })),
      h("div", { class: "wb-tutor-form" },
        field,
        button("Visualize with these answers", go, { class: "wb-btn-primary", title: "Cmd+Enter or Ctrl+Enter" })),
    );
    field.focus();
  }

  showTutorFrame(code, inputs) {
    const frame = h("iframe", { src: tutorUrl(code, inputs), title: "Python Tutor" });
    // Room for the code plus Python Tutor's slider, output box, and frames; the student can drag it taller.
    const box = h("div", { class: "wb-tutor-box", style: `height: ${tutorHeight(code)}px` }, frame);
    const reloadLabel = inputs.length ? "↻ Reload code or answers" : "↻ Reload code";
    this.tutorPanel.replaceChildren(
      this.tutorHead("Step through the program one line at a time on pythontutor.com. Drag the bottom edge to resize.",
        button(reloadLabel, () => this.loadVisualizer(), { class: "wb-btn-quiet", title: "Send the current editor contents to Python Tutor" }),
        button("✕ Close", () => this.closeVisualizer(), { class: "wb-btn-quiet" })),
      box,
    );
  }

  tutorHead(note, ...buttons) {
    return h("div", { class: "wb-tutor-head" },
      h("span", { class: "wb-console-title" }, "Python Tutor"),
      h("span", { class: "wb-tutor-note" }, note),
      h("span", { class: "wb-spacer" }),
      ...buttons);
  }

  closeVisualizer() {
    this.tutorPanel.hidden = true;
    this.tutorPanel.replaceChildren();
    this.tutorButton.textContent = "Visualize";
  }

  addExpandToggle(toolbar) {
    const toggle = button("⤢", () => this.toggleExpanded(), { class: "wb-btn-quiet wb-btn-icon", title: "Expand editor" });
    toolbar.append(toggle);
    this.expandToggle = toggle;
  }

  toggleExpanded(force) {
    const expanded = this.classList.toggle("is-expanded", force);
    document.body.classList.toggle("wb-has-expanded", expanded);
    this.expandToggle.textContent = expanded ? "⤡" : "⤢";
    this.expandToggle.title = expanded ? "Back to the page" : "Expand editor";
    this.editor?.setMaxLines(expanded ? null : this.maxLines);
    this.editor?.refresh();
    if (expanded) {
      this.escHandler = (event) => { if (event.key === "Escape") this.toggleExpanded(false); };
      document.addEventListener("keydown", this.escHandler);
    } else if (this.escHandler) {
      document.removeEventListener("keydown", this.escHandler);
    }
  }
}

// ---------------------------------------------------------- <wb-example>

class ExampleElement extends RunnableElement {
  render() {
    const spec = this.spec;
    this.maxLines = spec.maxLines ?? 30;
    this.buildRunner({
      code: spec.code, readOnly: false, minLines: 1, maxLines: this.maxLines,
      onChange: (value) => { this.resetButton.hidden = value === spec.code; },
    });
    this.classList.add("wb-example");

    const resetButton = button("Restore original", () => this.restore(), { class: "wb-btn-quiet", hidden: true });
    this.resetButton = resetButton;
    const toolbar = h("div", { class: "wb-toolbar" },
      this.runButton, this.tutorButton, this.statusLabel,
      h("span", { class: "wb-spacer" }),
      resetButton,
      h("a", { class: "wb-btn wb-btn-quiet", href: labUrl(spec.code), target: "_blank", rel: "noopener", onclick: (e) => { e.currentTarget.href = labUrl(this.editor?.getValue() ?? spec.code); } }, "Open in PyLab"),
    );
    this.addExpandToggle(toolbar);

    if (spec.output != null) {
      this.consoleTitle.textContent = "Output";
      this.console.append(spec.output, "wb-console-out");
    } else {
      this.consoleWrap.hidden = true;
    }
    this.append(
      h("div", { class: "wb-widget-head" }, h("span", { class: "wb-widget-label" }, spec.title ?? "Example")),
      this.editorHost, toolbar, this.consoleWrap, this.tutorPanel,
    );
  }

  async runInteractive() {
    this.consoleWrap.hidden = false;
    await super.runInteractive();
  }

  restore() {
    this.editor.setValue(this.spec.code);
    this.resetButton.hidden = true;
  }
}

// --------------------------------------------------------- <wb-exercise>

class ExerciseElement extends RunnableElement {
  render() {
    const spec = this.spec;
    const record = this.record;
    this.maxLines = spec.maxLines ?? 24;
    this.buildRunner({
      code: record.work ?? spec.starter ?? "",
      readOnly: false,
      minLines: spec.minLines ?? 6,
      maxLines: this.maxLines,
      onChange: (value) => this.progress.setWork(this.exerciseId, value),
    });
    this.classList.add("wb-exercise");

    this.badge = xpBadge(spec.xp ?? 5, () => this.record);
    this.statusPill = h("span", { class: "wb-status-pill" });
    this.checkButton = button("✓ Check", () => this.check(), { class: "wb-btn-check" });
    this.checkButton.dataset.disableWhileRunning = "";
    this.resultPanel = h("div", { class: "wb-result", hidden: true });
    this.answerPanel = h("div", { class: "wb-answer", hidden: true });
    this.revealButton = button("", () => this.reveal(), { class: "wb-btn-quiet wb-btn-reveal", hidden: !spec.answer });

    const toolbar = h("div", { class: "wb-toolbar" },
      this.runButton, this.tutorButton, this.checkButton, this.statusLabel,
      h("span", { class: "wb-spacer" }),
      button("Reset", () => this.reset(), { class: "wb-btn-quiet", title: "Back to the starter code" }),
      this.revealButton,
      spec.boss
        ? h("a", { class: "wb-btn wb-btn-quiet", href: bossLabUrl(context.workbookId, this.exerciseId) }, "Open in PyLab")
        : h("a", { class: "wb-btn wb-btn-quiet", href: "#", target: "_blank", rel: "noopener", onclick: (e) => { e.currentTarget.href = labUrl(this.editor?.getValue() ?? ""); } }, "Open in PyLab"),
    );
    this.addExpandToggle(toolbar);

    this.append(
      h("div", { class: "wb-widget-head" },
        h("span", { class: "wb-widget-label" }, spec.title ?? "Your code"),
        this.statusPill, this.badge),
      this.editorHost, toolbar, this.consoleWrap, this.tutorPanel, this.resultPanel, this.answerPanel,
    );
    this.consoleWrap.hidden = true;
    this.refreshState();
    if (record.revealed && spec.answer) this.showAnswer();
  }

  refreshState() {
    const record = this.record;
    this.badge.refresh();
    this.classList.toggle("is-passed", Boolean(record.passed));
    this.classList.toggle("is-revealed", Boolean(record.revealed));
    this.statusPill.textContent = record.passed ? "✓ Correct" : "";
    this.statusPill.className = "wb-status-pill" + (record.passed ? " is-good" : "");
    const cost = record.revealed ? 0 : this.spec.xp ?? 5;
    this.revealButton.textContent = record.revealed ? "Answer shown" : isInstructor() ? "Show answer" : `Show answer (−${cost} XP)`;
    this.revealButton.disabled = Boolean(record.revealed);
  }

  async runInteractive() {
    this.consoleWrap.hidden = false;
    this.resultPanel.hidden = true;
    await super.runInteractive();
  }

  async check() {
    if (this.busy) return;
    await this.editorReady;
    this.setBusy(true);
    this.editor.clearErrorLine();
    this.consoleWrap.hidden = true;
    this.resultPanel.hidden = false;
    this.resultPanel.replaceChildren(h("div", { class: "wb-result-pending" }, "Checking…"));
    try {
      const outcome = await runCases(this.spec, this.editor.getValue(), this.spec.files ?? []);
      this.renderResult(outcome);
      if (outcome.pass) this.succeed();
    } catch (error) {
      this.resultPanel.replaceChildren(h("div", { class: "wb-result-case is-bad" }, h("div", { class: "wb-result-case-title" }, "✗ Could not check"), h("pre", { class: "wb-result-text" }, describeRunFailure(error))));
    } finally {
      this.setBusy(false);
    }
  }

  succeed() {
    const first = !this.record.passed;
    this.progress.markPassed(this.exerciseId);
    const added = this.progress.award(this.exerciseId, this.spec.xp ?? 5);
    if (added) toast(`+${added} XP`, "good");
    else if (first && this.record.revealed) toast("Correct! (no XP: the answer was shown)", "info");
    this.refreshState();
  }

  renderResult(outcome) {
    this.resultPanel.replaceChildren(...renderOutcome(outcome, { markErrorLine: (line) => this.editor.markErrorLine(line) }));
  }

  reveal() {
    if (!confirmReveal(this.exerciseId, this.spec.xp ?? 5)) return;
    this.refreshState();
    this.showAnswer();
  }

  async showAnswer() {
    this.answerPanel.hidden = false;
    if (this.answerPanel.childElementCount) return;
    const host = h("div");
    this.answerPanel.append(h("div", { class: "wb-answer-title" }, "Model answer"), host);
    if (this.spec.answerNote) this.answerPanel.append(h("p", { class: "wb-answer-note" }, this.spec.answerNote));
    await createEditor(host, { value: decodeBase64(this.spec.answer), readOnly: true, minLines: 1, maxLines: null });
  }

  async reset() {
    await this.editorReady;
    if (!window.confirm("Replace your code with the starter code?")) return;
    this.editor.setValue(this.spec.starter ?? "");
    this.progress.setWork(this.exerciseId, this.spec.starter ?? "");
    this.console.clear();
    this.consoleWrap.hidden = true;
    this.resultPanel.hidden = true;
  }
}

// ------------------------------------------------------------ <wb-table>

class TableElement extends WorkbookElement {
  render() {
    const spec = this.spec;
    const record = this.record;
    this.classList.add("wb-table");
    this.perBlank = spec.xp ?? 1;
    this.inputs = new Map();
    const saved = record.work ?? {};

    for (const cell of this.querySelectorAll("[data-blank]")) {
      const name = cell.dataset.blank;
      const key = spec.blanks?.[name];
      if (!key) {
        cell.append(h("span", { class: "wb-widget-error" }, `no key for "${name}"`));
        continue;
      }
      const input = h("input", { type: "text", class: "wb-blank", "aria-label": `Answer ${name}`, autocomplete: "off", spellcheck: "false", placeholder: key.placeholder ?? "" });
      if (key.width) input.style.width = key.width;
      input.value = saved[name] ?? "";
      input.addEventListener("input", () => {
        cell.classList.remove("is-right", "is-wrong");
        this.saveWork();
      });
      input.addEventListener("keydown", (e) => { if (e.key === "Enter") this.check(); });
      cell.replaceChildren(input);
      cell.classList.add("wb-blank-cell");
      this.inputs.set(name, { input, cell, key });
    }

    this.badge = h("span", { class: "wb-xp-badge" });
    this.statusPill = h("span", { class: "wb-status-pill" });
    this.revealButton = button("", () => this.reveal(), { class: "wb-btn-quiet wb-btn-reveal" });
    this.summaryLine = h("div", { class: "wb-result-summary", hidden: true });
    this.append(h("div", { class: "wb-toolbar" },
      button("✓ Check", () => this.check(), { class: "wb-btn-check" }),
      this.statusPill,
      h("span", { class: "wb-spacer" }),
      this.badge,
      button("Clear", () => this.clear(), { class: "wb-btn-quiet" }),
      this.revealButton,
    ), this.summaryLine);
    this.refreshState();
    if (record.revealed) this.fillAnswers();
    else this.markEarned();
  }

  get total() {
    return this.inputs.size * this.perBlank;
  }

  get remainingCost() {
    let cost = 0;
    for (const name of this.inputs.keys()) if (!this.progress.hasEarnedPart(this.exerciseId, name)) cost += this.perBlank;
    return cost;
  }

  refreshState() {
    const record = this.record;
    const earned = Object.values(record.parts ?? {}).reduce((a, b) => a + b, 0);
    this.badge.textContent = record.revealed ? `${this.total} XP · answers shown` : earned ? `+${earned} of ${this.total} XP earned` : `${this.total} XP (${this.perBlank} per blank)`;
    this.badge.classList.toggle("is-earned", earned > 0 && earned === this.total);
    this.badge.classList.toggle("is-revealed", Boolean(record.revealed));
    this.classList.toggle("is-passed", Boolean(record.passed));
    this.classList.toggle("is-revealed", Boolean(record.revealed));
    this.statusPill.textContent = record.passed ? "✓ All correct" : "";
    this.statusPill.className = "wb-status-pill" + (record.passed ? " is-good" : "");
    const cost = this.remainingCost;
    this.revealButton.textContent = record.revealed ? "Answers shown" : isInstructor() ? "Show answers" : `Show answers (−${cost} XP)`;
    this.revealButton.disabled = Boolean(record.revealed);
  }

  markEarned() {
    for (const [name, { cell }] of this.inputs) {
      if (this.progress.hasEarnedPart(this.exerciseId, name) && cell.querySelector("input").value) cell.classList.add("is-right");
    }
  }

  saveWork() {
    const work = {};
    for (const [name, { input }] of this.inputs) work[name] = input.value;
    this.progress.setWork(this.exerciseId, work);
  }

  check() {
    let right = 0;
    let added = 0;
    let attempted = 0;
    for (const [name, { input, cell, key }] of this.inputs) {
      if (!input.value.trim()) { cell.classList.remove("is-right", "is-wrong"); continue; }
      attempted++;
      const ok = matchAnswer(input.value, key.accept, { caseSensitive: key.caseSensitive });
      cell.classList.toggle("is-right", ok);
      cell.classList.toggle("is-wrong", !ok);
      if (ok) {
        right++;
        added += this.progress.award(this.exerciseId, this.perBlank, name);
      }
    }
    this.summaryLine.hidden = false;
    if (attempted === 0) {
      this.summaryLine.className = "wb-result-summary";
      this.summaryLine.textContent = "Fill in at least one blank first.";
    } else if (right === this.inputs.size) {
      this.summaryLine.className = "wb-result-summary is-good";
      this.summaryLine.textContent = "✓ All correct!";
      this.progress.markPassed(this.exerciseId);
    } else {
      this.summaryLine.className = "wb-result-summary is-bad";
      this.summaryLine.textContent = `${right} of ${this.inputs.size} correct. The highlighted cells need another look.`;
    }
    if (added) toast(`+${added} XP`, "good");
    this.refreshState();
  }

  reveal() {
    if (!confirmReveal(this.exerciseId, this.remainingCost)) return;
    this.fillAnswers();
    this.refreshState();
  }

  fillAnswers() {
    for (const { input, cell, key } of this.inputs.values()) {
      input.value = key.show ?? key.accept[0];
      input.readOnly = true;
      cell.classList.remove("is-wrong");
      cell.classList.add("is-answer");
    }
    this.summaryLine.hidden = true;
    this.saveWork();
  }

  clear() {
    if (this.record.revealed) return;
    for (const { input, cell } of this.inputs.values()) {
      input.value = "";
      cell.classList.remove("is-right", "is-wrong");
    }
    this.summaryLine.hidden = true;
    this.saveWork();
  }
}

// ------------------------------------------------------------ <wb-short>

class ShortElement extends WorkbookElement {
  render() {
    const spec = this.spec;
    const record = this.record;
    this.classList.add("wb-short");
    this.minChars = spec.minChars ?? 20;
    this.amount = spec.xp ?? 2;

    this.textarea = h("textarea", { class: "wb-short-input", rows: spec.rows ?? 3, placeholder: spec.placeholder ?? "Write your answer in your own words…" });
    this.textarea.value = record.work ?? "";
    this.textarea.addEventListener("input", () => {
      this.progress.setWork(this.exerciseId, this.textarea.value);
      this.refreshState();
    });

    this.badge = xpBadge(this.amount, () => this.record);
    this.statusPill = h("span", { class: "wb-status-pill" });
    this.compareButton = button("Compare with model answer", () => this.compare(), { class: "wb-btn-check" });
    this.revealButton = button("", () => this.reveal(), { class: "wb-btn-quiet wb-btn-reveal" });
    this.hint = h("span", { class: "wb-short-hint" });
    this.answerPanel = h("div", { class: "wb-answer", hidden: true });
    this.selfCheck = h("div", { class: "wb-self-check", hidden: true },
      h("span", {}, "Did your answer cover the same idea?"),
      button(`I got it (+${this.amount} XP)`, () => this.gotIt(), { class: "wb-btn-primary" }),
      button("Not quite, I'll revisit", () => this.notQuite(), { class: "wb-btn-quiet" }),
    );

    this.append(
      h("div", { class: "wb-widget-head" }, h("span", { class: "wb-widget-label" }, spec.title ?? "Your answer"), this.statusPill, this.badge),
      this.textarea,
      h("div", { class: "wb-toolbar" }, this.compareButton, this.hint, h("span", { class: "wb-spacer" }), this.revealButton),
      this.answerPanel, this.selfCheck,
    );
    this.refreshState();
    if (record.compared || record.revealed) this.showAnswer();
  }

  refreshState() {
    const record = this.record;
    const length = this.textarea.value.trim().length;
    this.badge.refresh();
    this.classList.toggle("is-passed", Boolean(record.passed));
    this.classList.toggle("is-revealed", Boolean(record.revealed));
    this.statusPill.textContent = record.passed ? "✓ Got it" : "";
    this.statusPill.className = "wb-status-pill" + (record.passed ? " is-good" : "");
    const ready = length >= this.minChars;
    this.compareButton.disabled = !ready || Boolean(record.compared || record.revealed);
    this.compareButton.hidden = Boolean(record.compared || record.revealed);
    this.hint.textContent = record.compared || record.revealed ? "" : ready ? "" : `Write at least ${this.minChars} characters, then compare.`;
    this.revealButton.hidden = Boolean(record.compared || record.revealed);
    this.revealButton.textContent = isInstructor() ? "Show answer" : `Skip and show answer (−${this.amount} XP)`;
    this.selfCheck.hidden = !(record.compared && !record.passed && !record.revealed);
  }

  compare() {
    this.record.compared = true;
    this.progress.save();
    this.showAnswer();
    this.refreshState();
  }

  reveal() {
    if (!confirmReveal(this.exerciseId, this.amount)) return;
    this.showAnswer();
    this.refreshState();
  }

  showAnswer() {
    this.answerPanel.hidden = false;
    if (this.answerPanel.childElementCount) return;
    const text = decodeBase64(this.spec.answer);
    const body = h("div", { class: "wb-answer-text" });
    for (const paragraph of text.split(/\n\s*\n/)) body.append(h("p", { html: inlineCode(paragraph) }));
    this.answerPanel.append(h("div", { class: "wb-answer-title" }, "Model answer"), body);
    this.textarea.readOnly = Boolean(this.record.revealed);
  }

  gotIt() {
    this.progress.markPassed(this.exerciseId);
    const added = this.progress.award(this.exerciseId, this.amount);
    if (added) toast(`+${added} XP`, "good");
    this.refreshState();
  }

  notQuite() {
    this.selfCheck.hidden = true;
    toast("No problem. Reread the answer and come back to it.", "info");
  }
}

/** Escape HTML and turn `code` spans into <code>. */
function inlineCode(text) {
  const escaped = text.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  return escaped.replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>");
}
