"""Build workbooks/lecture-12/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-12/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-12
"""
import base64, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=()):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""), capture_output=True, text=True)
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

def example(code, output=True, **kw):
    spec = {"type": "example", "code": code.rstrip("\n"), **kw}
    if output:
        spec["output"] = run(code)
    return spec

def case(name, inputs, code=None, check=None):
    """A grading case: `expected` from running the model answer with `inputs`."""
    c = {"name": name, "inputs": list(inputs)}
    if code is not None:
        c["expected"] = run_with_prompts(code, inputs)
    if check:
        c["check"] = check
    return c

TF = {"accept": ["True"], "show": "True"}, {"accept": ["False"], "show": "False"}
def tf(value):
    return dict(TF[0] if value else TF[1])

def num(value, width="5rem"):
    """A numeric table blank: accept the value as printed and as an int/float."""
    forms = [str(value)]
    if isinstance(value, float) and value == int(value):
        forms.append(str(int(value)))
    elif isinstance(value, int):
        forms.append(f"{value}.0")
    return {"accept": forms, "placeholder": "?", "width": width}

def word(accept, placeholder="?", width="8rem", show=None):
    d = {"accept": list(accept), "placeholder": placeholder, "width": width}
    if show:
        d["show"] = show
    return d

WHILE = "assert 'while' in __source__, 'Repeat the work with a while loop.'\n"

E = {}

# ============================================================ 1. A loop repeats work
E["ex-1"] = example("count = 1\n\nwhile count <= 5:\n    print(count)\n    count = count + 1\n")
E["cp1-body"] = {"type": "short", "xp": 2, "minChars": 10, "rows": 2, "placeholder": "Which statements form the loop body?", "answer": b64(
    "The loop body contains `print(count)` and `count = count + 1`.")}
E["cp1-count"] = {"type": "table", "xp": 1, "blanks": {
    "iters": word(["5", "five", "5 iterations", "five iterations"], "how many?", "8rem", "5")}}
E["cp1-changes"] = {"type": "short", "xp": 2, "minChars": 10, "rows": 2, "placeholder": "What changes from one iteration to the next?", "answer": b64(
    "The value of `count` changes from one pass to the next.")}

# ============================================================ 2. Spot repetition in a problem
REPEAT_WORDS = ["keep reading", "until", "keep", "reading", "keep reading temperatures", "count", "and count"]
E["cp2-words"] = {"type": "table", "xp": 1, "blanks": {
    "w1": word(REPEAT_WORDS, "word or phrase", "10rem", "keep reading"),
    "w2": word(REPEAT_WORDS, "word or phrase", "10rem", "until")}}
E["cp2-remember"] = {"type": "short", "xp": 2, "minChars": 10, "rows": 2, "placeholder": "What must the program remember while it repeats?", "answer": b64(
    "The program must remember a count of the temperatures above zero.")}

# ============================================================ 3. A while loop tests a condition
E["ex-3"] = example("balance = 100.0\ntarget = 200.0\n\nwhile balance < target:\n    balance = balance * 1.5\n\nprint(balance)\n")
YES = word(["yes", "y", "runs", "true"], "yes or no", "6rem", "yes")
NO = word(["no", "n", "does not run", "false"], "yes or no", "6rem", "no")
E["cp3"] = {"type": "table", "xp": 1, "blanks": {
    "c1": tf(True), "r1": dict(YES),
    "c2": tf(True), "r2": dict(YES),
    "c3": tf(False), "r3": dict(NO)}}
E["cp3-why"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 3, "placeholder": "Why would while balance >= target: be the wrong condition?", "answer": b64(
    "That condition is false at the starting balance of 100, so the loop would run zero times. It also describes when the program has already reached the target rather than when it still needs to keep going.")}

# ============================================================ 4. Every while loop needs three parts
E["ex-4"] = example("count = 1                 # initialize\n\nwhile count <= 5:        # test\n    print(count)\n    count = count + 1    # update\n")
INIT = ["initialize", "initialise", "initialization", "initialisation", "init"]
TEST = ["test", "the test", "condition"]
BODY = ["body work", "body", "work", "body-work"]
UPDATE = ["update", "the update"]
E["cp4"] = {"type": "table", "xp": 1, "blanks": {
    "l1": word(INIT, "label", "9rem", "initialize"),
    "l2": word(TEST, "label", "9rem", "test"),
    "l3": word(BODY, "label", "9rem", "body work"),
    "l4": word(UPDATE, "label", "9rem", "update")}}

