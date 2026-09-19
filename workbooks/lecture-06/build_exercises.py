"""Build workbooks/lecture-06/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-06/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-06
"""
import base64, json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()

def run(code, inputs=()):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""), capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n")

def example(code, output=True, **kw):
    """Examples that call input() must use output=False: the checker runs
    them with no scripted answers, and Run shows an inline prompt instead."""
    spec = {"type": "example", "code": code.rstrip("\n"), **kw}
    if output:
        spec["output"] = run(code)
    return spec

def case(name, inputs, code, **kw):
    """A code case whose expected output comes from running `code` with `inputs`."""
    return {"name": name, "inputs": list(inputs), "expected": run(code, inputs), **kw}

def fstr(*forms):
    """Accepted spellings of an f-string expression: with single or double quotes, or bare."""
    out = []
    for body in forms:
        out += [f"f'{body}'", f'f"{body}"', body, body.strip("{}")]
    return out

E = {}

# ---------------------------------------------------------------- 1. Input, Processing, and Output
E["ex-area"] = example("length = 8\nwidth = 5\narea = length * width\nprint(area)\n")
E["cp1"] = {"type": "short", "xp": 2, "answer": b64(
    "The input values are 8 and 5. The processing step multiplies `length` by `width`. The output is 40.")}

# ---------------------------------------------------------------- 2. Controlling print()
E["ex-print"] = example("print('Total:', 42, 'items')\nprint('Finished')\n")
E["ex-sep"] = example("print('2026', '09', '21', sep='-')\nprint('A', 'B', 'C', sep=' | ')\n")
E["ex-end"] = example("print('COMP', end=' ')\nprint('1001')\n")
cp2 = "print('red', 'green', 'blue', sep=', ')\nprint('Loading', end='...')\nprint('done')\n"
E["ex-cp2"] = example(cp2, output=False)
assert run(cp2) == "red, green, blue\nLoading...done"
E["cp2"] = {"type": "table", "xp": 1, "blanks": {
    "l1": {"accept": ["red, green, blue"], "caseSensitive": True, "placeholder": "line 1", "width": "16rem"},
    "l2": {"accept": ["Loading...done"], "caseSensitive": True, "placeholder": "line 2", "width": "16rem"}}}

# ---------------------------------------------------------------- 3. Reading Keyboard Input
E["ex-name"] = example("name = input('Name: ')\nprint('Hello', name)\n", output=False)
E["ex-age"] = example("age = int(input('Age: '))\nnext_age = age + 1\nprint('Next age:', next_age)\n", output=False)
E["ex-price"] = example("price = float(input('Price: '))\nquantity = int(input('Quantity: '))\ntotal = price * quantity\nprint('Total:', total)\n", output=False)
E["ex-twenty"] = example("age = int('twenty')\nprint(age)\n", output=False)
cp3 = "students = int(input('Number of students: '))\ntemperature = float(input('Temperature: '))\n"
cp3_check = '''assert "students" in dir(), "Keep the name students."
assert "temperature" in dir(), "Keep the name temperature."
assert type(students) is int, "students should be converted with int(): a count is a whole number."
assert type(temperature) is float, "temperature should be converted with float(): it may have a decimal part."
'''
E["cp3"] = {"type": "code", "xp": 2, "minLines": 2,
    "starter": "students = ______(input('Number of students: '))\ntemperature = ______(input('Temperature: '))\n",
    "cases": [{"name": "Typed 28 and 21.5", "inputs": ["28", "21.5"], "check": cp3_check}],
    "answer": b64(cp3),
    "answerNote": "The program prints nothing; Check looks at the types of the two names."}
E["cp3-why"] = {"type": "short", "xp": 2, "answer": b64(
    "`input()` always returns a `str`, even when the user types digits. Conversion is a separate operation: `int()` or `float()` must be applied to the text.")}
