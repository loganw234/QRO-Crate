"""The in-process evaluator (qro/p4_eval.py), held to this repository's reading of the SHACL Recommendation: every
micro case of p4_cases.py (one per constraint component and outcome) with the failing focus nodes written beside it;
the graph's indexes; the report's shape; and the two bugs the evaluator's prototype had, as plants. The same cases are
held to a real engine in the stage tests/p4shacl/, which is where a reading of mine that is wrong shows."""
import pytest
from p4_cases import BLANK, CASES, EX, MAX, P, Q, T1, A, B, C, Z
from qro import p4_eval as V
from qro.p4_model import RDF_TYPE, XSD, XSD_DOUBLE, XSD_INTEGER, XSD_STRING, BNode, Lit, Shape, inv, one_or_more


@pytest.mark.parametrize("c", CASES, ids=[c.name for c in CASES])
def test_the_case_fails_where_the_recommendation_says(c):
    got = V.failing_pairs(V.validate(c.shapes, c.data))
    assert got == sorted(c.fails), (c.name, got)


def test_there_is_a_case_for_every_component_of_the_model():
    components = {c.component for c in CASES}
    assert components >= {"datatype", "bounds", "pattern", "length", "in", "nodeKind", "class", "count", "hasValue",
                          "closed", "or", "not", "path", "target", "level", "several"}
    assert len(CASES) >= 120 and len({c.name for c in CASES}) == len(CASES)


def test_every_kind_of_target_and_every_kind_of_path_has_a_case_that_fails_and_one_that_conforms():
    for kind in ("a class", "subjects of a property", "objects of a property", "a node the graph holds"):
        assert any(c.component == "target" and kind in c.name for c in CASES), kind
    assert any(c.fails for c in CASES if c.component == "path" and "inverse" in c.name)
    assert any(not c.fails for c in CASES if c.component == "path" and "inverse" in c.name)
    assert any(not c.fails for c in CASES if c.component == "path" and "reached" in c.name)


# -- the graph -------------------------------------------------------------------------------------------------------------
def test_the_graph_indexes_subjects_objects_instances_and_values_in_a_fixed_order():
    g = V.Graph([(B, P, Lit("2")), (A, P, Lit("1")), (A, RDF_TYPE, T1), (A, Q, B), (BLANK, P, Lit("1"))])
    assert list(g.subjects_of[P]) == [A, B, BLANK] and list(g.objects_of[P]) == [Lit("1"), Lit("2")]
    assert list(g.instances[T1]) == [A] and g.values(A, P) == [Lit("1")] and g.values(A, inv(P)) == []
    assert g.values(Lit("1"), inv(P)) == [A, BLANK] and g.values(B, inv(Q)) == [A]
    assert g.is_a(A, T1) and not g.is_a(B, T1) and not g.is_a(Lit("x"), T1)
    assert g.types(A) == [T1] and g.types(Z) == []


def test_asking_for_a_node_the_graph_does_not_hold_adds_it_to_nothing():
    """The prototype's first bug: a dict that grew a key as it was read, so every node later became a target."""
    g = V.Graph([(A, P, Lit("x"))])
    before = (set(g.sp), set(g.po), {k: list(v) for k, v in g.subjects_of.items()})
    for node in (Z, Lit("y"), BLANK):
        assert g.values(node, P) == [] and g.values(node, inv(P)) == [] and g.values(node, one_or_more(P)) == []
        assert g.types(node) == []
    assert (set(g.sp), set(g.po), {k: list(v) for k, v in g.subjects_of.items()}) == before
    shape = Shape(id="urn:s", targets=(("subjectsOf", P),), props=(Shape(path=Q, min_count=1),))
    assert [r.focus for r in V.validate([shape], g)] == [A]


