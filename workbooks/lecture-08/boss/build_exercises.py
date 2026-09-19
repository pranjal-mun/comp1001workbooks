"""Build workbooks/lecture-08/boss/exercises.json: the Lecture 8 boss problems.

Expected outputs are produced by actually running the model solutions. Run
from anywhere:

    python3 workbooks/lecture-08/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-08/boss
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

# Lecture 8 teaches one two-way decision. Every boss must be exactly one
# if/else with the shared work (the print) after the branches.
ONE_IF_ELSE = '''import re
assert len(re.findall(r"^\\s*if\\b", __source__, re.M)) == 1, "Use exactly one if statement."
assert re.search(r"^\\s*else\\s*:", __source__, re.M), "Handle the other case with else."
assert not re.search(r"^\\s*elif\\b", __source__, re.M), "elif is not part of this lecture; one if and one else are enough here."
assert __source__.count("print(") == 1, "Choose the value inside the branches, then print once after them."
'''

E = {}

# ---------------------------------------------------------------- 1 Even or odd
parity = """number = int(input('Number: '))
if number % 2 == 0:
    kind = 'even'
else:
    kind = 'odd'
print(f'{number} is {kind}.')
"""
E["parity"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 6,
    "starter": "number = int(input('Number: '))\n# Print whether the number is even or odd.\n",
    "cases": input_cases(parity, ("Typed 14", ["14"]), ("Typed 7", ["7"]), ("Typed 0", ["0"]), ("Typed -3", ["-3"])),
    "check": ONE_IF_ELSE + """assert "%" in __source__, "Test the remainder with % to tell even from odd."
assert __stdout__.strip().endswith("."), "End the message with a full stop, as in 14 is even."
""",
    "answer": b64(parity),
    "answerNote": "number % 2 is 0 for every even number, including 0 and negative numbers."}

# ---------------------------------------------------------------- 2 Dog years
dog = """years = float(input('Human years: '))
if years <= 2:
    dog_years = years * 10.5
else:
    dog_years = 21 + (years - 2) * 4
print(f'{years:.1f} human years is {dog_years:.1f} dog years.')
"""
E["dog"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 6,
    "starter": "years = float(input('Human years: '))\n# Print the age in dog years to one decimal place.\n",
    "cases": input_cases(dog, ("Typed 7", ["7"]), ("Typed 2", ["2"]), ("Typed 1", ["1"]), ("Typed 15", ["15"]), ("Typed 1.2", ["1.2"])),
    "check": ONE_IF_ELSE + """assert ":.1f" in __source__, "Show both numbers to one decimal place with :.1f in the f-string."
assert "10.5" in __source__ and "4" in __source__, "Use 10.5 dog years for each of the first two years and 4 for each year after that."
""",
    "answer": b64(dog),
    "answerNote": "The first two years are worth 21 dog years. The else branch starts from 21 and adds 4 for each remaining year. Both formulas give 21 at exactly 2 years."}

# ---------------------------------------------------------------- 3 Chess square
square = """position = input('Square: ')
column = 'abcdefgh'.find(position[0])
row = int(position[1])
if (column + row) % 2 == 0:
    colour = 'white'
else:
    colour = 'black'
print(f'{position} is a {colour} square.')
"""
E["square"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 8,
    "starter": "position = input('Square: ')\n# Print whether the square is black or white.\n",
    "cases": input_cases(square, ("Typed a1", ["a1"]), ("Typed d5", ["d5"]), ("Typed h1", ["h1"]), ("Typed g7", ["g7"]), ("Typed c6", ["c6"])),
    "check": ONE_IF_ELSE + """assert ".find(" in __source__, "Turn the column letter into a number with 'abcdefgh'.find(...) instead of testing each letter."
assert "%" in __source__, "Use % to decide the colour from the column number and the row."
assert "ord(" not in __source__, "ord() is not part of this course; use .find() on the string of column letters."
assert "[" in __source__, "Pick the letter and the digit out of position with indexes."
""",
    "answer": b64(square),
    "answerNote": "'abcdefgh'.find('a') is 0. For a1 the sum is 0 + 1, which is odd, and a1 is black. Each move of one square changes the sum by one and the colour flips."}

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-08-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 8 Boss Problems",
    "short": "L08 bosses",
    "subtitle": "Problem solving with decisions: the if statement",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-08/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
