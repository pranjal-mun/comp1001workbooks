"""Build workbooks/lecture-10/exercises.json.

Expected outputs are produced by actually running the code, so the specs
cannot drift from Python's real behaviour. Run from anywhere:

    python3 workbooks/lecture-10/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-10
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
    spec = {"type": "example", "code": code.rstrip("\n"), **kw}
    if output:
        spec["output"] = run(code)
    return spec

def blank(*accept, **kw):
    return {"accept": list(accept), **kw}

def input_cases(answer, cases):
    """cases: [(name, inputs)] -> graded cases whose expected output comes from the model answer."""
    return [{"name": name, "inputs": list(inputs), "expected": run(answer, inputs)} for name, inputs in cases]

def rewrite_cases(answer, cases):
    """cases: [(name, [[old, new], ...])] -> graded cases; the first case has no rewrite."""
    out = []
    for name, rewrites in cases:
        code = answer
        for old, new in rewrites:
            assert old in code, (name, old)
            code = code.replace(old, new)
        case = {"name": name, "expected": run(code)}
        if rewrites:
            case["rewrite"] = rewrites
        out.append(case)
    return out

# Answer vocabularies reused by several trace tables.
TRUE = blank("True", "T", "true")
FALSE = blank("False", "F", "false")
SKIPPED = blank("skipped", "skip", "not reached", "not tested", "never reached", "never tested", "not run")
CHAIN = blank("chain", "elif chain", "an elif chain", "if/elif/else chain", "if-elif-else chain", "elif", "if/elif/else", "one chain")
SEPARATE = blank("separate ifs", "separate if", "separate if statements", "separate", "separate if's", "independent ifs", "separate ifs statements", "two ifs", "separate if statement")
NESTED = blank("nested if", "nested", "nested decision", "nesting", "a nested if", "nested if statement", "nested ifs")

E = {}

# ---------------------------------------------------------------- 1. Nested Decisions
E["ex-w01"] = example('member = "yes"\ntotal = 120\n\nif member == "yes":\n    if total > 100:\n        discount = 0.20\n    else:\n        discount = 0.10\nelse:\n    discount = 0.0\n\nprint("Discount:", discount)\n')
E["cp1"] = {"type": "table", "xp": 1, "blanks": {
    "outer": FALSE,
    "inner": blank("no", "not tested", "no, skipped", "skipped", "never", "no it is skipped", "not reached"),
    "discount": blank("0.0", "0", "0.00")}}
E["cp1-why"] = {"type": "short", "xp": 2, "answer": b64(
    "The outer condition is `False`. The inner condition is not tested. Python takes the outer `else`, so `discount` becomes `0.0`.")}

E["ex-w02"] = example('member = "yes"\ntotal = 80\n\nif member == "yes":\n    if total > 100:\n        message = "Large member order"\n    else:\n        message = "Member order"\nelse:\n    message = "Regular order"\n\nprint(message)\n')
DAY = ("day == 'Saturday'", 'day == "Saturday"', "day == saturday", "if day == 'Saturday'", 'if day == "Saturday"', "the day condition", "day condition", "the day test", "day", "day == 'saturday'", 'day == "saturday"')
WEATHER = ("weather == 'rain'", 'weather == "rain"', "weather == rain", "if weather == 'rain'", 'if weather == "rain"', "the weather condition", "weather condition", "the weather test", "weather", "the inner if", "inner if")
E["cp2"] = {"type": "table", "xp": 1, "blanks": {
    "inner": blank(*WEATHER, width="16rem", placeholder="condition"),
    "outer": blank(*DAY, "the outer if", "outer if", width="16rem", placeholder="condition"),
    "first": blank(*DAY, width="16rem", placeholder="condition")}}
E["cp2-when"] = {"type": "short", "xp": 2, "answer": b64(
    "The condition `day == 'Saturday'` is tested first. The inner weather condition is tested only when the day condition is `True`. "
    "The indented `else` matches the weather test; the unindented `else` matches the day test.")}

E["cp3"] = {"type": "table", "xp": 1, "blanks": {
    "v1": TRUE, "a1": blank("if block", "if", "outer if block", "the if block", "enter the if block", "outer if", "enter the outer block", "the outer if block"),
    "v2": TRUE, "a2": blank("if block", "if", "inner if block", "the if block", "enter the if block", "inner if", "enter the inner if block", "the inner if block"),
    "message": blank("'Large member order'", '"Large member order"', "Large member order", caseSensitive=True, width="16rem"),
    "printed": blank("Large member order", caseSensitive=True, width="16rem")}}

# ---------------------------------------------------------------- 2. Multiple Alternatives
grade_chain = 'score = 76\n\nif score >= 80:\n    grade = "A"\nelif score >= 70:\n    grade = "B"\nelif score >= 60:\n    grade = "C"\nelif score >= 50:\n    grade = "D"\nelse:\n    grade = "F"\n\nprint("Grade:", grade)\n'
E["ex-w03"] = example(grade_chain)
NEXT = blank("next", "next condition", "test the next condition", "try the next condition", "move to the next condition", "go to the next elif", "next elif")
RUN = blank("run", "run the block", "run this block", "runs", "run the branch", "run this branch", "store 'C'", "grade = 'C'", 'grade = "C"', "store C", "run and skip the rest")
E["cp4"] = {"type": "table", "xp": 1, "blanks": {
    "v1": FALSE, "n1": NEXT,
    "v2": FALSE, "n2": NEXT,
    "v3": TRUE, "n3": RUN,
    "v4": SKIPPED, "n4": SKIPPED,
    "grade": blank("C", "'C'", '"C"', caseSensitive=True)}}

E["ex-w04"] = example('score = 92\n\nif score >= 80:\n    grade = "A"\nelif score >= 70:\n    grade = "B"\nelse:\n    grade = "C or below"\n\nprint(grade)\n')
E["cp5"] = {"type": "table", "xp": 1, "blanks": {
    "c1": blank("1", "1 (True)", "1, True", "1 True", "1 - True", "first", "first, True", "tested first", "1: True", "1 true"),
    "c2": SKIPPED, "c3": SKIPPED}}

E["ex-w05"] = example('score = 92\n\nif score >= 50:\n    grade = "D"\nelif score >= 60:\n    grade = "C"\nelif score >= 70:\n    grade = "B"\nelif score >= 80:\n    grade = "A"\n\nprint(grade)\n')
def temp(n):
    return blank(f"temperature >= {n}", f"temperature>={n}", f">= {n}", f">={n}", f"temperature >= {n}.0", str(n), width="14rem", placeholder="condition")
E["cp6"] = {"type": "table", "xp": 1, "blanks": {"o1": temp(30), "o2": temp(20), "o3": temp(10)}}

E["cp7"] = {"type": "short", "xp": 2, "answer": b64(
    "Python already knows that `age < 5` is `False`, so the age is at least 5. The second branch needs only the upper test `age < 18`; the earlier failure supplies the lower limit.")}

temp_chain = 'temperature = 4\n\nif temperature >= 30:\n    label = "hot"\nelif temperature >= 20:\n    label = "warm"\nelif temperature >= 10:\n    label = "cool"\nelse:\n    label = "cold"\n\nprint(label)\n'
E["ex-w07"] = example(temp_chain)
def branch(n, word):
    return blank(f"temperature >= {n}", f"temperature>={n}", f">= {n}", f">={n}", word, f"the {word} branch", f"{word} branch", f"first branch" if n == 30 else f"the {n} branch", width="14rem", placeholder="condition or catch-all")
E["cp8"] = {"type": "table", "xp": 1, "blanks": {
    "b1": branch(30, "hot"), "l1": blank("hot", "'hot'", '"hot"'),
    "b2": branch(20, "warm"), "l2": blank("warm", "'warm'", '"warm"'),
    "b3": branch(10, "cool"), "l3": blank("cool", "'cool'", '"cool"'),
    "b4": blank("catch-all", "catch all", "else", "final else", "the final else", "the catch-all", "the else", "else branch", width="14rem", placeholder="condition or catch-all"),
    "l4": blank("cold", "'cold'", '"cold"')}}

# ---------------------------------------------------------------- 3. Choosing a Decision Structure
E["ex-w08"] = example('score = 95\ngrade = ""\n\nif score >= 80:\n    grade = "A"\nif score >= 70:\n    grade = "B"\n\nprint(grade)\n')
E["ex-w09"] = example('temperature = 31\n\nif temperature > 30:\n    print("Heat warning")\nif temperature > 25:\n    print("Bring water")\n')
E["cp9"] = {"type": "table", "xp": 1, "blanks": {"g": CHAIN, "w": SEPARATE, "a": CHAIN}}
E["cp9-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Use a chain for one letter grade, separate `if` statements for every applicable safety warning, and a chain for one age category. "
    "A chain makes alternatives mutually exclusive; separate `if`s allow several results.")}
E["cp10"] = {"type": "table", "xp": 1, "blanks": {"a": CHAIN, "b": NESTED}}
E["cp10a-why"] = {"type": "short", "xp": 2, "rows": 2, "answer": b64(
    "Use an `elif` chain because exactly one shipping rate must be selected.")}
E["cp10b-why"] = {"type": "short", "xp": 2, "rows": 2, "answer": b64(
    "Use a nested decision because the order-total question matters only inside the member branch.")}

# ---------------------------------------------------------------- Final Review
for n, text in enumerate([
    "A nested decision is an `if` statement inside a branch of another decision.",
    "A matching `if` and `else` begin in the same column. A more deeply indented `else` belongs to an equally indented inner `if`.",
    "Python runs that condition's block and skips all later parts of the same chain.",
    "A broad condition placed first can accept values meant for a more specific case, making the specific branch unreachable.",
    "It catches every value that failed all earlier conditions.",
    "A chain stops after its first true condition, so at most one branch runs. Separate `if` statements are all tested, so several blocks can run.",
    "Nesting is clearer when a later question is relevant only inside one branch of an earlier question.",
], start=1):
    E[f"fr{n}"] = {"type": "short", "xp": 2, "rows": 2, "answer": b64(text)}

# ---------------------------------------------------------------- Additional Practice
E["ex-pa"] = example('member = "yes"\nvisits = 3\n\nif member == "yes":\n    if visits >= 5:\n        reward = "large"\n    else:\n        reward = "small"\nelse:\n    reward = "none"\n\nprint(reward)\n')
E["pa"] = {"type": "table", "xp": 1, "blanks": {
    "outer": TRUE, "inner": FALSE,
    "branch": blank("inner else", "the inner else", "else", "inner else block", "the inner else block", "else block", "inner else branch", "reward = 'small'", 'reward = "small"', width="14rem"),
    "output": blank("small", "'small'", '"small"', caseSensitive=True)}}

pb = 'value = 100\n\nif value >= 100:\n    label = "high"\nelif value >= 50:\n    label = "medium"\nelse:\n    label = "low"\n\nprint(label)\n'
E["pb"] = {"type": "code", "xp": 5, "minLines": 9,
    "starter": 'value = 100\n\nif value :\n    label = "high"\nelif value :\n    label = "medium"\nelse:\n    label = "low"\n\nprint(label)\n',
    "cases": rewrite_cases(pb, [
        ("value = 100", []),
        ("value = 99", [["value = 100", "value = 99"]]),
        ("value = 50", [["value = 100", "value = 50"]]),
        ("value = 49", [["value = 100", "value = 49"]]),
        ("value = 250", [["value = 100", "value = 250"]])]),
    "answer": b64(pb)}
E["pb-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Fill the conditions with `>= 100` and `>= 50`. The high condition comes first because every high value also satisfies the broader medium condition.")}

pc = 'points = 1000\n\nif points >= 1000:\n    level = "gold"\nelif points >= 500:\n    level = "silver"\nelif points >= 100:\n    level = "bronze"\nelse:\n    level = "starting"\n\nprint(level)\n'
E["pc"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": 'points = 1000\n\nif points >= 100:\n    level = "bronze"\nelif points >= 500:\n    level = "silver"\nelif points >= 1000:\n    level = "gold"\nelse:\n    level = "starting"\n\nprint(level)\n',
    "cases": rewrite_cases(pc, [
        ("points = 1000", []),
        ("points = 999", [["points = 1000", "points = 999"]]),
        ("points = 500", [["points = 1000", "points = 500"]]),
        ("points = 100", [["points = 1000", "points = 100"]]),
        ("points = 99", [["points = 1000", "points = 99"]])]),
    "answer": b64(pc),
    "answerNote": "Test the highest threshold first, then move toward the broadest condition."}

E["pd"] = {"type": "table", "xp": 1, "blanks": {"d1": SEPARATE, "d2": CHAIN, "d3": SEPARATE}}
E["pd-why"] = {"type": "short", "xp": 2, "answer": b64(
    "Use separate `if`s for all earned badges (several can apply at once), a chain for one age label (exactly one applies), "
    "and separate `if`s for every applicable weather warning.")}

pe = 'region = "local"\ndistance = 10\n\nif region == "local":\n    if distance <= 10:\n        message = "Delivery charge: $5"\n    else:\n        message = "Delivery charge: $8"\nelse:\n    message = "Delivery not accepted"\n\nprint(message)\n'
E["pe"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": 'region = "local"\ndistance = 10\n\n# Write the nested decision here.\n\n\n\n\nprint(message)\n',
    "check": 'import re\nassert re.search(r"^\\s+if ", __source__, re.M), "Put the distance decision inside the local branch: an indented if statement."',
    "cases": rewrite_cases(pe, [
        ("local, 10 km", []),
        ("local, 11 km", [["distance = 10", "distance = 11"]]),
        ("local, 3 km", [["distance = 10", "distance = 3"]]),
        ("not local", [['region = "local"', 'region = "north"']])]),
    "answer": b64(pe),
    "answerNote": "The distance decision belongs inside the local branch."}

E["ex-pf"] = example(grade_chain.replace("score = 76", "score = 64"))
E["pf"] = {"type": "short", "xp": 2, "rows": 9, "placeholder": "score → grade — what it tests, one case per line", "answer": b64(
    "One compact set is 49/F, 50/D, 59/D, 60/C, 69/C, 70/B, 79/B, and 80/A. It checks each boundary from both sides and reaches every branch. "
    "Adding a value above 80, such as 95/A, is also useful.")}

# ---------------------------------------------------------------- Putting It All Together
admission = 'age = int(input("Age: "))\nmember = input("Member (yes/no): ")\nvisits = int(input("Previous visits: "))\n\nif age < 13:\n    base_price = 8\nelif age < 65:\n    base_price = 14\nelse:\n    base_price = 10\n\nif member == "yes":\n    if visits >= 5:\n        discount = 3\n    else:\n        discount = 1\nelse:\n    discount = 0\n\nfinal_price = base_price - discount\nprint(f"Admission: ${final_price:.2f}")\n'
E["ex-admission"] = example(admission, output=False)
assert run(admission, ["13", "no", "0"]).endswith("Admission: $14.00")
assert run(admission, ["65", "yes", "5"]).endswith("Admission: $7.00")
assert run(admission, ["12", "yes", "2"]).endswith("Admission: $7.00")
E["syn"] = {"type": "table", "xp": 1, "blanks": {
    "age": blank("age < 13", "age<13", "< 13", "<13", "first", "the first", "first branch", width="12rem"),
    "member": TRUE, "visits": FALSE,
    "base": blank("8", "8.0", "$8"), "discount": blank("1", "1.0", "$1"),
    "output": blank("Admission: $7.00", caseSensitive=True, width="14rem")}}

# ---------------------------------------------------------------- Coding Practice
c01 = 'month = 1\nday = 1\n\noccasion = "Ordinary day"\n\nif month == 1:\n    if day == 1:\n        occasion = "New Year Day"\nelif month == 7:\n    if day == 1:\n        occasion = "Canada Day"\nelif month == 9:\n    if day == 30:\n        occasion = "National Day for Truth and Reconciliation"\nelif month == 12:\n    if day == 31:\n        occasion = "Year End"\n\nprint(occasion)\n'
E["c01"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": 'month = 1\nday = 1\n\noccasion = "Ordinary day"\n\n# Add the nested decision here.\n\n\n\n\nprint(occasion)\n',
    "check": 'import re\nassert re.search(r"^\\s+if day", __source__, re.M), "Compare the day only after its month matches: nest each day test inside the matching month branch."',
    "cases": rewrite_cases(c01, [
        ("1 / 1", []),
        ("7 / 1", [["month = 1", "month = 7"]]),
        ("9 / 30", [["month = 1", "month = 9"], ["day = 1", "day = 30"]]),
        ("12 / 31", [["month = 1", "month = 12"], ["day = 1", "day = 31"]]),
        ("7 / 2", [["month = 1", "month = 7"], ["day = 1", "day = 2"]]),
        ("3 / 1", [["month = 1", "month = 3"]])]),
    "answer": b64(c01),
    "answerNote": "Start with the catch-all label, then use a month chain. Nest each day test inside its matching month branch."}

c02 = 'score = 90\n\nif score >= 90:\n    grade = "A"\nelif score >= 80:\n    grade = "B"\nelif score >= 70:\n    grade = "C"\nelif score >= 60:\n    grade = "D"\nelse:\n    grade = "F"\n\nprint(grade)\n'
E["c02"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": 'score = 90\n\n# Add the ordered chain here.\n\n\n\n\n\n\nprint(grade)\n',
    "check": 'assert " and " not in __source__ and " or " not in __source__, "Use only one comparison in each condition; let the earlier branches rule out the upper limits."',
    "cases": rewrite_cases(c02, [(f"score = {s}", [] if s == 90 else [["score = 90", f"score = {s}"]]) for s in (90, 89, 80, 79, 70, 69, 60, 59)]),
    "answer": b64(c02),
    "answerNote": "Order the lower bounds from largest to smallest. The failed earlier tests supply the upper limits for later bands."}

E["c03"] = {"type": "short", "xp": 2, "rows": 6, "answer": b64(
    "A nested decision asks a later question only inside one branch of an earlier question; for example, ask whether a library user is a member, then ask about overdue days only for members. "
    "A chain chooses one of several alternatives; for example, assign one size label from a package's weight.")}
E["c04a"] = {"type": "short", "xp": 2, "answer": b64(
    "The two equality conditions cannot both be true for one string, so swapping them does not change the selected branch.")}
E["c04b"] = {"type": "short", "xp": 2, "answer": b64(
    "A value of 1000 or more satisfies both comparisons. Placing `points >= 500` first would incorrectly capture it, so order matters.")}

c05 = 'temperature = 9\n\nif temperature < 10:\n    label = "cold"\nelif temperature < 20:\n    label = "cool"\nelif temperature < 30:\n    label = "warm"\nelse:\n    label = "hot"\n\nprint(label)\n'
E["c05"] = {"type": "code", "xp": 5, "minLines": 10,
    "starter": 'temperature = 9\n\n# Rewrite the chain using < comparisons, smallest cutoff first.\n\n\n\n\n\n\nprint(label)\n',
    "check": 'import re\nassert ">" not in __source__, "Use only < comparisons."\nassert re.findall(r"<\\s*(\\d+)", __source__) == ["10", "20", "30"], "The tests must run from the smallest cutoff (10) to the largest (30)."',
    "cases": rewrite_cases(c05, [(f"temperature = {t}", [] if t == 9 else [["temperature = 9", f"temperature = {t}"]]) for t in (9, 10, 19, 20, 29, 30)]),
    "answer": b64(c05),
    "answerNote": "With <, start at the lowest upper boundary and move upward."}

E["ex-c06"] = example(E["ex-w01"]["code"] + "\n")
E["c06"] = {"type": "short", "xp": 2, "rows": 5, "placeholder": "member, total → expected discount, one case per line", "answer": b64(
    "One suitable set is (no, 120) → 0.0, (yes, 99) → 0.10, (yes, 100) → 0.10, and (yes, 101) → 0.20. "
    "It reaches every branch and checks both sides of the strict `> 100` boundary.")}

c07 = 'letter = input("Rating letter: ")\nmodifier = input("Modifier (+, -, or none): ")\n\nif letter == "A":\n    value = 4.0\nelif letter == "B":\n    value = 3.0\nelif letter == "C":\n    value = 2.0\nelif letter == "D":\n    value = 1.0\nelse:\n    value = 0.0\n\nif modifier == "+":\n    if letter == "A":\n        value = 4.0\n    else:\n        value = value + 0.3\nelif modifier == "-":\n    value = value - 0.3\n\nprint(f"Numeric value: {value:.1f}")\n'
E["c07"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": 'letter = input("Rating letter: ")\nmodifier = input("Modifier (+, -, or none): ")\n\n# Choose the base value, apply the modifier, and print.\n\n\n\n\n',
    "cases": input_cases(c07, [("B −", ["B", "-"]), ("A +", ["A", "+"]), ("C none", ["C", "none"]), ("A −", ["A", "-"]), ("F +", ["F", "+"]), ("D none", ["D", "none"])]),
    "answer": b64(c07),
    "answerNote": "Use one chain for the base value. Use a second decision for the modifier, with a nested exception for A+."}

c08 = 'number = float(input("Rating number: "))\n\nif number >= 3.5:\n    rating = "Excellent"\nelif number >= 2.5:\n    rating = "Good"\nelif number >= 1.5:\n    rating = "Fair"\nelif number >= 0.5:\n    rating = "Poor"\nelse:\n    rating = "Unacceptable"\n\nprint(rating)\n'
E["c08"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": 'number = float(input("Rating number: "))\n\n# Add one ordered chain and print the rating.\n\n\n\n\n',
    "cases": input_cases(c08, [(v, [v]) for v in ("2.5", "2.49", "4", "3.5", "3.49", "1.5", "0.5", "0.49")]),
    "answer": b64(c08),
    "answerNote": "The halfway boundaries are 3.5, 2.5, 1.5, and 0.5. Test them from largest to smallest so a tie enters the higher band."}

c09 = 'mode_code = input("Mode code: ")\nzone_code = int(input("Zone: "))\n\nif mode_code == "B":\n    mode = "Bus"\nelif mode_code == "F":\n    mode = "Ferry"\nelse:\n    mode = "Rail"\n\nif zone_code == 1:\n    zone = "Zone 1"\nelif zone_code == 2:\n    zone = "Zone 2"\nelse:\n    zone = "Zone 3"\n\nprint(f"{mode}, {zone}")\n'
E["c09"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": 'mode_code = input("Mode code: ")\nzone_code = int(input("Zone: "))\n\n# Translate both parts, then print one description.\n\n\n\n\n',
    "cases": input_cases(c09, [("F 2", ["F", "2"]), ("R 1", ["R", "1"]), ("B 3", ["B", "3"]), ("B 1", ["B", "1"]), ("F 3", ["F", "3"])]),
    "answer": b64(c09),
    "answerNote": "Use one chain to translate the mode and another chain to translate the zone. These are two separate values, so they are two separate decisions."}

c10 = 'month = int(input("Month number: "))\nday = int(input("Day: "))\n\nif month < 3:\n    schedule = "Winter"\nelif month == 3:\n    if day < 15:\n        schedule = "Winter"\n    else:\n        schedule = "Spring"\nelif month < 6:\n    schedule = "Spring"\nelif month == 6:\n    if day < 15:\n        schedule = "Spring"\n    else:\n        schedule = "Summer"\nelif month < 9:\n    schedule = "Summer"\nelif month == 9:\n    if day < 15:\n        schedule = "Summer"\n    else:\n        schedule = "Fall"\nelif month < 12:\n    schedule = "Fall"\nelse:\n    if day < 15:\n        schedule = "Fall"\n    else:\n        schedule = "Winter"\n\nprint(schedule)\n'
E["c10"] = {"type": "code", "xp": 10, "minLines": 14,
    "starter": 'month = int(input("Month number: "))\nday = int(input("Day: "))\n\n# Add the ordered and nested decisions here.\n\n\n\n\n\nprint(schedule)\n',
    "cases": input_cases(c10, [(f"{m} / {d}", [str(m), str(d)]) for m, d in ((3, 14), (3, 15), (6, 14), (6, 15), (9, 14), (9, 15), (12, 14), (12, 15), (1, 20), (7, 4), (11, 30))]),
    "answer": b64(c10),
    "answerNote": "Months strictly between change months need only one assignment. In each change month, nest a test for day 15."}

c11 = 'purchase = float(input("Purchase total: $"))\n\nif purchase >= 200:\n    rate = 0.15\nelif purchase >= 100:\n    rate = 0.10\nelif purchase >= 50:\n    rate = 0.05\nelse:\n    rate = 0.0\n\nvoucher = purchase * rate\nprint(f"Voucher: ${voucher:.2f}")\n'
E["c11"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": 'purchase = float(input("Purchase total: $"))\n\n# Choose one rate, calculate the voucher, and print.\n\n\n\n\n',
    "cases": input_cases(c11, [(f"${v}", [v]) for v in ("49", "200", "100", "50", "199.99", "99.99", "1000")]),
    "answer": b64(c11),
    "answerNote": "Test the largest purchase threshold first. The final else supplies the zero rate."}

c12 = 'kind = input("Enter w or f: ")\nvalue = float(input("Value: "))\n\nif kind == "f":\n    wavelength = 3.0e8 / value\nelse:\n    wavelength = value\n\nif wavelength >= 1.0e-1:\n    band = "Radio"\nelif wavelength >= 1.0e-3:\n    band = "Microwave"\nelse:\n    band = "Shorter wavelength"\n\nprint(band)\n'
E["c12"] = {"type": "code", "xp": 10, "minLines": 12,
    "starter": 'kind = input("Enter w or f: ")\nvalue = float(input("Value: "))\n\n# Convert when needed, then classify the wavelength.\n\n\n\n\n',
    "cases": input_cases(c12, [("f 3e9", ["f", "3e9"]), ("w 0.0005", ["w", "0.0005"]), ("w 0.05", ["w", "0.05"]), ("f 1e10", ["f", "1e10"]), ("w 2", ["w", "2"]), ("f 1e13", ["f", "1e13"])]),
    "answer": b64(c12),
    "answerNote": "Use the first decision to make sure wavelength is in metres. Then classify that one value from the largest cutoff down."}

c13 = 'x = float(input("x: "))\ny = float(input("y: "))\n\nif x == 0:\n    if y == 0:\n        location = "origin"\n    else:\n        location = "vertical axis"\nelif y == 0:\n    location = "horizontal axis"\nelif x > 0:\n    if y > 0:\n        location = "quadrant I"\n    else:\n        location = "quadrant IV"\nelse:\n    if y > 0:\n        location = "quadrant II"\n    else:\n        location = "quadrant III"\n\nprint(location)\n'
E["c13"] = {"type": "code", "xp": 10, "minLines": 14,
    "starter": 'x = float(input("x: "))\ny = float(input("y: "))\n\n# Add the nested decisions and print the location.\n\n\n\n\n',
    "cases": input_cases(c13, [(f"({x}, {y})", [x, y]) for x, y in (("0", "0"), ("-3", "2"), ("4", "0"), ("0", "5"), ("2", "3"), ("-1", "-1"), ("3", "-2"))]),
    "answer": b64(c13),
    "answerNote": "Handle x == 0 first and nest the origin check there. Then handle y == 0. For all remaining points, nest a y test inside the positive-x and negative-x branches."}

for spec in E.values():
    if "starter" in spec:
        spec["starter"] = spec["starter"].rstrip("\n")

data = {
    "id": "lecture-10",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 10 Workbook",
    "subtitle": "Nested branches and elif chains",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-10/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
