// Checking: expected-output comparison, multi-case runs with rewrites and
// scripted input, instructor check scripts, and answer-cell matching.

import { runner } from "./runner.js";

/** Trailing whitespace per line and trailing blank lines are ignored. */
export function normalizeOutput(text) {
  return String(text ?? "")
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .map((line) => line.replace(/\s+$/, ""))
    .join("\n")
    .replace(/\n+$/, "");
}

/** Line-by-line comparison. Returns {pass, lines: [{expected, actual, ok}]}. */
export function compareOutput(expected, actual) {
  const want = normalizeOutput(expected).split("\n");
  const got = normalizeOutput(actual).split("\n");
  const count = Math.max(want.length, got.length);
  const lines = [];
  let pass = true;
  for (let i = 0; i < count; i++) {
    const ok = want[i] === got[i];
    if (!ok) pass = false;
    lines.push({ expected: want[i], actual: got[i], ok });
  }
  return { pass, lines };
}

/** Apply [from, to] literal rewrites to the student's source (case setup). */
export function applyRewrites(source, rewrites = []) {
  let result = source;
  for (const [from, to] of rewrites) {
    if (!result.includes(from)) {
      throw new Error(`This check expects the line \`${from}\` in your code so it can try a different starting value. Keep that line as given.`);
    }
    result = result.split(from).join(to);
  }
  return result;
}

/**
 * Run every case of a coding exercise. Each case: {name, inputs, expected,
 * rewrite, check}. A spec-level `check` script applies to every case.
 * Returns {pass, cases: [{name, pass, error, comparison, checkMessage, stdout, stderr, inputs}]}.
 */
export async function runCases(spec, source, files = []) {
  const cases = spec.cases?.length ? spec.cases : [{ name: "Program output", expected: spec.expected ?? "" }];
  const results = [];
  for (const testCase of cases) {
    const outcome = { name: testCase.name || "Case", pass: false, inputs: testCase.inputs ?? [] };
    try {
      const code = applyRewrites(source, testCase.rewrite);
      const project = [{ name: "main.py", content: code }, ...files.filter((f) => f.name !== "main.py")];
      const check = [spec.check, testCase.check].filter(Boolean).join("\n\n") || null;
      const result = await runner.run({ files: project, entry: "main.py", inputs: outcome.inputs, echoInput: false, check });
      outcome.stdout = result.stdout;
      outcome.stderr = result.stderr;
      if (result.status === "need-input") {
        outcome.error = "Your program asked for more input than this case provides.";
      } else if (result.status === "error") {
        outcome.error = "Your program stopped with an error.";
      } else {
        if (testCase.expected != null) {
          outcome.comparison = compareOutput(testCase.expected, result.stdout);
        }
        if (result.check && !result.check.passed) outcome.checkMessage = result.check.message;
        outcome.pass = (outcome.comparison?.pass ?? true) && !outcome.checkMessage;
      }
    } catch (error) {
      outcome.error = error.message;
    }
    results.push(outcome);
  }
  return { pass: results.every((r) => r.pass), cases: results };
}

/** Normalize a typed answer for comparison with accepted answers. */
export function normalizeAnswer(text, { caseSensitive = false } = {}) {
  let value = String(text ?? "").trim().replace(/\s+/g, " ");
  const classMatch = value.match(/^<class\s+['"]([^'"]+)['"]>$/i);
  if (classMatch) value = classMatch[1];
  if (!caseSensitive) value = value.toLowerCase();
  return value;
}

/** True if `answer` matches any of the accepted forms. */
export function matchAnswer(answer, accepted, options) {
  const given = normalizeAnswer(answer, options);
  if (!given) return false;
  return accepted.some((form) => normalizeAnswer(form, options) === given);
}
