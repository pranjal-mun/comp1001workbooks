"""Build workbooks/lecture-16/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The seeded random programs are
deterministic: the same seed and the same calls give the same output in
CPython and in the browser. Run from anywhere:

    python3 workbooks/lecture-16/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-16
"""
import base64, json, subprocess, sys, pathlib, random

ROOT = pathlib.Path(__file__).resolve().parents[2]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=()):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""), capture_output=True, text=True)
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

def example(code, output=True, **kw):
    spec = {"type": "example", "code": code.rstrip("\n"), **kw}
    if output:
        spec["output"] = run(code)
    return spec

def case(name, inputs, code=None, check=None):
    """A grading case: `expected` from running the model answer with `inputs`."""
    c = {"name": name, "inputs": list(inputs)}
    if code is not None:
        c["expected"] = run_with_prompts(code, inputs)
    if check:
        c["check"] = check
    return c

def num(*values, width="4rem"):
    return {"accept": [str(v) for v in values], "placeholder": "value", "width": width}

def yes_no(value):
    return {"accept": ["yes", "y", "true"] if value else ["no", "n", "false"], "placeholder": "yes / no", "width": "6rem", "show": "yes" if value else "no"}

def seq(*values, width="9rem"):
    """A cell holding several values, such as `0, 1, 2`."""
    parts = [str(v) for v in values]
    forms = [", ".join(parts), ",".join(parts), " ".join(parts), "; ".join(parts), " and ".join(parts)]
    if len(parts) > 1:
        forms.append(", ".join(parts[:-1]) + " and " + parts[-1])
        forms.append(", ".join(parts[:-1]) + ", and " + parts[-1])
    return {"accept": forms, "placeholder": "values", "width": width, "show": forms[0]}

def words(show, *others, width="10rem", placeholder="pattern"):
    return {"accept": [show, *others], "placeholder": placeholder, "width": width, "show": show}

def call(show, *others, width="12rem"):
    forms = []
    for text in (show, *others):
        forms.append(text)
        forms.append(text.replace(", ", ","))
        if text.startswith("random."):
            forms.append(text[len("random."):])
            forms.append(text[len("random."):].replace(", ", ","))
    return {"accept": forms, "placeholder": "random....", "width": width, "show": show, "caseSensitive": True}

E = {}

# ============================================================ 1. Recognize the Algorithm Before Writing the Loop
COUNTER = words("counter", "a counter", "count", "counting matches", "counting-matches", "counter pattern")
BEST = words("running best", "a running best", "running maximum", "a running maximum", "maximum", "running max", "best", "extreme", "running extreme", "largest")
SEARCH = words("first-match search", "search", "a search", "first match search", "first match", "a first-match search", "search that records a position",
               "first-match search that records a position", "record a position", "first-match", "search for the first match", "position")
ACCUM = words("accumulator and count", "accumulator", "an accumulator", "accumulator with a count", "an accumulator with a count", "accumulator and counter",
              "accumulator with count", "sum and count", "accumulator, count", "total and count", "accumulator + count")
E["cp1"] = {"type": "table", "xp": 1, "blanks": {"digits": dict(COUNTER), "largest": dict(BEST), "space": dict(SEARCH), "average": dict(ACCUM)}}

# ============================================================ 2. Sum and Average
sum_avg = ("digits = '38157'\ntotal = 0\ncount = 0\nfor character in digits:\n    value = int(character)\n    total = total + value\n    count = count + 1\n"
           "average = total / count\nprint('Total:', total)\nprint(f'Average: {average:.2f}')\n")
E["ex-sum"] = example(sum_avg)
assert E["ex-sum"]["output"] == "Total: 24\nAverage: 4.80"
empty_avg = ("text = ''\ntotal = 0\ncount = 0\nfor character in text:\n    total = total + int(character)\n    count = count + 1\n"
             "if count > 0:\n    print(f'Average: {total / count:.2f}')\nelse:\n    print('No values to average.')\n")
E["ex-empty-avg"] = example(empty_avg)
assert E["ex-empty-avg"]["output"] == "No values to average."
E["cp2"] = {"type": "table", "xp": 1, "blanks": {"t3": num(3), "c3": num(1), "t8": num(11), "c8": num(2), "t1": num(12), "c1": num(3)}}
total, count, rows = 0, 0, []
for character in "381":
    total, count = total + int(character), count + 1
    rows.append((total, count))
assert rows == [(3, 1), (11, 2), (12, 3)]
E["cp2-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why test count > 0 first?", "answer": b64(
    "The test prevents division by zero when no value was processed.")}

# ============================================================ 3. Counting Matches
digits_count = ("text = 'Room 201 opens at 9'.lower()\ndigits = 0\nfor character in text:\n    if character.isdigit():\n        digits = digits + 1\n"
                "print('Digit characters:', digits)\n")
