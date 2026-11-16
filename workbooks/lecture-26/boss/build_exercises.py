"""Build workbooks/lecture-26/boss/exercises.json: the Lecture 26 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_26_SHARED_CONTENT.tex, in its order. The listings below are copied
from it. Expected outputs are produced by actually running the model
solutions. Run from anywhere:

    python3 workbooks/lecture-26/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-26/boss
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
    ns = {"__name__": "lecture26boss"}
    answers = list(inputs)
    ns["input"] = lambda prompt="": answers.pop(0)
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    del ns["input"]
    return ns

E = {}

# ---------------------------------------------------------------- 1 Format a shop list (Stephenson 113)
fmt = SRC["boss_1"]
fmt_ns = namespace(fmt, [""])
E["shop-list"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 16,
    "starter": SRC["boss_1_starter"],
    "cases": input_cases(fmt,
        ("Example 1: typed tea, rice, salt, blank", ["tea", "rice", "salt", ""]),
        ("Example 2: typed blank", [""]),
        ("Example 3: typed bread, blank", ["bread", ""]),
        ("Example 4: typed tea, rice, blank", ["tea", "rice", ""]),
        ("Typed milk, eggs, flour, sugar, blank", ["milk", "eggs", "flour", "sugar", ""]),
        ("Typed a, b, c, d, e, blank", ["a", "b", "c", "d", "e", ""])),
    "check": AST + '''_fn("word_list_text", "words")
_f = _body("word_list_text")
assert not _calls("join"), "Build the string in a loop. Do not use join."
assert _loops(_f) and _slices(_f), "In word_list_text, loop over a slice that holds all but the last word, such as words[:-1]."
''' + returns("word_list_text", fmt_ns, ([],), (["tea"],), (["tea", "rice"],), (["a", "b", "c", "d"],)) + '''_keeps("word_list_text", (["tea", "rice", "salt"],))
''',
    "hints": [
        "Handle the short lists first: return `\"\"` for no words and `words[0]` for one word.",
        "For two or more words, start with `text = \"\"` and loop over `words[:-1]`. Put `\", \"` before every word except the first one in the loop.",
        "After the loop, return `text + \" and \" + words[-1]`. For two words the loop adds only the first word, so no comma appears.",
    ],
    "answer": b64(fmt),
    "answerNote": "The slice leaves the last word for the final \"and\". The input list stays unchanged."}
assert E["shop-list"]["cases"][0]["expected"] == "Words: tea, rice and salt"
assert E["shop-list"]["cases"][1]["expected"].rstrip() == "Words:"
assert E["shop-list"]["cases"][3]["expected"] == "Words: tea and rice"

# ---------------------------------------------------------------- 2 Trim extreme readings (Stephenson 106)
trim = SRC["boss_2"]
trim_ns = namespace(trim, [""])
E["trim"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 14,
    "starter": SRC["boss_2_starter"],
    "cases": input_cases(trim,
        ("Example 1: typed 14, 2, 8, 5, 11, 17, blank", ["14", "2", "8", "5", "11", "17", ""]),
        ("Example 2: typed 7, 1, 9, 4, blank", ["7", "1", "9", "4", ""]),
        ("Example 3: typed blank", [""]),
        ("Typed 5, 5, 5, blank", ["5", "5", "5", ""]),
        ("Typed 3, -1, 3, 8, 3, -1, 1000, blank", ["3", "-1", "3", "8", "3", "-1", "1000", ""]),
        ("Typed 6, 2, 9, 4, 1, blank", ["6", "2", "9", "4", "1", ""])),
    "check": AST + '''_fn("trimmed_copy", "values", "n")
_f = _body("trimmed_copy")
assert _func_calls("sorted", _f) and _slices(_f), "In trimmed_copy, make a sorted copy with sorted, then take the middle with the slice [n:len(values) - n]."
assert not _calls("sort", _f), "Use sorted, which keeps the input list unchanged. Do not call sort on the input."
''' + returns("trimmed_copy", trim_ns, ([4, 1, 3, 2], 0), ([4, 1, 3, 2], 1), ([4, 1, 3, 2], 2), ([9, 9, 1, 1, 5], 1), ([], 0), ([7, -3, 2, 7, 0, 5], 2)) + '''_keeps("trimmed_copy", ([14, 2, 8, 5, 11, 17], 2))
''',
    "hints": [
        "Read lines until a blank line and append `int(line)` for each value. Check `len(values) < 4` before you print anything else.",
        "In `trimmed_copy`, make `ordered = sorted(values)`. This copy is sorted and the input keeps its order.",
        "Return `ordered[n:len(values) - n]`. With `n = 0` this slice is the whole sorted copy. The slice `[n:-n]` would be empty there.",
    ],
    "answer": b64(trim),
    "answerNote": "sorted makes the copy. The end index len(values) - n keeps the whole copy when n is 0."}
assert E["trim"]["cases"][0]["expected"] == "Original: [14, 2, 8, 5, 11, 17]\nTrimmed: [8, 11]"
assert E["trim"]["cases"][2]["expected"] == "Need at least four values"

# ---------------------------------------------------------------- 3 Report a scores table (original, awaiting approval)
scores = SRC["boss_3_1"] + "\n" + SRC["boss_3_2"]
scores_ns = namespace(scores, ["1", "1", "8"])
E["scores"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 28,
    "starter": SRC["boss_3_starter"],
    "cases": input_cases(scores,
        ("Example 1: 2 students, 3 tests", ["2", "3", "10", "20", "30", "40", "50", "60"]),
        ("Example 2: 1 student, 1 test", ["1", "1", "8"]),
        ("3 students, 2 tests", ["3", "2", "90", "70", "55", "100", "0", "81"]),
        ("2 students, 1 test", ["2", "1", "33", "66"]),
        ("1 student, 4 tests", ["1", "4", "5", "0", "100", "45"])),
    "check": AST + '''_fn("table_with_row", "row", "table")
assert table_with_row.__defaults__ == (None,), "Give the table parameter the default None, as in def table_with_row(row, table=None):."
''' + returns("table_with_row", scores_ns, ([7],), ([3, 4], [[1, 2]]), ([5], [[1], [2], [3]]), ([], None)) + '''_old = [[1, 2], [5, 6]]
_row = [3, 4]
_new = table_with_row(_row, _old)
assert _old == [[1, 2], [5, 6]] and _row == [3, 4], "table_with_row([3, 4], [[1, 2], [5, 6]]) changed an input. Keep both inputs unchanged."
assert all(a is not b for a, b in zip(_new, _old)) and _new[-1] is not _row, "table_with_row returned a row that is also in an input. Copy every row, such as old_row[:] and row[:]."
_one = table_with_row([7])
_two = table_with_row([9])
assert _two == [[9]], "Two calls without a table returned " + repr(_one) + " and " + repr(_two) + ". Each call that omits the table must start a new table."
assert _func_calls("table_with_row") and _loops(), "Read the scores with loops and build the table with table_with_row."
''',
    "hints": [
        "In `table_with_row`, start with `result = []`. If `table is not None`, append a copy of each old row, such as `old_row[:]`. Then append `row[:]` and return `result`.",
        "Read the two dimensions. For each student, build a row with an inner loop of `int(input())` calls, then use `table = table_with_row(row, table)`.",
        "Print each row total with `sum(table[r])`. For column `c`, start `total = 0` and add `row[c]` from every row. Print `total / students` with `:.2f`.",
        "After the averages, set `table[0][0] = 100` and print the table. Then call `table_with_row([7])` and `table_with_row([9])`, set the first result's `[0][0]` to `0`, and print both after `Default tables:`.",
    ],
    "answer": b64(scores),
    "answerNote": "Every returned table holds new row lists, so a change to one row leaves the others unchanged. The None default gives each call without a table its own new table."}
assert E["scores"]["cases"][0]["expected"].endswith("After change: [[100, 20, 30], [40, 50, 60]]\nDefault tables: [[0]] [[9]]")

# ---------------------------------------------------------------- 4 Deal reproducible card hands (Stephenson 119 and 118)
cards = SRC["boss_4_1"] + "\n" + SRC["boss_4_2"]
cards_ns = namespace(cards, ["2", "0"])
E["cards"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 32,
    "starter": SRC["boss_4_starter"],
    "cases": input_cases(cards,
        ("Example 1: 3 players, 2 cards", ["3", "2"]),
        ("Example 2: 2 players, 0 cards", ["2", "0"]),
        ("Example 3: 5 players, 11 cards", ["5", "11"]),
        ("1 player, 5 cards", ["1", "5"]),
        ("4 players, 13 cards", ["4", "13"]),
        ("13 players, 4 cards", ["13", "4"])),
    "check": AST + '''_fn("create_deck")
_fn("shuffle_deck", "deck")
_fn("deal", "deck", "players", "cards")
_d = create_deck()
assert len(_d) == 52 and _d[:3] == ["2C", "3C", "4C"] and _d[-1] == "AS", "create_deck() should return the 52 codes in suit order CDHS and rank order 23456789TJQKA, starting ['2C', '3C', '4C'] and ending 'AS'."
assert create_deck() is not create_deck(), "create_deck() should return a new list on each call."
_s = create_deck()
_value, _printed = _call("shuffle_deck", _s)
assert _value is None and sorted(_s) == sorted(create_deck()), "shuffle_deck should change the deck in place, keep all 52 cards, and return None."
assert _func_calls("randint", _body("shuffle_deck")) or _calls("randint", _body("shuffle_deck")), "In shuffle_deck, choose each j with random.randint(0, i)."
assert not _calls("shuffle"), "Write the shuffle loop yourself. Do not call random.shuffle."
_deck = ["a", "b", "c", "d", "e", "f", "g"]
_hands = deal(_deck, 2, 3)
assert _hands == [["a", "c", "e"], ["b", "d", "f"]], "deal(['a', 'b', 'c', 'd', 'e', 'f', 'g'], 2, 3) should deal in rounds and return [['a', 'c', 'e'], ['b', 'd', 'f']], not " + repr(_hands) + "."
assert _deck == ["g"], "After deal(['a', 'b', 'c', 'd', 'e', 'f', 'g'], 2, 3), the deck should be ['g'], not " + repr(_deck) + ". Remove each dealt card with pop(0)."
_hands = deal(["x", "y"], 3, 0)
_hands[0].append("z")
assert _hands[1] == [], "deal returned hands that share one list. Build the hands with a comprehension of fresh empty lists."
assert _calls("pop", _body("deal")) and _comps(_body("deal")), "In deal, build the hands with a comprehension and take each card with pop(0)."
''',
    "hints": [
        "In `create_deck`, loop over the suits `\"CDHS\"` in the outer loop and the ranks `\"23456789TJQKA\"` in the inner loop. Append `rank + suit`.",
        "In `shuffle_deck`, use `for i in range(len(deck) - 1, 0, -1):`. Choose `j = random.randint(0, i)` and swap `deck[i]` and `deck[j]`. Keep `random.seed(26)` at the top.",
        "In `deal`, make `hands = [[] for player in range(players)]`. The outer loop counts rounds and the inner loop visits players: `hands[player].append(deck.pop(0))`.",
        "In the main program, check `players * cards > len(deck)` before you shuffle. Otherwise shuffle, deal, print each hand with its number, then print `Remaining:` and `len(deck)`.",
    ],
    "answer": b64(cards),
    "answerNote": "The fixed seed and the fixed shuffle loop give the same deck every run. deal removes cards with pop(0), so the deck shrinks as the hands grow."}
assert E["cards"]["cases"][0]["expected"] == "Hand 1: ['KH', 'QS']\nHand 2: ['JS', '5D']\nHand 3: ['4S', 'AD']\nRemaining: 46"
assert E["cards"]["cases"][2]["expected"] == "Not enough cards"

for spec in E.values():
    spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-26-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 26 Boss Problems",
    "short": "L26 bosses",
    "subtitle": "Lists with functions and tables",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-26/boss/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
for key, spec in E.items():
    for c in spec["cases"]:
        print(key, "|", c["name"], "|", c["expected"].replace("\n", " / "))
