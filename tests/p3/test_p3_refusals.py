"""The refusals before any value, in the study's order (qro/p3_refusals.py; P3's design, item 3), on the builder's
crates fed to the computation directly. Where a case needs two crates that share exactly one identity, the second is the
first's metadata edited in memory (its job ids, its commitments or its raw digests), which is structure alone: each
refusal is decided before any value is read, and the values of the cases that go on come from the one directory's raw
bytes."""
import copy
import hashlib

import pytest

import p3_builder as B
import p3_support as S
from qro import canonical, p3_compare
from qro import p3_declaration as D
from qro.refusal import Refused


def bundle(device, label="morning", base="2026-11-01T10:", minutes=0, coherence=True, **kw):
    jobs = [B.ka(start=f"{base}{minutes:02d}:00Z"), B.law(start=f"{base}{minutes + 1:02d}:00Z"),
            B.law("law-2", start=f"{base}{minutes + 3:02d}:00Z", five=40)]
    if coherence:
        jobs.append(B.coherence(start=f"{base}{minutes + 5:02d}:00Z"))
    return B.Bundle(device, label, jobs, **kw)


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    return B.build(tmp_path_factory.mktemp("refusals"), [bundle("ibm_kingston"), bundle("ibm_fez", minutes=10)])


def two(crate, edit, measures=S.FIVE, kind="real", question="fixed", device_a="ibm_kingston",
        device_b="ibm_kingston"):
    """(declaration, crates): run a the crate as it is, run b the same directory with its metadata edited by `edit`."""
    md = S.md_of(crate)
    md2 = copy.deepcopy(md)
    edit(md2["@graph"])
    d1, d2 = canonical.body_digest(md), canonical.body_digest(md2)
    assert d1 != d2
    plan = D.plan({m: "0/1" for m in measures}, {"a": {"device": device_a}, "b": {"device": device_b}}, kind=kind,
                  question=question)
    decl = D.read(D.write({"a": [d1], "b": [d2]}, plan))
    return decl, {d1: (crate, md), d2: (crate, md2)}


def refusal(decl, crates):
    with pytest.raises(Refused) as r:
        p3_compare.compute(decl, None, crates)
    return r.value


def of_type(graph, t):
    return [e for e in graph if t in canonical.types(e)]


def new_ids(graph):
    for e in of_type(graph, "qro:Job"):
        e["qro:jobId"] = e["qro:jobId"] + "x"


def no_commitments(graph):
    for e in of_type(graph, "qro:Pub"):
        e["qro:commitment"] = "none"


def new_raws(graph):
    for e in of_type(graph, "qro:RawResult"):
        e["sha256"] = hashlib.sha256(e["sha256"].encode("ascii")).hexdigest()


# -- 1. comparison-trivial ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("edit, said", [
    (lambda g: (no_commitments(g), new_raws(g)), "the same job id"),
    (lambda g: (new_ids(g), new_raws(g)), "the same commitment"),
    (lambda g: (new_ids(g), no_commitments(g)), "the same raw result")],
    ids=["by job id alone", "by commitment alone", "by raw digest alone"])
def test_trivial_by_each_identity_alone(base, edit, said):
    r = refusal(*two(base, edit))
    assert (r.name, r.detail) == ("comparison-trivial", said)
    assert r.where.startswith("run a ibmkingstonmorning") and " and run b ibmkingstonmorning" in r.where


def test_trivial_names_the_first_shared_pair_by_its_job_ids(base):
    r = refusal(*two(base, lambda g: (no_commitments(g), new_raws(g))))
    assert r.where == "run a ibmkingstonmorningcoherence and run b ibmkingstonmorningcoherence"


def test_none_commitments_are_never_shared_and_nothing_else_shared_is_no_refusal(base):
    """Both runs' commitments `none`, their job ids and raw digests apart: not trivial. The comparison goes on."""
    md = S.md_of(base)
    no_commitments(md["@graph"])
    md2 = copy.deepcopy(md)
    new_ids(md2["@graph"])
    new_raws(md2["@graph"])
    d1, d2 = canonical.body_digest(md), canonical.body_digest(md2)
    plan = D.plan({"n-crystal-share": "0/1"}, {"a": {"device": "ibm_kingston"}, "b": {"device": "ibm_kingston"}})
    record, _ = p3_compare.compute(D.read(D.write({"a": [d1], "b": [d2]}, plan)), None, {d1: (base, md),
                                                                                       d2: (base, md2)})
    assert S.measure(record, "n-crystal-share")["refused"] == "none"
    assert S.measure(record, "n-crystal-share")["causes"]["compile"] == "unexposed", \
        "a Pub whose commitment is none has no manifest circuit"


