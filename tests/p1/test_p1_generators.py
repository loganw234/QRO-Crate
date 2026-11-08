"""The two generators P1 registers with the checker (qro/register_p1.py GENERATORS, FORMAT.md item 20): their names, how the
checker merges them, and what step 9 makes of one that cannot run. (What they write is test_p1_generate.py's, and the
Atlas one's test_p1_atlas_generate.py's; that P1's code costs a crate with none of P1's terms nothing, with every
`qro.p1_*` module unimportable, is P1.1's test_p1_register.py, which finds the modules by listing the directory and so
holds the three modules of this build as well.)"""
import sys

import pytest

import qro
from p1_support import synthetic_atlas, twin_copy
from qro import checker, p1_generate, register_p1
from qro.refusal import Refused


def test_p1_registers_two_generators_and_no_name_of_the_fixtures():
    assert sorted(register_p1.GENERATORS) == ["qro-p1-atlas", "qro-p1-ibm"]
    assert not [n for n in register_p1.GENERATORS if n.startswith(checker.FIXTURE_NAMES)]
    assert register_p1.GENERATORS["qro-p1-ibm"] is register_p1.generate_ibm
    assert register_p1.GENERATORS["qro-p1-atlas"] is register_p1.generate_atlas


def test_each_registered_generator_is_its_crates_generator_and_not_the_others(tmp_path):
    ibm, atlas = twin_copy(tmp_path / "a"), synthetic_atlas(tmp_path / "b")
    assert register_p1.generate_ibm(ibm) == p1_generate.ibm(ibm)
    assert register_p1.generate_atlas(atlas) == p1_generate.atlas(atlas)
    with pytest.raises(p1_generate.GuardError):
        register_p1.generate_ibm(atlas)
    with pytest.raises(p1_generate.GuardError):
        register_p1.generate_atlas(ibm)


def test_the_checker_merges_them_and_loading_twice_changes_nothing():
    checker.load()
    first = dict(checker.GENERATORS)
    checker.load()
    assert dict(checker.GENERATORS) == first
    assert first["qro-p1-ibm"] is register_p1.generate_ibm and first["qro-p1-atlas"] is register_p1.generate_atlas


def test_a_second_function_under_a_name_p1_holds_is_refused(monkeypatch):
    checker.load()
    monkeypatch.setitem(checker.GENERATORS, "qro-p1-ibm", lambda crate: {})
    with pytest.raises(checker.RegistrationError, match="qro-p1-ibm"):
        checker.load()


def test_a_generator_that_cannot_run_is_refused_by_step_9s_name_with_the_failure_in_its_detail(tmp_path, monkeypatch):
    crate = twin_copy(tmp_path)
    checker.load()
    monkeypatch.setitem(sys.modules, "qro.p1_generate", None)          # the module will not import
    monkeypatch.delattr(qro, "p1_generate", raising=False)
    with pytest.raises(Refused) as x:
        checker.check(crate)
    assert x.value.name == "metadata-generated" and x.value.where == "./ qro:generator"
    assert "qro-p1-ibm failed on the records: ModuleNotFoundError" in x.value.detail


def test_a_crate_naming_a_generator_p1_does_not_register_is_step_unbuilt(tmp_path):
    from controls import plants_p1 as plants
    crate = plants.patch(twin_copy(tmp_path), lambda g: g[1].update({"qro:generator": "qro-p1-made-up"}))
    checker.load()
    with pytest.raises(Refused) as x:
        checker.check(crate)
    assert x.value.name == "step-unbuilt" and "qro-p1-made-up" in x.value.detail