E["ex-digits"] = example(digits_count)
assert E["ex-digits"]["output"] == "Digit characters: 4"
matches = "word = 'mississippi'\nmatches = 0\nfor character in word:\n    if character == 's':\n        matches = matches + 1\nprint(matches)\n"
E["ex-matches"] = example(matches)
assert E["ex-matches"]["output"] == "4"
E["cp3"] = {"type": "table", "xp": 1, "blanks": {"b": num(0), "a1": num(1), "n1": num(1), "a2": num(2), "n2": num(2), "a3": num(3)}}
counter, trace = 0, []
for character in "banana":
    if character == "a":
        counter = counter + 1
    trace.append(counter)
assert trace == [0, 1, 1, 2, 2, 3]

# ============================================================ 4. Maximum and Minimum
extremes = ("digits = '38157'\nlargest = int(digits[0])\nsmallest = int(digits[0])\nfor character in digits[1:]:\n    value = int(character)\n"
            "    if value > largest:\n        largest = value\n    if value < smallest:\n        smallest = value\nprint('Largest:', largest)\nprint('Smallest:', smallest)\n")
E["ex-extremes"] = example(extremes)
assert E["ex-extremes"]["output"] == "Largest: 8\nSmallest: 1"
E["cp4"] = {"type": "table", "xp": 1, "blanks": {"l8": num(8), "s8": num(3), "l1": num(8), "s1": num(1), "l5": num(8), "s5": num(1), "l7": num(8), "s7": num(1)}}
largest = smallest = 3
trace = []
for value in (8, 1, 5, 7):
    largest, smallest = max(largest, value), min(smallest, value)
    trace.append((largest, smallest))
assert trace == [(8, 3), (8, 1), (8, 1), (8, 1)]
E["cp4-why"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "placeholder": "Why is the first real value safer than 0?", "answer": b64(
    "A real item is always a valid candidate. Zero may not occur in the data and fails for an all-negative maximum.")}

# ============================================================ 5. Search for the First Match
first = ("text = 'abracadabra'\ntarget = 'c'\nfirst_position = -1\nfor position in range(len(text)):\n    if text[position] == target:\n"
         "        first_position = position\n        break\nprint('First position:', first_position)\n")
E["ex-first"] = example(first)
assert E["ex-first"]["output"] == "First position: 4"
E["ex-first-absent"] = example(first.replace("target = 'c'", "target = 'z'"))
assert E["ex-first-absent"]["output"] == "First position: -1"
E["cp5"] = {"type": "table", "xp": 1, "blanks": {"tested": seq(0, 1, 2), "stored": num(2), "absent": num(-1)}}
assert "mississippi".find("s") == 2
E["cp5-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why is break useful?", "answer": b64(
    "The `break` stops work once the earliest match is known.")}

# ============================================================ 6. Last Match and a Special First Pass
last = ("text = 'abracadabra'\ntarget = 'a'\nlast_position = -1\nfor position in range(len(text)):\n    if text[position] == target:\n"
        "        last_position = position\nprint('Last position:', last_position)\n")
E["ex-last"] = example(last)
assert E["ex-last"]["output"] == "Last position: 10"
first_pass = ("word = 'LOOP'\nfirst = True\nfor character in word:\n    if first:\n        print(character, end='')\n        first = False\n"
              "    else:\n        print(', ', character, sep='', end='')\nprint()\n")
E["ex-first-pass"] = example(first_pass)
assert E["ex-first-pass"]["output"] == "L, O, O, P"
E["cp6"] = {"type": "table", "xp": 1, "blanks": {"values": seq(1, 3, 5)}}
assert [p for p, c in enumerate("banana") if c == "a"] == [1, 3, 5]
E["cp6-why"] = {"type": "short", "xp": 2, "minChars": 15, "rows": 2, "placeholder": "Why must the loop continue?", "answer": b64(
    "The loop must continue because a later match can replace the current last position.")}

# ============================================================ 7. Comparing Adjacent Items
adjacent = ("digits = '112358813'\nprevious = digits[0]\nfor position in range(1, len(digits)):\n    current = digits[position]\n"
            "    if current == previous:\n        print(f'Duplicate {current} at positions {position - 1} and {position}')\n    previous = current\n")
E["ex-adjacent"] = example(adjacent)
assert E["ex-adjacent"]["output"] == "Duplicate 1 at positions 0 and 1\nDuplicate 8 at positions 5 and 6"
E["cp7"] = {"type": "table", "xp": 1, "blanks": {
    "p01": yes_no(False), "p12": yes_no(True), "p23": yes_no(False),
    "pair": {"accept": ["o/o", "o, o", "o and o", "o o", "oo", "'o'/'o'", "'o', 'o'", "'o' and 'o'", "o / o", "o,o", "o"], "placeholder": "pair", "width": "6rem", "show": "o/o"},
    "where": seq(1, 2, width="7rem")}}
pairs = [(a, b) for a, b in zip("book", "book"[1:])]
assert [a == b for a, b in pairs] == [False, True, False]

