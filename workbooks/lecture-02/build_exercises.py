"""Build workbooks/lecture-02/exercises.json.

Lecture 2 has no Python and no checked questions: it is problem solving on
paper. The pizza-payment figures printed in the page are still computed here
(with Decimal, half-cent rounded up, exactly as the lecture states the rules)
and asserted, so the prose cannot drift from the rules. Run from anywhere:

    python3 workbooks/lecture-02/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-02
"""
import json, pathlib
from decimal import Decimal, ROUND_HALF_UP

ROOT = pathlib.Path(__file__).resolve().parents[2]

def cents(amount):
    return int((Decimal(amount) * 100).to_integral_value(ROUND_HALF_UP))

def payment(food, tip, people, delivery="10", tax_rate="0.15"):
    """The lecture's agreed rules, including the smallest tip increase.
    Returns (tax, original bill, final tip, revised bill, payment) in cents."""
    assert people >= 1
    taxable = Decimal(food) + Decimal(delivery)
    tax = cents((taxable * Decimal(tax_rate)).quantize(Decimal("0.01"), ROUND_HALF_UP))
    original = cents(taxable) + tax + cents(tip)
    total, final_tip = original, cents(tip)
    while total % people:
        total += 1
        final_tip += 1
    return tax, original, final_tip, total, total // people

# Worked examples from the lecture body, checked against the printed values.
assert payment("70", "8", 4) == (1200, 10000, 800, 10000, 2500)
assert payment("70", "8", 3) == (1200, 10000, 802, 10002, 3334)
assert payment("70", "8", 1) == (1200, 10000, 800, 10000, 10000)
assert payment("19.99", "0", 1) == (450, 3449, 0, 3449, 3449)
assert payment("19.90", "0", 1)[0] == 449

E = {}

spec = {
    "id": "lecture-02",
    "course": "COMP 1001: Introduction to Programming",
    "title": "Lecture 2 Workbook",
    "subtitle": "Problem Solving",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {out.relative_to(ROOT)} with {len(E)} exercises")
