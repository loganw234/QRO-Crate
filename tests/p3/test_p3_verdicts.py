"""What a comparison computes for each measure (qro/p3_verdicts.py; P3's design, item 4): every interval P2's
`qro-hoeffding-kl/1` at M and the plan's alpha, mapped, recomputed here from the raw bytes by P2's own functions; the
vacuous interval where no shot is in scope; the difference, the drift bounds and the strong form exact, and UNMEASURED
with one member; and the means at their boundaries."""
from fractions import Fraction

import pytest

import p3_builder as B
import p3_support as S
from qro import p2_interval, p2_measures, p3_verdicts, spelling
from qro.p1_graph import Index

T = "2026-11-01T10:"


@pytest.fixture(scope="module")
def crate(tmp_path_factory):
    d = tmp_path_factory.mktemp("verdicts")
    k = [B.ka(start=f"{T}00:00Z"), B.law("law-0", start=f"{T}01:00Z", five=50, forbidden=2),
         B.law("law-1", start=f"{T}03:00Z", five=44, forbidden=6), B.law("law-2", start=f"{T}05:00Z", five=30),
         B.coherence(start=f"{T}40:00Z", agree=50)]
    f = [B.ka(start=f"{T}00:30Z"), B.law("law-0", start=f"{T}02:00Z", five=20, forbidden=1),
         B.law("law-1", start=f"{T}04:00Z", five=24, forbidden=3), B.coherence(start=f"{T}41:00Z", agree=20)]
    return B.build(d, [B.Bundle("ibm_kingston", "morning", k), B.Bundle("ibm_fez", "morning", f)])


def totals(crate, device, measure):
    """[(job id, total, shots in scope, map)] of each of a device's member jobs, from P2's pub_values directly."""
    md = S.md_of(crate)
    idx = Index(md)
    law = B.the_law()
    out = []
    for job in sorted(idx.of_type("qro:Job"), key=lambda j: j["qro:jobId"]):
        if idx.one(job, "qro:device")["name"] != device:
            continue
        for pub in idx.pubs_of(job):
            if pub["qro:role"] not in ("law", "coherence"):
                continue
            values = p2_measures.pub_values(crate, md, pub, law)
            if measure in values:
                v = values[measure]
                out.append((job["qro:jobId"], v.total, v.in_scope, v.mapping))
    return out


def iv(total, n, M, alpha, mapping):
    return p2_interval.mapped(p2_interval.interval(total, n, M, alpha), mapping)


@pytest.mark.parametrize("measure", S.FIVE)
@pytest.mark.parametrize("alpha", ["1/20", "1/10"])
def test_every_interval_is_p2s_at_m_and_alpha_mapped_from_the_raw_bytes(crate, measure, alpha):
    record, _ = S.computed(crate, crate, alpha=alpha)
    M, a = record["family"], Fraction(alpha)
    assert M == 3 * ((1 + 3) + (1 + 2)) + 2 * (1 + 1)
    m = S.measure(record, measure)
    pooled = {}
    for side, device in (("a", "ibm_kingston"), ("b", "ibm_fez")):
        jobs = totals(crate, device, measure)
        total, n = sum((t for _, t, _, _ in jobs), Fraction(0)), sum(k for _, _, k, _ in jobs)
        pooled[side] = iv(total, n, M, a, jobs[0][3])
        assert m[side]["interval"] == [spelling.rational(x) for x in pooled[side]]
        assert m[side]["inScope"] == n and m[side]["value"] == spelling.rational(jobs[0][3](Fraction(total) / n))
        each = [iv(t, k, M, a, mp) for _, t, k, mp in jobs] if len(jobs) > 1 else [pooled[side]]
        assert [x["interval"] for x in m[side]["members"]] == [[spelling.rational(y) for y in e] for e in each]
        assert [x["id"] for x in m[side]["members"]] == [j for j, _, _, _ in jobs]
        drift = p2_interval.drift(each, pooled[side]) if len(jobs) > 1 else None
        assert m[side]["drift"] == ("none" if drift is None else spelling.rational(drift))
    diff = p2_interval.difference(pooled["a"], pooled["b"])
    assert m["difference"] == [spelling.rational(x) for x in diff]
    if m["a"]["drift"] != "none" and m["b"]["drift"] != "none":
        sf = p2_interval.strong_form(diff, Fraction(m["a"]["drift"]), Fraction(m["b"]["drift"]))
        assert m["strongForm"] == spelling.rational(sf)
    else:
        assert m["strongForm"] == "none" and m["causes"]["drift"] == "UNMEASURED"


