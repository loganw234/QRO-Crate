"""Crate by crate, a real engine and the evaluator say the same (P4's design, item 5, (a)): the engine reads the shapes' Turtle
files as they are committed under profile/validator/qro-crate/, and the crate's metadata through rdflib's own JSON-LD parser
with RO-Crate's context replaced by the pinned copy. For the fixture, the graph of every term, every plant of P4's (the faults
the shapes see, the ones only the checker sees, the edge cases the checker accepts) and a seeded sample of mutated crates:
  - the triples rdflib makes are the triples qro/p4_expand.py makes, so the evaluator reads the graph an engine reads;
  - the engine's failing shapes, at the focus nodes it fails them, are the evaluator's, with the severity of each shape's level;
  - and the plants' declarations hold in the engine's report as they do in the evaluator's."""
import json

import pytest
from p4shacl_helpers import ROOT, failing_must, mine, quick_stage_module, run_engine, shape_files, theirs, unclaimed, without
from qro import canonical, p4_eval, p4_expand
from qro import p4_examples as X
from qro import p4_shapes as H
from qro import vocabulary as V
from qro.p4_model import SEVERITY

helpers = quick_stage_module("p4_helpers")
SHAPES = H.build()
LEVEL = {s.id: s.level for s in SHAPES}


def corpus():
    """([(name, metadata dict)], [(name, the first refusal of steps 1 to 3)]): for the crates compared, the fixture, the
    graph of every term, the plants the expansion reads and a seeded sample of mutated crates, valid and general; and for
    the crates the expansion refuses to read, which are not compared but are never left out unseen: what the checker says."""
    out = []
    with X.Workspace(SHAPES) as work:
        out.append(("fixture", work.fresh()))
        out.append(("every-term", X.honest_metadata(work.fresh())))
        for p in X.every_plant():
            out.append((p.name, work.of_plant(p)))
        for seed in range(40):
            out.append((f"valid-{seed}", helpers.valid_mutated(work.pristine, seed)))
            out.append((f"mutated-{seed}", helpers.mutated(work.pristine, seed)))
        readable, unread = [], []
        for name, md in out:
            try:
                data = canonical.dumps(md)
            except (TypeError, ValueError):                     # not JSON the writer can write: there are no bytes to read
                continue
            try:
                p4_expand.expand(md)
            except p4_expand.ExpandError:
                with work.staged(md) as crate:
                    unread.append((name, helpers.early_verdict(crate, data)))
                continue
            readable.append((name, md))
    return readable, unread


CRATES, UNREAD = corpus()


@pytest.fixture(scope="module")
def engine():
    jobs = [{"id": name, "kind": "crate", "metadata": canonical.dumps(md).decode("ascii"), "shapes": shape_files()}
            for name, md in CRATES]
    answers, _ = run_engine(jobs, timeout=1500)
    return answers


def test_the_corpus_is_the_fixture_the_graph_of_every_term_the_plants_the_expansion_reads_and_the_sample():
    names = [n for n, _ in CRATES]
    assert names[:2] == ["fixture", "every-term"] and len(names) == len(set(names))
    plants = {p.name: p for p in X.every_plant()}
    unread = {n for n in plants if n not in names}
    assert unread == {p.name for p in plants.values() if p.unreadable}
    assert len(names) >= 270 and sum(n.startswith("valid-") for n in names) >= 35


def test_every_crate_the_expansion_refuses_to_read_is_refused_by_the_checker():
    """The lead's ruling of 2026-10-16T14:58:58Z: the evaluator abstains from a crate whose id it cannot resolve, so the
    checker must have refused the crate, at steps 1 to 3; the gates never skip one. The plants and the seeds' that the
    expansion refuses are counted here, so a corpus that drops them cannot go unseen."""
    assert len(UNREAD) >= 6 + 4                                          # the abstains plants, and seeds that hold an odd id
    assert [(n, early) for n, early in UNREAD if early == "ok"] == []
    assert {n for n, _ in UNREAD} >= {p.name for p in X.every_plant() if p.unreadable}
    assert {early for _, early in UNREAD} == {"spelling", "graph-form"}          # an id is `spelling`, a reference to a bad one `graph-form`


def test_the_engine_reads_every_crate(engine):
    bad = {n: a.get("error") for n, a in engine.items() if not a["ok"]}
    assert bad == {}


def test_the_triples_rdflib_makes_are_the_triples_the_expansion_makes(engine):
    wrong = []
    for name, md in CRATES:
        if theirs(engine[name]["triples"]) != mine(p4_expand.expand(md)):
            wrong.append(name)
    assert wrong == []


