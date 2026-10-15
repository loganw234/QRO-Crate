"""IBM dry runs of the free-tier unit's job shapes, for study QRO-0 (sections 9.1 and 13). Logan, 2026-10-14:
"Dry runs are safe and clear to run anytime, only the real QPU runs are a hold point".

qiskit-ibm-runtime 0.50.0's dry run "performs a dry run without executing the job on a QPU" and returns
"randomized mock data" (base_primitive.py:127-142). Before anything is submitted, the service renames the backend
to its mock counterpart, "ibm_kingston" to "mock_kingston", and refuses if no such backend resolves
(qiskit_runtime_service.py:1102-1111). This tool adds two guards of its own:
  - it submits only when every device's mock backend resolves by name, through the runtime's own lookup;
  - it cancels and refuses at once if IBM records any submission on a backend whose name does not start "mock_".

  --probe   read-only: the instance's plan, its usage as IBM reports it, which mock backends it lists, and
            whether each device's mock backend resolves by name. The listing may omit backends, so the
            runtime falls back to one configuration request by name (qiskit_runtime_service.py:1004-1029).
  --submit  the probe, then dry runs on each device's mock backend, then the usage again. It uses v0's frozen
            circuits (moth-quantum, docs/records/2026-10-05/ibm/<device>/bundle/*.qpy), each held to its
            manifest's isa_sha256:
              v0-known-answer  1 PUB  x  1,024 shots   v0 was charged 2 s for this shape
              v0-law           1 PUB  x 24,576 shots   9 s
              v0-coherence     2 PUBs x  4,096 shots   4 s
              unit-control     2 PUBs x  2,048 shots   the known answer twice, standing in for it and its complement
              unit-film        3 PUBs x 16,384 shots   the law and both coherence bases
            with v0's options as sent. For each job it keeps IBM's job document (whitelisted, the backend name
            included), its usage estimation, its metrics (whitelisted) and the result's execution metadata. The
            results' counts are mock data, so none are kept.

The key is named by QF_IBM_KEY_FILE and QF_IBM_INSTANCE_FILE, which default to the owner's files under
~/.quantum-film, outside every repository. The key and the instance are never printed or written. The account is
reached only through Quantum-Film's own account and keyleak modules, as ibm_refetch_v0.py does.

Under --out it writes probe.json (and, with --submit, one file per job, usage-after.json and MANIFEST.json),
refusing any file that would carry a credential or address pattern, and never overwriting.

Usage: <the qf-ibm venv's python> -I ibm_dryrun_v0.py --moth <moth-quantum> --out <dir> (--probe | --submit)
"""
if __name__ != "__main__":
    raise ImportError("a tool that uses the owner's key, not a module")

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
g.add_argument("--probe", action="store_true")
g.add_argument("--submit", action="store_true")
args = ap.parse_args()
MOTH = args.moth.resolve()
sys.path.insert(0, str(MOTH))
from quantum_film.ibm import account, keyleak  # noqa: E402  (no qiskit imported by these)

refused = keyleak.refusals(os.environ, os.getcwd(), os.path.expanduser("~"), urllib.request.getproxies())
if refused:
    for r in refused:
        print(f"REFUSED: {r}")
    sys.exit(2)
PINS = {"qiskit": "2.5.2", "qiskit-ibm-runtime": "0.50.0"}
for pkg, want in PINS.items():
    have = importlib.metadata.version(pkg)
    if have != want:
        sys.exit(f"REFUSED: {pkg} is {have}, not {want}; the dry run's routing was read in {want}")

from qiskit import qpy  # noqa: E402
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2  # noqa: E402

FORBIDDEN = re.compile(r"crn:v1|crn%3av1|apikey|bearer |authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}",
                       re.I)
IBM = MOTH / "docs" / "records" / "2026-10-05" / "ibm"
DEVICES = ("ibm_kingston", "ibm_marrakesh", "ibm_fez")
JOB_KEEP = ("id", "created", "backend", "status", "state", "program", "estimated_running_time_seconds",
            "estimated_start_time", "estimated_completion_time")
