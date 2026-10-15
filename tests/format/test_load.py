"""checker.load(): each parcel's declarations merged into the checker's registries, and the command line and the
controls' run loading them before they check a crate (P0.1, after its verifier's round 1, D3: nothing registered a
parcel's step for a real crate). Each parcel's module is written here as a file a parcel would write, and found as
the checker finds one, under a name of the test's own; the registries are restored after each test."""
import importlib
import itertools
import json
import sys
from pathlib import Path

import pytest

from qro import canonical, checker, fixture
from qro.__main__ import main

NL = chr(10)
FRESH = itertools.count()
RAW = "data/raw.counts.json"
SOURCE = NL.join([
    "from qro.refusal import Refused", "", "",
    "def step4(crate_dir, md):",
    "    raise Refused('commitment', 'data/raw.counts.json', 'the provider echoed another')", "", "",
    "def form(data):", "    return 0", "", "",
    "def rule(crate_dir, md):", "    pass", "", "",
    "def generate(crate_dir):", "    return {}", "", "",
    "STEPS = {4: step4}",
    "RAW_FORMS = {'zz-form': form}",
    "COUNTS = [rule]",
    "GENERATORS = {'zz-generator': generate}", ""])


@pytest.fixture
def parcels(tmp_path, monkeypatch):
    """write(parcel, source): that parcel's registration module, as a file on a fresh path under a fresh name, which
    it returns. The registries start unbuilt, whatever an earlier test in the process loaded: once a parcel's real
    module exists, the command line's tests load it."""
    monkeypatch.setattr(checker, "STEPS", {n: None for n in range(4, 9)})
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    monkeypatch.setattr(checker, "GENERATORS", {})
    monkeypatch.setattr(checker, "COUNTS", [])
    where = tmp_path / "modules"
    where.mkdir()
    monkeypatch.syspath_prepend(str(where))
    prefix = f"zz_register_{next(FRESH)}_"
    monkeypatch.setattr(checker, "registration", lambda parcel: prefix + parcel.lower())

    def write(parcel, source):
        (where / f"{prefix}{parcel.lower()}.py").write_text(source, encoding="utf-8")
        importlib.invalidate_caches()
        return prefix + parcel.lower()
    yield write
    for k in [k for k in sys.modules if k.startswith(prefix)]:
        del sys.modules[k]


def committed(d):
    """The fixture, its raw result carrying a step-4 term: refused `step-unbuilt` unless step 4 is registered."""
    c = fixture.make(Path(d) / "crate")
    p = c / canonical.DESCRIPTOR
    md = json.loads(p.read_bytes())
    next(e for e in md["@graph"] if e["@id"] == RAW)["qro:commitment"] = "a" * 64
    p.write_bytes(canonical.dumps(md))
    return c


def test_a_parcels_module_is_qro_register_and_its_name():
    """The name FORMAT.md item 20 and CLAUDE.md give a parcel."""
    assert [checker.registration(p) for p in ("P1", "P2", "P5")] == ["qro.register_p1", "qro.register_p2",
                                                                     "qro.register_p5"]


def test_the_fixtures_names_are_the_ones_no_parcel_may_register():
    assert fixture.RAW_FORM.startswith(checker.FIXTURE_NAMES) and fixture.GENERATOR.startswith(checker.FIXTURE_NAMES)


def test_with_no_parcel_module_nothing_is_loaded(parcels):
    before = (dict(checker.STEPS), dict(checker.RAW_FORMS), list(checker.COUNTS), dict(checker.GENERATORS))
    checker.load()
    assert (checker.STEPS, checker.RAW_FORMS, checker.COUNTS, checker.GENERATORS) == before


def test_a_parcels_declarations_are_merged_and_loading_again_changes_nothing(parcels):
    parcels("P1", SOURCE)
    checker.load()
    step, rules = checker.STEPS[4], len(checker.COUNTS)
    assert (step.__name__, checker.RAW_FORMS["zz-form"].__name__, checker.GENERATORS["zz-generator"].__name__,
            checker.COUNTS[-1].__name__) == ("step4", "form", "generate", "rule")
    checker.load()
    assert checker.STEPS[4] is step and len(checker.COUNTS) == rules


def test_two_parcels_rules_of_one_name_are_both_kept(parcels):
    """P0.1's verifier, round 2, 4.1.6: rules are told apart by what they are, never by their names."""
    parcels("P1", NL.join(["def rule(crate_dir, md):", "    pass", "", "", "COUNTS = [rule]", ""]))
    parcels("P2", NL.join(["def rule(crate_dir, md):", "    pass", "", "", "COUNTS = [rule]", ""]))
    checker.load()
    assert [r.__name__ for r in checker.COUNTS] == ["rule", "rule"] and checker.COUNTS[0] is not checker.COUNTS[1]


