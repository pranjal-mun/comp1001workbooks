"""Build workbooks/lecture-28/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_28_SHARED_CONTENT.tex; the listings below are copied from it and
model answers follow its \\solution{...} text. Run from anywhere:

    python3 workbooks/lecture-28/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-28
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
    ns = {"__name__": "lecture28"}
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


# Listings from the kit, in workbook order.
SRC = {}
SRC['quick_1'] = '''values = [9, 2, 9, 4]
print(sorted(values))
print(values)'''
SRC['slide_4'] = '''values = [5, 2, 9, 1]
i = 0
smallest = 3
values[i], values[smallest] = values[smallest], values[i]
print(values)'''
SRC['quick_2'] = '''values = [6, 4, 1]
i = 0
smallest = ____(a)____
values[i], values[smallest] = values[smallest], values[i]
print(values)'''
SRC['slide_5'] = '''def selection_sort(values):
    n = len(values)
    for i in range(n - 1):
        smallest = i
        for j in range(i + 1, n):
            if values[j] < values[smallest]:
                smallest = j
        values[i], values[smallest] = values[smallest], values[i]'''
SRC['checkpoint_1_starter'] = '''def selection_desc(values):
    pass

values = [3, 7, 2, 7]'''
SRC['slide_10'] = '''def selection_desc(values):
    n = len(values)
    for i in range(n - 1):
        largest = i
        for j in range(i + 1, n):
            if values[j] > values[largest]:
                largest = j
        values[i], values[largest] = values[largest], values[i]'''
SRC['checkpoint_1_test'] = '''values = [3, 7, 2, 7]
selection_desc(values)
print(values)'''
SRC['slide_12'] = '''def merge(left, right):
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
    return result'''
SRC['quick_7'] = '''right = [4, 8, 9]
j = 1
result = [1, 4]
result.extend(____(a)____)
print(result)'''
SRC['slide_13'] = '''def merge(left, right):
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
    return result'''
SRC['quick_9'] = '''print(merge([3, 7], [2, 8, 9]))
print(merge([], [6]))'''
SRC['slide_17'] = '''def merge_sort(values):
    if len(values) <= 1:
        return values[:]
    mid = len(values) // 2
    left = merge_sort(values[:mid])
    right = merge_sort(values[mid:])
    return merge(left, right)'''
SRC['quick_10'] = '''values = [9, 4, 6, 2, 5]
mid = len(values) // ____(a)____
print(values[:mid])
print(values[mid:])'''
SRC['slide_18'] = '''def merge_sort(values):
    if len(values) <= 1:
        return values[:]
    mid = len(values) // 2
    left = merge_sort(values[:mid])
    right = merge_sort(values[mid:])
    return merge(left, right)'''
SRC['big_o_1'] = '''n = 8
steps = 0
for i in range(n):
    steps = steps + 1
print(steps)'''
SRC['big_o_2'] = '''n = 8
steps = 0
for i in range(n):
    for j in range(n):
        steps = steps + 1
print(steps)'''
SRC['big_o_3'] = '''n = 8
steps = 0
while n > 1:
    n = n // 2
    steps = steps + 1
print(steps)'''
SRC['quick_13'] = '''def count_pairs(values):
    count = 0
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] == values[j]:
                count = count + 1
    return count
'''
SRC['quick_14'] = '''def show_total_and_largest(values):
    total = 0
    for v in values:
        total = total + v
    print(total)
    largest = values[0]
    for v in values:
        if v > largest:
            largest = v
    print(largest)
'''
SRC['quick_15'] = '''def count_halvings(values):
    steps = 0
    for v in values:
        k = len(values)
        while k > 1:
            k = k // 2
            steps = steps + 1
    return steps
'''
SRC['checkpoint_2_starter'] = '''def merge(left, right):
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

def merge_sort(values):
    pass

values = [7, 2, 7]'''
SRC['slide_23'] = '''def merge_sort(values):
    if len(values) <= 1:
        return values[:]
    mid = len(values) // 2
    left = merge_sort(values[:mid])
    right = merge_sort(values[mid:])
    return merge(left, right)'''
SRC['checkpoint_2_test'] = '''values = [7, 2, 7]
print(merge_sort(values))
print(values)'''
SRC['practice_1_starter'] = '''def merge_desc(left, right):
    pass

def merge_sort_desc(values):
    pass'''
SRC['practice_1_merge'] = '''def merge_desc(left, right):
    result = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] >= right[j]:
            result.append(left[i])
            i = i + 1
        else:
            result.append(right[j])
            j = j + 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result'''
SRC['practice_1'] = '''def merge_sort_desc(values):
    if len(values) <= 1:
        return values[:]
    mid = len(values) // 2
    left = merge_sort_desc(values[:mid])
    right = merge_sort_desc(values[mid:])
    return merge_desc(left, right)

for case in [[], [5], [6, 2, 6, 9, 1], [9, 6, 4, 1]]:
    print(merge_sort_desc(case))
    print(case)'''
SRC['practice_2'] = '''def unique_counting(values):
    result = values[:]
    i = 0
    while i < len(result):
        copies = result.count(result[i])
        if copies > 1:
            result.pop(i)
        else:
            i = i + 1
    return result

values = [4, 2, 4, 7, 2]
print(unique_counting(values))
print(values)'''
SRC['practice_3_starter'] = '''def unique_sorted(values):
    pass'''
SRC['practice_3'] = '''def unique_sorted(values):
    ordered = sorted(values)
    result = []
    for value in ordered:
        if len(result) == 0 or value != result[-1]:
            result.append(value)
    return result

for case in [[8, 3, 8, 1, 3], [], [5, 5, 5]]:
    print(unique_sorted(case))'''
SRC['practice_4_starter'] = '''def merge_sort_loop(values):
    pass'''
SRC['practice_4_merge'] = '''def merge(left, right):
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
    return result'''
SRC['practice_4'] = '''def merge_sort_loop(values):
    result = values[:]
    width = 1
    while width < len(result):
        next_result = []
        for start in range(0, len(result), 2 * width):
            left = result[start:start + width]
            right = result[start + width:start + 2 * width]
            next_result.extend(merge(left, right))
        result = next_result
        width = width * 2
    return result

for case in [[4], [7, 2], [9, 4, 7, 2, 8, 3, 6, 1]]:
    print(merge_sort_loop(case))'''
SRC['practice_5_starter'] = '''def unique_in_order(values):
    pass'''
SRC['practice_5_helpers'] = '''def unique_sorted(values):
    ordered = sorted(values)
    result = []
    for value in ordered:
        if len(result) == 0 or value != result[-1]:
            result.append(value)
    return result


def binary_search(values, target):
    low = 0
    high = len(values) - 1
    while low <= high:
        mid = (low + high) // 2
        if values[mid] == target:
            return mid
        elif values[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1'''
SRC['practice_5'] = '''def unique_in_order(values):
    keys = unique_sorted(values)
    used = [False] * len(keys)
    result = []
    for value in values:
        pos = binary_search(keys, value)
        if not used[pos]:
            result.append(value)
            used[pos] = True
    return result

for case in [[4, 2, 4, 7, 2], [], [9, 3, 6]]:
    print(unique_in_order(case))'''
SRC['boss_1_starter'] = '''def selection_sort(values):
    pass

seed = int(input())'''
SRC['boss_1_1'] = '''def selection_sort(values):
    n = len(values)
    for i in range(n - 1):
        smallest = i
        for j in range(i + 1, n):
            if values[j] < values[smallest]:
                smallest = j
        values[i], values[smallest] = values[smallest], values[i]'''
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
print(sorted(picks))'''
SRC['boss_2_starter'] = '''def merge_unique(left, right):
    pass

left = [int(word) for word in input().split()]
right = [int(word) for word in input().split()]'''
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
    return result'''
SRC['boss_2_2'] = '''left = [int(word) for word in input().split()]
right = [int(word) for word in input().split()]
result = merge_unique(left, right)
print(result)
print(len(result))'''
SRC['boss_3_starter'] = '''def selection_sort_count(values):
    pass

def selection_sort_desc_count(values):
    pass

values = []'''
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
    return comparisons'''
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
    return comparisons'''
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
print("Descending comparisons:", count)'''
SRC['boss_4_starter'] = '''def merge_count(left, right):
    pass

def merge_sort_count(values):
    pass

def selection_count(n):
    pass

seed = int(input())'''
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
    return result'''
SRC['boss_4_2'] = '''def merge_sort(values):
    if len(values) <= 1:
        return values[:]
    mid = len(values) // 2
    left = merge_sort(values[:mid])
    right = merge_sort(values[mid:])
    return merge(left, right)'''
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
    return comparisons'''
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
    return n * (n - 1) // 2'''
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
print(sorted(eight_values))'''

E = {}

def ex(name, code, output=True):
    E[name] = example(code, output)
    return E[name]

SELECTION = SRC["slide_5"]
MERGE = SRC["slide_12"]
MERGE_SORT = SRC["slide_17"]
assert SRC["slide_13"] == MERGE
assert SRC["slide_18"] == SRC["slide_23"] == MERGE_SORT

# Extra check helpers for sorting. `_stores(name)` is true when a function
# assigns to an element such as values[i]. `_sorts_in_place` calls a function
# on a copy of a list and compares the list afterwards. `_keeps_all` checks
# that a call leaves every list argument unchanged. `_uses_in(name)` finds a
# membership test such as `x in values`.
SORTING = '''def _stores(name):
    return any(isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store) for n in ast.walk(_body(name)))
def _sorts_in_place(name, items, want):
    data = list(items)
    value, printed = _call(name, data)
    assert data == want, name + "(" + repr(list(items)) + ") left the list as " + repr(data) + ". It should become " + repr(want) + "."
    assert value is None, name + " should change the list in place and return nothing, not " + repr(value) + "."
def _keeps_all(name, args):
    given = copy.deepcopy(list(args))
    _call(name, *given)
    assert given == list(args), _shown(name, args) + " changed an input list. Keep every input list unchanged."
def _uses_in(name):
    return [n for n in ast.walk(_body(name)) if isinstance(n, ast.Compare) and any(isinstance(o, (ast.In, ast.NotIn)) for o in n.ops)]
'''

def no_builtin_sort(*fns):
    lines = ""
    for fn in fns:
        lines += f'assert not _func_calls("sorted", _body({fn!r})) and not _calls("sort", _body({fn!r})), "Sort the values yourself in {fn}. Do not use sort or sorted."\n'
    return lines

LISTS = [[], [4], [2, 1], [1, 2], [3, 7, 2, 7], [5, 2, 9, 1], [9, 8, 7, 6, 5], [1, 2, 3, 4], [4, 4, 4], [-3, 10, 0, -3, 8, 2]]

# ============================================================ 2. Selection sort selects and swaps
assert ex("ex-swap", SRC["slide_4"])["output"] == "[1, 2, 9, 5]"

# ============================================================ 3. The selection sort algorithm and function
assert ex("ex-selection", SELECTION + "\n\nvalues = [5, 2, 9, 1]\nselection_sort(values)\nprint(values)\n")["output"] == "[1, 2, 5, 9]"

# Checkpoint 1
cp1 = SRC["slide_10"] + "\n\n" + SRC["checkpoint_1_test"]
assert out(cp1) == "[7, 7, 3, 2]"
E["cp1"] = {"type": "code", "xp": 5, "minLines": 14,
    "starter": SRC["checkpoint_1_starter"],
    "cases": [case("values = [3, 7, 2, 7]", cp1)],
    "check": AST + SORTING + '''_fn("selection_desc", "values")
assert len(_loops(_body("selection_desc"))) >= 2, "Use selection sort in selection_desc: an outer loop over the positions and an inner loop that finds the largest remaining value."
assert _stores("selection_desc"), "Swap the values inside the list in selection_desc, for example values[i], values[largest] = values[largest], values[i]."
''' + no_builtin_sort("selection_desc") + '''assert not _func_calls("max", _body("selection_desc")), "Find the largest value with the inner loop in selection_desc. Do not use max."
''' + "".join(f"_sorts_in_place('selection_desc', {v!r}, {sorted(v, reverse=True)!r})\n" for v in LISTS),
    "answer": b64(cp1),
    "answerNote": "Each pass selects the largest remaining value with a strict > test. The swap puts it at index i."}

def desc_trace(values):
    values, rows, comparisons = list(values), [], 0
    for i in range(len(values) - 1):
        largest = i
        for j in range(i + 1, len(values)):
            comparisons += 1
            if values[j] > values[largest]:
                largest = j
        values[i], values[largest] = values[largest], values[i]
        rows.append((str(largest), str(values)))
    return rows, comparisons
rows, comparisons = desc_trace([3, 7, 2, 7])
assert rows == [("1", "[7, 3, 2, 7]"), ("3", "[7, 7, 2, 3]"), ("3", "[7, 7, 3, 2]")] and comparisons == 6
blanks = {}
for i, (index, after) in enumerate(rows, 1):
    blanks[f"s{i}"] = accept(index, width="3.5rem", placeholder="")
    blanks[f"l{i}"] = lst(after, width="10rem")
blanks["cmp"] = accept("6", width="3.5rem", placeholder="")
E["cp1-trace"] = {"type": "table", "xp": 1, "blanks": blanks}

# ============================================================ 5. Merging two sorted lists
assert ex("ex-merge", MERGE + "\n\nprint(merge([2, 6], [1, 4, 8]))\n")["output"] == "[1, 2, 4, 6, 8]"

# ============================================================ 6. Trace a merge
assert ex("ex-merge-trace", MERGE + "\n\nleft = [2, 6]\nright = [1, 4, 8]\nprint(merge(left, right))\n")["output"] == "[1, 2, 4, 6, 8]"

# ============================================================ 7. Merge sort splits and combines
assert ex("ex-merge-sort", MERGE + "\n\n" + MERGE_SORT + "\n\nvalues = [8, 3, 6, 1]\nprint(merge_sort(values))\nprint(values)\n")["output"] == "[1, 3, 6, 8]\n[8, 3, 6, 1]"

# ============================================================ 8. Trace the recursive calls
CALL_TRACE = '''calls = 0

def merge_sort(values):
    global calls
    calls = calls + 1
    number = calls
    print("call", number, "starts with", values)
    if len(values) <= 1:
        result = values[:]
    else:
        mid = len(values) // 2
        left = merge_sort(values[:mid])
        right = merge_sort(values[mid:])
        result = merge(left, right)
    print("call", number, "returns", result)
    return result
'''
assert out(MERGE + "\n\n" + CALL_TRACE + "\nmerge_sort([8, 3, 6, 1])\n").split("\n")[-1] == "call 1 returns [1, 3, 6, 8]"
assert ex("ex-calls", MERGE + "\n\n" + MERGE_SORT + "\n\nprint(merge_sort([8, 3, 6, 1]))\n")["output"] == "[1, 3, 6, 8]"

# ============================================================ 10. Big O: how the time and memory requirements grow
assert ex("ex-bigo-1", SRC["big_o_1"])["output"] == "8"
assert ex("ex-bigo-2", SRC["big_o_2"])["output"] == "64"
assert ex("ex-bigo-3", SRC["big_o_3"])["output"] == "3"

# Checkpoint 2 (ids cp3 and cp3-trace keep saved progress)
cp3 = SRC["checkpoint_2_starter"].split("def merge_sort")[0] + MERGE_SORT + "\n\n" + SRC["checkpoint_2_test"]
assert out(cp3) == "[2, 7, 7]\n[7, 2, 7]"
cp3_ns = namespace(cp3)
E["cp3"] = {"type": "code", "xp": 5, "minLines": 26,
    "starter": SRC["checkpoint_2_starter"],
    "cases": [case("values = [7, 2, 7]", cp3)],
    "check": AST + SORTING + '''_fn("merge_sort", "values")
assert _func_calls("merge_sort", _body("merge_sort")), "merge_sort should call itself on each half of the list."
assert _func_calls("merge", _body("merge_sort")), "Combine the two sorted halves with the merge function in merge_sort."
''' + no_builtin_sort("merge_sort", "merge") + returns("merge_sort", cp3_ns, *[(v,) for v in LISTS]) + '''_keeps("merge_sort", ([7, 2, 7],))
for _v in ([], [5]):
    assert _call("merge_sort", _v)[0] is not _v, "merge_sort(" + repr(_v) + ") returned the input list itself. Return a copy, values[:], in the base case."
''',
    "answer": b64(cp3),
    "answerNote": "The base case returns a copy. Each recursive call sorts one slice, and merge combines the two results."}
CP3_TRACE = [("[7, 2, 7]", "[2, 7, 7]"), ("[7]", "[7]"), ("[2, 7]", "[2, 7]"), ("[2]", "[2]"), ("[7]", "[7]")]
calls = out(MERGE + "\n\n" + CALL_TRACE + "\nmerge_sort([7, 2, 7])\n").split("\n")
starts = [line.split("starts with ")[1] for line in calls if "starts" in line]
returns_by_call = {line.split()[1]: line.split("returns ")[1] for line in calls if "returns" in line}
assert [(s, returns_by_call[str(i)]) for i, s in enumerate(starts, 1)] == CP3_TRACE
blanks = {}
for i, (given, back) in enumerate(CP3_TRACE, 1):
    blanks[f"i{i}"] = lst(given, width="8rem")
    blanks[f"r{i}"] = lst(back, width="8rem")
blanks["op"] = accept("sorted(values)", "sorted", "sorted()", "sorted(values[:])", width="10rem", placeholder="code", show="sorted(values)")
E["cp3-trace"] = {"type": "table", "xp": 1, "blanks": blanks}

# ============================================================ Coding Practice
# 1. Merge sort in descending order (P12.3)
p1 = SRC["practice_1_merge"] + "\n\n" + SRC["practice_1"]
assert out(p1) == "[]\n[]\n[5]\n[5]\n[9, 6, 6, 2, 1]\n[6, 2, 6, 9, 1]\n[9, 6, 4, 1]\n[9, 6, 4, 1]"
p1_ns = namespace(p1)
E["p1"] = {"type": "code", "xp": 5, "minLines": 24,
    "starter": SRC["practice_1_starter"] + "\n\n# Print each result and its input for the four test lists.\n",
    "cases": [case("[], [5], [6, 2, 6, 9, 1] and [9, 6, 4, 1]", p1)],
    "check": AST + SORTING + '''_fn("merge_desc", "left", "right")
_fn("merge_sort_desc", "values")
assert _func_calls("merge_sort_desc", _body("merge_sort_desc")), "merge_sort_desc should call itself on each half of the list."
assert _func_calls("merge_desc", _body("merge_sort_desc")), "Combine the two sorted halves with merge_desc in merge_sort_desc."
assert not _calls("reverse", _body("merge_sort_desc")) and not _calls("reverse", _body("merge_desc")), "Build the descending order with the comparison in merge_desc. Do not reverse a list."
''' + no_builtin_sort("merge_desc", "merge_sort_desc")
    + returns("merge_desc", p1_ns, ([6, 2], [9, 6, 1]), ([], [4]), ([3], []), ([5, 5], [5]), ([9, 1], [8, 7, 0]))
    + returns("merge_sort_desc", p1_ns, *[(v,) for v in LISTS]) + '''_keeps("merge_sort_desc", ([6, 2, 6, 9, 1],))
_keeps_all("merge_desc", ([6, 2], [9, 6, 1]))
''',
    "answer": b64(p1),
    "answerNote": "Only the comparison changes: >= takes the larger front value, and the left value first when they are equal."}
E["p1-cmp"] = {"type": "table", "xp": 1, "blanks": {
    "cmp": accept("left[i] >= right[j]", "left[i]>=right[j]", ">=", "right[j] <= left[i]", width="12rem", placeholder="code", show="left[i] >= right[j]")}}
E["p1-why"] = short("Each remaining slice is already in descending order. Its values are no larger than every value already in the result, so they belong at the end.")

# 2. Remove duplicates by counting (R12.13)
assert ex("ex-p2", SRC["practice_2"])["output"] == "[4, 7, 2]\n[4, 2, 4, 7, 2]"
def counting_trace(values):
    result, i, rows = values[:], 0, []
    while i < len(result):
        element = result[i]
        copies = result.count(element)
        if copies > 1:
            result.pop(i)
            action = "Remove"
        else:
            action = "Advance"
        rows.append((str(i), str(element), str(copies), action, str(result)))
        if action == "Advance":
            i += 1
    return rows
P2_TRACE = counting_trace([4, 2, 4, 7, 2])
assert P2_TRACE == [("0", "4", "2", "Remove", "[2, 4, 7, 2]"), ("0", "2", "2", "Remove", "[4, 7, 2]"),
                    ("0", "4", "1", "Advance", "[4, 7, 2]"), ("1", "7", "1", "Advance", "[4, 7, 2]"),
                    ("2", "2", "1", "Advance", "[4, 7, 2]")]
blanks = {}
for r, (i, element, copies, action, after) in enumerate(P2_TRACE, 1):
    blanks[f"e{r}"] = accept(element, width="3rem", placeholder="")
    blanks[f"c{r}"] = accept(copies, width="3rem", placeholder="")
    blanks[f"a{r}"] = accept(action, width="6rem", placeholder="action")
    blanks[f"r{r}"] = lst(after, width="9rem")
blanks["survive"] = accept("last", "the last", "the last copy", "last copy", "last one", "the last one", width="9rem", placeholder="first or last", show="The last copy")
blanks["total"] = accept("n*n", "n * n", "n^2", "n**2", "n ** 2", "n²", width="6rem", placeholder="formula", show="n * n")
E["p2-trace"] = {"type": "table", "xp": 1, "blanks": blanks}

# 3. Sort, then compare neighbors (R12.15)
p3 = SRC["practice_3"]
assert out(p3) == "[1, 3, 8]\n[]\n[5]"
p3_ns = namespace(p3)
E["p3"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": SRC["practice_3_starter"] + "\n\n# Print the result for [8, 3, 8, 1, 3], then [], then [5, 5, 5].\n",
    "cases": [case("[8, 3, 8, 1, 3], [] and [5, 5, 5]", p3)],
    "check": AST + SORTING + '''_fn("unique_sorted", "values")
_f = _body("unique_sorted")
assert _func_calls("sorted", _f), "Call sorted(values) in unique_sorted. Then compare neighbors in the sorted list."
assert len(_loops(_f)) == 1, "Use one loop over the sorted list in unique_sorted."
assert not _uses_in("unique_sorted"), "Compare each value with the last value added in unique_sorted. Do not use in to test membership."
assert not _calls("count", _f) and not _func_calls("set", _f), "Compare neighbors in unique_sorted. Do not use count or set."
''' + returns("unique_sorted", p3_ns, *[(v,) for v in LISTS + [[8, 3, 8, 1, 3], [5, 5, 5]]]) + '''_keeps("unique_sorted", ([8, 3, 8, 1, 3],))
''',
    "answer": b64(p3),
    "answerNote": "After sorting, equal values sit next to each other. A value enters the result only when it differs from result[-1]."}
P3_TRACE = [("1", "Add", "[1]"), ("3", "Add", "[1, 3]"), ("3", "Skip", "[1, 3]"), ("8", "Add", "[1, 3, 8]"), ("8", "Skip", "[1, 3, 8]")]
blanks = {}
for r, (element, action, after) in enumerate(P3_TRACE, 1):
    blanks[f"e{r}"] = accept(element, width="3rem", placeholder="")
    blanks[f"a{r}"] = accept(action, width="5rem", placeholder="action")
    blanks[f"r{r}"] = lst(after, width="8rem")
E["p3-trace"] = {"type": "table", "xp": 1, "blanks": blanks}
E["p3-cost"] = {"type": "table", "xp": 1, "blanks": {
    "pass": accept("n-1", "n - 1", width="5rem", placeholder="formula", show="n - 1"),
    "pass1000": accept("999", width="6rem", placeholder=""),
    "total": accept("10999", "10,999", width="6rem", placeholder="", show="10,999")}}
assert 10_000 + 999 == 10999

# 4. Merge sort without recursion (P12.16)
p4 = SRC["practice_4_merge"] + "\n\n" + SRC["practice_4"]
assert out(p4) == "[4]\n[2, 7]\n[1, 2, 3, 4, 6, 7, 8, 9]"
p4_ns = namespace(p4)
P4_LISTS = [[4], [7, 2], [9, 4, 7, 2, 8, 3, 6, 1], [1, 2], [5, 5, 1, 1], [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3]]
E["p4"] = {"type": "code", "xp": 5, "minLines": 28,
    "starter": SRC["practice_4_merge"] + "\n\n" + SRC["practice_4_starter"] + "\n\n# Print the result for [4], then [7, 2], then [9, 4, 7, 2, 8, 3, 6, 1].\n",
    "cases": [case("[4], [7, 2] and [9, 4, 7, 2, 8, 3, 6, 1]", p4)],
    "check": AST + SORTING + '''_fn("merge_sort_loop", "values")
_f = _body("merge_sort_loop")
assert not _func_calls("merge_sort_loop", _f), "Write merge_sort_loop without recursion. Use a while loop that doubles width."
assert [n for n in ast.walk(_f) if isinstance(n, ast.While)], "Use a while loop in merge_sort_loop that runs while width is less than the length."
assert _func_calls("merge", _f), "Combine each pair of neighboring runs with merge in merge_sort_loop."
''' + no_builtin_sort("merge_sort_loop", "merge") + returns("merge_sort_loop", p4_ns, *[(v,) for v in P4_LISTS]) + '''_keeps("merge_sort_loop", ([9, 4, 7, 2, 8, 3, 6, 1],))
''',
    "answer": b64(p4),
    "answerNote": "Each round merges runs of length width into runs of length 2 * width. Eight elements need three rounds."}
def rounds(values):
    result, width, rows = values[:], 1, []
    while width < len(result):
        result = [x for s in range(0, len(result), 2 * width) for x in sorted(result[s:s + 2 * width])]
        rows.append((str(width), str(result)))
        width *= 2
    return rows
P4_ROUNDS = rounds([9, 4, 7, 2, 8, 3, 6, 1])
assert P4_ROUNDS == [("1", "[4, 9, 2, 7, 3, 8, 1, 6]"), ("2", "[2, 4, 7, 9, 1, 3, 6, 8]"), ("4", "[1, 2, 3, 4, 6, 7, 8, 9]")]
blanks = {}
for r, (width, after) in enumerate(P4_ROUNDS, 1):
    blanks[f"w{r}"] = accept(width, width="3rem", placeholder="")
    blanks[f"l{r}"] = lst(after, width="15rem")
blanks["levels"] = accept("3", width="3rem", placeholder="")
E["p4-rounds"] = {"type": "table", "xp": 1, "blanks": blanks}

# 5. Keep the first occurrence in the original order (R12.16)
p5 = SRC["practice_5_helpers"] + "\n\n\n" + SRC["practice_5"]
assert out(p5) == "[4, 2, 7]\n[]\n[9, 3, 6]"
p5_ns = namespace(p5)
E["p5"] = {"type": "code", "xp": 10, "minLines": 40,
    "starter": SRC["practice_5_helpers"] + "\n\n\n" + SRC["practice_5_starter"] + "\n\n# Print the result for [4, 2, 4, 7, 2], then [], then [9, 3, 6].\n",
    "cases": [case("[4, 2, 4, 7, 2], [] and [9, 3, 6]", p5)],
    "check": AST + SORTING + '''_fn("unique_in_order", "values")
_f = _body("unique_in_order")
assert _func_calls("unique_sorted", _f), "Build keys with unique_sorted(values) in unique_in_order."
assert _func_calls("binary_search", _f), "Find each value's index in keys with binary_search in unique_in_order."
assert not _uses_in("unique_in_order"), "Use the used flags to skip later copies in unique_in_order. Do not use in to test membership."
assert not _calls("index", _f) and not _calls("count", _f) and not _func_calls("set", _f), "Use binary_search and the used flags in unique_in_order. Do not use index, count or set."
''' + returns("unique_in_order", p5_ns, *[(v,) for v in LISTS + [[4, 2, 4, 7, 2], [9, 3, 6], [7, 7, 1, 7, 1]]]) + '''_keeps("unique_in_order", ([4, 2, 4, 7, 2],))
''',
    "answer": b64(p5),
    "answerNote": "The first copy of a value sets its flag. Later copies find the same index in keys and are skipped."}
E["p5-cost"] = {"type": "table", "xp": 1, "blanks": {
    "search": accept("20000", "20,000", width="6rem", placeholder="", show="20,000"),
    "total": accept("30999", "30,999", width="6rem", placeholder="", show="30,999"),
    "item2": accept("1000000", "1,000,000", width="7rem", placeholder="", show="1,000,000")}}
assert 1000 * 10 * 2 == 20000 and 10000 + 999 + 20000 == 30999

# ---------------------------------------------------------------- quick checks
def predict(code):
    blanks = {}
    for i, line in enumerate(out(code).split("\n"), 1):
        blanks[f"l{i}"] = lst(line, width="14rem", placeholder="output") if line.startswith("[") else accept(line, placeholder="output")
    return {"type": "table", "xp": 1, "blanks": blanks}

def true_false(*answers):
    forms = {True: ["True", "T"], False: ["False", "F"]}
    return {"type": "table", "xp": 1, "blanks": {f"t{i}": accept(*forms[a], width="6rem", placeholder="True or False", show=forms[a][0]) for i, a in enumerate(answers, 1)}}

def choice(letter):
    return {"type": "table", "xp": 1, "blanks": {"c": accept(letter, f"({letter})", f"{letter})", width="4rem", placeholder="letter", show=letter)}}

def gap(key, fills, want, width="7rem", prefix=""):
    """Every accepted answer for gap (a) must make the program print the stated output."""
    for fill in fills:
        assert out(prefix + SRC[key].replace("____(a)____", fill)) == want, (key, fill)
    return {"type": "table", "xp": 1, "blanks": {"a": accept(*fills, width=width, placeholder="code", show=fills[0])}}

def selection_pick(values):
    smallest = 0
    for j in range(1, len(values)):
        if values[j] < values[smallest]:
            smallest = j
    return smallest

def comparisons(n):
    return sum(range(n))

def levels(n):
    count = 0
    while n > 1:
        n //= 2
        count += 1
    return count

E["q1"] = predict(SRC["quick_1"])
assert out(SRC["quick_1"]) == "[2, 4, 9, 9]\n[9, 2, 9, 4]"
E["q2"] = gap("quick_2", ["2"], "[1, 4, 6]", "5rem")
assert selection_pick([6, 2, 2, 5]) == 1
E["q3"] = choice("B")
assert len(range(6 - 1)) == 5 and len(range(0 - 1)) == 0
E["q4"] = true_false(True, False)
assert comparisons(5) == 10
E["q5"] = choice("C")
assert comparisons(10) == 45
E["q6"] = true_false(False, True)
E["q7"] = gap("quick_7", ["right[j:]", "right[1:]"], "[1, 4, 8, 9]", "8rem")
assert out(MERGE + "\nprint(merge([5], [5]) == [5, 5])") == "True"
E["q8"] = choice("A")
E["q9"] = predict(MERGE + "\n\n" + SRC["quick_9"])
assert out(MERGE + "\n\n" + SRC["quick_9"]) == "[2, 3, 7, 8, 9]\n[6]"
E["q10"] = gap("quick_10", ["2"], "[9, 4]\n[6, 2, 5]", "5rem")
E["q11"] = true_false(True, False)
assert levels(16) == 4
E["q12"] = choice("D")
# Quick check 10 (Big O): step counts grow as n^2, n, and n log2 n
_q13, _q14, _q15 = namespace(SRC["quick_13"]), namespace(SRC["quick_14"]), namespace(SRC["quick_15"])
assert _q13["count_pairs"](list(range(1024))) == 0 and _q15["count_halvings"](list(range(1024))) == 10240
assert 2 * (20000 * 19999) / (10000 * 9999) > 7.99
E["q13"] = choice("D")
E["q14"] = choice("A")
E["q15"] = choice("C")
E["q16"] = choice("B")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-28",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 28 Workbook",
    "subtitle": "Selection sort and merge sort",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-28/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
