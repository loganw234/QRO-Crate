"""The examples and the plants (qro/p4_examples.py), and gates 1, 3 and 4 of P4's design (item 4.6) over them:
  1. soundness: if a must shape fails, the checker refuses, by a name the failing shapes claim (a plant is one fault; for
     a crate with several, only that it refuses); and no must shape fails on a crate the checker accepts, whether it is
     P0's fixture, an edge case of P4's, or the plant of another parcel whose control row says it is accepted. The
     abstains plants are the ones the evaluator cannot read: the reader refuses their ids (FORMAT.md item 22), so the
     checker has refused the crate, and a gate that skipped them would not know it (limit 19);
  3. coverage: every must shape is made to fail by some plant, or this fails by its name;
  4. the positive example conforms to every shape and is accepted.
Each plant declares what the checker must say and which must shapes must fail, and the tests run both. The checker
that judges is the one the command line has with --fixtures."""
import copy
import tempfile
from pathlib import Path

import pytest
from p4_helpers import (Case, accepted_control_problems, early_verdict, fuzz_problems, mutated, own_name_problems,
                        positive_problems, prepare, session_corpus, soundness_problems, uncovered, valid_mutated)
from qro import canonical, checker, fixture
from qro import p4_examples as X
from qro import p4_expand
from qro import p4_shapes as H
from qro import vocabulary as V


@pytest.fixture(autouse=True)
def registered(monkeypatch):
    prepare(monkeypatch)


@pytest.fixture(scope="module")
def work():
    with pytest.MonkeyPatch.context() as mp:
        prepare(mp)
        with X.Workspace() as w:
            yield w


# -- the plants -------------------------------------------------------------------------------------------------------------------
def test_the_plants_are_named_once_and_each_has_a_family_a_refusal_and_real_shapes():
    plants = X.every_plant()
    names = [p.name for p in plants]
    assert len(names) == len(set(names)) >= 180
    ids = {X.local(s.id) for s in H.build()}
    for p in plants:
        assert p.family in X.FAMILIES, p.name
        assert p.checker in V.REFUSAL or p.checker == X.GENERATED, p.name
        assert set(p.shapes) <= ids, (p.name, set(p.shapes) - ids)
        assert p.fault and callable(p.edit)
        assert not (p.shapes and p.why), "a fault the shapes see needs no excuse for it"
        assert set(p.engine) <= ids and (not p.engine or p.unreadable), p.name       # only a plant the expansion refuses names these
        assert not p.unreadable or (p.why and not p.shapes), p.name                    # and it says why, and declares no evaluator shape
    assert {p.family for p in plants} == set(X.FAMILIES)


def test_the_plants_made_from_the_table_are_a_spelling_fault_a_domain_fault_and_for_one_value_two_a_term():
    made = X.generated()
    assert [p.name for p in made if p.family == "spelling"] == ["spell-" + H.slug(t.key) for t in V.TERMS]
    assert [p.name for p in made if p.family == "domain"] == ["domain-" + H.slug(t.key) for t in V.TERMS
                                                               if "*" not in t.domain]
    assert [p.name for p in made if p.family == "cardinality"] == [
        "many-" + H.slug(t.key) for t in V.TERMS if not t.many and X.valid_values(t) is not None]
    for p in made:
        want = (p.name,) if p.family == "domain" else ("term-" + p.name.split("-", 1)[1],)
        assert p.shapes == want, p.name
    assert not any("many-" + H.slug(t.key) in [p.name for p in made] for t in V.TERMS if t.many or t.spelling == "slot")


def test_a_term_that_is_a_list_has_two_values_in_the_graph_of_every_term_and_one_that_is_not_has_one():
    md = X.honest_metadata()
    for t in V.TERMS:
        values = [e[t.key] for e in md["@graph"] if t.key in e]
        assert values, t.key
        if t.many and X.valid_values(t) and t.key != "mentions":          # the root mentions the actions there are
            assert any(isinstance(v, list) and len(v) == 2 for v in values), t.key
        if not t.many:
            assert not any(isinstance(v, list) for v in values), t.key


def test_each_plant_is_judged_by_the_checker_as_it_declares(work):
    cases, _ = session_corpus()
    plants = {p.name: p for p in X.every_plant()}
    assert len(cases) == len(plants)
    for c in cases:
        assert c.checker == plants[c.name].checker, (c.name, c.checker)


