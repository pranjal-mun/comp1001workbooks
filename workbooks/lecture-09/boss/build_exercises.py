"""Build workbooks/lecture-09/boss/exercises.json: the Lecture 9 boss problems.

Expected outputs are produced by actually running the model solutions. Run
from anywhere:

    python3 workbooks/lecture-09/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-09/boss
"""
import base64, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=()):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""),
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n")

def input_cases(solution, *runs):
    return [{"name": name, "inputs": list(inputs), "expected": run(solution, inputs)} for name, inputs in runs]

# Lecture 9 adds relational operators, abs() and separate if statements to
# the one if/else from Lecture 8. No elif, and no and/or yet.
NO_ELIF = 'import re\nassert not re.search(r"^\\s*elif\\b", __code__, re.M), "elif is not part of this lecture yet."\n'
NO_BOOL_OPS = ('assert not re.search(r"\\b(and|or|not)\\b", __code__), "and, or and not are not part of this lecture yet; use separate if statements."\n')

E = {}

# ---------------------------------------------------------------- 1 Tuning
tuning = """reading = float(input('Frequency (Hz): '))
difference = abs(reading - 440)
if difference <= 1:
    print(f'{reading} Hz is in tune with A4.')
else:
    print(f'{reading} Hz is {difference:.1f} Hz away from A4.')
"""
E["tuning"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 6,
    "starter": "reading = float(input('Frequency (Hz): '))\n# Report whether the reading is within 1 Hz of A4.\n",
    "cases": input_cases(tuning, ("Typed 440.5", ["440.5"]), ("Typed 445", ["445"]), ("Typed 441", ["441"]),
                         ("Typed 438.9", ["438.9"]), ("Typed 439", ["439"])),
    "check": NO_ELIF + NO_BOOL_OPS + """assert len(re.findall(r"^\\s*if\\b", __code__, re.M)) == 1 and re.search(r"^\\s*else\\s*:", __code__, re.M), "Use exactly one if with an else."
assert "abs(" in __code__, "Use abs() so that a reading below 440 and a reading above 440 are handled by the same comparison."
assert "<=" in __code__ or ">" in __code__, "A difference of exactly 1 Hz counts as in tune; check the boundary."
assert len(__stdout__.strip().splitlines()) == 1, "Print one line."
""",
    "answer": b64(tuning),
    "hints": [
        "`abs(reading - 440)` is the distance from A4 whether the reading is sharp or flat. Compare that one number with 1.",
    ],
    "answerNote": "abs() folds the two sides of 440 into one distance, so one comparison covers sharp and flat readings. The boundary 441 is in tune because the test is <=."}

# ---------------------------------------------------------------- 2 Equilateral
equilateral = """a = float(input('Side a: '))
b = float(input('Side b: '))
c = float(input('Side c: '))
kind = 'equilateral'
if a != b:
    kind = 'not equilateral'
if b != c:
    kind = 'not equilateral'
print(f'A triangle with sides {a}, {b} and {c} is {kind}.')
"""
E["equilateral"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 8,
    "starter": "a = float(input('Side a: '))\nb = float(input('Side b: '))\nc = float(input('Side c: '))\n# Report whether the triangle is equilateral.\n",
    "cases": input_cases(equilateral, ("Typed 3 3 3", ["3", "3", "3"]), ("Typed 3 4 3", ["3", "4", "3"]),
                         ("Typed 2.5 2.5 2.5", ["2.5", "2.5", "2.5"]), ("Typed 5 5 5.5", ["5", "5", "5.5"]),
                         ("Typed 6 7 8", ["6", "7", "8"])),
    "check": NO_ELIF + NO_BOOL_OPS + """assert len(re.findall(r"^\\s*if\\b", __code__, re.M)) >= 2, "Compare the sides with separate if statements, one pair per if."
assert not re.search(r"^\\s*else\\s*:", __code__, re.M), "Start with kind = 'equilateral' and let the if statements change it; no else is needed."
assert __code__.count("print(") == 1, "Print once, after the if statements."
assert "==" in __code__ or "!=" in __code__, "Compare the sides with == or !=."
""",
    "answer": b64(equilateral),
    "hints": [
        "Store `kind = 'equilateral'` first. Then an `if` that compares `a` with `b` and another that compares `b` with `c` can each change it to `'not equilateral'`. If `a` equals `b` and `b` equals `c`, then `a` equals `c` as well, so two comparisons are enough.",
    ],
    "answerNote": "Two comparisons cover all three pairs: when a == b and b == c, a == c follows. Each if overrides the default on its own, so no and is needed."}

# ---------------------------------------------------------------- 3 Phone bill
phone = """minutes = int(input('Minutes: '))
texts = int(input('Texts: '))
base = 15.00
fee = 0.44
subtotal = base + fee
print(f'Base plan: ${base:.2f}')
if minutes > 50:
    extra_minutes = (minutes - 50) * 0.25
    subtotal = subtotal + extra_minutes
    print(f'Extra minutes: ${extra_minutes:.2f}')
if texts > 50:
    extra_texts = (texts - 50) * 0.15
    subtotal = subtotal + extra_texts
    print(f'Extra texts: ${extra_texts:.2f}')
tax = subtotal * 0.15
print(f'911 fee: ${fee:.2f}')
print(f'Tax: ${tax:.2f}')
print(f'Total: ${subtotal + tax:.2f}')
"""
E["phone"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 12,
    "starter": "minutes = int(input('Minutes: '))\ntexts = int(input('Texts: '))\n# Print the bill, one charge per line.\n",
    "cases": input_cases(phone, ("Typed 60 and 70", ["60", "70"]), ("Typed 50 and 50", ["50", "50"]),
                         ("Typed 120 and 10", ["120", "10"]), ("Typed 0 and 51", ["0", "51"]),
                         ("Typed 51 and 51", ["51", "51"])),
    "check": NO_ELIF + NO_BOOL_OPS + """assert len(re.findall(r"^\\s*if\\b", __code__, re.M)) == 2, "Use two separate if statements: one for the extra minutes and one for the extra texts."
assert not re.search(r"^\\s*else\\s*:", __code__, re.M), "No else is needed: when there is no extra charge, nothing is printed for it."
assert re.search(r":[^}]*\\.2f\\}", __source__), "Show every amount with two decimal places."
lines = __stdout__.strip().splitlines()
assert 4 <= len(lines) <= 6, "Print the base plan, any extra charges, the 911 fee, the tax and the total, one per line."
assert "Base plan:" in lines[0] and lines[-1].startswith("Total:"), "Start with the base plan and end with the total."
""",
    "answer": b64(phone),
    "hints": [
        "Keep a running `subtotal` that starts at 15.00 + 0.44. Each `if` adds its extra charge to it and prints its own line. The tax is 15 percent of the subtotal, and the total is the subtotal plus the tax.",
        "The extra minutes cost `(minutes - 50) * 0.25`, but only when `minutes > 50`. A plan with exactly 50 minutes has no extra charge, so 50 must not print a line.",
        "`${extra_minutes:.2f}` prints the amount with two decimals. Only print an extra line when there is an extra charge, so put the print inside the if.",
    ],
    "answerNote": "Each if adds its charge to the subtotal and prints its own line, so the tax and total come out right whether zero, one or both extras apply."}

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-09-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 9 Boss Problems",
    "short": "L09 bosses",
    "subtitle": "Relational operators and comparing values",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-09/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
