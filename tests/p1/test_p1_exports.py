"""The guards P1 exports for P5 (qro/p1_guards.py; P1.3, the lead's ruling of 2026-11-08T15:33:03Z): the names and signatures P5's
unit generator imports are pinned here, so that a later change of P1's that would break P5 fails P1's own tests; each guard is
called directly, on the twin's own records, with what P5 can pass (a plain namespace for a job, a four-key dict for the files),
and refuses one planted fault with its guard's letter; P1's generator reaches each through the module, so each rule has one place;
and the module imports nothing of the generator, of P2's or of a register module.

The twin is read, never written: the pristine twin of P1 alone, built once in the process."""
import ast
import dataclasses
import inspect
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from controls import plants_p1 as plants
from p1_support import ROOT
from qro import p1_forms, p1_generate as G, p1_guards as P, p1_records as rec

PINNED = {
    "GuardError": "(guard, where, detail)",
    "hold": "(ok, guard, where, detail)",
    "read_record": "(guard, where, fn, *args)",
    "hold_line": "(crate, name, files, manifest, mdigest, spec, line)",
    "hold_device_runs": "(crate, where, found, manifest, spec, line)",
    "hold_commitments_and_counts": "(files, manifest, spec, line, records, raw)",
    "hold_metrics": "(files, line, metrics, raw)",
    "hold_refetch_job": "(crate, path, job)",
    "hold_refetch_result": "(crate, path, job, raw_path, committed_path)",
    "hold_read_manifest": "(crate, held, root, expect, carried, snapshot)",
}
ROOT_OF_READ = f"{G.READ}/ibm-refetch/"


class Held:
    """Everything the guards are given for the twin's morning known-answer job, parsed from the twin's own records."""

    def __init__(self):
        self.crate = G.Crate(plants.pristine_twin_alone())
        self.by = G._by_kind(self.crate, G.IBM_LAYOUTS, False)
        manifests = G._manifests(self.crate, self.by)
        self.jobs = G._jobs(self.crate, self.by, manifests)
        self.reads = G._reads(self.crate, self.by, self.jobs)
        j = next(j for j in self.jobs if j.label == "morning" and any(c.role == "known-answer" for c in j.spec))
        self.job = j
        self.files = {k: j.files[k] for k in ("line", "raw", "metrics", "submitting")}
        self.found = {k: [(path, c.name)] for k, (path, _, c) in j.records.items()}
        self.raw = p1_forms.parse_ibm_result(self.crate.read(j.files["raw"]))
        self.facts = SimpleNamespace(device=j.device, id=j.id, spec=j.spec, line=j.line, first=j.first, metrics=j.metrics)
        read_job, _, self.job_path, self.result_path = self.reads[j.id]
        self.committed = G.RECORDS_DIR + j.files["raw"]
        self.manifest_paths = [r for r, _ in self.by["refetch-manifest"]]


@pytest.fixture(scope="module")
def held():
    return Held()


def guard_of(call, *args, **kwargs):
    with pytest.raises(P.GuardError) as x:
        call(*args, **kwargs)
    return x.value


# -- 1. the names ----------------------------------------------------------------------------------------------------------------
def test_the_exported_names_are_exactly_these_and_import_as_p5_writes_them():
    assert P.EXPORTS == ("GuardError", "hold", "read_record", "hold_line", "hold_device_runs", "hold_commitments_and_counts",
                         "hold_metrics", "hold_refetch_job", "hold_refetch_result", "hold_read_manifest", "MAX_PUBS")
    ns = {}
    exec("from qro.p1_guards import (" + ", ".join(P.EXPORTS) + ")", ns)
    assert all(n in ns for n in P.EXPORTS) and ns["MAX_PUBS"] == 10
    assert inspect.isclass(P.GuardError) and G.GuardError is P.GuardError
    assert all(callable(getattr(P, n)) for n in P.EXPORTS if n != "MAX_PUBS")