E["cp3-error"] = {"type": "table", "xp": 1, "blanks": {"err": {
    "accept": ["ValueError", "a ValueError", "value error"], "placeholder": "name of the error", "width": "12rem", "show": "ValueError"}}}

# ---------------------------------------------------------------- 4. Building Output with F-Strings
E["ex-fstring"] = example("name = 'Maya'\ncount = 3\n\nprint(f'{name} has {count} items')\nprint(f'{count} squared is {count ** 2}')\n")
cp4 = "course = 'COMP 1001'\nstudents = 28\nprint(f'{course} has {students} students')\n"
cp4_check = '''assert "{course}" in __source__, "Put the variable name course inside braces: {course}."
assert "{students}" in __source__, "Put the variable name students inside braces: {students}."
assert "f'" in __source__ or 'f"' in __source__, "Write f before the opening quote to make an f-string."
'''
E["cp4"] = {"type": "code", "xp": 2, "minLines": 3, "check": cp4_check,
    "starter": "course = 'COMP 1001'\nstudents = 28\nprint(f'________________________________________')\n",
    "cases": [{"name": "Program output", "expected": run(cp4)},
              {"name": "students = 31", "rewrite": [["students = 28", "students = 31"]], "expected": run(cp4.replace("students = 28", "students = 31"))}],
    "answer": b64(cp4)}
E["cp4-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The variable names `course` and `students` must be inside braces. The connecting words and spaces (` has ` and ` students`) are ordinary string text.")}

# ---------------------------------------------------------------- 5. Format Specifiers
E["ex-money"] = example("subtotal = 19.5\nprint(f'Subtotal: ${subtotal:.2f}')\n")
E["ex-thousands"] = example("population = 1234567\nprint(f'{population:,}')\n")
assert eval("f'{7.5:.2f}'") == "7.50" and eval("f'{2500.4:,.2f}'") == "2,500.40" and eval("f'{42:05d}'") == "00042"
E["cp5"] = {"type": "table", "xp": 1, "blanks": {
    "e1": {"accept": fstr("{7.5:.2f}"), "caseSensitive": True, "placeholder": "f'{…}'", "width": "12rem"},
    "e2": {"accept": fstr("{2500.4:,.2f}"), "caseSensitive": True, "placeholder": "f'{…}'", "width": "12rem"},
    "e3": {"accept": fstr("{42:05d}", "{42:05}"), "caseSensitive": True, "placeholder": "f'{…}'", "width": "12rem"}}}
E["cp5-why"] = {"type": "short", "xp": 2, "answer": b64(
    "No. Formatting creates display text; it does not change the stored value. After `print(f'{subtotal:.2f}')`, `subtotal` still holds the same number.")}

# ---------------------------------------------------------------- 6. Aligning a Simple Table
E["ex-table"] = example("print(f'{\"Item\":<12}{\"Price\":>8}')\nprint(f'{\"Coffee\":<12}{3.5:>8.2f}')\nprint(f'{\"Sandwich\":<12}{12.75:>8.2f}')\n")
cp6 = "print(f'{\"Name\":<10}{\"Score\":>6}')\nprint(f'{\"Ava\":<10}{91:>6}')\n"
cp6_check = '''assert "<10" in __source__, "Names use a left-aligned width of 10: the specifier is <10."
assert ">6" in __source__, "Scores use a right-aligned width of 6: the specifier is >6."
'''
E["cp6"] = {"type": "code", "xp": 2, "minLines": 2, "check": cp6_check,
    "starter": "print(f'{\"Name\":_____}{\"Score\":_____}')\nprint(f'{\"Ava\":_____}{91:_____}')\n",
    "cases": [{"name": "Program output", "expected": run(cp6)}],
    "answer": b64(cp6)}
E["cp6-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Right alignment places digits with the same place value in the same column, so the ones, tens, and decimal points line up and the numbers are easy to compare.")}

