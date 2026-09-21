"""Build workbooks/lecture-14/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-14/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-14
"""
import base64, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=()):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""), capture_output=True, text=True)
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

def example(code, output=True, **kw):
    spec = {"type": "example", "code": code.rstrip("\n"), **kw}
    if output:
        spec["output"] = run(code)
    return spec

def case(name, inputs, code=None, check=None):
    """A grading case: `expected` from running the model answer with `inputs`."""
    c = {"name": name, "inputs": list(inputs)}
    if code is not None:
        c["expected"] = run_with_prompts(code, inputs)
    if check:
        c["check"] = check
    return c

def num(*values, width="4rem"):
    return {"accept": [str(v) for v in values], "placeholder": "value", "width": width}

def yes_no(value):
    return {"accept": ["yes", "y", "true"] if value else ["no", "n", "false"], "placeholder": "yes / no", "width": "6rem", "show": "yes" if value else "no"}

def seq(*values, width="9rem"):
    """A cell holding the values a range supplies, such as `0, 1, 2`."""
    if not values:
        return {"accept": ["none", "no values", "nothing", "(none)", "no value", "empty", "-", "0 values", "none supplied"],
                "placeholder": "values", "width": width, "show": "no values"}
    parts = [str(v) for v in values]
    forms = [", ".join(parts), ",".join(parts), " ".join(parts), "; ".join(parts), " and ".join(parts)]
    if len(parts) > 1:
        forms.append(", ".join(parts[:-1]) + " and " + parts[-1])
        forms.append(", ".join(parts[:-1]) + ", and " + parts[-1])
    return {"accept": forms, "placeholder": "values", "width": width, "show": forms[0]}

def rng(start, stops, step=None, width="10rem"):
    """A cell holding a range call. `stops` lists every stop value that gives
    the wanted sequence; spacing after the commas is optional."""
    forms = []
    for stop in stops:
        args = [str(start), str(stop)] + ([str(step)] if step is not None else [])
        forms.append("range(" + ", ".join(args) + ")")
        forms.append("range(" + ",".join(args) + ")")
        if step is None:
            forms.append(f"range({start}, {stop}, 1)")
            forms.append(f"range({start},{stop},1)")
    return {"accept": forms, "placeholder": "range(...)", "width": width, "show": forms[0], "caseSensitive": True}

def loop_kind(kind):
    other = "while" if kind == "for" else "for"
    return {"accept": [kind, f"{kind} loop", f"a {kind} loop", f"{kind} loop"], "placeholder": "for / while", "width": "7rem", "show": kind}

E = {}

# ============================================================ 1. A for loop visits each item
for5 = "for number in range(5):\n    print(number)\n"
E["ex-for5"] = example(for5)
assert E["ex-for5"]["output"] == "0\n1\n2\n3\n4"
E["cp1"] = {"type": "table", "xp": 1, "blanks": {
    "first": num(0), "last": num(4), "count": num(5),
    "body": {"accept": ["print(number)", "print number", "print"], "caseSensitive": True, "placeholder": "statement", "width": "10rem", "show": "print(number)"}}}

# ============================================================ 2. range(n)
E["ex-range4"] = example("for i in range(4):\n    print(i, end=' ')\nprint()\n")
assert E["ex-range4"]["output"].rstrip() == "0 1 2 3"
E["ex-check3"] = example("for step in range(3):\n    print('Check the result')\n")
assert E["ex-check3"]["output"] == "Check the result\nCheck the result\nCheck the result"
E["cp2"] = {"type": "table", "xp": 1, "blanks": {
    "r3": seq(0, 1, 2), "r1": seq(0), "r0": seq(), "r8": num(8)}}
assert list(range(3)) == [0, 1, 2] and list(range(1)) == [0] and list(range(0)) == [] and len(range(8)) == 8

