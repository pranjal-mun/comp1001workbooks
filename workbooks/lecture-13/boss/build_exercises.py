"""Build workbooks/lecture-13/boss/exercises.json: the Lecture 13 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_13_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Run from anywhere:

    python3 workbooks/lecture-13/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-13/boss
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

def run_with_prompts(code, inputs):
    """Run with scripted input() answers, echoing prompts but not the answers,
    exactly as the grader does (echoInput: false)."""
    wrapper = (
        "import builtins, sys\n"
        "_answers = " + repr(list(inputs)) + "\n"
        "def _input(prompt=''):\n"
        "    sys.stdout.write(str(prompt))\n"
        "    return _answers.pop(0)\n"
        "builtins.input = _input\n"
        + code
    )
    return run(wrapper)

def input_cases(solution, *runs):
    return [{"name": name, "inputs": list(inputs), "expected": run_with_prompts(solution, inputs)} for name, inputs in runs]

NO_IMPORT = 'assert "import" not in __source__, "Solve it with a while loop and arithmetic; no import is needed."\n'
ONE_BREAK = '''assert "while True" in __source__, "Keep the while True loop and leave it with one break."
assert __source__.count("break") == 1, "Use exactly one break to leave the loop."
'''

E = {}

# ---------------------------------------------------------------- 1 Oliver's Treat Average
treats = """total = 0
count = 0

while True:
    treats = int(input('Treats (-1 to finish): '))
    if treats == -1:
        break
    total = total + treats
    count = count + 1

if count > 0:
    print(f'Average treats: {total / count:.2f}')
else:
    print('No days were entered.')
"""
E["treats"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 12,
    "starter": "total = 0\ncount = 0\n\nwhile True:\n    treats = int(input('Treats (-1 to finish): '))\n    # Test the sentinel before updating total and count.\n\n# Print a safe result here.\n",
    "cases": input_cases(treats, ("Typed 2, 4, 6, -1", ["2", "4", "6", "-1"]), ("Typed -1", ["-1"]),
                         ("Typed 5, -1", ["5", "-1"]), ("Typed 0, 0, 3, -1", ["0", "0", "3", "-1"]), ("Typed 1, 2, -1", ["1", "2", "-1"])),
    "check": ONE_BREAK + NO_IMPORT + '''import re
update = re.search(r"total\\s*(\\+=|=\\s*total\\s*\\+)", __source__)
assert update, "Add each count to total inside the loop with total = total + treats."
assert __source__.index("break") < update.start(), "Test the sentinel and break before total and count are updated."
assert re.search(r"if\\s+count\\s*(>\\s*0|!=\\s*0|>=\\s*1)\\s*:|if\\s+count\\s*:", __source__), "Test count > 0 before dividing by it."
assert ":.2f" in __source__, "Print the average with two digits after the decimal point using :.2f."
''',
    "answer": b64(treats),
    "answerNote": "The sentinel is tested before either accumulator changes. The final decision checks count before division, so entering -1 first is safe."}
assert E["treats"]["cases"][0]["expected"].endswith("Average treats: 4.00")
assert E["treats"]["cases"][1]["expected"].endswith("No days were entered.")

# ---------------------------------------------------------------- 2 Campus Shop Cash Total
cash = """total = 0.0

while True:
    text = input('Price, or blank to finish: $')
    if text == '':
        break
    total = total + float(text)

cents = round(total * 100)
remainder = cents % 5
if remainder < 3:
    cash_cents = cents - remainder
else:
    cash_cents = cents + 5 - remainder

print(f'Card total: ${cents / 100:.2f}')
print(f'Cash total: ${cash_cents / 100:.2f}')
"""
E["cash"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 14,
    "starter": "total = 0.0\n\nwhile True:\n    text = input('Price, or blank to finish: $')\n    # Test text before converting it to a number.\n\n# Convert the total to cents, round for cash, and print both totals.\n",
    "cases": input_cases(cash, ("Typed 1.02, 2.01, blank", ["1.02", "2.01", ""]), ("Blank first", [""]),
                         ("Typed 0.99, blank", ["0.99", ""]), ("Typed 1.01, blank", ["1.01", ""]), ("Typed 1.03, blank", ["1.03", ""]),
                         ("Typed 2.50, 2.50, blank", ["2.50", "2.50", ""]), ("Typed 4.99, 0.08, blank", ["4.99", "0.08", ""])),
    "check": ONE_BREAK + NO_IMPORT + '''assert "float(" in __source__, "Convert each price with float() after the blank-line test."
assert __source__.index("break") < __source__.index("float("), "Test text for the blank line before calling float() on it."
assert "round(" in __source__, "Convert the total to whole cents with round(total * 100)."
assert "% 5" in __source__ or "%5" in __source__, "Use the remainder cents % 5 to round the cash total."
assert __source__.count("print(") == 2, "Print exactly two lines: the card total and the cash total."
''',
    "answer": b64(cash),
    "answerNote": "The blank string is tested before float is called. Converting the completed total to cents makes the last step an integer remainder calculation. The initialized total also gives a safe sentinel-first result."}
assert E["cash"]["cases"][0]["expected"].endswith("Card total: $3.03\nCash total: $3.05")
assert E["cash"]["cases"][1]["expected"].endswith("Card total: $0.00\nCash total: $0.00")
assert E["cash"]["cases"][2]["expected"].endswith("Card total: $0.99\nCash total: $1.00")
assert E["cash"]["cases"][3]["expected"].endswith("Card total: $1.01\nCash total: $1.00")
assert E["cash"]["cases"][4]["expected"].endswith("Card total: $1.03\nCash total: $1.05")

# ---------------------------------------------------------------- 3 Square Root Check
sqrt = """number = float(input('Number: '))
guess = number / 2
updates = 0