def test_jobs_that_state_no_job_id_share_none(base):
    """Both runs' jobs state no qro:jobId, their commitments `none` and their raw digests apart: an absent id is never
    shared."""
    md = S.md_of(base)
    for e in of_type(md["@graph"], "qro:Job"):
        del e["qro:jobId"]
    no_commitments(md["@graph"])
    md2 = copy.deepcopy(md)
    new_raws(md2["@graph"])
    d1, d2 = canonical.body_digest(md), canonical.body_digest(md2)
    plan = D.plan({"n-crystal-share": "0/1"}, {"a": {"device": "ibm_kingston"}, "b": {"device": "ibm_kingston"}})
    record, _ = p3_compare.compute(D.read(D.write({"a": [d1], "b": [d2]}, plan)), None,
                                   {d1: (base, md), d2: (base, md2)})
    assert S.measure(record, "n-crystal-share")["refused"] == "none"


def test_a_shared_control_job_is_no_refusal(base):
    """Run b's crate shares run a's known-answer job, every identity of it, and no member: not trivial. (Both runs'
    member Pubs say `none`, so that each run's logical circuit is `unexposed` alike.)"""
    md = S.md_of(base)
    g = md["@graph"]
    controls = {e["@id"] for e in of_type(g, "qro:Job") if "knownanswer" in e["qro:jobId"]}
    members = {p["@id"] for e in of_type(g, "qro:Job") if e["@id"] not in controls for p in e["object"]}
    for e in of_type(g, "qro:Pub"):
        if e["@id"] in members:
            e["qro:commitment"] = "none"
    md2 = copy.deepcopy(md)
    g2 = md2["@graph"]
    for e in of_type(g2, "qro:Job"):
        if e["@id"] not in controls:
            e["qro:jobId"] += "x"
    raws = {r["@id"] for e in of_type(g2, "qro:Job") if e["@id"] not in controls for r in e["result"]}
    for e in of_type(g2, "qro:RawResult"):
        if e["@id"] in raws:
            e["sha256"] = hashlib.sha256(e["sha256"].encode("ascii")).hexdigest()
    d1, d2 = canonical.body_digest(md), canonical.body_digest(md2)
    plan = D.plan({"n-crystal-share": "0/1"}, {"a": {"device": "ibm_kingston"}, "b": {"device": "ibm_kingston"}})
    record, _ = p3_compare.compute(D.read(D.write({"a": [d1], "b": [d2]}, plan)), None,
                                   {d1: (base, md), d2: (base, md2)})
    a, b = (set(record["runs"][s]["crates"][0]["jobs"]) for s in "ab")
    assert a & b == {"ibmkingstonmorningknownanswer"}


def test_a_run_against_itself_is_trivial(base):
    md = S.md_of(base)
    d = canonical.body_digest(md)
    plan = D.plan({"x0x1": "0/1"}, {"a": {"device": "ibm_kingston"}, "b": {"device": "ibm_kingston"}})
    r = refusal(D.read(D.write({"a": [d], "b": [d]}, plan)), {d: (base, md)})
    assert (r.name, r.detail) == ("comparison-trivial", "the same job id")


# -- 2. question-differs ------------------------------------------------------------------------------------------------
def law_file_moved(g):
    q = of_type(g, "qro:Question")[0]
    next(e for e in g if e["@id"] == q["qro:law"]["@id"])["sha256"] = "0" * 64


def decode_renamed(g):
    for e in of_type(g, "qro:Decode"):
        e["qro:decodeRule"] = "quantum_film.ibm.decode/v2"


@pytest.mark.parametrize("edit", [law_file_moved, decode_renamed, lambda g: of_type(g, "qro:Question")[0].update(
    {"qro:twins": ["uniform"]})], ids=["the law file", "the decode rule", "the twins"])
def test_the_runs_questions_differing_by_digest_is_refused(base, edit):
    """Run b, fez's jobs, read from the crate's metadata with its question edited: they share no identity with
    kingston's."""
    decl, crates = two(base, edit, device_b="ibm_fez")
    r = refusal(decl, crates)
    assert (r.name, r.where) == ("question-differs", "the question")
    assert "the plan's question is fixed" in r.detail


