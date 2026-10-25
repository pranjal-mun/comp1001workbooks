"""Build the Unit 5 (Functions) question bank: index.html and exercises.json.

Fifteen Part 2 style programming questions for term tests and the final exam,
in the boss problem layout, for the instructor to review. The page opens only in instructor mode. Each
question uses Lectures 17 to 20 and may use any earlier lecture. Sample runs
and expected outputs are produced by actually running the model solutions.
Run from anywhere:

    python3 workbooks/question-bank/functions/build_exercises.py
    python3 tools/check_workbook.py workbooks/question-bank/functions
"""
import base64, contextlib, html, io, json, subprocess, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=(), typed=False):
    """Run with scripted input() answers, echoing prompts but not the answers,
    exactly as the grader does (echoInput: false). With typed=True the answers
    are echoed between markers, for the sample runs on the page."""
    wrapper = (
        "import builtins, sys\n"
        "_answers = " + repr(list(inputs)) + "\n"
        "def _input(prompt=''):\n"
        "    sys.stdout.write(str(prompt))\n"
        "    answer = _answers.pop(0)\n"
        + ("    sys.stdout.write('\\x00' + answer + '\\x01\\n')\n" if typed else "")
        + "    return answer\n"
        "builtins.input = _input\n"
        + code
    )
    p = subprocess.run([sys.executable, "-c", wrapper], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n")

def input_cases(solution, *runs):
    return [{"name": name, "inputs": list(inputs), "expected": run(solution, inputs)} for name, inputs in runs]

def namespace(code):
    ns = {"__name__": "question_bank"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    return ns

def returns(ns, name, calls):
    """Check lines that call `name` on each argument tuple and compare with the model answer."""
    return "".join(f"_returns({name!r}, {args!r}, {ns[name](*args)!r})\n" for args in calls)

# A check runs after the student's program in a copy of its namespace. `_fn`
# finds a function the program defined; `_call` calls it with its output
# captured, so the test call does not add to the program's own output. `_guard`
# looks for the standard guard as the last statement of the file. `_local_state`
# allows only uppercase constants to be assigned at the top level.
FN = '''import types, io, contextlib, re, ast
_WORDS = ["empty parentheses", "one parameter", "two parameters", "three parameters", "four parameters", "five parameters"]
def _fn(name, *params):
    f = globals().get(name)
    assert isinstance(f, types.FunctionType), "Define a function named " + name + " with def."
    assert f.__code__.co_argcount == len(params), "Define " + name + "(" + ", ".join(params) + ") with " + _WORDS[len(params)] + "."
    return f
def _call(name, *args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        value = globals()[name](*args)
    return value, buffer.getvalue()
def _shown(name, args):
    return name + "(" + ", ".join(repr(a) for a in args) + ")"
def _returns(name, args, want):
    value, printed = _call(name, *args)
    call = _shown(name, args)
    if value is None:
        raise AssertionError(call + " returned None. Return a value on every path.")
    assert not printed, call + " printed something. Return the value and let main() print it."
    if isinstance(want, bool):
        ok = value is want
    elif isinstance(want, float):
        ok = isinstance(value, (int, float)) and not isinstance(value, bool) and abs(value - want) <= 1e-9 * max(1, abs(want))
    else:
        ok = value == want and type(value) is type(want)
    assert ok, call + " should return " + repr(want) + ", not " + repr(value) + "."
def _guard():
    _tree = ast.parse(__source__)
    _last = _tree.body[-1] if _tree.body else None
    _ok = False
    if isinstance(_last, ast.If) and not _last.orelse and isinstance(_last.test, ast.Compare):
        _sides = [_last.test.left] + list(_last.test.comparators)
        _names = [s.id for s in _sides if isinstance(s, ast.Name)]
        _texts = [s.value for s in _sides if isinstance(s, ast.Constant)]
        _call_main = (len(_last.body) == 1 and isinstance(_last.body[0], ast.Expr) and isinstance(_last.body[0].value, ast.Call)
                      and isinstance(_last.body[0].value.func, ast.Name) and _last.body[0].value.func.id == "main"
                      and not _last.body[0].value.args and not _last.body[0].value.keywords)
        _ok = (len(_sides) == 2 and isinstance(_last.test.ops[0], ast.Eq) and _names == ["__name__"]
               and _texts == ["__main__"] and _call_main)
    assert _ok, "End the file with the standard guard: if __name__ == '__main__': followed by an indented main()."
def _body(name):
    for node in ast.parse(__source__).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return list(ast.walk(node))
    return []
def _local_state():
    _tree = ast.parse(__source__)
    assert not any(isinstance(n, (ast.Global, ast.Nonlocal)) for n in ast.walk(_tree)), "Do not use global or nonlocal. Pass values as arguments and return results."
    for _n in _tree.body:
        _targets = _n.targets if isinstance(_n, ast.Assign) else [_n.target] if isinstance(_n, (ast.AugAssign, ast.AnnAssign)) else []
        for _t in _targets:
            for _m in ast.walk(_t):
                if isinstance(_m, ast.Name):
                    assert _m.id.isupper(), "Keep changing data local: assign " + _m.id + " inside a function. Only uppercase constants belong at the top level."
def _uses(caller, callee):
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == callee for n in _body(caller)), caller + " should call " + callee + " instead of repeating its work."
def _no_input(name):
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("input", "print") for n in _body(name)), name + " should not call input() or print(). Take the values as parameters and return the result."
def _keyword(caller, callee, keyword):
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == callee and any(k.arg == keyword for k in n.keywords)
               for n in _body(caller)), "In " + caller + ", call " + callee + " with the keyword argument " + keyword + "=..."
'''

E = {}   # exercise specs, by id
Q = []   # page sections, in order

def emoji(rating):
    return "👹" if rating < 3 else "👾" if rating == 3 else "🐉" if rating < 5 else "💀"

def question(qid, title, toc, lectures, rating, names, statement, reading, examples, constraints, rules, rubric, mistakes,
             solution, starter, cases, check, hints, note):
    """Record one question: its spec for the grader and its section for the page.
    `names` labels the typed values in the examples; a name starting with * takes
    all the remaining lines. `examples` is a list of (typed lines, explanation)
    pairs and must match the first cases, in order."""
    E[qid] = {"type": "code", "xp": 25, "boss": emoji(rating), "minLines": 24, "starter": starter, "cases": cases,
              "check": FN + check + "_local_state()\n_guard()\n", "hints": hints, "answer": b64(solution), "answerNote": note}
    for (inputs, _), case in zip(examples, cases):
        assert case["inputs"] == inputs, (qid, inputs)
    Q.append(dict(qid=qid, title=title, toc=toc, lectures=lectures, rating=rating, names=names, statement=statement,
                  reading=reading, examples=examples, cases=cases[len(examples):],
                  constraints=constraints, rules=rules, rubric=rubric, mistakes=mistakes, solution=solution))

# ---------------------------------------------------------------- Wind chill
windchill = """def wind_chill(temperature, wind_speed):
    if wind_speed < 5:
        return round(temperature)
    factor = wind_speed ** 0.16
    chill = 13.12 + 0.6215 * temperature - 11.37 * factor + 0.3965 * temperature * factor
    return round(chill)

def risk(chill):
    if chill <= -40:
        return 'Very high'
    elif chill <= -28:
        return 'High'
    elif chill <= -10:
        return 'Moderate'
    else:
        return 'Low'

def main():
    temperature = float(input())
    wind_speed = float(input())
    chill = wind_chill(temperature, wind_speed)
    print(f'Feels like: {chill}')
    print(f'Risk of frostbite: {risk(chill)}')

if __name__ == '__main__':
    main()
"""
ns = namespace(windchill)
question("windchill", "Wind chill in St. John's", "Wind chill", "Lectures 18 to 20; also 5 and 10", 2.5, ['temperature', 'wind_speed'],
    "<p>Given the air temperature in degrees Celsius and the wind speed in km/h, print the wind chill and the risk of frostbite. "
    "St. John's is one of the windiest cities in Canada, so its forecasts give both.</p>"
    "<p>When the wind speed is at least 5 km/h, the wind chill is "
    "<code>13.12 + 0.6215 T - 11.37 V<sup>0.16</sup> + 0.3965 T V<sup>0.16</sup></code>, "
    "where <code>T</code> is the temperature and <code>V</code> is the wind speed. Below 5 km/h the wind chill is the temperature itself. "
    "Round the wind chill to a whole number with <code>round()</code>.</p>"
    "<table><thead><tr><th>Wind chill</th><th>Risk</th></tr></thead><tbody>"
    "<tr><td>-40 or lower</td><td>Very high</td></tr><tr><td>-39 to -28</td><td>High</td></tr>"
    "<tr><td>-27 to -10</td><td>Moderate</td></tr><tr><td>-9 or higher</td><td>Low</td></tr></tbody></table>",
    'Read <code>temperature</code> and then <code>wind_speed</code> with <code>float(input())</code>, and print two lines.',
    [(["-12", "40"], "With 40 km/h of wind, -12 degrees feels like -23, which is in the Moderate band."),
     (["3", "4"], "The wind is below 5 km/h, so the wind chill is the temperature, 3.")],
    ['<code>-50 &lt;= temperature &lt;= 10</code>', '<code>0 &lt;= wind_speed &lt;= 100</code>'],
    ["Define <code>wind_chill(temperature, wind_speed)</code>; it returns the rounded wind chill.",
     "Define <code>risk(chill)</code>; it returns the risk word from an <code>if</code>/<code>elif</code>/<code>else</code> chain.",
     "Neither function calls <code>input()</code> or <code>print()</code>. <code>main()</code> reads the values, calls both functions and prints.",
     "End the file with <code>if __name__ == '__main__':</code> and <code>main()</code>. Only uppercase constants are assigned at the top level."],
    [("<code>wind_chill</code> with two parameters; the formula is correct, with <code>** 0.16</code>", 3),
     ("Below 5 km/h it returns the temperature; the result is rounded and returned, not printed", 2),
     ("<code>risk</code> returns the correct word, also at -10, -28 and -40", 2),
     ("<code>main()</code> reads and converts both values, calls the functions, prints both lines", 2),
     ("Program ends with the <code>__main__</code> guard; output matches the examples", 1)],
    "<code>wind_speed ** 1/6</code>, or <code>** 0.16</code> on the whole expression. A chain that tests <code>chill &lt;= -10</code> first, so -45 is Moderate. "
    "Printing inside <code>wind_chill</code> and then printing its <code>None</code> in <code>main()</code>.",
    windchill,
    "def wind_chill(temperature, wind_speed):\n    pass\n\ndef risk(chill):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(windchill, ("Example 1: -12 and 40", ["-12", "40"]), ("Example 2: 3 and 4", ["3", "4"]),
                ("Typed -30 and 50", ["-30", "50"]), ("Typed -20 and 30", ["-20", "30"]), ("Typed 5 and 5", ["5", "5"]),
                ("Typed -25 and 60", ["-25", "60"]), ("Typed -38.5 and 4.9", ["-38.5", "4.9"])),
    '''_fn("wind_chill", "temperature", "wind_speed")
_fn("risk", "chill")
_fn("main")
_no_input("wind_chill")
_no_input("risk")
''' + returns(ns, "wind_chill", [(-12.0, 40.0), (3.0, 4.0), (-30.0, 50.0), (0.0, 5.0), (-10.0, 0.0), (10.0, 100.0)])
    + returns(ns, "risk", [(-50,), (-40,), (-39,), (-28,), (-27,), (-10,), (-9,), (5,)]),
    ["Compute <code>factor = wind_speed ** 0.16</code> once and use it in both terms of the formula.",
     "Return early when the wind is light: <code>if wind_speed &lt; 5: return round(temperature)</code>.",
     "Start the risk chain with the coldest band, <code>chill &lt;= -40</code>, so each later test only sees warmer values."],
    "The risk chain starts at the coldest band. Starting at the warmest band with > also works.")

# ---------------------------------------------------------------- Newfoundland time
nltime = """OFFSET = 90
MINUTES_PER_DAY = 24 * 60

def to_minutes(clock):
    colon = clock.find(':')
    hours = int(clock[:colon])
    minutes = int(clock[colon + 1:])
    return hours * 60 + minutes

def to_12_hour(total):
    hours = total // 60
    minutes = total % 60
    if hours < 12:
        suffix = 'am'
    else:
        suffix = 'pm'
    hours = hours % 12
    if hours == 0:
        hours = 12
    return f'{hours}:{minutes:02d} {suffix}'

def main():
    toronto = to_minutes(input().strip())
    later = toronto + OFFSET
    newfoundland = later % MINUTES_PER_DAY
    print(f'Toronto: {to_12_hour(toronto)}')
    print(f'Newfoundland: {to_12_hour(newfoundland)}')
    if later >= MINUTES_PER_DAY:
        print('That is the next day in Newfoundland.')

if __name__ == '__main__':
    main()
"""
ns = namespace(nltime)
question("nltime", "Newfoundland time", "Newfoundland time", "Lectures 18 to 20; also 5, 7 and 10", 3, ['clock'],
    "<p>Given a time in Toronto on the 24-hour clock, such as <code>14:05</code> or <code>7:30</code>, print that time and the time in Newfoundland "
    "on the 12-hour clock, with am or pm. Newfoundland time is 1 hour and 30 minutes ahead of Toronto time.</p>"
    "<p>On the 12-hour clock, the hour 0 is shown as 12 am and the hour 12 as 12 pm, and the minutes always have 2 digits. "
    "When the Newfoundland time is past midnight, also print <code>That is the next day in Newfoundland.</code></p>",
    'Read <code>clock</code> with <code>input()</code> and print two or three lines.',
    [(["14:05"], "2:05 pm plus 1 hour 30 minutes is 3:35 pm."),
     (["23:10"], "11:10 pm plus 1 hour 30 minutes is 12:40 am, after midnight, so the next-day line is printed.")],
    ['<code>clock</code> is the hours from 0 to 23 (1 or 2 digits), a colon, then 2 digits of minutes.', 'Spaces before or after <code>clock</code> are ignored.'],
    ["Use the constants <code>OFFSET = 90</code> and <code>MINUTES_PER_DAY = 24 * 60</code> from the starter.",
     "Define <code>to_minutes(clock)</code>; it returns the minutes after midnight for a text such as <code>'7:30'</code>, using <code>find()</code> and slices.",
     "Define <code>to_12_hour(total)</code>; it returns the 12-hour text for minutes after midnight, such as <code>'7:30 am'</code>.",
     "Neither function calls <code>input()</code> or <code>print()</code>. Use <code>%</code> to wrap past midnight.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>to_minutes</code>: finds the colon, slices both parts, converts with <code>int()</code>, returns the total", 2),
     ("<code>to_12_hour</code>: hours and minutes with <code>//</code> and <code>%</code>, two-digit minutes, returns the text", 2),
     ("am/pm correct, and the hour 0 shows as 12 and the hour 12 as 12 pm", 2),
     ("Adds the offset and wraps with <code>% MINUTES_PER_DAY</code>; the next-day line only when it wraps", 2),
     ("<code>main()</code> calls the functions for both times; guard; output matches the examples", 2)],
    "<code>clock[:2]</code>, which fails for <code>7:30</code>. <code>hours % 12</code> without the 12 fix, so midnight shows as 0:15. "
    "Testing for the next day after the <code>%</code>, so the test is never true.",
    nltime,
    "OFFSET = 90\nMINUTES_PER_DAY = 24 * 60\n\ndef to_minutes(clock):\n    pass\n\ndef to_12_hour(total):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(nltime, ("Example 1: 14:05", ["14:05"]), ("Example 2: 23:10", ["23:10"]), ("Typed 0:00", ["0:00"]),
                ("Typed 7:30", ["7:30"]), ("Typed 10:30", ["10:30"]), ("Typed 22:29", ["22:29"]), ("Typed 22:30", ["22:30"]),
                ("Typed 11:45 with spaces", [" 11:45 "])),
    '''assert globals().get("OFFSET") == 90 and globals().get("MINUTES_PER_DAY") == 1440, "Keep the constants OFFSET = 90 and MINUTES_PER_DAY = 24 * 60."
_fn("to_minutes", "clock")
_fn("to_12_hour", "total")
_fn("main")
_no_input("to_minutes")
_no_input("to_12_hour")
''' + returns(ns, "to_minutes", [("0:00",), ("7:30",), ("14:05",), ("23:59",), ("12:00",)])
    + returns(ns, "to_12_hour", [(0,), (5,), (450,), (719,), (720,), (785,), (1439,)]),
    ["In <code>to_minutes</code>, <code>colon = clock.find(':')</code>. The hours are <code>clock[:colon]</code> and the minutes are <code>clock[colon + 1:]</code>.",
     "In <code>to_12_hour</code>, decide am or pm before you change the hours. Then <code>hours % 12</code>, and 0 becomes 12.",
     "Keep <code>later = toronto + OFFSET</code> before the <code>%</code>. It is at least <code>MINUTES_PER_DAY</code> exactly when the time wraps."],
    "Working in minutes after midnight makes the offset and the wrap a single + and %.")

