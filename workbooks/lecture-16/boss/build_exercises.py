"""Build workbooks/lecture-16/boss/exercises.json: the Lecture 16 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_16_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions; the seeded random programs give
the same output in CPython and in the browser. Run from anywhere:

    python3 workbooks/lecture-16/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-16/boss
"""
import base64, json, subprocess, sys, pathlib

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

RE = "import re\n"
WHILE = RE + 'assert re.search(r"^\\s*while\\b", __code__, re.M), "Use a while loop; the number of lines is not known in advance."\n'
TWO_DP = 'assert re.search(r":[^}]*\\.2f\\}", __source__), "Print the result with two decimal places using :.2f."\n'
SEED = 'assert re.search(r"random\\.seed\\(\\s*seed\\s*\\)", __code__), "Seed the generator with random.seed(seed) before the first random call."\n'

E = {}

# ---------------------------------------------------------------- 1 Term Grade Average
grades = """grade = input()
total = 0.0
count = 0
while grade != '':
    if grade == 'A+' or grade == 'A':
        points = 4.0
    elif grade == 'A-':
        points = 3.7
    elif grade == 'B+':
        points = 3.3
    elif grade == 'B':
        points = 3.0
    elif grade == 'B-':
        points = 2.7
    elif grade == 'C+':
        points = 2.3
    elif grade == 'C':
        points = 2.0
    elif grade == 'C-':
        points = 1.7
    elif grade == 'D+':
        points = 1.3
    elif grade == 'D':
        points = 1.0
    else:
        points = 0.0
    total = total + points
    count = count + 1
    grade = input()
if count == 0:
    print('No grades entered.')
else:
    print(f'Grade point average: {total / count:.2f}')
"""
E["grades"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 20,
    "starter": "grade = input()\ntotal = 0.0\ncount = 0\n# Convert and accumulate grades until the blank sentinel.\n",
    "cases": input_cases(grades,
        ("Typed A, C+, B, blank", ["A", "C+", "B", ""]),
        ("Typed blank", [""]),
        ("Typed F, blank", ["F", ""]),
        ("Typed A+, A-, B+, B-, C-, D+, D, blank", ["A+", "A-", "B+", "B-", "C-", "D+", "D", ""]),
        ("Typed C, C, C, blank", ["C", "C", "C", ""]),
        ("Typed A+, F, blank", ["A+", "F", ""])),
    "check": WHILE + TWO_DP + '''assert "import" not in __code__, "No import is needed; a while loop and if statements are enough."
assert re.search(r"grade\\s*!=\\s*''|''\\s*!=\\s*grade|grade\\s*!=\\s*\\"\\"|\\"\\"\\s*!=\\s*grade|grade\\s*==\\s*''|len\\(grade\\)", __source__), "Stop the loop at the blank line: while grade != ''."
assert "elif" in __code__, "Convert each grade with an if, elif, else chain."
assert re.search(r"count\\s*==\\s*0|count\\s*>\\s*0|count\\s*<\\s*1|count\\s*>=\\s*1", __code__), "Test whether count is 0 before dividing."
''',
    "hints": [
        "The loop condition is `while grade != ''`. Inside it, turn `grade` into a number of points, add the points to `total`, add 1 to `count`, and read the next `grade` as the last statement of the body.",
        "Convert with a chain that starts `if grade == 'A+' or grade == 'A':` and sets `points = 4.0`, then one `elif` per remaining grade down to `D`, and an `else` for `F` that sets `points = 0.0`.",
        "After the loop, `if count == 0:` print `No grades entered.`; otherwise print `f'Grade point average: {total / count:.2f}'`.",
    ],
    "answer": b64(grades),
    "answerNote": "Use one branch for each grade point value, add it to the total, and count the grade. Divide only when the count is positive."}
assert E["grades"]["cases"][0]["expected"] == "Grade point average: 3.10"
assert E["grades"]["cases"][1]["expected"] == "No grades entered."
assert E["grades"]["cases"][2]["expected"] == "Grade point average: 0.00"

