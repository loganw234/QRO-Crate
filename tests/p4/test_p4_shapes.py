"""The shapes the table makes (qro/p4_shapes.py): every row has its shapes and every spelling its constraint; a pattern
is read from qro/spelling.py and never written again; a description claims no more than its shape holds; level, folder
and severity agree; each shape's claim is a refusal; and a row changed in memory changes exactly its own shapes (gates 6
and 7 of P4's design, item 4.6). The structural shapes are read from the table's own functions, and each is planted."""
import dataclasses
import re

import pytest
from p4_helpers import SH_NAMES, turtle_problems
from qro import p4_expand, p4_turtle
from qro import p4_shapes as H
from qro import spelling as S
from qro import vocabulary as V
from qro.p4_model import RDF_TYPE, XSD_INTEGER, XSD_STRING, Lit, Shape, inv, one_or_more, walk


def by_id(shapes=None):
    return {s.id: s for s in (H.build() if shapes is None else shapes)}


def local(i):
    return i.split("#", 1)[1]


def prop_of(shape):
    """The one property shape of a term's shape."""
    assert len(shape.props) == 1
    return shape.props[0]


# -- every row has its shapes -------------------------------------------------------------------------------------------
def test_the_table_makes_no_problem():
    assert V.sanity() == [] and H.problems() == []


def test_every_row_has_a_term_shape_and_a_domain_shape_unless_it_stands_anywhere():
    ids = {local(i) for i in by_id()}
    for t in V.TERMS:
        assert "term-" + H.slug(t.key) in ids, t.key
        assert ("domain-" + H.slug(t.key) in ids) == ("*" not in t.domain), t.key
    assert sum(i.startswith("term-") for i in ids) == len(V.TERMS)
    assert sum(i.startswith("domain-") for i in ids) == sum("*" not in t.domain for t in V.TERMS)


def test_the_shapes_are_these_families_and_no_others():
    ids = [local(i) for i in by_id()]
    families = {"entity", "descriptor", "root", "action-mentioned", "file-digest-present", "file-reached",
                "rawresult-form", "profile-entities", "profile-version"}
    absence = [i for i in ids if i.startswith("absence-")]
    assert set(ids) == families | {i for i in ids if i.startswith(("term-", "domain-", "absence-"))}
    assert families <= set(ids) and len(ids) == len(set(ids))
    want = sum(len([x for x in t.domain if x not in ("*", V.ROOT, V.DESC, V.LOCAL)]) for t in V.TERMS
               if t.absent and not {"*", V.ROOT, V.DESC, V.LOCAL} & set(t.domain))
    assert len(absence) == want > 0


def test_a_shapes_id_is_a_lowercase_kebab_anchor_of_the_profiles_page():
    for s in H.build():
        assert s.id.startswith(V.PROFILE + "#") and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", local(s.id)), s.id
    assert H.slug("qro:shots") == "qro-shots" and H.slug("contentSize") == "contentsize"
    assert H.shape_iri("x") == V.PROFILE + "#x"


def test_the_groups_are_the_files_in_order_and_a_group_with_no_shape_is_not_written(monkeypatch):
    assert list(H.groups()) == list(H.FILES)
    monkeypatch.setattr(V, "TERMS", tuple(dataclasses.replace(t, absent=()) if t.absent and t.key != "qro:signature"
                                          and t.key != "qro:trustedTime" else t for t in V.TERMS))
    assert "should/1_absence.ttl" not in H.groups() and len(H.groups()) == 3
    assert [s for s in H.build() if s.level == "should"] == []


def test_the_folder_of_a_shape_is_its_level_and_its_severity_the_levels_everywhere():
    for path, shapes in H.groups().items():
        for s in shapes:
            assert s.level == H.level_of(path) == path.split("/")[0], s.id
        text = p4_turtle.render(shapes, H.prefixes(), ["x"])
        want = {"must": "Violation", "should": "Warning"}[H.level_of(path)]
        assert set(re.findall(r"sh:severity sh:(\w+)", text)) == {want}, path
        reports = len(shapes) + sum(1 for s in shapes for _ in s.props)
        assert text.count("sh:severity") == reports, path


