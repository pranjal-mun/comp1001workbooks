"""Build workbooks/lecture-12/boss/exercises.json: the Lecture 12 boss problems.

The problems are the Boss Problems section of the kit's
LECTURE_12_SHARED_CONTENT.tex, in the kit's order. Expected outputs are
produced by actually running the model solutions. Run from anywhere:

    python3 workbooks/lecture-12/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-12/boss
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

# Lecture 12 teaches the while loop. Every boss repeats with while, not for.
WHILE_ONLY = '''import re
assert re.search(r"^\\s*while\\b", __source__, re.M), "Repeat the work with a while loop."
assert not re.search(r"^\\s*for\\b", __source__, re.M), "Use a while loop; for is not part of this lecture."
'''

E = {}

# ---------------------------------------------------------------- 1 Campus Shop Clearance Table
clearance = """DISCOUNT_RATE = 0.25
price = float(input('First price: $'))
rows = int(input('Rows: '))
count = 0

print('Original  Discount  Sale')
while count < rows:
    discount = price * DISCOUNT_RATE
    sale_price = price - discount
    print(f'${price:.2f}  ${discount:.2f}  ${sale_price:.2f}')
    price = price + 5
    count = count + 1
"""
E["clearance"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 12,
    "starter": "DISCOUNT_RATE = 0.25\nprice = float(input('First price: $'))\nrows = int(input('Rows: '))\ncount = 0\n\nprint('Original  Discount  Sale')\n\n# Write the loop here.\n",
    "cases": input_cases(clearance, ("Typed 20 and 3", ["20", "3"]), ("Typed 12.5 and 0", ["12.5", "0"]),
                         ("Typed 9.99 and 2", ["9.99", "2"]), ("Typed 4 and 1", ["4", "1"])),
    "check": WHILE_ONLY + """assert __source__.count("DISCOUNT_RATE") >= 2, "Work out the discount with price * DISCOUNT_RATE instead of writing 0.25 again."
assert ":.2f" in __source__, "Show every amount with :.2f in the f-string."
assert __source__.count("print(") == 2, "Print one row per pass with a single print() inside the loop, and keep the heading print() outside it."
assert count == rows, "Add 1 to count on every pass so the loop stops after rows passes."
""",
    "answer": b64(clearance),
    "answerNote": "Both price and count are updated on every pass. When rows is 0, the first test is false, so only the heading is printed."}

# ---------------------------------------------------------------- 2 Shared Tutorial Teams
teams = """first = int(input('First group: '))
second = int(input('Second group: '))
team_size = min(first, second)

while first % team_size != 0 or second % team_size != 0:
    team_size = team_size - 1

print('Largest shared team size:', team_size)
"""
E["teams"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 8,
    "starter": "first = int(input('First group: '))\nsecond = int(input('Second group: '))\nteam_size = min(first, second)\n\n# Decrease team_size until it divides both groups.\n\nprint('Largest shared team size:', team_size)\n",
    "cases": input_cases(teams, ("Typed 120 and 48", ["120", "48"]), ("Typed 7 and 5", ["7", "5"]),
                         ("Typed 36 and 36", ["36", "36"]), ("Typed 9 and 27", ["9", "27"]), ("Typed 1 and 40", ["1", "40"])),
    "check": WHILE_ONLY + """assert "%" in __source__, "Use % to test whether team_size divides a group exactly."
assert "gcd" not in __source__ and "import" not in __source__, "Search for the answer with the loop; do not import a module."
assert "team_size - 1" in __source__ or "team_size -= 1" in __source__, "Decrease team_size by 1 on each pass."
assert __source__.count("print(") == 1, "Keep the single print() after the loop."
""",
    "answer": b64(teams),
    "answerNote": "The loop continues while at least one group has a remainder. A team size of 1 divides every positive group size, so the search always stops."}

# ---------------------------------------------------------------- 3 Binary Room Code
binary = """bits = input('Binary code: ')
index = 0
value = 0

while index < len(bits):
    value = value * 2 + int(bits[index])
    index = index + 1

print('Room number:', value)
"""
E["binary"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 9,
    "starter": "bits = input('Binary code: ')\nindex = 0\nvalue = 0\n\n# Process one character on each pass.\n\nprint('Room number:', value)\n",
    "cases": input_cases(binary, ("Typed 101101", ["101101"]), ("Typed 0", ["0"]), ("Typed 1", ["1"]),
                         ("Typed 1000", ["1000"]), ("Typed 11111111", ["11111111"])),
    "check": WHILE_ONLY + """
assert "len(bits)" in __source__, "Test index against len(bits) so every character is processed once."
assert "bits[index]" in __source__, "Pick one character out of bits with bits[index]."
assert not re.search(r"int\\(\\s*bits\\s*,", __source__), "Build the value one digit at a time; int(bits, 2) is not part of this course."
assert "* 2" in __source__ or "*2" in __source__, "Double the value built so far before adding the new digit."
assert __source__.count("print(") == 1, "Keep the single print() after the loop."
""",
    "answer": b64(binary),
    "answerNote": "Multiplying by 2 makes room for the next binary digit. The index starts at 0 and advances once per pass, so every character is processed exactly once."}

# ---------------------------------------------------------------- 4 Circle Estimate
circle = """terms = int(input('Terms: '))
step = 1
denominator = 1
sign = 1
estimate = 0.0

while step <= terms:
    estimate = estimate + sign * 4 / denominator
    print(f'After {step}: {estimate:.6f}')
    denominator = denominator + 2
    sign = -sign
    step = step + 1
"""
E["circle"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 12,
    "starter": "terms = int(input('Terms: '))\nstep = 1\ndenominator = 1\nsign = 1\nestimate = 0.0\n\n# Add one term and print one estimate on each pass.\n",
    "cases": input_cases(circle, ("Typed 1", ["1"]), ("Typed 4", ["4"]), ("Typed 2", ["2"]), ("Typed 10", ["10"])),
    "check": WHILE_ONLY + """assert "math" not in __source__ and "import" not in __source__, "Build the estimate with the loop; do not import a module."
assert ":.6f" in __source__, "Show the estimate with :.6f in the f-string."
assert __source__.count("print(") == 1, "Print one estimate per pass with a single print() inside the loop."
assert denominator == 2 * terms + 1, "Add 2 to denominator on every pass so it moves through 1, 3, 5, 7 and so on."
assert sign == (1 if terms % 2 == 0 else -1), "Flip sign on every pass so the terms alternate between adding and subtracting."
assert step == terms + 1, "Add 1 to step on every pass and stop after terms passes."
""",
    "answer": b64(circle),
    "answerNote": "The denominator advances through the positive odd integers, while sign = -sign alternates addition and subtraction. The inclusive test produces exactly the requested number of lines."}

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-12-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 12 Boss Problems",
    "short": "L12 bosses",
    "subtitle": "Problem solving with loops: the while loop",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-12/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
