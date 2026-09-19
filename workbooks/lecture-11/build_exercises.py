"""Build workbooks/lecture-11/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-11/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-11
"""
import base64, itertools, json, subprocess, sys, pathlib

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

TF = {"accept": ["True"], "show": "True"}, {"accept": ["False"], "show": "False"}
def tf(value):
    return dict(TF[0] if value else TF[1])

def quoted(text):
    return [f"'{text}'", f'"{text}"']

E = {}

# ============================================================ 1. Boolean Values and Operators
E["ex-e01"] = example("age = 20\nis_adult = age >= 18\n\nprint(is_adult)\nprint(type(is_adult))\n")
E["ex-e02"] = example("has_ticket = True\n\nif has_ticket:\n    print('Entry allowed')\n")
E["cp1"] = {"type": "table", "xp": 1, "blanks": {
    "paid": {"accept": ["has_paid", "is_paid", "was_paid", "payment_received", "has_payment", "is_payment_received", "payment_was_received", "has_received_payment"], "caseSensitive": True, "placeholder": "name", "width": "14rem"},
    "valid": {"accept": ["is_valid", "is_score_valid", "score_is_valid", "has_valid_score", "is_valid_score"], "caseSensitive": True, "placeholder": "name", "width": "14rem"},
    "ready": {"accept": ["if is_ready:", "if is_ready", "is_ready"], "caseSensitive": True, "placeholder": "if …:", "width": "14rem"}}}

E["ex-e03"] = example("age = 20\nhas_id = True\n\ncan_enter = age >= 18 and has_id\nprint(can_enter)\n")
E["cp2"] = {"type": "table", "xp": 1, "blanks": {
    "expr": {"accept": ["signed_in and is_available", "is_available and signed_in"], "caseSensitive": True, "placeholder": "expression", "width": "18rem"},
    "value": tf(False)}}

E["ex-e04"] = example("day = 'Saturday'\nis_weekend = day == 'Saturday' or day == 'Sunday'\n\nprint(is_weekend)\n")
yY = [f"choice == {a} or choice == {b}" for a, b in [("'y'", "'Y'"), ("'Y'", "'y'"), ('"y"', '"Y"'), ('"Y"', '"y"')]]
E["cp3"] = {"type": "table", "xp": 1, "blanks": {
    "cond": {"accept": yY + [c.replace("choice", "(choice", 1).replace(" or ", ") or (") + ")" for c in yY], "caseSensitive": True, "placeholder": "condition", "width": "20rem"},
    "both": tf(True)}}

E["ex-e05"] = example("is_closed = False\n\nif not is_closed:\n    print('The service is open')\n")
E["cp4"] = {"type": "table", "xp": 1, "blanks": {
    "nt": tf(False), "nf": tf(True),
    "rewrite": {"accept": ["not is_valid", "(not is_valid)"], "caseSensitive": True, "placeholder": "expression", "width": "12rem"}}}

E["cp5-table"] = {"type": "table", "xp": 1, "blanks": {
    "r1and": tf(False), "r1or": tf(True), "r2and": tf(False), "r2or": tf(False)}}
E["cp5-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Python's `or` also produces `True` when both inputs are `True`; it means \"at least one.\"")}

E["ex-e06"] = example("a = True\nb = False\nc = False\n\nprint(a or b and c)\nprint((a or b) and c)\n")
E["cp6-group"] = {"type": "table", "xp": 1, "blanks": {
    "g": {"accept": ["(not a) or (b and c)", "not a or (b and c)", "((not a) or (b and c))"], "caseSensitive": True, "placeholder": "with parentheses", "width": "16rem"}}}
E["cp6-why"] = {"type": "short", "xp": 2, "answer": b64(
    "No. The two expressions are not always equal. For example, when `a` is `True` and `c` is `False`, `a or (b and c)` is `True` and `(a or b) and c` is `False`.")}

# ============================================================ 2. Readable and Safe Conditions
E["ex-e07"] = example("count = 0\ntotal = 100\n\nhas_large_average = count > 0 and total / count > 50\nprint(has_large_average)\n")
E["cp7-first"] = {"type": "table", "xp": 1, "blanks": {
    "first": {"accept": ["count > 0", "(count > 0)", "the left side", "left side", "the left part", "left part", "the first part"], "caseSensitive": False, "placeholder": "which part?", "width": "12rem"}}}
E["cp7-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Python skips `total / count > 50` because `count > 0` is `False`, so the whole `and` expression is already known to be `False`. Reversing the parts would attempt the division by zero before reaching the guard.")}

