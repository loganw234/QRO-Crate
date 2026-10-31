"""The JSON-LD expansion (qro/p4_expand.py): a QRO crate's metadata as triples. What it makes of the fixture, each form
of value, key, type and id it reads, and each it refuses (an ExpandError, never a guess). The engine stage holds the
triples equal to rdflib's, crate by crate; here it is held to the rules the module states."""
import copy
import json

import pytest

from qro import fixture
from qro import p4_expand as E
from qro import vocabulary as V
from qro.p4_model import RDF_TYPE, XSD_INTEGER, BNode, Lit

SCHEMA = "http://schema.org/"


@pytest.fixture(scope="module")
def fixture_md(tmp_path_factory):
    crate = fixture.make(tmp_path_factory.mktemp("fx") / "crate")
    return json.loads((crate / "ro-crate-metadata.json").read_bytes())


def md_with(base, *entities):
    md = copy.deepcopy(base)
    md["@graph"].extend(copy.deepcopy(list(entities)))
    return md


def triples(entity, base):
    return set(E.expand(md_with(base, entity))) - set(E.expand(base))


# -- the fixture ------------------------------------------------------------------------------------------------------
def test_the_fixture_is_these_triples(fixture_md):
    t = set(E.expand(fixture_md))
    root, desc, notes, raw = E.BASE, E.BASE + "ro-crate-metadata.json", E.BASE + "data/notes.txt", E.BASE + "data/raw.counts.json"
    assert (root, RDF_TYPE, SCHEMA + "Dataset") in t and (desc, RDF_TYPE, SCHEMA + "CreativeWork") in t
    assert (desc, SCHEMA + "about", root) in t and (desc, "http://purl.org/dc/terms/conformsTo", V.ROCRATE) in t
    assert {(root, SCHEMA + "hasPart", notes), (root, SCHEMA + "hasPart", raw)} <= t
    assert {(raw, RDF_TYPE, SCHEMA + "MediaObject"), (raw, RDF_TYPE, V.NAMESPACE + "RawResult")} <= t
    assert (raw, V.NAMESPACE + "shots", Lit("8", XSD_INTEGER)) in t
    assert (raw, V.NAMESPACE + "rawForm", Lit("qro-fixture-counts")) in t
    assert (root, SCHEMA + "license", "https://creativecommons.org/licenses/by/4.0/") in t
    for want in V.profile_entities():
        assert (want["@id"], SCHEMA + "version", Lit(want["version"])) in t
        assert (want["@id"], RDF_TYPE, "http://www.w3.org/ns/dx/prof/Profile") in t
        assert (want["@id"], RDF_TYPE, SCHEMA + "CreativeWork") in t
    assert len(t) == len(E.expand(fixture_md)) == 36
    assert E.expand(fixture_md) == E.expand(copy.deepcopy(fixture_md))


def test_the_expansion_makes_no_blank_node_of_a_crate_whose_entities_have_ids(fixture_md):
    assert not any(isinstance(x, BNode) for t in E.expand(fixture_md) for x in t)


def test_the_base_is_a_file_iri_ending_in_a_slash_because_the_digest_shape_reads_a_path_in_the_crate_from_it():
    assert E.BASE == "file:///crate/" and E.BASE.startswith("file:") and E.BASE.endswith("/")


# -- values ------------------------------------------------------------------------------------------------------------
def test_a_string_a_whole_number_a_reference_and_a_list_of_them_are_read(fixture_md):
    got = triples({"@id": "#x", "@type": "CreativeWork", "name": "n", "qro:shots": 5,
                   "hasPart": [{"@id": "a/b"}, {"@id": "https://example.org/z"}]}, fixture_md)
    x = E.BASE + "#x"
    assert got == {(x, RDF_TYPE, SCHEMA + "CreativeWork"), (x, SCHEMA + "name", Lit("n")),
                   (x, V.NAMESPACE + "shots", Lit("5", XSD_INTEGER)), (x, SCHEMA + "hasPart", E.BASE + "a/b"),
                   (x, SCHEMA + "hasPart", "https://example.org/z")}


@pytest.mark.parametrize("value", [1.5, True, False, None, {"@value": "x"}, {"@id": "a", "name": "b"}, {},
                                   [[1]], [{"@list": []}], ["a", None]])
def test_a_value_the_reader_does_not_admit_is_refused_never_dropped(fixture_md, value):
    with pytest.raises(E.ExpandError):
        E.expand(md_with(fixture_md, {"@id": "#x", "@type": "CreativeWork", "name": value}))


def test_a_negative_and_a_very_large_integer_are_read_as_they_are(fixture_md):
    got = triples({"@id": "#x", "@type": "CreativeWork", "qro:shots": -1}, fixture_md)
    assert (E.BASE + "#x", V.NAMESPACE + "shots", Lit("-1", XSD_INTEGER)) in got
    got = triples({"@id": "#x", "@type": "CreativeWork", "qro:shots": 2 ** 70}, fixture_md)
    assert (E.BASE + "#x", V.NAMESPACE + "shots", Lit(str(2 ** 70), XSD_INTEGER)) in got


