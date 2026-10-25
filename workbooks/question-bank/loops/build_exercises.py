"""Build the Unit 4 (Loops) question bank: index.html and exercises.json.

Ten Part 2 style programming questions for term tests and the final exam,
in the boss problem layout, for the instructor to review. The page opens only
in instructor mode. Each question uses Lectures 12 to 16 and may use any
earlier lecture; programs are top-level code, as in the Unit 4 bosses. Sample
runs and expected outputs are produced by actually running the model
solutions; the seeded random program gives the same output in CPython and in
the browser. Run from anywhere:

    python3 workbooks/question-bank/loops/build_exercises.py
    python3 tools/check_workbook.py workbooks/question-bank/loops
"""
import base64, html, json, subprocess, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=()):
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
    p = subprocess.run([sys.executable, "-c", wrapper], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n")

def input_cases(solution, *runs):
    return [{"name": name, "inputs": list(inputs), "expected": run(solution, inputs)} for name, inputs in runs]

# A check runs after the student's program in a copy of its namespace and looks
# at the shape of the code. `_loop` asks for a kind of loop, `_for_range` for a
# for loop over range(...), `_nested` for one loop inside another. `_plain`
# rules out the tools from later units (lists, split, join, sorted) and any
# import other than the ones allowed.
LOOP = '''import ast, re
_NODES = list(ast.walk(ast.parse(__source__)))
_KIND = {"while": ast.While, "for": ast.For}
def _loop(kind, message):
    assert any(isinstance(n, _KIND[kind]) for n in _NODES), message
def _for_range(message):
    assert any(isinstance(n, ast.For) and isinstance(n.iter, ast.Call) and isinstance(n.iter.func, ast.Name)
               and n.iter.func.id == "range" for n in _NODES), message
def _nested(outer, inner, message):
    assert any(isinstance(n, _KIND[outer]) and any(isinstance(m, _KIND[inner]) for b in n.body for m in ast.walk(b))
               for n in _NODES), message
def _called(name):
    for n in _NODES:
        if isinstance(n, ast.Call):
            f = n.func
            if (f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "") == name:
                return True
    return False
def _plain(allowed=()):
    assert not any(isinstance(n, (ast.List, ast.ListComp, ast.Dict, ast.DictComp, ast.Set, ast.SetComp)) for n in _NODES), \\
        "Solve it without lists, dictionaries or sets. Keep a running total or a best-so-far value instead."
    for _name in ("split", "join", "list", "sorted", "reversed", "count", "replace"):
        assert not _called(_name), "Do not use " + _name + "() here. Work through the values one at a time with a loop."
    for n in _NODES:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            _mods = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module]
            assert all(m in allowed for m in _mods), "No import is needed here" + (", except import " + allowed[0] if allowed else "") + "."
def _no_repeat():
    for n in _NODES:
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult):
            assert not any(isinstance(s, ast.Constant) and isinstance(s.value, str) for s in (n.left, n.right)), \\
                "Build each row one character at a time inside the inner loop, not with * on a string."
'''

PLAIN_RULE = "No lists, <code>split()</code>, <code>join()</code> or <code>count()</code>; no import is needed."

E = {}   # exercise specs, by id
Q = []   # page sections, in order

def emoji(rating):
    return "👹" if rating < 3 else "👾" if rating == 3 else "🐉" if rating < 5 else "💀"

def question(qid, title, toc, lectures, rating, names, statement, reading, examples, constraints, rules, rubric, mistakes,
             solution, starter, cases, check, hints, note, allowed=()):
    """Record one question: its spec for the grader and its section for the page.
    `names` labels the typed values in the examples; a name starting with * takes
    all the remaining lines. `examples` is a list of (typed lines, explanation)
    pairs and must match the first cases, in order."""
    E[qid] = {"type": "code", "xp": 25, "boss": emoji(rating), "minLines": 20, "starter": starter, "cases": cases,
              "check": LOOP + check + f"_plain({allowed!r})\n", "hints": hints, "answer": b64(solution), "answerNote": note}
    for (inputs, _), case in zip(examples, cases):
        assert case["inputs"] == inputs, (qid, inputs)
    if not allowed:
        rules = rules + [PLAIN_RULE]
    Q.append(dict(qid=qid, title=title, toc=toc, lectures=lectures, rating=rating, names=names, statement=statement,
                  reading=reading, examples=examples, cases=cases[len(examples):],
                  constraints=constraints, rules=rules, rubric=rubric, mistakes=mistakes, solution=solution))

# ---------------------------------------------------------------- Bell Island ferry
ferry = """CAPACITY = 150

crossings = int(input())
total = 0
busiest = 0
busiest_count = -1
full = 0
for crossing in range(1, crossings + 1):
    passengers = int(input())
    total = total + passengers
    if passengers > busiest_count:
        busiest = crossing
        busiest_count = passengers
    if passengers == CAPACITY:
        full = full + 1
print(f'Passengers: {total}')
print(f'Average per crossing: {total / crossings:.1f}')
print(f'Busiest crossing: {busiest} with {busiest_count}')
print(f'Full crossings: {full}')
"""
question("ferry", "Bell Island ferry", "Bell Island ferry", "Lecture 14; also 8 to 11", 2, ["crossings", "*passengers"],
    "<p>The ferry between Portugal Cove and Bell Island carries at most 150 passengers. Given the number of crossings in a day "
    "and the number of passengers on each crossing, print the total number of passengers, the average per crossing to 1 decimal place, "
    "the busiest crossing and how many crossings were full.</p>"
    "<p>Crossings are numbered from 1. When two crossings tie for the most passengers, report the earlier one.</p>",
    "Read <code>crossings</code> with <code>int(input())</code>, then one passenger count per crossing, and print four lines.",
    [(["5", "120", "150", "98", "150", "143"], "661 passengers over 5 crossings is 132.2 each. Crossings 2 and 4 both carried 150; crossing 2 came first."),
     (["1", "0"], "One empty crossing: the total and the average are 0, and crossing 1 is the busiest with 0.")],
    ["<code>1 &lt;= crossings &lt;= 30</code>", "<code>0 &lt;= passengers &lt;= 150</code> on every crossing"],
    ["Keep the capacity in the constant <code>CAPACITY = 150</code>.",
     "Read the passenger counts inside a <code>for</code> loop over <code>range(...)</code>, one count per pass."],
    [("<code>for</code> loop over <code>range</code> runs exactly <code>crossings</code> times and reads one count per pass", 3),
     ("Running total and average with <code>:.1f</code>", 2),
     ("Busiest crossing: best-so-far count and its crossing number, earlier crossing kept on a tie", 3),
     ("Full crossings counted against <code>CAPACITY</code>; output matches the examples", 2)],
    "Starting the best-so-far count at 150 or at the first count without reading it in the loop. Using <code>&gt;=</code>, which reports the later of two tied crossings. "
    "Numbering crossings from 0. Dividing by a counter that was never increased.",
    ferry,
    "CAPACITY = 150\n\ncrossings = int(input())\n# Read one passenger count per crossing.\n",
    input_cases(ferry, ("Example 1: 5 crossings", ["5", "120", "150", "98", "150", "143"]), ("Example 2: one empty crossing", ["1", "0"]),
                ("Typed 4 rising counts", ["4", "30", "60", "90", "120"]), ("Typed 3 full crossings", ["3", "150", "150", "150"]),
                ("Typed 6 crossings", ["6", "75", "140", "149", "150", "12", "150"]), ("Typed a busy first crossing", ["3", "149", "20", "148"])),
    '''assert globals().get("CAPACITY") == 150, "Define the constant CAPACITY = 150 and compare with it."
_for_range("Read the counts inside a for loop over range(...), one count per crossing.")
''',
    ["Start <code>total</code> and <code>full</code> at 0 before the loop, and the best-so-far count below any real count, such as -1.",
     "Loop with <code>for crossing in range(1, crossings + 1):</code> so <code>crossing</code> is already the crossing number.",
     "Inside the loop, read the count, add it to the total, and replace the best only when the new count is strictly larger."],
    "The best-so-far starts at -1 so the first crossing always replaces it. Reading the first count before the loop also works.")

# ---------------------------------------------------------------- Step challenge
steps = """goal = int(input())
day = 0
met = 0
line = input()
while line != '':
    day = day + 1
    count = int(line)
    if count >= goal:
        print(f'Day {day}: goal met')
        met = met + 1
    else:
        print(f'Day {day}: {goal - count} short')
    line = input()
if day == 0:
    print('No days entered')
else:
    print(f'Goal met on {met} of {day} days')
"""
question("steps", "Step challenge", "Step challenge", "Lectures 12 and 13; also 8 to 11", 2, ["goal", "*counts"],
    "<p>The Department of Computer Science runs a step challenge. Given a daily step goal and then the step count for each day, "
    "print one line per day: <code>goal met</code> when the count reaches the goal, otherwise how many steps short it was. "
    "A blank line ends the days. Then print on how many days the goal was met.</p>"
    "<p>When no days are entered, print <code>No days entered</code> instead of the summary.</p>",
    "Read <code>goal</code> with <code>int(input())</code>, then one count per line until a blank line.",
    [(["8000", "9500", "7200", "8000", ""], "Day 2 is 800 short of 8000. Day 3 is exactly 8000, which counts as met."),
     (["10000", ""], "The first count is a blank line, so there are no days.")],
    ["<code>1 &lt;= goal &lt;= 50000</code>", "<code>0 &lt;= count &lt;= 100000</code> on each day", "The last line is blank."],
    ["Read the counts with a <code>while</code> loop that stops at the blank line (a sentinel loop)."],
    [("Sentinel loop: reads before the loop and again at the end of the body, stops at the blank line", 3),
     ("Converts each count only after the blank-line test", 1),
     ("Correct day numbers and the met / short lines, with exactly the goal counting as met", 3),
     ("Counts the days met and prints the summary, or <code>No days entered</code>", 2),
     ("Output matches the examples", 1)],
    "Calling <code>int(input())</code> before testing for the blank line, which fails on the sentinel. Forgetting the read at the end of the loop body, "
    "so the loop never ends. Printing the shortfall as <code>count - goal</code>. Treating exactly the goal as short.",
    steps,
    "goal = int(input())\n# Read one count per line until a blank line.\n",
    input_cases(steps, ("Example 1: goal 8000", ["8000", "9500", "7200", "8000", ""]), ("Example 2: no days", ["10000", ""]),
                ("Typed goal 5000, 3 days", ["5000", "4999", "0", "12000", ""]), ("Typed goal 6000, 1 day", ["6000", "6000", ""]),
                ("Typed goal 7500, 4 days", ["7500", "7400", "7600", "7499", "7501", ""])),
    '''_loop("while", "Read the counts with a while loop that stops at the blank line.")
''',
    ["Read the first line before the loop, and test <code>line != ''</code> in the <code>while</code> header.",
     "Convert with <code>int(line)</code> inside the loop, after the test, and read the next line as the last step of the body.",
     "Keep two counters, one for the days and one for the days met; after the loop, test whether any days were read."],
    "A classic sentinel loop: the read before the loop and the read at the end of the body are the same statement.")

# ---------------------------------------------------------------- Digital root
digitroot = """number = int(input())
chain = str(number)
steps = 0
while number >= 10:
    total = 0
    while number > 0:
        total = total + number % 10
        number = number // 10
    number = total
    chain = chain + ' -> ' + str(number)
    steps = steps + 1
print(chain)
if steps == 1:
    print(f'Digital root: {number} after 1 step')
else:
    print(f'Digital root: {number} after {steps} steps')
"""
question("digitroot", "Digital root", "Digital root", "Lectures 12 and 15", 3, ["number"],
    "<p>The digital root of a whole number is found by adding up its digits, then adding up the digits of that sum, and so on, "
    "until one digit is left. Given a number, print every number in the chain separated by <code> -&gt; </code>, "
    "then the digital root and how many digit sums it took.</p>"
    "<p>A number that already has one digit is its own digital root after 0 steps. Write <code>1 step</code> but <code>2 steps</code>.</p>",
    "Read <code>number</code> with <code>int(input())</code> and print two lines.",
    [(["9875"], "9 + 8 + 7 + 5 = 29, then 2 + 9 = 11, then 1 + 1 = 2: three digit sums."),
     (["7"], "7 already has one digit, so the chain is just 7 and no sums are needed.")],
    ["<code>0 &lt;= number &lt;= 10<sup>15</sup></code>"],
    ["Find each digit sum with <code>%</code> and <code>//</code> in a <code>while</code> loop, not by indexing a string.",
     "Put that loop inside another <code>while</code> loop that repeats until one digit is left."],
    [("Outer <code>while</code> loop that repeats while the number has two or more digits", 2),
     ("Inner loop: <code>% 10</code> takes the last digit, <code>// 10</code> drops it, total starts at 0 for each sum", 3),
     ("The sum becomes the new number; the chain text grows with <code> -&gt; </code>", 2),
     ("Counts the sums and prints step or steps correctly", 2),
     ("Output matches the examples, including a one-digit number", 1)],
    "Resetting the digit total once, before the outer loop, so each sum adds to the last. Using <code>while number &gt; 10</code>, which stops at 10. "
    "Losing the original number because the inner loop reduced it to 0 before it was printed.",
    digitroot,
    "number = int(input())\nchain = str(number)\nsteps = 0\n# Add up the digits until one digit is left.\n",
    input_cases(digitroot, ("Example 1: 9875", ["9875"]), ("Example 2: 7", ["7"]), ("Typed 10", ["10"]), ("Typed 19", ["19"]),
                ("Typed 0", ["0"]), ("Typed 999999999999", ["999999999999"]), ("Typed 1000000", ["1000000"]), ("Typed 38", ["38"])),
    '''_nested("while", "while", "Put the digit-sum while loop inside a while loop that repeats until one digit is left.")
assert "%" in __code__ and "//" in __code__, "Take the last digit with % 10 and drop it with // 10."
assert not any(isinstance(n, ast.Subscript) for n in _NODES), "Find the digits with % and //, not by indexing a string."
''',
    ["The outer loop runs <code>while number &gt;= 10</code>.",
     "Inside it, start <code>total = 0</code>, then loop <code>while number &gt; 0</code>, adding <code>number % 10</code> and doing <code>number = number // 10</code>.",
     "After the inner loop, set <code>number = total</code>, add <code>' -&gt; ' + str(number)</code> to the chain and count one step."],
    "The chain starts as the text of the original number, so it is printed correctly even after the inner loop changes number.")

# ---------------------------------------------------------------- Freezing streak
coldstreak = """day = 0
freezing = 0
run = 0
longest = 0
start = 0
line = input()
while line != '':
    day = day + 1
    high = float(line)
    if high < 0:
        freezing = freezing + 1
        run = run + 1
        if run > longest:
            longest = run
            start = day - run + 1
    else:
        run = 0
    line = input()
print(f'Days: {day}')
print(f'Freezing days: {freezing}')
if longest == 0:
    print('No freezing streak')
elif longest == 1:
    print(f'Longest freezing streak: 1 day, day {start}')
else:
    print(f'Longest freezing streak: {longest} days, day {start} to day {start + longest - 1}')
"""
question("coldstreak", "Freezing streak", "Freezing streak", "Lectures 13 and 16; also 8 to 11", 3, ["*highs"],
    "<p>Given the daily high temperature in St. John's for a run of days, one per line and ended by a blank line, print the number of days, "
    "the number of freezing days (a high below 0), and the longest streak of freezing days in a row with its first and last day.</p>"
    "<p>Days are numbered from 1. When two streaks are equally long, report the earlier one. A high of exactly 0 is not freezing. "
    "Write <code>1 day, day 3</code> for a one-day streak and <code>No freezing streak</code> when there is none.</p>",
    "Read one high per line with <code>input()</code> until a blank line, and print three lines.",
    [(["-3.5", "-1", "2", "-0.5", "-4", "-7", "-2", "1", ""], "Days 1 and 2 freeze, day 3 thaws, then days 4 to 7 freeze: a streak of 4."),
     (["1.5", "0", "3", ""], "No high is below 0; the 0 on day 2 does not count.")],
    ["<code>0 &lt;= days &lt;= 60</code>", "<code>-30 &lt;= high &lt;= 30</code>, with at most 1 decimal place", "The last line is blank."],
    ["Read the highs with a <code>while</code> loop that stops at the blank line.",
     "Track the current streak and the longest one with counters; do not store the highs."],
    [("Sentinel loop that reads every high and stops at the blank line", 2),
     ("Counts the days and the freezing days, with 0 not freezing", 2),
     ("Current streak grows on a freezing day and resets to 0 on any other day", 2),
     ("Longest streak and its first day updated only on a strictly longer streak", 2),
     ("Correct first and last day; prints the three cases of the last line", 2)],
    "Comparing the streak with the longest only when a thaw ends it, which misses a streak that runs to the last day. Using <code>&gt;=</code>, which reports the later of two equal streaks. "
    "Saving the day number at the end of the streak as its first day. Testing <code>high &lt;= 0</code>.",
    coldstreak,
    "day = 0\nline = input()\n# Read one high per line until a blank line.\n",
    input_cases(coldstreak, ("Example 1: 8 days", ["-3.5", "-1", "2", "-0.5", "-4", "-7", "-2", "1", ""]), ("Example 2: no freezing", ["1.5", "0", "3", ""]),
                ("Typed no days", [""]), ("Typed one-day streaks", ["-1", "2", "-3", ""]), ("Typed two equal streaks", ["-2", "-2", "5", "-1", "-1", ""]),
                ("Typed a streak to the end", ["4", "-10", "-12", "-8", ""]), ("Typed 0 between frosts", ["-1", "0", "-1", "-1", ""])),
    '''_loop("while", "Read the highs with a while loop that stops at the blank line.")
''',
    ["Keep <code>run</code>, the length of the streak that ends today, and <code>longest</code>, the best streak so far.",
     "On a freezing day add 1 to <code>run</code>; on any other day set it back to 0.",
     "Right after <code>run</code> grows, test <code>run &gt; longest</code>; when it is, save it and its first day, <code>day - run + 1</code>."],
    "Testing the streak every time it grows handles a streak that is still going on the last day.")

# ---------------------------------------------------------------- Hooked rug pattern
rug = """size = input()
while not (size.isdigit() and 3 <= int(size) <= 15 and int(size) % 2 == 1):
    print('Size must be an odd number from 3 to 15.')
    size = input()
n = int(size)
for row in range(n):
    line = ''
    for col in range(n):
        if row == 0 or row == n - 1 or col == 0 or col == n - 1:
            line = line + '#'
        elif row == n // 2 and col == n // 2:
            line = line + 'O'
        elif row == col or row + col == n - 1:
            line = line + 'X'
        else:
            line = line + '.'
    print(line)
"""
question("rug", "Hooked rug pattern", "Hooked rug", "Lectures 13 to 15; also 8 to 11", 3, ["*size"],
    "<p>A hooked rug pattern is drawn on a square grid. Given its size <code>n</code>, print <code>n</code> rows of <code>n</code> characters: "
    "<code>#</code> on the border, <code>O</code> in the very centre, <code>X</code> on the two diagonals inside the border, and <code>.</code> everywhere else.</p>"
    "<p>The size must be an odd whole number from 3 to 15. Until it is, print <code>Size must be an odd number from 3 to 15.</code> and read it again.</p>",
    "Read <code>size</code> with <code>input()</code>, again after each invalid value, and print the pattern.",
    [(["7"], "Rows and columns 0 and 6 are the border. Row 3, column 3 is the centre. The rest of the two diagonals are X."),
     (["4", "twenty", "17", "5"], "4 is even, twenty is not a number and 17 is too big, so the size is asked for three more times.")],
    ["<code>size</code> is any text; a valid size has only digits.", "At most 10 invalid sizes are typed."],
    ["Validate the size with a <code>while</code> loop.",
     "Draw the grid with a <code>for</code> loop over the columns inside a <code>for</code> loop over the rows.",
     "Build each row one character at a time; do not use <code>*</code> on a string."],
    [("Validation loop: tests digits before <code>int()</code>, odd and in range, prints the message and reads again", 3),
     ("Nested <code>for</code> loops over <code>range(n)</code> for rows and columns", 2),
     ("Border, centre and both diagonals tested in the right order", 3),
     ("Builds one row per pass of the outer loop and prints it once", 1),
     ("Output matches the examples", 1)],
    "Calling <code>int(size)</code> before checking <code>isdigit()</code>, which crashes on <code>twenty</code>. Testing the diagonals before the border or the centre, "
    "so the corners or the centre come out as X. Using <code>row + col == n</code> for the second diagonal. Printing inside the inner loop.",
    rug,
    "size = input()\n# Ask again until the size is valid, then draw the rug.\n",
    input_cases(rug, ("Example 1: 7", ["7"]), ("Example 2: three bad sizes", ["4", "twenty", "17", "5"]), ("Typed 3", ["3"]),
                ("Typed 15", ["15"]), ("Typed -5, 0, 9", ["-5", "0", "9"]), ("Typed 1, 2.5, 11", ["1", "2.5", "11"])),
    '''_loop("while", "Validate the size with a while loop that asks again.")
_nested("for", "for", "Draw the rug with a for loop over the columns inside a for loop over the rows.")
_no_repeat()
''',
    ["Test <code>size.isdigit()</code> first and combine the tests with <code>and</code>, so <code>int(size)</code> only runs on digits.",
     "For each row, start <code>line = ''</code>, loop over the columns adding one character, then print the line after the inner loop.",
     "Test the border first, then the centre <code>n // 2</code>, then the diagonals <code>row == col</code> and <code>row + col == n - 1</code>."],
    "The order of the if/elif chain is what keeps the corners as # and the centre as O.")

# ---------------------------------------------------------------- Hailstone chains
collatz = """low = int(input())
high = int(input())
best = low
best_steps = -1
peak = 0
peak_start = low
for start in range(low, high + 1):
    n = start
    steps = 0
    while n != 1:
        if n > peak:
            peak = n
            peak_start = start
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        steps = steps + 1
    if n > peak:
        peak = n
        peak_start = start
    if steps > best_steps:
        best = start
        best_steps = steps
print(f'Longest chain: {best} takes {best_steps} steps')
print(f'Highest value: {peak}, reached from {peak_start}')
"""
question("collatz", "Hailstone chains", "Hailstone chains", "Lectures 14 to 16; also 8 to 11", 4, ["low", "high"],
    "<p>A hailstone chain starts at a whole number. While the number is not 1, an even number is halved and an odd number <code>n</code> becomes "
    "<code>3n + 1</code>; each change is one step. The chain from 6 is 6, 3, 10, 5, 16, 8, 4, 2, 1: 8 steps, and its highest value is 16.</p>"
    "<p>Given <code>low</code> and <code>high</code>, look at the chain of every start from <code>low</code> to <code>high</code>, inclusive. "
    "Print the start whose chain takes the most steps, and the highest value any chain reaches with the first start that reaches it. "
    "On a tie, report the smaller start. The start itself counts as a value of its chain.</p>",
    "Read <code>low</code> and then <code>high</code> with <code>int(input())</code>, and print two lines.",
    [(["1", "10"], "9 takes 19 steps, more than any other start up to 10. Both 7 and 9 climb to 52; 7 is the smaller start."),
     (["27", "27"], "Only one start: 27 takes 111 steps and climbs as high as 9232.")],
    ["<code>1 &lt;= low &lt;= high &lt;= 5000</code>", "<code>high - low &lt;= 1000</code>"],
    ["Use a <code>for</code> loop over <code>range(...)</code> for the starts and a <code>while</code> loop inside it for each chain."],
    [("<code>for</code> loop covers <code>low</code> to <code>high</code> inclusive; <code>while</code> loop inside it runs one chain", 3),
     ("Halve or <code>3n + 1</code> rule correct, with <code>//</code> so the values stay whole; steps counted, reset for each start", 2),
     ("Longest chain tracked with its start; the smaller start kept on a tie", 2),
     ("Highest value tracked over every value, including the start, with the first start that reaches it", 2),
     ("Output matches the examples", 1)],
    "Changing the loop variable itself instead of a copy, so the starts skip around. <code>range(low, high)</code>, which leaves out <code>high</code>. "
    "Using <code>n / 2</code>, which gives floats such as <code>52.0</code>. Not resetting <code>steps</code> for each start.",
    collatz,
    "low = int(input())\nhigh = int(input())\n# Follow the chain of every start from low to high.\n",
    input_cases(collatz, ("Example 1: 1 to 10", ["1", "10"]), ("Example 2: 27 only", ["27", "27"]), ("Typed 1 to 1", ["1", "1"]),
                ("Typed 2 to 5", ["2", "5"]), ("Typed 100 to 200", ["100", "200"]), ("Typed 4000 to 5000", ["4000", "5000"]),
                ("Typed 6 to 8", ["6", "8"]), ("Typed 12 to 13, a tie", ["12", "13"])),
    '''_for_range("Loop over the starts with a for loop over range(...).")
_nested("for", "while", "Follow each chain with a while loop inside the for loop over the starts.")
''',
    ["Copy the loop variable, <code>n = start</code>, and change only the copy in the <code>while n != 1</code> loop.",
     "Before each change, compare <code>n</code> with the highest value so far; after the loop, compare the final 1 as well.",
     "After the chain, compare its steps with the best so far using <code>&gt;</code>, so a later start never replaces an equal one."],
    "Checking the peak before each step means the start itself is counted. A single start of 1 has no steps, so the check after the loop catches it.")

# ---------------------------------------------------------------- Sentence statistics
words = """sentence = input()
count = 0
letters = 0
longest = ''
current = ''
for i in range(len(sentence)):
    if sentence[i] != ' ':
        current = current + sentence[i]
    elif current != '':
        count = count + 1
        letters = letters + len(current)
        if len(current) > len(longest):
            longest = current
        current = ''
if current != '':
    count = count + 1
    letters = letters + len(current)
    if len(current) > len(longest):
        longest = current
if count == 0:
    print('No words')
else:
    print(f'Words: {count}')
    print(f'Longest word: {longest} ({len(longest)} characters)')
    print(f'Average length: {letters / count:.1f}')
"""
question("words", "Sentence statistics", "Sentence statistics", "Lectures 14 and 16; also 6 and 7", 4, ["sentence"],
    "<p>Given a sentence, print how many words it has, its longest word with that word's length, and the average word length to 1 decimal place. "
    "A word is a run of characters other than spaces, so punctuation is part of a word. Words may be separated by more than one space, "
    "and the sentence may start or end with spaces.</p>"
    "<p>When two words are equally long, report the first. When there are no words, print <code>No words</code>.</p>",
    "Read <code>sentence</code> with <code>input()</code> and print three lines, or one.",
    [(["  The ferry  to Bell Island leaves at noon "], "8 words with 32 characters in all, so 4.0 on average. Island and leaves both have 6; Island comes first."),
     (["   "], "Only spaces, so there are no words.")],
    ["<code>0 &lt;= len(sentence) &lt;= 200</code>", "<code>sentence</code> has letters, digits, punctuation and spaces, but no tabs."],
    ["Go through the sentence one character at a time with <code>for i in range(len(sentence))</code>.",
     "Do not use <code>split()</code>, <code>strip()</code> or a list. Build the current word in a string."],
    [("<code>for</code> loop over the indexes; builds the current word one character at a time", 2),
     ("A word ends at a space only when the current word is not empty, so extra spaces do not count", 2),
     ("The last word, with no space after it, is counted after the loop", 2),
     ("Longest word kept with <code>&gt;</code> so the first of equal words stays; total length for the average", 2),
     ("Prints <code>No words</code> or the three lines with <code>:.1f</code>; output matches the examples", 2)],
    "Counting spaces plus one, which is wrong when there are extra spaces. Forgetting the last word. Counting the average as characters in the sentence "
    "divided by words, which includes the spaces. Dividing by 0 when there are no words.",
    words,
    "sentence = input()\n# Go through the sentence one character at a time.\n",
    input_cases(words, ("Example 1: the ferry", ["  The ferry  to Bell Island leaves at noon "]), ("Example 2: only spaces", ["   "]),
                ("Typed an empty line", [""]), ("Typed one word", ["Go"]), ("Typed punctuation", ["St. John's is foggy, again!"]),
                ("Typed equal lengths", ["a bb ccc bb ddd a"]), ("Typed Memorial University of Newfoundland", ["Memorial University of Newfoundland"])),
    '''_for_range("Go through the sentence with for i in range(len(sentence)).")
assert not _called("strip"), "Do not use strip(). Skip the extra spaces with the test inside the loop."
''',
    ["Keep the word being read in <code>current</code>. A character that is not a space is added to it.",
     "At a space, if <code>current</code> is not empty, a word has just ended: count it, add its length, compare it with the longest, and empty <code>current</code>.",
     "After the loop, <code>current</code> may still hold the last word; handle it the same way."],
    "The end-of-word code appears twice, once at a space and once after the loop; with functions from Unit 5 it would be one function.")

# ---------------------------------------------------------------- Guess my number
guess = """top = int(input())
low = 1
high = top
guesses = 0
while True:
    if low > high:
        print('Those answers do not add up.')
        break
    middle = (low + high) // 2
    guesses = guesses + 1
    print(f'Guess {guesses}: {middle}')
    answer = input().strip().lower()
    while answer != 'h' and answer != 'l' and answer != 'c':
        print('Type h, l or c.')
        answer = input().strip().lower()
    if answer == 'c':
        print(f'Got it on guess {guesses}.')
        break
    elif answer == 'h':
        low = middle + 1
    else:
        high = middle - 1
"""
question("guess", "Guess my number", "Guess my number", "Lectures 13 and 15; also 8 to 11", 4, ["top", "*answers"],
    "<p>The user thinks of a whole number from 1 to <code>top</code> and the program guesses it. Each guess is the middle of the numbers still possible, "
    "<code>(low + high) // 2</code>. After each guess the user types <code>h</code> if their number is higher, <code>l</code> if it is lower, "
    "or <code>c</code> if the guess is correct, in either case and with any spaces around it.</p>"
    "<p>Any other answer prints <code>Type h, l or c.</code> and is read again without a new guess. If the answers leave no number possible, "
    "print <code>Those answers do not add up.</code> and stop.</p>",
    "Read <code>top</code> with <code>int(input())</code>, then one answer after each guess.",
    [(["100", "h", "l", "x", "h", "c"], "50, then 75, then 62. x is not an answer, so the answer about 62 is read again. Higher than 62 and lower than 75 leaves 63 to 74, so the next guess is 68."),
     (["10", "l", "l", "l"], "Lower than 5, 2 and 1 leaves nothing from 1 to 10.")],
    ["<code>1 &lt;= top &lt;= 1000</code>", "The answers end as soon as the program stops."],
    ["Keep guessing in a <code>while</code> loop and leave it with <code>break</code>.",
     "Validate each answer with a <code>while</code> loop inside it."],
    [("Outer <code>while</code> loop with <code>break</code> on a correct guess and when no number is left", 3),
     ("Guess is <code>(low + high) // 2</code>; <code>h</code> and <code>l</code> move <code>low</code> or <code>high</code> past the guess", 3),
     ("Inner validation loop; answers are stripped and lower-cased; an invalid answer does not count as a guess", 2),
     ("Guess numbers and messages; output matches the examples", 2)],
    "Moving <code>low</code> to <code>middle</code> instead of <code>middle + 1</code>, which repeats the same guess forever. Counting an invalid answer as a guess. "
    "Testing <code>answer != 'h' or answer != 'l'</code>, which is always true. Never checking <code>low &gt; high</code>, so the program guesses outside the range.",
    guess,
    "top = int(input())\nlow = 1\nhigh = top\nguesses = 0\n# Guess the middle until the answer is c.\n",
    input_cases(guess, ("Example 1: 100 and a typo", ["100", "h", "l", "x", "h", "c"]), ("Example 2: inconsistent answers", ["10", "l", "l", "l"]),
                ("Typed 1 and c", ["1", "c"]), ("Typed 100, always higher", ["100", "H", " h", "h ", "H", "h", "h", "c"]),
                ("Typed 20 and two bad answers", ["20", "maybe", "", "C"]), ("Typed 1000, lower then higher", ["1000", "l", "h", "l", "h", "c"]),
                ("Typed 3, higher past the top", ["3", "h", "h"])),
    '''_loop("while", "Keep guessing in a while loop.")
assert "break" in __code__, "Leave the guessing loop with break when the guess is correct or no number is left."
_nested("while", "while", "Read the answer again in a while loop inside the guessing loop until it is h, l or c.")
''',
    ["Keep <code>low</code> and <code>high</code>, the smallest and largest numbers still possible; start them at 1 and <code>top</code>.",
     "At the top of <code>while True:</code>, stop with a message if <code>low &gt; high</code>; otherwise print the next guess and read an answer.",
     "Repeat the read <code>while answer != 'h' and answer != 'l' and answer != 'c'</code>, then <code>break</code> on c or move <code>low</code> to <code>middle + 1</code> or <code>high</code> to <code>middle - 1</code>."],
    "This is binary search: each answer halves the numbers left, so 100 needs at most 7 guesses.")

# ---------------------------------------------------------------- Longest mirror run
mirror = """text = input()
lower = text.lower()
best_start = 0
best_length = 0
for start in range(len(text)):
    for end in range(start + 2, len(text) + 1):
        left = start
        right = end - 1
        same = True
        while left < right:
            if lower[left] != lower[right]:
                same = False
                break
            left = left + 1
            right = right - 1
        if same and end - start > best_length:
            best_start = start
            best_length = end - start
if best_length == 0:
    print('No mirror run')
else:
    print(f'Longest mirror run: {text[best_start:best_start + best_length]}')
    print(f'Position {best_start}, length {best_length}')
"""
question("mirror", "Longest mirror run", "Longest mirror run", "Lectures 14 and 15; also 6 and 7", 5, ["text"],
    "<p>A mirror run is a part of a text, at least 2 characters long, that reads the same forwards and backwards. Capital and small letters count as the same, "
    "and spaces and punctuation are characters like any other. Given a text, print its longest mirror run as typed, and the position and length of that run.</p>"
    "<p>Positions count from 0, as indexes do. When two runs are equally long, report the one that starts first. "
    "When there is none, print <code>No mirror run</code>.</p>",
    "Read <code>text</code> with <code>input()</code> and print two lines, or one.",
    [(["Kayak on Quidi Vidi"], "Kayak reads the same both ways once case is ignored, and no longer run exists. It starts at position 0."),
     (["COMP 1001"], "1001 is the longest run, at position 5. The single characters do not count.")],
    ["<code>0 &lt;= len(text) &lt;= 60</code>"],
    ["Try every start and end with a <code>for</code> loop inside a <code>for</code> loop.",
     "Test each run by comparing characters from both ends inward in a loop, leaving it with <code>break</code> at the first mismatch.",
     "Do not reverse a string with a slice such as <code>[::-1]</code>; slices are fine for printing the answer."],
    [("Nested <code>for</code> loops cover every run of 2 or more characters, including the last character", 3),
     ("Inner loop compares from both ends inward, ignoring case, with <code>break</code> at a mismatch", 3),
     ("Best run kept with <code>&gt;</code> so the first of equal runs stays", 2),
     ("Prints the run as typed, its position and length, or <code>No mirror run</code>", 2)],
    "<code>range(start + 1, len(text))</code> for the end, which misses runs that finish on the last character. Comparing the lower-case copy but printing it, "
    "so the run is not shown as typed. Counting single characters as runs. A flag that is not reset for each run.",
    mirror,
    "text = input()\n# Try every run of at least 2 characters.\n",
    input_cases(mirror, ("Example 1: Kayak on Quidi Vidi", ["Kayak on Quidi Vidi"]), ("Example 2: COMP 1001", ["COMP 1001"]),
                ("Typed abc", ["abc"]), ("Typed an empty line", [""]), ("Typed abba deed", ["abba deed"]), ("Typed Noon", ["Noon"]),
                ("Typed a run at the end", ["xyz level"]), ("Typed one character", ["a"]), ("Typed a run with spaces", ["Step on no pets!"])),
    '''_nested("for", "for", "Try every start and end with a for loop inside a for loop.")
assert "break" in __code__, "Stop comparing a run with break at its first mismatch."
assert not re.search(r"\\[[^\\]]*:[^\\]]*:\\s*-", __code__), "Compare characters from both ends in a loop instead of reversing with [::-1]."
''',
    ["Let <code>start</code> run over every index and <code>end</code> from <code>start + 2</code> to <code>len(text)</code>, so the run is <code>text[start:end]</code>.",
     "To test a run, set <code>left = start</code>, <code>right = end - 1</code> and move them toward each other <code>while left &lt; right</code>, comparing lower-case characters.",
     "Keep a flag that starts <code>True</code> for each run and becomes <code>False</code> at a mismatch, then <code>break</code>."],
    "About len(text) cubed comparisons in the worst case, which is fine for 60 characters.")

# ---------------------------------------------------------------- Pig
pig = """import random

seed = int(input())
target = int(input())
hold = int(input())
random.seed(seed)
score_a = 0
score_b = 0
player = 'A'
turns = 0
while score_a < target and score_b < target:
    turns = turns + 1
    if player == 'A':
        score = score_a
    else:
        score = score_b
    turn_total = 0
    rolls = ''
    bust = False
    while turn_total < hold and score + turn_total < target:
        roll = random.randint(1, 6)
        rolls = rolls + ' ' + str(roll)
        if roll == 1:
            bust = True
            break
        turn_total = turn_total + roll
    if bust:
        result = 'bust'
    else:
        score = score + turn_total
        result = f'hold {turn_total}'
    print(f'Turn {turns}, {player}:{rolls}, {result}, score {score}')
    if player == 'A':
        score_a = score
        player = 'B'
    else:
        score_b = score
        player = 'A'
if score_a >= target:
    print(f'A wins {score_a} to {score_b} on turn {turns}')
else:
    print(f'B wins {score_b} to {score_a} on turn {turns}')
"""
question("pig", "The dice game Pig", "Pig", "Lectures 15 and 16; also 8 to 11", 5, ["seed", "target", "hold"],
    "<p>Two players, A and B, play Pig with one die; A goes first and they take turns. On a turn the player rolls again and again, adding each roll to a turn total. "
    "Rolling a 1 is a bust: the turn ends and its total is lost. Otherwise the player stops and adds the turn total to their score as soon as "
    "the turn total reaches <code>hold</code>, or as soon as their score plus the turn total reaches <code>target</code>. "
    "The first player whose score reaches <code>target</code> wins.</p>"
    "<p>Given <code>seed</code>, <code>target</code> and <code>hold</code>, simulate the game with <code>random.seed(seed)</code> and "
    "<code>random.randint(1, 6)</code> for every roll. Print one line per turn with its rolls, the result and the player's score, then the winner.</p>",
    "Read <code>seed</code>, <code>target</code> and <code>hold</code> with <code>int(input())</code>.",
    [(["7", "20", "10"], "A rolls 3, 2, 4 and 6, passing hold 10 with 15, and holds. Turns 2 to 4 all end on a 1. On turn 5, A stops after 3 and 5 because 15 + 8 reaches 20."),
     (["6", "12", "100"], "With hold 100, each player keeps rolling until a 1 or until the score reaches 12. Three turns bust; on turn 4, B reaches 13 and wins.")],
    ["<code>0 &lt;= seed &lt;= 10000</code>", "<code>10 &lt;= target &lt;= 50</code>", "<code>1 &lt;= hold &lt;= 100</code>"],
    ["Call <code>random.seed(seed)</code> once, before the first roll, and roll only with <code>random.randint(1, 6)</code>, so the rolls match the examples.",
     "Play the turns in a <code>while</code> loop and the rolls of one turn in a <code>while</code> loop inside it.",
     "No lists or <code>split()</code>; the only import is <code>random</code>."],
    [("Outer loop runs until a score reaches the target and switches players each turn", 2),
     ("Inner loop rolls while the turn total is below <code>hold</code> and the score plus turn total is below <code>target</code>", 3),
     ("A 1 ends the turn with <code>break</code> and loses the turn total; otherwise the total is added to the right player", 2),
     ("Seeded once, one <code>randint(1, 6)</code> per roll, so the turn lines match", 2),
     ("Winner line with both scores and the number of turns", 1)],
    "Seeding inside the loop, which repeats the same rolls every turn. Adding the 1 to the turn total. Keeping the turn total after a bust. "
    "Testing only <code>hold</code>, so a player rolls past the target. Updating the wrong player's score.",
    pig,
    "import random\n\nseed = int(input())\ntarget = int(input())\nhold = int(input())\nrandom.seed(seed)\n# Play turns until someone reaches the target.\n",
    input_cases(pig, ("Example 1: seed 7, target 20, hold 10", ["7", "20", "10"]), ("Example 2: seed 6, target 12, hold 100", ["6", "12", "100"]),
                ("Typed seed 1, target 30, hold 15", ["1", "30", "15"]), ("Typed seed 42, target 25, hold 8", ["42", "25", "8"]),
                ("Typed seed 2026, target 50, hold 20", ["2026", "50", "20"]), ("Typed seed 0, target 10, hold 1", ["0", "10", "1"])),
    '''_nested("while", "while", "Roll the dice of one turn in a while loop inside the loop over the turns.")
assert "break" in __code__, "End a turn with break when the roll is a 1."
assert re.search(r"random\\.seed\\(\\s*seed\\s*\\)", __code__), "Seed the generator with random.seed(seed) before the first roll."
assert re.search(r"random\\.randint\\(\\s*1\\s*,\\s*6\\s*\\)", __code__), "Roll the die with random.randint(1, 6)."
assert __code__.count("random.seed(") == 1, "Seed the generator once, before the game, not once per turn."
''',
    ["Copy the current player's score into <code>score</code> at the start of the turn and write it back at the end, so one inner loop serves both players.",
     "Roll <code>while turn_total &lt; hold and score + turn_total &lt; target</code>; build the rolls into a string as you go.",
     "On a 1, set a <code>bust</code> flag and <code>break</code>; after the inner loop, add the turn total only when there was no bust, print the line and switch players."],
    "The score copy keeps the turn code the same for both players; with functions it would be a play_turn function.",
    allowed=("random",))

# ---------------------------------------------------------------- page
def esc(text):
    return html.escape(text, quote=False)

def typed(value):
    """One typed line as the boss pages show it: blank for an empty line, quotes when spaces surround it."""
    if value.strip() == "":
        return "blank" if value == "" else f'"{value}"'
    return f'"{value}"' if value != value.strip() else value

def named(names, inputs):
    """The Input line of an example, such as crossings = 5, passengers = 120, 150."""
    parts = []
    for i, name in enumerate(names):
        if name.startswith("*"):
            parts.append(name[1:] + " = " + ", ".join(typed(v) for v in inputs[i:]))
        else:
            parts.append(f"{name} = {typed(inputs[i])}")
    return ", ".join(parts)

def example(q, inputs, explanation, n):
    out = run(q["solution"], inputs)
    output = "Output:\n" + out if "\n" in out else "Output: " + out
    return (f'<div class="wb-block">\n  <div class="wb-block-title">Example {n}</div>\n'
            f'  <pre class="wb-output">Input: {esc(named(q["names"], inputs))}\n{esc(output)}\nExplanation: {esc(explanation)}</pre>\n</div>\n')

def table(cases):
    """More typed inputs and their output, as on the boss pages; runs longer than 5 lines are left out."""
    rows = ""
    for case in cases:
        lines = case["expected"].split("\n")
        if len(lines) <= 5:
            rows += (f'    <tr><td><code>{esc(", ".join(typed(v) for v in case["inputs"]))}</code></td>'
                     f'<td>{" then ".join("<code>" + esc(line) + "</code>" for line in lines)}</td></tr>\n')
    return f'<table>\n  <thead><tr><th>Typed</th><th>Output</th></tr></thead>\n  <tbody>\n{rows}  </tbody>\n</table>\n' if rows else ""

def section(n, q):
    examples = "".join(example(q, inputs, text, i) for i, (inputs, text) in enumerate(q["examples"], 1))
    items = lambda rows: "".join(f"<li>{r}</li>" for r in rows)
    rubric = "".join(f"<tr><td>{what}</td><td>{pts}</td></tr>" for what, pts in q["rubric"])
    assert sum(pts for _, pts in q["rubric"]) == 10, q["qid"]
    return f'''<h2 id="{q["qid"]}" data-toc-title="{emoji(q["rating"])} {esc(q["toc"])}">{emoji(q["rating"])} Question {n}: {esc(q["title"])}</h2>
<p class="wb-meta">10 points · Difficulty {q["rating"]} of 5 · {q["lectures"]}</p>
{q["statement"]}
<p>{q["reading"]}</p>
{examples}<div class="wb-block">
  <div class="wb-block-title">Constraints</div>
  <ul>{items(q["constraints"])}</ul>
</div>
{table(q["cases"])}<div class="wb-block">
  <div class="wb-block-title">Rules the checker enforces</div>
  <ul>{items(q["rules"])}</ul>
</div>
<wb-exercise id="{q["qid"]}"></wb-exercise>
<div class="wb-block">
  <div class="wb-block-title">Marking rubric (10 points)</div>
  <table><thead><tr><th>What we look for</th><th>Points</th></tr></thead><tbody>{rubric}</tbody></table>
  <p>Common mistakes: {q["mistakes"]}</p>
</div>
'''

PAGE = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>COMP 1001 – Question Bank: Loops</title>
  <link rel="icon" href="../../../runtime/img/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="../../../runtime/img/favicon-32.png" type="image/png" sizes="32x32">
  <link rel="stylesheet" href="../../../runtime/workbook.css">
  <script type="module">
    // Instructor only: anyone else is sent back to the workbooks page.
    import { initInstructor, isInstructor } from "../../../runtime/instructor.js";
    import { initWorkbook } from "../../../runtime/workbook.js";
    initInstructor();
    if (isInstructor()) initWorkbook({ id: "bank-loops", specs: "./exercises.json" });
    else location.replace("../../../index.html");
  </script>
</head>
<body>
<main>

<div class="wb-title-block">
  <div>
    <div class="wb-course">COMP 1001: Introduction to Programming</div>
    <h1>Question Bank: Loops</h1>
    <div class="wb-subtitle">Unit 4, Lectures 12 to 16, with earlier material</div>
    <p class="wb-meta">Pranjal Patra<br>Department of Computer Science, Memorial University of Newfoundland</p>
  </div>
  <img src="../../../runtime/img/mun-logo.svg" alt="Memorial University of Newfoundland">
</div>

<section class="wb-outcomes">
  <h2 id="about" data-toc-title="About this bank">About this bank</h2>
  <p>{count} programming questions in the style of Part 2 of a term test, each worth 10 points, for term tests and the final exam. Each one asks for a complete program
  written as top-level code, as in the Unit 4 boss problems: <code>while</code> loops with sentinels and input validation, <code>for</code> loops over <code>range</code>,
  nested loops, <code>break</code>, running totals and best-so-far values, and one seeded <code>random</code> simulation. Decisions and strings from earlier units
  are used freely. Nothing needs functions, lists, exceptions or files.</p>
  <p>The questions are in order of difficulty, from 👹 to 💀: {spread}. Each one has the statement, two examples, the constraints, the rules the checker enforces,
  and, after the editor, a marking rubric and the common mistakes. <strong>Check</strong> runs the program on the examples and more inputs, and also checks the kind
  of loop it uses. <strong>Open in PyLab</strong> shows the question beside a full-screen editor.</p>
  <p>Programs here read values with a plain <code>input()</code> that shows no prompt, so the examples show only what the program prints. On a test paper, add prompts and sample runs.</p>
  <p class="wb-meta">This page opens only in instructor mode. It is not linked for students.</p>
</section>
<hr>

{sections}
</main>
</body>
</html>
'''

Q.sort(key=lambda q: q["rating"])   # stable: equal ratings keep the order above
E = {q["qid"]: E[q["qid"]] for q in Q}
levels = {}
for q in Q:
    levels[q["rating"]] = levels.get(q["rating"], 0) + 1
spread = ", ".join(f"{count} at {rating}" for rating, count in levels.items())

(HERE / "exercises.json").write_text(json.dumps({"id": "bank-loops", "course": "COMP 1001", "title": "Question Bank: Loops",
    "subtitle": "Unit 4, Lectures 12 to 16", "exercises": E}, indent=2, ensure_ascii=False) + "\n")
(HERE / "index.html").write_text(PAGE.replace("{count}", str(len(Q))).replace("{spread}", spread)
                                     .replace("{sections}", "<hr>\n\n".join(section(n, q) for n, q in enumerate(Q, 1))))
print(f"wrote {len(E)} questions: {spread}")
