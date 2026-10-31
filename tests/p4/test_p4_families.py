"""The second verifier's three families of crates (P4's verifier, round 2, defects 1 and 2; the lead's ruling of 2026-10-26T11:18:27Z).
The first verifier's pool deletes, sets, retypes and renames what the fixture has, so it never added an entity under an old
@id, a File, or a top-level key, and the claims were true of what it made: a must shape failed on such a crate where the checker
refused by a name no failing shape claimed. The families make them (tests/p4/p4_sweeps.py: `duplicates`, `contexts`,
`added_files`), and FORM names the refusals they are refused by. Held here, without an engine:
  - each family is what it says, and no crate of it is in the first verifier's pool;
  - every crate of the three is refused by a name a failing shape claims, and none is accepted by steps 1 to 3 while a must
    shape fails (A), claimed by none (B), or read by the expansion and accepted (U);
  - each name FORM adds is needed: with it taken away, the sweeps find a crate the shapes fail under a name no shape claims.
    `context` is the one the evaluator cannot see, for it abstains from a context of the crate's own: the engine stage reads
    those crates through pyshacl (tests/p4shacl/test_p4shacl_families.py);
  - the crates the checker accepts conform, and a shape stricter than the checker is found by them;
  - a File added at the path of a link is refused `file-link`: a junction on Windows, which needs no privilege (a symbolic link
    needs one there), a symbolic link elsewhere, made the way tests/format/test_hostile.py makes one."""
import dataclasses

import pytest
from p4_helpers import prepare
from p4_sweeps import (CLASHES, CLASSES, LINK, MORE, TOP_LEVEL, added_files, alias_problems, context_variants, contexts, crate_of,
                       duplicates, early, edits, families, judge, sweep)
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


def test_the_families_are_the_three_the_second_verifier_found_and_none_of_their_crates_is_in_the_pool(work):
    base = work.pristine
    assert len(base["@graph"]) == 6 and len(duplicates(base)) == 6 * (1 + len(V.TERMS)) + len(CLASHES) == 388
    assert len(contexts(base)) == len(context_variants()) + len(TOP_LEVEL) == 8 + 5 == 13 and "an @reverse" in TOP_LEVEL
    assert len(added_files(base)) == 2 * 2 * 2 * 2 * 2 * 2 + 4 == 68 and LINK == "data/jct"
    names = [entry[0] for entry in families(base)]
    assert len(names) == len(set(names)) == 469 and not set(names) & {entry[0] for entry in edits(base)}


def test_every_crate_of_the_families_is_refused_by_a_name_a_failing_shape_claims_and_none_is_accepted_while_a_shape_fails(work, shapes):
    r = sweep(work, shapes, pool=families)
    assert r["A"] == [] and r["B"] == {} and r["U"] == [], (r["A"][:3], list(r["B"].items())[:3], r["U"][:3])
    assert r["n"] == 469 and r["unreadable"] == 13                       # the evaluator abstains from the 13 contexts and top-level keys
    assert r["held"] >= 400 and len(r["failing"]) >= 70                  # and the sweep is not vacuous: 430 and 78 when it was written


def test_the_checker_says_context_of_a_context_of_the_crates_own_and_graph_form_of_a_top_level_key(work):
    found = {}
    for name, apply in contexts(work.pristine):
        found[name] = early(work, crate_of(work.pristine, apply))
    assert {n: e for n, e in found.items() if n.startswith("context ")} == {n: "context" for n in found if n.startswith("context ")}
    assert {n: e for n, e in found.items() if n.startswith("top level ")} == {n: "graph-form" for n in found if n.startswith("top level ")}
    assert len(found) == 13


@pytest.mark.parametrize("name, seen_by", [("spelling", "the classes"), ("term-unknown", "the alias crates"), ("graph-form", "the families"),
                                           ("file-missing", "the families"), ("file-link", "the families")])
def test_each_refusal_of_form_the_evaluator_can_see_is_needed_by_a_crate_the_sweeps_make(work, monkeypatch, name, seen_by):
    """With `name` taken out of FORM, the sweeps find a crate on which a must shape fails and the checker's refusal is claimed by
    none of the failing shapes. Which sweep sees it is said: the 21 classes and five edits of P4's own, the alias-key crates, or
    the three families. `context` is the engine stage's (the evaluator abstains from a context of the crate's own)."""
    assert name in H.FORM
    monkeypatch.setattr(H, "FORM", tuple(f for f in H.FORM if f != name))
    poor = H.build()
    own = {X.local(s.id): s.claims for s in H.build(widen=False)}
    assert all(name not in s.claims or name in own[X.local(s.id)] for s in poor), "the name is left in a shape that does not mirror it"
    names = [entry[0] for entry in families(work.pristine)]
    mine = {"graph-form": [n for n in names if n.startswith(("again", "case clash", "a File where"))],
            "file-missing": [n for n in names if n.startswith("added")], "file-link": [n for n in names if "a link" in n]}.get(name)
    found = {"the classes": lambda: sweep(work, poor, only=set(CLASSES) | set(MORE))["B"],
             "the alias crates": lambda: alias_problems(work, poor),
             "the families": lambda: sweep(work, poor, pool=families, only=set(mine))["B"]}[seen_by]()
    assert found, (name, seen_by)
    if name == "file-link":
        assert all(any("link" in n for n in ns) for ns in found.values()), found
    if name == "file-missing":
        assert {refusal for refusal, _ in found} == {"file-missing"}, found
    if name == "graph-form":
        assert {refusal for refusal, _ in found} == {"graph-form"}, found


