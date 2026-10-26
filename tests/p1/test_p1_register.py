"""What P1 registers with the checker (FORMAT.md, item 20), and what a check of a crate with none of P1's entities
costs and risks: nothing. `qro.register_p1` imports only the standard library; each step it declares returns
before importing anything else of P1's when the metadata holds no entity its step visits; so P0's fixture, and every
other parcel's crate, is accepted with the module loaded and with every `qro.p1_*` module made unimportable, in
process and as the command line runs. A control: a crate with P1's entities, under the same poison, is not accepted."""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from p1_builder import SNAPS, ibm_model, read_md, snapshot_path

from qro import canonical, checker, fixture, register_p1
from qro.checker import RegistrationError
from qro.refusal import Refused

ROOT = Path(__file__).resolve().parents[2]
P1_MODULES = sorted(p.stem for p in (ROOT / "qro").glob("p1_*.py"))


@pytest.fixture
def fresh(monkeypatch):
    """The registries as no parcel has touched them, restored after the test."""
    monkeypatch.setattr(checker, "STEPS", {n: None for n in range(4, 9)})
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    monkeypatch.setattr(checker, "GENERATORS", {})
    monkeypatch.setattr(checker, "COUNTS", [])


def poison(monkeypatch):
    """Every qro.p1_* module unimportable: None in sys.modules refuses the import, and the package attribute that a
    `from qro import p1_x` would find first is removed."""
    import qro
    for name in P1_MODULES:
        monkeypatch.setitem(sys.modules, f"qro.{name}", None)
        monkeypatch.delattr(qro, name, raising=False)


# -- what is registered --------------------------------------------------------------------------------------------------
def test_p1_registers_steps_4_5_and_8_and_its_three_raw_forms_and_nothing_else_of_the_checkers(fresh):
    checker.load()
    assert {n for n, f in checker.STEPS.items() if f is not None and f.__module__ == "qro.register_p1"} == {4, 5, 8}
    assert checker.STEPS[4] is register_p1.step4 and checker.STEPS[5] is register_p1.step5
    assert checker.STEPS[8] is register_p1.step8
    assert {k for k, f in checker.RAW_FORMS.items() if f.__module__ == "qro.register_p1"} == {
        "ibm-sampler-result/v1", "atlas-tomography-result/v1", "atlas-known-answer-vector/v1"}
    assert [f for f in checker.COUNTS if f.__module__ == "qro.register_p1"] == []


def test_p1_declares_no_count_rule_and_only_its_own_two_generators():
    """Shots are counted by the raw forms; there is no count of any other entity (design item 9). The generators are
    the producer side's: if declared, only P1's two."""
    assert getattr(register_p1, "COUNTS", ()) == ()
    assert set(getattr(register_p1, "GENERATORS", {})) <= {"qro-p1-ibm", "qro-p1-atlas"}


def test_p1_registers_only_steps_the_vocabulary_gives_it(fresh):
    owners = checker.step_owners()
    assert set(register_p1.STEPS) == {n for n, o in owners.items() if o == "P1"} == {4, 5, 8}
    assert all(callable(f) for f in register_p1.STEPS.values())


def test_no_name_p1_registers_is_a_name_of_the_fixtures():
    names = list(register_p1.RAW_FORMS) + list(getattr(register_p1, "GENERATORS", {}))
    assert names and not any(n.startswith(checker.FIXTURE_NAMES) for n in names)


def test_loading_twice_changes_nothing(fresh):
    checker.load()
    before = (dict(checker.STEPS), dict(checker.RAW_FORMS))
    checker.load()
    assert (checker.STEPS, checker.RAW_FORMS) == before


def test_a_second_function_under_a_name_p1_holds_is_refused(fresh):
    checker.RAW_FORMS["ibm-sampler-result/v1"] = len
    with pytest.raises(RegistrationError, match="ibm-sampler-result/v1, which another function already holds"):
        checker.load()


