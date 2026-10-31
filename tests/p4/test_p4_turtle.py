"""The Turtle writer (qro/p4_turtle.py): every construct of the model as the text it must be, so that the file an engine
reads is the shape the evaluator judges by. A golden text for a shape that uses everything; each escape; the severity a
property shape carries and the shapes that carry none; what the writer refuses. An engine reads this Turtle in the
stage tests/p4shacl/, which is where its meaning is held; here its text is."""
import re

import pytest

from qro import p4_turtle as T
from qro.p4_model import RDF, RDF_TYPE, SH, XSD, XSD_BOOLEAN, XSD_INTEGER, XSD_STRING, BNode, Lit, Shape, inv, one_or_more

EX = "http://example.org/"
PREFIXES = (("sh", SH), ("rdf", RDF), ("xsd", XSD), ("ex", EX), ("qs", EX + "s#"))
W = T.Writer(PREFIXES)

EVERYTHING = Shape(
    id=EX + "s#a", name='A "name"', description="d é", message="m", level="should", claims=("one", "two"),
    kind="CHECKED", targets=(("class", EX + "T"), ("subjectsOf", EX + "p"), ("objectsOf", EX + "q"), ("node", EX + "n")),
    node_kind="IRI", classes=(EX + "C",), closed=True, ignored=(RDF_TYPE, EX + "p"),
    props=(Shape(path=EX + "p", min_count=1, max_count=2, pattern="^a\\s$", datatype=XSD_STRING,
                 in_=(Lit("x"), Lit("5", XSD_INTEGER), Lit("true", XSD_BOOLEAN), Lit("1.5", XSD + "decimal"), EX + "i"),
                 has_value=(Lit("v"),)),
           Shape(path=inv(EX + "p"), min_length=1, max_length=3, min_inclusive=0, max_inclusive=9),
           Shape(path=one_or_more(inv(EX + "p")), qvs=((Shape(props=(Shape(path=EX + "q", min_count=1),)), 1),))),
    or_=(Shape(classes=(EX + "A",)), Shape(in_=())), not_=(Shape(datatype=XSD_INTEGER),))

GOLDEN = '''qs:a
    a sh:NodeShape ;
    sh:name "A \\"name\\"" ;
    sh:description "d \\u00e9" ;
    sh:message "m" ;
    sh:severity sh:Warning ;
    qs:claims "one", "two" ;
    qs:kind "CHECKED" ;
    sh:targetClass ex:T ;
    sh:targetSubjectsOf ex:p ;
    sh:targetObjectsOf ex:q ;
    sh:targetNode ex:n ;
    sh:nodeKind sh:IRI ;
    sh:class ex:C ;
    sh:closed true ;
    sh:ignoredProperties ( rdf:type ex:p ) ;
    sh:or (
        [
            sh:class ex:A
        ]
        [
            sh:in ( )
        ]
    ) ;
    sh:not [
        sh:datatype xsd:integer
    ] ;
    sh:property [
        sh:path ex:p ;
        sh:severity sh:Warning ;
        sh:datatype xsd:string ;
        sh:in ( "x" 5 true "1.5"^^xsd:decimal ex:i ) ;
        sh:hasValue "v" ;
        sh:pattern "^a\\\\s$" ;
        sh:minCount 1 ;
        sh:maxCount 2
    ] ;
    sh:property [
        sh:path [ sh:inversePath ex:p ] ;
        sh:severity sh:Warning ;
        sh:minLength 1 ;
        sh:maxLength 3 ;
        sh:minInclusive 0 ;
        sh:maxInclusive 9
    ] ;
    sh:property [
        sh:path [ sh:oneOrMorePath [ sh:inversePath ex:p ] ] ;
        sh:severity sh:Warning ;
        sh:qualifiedValueShape [
            sh:property [
                sh:path ex:q ;
                sh:minCount 1
            ]
        ] ;
        sh:qualifiedMinCount 1
    ] .'''


def test_a_shape_that_uses_every_construct_is_this_text():
    assert W.shape(EVERYTHING) == GOLDEN


def test_a_file_is_a_banner_the_prefixes_then_a_statement_a_shape_with_a_blank_line_before_each():
    shapes = [Shape(id=EX + "s#one", targets=(("class", EX + "T"),)), Shape(id=EX + "s#two", node_kind="IRI")]
    text = T.render(shapes, PREFIXES, ["first line", "", "third"])
    assert text == (
        "# first line\n#\n# third\n"
        f"@prefix sh: <{SH}> .\n@prefix rdf: <{RDF}> .\n@prefix xsd: <{XSD}> .\n@prefix ex: <{EX}> .\n"
        f"@prefix qs: <{EX}s#> .\n"
        "\nqs:one\n    a sh:NodeShape ;\n    sh:severity sh:Violation ;\n    sh:targetClass ex:T .\n"
        "\nqs:two\n    a sh:NodeShape ;\n    sh:severity sh:Violation ;\n    sh:nodeKind sh:IRI .\n")


