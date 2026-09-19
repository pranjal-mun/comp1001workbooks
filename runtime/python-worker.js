"use strict";

// Runs Python (Pyodide) in a Web Worker for the workbook pages and the lab.
//
// Message in:  { type: "run", id, files: [{name, content}], entry, inputs: [..],
//                echoInput: bool, check: string|null }
// Message out: { type: "ready" } | { type: "fatal", error }
//            | { type: "result", id, status: "ok"|"error"|"need-input",
//                stdout, stderr, prompt?, check?: {passed, message} }
//
// input() is replay-based: the program is run with a script of answers. When
// the script runs out, the program stops with status "need-input" and the UI
// re-runs it from the top once the student has typed the next line.

const PYODIDE_VERSION = "0.27.7";
const PYODIDE_CDN_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const PYODIDE_LOCAL_URL = new URL("../vendor/pyodide/", self.location.href).href;
const PROJECT_DIR = "/home/pyodide/project";
const MAX_OUTPUT_CHARS = 200 * 1024;

let pyodide;

initialize();

async function initialize() {
  try {
    pyodide = await loadRuntime();
    ensureProjectDirectory();
    pyodide.runPython(HARNESS);
    self.postMessage({ type: "ready" });
  } catch (error) {
    self.postMessage({ type: "fatal", error: formatError(error) });
  }
}

async function loadRuntime() {
  const forceLocal = new URLSearchParams(self.location.search).has("localAssets");
  if (!forceLocal) {
    try {
      importScripts(`${PYODIDE_CDN_URL}pyodide.js`);
      return await loadPyodide({ indexURL: PYODIDE_CDN_URL });
    } catch {
      // Continue with the local pinned runtime below.
    }
  }
  importScripts(`${PYODIDE_LOCAL_URL}pyodide.js`);
  return loadPyodide({ indexURL: PYODIDE_LOCAL_URL });
}

self.addEventListener("message", (event) => {
  const message = event.data;
  if (message?.type !== "run" || !pyodide) return;
  try {
    const result = runProject(message);
    self.postMessage({ type: "result", id: message.id, ...result });
  } catch (error) {
    self.postMessage({
      type: "result",
      id: message.id,
      status: "error",
      stdout: "",
      stderr: formatError(error),
    });
  }
});

function ensureProjectDirectory() {
  if (!pyodide.FS.analyzePath(PROJECT_DIR).exists) pyodide.FS.mkdirTree(PROJECT_DIR);
}

function clearProjectDirectory() {
  for (const name of pyodide.FS.readdir(PROJECT_DIR)) {
    if (name !== "." && name !== "..") pyodide.FS.unlink(`${PROJECT_DIR}/${name}`);
  }
}

function runProject({ files, entry, inputs = [], echoInput = false, check = null }) {
  clearProjectDirectory();
  for (const file of files) {
    pyodide.FS.writeFile(`${PROJECT_DIR}/${file.name}`, file.content, { encoding: "utf8" });
  }
  const moduleNames = files
    .filter((file) => file.name.endsWith(".py"))
    .map((file) => file.name.slice(0, -3));
  const run = pyodide.globals.get("__workbook_run");
  const resultJson = run(
    entry,
    pyodide.toPy(inputs),
    echoInput,
    check,
    pyodide.toPy(moduleNames),
    MAX_OUTPUT_CHARS,
  );
  run.destroy();
  return JSON.parse(resultJson);
}

function formatError(error) {
  return error instanceof Error ? `${error.name}: ${error.message}` : String(error);
}

// The Python side of the harness. Defined once at startup; __workbook_run is
// called for every execution with a fresh namespace.
const HARNESS = String.raw`
import builtins
import io
import json
import os
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr

PROJECT_DIR = "${PROJECT_DIR}"

class _NeedInput(BaseException):
    """Raised when input() is called and the answer script is exhausted."""
    def __init__(self, prompt):
        super().__init__(prompt)
        self.prompt = prompt

class _LimitedWriter(io.TextIOBase):
    def __init__(self, limit):
        self.limit = limit
        self.parts = []
        self.length = 0
        self.truncated = False

    def writable(self):
        return True

    def write(self, value):
        value = str(value)
        remaining = self.limit - self.length
        if remaining > 0:
            chunk = value[:remaining]
            self.parts.append(chunk)
            self.length += len(chunk)
        if len(value) > remaining:
            self.truncated = True
        return len(value)

    def flush(self):
        pass

    def getvalue(self):
        value = "".join(self.parts)
        if self.truncated:
            value += "\n[Output truncated at 200 KB]"
        return value

def _make_input(script, echo, out):
    answers = list(script)
    def scripted_input(prompt=""):
        prompt = str(prompt)
        out.write(prompt)
        if not answers:
            raise _NeedInput(prompt)
        answer = answers.pop(0)
        if echo:
            out.write(answer + "\n")
        return answer
    return scripted_input

def _format_user_traceback(exc):
    # Drop the harness frame (the exec call) so the trace starts in the
    # student's file, the way IDLE shows it.
    tb = exc.__traceback__
    if tb is not None and tb.tb_next is not None:
        tb = tb.tb_next
    return "".join(traceback.format_exception(type(exc), exc, tb))

def __workbook_run(entry, inputs, echo_input, check, module_names, output_limit):
    inputs = list(inputs)
    module_names = list(module_names)
    os.chdir(PROJECT_DIR)
    if PROJECT_DIR not in sys.path:
        sys.path.insert(0, PROJECT_DIR)
    for name in module_names:
        sys.modules.pop(name, None)

    stdout = _LimitedWriter(output_limit)
    stderr = _LimitedWriter(output_limit)
    sys.stdin = io.StringIO("\n".join(inputs) + ("\n" if inputs else ""))
    sys.argv = [entry]
    namespace = {"__name__": "__main__", "__file__": entry, "__package__": None}
    status = "ok"
    prompt = None
    check_result = None

    original_input = builtins.input
    builtins.input = _make_input(inputs, echo_input, stdout)
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                with open(entry, "rb") as source_file:
                    source = source_file.read()
                exec(compile(source, entry, "exec"), namespace)
            except _NeedInput as need:
                status = "need-input"
                prompt = need.prompt
            except SystemExit as exit_exc:
                if exit_exc.code not in (None, 0):
                    status = "error"
                    stderr.write(_format_user_traceback(exit_exc))
            except BaseException as exc:
                status = "error"
                stderr.write(_format_user_traceback(exc))

            if status == "ok" and check:
                check_result = _run_check(check, namespace, source.decode("utf-8", "replace"), stdout.getvalue())
    finally:
        builtins.input = original_input

    return json.dumps({
        "status": status,
        "stdout": stdout.getvalue(),
        "stderr": stderr.getvalue(),
        "prompt": prompt,
        "check": check_result,
    })

def _run_check(check, namespace, source, captured_stdout):
    """Run an instructor check script after the student's code.

    The script sees the student's namespace plus __source__ (the code text)
    and __stdout__ (what it printed). It reports a failure by raising
    AssertionError("message shown to the student")."""
    env = dict(namespace)
    env["__source__"] = source
    env["__stdout__"] = captured_stdout
    try:
        exec(compile(check, "<check>", "exec"), env)
    except AssertionError as failure:
        return {"passed": False, "message": str(failure) or "A check failed."}
    except Exception as failure:
        return {"passed": False, "message": f"{type(failure).__name__}: {failure}"}
    return {"passed": True, "message": ""}
`;
