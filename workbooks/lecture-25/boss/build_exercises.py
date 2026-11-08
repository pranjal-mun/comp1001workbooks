"""Build workbooks/lecture-25/boss/exercises.json: the Lecture 25 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_25_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Run from anywhere:

    python3 workbooks/lecture-25/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-25/boss
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

# A check runs after the student's program in a copy of its namespace.
# `_calls(method)` lists method calls such as .sort(). `_func_calls` lists
# calls of a plain function name. `_comps()` lists list comprehensions.
# `_swaps()` lists tuple assignments such as a[i], a[j] = a[j], a[i].
# `_no_defs()` asks for a script with no def.
AST = '''import ast
_TREE = ast.parse(__source__)
def _calls(method):
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == method]
def _func_calls(name):
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name]
def _comps():
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.ListComp)]
def _loops():
    return [n for n in ast.walk(_TREE) if isinstance(n, (ast.For, ast.While))]
def _swaps():
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Tuple) and isinstance(n.value, ast.Tuple)]
def _no_defs():
    assert not any(isinstance(n, ast.FunctionDef) for n in ast.walk(_TREE)), "Write a script. Do not define functions with def."
'''

E = {}

# ---------------------------------------------------------------- 1 Three orders of readings (Stephenson 104)
readings = """readings = []
reading = int(input())
while reading != -999:
    readings.append(reading)
    reading = int(input())
print("Original:", readings)
descending = sorted(readings, reverse=True)
print("Descending:", descending)
print("After sorted:", readings)
readings.sort()
print("Ascending:", readings)
"""
E["readings"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 11,
    "starter": "readings = []\n# Read the values and print the four labeled lists.\n",
    "cases": input_cases(readings,
        ("Example 1: typed 7, -2, 7, 3, -999", ["7", "-2", "7", "3", "-999"]),
        ("Example 2: typed -999", ["-999"]),
        ("Typed 5, -999", ["5", "-999"]),
        ("Typed 999, -998, 0, -999", ["999", "-998", "0", "-999"]),
        ("Typed 4, 4, 4, -999", ["4", "4", "4", "-999"]),
        ("Typed 1 to 6 in mixed order, then -999", ["3", "6", "1", "5", "2", "4", "-999"])),
    "check": AST + '''_no_defs()
assert _calls("append"), "Store the readings in one list with append."
assert any(any(k.arg == "reverse" for k in c.keywords) for c in _func_calls("sorted")), "Make the descending list with sorted and reverse=True."
assert _calls("sort"), "Change the stored list to ascending order with sort()."
''',
    "hints": [
        "Read the first reading with `int(input())` before the loop. Repeat `while reading != -999`: append the reading, then read the next one at the end of the loop body.",
        "Print `\"Original:\"` and the list. Then make a separate list with `sorted(readings, reverse=True)` and print it after `\"Descending:\"`.",
        "`sorted` does not change `readings`, so `\"After sorted:\"` still shows the input order.",
        "Call `readings.sort()` without an assignment. Then print `\"Ascending:\"` and `readings`.",
    ],
    "answer": b64(readings),
    "answerNote": "sorted creates the descending copy. The later sort call changes the stored list."}
assert E["readings"]["cases"][0]["expected"] == "Original: [7, -2, 7, 3]\nDescending: [7, 7, 3, -2]\nAfter sorted: [7, -2, 7, 3]\nAscending: [-2, 3, 7, 7]"
assert E["readings"]["cases"][1]["expected"] == "Original: []\nDescending: []\nAfter sorted: []\nAscending: []"

# ---------------------------------------------------------------- 2 Compare sensor readings with their average (Stephenson 112)
average = """values = []
line = input()
while line != "":
    values.append(float(line))
    line = input()
if len(values) == 0:
    print("No values")
else:
    average = sum(values) / len(values)
    below = [value for value in values if value < average]
    equal = [value for value in values if value == average]
    above = [value for value in values if value > average]
    print(f"Average: {average:.2f}")
    print("Below:", below)
    print("Equal:", equal)
    print("Above:", above)
