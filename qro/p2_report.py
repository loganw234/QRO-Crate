"""Report functions: the figures Quantum-Film's table prints that no step of the checker reads (P2's design, item 4;
P2.1). Floats, and never written to a crate. Standard library and qro only; they reproduce Quantum-Film's
quantum_film/compare.py and pauli_tile.score as READ, importing neither.

  floor(n, law)          a perfect sampler's TVD to the law at n shots: replica r lays n exact draws from the law, draw
                         i taking golden uniform i of stream("compare-floor", stock, n, r) (its 64-bit word's top bits,
                         the law's denominator being a power of two, pick the layout by the cumulative weights); each
                         replica's TVD exact; the mean, and the value at rank ceil(percentile * replicas / 100),
                         ascending, of `replicas` of them.
  z_scores(counts, A)    each site's and each pair's occupation against the kernel K = A / M, as z = (measured -
                         exact) / binomial standard error: the one-site and pair max |z| and chi-squared.
  xeb_se(counts, law)    linear XEB's standard error over N-crystal counts; coherence_se(mean, shots) a parity's.
The sampled TVD has a floor, so it is a statistic and never placed in a range; nothing CHECKED rests on any of these.
"""
import bisect
import hashlib
import itertools
import math
from fractions import Fraction

DOMAIN = b"quantum-film/uniform/v1"               # golden.uniform's domain (Quantum-Film, READ)
REPLICAS, PERCENTILE = 200, 95


def stream(*parts):
    """Quantum-Film's stream encoding: a string as s<len>:<utf-8>, a whole number as i<n>, joined by |."""
    out = []
    for p in parts:
        if isinstance(p, str):
            b = p.encode("utf-8")
            out.append(b"s%d:%s" % (len(b), b))
        elif type(p) is int:
            out.append(b"i%d" % p)
        else:
            raise TypeError("a stream part is a string or a whole number")
    return b"|".join(out)


def uniform_words(parts, count):
    """The first `count` golden uniforms of stream(*parts), as 64-bit whole numbers: word i is the first 8 bytes,
    big-endian, of SHA-256(DOMAIN | stream | i)."""
    head = hashlib.sha256(DOMAIN + b"|" + stream(*parts) + b"|")
    out = []
    for i in range(count):
        h = head.copy()
        h.update(b"%d" % i)
        out.append(int.from_bytes(h.digest()[:8], "big"))
    return out


def replica_tvd(n, r, law):
    """One replica's exact TVD to the law: n draws on stream("compare-floor", stock, n, r)."""
    bits = law.den.bit_length() - 1
    if law.den != 1 << bits:
        raise ValueError("the law's denominator is not a power of two, so the top bits of a uniform word do not pick "
                         "a layout exactly")
    cum = list(itertools.accumulate(law.weights))
    c = [0] * law.D
    for word in uniform_words(("compare-floor", law.stock, n, r), n):
        c[bisect.bisect_right(cum, word >> (64 - bits))] += 1
    return Fraction(sum(abs(ci * law.den - n * w) for ci, w in zip(c, law.weights)), 2 * n * law.den)


def floor(n, law, replicas=REPLICAS, percentile=PERCENTILE):
    """{"mean", "upper": floats; "exact_mean", "exact_upper": Fractions} of the perfect sampler's TVD at n shots."""
    if type(n) is not int or n < 1 or type(replicas) is not int or replicas < 1:
        raise ValueError("a floor needs positive whole numbers of shots and replicas")
    vals = sorted(replica_tvd(n, r, law) for r in range(replicas))
    rank = -(-percentile * replicas // 100)
    mean = sum(vals, Fraction(0)) / replicas
    return {"mean": float(mean), "upper": float(vals[rank - 1]), "exact_mean": mean, "exact_upper": vals[rank - 1]}


def z_scores(counts, A):
    """{"one_site": {"z", "max_abs_z", "chi2"}, "pairs": {"max_abs_z", "chi2", "worst_pair"}} of counts against the
    kernel K = A / M (pauli_tile.score's statistics, READ): z = (measured / shots - exact) / sqrt(exact (1 - exact) /
    shots), exact K_qq for a site and K_ii K_jj - K_ij^2 for a pair."""
    M = len(A)
    shots = sum(counts.values())
    one, two = [0] * M, {}
    for Y, c in counts.items():
        for i in Y:
            one[i] += c
        for p in itertools.combinations(Y, 2):
            two[p] = two.get(p, 0) + c
    K = [[a / M for a in row] for row in A]
    z1 = [(one[q] / shots - K[q][q]) / math.sqrt(K[q][q] * (1 - K[q][q]) / shots) for q in range(M)]
    z2 = {}
    for i, j in itertools.combinations(range(M), 2):
        ex = K[i][i] * K[j][j] - K[i][j] ** 2
        z2[(i, j)] = (two.get((i, j), 0) / shots - ex) / math.sqrt(ex * (1 - ex) / shots)
    worst = max(z2, key=lambda p: abs(z2[p]))
    return {"one_site": {"z": z1, "max_abs_z": max(abs(z) for z in z1), "chi2": sum(z * z for z in z1)},
            "pairs": {"max_abs_z": abs(z2[worst]), "chi2": sum(z * z for z in z2.values()), "worst_pair": worst}}


def xeb_se(counts, law):
    """Linear XEB's standard error over N-crystal counts {layout: shots} (compare.xeb, READ); None below two shots."""
    n = sum(counts.values())
    if n < 2:
        return None
    s1 = sum(c * law.weight[Y] for Y, c in counts.items())
    s2 = sum(c * law.weight[Y] ** 2 for Y, c in counts.items())
    var = (Fraction(s2, law.den * law.den) - Fraction(s1 * s1, n * law.den * law.den)) / (n - 1)
    return math.sqrt(var / n) / float(law.norm)


def coherence_se(mean, shots):
    """A parity's binomial standard error, sqrt((1 - mean^2) / shots) (compare.coherence, READ)."""
    return math.sqrt((1 - mean * mean) / shots)