def test_a_plant_with_files_is_built_in_a_copy_and_the_reused_crate_is_left_as_it_was(work):
    before = {p: p.read_bytes() for p in work.crate.rglob("*") if p.is_file()}
    shot = next(p for p in X.PLANTS if p.name == "shot-moved")
    assert work.judge(shot).checker == "raw-digest"
    assert {p: p.read_bytes() for p in work.crate.rglob("*") if p.is_file()} == before


def test_a_plants_graph_is_made_in_order_again_so_the_fault_is_the_edit_and_nothing_else(work):
    early = X.Plant("zz", "an entity that sorts before the others", X.add({"@id": "#", "@type": "CreativeWork"}), "graph-form")
    md = work.of_plant(early)
    ids = [e["@id"] for e in md["@graph"]]
    assert ids[:2] == [V.DESC, V.ROOT] and ids[2:] == sorted(ids[2:])
    late = X.Plant("zz", "an entity that sorts after the others", X.add({"@id": "zzz", "@type": "CreativeWork", "name": "x"}),
                   X.GENERATED)
    assert work.judge(late).checker == X.GENERATED


def test_the_workspace_restores_the_metadata_after_a_plant(work):
    pristine = (work.crate / canonical.DESCRIPTOR).read_bytes()
    for p in X.PLANTS[:6]:
        work.judge(p)
        assert (work.crate / canonical.DESCRIPTOR).read_bytes() == pristine


# -- gate 4: the positive examples ---------------------------------------------------------------------------------------------------
def test_the_fixture_is_accepted_with_fixtures_and_refused_step_unbuilt_without(tmp_path, monkeypatch):
    crate = fixture.make(tmp_path / "crate")
    assert X.checker_verdict(crate) == "accepted"
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    monkeypatch.setattr(checker, "GENERATORS", {})
    assert X.checker_verdict(crate) == "step-unbuilt"


def test_the_fixture_conforms_to_every_shape_of_every_level(work):
    assert positive_problems(work.shapes, work.pristine) == []


def test_the_graph_of_every_term_is_read_by_the_strict_reader_and_conforms_to_every_shape_of_every_level():
    md = X.honest_metadata()
    canonical.write(md)                                              # the strict reader, which refuses what it does not read
    used = {k for e in md["@graph"] for k in e}
    assert {t.key for t in V.TERMS} <= used
    assert positive_problems(H.build(), md) == []


def test_the_graph_of_every_term_puts_each_term_on_each_kind_of_entity_its_domain_admits():
    md = X.honest_metadata()
    for t in V.TERMS:
        for token in t.domain:
            if token in (V.DESC,) or t.key == "conformsTo":
                continue
            host = X.host_for(token, copy.deepcopy(md["@graph"]), "#nowhere")
            hosts = [e for e in md["@graph"] if t.key in e]
            assert hosts, t.key
            if token not in ("*", V.ROOT, V.LOCAL, "Profile", "qro:RawResult"):
                assert any(token in canonical.types(e) for e in hosts), (t.key, token)
            assert token in ("*", V.ROOT, V.LOCAL, "Profile", "qro:RawResult") or token in canonical.types(host), (t.key, token)


def test_the_graph_of_every_term_is_checked_by_the_checker_no_further_than_the_strict_reader():
    """What the checker says of it past step 1 is the parcels' steps' to say, and changes as they are built."""
    md = X.honest_metadata()
    assert any(V.TERM[k].step and V.TERM[k].step > 3 for e in md["@graph"] for k in e if k in V.TERM)


# -- gate 1: soundness, over every plant ---------------------------------------------------------------------------------------------------
def test_no_must_shape_is_stricter_than_the_checker_on_any_plant_and_each_declared_shape_fails():
    cases, shapes = session_corpus()
    assert soundness_problems(shapes, cases) == []


def test_the_refusal_of_each_plant_is_one_a_failing_shape_mirrors_itself_and_not_only_one_of_form():
    cases, shapes = session_corpus()
    own = {X.local(s.id): s.claims for s in H.build(widen=False)}
    assert own_name_problems(shapes, cases, own) == []
    assert own["term-name"] == ("spelling",) and "term-unknown" not in own["term-name"] and own["file-reached"][-1] == "graph-form"
    assert own["term-haspart"] == own["term-about"] == ("spelling",)         # a term of spelling `ref` too: FORM adds graph-form


