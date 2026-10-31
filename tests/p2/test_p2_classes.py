"""Signal or integrity, computed from the law's bytes and the twin's rule, never declared (P2's design, item 3): (a) a
twin equal to the law makes every measure integrity; (b) a twin that differs from it is signal exactly where an
expected value moves; (c) the uniform and dephased columns are section 7's, row by row; (d) mutants of the classifier
each fail (a), (b) or (c)."""
from fractions import Fraction

import pytest

from qro import p2_law

F = Fraction


def v0():
    return p2_law.read(p2_law.law_bytes())


def classes_under(law, twin_model, classify=p2_law.classify):
    """{measure: class} of a twin model against the law, by `classify`."""
    e_law = p2_law.expected(p2_law.model_of("law", law), law)
    e_twin = p2_law.expected(twin_model, law)
    return {m: classify(e_law[m], e_twin[m]) for m in p2_law.MEASURES}


def equal_twin(law):
    return p2_law.Model(law.weights, law.den, dict(law.observables))


def bent_twin(law):
    """The law's table with 1/4096 moved from its first allowed layout to its first forbidden one."""
    w = list(law.weights)
    allowed = next(i for i, x in enumerate(w) if x > 0)
    forbidden = next(i for i, x in enumerate(w) if x == 0)
    w[allowed] -= 1
    w[forbidden] += 1
    return p2_law.Model(tuple(w), law.den, dict(law.observables))


def coherence_twin(law):
    return p2_law.Model(law.weights, law.den, {**law.observables, "Y0Y1": F(1, 3)})


MOVES_WITH_A_LAYOUT = {"one-site-occupations", "pair-occupations", "forbidden-share", "tvd", "linear-xeb",
                       "nn-pair-correlation"}
# section 7's table, as P2's design item 2 measured it: (law, uniform twin, dephased twin; classes uniform / dephased)
TABLE = {"n-crystal-share": (F(1), F(1), F(1), "integrity", "integrity"),
         "forbidden-share": (F(0), F(85, 273), F(0), "signal", "integrity"),
         "tvd": (F(0), F(85, 273), F(0), "signal", "integrity"),
         "linear-xeb": (F(1), F(0), F(1), "signal", "integrity"),
         "nn-pair-correlation": (F(16, 25), F(64, 75), F(16, 25), "signal", "integrity"),
         "x0x1": (F(3, 8), F(0), F(0), "signal", "signal"),
         "y0y1": (F(3, 8), F(0), F(0), "signal", "signal"),
         "crystals-per-shot": (None, None, None, "integrity", "integrity"),
         "one-site-occupations": (None, None, None, "integrity", "integrity"),
         "pair-occupations": (None, None, None, "signal", "integrity")}


def a_holds(law, classify):
    return set(classes_under(law, equal_twin(law), classify).values()) == {"integrity"}


def b_holds(law, classify):
    bent = classes_under(law, bent_twin(law), classify)
    coh = classes_under(law, coherence_twin(law), classify)
    return ({m for m, c in bent.items() if c == "signal"} == MOVES_WITH_A_LAYOUT
            and {m for m, c in coh.items() if c == "signal"} == {"y0y1"})


def c_holds(law, classify):
    uni = classes_under(law, p2_law.model_of("uniform", law), classify)
    dep = classes_under(law, p2_law.model_of("dephased", law), classify)
    return all((uni[m], dep[m]) == TABLE[m][3:] for m in p2_law.MEASURES)


def test_a_a_twin_equal_to_the_law_makes_every_measure_integrity():
    assert a_holds(v0(), p2_law.classify)


def test_b_a_twin_that_moves_one_weight_is_signal_exactly_where_an_expectation_moves():
    law = v0()
    bent = classes_under(law, bent_twin(law))
    assert {m for m, c in bent.items() if c == "signal"} == MOVES_WITH_A_LAYOUT
    assert {m for m, c in bent.items() if c == "integrity"} == {"n-crystal-share", "crystals-per-shot", "x0x1", "y0y1"}


def test_b_a_twin_equal_to_the_law_but_for_one_coherence_is_signal_on_that_coherence_only():
    law = v0()
    assert {m for m, c in classes_under(law, coherence_twin(law)).items() if c == "signal"} == {"y0y1"}


def test_c_the_uniform_and_dephased_columns_are_section_7s_row_by_row():
    law = v0()
    got = p2_law.classes(law)
    for m, (lv, uv, dv, uc, dc) in TABLE.items():
        u, d = got[(m, "uniform")], got[(m, "dephased")]
        assert (u.cls, d.cls) == (uc, dc), m
        assert (u.law_value, u.twin_value, d.law_value, d.twin_value) == (lv, uv, lv, dv), m
    assert sorted(got) == sorted((m, t) for m in p2_law.MEASURES for t in ("dephased", "uniform"))


def test_c_the_vector_measures_carry_a_class_and_no_value():
    got = p2_law.classes(v0())
    for m in p2_law.VECTOR:
        for t in p2_law.TWINS:
            assert got[(m, t)].law_value is None and got[(m, t)].twin_value is None


def test_the_measure_sets_partition_is_the_vocabularys_ten_words():
    assert set(p2_law.SCALAR) | set(p2_law.VECTOR) == set(p2_law.MEASURES)
    assert not set(p2_law.SCALAR) & set(p2_law.VECTOR)
    assert set(p2_law.CERTIFIED) < set(p2_law.SCALAR) and len(p2_law.MEASURES) == 10
    assert p2_law.TWINS == ("dephased", "uniform")


MUTANTS = {
    "always signal": lambda a, b: "signal",
    "always integrity": lambda a, b: "integrity",
    "signal where the law's value is nonzero": lambda a, b: "signal" if a else "integrity",
    "the twin's value read for the law's": lambda a, b: p2_law.classify(b, b),
    "integrity where the two differ": lambda a, b: "integrity" if a != b else "signal",
}


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
def test_d_each_mutant_of_the_classifier_fails_a_b_or_c(mutant):
    law, classify = v0(), MUTANTS[mutant]
    assert a_holds(law, p2_law.classify) and b_holds(law, p2_law.classify) and c_holds(law, p2_law.classify)
    assert not (a_holds(law, classify) and b_holds(law, classify) and c_holds(law, classify))


def test_d_the_classes_function_uses_the_classifier_and_is_memoised_by_the_laws_digest(monkeypatch):
    law = v0()
    p2_law.clear()
    honest = p2_law.classes(law)
    assert p2_law.classes(law) is honest
    monkeypatch.setattr(p2_law, "classify", MUTANTS["always signal"])
    assert p2_law.classes(law) is honest, "memoised: the law's bytes have not changed"
    p2_law.clear()
    assert {c.cls for c in p2_law.classes(law).values()} == {"signal"}
    monkeypatch.undo()
    p2_law.clear()
    assert p2_law.classes(law) == honest


def test_the_small_law_has_its_own_classes():
    from p2_builder import small_law_bytes
    got = p2_law.classes(p2_law.read(small_law_bytes()))
    assert got[("x0x1", "dephased")].cls == "signal" and got[("x0x1", "dephased")].law_value == F(4, 5)
    assert got[("forbidden-share", "uniform")].twin_value == F(1, 3)      # two of the six layouts are forbidden
    assert got[("n-crystal-share", "uniform")].cls == "integrity"