# -- 2. the signatures -----------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", sorted(PINNED))
def test_each_exported_name_has_the_signature_p5_relies_on(name):
    target = P.GuardError.__init__ if name == "GuardError" else getattr(P, name)
    got = str(inspect.signature(target))
    assert got.replace("(self, ", "(") == PINNED[name], f"{name}{got}: P5 calls it as {name}{PINNED[name]}"


# -- 3. each guard, on the twin's records and what P5 can pass, holds ------------------------------------------------------------
def test_each_guard_holds_the_twins_known_answer_job_given_what_p5_can_pass(held):
    j = held
    P.hold_line(j.crate, j.job.name, j.files, j.job.manifest, j.job.mdigest, j.job.spec, j.job.line)
    records = P.hold_device_runs(j.crate, "w", j.found, j.job.manifest, j.job.spec, j.job.line)
    assert sorted(records) == sorted(j.job.records) and all(len(v) == 3 for v in records.values())
    assert P.hold_commitments_and_counts(j.files, j.job.manifest, j.job.spec, j.job.line, records, j.raw) is None
    assert P.hold_metrics(j.files, j.job.line, j.job.metrics, j.raw) is None
    first = P.hold_refetch_job(j.crate, j.job_path, j.facts)
    assert isinstance(first, rec.RefetchJob) and first.job_id == j.job.id
    second = P.hold_refetch_result(j.crate, j.result_path, j.facts, j.files["raw"], j.committed)
    assert isinstance(second, rec.RefetchResult) and second.committed_path == j.committed
    listed = P.hold_read_manifest(j.crate, j.manifest_paths, ROOT_OF_READ, rec.REFETCH_MANIFEST_FORMAT, {j.job.device},
                                  G._LISTED_SNAPSHOT)
    assert isinstance(listed, dict) and listed
    assert P.hold_read_manifest(j.crate, [], "nothing-here/", rec.REFETCH_MANIFEST_FORMAT, set(), G._LISTED_SNAPSHOT) is None


def test_hold_and_read_record_are_the_one_place_a_guard_raises_and_a_reader_refuses():
    P.hold(True, "G0", "w", "d")
    x = guard_of(P.hold, False, "G0", "w", "d")
    assert (x.guard, x.where, x.detail, str(x)) == ("G0", "w", "d", "G0 at w: d")
    assert P.read_record("G0", "w", lambda a, b: a + b, 1, 2) == 3
    for error in (rec.RecordError, p1_forms.RawFormError, p1_forms.SnapshotError):
        def refuses(error=error):
            raise error("no")
        y = guard_of(P.read_record, "G5", "w", refuses)
        assert (y.guard, y.where, y.detail) == ("G5", "w", "no")
    with pytest.raises(KeyError):                    # what is no reader's refusal is not turned into one
        P.read_record("G5", "w", {}.__getitem__, "x")


# -- 4. each guard, given one planted fault, raises its letter -------------------------------------------------------------------
def test_g2_the_line_is_held_to_the_manifest_and_the_marker_to_the_job_and_its_bundle(held):
    j = held
    args = (j.crate, j.job.name, j.files, j.job.manifest, j.job.mdigest, j.job.spec, j.job.line)
    for what, edit in {
            "bundle_sha256": lambda a: [*a[:6], dataclasses.replace(a[6], bundle_sha256="0" * 64)],
            "commitments": lambda a: [*a[:6], dataclasses.replace(a[6], commitments=("0" * 64,))],
            "stock": lambda a: [*a[:6], dataclasses.replace(a[6], stock="other")],
            "kind": lambda a: [*a[:6], dataclasses.replace(a[6], kind="other")],
            "route": lambda a: [*a[:6], dataclasses.replace(a[6], route="other")],
            "backend": lambda a: [*a[:6], dataclasses.replace(a[6], backend="other")],
            "program": lambda a: [*a[:6], dataclasses.replace(a[6], program="other")],
            "the marker's bundle": lambda a: [a[0], a[1], a[2], a[3], "0" * 64, a[5], dataclasses.replace(a[6], bundle_sha256="0" * 64)],
            "the marker's job": lambda a: [a[0], "another-job", *a[2:]]}.items():
        x = guard_of(P.hold_line, *edit(list(args)))
        assert x.guard == "G2", what
    assert guard_of(P.hold_line, *edit_name(args)).where == j.files["submitting"]


