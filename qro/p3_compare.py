"""The comparison of two runs: the one function that computes a comparison's record, the check that holds a
comparison crate to it, and `make`, its producer (P3's design, items 1, 7 and 8; P3.1). Standard library and qro only.

    python -m qro compare COMPARISON_DIR CRATE_DIR [CRATE_DIR ...]      P0's command, which calls check() here
    python -m qro.p3_compare make --declaration FILE [--preregistration FILE] --out DIR CRATE_DIR [CRATE_DIR ...]

COMPUTE (`compute`) is a pure function of the declaration's bytes, the copy of the pre-registration and the runs'
crates' bytes, which `make` and `check` both call. In this order:
  1. `step-unbuilt` for what this version does not build (qro.p3_declaration.unbuilt), before any crate is read;
  2. each crate read (qro.p3_runs), each run's jobs selected, and each measure's members found: structure, no count;
  3. `step-unbuilt` for a crate holding a qro:Unit (P3.2's left-out rule); then the refusals before any value, in the
     study's order (qro.p3_refusals): `comparison-trivial`, `question-differs`, `role-missing` (per measure, and whole
     where none is left), `kind-not-qpu`; and `selector-late`, kept (qro.p3_declaration.late);
  4. `step-unbuilt` for a coherence measure whose readout is covered (qro.p3_readout): its bound is P3.2's;
  5. the family M (qro.p3_verdicts.family), fixed before any value is read;
  6. only then the values, from the raw bytes by P2's pub_values, and P2's intervals at M; the verdicts, causes,
     statements and unseen factors (qro.p3_verdicts); and the record (qro.p3_record's form).
It never reads a crate's Measurements, Contrasts, `qro:alpha` or `qro:family`, which are each crate's own (P2's limit
7): the classes come from qro.p2_law.classes, computed from each crate's law.

CHECK (`check(comparison_dir, crate_dirs)`, P0's contract, FORMAT.md item 23): a Summary whose str() is the one
ACCEPTED line, or Refused (exit 1), or Misuse (exit 2). In this order:
  1. misuse: the comparison's own directory given again as a crate directory, however the two are spelt (a link is
     followed);
  2. the comparison crate by the checker's nine steps: its refusal, at its place; then misuse where the crate they
     accept is no comparison, its generator not `qro-p3-comparison`;
  3. misuse, once each crate's identity is read (its metadata's body digest, read by the strict reader): a crate the
     declaration does not name, two given with one body digest, and a crate the declaration names that is not given
     (where a crate given cannot be read, this waits for its nine steps);
  4. each crate by the nine steps, whole (the design's limit 14): a refused crate refuses the comparison by its own
     name, at "crate <n>: <where>", n its place among the crates given;
  5. the record computed again by `compute`;
  6. the carried comparison/record.json held to those bytes, byte for byte: refused `comparison-generated` at
     "comparison/record.json line L column C" (qro.canonical.first_difference).
Anything else raised is the check failing, never a verdict: P0's command answers it exit 3.

MAKE (`make`) writes a comparison crate into an empty directory outside this repository: it reads the declaration
strictly, checks each crate by the nine steps, computes the record by `compute`, writes the declaration's bytes, the copy
of the pre-registration where the declaration names one, and the record, generates the metadata with the comparison's
generator and writes it with qro.canonical.write, which holds it to the strict reader, and checks the comparison crate
by the nine steps. So it never writes a comparison the check would refuse: a refusal is its exit 1 and one line.
It makes each directory one level at a time and each file anew, listing each as it is made, and a make that fails, at
any point, removes what it listed, files first and then directories, the deepest first, each only while it is still
what it made, by unlink and rmdir, never recursively; what another put among them stays (P1's limit 22, the same rule).
Its command line writes one line, as `python -m qro check` writes its own: exit 0 and `MADE comparison <identity>: ...`,
1 and a REFUSED line, 2 misuse and the usage, 3 the command itself failing.
"""
import contextlib
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

from qro import canonical, checker, p2_interval, p2_law, p3_declaration, p3_readout, p3_record, p3_refusals
from qro import p3_runs, p3_verdicts, reader, spelling
from qro.p3_declaration import RUNS
from qro.refusal import Refused

USAGE = ("usage: python -m qro.p3_compare make --declaration FILE [--preregistration FILE] --out DIR CRATE_DIR "
         "[CRATE_DIR ...]")
