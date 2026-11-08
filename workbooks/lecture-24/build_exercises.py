"""Build workbooks/lecture-24/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_24_SHARED_CONTENT.tex; model answers follow its \\solution{...}
text. Run from anywhere:

    python3 workbooks/lecture-24/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-24
"""
import base64, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, ok=True):
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    if ok:
        assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n"), p.stderr

def out(code):
    return run(code)[0]

def example(code, output=True):
    spec = {"type": "example", "code": code.rstrip("\n")}
    if output:
        spec["output"] = out(code)
    return spec

def accept(*values, width="8rem", placeholder="answer", show=None):
    spec = {"accept": list(values), "placeholder": placeholder, "width": width}
    if show is not None:
        spec["show"] = show
    return spec

def lst(text, width="10rem", placeholder="list"):
    """A blank for a printed list: accept it with or without spaces after the commas."""
    return accept(text, text.replace(", ", ","), width=width, placeholder=placeholder, show=text)

def short(answer, xp=2, min_chars=15, rows=3, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

def rewritten(code, pairs):
    for old, new in pairs:
        assert old in code, old
        code = code.replace(old, new)
    return code

def case(name, code, pairs=()):
    spec = {"name": name, "expected": out(rewritten(code, pairs))}
    if pairs:
        spec["rewrite"] = [list(p) for p in pairs]
    return spec

# A check runs after the student's program in a copy of its namespace.
# `_calls(method)` counts method calls such as .append(...). `_slices()`
# lists the slice nodes. `_index_set(name)` is true when the file assigns to
# an element such as name[i] = ... `_literal_lists()` finds list displays
# that hold elements.
AST = '''import ast
_TREE = ast.parse(__source__)
def _calls(method):
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == method]
def _func_calls(name):
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name]
def _slices():
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.Slice)]
def _index_set(name):
    for n in ast.walk(_TREE):
        targets = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AugAssign) else []
        for t in targets:
            if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == name and not isinstance(t.slice, ast.Slice):
                return True
    return False
def _loops():
    return [n for n in ast.walk(_TREE) if isinstance(n, (ast.For, ast.While))]
def _literal_lists():
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.List) and n.elts]
def _assigned(name):
    return [n for n in ast.walk(_TREE) if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign))
            and any(isinstance(t, ast.Name) and t.id == name for t in (n.targets if isinstance(n, ast.Assign) else [n.target]))]
'''

E = {}

# ============================================================ 1. Values, indexes, and length
E["ex-create"] = example('''marks = [72, 85, 63, 90]
names = ["Ada", "Alan", "Grace"]
empty = []
also_empty = list()
letters = list("cat")
''', output=False)
E["ex-index"] = example('''marks = [72, 85, 63, 90]
print(marks[0])
print(marks[2])
print(marks[-1])
''')
assert E["ex-index"]["output"] == "72\n63\n90"
E["ex-length"] = example('''marks = [72, 85, 63, 90]
i = 4
if 0 <= i and i < len(marks):
    print(marks[i])
else:
    print("Outside the list")
''')
assert E["ex-length"]["output"] == "Outside the list"
assert "IndexError" in run("marks = [72, 85, 63, 90]\nprint(marks[4])\n", ok=False)[1]

# ============================================================ 2. Mutable lists and immutable strings
E["ex-replace"] = example('''marks = [72, 85, 63, 90]
marks[0] = 100
print(marks)
''')
assert E["ex-replace"]["output"] == "[100, 85, 63, 90]"
string_error = '''word = "cat"
word[0] = "b"
'''
assert "TypeError" in run(string_error, ok=False)[1]
E["ex-string-error"] = example(string_error, output=False)
E["ex-new-string"] = example('''word = "cat"
word = "b" + word[1:]
print(word)
''')
assert E["ex-new-string"]["output"] == "bat"

# ============================================================ 3. Loops with values or indexes
E["ex-value-loop"] = example('''marks = [72, 85, 63]
for mark in marks:
    print(mark)
''')
E["ex-value-assign"] = example('''marks = [72, 85, 63]
for mark in marks:
    mark = mark + 5
print(marks)
''')
assert E["ex-value-assign"]["output"] == "[72, 85, 63]"
E["ex-index-loop"] = example('''marks = [72, 85, 63]
for i in range(len(marks)):
    marks[i] = marks[i] + 5
print(marks)
''')
assert E["ex-index-loop"]["output"] == "[77, 90, 68]"

# Checkpoint 1
cp1 = '''marks = [72, 85, 63, 90]
marks[-1] = 95
for i in range(len(marks)):
    marks[i] = marks[i] + 5
    print(i, marks[i])
'''
assert out(cp1) == "0 77\n1 90\n2 68\n3 100"
E["cp1"] = {"type": "code", "xp": 5, "minLines": 6,
    "starter": "marks = [72, 85, 63, 90]\n# Change the elements and print each index and value.\n",
    "cases": [case("marks = [72, 85, 63, 90]", cp1)],
    "check": AST + '''assert _loops(), "Use a loop to add 5 to each element."
assert _index_set("marks"), "Change the elements of marks with index assignment, such as marks[i] = marks[i] + 5."
assert marks == [77, 90, 68, 100], "Change the list itself. At the end, marks should be [77, 90, 68, 100], not " + repr(marks) + "."
''',
    "answer": b64(cp1),
    "answerNote": "The code sets marks[-1] to 95 before the loop starts."}
cp1_ns = {}
exec(cp1.replace("print(i, marks[i])", "pass"), cp1_ns)
assert cp1_ns["marks"] == [77, 90, 68, 100]
E["cp1-final"] = {"type": "table", "xp": 1, "blanks": {"final": lst("[77, 90, 68, 100]", width="12rem")}}

# ============================================================ 4. Adding elements
E["ex-append-insert"] = example('''names = ["Ada", "Grace"]
names.append("Lin")
names.insert(1, "Alan")
print(names)
''')
assert E["ex-append-insert"]["output"] == "['Ada', 'Alan', 'Grace', 'Lin']"
E["ex-extend"] = example('''a = [10, 20]
a.extend([30, 40])
print(a)
''')
E["ex-append-list"] = example('''b = [10, 20]
b.append([30, 40])
print(b)
''')
assert E["ex-append-list"]["output"] == "[10, 20, [30, 40]]"

# ============================================================ 5. Removing elements
# The table rows, each from a new list.
for op, after in (("items.remove(10)", [20, 10, 30]), ("items.pop()", [10, 20, 10]),
                  ("items.pop(1)", [10, 10, 30]), ("del items[1]", [10, 10, 30])):
    ns = {"items": [10, 20, 10, 30]}
    exec(op, ns)
    assert ns["items"] == after
E["ex-pop-remove"] = example('''items = [10, 20, 10, 30]
served = items.pop(1)
items.remove(10)
del items[-1]
print(served)
print(items)
''')
assert E["ex-pop-remove"]["output"] == "20\n[10]"

# ============================================================ 6. Searching a list
E["ex-search"] = example('''marks = [72, 85, 72, 90]
print(72 in marks)
print(marks.index(72))
print(marks.count(72))
if 63 in marks:
    print(marks.index(63))
else:
    print("63 is absent")
''')
assert E["ex-search"]["output"] == "True\n0\n2\n63 is absent"
assert "ValueError" in run("marks = [72, 85, 72, 90]\nmarks.index(63)\n", ok=False)[1]

# Checkpoint 2
cp2 = '''queue = ["Ada", "Ben", "Ada"]
queue.append("Chen")
served = queue.pop(0)
print(served)
if "Ada" in queue:
    print(queue.index("Ada"))
    print(queue.count("Ada"))
print(queue)
'''
assert out(cp2) == "Ada\n1\n1\n['Ben', 'Ada', 'Chen']"
E["cp2"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": 'queue = ["Ada", "Ben", "Ada"]\n# Change the queue, then print the search results.\n',
    "cases": [case('queue = ["Ada", "Ben", "Ada"]', cp2)],
    "check": AST + '''assert _calls("append"), "Add Chen at the end with append."
assert _calls("pop"), "Remove the first name with pop(0)."
assert _calls("index"), "Find the first index of Ada with index."
assert _calls("count"), "Count the matches of Ada with count."
assert any(isinstance(n, ast.Compare) and any(isinstance(o, ast.In) for o in n.ops) for n in ast.walk(_TREE)), "Test whether Ada is in queue with in before you call index."
''',
    "answer": b64(cp2),
    "answerNote": "The code removes the first Ada. The second Ada is at index 1."}

# ============================================================ 7. Slices and separate lists
E["ex-slices"] = example('''marks = [72, 85, 63, 90]
print(marks[1:3])
print(marks[:2])
print(marks[-2:])
print(marks[:])
''')
assert E["ex-slices"]["output"] == "[85, 63]\n[72, 85]\n[63, 90]\n[72, 85, 63, 90]"
E["ex-slice-copy"] = example('''marks = [72, 85, 63, 90]
part = marks[1:3]
part[0] = 100
print(marks)
print(part)
''')
assert E["ex-slice-copy"]["output"] == "[72, 85, 63, 90]\n[100, 63]"

# ============================================================ 8. Two names for one list
E["ex-alias"] = example('''a = [10, 20, 30]
b = a
b[1] = 99
print(a)
print(b)
''')
assert E["ex-alias"]["output"] == "[10, 99, 30]\n[10, 99, 30]"
E["ex-alias-trace"] = example('''marks = [60, 70, 80]
backup = marks
backup.append(90)
marks[0] = 65
removed = backup.pop(1)
print(marks)
print(removed)
''')
assert E["ex-alias-trace"]["output"] == "[65, 80, 90]\n70"

# ============================================================ 9. Making a separate copy
E["ex-copy"] = example('''a = [10, 20, 30]
b = a[:]
b[1] = 99
print(a)
print(b)
''')
assert E["ex-copy"]["output"] == "[10, 20, 30]\n[10, 99, 30]"

# Checkpoint 3
cp3 = '''scores = [60, 70, 80, 90]
saved = scores[:]
middle = scores[1:3]
middle[0] = 0
scores[-1] = 100
print(scores)
print(saved)
print(middle)
'''
assert out(cp3) == "[60, 70, 80, 100]\n[60, 70, 80, 90]\n[0, 80]"
assert out(cp3.replace("saved = scores[:]", "saved = scores")).split("\n")[1] == "[60, 70, 80, 100]"
E["cp3"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "scores = [60, 70, 80, 90]\n# Make the copy and slice, then change and print the lists.\n",
    "cases": [case("scores = [60, 70, 80, 90]", cp3)],
    "check": AST + '''assert saved is not scores, "Make saved a separate copy, such as scores[:]. The assignment saved = scores only gives the same list a second name."
assert any(n.lower is not None or n.upper is not None for n in _slices()), "Use a slice such as scores[1:3] to make middle."
assert middle is not scores and middle is not saved, "Make middle with a slice. A slice is a new list."
''',
    "answer": b64(cp3),
    "answerNote": "If you use saved = scores, the second output is [60, 70, 80, 100]. middle remains a separate list."}
E["cp3-alias"] = short("The second line becomes [60, 70, 80, 100]. Both names refer to one list, so the change to scores[-1] shows through saved. middle remains a separate list.",
                       min_chars=15, placeholder="The output with saved = scores…")

# ============================================================ 10. Common list errors
E["ex-append-none"] = example('''marks = [72, 85]
marks = marks.append(90)
print(marks)
''')
assert E["ex-append-none"]["output"] == "None"
E["ex-append-fix"] = example('''marks = [72, 85]
marks.append(90)
''', output=False)
E["ex-remove-loop"] = example('''items = [0, 0, 1]
for item in items:
    if item == 0:
        items.remove(item)
print(items)
''')
assert E["ex-remove-loop"]["output"] == "[0, 1]"

# ============================================================ Coding Practice
# 1. Build number patterns
p1 = '''values = []
for number in range(0, 16, 3):
    values.append(number)
print(values)

values = []
for number in range(1, 6):
    values.append(number * number)
print(values)

values = []
for i in range(8):
    values.append(i % 2)
print(values)
'''
assert out(p1) == "[0, 3, 6, 9, 12, 15]\n[1, 4, 9, 16, 25]\n[0, 1, 0, 1, 0, 1, 0, 1]"
E["p1"] = {"type": "code", "xp": 5, "minLines": 14,
    "starter": "values = []\n",
    "cases": [case("Three lists", p1)],
    "check": AST + '''assert len(_loops()) >= 3, "Write three loops, one for each list."
assert len(_calls("append")) >= 3, "Use append in each loop to add one element per pass."
assert not _literal_lists(), "Build each list with append in a loop. Start each list with values = [] and do not type the elements."
''',
    "answer": b64(p1),
    "answerNote": "Each loop adds one element per pass."}

# 2. Shift elements by index
shift_a = '''values = [5, 8, 2, 9]
for i in range(1, len(values)):
    values[i] = values[i - 1]
print(values)
'''
shift_b = '''values = [5, 8, 2, 9]
for i in range(len(values) - 1, 0, -1):
    values[i] = values[i - 1]
print(values)
'''
E["ex-shift-a"] = example(shift_a, output=False)
E["ex-shift-b"] = example(shift_b, output=False)
assert out(shift_a) == "[5, 5, 5, 5]" and out(shift_b) == "[5, 5, 8, 2]"
def passes(code):
    """i and the list after each pass of the loop."""
    trace = code.replace("    values[i] = values[i - 1]\n", "    values[i] = values[i - 1]\n    print(i, values)\n")
    return [line.split(" ", 1) for line in out(trace).split("\n")[:-1]]
TRACE_A = passes(shift_a)
TRACE_B = passes(shift_b)
assert TRACE_A == [["1", "[5, 5, 2, 9]"], ["2", "[5, 5, 5, 9]"], ["3", "[5, 5, 5, 5]"]]
assert TRACE_B == [["3", "[5, 8, 2, 2]"], ["2", "[5, 8, 8, 2]"], ["1", "[5, 5, 8, 2]"]]
blanks = {}
for tag, trace in (("a", TRACE_A), ("b", TRACE_B)):
    for k, (i, values) in enumerate(trace, 1):
        blanks[f"{tag}i{k}"] = accept(i, width="4rem", placeholder="i")
        blanks[f"{tag}v{k}"] = lst(values, width="11rem")
E["p2-table"] = {"type": "table", "xp": 1, "blanks": blanks}
E["p2-why"] = short("Script A prints [5, 5, 5, 5]. Script B prints [5, 5, 8, 2].\n\n"
                    "Script B moves every element one index to the right. Index 0 keeps its old value.\n\n"
                    "Script A goes forward. Each pass reads an element that the previous pass already replaced. "
                    "So the value 5 goes into every index.\n\n"
                    "Script B goes backward. Each pass reads an element before the loop replaces it.",
                    min_chars=30, rows=4, placeholder="Which script moves every element, and why the other does not…")

# 3. Keep three independent copies
p3 = '''prices = [8, 12, 5]
first = prices[:]
second = prices.copy()
third = []
for price in prices:
    third.append(price)
prices[-1] = 9
print(prices)
print(first)
print(second)
print(third)
'''
assert out(p3) == "[8, 12, 9]\n[8, 12, 5]\n[8, 12, 5]\n[8, 12, 5]"
P3_OTHER = [("prices = [8, 12, 5]", "prices = [4, 7, 1, 20]")]
E["p3"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": "prices = [8, 12, 5]\n",
    "cases": [case("prices = [8, 12, 5]", p3), case("prices = [4, 7, 1, 20]", p3, P3_OTHER)],
    "check": AST + '''assert any(n.lower is None and n.upper is None and n.step is None for n in _slices()), "Make first with a full slice: prices[:]."
assert _calls("copy"), "Make second with prices.copy()."
assert _loops() and _calls("append"), "Make third with a loop and append: start with third = [] and add each price."
assert not _func_calls("list"), "Do not use list() in this practice."
for _name in ("first", "second", "third"):
    assert _name in globals() and isinstance(globals()[_name], list), "Make a list named " + _name + "."
    assert globals()[_name] is not prices, "Make " + _name + " a separate copy. Do not assign prices to it."
''',
    "answer": b64(p3),
    "answerNote": "Each copy keeps the original last price."}

# 4. Repair two index loops
bug_a = '''values = [3, 6, 9]
for i in range(1, len(values) + 1):
    values[i] = i * i
print(values)
'''
bug_b = '''values = []
for i in range(3):
    values[i] = (i + 1) * (i + 1)
print(values)
'''
E["ex-bug-a"] = example(bug_a, output=False)
E["ex-bug-b"] = example(bug_b, output=False)
assert "IndexError" in run(bug_a, ok=False)[1] and "IndexError" in run(bug_b, ok=False)[1]
E["p4-errors"] = {"type": "table", "xp": 1, "blanks": {
    "ai": accept("3", width="5rem", placeholder="index"),
    "ae": accept("IndexError", width="9rem", placeholder="error"),
    "bi": accept("0", width="5rem", placeholder="index"),
    "be": accept("IndexError", width="9rem", placeholder="error"),
}}
E["p4-valid"] = short("Script A: its valid indexes are 0, 1, 2, -3, -2, and -1.\n\n"
                      "Script B: its empty list has no valid indexes.",
                      min_chars=15, placeholder="The valid indexes for each script…")
fix_a = '''values = [3, 6, 9]
for i in range(len(values)):
    values[i] = (i + 1) * (i + 1)
print(values)
'''
fix_b = '''values = []
for i in range(3):
    values.append((i + 1) * (i + 1))
print(values)
'''
p4 = fix_a + "\n" + fix_b
assert out(p4) == "[1, 4, 9]\n[1, 4, 9]"
E["p4"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "# Script A\n" + bug_a + "\n# Script B\n" + bug_b,
    "cases": [case("Both scripts", p4)],
    "check": AST + '''assert len(_loops()) >= 2, "Keep both scripts, each with its loop."
assert _index_set("values"), "In Script A, replace the existing elements with index assignment, such as values[i] = ..."
assert _calls("append"), "In Script B, add the new elements with append. The empty list has no index to assign."
assert not [n for n in _literal_lists() if len(n.elts) == 3 and all(isinstance(e, ast.Constant) and e.value in (1, 4, 9) for e in n.elts)], "Compute the squares in the loop. Do not type [1, 4, 9]."
''',
    "answer": b64(p4),
    "answerNote": "Each corrected script prints [1, 4, 9]. The first replaces existing elements. The second adds new elements."}

# 5. Save, reset, and empty
p5 = '''readings = [14, 9, 18, 7]
saved = readings.copy()
for i in range(len(readings)):
    readings[i] = 0
print(readings)
print(saved)
while len(readings) > 0:
    readings.pop()
print(readings)
'''
assert out(p5) == "[0, 0, 0, 0]\n[14, 9, 18, 7]\n[]"
P5_OTHER = [("readings = [14, 9, 18, 7]", "readings = [3, 5, 8, 13, 21, 34]")]
E["p5"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "readings = [14, 9, 18, 7]\n",
    "cases": [case("readings = [14, 9, 18, 7]", p5), case("readings = [3, 5, 8, 13, 21, 34]", p5, P5_OTHER)],
    "check": AST + '''assert len(_assigned("readings")) == 1, "Do not assign a new list to readings. Change the elements of the same list."
assert _index_set("readings"), "Reset each element with index assignment in a loop, such as readings[i] = 0."
assert _calls("pop"), "Empty the list with pop in a loop."
assert not _calls("clear") and not any(isinstance(n, ast.Delete) for n in ast.walk(_TREE)), "Remove the elements with pop in a loop, not with clear or del."
assert isinstance(globals().get("saved"), list) and saved is not readings, "Save a separate copy in saved, such as readings.copy()."
''',
    "answer": b64(p5),
    "answerNote": "The copy keeps the readings. The removal loop checks the current length before each pop."}

# 6. Print four selections
p6 = '''values = [9, 4, 11, 6, 2, 7, 8, 5, 10, 3]
for i in range(0, len(values), 2):
    print(values[i], end=" ")
print()
for value in values:
    if value % 2 == 0:
        print(value, end=" ")
print()
for i in range(len(values) - 1, -1, -1):
    print(values[i], end=" ")
print()
print(values[0], values[-1])
'''
assert [line.rstrip() for line in out(p6).split("\n")] == ["9 11 2 8 10", "4 6 2 8 10", "3 10 5 8 7 2 6 11 4 9", "9 3"]
P6_OTHER = [("values = [9, 4, 11, 6, 2, 7, 8, 5, 10, 3]", "values = [12, 7, 3, 20, 15, 6, 1]")]
E["p6"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": "values = [9, 4, 11, 6, 2, 7, 8, 5, 10, 3]\n",
    "cases": [case("values = [9, 4, 11, 6, 2, 7, 8, 5, 10, 3]", p6),
              case("values = [12, 7, 3, 20, 15, 6, 1]", p6, P6_OTHER)],
    "check": AST + '''assert not _calls("reverse") and not _func_calls("reversed"), "Print the reverse order with an index loop that counts down. Do not use reverse or reversed."
assert not [n for n in _slices() if n.step is not None and isinstance(n.step, ast.UnaryOp)], "Print the reverse order with an index loop that counts down, not with a slice such as values[::-1]."
''',
    "answer": b64(p6),
    "answerNote": "The first line selects positions. The second selects values."}

# ---------------------------------------------------------------- quick checks
# Understanding questions after each section: predict the output, fill in
# the gaps, multiple choice, and true or false. Each blank is worth 1 XP.
# Predict answers come from running the code.
def predict(code):
    blanks = {}
    for i, line in enumerate(out(code).split("\n"), 1):
        blanks[f"l{i}"] = lst(line, width="12rem", placeholder="output") if line.startswith("[") else accept(line, placeholder="output")
    return {"type": "table", "xp": 1, "blanks": blanks}

def true_false(*answers):
    forms = {True: ["True", "T"], False: ["False", "F"]}
    return {"type": "table", "xp": 1, "blanks": {f"t{i}": accept(*forms[a], width="6rem", placeholder="True or False", show=forms[a][0]) for i, a in enumerate(answers, 1)}}

def choice(letter):
    return {"type": "table", "xp": 1, "blanks": {"c": accept(letter, f"({letter})", f"{letter})", width="4rem", placeholder="letter", show=letter)}}

def gaps(**blanks):
    return {"type": "table", "xp": 1, "blanks": {name: accept(*forms, width=width, placeholder="code", show=forms[0]) for name, (forms, width) in blanks.items()}}

E["q1"] = predict('''nums = [4, 8, 15, 16, 23]
print(nums[1] + nums[-2])
print(len(nums))''')
E["q2"] = true_false(True, False)
E["q3"] = choice("B")
E["q4"] = true_false(True, False)
E["q5"] = predict('''nums = [1, 2, 3]
for n in nums:
    n = n * 10
print(nums)
for i in range(len(nums)):
    nums[i] = nums[i] * 10
print(nums)''')
E["q6"] = gaps(a=(['range(len(vals))', 'range(0, len(vals))'], "12rem"), b=(['vals[i] * 2', '2 * vals[i]', 'vals[i] + vals[i]'], "10rem"))
E["q7"] = predict('''a = [5, 6]
a.insert(0, 4)
a.append(7)
a.insert(2, 9)
print(a)
print(len(a))''')
E["q8"] = choice("B")
E["q9"] = predict('''items = [3, 1, 3, 5]
x = items.pop()
items.remove(3)
print(x)
print(items)''')
E["q10"] = gaps(a=(['remove'], "7rem"), b=(['pop'], "7rem"), c=(['del'], "7rem"))
E["q11"] = predict('''letters = ["b", "a", "b", "c"]
print(letters.index("b"))
print(letters.count("b"))
print("d" in letters)''')
E["q12"] = choice("C")
E["q13"] = predict('''vals = [10, 20, 30, 40, 50]
print(vals[1:4])
print(vals[:3])
print(vals[-2:])''')
E["q14"] = gaps(a=(['2:4', '-3:-1', '2:-1', '-3:4'], "7rem"), b=([':4', '0:4', ':-1', '0:-1'], "7rem"))
E["q15"] = predict('''a = [1, 2, 3]
b = a
b.append(4)
a[0] = 0
print(a)
print(b)''')
E["q16"] = true_false(True, False)
E["q17"] = choice("C")
E["q18"] = predict('''a = [1, 2, 3]
b = a[:]
c = a
c[1] = 7
b[0] = 5
print(a)
print(b)''')
E["q19"] = predict('''nums = [3, 4]
result = nums.append(5)
print(result)
print(nums)''')
E["q20"] = true_false(True, False)

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-24",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 24 Workbook",
    "subtitle": "Lists: properties and operations",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-24/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