# ============================================================ 3. range(start, stop)
E["ex-range16"] = example("for number in range(1, 6):\n    print(number, end=' ')\nprint()\n")
assert E["ex-range16"]["output"].rstrip() == "1 2 3 4 5"
E["ex-total"] = example("total = 0\nfor number in range(1, 6):\n    total = total + number\nprint('Total:', total)\n")
assert E["ex-total"]["output"] == "Total: 15"
E["cp3"] = {"type": "table", "xp": 1, "blanks": {
    "r37": rng(3, [8]), "r1015": rng(10, [16]), "n49": num(5)}}
assert list(range(3, 8)) == [3, 4, 5, 6, 7] and list(range(10, 16)) == list(range(10, 16)) and len(range(4, 9)) == 5
E["cp3-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why is the stop value one larger?", "answer": b64(
    "The stop value is excluded, so it must be one larger than the last value when the step is 1.")}

# ============================================================ 4. range(start, stop, step)
E["ex-step2"] = example("for number in range(0, 10, 2):\n    print(number, end=' ')\nprint()\n")
assert E["ex-step2"]["output"].rstrip() == "0 2 4 6 8"
assert list(range(2, 9, 2)) == [2, 4, 6, 8] and list(range(1, 10, 3)) == [1, 4, 7] and list(range(5, 16, 5)) == [5, 10, 15]
E["cp4"] = {"type": "table", "xp": 1, "blanks": {
    "r182": seq(1, 3, 5, 7), "r4134": seq(4, 8, 12),
    "tens": rng(10, [51, 52, 53, 54, 55, 56, 57, 58, 59, 60], 10, width="12rem")}}
assert list(range(1, 8, 2)) == [1, 3, 5, 7] and list(range(4, 13, 4)) == [4, 8, 12]
for stop in range(51, 61):
    assert list(range(10, stop, 10)) == [10, 20, 30, 40, 50]

# ============================================================ 5. Counting backwards
E["ex-countdown"] = example("for number in range(5, 0, -1):\n    print(number)\nprint('Go!')\n")
assert E["ex-countdown"]["output"] == "5\n4\n3\n2\n1\nGo!"
assert list(range(5, -1, -1)) == [5, 4, 3, 2, 1, 0] and list(range(5, 0)) == []
E["cp5"] = {"type": "table", "xp": 1, "blanks": {
    "r40": seq(4, 3, 2, 1), "r4m1": seq(4, 3, 2, 1, 0),
    "evens": rng(10, [0, 1], -2, width="12rem")}}
assert list(range(4, 0, -1)) == [4, 3, 2, 1] and list(range(4, -1, -1)) == [4, 3, 2, 1, 0]
for stop in (0, 1):
    assert list(range(10, stop, -2)) == [10, 8, 6, 4, 2]

# ============================================================ 6. Choosing a loop
E["ex-for-count"] = example("for number in range(1, 6):\n    print(number)\n")
E["ex-while-count"] = example("number = 1\nwhile number <= 5:\n    print(number)\n    number = number + 1\n")
assert E["ex-for-count"]["output"] == E["ex-while-count"]["output"] == "1\n2\n3\n4\n5"
E["cp6"] = {"type": "table", "xp": 1, "blanks": {
    "hundred": loop_kind("for"), "done": loop_kind("while"), "word": loop_kind("for"), "balance": loop_kind("while")}}