def test_an_empty_list_makes_no_triple(fixture_md):
    assert triples({"@id": "#x", "@type": "CreativeWork", "hasPart": []}, fixture_md) == {
        (E.BASE + "#x", RDF_TYPE, SCHEMA + "CreativeWork")}


# -- keys ----------------------------------------------------------------------------------------------------------------
def test_a_key_is_a_term_of_the_context_a_qro_name_a_compact_iri_or_an_absolute_one_and_else_dropped(fixture_md):
    got = triples({"@id": "#x", "@type": "CreativeWork", "madeUp": "gone", "schema:name": "a", "dct:format": "b",
                   "qro:anything": "c", "urn:p:q": "d", "HTML": "e"}, fixture_md)
    x = E.BASE + "#x"
    assert got == {(x, RDF_TYPE, SCHEMA + "CreativeWork"), (x, SCHEMA + "name", Lit("a")),
                   (x, "http://purl.org/dc/terms/format", Lit("b")), (x, V.NAMESPACE + "anything", Lit("c")),
                   (x, "urn:p:q", Lit("d")), (x, "http://www.w3.org/1999/02/22-rdf-syntax-ns#HTML", Lit("e"))}


@pytest.mark.parametrize("key", ["@reverse", "@graph", "@included", "@nest", "@value", "@context", "@language"])
def test_a_keyword_the_expansion_does_not_read_is_refused(fixture_md, key):
    with pytest.raises(E.ExpandError, match="keyword"):
        E.expand(md_with(fixture_md, {"@id": "#x", "@type": "CreativeWork", key: "x"}))


@pytest.mark.parametrize("key", ["_:b", "1a:b", ":x", "a b:c"])
def test_a_key_with_a_colon_that_is_neither_a_scheme_nor_a_prefix_is_refused(fixture_md, key):
    with pytest.raises(E.ExpandError):
        E.expand(md_with(fixture_md, {"@id": "#x", "@type": "CreativeWork", key: "x"}))


# -- types -----------------------------------------------------------------------------------------------------------------
def test_a_type_is_a_term_a_compact_or_absolute_iri_or_else_relative_to_the_base(fixture_md):
    types = ["File", "MediaObject", "qro:Job", "schema:Thing", "urn:t:u", "Foo"]
    got = triples({"@id": "#x", "@type": types}, fixture_md)
    x = E.BASE + "#x"
    assert got == {(x, RDF_TYPE, SCHEMA + "MediaObject"), (x, RDF_TYPE, V.NAMESPACE + "Job"),
                   (x, RDF_TYPE, SCHEMA + "Thing"), (x, RDF_TYPE, "urn:t:u"), (x, RDF_TYPE, E.BASE + "Foo")}


@pytest.mark.parametrize("bad", [5, None, "", ["File", 5], {"a": 1}])
def test_a_type_that_is_no_string_is_refused(fixture_md, bad):
    with pytest.raises(E.ExpandError):
        E.expand(md_with(fixture_md, {"@id": "#x", "@type": bad}))


# -- ids --------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("given, iri", [
    ("./", E.BASE), ("data/a.json", E.BASE + "data/a.json"), ("d/", E.BASE + "d/"), ("#frag", E.BASE + "#frag"),
    ("a/b#c", E.BASE + "a/b#c"), ("x", E.BASE + "x"), ("a%20b", E.BASE + "a%20b"), ("a_(b)~c", E.BASE + "a_(b)~c"),
    ("https://example.org/x", "https://example.org/x"), ("urn:a:b", "urn:a:b"), ("foo:bar", "foo:bar"),
    ("http://h/p?q=1#f", "http://h/p?q=1#f"), ("qro:thing", V.NAMESPACE + "thing"),
    ("schema:Thing", SCHEMA + "Thing"), ("dct:conformsTo", "http://purl.org/dc/terms/conformsTo"),
    ("notes.txt:hidden", "notes.txt:hidden"), ("schema://example.org/x", "schema://example.org/x"),
    ("qro://h/p", "qro://h/p"), ("#a?b", E.BASE + "#a?b"), ("#a/b", E.BASE + "#a/b"), ("x#a?b", E.BASE + "x#a?b"),
    ("d/#a/b?c", E.BASE + "d/#a/b?c"), ("#a:b", E.BASE + "#a:b"), ("#:", E.BASE + "#:"), ("#a:b://c", E.BASE + "#a:b://c"),
    ("#schema:x", E.BASE + "#schema:x"), ("#_:b", E.BASE + "#_:b"), ("x;", E.BASE + "x;"), ("a;b.txt", E.BASE + "a;b.txt"),
    ("a/@b", E.BASE + "a/@b"), ("x;/", E.BASE + "x;/"), (";x", E.BASE + ";x"),
    ("https://Example.ORG/A/../b?Q#F", "https://Example.ORG/A/../b?Q#F"), ("urn:A:B", "urn:A:B"), ("http://x/?", "http://x/?"),
    ("http://x/#", "http://x/#"), ("tag:a#", "tag:a#"), ("https://u:p@h:80/%2e%2E/./x", "https://u:p@h:80/%2e%2E/./x")])