@pytest.mark.parametrize("parcel, step, owner", [("P2", 4, "P1"), ("P1", 6, "P2"), ("P1", 3, "P0"), ("P1", 9, "P0"),
                                                 ("P3", 5, "P1"), ("P1", 10, "no parcel")])
def test_a_step_another_parcel_owns_is_refused(parcels, parcel, step, owner):
    parcels(parcel, f"STEPS = {{{step}: print}}" + NL)
    with pytest.raises(checker.RegistrationError, match=f"registers step {step}, which is {owner}'s"):
        checker.load()


def test_a_name_another_function_holds_is_refused(parcels):
    checker.RAW_FORMS["zz-held"] = len
    parcels("P1", "RAW_FORMS = {'zz-held': print}" + NL)
    with pytest.raises(checker.RegistrationError, match="registers zz-held, which another function already holds"):
        checker.load()


def test_two_parcels_registering_one_name_are_refused_at_the_later(parcels):
    """Parcels load in the vocabulary's order, so the later one is named (P0.1's verifier, round 2, 4.1.6)."""
    parcels("P1", "GENERATORS = {'zz-generator': print}" + NL)
    later = parcels("P2", "GENERATORS = {'zz-generator': len}" + NL)
    with pytest.raises(checker.RegistrationError, match=f"^{later} registers zz-generator, which another function"):
        checker.load()


@pytest.mark.parametrize("declared", ["RAW_FORMS = {fixture.RAW_FORM: fixture.read_counts}",
                                      "GENERATORS = {fixture.GENERATOR: fixture.generate}"],
                         ids=["the fixture's raw form", "the fixture's generator"])
def test_a_name_of_the_fixtures_is_refused_with_or_without_fixtures(parcels, declared):
    """P0.1's verifier, round 2, 4.3.2: registered with the fixture's own functions, they made the plain command
    line accept the fixture."""
    parcels("P1", "from qro import fixture" + NL + declared + NL)
    with pytest.raises(checker.RegistrationError, match="a name of P0's fixture"):
        checker.load()


@pytest.mark.parametrize("change", ["checker.STEPS[4] = print", "checker.RAW_FORMS['zz-direct'] = print",
                                    "checker.COUNTS.append(print)", "checker.GENERATORS['zz-direct'] = print"],
                         ids=["a step", "a raw form", "a count rule", "a generator"])
def test_a_module_that_changes_the_registries_itself_is_refused(parcels, change):
    """P0.1's verifier, round 2, 4.3.1: set directly, a second parcel's step 4 replaced the first's in silence. Each
    registry is held, each changed in place (round 3, note 9)."""
    parcels("P2", "from qro import checker" + NL + change + NL)
    with pytest.raises(checker.RegistrationError, match="changes the checker's registries itself"):
        checker.load()


def test_a_name_near_the_fixtures_is_a_parcels_to_register(parcels):
    """The fixture's prefix is exactly qro-fixture (round 3, note 10): a name short of it is not the fixture's."""
    parcels("P1", "RAW_FORMS = {'qro-fixtur': print, 'qro-fix': len}" + NL)
    checker.load()
    assert set(checker.RAW_FORMS) == {"qro-fixtur", "qro-fix"}


def test_a_module_that_will_not_load_carries_its_own_error_as_the_cause(parcels):
    """Round 3, note 10: the RegistrationError keeps the module's own error, for whoever reads the traceback."""
    parcels("P1", "raise RuntimeError('its own')" + NL)
    with pytest.raises(checker.RegistrationError) as r:
        checker.load()
    assert isinstance(r.value.__cause__, RuntimeError) and str(r.value.__cause__) == "its own"


def test_the_command_line_loads_every_parcel_before_it_checks(parcels, tmp_path, capfd):
    """Unloaded, the crate is refused step-unbuilt; loaded, by the parcel's own step."""
    c = committed(tmp_path)
    assert main(["check", "--fixtures", str(c)]) == 1
    assert capfd.readouterr().out.startswith("REFUSED step-unbuilt at data/raw.counts.json qro:commitment")
    parcels("P1", SOURCE)
    assert main(["check", "--fixtures", str(c)]) == 1
    assert capfd.readouterr().out == "REFUSED commitment at data/raw.counts.json: the provider echoed another" + NL