"""
E["average"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 15,
    "starter": "values = []\n# Read the values and print the average and filtered lists.\n",
    "cases": input_cases(average,
        ("Example 1: typed 2, 5, 8, blank", ["2", "5", "8", ""]),
        ("Example 2: typed blank", [""]),
        ("Typed 4, blank", ["4", ""]),
        ("Typed 1, 2, 2, blank", ["1", "2", "2", ""]),
        ("Typed -3.5, 2, 2, 10, 1, blank", ["-3.5", "2", "2", "10", "1", ""]),
        ("Typed 7, 7, 7, blank", ["7", "7", "7", ""])),
    "check": AST + '''_no_defs()
assert _func_calls("float"), "Read each value with float."
assert _func_calls("sum") and _func_calls("len"), "Calculate the average with sum and len."
assert len(_comps()) >= 3, "Build the three filtered lists with comprehensions, such as [value for value in values if value < average]."
''',
    "hints": [
        "Read lines with `input()` until a blank line. Append `float(line)` for each nonblank line.",
        "Check `len(values) == 0` first and print `\"No values\"`. This also prevents a division by zero.",
        "Calculate `average = sum(values) / len(values)`. Build each list with a comprehension, such as `[value for value in values if value < average]`.",
        "Print the average with `f\"Average: {average:.2f}\"`. Compare with `average` itself, not the rounded text. For 1, 2, 2 the average is 1.666..., so no value is equal.",
    ],
    "answer": b64(average),
    "answerNote": "The length check handles empty input before division. Each condition compares an original value with the unrounded average."}
assert E["average"]["cases"][0]["expected"] == "Average: 5.00\nBelow: [2.0]\nEqual: [5.0]\nAbove: [8.0]"
assert E["average"]["cases"][1]["expected"] == "No values"
assert "Equal: []" in E["average"]["cases"][3]["expected"]

# ---------------------------------------------------------------- 3 Keep names and marks matched (original, awaiting approval)
matched = """names = ["Lia", "Omar", "Nia", "Theo"]
marks = [72, 94, 94, 61]
move_name = input()
new_position = int(input())
best = 0
for i in range(1, len(marks)):
    if marks[i] > marks[best]:
        best = i
print("First highest:", names[best], marks[best])
names[0], names[best] = names[best], names[0]
marks[0], marks[best] = marks[best], marks[0]
print("Swap names:", names)
print("Swap marks:", marks)
old_position = names.index(move_name)
moved_name = names.pop(old_position)
moved_mark = marks.pop(old_position)
names.insert(new_position, moved_name)
marks.insert(new_position, moved_mark)
print("Move names:", names)
print("Move marks:", marks)
names.reverse()
marks.reverse()
print("Reverse names:", names)
print("Reverse marks:", marks)
"""
E["matched"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 22,
    "starter": 'names = ["Lia", "Omar", "Nia", "Theo"]\nmarks = [72, 94, 94, 61]\n# Read the move, then change both lists in the required order.\n',
    "cases": input_cases(matched,
        ("Example 1: typed Nia, 0", ["Nia", "0"]),
        ("Example 2: typed Theo, 3", ["Theo", "3"]),
        ("Typed Lia, 3", ["Lia", "3"]),
        ("Typed Omar, 2", ["Omar", "2"]),
        ("Typed Theo, 0", ["Theo", "0"]),
        ("Typed Nia, 1", ["Nia", "1"])),
    "check": AST + '''_no_defs()
assert not _func_calls("max"), "Find the index of the highest mark with a loop. Do not use max."
assert _loops(), "Find the index of the highest mark with a loop."
assert len(_swaps()) >= 2, "Use the swap idiom on each list, such as names[0], names[best] = names[best], names[0]."
assert len(_calls("pop")) >= 2 and len(_calls("insert")) >= 2, "Move the pair with pop and insert on both lists."
assert len(_calls("reverse")) >= 2, "Reverse both lists with reverse()."
assert names[marks.index(94)] in ("Omar", "Nia") and len(names) == len(marks) == 4, "Keep both lists the same length, with each name matched to its mark."
''',
    "hints": [
        "Read the name with `input()` and the index with `int(input())`. Find the highest-mark index with the loop from Section 4: start with `best = 0` and use `>` so the first 94 wins.",
        "Swap in both lists with the same indexes: `names[0], names[best] = names[best], names[0]`, then the same statement for `marks`.",
        "Find the named student's index once, for example with `names.index(move_name)`. Pop that index from both lists, then insert each popped value at the new index.",
        "Call `reverse()` on both lists. Print the two lists after each of the three changes, with the labels in the examples.",
    ],
    "answer": b64(matched),
    "answerNote": "The move uses the same old index and destination in both lists. The two reversals preserve the pairs."}
assert E["matched"]["cases"][0]["expected"] == (
    "First highest: Omar 94\nSwap names: ['Omar', 'Lia', 'Nia', 'Theo']\nSwap marks: [94, 72, 94, 61]\n"
    "Move names: ['Nia', 'Omar', 'Lia', 'Theo']\nMove marks: [94, 94, 72, 61]\n"
    "Reverse names: ['Theo', 'Lia', 'Omar', 'Nia']\nReverse marks: [61, 72, 94, 94]")

# ---------------------------------------------------------------- 4 Fit a line to sensor points (Stephenson 117)
fit = """x_values = []
y_values = []
line = input()
while line != "":
    x_values.append(float(line))
    y_values.append(float(input()))
    line = input()
