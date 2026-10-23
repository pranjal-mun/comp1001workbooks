"""Build workbooks/lecture-18/boss/exercises.json: the Lecture 18 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_18_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Run from anywhere:

    python3 workbooks/lecture-18/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-18/boss
"""
import base64, itertools, json, subprocess, sys, pathlib

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
# function the program defined; `_call` calls it with its output captured, so
# the test call does not add to the program's own output.
FN = '''import types, io, contextlib, re, ast
_WORDS = ["empty parentheses", "one parameter", "two parameters", "three parameters"]
def _fn(name, *params):
    f = globals().get(name)
    assert isinstance(f, types.FunctionType), "Define a function named " + name + " with def."
    assert f.__code__.co_argcount == len(params), "Define " + name + "(" + ", ".join(params) + ") with " + _WORDS[len(params)] + "."
    return f
def _call(name, *args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        value = globals()[name](*args)
    return value, buffer.getvalue()
def _shown(name, args):
    return name + "(" + ", ".join(repr(a) for a in args) + ")"
def _returns(name, args, want):
    value, printed = _call(name, *args)
    call = _shown(name, args)
    if value is None:
        raise AssertionError(call + " returned None. Return a value on every path.")
    if isinstance(want, bool):
        ok = value is want
    else:
        ok = isinstance(value, (int, float)) and not isinstance(value, bool) and abs(value - want) < 1e-9
    assert ok, call + " should return " + repr(want) + ", not " + repr(value) + "."
def _body(name):
    for node in ast.parse(__source__).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return list(ast.walk(node))
    return []
'''

E = {}

# ---------------------------------------------------------------- 1 Diagonal length
diagonal = """def diagonal(width, height):
    return (width ** 2 + height ** 2) ** 0.5

width = float(input())
height = float(input())
print(f'{diagonal(width, height):.2f}')
"""
diag_ns = {}
exec(diagonal.split("\nwidth = float")[0], diag_ns)
DIAG_CALLS = [(3.0, 4.0), (8.0, 15.0), (1.0, 1.0), (0.5, 1.2)]
E["diagonal"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 6,
    "starter": ("def diagonal(width, height):\n    # Return the diagonal length.\n\nwidth = float(input())\nheight = float(input())\n"
                "# Call the function and print two decimal places.\n"),
    "cases": input_cases(diagonal, ("Example 1: typed 8 and 15", ["8", "15"]), ("Example 2: typed 1 and 1", ["1", "1"]),
                         ("Typed 3 and 4", ["3", "4"]), ("Typed 10000 and 10000", ["10000", "10000"]),
                         ("Typed 0.5 and 1.2", ["0.5", "1.2"]), ("Typed 2.5 and 6", ["2.5", "6"])),
    "check": FN + '_fn("diagonal", "width", "height")\n'
             + "".join(f"_returns('diagonal', {args!r}, {diag_ns['diagonal'](*args)!r})\n" for args in DIAG_CALLS)
             + '''assert _call("diagonal", 3.0, 4.0)[1] == "", "Print only in the caller: diagonal returns the length and prints nothing."
''',
    "hints": [
        "`diagonal` returns `(width ** 2 + height ** 2) ** 0.5`. For 8 and 15 that is the square root of 64 + 225 = 289, which is `17.0`.",
        "The caller formats the returned value: `print(f'{diagonal(width, height):.2f}')`. The function itself prints nothing.",
    ],
    "answer": b64(diagonal),
    "answerNote": "The function returns the calculation. Formatting belongs to the caller."}
assert [c["expected"] for c in E["diagonal"]["cases"][:2]] == ["17.00", "1.41"]

