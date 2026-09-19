"""Build workbooks/lecture-08/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-08/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-08
"""
import base64, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Mirrors the grader: input() writes its prompt to stdout and the typed
# answer is not echoed, so expected output for input() programs includes
# the prompt text.
HARNESS = """import builtins, json, sys
code, answers = json.load(sys.stdin)
def _input(prompt=''):
    sys.stdout.write(str(prompt))
    return answers.pop(0)
builtins.input = _input
exec(compile(code, 'main.py', 'exec'), {'__name__': '__main__'})
"""

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=()):
    p = subprocess.run([sys.executable, "-c", HARNESS], input=json.dumps([code, list(inputs)]), capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n")

def example(code, output=True, **kw):
    spec = {"type": "example", "code": code.rstrip("\n"), **kw}
    if output:
        spec["output"] = run(code)
    return spec

def case(name, code, inputs=(), rewrite=None, check=None):
    """A case whose expected output comes from running `code` (the model answer)."""
    source = code
    for old, new in rewrite or []:
        assert old in source, old
        source = source.replace(old, new)
    c = {"name": name, "expected": run(source, inputs)}
    if inputs:
        c["inputs"] = list(inputs)
    if rewrite:
        c["rewrite"] = rewrite
    if check:
        c["check"] = check
    return c

TRUE = {"accept": ["True"], "caseSensitive": True, "placeholder": "True / False", "width": "8rem"}
FALSE = {"accept": ["False"], "caseSensitive": True, "placeholder": "True / False", "width": "8rem"}
IF = {"accept": ["if", "if branch", "the if branch"], "placeholder": "if / else", "width": "7rem", "show": "if"}
ELSE = {"accept": ["else", "else branch", "the else branch"], "placeholder": "if / else", "width": "7rem", "show": "else"}
INSIDE = {"accept": ["inside"], "placeholder": "inside / outside", "width": "9rem"}
OUTSIDE = {"accept": ["outside"], "placeholder": "inside / outside", "width": "9rem"}

E = {}

# ---------------------------------------------------------------- Section 1
E["ex-w01"] = example("temperature = 16\n\nif temperature < 18:\n    print('Bring a jacket.')\n\nprint('Have a good day!')\n")
E["cp1"] = {"type": "table", "xp": 1, "blanks": {
    "skipped": {"accept": ["Bring a jacket.", "Bring a jacket", "print('Bring a jacket.')", "the first line", "first line", "line 1", "1"], "caseSensitive": True, "placeholder": "the line of output", "width": "14rem", "show": "Bring a jacket."},
    "appears": {"accept": ["Have a good day!", "Have a good day", "print('Have a good day!')", "the second line", "second line", "line 2", "2"], "caseSensitive": True, "placeholder": "the line of output", "width": "14rem", "show": "Have a good day!"}}}
E["cp1-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The line `Bring a jacket.` is skipped because `22 < 18` is `False`, so Python skips the indented body. "
    "The line `Have a good day!` still appears because its `print` call is outside the `if` block, so it always runs.")}
# ---------------------------------------------------------------- Section 2
E["cp2-question"] = {"type": "short", "xp": 2, "minChars": 10, "rows": 2, "placeholder": "Is the …?", "answer": b64(
    "Ask, “Is the visitor younger than 18?” In Python the condition is `age < 18`.")}
below = [str(n) for n in range(0, 18)]
above = [str(n) for n in range(19, 121)]
E["cp2-ages"] = {"type": "table", "xp": 1, "blanks": {
    "below": {"accept": below, "placeholder": "an age", "width": "6rem", "show": "17"},
    "at": {"accept": ["18"], "placeholder": "an age", "width": "6rem"},
    "above": {"accept": above, "placeholder": "an age", "width": "6rem", "show": "19"}}}
# ---------------------------------------------------------------- Section 3
E["ex-w02"] = example("balance = 35\n\nif balance < 50:\n    print('Low balance')\n\nprint('Balance checked')\n")
E["cp3"] = {"type": "table", "xp": 1, "blanks": {
    "kw": {"accept": ["if"], "caseSensitive": True, "placeholder": "keyword", "width": "8rem"},
    "cond": {"accept": ["score >= 60", "score>=60"], "caseSensitive": True, "placeholder": "condition", "width": "10rem", "show": "score >= 60"},
    "colon": {"accept": [":"], "placeholder": "punctuation", "width": "8rem"},
    "body": {"accept": ["print('Pass')", "print(\"Pass\")", "print('Pass') (indented)", "the indented print call", "the indented line", "indented print"], "caseSensitive": True, "placeholder": "the statement", "width": "12rem", "show": "print('Pass')"},
    "printed": {"accept": ["nothing", "nothing is printed", "nothing at all", "no output", "none", "it prints nothing", "no line", "-", "—"], "placeholder": "what is printed?", "width": "12rem", "show": "nothing"}}}
