"""Build workbooks/lecture-18/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_18_SHARED_CONTENT.tex; model answers follow its \\solution{...}
text. Run from anywhere:

    python3 workbooks/lecture-18/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-18
"""
import base64, json, math, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=(), ok=True):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""), capture_output=True, text=True)
    if ok:
        assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n"), p.stderr

def out(code, inputs=()):
    return run(code, inputs)[0]

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
    return out(wrapper)

def example(code, output=True):
    spec = {"type": "example", "code": code.rstrip("\n")}
    if output:
        spec["output"] = out(code)
    return spec

def program_case(name, code):
    return {"name": name, "expected": out(code)}

def input_cases(code, *runs):
    return [{"name": name, "inputs": list(inputs), "expected": run_with_prompts(code, inputs)} for name, inputs in runs]

def num(*values, width="5rem"):
    return {"accept": [str(v) for v in values], "placeholder": "value", "width": width}

def short(answer, xp=2, min_chars=15, rows=2, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

def namespace(code):
    ns = {}
    exec(code, ns)
    return ns

E = {}

# ---------------------------------------------------------------- checks shared by the coding tasks
# A check runs after the student's program in the same namespace. `_fn` finds a
# function the program defined and checks its parameter count. `_returns` calls
# it with its output captured, so the test call does not add to the program's
# own output, and compares the returned value.
FN = '''import types, io, contextlib, re
_WORDS = ["empty parentheses", "one parameter", "two parameters", "three parameters", "four parameters"]
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
    value, printed = _call(name, *args)
    call = _shown(name, args)
    if value is None:
        raise AssertionError(call + " returned None. Send the result back with return.")
    if isinstance(want, bool):
        ok = value is want
    elif isinstance(want, (int, float)):
        ok = isinstance(value, (int, float)) and not isinstance(value, bool) and abs(value - want) < 1e-9
    else:
        ok = value == want
    assert ok, call + " should return " + repr(want) + ", not " + repr(value) + "."
def _prints(name, args, want):
    value, printed = _call(name, *args)
    assert printed == want, _shown(name, args) + " should print " + repr(want.rstrip("\\n")) + ", not " + repr(printed.rstrip("\\n")) + "."
    assert value is None, _shown(name, args) + " should print its output and return None."
def _calls(name):
    return len(re.findall(r"\\b" + name + r"\\s*\\(", __code__)) - 1
'''

def returns(name, ns, *calls):
    """Check lines that compare each call's returned value with the model's."""
    lines = []
    for args in calls:
        want = ns[name](*args)
        lines.append(f"_returns({name!r}, {args!r}, {want!r})\n")
    return "".join(lines)

def prints(name, ns, *calls):
    """Check lines that compare each call's screen output with the model's."""
    import io, contextlib
    lines = []
    for args in calls:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            ns[name](*args)
        lines.append(f"_prints({name!r}, {args!r}, {buffer.getvalue()!r})\n")
    return "".join(lines)

# ============================================================ 1. Parameters and arguments
greet = '''def greet(name):
    """Display a greeting for name."""
    print("Hello,", name)

greet("Maya")
greet("Noah")
'''
E["ex-greet"] = example(greet)
assert E["ex-greet"]["output"] == "Hello, Maya\nHello, Noah"

# ============================================================ 2. A function can send a result back
cube = '''def cube_volume(side_length):
    """Return the cube's volume."""
    volume = side_length ** 3
    return volume

answer = cube_volume(2)
print(answer)
'''
E["ex-cube"] = example(cube, output=False)
assert out(cube) == "8"
assert out(cube + "first = cube_volume(2)\nsecond = cube_volume(10)\nprint(first, second)\n").endswith("8 1000")

# ============================================================ 3. Argument order and local parameter changes
difference = '''def difference(first, second):
    """Return first minus second."""
    return first - second
'''
E["ex-difference"] = example(difference, output=False)
assert out(difference + "print(difference(20, 6), difference(6, 20))\n") == "14 -14"
double = '''def double(n):
    n = n * 2
    return n

value = 5
result = double(value)
print(value, result)
'''
E["ex-double"] = example(double, output=False)
assert out(double) == "5 10"

# Checkpoint 1
adjust = '''def adjust(amount, step):
    amount = amount + step
    return amount

score = 8
new_score = adjust(score, 3)
print(score, new_score)
'''
assert out(adjust) == "8 11"
E["cp1-predict"] = {"type": "table", "xp": 1, "blanks": {"score": num(8), "new_score": num(11)}}
E["cp1"] = short("Parameters: `amount`, `step`.\n\nArguments: the value `8` from `score`, then `3`.\n\n"
                 "The function changes its own `amount` to `11` and returns it. The program prints `8 11`.",
                 min_chars=20, rows=3, placeholder="Parameters: … Arguments: …")

# ============================================================ 4. Returned values and early returns
square_plus = '''def square(n):
    return n * n

result = square(4) + 1
'''
E["ex-square"] = example(square_plus, output=False)
assert out(square_plus + "print(result)\n") == "17"
magnitude = '''def magnitude(number):
    if number < 0:
        return -number
    return number

print(magnitude(-5))
print(magnitude(3))
'''
E["ex-magnitude"] = example(magnitude, output=False)
assert out(magnitude) == "5\n3"

# ============================================================ 5. Returns in loops and alternative cases
first_digit = '''def first_digit(text):
    for character in text:
        if character in "0123456789":
            return character
    return ""

print(first_digit("Room 204"))
'''
E["ex-first-digit"] = example(first_digit, output=False)
assert out(first_digit) == "2"
score_label = '''def score_label(score):
    if score >= 80:
        return "Excellent"
    if score >= 50:
        return "Pass"
    return "Try again"
'''
E["ex-score-label"] = example(score_label, output=False)

# Checkpoint 2
fee = '''def delivery_fee(total, express):
    """Return the delivery fee."""
    if express:
        return 8
    if total >= 40:
        return 0
    return 4

print(delivery_fee(50, True))
print(delivery_fee(40, False))
print(delivery_fee(20, False))
'''
assert out(fee) == "8\n0\n4"
fee_ns = namespace(fee.split("\nprint(")[0])
FEE_CASES = [(50, True), (40, False), (20, False), (30, True), (40, True), (0, True), (39, False), (0, False), (100, False)]

def fee_case(args):
    want = fee_ns["delivery_fee"](*args)
    return {"name": f"delivery_fee{args} returns {want}", "check": returns("delivery_fee", fee_ns, args)}

E["cp2"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "def delivery_fee(total, express):\n    # Return the delivery fee.\n",
    "cases": [fee_case(args) for args in FEE_CASES],
    "check": FN + '_fn("delivery_fee", "total", "express")\n',
    "answer": b64(fee),
    "answerNote": "Check express delivery first: it applies even when the total reaches 40."}

# ============================================================ 6. Reaching the end gives back None
banner = '''def show_banner(text):
    print("=" * len(text))
    print(text)
    print("=" * len(text))

result = show_banner("Hi")
print(result)
'''
E["ex-banner"] = example(banner)
assert E["ex-banner"]["output"] == "==\nHi\n==\nNone"

# ============================================================ 7. Printing and returning do different jobs
show_square = '''def show_square(n):
    print(n * n)

x = show_square(4)
'''
E["ex-show-square"] = example(show_square, output=False)
assert out(show_square + "print(x)\n") == "16\nNone"
square_y = '''def square(n):
    return n * n

y = square(4)
'''
E["ex-square-y"] = example(square_y, output=False)
assert out(square_y + "print(y + 1)\n") == "17"
assert "TypeError" in run(show_square + "x + 1\n", ok=False)[1]

# ============================================================ 8. Missing-return paths
sign_missing = '''def sign_label(number):
    if number < 0:
        return "negative"

print(sign_label(-2))
print(sign_label(2))
'''
E["ex-sign-missing"] = example(sign_missing)
assert E["ex-sign-missing"]["output"] == "negative\nNone"
sign_fixed = '''def sign_label(number):
    """Return negative or nonnegative."""
    if number < 0:
        return "negative"
    return "nonnegative"
'''
E["ex-sign-fixed"] = example(sign_fixed, output=False)
assert out(sign_fixed + "print(sign_label(-2), sign_label(0), sign_label(2))\n") == "negative nonnegative nonnegative"

# ============================================================ 9. A predicate returns True or False
is_even = '''def is_even(number):
    """Return whether number is even."""
    return number % 2 == 0

if is_even(6):
    print("Even")
'''
E["ex-is-even"] = example(is_even)
assert E["ex-is-even"]["output"] == "Even"
assert out(is_even + "print(is_even(6), is_even(-3), is_even(0))\n").endswith("True False True")

# ============================================================ 10. Boolean results from loops
has_digit = '''def has_digit(text):
    """Return whether text has a digit."""
    for character in text:
        if character in "0123456789":
            return True
    return False
'''
E["ex-has-digit"] = example(has_digit, output=False)
assert out(has_digit + 'print(has_digit("Room 2"), has_digit("Room"), has_digit(""))\n') == "True False False"

# Checkpoint 3
prime = '''def is_prime(number):
    """Return whether number is prime."""
    if number < 2:
        return False
    for divisor in range(2, number):
        if number % divisor == 0:
            return False
    return True
'''
prime_ns = namespace(prime)
PRIME_CASES = [1, 2, 9, 17, -7, 0, 3, 4, 25, 97]
assert [prime_ns["is_prime"](n) for n in (1, 2, 9, 17)] == [False, True, False, True]

def prime_case(n):
    want = prime_ns["is_prime"](n)
    return {"name": f"is_prime({n}) returns {want}", "check": returns("is_prime", prime_ns, (n,))}

E["cp3"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "def is_prime(number):\n    # Return whether number is prime.\n",
    "cases": [prime_case(n) for n in PRIME_CASES],
    "check": FN + '''_fn("is_prime", "number")
assert re.search(r"^\\s*(for|while)\\b", __code__, re.M), "Test possible divisors with a loop."
assert "%" in __code__, "Use % to check divisibility."
''',
    "answer": b64(prime),
    "answerNote": "For `2`, the loop has no iterations. The final return gives `True`. "
                  "For `9`, divisor `3` gives a remainder of zero, so the function returns `False`."}

# ============================================================ Coding Practice
# 1. Inputs and results
E["p1"] = short("The arguments are 6 and 2; the parameters are `width` and `height`. This definition requires two arguments. "
                "One call returns one value, 12.", min_chars=20, rows=3,
                placeholder="Arguments: … Parameters: … Returned value: …")
area = '''def rectangle_area(width, height):
    return width * height

print(rectangle_area(6, 2))
'''
E["p1-call"] = {"type": "code", "xp": 2, "minLines": 4,
    "starter": "def rectangle_area(width, height):\n    return width * height\n\n# Confirm the result with a call.\n",
    "cases": [program_case("Program output", area)],
    "check": FN + '''_fn("rectangle_area", "width", "height")
assert re.search(r"\\brectangle_area\\s*\\(\\s*6\\s*,\\s*2\\s*\\)", __code__), "Call rectangle_area(6, 2) and print the result."
''',
    "answer": b64(area)}
assert E["p1-call"]["cases"][0]["expected"] == "12"

# 2. Money display
money = '''def show_money(amount):
    print(f'${amount:.2f}')

show_money(7.5)
show_money(0)
'''
money_ns = namespace(money.split("\nshow_money(7.5)")[0])
E["p2"] = {"type": "code", "xp": 5, "minLines": 5,
    "starter": "def show_money(amount):\n    # Print the amount with a dollar sign and two decimal places.\n\n# Test with 7.5 and 0.\n",
    "cases": [program_case("Program output", money)],
    "check": FN + '_fn("show_money", "amount")\n' + prints("show_money", money_ns, (3.14159,), (12,))
             + 'assert _calls("show_money") == 2, "Use the same function for both calls: call show_money twice."\n',
    "answer": b64(money),
    "answerNote": "This function's job is output, so its return value is `None`. Each caller uses `show_money(amount)`."}
assert E["p2"]["cases"][0]["expected"] == "$7.50\n$0.00"
E["p2-eur"] = short("To change the currency label, replace the print line with `print(f'EUR {amount:.2f}')`.",
                    min_chars=10, rows=2, placeholder="The line to change and its new version…")

# 3. Letter-to-digit conversion
E["p3-plan"] = short("Start with an empty result. For each character, append the digit for its letter group, or append the unchanged character. "
                     "Return the completed result.", min_chars=30, rows=4, placeholder="Pseudocode, one step per line…")
phone = '''def phone_digits(text):
    result = ''
    for character in text:
        if character in 'ABC':
            result = result + '2'
        elif character in 'DEF':
            result = result + '3'
        elif character in 'GHI':
            result = result + '4'
        elif character in 'JKL':
            result = result + '5'
        elif character in 'MNO':
            result = result + '6'
        elif character in 'PQRS':
            result = result + '7'
        elif character in 'TUV':
            result = result + '8'
        elif character in 'WXYZ':
            result = result + '9'
        else:
            result = result + character
    return result

print('[' + phone_digits('8-CAT') + ']')
print('[' + phone_digits('') + ']')
'''
phone_ns = namespace(phone.split("\nprint(")[0])
E["p3"] = {"type": "code", "xp": 10, "minLines": 22,
    "starter": "def phone_digits(text):\n    # Return text with each letter replaced by its keypad digit.\n\n# Print each result inside [ and ].\n",
    "cases": [program_case("Program output", phone)],
    "check": FN + '_fn("phone_digits", "text")\n'
             + returns("phone_digits", phone_ns, ("8-CAT",), ("",), ("HELLO",), ("PQRS-TUV-WXYZ",), ("1-800-FLOWERS",), ("ADGJMPTW",)),
    "answer": b64(phone)}
assert E["p3"]["cases"][0]["expected"] == "[8-228]\n[]"

# 4. Separated copies
copies = '''def separated_copies(text, count, separator):
    result = ''
    for index in range(count):
        if index > 0:
            result = result + separator
        result = result + text
    return result

print('[' + separated_copies('go', 3, '/') + ']')
print('[' + separated_copies('go', 0, '/') + ']')
print('[' + separated_copies('go', 1, '/') + ']')
'''
copies_ns = namespace(copies.split("\nprint(")[0])
E["p4"] = {"type": "code", "xp": 5, "minLines": 11,
    "starter": "def separated_copies(text, count, separator):\n    # Return count copies with the separator only between copies.\n\n# Print each result inside brackets.\n",
    "cases": [program_case("Program output", copies)],
    "check": FN + '_fn("separated_copies", "text", "count", "separator")\n'
             + returns("separated_copies", copies_ns, ("go", 3, "/"), ("go", 0, "/"), ("go", 1, "/"), ("ab", 2, ", "), ("x", 5, "")),
    "answer": b64(copies),
    "answerNote": "The separator is appended before every copy after the first, so the result has no trailing separator."}
assert E["p4"]["cases"][0]["expected"] == "[go/go/go]\n[]\n[go]"

# 5. Vowel count
vowels = '''def vowel_count(text):
    count = 0
    for character in text:
        if character.lower() in 'aeiou':
            count = count + 1
    return count

print(vowel_count('Blue sky'))
print(vowel_count(''))
print(vowel_count('AEIOU'))
'''
vowels_ns = namespace(vowels.split("\nprint(")[0])
E["p5"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": "def vowel_count(text):\n    # Return the number of vowels in text.\n\n# Print the three results.\n",
    "cases": [program_case("Program output", vowels)],
    "check": FN + '_fn("vowel_count", "text")\n'
             + returns("vowel_count", vowels_ns, ("Blue sky",), ("",), ("AEIOU",), ("Programming",), ("xyz",), ("QUEUE queue",)),
    "answer": b64(vowels),
    "answerNote": "This program takes text as arguments and prints the vowel count for each string. "
                  "The counter starts at zero. Each vowel adds one, and the function returns the count after the loop."}
assert E["p5"]["cases"][0]["expected"] == "2\n0\n5"

# 6. Word count
words = '''def word_count(text):
    count = 0
    in_word = False
    for character in text:
        if character == ' ':
            in_word = False
        elif not in_word:
            count = count + 1
            in_word = True
    return count

print(word_count('red  blue'))
print(word_count(''))
print(word_count('   one   '))
'''
words_ns = namespace(words.split("\nprint(")[0])
E["p6"] = {"type": "code", "xp": 5, "minLines": 13,
    "starter": "def word_count(text):\n    # Return the number of words in text.\n\n# Print the three results.\n",
    "cases": [program_case("Program output", words)],
    "check": FN + '_fn("word_count", "text")\n'
             + 'assert not re.search(r"\\bsplit\\b", __code__), "Do not use split. Count a new word at each non-space character that follows a space or the start of the text."\n'
             + returns("word_count", words_ns, ("red  blue",), ("",), ("   one   ",), ("a b c",), ("   ",), ("one",), (" x  y ",)),
    "answer": b64(words),
    "answerNote": "A new word begins at a non-space character when `in_word` is false."}
assert E["p6"]["cases"][0]["expected"] == "2\n0\n1"

# 7. Interior letter swap
swap = '''def swap_inside(word, first, second):
    result = ''
    for index in range(len(word)):
        if index == first:
            result = result + word[second]
        elif index == second:
            result = result + word[first]
        else:
            result = result + word[index]
    return result

print(swap_inside('planet', 1, 4))
print(swap_inside('abcd', 1, 2))
'''
swap_ns = namespace(swap.split("\nprint(")[0])
E["p7"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": "def swap_inside(word, first, second):\n    # Return word with the characters at first and second exchanged.\n\n# Print the two results.\n",
    "cases": [program_case("Program output", swap)],
    "check": FN + '_fn("swap_inside", "word", "first", "second")\n'
             + returns("swap_inside", swap_ns, ("planet", 1, 4), ("abcd", 1, 2), ("python", 2, 3), ("abcdef", 1, 4), ("letter", 2, 3)),
    "answer": b64(swap),
    "answerNote": "At each selected index, append the character from the other index. Copy every other character unchanged."}
assert E["p7"]["cases"][0]["expected"] == "peanlt\nacbd"

# 8. Solid measurements
solids = '''import math

def sphere_volume(r):
    return 4 * math.pi * r ** 3 / 3

def sphere_area(r):
    return 4 * math.pi * r ** 2

def cylinder_volume(r, h):
    return math.pi * r ** 2 * h

def cylinder_area(r, h):
    return 2 * math.pi * r * (r + h)

def cone_volume(r, h):
    return math.pi * r ** 2 * h / 3

def cone_area(r, h):
    return math.pi * r * (r + (r ** 2 + h ** 2) ** 0.5)

r = float(input())
h = float(input())
print(f'{sphere_volume(r):.2f}')
print(f'{sphere_area(r):.2f}')
print(f'{cylinder_volume(r, h):.2f}')
print(f'{cylinder_area(r, h):.2f}')
print(f'{cone_volume(r, h):.2f}')
print(f'{cone_area(r, h):.2f}')
'''
solids_ns = namespace(solids.split("\nr = float")[0])
SOLID_ONE = [("sphere_volume", ("r",)), ("sphere_area", ("r",))]
SOLID_TWO = [("cylinder_volume", ("r", "h")), ("cylinder_area", ("r", "h")), ("cone_volume", ("r", "h")), ("cone_area", ("r", "h"))]
solid_check = FN + "".join(f'_fn({n!r}, {", ".join(map(repr, p))})\n' for n, p in SOLID_ONE + SOLID_TWO)
solid_check += 'assert re.search(r"\\bmath\\.pi\\b", __code__), "Use math.pi."\n'
for n, _ in SOLID_ONE:
    solid_check += returns(n, solids_ns, (1.0,), (2.5,))
for n, _ in SOLID_TWO:
    solid_check += returns(n, solids_ns, (1.0, 1.0), (2.0, 3.0))
E["p8"] = {"type": "code", "xp": 10, "minLines": 27,
    "starter": ("import math\n\n# Define the six functions here.\n\nr = float(input())\nh = float(input())\n"
                "# Print the six results in order, each to two decimal places.\n"),
    "cases": input_cases(solids, ("Typed 2 and 3", ["2", "3"]), ("Typed 1 and 1", ["1", "1"]), ("Typed 0.5 and 4", ["0.5", "4"]),
                         ("Typed 10 and 2.5", ["10", "2.5"])),
    "check": solid_check,
    "answer": b64(solids),
    "answerNote": "Each function returns one measurement. The caller reads the dimensions once and formats all six results."}
assert E["p8"]["cases"][0]["expected"] == "33.51\n50.27\n37.70\n62.83\n12.57\n35.22"

# 9. Read and return a number
reader = '''def read_number(message):
    return float(input(message + ' '))

length = read_number('Length:')
width = read_number('Width:')
print(length * width)
'''
E["p9"] = {"type": "code", "xp": 5, "minLines": 5,
    "starter": "def read_number(message):\n    # Display message and a space, then return the number typed as a float.\n\n# Read the length and width, then print their product.\n",
    "cases": input_cases(reader, ("Typed 2.5 and 4", ["2.5", "4"]), ("Typed 3 and 3", ["3", "3"]), ("Typed 0.5 and 0.5", ["0.5", "0.5"])),
    "check": FN + '''_f = _fn("read_number", "message")
assert "input" in _f.__code__.co_names and "float" in _f.__code__.co_names, "Read the number with input() and convert it with float() inside read_number."
assert _calls("read_number") == 2, "Call read_number twice: once with Length: and once with Width:."
''',
    "answer": b64(reader),
    "answerNote": "Each call returns the converted input. This output capture shows prompts without typed-input echo; "
                  "an interactive terminal also echoes the user's input."}
assert E["p9"]["cases"][0]["expected"] == "Length: Width: 10.0"

# 10. Pay calculation
pay = '''def weekly_pay(rate, hours):
    if hours <= 35:
        return rate * hours
    return rate * 35 + (hours - 35) * rate * 1.5

def show_pay(name, amount):
    print(f'{name}: ${amount:.2f}')

name = input()
rate = float(input())
hours = float(input())
show_pay(name, weekly_pay(rate, hours))
'''
pay_ns = namespace(pay.split("\nname = input")[0])
E["p10"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": ("def weekly_pay(rate, hours):\n    # Return the pay for the week.\n\ndef show_pay(name, amount):\n"
                "    # Print the name and pay to two decimal places.\n\n# Read a name, rate, and hours, then call both functions.\n"),
    "cases": input_cases(pay, ("Typed Lee, 12, 37", ["Lee", "12", "37"]), ("Typed Sam, 12, 0", ["Sam", "12", "0"]),
                         ("Typed Ana, 20, 35", ["Ana", "20", "35"]), ("Typed Kim, 10, 40", ["Kim", "10", "40"])),
    "check": FN + '_fn("weekly_pay", "rate", "hours")\n_fn("show_pay", "name", "amount")\n'
             + returns("weekly_pay", pay_ns, (12.0, 37.0), (12.0, 0.0), (20.0, 35.0), (10.0, 40.0))
             + prints("show_pay", pay_ns, ("Ana", 3.5), ("Lee", 456.0)),
    "answer": b64(pay),
    "answerNote": "The calculation returns an amount. The output function receives that amount as an argument."}