# ---------------------------------------------------------------- 2 Campus Route Perimeter
perimeter = """import math
first_x = float(input())
first_y = float(input())
previous_x = first_x
previous_y = first_y
perimeter = 0.0
x_text = input()
while x_text != '':
    current_x = float(x_text)
    current_y = float(input())
    perimeter = perimeter + math.sqrt(
        (current_x - previous_x) ** 2 + (current_y - previous_y) ** 2
    )
    previous_x = current_x
    previous_y = current_y
    x_text = input()
perimeter = perimeter + math.sqrt(
    (first_x - previous_x) ** 2 + (first_y - previous_y) ** 2
)
print(f'Route perimeter: {perimeter:.2f}')
"""
E["perimeter"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 14,
    "starter": "import math\nfirst_x = float(input())\nfirst_y = float(input())\n# Remember both the first and previous points.\n",
    "cases": input_cases(perimeter,
        ("Typed 0, 0, 3, 0, 3, 4, blank", ["0", "0", "3", "0", "3", "4", ""]),
        ("Typed 1, 1, 4, 1, blank", ["1", "1", "4", "1", ""]),
        ("Typed 0, 0, 1, 0, 1, 1, 0, 1, blank", ["0", "0", "1", "0", "1", "1", "0", "1", ""]),
        ("Typed 2.5, -1, -0.5, 3, blank", ["2.5", "-1", "-0.5", "3", ""]),
        ("Typed 0, 0, 0, 5, 12, 5, 12, 0, 6, -8, blank", ["0", "0", "0", "5", "12", "5", "12", "0", "6", "-8", ""])),
    "check": WHILE + TWO_DP + '''assert "math.sqrt(" in __code__, "Compute each segment length with math.sqrt()."
assert "previous_x" in __code__ and "previous_y" in __code__, "Keep the previous point in previous_x and previous_y."
assert re.search(r"first_x\\s*-|-\\s*first_x", __code__), "After the loop, add the segment from the last point back to first_x, first_y."
''',
    "hints": [
        "Before the loop, copy the first point into `previous_x` and `previous_y`, set `perimeter = 0.0`, and read the next `x` as text: `x_text = input()`.",
        "Loop `while x_text != ''`. Inside, convert `current_x = float(x_text)`, read `current_y = float(input())`, and add `math.sqrt((current_x - previous_x) ** 2 + (current_y - previous_y) ** 2)` to `perimeter`.",
        "Still inside the loop, make the current point the previous one and read the next `x_text` as the last statement.",
        "After the loop, add the segment from `(previous_x, previous_y)` back to `(first_x, first_y)`, then print `f'Route perimeter: {perimeter:.2f}'`.",
    ],
    "answer": b64(perimeter),
    "answerNote": "Add each new segment from the previous point, update the previous point, then close the route after the loop."}
assert E["perimeter"]["cases"][0]["expected"] == "Route perimeter: 12.00"
assert E["perimeter"]["cases"][1]["expected"] == "Route perimeter: 6.00"
assert E["perimeter"]["cases"][2]["expected"] == "Route perimeter: 4.00"

# ---------------------------------------------------------------- 3 Running Record Board
records = """import random
seed = int(input())
n = int(input())
random.seed(seed)
largest = random.randint(1, 100)
updates = 0
print(largest)
for item in range(1, n):
    value = random.randint(1, 100)
    if value > largest:
        largest = value
        updates = updates + 1
        print(value, 'new record')
    else:
        print(value)
print('Maximum:', largest)
print('Updates:', updates)
"""
E["records"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 12,
    "starter": "import random\nseed = int(input())\nn = int(input())\nrandom.seed(seed)\n# Generate the first value before the remaining-value loop.\n",
    "cases": input_cases(records,
        ("Typed 5, 6", ["5", "6"]),
        ("Typed 2, 1", ["2", "1"]),
        ("Typed 1, 10", ["1", "10"]),
        ("Typed 42, 3", ["42", "3"]),
        ("Typed 7, 20", ["7", "20"])),
    "check": RE + SEED + '''assert re.search(r"^\\s*for\\b", __code__, re.M), "Use a for loop for the remaining n - 1 values."
assert len(re.findall(r"random\\.randint\\(\\s*1\\s*,\\s*100\\s*\\)", __code__)) == 2, "Call random.randint(1, 100) in exactly two places: once for the first value and once inside the loop."
assert not re.search(r"largest\\s*=\\s*0\\b|largest\\s*=\\s*-", __code__), "Initialize the running maximum from the first generated value, not from 0."
''',
    "hints": [
        "Generate the first value with `largest = random.randint(1, 100)`, set `updates = 0`, and print `largest` on its own line before the loop.",
        "Loop `for item in range(1, n)` so the body runs `n - 1` times. Each pass generates `value = random.randint(1, 100)`.",
        "If `value > largest`, store it as the new `largest`, add 1 to `updates`, and print `value, 'new record'`; otherwise print `value` alone.",
        "After the loop, print `'Maximum:', largest` and `'Updates:', updates`.",
    ],
    "answer": b64(records),
    "answerNote": "The first generated number is a real starting maximum. Increment the update counter only when a later number beats it."}