# ---------------------------------------------------------------- Section 4
E["ex-w03"] = example("total = 72\n\nif total >= 50:\n    shipping = 0\n    print('Free shipping')\n\nprint('Order checked')\n")
E["cp4"] = {"type": "table", "xp": 1, "blanks": {
    "l1": INSIDE, "l2": INSIDE, "l3": OUTSIDE}}
E["cp4-always"] = {"type": "table", "xp": 1, "blanks": {"always": {
    "accept": ["print('Record complete')", "print(\"Record complete\")", "Record complete", "the last print", "the final print", "the last line", "the final line", "line 5"],
    "caseSensitive": True, "placeholder": "the statement", "width": "16rem", "show": "print('Record complete')"}}}
# ---------------------------------------------------------------- Section 5
w04 = "total = 42\n\nif total >= 50:\n    shipping = 0\nelse:\n    shipping = 8\n\nprint('Shipping:', shipping)\n"
E["ex-w04"] = example(w04)
E["ex-w05"] = example(w04.replace("total = 42", "total = 50"))
E["cp5"] = {"type": "table", "xp": 1, "blanks": {
    "c49": FALSE, "b49": ELSE, "s49": {"accept": ["8"], "width": "5rem"},
    "c50": TRUE, "b50": IF, "s50": {"accept": ["0"], "width": "5rem"},
    "c51": TRUE, "b51": IF, "s51": {"accept": ["0"], "width": "5rem"}}}
for t in ("49", "50", "51"):
    assert run(w04.replace("total = 42", f"total = {t}")) == "Shipping: " + E["cp5"]["blanks"]["s" + t]["accept"][0]
# ---------------------------------------------------------------- Section 6
E["cp6-path"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "Read 64, test `total >= 50`, take the Yes path, assign `shipping = 0`, then print the shipping charge.")}
E["cp6-value"] = {"type": "table", "xp": 1, "blanks": {"value": {"accept": ["0"], "placeholder": "value", "width": "6rem"}}}
E["cp6-rejoin"] = {"type": "short", "xp": 2, "minChars": 10, "rows": 2, "answer": b64(
    "The Yes and No paths rejoin immediately before the shared output step, “Print the shipping charge.”")}
# ---------------------------------------------------------------- Section 7
E["ex-w06"] = example("total = 38\n\nif total >= 50:\n    shipping = 0\nelse:\n    shipping = 8\n\nfinal_total = total + shipping\nprint('Final total:', final_total)\n")
cp7 = "balance = -20\n\nif balance < 0:\n    status = 'Overdrawn'\nelse:\n    status = 'Available'\n\nprint('Status:', status)\n"
E["cp7-fix"] = {"type": "code", "xp": 2, "minLines": 8,
    "starter": "balance = -20\n\nif balance < 0:\n    status = 'Overdrawn'\n    print('Status:', status)\nelse:\n    status = 'Available'\n    print('Status:', status)\n",
    "cases": [case("balance = -20", cp7), case("balance = 120", cp7, rewrite=[["balance = -20", "balance = 120"]])],
    "check": 'assert __source__.count("print(") == 1, "The print call is still duplicated. Keep exactly one print, written once after the decision."\n'
             'assert any(line.startswith("print(") for line in __source__.split("\\n")), "Put the single print at the left margin, after the if/else, so it runs in both cases."',
    "answer": b64(cp7)}
# ---------------------------------------------------------------- Section 8
E["cp8"] = {"type": "table", "xp": 1, "blanks": {
    "late": {"accept": ["days > 0", "days>0", "0 < days", "0<days", "days >= 1", "days>=1"], "caseSensitive": True, "placeholder": "condition", "width": "10rem", "show": "days > 0"},
    "full": {"accept": ["people >= 30", "people>=30", "30 <= people", "30<=people", "people > 29", "people>29"], "caseSensitive": True, "placeholder": "condition", "width": "10rem", "show": "people >= 30"},
    "boundary": {"accept": ["30"], "placeholder": "value", "width": "6rem"}}}
# ---------------------------------------------------------------- Section 9
E["ex-w07"] = example("if total >= 50\n    shipping = 0\n", output=False)
E["ex-w08"] = example("if total >= 50:\nshipping = 0\n", output=False)
cp9 = "age = 15\n\nif age < 18:\n    print('Reduced price')\n"
E["cp9-fix"] = {"type": "code", "xp": 2, "minLines": 4,
    "starter": "age = 15\n\nif age < 18\nprint('Reduced price')\n",
    "cases": [case("age = 15", cp9), case("age = 30 (nothing printed)", cp9, rewrite=[["age = 15", "age = 30"]])],
    "check": 'assert "age < 18" in __source__ or "age<18" in __source__ or "18 > age" in __source__, "Keep the condition age < 18."',
    "answer": b64(cp9)}
