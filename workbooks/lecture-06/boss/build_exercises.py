"""Build workbooks/lecture-06/boss/exercises.json: the Lecture 6 boss problems.

Expected outputs are produced by actually running the model solutions with
the scripted keyboard input. Run from anywhere:

    python3 workbooks/lecture-06/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-06/boss
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

def cases(solution, *runs):
    """One case per set of typed answers: (name, [answers...])."""
    return [{"name": name, "inputs": list(inputs), "expected": run(solution, inputs)} for name, inputs in runs]

FSTRING = 'assert "f\'" in __source__ or \'f"\' in __source__, "Build the output with an f-string (f before the opening quote)."\n'
NO_IF = 'assert "if " not in __source__, "No if statements: arithmetic alone does the job."\n'
NO_LOOP = 'assert "for " not in __source__ and "while " not in __source__, "No loops: use the formula."\n'

E = {}

# ---------------------------------------------------------------- 1 Treats
treats = """days = int(input('Days: '))
total = days * (days + 1) // 2
print(f'Oliver has eaten {total} treats by day {days}.')
"""
E["treats"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 3,
    "starter": "days = input('Days: ')\n# Print how many treats Oliver has eaten by that day.\n",
    "cases": cases(treats, ("Typed 7", ["7"]), ("Typed 2", ["2"]), ("Typed 30", ["30"]), ("Typed 120", ["120"])),
    "check": FSTRING + NO_LOOP + """import re
assert type(days) is int, "Convert the typed text with int() so days is a whole number."
assert not re.search(r"\\d\\.0\\b", __stdout__), "The total must be a whole number: divide with // rather than /."
assert len(__stdout__.strip().splitlines()) == 1, "Print one line with a single print() call."
""",
    "answer": b64(treats),
    "answerNote": "1 + 2 + ... + n is n(n + 1) / 2. The product of two consecutive whole numbers is always even, so // divides it exactly."}

# ---------------------------------------------------------------- 2 Bottle deposits
deposits = """SMALL_DEPOSIT = 0.10
LARGE_DEPOSIT = 0.25
small = int(input('Small containers: '))
large = int(input('Large containers: '))
refund = small * SMALL_DEPOSIT + large * LARGE_DEPOSIT
print(f'Refund: ${refund:.2f}')
"""
E["deposits"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 6,
    "starter": "small = input('Small containers: ')\nlarge = input('Large containers: ')\n# Print the refund as money.\n",
    "cases": cases(deposits, ("Typed 11 and 3", ["11", "3"]), ("Typed 0 and 0", ["0", "0"]),
                   ("Typed 120 and 0", ["120", "0"]), ("Typed 7 and 12", ["7", "12"])),
    "check": FSTRING + NO_IF + """import re
assert type(small) is int and type(large) is int, "Convert both counts with int(): they are whole numbers."
constants = {k: v for k, v in globals().items() if k == k.upper() and not k.startswith("__") and isinstance(v, float)}
assert 0.1 in constants.values() and 0.25 in constants.values(), "Store the two deposit amounts, 0.10 and 0.25, in ALL_CAPS constants (for example SMALL_DEPOSIT)."
assert re.search(r":\\s*[<>^]?\\d*\\.2f", __source__), "Show the refund with the .2f specifier so it always has two decimals."
assert "round(" not in __source__, "Do not round the value; let the .2f specifier format the display."
assert len(__stdout__.strip().splitlines()) == 1, "Print one line with a single print() call."
""",
    "answer": b64(deposits),
    "answerNote": "The value of refund is not rounded; .2f only changes how it is displayed."}

# ---------------------------------------------------------------- 3 Day-old bread
bread = """PRICE = 3.49
DISCOUNT_RATE = 0.60
loaves = int(input('Loaves: '))
regular = loaves * PRICE
discount = regular * DISCOUNT_RATE
total = regular - discount
print(f'Regular price: ${regular:7.2f}')
print(f'Discount:      ${discount:7.2f}')
print(f'Total:         ${total:7.2f}')
"""
E["bread"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 9,
    "starter": "loaves = input('Loaves: ')\n# Print the regular price, the discount, and the total.\n",
    "cases": cases(bread, ("Typed 3", ["3"]), ("Typed 1", ["1"]), ("Typed 12", ["12"]), ("Typed 100", ["100"])),
    "check": FSTRING + NO_IF + """import re
assert type(loaves) is int, "Convert the typed text with int(): loaves is a whole number."
assert "round(" not in __source__, "Do not round the values; let the .2f specifier format the display."
assert len(re.findall(r":\\s*[<>^]?\\d+\\.2f", __source__)) >= 3, "Give each amount a width and two decimals, as in {total:7.2f}, so the decimal points line up."
lines = __stdout__.split("Loaves: ", 1)[-1].strip().splitlines()
assert len(lines) == 3, "Print exactly three lines: regular price, discount, and total."
assert len({line.find("$") for line in lines}) == 1 and len({line.rfind(".") for line in lines}) == 1, "The dollar signs and the decimal points must line up in one column."
""",
    "answer": b64(bread),
    "answerNote": "A width of 7 leaves room for amounts up to 9999.99. The dollar sign is ordinary text before the braces."}

# ---------------------------------------------------------------- 4 Countdown
countdown = """seconds = int(input('Seconds: '))
days = seconds // 86400
remaining = seconds % 86400
hours = remaining // 3600
remaining = remaining % 3600
minutes = remaining // 60
remaining = remaining % 60
print(f'{days}:{hours:02d}:{minutes:02d}:{remaining:02d}')
"""
E["countdown"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 8,
    "starter": "seconds = input('Seconds: ')\n# Print the time left as D:HH:MM:SS.\n",
    "cases": cases(countdown, ("Typed 93784", ["93784"]), ("Typed 59", ["59"]), ("Typed 86400", ["86400"]), ("Typed 1000000", ["1000000"])),
    "check": FSTRING + NO_IF + """import re
assert type(seconds) is int, "Convert the typed text with int(): seconds is a whole number."
assert "//" in __source__ and "%" in __source__, "Split the seconds with // (how many whole units fit) and % (what is left over)."
assert re.search(r":0?2d?\\}", __source__), "Pad the hours, minutes, and seconds with the 02d specifier so each has two digits."
assert "str(" not in __source__ and "zfill" not in __source__, "Do the padding with a format specifier, not by building text with str()."
assert len(__stdout__.strip().splitlines()) == 1, "Print one line with a single print() call."
""",
    "answer": b64(countdown),
    "answerNote": "Each // takes out the biggest unit that fits, and the matching % leaves the rest for the smaller units."}

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-06-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 6 Boss Problems",
    "short": "L06 bosses",
    "subtitle": "Input and output, and f-strings",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-06/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
