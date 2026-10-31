"""Certified intervals, `qro-hoeffding-kl/1`, rounded outward in integer arithmetic only (P2's design, item 5; P2.1).
Standard library only, and no float and no libm anywhere: this module imports no `math`, so every host writes the
same endpoints, byte for byte (a test reads its imports and refuses `math.log`).

THE BOUND (study QRO-0, section 8; Hoeffding 1963, Theorem 1, in its KL form): for the mean p = T / n of n independent
variables in [0, 1], the set C = {mu : n kl(p, mu) <= B}, B = ln(2 M / alpha), holds the target with probability at
least 1 - alpha / M, each side failing with probability at most e^-B; over a stated family of M intervals the union
bound holds all of them at 1 - alpha.

THE ALGORITHM, every rounding directed so that no rounding can narrow the interval:
  1. p = T / n exactly (a Fraction; T a whole number, or for linear XEB a sum of w / w_max).
  2. ln of a positive rational a / b is enclosed in fixed point at S = 2^PRECISION: a / b = 2^e y with y in [1, 2)
     from bit lengths and one comparison; z = (y - 1) / (y + 1) in [0, 1/3); ln y = 2 atanh z = 2 sum z^(2k+1) / (2k+1).
     The lower end floors z S, every square and power, and each term t_k / (2k+1), and stops after TERMS terms (the rest
     of the series is positive). The upper end ceils each of them and adds ceil(t_K S / ((2K+1)(S - z2_hi))), which
     bounds the rest of the series from above, whatever K is: TERMS buys tightness, never soundness. ln 2 = 2 atanh(1/3)
     the same way, and ln(a / b) = e ln 2 + ln y, ln 2's end chosen by the sign of e.
  3. kl_lo(p, q) = p ln_lo(p / q) + (1 - p) ln_lo((1 - p) / (1 - q)), each product floored, 0 ln 0 = 0; B_hi the upper
     end of ln(2 M / alpha). A point q is PROVEN OUTSIDE C when n kl_lo(p, q) > B_hi, in integers.
  4. Each end by bisection on the grid j / 2^GRID. The lower end is the last point proven outside below p, or 0; the
     upper end the first proven outside above p, or 1. An end is only ever a point proven outside (or 0 or 1), and
     kl(p, .) decreases on [0, p] and increases on [p, 1], so every mu beyond an end is outside too: C lies within
     [L, U] whatever path the bisection takes and however loose the enclosure, which costs only tightness.
  5. A measure's interval is that of its per-shot mean mapped by the measure's increasing affine map (shares: the
     identity; linear XEB: ((w_max / den) x - 1/D) / norm; a parity: 2x - 1), exactly.
After that one inversion every difference, drift bound and strong form is exact rational arithmetic on the endpoints
(`pooled`, `difference`, `abs_lower`, `drift`, `strong_form`): rounding happens once, outward, and nothing after it
rounds. P3 calls these with the family of its own comparison; P2 never decides a verdict.
"""
from dataclasses import dataclass
from fractions import Fraction

RULE = "qro-hoeffding-kl/1"
PRECISION = 128               # ln is enclosed in units of 2^-128
GRID = 48                     # an endpoint is j / 2^48
TERMS = 41                    # series terms before the tail bound; any count is sound, 41 is past 2^-128 at z < 1/3
ALPHA = Fraction(1, 20)


