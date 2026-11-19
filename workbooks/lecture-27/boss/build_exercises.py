"""Build workbooks/lecture-27/boss/exercises.json: the Lecture 27 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_27_SHARED_CONTENT.tex, in its order. The listings below are copied
from it. Expected outputs are produced by actually running the model
solutions. Run from anywhere:

    python3 workbooks/lecture-27/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-27/boss
"""
import base64, contextlib, copy, io, json, subprocess, sys, pathlib
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


# Boss listings from the kit.
SRC = {}
SRC['boss_1_starter'] = '''def count_in_range(values, low, high):
    pass
'''
SRC['boss_1'] = '''def count_in_range(values, low, high):
    count = 0
    for value in values:
        if value >= low and value < high:
            count = count + 1
    return count

values = []
line = input()
while line != "":
    values.append(float(line))
    line = input()
low = float(input())
high = float(input())
print("Count:", count_in_range(values, low, high))
'''
SRC['boss_2_starter'] = '''def is_sorted(values):
    pass
'''
SRC['boss_2_1'] = '''def is_sorted(values):
    ascending = True
    descending = True
    for i in range(1, len(values)):
        if values[i] < values[i - 1]:
            ascending = False
        if values[i] > values[i - 1]:
            descending = False
    return ascending or descending
'''
SRC['boss_2_2'] = '''values = []
line = input()
while line != "":
    values.append(float(line))
    line = input()
if not is_sorted(values):
    print("Binary search cannot be used")
else:
    ascending = True
    for i in range(1, len(values)):
        if values[i] < values[i - 1]:
            ascending = False
    if ascending:
        print("Ascending binary search can be used")
    else:
        print("Descending binary search can be used")
'''
SRC['boss_3_starter'] = '''def linear_checks(values, target):
    pass

def binary_checks(values, target):
    pass
'''
SRC['boss_3_1'] = '''def linear_checks(values, target):
    checks = 0
    for i in range(len(values)):
        checks = checks + 1
        if values[i] == target:
            return checks
    return checks

def binary_checks(values, target):
    low = 0
    high = len(values) - 1
    checks = 0
    while low <= high:
        mid = (low + high) // 2
        checks = checks + 1
        if values[mid] == target:
            return checks
        elif values[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return checks
'''
SRC['boss_3_2'] = '''values = list(range(3, 301, 3))
print(f'{"Target":>7} {"Present":>7} {"Linear":>7} {"Binary":>7}')
line = input()
while line != "":
    target = int(line)
    present = target in values
    linear = linear_checks(values, target)
    binary = binary_checks(values, target)
    print(f"{target:7d} {str(present):>7} {linear:7d} {binary:7d}")
    line = input()
'''
SRC['boss_4_starter'] = '''def sublist_start(larger, smaller):
    pass

def is_sublist(larger, smaller):
    pass
'''
SRC['boss_4_1'] = '''def sublist_start(larger, smaller):
    k = len(smaller)
    for start in range(len(larger) - k + 1):
        j = 0
        while j < k and larger[start + j] == smaller[j]:
            j = j + 1
        if j == k:
            return start
    return -1

def is_sublist(larger, smaller):
    return sublist_start(larger, smaller) != -1
'''
SRC['boss_4_2'] = '''larger = []
for word in input().split():
    larger.append(int(word))
smaller = []
for word in input().split():
    smaller.append(int(word))
found = is_sublist(larger, smaller)
print("Found:", found)
if found:
    print("Start:", sublist_start(larger, smaller))
'''

# A check runs after the student's program in a copy of its namespace.
# `_fn` finds a function and checks its parameter count. `_returns` compares
# a returned value with the model's. `_keeps` checks that a call leaves its
# list argument unchanged. `_body(name)` lists the nodes inside one function.
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
    assert given == list(args), call + " changed an input list. Keep the inputs unchanged."