def test_a_crate_whose_question_lacks_the_plans_measure_set_is_refused_whatever_the_question_says(base):
    for edit in (lambda g: of_type(g, "qro:Question")[0].pop("qro:measureSet"),
                 lambda g: g.remove(of_type(g, "qro:Question")[0])):
        for question in ("fixed", "varied"):
            decl, crates = two(base, edit, device_b="ibm_fez", question=question)
            r = refusal(decl, crates)
            assert r.name == "question-differs" and r.where.startswith("run b crate "), (r.where, question)
            assert "measure set is none" in r.detail


def test_a_measures_member_pubs_running_two_logical_circuits_is_refused(tmp_path):
    crate = B.build(tmp_path, [bundle("ibm_kingston"), bundle("ibm_fez", minutes=10, logical={"law": 1})])
    _, decl = S.declare(crate, crate, measures=("n-crystal-share", "x0x1"))
    with pytest.raises(Refused) as r:
        p3_compare.compute(decl, None, S.crates_of(crate))
    assert (r.value.name, r.value.where) == ("question-differs", "n-crystal-share")
    assert "ran 2 logical circuits" in r.value.detail
    record, _ = S.computed(crate, crate, measures=("x0x1",))
    assert S.measure(record, "x0x1")["causes"]["question"] == "EQUAL", "the coherence's circuits are one"


def test_varied_goes_on_with_the_question_differs(tmp_path, base):
    crate = B.build(tmp_path, [bundle("ibm_kingston"), bundle("ibm_fez", minutes=10, logical={"law": 1})])
    record, _ = S.computed(crate, crate, measures=("n-crystal-share", "x0x1"), question="varied")
    law, xx = S.measure(record, "n-crystal-share"), S.measure(record, "x0x1")
    assert law["causes"]["question"] == "DIFFERS" and "question-varied" in law["statements"]
    assert "isolated-pipeline" not in law["statements"] and "question" not in law["unseen"]
    assert xx["causes"]["question"] == "EQUAL" and "question-varied" not in xx["statements"]
    decl, crates = two(base, law_file_moved, device_b="ibm_fez", question="varied", measures=("n-crystal-share",))
    record, _ = p3_compare.compute(decl, None, crates)
    assert record["runs"]["a"]["question"] != record["runs"]["b"]["question"]
    assert S.measure(record, "n-crystal-share")["causes"]["question"] == "DIFFERS"


# -- 3. role-missing ---------------------------------------------------------------------------------------------------
def test_a_measure_a_run_lacks_is_refused_by_name_and_the_comparison_goes_on(tmp_path):
    crate = B.build(tmp_path, [bundle("ibm_kingston"), bundle("ibm_fez", minutes=10, coherence=False)])
    record, facts = S.computed(crate, crate)
    refused = {m["measure"]: m for m in record["measures"] if m["refused"] != "none"}
    assert sorted(refused) == ["x0x1", "y0y1"]
    assert refused["x0x1"] == {"epsilon": "0/1", "lacking": ["b"], "measure": "x0x1", "refused": "role-missing"}
    assert facts["refused"] == 2 and facts["measures"] == 5
    assert record["family"] == 3 * (1 + 2 + 1 + 2), "the refused measures count nothing"


def test_with_no_measure_left_the_whole_comparison_is_refused_role_missing(tmp_path):
    crate = B.build(tmp_path, [bundle("ibm_kingston"), B.Bundle("ibm_fez", "morning", [B.ka()])])
    _, decl = S.declare(crate, crate, measures=("n-crystal-share", "x0x1"))
    with pytest.raises(Refused) as r:
        p3_compare.compute(decl, None, S.crates_of(crate))
    assert (r.value.name, r.value.where) == ("role-missing", "the plan's measures")
    assert r.value.detail == "n-crystal-share: run b has no member; x0x1: run b has no member"


def test_both_runs_lacking_a_role_are_named(tmp_path):
    crate = B.build(tmp_path, [bundle("ibm_kingston", coherence=False), bundle("ibm_fez", minutes=10,
                                                                              coherence=False)])
    record, _ = S.computed(crate, crate, measures=("n-crystal-share", "y0y1"))
    assert S.measure(record, "y0y1")["lacking"] == ["a", "b"]


# -- 4. kind-not-qpu -----------------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def simulated(tmp_path_factory):
    return B.build(tmp_path_factory.mktemp("sim"), [bundle("ibm_kingston"), bundle("fake_fez", minutes=10,
                                                                                    kind="simulator")])