METRIC_KEEP = ("timestamps", "usage", "qiskit_version", "calibration_id", "num_circuits", "num_qubits",
               "executions", "bss", "estimated_start_time", "estimated_completion_time")
SHAPES = (("v0-known-answer", (("known-answer", 1024),)),
          ("v0-law", (("law", 24576),)),
          ("v0-coherence", (("coherence-xx", 4096), ("coherence-yy", 4096))),
          ("unit-control", (("known-answer", 2048), ("known-answer", 2048))),
          ("unit-film", (("law", 16384), ("coherence-xx", 16384), ("coherence-yy", 16384))))
started = datetime.now(timezone.utc)


def iso(t):
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def plain(v):
    if isinstance(v, datetime):
        return iso(v if v.tzinfo else v.replace(tzinfo=timezone.utc))
    if isinstance(v, dict):
        return {str(k): plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [plain(x) for x in v]
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)


written = []


def write(path, obj):
    text = json.dumps(plain(obj), sort_keys=True, indent=1, ensure_ascii=True) + "\n"
    if FORBIDDEN.search(text):
        sys.exit(f"REFUSED: {path.name} would carry a credential or address pattern; nothing written for it")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        sys.exit(f"REFUSED: {path} exists; a record is never overwritten")
    path.write_text(text, encoding="ascii", newline="\n")
    written.append(path)


def usage_of(service):
    """IBM's usage for the instance: the usage_* numbers and flags, the usage period if it holds only dates or
    numbers, and the names of any other keys (their values, identifiers among them, are not kept)."""
    u = service.usage()
    kept = {k: v for k, v in u.items() if k.startswith("usage_") and isinstance(v, (int, float, bool))}
    period = u.get("usage_period")
    if isinstance(period, dict) and all(isinstance(v, (str, int, float)) or v is None for v in period.values()):
        kept["usage_period"] = period
    return {"kept": kept, "other_keys": sorted(k for k in u if k not in kept)}


env = dict(os.environ)
home = Path(os.path.expanduser("~")) / ".quantum-film"
env.setdefault(account.KEY_VARIABLE, str(home / "ibm-apikey.json"))
env.setdefault(account.INSTANCE_VARIABLE, str(home / "ibm.instance"))
service = account.connect(QiskitRuntimeService, env, MOTH)

plan, pricing = account.plan_of(service)
names = sorted(b.name for b in service.backends())
mocks = [n for n in names if n.startswith("mock_")]
usage_before = usage_of(service)


def by_name(name):
    """The runtime's own lookup, which the dry run uses: the listing first, then one uncached configuration
    request by name (qiskit_runtime_service.py:1004-1029; a GET). The instance is passed, so the runtime has
    no instance to guess and log. Only the exception's class is kept, never its message."""
    try:
        be = service.backend(name=name, instance=service.active_instance())
        return {"resolved": True, "name": be.name}
    except Exception as ex:
        return {"resolved": False, "error_class": type(ex).__name__}


lookups = {d: by_name("mock_" + d.split("_", 1)[1]) for d in DEVICES}
probe = {"format": "qro-crate/ibm-dryrun-probe/v1", "at": {"clock": "local", "value": iso(started)},
         "plan": plan, "pricing_type": pricing, "backends": names, "mock_backends": mocks,
         "mock_for": {d: ("mock_" + d.split("_", 1)[1]) in mocks for d in DEVICES},
         "mock_by_name": lookups, "usage": usage_before}
write(args.out / "probe.json", probe)
print(f"plan {plan} ({pricing}); {len(names)} backends listed; mock backends listed: {mocks or 'none'}")
print(f"mock backends by name: {lookups}")
print(f"usage before: {usage_before['kept']}")
if args.probe:
    sys.exit(0)