def test_a_smaller_alpha_widens_every_interval(crate):
    wide, _ = S.computed(crate, crate, alpha="1/20")
    narrow, _ = S.computed(crate, crate, alpha="1/10")
    for m in S.FIVE:
        w, n = (S.measure(r, m)["a"]["interval"] for r in (wide, narrow))
        assert Fraction(w[0]) <= Fraction(n[0]) and Fraction(n[1]) <= Fraction(w[1]) and w != n, m


def test_the_vacuous_interval_is_the_maps_image_of_zero_and_one():
    for mapping in (p2_interval.IDENTITY, p2_interval.PARITY, p2_interval.xeb(9, 4096, 4368, Fraction(1, 3))):
        assert p3_verdicts.interval(Fraction(0), 0, 70, Fraction(1, 20), mapping) == (mapping(Fraction(0)),
                                                                                       mapping(Fraction(1)))
    assert p3_verdicts.interval(Fraction(0), 0, 70, Fraction(1, 20), p2_interval.PARITY) == (-1, 1)


def test_a_run_of_one_member_has_its_pooled_interval_and_no_drift():
    tallies = [("j1", Fraction(30), 64, p2_interval.IDENTITY)]
    got = p3_verdicts.run_of(tallies, 10, Fraction(1, 20))
    assert got["drift"] is None and got["members"] == [("j1", 64, got["interval"])]
    assert got["interval"] == p2_interval.interval(Fraction(30), 64, 10, Fraction(1, 20))


def test_a_run_of_two_members_has_p2s_drift_bound():
    tallies = [("j1", 30, 64, p2_interval.IDENTITY), ("j2", Fraction(50), 64, p2_interval.IDENTITY)]
    got = p3_verdicts.run_of(tallies, 10, Fraction(1, 20))
    each = [p2_interval.interval(30, 64, 10, Fraction(1, 20)), p2_interval.interval(50, 64, 10, Fraction(1, 20))]
    assert [iv for _, _, iv in got["members"]] == each
    assert got["drift"] == p2_interval.drift(each, got["interval"]) and got["value"] == Fraction(80, 128)


@pytest.mark.parametrize("total", [0.5, True, "1/2", None])
def test_a_total_that_is_no_whole_number_or_fraction_is_refused_before_it_is_summed(total):
    v = p2_measures.Value("x0x1", 4, Fraction(1, 2), total, p2_interval.PARITY)
    with pytest.raises(p3_verdicts.ValueProblem):
        p3_verdicts.total_of([v])


def test_two_pubs_of_one_job_on_two_maps_are_refused():
    a = p2_measures.Value("linear-xeb", 4, Fraction(1), 2, p2_interval.IDENTITY)
    b = p2_measures.Value("linear-xeb", 4, Fraction(1), 2, p2_interval.PARITY)
    with pytest.raises(p3_verdicts.ValueProblem):
        p3_verdicts.total_of([a, b])
    assert p3_verdicts.total_of([a, a]) == (4, 8, p2_interval.IDENTITY)


@pytest.mark.parametrize("diff, epsilon, want", [
    ((Fraction(1, 10), Fraction(2, 10)), Fraction(1, 10), "unresolved"),
    ((Fraction(1, 10), Fraction(2, 10)), Fraction(99, 1000), "differ"),
    ((Fraction(-2, 10), Fraction(-1, 10)), Fraction(1, 10), "unresolved"),
    ((Fraction(-2, 10), Fraction(-1, 10)), Fraction(99, 1000), "differ"),
    ((Fraction(-1, 10), Fraction(1, 20)), Fraction(1, 10), "agree"),
    ((Fraction(-1, 10), Fraction(1, 20)), Fraction(99, 1000), "unresolved"),
    ((Fraction(-1, 20), Fraction(1, 10)), Fraction(1, 10), "agree"),
    ((Fraction(0), Fraction(0)), Fraction(0), "agree"),
    ((Fraction(-1, 10), Fraction(1, 10)), Fraction(0), "unresolved"),
    ((Fraction(1, 10**9), Fraction(1, 10)), Fraction(0), "differ")],
    ids=["L equal to epsilon is not differ", "L just above it is", "the same below zero", "and differ below zero",
         "U equal to epsilon is agree", "U just above it is not", "U at the other end", "a point at zero, epsilon 0",
         "across zero at epsilon 0", "just above zero at epsilon 0"])
def test_the_means_at_their_boundaries(diff, epsilon, want):
    assert p3_verdicts.means(diff, epsilon) == want


def test_abs_upper_is_the_larger_end_in_size():
    assert p3_verdicts.abs_upper((Fraction(-3), Fraction(2))) == 3
    assert p3_verdicts.abs_upper((Fraction(1), Fraction(2))) == 2
