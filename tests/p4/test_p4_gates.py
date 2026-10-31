"""The gates watched failing (gate 5 of P4's design, item 4.6): a gate that has never been seen to fail proves nothing.
Each gate of p4_helpers.py is run on shapes planted wrong, and must say so by name:
  1. soundness: a shape stricter than the checker; a shape that has gone weaker than its plant; a claim that is missing;
  2. the spelling differential: a digest one character too long, a word missing from a set;
  3. coverage: a shape deleted;
  4. the positive examples: a descriptor that asks for more than the table's;
and the sanity check of the Turtle text, with a fault of each kind it names. The real bug the first draft of the design had,
a root that asked what its hasPart names, is among them."""
import dataclasses

import pytest
from p4_helpers import (differential, own_name_problems, positive_problems, session_corpus, soundness_problems,
                        turtle_problems, uncovered)
from qro import p4_examples as X
from qro import p4_shapes as H
from qro import p4_turtle
from qro import vocabulary as V
from qro.p4_model import XSD_STRING, Shape


def named(shapes, name):
    return next(s for s in shapes if s.id == H.shape_iri(name))


def swapped(shapes, name, **changes):
    target = named(shapes, name)
    return [dataclasses.replace(s, **changes) if s is target else s for s in shapes]


def without(shapes, name):
    target = named(shapes, name)
    return [s for s in shapes if s is not target]


@pytest.fixture(scope="module")
def corpus():
    return session_corpus()


def only(cases, *names):
    return [c for c in cases if c.name in names]


# -- the real shapes pass every gate -------------------------------------------------------------------------------------------
def test_the_real_shapes_pass_every_gate(corpus):
    cases, shapes = corpus
    honest = X.honest_metadata()
    assert soundness_problems(shapes, cases) == [] and uncovered(shapes, cases) == []
    assert positive_problems(shapes, honest) == [] and [x for x in differential() if x[2] == "stricter"] == []


# -- 1. soundness ----------------------------------------------------------------------------------------------------------------
def test_a_root_that_asks_what_hasPart_names_is_found_by_the_edge_plant(corpus):
    cases, shapes = corpus
    root = named(shapes, "root")
    drafted = dataclasses.replace(root, props=root.props + (Shape(path="http://schema.org/hasPart", or_=(
        Shape(classes=("http://schema.org/MediaObject",)), Shape(classes=("http://schema.org/Dataset",)))),))
    found = soundness_problems([drafted if s is root else s for s in shapes], cases)
    assert any(f.startswith("edge-hasPart-an-action:") for f in found) and any(
        f.startswith("edge-hasPart-an-absolute-iri:") for f in found)


def test_a_digest_rule_that_exempts_a_list_of_web_schemes_is_found_by_the_edge_plant(corpus):
    cases, shapes = corpus
    digest = named(shapes, "file-digest-present")
    drafted = dataclasses.replace(digest, or_=(Shape(pattern="^(https?|ftps?|urn):|#"), digest.or_[2]))
    found = soundness_problems([drafted if s is digest else s for s in shapes], cases)
    assert any(f.startswith("edge-file-absolute-scheme:") for f in found), found


def test_a_digest_rule_that_asks_every_file_for_a_digest_is_found(corpus):
    cases, shapes = corpus
    found = soundness_problems(swapped(shapes, "file-digest-present", or_=(named(shapes, "file-digest-present").or_[2],)),
                               cases)
    assert any(f.startswith(("edge-file-absolute-scheme:", "edge-file-fragment-id:")) for f in found), found


def test_a_shape_stricter_than_the_checker_on_the_fixture_is_found_by_every_edge_plant(corpus):
    cases, shapes = corpus
    stricter = dataclasses.replace(named(shapes, "descriptor"), props=named(shapes, "descriptor").props + (
        Shape(path="http://schema.org/name", min_count=1),))
    found = soundness_problems([stricter if s.id == stricter.id else s for s in shapes], cases)
    assert len([f for f in found if f.startswith("edge-")]) >= 15, found[:3]


def test_a_shape_that_has_gone_weaker_than_its_plant_is_named(corpus):
    cases, shapes = corpus
    loosened = swapped(shapes, "term-sha256", props=(Shape(path="http://schema.org/sha256", max_count=1),))
    assert soundness_problems(loosened, only(cases, "spell-sha256")) == ["spell-sha256: term-sha256 does not fail"]


def test_a_domain_shape_widened_to_admit_everything_is_named(corpus):
    cases, shapes = corpus
    widened = swapped(shapes, "domain-qro-shots", classes=(), or_=())
    found = soundness_problems(widened, only(cases, "domain-qro-shots"))
    assert found == ["domain-qro-shots: domain-qro-shots does not fail"]