assert [c["expected"] for c in E["p10"]["cases"][:2]] == ["Lee: $456.00", "Sam: $0.00"]

# 11. Preparation instructions
steps = '''def base_steps():
    print('Fill the container.')
    print('Add the mixture.')

def finish_steps(warm):
    if warm:
        print('Warm the mixture.')
    else:
        print('Leave it cool.')

choice = input()
base_steps()
finish_steps(choice == 'warm')
'''
# __code__ empties string literals, so 'warm' appears there as ''.
WARM_CHECK = (r'''assert re.search(r"\bfinish_steps\s*\(\s*(choice\s*==\s*[\x22\x27]{2}|[\x22\x27]{2}\s*==\s*choice)\s*\)", __code__), "Pass the comparison choice == 'warm' to finish_steps."
''')
steps_ns = namespace(steps.split("\nchoice = input")[0])
E["p11"] = {"type": "code", "xp": 5, "minLines": 13,
    "starter": ("def base_steps():\n    # Print the two base steps.\n\ndef finish_steps(warm):\n    # Print the final instruction.\n\n"
                "# Read warm or cool, then call both functions.\n"),
    "cases": input_cases(steps, ("Typed warm", ["warm"]), ("Typed cool", ["cool"])),
    "check": FN + '_fn("base_steps")\n_fn("finish_steps", "warm")\n'
             + prints("base_steps", steps_ns, ()) + prints("finish_steps", steps_ns, (True,), (False,))
             + WARM_CHECK,
    "answer": b64(steps),
    "answerNote": "Both functions perform output and return `None`; the Boolean argument chooses the final instruction."}