# ============================================================ 5. Build the investment program gradually
E["ex-5a"] = example("RATE = 50.0\nINITIAL_BALANCE = 100.0\nTARGET = 200.0\n\nbalance = INITIAL_BALANCE\nyear = 0\n", output=False)
invest = ("RATE = 50.0\nINITIAL_BALANCE = 100.0\nTARGET = 200.0\n\nbalance = INITIAL_BALANCE\nyear = 0\n\n"
          "while balance < TARGET:\n    year = year + 1\n    interest = balance * RATE / 100\n    balance = balance + interest\n"
          "    print(f'After year {year}: ${balance:.2f}')\n\nprint(f'Target reached after {year} years.')\n")
E["ex-5c"] = example(invest)
E["cp5"] = {"type": "table", "xp": 1, "blanks": {
    "y0": num(0), "b0": num(100.0),
    "y1": num(1), "b1": num(150.0), "i1": num(50.0),
    "y2": num(2), "b2": num(225.0), "i2": num(75.0)}}
E["cp5-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why is the final message outside the loop?", "answer": b64(
    "It should be printed once, after the target has been reached. Putting it in the loop would print it after every year.")}

# ============================================================ 6. A while loop may run zero times
E["ex-6"] = example("level = 5\n\nwhile level < 3:\n    print('Inside the loop')\n    level = level + 1\n\nprint('Finished')\n")
ZERO = ["zero times", "zero", "0", "0 times", "never", "runs zero times"]
ONE = ["one time", "once", "one", "1", "1 time", "runs once"]
MORE = ["more than one time", "more than one", "more than once", "four times", "4 times", "4", "four", "more than one time (four)", "more than once (four times)"]
E["cp6"] = {"type": "table", "xp": 1, "blanks": {
    "z": word(ZERO, "how many times?", "10rem", "zero times"),
    "o": word(ONE, "how many times?", "10rem", "one time"),
    "m": word(MORE, "how many times?", "10rem", "more than one time")}}

# ============================================================ 7. An infinite loop never reaches its stopping point
cp7 = "count = 3\nwhile count > 0:\n    print(count)\n    count = count - 1\n"
E["cp7"] = {"type": "code", "xp": 2, "minLines": 5, "starter": "count = 3\nwhile count > 0:\n    print(count)\n",
    "cases": [{"name": "prints 3, 2, 1", "expected": run(cp7)}],
    "check": ("assert __source__.count('print(') == 1, 'Keep the single print(count) and let the loop repeat it.'\n"
              "assert count == 0, 'Subtract 1 from count on every pass so that count > 0 becomes False.'"),
    "answer": b64(cp7),
    "answerNote": "The update runs after the print, so 3, 2 and 1 are printed before count reaches 0."}
E["cp7-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "How does your line make the condition eventually become false?", "answer": b64(
    "Subtracting 1 after each `print` call changes `count` from 3 to 2 to 1 to 0. At 0, `count > 0` is `False`.")}

# ============================================================ 8. Off-by-one errors change the number of passes
E["ex-8"] = example("n = 1\nwhile n <= 5:\n    print(n, end=' ')\n    n = n + 1\nprint()\n")
E["cp8"] = {"type": "table", "xp": 1, "blanks": {
    "f1": num(2), "l1": num(6), "p1": num(5),
    "f2": num(2), "l2": num(5), "p2": num(4),
    "f3": num(6), "l3": num(2), "p3": num(5)}}

# ============================================================ 9. An accumulator builds a result
E["ex-9"] = example("total = 0\nnumber = 1\n\nwhile number <= 5:\n    total = total + number\n    number = number + 1\n\nprint('Total:', total)\n")
E["cp9"] = {"type": "table", "xp": 1, "blanks": {
    "a1": num(1),
    "b2": num(1), "a2": num(3),
    "b3": num(3), "a3": num(6),
    "b4": num(6), "a4": num(10),
    "b5": num(10), "a5": num(15)}}