# ============================================================ 7. The loop variable
E["ex-loopvar"] = example("for i in range(3):\n    print('Start:', i)\n    i = 100\n    print('Changed:', i)\n")
assert E["ex-loopvar"]["output"] == "Start: 0\nChanged: 100\nStart: 1\nChanged: 100\nStart: 2\nChanged: 100"
E["cp7"] = {"type": "table", "xp": 1, "blanks": {
    "pass2": num(1),
    "header": {"accept": ["for number in range(1, 6):", "for number in range(1, 6)", "for number in range(1,6):", "for number in range(1,6)",
                          "for value in range(1, 6):", "for value in range(1, 6)", "for value in range(1,6):", "for value in range(1,6)",
                          "for count in range(1, 6):", "for count in range(1, 6)", "for count in range(1,6):", "for count in range(1,6)",
                          "for n in range(1, 6):", "for n in range(1, 6)", "for n in range(1,6):", "for n in range(1,6)",
                          "for step in range(1, 6):", "for step in range(1, 6)", "for step in range(1,6):", "for step in range(1,6)",
                          "for day in range(1, 6):", "for day in range(1, 6)", "for day in range(1,6):", "for day in range(1,6)",
                          "for item in range(1, 6):", "for item in range(1, 6)", "for item in range(1,6):", "for item in range(1,6)",
                          "for integer in range(1, 6):", "for integer in range(1, 6)", "for integer in range(1,6):", "for integer in range(1,6)"],
               "caseSensitive": True, "placeholder": "for ... in range(1, 6):", "width": "16rem", "show": "for number in range(1, 6):"}}}
E["cp7-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why is the assignment ineffective?", "answer": b64(
    "The loop assigns the next value from the range at the start of every pass, so the assignment to 100 is overwritten.")}

# ============================================================ 8. Looping directly over a string
E["ex-chars"] = example("word = 'Python'\n\nfor character in word:\n    print(character)\n")
assert E["ex-chars"]["output"] == "P\ny\nt\nh\no\nn"
E["ex-letters"] = example("text = 'A1 b2'\nletters = 0\n\nfor character in text:\n    if character.isalpha():\n        letters = letters + 1\n\nprint('Letters:', letters)\n")
assert E["ex-letters"]["output"] == "Letters: 2"
E["cp8"] = {"type": "table", "xp": 1, "blanks": {
    "chars": {"accept": ["l, o, o, p", "l,o,o,p", "l o o p", "'l', 'o', 'o', 'p'", "'l','o','o','p'", "l o o p ", "loop", "l; o; o; p"],
              "placeholder": "values", "width": "9rem", "show": "l, o, o, p"},
    "empty": num(0)}}
E["cp8-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why is direct looping safer?", "answer": b64(
    "Direct looping visits only characters that exist, so it cannot use an index outside the string.")}

# ============================================================ 9. Looping over indexes
E["ex-index"] = example("text = 'code'\n\nfor position in range(len(text)):\n    print(position, text[position])\n")
assert E["ex-index"]["output"] == "0 c\n1 o\n2 d\n3 e"
DIRECT = {"accept": ["direct", "directly", "direct looping", "direct loop", "by character", "character"], "placeholder": "direct / by index", "width": "9rem", "show": "direct"}
BY_INDEX = {"accept": ["by index", "index", "by indexes", "by position", "index looping", "indexes", "range(len(text))"], "placeholder": "direct / by index", "width": "9rem", "show": "by index"}
E["cp9"] = {"type": "table", "xp": 1, "blanks": {
    "idx": seq(0, 1, 2, 3, 4, width="10rem"), "last": num(4),
    "vowels": dict(DIRECT), "beside": dict(BY_INDEX)}}
assert list(range(len("loops"))) == [0, 1, 2, 3, 4]

# ============================================================ 10. Building a string
E["ex-upper"] = example("word = 'Python'\nresult = ''\n\nfor character in word:\n    result = result + character.upper()\n\nprint(result)\n")
assert E["ex-upper"]["output"] == "PYTHON"
E["ex-compact"] = example("text = 'a b c'\ncompact = ''\n\nfor character in text:\n    if character != ' ':\n        compact = compact + character\n\nprint(compact)\n")
assert E["ex-compact"]["output"] == "abc"
def text(value, width="6rem"):
    return {"accept": [f"'{value}'", f'"{value}"', value], "caseSensitive": True, "placeholder": "string", "width": width, "show": f"'{value}'"}
E["cp10"] = {"type": "table", "xp": 1, "blanks": {"g_after": text("G"), "o_before": text("G"), "o_after": text("GO")}}
result = ""
trace = []
for character in "go":
    before = result
    result = result + character.upper()
    trace.append((before, result))
