"""A reference outside the id rule on each term of spelling `ref`, through a real engine (the lead's ruling of 2026-10-19T17:41:46Z:
the shapes of the 18 terms whose spelling is `ref` claim `graph-form`; since the ruling of 2026-10-26T11:18:27Z every must shape
does, as FORM, and this stays as the evidence that these 18 need it). The report of P4's resume found it: the root's reference to
`_:b0` is a blank node to rdflib, which the node kind of `term-haspart` refuses, on a crate the checker refuses `graph-form`
(FORMAT.md item 22: a reference that is no absolute IRI names no entity) and the evaluator cannot read. This holds the claim over
every such term, not the one plant:
  - the crates are one reference of each kind (tests/p4/p4_refs.py: no form of the rule, a form that no entity holds, an id
    that reads as an IRI, and absolute IRIs) added to each term, on a host its domain admits;
  - where steps 1 to 3 accept the crate a real engine fails no must shape; where they refuse it and the engine fails any, the
    failing shapes claim the refusal;
  - a shape that is no `ref` term's also fails on some of them (the descriptor, the root, the shapes of the terms whose host
    the reference unmakes), and each of those claims the refusal too: nothing is widened for them;
  - the claim taken away from the shapes of the `ref` terms is watched failing: the crates it was added for are found, and the
    helpers that find them (`unclaimed`, `without`, `failing_must`) are held on a case of their own first."""
import pytest
from p4shacl_helpers import failing_must, quick_stage_module, run_engine, shape_files, unclaimed, without
from qro import canonical
from qro import p4_examples as X
from qro import p4_shapes as H

helpers = quick_stage_module("p4_helpers")
refs = quick_stage_module("p4_refs")
SHAPES = H.build()
CLAIMS = {X.local(s.id): s.claims for s in SHAPES}
REF_SHAPES = {"term-" + H.slug(t.key) for t in refs.ref_terms()}


def crates():
    """[(term key, reference, the checker's refusal at steps 1 to 3 or "ok", the metadata's bytes)] for every term and reference."""
    out = []
    with pytest.MonkeyPatch.context() as mp:
        helpers.prepare(mp)
        with X.Workspace(SHAPES) as work:
            for t in refs.ref_terms():
                for bad in refs.BAD:
                    md = refs.crate_with(work.pristine, t, bad)
                    data = canonical.dumps(md)
                    with work.staged(md) as crate:
                        out.append((t.key, bad, helpers.early_verdict(crate, data), data.decode("ascii")))
    return out


CRATES = crates()


@pytest.fixture(scope="module")
def cases():
    """[(name, the checker's refusal or "ok", the must shapes the engine fails)] for every crate, one engine run."""
    jobs = [{"id": f"{k}|{b}", "kind": "crate", "metadata": data, "shapes": shape_files()} for k, b, _, data in CRATES]
    answers, _ = run_engine(jobs, timeout=1500)
    out = []
    for k, b, early, _ in CRATES:
        got = answers[f"{k}|{b}"]
        assert got["ok"], (k, b, got.get("error"))
        out.append((f"{k}|{b}", early, failing_must(got)))
    return out


def test_the_helpers_ask_the_union_of_the_failing_shapes_claims_and_take_a_claim_from_the_shapes_named_only():
    """The instruments of the tests below, held on a case of their own, with no engine: the first failing shape lacking a refusal
    that a later one claims is no unclaimed refusal, and a claim taken away is taken from the shapes named and from no other."""
    claims = {"a": ("x",), "b": ("y",), "c": ("x", "y")}
    cases = [("both", "y", ["a", "b"]), ("neither", "z", ["a", "b"]), ("a later one claims it", "y", ["a", "c"]), ("none fails", "z", [])]
    assert unclaimed(cases, claims) == ["neither"]
    poor = without(claims, {"b", "c"}, "y")
    assert poor == {"a": ("x",), "b": (), "c": ("x",)}
    assert unclaimed(cases, poor) == ["a later one claims it", "both", "neither"]
    assert without(claims, set(), "y") == claims and without(claims, {"a"}, "y") == claims
    reports = [("b", "Violation"), ("a", "Violation"), ("a", "Violation"), ("w", "Warning")]
    answer = {"results": [{"shape": f"file:///profile#{name}", "severity": severity} for name, severity in reports]}
    assert failing_must(answer) == ["a", "b"]                                         # the Violations, once each, sorted


def test_the_crates_are_a_reference_of_each_kind_on_each_term_of_spelling_ref():
    assert len(CRATES) == len(refs.ref_terms()) * len(refs.BAD) >= 18 * 16
    assert {early for _, _, early, _ in CRATES} == {"graph-form", "spelling", "ok"}
    assert {bad for _, bad, early, _ in CRATES if early == "ok"} >= set(refs.ACCEPTED)


def test_where_steps_1_to_3_accept_the_crate_a_real_engine_fails_no_must_shape(cases):
    accepted = [(name, failing) for name, early, failing in cases if early == "ok"]
    assert len(accepted) >= 2 * 15                                                   # the absolute IRIs, on 15 of the 18 terms
    assert [x for x in accepted if x[1]] == []


def test_where_a_real_engine_fails_a_must_shape_a_failing_shape_claims_the_refusal(cases):
    assert len([c for c in cases if c[2]]) >= 60                                     # the engine fails a must shape on 60 of the 288
    assert unclaimed(cases, CLAIMS) == []


def test_a_real_engine_fails_the_shape_of_a_term_of_spelling_ref_on_a_blank_node_and_on_no_other_reference(cases):
    blank = {name.split("|", 1)[1] for name, _, failing in cases if set(failing) & REF_SHAPES}
    assert blank == {"_:b0"}, blank                                                  # pyshacl 0.40.1 on rdflib 7.6.0
    on_a_term = {name.split("|", 1)[0] for name, _, failing in cases if set(failing) & REF_SHAPES}
    assert on_a_term == {t.key for t in refs.ref_terms()}                            # and on every such term: each needs the claim


def test_every_shape_that_is_no_ref_terms_and_fails_on_such_a_reference_claims_graph_form_too(cases):
    """The lead's question: does a shape that is no `ref` term's fail on a reference the checker refuses `graph-form`? Some do,
    and each already claims it, so nothing is widened."""
    others = {}
    for name, early, failing in cases:
        for f in failing:
            if f not in REF_SHAPES:
                others.setdefault(f, set()).add(early)
    assert {"descriptor", "root", "file-reached"} <= set(others), sorted(others)
    assert "graph-form" in {e for early in others.values() for e in early}
    for f, refusals in others.items():
        assert "graph-form" in CLAIMS[f] and refusals <= set(CLAIMS[f]), (f, refusals, CLAIMS[f])


def test_the_claim_taken_away_from_the_shapes_of_the_ref_terms_is_found(cases):
    poor = without(CLAIMS, REF_SHAPES, "graph-form")
    found = unclaimed(cases, poor)
    expected = sorted(name for name, early, failing in cases if failing and set(failing) <= REF_SHAPES and early == "graph-form")
    assert found == expected and len(found) >= 15, found                             # 15 of the 18: three also fail a shape that claims it
    assert {name.split("|", 1)[1] for name in found} == {"_:b0"}
