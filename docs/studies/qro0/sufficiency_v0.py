"""Kourousias et al.'s finite-shot sufficiency test (arXiv:2610.09931v2, Eqs. 11-12, Supplement S1.5),
applied to Quantum-Film's 31 IBM law jobs of 2026-10-05. An instrument for study QRO-0, section 16.

Reads the committed device-run records and the law jobs' metrics files only (stdlib, read-only). For two
coarse outcome objects it computes each job's empirical law, every pair's Hellinger distance, the paper's
simultaneous radius eta = sqrt(1 - exp(-c/n)), c = (B-1) ln 2 + ln(M/alpha), and the pass / fail / unresolved
verdict of two field policies at several tolerances. It then gives the least whole shots per job that each of
the paper's rules needs: its Eq. 13 and its planning rule for v0's family of 31 laws, and the planning rule
alone for a proposed campaign of nine. And it gives what those would cost under three models of the QPU
charge IBM reported for v0's 65 jobs. The law's forbidden set is recomputed from the 4x4 tile's integer kernel and held to Quantum-Film's own
counts (1,360 of 4,368 forbidden; weights 0, 1, 4, 9).

Usage: python -I sufficiency_v0.py <path to moth-quantum>
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
DEVICES = ("ibm_kingston", "ibm_marrakesh", "ibm_fez")
ALPHA = 0.05
TOLERANCES = (0.02, 0.05, 0.10)

# ---- the law's support, from the integer kernel A = 16 K of pauli-4x4 (L = 4, Fermi disc r^2 = 1) ----
L, NSITES, N = 4, 16, 5
COS = (1, 0, -1, 0)                                   # cos(2 pi m / 4)
DISC = [(kx, ky) for kx in (-1, 0, 1) for ky in (-1, 0, 1) if kx * kx + ky * ky <= 1]
assert len(DISC) == N, DISC
SITES = [divmod(s, L) for s in range(NSITES)]         # site = x * 4 + y
A = [[sum(COS[(kx * (xi - xj) + ky * (yi - yj)) % L] for kx, ky in DISC) for (xj, yj) in SITES]
     for (xi, yi) in SITES]


def det(m):
    """Exact determinant by Fraction elimination."""
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


W = {Y: det([[A[i][j] for j in Y] for i in Y]) for Y in itertools.combinations(range(NSITES), N)}
FORBIDDEN = {Y for Y, w in W.items() if w == 0}
assert len(W) == 4368 and len(FORBIDDEN) == 1360, (len(W), len(FORBIDDEN))
assert sum(W.values()) == NSITES ** N, sum(W.values())                      # sum of det(K_Y) is 1
assert {w / 256 for w in W.values()} == {0, 1, 4, 9}, sorted({w / 256 for w in W.values()})


# ---- the jobs ----
def law_records():
    for dev in DEVICES:
        d = IBM / dev
        for run in [d / "run"] + sorted(d.glob("sheet-*/run")):
            rec = json.loads((run / "law-pub0-law.json").read_text())
            assert rec["role"] == "law", rec["role"]
            yield dev, rec["source"]["job_id"], rec


def objects(counts):
    """Two coarse outcome objects of one job: crystal count (B = 17) and a three-way class (B = 3)."""
    weight = [0] * (NSITES + 1)
    three = {"five-allowed": 0, "five-forbidden": 0, "not-five": 0}
    for ones, n in counts:
        weight[len(ones)] += n
        if len(ones) == N:
            three["five-forbidden" if tuple(ones) in FORBIDDEN else "five-allowed"] += n
        else:
            three["not-five"] += n
    return {"crystal count (B=17)": weight, "three-way class (B=3)": list(three.values())}


def hellinger(p, q):
    bc = sum(math.sqrt(a * b) for a, b in zip(p, q))
    return math.sqrt(max(0.0, 1.0 - bc))


jobs = []
for dev, job, rec in law_records():
    counts = rec["counts"]
    shots = sum(n for _, n in counts)
    jobs.append((dev, job, shots, objects(counts)))

M = len(jobs)
assert M == 31 and {s for *_, s, _ in jobs} == {24576}, (M, {s for *_, s, _ in jobs})
PLANNING, R_HAT = [], {}


def shots_needed(c, radius):
    """The least whole n whose radius sqrt(1 - exp(-c/n)) is at most `radius`: n >= c / -ln(1 - radius^2)."""
    n = math.ceil(c / -math.log1p(-radius * radius))
    assert math.sqrt(-math.expm1(-c / n)) <= radius < math.sqrt(-math.expm1(-c / (n - 1))), (c, radius, n)
    return n
print(f"jobs: {M} law jobs, 24,576 shots each; alpha = {ALPHA}; contexts M = {M}")
print("law support: 1,360 of 4,368 five-crystal layouts forbidden (recomputed and held)")

for name in next(iter(jobs))[3]:
    B = len(next(iter(jobs))[3][name])
    laws = [[c / s for c in o[name]] for _, _, s, o in jobs]
    c = (B - 1) * math.log(2) + math.log(M / ALPHA)
    eta = math.sqrt(1 - math.exp(-c / 24576))
    print(f"\n== {name}: radius eta = {eta:.4f} per law; a pair's interval is H +- {2 * eta:.4f}")
    H = [[hellinger(laws[i], laws[j]) for j in range(M)] for i in range(M)]
    within = {dev: max((H[i][j] for i in range(M) for j in range(M)
                        if i < j and jobs[i][0] == dev and jobs[j][0] == dev), default=0.0) for dev in DEVICES}
    for dev in DEVICES:
        n = sum(1 for j in jobs if j[0] == dev)
        print(f"  within {dev} ({n} jobs): largest job-to-job H = {within[dev]:.4f}")
    across = [H[i][j] for i in range(M) for j in range(M) if i < j and jobs[i][0] != jobs[j][0]]
    print(f"  across devices: H from {min(across):.4f} to {max(across):.4f}")
    policies = {
        "{} (pool every job)": [[i for i in range(M)]],
        "{device} (pool a device's jobs)": [[i for i in range(M) if jobs[i][0] == d] for d in DEVICES],
    }
    for pol, cells in policies.items():
        hat = max(H[i][j] for cell in cells for i in cell for j in cell if i < j)
        lo, hi = max(0.0, hat - 2 * eta), min(1.0, hat + 2 * eta)
        verdicts = []
        for eps in TOLERANCES:
            v = "pass" if hi <= eps else "fail" if lo > eps else "unresolved"
            verdicts.append(f"eps {eps}: {v}")
        print(f"  record {pol}: risk {hat:.4f}, interval [{lo:.4f}, {hi:.4f}] -> " + "; ".join(verdicts))
    r_hat = max(within.values())
    R_HAT[name] = (B, r_hat)
    for eps in (0.05, 0.10):
        floor = shots_needed(c, eps / 4)
        test = shots_needed(c, (eps - r_hat) / 2)
        plan = shots_needed(c, (eps - r_hat) / 4)
        PLANNING.append((M, name, eps, plan))
        print(f"  shots per job for the {{device}} policy at {eps}, with the observed within-device risk {r_hat:.4f}, "
              f"each the least whole count that meets its rule: "
              f"as the empirical risk (the paper's Eq. 13, the observed-risk test) {test:,}; "
              f"as the true risk of a new run (4 eta <= eps - R, the paper's planning rule) {plan:,}; "
              f"the planning rule at zero true risk (4 eta <= eps) {floor:,}")

print("\n== the radius on finer objects, at the same 24,576 shots, M and alpha (no laws computed)")
for name, B in (("five-crystal layout, plus one 'not five' outcome", 4368 + 1), ("raw 16-bit outcome", 2 ** 16)):
    c = (B - 1) * math.log(2) + math.log(M / ALPHA)
    print(f"  {name} (B={B:,}): eta = {math.sqrt(1 - math.exp(-c / 24576)):.4f}")

# ---- planning the proposed campaign: three devices, three law jobs each, so M = 9 laws ----
M_PLAN = 9
print(f"\n== planning the proposed campaign: three devices with three law jobs each (M = {M_PLAN}), "
      f"v0's within-device risk taken as the true risk; the planning rule, the least whole count")
for name, (B, r_hat) in R_HAT.items():
    c = (B - 1) * math.log(2) + math.log(M_PLAN / ALPHA)
    for eps in (0.05, 0.10):
        plan = shots_needed(c, (eps - r_hat) / 4)
        PLANNING.append((M_PLAN, name, eps, plan))
        print(f"  {name} at {eps}: {plan:,} shots a law job")


# ---- what those counts would cost: IBM's reported charges for all 65 of v0's jobs ----
def charged(run, role):
    """(shots the job's records hold, IBM's whole-second charge) for one job, the charge tied to the job by its id."""
    m = json.loads((run / f"{role}-metrics.json").read_text())
    shots = 0
    for p in sorted(run.glob(f"{role}-pub*.json")):
        rec = json.loads(p.read_text())
        assert rec["source"]["job_id"] == m["job_id"], (run, role, rec["source"]["job_id"], m["job_id"])
        shots += sum(n for _, n in rec["counts"])
    return shots, m["metrics"]["usage"]["qpu_charge_time_seconds"]


points = []
for dev in DEVICES:
    d = IBM / dev
    for run in [d / "run"] + sorted(d.glob("sheet-*/run")):
        for role in ("known-answer", "law", "coherence"):
            if (run / f"{role}-metrics.json").exists():
                points.append((role,) + charged(run, role))
assert len(points) == 65, len(points)
levels = sorted(set(points), key=lambda p: p[1])
print(f"\n== QPU charge: IBM's qpu_charge_time_seconds for v0's {len(points)} jobs, whole seconds, REPORTED: "
      + "; ".join(f"{role}, {s:,} shots: {q} s ({points.count((role, s, q))} jobs)" for role, s, q in levels))
law_rate = Fraction(max(q for role, _, q in points if role == "law"), 24576)
xs, ys = [s for _, s, _ in points], [q for *_, q in points]
mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
icept = my - slope * mx
MODELS = (
    ("(a) through the origin at the law jobs' charge", lambda n: float(law_rate) * n,
     f"{float(law_rate) * 1000:.3f} ms a shot"),
    ("(b) a least-squares line through all 65 jobs", lambda n: icept + slope * n,
     f"{icept:.2f} s plus {slope * 1000:.3f} ms a shot"),
    ("(c) moth-quantum's docs/HARDWARE.md:28, READ", lambda n: 2 + 0.00035 * n, "about 2 s plus about 0.35 ms a shot"),
)
print("  three cost models, each an estimate from v0's job sizes:")
for label, _, form in MODELS:
    print(f"    {label}: {form}")
for m_, name, eps, plan in PLANNING:
    costs = [f(plan) for _, f, _ in MODELS]
    line = f"  M = {m_}, {name} at {eps}: {plan:,} shots, " + ", ".join(f"{t:.0f} s" for t in costs) + " a job by (a), (b), (c)"
    if m_ == M_PLAN:
        line += f"; nine law jobs {9 * min(costs) / 60:.1f} to {9 * max(costs) / 60:.1f} min"
    print(line)
