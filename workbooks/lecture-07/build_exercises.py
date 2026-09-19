"""Build workbooks/lecture-07/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-07/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-07
"""
import base64, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=()):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""), capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n")

def example(code, output=True, **kw):
    spec = {"type": "example", "code": code.rstrip("\n"), **kw}
    if output:
        spec["output"] = run(code)
    return spec

def quoted(text):
    """Every reasonable way to write a string literal answer in a blank."""
    return [f"'{text}'", f'"{text}"', text]

def program(starter, solution, cases, xp=5, check=None, **kw):
    """A `code` spec whose cases are scripted input() runs of the model solution."""
    spec = {"type": "code", "xp": xp, "starter": starter,
            "cases": [{"name": name, "inputs": list(inputs), "expected": run(solution, inputs)} for name, inputs in cases],
            "answer": b64(solution), **kw}
    if check:
        spec["check"] = check
    return spec

# A check script that forbids typing the looked-up abbreviations as literals.
NO_LITERAL_LOOKUP = '''import re
literals = [a or b for a, b in re.findall(r"'([^']*)'|\\"([^\\"]*)\\"", __source__)]
for lit in literals:
    assert not (len(lit) == 3 and lit in %s and lit != %r), "Do not type the abbreviation %%r yourself: slice it out of the stored string with calculated boundaries." %% lit
assert "[" in __source__ and ":" in __source__.split("input(")[-1], "Use a slice with calculated start and end boundaries."
'''

E = {}

# ---------------------------------------------------------------- 1. Strings Are Sequences
E["ex-w01"] = example("course = 'COMP 1001'\nmessage = \"Welcome!\"\n\nprint(course)\nprint(message)\n")
E["ex-w02"] = example("word = 'Python'\ncourse = 'COMP 1001'\n\nprint(len(word))\nprint(len(course))\n")
E["cp1-count"] = {"type": "table", "xp": 1, "blanks": {"n1": {"accept": ["6"]}, "n2": {"accept": ["9"]}}}
E["cp1-why"] = {"type": "short", "xp": 2, "answer": b64(
    "A space is a character, so `len()` counts it. `'ice cream'` has three letters, one space, and five letters: 9 characters in total.")}

# ---------------------------------------------------------------- 2. Joining and Repeating Strings
E["ex-w03"] = example("first = 'data'\nsecond = 'science'\nphrase = first + ' ' + second\n\nprint(phrase)\n")
E["ex-w04"] = example("print('-' * 12)\nprint('go! ' * 3)\n")
E["ex-w05"] = example("room = 301\nlabel = 'Room ' + str(room)\nprint(label)\n")
cp2 = "print('COMP' + ' ' + '1001')\nprint('=' * 20)\nprint('Lab ' + str(4))\n"
E["cp2"] = {"type": "code", "xp": 2, "minLines": 6,
    "starter": "# 1. Join 'COMP', one space, and '1001'\nprint(...)\n\n# 2. A line of 20 equals signs\nprint(...)\n\n# 3. Complete the conversion\nprint('Lab ' + ...(4))\n",
    "cases": [{"name": "Program output", "expected": run(cp2)}],
    "check": 'assert "COMP 1001" not in __source__, "Build \'COMP 1001\' from the three pieces with +, rather than typing it as one string."\n'
             'assert "=" * 20 not in __source__, "Use repetition (*) to make the 20 equals signs, rather than typing them."\n'
             'assert "str(" in __source__, "Use str() to turn the number 4 into text before joining it."',
    "answer": b64(cp2)}

# ---------------------------------------------------------------- 3. Character Positions and Indexes
E["ex-w06"] = example("word = 'Python'\n\nprint(word[0])\nprint(word[2])\nprint(word[5])\n")
E["ex-w07"] = example("word = 'Python'\n\nprint(word[-1])\nprint(word[-2])\nprint(word[-6])\n")
E["cp3"] = {"type": "table", "xp": 1, "blanks": {
    "i1": {"accept": quoted("y"), "caseSensitive": True},
    "i2": {"accept": quoted("h"), "caseSensitive": True},
    "i3": {"accept": ["5"]},
    "last": {"accept": ["word[-1]", "word[len(word) - 1]", "word[len(word)-1]", "word[len(word) -1]", "word[len(word)- 1]"],
             "placeholder": "expression", "width": "14rem"}}}

