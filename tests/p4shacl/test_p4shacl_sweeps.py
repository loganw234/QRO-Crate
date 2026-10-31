"""The sweeps whose cost does not fit the quick stage, and the alias-key crates through a real engine (P4's verifier, round 1,
defects 2 and 3). The first two need no engine; they are here because this stage is where a run of some minutes is paid for,
and the quick stage's tests/p4/test_p4_sweeps.py and test_p4_profile_crate.py hold the same properties over a sample.

  - every single edit of the fixture the verifier's pool makes (12,591: about 12 s): when a must shape fails the checker
    refuses the crate, by a name a failing shape claims; and the 1,088 the expansion cannot read are each refused by the
    checker too (steps 1 to 3), none left out unseen;
  - the 124 alias-key crates, through pyshacl: the engine fails the shapes the evaluator fails, and the claims hold (the second
    verifier's three families go through it too, in test_p4shacl_families.py);
  - 20,000 random edits of the Profile Crate, and of the files beside it, into its check: it raises on none and never needs
    its safety net (about 13 s)."""
import pytest
from p4shacl_helpers import quick_stage_module, run_engine, shape_files
from qro import canonical, fixture, checker
from qro import p4_examples as X
from qro import p4_shapes as H

sweeps = quick_stage_module("p4_sweeps")
fuzz = quick_stage_module("p4_pcfuzz")
SHAPES = H.build()


@pytest.fixture(scope="module")
def work():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(checker, "STEPS", {n: None for n in range(4, 9)})
        mp.setattr(checker, "RAW_FORMS", {})
        mp.setattr(checker, "COUNTS", [])
        mp.setattr(checker, "GENERATORS", {})
        fixture.register()
        checker.load()
        with X.Workspace(SHAPES) as w:
            yield w


def test_every_single_edit_of_the_pool_is_refused_by_a_name_a_failing_shape_claims(work):
    r = sweeps.sweep(work, SHAPES)
    assert r["A"] == [] and r["B"] == {} and r["U"] == [], (r["A"][:3], list(r["B"].items())[:3], r["U"][:3])
    assert r["n"] == 12591 and r["unreadable"] == 1088 and r["held"] >= 10000 and len(r["failing"]) >= 120


def test_the_engine_fails_the_shapes_the_evaluator_fails_on_every_alias_key_crate_and_the_claims_hold(work):
    crates = sweeps.alias_crates(work)
    jobs = [{"id": name, "kind": "crate", "metadata": canonical.dumps(md).decode("ascii"), "shapes": shape_files()}
            for name, (_, _, md) in crates.items()]
    answers, _ = run_engine(jobs, timeout=900)
    claims = {X.local(s.id): s.claims for s in SHAPES}
    wrong = []
    for name, (term, alias, md) in crates.items():
        must, _, why = X.shapes_verdict(md, SHAPES)
        got = answers[name]
        failing = sorted({r["shape"].split("#", 1)[1] for r in got["results"] if r["severity"] == "Violation"}) if got["ok"] else None
        if why or failing != list(must):
            wrong.append((name, alias, why[:40], failing, list(must)))
        elif must and sweeps.early(work, md) not in {c for s in must for c in claims[s]}:
            wrong.append((name, alias, "claims", list(must)))
    assert wrong == []
    assert len(crates) == 124


def test_the_check_raises_on_nothing_and_never_needs_its_net_over_20000_random_edits():
    r = fuzz.run(20000, seed=3)
    assert r["raised"] == {} and r["net"] == 0 and r["not_problems"] == 0, r
    assert r["clean"] + r["refused"] == 20000 and r["refused"] > 12000 and r["clean"] > 1000
    assert r["raw"] >= 400 and r["files"] >= 2000 and r["edited"] >= 30000
