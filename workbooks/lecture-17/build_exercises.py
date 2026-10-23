"""Build workbooks/lecture-17/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_17_SHARED_CONTENT.tex; model answers follow its \\solution{...}
text. Run from anywhere:

    python3 workbooks/lecture-17/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-17
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

def rewrite_case(name, code, rewrites=()):
    """A grading case whose `expected` comes from running the model answer
    with the same rewrites applied."""
    source = code
    for old, new in rewrites:
        assert old in source, old
        source = source.replace(old, new)
    c = {"name": name, "expected": out(source)}
    if rewrites:
        c["rewrite"] = [list(r) for r in rewrites]
    return c

def num(*values, width="4rem"):
    return {"accept": [str(v) for v in values], "placeholder": "value", "width": width}

def line(text, width="14rem"):
    forms = [text, f"'{text}'", f'"{text}"']
    return {"accept": forms, "placeholder": "output line", "width": width, "show": text, "caseSensitive": True}

def true_false(value):
    return {"accept": ["true", "t", "yes"] if value else ["false", "f", "no"], "placeholder": "true / false", "width": "7rem", "show": "True" if value else "False"}

def short(answer, xp=2, min_chars=15, rows=2, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

E = {}

# ---------------------------------------------------------------- checks shared by the coding tasks
# A check runs after the student's program in the same namespace. These helpers
# find a function the program defined and call it with its output captured, so
# the call does not add to the program's own output.
FN = '''import types, io, contextlib, re
def _fn(name):
    f = globals().get(name)
    assert isinstance(f, types.FunctionType), "Define a function named " + name + " with def."
    assert f.__code__.co_argcount == 0, "Define " + name + " with empty parentheses."
    assert f.__doc__ and f.__doc__.strip() and "___" not in f.__doc__, "Give " + name + " a docstring as the first statement of its body."
    return f
def _out(f):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        f()
    return buffer.getvalue()
def _local(name, *variables):
    f = _fn(name)
    for v in variables:
        assert v in f.__code__.co_varnames, "Assign " + v + " inside the body of " + name + "."
'''

def calls(name, count, message):
    """The function name appears once in its def and `count` times as a call."""
    return f'assert len(re.findall(r"\\b{name}\\s*\\(", __code__)) == {count} + 1, "{message}"\n'

# ============================================================ 3. A function as a black box
assert round(6.8275, 2) == 6.83
assert len("coffee") == 6
E["cp1"] = short('The function name is `len`. The argument is `"coffee"`, and the result is `6`. Its promise is to return the number of characters '
                 'in the string. We can use that promise without knowing its internal instructions.',
                 min_chars=20, rows=3, placeholder="Function name: … Argument: … Result: …")

# ============================================================ 4. Our first function
first_function = '''def greet():
    """Display a greeting."""
    print("Hello!")

greet()
greet()
'''
E["ex-greet"] = example(first_function)
assert E["ex-greet"]["output"] == "Hello!\nHello!"

# ============================================================ 5. A call runs the body, then execution continues
call_and_continue = 'def greet():\n    print("Hello!")\n\ngreet()\nprint("Back here")\n'
E["ex-call"] = example(call_and_continue, output=False)
assert out(call_and_continue) == "Hello!\nBack here"

# ============================================================ 6. Loops and decisions inside a function
countdown = '''def countdown():
    for number in range(3, 0, -1):
        print(number)
    print("Go!")

countdown()
'''
E["ex-countdown"] = example(countdown)
assert E["ex-countdown"]["output"] == "3\n2\n1\nGo!"
show_result = '''def show_result():
    mark = int(input("Mark: "))
    if mark >= 50:
        print("Pass")
    else:
        print("Try again")

show_result()
'''
E["ex-result"] = example(show_result, output=False)
assert run_with_prompts(show_result, ["72"]) == "Mark: Pass"
assert run_with_prompts(show_result, ["40"]) == "Mark: Try again"

# ============================================================ 7. Python needs the definition before the call runs
order_fail = 'greet()\n\ndef greet():\n    print("Hello!")\n'
E["ex-order-fail"] = example(order_fail, output=False)
stdout, stderr = run(order_fail, ok=False)
assert stdout == "" and "NameError" in stderr
order_fixed = 'def greet():\n    print("Hello!")\n\ngreet()\n'
E["ex-order-fixed"] = example(order_fixed, output=False)
assert out(order_fixed) == "Hello!"

# Checkpoint 2: Coffee for two
coffee = '''def make_coffee():
    """Display the steps for one cup of coffee."""
    print("Grind the beans")
    print("Brew the coffee")
    print("Pour into a cup")

make_coffee()
make_coffee()
'''
STEPS = ["Grind the beans", "Brew the coffee", "Pour into a cup"]
E["cp2"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "def make_coffee():\n    # Write the docstring and body.\n\n# Add the calls.\n",
    "cases": [rewrite_case("Two calls", coffee)],
    "check": FN + '_f = _fn("make_coffee")\n'
             'assert _out(_f) == "Grind the beans\\nBrew the coffee\\nPour into a cup\\n", '
             '"make_coffee should print Grind the beans, Brew the coffee, and Pour into a cup, in that order, and nothing else."\n'
             + calls("make_coffee", 2, "Call make_coffee twice."),
    "answer": b64(coffee)}
assert E["cp2"]["cases"][0]["expected"] == "\n".join(STEPS * 2)
E["cp2-predict"] = {"type": "table", "xp": 1, "blanks": {f"l{i + 1}": line(text, "12rem") for i, text in enumerate(STEPS * 2)}}

# Checkpoint 3: A function that reads a mark
grade = '''def show_grade():
    """Read a mark and show its grade message."""
    mark = int(input("Mark: "))
    if mark >= 80:
        print("Excellent")
    elif mark >= 50:
        print("Pass")
    else:
        print("Try again")

show_grade()
'''
MESSAGES = ("Excellent", "Pass", "Try again")

def message_case(mark, want):
    """Check-only case: the prompt is the student's choice, so look at the message only."""
    others = [m for m in MESSAGES if m != want]
    check = (f'_lines = __stdout__.rstrip().split("\\n")\n'
             f'assert _lines[-1].endswith("{want}") and not any(_m in __stdout__ for _m in {others!r}), '
             f'"With the mark {mark}, print {want} and no other message."\n')
    return {"name": f"Typed {mark}", "inputs": [str(mark)], "check": check}

