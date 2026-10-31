"""Build workbooks/lecture-21/boss/exercises.json: the Lecture 21 boss problems.

The three problems are the Boss Problems section of the kit's
LECTURE_21_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Each boss also has the workbook's
trace or written questions, placed after its code box. Run from
anywhere:

    python3 workbooks/lecture-21/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-21/boss
"""
import base64, contextlib, io, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=(), ok=True):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""),
                       capture_output=True, text=True)
    if ok:
        assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n"), p.stderr

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
    return run(wrapper)[0]

def input_cases(solution, *runs):
    return [{"name": name, "inputs": list(inputs), "expected": run_with_prompts(solution, inputs)} for name, inputs in runs]

def namespace(code):
    ns = {"__name__": "lecture21_boss"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    return ns

def accept(*values, width="8rem", placeholder="answer", show=None):
    spec = {"accept": list(values), "placeholder": placeholder, "width": width}
    if show is not None:
        spec["show"] = show
    return spec

def short(answer, xp=2, min_chars=30, rows=4, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

# A check runs after the student's program in a copy of its namespace. `_fn`
# finds a function the program defined; `_call` calls it with its output
# captured, so the test call does not add to the program's own output. `_guard`
# looks for the standard guard as the last statement of the file. `_recursive`
# asks for exactly one call of the function inside its own body, and
# `_no_loops` rejects for and while loops anywhere in the file.
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
    call = _shown(name, args)
    try:
        value, printed = _call(name, *args)
    except RecursionError:
        raise AssertionError(call + " raised RecursionError. Check that every recursive call moves toward the base case.")
    if value is None:
        raise AssertionError(call + " returned None. Return a value on every path.")
    if isinstance(want, float):
        ok = isinstance(value, (int, float)) and not isinstance(value, bool) and abs(value - want) <= 1e-9 * max(1, abs(want))
    else:
        ok = value == want and type(value) is type(want)
    assert ok, call + " should return " + repr(want) + ", not " + repr(value) + "."
def _guard():
    _tree = ast.parse(__source__)
    _last = _tree.body[-1] if _tree.body else None
    _ok = False
    if isinstance(_last, ast.If) and not _last.orelse and isinstance(_last.test, ast.Compare):
        _sides = [_last.test.left] + list(_last.test.comparators)
        _names = [s.id for s in _sides if isinstance(s, ast.Name)]
        _texts = [s.value for s in _sides if isinstance(s, ast.Constant)]
        _call_main = (len(_last.body) == 1 and isinstance(_last.body[0], ast.Expr) and isinstance(_last.body[0].value, ast.Call)
                      and isinstance(_last.body[0].value.func, ast.Name) and _last.body[0].value.func.id == "main"
                      and not _last.body[0].value.args and not _last.body[0].value.keywords)
        _ok = (len(_sides) == 2 and isinstance(_last.test.ops[0], ast.Eq) and _names == ["__name__"]
               and _texts == ["__main__"] and _call_main)
    assert _ok, "End the file with the standard guard: if __name__ == '__main__': followed by an indented main()."
def _body(name):
    for node in ast.parse(__source__).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return list(ast.walk(node))
    return []
def _calls_in(name, callee):
    return [n for n in _body(name) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == callee]
def _recursive(name):
    _n = len(_calls_in(name, name))
    assert _n >= 1, "Make " + name + " recursive: call " + name + " inside its own body."
    assert _n == 1, "Use one recursive call: call " + name + " once inside its own body, not " + str(_n) + " times."
def _no_loops():
    assert not any(isinstance(n, (ast.For, ast.While, ast.comprehension)) for n in ast.walk(ast.parse(__source__))), "Use recursion and no loops. Remove the for or while loop."
def _no_global():
    assert not any(isinstance(n, (ast.Global, ast.Nonlocal)) for n in ast.walk(ast.parse(__source__))), "Do not use global or nonlocal. Keep each value in its own call and return results."
'''

E = {}

# ---------------------------------------------------------------- 1 Common factor finder
gcd = """def gcd(a, b):
    if b == 0:
        return a
    return gcd(b, a % b)

def main():
    a = int(input())
    b = int(input())
    print('GCD:', gcd(a, b))

if __name__ == '__main__':
    main()
"""
gcd_ns = namespace(gcd)
# The workbook's trace of gcd(48, 18): the calls in order, each returning 6.
trace = []
def _trace(a, b):
    trace.append((a, b))
    return a if b == 0 else _trace(b, a % b)
assert _trace(48, 18) == 6 and trace == [(48, 18), (18, 12), (12, 6), (6, 0)]
GCD_CALLS = [(48, 18), (18, 48), (7, 0), (1, 0), (10000, 0), (1, 10000), (10000, 1), (12, 8), (17, 5), (100, 75),
             (9999, 3333), (10000, 9999), (6, 6), (270, 192)]
E["gcd"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 14,
    "starter": "def gcd(a, b):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    "cases": input_cases(gcd, ("Example 1: typed 48 and 18", ["48", "18"]), ("Example 2: typed 7 and 0", ["7", "0"]),
                         ("Typed 18 and 48", ["18", "48"]), ("Typed 1 and 10000", ["1", "10000"]),
                         ("Typed 10000 and 9999", ["10000", "9999"]), ("Typed 270 and 192", ["270", "192"]),
                         ("Typed 10000 and 0", ["10000", "0"])),
    "check": FN + '''_fn("gcd", "a", "b")
_fn("main")
_recursive("gcd")
_no_loops()
assert any(isinstance(_n, ast.Compare) and len(_n.ops) == 1 and isinstance(_n.ops[0], ast.Eq)
           and sorted(type(_s).__name__ + str(getattr(_s, "id", getattr(_s, "value", "")))
                      for _s in [_n.left] + _n.comparators) == ["Constant0", "Nameb"]
           for _n in ast.walk(ast.parse(__source__))), "Use b == 0 as the base case."
''' + "".join(f"_returns('gcd', {a!r}, {gcd_ns['gcd'](*a)!r})\n" for a in GCD_CALLS) + "_guard()\n",
    "hints": [
        "Start `gcd` with the base case: `if b == 0:` return `a`. For 7 and 0 that returns 7 at once.",
        "Otherwise return `gcd(b, a % b)`. For 48 and 18 the remainder `48 % 18` is 12, so the next call is `gcd(18, 12)`, then `gcd(12, 6)`, then `gcd(6, 0)`, which returns 6.",
        "In `main`, read `a` and `b` with `int(input())`, one per line, and print `'GCD:'` and `gcd(a, b)` with one `print`.",
    ],
    "answer": b64(gcd),
    "answerNote": "For positive `b`, the remainder is at least zero and less than `b`. The second argument therefore decreases until it reaches zero. The base call returns 6 in the trace. Every waiting call returns that same value."}
assert [c["expected"] for c in E["gcd"]["cases"][:2]] == ["GCD: 6", "GCD: 7"]

TF = lambda value: accept(value, value.lower(), placeholder="True/False", width="6rem")
E["gcd-trace"] = {"type": "table", "xp": 1, "blanks": {
    "c1": accept("gcd(48, 18)", "gcd(48,18)", width="9rem", placeholder="call", show="gcd(48, 18)"),
    "c2": accept("gcd(18, 12)", "gcd(18,12)", width="9rem", placeholder="call", show="gcd(18, 12)"),
    "c3": accept("gcd(12, 6)", "gcd(12,6)", width="9rem", placeholder="call", show="gcd(12, 6)"),
    "c4": accept("gcd(6, 0)", "gcd(6,0)", width="9rem", placeholder="call", show="gcd(6, 0)"),
    "b1": TF("False"), "b2": TF("False"), "b3": TF("False"), "b4": TF("True"),
    "v1": accept("6", placeholder="value", width="5rem"), "v2": accept("6", placeholder="value", width="5rem"),
    "v3": accept("6", placeholder="value", width="5rem"), "v4": accept("6", placeholder="value", width="5rem"),
}}
E["gcd-why"] = short("For positive `b`, the remainder is at least zero and less than `b`. "
                     "The second argument therefore decreases until it reaches zero.\n\n"
                     "The base call returns 6 in the trace. Every waiting call returns that same value.",
                     placeholder="Why a positive second argument gets closer to zero…")

# ---------------------------------------------------------------- 2 Total until blank
total = """def read_total():
    line = input()
    if line == "":
        return 0.0
    number = float(line)
    return number + read_total()

def main():
    total = read_total()
    print(f'Total: {total:.2f}')

if __name__ == '__main__':
    main()
"""
total_ns = namespace(total)
# Direct calls of read_total with input() fed from a list, as the check makes them.
def feed(lines):
    import builtins
    answers, saved = list(lines), builtins.input
    builtins.input = lambda prompt="": answers.pop(0)
    try:
        return total_ns["read_total"]()
    finally:
        builtins.input = saved
FEEDS = [[""], ["4.5", "0", "-1.25", ""], ["0", ""], ["0", "5", ""], ["5", "-7.5", ""], ["2", "3", "4", ""], ["-1000", ""], ["1000"] * 80 + [""]]
FEED_WANT = [feed(f) for f in FEEDS]
assert FEED_WANT[:2] == [0.0, 3.25] and all(type(v) is float for v in FEED_WANT)
EIGHTY = ["12.5", "-7.25"] * 40 + [""]
E["total"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 14,
    "starter": "def read_total():\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    "cases": input_cases(total, ("Example 1: typed 4.5, 0, -1.25, blank", ["4.5", "0", "-1.25", ""]),
                         ("Example 2: typed blank", [""]),
                         ("Typed 0, 5, blank", ["0", "5", ""]),
                         ("Typed 5, -7.5, blank", ["5", "-7.5", ""]),
                         ("Typed -1000, blank", ["-1000", ""]),
                         ("Typed 80 numbers (12.5 and -7.25 in turn), blank", EIGHTY),
                         ("Typed 1000 eighty times, blank", ["1000"] * 80 + [""])),
    "check": FN + f'''import builtins as _builtins
_fn("read_total")
_fn("main")
_recursive("read_total")
_no_loops()
_no_global()
assert len(_calls_in("read_total", "input")) == 1, "Read exactly one line in each call: use one input() in read_total."
assert not _calls_in("read_total", "print"), "read_total returns the total and does not print. Print in main."
assert len(_calls_in("main", "read_total")) == 1, "In main, call read_total() once and print the total it returns."
def _fed(_lines):
    _answers = list(_lines)
    def _input(prompt=""):
        if not _answers:
            raise AssertionError("read_total() kept reading after the blank line. Return 0.0 at the blank line without another call.")
        return _answers.pop(0)
    _saved = _builtins.input
    _builtins.input = _input
    try:
        _value, _printed = _call("read_total")
    finally:
        _builtins.input = _saved
    _shown = ", ".join(repr(_l) for _l in _lines)
    assert not _printed, "read_total returns the total and does not print. Print in main."
    assert _value is not None, "With the lines " + _shown + ", read_total() returned None. Return the total from each call."
    return _value, _shown
for _lines, _want in zip({FEEDS!r}, {FEED_WANT!r}):
    _value, _shown = _fed(_lines)
    assert isinstance(_value, float) and abs(_value - _want) <= 1e-9 * max(1, abs(_want)), "With the lines " + _shown[:60] + ", read_total() should return " + repr(_want) + ", not " + repr(_value) + "."
''' + "_guard()\n",
    "hints": [
        "Each call of `read_total` starts with `line = input()`. If `line == \"\"`, return `0.0` without another call.",
        "Otherwise convert the line with `number = float(line)` and return `number + read_total()`. The recursive call reads the next line. For the lines 4.5, 0, -1.25 and a blank line, the fourth call returns `0.0` first.",
        "In `main`, call `read_total()` once and print `f'Total: {total:.2f}'`. The waiting calls return -1.25, -1.25, and 3.25, so the program prints `Total: 3.25`.",
    ],
    "answer": b64(total),
    "answerNote": "The calls read `4.5`, `0`, `-1.25`, and a blank line, in that order. The fourth call returns `0.0` first. The waiting calls then return `-1.25`, `-1.25`, and `3.25`. Each call has its own `number` in its own frame. The earlier frame keeps its number while it waits for the later call."}
assert [c["expected"] for c in E["total"]["cases"][:2]] == ["Total: 3.25", "Total: 0.00"]

E["total-why"] = short("The calls read `4.5`, `0`, `-1.25`, and a blank line, in that order. The fourth call returns `0.0` first. The waiting calls then return `-1.25`, `-1.25`, and `3.25`.\n\n"
                       "Each call has its own `number` in its own frame. The earlier frame keeps its number while it waits for the later call.",
                       rows=6, placeholder="The line read by each call… Which call supplies the first returned answer… Why a new call does not erase its caller's number…")

# ---------------------------------------------------------------- 3 Square root by better guesses
root = """def square_root(n, guess=1.0):
    if abs(guess * guess - n) <= 1e-12:
        return guess
    better = (guess + n / guess) / 2
    return square_root(n, better)

def main():
    n = float(input())
    print(f'Root: {square_root(n):.6f}')

if __name__ == '__main__':
    main()
"""
root_ns = namespace(root)
assert abs(root_ns["square_root"](2) - 1.414213562373095) < 1e-15 and root_ns["square_root"](1) == 1.0
assert "RecursionError" in run(root.replace("1e-12", "1e-30") + "\nsquare_root(2)\n", ["2"], ok=False)[1]
ROOT_CALLS = [(1,), (2,), (4,), (9,), (10,), (50.5,), (100,), (2, 2.0), (9, 3.0), (100, 50.0), (2, 0.5), (1, 1.0), (36, 0.001)]
E["root"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 12,
    "starter": "def square_root(n, guess=1.0):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    "cases": input_cases(root, ("Example 1: typed 2", ["2"]), ("Example 2: typed 1", ["1"]), ("Typed 4", ["4"]),
                         ("Typed 10", ["10"]), ("Typed 50.5", ["50.5"]), ("Typed 100", ["100"])),
    "check": FN + '''_f = _fn("square_root", "n", "guess")
assert _f.__defaults__ == (1.0,), "Give guess the default value 1.0 and give n no default: def square_root(n, guess=1.0)."
_fn("main")
_recursive("square_root")
_no_loops()
assert _calls_in("square_root", "abs"), "Find the error with abs(guess * guess - n)."
assert any(isinstance(n, ast.Constant) and n.value == 1e-12 for n in _body("square_root")), "Use the tolerance 1e-12 in the submitted program."
_m = _calls_in("main", "square_root")
assert _m and all(len(c.args) == 1 and not c.keywords for c in _m), "In main, call square_root(n) with one argument so it uses the default guess."
''' + "".join(f"_returns('square_root', {a!r}, {root_ns['square_root'](*a)!r})\n" for a in ROOT_CALLS) + "_guard()\n",
    "hints": [
        "Write the header as `def square_root(n, guess=1.0):`. The base case is `if abs(guess * guess - n) <= 1e-12:`, which returns `guess`. For `n = 1` the first guess already has zero error.",
        "Otherwise compute `better = (guess + n / guess) / 2` and return `square_root(n, better)`. For `n = 2` the guesses are 1.0, 1.5, 1.4166..., and so on.",
        "In `main`, read `n` with `float(input())` and print `f'Root: {square_root(n):.6f}'`. For 2 that prints `Root: 1.414214`.",
    ],
    "answer": b64(root),
    "answerNote": "For 1, the first guess satisfies the base case. For 2, the returned guess is about `1.414213562373095`. With tolerance `1e-30`, this calculation raises `RecursionError`. Floating-point rounding prevents the squared error from becoming that small. The guesses stop improving enough to reach the base case."}
assert [c["expected"] for c in E["root"]["cases"][:2]] == ["Root: 1.414214", "Root: 1.000000"]

E["root-why"] = short("With tolerance `1e-30`, this calculation raises `RecursionError`.\n\n"
                      "Floating-point rounding prevents the squared error from becoming that small. "
                      "The guesses stop improving enough to reach the base case.",
                      rows=5, placeholder="What happens with 1e-30… Why the base case cannot be reached…")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-21-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 21 Boss Problems",
    "short": "L21 bosses",
    "subtitle": "Problem solving with recursion: the recursive idea",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-21/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
