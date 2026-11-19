"""Build workbooks/lecture-27/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_27_SHARED_CONTENT.tex; the listings below are copied from it and
model answers follow its \\solution{...} text. Run from anywhere:

    python3 workbooks/lecture-27/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-27
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
    ns = {"__name__": "lecture27"}
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
SRC['slide_2'] = '''values = [18, 5, 12, 5]
print(5 in values)
print(values.index(5))
'''
SRC['quick_1'] = '''values = [13, 6, 9, 6]
print(7 in values)
print(values.index(6))
'''
SRC['slide_4'] = '''def linear_search(values, target):
    for i in range(len(values)):
        if values[i] == target:
            return i
    return -1

values = [18, 5, 12, 5, 9]
print(linear_search(values, 12))
print(linear_search(values, 7))
'''
SRC['quick_2'] = '''def find(values, target):
    for i in range(len(values)):
        if values[i] == target:
            return i
    return ____(a)____
print(find([2, 11], 8))
'''
SRC['slide_5'] = '''def linear_search(values, target):
    for i in range(len(values)):
        if values[i] == target:
            return i
    return -1

values = [18, 5, 12, 5, 9]
print(linear_search(values, 12))
'''
SRC['slide_6'] = '''def linear_search(values, target):
    for i in range(len(values)):
        if values[i] == target:
            return i
    return -1

values = [18, 5, 12]
print(linear_search(values, 7))
'''
SRC['quick_3'] = '''values = [14, 3, 14, 8]
print(linear_search(values, 14))
print(linear_search(values, 8))
'''
SRC['checkpoint_1_starter'] = '''def first_at_least(values, limit):
    pass

values = [32, 48, 51, 48, 65]
'''
SRC['slide_8'] = '''def first_at_least(values, limit):
    for i in range(len(values)):
        if values[i] >= limit:
            return i
    return -1

values = [32, 48, 51, 48, 65]
print(first_at_least(values, 50))
tests = [[50, 32], [32, 65], [32], []]
for case in tests:
    print(first_at_least(case, 50))
'''
SRC['slide_11'] = '''def binary_search(values, target):
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
    return -1
'''
SRC['quick_5'] = '''low = 2
high = 9
mid = (low + high) ____(a)____ 2
print(mid)
'''
SRC['slide_12_1'] = '''def binary_search(values, target):
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
    return -1
'''
SRC['slide_12_2'] = '''print(binary_search(values,17))
'''
SRC['slide_13_1'] = '''def binary_search(values, target):
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
    return -1
'''
SRC['slide_13_2'] = '''print(binary_search(values, 8))
'''
SRC['slide_15'] = '''values = [1, 4, 5, 8, 9, 12, 17, 20, 24, 32]
'''
SRC['checkpoint_2_starter'] = '''def binary_search(values, target):
    pass

values = [1, 4, 5, 8, 9, 12, 17, 20, 24, 32]
'''
SRC['slide_16_1'] = '''def binary_search(values, target):
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
    return -1
'''
SRC['slide_16_2'] = '''print(binary_search(values,15))
'''
SRC['slide_18'] = '''values = [30, 10, 20]
ordered = sorted(values)

print(linear_search(values, 30))
print(binary_search(ordered, 30))
print(values)
print(ordered)
'''
SRC['slide_19_1'] = '''def search_range(v, target, low, high):
    if low > high:
        return -1
    mid = (low + high) // 2
    if v[mid] == target:
        return mid
    if v[mid] < target:
        return search_range(
            v, target, mid + 1, high)
    return search_range(
        v, target, low, mid - 1)
'''
SRC['slide_19_2'] = '''def binary_search_rec(
        values, target):
    return search_range(
        values, target, 0,
        len(values) - 1)
'''
SRC['slide_20'] = '''def search_range(v, target, low, high):
    if low > high:
        return -1
    mid = (low + high) // 2
    if v[mid] == target:
        return mid
    if v[mid] < target:
        return search_range(
            v, target, mid + 1, high)
    return search_range(
        v, target, low, mid - 1)
'''
SRC['quick_11'] = '''def empty_result(low, high):
    if low ____(a)____ high:
        return -1
    return 0
print(empty_result(5, 4))
'''
SRC['slide_21'] = '''values = [6, 4, 11]
ordered = [1, 4, 7, 11]
'''
SRC['checkpoint_3_starter'] = '''def search_range(v, target, low, high):
    if low > high:
        return -1
    mid = (low + high) // 2
    if v[mid] == target:
        return mid
    if v[mid] < target:
        return search_range(
            v, target, mid + 1, high)
    return search_range(
        v, target, low, mid - 1)

def binary_search_rec(
        values, target):
    return search_range(
        values, target, 0,
        len(values) - 1)

def first_shared(values, ordered):
    pass

values = [6, 4, 11]
ordered = [1, 4, 7, 11]
'''
SRC['slide_22'] = '''def first_shared(values, ordered):
    for i in range(len(values)):
        pos = binary_search_rec(
            ordered, values[i])
        if pos != -1:
            return i
    return -1

values = [6, 4, 11]
ordered = [1, 4, 7, 11]
print(first_shared(values, ordered))
print(first_shared([6, 9], ordered))
print(first_shared([], ordered))
'''
SRC['slide_23'] = '''values = [4, 4, 4]
print(linear_search(values, 4))
pos = binary_search(values, 4)
print(pos)
if pos != -1:
    print(values[pos] == 4)
'''
SRC['quick_12'] = '''values = [3, 5, 5, 5, 9, 11]
print(linear_search(values, 5))
pos = binary_search(values, 5)
print(pos)
print(values[pos])
'''
SRC['practice_1_trace'] = '''def below_eight(values):
    matches = []
    for i in range(len(values)):
        if values[i] < 8:
            matches.append(i)
    return matches

values = [9, 4, 8, 2, 6]
print(below_eight(values))
'''
SRC['practice_1_starter'] = '''def first_below_eight(values):
    pass
'''
SRC['practice_1'] = '''def first_below_eight(values):
    for i in range(len(values)):
        if values[i] < 8:
            return i
    return -1

print(first_below_eight([9, 4, 8, 2, 6]))
print(first_below_eight([8, 10]))
print(first_below_eight([]))
'''
SRC['practice_2_min'] = '''def smallest(values):
    result = None
    for value in values:
        if result is None or value < result:
            result = value
    return result
'''
SRC['practice_2_starter'] = '''def extremes(values):
    pass
'''
SRC['practice_2'] = '''def extremes(values):
    small = None
    large = None
    for value in values:
        if small is None or value < small:
            small = value
        if large is None or value > large:
            large = value
    if small is None:
        return []
    return [small, large]

print(extremes([16, 3, 25, 7]))
print(extremes([6]))
print(extremes([]))
'''
SRC['practice_3_starter'] = '''def search_or_position(values, target):
    pass

values = [6, 14, 23]
'''
SRC['practice_3'] = '''def search_or_position(values, target):
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
    return -low - 1

values = [6, 14, 23]
for target in [2, 18, 30, 14]:
    result = search_or_position(values, target)
    print(result)
    if result < 0:
        k = -result - 1
        print("Insert at", k)
print(search_or_position([], 5))
'''
SRC['practice_4_data'] = '''names = ["Ada", "Bea", "Nia", "Sol"]
numbers = ["555-0142", "555-0183", "555-0127", "555-0164"]
'''
SRC['practice_4_starter'] = '''def phone_number(names, numbers, target):
    pass
'''
SRC['practice_4'] = '''def phone_number(names, numbers, target):
    low = 0
    high = len(names) - 1
    while low <= high:
        mid = (low + high) // 2
        if names[mid] == target:
            return numbers[mid]
        elif names[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return None

names = ["Ada", "Bea", "Nia", "Sol"]
numbers = ["555-0142", "555-0183", "555-0127", "555-0164"]
for target in ["Bea", "Nia", "Zed"]:
    print(phone_number(names, numbers, target))
print(phone_number([], [], "Ada"))
'''
SRC['practice_5_starter'] = '''def has_pair(values, v):
    pass
'''
SRC['practice_5'] = '''def has_pair(values, v):
    for i in range(len(values)):
        target = v - values[i]
        low = i + 1
        high = len(values) - 1
        while low <= high:
            mid = (low + high) // 2
            if values[mid] == target:
                return True
            elif values[mid] < target:
                low = mid + 1
            else:
                high = mid - 1
    return False

print(has_pair([2, 7, 11, 16], 18))
print(has_pair([2, 7, 11, 16], 10))
print(has_pair([5, 5], 10))
print(has_pair([5], 10))
print(has_pair([], 10))
'''
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

E = {}

def ex(name, code, output=True):
    E[name] = example(code, output)
    return E[name]

LINEAR = SRC["slide_4"].split("\nvalues =")[0].rstrip() + "\n"
BINARY = SRC["slide_11"]
RECURSIVE = SRC["slide_19_1"] + "\n" + SRC["slide_19_2"]
HELPERS = LINEAR + "\n" + BINARY + "\n" + RECURSIVE + "\n"
TEN = "values = [1, 4, 5, 8, 9, 12, 17, 20, 24, 32]\n"

# Extra check helpers for searches. `_Counted` is a list that records each
# index the function reads, so a check can confirm a binary search visits
# only a few elements.
SEARCH = '''class _Counted(list):
    def __init__(self, items):
        list.__init__(self, items)
        self.seen = set()
    def __getitem__(self, i):
        if isinstance(i, int):
            self.seen.add(i % len(self) if len(self) else i)
        return list.__getitem__(self, i)
def _visits(name, items, *rest):
    data = _Counted(items)
    _call(name, data, *rest)
    return len(data.seen)
'''

def no_shortcuts(fn, words=("index", "count", "find")):
    lines = ""
    for w in words:
        lines += f'assert not _calls({w!r}, _body({fn!r})), "Write the search with a loop in {fn}. Do not call .{w}()."\n'
    lines += f'assert not [n for n in ast.walk(_body({fn!r})) if isinstance(n, ast.Compare) and any(isinstance(o, (ast.In, ast.NotIn)) for o in n.ops)], "Check the elements one at a time in {fn}. Do not use in to test membership."\n'
    return lines

# ============================================================ 1. A search returns a position
assert ex("ex-position", SRC["slide_2"])["output"] == "True\n1"

# ============================================================ 2. Linear search checks each element
assert ex("ex-linear", SRC["slide_4"])["output"] == "2\n-1"

# ============================================================ 3. Trace a linear search
assert ex("ex-present", SRC["slide_5"])["output"] == "2"
assert ex("ex-absent", SRC["slide_6"])["output"] == "-1"

# Checkpoint 1
cp1 = SRC["slide_8"]
assert out(cp1) == "2\n0\n1\n-1\n-1"
cp1_ns = namespace(cp1)
E["cp1"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": SRC["checkpoint_1_starter"],
    "cases": [case("values = [32, 48, 51, 48, 65] and four test lists", cp1)],
    "check": AST + '''_fn("first_at_least", "values", "limit")
assert _loops(_body("first_at_least")), "Use a loop in first_at_least to check the elements in order."
''' + no_shortcuts("first_at_least", ("index",)) + returns("first_at_least", cp1_ns,
        ([32, 48, 51, 48, 65], 50), ([50, 32], 50), ([32, 65], 50), ([32], 50), ([], 50),
        ([7, 3, 9], 3), ([1, 2], 5), ([5, 5, 5], 5), ([-4, -2, 0], -3)) + '''_keeps("first_at_least", ([32, 48, 51, 48, 65], 50))
''',
    "answer": b64(cp1),
    "answerNote": "The loop returns at the first value that is at least the limit. The return -1 after the loop runs only when no value qualifies."}
E["cp1-max"] = {"type": "table", "xp": 1, "blanks": {
    "n": accept("n", "len(values)", "n checks", width="7rem", placeholder="checks", show="n")}}

# ============================================================ 4. The cost of linear search
# (static table)

# ============================================================ 5. Binary search removes half the range
ex("ex-binary", BINARY + "\n" + TEN + "print(binary_search(values, 17))\nprint(binary_search(values, 15))\n")
assert E["ex-binary"]["output"] == "6\n-1"

# ============================================================ 6. Trace a binary search
ex("ex-trace17", BINARY + "\n" + TEN + SRC["slide_12_2"].replace("values,17", "values, 17"))
assert E["ex-trace17"]["output"] == "6"

# ============================================================ 7. Sorted data and a smaller range
ex("ex-unsorted", BINARY + "\nvalues = [1, 8, 4, 12, 20]\n" + SRC["slide_13_2"])
assert E["ex-unsorted"]["output"] == "-1"

# Checkpoint 2
cp2 = SRC["slide_16_1"] + "\n" + TEN + "print(binary_search(values, 15))\n"
assert out(cp2) == "-1"
cp2_ns = namespace(cp2)
CP2_CALLS = [([1, 4, 5, 8, 9, 12, 17, 20, 24, 32], t) for t in (1, 32, 9, 17, 15, 0, 40)] + [([], 3), ([6], 6), ([6], 2), ([2, 7], 7)]
E["cp2"] = {"type": "code", "xp": 5, "minLines": 14,
    "starter": SRC["checkpoint_2_starter"],
    "cases": [case("search for 15", cp2)],
    "check": AST + SEARCH + '''_fn("binary_search", "values", "target")
assert [n for n in ast.walk(_body("binary_search")) if isinstance(n, ast.While)], "Use a while loop with low and high in binary_search."
''' + no_shortcuts("binary_search") + returns("binary_search", cp2_ns, *CP2_CALLS) + '''_keeps("binary_search", ([1, 4, 5, 8, 9, 12, 17, 20, 24, 32], 15))
for _n in (10, 16, 100):
    for _t in (0, 1, 2 * _n - 1, 2 * _n + 5):
        _v = _visits("binary_search", list(range(1, 2 * _n, 2)), _t)
        assert _v <= _n.bit_length(), "binary_search visited " + str(_v) + " elements of a sorted list of " + str(_n) + " elements. A binary search checks at most " + str(_n.bit_length()) + ". Move low or high past mid after each failed check."
''',
    "answer": b64(cp2),
    "answerNote": "After a middle value below the target, low moves to mid + 1. After a middle value above it, high moves to mid - 1."}
CP2_TRACE = [("0", "9", "4", "9"), ("5", "9", "7", "20"), ("5", "6", "5", "12"), ("6", "6", "6", "17")]
blanks = {}
for i, row in enumerate(CP2_TRACE, 1):
    for name, value in zip(("low", "high", "mid", "val"), row):
        blanks[f"{name}{i}"] = accept(value, width="3.5rem", placeholder="")
blanks["flow"] = accept("6", width="3.5rem", placeholder="")
blanks["fhigh"] = accept("5", width="3.5rem", placeholder="")
blanks["nbin"] = accept("4", width="3.5rem", placeholder="")
blanks["nlin"] = accept("10", width="3.5rem", placeholder="")
E["cp2-trace"] = {"type": "table", "xp": 1, "blanks": blanks}

# ============================================================ 8. The cost of binary search and the choice
assert ex("ex-choice", HELPERS + "\n" + SRC["slide_18"])["output"] == "0\n2\n[30, 10, 20]\n[10, 20, 30]"

# ============================================================ 9. Recursive binary search
ex("ex-recursive", RECURSIVE + "\n" + TEN + "print(binary_search_rec(values, 17))\nprint(binary_search_rec(values, 15))\n")
assert E["ex-recursive"]["output"] == "6\n-1"
ex("ex-rec-trace", SRC["slide_20"] + "\n" + TEN + "print(search_range(values, 15, 0, 9))\n")
assert E["ex-rec-trace"]["output"] == "-1"

# Checkpoint 3
cp3_defs = SRC["checkpoint_3_starter"].split("def first_shared")[0]
cp3 = cp3_defs + SRC["slide_22"]
assert out(cp3) == "1\n-1\n-1"
cp3_ns = namespace(cp3)
E["cp3"] = {"type": "code", "xp": 5, "minLines": 26,
    "starter": SRC["checkpoint_3_starter"],
    "cases": [case("values = [6, 4, 11], then [6, 9] and []", cp3)],
    "check": AST + '''_fn("first_shared", "values", "ordered")
assert _func_calls("binary_search_rec", _body("first_shared")), "Call binary_search_rec inside first_shared for each candidate."
''' + no_shortcuts("first_shared", ("index", "count")) + returns("first_shared", cp3_ns,
        ([6, 4, 11], [1, 4, 7, 11]), ([6, 9], [1, 4, 7, 11]), ([], [1, 4, 7, 11]), ([3, 5], []),
        ([11, 1], [1, 4, 7, 11]), ([2, 2, 7], [7]), ([8, 3, 4], [1, 3, 4, 8])) + '''_keeps("first_shared", ([6, 4, 11], [1, 4, 7, 11]))
_o = [1, 4, 7, 11]
first_shared([6, 4, 11], _o)
assert _o == [1, 4, 7, 11], "first_shared changed the ordered list to " + repr(_o) + ". Keep both lists unchanged."
''',
    "answer": b64(cp3),
    "answerNote": "The loop visits the candidates from left to right. The first search result that is not -1 gives the answer index."}
E["cp3-trace"] = {"type": "table", "xp": 1, "blanks": {
    "t1": accept("6", width="3.5rem", placeholder=""), "r1": accept("-1", width="3.5rem", placeholder=""),
    "t2": accept("4", width="3.5rem", placeholder=""), "r2": accept("1", width="3.5rem", placeholder="")}}

# ============================================================ 10. Duplicate values and result checks
assert ex("ex-duplicates", HELPERS + "\n" + SRC["slide_23"])["output"] == "0\n1\nTrue"

# ============================================================ Coding Practice
# 1. Collect matching indexes (R6.15)
assert ex("ex-p1-trace", SRC["practice_1_trace"])["output"] == "[1, 3, 4]"
E["p1-trace"] = {"type": "table", "xp": 1, "blanks": {
    **{f"t{i}": accept(v, width="5rem", placeholder="", show=v) for i, v in enumerate(["False", "True", "False", "True", "True"], 1)},
    **{f"r{i}": lst(v, width="8rem") for i, v in enumerate(["[]", "[1]", "[1]", "[1, 3]", "[1, 3, 4]"], 1)},
    "ret": lst("[1, 3, 4]", width="8rem")}}
p1 = SRC["practice_1"]
assert out(p1) == "1\n-1\n-1"
p1_ns = namespace(p1)
E["p1"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": SRC["practice_1_starter"].rstrip("\n") + "\n\n# Print the three test results here.\n",
    "cases": [case("[9, 4, 8, 2, 6], [8, 10] and []", p1)],
    "check": AST + '''_fn("first_below_eight", "values")
assert _loops(_body("first_below_eight")), "Use a loop in first_below_eight."
assert not _calls("append", _body("first_below_eight")), "first_below_eight returns one index. Stop at the first match with return instead of appending."
''' + returns("first_below_eight", p1_ns, ([9, 4, 8, 2, 6],), ([8, 10],), ([],), ([3],), ([8, 9, 7],), ([8, 8, 8],)) + '''_keeps("first_below_eight", ([9, 4, 8, 2, 6],))
''',
    "answer": b64(p1),
    "answerNote": "return i ends the function at the first match. return -1 after the loop handles no match and the empty list."}

# 2. Count visits while finding extremes (R12.8)
assert ex("ex-p2-min", SRC["practice_2_min"] + "\nprint(smallest([16, 3, 25, 7]))\nprint(smallest([]))\n")["output"] == "3\nNone"
E["p2-counts"] = {"type": "table", "xp": 1, "blanks": {
    "s1": accept("1", width="5rem", placeholder=""), "s10": accept("10", width="5rem", placeholder=""),
    "s1000": accept("1000", "1,000", width="5rem", placeholder="", show="1000"),
    "b1": accept("1", width="5rem", placeholder=""), "b10": accept("10", width="5rem", placeholder=""),
    "b1000": accept("1000", "1,000", width="5rem", placeholder="", show="1000"),
    "lfirst": accept("1", width="5rem", placeholder=""),
    "labsent": accept("1000", "1,000", width="5rem", placeholder="", show="1000")}}
p2 = SRC["practice_2"]
assert out(p2) == "[3, 25]\n[6, 6]\n[]"
p2_ns = namespace(p2)
E["p2"] = {"type": "code", "xp": 5, "minLines": 14,
    "starter": SRC["practice_2_starter"].rstrip("\n") + "\n\n# Print the three test results here.\n",
    "cases": [case("[16, 3, 25, 7], [6] and []", p2)],
    "check": AST + '''_fn("extremes", "values")
_f = _body("extremes")
assert len(_loops(_f)) == 1, "Find both extremes in one loop in extremes."
assert not _func_calls("min", _f) and not _func_calls("max", _f) and not _func_calls("sorted", _f) and not _calls("sort", _f), "Compare the values yourself in extremes. Do not use min, max or sorting."
''' + returns("extremes", p2_ns, ([16, 3, 25, 7],), ([6],), ([],), ([-2, -9, -4],), ([5, 5],), ([1, 2, 3, 4],)) + '''_keeps("extremes", ([16, 3, 25, 7],))
''',
    "answer": b64(p2),
    "answerNote": "One loop visits each element once. It compares that element with both extremes."}

# 3. Return an insertion position (P12.15)
p3 = SRC["practice_3"]
assert out(p3) == "-1\nInsert at 0\n-3\nInsert at 2\n-4\nInsert at 3\n1\n-1"
p3_ns = namespace(p3)
P3_CALLS = [([6, 14, 23], t) for t in (2, 6, 10, 14, 18, 23, 30)] + [([], 5), ([4], 4), ([4], 1), ([4], 9), ([1, 3, 5, 7, 9, 11], 8)]
E["p3"] = {"type": "code", "xp": 5, "minLines": 20,
    "starter": SRC["practice_3_starter"].rstrip("\n") + "\n\n# Search for 2, 18, 30 and 14. Then search an empty list for 5.\n",
    "cases": [case("targets 2, 18, 30, 14, then an empty list", p3)],
    "check": AST + SEARCH + '''_fn("search_or_position", "values", "target")
assert [n for n in ast.walk(_body("search_or_position")) if isinstance(n, ast.While)], "Use a binary search with a while loop in search_or_position."
''' + no_shortcuts("search_or_position") + returns("search_or_position", p3_ns, *P3_CALLS) + '''_keeps("search_or_position", ([6, 14, 23], 10))
_v = _visits("search_or_position", list(range(0, 200, 2)), 101)
assert _v <= 7, "search_or_position visited " + str(_v) + " elements of a sorted list of 100 elements. Use binary search, which checks at most 7."
''',
    "answer": b64(p3),
    "answerNote": "When the loop ends without a match, low is the insertion index k. The function returns -k - 1, so every missing result is negative."}

# 4. Look up a phone number (P12.4)
p4 = SRC["practice_4"]
assert out(p4) == "555-0183\n555-0127\nNone\nNone"
p4_ns = namespace(p4)
NAMES = ["Ada", "Bea", "Nia", "Sol"]
NUMBERS = ["555-0142", "555-0183", "555-0127", "555-0164"]
E["p4"] = {"type": "code", "xp": 5, "minLines": 16,
    "starter": SRC["practice_4_starter"].rstrip("\n") + "\n\n" + SRC["practice_4_data"] + "\n# Look up Bea, Nia and Zed. Then test empty lists.\n",
    "cases": [case("Bea, Nia, Zed, then empty lists", p4)],
    "check": AST + SEARCH + '''_fn("phone_number", "names", "numbers", "target")
assert [n for n in ast.walk(_body("phone_number")) if isinstance(n, ast.While)], "Use a binary search with a while loop on names in phone_number."
''' + no_shortcuts("phone_number") + returns("phone_number", p4_ns,
        *[(NAMES, NUMBERS, t) for t in ("Ada", "Bea", "Nia", "Sol", "Al", "Cy", "Zed")], ([], [], "Ada")) + '''_keeps("phone_number", (["Ada", "Bea", "Nia", "Sol"], ["555-0142", "555-0183", "555-0127", "555-0164"], "Nia"))
_names = ["n" + str(100 + i) for i in range(64)]
_nums = [str(i) for i in range(64)]
_data = _Counted(_names)
_call("phone_number", _data, _nums, "n999")
assert len(_data.seen) <= 7, "phone_number visited " + str(len(_data.seen)) + " of 64 names. Use binary search on names, which checks at most 7."
''',
    "answer": b64(p4),
    "answerNote": "The binary search runs on names. The index of the matching name selects the number from the related list."}

# 5. Find two values with a given sum (R12.25)
p5 = SRC["practice_5"]
assert out(p5) == "True\nFalse\nTrue\nFalse\nFalse"
p5_ns = namespace(p5)
def brute(values, v):
    return any(values[i] + values[j] == v for i in range(len(values)) for j in range(i + 1, len(values)))
P5_CALLS = [([2, 7, 11, 16], 18), ([2, 7, 11, 16], 10), ([5, 5], 10), ([5], 10), ([], 10),
            ([1, 3, 5, 7], 8), ([1, 3, 5, 7], 2), ([1, 3, 5, 7], 14), ([-4, 0, 4], 0), ([3, 3, 3], 6)]
for vals, v in P5_CALLS:
    assert p5_ns["has_pair"](list(vals), v) == brute(vals, v), (vals, v)
E["p5"] = {"type": "code", "xp": 10, "minLines": 22,
    "starter": SRC["practice_5_starter"].rstrip("\n") + "\n\n# Print the five test results here.\n",
    "cases": [case("the five listed tests", p5)],
    "check": AST + '''_fn("has_pair", "values", "v")
assert [n for n in ast.walk(_body("has_pair")) if isinstance(n, ast.While)], "Use a binary search with a while loop to find each partner in has_pair."
''' + no_shortcuts("has_pair") + returns("has_pair", p5_ns, *P5_CALLS) + '''_keeps("has_pair", ([2, 7, 11, 16], 18))
''',
    "answer": b64(p5),
    "answerNote": "Each search covers only the indexes after i, so an element never pairs with itself."}
E["p5-cost"] = {"type": "table", "xp": 1, "blanks": {
    "bin": accept("80", width="5rem", placeholder=""), "pairs": accept("120", width="5rem", placeholder="")}}
assert 16 * (16).bit_length() == 80 and 16 * 15 // 2 == 120

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

def checks_linear(values, target):
    n = 0
    for v in values:
        n += 1
        if v == target:
            break
    return n

def checks_binary(values, target):
    low, high, n = 0, len(values) - 1, 0
    while low <= high:
        mid = (low + high) // 2
        n += 1
        if values[mid] == target:
            break
        elif values[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return n

E["q1"] = predict(SRC["quick_1"])
assert out(SRC["quick_1"]) == "False\n1"
E["q2"] = gap("quick_2", ["-1"], "-1", "5rem")
E["q3"] = predict(LINEAR + SRC["quick_3"])
assert out(LINEAR + SRC["quick_3"]) == "0\n3"
assert checks_linear([4, 7, 2, 8, 6, 19, 1], 19) == 6
E["q4"] = choice("B")
E["q5"] = gap("quick_5", ["//"], "5", "5rem")
# Question 6: the first middle check of 22 in [2, 6, 10, 14, 18, 22, 26] is index 3 (14), so low = 4.
assert (0 + 6) // 2 == 3 and [2, 6, 10, 14, 18, 22, 26][3] < 22
E["q6"] = choice("D")
assert (4 + 4) // 2 == 4 and (3 + 7) // 2 == 5
E["q7"] = true_false(True, False)
assert out(BINARY + "print(binary_search([2, 9, 5, 13, 21], 9))") == "-1"
assert (2 + 3) // 2 == 2
E["q8"] = true_false(False, True)
assert max(checks_binary(list(range(16)), t) for t in range(-1, 17)) == 5
E["q9"] = choice("A")
assert out("values = [27, 7, 17]\nordered = sorted(values)\nprint(values)\nprint(ordered.index(27))") == "[27, 7, 17]\n2"
E["q10"] = true_false(True, False)
E["q11"] = gap("quick_11", [">"], "-1", "5rem")
E["q12"] = predict(HELPERS + SRC["quick_12"])
assert out(HELPERS + SRC["quick_12"]) == "1\n2\n5"

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-27",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 27 Workbook",
    "subtitle": "Linear and binary search",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-27/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
