"""The shapes are for an engine run without inference (limit 2; the fourth verifier's most consequential note, MEASURED): on the
accepted fixture crate pyshacl 0.40.1 conforms with inference `none`, its default and the only mode this stage reads the shapes
with elsewhere, and fails with `rdfs`, `owlrl` and `both`, on `descriptor`, `entity` and `profile-entities`, with the counts the
README and every Turtle banner quote (qro.p4_profile.INFERENCE and INFERENCE_SHAPES). The shapes judge the graph a crate says; an
inference adds triples to it that these shapes do not allow, so a user who runs the shapes under an inference sees a good crate
fail, and the documents say not to."""
import pytest
from p4shacl_helpers import failing_must, run_engine, shape_files
from qro import canonical
from qro import p4_examples as X
from qro import p4_profile as P
from qro import p4_shapes as H

MODES = ("none", "rdfs", "owlrl", "both")


@pytest.fixture(scope="module")
def metadata():
    with X.Workspace(H.build()) as work:
        return canonical.dumps(work.fresh()).decode("ascii")


@pytest.fixture(scope="module")
def answers(metadata):
    jobs = [{"id": mode, "kind": "crate", "metadata": metadata, "shapes": shape_files(), "inference": mode} for mode in MODES]
    got, versions = run_engine(jobs)
    assert versions == {"pyshacl": "0.40.1", "rdflib": "7.6.0"}
    for mode in MODES:
        assert got[mode]["ok"], (mode, got[mode].get("error"))
    return got


def test_with_no_inference_the_accepted_fixture_crate_conforms_to_every_shape(answers):
    assert answers["none"]["conforms"] is True and answers["none"]["results"] == []


def test_with_rdfs_owlrl_or_both_the_same_crate_is_failed_with_the_counts_the_documents_quote(answers):
    got = {mode: len(answers[mode]["results"]) for mode in MODES[1:]}
    assert got == P.INFERENCE, got
    for mode in MODES[1:]:
        assert answers[mode]["conforms"] is False


def test_it_is_the_closed_shapes_that_fail_and_no_other_must_shape_in_each_mode(answers):
    failing = {mode: failing_must(answers[mode]) for mode in MODES[1:]}
    assert failing == {mode: sorted(P.INFERENCE_SHAPES) for mode in MODES[1:]}, failing        # the shapes the documents name
    for mode in MODES[1:]:
        assert {r["severity"] for r in answers[mode]["results"]} == {"Violation"}


def test_a_job_that_names_no_inference_runs_with_none_the_mode_the_shapes_are_for(metadata):
    got, _ = run_engine([{"id": "x", "kind": "crate", "metadata": metadata, "shapes": shape_files()}])
    assert got["x"]["ok"] and got["x"]["conforms"] is True and got["x"]["results"] == []


def test_the_job_refuses_an_inference_mode_pyshacl_does_not_have(metadata):
    got, _ = run_engine([{"id": "x", "kind": "crate", "metadata": metadata, "shapes": shape_files(), "inference": "everything"}])
    assert got["x"]["ok"] is False and "inference is one of none, rdfs, owlrl, both" in got["x"]["error"]