def test_a_simulator_in_a_comparison_declared_real_is_refused(simulated):
    _, decl = S.declare(simulated, simulated, device_b="fake_fez")
    with pytest.raises(Refused) as r:
        p3_compare.compute(decl, None, S.crates_of(simulated))
    assert (r.value.name, r.value.where) == ("kind-not-qpu", "run b fakefezmorningcoherence")
    assert "simulator" in r.value.detail and "declared real" in r.value.detail


def test_the_same_declared_a_rehearsal_is_computed_and_says_so(simulated):
    record, facts = S.computed(simulated, simulated, device_b="fake_fez", kind="rehearsal")
    assert record["kind"] == "rehearsal" and record["runs"]["b"]["kinds"] == ["simulator"]
    assert facts["kind"] == "rehearsal"


def test_a_device_of_no_stated_kind_is_not_a_qpu(base):
    decl, crates = two(base, lambda g: next(e for e in g if e["@id"] == "#device-ibm_fez").pop("qro:deviceKind"),
                       device_b="ibm_fez")
    r = refusal(decl, crates)
    assert r.name == "kind-not-qpu" and "of no stated kind" in r.detail


# -- the order ---------------------------------------------------------------------------------------------------------
def test_trivial_comes_before_kind(simulated):
    md = S.md_of(simulated)
    d = canonical.body_digest(md)
    plan = D.plan({"x0x1": "0/1"}, {"a": {"device": "fake_fez"}, "b": {"device": "fake_fez"}})
    r = refusal(D.read(D.write({"a": [d], "b": [d]}, plan)), {d: (simulated, md)})
    assert r.name == "comparison-trivial"


def test_trivial_comes_before_question_differs(base):
    r = refusal(*two(base, lambda g: (no_commitments(g), new_raws(g), decode_renamed(g))))
    assert r.name == "comparison-trivial"


def test_question_differs_comes_before_role_missing_and_kind(simulated):
    """Run b, the simulator's law job alone, read with its crate's law File moved: it lacks x0x1 and is no qpu, and
    its question differs, which is refused first."""
    md = S.md_of(simulated)
    md2 = copy.deepcopy(md)
    law_file_moved(md2["@graph"])
    d1, d2 = canonical.body_digest(md), canonical.body_digest(md2)
    plan = D.plan({"x0x1": "0/1", "n-crystal-share": "0/1"},
                  {"a": {"device": "ibm_kingston"}, "b": {"device": "fake_fez", "jobs": ["fakefezmorninglaw"]}})
    r = refusal(D.read(D.write({"a": [d1], "b": [d2]}, plan)), {d1: (simulated, md), d2: (simulated, md2)})
    assert r.name == "question-differs"


def test_question_differs_comes_before_a_whole_role_missing(base):
    """Run b, fez's law jobs alone with its crate's law File moved, has no member of the plan's one measure, and its
    question differs: refused question-differs, which comes first."""
    md = S.md_of(base)
    md2 = copy.deepcopy(md)
    law_file_moved(md2["@graph"])
    d1, d2 = canonical.body_digest(md), canonical.body_digest(md2)
    plan = D.plan({"x0x1": "0/1"}, {"a": {"device": "ibm_kingston"},
                                    "b": {"device": "ibm_fez", "jobs": ["ibmfezmorninglaw", "ibmfezmorninglaw2"]}})
    r = refusal(D.read(D.write({"a": [d1], "b": [d2]}, plan)), {d1: (base, md), d2: (base, md2)})
    assert (r.name, r.where) == ("question-differs", "the question")


def test_role_missing_whole_comes_before_kind(simulated):
    plan = D.plan({"x0x1": "0/1"}, {"a": {"device": "ibm_kingston"}, "b": {"device": "fake_fez",
                                                                           "jobs": ["fakefezmorninglaw"]}})
    d = S.digest_of(simulated)
    r = refusal(D.read(D.write({"a": [d], "b": [d]}, plan)), S.crates_of(simulated))
    assert r.name == "role-missing"


def test_a_crate_holding_a_unit_is_refused_step_unbuilt_before_any_refusal(base):
    md = S.md_of(base)
    md["@graph"].append({"@id": "#unit", "@type": "qro:Unit"})
    d = canonical.body_digest(md)
    plan = D.plan({"x0x1": "0/1"}, {"a": {"device": "ibm_kingston"}, "b": {"device": "ibm_kingston"}})
    r = refusal(D.read(D.write({"a": [d], "b": [d]}, plan)), {d: (base, md)})
    assert (r.name, r.where) == ("step-unbuilt", f"run a crate {d}")
    assert "left-out rule" in r.detail