# ---------------------------------------------------------------- Student number
studentno = """def digit_total(text):
    total = 0
    for i in range(len(text)):
        total = total + int(text[i])
    return total

def is_valid(number):
    if len(number) != 9 or not number.isdigit():
        return False
    if number[:2] != '20':
        return False
    return digit_total(number[:8]) % 10 == int(number[8])

def entry_year(number):
    return int(number[:4])

def main():
    attempts = 1
    number = input().strip()
    while not is_valid(number):
        print('Not a valid student number. Try again.')
        attempts = attempts + 1
        number = input().strip()
    print(f'Entry year: {entry_year(number)}')
    print(f'Attempts: {attempts}')

if __name__ == '__main__':
    main()
"""
ns = namespace(studentno)
question("studentno", "Memorial student number", "Student number", "Lectures 18 to 20; also 7, 11, 13 and 14", 3, ['*numbers'],
    "<p>Given student numbers typed one per line, keep reading until a valid one arrives. After each invalid number print "
    "<code>Not a valid student number. Try again.</code> Then print the entry year and the number of attempts.</p>"
    "<p>In this question, a Memorial student number is valid when all of these are true:</p>"
    "<ul><li>It has exactly 9 characters, and all of them are digits.</li><li>It starts with <code>20</code>. The first 4 digits are the year the student started.</li>"
    "<li>The last digit is a check digit: it equals the sum of the first 8 digits, mod 10.</li></ul>"
    "<p>For example, in <code>202412348</code> the first 8 digits add up to 2+0+2+4+1+2+3+4 = 18, and 18 mod 10 is 8, the last digit. So it is valid.</p>",
    'Read the student numbers one per line with <code>input()</code>, and stop at the first valid one.',
    [(["2024123", "202412345", "202412348"], "2024123 is too short. In 202412345 the check digit should be 8, not 5. 202412348 is valid on the third attempt."),
     (["202301233"], "2+0+2+3+0+1+2+3 = 13, and 13 mod 10 is 3, the last digit, so the first number is valid.")],
    ['A line can hold any characters, including letters, and can have spaces around it.', 'The last line is always a valid student number.'],
    ["Define <code>digit_total(text)</code>; it returns the sum of the digits in a text of digits, using a loop.",
     "Define <code>is_valid(number)</code>; it returns <code>True</code> or <code>False</code> and calls <code>digit_total</code>.",
     "Define <code>entry_year(number)</code>; it returns the year as an <code>int</code>.",
     "None of the three calls <code>input()</code> or <code>print()</code>. <code>main()</code> has the input loop.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>digit_total</code>: a loop that adds each digit as an <code>int</code>, returns the total", 2),
     ("<code>is_valid</code>: length 9 and all digits checked first, so no <code>int()</code> error on letters", 2),
     ("<code>is_valid</code>: starts with 20, and the check digit test calls <code>digit_total</code> on the first 8 digits", 2),
     ("<code>entry_year</code> returns <code>int(number[:4])</code>", 1),
     ("Input loop in <code>main()</code>: reads again after each invalid number and counts the attempts", 2),
     ("Guard; output matches the examples", 1)],
    "Calling <code>int()</code> on the digits before the length and digit tests, which crashes on <code>20A4</code>. "
    "Adding all 9 digits, check digit included. Counting the attempts from 0, so one good number shows 0.",
    studentno,
    "def digit_total(text):\n    pass\n\ndef is_valid(number):\n    pass\n\ndef entry_year(number):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(studentno, ("Example 1: three tries", ["2024123", "202412345", "202412348"]), ("Example 2: valid at once", ["202301233"]),
                ("Letters, then valid", ["20A412348", "abc", "202412348"]), ("Wrong start, then valid", ["192412347", "202000004"]),
                ("Too long, then spaces around a valid one", ["2024123480", "  202599995  "])),
    '''_fn("digit_total", "text")
_fn("is_valid", "number")
_fn("entry_year", "number")
_fn("main")
_uses("is_valid", "digit_total")
_no_input("digit_total")
_no_input("is_valid")
''' + returns(ns, "digit_total", [("0",), ("7",), ("20241234",), ("99999999",)])
    + returns(ns, "is_valid", [("202412348",), ("202412345",), ("2024123",), ("20241234a",), ("192412347",), ("202000004",), ("2024123480",)])
    + returns(ns, "entry_year", [("202412348",), ("201900001",)]),
    ["In <code>digit_total</code>, loop with <code>for i in range(len(text))</code> and add <code>int(text[i])</code>.",
     "In <code>is_valid</code>, return <code>False</code> early when the length is not 9 or <code>number.isdigit()</code> is false. Only then is <code>int()</code> safe.",
     "The check digit test is <code>digit_total(number[:8]) % 10 == int(number[8])</code>."],
    "The early returns in is_valid make sure int() only sees digits.")

