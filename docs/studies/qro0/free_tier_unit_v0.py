"""Sizing a free-tier unit for QRO-0's next round: what one fixed batch costs on IBM's Open Plan, and what one
unit, and k units pooled, can certify. For study QRO-0, section 9.1. Stdlib only, read-only.

Logan, 2026-10-14: "Ideally we can size a run that can be repeated by anyone on a free tier to give adequate
data, allowing anyone to contribute more runs of the same thing for no cost."

Every figure is arithmetic on v0's records. Where it projects a new unit, it takes as the new unit's truth:
  - v0's per-device means, and its largest job-to-job deviations (drift);
  - v0's coherence values and single-site means, each from one 4,096-shot job a device, so they carry v0's own
    sampling noise (about 0.015 on a parity);
  - v0's largest within-device Hellinger distances R, recomputed here as sufficiency_v0.py does;
  - the readout errors IBM reported at v0's freeze.
That is a projection under those assumptions, not a measurement of any new run.

The unit: D devices (v0's three), r passes. Each pass runs on every device in turn, one job at a time and each
awaited, so the devices interleave:
  - a control job: two PUBs at Nc shots each, the known answer X on {0,1,3,7,12} and its complement. Bit order
    is held, and every chain qubit is read prepared in 0 and in 1;
  - then the film, in one of two shapes:
      "film":  one job holding the law and both coherence bases, N shots each;
      "split": a law job at NL, then a coherence job holding both bases at NC each.
Each job's PUBs share one shot count: qiskit-ibm-runtime 0.50.0 warns "Specifying different 'shots' across pubs
is deprecated" (sampler.py:129-136; moth-quantum, quantum_film/ibm/bundle.py:53-56).

Certified intervals are isolation_v0.py's: Hoeffding's KL form, two-sided, at alpha/M for a family of M.
  - One unit: its own family at alpha = 0.05: every job and device pool for five measures, the pair's
    single-site means, and the pair's readout bounds.
  - k units pooled: look k spends alpha / (k (k+1)), and the spends sum to alpha. A look's family is everything
    that look computes: the pooled intervals, the same again leaving out each contributor in turn, and every
    unit's device means for the strong form at unit granularity. The projection takes each unit from a
    different contributor, the largest family.

Readout, for the pair's qubits 1 and 2, under the confusion model P' = a_1 a_2 + a_1 f_2 <z_2> + a_2 f_1 <z_1>
+ f_1 f_2 P, with a = p10 - p01 and f = 1 - p01 - p10. With the measured single-site means m' = a + f <z>, the
offset is a_1 m'_2 + a_2 m'_1 - a_1 a_2, and 0 < f_1 f_2 <= 1 shrinks the parity toward 0.

Usage: python -I free_tier_unit_v0.py <path to moth-quantum>
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
SHORT = {"ibm_kingston": "K", "ibm_marrakesh": "M", "ibm_fez": "F"}
ALPHA = 0.05
WINDOW = 600                          # docs/HARDWARE.md:15, READ: 10 QPU-minutes per rolling 28 days

# ---- the law, from its integer kernel (as the other instruments) ----
L_, NSITES, N5 = 4, 16, 5
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


W = {Y: int(det([[AK[i][j] for j in Y] for i in Y])) for Y in itertools.combinations(range(NSITES), N5)}
assert sum(W.values()) == NSITES ** N5 and sum(1 for w in W.values() if w == 0) == 1360 and max(W.values()) == 2304
D_LAYOUTS = len(W)
NORM = Fraction(sum(w * w for w in W.values()), NSITES ** N5 * NSITES ** N5) - Fraction(1, D_LAYOUTS)
XEB_SCALE = (9 / 4096) / float(NORM)          # d(linear XEB) / d(mean of X), X = P(Y) * 4096/9 in [0, 1]


# ---- Hoeffding's KL interval (isolation_v0.py's) ----
def kl(p, q):
    out = 0.0
    if p > 0:
        out += p * math.log(p / q)
    if p < 1:
        out += (1 - p) * math.log((1 - p) / (1 - q))
    return out


def interval(mean, n, budget):
    """{mu : n kl(mean, mu) <= budget}, by bisection on each side."""
    lo_a, lo_b = 0.0, mean
    for _ in range(200):
        mid = (lo_a + lo_b) / 2
        (lo_a, lo_b) = (mid, lo_b) if n * kl(mean, mid) > budget else (lo_a, mid)
    hi_a, hi_b = mean, 1.0
    for _ in range(200):
        mid = (hi_a + hi_b) / 2
        (hi_a, hi_b) = (hi_a, mid) if n * kl(mean, mid) > budget else (mid, hi_b)
    return (0.0 if mean == 0 else lo_b), (1.0 if mean == 1 else hi_a)


def budget(m_family, alpha):
    return math.log(2 * m_family / alpha)


def hellinger(p, q):
    return math.sqrt(max(0.0, 1.0 - sum(math.sqrt(a * b) for a, b in zip(p, q))))


# ---- v0's plug-ins ----
def runs(dev):
    return [IBM / dev / "run"] + sorted((IBM / dev).glob("sheet-*/run"))


plug, objects = {}, {"three-way class": {}, "crystal count": {}}
for dev in DEVICES:
    jobs = []
    for run in runs(dev):
        rec = json.loads((run / "law-pub0-law.json").read_text())
        counts = [(tuple(ones), n) for ones, n in rec["counts"]]
        n = sum(c for _, c in counts)
        five = [(Y, c) for Y, c in counts if len(Y) == N5]
        n5 = sum(c for _, c in five)
        forb = sum(c for Y, c in five if W[Y] == 0)
        jobs.append((n, n5, forb, sum(c * W[Y] for Y, c in five) / 2304))
        weight = [0] * (NSITES + 1)
        for Y, c in counts:
            weight[len(Y)] += c
        objects["crystal count"].setdefault(dev, []).append([w / n for w in weight])
        objects["three-way class"].setdefault(dev, []).append([(n5 - forb) / n, forb / n, (n - n5) / n])
    tn, t5, tf, tx = (sum(j[i] for j in jobs) for i in range(4))
    means = {"five-crystal share": t5 / tn, "forbidden share": tf / t5, "linear XEB": tx / t5}
    drift = {"five-crystal share": max(abs(j[1] / j[0] - means["five-crystal share"]) for j in jobs),
             "forbidden share": max(abs(j[2] / j[1] - means["forbidden share"]) for j in jobs),
             "linear XEB": max(abs(j[3] / j[1] - means["linear XEB"]) for j in jobs)}
    single = {}
    for k, basis in ((0, "<X0X1>"), (1, "<Y0Y1>")):
        rec = json.loads(next((IBM / dev / "run").glob(f"coherence-pub{k}-*.json")).read_text())
        shots = sum(c for _, c in rec["counts"])
        means[basis] = sum(c for ones, c in rec["counts"] if (0 in ones) == (1 in ones)) / shots
        single[basis] = [sum(c for ones, c in rec["counts"] if s not in ones) / shots for s in (0, 1)]   # P(z = +1)
    man = json.loads((IBM / dev / "bundle" / "manifest.json").read_text())
    snap = json.loads((IBM / dev / ("properties-" + man["target"]["calibration"].replace("-", "").replace(":", "")
                                    + ".json")).read_text())
    chain = next(j for j in man["jobs"] if j["job"] == "coherence")["circuits"][0]["chain"]
    pair = [chain[i] for i in man["pair"]]
    readout = []
    for q in pair:
        props = {e["name"]: e["value"] for e in snap["qubits"][q]}
        readout.append((props["prob_meas1_prep0"], props["prob_meas0_prep1"]))
    plug[dev] = {"means": means, "drift": drift, "single": single, "readout": readout, "pair": pair}

# R: the largest within-device Hellinger distance between two of v0's law jobs (sufficiency_v0.py's R)
R_V0 = {}
for name, b in (("three-way class", 3), ("crystal count", 17)):
    R_V0[name] = (b, max(hellinger(p, q) for dev in DEVICES
                         for p, q in itertools.combinations(objects[name][dev], 2)))

MEASURES = ("five-crystal share", "forbidden share", "linear XEB", "<X0X1>", "<Y0Y1>")
SCALE = {"five-crystal share": 1.0, "forbidden share": 1.0, "linear XEB": XEB_SCALE, "<X0X1>": 2.0, "<Y0Y1>": 2.0}

# ---- QPU charge: three models, from v0's 65 jobs (as sufficiency_v0.py) ----
points = []
for dev in DEVICES:
    for run in runs(dev):
        for role in ("known-answer", "law", "coherence"):
            if (run / f"{role}-metrics.json").exists():
                m = json.loads((run / f"{role}-metrics.json").read_text())
                shots = 0
                for p in sorted(run.glob(f"{role}-pub*.json")):
                    rec = json.loads(p.read_text())
                    assert rec["source"]["job_id"] == m["job_id"], (run, role)
                    shots += sum(c for _, c in rec["counts"])
                points.append((shots, m["metrics"]["usage"]["qpu_charge_time_seconds"]))
assert len(points) == 65, len(points)
LEFT_NOW = WINDOW - sum(q for _, q in points)        # what v0's 65 charges leave of the window
law_rate = max(q for s, q in points if s == 24576) / 24576
mx, my = sum(s for s, _ in points) / 65, sum(q for _, q in points) / 65
slope = sum((s - mx) * (q - my) for s, q in points) / sum((s - mx) ** 2 for s, _ in points)
icept = my - slope * mx
MODELS = (lambda n: law_rate * n, lambda n: icept + slope * n, lambda n: 2 + 0.00035 * n)


def unit_cost(job_shots):
    """(lowest, highest) over the three models of the unit's charge, each job rounded up to a whole second."""
    totals = [sum(math.ceil(f(s)) for s in job_shots) for f in MODELS]
    return min(totals), max(totals)


