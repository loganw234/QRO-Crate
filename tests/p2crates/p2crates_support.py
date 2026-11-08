"""Support for the p2-crates stage (P2.2): moth-quantum's checkout named by QRO_MOTH_ROOT (the runner skips the stage by
name without it, and this module fails to import without it, so a run by hand without it is an error and not a pass);
v0's two crates, each built once in a process by P1's adapter as a process, outside the tree, and checked once by the
command line as a process; and Quantum-Film's printed figures, read at run time from its page in moth-quantum,
moth-quantum's docs/HARDWARE-RESULTS.md, never copied into the tree. Nothing of Moth's or IBM's enters the tree: the
crates live in the system's temporary files and are removed when the process ends, each directory by the process that
made it.
Nothing here prints or keeps an IBM job id: a run is named by its device and its bundle (`ibm_kingston/morning`,
`ibm_fez/sheet-03`).

It names no function `test*` and no class `Test*`. It copies two functions of tests/p1crates/p1crates_support.py,
`process` and the build, rather than import them: Miniconda has a `tests` package of its own."""
import atexit
import os
import re
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

from qro import canonical, p1_decode, p2_law, p2_measures, reader
from qro.p1_graph import Index

MOTH = Path(os.environ["QRO_MOTH_ROOT"])
ROOT = Path(__file__).resolve().parents[2]
RESULTS = MOTH / "docs" / "HARDWARE-RESULTS.md"
DEVICES = ("ibm_kingston", "ibm_marrakesh", "ibm_fez")
_BUILT, _CHECKED = {}, {}


def process(argv, module="qro.p1_adapter"):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-m", module, *argv], capture_output=True, text=True, env=env, cwd=ROOT)


def built(kind):
    """v0's crate of this kind, built by `python -m qro.p1_adapter` from moth-quantum into a new directory of the
    system's temporary files, once: (its directory, the identity the adapter printed, the line it printed)."""
    if kind not in _BUILT:
        d = Path(tempfile.mkdtemp(prefix=f"p2-real-{kind}-"))
        atexit.register(shutil.rmtree, str(d), True)
        out = d / "crate"
        done = process([kind, "--moth", str(MOTH), "--out", str(out)])
        assert (done.returncode, done.stderr) == (0, ""), (done.returncode, done.stdout[-300:], done.stderr[-300:])
        _BUILT[kind] = (out, done.stdout.split()[-1], done.stdout.strip())
    return _BUILT[kind]


def checked(kind):
    """The command line's verdict on the crate, once: (exit code, stdout, stderr)."""
    if kind not in _CHECKED:
        run = process(["check", str(built(kind)[0])], module="qro")
        _CHECKED[kind] = (run.returncode, run.stdout.strip(), run.stderr.strip())
    return _CHECKED[kind]


def metadata(kind):
    return reader.read((built(kind)[0] / canonical.DESCRIPTOR).read_bytes())


def law():
    return p2_law.read(p2_law.law_bytes())


# -- the runs of the IBM crate, by device and bundle ------------------------------------------------------------------------
def run_of(job):
    """A Job's run, `<device>/<bundle>`, from its line's path: `morning` for the device's first bundle."""
    m = re.fullmatch(r"2026-10-05/ibm/(ibm_[a-z]+)/(?:(sheet-[0-9]+)/)?run/[a-z-]+-line\.json", job["qro:line"]["@id"])
    assert m, "a job line of v0's IBM records"
    return f"{m.group(1)}/{m.group(2) or 'morning'}"


def pubs(md):
    """{(run, role, measure word or basis): the Pub}: every law and coherence Pub of the IBM crate, by its run."""
    idx = Index(md)
    out = {}
    for job in idx.of_type("qro:Job"):
        for pub in idx.refs_of_type(job, "object", "qro:Pub"):
            if pub["qro:role"] == "law":
                out[(run_of(job), "law")] = pub
            elif pub["qro:role"] == "coherence":
                out[(run_of(job), "x0x1" if pub["qro:basis"].startswith("XX") else "y0y1")] = pub
    return out


def runs_by_job_id(md):
    """{an IBM job id: its run}: for reading a table that names jobs, which nothing here prints or keeps."""
    return {job["qro:jobId"]: run_of(job) for job in Index(md).of_type("qro:Job")}


def counts(crate, md, pub):
    """The Pub's decoded counts, {the sorted tuple of qubits read 1: shots}, from the raw bytes (P1.1's pub_counts)."""
    return p1_decode.pub_counts(crate, md, pub["@id"])


def five(c, law_):
    return {Y: n for Y, n in c.items() if len(Y) == law_.N}


def values(crate, md, pub, law_):
    return p2_measures.pub_values(crate, md, pub, law_)


# -- Quantum-Film's printed figures, read from its page ----------------------------------------------------------------------
def _cells(line):
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)[1:-1]]


def table(heading, text=None):
    """The first Markdown table under a heading of HARDWARE-RESULTS.md: [header cells, row cells...]."""
    text = RESULTS.read_text(encoding="utf-8") if text is None else text
    lines = text.splitlines()
    start = lines.index(heading)
    out = []
    for line in lines[start + 1:]:
        if line.startswith("|"):
            if not line.startswith("|---"):
                out.append(_cells(line))
        elif out:
            break
        elif line.startswith("#"):
            break
    return out


def side_by_side():
    """{measure label: {column: cell}} of the page's table "The three devices side by side"."""
    rows = table("## The three devices side by side")
    head = rows[0]
    return {r[0]: dict(zip(head[1:], r[1:])) for r in rows[1:]}


def sheets(device):
    """[(job id, five-crystal share, forbidden share, XEB, TVD)] of the device's sheet table, as printed."""
    text = RESULTS.read_text(encoding="utf-8")
    part = text.split("## The sheets: more law runs on each device", 1)[1]
    rows = table(f"### {device}", part)
    out = []
    for r in rows[1:]:
        job = r[0].strip("`")
        xeb = r[4].split()[0]
        out.append((job, r[2], r[3], xeb, r[5].split(" / ")[0]))
    return out


def figure(cell):
    """A printed figure's value: the first number of its cell."""
    return float(re.match(r"[-+]?[0-9]+\.[0-9]+", cell.strip()).group(0))


def figures(cell):
    """Every number a cell prints: a value and its error, or two values beside a slash."""
    return [float(x) for x in re.findall(r"[-+]?[0-9]+\.[0-9]+", cell)]


def printed(x, places=4):
    """A float as Quantum-Film's tables print it, at so many places."""
    return float(f"{x:.{places}f}")


def frac(spelt):
    return Fraction(spelt)
