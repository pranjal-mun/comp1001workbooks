"""Build workbooks/lecture-17/boss/exercises.json: the Lecture 17 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_17_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Run from anywhere:

    python3 workbooks/lecture-17/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-17/boss
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

# A check runs after the student's program in the same namespace. `_fn` finds a
# function the program defined; `_out` calls it with its output captured, so
# the test call does not add to the program's own output.
FN = '''import types, io, contextlib, re
def _fn(name):
    f = globals().get(name)
    assert isinstance(f, types.FunctionType), "Define a function named " + name + " with def."
    assert f.__code__.co_argcount == 0, "Define " + name + " with empty parentheses."
    assert f.__doc__ and f.__doc__.strip(), "Give " + name + " a docstring as the first statement of its body."
    return f
def _out(f):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        f()
    return buffer.getvalue()
def _calls(name):
    return len(re.findall(r"\\b" + name + r"\\s*\\(", __code__)) - 1
'''

E = {}

# ---------------------------------------------------------------- 1 Practice notice
notice = """def show_heading():
    \"\"\"Display the notice heading.\"\"\"
    print('Practice notice')

def show_details():
    \"\"\"Display the practice details.\"\"\"
    print('Topic: functions')
    print('Task: test each part')

def show_closing():
    \"\"\"Display the closing instruction.\"\"\"
    print('Keep your results.')

show_heading()
show_details()
show_closing()
"""
E["notice"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 16,
    "starter": ("def show_heading():\n    # Write the docstring and body.\n\ndef show_details():\n    # Write the docstring and body.\n\n"
                "def show_closing():\n    # Write the docstring and body.\n\n# Call the functions in order.\n"),
    "cases": [{"name": "Example 1", "expected": run(notice)}, {"name": "Example 2 (run the program again)", "expected": run(notice)}],
    "check": FN + '''assert "input(" not in __code__, "Read no input; the notice is fixed."
assert _out(_fn("show_heading")) == "Practice notice\\n", "show_heading should print Practice notice and nothing else."
assert _out(_fn("show_details")) == "Topic: functions\\nTask: test each part\\n", "show_details should print Topic: functions and Task: test each part and nothing else."
assert _out(_fn("show_closing")) == "Keep your results.\\n", "show_closing should print Keep your results. and nothing else."
for _name in ("show_heading", "show_details", "show_closing"):
    assert _calls(_name) == 1, "Call " + _name + " once, after all three definitions."
''',
    "hints": [
        "Each function prints its own part of the notice. `show_heading` prints one line, `show_details` prints two lines, and `show_closing` prints one line.",
        "The first statement of each body is its docstring, for example `\"\"\"Display the notice heading.\"\"\"`. The `print` calls come after it.",
        "After the three definitions, the top-level code is three calls: `show_heading()`, `show_details()`, and `show_closing()`, in that order.",
    ],
    "answer": b64(notice),
    "answerNote": "Each function prints its assigned part. An independent call to each function checks that part before the complete notice is run."}
assert E["notice"]["cases"][0]["expected"] == "Practice notice\nTopic: functions\nTask: test each part\nKeep your results."

# ---------------------------------------------------------------- 2 Framed rows
framed = """def print_border():
    \"\"\"Display a border of six equals signs.\"\"\"
    print('======')

rows = int(input())
print_border()
for row in range(rows):
    for column in range(6):
        print('*', end='')
    print()