# ---- one unit's design ----
def design(shape, a, b, nc, d=3, r=3):
    if shape == "film":
        n_law, n_coh, per_pass, name = a, a, [2 * nc, 3 * a], f"film N={a:,}, Nc={nc:,}"
    else:
        n_law, n_coh, per_pass, name = a, b, [2 * nc, a, 2 * b], f"split NL={a:,}, NC={b:,}, Nc={nc:,}"
    return {"name": name, "d": d, "r": r, "n_law": n_law, "n_coh": n_coh, "nc": nc, "jobs": per_pass * (d * r)}


PER_DEVICE_EXTRA = 2 * 2 + 2 * 2          # the pair's single-site means (2 qubits, 2 bases), its readout (2 x 2)


def unit_family(dz):
    return len(MEASURES) * (dz["d"] * dz["r"] + dz["d"]) + PER_DEVICE_EXTRA * dz["d"]


def look_family(dz, k):
    pooled = (len(MEASURES) + PER_DEVICE_EXTRA) * dz["d"]
    return pooled * (1 + k) + len(MEASURES) * dz["d"] * k      # pooled, each contributor left out, unit means


def capacity(dz, k=1, look=False):
    """Projected certified intervals for k units of design dz pooled; look=False is one unit's own family."""
    d, r = dz["d"], dz["r"]
    if look:
        m_family, a = look_family(dz, k), ALPHA / (k * (k + 1))
    else:
        m_family, a = unit_family(dz), ALPHA
    bud = budget(m_family, a)
    out = {}
    for dev in DEVICES:
        p = plug[dev]["means"]
        n_pool = {"five-crystal share": k * r * dz["n_law"]}
        n_pool["forbidden share"] = n_pool["linear XEB"] = n_pool["five-crystal share"] * p["five-crystal share"]
        n_pool["<X0X1>"] = n_pool["<Y0Y1>"] = k * r * dz["n_coh"]
        out[dev] = {m: interval(p[m], n_pool[m], bud) for m in MEASURES}
        if not look:
            out[dev]["job"] = {m: interval(p[m], n_pool[m] / r, bud) for m in MEASURES}
        ups = [(interval(p01, k * r * dz["nc"], bud)[1], interval(p10, k * r * dz["nc"], bud)[1])
               for p01, p10 in plug[dev]["readout"]]
        amax = [max(u) for u in ups]                               # |a_q| <= max(p01, p10) <= its upper bound
        g_max = 1 - (1 - sum(ups[0])) * (1 - sum(ups[1]))         # 1 - f_1 f_2 at most
        out[dev]["readout"] = {}
        for m in ("<X0X1>", "<Y0Y1>"):
            ms = []                                               # |m'| at most, for each qubit of the pair
            for q01 in plug[dev]["single"][m]:
                lo, hi = interval(q01, n_pool[m], bud)
                ms.append(max(abs(2 * lo - 1), abs(2 * hi - 1)))
            offset = amax[0] * ms[1] + amax[1] * ms[0] + amax[0] * amax[1]
            lo, hi = (2 * x - 1 for x in out[dev][m])             # the measured parity's certified interval
            out[dev]["readout"][m] = {"offset": offset, "g": g_max, "true_lo": lo - offset,
                                      "true_hi": (hi + offset) / (1 - g_max)}
    return out, bud, m_family


