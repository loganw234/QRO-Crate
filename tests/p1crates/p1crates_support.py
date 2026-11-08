"""Support for the p1-crates stage (P1.2): moth-quantum's checkout named by QRO_MOTH_ROOT (the runner skips the stage by
name without it, and this module fails to import without it, so a run by hand without it is an error and not a pass),
and the two real crates, each built once in a process by the adapter as a process, outside the tree, and checked once by
the command line as a process. Nothing of Moth's or IBM's enters the tree: the crates live in the system's temporary
files and are removed when the process ends.

It names no function `test*` and no class `Test*`. The sweeps at the end are the twin's (tests/p1/test_p1_sweeps.py) over the
real crates' entities; they are copied and not imported, since Miniconda has a `tests` package of its own."""
import atexit
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from qro import canonical, p1_forms, p1_steps, reader, spelling
from qro.p1_graph import Index
from qro.refusal import Refused

MOTH = Path(os.environ["QRO_MOTH_ROOT"])
ROOT = Path(__file__).resolve().parents[2]
_BUILT = {}                       # kind -> (the crate's directory, its identity as the adapter printed it, the build's seconds)
_REAL_PARSE, _REAL_CLAIMS, _REAL_LOAD = p1_forms.parse_snapshot, None, p1_forms.load_json


def process(argv, module="qro.p1_adapter"):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-m", module, *argv], capture_output=True, text=True, env=env, cwd=ROOT)


def built(kind):
    """The real crate of this kind: built by `python -m qro.p1_adapter` from moth-quantum into a new directory in the system's
    temporary files, once. (The directory, the identity the adapter printed, the line it printed.)"""
    if kind not in _BUILT:
        d = Path(tempfile.mkdtemp(prefix=f"p1-real-{kind}-"))
        atexit.register(shutil.rmtree, str(d), True)
        out = d / "crate"
        done = process([kind, "--moth", str(MOTH), "--out", str(out)])
        assert (done.returncode, done.stderr) == (0, ""), (done.returncode, done.stdout[-300:], done.stderr[-300:])
        words = done.stdout.split()
        _BUILT[kind] = (out, words[-1], done.stdout.strip())
    return _BUILT[kind]


_CHECKED = {}


def checked(kind):
    """The command line's verdict on the real crate, once: (exit code, stdout, stderr)."""
    if kind not in _CHECKED:
        crate = built(kind)[0]
        run = process(["check", str(crate)], module="qro")
        _CHECKED[kind] = (run.returncode, run.stdout.strip(), run.stderr.strip())
    return _CHECKED[kind]


def metadata(kind):
    return reader.read((built(kind)[0] / canonical.DESCRIPTOR).read_bytes())


def digests(crate):
    """{path: SHA-256} of every file of a crate."""
    return {p.relative_to(crate).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(Path(crate).rglob("*")) if p.is_file()}


def read(crate, rel):
    return Path(crate).joinpath(*rel.split("/")).read_bytes()


def types_of(e):
    return canonical.types(e)


def of_type(md, t):
    return sorted((e for e in md["@graph"] if t in types_of(e)), key=lambda e: e["@id"])


def memo_parses(monkeypatch):
    """What is parsed from identical bytes is parsed once in the process: the snapshots and the JSON the readers load. The
    controls check the real crate again and again, each time with one record altered."""
    parsed, loaded, claimed = {}, {}, {}
    from qro import p1_calibration
    real_claims = p1_calibration.claims

    def parse(data):
        if data not in parsed:
            parsed[data] = _REAL_PARSE(data)
        return parsed[data]

    def claims(snapshot):
        if id(snapshot) not in claimed:
            claimed[id(snapshot)] = (snapshot, real_claims(snapshot))
        return claimed[id(snapshot)][1]

    def load_json(data, what, error=p1_forms.RawFormError):
        if (data, error) not in loaded:
            loaded[(data, error)] = _REAL_LOAD(data, what, error)
        return loaded[(data, error)]
    monkeypatch.setattr(p1_forms, "parse_snapshot", parse)
    monkeypatch.setattr(p1_calibration, "claims", claims)
    monkeypatch.setattr(p1_forms, "load_json", load_json)


# -- the sweeps, per entity (copied from tests/p1/test_p1_sweeps.py) --------------------------------------------------------------------
def other_digest(d):
    return ("0" if d[0] != "0" else "1") + d[1:]


