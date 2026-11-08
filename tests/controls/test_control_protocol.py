"""The controls' runner's protocol for P3's and P5's rows (P0.10; FORMAT.md item 24; controls/registry.py's docstring):
  - a plant that raises `Refused` makes that refusal the control's outcome, judged by its name;
  - a plant that returns a `Compared` has the comparison check's outcome, judged by name, and `step-unbuilt` while
    P3's module is missing (made missing here, so the test holds after P3's module lands);
  - a `states` row is met when its sentence is in its plant's STATEMENTS set and its TWINS entry's crate is accepted
    without saying it; a built `states` row with either entry missing is pending, never WRONG and never counted;
  - joint-omission is refused `comparison-generated`;
  - P4's walk of accepted plants still skips a tuple, a `Compared` among them.
Each case is a stand-in control and plant put in place only inside its test, so no parcel's real plant meets them."""
import importlib
import importlib.util
import sys
import types
from pathlib import Path

import pytest

from controls import registry as R
from controls import run
from controls.plant import main as plant_main
from qro import __main__ as cli
from qro.refusal import Refused

ROOT = Path(__file__).resolve().parents[2]
SAID = "a sentence the plant says"


@pytest.fixture
def stand_ins(monkeypatch):
    """Replaces the runner's table by the stand-in rows added so far (a run of the whole table builds every parcel's
    twin, and is held by test_control_registry); returns the function that adds one."""
    added = []

    def add(control):
        added.append(control)
        monkeypatch.setattr(run, "CONTROLS", tuple(added))
        monkeypatch.setattr(run, "CONTROL", {**R.CONTROL, **{c.name: c for c in added}})
        return control
    return add


@pytest.fixture
def no_p3(monkeypatch):
    monkeypatch.delitem(sys.modules, cli.COMPARE, raising=False)
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda name, *a: None if name == cli.COMPARE else real(name, *a))


class Summary:
    def __init__(self, line):
        self.line = line

    def __str__(self):
        return self.line


def p3_stand_in(monkeypatch, check):
    module = types.ModuleType(cli.COMPARE)
    module.check = check
    monkeypatch.setitem(sys.modules, cli.COMPARE, module)


# -- a plant's own refusal -----------------------------------------------------------------------------------------
def kit_dirty(d):
    raise Refused("kit-dirty", "the tree", "a tracked file differs from HEAD")


def test_a_plants_own_refusal_is_the_controls_outcome():
    assert run.outcome("kit-dirty", {"kit-dirty": kit_dirty}) == ("refused", "kit-dirty",
                                                                  "the tree: a tracked file differs from HEAD")


def test_a_plants_own_refusal_is_judged_by_its_name(stand_ins, capsys):
    stand_ins(R.Control("zz-kit", "a dirty tree", "refused", "kit-dirty", "P5", "`kit-dirty`"))
    assert run.main({"zz-kit": kit_dirty}, {}, {}) == 0
    assert "ok        zz-kit                 refused kit-dirty at the tree: a tracked file differs from HEAD" in \
        capsys.readouterr().out
    stand_ins(R.Control("zz-kit2", "a dirty tree", "refused", "kit-dirty", "P5", "`kit-dirty`"))

    def wrong_name(d):
        raise Refused("key-leak", "the tree", "a refusal by another name proves nothing about the fault planted")
    assert run.main({"zz-kit": kit_dirty, "zz-kit2": wrong_name}, {}, {}) == 1
    out = capsys.readouterr().out
    assert "WRONG     zz-kit2" in out and "refused key-leak at the tree" in out and "section 11 says `kit-dirty`" in out


def test_a_plants_own_refusal_is_a_refusal_by_the_plant_command_too(capfd, monkeypatch):
    monkeypatch.setattr("controls.plant.plants", lambda: {"zz-kit": kit_dirty})
    assert plant_main(["zz-kit"]) == 1
    assert capfd.readouterr().out == "REFUSED kit-dirty at the tree: a tracked file differs from HEAD\n"


# -- a comparison's plant -------------------------------------------------------------------------------------------
def compared(d):
    dirs = [Path(d) / n for n in ("comparison", "a", "b")]
    for each in dirs:
        each.mkdir()
    return R.Compared(str(dirs[0]), (str(dirs[1]), str(dirs[2])))


def test_a_compared_is_a_named_tuple_of_the_comparison_and_its_crates():
    c = R.Compared("c", ("a", "b"))
    assert isinstance(c, tuple) and (c.comparison_dir, c.crate_dirs) == ("c", ("a", "b"))


def test_a_compared_is_step_unbuilt_while_p3s_module_is_missing(no_p3):
    got = run.outcome("zz", {"zz": compared})
    assert got[:2] == ("refused", "step-unbuilt") and got[2].startswith("comparison: the comparison check, ")


def test_a_compared_plant_through_the_plant_command_is_the_commands_refusal(no_p3, capfd, monkeypatch):
    monkeypatch.setattr("controls.plant.plants", lambda: {"zz": compared})
    assert plant_main(["zz"]) == 1
    assert capfd.readouterr().out.startswith("REFUSED step-unbuilt at comparison: ")


