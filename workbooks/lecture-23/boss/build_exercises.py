"""Build workbooks/lecture-23/boss/exercises.json: the Lecture 23 boss problems.

The two problems are the Boss Problems section of the kit's
LECTURE_23_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Each boss also has the workbook's
written question, placed after its code box. Run from anywhere:

    python3 workbooks/lecture-23/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-23/boss
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
    ns = {"__name__": "lecture23_boss"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    return ns

def short(answer, xp=2, min_chars=30, rows=4, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

# A check runs after the student's program in a copy of its namespace. `_fn`
# finds a function the program defined; `_call` calls it with its output
# captured. `_returns` compares a returned value with the model's. `_guard`
# looks for the standard guard as the last statement of the file.
# `_recursive` asks for calls of a function inside its own body (exactly
# `count` of them when given). `_loop_only` asks for a loop and no call of any
# function defined in the file. `_plain` rejects lists, dictionaries, sets,
# global, nonlocal, imports and decorators anywhere in the file.
FN = '''import types, io, contextlib, re, ast
_WORDS = ["empty parentheses", "one parameter", "two parameters", "three parameters"]
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
    assert not printed, name + " returns its answer and does not print. Print in main."
    if value is None:
        raise AssertionError(call + " returned None. Send the result back with return.")
    if isinstance(want, int):
        ok = isinstance(value, int) and not isinstance(value, bool) and value == want
    else:
        ok = value == want and type(value) is type(want)
    assert ok, call + " should return " + repr(want) + ", not " + repr(value) + "."
def _guard():
    _last = _TREE.body[-1] if _TREE.body else None
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
    if count is not None:
        assert _n == count, "Make " + str(count) + " recursive calls of " + name + " inside its own body, not " + str(_n) + "."
def _no_loops(name):
    assert not _has_loop(name), "Use recursion with no loop in " + name + ". Remove the for or while loop."
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

E = {}

# ---------------------------------------------------------------- 1 Binary, two ways
binary = """def binary_rec(n):
    if n < 2:
        return str(n)
    return binary_rec(n // 2) + str(n % 2)

def binary_loop(n):
    if n == 0:
        return "0"
    result = ""
    while n > 0:
        result = str(n % 2) + result
        n = n // 2
    return result

def main():
    n = int(input())
    if n < 0:
        print("Error: enter a nonnegative integer")
    else:
        print("Recursive:", binary_rec(n))
        print("Loop:", binary_loop(n))

if __name__ == '__main__':
    main()
"""
binary_ns = namespace(binary)
assert all(binary_ns["binary_rec"](n) == binary_ns["binary_loop"](n) == format(n, "b") for n in range(70000))
BIN_CALLS = [(n,) for n in range(0, 301)] + [(n,) for n in (511, 512, 1023, 1024, 4096, 40000, 65534, 65535)]
# No bin(), no format(), and no binary format code in an f-string or a
# str.format template.
NO_BIN = r'''for _n in ast.walk(_TREE):
    assert not (isinstance(_n, ast.Call) and isinstance(_n.func, ast.Name) and _n.func.id in ("bin", "format")), "Do not use bin() or format(). Build the binary digits with // and %."
    if isinstance(_n, ast.FormattedValue) and _n.format_spec is not None:
        for _part in ast.walk(_n.format_spec):
            assert not (isinstance(_part, ast.Constant) and isinstance(_part.value, str) and "b" in _part.value), "Do not use a binary format code such as :b. Build the binary digits with // and %."
    if isinstance(_n, ast.Constant) and isinstance(_n.value, str):
        assert not re.search(r"\{[^{}]*:[^{}]*b[^{}]*\}", _n.value), "Do not use a binary format code such as {:b}. Build the binary digits with // and %."
'''
E["binary"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 20,
    "starter": "def binary_rec(n):\n    pass\n\ndef binary_loop(n):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    "cases": input_cases(binary, ("Example 1: typed 13", ["13"]), ("Example 2: typed 0", ["0"]),
                         ("Example 3: typed -1", ["-1"]), ("Typed 1", ["1"]), ("Typed 2", ["2"]),
                         ("Typed 255", ["255"]), ("Typed 256", ["256"]), ("Typed 1000", ["1000"]),
                         ("Typed 65535", ["65535"])),
    "check": FN + '''_fn("binary_rec", "n")
_fn("binary_loop", "n")
_fn("main")
_recursive("binary_rec")
_no_loops("binary_rec")
assert not _calls_in("binary_rec", "binary_loop"), "Use recursion in binary_rec. Do not call binary_loop from it."
_loop_only("binary_loop")
''' + NO_BIN + '''_plain()
''' + "".join(f"_returns('binary_rec', {a!r}, {binary_ns['binary_rec'](*a)!r})\n" for a in BIN_CALLS)
    + "".join(f"_returns('binary_loop', {a!r}, {binary_ns['binary_loop'](*a)!r})\n" for a in BIN_CALLS) + "_guard()\n",
    "hints": [
        "In `binary_rec`, a number below 2 is its own binary digit: `if n < 2:` return `str(n)`. That base case also returns `\"0\"` for zero.",
        "Otherwise `n // 2` holds the earlier digits and `n % 2` is the last one. Return `binary_rec(n // 2) + str(n % 2)`. For 13 the calls are 13, 6, 3, and 1, and the result is `\"1101\"`.",
        "In `binary_loop`, return `\"0\"` for zero first. Then start with `result = \"\"` and repeat while `n > 0`: put `str(n % 2)` at the front of `result` and set `n = n // 2`.",
        "In `main`, read `n` with `int(input())`. If it is negative, print the error line. Otherwise print `\"Recursive:\"` and `binary_rec(n)`, then `\"Loop:\"` and `binary_loop(n)`.",
    ],
    "answer": b64(binary),
    "answerNote": "The recursive call returns the earlier binary digits. The remainder supplies the final digit. The loop places each new digit at the front of its result."}
assert [c["expected"] for c in E["binary"]["cases"][:3]] == ["Recursive: 1101\nLoop: 1101", "Recursive: 0\nLoop: 0",
                                                             "Error: enter a nonnegative integer"]

E["binary-why"] = short("I prefer the loop because its updates are easy to follow and it uses one conversion frame. "
                        "The recursive version also reads clearly as a smaller conversion followed by one digit. "
                        "It keeps one conversion frame for each call until the base case returns.\n\n"
                        "Either preference is valid when the reasons match the code.",
                        placeholder="The version you prefer… One reason about clarity… One reason about unfinished calls…")

# ---------------------------------------------------------------- 2 The fewest edits
edits = """def edit_distance(s, t):
    if s == "":
        return len(t)
    if t == "":
        return len(s)
    cost = 0
    if s[-1] != t[-1]:
        cost = 1
    delete = edit_distance(s[:-1], t) + 1
    insert = edit_distance(s, t[:-1]) + 1
    substitute = edit_distance(s[:-1], t[:-1]) + cost
    return min(delete, insert, substitute)

def main():
    s = input()
    t = input()
    print("Distance:", edit_distance(s, t))

if __name__ == '__main__':
    main()
"""
edits_ns = namespace(edits)

def naive_calls(a, b):
    """Calls made by edit_distance on strings of lengths a and b, with three
    recursive calls for every pair of nonempty strings and no saved answers."""
    if a == 0 or b == 0:
        return 1
    return 1 + naive_calls(a - 1, b) + naive_calls(a, b - 1) + naive_calls(a - 1, b - 1)

# The repeated pair in the workbook's trace of edit_distance("ab", "ac").
seen = []
def _trace(s, t):
    seen.append((s, t))
    if s == "" or t == "":
        return max(len(s), len(t))
    return min(_trace(s[:-1], t) + 1, _trace(s, t[:-1]) + 1, _trace(s[:-1], t[:-1]) + (s[-1] != t[-1]))
assert _trace("ab", "ac") == 1 and seen.count(("a", "a")) >= 2 and len(seen) == naive_calls(2, 2) == 19
assert naive_calls(1, 1) == 4 and naive_calls(4, 4) == 481

EDIT_CALLS = [("", ""), ("a", ""), ("", "a"), ("abcd", ""), ("", "abcd"), ("a", "a"), ("a", "b"), ("ab", "ba"),
              ("at", "cat"), ("cat", "at"), ("ab", "ac"), ("cat", "act"), ("cat", "cut"), ("same", "same"),
              ("abcd", "dcba"), ("abcd", "abc"), ("abc", "abcd"), ("abcd", "bcd"), ("kite", "bite"), ("tree", "free"),
              ("milk", "silk"), ("dog", "god"), ("aaaa", "a"), ("a", "aaaa"), ("abba", "baab"), ("ring", "rang"),
              ("abc", "xyz"), ("star", "rats"), ("bake", "cake"), ("lamp", "camp"), ("cold", "card"), ("zz", "zzzz"),
              ("abcd", "wxyz"), ("abca", "acba"), ("node", "done"), ("head", "heal"), ("a", "ba"), ("ba", "a"),
              ("rain", "ran"), ("ran", "rain")]
assert all(len(s) <= 4 and len(t) <= 4 and (s + t).islower() or s + t == "" for s, t in EDIT_CALLS)
EDIT_COUNT = [("ab", "ac"), ("a", "b"), ("abc", "abd"), ("same", "same"), ("abcd", "wxyz"), ("ab", "abcd")]
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
''' + "".join(f'''_c = _count_calls("edit_distance", {a!r})
assert _c == {naive_calls(len(a[0]), len(a[1]))}, _shown("edit_distance", {a!r}) + " made " + str(_c) + " calls, not {naive_calls(len(a[0]), len(a[1]))}. Make three recursive calls for every pair of nonempty strings, stop only when a string is empty, and do not save earlier answers."
''' for a in EDIT_COUNT)
E["edits"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 18,
    "starter": "def edit_distance(s, t):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    "cases": input_cases(edits, ("Example 1: typed at and cat", ["at", "cat"]),
                         ("Example 2: typed blank and go", ["", "go"]),
                         ("Example 3: typed ab and ac", ["ab", "ac"]),
                         ("Typed blank and blank", ["", ""]),
                         ("Typed abcd and blank", ["abcd", ""]),
                         ("Typed cat and act", ["cat", "act"]),
                         ("Typed same and same", ["same", "same"]),
                         ("Typed abcd and dcba", ["abcd", "dcba"]),
                         ("Typed kite and bit", ["kite", "bit"])),
    "check": FN + '''_fn("edit_distance", "s", "t")
_fn("main")
_recursive("edit_distance", 3)
for _name in _defined():
    assert not _has_loop(_name), "Use no loops. Remove the for or while loop from " + _name + "."
_plain()
''' + "".join(f"_returns('edit_distance', {a!r}, {edits_ns['edit_distance'](*a)!r})\n" for a in EDIT_CALLS) + COUNT + "_guard()\n",
    "hints": [
        "Start with the two base cases: if `s == \"\"`, return `len(t)`. If `t == \"\"`, return `len(s)`.",
        "Set `cost` to 0 when the last characters match and 1 when they differ. `s[:-1]` is `s` without its last character.",
        "Make the three calls and add each cost: `edit_distance(s[:-1], t) + 1` deletes, `edit_distance(s, t[:-1]) + 1` inserts, and `edit_distance(s[:-1], t[:-1]) + cost` substitutes or matches. Return `min` of the three.",
        "In `main`, read `s` and `t` with two `input()` calls. A blank line gives the empty string. Print `\"Distance:\"` and `edit_distance(s, t)`.",
    ],
    "answer": b64(edits),
    "answerNote": "An empty string needs one edit for each character in the other string. For nonempty strings, compare deletion, insertion, and substitution or a match. The minimum is the cheapest choice."}
assert [c["expected"] for c in E["edits"]["cases"][:3]] == ["Distance: 1", "Distance: 2", "Distance: 1"]

E["edits-trace"] = short('The pair ("a", "a") appears on both of these paths:\n'
                         '1. ("ab", "ac"), then ("a", "ac"), then ("a", "a").\n'
                         '2. ("ab", "ac"), then ("ab", "a"), then ("a", "a").\n\n'
                         'Both calls return 0. Each computes its answer separately.',
                         rows=6, placeholder="The repeated pair… Two call paths that reach it… The distance it returns…")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-23-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 23 Boss Problems",
    "short": "L23 bosses",
    "subtitle": "Recursion versus iteration and Towers of Hanoi",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-23/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
