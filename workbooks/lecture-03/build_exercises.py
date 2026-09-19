"""Build workbooks/lecture-03/exercises.json.

Lecture 3 has one supplied Python script, no Python writing and no checked
questions. Every transcript printed on the page is produced by running that
script here and asserted, so the page cannot drift from Python's behaviour.
Run from anywhere:

    python3 workbooks/lecture-03/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-03
"""
import json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def run(code, inputs=()):
    p = subprocess.run([sys.executable, "-c", code], input="\n".join(inputs) + ("\n" if inputs else ""), capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.rstrip("\n")

def example(code, output=True, **kw):
    spec = {"type": "example", "code": code.rstrip("\n"), **kw}
    if output:
        spec["output"] = run(code)
    return spec

E = {}

# ------------------------------------------------- The supplied script
# Byte-for-byte the listing in LECTURE_03_SHARED_CONTENT.tex (also on
# slides 18 and 22). The instructor asked for integer-cent arithmetic
# rather than the decimal module; see the kit's HANDOFF_ISSUES.md.
PIZZA = '''prices = input("Pizza prices: ").split()
tip = float(input("Agreed tip: "))
people = float(input("People: "))
if people < 1 or people != int(people):
    print("Enter a whole number of people"
          " of at least 1")
else:
    people = int(people)
    food = sum(map(float, prices))
    subtotal = round((food + 10) * 100)  # cents
    tax = (subtotal * 15 + 50) // 100  # half-up
    tip = round(tip * 100)
    total = subtotal + tax + tip
    while total % people:
        tip += 1
        total += 1
    print(f"Final tip: CA${tip/100:.2f}")
    print(f"Total: CA${total/100:.2f}")
    print(f"Each: CA${total/people/100:.2f}")
'''
E["ex-pizza"] = example(PIZZA, output=False, title="pizza.py")

def pizza(prices, tip, people):
    """Run the supplied script with these answers; return its result lines.

    With piped stdin the three prompts are printed on the first line with
    no newline after them (IDLE echoes the typed answer instead), so strip
    the prompt text before comparing.
    """
    out = run(PIZZA, [prices, tip, people])
    for prompt in ("Pizza prices: ", "Agreed tip: ", "People: "):
        assert out.startswith(prompt), out
        out = out[len(prompt):]
    return out.split("\n")

# The four Shell interactions printed in the workbook. The page shows them as
# static transcripts; assert here that the script really prints them.
TRANSCRIPTS = {
    "3": ["Final tip: CA$8.02", "Total: CA$100.02", "Each: CA$33.34"],
    "4": ["Final tip: CA$8.00", "Total: CA$100.00", "Each: CA$25.00"],
    "1": ["Final tip: CA$8.00", "Total: CA$100.00", "Each: CA$100.00"],
    "0": ["Enter a whole number of people of at least 1"],
}
for people, expected in TRANSCRIPTS.items():
    got = pizza("25 25 20", "8", people)
    assert got == expected, (people, got)
assert pizza("25 25 20", "8", "2.5") == TRANSCRIPTS["0"]

data = {
    "id": "lecture-03",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 3 Workbook",
    "subtitle": "Algorithms, Pseudocode and Programs",
    "exercises": E,
}
out = ROOT / "workbooks/lecture-03/exercises.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("wrote", out, len(E), "specs")