assert [c["expected"] for c in E["p11"]["cases"]] == ["Fill the container.\nAdd the mixture.\nWarm the mixture.",
                                                      "Fill the container.\nAdd the mixture.\nLeave it cool."]

# 12. Viewing angle
angle = '''import math

def view_angle(distance, bottom, height):
    return (math.atan((bottom + height) / distance)
            - math.atan(bottom / distance))

def standard_angle(distance):
    return view_angle(distance, 1, 2)

print(f'{standard_angle(4):.3f}')
print(f'{view_angle(5, 0, 5):.3f}')
'''
angle_ns = namespace(angle.split("\nprint(")[0])
E["p12"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": ("import math\n\ndef view_angle(distance, bottom, height):\n    # Return the viewing angle in radians.\n\n"
                "def standard_angle(distance):\n    # Return the angle for bottom 1 and height 2.\n\n# Print the two results to three decimal places.\n"),
    "cases": [program_case("Program output", angle)],
    "check": FN + '''_fn("view_angle", "distance", "bottom", "height")
_s = _fn("standard_angle", "distance")
assert "view_angle" in _s.__code__.co_names, "Let standard_angle call view_angle with bottom 1 and height 2."
''' + returns("view_angle", angle_ns, (5, 0, 5), (2, 0.5, 1.5), (10, 3, 1)) + returns("standard_angle", angle_ns, (4,), (1,), (7.5,)),
    "answer": b64(angle),
    "answerNote": "The general function receives every varying measurement. The second function supplies fixed screen dimensions."}