assert trace == [("", "G"), ("G", "GO")]
E["cp10-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 3, "placeholder": "Why must the initialization come first?", "answer": b64(
    "The accumulator must be initialized before the loop so the first pass has an existing string to add to and later passes do not erase earlier work.")}

# ============================================================ 11. Counting characters
E["ex-vowels"] = example("text = 'Programming is useful'.lower()\nvowels = 0\n\nfor character in text:\n    if character in 'aeiou':\n        vowels = vowels + 1\n\nprint(f'Vowels: {vowels}')\n")
assert E["ex-vowels"]["output"] == "Vowels: 7"
E["cp11"] = {"type": "table", "xp": 1, "blanks": {
    "i_in": yes_no(True), "i_n": num(1),
    "d_in": yes_no(False), "d_n": num(1),
    "e_in": yes_no(True), "e_n": num(2),
    "a_in": yes_no(True), "a_n": num(3),
    "init": {"accept": ["vowels = 0", "vowels=0"], "caseSensitive": True, "placeholder": "statement", "width": "8rem", "show": "vowels = 0"}}}
vowels, counts = 0, []
for character in "idea":
    if character in "aeiou":
        vowels = vowels + 1
    counts.append(vowels)
assert counts == [1, 1, 2, 3]

# ============================================================ 12. Putting It All Together
label = ("label = input('Course label: ')\ncompact = ''\ndigits = 0\n\nfor character in label:\n    if character != ' ':\n        compact = compact + character.upper()\n"
         "    if character.isdigit():\n        digits = digits + 1\n\nprint('Code:', compact)\nprint('Digits:', digits)\n")
E["ex-label"] = example(label, output=False)
assert run_with_prompts(label, ["Comp 1001"]) == "Course label: Code: COMP1001\nDigits: 4"
assert run_with_prompts(label, [""]) == "Course label: Code: \nDigits: 0"
assert run_with_prompts(label, ["A 1"]) == "Course label: Code: A1\nDigits: 1"

# ============================================================ Review
E["fr1"] = {"type": "short", "xp": 2, "answer": b64("A `for` loop runs once for each item in a sequence.")}
E["fr2"] = {"type": "short", "xp": 2, "answer": b64("`range(5)` supplies 0, 1, 2, 3, 4.")}
E["fr3"] = {"type": "short", "xp": 2, "answer": b64("The stop is exclusive because it is not supplied.")}
E["fr4"] = {"type": "short", "xp": 2, "answer": b64("The three arguments give the first value, the excluded boundary, and the amount added each pass.")}
E["fr5"] = {"type": "short", "xp": 2, "answer": b64("Use `while` when the number of passes is not known before the loop.")}
E["fr6"] = {"type": "short", "xp": 2, "answer": b64("The loop variable receives each item from the sequence.")}
E["fr7"] = {"type": "short", "xp": 2, "answer": b64("Loop by index when the position is needed.")}
E["fr8"] = {"type": "short", "xp": 2, "answer": b64("Start a string accumulator with the empty string.")}

# ============================================================ Coding Practice
NO_WHILE = 'assert "while" not in __code__, "Use a for loop here, not a while loop."\n'
ONE_FOR = '''import re
assert len(re.findall(r"^\\s*for\\b", __code__, re.M)) == 1, "Use exactly one for loop."
'''

# A. Choose the Loop
E["pa"] = {"type": "table", "xp": 1, "blanks": {
    "seats": loop_kind("for"), "names": loop_kind("while"), "digits": loop_kind("for"), "interest": loop_kind("while")}}
E["pa-why"] = {"type": "short", "xp": 2, "minChars": 40, "rows": 4, "placeholder": "One reason per task…", "answer": b64(
    "Use `for` for the seat labels because the count is known. Use `while` for names because the sentinel decides when to stop. "
    "Use `for` for the student number because the loop visits every character. Use `while` for the balance because the number of passes depends on when the target is reached.")}