def test_the_engine_fails_the_shapes_at_the_focus_nodes_the_evaluator_does_and_with_the_severity_of_the_level(engine):
    wrong, severities = [], set()
    for name, md in CRATES:
        results = p4_eval.validate(SHAPES, p4_expand.expand(md))
        got = engine[name]
        seen = sorted({(r["shape"], r["focus"]) for r in got["results"]})
        if seen != p4_eval.failing_pairs(results):
            wrong.append(name)
        for r in got["results"]:
            severities.add(r["severity"])
            assert r["severity"] == SEVERITY[LEVEL[r["shape"]]], (name, r)
    assert wrong == [] and severities >= {"Violation", "Warning"}


def test_the_engine_confirms_what_each_plant_declares(engine):
    """A fault the shapes see fails its declared shapes in the engine's report; a crate the checker accepts (or only
    the checker sees) has no must result in it."""
    plants = {p.name: p for p in X.every_plant()}
    checked = 0
    for name, _ in CRATES:
        p = plants.get(name)
        if p is None:
            continue
        failing = {r["shape"].split("#", 1)[1] for r in engine[name]["results"] if r["severity"] == "Violation"}
        if p.shapes:
            assert set(p.shapes) <= failing, (name, sorted(failing))
        else:
            assert failing == set(), (name, sorted(failing))
        checked += 1
    assert checked >= 230


def test_the_fixture_and_the_graph_of_every_term_conform_to_every_shape_of_every_level_in_the_engine(engine):
    for name in ("fixture", "every-term"):
        assert engine[name]["results"] == [] and engine[name]["conforms"] is True, name


def test_the_engines_triples_are_json_the_comparison_can_read(engine):
    sample = engine["fixture"]["triples"][0]
    assert len(sample) == 3 and json.dumps(sample) and isinstance(sample[1], str)


def test_rdflib_reads_the_profile_crate_and_every_property_of_it_reaches_the_graph():
    """The Profile Crate is JSON-LD with RO-Crate's context and the prefix qro, the list a QRO crate has. An engine's parser keeps
    every key of it: a key the context does not define would be dropped without a word, and the count of triples would fall
    short of the count of values."""
    md = json.loads((ROOT / "profile" / "ro-crate-metadata.json").read_bytes())
    assert md["@context"] == V.context()                       # which the runner takes as it is
    want = sum(len(v) if isinstance(v, list) else 1 for e in md["@graph"] for k, v in e.items() if k != "@id")
    answers, _ = run_engine([{"id": "profile-crate", "kind": "crate", "metadata": json.dumps(md), "shapes": []}])
    got = answers["profile-crate"]
    assert got["ok"], got.get("error")
    assert len(got["triples"]) == want >= 400


def test_a_real_engine_fails_the_must_shapes_an_abstaining_plant_declares_and_no_others_on_a_crate_the_checker_refuses():
    """The plants the expansion refuses to read: the reader refuses their ids (FORMAT.md item 22), so the checker refuses each
    at step 1, the evaluator abstains, and a real engine reads the crate its own way. A blank-node id fails `entity`, an id that
    begins with an at sign (the root to rdflib, which then has two names) `term-name`, and an absolute `file:` id
    `file-digest-present`, and the root's reference to a blank node `term-haspart`; the other two fail none. Whatever the engine
    fails it fails on a crate the checker refused, by a name those shapes claim: the soundness of the claims for the one kind of
    crate the evaluator cannot see (limit 19). The last of them was the one plant whose refusal, `graph-form`, no failing shape
    claimed, until the shapes of the terms of spelling `ref` claimed it (the lead's ruling of 2026-10-19T17:41:46Z); the claim
    taken away from them is watched failing here, on that plant alone."""
    claims = {X.local(s.id): s.claims for s in SHAPES}
    with X.Workspace(SHAPES) as work:
        plants = [p for p in X.every_plant() if p.unreadable]
        jobs = [{"id": p.name, "kind": "crate", "metadata": canonical.dumps(work.of_plant(p)).decode("ascii"),
                 "shapes": shape_files()} for p in plants]
    answers, _ = run_engine(jobs)
    assert len(plants) == 6 and sum(bool(p.engine) for p in plants) == 4
    cases = []
    for p in plants:
        got = answers[p.name]
        assert got["ok"], got.get("error")
        failing = failing_must(got)
        assert failing == sorted(p.engine), (p.name, failing)
        assert p.checker in ("spelling", "graph-form"), p.name
        cases.append((p.name, p.checker, failing))
    assert unclaimed(cases, claims) == []                                        # none: every refusal is claimed
    refs = {"term-" + H.slug(t.key) for t in V.TERMS if t.spelling == "ref"}
    poor = without(claims, refs, "graph-form")                                   # and with the claim taken away, the one plant
    assert unclaimed(cases, poor) == ["abstains-blank-node-reference"]
