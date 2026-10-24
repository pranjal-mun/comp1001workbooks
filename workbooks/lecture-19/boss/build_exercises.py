"""Build workbooks/lecture-19/boss/exercises.json: the Lecture 19 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_19_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Run from anywhere:

    python3 workbooks/lecture-19/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-19/boss
"""
import base64, json, random, re, subprocess, sys, pathlib

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
    ns = {"__name__": "lecture19_boss"}
    exec(code, ns)
    return ns

# A check runs after the student's program in a copy of its namespace. `_fn`
# finds a function the program defined; `_call` calls it with its output
# captured, so the test call does not add to the program's own output. `_guard`
# looks for the standard guard as the last statement of the file.
FN = '''import types, io, contextlib, re, ast
_WORDS = ["empty parentheses", "one parameter", "two parameters", "three parameters"]
def _fn(name, *params):
    f = globals().get(name)
    assert isinstance(f, types.FunctionType), "Define a function named " + name + " with def."
    assert f.__code__.co_argcount == len(params), "Define " + name + "(" + ", ".join(params) + ") with " + _WORDS[len(params)] + "."
    return f
def _call(name, *args, **kwargs):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        value = globals()[name](*args, **kwargs)
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
'''

E = {}

# ---------------------------------------------------------------- 1 Centered text
center = """def center_text(text, width=24):
    if len(text) >= width:
        return text
    spaces = (width - len(text)) // 2
    return ' ' * spaces + text

def main():
    text = input()
    width = int(input())
    print('|' + center_text(text, width=width) + '|')

if __name__ == '__main__':
    main()
"""
center_ns = namespace(center)
assert center_ns["center_text"]("Hi") == " " * 11 + "Hi"
CENTER_CALLS = [("Hi", 9), ("wide", 0), ("", 4), ("abc", 3), ("abc", 4), ("ab", 5), ("ab", 6), ("x", 1), ("long text", 4),
                ("", 0), ("", 1), ("A" * 80, 80), ("odd", 80)]
E["center"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 12,
    "starter": ("def center_text(text, width=24):\n    # Return the text with the required leading spaces.\n\n"
                "def main():\n    text = input()\n    width = int(input())\n    # Print the helper's result between | characters.\n\n"
                "if __name__ == '__main__':\n    main()\n"),
    "cases": input_cases(center, ("Example 1: typed Hi and 9", ["Hi", "9"]), ("Example 2: typed wide and 0", ["wide", "0"]),
                         ("Example 3: typed an empty line and 4", ["", "4"]), ("Typed abc and 3", ["abc", "3"]),
                         ("Typed ab and 5", ["ab", "5"]), ("Typed ab and 6", ["ab", "6"]),
                         ("Typed Centered text and 24", ["Centered text", "24"])),
    "check": FN + '''_f = _fn("center_text", "text", "width")
assert _f.__defaults__ == (24,), "Give center_text the default width=24."
_fn("main")
_c = _calls_in("main", "center_text")
assert _c and all([k.arg for k in c.keywords] == ["width"] for c in _c), "In main, call center_text with width as a keyword argument: center_text(text, width=width)."
_value, _ = _call("center_text", "Hi")
assert _value == " " * 11 + "Hi", "center_text('Hi') uses the default width 24 and should return 11 spaces followed by Hi, not " + repr(_value) + "."
''' + "".join(f"_returns('center_text', {args!r}, {center_ns['center_text'](*args)!r})\n" for args in CENTER_CALLS) + "_guard()\n",
    "hints": [
        "If `len(text) >= width`, there is no spare space, so return `text` unchanged. For `wide` and width 0 this returns `wide`.",
        "Otherwise the spare space is `width - len(text)`. Integer division by 2 gives the smaller half: for `Hi` and 9 the spare space is 7 and `7 // 2` is 3.",
        "Return `' ' * spaces + text`, with no spaces after the text. In `main`, print `'|' + center_text(text, width=width) + '|'`.",
    ],
    "answer": b64(center),
    "answerNote": "The length check handles text that fills or exceeds the width. Integer division chooses the smaller half of any spare space. "
                  "`center_text('Hi')` returns eleven spaces followed by `Hi`."}
assert [c["expected"] for c in E["center"]["cases"][:3]] == ["|   Hi|", "|wide|", "|  |"]