'''

def returns(name, ns, *calls):
    lines = ""
    for args in calls:
        want = ns[name](*copy.deepcopy(list(args)))
        lines += f"_returns({name!r}, {args!r}, {want!r})\n"
    return lines

def namespace(code, inputs):
    ns = {"__name__": "lecture27boss"}
    answers = list(inputs)
    ns["input"] = lambda prompt="": answers.pop(0)
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    del ns["input"]
    return ns

AST += '''def _main():
    return ast.Module(body=[n for n in _TREE.body if not isinstance(n, ast.FunctionDef)], type_ignores=[])
def _has(kind, tree):
    return [n for n in ast.walk(tree) if isinstance(n, kind)]
'''

E = {}

# ---------------------------------------------------------------- 1 Count readings within limits (Stephenson 121)
rng = SRC["boss_1"]
rng_ns = namespace(rng, ["", "0", "1"])
E["in-range"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 16,
    "starter": SRC["boss_1_starter"],
    "cases": input_cases(rng,
        ("Example 1: typed 1.5, 4, 4, 9, blank, 4, 9", ["1.5", "4", "4", "9", "", "4", "9"]),
        ("Example 2: typed blank, 0, 10", ["", "0", "10"]),
        ("Example 3: typed 2, 5, blank, 7, 8", ["2", "5", "", "7", "8"]),
        ("Typed -3, 0, 2.5, 7, 7, 10, blank, 0, 7", ["-3", "0", "2.5", "7", "7", "10", "", "0", "7"]),
        ("Typed 5, 5, 5, blank, 5, 5", ["5", "5", "5", "", "5", "5"]),
        ("Typed -1000, 1000, blank, -1000, 1000", ["-1000", "1000", "", "-1000", "1000"])),
    "check": AST + '''_fn("count_in_range", "values", "low", "high")
_f = _body("count_in_range")
assert _loops(_f), "In count_in_range, use a loop and a counter."
assert not _calls("count") and not _comps(), "Count the matches with a loop and a counter. Do not use count() or a comprehension."
''' + returns("count_in_range", rng_ns, ([], 0, 10), ([4.0, 4.0, 9.0], 4.0, 9.0), ([1, 2, 3], 2, 2), ([1, 2, 3], 0, 1000), ([-5, 0, 5], -5, 5), ([7, 7, 8], 8, 9)) + '''_keeps("count_in_range", ([1.5, 4.0, 4.0, 9.0], 4.0, 9.0))
''',
    "hints": [
        "Read lines until a blank line and append `float(line)` for each reading. Then read the two limits with `float(input())`.",
        "In `count_in_range`, start `count = 0` and loop over every value. Do not stop at the first match.",
        "Add 1 when `value >= low and value < high`. Return `count` after the loop, then print `\"Count:\"` and the result.",
    ],
    "answer": b64(rng),
    "answerNote": "The lower limit is included and the upper limit is excluded. The loop visits every reading, so repeated values are counted separately."}
assert E["in-range"]["cases"][0]["expected"] == "Count: 2"
assert E["in-range"]["cases"][1]["expected"] == "Count: 0"

# ---------------------------------------------------------------- 2 Check the order before searching (Stephenson 120)
order = SRC["boss_2_1"] + "\n" + SRC["boss_2_2"]
order_ns = namespace(order, [""])
E["order"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 20,
    "starter": SRC["boss_2_starter"],
    "cases": input_cases(order,
        ("Example 1: typed 18, 12, 12, 3, blank", ["18", "12", "12", "3", ""]),
        ("Example 2: typed blank", [""]),
        ("Example 3: typed 3, 8, 5, blank", ["3", "8", "5", ""]),
        ("Typed 1, 4, 4, 9.5, blank", ["1", "4", "4", "9.5", ""]),
        ("Typed 6, 6, 6, blank", ["6", "6", "6", ""]),
        ("Typed 7, blank", ["7", ""]),
        ("Typed 9, 2, 5, blank", ["9", "2", "5", ""]),
        ("Typed 1, 2, 3, 2, blank", ["1", "2", "3", "2", ""])),
    "check": AST + '''_fn("is_sorted", "values")