E["cp9-where"] = {"type": "short", "xp": 2, "minChars": 10, "rows": 2, "placeholder": "Where must total = 0 appear?", "answer": b64(
    "It must appear before the loop so that initialization happens once.")}

# ============================================================ 10. A counter records how many times something happens
E["ex-10"] = example("evens = 0\nnumber = 1\n\nwhile number <= 10:\n    if number % 2 == 0:\n        evens = evens + 1\n    number = number + 1\n\nprint('Even numbers:', evens)\n")
E["cp10"] = {"type": "table", "xp": 1, "blanks": {
    "e1": num(0, "4rem"), "e2": num(1, "4rem"), "e3": num(1, "4rem"),
    "e4": num(2, "4rem"), "e5": num(2, "4rem"), "e6": num(3, "4rem")}}
E["cp10-why"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 3, "placeholder": "Why must number = number + 1 run on every iteration?", "answer": b64(
    "The loop-control variable must move toward 11 on every pass. If the update ran only for even values, the loop would stop changing at the first odd value and would be infinite.")}

# ============================================================ 11. A loop can read until the user stops
E["ex-11"] = example("total = 0.0\ntext = input('Value, or press Enter to finish: ')\n\nwhile text != '':\n    total = total + float(text)\n    text = input('Value, or press Enter to finish: ')\n\nprint(f'Total: {total:.2f}')\n", output=False)
E["cp11-before"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why is an input call needed before this loop?", "answer": b64(
    "The first input initializes `text` for the first condition test.")}
E["cp11-end"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why is another input call needed at the end of the body?", "answer": b64(
    "The second input updates `text` for the next test.")}
E["cp11-blank"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "What happens if the user presses Enter at the first prompt?", "answer": b64(
    "If the first input is blank, the loop runs zero times and the program prints `Total: 0.00`.")}

# ============================================================ Final review
FR = [
    "One iteration is one complete execution of the loop body.",
    "Initialize a loop-control value, test a condition, and update a value so that the condition can eventually become false.",
    "It runs zero times when its condition is `False` at the first test.",
    "The update may be missing, or the update may move the loop-control value away from a false condition. An update hidden on a path that never runs can cause the same problem.",
    "It is a loop error that causes one too many or one too few iterations.",
    "Start at 0 because adding 0 does not change the first value.",
    "An accumulator adds values to build a result. A counter adds 1 when an event occurs.",
    "The first input initializes the value used by the test. The second updates that value before the loop returns to the test.",
]
for i, ans in enumerate(FR, 1):
    E[f"fr{i}"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "answer": b64(ans)}

# ============================================================ Putting It All Together
pt = ("RATE = 50.0\nINITIAL_BALANCE = 100.0\nTARGET = 200.0\n\nbalance = INITIAL_BALANCE\nyear = 0\n\n"
      "while balance < TARGET:\n    year = year + 1\n    interest = balance * RATE / 100\n    balance = balance + interest\n\n"
      "print(f'Years: {year}')\nprint(f'Final balance: ${balance:.2f}')\n")
E["ex-pt"] = example(pt)
E["cp-int"] = {"type": "table", "xp": 1, "blanks": {
    "iters": word(["0", "zero", "none", "0 iterations", "zero iterations"], "how many?", "8rem", "0"),
    "line1": word(["Years: 0", "Years:0"], "first line printed", "14rem", "Years: 0"),
    "line2": word(["Final balance: $200.00", "Final balance: $200.0", "Final balance: 200.00", "Final balance:$200.00"], "second line printed", "14rem", "Final balance: $200.00")}}
E["cp-int-why"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 3, "placeholder": "Why does the program not need a special if statement for this case?", "answer": b64(
    "The `while` condition is already false, and the variables were initialized before the loop, so the existing structure handles the case.")}

# ============================================================ Coding Practice
# ---- A. Print square numbers
ca = "limit = int(input('Limit: '))\nnumber = 1\n\nwhile number * number < limit:\n    print(number * number, end=' ')\n    number = number + 1\n\nprint()\n"
E["ca"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "limit = int(input('Limit: '))\nnumber = 1\n\nwhile ______________________________:\n    print(________________, end=' ')\n    number = _________________________\n\nprint()\n",
    "cases": [case("limit = 20", ["20"], ca), case("limit = 1", ["1"], ca), case("limit = 16", ["16"], ca), case("limit = 50", ["50"], ca)],
    "check": WHILE,
    "answer": b64(ca),
    "answerNote": "The loop tests the next square before printing it. With limit = 1, the first test is false and the loop runs zero times."}