def test_a_term_shape_that_forgot_its_cardinality_is_named_by_the_plant_that_gives_the_term_two_values(corpus):
    cases, shapes = corpus
    term = named(shapes, "term-name")
    loosened = swapped(shapes, "term-name", props=(dataclasses.replace(term.props[0], max_count=None),))
    assert soundness_problems(loosened, only(cases, "many-name")) == ["many-name: term-name does not fail"]


def test_an_entity_shape_that_is_not_closed_is_named_by_the_plants_of_a_key_the_table_does_not_name(corpus):
    cases, shapes = corpus
    open_ = swapped(shapes, "entity", closed=False)
    found = soundness_problems(open_, only(cases, "qro-term-unknown", "rocrate-key-no-kind"))
    assert len(found) == 2 and all("entity does not fail" in f for f in found)


def test_a_claim_that_leaves_out_the_refusal_is_named(corpus):
    cases, shapes = corpus
    wrong = swapped(shapes, "term-sha256", claims=("graph-form",))
    found = soundness_problems(wrong, only(cases, "spell-sha256"))
    assert found and "claim ['graph-form']; steps 1 to 3 say spelling" in found[0]
    none = swapped(shapes, "term-sha256", claims=())
    assert soundness_problems(none, only(cases, "spell-sha256"))


def test_a_shape_whose_own_claim_is_wrong_is_named_though_every_must_shape_claims_the_six_of_form(corpus):
    cases, shapes = corpus
    own = {X.local(s.id): s.claims for s in H.build(widen=False)}
    assert own_name_problems(shapes, only(cases, "spell-sha256"), own) == []
    own["term-sha256"] = ("graph-form",)                     # the widened claims still hold `spelling`, so the soundness gate is quiet
    assert soundness_problems(shapes, only(cases, "spell-sha256")) == []
    found = own_name_problems(shapes, only(cases, "spell-sha256"), own)
    assert found and found[0].startswith("spell-sha256: steps 1 to 3 say spelling, and ['term-sha256'] fail and mirror ['graph-form']")


def test_a_declared_shape_that_does_not_exist_is_named(corpus):
    cases, shapes = corpus
    found = soundness_problems(without(shapes, "term-sha256"), only(cases, "spell-sha256"))
    assert found == ["spell-sha256: declares term-sha256, which is no shape"]


def test_a_must_shape_that_fails_on_a_plant_that_declares_none_is_named(corpus):
    cases, shapes = corpus
    nosy = Shape(id=H.shape_iri("nosy"), targets=(("class", "http://schema.org/Dataset"),), node_kind="IRI",
                 classes=("urn:no-such-class",), claims=("graph-form",))
    found = soundness_problems(list(shapes) + [nosy], only(cases, "edge-two-actions"))
    assert any("declares no failing shape" in f and "nosy" in f for f in found)


# -- 2. the spelling differential --------------------------------------------------------------------------------------------------
def test_a_digest_pattern_one_character_too_long_is_found_by_the_differential(monkeypatch):
    monkeypatch.setitem(H.SPELLING_SHAPES, "digest", lambda: dict(datatype=XSD_STRING, pattern="^[0-9a-f]{65}$",
                                                                  max_length=64))
    assert [x for x in differential() if x[2] == "stricter" and x[0] == "digest"]
    shapes = H.build()
    assert positive_problems(shapes, X.honest_metadata())                     # and the graph of every term fails it


@pytest.mark.parametrize("dropped", [0, 1, 2, -1])
def test_a_word_missing_from_a_set_is_found_by_the_differential_wherever_in_the_set_it_stood(monkeypatch, dropped):
    real = H.spelling_constraints

    def short(spelling):
        c = real(spelling)
        if spelling == "word:calibration-link":
            words = list(c["in_"])
            del words[dropped]
            return dict(c, in_=tuple(words))
        return c
    monkeypatch.setattr(H, "spelling_constraints", short)
    assert [x for x in differential() if x[2] == "stricter" and x[0] == "word:calibration-link"]


def test_the_first_word_of_a_set_missing_is_found_by_the_graph_of_every_term_too(monkeypatch):
    real = H.spelling_constraints
    monkeypatch.setattr(H, "spelling_constraints", lambda s: dict(real(s), in_=real(s)["in_"][1:])
                        if s == "word:calibration-link" else real(s))
    assert any("calibrationlink" in p for p in positive_problems(H.build(), X.honest_metadata()))


