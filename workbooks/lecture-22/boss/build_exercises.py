"""Build workbooks/lecture-22/boss/exercises.json: the Lecture 22 boss problems.

The three problems are the Boss Problems section of the kit's
LECTURE_22_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Run from anywhere:

    python3 workbooks/lecture-22/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-22/boss
"""
import base64, contextlib, io, json, subprocess, sys, time, pathlib

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

def namespace(code):
    ns = {"__name__": "lecture22_boss"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    return ns

def printed(ns, name, *args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        ns[name](*args)
    return buffer.getvalue()

# A check runs after the student's program in a copy of its namespace. `_fn`
# finds a function the program defined; `_call` calls it with its output
# captured, so the test call does not add to the program's own output.
# `_returns` compares a returned value and `_prints` compares what a call
# prints. `_guard` looks for the standard guard as the last statement of the
# file. `_local_state` allows only uppercase constants at the top level.
# `_self_calls` counts the calls a function makes to itself, and `_plain`
# rejects loops, lists and dictionaries anywhere in the program.
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
def _returns(name, args, want, quiet=False):
    value, out = _call(name, *args)
    call = _shown(name, args)
    if quiet:
        assert out == "", call + " printed something. Return the result and let main print it."
    if value is None:
        raise AssertionError(call + " returned None. Return a value on every path.")
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
def _local_state():
    _tree = ast.parse(__source__)
    assert not any(isinstance(n, (ast.Global, ast.Nonlocal)) for n in ast.walk(_tree)), "Do not use global or nonlocal. Pass values as arguments and return results."
    for _n in _tree.body:
        _targets = _n.targets if isinstance(_n, ast.Assign) else [_n.target] if isinstance(_n, (ast.AugAssign, ast.AnnAssign)) else []
        for _t in _targets:
            for _m in ast.walk(_t):
                if isinstance(_m, ast.Name):
                    assert _m.id.isupper(), "Keep changing data local: assign " + _m.id + " inside a function. Only uppercase constants belong at the top level."
def _calls_in(name, callee):
    return [n for n in _body(name) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == callee]
def _self_calls(name):
    return len(_calls_in(name, name))
def _plain():
    for _n in ast.walk(ast.parse(__source__)):
        assert not isinstance(_n, (ast.For, ast.While, ast.comprehension)), "Use recursion and no loops."
        assert not isinstance(_n, (ast.List, ast.Dict, ast.Set)), "Use no lists or dictionaries. Keep the values in parameters and return values."
'''

def returns(name, ns, *calls, quiet=False):
    return "".join(f"_returns({name!r}, {args!r}, {ns[name](*args)!r}{', quiet=True' if quiet else ''})\n" for args in calls)

def prints(name, ns, *calls):
    return "".join(f"_prints({name!r}, {args!r}, {printed(ns, name, *args)!r})\n" for args in calls)

E = {}

# ---------------------------------------------------------------- 1 Twelve days of shop supplies
GIFTS = ["1 paper bag", "2 pencils", "3 notebooks", "4 erasers", "5 rulers", "6 folders",
         "7 markers", "8 glue sticks", "9 labels", "10 brushes", "11 stamps", "12 cards"]
gifts = '''def show_gift(day):
    if day == 1:
        print("1 paper bag")
    elif day == 2:
        print("2 pencils")
    elif day == 3:
        print("3 notebooks")
    elif day == 4:
        print("4 erasers")
    elif day == 5:
        print("5 rulers")
    elif day == 6:
        print("6 folders")
    elif day == 7:
        print("7 markers")
    elif day == 8:
        print("8 glue sticks")
    elif day == 9:
        print("9 labels")
    elif day == 10:
        print("10 brushes")
    elif day == 11:
        print("11 stamps")
    elif day == 12:
        print("12 cards")
'''
song_rest = '''def show_gifts(day):
    if day == 0:
        return
    show_gift(day)
    show_gifts(day - 1)

def show_verse(day):
    print("Day", day)
    show_gifts(day)

def show_song(days):
    if days == 0:
        return
    show_song(days - 1)
    show_verse(days)

def main():
    days = int(input())
    show_song(days)

if __name__ == '__main__':
    main()
'''
song = gifts + "\n" + song_rest
song_ns = namespace(song)
assert all(song.count(g) == 1 for g in GIFTS)
E["song"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 44,
    "starter": ("def show_gift(day):\n    pass\n\ndef show_gifts(day):\n    pass\n\ndef show_verse(day):\n    pass\n\n"
                "def show_song(days):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n"),
    "cases": input_cases(song, ("Example 1: typed 3", ["3"]), ("Example 2: typed 1", ["1"]), ("Typed 2", ["2"]),
                         ("Typed 6", ["6"]), ("Typed 12", ["12"])),
    "check": FN + '''_fn("show_gift", "day")
_fn("show_gifts", "day")
_fn("show_verse", "day")
_fn("show_song", "days")
_fn("main")
assert any(isinstance(n, ast.If) and len(n.orelse) == 1 and isinstance(n.orelse[0], ast.If) for n in _body("show_gift")), "In show_gift, use an if/elif chain with one branch for each day."
for _g in ''' + repr(GIFTS) + ''':
    assert __source__.count(_g) <= 1, "Write the text \\"" + _g + "\\" only once in your code, in show_gift."
assert _self_calls("show_gifts") >= 1, "Use recursion in show_gifts: it calls show_gifts with a smaller day."
assert _self_calls("show_song") >= 1, "Use recursion in show_song: it calls show_song with a smaller number of days."
assert _calls_in("show_verse", "show_gifts"), "In show_verse, print the heading and then call show_gifts."
assert _calls_in("main", "show_song"), "In main, read the number of days and call show_song."
_plain()
''' + prints("show_gift", song_ns, *[(d,) for d in range(1, 13)])
    + prints("show_gifts", song_ns, (1,), (4,), (12,))
    + prints("show_verse", song_ns, (1,), (5,))
    + prints("show_song", song_ns, *[(d,) for d in range(1, 13)]) + "_guard()\n",
    "hints": [
        "`show_gift` is an `if`/`elif` chain with one `print` for each day, such as `if day == 1:` followed by `print(\"1 paper bag\")`.",
        "`show_gifts(day)` stops when `day == 0`. Otherwise it calls `show_gift(day)` first and then `show_gifts(day - 1)`, so the gifts come out in decreasing order.",
        "`show_song(days)` also stops at 0. Otherwise it calls `show_song(days - 1)` first and then `show_verse(days)`, so the verses come out in increasing order. `show_verse` prints `\"Day\", day` and calls `show_gifts(day)`.",
    ],
    "answer": b64(song),
    "answerNote": "`show_song` prints each verse after its smaller call finishes. `show_gifts` prints its gift before making the smaller call. "
                  "This places the verses in increasing order and the gifts in decreasing order."}
assert E["song"]["cases"][0]["expected"] == "Day 1\n1 paper bag\nDay 2\n2 pencils\n1 paper bag\nDay 3\n3 notebooks\n2 pencils\n1 paper bag"
assert E["song"]["cases"][1]["expected"] == "Day 1\n1 paper bag"
assert E["song"]["cases"][4]["expected"].count("\n") + 1 == 12 + 78

# ---------------------------------------------------------------- 2 Encode repeated letters
encode = '''def run_length(text, index, count):
    if index == len(text):
        return count
    if text[index] != text[0]:
        return count
    return run_length(text, index + 1, count + 1)

def encode(text):
    if text == "":
        return ""
    length = run_length(text, 0, 0)
    return text[0] + str(length) + encode(text[length:])

def main():
    text = input()
    print('Encoded: "' + encode(text) + '"')

if __name__ == '__main__':
    main()
'''
enc_ns = namespace(encode)
E["encode"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 24,
    "starter": ("def run_length(text, index, count):\n    pass\n\ndef encode(text):\n    pass\n\ndef main():\n    pass\n\n"
                "if __name__ == '__main__':\n    main()\n"),
    "cases": input_cases(encode, ("Example 1: typed AAAAAAAAAAAABBBBAAAAAAB", ["AAAAAAAAAAAABBBBAAAAAAB"]),
                         ("Example 2: typed a blank line", [""]), ("Typed A", ["A"]), ("Typed AaAA", ["AaAA"]),
                         ("Typed 80 copies of z", ["z" * 80]), ("Typed Mississippi", ["Mississippi"])),
    "check": FN + '''_fn("run_length", "text", "index", "count")
_fn("encode", "text")
_fn("main")
assert _self_calls("run_length") >= 1, "Use recursion in run_length: it calls itself with the next index and count."
assert _self_calls("encode") >= 1, "Use recursion in encode: it encodes the rest of the text with another call to encode."
assert _calls_in("encode", "run_length"), "In encode, find the length of the first run with run_length(text, 0, 0)."
_local_state()
_plain()
''' + returns("run_length", enc_ns, ("AAAAB", 0, 0), ("A", 0, 0), ("AB", 0, 0), ("AAA", 2, 2), ("aA", 0, 0), ("z" * 80, 0, 0), quiet=True)
    + returns("encode", enc_ns, ("",), ("A",), ("AaAA",), ("A" * 80,), ("AB" * 40,), ("Mississippi",), ("AAAAAAAAAAAABBBBAAAAAAB",), quiet=True)
    + "_guard()\n",
    "hints": [
        "`run_length` returns `count` when `index` reaches `len(text)` or when `text[index]` differs from `text[0]`. Otherwise it returns `run_length(text, index + 1, count + 1)`.",
        "`encode` returns `\"\"` for empty text. Otherwise it finds `length = run_length(text, 0, 0)`. For `AAAAB` that is 4.",
        "Return `text[0] + str(length) + encode(text[length:])`. In `main`, read the line and print `'Encoded: \"' + encode(text) + '\"'`.",
    ],
    "answer": b64(encode),
    "answerNote": "The helper stops at the end of the string or at the first different character. The helper passes its count to the next call. "
                  "`encode` combines one encoded run with the encoded remainder."}
assert [c["expected"] for c in E["encode"]["cases"][:2]] == ['Encoded: "A12B4A6B1"', 'Encoded: ""']

# ---------------------------------------------------------------- 3 Exact coin total
coins = '''def possible_change(dollars, coins):
    cents = int(round(dollars * 100))
    return change_helper(cents, coins)

def change_helper(cents, coins):
    if cents == 0 and coins == 0:
        return True
    if cents <= 0 or coins <= 0:
        return False
    if cents < coins or cents > 25 * coins:
        return False
    return (change_helper(cents - 25, coins - 1)
            or change_helper(cents - 10, coins - 1)
            or change_helper(cents - 5, coins - 1)
            or change_helper(cents - 1, coins - 1))

def main():
    dollars = float(input())
    coins = int(input())
    print("Possible:", possible_change(dollars, coins))

if __name__ == '__main__':
    main()
'''
coin_ns = namespace(coins)
# The calls whose every call to change_helper is recorded: the wrapper checks
# that each one gets integer cents and that a branch with negative cents or no
# coins left makes no more calls.
WATCHED = [(0.29, 5), (0.04, 3), (0.57, 3), (1.00, 5), (0.00, 2), (0.10, 0)]
POSSIBLE = [(0.29, 5), (0.29, 2), (0.57, 5), (0.57, 3), (2.00, 8), (1.99, 8), (0.08, 8), (0.50, 1), (0.10, 1),
            (0.00, 3), (0.05, 0), (0.15, 2), (0.30, 3), (1.10, 8), (0.04, 3)]
HELPER = [(0, 0), (25, 1), (24, 1), (100, 4), (100, 5), (5, 5), (7, 3), (0, 1), (1, 0)]
watch = '''_h = change_helper.__globals__["change_helper"]
_stack = []
_bad = []
def _watch(cents, coins):
    if not (isinstance(cents, int) and not isinstance(cents, bool)):
        _bad.append("Use integer cents in every helper call. Convert with int(round(dollars * 100)) in possible_change, not " + repr(cents) + ".")
    elif _stack and (_stack[-1][0] < 0 or _stack[-1][1] <= 0):
        _bad.append("Stop impossible branches: change_helper" + repr(_stack[-1]) + " should return False without calling change_helper again.")
    if not _bad and len(_stack) > 20:
        _bad.append("Use one fewer coin in each recursive call, so every branch stops.")
    if _bad:
        raise RecursionError("stopped")
    _stack.append((cents, coins))
    try:
        return _h(cents, coins)
    finally:
        _stack.pop()
change_helper.__globals__["change_helper"] = _watch
try:
    for _args in ''' + repr(WATCHED) + ''':
        try:
            _call("possible_change", *_args)
        except RecursionError:
            pass
        assert not _bad, _bad[0]
finally:
    change_helper.__globals__["change_helper"] = _h
'''
E["coins"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 26,
    "starter": ("def possible_change(dollars, coins):\n    pass\n\ndef change_helper(cents, coins):\n    pass\n\ndef main():\n    pass\n\n"
                "if __name__ == '__main__':\n    main()\n"),
    "cases": input_cases(coins, ("Example 1: typed 1.00 and 4", ["1.00", "4"]), ("Example 2: typed 1.00 and 5", ["1.00", "5"]),
                         ("Example 3: typed 0.00 and 0", ["0.00", "0"]), ("Typed 2.00 and 8", ["2.00", "8"]),
                         ("Typed 0.29 and 5", ["0.29", "5"]), ("Typed 0.29 and 2", ["0.29", "2"]),
                         ("Typed 1.99 and 8", ["1.99", "8"]), ("Typed 0.08 and 8", ["0.08", "8"]),
                         ("Typed 0.50 and 1", ["0.50", "1"]), ("Typed 0.00 and 3", ["0.00", "3"]),
                         ("Typed 0.05 and 0", ["0.05", "0"])),
    "check": FN + '''_fn("possible_change", "dollars", "coins")
_fn("change_helper", "cents", "coins")
_fn("main")
assert _calls_in("possible_change", "round"), "In possible_change, convert with int(round(dollars * 100)) so 0.29 becomes 29 cents."
assert _calls_in("possible_change", "change_helper"), "In possible_change, return the answer from change_helper(cents, coins)."
assert any(isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or) and
           sum(isinstance(m, ast.Call) and isinstance(m.func, ast.Name) and m.func.id == "change_helper" for m in ast.walk(n)) >= 4
           for n in _body("change_helper")), "Join the four recursive choices, one for each coin, with or."
_plain()
''' + watch + returns("change_helper", coin_ns, *HELPER) + returns("possible_change", coin_ns, *POSSIBLE) + "_guard()\n",
    "hints": [
        "In `possible_change`, set `cents = int(round(dollars * 100))` and return `change_helper(cents, coins)`. `round` matters: `0.29 * 100` is `28.999999999999996`.",
        "`change_helper` returns `True` when `cents` and `coins` are both 0. It returns `False` when either one is 0 or below, before making any more calls.",
        "Otherwise try each coin with one fewer coin left: `change_helper(cents - 25, coins - 1) or change_helper(cents - 10, coins - 1)`, and the same for 5 and 1.",
        "To stop more impossible branches early, also return `False` when `cents < coins` or `cents > 25 * coins`.",
    ],
    "answer": b64(coins),
    "answerNote": "Each choice uses one coin and reduces the amount by its value. Success requires both remaining values to be zero. "
                  "An amount below `coins` cents is too small for that many coins. An amount above `25 * coins` cents is too large."}
assert [c["expected"] for c in E["coins"]["cases"][:3]] == ["Possible: True", "Possible: False", "Possible: True"]
assert coin_ns["possible_change"](0.29, 5) is True and coin_ns["possible_change"](0.57, 5) is True

# A version without the range test still passes, and stays fast: time its
# heaviest checks here (the browser is a few times slower than this).
naive = coins.replace("    if cents < coins or cents > 25 * coins:\n        return False\n", "")
naive_ns = namespace(naive)
start = time.perf_counter()
for args in POSSIBLE + [(1.99, 8)]:
    assert naive_ns["possible_change"](*args) == coin_ns["possible_change"](*args)
print(f"naive coin solution: {time.perf_counter() - start:.3f} s for the possible_change checks")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-22-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 22 Boss Problems",
    "short": "L22 bosses",
    "subtitle": "Tracing recursion and recursive helpers",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-22/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
