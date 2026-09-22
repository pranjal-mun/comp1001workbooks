"""Build workbooks/lecture-15/boss/exercises.json: the Lecture 15 boss problems.

The four problems are the Boss Problems section of the kit's
LECTURE_15_SHARED_CONTENT.tex, in its order. Expected outputs are produced
by actually running the model solutions. Run from anywhere:

    python3 workbooks/lecture-15/boss/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-15/boss
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

NO_IMPORT = 'assert "import" not in __code__, "Solve it with loops and the tools from this lecture; no import is needed."\n'
NESTED_FOR = '''import re
_fors = [len(m.group(1).expandtabs(4)) for m in re.finditer(r"^([ \\t]*)for\\b", __code__, re.M)]
assert len(_fors) >= 2 and max(_fors) > min(_fors), "Use nested for loops: an inner for loop inside the body of an outer one."
'''

E = {}

# ---------------------------------------------------------------- 1 Course Product Grid
grid = """size = int(input())

print("    ", end="")
for column in range(1, size + 1):
    print(f"{column:4}", end="")
print()

for row in range(1, size + 1):
    print(f"{row:4}", end="")
    for column in range(1, size + 1):
        print(f"{row * column:4}", end="")
    print()
"""
E["grid"] = {"type": "code", "xp": 10, "boss": "👹", "minLines": 10,
    "starter": "size = int(input())\n# Print the column labels, then the labelled rows.\n",
    "cases": input_cases(grid, ("Typed 3", ["3"]), ("Typed 1", ["1"]), ("Typed 9", ["9"]), ("Typed 5", ["5"]), ("Typed 2", ["2"])),
    "check": NESTED_FOR + NO_IMPORT + '''assert "while" not in __code__, "Use for loops here, not a while loop."
assert re.search(r":[^}]*4\\}", __source__), "Give every label and product a field width of four with :4."
''',
    "answer": b64(grid),
    "hints": [
        'The first line is the empty top-left corner followed by the column labels. Start it with `print("    ", end="")` (four spaces), then `for column in range(1, size + 1):` prints `f"{column:4}"` with `end=""`, and an empty `print()` ends the line.',
        'Each later row starts with its label, `print(f"{row:4}", end="")`, and then an inner loop over the same columns prints `f"{row * column:4}"` with `end=""`.',
        'The empty `print()` that ends a row belongs after the inner loop but inside the outer loop. For a size of 1, the first line is the four-space corner followed by the label 1 in a four-character field, and the second line is the label 1 followed by the product 1, each in a four-character field.',
    ],
    "answerNote": "Print four spaces for the empty top-left corner. Then use one loop for the column labels and nested loops for the labelled rows and products."}
assert E["grid"]["cases"][0]["expected"] == "       1   2   3\n   1   1   2   3\n   2   2   4   6\n   3   3   6   9"
assert E["grid"]["cases"][1]["expected"] == "       1\n   1   1"
assert E["grid"]["cases"][2]["expected"].split("\n")[-1] == "   9   9  18  27  36  45  54  63  72  81"

# ---------------------------------------------------------------- 2 Lab Station Binary Label
binary = """number = int(input())
result = ""
quotient = number

while True:
    remainder = quotient % 2
    result = str(remainder) + result
    quotient = quotient // 2
    if quotient == 0:
        break