def edit_name(args):
    return [args[0], "another-job", *args[2:]]


def test_g3_the_records_are_one_for_each_pub_with_a_digest_that_is_their_bodys_and_a_source_that_agrees(held):
    j = held
    m, spec, line = j.job.manifest, j.job.spec, j.job.line
    path, circuit = j.found[0][0]
    assert guard_of(P.hold_device_runs, j.crate, "w", {}, m, spec, line).guard == "G3"                        # none
    assert "has 2 records" in guard_of(P.hold_device_runs, j.crate, "w", {0: [(path, circuit)] * 2}, m, spec, line).detail
    assert "is of circuit" in guard_of(P.hold_device_runs, j.crate, "w", {0: [(path, "another")]}, m, spec, line).detail
    for term, edit in {"stock": dict(stock="other"), "backend": dict(backend="other"), "route": dict(route="other"),
                       "decode": dict(decode="other"), "options_sha256": dict(options_sha256="0" * 64)}.items():
        x = guard_of(P.hold_device_runs, j.crate, "w", j.found, dataclasses.replace(m, **edit), spec, line)
        assert x.guard == "G3" and term in x.detail, term
    x = guard_of(P.hold_device_runs, j.crate, "w", j.found, m, spec, dataclasses.replace(line, job_id="other-job"))
    assert x.guard == "G3" and "source.job_id" in x.detail
    x = guard_of(P.hold_device_runs, j.crate, "w", j.found, m, (dataclasses.replace(spec[0], salt="0" * 32),), line)
    assert x.guard == "G3" and "source.salt" in x.detail
    x = guard_of(P.hold_device_runs, j.crate, "w", j.found, m, (dataclasses.replace(spec[0], role="law"),), line)
    assert x.guard == "G3" and "role" in x.detail
    x = guard_of(P.hold_device_runs, j.crate, "w", {}, m, (None,) * (P.MAX_PUBS + 1), line)
    assert x.guard == "G3" and f"{P.MAX_PUBS + 1} PUBs" in x.detail and "PUBs []" not in x.detail
    good = j.crate.read(path)
    altered = good.replace(j.job.records[0][1].digest.encode("ascii"), b"0" * 64, 1)
    assert altered != good
    x = guard_of(P.hold_device_runs, SimpleNamespace(read=lambda rel: altered), "w", j.found, m, spec, line)
    assert x.guard == "G3" and "digest" in x.detail
    assert "PUBs []" in guard_of(P.hold_device_runs, j.crate, "w", {}, m, (None,) * P.MAX_PUBS, line).detail
    fake = SimpleNamespace(read=lambda rel: j.crate.read(rel)[:-1] + b"X")
    assert guard_of(P.hold_device_runs, fake, "w", j.found, m, spec, line).guard == "G3"              # a record that is no record


