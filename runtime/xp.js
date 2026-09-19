// XP: earned once per exercise for a correct answer, spent to reveal a model
// answer. The balance is shared across every workbook on this site.

const KEY = "pylab-workbooks:xp";

function read() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY));
    if (saved && typeof saved.balance === "number" && Array.isArray(saved.history)) return saved;
  } catch {
    // Fall through to the default.
  }
  return { balance: 0, history: [] };
}

function write(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    // Storage unavailable; the badge still works for this page view.
  }
}

class XP {
  constructor() {
    this.state = read();
    this.listeners = new Set();
  }

  get balance() {
    return this.state.balance;
  }

  subscribe(fn) {
    this.listeners.add(fn);
    fn(this.balance, null);
    return () => this.listeners.delete(fn);
  }

  notify(change) {
    for (const fn of this.listeners) fn(this.balance, change);
  }

  canAfford(amount) {
    return this.balance >= amount;
  }

  /** True if this exercise has already paid out (guards against earn → reset → earn). */
  hasEarned(exerciseId, workbookId) {
    return this.state.history.some((h) => h.delta > 0 && h.exercise === exerciseId && h.workbook === workbookId);
  }

  /** Award once per exercise; returns false if nothing was added. */
  earn(exerciseId, amount, workbookId) {
    if (amount <= 0 || this.hasEarned(exerciseId, workbookId)) return false;
    this.state.balance += amount;
    this.state.history.push({ at: Date.now(), workbook: workbookId, exercise: exerciseId, delta: +amount });
    write(this.state);
    this.notify({ delta: +amount, exerciseId });
    return true;
  }

  spend(exerciseId, amount, workbookId) {
    if (amount > this.balance) return false;
    this.state.balance -= amount;
    this.state.history.push({ at: Date.now(), workbook: workbookId, exercise: exerciseId, delta: -amount });
    write(this.state);
    this.notify({ delta: -amount, exerciseId });
    return true;
  }

  /** Replace the state wholesale (import). */
  load(state) {
    this.state = { balance: Number(state?.balance) || 0, history: Array.isArray(state?.history) ? state.history : [] };
    write(this.state);
    this.notify(null);
  }

  reset() {
    this.load({ balance: 0, history: [] });
  }

  snapshot() {
    return structuredClone(this.state);
  }
}

export const xp = new XP();