print(result)
"""
E["binary"] = {"type": "code", "xp": 15, "boss": "👾", "minLines": 10,
    "starter": "number = int(input())\nresult = \"\"\nquotient = number\n\nwhile True:\n    # Add one binary digit and decide whether to stop.\n    break\n\nprint(result)\n",
    "cases": input_cases(binary, ("Typed 13", ["13"]), ("Typed 0", ["0"]), ("Typed 1023", ["1023"]), ("Typed 1", ["1"]),
                         ("Typed 2", ["2"]), ("Typed 8", ["8"]), ("Typed 255", ["255"]), ("Typed 512", ["512"])),
    "check": NO_IMPORT + '''import re
assert re.search(r"^\\s*while\\s+True\\b", __code__, re.M), "Use while True for the loop."
assert len(re.findall(r"^\\s*break\\b", __code__, re.M)) == 1, "Leave the loop with exactly one break."
assert re.search(r"%\\s*2\\b", __code__), "Find each binary digit with the remainder after division by 2."
assert re.search(r"//\\s*2\\b", __code__), "Move to the next digit with integer division by 2."
assert "bin(" not in __code__ and "format(" not in __code__ and ":b" not in __code__, "Build the digits with the loop; bin() and format codes are not needed."
assert __stdout__.count("\\n") <= 1, "Print exactly one line."
''',
    "answer": b64(binary),
    "hints": [
        'Each pass takes one digit: `remainder = quotient % 2` is 0 or 1, and `result = str(remainder) + result` puts it at the front of the result.',
        'After adding the digit, move on with `quotient = quotient // 2`. When the quotient has reached 0 there are no digits left, so `if quotient == 0:` is where the one `break` belongs.',
        'Trace 13: the remainders are 1, 0, 1, 1 and the quotients are 6, 3, 1, 0, so the result grows as `1`, `01`, `101`, `1101`. Because the digit is added before the test, a number of 0 still produces the digit `0`.',
    ],
    "answerNote": "Each remainder is the next binary digit from the right. Adding it to the front keeps the final digits in reading order. The loop also handles zero because it computes one remainder before the break."}
assert E["binary"]["cases"][0]["expected"] == "1101"
assert E["binary"]["cases"][1]["expected"] == "0"
assert E["binary"]["cases"][2]["expected"] == "1111111111"
assert E["binary"]["cases"][7]["expected"] == "1000000000"

# ---------------------------------------------------------------- 3 Phrase Mirror Check
mirror = """phrase = input()
cleaned = ""

for character in phrase.lower():
    if character == " " or character == "," or character == "." \\
            or character == "!" or character == "?":
        continue
    cleaned = cleaned + character