def test_a_top_level_shape_with_a_path_is_a_property_shape():
    text = W.shape(Shape(id=EX + "s#p", path=EX + "p", min_count=1, targets=(("class", EX + "T"),)))
    assert text.splitlines()[:3] == ["qs:p", "    a sh:PropertyShape ;", "    sh:path ex:p ;"]


# -- the severity: on every property shape that reports, on nothing nested in an alternative ------------------------------
@pytest.mark.parametrize("level, word", [("must", "Violation"), ("should", "Warning"), ("may", "Info")])
def test_each_level_is_its_severity_on_the_shape_and_on_every_property_shape_it_holds(level, word):
    shape = Shape(id=EX + "s#a", level=level, props=(Shape(path=EX + "p", min_count=1), Shape(path=EX + "q",
                                                                                                 min_count=1)))
    text = W.shape(shape)
    assert text.count(f"sh:severity sh:{word}") == 3 and "sh:severity" in text.splitlines()[2]
    assert not {"Violation", "Warning", "Info"} - {word} & set(re.findall(r"sh:severity sh:(\w+)", text))


def test_a_shape_nested_in_an_alternative_a_negation_or_a_qualified_value_shape_carries_no_severity():
    inner = Shape(props=(Shape(path=EX + "p", min_count=1),))
    shape = Shape(id=EX + "s#a", or_=(inner,), not_=(inner,), qvs=((inner, 1),), props=(Shape(path=EX + "q", max_count=1),))
    text = W.shape(shape)
    assert re.findall(r"sh:severity sh:(\w+)", text) == ["Violation", "Violation"]       # the shape, and the one property
    assert len(re.findall(r"sh:path ex:p ;\n\s+sh:minCount 1\n", text)) == 3             # in each of the three: no severity


def test_a_message_is_written_on_the_shapes_that_report_and_nowhere_else():
    inner = Shape(props=(Shape(path=EX + "p", message="inside"),), message="not written")
    shape = Shape(id=EX + "s#a", message="top", or_=(inner,), props=(Shape(path=EX + "q", message="property"),))
    text = W.shape(shape)
    assert 'sh:message "top"' in text and 'sh:message "property"' in text
    assert "inside" not in text and "not written" not in text


def test_the_name_the_description_and_the_annotations_are_a_named_shapes_alone():
    nested = Shape(path=EX + "p", name="nested name", description="nested description", claims=("x",), kind="READ")
    text = W.shape(Shape(id=EX + "s#a", props=(nested,)))
    assert "sh:name" not in text and "sh:description" not in text and "qs:claims" not in text and "qs:kind" not in text


# -- the names: prefixes, escapes and the literals ---------------------------------------------------------------------
def test_an_iri_is_the_longest_prefix_that_fits_and_else_in_angle_brackets():
    w = T.Writer((("a", EX), ("b", EX + "deep/")))
    assert w.iri(EX + "deep/x") == "b:x" and w.iri(EX + "x") == "a:x" and w.iri(EX + "deep/") == "<" + EX + "deep/>"
    for odd in ("1abc", "a.b", "a/b", "a:b", "", "-a"):
        assert w.iri(EX + odd) == f"<{EX}{odd}>", odd
    assert w.iri("urn:other") == "<urn:other>"
    nested = T.Writer((("a", EX), ("b", EX + "deep")))                  # both fit: the longer base is the one written
    assert nested.iri(EX + "deepx") == "b:x" and nested.iri(EX + "deep") == "a:deep" and nested.iri(EX + "dee") == "a:dee"
    assert T.Writer((("b", EX), ("a", EX))).iri(EX + "x") == "a:x"      # one base twice: the name that sorts first


@pytest.mark.parametrize("bad", [EX + "a b", EX + "a<b", EX + 'a"b', EX + "a{b", EX + "a}b", EX + "a|b", EX + "a^b",
                                 EX + "a`b", EX + "a\\b", EX + "a\tb", EX + "a\nb", EX + "café", EX + "a\x7fb"])
def test_an_iri_that_cannot_be_written_whole_is_refused_never_written_wrong(bad):
    with pytest.raises(ValueError):
        W.iri(bad)
    with pytest.raises(ValueError):
        T.node(bad)