# ---------------------------------------------------------------- COMP 1001 grade
grade = """LAB_WEIGHT = 0.30
TEST_WEIGHT = 0.20
FINAL_WEIGHT = 0.30

def course_mark(labs, test1, test2, final, bonus=0):
    mark = labs * LAB_WEIGHT + (test1 + test2) * TEST_WEIGHT + final * FINAL_WEIGHT + bonus
    if mark > 100:
        mark = 100
    return mark

def letter_grade(mark):
    if mark >= 80:
        return 'A'
    elif mark >= 65:
        return 'B'
    elif mark >= 55:
        return 'C'
    elif mark >= 50:
        return 'D'
    else:
        return 'F'

def main():
    labs = float(input())
    test1 = float(input())
    test2 = float(input())
    final = float(input())
    attended = input().strip().lower()
    if attended == 'yes':
        mark = course_mark(labs, test1, test2, final, bonus=1)
    else:
        mark = course_mark(labs, test1, test2, final)
    print(f'Course mark: {mark:.1f}')
    print(f'Letter grade: {letter_grade(mark)}')

if __name__ == '__main__':
    main()
"""
ns = namespace(grade)
question("grade", "COMP 1001 course grade", "Course grade", "Lectures 18 to 20; also 6, 9 and 10", 3, ['labs', 'test1', 'test2', 'final', 'attended'],
    "<p>Given a student's four marks and whether they attended, print the COMP 1001 course mark with 1 decimal place and the letter grade.</p>"
    "<p>The course mark is built from the lab quizzes (30%), Term Test 1 (20%), Term Test 2 (20%) and the final exam (30%). "
    "A student who attended Labs 1 to 8 and both term tests gets 1 bonus mark, but the course mark is capped at 100.</p>"
    "<table><thead><tr><th>Course mark</th><th>Letter grade</th></tr></thead><tbody>"
    "<tr><td>80 to 100</td><td>A</td></tr><tr><td>65 to under 80</td><td>B</td></tr><tr><td>55 to under 65</td><td>C</td></tr>"
    "<tr><td>50 to under 55</td><td>D</td></tr><tr><td>under 50</td><td>F</td></tr></tbody></table>",
    'Read <code>labs</code>, <code>test1</code>, <code>test2</code> and <code>final</code> with <code>float(input())</code>, then <code>attended</code> with <code>input()</code>, and print two lines.',
    [(["70", "64", "81", "77", "yes"], "21.0 + 12.8 + 16.2 + 23.1 = 73.1, plus the bonus mark is 74.1, a B."),
     (["100", "100", "99.5", "100", "YES"], "The weighted mark is 99.9. The bonus would make it 100.9, so the cap brings it to 100.0.")],
    ['<code>0 &lt;= labs, test1, test2, final &lt;= 100</code>', '<code>attended</code> is yes or no, with any capitals and spaces around it.'],
    ["Use the constants <code>LAB_WEIGHT</code>, <code>TEST_WEIGHT</code> and <code>FINAL_WEIGHT</code> from the starter inside <code>course_mark</code>.",
     "Define <code>course_mark(labs, test1, test2, final, bonus=0)</code>, with a default value of 0 for the bonus; it returns the mark, capped at 100.",
     "In <code>main()</code>, call <code>course_mark</code> with the keyword argument <code>bonus=1</code> when the student attended.",
     "Define <code>letter_grade(mark)</code> with an <code>if</code>/<code>elif</code>/<code>else</code> chain. Neither function calls <code>input()</code> or <code>print()</code>.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>course_mark</code> with the default parameter <code>bonus=0</code>; the weighted sum uses the constants", 3),
     ("The cap at 100 is applied after the bonus is added", 1),
     ("<code>main()</code> passes <code>bonus=1</code> as a keyword argument only for yes, after <code>strip()</code> and <code>lower()</code>", 2),
     ("<code>letter_grade</code> returns the correct letter, also at 80, 65, 55 and 50", 2),
     ("Mark printed with 1 decimal place; guard; output matches the examples", 2)],
    "Adding the bonus after the cap, so 100 becomes 101. Writing <code>0.3</code> and <code>0.2</code> in the formula instead of using the constants. "
    "Comparing <code>attended == 'yes'</code> without <code>strip()</code> and <code>lower()</code>.",
    grade,
    "LAB_WEIGHT = 0.30\nTEST_WEIGHT = 0.20\nFINAL_WEIGHT = 0.30\n\ndef course_mark(labs, test1, test2, final, bonus=0):\n    pass\n\n"
    "def letter_grade(mark):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(grade, ("Example 1", ["70", "64", "81", "77", "yes"]), ("Example 2", ["100", "100", "99.5", "100", "YES"]),
                ("No bonus, exactly 80", ["80", "80", "80", "80", "no"]), ("Bonus lifts 64 to 65", ["64", "64", "64", "64", " Yes"]),
                ("Fail", ["40", "45", "30", "20", "no"]), ("Exactly 50", ["50", "50", "50", "50", "No"])),
    '''assert (globals().get("LAB_WEIGHT"), globals().get("TEST_WEIGHT"), globals().get("FINAL_WEIGHT")) == (0.3, 0.2, 0.3), "Keep the three weight constants: 0.30, 0.20 and 0.30."
_f = _fn("course_mark", "labs", "test1", "test2", "final", "bonus")
assert _f.__defaults__ == (0,), "Give bonus a default value of 0: def course_mark(labs, test1, test2, final, bonus=0)."
for _c in ("LAB_WEIGHT", "TEST_WEIGHT", "FINAL_WEIGHT"):
    assert _c in _f.__code__.co_names, "Use " + _c + " in course_mark instead of writing its value again."
_fn("letter_grade", "mark")
_fn("main")
_keyword("main", "course_mark", "bonus")
_no_input("course_mark")
_no_input("letter_grade")
''' + returns(ns, "course_mark", [(70.0, 64.0, 81.0, 77.0), (70.0, 64.0, 81.0, 77.0, 1), (100.0, 100.0, 100.0, 100.0, 1), (0.0, 0.0, 0.0, 0.0)])
    + returns(ns, "letter_grade", [(100,), (80,), (79.9,), (65,), (64.5,), (55,), (54.9,), (50,), (49.9,), (0,)]),
    ["The weighted sum is <code>labs * LAB_WEIGHT + (test1 + test2) * TEST_WEIGHT + final * FINAL_WEIGHT + bonus</code>.",
     "Cap after the bonus: <code>if mark &gt; 100: mark = 100</code>, then return it.",
     "In <code>main()</code>, the two calls differ only in <code>bonus=1</code>: <code>course_mark(labs, test1, test2, final, bonus=1)</code>."],
    "The default value lets main() leave the bonus out for students who did not attend.")

# ---------------------------------------------------------------- Rain in St. John's
rain = """def rain_category(mm):
    if mm == 0:
        return 'Dry'
    elif mm < 10:
        return 'Light'
    elif mm < 25:
        return 'Moderate'
    else:
        return 'Heavy'

def main():
    days = 0
    total = 0
    wettest_day = 0
    wettest = 0
    heavy = 0
    text = input().strip()
    while text != '':
        mm = float(text)
        days = days + 1
        total = total + mm
        category = rain_category(mm)
        print(f'Day {days}: {category}')
        if category == 'Heavy':
            heavy = heavy + 1
        if days == 1 or mm > wettest:
            wettest = mm
            wettest_day = days
        text = input().strip()
    if days == 0:
        print('No days entered.')
    else:
        print(f'Average: {total / days:.1f} mm')
        print(f'Wettest: day {wettest_day} with {wettest:.1f} mm')
        print(f'Heavy days: {heavy}')

if __name__ == '__main__':
    main()
"""
ns = namespace(rain)
question("rain", "Rainy days in St. John's", "Rainy days", "Lectures 18 to 20; also 10, 13 and 16", 3, ['*rainfall'],
    "<p>Given the rainfall for a number of days in St. John's, in mm, one per line and ended by a blank line, print each day's category. "
    "Then print the average rainfall with 1 decimal place, the wettest day and its rainfall, and the number of heavy days. "
    "If two days tie for the wettest, report the first one. If the first line is blank, print <code>No days entered.</code> and nothing else.</p>"
    "<table><thead><tr><th>Rainfall</th><th>Category</th></tr></thead><tbody>"
    "<tr><td>0 mm</td><td>Dry</td></tr><tr><td>more than 0 and under 10 mm</td><td>Light</td></tr>"
    "<tr><td>10 to under 25 mm</td><td>Moderate</td></tr><tr><td>25 mm or more</td><td>Heavy</td></tr></tbody></table>",
    'Read the rainfall for each day with <code>input()</code> until a blank line.',
    [(["4.5", "0", "31", "12", "31", ""], "The total is 78.5 mm over 5 days. Days 3 and 5 tie at 31 mm, so day 3 is the wettest."),
     ([""], "The first line is blank, so there is nothing to report.")],
    ['<code>0 &lt;= rainfall &lt;= 500</code> on each day', 'A line of only spaces counts as blank.'],
    ["Define <code>rain_category(mm)</code>; it returns the category word and does not print.",
     "Use a <code>while</code> loop in <code>main()</code> that stops at the blank line.",
     "Keep the running values (count, total, wettest, heavy days) local to <code>main()</code>.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>rain_category</code> returns the correct word, also at 0, 10 and 25", 2),
     ("Sentinel loop: reads before the loop and at the end of the body; stops at the blank line", 2),
     ("Prints each day's number and category, calling <code>rain_category</code>", 1),
     ("Count, total and average correct", 2),
     ("Wettest day: keeps the first of a tie; counts heavy days", 2),
     ("<code>No days entered.</code> case; guard; output matches the examples", 1)],
    "Converting the blank line with <code>float()</code> before the test. Using <code>&gt;=</code> for the wettest day, so a tie reports the later day. "
    "Dividing by the number of days when it is 0.",
    rain,
    "def rain_category(mm):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(rain, ("Example 1", ["4.5", "0", "31", "12", "31", ""]), ("Example 2: blank at once", [""]),
                ("One dry day", ["0", ""]), ("Edges 10 and 25", ["9.9", "10", "24.9", "25", ""]),
                ("Wettest is last", ["2", "3", "40.2", " "])),
    '''_fn("rain_category", "mm")
_fn("main")
_no_input("rain_category")
assert any(isinstance(n, ast.While) for n in _body("main")), "Use a while loop in main() that stops at the blank line."
''' + returns(ns, "rain_category", [(0.0,), (0.1,), (9.9,), (10.0,), (24.9,), (25.0,), (80.0,)]),
    ["Read the first line before the loop and the next line at the end of the loop body. Convert with <code>float()</code> only inside the loop.",
     "Start the wettest day when <code>days == 1</code>, then replace it only when <code>mm &gt; wettest</code>.",
     "Test <code>days == 0</code> after the loop, before you divide."],
    "Comparing the category word returned by rain_category keeps the heavy rule in one place.")

