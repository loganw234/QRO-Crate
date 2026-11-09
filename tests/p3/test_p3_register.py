"""What P3 registers with the checker (qro/register_p3.py; FORMAT.md item 20): the comparison crate's generator and
nothing else, loaded by checker.load(); a crate that is no comparison costs P3 nothing, P0's fixture accepted with P3's
modules unimportable; and a comparison crate whose generator cannot be loaded is refused by step 9's name, never
accepted."""
import builtins

import pytest

from controls import plants_p1, plants_p3
from qro import checker, fixture, register_p3
from qro.refusal import Refused


def test_p3_registers_its_generator_and_nothing_else():
    assert sorted(n for n in vars(register_p3) if n.isupper()) == ["GENERATORS"]
    assert list(register_p3.GENERATORS) == ["qro-p3-comparison"]
    checker.load()
    assert checker.GENERATORS["qro-p3-comparison"] is register_p3.GENERATORS["qro-p3-comparison"]
    assert all(v is None or getattr(v, "__module__", "") != "qro.register_p3" for v in checker.STEPS.values())


@pytest.fixture
def unimportable(monkeypatch):
    """Every qro.p3_* module refused at import, as a tree without them would refuse them."""
    real = builtins.__import__

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):
        names = [name] + [f"{name}.{f}" for f in (fromlist or ())]
        if any(n.startswith("qro.p3_") for n in names) or (name == "qro" and any(
                str(f).startswith("p3_") for f in (fromlist or ()))):
            raise ImportError(f"{name}: P3's modules are made unimportable in this test")
        return real(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, "__import__", guarded)


def test_p0s_fixture_is_accepted_with_p3s_modules_unimportable(tmp_path, unimportable):
    fixture.register()
    checker.load()
    md = checker.check(fixture.make(tmp_path / "crate"))
    assert md["@graph"][1]["qro:generator"] == fixture.GENERATOR


def test_a_comparison_crate_whose_generator_cannot_load_is_refused_by_step_9_never_accepted(tmp_path, monkeypatch):
    t = plants_p1.twin_crate(tmp_path / "t")
    out = plants_p3.hand_written(tmp_path / "comparison", plants_p3.declaration(t, t), plants_p3.PLACEHOLDER)
    checker.load()
    real = builtins.__import__

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "qro" and "p3_record" in (fromlist or ()):
            raise ImportError("qro.p3_record is made unimportable in this test")
        return real(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, "__import__", guarded)
    with pytest.raises(Refused) as r:
        checker.check(out)
    assert (r.value.name, r.value.where) == ("metadata-generated", "./ qro:generator")
