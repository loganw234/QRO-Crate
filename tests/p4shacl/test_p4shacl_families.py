"""The second verifier's three families of crates through a real engine (P4's verifier, round 2, defects 1 and 2; the lead's ruling of
2026-10-26T11:18:27Z): an @id added again, a File added whose file the disk lacks or is a link, a top-level @context of the crate's own
and a top-level key. tests/p4/test_p4_families.py holds the claims over them with the evaluator; the evaluator abstains from the 13
that change the @context or the top level, and a real engine does not: it reads the crate's own context and fails shapes on a crate
the checker has refused `context`. Held here, in one engine run over the 13 that change the @context or the top level, the 68 added
Files, the 4 paths the reader holds as one, and every third of the 384 @ids added again (each of the 63 terms is among them, on two
entities at least; the evaluator holds all 388 in the quick stage, and the engine's agreement with it is shown on this sample, as
on 4,350 crates the second verifier made):
  - on every crate the evaluator reads, the engine fails the must shapes the evaluator does;
  - on every crate, the engine fails no must shape where steps 1 to 3 accept the crate (A), and the refusal is claimed by one of
    the shapes it fails (B);
  - the engine reads at least one crate with a changed context, and fails a must shape on six of the eight variants, each of
    which claims `context`;
  - each name FORM adds is needed: with it taken away, the engine's failures leave a crate unclaimed, and `context`, which the
    evaluator cannot see, is among them."""
import pytest
from p4shacl_helpers import failing_must, quick_stage_module, run_engine, shape_files, unclaimed
from qro import canonical, checker, fixture
from qro import p4_examples as X
from qro import p4_shapes as H
from qro import vocabulary as V

sweeps = quick_stage_module("p4_sweeps")
SHAPES = H.build()
EVERY = 3


@pytest.fixture(scope="module")
def work():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(checker, "STEPS", {n: None for n in range(4, 9)})
        mp.setattr(checker, "RAW_FORMS", {})
        mp.setattr(checker, "COUNTS", [])
        mp.setattr(checker, "GENERATORS", {})
        fixture.register()
        checker.load()
        with X.Workspace(SHAPES) as w:
            yield w


@pytest.fixture(scope="module")
def judged(work):
    """{name: (the metadata, the checker's refusal at steps 1 to 3 or "ok", the evaluator's must shapes or None where it abstains,
    the engine's must shapes)} for the crates of the three families the engine reads, from one engine run."""
    crates = []
    again = len(work.pristine["@graph"]) * (1 + len(V.TERMS))                # the @ids added again come first
    for i, (name, apply, files) in enumerate(sweeps.families(work.pristine)):
        if i < again and i % EVERY:
            continue
        md = sweeps.crate_of(work.pristine, apply)
        assert md is not None, name
        crates.append((name, md, sweeps.early(work, md, files)))
    jobs = [{"id": name, "kind": "crate", "metadata": canonical.dumps(md).decode("ascii"), "shapes": shape_files()}
            for name, md, _ in crates]
    answers, _ = run_engine(jobs, timeout=1500)
    out = {}
    for name, md, early in crates:
        got = answers[name]
        assert got["ok"], (name, got.get("error"))
        must, _, why = X.shapes_verdict(md, SHAPES)
        out[name] = (md, early, None if why else must, tuple(failing_must(got)))
    return out


def test_the_engine_fails_the_must_shapes_the_evaluator_fails_on_every_crate_of_the_families_the_evaluator_reads(judged):
    read = {name: (must, engine) for name, (_, _, must, engine) in judged.items() if must is not None}
    assert len(judged) == 128 + 4 + 13 + 68 and len(read) == len(judged) - 13
    assert {name: (list(must), list(engine)) for name, (must, engine) in read.items() if tuple(must) != engine} == {}
    assert sum(bool(engine) for _, engine in read.values()) >= 170                           # 186 of 200 when it was written


def test_a_real_engine_fails_no_must_shape_where_steps_1_to_3_accept_the_crate_and_the_shapes_it_fails_claim_the_refusal(judged):
    claims = {X.local(s.id): s.claims for s in SHAPES}
    cases = [(name, early, list(engine)) for name, (_, early, _, engine) in judged.items()]
    accepted = [name for name, early, _ in cases if early == "ok"]
    assert len(accepted) == 3 and [name for name, early, engine in cases if early == "ok" and engine] == []      # none is stricter
    assert unclaimed(cases, claims) == []
    assert sum(bool(engine) for _, _, engine in cases) >= 180                                  # 197 of 213 when it was written: not vacuous


def test_the_engine_reads_a_crate_with_a_context_of_its_own_and_fails_a_must_shape_on_six_of_the_eight_variants(judged, work):
    variants = {name: v for name, v in judged.items() if name.startswith("context ")}
    assert len(variants) == 8 and all(md["@context"] != work.pristine["@context"] for md, _, _, _ in variants.values())
    claims = {X.local(s.id): s.claims for s in SHAPES}
    for name, (md, early, must, engine) in variants.items():
        assert early == "context" and must is None, name                  # the checker refuses it, and the evaluator abstains
        assert all("context" in claims[s] for s in engine), (name, engine)
    failing = {name: engine for name, (_, _, _, engine) in variants.items() if engine}
    assert len(failing) == 6, sorted(failing)                             # not `sets @vocab`, nor `defines a term nobody uses`
    assert {"entity", "root"} <= {s for engine in failing.values() for s in engine}
    assert variants["context redefines name"][3] == ("entity", "profile-entities", "root")         # the verifier's first case


def test_a_top_level_key_is_refused_graph_form_and_the_shapes_the_engine_fails_claim_it_the_reverse_one_among_them(judged):
    top = {name: v for name, v in judged.items() if name.startswith("top level ")}
    assert len(top) == 5 and {early for _, early, _, _ in top.values()} == {"graph-form"}
    claims = {X.local(s.id): s.claims for s in SHAPES}
    assert top["top level an @reverse"][3] == ("term-name",)              # read as a second name of the root: no `spelling` there
    assert all("graph-form" in claims[s] for _, _, _, engine in top.values() for s in engine)


@pytest.mark.parametrize("name, crates", [("context", ("context ",)), ("graph-form", ("top level ", "again ", "case clash", "a File where")),
                                          ("file-missing", ("added",)), ("file-link", ("added File at a link",))])
def test_each_refusal_of_form_the_engine_needs_is_found_missing_by_the_crates_it_leaves_unclaimed(judged, monkeypatch, name, crates):
    """With `name` taken out of FORM, the engine's failures on some crate of the families leave the checker's refusal claimed by
    none of the shapes it fails. `context` is seen here and nowhere else: the evaluator abstains from those crates."""
    monkeypatch.setattr(H, "FORM", tuple(f for f in H.FORM if f != name))
    poor = {X.local(s.id): s.claims for s in H.build()}
    cases = [(n, early, list(engine)) for n, (_, early, _, engine) in judged.items()]
    found = unclaimed(cases, poor)
    assert found and all(n.startswith(crates) for n in found), (name, found[:4])
    if name == "context":
        assert len(found) == 6                                            # the six variants a real engine fails a shape on
    if name == "graph-form":
        assert "top level an @reverse" in found                           # and the one the evaluator cannot read is among them
    if name == "file-link":
        assert len(found) == 3                                            # the three links on which a must shape fails
