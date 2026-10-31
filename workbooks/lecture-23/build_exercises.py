"""Build workbooks/lecture-23/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_23_SHARED_CONTENT.tex; model answers follow its \\solution{...}
text. Run from anywhere:

    python3 workbooks/lecture-23/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-23
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
    ns = {"__name__": "lecture23"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    return ns

E = {}

# ---------------------------------------------------------------- checks shared by the coding tasks
# A check runs after the student's program in a copy of its namespace.
# `_fn` finds a function and checks its parameters. `_call` calls it with its
# output captured. `_returns` compares a returned value with the model's.
# `_recursive` asks for a call of the function inside its own body (exactly
# `count` calls when given). `_loop_only` asks for a for or while loop and no
# call of any function defined in the file, so the loop version cannot reach
# recursion through another function. `_no_loops` rejects loops in one
# function. `_plain` rejects lists, dictionaries, sets, global, nonlocal,
# imports and decorators anywhere in the file.
FN = '''import types, io, contextlib, ast
_WORDS = ["empty parentheses", "one parameter", "two parameters", "three parameters", "four parameters", "five parameters"]
_TREE = ast.parse(__source__)
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
        raise AssertionError(call + " raised RecursionError. Check the base case and that every recursive call moves toward it.")
    if value is None:
        raise AssertionError(call + " returned None. Send the result back with return.")
    if isinstance(want, bool):
        ok = value is want
    elif isinstance(want, int):
        ok = isinstance(value, int) and not isinstance(value, bool) and value == want
    else:
        ok = value == want and type(value) is type(want)
    assert ok, call + " should return " + repr(want) + ", not " + repr(value) + "."
def _node(name):
    for node in _TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None
def _body(name):
    node = _node(name)
    return list(ast.walk(node)) if node else []
def _calls_in(name, callee):
    return [n for n in _body(name) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == callee]
def _defined():
    return [n.name for n in _TREE.body if isinstance(n, ast.FunctionDef)]
def _has_loop(name):
    return any(isinstance(n, (ast.For, ast.While, ast.comprehension)) for n in _body(name))
def _recursive(name, count=None):
    _n = len(_calls_in(name, name))
    assert _n >= 1, "Use recursion in " + name + ": call " + name + " inside its own body with a smaller input."
    if count == 1:
        assert _n == 1, "Use one recursive call: call " + name + " once inside its own body, not " + str(_n) + " times."
def _no_loops(name):
    assert not _has_loop(name), "Use recursion and no loops in " + name + ". Remove the for or while loop."
def _loop_only(name):
    assert _has_loop(name), "Use a loop in " + name + ": a for or while loop."
    _other = [c for c in _defined() if _calls_in(name, c)]
    assert not _other, "Use a loop with no recursion in " + name + ". Do not call " + _other[0] + " from it."
def _plain():
    for _n in ast.walk(_TREE):
        assert not isinstance(_n, (ast.List, ast.ListComp, ast.Dict, ast.DictComp, ast.Set, ast.SetComp)), "Do not use lists, dictionaries, or sets."
        assert not (isinstance(_n, ast.Call) and isinstance(_n.func, ast.Name) and _n.func.id in ("list", "dict", "set")), "Do not use lists, dictionaries, or sets."
        assert not isinstance(_n, (ast.Global, ast.Nonlocal)), "Do not use global or nonlocal. Pass values as arguments and return results."
        assert not isinstance(_n, (ast.Import, ast.ImportFrom)), "Do not import modules. Use only the operations in the statement."
        assert not (isinstance(_n, ast.FunctionDef) and _n.decorator_list), "Do not put a decorator on a function. Do not save earlier answers."
'''

def returns(name, ns, *calls):
    """Check lines that compare each call's returned value with the model's."""
    return "".join(f"_returns({name!r}, {args!r}, {ns[name](*args)!r})\n" for args in calls)

def call_case(name, ns, args):
    """A check-only case for one direct call, named after the call and its result."""
    want = ns[name](*args)
    shown = name + "(" + ", ".join(repr(a) for a in args) + ")"
    return {"name": f"{shown} returns {want!r}", "check": returns(name, ns, args)}

# ============================================================ 1. The same factorial problem, written two ways
factorial_rec = '''def factorial_rec(n):
    if n == 0:
        return 1
    return n * factorial_rec(n - 1)
'''
factorial_loop = '''def factorial_loop(n):
    result = 1
    for i in range(1, n + 1):
        result = result * i
    return result
'''
E["ex-factorial-rec"] = example(factorial_rec, output=False)
E["ex-factorial-loop"] = example(factorial_loop, output=False)
assert namespace(factorial_rec)["factorial_rec"](4) == 24 == namespace(factorial_loop)["factorial_loop"](4)
assert namespace(factorial_rec)["factorial_rec"](0) == 1 == namespace(factorial_loop)["factorial_loop"](0)

# ============================================================ 2. Frame cost and the problem's shape
# Prose and a picture of the frames only. A very large input reaches the depth limit.
assert "RecursionError" in run(factorial_rec + "factorial_rec(10000)\n", ok=False)[1]

# Checkpoint 1
squares = '''def squares_rec(n):
    if n == 0:
        return 0
    smaller = squares_rec(n - 1)
    return n * n + smaller

def squares_loop(n):
    total = 0
    for i in range(1, n + 1):
        total = total + i * i
    return total
'''
sq_ns = namespace(squares)
assert [sq_ns["squares_rec"](n) for n in (0, 3)] == [0, 14] == [sq_ns["squares_loop"](n) for n in (0, 3)]
E["cp1"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": "def squares_rec(n):\n    pass\n\ndef squares_loop(n):\n    pass\n",
    "cases": [call_case("squares_rec", sq_ns, (0,)), call_case("squares_rec", sq_ns, (3,)),
              call_case("squares_loop", sq_ns, (0,)), call_case("squares_loop", sq_ns, (3,))],
    "check": FN + '''_fn("squares_rec", "n")
_fn("squares_loop", "n")
_recursive("squares_rec")
_no_loops("squares_rec")
assert not _calls_in("squares_rec", "squares_loop"), "Use recursion in squares_rec. Do not call squares_loop from it."
_loop_only("squares_loop")
_plain()
''' + returns("squares_rec", sq_ns, *[(n,) for n in range(21)]) + returns("squares_loop", sq_ns, *[(n,) for n in range(21)]),
    "answer": b64(squares),
    "answerNote": "Both return 0 for 0 and 14 for 3."}
E["cp1-choice"] = short("Choose the loop for a large input. It uses one function frame. The recursive version reaches depth n + 1.",
                        min_chars=20, placeholder="Which version for a large input, and why…")

# ============================================================ 3. Naive Fibonacci and repeated work
fib = '''def fib(n):
    if n <= 1:
        return n
    left = fib(n - 1)
    right = fib(n - 2)
    return left + right
'''
E["ex-fib"] = example(fib, output=False)
fib_ns = namespace(fib)
assert [fib_ns["fib"](n) for n in range(8)] == [0, 1, 1, 2, 3, 5, 8, 13]

# ============================================================ 4. Tracing calls and comparing work with depth
fib_trace = fib + '''
print(fib(4))
'''
# The trace table beside the listing gives the answer, so the console starts empty.
E["ex-fib-trace"] = example(fib_trace, output=False)
assert out(fib_trace) == "3"
E["ex-fib-counts"] = example(fib, output=False)
# The call counts and peak depths in the table, counted by a copy that returns them.
def counted_fib(n):
    if n <= 1:
        return n, 1, 1
    a, ca, da = counted_fib(n - 1)
    b, cb, db = counted_fib(n - 2)
    return a + b, 1 + ca + cb, 1 + max(da, db)
assert counted_fib(4)[1] == 9
assert [counted_fib(n)[1:] for n in (10, 20)] == [(177, 10), (21891, 20)]
# fib(30) makes 2,692,537 calls: T(n) = 2 * fib(n + 1) - 1, with peak depth n.
assert 2 * fib_ns["fib"](31) - 1 == 2692537

# ============================================================ 5. Carrying Fibonacci values through a loop
# Prose only.

# Checkpoint 2
fib_loop = '''def fib_loop(n):
    a = 0
    b = 1
    for i in range(n):
        next_value = a + b
        a = b
        b = next_value
    return a
'''
fl_ns = namespace(fib_loop)
assert [fl_ns["fib_loop"](n) for n in (0, 1, 5)] == [0, 1, 5]
E["cp2"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": "def fib_loop(n):\n    pass\n",
    "cases": [call_case("fib_loop", fl_ns, (n,)) for n in (0, 1, 5)],
    "check": FN + '''_fn("fib_loop", "n")
_loop_only("fib_loop")
_plain()
''' + returns("fib_loop", fl_ns, *[(n,) for n in range(31)]) + returns("fib_loop", fl_ns, (100,)),
    "answer": b64(fib_loop),
    "answerNote": "The table follows one call, fib_loop(5). It returns 5 after five additions. Inputs 0 and 1 return 0 and 1. The loop uses one function frame."}

# ============================================================ 6. Towers of Hanoi and the three-disc moves
# Prose and numbered moves; section 7 prints the same seven moves.
HANOI_THREE = "\n".join(["Move 1 A to C", "Move 2 A to B", "Move 1 C to B", "Move 3 A to C",
                         "Move 1 B to A", "Move 2 B to C", "Move 1 A to C"])

# ============================================================ 7. Reading and tracing the Hanoi function
hanoi = '''def hanoi(n, source, target, spare):
    if n == 0:
        return
    hanoi(n - 1, source, spare, target)
    print("Move", n, source,
          "to", target)
    hanoi(n - 1, spare, target, source)

hanoi(3, "A", "C", "B")
'''
E["ex-hanoi"] = example(hanoi)
assert E["ex-hanoi"]["output"] == HANOI_THREE
hanoi_trace = '''def hanoi(n, source, target, spare):
    if n == 0:
        return
    hanoi(n - 1,
          source, spare, target)
    print("Move", n, source,
          "to", target)
    hanoi(n - 1,
          spare, target, source)
'''
E["ex-hanoi-trace"] = example(hanoi_trace, output=False)
assert out(hanoi_trace + 'hanoi(2, "A", "C", "B")\n') == "Move 1 A to B\nMove 2 A to C\nMove 1 B to C"

# ============================================================ 8. Counting the Hanoi moves
# Checkpoint 3
hanoi_moves = '''def hanoi_moves(n):
    if n == 0:
        return 0
    smaller = hanoi_moves(n - 1)
    return 2 * smaller + 1
'''
hm_ns = namespace(hanoi_moves)
assert [hm_ns["hanoi_moves"](n) for n in range(6)] == [0, 1, 3, 7, 15, 31]
E["cp3"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "def hanoi_moves(n):\n    pass\n",
    "cases": [call_case("hanoi_moves", hm_ns, (0,)), call_case("hanoi_moves", hm_ns, (3,))],
    "check": FN + '''_fn("hanoi_moves", "n")
_recursive("hanoi_moves", 1)
_no_loops("hanoi_moves")
assert not _calls_in("hanoi_moves", "print"), "hanoi_moves returns a number. It does not print the moves."
assert not any(isinstance(_n, ast.Pow) for _n in _body("hanoi_moves")), "Build the count from the smaller count with 2 * smaller + 1. Do not use **."
_plain()
''' + returns("hanoi_moves", hm_ns, *[(n,) for n in range(21)]) + '''_f = globals()["hanoi_moves"]
_g = _f.__globals__
_box = [0]
def _counting(n):
    _box[0] += 1
    return _f(n)
for _n in (3, 10):
    _box[0] = 0
    _g["hanoi_moves"] = _counting
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            _counting(_n)
    finally:
        _g["hanoi_moves"] = _f
    assert _box[0] == _n + 1, "hanoi_moves(" + str(_n) + ") made " + str(_box[0]) + " calls, not " + str(_n + 1) + ". Each call with n above 0 calls hanoi_moves(n - 1) once."
''',
    "answer": b64(hanoi_moves),
    "answerNote": "hanoi_moves(3) makes four calls and returns 7. Counting the moves needs far less work than printing all seven moves."}
E["cp3-calls"] = short("hanoi_moves(3) makes four calls and returns 7. Counting the moves needs far less work than printing all seven moves.",
                       min_chars=10, placeholder="How many calls for hanoi_moves(3)…")

# ============================================================ Coding Practice
# 1. Keep every other character
alternate_rec = '''def alternate_rec(text):
    if text == "":
        return ""
    return text[0] + alternate_rec(text[2:])
'''
E["ex-alternate-rec"] = example(alternate_rec, output=False)
alternate = '''def alternate_loop(text):
    result = ""
    for index in range(0, len(text), 2):
        result = result + text[index]
    return result
'''
al_ns = namespace(alternate)
ar_ns = namespace(alternate_rec)
TEXTS = [("abcdef",), ("x",), ("",), ("ab",), ("abc",), ("abcdefg",), ("hello world",), ("0123456789",)]
for args in TEXTS:
    assert al_ns["alternate_loop"](*args) == ar_ns["alternate_rec"](*args)
E["p1"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "def alternate_loop(text):\n    pass\n",
    "cases": [call_case("alternate_loop", al_ns, args) for args in (("abcdef",), ("x",), ("",))],
    "check": FN + '''_fn("alternate_loop", "text")
_loop_only("alternate_loop")
assert not _calls_in("alternate_loop", "alternate_rec"), "Use a loop with no recursion in alternate_loop. Do not call alternate_rec from it."
assert not any(isinstance(_n, ast.Slice) and _n.step is not None for _n in _body("alternate_loop")), "Do not use a slice with a step. Build the answer one character at a time."
_plain()
''' + returns("alternate_loop", al_ns, *TEXTS),
    "answer": b64(alternate),
    "answerNote": "The loop visits every even position once. For empty input, the loop makes no updates and the function returns the empty string."}

# 2. Count calls while shrinking
reduce_reading = '''def reduce_reading(n):
    if n <= 10:
        return n
    return reduce_reading(n // 3)
'''
E["ex-reduce"] = example(reduce_reading, output=False)
rr_ns = namespace(reduce_reading)
reading_calls = '''def reading_calls(n):
    if n <= 10:
        return 1
    return 1 + reading_calls(n // 3)
'''
rc_ns = namespace(reading_calls)
assert [rr_ns["reduce_reading"](n) for n in (0, 10, 11, 100)] == [0, 10, 3, 3]
assert [rc_ns["reading_calls"](n) for n in (0, 10, 11, 100)] == [1, 1, 2, 4]
E["p2-table"] = {"type": "table", "xp": 1, "blanks": {
    "r0": accept("0", placeholder="reading", width="5rem"), "c0": accept("1", placeholder="calls", width="5rem"),
    "r10": accept("10", placeholder="reading", width="5rem"), "c10": accept("1", placeholder="calls", width="5rem"),
    "r11": accept("3", placeholder="reading", width="5rem"), "c11": accept("2", placeholder="calls", width="5rem"),
    "r100": accept("3", placeholder="reading", width="5rem"), "c100": accept("4", placeholder="calls", width="5rem"),
}}
E["p2-trace"] = short("The inputs are 100, 33, 11, and 3. Each call returns the reduced reading 3.",
                      min_chars=15, placeholder="The inputs in call order and each returned value…")
E["p2"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "def reading_calls(n):\n    pass\n",
    "cases": [call_case("reading_calls", rc_ns, (n,)) for n in (0, 10, 11, 100)],
    "check": FN + '''_fn("reading_calls", "n")
_recursive("reading_calls")
_no_loops("reading_calls")
assert not _calls_in("reading_calls", "reduce_reading"), "Do not call reduce_reading from reading_calls. Count the calls with reading_calls itself."
_plain()
''' + returns("reading_calls", rc_ns, *[(n,) for n in (0, 1, 9, 10, 11, 32, 33, 34, 99, 100, 101, 1000, 10**6, 10**12)]),
    "answer": b64(reading_calls),
    "answerNote": "The count function returns 1, 2, 3, and 4 as its calls finish. Each call includes itself in the returned count."}

# 3. Stay within a move budget
tower = '''def tower_within(budget):
    discs = 0
    moves = 0
    while 2 * moves + 1 <= budget:
        moves = 2 * moves + 1
        discs = discs + 1
    return discs
'''
tw_ns = namespace(tower)
assert [tw_ns["tower_within"](b) for b in (0, 6, 7, 31)] == [0, 2, 3, 5]
BUDGETS = [(b,) for b in list(range(0, 70)) + [127, 128, 1000, 1023, 1024, 10**6, 2**40 - 1, 2**40]]
E["p3"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": "def tower_within(budget):\n    pass\n",
    "cases": [call_case("tower_within", tw_ns, (b,)) for b in (0, 6, 7, 31)],
    "check": FN + '''_fn("tower_within", "budget")
_loop_only("tower_within")
assert not any(isinstance(_n, ast.BinOp) and isinstance(_n.op, ast.Pow) for _n in ast.walk(_TREE)), "Do not use **. Build each move count from the one before."
assert not _calls_in("tower_within", "pow"), "Do not use pow. Build each move count from the one before."
_plain()
''' + returns("tower_within", tw_ns, *BUDGETS),
    "answer": b64(tower),
    "answerNote": "The loop adds one disc to the count only if the required moves fit within the budget. For a budget of 6, two discs need 3 moves. Three discs need 7 moves and exceed that budget."}

# 4. Find one Hanoi move
hanoi_move = '''def hanoi_move(n, step, source, target, spare):
    smaller_moves = 2 ** (n - 1) - 1
    if step <= smaller_moves:
        return hanoi_move(
            n - 1, step, source, spare, target)
    if step == smaller_moves + 1:
        return "Move " + str(n) + " " + source + " to " + target
    return hanoi_move(
        n - 1, step - smaller_moves - 1,
        spare, target, source)
'''
hmv_ns = namespace(hanoi_move)
# Every move matches the printed solution of section 7, for each size and two peg orders.
for n in range(1, 7):
    for pegs in (("A", "C", "B"), ("X", "Y", "Z")):
        printed = out(hanoi.replace('hanoi(3, "A", "C", "B")', f"hanoi({n}, {pegs[0]!r}, {pegs[1]!r}, {pegs[2]!r})")).split("\n")
        assert [hmv_ns["hanoi_move"](n, s, *pegs) for s in range(1, 2 ** n)] == printed
assert [hmv_ns["hanoi_move"](*a) for a in ((1, 1, "A", "C", "B"), (3, 4, "A", "C", "B"), (3, 6, "A", "C", "B"))] == \
       ["Move 1 A to C", "Move 3 A to C", "Move 2 B to C"]
MOVE_CALLS = [(n, s, "A", "C", "B") for n in range(1, 7) for s in range(1, 2 ** n)] + \
             [(n, s, "P", "Q", "R") for n in (2, 4, 6) for s in (1, 2 ** (n - 1), 2 ** n - 1)]
# The checker counts the calls of one top-level hanoi_move call: following
# only the smaller transfer that holds the move needs at most n calls.
COUNT = '''def _count_calls(name, args):
    _f = globals()[name]
    _g = _f.__globals__
    _box = [0]
    def _counting(*a):
        _box[0] += 1
        return _f(*a)
    _g[name] = _counting
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            _counting(*args)
    finally:
        _g[name] = _f
    return _box[0]
for _args in [(6, 1, "A", "C", "B"), (6, 33, "A", "C", "B"), (6, 63, "A", "C", "B"), (5, 22, "A", "C", "B")]:
    _c = _count_calls("hanoi_move", _args)
    assert _c <= _args[0], _shown("hanoi_move", _args) + " made " + str(_c) + " calls. Follow only the smaller transfer that contains the move: at most " + str(_args[0]) + " calls."
'''
E["p4"] = {"type": "code", "xp": 10, "minLines": 14,
    "starter": "def hanoi_move(n, step, source, target, spare):\n    pass\n",
    "cases": [call_case("hanoi_move", hmv_ns, a) for a in ((1, 1, "A", "C", "B"), (3, 4, "A", "C", "B"), (3, 6, "A", "C", "B"))],
    "check": FN + '''_fn("hanoi_move", "n", "step", "source", "target", "spare")
_recursive("hanoi_move")
assert not _calls_in("hanoi_move", "print"), "hanoi_move returns one move as a string. Do not print the moves."
_plain()
''' + returns("hanoi_move", hmv_ns, *MOVE_CALLS) + COUNT,
    "answer": b64(hanoi_move),
    "answerNote": "The first smaller transfer occupies the first smaller_moves positions. The largest disc moves next. A position in the second transfer must be adjusted to start counting there at 1."}

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-23",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 23 Workbook",
    "subtitle": "Recursion versus iteration and Towers of Hanoi",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-23/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