def test_every_claim_is_a_refusal_the_table_names_and_each_family_claims_what_it_mirrors():
    claims = {local(s.id): s.claims for s in H.build()}
    assert all(c in V.REFUSAL for cs in claims.values() for c in cs)
    # the refusals a shape mirrors, then the six of form that can come first (FORM: spelling, term-unknown, graph-form,
    # context, file-missing, file-link) that it does not name already, written out in full: the sweeps hold them true
    # (test_p4_sweeps.py, test_p4_families.py), this holds them as they are
    assert H.FORM == ("spelling", "term-unknown", "graph-form", "context", "file-missing", "file-link")
    assert claims["entity"] == ("term-unknown", "field-kind", "graph-form", "spelling", "context", "file-missing", "file-link")
    assert claims["descriptor"] == claims["root"] == claims["action-mentioned"] == claims["profile-entities"] == (
        "graph-form", "spelling", "term-unknown", "context", "file-missing", "file-link")
    assert claims["file-digest-present"] == ("file-digest", "raw-digest", "spelling", "term-unknown", "graph-form", "context",
                                             "file-missing", "file-link")
    assert claims["file-reached"] == ("file-unlisted", "graph-form", "spelling", "term-unknown", "context", "file-missing", "file-link")
    assert claims["rawresult-form"] == ("raw-form", "graph-form", "file-unlisted", "spelling", "term-unknown", "context",
                                        "file-missing", "file-link")
    assert claims["profile-version"] == ("context", "graph-form", "spelling", "term-unknown", "file-missing", "file-link")
    for t in V.TERMS:
        assert claims["term-" + H.slug(t.key)] == ("spelling", "term-unknown", "graph-form", "context", "file-missing", "file-link"), t.key
        if "*" not in t.domain:
            assert claims["domain-" + H.slug(t.key)] == ("graph-form", "spelling", "term-unknown", "context", "file-missing", "file-link")
    assert all(not s.claims for s in H.build() if s.level == "should")


def test_every_must_shape_claims_each_refusal_of_steps_1_and_2_that_can_come_before_its_own():
    """The ruling of 2026-10-26T11:18:27Z: FORM is the refusals of steps 1 and 2 that RDF cannot show and that can come first, so
    every must shape claims all of them; and each other refusal of steps 1 and 2 is claimed by a shape that mirrors it (its own
    claim), so that a refusal P0 adds to those steps is a decision here and not a silence."""
    shapes, own = H.build(), {local(s.id): s.claims for s in H.build(widen=False)}
    for s in shapes:
        assert (set(H.FORM) <= set(s.claims)) == (s.level == "must"), s.id
    early = {r.name for r in V.REFUSALS if {"step 1", "step 2"} & set(r.where.split("; "))}
    assert set(H.FORM) <= early and early - set(H.FORM) == {"field-kind", "file-unlisted", "file-digest", "raw-digest"}, sorted(early)
    for name in early - set(H.FORM):
        assert any(name in claims for claims in own.values()), f"{name} is claimed by no shape's own claims, and is not in FORM"
    assert {n for n, claims in own.items() if "field-kind" in claims} == {"entity"}
    assert {n for n, claims in own.items() if "file-digest" in claims or "raw-digest" in claims} == {"file-digest-present"}
    assert {n for n, claims in own.items() if "file-unlisted" in claims} == {"file-reached", "rawresult-form"}


def test_the_generated_shapes_use_neither_construct_the_evaluator_and_pyshacl_read_differently():
    """Limit 23: `sh:minLength 0` on a blank node is failed by the evaluator and passed by pyshacl 0.40.1, and `sh:maxInclusive`
    with no `sh:minInclusive` is failed by the evaluator against a boolean literal and passed by pyshacl. The engine stage holds
    the two disagreements as they are (tests/p4shacl/test_p4shacl_disagree.py); here, that no shape of the table's uses either."""
    seen = lows = pairs = 0
    maxes = set()
    for s in H.build():
        for shape in walk(s):
            seen += 1
            assert shape.min_length is None or shape.min_length >= 1, local(s.id)
            assert shape.max_inclusive is None or shape.min_inclusive is not None, local(s.id)
            lows += shape.min_length is not None
            pairs += shape.max_inclusive is not None
            if shape.max_length is not None:
                maxes.add(shape.max_length)
    assert seen >= 250 and lows >= 1 and pairs >= 1                 # and the check looked at shapes that have a bound
    assert len(maxes) >= 3, maxes          # limit 23 says `sh:maxLength` is used, with several bounds (10, 19, 40, 64, 2002 when it was written)


def test_the_shapes_do_use_integers_and_no_crate_reaches_the_lexical_forms_the_evaluator_and_pyshacl_read_differently():
    """Limit 23's third thing (the fourth verifier's note, MEASURED): on a literal whose lexical form Python's int() reads and XSD's
    lexical space may not, the evaluator fails the integer shape and pyshacl accepts the literal. The engine stage holds that
    (tests/p4shacl/test_p4shacl_disagree.py). Here, what makes it harmless: the shapes use sh:datatype xsd:integer on the table's
    integer terms and no other; the checker refuses each of the six forms as a value, as it refuses everything but a JSON number
    written in its one spelling; and the expansion writes a number as its decimal digits alone, so none of the forms is made."""
    terms = {t.key for t in V.TERMS if t.spelling == "integer"}
    used = {local(s.id) for s in H.build() for shape in walk(s) if shape.datatype == XSD_INTEGER}
    assert len(terms) == 3 and used == {"term-" + H.slug(k) for k in terms}, (terms, used)          # "three terms", limit 23
    forms = (" 1", "1 ", chr(9) + "1" + chr(10), "1_0", chr(0x661), chr(0xFF11))
    for form in forms:
        assert S.problem("integer", form) == "not a non-negative integer of at most 2^63 - 1", ascii(form)
        assert int(form) in (1, 10)                                                       # Python's int() does read each of them
        assert p4_expand.literal(form) == Lit(form) and p4_expand.literal(form).datatype != XSD_INTEGER        # a string, never an integer
    for n in (0, 1, 10, 2 ** 63 - 1):
        assert S.problem("integer", n) is None and p4_expand.literal(n) == Lit(str(n), XSD_INTEGER)             # the digits alone


