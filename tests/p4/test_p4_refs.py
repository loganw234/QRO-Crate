"""A reference outside the id rule on each term of spelling `ref`, without an engine (the lead's ruling of 2026-10-19T17:41:46Z:
the shapes of those terms claim `graph-form`; since 2026-10-26T11:18:27Z every must shape does, as FORM). The crates are made
by tests/p4/p4_refs.py: the fixture's metadata with one reference added to each such term. Held here, over a few kinds of
reference:
  - the shape of each such term, and every other must shape, claims `graph-form`;
  - a crate the expansion cannot read is refused by the checker (the gates skip none);
  - where the evaluator reads the crate: no must shape fails on one steps 1 to 3 accept, and the failing shapes of a refused one
    claim the refusal.
A real engine reads a blank node where the evaluator abstains, and that is the engine stage's (tests/p4shacl/test_p4shacl_refs.py)."""
import pytest
from p4_helpers import claims_of, early_verdict, must_failing, prepare
from p4_refs import ACCEPTED, BAD, IRI_LIKE, NO_ENTITY, UNNAMED, crate_with, ref_terms
from qro import canonical
from qro import p4_examples as X
from qro import p4_expand
from qro import p4_shapes as H
from qro import vocabulary as V

SOME = ("_:b0", "./x", "#nowhere", "schema:a", "https://example.org/x")


@pytest.fixture(autouse=True)
def registered(monkeypatch):
    prepare(monkeypatch)


@pytest.fixture(scope="module")
def work():
    with pytest.MonkeyPatch.context() as mp:
        prepare(mp)
        with X.Workspace() as w:
            yield w


@pytest.fixture(scope="module")
def judged(work):
    """[(term, reference, the checker's refusal at steps 1 to 3 or "ok", the triples or None where the expansion cannot read it)]"""
    out = []
    for t in ref_terms():
        for bad in SOME:
            md = crate_with(work.pristine, t, bad)
            data = canonical.dumps(md)
            with work.staged(md) as crate:
                early = early_verdict(crate, data)
            try:
                triples = p4_expand.expand(md)
            except p4_expand.ExpandError:
                triples = None
            out.append((t.key, bad, early, triples))
    return out


def test_the_references_are_of_four_kinds_and_the_terms_are_the_tables_terms_of_spelling_ref():
    assert set(BAD) == set(UNNAMED) | set(NO_ENTITY) | set(IRI_LIKE) | set(ACCEPTED) and len(set(BAD)) == len(BAD)
    terms = ref_terms()
    assert len(terms) >= 18 and all(t.spelling == "ref" for t in terms)
    assert {"about", "conformsTo", "mentions", "license", "hasPart", "instrument", "object", "result"} <= {t.key for t in terms}
    assert set(SOME) <= set(BAD)


def test_the_shape_of_each_term_of_spelling_ref_claims_graph_form_as_does_every_must_shape():
    """The claim of the ruling of 2026-10-19T17:41:46Z, which FORM now holds for every must shape (the ruling of
    2026-10-26T11:18:27Z): a term's own claim is its spelling, and graph-form is one of FORM's."""
    claims, own = claims_of(H.build()), claims_of(H.build(widen=False))
    for t in V.TERMS:
        assert own["term-" + H.slug(t.key)] == ("spelling",), t.key
        assert claims["term-" + H.slug(t.key)][0] == "spelling" and "graph-form" in claims["term-" + H.slug(t.key)], t.key
    assert {t.key for t in ref_terms()} <= {t.key for t in V.TERMS}
    assert all("graph-form" in claims[s.id.split("#", 1)[1]] for s in H.build() if s.level == "must")


def holders(md, key, reference):
    """The entities of the metadata that hold `reference` under `key`, alone or in a list."""
    out = []
    for e in md["@graph"]:
        have = e.get(key)
        if have == {"@id": reference} or (isinstance(have, list) and {"@id": reference} in have):
            out.append(e)
    return out


def test_a_term_is_put_on_a_host_its_domain_admits_and_the_reference_is_added_beside_the_valid_ones(work):
    by_key = {t.key: t for t in ref_terms()}
    md = crate_with(work.pristine, by_key["hasPart"], "#nowhere")
    (host,) = holders(md, "hasPart", "#nowhere")
    assert "Dataset" in canonical.types(host) and host["@id"] == X.HOST          # a host the crate has none of is made, as a plant's is
    md = crate_with(work.pristine, by_key["about"], "_:b0")
    assert next(e for e in md["@graph"] if e["@id"] == V.DESC)["about"] == {"@id": "_:b0"}
    md = crate_with(work.pristine, by_key["qro:line"], "./x")
    (host,) = holders(md, "qro:line", "./x")
    assert "qro:Job" in canonical.types(host)
    md = crate_with(work.pristine, by_key["conformsTo"], "_:b0")
    (host,) = holders(md, "conformsTo", "_:b0")
    assert host["@id"] == V.ROOT and {"@id": V.PROFILE} in host["conformsTo"] and len(host["conformsTo"]) == 3


def test_a_crate_with_a_reference_that_is_no_absolute_iri_is_refused_by_the_checker(judged):
    assert len(judged) == len(ref_terms()) * len(SOME)
    for key, bad, early, _ in judged:
        if bad in UNNAMED + NO_ENTITY + IRI_LIKE:
            assert early in ("graph-form", "spelling"), (key, bad, early)
    assert {early for _, bad, early, _ in judged if bad in UNNAMED + NO_ENTITY} == {"graph-form"}


def test_a_crate_the_expansion_cannot_read_is_refused_by_the_checker_and_none_is_skipped(judged):
    unread = [(key, bad, early) for key, bad, early, triples in judged if triples is None]
    assert len(unread) >= 2 * len(ref_terms())                          # `_:b0` and `./x` on every term
    assert [x for x in unread if x[2] == "ok"] == []


def test_where_the_evaluator_reads_the_crate_no_must_shape_fails_on_one_steps_1_to_3_accept_and_the_failing_claim_the_refusal(judged):
    shapes = H.build()
    claims = claims_of(shapes)
    read = [(key, bad, early, triples) for key, bad, early, triples in judged if triples is not None]
    assert len(read) >= 2 * len(ref_terms())
    failed = 0
    for key, bad, early, triples in read:
        failing = must_failing(shapes, triples)
        if early == "ok":
            assert failing == set(), (key, bad, sorted(failing))
        elif failing:
            failed += 1
            assert early in {c for s in failing for c in claims[s]}, (key, bad, early, sorted(failing))
    assert failed >= 6                                                   # and the check saw refused crates the shapes fail on
