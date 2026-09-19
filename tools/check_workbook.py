#!/usr/bin/env python3
"""Verify a workbook's exercises.json against a real Python interpreter.

    python3 tools/check_workbook.py workbooks/lecture-04

For every example with an `output`, runs its code and compares. For every
code exercise with a model `answer`, runs the answer through each case
(inputs, rewrite, expected, check script) exactly as the browser grader does
and reports any case the model answer would fail. Exit status 1 on failure.
"""
import base64
import io
import json
import pathlib
import sys
import traceback


def decode(text):
    return base64.b64decode("".join(text.split())).decode("utf-8")


def normalize(text):
    lines = [line.rstrip() for line in str(text or "").replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def run(source, inputs=(), check=None):
    """Mirror runtime/python-worker.js: scripted input(), captured stdout, check script."""
    answers = list(inputs)
    out = io.StringIO()
    namespace = {"__name__": "__main__", "__file__": "main.py"}

    def scripted_input(prompt=""):
        out.write(str(prompt))
        if not answers:
            raise RuntimeError("input() called with no scripted answer left")
        return answers.pop(0)

    import builtins
    original_input, original_stdout = builtins.input, sys.stdout
    builtins.input, sys.stdout = scripted_input, out
    status, check_message = "ok", None
    try:
        try:
            exec(compile(source, "main.py", "exec"), namespace)
        except BaseException as exc:  # noqa: BLE001 - report any failure
            status = "error"
            out.write(traceback.format_exc())
        if status == "ok" and check:
            env = dict(namespace)
            env["__source__"] = source
            env["__stdout__"] = out.getvalue()
            try:
                exec(compile(check, "<check>", "exec"), env)
            except AssertionError as failure:
                check_message = str(failure) or "A check failed."
            except Exception as failure:  # noqa: BLE001
                check_message = f"{type(failure).__name__}: {failure}"
    finally:
        builtins.input, sys.stdout = original_input, original_stdout
    return status, out.getvalue(), check_message


def apply_rewrites(source, rewrites):
    for old, new in rewrites or []:
        if old not in source:
            raise ValueError(f"rewrite target not found: {old!r}")
        source = source.replace(old, new)
    return source


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    path = pathlib.Path(argv[0])
    if path.is_dir():
        path = path / "exercises.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    failures = 0
    checked = 0
    for eid, spec in data["exercises"].items():
        kind = spec.get("type")
        if kind == "example" and spec.get("output") is not None:
            checked += 1
            status, stdout, _ = run(spec["code"])
            if normalize(stdout) != normalize(spec["output"]):
                failures += 1
                print(f"FAIL example {eid}: output differs\n--- expected\n{spec['output']}\n--- actual\n{stdout}")
        elif kind == "code" and spec.get("answer"):
            answer = decode(spec["answer"])
            cases = spec.get("cases") or [{"name": "Program output", "expected": spec.get("expected", "")}]
            for case in cases:
                checked += 1
                try:
                    source = apply_rewrites(answer, case.get("rewrite"))
                except ValueError as error:
                    failures += 1
                    print(f"FAIL {eid} / {case.get('name')}: {error}")
                    continue
                check = "\n\n".join(filter(None, [spec.get("check"), case.get("check")])) or None
                status, stdout, message = run(source, case.get("inputs", ()), check)
                ok = status == "ok" and not message
                if ok and case.get("expected") is not None:
                    ok = normalize(stdout) == normalize(case["expected"])
                if not ok:
                    failures += 1
                    print(f"FAIL {eid} / {case.get('name')}: status={status} check={message!r}\n--- expected\n{case.get('expected')}\n--- actual\n{stdout}")
    print(f"{checked} checks, {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