E["ex-e08"] = example("is_adult = True\nhas_id = False\n\nfirst = not (is_adult and has_id)\nsecond = (not is_adult) or (not has_id)\n\nprint(first)\nprint(second)\n")
E["cp8"] = {"type": "table", "xp": 1, "blanks": {
    "m1": {"accept": ["(not is_member) and (not has_pass)", "not is_member and not has_pass", "(not has_pass) and (not is_member)", "not has_pass and not is_member"], "caseSensitive": True, "placeholder": "rewritten expression", "width": "20rem"},
    "m2": {"accept": ["(not is_open) or (not is_staffed)", "not is_open or not is_staffed", "(not is_staffed) or (not is_open)", "not is_staffed or not is_open"], "caseSensitive": True, "placeholder": "rewritten expression", "width": "20rem"}}}
E["cp8-op"] = {"type": "short", "xp": 1, "minChars": 8, "rows": 2, "placeholder": "What happens to the operator?", "answer": b64(
    "The operator changes from `or` to `and`, or from `and` to `or`.")}

E["ex-e09"] = example("score = 84\nis_valid = 0 <= score <= 100\n\nprint(is_valid)\n")
E["cp9"] = {"type": "table", "xp": 1, "blanks": {
    "v": {"accept": ["1 <= value <= 10", "10 >= value >= 1"], "caseSensitive": True, "placeholder": "chained comparison", "width": "14rem"},
    "t": {"accept": ["0 < temperature < 100", "100 > temperature > 0"], "caseSensitive": True, "placeholder": "chained comparison", "width": "14rem"}}}

# ============================================================ 3. String Tests and Input Validation
E["ex-e10"] = example("code = 'COMP1001'\n\nprint(code.isalpha())\nprint(code.startswith('COMP'))\nprint(code.endswith('1001'))\n")
E["cp10"] = {"type": "table", "xp": 1, "blanks": {"a": tf(True), "b": tf(False), "c": tf(True), "d": tf(False)}}
assert (run("print('42'.isdigit(), '-5'.isdigit(), 'StJohns'.isalpha(), 'report.txt'.endswith('.pdf'))")) == "True False True False"
E["cp10-why"] = {"type": "short", "xp": 1, "minChars": 10, "rows": 2, "answer": b64(
    "The minus sign is a character, but it is not a digit.")}

e11 = ("raw = input('Enter your age: ').strip()\n\n"
       "if not raw.isdigit():\n    print('Please enter a whole number.')\n"
       "elif int(raw) > 130:\n    print('That age is outside the expected range.')\n"
       "else:\n    age = int(raw)\n    print(f'Age recorded: {age}')\n")
E["ex-e11"] = example(e11, output=False)
assert run(e11, ["twenty"]) == "Enter your age: Please enter a whole number."
assert run(e11, ["24"]) == "Enter your age: Age recorded: 24"
E["cp11-order"] = {"type": "table", "xp": 1, "blanks": {
    "convert": {"accept": ["3"], "placeholder": "#", "width": "4rem"},
    "read": {"accept": ["1"], "placeholder": "#", "width": "4rem"},
    "test": {"accept": ["2"], "placeholder": "#", "width": "4rem"}}}
E["cp11-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The test prevents `int()` from receiving text that would cause a `ValueError`. Converting first would defeat the check because bad text would already have caused the error.")}

e12 = ("choice = input('Choose small or large: ').strip().lower()\n\n"
       "if choice == 'small' or choice == 'large':\n    print('Choice recorded:', choice)\n"
       "else:\n    print('Please enter small or large.')\n")
E["ex-e12"] = example(e12, output=False)
assert run(e12, ["LARGE"]) == "Choose small or large: Choice recorded: large"
E["ex-e13"] = example("score = 108\nis_valid = 0 <= score <= 100\n\nif is_valid:\n    print('Score recorded')\nelse:\n    print('Score must be from 0 to 100.')\n")
colours = []
for order in itertools.permutations(["red", "green", "blue"]):
    for q in ("'", '"'):
        colours.append(" or ".join(f"colour == {q}{c}{q}" for c in order))
E["cp12"] = {"type": "table", "xp": 1, "blanks": {
    "colour": {"accept": colours, "caseSensitive": True, "placeholder": "condition", "width": "26rem"},
    "rating": {"accept": ["1 <= rating <= 5", "5 >= rating >= 1"], "caseSensitive": True, "placeholder": "chained comparison", "width": "14rem"}}}
E["cp12-where"] = {"type": "short", "xp": 1, "minChars": 10, "rows": 2, "answer": b64(
    "Immediately after reading and cleaning the input, so that later code can rely on the value having passed the checks.")}

# ============================================================ Final Review
E["fr1"] = {"type": "table", "xp": 1, "blanks": {"vals": {
    "accept": ["True and False", "True, False", "True False", "False and True", "False, True", "False True", "True/False", "True or False", "False or True"],
    "caseSensitive": True, "placeholder": "the two values", "width": "12rem"}}}
E["fr2"] = {"type": "short", "xp": 2, "answer": b64(
    "`A and B` is true only when both parts are true. `A or B` is true when at least one part is true, including when both parts are true.")}