def diff_lower(cap, a_dev, b_dev, m):
    """The certified lower end of |mean_A - mean_B|, in the measure's own units."""
    (alo, ahi), (blo, bhi) = cap[a_dev][m], cap[b_dev][m]
    return max(0.0, alo - bhi, blo - ahi) * SCALE[m]


def readout_parts(cap, a_dev, b_dev, m):
    """For a certified-sign difference: (shrinkage term g*P of the lower device, both offsets, the bound,
    and what both devices' shrinkage terms would sum to), or None."""
    ra, rb = cap[a_dev]["readout"][m], cap[b_dev]["readout"][m]
    (alo, ahi), (blo, bhi) = cap[a_dev][m], cap[b_dev][m]
    if ra["true_lo"] <= 0 or rb["true_lo"] <= 0 or not (alo > bhi or blo > ahi):
        return None
    low = rb if alo > bhi else ra
    shrink, offsets = low["g"] * low["true_hi"], ra["offset"] + rb["offset"]
    return shrink, offsets, shrink + offsets, ra["g"] * ra["true_hi"] + rb["g"] * rb["true_hi"]


def beyond_readout(cap, a_dev, b_dev, m):
    """The certified lower end of |true parity A - true parity B| once readout is allowed for, or None.

    If A's measured parity lies above B's (certified), readout can have widened the gap only by shrinking B more
    than A, plus both offsets: by at most g_B * (B's true parity, at most) + offset_A + offset_B, provided both
    true parities are certified positive. Symmetrically if B lies above A."""
    ra, rb = cap[a_dev]["readout"][m], cap[b_dev]["readout"][m]
    if ra["true_lo"] <= 0 or rb["true_lo"] <= 0:
        return None
    (alo, ahi), (blo, bhi) = cap[a_dev][m], cap[b_dev][m]
    if alo > bhi:
        return 2 * (alo - bhi) - (rb["g"] * rb["true_hi"] + ra["offset"] + rb["offset"])
    if blo > ahi:
        return 2 * (blo - ahi) - (ra["g"] * ra["true_hi"] + ra["offset"] + rb["offset"])
    return None


