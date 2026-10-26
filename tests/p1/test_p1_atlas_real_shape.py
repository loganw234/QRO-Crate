"""The six real Atlas law results are read whole (the verifier's D1, round 1). Five of the six real results of 2026-09-26
carry a top-level `fetched_at`, which the first build's closed form refused, so the real Atlas crate could not have been
built. The records are the ground truth: the form admits `fetched_at`, holds it to the profile's spelling and reads it for
nothing.

No Moth byte is in this tree. What is held here was measured from the real files, read only: for each of the six, the
number of distinct layouts its all-Z setting holds, and whether it carries `fetched_at`. The bytes the tests read are made
by p1_builder in their shape: nine settings of 4,096 shots, the engine's observables and density matrices, the wrapper's
keys sorted and indented one space as Quantum-Film writes them, and a `fetched_at` of a time made here."""
import json
from pathlib import Path

import pytest
from p1_builder import ALL_Z, GENERATOR, REAL_LABELS, atlas_model, atlas_result_in_real_shape

from qro import canonical, checker, p1_decode, p1_forms

# (the day of the record, the layouts its all-Z setting holds, whether it carries fetched_at), measured from the real files
REAL = (("2026-09-25", 1995, False), ("2026-09-26", 2006, True), ("2026-09-26", 1997, True),
        ("2026-09-26", 2026, True), ("2026-09-26", 2020, True), ("2026-09-26", 2027, True))
IDS = [f"{day}-{layouts}" for day, layouts, _ in REAL]


def made(i, with_fetched_at=True):
    """(the layouts, the bytes) of the i-th real result's shape; `fetched_at` is a time made here, where it carries one."""
    _, layouts, carries = REAL[i]
    stamp = f"2026-09-26T11:4{i}:0{i}Z" if carries and with_fetched_at else None
    return layouts, atlas_result_in_real_shape(layouts, stamp, seed=i)


@pytest.fixture
def loaded(monkeypatch):
    """The registries fresh, P1's declarations loaded as the command line loads them, and a pass-through generator."""
    monkeypatch.setattr(checker, "STEPS", {n: None for n in range(4, 9)})
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    monkeypatch.setattr(checker, "GENERATORS", {GENERATOR: lambda crate: json.loads(
        (Path(crate) / canonical.DESCRIPTOR).read_bytes())})
    monkeypatch.setattr(checker, "COUNTS", [])
    checker.load()


def test_the_six_results_are_the_six_the_records_hold():
    assert len(REAL) == 6 and sum(1 for _, _, carries in REAL if carries) == 5
    assert [layouts for _, layouts, _ in REAL] == [1995, 2006, 1997, 2026, 2020, 2027]


@pytest.mark.parametrize("i", range(len(REAL)), ids=IDS)
def test_each_of_the_six_real_law_results_is_read_whole_in_its_shape(i):
    layouts, data = made(i)
    assert (b'"fetched_at"' in data) == REAL[i][2]
    r = p1_forms.parse_atlas_result(data)
    assert (r.shots, len(r.settings), r.spans, r.first_shot) == (4096, 9, (), None)
    assert set(r.settings) == set(REAL_LABELS) and p1_decode.z_setting(r) == ALL_Z
    layout = p1_decode.atlas_layouts(r)
    assert (len(layout), sum(layout.values())) == (layouts, 4096) and all(len(sites) == 5 for sites in layout)


@pytest.mark.parametrize("i", range(1, len(REAL)), ids=IDS[1:])
def test_fetched_at_is_read_for_nothing(i):
    with_stamp, without = made(i)[1], made(i, with_fetched_at=False)[1]
    assert b'"fetched_at"' in with_stamp and b'"fetched_at"' not in without
    assert p1_forms.parse_atlas_result(with_stamp) == p1_forms.parse_atlas_result(without)


@pytest.mark.parametrize("i", range(len(REAL)), ids=IDS)
def test_the_checker_accepts_an_atlas_crate_whose_law_result_is_in_each_of_the_six_shapes(loaded, tmp_path, i):
    """Step 3 counts its 4,096 shots by the reader, step 5 accounts for it under the rule, and P2's seam, pub_counts,
    gives its layouts back on the metadata the checker returns."""
    layouts, data = made(i)
    crate = atlas_model(law=(data, 4096)).write(tmp_path / "crate")
    md = checker.check(crate)
    assert len(p1_decode.pub_counts(crate, md, "#pub-alaw-0")) == layouts