print_border()
"""
E["framed"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 12,
    "starter": "def print_border():\n    # Write the docstring and body.\n\nrows = int(input())\n# Print the borders and rows.\n",
    "cases": input_cases(framed, ("Example 1: typed 2", ["2"]), ("Example 2: typed 0", ["0"]), ("Typed 1", ["1"]), ("Typed 3", ["3"]), ("Typed 4", ["4"])),
    "check": FN + '''assert _out(_fn("print_border")) == "======\\n", "print_border should print exactly six = characters and nothing else."
assert _calls("print_border") == 2, "Call print_border exactly twice: once before the rows and once after them."
assert re.search(r"^([ \\t]*)(for|while)\\b.*\\n(\\1[ \\t]+.*\\n)*?\\1[ \\t]+(for|while)\\b", __code__, re.M), "Use nested loops for the pattern rows."
import ast
_rest = [n for f in ast.parse(__source__).body if not (isinstance(f, ast.FunctionDef) and f.name == "print_border") for n in ast.walk(f)]
_text = lambda n: isinstance(n, ast.Constant) and isinstance(n.value, str)
assert not any(isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult) and (_text(n.left) or _text(n.right)) for n in _rest), "Do not use string repetition for the rows; print each * in the inner loop."
''',
    "hints": [
        "Call `print_border()` once before the rows and once after them. The rows go between the two calls.",
        "The outer loop is `for row in range(rows):`. Each pass prints one row of six `*` characters.",
        "Inside it, `for column in range(6):` prints one star with `print('*', end='')`. After the inner loop, an empty `print()` ends the row.",
    ],
    "answer": b64(framed),
    "answerNote": "The outer loop chooses a row. The inner loop prints its six characters, then an empty `print()` ends that row."}
assert E["framed"]["cases"][0]["expected"] == "======\n******\n******\n======"
assert E["framed"]["cases"][1]["expected"] == "======\n======"

# ---------------------------------------------------------------- 3 Group entry report
group = """def show_heading():
    \"\"\"Display the entry-report heading.\"\"\"
    print('Group entry')

def report_group_cost():
    \"\"\"Read group ages and display their total entry cost.\"\"\"
    total = 0
    line = input()
    while line != '':
        age = int(line)
        if age <= 4:
            price = 0
        elif age <= 15:
            price = 8
        elif age <= 59:
            price = 15
        else:
            price = 10
        total = total + price
        line = input()
    print('Total: $%.2f' % total)

def show_closing():
    \"\"\"Display the end of the entry report.\"\"\"
    print('End of report')

show_heading()
report_group_cost()
show_closing()
"""
E["group"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 24,
    "starter": ("def show_heading():\n    # Write the docstring and body.\n\ndef report_group_cost():\n    # Write the docstring and body.\n\n"
                "def show_closing():\n    # Write the docstring and body.\n\n# Call the functions in order.\n"),
    "cases": input_cases(group,
        ("Example 1: typed 4, 5, 16, 60, blank", ["4", "5", "16", "60", ""]),
        ("Example 2: typed blank", [""]),
        ("Typed 0, 4, 15, 16, 59, 60, 120, blank", ["0", "4", "15", "16", "59", "60", "120", ""]),
        ("Typed 30, 30, blank", ["30", "30", ""]),
        ("Typed 20 ages of 61, blank", ["61"] * 20 + [""])),
    "check": FN + '''import ast
_fn("report_group_cost")
assert _out(_fn("show_heading")) == "Group entry\\n", "show_heading should print Group entry and nothing else."
assert _out(_fn("show_closing")) == "End of report\\n", "show_closing should print End of report and nothing else."
for _name in ("show_heading", "report_group_cost", "show_closing"):
    assert _calls(_name) == 1, "Call " + _name + " once, after all three definitions."
_tree = ast.parse(__source__)
_inside = [n for f in _tree.body if isinstance(f, ast.FunctionDef) and f.name == "report_group_cost" for n in ast.walk(f)]
def _count(nodes, test):
    return sum(1 for n in nodes if test(n))
_is_input = lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "input"
_is_print = lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print"
assert _count(_inside, _is_input) == _count(list(ast.walk(_tree)), _is_input), "Keep the input inside report_group_cost."
assert _count(_inside, _is_print) >= 1, "Keep the total output inside report_group_cost."
assert any(isinstance(n, ast.While) for n in _inside), "Use a sentinel loop: a while loop that stops at the blank line."
assert "elif" in __code__ and "else" in __code__, "Choose each price with an if/elif/else chain."
''',
    "hints": [
        "`report_group_cost` does the whole cost report. It sets `total = 0`, reads the first `line = input()`, and loops `while line != ''`. The last statement of the loop body reads the next `line`.",
        "Inside the loop, convert with `age = int(line)`, then choose `price` with `if age <= 4:` (0), `elif age <= 15:` (8), `elif age <= 59:` (15), and `else:` (10). Add `price` to `total`.",
        "After the loop, still inside `report_group_cost`, print `'Total: $%.2f' % total`. An empty group never enters the loop, so the total stays 0.",
        "`show_heading` prints `Group entry` and `show_closing` prints `End of report`. The top-level code calls the three functions in that order.",
    ],
    "answer": b64(group),
    "answerNote": "Check for the blank line before converting an age to an integer. The total begins at zero, so the empty group is handled by the same output statement."}
assert E["group"]["cases"][0]["expected"] == "Group entry\nTotal: $33.00\nEnd of report"
assert E["group"]["cases"][1]["expected"] == "Group entry\nTotal: $0.00\nEnd of report"

# ---------------------------------------------------------------- 4 Two growth tables
growth = """def print_separator():
    \"\"\"Display a separator of ten hyphens.\"\"\"
    print('----------')

