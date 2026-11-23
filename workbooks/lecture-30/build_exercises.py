"""Build workbooks/lecture-30/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_30_SHARED_CONTENT.tex; the listings below are copied from it and
model answers follow its \\solution{...} text. Run from anywhere:

    python3 workbooks/lecture-30/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-30
"""
import base64, contextlib, io, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=()):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""),
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n")

def run_error(code, inputs=()):
    """Run code that must stop with an exception; return (stdout, exception type)."""
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""),
                       capture_output=True, text=True)
    assert p.returncode != 0, "expected an exception"
    return p.stdout.rstrip("\n"), p.stderr.strip().split("\n")[-1].split(":")[0]

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

def example(code, output=True):
    spec = {"type": "example", "code": code.rstrip("\n")}
    if output:
        spec["output"] = run(code)
    return spec

def accept(*values, width="10rem", placeholder="answer", show=None):
    spec = {"accept": list(values), "placeholder": placeholder, "width": width}
    if show is not None:
        spec["show"] = show
    return spec

def exc(name, width="12rem"):
    return accept(name, width=width, placeholder="exception", show=name)

NONE = accept("none", "None", "no exception", "No exception", "no", width="12rem", placeholder="exception", show="none")

def short(answer, xp=2, min_chars=15, rows=3, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

def input_cases(solution, *runs):
    return [{"name": name, "inputs": list(inputs), "expected": run_with_prompts(solution, inputs)} for name, inputs in runs]

def table(**blanks):
    return {"type": "table", "xp": 1, "blanks": blanks}

def choice(letter):
    return table(c=accept(letter, letter.lower(), width="3.5rem", placeholder="", show=letter))

def true_false(*values):
    return table(**{f"t{i}": accept(str(v), str(v).lower(), width="6rem", placeholder="", show=str(v)) for i, v in enumerate(values, 1)})

# A check runs after the student's program in a copy of its namespace.
# `_H` lists every except handler. `_names(h)` gives the exception names a
# handler lists. `_handles(name)` is true when some handler names that type.
# `_tries()` lists try statements. `_def(name)` is the def node of a function,
# and `_raises(node)` lists the raise statements inside a node. Every exercise
# rejects a bare except and except Exception.
EXC = '''import ast, types, io, contextlib
_TREE = ast.parse(__source__)
_H = [n for n in ast.walk(_TREE) if isinstance(n, ast.ExceptHandler)]
def _names(h):
    t = h.type
    if isinstance(t, ast.Tuple):
        return [e.id for e in t.elts if isinstance(e, ast.Name)]
    return [t.id] if isinstance(t, ast.Name) else []
def _handles(name):
    return any(name in _names(h) for h in _H)
def _tries():
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.Try)]
def _loops():
    return [n for n in ast.walk(_TREE) if isinstance(n, (ast.For, ast.While))]
def _fn(name, *params):
    f = globals().get(name)
    assert isinstance(f, types.FunctionType), "Define a function named " + name + " with def."
    assert f.__code__.co_argcount == len(params), "Define " + name + "(" + ", ".join(params) + ")."
    return f
def _def(name):
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.FunctionDef) and n.name == name][0]
def _raises(node):
    return [n for n in ast.walk(node) if isinstance(n, ast.Raise)]
def _quiet(f, *args):
    """Call f with its output hidden. Return (result, exception type name or None, output)."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            return f(*args), None, buf.getvalue()
    except Exception as e:
        return None, type(e).__name__ + ": " + str(e), buf.getvalue()
assert all(h.type is not None for h in _H), "Do not use a bare except. Name the exception types that you expect."
assert not any(n in ("Exception", "BaseException") for h in _H for n in _names(h)), "Name the specific exception types. Do not use except Exception."
'''

def needs(*names):
    return "".join(f'assert _handles({n!r}), "Add an except block that names {n}."\n' for n in names)
# Listings from the kit, in workbook order.
SRC = {}
SRC['slide_2'] = '''def withdraw(balance, amount):
    """Return balance minus amount.

    amount must be a positive int
    that is at most balance.
    """
    return balance - amount'''
SRC['quick_2'] = '''def check(n):
    if n > 10:
        ____(a)____ ValueError("n must be at most 10")
    return n

try:
    check(12)
except ValueError as ____(b)____:
    print("Too big:", ____(c)____)'''
SRC['slide_4_1'] = '''def withdraw(balance, amount):
    """Return balance minus amount.

    Raises TypeError if amount is not an int.
    Raises ValueError if amount is not positive
    or is more than balance.
    """
    if type(amount) != int:
        raise TypeError("amount must be an int")
    if amount <= 0:
        raise ValueError("amount must be positive")
    if amount > balance:
        raise ValueError("amount is too large")
    return balance - amount'''
SRC['slide_4_2'] = '''print(withdraw(500, 100))
print(withdraw(500, 900))
print("Done")'''
SRC['quick_3'] = '''def half(n):
    if n % 2 != 0:
        raise ValueError("n must be even")
    print("Halving", n)
    return n // 2

print(half(8))
print(half(5))
print("End")'''
SRC['slide_5_1'] = '''def withdraw(balance, amount):
    if amount > balance:
        print("Insufficient funds.")
        return balance
    return balance - amount

balance = withdraw(500, 900)
print("Take your cash.")'''
SRC['slide_5_2'] = '''def withdraw(balance, amount):
    if amount > balance:
        raise ValueError("amount is too large")
    return balance - amount'''
SRC['quick_4'] = '''def find_price(names, prices, name):
    if name not in names:
        print("Not found.")
        return 0
    return prices[names.index(name)]'''
SRC['quick_5'] = '''def get_item(items, position):
    """Return the item at position, counting from 1.

    position must be an int from 1 to len(items).
    """
    if type(position) != int:
        raise ____(a)____("position must be an int")
    if position < 1 or position > len(items):
        raise ____(b)____("position is out of range")
    return items[position - 1]'''
SRC['slide_7'] = '''balance = 500
amount = int(input("Withdraw amount: "))
try:
    balance = withdraw(balance, amount)
except ValueError as err:
    print("Cannot withdraw:", err)
print("Balance:", balance)'''
SRC['quick_6'] = '''def check(n):
    if n < 0:
        raise ValueError("n is negative")
    return n

for n in [4, -1]:
    try:
        print(check(n) * 10)
    except ValueError as err:
        print("Error:", err)'''
SRC['slide_11'] = '''try:
    number = int(input("Number: "))
except ValueError:
    print("Enter a whole number.")
else:
    print(f"Twice that is {number * 2}")'''
SRC['quick_8'] = '''text = input()
try:
    n = int(text)
except ValueError:
    print("Bad")
else:
    print(n + 1)
print("Done")'''
SRC['slide_12_1'] = '''try:
    amount = int(input("Amount: "))
    print(withdraw(500, amount))
except ValueError:
    print("Enter a whole number.")'''
SRC['slide_12_2'] = '''try:
    amount = int(input("Amount: "))
except ValueError:
    print("Enter a whole number.")
else:
    print(withdraw(500, amount))'''
SRC['slide_13'] = '''text = input("People: ")
try:
    share = 60 / int(text)
except ValueError:
    print("Enter a whole number.")
else:
    print(f"Share: {share}")
finally:
    print("Finished.")
print("After the try statement.")'''
SRC['quick_10'] = '''def to_int(text):
    try:
        return int(text)
    finally:
        print("Checked", text)

print(to_int("3"))
print(to_int("a"))'''
SRC['slide_15'] = '''def divide(a_text, b_text):
    try:
        result = int(a_text) / int(b_text)
    except ValueError:
        print("A")
    else:
        print("B", result)
    finally:
        print("C")
    print("D")'''
SRC['slide_17'] = '''def average(values):
    return sum(values) / len(values)

def report(marks):
    avg = average(marks)
    print(f"Average: {avg:.1f}")

report([70, 85, 90])
report([])'''
SRC['quick_12'] = '''def total(values):
    result = 0
    for n in values:
        result = result + n
    return result

print(total([1, 2]))
print(total([3, "4"]))'''
SRC['quick_13'] = '''def inner():
    print("A")
    int("x")
    print("B")

def outer():
    inner()
    print("C")

try:
    outer()
except ValueError:
    print("D")
print("E")'''
SRC['slide_19'] = '''def parse_mark(text):
    try:
        mark = int(text)
    except ValueError:
        mark = 0
    return mark

print(parse_mark("80") + parse_mark("9O"))'''
SRC['quick_14'] = '''def to_number(text):
    try:
        return int(text)
    except ValueError:
        return 0

print(to_number("5") + to_number("x") + to_number("7"))'''
SRC['slide_20'] = '''def parse_mark(text):
    mark = int(text)
    if mark < 0 or mark > 100:
        raise ValueError("mark must be 0 to 100")
    return mark

def total_marks(texts):
    total = 0
    for text in texts:
        total = total + parse_mark(text)
    return total

print(total_marks(["70", "150", "60"]))'''
SRC['slide_22_1'] = '''def withdraw(balance, amount):
    if amount > balance:
        raise ValueError("amount is too large")
    return balance - amount'''
SRC['slide_22_2'] = '''try:
    balance = withdraw(balance, amount)
except ValueError as err:
    print("Cannot withdraw:", err)'''
SRC['slide_23'] = '''try:
    # code that might fail
except ValueError as err:
    # a ValueError was raised
else:
    # no exception was raised
finally:
    # always executed, last
# execution continues here'''
SRC['practice_1_solution'] = '''def percent(part, whole):
    """Return a percentage.

    Raise ValueError("whole must be positive") if whole <= 0.
    Raise ValueError("part must be from 0 to whole") if
    part is outside 0 to whole.
    """
    if whole <= 0:
        raise ValueError("whole must be positive")
    if part < 0 or part > whole:
        raise ValueError("part must be from 0 to whole")
    return part / whole * 100

try:
    part = int(input())
    whole = int(input())
except ValueError as err:
    print("Error:", err)
else:
    try:
        result = percent(part, whole)
    except ValueError as err:
        print("Error:", err)
    else:
        print(f"Percent: {result:.1f}")'''
SRC['practice_2_prompt'] = '''def inspect(values):
    for value in values:
        if value < 0: raise ValueError("negative")
        print(value)

try:
    inspect([2, -3])
except ValueError: print("Bad")
else: print("Good")
finally: print("Checked")
print("End")'''
SRC['practice_3_solution'] = '''def show_ratio(a_text, b_text):
    try:
        a = float(a_text)
        b = float(b_text)
        print(f"{a / b:.2f}")
    except ValueError:
        print("Enter numbers.")
    finally:
        print("Ratio checked.")

show_ratio("3", "4")
show_ratio("3", "x")
try:
    show_ratio("3", "0")
except ZeroDivisionError:
    print("Cannot divide by zero.")'''
SRC['practice_4_prompt'] = '''def check_value():
    try:
        raise ValueError("bad value")
    finally:
        print(1 / 0)

try:
    check_value()
except ValueError:
    print("Value error")
except ZeroDivisionError:
    print("Division error")'''
SRC['boss_1_starter'] = '''def average(values):
    if len(values) == 0:
        print("No values.")
        return -1
    return sum(values) / len(values)'''
SRC['boss_1_solution'] = '''def average(values):
    """Return the average. Raise ValueError for no values."""
    if len(values) == 0:
        raise ValueError("no values")
    return sum(values) / len(values)

values = []
text = input()
while text != "":
    try:
        values.append(float(text))
    except ValueError:
        print("Enter a number.")
    text = input()
try:
    result = average(values)
except ValueError as err:
    print("No average:", err)
else:
    print(f"Average: {result:.2f}")'''
SRC['boss_2_starter'] = '''def gcd(a, b):
    """Return the greatest common divisor of non-negative a and b."""
    pass'''
SRC['boss_2_solution'] = '''def gcd(a, b):
    while b != 0:
        remainder = a % b
        a = b
        b = remainder
    return a

def reduce_fraction(top, bottom):
    if bottom == 0:
        raise ValueError("denominator must not be zero")
    if bottom < 0:
        top = -top
        bottom = -bottom
    divisor = gcd(abs(top), bottom)
    return str(top // divisor) + "/" + str(bottom // divisor)

try:
    top = int(input())
    bottom = int(input())
except ValueError:
    print("Enter whole numbers.")
else:
    try:
        print(reduce_fraction(top, bottom))
    except ValueError as err:
        print("Error:", err)'''
SRC['boss_3_starter'] = '''def proper_divisors(n):
    """Return the proper divisors of n."""
    pass'''
SRC['boss_3_solution'] = '''def proper_divisors(n):
    if n < 1:
        raise ValueError("n must be at least 1")
    divisors = []
    for candidate in range(1, n):
        if n % candidate == 0:
            divisors.append(candidate)
    return divisors

def is_perfect(n):
    return sum(proper_divisors(n)) == n

if __name__ == "__main__":
    text = input()
    while text != "":
        try:
            n = int(text)
        except ValueError:
            print(f"{text}: not a whole number")
        else:
            try:
                perfect = is_perfect(n)
            except ValueError as err:
                print(f"{text}: {err}")
            else:
                if perfect:
                    print(f"{n} is perfect")
                else:
                    print(f"{n} is not perfect")
        text = input()'''
SRC['boss_4_starter'] = '''ITEMS = ["pen", "book", "cup"]
PRICES = [1.50, 12.00, 4.25]'''
SRC['boss_4_solution'] = '''ITEMS = ["pen", "book", "cup"]
PRICES = [1.50, 12.00, 4.25]

def parse_quantity(text):
    quantity = int(text)
    if quantity < 1:
        raise ValueError("quantity must be at least 1")
    return quantity

def line_cost(line):
    parts = line.split(",")
    if len(parts) != 2:
        raise ValueError("expected item,quantity")
    item = parts[0].strip()
    quantity_text = parts[1].strip()
    if item not in ITEMS:
        raise ValueError("unknown item " + item)
    quantity = parse_quantity(quantity_text)
    return PRICES[ITEMS.index(item)] * quantity

total = 0
line = input()
while line != "":
    try:
        cost = line_cost(line)
    except ValueError as err:
        print("Rejected:", err)
    else:
        total = total + cost
        print(f"Added {cost:.2f}")
    finally:
        print("Checked:", line)
    line = input()
print(f"Total: {total:.2f}")'''

E = {}
WD = SRC["slide_4_1"]

def ex(name, code, output=False):
    E[name] = example(code, output)
    return E[name]

def out(*values, width="10rem"):
    """Blanks l1, l2, ... for lines of output. A name ending in Error is an exception blank."""
    return table(**{f"l{i}": (exc(v) if v.endswith("Error") else accept(v, width=width, placeholder="output"))
                    for i, v in enumerate(values, 1)})

# ============================================================ 1. A withdraw function with no checks
ex("ex-withdraw", SRC["slide_2"] + "\n\nprint(withdraw(500, 100))\n")
assert run(SRC["slide_2"] + "\nprint(withdraw(500, 100))\nprint(withdraw(500, 900))\nprint(withdraw(500, -50))") == "400\n-400\n550"
assert run_error(SRC["slide_2"] + '\nwithdraw(500, "100")')[1] == "TypeError"
E["s1-calls"] = table(r1=accept("400", width="8rem", placeholder="result"), r2=accept("-400", width="8rem", placeholder="result"),
                      r3=accept("550", width="8rem", placeholder="result"), r4=exc("TypeError"))
E["s1-why"] = short("The calls with 900, -50 and \"100\" break the rule. The calls with 900 and -50 return a wrong balance. "
                    "The function should refuse them by raising an exception.")
E["q1"] = true_false(True, False)

# ============================================================ 2. Two sides of a function call
NAMES = ("err", "e", "error", "exc", "ex")
q2 = SRC["quick_2"]
for name in NAMES:
    assert run(q2.replace("____(a)____", "raise").replace("____(b)____", name).replace("____(c)____", name)) == "Too big: n must be at most 10"
E["q2"] = table(a=accept("raise", width="8rem", placeholder="keyword", show="raise"),
                b=accept(*NAMES, width="8rem", placeholder="name", show="err"),
                c=accept(*NAMES, width="8rem", placeholder="name", show="err"))

# ============================================================ 3. The raise statement
ex("ex-raise", WD + "\n\n" + SRC["slide_4_2"])
assert run_error(WD + "\n" + SRC["slide_4_2"]) == ("400", "ValueError")
assert run_error(SRC["quick_3"]) == ("Halving 8\n4", "ValueError")
E["q3"] = out("Halving 8", "4", "ValueError")

# ============================================================ 4. Raising an exception or printing an error
assert ex("ex-print-error", SRC["slide_5_1"], output=True)["output"] == "Insufficient funds.\nTake your cash."
ex("ex-raise-error", SRC["slide_5_2"] + "\n\nprint(withdraw(500, 100))\nprint(withdraw(500, 900))\n")
E["q4"] = choice("B")

# ============================================================ 5. Choosing an exception type
q5 = SRC["quick_5"].replace("____(a)____", "TypeError").replace("____(b)____", "IndexError")
assert run_error(q5 + '\nget_item(["a"], "1")')[1] == "TypeError"
assert run_error(q5 + '\nget_item(["a"], 2)')[1] == "IndexError"
assert run(q5 + '\nprint(get_item(["a", "b"], 2))') == "b"
E["q5"] = table(a=exc("TypeError"), b=exc("IndexError"))

# ============================================================ 6. Handling an exception that a function raises
caller = WD + "\n\n" + SRC["slide_7"]
ex("ex-caller", caller)
assert run_with_prompts(caller, ["100"]) == "Withdraw amount: Balance: 400"
assert run_with_prompts(caller, ["900"]) == "Withdraw amount: Cannot withdraw: amount is too large\nBalance: 500"
assert run(SRC["quick_6"]) == "40\nError: n is negative"
E["q6"] = out("40", "Error: n is negative", width="14rem")

# ============================================================ 7. A bad value or a bug
E["q7"] = true_false(False, True)
# Checkpoint 1
abc = lambda letter: accept(letter, letter.lower(), width="3.5rem", placeholder="", show=letter)
E["cp1"] = table(i1=abc("A"), i2=abc("B"), i3=abc("C"), i4=abc("C"))

# ============================================================ 8. The else clause
ex("ex-else", SRC["slide_11"])
assert run_with_prompts(SRC["slide_11"], ["21"]) == "Number: Twice that is 42"
assert run_with_prompts(SRC["slide_11"], ["abc"]) == "Number: Enter a whole number."
assert run(SRC["quick_8"], ["7"]) == "8\nDone" and run(SRC["quick_8"], ["x"]) == "Bad\nDone"
E["q8"] = out("8", "Done", "Bad", "Done")

# ============================================================ 9. Why use else
in_try = WD + "\n\n" + SRC["slide_12_1"]
in_else = WD + "\n\n" + SRC["slide_12_2"]
ex("ex-success-try", in_try)
ex("ex-success-else", in_else)
assert run_with_prompts(in_try, ["900"]) == "Amount: Enter a whole number."
assert run_error(in_else, ["900"])[1] == "ValueError"
assert run_with_prompts(in_else, ["100"]) == "Amount: 400"
E["q9"] = choice("C")

# ============================================================ 10. The finally clause
ex("ex-finally", SRC["slide_13"])
assert run_with_prompts(SRC["slide_13"], ["4"]) == "People: Share: 15.0\nFinished.\nAfter the try statement."
assert run_with_prompts(SRC["slide_13"], ["four"]) == "People: Enter a whole number.\nFinished.\nAfter the try statement."
assert run_error(SRC["slide_13"], ["0"]) == ("People: Finished.", "ZeroDivisionError")
assert run_error(SRC["quick_10"]) == ("Checked 3\n3\nChecked a", "ValueError")
E["q10"] = out("Checked 3", "3", "Checked a", "ValueError")

# ============================================================ 11. Flow of control in a full try statement
E["q11"] = true_false(False, True)
# Checkpoint 2
cp2 = SRC["slide_15"] + '\n\ndivide("8", "2")\ndivide("8", "x")\ndivide("8", "0")\n'
assert run_error(cp2) == ("B 4.0\nC\nD\nA\nC\nD\nC", "ZeroDivisionError")
NONE = accept("none", "None", "no line", width="10rem", placeholder="output", show="none")
o = lambda v: accept(v, width="10rem", placeholder="output")
E["cp2"] = table(a1=o("B 4.0"), a2=o("C"), a3=o("D"), b1=o("A"), b2=o("C"), b3=o("D"),
                 c1=o("C"), c2=exc("ZeroDivisionError"), c3=NONE)
ex("ex-cp2", cp2)

# ============================================================ 12. Reading a traceback
ex("ex-grades", SRC["slide_17"])
assert run_error(SRC["slide_17"]) == ("Average: 81.7", "ZeroDivisionError")
assert run_error(SRC["quick_12"]) == ("3", "TypeError")
E["q12"] = table(a=exc("TypeError"), b=accept("total", "total()", width="8rem", placeholder="function", show="total"),
                 c=accept("8", width="5rem", placeholder="line"))

# ============================================================ 13. An unhandled exception passes to the caller
assert run(SRC["quick_13"]) == "A\nD\nE"
E["q13"] = out("A", "D", "E")

# ============================================================ 14. Handling an exception too early
assert ex("ex-too-early", SRC["slide_19"], output=True)["output"] == "80"
assert run(SRC["quick_14"]) == "12"
E["q14"] = choice("D")

# Checkpoint 3
assert run_error(SRC["slide_20"]) == ("", "ValueError")
E["cp3"] = table(t=exc("ValueError"),
                 m=accept("mark must be 0 to 100", width="14rem", placeholder="message", show="mark must be 0 to 100"),
                 n=accept("4", width="5rem", placeholder="line"),
                 f=accept("parse_mark", "parse_mark()", width="10rem", placeholder="function", show="parse_mark"),
                 v=accept('"150"', "150", "'150'", width="8rem", placeholder="value", show='"150"'))
E["cp3-frames"] = short("parse_mark (line 4) is the bottom frame. Above it is total_marks (line 10), and the top level (line 13) is at the top.")
ex("ex-cp3", SRC["slide_20"])

# ============================================================ Coding Practice
# 1. A percentage (R7.5)
p1 = SRC["practice_1_solution"]
p1_cases = input_cases(p1,
    ("Inputs 3 and 4", ["3", "4"]),
    ("Inputs 5 and 0", ["5", "0"]),
    ("Inputs 7 and 4", ["7", "4"]),
    ("Input abc", ["abc", "4"]),
    ("Inputs -1 and 4", ["-1", "4"]),
    ("Inputs 4 and 4", ["4", "4"]),
    ("Inputs 1 and 3", ["1", "3"]))
assert [c["expected"] for c in p1_cases] == ["Percent: 75.0", "Error: whole must be positive", "Error: part must be from 0 to whole",
    "Error: invalid literal for int() with base 10: 'abc'", "Error: part must be from 0 to whole", "Percent: 100.0", "Percent: 33.3"]
E["p1"] = {"type": "code", "xp": 5, "minLines": 16,
    "starter": "def percent(part, whole):\n    pass\n",
    "cases": p1_cases,
    "check": EXC + needs("ValueError") + '''_f = _fn("percent", "part", "whole")
assert len(_raises(_def("percent"))) >= 2, "Raise ValueError in percent for each rule. Use a raise statement for each one."
assert not any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "print" for n in ast.walk(_def("percent"))), "percent must not print. The caller prints the error."
assert any(t.orelse for t in _tries()), "Print the percentage in an else block."
for _args, _want in [((1, 0), "ValueError: whole must be positive"), ((5, 4), "ValueError: part must be from 0 to whole"), ((-1, 4), "ValueError: part must be from 0 to whole")]:
    assert _quiet(_f, *_args)[1] == _want, "percent" + str(_args) + " should raise " + _want
assert _quiet(_f, 1, 4)[0] == 25.0, "percent(1, 4) should return 25.0."
''',
    "answer": b64(p1),
    "answerNote": "percent only raises. The caller converts the input, calls percent in a small try block, and prints the result in else."}
E["p1-why"] = short("The two raise statements in percent raise the exceptions. The except block in the caller handles them. "
                    "The function does not print because the caller decides what the user sees.")

# 2. The statement after raise (R7.6)
p2 = SRC["practice_2_prompt"]
assert run(p2) == "2\nBad\nChecked\nEnd"
assert run(p2.replace("inspect([2, -3])", "inspect([2, 3])")) == "2\n3\nGood\nChecked\nEnd"
ex("ex-p2", p2)
E["p2-out"] = table(a1=o("2"), a2=o("Bad"), a3=o("Checked"), a4=o("End"),
                    b1=o("2"), b2=o("3"), b3=o("Good"), b4=o("Checked"), b5=o("End"))
E["p2-next"] = short("After raise, control jumps to the first statement of the matching except block, here print(\"Bad\"). "
                     "The rest of inspect is skipped. The finally block runs after that.")

# 3. A ratio (R7.16)
p3 = SRC["practice_3_solution"]
assert run(p3) == "0.75\nRatio checked.\nEnter numbers.\nRatio checked.\nRatio checked.\nCannot divide by zero."
p3_main = p3.split("\ntry:\n")[0]
p3_starter = 'def show_ratio(a_text, b_text):\n    pass\n\n\nshow_ratio("3", "4")\nshow_ratio("3", "x")\n'
E["p3"] = {"type": "code", "xp": 5, "minLines": 11,
    "starter": p3_starter,
    "cases": [{"name": 'Calls with "3", "4" and "3", "x"', "expected": run(p3_main)}],
    "check": EXC + needs("ValueError") + '''_f = _fn("show_ratio", "a_text", "b_text")
_d = _def("show_ratio")
_t = [n for n in ast.walk(_d) if isinstance(n, ast.Try)]
assert any(t.finalbody for t in _t), "Print Ratio checked. in a finally block inside show_ratio."
assert all(_names(h) == ["ValueError"] for t in _t for h in t.handlers), "Inside show_ratio, handle only ValueError."
_r, _e, _o = _quiet(_f, "3", "0")
assert _e is not None and _e.startswith("ZeroDivisionError"), 'show_ratio("3", "0") should let the ZeroDivisionError pass to the caller.'
assert "Ratio checked." in _o, 'The finally block should print Ratio checked. for "3" and "0" as well.'
''',
    "answer": b64(p3_main),
    "answerNote": "The finally block prints on every path. For \"3\" and \"0\" it runs first, and then the ZeroDivisionError passes to the caller."}
E["p3-why"] = short("For \"3\" and \"0\", the finally block prints Ratio checked. and then the ZeroDivisionError passes to the caller. "
                    "Real programs use finally to release something, such as closing a file.")

# 4. An exception inside finally (R7.18)
assert ex("ex-p4", SRC["practice_4_prompt"], output=True)["output"] == "Division error"
E["p4-out"] = table(out=accept("Division error", width="12rem", placeholder="output"))
E["p4-why"] = short("The ZeroDivisionError raised in the finally block replaces the ValueError, so the ZeroDivisionError block runs. "
                    "A finally block should contain only code that cannot fail.")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-30",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 30 Workbook",
    "subtitle": "raise, else, finally, and tracebacks",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-30/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