def test_a_File_added_at_the_path_of_a_link_is_refused_file_link_and_the_shapes_that_fail_claim_it(work, shapes):
    """The ruling claimed `file-link` from reading checker.walk, the host being thought unable to make a link (a symbolic link
    needs a privilege here that it lacks). A directory junction needs none, so it is planted: at the path of a File entity added
    with and without a digest and a size, listed or not, where the walk refuses the link before it reads the entity."""
    base, claims = work.pristine, {X.local(s.id): s.claims for s in shapes}
    links = [(n, a, f) for n, a, f in added_files(base) if "link" in n]
    assert len(links) == 4 and all(f is not None for _, _, f in links)
    kinds = {}
    for name, apply, files in links:
        md = crate_of(base, apply)
        assert early(work, md, files) == "file-link", name
        kinds[name] = judge(work, shapes, md, claims, files)
    assert {n: (k, tuple(m)) for n, (k, _, m) in kinds.items()} == {
        f"added File at a link {LINK}": ("held", ("file-digest-present",)),
        f"added File at a link {LINK}, listed": ("held", ("file-digest-present",)),
        f"added File at a link {LINK} with a digest and a size": ("held", ("file-reached",)),
        f"added File at a link {LINK} with a digest and a size, listed": ("conforms", ())}


def test_the_crates_the_checker_accepts_conform_and_a_stricter_shape_is_found_by_them(work, shapes):
    accepted = [(n, a, f) for n, a, f in families(work.pristine) if early(work, crate_of(work.pristine, a), f) == "ok"]
    assert sorted(n for n, _, _ in accepted) == sorted([
        'added "File" x.txt with a digest with a size, listed, on disk', 'added "File" data/x.txt with a digest with a size, listed, on disk',
        "case clash of a CreativeWork"])
    claims = {X.local(s.id): s.claims for s in shapes}
    assert {judge(work, shapes, crate_of(work.pristine, a), claims, f)[0] for _, a, f in accepted} == {"conforms"}
    stricter = Shape(id=H.shape_iri("never-true"), targets=(("class", H.term_iri("File")),), pattern="impossible$",
                     claims=H.claims_of("graph-form"))
    got = {n: judge(work, list(shapes) + [stricter], crate_of(work.pristine, a), {**claims, "never-true": stricter.claims}, f)[0]
           for n, a, f in accepted}
    assert set(got.values()) == {"A"} and len(got) == 3                  # the checker accepts each, and the shape that fails them is stricter


def test_a_crate_the_expansion_cannot_read_and_the_checker_accepts_is_found_with_its_files(work, shapes, monkeypatch):
    """The sweep never skips a crate the expansion refuses (P4's verifier, round 1, defect 1), and a crate of the families is
    judged with its files on disk: made to refuse every crate, the expansion leaves the three that steps 1 to 3 accept as `U`, and
    the file that makes two of them accepted is the file the judge stages."""
    monkeypatch.setattr(X, "shapes_verdict", lambda md, shapes: ((), (), "refused by the test"))
    r = sweep(work, shapes, pool=families)
    assert sorted(r["U"]) == sorted([
        'added "File" x.txt with a digest with a size, listed, on disk', 'added "File" data/x.txt with a digest with a size, listed, on disk',
        "case clash of a CreativeWork"])
    assert r["n"] == 469 and r["unreadable"] == 469 - 3 and r["held"] == 0 and r["A"] == [] and r["B"] == {}


def test_a_claim_left_out_of_one_shape_is_found_by_the_families(work, shapes):
    """The families are watched failing on one shape's claim too, not on FORM alone: `term-contentsize` without `graph-form` is
    found by the same size added under an @id the graph has."""
    real = {X.local(s.id): s.claims for s in shapes}["term-contentsize"]
    poor = [dataclasses.replace(s, claims=tuple(c for c in real if c != "graph-form")) if X.local(s.id) == "term-contentsize" else s
            for s in shapes]
    found = sweep(work, poor, pool=families, only={"again data/notes.txt + contentSize", "again data/raw.counts.json + contentSize"})["B"]
    assert [(refusal, must) for refusal, must in found] == [("graph-form", ("term-contentsize",))]
