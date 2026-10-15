"""What the calibrations in force at execution change: for study QRO-0, after the read of 2026-10-14
(records/2026-10-14/ibm-refetch, made by ibm_refetch_v0.py with the owner's key). Stdlib only, read-only.

It refuses unless moth-quantum is a clean 3a73823 and the read's MANIFEST, and every file it lists, hash as the
study records them. Then:
  1. which snapshot IBM's history returned for each job's first shot (the link the read recorded), and what each
     bundle was frozen against: one morning bundle and the sheet bundles per device, and whether each freeze
     snapshot is carried by any record. The predictions' snapshots are compared with their freezes;
  2. how far each execution-time snapshot is from the morning bundle's freeze, and from the sheet bundles' freeze
     where a record carries it, device-wide and on the device's own chain: the 16 qubits' readout and coherence
     times, and the CZ couplers between consecutive chain qubits;
  3. section 6.1's readout model, rerun with the execution-time snapshots in place of the freeze-time ones;
  4. the jobs whose `running` time and first shot fall under different returned snapshots;
  5. how long after its stamp each snapshot first appears in IBM's history, bounded by the read's own queries,
     and the jobs whose first shot falls in that gap under a newer snapshot already stamped and measured.

Usage: python -I calibration_at_execution_v0.py <QRO-Crate root> <moth-quantum root>
"""
import hashlib
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

if __name__ != "__main__":
    raise ImportError("an instrument, not a module")

QRO, MOTH = Path(sys.argv[1]), Path(sys.argv[2])
MANIFEST_SHA256 = "1761adbb0536875ea51f4dd45c4013a1dd32e005a5aacc2105ca3d9170719388"   # the study's section 15


def pinned(root, want="3a73823"):
    """Refuse unless the tree read is a clean checkout of the commit the study names."""
    import subprocess
    head = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], cwd=root, capture_output=True, text=True,
                          check=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True,
                           check=True).stdout.strip()
    if head != want or dirty:
        sys.exit(f"REFUSED: moth-quantum is at {head}{' with uncommitted changes' if dirty else ''}, not a clean {want}")