# -- the spellings --------------------------------------------------------------------------------------------------------
def test_a_constraint_for_every_spelling_of_the_table_and_for_no_other():
    assert set(H.SPELLING_SHAPES) == set(V.SPELLINGS)
    for sp in V.SPELLINGS:
        assert (H.spelling_constraints(sp) is None) == (sp == "slot")


def test_a_spelling_with_no_constraint_a_constraint_for_no_spelling_and_a_word_set_that_is_none_are_named(monkeypatch):
    monkeypatch.setitem(V.SPELLINGS, "decimal", "a number")
    assert any("decimal: no shape constraint" in p for p in H.problems())
    monkeypatch.delitem(V.SPELLINGS, "decimal")
    monkeypatch.setitem(H.SPELLING_SHAPES, "ordinal", lambda: {})
    assert any("ordinal: has a shape constraint" in p for p in H.problems())
    with pytest.raises(H.TableProblem, match="names no word set"):
        H.spelling_constraints("word:no-such-set")
    with pytest.raises(H.TableProblem, match="no shape constraint"):
        H.spelling_constraints("decimal")


E = dict
EXPECTED = {
    "integer": E(datatype=XSD_INTEGER, min_inclusive=0, max_inclusive=2 ** 63 - 1),
    "size": E(datatype=XSD_STRING, pattern="^((0|[1-9][0-9]*))$", max_length=19),
    "digest": E(datatype=XSD_STRING, pattern="^([0-9a-f]{64})$", max_length=64),
    "commit": E(datatype=XSD_STRING, pattern="^([0-9a-f]{40})$", max_length=40),
    "rational": E(datatype=XSD_STRING, pattern="^(0/1|-?[1-9][0-9]*/[1-9][0-9]*)$", max_length=2002),
    "binary64": E(datatype=XSD_STRING, pattern="^(([0-9a-f]{16}) ([!-~]+))$"),
    "time": E(datatype=XSD_STRING, pattern="^(([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})"
                                         "(\\.[0-9]*[1-9])?Z)$"),
    "date": E(datatype=XSD_STRING, pattern="^([0-9]{4}-[0-9]{2}-[0-9]{2})$", max_length=10),
    "text": E(datatype=XSD_STRING, min_length=1, pattern="^[^\\s]([\\s\\S]*[^\\s])?$"),
    "iri": E(datatype=XSD_STRING, pattern="^([A-Za-z][A-Za-z0-9+-]+:[!-~]+)$"),
    "ref": E(node_kind="IRI"),
}


@pytest.mark.parametrize("sp", sorted(EXPECTED))
def test_each_spellings_constraint_is_this(sp):
    assert H.spelling_constraints(sp) == EXPECTED[sp]


def test_a_regular_expression_is_read_from_the_spelling_module_and_a_change_there_changes_the_shape(monkeypatch):
    for sp, key in (("digest", "digest"), ("commit", "commit"), ("size", "size"), ("rational", "rational"),
                    ("binary64", "binary64"), ("time", "time"), ("date", "date"), ("iri", "iri")):
        monkeypatch.setitem(S.PATTERNS, key, re.compile("ZZZ" + sp))
        assert H.spelling_constraints(sp)["pattern"] == f"^(ZZZ{sp})$", sp
        monkeypatch.undo()
    monkeypatch.setitem(S.PATTERNS, "digest", re.compile("[0-9a-f]{65}"))
    assert "{65}" in prop_of(by_id()[H.shape_iri("term-sha256")]).pattern
    assert "{65}" in prop_of(by_id()[H.shape_iri("term-qro-commitment")]).or_[0].pattern


def test_a_pattern_that_is_a_form_is_closed_by_a_length_where_the_form_has_one():
    """`$` lets one trailing line feed by in Python; a fixed length closes it (MEASURED, pyshacl 0.40.1)."""
    assert H.spelling_constraints("digest")["max_length"] == 64 and H.spelling_constraints("commit")["max_length"] == 40
    assert H.spelling_constraints("date")["max_length"] == 10 and H.spelling_constraints("size")["max_length"] == 19
    assert H.spelling_constraints("rational")["max_length"] == 2 * S.TERM_DIGITS + 2