# ---------------------------------------------------------------- 7. Recognizing Legacy % Formatting
E["ex-legacy"] = example("price = 3.5\nprint('Price: %.2f' % price)\n")
E["ex-legacy-f"] = example("price = 3.5\nprint(f'Price: {price:.2f}')\n")
cp7 = "distance = 12.5\nprint(f'Distance: {distance:.1f} km')\n"
cp7_check = '''assert "%" not in __source__, "Remove the legacy % formatting: write an f-string instead."
assert "f'" in __source__ or 'f"' in __source__, "Write f before the opening quote to make an f-string."
assert "{distance:.1f}" in __source__.replace(" ", ""), "Put the value and its specifier inside braces: {distance:.1f}."
'''
E["cp7"] = {"type": "code", "xp": 2, "minLines": 2, "check": cp7_check,
    "starter": "distance = 12.5\nprint('Distance: %.1f km' % distance)\n",
    "cases": [{"name": "distance = 12.5", "expected": run(cp7)},
              {"name": "distance = 3", "rewrite": [["distance = 12.5", "distance = 3"]], "expected": run(cp7.replace("distance = 12.5", "distance = 3"))}],
    "answer": b64(cp7),
    "answerNote": "Keep the surrounding words and unit as ordinary text; only the value and its specifier go inside braces."}

# ---------------------------------------------------------------- 8. Escape Sequences
E["ex-escape"] = example("print('First line\\nSecond line')\nprint('A\\tB')\nprint(\"She said, \\\"Hello.\\\"\")\nprint('C:\\\\courses\\\\comp1001')\n")
cp8 = "print('input\\nprocess\\noutput')\n"
cp8_check = '''assert __source__.count("print(") == 1, "Use one print() call with one string literal."
assert "\\\\n" in __source__, "Use the newline escape \\\\n inside the string to start each new line."
'''
E["cp8"] = {"type": "code", "xp": 2, "minLines": 1, "check": cp8_check,
    "starter": "print('____________________')\n",
    "cases": [{"name": "Program output", "expected": run(cp8)}],
    "answer": b64(cp8)}
E["cp8-backslash"] = {"type": "table", "xp": 1, "blanks": {"seq": {
    "accept": ["\\\\", "'\\\\'", "\"\\\\\"", "two backslashes", "a double backslash", "double backslash", "backslash backslash"],
    "caseSensitive": True, "placeholder": "escape sequence", "width": "12rem", "show": "\\\\"}}}

# ---------------------------------------------------------------- Final Review
fr = ("item = input('Item: ')\nprice = float(input('Price: '))\nquantity = int(input('Quantity: '))\ntotal = price * quantity\n\n"
      "print(f'{\"Item\":<12}{\"Quantity\":>10}{\"Total\":>12}')\nprint(f'{item:<12}{quantity:>10}{total:>12.2f}')\n")
E["ex-fr"] = example(fr, output=False)
fr_lines = ["Item          Quantity       Total", "Notebook             3       14.25"]
assert run(fr, ["Notebook", "4.75", "3"]).endswith("\n".join(fr_lines))
E["fr1"] = {"type": "table", "xp": 1, "blanks": {"t": {"accept": ["str", "string"], "placeholder": "type", "show": "str"}}}
E["fr2"] = {"type": "table", "xp": 1, "blanks": {"p": {"accept": ["float"]}, "q": {"accept": ["int"]}}}
E["fr3"] = {"type": "table", "xp": 1, "blanks": {"total": {"accept": ["14.25"], "placeholder": "value"}}}
E["fr4"] = {"type": "table", "xp": 1, "blanks": {
    "l1": {"accept": [fr_lines[-2]], "caseSensitive": True, "placeholder": "heading line", "width": "22rem"},
    "l2": {"accept": [fr_lines[-1]], "caseSensitive": True, "placeholder": "data line", "width": "22rem"}}}