# B. Count the Iterations
E["pb"] = {"type": "table", "xp": 1, "blanks": {"r7": num(7), "r39": num(6), "r2132": num(6), "r81m2": num(4), "r44": num(0)}}
assert [len(range(7)), len(range(3, 9)), len(range(2, 13, 2)), len(range(8, 1, -2)), len(range(4, 4))] == [7, 6, 6, 4, 0]

# C. Choose the Bounds
E["pc"] = {"type": "table", "xp": 1, "blanks": {
    "b26": rng(2, [7]), "b016": rng(0, [17, 18, 19, 20], 4), "b91": rng(9, [0, -1], -2), "b60": rng(6, [-1], -1)}}
for stop in (17, 18, 19, 20):
    assert list(range(0, stop, 4)) == [0, 4, 8, 12, 16]
for stop in (0, -1):
    assert list(range(9, stop, -2)) == [9, 7, 5, 3, 1]
assert list(range(2, 7)) == [2, 3, 4, 5, 6] and list(range(6, -1, -1)) == [6, 5, 4, 3, 2, 1, 0]

# D. Number a Week
week = "for day in range(1, 8):\n    print('Day', day)\n"
E["pd"] = {"type": "code", "xp": 2, "minLines": 3, "starter": "# Print Day 1 through Day 7, one per line.\n",
    "cases": [{"name": "Day 1 through Day 7", "expected": run(week)}],
    "check": ONE_FOR + NO_WHILE + '''assert re.search(r"range\\(\\s*[^,()]+\\s*,\\s*[^,()]+\\s*\\)", __code__), "Use a two-argument range, such as range(start, stop)."
''',
    "answer": b64(week),
    "answerNote": "The stop value is 8 because 8 is excluded."}
assert E["pd"]["cases"][0]["expected"] == "Day 1\nDay 2\nDay 3\nDay 4\nDay 5\nDay 6\nDay 7"

# E. Celsius Review Table
celsius = "print('Celsius Fahrenheit')\nfor celsius in range(-10, 31, 10):\n    fahrenheit = celsius * 9 / 5 + 32\n    print(celsius, fahrenheit)\n"
E["pe"] = {"type": "code", "xp": 5, "minLines": 5, "starter": "# Print the heading, then one row per Celsius value.\n",
    "cases": [{"name": "-10 through 30", "expected": run(celsius)}],
    "check": ONE_FOR + NO_WHILE + '''assert re.search(r"range\\([^()]*,[^()]*,[^()]*\\)", __code__), "Use a three-argument range with a step of 10."
assert __stdout__.startswith("Celsius Fahrenheit"), "Print the heading Celsius Fahrenheit before the loop."
''',
    "answer": b64(celsius),
    "answerNote": "The range includes 30 by using an excluded stop of 31."}
assert E["pe"]["cases"][0]["expected"] == "Celsius Fahrenheit\n-10 14.0\n0 32.0\n10 50.0\n20 68.0\n30 86.0"

# F. Rewrite with while
evens_for = "total = 0\nfor number in range(2, 9, 2):\n    total = total + number\nprint(total)\n"
evens_while = "total = 0\nnumber = 2\nwhile number < 9:\n    total = total + number\n    number = number + 2\nprint(total)\n"
assert run(evens_for) == run(evens_while) == "20"
E["pf"] = {"type": "code", "xp": 5, "minLines": 7, "starter": evens_for,
    "cases": [{"name": "total of 2, 4, 6, 8", "expected": run(evens_while),
               "check": 'assert number == 10, "After the loop, number should have reached 10: the first value not below 9."'}],
    "check": '''import re
assert re.search(r"^\\s*while\\b", __code__, re.M), "Rewrite the loop with while."
assert not re.search(r"^\\s*for\\b", __code__, re.M), "Replace the for loop; the while loop does the counting."
assert "range(" not in __code__, "A while loop does not use range(); initialize number yourself and add 2 on each pass."
''',
    "answer": b64(evens_while),
    "answerNote": "The while version needs explicit initialization, a condition that excludes 9, and an update of 2."}

