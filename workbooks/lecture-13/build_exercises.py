"""Build workbooks/lecture-13/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-13/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-13
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
    return {"accept": ["yes", "y"] if value else ["no", "n"], "placeholder": "yes / no", "width": "6rem", "show": "yes" if value else "no"}

def cond(left, value):
    """A trace-table condition cell such as `3 > 0 is True`; accept the short forms too."""
    v = "True" if value else "False"
    forms = [f"{left} is {v}", f"{left} {v}", f"{left}: {v}", f"{left} -> {v}", f"{left} → {v}", f"{left} = {v}", f"{left} == {v}", v, left]
    forms += [f.replace(" > ", ">") for f in forms if " > " in f]
    return {"accept": forms, "placeholder": "condition", "width": "10rem", "show": f"{left} is {v}"}

E = {}

# ============================================================ 1. Hand-tracing executes code on paper
digits = "n = 1729\ntotal = 0\n\nwhile n > 0:\n    digit = n % 10\n    total = total + digit\n    n = n // 10\n\nprint(total)\n"
E["ex-digits"] = example(digits)
assert E["ex-digits"]["output"] == "19"
E["cp1"] = {"type": "table", "xp": 1, "blanks": {
    "digit": num(9),
    "stmt": {"accept": ["n = n // 10", "n //= 10", "n=n//10", "n//=10", "n = n//10", "n // 10", "n//10", "// 10", "//"], "caseSensitive": True, "placeholder": "statement", "width": "10rem", "show": "n = n // 10"}}}
E["cp1-end"] = {"type": "short", "xp": 1, "minChars": 10, "rows": 2, "placeholder": "When does the loop end?", "answer": b64(
    "The loop ends when `n > 0` is false. For this program, that happens when `n` is `0`.")}

# ============================================================ 2. A trace table records each pass
E["ex-cp2"] = example("n = 3\ntotal = 0\nwhile n > 0:\n    total = total + n\n    n = n - 1\n", output=False)
E["cp2"] = {"type": "table", "xp": 1, "blanks": {
    "c0": cond("3 > 0", True),
    "c1": cond("3 > 0", True), "n1": num(2), "t1": num(3),
    "c2": cond("2 > 0", True), "n2": num(1), "t2": num(5),
    "c3": cond("1 > 0", True), "n3": num(0), "t3": num(6),
    "c4": cond("0 > 0", False), "n4": num(0), "t4": num(6)}}

# ============================================================ 3. Tracing exposes common loop bugs
reset = "n = 1\nwhile n <= 4:\n    total = 0\n    total = total + n\n    n = n + 1\n\nprint(total)\n"
E["ex-reset"] = example(reset)
assert E["ex-reset"]["output"] == "4"
E["cp3"] = {"type": "table", "xp": 1, "blanks": {
    "p1": num(1), "p2": num(2), "p3": num(3), "p4": num(4),
    "line": {"accept": ["total = 0", "total=0"], "caseSensitive": True, "placeholder": "line", "width": "8rem", "show": "total = 0"}}}
E["cp3-where"] = {"type": "short", "xp": 1, "minChars": 10, "rows": 2, "placeholder": "Where does the line belong?", "answer": b64(
    "Move `total = 0` before the loop so that it runs once, before any values are added.")}

# ============================================================ 4. A sentinel marks the end of input
marks = ("total = 0.0\ncount = 0\nmark = float(input('Mark (-1 to finish): '))\n\n"
         "while mark != -1:\n    total = total + mark\n    count = count + 1\n    mark = float(input('Mark (-1 to finish): '))\n\n"
         "print('Values entered:', count)\nprint(f'Total: {total:.1f}')\n")
E["ex-marks"] = example(marks, output=False)
assert run_with_prompts(marks, ["72", "84", "-1"]).endswith("Values entered: 2\nTotal: 156.0")
E["cp4"] = {"type": "table", "xp": 1, "blanks": {
    "s72": yes_no(False), "a72": yes_no(True), "c72": num(1),
    "s84": yes_no(False), "a84": yes_no(True), "c84": num(2),
    "s-1": yes_no(True), "a-1": yes_no(False), "c-1": num(2)}}
E["cp4-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The test must happen first because the sentinel is a control value, not a mark. Adding it would change the result.")}

# ============================================================ 5. Choose a sentinel that cannot be real data
temps = ("total = 0.0\ntext = input('Temperature, or done: ').strip().lower()\n\n"
         "while text != 'done':\n    temperature = float(text)\n    total = total + temperature\n"
         "    text = input('Temperature, or done: ').strip().lower()\n\nprint(f'Total: {total:.1f}')\n")
E["ex-temps"] = example(temps, output=False)
assert run_with_prompts(temps, ["-1", "4", "done"]).endswith("Total: 3.0")
E["cp5"] = {"type": "table", "xp": 1, "blanks": {
    "dist": {"accept": ["0", "0.0", "-1", "-1.0", "zero"], "placeholder": "sentinel", "width": "8rem", "show": "0"},
    "whole": {"accept": ["none", "no numeric sentinel", "there is none", "no number", "not a number", "a word", "text", "done", "'done'", "\"done\"", "blank line", "a blank line", "blank", "empty string", "an empty string", "''", "\"\"", "the empty string", "a blank line or 'done'", "blank line or 'done'", "a blank line or a word such as 'done'", "read text", "read text first"],
              "placeholder": "sentinel", "width": "12rem", "show": "a blank line or 'done'"}}}
E["cp5-why"] = {"type": "short", "xp": 2, "answer": b64(
    "For positive distances, `0` is safe because a positive distance must be greater than zero.\n\n"
    "For any whole number, no numeric sentinel is safe. Read text and use a blank line or a word such as `'done'`.")}

# ============================================================ 6. A priming read prepares the first test
priming = ("text = input('Value, or blank to finish: ')   # priming read\n\n"
           "while text != '':\n    value = float(text)\n    print(f'Received: {value:.1f}')\n"
           "    text = input('Value, or blank to finish: ')  # next read\n")
E["ex-priming"] = example(priming, output=False)
assert run_with_prompts(priming, ["2.5", ""]).endswith("Received: 2.5\nValue, or blank to finish: ")
E["cp6"] = {"type": "table", "xp": 1, "blanks": {
    "before": {"accept": ["priming read", "the priming read", "priming", "a priming read", "priming-read", "gives the loop condition its first value", "provides the first value for the test", "provides a value for the first test", "first value for the loop condition", "the first test"],
               "placeholder": "purpose", "width": "14rem", "show": "priming read"},
    "bottom": {"accept": ["next read", "the next read", "next", "reads the next value", "obtains the value for the next test", "the value for the next test", "value for the next test", "gets the next value", "read the next value", "next value"],
               "placeholder": "purpose", "width": "14rem", "show": "next read"}}}
E["cp6-missing"] = {"type": "short", "xp": 2, "answer": b64(
    "If the second input were missing and the first value were not blank, `text` would never change and the loop would not end.")}

# ============================================================ 7. while True with break avoids the duplicate read
brk = ("total = 0.0\ncount = 0\n\nwhile True:\n    mark = float(input('Mark (-1 to finish): '))\n"
       "    if mark == -1:\n        break\n    total = total + mark\n    count = count + 1\n\nprint('Values entered:', count)\n")
E["ex-break"] = example(brk, output=False)
assert run_with_prompts(brk, ["72", "84", "-1"]).endswith("Values entered: 2")
E["cp7"] = {"type": "table", "xp": 1, "blanks": {
    "where": {"accept": ["the first line after the loop", "first line after the loop", "the line after the loop", "after the loop", "at the first line after the loop", "the first statement after the loop", "first statement after the loop", "the statement after the loop", "the print", "the print statement", "the print line", "at the print", "print('Values entered:', count)", "print", "the last line", "after the while loop", "the line after the while loop", "outside the loop"],
              "placeholder": "where?", "width": "16rem", "show": "the first line after the loop"},
    "breaks": {"accept": ["1", "one"], "placeholder": "how many?", "width": "6rem", "show": "1"}}}
E["cp7-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The `break` runs before the addition, so the sentinel is not processed.")}

# ============================================================ 8. Compare the two sentinel structures
WT = ["while True", "while true", "while True with break", "while True with one break", "while True with one clear break", "while True and break", "while True / break", "while true with break", "while True with a break"]
PR = ["priming read", "priming-read", "priming", "a priming read", "the priming read", "priming read loop", "priming-read loop"]
E["cp8"] = {"type": "table", "xp": 1, "blanks": {
    "once": {"accept": WT, "placeholder": "structure", "width": "10rem", "show": "while True"},
    "header": {"accept": PR, "placeholder": "structure", "width": "10rem", "show": "priming read"},
    "standard": {"accept": WT, "placeholder": "structure", "width": "14rem", "show": "while True with one clear break"}}}

# ============================================================ 9. Plan the user conversation with a storyboard
E["cp9-story"] = {"type": "short", "xp": 2, "minChars": 40, "rows": 5, "placeholder": "Prompt and reply on each line, then the final output…", "answer": b64(
    "One possible storyboard:\n\n`Distance (0 to finish): 2.5`\n`Distance (0 to finish): 1.25`\n`Distance (0 to finish): 0`\n`Total distance: 3.75 km`")}
E["cp9-zero"] = {"type": "table", "xp": 1, "blanks": {
    "zero": {"accept": ["Total distance: 0.00 km", "Total distance: 0.0 km", "Total distance: 0 km", "Total distance: 0.00", "Total distance: 0.0", "Total distance: 0", "0.00 km", "0.0 km", "0 km", "0.00", "0.0", "0", "a total of 0", "a total of zero", "total 0", "zero", "Total: 0.00", "Total: 0.0", "Total: 0"],
             "placeholder": "output", "width": "14rem", "show": "Total distance: 0.00 km"}}}

# ============================================================ 10. Guard an average against empty input
average = ("total = 0.0\ncount = 0\n\nwhile True:\n    mark = float(input('Mark (-1 to finish): '))\n    if mark == -1:\n        break\n"
           "    total = total + mark\n    count = count + 1\n\nif count > 0:\n    average = total / count\n"
           "    print(f'Average of {count} marks: {average:.2f}')\nelse:\n    print('No marks were entered.')\n")
E["ex-average"] = example(average, output=False)
assert run_with_prompts(average, ["72", "84", "-1"]).endswith("Average of 2 marks: 78.00")
assert run_with_prompts(average, ["-1"]).endswith("No marks were entered.")
E["cp10"] = {"type": "table", "xp": 1, "blanks": {
    "total": {"accept": ["0.0", "0", "0.00"], "placeholder": "value", "width": "5rem", "show": "0.0"},
    "count": num(0, width="5rem"),
    "safe": {"accept": ["no", "n", "not safe", "unsafe", "no, ZeroDivisionError", "no (ZeroDivisionError)"], "placeholder": "yes / no", "width": "6rem", "show": "no"},
    "branch": {"accept": ["else", "the else branch", "else branch", "the else", "else:", "the else:", "No marks were entered.", "print('No marks were entered.')", "the second branch", "the else part"],
               "placeholder": "branch", "width": "10rem", "show": "the else branch"}}}

# ============================================================ 11. Test sentinel loops at their boundaries
E["cp11"] = {"type": "short", "xp": 2, "minChars": 40, "rows": 6, "placeholder": "One test per line: input sequence, expected result, purpose…", "answer": b64(
    "One useful set is:\n\n"
    "`-1`: zero prices; no division by zero (sentinel first).\n\n"
    "`12.50, -1`: count 1; total 12.50 (one data value).\n\n"
    "`0, 8.25, 3.75, -1`: count 3; total 12.00 (zero price and repeated updates).")}

# ============================================================ Final review
E["fr1"] = {"type": "short", "xp": 2, "answer": b64("Follow the program one statement at a time and record each value as it changes.")}
E["fr2"] = {"type": "short", "xp": 2, "answer": b64("A row should record the condition and variable state at a clear moment, usually before the loop, after a pass, or at exit. Updates should be recorded in statement order.")}
E["fr3"] = {"type": "short", "xp": 2, "answer": b64("Examples include an incorrect initial value, an off-by-one boundary, a missing update, and an accumulator reset inside the loop.")}
E["fr4"] = {"type": "short", "xp": 2, "answer": b64("A sentinel is a special input value that marks the end of a sequence and is not processed as data.")}
E["fr5"] = {"type": "short", "xp": 2, "answer": b64("A temperature of `-1` is valid data, so the program could stop before processing all temperatures.")}
E["fr6"] = {"type": "short", "xp": 2, "answer": b64("A priming read is the input operation before a loop that provides the first value for the loop condition.")}
E["fr7"] = {"type": "short", "xp": 2, "answer": b64("It leaves the nearest enclosing loop immediately and continues at the first statement after that loop.")}
E["fr8"] = {"type": "short", "xp": 2, "answer": b64("The count may be zero when the sentinel is entered first. Testing the count prevents division by zero.")}

# ============================================================ Putting It All Together
study = ("total = 0.0\ncount = 0\n\nwhile True:\n    minutes = float(input('Study time (-1 to finish): '))\n    if minutes == -1:\n        break\n"
         "    total = total + minutes\n    count = count + 1\n\nif count > 0:\n    average = total / count\n"
         "    print(f'Average of {count} entries: {average:.2f} minutes')\nelse:\n    print('No study times were entered.')\n")
study_starter = (study.replace("if minutes == -1:", "if ________________________________________________:")
                 .replace("    total = total + minutes\n    count = count + 1\n", "    _________________________________________________\n    _________________________________________________\n")
                 .replace("if count > 0:", "if _________________________________________________:")
                 .replace("average = total / count", "average = ________________________________________"))
assert sum("____" in line for line in study_starter.splitlines()) == 5
SENTINEL_FIRST = '''import re
assert "while True" in __source__, "Keep the while True loop with one break."
assert __source__.count("break") == 1, "Use exactly one break to leave the loop."
update = re.search(r"total\\s*(\\+=|=\\s*total\\s*\\+)", __source__)
assert update, "Add each value to total with total = total + ... inside the loop."
assert __source__.index("break") < update.start(), "Test the sentinel and break before total and count are updated."
'''
COUNT_GUARD = '''import re
assert re.search(r"if\\s+count\\s*(>\\s*0|!=\\s*0|>=\\s*1)\\s*:|if\\s+count\\s*:", __source__), "Test count > 0 before dividing by it."
'''
E["syn"] = {"type": "code", "xp": 5, "minLines": 15, "starter": study_starter,
    "cases": [case("30, 45, -1", ["30", "45", "-1"], study),
              case("-1 first", ["-1"], study),
              case("60, -1", ["60", "-1"], study),
              case("0, 0, 90, -1", ["0", "0", "90", "-1"], study)],
    "check": SENTINEL_FIRST + COUNT_GUARD,
    "answer": b64(study),
    "answerNote": "The sentinel is tested before the two updates, and the count is tested before division."}
assert run_with_prompts(study, ["30", "45", "-1"]).endswith("Average of 2 entries: 37.50 minutes")

# ============================================================ Coding Practice
# A. Trace a digit loop
E["pa"] = {"type": "table", "xp": 1, "blanks": {
    "n1": num(305), "d1": num(5), "t1": num(5), "a1": num(30),
    "n2": num(30), "d2": num(0), "t2": num(5), "a2": num(3),
    "n3": num(3), "d3": num(3), "t3": num(8), "a3": num(0)}}
assert run("n = 305\n" + "total = 0\nwhile n > 0:\n    digit = n % 10\n    total = total + digit\n    n = n // 10\nprint(total, n)\n") == "8 0"

# B. Choose sentinels
E["pb"] = {"type": "table", "xp": 1, "blanks": {
    "ages": {"accept": ["-1", "-2", "-5", "-10", "-99", "-100", "-999", "131", "150", "200", "999", "1000"], "placeholder": "sentinel", "width": "8rem", "show": "-1"},
    "temps": {"accept": ["blank line", "a blank line", "blank", "empty string", "an empty string", "the empty string", "''", "\"\"", "done", "'done'", "\"done\"", "stop", "'stop'", "quit", "'quit'", "a word", "a word such as 'done'", "text", "none", "no numeric sentinel"],
              "placeholder": "sentinel", "width": "8rem", "show": "a blank line"},
    "ratings": {"accept": ["0", "-1", "6", "10", "99", "100", "-5", "-10"], "placeholder": "sentinel", "width": "8rem", "show": "0"}}}
E["pb-why"] = {"type": "short", "xp": 2, "answer": b64(
    "`-1` for ages because it is outside 0 through 130. A blank line for temperatures because every numeric value may be valid. `0` for ratings because it is outside 1 through 5.")}

# C. Convert a priming-read loop
words_old = "text = input('Word, or blank to finish: ')\nwhile text != '':\n    print(text.upper())\n    text = input('Word, or blank to finish: ')\n"
words = "while True:\n    text = input('Word, or blank to finish: ')\n    if text == '':\n        break\n    print(text.upper())\n"
for inputs in (["hello", "world", ""], [""], ["Ada", ""]):
    assert run_with_prompts(words_old, inputs) == run_with_prompts(words, inputs)
E["pc"] = {"type": "code", "xp": 5, "minLines": 6, "starter": words_old,
    "cases": [case("hello, world, blank", ["hello", "world", ""], words),
              case("blank first", [""], words),
              case("Ada, blank", ["Ada", ""], words)],
    "check": '''assert "while True" in __source__, "Rewrite the loop as while True with one break."
assert __source__.count("break") == 1, "Use exactly one break to leave the loop."
assert __source__.count("input(") == 1, "The input line should appear once, inside the loop."
''',
    "answer": b64(words),
    "answerNote": "The input appears once, and the blank line is tested before text.upper() is printed."}

# D. Repair sentinel placement
repair = ("total = 0.0\ncount = 0\n\nwhile True:\n    value = float(input('Value (-1 to finish): '))\n    if value == -1:\n        break\n"
          "    total = total + value\n    count = count + 1\n\nprint('Count:', count)\nprint(f'Total: {total:.1f}')\n")
repair_starter = ("total = 0.0\ncount = 0\n\nwhile True:\n    value = float(input('Value (-1 to finish): '))\n    total = total + value\n    count = count + 1\n"
                  "    if value == -1:\n        break\n\nprint('Count:', count)\nprint(f'Total: {total:.1f}')\n")
assert run_with_prompts(repair_starter, ["5", "10", "-1"]).endswith("Count: 3\nTotal: 14.0")
E["pd"] = {"type": "code", "xp": 5, "minLines": 11, "starter": repair_starter,
    "cases": [case("5, 10, -1", ["5", "10", "-1"], repair),
              case("-1 first", ["-1"], repair),
              case("2.5, -1", ["2.5", "-1"], repair)],
    "check": SENTINEL_FIRST,
    "answer": b64(repair),
    "answerNote": "The test now occurs before either update."}

# E. Complete a safe average
safe = "total = 156.0\ncount = 2\n\nif count > 0:\n    average = total / count\n    print(f'Average: {average:.2f}')\nelse:\n    print('No values were entered.')\n"
safe_starter = safe.replace("if count > 0:", "if ____________________:").replace("    print('No values were entered.')", "    ________________________________________________")
E["pe"] = {"type": "code", "xp": 2, "minLines": 8, "starter": safe_starter,
    "cases": [case("total = 156.0, count = 2", [], safe),
              {"name": "total = 0.0, count = 0", "rewrite": [["total = 156.0", "total = 0.0"], ["count = 2", "count = 0"]],
               "expected": run_with_prompts(safe.replace("total = 156.0", "total = 0.0").replace("count = 2", "count = 0"), [])},
              {"name": "total = 90.0, count = 1", "rewrite": [["total = 156.0", "total = 90.0"], ["count = 2", "count = 1"]],
               "expected": run_with_prompts(safe.replace("total = 156.0", "total = 90.0").replace("count = 2", "count = 1"), [])}],
    "check": COUNT_GUARD,
    "answer": b64(safe),
    "answerNote": "The test prevents division by zero when no data values were entered."}
assert E["pe"]["cases"][1]["expected"] == "No values were entered."

# F. Design and test a sentinel loop
study_total = ("total = 0.0\ncount = 0\n\nwhile True:\n    minutes = float(input('Study time (-1 to finish): '))\n    if minutes == -1:\n        break\n"
               "    total = total + minutes\n    count = count + 1\n\nprint('Entries:', count)\nprint(f'Total minutes: {total:.1f}')\n")
E["pf-story"] = {"type": "short", "xp": 2, "minChars": 40, "rows": 5, "placeholder": "Prompt and reply on each line, then the two output lines…", "answer": b64(
    "One storyboard:\n\n`Study time (-1 to finish): 30`\n`Study time (-1 to finish): 45`\n`Study time (-1 to finish): -1`\n`Entries: 2`\n`Total minutes: 75.0`")}
E["pf"] = {"type": "code", "xp": 10, "minLines": 12, "starter": "total = 0.0\ncount = 0\n\n# Read study times with input('Study time (-1 to finish): ') until -1.\n",
    "cases": [case("30, 45, -1", ["30", "45", "-1"], study_total),
              case("-1 first", ["-1"], study_total),
              case("0, 15, -1", ["0", "15", "-1"], study_total),
              case("120, -1", ["120", "-1"], study_total)],
    "check": SENTINEL_FIRST + '''assert __source__.count("input(") == 1, "The input line should appear once, inside the while True loop."
''',
    "answer": b64(study_total)}
E["pf-zero"] = {"type": "table", "xp": 1, "blanks": {
    "entries": {"accept": ["Entries: 0", "0"], "placeholder": "first line", "width": "10rem", "show": "Entries: 0"},
    "total": {"accept": ["Total minutes: 0.0", "0.0", "0", "Total minutes: 0"], "placeholder": "second line", "width": "12rem", "show": "Total minutes: 0.0"}}}

# G. Predict loop output
evens = "value = 2\nwhile value <= 6:\n    print(value)\n    value = value + 2\n"
E["pg"] = {"type": "table", "xp": 2, "blanks": {
    "out": {"accept": ["2 4 6", "2, 4, 6", "2,4,6", "2; 4; 6", "2 / 4 / 6", "2 4 6 (one per line)"], "placeholder": "output, separated by spaces", "width": "14rem", "show": "2 4 6"}}}
E["ex-evens"] = example(evens)
assert E["ex-evens"]["output"] == "2\n4\n6"

# H. Find the loop bugs and count the passes
forever_fixed = "number = 3\nwhile number > 0:\n    print(number)\n    number = number - 1\n"
E["ph1-why"] = {"type": "short", "xp": 1, "minChars": 10, "rows": 2, "placeholder": "Why does it never end?", "answer": b64(
    "The loop never changes `number`, so `number > 0` stays true. Add `number = number - 1` inside the loop.")}
E["ph1"] = {"type": "code", "xp": 2, "minLines": 4, "starter": "number = 3\nwhile number > 0:\n    print(number)\n",
    "cases": [{"name": "number = 3", "expected": run(forever_fixed)},
              {"name": "number = 5", "rewrite": [["number = 3", "number = 5"]], "expected": run(forever_fixed.replace("number = 3", "number = 5"))}],
    "check": '''assert "while" in __source__, "Keep the while loop and repair it."
''',
    "answer": b64(forever_fixed),
    "answerNote": "The update makes number smaller on every pass, so the condition eventually becomes false."}
assert run(forever_fixed) == "3\n2\n1"

four_fixed = "count = 0\nwhile count < 3:\n    count = count + 1\n\nprint('Passes:', count)\n"
four_starter = "count = 0\nwhile count <= 3:\n    count = count + 1\n\nprint('Passes:', count)\n"
assert run(four_starter) == "Passes: 4"
E["ph2-why"] = {"type": "short", "xp": 1, "minChars": 10, "rows": 2, "placeholder": "Why four passes?", "answer": b64(
    "The loop starts at zero and accepts 0, 1, 2, and 3. Change the test to `count < 3`.")}
E["ph2"] = {"type": "code", "xp": 2, "minLines": 4, "starter": four_starter,
    "cases": [{"name": "three passes", "expected": run(four_fixed)}],
    "check": '''assert "count = 0" in __source__, "Keep count starting at 0 and repair the test instead."
assert "while" in __source__, "Keep the while loop and repair its test."
''',
    "answer": b64(four_fixed)}

passes = "i = 1\nwhile i < 11:\n    i = i + 1\n\nj = 10\nwhile j > 0:\n    j = j - 2\n\nk = -10\nwhile k <= 10:\n    k = k + 3\n"
E["ex-passes"] = example(passes, output=False)
assert run(passes + "print(i - 1, 10 // 2, (k + 10) // 3)") == "10 5 7"
E["ph3"] = {"type": "table", "xp": 1, "blanks": {"i": num(10), "j": num(5), "k": num(7)}}

# I. Track a minimum safely
minimum = ("first = True\n\nwhile True:\n    value = int(input('Value (0 to finish): '))\n    if value == 0:\n        break\n"
           "    if first:\n        minimum = value\n        first = False\n    elif value < minimum:\n        minimum = value\n\n"
           "if first:\n    print('No values were entered.')\nelse:\n    print('Minimum:', minimum)\n")
minimum_starter = minimum.replace("    if first:\n        minimum = value", "    if ________________________________________________:\n        minimum = value").replace("elif value < minimum:", "elif _____________________________________________:")
assert sum("____" in line for line in minimum_starter.splitlines()) == 2
E["pi"] = {"type": "code", "xp": 5, "minLines": 16, "starter": minimum_starter,
    "cases": [case("4, 7, -2, -5, 0", ["4", "7", "-2", "-5", "0"], minimum),
              case("0 first", ["0"], minimum),
              case("9, 0", ["9", "0"], minimum),
              case("5, 5, 3, 0", ["5", "5", "3", "0"], minimum)],
    "check": '''assert "minimum = 0" not in __source__, "Do not start minimum at 0; let the first data value initialize it."
assert "first" in __source__, "Use the first flag to notice the first data value."
''',
    "answer": b64(minimum),
    "answerNote": "The first data value initializes minimum. Later values replace it only when they are smaller. For inputs 4, 7, -2, -5, 0, the minimum states are 4, 4, -2, -5."}

# J. Convert two currency sequences
currency = ("rate = 1.36\n\nwhile True:\n    usd = float(input('USD amount (0 to finish): '))\n    if usd == 0:\n        break\n    print(f'CAD {usd * rate:.2f}')\n\n"
            "while True:\n    cad = float(input('CAD amount (0 to finish): '))\n    if cad == 0:\n        break\n    print(f'USD {cad / rate:.2f}')\n")
E["pj"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": "rate = 1.36\n\n# First loop: input('USD amount (0 to finish): '), print CAD amounts.\n\n# Second loop: input('CAD amount (0 to finish): '), print USD amounts.\n",
    "cases": [case("10, 0, 13.60, 0", ["10", "0", "13.60", "0"], currency),
              case("0, 0", ["0", "0"], currency),
              case("5, 20, 0, 6.80, 34, 0", ["5", "20", "0", "6.80", "34", "0"], currency)],
    "check": '''import re
assert len(re.findall(r"^\\s*while\\b", __source__, re.M)) == 2, "Use two sentinel-controlled while loops, one for each currency."
assert "1.36" in __source__, "Use the rate 1.36 in both conversions."
assert ":.2f" in __source__, "Print each converted amount with two digits after the decimal point using :.2f."
''',
    "answer": b64(currency),
    "answerNote": "Each sentinel is tested before conversion. Inputs 10, 0, 13.60, 0 print CAD 13.60 and USD 10.00. Inputs 0, 0 print no conversions."}
assert "CAD 13.60" in E["pj"]["cases"][0]["expected"] and "USD 10.00" in E["pj"]["cases"][0]["expected"]

# K. Control room occupancy
room = ("capacity = 12\noccupancy = 0\n\nwhile occupancy < capacity:\n    change = int(input('Group change (0 to close): '))\n    if change == 0:\n        break\n"
        "    if change > 0 and occupancy + change > capacity:\n        print('Group cannot enter.')\n    else:\n        occupancy = occupancy + change\n        print('Occupancy:', occupancy)\n\n"
        "print('Final occupancy:', occupancy)\n")
E["pk"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": "capacity = 12\noccupancy = 0\n\n# Read each change with input('Group change (0 to close): ').\n",
    "cases": [case("5, 8, 7", ["5", "8", "7"], room),
              case("4, -2, 0", ["4", "-2", "0"], room),
              case("12", ["12"], room),
              case("0 first", ["0"], room),
              case("10, 3, -4, 6, 0", ["10", "3", "-4", "6", "0"], room)],
    "check": '''assert "capacity" in __source__, "Use the capacity name for the limit of 12."
assert __source__.count("Group cannot enter.") == 1, "Print Group cannot enter. once, when a group would exceed the capacity."
''',
    "answer": b64(room),
    "answerNote": "For 5, 8, 7, the accepted occupancies are 5 and 12. For 4, -2, 0, they are 4 and 2, and the final occupancy is 2."}

# L. Trace the minimum program
F = {"accept": ["False", "F"], "show": "False", "placeholder": "True / False", "width": "7rem"}
E["pl"] = {"type": "table", "xp": 1, "blanks": {
    "f1": dict(F), "m1": num(4), "s1": yes_no(False),
    "f2": dict(F), "m2": num(4), "s2": yes_no(False),
    "f3": dict(F), "m3": num(-2), "s3": yes_no(False),
    "f4": dict(F), "m4": num(-5), "s4": yes_no(False),
    "f5": dict(F), "m5": num(-5), "s5": yes_no(True)}}
E["pl-why"] = {"type": "short", "xp": 2, "answer": b64(
    "If `minimum` started at zero, none of the positive data values would be smaller, so the program would incorrectly print zero even though zero is only the sentinel.")}

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-13",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 13 Workbook",
    "subtitle": "Hand-tracing, sentinels, and common loop bugs",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-13/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