# ---------------------------------------------------------------- 4. Indexes Must Be in Range
E["ex-w08"] = example("word = 'Python'\nprint(word[6])\n", output=False)
E["cp4"] = {"type": "table", "xp": 1, "blanks": {
    "n": {"accept": ["10"]}, "last": {"accept": ["9"]},
    "err": {"accept": ["IndexError", "an IndexError", "IndexError: string index out of range", "index error"], "placeholder": "error name", "width": "12rem"}}}

# ---------------------------------------------------------------- 5. Slicing a String
E["ex-w09"] = example("word = 'Python'\n\nprint(word[0:3])\nprint(word[2:5])\n")
E["ex-w10"] = example("word = 'Python'\n\nprint(word[:3])\nprint(word[3:])\nprint(word[-3:])\nprint(word[:])\n")
E["cp5-slices"] = {"type": "table", "xp": 1, "blanks": {
    "s1": {"accept": ["course[:4]", "course[0:4]", "course[:-4]", "course[0:-4]"], "placeholder": "slice", "width": "10rem"},
    "s2": {"accept": ["course[4:]", "course[4:8]", "course[-4:]", "course[-4:8]"], "placeholder": "slice", "width": "10rem"},
    "s3": {"accept": ["course[2:5]", "course[-6:-3]", "course[2:-3]", "course[-6:5]"], "placeholder": "slice", "width": "10rem"}}}
E["cp5-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The end is a stopping boundary, not a position to include. Excluding it lets two adjacent slices meet cleanly without losing or repeating a character, as in `course[:4] + course[4:]`, and makes the length of `text[a:b]` simply `b - a`.")}

# ---------------------------------------------------------------- 6. Strings Are Immutable
E["ex-w11"] = example("word = 'Python'\nword[0] = 'J'\n", output=False)
E["ex-w12"] = example("word = 'Python'\nnew_word = 'J' + word[1:]\n\nprint(word)\nprint(new_word)\n")
E["cp6-expr"] = {"type": "table", "xp": 1, "blanks": {"e": {
    "accept": ["'h' + label[1:]", "\"h\" + label[1:]", "'h' + label[1:3]", "\"h\" + label[1:3]", "'h' + label[-2:]", "\"h\" + label[-2:]",
               "'h'+label[1:]", "\"h\"+label[1:]", "'h'+label[1:3]", "\"h\"+label[1:3]"],
    "caseSensitive": True, "placeholder": "expression", "width": "14rem"}}}
E["cp6-why"] = {"type": "short", "xp": 2, "answer": b64(
    "No. Strings are immutable, so the expression creates a new string `'hat'` and leaves `label` referring to `'cat'`. Only an assignment such as `label = 'h' + label[1:]` would make the name refer to the new value.")}

# ---------------------------------------------------------------- 7. Methods Create New Strings
E["ex-w13"] = example("name = '  Ada Lovelace  '\nclean_name = name.strip()\nupper_name = clean_name.upper()\n\nprint(name)\nprint(clean_name)\nprint(upper_name)\n")
E["ex-w14"] = example("message = 'red balloon, red kite'\nchanged = message.replace('red', 'blue')\n\nprint(message)\nprint(changed)\n")
cp7 = "title = '  Python Basics  '\n\nclean_title = title.strip()\nclean_title = clean_title.lower()\n\nprint(clean_title)\n"
E["cp7"] = {"type": "code", "xp": 5, "minLines": 6,
    "starter": "title = '  Python Basics  '\n\n# Your statements here\n\nprint(clean_title)\n",
    "cases": [{"name": "Program output", "expected": run(cp7)}],
    "check": "assert title == '  Python Basics  ', \"Leave title as it is: the methods should return new strings, not change the original.\"\n"
             "assert clean_title == 'python basics', 'clean_title should hold the stripped, lowercase text.'\n"
             "assert '.strip(' in __source__ and '.lower(' in __source__, 'Use the .strip() and .lower() methods.'",
    "answer": b64(cp7),
    "answerNote": "The one-line version clean_title = title.strip().lower() is also correct."}
E["cp7-why"] = {"type": "short", "xp": 2, "answer": b64(
    "String methods do not modify `title`; they return a new string. If the result is not assigned to a name, the new value is discarded and nothing is kept.")}

