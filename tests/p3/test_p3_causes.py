"""The causes, one status a measure, each read from the crates (qro/p3_verdicts.py's `causes`; P3's design, item 5's
table), and each outcome of each on the builder's crates: the compile EQUAL, DIFFERS and held, DIFFERS and not held
(its Compile without a Hold, or a gate list not carried), and `unexposed`; what was submitted EQUAL, DIFFERS by its
options, shots, program, route, kind or decode, and `unexposed`; the producing commit EQUAL, DIFFERS and `unknown`; the
device EQUAL and DIFFERS; drift CONTROLLED and UNMEASURED; sampling CONTROLLED always; isolated from the pipeline where
every one allows; and the unseen factors a date, a known answer or a bit order leaves seen."""
import copy
from fractions import Fraction

import pytest

import p3_builder as B
import p3_support as S
from qro import canonical, p3_compare
from qro import p3_declaration as D

T = "2026-11-01T10:"
COMMIT_A, COMMIT_B = "a" * 40, "b" * 40


def jobs(minute=0, five=48, shots=64, commit="unknown", coherence=True):
    out = [B.ka(start=f"{T}{minute:02d}:00Z", shots=shots, commit=commit),
           B.law("law-0", start=f"{T}{minute + 1:02d}:00Z", five=five, shots=shots, commit=commit),
           B.law("law-1", start=f"{T}{minute + 3:02d}:00Z", five=five - 2, shots=shots, commit=commit)]
    if coherence:
        out.append(B.coherence(start=f"{T}{minute + 40:02d}:00Z", shots=shots, commit=commit))
    return out


def pair(tmp_path, k=None, f=None, **fez):
    return B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", k or jobs()),
                              B.Bundle("ibm_fez", "morning", f or jobs(10), **fez)])


def causes(record, measure="n-crystal-share"):
    return S.measure(record, measure)["causes"]


def statements(record, measure="n-crystal-share"):
    return S.measure(record, measure)["statements"]


def test_one_gate_list_is_equal_and_held(tmp_path):
    crate = pair(tmp_path)
    record, _ = S.computed(crate, crate)
    for m in S.FIVE:
        assert (causes(record, m)["compile"], causes(record, m)["hold"]) == ("EQUAL", "holds"), m
        assert "compile" in S.measure(record, m)["unseen"] and "compile-unheld" not in statements(record, m)


def test_two_gate_lists_each_held_differ_and_are_logically_equivalent(tmp_path):
    crate = pair(tmp_path, gates={"law": 1})
    record, _ = S.computed(crate, crate)
    assert (causes(record)["compile"], causes(record)["hold"]) == ("DIFFERS", "holds")
    assert "compile-unheld" not in statements(record) and "compile" not in S.measure(record, "n-crystal-share")["unseen"]
    assert causes(record, "x0x1")["compile"] == "EQUAL", "fez's coherence gate lists are kingston's"


def test_a_gate_list_no_hold_held_is_not_held(tmp_path):
    crate = pair(tmp_path, gates={"law": 1}, held=False)
    record, _ = S.computed(crate, crate)
    assert (causes(record)["compile"], causes(record)["hold"]) == ("DIFFERS", "withheld")
    assert "compile-unheld" in statements(record)


def test_a_gate_list_the_crate_does_not_carry_is_not_held(tmp_path):
    crate = pair(tmp_path, gates={"law": 1})
    md = S.md_of(crate)
    md["@graph"] = [e for e in md["@graph"] if e["@id"] != "gates/law-variant1.gates.json"]
    d = canonical.body_digest(md)
    plan = D.plan({"n-crystal-share": "0/1"}, {"a": {"device": "ibm_kingston"}, "b": {"device": "ibm_fez"}})
    record, _ = p3_compare.compute(D.read(D.write({"a": [d], "b": [d]}, plan)), None, {d: (crate, md)})
    assert (causes(record)["compile"], causes(record)["hold"]) == ("DIFFERS", "withheld")


def test_a_compile_whose_hold_is_taken_out_is_not_held(tmp_path):
    """Its Compile is there and its Hold is not: step 7 entered on no Hold of it, so nothing held its gate lists."""
    crate = pair(tmp_path, gates={"law": 1})
    md = S.md_of(crate)
    md["@graph"] = [e for e in md["@graph"] if not e["@id"].startswith("#hold-")]
    d = canonical.body_digest(md)
    plan = D.plan({"n-crystal-share": "0/1"}, {"a": {"device": "ibm_kingston"}, "b": {"device": "ibm_fez"}})
    record, _ = p3_compare.compute(D.read(D.write({"a": [d], "b": [d]}, plan)), None, {d: (crate, md)})
    assert (causes(record)["compile"], causes(record)["hold"]) == ("DIFFERS", "withheld")