assert E["p12"]["cases"][0]["expected"] == "0.399\n0.785"

# 13. Lens calculation
lens = '''def focal_length(n, radius1, radius2, thickness):
    q = (n - 1) * (1 / radius1 - 1 / radius2
        + (n - 1) * thickness / (n * radius1 * radius2))
    return 1 / q

print(f'{focal_length(1.5, 10, -10, 0):.3f}')
print(f'{focal_length(1.5, 10, -10, 2):.3f}')
'''
lens_ns = namespace(lens.split("\nprint(")[0])
E["p13"] = {"type": "code", "xp": 5, "minLines": 7,
    "starter": "def focal_length(n, radius1, radius2, thickness):\n    # Compute q, then return 1 / q.\n\n# Print the two results to three decimal places.\n",
    "cases": [program_case("Program output", lens)],
    "check": FN + '_fn("focal_length", "n", "radius1", "radius2", "thickness")\n'
             + returns("focal_length", lens_ns, (1.5, 10, -10, 0), (1.5, 10, -10, 2), (1.6, 20, -15, 1), (1.5, 10, 20, 0.5)),
    "answer": b64(lens),
    "answerNote": "Compute the reciprocal value q first, then return its reciprocal. The input rules exclude division by zero."}
assert E["p13"]["cases"][0]["expected"] == "10.000\n10.345"