# ---------------------------------------------------------------- 8. Inspecting and Separating Text
E["ex-w15"] = example("message = 'banana bread'\n\nprint(message.find('ana'))\nprint(message.find('z'))\nprint(message.count('a'))\nprint('bread' in message)\nprint('rice' in message)\n")
E["ex-w16"] = example("colours = 'red,green,blue'\npieces = colours.split(',')\nprint(pieces)\n")
E["cp8"] = {"type": "table", "xp": 1, "blanks": {
    "f": {"accept": ["2"]}, "c": {"accept": ["4"]},
    "m": {"accept": ["'sip' in text", "\"sip\" in text"], "caseSensitive": True, "placeholder": "expression", "width": "12rem"},
    "op": {"accept": [".find()", "find()", "find", ".find", "text.find(part)", "text.find()", "text.find(...)", "the find() method", "find method", ".find(part)", "text.find('sip')"],
           "placeholder": "operation", "width": "12rem"}}}

# ---------------------------------------------------------------- 9. Looking at the Digits of a Number
E["ex-w17"] = example("number = 12345\ndigits = str(number)\n\nprint(len(digits))\nprint(digits[0])\nprint(digits[-1])\n")
E["cp9"] = {"type": "table", "xp": 1, "blanks": {
    "n": {"accept": ["len(str(code))"], "placeholder": "expression", "width": "12rem"},
    "d": {"accept": ["str(code)[-1]", "str(code)[4]", "str(code)[len(str(code)) - 1]", "str(code)[len(str(code))-1]"], "placeholder": "expression", "width": "12rem"}}}

# ---------------------------------------------------------------- Final Review
fr = "raw_title = '  Introduction to Python  '\ntitle = raw_title.strip()\nshort_title = title[:12]\n\nprint(title)\nprint(short_title)\nprint(len(title))\nprint('Python' in title)\n"
E["ex-w18"] = example(fr, output=False)
E["fr1"] = {"type": "table", "xp": 1, "blanks": {"t": {"accept": quoted("Introduction to Python"), "caseSensitive": True, "placeholder": "string", "width": "16rem"}}}
E["fr2"] = {"type": "table", "xp": 1, "blanks": {"r": {
    "accept": ["0 through 11", "0-11", "0 - 11", "0 to 11", "0..11", "0…11", "0 up to 11", "0 through 11 inclusive", "0 to 11 inclusive", "0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11", "0,1,2,3,4,5,6,7,8,9,10,11", "indexes 0 through 11", "indexes 0 to 11"],
    "placeholder": "e.g. 3 through 7", "width": "12rem"}}}
fr_lines = run(fr).split("\n")
E["fr3"] = {"type": "table", "xp": 1, "blanks": {
    f"l{i + 1}": {"accept": [line], "caseSensitive": True, "placeholder": f"line {i + 1}", "width": "16rem"} for i, line in enumerate(fr_lines)}}
E["fr4"] = {"type": "short", "xp": 2, "answer": b64(
    "No. `.strip()` returns a new string, which is assigned to `title`. Strings are immutable, so `raw_title` still refers to `'  Introduction to Python  '` with its outer spaces.")}
E["ex-w18-run"] = example(fr)

# ---------------------------------------------------------------- Putting It All Together
E["ex-w19"] = example("raw_name = input('Name: ')\nraw_code = input('Course code: ')\n\nname = raw_name.strip()\ncode = raw_code.strip().upper()\n", output=False)
badge = ("raw_name = input('Name: ')\nraw_code = input('Course code: ')\n\n"
         "name = raw_name.strip()\ncode = raw_code.strip().upper()\nbadge = name + ' | ' + code\nborder = '-' * len(badge)\n\n"
         "print(border)\nprint(badge)\nprint(border)\nprint('COMP course:', 'COMP' in code)\n")
E["badge"] = program(
    "raw_name = input('Name: ')\nraw_code = input('Course code: ')\n\nname = ...\ncode = ...\nbadge = ...\nborder = ...\n\n"
    "print(border)\nprint(badge)\nprint(border)\nprint('COMP course:', ...)\n",
    badge,
    [("Ada Lovelace, comp1001", ["  Ada Lovelace  ", " comp1001 "]), ("Li, art", ["Li", "art"]), ("Grace Hopper, COMP 2001", ["Grace Hopper ", "comp 2001"])],
    xp=10, minLines=12,
    check="assert '.strip(' in __source__, 'Use .strip() to remove the outer whitespace from both inputs.'\n"
          "assert '.upper(' in __source__, 'Use .upper() to store the course code in uppercase.'\n"
          "assert 'len(' in __source__, 'Make the border exactly as long as the badge by repeating \"-\" len(badge) times.'\n"
          "assert ' in ' in __source__, \"Use the in operator to report whether 'COMP' occurs in the code.\"")