def test_runs_on_two_dates_leave_the_date_seen(tmp_path):
    k = [B.ka(start="2026-11-01T10:00:00Z"), B.law(start="2026-11-01T10:01:00Z")]
    f = [B.ka(start="2026-11-02T10:00:00Z"), B.law(start="2026-11-02T10:01:00Z")]
    crate = pair(tmp_path, k=k, f=f)
    record, _ = S.computed(crate, crate, measures=("n-crystal-share",))
    assert "date" not in S.measure(record, "n-crystal-share")["unseen"]
    same = pair(tmp_path / "same")
    record, _ = S.computed(same, same, measures=("n-crystal-share",))
    assert "date" in S.measure(record, "n-crystal-share")["unseen"]


def test_bundles_naming_other_known_answers_leave_the_known_answer_seen(tmp_path):
    """Fez's bundle names the known answer and its complement, kingston's the known answer alone."""
    f = [B.control(start=f"{T}10:00Z"), B.law(start=f"{T}11:00Z"), B.law("law-1", start=f"{T}13:00Z")]
    crate = pair(tmp_path, f=f)
    record, _ = S.computed(crate, crate, measures=("n-crystal-share",))
    assert "known-answer" not in S.measure(record, "n-crystal-share")["unseen"]


def test_two_bit_orders_leave_the_decode_seen(tmp_path):
    """Fez's raw results written in the mirror order, which its Decodes name (`lsb-first`), each read right: one decode
    rule and two bit orders, so the decode is no factor both runs share (round 2, item 4), and every value is the one
    the order the rule names gives."""
    mirrored = pair(tmp_path, order="lsb-first")
    record, _ = S.computed(mirrored, mirrored)
    same = pair(tmp_path / "same")
    base, _ = S.computed(same, same)
    for m in S.FIVE:
        assert "decode" not in S.measure(record, m)["unseen"] and "decode" in S.measure(base, m)["unseen"], m
        assert S.measure(record, m)["b"]["value"] == S.measure(base, m)["b"]["value"], m


def test_one_gate_list_equal_and_not_held_is_still_equal(tmp_path):
    crate = pair(tmp_path, held=False)
    record, _ = S.computed(crate, crate)
    assert (causes(record)["compile"], causes(record)["hold"]) == ("EQUAL", "withheld")
    assert "compile-unheld" not in statements(record)


def test_member_pubs_with_no_manifest_circuit_leave_the_compile_and_what_was_submitted_unexposed(tmp_path):
    crate = pair(tmp_path)
    md = S.md_of(crate)
    for e in md["@graph"]:
        if "qro:Pub" in canonical.types(e) and e["qro:role"] != "known-answer":
            e["qro:commitment"] = "none"
    d = canonical.body_digest(md)
    plan = D.plan({"n-crystal-share": "0/1"}, {"a": {"device": "ibm_kingston"}, "b": {"device": "ibm_fez"}})
    record, _ = p3_compare.compute(D.read(D.write({"a": [d], "b": [d]}, plan)), None, {d: (crate, md)})
    c = causes(record)
    assert (c["compile"], c["hold"], c["submitted"]) == ("unexposed", "unexposed", "unexposed")
    assert {"compile-unheld", "submitted-differs"} <= set(statements(record))
    assert not {"compile", "submitted"} & set(S.measure(record, "n-crystal-share")["unseen"])


@pytest.mark.parametrize("fez, said", [
    ({"options": {"default_shots": 64, "execution": {"init_qubits": True, "rep_delay": 0.0005}}}, "options"),
    ({}, "shots"), ({"program": "estimator"}, "program"), ({"route": "ibm-batch"}, "route"),
    ({"kind": "simulator"}, "kind"), ({"decode": "quantum_film.ibm.decode/v2"}, "decode")],
    ids=["by its options", "by its shots", "by its program", "by its route", "by its kind", "by its decode"])
def test_what_was_submitted_differs(tmp_path, fez, said):
    """Each fact of what was submitted varied alone on fez's bundle (round 2, item 4: the builder held program, route,
    kind and decode constant). A simulator is compared in a rehearsal, as a real comparison refuses it kind-not-qpu."""
    crate = pair(tmp_path, f=jobs(10, shots=80) if said == "shots" else None, **fez)
    record, _ = S.computed(crate, crate, kind="rehearsal" if said == "kind" else "real")
    assert causes(record)["submitted"] == "DIFFERS" and "submitted-differs" in statements(record)
    assert "submitted" not in S.measure(record, "n-crystal-share")["unseen"]


def test_what_was_submitted_is_equal_by_default(tmp_path):
    crate = pair(tmp_path)
    record, _ = S.computed(crate, crate)
    assert causes(record)["submitted"] == "EQUAL" and "submitted" in S.measure(record, "n-crystal-share")["unseen"]