def test_a_path_one_step_or_more_visits_each_node_once_and_ends_in_a_cycle():
    g = V.Graph([(A, P, B), (B, P, C), (C, P, A), (C, P, Z)])
    assert sorted(g.values(A, one_or_more(P)), key=V.node_key) == [A, B, C, Z]
    assert g.values(Z, one_or_more(P)) == []
    assert sorted(g.values(Z, one_or_more(inv(P))), key=V.node_key) == [A, B, C]


def test_an_inverse_of_a_path_that_is_not_one_predicate_is_refused():
    g = V.Graph([(A, P, B)])
    with pytest.raises(ValueError, match="one predicate"):
        g.values(A, inv(one_or_more(P)))


def test_terms_are_ordered_by_kind_then_text_so_that_nothing_depends_on_the_hosts_hash_seed():
    nodes = [Lit("b"), BNode(2), B, Lit("a", XSD_INTEGER), BNode(10), A, Lit("a"), Lit("b", XSD_INTEGER)]
    ordered = sorted(nodes, key=V.node_key)
    # the text first (a string of datatype integer sorts after a string of datatype string, if the datatype came first),
    # and the same text by datatype
    assert ordered == [A, B, BNode(2), BNode(10), Lit("a", XSD_INTEGER), Lit("a"), Lit("b", XSD_INTEGER), Lit("b")]


def test_the_focus_nodes_of_a_shape_with_several_targets_are_each_once_and_in_the_one_order():
    g = V.Graph([(B, P, Lit("1")), (C, P, Lit("1")), (A, Q, Lit("1")), (Z, RDF_TYPE, T1)])
    shape = Shape(id="urn:s", targets=(("subjectsOf", P), ("subjectsOf", Q), ("class", T1), ("node", A)))
    assert V.focus_nodes(g, shape) == [A, B, C, Z]


# -- the helpers the components use ------------------------------------------------------------------------------------------
def test_a_string_is_an_iri_or_a_lexical_form_and_a_blank_node_has_none():
    assert V.string_of(A) == A and V.string_of(Lit("x")) == "x" and V.string_of(Lit("5", XSD_INTEGER)) == "5"
    assert V.string_of(BLANK) is None


@pytest.mark.parametrize("lit, ok", [
    (Lit("5", XSD_INTEGER), True), (Lit("-5", XSD_INTEGER), True), (Lit("+5", XSD_INTEGER), True),
    (Lit("5.0", XSD_INTEGER), False), (Lit("", XSD_INTEGER), False), (Lit("5 ", XSD_INTEGER), False),
    (Lit("٥", XSD_INTEGER), False), (Lit("true", XSD + "boolean"), True), (Lit("1", XSD + "boolean"), True),
    (Lit("yes", XSD + "boolean"), False), (Lit("5.5", XSD + "decimal"), True), (Lit(".5", XSD + "decimal"), True),
    (Lit("5.", XSD + "decimal"), True), (Lit("5e1", XSD + "decimal"), False), (Lit("5.0E0", XSD_DOUBLE), True),
    (Lit("-INF", XSD_DOUBLE), True), (Lit("NaN", XSD_DOUBLE), True), (Lit("inf", XSD_DOUBLE), False),
    (Lit("x", XSD_STRING), True), (Lit("anything", XSD + "token"), True)])
def test_a_literal_is_well_formed_for_its_datatype(lit, ok):
    assert V.well_formed(lit) is ok


def test_a_number_is_a_well_formed_integer_decimal_or_double_and_nothing_else():
    assert V.number(Lit("7", XSD_INTEGER)) == 7 and V.number(Lit("5.5", XSD + "decimal")) == V.Fraction(11, 2)
    assert V.number(Lit("2.5E0", XSD_DOUBLE)) == 2.5 and V.number(Lit("INF", XSD_DOUBLE)) == float("inf")
    for none in (Lit("NaN", XSD_DOUBLE), Lit("x"), Lit("x", XSD_INTEGER), A, BLANK, Lit("true", XSD + "boolean")):
        assert V.number(none) is None


