"""Build workbooks/lecture-21/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_21_SHARED_CONTENT.tex; model answers follow its \\solution{...}
text. Run from anywhere:

    python3 workbooks/lecture-21/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-21
"""
import base64, contextlib, io, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, ok=True):
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    if ok:
        assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n"), p.stderr

def out(code):
    return run(code)[0]

def example(code, output=True):
    spec = {"type": "example", "code": code.rstrip("\n")}
    if output:
        spec["output"] = out(code)
    return spec

def accept(*values, width="8rem", placeholder="answer", show=None):
    spec = {"accept": list(values), "placeholder": placeholder, "width": width}
    if show is not None:
        spec["show"] = show
    return spec

def short(answer, xp=2, min_chars=15, rows=3, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

def namespace(code):
    ns = {"__name__": "lecture21"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    return ns

E = {}

# ---------------------------------------------------------------- checks shared by the coding tasks
# A check runs after the student's program in the same namespace (a copy of it).
# `_fn` finds a function the program defined and checks its parameters. `_call`
# calls it with its output captured. `_returns` compares a returned value with
# the model's. `_recursive` asks for exactly one call of the function inside its
# own body, and `_no_loops` rejects for and while loops anywhere in the file.
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
        raise AssertionError(call + " returned None. Send the result back with return.")
    if isinstance(want, bool):
        ok = value is want
    elif isinstance(want, (int, float)):
        ok = isinstance(value, (int, float)) and not isinstance(value, bool) and abs(value - want) <= 1e-9 * max(1, abs(want))
    else:
        ok = value == want and type(value) is type(want)
    assert ok, call + " should return " + repr(want) + ", not " + repr(value) + "."
def _body(name):
    for node in ast.parse(__source__).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return list(ast.walk(node))
    return []
def _defs():
    return [n for n in ast.parse(__source__).body if isinstance(n, ast.FunctionDef)]
def _recursive(name):
    _n = len([n for n in _body(name) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name])
    assert _n >= 1, "Make " + name + " recursive: call " + name + " inside its own body with a smaller input."
    assert _n == 1, "Use one recursive call: call " + name + " once inside its own body, not " + str(_n) + " times."
def _no_loops():
    assert not any(isinstance(n, (ast.For, ast.While, ast.comprehension)) for n in ast.walk(ast.parse(__source__))), "Use recursion and no loops. Remove the for or while loop."
'''

def returns(name, ns, *calls):
    """Check lines that compare each call's returned value with the model's."""
    return "".join(f"_returns({name!r}, {args!r}, {ns[name](*args)!r})\n" for args in calls)

def call_case(name, ns, args):
    """A check-only case for one direct call, named after the call and its result."""
    want = ns[name](*args)
    shown = name + "(" + ", ".join(repr(a) for a in args) + ")"
    return {"name": f"{shown} returns {want!r}", "check": returns(name, ns, args)}

# ============================================================ 1. The recursive idea
# Prose, a picture and the six-stage table only.

# ============================================================ 2. Triangle numbers
triangle_doc = '''def triangle(n):
    """Return the sum from 1 to n."""
    if n == 0:
        return 0
    return n + triangle(n - 1)

print(triangle(4))
'''
E["ex-triangle"] = example(triangle_doc)
assert E["ex-triangle"]["output"] == "10"

triangle3 = '''def triangle(n):
    if n == 0:
        return 0
    return n + triangle(n - 1)

print(triangle(3))
'''
# The trace table below the listing gives the answer, so the console starts empty.
E["ex-triangle3"] = example(triangle3, output=False)
assert out(triangle3) == "6"
tri_ns = namespace(triangle3)
assert [tri_ns["triangle"](n) for n in (3, 2, 1, 0)] == [6, 3, 1, 0]

# Checkpoint 1
squares = '''def sum_squares(n):
    if n == 0:
        return 0
    return n * n + sum_squares(n - 1)
'''
squares_ns = namespace(squares)
assert [squares_ns["sum_squares"](n) for n in (0, 1, 3)] == [0, 1, 14]
E["cp1"] = {"type": "code", "xp": 5, "minLines": 6,
    "starter": "def sum_squares(n):\n    pass\n",
    "cases": [call_case("sum_squares", squares_ns, (n,)) for n in (0, 1, 3)],
    "check": FN + '''_fn("sum_squares", "n")
_recursive("sum_squares")
_no_loops()
''' + returns("sum_squares", squares_ns, *[(n,) for n in range(11)]),
    "answer": b64(squares),
    "answerNote": "The smaller call adds the squares up to `n - 1`. This call adds `n * n`. "
                  "`sum_squares(0)` returns `0`, `sum_squares(1)` returns `1`, and `sum_squares(3)` returns `14`."}

# ============================================================ 3. Printing a triangle
print_triangle = '''def print_triangle(n):
    if n == 0:
        return
    print_triangle(n - 1)
    print("[]" * n)

print_triangle(3)
'''
E["ex-print-triangle"] = example(print_triangle)
assert E["ex-print-triangle"]["output"] == "[]\n[][]\n[][][]"

# ============================================================ 4. Factorial
factorial_doc = '''def factorial(n):
    """Return n factorial."""
    if n == 0:
        return 1
    return n * factorial(n - 1)

print(factorial(4))
'''
E["ex-factorial"] = example(factorial_doc)
assert E["ex-factorial"]["output"] == "24"

# ============================================================ 5. One stack frame per call
factorial3 = '''def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

print(factorial(3))
'''
# The trace table below the listing gives the answer, so the console starts empty.
E["ex-factorial3"] = example(factorial3, output=False)
assert out(factorial3) == "6"
fact_ns = namespace(factorial3)
assert [fact_ns["factorial"](n) for n in (3, 2, 1, 0, 4)] == [6, 2, 1, 1, 24]

# Checkpoint 2
power = '''def power(base, n):
    if n == 0:
        return 1
    return base * power(base, n - 1)
'''
power_ns = namespace(power)
assert [power_ns["power"](2, n) for n in (0, 1, 4)] == [1, 2, 16]
E["cp2"] = {"type": "code", "xp": 5, "minLines": 6,
    "starter": "def power(base, n):\n    pass\n",
    "cases": [call_case("power", power_ns, (2, n)) for n in (0, 1, 4)],
    "check": FN + '''_fn("power", "base", "n")
_recursive("power")
_no_loops()
assert not any(isinstance(n, ast.Pow) or (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "pow")
               for n in ast.walk(ast.parse(__source__))), "Build the power with multiplication and one recursive call. Do not use ** or pow."
''' + returns("power", power_ns, *[(b, n) for b in (1, 2, 3, 10) for n in (0, 1, 2, 5)]),
    "answer": b64(power),
    "answerNote": "The smaller call supplies `n - 1` factors. Multiply by `base` to add one more factor. "
                  "`power(2, 0)` returns `1`, `power(2, 1)` returns `2`, and `power(2, 4)` returns `16`."}

# ============================================================ 6. Reaching the base case
broken = '''def broken(n):
    return n + broken(n - 1)
'''
wrong_way = '''def wrong_way(n):
    if n == 0:
        return 0
    return n + wrong_way(n + 1)
'''
# Both listings only define a function, so running them prints nothing.
E["ex-broken"] = example(broken, output=False)
E["ex-wrong-way"] = example(wrong_way, output=False)
assert "RecursionError" in run(broken + "broken(2)\n", ok=False)[1]
assert "RecursionError" in run(wrong_way + "wrong_way(2)\n", ok=False)[1]

# ============================================================ 7. Removing a digit
# Checkpoint 3
digits = '''def digit_sum(n):
    if n < 10:
        return n
    return digit_sum(n // 10) + n % 10
'''
digits_ns = namespace(digits)
assert [digits_ns["digit_sum"](n) for n in (0, 7, 407)] == [0, 7, 11]
assert 407 // 10 == 40 and 407 % 10 == 7
E["cp3"] = {"type": "code", "xp": 5, "minLines": 6,
    "starter": "def digit_sum(n):\n    pass\n",
    "cases": [call_case("digit_sum", digits_ns, (n,)) for n in (0, 7, 407)],
    "check": FN + '''_fn("digit_sum", "n")
_recursive("digit_sum")
_no_loops()
assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "str" for n in _body("digit_sum")), "Remove a digit with // 10 and find it with % 10. Do not convert the number to a string."
''' + returns("digit_sum", digits_ns, *[(n,) for n in (0, 5, 9, 10, 19, 40, 99, 100, 407, 9999, 12345, 1000000)]),
    "answer": b64(digits),
    "answerNote": "`n // 10` removes one digit. The recursive call finds the sum of the digits that remain. "
                  "`digit_sum(0)` returns `0`, `digit_sum(7)` returns `7`, and `digit_sum(407)` returns `11`."}

# ============================================================ 8. Shortening a string
reverse = '''def reverse(text):
    if len(text) <= 1:
        return text
    return reverse(text[1:]) + text[0]

print(reverse("CAT"))
'''
E["ex-reverse"] = example(reverse)
assert E["ex-reverse"]["output"] == "TAC"
assert namespace(reverse)["reverse"]("AT") == "TA"

# ============================================================ Coding Practice
# 1. Explain the stopping point
E["p1"] = short("Recursion solves a problem using a call to the same function on a smaller input. "
                "A base case supplies an answer directly.\n\n"
                "Calls that never reach a base case keep making more calls without finishing. "
                "Python eventually raises `RecursionError`.",
                min_chars=40, rows=5, placeholder="Recursion… Calls that continue without reaching a base case… What Python raises…")

# 2. Repeated text
repeat = '''def repeat_text(text, count):
    if count == 0:
        return ""
    return text + repeat_text(text, count - 1)
'''
repeat_ns = namespace(repeat)
assert [repeat_ns["repeat_text"]("ab", c) for c in (0, 1, 3)] == ["", "ab", "ababab"]
E["p2-table"] = {"type": "table", "xp": 1, "blanks": {
    "r0": accept('""', "''", placeholder="string", show='""'),
    "r1": accept('"ab"', "'ab'", "ab", placeholder="string", show='"ab"'),
    "r3": accept('"ababab"', "'ababab'", "ababab", width="9rem", placeholder="string", show='"ababab"'),
}}
E["p2"] = short("The base case is `count == 0`. It returns the empty string.\n\n"
                "The smaller call returns one fewer copy of `text`. Adding `text` at the front supplies the missing copy. "
                "The recursive argument decreases by 1 until it reaches 0.",
                min_chars=40, rows=5, placeholder="The base case and its returned value… How the recursive case uses the smaller answer…")

# 3. A product of digits
product = '''def digit_product(n):
    if n < 10:
        return n
    return digit_product(n // 10) * (n % 10)
'''
product_ns = namespace(product)
assert [product_ns["digit_product"](n) for n in (234, 23, 2, 204, 20)] == [24, 6, 2, 0, 0]
E["p3-trace"] = {"type": "table", "xp": 1, "blanks": {
    "c2": accept("digit_product(23)", width="11rem", placeholder="call"),
    "c3": accept("digit_product(2)", width="11rem", placeholder="call"),
    "v1": accept("6 × 4 = 24", "6 x 4 = 24", "6 * 4 = 24", "6*4=24", "6×4=24", "6x4=24", "24", placeholder="value", show="6 × 4 = 24"),
    "v2": accept("2 × 3 = 6", "2 x 3 = 6", "2 * 3 = 6", "2*3=6", "2×3=6", "2x3=6", "6", placeholder="value", show="2 × 3 = 6"),
    "v3": accept("2", placeholder="value"),
}}
E["p3"] = short("A single digit is the base case, including zero. Its product is that digit.\n\n"
                "For 204, the call for 20 multiplies 2 by 0. The call for 204 then multiplies 0 by 4, so it also returns 0.",
                min_chars=40, rows=5, placeholder="The base case and its answer… Why digit_product(204) returns zero…")

# 4. Largest digit
largest = '''def largest_digit(n):
    if n < 10:
        return n
    smaller = largest_digit(n // 10)
    last = n % 10
    if last > smaller:
        return last
    return smaller
'''
largest_ns = namespace(largest)
assert [largest_ns["largest_digit"](n) for n in (0, 7, 5832, 909)] == [0, 7, 8, 9]
E["p4"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": "def largest_digit(n):\n    pass\n",
    "cases": [call_case("largest_digit", largest_ns, (n,)) for n in (0, 7, 5832, 909)],
    "check": FN + '''_fn("largest_digit", "n")
_recursive("largest_digit")
_no_loops()
assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "str" for n in _body("largest_digit")), "Do not convert the number to a string. Use n // 10 and n % 10."
_ops = [type(n.op) for n in _body("largest_digit") if isinstance(n, ast.BinOp)]
assert ast.FloorDiv in _ops and ast.Mod in _ops, "Find the largest digit in n // 10, then compare it with n % 10."
''' + returns("largest_digit", largest_ns, *[(n,) for n in (0, 1, 9, 10, 19, 90, 123, 321, 5832, 909, 1000, 7007, 123456789, 987654321)]),
    "answer": b64(largest),
    "answerNote": "A single digit returns itself. Each larger call compares one digit with the largest digit already found in the remaining number."}

# 5. Letter score
score = '''def letter_score(text):
    if text == "":
        return 0
    value = 1
    if text[0] == "B":
        value = 3
    elif text[0] == "C":
        value = 5
    return value + letter_score(text[1:])
'''
score_ns = namespace(score)
assert [score_ns["letter_score"](t) for t in ("", "B", "CAB")] == [0, 3, 9]
E["p5"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": "def letter_score(text):\n    pass\n",
    "cases": [call_case("letter_score", score_ns, (t,)) for t in ("", "B", "CAB")],
    "check": FN + '''_fn("letter_score", "text")
_recursive("letter_score")
_no_loops()
assert "count" not in __code__, "Use the score of text[1:] to build the answer. Do not count the letters with count."
''' + returns("letter_score", score_ns, *[(t,) for t in ("", "A", "B", "C", "AA", "CAB", "BAC", "CCCCC", "ABCABC", "A" * 50 + "C" * 50)]),
    "answer": b64(score),
    "answerNote": "The empty string contributes zero. For a nonempty string, add the first letter's value to the score of the remaining text."}

# 6. Find a piece of text
contains = '''def contains(text, piece):
    if piece == "":
        return True
    if len(text) < len(piece):
        return False
    if text[:len(piece)] == piece:
        return True
    return contains(text[1:], piece)
'''
contains_ns = namespace(contains)
CONTAINS_SHOWN = [("banana", "nan"), ("banana", "nab"), ("", ""), ("", "a")]
assert [contains_ns["contains"](*a) for a in CONTAINS_SHOWN] == [True, False, True, False]
CONTAINS_MORE = [("abc", ""), ("abc", "abc"), ("abc", "abcd"), ("abc", "a"), ("abc", "c"), ("abc", "bc"), ("abc", "ac"),
                 ("aaab", "aab"), ("mississippi", "ssip"), ("mississippi", "sipx"), ("banana", "ana"), ("a", "a"), ("a", "b")]
E["p6"] = {"type": "code", "xp": 10, "minLines": 10,
    "starter": "def contains(text, piece):\n    pass\n",
    "cases": [call_case("contains", contains_ns, a) for a in CONTAINS_SHOWN],
    "check": FN + '''_fn("contains", "text", "piece")
_recursive("contains")
_no_loops()
_tree = ast.parse(__source__)
assert not any(isinstance(n, ast.Compare) and any(isinstance(o, (ast.In, ast.NotIn)) for o in n.ops) for n in ast.walk(_tree)), "Do not use in. Compare text[:len(piece)] with piece instead."
assert not any(isinstance(n, ast.Attribute) and n.attr in ("find", "count") for n in ast.walk(_tree)), "Do not use find or count. Compare text[:len(piece)] with piece instead."
assert any(isinstance(n, ast.Slice) for n in _body("contains")), "Use slicing: text[:len(piece)] for the start and text[1:] for the shorter text."
''' + returns("contains", contains_ns, *CONTAINS_SHOWN, *CONTAINS_MORE),
    "answer": b64(contains),
    "answerNote": "The empty piece succeeds immediately. A text that is too short fails immediately. "
                  "Every other call either finds a match at the start or searches the shorter text."}

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-21",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 21 Workbook",
    "subtitle": "Problem solving with recursion: the recursive idea",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-21/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