def test_a_plant_the_checker_accepts_but_for_step_9_has_every_must_shape_conforming():
    cases, shapes = session_corpus()
    edges = [c for c in cases if c.checker == X.GENERATED]
    assert len(edges) >= 14 and {c.family for c in edges} == {"edges"}
    for c in edges:
        assert c.early == "ok", c.name
        assert not c.unreadable, (c.name, "a crate the checker accepts is a crate the expansion reads")
        assert not c.declared and soundness_problems(shapes, [c]) == [], c.name


def test_a_plant_the_shapes_cannot_see_is_refused_by_the_checker_and_no_must_shape_fails():
    cases, shapes = session_corpus()
    limits = [c for c in cases if c.family == "limits"]
    assert len(limits) == 11
    for c in limits:
        assert c.checker != X.GENERATED and c.early != "ok", c.name
        assert soundness_problems(shapes, [c]) == [], c.name


def test_the_ids_the_expansion_does_not_resolve_are_ones_the_reader_refuses_and_so_the_checker_refuses_the_crate():
    """After P0.5 (FORMAT.md item 22) the reader refuses every id the expansion knows rdflib reads otherwise: the evaluator
    abstains from these crates and the checker has refused them, at step 1, as `spelling`."""
    cases, _ = session_corpus()
    abstains = [c for c in cases if c.family == "abstains"]
    assert len(abstains) == 6
    for c in abstains:
        assert c.unreadable and c.checker == c.early and c.triples == (), c.name
        assert c.checker == ("graph-form" if c.name.endswith("reference") else "spelling"), c.name      # an id, and a reference to one
    assert [c.name for c in cases if c.unreadable] == [c.name for c in abstains]          # and no other plant is unreadable


def test_a_case_the_expansion_refuses_to_read_is_never_skipped_and_the_checker_must_have_refused_it():
    """After P0.5 (the lead's ruling of 2026-10-16T14:58:58Z): the evaluator abstains from such a crate, so the gate asks
    steps 1 to 3. Here two cases that differ in that alone."""
    cases, shapes = session_corpus()
    abstained = next(c for c in cases if c.family == "abstains")
    accepted = Case(abstained.name, abstained.checker, "ok", abstained.triples, abstained.declared, abstained.unreadable,
                    abstained.family)
    assert soundness_problems(shapes, [abstained]) == []
    found = soundness_problems(shapes, [accepted])
    assert len(found) == 1 and "the expansion refuses it" in found[0] and "steps 1 to 3 accept it" in found[0], found


def test_the_fuzz_finds_a_crate_the_expansion_refuses_and_steps_1_to_3_accept(work, monkeypatch):
    """The valid insertions are all accepted; an expansion that refused each of them is a gap the fuzz names, and counts."""
    monkeypatch.setattr(p4_expand, "expand", lambda md: (_ for _ in ()).throw(p4_expand.ExpandError("refused by the test")))
    problems, accepted, refused = fuzz_problems(work, work.shapes, range(30), make=valid_mutated)
    assert accepted >= 20 and refused >= accepted and len(problems) == accepted, (accepted, refused, len(problems))
    assert all("the expansion refuses it" in p for p in problems)


def test_the_walk_over_accepted_plants_finds_a_crate_the_expansion_refuses(monkeypatch):
    from controls.registry import Control
    rows = (Control("zz-accepted", "an honest crate", "accepted", None, "P9", "accepted"),)
    monkeypatch.setattr(p4_expand, "expand", lambda md: (_ for _ in ()).throw(p4_expand.ExpandError("refused by the test")))
    problems, examined = accepted_control_problems(
        H.build(), controls=rows, plants={"zz-accepted": lambda d: fixture.make(Path(d) / "honest")})
    assert examined == 1 and len(problems) == 1 and "the expansion refuses it" in problems[0], problems


def test_a_fault_with_a_declared_refusal_is_one_the_checker_raises_before_step_4():
    cases, _ = session_corpus()
    for c in cases:
        if c.family not in ("limits", "edges", "abstains"):
            assert c.checker in V.REFUSAL and V.REFUSAL[c.checker].where.split(";")[0] in ("step 1", "step 2", "step 3"), c.name