def strong_form(cap, a_dev, b_dev, m):
    """One unit's projected strong form: the certified difference less both devices' drift bounds U(D)."""
    u = [plug[x]["drift"][m] * SCALE[m] + (cap[x]["job"][m][1] - cap[x]["job"][m][0]) / 2 * SCALE[m]
         + (cap[x][m][1] - cap[x][m][0]) / 2 * SCALE[m] for x in (a_dev, b_dev)]
    return diff_lower(cap, a_dev, b_dev, m) - u[0] - u[1]


def hellinger_eps(n_law, m_laws):
    out = {}
    for name, (b, r_true) in R_V0.items():
        c = (b - 1) * math.log(2) + math.log(m_laws / ALPHA)
        out[name] = r_true + 4 * math.sqrt(-math.expm1(-c / n_law))
    return out


DESIGNS = ([design("film", n, None, nc) for n in (8192, 12288, 16384, 24576) for nc in (1024, 2048, 4096)]
           + [design("split", nl, ncoh, 2048) for nl, ncoh in ((24576, 8192), (24576, 16384), (16384, 16384))])

print("v0's plug-ins (MEASURED on v0's records; readout REPORTED at v0's freeze; coherence from one job a device):")
for dev in DEVICES:
    p, dr, sg = plug[dev]["means"], plug[dev]["drift"], plug[dev]["single"]
    print(f"  {dev}: five {p['five-crystal share']:.4f} (largest job deviation {dr['five-crystal share']:.4f}); "
          f"forbidden {p['forbidden share']:.4f} ({dr['forbidden share']:.4f}); "
          f"<X0X1> {2 * p['<X0X1>'] - 1:+.4f} (single-site {2 * sg['<X0X1>'][0] - 1:+.4f}, {2 * sg['<X0X1>'][1] - 1:+.4f}); "
          f"<Y0Y1> {2 * p['<Y0Y1>'] - 1:+.4f} (single-site {2 * sg['<Y0Y1>'][0] - 1:+.4f}, {2 * sg['<Y0Y1>'][1] - 1:+.4f}); "
          f"pair {plug[dev]['pair']} readout (p01, p10) "
          + ", ".join(f"({a:.4f}, {b:.4f})" for a, b in plug[dev]["readout"]))