while abs(guess * guess - number) > 0.000001:
    guess = (guess + number / guess) / 2
    updates = updates + 1

print(f'Square root: {guess:.6f}')
print('Updates:', updates)
"""
E["sqrt"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 9,
    "starter": "number = float(input('Number: '))\nguess = number / 2\nupdates = 0\n\n# Improve guess until it is accurate enough.\n\nprint(f'Square root: {guess:.6f}')\nprint('Updates:', updates)\n",
    "cases": input_cases(sqrt, ("Typed 4", ["4"]), ("Typed 25", ["25"]), ("Typed 2", ["2"]), ("Typed 100", ["100"]), ("Typed 0.25", ["0.25"]), ("Typed 1", ["1"])),
    "check": NO_IMPORT + '''assert "while" in __source__, "Repeat the improvement with a while loop whose condition tests the error."
assert "abs(" in __source__, "Measure the error with abs(guess * guess - number)."
assert "0.000001" in __source__ or "1e-6" in __source__ or "1e-06" in __source__, "Stop when the error is no longer greater than 0.000001."
assert "break" not in __source__, "Put the stopping test in the while header; no break is needed."
assert "** 0.5" not in __source__ and "**0.5" not in __source__ and "sqrt" not in __source__, "Estimate the root with the averaging step, not with ** 0.5 or a square-root function."
''',
    "answer": b64(sqrt),
    "answerNote": "The loop tests the error in the current guess. For 4, the initial guess is already exact, so tracing shows zero passes. Each pass for 25 improves the guess and increments the counter once."}
assert E["sqrt"]["cases"][0]["expected"].endswith("Square root: 2.000000\nUpdates: 0")
assert E["sqrt"]["cases"][1]["expected"].endswith("Square root: 5.000000\nUpdates: 5")

# ---------------------------------------------------------------- 4 Factor Trail
factors = """number = int(input('Number: '))
remaining = number
factor = 2

print('Prime factors:')
while factor <= remaining:
    if remaining % factor == 0:
        print(factor)
        remaining = remaining // factor
    else:
        factor = factor + 1
"""
E["factors"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 10,
    "starter": "number = int(input('Number: '))\nremaining = number\nfactor = 2\n\nprint('Prime factors:')\n\n# Reduce remaining until every factor has been printed.\n",
    "cases": input_cases(factors, ("Typed 84", ["84"]), ("Typed 13", ["13"]), ("Typed 2", ["2"]), ("Typed 360", ["360"]), ("Typed 97", ["97"]), ("Typed 1000", ["1000"])),
    "check": NO_IMPORT + '''import re
assert len(re.findall(r"^\\s*while\\b", __source__, re.M)) == 1, "Use one while loop that runs until remaining has been reduced to 1."
assert "%" in __source__, "Test whether factor divides remaining exactly with %."
assert "//" in __source__, "Divide remaining by the factor with // so that it stays an int."
assert "break" not in __source__, "Let the while condition end the loop; no break is needed."
assert __stdout__.count("\\n") >= 1, "Print each prime factor on its own line."
''',
    "answer": b64(factors),
    "answerNote": "A successful division reduces remaining but keeps the same possible factor, which is why 2 is printed twice for 84. If the input is prime, every smaller candidate fails and the input itself is eventually printed."}
assert E["factors"]["cases"][0]["expected"].endswith("Prime factors:\n2\n2\n3\n7")
assert E["factors"]["cases"][1]["expected"].endswith("Prime factors:\n13")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-13-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 13 Boss Problems",
    "short": "L13 bosses",
    "subtitle": "Hand-tracing, sentinels, and common loop bugs",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-13/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
