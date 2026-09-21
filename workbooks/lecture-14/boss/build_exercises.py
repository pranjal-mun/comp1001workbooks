"""Build workbooks/lecture-14/boss/exercises.json: the Lecture 14 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_14_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Run from anywhere:

    python3 workbooks/lecture-14/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-14/boss
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

NO_IMPORT = 'assert "import" not in __code__, "Solve it with a for loop and the string tools from this lecture; no import is needed."\n'
ONE_FOR = '''import re
assert len(re.findall(r"^\\s*for\\b", __code__, re.M)) == 1, "Use exactly one for loop."
assert "while" not in __code__, "A for loop fits here; no while loop is needed."
'''

E = {}

# ---------------------------------------------------------------- 1 Forecast Conversion Table
forecast = """start = int(input())
end = int(input())

print('Celsius Fahrenheit')
for celsius in range(start, end + 1, 10):
    fahrenheit = celsius * 9 / 5 + 32
    print(celsius, fahrenheit)
"""
E["forecast"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 8,
    "starter": "start = int(input())\nend = int(input())\n\nprint('Celsius Fahrenheit')\n# Write the loop.\n",
    "cases": input_cases(forecast, ("Typed -20, 0", ["-20", "0"]), ("Typed 30, 30", ["30", "30"]), ("Typed 0, 50", ["0", "50"]),
                         ("Typed -100, 100", ["-100", "100"]), ("Typed -30, -10", ["-30", "-10"])),
    "check": ONE_FOR + NO_IMPORT + '''assert re.search(r"range\\([^()]*,[^()]*,[^()]*\\)", __code__), "Give range() a start, a stop and a step of 10."
assert __stdout__.startswith("Celsius Fahrenheit"), "Keep the heading line Celsius Fahrenheit before the loop."
''',
    "answer": b64(forecast),
    "hints": [
        'The rows are `start`, `start + 10`, and so on up to `end`, so the loop is `for celsius in range(start, ?, 10):`.',
        'The stop value of a range is excluded, so `range(start, end, 10)` leaves out `end`. Use an excluded stop of `end + 1`: every value changes by 10, so adding 1 places the stop past `end` without adding a row.',
        'Inside the loop compute `fahrenheit = celsius * 9 / 5 + 32` and print `celsius` and `fahrenheit` with one `print()`.',
    ],
    "answerNote": "Use an excluded stop of end + 1. Because every value changes by 10, adding 1 places the excluded stop past end."}
assert E["forecast"]["cases"][0]["expected"] == "Celsius Fahrenheit\n-20 -4.0\n-10 14.0\n0 32.0"
assert E["forecast"]["cases"][1]["expected"] == "Celsius Fahrenheit\n30 86.0"

# ---------------------------------------------------------------- 2 Mirror Word Check
mirror = """word = input()
reversed_word = ''

for character in word:
    reversed_word = character + reversed_word

if word == reversed_word:
    print('Mirror word')
else:
    print('Not a mirror word')
"""
E["mirror"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 10,
    "starter": "word = input()\nreversed_word = ''\n\n# Build reversed_word, then compare the strings.\n",
    "cases": input_cases(mirror, ("Typed level", ["level"]), ("Typed an empty string", [""]), ("Typed Level", ["Level"]),
                         ("Typed noon", ["noon"]), ("Typed python", ["python"]), ("Typed a", ["a"]), ("Typed abba", ["abba"]), ("Typed abc", ["abc"])),
    "check": ONE_FOR + NO_IMPORT + '''assert "[::" not in __code__ and "reversed(" not in __code__, "Build the reversed string with the for loop, not with slicing or reversed()."
assert ".lower(" not in __code__ and ".upper(" not in __code__ and ".casefold(" not in __code__, "Compare uppercase and lowercase characters exactly; do not change the case."
assert __stdout__.count("\\n") <= 1, "Print exactly one line."
''',
    "answer": b64(mirror),
    "hints": [
        'Visit each character with `for character in word:`. On every pass, put the character in front of what has been built so far: `reversed_word = character + reversed_word`.',
        'Trace `level`: after each pass `reversed_word` is `l`, `el`, `vel`, `evel`, `level`. Putting the character first is what reverses the order.',
        'After the loop, one `if word == reversed_word:` with an `else` chooses between `Mirror word` and `Not a mirror word`. An empty word gives an empty reversed word, so it is a mirror word.',
    ],
    "answerNote": "Add each character to the front of reversed_word. Then one if/else chooses the message."}
assert E["mirror"]["cases"][0]["expected"] == "Mirror word"
assert E["mirror"]["cases"][1]["expected"] == "Mirror word"
assert E["mirror"]["cases"][2]["expected"] == "Not a mirror word"

# ---------------------------------------------------------------- 3 Sensor Parity Bit
parity = """bits = input()
ones = 0
valid = len(bits) == 8

for bit in bits:
    if bit not in '01':
        valid = False
    if bit == '1':
        ones = ones + 1

if not valid:
    print('Invalid data')
elif ones % 2 == 0:
    print('Parity bit: 0')
else:
    print('Parity bit: 1')
