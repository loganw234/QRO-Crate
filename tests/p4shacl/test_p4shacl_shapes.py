"""The shapes' own files, as an engine reads them (P4's design, item 5): each is SHACL, by the SHACL-SHACL shapes that ship with
pyshacl, alone and together, which is what rocrate-validator does with a profile's files; the shapes named are the shapes the
generator makes; each carries the severity of its folder and so does every property shape it reports through; and the claims
an engine reads are the model's. The quick stage reads the same properties off the model and the text. This stage reads them off
the Turtle, with a parser that is not mine, and a slip of the writer shows only here: a wrong `sh:` name, a list written wrong,
a severity in the wrong place."""
import pytest
from p4shacl_helpers import ROOT, run_engine, shape_files
from qro import p4_shapes as H
from qro import vocabulary as V
from qro.p4_model import SEVERITY

FILES = shape_files()
CLAIMS = V.PROFILE + "#claims"
FOLDER = {"must": "Violation", "should": "Warning"}


@pytest.fixture(scope="module")
def engine():
    jobs = [{"id": "all", "kind": "meta", "shapes": FILES}] + [
        {"id": f, "kind": "meta", "shapes": [f]} for f in FILES] + [
        {"id": "read", "kind": "shapes", "shapes": FILES, "claims_predicate": CLAIMS}]
    answers, _ = run_engine(jobs)
    return answers


def test_the_files_are_the_four_the_generator_writes_in_the_layout_rocrate_validator_reads():
    base = ROOT / "profile" / "validator" / "qro-crate"
    assert [p.replace("\\", "/").split("qro-crate/")[1] for p in FILES] == [
        "must/1_structure.ttl", "must/2_terms.ttl", "must/3_domains.ttl", "should/1_absence.ttl"]
    assert (base / "profile.ttl").is_file() and sorted(d.name for d in base.iterdir() if d.is_dir()) == ["must", "should"]


@pytest.mark.parametrize("which", ["all"] + FILES, ids=["all four together"] + [f.rsplit("/", 2)[1] + "/" + f.rsplit("/", 1)[1]
                                                                                 for f in FILES])
def test_the_shapes_are_shacl_by_the_shacl_shacl_shapes_of_the_engine(engine, which):
    a = engine[which]
    assert a["ok"], a.get("error")
    assert a["conforms"] is True, a["text"][:600]


def test_the_engine_reads_the_shapes_the_generator_makes_and_no_other(engine):
    read = engine["read"]["shapes"]
    assert set(read) == {s.id for s in H.build()}
    assert engine["read"]["triples"] > 2000


def test_each_shape_has_the_severity_of_its_folder_and_every_property_shape_it_reports_through_has_it_too(engine):
    read = engine["read"]["shapes"]
    for path, shapes in H.groups().items():
        want = FOLDER[H.level_of(path)]
        assert SEVERITY[H.level_of(path)] == want
        for s in shapes:
            got = read[s.id]
            assert got["severity"] == want, s.id
            assert set(got["properties"]) <= {want}, (s.id, got["properties"])
            assert len(got["properties"]) == len(s.props), s.id


def test_the_claims_the_engine_reads_are_the_models(engine):
    read = engine["read"]["shapes"]
    for s in H.build():
        assert read[s.id]["claims"] == sorted(s.claims), s.id


def test_a_shape_nested_in_an_alternative_has_no_severity_the_engine_reads_as_a_result_of_its_own(engine):
    """profile-entities holds its per-profile shapes in sh:or: they are not reported through, and carry none."""
    got = engine["read"]["shapes"][H.shape_iri("profile-entities")]
    assert got["properties"] == [] and got["severity"] == "Violation"


def test_the_meta_check_is_not_vacuous_a_shape_that_is_not_shacl_is_refused_and_one_that_is_is_not():
    """A check that nothing fails proves nothing, so it is shown refusing four malformed shapes, each in its own graph, and
    accepting a good one. (The inference argument of the engine's meta check makes no difference to these five: MEASURED
    with inference rdfs, none and unset.)"""
    p = "@prefix sh: <http://www.w3.org/ns/shacl#> .\n@prefix ex: <http://example.org/> .\n"
    bad = {"a count that is text": p + 'ex:b a sh:NodeShape ; sh:property [ sh:path ex:p ; sh:minCount "x" ] .\n',
           "a property shape with no path": p + "ex:b a sh:NodeShape ; sh:property [ sh:minCount 1 ] .\n",
           "closed that is text": p + 'ex:b a sh:NodeShape ; sh:closed "yes" .\n',
           "a node kind that is no kind": p + "ex:b a sh:NodeShape ; sh:nodeKind ex:NotAKind .\n"}
    good = p + "ex:g a sh:NodeShape ; sh:property [ sh:path ex:p ; sh:minCount 1 ] .\n"
    jobs = [{"id": k, "kind": "meta", "shapes": v} for k, v in bad.items()] + [{"id": "good", "kind": "meta", "shapes": good}]
    answers, _ = run_engine(jobs)
    assert answers["good"]["ok"] and answers["good"]["conforms"] is True
    for k in bad:
        assert answers[k]["ok"] and answers[k]["conforms"] is False, k

