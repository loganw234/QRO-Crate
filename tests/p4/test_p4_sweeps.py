"""The claims, held by sweeps (P4's verifier, round 1, defect 2): single edits of the fixture, and crates with a key spelt
another way, each judged by steps 1 to 3 of the checker and by the evaluator.

What the sweeps hold, and over what: when a must shape fails on such a crate the checker refuses it (never stricter), and
the checker's refusal is a name that one of the failing shapes claims. The 21 classes of edits the verifier found are
named and held here, with five edits of P4's own that alone notice a claim (`MORE`); so are every 6th edit of its whole
pool and every alias crate. The whole pool (12,591 edits) and the alias crates through a real engine are in
tests/p4shacl/test_p4shacl_sweeps.py. The second verifier's three families of crates, which this pool never makes (an @id added
again, a context or top-level key of the crate's own, a File added), are in tests/p4/test_p4_families.py and
tests/p4shacl/test_p4shacl_families.py. The sweep is watched failing on a claim that leaves out the refusal and on a shape
stricter than the checker."""
import dataclasses

import pytest
from p4_helpers import prepare
from p4_sweeps import CLASSES, MORE, add_entity, alias_crates, alias_problems, both, crate_of, early, edits, judge, listed, sweep
from qro import p4_examples as X
from qro import p4_shapes as H
from qro import vocabulary as V
from qro.p4_model import Shape


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
def shapes():
    return H.build()


def test_the_pool_is_the_verifiers_and_its_classes_are_all_in_it(work):
    names = [n for n, _ in edits(work.pristine)]
    assert len(names) == 12591 and set(CLASSES) | set(MORE) <= set(names)
    assert len(CLASSES) == len(set(CLASSES)) == 35          # 21 classes, two edits of each where it has two
    assert len(MORE) == len(set(MORE)) == 5 and not set(MORE) & set(CLASSES)


def test_each_of_the_21_classes_has_a_must_shape_fail_and_the_checkers_refusal_claimed(work, shapes):
    r = sweep(work, shapes, only=set(CLASSES) | set(MORE))
    assert r["A"] == [] and r["B"] == {} and r["U"] == [], r
    assert r["held"] == r["n"] >= len(CLASSES) + len(MORE) and r["unreadable"] == 0   # every one makes a must shape fail, none is vacuous


def test_every_6th_single_edit_of_the_pool_is_refused_by_a_name_a_failing_shape_claims(work, shapes):
    r = sweep(work, shapes, stride=6, offset=0)
    assert r["A"] == [] and r["B"] == {} and r["U"] == [], (r["A"][:3], list(r["B"].items())[:3], r["U"][:3])
    assert r["n"] >= 2000 and r["held"] >= 1700 and len(r["failing"]) >= 100         # and the sweep is not vacuous


def test_every_alias_key_crate_is_refused_and_the_shapes_that_fail_claim_the_refusal(work, shapes):
    crates = alias_crates(work)
    assert len(crates) == 2 * (len(V.TERMS) - 1) == 124
    assert alias_problems(work, shapes) == []


def test_the_claims_of_a_must_shape_are_its_own_refusals_then_the_six_of_form():
    for s in shapes_of_the_table():
        if s.level == "must":
            assert s.claims[-len(H.FORM):] == H.FORM or set(H.FORM) <= set(s.claims), s.id
            assert len(s.claims) == len(set(s.claims)), s.id
        else:
            assert s.claims == (), s.id
    assert H.claims_of("graph-form") == ("graph-form", "spelling", "term-unknown", "context", "file-missing", "file-link")
    assert H.claims_of("spelling") == ("spelling", "term-unknown", "graph-form", "context", "file-missing", "file-link")
    assert H.claims_of("term-unknown") == ("term-unknown", "spelling", "graph-form", "context", "file-missing", "file-link")
    assert H.claims_of("file-link", "x") == ("file-link", "x", "spelling", "term-unknown", "graph-form", "context", "file-missing")
    assert H.FORM == ("spelling", "term-unknown", "graph-form", "context", "file-missing", "file-link")


def shapes_of_the_table():
    return H.build()


# -- the sweeps, watched failing ------------------------------------------------------------------------------------------------
def with_claims(shapes, local, claims):
    return [dataclasses.replace(s, claims=claims) if X.local(s.id) == local else s for s in shapes]


@pytest.mark.parametrize("local, left_out", [("term-name", "term-unknown"), ("root", "spelling"), ("file-reached", "graph-form"),
                                             ("domain-conformsto", "term-unknown"), ("file-reached", "file-unlisted"),
                                             ("file-digest-present", "file-digest"), ("file-digest-present", "raw-digest")])