# 14. Tapered container
container = '''import math

def container_volume(r1, r2, h):
    return math.pi * h * (r1 ** 2 + r2 ** 2 + r1 * r2) / 3

def container_area(r1, r2, h):
    slant = ((r2 - r1) ** 2 + h ** 2) ** 0.5
    return math.pi * (r1 + r2) * slant + math.pi * r1 ** 2

print(f'{container_volume(1, 1, 2):.3f}')
print(f'{container_area(1, 1, 2):.3f}')
'''
container_ns = namespace(container.split("\nprint(")[0])
E["p14"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": ("import math\n\ndef container_volume(r1, r2, h):\n    # Return the volume.\n\ndef container_area(r1, r2, h):\n"
                "    # Return the area of the side and bottom.\n\n# Print both results to three decimal places.\n"),
    "cases": [program_case("Program output", container)],
    "check": FN + '_fn("container_volume", "r1", "r2", "h")\n_fn("container_area", "r1", "r2", "h")\n'
             + returns("container_volume", container_ns, (1, 1, 2), (1, 2, 3), (0.5, 1.5, 1))
             + returns("container_area", container_ns, (1, 1, 2), (1, 2, 3), (0.5, 1.5, 1)),
    "answer": b64(container),
    "answerNote": "The area function computes the slant length from the vertical height and the difference between the radii."}
