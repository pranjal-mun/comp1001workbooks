"""Build workbooks/lecture-31/boss/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_31_SHARED_CONTENT.tex; the listings below are copied from it and
model answers follow its \\solution{...} text. Run from anywhere:

    python3 workbooks/lecture-31/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-31/boss
"""
import base64, contextlib, io, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=()):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""),
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n")

def run_error(code, inputs=()):
    """Run code that must stop with an exception; return (stdout, exception type)."""
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""),
                       capture_output=True, text=True)
    assert p.returncode != 0, "expected an exception"
    return p.stdout.rstrip("\n"), p.stderr.strip().split("\n")[-1].split(":")[0]

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

def example(code, output=True):
    spec = {"type": "example", "code": code.rstrip("\n")}
    if output:
        spec["output"] = run(code)
    return spec

def accept(*values, width="10rem", placeholder="answer", show=None):
    spec = {"accept": list(values), "placeholder": placeholder, "width": width}
    if show is not None:
        spec["show"] = show
    return spec

def exc(name, width="12rem"):
    return accept(name, width=width, placeholder="exception", show=name)

NONE = accept("none", "None", "no exception", "No exception", "no", width="12rem", placeholder="exception", show="none")

def short(answer, xp=2, min_chars=15, rows=3, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

def input_cases(solution, *runs):
    return [{"name": name, "inputs": list(inputs), "expected": run_with_prompts(solution, inputs)} for name, inputs in runs]

def table(**blanks):
    return {"type": "table", "xp": 1, "blanks": blanks}

def choice(letter):
    return table(c=accept(letter, letter.lower(), width="3.5rem", placeholder="", show=letter))

def true_false(*values):
    return table(**{f"t{i}": accept(str(v), str(v).lower(), width="6rem", placeholder="", show=str(v)) for i, v in enumerate(values, 1)})

# A check runs after the student's program in a copy of its namespace.
# `_H` lists every except handler. `_names(h)` gives the exception names a
# handler lists. `_handles(name)` is true when some handler names that type.
# `_tries()` lists try statements. `_def(name)` is the def node of a function,
# and `_raises(node)` lists the raise statements inside a node. Every exercise
# rejects a bare except and except Exception.
EXC = '''import ast, types, io, contextlib
_TREE = ast.parse(__source__)
_H = [n for n in ast.walk(_TREE) if isinstance(n, ast.ExceptHandler)]
def _names(h):
    t = h.type
    if isinstance(t, ast.Tuple):
        return [e.id for e in t.elts if isinstance(e, ast.Name)]
    return [t.id] if isinstance(t, ast.Name) else []
def _handles(name):
    return any(name in _names(h) for h in _H)
def _tries():
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.Try)]
def _loops():
    return [n for n in ast.walk(_TREE) if isinstance(n, (ast.For, ast.While))]
def _fn(name, *params):
    f = globals().get(name)
    assert isinstance(f, types.FunctionType), "Define a function named " + name + " with def."
    assert f.__code__.co_argcount == len(params), "Define " + name + "(" + ", ".join(params) + ")."
    return f
def _def(name):
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.FunctionDef) and n.name == name][0]
def _raises(node):
    return [n for n in ast.walk(node) if isinstance(n, ast.Raise)]
def _quiet(f, *args):
    """Call f with its output hidden. Return (result, exception type name or None, output)."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            return f(*args), None, buf.getvalue()
    except Exception as e:
        return None, type(e).__name__ + ": " + str(e), buf.getvalue()
assert all(h.type is not None for h in _H), "Do not use a bare except. Name the exception types that you expect."
assert not any(n in ("Exception", "BaseException") for h in _H for n in _names(h)), "Name the specific exception types. Do not use except Exception."
'''

def needs(*names):
    return "".join(f'assert _handles({n!r}), "Add an except block that names {n}."\n' for n in names)
# Listings from the kit, in workbook order.
SRC = {}
SRC['boss_1_starter'] = '''FIRST_ITEM_COST = 10.95
NEXT_ITEM_COST = 2.95'''
SRC['boss_1_solution'] = '''FIRST_ITEM_COST = 10.95
NEXT_ITEM_COST = 2.95


def to_items(text):
    """Return an item count of at least 1.

    Raise ValueError if the text is not such a count.
    """
    items = int(text)
    if items < 1:
        raise ValueError("items must be at least 1")
    return items


def shipping_cost(items):
    """Return the cost for a valid item count. Raise no exception."""
    return FIRST_ITEM_COST + (items - 1) * NEXT_ITEM_COST


def main():
    """Print the shipping cost and return None. Handle ValueError."""
    while True:
        try:
            items = to_items(input())
            break
        except ValueError:
            print("Enter a whole number of at least 1.")
    print(f"Shipping: ${shipping_cost(items):.2f}")


main()'''
SRC['boss_2_starter'] = '''MONTHS = ["january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"]
DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]'''
SRC['boss_2_solution'] = '''MONTHS = ["january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"]
DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def days_in_month(name):
    """Return the number of days. Raise ValueError for an unknown month."""
    name = name.lower()
    if name not in MONTHS:
        raise ValueError("unknown month")
    return DAYS[MONTHS.index(name)]


def check_date(line):
    """Return the day. Raise ValueError if the line is not a valid date."""
    parts = line.split()
    if len(parts) != 2:
        raise ValueError("expected month and day")
    days = days_in_month(parts[0])
    day = int(parts[1])
    if day < 1 or day > days:
        raise ValueError("day out of range")
    return day


def main():
    """Print the date results and return None. Handle ValueError."""
    count = 0
    while True:
        line = input().strip()
        if line == "":
            break
        try:
            check_date(line)
        except ValueError as err:
            print(f"Rejected: {line} ({err})")
        else:
            print(f"Valid: {line}")
            count = count + 1
    if count == 0:
        print("No valid dates.")
    else:
        print(f"Valid dates: {count}")


main()'''

PURE = '''def _calls(name, fn):
    return any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == fn for n in ast.walk(_def(name)))
def _pure(*names):
    for _n in names:
        assert not _calls(_n, "input") and not _calls(_n, "print"), _n + " must not use input or print. main reads the input and prints."
def _docs(*names):
    for _n in names:
        assert any(isinstance(n, ast.FunctionDef) and n.name == _n for n in ast.walk(_TREE)), "Define a function named " + _n + "."
        assert ast.get_docstring(_def(_n)), "Write a docstring for " + _n + "."
'''

E = {}

# ---------------------------------------------------------------- 1 Shipping cost (Stephenson 83)
ship = SRC["boss_1_solution"]
ship_cases = input_cases(ship,
    ("Example 1: 3", ["3"]),
    ("Example 2: 0, two, 1", ["0", "two", "1"]),
    ("Ten items", ["10"]),
    ("A negative count, then 2", ["-4", "2"]),
    ("A decimal, a blank line, then 5", ["2.5", "", "5"]),
    ("Spaces around a number", [" 4 "]))
assert [c["expected"] for c in ship_cases] == ["Shipping: $16.85",
    "Enter a whole number of at least 1.\nEnter a whole number of at least 1.\nShipping: $10.95",
    "Shipping: $37.50", "Enter a whole number of at least 1.\nShipping: $13.90",
    "Enter a whole number of at least 1.\nEnter a whole number of at least 1.\nShipping: $22.75", "Shipping: $19.80"]
E["shipping-cost"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 22,
    "starter": SRC["boss_1_starter"],
    "cases": ship_cases,
    "check": EXC + PURE + needs("ValueError") + '''_t = _fn("to_items", "text")
_s = _fn("shipping_cost", "items")
_fn("main")
_pure("to_items", "shipping_cost")
_docs("to_items", "shipping_cost", "main")
assert _quiet(_t, "0")[1] == "ValueError: items must be at least 1", 'to_items("0") should raise ValueError("items must be at least 1").'
assert (_quiet(_t, "two")[1] or "").startswith("ValueError"), 'to_items("two") should let the ValueError from int pass to the caller.'
assert _quiet(_t, "3")[0] == 3, 'to_items("3") should return 3.'
assert round(_quiet(_s, 1)[0], 2) == 10.95 and round(_quiet(_s, 3)[0], 2) == 16.85, "shipping_cost(1) should return 10.95, and shipping_cost(3) should return 16.85."
assert _loops(), "Ask again in a while loop until the count is valid."
''',
    "hints": [
        "`to_items` converts with `int` and raises `ValueError(\"items must be at least 1\")` when the count is below 1. It does not catch anything.",
        "`shipping_cost` returns `FIRST_ITEM_COST` plus `(items - 1)` times `NEXT_ITEM_COST`.",
        "In `main`, use `while True:` with `try:`, `items = to_items(input())` and `break`. The `except ValueError:` block prints the message. After the loop, print `f\"Shipping: ${...:.2f}\"`.",
    ],
    "answer": b64(ship),
    "answerNote": "to_items converts and checks, shipping_cost computes, and main is the only function that reads input, prints and handles the exception."}

# ---------------------------------------------------------------- 2 Checking dates (Stephenson 38)
dates = SRC["boss_2_solution"]
date_cases = input_cases(dates,
    ("Example 1: five entries", ["March 14", "february 29", "February 30", "Smarch 3", "March 14.5", ""]),
    ("Example 2: blank line only", [""]),
    ("April 31 and a missing day", ["April 31", "march", ""]),
    ("Day 0 and three parts", ["June 0", "June 1 2026", "DECEMBER 31", ""]),
    ("Spaces around the line", ["  july 4  ", "January   1", ""]),
    ("Only bad entries", ["x 1", "May five", ""]))
assert date_cases[0]["expected"] == ("Valid: March 14\nValid: february 29\nRejected: February 30 (day out of range)\n"
    "Rejected: Smarch 3 (unknown month)\nRejected: March 14.5 (invalid literal for int() with base 10: '14.5')\nValid dates: 2")
assert date_cases[1]["expected"] == "No valid dates."
assert date_cases[2]["expected"] == "Rejected: April 31 (day out of range)\nRejected: march (expected month and day)\nNo valid dates."
E["checking-dates"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 34,
    "starter": SRC["boss_2_starter"],
    "cases": date_cases,
    "check": EXC + PURE + needs("ValueError") + '''_d = _fn("days_in_month", "name")
_c = _fn("check_date", "line")
_fn("main")
_pure("days_in_month", "check_date")
_docs("days_in_month", "check_date", "main")
assert _quiet(_d, "FEBRUARY")[0] == 29 and _quiet(_d, "april")[0] == 30, 'days_in_month("FEBRUARY") should return 29, and days_in_month("april") should return 30.'
assert _quiet(_d, "Smarch")[1] == "ValueError: unknown month", 'days_in_month("Smarch") should raise ValueError("unknown month").'
assert _quiet(_c, "March 14")[0] == 14, 'check_date("March 14") should return 14.'
assert _quiet(_c, "march")[1] == "ValueError: expected month and day", 'check_date("march") should raise ValueError("expected month and day").'
assert _quiet(_c, "June 0")[1] == "ValueError: day out of range", 'check_date("June 0") should raise ValueError("day out of range").'
assert (_quiet(_c, "May five")[1] or "").startswith("ValueError: invalid literal"), 'check_date("May five") should let the ValueError from int pass to the caller.'
assert any(h.name for h in _H), "Handle the exception with except ValueError as err, and print the message."
assert _loops(), "Read the lines with a while loop that stops at a blank line."
''',
    "hints": [
        "`days_in_month` lowers the name, raises `ValueError(\"unknown month\")` if it is not in `MONTHS`, and returns `DAYS[MONTHS.index(name)]`.",
        "`check_date` splits the line. It raises for a wrong number of parts, calls `days_in_month`, converts the day with `int`, and raises when the day is below 1 or above the month's days.",
        "In `main`, strip each line and `break` on `\"\"`. Call `check_date` in `try`. `except ValueError as err:` prints `f\"Rejected: {line} ({err})\"`. Otherwise print `Valid:` and add 1 to a count. Check the count after the loop.",
    ],
    "answer": b64(dates),
    "answerNote": "The two helpers only raise. main skips a bad line with a message, counts the valid ones and checks for the empty case at the end."}

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-31-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 31 Boss Problems",
    "short": "L31 bosses",
    "subtitle": "Input validation and robust programs",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-31/boss/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
for key, spec in E.items():
    for c in spec.get("cases", []):
        print(key, "|", c["name"], "|", c["expected"].replace("\n", " / "))
