"""Build workbooks/lecture-04/boss/exercises.json: the Lecture 4 boss problems.

Expected outputs are produced by actually running the model solutions. Run
from anywhere:

    python3 workbooks/lecture-04/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-04/boss
"""
import base64, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code):
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n")

def rewritten(code, *pairs):
    for old, new in pairs:
        assert old in code, old
        code = code.replace(old, new)
    return code

def cases(solution, first, *others):
    """One case per set of values. `first` names the values as written in the
    starter; every other set is a list of [from, to] rewrites of those lines."""
    out = [{"name": first, "expected": run(solution)}]
    for name, pairs in others:
        out.append({"name": name, "rewrite": pairs, "expected": run(rewritten(solution, *pairs))})
    return out

NO_AUGMENTED = 'assert "+=" not in __source__, "Write the update in full, as in count = count + 1; the += shortcut comes later."\n'

E = {}

# ---------------------------------------------------------------- 1 Swap
swap = """oliver = 'sofa'
sabina = 'basket'
holder = oliver
oliver = sabina
sabina = holder
print(oliver, sabina)
"""
E["swap"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 6,
    "starter": "oliver = 'sofa'\nsabina = 'basket'\n# Make the two pets trade places, then print where each one is.\n",
    "cases": cases(swap, "sofa and basket",
        ("bed and windowsill", [["oliver = 'sofa'", "oliver = 'bed'"], ["sabina = 'basket'", "sabina = 'windowsill'"]]),
        ("porch and kitchen", [["oliver = 'sofa'", "oliver = 'porch'"], ["sabina = 'basket'", "sabina = 'kitchen'"]]),
        ("rug and rug", [["oliver = 'sofa'", "oliver = 'rug'"], ["sabina = 'basket'", "sabina = 'rug'"]])),
    "check": NO_AUGMENTED + """import re
assert not re.search(r"^\\s*\\w+\\s*,\\s*\\w+\\s*=", __source__, re.M), "Swap with a third variable, one assignment at a time; the a, b = b, a form comes later."
names = [k for k in globals() if not k.startswith("__") and k != "re"]
assert len(names) >= 3, "Use a third variable to hold one of the values while you swap."
assert len(__stdout__.strip().splitlines()) == 1, "Print both values with one print() call so they land on one line."
""",
    "answer": b64(swap),
    "answerNote": "The moment oliver is overwritten its old value is gone, so a third name keeps a copy first."}

# ---------------------------------------------------------------- 2 Seats
seats = """seated = 0
group_1 = 40
group_2 = 25
group_3 = 55
seated = seated + group_1
print('After group 1:', seated)
seated = seated + group_2
print('After group 2:', seated)
seated = seated + group_3
print('After group 3:', seated)
"""
E["seats"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 10,
    "starter": "seated = 0\ngroup_1 = 40\ngroup_2 = 25\ngroup_3 = 55\n# Seat each group and report the count.\n",
    "cases": cases(seats, "40, 25, 55",
        ("0, 60, 60", [["group_1 = 40", "group_1 = 0"], ["group_2 = 25", "group_2 = 60"], ["group_3 = 55", "group_3 = 60"]]),
        ("50, -10, 80", [["group_1 = 40", "group_1 = 50"], ["group_2 = 25", "group_2 = -10"], ["group_3 = 55", "group_3 = 80"]]),
        ("120, 0, 0", [["group_1 = 40", "group_1 = 120"], ["group_2 = 25", "group_2 = 0"], ["group_3 = 55", "group_3 = 0"]])),
    "check": NO_AUGMENTED + """import re
updates = re.findall(r"^\\s*seated\\s*=\\s*seated\\s*\\+", __source__, re.M)
assert len(updates) == 3, "Update the running count three times, once per group, in the form seated = seated + ..."
assert len(__stdout__.strip().splitlines()) == 3, "Print exactly three lines, one after each group."
assert type(seated) is int, "seated should still be a whole number (an int) at the end."
""",
    "answer": b64(seats),
    "answerNote": "Each update reads the old count, adds one group, and stores the result back under the same name."}

# ---------------------------------------------------------------- 3 Vet record
vet = """pet = 'Oliver'
age = 7
weight = 3.5
vaccinated = True
print(pet, type(pet))
print(age, type(age))
print(weight, type(weight))
print(vaccinated, type(vaccinated))
"""
E["vet"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 8,
    "starter": "pet = 'Oliver'\nage = 7\nweight = 3.5\nvaccinated = True\n# Print each value followed by its type.\n",
    "cases": cases(vet, "Oliver, as given",
        ("Sabina, age unknown", [["pet = 'Oliver'", "pet = 'Sabina'"], ["age = 7", "age = 'unknown'"], ["weight = 3.5", "weight = 4"]]),
        ("half years, text flag", [["age = 7", "age = 7.5"], ["vaccinated = True", "vaccinated = 'yes'"]]),
        ("tag number, quoted weight", [["pet = 'Oliver'", "pet = 1001"], ["weight = 3.5", "weight = '3.5'"]])),
    "check": """import re
assert "type(" in __source__, "Ask Python for each type with type(); do not type the answer in yourself."
assert "class" not in __source__ and not re.search(r"\\b(int|float|str|bool)\\b", __source__), "The type names must come from type() at run time, not from text you typed."
assert len(__stdout__.strip().splitlines()) == 4, "Print four lines, one per field, in the order given."
""",
    "answer": b64(vet),
    "answerNote": "The type belongs to the value, not the name, so the same four lines report whatever is assigned that run."}

# ---------------------------------------------------------------- 4 Repair
repair_starter = """# course record
lecture room = 'EN2043'
class = 'COMP 1001'
instructor-name = 'Pranjal Patra'
students = 119
students = Students + 1
print(lecture room, class, instructor-name, students)
"""
repair = """# The room is booked for the whole term, so it is a constant.
ROOM = 'EN2043'
course_code = 'COMP 1001'
instructor_name = 'Pranjal Patra'
students = 119
students = students + 1
print(ROOM, course_code, instructor_name, students)
"""
E["repair"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 7,
    "starter": repair_starter,
    "cases": cases(repair, "119 students",
        ("0 students", [["students = 119", "students = 0"]]),
        ("57 students", [["students = 119", "students = 57"]])),
    "check": NO_AUGMENTED + """import re
user = {k: v for k, v in globals().items() if not k.startswith("__") and k != "re"}
for k in user:
    assert len(k) > 1, f"The name {k} is too short to be meaningful."
    assert re.fullmatch(r"[a-z][a-z0-9_]*", k) or re.fullmatch(r"[A-Z][A-Z0-9_]*", k), f"Write {k} in lower_case_with_underscores (or ALL_CAPS if it is a constant)."
constants = {k: v for k, v in user.items() if k == k.upper()}
assert constants, "The room does not change all term, so store it under an ALL_CAPS name (for example ROOM)."
assert any(v == "EN2043" for v in constants.values()), "Keep the room EN2043 in the constant."
assert re.search(r"^\\s*students\\s*=\\s*students\\s*\\+\\s*1", __source__, re.M), "Keep the update students = students + 1; fix the spelling rather than typing in the new count."
assert any(line.strip().startswith("#") for line in __source__.splitlines()), "Keep one comment that explains a choice (a line starting with #)."
""",
    "answer": b64(repair),
    "answerNote": "Five repairs: the space, the keyword class, the hyphen, the ALL_CAPS constant, and the capital S in Students."}

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-04-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 4 Boss Problems",
    "short": "L04 bosses",
    "subtitle": "Variables, types, and assignment",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-04/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