def test_a_word_set_is_its_words_in_the_tables_order():
    for t in V.TERMS:
        if t.spelling.startswith("word:"):
            c = H.spelling_constraints(t.spelling)
            assert c == dict(datatype=XSD_STRING, in_=tuple(Lit(w) for w in V.WORDS[t.spelling[5:]]))


# -- a term's shape -----------------------------------------------------------------------------------------------------------------
def test_a_term_shape_is_the_rows_cardinality_spelling_and_absence_words():
    shapes = by_id()
    for t in V.TERMS:
        s = shapes[H.shape_iri("term-" + H.slug(t.key))]
        p = prop_of(s)
        assert s.targets == (("subjectsOf", H.term_iri(t.key)),) and p.path == H.term_iri(t.key)
        assert p.max_count == (None if t.many else 1) and p.min_count is None
        base = H.spelling_constraints(t.spelling)
        absent = tuple(Lit(a) for a in t.absent)
        if not t.absent:
            assert {k: getattr(p, k) for k in base} == base, t.key
        elif base is None:
            assert p.in_ == absent, t.key
        else:
            assert p.or_ == (Shape(**base), Shape(in_=absent)), t.key
        assert s.kind == t.kind and s.name == f"{t.key}: its one spelling" and s.level == "must"


def test_a_slot_takes_only_its_absence_words_and_a_slot_with_none_is_named(monkeypatch):
    p = prop_of(by_id()[H.shape_iri("term-qro-signature")])
    assert p.in_ == (Lit("none"),) and p.datatype is None and p.or_ == ()
    two = V.Term("qro:slotty2", "REPORTED", "slot", False, ("none", "unknown"), "body", None, "P0", "m")
    monkeypatch.setattr(V, "TERMS", V.TERMS + (two,))
    assert prop_of(by_id()[H.shape_iri("term-qro-slotty2")]).in_ == (Lit("none"), Lit("unknown"))      # each of its words
    monkeypatch.setattr(V, "TERMS", V.TERMS[:-1] + (V.Term("qro:slotty", "REPORTED", "slot", False, (), "body", None, "P0", "m"),))
    with pytest.raises(H.TableProblem, match="a slot with no absence word"):
        H.build()


def test_a_term_that_is_neither_a_qro_name_nor_in_rocrates_context_is_named(monkeypatch):
    monkeypatch.setattr(V, "TERMS", V.TERMS + (V.Term("nonesuch", "REPORTED", "text", False, (), "body", None, "P0", "m"),))
    assert any("nonesuch: neither a qro: name nor a term of RO-Crate 1.3's context" in p for p in H.problems())
    assert H.term_iri("qro:rawForm") == V.NAMESPACE + "rawForm" and H.term_iri("hasPart") == "http://schema.org/hasPart"


def test_a_description_claims_no_more_than_its_shape_holds():
    shapes = by_id()
    phrase = {"CHECKED": "the form only: step {step} re-derives the value",
              "READ": "the form only: the checker's arithmetic takes the value as given",
              "ANCHORED": "stated, not checked, until the crate holds the provider's own record of it",
              "REPORTED": "stated, not checked"}
    for t in V.TERMS:
        d = shapes[H.shape_iri("term-" + H.slug(t.key))].description
        assert d.endswith(phrase[t.kind].format(step=t.step)), t.key
        assert ("re-derives" in d) == (t.kind == "CHECKED") and ("takes the value as given" in d) == (t.kind == "READ")
        assert ("a list of one value or more" in d) == t.many and ("one value;" in d) == (not t.many)
        for a in t.absent:
            assert a in d, t.key
    assert H.kind_phrase(V.TERM["sha256"]) == "the form only: step 2 re-derives the value"


def test_a_domain_shape_names_where_the_term_stands():
    shapes = by_id()
    for t in V.TERMS:
        if "*" in t.domain:
            continue
        s = shapes[H.shape_iri("domain-" + H.slug(t.key))]
        alts = [H.domain_alternative(tok) for tok in t.domain]
        assert s.targets == (("subjectsOf", H.term_iri(t.key)),) and s.level == "must"
        if len(alts) > 1:
            assert s.or_ == tuple(alts) and not s.classes, t.key
        else:
            assert (s.classes, s.pattern, s.props) == (alts[0].classes, alts[0].pattern, alts[0].props), t.key
        assert H.domain_text(t) in s.message and H.domain_text(t) in s.description
        notes = {V.LOCAL: "a File here is any File", V.ROOT: "the root is what the descriptor is about",
                 V.DESC: "the descriptor is the entity named " + V.DESC}            # said where the token is, and only there
        for token, text in notes.items():
            assert (text in s.description) == (token in t.domain), (t.key, token)