def test_each_step_runs_for_a_crate_that_holds_only_the_entities_of_its_own_type(tmp_path):
    """The wrappers skip a crate with none of a step's entities, and only that: step 8 visits Jobs as well as
    Snapshots, so a crate whose jobs claim a link to snapshots it does not hold is not passed over for holding none."""
    m = ibm_model()
    for path in [p for p in m.files if p.startswith("snapshots/")]:
        del m.files[path], m.ents[path]
    for job, n in (("jobka", 1), ("joblaw", 2), ("jobcoh", 1)):
        m.ents["#job-" + job]["qro:calibration"] = [{"@id": f"https://example.org/snapshot-{i}"} for i in range(n)]
    crate = m.write(tmp_path / "crate")
    with pytest.raises(Refused) as r:
        register_p1.step8(crate, read_md(crate))
    assert r.value.name == "calibration-link" and "is not a Snapshot of the crate" in r.value.detail
    m = ibm_model()                                                     # decodes with no Pub, no Snapshot, no commitment
    for pub in [i for i in m.ents if i.startswith("#pub-")]:
        del m.ents[pub]
    for job in ("jobka", "joblaw", "jobcoh"):
        del m.ents["#job-" + job]["object"]
        m.ents["#decode-" + job]["qro:knownAnswer"] = {"@id": "https://example.org/a-known-answer"}
    crate = m.write(tmp_path / "decodes")
    md = read_md(crate)
    assert not [e for e in md["@graph"] if "qro:Pub" in (e["@type"] if isinstance(e["@type"], list) else [e["@type"]])]
    with pytest.raises(Refused) as r:
        register_p1.step5(crate, md)
    assert r.value.name == "known-answer" and "names no entity" in r.value.detail


def test_step_8_runs_for_a_crate_that_holds_snapshots_and_no_job(tmp_path):
    """The verifier's D2 of round 2. Step 8 visits Snapshots as well as Jobs, and the test above holds that only from the Job
    side (jobs, no snapshots), so a guard on Jobs alone passed every test. A crate of snapshots, one with a false claim, and a
    plain action that is no Job: the step must run, and refuse it. Steps 4 and 5 have no entity of theirs here and return."""
    m = ibm_model()
    for i in [i for i, e in m.ents.items() if {"qro:Job", "qro:Pub", "qro:Decode"} & set(
            e["@type"] if isinstance(e["@type"], list) else [e["@type"]])]:
        del m.ents[i]
    for path in [p for p in m.files if not p.startswith("snapshots/")]:
        del m.files[path]
        m.ents.pop(path, None)
    m.entity("#an-action", "CreateAction", name="an action that is no Job")
    m.ents[snapshot_path(SNAPS["s0902"][0])]["qro:valuesDigest"] = "0" * 64
    crate = m.write(tmp_path / "snapshots")
    md = read_md(crate)
    kinds = {t for e in md["@graph"] for t in (e["@type"] if isinstance(e["@type"], list) else [e["@type"]])}
    assert "qro:Snapshot" in kinds and not kinds & {"qro:Job", "qro:Pub", "qro:Decode"}
    with pytest.raises(Refused) as r:
        register_p1.step8(crate, md)
    assert r.value.name == "calibration-link" and "qro:valuesDigest" in r.value.where
    register_p1.step4(crate, md)
    register_p1.step5(crate, md)


def test_step_5_runs_for_a_crate_that_holds_decodes_and_no_job(tmp_path):
    """The verifier's D3 of round 3, the next step's D2 of round 2. Step 5 visits Decodes, and the test above keeps the Jobs in
    its crate of Decodes, so a guard on Jobs alone (mutant 12) passed every test. A crate of Decodes with no Job and no Pub: the
    step must run, and refuse a Decode whose raw result no job made. Step 4 has no Pub here and returns, and step 8 (the
    snapshots are honest, and there is no Job) returns too."""
    m = ibm_model()
    for i in [i for i, e in m.ents.items() if {"qro:Job", "qro:Pub"} & set(
            e["@type"] if isinstance(e["@type"], list) else [e["@type"]])]:
        del m.ents[i]
    for decode in ("jobka", "joblaw", "jobcoh"):
        m.ents["#decode-" + decode]["qro:knownAnswer"] = {"@id": "https://example.org/a-known-answer"}
    crate = m.write(tmp_path / "decodes")
    md = read_md(crate)
    kinds = {t for e in md["@graph"] for t in (e["@type"] if isinstance(e["@type"], list) else [e["@type"]])}
    assert "qro:Decode" in kinds and not kinds & {"qro:Job", "qro:Pub"}
    with pytest.raises(Refused) as r:
        register_p1.step5(crate, md)
    assert r.value.name == "known-answer" and r.value.where.startswith("#decode-")
    register_p1.step4(crate, md)
    register_p1.step8(crate, md)


def test_the_registered_readers_count_a_results_shots_and_refuse_what_is_no_result(fresh):
    from p1_builder import atlas_result, atlas_vector, raw_ibm
    checker.load()
    assert checker.RAW_FORMS["ibm-sampler-result/v1"](raw_ibm([[1, 2, 3]], [None])) == 3
    assert checker.RAW_FORMS["atlas-tomography-result/v1"](atlas_result({(0, 1, 2, 3, 4): 7})) == 7
    assert checker.RAW_FORMS["atlas-known-answer-vector/v1"](atlas_vector()) == 4096
    for form in ("ibm-sampler-result/v1", "atlas-tomography-result/v1", "atlas-known-answer-vector/v1"):
        with pytest.raises(checker.RawFormError):
            checker.RAW_FORMS[form](b"not a result")