assert _loops(_body("is_sorted")), "In is_sorted, compare neighboring values with a loop."
assert not _calls("sort") and not _func_calls("sorted"), "Check neighboring values with loops. Do not sort the input."
assert _func_calls("is_sorted", _main()), "Call is_sorted in the main program."
''' + returns("is_sorted", order_ns, ([],), ([5],), ([1, 2, 2, 3],), ([3, 3, 1],), ([1, 3, 2],), ([2, 2, 2],), ([5, 1, 5],), ([1, 2, 3, 2],)) + '''_keeps("is_sorted", ([18, 12, 12, 3],))
''',
    "hints": [
        "In `is_sorted`, start with `ascending = True` and `descending = True`. Loop over `i` from 1 to `len(values) - 1` and compare `values[i]` with `values[i - 1]`.",
        "A decrease (`values[i] < values[i - 1]`) sets `ascending = False`. An increase sets `descending = False`. Return `ascending or descending`.",
        "In the main program, print `Binary search cannot be used` when `is_sorted` returns False. Otherwise check ascending order with the same loop, and print the ascending message first when it holds.",
    ],
    "answer": b64(order),
    "answerNote": "Equal neighbors keep both flags. An empty or one-element list has no neighbors, so both orders hold and the ascending message wins."}
assert E["order"]["cases"][0]["expected"] == "Descending binary search can be used"
assert E["order"]["cases"][1]["expected"] == "Ascending binary search can be used"
assert E["order"]["cases"][2]["expected"] == "Binary search cannot be used"

# ---------------------------------------------------------------- 3 Compare the work of two searches (original, awaiting approval)
work = SRC["boss_3_1"] + "\n" + SRC["boss_3_2"]
work_ns = namespace(work, [""])
M3 = list(range(3, 301, 3))
E["work"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 32,
    "starter": SRC["boss_3_starter"],
    "cases": input_cases(work,
        ("Example 1: typed 3, 300, 4, 303, blank", ["3", "300", "4", "303", ""]),
        ("Example 2: typed blank", [""]),
        ("Typed 150, 1, 151, blank", ["150", "1", "151", ""]),
        ("Typed -1000, 1000, 297, 6, blank", ["-1000", "1000", "297", "6", ""]),
        ("Typed 153, 99, 0, blank", ["153", "99", "0", ""])),
    "check": AST + '''_fn("linear_checks", "values", "target")
_fn("binary_checks", "values", "target")
assert _has(ast.For, _body("linear_checks")), "In linear_checks, use a for loop."
assert _has(ast.While, _body("binary_checks")), "In binary_checks, use a while loop with low and high."
assert not _calls("index") and not _calls("count"), "Count the checks with loops. Do not use index or count."
''' + returns("linear_checks", work_ns, ([], 5), ([5], 5), ([5], 6), ([4, 8, 8, 2], 8), (M3, 3), (M3, 150), (M3, 301)) + returns("binary_checks", work_ns, ([], 5), ([5], 5), ([5], 6), ([1, 3, 5, 7], 7), ([1, 3, 5, 7], 0), (M3, 3), (M3, 150), (M3, 151), (M3, 300), (list(range(1, 17)), 16)) + '''_keeps("linear_checks", ([1, 3, 5, 7], 7))
_keeps("binary_checks", ([1, 3, 5, 7], 7))
''',
    "hints": [
        "Copy `linear_search` and add `checks = 0`. Add 1 at the start of each iteration, before the comparison. Return `checks` at a match and after the loop.",
        "Copy the loop version of `binary_search` the same way. Add 1 after you compute `mid`, then compare `values[mid]` with the target.",
        "In the main program, build the list once and print the header with four fields like `f'{\"Target\":>7}'`, separated by one space.",
        "For each target, set `present = target in values`. Print `f\"{target:7d} {str(present):>7} {linear:7d} {binary:7d}\"`.",
    ],
    "answer": b64(work),
    "answerNote": "The maximum remaining lengths after failed checks are 50, 25, 12, 6, 3, 1 and 0. Seven checks are enough for 100 elements, which matches ⌊log2 100⌋ + 1 = 7."}
assert E["work"]["cases"][0]["expected"] == " Target Present  Linear  Binary\n      3    True       1       6\n    300    True     100       7\n      4   False     100       7\n    303   False     100       7"
assert E["work"]["cases"][1]["expected"] == " Target Present  Linear  Binary"

# ---------------------------------------------------------------- 4 Find a consecutive pattern (Stephenson 125)
pat = SRC["boss_4_1"] + "\n" + SRC["boss_4_2"]
pat_ns = namespace(pat, ["", ""])
E["pattern"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 26,
    "starter": SRC["boss_4_starter"],
    "cases": input_cases(pat,
        ("Example 1: typed 8 3 8 3 6, then 8 3 6", ["8 3 8 3 6", "8 3 6"]),
        ("Example 2: typed 5 9, then blank", ["5 9", ""]),
        ("Example 3: typed 2 4 7, then 2 7", ["2 4 7", "2 7"]),
        ("Typed 1 2 3, then 1 2 3", ["1 2 3", "1 2 3"]),
        ("Typed blank, then blank", ["", ""]),
        ("Typed 4 5, then 4 5 6", ["4 5", "4 5 6"]),
        ("Typed 7 1 7 1 7 2, then 7 1 7 2", ["7 1 7 1 7 2", "7 1 7 2"]),
        ("Typed -3 0 -3, then -3", ["-3 0 -3", "-3"])),
    "check": AST + '''_fn("sublist_start", "larger", "smaller")
