"""Build workbooks/lecture-19/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_19_SHARED_CONTENT.tex; model answers follow its \\solution{...}
text. Run from anywhere:

    python3 workbooks/lecture-19/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-19
"""
import base64, json, subprocess, sys, pathlib

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
    return out(wrapper)

def example(code, output=True):
    spec = {"type": "example", "code": code.rstrip("\n")}
    if output:
        spec["output"] = out(code)
    return spec

def input_cases(code, *runs):
    return [{"name": name, "inputs": list(inputs), "expected": run_with_prompts(code, inputs)} for name, inputs in runs]

def accept(*values, width="8rem", placeholder="answer"):
    return {"accept": list(values), "placeholder": placeholder, "width": width}

def short(answer, xp=2, min_chars=15, rows=3, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

def namespace(code):
    ns = {"__name__": "lecture19"}
    exec(code, ns)
    return ns

def quoted(text):
    """Accepted spellings of a returned string: with single or double quotes, or bare."""
    return [repr(text), '"' + text + '"', text] if text else ["''", '""', "empty", "the empty string", "empty string"]

E = {}

# ---------------------------------------------------------------- checks shared by the coding tasks
# A check runs after the student's program in the same namespace (a copy of it).
# `_fn` finds a function the program defined and checks its parameters. `_call`
# calls it with its output captured, so the test call does not add to the
# program's own output. `_guard` looks for the standard guard as the last
# statement of the file.
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
        raise AssertionError(call + " returned None. Send the result back with return.")
    if isinstance(want, bool):
        ok = value is want
    elif isinstance(want, (int, float)):
        ok = isinstance(value, (int, float)) and not isinstance(value, bool) and abs(value - want) < 1e-9
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
'''

def returns(name, ns, *calls):
    """Check lines that compare each call's returned value with the model's."""
    return "".join(f"_returns({name!r}, {args!r}, {ns[name](*args)!r})\n" for args in calls)

# ============================================================ 1. Positional arguments
positional = '''def make_label(text, width, symbol):
    return symbol * width + " " + text

print(make_label("Sale", 3, "!"))
'''
E["ex-positional"] = example(positional)
assert E["ex-positional"]["output"] == "!!! Sale"

# ============================================================ 2. Keyword and mixed arguments
# The listings in this section are calls without the definition, shown as static code.
for call in ['make_label("Sale", 3, "!")', 'make_label(symbol="!", text="Sale", width=3)',
             'make_label("Sale", 3, symbol="!")', 'make_label("Sale", width=3, symbol="!")']:
    assert out(positional + f"print({call})\n").endswith("!!! Sale")
assert "SyntaxError" in run(positional + 'make_label(text="Sale", 3, "!")\n', ok=False)[1]
assert "TypeError" in run(positional + 'make_label("Sale", text="Deal",\n           width=3, symbol="!")\n', ok=False)[1]

# ============================================================ 3. Defaults and parameter order
defaults = '''def make_label(text, width=3, symbol="-"):
    return symbol * width + " " + text
'''
E["ex-defaults"] = example(defaults, output=False)
assert out(defaults + 'print(make_label("Sale"))\nprint(make_label("Sale", 5))\nprint(make_label("Sale", symbol="*"))\n') == "--- Sale\n----- Sale\n*** Sale"
label_ok = '''def label(text, width=3):
    return "-" * width + text
'''
E["ex-label-valid"] = example(label_ok, output=False)
assert "SyntaxError" in run('def label(width=3, text):\n    return "-" * width + text\n', ok=False)[1]

# Checkpoint 1
cp1_program = '''def make_label(text, width=3, symbol="-"):
    return symbol * width + " " + text

print(make_label("Go", symbol="!"))
print(make_label(symbol="*", text="Hi", width=2))
print(make_label("OK", 4, "="))
'''
cp1_answer = '''def make_label(text, width=3, symbol="-"):
    return symbol * width + " " + text

print(make_label("Go", symbol="!"))
print(make_label(symbol="*", text="Hi", width=2))
print(make_label(text="OK",
                 width=4,
                 symbol="="))
'''
assert out(cp1_program) == out(cp1_answer) == "!!! Go\n** Hi\n==== OK"
E["cp1-predict"] = {"type": "table", "xp": 1, "blanks": {
    "l1": accept("!!! Go", '"!!! Go"', "'!!! Go'", placeholder="printed line"),
    "l2": accept("** Hi", '"** Hi"', "'** Hi'", placeholder="printed line"),
    "l3": accept("==== OK", '"==== OK"', "'==== OK'", placeholder="printed line"),
}}
for key in E["cp1-predict"]["blanks"]:
    E["cp1-predict"]["blanks"][key]["caseSensitive"] = True
E["cp1"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": cp1_program,
    "cases": [{"name": "Program output", "expected": out(cp1_program)}],
    "check": FN + '''_calls = [n for n in ast.walk(ast.parse(__source__)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "make_label"]
_ok_calls = [c for c in _calls if any(isinstance(k.value, ast.Constant) and k.value.value == "OK" for k in c.keywords)
             or any(isinstance(a, ast.Constant) and a.value == "OK" for a in c.args)]
assert len(_calls) == 3 and len(_ok_calls) == 1, "Keep the three print calls. Rewrite only the third one."
_third = _ok_calls[0]
assert not _third.args and sorted(k.arg for k in _third.keywords) == ["symbol", "text", "width"], "Rewrite the third call with only keyword arguments: text=, width=, and symbol=."
''',
    "answer": b64(cp1_answer),
    "answerNote": 'First call: `width` keeps its default, `3`. Second call: every value binds by name, even in a different order. '
                  'The returned string is still `"==== OK"`.'}

# ============================================================ 4. Main coordinates the program
main_steps = '''def main():
    print("Starting")
    for number in range(1, 4):
        print(number)

main()
'''
E["ex-main"] = example(main_steps)
assert E["ex-main"]["output"] == "Starting\n1\n2\n3"
fahrenheit = '''def to_fahrenheit(celsius):
    return celsius * 9 / 5 + 32

def main():
    temperature = float(input("Celsius: "))
    converted = to_fahrenheit(temperature)
    print(converted)

main()
'''
E["ex-fahrenheit"] = example(fahrenheit, output=False)
assert run_with_prompts(fahrenheit, ["20"]) == "Celsius: 68.0"

# ============================================================ 5. Definitions before calls
before = '''def main():
    print(cube_volume(2))

def cube_volume(side):
    return side ** 3

main()
'''
E["ex-before"] = example(before, output=False)
assert out(before) == "8"
assert "NameError" in run("print(cube_volume(2))\n", ok=False)[1]

# ============================================================ 6. The name guard
demo = '''# demo.py
def main():
    print("Ready")

if __name__ == "__main__":
    main()
'''
E["ex-demo"] = example(demo, output=False)
assert out(demo) == "Ready"
assert namespace(demo)["__name__"] == "lecture19"  # imported: the guard skips main()

# ============================================================ 7. The course program layout
layout = '''import math
TAX_RATE = 0.15

def rounded_total(subtotal):
    taxed = subtotal * (1 + TAX_RATE)
    return math.ceil(taxed)

def main():
    print(rounded_total(20))

if __name__ == "__main__":
    main()
'''
E["ex-layout"] = example(layout, output=False)
assert out(layout) == "23"

# Checkpoint 2
fee = '''def fee(total, rate=0.1):
    return total * rate

def main():
    print(fee(20, rate=0.2))

if __name__ == "__main__":
    main()
'''
assert out(fee) == "4.0"
assert out(f"import sys, types\nm = types.ModuleType('fee_demo')\nexec({fee!r}, m.__dict__)\n") == ""
E["cp2-run"] = {"type": "table", "xp": 1, "blanks": {"run": accept("4.0", placeholder="output", width="6rem")}}
E["cp2"] = short('Run directly: `4.0`. The explicit keyword argument uses `rate=0.2`, replacing the default `0.1`.\n\n'
                 'Import: No automatic output. Python defines the functions, but the guard skips the call to `main()`.\n\n'
                 'The condition checks whether `__name__` equals `"__main__"`.',
                 min_chars=30, rows=4, placeholder="Run directly: … Import: … Rate: … The guard checks: …")

# ============================================================ 8. Functions calling functions
share = '''def share(total, people):
    return total / people

def show_share(total, people):
    amount = share(total, people)
    print(amount)

def main():
    show_share(36, 3)

if __name__ == "__main__":
    main()
'''
E["ex-share"] = example(share, output=False)
assert out(share) == "12.0"

# ============================================================ 9. The call stack and frames
# Static table and the two one-line listings; they come from the program in Section 8.

# ============================================================ 10. Reading tracebacks
# bill.py and its traceback are shown as static code and output. Check the
# traceback lines against a real run under the file name bill.py.
bill = share.replace("show_share(36, 3)", "show_share(36, 0)")
tb = subprocess.run([sys.executable, "-c", f"exec(compile({bill!r}, 'bill.py', 'exec'))"], capture_output=True, text=True).stderr
for line in ['File "bill.py", line 12, in <module>', 'File "bill.py", line 9, in main', 'File "bill.py", line 5, in show_share',
             'File "bill.py", line 2, in share', "ZeroDivisionError: division by zero"]:
    assert line in tb, (line, tb)

# Checkpoint 3
assert "unsupported operand type(s) for /: 'str' and 'int'" in run('print("18" / 3)\n', ok=False)[1]
assert out("print(18 / 3)\n") == "6.0"
E["cp3-read"] = {"type": "table", "xp": 1, "blanks": {
    "type": accept("TypeError", placeholder="error type"),
    "active": accept("ratio", "ratio()", placeholder="function"),
    "bottom": accept("main", "main()", placeholder="function"),
    "middle": accept("print_ratio", "print_ratio()", placeholder="function"),
    "top": accept("ratio", "ratio()", placeholder="function"),
    "fix": accept("print_ratio(18, 3)", "print_ratio(18,3)", "print_ratio(18.0, 3)", "print_ratio(18.0,3)", placeholder="corrected call", width="11rem"),
    "output": accept("6.0", placeholder="output", width="6rem"),
}}
E["cp3"] = short('`TypeError`: `ratio` tries to divide a string by an integer on line 2.\n\n'
                 'The string `"18"` enters on line 8 in `main`. Use a number: `print_ratio(18, 3)`\n\n'
                 'The corrected program prints `6.0`.\n\n'
                 'The function frames from bottom to top are `main`, `print_ratio`, and `ratio`. The active function at the failure is `ratio`.',
                 min_chars=30, rows=4, placeholder="The argument that caused the problem, where it entered, and the fix…")

# ============================================================ Coding Practice
# 1. Trace a cube report
cube_report = '''def cube(number):
    return number ** 3

def main():
    small = cube(3)
    large = cube(5)
    print(small)
    print(large)

if __name__ == '__main__':
    main()
'''
assert out(cube_report) == "27\n125"
E["p1-trace"] = short("`main` calls `cube(3)`, which returns `27`; `main` stores it in `small`. It calls `cube(5)`, which returns `125`, "
                      "and stores it in `large`. It then executes the two print calls, in order. The output is:\n`27`\n`125`",
                      min_chars=40, rows=6, placeholder="The statements that execute, in order, including each return…")
E["p1-output"] = {"type": "table", "xp": 1, "blanks": {"l1": accept("27", placeholder="output", width="6rem"),
                                                         "l2": accept("125", placeholder="output", width="6rem")}}

# 2. Return behaviour
TRUTH = ["false", "true", "false", "false", "true", "true", "true"]
E["p2"] = {"type": "table", "xp": 1, "blanks": {
    f"s{i}": {"accept": [v, v[0]], "placeholder": "true or false", "width": "7rem", "show": v.capitalize()}
    for i, v in enumerate(TRUTH, 1)}}
E["p2-why"] = short("1. False. A function can reach the end of its body and return `None`.\n"
                    "2. True. Different branches can contain different returns.\n"
                    "3. False. `return` ends the current call.\n"
                    "4. False. For example, a function can call `random.randint` without receiving a parameter.\n"
                    "5. True. A function may do other work or simply finish, returning `None`.\n"
                    "6. True. A bare `return` ends the call and returns `None`.\n"
                    "7. True. A call follows one execution path and returns one object.",
                    min_chars=60, rows=7, placeholder="1. … 2. … (one reason for each statement)")
# Check the two claims that can be run.
assert out("def f():\n    x = 1\nprint(f())\n") == "None"
assert out("def f():\n    return\n    print('no')\nprint(f())\n") == "None"

# 3. Trace number names
names = '''def small_name(number):
    if number == 1:
        return 'one'
    if number == 2:
        return 'two'
    if number == 3:
        return 'three'
    if number == 4:
        return 'four'
    return ''

def number_name(number):
    if 1 <= number <= 4:
        return small_name(number)
    if number == 20:
        return 'twenty'
    if 21 <= number <= 24:
        return 'twenty-' + small_name(number - 20)
    return ''
'''
names_ns = namespace(names)
NAME_CALLS = [4, 20, 23, 0, -3, 25]
assert [names_ns["number_name"](n) for n in NAME_CALLS] == ["four", "twenty", "twenty-three", "", "", ""]
E["p3"] = {"type": "table", "xp": 1, "blanks": {
    f"r{i}": {"accept": quoted(names_ns["number_name"](n)), "placeholder": "string", "width": "9rem",
              "show": repr(names_ns["number_name"](n))}
    for i, n in enumerate(NAME_CALLS, 1)}}
E["p3-why"] = short("The returned strings are `'four'`, `'twenty'`, `'twenty-three'`, `''`, `''`, and `''`, in that order. "
                    "The first call uses `small_name(4)`. The second returns directly. The third uses `small_name(3)` after subtracting 20. "
                    "The final three calls reach the last return.",
                    min_chars=40, rows=5, placeholder="For each call: the branch taken and any helper argument…")

# 4. Trace a loop with returns
halvings = '''def count_halvings(number):
    if number < 0:
        return -1
    count = 0
    while number > 1:
        if number % 2 != 0:
            return count
        number = number // 2
        count = count + 1
    return count
'''
halv_ns = namespace(halvings)
HALV_CALLS = [-2, 0, 1, 8, 12]
assert [halv_ns["count_halvings"](n) for n in HALV_CALLS] == [-1, 0, 0, 3, 2]
E["p4"] = {"type": "table", "xp": 1, "blanks": {
    f"r{i}": accept(str(halv_ns["count_halvings"](n)), placeholder="value", width="5rem") for i, n in enumerate(HALV_CALLS, 1)}}
E["p4-trace"] = short("For `-2`, the first return gives `-1` before `count` is created. For `0` and `1`, the loop does not run and the result is `0`. "
                      "For `8`, the pairs `(number, count)` are `(4, 1)`, `(2, 2)`, `(1, 3)`, so the result is `3`. "
                      "For `12`, the pairs are `(6, 1)` and `(3, 2)`; the odd value `3` triggers a return of `2`.",
                      min_chars=40, rows=5, placeholder="The (number, count) pairs after each completed iteration…")

# 5. Separate call frames
exchange = '''def exchange(first, second):
    saved = first
    first = second
    second = saved

def main():
    left = 6
    right = 9
    exchange(left, right)
    print(left, right)

if __name__ == '__main__':
    main()
'''
assert out(exchange) == "6 9"
E["p5"] = {"type": "table", "xp": 1, "blanks": {"out": accept("6 9", placeholder="output", width="6rem")}}
E["p5-why"] = short("The output is `6 9`. `exchange` changes the names `first` and `second` in its own frame. "
                    "The names `left` and `right` in the waiting `main` frame still have the values `6` and `9`.",
                    min_chars=30, rows=4, placeholder="Explain using the two calls' frames…")

# 6. Geometry helpers
geometry = '''import math

def sphere_volume(radius):
    return 4 * math.pi * radius ** 3 / 3

def sphere_surface(radius):
    return 4 * math.pi * radius ** 2

def cylinder_volume(radius, height):
    return math.pi * radius ** 2 * height

def cylinder_surface(radius, height):
    return 2 * math.pi * radius * (radius + height)

def cone_volume(radius, height):
    return math.pi * radius ** 2 * height / 3

def cone_surface(radius, height):
    slant = math.sqrt(radius ** 2 + height ** 2)
    return math.pi * radius * (radius + slant)

def main():
    radius = float(input('Radius: '))
    height = float(input('Height: '))
    print(f'Sphere volume: {sphere_volume(radius):.2f}')
    print(f'Sphere surface: {sphere_surface(radius):.2f}')
    print(f'Cylinder volume: {cylinder_volume(radius, height):.2f}')
    print(f'Cylinder surface: {cylinder_surface(radius, height):.2f}')
    print(f'Cone volume: {cone_volume(radius, height):.2f}')
    print(f'Cone surface: {cone_surface(radius, height):.2f}')

if __name__ == '__main__':
    main()
'''
geo_ns = namespace(geometry)
assert run_with_prompts(geometry, ["3", "4"]) == ("Radius: Height: Sphere volume: 113.10\nSphere surface: 113.10\nCylinder volume: 113.10\n"
                                                  "Cylinder surface: 131.95\nCone volume: 37.70\nCone surface: 75.40")

def report_case(name, code, inputs, label):
    """Check-only case: any prompts are accepted, so compare the report lines
    with the prompts removed from the front of the first one."""
    with_prompts = run_with_prompts(code, inputs)
    prompts = "Radius: Height: "
    assert with_prompts.startswith(prompts)
    want = with_prompts[len(prompts):].split("\n")
    check = f'''_want = {want!r}
_got = [line.rstrip() for line in __stdout__.rstrip("\\n").split("\\n")]
assert len(_got) == len(_want), "{label}, print exactly six report lines, one per measurement."
assert _got[0].endswith(_want[0]), "{label}, the first report line should end with " + repr(_want[0]) + "."
for _i in range(1, len(_want)):
    assert _got[_i] == _want[_i], "{label}, line " + str(_i + 1) + " should be " + repr(_want[_i]) + ", not " + repr(_got[_i]) + "."
'''
    return {"name": name, "inputs": list(inputs), "check": check}

GEO_ONE = ["sphere_volume", "sphere_surface"]
GEO_TWO = ["cylinder_volume", "cylinder_surface", "cone_volume", "cone_surface"]
geo_check = FN + "".join(f'_fn({n!r}, "radius")\n' for n in GEO_ONE) + "".join(f'_fn({n!r}, "radius", "height")\n' for n in GEO_TWO)
geo_check += '_fn("main")\n'
geo_check += 'assert re.search(r"\\bmath\\.pi\\b", __code__), "Use math.pi."\n'
geo_check += 'assert re.search(r"\\bmath\\.sqrt\\s*\\(", __code__), "Use math.sqrt for the slant length s."\n'
for n in GEO_ONE:
    geo_check += returns(n, geo_ns, (1.0,), (2.5,))
for n in GEO_TWO:
    geo_check += returns(n, geo_ns, (1.0, 1.0), (2.0, 3.0))
geo_check += '_guard()\n'
E["p6"] = {"type": "code", "xp": 10, "minLines": 32,
    "starter": ("import math\n\n# Define the six helpers here.\n\ndef main():\n    # Read the radius and the height, call all six helpers,\n"
                "    # and print the labeled results to two decimal places.\n\nif __name__ == '__main__':\n    main()\n"),
    "cases": [report_case("Radius 3 and height 4", geometry, ["3", "4"], "For radius 3 and height 4"),
              report_case("Radius 1 and height 1", geometry, ["1", "1"], "For radius 1 and height 1"),
              report_case("Radius 2.5 and height 10", geometry, ["2.5", "10"], "For radius 2.5 and height 10"),
              report_case("Radius 0.5 and height 0.2", geometry, ["0.5", "0.2"], "For radius 0.5 and height 0.2")],
    "check": geo_check,
    "answer": b64(geometry),
    "answerNote": "Each helper returns one calculation. `main` handles input and formatting."}

# 7. Read a number
reader = '''def read_number(prompt='Value:'):
    return float(input(prompt + ' '))

def main():
    first = read_number()
    second = read_number(prompt='Next:')
    print(f'Total: {first + second:.1f}')

if __name__ == '__main__':
    main()
'''
E["p7"] = {"type": "code", "xp": 10, "minLines": 10,
    "starter": ("def read_number(prompt='Value:'):\n    # Read and return a float, using the prompt followed by one space.\n\n"
                "def main():\n    # Read two numbers and print their total to one decimal place.\n\nif __name__ == '__main__':\n    main()\n"),
    "cases": input_cases(reader, ("Typed 2.5 and 4", ["2.5", "4"]), ("Typed 0 and 0", ["0", "0"]), ("Typed 1.25 and -3", ["1.25", "-3"])),
    "check": FN + '''_f = _fn("read_number", "prompt")
assert _f.__defaults__ == ("Value:",), "Give read_number the default prompt='Value:'."
assert "input" in _f.__code__.co_names and "float" in _f.__code__.co_names, "Read the number with input() and convert it with float() inside read_number."
_fn("main")
_calls = [n for n in _body("main") if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "read_number"]
assert any(not c.args and not c.keywords for c in _calls), "In main, read the first number with the default prompt: read_number()."
assert any(not c.args and [k.arg for k in c.keywords] == ["prompt"] and isinstance(c.keywords[0].value, ast.Constant)
           and c.keywords[0].value.value == "Next:" for c in _calls), "Read the second number with the keyword call read_number(prompt='Next:')."
_guard()
''',
    "answer": b64(reader),
    "answerNote": "The helper returns the converted input. `main` calls it twice and prints the total."}
assert [c["expected"] for c in E["p7"]["cases"][:2]] == ["Value: Next: Total: 6.5", "Value: Next: Total: 0.0"]

# 8. Order credit
credit = '''def order_credit(total, items):
    if total < 40:
        return 3 * items
    if total < 80 and items >= 2:
        return 2 * items
    if total <= 120 and items >= 3:
        return items
    return 0

def main():
    total = float(input('Total (-1 to stop): '))
    while total != -1:
        items = int(input('Items: '))
        credit = order_credit(total, items)
        print(f'Credit: ${credit:.2f}')
        total = float(input('Total (-1 to stop): '))

if __name__ == '__main__':
    main()
'''
credit_ns = namespace(credit)

def credit_case(name, inputs):
    printed = run_with_prompts(credit, inputs)
    want = [line.split("Items: ")[-1] for line in printed.split("\n") if "Credit: " in line]
    check = f'''_want = {want!r}
_got = re.findall(r"Credit: \\$\\S*", __stdout__)
assert len(_got) == len(_want), "Print one Credit line for each order: " + str(len(_want)) + " here, not " + str(len(_got)) + "."
for _i in range(len(_want)):
    assert _got[_i] == _want[_i], "Order " + str(_i + 1) + " should print " + repr(_want[_i]) + ", not " + repr(_got[_i]) + "."
'''
    return {"name": name, "inputs": list(inputs), "check": check}

CREDIT_CALLS = [(39.0, 1), (40.0, 2), (80.0, 3), (120.0, 2), (0.0, 0), (39.99, 4), (40.0, 1), (79.99, 2), (79.99, 1),
                (80.0, 2), (120.0, 3), (120.01, 3), (100.0, 5), (150.0, 10)]
E["p8"] = {"type": "code", "xp": 10, "minLines": 20,
    "starter": ("def order_credit(total, items):\n    # Return the credit for one order.\n\n"
                "def main():\n    # Read totals until -1, reading the item count only for an order.\n\nif __name__ == '__main__':\n    main()\n"),
    "cases": [credit_case("Orders (39, 1), (40, 2), (80, 3), (120, 2), then -1", ["39", "1", "40", "2", "80", "3", "120", "2", "-1"]),
              credit_case("The sentinel -1 first", ["-1"]),
              credit_case("Orders (79.99, 2), (120.01, 3), (0, 0), then -1", ["79.99", "2", "120.01", "3", "0", "0", "-1"])],
    "check": FN + '_fn("order_credit", "total", "items")\n_fn("main")\n' + returns("order_credit", credit_ns, *CREDIT_CALLS) + "_guard()\n",
    "answer": b64(credit),
    "answerNote": "The report lines for the four orders are `Credit: $3.00`, `Credit: $4.00`, `Credit: $3.00`, and `Credit: $0.00`. "
                  "With `-1` first, the program prints no credit and does not ask for an item count."}
assert E["p8"]["cases"][0]["check"].startswith("_want = ['Credit: $3.00', 'Credit: $4.00', 'Credit: $3.00', 'Credit: $0.00']")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-19",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 19 Workbook",
    "subtitle": "Argument styles, main(), and the call stack",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-19/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
