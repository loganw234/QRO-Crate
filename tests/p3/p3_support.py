"""Helpers for P3's tests (P3.1). It names no function `test*` and no class `Test*`.

  - `crates_of(*dirs)`: {body digest: (directory, metadata)} of crates read by the strict reader, for the computation fed
    directly (the builder's crates name a generator no parcel registers, so the checker stops at their step 9);
  - `declare(...)`: a declaration's bytes and its Declaration, from the pool and a plan of what this version builds;
  - `computed(...)`: qro.p3_compare.compute on them;
  - `fast_checks(monkeypatch)`: the checker's nine steps memoised by the bytes of every file of the crate, so that the
    tests that check one twin many times check it once in the process. It keeps an acceptance and never a refusal, and a
    crate whose files change is another key;
  - `process(argv, module)`: a command of the tree run as a process, as a user runs it;
  - `mask(text)`: an IBM job id, 20 letters and digits, masked in what a test prints.
"""
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

from qro import canonical, checker, p3_compare, p3_declaration, reader

ROOT = Path(__file__).resolve().parents[2]
FIVE = ("forbidden-share", "linear-xeb", "n-crystal-share", "x0x1", "y0y1")
LAW_MEASURES = ("forbidden-share", "linear-xeb", "n-crystal-share")
COHERENCES = ("x0x1", "y0y1")


def md_of(crate):
    return reader.read((Path(crate) / canonical.DESCRIPTOR).read_bytes())


def digest_of(crate):
    return canonical.body_digest(md_of(crate))


def crates_of(*dirs):
    out = {}
    for d in dirs:
        md = md_of(d)
        out[canonical.body_digest(md)] = (Path(d), md)
    return out


def declare(a, b, measures=FIVE, epsilon="0/1", runs=None, kind="real", question="fixed", alpha="1/20",
            granularity="job", preregistration="none", device_a="ibm_kingston", device_b="ibm_fez"):
    """(bytes, Declaration) of crate `a` against crate `b` (directories), over `measures` ({measure: epsilon} or names
    at `epsilon`), the runs' selectors `runs` (default: each its device)."""
    if not isinstance(measures, dict):
        measures = {m: epsilon for m in measures}
    runs = runs or {"a": {"device": device_a}, "b": {"device": device_b}}
    plan = p3_declaration.plan(measures, runs, kind=kind, question=question, alpha=alpha, granularity=granularity)
    data = p3_declaration.write({"a": [digest_of(a)], "b": [digest_of(b)]}, plan, preregistration)
    return data, p3_declaration.read(data)


def computed(a, b, preregistration=None, **kw):
    """(the record, the facts) of crate `a` against crate `b`, computed directly."""
    _, decl = declare(a, b, **kw)
    return p3_compare.compute(decl, preregistration, crates_of(*{Path(a), Path(b)}))


def measure(record, name):
    return next(m for m in record["measures"] if m["measure"] == name)


def tree_digest(crate):
    """The SHA-256 over every file of a crate, its path and its bytes, in path order."""
    h = hashlib.sha256()
    crate = Path(crate)
    for p in sorted(crate.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(crate).as_posix().encode("utf-8") + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


_ACCEPTED = {}


def fast_checks(monkeypatch):
    real = checker.check

    def check(crate_dir):
        key = tree_digest(crate_dir)
        if key not in _ACCEPTED:
            _ACCEPTED[key] = real(crate_dir)
        return _ACCEPTED[key]
    monkeypatch.setattr(checker, "check", check)


def own_metadata(crate):
    """A stand-in step 9 for the builder's crates, which no parcel's generator makes: the crate's own metadata, so
    that the checker's steps 1 to 8 hold them and step 9 holds nothing. Registered only inside a test."""
    import json
    return json.loads((Path(crate) / canonical.DESCRIPTOR).read_bytes())


def builder_generator(monkeypatch):
    import p3_builder
    monkeypatch.setitem(checker.GENERATORS, p3_builder.GENERATOR, own_metadata)


def process(argv, module="qro", stdin=None):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-m", module, *argv], capture_output=True, text=True, env=env, cwd=ROOT,
                          stdin=stdin)


JOB_ID = re.compile(r"\b[a-z0-9]{20}\b")


def mask(text):
    return JOB_ID.sub("<job id>", text)