# G. Compare Accumulators
acc_while = "total = 0\nnumber = 1\nwhile number < 5:\n    total = total + number\n    number = number + 1\n"
acc_for = "total = 0\nfor number in range(1, 5):\n    total = total + number\n"
E["ex-acc-while"] = example(acc_while, output=False)
E["ex-acc-for"] = example(acc_for, output=False)
assert run(acc_while + "print(total)") == run(acc_for + "print(total)") == "10"
E["pg"] = {"type": "table", "xp": 1, "blanks": {
    "w1": num(1), "w2": num(3), "w3": num(6), "w4": num(10),
    "f1": num(1), "f2": num(3), "f3": num(6), "f4": num(10),
    "same": yes_no(True)}}

# H. Trace the Output
score = "score = 2\nfor bonus in range(1, 4):\n    score = score + bonus\n    print(score)\n"
E["ex-score"] = example(score, output=False)
assert run(score) == "3\n5\n8"
E["ph"] = {"type": "table", "xp": 1, "blanks": {"s1": num(3), "s2": num(5), "s3": num(8)}}

# I. Changing Value Trace
product = "number = 3\nfor factor in range(2, 5):\n    number = number * factor\n    print(number)\n"
E["ex-product"] = example(product, output=False)
assert run(product) == "6\n18\n72"
E["pi"] = {"type": "table", "xp": 1, "blanks": {
    "f1": num(2), "n1": num(6), "f2": num(3), "n2": num(18), "f3": num(4), "n3": num(72)}}

# J. One Character Per Line
room = "room = input('Room code: ')\nfor character in room:\n    print(character)\n"
E["pj"] = {"type": "code", "xp": 2, "minLines": 4, "starter": "room = input('Room code: ')\n# Print each character on its own line.\n",
    "cases": [case("Typed EN2043", ["EN2043"], room), case("Typed an empty string", [""], room), case("Typed A1", ["A1"], room)],
    "check": ONE_FOR + NO_WHILE + '''assert "range(" not in __code__, "Loop directly over the string: for character in room."
assert "[" not in __code__, "Loop directly over the string; no index is needed."
''',
    "answer": b64(room),
    "answerNote": "An empty string causes zero loop iterations."}
assert E["pj"]["cases"][0]["expected"] == "Room code: E\nN\n2\n0\n4\n3"

# K. Reverse a Word
reverse = "text = input('Word: ')\nreversed_text = ''\nfor character in text:\n    reversed_text = character + reversed_text\nprint(reversed_text)\n"
E["pk"] = {"type": "code", "xp": 5, "minLines": 6, "starter": "text = input('Word: ')\nreversed_text = ''\n# Add each character to the front of reversed_text.\n",
    "cases": [case("Typed loops", ["loops"], reverse), case("Typed an empty string", [""], reverse),
              case("Typed a", ["a"], reverse), case("Typed Python", ["Python"], reverse)],
    "check": ONE_FOR + NO_WHILE + '''assert "[::" not in __code__ and "reversed(" not in __code__, "Build the reversed copy with the loop, not with slicing or reversed()."
''',
    "answer": b64(reverse),
    "answerNote": "Adding the current character before the old accumulator reverses the order."}
assert E["pk"]["cases"][0]["expected"] == "Word: spool"