E["fr3"] = {"type": "table", "xp": 1, "blanks": {"order": {
    "accept": ["not, and, or", "not and or", "not, then and, then or", "not then and then or", "not > and > or", "not; and; or", "not / and / or", "not → and → or", "not, and, then or", "not first, then and, then or"],
    "placeholder": "first, second, third", "width": "16rem", "show": "not, and, or"}}}
E["fr4"] = {"type": "short", "xp": 2, "answer": b64(
    "Python evaluates from left to right. If the left part is false, the whole `and` expression must be false, so Python skips the right part.")}
E["fr5"] = {"type": "table", "xp": 1, "blanks": {"eq": {
    "accept": ["(not A) and (not B)", "not A and not B", "(not B) and (not A)", "not B and not A"], "caseSensitive": True, "placeholder": "equivalent expression", "width": "16rem"}}}
E["fr6"] = {"type": "table", "xp": 1, "blanks": {"chain": {
    "accept": ["0 <= x <= 100", "100 >= x >= 0"], "caseSensitive": True, "placeholder": "chained comparison", "width": "12rem"}}}
E["fr7"] = {"type": "short", "xp": 2, "answer": b64(
    "Bad data is rejected where it enters. Code after the check can then rely on the value being usable.")}
E["fr8"] = {"type": "short", "xp": 2, "answer": b64(
    "The variable already contains a Boolean value. The direct form states the condition without a redundant comparison.")}

# ============================================================ Additional Practice
E["pa"] = {"type": "table", "xp": 1, "blanks": {
    "r1and": tf(True), "r1or": tf(True), "r2and": tf(False), "r2or": tf(True),
    "r3and": tf(False), "r3or": tf(True), "r4and": tf(False), "r4or": tf(False)}}
assert run("a=True;b=False;c=True\nprint(a and b, a or b, not b, a and b or c, a and (b or c))") == "False True True True True"
E["pb"] = {"type": "table", "xp": 1, "blanks": {"e1": tf(False), "e2": tf(True), "e3": tf(True), "e4": tf(True), "e5": tf(True)}}
E["pc"] = {"type": "table", "xp": 1, "blanks": {
    "paid": {"accept": ["if has_paid:", "if has_paid"], "caseSensitive": True, "placeholder": "if …:", "width": "14rem"},
    "empty": {"accept": ["if not is_empty:", "if not is_empty"], "caseSensitive": True, "placeholder": "if …:", "width": "14rem"},
    "name": {"accept": ["was_found", "is_file_found", "is_found", "file_found", "file_was_found", "has_file", "has_found_file", "found_file", "is_file_present", "file_exists", "was_file_found"], "caseSensitive": True, "placeholder": "name", "width": "14rem"}}}
E["pd-cond"] = {"type": "table", "xp": 1, "blanks": {"cond": {
    "accept": ["count > 0 and total / count > 10", "count > 0 and total/count > 10", "count >= 1 and total / count > 10", "count >= 1 and total/count > 10",
               "(count > 0) and (total / count > 10)", "(count > 0) and (total/count > 10)"],
    "caseSensitive": True, "placeholder": "condition", "width": "22rem"}}}
E["pd-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Use `count > 0 and total / count > 10`. When `count` is zero, the false left side causes Python to skip the unsafe division.")}
E["pe"] = {"type": "table", "xp": 1, "blanks": {
    "m1": {"accept": ["(not is_member) or (not has_paid)", "not is_member or not has_paid", "(not has_paid) or (not is_member)", "not has_paid or not is_member"], "caseSensitive": True, "placeholder": "rewritten expression", "width": "20rem"},
    "m2": {"accept": ["(not is_weekend) and (not is_holiday)", "not is_weekend and not is_holiday", "(not is_holiday) and (not is_weekend)", "not is_holiday and not is_weekend"], "caseSensitive": True, "placeholder": "rewritten expression", "width": "20rem"}}}
assert run("print('1001'.isdigit(), '10.5'.isdigit(), 'Python'.isalpha(), 'COMP1001'.startswith('COMP'), 'photo.png'.endswith('.jpg'))") == "True False True True False"
E["pf"] = {"type": "table", "xp": 1, "blanks": {"s1": tf(True), "s2": tf(False), "s3": tf(True), "s4": tf(True), "s5": tf(False)}}

pg = ("raw = input('Quantity: ').strip()\n\n"
      "if not raw.isdigit():\n    print('Enter a whole number.')\n"
      "elif not 1 <= int(raw) <= 20:\n    print('Quantity must be from 1 to 20.')\n"
      "else:\n    quantity = int(raw)\n    print('Quantity recorded:', quantity)\n")
pg_starter = ("raw = input('Quantity: ')____________________\n\n"
              "if _________________________________________:\n    print('Enter a whole number.')\n"
              "elif _______________________________________:\n    print('Quantity must be from 1 to 20.')\n"
              "else:\n    quantity = ______________________________\n    print('Quantity recorded:', quantity)\n")