def test_the_module_imports_nothing_at_its_top_level_and_only_p1s_modules_inside_a_function():
    tree = ast.parse((ROOT / "qro" / "register_p1.py").read_text(encoding="utf-8"))
    assert not [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    inside = [n for f in ast.walk(tree) if isinstance(f, ast.FunctionDef) for n in ast.walk(f)
              if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert inside and all(isinstance(n, ast.ImportFrom) and n.module == "qro" and
                          {a.name for a in n.names} <= set(P1_MODULES) for n in inside)


def test_every_module_of_p1s_imports_only_the_standard_library_and_the_package():
    """Standard library only (CLAUDE.md): no third-party import in any module of P1's."""
    stdlib = set(sys.stdlib_module_names)
    for name in P1_MODULES + ["register_p1"]:
        tree = ast.parse((ROOT / "qro" / f"{name}.py").read_text(encoding="utf-8"))
        roots = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        roots |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level == 0}
        assert roots <= stdlib | {"qro"}, (name, roots - stdlib)


# -- P0's fixture, with P1 loaded and with P1's modules made unimportable ----------------------------------------------------------------
def test_p0s_fixture_is_accepted_with_p1s_module_loaded(fresh, tmp_path):
    fixture.register()
    checker.load()
    assert checker.STEPS[4] is register_p1.step4
    crate = fixture.make(tmp_path / "crate")
    assert canonical.body_digest(checker.check(crate)) == canonical.body_digest(read_md(crate))


def test_p0s_fixture_is_accepted_with_every_qro_p1_module_unimportable(fresh, tmp_path, monkeypatch):
    fixture.register()
    checker.load()
    poison(monkeypatch)
    for name in P1_MODULES:
        with pytest.raises(ImportError):
            __import__(f"qro.{name}")
    assert checker.STEPS[4] is register_p1.step4
    crate = fixture.make(tmp_path / "crate")
    assert canonical.body_digest(checker.check(crate)) == canonical.body_digest(read_md(crate))


def test_a_crate_with_p1s_entities_is_not_accepted_when_its_modules_are_unimportable(fresh, tmp_path, monkeypatch):
    """The control of the poison: it bites. A Pub is an entity step 4 visits, and the step cannot import itself."""
    crate = ibm_model().write(tmp_path / "crate")
    md = read_md(crate)
    checker.load()
    poison(monkeypatch)
    with pytest.raises(ImportError):
        register_p1.step4(crate, md)
    with pytest.raises(ImportError):
        register_p1.step5(crate, md)
    with pytest.raises(ImportError):
        register_p1.step8(crate, md)


def with_a_pub(tmp_path):
    """P0's fixture crate and one entity step 4 visits: a Pub, which P0's own tests use as step 4's carrier."""
    crate = fixture.make(tmp_path / "crate")
    p = crate / canonical.DESCRIPTOR
    md = fixture.with_entity(json.loads(p.read_bytes()), {"@id": "#pub", "@type": "qro:Pub",
                                                          "qro:commitment": "a" * 64})
    p.write_bytes(canonical.dumps(md))
    return crate


def run_poisoned(argv):
    """The command line, in a process in which every qro.p1_* module is unimportable."""
    script = ("import sys\n"
              f"for n in {P1_MODULES!r}:\n    sys.modules['qro.' + n] = None\n"
              "from qro.__main__ import main\n"
              "sys.exit(main(sys.argv[1:]))\n")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, "-c", script, *argv], capture_output=True, env=env, cwd=ROOT)


def test_the_command_line_accepts_p0s_fixture_with_every_qro_p1_module_unimportable(tmp_path):
    crate = fixture.make(tmp_path / "crate")
    p = run_poisoned(["check", "--fixtures", str(crate)])
    want = canonical.body_digest(read_md(crate))
    assert (p.returncode, p.stdout, p.stderr) == (0, f"ACCEPTED {want}\n".encode(), b"")


def test_the_command_line_does_not_accept_a_crate_with_a_pub_when_p1s_modules_are_unimportable(tmp_path):
    """The control of the process's poison: the step cannot import itself, which is the checker failing (exit 3), not
    a verdict; and with the modules importable the same crate is refused for its commitment, by step 4's name."""
    crate = with_a_pub(tmp_path)
    p = run_poisoned(["check", "--fixtures", str(crate)])
    assert p.returncode == 3 and p.stdout == b"" and p.stderr.startswith(b"FAILED: the checker itself failed")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONPATH=str(ROOT))
    q = subprocess.run([sys.executable, "-m", "qro", "check", "--fixtures", str(crate)], capture_output=True, env=env,
                       cwd=ROOT)
    assert q.returncode == 1 and q.stdout.startswith(b"REFUSED commitment at #pub")