# ---- B. Build totals and products
cb1 = ("first = int(input('First: '))\nlast = int(input('Last: '))\nnumber = first\ntotal = 0\n\n"
       "while number <= last:\n    if number % 2 != 0:\n        total = total + number\n    number = number + 1\n\nprint('Total:', total)\n")
E["cb1"] = {"type": "code", "xp": 5, "minLines": 11,
    "starter": ("first = int(input('First: '))\nlast = int(input('Last: '))\nnumber = first\ntotal = 0\n\n"
                "while ______________________________:\n    if ______________________________:\n        total = ______________________\n    number = _________________________\n\nprint('Total:', total)\n"),
    "cases": [case("first = 3, last = 9", ["3", "9"], cb1), case("first = 2, last = 10", ["2", "10"], cb1),
              case("first = 4, last = 4", ["4", "4"], cb1), case("first = 1, last = 1", ["1", "1"], cb1)],
    "check": WHILE + "assert '%' in __source__, 'Use % to tell an odd number from an even one.'\n",
    "answer": b64(cb1),
    "answerNote": "A sum starts at 0. The loop-control variable number changes on every iteration, whether or not the value was added."}
cb2 = "number = 1\nproduct = 1\n\nwhile number <= 5:\n    product = product * number\n    number = number + 1\n\nprint('Product:', product)\n"
E["cb2"] = {"type": "code", "xp": 2, "minLines": 8,
    "starter": "number = 1\nproduct = 1\n\nwhile ______________________________:\n    product = ________________________\n    number = _________________________\n\nprint('Product:', product)\n",
    "cases": [{"name": "1 through 5", "expected": run(cb2)}],
    "check": WHILE + "assert '120' not in __source__, 'Multiply the numbers in the loop instead of writing 120 in the code.'\nassert number == 6, 'Add 1 to number on every pass so the loop stops after 5.'\n",
    "answer": b64(cb2),
    "answerNote": "A product starts at 1. Starting at 0 would make every later product 0."}

# ---- C. Trace a loop
E["cc"] = {"type": "table", "xp": 1, "blanks": {
    "v1": num(2), "t1": num(2), "u1": num(4),
    "v2": num(4), "t2": num(6), "u2": num(6),
    "v3": num(6), "t3": num(12), "u3": num(8),
    "v4": num(8), "t4": num(20), "u4": num(10)}}
E["cc-final"] = {"type": "table", "xp": 1, "blanks": {
    "cond": word(["10 <= 8", "10<=8", "value <= 8 with value = 10", "10 <= 8 is False"], "the last test", "10rem", "10 <= 8"),
    "val": tf(False)}}

# ---- D. Predict and complete loops
E["cd"] = {"type": "table", "xp": 1, "blanks": {
    "o1": word(["1 2 3 4", "1 2 3 4 ", "1, 2, 3, 4"], "output", "10rem", "1 2 3 4"),
    "o2": word(["5 3 1", "5 3 1 ", "5, 3, 1"], "output", "10rem", "5 3 1")}}
cd = "number = 5\n\nwhile number >= 1:\n    print(number)\n    number = number - 1\n"
E["cd-count"] = {"type": "code", "xp": 2, "minLines": 6,
    "starter": "number = ____________________\n\nwhile ____________________:\n    print(number)\n    number = ____________________\n",
    "cases": [{"name": "5 down to 1", "expected": run(cd)}],
    "check": WHILE + "assert __source__.count('print(') == 1, 'Keep the single print(number) and let the loop repeat it.'\nassert number == 0, 'Subtract 1 from number on every pass so that number >= 1 becomes False.'\n",
    "answer": b64(cd)}

# ---- E. Diagnose loop bugs
E["ce-parts"] = {"type": "table", "xp": 1, "blanks": {
    "p1": word(INIT + ["initialization"], "part", "9rem", "initialize"),
    "p2": word(TEST + ["testing"], "part", "9rem", "test"),
    "p3": word(UPDATE + ["updating"], "part", "9rem", "update")}}
