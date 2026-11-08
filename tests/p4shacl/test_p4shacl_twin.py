"""P1's twin read by a real engine (P4.3; P4's design, item 6, the example table's "P1's twin", and D8): the shapes' half of the twin
as the profile's second positive example, the evaluator's being tests/p4/test_p4_twin.py. The twin is built at stage time by P1.2's
toolkit (tests/p4/p4_twin.py), once as the tree builds it (P2's module present: the first crate to carry P2's terms into P4's shapes
outside a plant) and once as P1 alone builds it, and pyshacl reads its descriptor against the committed Turtle of
profile/validator/qro-crate/. Held here:
  - the engine reads both, and the triples rdflib makes are the triples the expansion makes (the expansion's triples, the engine's);
  - every must shape, and every should shape, conforms to each in the engine: its report is empty;
  - the engine fails what the evaluator fails on a twin with one value of P2's made wrong, so the engine reads P2's terms on it."""
import copy

import pytest
from p4shacl_helpers import failing_must, mine, quick_stage_module, run_engine, shape_files, theirs
from qro import canonical, p4_eval, p4_expand
from qro import p4_examples as X
from qro import p4_shapes as H

twin = quick_stage_module("p4_twin")
SHAPES = H.build()
BAD = "twin-with-a-measure-no-law-has"


def bad_measure(md):
    """The twin's metadata with the first `qro:measure` it carries made a word the table does not have."""
    md = copy.deepcopy(md)
    host = next(e for e in md["@graph"] if "qro:measure" in e)
    host["qro:measure"] = "no-such-measure"
    return md


def job(name, md):
    return {"id": name, "kind": "crate", "metadata": canonical.dumps(md).decode("ascii"), "shapes": shape_files()}


@pytest.fixture(scope="module")
def engine():
    mds = {name: twin.metadata_of(name) for name in twin.names()}
    jobs = [job(name, md) for name, md in mds.items()] + [job(BAD, bad_measure(mds["p1-twin"]))]
    answers, _ = run_engine(jobs, timeout=900)
    return answers, mds


def test_the_examples_the_engine_reads_are_the_twin_with_p2_and_the_twin_alone():
    assert twin.names() == ["p1-twin", "p1-twin-alone"]


def test_the_engine_reads_both_twins(engine):
    answers, _ = engine
    assert {n: a.get("error") for n, a in answers.items() if not a["ok"]} == {}


def test_the_triples_rdflib_makes_of_a_twin_are_the_triples_the_expansion_makes(engine):
    answers, mds = engine
    for name, md in mds.items():
        got, want = theirs(answers[name]["triples"]), mine(p4_expand.expand(md))
        assert len(want) > 500 and got == want, (name, len(got), len(want), sorted(map(str, got ^ want))[:3])


@pytest.mark.parametrize("name", twin.names())
def test_every_shape_of_every_level_conforms_to_the_twin_in_the_engine(engine, name):
    answers, _ = engine
    got = answers[name]
    assert got["results"] == [] and got["conforms"] is True and failing_must(got) == []


def test_the_engine_fails_the_shape_of_a_term_of_p2_on_a_twin_with_one_value_made_wrong_as_the_evaluator_does(engine):
    """The control that the engine reads P2's terms on the twin: `qro:measure` made a word the table does not have fails the term's
    shape in the engine and in the evaluator, at the same focus, and the twin it was made from conforms."""
    answers, mds = engine
    results = p4_eval.validate(SHAPES, p4_expand.expand(bad_measure(mds["p1-twin"])))
    got = answers[BAD]
    seen = sorted({(r["shape"], r["focus"]) for r in got["results"]})
    assert seen == p4_eval.failing_pairs(results) and seen
    assert failing_must(got) == sorted(X.local(i) for i in p4_eval.failing(results, "must")) == ["term-qro-measure"]
