"""Build workbooks/lecture-04/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-04/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-04
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

def types(*names):
    return [{"accept": [n]} for n in names]

E = {}

# ---------------------------------------------------------------- Section 1
E["ex-w01"] = example("price = 24.95\nprint(price)\n")
E["ex-w02"] = example("course = 'COMP 1001'\nroom = 2006\n", output=False)
E["cp1"] = {
    "type": "table", "xp": 1,
    "blanks": {
        "name1": {"accept": ["course"], "placeholder": "name"},
        "name2": {"accept": ["room"], "placeholder": "name"},
        "value1": {"accept": ["'COMP 1001'", "\"COMP 1001\"", "COMP 1001"], "caseSensitive": True, "placeholder": "value"},
        "value2": {"accept": ["2006"], "placeholder": "value"},
    },
}
# ---------------------------------------------------------------- Section 2
E["ex-w03"] = example("bottles = 6\nprint(bottles)\nbottles = 8\nprint(bottles)\n")
E["ex-w04"] = example("count = 4\ncount = count + 1\nprint(count)\n")
E["ex-w05"] = example("score = 10\nscore = 12\nscore = score + 1\n", output=False)
E["cp2-trace"] = {"type": "table", "xp": 1, "blanks": {"s1": {"accept": ["10"]}, "s2": {"accept": ["12"]}, "s3": {"accept": ["13"]}}}
E["cp2-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The last statement evaluates `12 + 1` first and assigns the result, 13, to `score`. "
    "It is an instruction (\"make `score` refer to the value of `score + 1`\"), not a mathematical equation, "
    "so it is valid even though `score` cannot equal `score + 1` in mathematics. The program has no printed output.")}
# ---------------------------------------------------------------- Section 3
E["ex-w06"] = example("print(type(42))\nprint(type(3.5))\nprint(type('42'))\nprint(type(True))\n")
E["cp3-types"] = {"type": "table", "xp": 1, "blanks": {
    "t1": {"accept": ["int"]}, "t2": {"accept": ["float"]}, "t3": {"accept": ["str"]}, "t4": {"accept": ["bool"]}}}
E["cp3-tool"] = {"type": "table", "xp": 1, "blanks": {"tool": {
    "accept": ["type()", "type", "the type() function", "type() function", "print(type())", "print(type(...))", "type(...)", "the type function", "print(type(x))", "type(x)"],
    "placeholder": "a Python function", "width": "18rem"}}}
# ---------------------------------------------------------------- Section 4
E["ex-w07"] = example("value = 10\nprint(value, type(value))\nvalue = 'ten'\nprint(value, type(value))\n")
E["ex-w08"] = example("status = 'ready'\nstatus = True\nstatus = 1\n", output=False)
E["cp4-trace"] = {"type": "table", "xp": 1, "blanks": {
    "v1": {"accept": ["'ready'", "\"ready\"", "ready"], "caseSensitive": True}, "t1": {"accept": ["str"]},
    "v2": {"accept": ["True"], "caseSensitive": True}, "t2": {"accept": ["bool"]},
    "v3": {"accept": ["1"]}, "t3": {"accept": ["int"]}}}
E["cp4-why"] = {"type": "short", "xp": 2, "answer": b64(
    "A reader must keep checking what kind of value the name currently refers to. "
    "Code written for the earlier kind of value (for example, text) may no longer work once the name refers to a number, and it is harder to tell what `status` means at any given line.")}
# ---------------------------------------------------------------- Section 5
E["cp5-names"] = {"type": "table", "xp": 1, "blanks": {
    "n1": {"accept": ["valid"]}, "n2": {"accept": ["valid"]}, "n3": {"accept": ["invalid"]}, "n4": {"accept": ["invalid"]}, "n5": {"accept": ["valid"]}}}
E["cp5-why"] = {"type": "short", "xp": 2, "answer": b64(
    "`student_count` best follows the course convention: lowercase words separated by an underscore, with a clear meaning. "
    "`3students` is invalid because it starts with a digit; `for` is invalid because it is a keyword. "
    "`studentCount` and `Students` are valid Python but do not follow `lower_case_with_underscores`.")}
# ---------------------------------------------------------------- Section 6
E["ex-w09"] = example("TAX_RATE = 0.15\nMAX_ATTEMPTS = 3\n", output=False)
E["ex-w10"] = example("# Use one named value so the rate is easy to update later.\nTAX_RATE = 0.15\n\nprint('Current tax rate:', TAX_RATE)\n")
E["cp6-names"] = {"type": "table", "xp": 1, "blanks": {
    "r1": {"accept": ["TAX_RATE", "TAX_RATE_PERCENT", "SALES_TAX_RATE", "TAX"], "caseSensitive": True, "placeholder": "constant"},
    "r2": {"accept": ["number_of_seats", "seat_count", "num_seats", "seats", "seat_total", "total_seats", "num_of_seats", "seats_count"], "caseSensitive": True},
    "r3": {"accept": ["unit_price", "price_per_unit", "price", "item_price", "unit_cost"], "caseSensitive": True}}}
E["cp6-comment"] = {"type": "short", "xp": 2, "minChars": 15, "placeholder": "# …", "answer": b64(
    "One suitable comment is:\n\n`# Keep the rate in one place so later changes stay consistent.`\n\n"
    "A useful comment gives the reason for the choice. The capital letters in `TAX_RATE` express the intent that the value stays fixed; Python does not enforce it.")}
# ---------------------------------------------------------------- Section 7
E["ex-w11"] = example("print(total_cost)\n", output=False)
E["ex-w12"] = example("total_cost = 25.0\nprint(totl_cost)\n", output=False)
fix = "room_capacity = 35\nprint(room_capacity)\n"
E["cp7-fix"] = {"type": "code", "xp": 2, "minLines": 3,
    "starter": "room_capacity = 35\nprint(Room_capacity)\n",
    "cases": [{"name": "Program output", "expected": run(fix)}],
    "check": 'assert "Room_capacity" not in __source__, "The name Room_capacity is still in the program. Make both spellings match the assignment."\n'
             'assert "room_capacity" in __source__, "Keep the name room_capacity from the original assignment."',
    "answer": b64(fix)}
E["cp7-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Python names are case-sensitive. The assignment creates `room_capacity`, so `Room_capacity` (with a capital R) is a different, undefined name and Python raises a `NameError`.")}
# ---------------------------------------------------------------- Final Review
w14 = "MAX_SEATS = 30\navailable = 24\nlabel = 'Room A'\n\nprint(label, available)\navailable = 22\nprint(label, available)\n"
E["ex-w14"] = example(w14, output=False)
E["fr1"] = {"type": "short", "xp": 2, "answer": b64(
    "`MAX_SEATS` is the name intended as a constant. `available` and `label` are ordinary variable names. All three names are assigned using the same Python syntax; only the capital letters signal the intent.")}
E["fr2"] = {"type": "table", "xp": 1, "blanks": {"t1": {"accept": ["int"]}, "t2": {"accept": ["int"]}, "t3": {"accept": ["str"]}}}
E["fr3"] = {"type": "table", "xp": 1, "blanks": {"a1": {"accept": ["24"]}, "a2": {"accept": ["22"]}}}
E["fr4"] = {"type": "table", "xp": 1, "blanks": {
    "l1": {"accept": ["Room A 24"], "caseSensitive": True, "placeholder": "first line", "width": "14rem"},
    "l2": {"accept": ["Room A 22"], "caseSensitive": True, "placeholder": "second line", "width": "14rem"}}}
E["fr5"] = {"type": "short", "xp": 2, "answer": b64(
    "The capital letters communicate that the maximum is intended to remain fixed while the program runs. Python would still allow a later reassignment; the convention is for human readers.")}
# ---------------------------------------------------------------- Additional Practice
E["pa"] = {"type": "table", "xp": 1, "blanks": {"t1": {"accept": ["int"]}, "t2": {"accept": ["float"]}, "t3": {"accept": ["str"]}, "t4": {"accept": ["bool"]}}}
E["pb"] = {"type": "table", "xp": 1, "blanks": {
    "n1": {"accept": ["first_score", "score_1", "score1", "initial_score", "score_one", "first_result"], "caseSensitive": True},
    "n2": {"accept": ["total_price", "price_total", "total_cost", "total"], "caseSensitive": True},
    "n3": {"accept": ["class_name", "class_code", "course", "course_code", "course_name", "class_level", "class_size", "class_label", "class_title", "class_id", "class_number", "class_type", "class_year", "class_section", "student_class", "python_class", "class_period", "class_room", "classroom"], "caseSensitive": True},
    "n4": {"accept": ["lab_seats", "seat_count", "number_of_seats", "lab_seat_count", "num_seats", "seats", "lab_capacity", "seats_in_lab", "total_seats", "num_lab_seats", "number_of_lab_seats", "seats_available", "available_seats"], "caseSensitive": True}}}
E["ex-w15"] = example("item_count = 5\nitem_count = 8\nitem_count = 'eight'\n", output=False)
E["pc-trace"] = {"type": "table", "xp": 1, "blanks": {
    "v1": {"accept": ["5"]}, "t1": {"accept": ["int"]},
    "v2": {"accept": ["8"]}, "t2": {"accept": ["int"]},
    "v3": {"accept": ["'eight'", "\"eight\"", "eight"], "caseSensitive": True}, "t3": {"accept": ["str"]}}}
E["pc-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The third assignment, `item_count = 'eight'`, may be a design mistake: a count normally remains numeric, and code that expects a number in `item_count` may stop working. It is legal Python and produces no output.")}
pd_answer = "course_code = 'COMP 1001'\nstudent_count = 28\nMAX_CLASS_SIZE = 40\nprint(course_code, student_count, MAX_CLASS_SIZE)\n"
pd_check = '''user = {k: v for k, v in globals().items() if not k.startswith("__")}
texts = {k: v for k, v in user.items() if isinstance(v, str)}
whole = {k: v for k, v in user.items() if type(v) is int}
constants = {k: v for k, v in whole.items() if k == k.upper() and any(ch.isalpha() for ch in k)}
counts = {k: v for k, v in whole.items() if k not in constants}
assert texts, "Store the course code as text (a str value in quotes) in a variable."
assert counts, "Store the number of students as a whole number (an int, no quotes) in a variable."
assert constants, "Store the maximum class size using the constant convention: an ALL_CAPS name such as MAX_CLASS_SIZE."
lines = __stdout__.strip("\\n").split("\\n")
assert len(lines) == 1, "Display the three values on one line, with one print() call."
expected = {f"{c} {n} {m}" for c in texts.values() for n in counts.values() for m in constants.values()}
assert lines[0] in expected, "Print the course code, the number of students, and the maximum in that order, separated by spaces (one print with three values)."
'''
E["pd"] = {"type": "code", "xp": 10, "minLines": 6, "starter": "# Course information\n",
    "cases": [{"name": "Your values, in the requested order", "check": pd_check}],
    "answer": b64(pd_answer),
    "answerNote": "Output: COMP 1001 28 40. Other values are fine if the types, names, and display order meet the question."}
assert run(pd_answer) == "COMP 1001 28 40"
# ---------------------------------------------------------------- Putting It All Together
E["ex-w16"] = example("# Keep the room limit in one place for future updates.\nMAX_SEATS = 30\nroom_label = 'Room A'\nbooked = 24\n", output=False)
w17 = "# Keep the room limit in one place for future updates.\nMAX_SEATS = 30\nroom_label = 'Room A'\nbooked = 24\n\nprint('Capacity:', MAX_SEATS)\nprint(room_label, booked)\nbooked = booked + 1\nprint(room_label, booked)\n"
E["ex-w17"] = example(w17)
E["room-check"] = {"type": "table", "xp": 1, "blanks": {
    "l1": {"accept": ["Capacity: 30"], "caseSensitive": True, "placeholder": "line 1", "width": "14rem"},
    "l2": {"accept": ["Room A 0"], "caseSensitive": True, "placeholder": "line 2", "width": "14rem"},
    "l3": {"accept": ["Room A 1"], "caseSensitive": True, "placeholder": "line 3", "width": "14rem"},
    "t": {"accept": ["int"], "placeholder": "type"}}}
E["ex-w17-zero"] = example(w17.replace("booked = 24", "booked = 0"), output=False)
E["room-why"] = {"type": "short", "xp": 2, "answer": b64(
    "There is no later assignment to `MAX_SEATS`, so its value never changes. The capital letters alone do not prevent a change; a later `MAX_SEATS = …` statement would be accepted by Python.")}
# ---------------------------------------------------------------- Coding Practice
ca = "first = 3\nsecond = first + 2\nfirst = first + 1\nprint(first, second)\n"
E["ca"] = {"type": "code", "xp": 5, "minLines": 5, "starter": "first = 3\n# Add the remaining statements.\n",
    "cases": [
        {"name": "first = 3", "expected": run(ca)},
        {"name": "first = 0", "rewrite": [["first = 3", "first = 0"]], "expected": run(ca.replace("first = 3", "first = 0"))}],
    "answer": b64(ca)}
E["ca-trace"] = {"type": "table", "xp": 1, "blanks": {
    "f1": {"accept": ["3"]}, "s1": {"accept": ["not yet assigned", "not assigned", "unassigned", "undefined", "no value", "none", "-", "—", "not defined", "does not exist", "nothing"], "placeholder": "e.g. not yet assigned"},
    "f2": {"accept": ["3"]}, "s2": {"accept": ["5"]},
    "f3": {"accept": ["4"]}, "s3": {"accept": ["5"]}}}
cb = "first = 3\nfirst = first + 1\nsecond = first + 2\nprint(first, second)\n"
E["cb"] = {"type": "code", "xp": 5, "minLines": 5, "starter": "first = 3\n# Add the remaining statements.\n",
    "cases": [
        {"name": "first = 3", "expected": run(cb)},
        {"name": "first = 0", "rewrite": [["first = 3", "first = 0"]], "expected": run(cb.replace("first = 3", "first = 0"))}],
    "answer": b64(cb)}
E["cb-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Here `second` is assigned after `first` has already been increased, so it uses the updated value (4 + 2 = 6). In Coding Practice A, `second` used the original value of `first` (3 + 2 = 5). The order of statements changes which value is read.")}
E["cc-types"] = {"type": "table", "xp": 1, "blanks": {
    "t1": {"accept": ["int"]}, "t2": {"accept": ["float"]}, "t3": {"accept": ["str"]}, "t4": {"accept": ["str"]}, "t5": {"accept": ["str"]}}}
E["cc-same"] = {"type": "short", "xp": 1, "minChars": 5, "rows": 2, "placeholder": "Which two literals?", "answer": b64(
    "`'7'` and `\"7\"` contain the same text: single and double quotes both mark a string, and the quotes are not part of the value. `\"7.0\"` is different text because it includes a decimal point and a zero as characters.")}
cc = "print(type(7))\nprint(type(7.0))\nprint(type('7'))\nprint(type(\"7\"))\nprint(type(\"7.0\"))\n"
E["cc"] = {"type": "code", "xp": 5, "minLines": 6, "starter": "# Display the five types in the requested order.\n",
    "cases": [{"name": "Program output", "expected": run(cc)}], "answer": b64(cc)}
E["ex-w18"] = example("m = 40\nn = 18\nt = 'Lab A'\nprint(t, n, m)\n")
cd = "# Keep the room limit in one place for future updates.\nMAX_SEATS = 40\nbooked = 18\nroom_label = 'Lab A'\nprint(room_label, booked, MAX_SEATS)\n"
cd_check = '''import re
user = {k: v for k, v in globals().items() if not k.startswith("__")}
for short in ("m", "n", "t"):
    assert short not in user, f"The name {short} is still used. Replace every single-letter name with a meaningful one."
constants = {k: v for k, v in user.items() if type(v) is int and k == k.upper() and any(ch.isalpha() for ch in k)}
assert constants, "Store the fixed room capacity under an ALL_CAPS name (the constant convention), e.g. MAX_SEATS."
assert any(v == 40 for v in constants.values()) or any(v == 40 for v in user.values()), "Keep the capacity value 40."
counts = {k: v for k, v in user.items() if type(v) is int and k not in constants}
assert counts, "Store the booking count under a lowercase descriptive name (it is a value that can change, not a constant)."
assert any(isinstance(v, str) for v in user.values()), "Store the room label as text under a descriptive name."
code_lines = [line for line in __source__.split("\\n") if line.strip()]
assert any(re.match(r"\\s*#", line) or "#" in line.split("'")[0].split('"')[0] for line in code_lines), "Add one useful comment (a line or note starting with #) that explains a choice."
for k in user:
    assert len(k) > 1, f"The name {k} is too short to be meaningful."
'''
E["cd"] = {"type": "code", "xp": 10, "minLines": 7, "starter": "# Write your revised program below.\n",
    "check": cd_check,
    "cases": [
        {"name": "18 bookings", "expected": run(cd)},
        {"name": "0 bookings", "rewrite": [["= 18", "= 0"]], "expected": run(cd.replace("= 18", "= 0"))}],
    "answer": b64(cd),
    "answerNote": "Other meaningful names and a useful reason-based comment are acceptable."}
E["cd-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Descriptive names (`room_label`, `booked`, `MAX_SEATS`) explain what each value means without a reader having to guess. "
    "Capital letters distinguish the intended fixed capacity from a count that may change. "
    "The comment explains why the setting is kept in one place, so a future change is made once and stays consistent.")}

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-04",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 4 Workbook",
    "subtitle": "Variables, types, and assignment",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-04/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