# ---------------------------------------------------------------- Coding Practice
E["cpr1"] = {"type": "table", "xp": 1, "blanks": {
    "v1": {"accept": ["8"]}, "t1": {"accept": ["int"]},
    "v2": {"accept": quoted("ce"), "caseSensitive": True}, "t2": {"accept": ["str"]},
    "v3": {"accept": quoted("icecream"), "caseSensitive": True}, "t3": {"accept": ["str"]},
    "v4": {"accept": quoted("creamice"), "caseSensitive": True}, "t4": {"accept": ["str"]},
    "v5": {"accept": quoted("iceice"), "caseSensitive": True}, "t5": {"accept": ["str"]}}}
E["ex-p02"] = example("n = 4\nnumeric_result = n + n\n\ndigit = '4'\ntext_result = digit + digit\n", output=False)
E["cpr2"] = {"type": "short", "xp": 2, "answer": b64(
    "`numeric_result` is the integer `8` because `+` adds two `int` values. `text_result` is the string `'44'` because `+` between two strings means concatenation: the characters are joined end to end. The operator does different work depending on the types of its operands.")}
E["cpr3"] = {"type": "table", "xp": 1, "blanks": {
    "first": {"accept": ["word[0]"], "placeholder": "expression", "width": "12rem"},
    "last": {"accept": ["word[-1]", "word[len(word) - 1]", "word[len(word)-1]"], "placeholder": "expression", "width": "12rem"},
    "mid": {"accept": ["word[len(word) // 2]", "word[len(word)//2]", "word[(len(word) - 1) // 2]", "word[(len(word)-1)//2]", "word[len(word) // 2 ]"], "placeholder": "expression", "width": "12rem"}}}
weekday = "days = 'SunMonTueWedThuFriSat'\nday_number = int(input('Day number (0-6): '))\n\nstart = 3 * day_number\nabbreviation = days[start:start + 3]\nprint(abbreviation)\n"
E["cpr4"] = program(
    "days = 'SunMonTueWedThuFriSat'\nday_number = int(input('Day number (0-6): '))\n\nstart = ...\nabbreviation = ...\nprint(abbreviation)\n",
    weekday, [("Day 0", ["0"]), ("Day 6", ["6"]), ("Day 3", ["3"])],
    check=NO_LITERAL_LOOKUP % ("'SunMonTueWedThuFriSat'", "Day"))
swap = "word = 'seesaw'\nfirst = 's'\nsecond = 'e'\n\nword = word.replace(first, '*')\nword = word.replace(second, first)\nword = word.replace('*', second)\n\nprint(word)\n"
E["cpr5"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "word = 'seesaw'\nfirst = 's'\nsecond = 'e'\n\n# Three .replace() calls, each stored back in word\n\nprint(word)\n",
    "cases": [{"name": "seesaw", "expected": run(swap)},
              {"name": "excess", "rewrite": [["word = 'seesaw'", "word = 'excess'"]], "expected": run(swap.replace("word = 'seesaw'", "word = 'excess'"))}],
    "check": "assert __source__.count('.replace(') >= 3, 'Use three .replace() calls: one to the temporary character, and two to swap.'\n"
             "assert \"'*'\" in __source__ or '\"*\"' in __source__, \"Use '*' as the temporary character.\"\n"
             "assert 'word = word.replace' in __source__.replace('  ', ' '), 'Store each result back in word; .replace() returns a new string.'",
    "answer": b64(swap)}
E["cpr5-value"] = {"type": "table", "xp": 1, "blanks": {"v": {"accept": quoted("esseaw"), "caseSensitive": True, "placeholder": "final value"}}}
middle = "text = 'Python'\nmiddle = len(text) // 2\n\nprint(text[0])\nprint(text[-1])\nprint(text[middle])\nprint(text[middle - 1:middle + 1])\n"
E["cpr6"] = {"type": "code", "xp": 5, "minLines": 7,
    "starter": "text = 'Python'\nmiddle = len(text) // 2\n\nprint(...)  # 1. first character\nprint(...)  # 2. last character\nprint(...)  # 3. single middle character (odd length)\nprint(...)  # 4. middle two characters (even length)\n",
    "cases": [{"name": "text = 'Python' (even length)", "expected": run(middle)},
              {"name": "text = 'racecar' (odd length)", "rewrite": [["text = 'Python'", "text = 'racecar'"]], "expected": run(middle.replace("text = 'Python'", "text = 'racecar'"))}],
    "check": "import re\nfor n in re.findall(r'text\\[\\s*(-?\\d+)', __source__):\n    assert n in ('0', '-1'), 'Do not use fixed numeric indexes (other than 0 and -1); calculate them from len(text).'",
    "answer": b64(middle)}