print("  within-device Hellinger R over v0's 31 law jobs: "
      + "; ".join(f"{name} {r:.4f}" for name, (_, r) in R_V0.items()))
print(f"charge models: (a) {law_rate * 1000:.3f} ms a shot; (b) {icept:.2f} s + {slope * 1000:.3f} ms a shot; "
      f"(c) 2 s + 0.35 ms a shot; each job rounded up to a whole second. v0's 65 jobs were charged "
      f"{sum(q for _, q in points)} s, leaving {LEFT_NOW} of the window's {WINDOW}")

print(f"\n== 1. each design: 3 devices x 3 passes, interleaved; cost against the Open Plan's {WINDOW} s per 28 days "
      f"(and the {LEFT_NOW} s left after v0)")
print("  design | jobs | shots | QPU s, lowest to highest model | units a window (highest) | fits the left | "
      "Hellinger planning eps, 3-way / crystal | <X0X1> K-F: certified |diff| at least; and beyond readout")
for dz in DESIGNS:
    lo, hi = unit_cost(dz["jobs"])
    cap, bud, mf = capacity(dz)
    he = hellinger_eps(dz["n_law"], dz["d"] * dz["r"])
    low = diff_lower(cap, "ibm_kingston", "ibm_fez", "<X0X1>")
    br = beyond_readout(cap, "ibm_kingston", "ibm_fez", "<X0X1>")
    print(f"  {dz['name']} | {len(dz['jobs'])} | {sum(dz['jobs']):,} | {lo} to {hi} | {WINDOW // hi} | "
          f"{'yes' if hi <= LEFT_NOW else 'no'} | {he['three-way class']:.3f} / {he['crystal count']:.3f} | "
          f"{low:.4f}; " + ("not certified" if br is None else f"{br:+.4f}"))

for name in ("film N=16,384, Nc=2,048", "film N=24,576, Nc=2,048", "split NL=24,576, NC=8,192, Nc=2,048"):
    dz = next(x for x in DESIGNS if x["name"] == name)
    cap, bud, mf = capacity(dz)
    print(f"\n== 2. one unit of {name}: its own family of {mf} intervals at alpha {ALPHA} (budget {bud:.3f})")
    for dev in DEVICES:
        row = []
        for m in MEASURES:
            lo, hi = cap[dev][m]
            jlo, jhi = cap[dev]["job"][m]
            row.append(f"{m} pool +-{(hi - lo) / 2 * SCALE[m]:.4f}, job +-{(jhi - jlo) / 2 * SCALE[m]:.4f}")
        print(f"  {dev}: " + "; ".join(row))
        ro = cap[dev]["readout"]["<X0X1>"]
        print(f"    the pair's readout on <X0X1>: the parity shrinks by a factor of at least {1 - ro['g']:.4f}; "
              f"the offset is at most {ro['offset']:.6f}")
    for a_dev, b_dev in itertools.combinations(DEVICES, 2):
        cells = []
        for m in MEASURES:
            low = diff_lower(cap, a_dev, b_dev, m)
            cell = f"{m} {'differ' if low > 0 else 'unresolved'} ({low:.4f})"
            if m in ("five-crystal share", "forbidden share", "linear XEB"):
                cell += f", strong form {strong_form(cap, a_dev, b_dev, m):+.4f}"
            else:
                br = beyond_readout(cap, a_dev, b_dev, m)
                cell += ", beyond readout " + ("not certified" if br is None else f"{br:+.4f}")
                parts = readout_parts(cap, a_dev, b_dev, m)
                if parts:
                    cell += (f" [readout bound {parts[2]:.4f}: the lower device's shrinkage {parts[0]:.4f} plus both "
                             f"offsets {parts[1]:.4f}; both devices' shrinkage would sum to {parts[3]:.4f}]")
            cells.append(cell)
        print(f"  {SHORT[a_dev]}-{SHORT[b_dev]}, projected at eps = 0: " + "; ".join(cells))