assert E["p14"]["cases"][0]["expected"] == "6.283\n15.708"

# 15. Grid border
grid = '''def print_border_grid(width, height, border):
    for row in range(height):
        line = ''
        for column in range(width):
            if (row == 0 or row == height - 1
                    or column == 0 or column == width - 1):
                line = line + border
            else:
                line = line + '.'
        print(line)

print_border_grid(5, 3, '#')
print_border_grid(2, 2, '*')
'''
grid_ns = namespace(grid.split("\nprint_border_grid(5")[0])
E["p15"] = {"type": "code", "xp": 10, "minLines": 13,
    "starter": "def print_border_grid(width, height, border):\n    # Print the grid, one row per line.\n\n# Test (5, 3, '#') and (2, 2, '*').\n",
    "cases": [program_case("Program output", grid)],
    "check": FN + '_fn("print_border_grid", "width", "height", "border")\n'
             + prints("print_border_grid", grid_ns, (4, 4, "+"), (3, 2, "@"), (6, 5, "#")),
    "answer": b64(grid),
    "answerNote": "The row and column tests identify the outside cells. This output-only function needs no value-producing return."}
assert E["p15"]["cases"][0]["expected"] == "#####\n#...#\n#####\n**\n**"

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-18",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 18 Workbook",
    "subtitle": "Parameters and return values",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-18/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