E["pg"] = {"type": "code", "xp": 5, "minLines": 9, "starter": pg_starter,
    "cases": [case("'five' (nonnumeric text)", ["five"], pg),
              case("'0' (below range)", ["0"], pg),
              case("'1' (lower boundary)", ["1"], pg),
              case("'20' (upper boundary)", ["20"], pg),
              case("'21' (above range)", ["21"], pg),
              case("' 8 ' (surrounding spaces)", [" 8 "], pg)],
    "check": "assert isinstance(globals().get('quantity', 0), int), 'quantity should hold the converted int, not the text.'",
    "answer": b64(pg)}
whole = ["whole-number error", "whole number error", "Enter a whole number.", "Enter a whole number", "error: whole number", "whole-number message", "whole number message"]
rng = ["range error", "Quantity must be from 1 to 20.", "Quantity must be from 1 to 20", "range message", "out of range", "error: range"]
def rec(n):
    return {"accept": [f"record {n}", f"Quantity recorded: {n}", f"recorded {n}", f"records {n}", f"accepted {n}", f"accept {n}", f"quantity recorded {n}", f"Quantity recorded: {n}."], "placeholder": "result", "width": "14rem", "show": f"record {n}"}
E["ph"] = {"type": "table", "xp": 1, "blanks": {
    "five": {"accept": whole, "placeholder": "result", "width": "14rem"},
    "zero": {"accept": rng, "placeholder": "result", "width": "14rem"},
    "one": rec(1), "twenty": rec(20),
    "twentyone": {"accept": rng, "placeholder": "result", "width": "14rem"},
    "spaced": rec(8)}}

# ============================================================ Putting It All Together
E["ex-e14"] = example("course = input('Course code: ').strip().upper()\nraw_seats = input('Number of seats: ').strip()\n", output=False)
syn = ("course = input('Course code: ').strip().upper()\nraw_seats = input('Number of seats: ').strip()\n\n"
       "is_comp_course = course.startswith('COMP')\nhas_whole_seats = raw_seats.isdigit()\n\n"
       "if not is_comp_course or not has_whole_seats:\n    print('Enter a COMP course and a whole seat count.')\n"
       "else:\n    seats = int(raw_seats)\n    is_valid_count = 1 <= seats <= 40\n"
       "    if is_valid_count:\n        print('Request recorded')\n    else:\n        print('Seats must be from 1 to 40.')\n")
syn_starter = syn.replace("seats = int(raw_seats)", "seats = _________________________________").replace("is_valid_count = 1 <= seats <= 40", "is_valid_count = ________________________")
E["syn"] = {"type": "code", "xp": 5, "minLines": 15, "starter": syn_starter,
    "cases": [case("COMP1001, 24", ["COMP1001", "24"], syn),
              case("COMP1001, 0", ["COMP1001", "0"], syn),
              case("comp2001, 40", ["comp2001", "40"], syn),
              case("COMP1001, 41", ["COMP1001", "41"], syn),
              case("MATH1000, many", ["MATH1000", "many"], syn)],
    "check": "assert isinstance(globals().get('is_valid_count', True), bool), 'is_valid_count should hold a Boolean value from a comparison.'",
    "answer": b64(syn)}
E["syn-msg"] = {"type": "table", "xp": 1, "blanks": {"msg": {
    "accept": ["Seats must be from 1 to 40.", "Seats must be from 1 to 40"], "caseSensitive": True, "placeholder": "the printed message", "width": "18rem"}}}
e15 = syn.replace("print('Request recorded')", "print('Request recorded:', course, seats)")
E["ex-e15"] = example(e15, output=False)
assert run(e15, ["comp1001", "24"]).endswith("Request recorded: COMP1001 24")
assert run(e15, ["MATH1000", "many"]).endswith("Enter a COMP course and a whole seat count.")

# ============================================================ Coding Practice
def tv(v):
    return {"accept": ["T", "True"] if v else ["F", "False"], "show": "T" if v else "F", "width": "4rem"}
rows = list(itertools.product([False, True], repeat=3))
E["cx1"] = {"type": "table", "xp": 1, "blanks": {}}
for i, (p, q, r) in enumerate(rows, 1):
    E["cx1"]["blanks"][f"a{i}"] = tv((p and q) or not r)
    E["cx1"]["blanks"][f"b{i}"] = tv(not (p and (q or not r)))
assert [E["cx1"]["blanks"][f"a{i}"]["show"] for i in range(1, 9)] == list("TFTFTFTT")
assert [E["cx1"]["blanks"][f"b{i}"]["show"] for i in range(1, 9)] == list("TTTTFTFF")

E["cx2-table"] = {"type": "table", "xp": 1, "blanks": {
    "ab1": tv(True), "ba1": tv(True), "ab2": tv(False), "ba2": tv(False), "ab3": tv(False), "ba3": tv(False), "ab4": tv(False), "ba4": tv(False)}}
