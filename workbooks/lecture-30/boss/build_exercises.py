"""Build workbooks/lecture-30/boss/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_30_SHARED_CONTENT.tex; the listings below are copied from it and
model answers follow its \\solution{...} text. Run from anywhere:

    python3 workbooks/lecture-30/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-30/boss
"""
import base64, contextlib, io, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]

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

# ---------------------------------------------------------------- 1 Average or nothing (original, approved 2026-11-23)
avg = SRC["boss_1_solution"]
avg_cases = input_cases(avg,
    ("Example 1: 4, 8", ["4", "8", ""]),
    ("Example 2: -1", ["-1", ""]),
    ("Example 3: blank line only", [""]),
    ("Three decimals", ["2.5", "3.5", "10", ""]),
    ("A single zero", ["0", ""]),
    ("Spaces around a number", [" 7 ", "9", ""]))
assert [c["expected"] for c in avg_cases] == ["Average: 6.00", "Average: -1.00", "No average: no values", "Average: 5.33", "Average: 0.00", "Average: 8.00"]
E["average-or-nothing"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 14,
    "starter": SRC["boss_1_starter"],
    "cases": avg_cases,
    "check": EXC + needs("ValueError") + '''_f = _fn("average", "values")
_d = _def("average")
assert _raises(_d), "average should raise ValueError for an empty list."
assert not any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "print" for n in ast.walk(_d)), "average must not print. The caller prints the message."
assert _quiet(_f, [])[1] == "ValueError: no values", 'average([]) should raise ValueError("no values").'
assert _quiet(_f, [2.0, 4.0])[0] == 3.0, "average([2.0, 4.0]) should return 3.0."
assert any(t.orelse for t in _tries()), "Print the average in an else block."
assert _loops(), "Read the lines with a while loop that stops at a blank line."
''',
    "hints": [
        "Replace the `print` and `return -1` in `average` with `raise ValueError(\"no values\")`. Add that to the docstring.",
        "Read lines into a list until the line is `\"\"`. Convert each line with `float` and append it.",
        "Call `average` alone in a `try` block. `except ValueError as err:` prints `No average:` and `err`. The `else` block prints `f\"Average: {result:.2f}\"`.",
    ],
    "answer": b64(avg),
    "answerNote": "average only raises. The caller handles the ValueError and prints the result in else, so -1 is a real average and not a signal."}

# ---------------------------------------------------------------- 2 Reduce a fraction (Stephenson 101)
frac = SRC["boss_2_solution"]
frac_cases = input_cases(frac,
    ("Example 1: 18, -24", ["18", "-24"]),
    ("Example 2: 0, 9", ["0", "9"]),
    ("Example 3: 4, 0", ["4", "0"]),
    ("12 and 18", ["12", "18"]),
    ("Both negative", ["-6", "-4"]),
    ("Negative top", ["-5", "10"]),
    ("Already reduced", ["7", "1"]),
    ("Text on the first line", ["abc", "4"]),
    ("Decimal on the second line", ["7", "2.5"]),
    ("Zero over a negative", ["0", "-3"]))
assert [c["expected"] for c in frac_cases] == ["-3/4", "0/1", "Error: denominator must not be zero", "2/3", "3/2", "-1/2", "7/1",
    "Enter whole numbers.", "Enter whole numbers.", "0/1"]
E["reduce-fraction"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 22,
    "starter": SRC["boss_2_starter"],
    "cases": frac_cases,
    "check": EXC + needs("ValueError") + '''_g = _fn("gcd", "a", "b")
_r = _fn("reduce_fraction", "top", "bottom")
assert any(isinstance(n, ast.While) for n in ast.walk(_def("gcd"))), "Use a while loop in gcd (Euclid's algorithm)."
assert _quiet(_g, 12, 18)[0] == 6 and _quiet(_g, 5, 0)[0] == 5, "gcd(12, 18) should return 6, and gcd(5, 0) should return 5."
assert _quiet(_r, 4, 0)[1] == "ValueError: denominator must not be zero", 'reduce_fraction(4, 0) should raise ValueError("denominator must not be zero").'
assert _quiet(_r, 18, -24)[0] == "-3/4", 'reduce_fraction(18, -24) should return the string "-3/4".'
assert len(_tries()) >= 2, "Use separate try blocks for the conversion and for the call to reduce_fraction."
''',
    "hints": [
        "Euclid's algorithm: while `b` is not 0, replace `a, b` with `b` and `a % b`. Then `a` is the greatest common divisor.",
        "In `reduce_fraction`, raise for a zero bottom first. If the bottom is negative, change the sign of both numbers. Divide both by `gcd(abs(top), bottom)`.",
        "Convert both lines in one `try` block. In its `else` block, call `reduce_fraction` in a second `try` that prints `Error:` and `err`.",
    ],
    "answer": b64(frac),
    "answerNote": "Both errors are ValueError, but they come from different places. Separate try blocks give each one its own message."}

# ---------------------------------------------------------------- 3 Proper divisors and perfect numbers (Stephenson 109, 110)
perf = SRC["boss_3_solution"]
perf_cases = input_cases(perf,
    ("Example 1: 6, 8", ["6", "8", ""]),
    ("Example 2: 0, abc", ["0", "abc", ""]),
    ("28, 1, 12", ["28", "1", "12", ""]),
    ("A negative number and 496", ["-4", "496", ""]),
    ("A decimal and spaces", ["2.5", " 6 ", ""]))