# -- the report -------------------------------------------------------------------------------------------------------------
def test_a_result_has_the_shape_the_level_the_focus_node_and_a_reason_and_the_report_is_in_a_fixed_order():
    s1 = Shape(id="urn:b", level="should", targets=(("subjectsOf", P),), props=(Shape(path=P, max_count=1),))
    s2 = Shape(id="urn:a", targets=(("subjectsOf", P),), node_kind="IRI")
    data = [(A, P, Lit("1")), (A, P, Lit("2")), (BLANK, P, Lit("1"))]
    results = V.validate([s1, s2], data)
    assert [(r.shape, r.level, r.focus) for r in results] == [("urn:b", "should", A), ("urn:a", "must", BLANK)]
    assert all(r.reason for r in results)
    assert V.failing(results) == ["urn:a", "urn:b"] and V.failing(results, "must") == ["urn:a"]
    assert V.failing(results, "should") == ["urn:b"] and V.failing(results, "may") == []
    assert V.failing_pairs(results) == [("urn:a", "_:blank"), ("urn:b", A)]
    assert V.failing_pairs(results, "must") == [("urn:a", "_:blank")] and V.failing_pairs(results, "should") == [("urn:b", A)]
    assert V.failing_pairs(results, "may") == []
    assert V.validate([s1, s2], list(reversed(data))) == results


def test_a_focus_node_is_named_as_the_engine_runner_names_it():
    assert V.focus_name(A) == A and V.focus_name(BLANK) == "_:blank" and V.focus_name(Lit("lexical", XSD_INTEGER)) == "lexical"


def test_validate_takes_a_graph_or_triples():
    shape = Shape(id="urn:s", targets=(("subjectsOf", P),), node_kind="IRI")
    data = [(BLANK, P, B)]
    assert V.validate([shape], V.Graph(data)) == V.validate([shape], data) == V.validate([shape], iter(data))


# -- the prototype's two bugs, and what a reading of the Recommendation could get wrong ------------------------------------------------
def test_a_bound_compares_a_number_and_a_string_of_digits_is_not_one():
    """The prototype read "5" as 5 and let a string through the bounds; the Recommendation does not compare them."""
    s = Shape(id="urn:s", targets=(("subjectsOf", P),), props=(Shape(path=P, min_inclusive=0, max_inclusive=MAX),))
    assert V.validate([s], [(A, P, Lit("5"))]) and not V.validate([s], [(A, P, Lit("5", XSD_INTEGER))])


def test_a_pattern_searches_and_the_end_anchor_lets_one_trailing_line_feed_by():
    """Python's and an XPath engine's `$` differ here; the shapes that matter close it with a length (qro/p4_shapes.py)."""
    s = Shape(id="urn:s", targets=(("subjectsOf", P),), props=(Shape(path=P, pattern="^ab$"),))
    assert not V.validate([s], [(A, P, Lit("ab\n"))]) and V.validate([s], [(A, P, Lit("ab\n\n"))])
    capped = Shape(id="urn:s", targets=(("subjectsOf", P),), props=(Shape(path=P, pattern="^ab$", max_length=2),))
    assert V.validate([capped], [(A, P, Lit("ab\n"))])


def test_a_blank_node_value_violates_a_pattern_a_length_and_a_bound_alike():
    for kw in ({"pattern": ".*"}, {"min_length": 0}, {"max_length": 99}, {"min_inclusive": 0}, {"max_inclusive": 9}):
        s = Shape(id="urn:s", targets=(("subjectsOf", P),), props=(Shape(path=P, **kw),))
        assert V.validate([s], [(A, P, BLANK)]), kw


def test_a_class_is_met_by_the_rdf_type_triples_alone():
    s = Shape(id="urn:s", targets=(("subjectsOf", P),), props=(Shape(path=P, classes=(T1,)),))
    assert V.validate([s], [(A, P, B), (B, EX + "subClassTypeOf", T1)]) and not V.validate([s], [(A, P, B), (B, RDF_TYPE, T1)])