month = "months = 'JanFebMarAprMayJunJulAugSepOctNovDec'\nmonth_number = int(input('Month number (1-12): '))\n\nstart = 3 * (month_number - 1)\nmonth = months[start:start + 3]\nprint(month)\n"
E["cpr7"] = program(
    "months = 'JanFebMarAprMayJunJulAugSepOctNovDec'\nmonth_number = int(input('Month number (1-12): '))\n\nstart = ...\nmonth = ...\nprint(month)\n",
    month, [("Month 1", ["1"]), ("Month 12", ["12"]), ("Month 7", ["7"])],
    check=NO_LITERAL_LOOKUP % ("'JanFebMarAprMayJunJulAugSepOctNovDec'", "Jan"))
abbrev = "word = input('Word: ')\nabbreviation = word[:3] + '...' + word[-3:]\nprint(abbreviation)\n"
E["cpr8"] = program("word = input('Word: ')\nabbreviation = ...\nprint(abbreviation)\n", abbrev,
    [("Mississippi", ["Mississippi"]), ("Python", ["Python"]), ("Newfoundland", ["Newfoundland"])])
phone = "digits = input('Ten digits: ')\n\nformatted = '(' + digits[:3] + ') '\nformatted = formatted + digits[3:6] + '-' + digits[6:]\nprint(formatted)\n"
E["cpr9"] = program("digits = input('Ten digits: ')\n\nformatted = ...\nprint(formatted)\n", phone,
    [("7095550123", ["7095550123"]), ("0123456789", ["0123456789"])],
    check="import re\nassert not re.search(r'\\bint\\(', __source__), 'Keep the input as a string so that a leading zero is preserved.'",
    answerNote="A single expression '(' + digits[:3] + ') ' + digits[3:6] + '-' + digits[6:] is also fine.")
path = "folder = input('Folder: ')\nname = input('File name: ')\nextension = input('Extension: ')\n\npath = folder + '/' + name + '.' + extension\nprint(path)\n"
E["cpr10"] = program("folder = input('Folder: ')\nname = input('File name: ')\nextension = input('Extension: ')\n\npath = ...\nprint(path)\n", path,
    [("notes/lecture07.txt", ["notes", "lecture07", "txt"]), ("images/logo.png", ["images", "logo", "png"])])
comma = "digits = input('Five digits: ')\nformatted = digits[:2] + ',' + digits[2:]\nprint(formatted)\n"
E["cpr11"] = program("digits = input('Five digits: ')\nformatted = ...\nprint(formatted)\n", comma,
    [("23456", ["23456"]), ("10000", ["10000"])])
thousands = "digits = input('Whole number: ')\nformatted = digits[:-3] + ',' + digits[-3:]\nprint(formatted)\n"
E["cpr12"] = program("digits = input('Whole number: ')\nformatted = ...\nprint(formatted)\n", thousands,
    [("1000", ["1000"]), ("999999", ["999999"]), ("12345", ["12345"])],
    check="import re\nassert not re.search(r'\\bint\\(', __source__), 'Do not convert the input to an integer; slice the text.'")
frame = "name = input('Name: ')\n\nborder = '+' + '-' * (len(name) + 2) + '+'\nmiddle = '| ' + name + ' |'\n\nprint(border)\nprint(middle)\nprint(border)\n"
E["cpr13"] = program("name = input('Name: ')\n\nborder = ...\nmiddle = ...\n\nprint(border)\nprint(middle)\nprint(border)\n", frame,
    [("Ada", ["Ada"]), ("Li", ["Li"]), ("Grace Hopper", ["Grace Hopper"])],
    check="import re\nassert not re.search(r'-{2,}', __source__), 'Build the border by repeating \"-\" with *, not by typing a fixed run of hyphens.'\n"
          "assert 'len(' in __source__, 'Use len(name) so the border fits any name.'")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-07",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 7 Workbook",
    "subtitle": "Strings",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-07/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
