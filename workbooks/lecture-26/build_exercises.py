"""Build workbooks/lecture-26/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_26_SHARED_CONTENT.tex; the listings below are copied from it and
model answers follow its \\solution{...} text. Run from anywhere:

    python3 workbooks/lecture-26/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-26
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
    ns = {"__name__": "lecture26"}
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
SRC['slide_2'] = '''def clear_negatives(values):
    """Change values in place."""
    for i in range(len(values)):
        if values[i] < 0:
            values[i] = 0

marks = [6, -2, 4]
result = clear_negatives(marks)
print(marks)
print(result)
'''
SRC['slide_3'] = '''def reset_local(values):
    values = []
marks = [6, -2, 4]
reset_local(marks)
print(marks)
'''
SRC['quick_1'] = '''def drop_last(values):
    values.pop()
nums = [5, 9, 12]
print(drop_last(nums))
print(nums)
'''
SRC['quick_2'] = '''def reset_first(values):
    values[____(a)____] = 0
    values = [7, 7]
nums = [8, 3]
reset_first(nums)
print(nums)
'''
SRC['slide_4'] = '''def nonnegative_copy(values):
    """Return a new list."""
    return [max(0, v)
            for v in values]
marks = [6, -2, 4]
clean = nonnegative_copy(marks)
print(marks)
print(clean)
'''
SRC['slide_5'] = '''def fix_marks(values):
    for i in range(len(values)):
        if values[i] < 0:
            values[i] = 0
    return values

marks = [6, -2, 4]
clean = fix_marks(marks)
print(clean)
print(marks)
'''
SRC['quick_3'] = '''def doubled_copy(values):
    return [v * 2 for v in values]
def double_values(values):
    for i in range(len(values)):
        values[i] = values[i] * 2
values = [3, 5]
'''
SRC['slide_6'] = '''def add_item(item, items=[]):
    items.append(item)
    return items

print(add_item("a"))
print(add_item("b"))
print(add_item("c"))
'''
SRC['quick_5'] = '''def collect(item, items=[]):
    items.append(item)
    return items
print(collect(4))
print(collect(7))
'''
SRC['quick_6'] = '''def collect(item, items=[]):
    items.append(item)
    return items
first = collect(3)
second = collect(8, ____(a)____)
print(first, second)
'''
SRC['slide_7'] = '''def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

print(add_item("a"))
print(add_item("b"))
names = []
add_item("c", names)
print(names)
'''
SRC['checkpoint_1_starter'] = '''def with_mark(mark, marks=None):
    pass
source = [50]
'''
SRC['slide_9_1'] = '''def with_mark(mark, marks=None):
    if marks is None:
        result = []
    else:
        result = marks[:]
    result.append(mark)
    return result
'''
SRC['slide_9_2'] = '''first = with_mark(70)
second = with_mark(80)
source = [50]
third = with_mark(90, source)
print(first, second)
print(source, third)
'''
SRC['slide_11'] = '''values = [2, 4, 6, 8, 10, 12]
half = len(values) // 2
for i in range(half):
    values[i], values[i + half] = values[i + half], values[i]
print(values)
'''
SRC['quick_9'] = '''values = [1, 3, 7, 9]
half = len(values) // 2
for i in range(half):
    values[i], values[i + half] = values[i + half], values[i]
print(values)
'''
SRC['quick_10'] = '''values = [1, 3, 5, 7, 9, 11]
half = len(values) // 2
swaps = 0
for i in range(____(a)____):
    swaps = swaps + 1
print(swaps)
'''
SRC['slide_12'] = '''table = [
    [2, 4, 6],
    [1, 3, 5]
]
print(len(table))
print(len(table[0]))
'''
SRC['quick_11'] = '''table = [[8, 1], [6, 3], [9, 4]]
'''
SRC['slide_13'] = '''table = [[2, 4, 6], [1, 3, 5]]
print(table[1])
print(table[1][2])
table[0][1] = 9
print(table[0])
'''
SRC['slide_14'] = '''grid = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
print(grid[0][2])
print(grid[2][0])
'''
SRC['quick_13'] = '''table = [[8, 6, 4, 2], [9, 7, 5, 3]]
print(table[1][3])
table[0][2] = 11
print(table[0])
'''
SRC['quick_14'] = '''table = [[5, 8, 11], [7, 10, 13]]
print(table[1][____(a)____])
'''
SRC['slide_15'] = '''table = [[2, 4, 6], [1, 3, 5]]
for r in range(len(table)):
    for c in range(len(table[r])):
        print(table[r][c], end=" ")
    print()
'''
SRC['quick_15'] = '''table = [[7, 8], [9, 1]]
for row in table:
    for value in row:
        print(value, end=" ")
    # Replace this comment.
'''
SRC['slide_16'] = '''grid = [[0] * 3] * 2
grid[0][1] = 9
print(grid)
'''
SRC['slide_17_1'] = '''grid = []
for row in range(2):
    new_row = [0] * 3
    grid.append(new_row)
grid[0][1] = 9
print(grid)
'''
SRC['slide_17_2'] = '''grid = [[0] * 3 for row in range(2)]
'''
SRC['quick_17'] = '''table = [[0] * 2] * 3
table[2][0] = 6
print(table)
'''
SRC['quick_18'] = '''table = [[0] * 2 for r in ____(a)____]
table[0][1] = 6
print(table)
'''
SRC['checkpoint_2_starter'] = '''def number_grid(rows, cols):
    pass
'''
SRC['slide_19'] = '''def number_grid(rows, cols):
    result = []
    for r in range(rows):
        cells = []
        for c in range(cols):
            cells.append(10 * r + c)
        result.append(cells)
    return result
grid = number_grid(2, 3)
grid[0][1] = 99
print(grid)
'''
SRC['slide_20_1'] = '''table = [[2, 4], [1, 3]]
outer = table[:]
outer[0][0] = 9
print(table)
'''
SRC['slide_20_2'] = '''table = [[2, 4], [1, 3]]
copy = [row[:] for row in table]
copy[0][0] = 9
print(table)
print(copy)
'''
SRC['quick_19'] = '''table = [[8, 6], [4, 2]]
'''
SRC['slide_21'] = '''def row_totals(table):
    totals = []
    for row in table:
        totals.append(sum(row))
    return totals

table = [[2, 4, 6], [1, 3, 5]]
print(row_totals(table))
'''
SRC['quick_21'] = '''table = [[3, 8], [2, 5], []]
totals = []
for row in table:
    totals.append(sum(row))
print(totals)
'''
SRC['quick_22'] = '''table = [[2, 5], [6, 7]]
totals = []
for row in table:
    totals.append(____(a)____)
print(totals)
'''
SRC['slide_22'] = '''def column_total(table, col):
    total = 0
    for row in table:
        total = total + row[col]
    return total

table = [[2, 4, 6], [1, 3, 5]]
print(column_total(table, 1))
'''
SRC['quick_23'] = '''table = [[4, 6, 8], [1, 3, 5]]
'''
SRC['slide_23'] = '''def table_total(table):
    total = 0
    for row in table:
        for value in row:
            total = total + value
    return total

table = [[2, 4, 6], [1, 3, 5]]
print(table_total(table))
'''
SRC['slide_24'] = '''def clear_cells(table):
    """Change cells in place."""
    for row in table:
        for col in range(len(row)):
            if row[col] < 0:
                row[col] = 0

table = [[-2, 4, -1], [3, -5, 6]]
clear_cells(table)
print(table)
'''
SRC['quick_25'] = '''table = [[1, 5], [2, 8]]
total = 0
for row in table:
    for value in row:
        total = total + value
print(total)
'''
SRC['quick_26'] = '''def set_last(table):
    for row in table:
        ____(a)____ = 8
table = [[3, 1], [5, 2]]
set_last(table)
print(table)
'''
SRC['checkpoint_3_starter'] = '''def row_totals(table):
    totals = []
    for row in table:
        totals.append(sum(row))
    return totals

def column_total(table, col):
    total = 0
    for row in table:
        total = total + row[col]
    return total

def clean_table(table):
    pass
table = [[-2, 4, -1], [3, -5, 6]]
'''
SRC['slide_26'] = '''def clean_table(table):
    result = []
    for row in table:
        new_row = []
        for v in row:
            new_row.append(max(0, v))
        result.append(new_row)
    return result
table = [[-2, 4, -1], [3, -5, 6]]
clean = clean_table(table)
print(clean)
print(row_totals(clean))
print(column_total(clean, 1))
print(table)
'''
SRC['practice_1_bug'] = '''def fill_squares(values):
    result = []
    for i in range(len(values)):
        result.append(i * i)
    values = result

values = [8, 8, 8, 8]
fill_squares(values)
print(values)
'''
SRC['practice_1_starter'] = '''def fill_squares(values):
    pass

def index_squares(values):
    pass
'''
SRC['practice_1'] = '''def fill_squares(values):
    """Change values in place and return None."""
    for i in range(len(values)):
        values[i] = i * i

def index_squares(values):
    """Return a new list and keep values unchanged."""
    result = []
    for i in range(len(values)):
        result.append(i * i)
    return result

values = [8, 8, 8, 8]
print(index_squares(values))
print(values)
print(fill_squares(values))
print(values)
print(index_squares([]))
print(fill_squares([]))
'''
SRC['practice_2_starter'] = '''# Write four headers and descriptions above your implementations.
'''
SRC['practice_2'] = '''def sort_decreasing(values):
    """Sort values in place and return None."""
    values.sort(reverse=True)

def below_limit_copy(values, limit):
    """Return a new list and keep values unchanged."""
    return [v for v in values if v < limit]

values = [7, 2, 9, 2]
print(below_limit_copy(values, 7))
print(values)
print(sort_decreasing(values))
print(values)
empty = []
print(below_limit_copy(empty, 7))
print(sort_decreasing(empty))
print(empty)
'''
SRC['practice_3_starter'] = '''def alternating_copy(first, second):
    pass
'''
SRC['practice_3'] = '''def alternating_copy(first, second):
    """Return a new list and keep both inputs unchanged."""
    result = []
    i = 0
    while i < len(first) or i < len(second):
        if i < len(first):
            result.append(first[i])
        if i < len(second):
            result.append(second[i])
        i = i + 1
    return result

first = [3, 8]
second = [6, 1, 5, 9]
print(alternating_copy(first, second))
print(first)
print(second)
print(alternating_copy([], [4, 7]))
print(alternating_copy([4, 7], []))
print(alternating_copy([], []))
'''
SRC['practice_4_starter'] = '''m = 3
n = 5
# Build, fill, total, and print the two tables.
'''
SRC['practice_4'] = '''m = 3
n = 5
table = [[0] * n for r in range(m)]
for r in range(m):
    for c in range(n):
        table[r][c] = (r + c) % 2
print("Checkerboard:")
for row in table:
    for value in row:
        print(value, end=" ")
    print()
table = [[0] * n for r in range(m)]
for r in range(m):
    for c in range(n):
        if r == 0 or r == m - 1 or c == 0 or c == n - 1:
            table[r][c] = 1
total = 0
for row in table:
    total = total + sum(row)
print("Border:")
for row in table:
    for value in row:
        print(value, end=" ")
    print()
print("Border total:", total)
'''
SRC['practice_5_data'] = '''heights = [[1, 3, 5, 2, 6],
           [4, 2, 0, 5, 3],
           [6, 5, 3, 1, 4],
           [2, 4, 6, 0, 5]]
'''
SRC['practice_5_starter'] = '''def print_flood_map(heights, water_level):
    pass
'''
SRC['practice_5'] = '''def print_flood_map(heights, water_level):
    """Print the map, keep heights unchanged, and return None."""
    for row in heights:
        for height in row:
            if height <= water_level:
                print("*", end="")
            else:
                print(".", end="")
        print()

heights = [[1, 3, 5, 2, 6],
           [4, 2, 0, 5, 3],
           [6, 5, 3, 1, 4],
           [2, 4, 6, 0, 5]]
print("Level 2:")
print_flood_map(heights, 2)
print("Level 4:")
print_flood_map(heights, 4)
'''
SRC['practice_6_starter'] = '''def neighbor_average(table, row, col):
    pass
'''
SRC['practice_6'] = '''def neighbor_average(table, row, col):
    """Return the neighbor average and keep table unchanged."""
    total = 0
    count = 0
    for r in range(row - 1, row + 2):
        for c in range(col - 1, col + 2):
            if 0 <= r < len(table) and 0 <= c < len(table[r]):
                if r != row or c != col:
                    total = total + table[r][c]
                    count = count + 1
    if count == 0:
        return 0.0
    return total / count

table = [[2, 4, 8, 10], [6, 12, 14, 16], [18, 20, 22, 24]]
print(f"{neighbor_average(table, 0, 0):.2f}")
print(f"{neighbor_average(table, 0, 2):.2f}")
print(f"{neighbor_average(table, 1, 1):.2f}")
'''
SRC['boss_1_starter'] = '''def word_list_text(words):
    pass

words = []
'''
SRC['boss_1'] = '''def word_list_text(words):
    """Return one string and keep words unchanged."""
    if len(words) == 0:
        return ""
    if len(words) == 1:
        return words[0]
    text = ""
    for word in words[:-1]:
        if text != "":
            text = text + ", "
        text = text + word
    return text + " and " + words[-1]

words = []
word = input()
while word != "":
    words.append(word)
    word = input()
print("Words:", word_list_text(words))
'''
SRC['boss_2_starter'] = '''def trimmed_copy(values, n):
    pass

values = []
'''
SRC['boss_2'] = '''def trimmed_copy(values, n):
    """Return a sorted trimmed copy and keep values unchanged."""
    ordered = sorted(values)
    return ordered[n:len(values) - n]

values = []
line = input()
while line != "":
    values.append(int(line))
    line = input()
if len(values) < 4:
    print("Need at least four values")
else:
    print("Original:", values)
    print("Trimmed:", trimmed_copy(values, 2))
'''
SRC['boss_3_starter'] = '''def table_with_row(row, table=None):
    pass

# Read dimensions and scores, then print the required results.
'''
SRC['boss_3_1'] = '''def table_with_row(row, table=None):
    """Return independent row copies and keep inputs unchanged."""
    result = []
    if table is not None:
        for old_row in table:
            result.append(old_row[:])
    result.append(row[:])
    return result
'''
SRC['boss_3_2'] = '''students = int(input())
tests = int(input())
table = []
for r in range(students):
    row = []
    for c in range(tests):
        row.append(int(input()))
    table = table_with_row(row, table)
print("Scores:", table)
for r in range(students):
    print(f"Row {r + 1} total: {sum(table[r])}")
for c in range(tests):
    total = 0
    for row in table:
        total = total + row[c]
    print(f"Column {c + 1} average: {total / students:.2f}")
table[0][0] = 100
print("After change:", table)
first = table_with_row([7])
second = table_with_row([9])
first[0][0] = 0
print("Default tables:", first, second)
'''
SRC['boss_4_starter'] = '''import random
random.seed(26)

def create_deck():
    pass

def shuffle_deck(deck):
    pass

def deal(deck, players, cards):
    pass
'''
SRC['boss_4_1'] = '''import random
random.seed(26)

def create_deck():
    """Return a new list of 52 card codes."""
    deck = []
    for suit in "CDHS":
        for rank in "23456789TJQKA":
            deck.append(rank + suit)
    return deck

def shuffle_deck(deck):
    """Shuffle deck in place and return None."""
    for i in range(len(deck) - 1, 0, -1):
        j = random.randint(0, i)
        deck[i], deck[j] = deck[j], deck[i]

def deal(deck, players, cards):
    """Remove cards from deck and return independent hands."""
    hands = [[] for player in range(players)]
    for turn in range(cards):
        for player in range(players):
            hands[player].append(deck.pop(0))
    return hands
'''
SRC['boss_4_2'] = '''players = int(input())
cards = int(input())
deck = create_deck()
if players * cards > len(deck):
    print("Not enough cards")
else:
    shuffle_deck(deck)
    hands = deal(deck, players, cards)
    for player in range(players):
        print(f"Hand {player + 1}:", hands[player])
    print("Remaining:", len(deck))
'''

E = {}

def ex(name, key, output=True):
    E[name] = example(SRC[key], output)
    return E[name]

# ============================================================ 1. Shared list parameters and local assignment
assert ex("ex-clear", "slide_2")["output"] == "[6, 0, 4]\nNone"
assert ex("ex-reset", "slide_3")["output"] == "[6, -2, 4]"

# ============================================================ 2. New lists and function styles
assert ex("ex-copy", "slide_4")["output"] == "[6, -2, 4]\n[6, 0, 4]"
assert ex("ex-fix", "slide_5")["output"] == "[6, 0, 4]\n[6, 0, 4]"

# ============================================================ 3. A list default persists
assert ex("ex-default", "slide_6")["output"] == "['a']\n['a', 'b']\n['a', 'b', 'c']"

# ============================================================ 4. A safe default with None
assert ex("ex-none", "slide_7")["output"] == "['a']\n['b']\n['c']"

# Checkpoint 1
cp1 = SRC["slide_9_1"] + SRC["slide_9_2"]
assert out(cp1) == "[70] [80]\n[50] [50, 90]"
cp1_ns = namespace(cp1)
E["cp1"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": SRC["checkpoint_1_starter"],
    "cases": [case("two default calls, then source = [50]", cp1)],
    "check": AST + '''_fn("with_mark", "mark", "marks")
assert with_mark.__defaults__ == (None,), "Give marks the default value None, as in def with_mark(mark, marks=None):."
''' + returns("with_mark", cp1_ns, (70,), (5, [1, 2]), (9, []), (4, [4, 4])) + '''_keeps("with_mark", ([1, 2], 5))
_one = with_mark(1)
_two = with_mark(2)
assert _two == [2], "Two calls without a list returned " + repr(_one) + " and " + repr(_two) + ". Each call that omits marks must start with a new empty list."
_given = [3]
_result = with_mark(6, _given)
assert _result is not _given, "with_mark(6, source) returned the input list itself. Copy the input list before you append."
''',
    "answer": b64(cp1),
    "answerNote": "Every call creates a result list. The third call copies source before it appends 90."}
# _keeps passes the list first, so check the argument order explicitly.
E["cp1"]["check"] = E["cp1"]["check"].replace('_keeps("with_mark", ([1, 2], 5))', '''_src = [1, 2]
with_mark(5, _src)
assert _src == [1, 2], "with_mark(5, [1, 2]) changed its input list to " + repr(_src) + ". Keep the input unchanged."''')
E["cp1-predict"] = {"type": "table", "xp": 1, "blanks": {
    "first": lst("[70]", width="9rem"), "second": lst("[80]", width="9rem"),
    "third": lst("[50, 90]", width="9rem"), "source": lst("[50]", width="9rem")}}

# ============================================================ 5. Work out an algorithm with cards
assert ex("ex-halves", "slide_11")["output"] == "[8, 10, 12, 2, 4, 6]"

# ============================================================ 6. A table is a list of rows
assert ex("ex-table", "slide_12")["output"] == "2\n3"

# ============================================================ 7. Row first, then column
assert ex("ex-index", "slide_13")["output"] == "[1, 3, 5]\n5\n[2, 9, 6]"
assert ex("ex-square", "slide_14")["output"] == "3\n7"

# ============================================================ 8. Nested loops visit each cell
assert ex("ex-nested", "slide_15")["output"] == "2 4 6 \n1 3 5 "

# ============================================================ 9. Shared rows and independent rows
assert ex("ex-shared", "slide_16")["output"] == "[[0, 9, 0], [0, 9, 0]]"
assert ex("ex-independent", "slide_17_1")["output"] == "[[0, 9, 0], [0, 0, 0]]"
E["ex-independent-comp"] = example(SRC["slide_17_2"] + "grid[0][1] = 9\nprint(grid)\n")
assert E["ex-independent-comp"]["output"] == "[[0, 9, 0], [0, 0, 0]]"

# Checkpoint 2
cp2 = SRC["slide_19"]
assert out(cp2) == "[[0, 99, 2], [10, 11, 12]]"
cp2_ns = namespace(cp2)
E["cp2"] = {"type": "code", "xp": 5, "minLines": 11,
    "starter": SRC["checkpoint_2_starter"],
    "cases": [case("number_grid(2, 3), then grid[0][1] = 99", cp2)],
    "check": AST + '''_fn("number_grid", "rows", "cols")
_f = _body("number_grid")
assert len([n for n in _loops(_f) if _loops(ast.Module(body=n.body, type_ignores=[]))]) >= 1, "Build the table with nested loops: an outer loop for rows and an inner loop for columns."
''' + returns("number_grid", cp2_ns, (2, 3), (1, 1), (3, 2), (0, 4), (2, 0)) + '''_g = number_grid(3, 2)
_g[0][0] = -1
assert _g[1][0] == 10 and _g[2][0] == 20, "Changing number_grid(3, 2)[0][0] also changed another row: " + repr(_g) + ". Create a new row list for every row."
''',
    "answer": b64(cp2),
    "answerNote": "The inner loop builds one new row list. The outer loop appends it once."}
E["cp2-trace"] = {"type": "table", "xp": 1, "blanks": {
    f"v{i}": accept(v, width="4rem", placeholder="value") for i, v in enumerate(["0", "1", "2", "10", "11", "12"], 1)}}

# ============================================================ 10. Copy each numeric row
assert ex("ex-outer", "slide_20_1")["output"] == "[[9, 4], [1, 3]]"
assert ex("ex-rowcopy", "slide_20_2")["output"] == "[[2, 4], [1, 3]]\n[[9, 4], [1, 3]]"

# ============================================================ 11. Row totals
assert ex("ex-rowtotals", "slide_21")["output"] == "[12, 9]"

# ============================================================ 12. A column total
assert ex("ex-coltotal", "slide_22")["output"] == "7"

# ============================================================ 13. All cells and changes in place
assert ex("ex-alltotal", "slide_23")["output"] == "21"
assert ex("ex-clearcells", "slide_24")["output"] == "[[0, 4, 0], [3, 0, 6]]"

# Checkpoint 3
cp3 = SRC["checkpoint_3_starter"].replace("def clean_table(table):\n    pass\ntable = [[-2, 4, -1], [3, -5, 6]]\n", "") + SRC["slide_26"]
assert out(cp3) == "[[0, 4, 0], [3, 0, 6]]\n[4, 9]\n4\n[[-2, 4, -1], [3, -5, 6]]"
cp3_ns = namespace(cp3)
CP3_CALLS = (([[-2, 4, -1], [3, -5, 6]],), ([],), ([[1, 2], [3, 4]],), ([[-7]],), ([[0, -1, 5]],))
E["cp3"] = {"type": "code", "xp": 5, "minLines": 26,
    "starter": SRC["checkpoint_3_starter"],
    "cases": [case("table = [[-2, 4, -1], [3, -5, 6]]", cp3)],
    "check": AST + '''_fn("clean_table", "table")
_fn("row_totals", "table")
_fn("column_total", "table", "col")
assert _func_calls("row_totals") and _func_calls("column_total"), "Use row_totals and column_total to print the totals of the clean table."
''' + returns("clean_table", cp3_ns, *CP3_CALLS) + '''_keeps("clean_table", ([[-2, 4, -1], [3, -5, 6]],))
_t = [[1, 2], [3, 4]]
_r = clean_table(_t)
assert all(a is not b for a, b in zip(_r, _t)), "clean_table([[1, 2], [3, 4]]) returned a row of the input table. Build a new list for every result row."
''',
    "answer": b64(cp3),
    "answerNote": "Each result row is new. The original table keeps its negative cells."}
E["cp3-trace"] = {"type": "table", "xp": 1, "blanks": {
    f"n{i}": lst(v, width="8rem") for i, v in enumerate(["[0]", "[0, 4]", "[0, 4, 0]", "[3]", "[3, 0]", "[3, 0, 6]"], 1)}}

# ============================================================ Coding Practice
# 1. Repair a local assignment (R6.21)
assert out(SRC["practice_1_bug"]) == "[8, 8, 8, 8]"
E["ex-p1-bug"] = example(SRC["practice_1_bug"], output=False)
E["p1-print"] = {"type": "table", "xp": 1, "blanks": {"p": lst("[8, 8, 8, 8]", width="11rem")}}
E["p1-why"] = short("The assignment `values = result` changes only the parameter's reference. "
                    "The caller's name still refers to the original list, so its elements stay 8.",
                    min_chars=20, placeholder="Why the caller's list keeps its elements…")
p1 = SRC["practice_1"]
assert out(p1) == "[0, 1, 4, 9]\n[8, 8, 8, 8]\nNone\n[0, 1, 4, 9]\n[]\nNone"
p1_ns = namespace(p1)
E["p1"] = {"type": "code", "xp": 5, "minLines": 18,
    "starter": SRC["practice_1_starter"],
    "cases": [case("[8, 8, 8, 8] and []", p1)],
    "check": AST + '''_fn("fill_squares", "values")
_fn("index_squares", "values")
def _fill(given, want):
    values = list(given)
    result, printed = _call("fill_squares", values)
    assert result is None, "fill_squares(" + repr(given) + ") should change the list and return None, not " + repr(result) + "."
    assert values == want, "After fill_squares(" + repr(given) + "), the list should be " + repr(want) + ", not " + repr(values) + "."
_fill([8, 8, 8, 8], [0, 1, 4, 9])
_fill([], [])
_fill([5], [0])
''' + returns("index_squares", p1_ns, ([8, 8, 8, 8],), ([],), ([3, 3],)) + '''_keeps("index_squares", ([8, 8, 8, 8],))
''',
    "answer": b64(p1),
    "answerNote": "fill_squares assigns to elements of the shared list. index_squares builds and returns a separate list."}

# 2. Choose a function style (R6.12)
E["p2-headers"] = short(
    "`def sort_decreasing(values):` Sort values in place and return None.\n\n"
    "`def remove_below(values, limit):` Remove values below limit in place and return None.\n\n"
    "`def below_limit_copy(values, limit):` Return a new list of values below limit and keep the input unchanged.\n\n"
    "`def squared_copy(values):` Return a new list of squared values and keep the input unchanged.",
    min_chars=60, rows=6, placeholder="Four headers, each with a one-line description…")
p2 = SRC["practice_2"]
assert out(p2) == "[2, 2]\n[7, 2, 9, 2]\nNone\n[9, 7, 2, 2]\n[]\nNone\n[]"
p2_ns = namespace(p2)
E["p2"] = {"type": "code", "xp": 5, "minLines": 16,
    "starter": "def sort_decreasing(values):\n    pass\n\ndef below_limit_copy(values, limit):\n    pass\n",
    "cases": [case("[7, 2, 9, 2] and []", p2)],
    "check": AST + '''_fn("sort_decreasing", "values")
_fn("below_limit_copy", "values", "limit")
def _sorts(given, want):
    values = list(given)
    result, printed = _call("sort_decreasing", values)
    assert result is None, "sort_decreasing(" + repr(given) + ") should change the list and return None, not " + repr(result) + "."
    assert values == want, "After sort_decreasing(" + repr(given) + "), the list should be " + repr(want) + ", not " + repr(values) + "."
_sorts([7, 2, 9, 2], [9, 7, 2, 2])
_sorts([], [])
_sorts([1, 5, 3], [5, 3, 1])
''' + returns("below_limit_copy", p2_ns, ([7, 2, 9, 2], 7), ([], 7), ([1, 8, 3, 8], 8), ([9, 10], 5)) + '''_src = [7, 2, 9, 2]
below_limit_copy(_src, 7)
assert _src == [7, 2, 9, 2], "below_limit_copy([7, 2, 9, 2], 7) changed its input list to " + repr(_src) + ". Keep the input unchanged."
''',
    "answer": b64(p2),
    "answerNote": "The verb name changes the list and returns None. The noun name returns a new list."}

# 3. Alternate two lists (P6.30)
p3 = SRC["practice_3"]
assert out(p3) == "[3, 6, 8, 1, 5, 9]\n[3, 8]\n[6, 1, 5, 9]\n[4, 7]\n[4, 7]\n[]"
p3_ns = namespace(p3)
E["p3"] = {"type": "code", "xp": 5, "minLines": 18,
    "starter": SRC["practice_3_starter"],
    "cases": [case("[3, 8] with [6, 1, 5, 9], then the empty inputs", p3)],
    "check": AST + '''_fn("alternating_copy", "first", "second")
''' + returns("alternating_copy", p3_ns, ([3, 8], [6, 1, 5, 9]), ([], [4, 7]), ([4, 7], []), ([], []), ([1, 2, 3, 4], [9]), ([5], [6])) + '''_a = [3, 8]
_b = [6, 1, 5, 9]
alternating_copy(_a, _b)
assert _a == [3, 8] and _b == [6, 1, 5, 9], "alternating_copy([3, 8], [6, 1, 5, 9]) changed an input list. Keep both inputs unchanged."
''',
    "answer": b64(p3),
    "answerNote": "Each index can supply an element from either input. The length checks prevent access beyond an input."}

# 4. Build table patterns (R6.28)
p4 = SRC["practice_4"]
assert out(p4) == "Checkerboard:\n0 1 0 1 0 \n1 0 1 0 1 \n0 1 0 1 0 \nBorder:\n1 1 1 1 1 \n1 0 0 0 1 \n1 1 1 1 1 \nBorder total: 12"
P4_ROW = [("m = 3", "m = 1")]
P4_COL = [("n = 5", "n = 1")]
P4_SQ = [("m = 3", "m = 4"), ("n = 5", "n = 4")]
assert out(rewritten(p4, P4_ROW)).endswith("Border total: 5")
assert out(rewritten(p4, P4_SQ)).endswith("Border total: 12")
E["p4"] = {"type": "code", "xp": 5, "minLines": 24,
    "starter": SRC["practice_4_starter"],
    "cases": [case("m = 3, n = 5", p4), case("m = 1, n = 5", p4, P4_ROW), case("m = 3, n = 1", p4, P4_COL), case("m = 4, n = 4", p4, P4_SQ)],
    "check": AST + '''assert len(_loops()) >= 4, "Use nested loops to fill each table and to print its rows."
''',
    "answer": b64(p4),
    "answerNote": "Each construction evaluates a new row list for every row."}

# 5. Print a flood map (P6.35)
p5 = SRC["practice_5"]
assert out(p5) == "Level 2:\n*..*.\n.**..\n...*.\n*..*.\nLevel 4:\n**.*.\n***.*\n..***\n**.*."
E["p5"] = {"type": "code", "xp": 5, "minLines": 18,
    "starter": SRC["practice_5_starter"] + "\nheights = [[1, 3, 5, 2, 6],\n           [4, 2, 0, 5, 3],\n           [6, 5, 3, 1, 4],\n           [2, 4, 6, 0, 5]]\n",
    "cases": [case("levels 2 and 4", p5)],
    "check": AST + '''_fn("print_flood_map", "heights", "water_level")
_h = [[1, 3], [0, 5]]
_value, _printed = _call("print_flood_map", _h, -1)
assert _value is None, "print_flood_map should print the map and return None, not " + repr(_value) + "."
assert _printed == "..\\n..\\n", "print_flood_map([[1, 3], [0, 5]], -1) should print two rows of dots, not " + repr(_printed) + "."
_value, _printed = _call("print_flood_map", _h, 9)
assert _printed == "**\\n**\\n", "print_flood_map([[1, 3], [0, 5]], 9) should print two rows of stars, not " + repr(_printed) + "."
assert _h == [[1, 3], [0, 5]], "print_flood_map changed the height table. Keep it unchanged."
''',
    "answer": b64(p5),
    "answerNote": "Equality with the level counts as flooded. The final print call ends each row."}

# 6. Average nearby cells (P6.23)
p6 = SRC["practice_6"]
assert out(p6) == "7.33\n11.20\n11.75"
p6_ns = namespace(p6)
P6_T = [[2, 4, 8, 10], [6, 12, 14, 16], [18, 20, 22, 24]]
E["p6"] = {"type": "code", "xp": 5, "minLines": 18,
    "starter": SRC["practice_6_starter"] + "\ntable = [[2, 4, 8, 10], [6, 12, 14, 16], [18, 20, 22, 24]]\n",
    "cases": [case("[0][0], [0][2] and [1][1]", p6)],
    "check": AST + '''_fn("neighbor_average", "table", "row", "col")
''' + returns("neighbor_average", p6_ns, (P6_T, 0, 0), (P6_T, 0, 2), (P6_T, 1, 1), (P6_T, 2, 3), ([[1, 5, 9]], 0, 1), ([[4], [6], [8]], 2, 0), ([[7]], 0, 0)) + '''_keeps("neighbor_average", (''' + repr(P6_T) + ''', 1, 1))
''',
    "answer": b64(p6),
    "answerNote": "Check both bounds before accessing a cell. A negative Python index would otherwise select a cell from the opposite edge."}
assert namespace(p6)["neighbor_average"]([[7]], 0, 0) == 0.0

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

def gap(key, fills, want, width="7rem"):
    """Every accepted answer for gap (a) must make the program print the stated output."""
    for fill in fills:
        assert out(SRC[key].replace("____(a)____", fill)) == want, (key, fill)
    return {"type": "table", "xp": 1, "blanks": {"a": accept(*fills, width=width, placeholder="code", show=fills[0])}}

def mcq(setup, options, letter, goal):
    """Exactly one option meets the goal, and it is the keyed letter."""
    good = []
    for option in options:
        p = subprocess.run([sys.executable, "-c", setup + "\nresult = " + option + "\nprint(bool(" + goal + "))"], capture_output=True, text=True)
        good.append(p.stdout.strip() == "True")
    assert good.count(True) == 1 and "ABCD"[good.index(True)] == letter, (options, good)
    return choice(letter)

E["q1"] = predict(SRC["quick_1"])
E["q2"] = gap("quick_2", ["0", "-2"], "[0, 3]", "5rem")
E["q3"] = mcq(SRC["quick_3"], ["values[:]", "double_values(values)", "doubled_copy(values)", "values.reverse()"], "C",
              "result == [6, 10] and values == [3, 5]")
E["q4"] = true_false(True, False)
E["q5"] = predict(SRC["quick_5"])
E["q6"] = gap("quick_6", ["[]", "list()"], "[3] [8]", "6rem")
E["q7"] = choice("B")
for fixture, want in (([], False), (None, True), ([4], False)):
    assert out(f"items = {fixture!r}\nprint(items is None)") == str(want)
E["q8"] = true_false(False, True)
E["q9"] = predict(SRC["quick_9"])
E["q10"] = gap("quick_10", ["half", "3", "len(values) // 2", "len(values)//2"], "3", "10rem")
E["q11"] = mcq(SRC["quick_11"], ["len(table[0])", "len(table[1])", "len(table[0][0:1])", "len(table)"], "D", "result == 3")
E["q12"] = true_false(True, False)
assert "IndexError" in run("table = []\nprint(len(table[0]))", ok=False)[1]
E["q13"] = predict(SRC["quick_13"])
E["q14"] = gap("quick_14", ["2", "-1"], "13", "5rem")
E["q15"] = choice("A")
assert out(SRC["quick_15"].replace("    # Replace this comment.", "    print()")) == "7 8 \n9 1 "
E["q16"] = true_false(False, True)
E["q17"] = predict(SRC["quick_17"])
E["q18"] = gap("quick_18", ["range(3)", "range(0, 3)"], "[[0, 6], [0, 0], [0, 0]]", "8rem")
E["q19"] = choice("C")
assert out("table = [[8, 6], [4, 2]]\ncopy = [row[:] for row in table]\ncopy[0][0] = 1\nprint(table)") == "[[8, 6], [4, 2]]"
assert out("table = [[8, 6], [4, 2]]\ncopy = [row for row in table]\ncopy[0][0] = 1\nprint(table)") == "[[1, 6], [4, 2]]"
E["q20"] = true_false(True, False)
E["q21"] = predict(SRC["quick_21"])
E["q22"] = gap("quick_22", ["sum(row)"], "[7, 13]", "8rem")
E["q23"] = mcq(SRC["quick_23"], ["sum(table[0])", "table[0][1] + table[1][1]", "sum(table[1])", "table[0][2] + table[1][2]"], "D", "result == 13")
E["q24"] = true_false(False, True)
E["q25"] = predict(SRC["quick_25"])
E["q26"] = gap("quick_26", ["row[-1]", "row[1]", "row[len(row) - 1]", "row[len(row)-1]"], "[[3, 8], [5, 8]]", "9rem")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-26",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 26 Workbook",
    "subtitle": "Lists with functions and tables",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-26/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