# ============================================================ 8. The Random Module
rand_api = "import random\nrandom.seed(7)\nprint(random.randint(1, 6))\nprint(f'{random.random():.4f}')\nprint(random.choice('abcdef'))\n"
E["ex-random"] = example(rand_api)
assert E["ex-random"]["output"] == "3\n0.9479\nd"
E["cp8"] = {"type": "table", "xp": 1, "blanks": {
    "die": call("random.randint(1, 6)"),
    "rgb": call("random.choice('RGB')", 'random.choice("RGB")'),
    "decimal": call("random.random()"),
    "six": yes_no(True)}}
random.seed(0)
assert all(1 <= random.randint(1, 6) <= 6 for _ in range(1000)) and 6 in {random.randint(1, 6) for _ in range(1000)}

# ============================================================ 9. Random Seeds
seeded = "import random\nrandom.seed(3)\nfor trial in range(5):\n    die_1 = random.randint(1, 6)\n    die_2 = random.randint(1, 6)\n    print(die_1, die_2)\n"
E["ex-seed"] = example(seeded)
assert E["ex-seed"]["output"] == "2 5\n5 2\n3 5\n4 6\n5 1"
E["cp9"] = {"type": "short", "xp": 2, "minChars": 40, "rows": 4, "placeholder": "Same seed and ..., useful because ..., a finished game should ...", "answer": b64(
    "Use the same seed and make the same random calls in the same order. Repeatability lets a programmer reproduce and investigate a failure. "
    "A finished game usually omits the fixed seed so play varies, although a seed can remain an optional testing setting.")}

# ============================================================ 10. Simulation
simulation = ("import random\nrandom.seed(42)\nTRIALS = 10000\nhits = 0\nfor trial in range(TRIALS):\n    die_1 = random.randint(1, 6)\n    die_2 = random.randint(1, 6)\n"
              "    if die_1 + die_2 == 7:\n        hits = hits + 1\nestimate = hits / TRIALS\nprint('Trials:', TRIALS)\nprint('Sums of 7:', hits)\n"
              "print(f'Estimated probability: {estimate:.4f}')\n")
E["ex-simulation"] = example(simulation)
assert E["ex-simulation"]["output"] == "Trials: 10000\nSums of 7: 1704\nEstimated probability: 0.1704"
E["cp10"] = {"type": "table", "xp": 1, "blanks": {"estimate": num("0.19", ".19", "19%", "38 / 200 = 0.19", "38/200 = 0.19", "38/200", "38 / 200", width="8rem")}}
assert 38 / 200 == 0.19
E["cp10-why"] = {"type": "short", "xp": 2, "minChars": 30, "rows": 3, "placeholder": "One iteration represents ... A more stable estimate comes from ...", "answer": b64(
    "One iteration represents one trial of the process. Increasing the number of trials usually makes the estimate more stable.")}

# ============================================================ 11. Solve a Simpler Problem First
E["cp11"] = {"type": "short", "xp": 2, "minChars": 40, "rows": 4, "placeholder": "The order of the tasks, then why one toss comes first…", "answer": b64(
    "Generate one result, increase a counter when it is heads, place those steps in a 1,000-pass loop, then print the final count. "
    "The first task verifies the random call that becomes the loop body.")}

# ============================================================ 12. Putting It All Together
one_pair = "import random\nrandom.seed(12)\nprevious = random.randint(0, 9)\ncurrent = random.randint(0, 9)\nprint(previous, current)\nprint(current > previous)\n"
E["ex-pair"] = example(one_pair)
assert E["ex-pair"]["output"] == "7 4\nFalse"
pairs_code = ("import random\nrandom.seed(12)\nPAIRS = 8\nincreases = 0\nprevious = random.randint(0, 9)\nfor pair in range(PAIRS):\n    current = random.randint(0, 9)\n"
              "    if current > previous:\n        increases = increases + 1\n    previous = current\nprint('Pairs:', PAIRS)\nprint('Increases:', increases)\n"
              "print(f'Estimated fraction: {increases / PAIRS:.3f}')\n")
E["ex-pairs"] = example(pairs_code)
assert E["ex-pairs"]["output"] == "Pairs: 8\nIncreases: 4\nEstimated fraction: 0.500"
E["cp12"] = {"type": "short", "xp": 2, "minChars": 40, "rows": 4, "placeholder": "Why initialize previous first, why update it last, what makes the output repeat…", "answer": b64(
    "The first comparison needs a real earlier digit. The update makes the current digit the earlier digit for the next pair. "
    "The fixed seed and unchanged sequence of random calls make the output reproducible.")}