def held(fetch):
    """Refuse unless the read's MANIFEST is the one the study names, the directory holds exactly the files it
    lists, and every one of them still hashes as listed."""
    raw = (fetch / "MANIFEST.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        sys.exit("REFUSED: records/2026-10-14/ibm-refetch/MANIFEST.json is not the one the study names")
    listed = json.loads(raw)["files"]
    present = {p.relative_to(fetch).as_posix() for p in fetch.rglob("*") if p.is_file()} - {"MANIFEST.json"}
    if present != {f["path"] for f in listed}:
        sys.exit(f"REFUSED: the read's directory does not hold exactly the files its MANIFEST lists: "
                 f"{sorted(present ^ {f['path'] for f in listed})[:5]}")
    for f in listed:
        data = (fetch / f["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != f["sha256"] or len(data) != f["bytes"]:
            sys.exit(f"REFUSED: {f['path']} does not hash as its MANIFEST lists")


pinned(MOTH)
FETCH = QRO / "records" / "2026-10-14" / "ibm-refetch"
held(FETCH)
IBM = MOTH / "docs" / "records" / "2026-10-05" / "ibm"
DEVICES = ("ibm_kingston", "ibm_marrakesh", "ibm_fez")
MEASURED_XX = {"ibm_kingston": 0.3315, "ibm_marrakesh": 0.3135, "ibm_fez": 0.2690}   # HARDWARE-RESULTS.md:46, READ
for _dev, _published in MEASURED_XX.items():                                         # ... and held to the records
    _rec = json.loads((IBM / _dev / "run" / "coherence-pub0-coherence-xx.json").read_text())
    _agree = sum(n for ones, n in _rec["counts"] if (0 in ones) == (1 in ones))
    assert round(2 * _agree / sum(n for _, n in _rec["counts"]) - 1, 4) == _published, (_dev, _agree)


def utc(s):
    t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return (t if t.tzinfo else t.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def file_stamp(t):
    return utc(t).strftime("%Y%m%dT%H%M%SZ")


def qubit_props(snap):
    return [{e["name"]: e["value"] for e in q} for q in snap["qubits"]]


def gate_errors(snap):
    out = {}
    for g in snap["gates"]:
        for p in g.get("parameters", []):
            if p["name"] == "gate_error":
                out[(g["gate"], tuple(g["qubits"]))] = p["value"]
    return out


def all_values(snap, field="value"):
    """Every (where, name) -> its value (or its own measurement date) in a snapshot, for counting what changed."""
    vals = {}
    for i, q in enumerate(snap["qubits"]):
        for e in q:
            vals[("qubit", i, e["name"])] = e.get(field)
    for g in snap["gates"]:
        for p in g.get("parameters", []):
            vals[("gate", g["gate"], tuple(g["qubits"]), p["name"])] = p.get(field)
    return vals


def differing(a, b):
    va, vb = all_values(a), all_values(b)
    common = set(va) & set(vb)
    return sum(1 for k in common if va[k] != vb[k]), len(common)


def newest_value_date(snap):
    return max(utc(v) for v in all_values(snap, "date").values() if v)


def carried(dev, stamp):
    """The snapshot stamped `stamp`, from moth-quantum's records or the 2026-10-14 read, or None if neither holds it."""
    for where in (IBM / dev, FETCH / dev):
        p = where / f"properties-{file_stamp(stamp)}.json"
        if p.exists():
            return json.loads(p.read_text())
    return None


def cz(errors, coupler):
    """A coupler's CZ error, in either qubit order, or None when the snapshot has none."""
    for key in (("cz", coupler), ("cz", coupler[::-1])):
        if key in errors:
            return errors[key]
    return None


records = [json.loads(p.read_text()) for p in sorted(FETCH.glob("ibm_*/db*.json"))]
assert len(records) == 65, len(records)
manifests = {dev: [json.loads((IBM / dev / "bundle" / "manifest.json").read_text())]
             + [json.loads(p.read_text()) for p in sorted((IBM / dev).glob("sheet-*/bundle/manifest.json"))]
             for dev in DEVICES}

print("== 1. the snapshot IBM's history returned for each job's first shot, and what each bundle was frozen against")
for dev in DEVICES:
    morning, sheets = manifests[dev][0], manifests[dev][1:]
    freeze = carried(dev, morning["target"]["calibration"])
    pred_stamp = utc(json.loads((IBM / dev / "prediction-backend.json").read_text())["calibration"])
    pred = carried(dev, pred_stamp)
    d, n = differing(pred, freeze)
    print(f"  {dev}: morning bundle frozen against {morning['target']['calibration']}; its prediction built from "
          f"{pred['last_update_date']}, which differs from that freeze in {d} of {n} values")
    for st in sorted({m["target"]["calibration"] for m in sheets}):
        k = sum(1 for m in sheets if m["target"]["calibration"] == st)
        print(f"    {k} sheet bundles frozen against {st}: "
              + ("carried by the 2026-10-14 read" if carried(dev, st) else "no record carries that snapshot"))
    by = {}
    for r in (r for r in records if r["device"] == dev):
        by.setdefault(r["calibration"]["before_first_shot"]["stamp"], []).append(r)
    for st, rs in sorted(by.items()):
        first = min(utc(r["calibration"]["first_shot"]) for r in rs)
        gap = (first - utc(st)).total_seconds() / 60
        print(f"    returned for {len(rs)} first shots ({', '.join(sorted({r['role'] for r in rs}))}): {st}, "
              f"the earliest of those shots {gap:.0f} min after the stamp")

print("\n== 2. execution-time snapshots against the morning bundle's freeze (and the sheet bundles' freeze where carried)")
for dev in DEVICES:
    morning, sheets = manifests[dev][0], manifests[dev][1:]
    freeze = carried(dev, morning["target"]["calibration"])
    sheet_freezes = {m["target"]["calibration"] for m in sheets}
    chain = next(c for j in morning["jobs"] for c in j["circuits"] if c["role"] == "law")["chain"]
    couplers = list(zip(chain, chain[1:]))
    fq, fg, fall, fdate = qubit_props(freeze), gate_errors(freeze), all_values(freeze), all_values(freeze, "date")
    for snap_path in sorted((FETCH / dev).glob("properties-*.json")):
        snap = json.loads(snap_path.read_text())
        sq, sg, sall, sdate = qubit_props(snap), gate_errors(snap), all_values(snap), all_values(snap, "date")
        common = set(fall) & set(sall)
        changed = sum(1 for k in common if fall[k] != sall[k])
        redated = sum(1 for k in common if fdate.get(k) != sdate.get(k))
        newest = newest_value_date(snap)
        after = (newest - utc(snap["last_update_date"])).total_seconds() / 60
        print(f"  {dev} {snap['last_update_date']} against the morning freeze {freeze['last_update_date']}: "
              f"{changed} of {len(common)} values differ; {redated} carry a different measurement date; "
              f"the newest measurement date inside it is {newest.isoformat()}, {after:.2f} min after its stamp")
        if 0 < changed <= 10:
            for k in sorted(k for k in common if fall[k] != sall[k]):
                qubits = k[1] if k[0] == "qubit" else k[2]
                qubits = (qubits,) if isinstance(qubits, int) else qubits
                print(f"    changed: {k}, {fall[k]} -> {sall[k]}; "
                      f"{'on' if set(qubits) <= set(chain) else 'not on'} the chain {chain[0]}..{chain[-1]}")
        for st in sorted(sheet_freezes):
            sf = carried(dev, st)
            if sf is not None and sf["last_update_date"] not in (freeze["last_update_date"], snap["last_update_date"]):
                d, n = differing(sf, snap)
                print(f"    against the sheet bundles' freeze {st}: {d} of {n} values differ")
        for name in ("readout_error", "prob_meas1_prep0", "prob_meas0_prep1", "T1", "T2"):
            d = [sq[q][name] - fq[q][name] for q in chain if name in sq[q] and name in fq[q]]
            print(f"    chain {name}: mean change {statistics.mean(d):+.4g}, largest |change| {max(abs(x) for x in d):.4g} "
                  f"(freeze mean {statistics.mean(fq[q][name] for q in chain):.4g})")
        pairs = [(cz(sg, c), cz(fg, c)) for c in couplers]
        dz = [a - b for a, b in pairs if a is not None and b is not None]
        print(f"    chain CZ gate_error over {len(dz)} couplers: mean change {statistics.mean(dz):+.4g}, "
              f"largest |change| {max(abs(x) for x in dz):.4g} "
              f"(freeze mean {statistics.mean(b for _, b in pairs if b is not None):.4g})")

print("\n== 3. the readout model of section 6.1, on the snapshot each coherence job ran under (conditional, REPORTED inputs)")
model = {}
for dev in DEVICES:
    man = manifests[dev][0]
    coh = next(r for r in records if r["device"] == dev and r["role"] == "coherence")
    snap = json.loads((FETCH / coh["calibration"]["before_first_shot"]["file"]).read_text())
    chain = next(j for j in man["jobs"] if j["job"] == "coherence")["circuits"][0]["chain"]
    pair = [chain[i] for i in man["pair"]]
    q = qubit_props(snap)
    terms = [((q[p]["prob_meas0_prep1"] - q[p]["prob_meas1_prep0"]), 1 - q[p]["prob_meas1_prep0"] - q[p]["prob_meas0_prep1"])
             for p in pair]
    model[dev] = terms[0][0] * terms[1][0] + terms[0][1] * terms[1][1] * 0.375
    created = utc(coh["holds"]["created_ibm"])
    ages = []
    for p_ in pair:
        for e in snap["qubits"][p_]:
            if e["name"] in ("prob_meas0_prep1", "prob_meas1_prep0"):
                ages.append((created - utc(e["date"])).total_seconds() / 3600)
    print(f"  {dev}: the pair's readout values were measured {min(ages):.1f} to {max(ages):.1f} h before the job was created")
    print(f"  {dev}: coherence job {coh['job_id']} ran under {snap['last_update_date']}; pair {pair}; "
          f"attenuation {terms[0][1] * terms[1][1]:.4f}; the law's +0.375 would read {model[dev]:+.4f} "
          f"(measured {MEASURED_XX[dev]:+.4f})")
print(f"  kingston minus fez from readout alone: {model['ibm_kingston'] - model['ibm_fez']:+.4f}, "
      f"against the measured {MEASURED_XX['ibm_kingston'] - MEASURED_XX['ibm_fez']:+.4f}")

print("\n== 4. jobs whose `running` time and first shot fall under different returned snapshots")
cross = [r for r in records if r["calibration"]["before_running"]["stamp"] != r["calibration"]["before_first_shot"]["stamp"]]
for r in cross:
    c = r["calibration"]
    print(f"  {r['device']} {r['role']} {r['job_id']}: running {c['running']} under {c['before_running']['stamp']}; "
          f"first shot {c['first_shot']} under {c['before_first_shot']['stamp']}")
print(f"  {len(cross)} of {len(records)}")

print("\n== 5. when each snapshot first appears in IBM's history, bounded by the read's own queries; and the jobs whose")
print("   first shot falls after a newer snapshot's stamp and newest value date but before the history returned it")
in_gap = []
for dev in DEVICES:
    queries = []                                  # (time queried, stamp returned), both links of every job
    for r in (r for r in records if r["device"] == dev):
        for link in ("before_running", "before_first_shot"):
            queries.append((utc(r["calibration"][link]["queried_at"]), r["calibration"][link]["stamp"]))
    snaps = sorted({json.loads(p.read_text())["last_update_date"] for p in (FETCH / dev).glob("properties-*.json")},
                   key=utc)
    for st in snaps:
        t0 = utc(st)
        later_misses = [q for q, got in queries if q > t0 and utc(got) < t0]
        hits = [q for q, got in queries if got == st]
        lo = (max(later_misses) - t0).total_seconds() / 60 if later_misses else None
        hi = (min(hits) - t0).total_seconds() / 60 if hits else None
        print(f"  {dev} {st}: first returned {hi:.1f} min after its stamp at the latest"
              + (f"; not yet returned {lo:.1f} min after it" if lo is not None else "; no earlier query bounds it"))
    for r in (r for r in records if r["device"] == dev):
        shot, got = utc(r["calibration"]["first_shot"]), r["calibration"]["before_first_shot"]["stamp"]
        for st in snaps:
            if utc(got) < utc(st) < shot:
                snap = carried(dev, st)
                if newest_value_date(snap) < shot:
                    in_gap.append((dev, r["role"], r["job_id"], r["calibration"]["first_shot"], got, st))
for dev, role, job, shot, got, st in in_gap:
    print(f"  {dev} {role} {job}: first shot {shot}; the history returned {got}; {st} was already stamped and measured")
print(f"  {len(in_gap)} of {len(records)} jobs")