def _ceil_div(a, b):
    return -((-a) // b)


class Enclosure:
    """ln of a positive rational, enclosed: [lo, hi] in units of 2^-precision, every rounding directed."""

    def __init__(self, precision=PRECISION, terms=TERMS):
        if type(precision) is not int or type(terms) is not int or precision < 4 or terms < 0:
            raise ValueError("an enclosure has a whole precision of at least 4 bits and a whole count of terms")
        self.precision, self.terms, self.S = precision, terms, 1 << precision
        self.ln2 = self.atanh2(1, 3)

    def _series(self, num, den, record=None):
        """[lo, hi] of 2 atanh(num / den) S. With `record`, every rounded quantity is appended to it, in order, for
        the test that holds each to its exact rational."""
        S, K = self.S, self.terms
        zl, zh = (num * S) // den, _ceil_div(num * S, den)
        z2l, z2h = (zl * zl) // S, _ceil_div(zh * zh, S)
        tl, th, sl, sh = zl, zh, 0, 0
        for k in range(K):
            d = 2 * k + 1
            ql, qh = tl // d, _ceil_div(th, d)
            sl += ql
            sh += qh
            if record is not None:
                record.append((tl, th, ql, qh))
            tl, th = (tl * z2l) // S, _ceil_div(th * z2h, S)
        tail = _ceil_div(th * S, (2 * K + 1) * (S - z2h))
        if record is not None:
            record.append((zl, zh, z2l, z2h, tl, th, tail))
        return 2 * sl, 2 * (sh + tail)

    def atanh2(self, num, den):
        """[lo, hi] of 2 atanh(num / den), in units of 2^-precision, for whole 0 <= num and 3 num <= den."""
        if type(num) is not int or type(den) is not int or num < 0 or den < 1 or 3 * num > den:
            raise ValueError("2 atanh(z) is enclosed for z = num / den in [0, 1/3]")
        return self._series(num, den)

    def steps(self, num, den):
        """Every rounded quantity of 2 atanh(num / den): {"terms": [(t_lo, t_hi, term_lo, term_hi) for k < terms],
        "z": (z_lo, z_hi), "z2": (z2_lo, z2_hi), "last": (t_lo, t_hi) of t_terms, "tail": the tail's bound,
        "bounds": (lo, hi)}."""
        record = []
        lo, hi = self._series(num, den, record)
        zl, zh, z2l, z2h, tl, th, tail = record.pop()
        return {"terms": record, "z": (zl, zh), "z2": (z2l, z2h), "last": (tl, th), "tail": tail, "bounds": (lo, hi)}

    def ln(self, a, b):
        """[lo, hi] of ln(a / b), in units of 2^-precision, for positive whole numbers a and b."""
        if type(a) is not int or type(b) is not int or a < 1 or b < 1:
            raise ValueError("ln is enclosed for a / b with a and b positive whole numbers")
        e = a.bit_length() - b.bit_length()
        if (a << max(0, -e)) < (b << max(0, e)):
            e -= 1
        yn, yd = (a, b << e) if e >= 0 else (a << -e, b)               # y = yn / yd in [1, 2)
        lo, hi = self.atanh2(yn - yd, yn + yd)
        l2lo, l2hi = self.ln2
        return (e * l2lo + lo, e * l2hi + hi) if e >= 0 else (e * l2hi + lo, e * l2lo + hi)


_DEFAULT = []


def enclosure():
    """The enclosure every interval of this rule uses: 2^-128, 41 terms."""
    if not _DEFAULT:
        _DEFAULT.append(Enclosure())
    return _DEFAULT[0]


def kl_lower(p, q, E=None):
    """A lower bound on kl(p, q), in units of 2^-precision: p in [0, 1] and q in (0, 1), both Fractions."""
    E = enclosure() if E is None else E
    if not (isinstance(p, Fraction) and isinstance(q, Fraction) and 0 <= p <= 1 and 0 < q < 1):
        raise ValueError("kl(p, q) is bounded for Fractions p in [0, 1] and q in (0, 1)")
    out = 0
    if p > 0:
        lo, _ = E.ln(p.numerator * q.denominator, p.denominator * q.numerator)
        out += (p.numerator * lo) // p.denominator
    if p < 1:
        r, s = 1 - p, 1 - q
        lo, _ = E.ln(r.numerator * s.denominator, r.denominator * s.numerator)
        out += (r.numerator * lo) // r.denominator
    return out


def budget_upper(family, alpha, E=None):
    """An upper bound on B = ln(2 M / alpha), in units of 2^-precision."""
    E = enclosure() if E is None else E
    a = Fraction(2 * family) / alpha
    return E.ln(a.numerator, a.denominator)[1]


def _checked(total, n, family, alpha):
    if type(n) is not int or n < 1:
        raise ValueError("an interval needs a positive whole number of shots")
    if type(total) is not int and not isinstance(total, Fraction):
        raise TypeError("the total of the per-shot variables is a whole number or a Fraction, never a float")
    if not 0 <= total <= n:
        raise ValueError("the total of n variables in [0, 1] lies in [0, n]")
    if type(family) is not int or family < 1:
        raise ValueError("the family is a positive whole number of intervals")
    if not isinstance(alpha, Fraction) or not 0 < alpha < 1:
        raise ValueError("alpha is a Fraction in (0, 1)")
    return Fraction(total) / n


def interval(total, n, family, alpha=ALPHA, E=None, grid=GRID):
    """(L, U), Fractions on the grid j / 2^grid, holding {mu : n kl(total / n, mu) <= ln(2 family / alpha)}."""
    p = _checked(total, n, family, alpha)
    E = enclosure() if E is None else E
    b_hi = budget_upper(family, alpha, E)
    G = 1 << grid

    def outside(j):
        return n * kl_lower(p, Fraction(j, G), E) > b_hi

    lo, hi = 0, _ceil_div(p.numerator * G, p.denominator)      # lo: 0 or proven outside; hi = ceil(p G)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if Fraction(mid, G) < p and outside(mid):
            lo = mid
        else:
            hi = mid
    lower = Fraction(lo, G)
    lo, hi = (p.numerator * G) // p.denominator, G             # lo = floor(p G); hi: 1 or proven outside
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if Fraction(mid, G) > p and outside(mid):
            hi = mid
        else:
            lo = mid
    return lower, Fraction(hi, G)


@dataclass(frozen=True)
class Affine:
    """An increasing affine map x -> scale x + offset, from a per-shot mean to a measure's units."""
    scale: Fraction
    offset: Fraction

    def __post_init__(self):
        if not (isinstance(self.scale, Fraction) and isinstance(self.offset, Fraction) and self.scale > 0):
            raise ValueError("an affine map here is increasing, with Fraction scale and offset")

    def __call__(self, x):
        return self.scale * x + self.offset


IDENTITY = Affine(Fraction(1), Fraction(0))
PARITY = Affine(Fraction(2), Fraction(-1))


def xeb(w_max, den, D, norm):
    """Linear XEB's map from the mean of w(Y) / w_max over the N-crystal shots: F = ((w_max / den) x - 1/D) / norm."""
    return Affine(Fraction(w_max, den) / norm, -Fraction(1, D) / norm)


def mapped(bounds, mapping):
    """An interval mapped by an increasing affine map, exactly."""
    return mapping(bounds[0]), mapping(bounds[1])


# -- what P3 calls: exact on exact endpoints ---------------------------------------------------------------------------
def pooled(jobs, family, alpha=ALPHA):
    """The interval of the jobs' pooled shots: jobs is [(total, n), ...]."""
    return interval(sum((Fraction(t) for t, _ in jobs), Fraction(0)), sum(n for _, n in jobs), family, alpha)


def difference(a, b):
    """The interval of a - b, from intervals a and b: [L_a - U_b, U_a - L_b]."""
    return a[0] - b[1], a[1] - b[0]


def abs_lower(d):
    """The lower bound of |x| over an interval d: max(0, L, -U)."""
    return max(Fraction(0), d[0], -d[1])


def drift(job_intervals, pooled_interval):
    """U(D), the drift bound: the most any job's interval leaves the run's pooled one, max over jobs of
    max(U_j - L, U - L_j)."""
    L, U = pooled_interval
    return max(max(u - L, U - lo) for lo, u in job_intervals)


def strong_form(diff, drift_a, drift_b):
    """The strong form of a difference: L(|diff|) - U(D_A) - U(D_B)."""
    return abs_lower(diff) - drift_a - drift_b