E["cx2-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Yes. Both expressions are true only in the row where both inputs are true. In the other three rows, both expressions are false. This property is called commutativity, but the truth table is enough to establish it here.")}

E["cx3"] = {"type": "table", "xp": 1, "blanks": {
    "and": {"accept": ["has_cats and has_dogs", "has_dogs and has_cats"], "caseSensitive": True, "placeholder": "expression", "width": "18rem"},
    "or": {"accept": ["has_cats or has_dogs", "has_dogs or has_cats"], "caseSensitive": True, "placeholder": "expression", "width": "18rem"},
    "not": {"accept": ["has_cats and not has_dogs", "has_cats and (not has_dogs)", "not has_dogs and has_cats", "(not has_dogs) and has_cats"], "caseSensitive": True, "placeholder": "expression", "width": "18rem"}}}

cx4_exprs = ["b and x == 0", "b or x == 0", "not b and x == 0", "not b or x == 0", "b and x != 0", "b or x != 0", "not b and x != 0", "not b or x != 0"]
cx4_vals = run("b = False\nx = 0\n" + "\n".join(f"print({e})" for e in cx4_exprs)).split("\n")
assert cx4_vals == ["False", "True", "True", "True", "False", "False", "False", "True"]
E["cx4"] = {"type": "table", "xp": 1, "blanks": {f"v{i}": tf(v == "True") for i, v in enumerate(cx4_vals, 1)}}

E["cx5"] = {"type": "table", "xp": 1, "blanks": {
    "s1": {"accept": ["is_ready"], "caseSensitive": True, "placeholder": "expression", "width": "12rem"},
    "s2": {"accept": ["not is_ready"], "caseSensitive": True, "placeholder": "expression", "width": "12rem"},
    "s3": {"accept": ["not is_ready"], "caseSensitive": True, "placeholder": "expression", "width": "12rem"},
    "s4": {"accept": ["is_ready"], "caseSensitive": True, "placeholder": "expression", "width": "12rem"}}}

cx6b = ["count != 0 and count <= 30", "count <= 30 and count != 0", "not count == 0 and count <= 30", "count != 0 and count <= 30"]
E["cx6"] = {"type": "table", "xp": 2, "blanks": {
    "a": {"accept": ["is_valid = score >= 50", "score >= 50"], "caseSensitive": True, "placeholder": "is_valid = …", "width": "22rem"},
    "b": {"accept": [f"is_valid = {e}" for e in cx6b] + cx6b, "caseSensitive": True, "placeholder": "is_valid = …", "width": "22rem"}}}

cx7_broken = ("raw = input('Number of tickets: ').strip()\ntickets = int(raw)\n\n"
              "if raw.isdigit() and 1 <= tickets <= 8:\n    print('Accepted')\nelse:\n    print('Enter a whole number from 1 to 8.')\n")
cx7 = ("raw = input('Number of tickets: ').strip()\n\n"
       "if not raw.isdigit():\n    print('Enter a whole number from 1 to 8.')\n"
       "else:\n    tickets = int(raw)\n    if 1 <= tickets <= 8:\n        print('Accepted')\n    else:\n        print('Enter a whole number from 1 to 8.')\n")
E["cx7-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The conversion happens before the digit test. Non-digit text causes a `ValueError`, so the validation message never appears. Test the text first and convert only on the safe path.")}
E["cx7"] = {"type": "code", "xp": 5, "minLines": 8, "starter": cx7_broken,
    "cases": [case("'five' (must not crash)", ["five"], cx7), case("'3'", ["3"], cx7), case("'9'", ["9"], cx7), case("'0'", ["0"], cx7), case("' 8 '", [" 8 "], cx7)],
    "answer": b64(cx7)}

cx8 = ("mode = input('Mode: ').strip().lower()\na = int(input('First: '))\nb = int(input('Second: '))\nc = int(input('Third: '))\n\n"
       "if mode != 'strict' and mode != 'lenient':\n    print('Mode must be strict or lenient.')\n"
       "else:\n    if mode == 'strict':\n        increasing = a < b < c\n        decreasing = a > b > c\n"
       "    else:\n        increasing = a <= b <= c\n        decreasing = a >= b >= c\n\n"
       "    if increasing and decreasing:\n        print('both')\n    elif increasing:\n        print('increasing')\n"
       "    elif decreasing:\n        print('decreasing')\n    else:\n        print('neither')\n")
cx8_starter = "mode = input('Mode: ').strip().lower()\na = int(input('First: '))\nb = int(input('Second: '))\nc = int(input('Third: '))\n\n# Define increasing and decreasing, then print one result.\n"
mode_check = ("import re\n"
              "words = re.findall(r'\\b(increasing|decreasing|both|neither)\\b', __stdout__)\n"
              "assert not words, 'The mode \"fast\" is not strict or lenient. Reject it instead of printing a result.'\n"
              "assert __stdout__.strip().split('Third: ')[-1].strip(), 'Print a message that explains the mode must be strict or lenient.'")
