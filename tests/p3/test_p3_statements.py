"""The statements (qro/p3_verdicts.py's `statements`; P3's design, item 5's table): each word said exactly when its
condition holds, over a grid of every condition the table reads, held to the table's conditions written here again as
plain predicates; the words in the vocabulary's order; and the three sentences of section 11's `states` rows the
vocabulary's meanings of the words that say them."""
import itertools
from fractions import Fraction

import pytest

from controls import registry
from qro import p3_verdicts
from qro import vocabulary as V

EPS = Fraction(1, 20)


def spec(c):
    """The table's conditions, each word on its own, as the design's item 5 writes them."""
    k, sf, causes, rho = c["members"], c["strongForm"], c["causes"], c["rho"]
    drift = all(k[s] >= 2 for s in "ab")
    pipeline = (causes["question"] == "EQUAL" and causes["submitted"] == "EQUAL" and causes["commit"] == "EQUAL"
                and (causes["compile"] == "EQUAL" or (causes["compile"] == "DIFFERS" and causes["hold"] == "holds"))
                and drift and sf is not None and sf > EPS)
    beyond = c["readout"] == "CONTROLLED" and sf is not None and rho is not None and sf - rho > EPS
    out = {
        "isolated-pipeline": pipeline,
        "drift-unmeasured": any(k[s] == 1 for s in "ab"),
        "strong-form-short": drift and sf is not None and sf <= EPS,
        "question-varied": causes["question"] == "DIFFERS",
        "submitted-differs": causes["submitted"] != "EQUAL",
        "commit-unknown": causes["commit"] == "unknown",
        "commit-differs": causes["commit"] == "DIFFERS",
        "compile-unheld": causes["compile"] == "unexposed" or (causes["compile"] == "DIFFERS"
                                                              and causes["hold"] != "holds"),
        "device-alone": causes["device"] == "DIFFERS" and c["interleaved"],
        "device-and-time": causes["device"] == "DIFFERS" and not c["interleaved"],
        "one-device": causes["device"] == "EQUAL",
        "quantum-unpiped": not pipeline,
        "readout-unbounded": c["readout"] == "UNMEASURED",
        "readout-short": c["readout"] == "CONTROLLED" and sf is not None and rho is not None and sf - rho <= EPS}
    for twin in ("dephased", "uniform"):
        classes = [c["classes"][s][twin] for s in "ab"]
        out[f"integrity-{twin}"] = "integrity" in classes
        out[f"quantum-{twin}"] = pipeline and all(x == "signal" for x in classes) and beyond
    return [w for w in V.WORDS["statement"] if out[w]]


def conditions():
    base = {"question": "EQUAL", "submitted": "EQUAL", "commit": "EQUAL", "compile": "EQUAL", "hold": "holds",
            "device": "DIFFERS", "drift": "CONTROLLED", "sampling": "CONTROLLED"}
    variants = [("question", "DIFFERS"), ("submitted", "DIFFERS"), ("submitted", "unexposed"), ("commit", "unknown"),
                ("commit", "DIFFERS"), ("compile", "DIFFERS"), ("compile", "unexposed"), ("hold", "withheld"),
                ("device", "EQUAL")]
    for changed in itertools.chain([()], itertools.combinations(variants, 1), itertools.combinations(variants, 2)):
        causes = dict(base)
        for key, value in changed:
            causes[key] = value
        for members in ({"a": 2, "b": 3}, {"a": 1, "b": 3}, {"a": 1, "b": 1}):
            drift = all(v >= 2 for v in members.values())
            for sf in ((None,) if not drift else (Fraction(-1, 10), EPS, Fraction(1, 10), Fraction(3, 10))):
                for interleaved in (False, True):
                    for readout, rho in (("UNMEASURED", None), ("CONTROLLED", Fraction(1, 10)),
                                         ("CONTROLLED", Fraction(1, 20)), ("CONTROLLED", Fraction(0))):
                        for cls in (("signal", "signal"), ("integrity", "signal"), ("signal", "integrity"),
                                    ("integrity", "integrity")):
                            yield {"causes": causes, "members": members, "strongForm": sf, "epsilon": EPS,
                                   "interleaved": interleaved, "readout": readout, "rho": rho,
                                   "classes": {"a": {"dephased": cls[0], "uniform": cls[1]},
                                               "b": {"dephased": cls[0], "uniform": "signal"}}}


def test_each_statement_is_said_exactly_when_its_condition_holds():
    seen = set()
    n = 0
    for c in conditions():
        got = p3_verdicts.statements(c)
        assert got == spec(c), c
        seen |= set(got)
        n += 1
    assert n == 46 * 6 * 2 * 4 * 4
    assert seen == set(V.WORDS["statement"]), "the grid reaches every word"


def test_the_words_are_listed_in_the_vocabularys_order():
    c = next(iter(conditions()))
    got = p3_verdicts.statements(c)
    order = list(V.WORDS["statement"])
    assert got == sorted(got, key=order.index)


@pytest.mark.parametrize("row, word", [("single-runs", "drift-unmeasured"), ("readout-unbounded", "readout-unbounded"),
                                       ("time-confounded", "device-and-time")])
def test_section_11s_three_sentences_are_the_meanings_of_the_words_that_say_them(row, word):
    assert registry.sentence(registry.CONTROL[row]) == V.WORDS["statement"][word]


def test_isolated_as_quantum_against_a_twin_needs_its_signal_in_both_runs():
    c = {"causes": {"question": "EQUAL", "submitted": "EQUAL", "commit": "EQUAL", "compile": "EQUAL",
                    "hold": "holds", "device": "DIFFERS"}, "members": {"a": 2, "b": 2}, "strongForm": Fraction(1, 2),
         "epsilon": EPS, "interleaved": True, "readout": "CONTROLLED", "rho": Fraction(1, 10),
         "classes": {"a": {"dephased": "signal", "uniform": "signal"}, "b": {"dephased": "signal", "uniform": "signal"}}}
    assert p3_verdicts.statements(c) == ["isolated-pipeline", "device-alone", "quantum-dephased", "quantum-uniform"]
    c["classes"]["b"]["uniform"] = "integrity"
    assert p3_verdicts.statements(c) == ["isolated-pipeline", "device-alone", "integrity-uniform", "quantum-dephased"]
