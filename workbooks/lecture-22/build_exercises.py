"""Build workbooks/lecture-22/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_22_SHARED_CONTENT.tex; model answers follow its \\solution{...}
text. Run from anywhere:

    python3 workbooks/lecture-22/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-22
"""
import base64, contextlib, io, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=(), ok=True):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""), capture_output=True, text=True)
    if ok:
        assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n"), p.stderr

def out(code, inputs=()):
    return run(code, inputs)[0]

def example(code, output=True):
    spec = {"type": "example", "code": code.rstrip("\n")}
    if output:
        spec["output"] = out(code)
    return spec

def accept(*values, width="5rem", placeholder="answer"):
    return {"accept": list(values), "placeholder": placeholder, "width": width}

def short(answer, xp=2, min_chars=15, rows=3, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

def namespace(code):
    ns = {"__name__": "lecture22"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    return ns

def printed(ns, name, *args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        ns[name](*args)
    return buffer.getvalue()

def trace(ns, name, *args):
    """Call ns[name] and record (input, depth, returned) for every call, in entry order."""
    original = ns[name]
    calls, depth = [], [0]
    def wrapper(*a):
        depth[0] += 1
        row = [a, depth[0], None]
        calls.append(row)
        row[2] = original(*a)
        depth[0] -= 1
        return row[2]
    ns[name] = wrapper
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            wrapper(*args)
    finally:
        ns[name] = original
    return [tuple(r) for r in calls]

E = {}

# ---------------------------------------------------------------- checks shared by the coding tasks
# A check runs after the student's program in a copy of its namespace. `_fn`
# finds a function the program defined and checks its parameters. `_call`
# calls it with its output captured. `_returns` compares a returned value and
# `_prints` compares what a call prints. `_self_calls` counts the calls a
# function makes to itself in its source, and `_no_loops` rejects for and
# while loops in a function.
FN = '''import types, io, contextlib, ast
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
    value, _ = _call(name, *args)
    call = _shown(name, args)
    if value is None:
        raise AssertionError(call + " returned None. Send the result back with return.")
    if isinstance(want, bool):
        ok = value is want
    else:
        ok = value == want and type(value) is type(want)
    assert ok, call + " should return " + repr(want) + ", not " + repr(value) + "."
def _lines(text):
    return ", ".join(text.rstrip("\\n").split("\\n")) if text.strip() else "nothing"
def _prints(name, args, want):
    _, got = _call(name, *args)
    call = _shown(name, args)
    assert got.rstrip("\\n").split("\\n") == want.rstrip("\\n").split("\\n"), call + " should print the lines " + _lines(want) + ", not " + _lines(got) + "."
def _body(name):
    for node in ast.parse(__source__).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return list(ast.walk(node))
    return []
def _calls_in(name, callee):
    return [n for n in _body(name) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == callee]
def _self_calls(name):
    return len(_calls_in(name, name))
def _no_loops(name):
    assert not any(isinstance(n, (ast.For, ast.While, ast.comprehension)) for n in _body(name)), "Use recursion and no loop in " + name + "."
'''

def returns(name, ns, *calls):
    """Check lines that compare each call's returned value with the model's."""
    return "".join(f"_returns({name!r}, {args!r}, {ns[name](*args)!r})\n" for args in calls)

def prints(name, ns, *calls):
    """Check lines that compare what each call prints with the model's output."""
    return "".join(f"_prints({name!r}, {args!r}, {printed(ns, name, *args)!r})\n" for args in calls)

def call_case(kind, name, ns, args):
    """Check-only case: one direct call, named after the call."""
    line = (prints if kind == "prints" else returns)(name, ns, args)
    return {"name": name + "(" + ", ".join(repr(a).replace("'", '"') for a in args) + ")", "check": line}

# ============================================================ 1. Printing before and after the call
visit = '''def visit(n):
    if n == 0:
        return
    print("enter", n)
    visit(n - 1)
    print("leave", n)

visit(2)
'''
E["ex-visit"] = example(visit)
assert E["ex-visit"]["output"] == "enter 2\nenter 1\nleave 1\nleave 2"
# The second listing has the trace table instead of an output block.
E["ex-visit-trace"] = example(visit, output=False)

# Checkpoint 1
cp1_starter = '''def show_digits(n):
    pass
'''
cp1_answer = '''def show_digits(n):
    if n >= 10:
        show_digits(n // 10)
    print(n % 10)
'''
cp1_ns = namespace(cp1_answer)
assert printed(cp1_ns, "show_digits", 407) == "4\n0\n7\n" and printed(cp1_ns, "show_digits", 7) == "7\n"
E["cp1"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": cp1_starter,
    "cases": [call_case("prints", "show_digits", cp1_ns, (n,)) for n in (7, 407, 10)],
    "check": FN + '''_fn("show_digits", "n")
_no_loops("show_digits")
assert _self_calls("show_digits") == 1, "Use one recursive call: show_digits calls itself once."
_ops = [type(n.op) for n in _body("show_digits") if isinstance(n, ast.BinOp)]
assert ast.FloorDiv in _ops and ast.Mod in _ops, "Use // 10 and % 10 to split the number into its digits."
''' + prints("show_digits", cp1_ns, *[(n,) for n in (1, 9, 70, 100, 1001, 2026, 90210)]),
    "answer": b64(cp1_answer),
    "answerNote": "The earlier digits print first. `407 // 10` is `40`. `407 % 10` is `7`. `show_digits(7)` prints just `7`."}

# ============================================================ 2. Recursion depth
factorial = '''def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

factorial(3)
'''
E["ex-factorial"] = example(factorial, output=False)
fact_ns = namespace(factorial)
assert [d for _, d, _ in trace(fact_ns, "factorial", 3)] == [1, 2, 3, 4]

# ============================================================ 3. Reading errors and checking progress
# The countdown(3) listing is shown as static code with its traceback excerpt:
# run, it prints 3 many times and raises RecursionError.
countdown_call = '''def countdown(n):
    if n == 0:
        return
    print(n)
    countdown(n)

countdown(3)
'''
stdout, stderr = run(countdown_call, ok=False)
assert "RecursionError: maximum recursion depth exceeded" in stderr and set(stdout.split("\n")) == {"3"}
assert 'line 7, in <module>' in stderr and 'line 5, in countdown' in stderr
countdown_bug = '''def countdown(n):
    if n == 0:
        return
    print(n)
    countdown(n)
'''
countdown_fix = '''def countdown(n):
    if n == 0:
        return
    print(n)
    countdown(n - 1)
'''
E["ex-countdown-bug"] = example(countdown_bug, output=False)
E["ex-countdown-fix"] = example(countdown_fix, output=False)
assert out(countdown_fix + "countdown(3)\n") == "3\n2\n1"

# ============================================================ 4. Base answers and missing returns
product = '''def product(n):
    if n == 0:
        return 0
    return n * product(n - 1)

print(product(3))
'''
E["ex-product"] = example(product)
assert E["ex-product"]["output"] == "0"
total_bug = '''def total(n):
    if n == 0:
        return 0
    total(n - 1)
'''
total_fix = '''def total(n):
    if n == 0:
        return 0
    return n + total(n - 1)
'''
E["ex-total-bug"] = example(total_bug, output=False)
E["ex-total-fix"] = example(total_fix, output=False)
assert out(total_fix + "print(total(3))\n") == "6"
total_trace = total_bug + '''
print(total(2))
'''
E["ex-total-trace"] = example(total_trace)
assert E["ex-total-trace"]["output"] == "None"
assert [(a[0], r) for a, _, r in trace(namespace(total_bug), "total", 2)] == [(2, None), (1, None), (0, 0)]

# ============================================================ 5. Palindrome helpers and stopping cases
wrapper = '''def is_palindrome(text):
    return palindrome_helper(
        text, 0, len(text) - 1)
'''
E["ex-is-palindrome"] = example(wrapper, output=False)

# Checkpoint 2
cp2_starter = '''def palindrome_helper(text, start, end):
    pass

def is_palindrome(text):
    return palindrome_helper(text, 0, len(text) - 1)
'''
cp2_answer = '''def palindrome_helper(text, start, end):
    if start >= end:
        return True
    if text[start] != text[end]:
        return False
    return palindrome_helper(
        text, start + 1, end - 1)

def is_palindrome(text):
    return palindrome_helper(text, 0, len(text) - 1)
'''
cp2_ns = namespace(cp2_answer)
assert [cp2_ns["is_palindrome"](w) for w in ("abba", "abc", "")] == [True, False, True]
E["cp2"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": cp2_starter,
    "cases": [call_case("returns", "is_palindrome", cp2_ns, (w,)) for w in ("abba", "abc", "")],
    "check": FN + '''_fn("palindrome_helper", "text", "start", "end")
_fn("is_palindrome", "text")
assert _calls_in("is_palindrome", "palindrome_helper"), "Keep is_palindrome as given: it calls palindrome_helper(text, 0, len(text) - 1)."
_no_loops("palindrome_helper")
assert _self_calls("palindrome_helper") == 1, "Use one recursive call: palindrome_helper calls itself once."
''' + returns("palindrome_helper", cp2_ns, ("abba", 0, 3), ("abba", 1, 2), ("abba", 2, 1), ("abc", 0, 2), ("", 0, -1), ("abca", 1, 2), ("xabay", 1, 3))
      + returns("is_palindrome", cp2_ns, *[(w,) for w in ("a", "ab", "aa", "aba", "abca", "racecar", "robot", "level", "abcba", "abccba", "abcdba")]),
    "answer": b64(cp2_answer),
    "answerNote": "Each recursive call moves both indices inward. A mismatch stops the check immediately. "
                  "The helper's Boolean answer returns through the wrapper."}

# ============================================================ 6. Tracing the palindrome helper
helper_trace = '''def palindrome_helper(
        text, start, end):
    if start >= end:
        return True
    if text[start] != text[end]:
        return False
    return palindrome_helper(
        text, start + 1, end - 1)

'''
trace_abba = helper_trace + 'palindrome_helper("abba", 0, 3)\n'
trace_abca = helper_trace + 'palindrome_helper("abca", 0, 3)\n'
E["ex-trace-abba"] = example(trace_abba, output=False)
E["ex-trace-abca"] = example(trace_abca, output=False)
helper_ns = namespace(helper_trace)
assert [(a[1], a[2], r) for a, _, r in trace(helper_ns, "palindrome_helper", "abba", 0, 3)] == [(0, 3, True), (1, 2, True), (2, 1, True)]
assert [(a[1], a[2], r) for a, _, r in trace(helper_ns, "palindrome_helper", "abca", 0, 3)] == [(0, 3, False), (1, 2, False)]

# ============================================================ 7. Skipping nonletters
sentence = '''def sentence_helper(text, start, end):
    if start >= end:
        return True
    first = text[start]
    last = text[end]
    if not first.isalpha():
        return sentence_helper(text, start + 1, end)
    if not last.isalpha():
        return sentence_helper(text, start, end - 1)
    if first.lower() != last.lower():
        return False
    return sentence_helper(text, start + 1, end - 1)
'''
E["ex-sentence"] = example(sentence, output=False)
panama = "A man, a plan, a canal, Panama!"
assert namespace(sentence)["sentence_helper"](panama, 0, len(panama) - 1) is True
sentence_trace = '''def sentence_helper(text, start, end):
    if start >= end:
        return True
    first = text[start]
    last = text[end]
    if not first.isalpha():
        return sentence_helper(
            text, start + 1, end)
    if not last.isalpha():
        return sentence_helper(
            text, start, end - 1)
    if first.lower() != last.lower():
        return False
    return sentence_helper(
        text, start + 1, end - 1)
'''
E["ex-sentence-trace"] = example(sentence_trace, output=False)
assert [(a[1], a[2], r) for a, _, r in trace(namespace(sentence_trace), "sentence_helper", " A,ba!", 0, 5)] == \
    [(0, 5, True), (1, 5, True), (1, 4, True), (2, 3, True), (3, 3, True)]

# ============================================================ 8. Two recursive calls
fib = '''def fib(n):
    if n <= 1:
        return n
    left = fib(n - 1)
    right = fib(n - 2)
    return left + right
'''
E["ex-fib"] = example(fib, output=False)
fib_trace = fib + '''
print(fib(3))
'''
# The workbook shows the trace table for this listing, not an output block.
E["ex-fib-trace"] = example(fib_trace, output=False)
assert out(fib_trace) == "2"
assert [(a[0], d, r) for a, d, r in trace(namespace(fib), "fib", 3)] == [(3, 1, 2), (2, 2, 1), (1, 3, 1), (0, 3, 0), (1, 2, 1)]

# Checkpoint 3
cp3_starter = '''def ways(n):
    pass
'''
cp3_answer = '''def ways(n):
    if n <= 1:
        return 1
    one_step = ways(n - 1)
    two_steps = ways(n - 2)
    return one_step + two_steps
'''
cp3_ns = namespace(cp3_answer)
assert [cp3_ns["ways"](n) for n in (0, 2, 3)] == [1, 2, 3]
E["cp3"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": cp3_starter,
    "cases": [call_case("returns", "ways", cp3_ns, (n,)) for n in (0, 2, 3)],
    "check": FN + '''_fn("ways", "n")
_no_loops("ways")
assert _self_calls("ways") == 2, "Use two recursive calls in ways for the larger inputs."
''' + returns("ways", cp3_ns, *[(n,) for n in range(1, 13)]),
    "answer": b64(cp3_answer),
    "answerNote": "A first step of 1 leaves `n - 1` stairs. A first step of 2 leaves `n - 2` stairs. "
                  "The groups have different first steps, so add their counts. "
                  "`ways(0) = 1`, `ways(2) = 2`, and `ways(3) = 3`."}

# ============================================================ 9. Tests near the stopping points
assert printed(cp1_ns, "show_digits", 10) == "1\n0\n"
assert [cp2_ns["is_palindrome"](w) for w in ("", "a", "ab")] == [True, True, False]
assert namespace(fib)["fib"](2) == 1 and cp3_ns["ways"](0) == 1

# ============================================================ Coding Practice
# 1. Trace an expression
adjust = '''def adjust(n):
    if n == 0:
        return 2
    return 3 * adjust(n - 1) - 1

print((adjust(2) - adjust(1)) * adjust(0))
'''
assert out(adjust) == "18"
adjust_ns = namespace(adjust)
ADJUST = trace(adjust_ns, "adjust", 2) + trace(adjust_ns, "adjust", 1) + trace(adjust_ns, "adjust", 0)
assert [(a[0], d, r) for a, d, r in ADJUST] == [(2, 1, 14), (1, 2, 5), (0, 3, 2), (1, 1, 5), (0, 2, 2), (0, 1, 2)]
p1_blanks = {}
for i, (a, d, r) in enumerate(ADJUST, 1):
    p1_blanks[f"in{i}"] = accept(str(a[0]), placeholder="input")
    p1_blanks[f"d{i}"] = accept(str(d), placeholder="depth")
    p1_blanks[f"r{i}"] = accept(str(r), placeholder="value")
E["p1-trace"] = {"type": "table", "xp": 1, "blanks": p1_blanks}
E["p1-output"] = short("`18`\n\nThe three calls in the printed expression return 14, 5, and 2. "
                       "The expression is (14 − 5) × 2. The maximum depth is 3.",
                       min_chars=2, rows=3, placeholder="The printed output, and how the returned values give it…")

# 2. Count branching calls
branch = '''def branch(n):
    if n == 0:
        return 1
    left = branch(n - 1)
    right = branch(n - 1)
    return 1 + left + right
'''
branch_ns = namespace(branch)
p2_blanks = {}
for n in range(3):
    rows = trace(branch_ns, "branch", n)
    p2_blanks[f"c{n}"] = accept(str(rows[0][2]), placeholder="count")
    p2_blanks[f"d{n}"] = accept(str(max(d for _, d, _ in rows)), placeholder="depth")
assert [p2_blanks[f"c{n}"]["accept"][0] for n in range(3)] == ["1", "3", "7"]
assert [p2_blanks[f"d{n}"]["accept"][0] for n in range(3)] == ["1", "2", "3"]
E["p2"] = {"type": "table", "xp": 1, "blanks": p2_blanks}
BRANCH = trace(branch_ns, "branch", 2)
assert [(a[0], d, r) for a, d, r in BRANCH] == [(2, 1, 7), (1, 2, 3), (0, 3, 1), (0, 3, 1), (1, 2, 3), (0, 3, 1), (0, 3, 1)]
p2t_blanks = {}
for i, (a, d, r) in enumerate(BRANCH, 1):
    p2t_blanks[f"in{i}"] = accept(str(a[0]), placeholder="input")
    p2t_blanks[f"d{i}"] = accept(str(d), placeholder="depth")
    p2t_blanks[f"r{i}"] = accept(str(r), placeholder="count")
E["p2-trace"] = {"type": "table", "xp": 1, "blanks": p2t_blanks}

# 3. Smallest letter
smallest = '''def smallest_letter(text):
    if len(text) == 1:
        return text
    smaller = smallest_letter(text[1:])
    if text[0] < smaller:
        return text[0]
    return smaller
'''
small_ns = namespace(smallest)
E["p3"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": "def smallest_letter(text):\n    pass\n",
    "cases": [call_case("returns", "smallest_letter", small_ns, (w,)) for w in ("m", "cabin", "zoo")],
    "check": FN + '''_fn("smallest_letter", "text")
_no_loops("smallest_letter")
assert _self_calls("smallest_letter") == 1, "Use one recursive call: smallest_letter calls itself once."
assert not any(isinstance(n, ast.Call) and ((isinstance(n.func, ast.Name) and n.func.id in ("sorted", "min", "max"))
               or (isinstance(n.func, ast.Attribute) and n.func.attr == "sort")) for n in _body("smallest_letter")), "Compare the letters yourself with <. Do not use sorted, sort, min, or max."
assert any(isinstance(n, ast.Compare) and any(isinstance(o, ast.Lt) for o in n.ops) for n in _body("smallest_letter")), "Compare letters with <."
''' + returns("smallest_letter", small_ns, *[(w,) for w in ("aaa", "zyx", "z", "az", "za", "banana", "recursion", "zyxwvutsrqponmlkjihgfedcba", "qwerty")]),
    "answer": b64(smallest),
    "answerNote": "A one-letter word returns its only letter. Each larger call compares its first letter with the smallest letter in the rest of the word."}

# 4. Lowercase a selected range
lowercase = '''def lowercase_part(text, start, end):
    if start > end:
        return ""
    return text[start].lower() + lowercase_part(
        text, start + 1, end)

def lowercase_text(text):
    return lowercase_part(text, 0, len(text) - 1)
'''
lower_ns = namespace(lowercase)
E["p4"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": "def lowercase_part(text, start, end):\n    pass\n\ndef lowercase_text(text):\n    pass\n",
    "cases": [call_case("returns", "lowercase_part", lower_ns, ("AB-CD", 1, 3)),
              call_case("returns", "lowercase_text", lower_ns, ("Shop!",)),
              call_case("returns", "lowercase_text", lower_ns, ("",))],
    "check": FN + '''_fn("lowercase_part", "text", "start", "end")
_fn("lowercase_text", "text")
_no_loops("lowercase_part")
_no_loops("lowercase_text")
assert _self_calls("lowercase_part") == 1, "Use one recursive call in the helper: lowercase_part calls itself once."
assert _calls_in("lowercase_text", "lowercase_part"), "In lowercase_text, call the helper lowercase_part for the whole string."
for _n in ast.walk(ast.parse(__source__)):
    if isinstance(_n, ast.Call) and isinstance(_n.func, ast.Attribute) and _n.func.attr == "lower":
        _on = _n.func.value
        assert isinstance(_on, ast.Subscript) and not isinstance(_on.slice, ast.Slice), "Use lower() on one character at a time, such as text[start].lower(). Do not use it on the whole string or on a slice."
''' + returns("lowercase_part", lower_ns, ("", 0, -1), ("X", 0, 0), ("AB", 1, 0), ("HeLLo World", 0, 10), ("HeLLo World", 2, 6), ("ABC", 2, 2))
      + returns("lowercase_text", lower_ns, *[(w,) for w in ("aB 7!", "ABC", "x", "Hello, World!", "MIXED case 123")]),
    "answer": b64(lowercase),
    "answerNote": "The wrapper chooses the whole range. The helper adds one lowercase character to the answer for the rest of that range."}

# 5. Multiply by halving
multiply = '''def multiply(a, b):
    if b == 0:
        return 0
    half = multiply(a, b // 2)
    doubled = half + half
    if b % 2 == 0:
        return doubled
    return doubled + a
'''
mult_ns = namespace(multiply)
assert all(mult_ns["multiply"](a, b) == a * b for a in range(15) for b in range(40))
E["p5"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": "def multiply(a, b):\n    pass\n",
    "cases": [call_case("returns", "multiply", mult_ns, (7, b)) for b in (0, 4, 5)],
    "check": FN + '''_fn("multiply", "a", "b")
_no_loops("multiply")
assert not any(isinstance(n, (ast.BinOp, ast.AugAssign)) and isinstance(n.op, (ast.Mult, ast.Div)) for n in ast.walk(ast.parse(__source__))), "Build the answer with addition. Do not use * or /."
assert _self_calls("multiply") == 1, "Use one recursive call in multiply: find the product with b // 2 once and reuse it."
''' + returns("multiply", mult_ns, (0, 8), (3, 1), (0, 0), (1, 1), (12, 13), (1, 100), (25, 64), (9, 1000), (123, 77)),
    "answer": b64(multiply),
    "answerNote": "For 4, doubling the product with 2 supplies all four copies of `a`. For 5, one more copy is needed."}

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-22",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 22 Workbook",
    "subtitle": "Tracing recursion and recursive helpers",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-22/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