# ---------------------------------------------------------------- Harshad numbers
harshad = """def digit_sum(n):
    total = 0
    while n > 0:
        total = total + n % 10
        n = n // 10
    return total

def is_harshad(n):
    return n % digit_sum(n) == 0

def main():
    low = int(input())
    high = int(input())
    found = ''
    count = 0
    for n in range(low, high + 1):
        if is_harshad(n):
            found = found + str(n) + ' '
            count = count + 1
    print(f'Harshad numbers: {found.strip()}')
    print(f'Count: {count}')

if __name__ == '__main__':
    main()
"""
ns = namespace(harshad)
question("harshad", "Harshad numbers", "Harshad numbers", "Lectures 18 to 20; also 5, 12 and 14", 3, ['low', 'high'],
    "<p>Given two whole numbers, print every Harshad number from the first to the second, including both, on one line with a space between them. "
    "Then print how many there are.</p>"
    "<p>A Harshad number is divisible by the sum of its own digits. 18 is one, because 1 + 8 = 9 and 18 is divisible by 9. "
    "19 is not, because 1 + 9 = 10 and 19 is not divisible by 10.</p>",
    'Read <code>low</code> and then <code>high</code> with <code>int(input())</code>, and print two lines.',
    [(["10", "30"], "Each listed number is divisible by its digit sum: 10 by 1, 12 by 3, 18 by 9, 20 by 2, 21 by 3, 24 by 6, 27 by 9 and 30 by 3."),
     (["101", "110"], "102 has digit sum 3 and 102 = 3 x 34. 101 has digit sum 2 and is odd, so it is not one.")],
    ['<code>1 &lt;= low &lt;= high &lt;= 10000</code>'],
    ["Define <code>digit_sum(n)</code>; it returns the sum of the digits, using <code>%</code> and <code>//</code> in a loop (not <code>str()</code>).",
     "Define <code>is_harshad(n)</code>; it returns <code>True</code> or <code>False</code> and calls <code>digit_sum</code>.",
     "Neither function calls <code>input()</code> or <code>print()</code>.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>digit_sum</code>: a <code>while</code> loop with <code>% 10</code> and <code>// 10</code>; returns the sum", 3),
     ("<code>is_harshad</code> returns a <code>bool</code> and calls <code>digit_sum</code>", 2),
     ("<code>main()</code>: a <code>for</code> loop over <code>range(low, high + 1)</code> that calls <code>is_harshad</code>", 2),
     ("The numbers printed on one line with spaces, and the count is correct", 2),
     ("Guard; output matches the examples", 1)],
    "<code>range(low, high)</code>, which leaves out the last number. <code>n / 10</code>, which never reaches 0 as an int. "
    "Printing inside <code>is_harshad</code> instead of returning.",
    harshad,
    "def digit_sum(n):\n    pass\n\ndef is_harshad(n):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(harshad, ("Example 1: 10 to 30", ["10", "30"]), ("Example 2: 101 to 110", ["101", "110"]),
                ("1 to 12", ["1", "12"]), ("One number, 19", ["19", "19"]), ("1000 to 1010", ["1000", "1010"])),
    '''_fn("digit_sum", "n")
_fn("is_harshad", "n")
_fn("main")
_uses("is_harshad", "digit_sum")
_no_input("digit_sum")
_no_input("is_harshad")
assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "str" for n in _body("digit_sum")), "In digit_sum, take the digits off with % 10 and // 10 instead of str()."
''' + returns(ns, "digit_sum", [(7,), (18,), (19,), (100,), (9999,), (12345,)])
    + returns(ns, "is_harshad", [(1,), (18,), (19,), (21,), (100,), (101,), (1729,)]),
    ["<code>n % 10</code> is the last digit and <code>n // 10</code> drops it. Repeat while <code>n &gt; 0</code>.",
     "<code>is_harshad</code> can be one line: <code>return n % digit_sum(n) == 0</code>.",
     "Build the line as text: <code>found = found + str(n) + ' '</code>, and <code>strip()</code> it when you print."],
    "digit_sum changes its own parameter n, which does not change the n in main(): each call has its own local variables.")

# ---------------------------------------------------------------- Password rules
password = """def count_digits(text):
    count = 0
    for i in range(len(text)):
        if text[i].isdigit():
            count = count + 1
    return count

def count_upper(text):
    count = 0
    for i in range(len(text)):
        if text[i].isupper():
            count = count + 1
    return count

def is_strong(password, min_length=8):
    return len(password) >= min_length and count_digits(password) >= 2 and count_upper(password) >= 1

def show_problems(password, min_length):
    if len(password) < min_length:
        print(f'Use at least {min_length} characters.')
    if count_digits(password) < 2:
        print('Use at least 2 digits.')
    if count_upper(password) < 1:
        print('Use at least 1 capital letter.')

def main():
    account = input().strip().lower()
    if account == 'staff':
        length = 12
    else:
        length = 8
    password = input()
    while not is_strong(password, min_length=length):
        show_problems(password, length)
        password = input()
    print('Password saved.')

if __name__ == '__main__':
    main()
"""
ns = namespace(password)
question("password", "Password rules", "Password rules", "Lectures 18 to 20; also 7, 11, 13 and 14", 3, ['account', '*passwords'],
    "<p>Given an account type and then new passwords one per line, keep reading until a strong password arrives. "
    "After each weak password, print one line for each rule it breaks, in the order of the examples. Then print <code>Password saved.</code></p>"
    "<p>A password is strong when it has at least 2 digits, at least 1 capital letter, and at least 8 characters. Staff accounts need at least 12 characters.</p>",
    'Read <code>account</code>, then the passwords one per line, with <code>input()</code>, and stop at the first strong one.',
    [(["student", "maple", "Maple2026"], "maple breaks all three rules. Maple2026 has 9 characters, 4 digits and a capital letter."),
     (["Staff", "Harbour2026", "Harbour2026!!"], "Harbour2026 has 11 characters, which is enough for a student but not for staff.")],
    ['<code>account</code> is student or staff, with any capitals and spaces around it.', 'The last password is always strong.'],
    ["Define <code>count_digits(text)</code> and <code>count_upper(text)</code>; each returns a count, using a loop.",
     "Define <code>is_strong(password, min_length=8)</code>; it returns <code>True</code> or <code>False</code> and calls both count functions.",
     "Define <code>show_problems(password, min_length)</code>, which prints the broken rules.",
     "In <code>main()</code>, call <code>is_strong</code> with the keyword argument <code>min_length=</code>. The count functions and <code>is_strong</code> do not call <code>input()</code> or <code>print()</code>.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>count_digits</code> and <code>count_upper</code>: a loop over the characters with <code>isdigit()</code> and <code>isupper()</code>", 2),
     ("<code>is_strong</code>: the default <code>min_length=8</code>; returns a <code>bool</code> from the three rules; calls both counts", 3),
     ("<code>show_problems</code>: separate <code>if</code> statements, so every broken rule is printed", 2),
     ("<code>main()</code>: 12 for staff, keyword argument <code>min_length=</code>, input loop until strong", 2),
     ("Guard; output matches the examples", 1)],
    "An <code>elif</code> chain in <code>show_problems</code>, so only the first broken rule is printed. Returning inside the loop of a count function, "
    "so it stops after the first character. Forgetting to pass the staff length to <code>show_problems</code>.",
    password,
    "def count_digits(text):\n    pass\n\ndef count_upper(text):\n    pass\n\ndef is_strong(password, min_length=8):\n    pass\n\n"
    "def show_problems(password, min_length):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(password, ("Example 1: student", ["student", "maple", "Maple2026"]), ("Example 2: staff", ["Staff", "Harbour2026", "Harbour2026!!"]),
                ("Student, strong at once", ["student", "AB12cdef"]), ("Student, one rule at a time", ["student", "abcdefgh", "abcdefg12", "Abcdefg12"]),
                ("Staff, 12 exactly", [" STAFF ", "Short1", "Longer12Pass"])),
    '''_fn("count_digits", "text")
_fn("count_upper", "text")
_s = _fn("is_strong", "password", "min_length")
assert _s.__defaults__ == (8,), "Give min_length a default value of 8: def is_strong(password, min_length=8)."
_fn("show_problems", "password", "min_length")
_fn("main")
_uses("is_strong", "count_digits")
_uses("is_strong", "count_upper")
_keyword("main", "is_strong", "min_length")
_no_input("count_digits")
_no_input("count_upper")
_no_input("is_strong")
''' + returns(ns, "count_digits", [("",), ("abc",), ("a1b2c3",), ("2026",)])
    + returns(ns, "count_upper", [("",), ("abc",), ("St. John's",), ("MUN CS",)])
    + returns(ns, "is_strong", [("Maple2026",), ("maple2026",), ("Maple2a26",), ("Mple2026",), ("Ma2026",), ("Harbour2026",), ("Harbour2026", 12), ("Harbour2026!", 12)]),
    ["A count function: start <code>count = 0</code>, loop <code>for i in range(len(text))</code>, add 1 when <code>text[i].isdigit()</code>, and return after the loop.",
     "<code>is_strong</code> can return one condition joined with <code>and</code>.",
     "Use three separate <code>if</code> statements in <code>show_problems</code>, not <code>elif</code>, so each broken rule gets its line."],
    "is_strong uses the default length for students and the keyword argument for staff.")

# ---------------------------------------------------------------- Shift cipher
cipher = """ALPHABET = 'abcdefghijklmnopqrstuvwxyz'

def shift_letter(letter, shift):
    position = ALPHABET.find(letter)
    if position == -1:
        return letter
    return ALPHABET[(position + shift) % 26]

def encode(message, shift):
    result = ''
    for i in range(len(message)):
        result = result + shift_letter(message[i], shift)
    return result

def main():
    message = input().lower()
    shift = int(input())
    secret = encode(message, shift)
    print(f'Encoded: {secret}')
    print(f'Decoded: {encode(secret, -shift)}')

if __name__ == '__main__':
    main()
"""
ns = namespace(cipher)
question("cipher", "Shift cipher", "Shift cipher", "Lectures 18 to 20; also 5, 7 and 14", 3, ['message', 'shift'],
    "<p>Given a message and a shift, change the message to lowercase and print it encoded with a shift cipher. "
    "Then decode the encoded message with the opposite shift and print it, to show it comes back.</p>"
    "<p>A shift cipher moves each letter a fixed number of places along the alphabet. With a shift of 3, <code>a</code> becomes <code>d</code>, "
    "and <code>y</code> wraps around to <code>b</code>. A negative shift moves the other way. Characters that are not letters stay as they are.</p>",
    'Read <code>message</code> with <code>input()</code> and <code>shift</code> with <code>int(input())</code>, and print two lines.',
    [(["Meet at the Bruneau Centre", "3"], "Each letter moves 3 places: m to p, e to h, t to w. The spaces stay."),
     (["COMP 1001 rocks!", "-28"], "A shift of -28 is the same as -2 after wrapping, so c becomes a and o becomes m. Digits and ! stay.")],
    ['<code>-1000 &lt;= shift &lt;= 1000</code>', '<code>message</code> can hold any characters.'],
    ["Use the constant <code>ALPHABET = 'abcdefghijklmnopqrstuvwxyz'</code> with <code>find()</code> and <code>%</code>.",
     "Define <code>shift_letter(letter, shift)</code>; it returns one shifted character.",
     "Define <code>encode(message, shift)</code>; it returns the whole shifted message and calls <code>shift_letter</code>.",
     "Neither function calls <code>input()</code> or <code>print()</code>. <code>main()</code> uses <code>encode</code> for both lines.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>shift_letter</code>: <code>find()</code> for the position; non-letters (position -1) returned unchanged", 2),
     ("<code>shift_letter</code>: wraps with <code>% 26</code>, also for negative and large shifts", 2),
     ("<code>encode</code>: builds the result in a loop, calls <code>shift_letter</code>, returns the text", 3),
     ("<code>main()</code>: lowercases the message, decodes with <code>encode(secret, -shift)</code>", 2),
     ("Guard; output matches the examples", 1)],
    "<code>ALPHABET[position + shift]</code> without <code>% 26</code>, which fails past <code>z</code>. Shifting spaces and punctuation. "
    "Writing a separate decode function that repeats <code>encode</code> instead of passing <code>-shift</code>.",
    cipher,
    "ALPHABET = 'abcdefghijklmnopqrstuvwxyz'\n\ndef shift_letter(letter, shift):\n    pass\n\ndef encode(message, shift):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(cipher, ("Example 1: shift 3", ["Meet at the Bruneau Centre", "3"]), ("Example 2: shift -28", ["COMP 1001 rocks!", "-28"]),
                ("Wrap past z", ["xyz abc", "5"]), ("Shift 0", ["Same text.", "0"]), ("Shift 26", ["full circle", "26"]), ("Shift 100", ["Signal Hill", "100"])),
    '''assert globals().get("ALPHABET") == "abcdefghijklmnopqrstuvwxyz", "Keep the constant ALPHABET = 'abcdefghijklmnopqrstuvwxyz'."
_fn("shift_letter", "letter", "shift")
_fn("encode", "message", "shift")
_fn("main")
_uses("encode", "shift_letter")
_no_input("shift_letter")
_no_input("encode")
''' + returns(ns, "shift_letter", [("a", 3), ("y", 3), ("z", 1), ("a", -1), ("m", 26), ("q", -40), (" ", 5), ("!", -3), ("7", 2)])
    + returns(ns, "encode", [("", 4), ("hello, world", 1), ("abc xyz", -3), ("st. john's", 13)]),
    ["<code>position = ALPHABET.find(letter)</code> is -1 for a character that is not a lowercase letter. Return it unchanged.",
     "The new letter is <code>ALPHABET[(position + shift) % 26]</code>. Python's <code>%</code> gives a result from 0 to 25 even for a negative shift.",
     "Decoding is encoding with the opposite shift: <code>encode(secret, -shift)</code>."],
    "One encode function does both jobs, because decoding is a shift by -shift.")