# -- 3. coverage -------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["term-sha256", "domain-qro-shots", "root", "file-reached", "profile-version", "entity"])
def test_a_deleted_shape_is_named_by_the_coverage_gate(corpus, name):
    cases, shapes = corpus
    assert uncovered(without(shapes, name), cases) == []                          # nothing left uncovered by what is left
    never = dataclasses.replace(named(shapes, name), id=H.shape_iri(name + "-never"), targets=(("class", "urn:none"),))
    assert uncovered(list(shapes) + [never], cases) == [name + "-never"]


def test_a_shape_that_only_fails_on_a_crate_no_plant_builds_is_named(corpus):
    cases, shapes = corpus
    stray = Shape(id=H.shape_iri("stray"), targets=(("class", "urn:none"),), node_kind="IRI", claims=("graph-form",))
    assert uncovered(list(shapes) + [stray], cases) == ["stray"]


# -- 4. the positive examples ----------------------------------------------------------------------------------------------------------------
def test_a_descriptor_that_asks_for_more_than_the_tables_fails_the_fixture(corpus):
    _, shapes = corpus
    stricter = swapped(shapes, "descriptor", props=named(shapes, "descriptor").props + (
        Shape(path="http://schema.org/name", min_count=1),))
    found = positive_problems(stricter, X.Workspace(shapes).pristine)
    assert found and all("#descriptor (must) fails at" in f for f in found)


def test_an_entity_shape_that_lists_one_type_too_few_fails_the_graph_of_every_term(corpus):
    _, shapes = corpus
    entity = named(shapes, "entity")
    short = swapped(shapes, "entity", props=(dataclasses.replace(entity.props[0], in_=entity.props[0].in_[:-1]),))
    found = positive_problems(short, X.honest_metadata())
    assert found and "entity" in found[0]


def test_a_root_that_asks_one_term_too_many_fails_the_fixture(corpus):
    _, shapes = corpus
    root = named(shapes, "root")
    more = swapped(shapes, "root", props=root.props + (Shape(path="http://schema.org/keywords", min_count=1),))
    assert any("root" in p for p in positive_problems(more, X.Workspace(shapes).pristine))


def test_the_positive_gate_reads_a_should_shape_too(corpus):
    _, shapes = corpus
    asked = swapped(shapes, "absence-qro-commitment-qro-pub", props=(Shape(path=V.NAMESPACE + "commitment", min_count=2),))
    assert any("absence-qro-commitment-qro-pub (should)" in p for p in positive_problems(asked, X.honest_metadata()))


# -- the sanity check of the Turtle text -------------------------------------------------------------------------------------------------------
GOOD = '@prefix a: <urn:x> .\n@prefix sh: <http://www.w3.org/ns/shacl#> .\n\na:s\n    a sh:NodeShape ;\n    sh:name "x" .\n'


@pytest.mark.parametrize("text, found", [
    (GOOD, None),
    (GOOD.replace("sh:NodeShape", "sh:NodeShape ["), "unbalanced []"),
    (GOOD.replace("sh:name", "sh:oneOrMore"), "sh:oneOrMore is no name SHACL Core has"),
    (GOOD.replace("sh:NodeShape", "sh:Shape"), "sh:Shape is no name SHACL Core has"),
    (GOOD.replace("@prefix sh: <http://www.w3.org/ns/shacl#> .\n", ""), "the prefix sh: is used and not declared"),
    (GOOD.replace('"x" .', '"x"'), "a statement that does not end"),
    (GOOD.replace('"x"', '"café"'), "not ASCII"),
    (GOOD.replace("\n", "\r\n"), "not ASCII with LF"),
    (GOOD.replace("    a", "\ta"), "no tab"),
    (GOOD.rstrip("\n"), "final line feed"),
    (GOOD.replace("sh:NodeShape ;", "sh:NodeShape ] [ ;"), "a bracket closed before it opened"),
    (GOOD + "\nz:b a:c a:d .\n", "the prefix z: is used and not declared"),
])
def test_the_turtle_sanity_check_names_each_fault_and_passes_what_has_none(text, found):
    from p4_helpers import turtle_problems as check
    got = check(text)
    if found is None:
        assert got == []
    else:
        assert any(found in g for g in got), (found, got)


def test_a_string_with_brackets_and_an_iri_with_a_hash_do_not_confuse_the_sanity_check():
    text = GOOD.replace('"x"', '"a [ ( \\" # not a bracket"').replace("urn:x", "urn:x#frag")
    assert turtle_problems(text) == []
    assert turtle_problems(p4_turtle.render([Shape(id="urn:s", pattern="^[(]$")], (("sh", "http://www.w3.org/ns/shacl#"),),
                                            ["x"])) == []
