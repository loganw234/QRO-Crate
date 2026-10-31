"""The micro cases through a real SHACL engine (P4's design, item 5): each small model of tests/p4/p4_cases.py rendered
as Turtle by the writer and its graph as N-Triples, read by pyshacl in the engine's own interpreter, and its report
held to the failing focus nodes written beside the case (this repository's reading of the Recommendation) and to the
evaluator's. This is where a misreading of the Recommendation shows, and where a slip of the Turtle writer shows: a
wrong `sh:` name, a list written wrong, a severity in the wrong place.

The cases are read from the file of the quick stage by its path, not imported by name: a `tests` package in another
site-packages shadows any helper imported through `tests.` (CLAUDE.md), and the two stages are two sessions."""
import importlib.util
import sys
from pathlib import Path

import pytest
from p4shacl_helpers import ROOT, run_engine
from qro import p4_eval, p4_turtle
from qro.p4_model import SEVERITY


def load_cases():
    spec = importlib.util.spec_from_file_location("p4_cases_of_the_quick_stage", ROOT / "tests" / "p4" / "p4_cases.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CASES = load_cases()


@pytest.fixture(scope="module")
def engine():
    """The engine's answer to every case, in one process: {case index: result}."""
    jobs = [{"id": str(i), "kind": "graph", "shapes": p4_turtle.render(c.shapes, CASES.PREFIXES, ["micro case"]),
             "data": p4_turtle.ntriples(c.data)} for i, c in enumerate(CASES.CASES)]
    answers, versions = run_engine(jobs)
    return answers, versions


@pytest.mark.parametrize("i", range(len(CASES.CASES)), ids=[c.name for c in CASES.CASES])
def test_the_engine_fails_the_focus_nodes_the_case_says_and_the_evaluator_does_too(engine, i):
    answers, _ = engine
    c, got = CASES.CASES[i], answers[str(i)]
    assert got["ok"], got.get("error")
    seen = sorted({(r["shape"], r["focus"]) for r in got["results"]})
    assert seen == sorted(c.fails), c.name
    assert p4_eval.failing_pairs(p4_eval.validate(c.shapes, c.data)) == seen


def test_every_result_carries_the_severity_of_the_level_of_the_shape_that_holds_it(engine):
    answers, _ = engine
    checked, severities = 0, set()
    for i, c in enumerate(CASES.CASES):
        level = {s.id: s.level for s in c.shapes}            # a shape id is reused by cases of other levels
        for r in answers[str(i)]["results"]:
            assert r["severity"] == SEVERITY[level[r["shape"]]], (c.name, r)
            checked += 1
            severities.add(r["severity"])
    assert checked >= 60 and severities == {"Violation", "Warning", "Info"}


def test_the_engine_is_the_one_the_requirements_name(engine):
    _, versions = engine
    assert versions == {"pyshacl": "0.40.1", "rdflib": "7.6.0"}


def test_the_cases_are_read_from_the_quick_stages_file():
    assert Path(CASES.__file__).resolve() == (ROOT / "tests" / "p4" / "p4_cases.py").resolve() and len(CASES.CASES) >= 120