# ============================================================ Review
E["fr1"] = {"type": "short", "xp": 2, "answer": b64("Accumulator, counter, running best, and first-match search.")}
E["fr2"] = {"type": "short", "xp": 2, "answer": b64("A real item is a valid candidate, while an invented starting value may win incorrectly.")}
E["fr3"] = {"type": "short", "xp": 2, "answer": b64("The earliest match is final, but the last match can be replaced.")}
E["fr4"] = {"type": "short", "xp": 2, "answer": b64("`-1`.")}
E["fr5"] = {"type": "short", "xp": 2, "answer": b64("Index 0 has no previous item.")}
E["fr6"] = {"type": "short", "xp": 2, "answer": b64("The integers 1 through 6, inclusive.")}
E["fr7"] = {"type": "short", "xp": 2, "answer": b64("A repeatable pseudorandom sequence.")}
E["fr8"] = {"type": "short", "xp": 2, "answer": b64("One trial of the process.")}
E["fr9"] = {"type": "short", "xp": 2, "answer": b64("The smaller solution usually becomes the body or initialization of the full loop.")}

# ============================================================ Coding Practice
RE = "import re\n"
WHILE = RE + 'assert re.search(r"^\\s*while\\b", __code__, re.M), "Use a while loop; the number of values is not known in advance."\n'
FOR = RE + 'assert re.search(r"^\\s*for\\b", __code__, re.M), "Use a for loop."\n'
ANY_LOOP = RE + 'assert re.search(r"^\\s*(for|while)\\b", __code__, re.M), "Use a loop."\n'
TWO_DP = 'assert re.search(r":[^}]*\\.2f\\}", __source__), "Print the value with two decimal places using :.2f."\n'
FOUR_DP = 'assert re.search(r":[^}]*\\.4f\\}", __source__), "Print the value with four decimal places using :.4f."\n'
SEED = 'assert re.search(r"random\\.seed\\(\\s*seed\\s*\\)", __code__), "Seed the generator with random.seed(seed) before the first random call."\n'

# 1. Safe Extreme Initialization
E["p1"] = {"type": "short", "xp": 2, "minChars": 60, "rows": 5, "placeholder": "Why 0 is unsafe, one failing data set for each, and the safe approach…", "answer": b64(
    "For `largest = 0`, the data `-8, -3, -5` incorrectly leaves 0 as the largest. For `smallest = 0`, the data `4, 9, 2` incorrectly leaves 0 as the smallest. "
    "Initialize both from the first real item, then process the remaining items.")}
assert max(0, -8, -3, -5) == 0 and min(0, 4, 9, 2) == 0

# 2. Sensor Summary
sensor = """import math
count = 0
total = 0.0
square_total = 0.0
text = input()
while text != '':
    value = float(text)
    count = count + 1
    total = total + value
    square_total = square_total + value * value
    text = input()
if count < 2:
    print('Need at least two values.')
else:
    average = total / count
    deviation = math.sqrt((square_total - total * total / count) / (count - 1))
    print('Count:', count)
    print(f'Average: {average:.2f}')
    print(f'Standard deviation: {deviation:.2f}')
"""
E["p2"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": "import math\ncount = 0\ntotal = 0.0\nsquare_total = 0.0\ntext = input()\n# Read values until the blank line, then print the summary.\n",
    "cases": [case("Typed 2, 4, 6, blank", ["2", "4", "6", ""], sensor), case("Typed 5, blank", ["5", ""], sensor),
              case("Typed blank", [""], sensor), case("Typed 1.5, 2.5, blank", ["1.5", "2.5", ""], sensor),
              case("Typed 10, 10, 10, 10, blank", ["10", "10", "10", "10", ""], sensor), case("Typed 3, 7, 8, 12, blank", ["3", "7", "8", "12", ""], sensor)],
    "check": WHILE + TWO_DP + '''assert "math.sqrt(" in __code__, "Take the square root with math.sqrt()."
assert re.search(r"count\\s*<\\s*2|count\\s*<=\\s*1|count\\s*>=\\s*2|count\\s*>\\s*1", __code__), "Test count < 2 before dividing."
''',
    "answer": b64(sensor),
    "answerNote": "The loop needs only the count, sum, and sum of squares. The size check protects both the average and the denominator."}
assert E["p2"]["cases"][0]["expected"] == "Count: 3\nAverage: 4.00\nStandard deviation: 2.00"
assert E["p2"]["cases"][1]["expected"] == E["p2"]["cases"][2]["expected"] == "Need at least two values."

# 3. Two-Step Sequence
two_step = """n = int(input())
older = 2
newer = 3
for position in range(3, n + 1):
    next_value = older + newer
    older = newer
    newer = next_value
if n == 1:
    print(older)
else:
    print(newer)
"""
E["p3"] = {"type": "code", "xp": 5, "minLines": 8, "starter": "n = int(input())\nolder = 2\nnewer = 3\n# Keep only the previous two terms.\n",
    "cases": [case("Typed 6", ["6"], two_step), case("Typed 1", ["1"], two_step), case("Typed 2", ["2"], two_step),
              case("Typed 3", ["3"], two_step), case("Typed 10", ["10"], two_step), case("Typed 20", ["20"], two_step)],
    "check": ANY_LOOP + '''assert "[" not in __code__, "Keep only the previous two terms in older and newer; no list is needed."
assert __stdout__.count("\\n") <= 1, "Print only term n."
''',
    "answer": b64(two_step),
    "answerNote": "Term 1 is `older`; every later term is `newer` after the loop, which makes zero passes for n = 2."}