# ---------------------------------------------------------------- Final review
E["fr1"] = {"type": "table", "xp": 1, "blanks": {
    "v1": {"accept": ["True", "False"], "caseSensitive": True, "placeholder": "value", "width": "7rem", "show": "True"},
    "v2": {"accept": ["False", "True"], "caseSensitive": True, "placeholder": "value", "width": "7rem", "show": "False"}}}
E["fr2"] = {"type": "short", "xp": 2, "answer": b64(
    "The keyword `if`, a condition, a colon at the end of the header, and an indented body.")}
E["fr3"] = {"type": "short", "xp": 2, "answer": b64(
    "Python uses indentation. Statements at the same indentation level belong to the same block.")}
E["fr4"] = {"type": "short", "xp": 2, "answer": b64(
    "The `else` block runs when the matching `if` condition is `False`.")}
E["fr5"] = {"type": "short", "xp": 2, "answer": b64(
    "Both branches contain behaviour that must be checked. The boundary is where operators such as `>` and `>=` differ, so it often reveals an incorrect condition.")}
w09 = "score = 60\nif score >= 60:\n    result = 'Pass'\nelse:\n    result = 'Try again'\nprint(result)\n"
E["ex-w09"] = example(w09, output=False)
E["fr6"] = {"type": "table", "xp": 1, "blanks": {
    "cond": TRUE, "branch": IF,
    "out": {"accept": ["Pass"], "caseSensitive": True, "placeholder": "output", "width": "8rem"}}}
assert run(w09) == "Pass"
# ---------------------------------------------------------------- Additional practice
pa = "if age < 18:\n    price = 8\nelse:\n    price = 12\n\nprint('Price:', price)\n"
E["pa"] = {"type": "table", "xp": 1, "blanks": {
    "c15": TRUE, "b15": IF, "p15": {"accept": ["8"], "width": "5rem"}, "o15": {"accept": ["Price: 8"], "caseSensitive": True, "placeholder": "output", "width": "8rem"},
    "c21": FALSE, "b21": ELSE, "p21": {"accept": ["12"], "width": "5rem"}, "o21": {"accept": ["Price: 12"], "caseSensitive": True, "placeholder": "output", "width": "8rem"}}}
assert run("age = 15\n" + pa) == "Price: 8" and run("age = 21\n" + pa) == "Price: 12"
pb = "fuel = 5\n\nif fuel < 10:\n    print('Low fuel')\n"
E["pb"] = {"type": "code", "xp": 2, "minLines": 4,
    "starter": "fuel = 5\n\n# Write the if statement below.\n",
    "cases": [case("fuel = 5", pb), case("fuel = 10 (nothing printed)", pb, rewrite=[["fuel = 5", "fuel = 10"]]), case("fuel = 25 (nothing printed)", pb, rewrite=[["fuel = 5", "fuel = 25"]])],
    "answer": b64(pb)}
pc = "mark = 65\n\nif mark >= 50:\n    result = 'Pass'\nelse:\n    result = 'Not yet'\n\nprint(result)\n"
E["pc"] = {"type": "code", "xp": 5, "minLines": 7,
    "starter": "mark = 65\n\n# Store 'Pass' or 'Not yet' in result, then print result once.\n",
    "cases": [case("mark = 65", pc), case("mark = 50", pc, rewrite=[["mark = 65", "mark = 50"]]), case("mark = 49", pc, rewrite=[["mark = 65", "mark = 49"]])],
    "check": 'assert "result" in globals(), "Store the message in a variable named result."\n'
             'assert __source__.count("print(") == 1, "Print result exactly once, after the decision."',
    "answer": b64(pc)}
E["pd-cases"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "Case 1: the item is late, so the fee is 5 dollars. Case 2: the item is not late, so the fee is 0 dollars.")}
E["pd-question"] = {"type": "short", "xp": 2, "minChars": 10, "rows": 2, "placeholder": "Is …?", "answer": b64(
    "Ask, “Is `days_late > 0`?”")}
E["pd-flow"] = {"type": "short", "xp": 2, "minChars": 30, "rows": 4, "placeholder": "Start with the input step, then the diamond, then …", "answer": b64(
    "Read `days_late`. Diamond: `days_late > 0`? Yes path: `fee = 5`. No path: `fee = 0`. Both paths rejoin at one shared step: print the fee.")}