# ---------------------------------------------------------------- Additional Practice
pa = "print('A', 'B', 'C', sep='-')\nprint('Ready', end='...')\nprint('go')\n"
pa_check = '''assert "sep=" in __source__.replace(" ", ""), "Display A-B-C with one print() call that uses sep='-'."
assert "end=" in __source__.replace(" ", ""), "Display Ready...go with two print() calls; the first uses end='...'."
assert __source__.count("print(") == 3, "Use exactly three print() calls: one for A-B-C and two for Ready...go."
'''
E["pa"] = {"type": "code", "xp": 5, "minLines": 3, "check": pa_check,
    "starter": "# Display A-B-C using sep, then Ready...go using end.\n",
    "cases": [{"name": "Program output", "expected": run(pa)}],
    "answer": b64(pa)}
pb = "distance = float(input('Distance: '))\ntrips = int(input('Trips: '))\ntotal_distance = distance * trips\nprint(f'Total distance: {total_distance}')\n"
pb_check = '''assert type(distance) is float, "Convert the distance with float()."
assert type(trips) is int, "Convert the number of trips with int()."
assert "total_distance" in dir() and total_distance == distance * trips, "total_distance should be the distance multiplied by the number of trips."
assert str(total_distance) in __stdout__, "Display total_distance with print()."
'''
E["pb"] = {"type": "code", "xp": 5, "minLines": 4, "check": pb_check,
    "starter": "distance = ______(input('Distance: '))\ntrips = ______(input('Trips: '))\ntotal_distance = ____________________\nprint(______________________________)\n",
    "cases": [{"name": "Typed 12.5 and 3", "inputs": ["12.5", "3"]},
              {"name": "Typed 8 and 4", "inputs": ["8", "4"]}],
    "answer": b64(pb),
    "answerNote": "Any label is fine as long as the product is displayed."}
assert eval("f'{5:05d}'") == "00005" and eval("f'{12345.6:,.2f}'") == "12,345.60" and eval("f'{\"Lab\":^9}'") == "   Lab   "
E["pc"] = {"type": "table", "xp": 1, "blanks": {
    "e1": {"accept": fstr("{5:05d}", "{5:05}"), "caseSensitive": True, "placeholder": "f'{…}'", "width": "12rem"},
    "e2": {"accept": fstr("{12345.6:,.2f}"), "caseSensitive": True, "placeholder": "f'{…}'", "width": "12rem"},
    "e3": {"accept": fstr("{'Lab':^9}", '{"Lab":^9}'), "caseSensitive": True, "placeholder": "f'{…}'", "width": "12rem"}}}
pd = "print(f'{\"Item\":<10}{\"Price\":>8}')\nprint(f'{\"Pen\":<10}{1.25:>8.2f}')\nprint(f'{\"Notebook\":<10}{4.75:>8.2f}')\n"
pd_check = '''assert "<10" in __source__, "Items use a left-aligned width of 10: <10."
assert ">8.2f" in __source__, "Prices use a right-aligned width of 8 with two decimal places: >8.2f."
'''
E["pd"] = {"type": "code", "xp": 5, "minLines": 3, "check": pd_check,
    "starter": "# Print the heading row, then Pen and Notebook.\n",
    "cases": [{"name": "Program output", "expected": run(pd)}],
    "answer": b64(pd)}
E["pe"] = {"type": "short", "xp": 2, "minChars": 40, "rows": 4, "answer": b64(
    "The `f` marks an f-string. The braces contain the expression to evaluate. The colon begins the format specifier. "
    "The width `10` reserves at least ten character positions and right aligns by default. `.2f` displays a floating-point value with two digits after the decimal point.")}