E["cx8"] = {"type": "code", "xp": 10, "minLines": 12, "starter": cx8_starter,
    "cases": [case("strict, 3, 4, 4", ["strict", "3", "4", "4"], cx8),
              case("lenient, 4, 4, 4", ["lenient", "4", "4", "4"], cx8),
              case("strict, 1, 2, 3", ["strict", "1", "2", "3"], cx8),
              case("lenient, 5, 3, 3", ["lenient", "5", "3", "3"], cx8),
              case("STRICT, 9, 6, 2", ["STRICT", "9", "6", "2"], cx8),
              case("lenient, 2, 9, 1", ["lenient", "2", "9", "1"], cx8),
              case("fast, 1, 2, 3 (reject the mode)", ["fast", "1", "2", "3"], check=mode_check)],
    "answer": b64(cx8)}

cx9 = ("a = int(input('First: '))\nb = int(input('Second: '))\nc = int(input('Third: '))\n\n"
       "is_in_order = a <= b <= c or a >= b >= c\n\nif is_in_order:\n    print('in order')\nelse:\n    print('not in order')\n")
cx9_starter = "a = int(input('First: '))\nb = int(input('Second: '))\nc = int(input('Third: '))\n\nis_in_order = __________________________________________\n"
E["cx9"] = {"type": "code", "xp": 5, "minLines": 8, "starter": cx9_starter,
    "cases": [case("1, 2, 2", ["1", "2", "2"], cx9), case("1, 5, 2", ["1", "5", "2"], cx9), case("9, 4, 4", ["9", "4", "4"], cx9), case("3, 3, 3", ["3", "3", "3"], cx9), case("2, 1, 5", ["2", "1", "5"], cx9)],
    "check": "assert isinstance(globals().get('is_in_order'), bool), 'Keep the Boolean result in is_in_order, then test that variable.'",
    "answer": b64(cx9)}

cx10 = ("a = int(input('A: '))\nb = int(input('B: '))\nc = int(input('C: '))\nd = int(input('D: '))\n\n"
        "has_two_pairs = ((a == b and c == d)\n                 or (a == c and b == d)\n                 or (a == d and b == c))\n\n"
        "if has_two_pairs:\n    print('two pairs')\nelse:\n    print('not two pairs')\n")
cx10_starter = "a = int(input('A: '))\nb = int(input('B: '))\nc = int(input('C: '))\nd = int(input('D: '))\n\n# Test the three possible pairings.\n"
E["cx10"] = {"type": "code", "xp": 5, "minLines": 9,  "starter": cx10_starter,
    "cases": [case("1, 2, 2, 1", ["1", "2", "2", "1"], cx10), case("1, 2, 2, 3", ["1", "2", "2", "3"], cx10), case("2, 2, 2, 2", ["2", "2", "2", "2"], cx10),
              case("7, 7, 3, 3", ["7", "7", "3", "3"], cx10), case("5, 1, 5, 1", ["5", "1", "5", "1"], cx10), case("4, 4, 4, 9", ["4", "4", "4", "9"], cx10)],
    "answer": b64(cx10)}

cx11 = ("text = input('Text: ')\n\nprint('letters only:', text.isalpha())\nprint('uppercase:', text.isupper())\nprint('lowercase:', text.islower())\n"
        "print('digits only:', text.isdigit())\nprint('begins COMP:', text.startswith('COMP'))\nprint('ends period:', text.endswith('.'))\n")
def report_check(text):
    want = run("t = " + repr(text) + "\nprint(t.isalpha(), t.isupper(), t.islower(), t.isdigit(), t.startswith('COMP'), t.endswith('.'))").split()
    return ("import re\n"
            "found = re.findall(r'\\b(True|False)\\b', __stdout__)\n"
            f"assert len(found) == 6, 'Print exactly six Boolean results, one per property, in the listed order (found ' + str(len(found)) + ').'\n"
            f"assert found == {want!r}, 'For ' + {text!r} + ' the six results in order should be {', '.join(want)}; you printed ' + ', '.join(found) + '.'\n"
            "lines = [line for line in __stdout__.split('\\n') if line.strip()]\n"
            "assert all(re.search(r'[A-Za-z]', line.split('True')[0].split('False')[0].replace('Text:', '')) for line in lines), 'Label each result so a reader knows which property it reports.'")
E["cx11"] = {"type": "code", "xp": 5, "minLines": 8, "starter": "text = input('Text: ')\n\n# Print one labelled Boolean result for each property.\n",
    "cases": [case("COMP1001", ["COMP1001"], check=report_check("COMP1001")),
              case("notes.", ["notes."], check=report_check("notes.")),
              case("Memorial", ["Memorial"], check=report_check("Memorial")),
              case("2026", ["2026"], check=report_check("2026")),
              case("COMPUTER", ["COMPUTER"], check=report_check("COMPUTER"))],
    "answer": b64(cx11), "answerNote": "Any clear labels are fine; Check looks at the six True/False values in order."}