# ---------------------------------------------------------------- 2 Triangle check
triangle = """def can_form_triangle(a, b, c):
    return a + b > c and a + c > b and b + c > a

a = float(input())
b = float(input())
c = float(input())
print(can_form_triangle(a, b, c))
"""
tri_ns = {}
exec(triangle.split("\na = float")[0], tri_ns)
TRIPLES = list(itertools.product(range(1, 8), repeat=3))
tri_bits = "".join("1" if tri_ns["can_form_triangle"](*t) else "0" for t in TRIPLES)
E["triangle"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 6,
    "starter": "def can_form_triangle(a, b, c):\n    # Return the Boolean expression.\n\n# Read three lengths, call the function, and print the result.\n",
    "cases": input_cases(triangle, ("Example 1: typed 4, 6, 7", ["4", "6", "7"]), ("Example 2: typed 2, 5, 7", ["2", "5", "7"]),
                         ("Typed 3, 4, 5", ["3", "4", "5"]), ("Typed 1, 1, 2", ["1", "1", "2"]), ("Typed 7, 2, 5", ["7", "2", "5"]),
                         ("Typed 5, 9, 4", ["5", "9", "4"]), ("Typed 0.5, 0.5, 0.5", ["0.5", "0.5", "0.5"])),
    "check": FN + f'''_fn("can_form_triangle", "a", "b", "c")
_nodes = _body("can_form_triangle")
assert sum(isinstance(n, ast.Return) for n in _nodes) == 1 and not any(isinstance(n, (ast.If, ast.IfExp)) for n in _nodes), "Return one Boolean expression: use a single return statement and no if."
import itertools
_want = {tri_bits!r}
for _i, _t in enumerate(itertools.product(range(1, 8), repeat=3)):
    _returns("can_form_triangle", _t, _want[_i] == "1")
''',
    "hints": [
        "Each pair of lengths needs a sum strictly greater than the remaining length. The three comparisons are `a + b > c`, `a + c > b`, and `b + c > a`.",
        "All three comparisons must be true, so join them with `and` in one `return` statement. For 2, 5, 7 the first comparison is `7 > 7`, which is `False`.",
        "Read the lengths with `a = float(input())`, `b = float(input())`, and `c = float(input())`, then print `can_form_triangle(a, b, c)`.",
    ],
    "answer": b64(triangle),
    "answerNote": "All three comparisons must be true, so the expression uses `and`."}
assert [c["expected"] for c in E["triangle"]["cases"][:2]] == ["True", "False"]

# ---------------------------------------------------------------- 3 Middle of three
middle = """def middle_value(a, b, c):
    if (a <= b <= c) or (c <= b <= a):
        return b
    if (b <= a <= c) or (c <= a <= b):
        return a
    return c

a = int(input())
b = int(input())
c = int(input())
print(middle_value(a, b, c))
"""
mid_ns = {}
exec(middle.split("\na = int")[0], mid_ns)
MID_TRIPLES = list(itertools.product(range(-2, 3), repeat=3))
for t in MID_TRIPLES:
    assert mid_ns["middle_value"](*t) == sorted(t)[1]
mid_digits = "".join(str(mid_ns["middle_value"](*t) + 2) for t in MID_TRIPLES)
E["middle"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 11,
    "starter": "def middle_value(a, b, c):\n    # Return the middle value on every path.\n\n# Read three integers and print the returned result.\n",
    "cases": input_cases(middle, ("Example 1: typed 14, 3, 8", ["14", "3", "8"]), ("Example 2: typed 5, 5, 9", ["5", "5", "9"]),
                         ("Typed 9, 5, 5", ["9", "5", "5"]), ("Typed 7, 7, 7", ["7", "7", "7"]), ("Typed 2, 1, 3", ["2", "1", "3"]),
                         ("Typed -1000000, 1000000, 0", ["-1000000", "1000000", "0"])),
    "check": FN + f'''_fn("middle_value", "a", "b", "c")
assert not re.search(r"\\b(sorted|sort|list|min|max)\\b|\\[", __code__), "Do not use sorting, lists, min, or max. Compare the values instead."
assert sum(isinstance(n, ast.Return) for n in _body("middle_value")) >= 2, "Use several return statements, one for each way a value can be the middle."
import itertools
_want = {mid_digits!r}
for _i, _t in enumerate(itertools.product(range(-2, 3), repeat=3)):
    _returns("middle_value", _t, int(_want[_i]) - 2)
''',
    "hints": [
        "`b` is the middle when it lies between the other two, in either order: `a <= b <= c` or `c <= b <= a`. Return `b` in that case.",
        "Test `a` the same way with `b <= a <= c` or `c <= a <= b`, and return `a`. For 14, 3, 8 neither test is true.",
        "If neither `b` nor `a` is the middle, the last line returns `c`. Inclusive comparisons handle ties: for 5, 5, 9 the first test `5 <= 5 <= 9` is true and returns 5.",
    ],
    "answer": b64(middle),
    "answerNote": "Test whether b lies between the other two values, then whether a does. If neither does, c is the middle. Inclusive comparisons handle ties."}
