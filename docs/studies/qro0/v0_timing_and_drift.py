"""Timing and drift on Quantum-Film's IBM records of 2026-10-05: the figures study QRO-0 quotes in sections
4.4, 6 and 6.1. An instrument: stdlib only, read-only, run with python -I.

  1. The clock: a git commit time is truncated to the second (measured on this desktop, git 2.45.2), so the
     commit adding a job line, which contains IBM's created time, bounds the local clock's lag below by
     created - (commit second + 1). fixed_at (local) is written after IBM's finished time, which bounds it
     by finished - fixed_at. Both maxima assume one constant offset over the day.
  2. The execution spans (no timezone in the payload), read as UTC: do they fall inside [running, finished]?
  3. The gap from each bundle's known-answer job to its law job, by created time and between shots.
  4. Drift: each law job's five-crystal share, forbidden share and linear XEB (compare.py's formula, exactly),
     per device the between-run SD beside one run's sampling error, and kingston against fez.
  5. Readout's share of the coherence difference, under a confusion model, the coherence values held to the
     committed records.
  6. Which bytes stay equal: each sheet's law QPY and gate list against its morning bundle's; options digests.
  7. When each device ran: the law jobs' blocks, the largest step, and every job of the day in created order.

Usage: python -I v0_timing_and_drift.py <path to moth-quantum>
"""
import itertools
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime, timezone
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

