"""Build workbooks/lecture-31/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_31_SHARED_CONTENT.tex; the listings below are copied from it and
model answers follow its \\solution{...} text. Run from anywhere:

    python3 workbooks/lecture-31/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-31
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
SRC['slide_2'] = '''mark = int(input("Mark: "))
print(f"You entered {mark}")'''
SRC['slide_4'] = '''while True:
    try:
        mark = int(input("Mark: "))
        break
    except ValueError:
        print("Please type a whole number.")
print(f"You entered {mark}")'''
SRC['quick_1'] = '''while True:
    try:
        n = int(input())
        break
    except ValueError:
        print("Try again.")
print(n * 2)'''
SRC['slide_6'] = '''while True:
    try:
        mark = int(input("Mark: "))
        if mark < 0 or mark > 100:
            raise ValueError("mark out of range")
        break
    except ValueError:
        print("Enter a mark from 0 to 100.")
print(f"You entered {mark}")'''
SRC['slide_7'] = '''def to_mark(text):
    """Return text as a mark from 0 to 100.

    Raise ValueError if it is not one.
    """
    mark = int(text)
    if mark < 0 or mark > 100:
        raise ValueError("mark out of range")
    return mark'''
SRC['slide_8'] = '''def main():
    while True:
        try:
            mark = to_mark(input("Mark: "))
            break
        except ValueError:
            print("Enter a mark from 0 to 100.")
    print(f"You entered {mark}")


main()'''
SRC['quick_3'] = '''def to_age(text):
    """Return text as an age from 0 to 120.

    Raise ValueError if it is not one.
    """
    age = ____(a)____(text)
    if age < 0 or age > 120:
        ____(b)____ ValueError("age out of range")
    return age

while True:
    try:
        age = to_age(input())
        ____(c)____
    except ValueError:
        print("Enter an age from 0 to 120.")'''
SRC['slide_9'] = '''def main():
    marks = []
    while True:
        text = input("Mark: ").strip()
        if text == "":
            break
        try:
            marks.append(to_mark(text))
        except ValueError:
            print(f"Not saved: {text}")
    print(f"Saved: {marks}")'''
SRC['quick_4'] = '''counts = []
while True:
    text = input().strip()
    if text == "":
        break
    try:
        counts.append(int(text))
    except ValueError:
        print("Skipped", text)
print(counts)'''
SRC['slide_11'] = '''def main():
    marks = []
    # the loop that reads the marks
    if len(marks) == 0:
        print("No marks.")
        return
    average = sum(marks) / len(marks)
    print(f"Average: {average:.1f}")'''
SRC['slide_12'] = '''if text.isdigit():
    mark = int(text)'''
SRC['slide_14'] = '''def to_mark(text):
    """Return text as a mark from 0 to 100.

    Raise ValueError if it is not one.
    """
    mark = int(text)
    if mark < 0 or mark > 100:
        raise ValueError("mark out of range")
    return mark

def main():
    while True:
        try:
            mark = to_mark(input("Mark: "))
            break
        except ValueError:
            print("Enter a mark from 0 to 100.")'''
SRC['slide_15'] = '''def main():
    marks = []
    while True:
        text = input("Mark: ").strip()
        if text == "":
            break
        try:
            marks.append(to_mark(text))
        except ValueError:
            print(f"Not saved: {text}")
    if len(marks) == 0:
        print("No marks.")
        return
    average = sum(marks) / len(marks)
    print(f"Average: {average:.1f}")'''
SRC['practice_1_solution'] = '''def to_letter(text):
    """Return one lowercase letter from a to z.

    Raise ValueError if the lowercase text is not one such letter.
    """
    letter = text.lower()
    if len(letter) != 1 or letter < "a" or letter > "z":
        raise ValueError("enter one letter")
    return letter


def main():
    """Print Vowel or Consonant. Return None. Handle ValueError."""
    while True:
        try:
            letter = to_letter(input("Letter: "))
            break
        except ValueError:
            print("Enter one letter.")
    if letter in ["a", "e", "i", "o", "u"]:
        print("Vowel")
    else:
        print("Consonant")


main()'''
SRC['practice_2_correct'] = '''def to_quantity(text):
    """Return text as a quantity from 1 to 50.

    Raise ValueError if it is not one.
    """
    quantity = int(text)
    if quantity < 1 or quantity > 50:
        raise ValueError("quantity out of range")
    return quantity'''
SRC['practice_2_bug'] = '''def to_quantity(text):
    """Return text as a quantity from 1 to 50.

    Raise ValueError if it is not one.
    """
    quantity = int(text)
    if quantity < 1 or quantity >= 50:
        raise ValueError("quantity out of range")
    return quantity'''

# Extra checks for the exam pattern: helper functions use no input or print,
# and every function the student writes has a docstring.
PURE = '''def _calls(name, fn):
    return any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == fn for n in ast.walk(_def(name)))
def _pure(*names):
    for _n in names:
        assert not _calls(_n, "input") and not _calls(_n, "print"), _n + " must not use input or print. main reads the input and prints."
def _docs(*names):
    for _n in names:
        assert any(isinstance(n, ast.FunctionDef) and n.name == _n for n in ast.walk(_TREE)), "Define a function named " + _n + "."
        assert ast.get_docstring(_def(_n)), "Write a docstring for " + _n + "."
'''

E = {}
TO_MARK = SRC["slide_7"]

def ex(name, code, output=False):
    E[name] = example(code, output)
    return E[name]

def out(*values, width="10rem"):
    """Blanks l1, l2, ... for lines of output. A name ending in Error is an exception blank."""
    return table(**{f"l{i}": (exc(v) if v.endswith("Error") else accept(v, width=width, placeholder="output"))
                    for i, v in enumerate(values, 1)})

# ============================================================ 1. Bad input
ex("ex-bad", SRC["slide_2"])
assert run_error(SRC["slide_2"], ["abc"])[1] == "ValueError"
assert run_with_prompts(SRC["slide_2"], ["150"]) == "Mark: You entered 150"
assert run_with_prompts(SRC["slide_2"], ["72"]) == "Mark: You entered 72"
assert run_error(SRC["slide_2"], ["7.5"])[1] == "ValueError"
TB = ("ValueError", "ValueError traceback", "a ValueError traceback", "traceback", "a traceback", "error", "ValueError error")
E["s1-runs"] = table(r1=accept(*TB, width="14rem", placeholder="what happens", show="ValueError traceback"),
                     r2=accept("You entered 150", width="14rem", placeholder="what happens"),
                     r3=accept("You entered 72", width="14rem", placeholder="what happens"),
                     r4=accept(*TB, width="14rem", placeholder="what happens", show="ValueError traceback"))
E["s1-why"] = short("The inputs abc and 7.5 are not whole numbers. The input 150 is a whole number outside 0 to 100. "
                    "The program accepted that bad value without an error message.")

# ============================================================ 2. The validation loop
ex("ex-loop", SRC["slide_4"])
assert run_with_prompts(SRC["slide_4"], ["abc", "7.5", "72"]) == \
    "Mark: Please type a whole number.\nMark: Please type a whole number.\nMark: You entered 72"
assert run(SRC["quick_1"], ["ten", "4.5", "6"]) == "Try again.\nTry again.\n12"
E["q1"] = out("Try again.", "Try again.", "12")

# ============================================================ 3. Checking the range
ex("ex-range", SRC["slide_6"])
assert run_with_prompts(SRC["slide_6"], ["abc", "150", "72"]) == \
    "Mark: Enter a mark from 0 to 100.\nMark: Enter a mark from 0 to 100.\nMark: You entered 72"
assert run('print(int("150"))') == "150"
E["q2"] = true_false(False, True)

# ============================================================ 4. A function that converts and checks
calls = TO_MARK + '\n\nprint(to_mark("72"))\nprint(to_mark(" 72 "))\nprint(to_mark("150"))\n'
assert run_error(calls) == ("72\n72", "ValueError")
assert run_error(TO_MARK + '\nto_mark("abc")')[1] == "ValueError"
ex("ex-to-mark", calls)
main1 = TO_MARK + "\n\n" + SRC["slide_8"]
ex("ex-main", main1)
assert run_with_prompts(main1, ["abc", "150", "72"]) == \
    "Mark: Enter a mark from 0 to 100.\nMark: Enter a mark from 0 to 100.\nMark: You entered 72"
q3 = SRC["quick_3"].replace("____(a)____", "int").replace("____(b)____", "raise").replace("____(c)____", "break")
assert run(q3 + '\nprint(age)', ["abc", "130", "-1", "35"]) == "Enter an age from 0 to 120.\n" * 3 + "35"
E["q3"] = table(a=accept("int", width="8rem", placeholder="name", show="int"),
                b=accept("raise", width="8rem", placeholder="keyword", show="raise"),
                c=accept("break", width="8rem", placeholder="keyword", show="break"))

# ============================================================ 5. Reading values until a blank line
blank = TO_MARK + "\n\n" + SRC["slide_9"] + "\n\n\nmain()\n"
ex("ex-blank", blank)
assert run_with_prompts(blank, ["72", "abc", "150", "95", ""]) == \
    "Mark: Mark: Not saved: abc\nMark: Not saved: 150\nMark: Mark: Saved: [72, 95]"
assert run(SRC["quick_4"], ["3", "two", " 5 ", "", "7"]) == "Skipped two\n[3, 5]"
E["q4"] = out("Skipped two", "[3, 5]")

# ============================================================ 6. The empty case
full = SRC["slide_14"].split("\ndef main")[0] + "\n\n" + SRC["slide_15"] + "\n\n\nmain()\n"
ex("ex-empty", full)
assert run_with_prompts(full, ["abc", ""]) == "Mark: Not saved: abc\nMark: No marks."
assert run_with_prompts(full, ["72", "95", ""]) == "Mark: Mark: Mark: Average: 83.5"
assert run_error("marks = []\nprint(sum(marks) / len(marks))")[1] == "ZeroDivisionError"
E["q5"] = choice("C")

# ============================================================ 7. Check first or try first
isd = 'text = "12"\n' + SRC["slide_12"] + "\nprint(mark)\n"
assert ex("ex-isdigit", isd, output=True)["output"] == "12"
assert run('for t in ["12", "-5", " 7 ", "3.5"]:\n    print(t.isdigit())') == "True\nFalse\nFalse\nFalse"
assert run('print("007".isdigit(), int("007"), "+4".isdigit(), int("+4"), "1,000".isdigit())') == "True 7 False 4 False"
assert run_error('int("1,000")')[1] == "ValueError"
tf = lambda v: accept(str(v), str(v).lower(), width="6rem", placeholder="", show=str(v))
E["q6"] = table(d1=tf(True), i1=accept("7", width="8rem", placeholder="result"),
                d2=tf(False), i2=accept("4", width="8rem", placeholder="result"),
                d3=tf(False), i3=exc("ValueError", width="9rem"))

# ============================================================ 8. Testing with bad input
q7 = SRC["quick_3"].split("\nwhile True")[0].replace("____(a)____", "int").replace("____(b)____", "raise")
assert run(q7 + '\nfor t in ["0", "120"]:\n    print(to_age(t))') == "0\n120"
for t in ["-1", "121", "abc"]:
    assert run_error(q7 + f'\nto_age("{t}")')[1] == "ValueError"
E["q7"] = choice("B")

# ============================================================ Coding Practice
# 1. Vowel or consonant (P3.19)
p1 = SRC["practice_1_solution"]
p1_cases = input_cases(p1,
    ("Example 1: E", ["E"]),
    ("Example 2: ab, 7, t", ["ab", "7", "t"]),
    ("A blank line, then u", ["", "u"]),
    ("A space, then Z", [" ", "Z"]),
    ("A word, then o", ["hello", "o"]))
assert [c["expected"] for c in p1_cases] == ["Letter: Vowel",
    "Letter: Enter one letter.\nLetter: Enter one letter.\nLetter: Consonant",
    "Letter: Enter one letter.\nLetter: Vowel", "Letter: Enter one letter.\nLetter: Consonant",
    "Letter: Enter one letter.\nLetter: Vowel"]
E["p1"] = {"type": "code", "xp": 5, "minLines": 20,
    "starter": "def to_letter(text):\n    pass\n\n\ndef main():\n    pass\n\n\nmain()\n",
    "cases": p1_cases,
    "check": EXC + PURE + needs("ValueError") + '''_f = _fn("to_letter", "text")
_fn("main")
_pure("to_letter")
_docs("to_letter", "main")
assert _raises(_def("to_letter")), "to_letter should raise ValueError for a bad input."
assert _quiet(_f, "E")[0] == "e", 'to_letter("E") should return "e".'
for _t in ["ab", "", "7", " "]:
    assert _quiet(_f, _t)[1] == "ValueError: enter one letter", "to_letter(" + repr(_t) + ') should raise ValueError("enter one letter").'
''',
    "answer": b64(p1),
    "answerNote": "to_letter only converts, checks and raises. main asks again in a validation loop and prints the result."}

# 2. Testing a validation function (original)
good = SRC["practice_2_correct"]
bug = SRC["practice_2_bug"]
assert run(good + '\nprint(to_quantity(" 24 "))') == "24"
for t, want in [("20", "20"), ("1", "1"), ("50", "50")]:
    assert run(good + f'\nprint(to_quantity("{t}"))') == want
for t in ["0", "51", "abc", ""]:
    assert run_error(good + f'\nto_quantity("{t}")')[1] == "ValueError"
assert run_error(bug + '\nto_quantity("50")')[1] == "ValueError"
assert run(bug + '\nprint(to_quantity("20"))') == "20" and run_error(bug + '\nto_quantity("abc")')[1] == "ValueError"
ex("ex-quantity", good + '\n\nprint(to_quantity(" 24 "))\n', output=True)
ex("ex-quantity-bug", bug + '\n\nprint(to_quantity("20"))\n', output=True)
VE = lambda: exc("ValueError", width="9rem")
E["p2-table"] = table(lo=accept("1", width="6rem", placeholder="input"), lo_r=accept("1", width="9rem", placeholder="result"),
                      hi=accept("50", width="6rem", placeholder="input"), hi_r=accept("50", width="9rem", placeholder="result"),
                      below=accept("0", width="6rem", placeholder="input"), below_r=VE(),
                      above=accept("51", width="6rem", placeholder="input"), above_r=VE(),
                      normal_r=accept("20", width="9rem", placeholder="result"), text_r=VE(), blank_r=VE())
E["p2-bug"] = table(t=accept("50", width="6rem", placeholder="input"), r=VE())
E["p2-why"] = short("Both versions return 20 for 20 and raise ValueError for abc.")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-31",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 31 Workbook",
    "subtitle": "Input validation and robust programs",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-31/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
