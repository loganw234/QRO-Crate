"""The report functions (P2's design, item 4): floats, never written to a crate, and never read by a step. The stream's
encoding; the golden uniforms against a plain re-computation; a replica's TVD against draws made here by a plain scan of
the cumulative weights; the floor's mean and rank; the z statistics, zero on the law's own table; and the standard
errors against their formulas. Quantum-Film's printed figures are P2.2's to reproduce, on v0's crates."""
import hashlib
import math
from fractions import Fraction

import pytest
from p2_builder import small_law_bytes

from qro import p2_law, p2_report

F = Fraction


def v0():
    return p2_law.read(p2_law.law_bytes())


def test_the_stream_encoding():
    assert p2_report.stream("compare-floor", "pauli-4x4", 24576, 0) == b"s13:compare-floor|s9:pauli-4x4|i24576|i0"
    assert p2_report.stream("é", -3) == b"s2:\xc3\xa9|i-3"
    for bad in (1.0, True, None, b"x"):
        with pytest.raises(TypeError):
            p2_report.stream(bad)


def plain_words(parts, count):
    out = []
    for i in range(count):
        stream = p2_report.stream(*parts)
        digest = hashlib.sha256(b"quantum-film/uniform/v1|" + stream + b"|" + str(i).encode()).digest()
        out.append(int.from_bytes(digest[:8], "big"))
    return out


def test_the_golden_uniforms_against_a_plain_recomputation():
    parts = ("compare-floor", "pauli-4x4", 10, 3)
    assert p2_report.uniform_words(parts, 25) == plain_words(parts, 25)
    assert all(0 <= w < 1 << 64 for w in p2_report.uniform_words(parts, 25))


def plain_tvd(n, r, law):
    bits = law.den.bit_length() - 1
    counts = [0] * law.D
    for w in plain_words(("compare-floor", law.stock, n, r), n):
        u, k, total = w >> (64 - bits), 0, law.weights[0]
        while total <= u:
            k += 1
            total += law.weights[k]
        counts[k] += 1
    return sum((abs(F(c, n) - F(w, law.den)) for c, w in zip(counts, law.weights)), F(0)) / 2


@pytest.mark.parametrize("n, r", [(1, 0), (10, 0), (10, 7), (333, 2)])
def test_a_replicas_tvd_against_draws_made_by_a_plain_scan(n, r):
    law = v0()
    got = p2_report.replica_tvd(n, r, law)
    assert got == plain_tvd(n, r, law)
    assert 0 < got <= 1


def test_no_draw_ever_lands_on_a_forbidden_layout():
    law = v0()
    for r in range(3):
        assert p2_report.replica_tvd(400, r, law) == plain_tvd(400, r, law)


def test_a_replica_needs_a_power_of_two_denominator():
    with pytest.raises(ValueError, match="not a power of two"):
        p2_report.replica_tvd(10, 0, p2_law.read(small_law_bytes()))


def test_the_floor_is_the_mean_and_the_ranked_replica():
    law = v0()
    vals = sorted(plain_tvd(20, r, law) for r in range(7))
    got = p2_report.floor(20, law, replicas=7, percentile=50)
    assert got["exact_mean"] == sum(vals, F(0)) / 7 and got["exact_upper"] == vals[math.ceil(50 * 7 / 100) - 1]
    assert (got["mean"], got["upper"]) == (float(got["exact_mean"]), float(got["exact_upper"]))
    assert p2_report.floor(20, law, replicas=7)["exact_upper"] == vals[-1], "the 95th of 7 is the largest"
    for n, replicas in ((0, 7), (20, 0), (2.0, 7), (20, True)):
        with pytest.raises(ValueError):
            p2_report.floor(n, law, replicas=replicas)


def test_the_z_statistics_are_zero_on_the_laws_own_table_and_follow_their_formula():
    law, A = v0(), p2_law.kernel()
    own = {Y: w for Y, w in zip(law.layouts, law.weights) if w}
    z = p2_report.z_scores(own, A)
    assert z["one_site"]["max_abs_z"] < 1e-9 and z["pairs"]["max_abs_z"] < 1e-9
    moved = dict(own)
    first = next(iter(moved))
    moved[first] += 64
    z = p2_report.z_scores(moved, A)
    shots, site = 4096 + 64, first[0]
    exact = A[site][site] / 16
    measured = (sum(c for Y, c in moved.items() if site in Y)) / shots
    assert z["one_site"]["z"][site] == pytest.approx((measured - exact) / math.sqrt(exact * (1 - exact) / shots))
    assert z["one_site"]["chi2"] == pytest.approx(sum(x * x for x in z["one_site"]["z"]))
    i, j = z["pairs"]["worst_pair"]
    ex = (A[i][i] * A[j][j] - A[i][j] ** 2) / 256                  # K_ii K_jj - K_ij^2, K = A / 16
    two = sum(c for Y, c in moved.items() if i in Y and j in Y) / shots
    assert z["pairs"]["max_abs_z"] == pytest.approx(abs((two - ex) / math.sqrt(ex * (1 - ex) / shots)))
    assert z["pairs"]["max_abs_z"] > 1


def test_the_standard_errors_against_their_formulas():
    law = v0()
    counts = {law.layouts[i]: c for i, c in ((1, 3), (2, 5), (7, 1), (40, 2))}
    xs = [F(law.weight[Y], law.den) for Y, c in counts.items() for _ in range(c)]
    mean = sum(xs, F(0)) / len(xs)
    var = sum(((x - mean) ** 2 for x in xs), F(0)) / (len(xs) - 1)
    assert p2_report.xeb_se(counts, law) == pytest.approx(math.sqrt(var / len(xs)) / float(law.norm), rel=1e-12)
    assert p2_report.xeb_se({law.layouts[1]: 1}, law) is None
    assert p2_report.coherence_se(0.6, 100) == pytest.approx(0.08)
    assert p2_report.coherence_se(1.0, 10) == 0.0