pd = "days_late = int(input('Days late: '))\n\nif days_late > 0:\n    fee = 5\nelse:\n    fee = 0\n\nprint('Fee:', fee)\n"
E["pd"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "# Read days_late, choose the fee, then print it once.\n",
    "cases": [case("3 days late", pd, inputs=["3"]), case("returned on time (0 days)", pd, inputs=["0"]), case("1 day late", pd, inputs=["1"])],
    "answer": b64(pd)}
pe = "age = 16\n\nif age >= 16:\n    print('Access allowed')\nelse:\n    print('Access denied')\n"
E["pe"] = {"type": "code", "xp": 2, "minLines": 6,
    "starter": "age = 16\n\nif age > 16\nprint('Access allowed')\n    else:\n        print('Access denied')\n",
    "cases": [case("age = 16 (the boundary)", pe), case("age = 15", pe, rewrite=[["age = 16", "age = 15"]]), case("age = 40", pe, rewrite=[["age = 16", "age = 40"]])],
    "answer": b64(pe)}
# ---------------------------------------------------------------- Putting It All Together
w10 = ("order_total = float(input('Order total: $'))\n\nif order_total >= 50:\n    shipping = 0\nelse:\n    shipping = 8\n\n"
       "final_total = order_total + shipping\nprint(f'Shipping: ${shipping:.2f}')\nprint(f'Final total: ${final_total:.2f}')\n")
E["ex-w10"] = example(w10, output=False)
assert run(w10, ["38"]) == "Order total: $Shipping: $8.00\nFinal total: $46.00"
assert run(w10, ["50"]) == "Order total: $Shipping: $0.00\nFinal total: $50.00"
assert run(w10, ["72.50"]) == "Order total: $Shipping: $0.00\nFinal total: $72.50"
E["it-trace"] = {"type": "table", "xp": 1, "blanks": {
    "cond": TRUE, "branch": IF,
    "ship": {"accept": ["0", "0.0", "0.00"], "placeholder": "value", "width": "7rem"},
    "final": {"accept": ["72.5", "72.50"], "placeholder": "value", "width": "7rem"}}}
E["it-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The calculation is shared by both cases, so it is written once after the branches instead of being repeated in each. It also needs the `shipping` value that the decision chooses, so it must come after the decision.")}
# ---------------------------------------------------------------- Coding Practice
ca = "number = float(input('Number: '))\n\nif number < 0:\n    magnitude = -number\nelse:\n    magnitude = number\n\nprint('Original:', number)\nprint('Magnitude:', magnitude)\n"
E["ca"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "# Ask for a number, choose the magnitude with one if/else, then print both.\n",
    "cases": [case("Number: -7.5", ca, inputs=["-7.5"]), case("Number: 4", ca, inputs=["4"]), case("Number: 0 (the boundary)", ca, inputs=["0"])],
    "check": 'assert "abs(" not in __source__, "Do not call abs(). Choose the magnitude with an if/else statement."\n'
             'assert "else" in __source__, "Use one if/else statement: one branch keeps the number, the other stores its opposite."',
    "answer": b64(ca)}
cb = ("name = input('Employee name: ')\nwage = float(input('Hourly wage: $'))\nhours = float(input('Hours worked: '))\n\n"
      "if hours > 40:\n    regular_pay = 40 * wage\n    overtime_hours = hours - 40\n    overtime_pay = overtime_hours * wage * 1.5\n    pay = regular_pay + overtime_pay\nelse:\n    pay = hours * wage\n\n"
      "print('Employee:', name)\nprint(f'Pay: ${pay:.2f}')\n")
cb_check = '''lines = [line.strip() for line in __source__.split("\\n")]
assert sum(line.startswith("if ") for line in lines) == 1, "Use exactly one if statement."
assert sum(line == "else:" for line in lines) == 1, "Use exactly one else branch."
assert not any(line.startswith("elif") for line in lines), "This task needs only a two-way decision: no elif."
assert any(line.startswith("print(") for line in __source__.split("\\n")), "Put the final output after the branches, at the left margin, so it runs in both cases."
'''
E["cb"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": "# Ask for the name, wage, and hours; choose the pay with one if/else; print after the branches.\n",
    "cases": [case("Sam, $20, 45 hours", cb, inputs=["Sam", "20", "45"]), case("Lee, $18, 40 hours (the boundary)", cb, inputs=["Lee", "18", "40"]), case("Ana, $15, 41 hours", cb, inputs=["Ana", "15", "41"])],
    "check": cb_check,
    "answer": b64(cb)}
assert run(cb, ["Sam", "20", "45"]).endswith("Pay: $950.00")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-08",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 8 Workbook",
    "subtitle": "Problem solving with decisions: the if statement",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-08/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
