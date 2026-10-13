"""Build workbooks/lecture-15/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-15/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-15
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

def num(*values, width="4rem"):
    return {"accept": [str(v) for v in values], "placeholder": "value", "width": width}

def yes_no(value):
    return {"accept": ["yes", "y", "true", "reached"] if value else ["no", "n", "false", "not reached", "skipped"],
            "placeholder": "yes / no", "width": "6rem", "show": "yes" if value else "no"}

def pair(a, b, width="5rem"):
    """A cell holding a printed pair such as `1 0`."""
    a, b = str(a), str(b)
    forms = [f"{a} {b}", f"{a}, {b}", f"{a},{b}", f"({a}, {b})", f"({a},{b})", f"{a}; {b}"]
    return {"accept": forms, "placeholder": "pair", "width": width, "show": forms[0]}

def words(*forms, width="8rem", placeholder="answer"):
    return {"accept": list(forms), "placeholder": placeholder, "width": width, "show": forms[0]}

E = {}

# ============================================================ 1. A nested loop is a loop inside a loop
nested = "for row in range(3):\n    for column in range(4):\n        print(row, column)\n"
E["ex-nested"] = example(nested)
assert E["ex-nested"]["output"] == "\n".join(f"{r} {c}" for r in range(3) for c in range(4))
E["cp1"] = {"type": "table", "xp": 1, "blanks": {
    "outer": num(3), "inner": num(4), "after03": pair(1, 0), "final": pair(2, 3)}}

# ============================================================ 2. Trace the inner loop completely for each outer pass
rowcol = 'for row in range(1, 3):\n    for column in range(1, 4):\n        print(f"row={row}, column={column}")\n'
E["ex-rowcol"] = example(rowcol)
assert E["ex-rowcol"]["output"] == "row=1, column=1\nrow=1, column=2\nrow=1, column=3\nrow=2, column=1\nrow=2, column=2\nrow=2, column=3"
trace = [(o, i) for o in range(2) for i in range(3)]
assert trace == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
E["cp2"] = {"type": "table", "xp": 1, "blanks": {}}
for n, (o, i) in enumerate(trace, start=1):
    E["cp2"]["blanks"][f"o{n}"] = num(o)
    E["cp2"]["blanks"][f"i{n}"] = num(i)

# ============================================================ 3. Multiply the iteration counts
count = "executions = 0\n\nfor row in range(3):\n    for column in range(4):\n        executions = executions + 1\n\nprint(executions)\n"
E["ex-count"] = example(count)
assert E["ex-count"]["output"] == "12"
assert len(range(5)) * len(range(3)) == 15 and len(range(2, 7)) * len(range(4)) == 20 and 20 * 20 == 400
E["cp3"] = {"type": "table", "xp": 1, "blanks": {"c53": num(15), "c274": num(20), "c2020": num(400)}}
E["cp3-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why multiply?", "answer": b64(
    "Each outer pass runs every inner pass, so the inner count is repeated once for every outer value.")}

# ============================================================ 4. Think of the loops as rows and columns
rect = 'for row in range(3):\n    for column in range(4):\n        print("*", end="")\n    print()\n'
E["ex-rect"] = example(rect)
assert E["ex-rect"]["output"] == "****\n****\n****"
E["cp4"] = {"type": "table", "xp": 1, "blanks": {"stars": num(10), "prints": num(2)}}
E["cp4-where"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Where is the empty print() indented?", "answer": b64(
    "It must be outside the inner loop but inside the outer loop, aligned with the inner `for` statement.")}

# ============================================================ 5. Nested loops can build a table
table = 'for row in range(1, 4):\n    for column in range(1, 5):\n        product = row * column\n        print(f"{product:4}", end="")\n    print()\n'
E["ex-table"] = example(table)
assert E["ex-table"]["output"] == "   1   2   3   4\n   2   4   6   8\n   3   6   9  12"
E["cp5"] = {"type": "table", "xp": 1, "blanks": {
    "p1": num(4), "p2": num(8), "p3": num(12), "p4": num(16), "p5": num(20),
    "fixed": words("row", "the row variable", "row variable", "the outer variable", "outer variable", "the outer loop variable",
                   "outer loop variable", "outer", "the outer loop", "outer loop", placeholder="variable")}}
assert [4 * c for c in range(1, 6)] == [4, 8, 12, 16, 20]

# ============================================================ 6. The inner range can depend on the outer value
triangle = 'for row in range(1, 6):\n    for column in range(row):\n        print("*", end="")\n    print()\n'
E["ex-triangle"] = example(triangle)
assert E["ex-triangle"]["output"] == "*\n**\n***\n****\n*****"
E["cp6"] = {"type": "table", "xp": 1, "blanks": {
    "r1": num(1), "r2": num(2), "r3": num(3), "r4": num(4), "r5": num(5), "total": num(15)}}
assert sum(len(range(r)) for r in range(1, 6)) == 15
E["cp6-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why not multiply?", "answer": b64(
    "The inner range changes with `row`, so there is no single fixed inner count to multiply by the number of outer passes.")}

# ============================================================ 7. Nested loops can visit every pair
pairs = 'text = "ABC"\n\nfor first in range(len(text)):\n    for second in range(first + 1, len(text)):\n        print(text[first], text[second])\n'
E["ex-pairs"] = example(pairs)
assert E["ex-pairs"]["output"] == "A B\nA C\nB C"
wxyz = [(t[a], t[b]) for t in ["WXYZ"] for a in range(len(t)) for b in range(a + 1, len(t))]
assert wxyz == [("W", "X"), ("W", "Y"), ("W", "Z"), ("X", "Y"), ("X", "Z"), ("Y", "Z")]
E["cp7"] = {"type": "table", "xp": 1, "blanks": {}}
for n, (a, b) in enumerate(wxyz, start=1):
    E["cp7"]["blanks"][f"pair{n}"] = pair(a, b)
E["cp7"]["blanks"]["count"] = num(6)
E["cp7-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why zero inner iterations?", "answer": b64(
    "On the final outer pass, `first + 1` equals the length of the string, so the inner range is empty.")}

# ============================================================ 8. break leaves a loop immediately
brk = 'for number in range(2, 10):\n    if number * number > 30:\n        break\n    print(number)\n\nprint("Finished")\n'
E["ex-break"] = example(brk)
assert E["ex-break"]["output"] == "2\n3\n4\n5\nFinished"
E["cp8"] = {"type": "table", "xp": 1, "blanks": {
    "first": num(6), "printed": yes_no(False),
    "after": {"accept": ['print("Finished")', "print('Finished')", "print(Finished)", "print Finished", "print(“Finished”)",
                         "the print statement", "print statement", "the print", "print", 'the print("Finished") statement',
                         "print(\"Finished\") statement"],
              "placeholder": "statement", "width": "10rem", "show": 'print("Finished")'}}}

# ============================================================ 9. break affects only the innermost loop
nested_break = 'for row in range(1, 4):\n    for column in range(1, 5):\n        if column == 3:\n            break\n        print(row, column)\n    print(f"End of row {row}")\n'
E["ex-nested-break"] = example(nested_break)
assert E["ex-nested-break"]["output"] == "1 1\n1 2\nEnd of row 1\n2 1\n2 2\nEnd of row 2\n3 1\n3 2\nEnd of row 3"
E["cp9"] = {"type": "table", "xp": 1, "blanks": {
    "which": words("the inner loop", "inner", "inner loop", "the inner for loop", "inner for loop", "for column", "the for column loop",
                   "for column loop", "column", "the column loop", "column loop", "the inner for column loop",
                   "for column in range(1, 5)", "for column in range(1, 5):", "for column in range(1,5)", "for column in range(1,5):",
                   width="10rem", placeholder="which loop"),
    "breaks": num(3), "endrows": num(3)}}
E["cp9-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "What would the outer loop need?", "answer": b64(
    "The outer loop would need its own stopping condition and its own `break`.")}

# ============================================================ 10. continue skips the rest of one pass
cont = 'for number in range(1, 11):\n    if number % 3 == 0:\n        continue\n    print(number, end=" ")\nprint()\n'
E["ex-continue"] = example(cont)
assert E["ex-continue"]["output"].rstrip() == "1 2 4 5 7 8 10"
E["cp10"] = {"type": "table", "xp": 1, "blanks": {
    "n2": yes_no(True), "n3": yes_no(False), "n4": yes_no(True), "n6": yes_no(False), "ends": yes_no(False)}}
assert [n % 3 != 0 for n in (2, 3, 4, 6)] == [True, False, True, False]
E["cp10-where"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Where does execution go?", "answer": b64(
    "Execution begins the next iteration of the nearest loop.")}

# ============================================================ 11. continue can hide a while-loop update
# The faulty listing is shown as static text on the page: it never ends.
E["cp11-a"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "placeholder": "Why does the loop stop making progress?", "answer": b64(
    "At 5, `continue` skips the update, so the condition is checked again with the same value.")}
E["cp11-b"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Where could the update move?", "answer": b64(
    "Move the update above the `if`.")}
E["cp11-c"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Which statement would you remove?", "answer": b64(
    "If a simple condition can express the same logic clearly, prefer removing `continue`.")}

# ============================================================ Final review
E["fr1"] = {"type": "short", "xp": 2, "answer": b64("The outer loop contains another loop. The inner loop is the loop inside the outer loop's body.")}
E["fr2"] = {"type": "short", "xp": 2, "answer": b64("For one outer value, the inner loop goes through all of its values. Then the outer loop advances and the inner loop starts again.")}
E["fr3"] = {"type": "short", "xp": 2, "answer": b64("Multiply the number of outer passes by the number of inner passes.")}
E["fr4"] = {"type": "short", "xp": 2, "answer": b64("It prevents `print` from moving to a new line, so several values can be printed on the same row.")}
E["fr5"] = {"type": "short", "xp": 2, "answer": b64("It should start a new line only after every column in the current row has been printed.")}
E["fr6"] = {"type": "short", "xp": 2, "answer": b64("It ends the nearest loop immediately and continues with the first statement after that loop.")}
E["fr7"] = {"type": "short", "xp": 2, "answer": b64("It skips the rest of the current iteration and begins the next iteration of the nearest loop.")}
E["fr8"] = {"type": "short", "xp": 2, "answer": b64("Only the inner loop is affected.")}

# ============================================================ Putting It All Together
seats1 = "for row in range(1, 4):\n    for seat in range(1, 6):\n        print(row, seat)\n"
seats2 = "for row in range(1, 4):\n    for seat in range(1, 6):\n        if seat == 3:\n            continue\n        print(row, seat)\n"
seats3 = ('for row in range(1, 4):\n    print(f"Row {row}:", end="")\n    for seat in range(1, 6):\n        if row == 2 and seat == 5:\n            break\n'
          '        if seat == 3:\n            continue\n        print(f" {seat}", end="")\n    print()\n')
E["ex-seats1"] = example(seats1)
E["ex-seats2"] = example(seats2)
E["ex-seats3"] = example(seats3)
assert E["ex-seats1"]["output"].count("\n") == 14
assert E["ex-seats2"]["output"].count("\n") == 11 and " 3" not in E["ex-seats2"]["output"].replace("3 ", "")
assert E["ex-seats3"]["output"] == "Row 1: 1 2 4 5\nRow 2: 1 2 4\nRow 3: 1 2 4 5"
E["syn-a"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "placeholder": "Why is the barrier test first?", "answer": b64(
    "The barrier test comes first because reaching the barrier should end the row, not merely skip one seat.")}
E["syn-b"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "placeholder": "Why does row 3 still print?", "answer": b64(
    "Row 3 still prints because the `break` affects only the inner seat loop.")}
E["syn"] = {"type": "table", "xp": 1, "blanks": {"total": num(11)}}
assert sum(len(line.split(":")[1].split()) for line in E["ex-seats3"]["output"].split("\n")) == 11

# ============================================================ Coding Practice
NO_WHILE = 'assert "while" not in __code__, "Use for loops here, not a while loop."\n'
ONE_FOR = '''import re
assert len(re.findall(r"^\\s*for\\b", __code__, re.M)) == 1, "Use exactly one for loop."
'''
TWO_FOR = '''import re
assert len(re.findall(r"^\\s*for\\b", __code__, re.M)) >= 2, "Use two for loops."
'''
NESTED_FOR = '''import re
_fors = [len(m.group(1).expandtabs(4)) for m in re.finditer(r"^([ \\t]*)for\\b", __code__, re.M)]
assert len(_fors) >= 2 and max(_fors) > min(_fors), "Use nested for loops: an inner for loop inside the body of an outer one."
'''
WHILE_LOOP = '''import re
assert re.search(r"^\\s*while\\b", __code__, re.M), "Use a while loop; the number of passes is not known in advance."
'''

# 1. Nested-loop vocabulary
E["p1"] = {"type": "short", "xp": 2, "minChars": 40, "rows": 3, "placeholder": "Define a nested loop and give one row-and-column task…", "answer": b64(
    "A nested loop is a loop inside the body of another loop. For example, a program can use the outer loop for rows of seats and the inner loop for the seat numbers across each row.")}

# 2. One loop for repeated rows
rows_nested = 'for row in range(3):\n    for column in range(5):\n        print("*", end="")\n    print()\n'
rows_one = 'for row in range(3):\n    print("*" * 5)\n'
E["ex-rows"] = example(rows_nested)
assert E["ex-rows"]["output"] == run(rows_one) == "*****\n*****\n*****"
E["p2"] = {"type": "code", "xp": 2, "minLines": 3, "starter": "# Print three rows of five stars with one for loop.\n",
    "cases": [{"name": "Three rows of five stars", "expected": run(rows_one)}],
    "check": ONE_FOR + NO_WHILE,
    "answer": b64(rows_one),
    "answerNote": "The inner loop is unnecessary when every row is exactly the same."}

# 3. Clock-reading practice
clock = 'for hour in range(1, 3):\n    for minute in range(0, 60, 20):\n        print(f"{hour}:{minute:02}")\n'
E["p3"] = {"type": "code", "xp": 5, "minLines": 4, "starter": "# Print the times from 1:00 through 2:40 at 20-minute intervals.\n",
    "cases": [{"name": "1:00 through 2:40", "expected": run(clock)}],
    "check": NESTED_FOR + NO_WHILE + '''assert re.search(r":[^}]*02[^}]*\\}", __source__), "Show the minutes in a two-digit field with :02."
''',
    "answer": b64(clock),
    "answerNote": "The outer loop supplies the hour and the inner loop supplies 0, 20, and 40 minutes."}
assert E["p3"]["cases"][0]["expected"] == "1:00\n1:20\n1:40\n2:00\n2:20\n2:40"

# 4. Destination tickets
tickets = ("ticket = 0\n\nfor destination in range(1, 4):\n    if destination == 1:\n        friends = 10\n    elif destination == 2:\n        friends = 3\n"
           "    else:\n        friends = 2\n\n    for friend in range(friends):\n        ticket = ticket + 1\n        print(ticket, destination)\n")
E["p4"] = {"type": "code", "xp": 5, "minLines": 8, "starter": "ticket = 0\n\n# For each destination, print one ticket line per friend.\n",
    "cases": [{"name": "Tickets 1 through 15", "expected": run(tickets)}],
    "check": NESTED_FOR + NO_WHILE,
    "answer": b64(tickets),
    "answerNote": "The outer loop chooses a destination. The inner count is selected from the number of friends in that destination."}
assert E["p4"]["cases"][0]["expected"].split("\n")[-3:] == ["13 2", "14 3", "15 3"]
assert E["p4"]["cases"][0]["expected"].count("\n") == 14

# 5. Addition table
addition = 'for row in range(1, 5):\n    for column in range(1, 5):\n        print(f"{row + column:4}", end="")\n    print()\n'
E["p5"] = {"type": "code", "xp": 5, "minLines": 4, "starter": "# Print the 4-by-4 addition table with a field width of four.\n",
    "cases": [{"name": "4-by-4 addition table", "expected": run(addition)}],
    "check": NESTED_FOR + NO_WHILE + '''assert re.search(r":[^}]*4\\}", __source__), "Give every value a field width of four with :4."
''',
    "answer": b64(addition),
    "answerNote": "Add the current row and column labels for each cell."}
assert E["p5"]["cases"][0]["expected"] == "   2   3   4   5\n   3   4   5   6\n   4   5   6   7\n   5   6   7   8"

# 6. Course and student averages
averages = ("overall_total = 0\n\nfor student in range(1, 3):\n    student_total = 0\n    for grade_number in range(3):\n        grade = int(input())\n"
            "        student_total = student_total + grade\n        overall_total = overall_total + grade\n"
            '    print(f"Student {student}: {student_total / 3:.1f}")\n\nprint(f"Overall: {overall_total / 6:.1f}")\n')
E["p6"] = {"type": "code", "xp": 10, "minLines": 9, "starter": "overall_total = 0\n\n# Read three grades for each of two students.\n",
    "cases": [case("Typed 80, 70, 90, 60, 75, 75", ["80", "70", "90", "60", "75", "75"], averages),
              case("Typed 100, 100, 100, 0, 0, 0", ["100", "100", "100", "0", "0", "0"], averages),
              case("Typed 50, 60, 70, 80, 90, 100", ["50", "60", "70", "80", "90", "100"], averages),
              case("Typed 71, 72, 74, 65, 66, 68", ["71", "72", "74", "65", "66", "68"], averages)],
    "check": NESTED_FOR + NO_WHILE + '''assert re.search(r":[^}]*\\.1f\\}", __source__), "Show each average with one decimal place using :.1f."
''',
    "answer": b64(averages),
    "answerNote": "Reset the student total on each outer pass and keep a separate overall total."}
assert E["p6"]["cases"][0]["expected"] == "Student 1: 80.0\nStudent 2: 70.0\nOverall: 75.0"
assert E["p6"]["cases"][3]["expected"] == "Student 1: 72.3\nStudent 2: 66.3\nOverall: 69.3"

# 7. Validated repeat choice
choice = ('while True:\n    choice = input().upper()\n    if choice != "Y" and choice != "N":\n        print("Invalid")\n        continue\n'
          '    if choice == "N":\n        print("Finished")\n        break\n    print("Again")\n')
E["p7"] = {"type": "code", "xp": 5, "minLines": 7, "starter": "# Read choices until N is entered.\n",
    "cases": [case("Typed maybe, y, n", ["maybe", "y", "n"], choice), case("Typed N", ["N"], choice),
              case("Typed Y, Y, n", ["Y", "Y", "n"], choice), case("Typed x, an empty line, yes, N", ["x", "", "yes", "N"], choice)],
    "check": '''import re
assert re.search(r"^\\s*while\\s+True\\b", __code__, re.M), "Use while True for the loop."
assert "continue" in __code__, "Discard an invalid choice with continue."
assert "break" in __code__, "Leave the loop with break when the choice is N."
''',
    "answer": b64(choice),
    "answerNote": "Invalid input is discarded with `continue`; `N` reaches the one loop exit."}
assert E["p7"]["cases"][0]["expected"] == "Invalid\nAgain\nFinished"
assert E["p7"]["cases"][3]["expected"] == "Invalid\nInvalid\nInvalid\nFinished"

# 8. Hollow notice frame
frame = ('side = int(input())\n\nfor row in range(side):\n    for column in range(side):\n'
         '        if row == 0 or row == side - 1 or column == 0 or column == side - 1:\n            print("#", end="")\n'
         '        else:\n            print(" ", end="")\n    print()\n')
E["p8"] = {"type": "code", "xp": 10, "minLines": 8, "starter": "side = int(input())\n\n# Print a hollow square with side characters on each edge.\n",
    "cases": [case("Typed 4", ["4"], frame), case("Typed 2", ["2"], frame), case("Typed 8", ["8"], frame),
              case("Typed 5", ["5"], frame), case("Typed 3", ["3"], frame)],
    "check": NESTED_FOR + NO_WHILE,
    "answer": b64(frame),
    "answerNote": "A position is on the border when its row or column is the first or last one."}
assert E["p8"]["cases"][0]["expected"] == "####\n#  #\n#  #\n####"
assert E["p8"]["cases"][1]["expected"] == "##\n##"

# 9. Number diamond
diamond = ('size = int(input())\n\nfor row in range(1, size + 1):\n    print(" " * (size - row), end="")\n    print(str(row) * (2 * row - 1))\n\n'
           'for row in range(size - 1, 0, -1):\n    print(" " * (size - row), end="")\n    print(str(row) * (2 * row - 1))\n')
E["p9"] = {"type": "code", "xp": 10, "minLines": 7, "starter": "size = int(input())\n\n# Print the growing half, then the shrinking half.\n",
    "cases": [case("Typed 3", ["3"], diamond), case("Typed 1", ["1"], diamond), case("Typed 5", ["5"], diamond),
              case("Typed 2", ["2"], diamond), case("Typed 4", ["4"], diamond)],
    "check": TWO_FOR + NO_WHILE,
    "answer": b64(diamond),
    "answerNote": "For row `r`, print `size - r` spaces and `2 * r - 1` copies of the row number. The lower half starts at `size - 1` so the widest row is not repeated."}
assert E["p9"]["cases"][0]["expected"] == "  1\n 222\n33333\n 222\n  1"
assert E["p9"]["cases"][1]["expected"] == "1"

# 10. Seat sale
sale = ('remaining = 12\nbuyers = 0\n\nwhile remaining > 0:\n    requested = int(input())\n    if requested > remaining:\n'
        '        print("Not enough seats")\n        continue\n    remaining = remaining - requested\n    buyers = buyers + 1\n\nprint(f"Buyers: {buyers}")\n')
E["p10"] = {"type": "code", "xp": 10, "minLines": 8, "starter": "remaining = 12\nbuyers = 0\n\n# Sell seats until none remain, then print the number of buyers.\n",
    "cases": [case("Typed 4, 3, 4, 2, 1", ["4", "3", "4", "2", "1"], sale), case("Typed 4, 4, 4", ["4", "4", "4"], sale),
              case("Typed 1 twelve times", ["1"] * 12, sale), case("Typed 3, 3, 3, 4, 3", ["3", "3", "3", "4", "3"], sale),
              case("Typed 2, 4, 4, 3, 1, 1", ["2", "4", "4", "3", "1", "1"], sale)],
    "check": WHILE_LOOP + '''assert not re.search(r"^\\s*for\\b", __code__, re.M), "A while loop fits here; the number of requests is not known."
''',
    "answer": b64(sale),
    "answerNote": "Only accepted requests change the remaining-seat count or buyer count."}
assert E["p10"]["cases"][0]["expected"] == "Not enough seats\nBuyers: 4"
assert E["p10"]["cases"][1]["expected"] == "Buyers: 3"
assert E["p10"]["cases"][4]["expected"] == "Not enough seats\nBuyers: 5"

# 11. Room occupancy
occupancy = ('occupancy = 0\n\nwhile occupancy < 8:\n    change = int(input())\n    proposed = occupancy + change\n    if proposed < 0 or proposed > 8:\n'
             '        print("Rejected")\n        continue\n    occupancy = proposed\n    print(occupancy)\n\nprint("Full")\n')
E["p11"] = {"type": "code", "xp": 10, "minLines": 8, "starter": "occupancy = 0\n\n# Read changes until the room reaches 8 people.\n",
    "cases": [case("Typed 5, 4, -2, 5", ["5", "4", "-2", "5"], occupancy), case("Typed 8", ["8"], occupancy),
              case("Typed 9, -1, 8", ["9", "-1", "8"], occupancy), case("Typed 3, 3, 3, -9, 2", ["3", "3", "3", "-9", "2"], occupancy),
              case("Typed 2, -2, 0, 8", ["2", "-2", "0", "8"], occupancy)],
    "check": WHILE_LOOP + '''assert not re.search(r"^\\s*for\\b", __code__, re.M), "A while loop fits here; the number of changes is not known."
''',
    "answer": b64(occupancy),
    "answerNote": "Test the proposed occupancy before changing the stored value, so a rejected group does not change the room count."}
assert E["p11"]["cases"][0]["expected"] == "5\nRejected\n3\n8\nFull"
assert E["p11"]["cases"][2]["expected"] == "Rejected\nRejected\n8\nFull"
assert E["p11"]["cases"][4]["expected"] == "2\n0\n0\n8\nFull"

# 12. Channel-width table
channel = 'for depth in range(5):\n    width = 8.0 * (1 - depth / 4)\n    print(f"Depth {depth} m: {width:.1f} m")\n'
E["p12"] = {"type": "code", "xp": 5, "minLines": 3, "starter": "# Print the width at each whole-metre depth from 0 through 4.\n",
    "cases": [{"name": "Depths 0 through 4", "expected": run(channel)}],
    "check": ONE_FOR + NO_WHILE + '''assert re.search(r":[^}]*\\.1f\\}", __source__), "Show the width with one decimal place using :.1f."
''',
    "answer": b64(channel),
    "answerNote": "The formula supplies the width for each depth."}
assert E["p12"]["cases"][0]["expected"] == "Depth 0 m: 8.0 m\nDepth 1 m: 6.0 m\nDepth 2 m: 4.0 m\nDepth 3 m: 2.0 m\nDepth 4 m: 0.0 m"

# 13. Terminal checkerboard
board = 'for row in range(8):\n    for column in range(8):\n        if (row + column) % 2 == 0:\n            print("#", end="")\n        else:\n            print(".", end="")\n    print()\n'
E["p13"] = {"type": "code", "xp": 5, "minLines": 6, "starter": "# Print the 8-by-8 checkerboard.\n",
    "cases": [{"name": "8-by-8 checkerboard", "expected": run(board)}],
    "check": NESTED_FOR + NO_WHILE + '''assert re.search(r"%\\s*2\\b", __code__), "Decide each character from the remainder of row + column after division by 2."
''',
    "answer": b64(board),
    "answerNote": "The sum `row + column` changes parity at every neighbouring position."}
assert E["p13"]["cases"][0]["expected"] == "\n".join(["#.#.#.#.", ".#.#.#.#"] * 4)

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-15",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 15 Workbook",
    "subtitle": "Nested loops, break and continue",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-15/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