# ---------------------------------------------------------------- Putting It All Together
pt1 = "item = input('Item: ')\nunit_price = float(input('Unit price: $'))\nquantity = int(input('Quantity: '))\ntotal = unit_price * quantity\n"
pt1_check = '''assert type(unit_price) is float, "Convert the unit price with float(): a price may have a decimal part."
assert type(quantity) is int, "Convert the quantity with int(): it is a whole number."
assert "total" in dir() and total == unit_price * quantity, "total should be the unit price multiplied by the quantity."
'''
E["pt1"] = {"type": "code", "xp": 2, "minLines": 4,
    "starter": "item = input('Item: ')\nunit_price = ______(input('Unit price: $'))\nquantity = ______(input('Quantity: '))\ntotal = __________________________\n",
    "cases": [{"name": "Typed Marker set, 6.5, 2", "inputs": ["Marker set", "6.5", "2"], "check": pt1_check}],
    "answer": b64(pt1),
    "answerNote": "The program prints nothing yet; Check looks at the types and the total."}
pt2_head = "item = 'Marker set'\nquantity = 2\ntotal = 13.0\n\n"
pt2 = pt2_head + "print(f'{\"Item\":<14}{\"Qty\":>8}{\"Total\":>12}')\nprint(f'{item:<14}{quantity:>8}{total:>12.2f}')\n"
pt2_check = '''assert "<14" in __source__, "The item column is left aligned with width 14: <14."
assert ">8" in __source__, "The quantity column is right aligned with width 8: >8."
assert ">12.2f" in __source__, "The total column is right aligned with width 12 and two decimal places: >12.2f."
'''
E["pt2"] = {"type": "code", "xp": 2, "minLines": 5, "check": pt2_check,
    "starter": pt2_head + "print(f'{\"Item\":_____}{\"Qty\":_____}{\"Total\":_____}')\nprint(f'{item:_____}{quantity:_____}{total:_____}')\n",
    "cases": [{"name": "Marker set, 2, 13.0", "expected": run(pt2)},
              {"name": "Pen, 12, 15.0", "rewrite": [["item = 'Marker set'", "item = 'Pen'"], ["quantity = 2", "quantity = 12"], ["total = 13.0", "total = 15.0"]],
               "expected": run(pt2.replace("item = 'Marker set'", "item = 'Pen'").replace("quantity = 2", "quantity = 12").replace("total = 13.0", "total = 15.0"))}],
    "answer": b64(pt2)}
receipt = pt1 + "\nprint('\\nReceipt')\nprint(f'{\"Item\":<14}{\"Qty\":>8}{\"Total\":>12}')\nprint(f'{item:<14}{quantity:>8}{total:>12.2f}')\n"
E["ex-receipt"] = example(receipt, output=False)
assert run(receipt, ["Marker set", "6.5", "2"]).endswith("Receipt\nItem               Qty       Total\nMarker set           2       13.00")

# ---------------------------------------------------------------- Coding Practice
c1 = ("number = float(input('Number: '))\nsquare = number * number\ncube = number * number * number\nfourth = number ** 4\n\n"
      "print(f'Square: {square}')\nprint(f'Cube: {cube}')\nprint(f'Fourth power: {fourth}')\n")
E["c1"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "number = float(input('Number: '))\nsquare = ____________________\ncube = ______________________\nfourth = ____________________\n\n# Print the three labelled results.\n",
    "cases": [case("Typed 2.5", ["2.5"], c1), case("Typed 3", ["3"], c1)],
    "check": 'assert __source__.count("**") == 1, "Use ** only for the fourth power; build the square and cube by multiplication."',
    "answer": b64(c1)}
c2 = ("first = int(input('First integer: '))\nsecond = int(input('Second integer: '))\n\n"
      "sum_value = first + second\ndifference = first - second\nproduct = first * second\naverage = sum_value / 2\n\n"
      "print(f'Sum: {sum_value}')\nprint(f'Difference: {difference}')\nprint(f'Product: {product}')\nprint(f'Average: {average:.2f}')\n")