# ---------------------------------------------------------------- 2 Ordinal words
ordinal = """def ordinal_word(number):
    if number == 1:
        return 'first'
    if number == 2:
        return 'second'
    if number == 3:
        return 'third'
    if number == 4:
        return 'fourth'
    if number == 5:
        return 'fifth'
    if number == 6:
        return 'sixth'
    if number == 7:
        return 'seventh'
    if number == 8:
        return 'eighth'
    if number == 9:
        return 'ninth'
    if number == 10:
        return 'tenth'
    if number == 11:
        return 'eleventh'
    if number == 12:
        return 'twelfth'
    return ''

def main():
    for number in range(1, 13):
        print(number, ordinal_word(number))

if __name__ == '__main__':
    main()
"""
ord_ns = namespace(ordinal)
WORDS = [ord_ns["ordinal_word"](n) for n in range(1, 13)]
E["ordinal"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 30,
    "starter": ("def ordinal_word(number):\n    # Return a word or the empty string.\n\n"
                "def main():\n    # Print the twelve integer-word pairs.\n\nif __name__ == '__main__':\n    main()\n"),
    "cases": [{"name": "Example 1: run main", "expected": run(ordinal)}],
    "check": FN + f'''_fn("ordinal_word", "number")
_fn("main")
assert any(isinstance(n, (ast.For, ast.While)) for n in _body("main")), "Use a loop in main to print the twelve pairs."
_value, _ = _call("ordinal_word", 0)
assert _value == "", "Example 2: ordinal_word(0) should return the empty string, so '|' + ordinal_word(0) + '|' prints ||."
_words = {WORDS!r}
for _n in range(-100, 101):
    _returns("ordinal_word", (_n,), _words[_n - 1] if 1 <= _n <= 12 else "")
_guard()
''',
    "hints": [
        "Compare `number` with each value from 1 to 12 and return the matching word at once: `if number == 1:` returns `'first'`.",
        "After the twelve tests, a final `return ''` handles every other integer, including the boundaries 0 and 13.",
        "In `main`, loop with `for number in range(1, 13):` and print `number, ordinal_word(number)`. The first line is `1 first`.",
    ],
    "answer": b64(ordinal),
    "answerNote": "Each matching branch returns immediately. The final return handles every integer outside the supported range."}
assert E["ordinal"]["cases"][0]["expected"].split("\n")[0] == "1 first"
assert len(E["ordinal"]["cases"][0]["expected"].split("\n")) == 12

# ---------------------------------------------------------------- 3 Random plate codes
plate = """import random

def random_letters(count=2):
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    result = ''
    for position in range(count):
        index = random.randint(0, 25)
        result = result + letters[index]
    return result

def random_digits(count=4):
    result = ''
    for position in range(count):
        result = result + str(random.randint(0, 9))
    return result

def make_plate():
    if random.randint(0, 1) == 0:
        return random_letters() + random_digits()
    return random_digits(count=3) + random_letters(count=3)

def main():
    print(make_plate())

if __name__ == '__main__':
    main()
"""
PLATE_RE = r"^([A-Z]{2}[0-9]{4}|[0-9]{3}[A-Z]{3})$"
assert re.match(PLATE_RE, run(plate))

