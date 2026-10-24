"""Build workbooks/lecture-20/boss/exercises.json: the Lecture 20 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_20_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Run from anywhere:

    python3 workbooks/lecture-20/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-20/boss
"""
import base64, contextlib, io, json, random, subprocess, sys, pathlib

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
    ns = {"__name__": "lecture20_boss"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    return ns

# A check runs after the student's program in a copy of its namespace. `_fn`
# finds a function the program defined; `_call` calls it with its output
# captured, so the test call does not add to the program's own output. `_guard`
# looks for the standard guard as the last statement of the file. `_local_state`
# allows only uppercase constants to be assigned at the top level.
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
    elif isinstance(want, float):
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
def _local_state():
    _tree = ast.parse(__source__)
    assert not any(isinstance(n, (ast.Global, ast.Nonlocal)) for n in ast.walk(_tree)), "Do not use global or nonlocal. Pass values as arguments and return results."
    for _n in _tree.body:
        _targets = _n.targets if isinstance(_n, ast.Assign) else [_n.target] if isinstance(_n, (ast.AugAssign, ast.AnnAssign)) else []
        for _t in _targets:
            for _m in ast.walk(_t):
                if isinstance(_m, ast.Name):
                    assert _m.id.isupper(), "Keep changing data local: assign " + _m.id + " inside a function. Only uppercase constants belong at the top level."
def _calls(name, attr):
    return [n for n in _body(name) if isinstance(n, ast.Call) and
            ((isinstance(n.func, ast.Attribute) and n.func.attr == attr) or (isinstance(n.func, ast.Name) and n.func.id == attr))]
'''

E = {}

# ---------------------------------------------------------------- 1 Distance fare
fare = """BASE_FARE = 3.50
RATE_PER_SEGMENT = 0.40
METRES_PER_SEGMENT = 200

def fare(kilometres):
    metres = kilometres * 1000
    return BASE_FARE + metres / METRES_PER_SEGMENT * RATE_PER_SEGMENT

def main():
    kilometres = float(input())
    amount = fare(kilometres)
    print(f'Fare: ${amount:.2f}')

if __name__ == '__main__':
    main()
"""
fare_ns = namespace(fare)
FARE_CALLS = [(0,), (1.5,), (0.2,), (0.1,), (1,), (2.35,), (12.75,), (1000,)]
E["fare"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 16,
    "starter": ("BASE_FARE = 3.50\nRATE_PER_SEGMENT = 0.40\nMETRES_PER_SEGMENT = 200\n\n"
                "def fare(kilometres):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n"),
    "cases": input_cases(fare, ("Example 1: typed 1.5", ["1.5"]), ("Example 2: typed 0", ["0"]), ("Typed 0.1", ["0.1"]),
                         ("Typed 2.35", ["2.35"]), ("Typed 12.75", ["12.75"]), ("Typed 1000", ["1000"])),
    "check": FN + '''_f = _fn("fare", "kilometres")
_fn("main")
assert globals().get("BASE_FARE") == 3.5 and globals().get("RATE_PER_SEGMENT") == 0.4 and globals().get("METRES_PER_SEGMENT") == 200, "Keep the three constants from the starter: BASE_FARE = 3.50, RATE_PER_SEGMENT = 0.40, METRES_PER_SEGMENT = 200."
for _c in ("BASE_FARE", "RATE_PER_SEGMENT", "METRES_PER_SEGMENT"):
    assert _c in _f.__code__.co_names, "Use " + _c + " in fare instead of writing its value again."
_local_state()
''' + "".join(f"_returns('fare', {a!r}, {float(fare_ns['fare'](*a))!r})\n" for a in FARE_CALLS) + "_guard()\n",
    "hints": [
        "Inside `fare`, convert the distance first: `metres = kilometres * 1000`. For 1.5 kilometres that is 1500 metres.",
        "`metres / METRES_PER_SEGMENT` is the number of 200-metre segments, including a fraction. For 1500 metres it is 7.5, and 7.5 times 0.40 is 3.00.",
        "Return `BASE_FARE + metres / METRES_PER_SEGMENT * RATE_PER_SEGMENT`. In `main`, read the distance with `float(input())`, call `fare`, and print `f'Fare: ${amount:.2f}'`.",
    ],
    "answer": b64(fare),
    "answerNote": "The constants express this program's fixed pricing rule. The only changing input to the calculation is its parameter."}
assert [c["expected"] for c in E["fare"]["cases"][:2]] == ["Fare: $6.50", "Fare: $3.50"]

# ---------------------------------------------------------------- 2 Measure description
measure = """TABLESPOONS_PER_CUP = 16
TEASPOONS_PER_TABLESPOON = 3
TEASPOONS_PER_CUP = TABLESPOONS_PER_CUP * TEASPOONS_PER_TABLESPOON

def to_teaspoons(quantity, unit):
    if unit == 'cup':
        return quantity * TEASPOONS_PER_CUP
    if unit == 'tablespoon':
        return quantity * TEASPOONS_PER_TABLESPOON
    return quantity

def describe(total):
    cups = total // TEASPOONS_PER_CUP
    remaining = total % TEASPOONS_PER_CUP
    tablespoons = remaining // TEASPOONS_PER_TABLESPOON
    teaspoons = remaining % TEASPOONS_PER_TABLESPOON
    return f'{cups} cups, {tablespoons} tablespoons, {teaspoons} teaspoons'

def main():
    quantity = int(input())
    unit = input()
    total = to_teaspoons(quantity, unit)
    print(describe(total))

if __name__ == '__main__':
    main()
"""
measure_ns = namespace(measure)
TSP_CALLS = [(q, u) for u in ("cup", "tablespoon", "teaspoon") for q in (0, 1, 2, 7, 10000)]
DESCRIBE_CALLS = [(t,) for t in (0, 1, 2, 3, 47, 48, 49, 70, 96, 100, 30000)]
E["measure"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 24,
    "starter": ("TABLESPOONS_PER_CUP = 16\nTEASPOONS_PER_TABLESPOON = 3\nTEASPOONS_PER_CUP = TABLESPOONS_PER_CUP * TEASPOONS_PER_TABLESPOON\n\n"
                "def to_teaspoons(quantity, unit):\n    pass\n\ndef describe(total):\n    pass\n\ndef main():\n    pass\n\n"
                "if __name__ == '__main__':\n    main()\n"),
    "cases": input_cases(measure, ("Example 1: typed 70 and teaspoon", ["70", "teaspoon"]), ("Example 2: typed 0 and cup", ["0", "cup"]),
                         ("Example 3: typed 20 and tablespoon", ["20", "tablespoon"]), ("Typed 1 and cup", ["1", "cup"]),
                         ("Typed 2 and tablespoon", ["2", "tablespoon"]), ("Typed 47 and teaspoon", ["47", "teaspoon"]),
                         ("Typed 10000 and tablespoon", ["10000", "tablespoon"])),
    "check": FN + '''_fn("to_teaspoons", "quantity", "unit")
_fn("describe", "total")
_fn("main")
assert (globals().get("TABLESPOONS_PER_CUP"), globals().get("TEASPOONS_PER_TABLESPOON"), globals().get("TEASPOONS_PER_CUP")) == (16, 3, 48), "Keep the three unit constants from the starter."
_ops = [type(n.op) for n in _body("describe") if isinstance(n, ast.BinOp)]
assert ast.FloorDiv in _ops and ast.Mod in _ops, "In describe, use integer division // and remainder % to split the teaspoons into larger units."
_local_state()
''' + "".join(f"_returns('to_teaspoons', {a!r}, {measure_ns['to_teaspoons'](*a)!r})\n" for a in TSP_CALLS)
      + "".join(f"_returns('describe', {a!r}, {measure_ns['describe'](*a)!r})\n" for a in DESCRIBE_CALLS) + "_guard()\n",
    "hints": [
        "`to_teaspoons` multiplies by `TEASPOONS_PER_CUP` for `'cup'` and by `TEASPOONS_PER_TABLESPOON` for `'tablespoon'`, and returns a teaspoon quantity unchanged. For 20 tablespoons it returns 60.",
        "In `describe`, `total // TEASPOONS_PER_CUP` is the number of cups and `total % TEASPOONS_PER_CUP` is what is left. For 70 teaspoons that is 1 cup and 22 teaspoons left.",
        "Divide the remainder the same way with `TEASPOONS_PER_TABLESPOON`: 22 gives 7 tablespoons and 1 teaspoon. Return `f'{cups} cups, {tablespoons} tablespoons, {teaspoons} teaspoons'`.",
    ],
    "answer": b64(measure),
    "answerNote": "Converting the input to teaspoons lets `describe` use one unit for every input. Each division uses the amount left after removing the larger units."}
assert [c["expected"] for c in E["measure"]["cases"][:3]] == ["1 cups, 7 tablespoons, 1 teaspoons", "0 cups, 0 tablespoons, 0 teaspoons",
                                                                "1 cups, 4 tablespoons, 0 teaspoons"]

# ---------------------------------------------------------------- 3 Password search
search = """import random

ALLOWED = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

def generate_password():
    \"\"\"Return a candidate using ALLOWED and the current random state.\"\"\"
    length = random.randint(7, 11)
    password = ''
    for position in range(length):
        password = password + random.choice(ALLOWED)
    return password

def is_good_password(password):
    upper = False
    lower = False
    digit = False
    for ch in password:
        if 'A' <= ch <= 'Z':
            upper = True
        if 'a' <= ch <= 'z':
            lower = True
        if '0' <= ch <= '9':
            digit = True
    return len(password) >= 9 and upper and lower and digit

def main():
    seed = int(input())
    random.seed(seed)
    attempts = 1
    password = generate_password()
    while not is_good_password(password):
        password = generate_password()
        attempts = attempts + 1
    print('Password:', password)
    print('Attempts:', attempts)

if __name__ == '__main__':
    main()
"""
search_ns = namespace(search)
GOOD_CALLS = [(p,) for p in ("", "abc", "Abcdefgh2", "abcdefgh2", "ABCDEFGH2", "Abcdefghi", "Abcdefg2", "A1bcdefgh", "123456789aB",
                             "EPyYngFb51", "W4Acq9GFz6", "zzzzzzzzA", "zZ0zzzzzz", "Zz9", "99999999aZ")]
ALLOWED = search_ns["ALLOWED"]
E["password"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 32,
    "starter": ("import random\n\nALLOWED = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'\n\n"
                "def generate_password():\n    pass\n\ndef is_good_password(password):\n    pass\n\ndef main():\n    pass\n\n"
                "if __name__ == '__main__':\n    main()\n"),
    "cases": input_cases(search, ("Example 1: typed 1", ["1"]), ("Example 2: typed 0", ["0"]), ("Typed 2", ["2"]),
                         ("Typed 42", ["42"]), ("Typed 2026", ["2026"]), ("Typed 1000000", ["1000000"])),
    "check": FN + f'''import random as _random
_fn("generate_password")
_fn("is_good_password", "password")
_fn("main")
assert globals().get("ALLOWED") == {ALLOWED!r}, "Keep the ALLOWED string exactly as the starter gives it."
assert _calls("generate_password", "randint"), "In generate_password, choose the length with random.randint(7, 11)."
assert _calls("generate_password", "choice"), "In generate_password, choose each character with random.choice(ALLOWED)."
_seeds = [n for n in ast.walk(ast.parse(__source__)) if isinstance(n, ast.Call) and
          ((isinstance(n.func, ast.Attribute) and n.func.attr == "seed") or (isinstance(n.func, ast.Name) and n.func.id == "seed"))]
assert len(_seeds) == 1 and _calls("main", "seed"), "Call random.seed once, in main."
assert not any(isinstance(n, (ast.For, ast.While)) and any(m in _seeds for m in ast.walk(n)) for n in _body("main")), "Set the seed once, before the search loop."
_local_state()
_random.seed(5)
for _i in range(200):
    _value, _ = _call("generate_password")
    assert isinstance(_value, str) and 7 <= len(_value) <= 11 and all(c in ALLOWED for c in _value), "generate_password() should return 7 to 11 characters from ALLOWED, not " + repr(_value) + "."
''' + "".join(f"_returns('is_good_password', {a!r}, {search_ns['is_good_password'](*a)!r})\n" for a in GOOD_CALLS) + "_guard()\n",
    "hints": [
        "In `generate_password`, call `random.randint(7, 11)` once for the length. Then start with `password = ''` and add `random.choice(ALLOWED)` once per position in a `for` loop.",
        "In `is_good_password`, start three flags at `False` and loop over the characters. `'A' <= ch <= 'Z'` sets the uppercase flag; the lowercase and digit tests work the same way. Return `len(password) >= 9 and upper and lower and digit`.",
        "In `main`, read the seed and call `random.seed(seed)` once. Set `attempts = 1` and generate the first candidate, then repeat `while not is_good_password(password):`, generating a new candidate and adding 1 to `attempts`. For seed 1 the loop runs once and the program prints `Password: EPyYngFb51` and `Attempts: 2`.",
    ],
    "answer": b64(search),
    "answerNote": "`main` controls the search and counts candidates. The checker can be tested with supplied strings. The generator intentionally uses "
                  "the random module's state; its seed is set once by `main`. No attempt count or candidate is stored globally."}
assert [c["expected"] for c in E["password"]["cases"][:2]] == ["Password: EPyYngFb51\nAttempts: 2", "Password: W4Acq9GFz6\nAttempts: 1"]

# ---------------------------------------------------------------- 4 Base conversion
base = """DIGITS = '0123456789ABCDEF'

def digit_value(ch):
    value = 0
    while DIGITS[value] != ch:
        value = value + 1
    return value

def to_decimal(text, base):
    number = 0
    for ch in text:
        number = number * base + digit_value(ch)
    return number

def from_decimal(number, base):
    if number == 0:
        return '0'
    text = ''
    while number > 0:
        digit = number % base
        text = DIGITS[digit] + text
        number = number // base
    return text

def main():
    source_base = int(input())
    target_base = int(input())
    if source_base < 2 or source_base > 16 or target_base < 2 or target_base > 16:
        print('Invalid base.')
        return
    text = input()
    number = to_decimal(text, source_base)
    print(from_decimal(number, target_base))

if __name__ == '__main__':
    main()
"""
base_ns = namespace(base)
VALUE_CALLS = [(c,) for c in "0123456789ABCDEF"]
DEC_CALLS = [("0", 2), ("000", 16), ("2A", 12), ("101101", 2), ("FF", 16), ("777", 8), ("114", 5), ("FFFFFFFFFFFF", 16), ("10", 3)]
FROM_CALLS = [(0, 2), (34, 5), (255, 16), (45, 2), (281474976710655, 16), (9, 3), (15, 16), (16, 16), (1, 2)]
E["base"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 34,
    "starter": ("DIGITS = '0123456789ABCDEF'\n\ndef digit_value(ch):\n    pass\n\ndef to_decimal(text, base):\n    pass\n\n"
                "def from_decimal(number, base):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n"),
    "cases": input_cases(base, ("Example 1: typed 12, 5, and 2A", ["12", "5", "2A"]), ("Example 2: typed 16, 2, and 000", ["16", "2", "000"]),
                         ("Example 3: typed 1 and 10", ["1", "10"]), ("Typed 10, 16, and 255", ["10", "16", "255"]),
                         ("Typed 2, 10, and 101101", ["2", "10", "101101"]), ("Typed 16, 16, and 0FF", ["16", "16", "0FF"]),
                         ("Typed 10, 17", ["10", "17"]), ("Typed 16, 10, and FFFFFFFFFFFF", ["16", "10", "FFFFFFFFFFFF"])),
    "check": FN + '''_fn("digit_value", "ch")
_fn("to_decimal", "text", "base")
_fn("from_decimal", "number", "base")
_fn("main")
assert globals().get("DIGITS") == "0123456789ABCDEF", "Keep the constant DIGITS = '0123456789ABCDEF'."
_tree = ast.parse(__source__)
for _n in ast.walk(_tree):
    if isinstance(_n, ast.Call) and isinstance(_n.func, ast.Name):
        assert _n.func.id not in ("bin", "oct", "hex"), "Convert by repeated integer division; do not use " + _n.func.id + "."
        assert not (_n.func.id == "int" and len(_n.args) + len(_n.keywords) >= 2), "Convert by place-value accumulation; do not use int(text, base)."
assert "digit_value" in globals()["to_decimal"].__code__.co_names, "In to_decimal, use digit_value for each character."
_local_state()
''' + "".join(f"_returns('digit_value', {a!r}, {base_ns['digit_value'](*a)!r})\n" for a in VALUE_CALLS)
      + "".join(f"_returns('to_decimal', {a!r}, {base_ns['to_decimal'](*a)!r})\n" for a in DEC_CALLS)
      + "".join(f"_returns('from_decimal', {a!r}, {base_ns['from_decimal'](*a)!r})\n" for a in FROM_CALLS) + "_guard()\n",
    "hints": [
        "`digit_value` finds the position of `ch` in `DIGITS`: start `value` at 0 and add 1 while `DIGITS[value] != ch`. For `'A'` it returns 10.",
        "`to_decimal` starts `number` at 0 and, for each character from left to right, sets `number = number * base + digit_value(ch)`. For `2A` in base 12 that gives 2, then 2 * 12 + 10, which is 34.",
        "`from_decimal` returns `'0'` for zero. Otherwise, while `number > 0`, put `DIGITS[number % base]` at the front of `text` and set `number = number // base`. For 34 in base 5 the remainders are 4, 1, 1, so the result is `114`.",
        "In `main`, read both bases first. If either is below 2 or above 16, print `Invalid base.` and `return` before reading the number text. Otherwise read the text and print `from_decimal(to_decimal(text, source_base), target_base)`.",
    ],
    "answer": b64(base),
    "answerNote": "The first conversion accumulates place values from left to right. The second repeatedly removes the last digit and places it at the front "
                  "of the result. The zero case needs a separate return because the division loop would otherwise produce an empty string."}
assert [c["expected"] for c in E["base"]["cases"][:3]] == ["114", "0", "Invalid base."]

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-20-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 20 Boss Problems",
    "short": "L20 bosses",
    "subtitle": "Stepwise refinement and variable scope",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-20/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