def test_each_kind_of_domain_token_is_this_alternative():
    about = "http://schema.org/about"
    assert H.domain_alternative(V.ROOT) == Shape(props=(Shape(path=inv(about), min_count=1),))
    assert H.domain_alternative(V.DESC) == Shape(pattern="(^|/)ro-crate-metadata\\.json$")
    assert H.domain_alternative(V.LOCAL) == Shape(classes=("http://schema.org/MediaObject",))
    assert H.domain_alternative("qro:Job") == Shape(classes=(V.NAMESPACE + "Job",))
    assert H.domain_alternative("File") == Shape(classes=("http://schema.org/MediaObject",))
    assert H.domain_shape(V.TERM["name"]) is None and H.domain_shape(V.TERM["qro:implementation"]) is None


# -- the absence shapes (should) --------------------------------------------------------------------------------------------------------------
def test_an_absence_shape_asks_a_term_with_absence_words_of_each_entity_of_a_type_it_belongs_to():
    got = {local(s.id): s for s in H.absence_shapes()}
    s = got["absence-qro-commitment-qro-pub"]
    assert s.level == "should" and s.claims == () and s.targets == (("class", V.NAMESPACE + "Pub"),)
    assert prop_of(s).path == V.NAMESPACE + "commitment" and prop_of(s).min_count == 1
    assert "should carry qro:commitment, or say none" in s.message
    assert "absence-qro-signature-root" not in got and not any("trustedtime" in k or "signature" in k for k in got)
    two = [k for k in got if k.startswith("absence-endtime-")]
    assert two == ["absence-endtime-qro-job"]


def test_an_absence_shape_is_made_for_a_term_whose_every_domain_token_is_a_type_and_for_no_other(monkeypatch):
    """The rule holds for a row the table does not have yet: a domain that mixes a type with the root, the descriptor, a
    File or anything has no absence shape, and one of two types has one for each."""
    base = V.TERM["qro:commitment"]
    rows = {"qro:odd": ("qro:Pub", V.ROOT), "qro:odder": ("qro:Pub", "*"), "qro:oddest": ("qro:Pub", V.LOCAL),
            "qro:oddly": ("qro:Pub", V.DESC), "qro:even": ("qro:Pub", "qro:Job")}
    monkeypatch.setattr(V, "TERMS", V.TERMS + tuple(dataclasses.replace(base, key=k, domain=d) for k, d in rows.items()))
    got = {local(s.id) for s in H.absence_shapes()}
    assert {"absence-qro-even-qro-pub", "absence-qro-even-qro-job"} <= got
    assert not any(k.startswith(("absence-qro-odd-", "absence-qro-odder-", "absence-qro-oddest-", "absence-qro-oddly-"))
                   for k in got)


# -- the structural shapes, planted against the table they are read from ---------------------------------------------------------------------
def test_the_root_shape_asks_what_the_table_requires_and_nothing_of_what_hasPart_names():
    s = by_id()[H.shape_iri("root")]
    assert s.targets == (("objectsOf", "http://schema.org/about"),) and s.classes == ("http://schema.org/Dataset",)
    paths = {p.path: p for p in s.props}
    for k in V.ROOT_REQUIRED:
        if k != "conformsTo":
            assert paths[H.term_iri(k)].min_count == 1 and paths[H.term_iri(k)].max_count is None, k
    conforms = paths["http://purl.org/dc/terms/conformsTo"]
    assert (conforms.min_count, conforms.max_count) == (2, 2) and conforms.has_value == (V.PROCESS_RUN_CRATE, V.PROFILE)
    assert paths["http://schema.org/mentions"].classes == ("http://schema.org/CreateAction",)
    assert s.not_ == (Shape(classes=("http://schema.org/CreateAction",)),)
    assert "http://schema.org/hasPart" in paths and paths["http://schema.org/hasPart"] == Shape(path="http://schema.org/hasPart",
                                                                                           min_count=1)


def test_the_descriptor_shape_is_the_tables_descriptor_and_nothing_more():
    s = by_id()[H.shape_iri("descriptor")]
    assert s.targets == (("subjectsOf", "http://schema.org/about"),) and s.closed and s.ignored == (RDF_TYPE,)
    assert s.pattern == "(^|/)ro-crate-metadata\\.json$"
    by = {p.path: p for p in s.props}
    assert by[RDF_TYPE].has_value == ("http://schema.org/CreativeWork",) and (by[RDF_TYPE].min_count, by[RDF_TYPE].max_count) == (1, 1)
    about = by["http://schema.org/about"]
    assert (about.min_count, about.max_count, about.node_kind, about.pattern) == (1, 1, "IRI", "/$")
    conforms = by["http://purl.org/dc/terms/conformsTo"]
    assert conforms.has_value == (V.ROCRATE,) and (conforms.min_count, conforms.max_count) == (1, 1)


