"""v0's real cases of four of P3's controls (P3's design, items 9 and 15; the brief's item 3): `single-runs`, each
device's morning law job alone; `time-confounded`, kingston against fez, every job in its device's own block;
`readout-unbounded`, the two coherences, no control covering qubits 0 and 1 both ways; and `simulator-in-real`, Atlas's
crate against the IBM crate, the question declared varied and the comparison real, refused `kind-not-qpu` by the
command as a process, with its twin, the same declared a rehearsal, accepted. And IBM against Atlas with the question
fixed is refused `question-differs` by the decode rule, as the study's section 8 says."""
import json

import pytest

import p3crates_support as S
from controls import plants_p3
from controls import registry as R
from qro import p3_compare, p3_declaration
from qro import vocabulary as V
from qro.refusal import Refused

K, F = "ibm_kingston", "ibm_fez"
LAW = ("forbidden-share", "linear-xeb", "n-crystal-share")
SAYS = V.WORDS["statement"]


def morning(device):
    """A device's morning bundle of the IBM crate: its manifest's digest, which its morning lines hold."""
    _, md, _ = S.checked("ibm")
    rel = f"2026-10-05/ibm/{device}/bundle/manifest.json"
    return {"bundles": [next(e["sha256"] for e in md["@graph"] if e["@id"] == rel)], "device": device}


def test_single_runs_each_devices_morning_law_job_alone_says_drift_unmeasured():
    _, record = S.comparison(morning(K), morning(F), measures=LAW)
    sentence = R.sentence(R.CONTROL["single-runs"])
    assert sentence == SAYS["drift-unmeasured"]
    for name in LAW:
        m = S.measure(record, name)
        assert (len(m["a"]["members"]), len(m["b"]["members"])) == (1, 1)
        assert "drift-unmeasured" in m["statements"] and m["causes"]["drift"] == "UNMEASURED", name
        assert m["strongForm"] == "none"
    jobs = record["runs"]["a"]["crates"][0]["jobs"]
    assert len(jobs) == 3, "the morning bundle's known answer, law and coherence jobs"


def test_single_runs_twin_the_day_of_law_jobs_does_not_say_it():
    _, record = S.comparison(S.device(K), S.device(F), measures=LAW)
    assert all("drift-unmeasured" not in S.measure(record, m)["statements"] for m in LAW)


def test_time_confounded_kingston_against_fez_says_the_difference_is_the_devices_and_its_times():
    _, record = S.comparison(S.device(K), S.device(F))
    assert R.sentence(R.CONTROL["time-confounded"]) == SAYS["device-and-time"]
    for m in record["measures"]:
        assert "device-and-time" in m["statements"] and "device-alone" not in m["statements"], m["measure"]


def test_readout_unbounded_the_coherences_say_readouts_effect_unbounded():
    _, record = S.comparison(S.device(K), S.device(F))
    assert R.sentence(R.CONTROL["readout-unbounded"]) == SAYS["readout-unbounded"]
    for name in ("x0x1", "y0y1"):
        m = S.measure(record, name)
        assert m["readout"] == {"bound": "none", "status": "UNMEASURED"} and "readout-unbounded" in m["statements"]


def atlas_against_ibm(tmp_path, kind):
    """The comparison crate of Atlas's law jobs against kingston's, the question varied, written by hand (make refuses
    the real one): (its directory, the two crates' directories)."""
    _, _, atlas = S.checked("atlas")
    _, _, ibm = S.checked("ibm")
    plan = p3_declaration.plan({m: "0/1" for m in LAW}, {"a": S.device("moth-atlas-emu"), "b": S.device(K)},
                               kind=kind, question="varied")
    data = p3_declaration.write({"a": [atlas], "b": [ibm]}, plan)
    out = plants_p3.hand_written(tmp_path / "comparison", data, plants_p3.PLACEHOLDER)
    return out, S.built("atlas"), S.built("ibm")


def test_simulator_in_real_is_refused_kind_not_qpu_by_the_command_as_a_process(tmp_path):
    out, atlas, ibm = atlas_against_ibm(tmp_path, "real")
    p = S.process(["compare", str(out), str(atlas), str(ibm)], module="qro")
    assert (p.returncode, p.stderr) == (1, ""), (S.mask(p.stdout[-300:]), S.mask(p.stderr[-300:]))
    assert p.stdout.startswith("REFUSED kind-not-qpu at run a ") and p.stdout.count("\n") == 1
    assert "its device moth-atlas-emu is of the kind simulator, not qpu" in p.stdout


def test_its_twin_the_same_declared_a_rehearsal_is_computed_and_says_so():
    _, record = S.comparison(S.device("moth-atlas-emu"), S.device(K), kind_a="atlas", measures=LAW,
                             kind="rehearsal", question="varied")
    assert record["kind"] == "rehearsal" and record["runs"]["a"]["kinds"] == ["simulator"]
    for name in LAW:
        m = S.measure(record, name)
        assert m["causes"]["question"] == "DIFFERS" and m["causes"]["compile"] == "unexposed"
        assert m["causes"]["submitted"] == "unexposed", "Atlas's jobs have no line, so no manifest"
        assert {"question-varied", "compile-unheld", "submitted-differs"} <= set(m["statements"]), "limit 18's two"


def test_ibm_against_atlas_with_the_question_fixed_is_refused_question_differs_by_its_decode_rule(tmp_path,
                                                                                                    monkeypatch):
    with pytest.raises(Refused) as r:
        S.comparison(S.device(K), S.device("moth-atlas-emu"), kind_b="atlas", measures=LAW)
    assert (r.value.name, r.value.where) == ("question-differs", "the question")
    S.fast_checks(monkeypatch)
    plan = p3_declaration.plan({m: "0/1" for m in LAW}, {"a": S.device(K), "b": S.device("moth-atlas-emu")})
    data = p3_declaration.write({"a": [S.checked("ibm")[2]], "b": [S.checked("atlas")[2]]}, plan)
    out = plants_p3.hand_written(tmp_path / "comparison", data, plants_p3.PLACEHOLDER)
    with pytest.raises(Refused) as again:
        p3_compare.check(out, [S.built("ibm"), S.built("atlas")])
    assert again.value.name == "question-differs"
    record = json.loads((out / "comparison" / "record.json").read_bytes())
    assert record == {"format": "qro-comparison-record/1"}, "the hand-written placeholder: no computation gave it"
