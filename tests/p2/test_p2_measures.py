"""The measures of a PUB (P2's design, item 1): each estimator against values worked by hand, and against the law's own
expected values on the law's own table and on the uniform one; the cases with no value; the bases each role is read
in; outcomes off the tile; the family and the intervals; the entities' spellings; and `measurements(md)`, read back
from a written crate."""
from fractions import Fraction

import pytest
from p2_builder import SMALL_LAW_COUNTS, SMALL_XX, SMALL_YY, read_md, small_law_bytes, small_model

from qro import p2_interval, p2_law, p2_measures
from qro.p2_measures import MeasureError

F = Fraction


def v0():
    return p2_law.read(p2_law.law_bytes())


def small():
    return p2_law.read(small_law_bytes())


def values(counts, law, basis=None, names=p2_measures.LAW_MEASURES):
    return {m: p2_measures.value(m, counts, law, basis) for m in names}


# -- by hand -----------------------------------------------------------------------------------------------------------
def test_the_law_measures_of_the_small_law_pub_worked_by_hand():
    """40 shots, 38 of two crystals; layouts (0,1) and (2,3) weigh 0 of 10, (0,2) and (0,3) 4, (1,2) and (1,3) 1."""
    got = values(SMALL_LAW_COUNTS, small())
    assert (got["n-crystal-share"].value, got["n-crystal-share"].in_scope) == (F(38, 40), 40)
    assert (got["forbidden-share"].value, got["forbidden-share"].in_scope) == (F(2 + 1, 38), 38)
    s = 15 * 4 + 13 * 4 + 4 * 1 + 3 * 1                         # sum of w(Y) over the two-crystal shots: 119
    D, sum_p2 = 6, F(4 ** 2 + 4 ** 2 + 1 + 1, 10 ** 2)
    assert got["linear-xeb"].value == (D * F(s, 38 * 10) - 1) / (D * sum_p2 - 1) == F(835, 988)
    tvd = F(abs(20 - 0) + abs(150 - 152) + abs(130 - 152) + abs(40 - 38) + abs(30 - 38) + abs(10 - 0), 2 * 38 * 10)
    assert got["tvd"].value == tvd == F(8, 95) and got["tvd"].in_scope == 38
    # the 2 x 2 torus's neighbour pairs (0,1), (0,2), (1,3), (2,3); occupations 32, 10, 21, 17 of 40
    nn = (F(3 * 40, 32 * 10) + F(16 * 40, 32 * 21) + F(3 * 40, 10 * 17) + F(1 * 40, 21 * 17)) / 4
    assert got["nn-pair-correlation"].value == nn == F(6127, 11424)
    assert small().nn_pairs == ((0, 1), (0, 2), (1, 3), (2, 3))


def test_the_coherence_measures_worked_by_hand():
    xx = p2_measures.value("x0x1", SMALL_XX, small(), "XXZZ")
    assert (xx.value, xx.in_scope, xx.total) == (F(2 * 36 - 40, 40), 40, 36)
    yy = p2_measures.value("y0y1", SMALL_YY, small(), "YYZZ")
    assert (yy.value, yy.in_scope, yy.total) == (F(2 * 35 - 40, 40), 40, 35)
    assert xx.mapping == yy.mapping == p2_interval.PARITY


@pytest.mark.parametrize("twin", ["law", "uniform"])
def test_on_a_tables_own_counts_each_measure_is_that_tables_expected_value(twin):
    """Counts proportional to the law's table give the law's expected values exactly; one shot of every layout gives
    the uniform twin's: the estimators and p2_law.expected agree on v0."""
    law = v0()
    weights = law.weights if twin == "law" else (1,) * law.D
    counts = {Y: w for Y, w in zip(law.layouts, weights) if w}
    got = values(counts, law)
    want = p2_law.expected(p2_law.model_of(twin, law), law)
    for m in p2_measures.LAW_MEASURES:
        assert got[m].value == want[m], m


