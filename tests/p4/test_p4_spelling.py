"""The spelling differential (gate 2 of P4's design, item 4.6): the sample values of p4_helpers.SAMPLES over every spelling of
the table, each judged by qro/spelling.py's own verdict and by the shape the generator makes of that spelling. No shape
refuses a value the checker accepts. Where a shape accepts a value the checker refuses it is looser, which is a stated limit (3), and every
one is listed here with its reason: so the day a shape gets stricter, or looser, a test says so.

Then the same, a term at a time: its absence words, its list or its one value."""
import pytest
from p4_helpers import LOOSER, SAMPLES, differential, object_of, shape_accepts
from qro import p4_eval, p4_examples as X, p4_shapes as H
from qro import p4_expand as E
from qro import spelling as S
from qro import vocabulary as V
from qro.p4_model import XSD_STRING, Shape

def test_no_shape_refuses_a_value_the_checkers_spelling_accepts():
    found = differential()
    assert [x for x in found if x[2] == "stricter"] == []


def test_the_expansion_reads_every_sample_the_checkers_spelling_accepts():
    """A sample the expansion cannot read is one the shapes would never see: the gate does not skip it unseen (after P0.5)."""
    assert [x for x in differential() if x[2] == "unread"] == []


def test_the_differential_finds_a_sample_the_spelling_accepts_and_the_expansion_cannot_read(monkeypatch):
    real = E.iri_of_id

    def blind(value):
        if value.startswith("#"):
            raise E.ExpandError("refused by the test")
        return real(value)
    monkeypatch.setattr(E, "iri_of_id", blind)
    assert [x for x in differential() if x[2] == "unread"] == [("ref", {"@id": "#a"}, "unread")]


def test_the_shapes_that_are_looser_are_exactly_the_stated_limits_and_each_has_its_reason():
    found = {(sp, v) for sp, v, who in differential() if who == "looser"}
    assert found == set(LOOSER), (sorted(found - set(LOOSER), key=repr), sorted(set(LOOSER) - found, key=repr))
    assert all(LOOSER.values())


def test_a_spelling_is_judged_on_samples_both_sides_of_each_edge():
    assert set(SAMPLES) >= set(V.SPELLINGS)
    total = sum(len(v) for v in SAMPLES.values())
    assert total >= 290
    for sp, values in SAMPLES.items():
        verdicts = [S.problem(sp, v) is None for v in values]
        assert any(verdicts) or sp == "slot", f"{sp}: no sample the checker accepts"
        assert not all(verdicts), f"{sp}: no sample the checker refuses"
        seen = [shape_accepts(sp, v) for v in values]
        assert any(x is True for x in seen) or sp == "slot", f"{sp}: no sample the shape accepts"
        assert any(x is False for x in seen), f"{sp}: no sample the shape refuses"


@pytest.mark.parametrize("sp", sorted(set(V.SPELLINGS) - {"slot"}))
def test_the_gate_is_watched_failing_on_a_shape_made_stricter_than_its_spelling(monkeypatch, sp):
    """A constraint that refuses everything is stricter than the checker wherever the checker accepts a value, and the
    differential says so for every spelling there is."""
    real = H.SPELLING_SHAPES[sp]
    monkeypatch.setitem(H.SPELLING_SHAPES, sp, lambda: dict(real(), in_=()))
    stricter = [x for x in differential() if x[2] == "stricter" and x[0] == sp]
    assert stricter, sp


def test_the_gate_is_watched_failing_on_the_digest_pattern_made_one_too_long(monkeypatch):
    monkeypatch.setitem(H.SPELLING_SHAPES, "digest", lambda: dict(datatype=XSD_STRING, pattern="^[0-9a-f]{65}$",
                                                                  max_length=64))
    assert [x for x in differential() if x[2] == "stricter" and x[0] == "digest"]


def test_the_gate_is_watched_failing_on_a_word_set_missing_a_word(monkeypatch):
    real = H.spelling_constraints

    def short(spelling):
        c = real(spelling)
        if spelling == "word:device-kind":
            return dict(c, in_=c["in_"][:-1])
        return c
    monkeypatch.setattr(H, "spelling_constraints", short)
    assert [x for x in differential() if x[2] == "stricter" and x[0] == "word:device-kind"]


# -- a term at a time: its absence words, its list or its one value ---------------------------------------------------------------
def term_accepts(t, *values):
    """Whether the term's shape takes `values` as the values of one property of one entity."""
    shape = next(s for s in H.build() if s.id == H.shape_iri("term-" + H.slug(t.key)))
    objs = [object_of(t.spelling, v) for v in values]
    assert None not in objs, (t.key, values)
    graph = p4_eval.Graph([("urn:s", H.term_iri(t.key), o) for o in objs] or [("urn:s", "urn:other", "urn:o")])
    return not p4_eval.property_reasons(graph, shape.props[0], "urn:s")


def test_every_terms_shape_takes_a_valid_value_and_an_absence_word_and_refuses_the_rest():
    for t in V.TERMS:
        good = X.valid_value(t)
        good = good if isinstance(good, list) else [good]
        assert term_accepts(t, *good), (t.key, "a valid value")
        bad = X.bad_value(t)
        bad = bad if isinstance(bad, list) else [bad]
        assert not term_accepts(t, *bad), (t.key, "a bad value")
        for a in t.absent:
            assert term_accepts(t, a), (t.key, a)
        if t.absent and t.spelling not in ("slot", "text", "iri"):
            assert not term_accepts(t, "an absence word the row does not have"), t.key


def test_a_many_term_takes_several_values_and_a_single_valued_one_takes_one():
    for t in V.TERMS:
        two = {"integer": [1, 2], "size": ["1", "2"], "digest": ["a" * 64, "b" * 64], "commit": ["a" * 40, "b" * 40],
               "rational": ["1/2", "1/3"], "binary64": [S.binary64(0.5), S.binary64(0.25)], "time": ["2026-10-14T00:00:00Z",
                                                                                                      "2026-10-15T00:00:00Z"],
               "date": ["2026-10-14", "2026-10-15"], "text": ["x", "y"], "iri": ["https://a.org/x", "https://b.org/x"],
               "ref": [{"@id": "https://a.org/x"}, {"@id": "https://b.org/x"}]}.get(t.spelling)
        if t.spelling.startswith("word:"):
            two = list(V.WORDS[t.spelling[5:]])[:2]
        if two is None or len(two) < 2:
            continue
        assert term_accepts(t, *two) == t.many, (t.key, t.many)


def test_an_empty_term_has_no_value_to_refuse():
    t = V.TERM["sha256"]
    shape = next(s for s in H.build() if s.id == H.shape_iri("term-sha256"))
    assert not p4_eval.property_reasons(p4_eval.Graph([("urn:s", "urn:other", "urn:o")]), shape.props[0], "urn:s")
    assert t and isinstance(shape.props[0], Shape)