"""
E["parity"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 14,
    "starter": "bits = input()\nones = 0\nvalid = len(bits) == 8\n\n# Inspect every character, then print one result.\n",
    "cases": input_cases(parity, ("Typed 10110010", ["10110010"]), ("Typed 00000001", ["00000001"]), ("Typed 1011", ["1011"]),
                         ("Typed an empty string", [""]), ("Typed 11111111", ["11111111"]), ("Typed 00000000", ["00000000"]),
                         ("Typed 1011001a", ["1011001a"]), ("Typed 101100100", ["101100100"]), ("Typed 10110012", ["10110012"]), ("Typed 11100000", ["11100000"])),
    "check": NO_IMPORT + '''import re
assert len(re.findall(r"^\\s*(for|while)\\b", __code__, re.M)) == 1, "Use one loop to validate the characters and count the 1 characters."
assert re.search(r"^\\s*for\\b", __code__, re.M), "Visit the characters with a for loop."
assert ".count(" not in __code__, "Count the 1 characters inside the loop, not with .count()."
assert re.search(r"%\\s*2\\b", __code__), "Test whether the count of 1 characters is even with % 2."
assert __stdout__.count("\\n") <= 1, "Print exactly one line."
''',
    "answer": b64(parity),
    "hints": [
        '`valid` already records whether the length is 8. In the loop, `if bit not in \'01\':` sets `valid = False`; a second `if bit == \'1\':` adds 1 to `ones`.',
        'The two `if` statements are independent: a `1` must be counted, and a bad character must clear the flag. Do not use `elif` between them.',
        'After the loop, test `not valid` first and print `Invalid data`. Otherwise `ones % 2 == 0` means the total is already even, so the parity bit is 0; else it is 1.',
    ],
    "answerNote": "The validity flag starts by checking the length. The loop changes it to False if a character is outside '01' and counts each 1."}
assert E["parity"]["cases"][0]["expected"] == "Parity bit: 0"
assert E["parity"]["cases"][1]["expected"] == "Parity bit: 1"
assert E["parity"]["cases"][2]["expected"] == "Invalid data"
assert E["parity"]["cases"][3]["expected"] == "Invalid data"
assert E["parity"]["cases"][6]["expected"] == "Invalid data"
assert E["parity"]["cases"][9]["expected"] == "Parity bit: 1"

# ---------------------------------------------------------------- 4 Shifted Course Note
shift = """message = input()
shift = int(input())
lowercase = 'abcdefghijklmnopqrstuvwxyz'
uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
shifted = ''

for character in message:
    if character in lowercase:
        position = lowercase.find(character)
        new_position = (position + shift) % 26
        shifted = shifted + lowercase[new_position]
    elif character in uppercase:
        position = uppercase.find(character)
        new_position = (position + shift) % 26
        shifted = shifted + uppercase[new_position]
    else:
        shifted = shifted + character

print(shifted)
"""
E["shift"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 18,
    "starter": ("message = input()\nshift = int(input())\nlowercase = 'abcdefghijklmnopqrstuvwxyz'\nuppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'\nshifted = ''\n\n"
                "# Visit each character and build shifted.\nprint(shifted)\n"),
    "cases": input_cases(shift, ("Typed COMP 1001, 3", ["COMP 1001", "3"]), ("Typed abc XYZ, -3", ["abc XYZ", "-3"]), ("Typed an empty string, 8", ["", "8"]),
                         ("Typed Hello, World!, 26", ["Hello, World!", "26"]), ("Typed xyz, 100", ["xyz", "100"]), ("Typed Zebra-42, -100", ["Zebra-42", "-100"]),
                         ("Typed attack at dawn, 13", ["attack at dawn", "13"]), ("Typed MUN, 0", ["MUN", "0"])),
    "check": ONE_FOR + NO_IMPORT + '''assert "ord(" not in __code__ and "chr(" not in __code__, "Find each letter in the alphabet strings; ord() and chr() are not needed."
assert ".find(" in __code__ or ".index(" in __code__, "Use find() to get each letter's position in the matching alphabet string."
assert re.search(r"%\\s*26\\b", __code__), "Wrap the new position with the remainder after division by 26."
assert re.search(r"shifted\\s*(\\+=|=\\s*shifted\\s*\\+)", __code__), "Build the answer in the string accumulator shifted."
''',
    "answer": b64(shift),
    "hints": [
        'For each character decide which of three cases it is: `if character in lowercase:`, `elif character in uppercase:`, `else:`. In the `else` branch add the character to `shifted` unchanged.',
        'For a lowercase letter, `position = lowercase.find(character)` is 0 for `a` through 25 for `z`. The new position is `(position + shift) % 26`: the remainder wraps past `z` and also handles a negative shift.',
        'Add `lowercase[new_position]` to `shifted`. The uppercase branch is the same with `uppercase` in place of `lowercase`.',
        'Trace `abc` with shift `-3`: `a` is at 0, `(0 - 3) % 26` is 23, and `lowercase[23]` is `x`.',
    ],
    "answerNote": "Use the lowercase alphabet for lowercase letters and the uppercase alphabet for uppercase letters. Add every non-letter without changing it."}
assert E["shift"]["cases"][0]["expected"] == "FRPS 1001"
assert E["shift"]["cases"][1]["expected"] == "xyz UVW"
assert E["shift"]["cases"][2]["expected"] == ""
assert E["shift"]["cases"][3]["expected"] == "Hello, World!"

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-14-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 14 Boss Problems",
    "short": "L14 bosses",
    "subtitle": "The for loop and ranges",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-14/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