is_palindrome = True
for position in range(len(cleaned) // 2):
    opposite = len(cleaned) - 1 - position
    if cleaned[position] != cleaned[opposite]:
        is_palindrome = False
        break

if is_palindrome:
    print("Palindrome")
else:
    print("Not a palindrome")
"""
E["mirror"] = {"type": "code", "xp": 20, "boss": "🐉", "minLines": 14,
    "starter": "phrase = input()\ncleaned = \"\"\n# Build cleaned, then compare matching positions from the two ends.\n",
    "cases": input_cases(mirror, ("Typed Never odd or even!", ["Never odd or even!"]), ("Typed Hello, MUN!", ["Hello, MUN!"]),
                         ("Typed an empty line", [""]), ("Typed A man, a plan, a canal. Panama!", ["A man, a plan, a canal. Panama!"]),
                         ("Typed Was it a car or a cat I saw?", ["Was it a car or a cat I saw?"]), ("Typed No lemon, no melon", ["No lemon, no melon"]),
                         ("Typed MUN", ["MUN"]), ("Typed a", ["a"]), ("Typed ab", ["ab"]), ("Typed Racecar", ["Racecar"]),
                         ("Typed Step on no pets.", ["Step on no pets."])),
    "check": NO_IMPORT + '''assert "continue" in __code__, "Skip each ignored character with continue while cleaning the phrase."
assert "break" in __code__, "Leave the comparison loop with break when a mismatched pair is found."
assert "[::" not in __code__ and "reversed(" not in __code__, "Compare the two ends with a loop, not with slicing or reversed()."
assert ".lower(" in __code__ or ".upper(" in __code__ or ".casefold(" in __code__, "Make uppercase and lowercase letters equal with lower() or upper()."
assert __stdout__.count("\\n") <= 1, "Print exactly one line."
''',
    "answer": b64(mirror),
    "hints": [
        'Clean first: `for character in phrase.lower():` visits every character in one case. If the character is a space, comma, period, exclamation mark or question mark, `continue`; otherwise add it to `cleaned`. For `Hello, MUN!` this gives `hellomun`.',
        'Compare from the two ends. Position `position` from the left pairs with `len(cleaned) - 1 - position` from the right, and `range(len(cleaned) // 2)` visits every pair once.',
        'Start with `is_palindrome = True`. When a pair differs, set it to `False` and `break`. After the loop, one `if`/`else` prints `Palindrome` or `Not a palindrome`.',
        'An empty phrase gives an empty `cleaned`, so the comparison loop makes zero passes and the flag stays `True`.',
    ],
    "answerNote": "Build a lowercase string containing only the letters. Compare the first letter with the last, the second with the second-last, and so on. Stop at the first mismatch."}
assert E["mirror"]["cases"][0]["expected"] == "Palindrome"
assert E["mirror"]["cases"][1]["expected"] == "Not a palindrome"
assert E["mirror"]["cases"][2]["expected"] == "Palindrome"
assert E["mirror"]["cases"][6]["expected"] == "Not a palindrome"
assert E["mirror"]["cases"][8]["expected"] == "Not a palindrome"
assert E["mirror"]["cases"][10]["expected"] == "Palindrome"

# ---------------------------------------------------------------- 4 Prime Roll Call
primes = """limit = int(input())
printed_prime = False

for candidate in range(2, limit + 1):
    is_prime = True
    for divisor in range(2, candidate):
        if candidate % divisor == 0:
            is_prime = False
            break
    if is_prime:
        print(candidate)
        printed_prime = True

if not printed_prime:
    print("No primes")
"""
E["primes"] = {"type": "code", "xp": 25, "boss": "💀", "minLines": 12,
    "starter": ("limit = int(input())\nprinted_prime = False\n\nfor candidate in range(2, limit + 1):\n    is_prime = True\n"
                "    # Test possible divisors here.\n\nif not printed_prime:\n    print(\"No primes\")\n"),
    "cases": input_cases(primes, ("Typed 10", ["10"]), ("Typed 1", ["1"]), ("Typed 2", ["2"]), ("Typed 30", ["30"]),
                         ("Typed 4", ["4"]), ("Typed 100", ["100"]), ("Typed 200", ["200"])),
    "check": NESTED_FOR + NO_IMPORT + '''assert "break" in __code__, "Leave the divisor loop with break as soon as a divisor is found."
assert "%" in __code__, "Recognise a divisor by a remainder of zero with %."
assert "while" not in __code__, "Use for loops here, not a while loop."
''',
    "answer": b64(primes),
    "hints": [
        'Inside the outer loop, test the divisors with `for divisor in range(2, candidate):`. For a candidate of 2 that range is empty, so 2 stays prime.',
        'A divisor leaves no remainder: `if candidate % divisor == 0:` sets `is_prime = False` and then `break`. The `break` ends only the divisor loop; the outer loop moves to the next candidate.',
        'After the inner loop, `if is_prime:` prints the candidate and sets `printed_prime = True`, so the final `No primes` line appears only when nothing was printed.',
    ],
    "answerNote": "Assume each candidate is prime, then look for evidence that it is not. Finding one divisor sets the Boolean variable to false and ends only the inner loop. The outer loop then tests the next candidate."}
assert E["primes"]["cases"][0]["expected"] == "2\n3\n5\n7"
assert E["primes"]["cases"][1]["expected"] == "No primes"
assert E["primes"]["cases"][2]["expected"] == "2"
assert E["primes"]["cases"][3]["expected"] == "2\n3\n5\n7\n11\n13\n17\n19\n23\n29"
assert E["primes"]["cases"][6]["expected"].count("\n") == 45

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-15-boss",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 15 Boss Problems",
    "short": "L15 bosses",
    "subtitle": "Nested loops, break and continue",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-15/boss/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