# ---------------------------------------------------------------- Campus parking
parking = """FREE_MINUTES = 15
DAY_RATE = 2.00
EVENING_RATE = 1.00
DAILY_MAX = 12.00
MINUTES_PER_DAY = 24 * 60

def day_fee(minutes, rate=DAY_RATE):
    if minutes <= FREE_MINUTES:
        return 0.0
    hours = (minutes + 59) // 60
    fee = hours * rate
    if fee > DAILY_MAX:
        fee = DAILY_MAX
    return fee

def parking_fee(minutes, rate=DAY_RATE):
    days = minutes // MINUTES_PER_DAY
    rest = minutes % MINUTES_PER_DAY
    return days * DAILY_MAX + day_fee(rest, rate)

def main():
    minutes = int(input())
    evening = input().strip().lower()
    if evening == 'yes':
        fee = parking_fee(minutes, rate=EVENING_RATE)
    else:
        fee = parking_fee(minutes)
    print(f'Fee: ${fee:.2f}')

if __name__ == '__main__':
    main()
"""
ns = namespace(parking)
question("parking", "Campus parking", "Campus parking", "Lectures 18 to 20; also 5, 6 and 10", 3.5, ['minutes', 'evening'],
    "<p>Given how many minutes a car was parked on campus and whether the evening rate applies, print the parking fee.</p>"
    "<ul><li>Each started hour costs $2.00, or $1.00 at the evening rate. So 61 minutes is 2 hours.</li>"
    "<li>A stay of 15 minutes or less is free.</li><li>The fee for one day is at most $12.00.</li>"
    "<li>A stay can be longer than a day. Each full day (1440 minutes) costs $12.00, and the minutes left over are charged by the rules above.</li></ul>",
    'Read <code>minutes</code> with <code>int(input())</code> and <code>evening</code> with <code>input()</code>, and print one line.',
    [(["130", "no"], "130 minutes is 3 started hours at $2.00."),
     (["3000", "Yes"], "3000 minutes is 2 full days ($24.00) and 120 minutes left over, which is 2 hours at $1.00.")],
    ['<code>0 &lt;= minutes &lt;= 100000</code>', '<code>evening</code> is yes or no, with any capitals and spaces around it.'],
    ["Use the constants from the starter.",
     "Define <code>day_fee(minutes, rate=DAY_RATE)</code>, the fee for a stay of less than a day.",
     "Define <code>parking_fee(minutes, rate=DAY_RATE)</code>; it calls <code>day_fee</code> for the minutes left over and passes the rate on.",
     "In <code>main()</code>, pass the evening rate as the keyword argument <code>rate=EVENING_RATE</code>. Neither fee function calls <code>input()</code> or <code>print()</code>.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>day_fee</code>: free up to 15 minutes; started hours with <code>(minutes + 59) // 60</code> or an <code>if</code> on the remainder", 3),
     ("<code>day_fee</code>: the $12.00 cap; <code>rate</code> has the default <code>DAY_RATE</code>", 2),
     ("<code>parking_fee</code>: full days with <code>//</code>, the rest with <code>%</code>, calls <code>day_fee</code> and passes the rate on", 2),
     ("<code>main()</code> uses <code>rate=EVENING_RATE</code> as a keyword argument for yes", 2),
     ("Fee with 2 decimal places; guard; output matches the examples", 1)],
    "<code>minutes // 60</code>, which charges 61 minutes as 1 hour. Calling <code>day_fee(rest)</code> in <code>parking_fee</code> without the rate, "
    "so the evening rate is lost after the first day. Applying the free 15 minutes to the whole stay instead of the minutes left over.",
    parking,
    "FREE_MINUTES = 15\nDAY_RATE = 2.00\nEVENING_RATE = 1.00\nDAILY_MAX = 12.00\nMINUTES_PER_DAY = 24 * 60\n\n"
    "def day_fee(minutes, rate=DAY_RATE):\n    pass\n\ndef parking_fee(minutes, rate=DAY_RATE):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(parking, ("Example 1: 130 minutes, day", ["130", "no"]), ("Example 2: 3000 minutes, evening", ["3000", "Yes"]),
                ("15 minutes", ["15", "no"]), ("16 minutes", ["16", "no"]), ("61 minutes", ["61", " NO "]),
                ("Cap at 6 hours", ["400", "no"]), ("Evening, 10 hours", ["600", "yes"]), ("Exactly one day", ["1440", "no"]),
                ("One day and 10 minutes, evening", ["1450", "yes"])),
    '''assert (globals().get("FREE_MINUTES"), globals().get("DAY_RATE"), globals().get("EVENING_RATE"), globals().get("DAILY_MAX"), globals().get("MINUTES_PER_DAY")) == (15, 2.0, 1.0, 12.0, 1440), "Keep the constants from the starter."
_d = _fn("day_fee", "minutes", "rate")
_p = _fn("parking_fee", "minutes", "rate")
assert _d.__defaults__ == (2.0,) and _p.__defaults__ == (2.0,), "Give rate the default value DAY_RATE in both functions."
_fn("main")
_uses("parking_fee", "day_fee")
_keyword("main", "parking_fee", "rate")
_no_input("day_fee")
_no_input("parking_fee")
''' + returns(ns, "day_fee", [(0,), (15,), (16,), (60,), (61,), (130,), (330,), (400,), (130, 1.0), (700, 1.0), (1439, 1.0)])
    + returns(ns, "parking_fee", [(130,), (1440,), (1450,), (3000, 1.0), (2900,), (4320, 1.0)]),
    ["The number of started hours is <code>(minutes + 59) // 60</code>: 60 minutes gives 1 and 61 gives 2.",
     "<code>parking_fee</code> splits the stay: <code>days = minutes // MINUTES_PER_DAY</code> and <code>rest = minutes % MINUTES_PER_DAY</code>.",
     "Pass the rate on: <code>day_fee(rest, rate)</code>. Otherwise the default day rate is used for every stay."],
    "Splitting the work in two functions lets each rule be tested on its own.")

# ---------------------------------------------------------------- Tuition payment plan
payplan = """MONTHLY_RATE = 0.01

def interest(balance):
    return balance * MONTHLY_RATE

def payment_due(owed, payment):
    if owed < payment:
        return owed
    return payment

def main():
    balance = float(input())
    payment = float(input())
    while payment <= interest(balance):
        print(f'The payment must be more than ${interest(balance):.2f}.')
        payment = float(input())
    month = 0
    total_paid = 0
    while balance > 0:
        month = month + 1
        owed = balance + interest(balance)
        paid = payment_due(owed, payment)
        balance = owed - paid
        total_paid = total_paid + paid
        print(f'Month {month}: paid ${paid:.2f}, balance ${balance:.2f}')
    print(f'Paid off in {month} months. Total paid: ${total_paid:.2f}')

if __name__ == '__main__':
    main()
"""
ns = namespace(payplan)
question("payplan", "Tuition payment plan", "Payment plan", "Lectures 18 to 20; also 6, 11, 12 and 13", 3.5, ['balance', '*payments'],
    "<p>Given a tuition balance and a monthly payment, print one line for each month until the balance is paid, then a line with the number of months and the total paid.</p>"
    "<p>In this question, at the start of each month 1% interest is added to the balance, then the payment is taken off. "
    "In the last month the student pays only what is still owed. The payment must be more than the first month's interest, or the balance would never go down: "
    "until it is, print the message in Example 2 and read the payment again. Show all money with 2 decimal places.</p>",
    'Read <code>balance</code> and then a payment with <code>float(input())</code>. Read the payment again each time it is too small.',
    [(["1000", "300"], "Month 1: 1000 + 10.00 interest = 1010.00, minus 300 leaves 710.00. In month 4 only 122.48 is owed, so that is the last payment."),
     (["500", "5", "120"], "The first month's interest is 5.00, so a payment of 5 never lowers the balance and is read again.")],
    ['<code>0 &lt; balance &lt;= 100000</code>', 'Each payment is more than 0, and the last one is always large enough.'],
    ["Use the constant <code>MONTHLY_RATE = 0.01</code> from the starter.",
     "Define <code>interest(balance)</code>; it returns one month of interest.",
     "Define <code>payment_due(owed, payment)</code>; it returns the payment, or the amount owed when that is smaller.",
     "Neither function calls <code>input()</code> or <code>print()</code>; <code>main()</code> calls both. Keep the balance, the month count and the total local to <code>main()</code>.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>interest</code> and <code>payment_due</code> return the correct values and use their parameters", 2),
     ("Validation loop: reads again while the payment is not more than the interest", 2),
     ("Each month: interest added first, then the payment taken off; the last payment is only what is owed", 3),
     ("Month count and total paid are correct", 2),
     ("Guard; money with 2 decimal places; output matches the examples", 1)],
    "Taking the payment off before the interest is added. Paying the full amount in the last month, so the balance goes below 0. "
    "An <code>if</code> instead of a <code>while</code> for the payment check, so a second bad payment is accepted.",
    payplan,
    "MONTHLY_RATE = 0.01\n\ndef interest(balance):\n    pass\n\ndef payment_due(owed, payment):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(payplan, ("Example 1", ["1000", "300"]), ("Example 2: payment too small at first", ["500", "5", "120"]),
                ("Paid in one month", ["100", "200"]), ("Two bad payments", ["2000", "10", "20", "1000"]), ("Payment equals the first amount owed", ["99", "99.99"])),
    '''assert globals().get("MONTHLY_RATE") == 0.01, "Keep the constant MONTHLY_RATE = 0.01."
_i = _fn("interest", "balance")
assert "MONTHLY_RATE" in _i.__code__.co_names, "Use MONTHLY_RATE in interest instead of writing 0.01."
_fn("payment_due", "owed", "payment")
_fn("main")
_uses("main", "interest")
_uses("main", "payment_due")
_no_input("interest")
_no_input("payment_due")
''' + returns(ns, "interest", [(0.0,), (100.0,), (1000.0,), (2550.0,)])
    + returns(ns, "payment_due", [(303.0, 300.0), (300.0, 300.0), (113.12, 300.0), (0.5, 20.0)]),
    ["Check the payment with a <code>while</code> loop before the main loop: <code>while payment &lt;= interest(balance):</code>.",
     "Each month: <code>owed = balance + interest(balance)</code>, <code>paid = payment_due(owed, payment)</code>, <code>balance = owed - paid</code>.",
     "In the last month <code>paid</code> equals <code>owed</code>, so the balance becomes exactly 0 and the loop stops."],
    "In the last month paid equals owed, so the balance is exactly 0.0 and the loop ends without a negative balance.")

