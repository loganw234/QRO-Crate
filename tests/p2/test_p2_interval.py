"""Certified intervals rounded outward in integer arithmetic (P2's design, item 5): each rounding held to its exact
rational, term by term, at 2^-12, 2^-64 and 2^-128; the enclosure against an 80-digit decimal oracle; each end of an
interval proven outside the KL set and the grid point past it inside; the edges; golden integers and dyadic
endpoints, the design's measured difference among them; and the exact functions after the one inversion."""
import random
import re
from decimal import Context
from fractions import Fraction

import pytest

from qro import p2_interval
from qro.p2_interval import Enclosure

F = Fraction
ORACLE = Context(prec=80)
SLACK = F(1, 10 ** 70)          # the oracle's own rounding, at 80 digits, far below 2^-128


def oracle_ln(q):
    return F(ORACLE.ln(ORACLE.divide(q.numerator, q.denominator)))


def oracle_kl(p, q):
    out = F(0)
    if p > 0:
        out += p * oracle_ln(p / q)
    if p < 1:
        out += (1 - p) * oracle_ln((1 - p) / (1 - q))
    return out


def zs(seed):
    """Arguments z = num / den of 2 atanh: the edges 0 and 1/3, near them, and random ones in [0, 1/3]."""
    rng = random.Random(seed)
    out = [(0, 1), (1, 3), (1, 7), (333, 1000), (10 ** 20 - 1, 3 * 10 ** 20), (1, 10 ** 30)]
    for _ in range(40):
        den = rng.randint(2, 10 ** rng.randint(1, 15))
        out.append((rng.randint(0, den // 3), den))
    return out


@pytest.mark.parametrize("precision, terms", [(12, 0), (12, 3), (12, 41), (64, 5), (64, 41), (128, 41), (128, 80)])
def test_each_rounded_quantity_of_the_series_is_on_its_side_of_its_exact_rational_term_by_term(precision, terms):
    E = Enclosure(precision, terms)
    S = E.S
    for num, den in zs(precision * 1000 + terms):
        z = F(num, den)
        st = E.steps(num, den)
        zl, zh = st["z"]
        assert zl <= z * S <= zh and zh - zl <= 1
        z2l, z2h = st["z2"]
        assert z2l <= z * z * S <= z2h
        assert len(st["terms"]) == terms
        t, exact_partial, lo_partial, hi_partial = z * S, F(0), 0, 0       # t = z^(2k+1) S, exactly
        for k, (tl, th, ql, qh) in enumerate(st["terms"]):
            d = 2 * k + 1
            assert tl <= t <= th, (k, "the power")
            assert ql <= t / d <= qh, (k, "the term")
            assert ql == tl // d and qh == -(-th // d), (k, "the term is the power's floor and ceiling over 2k+1")
            exact_partial += t / d
            lo_partial += ql
            hi_partial += qh
            assert lo_partial <= exact_partial <= hi_partial, (k, "the partial sum")
            t *= z * z
        tl, th = st["last"]
        assert tl <= t <= th, "the power after the last term"
        rest_bound = t / ((2 * terms + 1) * (1 - z * z))      # sum over k >= K of z^(2k+1) S / (2k+1) is at most this
        assert st["tail"] >= rest_bound, "the tail's bound is at or above the rest of the series"
        lo, hi = st["bounds"]
        assert (lo, hi) == (2 * lo_partial, 2 * (hi_partial + st["tail"]))
        assert lo <= 2 * exact_partial <= 2 * (exact_partial + rest_bound) <= hi


@pytest.mark.parametrize("precision", [12, 64, 96, 128])
def test_the_enclosure_holds_ln_against_an_80_digit_decimal_oracle(precision):
    E = Enclosure(precision)
    rng = random.Random(precision)
    cases = [(1, 1), (2, 1), (1, 2), (3, 2), (2, 3), (10 ** 30 + 1, 10 ** 30), (1, 10 ** 18), (10 ** 18, 7)]
    for _ in range(500):
        kind = rng.randrange(3)
        if kind == 0:
            a, b = rng.randint(1, 10 ** 12), rng.randint(1, 10 ** 12)
        elif kind == 1:                                  # near 1
            b = rng.randint(10 ** 6, 10 ** 15)
            a = b + rng.randint(-10, 10)
        else:                                            # near the reduction's ends: y close to 1 or to 2
            e = rng.randint(0, 60)
            b = rng.randint(1, 10 ** 9)
            a = max(1, (b << e) + rng.randint(-3, 3))
        cases.append((a, b))
    for a, b in cases:
        lo, hi = E.ln(a, b)
        x = oracle_ln(F(a, b))
        assert F(lo, E.S) <= x + SLACK and x - SLACK <= F(hi, E.S), (a, b)
        assert hi - lo <= 3 * (E.terms + 4) * (abs(a.bit_length() - b.bit_length()) + 2), (a, b, hi - lo)


def test_ln_2_is_enclosed_and_tight_at_every_precision_used():
    for precision in (12, 64, 128):
        E = Enclosure(precision)
        lo, hi = E.ln2
        x = oracle_ln(F(2))
        assert F(lo, E.S) <= x <= F(hi, E.S) and hi - lo <= 2 * (E.terms + 4)


def test_the_default_enclosures_integers_are_the_same_on_every_host():
    """Golden integers in units of 2^-128: ln 2, and the budget's upper end ln(2 M / alpha) at M = 70 and 5."""
    E = p2_interval.enclosure()
    assert (E.precision, E.terms) == (128, 41)
    assert E.ln2 == (235865763225513294137944142764154484360, 235865763225513294137944142764154484446)
    assert p2_interval.budget_upper(70, F(1, 20)) == 2700948648748810900927881050341812871468
    assert p2_interval.budget_upper(5, F(1, 20)) == 1802923974187279427748621108171049224566


def test_kl_lower_is_below_kl_on_every_pair_tried():
    rng = random.Random(5)
    E = p2_interval.enclosure()
    for _ in range(400):
        n = rng.randint(1, 30000)
        p = F(rng.randint(0, n), n)
        q = F(rng.randint(1, 2 ** 20 - 1), 2 ** 20)
        assert F(p2_interval.kl_lower(p, q, E), E.S) <= oracle_kl(p, q) + SLACK, (p, q)


def test_the_budget_is_bounded_from_above_and_tightly():
    E = p2_interval.enclosure()
    for M, alpha in ((1, F(1, 20)), (70, F(1, 20)), (99, F(1, 20)), (5, F(1, 3))):
        x = oracle_ln(F(2 * M) / alpha)
        assert x <= F(p2_interval.budget_upper(M, alpha, E), E.S) <= x + F(1, 2 ** 110)


CASES = [(14979, 24576, 70), (0, 24576, 70), (24576, 24576, 70), (1, 1, 1), (0, 1, 1), (7, 13, 2), (412, 1024, 99),
         (F(5236, 9), 1500, 5), (1, 100000, 3), (99999, 100000, 3)]


def assert_certified(total, n, family, bounds, tight=True):
    """Each end is a grid point proven outside {mu : n kl(p, mu) <= B} (or 0 or 1), by the oracle; with `tight`, two
    grid points inward is inside."""
    alpha = F(1, 20)
    L, U = bounds
    p, G = F(total) / n, F(1, 1 << p2_interval.GRID)
    B = oracle_ln(F(2 * family) / alpha)
    assert L <= p <= U
    assert (L * (1 << 48)).denominator == 1 and (U * (1 << 48)).denominator == 1, "on the grid j / 2^48"
    if L > 0:
        assert n * oracle_kl(p, L) > B, "the lower end is outside the set: certified"
        if tight and L + 2 * G < p:
            assert n * oracle_kl(p, L + 2 * G) <= B, "two grid points inward is inside: tight"
    elif tight:
        assert p == 0 or n * oracle_kl(p, 2 * G) <= B
    if U < 1:
        assert n * oracle_kl(p, U) > B
        if tight and U - 2 * G > p:
            assert n * oracle_kl(p, U - 2 * G) <= B
    elif tight:
        assert p == 1 or n * oracle_kl(p, 1 - 2 * G) <= B


@pytest.mark.parametrize("total, n, family", CASES)
def test_each_end_is_proven_outside_the_kl_set_and_the_grid_point_past_it_is_inside(total, n, family):
    assert_certified(total, n, family, p2_interval.interval(total, n, family, F(1, 20)))


def proven_outside(total, n, family, q):
    """The rule's own test of a point, from the module's public parts: n kl_lo(p, q) > B_hi, in integers."""
    E = p2_interval.enclosure()
    return n * p2_interval.kl_lower(F(total) / n, q, E) > p2_interval.budget_upper(family, F(1, 20), E)


def test_each_end_is_the_last_grid_point_proven_outside_the_next_one_inward_is_not():
    rng = random.Random(11)
    cases = CASES + [(rng.randint(0, n), n, rng.randint(1, 99)) for n in (rng.randint(1, 50000) for _ in range(30))]
    G = F(1, 1 << p2_interval.GRID)
    for total, n, family in cases:
        L, U = p2_interval.interval(total, n, family)
        p = F(total) / n
        if L > 0:
            assert proven_outside(total, n, family, L), (total, n, family)
            assert L + G >= p or not proven_outside(total, n, family, L + G), (total, n, family)
        if U < 1:
            assert proven_outside(total, n, family, U), (total, n, family)
            assert U - G <= p or not proven_outside(total, n, family, U - G), (total, n, family)


def test_the_edges_p_0_p_1_and_one_shot():
    assert p2_interval.interval(0, 24576, 70)[0] == 0
    assert p2_interval.interval(24576, 24576, 70)[1] == 1
    L, U = p2_interval.interval(1, 1, 1)
    assert U == 1 and 0 < L < 1
    L, U = p2_interval.interval(0, 1, 1)
    assert L == 0 and 0 < U < 1


GOLDEN = {(14979, 24576, 70): (F(42013843293343, 70368744177664), F(87517217359637, 140737488355328)),
          (131765, 221184, 70): (F(166510370401235, 281474976710656), F(168850823495361, 281474976710656)),
          (147047, 270336, 70): (F(76015589671257, 140737488355328), F(38544939548921, 70368744177664))}


@pytest.mark.parametrize("args", sorted(GOLDEN))
def test_golden_dyadic_endpoints_are_the_same_on_every_host(args):
    assert p2_interval.interval(*args) == GOLDEN[args]


def test_the_designs_measured_certified_difference_kingston_less_fez_is_reproduced():
    """P2's design (item 5, MEASURED by certified.py, a prototype on the same algorithm): kingston's pooled five-crystal
    share (131,765 of 221,184 shots, its 9 law PUBs) less fez's (147,047 of 270,336, its 11), at family 70, is
    [12330612205551 / 2^48, 16819644152847 / 2^48]: the study's [+0.0438, +0.0598]."""
    G = 1 << 48
    k = p2_interval.pooled([(131765, 221184)], 70)
    f = p2_interval.pooled([(147047, 270336)], 70)
    assert p2_interval.difference(k, f) == (F(12330612205551, G), F(16819644152847, G))
    assert round(F(12330612205551, G), 4) == F(438, 10000) and round(F(16819644152847, G), 4) == F(598, 10000)


@pytest.mark.parametrize("precision, terms", [(24, 3), (16, 0), (128, 0)])
def test_any_enclosure_is_sound_a_coarse_one_costs_only_tightness(precision, terms):
    """TERMS buys tightness, never soundness: with a coarse enclosure, or none of the series at all, every end is still
    proven outside the set, and the interval holds the default one."""
    E = Enclosure(precision, terms)
    wider = 0
    for total, n, family in CASES:
        fine = p2_interval.interval(total, n, family)
        coarse = p2_interval.interval(total, n, family, E=E)
        assert_certified(total, n, family, coarse, tight=False)
        assert coarse[0] <= fine[0] and fine[1] <= coarse[1]
        wider += coarse != fine
    assert wider, "the enclosure handed in is the one used: a coarse one widens some interval"


@pytest.mark.parametrize("args, error, reason", [
    ((1.5, 10, 1), TypeError, "never a float"), ((True, 10, 1), TypeError, "never a float"),
    ((11, 10, 1), ValueError, "lies in [0, n]"), ((-1, 10, 1), ValueError, "lies in [0, n]"),
    ((F(21, 2), 10, 1), ValueError, "lies in [0, n]"), ((1, 0, 1), ValueError, "a positive whole number of shots"),
    ((1, True, 1), ValueError, "a positive whole number of shots"),
    ((1, 10, 0), ValueError, "a positive whole number of intervals"),
    ((1, 10, 1.0), ValueError, "a positive whole number of intervals")])
def test_an_interval_refuses_what_is_no_mean_of_variables_in_0_1(args, error, reason):
    with pytest.raises(error, match=re.escape(reason)):
        p2_interval.interval(*args)


@pytest.mark.parametrize("alpha", [F(0), F(1), 0.05, F(3, 2)])
def test_alpha_is_a_fraction_strictly_between_0_and_1(alpha):
    with pytest.raises(ValueError, match=re.escape("alpha is a Fraction in (0, 1)")):
        p2_interval.interval(1, 10, 1, alpha)


def test_an_enclosure_refuses_arguments_outside_its_range():
    E = Enclosure(12)
    for args in ((1, 2), (-1, 3), (1, 0), (1.0, 3)):
        with pytest.raises(ValueError, match=re.escape("2 atanh(z) is enclosed for z = num / den in [0, 1/3]")):
            E.atanh2(*args)
    for args in ((0, 1), (1, 0), (1.0, 1)):
        with pytest.raises(ValueError, match="ln is enclosed for a / b with a and b positive whole numbers"):
            E.ln(*args)
    for args in ((3, 5), (True, 41), (128, -1)):
        with pytest.raises(ValueError, match="a whole precision of at least 4 bits"):
            Enclosure(*args)
    for p, q in ((F(1, 2), F(0)), (F(1, 2), F(1)), (F(1, 2), F(3, 2)), (F(3, 2), F(1, 2)), (0.5, F(1, 2))):
        with pytest.raises(ValueError, match=re.escape("kl(p, q) is bounded for Fractions p in [0, 1] and q in (0, 1)")):
            p2_interval.kl_lower(p, q)


def test_an_enclosure_takes_the_ends_of_its_ranges():
    assert Enclosure(4, 0).precision == 4
    E = Enclosure(12)
    assert E.atanh2(0, 1) == (0, 0) and E.atanh2(1, 3) == E.ln2


# -- after the inversion: exact ---------------------------------------------------------------------------------------
def test_the_affine_maps_are_exact_and_increasing():
    assert p2_interval.IDENTITY(F(3, 7)) == F(3, 7) and p2_interval.PARITY(F(3, 4)) == F(1, 2)
    m = p2_interval.xeb(9, 4096, 4368, F(52, 300))
    assert m(F(1, 3)) == (F(9, 4096) * F(1, 3) - F(1, 4368)) / F(52, 300)
    assert p2_interval.mapped((F(1, 4), F(3, 4)), p2_interval.PARITY) == (F(-1, 2), F(1, 2))
    for scale in (F(0), F(-1), 1):
        with pytest.raises(ValueError):
            p2_interval.Affine(scale, F(0))


def test_pooled_difference_drift_and_the_strong_form_are_exact_on_exact_endpoints():
    assert p2_interval.pooled([(3, 10), (4, 10)], 2) == p2_interval.interval(7, 20, 2)
    assert p2_interval.pooled([(F(1, 3), 2), (F(2, 3), 2)], 4) == p2_interval.interval(1, 4, 4)
    d = p2_interval.difference((F(1, 4), F(1, 2)), (F(1, 8), F(3, 8)))
    assert d == (F(-1, 8), F(3, 8))
    assert p2_interval.abs_lower(d) == 0
    assert p2_interval.abs_lower((F(1, 8), F(3, 8))) == F(1, 8)
    assert p2_interval.abs_lower((F(-3, 8), F(-1, 8))) == F(1, 8)
    jobs = [(F(1, 10), F(3, 10)), (F(2, 10), F(5, 10))]
    assert p2_interval.drift(jobs, (F(15, 100), F(4, 10))) == F(35, 100)
    assert p2_interval.strong_form((F(1, 2), F(3, 4)), F(1, 10), F(1, 20)) == F(1, 2) - F(1, 10) - F(1, 20)
