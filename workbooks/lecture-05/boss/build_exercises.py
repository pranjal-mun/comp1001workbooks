"""Build workbooks/lecture-05/boss/exercises.json: the Lecture 5 boss problems.

Expected outputs are produced by actually running the model solutions. Run
from anywhere:

    python3 workbooks/lecture-05/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-05/boss
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

QUALIFIED_MATH = '''import re
lines = [l.strip() for l in __source__.split("\\n")]
assert "import math" in lines, "Use the preferred course form: a line `import math` on its own."
assert not any(l.startswith("from math import") for l in lines), "Use `import math`, not `from math import ...`, so the module name stays visible."
'''

E = {}

# ---------------------------------------------------------------- 1 Digits
digits = """number = 3141
d1 = number // 1000
d2 = number // 100 % 10
d3 = number // 10 % 10
d4 = number % 10
total = d1 + d2 + d3 + d4
print(d1, "+", d2, "+", d3, "+", d4, "=", total)
"""
E["digits"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 7,
    "starter": "number = 3141\n# Take the number apart, one digit at a time.\n",
    "cases": cases(digits, "3141",
        ("9075", [["number = 3141", "number = 9075"]]),
        ("1000", [["number = 3141", "number = 1000"]]),
        ("2026", [["number = 3141", "number = 2026"]])),
    "check": '''assert "//" in __source__ and "%" in __source__, "Peel the digits off with // and %; do not turn the number into text."
assert "str(" not in __source__, "Peel the digits off with // and %; do not turn the number into text."
assert "if" not in __source__.split(), "No if statements are needed: // and % do all the work."
assert len(__stdout__.strip().splitlines()) == 1, "Print the whole sum on one line with one print() call."''',
    "answer": b64(digits),
    "answerNote": "number // 100 % 10 reads: drop the last two digits, then keep only the last one that remains."}

# ---------------------------------------------------------------- 2 Change
change = """cents = 1234
toonies = cents // 200
cents = cents % 200
loonies = cents // 100
cents = cents % 100
quarters = cents // 25
cents = cents % 25
dimes = cents // 10
cents = cents % 10
nickels = cents // 5
pennies = cents % 5
print("Toonies:", toonies)
print("Loonies:", loonies)
print("Quarters:", quarters)
print("Dimes:", dimes)
print("Nickels:", nickels)
print("Pennies:", pennies)
"""
E["change"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 14,
    "starter": "cents = 1234\n# Work out the coins, largest first.\n",
    "cases": cases(change, "1234 cents",
        ("999 cents", [["cents = 1234", "cents = 999"]]),
        ("5 cents", [["cents = 1234", "cents = 5"]]),
        ("388 cents", [["cents = 1234", "cents = 388"]])),
    "check": '''assert "//" in __source__ and "%" in __source__, "Use // for how many coins fit and % for what is left over."
assert "if" not in __source__.split(), "No if statements are needed: // and % do all the work."
assert len(__stdout__.strip().splitlines()) == 6, "Print exactly six lines, one per coin, largest coin first."''',
    "answer": b64(change),
    "answerNote": "Each coin takes what it can with //, and % leaves the rest for the next smaller coin."}

# ---------------------------------------------------------------- 3 Sort
sort3 = """a = 17
b = 4
c = 9
smallest = min(a, b, c)
largest = max(a, b, c)
middle = a + b + c - smallest - largest
print(smallest, middle, largest)
"""
E["sort3"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 7,
    "starter": "a = 17\nb = 4\nc = 9\n# Print the three values from smallest to largest.\n",
    "cases": cases(sort3, "17, 4, 9",
        ("3, 8, 3", [["a = 17", "a = 3"], ["b = 4", "b = 8"], ["c = 9", "c = 3"]]),
        ("-2, 10, 0", [["a = 17", "a = -2"], ["b = 4", "b = 10"], ["c = 9", "c = 0"]]),
        ("5, 5, 5", [["a = 17", "a = 5"], ["b = 4", "b = 5"], ["c = 9", "c = 5"]])),
    "check": '''assert "min(" in __source__ and "max(" in __source__, "Use min() for the smallest value and max() for the largest."
assert "sort" not in __source__, "No sorting: min, max, and a subtraction are enough."
assert "if" not in __source__.split(), "No if statements: min, max, and a subtraction are enough."
assert len(__stdout__.strip().splitlines()) == 1, "Print all three values with one print() call so they land on one line."''',
    "answer": b64(sort3),
    "answerNote": "The three values add up to smallest + middle + largest, so taking away the two you already know leaves the middle."}

# ---------------------------------------------------------------- 4 Earth
earth = """import math
lat1 = 47.5615
lon1 = -52.7126
lat2 = 45.4215
lon2 = -75.6972
t1 = math.radians(lat1)
g1 = math.radians(lon1)
t2 = math.radians(lat2)
g2 = math.radians(lon2)
distance = 6371.01 * math.acos(math.sin(t1) * math.sin(t2) + math.cos(t1) * math.cos(t2) * math.cos(g1 - g2))
print(round(distance, 1))
"""
vancouver = [["lat2 = 45.4215", "lat2 = 49.2827"], ["lon2 = -75.6972", "lon2 = -123.1207"]]
london = [["lat2 = 45.4215", "lat2 = 51.5074"], ["lon2 = -75.6972", "lon2 = -0.1278"]]
sydney = [["lat2 = 45.4215", "lat2 = -33.8688"], ["lon2 = -75.6972", "lon2 = 151.2093"]]
E["earth"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 10,
    "starter": "lat1 = 47.5615\nlon1 = -52.7126\nlat2 = 45.4215\nlon2 = -75.6972\n# Convert to radians, then apply the formula.\n",
    "cases": cases(earth, "St. John's to Ottawa",
        ("St. John's to Vancouver", vancouver),
        ("St. John's to London", london),
        ("St. John's to Sydney", sydney)),
    "check": QUALIFIED_MATH + '''assert "math.acos" in __source__, "The formula needs the inverse cosine: math.acos."
assert "math.radians" in __source__, "Convert each angle from degrees to radians with math.radians before using sin and cos."
assert "round(" in __source__, "Round the distance to one decimal place with round(..., 1)."''',
    "answer": b64(earth),
    "answerNote": "Forgetting math.radians is the classic mistake: sin and cos expect radians, and the distances come out wildly wrong."}

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-05-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 5 Boss Problems",
    "short": "L05 bosses",
    "subtitle": "Arithmetic, expressions, and modules",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-05/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