n = len(x_values)
if n < 2:
    print("Need at least two points")
else:
    s_x = sum([x_values[i] for i in range(n)])
    s_y = sum([y_values[i] for i in range(n)])
    s_xx = sum([x_values[i] ** 2 for i in range(n)])
    s_xy = sum([x_values[i] * y_values[i] for i in range(n)])
    denominator = s_xx - s_x ** 2 / n
    if denominator == 0:
        print("Cannot fit a line")
    else:
        slope = (s_xy - s_x * s_y / n) / denominator
        intercept = s_y / n - slope * s_x / n
        slope = round(slope, 2)
        intercept = round(intercept, 2)
        if slope == 0:
            slope = 0.0
        if intercept == 0:
            intercept = 0.0
        if intercept < 0:
            print(f"y = {slope:.2f}x - {-intercept:.2f}")
        else:
            print(f"y = {slope:.2f}x + {intercept:.2f}")
"""
E["fit"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 28,
    "starter": "x_values = []\ny_values = []\n# Read points, check the cases, and calculate the fitted line.\n",
    "cases": input_cases(fit,
        ("Example 1: points (0, -1), (2, 3), (4, 6)", ["0", "-1", "2", "3", "4", "6", ""]),
        ("Example 2: typed blank", [""]),
        ("Example 3: points (2, 4), (2, 7)", ["2", "4", "2", "7", ""]),
        ("One point (3, 4)", ["3", "4", ""]),
        ("Points on a line: (0, 1), (1, 3), (2, 5)", ["0", "1", "1", "3", "2", "5", ""]),
        ("Negative slope: (0, 5), (2, 1)", ["0", "5", "2", "1", ""]),
        ("Points (1, 1), (2, 2), (3, 3)", ["1", "1", "2", "2", "3", "3", ""]),
        ("Points (-2, 3), (1, -4), (5, 0), (6, -2)", ["-2", "3", "1", "-4", "5", "0", "6", "-2", ""])),
    "check": AST + '''_no_defs()
assert len(_func_calls("sum")) >= 4 and len(_comps()) >= 4, "Compute all four sums with sum and comprehensions over indexes, such as sum([x_values[i] for i in range(n)])."
assert _func_calls("round"), "Round each coefficient with round(value, 2) before you choose the intercept sign."
assert _calls("append"), "Store the points in two related lists with append."
''',
    "hints": [
        "Read an x line. While it is not blank, append `float(line)` to `x_values`, read the y line and append `float(input())` to `y_values`, then read the next x line.",
        "Let `n = len(x_values)`. If `n < 2`, print `\"Need at least two points\"`. Otherwise compute the four sums, such as `s_xy = sum([x_values[i] * y_values[i] for i in range(n)])`.",
        "Compute `d = s_xx - s_x ** 2 / n`. If `d == 0`, every x value is equal, so print `\"Cannot fit a line\"`.",
        "Compute `m` first, then `b` with the unrounded `m`. Round both to two places. If the rounded `b` is negative, print `- ` and `-b`; otherwise print `+ ` and `b`. Turn a rounded `-0.0` into `0.0` first.",
    ],
    "answer": b64(fit),
    "answerNote": "The calculation uses the unrounded slope for the intercept. The output handles a negative intercept without printing a plus sign before it."}
FIT = [c["expected"] for c in E["fit"]["cases"]]
assert FIT[:4] == ["y = 1.75x - 0.83", "Need at least two points", "Cannot fit a line", "Need at least two points"]
assert FIT[4:7] == ["y = 2.00x + 1.00", "y = -2.00x + 5.00", "y = 1.00x + 0.00"], FIT

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-25-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 25 Boss Problems",
    "short": "L25 bosses",
    "subtitle": "List algorithms, slices, and comprehensions",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-25/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
for key, spec in E.items():
    for c in spec["cases"]:
        print(key, "|", c["name"], "|", c["expected"].replace("\n", " / "))