REPO = Path(__file__).resolve().parents[1]
WRITER = "qro 0.1.0, the P3 producer"
KIND_PHRASE = {"real": "declared real", "rehearsal": "a rehearsal, never cited as a result"}
LATE_PHRASE = {"none": "pre-registered", "selector-late": "exploratory (selector-late)"}


class Misuse(Exception):
    """Misuse of the comparison check or of make: exit 2, its message then the usage."""


class Summary:
    """A comparison's verdict line: `ACCEPTED comparison <identity>: ...` (check) or `MADE comparison ...` (make)."""

    def __init__(self, word, identity, kind, late, measures, refused):
        self.word, self.identity, self.kind, self.late = word, identity, kind, late
        self.measures, self.refused = measures, refused

    def __str__(self):
        tail = f", {self.refused} refused role-missing" if self.refused else ""
        return (f"{self.word} comparison {self.identity}: {KIND_PHRASE[self.kind]}; {LATE_PHRASE[self.late]}; "
                f"{self.measures} measures{tail}")


# -- the one function ----------------------------------------------------------------------------------------------------
class Run:
    def __init__(self, side, selector, crates):
        self.side, self.selector, self.crates = side, selector, tuple(crates)
        self.jobs = tuple(j for c in self.crates for j in p3_runs.selected(c, selector))


def structure(declaration, crates):
    """(runs, {measure: {side: [(job, pubs)]}}, {digest: Crate}): what the comparison selects and measures, from the
    declaration and {body digest: (directory, metadata)}, reading no count."""
    read = {d: p3_runs.read(directory, md, d) for d, (directory, md) in crates.items()}
    runs = {side: Run(side, declaration.plan.runs[side], [read[d] for d in declaration.crates[side]]) for side in RUNS}
    members = {m.measure: {side: p3_runs.members(runs[side].jobs, m.measure) for side in RUNS}
               for m in declaration.plan.measures}
    return runs, members, read


def compute(declaration, preregistration, crates):
    """(the record, a dict, and the summary's facts) of a comparison: `declaration` a Declaration, `preregistration` the
    copy's bytes or None, `crates` {body digest: (directory, metadata)} of every crate the declaration names, each
    accepted by the nine steps. Raises Refused for the refusals before any value, in the module docstring's order."""
    plan = declaration.plan
    p3_declaration.unbuilt(declaration)
    runs, members, read = structure(declaration, crates)
    p3_refusals.units(runs)
    p3_refusals.trivial(members)
    digests, question = p3_refusals.question(runs, members, plan)
    refused = p3_refusals.role_missing(members, plan)
    p3_refusals.kind(runs, plan)
    late = p3_declaration.late(plan.digest, preregistration)
    p3_readout.unbuilt(read, members, refused)
    M = p3_verdicts.family(members, refused)
    cache, measures = {}, []
    for m in plan.measures:
        if m.measure in refused:
            measures.append({"epsilon": spelling.rational(m.epsilon), "lacking": refused[m.measure],
                             "measure": m.measure, "refused": "role-missing"})
            continue
        measures.append(_measure(m, members[m.measure], read, runs, question[m.measure], M, plan.alpha, cache))
    record = {"alpha": spelling.rational(plan.alpha), "declaration": declaration.digest, "family": M,
              "format": p3_record.RECORD_FORMAT, "kind": plan.kind, "late": late, "measures": measures,
              "plan": plan.digest, "runs": {side: _run(runs[side], digests[side]) for side in RUNS}}
    return record, {"kind": plan.kind, "late": late, "measures": len(plan.measures), "refused": len(refused)}


def _run(run, digest):
    return {"crates": [{"crate": c.digest, "jobs": sorted(p3_refusals.name(j) for j in run.jobs if j.crate == c.digest),
                        "left": "none"} for c in run.crates],
            "device": run.selector.device, "kinds": sorted({j.kind for j in run.jobs if isinstance(j.kind, str)}),
            "question": digest}