# -- gate 3: coverage -----------------------------------------------------------------------------------------------------------------------
def test_every_must_shape_is_made_to_fail_by_some_plant():
    cases, shapes = session_corpus()
    assert uncovered(shapes, cases) == []
    assert sum(s.level == "must" for s in shapes) >= 120


def test_coverage_names_a_must_shape_no_plant_makes_fail():
    cases, shapes = session_corpus()
    never = H.Shape(id=H.shape_iri("never-fails"), targets=(("class", "urn:no-such-class"),), node_kind="IRI",
                    claims=("graph-form",))
    assert uncovered(tuple(shapes) + (never,), cases) == ["never-fails"]


# -- the presence table, held both ways against the checker ------------------------------------------------------------------------------------
def required(entity, key):
    """What the shapes' tables say: a root carries the table's list; a File carries PRESENCE's; a raw result its form."""
    if entity == X.ROOT:
        return key in V.ROOT_REQUIRED
    names = list(H.PRESENCE["File"]) + (list(H.PRESENCE["qro:RawResult"]) if entity == X.RAW else [])
    return key in names


def test_a_term_the_presence_table_requires_is_refused_when_removed_and_one_it_does_not_is_accepted(work):
    seen = {True: 0, False: 0}
    for e in work.pristine["@graph"]:
        if e["@id"] not in (X.ROOT, X.NOTES, X.RAW):
            continue
        for key in [k for k in e if k not in ("@id", "@type")]:
            j = work.judge(X.Plant("removed", "f", X.drop(e["@id"], key), "x"))
            if required(e["@id"], key):
                seen[True] += 1
                assert j.checker not in ("accepted", X.GENERATED) and j.must, (e["@id"], key, j)
            else:
                seen[False] += 1
                assert j.checker == X.GENERATED and not j.must, (e["@id"], key, j)
    assert seen[True] >= 13 and seen[False] == 3          # encodingFormat of the two files, and the raw result's shots


def test_an_entity_that_leaves_off_a_term_with_absence_words_is_a_warning_and_the_checker_accepts_it(work):
    """Rule 2: absence is a word. The shape that asks for it is a Warning, because steps 1 to 3 (which the shapes mirror)
    accept an entity without the term, and no must shape fails; given a valid value, the shape conforms."""
    ids = {X.local(s.id) for s in H.absence_shapes()}
    seen = set()
    for t in V.TERMS:
        for tok in t.domain:
            sid = "absence-" + H.slug(t.key) + "-" + H.slug(tok)
            if sid not in ids:
                continue
            warned = {}
            for given in (False, True):
                md = work.fresh()
                host = X.host_for(tok, md["@graph"], "#abs-host")
                if given:
                    host[t.key] = X.valid_value(t)
                md = X.arranged(md)
                with work.staged(md) as crate:
                    early = early_verdict(crate, canonical.dumps(md))
                must, should, why = X.shapes_verdict(md, work.shapes)
                assert early == "ok" and must == () and why == "", (sid, given, early, must, why)
                warned[given] = should
            assert sid in warned[False] and sid not in warned[True], (sid, warned)
            seen.add(sid)
    assert seen == ids and len(ids) >= 8


def test_the_presence_table_names_only_terms_the_table_has_on_a_type_that_admits_them():
    for kind, keys in H.PRESENCE.items():
        assert kind in V.TYPE
        for k in keys:
            assert kind in V.TERM[k].domain or V.LOCAL in V.TERM[k].domain and kind == "File", (kind, k)


# -- a fuzz of mutations, the unknown unknowns ------------------------------------------------------------------------------------------------------
def test_no_must_shape_fails_on_a_valid_crate_made_by_inserting_valid_things(work):
    problems, accepted, refused = fuzz_problems(work, work.shapes, range(120), make=valid_mutated)
    assert problems == [] and accepted >= 100 and refused == 0, (accepted, refused, problems[:3])


def test_no_must_shape_fails_on_a_mutated_crate_that_steps_1_to_3_accept(work):
    problems, accepted, refused = fuzz_problems(work, work.shapes, range(120), make=mutated)
    assert problems == [] and accepted >= 10 and refused >= 8, (accepted, refused, problems[:3])


def test_the_fuzz_is_the_same_on_every_host_for_a_seed():
    a = mutated({"@context": V.context(), "@graph": [{"@id": V.DESC, "@type": "CreativeWork"}, {"@id": V.ROOT,
                                                                                                 "@type": "Dataset"}]}, 7)
    b = mutated({"@context": V.context(), "@graph": [{"@id": V.DESC, "@type": "CreativeWork"}, {"@id": V.ROOT,
                                                                                                 "@type": "Dataset"}]}, 7)
    assert a == b


