"""Build workbooks/lecture-01/exercises.json.

Lecture 1 is the course introduction: it has no questions and awards no XP.
The only widget is the runnable `add_five` example from the "Python and
interpretation" slide; its output is produced by running the code so the
page cannot drift from Python's behaviour. Run from anywhere:

    python3 workbooks/lecture-01/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-01
"""
import json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def run(code):
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n")

def example(code, **kw):
    code = code.rstrip("\n")
    return {"type": "example", "code": code, "output": run(code), **kw}

E = {}

E["ex-add-five"] = example('''def add_five(x):
    return x + 5

print(add_five(10))
print(add_five(37))
''', title="add_five.py")

data = {
    "id": "lecture-01",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 1 Workbook",
    "subtitle": "Course Introduction, Computers and Software",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-01/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