def test_the_descriptor_shape_follows_the_table_and_names_a_descriptor_that_is_not_about_the_root(monkeypatch):
    changed = dict(V.descriptor(), conformsTo=[{"@id": "https://w3id.org/ro/crate/9.9"}, {"@id": V.ROCRATE}])
    monkeypatch.setattr(V, "descriptor", lambda: changed)
    s = by_id()[H.shape_iri("descriptor")]
    assert {p.path: p for p in s.props}["http://purl.org/dc/terms/conformsTo"].has_value == (
        "https://w3id.org/ro/crate/9.9", V.ROCRATE)
    monkeypatch.setattr(V, "descriptor", lambda: dict(V.descriptor.__wrapped__() if hasattr(V.descriptor, "__wrapped__")
                                                      else changed, about={"@id": "elsewhere"}))
    with pytest.raises(H.TableProblem, match="about the root"):
        H.descriptor_shape()


def test_the_action_shape_asks_the_root_for_every_action_type_of_the_table(monkeypatch):
    s = by_id()[H.shape_iri("action-mentioned")]
    assert s.targets == (("class", "http://schema.org/CreateAction"),) and prop_of(s).path == inv("http://schema.org/mentions")
    assert prop_of(s).min_count == 1
    monkeypatch.setattr(V, "TYPES", tuple(dataclasses.replace(y, action=True) if y.key == "qro:Job" else y for y in V.TYPES))
    shapes = by_id()
    assert shapes[H.shape_iri("action-mentioned")].targets == (("class", "http://schema.org/CreateAction"),
                                                              ("class", V.NAMESPACE + "Job"))
    assert len(shapes[H.shape_iri("root")].props[-1].or_) == 2 and len(shapes[H.shape_iri("root")].not_[0].or_) == 2


def test_the_file_shapes_ask_the_presence_table_and_exempt_what_is_not_a_path_in_the_crate(monkeypatch):
    shapes = by_id()
    d = shapes[H.shape_iri("file-digest-present")]
    assert d.targets == (("class", "http://schema.org/MediaObject"),)
    assert d.or_[0] == Shape(pattern="#") and d.or_[1] == Shape(not_=(Shape(pattern="^file:"),))
    assert d.or_[2] == Shape(props=(Shape(path="http://schema.org/sha256", min_count=1),
                                    Shape(path="http://schema.org/contentSize", min_count=1)))
    r = shapes[H.shape_iri("rawresult-form")]
    assert r.targets == (("class", V.NAMESPACE + "RawResult"),) and r.classes == ("http://schema.org/MediaObject",)
    assert r.props == (Shape(path=V.NAMESPACE + "rawForm", min_count=1),)
    monkeypatch.setitem(H.PRESENCE, "File", ("sha256",))
    assert by_id()[H.shape_iri("file-digest-present")].or_[2] == Shape(
        props=(Shape(path="http://schema.org/sha256", min_count=1),))
    monkeypatch.setitem(H.PRESENCE, "qro:RawResult", ("qro:rawForm", "qro:shots"))
    assert len(by_id()[H.shape_iri("rawresult-form")].props) == 2


def test_the_reached_shape_follows_hasPart_back_to_what_the_descriptor_is_about():
    s = by_id()[H.shape_iri("file-reached")]
    assert s.targets == (("subjectsOf", "http://schema.org/sha256"),)
    p = prop_of(s)
    assert p.path == one_or_more(inv("http://schema.org/hasPart"))
    assert p.qvs == ((Shape(props=(Shape(path=inv("http://schema.org/about"), min_count=1),)), 1),)


def test_the_profile_shapes_are_the_tables_entities_and_hold_the_version_apart_from_the_rest(monkeypatch):
    shapes = by_id()
    e, v = shapes[H.shape_iri("profile-entities")], shapes[H.shape_iri("profile-version")]
    iris = tuple(x["@id"] for x in V.profile_entities())
    assert e.targets == tuple(("node", i) for i in iris) + (("class", "http://www.w3.org/ns/dx/prof/Profile"),)
    assert v.targets == tuple(("node", i) for i in iris)
    for alt, want in zip(e.or_, V.profile_entities()):
        assert alt.has_value == (want["@id"],) and alt.closed and alt.ignored == (RDF_TYPE,)
        by = {p.path: p for p in alt.props}
        assert by["http://schema.org/name"].has_value == (Lit(want["name"]),)
        assert by["http://schema.org/version"] == Shape(path="http://schema.org/version")
        assert by[RDF_TYPE].has_value == ("http://schema.org/CreativeWork", "http://www.w3.org/ns/dx/prof/Profile")
        assert (by[RDF_TYPE].min_count, by[RDF_TYPE].max_count) == (2, 2)
    for alt, want in zip(v.or_, V.profile_entities()):
        assert alt.has_value == (want["@id"],)
        assert alt.props == (Shape(path="http://schema.org/version", min_count=1, max_count=1,
                                   has_value=(Lit(want["version"]),)),)
    monkeypatch.setattr(V, "PROFILE_VERSION", "0.2")
    assert by_id()[H.shape_iri("profile-version")] != v and by_id()[H.shape_iri("profile-entities")] == e