assert run(cx11, ["COMP1001"]).endswith("letters only: False\nuppercase: True\nlowercase: False\ndigits only: False\nbegins COMP: True\nends period: False")

cx12 = ("from_unit = input('From unit: ').strip().lower()\nto_unit = input('To unit: ').strip().lower()\nvalue = float(input('Value: '))\n\n"
        "from_is_length = from_unit == 'cm' or from_unit == 'in'\nto_is_length = to_unit == 'cm' or to_unit == 'in'\n"
        "is_length_pair = from_is_length and to_is_length\nis_mass_pair = from_unit == 'kg' and to_unit == 'kg'\n\n"
        "if not (is_length_pair or is_mass_pair):\n    print('Unknown or incompatible units.')\n"
        "elif from_unit == to_unit:\n    print(f'{value:.2f} {to_unit}')\n"
        "elif from_unit == 'cm':\n    print(f'{value / 2.54:.2f} in')\nelse:\n    print(f'{value * 2.54:.2f} cm')\n")
cx12_starter = "from_unit = input('From unit: ').strip().lower()\nto_unit = input('To unit: ').strip().lower()\nvalue = float(input('Value: '))\n\n# Name the compatibility tests, then convert on the safe path.\n"
reject_check = ("import re\n"
                "tail = __stdout__.split('Value: ')[-1]\n"
                "assert not re.search(r'\\d+\\.\\d+ (cm|in|kg)', tail), 'These units are not compatible. Print an error message instead of a converted value.'\n"
                "assert tail.strip(), 'Print an error message for an unknown or incompatible pair.'")
E["cx12"] = {"type": "code", "xp": 10, "minLines": 14, "starter": cx12_starter,
    "cases": [case("cm, in, 25.4", ["cm", "in", "25.4"], cx12), case("in, cm, 10", ["in", "cm", "10"], cx12),
              case("kg, kg, 3", ["kg", "kg", "3"], cx12), case("CM, cm, 12.5", ["CM", "cm", "12.5"], cx12),
              case("kg, cm, 3 (incompatible)", ["kg", "cm", "3"], check=reject_check),
              case("m, cm, 1 (unknown unit)", ["m", "cm", "1"], check=reject_check)],
    "answer": b64(cx12), "answerNote": "The wording of the error message is yours to choose."}

cx13 = ("balance = float(input('Starting balance: $'))\naction = input('Action: ').strip().lower()\namount = float(input('Amount: $'))\n\n"
        "is_known_action = action == 'deposit' or action == 'withdraw'\nhas_valid_amounts = balance >= 0 and amount >= 0\n"
        "can_afford = action != 'withdraw' or amount <= balance\n\n"
        "if not is_known_action or not has_valid_amounts:\n    print('Enter a valid balance, action, and amount.')\n"
        "elif not can_afford:\n    print('Insufficient funds.')\n"
        "else:\n    if action == 'deposit':\n        balance = balance + amount\n    else:\n        balance = balance - amount\n    print(f'Balance: ${balance:.2f}')\n")
cx13_starter = "balance = float(input('Starting balance: $'))\naction = input('Action: ').strip().lower()\namount = float(input('Amount: $'))\n\n# Name the validity conditions before changing the balance.\n"
no_balance = ("tail = __stdout__.split('Amount: $')[-1]\n"
              "assert 'Balance:' not in tail, 'This transaction must be rejected. Do not print a new balance.'\n"
              "assert tail.strip(), 'Print a message that explains why the transaction was rejected.'")
insufficient = no_balance + "\nassert 'insufficient' in tail.lower(), 'A withdrawal larger than the balance should print an insufficient-funds message.'"
E["cx13"] = {"type": "code", "xp": 10, "minLines": 15, "starter": cx13_starter,
    "cases": [case("100, deposit, 25", ["100", "deposit", "25"], cx13), case("100, withdraw, 40", ["100", "withdraw", "40"], cx13),
              case("50, Withdraw, 50", ["50", "Withdraw", "50"], cx13), case("0, deposit, 12.5", ["0", "deposit", "12.5"], cx13),
              case("100, withdraw, 120 (insufficient funds)", ["100", "withdraw", "120"], check=insufficient),
              case("-5, deposit, 10 (negative balance)", ["-5", "deposit", "10"], check=no_balance),
              case("100, transfer, 10 (unknown action)", ["100", "transfer", "10"], check=no_balance),
              case("100, deposit, -3 (negative amount)", ["100", "deposit", "-3"], check=no_balance)],
    "answer": b64(cx13), "answerNote": "Rejection messages are yours to word; the insufficient-funds case must mention insufficient funds."}