GRADE_TESTS = [(80, "Excellent"), (50, "Pass"), (49, "Try again"), (100, "Excellent"), (79, "Pass"), (0, "Try again")]
for mark, want in GRADE_TESTS:
    assert run_with_prompts(grade, [str(mark)]) == "Mark: " + want
E["cp3"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": "def show_grade():\n    # Write the docstring and body.\n\n# Add the call.\n",
    "cases": [message_case(mark, want) for mark, want in GRADE_TESTS],
    "check": FN + '''_f = _fn("show_grade")
assert "input" in _f.__code__.co_names, "Read the mark with input() inside the body of show_grade."
assert re.search(r"^\\s*elif\\b", __code__, re.M) and re.search(r"^\\s*else\\s*:", __code__, re.M), "Choose the message with if, elif, and else."
''' + calls("show_grade", 1, "Call show_grade once."),
    "answer": b64(grade)}

# Checkpoint 4: Fibonacci numbers
fibonacci = '''def show_fibonacci():
    """Display the requested Fibonacci numbers."""
    count = int(input("How many? "))
    first = 0
    second = 1
    for position in range(count):
        print(first)
        next_number = first + second
        first = second
        second = next_number

show_fibonacci()
'''

def fib(n):
    a, b, values = 0, 1, []
    for _ in range(n):
        values.append(a)
        a, b = b, a + b
    return values

assert fib(7) == [0, 1, 1, 2, 3, 5, 8]

def fib_case(count):
    """Check-only case: whatever the prompt, the program must end with the numbers, one per line."""
    want = fib(count)
    text = "".join(f"{v}\n" for v in want)
    if not want:
        shown = "print no numbers"
    elif len(want) == 1:
        shown = f"print {want[0]}"
    else:
        shown = "print " + ", ".join(map(str, want)) + ", one per line"
    check = (f'import re\n_text = {text!r}\n'
             f'assert __stdout__.endswith(_text) and not re.search(r"\\d\\s*$", __stdout__[:len(__stdout__) - len(_text)]), '
             f'"With a count of {count}, {shown}."\n')
    return {"name": f"Typed {count}", "inputs": [str(count)], "check": check}

FIB_COUNTS = (7, 0, 1, 2)
for count in FIB_COUNTS:
    assert run_with_prompts(fibonacci, [str(count)]) == ("How many? " + "\n".join(map(str, fib(count)))).rstrip("\n")