def test_the_entity_shape_lists_every_term_and_every_type_of_the_table():
    s = by_id()[H.shape_iri("entity")]
    terms = list(dict.fromkeys(H.term_iri(t.key) for t in V.TERMS))
    assert s.node_kind == "IRI" and s.closed and s.ignored == (RDF_TYPE,) + tuple(terms)
    assert s.targets == (("subjectsOf", RDF_TYPE),) + tuple(("subjectsOf", p) for p in terms)
    assert prop_of(s) == Shape(path=RDF_TYPE, min_count=1, in_=tuple(H.term_iri(y.key) for y in V.TYPES),
                               message="an entity has a type, and it is one the profile lists")


# -- a row changed in memory changes exactly its own shapes (gate 7) ------------------------------------------------------------------------------
def swap_term(monkeypatch, key, **changes):
    monkeypatch.setattr(V, "TERMS", tuple(dataclasses.replace(t, **changes) if t.key == key else t for t in V.TERMS))


def diff(before, after):
    changed = {local(i) for i in before.keys() & after.keys() if before[i] != after[i]}
    return changed, {local(i) for i in after.keys() - before.keys()}, {local(i) for i in before.keys() - after.keys()}


MUTATIONS = {
    "a spelling": (lambda mp: swap_term(mp, "sha256", spelling="commit"), {"term-sha256"}, set(), set()),
    "a kind": (lambda mp: swap_term(mp, "qro:stamp", kind="READ", step=None), {"term-qro-stamp"}, set(), set()),
    "a step": (lambda mp: swap_term(mp, "qro:stamp", step=7), {"term-qro-stamp"}, set(), set()),
    "many": (lambda mp: swap_term(mp, "qro:calibration", many=False), {"term-qro-calibration"}, set(), set()),
    "a meaning": (lambda mp: swap_term(mp, "qro:stamp", meaning="another meaning"), set(), set(), set()),
    "an owner": (lambda mp: swap_term(mp, "qro:stamp", owner="P3"), set(), set(), set()),
    "a narrower domain": (lambda mp: swap_term(mp, "qro:clock", domain=("qro:Job",)), {"domain-qro-clock"}, set(), set()),
    "a domain that is anywhere": (lambda mp: swap_term(mp, "qro:clock", domain=("*",)), set(), set(), {"domain-qro-clock"}),
    "an absence word": (lambda mp: swap_term(mp, "qro:role", absent=("unknown",)), {"term-qro-role"},
                        {"absence-qro-role-qro-pub"}, set()),
    "an absence word taken away": (lambda mp: swap_term(mp, "qro:commitment", absent=()), {"term-qro-commitment"}, set(),
                                   {"absence-qro-commitment-qro-pub"}),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_a_row_changed_in_memory_changes_its_shapes_and_no_other(monkeypatch, name):
    before = by_id()
    mutate, changed, added, removed = MUTATIONS[name]
    mutate(monkeypatch)
    assert diff(before, by_id()) == (changed, added, removed)


def test_a_word_added_to_a_set_changes_the_shapes_of_the_terms_that_use_it_and_no_other(monkeypatch):
    before = by_id()
    monkeypatch.setitem(V.WORDS, "role", {**V.WORDS["role"], "extra": "an extra word"})
    changed, added, removed = diff(before, by_id())
    assert changed == {"term-qro-role"} and not added and not removed
    assert Lit("extra") in prop_of(by_id()[H.shape_iri("term-qro-role")]).in_


def test_a_term_added_adds_its_shapes_and_changes_the_entity_shape_alone(monkeypatch):
    before = by_id()
    monkeypatch.setattr(V, "TERMS", V.TERMS + (V.Term("qro:extra", "REPORTED", "text", False, (), "body", None, "P0", "m",
                                                      ("qro:Job",)),))
    assert diff(before, by_id()) == ({"entity"}, {"term-qro-extra", "domain-qro-extra"}, set())
    monkeypatch.undo()
    monkeypatch.setattr(V, "TERMS", tuple(t for t in V.TERMS if t.key != "qro:clock"))
    assert diff(before, by_id()) == ({"entity"}, set(), {"term-qro-clock", "domain-qro-clock"})


def test_the_root_required_list_the_descriptor_the_profile_version_and_the_action_types_are_read_where_they_stand(monkeypatch):
    before = by_id()
    monkeypatch.setattr(V, "ROOT_REQUIRED", V.ROOT_REQUIRED[:-1])
    assert diff(before, by_id()) == ({"root"}, set(), set())
    monkeypatch.undo()
    monkeypatch.setattr(V, "PROFILE_VERSION", "0.2")
    assert diff(before, by_id()) == ({"profile-version"}, set(), set())
    monkeypatch.undo()
    monkeypatch.setattr(V, "PRC_VERSION", "0.7")
    assert diff(before, by_id()) == ({"profile-version"}, set(), set())
    monkeypatch.undo()
    monkeypatch.setitem(H.PRESENCE, "File", ("sha256",))
    assert diff(before, by_id()) == ({"file-digest-present"}, set(), set())


def test_the_unrelated_shapes_do_not_depend_on_a_term_they_do_not_name(monkeypatch):
    before = by_id()
    swap_term(monkeypatch, "qro:record", spelling="text")
    changed, _, _ = diff(before, by_id())
    assert changed == {"term-qro-record"}


# -- the Turtle those shapes make --------------------------------------------------------------------------------------------------------------------
def test_every_generated_file_passes_the_sanity_check_of_the_text():
    for path, shapes in H.groups().items():
        text = p4_turtle.render(shapes, H.prefixes(), ["x"])
        assert turtle_problems(text) == [], path
        used = set(re.findall(r"\bsh:(\w+)", text))
        assert used <= SH_NAMES and "oneOrMore" not in used


def test_every_pattern_the_shapes_write_is_in_the_syntax_python_and_an_xpath_engine_share():
    patterns = [sh.pattern for s in H.build() for sh in walk(s) if sh.pattern is not None]
    assert len(patterns) >= 30 and len(set(patterns)) >= 10
    for p in patterns:
        for rx, why in H.NON_PORTABLE:
            assert not re.search(rx, p), (p, why)
    assert "\\s" in H.TEXT_PATTERN and not re.search(r"\\[dwDWbBAZ]", H.TEXT_PATTERN)


def test_a_pattern_outside_the_shared_syntax_is_named_by_the_generator(monkeypatch):
    for bad in ("(?:x)", "\\d", "\\w+", "\\x41", "(a)\\1", "a*?", "a++", "\\b", "\\A", "\\Z", "\\S\\D"):
        monkeypatch.setitem(S.PATTERNS, "digest", re.compile(bad))
        found = [p for p in H.problems() if "outside the syntax an engine shares" in p]
        assert found, bad
        monkeypatch.undo()


@pytest.mark.parametrize("text", ["(?:x)", "(?i)x", "(?=x)", "\\d", "\\D", "\\w", "\\W", "\\b", "\\B", "\\A", "\\Z",
                                  "\\p{L}", "\\P{L}", "\\x41", "(a)\\1", "[a-z]\\2", "a*?", "a+?", "a??", "a{2}?", "a*+",
                                  "a++"])
def test_each_construct_outside_the_shared_syntax_is_named_even_where_python_cannot_compile_it(text):
    assert any(re.search(rx, text) for rx, _ in H.NON_PORTABLE), text


@pytest.mark.parametrize("text", ["^[0-9a-f]{64}$", "^([A-Za-z][A-Za-z0-9+-]+:[!-~]+)$", "(^|/)ro-crate-metadata\\.json$",
                                  "^[^\\s]([\\s\\S]*[^\\s])?$", "^(0/1|-?[1-9][0-9]*/[1-9][0-9]*)$", "#", "/$"])
def test_a_pattern_in_the_shared_syntax_is_not_named(text):
    assert not any(re.search(rx, text) for rx, _ in H.NON_PORTABLE), text


def test_the_generator_names_two_shapes_of_one_id_a_claim_that_is_no_refusal_and_a_level_in_the_wrong_folder(monkeypatch):
    real = H.groups
    first = real()["must/1_structure.ttl"][0]
    monkeypatch.setattr(H, "groups", lambda widen=True: {**real(), "must/2_terms.ttl": real()["must/2_terms.ttl"] + [first]})
    assert any("share the id" in p for p in H.problems())
    monkeypatch.setattr(H, "groups", lambda widen=True: {**real(), "must/1_structure.ttl": [dataclasses.replace(first, claims=("zz",))]
                                              + real()["must/1_structure.ttl"][1:]})
    assert any("claims zz, which is no refusal" in p for p in H.problems())
    monkeypatch.setattr(H, "groups", lambda widen=True: {**real(), "should/1_absence.ttl": [dataclasses.replace(first, id=first.id + "x")]})
    assert any("level must in a should folder" in p for p in H.problems())


def test_the_shapes_the_expansion_cannot_see_are_the_documented_ones():
    """A shape cannot name a path the expansion would drop: every predicate in a term shape is one JSON-LD keeps."""
    for t in V.TERMS:
        assert p4_expand.iri_of_key(t.key) == H.term_iri(t.key), t.key
    assert p4_expand.iri_of_key("madeUp") is None                           # a key no context defines is dropped (limit 5)
    assert p4_expand.iri_of_key("schema:name") == H.term_iri("name")        # and one spelt another way is the table's term
