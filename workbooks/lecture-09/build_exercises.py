"""Build workbooks/lecture-09/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-09/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-09
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

def bools(*names, **overrides):
    """Blanks whose answer is True / False / TypeError, entered as text."""
    return {n: {"accept": [v], "placeholder": "True / False"} for n, v in names} | overrides

E = {}

# ---------------------------------------------------------------- Section 1
E["ex-w01"] = example("print(8 > 5)\nprint(8 < 5)\n")
E["ex-w02"] = example("condition = 12 >= 10\n\nprint(condition)\nprint(type(condition))\n")
E["cp1"] = {"type": "table", "xp": 1, "blanks": {
    "v1": {"accept": ["True"], "placeholder": "True / False"},
    "v2": {"accept": ["False"], "placeholder": "True / False"},
    "v3": {"accept": ["True"], "placeholder": "True / False"},
    "t": {"accept": ["bool", "boolean"], "show": "bool", "placeholder": "type"}}}
# ---------------------------------------------------------------- Section 2
E["ex-w03"] = example("x = 4\n\nprint(x < 4)\nprint(x <= 4)\nprint(x > 4)\nprint(x >= 4)\nprint(x == 4)\nprint(x != 4)\n")
E["cp2"] = {"type": "table", "xp": 1, "blanks": {
    "v1": {"accept": ["False"]}, "v2": {"accept": ["True"]}, "v3": {"accept": ["False"]},
    "v4": {"accept": ["True"]}, "v5": {"accept": ["True"]}, "v6": {"accept": ["False"]}}}
# ---------------------------------------------------------------- Section 3
E["ex-w04"] = example("floor = 13\n\nprint(floor == 13)\nprint(floor == 14)\n")
E["ex-w05"] = example("floor = 13\n\nif floor = 13:\n    print('Thirteenth floor')\n", output=False)
E["cp3-ops"] = {"type": "table", "xp": 1, "blanks": {
    "store": {"accept": ["="], "placeholder": "= or ==", "width": "6rem"},
    "test": {"accept": ["=="], "placeholder": "= or ==", "width": "6rem"}}}
cp3_fix = "score = 100\n\nif score == 100:\n    print('Perfect score')\n"
E["cp3-fix"] = {"type": "code", "xp": 2, "minLines": 4,
    "starter": "score = 100\n\nif score = 100:\n    print('Perfect score')\n",
    "cases": [
        {"name": "score = 100", "expected": run(cp3_fix)},
        {"name": "score = 99 (prints nothing)", "rewrite": [["score = 100", "score = 99"]], "expected": run(cp3_fix.replace("score = 100", "score = 99"))}],
    "check": 'assert "score == 100" in __source__, "The condition should test equality with score == 100."\n'
             'assert "= 100:" not in __source__.replace("==", ""), "An if condition must compare, not assign: use == in the condition."',
    "answer": b64(cp3_fix)}
# ---------------------------------------------------------------- Section 4
E["ex-w06"] = example("floor = 12\n\nprint(floor + 1 == 13)\nprint(2 * floor > 20)\n")
E["cp4"] = {"type": "table", "xp": 1, "blanks": {
    "l1": {"accept": ["8"], "placeholder": "left value", "width": "7rem"},
    "r1": {"accept": ["9"], "placeholder": "right value", "width": "7rem"},
    "v1": {"accept": ["True"], "placeholder": "True / False", "width": "7rem"},
    "l2": {"accept": ["8"], "placeholder": "left value", "width": "7rem"},
    "r2": {"accept": ["8.0"], "placeholder": "right value", "width": "7rem"},
    "v2": {"accept": ["True"], "placeholder": "True / False", "width": "7rem"}}}
# ---------------------------------------------------------------- Section 5
E["ex-w07"] = example("name1 = 'Ada'\nname2 = 'Ada'\nname3 = 'ada'\n\nprint(name1 == name2)\nprint(name1 == name3)\nprint(name1 != name3)\n")
E["cp5"] = {"type": "table", "xp": 1, "blanks": bools(("v1", "True"), ("v2", "False"), ("v3", "True"))}
E["cp5-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The comparison is `True` because the two strings are different: `'hello '` contains a trailing space, and a space is a character like any other.")}
# ---------------------------------------------------------------- Section 6
E["ex-w08"] = example("print('apple' < 'banana')\nprint('Zoe' < 'ada')\nprint('car' < 'cart')\n")
E["cp6"] = {"type": "table", "xp": 1, "blanks": bools(("v1", "True"), ("v2", "True"), ("v3", "True"))}
E["cp6-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The first characters decide the result: uppercase `D` comes before lowercase `c` in Python's character ordering, so `'Dog' < 'cat'` is `True`. The remaining characters are never compared.")}
# ---------------------------------------------------------------- Section 7
E["ex-w09"] = example("answer = 'YES'\n\nif answer.lower() == 'yes':\n    print('Response accepted')\nelse:\n    print('Please enter yes')\n")
E["ex-w10"] = example("first_name = 'Maya'\nsecond_name = 'MAYA'\n\nprint(first_name.lower() == second_name.lower())\n")
cp7 = "choice = 'N'\n\nif choice.lower() == 'n':\n    print('Letter n')\nelse:\n    print('Something else')\n"
E["cp7-cond"] = {"type": "code", "xp": 5, "minLines": 6,
    "starter": "choice = 'N'\n\nif False:  # replace False with your condition\n    print('Letter n')\nelse:\n    print('Something else')\n",
    "cases": [
        {"name": "choice = 'N'", "expected": run(cp7)},
        {"name": "choice = 'n'", "rewrite": [["choice = 'N'", "choice = 'n'"]], "expected": run(cp7.replace("'N'", "'n'"))},
        {"name": "choice = 'y'", "rewrite": [["choice = 'N'", "choice = 'y'"]], "expected": run(cp7.replace("'N'", "'y'"))},
        {"name": "choice = 'No'", "rewrite": [["choice = 'N'", "choice = 'No'"]], "expected": run(cp7.replace("'N'", "'No'"))}],
    "check": 'assert "False" not in __source__.split("if", 1)[1].split(":", 1)[0], "Replace False with a comparison that uses choice."\n'
             'assert ".lower()" in __source__ or ".upper()" in __source__, "Convert choice to one case (for example choice.lower()) before comparing it."',
    "answer": b64(cp7)}
E["cp7-why"] = {"type": "short", "xp": 2, "answer": b64(
    "`.lower()` produces a lowercase copy of `choice` for the comparison, so `'N'` and `'n'` both compare equal to `'n'`. Capitalization no longer affects the result, and the original string is unchanged.")}
# ---------------------------------------------------------------- Section 8
E["ex-w11"] = example("total = 0.1 + 0.2\n\nprint(total)\nprint(total == 0.3)\n")
E["ex-w12"] = example("total = 0.1 + 0.2\ntarget = 0.3\ntolerance = 1e-9\n\nclose_enough = abs(total - target) < tolerance\nprint(close_enough)\n")
E["cp8"] = {"type": "table", "xp": 2, "blanks": {"diff": {
    "accept": ["measurement - expected", "expected - measurement", "measurement-expected", "expected-measurement"],
    "caseSensitive": True, "placeholder": "an expression", "width": "16rem"}}}
E["cp8-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Computed floats can differ from the exact value by a tiny rounding amount, as in `0.1 + 0.2 == 0.3` being `False`. Exact `==` then rejects values that the problem treats as equal. Compare the size of the difference with a tolerance instead.")}
# ---------------------------------------------------------------- Section 9
E["ex-w13"] = example("print(10 == 10.0)\nprint('10' == 10)\n")
E["ex-w14"] = example("print('10' < 10)\n", output=False)
E["cp9"] = {"type": "table", "xp": 1, "blanks": bools(("v1", "True"), ("v2", "False"),
    v3={"accept": ["TypeError", "error", "type error"], "show": "TypeError", "placeholder": "True / False / TypeError"},
    conv={"accept": ["int('5')", "int(\"5\")", "int", "int()", "int('5') > 5", "int(\"5\") > 5", "float('5')", "float(\"5\")", "float", "float()", "float('5') > 5"],
          "caseSensitive": True, "show": "int('5')", "placeholder": "a conversion", "width": "12rem"})}
# ---------------------------------------------------------------- Section 10
E["cp10"] = {"type": "table", "xp": 1, "blanks": {
    "b": {"accept": ["30"], "placeholder": "value"},
    "at": {"accept": ["accepted", "accept"], "show": "accepted", "placeholder": "accepted / rejected"},
    "cond": {"accept": ["people <= 30", "people<=30", "30 >= people", "30>=people", "people < 31", "people<31"],
             "caseSensitive": True, "show": "people <= 30", "placeholder": "condition", "width": "12rem"}}}
# ---------------------------------------------------------------- Section 11
negatives = [str(n) for n in range(-1, -101, -1)] + ["-0.5", "-1.0", "-2.0", "-5.0", "-10.0", "-0.1", "-1.5", "-2.5", "-273"]
positives = [str(n) for n in range(1, 101)] + ["0.5", "1.0", "2.0", "5.0", "10.0", "0.1", "1.5", "2.5", "20.0", "25.0", "100.0"]
E["cp11"] = {"type": "table", "xp": 1, "blanks": {
    "i1": {"accept": negatives, "show": "-1", "placeholder": "temperature"},
    "e1": {"accept": ["warning", "a warning", "warning appears", "warning shown", "prints warning", "warn"], "show": "warning", "placeholder": "warning / no warning"},
    "i2": {"accept": ["0", "0.0"], "placeholder": "temperature"},
    "e2": {"accept": ["no warning", "none", "nothing", "no warning appears", "no", "no message"], "show": "no warning", "placeholder": "warning / no warning"},
    "i3": {"accept": positives, "show": "1", "placeholder": "temperature"},
    "e3": {"accept": ["no warning", "none", "nothing", "no warning appears", "no", "no message"], "show": "no warning", "placeholder": "warning / no warning"}}}
# ---------------------------------------------------------------- Final Review
E["fr1"] = {"type": "table", "xp": 1, "blanks": {
    "o1": {"accept": ["<"], "width": "6rem"}, "o2": {"accept": ["<="], "width": "6rem"}, "o3": {"accept": [">"], "width": "6rem"},
    "o4": {"accept": [">="], "width": "6rem"}, "o5": {"accept": ["=="], "width": "6rem"}, "o6": {"accept": ["!="], "width": "6rem"}}}
E["fr2"] = {"type": "short", "xp": 2, "answer": b64(
    "`=` is the assignment operator: it gives a value to a variable. `==` is the equality operator: it compares two values and produces `True` or `False`.")}
E["fr3"] = {"type": "table", "xp": 1, "blanks": {"t": {"accept": ["bool", "boolean"], "show": "bool", "placeholder": "type", "width": "8rem"}}}
E["fr4"] = {"type": "short", "xp": 2, "answer": b64(
    "Python compares character codes, not dictionary order. Uppercase letters come before lowercase letters, so uppercase `Z` comes before lowercase `a` and `'Zoe' < 'ada'` is `True`.")}
E["fr5"] = {"type": "table", "xp": 2, "blanks": {"cond": {
    "accept": ["a.lower() == b.lower()", "a.lower()==b.lower()", "b.lower() == a.lower()", "a.upper() == b.upper()", "a.upper()==b.upper()", "b.upper() == a.upper()", "a.casefold() == b.casefold()"],
    "caseSensitive": True, "show": "a.lower() == b.lower()", "placeholder": "comparison", "width": "16rem"}}}
E["fr6"] = {"type": "table", "xp": 2, "blanks": {"cond": {
    "accept": ["abs(x - y) < tolerance", "abs(x-y) < tolerance", "abs(x - y)<tolerance", "abs(x-y)<tolerance", "abs(y - x) < tolerance", "abs(y-x) < tolerance", "abs(x - y) < tol", "abs(x-y) < tol", "abs(x - y) < 1e-9", "abs(x-y) < 1e-9"],
    "caseSensitive": True, "show": "abs(x - y) < tolerance", "placeholder": "condition", "width": "16rem"}}}
E["fr7"] = {"type": "short", "xp": 2, "answer": b64(
    "The boundary is the one value where `>` and `>=` (or `<` and `<=`) give different results. A test at the boundary is the test that catches the wrong operator; tests only below and above it would pass with either operator.")}
# ---------------------------------------------------------------- Additional Practice
E["pa"] = {"type": "table", "xp": 1, "blanks": bools(("v1", "True"), ("v2", "False"), ("v3", "True"), ("v4", "True"), ("v5", "False"),
    v6={"accept": ["TypeError", "error", "type error"], "show": "TypeError", "placeholder": "True / False / TypeError"})}
E["pb"] = {"type": "table", "xp": 2, "blanks": {
    "c1": {"accept": ["age < 5", "age<5", "5 > age", "5>age", "child_age < 5", "years < 5"], "caseSensitive": True, "show": "age < 5", "placeholder": "condition", "width": "14rem"},
    "c2": {"accept": ["attempt == password", "attempt==password", "password == attempt", "password==attempt", "guess == password", "entry == password", "password_attempt == password"], "caseSensitive": True, "show": "attempt == password", "placeholder": "condition", "width": "14rem"},
    "c3": {"accept": ["value != previous", "value!=previous", "previous != value", "previous!=value"], "caseSensitive": True, "show": "value != previous", "placeholder": "condition", "width": "14rem"},
    "c4": {"accept": ["measurement <= 2.5", "measurement<=2.5", "2.5 >= measurement", "2.5>=measurement"], "caseSensitive": True, "show": "measurement <= 2.5", "placeholder": "condition", "width": "14rem"}}}
pc = "word1 = 'Hello'\nword2 = 'hello'\n\nif word1.lower() == word2.lower():\n    print('Match')\nelse:\n    print('Different')\n"
E["pc"] = {"type": "code", "xp": 5, "minLines": 7,
    "starter": "word1 = 'Hello'\nword2 = 'hello'\n\n# Print Match or Different.\n",
    "cases": [
        {"name": "'Hello' and 'hello'", "expected": run(pc)},
        {"name": "'Hello' and 'HELLO'", "rewrite": [["word2 = 'hello'", "word2 = 'HELLO'"]], "expected": run(pc.replace("word2 = 'hello'", "word2 = 'HELLO'"))},
        {"name": "'Hello' and 'help'", "rewrite": [["word2 = 'hello'", "word2 = 'help'"]], "expected": run(pc.replace("word2 = 'hello'", "word2 = 'help'"))},
        {"name": "'Hello' and 'hello ' (trailing space)", "rewrite": [["word2 = 'hello'", "word2 = 'hello '"]], "expected": run(pc.replace("word2 = 'hello'", "word2 = 'hello '"))}],
    "check": 'assert ".lower()" in __source__ or ".upper()" in __source__ or ".casefold()" in __source__, "Convert both strings to the same case (for example with .lower()) before comparing them."\n'
             'assert word1 == "Hello", "Do not change word1 itself; convert a copy inside the comparison."',
    "answer": b64(pc)}
pd = "calculated = 0.1 + 0.2\nexpected = 0.3\n\nclose_enough = abs(calculated - expected) < 0.0001\nprint(close_enough)\n"
E["pd"] = {"type": "code", "xp": 5, "minLines": 6,
    "starter": "calculated = 0.1 + 0.2\nexpected = 0.3\n\n# Store the Boolean value, then print it.\n",
    "cases": [
        {"name": "0.1 + 0.2 against 0.3", "expected": run(pd)},
        {"name": "0.1 + 0.2 against 0.31", "rewrite": [["expected = 0.3", "expected = 0.31"]], "expected": run(pd.replace("expected = 0.3", "expected = 0.31"))},
        {"name": "0.1 + 0.2 against 0.30005", "rewrite": [["expected = 0.3", "expected = 0.30005"]], "expected": run(pd.replace("expected = 0.3", "expected = 0.30005"))}],
    "check": 'assert "abs(" in __source__, "Use abs() so the difference is a nonnegative distance."\n'
             'assert "0.0001" in __source__ or "1e-4" in __source__ or "1e-04" in __source__, "Compare the difference with the tolerance 0.0001."\n'
             'user = {k: v for k, v in globals().items() if not k.startswith("__")}\n'
             'assert any(type(v) is bool for v in user.values()), "Store the comparison result in a variable before printing it."',
    "answer": b64(pd)}
below = ["19", "19.9", "19.5", "19.99", "18", "15", "10", "5", "1", "0", "12", "16", "17", "19.0", "0.5", "2", "3", "4", "6", "7", "8", "9", "11", "13", "14"]
above = ["21", "20.1", "20.5", "20.01", "22", "25", "30", "40", "50", "100", "21.0", "23", "24", "26", "27", "28", "29", "35", "45", "60", "75", "80", "90", "20.2", "20.9"]
E["pe"] = {"type": "table", "xp": 1, "blanks": {
    "cond": {"accept": ["mass > 20", "mass>20", "20 < mass", "20<mass", "mass > 20.0", "mass>20.0"], "caseSensitive": True, "show": "mass > 20", "placeholder": "condition", "width": "12rem"},
    "at": {"accept": ["no extra fee", "no fee", "no", "none", "not charged", "no charge", "regular price", "no extra charge", "nothing"], "show": "no extra fee", "placeholder": "fee or no fee?"},
    "m1": {"accept": below, "show": "19.9", "placeholder": "kg"}, "f1": {"accept": ["no", "no fee", "no extra fee", "none", "false"], "show": "no", "placeholder": "yes / no"},
    "m2": {"accept": ["20", "20.0"], "placeholder": "kg"}, "f2": {"accept": ["no", "no fee", "no extra fee", "none", "false"], "show": "no", "placeholder": "yes / no"},
    "m3": {"accept": above, "show": "20.1", "placeholder": "kg"}, "f3": {"accept": ["yes", "fee", "extra fee", "true"], "show": "yes", "placeholder": "yes / no"}}}
pf = "answer = 'Yes'\ncalculated = 0.1 + 0.2\nexpected = 0.3\n\nif answer.lower() == 'yes':\n    print('Accepted')\n\nif abs(calculated - expected) < 1e-9:\n    print('Values match')\n"
E["pf"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "answer = 'Yes'\ncalculated = 0.1 + 0.2\nexpected = 0.3\n\nif answer = 'yes':\n    print('Accepted')\n\nif calculated == expected:\n    print('Values match')\n",
    "cases": [
        {"name": "answer = 'Yes'", "expected": run(pf)},
        {"name": "answer = 'YES'", "rewrite": [["answer = 'Yes'", "answer = 'YES'"]], "expected": run(pf.replace("answer = 'Yes'", "answer = 'YES'"))},
        {"name": "answer = 'no'", "rewrite": [["answer = 'Yes'", "answer = 'no'"]], "expected": run(pf.replace("answer = 'Yes'", "answer = 'no'"))},
        {"name": "expected = 0.4", "rewrite": [["expected = 0.3", "expected = 0.4"]], "expected": run(pf.replace("expected = 0.3", "expected = 0.4"))}],
    "check": 'assert ".lower()" in __source__ or ".upper()" in __source__, "Normalize the answer with .lower() so any capitalization of yes is recognized."\n'
             'assert "abs(" in __source__, "Compare the size of the float difference with abs()."\n'
             'assert "1e-9" in __source__ or "0.000000001" in __source__, "Use the stated tolerance 1e-9."',
    "answer": b64(pf)}
# ---------------------------------------------------------------- Putting It All Together
cal = ("expected_label = 'sensor-a'\nentered_label = input('Sensor label: ')\n\n"
       "label_matches = entered_label.lower() == expected_label.lower()\nif label_matches:\n    print('Label accepted')\nelse:\n    print('Check the sensor label')\n\n"
       "measured = float(input('Measured value: '))\ntarget = float(input('Target value: '))\ntolerance = 1.0\n\n"
       "within_tolerance = abs(measured - target) < tolerance\nif within_tolerance:\n    print('Measurement accepted')\nelse:\n    print('Measurement outside tolerance')\n")
E["ex-w15"] = example(cal, output=False)
assert run(cal, ["SENSOR-A", "20.4", "20"]).endswith("Measurement accepted")
assert run(cal, ["sensor-a", "21", "20"]).endswith("Measurement outside tolerance")
assert run(cal, ["Sensor-A", "19.2", "20.0"]) == "Sensor label: Label accepted\nMeasured value: Target value: Measurement accepted"
E["it-trace"] = {"type": "table", "xp": 1, "blanks": {
    "b1": {"accept": ["True"], "placeholder": "True / False"},
    "m1": {"accept": ["Label accepted"], "caseSensitive": True, "placeholder": "message", "width": "16rem"},
    "b2": {"accept": ["True"], "placeholder": "True / False"},
    "m2": {"accept": ["Measurement accepted"], "caseSensitive": True, "placeholder": "message", "width": "16rem"}}}
E["it-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The condition `difference < tolerance` has a strict boundary at `1.0`. A difference below `1.0` is accepted, exactly `1.0` is rejected, and above `1.0` is rejected. Only a test at `1.0` shows whether `<` or `<=` was used.")}
# ---------------------------------------------------------------- Coding Practice
E["pr1"] = {"type": "short", "xp": 2, "answer": b64(
    "Integers are stored exactly, so `5 + 5` is exactly `10` and `==` is dependable. A floating-point calculation can carry a tiny rounding difference, so its result may not be exactly equal to the value you expect. Use `count == 10` and `abs(reading - 10.0) < 0.001`.")}
E["pr1-cond"] = {"type": "table", "xp": 2, "blanks": {
    "c1": {"accept": ["count == 10", "count==10", "10 == count", "10==count"], "caseSensitive": True, "show": "count == 10", "placeholder": "condition", "width": "16rem"},
    "c2": {"accept": ["abs(reading - 10.0) < 0.001", "abs(reading - 10) < 0.001", "abs(reading-10.0) < 0.001", "abs(reading-10) < 0.001", "abs(reading - 10.0)<0.001", "abs(reading-10.0)<0.001",
                      "abs(10.0 - reading) < 0.001", "abs(10 - reading) < 0.001", "abs(10.0-reading) < 0.001", "abs(reading - 10.0) < 1e-3", "abs(reading - 10) < 1e-3"],
           "caseSensitive": True, "show": "abs(reading - 10.0) < 0.001", "placeholder": "condition", "width": "16rem"}}}
pr2 = "floor = 13\nprint(floor == 13)\n"
E["pr2"] = {"type": "code", "xp": 5, "minLines": 3,
    "starter": "if floor = 13:\n    print(floor = 13)\n",
    "cases": [
        {"name": "floor = 13", "expected": run(pr2)},
        {"name": "floor = 12", "rewrite": [["floor = 13\n", "floor = 12\n"]], "expected": run(pr2.replace("floor = 13\n", "floor = 12\n"))}],
    "check": 'assert "floor == 13" in __source__, "The print should display the Boolean result of floor == 13."\n'
             'assert "if" not in __source__.split("#")[0].split(), "No if statement is needed: one assignment, then one print."\n'
             'assert type(floor) is int, "Store the floor number as a whole number in floor."',
    "answer": b64(pr2)}
E["ex-w16"] = example("entry = 'OPEN'\n\nif entry.lower() == 'open':\n    print('Accepted')\nelse:\n    print('Different')\n")
E["pr3"] = {"type": "table", "xp": 1, "blanks": {
    "c1": {"accept": ["True"], "placeholder": "True / False"}, "o1": {"accept": ["Accepted"], "caseSensitive": True, "placeholder": "output"},
    "c2": {"accept": ["False"], "placeholder": "True / False"}, "o2": {"accept": ["Different"], "caseSensitive": True, "placeholder": "output"}}}
rejected = ["'start '", "start ", "' start'", " start", "'stat'", "stat", "'starts'", "starts", "'star'", "star", "'strat'", "strat", "'start!'", "start!", "'begin'", "begin", "'stop'", "stop", "'sart'", "sart", "'startt'", "startt", "'st art'", "st art", "'start.'", "start.", "'restart'", "restart", "'starting'", "starting", "'started'", "started", "'go'", "go", "'run'", "run", "'quit'", "quit", "'start1'", "start1", "'s tart'", "s tart", "'srart'", "srart"]
E["pr4"] = {"type": "table", "xp": 1, "blanks": {
    "i1": {"accept": ["'start'", "start", "\"start\""], "caseSensitive": True, "show": "'start'", "placeholder": "input"},
    "e1": {"accept": ["accepted", "accept", "yes", "match", "accepted command", "command accepted"], "show": "accepted", "placeholder": "accepted / rejected"},
    "i2": {"accept": ["'START'", "START", "'Start'", "Start", "'StArT'", "StArT", "'sTART'", "sTART", "'StaRt'", "StaRt", "'sTaRt'", "sTaRt", "'STart'", "STart", "'starT'", "starT", "'Start'", "\"START\"", "\"Start\"", "'STArt'", "STArt", "'stART'", "stART", "'sTArT'", "sTArT", "'StART'", "StART", "'STARt'", "STARt", "'sTart'", "sTart", "'stArt'", "stArt", "'staRT'", "staRT", "'stArT'", "stArT", "'StaRT'", "StaRT", "'STaRT'", "STaRT"],
           "caseSensitive": True, "show": "'START'", "placeholder": "input"},
    "e2": {"accept": ["accepted", "accept", "yes", "match", "accepted command", "command accepted"], "show": "accepted", "placeholder": "accepted / rejected"},
    "i3": {"accept": rejected, "caseSensitive": True, "show": "'start '", "placeholder": "input"},
    "e3": {"accept": ["rejected", "reject", "no", "not accepted", "different", "unknown", "unknown command", "no match"], "show": "rejected", "placeholder": "accepted / rejected"}}}
E["pr5"] = {"type": "short", "xp": 2, "answer": b64(
    "Uppercase letters come before lowercase letters, so `'Zoe'` comes before `'ada'`. Digits come before letters, so `'9cats'` comes before `'birds'`. Spaces and punctuation are characters too and take part in the comparison, and a shorter string that begins a longer one comes first.")}
E["pr6"] = {"type": "table", "xp": 1, "blanks": {
    "s1": {"accept": ["'map'", "map", "\"map\""], "caseSensitive": True, "show": "'map'", "placeholder": "string"}, "p1": {"accept": ["3", "third", "position 3", "p"], "show": "3", "placeholder": "position"},
    "s2": {"accept": ["'Code'", "Code", "\"Code\""], "caseSensitive": True, "show": "'Code'", "placeholder": "string"}, "p2": {"accept": ["1", "first", "position 1", "C"], "show": "1", "placeholder": "position"},
    "s3": {"accept": ["'car'", "car", "\"car\""], "caseSensitive": True, "show": "'car'", "placeholder": "string"}, "p3": {"accept": ["end of 'car'", "end of car", "4", "end", "the end", "car ends", "'car' ends", "length", "shorter", "end of the shorter string", "after 3", "after position 3", "fourth", "position 4"], "show": "end of 'car'", "placeholder": "position or “end”"},
    "s4": {"accept": ["'9cats'", "9cats", "\"9cats\""], "caseSensitive": True, "show": "'9cats'", "placeholder": "string"}, "p4": {"accept": ["1", "first", "position 1", "9"], "show": "1", "placeholder": "position"}}}
pr7 = ("first = float(input('First number: '))\nsecond = float(input('Second number: '))\nthird = float(input('Third number: '))\n\n"
       "largest = first\nif second > largest:\n    largest = second\nif third > largest:\n    largest = third\n\nprint('Largest:', largest)\n")
E["pr7"] = {"type": "code", "xp": 10, "minLines": 11,
    "starter": "first = float(input('First number: '))\nsecond = float(input('Second number: '))\nthird = float(input('Third number: '))\n\nlargest = first\n# Compare second and third with largest.\n",
    "cases": [
        {"name": "4, 9, 2.5", "inputs": ["4", "9", "2.5"], "expected": run(pr7, ["4", "9", "2.5"])},
        {"name": "7, 7, 3", "inputs": ["7", "7", "3"], "expected": run(pr7, ["7", "7", "3"])},
        {"name": "1, 2, 10", "inputs": ["1", "2", "10"], "expected": run(pr7, ["1", "2", "10"])},
        {"name": "-5, -2, -9", "inputs": ["-5", "-2", "-9"], "expected": run(pr7, ["-5", "-2", "-9"])}],
    "check": 'assert "max(" not in __source__, "Do not call max(); compare the values with if statements."\n'
             'assert __source__.count("if ") >= 2, "Use two separate if statements, one for second and one for third."\n'
             'assert "else" not in __source__, "Two separate if statements are enough here; no else is needed."',
    "answer": b64(pr7)}
pr8 = ("first = input('First label: ')\nsecond = input('Second label: ')\n\nif first < second:\n    earlier = first\n    later = second\nelse:\n    earlier = second\n    later = first\n\n"
       "print('First in Python order:', earlier)\nprint('Second in Python order:', later)\n")
E["pr8"] = {"type": "code", "xp": 10, "minLines": 11,
    "starter": "first = input('First label: ')\nsecond = input('Second label: ')\n\n",
    "cases": [
        {"name": "Cedar, Birch", "inputs": ["Cedar", "Birch"], "expected": run(pr8, ["Cedar", "Birch"])},
        {"name": "apple, Apricot", "inputs": ["apple", "Apricot"], "expected": run(pr8, ["apple", "Apricot"])},
        {"name": "note, notebook", "inputs": ["note", "notebook"], "expected": run(pr8, ["note", "notebook"])},
        {"name": "9cats, birds", "inputs": ["9cats", "birds"], "expected": run(pr8, ["9cats", "birds"])}],
    "check": 'assert __source__.count("if ") == 1 and "else" in __source__, "Use one if/else statement to decide the order."\n'
             'assert ".lower()" not in __source__, "Python order keeps capitalization significant; do not change the case."',
    "answer": b64(pr8)}
pr9 = "command = input('Command: ')\n\nif command.lower() == 'quit':\n    print('Command accepted')\nelse:\n    print('Unknown command')\n"
E["pr9"] = {"type": "code", "xp": 5, "minLines": 7,
    "starter": "command = input('Command: ')\n\n",
    "cases": [
        {"name": "QUIT", "inputs": ["QUIT"], "expected": run(pr9, ["QUIT"])},
        {"name": "quite", "inputs": ["quite"], "expected": run(pr9, ["quite"])},
        {"name": "Quit", "inputs": ["Quit"], "expected": run(pr9, ["Quit"])},
        {"name": "quit (with a trailing space)", "inputs": ["quit "], "expected": run(pr9, ["quit "])}],
    "check": 'assert ".lower()" in __source__ or ".upper()" in __source__, "Normalize the command with .lower() so any capitalization of quit matches."',
    "answer": b64(pr9)}
pr10 = "first = float(input('First reading: '))\nsecond = float(input('Second reading: '))\n\nif abs(first - second) < 0.01:\n    print('Match')\nelse:\n    print('Different')\n"
E["pr10"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "first = float(input('First reading: '))\nsecond = float(input('Second reading: '))\n\n",
    "cases": [
        {"name": "2.0 and 1.995", "inputs": ["2.0", "1.995"], "expected": run(pr10, ["2.0", "1.995"])},
        {"name": "2.0 and 1.98", "inputs": ["2.0", "1.98"], "expected": run(pr10, ["2.0", "1.98"])},
        {"name": "1.995 and 2.0 (reversed)", "inputs": ["1.995", "2.0"], "expected": run(pr10, ["1.995", "2.0"])},
        {"name": "1.0 and 1.01 (exactly at the boundary)", "inputs": ["1.0", "1.01"], "expected": run(pr10, ["1.0", "1.01"])}],
    "check": 'assert "abs(" in __source__, "Use abs() so the order of the two readings does not matter."\n'
             'assert "0.01" in __source__ or "1e-2" in __source__, "Compare the difference with the tolerance 0.01."',
    "answer": b64(pr10),
    "answerNote": "abs(1.0 - 1.01) is 0.010000000000000009 in floating point. The boundary case prints Different either way. The strict < is still the right operator."}
pr11 = "bill = float(input('Bill: $'))\nrating = int(input('Service rating (1 or 2): '))\n\nif rating == 1:\n    tip_rate = 0.20\nelse:\n    tip_rate = 0.15\n\ntip = bill * tip_rate\nprint(f'Tip: ${tip:.2f}')\n"
E["pr11"] = {"type": "code", "xp": 10, "minLines": 10,
    "starter": "bill = float(input('Bill: $'))\nrating = int(input('Service rating (1 or 2): '))\n\n",
    "cases": [
        {"name": "$40, rating 1", "inputs": ["40", "1"], "expected": run(pr11, ["40", "1"])},
        {"name": "$40, rating 2", "inputs": ["40", "2"], "expected": run(pr11, ["40", "2"])},
        {"name": "$25.50, rating 1", "inputs": ["25.50", "1"], "expected": run(pr11, ["25.50", "1"])},
        {"name": "$0, rating 2", "inputs": ["0", "2"], "expected": run(pr11, ["0", "2"])}],
    "check": 'assert __source__.count("if ") == 1 and "else" in __source__, "Use one if/else statement to choose the tip rate."',
    "answer": b64(pr11)}
pr12 = "frequency = float(input('Frequency in Hz: '))\n\nif frequency < 3e9:\n    print('Below threshold')\nelse:\n    print('At or above threshold')\n"
E["pr12"] = {"type": "code", "xp": 5, "minLines": 7,
    "starter": "frequency = float(input('Frequency in Hz: '))\n\n",
    "cases": [
        {"name": "2.5e9 (below)", "inputs": ["2.5e9"], "expected": run(pr12, ["2.5e9"])},
        {"name": "3e9 (at the boundary)", "inputs": ["3e9"], "expected": run(pr12, ["3e9"])},
        {"name": "3.5e9 (above)", "inputs": ["3.5e9"], "expected": run(pr12, ["3.5e9"])},
        {"name": "3000000000 (at the boundary, written out)", "inputs": ["3000000000"], "expected": run(pr12, ["3000000000"])}],
    "answer": b64(pr12)}

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-09",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 9 Workbook",
    "subtitle": "Relational operators and comparing values",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-09/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