# ---------------------------------------------------------------- Run-length encoding
rle = """def compress(text):
    result = ''
    count = 1
    for i in range(1, len(text)):
        if text[i] == text[i - 1]:
            count = count + 1
        else:
            result = result + text[i - 1] + str(count)
            count = 1
    return result + text[len(text) - 1] + str(count)

def expand(code):
    result = ''
    i = 0
    while i < len(code):
        letter = code[i]
        i = i + 1
        digits = ''
        while i < len(code) and code[i].isdigit():
            digits = digits + code[i]
            i = i + 1
        result = result + letter * int(digits)
    return result

def main():
    text = input()
    code = compress(text)
    print(f'Compressed: {code}')
    print(f'Expanded: {expand(code)}')
    change = len(text) - len(code)
    if change > 0:
        print(f'Shorter by {change} characters')
    elif change < 0:
        print(f'Longer by {-change} characters')
    else:
        print('Same length')

if __name__ == '__main__':
    main()
"""
ns = namespace(rle)
question("rle", "Run-length encoding", "Run-length encoding", "Lectures 18 to 20; also 7, 11, 12 and 14", 4, ['text'],
    "<p>Given a line of text, print it compressed with run-length encoding, then expand the compressed text back and print it, "
    "then say how much shorter or longer the compressed text is.</p>"
    "<p>Run-length encoding writes each run of the same character as the character followed by the length of the run. "
    "<code>WWWWBBBW</code> becomes <code>W4B3W1</code>, and a run of 12 spaces becomes a space followed by <code>12</code>. "
    "To expand, read a character, then all the digits after it as one number, and repeat the character that many times.</p>",
    'Read <code>text</code> with <code>input()</code> and print three lines.',
    [(["WWWWWWWWWWWWBWW"], "A run of 12 W, one B and two W. The code has 7 characters instead of 15, so it is 8 shorter. The 12 is read back as one number."),
     (["Hello"], "Only the two l are a run, so the code H1e1l2o1 is longer than the text.")],
    ['<code>1 &lt;= len(text) &lt;= 1000</code>', '<code>text</code> has no digits. Spaces and punctuation count like any other character.'],
    ["Define <code>compress(text)</code>; it returns the encoded text, using a loop.",
     "Define <code>expand(code)</code>; it returns the original text and handles counts of 10 or more.",
     "Neither function calls <code>input()</code> or <code>print()</code>. <code>main()</code> prints the three lines.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>compress</code>: counts each run and adds the character and <code>str(count)</code> at the end of the run", 2),
     ("<code>compress</code>: the last run is added after the loop; a text of one character works", 1),
     ("<code>expand</code>: reads all the digits after a character as one number, so counts of 10 or more work", 3),
     ("<code>expand</code>: repeats the character with <code>*</code> and returns the text", 1),
     ("<code>main()</code>: prints both results and the correct shorter, longer or same line", 2),
     ("Guard; output matches the examples", 1)],
    "Forgetting the last run after the loop, so <code>WWB</code> gives <code>W2</code>. Reading one digit at a time in <code>expand</code>, "
    "so <code>W12</code> gives one W and then fails on <code>2</code>. Comparing <code>text[i]</code> with <code>text[i + 1]</code> past the end of the text.",
    rle,
    "def compress(text):\n    pass\n\ndef expand(code):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(rle, ("Example 1", ["WWWWWWWWWWWWBWW"]), ("Example 2", ["Hello"]), ("One character", ["x"]),
                ("Spaces and punctuation", ["!!!   ...."]), ("Same length", ["aabbcc"]), ("Long run", ["z" * 105])),
    '''_fn("compress", "text")
_fn("expand", "code")
_fn("main")
_no_input("compress")
_no_input("expand")
''' + returns(ns, "compress", [("a",), ("ab",), ("aab",), ("abb",), ("WWWWBBBW",), ("x" * 12,), ("  !",)])
    + returns(ns, "expand", [("a1",), ("W4B3W1",), ("x12",), ("a10b1",), (" 3!2",), ("z105",)]),
    ["In <code>compress</code>, start <code>count = 1</code> and loop <code>for i in range(1, len(text))</code>, comparing <code>text[i]</code> with <code>text[i - 1]</code>.",
     "When a run ends, add <code>text[i - 1] + str(count)</code>. After the loop, add the last run the same way.",
     "In <code>expand</code>, use a <code>while</code> loop with an index. After a character, collect digits while <code>code[i].isdigit()</code>, then add <code>letter * int(digits)</code>."],
    "expand needs its own index because each step reads a character and a number of any length.")

# ---------------------------------------------------------------- Dining card
dining = """BONUS_FROM = 100
BONUS_RATE = 0.10

def command_word(line):
    space = line.find(' ')
    if space == -1:
        return line
    return line[:space]

def command_amount(line):
    space = line.find(' ')
    if space == -1:
        return 0.0
    return float(line[space + 1:])

def load_value(amount):
    if amount >= BONUS_FROM:
        return amount + amount * BONUS_RATE
    return amount

def main():
    balance = 0.0
    line = input().strip().lower()
    while line != '':
        word = command_word(line)
        if word == 'load':
            added = load_value(command_amount(line))
            balance = round(balance + added, 2)
            print(f'Loaded ${added:.2f}')
        elif word == 'buy':
            price = command_amount(line)
            if price <= balance:
                balance = round(balance - price, 2)
                print(f'Bought ${price:.2f}')
            else:
                print(f'Declined: balance is ${balance:.2f}')
        elif word == 'balance':
            print(f'Balance: ${balance:.2f}')
        else:
            print('Unknown command')
        line = input().strip().lower()
    print(f'Final balance: ${balance:.2f}')

if __name__ == '__main__':
    main()
"""
ns = namespace(dining)
question("dining", "Campus dining card", "Dining card", "Lectures 18 to 20; also 6, 7, 10 and 13", 4, ['*commands'],
    "<p>Given commands for a campus dining card, one per line and ended by a blank line, carry out each command and print its result. "
    "Then print the final balance. The card starts at $0.00.</p>"
    "<table><thead><tr><th>Command</th><th>What it does</th><th>Prints</th></tr></thead><tbody>"
    "<tr><td><code>load 20</code></td><td>Adds money. A load of $100 or more gets a 10% bonus.</td><td><code>Loaded $20.00</code></td></tr>"
    "<tr><td><code>buy 8.25</code></td><td>Takes the price off, if the balance is enough.</td><td><code>Bought $8.25</code>, or <code>Declined: balance is $…</code></td></tr>"
    "<tr><td><code>balance</code></td><td>Nothing changes.</td><td><code>Balance: $…</code></td></tr>"
    "<tr><td>anything else</td><td>Nothing changes.</td><td><code>Unknown command</code></td></tr></tbody></table>"
    "<p>Commands can use capital letters. After each load or purchase, round the balance to 2 decimal places with <code>round()</code>, so cents never drift.</p>",
    'Read the commands one per line with <code>input()</code> until a blank line.',
    [(["load 20", "buy 8.25", "buy 15", "BALANCE", ""], "After the first purchase $11.75 is left, so the $15 purchase is declined."),
     (["load 100", "buy 109.99", "refund 5", "balance", ""], "The $100 load gets a $10 bonus, so the $109.99 purchase goes through. refund is not a command.")],
    ['<code>load</code> and <code>buy</code> are followed by a space and an amount, with <code>0 &lt; amount &lt;= 1000</code> and at most 2 decimal places.', 'Any other line is an unknown command.'],
    ["Use the constants <code>BONUS_FROM</code> and <code>BONUS_RATE</code> from the starter.",
     "Define <code>command_word(line)</code> and <code>command_amount(line)</code>; they return the word and the amount (as a <code>float</code>, or <code>0.0</code> when there is none), using <code>find()</code> and slices.",
     "Define <code>load_value(amount)</code>; it returns the money a load adds, bonus included.",
     "None of the three calls <code>input()</code> or <code>print()</code>. <code>main()</code> has the command loop and keeps the balance.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>command_word</code> and <code>command_amount</code>: split at the first space with <code>find()</code> and slices; no space handled", 2),
     ("<code>load_value</code>: the bonus from $100 up, using the constants", 1),
     ("Sentinel loop with <code>lower()</code>; the balance is kept in <code>main()</code> and starts at 0", 2),
     ("<code>buy</code>: declined when the price is more than the balance, and the balance is unchanged", 2),
     ("<code>balance</code> and unknown commands; final balance after the loop", 2),
     ("Guard; money with 2 decimal places; output matches the examples", 1)],
    "Splitting with a fixed slice such as <code>line[4:]</code>, which only works for <code>load</code>. Taking the price off before checking the balance. "
    "Testing <code>amount &gt; 100</code> for the bonus, so exactly $100 gets none.",
    dining,
    "BONUS_FROM = 100\nBONUS_RATE = 0.10\n\ndef command_word(line):\n    pass\n\ndef command_amount(line):\n    pass\n\n"
    "def load_value(amount):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(dining, ("Example 1", ["load 20", "buy 8.25", "buy 15", "BALANCE", ""]), ("Example 2", ["load 100", "buy 109.99", "refund 5", "balance", ""]),
                ("No commands", [""]), ("Buy with an empty card", ["buy 1", "load 99.99", "buy 99.99", "balance", ""]),
                ("Many small purchases", ["load 1", "buy 0.1", "buy 0.2", "buy 0.3", "buy 0.4", "buy 0.01", "balance", ""]),
                ("Large load and capitals", ["LOAD 250", "Buy 274.5", "buy 0.51", "help", ""]),
                ("Loads that add up to the exact price", ["load 0.7", "load 0.1", "buy 0.8", "balance", ""])),
    '''assert globals().get("BONUS_FROM") == 100 and globals().get("BONUS_RATE") == 0.1, "Keep the constants BONUS_FROM = 100 and BONUS_RATE = 0.10."
_fn("command_word", "line")
_fn("command_amount", "line")
_l = _fn("load_value", "amount")
assert "BONUS_FROM" in _l.__code__.co_names and "BONUS_RATE" in _l.__code__.co_names, "Use BONUS_FROM and BONUS_RATE in load_value instead of writing their values."
_fn("main")
_no_input("command_word")
_no_input("command_amount")
_no_input("load_value")
''' + returns(ns, "command_word", [("load 20",), ("buy 8.25",), ("balance",), ("refund 5",)])
    + returns(ns, "command_amount", [("load 20",), ("buy 8.25",), ("balance",), ("buy 0.5",)])
    + returns(ns, "load_value", [(20.0,), (99.99,), (100.0,), (250.0,)]),
    ["<code>space = line.find(' ')</code>. The word is <code>line[:space]</code> and the amount is <code>float(line[space + 1:])</code>. When <code>space</code> is -1, the whole line is the word.",
     "Keep <code>balance</code> in <code>main()</code>. For <code>buy</code>, compare first: <code>if price &lt;= balance:</code>.",
     "After each change, <code>balance = round(balance + added, 2)</code> or <code>round(balance - price, 2)</code>, so 0.1 + 0.2 does not leave a tiny error."],
    "Rounding the balance after each change keeps it in whole cents, so a purchase of the exact balance is never declined.")

