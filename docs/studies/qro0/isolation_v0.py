"""Section 8's certified statements under the adopted standard (Kourousias et al.'s ε-sufficiency, its supplement
S1.6's "semantic" form): ibm_kingston against ibm_fez on Quantum-Film's records of 2026-10-05. For study QRO-0,
draft 3. Stdlib only, read-only, exact rationals where the measure is exact.

Each measure is the mean of a bounded per-shot variable, mapped to [0, 1]:
  - five-crystal share   X = 1 if the shot holds exactly five crystals                    (all shots)
  - forbidden share      X = 1 if the five-crystal layout has det(K_Y) = 0              (five-crystal shots)
  - linear XEB           X = P(Y) * 4096 / 9, so F = (9 E[X] / 4096 - 1/D) / norm        (five-crystal shots)
  - <X0X1>, <Y0Y1>       X = 1 if the pair's two bits agree, so <PP> = 2 E[X] - 1          (coherence shots)

Every interval is Hoeffding's (1963, Thm 1) Chernoff bound in its KL form: {mu : n kl(mean, mu) <= ln(2M/alpha)}.
That bound holds for the mean of independent [0, 1] variables whatever their individual means. So it holds for
a job's shots, and for a device-day's pooled shots, whose target is the day's mean over its jobs. M counts every
interval in the family, so the family holds simultaneously at 1 - alpha (a union bound). It is conditional on
independent shots: within a job, independent of their order; across jobs, independent of each other.

For each measure it prints:
  - each device-day's mean with its interval, and the certified interval on the difference of the two;
  - drift: the certified bound U(D) on how far any one job's mean can sit from its day's mean;
  - the strong form, L(|diff|) - U(D_A) - U(D_B): when it is positive, every job of one device differs from every
    job of the other by at least that much.

Usage: python -I isolation_v0.py <path to moth-quantum>
"""
import itertools
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

if __name__ != "__main__":
    raise ImportError("an instrument, not a module")

ROOT = Path(sys.argv[1])


def pinned(root, want="3a73823"):
    """Refuse unless the tree read is a clean checkout of the commit the study names."""
    import subprocess
    head = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], cwd=root, capture_output=True, text=True,
                          check=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True,
                           check=True).stdout.strip()
    if head != want or dirty:
        sys.exit(f"REFUSED: moth-quantum is at {head}{' with uncommitted changes' if dirty else ''}, not a clean {want}")

pinned(ROOT)
IBM = ROOT / "docs" / "records" / "2026-10-05" / "ibm"
A, B = "ibm_kingston", "ibm_fez"
ALPHA = Fraction(1, 20)

L_, NSITES, N = 4, 16, 5
COS = (1, 0, -1, 0)
DISC = [(kx, ky) for kx in (-1, 0, 1) for ky in (-1, 0, 1) if kx * kx + ky * ky <= 1]
SITES = [divmod(s, L_) for s in range(NSITES)]
AK = [[sum(COS[(kx * (xi - xj) + ky * (yi - yj)) % L_] for kx, ky in DISC) for (xj, yj) in SITES]
      for (xi, yi) in SITES]


def det(m):
    m = [[Fraction(v) for v in row] for row in m]
    n, d = len(m), Fraction(1)
    for c in range(n):
        p = next((r for r in range(c, n) if m[r][c] != 0), None)
        if p is None:
            return Fraction(0)
        if p != c:
            m[c], m[p] = m[p], m[c]
            d = -d
        d *= m[c][c]
        for r in range(c + 1, n):
            f = m[r][c] / m[c][c]
            for k in range(c, n):
                m[r][k] -= f * m[c][k]
    return d


W = {Y: int(det([[AK[i][j] for j in Y] for i in Y])) for Y in itertools.combinations(range(NSITES), N)}
DEN, D = NSITES ** N, len(W)
assert D == 4368 and sum(W.values()) == DEN and sum(1 for w in W.values() if w == 0) == 1360
assert max(W.values()) == 9 * 256                                   # P(Y) <= 9/4096, so X = P * 4096/9 is in [0, 1]
NORM = Fraction(sum(w * w for w in W.values()), DEN * DEN) - Fraction(1, D)


def kl(p, q):
    """Bernoulli KL(p || q), in nats, for p in [0, 1] and q in (0, 1)."""
    out = 0.0
    if p > 0:
        out += p * math.log(p / q)
    if p < 1:
        out += (1 - p) * math.log((1 - p) / (1 - q))
    return out


def interval(total, n, budget):
    """{mu : n kl(total/n, mu) <= budget}, by bisection on each side. total may be a Fraction sum of [0,1] values."""
    m = float(Fraction(total) / n)
    lo_a, lo_b = 0.0, m
    for _ in range(200):
        mid = (lo_a + lo_b) / 2
        (lo_a, lo_b) = (mid, lo_b) if n * kl(m, mid) > budget else (lo_a, mid)
    hi_a, hi_b = m, 1.0
    for _ in range(200):
        mid = (hi_a + hi_b) / 2
        (hi_a, hi_b) = (hi_a, mid) if n * kl(m, mid) > budget else (mid, hi_b)
    return m, (0.0 if m == 0 else lo_b), (1.0 if m == 1 else hi_a)


