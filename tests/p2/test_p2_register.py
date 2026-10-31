"""What P2 registers (FORMAT.md, item 20; P2's design, item 12): steps 6 and 7 and nothing else; the entry rule the
lead set on E1, a term whose step, in the vocabulary, is the step's, or an entity of the step's own types, and nothing
else, a bare Compile among the nothing; the stated limit that rule concedes; and P0's fixture accepted with P2 loaded
and with every qro.p2_* module unimportable, in process and as a process, with the poison's control."""
import ast
import dataclasses
import os
import subprocess
import sys
from pathlib import Path

import pytest
from p2_builder import read_md, small_model

from qro import canonical, checker, fixture, p2_steps, register_p2
from qro import vocabulary as V
from qro.refusal import Refused

ROOT = Path(__file__).resolve().parents[2]
P2_MODULES = sorted(p.stem for p in (ROOT / "qro").glob("p2_*.py"))


@pytest.fixture
def fresh(monkeypatch):
    """The registries as no parcel has touched them, restored after the test."""
    monkeypatch.setattr(checker, "STEPS", {n: None for n in range(4, 9)})
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    monkeypatch.setattr(checker, "GENERATORS", {})
    monkeypatch.setattr(checker, "COUNTS", [])


def poison(monkeypatch):
    """Every qro.p2_* module unimportable: None in sys.modules refuses the import, and the package attribute that a
    `from qro import p2_x` would find first is removed."""
    import qro
    for name in P2_MODULES:
        monkeypatch.setitem(sys.modules, f"qro.{name}", None)
        monkeypatch.delattr(qro, name, raising=False)


# -- what is registered ------------------------------------------------------------------------------------------------
def test_p2_registers_steps_6_and_7_and_nothing_else(fresh):
    assert set(register_p2.STEPS) == {6, 7}
    assert register_p2.STEPS[6] is register_p2.step6 and register_p2.STEPS[7] is register_p2.step7
    for name in ("RAW_FORMS", "COUNTS", "GENERATORS"):
        assert not getattr(register_p2, name, None), name
    checker.load()
    assert {n for n, f in checker.STEPS.items() if f is not None and f.__module__ == "qro.register_p2"} == {6, 7}
    assert not [f for f in list(checker.RAW_FORMS.values()) + list(checker.GENERATORS.values()) + checker.COUNTS
                if f.__module__ == "qro.register_p2"]


def test_p2_registers_only_the_steps_the_vocabulary_gives_it():
    owners = checker.step_owners()
    assert set(register_p2.STEPS) == {n for n, o in owners.items() if o == "P2"} == {6, 7}


def test_no_name_p2_registers_is_a_name_of_the_fixtures():
    assert not any(str(n).startswith(checker.FIXTURE_NAMES) for n in register_p2.STEPS)
    assert not [k for k in vars(register_p2) if k.startswith(checker.FIXTURE_NAMES)]


def test_loading_twice_changes_nothing(fresh):
    checker.load()
    before = (dict(checker.STEPS), dict(checker.RAW_FORMS), dict(checker.GENERATORS), list(checker.COUNTS))
    checker.load()
    assert (checker.STEPS, checker.RAW_FORMS, checker.GENERATORS, checker.COUNTS) == before


