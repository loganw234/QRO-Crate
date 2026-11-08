"""Section 6.1's 70 certified intervals (P2's design, item 5's comparison; P2.2): ibm_kingston against ibm_fez on v0's IBM
crate, alpha 1/20 over the study's family of 70 (the three law measures on each of the 9 and 11 law jobs and on each
device's pooled day, and the two coherences on each device), computed by P2's `qro-hoeffding-kl/1` from the totals the
crate's raw bytes give. Every figure the study's instrument printed, docs/studies/qro0/isolation_v0.out.txt, is made
again here from P2's intervals, in the instrument's own words and places, and is the same line; and each of the 70
intervals is the instrument's own, which bisects in floats with math.log (its two functions, read from
docs/studies/qro0/isolation_v0.py, run here), to within the grid's step and the two bisections' slack."""
import ast
import math
import re
from fractions import Fraction

import pytest

import p2crates_support as S
from qro import p2_interval

FAMILY, ALPHA = 70, Fraction(1, 20)
A, B = "ibm_kingston", "ibm_fez"
LAW = (("five-crystal share", "n-crystal-share"), ("forbidden share", "forbidden-share"), ("linear XEB", "linear-xeb"))
KEPT = S.ROOT / "docs" / "studies" / "qro0" / "isolation_v0.out.txt"
INSTRUMENT = S.ROOT / "docs" / "studies" / "qro0" / "isolation_v0.py"


@pytest.fixture(scope="module")
def totals():
    """({(device, measure): [(total, shots) of each job]}, the law): each certified measure's per-shot total on each of
    kingston's and fez's law and coherence PUBs, from the crate's raw bytes, as step 6 measures them
    (qro.p2_measures.pub_values)."""
    crate, md = S.built("ibm")[0], S.metadata("ibm")
    law = S.law()
    out = {}
    for (run, _), pub in sorted(S.pubs(md).items()):
        device = run.split("/")[0]
        if device in (A, B):
            for measure, v in S.values(crate, md, pub, law).items():
                if v.mapping is not None:
                    out.setdefault((device, measure), []).append((v.total, v.in_scope))
    return out, law


def interval(total, n):
    return p2_interval.interval(total, n, FAMILY, ALPHA)


def lines(totals):
    """The instrument's lines, its format strings filled from P2's intervals, exact until they are printed."""
    jobs, law = totals
    scale = {"n-crystal-share": Fraction(1), "forbidden-share": Fraction(1),
             "linear-xeb": Fraction(law.w_max, law.den) / law.norm}
    to_measure = {"n-crystal-share": p2_interval.IDENTITY, "forbidden-share": p2_interval.IDENTITY,
                  "linear-xeb": p2_interval.xeb(law.w_max, law.den, law.D, law.norm)}
    out, count = [], 0
    for name, measure in LAW:
        rows = {}
        for device in (A, B):
            each = [interval(t, n) for t, n in jobs[(device, measure)]]
            pooled = p2_interval.pooled(jobs[(device, measure)], FAMILY, ALPHA)
            count += len(each) + 1
            mean = sum((Fraction(t) for t, _ in jobs[(device, measure)]), Fraction(0)) / sum(
                n for _, n in jobs[(device, measure)])
            rows[device] = (mean, pooled, p2_interval.drift(each, pooled), len(each))
        out.append(f"== {name}")
        f = to_measure[measure]
        for device, (mean, pooled, drift, n) in rows.items():
            out.append(f"  {device} ({n} jobs): day mean {float(f(mean)):.4f}, certified [{float(f(pooled[0])):.4f}, "
                       f"{float(f(pooled[1])):.4f}]; drift bound U(D) {float(drift * scale[measure]):.4f}")
        diff = p2_interval.difference(rows[A][1], rows[B][1])
        s = scale[measure]
        out.append(f"  difference ({A} - {B}): certified [{float(diff[0] * s):+.4f}, {float(diff[1] * s):+.4f}]; "
                   f"so the day means differ by at least {float(p2_interval.abs_lower(diff) * s):.4f}")
        strong = p2_interval.strong_form(diff, rows[A][2], rows[B][2])
        out.append(f"  strong form L(|diff|) - U(D_A) - U(D_B) = {float(strong * s):+.4f}: "
                   + ("every job of one device differs from every job of the other by at least that" if strong > 0
                      else "unresolved: the drift bounds are wider than the certified difference"))
    out.append("== coherence: one job a device, so drift is UNMEASURED and the strong form is not available")
    for measure, label in (("x0x1", "<X0X1>"), ("y0y1", "<Y0Y1>")):
        vals = {}
        for device in (A, B):
            (agree, n), = jobs[(device, measure)]
            lo, hi = p2_interval.mapped(interval(agree, n), p2_interval.PARITY)
            mean = p2_interval.PARITY(Fraction(agree, n))
            vals[device] = (lo, hi)
            count += 1
            out.append(f"  {label} {device}: {float(mean):+.4f}, certified [{float(lo):+.4f}, {float(hi):+.4f}]")
        d = p2_interval.difference(vals[A], vals[B])
        out.append(f"  {label} difference: certified [{float(d[0]):+.4f}, {float(d[1]):+.4f}]"
                   + (" (excludes 0)" if d[0] > 0 or d[1] < 0 else " (includes 0: unresolved even before drift)"))
    return out, count