def test_a_claim_that_leaves_out_one_of_the_refusals_is_found_by_the_classes_and_the_alias_crates(work, shapes, local, left_out):
    real = {X.local(s.id): s.claims for s in shapes}[local]
    assert left_out in real
    poor = with_claims(shapes, local, tuple(c for c in real if c != left_out))
    found = sweep(work, poor, only=set(CLASSES) | set(MORE))["B"]
    assert found or alias_problems(work, poor), (local, left_out)


def test_the_alias_crates_find_a_claim_that_lacks_the_refusal_of_an_alias_key(work, shapes):
    """The claim check of the alias crates is held on its own: the class sweep can find a poor claim too, and then a
    check that never flagged one would go by in the test above."""
    real = {X.local(s.id): s.claims for s in shapes}["term-sha256"]
    poor = with_claims(shapes, "term-sha256", tuple(c for c in real if c not in H.FORM))
    assert alias_problems(work, shapes) == []
    found = [p for p in alias_problems(work, poor) if p.startswith("a:sha256:")]          # a second sha256, spelt schema:sha256
    assert len(found) == 1 and "is refused term-unknown" in found[0] and "['term-sha256'] fail and claim []" in found[0], found


def test_the_checker_refuses_every_alias_key_crate_as_limit_5_says(work):
    """Limit 5: `term-unknown`, and `graph-form` on the descriptor and on a contextual Profile entity. The day the table or
    the checker moves one more crate to another name, this fails, and the limit is restated."""
    names = {name: early(work, md) for name, (_, _, md) in alias_crates(work).items()}
    assert set(names.values()) == {"term-unknown", "graph-form"}, sorted(set(names.values()))
    assert sorted(n for n, e in names.items() if e == "graph-form") == ["a:conformsTo", "a:version"]
    host = {n: [e for e in md["@graph"] if a in e] for n, (_, a, md) in alias_crates(work).items() if n in ("a:conformsTo", "a:version")}
    assert [e["@id"] for e in host["a:conformsTo"]] == ["ro-crate-metadata.json"]
    assert [e["@type"] for e in host["a:version"]] == [["CreativeWork", "Profile"]]


def test_a_shape_stricter_than_the_checker_is_found_by_the_sweep(work, shapes):
    stricter = Shape(id=H.shape_iri("never-true"), targets=(("class", H.term_iri("Dataset")),), pattern="impossible$",
                     claims=H.claims_of("graph-form"))
    benign = {'set ./.qro:writer="2026-10-14"', 'set data/notes.txt.name="1/2"', 'set data/raw.counts.json.encodingFormat="1"'}
    assert sweep(work, shapes, only=benign)["A"] == []                       # the checker accepts these, and the real shapes agree
    r = sweep(work, list(shapes) + [stricter], only=benign)
    assert sorted(name for name, _ in r["A"]) == sorted(benign) and all(must == ("never-true",) for _, must in r["A"])


def test_the_sweep_counts_a_crate_the_expansion_cannot_read_and_the_checker_refuses_and_flags_none(work, shapes):
    r = sweep(work, shapes, only={'set ./.hasPart={"@id": "x y"}'})
    assert r["n"] == 1 and r["unreadable"] == 1 and r["A"] == [] and r["B"] == {} and r["U"] == []


def test_a_crate_the_expansion_cannot_read_and_the_checker_accepts_is_found_by_the_sweep(work, shapes, monkeypatch):
    """The lead's ruling of 2026-10-16T14:58:58Z, after P0.5: the sweep never skips a crate the expansion refuses. Here the
    expansion is made to refuse every crate, and the edits the checker accepts at steps 1 to 3 are named; the one it refuses
    (a license that is an empty list) is only counted."""
    accepted = {'set ./.qro:writer="2026-10-14"', 'set data/notes.txt.name="1/2"', 'set data/raw.counts.json.encodingFormat="1"'}
    refused = 'set ./.license=[]'
    monkeypatch.setattr(X, "shapes_verdict", lambda md, shapes: ((), (), "refused by the test"))
    r = sweep(work, shapes, only=accepted | {refused})
    assert sorted(r["U"]) == sorted(accepted) and r["unreadable"] == 1 and r["n"] == 4 and r["held"] == 0