def test_a_compared_has_the_comparison_checks_outcome_judged_by_name(monkeypatch, stand_ins, capsys):
    seen = []

    def check(comparison_dir, crate_dirs):
        seen.append((Path(comparison_dir).name, [Path(c).name for c in crate_dirs]))
        raise Refused("comparison-trivial", "crate 1: ./", "the two runs share a job of a measured role")
    p3_stand_in(monkeypatch, check)
    assert run.outcome("zz", {"zz": compared}) == ("refused", "comparison-trivial",
                                                   "crate 1: ./: the two runs share a job of a measured role")
    assert seen == [("comparison", ["a", "b"])], "the comparison and its crates, in order"
    stand_ins(R.Control("zz-trivial", "a run against itself", "refused", "comparison-trivial", "P3", "x"))
    assert run.main({"zz-trivial": compared}, {}, {}) == 0
    assert "ok        zz-trivial" in capsys.readouterr().out


def test_a_compared_row_comes_out_wrong_while_p3s_module_is_missing(no_p3, stand_ins, capsys):
    """The two-way walk's stand-in that fails the new outcome: a row that expects P3's refusal, run before P3's module
    exists, is WRONG with `step-unbuilt`, never ok and never silently pending."""
    stand_ins(R.Control("zz-trivial", "a run against itself", "refused", "comparison-trivial", "P3", "x"))
    assert run.main({"zz-trivial": compared}, {}, {}) == 1
    assert "WRONG     zz-trivial             refused step-unbuilt at comparison: " in capsys.readouterr().out


def test_a_compared_that_the_check_accepts_is_accepted(monkeypatch):
    p3_stand_in(monkeypatch, lambda cd, crates: Summary("ACCEPTED comparison x"))
    assert run.outcome("zz", {"zz": compared}) == ("accepted", None, "")


def test_a_compared_is_told_before_the_custody_branch(monkeypatch):
    """It is a pair, so the custody branch would unpack it as (log, record) and check the directories as bytes."""
    p3_stand_in(monkeypatch, lambda cd, crates: Summary("ACCEPTED comparison x"))
    assert len(R.Compared("c", ("a",))) == 2
    assert run.outcome("zz", {"zz": compared})[0] == "accepted"
    assert run.outcome("zz", {"zz": lambda d: (b"", None)}) == ("accepted", None, "")     # a custody pair still is


def test_a_compared_that_breaks_the_modules_contract_fails_the_run_never_an_acceptance(monkeypatch):
    p3_stand_in(monkeypatch, lambda cd, crates: "nothing")
    with pytest.raises(RuntimeError, match="no ACCEPTED line"):
        run.outcome("zz", {"zz": compared})


# -- `states` rows ------------------------------------------------------------------------------------------------
STATES = R.Control("zz-states", "a fault the record states", "states", None, "P3", f'"{SAID}"')


class Said:
    """The crates the stand-in plant made: its STATEMENTS entry says SAID of those, and not of its twin."""
    made = set()


def plant(d):
    crate = R.twin(d)
    Said.made.add(str(crate))
    return crate


def twin(d):
    return R.twin(d)


def says(planted):
    return frozenset({SAID}) if str(planted) in Said.made else frozenset()


def met(stand_ins):
    stand_ins(STATES)
    return {"zz-states": plant}, {"zz-states": says}, {"zz-states": twin}


def test_a_states_row_is_met_when_the_plant_says_it_and_the_twin_does_not(stand_ins, capsys):
    every, statements, twins = met(stand_ins)
    assert run.outcome("zz-states", every, statements, twins) == ("states", None, "")
    assert run.main(every, statements, twins) == 0
    out = capsys.readouterr().out
    assert "ok        zz-states              states\n" in out


def test_a_states_row_whose_plant_does_not_say_it_is_wrong(stand_ins, capsys):
    every, _, twins = met(stand_ins)
    got = run.outcome("zz-states", every, {"zz-states": lambda planted: frozenset({"another"})}, twins)
    assert got == ("accepted", None, f"its plant does not say {SAID!r}")
    assert run.main(every, {"zz-states": lambda planted: frozenset()}, twins) == 1
    assert "WRONG     zz-states" in capsys.readouterr().out


def test_a_states_row_whose_twin_says_it_too_is_not_met(stand_ins):
    every, _, twins = met(stand_ins)
    got = run.outcome("zz-states", every, {"zz-states": lambda planted: frozenset({SAID})}, twins)
    assert got == ("twin-states", None, f"its twin says {SAID!r} too")


def test_a_states_row_whose_twin_is_refused_is_not_met(stand_ins):
    every, statements, _ = met(stand_ins)

    def bad_twin(d):
        crate = R.twin(d)
        (crate / "data" / "notes.txt").write_bytes(b"changed\n")
        return crate
    got = run.outcome("zz-states", every, statements, {"zz-states": bad_twin})
    assert got[:2] == ("twin-refused", "file-digest")


def test_a_states_row_is_met_only_with_the_sentence_in_a_set_not_a_string(stand_ins):
    every, _, twins = met(stand_ins)
    with pytest.raises(TypeError, match="not a set of sentences"):
        run.outcome("zz-states", every, {"zz-states": lambda planted: SAID}, twins)