assert E["p3"]["cases"][0]["expected"] == "21" and E["p3"]["cases"][1]["expected"] == "2" and E["p3"]["cases"][2]["expected"] == "3"

# 4. Exact Divisors
divisors = """number = int(input())
for candidate in range(2, number + 1):
    if number % candidate == 0:
        print(candidate)
"""
E["p4"] = {"type": "code", "xp": 5, "minLines": 4, "starter": "number = int(input())\n# Print every divisor from 2 through number, one per line.\n",
    "cases": [case("Typed 12", ["12"], divisors), case("Typed 7", ["7"], divisors), case("Typed 1", ["1"], divisors),
              case("Typed 2", ["2"], divisors), case("Typed 36", ["36"], divisors)],
    "check": FOR + 'assert re.search(r"%\\s*candidate|%\\s*\\w+\\s*==\\s*0", __code__), "Test each candidate with the remainder operator %."\n',
    "answer": b64(divisors),
    "answerNote": "A divisor leaves remainder 0. The range stops at number + 1 so the number itself is tested."}
assert E["p4"]["cases"][0]["expected"] == "2\n3\n4\n6\n12" and E["p4"]["cases"][2]["expected"] == ""

# 5. Prime Report
primes = """limit = int(input())
for candidate in range(2, limit + 1):
    prime = True
    for divisor in range(2, candidate):
        if candidate % divisor == 0:
            prime = False
            break
    if prime:
        print(candidate)
"""
E["p5"] = {"type": "code", "xp": 10, "minLines": 8, "starter": "limit = int(input())\n# Test every candidate from 2 through limit.\n",
    "cases": [case("Typed 10", ["10"], primes), case("Typed 2", ["2"], primes), case("Typed 3", ["3"], primes),
              case("Typed 20", ["20"], primes), case("Typed 50", ["50"], primes)],
    "check": RE + '''assert len(re.findall(r"^\\s*for\\b", __code__, re.M)) >= 2, "Use nested loops: an outer loop over the candidates and an inner loop over the divisors."
assert "True" in __code__ and "False" in __code__, "Use a Boolean variable that records whether a divisor was found."
''',
    "answer": b64(primes),
    "answerNote": "The inner loop stops at the first divisor. The flag `prime` survives the inner loop only when no divisor was found."}
assert E["p5"]["cases"][0]["expected"] == "2\n3\n5\n7" and E["p5"]["cases"][1]["expected"] == "2"

# 6. Last Token Game
tokens_game = """import random
seed = int(input())
tokens = int(input())
random.seed(seed)
player_turn = True
while tokens > 0:
    if player_turn:
        move = int(input())
    else:
        move = random.randint(1, 2)
    if move > tokens:
        move = tokens
    tokens = tokens - move
    if tokens == 0:
        if player_turn:
            print('Player wins')
        else:
            print('Computer wins')
    player_turn = not player_turn
"""

def token_inputs(seed, start, player_moves):
    """The input lines for one game: the seed, the pile, then only as many
    player moves as the game consumes (cycling through `player_moves`)."""
    random.seed(seed)
    tokens, player_turn, moves, i = start, True, [], 0
    while tokens > 0:
        if player_turn:
            move = player_moves[i % len(player_moves)]
            i += 1
            moves.append(move)
        else:
            move = random.randint(1, 2)
        if move > tokens:
            move = tokens
        tokens = tokens - move
        player_turn = not player_turn
    return [str(seed), str(start)] + [str(m) for m in moves]

E["p6"] = {"type": "code", "xp": 10, "minLines": 14,
    "starter": "import random\nseed = int(input())\ntokens = int(input())\nrandom.seed(seed)\nplayer_turn = True\n# Alternate turns until the pile is empty, then print the winner.\n",
    "cases": [case("Seed 1, 10 tokens, player takes 2", token_inputs(1, 10, [2]), tokens_game),
              case("Seed 3, 15 tokens, player takes 1", token_inputs(3, 15, [1]), tokens_game),
              case("Seed 7, 12 tokens, player alternates 1, 2", token_inputs(7, 12, [1, 2]), tokens_game),
              case("Seed 2, 30 tokens, player takes 2", token_inputs(2, 30, [2]), tokens_game),
              case("Seed 5, 11 tokens, player takes 2", token_inputs(5, 11, [2]), tokens_game)],
    "check": WHILE + SEED + '''assert re.search(r"random\\.randint\\(\\s*1\\s*,\\s*2\\s*\\)", __code__), "Choose the computer's move with random.randint(1, 2)."
assert __stdout__.count("\\n") <= 1, "Print one line: the winner."
''',
    "answer": b64(tokens_game),
    "answerNote": "`player_turn = not player_turn` switches the turn at the end of every pass. Reducing an oversized move keeps the pile from going negative."}