E["cp4"] = {"type": "code", "xp": 5, "minLines": 11,
    "starter": "def show_fibonacci():\n    # Write the docstring and body.\n\n# Add the call.\n",
    "cases": [fib_case(count) for count in FIB_COUNTS],
    "check": FN + '''_f = _fn("show_fibonacci")
assert "input" in _f.__code__.co_names, "Read the count with input() inside the body of show_fibonacci."
assert re.search(r"^\\s*(for|while)\\b", __code__, re.M), "Use a loop to print the numbers."
''' + calls("show_fibonacci", 1, "Call show_fibonacci once."),
    "answer": b64(fibonacci),
    "answerNote": "Input `7` gives the output lines `0, 1, 1, 2, 3, 5, 8`. Save the sum in `next_number` before changing either previous value."}

# ============================================================ 8. Decomposition and the six stages
notice = '''def show_heading():
    print("Study session")

def show_details():
    print("Room EN-1040, 10:00")

def show_reminder():
    print("Bring your workbook.")

show_heading()
show_details()
show_reminder()
'''
E["ex-notice"] = example(notice)
assert E["ex-notice"]["output"] == "Study session\nRoom EN-1040, 10:00\nBring your workbook."

# Checkpoint 5: Choosing function boundaries
E["cp5"] = short("Possible names and jobs:\n\n`read_mark`: Obtain the mark from the user.\n\n`calculate_grade`: Work out the grade for that mark.\n\n"
                 "`show_report`: Display the completed report.\n\n"
                 "Each name describes one job. We can test the grading calculation separately and reuse it wherever the program needs a grade.",
                 xp=2, min_chars=30, rows=6, placeholder="function_name: one job (one line for each function)")

# ============================================================ 9. A docstring describes the function's promise
docstring = '''def show_heading():
    """Display the heading for the study session."""
    print("Study session")
    print("=============")
'''
E["ex-docstring"] = example(docstring, output=False)
assert out(docstring) == ""
assert "Display the heading for the study session." in out(docstring + "\nhelp(show_heading)\n")

# ============================================================ Review (cheat sheet, no questions)
review_coffee = '''def make_coffee():
    """Display the coffee steps."""
    print("Grind the beans")
    print("Brew the coffee")
    print("Pour into a cup")

make_coffee()
make_coffee()
'''
E["ex-review-coffee"] = example(review_coffee)
assert E["ex-review-coffee"]["output"] == "\n".join(STEPS * 2)

# ============================================================ Coding Practice
# 1. Information in a call
E["p1"] = short("The function is `len`. The supplied information is the string `'paper'`. The value produced is `5`.", min_chars=20, rows=3,
                placeholder="Function: … Information supplied: … Value produced: …")
assert len("paper") == 5

# 2. Execution order
practice2 = "def show_tag():\n    print('Item')\n\nprint('Open')\nshow_tag()\nprint('Close')\n"
assert out(practice2) == "Open\nItem\nClose"
E["p2"] = {"type": "table", "xp": 1, "blanks": {"l1": line("Open", "8rem"), "l2": line("Item", "8rem"), "l3": line("Close", "8rem")}}

# 3. Names and promises
names = """def show_report_heading():
    \"\"\"Display the report heading.\"\"\"
    print('Report')

def show_closing():
    \"\"\"Display the closing reminder.\"\"\"
    print('Keep this report.')

show_report_heading()
show_closing()
"""
assert out(names) == "Report\nKeep this report."
E["p3"] = {"type": "code", "xp": 5, "minLines": 9, "starter": "# Define the two functions, then call each one once.\n",
    "cases": [{"name": "Your two functions"}],
    "check": '''import types, re
_mine = [f for f in list(globals().values()) if isinstance(f, types.FunctionType) and f.__code__.co_filename != "<check>"]
assert len(_mine) >= 2, "Define two functions with def: one for the report heading and one for the closing reminder."
for _f in _mine:
    assert _f.__code__.co_argcount == 0, "Define " + _f.__name__ + " with empty parentheses."
    assert _f.__doc__ and _f.__doc__.strip(), "Give " + _f.__name__ + " a docstring as the first statement of its body."
    assert len(re.findall(r"\\b" + _f.__name__ + r"\\s*\\(", __code__)) == 2, "Call " + _f.__name__ + " exactly once."
assert len([l for l in __stdout__.split("\\n") if l.strip()]) >= 2, "Give each function one output statement, so the program prints two lines."
''',
    "answer": b64(names),
    "answerNote": "One possible pair of functions. Each docstring describes the output task."}

