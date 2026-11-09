"""Readout coverage (qro/p3_readout.py; P3's design, item 4, with its correction 3), on the builder's crates: a coherence
measure whose member jobs all have controls covering qubits 0 and 1 prepared 0 and prepared 1, in the job itself or in
the job just before it on its device of the same bundle, is refused `step-unbuilt` at "<measure>: the readout bound"
(its bound is P3.2's); every other is UNMEASURED, `none`, and says readout-unbounded: one known-answer pattern, a
control of another bundle, a control not just before, a control on one run only, one qubit of the pair covered alone, a
tie, and the law measures always."""
import pytest

import p3_builder as B
import p3_support as S
from qro.refusal import Refused

T = "2026-11-01T10:"


def coherence_after(before, minute=0, coherence_minute=None, **kw):
    """Jobs on one device: `before` (a list of factories of a start time) and then the coherence job."""
    out = [make(f"{T}{minute + i:02d}:00Z") for i, make in enumerate(before)]
    out.append(B.coherence(start=f"{T}{coherence_minute if coherence_minute is not None else minute + len(before):02d}:00Z",
                           **kw))
    return out


def ka(start):
    return B.ka(start=start)


def ctl(start):
    return B.control(start=start)


def comp_only(start):
    return B.Job("complement-only", ("complement",), (B.complement_counts(),), start)


def law(start):
    return B.law(start=start)


def outcome(tmp_path, k, f, k_bundles=None, f_bundles=None, measures=("x0x1", "y0y1")):
    """("refused", where) or ("computed", {measure: (readout, its statements)})."""
    bundles = k_bundles or [B.Bundle("ibm_kingston", "morning", k)]
    bundles += f_bundles or [B.Bundle("ibm_fez", "morning", f)]
    crate = B.build(tmp_path, bundles)
    try:
        record, _ = S.computed(crate, crate, measures=measures)
    except Refused as r:
        assert r.name == "step-unbuilt", (r.name, r.where, r.detail)
        return "refused", r.where
    return "computed", {m["measure"]: (m["readout"], m["statements"]) for m in record["measures"]}


UNMEASURED = {"bound": "none", "status": "UNMEASURED"}


def unbounded(got):
    kind, by = got
    return kind == "computed" and all(r == UNMEASURED and "readout-unbounded" in w for r, w in by.values())


def test_one_known_answer_pattern_just_before_leaves_readout_unbounded(tmp_path):
    """P1's twin's case: qubits 0 and 1 are prepared 1 by the known answer, and never 0."""
    assert unbounded(outcome(tmp_path, coherence_after([ka]), coherence_after([ka], 10)))


def test_a_known_answer_and_its_complement_just_before_cover_both_qubits_both_ways(tmp_path):
    assert outcome(tmp_path, coherence_after([ctl]), coherence_after([ctl], 10)) == ("refused", "x0x1: the readout bound")


def test_controls_in_the_job_itself_cover_it(tmp_path):
    def inside(start):
        return B.Job("film", ("known-answer", "complement", "coherence-xx", "coherence-yy"),
                     (B.ka_counts(), B.complement_counts(), B.coherence_counts(), B.coherence_counts()), start)
    assert outcome(tmp_path, [inside(f"{T}00:00Z")], [inside(f"{T}10:00Z")]) == ("refused", "x0x1: the readout bound")


def test_a_known_answer_in_the_job_and_its_complement_just_before_cover_it_together(tmp_path):
    def film(start):
        return B.Job("film", ("known-answer", "coherence-xx", "coherence-yy"),
                     (B.ka_counts(), B.coherence_counts(), B.coherence_counts()), start)
    k = [ka(f"{T}00:00Z"), comp_only(f"{T}01:00Z"), film(f"{T}02:00Z")]
    f = [ka(f"{T}10:00Z"), comp_only(f"{T}11:00Z"), film(f"{T}12:00Z")]
    assert outcome(tmp_path, k, f)[0] == "refused"


def test_a_control_of_another_bundle_just_before_serves_nothing(tmp_path):
    k_bundles = [B.Bundle("ibm_kingston", "controls", [ctl(f"{T}00:00Z")]),
                 B.Bundle("ibm_kingston", "morning", [B.coherence("coherence-k", start=f"{T}02:00Z"),
                                                      ka(f"{T}05:00Z")])]
    f_bundles = [B.Bundle("ibm_fez", "morning", coherence_after([ctl], 10))]
    assert unbounded(outcome(tmp_path, None, None, k_bundles, f_bundles))


def test_a_control_not_just_before_serves_nothing(tmp_path):
    assert unbounded(outcome(tmp_path, coherence_after([ctl, law]), coherence_after([ctl], 10)))


def test_covered_on_one_run_alone_is_not_covered(tmp_path):
    assert unbounded(outcome(tmp_path, coherence_after([ctl]), coherence_after([ka], 10)))


def test_a_complement_alone_prepares_qubits_0_and_1_only_as_0(tmp_path):
    k = [ka(f"{T}00:00Z"), comp_only(f"{T}01:00Z"), B.coherence(start=f"{T}02:00Z")]
    f = [ka(f"{T}10:00Z"), comp_only(f"{T}11:00Z"), B.coherence(start=f"{T}12:00Z")]
    assert unbounded(outcome(tmp_path, k, f))


@pytest.mark.parametrize("pattern", ["without-0", "without-1"])
def test_a_pair_is_covered_only_where_both_its_qubits_are(tmp_path, pattern):
    """The known answer, {0, 1, 3, 7, 12}, just before with a pattern that leaves out one qubit of the pair: that qubit
    is prepared 1 and 0, the other only 1, so the pair is not covered (round 2, item 4: coverage read over one qubit
    alone would call it covered)."""
    def control(start):
        return B.Job("control", ("known-answer", pattern), (B.ka_counts(), B.pattern_counts(pattern)), start)
    assert unbounded(outcome(tmp_path, coherence_after([control]), coherence_after([control], 10)))


def test_a_tie_with_the_job_before_orders_nothing(tmp_path):
    assert unbounded(outcome(tmp_path, coherence_after([ctl], coherence_minute=0), coherence_after([ctl], 10,
                                                                                                   coherence_minute=10)))


def test_law_measures_have_no_readout_model_and_stay_unmeasured_when_the_coherence_is_covered(tmp_path):
    k = coherence_after([ctl]) + [B.law(start=f"{T}20:00Z")]
    f = coherence_after([ctl], 10) + [B.law(start=f"{T}30:00Z")]
    kind, by = outcome(tmp_path, k, f, measures=("n-crystal-share", "forbidden-share"))
    assert kind == "computed" and all(r == UNMEASURED for r, _ in by.values())


@pytest.mark.parametrize("measures", [("y0y1",), ("x0x1",)])
def test_each_coherence_measure_is_refused_by_its_own_name(tmp_path, measures):
    assert outcome(tmp_path, coherence_after([ctl]), coherence_after([ctl], 10), measures=measures) == (
        "refused", f"{measures[0]}: the readout bound")