def _measure(m, by_side, read, runs, question, M, alpha, cache):
    sides, classes = {}, {}
    for side in RUNS:
        tallies = []
        for job, pubs in sorted(by_side[side], key=lambda x: (p3_refusals.name(x[0]), x[0].crate)):
            crate = read[job.crate]
            values = [p3_verdicts.values_of(crate, p, cache)[m.measure] for p in pubs]
            total, n, mapping = p3_verdicts.total_of(values)
            tallies.append((p3_refusals.name(job), total, n, mapping))
        sides[side] = p3_verdicts.run_of(tallies, M, alpha)
        law = read[runs[side].crates[0].digest].law
        contrasts = p2_law.classes(law)
        classes[side] = {t: contrasts[(m.measure, t)].cls for t in p3_verdicts.TWINS}
    diff = p2_interval.difference(sides["a"]["interval"], sides["b"]["interval"])
    drifts = {side: sides[side]["drift"] for side in RUNS}
    strong = p2_interval.strong_form(diff, drifts["a"], drifts["b"]) if all(
        d is not None for d in drifts.values()) else None
    devices = {side: runs[side].selector.device for side in RUNS}
    causes = p3_verdicts.causes(by_side, read, question, devices, drifts)
    readout = p3_readout.status(m.measure)
    words = p3_verdicts.statements({
        "causes": causes, "members": {side: len(by_side[side]) for side in RUNS}, "strongForm": strong,
        "epsilon": m.epsilon, "interleaved": p3_verdicts.interleaved(by_side, devices),
        "readout": readout["status"], "rho": None, "classes": classes})
    return {"a": _side(sides["a"]), "b": _side(sides["b"]), "causes": causes, "classes": classes,
            "difference": p3_record.pair(diff), "epsilon": spelling.rational(m.epsilon),
            "means": p3_verdicts.means(diff, m.epsilon), "measure": m.measure, "readout": readout, "refused": "none",
            "statements": words, "strongForm": "none" if strong is None else spelling.rational(strong),
            "unseen": p3_verdicts.unseen(by_side, causes, read)}


def _side(s):
    return {"drift": "none" if s["drift"] is None else spelling.rational(s["drift"]),
            "inScope": s["n"], "interval": p3_record.pair(s["interval"]),
            "members": [{"id": i, "inScope": n, "interval": p3_record.pair(iv)} for i, n, iv in s["members"]],
            "value": "none" if s["value"] is None else spelling.rational(s["value"])}


# -- the check -----------------------------------------------------------------------------------------------------------
def _same(a, b):
    try:
        return os.path.samefile(a, b)
    except (OSError, ValueError):
        return False


def _identity(crate_dir):
    """A crate's body digest, read from its metadata by the strict reader; None where it cannot be read, which its
    nine steps then refuse."""
    try:
        return canonical.body_digest(reader.read((Path(crate_dir) / canonical.DESCRIPTOR).read_bytes()))
    except (Refused, OSError, ValueError):
        return None


def _misuse(declaration, given):
    """Misuse in the crates given ([(argument, its body digest or None)]) against the crates the declaration names."""
    named = set(declaration.crates["a"]) | set(declaration.crates["b"])
    seen = {}
    for arg, digest in given:
        if digest is None:
            continue
        if digest not in named:
            raise Misuse(f"{arg}: a crate the declaration does not name (its body digest is {digest})")
        if digest in seen:
            raise Misuse(f"{arg}: a crate given twice: its body digest is that of {seen[digest]}")
        seen[digest] = arg
    if all(d is not None for _, d in given):
        for digest in sorted(named - set(seen)):
            raise Misuse(f"the declaration names the crate {digest}, which is not given")


def located(refusal, prefix):
    """The refusal itself, its place now under `prefix` ("crate 2: data/x"): its name and its detail its own."""
    refusal.where = f"{prefix}: {refusal.where}"
    refusal.args = (f"{refusal.name} at {refusal.where}: {refusal.detail}",)
    return refusal


def _checked(crates):
    """{body digest: (directory, metadata)} of each crate, by the nine steps, a refusal at "crate <n>: <where>"."""
    out, given = {}, []
    for n, c in enumerate(crates, 1):
        try:
            md = checker.check(c)
        except Refused as r:
            raise located(r, f"crate {n}") from None
        digest = canonical.body_digest(md)
        given.append((c, digest))
        out[digest] = (Path(c), md)
    return out, given