E["ce-repairs"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 3, "placeholder": "Describe a repair for each of the three programs.", "answer": b64(
    "Assign `count` before the loop. Use `count <= 5` so that 5 is included. Change `count` on every pass through the body.")}
E["ce-line"] = {"type": "table", "xp": 1, "blanks": {
    "line": word(["while n <= 10:", "while n <= 10", "n <= 10", "while n < 11:", "while n < 11", "n < 11"], "corrected line", "12rem", "while n <= 10:")}}
E["ce-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why does the corrected line include 10?", "answer": b64(
    "The value 10 must make the condition true because 10 belongs in the required output. On the next test, 11 makes the condition false.")}

# ---- F. Stop on a blank line
cf = "count = 0\ntext = input('Text, or press Enter to finish: ')\n\nwhile text != '':\n    count = count + 1\n    text = input('Text, or press Enter to finish: ')\n\nprint('Lines:', count)\n"
E["cf"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "count = 0\ntext = input('Text, or press Enter to finish: ')\n\nwhile ______________________________:\n    count = __________________________\n    text = ___________________________\n\nprint('Lines:', count)\n",
    "cases": [case("three lines, then blank", ["one", "two", "three", ""], cf), case("blank at once", [""], cf), case("one line, then blank", ["hello", ""], cf)],
    "check": WHILE,
    "answer": b64(cf),
    "answerNote": "The first input initializes text; the input inside the body updates it."}
E["cf-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why is a blank line a suitable stopping value?", "answer": b64(
    "A blank line is suitable because the program is counting nonblank lines, so the blank value is not valid data.")}

# ---- G. Choose the controlling condition
E["cg"] = {"type": "table", "xp": 1, "blanks": {
    "c1": word(["number <= limit", "n <= limit", "count <= limit", "i <= limit", "number < limit + 1"], "condition", "11rem", "number <= limit"),
    "u1": word(["number", "n", "count", "i", "the counter"], "variable", "7rem", "number"),
    "c2": word(["balance < target", "target > balance"], "condition", "11rem", "balance < target"),
    "u2": word(["balance"], "variable", "7rem", "balance"),
    "c3": word(["text != ''", 'text != ""', "text != ''", "text"], "condition", "11rem", "text != ''"),
    "u3": word(["text"], "variable", "7rem", "text")}}
cg = "number = 1\nmatches = 0\n\nwhile number <= 20:\n    if number % 3 == 0:\n        matches = matches + 1\n    number = number + 1\n\nprint('Matches:', matches)\n"
E["cg-code"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "number = 1\nmatches = 0\n\n# Write the loop here.\n\nprint('Matches:', matches)\n",
    "cases": [{"name": "1 through 20", "expected": run(cg)}],
    "check": WHILE + "assert '% 3' in __source__ or '%3' in __source__, 'Use number % 3 to test whether a number is divisible by 3.'\nassert number == 21, 'Add 1 to number on every pass so the loop stops after 20.'\n",
    "answer": b64(cg),
    "answerNote": "The counter matches changes only when the test is true. The loop-control variable number changes on every pass."}

# ---- H. Sum even numbers
ch = "limit = int(input('Limit: '))\nnumber = 2\ntotal = 0\n\nwhile number <= limit:\n    total = total + number\n    number = number + 2\n\nprint('Total:', total)\n"
E["ch"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "limit = int(input('Limit: '))\nnumber = 2\ntotal = 0\n\n# Write the loop here.\n\nprint('Total:', total)\n",
    "cases": [case("limit = 10", ["10"], ch), case("limit = 1", ["1"], ch), case("limit = 7", ["7"], ch), case("limit = 0", ["0"], ch)],
    "check": WHILE,
    "answer": b64(ch),
    "answerNote": "The update skips directly to the next even integer. With limit = 1, the first test is false and the initialized total remains 0."}

# ---- I. Average entered values
ci = ("total = 0.0\ncount = 0\ntext = input('Value, or press Enter to finish: ')\n\n"
      "while text != '':\n    total = total + float(text)\n    count = count + 1\n    text = input('Value, or press Enter to finish: ')\n\n"
      "average = total / count\nprint(f'Average: {average:.2f}')\n")
