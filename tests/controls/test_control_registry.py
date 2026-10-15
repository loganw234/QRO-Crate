"""The controls' registry, walked both ways (ParcelRound, METHOD.md section 2; study QRO-0, section 11):
  - a row of P0's that no plant exercises fails, naming the row;
  - a plant naming no row fails, naming the plant;
  - each built control comes out as its row says, by the refusal's own name;
and the check is shown able to fail. Each row is held to the study's own section 11 table, cell for cell, and
each owner to section 13 where it names one (P0's verifier's notes)."""
import re
from pathlib import Path

import pytest

from controls import registry as R
from controls.run import outcome


def unexercised(controls, plants):
    return sorted(c.name for c in controls if c.owner == "P0" and c.name not in plants)


def orphaned(controls, plants):
    names = {c.name for c in controls}
    return sorted(p for p in plants if p not in names)


def test_every_p0_row_is_exercised_and_every_plant_names_a_row():
    assert unexercised(R.CONTROLS, R.PLANTS) == []
    assert orphaned(R.CONTROLS, R.PLANTS) == []


def test_the_registry_check_can_fail():
    """A dummy row and a dummy plant, each caught by name, then gone."""
    dummy = R.Control("dummy-row", "nothing", "refused", "spelling", "P0", "`spelling`")
    assert unexercised(R.CONTROLS + (dummy,), R.PLANTS) == ["dummy-row"]
    assert orphaned(R.CONTROLS, dict(R.PLANTS, **{"dummy-plant": None})) == ["dummy-plant"]


@pytest.mark.parametrize("name", sorted(R.PLANTS))
def test_each_built_control_comes_out_as_section_11_says(name):
    c = R.CONTROL[name]
    got, refusal, where = outcome(name)
    assert (got, refusal) == (c.expected, c.refusal), f"{got} {refusal} at {where}; section 11 says {c.text}"


STUDY = Path(__file__).resolve().parents[2] / "docs" / "studies" / "QRO-0.md"


def section(text, n):
    return re.search(rf"^## {n}\. .*?(?=^## \d+\. |\Z)", text, re.S | re.M).group(0)


def study_table():
    """Section 11's table, row by row: (control, planted fault, expected), each cell as the study writes it."""
    rows, inside = [], False
    for line in section(STUDY.read_text(encoding="utf-8"), 11).splitlines():
        if line.startswith("| control | planted fault | expected |"):
            inside = True
            continue
        if inside and line.startswith("|---"):
            continue
        if inside and line.startswith("|"):
            rows.append(tuple(c.strip() for c in re.split(r"(?<!\\)\|", line)[1:-1]))
        elif inside:
            break
    return rows


def test_the_registry_is_section_11s_table_cell_for_cell():
    table = study_table()
    assert len(table) == 30
    mine = [(c.name, c.fault, c.text) for c in R.CONTROLS]
    assert mine == [(a, b.replace("\\|", "|"), c.replace("\\|", "|")) for a, b, c in table]


def test_the_owners_are_section_13s_where_it_names_them():
    """Section 13 names some controls with their parcel; every one it names agrees with the registry."""
    s13 = section(STUDY.read_text(encoding="utf-8"), 13)
    parcels = s13.split("**The parcels.**", 1)[1].split("**Who owns each checker step**", 1)[0]
    named = 0
    for block in re.split(r"^- \*\*(?=P\d)", parcels, flags=re.M)[1:]:
        owner = block[:2]
        for name in re.findall(r"`([a-z]+(?:-[a-z]+)+)`", block):
            if name in R.CONTROL:
                named += 1
                assert R.CONTROL[name].owner == owner, f"{name}: section 13 gives it to {owner}"
    assert named >= 10, "section 13 names controls under P1, P2, P3 and P5"


def test_every_row_names_an_owner_and_a_consistent_outcome():
    for c in R.CONTROLS:
        assert c.owner in ("P0", "P1", "P2", "P3", "P4", "P5") and c.text and c.fault, c.name
        assert (c.expected == "refused") or c.refusal is None, c.name


def test_the_study_comparison_can_fail():
    """One cell changed in the registry's copy is caught."""
    table = study_table()
    changed = [(c.name, c.fault + " ", c.text) for c in R.CONTROLS]
    assert changed != [(a, b, c) for a, b, c in table]
