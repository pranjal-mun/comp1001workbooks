"""Build workbooks/lecture-10/boss/exercises.json: the Lecture 10 boss problems.

Expected outputs are produced by actually running the model solutions. Run
from anywhere:

    python3 workbooks/lecture-10/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-10/boss
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

# Lecture 10 adds elif chains and nested decisions. Still no and/or.
NO_BOOL_OPS = ('import re\n'
               'assert not re.search(r"\\b(and|or|not)\\b", __code__), "and, or and not are not part of this lecture yet; use an elif chain or a nested if."\n')
ONE_CHAIN = ('assert len(re.findall(r"^\\s*if\\b", __code__, re.M)) == 1, "One if/elif/else chain is enough: every case is a different alternative for the same value."\n'
             'assert re.search(r"^\\s*elif\\b", __code__, re.M), "Use elif for the middle alternatives."\n')

E = {}

# ---------------------------------------------------------------- 1 Shape
shape = """sides = int(input('Sides: '))
if sides == 3:
    name = 'a triangle'
elif sides == 4:
    name = 'a quadrilateral'
elif sides == 5:
    name = 'a pentagon'
elif sides == 6:
    name = 'a hexagon'
elif sides == 7:
    name = 'a heptagon'
elif sides == 8:
    name = 'an octagon'
elif sides == 9:
    name = 'a nonagon'
elif sides == 10:
    name = 'a decagon'
else:
    name = 'not one this program knows'
print(f'A shape with {sides} sides is {name}.')
"""
E["shape"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 12,
    "starter": "sides = int(input('Sides: '))\n# Print the name of the shape.\n",
    "cases": input_cases(shape, ("Typed 8", ["8"]), ("Typed 3", ["3"]), ("Typed 10", ["10"]),
                         ("Typed 2", ["2"]), ("Typed 11", ["11"]), ("Typed 6", ["6"])),
    "check": NO_BOOL_OPS + ONE_CHAIN + """assert re.search(r"^\\s*else\\s*:", __code__, re.M), "End the chain with else for a count outside 3 to 10."
assert __code__.count("print(") == 1, "Store the name inside the branches, then print once after the chain."
assert __stdout__.strip().endswith("."), "End the sentence with a full stop."
""",
    "answer": b64(shape),
    "hints": [
        "Store the name in the branches and print one f-string after the chain. The `else` branch stores the text for a count the chain does not know, so the same print works for every case.",
    ],
    "answerNote": "The chain compares sides with each count in turn. Whatever branch runs, the single print after it finishes the sentence."}

# ---------------------------------------------------------------- 2 Richter
richter = """magnitude = float(input('Magnitude: '))
if magnitude < 2.0:
    label = 'micro'
elif magnitude < 3.0:
    label = 'very minor'
elif magnitude < 4.0:
    label = 'minor'
elif magnitude < 5.0:
    label = 'light'
elif magnitude < 6.0:
    label = 'moderate'
elif magnitude < 7.0:
    label = 'strong'
elif magnitude < 8.0:
    label = 'major'
elif magnitude < 10.0:
    label = 'great'
else:
    label = 'meteoric'
print(f'A magnitude {magnitude} earthquake is {label}.')
"""
E["richter"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 12,
    "starter": "magnitude = float(input('Magnitude: '))\n# Print the descriptor for the magnitude.\n",
    "cases": input_cases(richter, ("Typed 7.2", ["7.2"]), ("Typed 5.5", ["5.5"]), ("Typed 2.0", ["2.0"]),
                         ("Typed 1.9", ["1.9"]), ("Typed 10", ["10"]), ("Typed 6", ["6"]), ("Typed 8.0", ["8.0"])),
    "check": NO_BOOL_OPS + ONE_CHAIN + """assert re.search(r"^\\s*else\\s*:", __code__, re.M), "End the chain with else for 10.0 or more."
assert __code__.count("print(") == 1, "Store the descriptor inside the branches, then print once after the chain."
assert __code__.count("<") + __code__.count(">") <= 9, "Order the branches so each one needs a single comparison; the earlier branches have already ruled out the smaller magnitudes."
""",
    "answer": b64(richter),
    "hints": [
        "Test the ranges from the smallest up. Once `magnitude < 2.0` has failed, the next `elif magnitude < 3.0` already knows the value is at least 2.0, so one comparison per branch is enough.",
    ],
    "answerNote": "Each branch of the chain only runs after every earlier test has failed, so `elif magnitude < 3.0` covers exactly 2.0 up to but not including 3.0."}

# ---------------------------------------------------------------- 3 Chinese zodiac
zodiac = """year = int(input('Year: '))
position = year % 12
if position == 0:
    animal = 'Monkey'