_fn("is_sublist", "larger", "smaller")
assert not _slices(), "Compare elements one at a time. Do not use slices."
for _n in _has(ast.Compare, _TREE):
    for _side in [_n.left] + _n.comparators:
        assert not (isinstance(_side, ast.Name) and _side.id in ("larger", "smaller")), "Compare elements one at a time. Do not compare whole lists with ==."
assert _loops(_body("sublist_start")), "In sublist_start, check each start position with a loop."
assert _func_calls("is_sublist", _main()) and _func_calls("sublist_start", _main()), "Call both is_sublist and sublist_start in the main program."
''' + returns("sublist_start", pat_ns, ([8, 3, 8, 3, 6], [8, 3, 6]), ([5, 9], []), ([], []), ([], [1]), ([2, 4, 7], [2, 7]), ([1, 2], [1, 2, 3]), ([1, 2, 1, 2], [1, 2]), ([3, 1, 4, 1], [4, 1])) + returns("is_sublist", pat_ns, ([8, 3, 8, 3, 6], [8, 3, 6]), ([5, 9], []), ([2, 4, 7], [2, 7]), ([1, 2], [1, 2, 3]), ([4], [4])) + '''_keeps("sublist_start", ([8, 3, 8, 3, 6], [8, 3, 6]))
_keeps("is_sublist", ([8, 3, 8, 3, 6], [8, 3, 6]))
''',
    "hints": [
        "Read each line with `input().split()` and append `int(word)` for each word. A blank line gives an empty list.",
        "In `sublist_start`, let `k = len(smaller)`. Loop over `start` in `range(len(larger) - k + 1)`. When `smaller` is longer, this range is empty.",
        "For each start, count matching elements with `j`: `while j < k and larger[start + j] == smaller[j]:` adds 1 to `j`. If `j == k`, return `start`. Return `-1` after the loop.",
        "`is_sublist` returns `sublist_start(larger, smaller) != -1`. In the main program, print `Found:` first, and print `Start:` only when it is found.",
    ],
    "answer": b64(pat),
    "answerNote": "The while loop stops at the first mismatch, so a failed start costs only the elements it compared. For an empty pattern, j == k at once, so the result is index 0."}
assert E["pattern"]["cases"][0]["expected"] == "Found: True\nStart: 2"
assert E["pattern"]["cases"][1]["expected"] == "Found: True\nStart: 0"
assert E["pattern"]["cases"][2]["expected"] == "Found: False"

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-27-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 27 Boss Problems",
    "short": "L27 bosses",
    "subtitle": "Linear and binary search",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-27/boss/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
for key, spec in E.items():
    for c in spec["cases"]:
        print(key, "|", c["name"], "|", c["expected"].replace("\n", " / "))