missing = [d for d in DEVICES if not lookups[d]["resolved"] or not lookups[d]["name"].startswith("mock_")]
if missing:
    sys.exit(f"REFUSED: no mock backend resolves by name for {missing}; no dry run is submitted")

records = []
for dev in DEVICES:
    man = json.loads((IBM / dev / "bundle" / "manifest.json").read_text())
    circuit_entry = {c["name"]: c for j in man["jobs"] for c in j["circuits"]}
    circuits = {}
    for name in ("known-answer", "law", "coherence-xx", "coherence-yy"):
        path = IBM / dev / "bundle" / f"{name}.qpy"
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != circuit_entry[name]["isa_sha256"]:
            sys.exit(f"REFUSED: {dev}/{name}.qpy does not hash as its manifest records")
        with open(path, "rb") as fh:
            circuits[name] = qpy.load(fh)[0]
    backend = service.backend(dev)
    for shape, pubs in SHAPES:
        sampler = SamplerV2(mode=backend, options=man["options"])
        rec = {"device": dev, "shape": shape, "pubs": [{"circuit": n, "shots": s} for n, s in pubs],
               "submitted_at": {"clock": "local", "value": iso(datetime.now(timezone.utc))}}
        try:
            job = sampler.run([(circuits[n], None, s) for n, s in pubs], dry_run=True)
        except Exception as ex:            # access may be restricted: record the refusal, submit nothing more
            rec["error"] = f"{type(ex).__name__}: {ex}"
            write(args.out / dev / f"{shape}.json", rec)
            print(f"{dev} {shape}: refused by the service: {rec['error'][:200]}")
            sys.exit(1)
        jid = job.job_id()
        doc = job._api_client.job_get(job_id=jid)
        on = doc.get("backend")
        if not str(on).startswith("mock_"):
            job.cancel()
            sys.exit(f"REFUSED: IBM records job {jid} on {on}, not a mock backend; it was cancelled at once")
        rec["job_id"] = jid
        job.wait_for_final_state(timeout=1800)
        doc = job._api_client.job_get(job_id=jid)
        rec["ibm_job"] = {k: doc[k] for k in JOB_KEEP if k in doc}
        rec["usage_estimation"] = job.usage_estimation
        metrics = job.metrics()
        rec["ibm_metrics"] = {k: metrics[k] for k in METRIC_KEEP if k in metrics}
        rec["status"] = str(job.status())
        try:
            result = job.result()
            rec["result_metadata"] = dict(result.metadata)
            rec["pub_metadata_keys"] = [sorted(getattr(p, "metadata", {}) or {}) for p in result]
        except Exception as ex:
            rec["result_error"] = f"{type(ex).__name__}: {ex}"
        write(args.out / dev / f"{shape}.json", rec)
        records.append(rec)
        u = rec["ibm_metrics"].get("usage", {})
        print(f"{dev} {shape}: job {jid} on {on}, {rec['status']}; estimated {rec['usage_estimation']}; "
              f"metrics usage {u}")

usage_after = usage_of(service)
write(args.out / "usage-after.json", {"at": {"clock": "local", "value": iso(datetime.now(timezone.utc))},
                                      "usage": usage_after})
print(f"usage after: {usage_after['kept']}")
manifest = {"format": "qro-crate/ibm-dryrun-manifest/v0", "started": {"clock": "local", "value": iso(started)},
            "finished": {"clock": "local", "value": iso(datetime.now(timezone.utc))},
            "versions": {p: importlib.metadata.version(p) for p in ("qiskit", "qiskit-ibm-runtime")},
            "moth_quantum_files_read": "docs/records/2026-10-05/ibm/<device>/bundle (manifest.json, *.qpy)",
            "files": [{"path": p.relative_to(args.out).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                       "bytes": p.stat().st_size} for p in written]}
write(args.out / "MANIFEST.json", manifest)
print(f"wrote {len(written)} files")
