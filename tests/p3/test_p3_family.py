"""The family M, `qro-family/1`, is structural (qro/p3_verdicts.py's `family`; P3's design, items 1 and 4, with its
correction 2): counted on hand-worked cases, one member, two, a vacuous one and a refused measure; the record's shape
(which measures are refused, the members, the readout's coverage and M) the same when every count changes; and M fixed
before any value is read, held by a pub_values poisoned until the family is counted."""
from fractions import Fraction

import pytest

import p3_builder as B
import p3_support as S
from qro import p2_interval, p2_measures, p3_compare, p3_verdicts, spelling

T = "2026-11-01T10:"


def crate_of(tmp_path, n_a, n_b, coherence=True, counts=None, name="crate"):
    """Kingston with n_a law jobs and fez with n_b, interleaved minute by minute, each with a coherence job."""
    counts = counts or {}

    def jobs(n, minute, device):
        out = [B.ka(start=f"{T}{minute:02d}:00Z")]
        for i in range(n):
            out.append(B.law(f"law-{i}", start=f"{T}{minute + 2 * i + 1:02d}:00Z", **counts.get((device, i), {})))
        if coherence:
            out.append(B.coherence(start=f"{T}{minute + 40:02d}:00Z", **counts.get((device, "c"), {})))
        return out
    return B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", jobs(n_a, 0, "k")),
                              B.Bundle("ibm_fez", "morning", jobs(n_b, 1, "f"))], name=name)


@pytest.mark.parametrize("n_a, n_b, measures, want", [
    (1, 1, ("n-crystal-share",), 1 + 1),
    (2, 1, ("n-crystal-share",), (1 + 2) + 1),
    (1, 2, ("forbidden-share",), 1 + (1 + 2)),
    (3, 2, ("n-crystal-share", "linear-xeb"), 2 * ((1 + 3) + (1 + 2))),
    (9, 11, S.FIVE, 3 * ((1 + 9) + (1 + 11)) + 2 * (1 + 1)),
], ids=["one member a run", "two and one", "one and two", "three and two, two measures", "v0's kingston and fez: 70"])
def test_m_on_hand_worked_cases(tmp_path, n_a, n_b, measures, want):
    crate = crate_of(tmp_path, n_a, n_b)
    record, _ = S.computed(crate, crate, measures=measures)
    assert record["family"] == want


def test_a_member_with_no_shot_in_scope_stays_counted_and_has_the_vacuous_interval(tmp_path):
    """Fez's second law job holds no five-crystal shot: its forbidden share and XEB have none in scope."""
    crate = crate_of(tmp_path, 2, 2, counts={("f", 1): {"five": 0, "forbidden": 0}})
    record, _ = S.computed(crate, crate, measures=("forbidden-share", "linear-xeb"))
    assert record["family"] == 2 * ((1 + 2) + (1 + 2))
    empty = next(m for m in S.measure(record, "forbidden-share")["b"]["members"] if m["id"] == "ibmfezmorninglaw1")
    assert (empty["inScope"], empty["interval"]) == (0, ["0/1", "1/1"])
    law = B.the_law()
    mapping = p2_interval.xeb(law.w_max, law.den, law.D, law.norm)
    xeb = next(m for m in S.measure(record, "linear-xeb")["b"]["members"] if m["id"] == "ibmfezmorninglaw1")
    assert xeb["interval"] == [spelling.rational(mapping(Fraction(0))), spelling.rational(mapping(Fraction(1)))]


def test_a_refused_measure_counts_nothing(tmp_path):
    crate = crate_of(tmp_path, 2, 3, coherence=False)
    record, facts = S.computed(crate, crate, measures=("n-crystal-share", "x0x1"))
    assert facts["refused"] == 1 and record["family"] == (1 + 2) + (1 + 3)


def shape(record):
    """The record's structure: M, each run's selected jobs, and each measure's refusal, keys, members and readout."""
    out = [record["family"], [[c["jobs"] for c in record["runs"][s]["crates"]] for s in "ab"]]
    for m in record["measures"]:
        out.append((m["measure"], m["refused"], sorted(m),
                    None if m["refused"] != "none" else ([x["id"] for x in m["a"]["members"]],
                                                         [x["id"] for x in m["b"]["members"]], m["readout"])))
    return out


def test_every_count_changed_leaves_the_records_shape_and_m_unchanged(tmp_path):
    """The same jobs, bundles and times with other counts in every raw result: their digests, P2's measurements and
    the values all move, and M, the selected jobs, the refusals, the members and the readout do not."""
    one = crate_of(tmp_path, 3, 2, name="one")
    other = crate_of(tmp_path, 3, 2, name="other", counts={
        **{("k", i): {"five": 20 + i, "forbidden": 1} for i in range(3)},
        **{("f", i): {"five": 60, "forbidden": 9} for i in range(2)}, ("k", "c"): {"agree": 10},
        ("f", "c"): {"agree": 63}})
    assert S.digest_of(one) != S.digest_of(other)
    first, _ = S.computed(one, one)
    second, _ = S.computed(other, other)
    assert shape(first) == shape(second)
    values = [[S.measure(r, m)["a"]["value"] for m in S.FIVE] for r in (first, second)]
    assert values[0] != values[1], "the counts did change the values"


def test_m_is_counted_before_any_value_is_read(tmp_path, monkeypatch):
    crate = crate_of(tmp_path, 2, 2)
    _, decl = S.declare(crate, crate)
    counted, real_family, real_values = [], p3_verdicts.family, p2_measures.pub_values

    def family(*a):
        counted.append(True)
        return real_family(*a)

    def pub_values(*a):
        assert counted, "a value was read before M was counted"
        return real_values(*a)
    monkeypatch.setattr(p3_verdicts, "family", family)
    monkeypatch.setattr(p2_measures, "pub_values", pub_values)
    record, _ = p3_compare.compute(decl, None, S.crates_of(crate))
    assert counted == [True] and record["family"] == 3 * ((1 + 2) + (1 + 2)) + 2 * (1 + 1)


def test_the_poison_is_able_to_fail(tmp_path, monkeypatch):
    """The control of the test above: a pub_values that raises is reached by the computation."""
    crate = crate_of(tmp_path, 1, 1)
    _, decl = S.declare(crate, crate, measures=("n-crystal-share",))

    def poisoned(*a):
        raise AssertionError("a value was read")
    monkeypatch.setattr(p2_measures, "pub_values", poisoned)
    with pytest.raises(AssertionError, match="a value was read"):
        p3_compare.compute(decl, None, S.crates_of(crate))