E["ci"] = {"type": "code", "xp": 5, "minLines": 11,
    "starter": "total = 0.0\ncount = 0\ntext = input('Value, or press Enter to finish: ')\n\n# Write the loop and final calculation here.\n",
    "cases": [case("4, 7.5, 2, blank", ["4", "7.5", "2", ""], ci), case("8, blank", ["8", ""], ci), case("1, 2, 3, 4, blank", ["1", "2", "3", "4", ""], ci)],
    "check": WHILE + "assert ':.2f' in __source__, 'Show the average to two decimal places with :.2f in the f-string.'\n",
    "answer": b64(ci),
    "answerNote": "The total accumulates the values and the counter records how many values were entered. The promise of at least one value means count is not zero when the division runs."}

# ---- J. Convert a sequence of prices
cj = ("CAD_PER_USD = 1.36\ncount = 0\ntext = input('USD, or press Enter to finish: ')\n\n"
      "while text != '':\n    usd = float(text)\n    cad = usd * CAD_PER_USD\n    print(f'CAD: ${cad:.2f}')\n    count = count + 1\n    text = input('USD, or press Enter to finish: ')\n\n"
      "print('Converted:', count)\n")
E["cj"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": "CAD_PER_USD = 1.36\ncount = 0\ntext = input('USD, or press Enter to finish: ')\n\n# Write the loop here.\n\nprint('Converted:', count)\n",
    "cases": [case("10, 0, blank", ["10", "0", ""], cj), case("blank at once", [""], cj), case("2.5, 19.99, 100, blank", ["2.5", "19.99", "100", ""], cj)],
    "check": WHILE + "assert __source__.count('CAD_PER_USD') >= 2, 'Multiply by the constant CAD_PER_USD instead of writing 1.36 again.'\nassert ':.2f' in __source__, 'Show each amount to two decimal places with :.2f in the f-string.'\n",
    "answer": b64(cj),
    "answerNote": "The loop tests the text before converting it. A blank string stops the loop, while the string '0' is valid data and converts to 0.0."}

# ---- K. Wait for a target price
ck = ("target = float(input('Target price: $'))\ncurrent = float(input('Current price: $'))\nupdates = 0\n\n"
      "while current < target:\n    current = float(input('Updated price: $'))\n    updates = updates + 1\n\n"
      "print(f'Target reached after {updates} updates.')\n")
E["ck"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "target = float(input('Target price: $'))\ncurrent = float(input('Current price: $'))\nupdates = 0\n\n# Write the loop here.\n\nprint(f'Target reached after {updates} updates.')\n",
    "cases": [case("target 50; prices 45, 48, 52", ["50", "45", "48", "52"], ck), case("target 50; price 50", ["50", "50"], ck),
              case("target 100; prices 20, 100", ["100", "20", "100"], ck)],
    "check": WHILE,
    "answer": b64(ck),
    "answerNote": "If the current price starts at the target, the loop runs zero times. The condition uses <, not <=, because a price equal to the target has reached it."}

# ---- L. Model radioactive decay
cl = "HALF_LIFE = 6\namount = 80.0\nhour = 0\n\nwhile hour < 24:\n    amount = amount * 0.5 ** (1 / HALF_LIFE)\n    hour = hour + 1\n    if hour % 6 == 0:\n        print(f'Hour {hour}: {amount:.2f} mg')\n"
E["cl"] = {"type": "code", "xp": 10, "minLines": 10,
    "starter": "HALF_LIFE = 6\namount = 80.0\nhour = 0\n\n# Write the loop here.\n",
    "cases": [{"name": "24 hours", "expected": run(cl)}],
    "check": WHILE + ("assert '0.5 **' in __source__ or '0.5**' in __source__, 'Multiply the amount by 0.5 ** (1 / HALF_LIFE) once per hour.'\n"
                      "assert hour == 24, 'Add 1 to hour on every pass and stop after 24 hourly updates.'\n"
                      "assert ':.2f' in __source__, 'Show the amount to two decimal places with :.2f in the f-string.'\n"),
    "answer": b64(cl),
    "answerNote": "The loop performs 24 hourly updates. The counter selects hours 6, 12, 18, and 24 for output."}

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-12",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 12 Workbook",
    "subtitle": "Problem solving with loops: the while loop",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-12/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
