// Per-workbook progress: each exercise's saved work, pass/reveal state, and
// what it has earned. Persisted in localStorage; exportable as JSON.

import { xp } from "./xp.js";

const PREFIX = "pylab-workbooks:progress:";

export class Progress {
  constructor(workbookId) {
    this.workbookId = workbookId;
    this.key = PREFIX + workbookId;
    this.state = this.read();
    this.listeners = new Set();
    this.saveTimer = null;
  }

  read() {
    try {
      const saved = JSON.parse(localStorage.getItem(this.key));
      if (saved && typeof saved.exercises === "object") return saved;
    } catch {
      // Fall through to the default.
    }
    return { exercises: {} };
  }

  save() {
    clearTimeout(this.saveTimer);
    this.saveTimer = null;
    try {
      localStorage.setItem(this.key, JSON.stringify(this.state));
    } catch {
      // Storage unavailable or full; work stays in memory for this page view.
    }
  }

  scheduleSave() {
    clearTimeout(this.saveTimer);
    this.saveTimer = setTimeout(() => this.save(), 300);
  }

  /** Per-exercise record: {work, passed, revealed, earned, cells}. */
  get(id) {
    return this.state.exercises[id] ?? (this.state.exercises[id] = {});
  }

  /** Save a student's draft (code text, table cells, or written answer). */
  setWork(id, work) {
    this.get(id).work = work;
    this.scheduleSave();
  }

  markPassed(id) {
    const record = this.get(id);
    if (!record.passed) {
      record.passed = true;
      this.save();
      this.notify();
    }
  }

  markRevealed(id) {
    const record = this.get(id);
    if (!record.revealed) {
      record.revealed = true;
      this.save();
      this.notify();
    }
  }

  /**
   * Award XP once for this exercise (or once per named part, e.g. a table
   * cell). Returns the XP actually added: 0 if already earned or revealed.
   */
  award(id, amount, part = null) {
    const record = this.get(id);
    if (record.revealed) return 0;
    if (part == null) {
      if (record.earned) return 0;
      record.earned = amount;
    } else {
      record.parts ??= {};
      if (record.parts[part]) return 0;
      record.parts[part] = amount;
    }
    this.save();
    const added = xp.earn(part == null ? id : `${id}#${part}`, amount, this.workbookId);
    this.notify();
    return added ? amount : 0;
  }

  /** True once every listed part has paid out. */
  hasEarnedPart(id, part) {
    return Boolean(this.state.exercises[id]?.parts?.[part]);
  }

  reveal(id, cost) {
    const record = this.get(id);
    if (record.revealed) return true;
    if (!xp.spend(id, cost, this.workbookId)) return false;
    record.revealed = true;
    this.save();
    this.notify();
    return true;
  }

  /** Clear saved work and pass state; what was earned or revealed stays. */
  resetExercise(id) {
    const record = this.state.exercises[id];
    if (record) {
      delete record.work;
      delete record.passed;
      delete record.compared;
    }
    this.save();
    this.notify();
  }

  resetAll() {
    this.state = { exercises: {} };
    this.save();
    this.notify();
  }

  subscribe(fn) {
    this.listeners.add(fn);
    fn(this);
    return () => this.listeners.delete(fn);
  }

  notify() {
    for (const fn of this.listeners) fn(this);
  }

  /** Counts for the progress bar: done = passed or revealed. */
  summary(ids) {
    let done = 0;
    for (const id of ids) {
      const record = this.state.exercises[id];
      if (record?.passed || record?.revealed) done++;
    }
    return { done, total: ids.length };
  }

  exportJSON() {
    return JSON.stringify({ format: "pylab-workbooks-progress/1", exportedAt: new Date().toISOString(), workbook: this.workbookId, progress: this.state, xp: xp.snapshot() }, null, 2);
  }

  importJSON(text) {
    const data = JSON.parse(text);
    if (data?.format !== "pylab-workbooks-progress/1") throw new Error("This file is not a workbook progress export.");
    if (data.workbook !== this.workbookId) throw new Error(`This file is for workbook "${data.workbook}", not "${this.workbookId}".`);
    this.state = data.progress && typeof data.progress.exercises === "object" ? data.progress : { exercises: {} };
    this.save();
    if (data.xp) xp.load(data.xp);
    this.notify();
  }
}