assert E["records"]["cases"][0]["expected"] == "80\n33\n95 new record\n46\n89\n95\nMaximum: 95\nUpdates: 1"
assert E["records"]["cases"][1]["expected"] == "8\nMaximum: 8\nUpdates: 0"

# ---------------------------------------------------------------- 4 Three-in-a-Row Trials
streaks = """import random
seed = int(input())
trials = int(input())
random.seed(seed)
total_flips = 0
for trial in range(trials):
    previous = ''
    run_length = 0
    flips = 0
    outcomes = ''
    while run_length < 3:
        outcome = random.choice('HT')
        outcomes = outcomes + outcome
        flips = flips + 1
        if outcome == previous:
            run_length = run_length + 1
        else:
            previous = outcome
            run_length = 1
    print(outcomes + ':', flips)
    total_flips = total_flips + flips
print(f'Average flips: {total_flips / trials:.2f}')
"""
E["streaks"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 16,
    "starter": "import random\nseed = int(input())\ntrials = int(input())\nrandom.seed(seed)\ntotal_flips = 0\n# Run one complete three-in-a-row experiment per trial.\n",
    "cases": input_cases(streaks,
        ("Typed 4, 2", ["4", "2"]),
        ("Typed 1, 1", ["1", "1"]),
        ("Typed 9, 5", ["9", "5"]),
        ("Typed 12, 3", ["12", "3"]),
        ("Typed 3, 10", ["3", "10"])),
    "check": RE + SEED + TWO_DP + '''assert re.search(r"^\\s*for\\b", __code__, re.M), "Use an outer for loop over the trials."
assert re.search(r"^\\s+while\\b", __code__, re.M), "Use an inner while loop that flips until the run length reaches 3."
assert re.search(r"random\\.choice\\(\\s*['\\"]HT['\\"]\\s*\\)", __source__), "Flip the coin with random.choice('HT')."
''',
    "hints": [
        "Each trial starts fresh: `previous = ''`, `run_length = 0`, `flips = 0`, and `outcomes = ''`. Put those four lines at the top of the `for trial in range(trials)` body.",
        "The inner loop is `while run_length < 3`. Each pass flips `outcome = random.choice('HT')`, appends it to `outcomes`, and adds 1 to `flips`.",
        "If `outcome == previous`, add 1 to `run_length`; otherwise set `previous = outcome` and `run_length = 1`.",
        "After the inner loop, print `outcomes + ':', flips` and add `flips` to `total_flips`. After the outer loop, print `f'Average flips: {total_flips / trials:.2f}'`.",
    ],
    "answer": b64(streaks),
    "answerNote": "Each inner loop resets its run state, extends or restarts the current run, and stops at length three. The outer loop accumulates the trial lengths."}
assert E["streaks"]["cases"][0]["expected"] == "HTHTTHHH: 8\nHTTHHTTHHTHHTTHHTTT: 19\nAverage flips: 13.50"
assert E["streaks"]["cases"][1]["expected"] == "HHTHTTT: 7\nAverage flips: 7.00"

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-16-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 16 Boss Problems",
    "short": "L16 bosses",
    "subtitle": "Common loop algorithms and random numbers",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-16/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