# 4. Definitions and calls
E["p4"] = {"type": "table", "xp": 1, "blanks": {"s1": true_false(False), "s2": true_false(True), "s3": true_false(False), "s4": true_false(True)}}
E["p4-fix"] = short("1. False: the body runs when called. 2. True. 3. False: a function can perform another task, such as a calculation. 4. True.",
                    min_chars=20, rows=3, placeholder="Correct statement 1… Correct statement 3…")

# 5. Repeated calls
practice5 = "def show_left():\n    print('Left')\n\ndef show_right():\n    print('Right')\n\nshow_left()\nshow_right()\nshow_left()\n"
assert out(practice5) == "Left\nRight\nLeft"
E["p5"] = {"type": "table", "xp": 1, "blanks": {"l1": line("Left", "8rem"), "l2": line("Right", "8rem"), "l3": line("Left", "8rem"),
    "left": num(2, "twice", "two"), "right": num(1, "once", "one")}}

# 6. A numerical summary
summary = """def show_smallest():
    \"\"\"Display the smallest of three fixed values.\"\"\"
    a = 8
    b = 3
    c = 7
    smallest = a
    if b < smallest:
        smallest = b
    if c < smallest:
        smallest = c
    print(smallest)

def show_average():
    \"\"\"Display the average of three fixed values.\"\"\"
    a = 8
    b = 3
    c = 7
    print((a + b + c) / 3)

show_smallest()
show_average()
"""
ALL_FOUR = [("a = 8", "a = 4"), ("b = 3", "b = 4"), ("c = 7", "c = 4")]
E["p6"] = {"type": "code", "xp": 5, "minLines": 18,
    "starter": ("def show_smallest():\n    # Write the docstring here.\n    a = 8\n    b = 3\n    c = 7\n    # Print the smallest value.\n\n"
                "def show_average():\n    # Write the docstring here.\n    a = 8\n    b = 3\n    c = 7\n    # Print the average.\n\nshow_smallest()\nshow_average()\n"),
    "cases": [rewrite_case("a = 8, b = 3, c = 7", summary), rewrite_case("All three values 4", summary, ALL_FOUR)],
    "check": FN + '_local("show_smallest", "a", "b", "c")\n_local("show_average", "a", "b", "c")\n',
    "answer": b64(summary),
    "answerNote": "Use comparisons to keep the smallest value found so far."}
assert E["p6"]["cases"][0]["expected"] == "3\n6.0" and E["p6"]["cases"][1]["expected"] == "4\n4.0"

# 7. Relationships between values
relations = """def show_relationships():
    \"\"\"Display three relationships between fixed values.\"\"\"
    a = 4
    b = 4
    c = 6
    print(a == b and b == c)
    print(a != b and a != c and b != c)
    print(a <= b and b <= c)

show_relationships()
"""
E["p7"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "def show_relationships():\n    # Write the docstring here.\n    a = 4\n    b = 4\n    c = 6\n    # Print the three Boolean values.\n\nshow_relationships()\n",
    "cases": [rewrite_case("a = 4, b = 4, c = 6", relations),
              rewrite_case("2, 2, 2", relations, [("a = 4", "a = 2"), ("b = 4", "b = 2"), ("c = 6", "c = 2")]),
              rewrite_case("1, 3, 5", relations, [("a = 4", "a = 1"), ("b = 4", "b = 3"), ("c = 6", "c = 5")]),
              rewrite_case("5, 3, 1", relations, [("a = 4", "a = 5"), ("b = 4", "b = 3"), ("c = 6", "c = 1")])],
    "check": FN + '_local("show_relationships", "a", "b", "c")\n',
    "answer": b64(relations),
    "answerNote": "Compare each pair needed by the rule."}
assert [c["expected"] for c in E["p7"]["cases"][:3]] == ["False\nFalse\nTrue", "True\nFalse\nTrue", "False\nTrue\nTrue"]

# 8. Digits of a number
digits = """def show_digits():
    \"\"\"Display the first digit, last digit, and digit count.\"\"\"
    number = 8040
    text = str(number)
    print(text[0])
    print(text[len(text) - 1])
    print(len(text))

show_digits()
"""
E["p8"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "def show_digits():\n    # Write the docstring here.\n    number = 8040\n    # Print the first digit, last digit, and number of digits.\n\nshow_digits()\n",
    "cases": [rewrite_case("number = 8040", digits), rewrite_case("number = 0", digits, [("number = 8040", "number = 0")]),
              rewrite_case("number = 7", digits, [("number = 8040", "number = 7")]), rewrite_case("number = 123456", digits, [("number = 8040", "number = 123456")])],
    "check": FN + '_local("show_digits", "number")\n',
    "answer": b64(digits),
    "answerNote": "Convert the nonnegative integer to text, then use indexing and length."}