initial_balance = float(input())
print_separator()
print('Rate: 2%')
balance = initial_balance
for year in range(1, 4):
    balance = balance * 1.02
    print('%d %.2f' % (year, balance))
print_separator()
print('Rate: 5%')
balance = initial_balance
for year in range(1, 4):
    balance = balance * 1.05
    print('%d %.2f' % (year, balance))
print_separator()
"""
E["growth"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 16,
    "starter": "def print_separator():\n    # Write the docstring and body.\n\ninitial_balance = float(input())\n# Produce both tables with shared separators.\n",
    "cases": input_cases(growth, ("Example 1: typed 100", ["100"]), ("Example 2: typed 0", ["0"]), ("Typed 10000", ["10000"]),
                         ("Typed 49.99", ["49.99"]), ("Typed 1", ["1"])),
    "check": FN + '''assert _out(_fn("print_separator")) == "----------\\n", "print_separator should print exactly ten hyphens and nothing else."
assert _calls("print_separator") == 3, "Call print_separator exactly three times: before the first table, between the tables, and after the second."
assert re.search(r"^(for|while)\\b", __code__, re.M), "Keep the growth loops at the top level, not inside a function."
assert re.search(r"^\\S.*\\binput\\(", __code__, re.M), "Read the initial balance once at the top level."
assert re.search(r"\\b1\\.02\\b", __code__) and re.search(r"\\b1\\.05\\b", __code__), "Multiply the balance by 1.02 in the first table and by 1.05 in the second."
''',
    "hints": [
        "`print_separator` prints ten hyphens. Call it before the first heading, between the tables, and after the second table.",
        "For the first table, print `'Rate: 2%'`, set `balance = initial_balance`, and loop `for year in range(1, 4):`. Each pass multiplies `balance` by `1.02` and prints `'%d %.2f' % (year, balance)`.",
        "For the second table, print `'Rate: 5%'` and reset `balance = initial_balance` before the loop. Without the reset, the second table would start from 106.12 for the input 100.",
    ],
    "answer": b64(growth),
    "answerNote": "Resetting the balance makes the tables comparable. The shared function keeps all separator lines identical."}
assert E["growth"]["cases"][0]["expected"] == ("----------\nRate: 2%\n1 102.00\n2 104.04\n3 106.12\n----------\n"
                                               "Rate: 5%\n1 105.00\n2 110.25\n3 115.76\n----------")
assert E["growth"]["cases"][1]["expected"] == ("----------\nRate: 2%\n1 0.00\n2 0.00\n3 0.00\n----------\n"
                                               "Rate: 5%\n1 0.00\n2 0.00\n3 0.00\n----------")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-17-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 17 Boss Problems",
    "short": "L17 bosses",
    "subtitle": "Problem solving with functions: black boxes and decomposition",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-17/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
