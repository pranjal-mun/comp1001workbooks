"""Build workbooks/lecture-07/boss/exercises.json: the Lecture 7 boss problems.

Expected outputs are produced by actually running the model solutions. Run
from anywhere:

    python3 workbooks/lecture-07/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-07/boss
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

def input_cases(solution, *runs):
    return [{"name": name, "inputs": list(inputs), "expected": run(solution, inputs)} for name, inputs in runs]

NO_IF = 'assert "if " not in __source__, "No if statements are needed."\n'
NO_SHORTCUTS = 'assert ".split(" not in __source__ and ".title(" not in __source__ and ".capitalize(" not in __source__, "Use .find() and slices to take the name apart; .split(), .title(), and .capitalize() are not part of this lecture."\n'

E = {}

# ---------------------------------------------------------------- 1 Digits
digits = """number = 3141
digits = str(number)
d1 = int(digits[0])
d2 = int(digits[1])
d3 = int(digits[2])
d4 = int(digits[3])
total = d1 + d2 + d3 + d4
print(f'{d1} + {d2} + {d3} + {d4} = {total}')
"""
E["digits"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 8,
    "starter": "number = 3141\n# Print the four digits added together and their sum.\n",
    "cases": cases(digits, "3141",
        ("8642", [["number = 3141", "number = 8642"]]),
        ("1000", [["number = 3141", "number = 1000"]]),
        ("2026", [["number = 3141", "number = 2026"]])),
    "check": NO_IF + """assert type(number) is int, "Keep number as an int; make a text copy with str() instead of changing the assignment."
assert "str(" in __source__, "Use str() to get the digits as characters."
assert "[" in __source__, "Pick out each digit with an index, as in digits[0]."
assert "//" not in __source__ and "%" not in __source__, "This time take the digits apart as characters, not with // and %."
assert __stdout__.count("+") == 3 and "=" in __stdout__, "Print the four digits joined by + signs, then = and the sum."
assert len(__stdout__.strip().splitlines()) == 1, "Print everything on one line with a single print() call."
""",
    "answer": b64(digits),
    "answerNote": "Each digits[i] is a one-character string. int() turns it back into a number before the addition."}

# ---------------------------------------------------------------- 2 Mailing label
label = """name = 'Pranjal Patra'
street = '230 Elizabeth Avenue'
city = "St. John's"
province = 'nl'
postal = 'a1c 5s7'
line_1 = name.upper()
line_2 = street.upper()
line_3 = city.upper() + ' ' + province.upper() + '  ' + postal.upper()
print(line_1)
print(line_2)
print(line_3)
print('-' * len(line_3))
"""
E["label"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 9,
    "starter": "name = 'Pranjal Patra'\nstreet = '230 Elizabeth Avenue'\ncity = \"St. John's\"\nprovince = 'nl'\npostal = 'a1c 5s7'\n# Print the label in capitals, then a line of dashes under it.\n",
    "cases": cases(label, "Memorial University",
        ("Water Street", [["name = 'Pranjal Patra'", "name = 'Ada Lovelace'"], ["street = '230 Elizabeth Avenue'", "street = '12 Water Street'"], ["postal = 'a1c 5s7'", "postal = 'A1C 1A1'"]]),
        ("Corner Brook", [["name = 'Pranjal Patra'", "name = 'Oliver Poodle'"], ["street = '230 Elizabeth Avenue'", "street = '1 Bark Lane'"], ["city = \"St. John's\"", "city = 'Corner Brook'"], ["postal = 'a1c 5s7'", "postal = 'a2h 6p9'"]]),
        ("Gander", [["name = 'Pranjal Patra'", "name = 'Sabina'"], ["street = '230 Elizabeth Avenue'", "street = '9 Whisker Way'"], ["city = \"St. John's\"", "city = 'gander'"], ["province = 'nl'", "province = 'Nl'"], ["postal = 'a1c 5s7'", "postal = 'a1v 1w8'"]])),
    "check": NO_IF + """import re