# ---------------------------------------------------------------- Prime gaps
primes = """def is_prime(n):
    if n < 2:
        return False
    divisor = 2
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor = divisor + 1
    return True

def next_prime(n):
    candidate = n + 1
    while not is_prime(candidate):
        candidate = candidate + 1
    return candidate

def main():
    low = int(input())
    high = int(input())
    count = 0
    twins = 0
    largest = 0
    gap_start = 0
    p = next_prime(low - 1)
    while p <= high:
        count = count + 1
        q = next_prime(p)
        if q <= high:
            if q - p == 2:
                twins = twins + 1
                print(f'Twin primes: {p} and {q}')
            if q - p > largest:
                largest = q - p
                gap_start = p
        p = q
    print(f'Primes: {count}')
    print(f'Twin pairs: {twins}')
    if largest == 0:
        print('Largest gap: none')
    else:
        print(f'Largest gap: {largest}, after {gap_start}')

if __name__ == '__main__':
    main()
"""
ns = namespace(primes)
question("primes", "Twin primes and prime gaps", "Prime gaps", "Lectures 18 to 20; also 12, 13 and 15", 4, ['low', 'high'],
    "<p>Given two whole numbers, low and high, look at the primes from low to high, including both. Print every pair of twin primes among them, "
    "in order, then the number of primes, the number of twin pairs, and the largest gap between two primes that are next to each other.</p>"
    "<p>A prime is a whole number greater than 1 whose only divisors are 1 and itself. Twin primes are two primes that differ by 2, such as 11 and 13. "
    "The gap after a prime is the distance to the next prime. Only count a pair or a gap when both primes are in the range. "
    "If two gaps tie for the largest, report the first. When there are fewer than two primes, print <code>Largest gap: none</code>.</p>",
    'Read <code>low</code> and then <code>high</code> with <code>int(input())</code>.',
    [(["10", "40"], "The primes are 11, 13, 17, 19, 23, 29, 31 and 37. The gaps after 23 and 31 are both 6, and 23 comes first."),
     (["24", "28"], "There are no primes from 24 to 28, so nothing is counted.")],
    ['<code>1 &lt;= low &lt;= high &lt;= 100000</code>'],
    ["Define <code>is_prime(n)</code>; it returns <code>True</code> or <code>False</code> and tries divisors only while <code>divisor * divisor &lt;= n</code>.",
     "Define <code>next_prime(n)</code>; it returns the smallest prime greater than <code>n</code> and calls <code>is_prime</code>.",
     "<code>main()</code> moves from prime to prime with <code>next_prime</code>. Neither function calls <code>input()</code> or <code>print()</code>.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>is_prime</code>: false below 2; a divisor loop that stops at the square root; returns a <code>bool</code>", 2),
     ("<code>next_prime</code>: starts above <code>n</code>, calls <code>is_prime</code> in a loop, returns the prime", 2),
     ("<code>main()</code>: steps through the primes in the range with <code>next_prime</code>, starting at the first prime that is at least low", 2),
     ("Twin pairs and the largest gap use only primes inside the range; ties keep the first gap", 2),
     ("Counts, the <code>none</code> case, guard; output matches the examples", 2)],
    "Counting a gap to a prime past high. Starting at <code>next_prime(low)</code>, which skips low when it is prime. "
    "A divisor loop up to <code>n</code>, which is correct but too slow for high near 100000.",
    primes,
    "def is_prime(n):\n    pass\n\ndef next_prime(n):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(primes, ("Example 1: 10 to 40", ["10", "40"]), ("Example 2: 24 to 28", ["24", "28"]), ("One prime", ["13", "16"]),
                ("Low is prime", ["2", "13"]), ("1 to 1", ["1", "1"]), ("Large range", ["99000", "100000"])),
    '''_fn("is_prime", "n")
_fn("next_prime", "n")
_fn("main")
_uses("next_prime", "is_prime")
_uses("main", "next_prime")
_no_input("is_prime")
_no_input("next_prime")
''' + returns(ns, "is_prime", [(0,), (1,), (2,), (3,), (4,), (9,), (25,), (29,), (97,), (7919,), (99991,), (99989,)])
    + returns(ns, "next_prime", [(0,), (1,), (2,), (13,), (24,), (89,), (99990,)]),
    ["In <code>is_prime</code>, return <code>False</code> below 2. Then try <code>divisor = 2, 3, ...</code> while <code>divisor * divisor &lt;= n</code>.",
     "<code>next_prime(n)</code> starts at <code>n + 1</code> and counts up until <code>is_prime</code> is true.",
     "Start with <code>p = next_prime(low - 1)</code>, so low itself counts when it is prime. Each step, <code>q = next_prime(p)</code>; use the pair only when <code>q &lt;= high</code>."],
    "next_prime(low - 1) is the first prime that is at least low, so main() never tests a number for being prime itself.")

# ---------------------------------------------------------------- Roman numerals
roman = """def digit_to_roman(digit, one, five, ten):
    if digit == 9:
        return one + ten
    if digit >= 5:
        return five + one * (digit - 5)
    if digit == 4:
        return one + five
    return one * digit

def to_roman(n):
    return (digit_to_roman(n // 1000, 'M', '', '')
            + digit_to_roman(n // 100 % 10, 'C', 'D', 'M')
            + digit_to_roman(n // 10 % 10, 'X', 'L', 'C')
            + digit_to_roman(n % 10, 'I', 'V', 'X'))

def value(letter):
    if letter == 'I':
        return 1
    elif letter == 'V':
        return 5
    elif letter == 'X':
        return 10
    elif letter == 'L':
        return 50
    elif letter == 'C':
        return 100
    elif letter == 'D':
        return 500
    elif letter == 'M':
        return 1000
    else:
        return 0

def from_roman(text):
    total = 0
    for i in range(len(text)):
        current = value(text[i])
        if i + 1 < len(text) and value(text[i + 1]) > current:
            total = total - current
        else:
            total = total + current
    return total

def is_roman(text):
    if text == '':
        return False
    for i in range(len(text)):
        if value(text[i]) == 0:
            return False
    total = from_roman(text)
    return 1 <= total <= 3999 and to_roman(total) == text

def main():
    text = input().strip().upper()
    while text != '':
        if text.isdigit():
            n = int(text)
            if 1 <= n <= 3999:
                print(f'{n} = {to_roman(n)}')
            else:
                print('Out of range: use 1 to 3999.')
        elif is_roman(text):
            print(f'{text} = {from_roman(text)}')
        else:
            print(f'{text} is not a valid Roman numeral.')
        text = input().strip().upper()

if __name__ == '__main__':
    main()
"""
ns = namespace(roman)
question("roman", "Roman numerals", "Roman numerals", "Lectures 18 to 20; also 5, 7, 10, 13 and 14", 5, ['*lines'],
    "<p>Given lines of input ended by a blank line, convert each one. A line of digits is a number to write as a Roman numeral. "
    "Any other line is a Roman numeral to convert to a number, but only if it is written correctly; otherwise print that it is not valid.</p>"
    "<p>The symbols are I = 1, V = 5, X = 10, L = 50, C = 100, D = 500 and M = 1000. Each decimal digit is written on its own, from the thousands down, "
    "with the symbols for that place: for the ones I, V and X; for the tens X, L and C; for the hundreds C, D and M; for the thousands M only.</p>"
    "<table><thead><tr><th>Digit</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>6</th><th>7</th><th>8</th><th>9</th></tr></thead><tbody>"
    "<tr><td>Ones</td><td>I</td><td>II</td><td>III</td><td>IV</td><td>V</td><td>VI</td><td>VII</td><td>VIII</td><td>IX</td></tr></tbody></table>"
    "<p>To read a numeral, add the value of each symbol, except that a symbol followed by a larger one is subtracted: in <code>XIV</code>, the I is subtracted. "
    "A numeral is valid when it uses only these symbols, its value is from 1 to 3999, and writing that value back as a Roman numeral gives the same text. "
    "So <code>IIII</code>, <code>VX</code> and <code>IC</code> are not valid.</p>",
    'Read the lines with <code>input()</code> until a blank line, and print one line for each.',
    [(["1994", "mcmxciv", "IIII", ""], "1994 is M, CM, XC, IV. The lowercase input is read as MCMXCIV. IIII reads as 4, but 4 is written IV, so IIII is not valid."),
     (["58", "LVIII", "4000", "ABC", ""], "58 is L, V, III. 4000 is out of range. A is not a Roman symbol, so ABC is not valid.")],
    ['A line of digits has no sign.', 'Spaces around a line are ignored, and lowercase letters count as capitals.'],
    ["Define <code>digit_to_roman(digit, one, five, ten)</code>; it returns one decimal digit written with the three symbols for its place.",
     "Define <code>to_roman(n)</code>, which calls <code>digit_to_roman</code> once for each place, and <code>value(letter)</code>, which returns 0 for a character that is not a symbol.",
     "Define <code>from_roman(text)</code>, which uses the subtraction rule, and <code>is_roman(text)</code>, which returns <code>True</code> or <code>False</code> and calls <code>to_roman</code> and <code>from_roman</code>.",
     "None of these five calls <code>input()</code> or <code>print()</code>. <code>main()</code> has the loop and prints.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>digit_to_roman</code>: correct for 0 to 9, using the three symbols it is given", 2),
     ("<code>to_roman</code>: splits <code>n</code> into its four digits with <code>//</code> and <code>%</code> and calls <code>digit_to_roman</code> with the right symbols", 2),
     ("<code>value</code> and <code>from_roman</code>: subtracts a symbol followed by a larger one, adds the rest", 2),
     ("<code>is_roman</code>: rejects other characters, values out of range, and numerals that do not convert back to the same text", 2),
     ("<code>main()</code>: digits or numeral, the out-of-range and not-valid messages, blank line ends", 1),
     ("Guard; output matches the examples", 1)],
    "Looking at <code>text[i + 1]</code> on the last symbol, which fails with an index error. Accepting <code>IIII</code> because it reads as 4. "
    "Repeating the same if chain three times instead of passing the symbols to <code>digit_to_roman</code>.",
    roman,
    "def digit_to_roman(digit, one, five, ten):\n    pass\n\ndef to_roman(n):\n    pass\n\ndef value(letter):\n    pass\n\n"
    "def from_roman(text):\n    pass\n\ndef is_roman(text):\n    pass\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(roman, ("Example 1", ["1994", "mcmxciv", "IIII", ""]), ("Example 2", ["58", "LVIII", "4000", "ABC", ""]),
                ("Edges", ["1", "3999", "0", "MMMCMXCIX", "MMMM", ""]), ("Subtractive pairs", ["XLIX", "IL", "VX", "XC", "CD", "  dcccxc  ", ""]),
                ("Blank at once", [""]), ("More numbers", ["444", "2026", "1001", "MXI", "MCMLXXX", ""])),
    '''_fn("digit_to_roman", "digit", "one", "five", "ten")
_fn("to_roman", "n")
_fn("value", "letter")
_fn("from_roman", "text")
_fn("is_roman", "text")
_fn("main")
_uses("to_roman", "digit_to_roman")
_uses("from_roman", "value")
_uses("is_roman", "to_roman")
_uses("is_roman", "from_roman")
for _name in ("digit_to_roman", "to_roman", "value", "from_roman", "is_roman"):
    _no_input(_name)
''' + returns(ns, "digit_to_roman", [(d, "I", "V", "X") for d in range(10)] + [(4, "X", "L", "C"), (9, "C", "D", "M"), (3, "M", "", "")])
    + returns(ns, "to_roman", [(1,), (4,), (9,), (14,), (40,), (90,), (400,), (944,), (1994,), (2026,), (3999,)])
    + returns(ns, "value", [("I",), ("V",), ("X",), ("L",), ("C",), ("D",), ("M",), ("A",), (" ",)])
    + returns(ns, "from_roman", [("III",), ("IV",), ("IX",), ("LVIII",), ("MCMXCIV",), ("MMMCMXCIX",), ("IIII",)])
    + returns(ns, "is_roman", [("XIV",), ("MCMXCIV",), ("IIII",), ("VX",), ("IC",), ("MMMM",), ("XIIV",), ("A",), ("",), ("MMMCMXCIX",)]),
    ["<code>digit_to_roman</code> has four cases: 9 is <code>one + ten</code>, 5 to 8 is <code>five</code> then <code>one</code> repeated, 4 is <code>one + five</code>, and 0 to 3 is <code>one</code> repeated.",
     "<code>to_roman</code> calls it four times: <code>(n // 1000, 'M', '', '')</code>, <code>(n // 100 % 10, 'C', 'D', 'M')</code>, <code>(n // 10 % 10, 'X', 'L', 'C')</code> and <code>(n % 10, 'I', 'V', 'X')</code>.",
     "In <code>from_roman</code>, subtract <code>value(text[i])</code> when <code>i + 1 &lt; len(text)</code> and the next symbol is larger; otherwise add it.",
     "<code>is_roman</code> checks every character with <code>value</code>, then returns <code>1 &lt;= total &lt;= 3999 and to_roman(total) == text</code>."],
    "Writing the value back with to_roman is the whole validity test: every rule about which symbols may repeat or come first is already inside to_roman.")