def check(comparison_dir, crate_dirs):
    """The comparison's Summary, or Refused, or Misuse."""
    checker.load()
    crate_dirs = [str(c) for c in crate_dirs]
    for c in crate_dirs:
        if _same(comparison_dir, c):
            raise Misuse(f"{c}: the comparison's own directory, given again as a crate directory")
    md = checker.check(comparison_dir)
    generator = md["@graph"][1].get("qro:generator")
    if generator != p3_record.GENERATOR:
        raise Misuse(f"{comparison_dir}: no comparison crate: its generator is {generator}, not "
                     f"{p3_record.GENERATOR}")
    comparison = Path(comparison_dir)
    declaration = p3_declaration.read(comparison.joinpath(*p3_record.DECLARATION.split("/")).read_bytes())
    prereg = None
    if declaration.preregistration is not None:
        prereg = comparison.joinpath(*declaration.preregistration.split("/")).read_bytes()
    p3_declaration.unbuilt(declaration)
    _misuse(declaration, [(c, _identity(c)) for c in crate_dirs])
    crates, given = _checked(crate_dirs)
    _misuse(declaration, given)
    record, facts = compute(declaration, prereg, crates)
    want = p3_record.dumps(record)
    have = comparison.joinpath(*p3_record.RECORD.split("/")).read_bytes()
    if have != want:
        raise Refused("comparison-generated", f"{p3_record.RECORD} {canonical.first_difference(have, want)}",
                      "the record is not what the declaration and the runs' crates give: verdicts are computed only "
                      "on the runs' data")
    return Summary("ACCEPTED", canonical.body_digest(md), **facts)


# -- make ------------------------------------------------------------------------------------------------------------------
class _Made:
    """What a make has made, listed as it makes it: each directory, made one level at a time, so that one already
    there is never listed, and each file, made anew, so that one already there is never overwritten or listed; each
    with its identity (device, file number)."""

    def __init__(self):
        self.directories, self.files = [], []

    def directory(self, path):
        missing = []
        while not path.exists() and path != path.parent:
            missing.append(path)
            path = path.parent
        for level in reversed(missing):
            try:
                os.mkdir(level)
            except FileExistsError:
                if not level.is_dir():
                    raise
                continue
            st = os.lstat(level)
            self.directories.append((level, (st.st_dev, st.st_ino)))

    def write(self, path, data):
        self.directory(path.parent)
        with open(path, "xb") as f:
            st = os.fstat(f.fileno())
            self.files.append((path, (st.st_dev, st.st_ino)))
            f.write(data)