# -- step 3: pinned as steps 1 and 2 are (the third verifier, note 5) --------------------------------------------------------------
def test_each_refusal_of_step_3_is_form_s_or_claimed_by_the_shape_that_mirrors_it_or_no_one_edit_fails_a_must_shape_under_it(work, shapes):
    """tests/p4/test_p4_shapes.py pins steps 1 and 2 against the vocabulary's refusals; the pin stopped there. Step 3 refuses
    `graph-form` (FORM's), `raw-form` (claimed by `rawresult-form`, which asks the raw result its form) and `count-unpaid`, which no
    shape claims: RDF holds `qro:shots` as the number it is and cannot compare it with the bytes, so the crate one edit away that
    reaches it, a stated count the file does not hold, conforms to every must shape and nothing is left unclaimed. The sweeps hold
    the rest over the pool (every `qro:shots` among its edits). A refusal P0 adds to step 3 is a decision here, not a silence."""
    late = {r.name for r in V.REFUSALS if "step 3" in r.where.split("; ")}
    assert late == {"graph-form", "raw-form", "count-unpaid"}, sorted(late)
    own = {X.local(s.id): s.claims for s in H.build(widen=False)}
    claims = {X.local(s.id): s.claims for s in shapes}
    assert "graph-form" in H.FORM and "count-unpaid" not in H.FORM and "raw-form" not in H.FORM
    assert [n for n, c in own.items() if "raw-form" in c] == ["rawresult-form"]
    assert [n for n, c in claims.items() if "count-unpaid" in c] == []
    wrong_count = work.fresh()
    next(e for e in wrong_count["@graph"] if e["@id"] == X.RAW)["qro:shots"] += 1
    wrong_count = X.arranged(wrong_count)
    assert early(work, wrong_count) == "count-unpaid" and judge(work, shapes, wrong_count, claims)[0] == "conforms"
    no_form = work.fresh()
    del next(e for e in no_form["@graph"] if e["@id"] == X.RAW)["qro:rawForm"]
    assert judge(work, shapes, X.arranged(no_form), claims) == ("held", "raw-form", ("rawresult-form",))
    shots = {name for name, _ in edits(work.pristine) if "qro:shots" in name}
    assert len(shots) >= 20 and sweep(work, shapes, only=shots)["B"] == {}                 # and the pool reaches it, and holds


# -- limit 4: a remote File with a sha256 (the third verifier, D2, MEASURED) -------------------------------------------------------------
@pytest.mark.parametrize("ident", ["https://example.org/f", "urn:x:y"])
@pytest.mark.parametrize("size", [False, True], ids=["no contentSize", "a contentSize"])
def test_a_remote_file_with_a_sha256_is_refused_graph_form_and_the_shapes_conform_where_the_root_lists_it_and_fail_file_reached_where_it_does_not(
        work, shapes, ident, size):
    """sha256 stands only on a File the crate holds, so the checker refuses a remote File that carries one, whether the root
    lists it or not. The shapes read any File: listed, it conforms (a thing only the checker sees); unlisted, `file-reached`
    fails, and it claims `graph-form`, the checker's name. Limit 4 says so."""
    claims = {X.local(s.id): s.claims for s in shapes}
    entity = {"@id": ident, "@type": "File", "sha256": "a" * 64, **({"contentSize": "6"} if size else {})}
    unlisted = crate_of(work.pristine, add_entity(entity))
    in_root = crate_of(work.pristine, both(add_entity(entity), listed(ident)))
    assert early(work, unlisted) == early(work, in_root) == "graph-form"
    kind, refusal, failing = judge(work, shapes, unlisted, claims)
    assert (kind, refusal, failing) == ("held", "graph-form", ("file-reached",)) and "graph-form" in claims["file-reached"]
    assert judge(work, shapes, in_root, claims)[0] == "conforms"


# -- the six realistic cases of the report (its probe5.py), with what the checker and the shapes each say --------------------------
def rename(md, old, new):
    for e in md["@graph"]:
        if e["@id"] == old:
            e["@id"] = new


PROBE5 = {
    "the root gets a second name spelt schema:name": (
        lambda md: md["@graph"][1].__setitem__("schema:name", "another name"), "term-unknown", ("term-name",)),
    "sha256 spelt schema:sha256 on a CreativeWork": (
        lambda md: md["@graph"].append({"@id": "#x", "@type": "CreativeWork", "schema:sha256": "a" * 64}),
        "term-unknown", ("domain-sha256", "file-reached")),
    "license is an empty list": (lambda md: md["@graph"][1].__setitem__("license", []), "spelling", ("root",)),
    "a file is renamed in its own entity only": (
        lambda md: rename(md, "data/notes.txt", "data/notes2.txt"), "graph-form", ("file-reached",)),
    "hasPart is one object, not a list": (
        lambda md: md["@graph"][1].__setitem__("hasPart", {"@id": "data/notes.txt"}), "spelling", ("file-reached",)),
    "an entity's @type is a list of one": (lambda md: md["@graph"][2].__setitem__("@type", ["File"]), "spelling", ()),
}


@pytest.mark.parametrize("why", sorted(PROBE5))
def test_the_realistic_cases_of_the_report_are_refused_by_a_name_the_failing_shapes_claim(work, shapes, why):
    edit, refusal, failing = PROBE5[why]
    md = work.fresh()
    edit(md)
    md = X.arranged(md)
    must, _, unreadable = X.shapes_verdict(md, shapes)
    assert unreadable == "" and early(work, md) == refusal and must == failing, (early(work, md), must)
    claims = {X.local(s.id): s.claims for s in shapes}
    assert not must or refusal in {c for s in must for c in claims[s]}