# -- no value ----------------------------------------------------------------------------------------------------------
def test_a_domain_with_no_shot_has_no_value():
    law = small()
    for m, v in values({}, law).items():
        assert v.value is None and v.in_scope == 0, m
    assert p2_measures.value("x0x1", {}, law, "XXZZ").value is None
    no_pairs = values({(0,): 3, (0, 1, 2): 1}, law)
    assert no_pairs["n-crystal-share"].value == 0 and no_pairs["n-crystal-share"].in_scope == 4
    for m in ("forbidden-share", "linear-xeb", "tvd"):
        assert no_pairs[m].value is None and no_pairs[m].in_scope == 0, m


def test_the_pair_correlation_has_no_value_where_a_neighbour_site_is_never_occupied():
    got = values({(0, 2): 5, (0, 3): 5}, small())
    assert got["nn-pair-correlation"].value is None and got["nn-pair-correlation"].in_scope == 10
    assert got["n-crystal-share"].value == 1


def test_neighbours_that_never_meet_correlate_0():
    """Every site occupied 5 of 10 times, and only the pairs (0,3) and (1,2), no neighbours, ever together."""
    got = values({(0, 3): 5, (1, 2): 5}, small())
    assert got["nn-pair-correlation"].value == 0


# -- bases and outcomes ------------------------------------------------------------------------------------------------
def test_each_role_is_read_in_its_basis():
    law = small()
    assert p2_measures.measures_of("law", "ZZZZ", law) == p2_measures.LAW_MEASURES
    assert p2_measures.measures_of("law", None, law) == p2_measures.LAW_MEASURES
    assert p2_measures.measures_of("coherence", "XXZZ", law) == ("x0x1",)
    assert p2_measures.measures_of("coherence", "YYZZ", law) == ("y0y1",)
    for role, basis, reason in (("law", "XZZZ", "read in Z on all 4 qubits"), ("law", "ZZZ", "read in Z"),
                                ("coherence", None, "states its basis"), ("coherence", "XYZZ", "exactly two"),
                                ("coherence", "ZZXX", "reads X2X3, which qro-measures/1 does not measure"),
                                ("known-answer", "ZZZZ", "is not measured")):
        with pytest.raises(MeasureError, match=reason):
            p2_measures.measures_of(role, basis, law)


@pytest.mark.parametrize("counts", [{(4,): 1}, {(-1,): 1}, {(1, 0): 1}, {(1, 1): 1}, {(0,): 0}, {(0,): True},
                                    {(0,): 1.0}, {(True,): 1}, {"01": 1}])
def test_an_outcome_off_the_tile_or_a_count_that_is_no_count_is_a_measure_error(counts):
    with pytest.raises(MeasureError):
        p2_measures._held(counts, small())


def test_a_measure_with_no_per_pub_value_is_a_measure_error():
    with pytest.raises(MeasureError, match="no per-PUB value"):
        p2_measures.value("pair-occupations", SMALL_LAW_COUNTS, small())


# -- the family and the intervals --------------------------------------------------------------------------------------
def test_the_family_counts_the_certified_values_and_each_interval_is_mapped():
    law = small()
    got = {("#pub-a-0", m): v for m, v in values(SMALL_LAW_COUNTS, law).items()}
    got[("#pub-b-0", "x0x1")] = p2_measures.value("x0x1", SMALL_XX, law, "XXZZ")
    got[("#pub-c-0", "n-crystal-share")] = p2_measures.value("n-crystal-share", {}, law)       # no value: no interval
    family, bounds = p2_measures.certify(got)
    assert family == 4 and sorted(bounds) == sorted([("#pub-a-0", "n-crystal-share"), ("#pub-a-0", "forbidden-share"),
                                                     ("#pub-a-0", "linear-xeb"), ("#pub-b-0", "x0x1")])
    xeb = got[("#pub-a-0", "linear-xeb")]
    assert xeb.total == F(119, 4)
    assert bounds[("#pub-a-0", "linear-xeb")] == p2_interval.mapped(p2_interval.interval(F(119, 4), 38, 4),
                                                                    p2_interval.xeb(4, 10, 6, law.norm))
    lo, hi = bounds[("#pub-b-0", "x0x1")]
    assert (lo, hi) == p2_interval.mapped(p2_interval.interval(36, 40, 4), p2_interval.PARITY) and lo < F(4, 5) < hi
    for k, (lo, hi) in bounds.items():
        assert lo <= got[k].value <= hi, k