def _unchanged(path, identity, kind):
    st = os.lstat(path)
    return kind(st.st_mode) and not getattr(st, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT \
        and (st.st_dev, st.st_ino) == identity


def clear(made):
    """Remove what a failed make listed, and nothing else: each file while it is still the regular file it wrote, then
    each directory, the deepest first, while it is still the one it made, by rmdir, which removes only an empty one.
    Nothing is removed recursively, and nothing because its path was computed. What cannot be removed is left."""
    directories = dict(made.directories)

    def still(path, identity, kind):
        return _unchanged(path, identity, kind) and all(
            _unchanged(d, directories[d], stat.S_ISDIR) for d in path.parents if d in directories)
    for path, identity in made.files:
        with contextlib.suppress(OSError):
            if still(path, identity, stat.S_ISREG):
                os.unlink(path)
    for path, identity in sorted(made.directories, key=lambda d: len(d[0].parts), reverse=True):
        with contextlib.suppress(OSError):
            if still(path, identity, stat.S_ISDIR):
                os.rmdir(path)


def _inside(path, parent):
    path, parent = Path(os.path.realpath(path)), Path(os.path.realpath(parent))
    return path == parent or parent in path.parents


def check_out(out, crate_dirs):
    """Misuse unless `out` holds nothing yet and lies neither in this repository nor in a crate given."""
    out = Path(out)
    try:
        if _inside(out, REPO):
            raise Misuse(f"{out}: inside this repository; a comparison is made outside the tree, so that nothing of it "
                         "can be committed")
        for c in crate_dirs:
            if _inside(out, c) or _inside(c, out):
                raise Misuse(f"{out}: inside or around the crate {c}")
        if out.exists() and (not out.is_dir() or any(out.iterdir())):
            raise Misuse(f"{out}: not an empty directory; make writes into one that holds nothing")
    except Misuse:
        raise
    except (OSError, ValueError) as x:
        raise Misuse(f"{out}: cannot be used ({x})") from None


def make(declaration_bytes, out, crate_dirs, preregistration=None, now=None):
    """Write a comparison crate into `out`, which must be empty or absent, and return its Summary: Refused, or Misuse,
    otherwise, with what it made removed."""
    checker.load()
    crate_dirs = [str(c) for c in crate_dirs]
    try:
        declaration = p3_declaration.read(declaration_bytes)
    except p3_declaration.DeclarationError as x:
        raise Misuse(f"the declaration is not {p3_declaration.FORMAT}: {x}") from None
    if (declaration.preregistration is None) != (preregistration is None):
        raise Misuse("the declaration names a pre-registration and none is given" if preregistration is None else
                     "a pre-registration is given and the declaration names none")
    if preregistration is not None and not isinstance(preregistration, bytes):
        raise Misuse("a pre-registration is bytes")
    check_out(out, crate_dirs)
    p3_declaration.unbuilt(declaration)
    _misuse(declaration, [(c, _identity(c)) for c in crate_dirs])
    crates, given = _checked(crate_dirs)
    _misuse(declaration, given)
    record, facts = compute(declaration, preregistration, crates)
    md = write_comparison(out, declaration, declaration_bytes, record, preregistration, now)
    return Summary("MADE", canonical.body_digest(md), **facts)


def write_comparison(out, declaration, declaration_bytes, record, preregistration=None, now=None):
    """Write the comparison crate of this declaration (its bytes and its Declaration) and record into `out`, empty or
    absent, and check it by the nine steps; its metadata. A write that fails, at any point, removes what it made
    (`clear`) and raises."""
    out, made = Path(out), _Made()
    try:
        made.directory(out)
        made.write(out.joinpath(*p3_record.DECLARATION.split("/")), bytes(declaration_bytes))
        if preregistration is not None:
            made.write(out.joinpath(*declaration.preregistration.split("/")), preregistration)
        made.write(out.joinpath(*p3_record.RECORD.split("/")), p3_record.dumps(record))
        md = p3_record.generate(out)
        when = (now or datetime.now(timezone.utc)).replace(microsecond=0)
        md["@graph"][1].update({"datePublished": when.strftime("%Y-%m-%d"), "qro:writer": WRITER,
                                "qro:writtenAt": spelling.time(when)})
        made.write(out / canonical.DESCRIPTOR, canonical.write(md))
        checker.check(out)
    except BaseException:
        with contextlib.suppress(Exception):
            clear(made)
        raise
    return md


def _arguments(argv):
    if argv[:1] != ["make"]:
        raise Misuse("the one command is make")
    args, crates, i = {}, [], 1
    names = {"--declaration": "declaration", "--preregistration": "preregistration", "--out": "out"}
    while i < len(argv):
        if argv[i] in names:
            if i + 1 >= len(argv) or names[argv[i]] in args or not argv[i + 1]:
                raise Misuse(f"{argv[i]}: given twice, or without its value")
            args[names[argv[i]]] = argv[i + 1]
            i += 2
        elif argv[i].startswith("--"):
            raise Misuse(f"{argv[i]}: not an option of make")
        else:
            crates.append(argv[i])
            i += 1
    if "declaration" not in args or "out" not in args or not crates:
        raise Misuse("--declaration, --out and one crate directory or more are needed")
    return args, crates


def _read_file(path, what):
    try:
        return Path(path).read_bytes()
    except (OSError, ValueError) as x:
        raise Misuse(f"{path}: the {what} cannot be read ({getattr(x, 'strerror', None) or x})") from None


def _verdict(argv):
    try:
        args, crates = _arguments(argv)
        for c in crates:
            if not os.path.isdir(c):
                raise Misuse(f"{c}: no such crate directory")
        declaration = _read_file(args["declaration"], "declaration")
        prereg = _read_file(args["preregistration"], "pre-registration") if "preregistration" in args else None
        return 0, str(make(declaration, args["out"], crates, prereg))
    except Misuse as x:
        return 2, f"{x}; {USAGE}"
    except Refused as r:
        return 1, f"REFUSED {r.name} at {r.where}: {r.detail}"
    except PermissionError as x:
        return 2, f"{x.filename or 'a path'}: cannot be read here, {x.strerror}; {USAGE}"


def main(argv, out=1, err=2):
    """The exit code, after its one line is written to a descriptor, unbuffered, as `python -m qro check` writes."""
    from qro.__main__ import write
    try:
        code, line = _verdict(argv)
    except BaseException as x:
        code, line = 3, f"FAILED: make itself failed, {checker.describe(x)}; this is not a verdict"
    try:
        write(out if code in (0, 1) else err, line)
    except Exception:
        return 3
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