@pytest.mark.parametrize("raw, written", [
    ("plain", '"plain"'), ('a"b', '"a\\"b"'), ("a\\b", '"a\\\\b"'), ("a\nb", '"a\\nb"'), ("a\tb", '"a\\tb"'),
    ("a\rb", '"a\\rb"'), ("\x00", '"\\u0000"'), ("\x1f", '"\\u001f"'), ("\x7f", '"\\u007f"'), ("é", '"\\u00e9"'),
    ("中", '"\\u4e2d"'), ("\U0001f600", '"\\U0001f600"'), ("\ud800", '"\\ud800"'), ("", '""'), (" ", '" "'),
    ("~", '"~"')])
def test_a_string_is_written_in_ascii_with_each_character_escaped_the_one_way(raw, written):
    assert T.escape(raw) == written and T.escape(raw).isascii()


def test_a_literal_is_written_by_its_datatype():
    assert W.literal(Lit("x")) == '"x"' and W.literal(Lit("5", XSD_INTEGER)) == "5"
    assert W.literal(Lit("-5", XSD_INTEGER)) == "-5" and W.literal(Lit("true", XSD_BOOLEAN)) == "true"
    assert W.literal(Lit("abc", XSD_INTEGER)) == '"abc"^^xsd:integer'
    assert W.literal(Lit("1", XSD_BOOLEAN)) == '"1"^^xsd:boolean'
    assert W.literal(Lit("x", "urn:t")) == '"x"^^<urn:t>'
    assert W.term(EX + "a") == "ex:a"
    with pytest.raises(ValueError):
        W.term(BNode(1))


def test_a_path_is_one_predicate_its_inverse_or_one_step_of_either_or_more():
    assert W.path(EX + "p") == "ex:p" and W.path(inv(EX + "p")) == "[ sh:inversePath ex:p ]"
    assert W.path(one_or_more(EX + "p")) == "[ sh:oneOrMorePath ex:p ]"
    assert W.path(one_or_more(inv(EX + "p"))) == "[ sh:oneOrMorePath [ sh:inversePath ex:p ] ]"
    with pytest.raises(ValueError):
        W.path(("zeroOrMore", EX + "p"))


def test_a_prefix_declared_twice_is_refused():
    with pytest.raises(ValueError, match="twice"):
        T.Writer((("a", EX), ("a", EX + "x/")))


# -- what render refuses --------------------------------------------------------------------------------------------------
def test_render_refuses_an_incoherent_shape_two_shapes_of_one_id_and_a_banner_that_is_not_a_line_of_ascii():
    ok = Shape(id=EX + "s#a")
    with pytest.raises(ValueError, match="level shall"):
        T.render([Shape(id=EX + "s#a", level="shall")], PREFIXES, [])
    with pytest.raises(ValueError, match="share an id"):
        T.render([ok, ok], PREFIXES, [])
    for banner in (["two\nlines"], ["café"]):
        with pytest.raises(ValueError, match="banner"):
            T.render([ok], PREFIXES, banner)


def test_the_text_is_ascii_with_lf_line_ends_and_no_tab_and_the_same_text_twice():
    a, b = T.render([EVERYTHING], PREFIXES, ["x"]), T.render([EVERYTHING], PREFIXES, ["x"])
    assert a == b and a.isascii() and "\r" not in a and "\t" not in a and a.endswith("\n") and not a.endswith("\n\n")


# -- N-Triples, for the data a micro case hands an engine --------------------------------------------------------------------
def test_a_term_in_n_triples():
    assert T.node(EX + "a") == f"<{EX}a>" and T.node(BNode(7)) == "_:b7"
    assert T.node(Lit("x")) == '"x"' and T.node(Lit("5", XSD_INTEGER)) == f'"5"^^<{XSD_INTEGER}>'
    assert T.node(Lit('q"\né')) == '"q\\"\\n\\u00e9"'
    with pytest.raises(TypeError):
        T.node(5)


def test_n_triples_are_sorted_one_to_a_line_and_end_in_a_line_feed():
    triples = [(EX + "b", EX + "p", Lit("2")), (EX + "a", EX + "p", Lit("1")), (EX + "a", EX + "p", EX + "z")]
    text = T.ntriples(triples)
    assert text.splitlines() == sorted(text.splitlines()) and len(text.splitlines()) == 3 and text.endswith(" .\n")
    assert text == T.ntriples(reversed(triples)) and T.ntriples([]) == ""
