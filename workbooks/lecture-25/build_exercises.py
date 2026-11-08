"""Build workbooks/lecture-25/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_25_SHARED_CONTENT.tex; model answers follow its \\solution{...}
text. Run from anywhere:

    python3 workbooks/lecture-25/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-25
"""
import base64, contextlib, io, json, subprocess, sys, pathlib

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

def namespace(code):
    ns = {"__name__": "lecture25"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    return ns

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
# `_calls(method)` lists method calls such as .append(...). `_func_calls`
# lists calls of a plain function name. `_loops()` lists for and while loops.
# `_comps()` lists list comprehensions. `_swap()` is true for a tuple
# assignment such as a[i], a[j] = a[j], a[i].
# For functions: `_fn` finds a function and checks its parameters. `_returns`
# compares a returned value with the model's. `_keeps` checks that a call
# leaves its list argument unchanged. `_body(name)` lists the nodes inside
# one function.
AST = '''import ast, copy, types, io, contextlib
_TREE = ast.parse(__source__)
def _calls(method, tree=None):
    return [n for n in ast.walk(tree or _TREE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == method]
def _func_calls(name, tree=None):
    return [n for n in ast.walk(tree or _TREE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name]
def _slices(tree=None):
    return [n for n in ast.walk(tree or _TREE) if isinstance(n, ast.Slice)]
def _loops(tree=None):
    return [n for n in ast.walk(tree or _TREE) if isinstance(n, (ast.For, ast.While))]
def _comps(tree=None):
    return [n for n in ast.walk(tree or _TREE) if isinstance(n, ast.ListComp)]
def _swap():
    return any(isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Tuple) and isinstance(n.value, ast.Tuple) for n in ast.walk(_TREE))
def _body(name):
    for node in _TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return ast.Module(body=[], type_ignores=[])
_WORDS = ["empty parentheses", "one parameter", "two parameters", "three parameters"]
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
    call = _shown(name, args)
    value, printed = _call(name, *copy.deepcopy(list(args)))
    if value is None and want is not None:
        raise AssertionError(call + " returned None. Send the result back with return.")
    assert value == want and type(value) is type(want), call + " should return " + repr(want) + ", not " + repr(value) + "."
def _keeps(name, args):
    call = _shown(name, args)
    given = copy.deepcopy(list(args))
    _call(name, *given)
    assert given == list(args), call + " changed its input list to " + repr(given[0]) + ". Keep the input unchanged."
'''

def returns(name, ns, *calls):
    """Check lines that compare each call's returned value with the model's."""
    lines = ""
    for args in calls:
        want = ns[name](*[list(a) if isinstance(a, list) else a for a in args])
        lines += f"_returns({name!r}, {args!r}, {want!r})\n"
    return lines

E = {}

# ============================================================ 1. Totals, counts, and built-in functions
E["ex-total"] = example('''marks = [40, 75, 50, 35]
total = 0
passes = 0
for mark in marks:
    total = total + mark
    if mark >= 50:
        passes = passes + 1
print(total, passes)
''')
assert E["ex-total"]["output"] == "200 2"
E["ex-builtins"] = example('''marks = [40, 75, 50, 35]
print(sum(marks))
print(max(marks), min(marks))
print(len(marks))
if len(marks) > 0:
    print(sum(marks) / len(marks))
''')
assert E["ex-builtins"]["output"] == "200\n75 35\n4\n50.0"
assert "ValueError" in run("print(max([]))", ok=False)[1]

# ============================================================ 2. Checking for a value
E["ex-found"] = example('''marks = [40, 75, 50, 35]
found = False
for m in marks:
    if m == 50:
        found = True
print(found)
print(50 in marks)
''')
assert E["ex-found"]["output"] == "True\nTrue"

# ============================================================ 3. The largest value and the longest string
E["ex-largest"] = example('''values = [42, 76, 68, 91]
largest = values[0]
for i in range(1, len(values)):
    if values[i] > largest:
        largest = values[i]
print(largest)
''')
assert E["ex-largest"]["output"] == "91"
E["ex-longest"] = example('''names = ["Ann", "Charlotte",
         "Zachary"]
longest = names[0]
for name in names[1:]:
    if len(name) > len(longest):
        longest = name
print(longest)
''')
assert E["ex-longest"]["output"] == "Charlotte"
assert out('print(max(["Ann", "Charlotte", "Zachary"]))') == "Zachary"

# ============================================================ 4. Largest indexes, related lists, and swaps
E["ex-best"] = example('''marks = [42, 76, 68, 91]
best = 0
for i in range(1, len(marks)):
    if marks[i] > marks[best]:
        best = i
print(best, marks[best])
''')
assert E["ex-best"]["output"] == "3 91"
E["ex-related"] = example('''names = ["Ann", "Ben", "Cal"]
marks = [70, 95, 80]
best = 0
for i in range(1, len(marks)):
    if marks[i] > marks[best]:
        best = i
print(names[best], marks[best])
''')
assert E["ex-related"]["output"] == "Ben 95"
E["ex-swap"] = example('''values = [42, 76, 68, 91]
i = 0
j = 3
values[i], values[j] = values[j], values[i]
print(values)
''')
assert E["ex-swap"]["output"] == "[91, 76, 68, 42]"
E["ex-swap-wrong"] = example('''values = [42, 76, 68, 91]
i = 0
j = 3
values[i] = values[j]
values[j] = values[i]
print(values)
''')
assert E["ex-swap-wrong"]["output"] == "[91, 76, 68, 91]"

# Checkpoint 1
cp1 = '''marks = [58, 91, 74, 91]
best = 0
for i in range(1, len(marks)):
    if marks[i] > marks[best]:
        best = i
print(best)
marks[0], marks[best] = marks[best], marks[0]
print(marks)
'''
assert out(cp1) == "1\n[91, 58, 74, 91]"
CP1_OTHER = [("marks = [58, 91, 74, 91]", "marks = [5, 3, 9, 9, 1]")]
assert out(rewritten(cp1, CP1_OTHER)) == "2\n[9, 3, 5, 9, 1]"
E["cp1"] = {"type": "code", "xp": 5, "minLines": 7,
    "starter": "marks = [58, 91, 74, 91]\n# Find the first largest index, then swap and print.\n",
    "cases": [case("marks = [58, 91, 74, 91]", cp1), case("marks = [5, 3, 9, 9, 1]", cp1, CP1_OTHER)],
    "check": AST + '''assert _loops(), "Use a loop to find the index of the first largest value."
assert not _func_calls("max") and not _calls("index"), "Find the index with a loop. Do not use max or index."
assert _swap(), "Swap the two elements with one statement, such as marks[0], marks[best] = marks[best], marks[0]."
''',
    "answer": b64(cp1),
    "answerNote": "The second 91 does not change best, because 91 > 91 is False."}
E["cp1-trace"] = {"type": "table", "xp": 1, "blanks": {
    f"b{i}": accept("1", width="4rem", placeholder="best") for i in (1, 2, 3)}}

# ============================================================ 5. Index changes after insertion and removal
E["ex-insert-pop"] = example('''values = [10, 30, 40]
values.insert(1, 20)
removed = values.pop(2)
print(removed)
print(values)
''')
assert E["ex-insert-pop"]["output"] == "30\n[10, 20, 40]"

# ============================================================ 6. Reverse order and slices
E["ex-reverse"] = example('''values = [10, 30, 20]
values.reverse()
print(values)
''')
assert E["ex-reverse"]["output"] == "[20, 30, 10]"
E["ex-reverse-slice"] = example('''values = [10, 30, 20]
backward = values[::-1]
print(values)
print(backward)
''')
assert E["ex-reverse-slice"]["output"] == "[10, 30, 20]\n[20, 30, 10]"

# ============================================================ 7. Sorting, aliases, and return values
E["ex-sort-alias"] = example('''marks = [70, 40, 90]
backup = marks
marks.sort()
print(marks)
print(backup)
''')
assert E["ex-sort-alias"]["output"] == "[40, 70, 90]\n[40, 70, 90]"
E["ex-sorted"] = example('''marks = [70, 40, 90]
ordered = sorted(marks)
print(marks)
print(ordered)
''')
assert E["ex-sorted"]["output"] == "[70, 40, 90]\n[40, 70, 90]"
E["ex-descending"] = example('''marks = [70, 40, 90]
ordered = sorted(marks,
                 reverse=True)
print(ordered)
marks.sort(reverse=True)
print(marks)
''')
assert E["ex-descending"]["output"] == "[90, 70, 40]\n[90, 70, 40]"
E["ex-sort-none"] = example('''marks = [70, 40, 90]
marks = marks.sort()
print(marks)
''')
assert E["ex-sort-none"]["output"] == "None"

# ============================================================ 8. A new list with reversed
E["ex-reversed"] = example('''nums = [10, 30, 20]
backward = list(reversed(nums))
print(backward)
print(nums)
''')
assert E["ex-reversed"]["output"] == "[20, 30, 10]\n[10, 30, 20]"

# ============================================================ 9. Functions that change a list or return a new list
E["ex-add-bonus"] = example('''def add_bonus(values):
    """Add 5 to each element."""
    for i in range(len(values)):
        values[i] = values[i] + 5

marks = [70, 80]
add_bonus(marks)
print(marks)
''')
assert E["ex-add-bonus"]["output"] == "[75, 85]"
E["ex-with-bonus"] = example('''def with_bonus(values):
    """Return new bonus values."""
    result = []
    for value in values:
        result.append(value + 5)
    return result

marks = [70, 80]
new_marks = with_bonus(marks)
print(marks)
print(new_marks)
''')
assert E["ex-with-bonus"]["output"] == "[70, 80]\n[75, 85]"

# Checkpoint 2
cp2 = '''def ranked_scores(values):
    result = values[:]
    result.remove(min(result))
    result.sort()
    return result
scores = [8, 6, 10, 6]
ranked = ranked_scores(scores)
print(ranked)
print(sum(ranked) / len(ranked))
print(scores)
'''
assert out(cp2) == "[6, 8, 10]\n8.0\n[8, 6, 10, 6]"
cp2_ns = namespace(cp2)
E["cp2"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": "def ranked_scores(values):\n    pass\nscores = [8, 6, 10, 6]\n",
    "cases": [case("scores = [8, 6, 10, 6]", cp2)],
    "check": AST + '''_fn("ranked_scores", "values")
_f = _body("ranked_scores")
assert _func_calls("min", _f) and _calls("remove", _f) and _calls("sort", _f), "Inside ranked_scores, use min, remove, and sort on the copy."
assert _slices(_f) or _calls("copy", _f) or _func_calls("list", _f), "Make a copy of values first, such as result = values[:]."
''' + returns("ranked_scores", cp2_ns, ([8, 6, 10, 6],), ([5, 1],), ([3, 3, 3],), ([9, 2, 7, 4],)) + '''_keeps("ranked_scores", ([8, 6, 10, 6],))
_keeps("ranked_scores", ([9, 2, 7, 4],))
''',
    "answer": b64(cp2),
    "answerNote": "The copy loses one lowest score. The input list stays unchanged."}
E["cp2-trace"] = {"type": "table", "xp": 1, "blanks": {
    "copy": lst("[8, 6, 10, 6]", width="11rem"),
    "remove": lst("[8, 10, 6]", width="11rem"),
    "sort": lst("[6, 8, 10]", width="11rem")}}

# ============================================================ 10. Building a list with a comprehension
E["ex-squares-loop"] = example('''squares = []
for n in range(1, 6):
    squares.append(n * n)
print(squares)
''')
E["ex-squares-comp"] = example('''squares = [n * n
           for n in range(1, 6)]
print(squares)
''')
assert E["ex-squares-loop"]["output"] == E["ex-squares-comp"]["output"] == "[1, 4, 9, 16, 25]"
E["ex-lengths"] = example('''names = ["Ada", "Alan", "Grace"]
lengths = [len(name)
           for name in names]
print(lengths)
print(names)
''')
assert E["ex-lengths"]["output"] == "[3, 4, 5]\n['Ada', 'Alan', 'Grace']"

# ============================================================ 11. Selecting and transforming elements
E["ex-passes-comp"] = example('''marks = [45, 50, 68, 49, 90]
passes = [m for m in marks
          if m >= 50]
print(passes)
''')
assert E["ex-passes-comp"]["output"] == "[50, 68, 90]"
E["ex-passes-loop"] = example('''marks = [45, 50, 68, 49, 90]
passes = []
for m in marks:
    if m >= 50:
        passes.append(m)
print(passes)
''')
assert E["ex-passes-loop"]["output"] == "[50, 68, 90]"
E["ex-upper"] = example('''names = ["Ada", "Grace", "Lin", "Alan"]
long_names = [name.upper() for name in names if len(name) > 3]
print(long_names)
''')
assert E["ex-upper"]["output"] == "['GRACE', 'ALAN']"

# ============================================================ 12. Choosing a readable loop
E["ex-report"] = example('''marks = [45, 50, 68]
passes = []
for mark in marks:
    if mark >= 50:
        passes.append(mark)
        print("Accepted:", mark)
    else:
        print("Below 50:", mark)
print(passes)
''')
assert E["ex-report"]["output"] == "Below 50: 45\nAccepted: 50\nAccepted: 68\n[50, 68]"
E["ex-simple"] = example('''nums = [-2, 3, 4, 7, 12]
simple = [2*n for n in nums]
print(simple)
''')
assert E["ex-simple"]["output"] == "[-4, 6, 8, 14, 24]"
E["ex-crowded"] = example('''nums = [-2, 3, 4, 7, 12]
crowded = [2*n + 1 for n in nums
           if n > 0 and n < 10
           and n % 2 == 0]
print(crowded)
''')
E["ex-crowded-loop"] = example('''nums = [-2, 3, 4, 7, 12]
result = []
for n in nums:
    if n > 0 and n < 10:
        if n % 2 == 0:
            result.append(2*n + 1)
print(result)
''')
assert E["ex-crowded"]["output"] == E["ex-crowded-loop"]["output"] == "[9]"

# Checkpoint 3: the deck asks for a comprehension and a loop solution. On the
# page both functions sit in one code box, so the loop version has its own name.
cp3 = '''def bonus_passes(marks):
    return [m + 5 for m in marks
            if m >= 50]

def bonus_passes_loop(marks):
    result = []
    for m in marks:
        if m >= 50:
            result.append(m + 5)
    return result

marks = [45, 50, 68, 49, 90]
print(bonus_passes(marks))
print(bonus_passes_loop(marks))
print(bonus_passes([]))
print(marks)
'''
assert out(cp3) == "[55, 73, 95]\n[55, 73, 95]\n[]\n[45, 50, 68, 49, 90]"
cp3_ns = namespace(cp3)
CP3_CALLS = (([45, 50, 68, 49, 90],), ([],), ([49, 50, 46],), ([100, 10],))
E["cp3"] = {"type": "code", "xp": 5, "minLines": 14,
    "starter": "def bonus_passes(marks):\n    pass\n\ndef bonus_passes_loop(marks):\n    pass\n\nmarks = [45, 50, 68, 49, 90]\n",
    "cases": [case("marks = [45, 50, 68, 49, 90]", cp3)],
    "check": AST + '''_fn("bonus_passes", "marks")
_fn("bonus_passes_loop", "marks")
assert _comps(_body("bonus_passes")), "Write bonus_passes with a list comprehension."
assert _loops(_body("bonus_passes_loop")) and _calls("append", _body("bonus_passes_loop")), "Write bonus_passes_loop with a loop and append."
''' + returns("bonus_passes", cp3_ns, *CP3_CALLS) + returns("bonus_passes_loop", cp3_ns, *CP3_CALLS) + '''_keeps("bonus_passes", ([45, 50, 68, 49, 90],))
_keeps("bonus_passes_loop", ([45, 50, 68, 49, 90],))
''',
    "answer": b64(cp3),
    "answerNote": "Both versions select marks with the original value. They apply the bonus after the selection."}

# ============================================================ Coding Practice
# 1. Products and negative values (R6.8)
p1 = '''values = [-3, 2, -4, 5]
product = 1
for value in values:
    product = product * value
negatives = 0
for value in values:
    if value < 0:
        negatives = negatives + 1
print(product)
print(negatives)
'''
assert out(p1) == "120\n2"
P1_EMPTY = [("values = [-3, 2, -4, 5]", "values = []")]
P1_OTHER = [("values = [-3, 2, -4, 5]", "values = [-1, -2, -3]")]
assert out(rewritten(p1, P1_EMPTY)) == "1\n0"
E["p1"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "values = [-3, 2, -4, 5]\n",
    "cases": [case("values = [-3, 2, -4, 5]", p1), case("values = []", p1, P1_EMPTY), case("values = [-1, -2, -3]", p1, P1_OTHER)],
    "check": AST + '''assert len(_loops()) >= 2, "Use one loop for the product and another loop for the count."
assert not _func_calls("range"), "Loop over the values directly. Do not use range."
''',
    "answer": b64(p1),
    "answerNote": "Both loops run zero times for an empty list. The initial values then become the results."}

# 2. Trace a removal by shifting (R6.16)
shift = '''values = [14, 5, 9, 2, 7]
position = 1
for i in range(position, len(values) - 1):
    values[i] = values[i + 1]
values.pop()
print(values)
'''
assert out(shift) == "[14, 9, 2, 7]"
E["ex-shift"] = example(shift, output=False)
trace = out(shift.replace("    values[i] = values[i + 1]\n", "    values[i] = values[i + 1]\n    print(i, values)\n")).split("\n")[:-1]
TRACE = [line.split(" ", 1) for line in trace]
assert TRACE == [["1", "[14, 9, 9, 2, 7]"], ["2", "[14, 9, 2, 2, 7]"], ["3", "[14, 9, 2, 7, 7]"]]
blanks = {}
for k, (i, values) in enumerate(TRACE, 1):
    blanks[f"i{k}"] = accept(i, width="4rem", placeholder="i")
    blanks[f"v{k}"] = lst(values, width="12rem")
blanks["final"] = lst("[14, 9, 2, 7]", width="12rem")
E["p2-table"] = {"type": "table", "xp": 1, "blanks": blanks}
E["p2-why"] = short("The shifts replace elements without changing the length. "
                    "After the shifts, the last value appears twice. The final removal deletes the repeated last element.",
                    min_chars=20, placeholder="Why the script needs the final pop…")

# 3. Keep nonnegative values (R6.18)
p3 = '''def nonnegative_comp(values):
    return [value for value in values if value >= 0]

def nonnegative_loop(values):
    result = []
    for value in values:
        if value >= 0:
            result.append(value)
    return result

values = [-5, 0, 8, -2, 8]
print(nonnegative_comp(values))
print(nonnegative_loop(values))
print(values)
'''
assert out(p3) == "[0, 8, 8]\n[0, 8, 8]\n[-5, 0, 8, -2, 8]"
p3_ns = namespace(p3)
P3_CALLS = (([-5, 0, 8, -2, 8],), ([],), ([-1, -9],), ([3, -3, 0, 3],))
P3_OTHER = [("values = [-5, 0, 8, -2, 8]", "values = [7, -1, -1, 0]")]
E["p3"] = {"type": "code", "xp": 5, "minLines": 13,
    "starter": "def nonnegative_comp(values):\n    pass\n\ndef nonnegative_loop(values):\n    pass\n\nvalues = [-5, 0, 8, -2, 8]\n",
    "cases": [case("values = [-5, 0, 8, -2, 8]", p3), case("values = [7, -1, -1, 0]", p3, P3_OTHER)],
    "check": AST + '''_fn("nonnegative_comp", "values")
_fn("nonnegative_loop", "values")
assert _comps(_body("nonnegative_comp")), "Write nonnegative_comp with a list comprehension."
assert _loops(_body("nonnegative_loop")) and _calls("append", _body("nonnegative_loop")), "Write nonnegative_loop with a loop and append."
assert not _calls("remove") and not _calls("pop") and not any(isinstance(n, ast.Delete) for n in ast.walk(_TREE)), "Build a new list. Do not remove elements from the list you loop through."
''' + returns("nonnegative_comp", p3_ns, *P3_CALLS) + returns("nonnegative_loop", p3_ns, *P3_CALLS) + '''_keeps("nonnegative_comp", ([-5, 0, 8, -2, 8],))
_keeps("nonnegative_loop", ([-5, 0, 8, -2, 8],))
''',
    "answer": b64(p3),
    "answerNote": "Both functions keep zero and repeated retained values. Either function returns [] for an empty input or an input containing only negative values."}

# 4. Insert into ascending order (R6.19)
p4 = '''def insert_ordered(values, value):
    position = 0
    while position < len(values) and values[position] <= value:
        position = position + 1
    values.insert(position, value)

values = [2, 6, 6, 12]
print(insert_ordered(values, 6))
print(values)
'''
assert out(p4) == "None\n[2, 6, 6, 6, 12]"
p4_ns = namespace(p4)
# 6.0 equals 6 but prints differently, so the last test shows where the new value went.
P4_TESTS = [([], 5), ([4, 8], 1), ([4, 8], 9), ([1, 3, 3, 7], 3), ([2, 6, 6, 12], 6.0)]
p4_lines = ""
for given, value in P4_TESTS:
    after = list(given)
    p4_ns["insert_ordered"](after, value)
    p4_lines += f"_ins({given!r}, {value!r}, {after!r})\n"
assert repr(after) == "[2, 6, 6, 6.0, 12]"
E["p4"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "def insert_ordered(values, value):\n    pass\n\nvalues = [2, 6, 6, 12]\n",
    "cases": [case("values = [2, 6, 6, 12], insert 6", p4)],
    "check": AST + '''_fn("insert_ordered", "values", "value")
_f = _body("insert_ordered")
assert _loops(_f), "Find the insertion index with a loop."
assert _calls("insert", _f), "Insert the value with insert."
assert not _calls("sort") and not _func_calls("sorted"), "Do not call sort or sorted. Find the position with a loop."
def _ins(given, value, want):
    call = _shown("insert_ordered", (given, value))
    values = list(given)
    result, printed = _call("insert_ordered", values, value)
    assert result is None, call + " should change the list and return None, not " + repr(result) + "."
    assert repr(values) == repr(want), "After " + call + ", the list should be " + repr(want) + ", not " + repr(values) + "."
''' + p4_lines,
    "answer": b64(p4),
    "answerNote": "The loop passes all smaller or equal values. Index len(values) inserts at the end."}

# 5. Check ascending order in two ways (P6.4)
p5 = '''def ascending_loop(values):
    ordered = True
    for i in range(1, len(values)):
        if values[i] < values[i - 1]:
            ordered = False
    return ordered

def ascending_comp(values):
    checks = [values[i - 1] <= values[i]
              for i in range(1, len(values))]
    return False not in checks

values = [1, 4, 4, 9]
print(ascending_loop(values), ascending_comp(values))
values = [1, 7, 3]
print(ascending_loop(values), ascending_comp(values))
'''
assert out(p5) == "True True\nFalse False"
p5_ns = namespace(p5)
P5_CALLS = (([1, 4, 4, 9],), ([1, 7, 3],), ([],), ([5],), ([3, 3],), ([2, 1],), ([1, 2, 3, 0],))
E["p5"] = {"type": "code", "xp": 5, "minLines": 15,
    "starter": "def ascending_loop(values):\n    pass\n\ndef ascending_comp(values):\n    pass\n",
    "cases": [case("[1, 4, 4, 9] and [1, 7, 3]", p5)],
    "check": AST + '''_fn("ascending_loop", "values")
_fn("ascending_comp", "values")
assert _loops(_body("ascending_loop")), "Write ascending_loop with adjacent comparisons in a loop."
_c = _body("ascending_comp")
assert _comps(_c), "In ascending_comp, build a list of adjacent comparison results with a comprehension."
assert any(isinstance(n, ast.Compare) and any(isinstance(o, (ast.In, ast.NotIn)) for o in n.ops) for n in ast.walk(_c)), "In ascending_comp, check the comparison results with in or not in."
assert not _calls("sort") and not _func_calls("sorted"), "Do not sort the list. Compare adjacent elements."
''' + returns("ascending_loop", p5_ns, *P5_CALLS) + returns("ascending_comp", p5_ns, *P5_CALLS),
    "answer": b64(p5),
    "answerNote": "An empty list of comparisons contains no False result. Equal adjacent values pass the comparison."}

# 6. Find the longest run (R6.20)
p6 = '''def longest_run(values):
    if len(values) == 0:
        return 0
    current = 1
    longest = 1
    for i in range(1, len(values)):
        if values[i] == values[i - 1]:
            current = current + 1
        else:
            current = 1
        if current > longest:
            longest = current
    return longest

print(longest_run([5, 5, 1, 1, 1, 2, 2]))
print(longest_run([]))
print(longest_run([4]))
'''
assert out(p6) == "3\n0\n1"
p6_ns = namespace(p6)
P6_CALLS = (([5, 5, 1, 1, 1, 2, 2],), ([],), ([4],), ([1, 2, 2, 2],), ([7, 7, 7, 7],), ([1, 2, 3],), ([3, 3, 1, 3, 3],))
E["p6"] = {"type": "code", "xp": 5, "minLines": 15,
    "starter": "def longest_run(values):\n    pass\n",
    "cases": [case("[5, 5, 1, 1, 1, 2, 2], [] and [4]", p6)],
    "check": AST + '''_fn("longest_run", "values")
assert _loops(_body("longest_run")) and _func_calls("range", _body("longest_run")), "Compare adjacent values with an index loop, such as for i in range(1, len(values))."
''' + returns("longest_run", p6_ns, *P6_CALLS) + '''_keeps("longest_run", ([5, 5, 1, 1, 1, 2, 2],))
''',
    "answer": b64(p6),
    "answerNote": "current counts the run ending at the current index. longest keeps the largest run length found so far."}

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

def gap_works(template, fills, want):
    """Every accepted gap answer must make the program print the stated output."""
    for fill in fills:
        assert out(template.format(*fill)) == want, (fill, template)

E["q1"] = predict('''values = []
print(sum(values))
print(len(values))''')
Q2 = "values = [3, 6, 9]\nif len(values) {} 0:\n    print(sum(values) / {})\n"
gap_works(Q2, [(">", "len(values)"), ("!=", "len(values)")], "6.0")
E["q2"] = gaps(a=([">", "!="], "5rem"), b=(["len(values)"], "10rem"))
E["q3"] = choice("B")
assert out("values = [3, 8]\nprint(6 not in values)") == "True"
E["q4"] = true_false(True, False)
E["q5"] = predict('''words = ["red", "blue", "gold"]
longest = words[0]
for word in words[1:]:
    if len(word) > len(longest):
        longest = word
print(longest)''')
E["q6"] = choice("D")
assert out('words = ["an", "b", "ant"]\nprint(max(words), min(words))') == "b an"
Q7 = "values = [9, 9, 2]\nbest = 0\nfor i in range(1, len(values)):\n    if values[i] {} values[best]:\n        best = i\nprint(best)\n"
gap_works(Q7, [(">",)], "0")
assert out(Q7.format(">=")) == "1"
E["q7"] = gaps(a=([">"], "5rem"))
E["q8"] = true_false(True, False)
E["q9"] = predict('''values = [2, 6, 8]
values.insert(1, 4)
removed = values.pop(2)
print(removed)
print(values[2])''')
Q10 = "values = [1, 7, 9]\nvalues.insert(1, 4)\nprint(values.pop({}))\nprint(values)\n"
gap_works(Q10, [("2",), ("-2",)], "7\n[1, 4, 9]")
E["q10"] = gaps(a=(["2", "-2"], "5rem"))
E["q11"] = choice("C")
E["q12"] = true_false(False, True)
E["q13"] = predict('''values = [6, 1, 4]
other = values
result = values.sort()
print(other)
print(result)''')
E["q14"] = choice("A")
Q15 = "nums = [3, 7]\nbackward = {}(reversed(nums))\nprint(backward)\nprint(nums)\n"
gap_works(Q15, [("list",)], "[7, 3]\n[3, 7]")
E["q15"] = gaps(a=(["list"], "6rem"))
E["q16"] = true_false(True, False)
E["q17"] = predict('''def trim(values):
    values.pop()
nums = [4, 8]
print(trim(nums))
print(nums)''')
Q18 = "def reset_first(values):\n    result = {}\n    result[0] = 0\n    return result\nnums = [3, 8]\nprint(reset_first(nums))\nprint(nums)\n"
Q18_FILLS = ["values[:]", "values.copy()", "list(values)", "values[0:]"]
gap_works(Q18, [(f,) for f in Q18_FILLS], "[0, 8]\n[3, 8]")
E["q18"] = gaps(a=(Q18_FILLS, "9rem"))
E["q19"] = predict('''values = [2, 0, -3]
result = [n + 4 for n in values]
print(result)
print(values)''')
E["q20"] = choice("A")
Q21 = "nums = [-2, 0, 2, 5]\nresult = [{} for n in nums if n {} 0]\nprint(result)\n"
Q21_A = ["n * 3", "3 * n", "n*3", "3*n"]
gap_works(Q21, [(a, ">") for a in Q21_A], "[6, 15]")
E["q21"] = gaps(a=(Q21_A, "7rem"), b=([">"], "5rem"))
E["q22"] = true_false(True, False)
E["q23"] = choice("D")
assert out("nums = [-1, 2, 6, 11]\nprint([2*n + 1 for n in nums if n > 0 and n < 8])") == "[5, 13]"
E["q24"] = true_false(True, False)

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-25",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 25 Workbook",
    "subtitle": "List algorithms, slices, and comprehensions",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-25/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