cx14 = ("pin = input('PIN: ').strip()\n\nhas_valid_format = (len(pin) == 4\n                    and pin.isdigit()\n                    and not pin.startswith('0'))\n\n"
        "if has_valid_format:\n    print('PIN format accepted')\nelse:\n    print('Enter four digits without a leading zero')\n")
cx14_starter = "pin = input('PIN: ').strip()\n\nhas_valid_format = ______________________________________\n"
E["cx14"] = {"type": "code", "xp": 5, "minLines": 8, "starter": cx14_starter,
    "cases": [case("4821", ["4821"], cx14), case("08A2", ["08A2"], cx14), case("0821 (leading zero)", ["0821"], cx14),
              case("482 (too short)", ["482"], cx14), case("48213 (too long)", ["48213"], cx14), case("12a4", ["12a4"], cx14), case("1000", ["1000"], cx14)],
    "check": ("import re\nassert not re.search(r'(?<![A-Za-z_0-9])int\\(', __source__), 'Do not convert the PIN to an integer; test it as text.'\n"
              "assert isinstance(globals().get('has_valid_format'), bool), 'Store the combined test in has_valid_format.'"),
    "answer": b64(cx14)}

cx15_head = ("left_dash = input('Left dashboard switch (0/1): ') == '1'\nright_dash = input('Right dashboard switch (0/1): ') == '1'\n"
             "child_lock = input('Child lock (0/1): ') == '1'\nmaster_unlock = input('Master unlock (0/1): ') == '1'\n"
             "left_inside = input('Left inside handle (0/1): ') == '1'\nleft_outside = input('Left outside handle (0/1): ') == '1'\n"
             "right_inside = input('Right inside handle (0/1): ') == '1'\nright_outside = input('Right outside handle (0/1): ') == '1'\n"
             "gear = input('Gear: ').strip().upper()\n\n")
cx15 = cx15_head + ("left_request = left_dash or left_outside or (left_inside and not child_lock)\n"
                    "right_request = right_dash or right_outside or (right_inside and not child_lock)\n"
                    "left_opens = gear == 'P' and master_unlock and left_request\nright_opens = gear == 'P' and master_unlock and right_request\n\n"
                    "if left_opens:\n    print('left door opens')\nif right_opens:\n    print('right door opens')\n"
                    "if not left_opens and not right_opens:\n    print('both doors stay closed')\n")
cx15_starter = cx15_head + "# Build left_request, right_request, left_opens, right_opens.\n"
def doors(ld, rd, cl, mu, li, lo, ri, ro, gear):
    return [ld, rd, cl, mu, li, lo, ri, ro, gear]
E["cx15"] = {"type": "code", "xp": 10, "minLines": 18, "maxLines": 30, "starter": cx15_starter,
    "cases": [case("Outside left handle", doors("0", "0", "0", "1", "0", "1", "0", "0", "P"), cx15),
              case("Child-locked inside handles", doors("0", "0", "1", "1", "1", "0", "1", "0", "P"), cx15),
              case("Inside handles, child lock off", doors("0", "0", "0", "1", "1", "0", "1", "0", "P"), cx15),
              case("Right dashboard switch", doors("0", "1", "0", "1", "0", "0", "0", "0", "P"), cx15),
              case("Both dashboard switches, gear D", doors("1", "1", "0", "1", "0", "0", "0", "0", "D"), cx15),
              case("Outside handles, master unlock off", doors("0", "0", "0", "0", "0", "1", "0", "1", "P"), cx15),
              case("Lower-case gear p", doors("1", "0", "0", "1", "0", "0", "0", "0", "p"), cx15)],
    "check": "\n".join(f"assert isinstance(globals().get({n!r}), bool), 'Store {n} as a Boolean value.'" for n in ["left_request", "right_request", "left_opens", "right_opens"]),
    "answer": b64(cx15)}

cx16 = ("voltage = float(input('Sensor voltage: '))\n\nif 12 <= voltage <= 18:\n"
        "    temperature = (75 / 0.5) * (voltage / (20 - voltage)) - (100 / 0.5)\n    print(f'Temperature: {temperature:.1f} C')\n"
        "else:\n    print('Voltage must be from 12 to 18 volts.')\n")
cx16_starter = "voltage = float(input('Sensor voltage: '))\n\n# Check the range before applying the formula.\n"
E["cx16"] = {"type": "code", "xp": 5, "minLines": 7, "starter": cx16_starter,
    "cases": [case("12", ["12"], cx16), case("11", ["11"], cx16), case("18", ["18"], cx16), case("15.5", ["15.5"], cx16), case("18.01", ["18.01"], cx16), case("0", ["0"], cx16)],
    "answer": b64(cx16)}
assert run(cx16, ["12"]).endswith("Temperature: 25.0 C")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-11",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 11 Workbook",
    "subtitle": "Boolean operators, bool, and input validation",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-11/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