# The scripted choices replace random.randint while make_plate runs. Each
# call randint(a, b) returns a plus the next scripted value, so the choices
# read as the example states them (format 0 or 1, letter indexes, digits).
SCRIPT = '''import random as _random
def _scripted(name, choices):
    _queue = list(choices)
    _real = _random.randint
    _f = globals().get(name)
    _g = _f.__globals__
    _had = "randint" in _g
    _old = _g.get("randint")
    def _fake(a, b):
        assert _queue, name + "() asked random.randint for more choices than the example lists."
        return a + _queue.pop(0)
    _random.randint = _fake
    if _had:
        _g["randint"] = _fake
    try:
        _value, _ = _call(name)
    finally:
        _random.randint = _real
        if _had:
            _g["randint"] = _old
    return _value
'''
plate_example1 = SCRIPT + '''_value = _scripted("make_plate", [0, 0, 25, 0, 4, 0, 7])
assert _value == "AZ0407", "Example 1: with the choices format 0, letter indexes 0 and 25, then digits 0, 4, 0, 7, make_plate() should return 'AZ0407', not " + repr(_value) + "."
'''
plate_example2 = SCRIPT + '''_value = _scripted("make_plate", [1, 0, 0, 0, 1, 1, 1])
assert _value == "000BBB", "Example 2: with the choices format 1, digits 0, 0, 0, then letter indexes 1, 1, 1, make_plate() should return '000BBB', not " + repr(_value) + "."
'''
plate_main = f'''_lines = __stdout__.rstrip("\\n").split("\\n")
assert len(_lines) == 1 and re.match(r"{PLATE_RE}", _lines[0]), "main should print one plate code: two letters and four digits, or three digits and three letters. It printed " + repr(__stdout__.rstrip()) + "."
'''
plate_many = f'''_seen = set()
for _i in range(200):
    _value, _ = _call("make_plate")
    assert isinstance(_value, str) and re.match(r"{PLATE_RE}", _value), "make_plate() should return two uppercase letters and four digits, or three digits and three uppercase letters, not " + repr(_value) + "."
    _seen.add(_value[0].isalpha())
assert _seen == {{True, False}}, "In 200 calls make_plate() should produce both formats. Choose the format with random.randint(0, 1)."
'''
# Make sure the scripted checks pass for the model and reject a swapped order.
E["plate"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 24,
    "starter": ("import random\n\ndef random_letters(count=2):\n    # Build and return count random letters.\n\n"
                "def random_digits(count=4):\n    # Build and return count random digits.\n\n"
                "def make_plate():\n    # Choose a format and call the helpers.\n\n"
                "def main():\n    # Print one plate code.\n\nif __name__ == '__main__':\n    main()\n"),
    "cases": [{"name": "Example 1: format 0, letters 0 and 25, digits 0, 4, 0, 7", "check": plate_example1},
              {"name": "Example 2: format 1, digits 0, 0, 0, letters 1, 1, 1", "check": plate_example2},
              {"name": "main prints one plate code", "check": plate_main},
              {"name": "200 calls to make_plate()", "check": plate_many}],
    "check": FN + '''_l = _fn("random_letters", "count")
_d = _fn("random_digits", "count")
_fn("make_plate")
_fn("main")
assert _l.__defaults__ == (2,), "Give random_letters the default count=2."
assert _d.__defaults__ == (4,), "Give random_digits the default count=4."
assert re.search(r"\\brandint\\s*\\(", __code__), "Use random.randint(a, b) for every random choice."
for _name, _kind in (("random_letters", str.isupper), ("random_digits", str.isdigit)):
    assert any(isinstance(n, (ast.For, ast.While)) for n in _body(_name)), "Use a loop in " + _name + " to build the string one character at a time."
    for _count in range(0, 7):
        _value, _ = _call(_name, _count)
        assert isinstance(_value, str) and len(_value) == _count and (_count == 0 or (_kind(_value) and _value.isascii())), _name + "(" + str(_count) + ") should return a string of " + str(_count) + " random characters, not " + repr(_value) + "."
_kw = [c for name in ("random_letters", "random_digits") for c in _calls_in("make_plate", name)]
assert any([k.arg for k in c.keywords] == ["count"] and not c.args for c in _kw), "In make_plate, use keyword calls such as random_digits(count=3) for the counts that differ from the defaults."
assert any(not c.args and not c.keywords for c in _kw), "In make_plate, let the defaults supply the counts for format 0: random_letters() and random_digits()."
assert _calls_in("main", "make_plate"), "Call make_plate() in main and print its result."
_guard()
''',
    "hints": [
        "Each helper starts with `result = ''` and loops `for position in range(count):`. A count of 0 makes the loop run zero times, so the empty string is returned.",
        "In `random_letters`, `index = random.randint(0, 25)` chooses a position in `'ABCDEFGHIJKLMNOPQRSTUVWXYZ'`; index 25 is `Z`. In `random_digits`, add `str(random.randint(0, 9))`.",
        "In `make_plate`, the first choice is the format: `if random.randint(0, 1) == 0:` returns `random_letters() + random_digits()`. Otherwise return `random_digits(count=3) + random_letters(count=3)`.",
    ],
    "answer": b64(plate),
    "answerNote": "The first random choice selects the format. The helper defaults supply the counts for format 0; keyword calls supply the counts for format 1. "
                  "A zero count makes the loop run zero times, leaving the returned string empty."}

# ---------------------------------------------------------------- 4 Magic date search
magic = """def is_leap_year(year):
    return year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)

def days_in_month(month, year):
    if month == 2:
        if is_leap_year(year):
            return 29
        return 28
    if month == 4 or month == 6 or month == 9 or month == 11:
        return 30
    return 31

def is_magic_date(day, month, year):
    if month < 1 or month > 12:
        return False
    if day < 1 or day > days_in_month(month, year):
        return False
    return day * month == year % 100

def main():
    start = int(input())
    end = int(input())
    for year in range(start, end + 1):
        for month in range(1, 13):
            for day in range(1, days_in_month(month, year) + 1):
                if is_magic_date(day, month, year):
                    print(year, month, day)

if __name__ == '__main__':
    main()
"""
magic_ns = namespace(magic)
assert len(run_with_prompts(magic, ["2000", "2099"]).split("\n")) == 212
LEAP_CALLS = [(y,) for y in (1900, 2000, 2001, 2004, 2024, 2100, 2400)]
MONTH_CALLS = [(m, y) for y in (2000, 2001, 2004, 2100) for m in range(1, 13)]
MAGIC_CALLS = [(2, 2, 2004), (1, 4, 2004), (4, 1, 2004), (30, 2, 2004), (29, 2, 2001), (29, 2, 2000), (1, 13, 2013), (1, 0, 2000),
               (0, 5, 2000), (31, 4, 2024), (12, 2, 2024), (3, 3, 2009), (32, 1, 2032), (11, 9, 2099), (9, 11, 2099), (1, 1, 2000)]