# -- the entities ------------------------------------------------------------------------------------------------------
def test_a_measurement_entitys_spelling():
    v = p2_measures.Value("linear-xeb", 38, F(835, 988), F(119, 4), None)
    assert p2_measures.measurement_entity("#pub-joblaw-0", v, (F(-1, 3), F(5, 4))) == {
        "@id": "#measurement-joblaw-0-linear-xeb", "@type": "qro:Measurement", "qro:measure": "linear-xeb",
        "qro:measuredPub": {"@id": "#pub-joblaw-0"}, "qro:inScope": 38, "qro:value": "835/988", "qro:lower": "-1/3",
        "qro:upper": "5/4"}
    none = p2_measures.measurement_entity("#pub-joblaw-0", p2_measures.Value("tvd", 0, None, None, None), None)
    assert none["qro:value"] == "none" and "qro:lower" not in none and "qro:upper" not in none
    with pytest.raises(MeasureError, match="#pub-"):
        p2_measures.measurement_entity("#job-x", v, None)


def test_a_contrast_entitys_spelling():
    got = p2_law.classes(small())
    assert p2_measures.contrast_entity(got[("x0x1", "uniform")]) == {
        "@id": "#contrast-x0x1-uniform", "@type": "qro:Contrast", "qro:measure": "x0x1", "qro:twin": "uniform",
        "qro:class": "signal", "qro:lawValue": "4/5", "qro:twinValue": "0/1"}
    assert p2_measures.contrast_entity(got[("pair-occupations", "dephased")]) == {
        "@id": "#contrast-pair-occupations-dephased", "@type": "qro:Contrast", "qro:measure": "pair-occupations",
        "qro:twin": "dephased", "qro:class": "integrity"}


def test_measurements_reads_a_written_crates_values(tmp_path):
    crate = small_model().write(tmp_path / "crate")
    got = p2_measures.measurements(read_md(crate))
    assert sorted(got) == sorted([("#pub-jobcoh-0", "x0x1"), ("#pub-jobcoh-1", "y0y1")] +
                                 [("#pub-joblaw-0", m) for m in p2_measures.LAW_MEASURES])
    assert got[("#pub-joblaw-0", "linear-xeb")]["value"] == F(835, 988)
    assert got[("#pub-joblaw-0", "tvd")] == {"in_scope": 38, "value": F(8, 95), "lower": None, "upper": None}
    x = got[("#pub-jobcoh-0", "x0x1")]
    assert x["value"] == F(4, 5) and x["lower"] < x["value"] < x["upper"] and x["in_scope"] == 40


def test_measurements_reads_the_absence_word_none_as_no_value():
    """A Measurement whose domain held no shot says `none`, and reads back as None with no interval (the first
    verifier's gap: a reader that took `none` for a rational survived, no crate tried holding one)."""
    md = {"@graph": [{"@id": "#measurement-x-0-tvd", "@type": "qro:Measurement", "qro:measure": "tvd",
                      "qro:measuredPub": {"@id": "#pub-x-0"}, "qro:inScope": 0, "qro:value": "none"},
                     {"@id": "#measurement-x-0-n-crystal-share", "@type": "qro:Measurement",
                      "qro:measure": "n-crystal-share", "qro:measuredPub": {"@id": "#pub-x-0"}, "qro:inScope": 3,
                      "qro:value": "0/1", "qro:lower": "0/1", "qro:upper": "1/2"}]}
    assert p2_measures.measurements(md) == {
        ("#pub-x-0", "tvd"): {"in_scope": 0, "value": None, "lower": None, "upper": None},
        ("#pub-x-0", "n-crystal-share"): {"in_scope": 3, "value": F(0), "lower": F(0), "upper": F(1, 2)}}


def test_pub_values_reads_the_counts_from_the_raw_bytes(tmp_path):
    crate = small_model().write(tmp_path / "crate")
    md = read_md(crate)
    pub = next(e for e in md["@graph"] if e["@id"] == "#pub-joblaw-0")
    assert p2_measures.pub_values(crate, md, pub, small()) == values(SMALL_LAW_COUNTS, small())
