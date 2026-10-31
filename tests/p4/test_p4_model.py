"""P4's shape model (qro/p4_model.py): the data the Turtle writer and the evaluator both read. What it holds: the terms
of a graph told apart, a shape's fields and their coherence, and each way a shape can be incoherent, planted."""
import pytest

from qro import p4_model as M
from qro.p4_model import BNode, Lit, Shape, inv, one_or_more

P = "http://example.org/p"


def test_a_literal_is_its_lexical_form_and_its_datatype():
    assert Lit("x") == Lit("x", M.XSD_STRING) and Lit("5", M.XSD_INTEGER) != Lit("5")
    assert Lit("5", M.XSD_INTEGER) != Lit("05", M.XSD_INTEGER)
    assert hash(Lit("x")) == hash(Lit("x", M.XSD_STRING))
    with pytest.raises(AttributeError):
        Lit("x").lexical = "y"


def test_a_blank_node_is_told_apart_by_its_number_alone():
    assert BNode(1) == BNode(1) and BNode(1) != BNode(2) and BNode(1) != "_:b1" and BNode(1) != Lit("1")
    assert len({BNode(1), BNode(1), BNode(2)}) == 2 and repr(BNode(3)) == "_:b3"


def test_the_levels_have_each_a_severity_and_no_other():
    assert M.LEVELS == ("must", "should", "may")
    assert M.SEVERITY == {"must": "Violation", "should": "Warning", "may": "Info"}


@pytest.mark.parametrize("iri", ["urn:a", "http://example.org/a?b=c#d", "a", "~", "!", "a" + chr(0x7e), "a-b_c.d"])
def test_an_iri_that_may_stand_between_angle_brackets_as_it_is_written(iri):
    assert M.iri_ok(iri)


@pytest.mark.parametrize("iri", ["", None, 5, b"x", "a b", "a<b", "a>b", 'a"b', "a{b", "a}b", "a|b", "a^b", "a`b",
                                 "a" + chr(92) + "b", "a" + chr(0) + "b", "a" + chr(9) + "b", "a" + chr(0x1f) + "b",
                                 "a" + chr(0x20), "a" + chr(0x7f) + "b", "caf" + chr(0xe9), chr(0x10ffff)])
def test_an_iri_that_is_empty_not_a_string_or_holds_a_character_turtle_or_ascii_forbids_is_not_ok(iri):
    assert not M.iri_ok(iri)


def test_the_paths_the_model_has():
    assert M.direct(P) and not M.direct(inv(P)) and not M.direct(one_or_more(P))
    for good in (P, inv(P), one_or_more(P), one_or_more(inv(P))):
        assert M.path_ok(good), good
    for bad in (("inv", inv(P)), ("oneOrMore", one_or_more(P)), ("sequence", P), ("inv",), None, 5, ("inv", 5),
                one_or_more(("oneOrMore", P))):
        assert not M.path_ok(bad), bad


def test_a_shape_that_holds_nothing_is_coherent_and_a_node_shape_when_it_has_no_path():
    assert M.problems(Shape(id="urn:s")) == []
    assert Shape().path is None and Shape().level == "must" and Shape().in_ is None and Shape().targets == ()


def test_every_shape_in_a_tree_is_walked_depth_first_in_the_order_the_writer_nests_them():
    leaf, forbidden, counted = Shape(pattern="x"), Shape(datatype="urn:d"), Shape(node_kind="IRI")
    prop = Shape(path=P, or_=(leaf,))
    tree = Shape(id="urn:s", props=(prop,), not_=(forbidden,), qvs=((counted, 1),))
    walked = list(M.walk(tree))
    assert len(walked) == 5
    assert all(a is b for a, b in zip(walked, [tree, prop, leaf, forbidden, counted]))


# -- each incoherence, planted ------------------------------------------------------------------------------------------
INCOHERENT = [
    ("a level outside the three", Shape(id="urn:s", level="shall"), "level shall"),
    ("a shape that stands alone without an id", Shape(), "needs an id"),
    ("a target of a kind the model does not have", Shape(id="urn:s", targets=(("everything", P),)), "target everything"),
    ("a target that is not an IRI", Shape(id="urn:s", targets=(("class", 5),)), "target class"),
    ("a node kind the model does not have", Shape(id="urn:s", node_kind="Literal"), "node kind Literal"),
    ("a count on a node shape", Shape(id="urn:s", min_count=1), "needs a path"),
    ("a maximum count on a node shape", Shape(id="urn:s", max_count=1), "needs a path"),
    ("a qualified value shape on a node shape", Shape(id="urn:s", qvs=((Shape(), 1),)), "needs a path"),
    ("a path the model does not have", Shape(id="urn:s", path=("sequence", P)), "path the model does not have"),
    ("a property shape with a target of its own", Shape(id="urn:s", path=P, targets=(("class", P),)),
     "no target of its own"),
    ("a pattern in more than ASCII", Shape(id="urn:s", pattern="café"), "printable ASCII"),
    ("an ignored property that is not an IRI", Shape(id="urn:s", closed=True, ignored=(5,)), "ignored property"),
    ("ignored properties without sh:closed", Shape(id="urn:s", ignored=(P,)), "without sh:closed"),
    ("a nested shape with an id", Shape(id="urn:s", props=(Shape(id="urn:t", path=P),)), "nameless"),
    ("a nested shape with a target", Shape(id="urn:s", props=(Shape(path=P, targets=(("class", P),)),)),
     "nameless"),
    ("sh:property of a shape with no path", Shape(id="urn:s", props=(Shape(),)), "has no path"),
    ("a qualified value shape that is a property shape", Shape(id="urn:s", path=P, qvs=((Shape(path=P), 1),)),
     "a node shape"),
    ("a qualified minimum of none", Shape(id="urn:s", path=P, qvs=((Shape(), 0),)), "minimum of one"),
    ("an alternative that is a property shape", Shape(id="urn:s", or_=(Shape(path=P),)), "a node shape"),
    ("a shape sh:not forbids that is a property shape", Shape(id="urn:s", not_=(Shape(path=P),)), "a node shape"),
]


@pytest.mark.parametrize("why, shape, text", INCOHERENT, ids=[w for w, _, _ in INCOHERENT])
def test_each_incoherent_shape_is_named(why, shape, text):
    found = M.problems(shape)
    assert found and any(text in f for f in found), found


def test_a_problem_deep_in_a_tree_is_found_and_names_the_shape_that_holds_it():
    deep = Shape(id="urn:outer", props=(Shape(path=P, or_=(Shape(level="shall"),)),))
    found = M.problems(deep)
    assert len(found) == 1 and "level shall" in found[0]
