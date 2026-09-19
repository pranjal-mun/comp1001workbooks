"""Build workbooks/lecture-05/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-05/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-05
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

def rewritten(code, *pairs):
    for old, new in pairs:
        assert old in code, old
        code = code.replace(old, new)
    return code

def blanks(**keys):
    """{name: accept-list-or-string} -> table blanks; strings become one-item lists."""
    out = {}
    for name, accept in keys.items():
        out[name] = {"accept": accept if isinstance(accept, list) else [accept]}
    return out

# Checks shared by the module exercises: the course form is `import math`
# followed by qualified names.
QUALIFIED_MATH = '''import re
lines = [l.strip() for l in __source__.split("\\n")]
assert "import math" in lines, "Use the preferred course form: a line `import math` on its own."
assert not any(l.startswith("from math import") for l in lines), "Use `import math`, not `from math import ...`, so the module name stays visible."
'''

E = {}

# ---------------------------------------------------------------- Section 1
E["ex-w01"] = example("print(8 + 5)\nprint(8 * 5)\nprint(2 ** 5)\n")
E["cp1"] = {"type": "table", "xp": 1, "blanks": blanks(
    v1="16", v2="8", v3="48", v4="27")}
E["cp1-power"] = {"type": "table", "xp": 1, "blanks": {"op": {
    "accept": ["**"], "placeholder": "operator", "width": "8rem"}}}

# ---------------------------------------------------------------- Section 2
E["ex-w02"] = example("print(17 / 5)\nprint(17 // 5)\nprint(17 % 5)\n")
E["ex-w03"] = example("total_minutes = 137\nhours = total_minutes // 60\nminutes = total_minutes % 60\n\nprint(hours)\nprint(minutes)\n")
E["cp2"] = {"type": "table", "xp": 1, "blanks": {
    "e1": {"accept": ["53 // 8", "53//8"], "placeholder": "expression", "width": "9rem"},
    "v1": {"accept": ["6"], "placeholder": "value", "width": "5rem"},
    "e2": {"accept": ["53 % 8", "53%8"], "placeholder": "expression", "width": "9rem"},
    "v2": {"accept": ["5"], "placeholder": "value", "width": "5rem"}}}
E["cp2-check"] = example("print(53 // 8)\nprint(53 % 8)\n", output=False)

# ---------------------------------------------------------------- Section 3
E["ex-w04"] = example("print(2 + 3 * 4)\nprint((2 + 3) * 4)\nprint(2 ** 3 * 4)\n")
E["cp3"] = {"type": "table", "xp": 1, "blanks": blanks(
    v1="4", v2="24", v3="8.0", v4="3.6")}
cp3_fix = "print((4 + 6) / 2)\n"
E["cp3-fix"] = {"type": "code", "xp": 2, "minLines": 2, "maxLines": 6,
    "starter": "print(4 + 6 / 2)\n",
    "cases": [{"name": "Program output", "expected": run(cp3_fix)}],
    "check": '''src = __source__.replace(" ", "")
assert "(4+6)" in src, "Group the addition with parentheses so it happens before the division: (4 + 6)."
assert "/2" in src, "Keep the division by 2."
assert "5.0" not in src, "Let Python compute the value; do not print 5.0 directly."''',
    "answer": b64(cp3_fix)}

# ---------------------------------------------------------------- Section 4
E["ex-w05"] = example("print(3 * 2)\nprint(3 * 2.0)\nprint(4 / 2)\n")
E["cp4"] = {"type": "table", "xp": 1, "blanks": {
    "v1": {"accept": ["7"], "placeholder": "value"}, "t1": {"accept": ["int"], "placeholder": "type"},
    "v2": {"accept": ["7.0"], "placeholder": "value"}, "t2": {"accept": ["float"], "placeholder": "type"},
    "v3": {"accept": ["3.0"], "placeholder": "value"}, "t3": {"accept": ["float"], "placeholder": "type"},
    "v4": {"accept": ["3"], "placeholder": "value"}, "t4": {"accept": ["int"], "placeholder": "type"}}}
E["cp4-check"] = example("print(5 + 2, type(5 + 2))\nprint(5 + 2.0, type(5 + 2.0))\nprint(9 / 3, type(9 / 3))\nprint(9 // 3, type(9 // 3))\n", output=False)

# ---------------------------------------------------------------- Section 5
E["ex-w06"] = example("print(int('42'))\nprint(float('3.5'))\nprint(str(42))\nprint(int(3.9))\n")
E["ex-w07"] = example("print(round(3.9))\nprint(round(3.14159, 2))\n")
E["cp5"] = {"type": "table", "xp": 1, "blanks": blanks(
    v1="8", v2="9", v3="8.76", v4="8.75")}
E["cp5-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Truncating (`int(8.75)`) discards the fractional part, moving toward zero, so the result is 8. "
    "Rounding (`round(8.75)`) chooses the nearest value at the requested precision, so the result is 9; "
    "exactly halfway values go to the even choice.")}

# ---------------------------------------------------------------- Section 6
E["ex-w08"] = example("result = 0.1 + 0.2\nprint(result)\n")
E["cp6-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Floats are stored in binary. Many decimal fractions (such as 0.1) need infinitely many binary digits, "
    "but a float has limited storage, so the stored value is the nearest representable approximation.")}
E["cp6-round"] = {"type": "short", "xp": 2, "answer": b64(
    "No. `round` produces a new rounded result for display. It does not change how the earlier values were stored "
    "and does not undo their approximation errors.")}

# ---------------------------------------------------------------- Section 7
E["ex-w09"] = example("import math\n\nprint(math.sqrt(81))\nprint(math.pi)\n")
E["ex-w10"] = example("from math import sqrt\nprint(sqrt(81))\n")
cp7 = "import math\nanswer = math.sqrt(49)\nprint(answer)\n"
E["cp7"] = {"type": "code", "xp": 2, "minLines": 3, "maxLines": 6,
    "starter": "import __________\nanswer = __________.sqrt(49)\nprint(answer)\n",
    "cases": [{"name": "Program output", "expected": run(cp7)}],
    "check": QUALIFIED_MATH + 'assert "math.sqrt(49)" in __source__.replace(" ", ""), "Call the function through its module: math.sqrt(49)."',
    "answer": b64(cp7)}
E["cp7-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The prefix `math.` shows the reader where `sqrt` comes from: it is supplied by the math module, not defined in this program. "
    "A reader can look up the function's source, and an unrelated local name `sqrt` cannot replace `math.sqrt`.")}

# ---------------------------------------------------------------- Section 8
E["cp8"] = {"type": "table", "xp": 1, "blanks": {
    "h": {"accept": ["3"], "placeholder": "value", "width": "5rem"},
    "he": {"accept": ["185 // 60", "185//60"], "placeholder": "expression", "width": "9rem"},
    "m": {"accept": ["5"], "placeholder": "value", "width": "5rem"},
    "me": {"accept": ["185 % 60", "185%60"], "placeholder": "expression", "width": "9rem"}}}

# ---------------------------------------------------------------- Final review
fr = "import math\n\ntotal_seconds = 3675\nhours = total_seconds // 3600\nremaining = total_seconds % 3600\nminutes = remaining // 60\n\nprint(hours)\nprint(minutes)\nprint(round(math.sqrt(50), 2))\n"
E["ex-w11"] = example(fr, output=False)
fr_lines = run(fr).split("\n")
assert fr_lines == ["1", "1", "7.07"], fr_lines
E["fr1"] = {"type": "table", "xp": 1, "blanks": blanks(l1=fr_lines[0], l2=fr_lines[1], l3=fr_lines[2])}
E["fr2"] = {"type": "short", "xp": 2, "answer": b64(
    "Floor division counts complete units: `total_seconds // 3600` is the number of complete hours and "
    "`remaining // 60` the number of complete minutes. Any fraction of an hour or minute is discarded, which is what a clock display needs.")}
E["fr3"] = {"type": "short", "xp": 2, "answer": b64(
    "`total_seconds % 3600` keeps the seconds left over after the complete hours are removed: 75 seconds here. "
    "That remainder is then used to find the complete minutes.")}
E["fr4"] = {"type": "table", "xp": 1, "blanks": {"name": {
    "accept": ["math", "math.", "math.sqrt", "import math"], "placeholder": "name", "width": "10rem"}}}

# ---------------------------------------------------------------- Additional practice
E["pa"] = {"type": "table", "xp": 1, "blanks": blanks(
    v1="13", v2="343", v3="4", v4="5", v5="2.5")}
E["pa-check"] = example("print(5 + 2 ** 3)\nprint((5 + 2) ** 3)\nprint(29 // 6)\nprint(29 % 6)\nprint(10 / 4)\n", output=False)
E["pb"] = {"type": "table", "xp": 1, "blanks": {
    "o1": {"accept": ["/"], "placeholder": "operator", "width": "6rem"},
    "o2": {"accept": ["//"], "placeholder": "operator", "width": "6rem"},
    "o3": {"accept": ["%"], "placeholder": "operator", "width": "6rem"}}}
E["pb-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Use `/` to divide the sum by 3 without discarding a fraction. Use `//` to count whole teams of four. "
    "Use `%` to find the people left over after the complete teams.")}
E["pc"] = {"type": "table", "xp": 1, "blanks": blanks(
    v1="12", v2="13", v3="12.99", v4="12.99")}
E["pc-why"] = {"type": "short", "xp": 2, "answer": b64(
    "`int(12.99)` truncates toward zero, giving 12. `round(12.99)` rounds to the nearest integer, 13. "
    "`round(12.994, 2)` rounds to two decimal places, 12.99. `float('12.99')` converts the text to the float 12.99.")}
pd = "import math\nanswer = math.sqrt(144)\nprint(answer)\n"
E["pd"] = {"type": "code", "xp": 5, "minLines": 4,
    "starter": "# Write your program here.\n",
    "cases": [{"name": "Program output", "expected": run(pd)}],
    "check": QUALIFIED_MATH + 'assert "math.sqrt(144)" in __source__.replace(" ", ""), "Compute the square root with math.sqrt(144)."',
    "answer": b64(pd)}

# ---------------------------------------------------------------- Putting it all together
E["ex-w12"] = example("duration_text = '185'\ntotal_minutes = int(duration_text)\nhours = total_minutes // 60\nminutes = total_minutes % 60\nprint(hours)\nprint(minutes)\n")
E["ex-w13"] = example("total_minutes = 185\nelapsed_hours = total_minutes / 60\nprint(elapsed_hours)\n")
E["ex-w14"] = example("import math\nx = 6\ny = 8\ndistance = math.sqrt(x ** 2 + y ** 2)\nprint(distance)\n")
trip = ("import math\nduration_text = '185'\nx = 6\ny = 8\ntotal_minutes = int(duration_text)\nhours = total_minutes // 60\n"
        "minutes = total_minutes % 60\ndistance = math.sqrt(x ** 2 + y ** 2)\nspeed = distance / (total_minutes / 60)\n"
        "print(hours)\nprint(minutes)\nprint(round(speed, 2))\n")
trip_case2 = [["duration_text = '185'", "duration_text = '60'"], ["x = 6", "x = 0"]]
E["trip"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": "duration_text = '185'\nx = 6\ny = 8\n# Complete the program.\n",
    "cases": [
        {"name": "'185', 6, 8", "expected": run(trip)},
        {"name": "'60', 0, 8", "rewrite": trip_case2, "expected": run(rewritten(trip, *trip_case2))}],
    "check": QUALIFIED_MATH + '''assert "int(duration_text)" in __source__.replace(" ", ""), "Convert the duration text with int(duration_text) before doing arithmetic on it."
assert "math.sqrt" in __source__, "Use math.sqrt for the distance."''',
    "answer": b64(trip)}

# ---------------------------------------------------------------- Coding practice
c1_values = "u = 3\nt = 2\na = 4\np = 100\nr = 10\nn = 2\nx = 3\ny = 4\nm = 1\n"
c1 = "import math\n" + c1_values + "s = u * t + a * t ** 2 / 2\nb = p * (1 + r / 100) ** n\nz = 4 * math.pi ** 2 * x ** 3 / (y ** 2 * (m + n))\nd = math.sqrt(x ** 2 + y ** 2)\n"
c1_check = QUALIFIED_MATH + '''import math as _m
for _name in ("s", "b", "z", "d"):
    assert _name in globals(), f"Assign a value to {_name}."
assert _m.isclose(s, u * t + a * t ** 2 / 2), "s should be u*t + a*t^2/2: multiply a by t squared, then divide that product by 2."
assert _m.isclose(b, p * (1 + r / 100) ** n), "b should be p(1 + r/100)^n: raise the parenthesised sum to the power n, then multiply by p."
assert _m.isclose(z, 4 * _m.pi ** 2 * x ** 3 / (y ** 2 * (m + n))), "z should be 4*pi^2*x^3 divided by the whole denominator y^2*(m + n); parenthesise the denominator."
assert _m.isclose(d, _m.sqrt(x ** 2 + y ** 2)), "d should be the square root of x^2 + y^2, using math.sqrt."
assert "math.pi" in __source__, "Use math.pi for pi."'''
c1_case2 = [["u = 3", "u = 5"], ["x = 3", "x = 6"], ["y = 4", "y = 8"]]
E["c1"] = {"type": "code", "xp": 10, "minLines": 14,
    "starter": "# Sample values; keep these lines. Add the import and the four assignments below.\n" + c1_values,
    "cases": [{"name": "sample values"}, {"name": "other values", "rewrite": c1_case2}],
    "check": c1_check,
    "answer": b64(c1),
    "answerNote": "Nothing is printed; Check verifies the four assigned values against the formulas."}
E["c2"] = {"type": "short", "xp": 2, "rows": 5, "minChars": 30, "placeholder": "Write each formula in mathematical notation; describe fraction bars, powers, and roots in words if needed…", "answer": b64(
    "area = π · radius² / 2 (the whole product π·radius² is over 2).\n\n"
    "length = √(a² + 4b²) (the square root covers the whole sum).\n\n"
    "scale = mass × ( √(1 + rate) / √(1 − rate) − 1 ). The final subtraction of 1 is outside the fraction but inside the multiplication by mass.")}
E["c3"] = {"type": "table", "xp": 1, "blanks": blanks(
    v1="9.0", v2="7", v3="9.5", v4="-3", v5="3.0")}
E["c3-check"] = example("import math\nx = 3.0\ny = -2.0\nm = 23\nn = 5\nprint(x + n * y - (x + n) * y)\nprint(m // n + m % n)\nprint(4 * x - n / 2)\nprint(2 - (2 - (2 - n)))\nprint(math.sqrt(math.sqrt(81)))\n", output=False)
E["c4"] = {"type": "table", "xp": 1, "blanks": blanks(
    v1="9", v2="1", v3="27", v4="27.5", v5="27", v6="28")}
E["c4-check"] = example("n = 27\nm = 28\nprint(n // 10 + n % 10)\nprint(n % 2 + m % 2)\nprint((m + n) // 2)\nprint((m + n) / 2)\nprint(int((m + n) / 2))\nprint(round((m + n) / 2))\n", output=False)
E["c4-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Floor division of two integers returns an `int` (27), while true division always returns a `float` (27.5). "
    "The average is exactly halfway: `int` truncates it to 27, and `round` chooses the even integer, 28.")}
E["ex-w16"] = example("measured = 1.2\nreference = 1.0\ndifference = measured - reference\nprint(difference)\n")
E["c5-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The float representing 1.2 is only an approximation, because 1.2 has no exact finite binary representation. "
    "Subtracting 1.0 exposes that small error in the printed digits.")}
c5 = "measured = 1.2\nreference = 1.0\ndifference = measured - reference\nprint(round(difference, 2))\n"
E["c5"] = {"type": "code", "xp": 5, "minLines": 5,
    "starter": "measured = 1.2\nreference = 1.0\n# Complete the revised program.\n",
    "cases": [{"name": "Program output", "expected": run(c5)}],
    "check": '''assert "round(" in __source__, "Use round(..., 2) on the difference before printing it."
assert "0.2" not in __source__.replace("1.2", ""), "Compute the difference with subtraction; do not print 0.2 directly."''',
    "answer": b64(c5)}
E["c5-exact"] = {"type": "short", "xp": 2, "answer": b64(
    "No. Rounding improves the displayed result, but `measured` and `reference` are still stored as the same approximate floats. "
    "Rounding cannot make earlier values exact.")}
c6 = "import math\nwidth = 9\nheight = 12\nperimeter = 2 * (width + height)\ndiagonal = math.sqrt(width ** 2 + height ** 2)\nprint(perimeter)\nprint(diagonal)\n"
E["c6"] = {"type": "code", "xp": 5, "minLines": 7,
    "starter": "width = 9\nheight = 12\n# Complete the program.\n",
    "cases": [
        {"name": "(9, 12)", "expected": run(c6)},
        {"name": "(5, 12)", "rewrite": [["width = 9", "width = 5"]], "expected": run(rewritten(c6, ("width = 9", "width = 5")))}],
    "check": QUALIFIED_MATH + 'assert "math.sqrt" in __source__, "Use math.sqrt for the diagonal."',
    "answer": b64(c6)}
E["c7-hand"] = {"type": "table", "xp": 1, "blanks": {
    "v1": {"accept": ["19", "19π", "19 π", "19pi", "19 pi", "19*pi", "19 * pi"], "placeholder": "multiple of π", "show": "19π"},
    "v2": {"accept": ["36", "36π", "36 π", "36pi", "36 pi", "36*pi", "36 * pi"], "placeholder": "multiple of π", "show": "36π"},
    "v3": {"accept": ["13", "13π", "13 π", "13pi", "13 pi", "13*pi", "13 * pi"], "placeholder": "multiple of π", "show": "13π"},
    "v4": {"accept": ["68", "68π", "68 π", "68pi", "68 pi", "68*pi", "68 * pi"], "placeholder": "multiple of π", "show": "68π"}}}
E["c7-steps"] = {"type": "short", "xp": 2, "rows": 4, "answer": b64(
    "For each section: compute the radius expression a² + ab + b², multiply by that section's height and by π/3 to get its volume. "
    "Add the three volumes. Round only the total, for display.")}
c7_dims = "a1 = 2\nb1 = 3\nh1 = 3\na2 = 3\nb2 = 3\nh2 = 4\na3 = 3\nb3 = 1\nh3 = 3\n"
c7 = ("import math\n" + c7_dims +
      "v1 = math.pi * h1 * (a1 ** 2 + a1 * b1 + b1 ** 2) / 3\nv2 = math.pi * h2 * (a2 ** 2 + a2 * b2 + b2 ** 2) / 3\n"
      "v3 = math.pi * h3 * (a3 ** 2 + a3 * b3 + b3 ** 2) / 3\nprint(round(v1 + v2 + v3, 2))\n")
E["c7"] = {"type": "code", "xp": 10, "minLines": 14,
    "starter": "a1 = 2\nb1 = 3\nh1 = 3\n# Add the other dimensions and complete the program.\n",
    "cases": [
        {"name": "given dimensions", "expected": run(c7)},
        {"name": "middle height 1", "rewrite": [["h2 = 4", "h2 = 1"]], "expected": run(rewritten(c7, ("h2 = 4", "h2 = 1")))}],
    "check": QUALIFIED_MATH + '''for _name in ("a1", "b1", "h1", "a2", "b2", "h2", "a3", "b3", "h3"):
    assert _name in globals(), f"Assign the dimension {_name} to its own variable."
assert "math.pi" in __source__, "Use math.pi for pi."
assert "round(" in __source__, "Round the total to two decimal places with round(..., 2)."''',
    "answer": b64(c7),
    "answerNote": "The second case sets h2 = 1, so the checker expects the line `h2 = 4` in your program."}
E["c8-branch"] = {"type": "short", "xp": 1, "minChars": 5, "rows": 2, "placeholder": "Which part of the formula?", "answer": b64(
    "The fraction R₂R₃ / (R₂ + R₃) represents the two parallel branches. R₁ is added to it because it comes before the branches.")}
E["c8-hand"] = {"type": "table", "xp": 1, "blanks": {
    "branch": {"accept": ["10", "10.0"], "placeholder": "ohms", "width": "6rem"},
    "total": {"accept": ["20", "20.0"], "placeholder": "ohms", "width": "6rem"}}}
c8 = "r1 = 10\nr2 = 20\nr3 = 20\ntotal = r1 + r2 * r3 / (r2 + r3)\nprint(total)\n"
c8_case2 = [["r1 = 10", "r1 = 5"], ["r2 = 20", "r2 = 12"], ["r3 = 20", "r3 = 6"]]
E["c8"] = {"type": "code", "xp": 5, "minLines": 5,
    "starter": "r1 = 10\nr2 = 20\nr3 = 20\n# Complete the program.\n",
    "cases": [
        {"name": "(10, 20, 20)", "expected": run(c8)},
        {"name": "(5, 12, 6)", "rewrite": c8_case2, "expected": run(rewritten(c8, *c8_case2))}],
    "check": 'assert "(r2+r3)" in __source__.replace(" ", ""), "Put the complete sum r2 + r3 in parentheses so the whole sum is the denominator."',
    "answer": b64(c8)}
c9 = "import math\nq1 = 0.000002\nq2 = 0.000003\nr = 0.5\nEPSILON = 8.854 * 10 ** (-12)\nforce = q1 * q2 / (4 * math.pi * EPSILON * r ** 2)\nprint(round(force, 3))\n"
E["c9"] = {"type": "code", "xp": 10, "minLines": 8,
    "starter": "q1 = 0.000002\nq2 = 0.000003\nr = 0.5\n# Complete the program.\n",
    "cases": [
        {"name": "both charges", "expected": run(c9)},
        {"name": "one zero charge", "rewrite": [["q1 = 0.000002", "q1 = 0"]], "expected": run(rewritten(c9, ("q1 = 0.000002", "q1 = 0")))}],
    "check": QUALIFIED_MATH + '''import math as _m
assert "EPSILON" in globals(), "Store the constant under the name EPSILON (capital letters, the constant convention)."
assert _m.isclose(EPSILON, 8.854e-12), "EPSILON should be 8.854 * 10 ** (-12)."
assert "math.pi" in __source__, "Use math.pi for pi."
assert "round(" in __source__, "Round the force to three decimal places with round(..., 3)."''',
    "answer": b64(c9)}

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-05",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 5 Workbook",
    "subtitle": "Arithmetic, expressions, and modules",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-05/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