assert E["p6"]["cases"][0]["inputs"][:2] == ["1", "10"]
assert E["p6"]["cases"][0]["expected"] in ("Player wins", "Computer wins")
assert {c["expected"] for c in E["p6"]["cases"]} == {"Player wins", "Computer wins"}

# 7. Four-Direction Walk
walk = """import random
seed = int(input())
steps = int(input())
random.seed(seed)
x = 0
y = 0
for step in range(steps):
    direction = random.choice('NSEW')
    if direction == 'N':
        y = y + 1
    elif direction == 'S':
        y = y - 1
    elif direction == 'E':
        x = x + 1
    else:
        x = x - 1
print(x, y)
"""
E["p7"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": "import random\nseed = int(input())\nsteps = int(input())\nrandom.seed(seed)\nx = 0\ny = 0\n# Take the steps, then print x and y.\n",
    "cases": [case("Typed 1, 5", ["1", "5"], walk), case("Typed 3, 1", ["3", "1"], walk), case("Typed 7, 10", ["7", "10"], walk),
              case("Typed 2, 25", ["2", "25"], walk), case("Typed 10, 100", ["10", "100"], walk)],
    "check": FOR + SEED + '''assert re.search(r"random\\.choice\\(\\s*['\\"]NSEW['\\"]\\s*\\)", __source__), "Choose each direction with random.choice('NSEW')."
assert __stdout__.count("\\n") <= 1, "Print one line: x and y separated by a space."
''',
    "answer": b64(walk),
    "answerNote": "Each loop pass changes exactly one coordinate by 1."}
assert E["p7"]["cases"][0]["expected"] == "0 1"

# 8. Three-Envelope Simulation
envelopes = """import random
seed = int(input())
trials = int(input())
random.seed(seed)
stay_wins = 0
switch_wins = 0
for trial in range(trials):
    prize = random.randint(1, 3)
    choice = random.randint(1, 3)
    if choice == prize:
        stay_wins = stay_wins + 1
    else:
        switch_wins = switch_wins + 1
print('Stay wins:', stay_wins)
print('Switch wins:', switch_wins)
"""
E["p8"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": "import random\nseed = int(input())\ntrials = int(input())\nrandom.seed(seed)\nstay_wins = 0\nswitch_wins = 0\n# Run the trials, then print both counts.\n",
    "cases": [case("Typed 1, 10", ["1", "10"], envelopes), case("Typed 5, 1", ["5", "1"], envelopes), case("Typed 42, 100", ["42", "100"], envelopes),
              case("Typed 2, 30", ["2", "30"], envelopes), case("Typed 9, 1000", ["9", "1000"], envelopes)],
    "check": FOR + SEED + '''assert len(re.findall(r"random\\.randint\\(\\s*1\\s*,\\s*3\\s*\\)", __code__)) >= 2, "Call random.randint(1, 3) twice per trial: first for the prize, then for the choice."
''',
    "answer": b64(envelopes),
    "answerNote": "Every trial adds 1 to exactly one counter, so the two counts always sum to the number of trials."}
assert E["p8"]["cases"][0]["expected"] == "Stay wins: 3\nSwitch wins: 7"

# 9. Line-Crossing Estimate
crossing = """import math
import random
seed = int(input())
trials = int(input())
random.seed(seed)
hits = 0
for trial in range(trials):
    start = 2 * random.random()
    angle = math.pi * random.random()
    if start + math.sin(angle) >= 2:
        hits = hits + 1
print(f'{trials / hits:.4f}')
"""
E["p9"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": "import math\nimport random\nseed = int(input())\ntrials = int(input())\nrandom.seed(seed)\nhits = 0\n# Count the hits, then print trials / hits.\n",
    "cases": [case("Typed 1, 100", ["1", "100"], crossing), case("Typed 2, 1000", ["2", "1000"], crossing), case("Typed 7, 50", ["7", "50"], crossing),
              case("Typed 3, 10", ["3", "10"], crossing), case("Typed 11, 5000", ["11", "5000"], crossing)],
    "check": FOR + SEED + FOUR_DP + '''assert len(re.findall(r"random\\.random\\(\\s*\\)", __code__)) >= 2, "Call random.random() twice per trial: first for start, then for angle."
assert "math.sin(" in __code__ and "math.pi" in __code__, "Use math.pi for the angle and math.sin() for the test."
''',
    "answer": b64(crossing),
    "answerNote": "The two random values describe one trial. The ratio estimates a constant."}
assert E["p9"]["cases"][0]["expected"] == "3.2258"

