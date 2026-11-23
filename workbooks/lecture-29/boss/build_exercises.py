"""Build workbooks/lecture-29/boss/exercises.json: the Lecture 29 boss problems.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_29_SHARED_CONTENT.tex; the listings below are copied from it and
model answers follow its \\solution{...} text. Run from anywhere:

    python3 workbooks/lecture-29/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-29/boss
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
# Boss listings from the kit.
SRC = {}
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

# ---------------------------------------------------------------- 1 Pick an item (original, awaiting approval)
pick = SRC["boss_1_solution"]
pick_cases = input_cases(pick,
    ("Example 1: position 3", ["3"]),
    ("Example 2: position 0", ["0"]),
    ("Position 1", ["1"]),
    ("Position 5", ["5"]),
    ("Position 6", ["6"]),
    ("Position -2", ["-2"]),
    ("Text two", ["two"]),
    ("Decimal 2.5", ["2.5"]),
    ("Blank line", [""]),
    ("Spaces around 4", [" 4 "]))
assert [c["expected"] for c in pick_cases] == ["cup", "Out of range.", "pen", "ruler", "Out of range.", "Out of range.",
    "Enter a whole number.", "Enter a whole number.", "Enter a whole number.", "bag"]
E["pick-item"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 11,
    "starter": SRC["boss_1_starter"],
    "cases": pick_cases,
    "check": EXC + needs("ValueError", "IndexError"),
    "hints": [
        "Convert the input with `int` inside the `try` block. The user counts from 1, so the list index is `position - 1`.",
        "Python accepts a negative index such as `items[-1]`, so it raises no exception for 0 or a negative position. Test `position < 1` with `if`.",
        "Give `ValueError` and `IndexError` separate `except` blocks. Both out-of-range cases print `Out of range.`",
    ],
    "answer": b64(pick),
    "answerNote": "The if test catches 0 and negative positions, which Python would accept as indexes. An IndexError covers positions above 5."}

# ---------------------------------------------------------------- 2 Running total (Stephenson 148)
total = SRC["boss_2_solution"]
total_cases = input_cases(total,
    ("Example 1: 2, bad, 3.5", ["2", "bad", "3.5", ""]),
    ("Example 2: blank line only", [""]),
    ("Whole numbers", ["1", "2", "3", ""]),
    ("Only invalid lines", ["x", "y", ""]),
    ("Negative and decimal values", ["-4", "0.5", "ten", ""]),
    ("Spaces around a number", [" 7 ", ""]))
assert total_cases[0]["expected"] == "Total: 2.0\nInvalid: bad\nTotal: 5.5\nFinal: 5.5\nSkipped: 1"
assert total_cases[1]["expected"] == "Final: 0.0\nSkipped: 0"
E["running-total"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 14,
    "starter": SRC["boss_2_starter"],
    "cases": total_cases,
    "check": EXC + needs("ValueError") + '''assert _loops(), "Read the lines with a while loop that stops at a blank line."
''',
    "hints": [
        "Read the first line before the loop, and read the next line at the end of the loop body. Stop when the line is `\"\"`.",
        "Put only the conversion and the lines that use its value in the `try` block. A `ValueError` prints `Invalid:` and adds 1 to `skipped`.",
        "Print the totals with f-strings such as `f\"Total: {total}\"`. Start `total` at `0.0` so it always prints as a float.",
    ],
    "answer": b64(total),
    "answerNote": "An invalid line raises ValueError before the total changes, so the handler only reports it and counts it."}

# ---------------------------------------------------------------- 3 Two trip speeds (original, awaiting approval)
# A zero time in the second trip is left out of the cases: the message of a
# float ZeroDivisionError is "float division by zero" before Python 3.14 and
# "division by zero" from 3.14 on.
trips = SRC["boss_3_solution"]
trip_cases = input_cases(trips,
    ("Example 1: 12, 3, 10, 2", ["12", "3", "10", "2"]),
    ("Example 2: 4, 0, 8, 2", ["4", "0", "8", "2"]),
    ("Example 3: 12, 3, 8, fast", ["12", "3", "8", "fast"]),
    ("Bad first distance", ["far", "3", "9", "4"]),
    ("Bad second distance", ["10", "4", "x", "2"]),
    ("Decimals", ["7.5", "2.5", "100", "8"]),
    ("Both trips bad", ["5", "", "", "3"]))
assert trip_cases[0]["expected"] == "Speed: 4.0\nSpeed: 5.0"
assert trip_cases[1]["expected"] == "Zero time.\nSpeed: 4.0"
assert trip_cases[2]["expected"] == "Speed: 4.0\nBad trip.\ncould not convert string to float: 'fast'"
E["trip-speeds"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 26,
    "starter": SRC["boss_3_starter"],
    "cases": trip_cases,
    "check": EXC + needs("ValueError", "ZeroDivisionError") + '''_fn("trip_speed", "distance_text", "time_text")
_grouped = [h for h in _H if set(_names(h)) == {"ValueError", "ZeroDivisionError"} and h.name == "err"]
assert _grouped, "In trip_speed, use one block: except (ValueError, ZeroDivisionError) as err:"
_f = [n for n in _TREE.body if isinstance(n, ast.FunctionDef) and n.name == "trip_speed"][0]
assert any(h in list(ast.walk(_f)) for h in _grouped), "Put the grouped except block inside trip_speed."
assert any(len(_names(h)) == 1 for h in _H if h not in list(ast.walk(_f))), "Handle ValueError and ZeroDivisionError in separate blocks for the first trip."
for _t in _tries():
    assert len(_t.body) <= 4, "Keep each try block small. Put only the lines that can fail inside it."
''',
    "hints": [
        "For the first trip, convert both values and divide inside one small `try`. Give `ValueError` and `ZeroDivisionError` their own `except` blocks.",
        "A flag such as `valid = True` records whether the calculation worked. Print the speed after the `try` statement only when the flag is still `True`.",
        "In `trip_speed`, one `except (ValueError, ZeroDivisionError) as err:` prints `Bad trip.` and then `err`. Print speeds with `f\"Speed: {speed:.1f}\"`.",
    ],
    "answer": b64(trips),
    "answerNote": "The first trip needs different messages, so it has two except blocks. The second trip gives the same response to both errors, so one grouped block prints the message from err."}

# ---------------------------------------------------------------- 4 Grade conversion (Stephenson 149, 51, 52)
grades = SRC["boss_4_solution"]
grade_cases = input_cases(grades,
    ("Example 1: 3.0, C+", ["3.0", "C+", ""]),
    ("Example 2: 0, 4.1", ["0", "4.1", ""]),
    ("Exact 4.0 and letter A", ["4.0", "A", ""]),
    ("Between two grades", ["3.5", "2.8", "1.1", ""]),
    ("Halfway values", ["3.15", "0.5", ""]),
    ("Invalid values", ["E", "-1", "b", ""]),
    ("Letters with signs", ["B-", "D+", "F", "A-", ""]))
assert grade_cases[0]["expected"] == "B\n2.3"
assert grade_cases[1]["expected"] == "F\nInvalid grade."
E["grade-convert"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 22,
    "starter": SRC["boss_4_starter"],
    "cases": grade_cases,
    "check": EXC + needs("ValueError") + '''assert len(_tries()) >= 2, "Inside the ValueError handler, use a second try for the letter lookup."
assert _loops(), "Read values with a while loop that stops at a blank line."
assert not any(isinstance(n, ast.Dict) for n in ast.walk(_TREE)), "Use the two parallel lists. Do not use a dictionary."
''',
    "hints": [
        "Try `float(text)` first. In range, find the closest value in `points`. A value exactly halfway between two grades takes the higher one.",
        "In the `except ValueError` block, use `letters.index(text)` in a second `try`. A missing letter raises another `ValueError`.",
        "The same position gives the matching grade points: `points[letters.index(text)]`. A value outside 0.0 to 4.0 is an `if` test, not an exception.",
    ],
    "answer": b64(grades),
    "answerNote": "The first try reads grade points. When float fails, the handler tries the letter list, and a second ValueError means the value is neither."}

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-29-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 29 Boss Problems",
    "short": "L29 bosses",
    "subtitle": "Exceptions and try / except",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-29/boss/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
for key, spec in E.items():
    for c in spec["cases"]:
        print(key, "|", c["name"], "|", c["expected"].replace("\n", " / "))