MONTH_GUARD = '''_dim = globals()["days_in_month"]
_g = globals()["is_magic_date"].__globals__
def _guarded(month, year):
    assert 1 <= month <= 12, "is_magic_date called days_in_month(" + str(month) + ", " + str(year) + "). Check that the month is from 1 through 12 first."
    return _dim(month, year)
_g["days_in_month"] = _guarded
try:
    for _args in ((1, 13, 2013), (1, 0, 2000), (5, -1, 2005), (1, 14, 2014)):
        _returns("is_magic_date", _args, False)
finally:
    _g["days_in_month"] = _dim
'''
E["magic"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 28,
    "starter": ("def is_leap_year(year):\n    # Return a Boolean value.\n\n"
                "def days_in_month(month, year):\n    # Return the month's length.\n\n"
                "def is_magic_date(day, month, year):\n    # Check the date and return a Boolean value.\n\n"
                "def main():\n    start = int(input())\n    end = int(input())\n    # Search years, months, and days in order.\n\n"
                "if __name__ == '__main__':\n    main()\n"),
    "cases": input_cases(magic, ("Example 1: typed 2004 and 2004", ["2004", "2004"]), ("Example 2: typed 2000 and 2000", ["2000", "2000"]),
                         ("Typed 2001 and 2001", ["2001", "2001"]), ("Typed 2024 and 2025", ["2024", "2025"]),
                         ("Typed 2099 and 2099", ["2099", "2099"]), ("Typed 2000 and 2099", ["2000", "2099"])),
    "check": FN + '''_fn("is_leap_year", "year")
_fn("days_in_month", "month", "year")
_m = _fn("is_magic_date", "day", "month", "year")
_fn("main")
assert "days_in_month" in _m.__code__.co_names, "is_magic_date must use days_in_month to reject a day past the end of the month."
assert "is_leap_year" in globals()["days_in_month"].__code__.co_names, "days_in_month must use is_leap_year for February."
_loops = [n for n in _body("main") if isinstance(n, (ast.For, ast.While))]
assert any(any(isinstance(m, (ast.For, ast.While)) and m is not n for m in ast.walk(n)) for n in _loops), "Put the nested search loops in main: years, then months, then days."
''' + "".join(f"_returns('is_leap_year', {a!r}, {magic_ns['is_leap_year'](*a)!r})\n" for a in LEAP_CALLS)
    + "".join(f"_returns('days_in_month', {a!r}, {magic_ns['days_in_month'](*a)!r})\n" for a in MONTH_CALLS)
    + "".join(f"_returns('is_magic_date', {a!r}, {magic_ns['is_magic_date'](*a)!r})\n" for a in MAGIC_CALLS)
    + MONTH_GUARD + "_guard()\n",
    "hints": [
        "`is_leap_year` returns one Boolean expression: `year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)`. It is `True` for 2000 and 2004 and `False` for 2001.",
        "`days_in_month` returns 29 or 28 for February, depending on `is_leap_year(year)`, then 30 for months 4, 6, 9, and 11, and 31 for the rest.",
        "`is_magic_date` returns `False` if the month is outside 1 through 12, then `False` if `day < 1 or day > days_in_month(month, year)`. Only then does it return `day * month == year % 100`.",
        "In `main`, loop `for year in range(start, end + 1):`, then over months 1 to 12, then over days 1 to `days_in_month(month, year)`, and print `year, month, day` when `is_magic_date` is true. For 2004 the first match is `2004 1 4`.",
    ],
    "answer": b64(magic),
    "answerNote": "The month check protects the month-length call. The day check rejects dates outside that month. Only valid dates reach the product test."}
assert [c["expected"] for c in E["magic"]["cases"][:2]] == ["2004 1 4\n2004 2 2\n2004 4 1", ""]

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-19-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 19 Boss Problems",
    "short": "L19 bosses",
    "subtitle": "Argument styles, main(), and the call stack",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-19/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
