"""Support for the p3-crates stage (P3.1): moth-quantum's checkout named by QRO_MOTH_ROOT (the runner skips the stage by
name without it, and this module fails to import without it, so a run by hand without it is an error and not a pass);
v0's two crates, each built once in a process by P1's adapter as a process, outside the tree, and checked once in the
process by the checker's nine steps; and v0's comparisons, each computed by qro.p3_compare.compute on those and written
by its writer, which checks the comparison crate by the nine steps, then held by the command as a process or by the
check in process, its crates' nine steps then answered from the one check of each (`fast_checks`). Nothing of Moth's or
IBM's enters the tree: the crates and the comparisons live in the system's temporary files, and are removed when the
process ends, each directory by the process that made it (the lead's ruling at P3's approval: v0's comparison crates
are built in tests only, never committed). Nothing here prints or keeps an IBM job id.

It names no function `test*` and no class `Test*`. It copies `process` and the build from tests/p2crates/
p2crates_support.py rather than import them: Miniconda has a `tests` package of its own."""
import atexit
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from qro import canonical, checker, p3_compare, p3_declaration

MOTH = Path(os.environ["QRO_MOTH_ROOT"])
ROOT = Path(__file__).resolve().parents[2]
FIVE = ("forbidden-share", "linear-xeb", "n-crystal-share", "x0x1", "y0y1")
_BUILT, _CHECKED, _MADE = {}, {}, {}


def process(argv, module="qro.p1_adapter"):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-m", module, *argv], capture_output=True, text=True, env=env, cwd=ROOT)


def temporary(prefix):
    d = Path(tempfile.mkdtemp(prefix=prefix))
    atexit.register(shutil.rmtree, str(d), True)
    return d


def built(kind):
    """v0's crate of this kind, built by `python -m qro.p1_adapter` from moth-quantum into a new directory of the
    system's temporary files, once: its directory."""
    if kind not in _BUILT:
        out = temporary(f"p3-real-{kind}-") / "crate"
        done = process([kind, "--moth", str(MOTH), "--out", str(out)])
        assert (done.returncode, done.stderr) == (0, ""), (done.returncode, done.stdout[-300:], done.stderr[-300:])
        _BUILT[kind] = out
    return _BUILT[kind]


def checked(kind):
    """(the crate's directory, its metadata, its body digest): the nine steps run on it once in the process."""
    if kind not in _CHECKED:
        checker.load()
        md = checker.check(built(kind))
        _CHECKED[kind] = (built(kind), md, canonical.body_digest(md))
    return _CHECKED[kind]


def fast_checks(monkeypatch):
    """The nine steps of each of v0's crates answered from its one check in this process, by its directory; every other
    directory checked afresh."""
    real = checker.check

    def check(crate_dir):
        for kind in ("ibm", "atlas"):
            if kind in _CHECKED and os.path.samefile(crate_dir, _CHECKED[kind][0]):
                return _CHECKED[kind][1]
        return real(crate_dir)
    monkeypatch.setattr(checker, "check", check)


def comparison(a, b, kind_a="ibm", kind_b="ibm", measures=FIVE, epsilon="0/1", kind="real", question="fixed"):
    """v0's comparison of selector `a` of crate `kind_a` against `b` of `kind_b`, once: (its directory, its record),
    or the Refused that its computation raised."""
    key = (repr(a), repr(b), kind_a, kind_b, measures, epsilon, kind, question)
    if key not in _MADE:
        crates = {}
        for k in {kind_a, kind_b}:
            d, md, digest = checked(k)
            crates[digest] = (d, md)
        plan = p3_declaration.plan({m: epsilon for m in measures}, {"a": a, "b": b}, kind=kind, question=question)
        data = p3_declaration.write({"a": [checked(kind_a)[2]], "b": [checked(kind_b)[2]]}, plan)
        declaration = p3_declaration.read(data)
        try:
            record, _ = p3_compare.compute(declaration, None, crates)
        except Exception as x:          # a Refused, kept as the answer; anything else fails the test that asked
            _MADE[key] = x
        else:
            out = temporary("p3-v0-comparison-") / "comparison"
            p3_compare.write_comparison(out, declaration, data, record)
            _MADE[key] = (out, record)
    if isinstance(_MADE[key], Exception):
        raise _MADE[key]
    return _MADE[key]


def device(name):
    return {"device": name}


def measure(record, name):
    return next(m for m in record["measures"] if m["measure"] == name)


def four(x):
    """A rational as the study prints it: signed, at four places."""
    from fractions import Fraction
    return f"{float(Fraction(x)):+.4f}"


JOB_ID = re.compile(r"\b[a-z0-9]{20}\b|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")


def mask(text):
    """An IBM job id, 20 letters and digits, and a Moth job id, a UUID, masked."""
    return JOB_ID.sub("<job id>", text)