@pytest.mark.parametrize("k, f, status, said", [
    ("unknown", "unknown", "unknown", "commit-unknown"),
    (COMMIT_A, "unknown", "unknown", "commit-unknown"),
    (COMMIT_A, COMMIT_A, "EQUAL", None),
    (COMMIT_A, COMMIT_B, "DIFFERS", "commit-differs")],
    ids=["unknown in both", "unknown in one", "recorded and one", "recorded and two"])
def test_the_producing_commit(tmp_path, k, f, status, said):
    crate = pair(tmp_path, k=jobs(commit=k), f=jobs(10, commit=f))
    record, _ = S.computed(crate, crate)
    assert causes(record)["commit"] == status
    words = {"commit-unknown", "commit-differs"} & set(statements(record))
    assert words == ({said} if said else set())
    assert ("commit" in S.measure(record, "n-crystal-share")["unseen"]) is (status == "EQUAL")


def test_one_device_in_both_runs_is_equal_and_its_time_alone_differs(tmp_path):
    crate = B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", jobs()),
                               B.Bundle("ibm_kingston", "sheet-01", jobs(10))])
    bundles = sorted({e["sha256"] for e in S.md_of(crate)["@graph"] if e["@id"].endswith("manifest.json")})
    assert len(bundles) == 2
    _, decl = S.declare(crate, crate, runs={"a": {"bundles": [bundles[0]], "device": "ibm_kingston"},
                                           "b": {"bundles": [bundles[1]], "device": "ibm_kingston"}})
    record, _ = p3_compare.compute(decl, None, S.crates_of(crate))
    for m in S.FIVE:
        assert causes(record, m)["device"] == "EQUAL" and "one-device" in statements(record, m)
        assert not {"device-alone", "device-and-time"} & set(statements(record, m))
        assert "device" in S.measure(record, m)["unseen"]


def test_two_devices_differ(tmp_path):
    crate = pair(tmp_path)
    record, _ = S.computed(crate, crate)
    assert causes(record)["device"] == "DIFFERS" and "device" not in S.measure(record, "n-crystal-share")["unseen"]


def test_drift_is_controlled_from_two_members_and_unmeasured_with_one(tmp_path):
    crate = pair(tmp_path)
    record, _ = S.computed(crate, crate)
    assert causes(record)["drift"] == "CONTROLLED" and causes(record, "x0x1")["drift"] == "UNMEASURED"
    assert "drift-unmeasured" in statements(record, "x0x1") and "drift-unmeasured" not in statements(record)


def test_sampling_is_controlled_always(tmp_path):
    crate = pair(tmp_path)
    record, _ = S.computed(crate, crate)
    assert {causes(record, m)["sampling"] for m in S.FIVE} == {"CONTROLLED"}


def test_isolated_from_the_pipeline_where_every_cause_allows_it(tmp_path):
    """The commit recorded and one, one gate list, what was sent one, two members a run, and a difference far wider
    than both drift bounds: isolated from the pipeline; not as quantum, readout UNMEASURED, and the five-crystal share
    integrity against both twins."""
    k = jobs(five=240, shots=256, commit=COMMIT_A, coherence=False)
    f = jobs(10, five=40, shots=256, commit=COMMIT_A, coherence=False)
    crate = pair(tmp_path, k=k, f=f)
    record, _ = S.computed(crate, crate, measures=("n-crystal-share",))
    m = S.measure(record, "n-crystal-share")
    assert Fraction(m["strongForm"]) > 0 and m["means"] == "differ"
    assert m["statements"] == ["isolated-pipeline", "device-and-time", "readout-unbounded", "integrity-dephased",
                               "integrity-uniform"]
    assert m["unseen"] == ["question", "compile", "submitted", "commit", "decode", "known-answer", "date"]
    tight, _ = S.computed(crate, crate, measures={"n-crystal-share": m["strongForm"]})
    assert "strong-form-short" in S.measure(tight, "n-crystal-share")["statements"], "not above epsilon at it"


def test_the_causes_read_no_record_of_p2s(tmp_path):
    """Every Measurement, Contrast and Measuring of P2's taken out of the metadata: the record is the same bytes."""
    crate = pair(tmp_path)
    md = S.md_of(crate)
    stripped = copy.deepcopy(md)
    stripped["@graph"] = [e for e in stripped["@graph"] if not {"qro:Measurement", "qro:Contrast", "qro:Measuring"}
                          & set(canonical.types(e))]
    out = []
    for m in (md, stripped):
        d = canonical.body_digest(m)
        plan = D.plan({x: "0/1" for x in S.FIVE}, {"a": {"device": "ibm_kingston"}, "b": {"device": "ibm_fez"}})
        record, _ = p3_compare.compute(D.read(D.write({"a": [d], "b": [d]}, plan)), None, {d: (crate, m)})
        record["runs"] = None
        record["declaration"] = None
        out.append(record)
    assert out[0] == out[1]