def test_g4_and_g5_the_commitments_and_the_counts(held):
    j = held
    files, m, spec, line, raw = j.files, j.job.manifest, j.job.spec, j.job.line, j.raw
    records = j.job.records
    path, run, c = records[0]
    bad = "0" * 64
    echo = dataclasses.replace(raw.pubs[0], echo=bad)
    variants = {
        "the manifest's": (files, m, (dataclasses.replace(c, commitment=bad),), line,
                           {0: (path, run, dataclasses.replace(c, commitment=bad))}, raw),
        "the line's": (files, m, spec, dataclasses.replace(line, commitments=(bad,)), records, raw),
        "the record's": (files, m, spec, line, {0: (path, dataclasses.replace(run, source={**run.source, "commitment": bad}), c)}, raw),
        "IBM's echo": (files, m, spec, line, records, dataclasses.replace(raw, pubs=(echo,))),
    }
    for name, args in variants.items():
        x = guard_of(P.hold_commitments_and_counts, *args)
        assert (x.guard, x.detail.startswith(name)) == ("G4", True), name
    x = guard_of(P.hold_commitments_and_counts, files, dataclasses.replace(m, decode="no-such-rule"), spec, line, records, raw)
    assert x.guard == "G5" and "no decode rule" in x.detail
    x = guard_of(P.hold_commitments_and_counts, files, m, (spec[0], spec[0]), line, records, raw)
    assert x.guard == "G5" and "holds 1 PUBs" in x.detail
    x = guard_of(P.hold_commitments_and_counts, files, m, (dataclasses.replace(spec[0], shots=spec[0].shots + 1),), line,
                 {0: (path, run, dataclasses.replace(c, shots=c.shots + 1))}, raw)
    assert x.guard == "G5" and "shots" in x.detail
    x = guard_of(P.hold_commitments_and_counts, files, m, spec, line,
                 {0: (path, dataclasses.replace(run, counts={"0" * 16: 1}), c)}, raw)
    assert x.guard == "G5" and "counts are not" in x.detail


def test_g6_the_metrics_name_the_job_and_the_device_agree_on_the_created_time_and_bound_the_span(held):
    j = held
    files, line, metrics, raw = j.files, j.job.line, j.job.metrics, j.raw
    assert raw.spans
    for what, args in {
            "job": (files, line, dataclasses.replace(metrics, job_id="other"), raw),
            "device": (files, line, dataclasses.replace(metrics, backend="other"), raw),
            "created": (files, line, dataclasses.replace(metrics, created=metrics.created.replace(year=2000)), raw),
            "running": (files, line, dataclasses.replace(metrics, running=raw.last_shot.replace(year=2100)), raw),
            "finished": (files, line, dataclasses.replace(metrics, finished=raw.first_shot.replace(year=2000)), raw)}.items():
        assert guard_of(P.hold_metrics, *args).guard == "G6", what
    spanless = dataclasses.replace(raw, spans=())
    assert P.hold_metrics(files, line, dataclasses.replace(metrics, running=raw.last_shot.replace(year=2100)), spanless) is None


def test_g7_the_read_of_a_job_is_held_to_the_job(held):
    j = held
    f = j.facts
    for what, job in {
            "device": SimpleNamespace(**{**vars(f), "device": "ibm_other"}),
            "id": SimpleNamespace(**{**vars(f), "id": "other-job"}),
            "role": SimpleNamespace(**{**vars(f), "spec": tuple(dataclasses.replace(c, role="law") for c in f.spec)}),
            "commitments": SimpleNamespace(**{**vars(f), "line": dataclasses.replace(f.line, commitments=("0" * 64,))}),
            "pub count": SimpleNamespace(**{**vars(f), "line": dataclasses.replace(f.line, commitments=(*f.line.commitments, "0" * 64))}),
            "first shot": SimpleNamespace(**{**vars(f), "first": f.first.replace(year=2000)}),
            "running": SimpleNamespace(**{**vars(f), "metrics": dataclasses.replace(f.metrics, running=f.metrics.running.replace(year=2000))}),
    }.items():
        assert guard_of(P.hold_refetch_job, j.crate, j.job_path, job).guard == "G7", what
    assert P.hold_refetch_job(j.crate, j.job_path, SimpleNamespace(**{**vars(f), "first": None}))      # no span: no first shot to hold


def test_g7_a_flag_the_read_does_not_hold_is_a_raise(held):
    j = held
    changed = j.crate.read(j.job_path).replace(b'"commitments_equal": true', b'"commitments_equal": false', 1)
    assert changed != j.crate.read(j.job_path)
    fake = SimpleNamespace(read=lambda rel: changed)
    x = guard_of(P.hold_refetch_job, fake, j.job_path, j.facts)
    assert x.guard == "G7" and "commitments_equal" in x.detail


