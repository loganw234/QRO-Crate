"""A re-fetch of IBM's own copy of each result of Quantum-Film's 65 jobs of 2026-10-05, for study QRO-0. It holds
each copy to the raw result Quantum-Film committed. That binds the committed bytes to the provider's copy, as of
this read: the gap study QRO-0 section 12 lists ("Bind the raw bytes beyond git").

It is read-only: nothing is submitted, and no QPU time is used. Logan cleared it on 2026-10-14: "You are clear to
use the IBM key however needed, only requiring permission for real QPU work".

For each job it fetches `GET /jobs/{id}/results`, the text quantum_film's runner wrote verbatim as UTF-8
(runner.py:309-316). It then compares the two in tiers:
  1. bytes: IBM's text, UTF-8, against the committed file's bytes;
  2. JSON: if the bytes differ, the two parsed;
  3. shots: if the JSON differs, every PUB's per-shot bitstrings, in the returned order, through Quantum-Film's own
     reader, quantum_film.ibm.raw.pubs. Also the counts, if the order differs.

It writes digests and verdicts. Where the bytes differ, it also writes IBM's copy beside them as evidence, after
a scan for credential and e-mail patterns. The account is reached only through quantum_film.ibm.account and
keyleak, as in ibm_refetch_v0.py.

Usage: <the qf-ibm venv's python> -I ibm_results_refetch_v0.py --moth <moth-quantum> --out <dir> (--job ID | --all)
"""
if __name__ != "__main__":
    raise ImportError("a tool that reads with the owner's key, not a module")

import argparse
import collections
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
from quantum_film.ibm import account, keyleak, raw  # noqa: E402  (no qiskit imported by these)

refused = keyleak.refusals(os.environ, os.getcwd(), os.path.expanduser("~"), urllib.request.getproxies())
if refused:
    for r in refused:
        print(f"REFUSED: {r}")
    sys.exit(2)
for pkg, want in {"qiskit": "2.5.2", "qiskit-ibm-runtime": "0.50.0"}.items():
    if importlib.metadata.version(pkg) != want:
        sys.exit(f"REFUSED: {pkg} is not {want}; the stack's behaviour was measured on {want}")
from qiskit_ibm_runtime import QiskitRuntimeService  # noqa: E402

FORBIDDEN = re.compile(r"crn:v1|apikey|bearer |authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", re.I)
IBM = MOTH / "docs" / "records" / "2026-10-05" / "ibm"
DEVICES = ("ibm_kingston", "ibm_marrakesh", "ibm_fez")
started = datetime.now(timezone.utc)
written = []


def iso(t):
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def write_new(path, data: bytes):
    if FORBIDDEN.search(data.decode("utf-8", "replace")):
        sys.exit(f"REFUSED: {path.name} would carry a credential or address pattern; nothing written for it")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        sys.exit(f"REFUSED: {path} exists; a fetch never overwrites a record")
    path.write_bytes(data)
    written.append(path)


def write_json(path, obj):
    write_new(path, (json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii"))


def committed():
    for dev in DEVICES:
        for run in [IBM / dev / "run"] + sorted((IBM / dev).glob("sheet-*/run")):
            for role in ("known-answer", "law", "coherence"):
                lp = run / f"{role}-line.json"
                if lp.exists():
                    yield dev, role, json.loads(lp.read_text())["job_id"], run / f"{role}-raw.json"


todo = [t for t in committed() if args.all or t[2] == args.job]
if not todo:
    sys.exit(f"REFUSED: no committed job line names {args.job}")
print(f"results to re-fetch: {len(todo)}")
env = dict(os.environ)
home = Path(os.path.expanduser("~")) / ".quantum-film"
env.setdefault(account.KEY_VARIABLE, str(home / "ibm-apikey.json"))
env.setdefault(account.INSTANCE_VARIABLE, str(home / "ibm.instance"))
service = account.connect(QiskitRuntimeService, env, MOTH)

tally = collections.Counter()
for dev, role, jid, raw_path in todo:
    job = service.job(jid)
    text = job._api_client.job_results(job_id=jid)
    ibm_bytes = text.encode("utf-8")
    ours = raw_path.read_bytes()
    rec = {"format": "qro-crate/ibm-results-refetch/v0", "job_id": jid, "device": dev, "role": role,
           "fetched_at": {"value": iso(datetime.now(timezone.utc)), "clock": "local"},
           "committed": {"path": raw_path.relative_to(MOTH).as_posix(), "bytes": len(ours),
                         "sha256": hashlib.sha256(ours).hexdigest()},
           "ibm_copy": {"bytes": len(ibm_bytes), "sha256": hashlib.sha256(ibm_bytes).hexdigest()},
           "bytes_equal": ibm_bytes == ours}
    if rec["bytes_equal"]:
        tier = "bytes"
    else:
        rec["json_equal"] = json.loads(text) == json.loads(ours.decode("utf-8"))
        if rec["json_equal"]:
            tier = "json"
        else:
            a, b = raw.pubs(text), raw.pubs(ours.decode("utf-8"))
            rec["shots_equal_in_order"] = [x[0] == y[0] for x, y in zip(a, b)] if len(a) == len(b) else False
            rec["counts_equal"] = ([collections.Counter(x[0]) == collections.Counter(y[0]) for x, y in zip(a, b)]
                                   if len(a) == len(b) else False)
            tier = "shots" if rec["shots_equal_in_order"] and all(rec["shots_equal_in_order"]) else "DIFFERS"
        write_new(args.out / dev / f"{jid}-results-ibm-copy.json", ibm_bytes)
        rec["ibm_copy"]["file"] = f"{dev}/{jid}-results-ibm-copy.json"
    rec["agree_at"] = tier
    tally[tier] += 1
    write_json(args.out / dev / f"{jid}.json", rec)
    print(f"{dev} {role:<12} {jid}: agree at {tier} ({len(ibm_bytes)} bytes from IBM, {len(ours)} committed)")

finished = datetime.now(timezone.utc)
write_json(args.out / "MANIFEST.json", {
    "format": "qro-crate/ibm-results-refetch-manifest/v0",
    "approved": "Logan, 2026-10-14: \"You are clear to use the IBM key however needed, only requiring permission "
                "for real QPU work\"",
    "started": {"value": iso(started), "clock": "local"}, "finished": {"value": iso(finished), "clock": "local"},
    "jobs": len(todo), "agree_at": dict(tally),
    "versions": {"python": sys.version.split()[0],
                 **{p: importlib.metadata.version(p) for p in ("qiskit", "qiskit-ibm-runtime", "numpy")}},
    "files": [{"path": p.relative_to(args.out).as_posix(), "bytes": p.stat().st_size,
               "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(written)]})
print(f"agreement: {dict(tally)}; wrote {len(written)} files under {args.out.name}/")
