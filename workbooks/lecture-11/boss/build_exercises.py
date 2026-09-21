"""Build workbooks/lecture-11/boss/exercises.json: the Lecture 11 boss problems.

Expected outputs are produced by actually running the model solutions. Run
from anywhere:

    python3 workbooks/lecture-11/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-11/boss
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

# Lecture 11 adds and/or/not, bool, and the string tests used for input
# validation. Still no loops, no functions, no imports.
NO_IMPORT = 'import re\nassert not re.search(r"^\\s*(import|from)\\b", __code__, re.M), "No imports. Everything here can be done with if statements and arithmetic."\n'
E = {}

# ---------------------------------------------------------------- 1 Leap year
leap = """year = int(input('Year: '))
if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
    print(f'{year} is a leap year.')
else:
    print(f'{year} is not a leap year.')
"""
E["leap"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 5,
    "starter": "year = int(input('Year: '))\n# Report whether the year is a leap year.\n",
    "cases": input_cases(leap, ("Typed 2024", ["2024"]), ("Typed 2023", ["2023"]), ("Typed 1900", ["1900"]),
                         ("Typed 2000", ["2000"]), ("Typed 2100", ["2100"]), ("Typed 1600", ["1600"])),
    "check": NO_IMPORT + """assert len(re.findall(r"^\\s*if\\b", __code__, re.M)) == 1 and re.search(r"^\\s*else\\s*:", __code__, re.M), "Use exactly one if with an else."
assert not re.search(r"^\\s*elif\\b", __code__, re.M), "No elif here. One condition built with and/or covers every case."
assert re.search(r"\\band\\b", __code__) and re.search(r"\\bor\\b", __code__), "Combine the three divisibility tests with and and or."
assert "%" in __code__, "Use % to test divisibility."
assert len(__stdout__.strip().splitlines()) == 1, "Print one line."
""",
    "answer": b64(leap),
    "hints": [
        "A year is a leap year when it is divisible by 4, except that a year divisible by 100 is not, unless it is also divisible by 400. Turn each 'divisible by' into a `%` test and join them with `and` and `or`. Brackets decide which pair is joined first.",
    ],
    "answerNote": "The brackets matter: the year must be divisible by 4, and then it must either miss 100 or hit 400. Without them, and binds before or and 1900 comes out as a leap year."}

# ---------------------------------------------------------------- 2 Licence plate
plate = """plate = input('Plate: ')
if len(plate) == 6 and plate[:3].isalpha() and plate[:3].isupper() and plate[3:].isdigit():
    print(f'{plate} is an old style plate.')
elif len(plate) == 7 and plate[:4].isdigit() and plate[4:].isalpha() and plate[4:].isupper():
    print(f'{plate} is a new style plate.')
else:
    print(f'{plate} is not a valid plate.')
"""
E["plate"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 7,
    "starter": "plate = input('Plate: ')\n# Say whether the plate is old style, new style, or not valid.\n",
    "cases": input_cases(plate, ("Typed ABC123", ["ABC123"]), ("Typed 1234ABC", ["1234ABC"]), ("Typed abc123", ["abc123"]),
                         ("Typed ABC12", ["ABC12"]), ("Typed 1234abc", ["1234abc"]), ("Typed 123ABCD", ["123ABCD"]),
                         ("Typed A1B2C3", ["A1B2C3"]), ("Typed 12345AB", ["12345AB"])),
    "check": NO_IMPORT + """assert re.search(r"^\\s*elif\\b", __code__, re.M) and re.search(r"^\\s*else\\s*:", __code__, re.M), "Use an if/elif/else chain: old style, new style, not valid."
assert "len(" in __code__, "Check the length first with len()."
assert ".isalpha()" in __code__ and ".isupper()" in __code__ and ".isdigit()" in __code__, "Use isalpha(), isupper() and isdigit() on the letter part and the digit part."
assert "[" in __code__, "Use slices to pick out the letter part and the digit part."
assert re.search(r"\\band\\b", __code__), "Join the tests for one style with and."
assert len(__stdout__.strip().splitlines()) == 1, "Print one line."
""",
    "answer": b64(plate),
    "hints": [
        "A slice like `plate[:3]` is the first three characters and `plate[3:]` is the rest. Test the length first, then each part with the string methods. `isalpha()` alone accepts lowercase letters, so add `isupper()`.",
    ],
    "answerNote": "Each style is one and-chain: right length, letters where letters belong, digits where digits belong. The length test comes first so the slices line up with the right parts."}

# ---------------------------------------------------------------- 3 Roulette
roulette = """spin = input('Spin: ')
if spin == '0' or spin == '00':
    print(f'Pay {spin}')