# ---- the law, as compare.py has it: integer det weights over 16^5, D = 4,368 layouts (held below) ----
L, NSITES, N = 4, 16, 5
COS = (1, 0, -1, 0)
DISC = [(kx, ky) for kx in (-1, 0, 1) for ky in (-1, 0, 1) if kx * kx + ky * ky <= 1]
SITES = [divmod(s, L) for s in range(NSITES)]
A = [[sum(COS[(kx * (xi - xj) + ky * (yi - yj)) % L] for kx, ky in DISC) for (xj, yj) in SITES]
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


W = {Y: int(det([[A[i][j] for j in Y] for i in Y])) for Y in itertools.combinations(range(NSITES), N)}
DEN, D = NSITES ** N, len(W)
assert D == 4368 and sum(W.values()) == DEN and sum(1 for w in W.values() if w == 0) == 1360
NORM = Fraction(sum(w * w for w in W.values()), DEN * DEN) - Fraction(1, D)


def xeb(counts):
    five = [(tuple(ones), n) for ones, n in counts if len(ones) == N]
    n = sum(c for _, c in five)
    s1 = sum(c * W[Y] for Y, c in five)
    s2 = sum(c * W[Y] ** 2 for Y, c in five)
    value = (Fraction(s1, n * DEN) - Fraction(1, D)) / NORM
    var = (Fraction(s2, DEN * DEN) - Fraction(s1 * s1, n * DEN * DEN)) / (n - 1)
    return value, math.sqrt(var / n) / float(NORM)


def utc(s):
    """An ISO time; a naive one (the spans) is read as UTC."""
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def spans(raw):
    v = raw["__value__"]["metadata"]["execution"]["execution_spans"]["__value__"]["spans"]
    return [(utc(s["__value__"]["start"]["__value__"]), utc(s["__value__"]["stop"]["__value__"])) for s in v]


def commit_time(path):
    rel = path.relative_to(ROOT).as_posix()
    out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%ct", "--", rel], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.split()
    assert len(out) == 1, (rel, out)
    return datetime.fromtimestamp(int(out[0]), tz=timezone.utc)


jobs = []          # one entry per job
for dev in DEVICES:
    for run in [IBM / dev / "run"] + sorted((IBM / dev).glob("sheet-*/run")):
        for role in ("known-answer", "law", "coherence"):
            line_path = run / f"{role}-line.json"
            if not line_path.exists():
                continue
            line = json.loads(line_path.read_text())
            met = json.loads((run / f"{role}-metrics.json").read_text())["metrics"]["timestamps"]
            raw = json.loads((run / f"{role}-raw.json").read_text())
            recs = [json.loads(p.read_text()) for p in sorted(run.glob(f"{role}-pub*.json"))]
            jobs.append({"dev": dev, "run": run, "role": role, "job": line["job_id"],
                         "created": utc(line["submitted_at"]), "running": utc(met["running"]),
                         "finished": utc(met["finished"]), "spans": spans(raw),
                         "commit": commit_time(line_path), "recs": recs})
assert len(jobs) == 65, len(jobs)

print("== 1. the clock (local behind IBM's, lower bounds, seconds)")
line_lag = [((j["created"] - j["commit"]).total_seconds() - 1.0, j) for j in jobs]
fix_lag = [((j["finished"] - utc(r["source"]["fixed_at"])).total_seconds(), j) for j in jobs for r in j["recs"]]
checked = next(j for j in jobs if j["job"] == "db1nn11b694s73dsidjg")
print(f"  job db1nn11b694s73dsidjg alone: line commit gives {(checked['created'] - checked['commit']).total_seconds() - 1:.6f}; "
      f"fixed_at gives {(checked['finished'] - utc(checked['recs'][0]['source']['fixed_at'])).total_seconds():.6f}")
for name, lags in (("line commits (65 jobs)", line_lag), ("fixed_at (68 records)", fix_lag)):
    vals = sorted(v for v, _ in lags)
    best = max(lags, key=lambda t: t[0])
    print(f"  {name}: largest bound {best[0]:.6f} (job {best[1]['job']}), median {statistics.median(vals):.6f}, "
          f"smallest {vals[0]:.6f}; positive in {sum(v > 0 for v in vals)} of {len(vals)}")

print("\n== 2. the spans, read as UTC")
inside = sum(all(j["running"] <= a and b <= j["finished"] for a, b in j["spans"]) for j in jobs)
print(f"  jobs whose every span lies inside [running, finished]: {inside} of {len(jobs)}; "
      f"spans per job: {sorted({len(j['spans']) for j in jobs})}")
delay = [(j["spans"][0][0] - j["running"]).total_seconds() for j in jobs]
print(f"  running to the first shot: {min(delay):.1f} to {max(delay):.1f} s (median {statistics.median(delay):.1f})")

print("\n== 3. known answer to law, per bundle")
by_run = {}
for j in jobs:
    by_run.setdefault(j["run"], {})[j["role"]] = j
gaps_c = [(b["law"]["created"] - b["known-answer"]["created"]).total_seconds() for b in by_run.values()]
gaps_s = [(b["law"]["spans"][0][0] - b["known-answer"]["spans"][-1][1]).total_seconds() for b in by_run.values()]
print(f"  {len(by_run)} bundles; by created time {min(gaps_c):.1f} to {max(gaps_c):.1f} s (median {statistics.median(gaps_c):.1f}); "
      f"known answer's last shot to law's first shot {min(gaps_s):.1f} to {max(gaps_s):.1f} s (median {statistics.median(gaps_s):.1f})")

print("\n== 4. drift over the law jobs")
law = {dev: [] for dev in DEVICES}
for j in jobs:
    if j["role"] != "law":
        continue
    (rec,) = j["recs"]
    counts = rec["counts"]
    shots = sum(n for _, n in counts)
    five = sum(n for ones, n in counts if len(ones) == N)
    forb = sum(n for ones, n in counts if len(ones) == N and W[tuple(ones)] == 0)
    x, xse = xeb(counts)
    law[j["dev"]].append({"job": j["job"], "created": j["created"], "five": five / shots,
                          "five_se": math.sqrt((five / shots) * (1 - five / shots) / shots),
                          "forb": forb / five, "forb_se": math.sqrt((forb / five) * (1 - forb / five) / five),
                          "xeb": float(x), "xeb_se": xse, "xeb_exact": x})
first = min(law["ibm_kingston"], key=lambda r: r["created"])
# held, not printed: the published row of HARDWARE-RESULTS.md:120 (READ), to its four places
assert (round(first["xeb"], 4), round(first["xeb_se"], 4), round(first["five"], 4), round(first["forb"], 4)) == (0.8444, 0.0117, 0.6095, 0.0431), first
print(f"  held to HARDWARE-RESULTS.md: kingston's first law job {first['job']} XEB {first['xeb']:+.4f} +- {first['xeb_se']:.4f}, "
      f"five-crystal share {first['five']:.4f}, forbidden {first['forb']:.4f}")
stats = {}
for dev, rows in law.items():
    stats[dev] = {}
    for m in ("five", "forb", "xeb"):
        vals = [r[m] for r in rows]
        sd = statistics.stdev(vals)
        se = statistics.mean(r[m + "_se"] for r in rows)
        stats[dev][m] = (len(vals), statistics.mean(vals), sd, se)
    print(f"  {dev} ({len(rows)} law jobs): " + "; ".join(
        f"{m}: mean {mu:.4f}, between-run SD {sd:.4f}, one run's sampling SE {se:.4f}, SD/SE {sd / se:.1f}"
        for m, (n, mu, sd, se) in stats[dev].items()))
print("  kingston against fez (pooled SD: equal weights, as section 6.1 states; df-weighted beside it):")
for m in ("five", "forb", "xeb"):
    n1, m1, s1, _ = stats["ibm_kingston"][m]
    n2, m2, s2, _ = stats["ibm_fez"][m]
    pooled = math.sqrt((s1 * s1 + s2 * s2) / 2)
    welch = (m1 - m2) / math.sqrt(s1 * s1 / n1 + s2 * s2 / n2)
    pooled_df = math.sqrt(((n1 - 1) * s1 * s1 + (n2 - 1) * s2 * s2) / (n1 + n2 - 2))
    print(f"    {m}: difference of means {m1 - m2:+.4f} = {(m1 - m2) / pooled:+.2f} pooled between-run SDs ({(m1 - m2) / pooled_df:+.2f} df-weighted); Welch t {welch:+.1f}")

print("\n== 5. readout's share of the coherence difference, under a model (conditional, not checked)")
print("  model: an independent classical confusion on each measured qubit, with the freeze-time snapshot's")
print("  prob_meas1_prep0 (p01) and prob_meas0_prep1 (p10), REPORTED; E[z'] = (p10 - p01) + (1 - p01 - p10) z;")
print("  the law's single-site <X> is 0, so the pair's measured parity is a_a a_b + f_a f_b <XX>.")
law_xx = Fraction(3, 8)
measured = {"ibm_kingston": 0.3315, "ibm_fez": 0.2690}            # HARDWARE-RESULTS.md:46, READ
for dev, published in measured.items():                           # ... and held to the committed records
    rec = json.loads((IBM / dev / "run" / "coherence-pub0-coherence-xx.json").read_text())
    agree = sum(n for ones, n in rec["counts"] if (0 in ones) == (1 in ones))
    assert round(2 * agree / sum(n for _, n in rec["counts"]) - 1, 4) == published, (dev, agree)
model = {}
for dev in DEVICES:
    man = json.loads((IBM / dev / "bundle" / "manifest.json").read_text())
    stamp = man["target"]["calibration"].replace("-", "").replace(":", "")
    snap = json.loads((IBM / dev / f"properties-{stamp}.json").read_text())
    coh = next(j for j in man["jobs"] if j["job"] == "coherence")
    chain = coh["circuits"][0]["chain"]
    pair = [chain[i] for i in man["pair"]]
    fa = []
    for q in pair:
        props = {e["name"]: e["value"] for e in snap["qubits"][q]}
        p01, p10 = props["prob_meas1_prep0"], props["prob_meas0_prep1"]
        fa.append((p10 - p01, 1 - p01 - p10))
    value = fa[0][0] * fa[1][0] + fa[0][1] * fa[1][1] * float(law_xx)
    model[dev] = value
    print(f"  {dev}: snapshot {man['target']['calibration']}, physical pair {pair}, "
          f"attenuation f_a f_b = {fa[0][1] * fa[1][1]:.4f}; the law's +0.375 would read {value:+.4f}")
gap = model["ibm_kingston"] - model["ibm_fez"]
print(f"  kingston minus fez from readout alone, under the model: {gap:+.4f}, "
      f"against the measured {measured['ibm_kingston'] - measured['ibm_fez']:+.4f}")

print("\n== 6. which bytes stay equal: the law circuit's QPY and gate list, each sheet against its morning bundle")
qpy_differs = gates_differs = sheets = 0
for dev in DEVICES:
    def law_entry(bundle_dir):
        man = json.loads((bundle_dir / "manifest.json").read_text())
        return next(c for j in man["jobs"] for c in j["circuits"] if c["role"] == "law")
    morning = law_entry(IBM / dev / "bundle")
    for b in sorted((IBM / dev).glob("sheet-*/bundle")):
        e = law_entry(b)
        sheets += 1
        qpy_differs += e["isa_sha256"] != morning["isa_sha256"]
        gates_differs += e["gates_sha256"] != morning["gates_sha256"]
print(f"  of {sheets} sheet law circuits: QPY bytes differ from the morning's (the predicted) in {qpy_differs}; "
      f"gate lists differ in {gates_differs}")
manifests = [json.loads(p.read_text()) for p in sorted(IBM.glob("*/bundle/manifest.json"))
             + sorted(IBM.glob("*/sheet-*/bundle/manifest.json"))]
print(f"  across all {len(manifests)} bundles: options digests {sorted({m['options_sha256'][:16] for m in manifests})}; "
      f"program and route {sorted({(m['program'], m['route']) for m in manifests})}")

print("\n== 7. when each device's law jobs ran: the blocks (created times, UTC) and the largest step between consecutive jobs")
blocks = {}
for dev in DEVICES:
    rows = sorted(law[dev], key=lambda r: r["created"])
    morning, sheets = rows[0], rows[1:]
    blocks[dev] = (sheets[0]["created"], sheets[-1]["created"])
    step = max(zip(sheets, sheets[1:]), key=lambda ab: abs(ab[1]["five"] - ab[0]["five"]))
    print(f"  {dev}: morning job {morning['created'].strftime('%H:%M:%S')}; sheet jobs {sheets[0]['created'].strftime('%H:%M:%S')}"
          f" to {sheets[-1]['created'].strftime('%H:%M:%S')} ({len(sheets)} jobs); largest step in five-crystal share "
          f"{step[1]['five'] - step[0]['five']:+.4f} between {step[0]['created'].strftime('%H:%M:%S')} and "
          f"{step[1]['created'].strftime('%H:%M:%S')}")
overlap = any(blocks[a][0] <= blocks[b][1] and blocks[b][0] <= blocks[a][1] for a in DEVICES for b in DEVICES if a < b)
print(f"  the three sheet blocks {'overlap' if overlap else 'are disjoint in time: device and time block differ together'}")
print("  every job of the day, all roles, in created order, by device (K kingston, M marrakesh, F fez):")
order = sorted(jobs, key=lambda j: j["created"])
for label, part in (("morning", [j for j in order if j["run"].parent.name.startswith("ibm_")]),
                    ("sheets", [j for j in order if j["run"].parent.name.startswith("sheet-")])):
    seq = "".join(j["dev"][4].upper() for j in part)
    runs = [seq[0]] + [b for a, b in zip(seq, seq[1:]) if a != b]
    spans_by = {d: (min(j["created"] for j in part if j["dev"] == d), max(j["created"] for j in part if j["dev"] == d))
                for d in DEVICES}
    print(f"    {label}: {len(part)} jobs, {seq}; the device changes {len(runs) - 1} times, so "
          + ("each device's jobs form one block: " if len(runs) == len(DEVICES) else "the devices interleave: ")
          + "; ".join(f"{d} {a.strftime('%H:%M:%S')} to {b.strftime('%H:%M:%S')}" for d, (a, b) in spans_by.items()))
