"""Build workbooks/lecture-24/boss/exercises.json: the Lecture 24 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_24_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Boss 4 also has the workbook's
written question, placed after its code box. Run from anywhere:

    python3 workbooks/lecture-24/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-24/boss
"""
import base64, json, subprocess, sys, pathlib

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

def short(answer, xp=2, min_chars=30, rows=4, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

# A check runs after the student's program in a copy of its namespace.
# `_calls(method)` lists method calls such as .append(...). `_func_calls`
# lists calls of a plain function name. `_slices()` lists slice nodes.
# `_index_set()` is true when the file assigns to an element, as in
# values[i] = 0. `_count_down()` is true for a range(...) call with a
# negative step. `_no_defs()` asks for a script with no def.
AST = '''import ast
_TREE = ast.parse(__source__)
def _calls(method):
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == method]
def _func_calls(name):
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name]
def _slices():
    return [n for n in ast.walk(_TREE) if isinstance(n, ast.Slice)]
def _index_set():
    for n in ast.walk(_TREE):
        targets = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AugAssign) else []
        for t in targets:
            if isinstance(t, ast.Subscript) and not isinstance(t.slice, ast.Slice):
                return True
    return False
def _negative(node):
    return (isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)) or (isinstance(node, ast.Constant) and isinstance(node.value, int) and node.value < 0)
def _count_down():
    return any(len(c.args) == 3 and _negative(c.args[2]) for c in _func_calls("range"))
def _no_defs():
    assert not any(isinstance(n, ast.FunctionDef) for n in ast.walk(_TREE)), "Write a script. Do not define functions with def."
def _no_dict_set():
    for _n in ast.walk(_TREE):
        assert not isinstance(_n, (ast.Dict, ast.DictComp, ast.Set, ast.SetComp)), "Use one list. Do not use dictionaries or sets."
        assert not (isinstance(_n, ast.Call) and isinstance(_n.func, ast.Name) and _n.func.id in ("dict", "set")), "Use one list. Do not use dictionaries or sets."
'''

E = {}

# ---------------------------------------------------------------- 1 Latest reading first
latest = """readings = []
reading = int(input())
while reading != -999:
    readings.append(reading)
    reading = int(input())
print("Readings:")
if len(readings) == 0:
    print("No readings")
else:
    for i in range(len(readings) - 1, -1, -1):
        print(readings[i])
"""
E["latest"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 12,
    "starter": "readings = []\n# Read, store, and display the readings.\n",
    "cases": input_cases(latest,
        ("Example 1: typed 18, -4, 18, -999", ["18", "-4", "18", "-999"]),
        ("Example 2: typed -999", ["-999"]),
        ("Typed 5, -999", ["5", "-999"]),
        ("Typed 999, -998, 0, -999", ["999", "-998", "0", "-999"]),
        ("Typed 1 to 6, then -999", ["1", "2", "3", "4", "5", "6", "-999"]),
        ("Typed 7, 7, 7, -999", ["7", "7", "7", "-999"])),
    "check": AST + '''_no_defs()
assert _calls("append"), "Store the readings in one list with append."
assert not _calls("reverse") and not _func_calls("reversed"), "Display the readings with an index loop from the end. Do not use reverse or reversed."
assert not [n for n in _slices() if n.step is not None], "Do not use a slice with a step. Display the readings with an index loop from the end."
assert _count_down(), "Display the readings with an index loop from the end, such as range(len(readings) - 1, -1, -1)."
''',
    "hints": [
        "Read the first reading with `int(input())` before the loop. Repeat `while reading != -999`: append `reading` to `readings`, then read the next one at the end of the loop body.",
        "After the loop, print `\"Readings:\"`. If `len(readings) == 0`, print `\"No readings\"`.",
        "Otherwise loop over the indexes from the end: `for i in range(len(readings) - 1, -1, -1):` and print `readings[i]`. For three readings the indexes are 2, 1, and 0. The stop value -1 is not included.",
    ],
    "answer": b64(latest),
    "answerNote": "The loop starts at the last valid index. It stops after index 0."}
assert [c["expected"] for c in E["latest"]["cases"][:2]] == ["Readings:\n18\n-4\n18", "Readings:\nNo readings"]

# ---------------------------------------------------------------- 2 One entry per word
words = """words = []
word = input()
while word != "":
    if word not in words:
        words.append(word)
    word = input()
print("Words:")
if len(words) == 0:
    print("No words")
else:
    for word in words:
        print(word)
"""
E["words"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 12,
    "starter": "words = []\n# Read the words and print each kept word.\n",
    "cases": input_cases(words,
        ("Example 1: typed rice, tea, rice, salt, tea, blank", ["rice", "tea", "rice", "salt", "tea", ""]),
        ("Example 2: typed blank", [""]),
        ("Typed Tea, tea, blank", ["Tea", "tea", ""]),
        ("Typed bread, blank", ["bread", ""]),
        ("Typed x, y, x, z, y, x, blank", ["x", "y", "x", "z", "y", "x", ""]),
        ("Typed salt, salt, salt, blank", ["salt", "salt", "salt", ""])),
    "check": AST + '''_no_defs()
_no_dict_set()
assert _calls("append"), "Keep each new word with append."
assert any(isinstance(n, ast.Compare) and any(isinstance(o, (ast.In, ast.NotIn)) for o in n.ops) for n in ast.walk(_TREE)), "Test whether the word is already in the list with in or not in before append."
''',
    "hints": [
        "Read the first word with `input()` before the loop. Repeat `while word != \"\"`. Read the next word at the end of the loop body.",
        "Inside the loop, append the word only if it is new: `if word not in words:` then `words.append(word)`. For rice, tea, rice, the second rice is already in `words`.",
        "After the loop, print `\"Words:\"`. Then print `\"No words\"` for an empty list, or print each element of `words` on its own line.",
    ],
    "answer": b64(words),
    "answerNote": "The membership test checks only words already kept."}
assert [c["expected"] for c in E["words"]["cases"][:2]] == ["Words:\nrice\ntea\nsalt", "Words:\nNo words"]

# ---------------------------------------------------------------- 3 Manage a waiting list
waiting = """waiting = ["Mia", "Noor"]
starting = waiting.copy()
line = input()
while line != "":
    parts = line.split()
    command = parts[0]
    if command == "add":
        waiting.append(parts[1])
    elif command == "front":
        waiting.insert(0, parts[1])
    elif command == "serve":
        if len(waiting) > 0:
            print("Served:", waiting.pop(0))
        else:
            print("Empty list")
    elif command == "cancel":
        name = parts[1]
        if name in waiting:
            waiting.remove(name)
        else:
            print("Name absent")
    elif command == "drop":
        i = int(parts[1])
        if i < len(waiting):
            del waiting[i]
        else:
            print("Invalid index")
    elif command == "next":
        n = int(parts[1])
        print(waiting[:n])
    line = input()
print("Starting:", starting)
print("Final:", waiting)
"""
E["waiting"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 30,
    "starter": 'waiting = ["Mia", "Noor"]\n# Save the starting list, then process commands.\n',
    "cases": input_cases(waiting,
        ("Example 1", ["add Ivo", "front Uma", "serve", "cancel Noor", "drop 1", "next 3", ""]),
        ("Example 2: typed blank", [""]),
        ("Example 3", ["serve", "serve", "serve", "cancel Mia", "drop 0", "next 2", ""]),
        ("Repeated names: cancel removes the first match", ["add Mia", "add Noor", "cancel Mia", "next 5", ""]),
        ("drop with an index past the end", ["drop 2", "drop 1", "next 2", ""]),
        ("next 0 and front then serve", ["next 0", "front Ola", "front Ari", "serve", "next 9", ""]),
        ("cancel an absent name", ["cancel Zed", "add Zed", "cancel Zed", "serve", ""])),
    "check": AST + '''_no_defs()
for _method, _command in (("append", "add"), ("insert", "front"), ("pop", "serve"), ("remove", "cancel")):
    assert _calls(_method), "Use " + _method + " for the " + _command + " command."
assert any(isinstance(n, ast.Delete) for n in ast.walk(_TREE)), "Use del for the drop command, such as del waiting[i]."
assert _slices(), "Use a slice for the next command, such as waiting[:n]."
''',
    "hints": [
        "Save the copy first: `starting = waiting.copy()`. Then read lines with `input()` until a blank line. Split each line: `parts = line.split()` gives `[\"add\", \"Ivo\"]` for `add Ivo`, so `parts[0]` is the command.",
        "Use one branch per command. `add` calls `waiting.append(parts[1])`. `front` calls `waiting.insert(0, parts[1])`. `next` prints `waiting[:n]` with `n = int(parts[1])`.",
        "Test before each change. For `serve`, pop only if `len(waiting) > 0`. For `cancel`, remove only if the name is `in waiting`. For `drop`, delete only if `i < len(waiting)`. Otherwise print the error line.",
        "After the loop, print `\"Starting:\"` with `starting` and `\"Final:\"` with `waiting`. If you write `starting = waiting`, both lines show the final list.",
    ],
    "answer": b64(waiting),
    "answerNote": "The saved copy keeps its original elements. Using starting = waiting would make both names show the final list."}
assert [c["expected"] for c in E["waiting"]["cases"][:3]] == [
    "Served: Uma\n['Mia']\nStarting: ['Mia', 'Noor']\nFinal: ['Mia']",
    "Starting: ['Mia', 'Noor']\nFinal: ['Mia', 'Noor']",
    "Served: Mia\nServed: Noor\nEmpty list\nName absent\nInvalid index\n[]\nStarting: ['Mia', 'Noor']\nFinal: []"]

# ---------------------------------------------------------------- 4 Cross out composite numbers
sieve = """limit = int(input())
values = []
for number in range(limit + 1):
    values.append(number)
values[0] = 0
values[1] = 0
p = 2
while p * p <= limit:
    if values[p] != 0:
        for multiple in range(p * p, limit + 1, p):
            values[multiple] = 0
    p = p + 1
print("Primes:")
for number in range(2, limit + 1):
    if values[number] != 0:
        print(values[number])
"""
def primes(limit):
    return [n for n in range(2, limit + 1) if all(n % d for d in range(2, int(n ** 0.5) + 1))]
for limit in (2, 3, 18, 100, 1000, 10000):
    assert run(sieve, [str(limit)]) == "\n".join(["Primes:"] + [str(p) for p in primes(limit)])
E["sieve"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 16,
    "starter": "limit = int(input())\nvalues = []\n# Build the list, cross out composites, and print primes.\n",
    "cases": input_cases(sieve,
        ("Example 1: typed 18", ["18"]),
        ("Example 2: typed 2", ["2"]),
        ("Typed 3", ["3"]),
        ("Typed 10", ["10"]),
        ("Typed 49", ["49"]),
        ("Typed 100", ["100"]),
        ("Typed 10000", ["10000"])),
    "check": AST + '''_no_defs()
assert _calls("append"), "Build the list of numbers with append in a loop."
assert _index_set(), "Cross out a number by replacing its element with 0, such as values[multiple] = 0."
assert any(len(c.args) == 3 for c in _func_calls("range")), "Visit the multiples with range and a step, such as range(p * p, limit + 1, p)."
assert not _calls("remove") and not _calls("pop") and not any(isinstance(n, ast.Delete) for n in ast.walk(_TREE)), "Do not remove elements. Each index must keep its meaning, so replace the element with 0."
assert not any(isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod) for n in ast.walk(_TREE)), "Cross out multiples with range and a step. Do not test divisors with %."
''',
    "hints": [
        "Build the list with `for number in range(limit + 1):` and `values.append(number)`. Then `values[5]` is 5. Cross out 0 and 1 with `values[0] = 0` and `values[1] = 0`.",
        "Try each candidate `p` from 2 while `p * p <= limit`. If `values[p]` is not 0, `p` is prime and its multiples are composite.",
        "Cross out the multiples with `for multiple in range(p * p, limit + 1, p):` and `values[multiple] = 0`. For limit 18 and `p = 3`, this visits 9, 12, 15, and 18.",
        "Print `\"Primes:\"`, then loop over the indexes 2 to `limit` and print each element that is not 0.",
    ],
    "answer": b64(sieve),
    "answerNote": "Starting at p * p is safe because smaller multiples have a smaller prime factor. The list keeps each number at its own index, so a crossed-out number becomes 0 instead of being removed."}
assert E["sieve"]["cases"][1]["expected"] == "Primes:\n2"

E["sieve-why"] = short("The sieve crosses out many multiples during one pass for a candidate. "
                       "Later candidates skip numbers already crossed out. "
                       "Starting at p * p is safe because smaller multiples have a smaller prime factor. "
                       "The earlier divisor method tests each candidate number separately.",
                       placeholder="How the sieve avoids testing every divisor…")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-24-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 24 Boss Problems",
    "short": "L24 bosses",
    "subtitle": "Lists: properties and operations",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-24/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
