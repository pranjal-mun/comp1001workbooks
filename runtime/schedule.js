// The course schedule: units, lectures, their dates, and which workbooks are
// posted. The landing page draws its dashboard from this, and a workbook
// page stays locked until the previous lecture's class has ended, so students
// can read one lecture ahead (instructor mode, see instructor.js, ignores the
// lock).
//
// When a new workbook is finished, set its `built` flag here. That is the
// only edit a lecture branch makes outside its own workbook folder. A lecture
// with `bosses: true` also has boss problems at workbooks/lecture-NN/boss/
// (workbook id lecture-NN-boss), which open at the same time as the workbook.

// Class ends at 10:50 local time; the next workbook opens then.
export const CLASS_END = { hour: 10, minute: 50 };

export const UNITS = [
  { n: 1, name: "Problem solving and a first program" },
  { n: 2, name: "Values, expressions, input and output" },
  { n: 3, name: "Decisions" },
  { n: 4, name: "Loops" },
  { n: 5, name: "Functions" },
  { n: 6, name: "Recursion" },
  { n: 7, name: "Lists, searching and sorting" },
  { n: 8, name: "Exceptions and files" },
  { n: 9, name: "Collections, objects and review" },
];

// Titles may contain <code>…</code>; they are inserted as HTML.
export const LECTURES = [
  { n: 1, unit: 1, date: "2026-09-09", title: "Course introduction, computers and software", built: true },
  { n: 2, unit: 1, date: "2026-09-11", title: "Problem solving: from understanding to reflection", built: true },
  { n: 3, unit: 1, date: "2026-09-14", title: "Algorithms, pseudocode and programs", built: true },
  { n: 4, unit: 2, date: "2026-09-16", title: "Variables, types, and assignment", built: true, bosses: true },
  { n: 5, unit: 2, date: "2026-09-18", title: "Arithmetic, expressions, and modules", built: true, bosses: true },
  { n: 6, unit: 2, date: "2026-09-21", title: "Input and output, and f-strings", built: true, bosses: true },
  { n: 7, unit: 2, date: "2026-09-23", title: "Strings", built: true, bosses: true },
  { n: 8, unit: 3, date: "2026-09-25", title: "Problem solving with decisions: the if statement", built: true, bosses: true },
  { n: 9, unit: 3, date: "2026-09-28", title: "Relational operators and comparing values", built: true },
  { n: 10, unit: 3, date: "2026-10-02", title: "Nested branches and elif chains", built: true },
  { n: 11, unit: 3, date: "2026-10-05", title: "Boolean operators, <code>bool</code>, and input validation", built: true },
  { n: 12, unit: 4, date: "2026-10-07", title: "The <code>while</code> loop", built: false },
  { n: 13, unit: 4, date: "2026-10-09", title: "Hand-tracing, sentinels, common loop bugs", built: false },
  { n: 14, unit: 4, date: "2026-10-14", title: "The <code>for</code> loop and ranges", built: false },
  { n: 15, unit: 4, date: "2026-10-16", title: "Nested loops, <code>break</code> and <code>continue</code>", built: false },
  { n: 16, unit: 4, date: "2026-10-19", title: "Loop algorithms, random numbers", built: false },
  { n: 17, unit: 5, date: "2026-10-21", title: "Functions as black boxes; decomposition", built: false },
  { n: 18, unit: 5, date: "2026-10-23", title: "Parameters and return values", built: false },
  { n: 19, unit: 5, date: "2026-10-26", title: "Argument styles, <code>main()</code>, the call stack", built: false },
  { n: 20, unit: 5, date: "2026-10-28", title: "Stepwise refinement and scope", built: false },
  { n: 21, unit: 6, date: "2026-10-30", title: "The recursive idea; base cases", built: false },
  { n: 22, unit: 6, date: "2026-11-02", title: "Tracing recursion; recursive helpers", built: false },
  { n: 23, unit: 6, date: "2026-11-04", title: "Recursion vs iteration; Towers of Hanoi", built: false },
  { n: 24, unit: 7, date: "2026-11-06", title: "Lists: properties and operations", built: false },
  { n: 25, unit: 7, date: "2026-11-09", title: "List algorithms, slices, comprehensions", built: false },
  { n: 26, unit: 7, date: "2026-11-13", title: "Lists with functions; tables", built: false },
  { n: 27, unit: 7, date: "2026-11-16", title: "Linear and binary search", built: false },
  { n: 28, unit: 7, date: "2026-11-18", title: "Selection sort and merge sort", built: false },
  { n: 29, unit: 8, date: "2026-11-20", title: "Exceptions: what they are; <code>try</code> / <code>except</code>", built: false },
  { n: 30, unit: 8, date: "2026-11-23", title: "<code>raise</code>, <code>else</code>, <code>finally</code>; reading tracebacks", built: false },
  { n: 31, unit: 8, date: "2026-11-25", title: "Input validation and robust programs", built: false },
  { n: 32, unit: 8, date: "2026-11-27", title: "Reading and writing text files", built: false },
  { n: 33, unit: 8, date: "2026-11-30", title: "Processing text; files that fail safely", built: false },
  { n: 34, unit: 9, date: "2026-12-02", title: "Sets and dictionaries", built: false },
  { n: 35, unit: 9, date: "2026-12-04", title: "Objects and classes", built: false },
  { n: 36, unit: 9, date: "2026-12-07", title: "Course review", built: false },
];

export const KEY_DATES = [
  { name: "Term Test 1", date: "2026-10-15", note: "Lectures 1 to 13, in your lab slot" },
  { name: "Term Test 2", date: "2026-11-10", note: "Lectures 1 to 23, in your lab slot" },
  { name: "Last day to drop", date: "2026-11-04" },
  { name: "Final examination", when: "Dec 10 to 18", note: "Registrar-scheduled" },
];

export const workbookId = (n) => `lecture-${String(n).padStart(2, "0")}`;
export const bossId = (n) => `${workbookId(n)}-boss`;

export function lecture(n) {
  return LECTURES.find((l) => l.n === n) ?? null;
}

/** The schedule entry for a workbook id such as "lecture-04" or "lecture-04-boss", or null. */
export function lectureFor(id) {
  const m = /^lecture-(\d+)(?:-boss)?$/.exec(id ?? "");
  return m ? lecture(Number(m[1])) : null;
}

/**
 * Local time at which the workbook for this lecture opens: the end of the
 * previous lecture's class, so the upcoming workbook is always available.
 * The first lecture opens at the start of its own day.
 */
export function opensAt(entry) {
  const prev = LECTURES.filter((l) => l.date < entry.date).pop();
  if (!prev) return new Date(`${entry.date}T00:00:00`);
  const d = new Date(`${prev.date}T00:00:00`);
  d.setHours(CLASS_END.hour, CLASS_END.minute, 0, 0);
  return d;
}

export function isOpen(entry, now = new Date()) {
  return now >= opensAt(entry);
}

/** "Wed, Oct 7" style; pass `weekday: null` for "Oct 7". */
export function fmtDate(iso, { weekday = "short" } = {}) {
  return new Date(`${iso}T12:00:00`).toLocaleDateString("en-CA", { ...(weekday ? { weekday } : {}), month: "short", day: "numeric" });
}

export function fmtOpens(entry) {
  const t = opensAt(entry);
  const date = t.toLocaleDateString("en-CA", { weekday: "short", month: "short", day: "numeric" });
  const time = t.toLocaleTimeString("en-CA", { hour: "numeric", minute: "2-digit" });
  return `${date} at ${time}`;
}