def test_g8_the_result_record_is_held_to_the_raw_result_and_to_the_path_it_names(held):
    j = held
    f = j.facts
    ok = P.hold_refetch_result(j.crate, j.result_path, f, j.files["raw"], j.committed)
    assert ok.committed_path == j.committed
    x = guard_of(P.hold_refetch_result, j.crate, j.result_path, f, j.files["raw"], j.committed + "x")
    assert x.guard == "G8" and "another file" in x.detail                                  # the caller's path decides
    assert P.hold_refetch_result(j.crate, j.result_path, f, j.files["raw"], ok.committed_path) is not None
    other = next(p for p in j.job.files.values() if p != j.files["raw"] and p.endswith(".json"))
    assert guard_of(P.hold_refetch_result, j.crate, j.result_path, f, other, j.committed).guard == "G8"       # not the raw's digest
    assert guard_of(P.hold_refetch_result, j.crate, j.result_path, SimpleNamespace(**{**vars(f), "device": "other"}),
                    j.files["raw"], j.committed).guard == "G8"
    assert guard_of(P.hold_refetch_result, j.crate, j.result_path, SimpleNamespace(**{**vars(f), "id": "other"}),
                    j.files["raw"], j.committed).guard == "G8"
    changed = j.crate.read(j.result_path).replace(b'"bytes_equal": true', b'"bytes_equal": false', 1)
    assert changed != j.crate.read(j.result_path)
    fake = SimpleNamespace(read=lambda rel: changed, info=j.crate.info)
    assert guard_of(P.hold_refetch_result, fake, j.result_path, f, j.files["raw"], j.committed).guard == "G8"


class Over:
    """The twin's crate, as far as G9 asks: its paths and what it says of a file may be changed."""

    def __init__(self, crate, paths=None, info=None):
        self.crate, self.paths, self._info = crate, crate.paths if paths is None else paths, info or {}

    def read(self, rel):
        return self.crate.read(rel)

    def info(self, rel):
        return self._info.get(rel) or self.crate.info(rel)


def test_g9_the_manifest_of_the_read_is_carried_and_lists_what_the_directory_holds_as_it_hashes(held):
    j = held
    root, expect, carried = ROOT_OF_READ, rec.REFETCH_MANIFEST_FORMAT, {j.job.device}
    path = j.manifest_paths[0]
    listed = P.hold_read_manifest(j.crate, j.manifest_paths, root, expect, carried, G._LISTED_SNAPSHOT)
    assert "more than one" in guard_of(P.hold_read_manifest, j.crate, [path, path], root, expect, carried, G._LISTED_SNAPSHOT).detail
    assert "not its MANIFEST" in guard_of(P.hold_read_manifest, j.crate, [], root, expect, carried, G._LISTED_SNAPSHOT).detail
    x = guard_of(P.hold_read_manifest, Over(j.crate, [*j.crate.paths, root + "extra.json"]), j.manifest_paths, root, expect, carried,
                 G._LISTED_SNAPSHOT)
    assert x.guard == "G9" and "not in its MANIFEST" in x.detail
    name = next(n for n in sorted(listed) if root + n in j.crate.paths)
    x = guard_of(P.hold_read_manifest, Over(j.crate, info={root + name: ("0" * 64, 1)}), j.manifest_paths, root, expect, carried,
                 G._LISTED_SNAPSHOT)
    assert x.guard == "G9" and "its MANIFEST lists" in x.detail
    shot = next(n for n in sorted(listed) if G._LISTED_SNAPSHOT.fullmatch(n) and
                G._LISTED_SNAPSHOT.fullmatch(n).group("device") == j.job.device and root + n in j.crate.paths)
    x = guard_of(P.hold_read_manifest, Over(j.crate, [p for p in j.crate.paths if p != root + shot]), j.manifest_paths, root, expect,
                 carried, G._LISTED_SNAPSHOT)
    assert x.guard == "G9" and "the crate lacks it" in x.detail
    assert P.hold_read_manifest(Over(j.crate, [p for p in j.crate.paths if p != root + shot]), j.manifest_paths, root, expect,
                                set(), G._LISTED_SNAPSHOT)                    # a device the crate carries no job of: not asked
    assert guard_of(P.hold_read_manifest, j.crate, j.manifest_paths, root, "another/format", carried, G._LISTED_SNAPSHOT).guard == "G9"