@pytest.mark.parametrize("missing, why", [("statements", "STATEMENTS"), ("twins", "TWINS")])
def test_a_built_states_row_missing_either_entry_is_pending_never_wrong_and_never_counted(stand_ins, capsys, missing,
                                                                                         why):
    every, statements, twins = met(stand_ins)
    if missing == "statements":
        statements = {}
    else:
        twins = {}
    code = run.main(every, statements, twins)
    lines = capsys.readouterr().out.splitlines()
    pending = next(x for x in lines if x.startswith("pending   zz-states"))
    assert code == 0 and why in pending and f'"{SAID}"' in pending and not any("WRONG     zz-states" in x for x in lines)
    assert lines[-1] == "0 of 0 built controls came out as section 11 says; 1 pending other parcels", lines[-1]


def test_the_counts_of_a_run_count_a_met_states_row_as_built(stand_ins, capsys):
    every, statements, twins = met(stand_ins)
    assert run.main(every, statements, twins) == 0
    assert capsys.readouterr().out.splitlines()[-1] == (
        "1 of 1 built controls came out as section 11 says; 0 pending other parcels")


def test_the_registry_row_a_states_plant_without_a_registry_row_is_not_judged(capsys):
    """outcome() reads the registry's own row for the name: a plant naming none is the generator's refusal, and here
    comes out as an acceptance, not a states row."""
    assert run.outcome("zz", {"zz": R.twin}) == ("accepted", None, "")


# -- the registry's tables of statements and twins ------------------------------------------------------------------
def test_statements_and_twins_are_merged_from_the_plants_modules_and_a_row_given_twice_is_refused():
    one = types.SimpleNamespace(__name__="controls.plants_zz", STATEMENTS={"a": 1}, TWINS={"a": 2})
    two = types.SimpleNamespace(__name__="controls.plants_zz2")
    assert R.merged_table([one, two], "STATEMENTS") == {"a": 1} and R.merged_table([one, two], "TWINS") == {"a": 2}
    clash = types.SimpleNamespace(__name__="controls.plants_zz3", STATEMENTS={"a": 3})
    with pytest.raises(R.PlantClash, match="gives STATEMENTS for"):
        R.merged_table([one, clash], "STATEMENTS")


def test_no_module_of_the_tree_gives_a_statement_or_twin_for_a_row_that_is_not_a_states_row():
    from tools import gen_vocabulary
    assert [p for p in gen_vocabulary.problems() if "STATEMENTS" in p or "TWINS" in p] == []


def test_the_generator_refuses_a_statement_or_twin_for_a_row_that_is_not_a_states_row(monkeypatch):
    from tools import gen_vocabulary
    monkeypatch.setattr(gen_vocabulary.C, "statements", lambda: {"shot-moved": 1, "single-runs": 2, "no-such-row": 3})
    monkeypatch.setattr(gen_vocabulary.C, "twins", lambda: {"count-unpaid": 1})
    assert [p for p in gen_vocabulary.problems() if "names no `states` control" in p] == [
        "STATEMENTS entry shot-moved names no `states` control", "STATEMENTS entry no-such-row names no `states` control",
        "TWINS entry count-unpaid names no `states` control"]


# -- the third need: P4's walk of accepted plants --------------------------------------------------------------------
def test_p4s_walk_of_accepted_plants_still_skips_a_tuple_a_compared_among_them(monkeypatch):
    """Changing nothing of P4's: its walk skips a planted thing that is a tuple, and a Compared is one."""
    monkeypatch.syspath_prepend(str(ROOT / "tests" / "p4"))
    import p4_helpers as H
    from qro import fixture, p4_shapes
    accepted = R.Control("zz-accepted", "an honest crate", "accepted", None, "P9", "accepted")
    shared = R.Control("zz-shared", "a comparison both runs accepted", "accepted", None, "P3", "accepted")
    made = {"zz-accepted": lambda d: fixture.make(Path(d) / "honest"), "zz-shared": compared}
    problems, examined = H.accepted_control_problems(p4_shapes.build(), controls=(accepted, shared), plants=made)
    assert problems == [] and examined == 1, "the crate is examined; the Compared, a tuple, is skipped"
    problems, examined = H.accepted_control_problems(p4_shapes.build(), controls=(shared,),
                                                     plants={"zz-shared": compared})
    assert (problems, examined) == ([], 0)


# -- the registry's joint-omission ---------------------------------------------------------------------------------
def test_joint_omission_is_judged_by_comparison_generated(monkeypatch):
    c = R.CONTROL["joint-omission"]
    assert (c.expected, c.refusal) == ("refused", "comparison-generated")

    def record_differs(d):
        raise Refused("comparison-generated", "comparison/record.json line 3 column 9", "not what the declaration gives")

    def wrong_name(d):
        raise Refused("measure-class", "x", "a refusal by another name")
    assert run.outcome("joint-omission", {"joint-omission": record_differs})[:2] == ("refused", "comparison-generated")
    assert run.outcome("joint-omission", {"joint-omission": wrong_name})[:2] != ("refused", "comparison-generated")