# 10. Tiny Number Generator
tiny = """state = int(input())
for count in range(12):
    state = (17 * state + 5) % 64
    print(state)
"""
E["p10"] = {"type": "code", "xp": 5, "minLines": 4, "starter": "state = int(input())\n# Repeat 12 times: compute the new state and print it.\n",
    "cases": [case("Typed 1", ["1"], tiny), case("Typed 0", ["0"], tiny), case("Typed 63", ["63"], tiny), case("Typed 10", ["10"], tiny)],
    "check": FOR + '''assert re.search(r"range\\(\\s*12\\s*\\)", __code__), "Repeat exactly 12 times with range(12)."
assert re.search(r"%\\s*64\\b", __code__), "Compute the new state with (17 * state + 5) % 64."
''',
    "answer": b64(tiny),
    "answerNote": "Each output becomes the state used by the next pass."}
assert E["p10"]["cases"][0]["expected"].split("\n")[:3] == ["22", "59", "48"]

# 11. Target Reading
target = """target = float(input())
count = 0
price = float(input())
count = count + 1
while price < target:
    price = float(input())
    count = count + 1
print(f'Reached: {price:.2f}')
print('Readings:', count)
"""
E["p11"] = {"type": "code", "xp": 5, "minLines": 8, "starter": "target = float(input())\ncount = 0\n# Read prices until one is at least the target.\n",
    "cases": [case("Typed 10, then 5, 9, 10", ["10", "5", "9", "10"], target), case("Typed 3.5, then 4", ["3.5", "4"], target),
              case("Typed 100, then 50, 150", ["100", "50", "150"], target), case("Typed 20, then 20", ["20", "20"], target),
              case("Typed 2, then 1.99, 1.5, 0.75, 2.25", ["2", "1.99", "1.5", "0.75", "2.25"], target)],
    "check": WHILE + TWO_DP + 'assert re.search(r"price\\s*<\\s*target|target\\s*>\\s*price", __code__), "Keep reading while price < target."\n',
    "answer": b64(target),
    "answerNote": "The target condition ends the loop; a counter records how many readings were needed."}
assert E["p11"]["cases"][0]["expected"] == "Reached: 10.00\nReadings: 3"

# 12. Eight-Digit Check
eight = """number = input()
total = 0
for position in range(7, -1, -2):
    total = total + int(number[position])
for position in range(6, -1, -2):
    doubled = 2 * int(number[position])
    total = total + doubled // 10 + doubled % 10
if total % 10 == 0:
    print('Valid')
else:
    partial = total - int(number[7])
    check = (10 - partial % 10) % 10
    print('Invalid')
    print('Required check digit:', check)
"""
def luhn_ok(digits):
    total = sum(int(digits[p]) for p in range(7, -1, -2))
    for p in range(6, -1, -2):
        d = 2 * int(digits[p])
        total += d // 10 + d % 10
    return total % 10 == 0
assert not luhn_ok("12345678") and luhn_ok("12345674")
E["p12"] = {"type": "code", "xp": 10, "minLines": 12, "starter": "number = input()\ntotal = 0\n# Add the two sums, then decide.\n",
    "cases": [case("Typed 12345674", ["12345674"], eight), case("Typed 12345678", ["12345678"], eight), case("Typed 00000000", ["00000000"], eight),
              case("Typed 79927398", ["79927398"], eight), case("Typed 49927398", ["49927398"], eight), case("Typed 99999999", ["99999999"], eight)],
    "check": FOR + '''assert "range(" in __code__, "Visit alternating positions with range() and a step of -2."
assert re.search(r"//\\s*10\\b", __code__) and re.search(r"%\\s*10\\b", __code__), "Split each doubled value into its decimal digits with // 10 and % 10."
''',
    "answer": b64(eight),
    "answerNote": "Index loops separate alternating positions. The needed check digit is the amount required to reach the next multiple of 10."}
assert E["p12"]["cases"][0]["expected"] == "Valid"
assert E["p12"]["cases"][1]["expected"] == "Invalid\nRequired check digit: 4"

# 13. Two Populations
populations = """a = float(input())
b = float(input())
c = float(input())
d = float(input())
prey = float(input())
predators = float(input())
periods = int(input())
for period in range(1, periods + 1):
    new_prey = prey * (1 + a - b * predators)
    new_predators = predators * (1 - c + d * prey)
    prey = new_prey
    predators = new_predators
    print(period, f'{prey:.2f}', f'{predators:.2f}')
"""
E["p13"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": "a = float(input())\nb = float(input())\nc = float(input())\nd = float(input())\nprey = float(input())\npredators = float(input())\nperiods = int(input())\n# Print one line per period.\n",
    "cases": [case("Zero rates, 10 and 5, 2 periods", ["0", "0", "0", "0", "10", "5", "2"], populations),
              case("0.1, 0.01, 0.01, 0.00002, 1000 and 20, 3 periods", ["0.1", "0.01", "0.01", "0.00002", "1000", "20", "3"], populations),
              case("0.5, 0.1, 0.2, 0.05, 8 and 2, 1 period", ["0.5", "0.1", "0.2", "0.05", "8", "2", "1"], populations),
              case("0.2, 0.02, 0.1, 0.001, 500 and 30, 5 periods", ["0.2", "0.02", "0.1", "0.001", "500", "30", "5"], populations)],
    "check": FOR + TWO_DP + '''assert "new_prey" in globals() and "new_predators" in globals(), "Compute new_prey and new_predators from the old populations before updating either variable."
''',
    "answer": b64(populations),
    "answerNote": "Both new values must use the old populations, so compute them before either update."}