# -- 5. one place for each rule --------------------------------------------------------------------------------------------------
CALLED = ("hold_line", "hold_device_runs", "hold_commitments_and_counts", "hold_metrics", "hold_refetch_job",
          "hold_refetch_result", "hold_read_manifest")


def test_p1s_generator_reaches_each_guard_through_the_module_and_passes_g8_the_layouts_path(held, monkeypatch):
    seen = {}
    for name in CALLED:
        real = getattr(P, name)

        def spy(*args, _name=name, _real=real):
            seen.setdefault(_name, []).append(args)
            return _real(*args)
        monkeypatch.setattr(P, name, spy)
    monkeypatch.setattr(G, "p2_module", lambda: None)
    G.ibm(held.crate.root)
    assert set(seen) == set(CALLED)
    committed = {a[4] for a in seen["hold_refetch_result"]}
    assert committed == {G.RECORDS_DIR + a[3] for a in seen["hold_refetch_result"]} and len(committed) == len(
        seen["hold_refetch_result"]) > 1


def parsed(module):
    return ast.parse(Path(module.__file__).read_text(encoding="utf-8"))


def test_the_generator_holds_no_private_copy_of_a_guard_and_binds_neither_switch_at_import():
    tree = parsed(G)
    defined = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert not defined & {"_hold", "_read", "_g2", "_g3", "_g4_g5", "_g6", "_g7", "_g8", "hold", "read_record"}
    assert not defined & {n for n in defined if re.fullmatch(r"_?hold_.*", n)}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "qro.p1_guards":
            raise AssertionError("p1_generate binds a name of p1_guards at import: one monkeypatch of p1_guards.hold would miss it")
        if isinstance(n, ast.ImportFrom) and n.module == "qro":
            assert not {a.asname or a.name for a in n.names} & {"hold", "read_record"}
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            assert n.func.id not in {"hold", "read_record", "_hold", "_read"}, f"line {n.lineno}"
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not names & {"_hold", "_read", "hold", "read_record"}
    assert "p1_guards" in {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "qro" for a in n.names}


def test_one_switch_turns_off_every_guard_of_both_modules(held, monkeypatch):
    monkeypatch.setattr(P, "hold", lambda *a: None)
    P.hold_line(held.crate, "another-job", held.files, held.job.manifest, "0" * 64, held.job.spec, held.job.line)
    monkeypatch.setattr(G, "p2_module", lambda: None)
    assert G.ibm(held.crate.root)


# -- the module imports no seam ------------------------------------------------------------------------------------------------------
def test_p1_guards_imports_the_standard_library_and_p1s_readers_and_nothing_else():
    modules = []
    for n in ast.walk(parsed(P)):
        if isinstance(n, ast.Import):
            modules += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            assert n.level == 0
            modules += [f"{n.module}.{a.name}" if n.module == "qro" else n.module for a in n.names]
    assert sorted(modules) == ["qro.p1_commit", "qro.p1_decode", "qro.p1_forms", "qro.p1_records"], modules
    assert not [m for m in modules if "generate" in m or "p2" in m or "register" in m]


# -- the page --------------------------------------------------------------------------------------------------------------------------
def test_the_page_has_a_section_that_names_each_export():
    page = (ROOT / "docs" / "P1.md").read_text(encoding="utf-8")
    start = page.index("## The guards P5 imports")
    end = page.find("\n## ", start + 5)
    section = page[start:end if end != -1 else None]
    for name in P.EXPORTS:
        assert f"`{name}`" in section or f"`{name}(" in section, name
    assert "tests/p1/test_p1_exports.py" in section