E["c2"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": "first = int(input('First integer: '))\nsecond = int(input('Second integer: '))\n\nsum_value = __________________\ndifference = __________________\nproduct = _____________________\naverage = _____________________\n\n# Print the four labelled results.\n",
    "cases": [case("Typed 20 and 25", ["20", "25"], c2), case("Typed 7 and 4", ["7", "4"], c2)],
    "answer": b64(c2)}
c3_head = "sum_value = 45\ndifference = -5\nproduct = 500\naverage = 22.5\n\n"
c3 = c3_head + "print(f'{\"Sum\":<12}{sum_value:>10}')\nprint(f'{\"Difference\":<12}{difference:>10}')\nprint(f'{\"Product\":<12}{product:>10}')\nprint(f'{\"Average\":<12}{average:>10.2f}')\n"
c3_check = '''assert __source__.count("<12") >= 4, "Every label uses a left-aligned width of 12: <12."
assert __source__.count(">10") >= 4, "Every value uses a right-aligned width of 10: >10."
assert ">10.2f" in __source__, "Keep two decimal places on the average: >10.2f."
'''
E["c3"] = {"type": "code", "xp": 5, "minLines": 8, "check": c3_check,
    "starter": c3_head + "print(f'{\"Sum\":_____}{sum_value:_____}')\n# Add the other three rows.\n",
    "cases": [{"name": "45, -5, 500, 22.5", "expected": run(c3)},
              {"name": "11, 3, 28, 5.5", "rewrite": [["sum_value = 45", "sum_value = 11"], ["difference = -5", "difference = 3"], ["product = 500", "product = 28"], ["average = 22.5", "average = 5.5"]],
               "expected": run(c3.replace("sum_value = 45", "sum_value = 11").replace("difference = -5", "difference = 3").replace("product = 500", "product = 28").replace("average = 22.5", "average = 5.5"))}],
    "answer": b64(c3)}
c4 = ("fuel = float(input('Fuel in tank (L): '))\nefficiency = float(input('Efficiency (km/L): '))\nprice = float(input('Price per litre: $'))\n\n"
      "cost_per_100 = 100 / efficiency * price\nrange_km = fuel * efficiency\n\n"
      "print(f'Cost per 100 km: ${cost_per_100:.2f}')\nprint(f'Range: {range_km:.1f} km')\n")
E["c4"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "fuel = float(input('Fuel in tank (L): '))\nefficiency = float(input('Efficiency (km/L): '))\nprice = float(input('Price per litre: $'))\n\ncost_per_100 = __________________________\nrange_km = ______________________________\n\n# Print both results with units.\n",
    "cases": [case("Typed 40, 12.5, 1.75", ["40", "12.5", "1.75"], c4), case("Typed 52, 9.6, 1.499", ["52", "9.6", "1.499"], c4)],
    "answer": b64(c4)}
c5 = "LETTER_O = ' ***\\n*   *\\n*   *\\n*   *\\n ***'\nLETTER_K = '*   *\\n*  *\\n***\\n*  *\\n*   *'\n\nprint(LETTER_O)\nprint(LETTER_K)\n"
c5_check = '''assert isinstance(LETTER_O, str) and isinstance(LETTER_K, str), "LETTER_O and LETTER_K must both be strings."
for name, letter in (("LETTER_O", LETTER_O), ("LETTER_K", LETTER_K)):
    rows = letter.rstrip("\\n").split("\\n")
    assert len(rows) == 5, f"{name} should draw five rows: use four newline escapes (\\\\n) inside the string."
    assert all(row.strip() for row in rows), f"Every row of {name} needs at least one symbol."
lines = __stdout__.rstrip("\\n").split("\\n")
assert len(lines) == 10, "The output should be ten lines: five for O, then five for K."
'''
E["c5"] = {"type": "code", "xp": 5, "minLines": 5,
    "starter": "LETTER_O = '____________________________'\nLETTER_K = '____________________________'\n\nprint(LETTER_O)\nprint(LETTER_K)\n",
    "cases": [{"name": "Two five-row letters", "check": c5_check}],
    "answer": b64(c5),
    "answerNote": "Any symbols are fine as long as each letter is one string with five rows."}