def test_the_family_is_the_studys_70(totals):
    jobs, _ = totals
    assert [len(jobs[(d, m)]) for _, m in LAW for d in (A, B)] == [9, 11] * 3
    assert [len(jobs[(d, m)]) for m in ("x0x1", "y0y1") for d in (A, B)] == [1] * 4
    assert sum(len(v) for v in jobs.values()) + 2 * len(LAW) == FAMILY


def test_every_figure_the_instrument_printed_is_made_again_from_p2s_70_intervals(totals):
    kept = [x for x in KEPT.read_text(encoding="utf-8").splitlines() if x]
    first = re.fullmatch(r"family: ([0-9]+) intervals, alpha ([0-9.]+), each at alpha/M; KL budget ln\(2M/alpha\) = "
                         r"([0-9.]+)", kept[0])
    assert first and (int(first.group(1)), Fraction(first.group(2))) == (FAMILY, ALPHA)
    made, count = lines(totals)
    assert count == FAMILY
    assert made == kept[1:]


def instruments_interval():
    """The instrument's own `kl` and `interval`, read from its source and run here: it refuses to be imported."""
    tree = ast.parse(INSTRUMENT.read_text(encoding="utf-8"))
    body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("kl", "interval")]
    assert [n.name for n in body] == ["kl", "interval"]
    space = {"math": math, "Fraction": Fraction}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(INSTRUMENT), "exec"), space)
    return space["interval"]


def test_each_of_the_70_is_the_instruments_float_interval_to_within_the_grid(totals):
    """The design's item 5 comparison. The instrument returns the last points its float bisection, with math.log,
    judged inside the set; P2's ends are grid points proven outside it in integers (tests/p2/test_p2_interval.py holds
    that). Each of P2's 70 intervals is the instrument's to within the grid's step, 2^-48, and the slack of the two
    bisections: no end is more than 2^-48 + 2e-15 from the other's (the design measured 4.06e-15 at most). Where the
    two differ, P2's end is the certified one: the instrument's rounding puts its ends on either side of the set's."""
    jobs, _ = totals
    float_interval = instruments_interval()
    budget = math.log(2 * FAMILY / float(ALPHA))
    pairs = [tj for v in jobs.values() for tj in v]
    for measure in ("n-crystal-share", "forbidden-share", "linear-xeb"):
        for device in (A, B):
            v = jobs[(device, measure)]
            pairs.append((sum((Fraction(t) for t, _ in v), Fraction(0)), sum(n for _, n in v)))
    assert len(pairs) == FAMILY
    farthest = 0.0
    for total, n in pairs:
        lo, hi = interval(total, n)
        _, flo, fhi = float_interval(total, n, budget)
        farthest = max(farthest, abs(flo - float(lo)), abs(float(hi) - fhi))
    assert 0 < farthest <= 2.0 ** -48 + 2e-15, farthest
