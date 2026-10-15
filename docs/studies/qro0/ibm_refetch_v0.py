"""A read of IBM's own copies of Quantum-Film's 65 jobs of 2026-10-05, for study QRO-0, question 4. Logan
approved it on 2026-10-14: "go ahead with the key use". It is read-only: no job is submitted and no QPU time
is used.

For each job it fetches, with the owner's key:
  1. the job document with its parameters (job_get, exclude_params=False): IBM's created time, state, backend
     and program, and the submitted PUBs' circuits, shots and options;
  2. its metrics: timestamps, usage, and any calibration id;
  3. the backend's properties nearest before the job's `running` time. qiskit-ibm-runtime 0.50.0's
     RuntimeJobV2.properties() returns exactly this (base_runtime_job.py:199-214): a timestamp match by the
     client against IBM's history, not a calibration IBM names for the job;
  4. the backend's properties nearest before the first shot of the job's execution span. The span is read
     from Quantum-Film's committed raw result, in UTC by IBM's reference.

The key is named by QF_IBM_KEY_FILE and QF_IBM_INSTANCE_FILE, which default to the owner's files under
~/.quantum-film. Those files are outside every repository, and the key is never printed or written.

It holds IBM's copies to Quantum-Film's committed files:
  - the created time, to the job line;
  - each PUB's `qf_commitment`, to the line's commitments;
  - each PUB's circuit, to the bundle's gate list;
  - the options and shots, to the manifest.

Under --out it writes:
  - <device>/<job_id>.json, one per job;
  - <device>/properties-<stamp>.json, one per distinct snapshot;
  - MANIFEST.json: every file's SHA-256 and size, the versions and the times.

It refuses to write anything that matches a credential or e-mail pattern.

The account is reached only through Quantum-Film's own quantum_film.ibm.account and keyleak, from the moth-quantum
tree. Those modules refuse to start under any key-leak condition, and make IAM's raw-key fallback fatal.

Usage: <the qf-ibm venv's python> -I ibm_refetch_v0.py --moth <moth-quantum> --out <dir> (--job ID | --all)
"""
if __name__ != "__main__":
    raise ImportError("a tool that reads with the owner's key, not a module")

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--moth", required=True, type=Path)
ap.add_argument("--out", required=True, type=Path)
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument("--job")
g.add_argument("--all", action="store_true")
args = ap.parse_args()
MOTH = args.moth.resolve()
sys.path.insert(0, str(MOTH))
from quantum_film.ibm import account, isa, keyleak  # noqa: E402  (no qiskit imported by these)

refused = keyleak.refusals(os.environ, os.getcwd(), os.path.expanduser("~"), urllib.request.getproxies())
if refused:
    for r in refused:
        print(f"REFUSED: {r}")
    sys.exit(2)
PINS = {"qiskit": "2.5.2", "qiskit-ibm-runtime": "0.50.0"}
for pkg, want in PINS.items():
    have = importlib.metadata.version(pkg)
    if have != want:
        sys.exit(f"REFUSED: {pkg} is {have}, not {want}; the stack's behaviour was measured on {want}")

from qiskit_ibm_runtime import QiskitRuntimeService  # noqa: E402

FORBIDDEN = re.compile(r"crn:v1|apikey|bearer |authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", re.I)
IBM = MOTH / "docs" / "records" / "2026-10-05" / "ibm"
DEVICES = ("ibm_kingston", "ibm_marrakesh", "ibm_fez")
JOB_KEEP = ("id", "created", "backend", "status", "state", "program")
METRIC_KEEP = ("timestamps", "usage", "qiskit_version", "calibration_id", "num_circuits", "num_qubits",
               "executions", "bss", "estimated_start_time", "estimated_completion_time")
started = datetime.now(timezone.utc)