elif position == 1:
    animal = 'Rooster'
elif position == 2:
    animal = 'Dog'
elif position == 3:
    animal = 'Pig'
elif position == 4:
    animal = 'Rat'
elif position == 5:
    animal = 'Ox'
elif position == 6:
    animal = 'Tiger'
elif position == 7:
    animal = 'Hare'
elif position == 8:
    animal = 'Dragon'
elif position == 9:
    animal = 'Snake'
elif position == 10:
    animal = 'Horse'
else:
    animal = 'Sheep'
print(f'{year} is the year of the {animal}.')
"""
E["zodiac"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 16,
    "starter": "year = int(input('Year: '))\n# Print the animal for the year.\n",
    "cases": input_cases(zodiac, ("Typed 2019", ["2019"]), ("Typed 2000", ["2000"]), ("Typed 2026", ["2026"]),
                         ("Typed 1999", ["1999"]), ("Typed 1925", ["1925"]), ("Typed 0", ["0"]), ("Typed 2035", ["2035"])),
    "check": NO_BOOL_OPS + ONE_CHAIN + """assert "%" in __code__, "Use % to find where the year falls in the 12-year cycle."
assert __code__.count("print(") == 1, "Store the animal inside the branches, then print once after the chain."
assert __code__.count("elif") >= 10, "The chain needs one branch per animal: eleven tests and an else."
""",
    "answer": b64(zodiac),
    "hints": [
        "The cycle repeats every 12 years, so `year % 12` is the same for 2000, 2012 and 1988. Work out what it is for each year in the table, then write one branch per value.",
        "`2000 % 12` is 8, so a remainder of 8 is the Dragon. `2001 % 12` is 9, the Snake, and so on up to 11, the Sheep. `2004 % 12` wraps round to 0, the Monkey.",
    ],
    "answerNote": "2000 % 12 is 8, so remainder 8 is the Dragon and the table wraps: 2004 gives 0 (Monkey) through 2011 giving 7 (Hare). Any year from 0 up works because % always lands in 0 to 11."}

# ---------------------------------------------------------------- 4 Note to frequency
note = """note = input('Note: ')
letter = note[0]
octave = int(note[1])
if letter == 'C':
    base = 261.63
elif letter == 'D':
    base = 293.66
elif letter == 'E':
    base = 329.63
elif letter == 'F':
    base = 349.23
elif letter == 'G':
    base = 392.00
elif letter == 'A':
    base = 440.00
else:
    base = 493.88
frequency = base * 2 ** (octave - 4)
print(f'{note} has a frequency of {frequency:.2f} Hz.')
"""
E["note"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 14,
    "starter": "note = input('Note: ')\n# Print the frequency of the note.\n",
    "cases": input_cases(note, ("Typed A4", ["A4"]), ("Typed C4", ["C4"]), ("Typed C5", ["C5"]),
                         ("Typed A3", ["A3"]), ("Typed C0", ["C0"]), ("Typed B8", ["B8"]), ("Typed G6", ["G6"])),
    "check": NO_BOOL_OPS + ONE_CHAIN + """assert __code__.count("elif") == 5 and re.search(r"^\\s*else\\s*:", __code__, re.M), "One chain with seven branches, one per letter: an if, five elifs and an else."
assert "[" in __code__, "Pick the letter and the octave digit out of note with indexes."
assert "**" in __code__, "Use ** to double or halve the fourth-octave frequency the right number of times."
assert re.search(r":[^}]*\\.2f\\}", __source__), "Show the frequency with two decimal places."
assert len(__stdout__.strip().splitlines()) == 1, "Print one line."
""",
    "answer": b64(note),
    "hints": [
        "`note[0]` is the letter and `int(note[1])` is the octave number. The chain only needs to know the letter: store that letter's fourth-octave frequency from the table in `base`.",
        "Going up one octave doubles the frequency and going down one halves it. From octave 4 to octave `octave` that is `octave - 4` doublings, so the answer is `base * 2 ** (octave - 4)`. A negative exponent halves.",
        "`A3`: base is 440.00, `octave - 4` is -1, and `440 * 2 ** -1` is 220.00.",
    ],
    "answerNote": "2 ** (octave - 4) is 1 for octave 4, 2 for octave 5, and 0.5 for octave 3, so one multiplication moves the base frequency to any octave."}

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-10-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 10 Boss Problems",
    "short": "L10 bosses",
    "subtitle": "Nested branches and elif chains",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-10/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