def test_the_gate_finds_the_hasPart_range_of_the_designs_first_draft_restored(work):
    """A root whose hasPart names an action is accepted by the checker and refused by that shape (MEASURED, probe_haspart):
    the plant `edge-hasPart-an-action` finds it, as the gate does."""
    real = H.root_shape()
    drafted = H.Shape(**{**real.__dict__, "props": real.props + (H.Shape(path="http://schema.org/hasPart", or_=(
        H.Shape(classes=("http://schema.org/MediaObject",)), H.Shape(classes=("http://schema.org/Dataset",)))),)})
    shapes = [drafted if x.id == real.id else x for x in work.shapes]
    cases, _ = session_corpus()
    found = soundness_problems(shapes, [c for c in cases if c.family in ("edges", "root")])
    assert found and all("edge-" in f for f in found) and any("edge-hasPart-an-action" in f for f in found), found


def test_the_fuzz_finds_a_shape_made_stricter_than_the_checker(work):
    """A shape that refuses every Job: the fuzz of valid insertions, which adds entities of every type, finds it."""
    never = H.Shape(id=H.shape_iri("no-job"), targets=(("class", V.NAMESPACE + "Job"),), node_kind="IRI",
                    classes=("urn:no-such-class",), claims=("graph-form",))
    problems, accepted, _ = fuzz_problems(work, list(work.shapes) + [never], range(120), make=valid_mutated)
    assert problems and accepted > 50 and "no-job" in problems[0]


# -- the other parcels' plants -------------------------------------------------------------------------------------------------------------------
def test_every_accepted_crate_plant_of_any_parcel_conforms_to_every_must_shape():
    from controls import registry
    problems, examined = accepted_control_problems(H.build())
    assert problems == [], problems
    built, crates = registry.plants(), 0
    for c in registry.CONTROLS:                       # counted here, apart from the walk: the accepted rows that are crates
        if c.expected == "accepted" and c.name in built:
            with tempfile.TemporaryDirectory() as d:
                crates += not isinstance(built[c.name](d), tuple)
    assert examined == crates                         # none is built yet but a custody log, so none is examined: the walk below is held on rows made here


def test_the_walk_over_accepted_plants_reads_what_the_registry_says_and_finds_a_stricter_shape(tmp_path):
    from controls.registry import Control
    rows = (Control("zz-accepted", "an honest crate with other contents", "accepted", None, "P9", "accepted"),
            Control("zz-refused", "a refused plant", "refused", "spelling", "P9", "spelling"),
            Control("zz-log", "a custody log", "accepted", None, "P9", "accepted"))

    def honest(d):
        return fixture.make(Path(d) / "honest", counts={"00": 1, "11": 6}, notes="other notes\n")

    def log(d):
        return (b"", None)
    made = {"zz-accepted": honest, "zz-refused": honest, "zz-log": log}
    problems, examined = accepted_control_problems(H.build(), controls=rows, plants=made)
    assert problems == [] and examined == 1
    stricter = [H.Shape(id=H.shape_iri("too-strict"), targets=(("class", "http://schema.org/Dataset"),), node_kind="IRI",
                        classes=("urn:no-such-class",), claims=("graph-form",))]
    problems, examined = accepted_control_problems(H.build() + stricter, controls=rows, plants=made)
    assert examined == 1 and len(problems) == 1 and "too-strict" in problems[0]


def test_the_walk_names_a_plant_whose_row_says_accepted_and_the_checker_refuses(tmp_path):
    from controls.registry import Control
    rows = (Control("zz-wrong", "a plant that is refused", "accepted", None, "P9", "accepted"),)

    def moved(d):
        c = fixture.make(Path(d) / "moved")
        (c / "data" / "notes.txt").write_bytes(b"changed\n")
        return c
    problems, examined = accepted_control_problems(H.build(), controls=rows, plants={"zz-wrong": moved})
    assert examined == 1 and len(problems) == 1 and "file-digest" in problems[0]


def test_the_expansion_is_the_one_the_plants_are_judged_by(work):
    assert p4_expand.expand(work.pristine) and len(p4_expand.expand(work.pristine)) == 36