assert perf_cases[0]["expected"] == "6 is perfect\n8 is not perfect"
assert perf_cases[1]["expected"] == "0: n must be at least 1\nabc: not a whole number"
assert perf_cases[2]["expected"] == "28 is perfect\n1 is not perfect\n12 is not perfect"
E["perfect-numbers"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 26,
    "starter": SRC["boss_3_starter"],
    "cases": perf_cases,
    "check": EXC + needs("ValueError") + '''_p = _fn("proper_divisors", "n")
_i = _fn("is_perfect", "n")
assert _quiet(_p, 12)[0] == [1, 2, 3, 4, 6], "proper_divisors(12) should return [1, 2, 3, 4, 6]."
assert _quiet(_p, 1)[0] == [], "proper_divisors(1) should return []."
assert _quiet(_p, 0)[1] == "ValueError: n must be at least 1", 'proper_divisors(0) should raise ValueError("n must be at least 1").'
assert not any(isinstance(n, ast.Try) for n in ast.walk(_def("is_perfect"))), "is_perfect should let the exception pass to its caller. Do not use try in it."
assert (_quiet(_i, 6)[0], _quiet(_i, 8)[0]) == (True, False), "is_perfect(6) should return True, and is_perfect(8) should return False."
assert any(isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and getattr(n.test.left, "id", "") == "__name__" for n in _TREE.body), 'Put the main program under if __name__ == "__main__":'
assert len(_tries()) >= 2, "Use separate try blocks for the conversion and for the call."
''',
    "hints": [
        "In `proper_divisors`, raise first when `n < 1`. Then test each candidate from 1 to `n - 1` with `n % candidate == 0`.",
        "`is_perfect` is one line: compare `sum(proper_divisors(n))` with `n`. It has no `try`, so a `ValueError` passes to its caller.",
        "In the loop, convert the line in one `try`. In its `else` block, call `is_perfect` in a second `try` and print `f\"{text}: {err}\"` for a `ValueError`.",
    ],
    "answer": b64(perf),
    "answerNote": "proper_divisors raises, is_perfect lets the exception pass, and the main program handles it. Each function does one job."}

# ---------------------------------------------------------------- 4 Order lines (original, approved 2026-11-23)
orders = SRC["boss_4_solution"]
order_cases = input_cases(orders,
    ("Example 1: pen,2 and cup, 1", ["pen,2", "cup, 1", ""]),
    ("Example 2: pen,0", ["pen,0", ""]),
    ("A quantity in words", ["book,3", "pen,two", ""]),
    ("Unknown item and wrong parts", ["hat,1", "pen", "pen,1,2", ""]),
    ("Spaces and a negative quantity", [" cup , 2 ", "book,-1", ""]),
    ("Blank line only", [""]))
assert order_cases[0]["expected"] == "Added 3.00\nChecked: pen,2\nAdded 4.25\nChecked: cup, 1\nTotal: 7.25"
assert order_cases[1]["expected"] == "Rejected: quantity must be at least 1\nChecked: pen,0\nTotal: 0.00"
assert order_cases[2]["expected"] == "Added 36.00\nChecked: book,3\nRejected: invalid literal for int() with base 10: 'two'\nChecked: pen,two\nTotal: 36.00"
E["order-lines"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 26,
    "starter": SRC["boss_4_starter"],
    "cases": order_cases,
    "check": EXC + needs("ValueError") + '''_q = _fn("parse_quantity", "text")
_c = _fn("line_cost", "line")
assert _quiet(_q, "0")[1] == "ValueError: quantity must be at least 1", 'parse_quantity("0") should raise ValueError("quantity must be at least 1").'
assert (_quiet(_q, "two")[1] or "").startswith("ValueError: invalid literal"), 'parse_quantity("two") should let the ValueError from int pass to the caller.'
assert _quiet(_c, "pen")[1] == "ValueError: expected item,quantity", 'line_cost("pen") should raise ValueError("expected item,quantity").'
assert _quiet(_c, "hat,1")[1] == "ValueError: unknown item hat", 'line_cost("hat,1") should raise ValueError("unknown item hat").'
assert _quiet(_c, " pen , 2 ")[0] == 3.0, 'line_cost(" pen , 2 ") should return 3.0.'
for _name in ("parse_quantity", "line_cost"):
    assert not any(isinstance(n, ast.Try) for n in ast.walk(_def(_name))), _name + " should raise and let exceptions pass. Handle them in the main program."
assert any(t.orelse and t.finalbody for t in _tries()), "In the main program, use try, except, else, and finally."
assert _loops(), "Read the lines with a while loop that stops at a blank line."
''',
    "hints": [
        "`parse_quantity` converts with `int` and raises for a value below 1. `line_cost` splits on `\",\"`, checks for two parts, strips each part, and checks `item in ITEMS`.",
        "The price is at the same position as the item: `PRICES[ITEMS.index(item)]`. Neither function uses `try`.",
        "In the loop, call `line_cost` alone in `try`. `except` prints `Rejected:`, `else` adds and prints `Added`, and `finally` prints `Checked:` and the line.",
    ],
    "answer": b64(orders),
    "answerNote": "The functions only raise. The main program is the one place that knows how to report a rejected line and continue, so the handler is there."}
E["orders-trace"] = short("parse_quantity raised the ValueError at the bottom of the traceback. line_cost called parse_quantity, and the top-level call line_cost(\"pen,0\") started the chain. "
                          "The handler belongs in the main program because only it knows how to report a rejected line and go on to the next one.",
                          min_chars=40, rows=5, placeholder="Label each frame, then explain where the handler belongs…")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-30-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 30 Boss Problems",
    "short": "L30 bosses",
    "subtitle": "raise, else, finally, and tracebacks",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-30/boss/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
for key, spec in E.items():
    for c in spec.get("cases", []):
        print(key, "|", c["name"], "|", c["expected"].replace("\n", " / "))