c6 = ("TAX_RATE = 0.15\nSHIPPING_PER_ITEM = 3.00\n\nsupplies_price = float(input('Supplies price: $'))\nitem_count = int(input('Number of items: '))\n\n"
      "tax = supplies_price * TAX_RATE\nshipping = item_count * SHIPPING_PER_ITEM\norder_total = supplies_price + tax + shipping\n\n"
      "print(f'Tax: ${tax:.2f}')\nprint(f'Shipping: ${shipping:.2f}')\nprint(f'Order total: ${order_total:.2f}')\n")
E["c6"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": "TAX_RATE = 0.15\nSHIPPING_PER_ITEM = 3.00\n\nsupplies_price = float(input('Supplies price: $'))\nitem_count = int(input('Number of items: '))\n\ntax = ______________________________\nshipping = _________________________\norder_total = ______________________\n\n# Print tax, shipping, and total.\n",
    "cases": [case("Typed 40 and 2", ["40", "2"], c6), case("Typed 129.99 and 5", ["129.99", "5"], c6)],
    "check": 'assert "TAX_RATE" in __source__ and "SHIPPING_PER_ITEM" in __source__, "Use the constants TAX_RATE and SHIPPING_PER_ITEM in the calculations."',
    "answer": b64(c6)}
c7 = ("price = float(input('Price: $'))\ntotal_cents = round(price * 100)\ndollars = total_cents // 100\ncents = total_cents % 100\n\n"
      "print(f'Dollars: {dollars}')\nprint(f'Cents: {cents:02d}')\n")
E["c7"] = {"type": "code", "xp": 5, "minLines": 7,
    "starter": "price = float(input('Price: $'))\ntotal_cents = round(price * 100)\ndollars = __________________________\ncents = ____________________________\n\nprint(f'Dollars: {dollars}')\nprint(f'Cents: {cents:02d}')\n",
    "cases": [case("Typed 4.05", ["4.05"], c7), case("Typed 19.99", ["19.99"], c7), case("Typed 3", ["3"], c7)],
    "check": 'assert "//" in __source__ and "%" in __source__, "Use integer division (//) for the dollars and remainder (%) for the cents."',
    "answer": b64(c7)}
c9 = ("balance = float(input('Initial balance: $'))\nannual_percent = float(input('Annual interest rate (%): '))\nmonthly_rate = annual_percent / 100 / 12\n\n"
      "month_1 = balance * (1 + monthly_rate)\nmonth_2 = month_1 * (1 + monthly_rate)\nmonth_3 = month_2 * (1 + monthly_rate)\n\n"
      "print(f'After month 1: ${month_1:.2f}')\nprint(f'After month 2: ${month_2:.2f}')\nprint(f'After month 3: ${month_3:.2f}')\n")
E["c9"] = {"type": "code", "xp": 5, "minLines": 11,
    "starter": "balance = float(input('Initial balance: $'))\nannual_percent = float(input('Annual interest rate (%): '))\nmonthly_rate = __________________________\n\nmonth_1 = _______________________________\nmonth_2 = _______________________________\nmonth_3 = _______________________________\n\n# Print each monthly balance as money.\n",
    "cases": [case("Typed 1000 and 6", ["1000", "6"], c9), case("Typed 250 and 12", ["250", "12"], c9)],
    "check": 'assert "for " not in __source__ and "while " not in __source__, "Do not use a loop: calculate the three months one after another."',
    "answer": b64(c9)}
c10 = ("r1 = float(input('R1 (ohms): '))\nr2 = float(input('R2 (ohms): '))\nr3 = float(input('R3 (ohms): '))\n\n"
       "total = r1 + (r2 * r3) / (r2 + r3)\nprint(f'Total resistance: {total:.2f} ohms')\n")