MIRROR = {"msb-first": "lsb-first", "atlas-register": "circuit-order"}


def sweep_pubs(crate, md):
    idx, facts, lines, listings = Index(md), {}, {}, {}
    pubs = sorted(idx.of_type("qro:Pub"), key=lambda e: e["@id"])
    for pub in pubs:
        p1_steps._pub4(crate, idx, facts, lines, listings, pub)
        flipped = dict(pub, **{"qro:commitment": other_digest(pub["qro:commitment"])}) if pub["qro:commitment"] != "none" \
            else dict(pub, **{"qro:commitment": "0" * 64})
        if pub["qro:commitment"] == "none":
            continue                                  # the provider held none: nothing for step 4 to hold it to
        with pytest.raises(Refused) as x:
            p1_steps._pub4(crate, idx, facts, lines, listings, flipped)
        assert (x.value.name, x.value.where) == ("commitment", f"{pub['@id']} qro:commitment"), pub["@id"]
    return len(pubs)


def sweep_decodes(crate, md):
    idx, verdicts = Index(md), {}
    decodes = sorted(idx.of_type("qro:Decode"), key=lambda e: e["@id"])
    law_pub = next(p["@id"] for p in idx.of_type("qro:Pub") if p.get("qro:role") != "known-answer")
    for d in decodes:
        p1_steps._decode5(crate, idx, verdicts, d)
        mirrored = dict(d, **{"qro:bitOrder": MIRROR[d["qro:bitOrder"]]})
        with pytest.raises(Refused) as x:
            p1_steps._decode5(crate, idx, verdicts, mirrored)
        assert x.value.name == "known-answer" and x.value.where.startswith(d["@id"] + " "), d["@id"]
        elsewhere = dict(d, **{"qro:knownAnswer": {"@id": law_pub}})
        with pytest.raises(Refused) as x:
            p1_steps._decode5(crate, idx, verdicts, elsewhere)
        assert (x.value.name, x.value.where) == ("known-answer", f"{d['@id']} qro:knownAnswer"), d["@id"]
    return len(decodes)


def sweep_snapshots_and_jobs(crate, md):
    from datetime import timedelta
    idx, snaps, by_name = Index(md), {}, {}
    snapshots = sorted(idx.of_type("qro:Snapshot"), key=lambda e: e["@id"])
    for e in snapshots:
        p1_steps._snapshot8(crate, idx, snaps, by_name, e)
        wrong = dict(e, **{"qro:valuesDigest": other_digest(e["qro:valuesDigest"])})
        with pytest.raises(Refused) as x:
            p1_steps._snapshot8(crate, idx, {}, {}, wrong)
        assert (x.value.name, x.value.where) == ("calibration-link", f"{e['@id']} qro:valuesDigest"), e["@id"]
    jobs = sorted(idx.of_type("qro:Job"), key=lambda e: e["@id"])
    words = {"history-at-first-shot": "history-in-gap", "history-in-gap": "history-at-first-shot", "unexposed": "history-at-first-shot",
             "unknown": "history-at-first-shot"}
    for job in jobs:
        p1_steps._job8(crate, idx, snaps, by_name, job)
        wrong = dict(job, **{"qro:calibrationLink": words[job["qro:calibrationLink"]]})
        with pytest.raises(Refused) as x:
            p1_steps._job8(crate, idx, snaps, by_name, wrong)
        assert x.value.name == "calibration-link" and x.value.where.startswith(job["@id"] + " "), job["@id"]
        if job["startTime"] != "unknown":
            later = dict(job, startTime=spelling.time(p1_forms.parse_time(job["startTime"], "Z") + timedelta(microseconds=1)))
            with pytest.raises(Refused) as x:
                p1_steps._job8(crate, idx, snaps, by_name, later)
            assert (x.value.name, x.value.where) == ("calibration-link", f"{job['@id']} startTime")
    return len(snapshots), len(jobs)


def visited(monkeypatch, names):
    seen = {n: [] for n in names}
    for n in names:
        real = getattr(p1_steps, n)

        def wrapper(*args, _real=real, _n=n):
            seen[_n].append(args[-1]["@id"])
            return _real(*args)
        monkeypatch.setattr(p1_steps, n, wrapper)
    return seen
