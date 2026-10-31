"""The spelling probe through a real engine (P4's design, item 5, (c)): the same sample values (p4_helpers.SAMPLES) the quick
stage judges with the evaluator, each now given to pyshacl on the shape the generator makes of its spelling, and compared three ways: with the
evaluator's verdict; with the checker's own (qro/spelling.py), so that no shape refuses what the checker accepts; and with the
list of values a shape is looser about, which is the stated limit 3 and which the quick stage holds too. A pattern is a Python
`re` search in the engine, as in the evaluator; no other engine was run."""
import pytest
from p4shacl_helpers import quick_stage_module, run_engine
from qro import p4_shapes, p4_turtle
from qro import spelling as S
from qro.p4_model import Shape

helpers = quick_stage_module("p4_helpers")
EX = "http://example.org/"
PREFIXES = (("sh", "http://www.w3.org/ns/shacl#"), ("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
            ("xsd", "http://www.w3.org/2001/XMLSchema#"), ("ex", EX), ("qs", EX + "shapes#"))
P, A, SHAPE = EX + "p", EX + "a", EX + "shapes#probe"


def cases():
    """[(spelling, value, shapes text, data text)] for each sample the expansion would read."""
    out = []
    text = {}
    for sp, values in helpers.SAMPLES.items():
        constraints = p4_shapes.spelling_constraints(sp)
        prop = Shape(path=P, **constraints) if constraints is not None else Shape(path=P, in_=())
        text[sp] = p4_turtle.render([Shape(id=SHAPE, targets=(("subjectsOf", P),), props=(prop,))], PREFIXES, ["probe"])
        for value in values:
            obj = helpers.object_of(sp, value)
            if obj is not None:
                out.append((sp, value, text[sp], p4_turtle.ntriples([(A, P, obj)])))
    return out


CASES = cases()


@pytest.fixture(scope="module")
def engine():
    jobs = [{"id": str(i), "kind": "graph", "shapes": shapes, "data": data} for i, (_, _, shapes, data) in enumerate(CASES)]
    answers, _ = run_engine(jobs, timeout=900)
    return {i: a for i, a in answers.items()}


def accepts(answer):
    assert answer["ok"], answer.get("error")
    return not answer["results"]


def test_there_are_samples_for_every_spelling_and_every_word_set_and_the_engine_reads_them_all(engine):
    assert len(CASES) >= 270
    assert {sp for sp, *_ in CASES} >= set(S_SPELLINGS) and all(a["ok"] for a in engine.values())


S_SPELLINGS = [sp for sp in helpers.SAMPLES if not sp.startswith("word:")]


def test_the_engine_takes_the_values_the_evaluator_takes_and_refuses_the_rest(engine):
    wrong = [(sp, value) for i, (sp, value, _, _) in enumerate(CASES)
             if accepts(engine[str(i)]) is not helpers.shape_accepts(sp, value)]
    assert wrong == []


def test_the_engine_refuses_no_value_the_checkers_spelling_accepts(engine):
    stricter = [(sp, value) for i, (sp, value, _, _) in enumerate(CASES)
                if S.problem(sp, value) is None and not accepts(engine[str(i)])]
    assert stricter == []


def test_the_values_the_engine_takes_and_the_checker_refuses_are_the_stated_limit_and_no_others(engine):
    looser = {(sp, value) for i, (sp, value, _, _) in enumerate(CASES)
              if S.problem(sp, value) is not None and accepts(engine[str(i)])}
    assert looser == set(helpers.LOOSER)