assert E["p8"]["cases"][0]["expected"] == "8\n0\n4" and E["p8"]["cases"][1]["expected"] == "0\n0\n1"

# 9. Middle characters
middle = """def show_middle():
    \"\"\"Display the central characters of a fixed word.\"\"\"
    word = 'planet'
    length = len(word)
    if length == 0:
        print('Empty')
    elif length % 2 == 1:
        print(word[length // 2])
    else:
        print(word[length // 2 - 1:length // 2 + 1])

show_middle()
"""
E["p9"] = {"type": "code", "xp": 5, "minLines": 11,
    "starter": "def show_middle():\n    # Write the docstring and body.\n    word = 'planet'\n\nshow_middle()\n",
    "cases": [rewrite_case("word = 'planet'", middle), rewrite_case("word = 'stone'", middle, [("word = 'planet'", "word = 'stone'")]),
              rewrite_case("word = ''", middle, [("word = 'planet'", "word = ''")]), rewrite_case("word = 'a'", middle, [("word = 'planet'", "word = 'a'")]),
              rewrite_case("word = 'ab'", middle, [("word = 'planet'", "word = 'ab'")])],
    "check": FN + '_local("show_middle", "word")\n',
    "answer": b64(middle),
    "answerNote": "Check the empty string before choosing an index. The docstring states the task, and one call runs it. The three test outputs are `an`, `o`, and `Empty`."}
assert [c["expected"] for c in E["p9"]["cases"][:3]] == ["an", "o", "Empty"]

# 10. A growing balance
balance = """def show_balance():
    \"\"\"Display a fixed balance after yearly interest.\"\"\"
    balance = 200.0
    years = 2
    for year in range(years):
        balance = balance * 1.03
    print('%.2f' % balance)

show_balance()
"""
E["p10"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "def show_balance():\n    # Write the docstring here.\n    balance = 200.0\n    years = 2\n    # Apply each year's interest, then print the final balance.\n\nshow_balance()\n",
    "cases": [rewrite_case("years = 2", balance), rewrite_case("years = 0", balance, [("years = 2", "years = 0")]),
              rewrite_case("years = 10", balance, [("years = 2", "years = 10")])],
    "check": FN + '''_local("show_balance", "balance", "years")
assert re.search(r"^\\s*(for|while)\\b", __code__, re.M), "Use a loop that applies one year of growth on each pass."
assert re.search(r"\\b1\\.03\\b", __code__), "Multiply the balance by 1.03 for each year."
''',
    "answer": b64(balance),
    "answerNote": "Each repetition applies one year of growth."}
assert E["p10"]["cases"][0]["expected"] == "212.18" and E["p10"]["cases"][1]["expected"] == "200.00"

# 11. A colour code
colour = """def show_colour():
    \"\"\"Display the colour code for a fixed temperature.\"\"\"
    temperature = 25
    if temperature <= 25:
        red = 0
        green = round(255 * temperature / 25)
        blue = 255
    elif temperature <= 50:
        red = 0
        green = 255
        blue = round(255 * (50 - temperature) / 25)
    elif temperature <= 75:
        red = round(255 * (temperature - 50) / 25)
        green = 255
        blue = 0
    else:
        red = 255
        green = round(255 * (100 - temperature) / 25)
        blue = 0
    print(65536 * red + 256 * green + blue)

show_colour()
"""
T = "temperature = 25"
E["p11"] = {"type": "code", "xp": 10, "minLines": 20,
    "starter": "def show_colour():\n    # Write the docstring here.\n    temperature = 25\n    # Find red, green, and blue, then print the combined code.\n\nshow_colour()\n",
    "cases": [rewrite_case("temperature = 25", colour)] + [rewrite_case(f"temperature = {t}", colour, [(T, f"temperature = {t}")]) for t in ("0", "50", "75", "100", "12.5", "40", "60", "90")],
    "check": FN + '''_local("show_colour", "temperature")
assert "round(" in __code__, "Round each component with round."
''',
    "answer": b64(colour),
    "answerNote": "The four branches keep one component fixed while another changes."}
assert [c["expected"] for c in E["p11"]["cases"][:6]] == ["65535", "255", "65280", "16776960", "16711680", "33023"]

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-17",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 17 Workbook",
    "subtitle": "Problem solving with functions: black boxes and decomposition",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-17/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