assert ".upper(" in __source__, "Use .upper() to make the capitals; do not retype the values."
assert "len(" in __source__ and re.search(r"['\\"]-['\\"]\\s*\\*|\\*\\s*['\\"]-['\\"]", __source__), "Make the dashes with '-' * len(...) so the line is exactly as long as the address line."
lines = __stdout__.strip().splitlines()
assert len(lines) == 4, "Print four lines: name, street, address line, dashes."
assert lines[2].count("  ") == 1, "Put exactly two spaces between the province and the postal code."
""",
    "answer": b64(label),
    "answerNote": "Every .upper() returns a new string; the five variables at the top keep their original text."}

# ---------------------------------------------------------------- 3 MUN email
email = """name = 'Pranjal Patra'
space = name.find(' ')
first = name[:space]
last = name[space + 1:]
initials = first[0].upper() + '.' + last[0].upper() + '.'
email = (first[0] + last).lower() + '@mun.ca'
print(f'Initials: {initials}')
print(f'Email: {email}')
"""
E["email"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 8,
    "starter": "name = 'Pranjal Patra'\n# Print the initials and the MUN email address.\n",
    "cases": cases(email, "Pranjal Patra",
        ("Ada Lovelace", [["name = 'Pranjal Patra'", "name = 'Ada Lovelace'"]]),
        ("grace hopper", [["name = 'Pranjal Patra'", "name = 'grace hopper'"]]),
        ("Oliver Poodle", [["name = 'Pranjal Patra'", "name = 'Oliver Poodle'"]])),
    "check": NO_IF + NO_SHORTCUTS + """import re
assert ".find(" in __source__, "Find the space with .find(' ') rather than counting characters by hand."
assert re.search(r"\\[[^\\]]*:[^\\]]*\\]", __source__), "Use slices to cut the first name and the last name out of name."
assert ".lower(" in __source__ and ".upper(" in __source__, "Use .lower() for the email address and .upper() for the initials."
assert len(__stdout__.strip().splitlines()) == 2, "Print two lines: the initials, then the email address."
""",
    "answer": b64(email),
    "answerNote": "name[:space] stops just before the space and name[space + 1:] starts just after it."}

# ---------------------------------------------------------------- 4 Clean up the name
tidy = """raw = input('Name: ')
name = raw.strip()
space = name.find(' ')
first = name[:space]
last = name[space + 1:]
first = first[0].upper() + first[1:].lower()
last = last[0].upper() + last[1:].lower()
print(f'Hello, {first} {last}!')
print(f'Roster: {last.upper()}, {first}')
print(f'Typed {len(raw)} characters, kept {len(first) + len(last) + 1}.')
"""
E["tidy"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 10,
    "starter": "raw = input('Name: ')\n# Clean up the name, then print the greeting, the roster line, and the character counts.\n",
    "cases": input_cases(tidy, ("Typed '  pRANJAL patra '", ["  pRANJAL patra "]),
                         ("Typed 'ada LOVELACE  '", ["ada LOVELACE  "]),
                         ("Typed ' oliver poodle'", [" oliver poodle"]),
                         ("Typed 'SABINA cat '", ["SABINA cat "])),
    "check": NO_IF + NO_SHORTCUTS + """import re
assert raw != raw.strip(), "Keep raw exactly as typed. .strip() returns a new string; store it under another name."
assert ".strip(" in __source__, "Remove the outer spaces with .strip()."
assert ".find(" in __source__, "Find the space with .find(' ') rather than counting characters by hand."
assert re.search(r"\\[[^\\]]*:[^\\]]*\\]", __source__), "Use slices to cut the first name and the last name apart."
assert ".upper(" in __source__ and ".lower(" in __source__, "Fix the capitals with .upper() and .lower()."
assert "len(" in __source__, "Count the characters with len()."
assert len(__stdout__.strip().splitlines()) == 3, "Print three lines: the greeting, the roster line, and the character counts."
""",
    "answer": b64(tidy),
    "answerNote": "A string cannot be changed in place. first[0].upper() + first[1:].lower() builds a new one with one capital."}

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-07-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 7 Boss Problems",
    "short": "L07 bosses",
    "subtitle": "Strings",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-07/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
