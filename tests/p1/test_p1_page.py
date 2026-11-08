"""docs/P1.md's counts of tests and plants, held to the counted ones (P1.2's second verifier, D2: the page said 79 planted
faults and 22 for G11 after round 1 had made them 108 and 31). Every count of planted faults, faults, tests, cases, plants
or controls the page states is checked here against what the tests and the plants hold now, so a count the page adds or
leaves stale fails this file until it is the counted one."""
import re

import test_p1_atlas_generate as atlas_tests
import test_p1_generate as generate_tests
from controls import plants_p1 as plants
from p1_support import ROOT

PAGE = (ROOT / "docs" / "P1.md").read_text(encoding="utf-8")
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "eleven": 11, "twelve": 12}
STATED = re.compile(r"\b([0-9][0-9,]*|" + "|".join(WORDS) + r") (planted faults|faults|tests|cases|plants|controls)\b",
                    re.IGNORECASE)


def counts():
    """{kind of count: the counts the tree holds of it}: the planted faults of the IBM generator's and of Atlas's
    tests, and the controls of the plants."""
    return {"planted faults": {len(generate_tests.CASES), len(atlas_tests.CASES)}, "controls": {len(plants.PLANTS)}}


def test_every_count_of_tests_or_plants_the_page_states_is_the_counted_one():
    found = STATED.findall(PAGE)
    assert found, "the page states no count: this file has lost what it holds"
    held = counts()
    for number, kind in found:
        n = WORDS.get(number.lower()) or int(number.replace(",", ""))
        assert kind.lower() in held, f"the page counts {number} {kind}, and nothing here holds that kind of count"
        assert n in held[kind.lower()], f"the page says {number} {kind}; the tree holds {sorted(held[kind.lower()])}"


def test_the_page_names_the_file_of_each_count_of_planted_faults():
    ibm, atlas = len(generate_tests.CASES), len(atlas_tests.CASES)
    assert (f"(`tests/p1/test_p1_generate.py`, {ibm} planted faults; G11's in `test_p1_atlas_generate.py`, {atlas} "
            "planted faults;") in PAGE
    assert f"the generator on the twin and its {ibm} planted faults (`test_p1_generate.py`)" in PAGE
    assert "seven controls" in PAGE and len(plants.PLANTS) == 7