E["c10"] = {"type": "code", "xp": 5, "minLines": 6,
    "starter": "r1 = float(input('R1 (ohms): '))\nr2 = float(input('R2 (ohms): '))\nr3 = float(input('R3 (ohms): '))\n\ntotal = __________________________________________\nprint(____________________________________________)\n",
    "cases": [case("Typed 10, 20, 20", ["10", "20", "20"], c10), case("Typed 5, 10, 30", ["5", "10", "30"], c10)],
    "answer": b64(c10)}
c11 = ("import math\n\ntemperature = float(input('Temperature (C): '))\nhumidity = float(input('Relative humidity (0 to 1): '))\n\n"
       "f_value = (17.27 * temperature) / (237.7 + temperature) + math.log(humidity)\ndew_point = (237.7 * f_value) / (17.27 - f_value)\nprint(f'Dew point: {dew_point:.1f} C')\n")
E["c11"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": "import math\n\ntemperature = float(input('Temperature (C): '))\nhumidity = float(input('Relative humidity (0 to 1): '))\n\nf_value = ________________________________________\ndew_point = ______________________________________\nprint(____________________________________________)\n",
    "cases": [case("Typed 20 and 0.5", ["20", "0.5"], c11), case("Typed 30 and 0.8", ["30", "0.8"], c11)],
    "check": 'assert "math.log(" in __source__, "Use math.log() for the natural logarithm of the humidity."',
    "answer": b64(c11)}
c12 = ("import math\n\nEPSILON = 8.854e-12\nq1 = float(input('Charge 1 (C): '))\nq2 = float(input('Charge 2 (C): '))\ndistance = float(input('Distance (m): '))\n\n"
       "force = (q1 * q2) / (4 * math.pi * EPSILON * distance ** 2)\nprint(f'Force: {force:.5f} N')\n")
E["c12"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": "import math\n\nEPSILON = 8.854e-12\nq1 = float(input('Charge 1 (C): '))\nq2 = float(input('Charge 2 (C): '))\ndistance = float(input('Distance (m): '))\n\nforce = __________________________________________\nprint(____________________________________________)\n",
    "cases": [case("Typed 1e-6, 2e-6, 0.5", ["1e-6", "2e-6", "0.5"], c12), case("Typed 3e-6, 3e-6, 0.2", ["3e-6", "3e-6", "0.2"], c12)],
    "check": 'assert "math.pi" in __source__, "Use math.pi for pi."',
    "answer": b64(c12)}
c13 = "print(' /---\\\\')\nprint('| o o |')\nprint('|  ^  |')\nprint('| --- |')\nprint(' \\\\---/')\nprint('Python', 'face', sep=' ')\n"
c13_check = '''lines = __stdout__.rstrip("\\n").split("\\n")
assert len(lines) == 6, "Display exactly six lines: a five-line face and then the label."
assert lines[5] == "Python face", "The sixth line must be exactly: Python face"
allowed = set("()|-\\\\/^o ")
for i, line in enumerate(lines[:5], start=1):
    bad = sorted(set(line) - allowed)
    assert not bad, f"Line {i} uses {bad!r}; the face may only use ( ) | - \\\\ / ^ o and spaces."
    assert line.strip(), f"Line {i} is empty; every line of the face needs some symbols."
assert "\\\\" in __stdout__, "Include at least one backslash in the face; remember it is written \\\\\\\\ in a string literal."
'''
E["c13"] = {"type": "code", "xp": 5, "minLines": 6,
    "starter": "# Write your print calls here.\n",
    "cases": [{"name": "A five-line face and its label", "check": c13_check}],
    "answer": b64(c13),
    "answerNote": "Many faces are acceptable. This one uses a doubled backslash so one backslash appears in the output."}
assert run(c13).split("\n")[5] == "Python face"

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-06",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 6 Workbook",
    "subtitle": "Input and output, and f-strings",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-06/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