else:
    number = int(spin)
    print(f'The spin landed on {number}.')
    print(f'Pay {number}')
    odd = number % 2 == 1
    first_group = number <= 10 or (number >= 19 and number <= 28)
    red = False
    if first_group and odd:
        red = True
    if not first_group and not odd:
        red = True
    if red:
        print('Pay Red')
    else:
        print('Pay Black')
    if odd:
        print('Pay Odd')
    else:
        print('Pay Even')
    if number <= 18:
        print('Pay 1 to 18')
    else:
        print('Pay 19 to 36')
"""
E["roulette"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 15,
    "starter": "spin = input('Spin: ')\n# Print every bet that pays for this spin.\n",
    "cases": input_cases(roulette, ("Typed 13", ["13"]), ("Typed 0", ["0"]), ("Typed 00", ["00"]), ("Typed 1", ["1"]),
                         ("Typed 12", ["12"]), ("Typed 36", ["36"]), ("Typed 20", ["20"]), ("Typed 18", ["18"]),
                         ("Typed 29", ["29"])),
    "check": NO_IMPORT + """assert re.search(r"^spin = input\\('Spin: '\\)\\s*$", __source__, re.M), "Keep spin as text, so that 00 stays 00. Convert to int only after ruling out 0 and 00."
assert re.search(r"\\band\\b", __code__) and re.search(r"\\bor\\b", __code__) and re.search(r"\\bnot\\b", __code__), "Use and, or and not to build the red test."
assert "%" in __code__, "Use % to tell odd from even."
__lines__ = __stdout__.strip().splitlines()
assert len(__lines__) in (1, 5), "0 and 00 print one line; every other spin prints five."
""",
    "answer": b64(roulette),
    "hints": [
        "Read the spin as text and test `spin == '0' or spin == '00'` before converting. Once you know it is 1 to 36, `int(spin)` gives a number to compare.",
        "Store `odd` and `first_group` as Boolean variables first. Red is `first_group and odd`, or `not first_group and not odd`. Then each print block is a short if/else on those names.",
    ],
    "answerNote": "The zeros are handled first, as text, so 00 never turns into 0. Naming odd and first_group turns the red rule into one readable line each, and the last three if/else blocks each print exactly one bet."}

# ---------------------------------------------------------------- 4 Next day
nextday = """year = int(input('Year: '))
month = int(input('Month: '))
day = int(input('Day: '))
if month == 2:
    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        days = 29
    else:
        days = 28
elif month == 4 or month == 6 or month == 9 or month == 11:
    days = 30
else:
    days = 31
next_year = year
next_month = month
next_day = day + 1
if next_day > days:
    next_day = 1
    next_month = month + 1
if next_month > 12:
    next_month = 1
    next_year = year + 1
print(f'The day after {year}-{month:02d}-{day:02d} is {next_year}-{next_month:02d}-{next_day:02d}.')
"""
E["nextday"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 18,
    "starter": "year = int(input('Year: '))\nmonth = int(input('Month: '))\nday = int(input('Day: '))\n# Print the date of the following day.\n",
    "cases": input_cases(nextday, ("Typed 2013 11 18", ["2013", "11", "18"]), ("Typed 2013 11 30", ["2013", "11", "30"]),
                         ("Typed 2013 12 31", ["2013", "12", "31"]), ("Typed 2024 2 28", ["2024", "2", "28"]),
                         ("Typed 2023 2 28", ["2023", "2", "28"]), ("Typed 2024 2 29", ["2024", "2", "29"]),
                         ("Typed 2100 2 28", ["2100", "2", "28"]), ("Typed 2000 2 28", ["2000", "2", "28"]),
                         ("Typed 2026 1 9", ["2026", "1", "9"]), ("Typed 2026 4 30", ["2026", "4", "30"])),
    "check": NO_IMPORT + """assert re.search(r"^\\s*elif\\b", __code__, re.M), "Use an if/elif/else chain for the number of days in the month."
assert re.search(r"\\band\\b", __code__) and re.search(r"\\bor\\b", __code__), "Use and and or for the leap year test and the 30 day months."
assert "%" in __code__, "Use % for the leap year test."
assert re.search(r":[^}]*0>?2d?\\}", __source__), "Show month and day with two digits using :02d."
assert len(__stdout__.strip().splitlines()) == 1, "Print one line."
""",
    "answer": b64(nextday),
    "hints": [
        "First work out how many days the month has: February depends on the leap year rule from Boss 1, four months have 30, the rest have 31. An if/elif/else chain that stores `days` does it.",
        "Add 1 to the day. If that passes `days`, the day becomes 1 and the month goes up by one. If the month passes 12, the month becomes 1 and the year goes up by one. Two separate ifs, in that order.",
        "Keep the typed date in `year`, `month` and `day` and put the answer in new variables, so the print can show both. `{month:02d}` prints 2 as `02`.",
    ],
    "answerNote": "The month length is one chain, then two rollover ifs run in order: day into month, then month into year. New variables hold the answer so the original date is still there for the print."}

data = {
    "id": "lecture-11-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 11 Boss Problems",
    "short": "L11 bosses",
    "subtitle": "Boolean operators, bool, and input validation",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-11/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
