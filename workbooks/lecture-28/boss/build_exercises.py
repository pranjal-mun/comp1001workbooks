"""Build workbooks/lecture-28/boss/exercises.json: the Lecture 28 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_28_SHARED_CONTENT.tex, in its order. The listings below are copied
from it. Expected outputs are produced by actually running the model
solutions. Run from anywhere:

    python3 workbooks/lecture-28/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-28/boss
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
SRC['boss_1_starter'] = '''def selection_sort(values):
    pass

seed = int(input())
'''
SRC['boss_1_1'] = '''def selection_sort(values):
    n = len(values)
    for i in range(n - 1):
        smallest = i
        for j in range(i + 1, n):
            if values[j] < values[smallest]:
                smallest = j
        values[i], values[smallest] = values[smallest], values[i]
'''
SRC['boss_1_2'] = '''import random

seed = int(input())
random.seed(seed)
picks = []
while len(picks) < 6:
    value = random.randint(1, 49)
    if value not in picks:
        picks.append(value)
print(picks)
ticket = picks[:]
selection_sort(ticket)
print(ticket)
print(sorted(picks))
'''
SRC['boss_2_starter'] = '''def merge_unique(left, right):
    pass

left = [int(word) for word in input().split()]
right = [int(word) for word in input().split()]
'''
SRC['boss_2_1'] = '''def merge_unique(left, right):
    result = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            value = left[i]
            i = i + 1
        else:
            value = right[j]
            j = j + 1
        if len(result) == 0 or value != result[-1]:
            result.append(value)
    for value in left[i:]:
        if len(result) == 0 or value != result[-1]:
            result.append(value)
    for value in right[j:]:
        if len(result) == 0 or value != result[-1]:
            result.append(value)
    return result
'''
SRC['boss_2_2'] = '''left = [int(word) for word in input().split()]
right = [int(word) for word in input().split()]
result = merge_unique(left, right)
print(result)
print(len(result))
'''
SRC['boss_3_starter'] = '''def selection_sort_count(values):
    pass

def selection_sort_desc_count(values):
    pass

values = []
'''
SRC['boss_3_1'] = '''def selection_sort_count(values):
    n = len(values)
    comparisons = 0
    for i in range(n - 1):
        smallest = i
        for j in range(i + 1, n):
            comparisons = comparisons + 1
            if values[j] < values[smallest]:
                smallest = j
        values[i], values[smallest] = values[smallest], values[i]
        print(values)
    return comparisons
'''
SRC['boss_3_2'] = '''def selection_sort_desc_count(values):
    n = len(values)
    comparisons = 0
    for i in range(n - 1):
        largest = i
        for j in range(i + 1, n):
            comparisons = comparisons + 1
            if values[j] > values[largest]:
                largest = j
        values[i], values[largest] = values[largest], values[i]
        print(values)
    return comparisons
'''
SRC['boss_3_3'] = '''values = []
line = input()
while line != "":
    values.append(int(line))
    line = input()
ascending = values[:]
descending = values[:]
n = len(values)
count = selection_sort_count(ascending)
print("Ascending comparisons:", count)
print("Formula:", n * (n - 1) // 2)
count = selection_sort_desc_count(descending)
print("Descending comparisons:", count)
'''
SRC['boss_4_starter'] = '''def merge_count(left, right):
    pass

def merge_sort_count(values):
    pass

def selection_count(n):
    pass

seed = int(input())
'''
SRC['boss_4_1'] = '''def merge(left, right):
    result = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i = i + 1
        else:
            result.append(right[j])
            j = j + 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
'''
SRC['boss_4_2'] = '''def merge_sort(values):
    if len(values) <= 1:
        return values[:]
    mid = len(values) // 2
    left = merge_sort(values[:mid])
    right = merge_sort(values[mid:])
    return merge(left, right)
'''
SRC['boss_4_3'] = '''def merge_count(left, right):
    comparisons = 0
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        comparisons = comparisons + 1
        if left[i] <= right[j]:
            i = i + 1
        else:
            j = j + 1
    return comparisons
'''
SRC['boss_4_4'] = '''def merge_sort_count(values):
    if len(values) <= 1:
        return 0
    mid = len(values) // 2
    left_part = values[:mid]
    right_part = values[mid:]
    left_count = merge_sort_count(left_part)
    right_count = merge_sort_count(right_part)
    current_count = merge_count(
        merge_sort(left_part), merge_sort(right_part))
    return left_count + right_count + current_count

def selection_count(n):
    return n * (n - 1) // 2
'''
SRC['boss_4_5'] = '''import random

seed = int(input())
random.seed(seed)
eight_values = []
print(f"{'n':>4} {'Selection':>10} {'Merge':>8}")
for n in [8, 16, 32]:
    values = []
    for i in range(n):
        values.append(random.randint(1, 100))
    if n == 8:
        eight_values = values[:]
    selection = selection_count(n)
    merged = merge_sort_count(values)
    print(f"{n:4d} {selection:10d} {merged:8d}")
print(sorted(eight_values))
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
    ns = {"__name__": "lecture28boss"}
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


# Sorting helpers. `_sorts_in_place` calls a function on a copy of a list and
# compares the list afterwards. `_no_sort(name)` is true when a function does
# not call sort or sorted.
AST += '''def _sorts_in_place(name, items, want):
    data = list(items)
    value, printed = _call(name, data)
    assert data == want, name + "(" + repr(list(items)) + ") left the list as " + repr(data) + ". It should become " + repr(want) + "."
    return value
def _no_sort(name):
    return not _func_calls("sorted", _body(name)) and not _calls("sort", _body(name))
def _uses_in(tree):
    return [n for n in ast.walk(tree) if isinstance(n, ast.Compare) and any(isinstance(o, (ast.In, ast.NotIn)) for o in n.ops)]
'''

LISTS = [[], [4], [2, 1], [1, 2], [3, 7, 2, 7], [5, 2, 9, 1], [9, 8, 7, 6, 5], [4, 4, 4], [-3, 10, 0, -3, 8, 2]]

E = {}

# ---------------------------------------------------------------- 1 Print a reproducible ticket (Stephenson 114)
ticket = SRC["boss_1_1"] + "\n\n" + SRC["boss_1_2"]
E["ticket"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 22,
    "starter": SRC["boss_1_starter"],
    "cases": input_cases(ticket,
        ("Example 1: typed 11", ["11"]),
        ("Example 2: typed 0", ["0"]),
        ("Typed 1", ["1"]),
        ("Typed 42", ["42"]),
        ("Typed 2026", ["2026"])),
    "check": AST + '''_fn("selection_sort", "values")
_f = _body("selection_sort")
assert len(_loops(_f)) >= 2, "Use selection sort in selection_sort: an outer loop over the positions and an inner loop that finds the smallest remaining value."
assert _no_sort("selection_sort"), "Sort the values yourself in selection_sort. Do not use sort or sorted inside it."
assert not _func_calls("min", _f), "Find the smallest value with the inner loop in selection_sort. Do not use min."
assert _calls("seed", _main()) and _calls("randint", _main()), "Call random.seed(seed) and then random.randint(1, 49) in the main program."
''' + "".join(f"assert _sorts_in_place('selection_sort', {v!r}, {sorted(v)!r}) is None, 'selection_sort should change the list in place and return nothing.'\n" for v in LISTS),
    "hints": [
        "After `random.seed(seed)`, start `picks = []`. Use `while len(picks) < 6:` and pick `value = random.randint(1, 49)` each time.",
        "Append the value only when `value not in picks`. A repeated number is skipped, and the loop picks again.",
        "`selection_sort` is the function from section 3. Sort `ticket = picks[:]`, then print `picks`, `ticket` and `sorted(picks)` on separate lines.",
    ],
    "answer": b64(ticket),
    "answerNote": "The same seed gives the same picks every time. The copy changes during selection sort, so picks keeps its first order."}
assert E["ticket"]["cases"][0]["expected"] == "[29, 36, 30, 33, 38, 13]\n[13, 29, 30, 33, 36, 38]\n[13, 29, 30, 33, 36, 38]"
assert E["ticket"]["cases"][1]["expected"] == "[25, 49, 27, 3, 17, 33]\n[3, 17, 25, 27, 33, 49]\n[3, 17, 25, 27, 33, 49]"

# ---------------------------------------------------------------- 2 Merge each value once (original, awaiting approval)
unique = SRC["boss_2_1"] + "\n\n" + SRC["boss_2_2"]
unique_ns = namespace(unique, ["", ""])
PAIRS = [([2, 2, 6], [2, 5, 5, 8]), ([], [4, 4, 9]), ([4, 4, 9], []), ([], []), ([1, 3, 5], [2, 4, 6]),
         ([7, 7, 7], [7]), ([-3, 0, 0, 4], [-3, 4, 9, 9]), ([1, 2], [3, 3, 3]), ([5, 5], [1, 1])]
E["merge-unique"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 26,
    "starter": SRC["boss_2_starter"],
    "cases": input_cases(unique,
        ("Example 1: typed 2 2 6, then 2 5 5 8", ["2 2 6", "2 5 5 8"]),
        ("Example 2: typed blank, then 4 4 9", ["", "4 4 9"]),
        ("Typed 1 3 5, then 2 4 6", ["1 3 5", "2 4 6"]),
        ("Typed 7 7 7, then 7", ["7 7 7", "7"]),
        ("Typed blank, then blank", ["", ""]),
        ("Typed -3 0 0 4, then -3 4 9 9", ["-3 0 0 4", "-3 4 9 9"]),
        ("Typed 1 2 3, then blank", ["1 2 3", ""])),
    "check": AST + '''_fn("merge_unique", "left", "right")
_f = _body("merge_unique")
assert [n for n in ast.walk(_f) if isinstance(n, ast.While)], "Use the two-index merge in merge_unique: a while loop with i and j."
assert not _calls("extend", _f), "Replace each remaining-slice extend with a loop in merge_unique, so the duplicate test also runs on those values."
assert not _uses_in(_f), "Compare each value with the last value added, result[-1], in merge_unique. Do not use in to test membership."
assert not _func_calls("sorted") and not _calls("sort") and not _func_calls("set"), "Merge the two lists with indices. Do not use sort, sorted or set in this program."
''' + returns("merge_unique", unique_ns, *PAIRS) + '''_keeps("merge_unique", ([2, 2, 6], [2, 5, 5, 8]))
_r = [2, 5, 5, 8]
merge_unique([2, 2, 6], _r)
assert _r == [2, 5, 5, 8], "merge_unique changed the right list. Keep both input lists unchanged."
''',
    "hints": [
        "Start from the `merge` function in section 5. Inside the while loop, pick `value` from the left or the right list and advance that index.",
        "Append `value` only when `len(result) == 0 or value != result[-1]`. Equal values sit next to each other because both lists are in ascending order.",
        "After the while loop, use `for value in left[i:]:` and `for value in right[j:]:` with the same test. Print the result, then `len(result)`.",
    ],
    "answer": b64(unique),
    "answerNote": "Both lists are ascending, so any repeated value reaches the result right after its first copy. Testing result[-1] is enough, and each remaining slice needs the same test."}
assert E["merge-unique"]["cases"][0]["expected"] == "[2, 5, 6, 8]\n4"
assert E["merge-unique"]["cases"][1]["expected"] == "[4, 9]\n2"

# ---------------------------------------------------------------- 3 Count every selection comparison (original, awaiting approval)
count = SRC["boss_3_1"] + "\n\n" + SRC["boss_3_2"] + "\n\n" + SRC["boss_3_3"]
E["count-selection"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 36,
    "starter": SRC["boss_3_starter"],
    "cases": input_cases(count,
        ("Example 1: typed 1, 4, 6, blank", ["1", "4", "6", ""]),
        ("Example 2: typed 5, blank", ["5", ""]),
        ("Example 3: typed blank", [""]),
        ("Typed 3, 1, 2, blank", ["3", "1", "2", ""]),
        ("Typed 9, 9, 1, 5, blank", ["9", "9", "1", "5", ""]),
        ("Typed -2, 7, 0, 7, 3, blank", ["-2", "7", "0", "7", "3", ""])),
    "check": AST + '''_fn("selection_sort_count", "values")
_fn("selection_sort_desc_count", "values")
for _name in ("selection_sort_count", "selection_sort_desc_count"):
    assert len(_loops(_body(_name))) >= 2, "Use selection sort in " + _name + ": an outer loop over the positions and an inner loop over the remaining values."
assert not _func_calls("sorted") and not _calls("sort"), "Use selection sort in both functions. Do not use sort or sorted in this program."
assert not _func_calls("min") and not _func_calls("max"), "Select each value with the inner loop. Do not use min or max."
''' + "".join(
        f"assert _sorts_in_place('selection_sort_count', {v!r}, {sorted(v)!r}) == {len(v) * (len(v) - 1) // 2}, 'selection_sort_count({v!r}) should return {len(v) * (len(v) - 1) // 2}, its number of value comparisons.'\n"
        f"assert _sorts_in_place('selection_sort_desc_count', {v!r}, {sorted(v, reverse=True)!r}) == {len(v) * (len(v) - 1) // 2}, 'selection_sort_desc_count({v!r}) should return {len(v) * (len(v) - 1) // 2}, its number of value comparisons.'\n"
        for v in LISTS),
    "hints": [
        "Read lines with `line = input()` and `while line != \"\":`, appending `int(line)`. Make two copies with `values[:]`, one for each sort.",
        "Copy `selection_sort` and add `comparisons = 0`. Add 1 inside the inner loop, just before the `if` that compares two values.",
        "Print `values` after the swap, inside the outer loop. Return `comparisons` after the outer loop. The descending version selects with `>` and a variable such as `largest`.",
    ],
    "answer": b64(count),
    "answerNote": "Every pass compares all the remaining candidates, so the counts are n - 1, n - 2, down to 1 for any input order. Sorted input does not reduce the total n(n - 1) / 2."}
assert E["count-selection"]["cases"][0]["expected"] == "[1, 4, 6]\n[1, 4, 6]\nAscending comparisons: 3\nFormula: 3\n[6, 4, 1]\n[6, 4, 1]\nDescending comparisons: 3"
assert E["count-selection"]["cases"][1]["expected"] == E["count-selection"]["cases"][2]["expected"] == "Ascending comparisons: 0\nFormula: 0\nDescending comparisons: 0"

# ---------------------------------------------------------------- 4 Compare the comparisons of two sorts (original, awaiting approval)
compare = "\n\n".join(SRC[f"boss_4_{i}"] for i in range(1, 6))
compare_ns = namespace(compare, ["7"])
E["compare-sorts"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 56,
    "starter": SRC["boss_4_starter"],
    "cases": input_cases(compare,
        ("Example 1: typed 7", ["7"]),
        ("Example 2: typed 0", ["0"]),
        ("Typed 1", ["1"]),
        ("Typed 13", ["13"]),
        ("Typed 100", ["100"])),
    "check": AST + '''_fn("merge_count", "left", "right")
_fn("merge_sort_count", "values")
_fn("selection_count", "n")
assert _func_calls("merge_sort_count", _body("merge_sort_count")), "merge_sort_count should call itself on each half of the list."
assert _func_calls("merge_count", _body("merge_sort_count")), "Count the current merge with merge_count in merge_sort_count."
for _name in ("merge_count", "merge_sort_count", "merge", "merge_sort"):
    assert _no_sort(_name), "Do not use sort or sorted in " + _name + ". Use merge_sort for the sorted parts."
''' + returns("merge_count", compare_ns, ([1, 3], [2, 4]), ([], [5]), ([5], []), ([1, 2], [3, 4]), ([3, 4], [1, 2]), ([4], [4]), ([1, 5, 9], [2, 6, 7, 8]))
    + returns("merge_sort_count", compare_ns, *[(v,) for v in LISTS + [[8, 3, 6, 1, 7, 2, 5, 4], list(range(16, 0, -1))]])
    + returns("selection_count", compare_ns, (0,), (1,), (8,), (16,), (32,), (1024,)) + '''_keeps("merge_sort_count", ([8, 3, 6, 1, 7, 2, 5, 4],))
_keeps("merge_count", ([1, 3], [2, 4]))
''',
    "hints": [
        "Copy `merge` and `merge_sort` from sections 5 and 7. `merge_count` runs the same while loop, adds 1 to `comparisons` on each pass, and advances `i` or `j` without building a list.",
        "`merge_sort_count` returns 0 for a list of length 0 or 1. Otherwise it splits at `mid` and calls itself on both parts.",
        "Add the two recursive counts and `merge_count(merge_sort(left_part), merge_sort(right_part))`. `selection_count(n)` returns `n * (n - 1) // 2`.",
        "After `random.seed(seed)`, build each list with `random.randint(1, 100)` in order 8, 16, 32. Print the header with `f\"{'n':>4} {'Selection':>10} {'Merge':>8}\"` and each row with `f\"{n:4d} {selection:10d} {merged:8d}\"`.",
    ],
    "answer": b64(compare),
    "answerNote": "A merge of m elements uses at most m - 1 comparisons, so the maximum counts are 17, 49 and 129. The random counts stay at or below those, far below the selection counts 28, 120 and 496."}
assert E["compare-sorts"]["cases"][0]["expected"] == "   n  Selection    Merge\n   8         28       15\n  16        120       46\n  32        496      119\n[7, 10, 13, 20, 42, 51, 69, 84]"
assert E["compare-sorts"]["cases"][1]["expected"] == "   n  Selection    Merge\n   8         28       17\n  16        120       45\n  32        496      121\n[6, 34, 50, 52, 54, 63, 66, 98]"
for c in E["compare-sorts"]["cases"]:
    merges = [int(line.split()[2]) for line in c["expected"].split("\n")[1:4]]
    assert all(m <= cap for m, cap in zip(merges, (17, 49, 129))), c

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-28-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 28 Boss Problems",
    "short": "L28 bosses",
    "subtitle": "Selection sort and merge sort",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-28/boss/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
for key, spec in E.items():
    for c in spec["cases"]:
        print(key, "|", c["name"], "|", c["expected"].replace("\n", " / "))