assert [c["expected"] for c in E["middle"]["cases"][:2]] == ["8", "5"]

# ---------------------------------------------------------------- 4 Integer text check
integer = """def is_integer_text(text):
    while len(text) > 0 and text[0] == ' ':
        text = text[1:]
    while len(text) > 0 and text[-1] == ' ':
        text = text[:-1]
    if len(text) == 0:
        return False
    if text[0] == '+' or text[0] == '-':
        text = text[1:]
    if len(text) == 0:
        return False
    for character in text:
        if character < '0' or character > '9':
            return False
    return True

text = input()
print(is_integer_text(text))
"""
int_ns = {}
exec(integer.split("\ntext = input")[0], int_ns)
TEXTS = ["  -42  ", "+", "", "007", "12 3", "-", "+5", "abc", "   ", "4.0", "--4", " 12", "12 ", "+-3", "0", "- 4", "9a", "+0099", "1,000", "  +  "]
E["integer"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 16,
    "starter": ("def is_integer_text(text):\n    # Check outside spaces, the optional sign, and every remaining character.\n\n"
                "text = input()\nprint(is_integer_text(text))\n"),
    "cases": input_cases(integer, ("Example 1: typed '  -42  '", ["  -42  "]), ("Example 2: typed '+'", ["+"]),
                         ("Example 3: typed an empty line", [""]), ("Typed '12 3'", ["12 3"]), ("Typed '+5'", ["+5"]),
                         ("Typed '--4'", ["--4"]), ("Typed '4.0'", ["4.0"]), ("Typed '   '", ["   "])),
    "check": FN + '''_fn("is_integer_text", "text")
assert not re.search(r"\\b(int|float)\\s*\\(", __code__), "Do not convert the text with int or float. Check each character instead."
_nodes = _body("is_integer_text")
assert sum(isinstance(n, ast.Return) for n in _nodes) >= 2, "Use several return paths: return False as soon as the text fails a rule."
assert any(isinstance(n, (ast.For, ast.While)) for n in _nodes), "Use a loop to check the remaining characters."
''' + "".join(f"_returns('is_integer_text', ({t!r},), {int_ns['is_integer_text'](t)!r})\n" for t in TEXTS),
    "hints": [
        "Remove the outside spaces with two loops. `while len(text) > 0 and text[0] == ' ':` drops the first character with `text = text[1:]`, and a second loop drops the last one with `text = text[:-1]`.",
        "If nothing is left, return `False`. If `text[0]` is `'+'` or `'-'`, remove it with `text[1:]`, then return `False` again if nothing is left. For `+` this second test returns `False`.",
        "Loop over the remaining characters. A character below `'0'` or above `'9'` is not a digit, so return `False` at once. After the loop, return `True`.",
    ],
    "answer": b64(integer),
    "answerNote": "The length checks protect indexing and reject an empty value or a sign alone. A non-digit ends the call with False. "
                  "Reaching the last line means every remaining character is a digit."}
assert [c["expected"] for c in E["integer"]["cases"][:3]] == ["True", "False", "False"]

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-18-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 18 Boss Problems",
    "short": "L18 bosses",
    "subtitle": "Parameters and return values",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-18/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