assert E["p13"]["cases"][0]["expected"] == "1 10.00 5.00\n2 10.00 5.00"

# 14. Vertical Motion Table
motion = """INTERVAL = 0.01
GRAVITY = 9.81
velocity = float(input())
height = 0.0
step = 0
print('0 0.00')
while height >= 0:
    height = height + velocity * INTERVAL
    velocity = velocity - GRAVITY * INTERVAL
    step = step + 1
    if step % 100 == 0 and height >= 0:
        print(step // 100, f'{height:.2f}')
"""
E["p14"] = {"type": "code", "xp": 10, "minLines": 10,
    "starter": "INTERVAL = 0.01\nGRAVITY = 9.81\nvelocity = float(input())\nheight = 0.0\nstep = 0\nprint('0 0.00')\n# Repeat until the height becomes negative.\n",
    "cases": [case("Typed 0", ["0"], motion), case("Typed 20", ["20"], motion), case("Typed 9.81", ["9.81"], motion),
              case("Typed 50", ["50"], motion), case("Typed 4", ["4"], motion)],
    "check": WHILE + TWO_DP + '''assert re.search(r"%\\s*100\\b", __code__), "Count the steps and print when step % 100 == 0."
assert "INTERVAL" in __code__ and "GRAVITY" in __code__, "Use the constants INTERVAL and GRAVITY in the updates."
''',
    "answer": b64(motion),
    "answerNote": "A step counter avoids unreliable equality tests on floating-point time."}
assert E["p14"]["cases"][0]["expected"] == "0 0.00"
assert E["p14"]["cases"][1]["expected"].split("\n")[0] == "0 0.00" and len(E["p14"]["cases"][1]["expected"].split("\n")) == 5

# 15. Decay Table
decay = """initial = float(input())
half_life = float(input())
for hour in range(25):
    relative = 2 ** (-hour / half_life)
    print(hour, f'{relative:.4f}', f'{initial * relative:.4f}')
"""
E["p15"] = {"type": "code", "xp": 5, "minLines": 5, "starter": "initial = float(input())\nhalf_life = float(input())\n# Print hours 0 through 24.\n",
    "cases": [case("Typed 100, 6", ["100", "6"], decay), case("Typed 1, 1", ["1", "1"], decay), case("Typed 50, 24", ["50", "24"], decay),
              case("Typed 8, 3", ["8", "3"], decay)],
    "check": FOR + FOUR_DP + '''assert re.search(r"range\\(\\s*25\\s*\\)|range\\(\\s*0\\s*,\\s*25\\s*\\)", __code__), "Visit hours 0 through 24 with range(25)."
assert re.search(r"2\\s*\\*\\*", __code__), "Compute the relative amount with 2 ** (-hour / half_life)."
''',
    "answer": b64(decay),
    "answerNote": "The loop generates the requested time points and evaluates the provided formula."}
rows = E["p15"]["cases"][0]["expected"].split("\n")
assert len(rows) == 25 and rows[0] == "0 1.0000 100.0000" and rows[-1] == "24 0.0625 6.2500"

# 16. Curve Point Table
curve = """for step in range(11):
    x = step / 10
    y = 0.00005 * x ** 3 - 0.03 * x ** 2 + 4 * x + 200
    print(f'{x:.4f}', f'{y:.4f}')
"""
E["p16"] = {"type": "code", "xp": 5, "minLines": 4, "starter": "# Use an integer counter to create x = 0.0, 0.1, ..., 1.0.\n",
    "cases": [{"name": "The 11 rows", "expected": run(curve)}],
    "check": FOR + FOUR_DP + '''assert re.search(r"range\\(\\s*11\\s*\\)|range\\(\\s*0\\s*,\\s*11\\s*\\)", __code__), "Count the rows with an integer counter: range(11)."
assert re.search(r"/\\s*10\\b|\\*\\s*0\\.1\\b|0\\.1\\s*\\*", __code__), "Turn the counter into x by dividing by 10."
''',
    "answer": b64(curve),
    "answerNote": "The integer counter creates exact tenths for a table that could later supply points to graphics code."}
rows = E["p16"]["cases"][0]["expected"].split("\n")
assert len(rows) == 11 and rows[0] == "0.0000 200.0000" and rows[-1] == "1.0000 203.9700"

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-16",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 16 Workbook",
    "subtitle": "Common loop algorithms and random numbers",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-16/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