def test_an_id_is_compact_absolute_or_resolved_against_the_base(fixture_md, given, iri):
    assert E.iri_of_id(given) == iri
    got = E.expand(md_with(fixture_md, {"@id": given, "@type": "CreativeWork"}))
    assert (iri, RDF_TYPE, SCHEMA + "CreativeWork") in got


@pytest.mark.parametrize("given, why", [
    ("_:b0", "blank node"), ("//example.org/x", "does not resolve"), ("a/../b", "does not resolve"),
    ("a/./b", "does not resolve"), ("../a", "does not resolve"), ("a//b", "does not resolve"),
    ("a?q", "does not resolve"), ("x#", "does not resolve"), ("#", "does not resolve"), ("a b", "does not resolve"),
    ("file:///elsewhere/x", "file:"), ("FILE:///x", "file:"), ("file:x", "file:"), ("1a:b", "neither a scheme"),
    (":x", "neither a scheme"), ("a/b#c:d", "neither a scheme"), ("a:b c", "a space"), ("", "an @id is a string"), (5, "an @id is a string"),
    ("@x", "begins with @"), ("@", "begins with @"), ("@x/y", "begins with @"), ("@0", "begins with @"),
    (None, "an @id is a string"), ("/abs/path", "does not resolve"), ("a\\b", "does not resolve")])
def test_an_id_the_expansion_does_not_resolve_the_way_rdflib_does_is_refused(fixture_md, given, why):
    with pytest.raises(E.ExpandError, match=why):
        E.iri_of_id(given)
    with pytest.raises(E.ExpandError):
        E.expand(md_with(fixture_md, {"@id": given, "@type": "CreativeWork"}))


def test_a_reference_is_read_by_the_same_rules_as_an_id(fixture_md):
    for bad in ("_:b", "a/../b", "file:///x"):
        with pytest.raises(E.ExpandError):
            E.expand(md_with(fixture_md, {"@id": "#x", "@type": "CreativeWork", "hasPart": [{"@id": bad}]}))


def test_an_entity_without_an_id_is_a_numbered_blank_node(fixture_md):
    got = E.expand(md_with(fixture_md, {"@type": "CreativeWork", "name": "a"}, {"@type": "File", "name": "b"}))
    subjects = {t[0] for t in got if isinstance(t[0], BNode)}
    assert subjects == {BNode(1), BNode(2)}
    assert (BNode(1), SCHEMA + "name", Lit("a")) in got and (BNode(2), SCHEMA + "name", Lit("b")) in got


def test_the_id_of_a_graph_entity_that_is_no_string_is_refused(fixture_md):
    with pytest.raises(E.ExpandError):
        E.expand(md_with(fixture_md, {"@id": ["a"], "@type": "CreativeWork"}))


# -- the document ---------------------------------------------------------------------------------------------------------------
def test_only_the_context_the_reader_holds_and_a_graph_of_entities_are_read(fixture_md):
    other = copy.deepcopy(fixture_md)
    other["@context"] = V.context() + [{"x": "https://example.org/"}]
    for md in (other, {"@context": V.context()}, {"@graph": []}, {**fixture_md, "extra": 1}, [], "x",
               {"@context": V.context(), "@graph": "x"}, {"@context": V.context(), "@graph": [1]}):
        with pytest.raises(E.ExpandError):
            E.expand(md)


def test_the_context_is_the_pinned_copy_and_a_copy_that_is_not_is_refused(monkeypatch):
    E.context.cache_clear()
    monkeypatch.setattr(V, "ROCRATE_CONTEXT_SHA256", "0" * 64)
    try:
        with pytest.raises(RuntimeError, match="pins"):
            E.context()
    finally:
        monkeypatch.undo()
        E.context.cache_clear()
    assert len(E.context()) == 3069 and E.context()["File"] == SCHEMA + "MediaObject"


def test_the_prefixes_are_the_contexts_gen_delim_terms_and_qro():
    p = E.prefixes()
    assert p["schema"] == SCHEMA and p["dct"] == "http://purl.org/dc/terms/" and p["qro"] == V.NAMESPACE
    assert "name" not in p and "File" not in p and all(v[-1] in ":/?#[]@" for k, v in p.items() if k != "qro")


def test_a_term_that_is_itself_a_compact_iri_is_expanded():
    assert E.iri_of_term("HTML") == "http://www.w3.org/1999/02/22-rdf-syntax-ns#HTML"
    assert E.iri_of_term("hasPart") == SCHEMA + "hasPart"
    with pytest.raises(KeyError):
        E.iri_of_term("nonesuch")


def test_a_context_with_a_term_that_is_no_plain_iri_is_refused(monkeypatch):
    E.context.cache_clear()
    real = json.loads
    monkeypatch.setattr(E.json, "loads", lambda data: {"@context": {"x": {"@id": "y"}}} if len(data) > 1000 else real(data))
    try:
        with pytest.raises(E.ExpandError, match="plain IRI"):
            E.context()
    finally:
        monkeypatch.undo()
        E.context.cache_clear()