LOAD_FAILURES = [
    ("P1", "raise RuntimeError('a parcel that will not import')" + NL, "RuntimeError: a parcel that will not import"),
    ("P1", "from qro.refusal import Refused" + NL + "raise Refused('commitment', 'x', 'y')" + NL,
     "cannot be loaded: Refused"),
    ("P1", "raise PermissionError(13, 'denied', 'some-file')" + NL, "cannot be loaded: PermissionError"),
    ("P1", "STEPS = [print]" + NL, "cannot be loaded: AttributeError"),
    ("P2", "STEPS = {4: print}" + NL, "registers step 4, which is P1's"),
    ("P1", "import sys" + NL + "sys.exit(0)" + NL, "SystemExit"),
    ("P1", NL.join(["from qro.refusal import Refused", "", "", "class Hostile(Exception):",
                    "    def __str__(self):", "        raise Refused('commitment', 'x', 'y')", "", "",
                    "raise Hostile()", ""]), "cannot be loaded: Hostile, whose text cannot be read"),
    ("P1", NL.join(["class Hostile(Exception):", "    def __str__(self):",
                    "        raise PermissionError(13, 'denied', 'some-file')", "", "", "raise Hostile()", ""]),
     "cannot be loaded: Hostile, whose text cannot be read")]


@pytest.mark.parametrize("parcel, source, failure", LOAD_FAILURES,
                         ids=["an error at import", "a refusal at import", "a want of permission at import",
                              "a declaration of the wrong kind", "a step not its parcel's", "an exit at import",
                              "an error whose text refuses", "an error whose text wants permission"])
def test_a_parcel_module_that_fails_to_load_is_the_checker_failing(parcels, tmp_path, capfd, parcel, source,
                                                                    failure):
    """P0.1's verifier, round 2, R2-3: a refusal raised at import was exit 1, a verdict on a crate never read, and a
    want of permission exit 2. Every way a module fails to load is exit 3, with or without --fixtures."""
    c = fixture.make(tmp_path / "crate")
    parcels(parcel, source)
    for argv in (["check", "--fixtures", str(c)], ["check", str(c)]):
        assert main(argv) == 3, argv
        err = capfd.readouterr().err
        assert err.startswith("FAILED: the checker itself failed, ") and failure in err and "not a verdict" in err


def test_a_step_raising_an_error_whose_text_refuses_is_the_checker_failing(parcels, tmp_path, capfd):
    """P0.1's verifier, round 3, C1, at check time: the command line's own catch-all wrote the text unguarded."""
    parcels("P1", NL.join(["from qro.refusal import Refused", "", "", "class Hostile(Exception):",
                           "    def __str__(self):", "        raise Refused('commitment', 'x', 'y')", "", "",
                           "def step4(crate_dir, md):", "    raise Hostile()", "", "", "STEPS = {4: step4}", ""]))
    assert main(["check", "--fixtures", str(committed(tmp_path))]) == 3
    assert capfd.readouterr().err.startswith("FAILED: the checker itself failed, Hostile, whose text cannot be read")


def test_a_refusal_whose_line_cannot_be_written_is_the_checker_failing(parcels, tmp_path, capfd):
    """A refusal is answered as one only when its line can be written: one whose detail was changed, after it was
    made, to a thing with no text."""
    parcels("P1", NL.join(["from qro.refusal import Refused", "", "", "class Detail:", "    def __format__(self, spec):",
                           "        raise ValueError('no text')", "", "",
                           "def step4(crate_dir, md):", "    r = Refused('commitment', 'x', 'y')", "    r.detail = Detail()",
                           "    raise r", "", "", "STEPS = {4: step4}", ""]))
    assert main(["check", "--fixtures", str(committed(tmp_path))]) == 3
    assert capfd.readouterr().err.startswith("FAILED: the checker itself failed, ValueError: no text")


@pytest.mark.parametrize("source", ["import sys" + NL + "sys.exit(0)" + NL, "raise RuntimeError('no')" + NL],
                         ids=["an exit 0", "an error"])
def test_the_controls_run_answers_a_module_that_will_not_load_as_its_own_failure(parcels, source, capsys):
    """P0.1's verifier, round 3, note 1: a module's SystemExit(0) ended the run with exit 0 and no output."""
    from controls import run
    parcels("P1", source)
    assert run.run() == 3
    assert capsys.readouterr().out.startswith("FAILED: the controls' run itself failed, ")


def test_the_controls_run_loads_every_parcel_too(parcels, tmp_path):
    from controls.run import outcome
    every = {"zz-committed": committed}
    assert outcome("zz-committed", every)[:2] == ("refused", "step-unbuilt")
    parcels("P1", SOURCE)
    assert outcome("zz-committed", every)[:2] == ("refused", "commitment")