# ---------------------------------------------------------------- Month calendar
calendar = """MONTHS = 'JanFebMarAprMayJunJulAugSepOctNovDec'

def is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def days_in_month(month, year):
    if month == 2:
        if is_leap(year):
            return 29
        return 28
    if month == 4 or month == 6 or month == 9 or month == 11:
        return 30
    return 31

def weekday(day, month, year):
    if month < 3:
        month = month + 12
        year = year - 1
    k = year % 100
    j = year // 100
    h = (day + 13 * (month + 1) // 5 + k + k // 4 + j // 4 + 5 * j) % 7
    return (h + 6) % 7

def print_calendar(month, year):
    print(f'{MONTHS[3 * (month - 1):3 * month]} {year}')
    print('Su Mo Tu We Th Fr Sa')
    column = weekday(1, month, year)
    line = '   ' * column
    for day in range(1, days_in_month(month, year) + 1):
        line = line + f'{day:2d} '
        column = column + 1
        if column == 7:
            print(line.rstrip())
            line = ''
            column = 0
    if line != '':
        print(line.rstrip())

def regatta_day(year):
    day = 1
    while weekday(day, 8, year) != 3:
        day = day + 1
    return day

def main():
    month = int(input())
    year = int(input())
    print_calendar(month, year)
    print(f'Regatta Day {year}: August {regatta_day(year)}')

if __name__ == '__main__':
    main()
"""
ns = namespace(calendar)
question("calendar", "Month calendar and Regatta Day", "Month calendar", "Lectures 18 to 20; also 5, 6, 10, 11, 14 and 15", 5, ['month', 'year'],
    "<p>Given a month and a year, print a calendar for that month. Then print the date of Regatta Day in that year. "
    "The Royal St. John's Regatta is held on the first Wednesday in August.</p>"
    "<p>The first line is the month's 3-letter name and the year. The second line is <code>Su Mo Tu We Th Fr Sa</code>. "
    "Then each week is one line, Sunday first. Each day takes 2 characters, right-aligned, with one space between days; "
    "a week that starts after Sunday begins with 3 spaces for each empty day. Lines have no spaces at the end.</p>"
    "<p>February has 29 days in a leap year. A year is a leap year when it is divisible by 4, except years divisible by 100 that are not divisible by 400. "
    "April, June, September and November have 30 days; the other months have 31.</p>"
    "<p>To find the day of the week of a date, treat January and February as months 13 and 14 of the year before. Then, with <code>k = year % 100</code> and <code>j = year // 100</code>, "
    "<code>h = (day + 13 * (month + 1) // 5 + k + k // 4 + j // 4 + 5 * j) % 7</code> gives 0 for Saturday, 1 for Sunday, up to 6 for Friday. "
    "<code>(h + 6) % 7</code> turns that into 0 for Sunday up to 6 for Saturday.</p>",
    'Read <code>month</code> and then <code>year</code> with <code>int(input())</code>.',
    [(["8", "2026"], "August 1, 2026 is a Saturday, so the first week has six empty days. The first Wednesday is August 5."),
     (["2", "2028"], "2028 is a leap year, so February has 29 days. February 1, 2028 is a Tuesday.")],
    ['<code>1 &lt;= month &lt;= 12</code>', '<code>1900 &lt;= year &lt;= 2100</code>'],
    ["Use the constant <code>MONTHS = 'JanFebMarAprMayJunJulAugSepOctNovDec'</code> and a slice for the month name.",
     "Define <code>is_leap(year)</code>, <code>days_in_month(month, year)</code> and <code>weekday(day, month, year)</code>, which returns 0 for Sunday up to 6 for Saturday. They return values and do not print.",
     "Define <code>print_calendar(month, year)</code>, which prints the calendar, and <code>regatta_day(year)</code>, which returns the day of August and calls <code>weekday</code>.",
     "<code>days_in_month</code> calls <code>is_leap</code>, and <code>print_calendar</code> calls <code>days_in_month</code> and <code>weekday</code>.",
     "End the file with the <code>__main__</code> guard. Only uppercase constants are assigned at the top level."],
    [("<code>is_leap</code> and <code>days_in_month</code>: correct for every month, also 1900, 2000 and 2024", 2),
     ("<code>weekday</code>: January and February moved to the year before; the formula and the shift to Sunday = 0", 2),
     ("<code>print_calendar</code>: header lines, leading spaces for the first week, 2-character days, a new line after Saturday, last line printed", 3),
     ("<code>regatta_day</code>: the first day of August whose weekday is 3, found with <code>weekday</code>", 2),
     ("Guard; output matches the examples", 1)],
    "Changing <code>month</code> and <code>year</code> for January and February in <code>main()</code> instead of only inside <code>weekday</code>. "
    "Forgetting to print the last week when it does not end on a Saturday. <code>year % 4 == 0</code> alone, so 1900 is a leap year.",
    calendar,
    "MONTHS = 'JanFebMarAprMayJunJulAugSepOctNovDec'\n\ndef is_leap(year):\n    pass\n\ndef days_in_month(month, year):\n    pass\n\n"
    "def weekday(day, month, year):\n    pass\n\ndef print_calendar(month, year):\n    pass\n\ndef regatta_day(year):\n    pass\n\n"
    "def main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    input_cases(calendar, ("Example 1: August 2026", ["8", "2026"]), ("Example 2: February 2028", ["2", "2028"]),
                ("February 2015 fills four weeks", ["2", "2015"]), ("January 2000", ["1", "2000"]), ("February 1900", ["2", "1900"]),
                ("December 2100", ["12", "2100"]), ("September 2024", ["9", "2024"])),
    '''assert globals().get("MONTHS") == "JanFebMarAprMayJunJulAugSepOctNovDec", "Keep the constant MONTHS = 'JanFebMarAprMayJunJulAugSepOctNovDec'."
_fn("is_leap", "year")
_fn("days_in_month", "month", "year")
_fn("weekday", "day", "month", "year")
_fn("print_calendar", "month", "year")
_fn("regatta_day", "year")
_fn("main")
_uses("days_in_month", "is_leap")
_uses("print_calendar", "days_in_month")
_uses("print_calendar", "weekday")
_uses("regatta_day", "weekday")
for _name in ("is_leap", "days_in_month", "weekday", "regatta_day"):
    _no_input(_name)
''' + returns(ns, "is_leap", [(2024,), (2026,), (1900,), (2000,), (2100,)])
    + returns(ns, "days_in_month", [(1, 2026), (2, 2026), (2, 2028), (2, 1900), (2, 2000), (4, 2026), (9, 2026), (11, 2026), (12, 2026)])
    + returns(ns, "weekday", [(1, 8, 2026), (5, 8, 2026), (1, 2, 2028), (1, 1, 2000), (29, 2, 2024), (31, 12, 2099), (1, 3, 1900)])
    + returns(ns, "regatta_day", [(2026,), (2027,), (2028,), (2000,), (2100,)]),
    ["Test the weekday function on its own first: <code>weekday(1, 8, 2026)</code> should be 6 (Saturday) and <code>weekday(1, 1, 2000)</code> should be 6 too.",
     "In <code>print_calendar</code>, start the first line with <code>'   ' * column</code>, where <code>column = weekday(1, month, year)</code>.",
     "Add each day with <code>f'{day:2d} '</code> and add 1 to <code>column</code>. When it reaches 7, print the line with <code>rstrip()</code> and start an empty one.",
     "After the loop, print the last line if it is not empty. <code>regatta_day</code> counts up from day 1 until <code>weekday(day, 8, year) == 3</code>."],
    "weekday changes its own month and year parameters for January and February; the caller's values do not change.")

# ---------------------------------------------------------------- page
def esc(text):
    return html.escape(text, quote=False)

def typed(value):
    """One typed line as the boss pages show it: blank for an empty line, quotes when spaces surround it."""
    if value.strip() == "":
        return "blank"
    return f'"{value}"' if value != value.strip() else value

def named(names, inputs):
    """The Input line of an example, such as temperature = -12, wind_speed = 40."""
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
  <title>COMP 1001 – Question Bank: Functions</title>
  <link rel="icon" href="../../../runtime/img/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="../../../runtime/img/favicon-32.png" type="image/png" sizes="32x32">
  <link rel="stylesheet" href="../../../runtime/workbook.css">
  <script type="module">
    // Instructor only: anyone else is sent back to the workbooks page.
    import { initInstructor, isInstructor } from "../../../runtime/instructor.js";
    import { initWorkbook } from "../../../runtime/workbook.js";
    initInstructor();
    if (isInstructor()) initWorkbook({ id: "bank-functions", specs: "./exercises.json" });
    else location.replace("../../../index.html");
  </script>
</head>
<body>
<main>

<div class="wb-title-block">
  <div>
    <div class="wb-course">COMP 1001: Introduction to Programming</div>
    <h1>Question Bank: Functions</h1>
    <div class="wb-subtitle">Unit 5, Lectures 17 to 20, with earlier material</div>
    <p class="wb-meta">Pranjal Patra<br>Department of Computer Science, Memorial University of Newfoundland</p>
  </div>
  <img src="../../../runtime/img/mun-logo.svg" alt="Memorial University of Newfoundland">
</div>

<section class="wb-outcomes">
  <h2 id="about" data-toc-title="About this bank">About this bank</h2>
  <p>{count} programming questions in the style of Part 2 of a term test, each worth 10 points, for term tests and the final exam. Each one asks for a complete program
  with functions that take parameters and return values, a <code>main()</code> function, and the <code>__main__</code> guard. Some use default and keyword arguments.
  Earlier material (strings, decisions, loops, input validation) is used freely. Nothing needs lists, exceptions or files.</p>
  <p>The questions are in order of difficulty, from 👹 to 💀: {spread}. Each one has the statement, two examples, the constraints, the rules the checker enforces,
  and, after the editor, a marking rubric and the common mistakes. <strong>Check</strong> runs the program on the examples and more inputs, and also calls each function
  directly, so a function that prints instead of returning does not pass. <strong>Open in PyLab</strong> shows the question beside a full-screen editor.</p>
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

(HERE / "exercises.json").write_text(json.dumps({"id": "bank-functions", "course": "COMP 1001", "title": "Question Bank: Functions",
    "subtitle": "Unit 5, Lectures 17 to 20", "exercises": E}, indent=2, ensure_ascii=False) + "\n")
(HERE / "index.html").write_text(PAGE.replace("{count}", str(len(Q))).replace("{spread}", spread)
                                     .replace("{sections}", "<hr>\n\n".join(section(n, q) for n, q in enumerate(Q, 1))))
print(f"wrote {len(E)} questions: {spread}")
