"""Build workbooks/lecture-20/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. The source is the kit's
LECTURE_20_SHARED_CONTENT.tex; model answers follow its \\solution{...}
text. Run from anywhere:

    python3 workbooks/lecture-20/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-20
"""
import base64, contextlib, io, itertools, json, re, subprocess, sys, pathlib

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

def accept(*values, width="8rem", placeholder="answer"):
    return {"accept": list(values), "placeholder": placeholder, "width": width}

def short(answer, xp=2, min_chars=15, rows=3, placeholder="Write your answer in your own words…"):
    return {"type": "short", "xp": xp, "minChars": min_chars, "rows": rows, "placeholder": placeholder, "answer": b64(answer)}

def namespace(code):
    ns = {"__name__": "lecture20"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    return ns

def name_list(*names):
    """Accepted spellings of a list of names in any order."""
    seps = [", ", ",", " ", " and ", ", and "]
    return [sep.join(p) for p in itertools.permutations(names) for sep in seps]

E = {}

# ---------------------------------------------------------------- checks shared by the coding tasks
# A check runs after the student's program in the same namespace (a copy of it).
# `_fn` finds a function the program defined and checks its parameters. `_call`
# calls it with its output captured, so the test call does not add to the
# program's own output. `_guard` looks for the standard guard as the last
# statement of the file. `_defs` lists the functions defined at the top level.
FN = '''import types, io, contextlib, re, ast
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
    value, printed = _call(name, *args)
    call = _shown(name, args)
    if value is None:
        raise AssertionError(call + " returned None. Send the result back with return.")
    if isinstance(want, bool):
        ok = value is want
    elif isinstance(want, (int, float)):
        ok = isinstance(value, (int, float)) and not isinstance(value, bool) and abs(value - want) <= 1e-9 * max(1, abs(want))
    else:
        ok = value == want and type(value) is type(want)
    assert ok, call + " should return " + repr(want) + ", not " + repr(value) + "."
def _guard():
    _tree = ast.parse(__source__)
    _last = _tree.body[-1] if _tree.body else None
    _ok = False
    if isinstance(_last, ast.If) and not _last.orelse and isinstance(_last.test, ast.Compare):
        _sides = [_last.test.left] + list(_last.test.comparators)
        _names = [s.id for s in _sides if isinstance(s, ast.Name)]
        _texts = [s.value for s in _sides if isinstance(s, ast.Constant)]
        _call_main = (len(_last.body) == 1 and isinstance(_last.body[0], ast.Expr) and isinstance(_last.body[0].value, ast.Call)
                      and isinstance(_last.body[0].value.func, ast.Name) and _last.body[0].value.func.id == "main"
                      and not _last.body[0].value.args and not _last.body[0].value.keywords)
        _ok = (len(_sides) == 2 and isinstance(_last.test.ops[0], ast.Eq) and _names == ["__name__"]
               and _texts == ["__main__"] and _call_main)
    assert _ok, "End the file with the standard guard: if __name__ == '__main__': followed by an indented main()."
def _body(name):
    for node in ast.parse(__source__).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return list(ast.walk(node))
    return []
def _calls_in(name, callee):
    return [n for n in _body(name) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == callee]
def _defs():
    return [n for n in ast.parse(__source__).body if isinstance(n, ast.FunctionDef)]
def _uses(node, *names):
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in names for n in ast.walk(node))
def _constant(value, label):
    _hits = [k for k, v in globals().items() if k.isupper() and isinstance(v, (int, float)) and not isinstance(v, bool)
             and abs(v - value) <= 1e-12 * max(1, abs(value))]
    assert _hits, "Store the " + label + " (" + repr(value) + ") in a named constant with an uppercase name."
'''

def returns(name, ns, *calls):
    """Check lines that compare each call's returned value with the model's."""
    return "".join(f"_returns({name!r}, {args!r}, {ns[name](*args)!r})\n" for args in calls)

def pattern_case(name, code, inputs, regex, what, prefix=""):
    """Check-only case: any prompts are accepted. The values that match `regex`
    in what the program prints must equal the model's, in order."""
    want = re.findall(regex, run_with_prompts(code, inputs))
    check = f'''_want = {want!r}
_got = re.findall({regex!r}, __stdout__)
_said = ", ".join(repr(_v) for _v in _got) or "nothing"
if _want:
    assert _got == _want, {prefix!r} + "Print the {what} " + ", ".join(repr(_v) for _v in _want) + " in that order, not " + _said + "."
else:
    assert not _got, {prefix!r} + "Print no {what} for this input, not " + _said + "."
'''
    return {"name": name, "inputs": list(inputs), "check": check}

# ============================================================ 1. Repeated work and reusable functions
age = '''age = int(input("Age: "))
while age < 0 or age > 120:
    print("Out of range")
    age = int(input("Age: "))
'''
tickets = '''count = int(input("Tickets: "))
while count < 1 or count > 10:
    print("Out of range")
    count = int(input("Tickets: "))
'''
E["ex-age"] = example(age, output=False)
E["ex-tickets"] = example(tickets, output=False)
assert run_with_prompts(age, ["130", "-1", "120"]) == "Age: Out of range\nAge: Out of range\nAge: "
assert run_with_prompts(tickets, ["0", "11", "1"]) == "Tickets: Out of range\nTickets: Out of range\nTickets: "

reader_def = '''def read_int_between(prompt, low, high):
    value = int(input(prompt))
    while value < low or value > high:
        print("Out of range")
        value = int(input(prompt))
    return value
'''
reader = reader_def + '''
age = read_int_between("Age: ", 0, 120)
quantity = read_int_between(
    "Tickets: ", 1, 10)
'''
E["ex-reader"] = example(reader, output=False)
assert run_with_prompts(reader, ["121", "0", "11", "10"]) == "Age: Out of range\nAge: Tickets: Out of range\nTickets: "

# ============================================================ 2. Parameters expose a calculation's inputs
hidden = '''price = 12
quantity = 3

def line_total():
    return price * quantity
'''
supplied = '''def line_total(price, quantity):
    return price * quantity
'''
E["ex-hidden"] = example(hidden, output=False)
E["ex-supplied"] = example(supplied, output=False)
assert namespace(hidden)["line_total"]() == 36
assert namespace(supplied)["line_total"](12, 3) == 36 and namespace(supplied)["line_total"](5, 2) == 10

# ============================================================ 3. Stepwise refinement and top-down design
# The main() outline is shown as static code: run alone, it stops at the first
# helper call with NameError, because the helpers are written in Section 4.
outline = '''def main():
    age = read_int_between("Age: ", 0, 120)
    quantity = read_int_between(
        "Tickets: ", 1, 10)
    total = ticket_total(age, quantity)
    show_booking(quantity, total)

if __name__ == "__main__":
    main()
'''
assert "NameError" in run(outline, ok=False)[1]

# ============================================================ 4. Refining and testing the helpers
ticket_total = '''def ticket_total(age, quantity):
    if age < 13:
        unit_price = 8
    else:
        unit_price = 12
    return unit_price * quantity
'''
show_booking = '''def show_booking(quantity, total):
    print("Tickets:", quantity)
    print("Total:", total)
'''
E["ex-ticket-total"] = example(ticket_total, output=False)
E["ex-show-booking"] = example(show_booking, output=False)
assert namespace(ticket_total)["ticket_total"](12, 2) == 16 and namespace(ticket_total)["ticket_total"](13, 2) == 24
assert out(show_booking + "show_booking(2, 16)\n") == "Tickets: 2\nTotal: 16"
# The whole booking program runs once the helpers exist.
assert run_with_prompts(reader_def + ticket_total + show_booking + outline, ["12", "2"]) == "Age: Tickets: Tickets: 2\nTotal: 16"

# Checkpoint 1
cp1_starter = reader_def + '''
def shipping_fee(weight):
    pass

def main():
    pass
'''
cp1_answer = reader_def + '''
def shipping_fee(weight):
    if weight <= 2:
        return 5
    return 5 + 2 * (weight - 2)

def main():
    weight = read_int_between(
        "Weight (kg): ", 1, 20)
    print("Fee:", shipping_fee(weight))

if __name__ == "__main__":
    main()
'''
cp1_ns = namespace(cp1_answer)
assert [cp1_ns["shipping_fee"](w) for w in (1, 2, 3)] == [5, 5, 7]
E["cp1-fees"] = {"type": "table", "xp": 1, "blanks": {
    "f1": accept("5", placeholder="fee", width="5rem"),
    "f2": accept("5", placeholder="fee", width="5rem"),
    "f3": accept("7", placeholder="fee", width="5rem"),
}}

def fee_case(name, inputs):
    """Check-only case: any prompt is accepted; the last printed line must end with the fee."""
    fee = str(cp1_ns["shipping_fee"](int(inputs[-1])))
    check = f'''_lines = __stdout__.rstrip("\\n").split("\\n")
assert re.search(r"(^|\\D){fee}\\s*$", _lines[-1]), "With the weights {', '.join(inputs)} typed, the last line printed should end with the fee {fee}, not " + repr(_lines[-1]) + "."
'''
    return {"name": name, "inputs": list(inputs), "check": check}

E["cp1"] = {"type": "code", "xp": 5, "minLines": 18,
    "starter": cp1_starter,
    "cases": [fee_case("Typed 1", ["1"]), fee_case("Typed 3", ["3"]), fee_case("Typed 0, 21, then 3", ["0", "21", "3"]),
              fee_case("Typed 20", ["20"])],
    "check": FN + '''_f = _fn("shipping_fee", "weight")
_fn("main")
_fn("read_int_between", "prompt", "low", "high")
assert not _uses(next(d for d in _defs() if d.name == "shipping_fee"), "print", "input"), "Keep the fee calculation separate from prompting and printing: shipping_fee only returns the fee."
''' + returns("shipping_fee", cp1_ns, *[(w,) for w in range(1, 21)]) + '''_c = _calls_in("main", "read_int_between")
assert _c, "In main, read the weight with read_int_between."
assert any(len(c.args) == 3 and [getattr(a, "value", None) for a in c.args[1:]] == [1, 20] for c in _c), "Call read_int_between with the limits 1 and 20."
assert _calls_in("main", "shipping_fee"), "In main, call shipping_fee(weight) and print the fee it returns."
_guard()
''',
    "answer": b64(cp1_answer),
    "answerNote": "`shipping_fee(1)` and `shipping_fee(2)` return `5`. `shipping_fee(3)` returns `5 + 2 * 1`, which is `7`."}

# ============================================================ 5. Local names and returned values
area = '''def rectangle_area(width, height):
    area = width * height
    return area

def main():
    result = rectangle_area(3, 4)
    print(result)

if __name__ == "__main__":
    main()
'''
# The workbook states the stored value in the prose; the console starts empty.
E["ex-area"] = example(area, output=False)
assert out(area) == "12"
# compute()/temp is shown as static code: it raises NameError after printing 42.
compute = '''def compute():
    temp = 42
    return temp

def main():
    result = compute()
    print(result)
    print(temp)

if __name__ == "__main__":
    main()
'''
stdout, stderr = run(compute, ok=False)
assert stdout == "42" and "NameError" in stderr

# ============================================================ 6. Separate calls and assignment paths
double_square = '''def double(number):
    temp = number * 2
    return temp

def square(number):
    temp = number * number
    return temp

def main():
    print(double(3), square(3))

if __name__ == "__main__":
    main()
'''
# The workbook gives this output in the prose, so the console starts empty.
E["ex-double-square"] = example(double_square, output=False)
assert out(double_square) == "6 9"
loop_scope = '''def main():
    for number in range(1, 4):
        square = number * number
    print(number, square)

if __name__ == "__main__":
    main()
'''
E["ex-loop-scope"] = example(loop_scope)
assert E["ex-loop-scope"]["output"] == "3 9"

# Checkpoint 2
cp2_program = '''def increase(number):
    amount = number + 2
    return amount

def main():
    amount = 5
    answer = increase(amount)
    print(amount, answer)
    print(number)

if __name__ == "__main__":
    main()
'''
stdout, stderr = run(cp2_program, ok=False)
assert stdout == "5 7" and "NameError" in stderr
cp2_answer = cp2_program.replace("    print(number)\n", "    print(answer)\n")
assert out(cp2_answer) == "5 7\n7"
E["cp2-first"] = {"type": "table", "xp": 1, "blanks": {"line": accept("5 7", placeholder="printed line")}}
E["cp2-why"] = short("Then `NameError`: `number` belongs to `increase`, so `main` cannot read it.",
                     min_chars=20, rows=3, placeholder="Why the final print fails…")
E["cp2-locals"] = {"type": "table", "xp": 1, "blanks": {
    "inc": {**accept(*name_list("number", "amount"), placeholder="names", width="11rem"), "show": "number, amount"},
    "main": {**accept(*name_list("amount", "answer"), placeholder="names", width="11rem"), "show": "amount, answer"},
}}
E["cp2"] = {"type": "code", "xp": 2, "minLines": 12,
    "starter": cp2_program,
    "cases": [{"name": "Program output", "expected": out(cp2_answer)}],
    "check": FN + '''_fn("increase", "number")
_fn("main")
assert not any(isinstance(n, ast.Name) and n.id == "number" for n in _body("main")), "Do not use the name number in main. It belongs to increase."
assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print" and len(n.args) == 1
           and isinstance(n.args[0], ast.Name) and n.args[0].id == "answer" for n in _body("main")), "Replace the final print with print(answer)."
''',
    "answer": b64(cp2_answer),
    "answerNote": "The helper's `amount` becomes `7`. The caller's `amount` stays `5`. The return gives the caller the value stored in `answer`."}

# ============================================================ 7. Reading a global name
discount = '''discount = 0.1

def discounted_price(price):
    return price * (1 - discount)

def main():
    print(discounted_price(20))

if __name__ == "__main__":
    main()
'''
# The workbook gives this output in the prose, so the console starts empty.
E["ex-discount"] = example(discount, output=False)
assert out(discount) == "18.0"

# ============================================================ 8. Shadowing and assignment
shadow = '''total = 100

def show_total(total):
    print(total)

def main():
    show_total(5)
    print(total)

if __name__ == "__main__":
    main()
'''
# The workbook gives this output in the prose, so the console starts empty.
E["ex-shadow"] = example(shadow, output=False)
assert out(shadow) == "5\n100"
# increment()/count is shown as static code with the error name as its output.
unbound = '''count = 0

def increment():
    count = count + 1

def main():
    increment()

if __name__ == "__main__":
    main()
'''
assert "UnboundLocalError" in run(unbound, ok=False)[1]

# ============================================================ 9. Explicit input and a return
explicit = '''def increment(count):
    return count + 1

def main():
    count = 0
    count = increment(count)
    print(count)

if __name__ == "__main__":
    main()
'''
# The workbook gives this output in the prose, so the console starts empty.
E["ex-explicit"] = example(explicit, output=False)
assert out(explicit) == "1"
assert namespace(explicit)["increment"](10) == 11

# ============================================================ 10. Fixed constants
seconds = '''SECONDS_PER_MINUTE = 60

def to_seconds(minutes):
    return minutes * SECONDS_PER_MINUTE

def main():
    print(to_seconds(3))

if __name__ == "__main__":
    main()
'''
# The workbook gives this output in the prose, so the console starts empty.
E["ex-seconds"] = example(seconds, output=False)
assert out(seconds) == "180"

# Checkpoint 3
cp3_program = '''TICKET_PRICE = 8
quantity = 2

def booking_total():
    return quantity * TICKET_PRICE

def main():
    quantity = 4
    print(booking_total())
    print(quantity)

if __name__ == "__main__":
    main()
'''
assert out(cp3_program) == "16\n4"
cp3_answer = '''TICKET_PRICE = 8
def booking_total(quantity):
    return quantity * TICKET_PRICE

def main():
    quantity = 4
    print(booking_total(quantity))
    print(quantity)
if __name__ == "__main__":
    main()
'''
assert out(cp3_answer) == "32\n4"
E["cp3-predict"] = {"type": "table", "xp": 1, "blanks": {
    "l1": accept("16", placeholder="output", width="5rem"),
    "l2": accept("4", placeholder="output", width="5rem"),
}}
E["cp3-why"] = short("The helper reads the global `quantity=2`. It cannot see `main`'s local `quantity=4`.",
                     min_chars=20, rows=3, placeholder="Why the helper uses a quantity of 2…")
E["cp3"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": cp3_program,
    "cases": [{"name": "Program output", "expected": out(cp3_answer)}],
    "check": FN + '''_fn("booking_total", "quantity")
_fn("main")
_top = [t.id for n in ast.parse(__source__).body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)]
assert "quantity" not in _top, "Remove the changing global quantity. main chooses the quantity and passes it to the helper."
assert globals().get("TICKET_PRICE") == 8, "Keep the constant TICKET_PRICE = 8."
_c = _calls_in("main", "booking_total")
assert _c and all(len(c.args) == 1 for c in _c), "In main, pass the quantity to the helper: booking_total(quantity)."
''' + "".join(f"_returns('booking_total', ({q},), {8 * q})\n" for q in (0, 1, 3, 4, 10)),
    "answer": b64(cp3_answer),
    "answerNote": "The revised program prints `32`, then `4`. Keep `TICKET_PRICE` as a fixed constant. "
                  "Remove the changing global quantity and pass the caller's value explicitly."}
E["cp3-constant"] = {"type": "table", "xp": 1, "blanks": {
    "name": {**accept("TICKET_PRICE", placeholder="name", width="10rem"), "caseSensitive": True}}}

# ============================================================ Coding Practice
# 1. Scope trace
scope_trace = '''value = 12

def shifted(value):
    result = value + 3
    return result

print(shifted(5))
print(value)
'''
assert out(scope_trace) == "8\n12"
E["p1-output"] = {"type": "table", "xp": 1, "blanks": {"l1": accept("8", placeholder="output", width="5rem"),
                                                         "l2": accept("12", placeholder="output", width="5rem")}}
E["p1"] = short("The top-level `value` is global in the module. The parameter `value` and local `result` belong to `shifted`; "
                "their scope is its body. The parameter shadows the global inside the helper.",
                min_chars=40, rows=4, placeholder="Each use of value, and result: global or parameter or local, and its scope…")

# 2. Refine a word report
E["p2"] = short("High-level steps: start both counts at zero; read and process words until a blank line; display both counts.\n\n"
                "Refine processing one word: add one to the word count, compare its length with the longest length, "
                "update that length when larger, then read again.\n\n"
                "If the first line is blank, skip processing and print zero for both results.",
                min_chars=60, rows=7, placeholder="High-level steps… Processing one word… When the first line is blank…")

# 3. Parameter reassignment
exchange = '''def exchange(left, right):
    saved = left
    left = right
    right = saved

def main():
    first = 6
    second = 9
    exchange(first, second)
    print(first, second)

main()
'''
assert out(exchange) == "6 9"
E["p3-output"] = {"type": "table", "xp": 1, "blanks": {"out": accept("6 9", placeholder="output", width="6rem")}}
E["p3"] = short("It prints `6 9`. Assignments in `exchange` change its local parameter bindings. "
                "The caller's `first` and `second` keep their values.",
                min_chars=30, rows=4, placeholder="Why changing the parameters does or does not change the caller's variables…")

# 4. Leap-year helper
leap = '''def is_leap_year(year):
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    if year % 4 == 0:
        return True
    return False

print(is_leap_year(2400))
print(is_leap_year(2100))
print(is_leap_year(2028))
print(is_leap_year(2027))
'''
leap_ns = namespace(leap)
E["p4"] = {"type": "code", "xp": 5, "minLines": 14,
    "starter": "def is_leap_year(year):\n    pass\n",
    "cases": [{"name": "Program output", "expected": out(leap)}],
    "check": FN + '''_fn("is_leap_year", "year")
_nodes = _body("is_leap_year")
assert sum(isinstance(n, ast.If) for n in _nodes) >= 3, "Use separate if statements, one for each divisibility rule."
assert sum(isinstance(n, ast.Return) for n in _nodes) >= 3, "Use early returns: each if statement returns its answer."
''' + returns("is_leap_year", leap_ns, *[(y,) for y in (1, 4, 100, 400, 1600, 1700, 1800, 1900, 2000, 2001, 2004, 2024, 2027, 2028, 2100, 2400)]),
    "answer": b64(leap),
    "answerNote": "Test the most specific divisibility rule first. Each return finishes the call."}
assert E["p4"]["cases"][0]["expected"] == "True\nFalse\nTrue\nFalse"

# 5. Reusable numeral helper
roman = '''def roman_digit(digit, one, five, ten):
    if digit < 4:
        return one * digit
    if digit == 4:
        return one + five
    if digit < 9:
        return five + one * (digit - 5)
    return one + ten

def roman_number(number):
    tens = roman_digit(number // 10, 'X', 'L', 'C')
    ones = roman_digit(number % 10, 'I', 'V', 'X')
    return tens + ones

print(roman_number(44))
print(roman_number(9))
print(roman_number(80))
'''
roman_ns = namespace(roman)
E["p5"] = {"type": "code", "xp": 10, "minLines": 18,
    "starter": "def roman_digit(digit, one, five, ten):\n    pass\n\ndef roman_number(number):\n    pass\n",
    "cases": [{"name": "Program output", "expected": out(roman)}],
    "check": FN + '''_fn("roman_digit", "digit", "one", "five", "ten")
_fn("roman_number", "number")
assert "roman_digit" in globals()["roman_number"].__code__.co_names, "Call roman_digit from roman_number for the tens and the ones."
''' + returns("roman_digit", roman_ns, *[(d, "I", "V", "X") for d in range(10)], *[(d, "X", "L", "C") for d in range(10)])
      + returns("roman_number", roman_ns, *[(n,) for n in range(1, 100)]),
    "answer": b64(roman),
    "answerNote": "The same helper handles both positions because the symbols arrive as parameters."}
assert E["p5"]["cases"][0]["expected"] == "XLIV\nIX\nLXXX"

# 6. Pay report
pay = '''def pay_amount(rate, hours):
    if hours <= 35:
        return rate * hours
    return rate * 35 + rate * 2 * (hours - 35)

def show_pay(name, amount):
    print('Worker:', name)
    print(f'Pay: ${amount:.2f}')

def main():
    name = input()
    rate = float(input())
    hours = float(input())
    show_pay(name, pay_amount(rate, hours))

if __name__ == '__main__':
    main()
'''
assert run_with_prompts(pay, ["Sam", "12", "38"]) == "Worker: Sam\nPay: $492.00"
pay_ns = namespace(pay)

def pay_case(name, inputs):
    amount = f"{pay_ns['pay_amount'](float(inputs[1]), float(inputs[2])):.2f}"
    check = f'''assert {inputs[0]!r} in __stdout__, "Print the worker's name, {inputs[0]}."
assert re.search(r"(^|[^0-9.]){re.escape(amount)}(?![0-9])", __stdout__), "For rate {inputs[1]} and {inputs[2]} hours, print the pay to two decimal places: {amount}."
'''
    return {"name": name, "inputs": list(inputs), "check": check}

E["p6"] = {"type": "code", "xp": 10, "minLines": 18,
    "starter": "",
    "cases": [pay_case("Sam, rate 12, 38 hours", ["Sam", "12", "38"]), pay_case("Sam, rate 12, 0 hours", ["Sam", "12", "0"]),
              pay_case("Ana, rate 20, 35 hours", ["Ana", "20", "35"]), pay_case("Kim, rate 10, 40 hours", ["Kim", "10", "40"]),
              pay_case("Lee, rate 12.5, 36 hours", ["Lee", "12.5", "36"])],
    "check": FN + '''_fn("main")
_helpers = [d for d in _defs() if d.name != "main"]
assert any(not _uses(d, "print", "input") and any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(d)) for d in _helpers), "Write a pay calculation that returns the pay without reading input or printing."
assert any(_uses(d, "print") for d in _helpers), "Write a display helper that prints the name and the pay."
''',
    "answer": b64(pay),
    "answerNote": "The calculation can be tested without reading input or printing a report. For Sam, rate 12 and 38 hours, the model prints "
                  "`Worker: Sam` and `Pay: $492.00`."}

# 7. Digit-bar report
bars = '''def digit_bars(digit):
    if digit == 0:
        return '||...'
    if digit == 1:
        return '...||'
    if digit == 2:
        return '..|.|'
    if digit == 3:
        return '..||.'
    if digit == 4:
        return '.|..|'
    if digit == 5:
        return '.|.|.'
    if digit == 6:
        return '.||..'
    if digit == 7:
        return '|...|'
    if digit == 8:
        return '|..|.'
    return '|.|..'

def check_digit(code):
    total = 0
    for ch in code:
        total = total + int(ch)
    return (10 - total % 10) % 10

def encode(code):
    result = '|'
    for ch in code:
        result = result + digit_bars(int(ch))
    result = result + digit_bars(check_digit(code))
    return result + '|'

print(encode('00000'))
print(encode('12345'))
'''
bars_ns = namespace(bars)
CODES = ["00000", "12345", "99999", "01234", "56789", "00019", "10000", "55555"]
E["p7"] = {"type": "code", "xp": 10, "minLines": 30,
    "starter": "",
    "cases": [{"name": "Program output", "expected": out(bars)}],
    "check": FN + '''_fn("digit_bars", "digit")
_fn("check_digit", "code")
_fn("encode", "code")
assert "digit_bars" in globals()["encode"].__code__.co_names, "Build the encoding in encode by calling digit_bars for each digit."
''' + returns("digit_bars", bars_ns, *[(d,) for d in range(10)])
      + returns("check_digit", bars_ns, *[(c,) for c in CODES])
      + returns("encode", bars_ns, *[(c,) for c in CODES]),
    "answer": b64(bars),
    "answerNote": "Each digit uses the same helper. The second remainder makes the check digit zero when the digit sum is already a multiple of ten."}
assert E["p7"]["cases"][0]["expected"] == "|||...||...||...||...||...||...|\n|...||..|.|..||..|..|.|.|..|.|.|"

# 8. Grant calculation
grant = '''def grant(income, children):
    if income < 18000:
        return 1200 * children
    if income < 28000:
        if children >= 2:
            return 900 * children
        return 0
    if income <= 36000 and children >= 3:
        return 500 * children
    return 0

def main():
    income = float(input())
    while income != -1:
        children = int(input())
        print(f'{grant(income, children):.2f}')
        income = float(input())

if __name__ == '__main__':
    main()
'''
grant_ns = namespace(grant)
MONEY = r"(?<![0-9.])[0-9]+\.[0-9]{2}(?![0-9])"
GRANT_CALLS = [(0, 0), (17999, 1), (17000, 3), (18000, 1), (18000, 2), (27999, 2), (28000, 2), (28000, 3), (36000, 3),
               (36000, 2), (36001, 3), (50000, 5), (10000.5, 2)]
E["p8"] = {"type": "code", "xp": 10, "minLines": 20,
    "starter": "",
    "cases": [pattern_case("Incomes 17000, 18000, 28000, 36001 with three children, then -1",
                           grant, ["17000", "3", "18000", "3", "28000", "3", "36001", "3", "-1"], MONEY, "grants"),
              pattern_case("The sentinel -1 first", grant, ["-1"], MONEY, "grants", "With -1 first, the program reads no child count. "),
              pattern_case("Incomes 27999 with 1 child, 27999 with 2, 36000 with 4, then -1",
                           grant, ["27999", "1", "27999", "2", "36000", "4", "-1"], MONEY, "grants")],
    "check": FN + '_fn("grant", "income", "children")\n_fn("main")\n' + returns("grant", grant_ns, *GRANT_CALLS),
    "answer": b64(grant),
    "answerNote": "The ordered conditions handle each income boundary. The sentinel is checked before reading a child count. "
                  "The test prints `3600.00`, `2700.00`, `1500.00`, and `0.00`."}
assert E["p8"]["cases"][0]["check"].startswith("_want = ['3600.00', '2700.00', '1500.00', '0.00']")
assert E["p8"]["cases"][1]["check"].startswith("_want = []")

# 9. Password confirmation
password = '''def password_ok(text):
    upper = False
    lower = False
    digit = False
    for ch in text:
        if 'A' <= ch <= 'Z':
            upper = True
        if 'a' <= ch <= 'z':
            lower = True
        if '0' <= ch <= '9':
            digit = True
    return len(text) >= 9 and upper and lower and digit

def main():
    password = input()
    confirmation = input()
    while password != confirmation or not password_ok(password):
        print('Try again.')
        password = input()
        confirmation = input()
    print('Accepted.')

if __name__ == '__main__':
    main()
'''
pw_ns = namespace(password)
PW = r"Try again\.|Accepted\."
PW_TESTS = ["abc", "Abcdefgh2", "abcdefgh2", "ABCDEFGH2", "Abcdefghi", "Abcdefg2", "Abcdefgh2!", "A1bcdefgh", "123456789aB", "", "Ab1Ab1Ab1"]
PW_WANT = [pw_ns["password_ok"](t) for t in PW_TESTS]
E["p9"] = {"type": "code", "xp": 10, "minLines": 24,
    "starter": "",
    "cases": [pattern_case("abc and abc, then Abcdefgh2 and Abcdefgh2", password, ["abc", "abc", "Abcdefgh2", "Abcdefgh2"], PW, "messages"),
              pattern_case("Abcdefgh2 and Abcdefgh2", password, ["Abcdefgh2", "Abcdefgh2"], PW, "messages"),
              pattern_case("Abcdefgh2 and Abcdefgh3, then Abcdefgh2 and Abcdefgh2", password,
                           ["Abcdefgh2", "Abcdefgh3", "Abcdefgh2", "Abcdefgh2"], PW, "messages", "A pair that does not match is rejected. "),
              pattern_case("abcdefgh2 twice, Short1A twice, then Abcdefgh22 twice", password,
                           ["abcdefgh2", "abcdefgh2", "Short1A", "Short1A", "Abcdefgh22", "Abcdefgh22"], PW, "messages")],
    "check": FN + f'''_fn("main")
_tests = {PW_TESTS!r}
_want = {PW_WANT!r}
_ok = False
for _d in _defs():
    _f = globals().get(_d.name)
    if _d.name == "main" or not isinstance(_f, types.FunctionType) or _f.__code__.co_argcount != 1:
        continue
    try:
        _got = [_call(_d.name, _t)[0] for _t in _tests]
    except Exception:
        continue
    if all(_g is _w for _g, _w in zip(_got, _want)):
        _ok = True
assert _ok, "Write a Boolean helper with one parameter that returns True when a password passes all four rules and False otherwise."
''',
    "answer": b64(password),
    "answerNote": "The rule helper has one visible input. The loop also checks that the two entries match."}
assert E["p9"]["cases"][0]["check"].startswith("_want = ['Try again.', 'Accepted.']")

# 10. Wire calculation
wire = '''import math

COPPER_RESISTIVITY = 1.678e-8
ALUMINIUM_RESISTIVITY = 2.82e-8

def diameter_metres(gauge):
    return 0.127 * 92 ** ((36 - gauge) / 39) / 1000

def resistance(length, gauge, resistivity):
    diameter = diameter_metres(gauge)
    return 4 * resistivity * length / (math.pi * diameter ** 2)

def copper_resistance(length, gauge):
    return resistance(length, gauge, COPPER_RESISTIVITY)

def aluminium_resistance(length, gauge):
    return resistance(length, gauge, ALUMINIUM_RESISTIVITY)

print(f'{copper_resistance(3, 18):.6f}')
print(f'{aluminium_resistance(3, 18):.6f}')
'''
wire_ns = namespace(wire)
E["p10"] = {"type": "code", "xp": 10, "minLines": 22,
    "starter": "",
    "cases": [{"name": "Program output", "expected": out(wire)}],
    "check": FN + '''_fn("diameter_metres", "gauge")
_fn("resistance", "length", "gauge", "resistivity")
for _name in ("copper_resistance", "aluminium_resistance"):
    _f = globals().get(_name)
    assert isinstance(_f, types.FunctionType), "Define a function named " + _name + " with def."
    assert "resistance" in _f.__code__.co_names, _name + " should call the reusable resistance calculation."
_constant(1.678e-8, "copper resistivity")
_constant(2.82e-8, "aluminium resistivity")
''' + returns("diameter_metres", wire_ns, *[(g,) for g in (0, 10, 18, 24, 36)])
      + returns("resistance", wire_ns, (3, 18, 1.678e-8), (0, 18, 2.82e-8), (10, 0, 1.678e-8), (2.5, 36, 2.82e-8)),
    "answer": b64(wire),
    "answerNote": "Both materials reuse the same diameter and resistance calculations. Converting diameter to metres keeps the units consistent."}
assert E["p10"]["cases"][0]["expected"] == "0.061163\n0.102789"

# 11. Drag-power report
drag = '''AIR_DENSITY = 1.2
AREA = 2.0
DRAG_COEFFICIENT = 0.3
METRES_PER_SECOND_PER_MPH = 0.447
WATTS_PER_HORSEPOWER = 746

def to_metres_per_second(speed):
    return speed * METRES_PER_SECOND_PER_MPH

def drag_force(velocity):
    return 0.5 * AIR_DENSITY * velocity ** 2 * AREA * DRAG_COEFFICIENT

def power_watts(velocity):
    return drag_force(velocity) * velocity

def main():
    speed = float(input())
    velocity = to_metres_per_second(speed)
    watts = power_watts(velocity)
    print(f'Watts: {watts:.3f}')
    print(f'Horsepower: {watts / WATTS_PER_HORSEPOWER:.3f}')

if __name__ == '__main__':
    main()
'''
assert run_with_prompts(drag, ["20"]) == "Watts: 257.226\nHorsepower: 0.345"
THREE = r"(?<![0-9.])[0-9]+\.[0-9]{3}(?![0-9])"
E["p11"] = {"type": "code", "xp": 10, "minLines": 24,
    "starter": "",
    "cases": [pattern_case(f"Typed {s}", drag, [s], THREE, "watts and horsepower", f"For {s} miles per hour: ")
              for s in ("20", "0", "55", "12.5")],
    "check": FN + '''_fn("main")
assert len([d for d in _defs() if d.name != "main"]) >= 3, "Write separate conversion, force, and power helpers."
_constant(1.2, "air density")
_constant(2.0, "area")
_constant(0.3, "drag coefficient")
''',
    "answer": b64(drag),
    "answerNote": "The functions follow the formula dependencies: convert speed, compute force, then compute power. Zero speed gives zero force and power. "
                  "For 20 miles per hour the model prints `Watts: 257.226` and `Horsepower: 0.345`."}
assert E["p11"]["cases"][0]["check"].startswith("_want = ['257.226', '0.345']")

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-20",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 20 Workbook",
    "subtitle": "Stepwise refinement and variable scope",
    "exercises": E,
}
outfile = ROOT / "workbooks/lecture-20/exercises.json"
outfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", outfile, len(E), "specs")