def utc(s):
    t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return (t if t.tzinfo else t.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def iso(t):
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def plain(v):
    """JSON-ready: datetimes as UTC ISO strings."""
    if isinstance(v, datetime):
        return iso(v if v.tzinfo else v.replace(tzinfo=timezone.utc))
    if isinstance(v, dict):
        return {str(k): plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [plain(x) for x in v]
    return v


written = []


def write(path, obj):
    text = json.dumps(plain(obj), sort_keys=True, indent=1, ensure_ascii=True) + "\n"
    if FORBIDDEN.search(text):
        sys.exit(f"REFUSED: {path.name} would carry a credential or address pattern; nothing written for it")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        sys.exit(f"REFUSED: {path} exists; a fetch never overwrites a record")
    path.write_text(text, encoding="ascii", newline="\n")
    written.append(path)


def jobs_on_disk():
    for dev in DEVICES:
        for run in [IBM / dev / "run"] + sorted((IBM / dev).glob("sheet-*/run")):
            bundle = run.parent / "bundle"
            man = json.loads((bundle / "manifest.json").read_text())
            for role in ("known-answer", "law", "coherence"):
                lp = run / f"{role}-line.json"
                if not lp.exists():
                    continue
                line = json.loads(lp.read_text())
                raw = json.loads((run / f"{role}-raw.json").read_text())
                spans = raw["__value__"]["metadata"]["execution"]["execution_spans"]["__value__"]["spans"]
                first_shot = min(utc(s["__value__"]["start"]["__value__"]) for s in spans)
                mjob = next(j for j in man["jobs"] if j["job"] == role)
                yield {"dev": dev, "role": role, "line": line, "first_shot": first_shot, "bundle": bundle,
                       "manifest": man, "mjob": mjob}


todo = [j for j in jobs_on_disk() if args.all or j["line"]["job_id"] == args.job]
if not todo:
    sys.exit(f"REFUSED: no committed job line names {args.job}")
print(f"jobs to read: {len(todo)}")

env = dict(os.environ)
home = Path(os.path.expanduser("~")) / ".quantum-film"
env.setdefault(account.KEY_VARIABLE, str(home / "ibm-apikey.json"))
env.setdefault(account.INSTANCE_VARIABLE, str(home / "ibm.instance"))
service = account.connect(QiskitRuntimeService, env, MOTH)
backends, snapshots = {}, {}


def snapshot(dev, at):
    """The device's properties nearest before `at` (UTC), saved once per stamp; returns its stamp."""
    be = backends.setdefault(dev, service.backend(dev))
    props = be.properties(datetime=at)
    if props is None:
        return None
    d = props.to_dict()
    stamp = utc(d["last_update_date"])
    key = (dev, iso(stamp))
    if key not in snapshots:
        name = "properties-" + iso(stamp).replace("-", "").replace(":", "").replace(".", "") + ".json"
        write(args.out / dev / name, d)
        snapshots[key] = name
    return {"stamp": iso(stamp), "file": f"{dev}/{snapshots[key]}", "queried_at": iso(at),
            "seconds_before_query": (at - stamp).total_seconds()}


for j in todo:
    line, jid = j["line"], j["line"]["job_id"]
    job = service.job(jid)
    doc = job._api_client.job_get(job_id=jid, exclude_params=False)
    params = doc.get("params", {})          # the client has already decoded it: circuits arrive as QuantumCircuit
    pubs = params.get("pubs", [])
    held = []
    for k, pub in enumerate(pubs):
        circ = pub.circuit if hasattr(pub, "circuit") else pub[0]
        shots = getattr(pub, "shots", None) if hasattr(pub, "circuit") else (pub[2] if len(pub) > 2 else None)
        entry = next(c for c in j["mjob"]["circuits"] if c["pub"] == k)
        frozen = json.loads((j["bundle"] / f"{entry['name']}.gates.json").read_text())
        try:
            copy = isa.gate_list(circ)
            gates_equal, layout_note = copy == frozen, "compared with layout"
        except isa.IsaRefusal as e:
            copy = None
            gates_equal, layout_note = None, f"IsaRefusal: {e}"
        if copy is not None and not gates_equal:
            gates_only = copy["gates"] == frozen["gates"]
        else:
            gates_only = gates_equal
        held.append({"pub": k, "name": entry["name"],
                     "commitment_in_ibm_copy": (circ.metadata or {}).get("qf_commitment"),
                     "commitment_in_line": line["commitments"][k] if k < len(line["commitments"]) else None,
                     "gate_list_equal": gates_equal, "gates_equal": gates_only, "gate_list_note": layout_note,
                     "shots_in_ibm_copy": shots, "shots_in_manifest": entry["shots"]})
    sent = params.get("options", {})
    frozen_opts = j["manifest"]["options"]
    options_equal = all(sent.get(a, {}).get(b) == frozen_opts.get(a, {}).get(b) for a, b in
                        (("dynamical_decoupling", "enable"), ("twirling", "enable_gates"),
                         ("twirling", "enable_measure")))
    metrics = job.metrics()
    running = utc(metrics["timestamps"]["running"])
    created = utc(doc["created"])
    rec = {
        "format": "qro-crate/ibm-refetch/v0",
        "job_id": jid, "device": j["dev"], "role": j["role"],
        "fetched_at": {"value": iso(datetime.now(timezone.utc)), "clock": "local"},
        "ibm_job": {k: doc.get(k) for k in JOB_KEEP if k in doc},
        "ibm_job_omitted_keys": sorted(k for k in doc if k not in JOB_KEEP and k != "params"),
        "ibm_params_keys": sorted(params),
        "ibm_options": sent,
        "ibm_metrics": {k: metrics.get(k) for k in METRIC_KEEP if k in metrics},
        "ibm_metrics_omitted_keys": sorted(k for k in metrics if k not in METRIC_KEEP),
        "holds": {
            "created_equal_to_line": created == utc(line["submitted_at"]),
            "created_ibm": iso(created), "submitted_at_line": line["submitted_at"],
            "pubs_in_ibm_copy": len(pubs), "pubs_in_line": len(line["commitments"]),
            "pubs": held,
            "commitments_equal": [h["commitment_in_ibm_copy"] for h in held] == list(line["commitments"]),
            "options_equal_to_manifest": options_equal,
        },
        "calibration": {
            "before_running": snapshot(j["dev"], running),
            "before_first_shot": snapshot(j["dev"], j["first_shot"]),
            "running": iso(running), "first_shot": iso(j["first_shot"]),
            "freeze_stamp_in_manifest": j["manifest"]["target"]["calibration"],
        },
    }
    write(args.out / j["dev"] / f"{jid}.json", rec)
    h = rec["holds"]
    print(f"{j['dev']} {j['role']:<12} {jid}: created {'=' if h['created_equal_to_line'] else '!='} line; "
          f"commitments {'equal' if h['commitments_equal'] else 'DIFFER'} ({len(held)} PUB); "
          f"gate lists {[p['gate_list_equal'] for p in held]}; options {'equal' if options_equal else 'DIFFER'}; "
          f"calibration before running {rec['calibration']['before_running']['stamp'] if rec['calibration']['before_running'] else None}, "
          f"before first shot {rec['calibration']['before_first_shot']['stamp'] if rec['calibration']['before_first_shot'] else None}")

finished = datetime.now(timezone.utc)
files = [{"path": p.relative_to(args.out).as_posix(), "bytes": p.stat().st_size,
          "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(written)]
write(args.out / "MANIFEST.json", {
    "format": "qro-crate/ibm-refetch-manifest/v0", "approved": "Logan, 2026-10-14: \"go ahead with the key use\"",
    "started": {"value": iso(started), "clock": "local"}, "finished": {"value": iso(finished), "clock": "local"},
    "jobs": len(todo), "selection": "all" if args.all else args.job,
    "versions": {"python": sys.version.split()[0], **{p: importlib.metadata.version(p) for p in
                                                      ("qiskit", "qiskit-ibm-runtime", "numpy")}},
    "moth_quantum_commit_files_read": "docs/records/2026-10-05/ibm (lines, raw spans, manifests, gate lists)",
    "files": files})
print(f"wrote {len(written)} files under {args.out.name}/")