print("\n== 3. the strong form within one unit, on the five-crystal share: the fewest shots a film PUB would need")
print("   (each design's other settings as film N, Nc=2,048), under v0's drift; the free tier allows about 16,384.")
print("   The strong form grows with N, so the least N is found by bisection on whole shots.")


def clears(n, a_dev, b_dev):
    cap, _, _ = capacity(design("film", n, None, 2048))
    return strong_form(cap, a_dev, b_dev, "five-crystal share") > 0


for a_dev, b_dev in itertools.combinations(DEVICES, 2):
    m = "five-crystal share"
    limit = (abs(plug[a_dev]["means"][m] - plug[b_dev]["means"][m]) - plug[a_dev]["drift"][m]
             - plug[b_dev]["drift"][m])        # the strong form as N grows without bound: |difference| less both drifts
    lo, hi = 16384, 1048576
    if clears(lo, a_dev, b_dev):             # the bracket's low end must fail, or the search is void; not an
        sys.exit(f"REFUSED: the search's low end already clears for {a_dev}, {b_dev}")   # assert, which -O strips
    if not clears(hi, a_dev, b_dev):
        print(f"  {SHORT[a_dev]}-{SHORT[b_dev]}: more than {hi:,} shots; as N grows the strong form tends to "
              f"{limit:+.4f}, " + ("so it never clears under v0's drift" if limit <= 0 else "so it clears beyond"))
        continue
    while hi - lo > 1:                      # clears(hi) holds and clears(lo) does not
        mid = (lo + hi) // 2
        (lo, hi) = (lo, mid) if clears(mid, a_dev, b_dev) else (mid, hi)
    print(f"  {SHORT[a_dev]}-{SHORT[b_dev]}: {hi:,} shots; as N grows the strong form tends to {limit:+.4f}")

print("\n== 4. k units pooled, look k spending alpha/(k(k+1)) over everything the look computes: the fewest units at")
print("   which each projected difference is certified (eps = 0); for the coherences, also beyond the pooled readout")
print("   bound; '>100' if not by 100. Each unit is taken from a different contributor.")
for name in ("film N=16,384, Nc=2,048", "film N=16,384, Nc=4,096", "film N=24,576, Nc=2,048"):
    dz = next(x for x in DESIGNS if x["name"] == name)
    found = {}
    for k in range(1, 101):
        cap, bud, mf = capacity(dz, k, look=True)
        for a_dev, b_dev in itertools.combinations(DEVICES, 2):
            for m in MEASURES:
                if diff_lower(cap, a_dev, b_dev, m) > 0:
                    found.setdefault((a_dev, b_dev, m, "differ"), k)
                if m in ("<X0X1>", "<Y0Y1>"):
                    br = beyond_readout(cap, a_dev, b_dev, m)
                    if br is not None and br > 0:
                        found.setdefault((a_dev, b_dev, m, "beyond readout"), k)
    print(f"  {name} (look 10's family: {look_family(dz, 10)} intervals):")
    for a_dev, b_dev in itertools.combinations(DEVICES, 2):
        cells = []
        for m in MEASURES:
            v0_diff = (plug[a_dev]["means"][m] - plug[b_dev]["means"][m]) * SCALE[m]
            cell = f"{m} ({v0_diff:+.4f}): {found.get((a_dev, b_dev, m, 'differ'), '>100')}"
            if m in ("<X0X1>", "<Y0Y1>"):
                cell += f", beyond readout {found.get((a_dev, b_dev, m, 'beyond readout'), '>100')}"
            cells.append(cell)
        print(f"    {SHORT[a_dev]}-{SHORT[b_dev]}: " + "; ".join(cells))
