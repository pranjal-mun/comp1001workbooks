"""Build workbooks/lecture-29/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_29_SHARED_CONTENT.tex; the listings below are copied from it and
model answers follow its \\solution{...} text. Run from anywhere:

    python3 workbooks/lecture-29/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-29
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
# `_tries()` lists try statements. Every exercise rejects a bare except,
# except Exception, and else or finally on a try (Lecture 30).
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
assert all(h.type is not None for h in _H), "Do not use a bare except. Name the exception types that you expect."
assert not any(n in ("Exception", "BaseException") for h in _H for n in _names(h)), "Name the specific exception types. Do not use except Exception."
assert not any(t.orelse or t.finalbody for t in _tries()), "Use only try and except here. Lecture 30 covers else and finally."
'''

def needs(*names):
    return "".join(f'assert _handles({n!r}), "Add an except block that names {n}."\n' for n in names)
# Listings from the kit, in workbook order.
SRC = {}
SRC['slide_2'] = '''total = int(input("Total points: "))
count = int(input("Number of scores: "))
print(f"Average: {total / count:.1f}")'''
SRC['quick_1'] = '''print("Start")
number = int("3")
print(number + 1)
print([1, 2][2])
print("End")'''
SRC['quick_2'] = '''total = 10
count = 6
average = total + count / 2'''
SRC['slide_8_1'] = '''try:
    age = int(input("Age: "))
    print(f"Next year you will be {age + 1}")
except ValueError:
    print("Enter the age as a whole number.")
print("Done")'''
SRC['quick_5'] = '''try:
    print("First")
    number = int(input())
    print(number)
except ValueError:
    print("Bad")
print("Last")'''
SRC['slide_10_1'] = '''text = input("Points: ")
try:
    points = int(text)
    print("Conversion worked.")
except ValueError:
    print("Conversion failed.")
print("Program continues.")'''
SRC['quick_6'] = '''values = [5, 10]
try:
    i = int(input())
    print(values[i])
except ____(a)____:
    print("No such position.")'''
SRC['slide_11_1'] = '''try:
    number = int(input("Number: "))
    print(100 / number)
except ValueError:
    print("Enter a whole number.")'''
SRC['quick_7'] = '''try:
    print("abc"[3])
except ValueError:
    print("Wrong value")
print("Done")'''
SRC['slide_12_1'] = '''values = [4, 0, 5]
try:
    i = int(input("Position: "))
    print(100 / values[i])
except ValueError:
    print("Not a whole number.")
except IndexError:
    print("No such position.")
except ZeroDivisionError:
    print("The value is 0.")'''
SRC['quick_8'] = '''try:
    [1, 2][5]
except (ValueError, IndexError):
    print("First")
except IndexError:
    print("Second")'''
SRC['slide_14_1'] = '''values = [4, 0, 5]
try:
    i = int(input("Position: "))
    print(100 / values[i])
except (ValueError, IndexError):
    print("Enter a position from 0 to 2.")
except ZeroDivisionError:
    print("The value at that position is 0.")'''
SRC['slide_15_1'] = '''text = "twelve"
try:
    number = int(text)
except ValueError as err:
    print("Conversion failed.")
    print(err)'''
SRC['quick_10'] = '''try:
    int("")
except ValueError as err:
    print(err)'''
SRC['slide_16_1'] = '''values = [8, 0, 2]
try:
    i = int(input("Position: "))
    print(10 // values[i])
except (ValueError, IndexError):
    print("Bad position")
except ZeroDivisionError:
    print("Zero value")'''
SRC['slide_18_1'] = '''scores = []
try:
    count = int(input("Count: "))
    per_count = 100 / count
    per_score = 100 / len(scores)
except ZeroDivisionError:
    print("Count must not be zero.")'''
SRC['slide_18_2'] = '''scores = []
try:
    count = int(input("Count: "))
    per_count = 100 / count
except ZeroDivisionError:
    print("Count must not be zero.")
per_score = 100 / len(scores)'''
SRC['quick_11'] = '''text = input()             # 1
print("Price")             # 2
quantity = int(text)       # 3
price = quantity * 5       # 4
print(price)               # 5
print("Done")              # 6'''
SRC['slide_19_1'] = '''try:
    quantity = int(input("Quantity: "))
    print(quantity * prise)
except:
    print("Enter a whole number.")'''
SRC['slide_21_1'] = '''text = input("Quantity: ")
if text.isdigit():
    quantity = int(text)
else:
    print("Enter a whole number.")'''
SRC['slide_21_2'] = '''text = input("Quantity: ")
try:
    quantity = int(text)
except ValueError:
    print("Enter a whole number.")'''
SRC['quick_13'] = '''text = "-3"
print(text.isdigit())
print(int(text))'''
SRC['slide_22_1'] = '''try:
    total = float(input("Total cost: "))
    items = int(input("Items: "))
    print(f"Cost per item: {total / items:.2f}")
except:
    print("Error")'''
SRC['slide_23_1'] = '''try:
    total = float(input("Total cost: "))
    items = int(input("Items: "))
    print(f"Cost per item: {total / items:.2f}")
except ValueError:
    print("Enter numbers only.")
except ZeroDivisionError:
    print("Items must not be zero.")'''
SRC['slide_24_1'] = '''try:
    # statements that might fail
except ValueError:
    # runs for a ValueError
except (IndexError, TypeError) as err:
    # runs for either type
    # print(err) shows the message
# execution continues here'''
SRC['practice_1_prompt'] = '''try:
    number = int(input())
    print(60 / number)
except ValueError:
    print("Enter a whole number.")'''
SRC['practice_1_solution'] = '''try:
    number = int(input())
    print(60 / number)
except ValueError:
    print("Enter a whole number.")
except ZeroDivisionError:
    print("The number must not be zero.")'''
SRC['practice_2_solution'] = '''def describe(text):
    try:
        number = int(text)
        print(number)
    except ValueError as err:
        print("Enter a whole number.")
        print(err)

describe("12")
describe("twelve")
describe("")
describe("4.0")'''
SRC['practice_3_solution'] = '''altitude_text = input()
unit = input()
valid = True
try:
    altitude = float(altitude_text)
except ValueError:
    print("Enter a number.")
    valid = False
if valid:
    if unit == "m":
        print(f"{100 - altitude / 300:.1f}")
    elif unit == "ft":
        print(f"{100 - altitude / 1000:.1f}")
    else:
        print("Unknown unit.")'''
SRC['practice_4_solution'] = '''text = input()
valid = True
try:
    price = float(text)
except ValueError:
    print("Enter a number.")
    text = input()
    try:
        price = float(text)
    except ValueError:
        print("No valid price.")
        valid = False
if valid:
    print(f"{price * 1.13:.2f}")'''
SRC['boss_1_starter'] = '''items = ["pen", "book", "cup", "bag", "ruler"]'''
SRC['boss_1_solution'] = '''items = ["pen", "book", "cup", "bag", "ruler"]
try:
    position = int(input())
    if position < 1:
        print("Out of range.")
    else:
        print(items[position - 1])
except ValueError:
    print("Enter a whole number.")
except IndexError:
    print("Out of range.")'''
SRC['boss_2_starter'] = '''total = 0.0
skipped = 0'''
SRC['boss_2_solution'] = '''total = 0.0
skipped = 0
text = input()
while text != "":
    try:
        value = float(text)
        total = total + value
        print(f"Total: {total}")
    except ValueError:
        print(f"Invalid: {text}")
        skipped = skipped + 1
    text = input()
print(f"Final: {total}")
print(f"Skipped: {skipped}")'''
SRC['boss_3_starter'] = '''def trip_speed(distance_text, time_text):
    pass'''
SRC['boss_3_solution'] = '''def trip_speed(distance_text, time_text):
    valid = True
    try:
        distance = float(distance_text)
        time = float(time_text)
        speed = distance / time
    except (ValueError, ZeroDivisionError) as err:
        print("Bad trip.")
        print(err)
        valid = False
    if valid:
        print(f"Speed: {speed:.1f}")

first_distance = input()
first_time = input()
valid = True
try:
    distance = float(first_distance)
    time = float(first_time)
    speed = distance / time
except ValueError:
    print("Bad number.")
    valid = False
except ZeroDivisionError:
    print("Zero time.")
    valid = False
if valid:
    print(f"Speed: {speed:.1f}")
second_distance = input()
second_time = input()
trip_speed(second_distance, second_time)'''
SRC['boss_4_starter'] = '''letters = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"]
points = [4.0, 4.0, 3.7, 3.3, 3.0, 2.7, 2.3, 2.0, 1.7, 1.3, 1.0, 0.0]'''
SRC['boss_4_solution'] = '''letters = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"]
points = [4.0, 4.0, 3.7, 3.3, 3.0, 2.7, 2.3, 2.0, 1.7, 1.3, 1.0, 0.0]
text = input()
while text != "":
    try:
        value = float(text)
        if 0.0 <= value <= 4.0:
            best = 0
            for i in range(1, len(points)):
                if points[i] != points[best] and value < (points[best] + points[i]) / 2:
                    best = i
            print(letters[best])
        else:
            print("Invalid grade.")
    except ValueError:
        try:
            position = letters.index(text)
            print(points[position])
        except ValueError:
            print("Invalid grade.")
    text = input()'''

E = {}

def ex(name, key, output=False):
    E[name] = example(SRC[key], output)
    return E[name]

# ============================================================ 1. Runtime errors
ex("ex-average", "slide_2")
assert run_with_prompts(SRC["slide_2"], ["250", "5"]) == "Total points: Number of scores: Average: 50.0"
assert run_error(SRC["slide_2"], ["two", "5"])[1] == "ValueError"
assert run_error(SRC["slide_2"], ["250", "0"])[1] == "ZeroDivisionError"
E["q1"] = table(l1=accept("Start", width="8rem", placeholder="output"), l2=accept("4", width="8rem", placeholder="output"),
                l3=exc("IndexError"))
assert run_error(SRC["quick_1"]) == ("Start\n4", "IndexError")

# ============================================================ 2. Syntax, runtime, and logic errors
assert "average = total + count / 2" in SRC["quick_2"] and run(SRC["quick_2"] + "\nprint(average)") == "13.0"
E["q2"] = choice("D")

# ============================================================ 3. Exception type and message
E["q3"] = true_false(True, False)

# ============================================================ 4. Common built-in exceptions
for expr, want in [('float("3,5")', "ValueError"), ('"abc"[3]', "IndexError"), ("[1, 2] + 3", "TypeError")]:
    assert run_error(f"print({expr})")[1] == want, expr
assert run('print(int(" 42 "))') == "42"
E["q4"] = table(e1=exc("ValueError"), e2=exc("IndexError"), e3=exc("TypeError"), e4=NONE)

# Checkpoint 1
CP1 = [('int("12.5")', "ValueError"), ("[3, 6, 9][3]", "IndexError"), ("len(42)", "TypeError"), ("7 % 0", "ZeroDivisionError")]
for expr, want in CP1:
    assert run_error(f"print({expr})")[1] == want, expr
assert run('print("7" * 2)') == "77"
E["cp1"] = table(e1=exc("ValueError"), e2=exc("IndexError"), e3=exc("TypeError"), e4=exc("ZeroDivisionError"), e5=NONE)
E["ex-cp1"] = example('print(int("12.5"))', output=False)

# ============================================================ 5. The try-except statement
ex("ex-age", "slide_8_1")
assert run_with_prompts(SRC["slide_8_1"], ["19"]) == "Age: Next year you will be 20\nDone"
assert run_with_prompts(SRC["slide_8_1"], ["old"]) == "Age: Enter the age as a whole number.\nDone"
assert run(SRC["quick_5"], ["word"]) == "First\nBad\nLast"
E["q5"] = table(l1=accept("First", width="8rem", placeholder="output"), l2=accept("Bad", width="8rem", placeholder="output"),
                l3=accept("Last", width="8rem", placeholder="output"))

# ============================================================ 6. Tracing a try-except statement
ex("ex-trace", "slide_10_1")
assert run_with_prompts(SRC["slide_10_1"], ["250"]) == "Points: Conversion worked.\nProgram continues."
assert run_with_prompts(SRC["slide_10_1"], ["two"]) == "Points: Conversion failed.\nProgram continues."
assert run(SRC["quick_6"].replace("____(a)____", "IndexError"), ["7"]) == "No such position."
E["q6"] = table(a=exc("IndexError"))

# ============================================================ 7. Unhandled exceptions
ex("ex-unhandled", "slide_11_1")
assert run_error(SRC["slide_11_1"], ["0"])[1] == "ZeroDivisionError"
assert run_error(SRC["quick_7"]) == ("", "IndexError")
E["q7"] = table(l1=exc("IndexError"))

# ============================================================ 8. Multiple except blocks and their order
ex("ex-multi", "slide_12_1")
for given, want in [("0", "25.0"), ("one", "Not a whole number."), ("5", "No such position."), ("1", "The value is 0.")]:
    assert run_with_prompts(SRC["slide_12_1"], [given]) == "Position: " + want, given
assert run(SRC["quick_8"]) == "First"
E["q8"] = choice("B")

# ============================================================ 9. A tuple of exception types
ex("ex-tuple", "slide_14_1")
assert run_with_prompts(SRC["slide_14_1"], ["7"]) == "Position: Enter a position from 0 to 2."
E["q9"] = true_false(True, False)

# ============================================================ 10. The exception object
assert ex("ex-err", "slide_15_1", output=True)["output"] == "Conversion failed.\ninvalid literal for int() with base 10: 'twelve'"
MSG_EMPTY = "invalid literal for int() with base 10: ''"
assert run(SRC["quick_10"]) == MSG_EMPTY
E["q10"] = table(l1=accept(MSG_EMPTY, width="24rem", placeholder="output", show=MSG_EMPTY))

# Checkpoint 2
CP2 = [("2", "5"), ("1", "Zero value"), ("3", "Bad position"), ("1.5", "Bad position"), ("-1", "5")]
for given, want in CP2:
    assert run_with_prompts(SRC["slide_16_1"], [given]) == "Position: " + want, given
E["cp2"] = table(**{f"o{i}": accept(want, width="10rem", placeholder="output") for i, (_, want) in enumerate(CP2, 1)})
ex("ex-cp2", "slide_16_1")

# ============================================================ 11. Size of the try block
ex("ex-big-try", "slide_18_1")
ex("ex-small-try", "slide_18_2")
assert run_with_prompts(SRC["slide_18_1"], ["4"]) == "Count: Count must not be zero."
assert run_error(SRC["slide_18_2"], ["4"])[1] == "ZeroDivisionError"
E["q11"] = choice("A")

# ============================================================ 12. Bare except and broad handlers
ex("ex-bare", "slide_19_1")
assert run_with_prompts(SRC["slide_19_1"], ["3"]) == "Quantity: Enter a whole number."
E["q12"] = true_false(True, False)

# ============================================================ 13. An if test or try-except
ex("ex-isdigit", "slide_21_1")
ex("ex-tryint", "slide_21_2")
assert run(SRC["quick_13"]) == "False\n-3"
E["q13"] = table(l1=accept("False", width="8rem", placeholder="output"), l2=accept("-3", width="8rem", placeholder="output"))

# Checkpoint 3
cp3 = SRC["slide_23_1"]
cp3_cases = input_cases(cp3,
    ("Inputs 10 and 2.5", ["10", "2.5"]),
    ("Inputs 10 and 4", ["10", "4"]),
    ("Inputs 12.5 and 0", ["12.5", "0"]),
    ("Inputs abc and 2", ["abc", "2"]),
    ("Inputs 9 and two", ["9", "two"]),
    ("Inputs 7 and -2", ["7", "-2"]))
assert cp3_cases[0]["expected"] == "Total cost: Items: Enter numbers only."
assert cp3_cases[1]["expected"] == "Total cost: Items: Cost per item: 2.50"
assert cp3_cases[2]["expected"] == "Total cost: Items: Items must not be zero."
E["cp3"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": SRC["slide_22_1"],
    "cases": cp3_cases,
    "check": EXC + needs("ValueError", "ZeroDivisionError"),
    "answer": b64(cp3),
    "answerNote": "float and int can raise ValueError, and the division can raise ZeroDivisionError. Each gets its own message."}
E["cp3-out"] = table(out=accept("Enter numbers only.", "Enter numbers only", width="14rem", placeholder="output", show="Enter numbers only."))

# ============================================================ Coding Practice
# 1. An unmatched exception (R7.7)
ex("ex-p1", "practice_1_prompt")
assert run(SRC["practice_1_prompt"], ["4"]) == "15.0"
assert run(SRC["practice_1_prompt"], ["word"]) == "Enter a whole number."
assert run_error(SRC["practice_1_prompt"], ["0"])[1] == "ZeroDivisionError"
E["p1-out"] = table(i4=accept("15.0", width="12rem", placeholder="output"),
                    iword=accept("Enter a whole number.", "Enter a whole number", width="14rem", placeholder="output", show="Enter a whole number."),
                    i0=exc("ZeroDivisionError", "14rem"))
E["p1-why"] = short("The input 0 ends with an unhandled ZeroDivisionError. The division 60 / 0 raises it, and the only except block names ValueError.")
p1 = SRC["practice_1_solution"]
E["p1"] = {"type": "code", "xp": 5, "minLines": 7,
    "starter": SRC["practice_1_prompt"],
    "cases": input_cases(p1, ("Input 4", ["4"]), ("Input word", ["word"]), ("Input 0", ["0"]), ("Input -5", ["-5"]), ("Input 2.5", ["2.5"])),
    "check": EXC + needs("ValueError", "ZeroDivisionError"),
    "answer": b64(p1),
    "answerNote": "The new block names ZeroDivisionError, the type that 60 / 0 raises."}

# 2. An exception object (R7.8)
p2 = SRC["practice_2_solution"]
assert run(p2) == ("12\nEnter a whole number.\ninvalid literal for int() with base 10: 'twelve'\nEnter a whole number.\n"
                   "invalid literal for int() with base 10: ''\nEnter a whole number.\ninvalid literal for int() with base 10: '4.0'")
E["p2"] = {"type": "code", "xp": 5, "minLines": 11,
    "starter": "def describe(text):\n    pass\n\n\n# Call describe with \"12\", \"twelve\", \"\" and \"4.0\".\n",
    "cases": [{"name": "Calls with \"12\", \"twelve\", \"\" and \"4.0\"", "expected": run(p2)}],
    "check": EXC + needs("ValueError") + '''_fn("describe", "text")
assert any(h.name == "err" for h in _H), "Name the exception object err: except ValueError as err."
''',
    "answer": b64(p2),
    "answerNote": "Each failing call prints the plain instruction, then the message stored in err."}
E["p2-who"] = short("The line Enter a whole number. is for the user. It says what to do. The exception message is for the programmer. It shows the text that int could not convert.")

# 3. Altitude and boiling point (P3.11)
p3 = SRC["practice_3_solution"]
p3_cases = input_cases(p3,
    ("1500 meters", ["1500", "m"]),
    ("2000 feet", ["2000", "ft"]),
    ("Bad number", ["high", "m"]),
    ("Bad unit", ["600", "km"]),
    ("Sea level", ["0", "m"]),
    ("Spaces around a number", [" 900 ", "ft"]))
assert [c["expected"] for c in p3_cases] == ["95.0", "98.0", "Enter a number.", "Unknown unit.", "100.0", "99.1"]
E["p3"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": "altitude_text = input()\nunit = input()\n",
    "cases": p3_cases,
    "check": EXC + needs("ValueError"),
    "answer": b64(p3),
    "answerNote": "A flag records whether the conversion worked. The unit is one of a few known words, so an if test checks it."}
E["p3-why"] = short("The unit has a short list of valid values, so an if test can check it. For the number, the conversion itself is the best test, so float runs inside try and a ValueError is handled.")

# 4. A second price (P7.13)
p4 = SRC["practice_4_solution"]
p4_cases = input_cases(p4,
    ("Valid first price", ["20"]),
    ("Invalid, then valid", ["abc", "20"]),
    ("Two invalid prices", ["abc", "x"]),
    ("Blank, then valid", ["", "5"]),
    ("Decimal price", ["9.99"]))
assert [c["expected"] for c in p4_cases] == ["22.60", "Enter a number.\n22.60", "Enter a number.\nNo valid price.", "Enter a number.\n5.65", "11.29"]
E["p4"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": "",
    "cases": p4_cases,
    "check": EXC + needs("ValueError") + '''assert len(_tries()) >= 2, "Use a second try statement inside the except block for the second price."
assert not _loops(), "Do not use a loop. Read the price at most twice."
''',
    "answer": b64(p4),
    "answerNote": "The second try sits inside the first except block, so the program reads a second price only after a bad first one."}

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-29",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 29 Workbook",
    "subtitle": "Exceptions and try / except",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-29/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