# L. Count Vowels
count_vowels = "word = input('Word: ')\nvowels = 0\nfor character in word:\n    if character.lower() in 'aeiou':\n        vowels = vowels + 1\nprint('Vowels:', vowels)\n"
E["pl"] = {"type": "code", "xp": 5, "minLines": 7, "starter": "word = input('Word: ')\nvowels = 0\n# Count the vowels, then print the total.\n",
    "cases": [case("Typed Idea", ["Idea"], count_vowels), case("Typed rhythm", ["rhythm"], count_vowels),
              case("Typed AEIOU", ["AEIOU"], count_vowels), case("Typed an empty string", [""], count_vowels),
              case("Typed Memorial", ["Memorial"], count_vowels)],
    "check": ONE_FOR + NO_WHILE + '''assert ".count(" not in __code__, "Count the vowels with the loop and an if, not with .count()."
''',
    "answer": b64(count_vowels),
    "answerNote": "Convert each character to lowercase for the membership test."}
assert E["pl"]["cases"][0]["expected"] == "Word: Vowels: 3" and E["pl"]["cases"][1]["expected"] == "Word: Vowels: 0"

# M. Currency Entries
currency = "RATE = 1.35\nusd = float(input('USD, or 0 to stop: '))\nwhile usd != 0:\n    cad = usd * RATE\n    print(f'CAD: {cad:.2f}')\n    usd = float(input('USD, or 0 to stop: '))\n"
E["pm"] = {"type": "code", "xp": 5, "minLines": 7, "starter": "RATE = 1.35\n# Read amounts with input('USD, or 0 to stop: ') until 0.\n",
    "cases": [case("Typed 10, 5, 0", ["10", "5", "0"], currency), case("Typed 0", ["0"], currency),
              case("Typed 2.5, 0", ["2.5", "0"], currency), case("Typed 100, 1, 0.5, 0", ["100", "1", "0.5", "0"], currency)],
    "check": '''import re
assert re.search(r"^\\s*while\\b", __code__, re.M), "Use a while loop; the number of entries is not known."
assert "1.35" in __code__, "Use the rate 1.35."
assert re.search(r":[^}]*\\.2f\\}", __source__), "Print each Canadian value with two decimal places using :.2f."
''',
    "answer": b64(currency),
    "answerNote": "The sentinel 0 stops the loop and is not converted."}
assert E["pm"]["cases"][0]["expected"].endswith("CAD: 13.50\nUSD, or 0 to stop: CAD: 6.75\nUSD, or 0 to stop: ")

# N. Hare and Lynx Populations
hares = ("years = int(input('Years: '))\nhares = 1000.0\nlynx = 20.0\nprint(0, f'{hares:.2f}', f'{lynx:.2f}')\n\n"
         "for year in range(1, years + 1):\n    new_hares = hares * (1 + 0.1 - 0.01 * lynx)\n    new_lynx = lynx * (1 - 0.01 + 0.00002 * hares)\n"
         "    hares = new_hares\n    lynx = new_lynx\n    print(year, f'{hares:.2f}', f'{lynx:.2f}')\n")
E["pn"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": "years = int(input('Years: '))\nhares = 1000.0\nlynx = 20.0\n# Print year 0, then one row per later year.\n",
    "cases": [case("Typed 0", ["0"], hares), case("Typed 2", ["2"], hares), case("Typed 1", ["1"], hares), case("Typed 5", ["5"], hares)],
    "check": ONE_FOR + NO_WHILE + '''assert "range(" in __code__, "Count the years with range(1, years + 1)."
assert re.search(r":[^}]*\\.2f\\}", __source__), "Show both populations with two decimal places using :.2f."
assert re.search(r"0\\.00002\\s*\\*\\s*hares|hares\\s*\\*\\s*0\\.00002", __code__), "Compute the lynx with lynx * (1 - 0.01 + 0.00002 * hares)."
''',
    "answer": b64(hares),
    "answerNote": "The temporary values prevent the new hare population from changing the lynx calculation for the same year."}
assert E["pn"]["cases"][0]["expected"] == "Years: 0 1000.00 20.00"
assert E["pn"]["cases"][1]["expected"] == "Years: 0 1000.00 20.00\n1 900.00 20.20\n2 808.20 20.36"

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-14",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 14 Workbook",
    "subtitle": "The for loop and ranges",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-14/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