def test_the_module_imports_nothing_at_its_top_level_and_only_the_vocabulary_and_p2_steps_inside():
    tree = ast.parse((ROOT / "qro" / "register_p2.py").read_text(encoding="utf-8"))
    assert not [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    inside = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert inside and all(isinstance(n, ast.ImportFrom) and n.module == "qro" for n in inside)
    assert {a.name for n in inside for a in n.names} == {"vocabulary", "p2_steps"}


# -- the entry rule (the lead's decision on E1) ------------------------------------------------------------------------
@pytest.fixture
def calls(monkeypatch):
    seen = []
    monkeypatch.setattr(p2_steps, "step6", lambda crate, md: seen.append(6))
    monkeypatch.setattr(p2_steps, "step7", lambda crate, md: seen.append(7))
    return seen


def graph(*entities):
    return {"@graph": [{"@id": "ro-crate-metadata.json", "@type": "CreativeWork"},
                       {"@id": "./", "@type": "Dataset", "qro:generator": "x"}, *entities]}


@pytest.mark.parametrize("entity, want", [
    ({"@id": "#m", "@type": ["CreateAction", "qro:Measuring"]}, [6]),
    ({"@id": "#c", "@type": "qro:Contrast"}, [6]),
    ({"@id": "#m", "@type": "qro:Measurement"}, [6]),
    ({"@id": "#h", "@type": ["CreateAction", "qro:Hold"]}, [7]),
    ({"@id": "#q", "@type": "CreativeWork", "qro:law": {"@id": "law.json"}}, [6]),
    ({"@id": "#x", "@type": "Thing", "qro:value": "none"}, [6]),
    ({"@id": "#x", "@type": "Thing", "qro:exactHold": "withheld"}, [7]),
    ({"@id": "#x", "@type": "Thing", "qro:holdRule": "qro-exact-hold/1"}, [7]),
    ({"@id": "#k", "@type": ["CreateAction", "qro:Compile"], "object": [{"@id": "a.qasm"}]}, []),
    ({"@id": "#p", "@type": "qro:Pub", "qro:role": "law", "qro:basis": "ZZZZ"}, []),
    ({"@id": "#q", "@type": ["CreativeWork", "qro:Question"]}, []),
    ({"@id": "#x", "@type": "Thing", "qro:commitment": "none"}, []),
])
def test_each_step_enters_on_its_own_terms_and_types_and_on_nothing_else(calls, entity, want):
    for step in (register_p2.step6, register_p2.step7):
        step(Path("."), graph(entity))
    assert calls == want


def test_a_terms_step_is_read_from_the_vocabulary(calls, monkeypatch):
    """A term moved to another step in the vocabulary moves the wrapper with it: no list of the wrapper's own."""
    monkeypatch.setitem(V.TERM, "qro:law", dataclasses.replace(V.TERM["qro:law"], step=7))
    md = graph({"@id": "#q", "@type": "CreativeWork", "qro:law": {"@id": "law.json"}})
    register_p2.step6(Path("."), md)
    register_p2.step7(Path("."), md)
    assert calls == [7]


def test_the_stated_limit_a_crate_stripped_of_p2s_terms_and_types_passes_steps_6_and_7(tmp_path, calls):
    """The lead's stated limit (E1): a crate that carries no term and no type of P2's passes steps 6 and 7, whatever
    law or coherence PUBs and Compiles it holds, a law file that is no law among them. Step 9 alone refuses it,
    wherever its generator writes P2's entities."""
    crate = small_model().write(tmp_path / "crate")
    (crate / "question" / "law.json").write_bytes(b"not a law")
    md = read_md(crate)
    p2_types = {"qro:Measuring", "qro:Contrast", "qro:Measurement", "qro:Hold"}
    md["@graph"] = [{k: v for k, v in e.items() if not (k in V.TERM and V.TERM[k].step in (6, 7))}
                    for e in md["@graph"] if not set(canonical.types(e)) & p2_types]
    assert any("qro:Compile" in canonical.types(e) for e in md["@graph"])
    assert any(e.get("qro:role") in ("law", "coherence") for e in md["@graph"])
    register_p2.step6(crate, md)
    register_p2.step7(crate, md)
    assert calls == []


def test_the_real_steps_refuse_the_same_crate_with_its_p2_entities(tmp_path):
    """The control of the limit: with P2's entities, the law file that is no law is refused by step 6's name."""
    crate = small_model().write(tmp_path / "crate")
    md = read_md(crate)
    (crate / "question" / "law.json").write_bytes(b"not a law")
    with pytest.raises(Refused) as r:
        register_p2.step6(crate, md)
    assert (r.value.name, r.value.where) == ("measure-class", "#question qro:law")


# -- P0's fixture ------------------------------------------------------------------------------------------------------
def test_p0s_fixture_is_accepted_with_p2s_module_loaded(fresh, tmp_path):
    fixture.register()
    checker.load()
    assert checker.STEPS[6] is register_p2.step6 and checker.STEPS[7] is register_p2.step7
    crate = fixture.make(tmp_path / "crate")
    assert canonical.body_digest(checker.check(crate)) == canonical.body_digest(read_md(crate))


def test_p0s_fixture_is_accepted_with_every_qro_p2_module_unimportable(fresh, tmp_path, monkeypatch):
    fixture.register()
    checker.load()
    poison(monkeypatch)
    for name in P2_MODULES:
        with pytest.raises(ImportError):
            __import__(f"qro.{name}")
    crate = fixture.make(tmp_path / "crate")
    assert canonical.body_digest(checker.check(crate)) == canonical.body_digest(read_md(crate))


def test_a_crate_with_p2s_entities_is_not_accepted_when_its_modules_are_unimportable(tmp_path, monkeypatch):
    """The control of the poison: it bites. The small crate carries P2's terms, and the steps cannot import
    themselves."""
    crate = small_model().write(tmp_path / "crate")
    md = read_md(crate)
    poison(monkeypatch)
    for step in (register_p2.step6, register_p2.step7):
        with pytest.raises(ImportError):
            step(crate, md)


ENV = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
ENV.update(PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8")


def run_script(script, argv):
    return subprocess.run([sys.executable, "-c", script, *argv], capture_output=True, env=ENV, cwd=ROOT)


def run_poisoned(argv):
    """The command line, in a process in which every qro.p2_* module is unimportable."""
    return run_script("import sys\n"
                      f"for n in {P2_MODULES!r}:\n    sys.modules['qro.' + n] = None\n"
                      "from qro.__main__ import main\n"
                      "sys.exit(main(sys.argv[1:]))\n", argv)


def test_the_command_line_accepts_p0s_fixture_with_every_qro_p2_module_unimportable(tmp_path):
    crate = fixture.make(tmp_path / "crate")
    p = run_poisoned(["check", "--fixtures", str(crate)])
    want = canonical.body_digest(read_md(crate))
    assert (p.returncode, p.stdout, p.stderr) == (0, f"ACCEPTED {want}\n".encode(), b"")


def test_the_command_line_does_not_accept_a_crate_with_p2s_entities_when_its_modules_are_unimportable(tmp_path):
    """The poison's control as a process: the step cannot import itself, which is the checker failing (exit 3), not
    a verdict; with the modules importable the same crate passes steps 6 and 7 and stops at step 9."""
    crate = small_model().write(tmp_path / "crate")
    p = run_poisoned(["check", str(crate)])
    assert p.returncode == 3 and p.stdout == b"" and p.stderr.startswith(b"FAILED: the checker itself failed")
    q = subprocess.run([sys.executable, "-m", "qro", "check", str(crate)], capture_output=True, env=ENV, cwd=ROOT)
    assert q.returncode == 1 and q.stdout.startswith(b"REFUSED step-unbuilt at ./ qro:generator")


def test_checking_a_crate_with_none_of_p2s_terms_imports_no_module_of_p2s_but_its_registration(tmp_path):
    crate = fixture.make(tmp_path / "crate")
    p = run_script("import os, sys\n"
                   "from qro.__main__ import main\n"
                   "code = main(sys.argv[1:])\n"
                   "loaded = sorted(m for m in sys.modules if m.startswith(('qro.p2_', 'qro.register_p2')))\n"
                   "os.write(2, ','.join(loaded).encode())\n"
                   "sys.exit(code)\n", ["check", "--fixtures", str(crate)])
    assert p.returncode == 0 and p.stdout.startswith(b"ACCEPTED ")
    assert p.stderr == b"qro.register_p2"