def runs(dev, role):
    out = []
    for run in [IBM / dev / "run"] + sorted((IBM / dev).glob("sheet-*/run")):
        for p in sorted(run.glob(f"{role}-pub*.json")):
            out.append(json.loads(p.read_text()))
    return out


def per_shot_totals(rec, measure):
    """(sum of X over the shots in scope, number of shots in scope) for one record, exactly."""
    counts = [(tuple(ones), n) for ones, n in rec["counts"]]
    if measure == "five-crystal share":
        return sum(n for Y, n in counts if len(Y) == N), sum(n for _, n in counts)
    five = [(Y, n) for Y, n in counts if len(Y) == N]
    if measure == "forbidden share":
        return sum(n for Y, n in five if W[Y] == 0), sum(n for _, n in five)
    if measure == "linear XEB":
        return sum(Fraction(n * W[Y], 9 * 256) for Y, n in five), sum(n for _, n in five)
    raise ValueError(measure)


def parity_totals(rec):
    """Shots where the pair (sites 0 and 1) agree, and all shots: the coherence record's counts list its ones."""
    agree = sum(n for ones, n in rec["counts"] if (0 in ones) == (1 in ones))
    return agree, sum(n for _, n in rec["counts"])


LAW_MEASURES = ("five-crystal share", "forbidden share", "linear XEB")
law = {dev: runs(dev, "law") for dev in (A, B)}
coh = {dev: runs(dev, "coherence") for dev in (A, B)}                 # pub 0 is XX, pub 1 is YY
assert len(law[A]) == 9 and len(law[B]) == 11 and len(coh[A]) == 2 and len(coh[B]) == 2
M = len(LAW_MEASURES) * (len(law[A]) + len(law[B]) + 2) + 2 * 2        # every interval this family computes
budget = math.log(2 * M / float(ALPHA))
print(f"family: {M} intervals, alpha {float(ALPHA)}, each at alpha/M; KL budget ln(2M/alpha) = {budget:.4f}")


def to_measure(name, x):
    if name == "linear XEB":
        return float((Fraction(x).limit_denominator(10 ** 12) * 9 / 4096 - Fraction(1, D)) / NORM)
    return x


for name in LAW_MEASURES:
    rows = {}
    for dev in (A, B):
        jobs = [per_shot_totals(r, name) for r in law[dev]]
        tot, n = sum(t for t, _ in jobs), sum(k for _, k in jobs)
        mean = interval(tot, n, budget)
        each = [interval(t, k, budget) for t, k in jobs]
        drift = max(max(hi - mean[1], mean[2] - lo) for _, lo, hi in each)       # U(D) in [0,1] units
        rows[dev] = (mean, drift, len(jobs))
    (ma, da, na), (mb, db, nb) = rows[A], rows[B]
    diff_lo, diff_hi = ma[1] - mb[2], ma[2] - mb[1]
    l_abs = max(0.0, diff_lo, -diff_hi)
    sep = l_abs - da - db
    scale = (9 / 4096) / float(NORM) if name == "linear XEB" else 1.0
    print(f"\n== {name}")
    for dev, (mean, drift, n) in rows.items():
        print(f"  {dev} ({n} jobs): day mean {to_measure(name, mean[0]):.4f}, certified "
              f"[{to_measure(name, mean[1]):.4f}, {to_measure(name, mean[2]):.4f}]; drift bound U(D) {drift * scale:.4f}")
    print(f"  difference ({A} - {B}): certified [{diff_lo * scale:+.4f}, {diff_hi * scale:+.4f}]; "
          f"so the day means differ by at least {l_abs * scale:.4f}")
    print(f"  strong form L(|diff|) - U(D_A) - U(D_B) = {sep * scale:+.4f}: "
          + ("every job of one device differs from every job of the other by at least that"
             if sep > 0 else "unresolved: the drift bounds are wider than the certified difference"))

print("\n== coherence: one job a device, so drift is UNMEASURED and the strong form is not available")
for k, label in ((0, "<X0X1>"), (1, "<Y0Y1>")):
    vals = {}
    for dev in (A, B):
        rec = next(r for r in coh[dev] if r["source"]["pub"] == k)
        agree, n = parity_totals(rec)
        m, lo, hi = interval(agree, n, budget)
        vals[dev] = (2 * m - 1, 2 * lo - 1, 2 * hi - 1)
        print(f"  {label} {dev}: {2 * m - 1:+.4f}, certified [{2 * lo - 1:+.4f}, {2 * hi - 1:+.4f}]")
    lo_d = vals[A][1] - vals[B][2]
    hi_d = vals[A][2] - vals[B][1]
    print(f"  {label} difference: certified [{lo_d:+.4f}, {hi_d:+.4f}]"
          + (" (excludes 0)" if lo_d > 0 or hi_d < 0 else " (includes 0: unresolved even before drift)"))
