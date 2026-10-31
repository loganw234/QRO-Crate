"""Steps 6 and 7 on whole crates (P2's design, items 6 and 7): the honest small and real crates accepted, at step level,
through the whole checker in process with a pass-through generator, and as a process up to step 9, and so are a crate
whose compile carries some of its gate lists, a crate with a sheet's compile and an Atlas-shaped crate; every refusal
of both steps, one plant each, by its name and its place; values that move with the raw bytes and not with a record;
the claim's three words; an orphan gate list, which no step of P2's reads (a stated limit); crates that a memo key
short of one component would pass; a coherence PUB on an Atlas raw result, refused; and the net: a bug in a step is a
refusal by the step's name, an OSError or a MemoryError the checker failing, a PermissionError misuse. Where a plant or
a test answers a verifier's report (P2.1, rounds 1 and 2), its comment or its docstring names the mutant it kills."""
import copy
import json
import os
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest
from p2_builder import (GENERATOR, SMALL_LAW_COUNTS, Model, atlas_model, compile_entity, edit, manifest, qasm, read_md,
                        real_model, refusal, rewrite, raw_ibm, rows_of, sha, sheet_model, small_gates, small_law_bytes,
                        small_model, transpile)

from qro import canonical, checker, p2_hold, p2_measures, p2_sim
from qro.__main__ import main
from qro.refusal import Refused

ROOT = Path(__file__).resolve().parents[2]
SMALL_HOLD, SMALL_COMPILE = "#hold-synth-morning", "#compile-synth-morning"
SHEET_HOLD, SHEET_COMPILE = "#hold-synth-sheet-01", "#compile-synth-sheet-01"


@pytest.fixture(scope="module")
def honest(tmp_path_factory):
    base = tmp_path_factory.mktemp("p2-honest")
    small_model().write(base / "small")
    real_model().write(base / "real")
    m = small_model(gate_lists=False)
    m.write(base / "withheld")
    m = small_model(gate_lists=False)
    logical = {n: m.files[f"bundle/{n}.qasm"] for n in ("law", "coherence-xx", "coherence-yy")}
    logical["known-answer"] = m.files["bundle/known-answer.qasm"]
    m.files["bundle/manifest.json"] = manifest([
        ("known-answer", "known-answer", "known-answer", "Z" * 16, logical["known-answer"], None),
        ("law", "law", "law", "ZZZZ", logical["law"], None),
        ("coherence", "coherence-xx", "coherence", "XXZZ", logical["coherence-xx"], None),
        ("coherence", "coherence-yy", "coherence", "YYZZ", logical["coherence-yy"], None)])
    m.write(base / "unexposed")
    small_model(uncarried=("coherence-xx",)).write(base / "mixed")
    sheet_model().write(base / "sheet")
    atlas_model().write(base / "atlas")
    return base


def crate(honest, tmp_path, kind="small"):
    dest = tmp_path / kind
    shutil.copytree(honest / kind, dest)
    return dest


def same(r, name, where, detail):
    assert r is not None, "accepted"
    assert (r.name, r.where) == (name, where), (r.name, r.where, r.detail)
    assert detail in r.detail, r.detail


FORMATS = {"json": "application/json", "qasm": "text/plain", "qasm3": "text/plain"}


def add_file(c, rel, b, *into):
    """A file added to a written crate: its bytes, its File entity with its digest and size, the root's hasPart, and
    each (entity, term) of `into`, a list of references, which then lists it too."""
    target = Path(c).joinpath(*rel.split("/"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b)

    def fn(ents):
        ents[rel] = {"@id": rel, "@type": "File", "sha256": sha(b), "contentSize": str(len(b)),
                     "encodingFormat": FORMATS.get(rel.rsplit(".", 1)[-1], "application/octet-stream")}
        for i, term in (("./", "hasPart"),) + into:
            ents[i][term] = sorted(ents[i][term] + [{"@id": rel}], key=lambda r: r["@id"])
    return edit(c, fn)


# -- the honest crates -------------------------------------------------------------------------------------------------
HONEST_HOLDS = {"small": {SMALL_HOLD: "holds"}, "real": {"#hold-ibm_kingston-morning": "holds"},
                "withheld": {SMALL_HOLD: "withheld"}, "unexposed": {SMALL_HOLD: "unexposed"},
                "mixed": {SMALL_HOLD: "withheld"}, "sheet": {SMALL_HOLD: "holds", SHEET_HOLD: "holds"}, "atlas": {}}


@pytest.mark.parametrize("kind", sorted(HONEST_HOLDS))
def test_the_honest_crates_pass_steps_6_and_7(honest, kind):
    """Each honest crate, its Holds' words the gate lists' own: `mixed` carries three of the four gate lists its
    manifest names (the coherence-xx list is withheld), `sheet` holds a second compile whose law and coherence
    circuits and gate lists lie outside its own object and result (the seam with P1.2's sheets; H60 survived without
    it), and `atlas` is Atlas-shaped, its law Pub decoded by Atlas's rule, with no compile."""
    c = honest / kind
    assert refusal(6, c) is None and refusal(7, c) is None
    holds = {e["@id"]: e["qro:exactHold"] for e in read_md(c)["@graph"] if "qro:Hold" in canonical.types(e)}
    assert holds == HONEST_HOLDS[kind]


def test_the_mixed_crate_carries_three_of_the_four_gate_lists_its_manifest_names(honest):
    """The shape `mixed` is said to have: the coherence-xx gate list named and not carried, the other three carried."""
    md = read_md(honest / "mixed")
    files = {e["sha256"] for e in md["@graph"] if isinstance(e.get("sha256"), str)}
    named = p2_hold.read_manifest((honest / "mixed" / "bundle" / "manifest.json").read_bytes())
    assert {n.name for n in named if n.gates_sha256 not in files} == {"coherence-xx"}
    assert not (honest / "mixed" / "bundle" / "coherence-xx.gates.json").exists()


def test_the_sheets_circuits_and_gate_lists_lie_outside_its_own_object_and_result(honest):
    """The shape `sheet` is said to have, as P1's twin slices a sheet (P1.md, 2026-10-26T10:55:57Z): its compile lists
    its manifest and its known-answer circuit's two files, nothing else; its manifest names four circuits; and the law
    and coherence circuits' logical files and gate lists are found, by digest, only among the morning bundle's."""
    md = read_md(honest / "sheet")
    ents = {e["@id"]: e for e in md["@graph"]}
    sheet = ents[SHEET_COMPILE]
    own = {r["@id"] for r in sheet["object"] + sheet["result"]}
    assert own == {"sheet-01/manifest.json", "sheet-01/known-answer.qasm", "sheet-01/known-answer.gates.json"}
    by_digest = {}
    for e in md["@graph"]:
        if isinstance(e.get("sha256"), str):
            by_digest.setdefault(e["sha256"], set()).add(e["@id"])
    named = p2_hold.read_manifest((honest / "sheet" / "sheet-01" / "manifest.json").read_bytes())
    assert [n.name for n in named] == ["known-answer", "law", "coherence-xx", "coherence-yy"]
    for n in named[1:]:
        assert by_digest[n.circuit_sha256] == {f"bundle/{n.name}.qasm"}, n.name
        assert by_digest[n.gates_sha256] == {f"bundle/{n.name}.gates.json"}, n.name


@pytest.fixture
def loaded(monkeypatch):
    """The checker's registries, loaded with every parcel present, restored after the test."""
    for name in ("STEPS", "RAW_FORMS", "GENERATORS"):
        monkeypatch.setattr(checker, name, dict(getattr(checker, name)))
    monkeypatch.setattr(checker, "COUNTS", list(checker.COUNTS))
    checker.load()
    assert checker.STEPS[6].__module__ == checker.STEPS[7].__module__ == "qro.register_p2"
    return checker


def pass_through(crate_dir):
    return json.loads((Path(crate_dir) / canonical.DESCRIPTOR).read_bytes())


@pytest.mark.parametrize("kind", ["small", "real"])
def test_the_whole_checker_accepts_the_honest_crates_with_a_pass_through_generator(honest, loaded, kind):
    loaded.GENERATORS[GENERATOR] = pass_through
    md = loaded.check(honest / kind)
    assert {e["@id"] for e in md["@graph"]} >= {"#measuring", "#question", "#contrast-x0x1-uniform"}


def test_the_whole_checker_refuses_a_planted_crate_by_the_steps_name(honest, loaded, tmp_path):
    loaded.GENERATORS[GENERATOR] = pass_through
    c = edit(crate(honest, tmp_path), lambda ents: ents["#contrast-x0x1-uniform"].update({"qro:class": "integrity"}))
    with pytest.raises(Refused) as r:
        loaded.check(c)
    assert (r.value.name, r.value.where) == ("measure-class", "#contrast-x0x1-uniform qro:class")


# -- step 6's refusals, one plant each ---------------------------------------------------------------------------------
def ents_edit(fn):
    return lambda c: edit(c, fn)


def drop(i, *, result_of=None, mention=False):
    def fn(ents):
        del ents[i]
        if result_of:
            ents[result_of]["result"] = [r for r in ents[result_of]["result"] if r["@id"] != i]
        if mention:
            ents["./"]["mentions"] = [r for r in ents["./"]["mentions"] if r["@id"] != i]
    return fn


def twin_of(i, new, *, mention=False, **changes):
    def fn(ents):
        ents[new] = {**copy.deepcopy(ents[i]), "@id": new, **changes}
        if mention:
            ents["./"]["mentions"] = sorted(ents["./"]["mentions"] + [{"@id": new}], key=lambda r: r["@id"])
    return fn


def set_term(i, **terms):
    terms = {k.replace("__", ":"): v for k, v in terms.items()}
    return lambda ents: ents[i].update(terms)


def del_term(i, term):
    return lambda ents: ents[i].pop(term)


def moved_one_shot(c):
    counts = dict(SMALL_LAW_COUNTS)
    counts[(0, 2)] -= 1
    counts[(0, 1)] += 1
    return rewrite(c, "run/joblaw-raw.json", raw_ibm([rows_of(counts)]))


def off_the_tile(c):
    counts = dict(SMALL_LAW_COUNTS)
    counts[(0, 2)] -= 1
    counts[(0, 5)] = 1
    return rewrite(c, "run/joblaw-raw.json", raw_ibm([rows_of(counts)]))


STEP6 = {
    "two questions": (ents_edit(lambda e: e.update({"#question-2": {
        "@id": "#question-2", "@type": ["CreativeWork", "qro:Question"], "name": "another"}})),
        "measure-class", "@graph", "carries exactly one qro:Question; this one carries 2"),
    "no twins": (ents_edit(del_term("#question", "qro:twins")), "measure-class", "#question qro:twins",
                 "the question carries the law, its circuit, the twins and the measure set"),
    "another measure set": (ents_edit(set_term("#question", qro__measureSet="qro-measures/2")), "step-unbuilt",
                            "#question qro:measureSet", "no measure set qro-measures/2 is built"),
    "one twin": (ents_edit(set_term("#question", qro__twins=["uniform"])), "measure-class", "#question qro:twins",
                 "the twins of qro-measures/1 are dephased, uniform"),
    "the law a rule": (ents_edit(set_term("#question", qro__law={"@id": "#rule-ibm"})), "measure-class",
                       "#question qro:law", "the law names no File the crate holds"),
    "the law's bytes out of form": (lambda c: rewrite(c, "question/law.json", small_law_bytes().rstrip(b"\n")),
                                    "measure-class", "#question qro:law", "the law file"),
    "a law the measure set cannot use": (lambda c: rewrite(c, "question/law.json", small_law_bytes((0, 5, 5, 0, 0, 0))),
                                         "measure-class", "#question qro:law", "the law never occupies the sites [1]"),
    "a law whose observables are not the set's": (
        lambda c: rewrite(c, "question/law.json", small_law_bytes(observables={"X0X1": Fraction(4, 5)})),
        "measure-class", "#question qro:law", "measures against a law whose observables are exactly X0X1, Y0Y1"),
    "a law with no xeb norm": (lambda c: rewrite(c, "question/law.json", small_law_bytes((1,) * 6, den=6)),
                               "measure-class", "#question qro:law", "linear XEB has no norm under this law"),
    "the law circuit outside the question's object": (
        ents_edit(set_term("#question", qro__lawCircuit={"@id": "bundle/coherence-xx.qasm"})), "measure-class",
        "#question qro:lawCircuit", "the law circuit is one of the question's own circuits, in its object"),
    "the law circuit a rule": (ents_edit(set_term("#question", qro__lawCircuit={"@id": "#rule-ibm"})),
                               "measure-class", "#question qro:lawCircuit", "the law circuit names no File"),
    "the law circuit of another width": (
        ents_edit(set_term("#question", qro__lawCircuit={"@id": "bundle/known-answer.qasm"})), "measure-class",
        "#question qro:lawCircuit",
        "the law is not the question's circuit's: the law circuit has 16 qubits; the law's tile has 4 sites"),
    "the law circuit bent": (lambda c: rewrite(c, "circuits/small-law.qasm", qasm(4, small_gates(t1=0.3))),
                             "measure-class", "#question qro:lawCircuit",
                             "the law is not the question's circuit's: it does not lay the law"),
    "the law circuit out of the subset": (lambda c: rewrite(c, "circuits/small-law.qasm", b"OPENQASM 3.0;\n"),
                                          "measure-class", "#question qro:lawCircuit", "does not open with"),
    "a law with one weight moved": (lambda c: rewrite(c, "question/law.json", small_law_bytes((0, 4, 3, 2, 1, 0))),
                                    "measure-class", "#question qro:lawCircuit",
                                    "the law is not the question's circuit's: it does not lay the law"),
    "a law with one coherence edited": (
        lambda c: rewrite(c, "question/law.json", small_law_bytes(observables={"X0X1": Fraction(1, 2),
                                                                               "Y0Y1": Fraction(4, 5)})),
        "measure-class", "#question qro:lawCircuit",
        "the law is not the question's circuit's: its X0X1 is +0.800000000000, where the law says 1/2"),
    "a class declared": (ents_edit(set_term("#contrast-x0x1-uniform", qro__class="integrity")), "measure-class",
                         "#contrast-x0x1-uniform qro:class",
                         "the crate says integrity; the law and the twin's rule give signal"),
    "a law value edited": (ents_edit(set_term("#contrast-x0x1-uniform", qro__lawValue="3/5")), "measure-class",
                           "#contrast-x0x1-uniform qro:lawValue", "the crate says 3/5; it is 4/5"),
    # kills H6, the twin's value left uncompared
    "a twin value edited": (ents_edit(set_term("#contrast-x0x1-uniform", qro__twinValue="1/7")), "measure-class",
                            "#contrast-x0x1-uniform qro:twinValue", "the crate says 1/7; it is 0/1"),
    "a vector measure with values": (
        ents_edit(set_term("#contrast-pair-occupations-uniform", qro__lawValue="1/2", qro__twinValue="1/2")),
        "measure-class", "#contrast-pair-occupations-uniform qro:lawValue", "is a vector measure"),
    "a contrast missing": (ents_edit(drop("#contrast-tvd-dephased", result_of="#measuring")), "measure-class",
                           "#question qro:measureSet", "no Contrast of tvd against dephased"),
    "a second contrast": (ents_edit(twin_of("#contrast-x0x1-uniform", "#contrast-x0x1-uniform-2")), "measure-class",
                          "#contrast-x0x1-uniform-2", "a second Contrast of x0x1 against uniform"),
    "a contrast without its class": (ents_edit(del_term("#contrast-tvd-uniform", "qro:class")), "measure-class",
                                     "#contrast-tvd-uniform qro:class", "a Contrast states its measure"),
    "a measurement without its value": (ents_edit(del_term("#measurement-joblaw-0-tvd", "qro:value")),
                                        "measure-class", "#measurement-joblaw-0-tvd qro:value",
                                        "a Measurement states its measure, its PUB, its shots in scope and its value"),
    "a value edited": (ents_edit(set_term("#measurement-joblaw-0-linear-xeb", qro__value="1/2")), "measure-class",
                       "#measurement-joblaw-0-linear-xeb qro:value", "the crate says 1/2; the raw bytes give 835/988"),
    "the shots in scope edited": (ents_edit(set_term("#measurement-joblaw-0-tvd", qro__inScope=40)), "measure-class",
                                  "#measurement-joblaw-0-tvd qro:inScope", "the crate says 40; the raw bytes hold 38"),
    "an interval's end edited": (ents_edit(set_term("#measurement-jobcoh-0-x0x1", qro__lower="0/1")),
                                 "measure-class", "#measurement-jobcoh-0-x0x1 qro:lower",
                                 "the crate says 0/1; the certified interval's end is"),
    # kills H8, the upper end left uncompared
    "an interval's upper end edited": (ents_edit(set_term("#measurement-jobcoh-0-x0x1", qro__upper="1/1")),
                                       "measure-class", "#measurement-jobcoh-0-x0x1 qro:upper",
                                       "the crate says 1/1; the certified interval's end is"),
    "an interval on a statistic": (ents_edit(set_term("#measurement-joblaw-0-tvd", qro__lower="0/1",
                                                      qro__upper="1/1")),
                                   "measure-class", "#measurement-joblaw-0-tvd qro:lower", "tvd carries no interval"),
    # the second verifier's note 2: a term of each Measurement no plant edited, y0y1's, n-crystal-share's and
    # nn-pair-correlation's (each kills its P mutant, step 6 comparing nothing of that measure's Measurements)
    "the y0y1 value edited": (ents_edit(set_term("#measurement-jobcoh-1-y0y1", qro__value="1/2")), "measure-class",
                              "#measurement-jobcoh-1-y0y1 qro:value", "the crate says 1/2; the raw bytes give 3/4"),
    "the n-crystal-share's shots in scope edited": (
        ents_edit(set_term("#measurement-joblaw-0-n-crystal-share", qro__inScope=39)), "measure-class",
        "#measurement-joblaw-0-n-crystal-share qro:inScope", "the crate says 39; the raw bytes hold 40"),
    "the nn-pair-correlation value edited": (
        ents_edit(set_term("#measurement-joblaw-0-nn-pair-correlation", qro__value="1/2")), "measure-class",
        "#measurement-joblaw-0-nn-pair-correlation qro:value", "the crate says 1/2; the raw bytes give 6127/11424"),
    "a measurement missing": (ents_edit(drop("#measurement-joblaw-0-tvd", result_of="#measuring")), "measure-class",
                              "#pub-joblaw-0", "the PUB's tvd has no Measurement"),
    "a measure its PUB has not": (ents_edit(twin_of("#measurement-joblaw-0-tvd", "#measurement-joblaw-0-x0x1",
                                                    **{"qro:measure": "x0x1"})),
                                  "measure-class", "#measurement-joblaw-0-x0x1 qro:measure",
                                  "#pub-joblaw-0, a PUB of role law, has no measure x0x1"),
    "a second measurement": (ents_edit(twin_of("#measurement-joblaw-0-tvd", "#measurement-joblaw-0-tvd-2")),
                             "measure-class", "#measurement-joblaw-0-tvd-2", "a second Measurement of tvd"),
    "a measurement on the known-answer pub": (
        ents_edit(twin_of("#measurement-joblaw-0-tvd", "#measurement-jobka-0-tvd",
                          **{"qro:measuredPub": {"@id": "#pub-jobka-0"}})),
        "measure-class", "#measurement-jobka-0-tvd qro:measure",
        "#pub-jobka-0, a PUB of role known-answer, has no measure tvd"),
    "a measurement of no pub": (ents_edit(set_term("#measurement-joblaw-0-tvd",
                                                   qro__measuredPub={"@id": "#job-joblaw"})),
                                "measure-class", "#measurement-joblaw-0-tvd qro:measuredPub",
                                "#job-joblaw is no Pub of the crate"),
    "one shot moved in the raw bytes": (moved_one_shot, "measure-class",
                                        "#measurement-joblaw-0-forbidden-share qro:value",
                                        "the crate says 3/38; the raw bytes give 2/19"),
    "a law pub read in another basis": (ents_edit(set_term("#pub-joblaw-0", qro__basis="XZZZ")), "measure-class",
                                        "#pub-joblaw-0", "a law PUB is read in Z on all 4 qubits"),
    "an outcome off the tile": (off_the_tile, "measure-class", "#pub-joblaw-0",
                                "the outcome (0, 5) is not a set of the law's 4 sites"),
    "no measuring": (ents_edit(drop("#measuring", mention=True)), "measure-class", "@graph",
                     "exactly one qro:Measuring; this one carries 0"),
    # kills H41, a second Measuring allowed
    "a second measuring": (ents_edit(twin_of("#measuring", "#measuring-2", mention=True)), "measure-class", "@graph",
                           "exactly one qro:Measuring; this one carries 2"),
    "alpha edited": (ents_edit(set_term("#measuring", qro__alpha="1/10")), "measure-class", "#measuring qro:alpha",
                     "the crate's intervals are at alpha 1/20"),
    "the family edited": (ents_edit(set_term("#measuring", qro__family=6)), "measure-class", "#measuring qro:family",
                          "the crate says 6; it carries 5 certified intervals"),
}


@pytest.mark.parametrize("plant", sorted(STEP6))
def test_each_refusal_of_step_6(honest, tmp_path, plant):
    make, name, where, detail = STEP6[plant]
    c = make(crate(honest, tmp_path))
    same(refusal(6, c), name, where, detail)


def test_a_record_changed_moves_no_measure(honest, tmp_path):
    """The measures come from the raw bytes alone (P2's design, found 2): Quantum-Film's device-run record of the law
    PUB rewritten, its digest with it, and step 6 accepts the crate unchanged."""
    c = crate(honest, tmp_path)
    rec = json.loads((c / "run" / "joblaw-pub0-law.json").read_bytes())
    rec["counts"] = [[[0, 1], 40]]
    rewrite(c, "run/joblaw-pub0-law.json", json.dumps(rec).encode("ascii") + b"\n")
    assert refusal(6, c) is None


@pytest.mark.parametrize("step, name", [(6, "measure-class"), (7, "compile-uncontrolled")])
def test_a_graph_the_index_cannot_read_is_refused_at_graph_with_its_reason(honest, step, name):
    md = read_md(honest / "small")
    md["@graph"].append(dict(next(e for e in md["@graph"] if e["@id"] == "#question")))
    same(refusal(step, honest / "small", md), name, "@graph", "#question: an @id twice in the graph")


def test_a_crate_with_no_question_is_refused_at_step_level(honest):
    md = read_md(honest / "small")
    for e in md["@graph"]:
        if e["@id"] == "#question":
            e["@type"] = "CreativeWork"
    same(refusal(6, honest / "small", md), "measure-class", "@graph", "this one carries 0")


def test_a_contrast_of_no_measure_of_the_set_is_refused_at_step_level(honest):
    md = read_md(honest / "small")
    next(e for e in md["@graph"] if e["@id"] == "#contrast-tvd-uniform")["qro:twin"] = "law"
    same(refusal(6, honest / "small", md), "measure-class", "#contrast-tvd-uniform qro:measure",
         "tvd against law is no contrast of qro-measures/1")


# -- step 7's refusals, one plant each ---------------------------------------------------------------------------------
def small_files(c, rel):
    return (Path(c) / rel).read_bytes()


def with_manifest(edit_doc, rel="bundle/manifest.json"):
    """The crate's manifest at `rel` rewritten by edit_doc(its parsed JSON), its digest with it."""
    def make(c):
        doc = json.loads(small_files(c, rel))
        edit_doc(doc)
        return rewrite(c, rel, json.dumps(doc, indent=1, sort_keys=True).encode("ascii") + b"\n")
    return make


def circuit_named(doc, name):
    return next(x for j in doc["jobs"] for x in j["circuits"] if x["name"] == name)


def job_of(doc, name):
    """The manifest's job whose first circuit is `name`."""
    return next(j for j in doc["jobs"] if j["circuits"][0]["name"] == name)


def break_gate_list(rel, name, manifest_rel="bundle/manifest.json"):
    """A carried gate list broken: an x on its first measured qubit, before its first barrier or measure, which flips
    that bit of every outcome; the file's digest and its manifest's `gates_sha256` of the circuit `name` made to agree
    (the second verifier's recipe, its break_list)."""
    def make(c):
        doc = json.loads(small_files(c, rel))
        i = next(k for k, g in enumerate(doc["gates"]) if g[0] in ("barrier", "measure"))
        q = next(g[1][0] for g in doc["gates"] if g[0] == "measure")
        doc["gates"].insert(i, ["x", [q], [], []])
        b = json.dumps(doc, indent=1, sort_keys=True).encode("ascii") + b"\n"
        rewrite(c, rel, b)
        return with_manifest(lambda d: circuit_named(d, name).update(gates_sha256=sha(b)), manifest_rel)(c)
    return make


broken_law_gate_list = break_gate_list("bundle/law.gates.json", "law")


def hostile_law_gate_list(c):
    b = b'{"format": "quantum-film/isa-gates/v1", "gates": [["sx", [10], [], []]], "gates": []}\n'
    rewrite(c, "bundle/law.gates.json", b)
    return with_manifest(lambda d: circuit_named(d, "law").update(gates_sha256=sha(b)))(c)


def unnamed_gate_list(term):
    """A gate list its manifest does not name, listed in the small compile's `term`: the law's list with one byte
    more, so another digest."""
    def make(c):
        b = small_files(c, "bundle/law.gates.json").replace(b"\n", b"\n ", 1)
        return add_file(c, "bundle/extra.gates.json", b, (SMALL_COMPILE, term))
    return make


def second_manifest(c):
    """A copy of the compile's manifest at another path, listed in its `object` too: two manifest.json files."""
    return add_file(c, "bundle/copy/manifest.json", small_files(c, "bundle/manifest.json"), (SMALL_COMPILE, "object"))


def flipped_xx(c):
    """The coherence-xx circuit with a Z on qubit 0 (two sdg) before its basis change, which turns the sign of its
    X0X1 parity, and its gate list transpiled again: both files and the manifest's two digests made to agree."""
    logical = qasm(4, small_gates() + ["sdg q[0];", "sdg q[0];"], "XXZZ", True)
    gates = transpile(logical)
    rewrite(c, "bundle/coherence-xx.qasm", logical)
    rewrite(c, "bundle/coherence-xx.gates.json", gates)
    return with_manifest(lambda d: circuit_named(d, "coherence-xx").update(circuit_sha256=sha(logical),
                                                                            gates_sha256=sha(gates)))(c)


STEP7 = {
    "a hold of no compile": (ents_edit(set_term(SMALL_HOLD, qro__heldCompile={"@id": "#question"})),
                             "compile-uncontrolled", f"{SMALL_HOLD} qro:heldCompile", "a Hold names one Compile"),
    "a hold with no rule": (ents_edit(del_term(SMALL_HOLD, "qro:holdRule")), "compile-uncontrolled",
                            f"{SMALL_HOLD} qro:holdRule", "a Hold names the rule it holds by"),
    "another hold rule": (ents_edit(set_term(SMALL_HOLD, qro__holdRule="qro-exact-hold/2")), "step-unbuilt",
                          f"{SMALL_HOLD} qro:holdRule", "no hold rule qro-exact-hold/2 is built"),
    "a hold with no word": (ents_edit(del_term(SMALL_HOLD, "qro:exactHold")), "compile-uncontrolled",
                            f"{SMALL_HOLD} qro:exactHold", "a Hold states what the compile's gate lists give"),
    "a compile without a hold": (ents_edit(drop(SMALL_HOLD, mention=True)), "compile-uncontrolled", SMALL_COMPILE,
                                 "a Compile has exactly one Hold; this one has 0"),
    "a compile with two holds": (ents_edit(twin_of(SMALL_HOLD, SMALL_HOLD + "-2", mention=True)),
                                 "compile-uncontrolled", SMALL_COMPILE, "this one has 2"),
    "no manifest in the compile's object": (
        ents_edit(lambda e: e[SMALL_COMPILE].update(object=[r for r in e[SMALL_COMPILE]["object"]
                                                            if r["@id"] != "bundle/manifest.json"])),
        "compile-uncontrolled", SMALL_COMPILE, "its object holds 0 manifest.json files, not one"),
    # kills H33, a second manifest.json allowed
    "a second manifest in the compile's object": (second_manifest, "compile-uncontrolled", SMALL_COMPILE,
                                                  "its object holds 2 manifest.json files, not one"),
    "a manifest out of form": (lambda c: rewrite(c, "bundle/manifest.json", b"{}\n"), "compile-uncontrolled",
                               SMALL_COMPILE, "the manifest is not quantum-film/hardware-bundle/v1"),
    "a gate list its manifest does not name": (unnamed_gate_list("result"), "compile-uncontrolled",
                                               f"{SMALL_COMPILE} result",
                                               "bundle/extra.gates.json is a gate list its manifest does not name"),
    # the second verifier's note 1: a gate list in the object is held to the manifest as one in the result is
    "a gate list in the compile's object its manifest does not name": (
        unnamed_gate_list("object"), "compile-uncontrolled", f"{SMALL_COMPILE} object",
        "bundle/extra.gates.json is a gate list its manifest does not name"),
    "a logical circuit not carried": (with_manifest(lambda d: circuit_named(d, "coherence-xx").update(
        circuit_sha256="ab" * 32)), "compile-uncontrolled", "bundle/manifest.json",
        "the logical circuit of coherence-xx, " + "ab" * 32 + ", is not carried"),
    "a gate list broken": (broken_law_gate_list, "compile-uncontrolled", "bundle/law.gates.json",
                           "the gate list of law does not pass the exact hold: (a) its distribution differs"),
    "a hostile gate list": (hostile_law_gate_list, "compile-uncontrolled", "bundle/law.gates.json",
                            "the gate list of law cannot be held: the gate list: the key 'gates' twice in one object"),
    "a broken gate list dropped from the result but carried": (
        lambda c: edit(broken_law_gate_list(c), lambda e: e[SMALL_COMPILE].update(
            result=[r for r in e[SMALL_COMPILE]["result"] if r["@id"] != "bundle/law.gates.json"])),
        "compile-uncontrolled", "bundle/law.gates.json", "the gate list of law does not pass the exact hold: (a)"),
    # kills H62, a compile's gate lists held only where its Hold says holds: on the mixed crate, whose Hold says
    # withheld, honestly, the carried law list broken
    "a carried gate list broken under a withheld hold": (
        broken_law_gate_list, "compile-uncontrolled", "bundle/law.gates.json",
        "the gate list of law does not pass the exact hold: (a)", "mixed"),
    # the second verifier's D1, three broken carried lists: the sheet's own, in the second Compile by id (kills U1,
    # only the first Compile held, and S1 and S2 below); the manifest's last entry (kills U4, the last entry not held);
    # and its first, a known-answer list (kills S1, the first entry not held, and S2, no known-answer list held)
    "the sheet's own known-answer gate list broken": (
        break_gate_list("sheet-01/known-answer.gates.json", "known-answer", "sheet-01/manifest.json"),
        "compile-uncontrolled", "sheet-01/known-answer.gates.json",
        "the gate list of known-answer does not pass the exact hold: (a)", "sheet"),
    "the manifest's last gate list broken": (
        break_gate_list("bundle/coherence-yy.gates.json", "coherence-yy"), "compile-uncontrolled",
        "bundle/coherence-yy.gates.json", "the gate list of coherence-yy does not pass the exact hold: (a)"),
    "the manifest's first gate list broken": (
        break_gate_list("bundle/known-answer.gates.json", "known-answer"), "compile-uncontrolled",
        "bundle/known-answer.gates.json", "the gate list of known-answer does not pass the exact hold: (a)"),
    "a role that cannot be judged": (with_manifest(lambda d: circuit_named(d, "coherence-xx").update(basis="XYZZ")),
                                     "compile-uncontrolled", "bundle/coherence-xx.gates.json",
                                     "the gate list of coherence-xx cannot be held: the basis XYZZ does not read"),
    "a coherence the law does not say": (
        lambda c: rewrite(c, "question/law.json", small_law_bytes(observables={"X0X1": Fraction(1, 2),
                                                                               "Y0Y1": Fraction(4, 5)})),
        "compile-uncontrolled", "bundle/coherence-xx.gates.json",
        "the gate list of coherence-xx does not pass the exact hold: (b) its logical circuit, a coherence circuit: "
        "the parity of qubits 0 and 1 is +0.8"),
    # kills H20, the parity's sign ignored
    "a coherence circuit of the wrong sign": (
        flipped_xx, "compile-uncontrolled", "bundle/coherence-xx.gates.json",
        "the gate list of coherence-xx does not pass the exact hold: (b) its logical circuit, a coherence circuit: "
        "the parity of qubits 0 and 1 is -0.8"),
    "holds where the gate lists give holds, said withheld": (
        ents_edit(set_term(SMALL_HOLD, qro__exactHold="withheld")), "compile-uncontrolled",
        f"{SMALL_HOLD} qro:exactHold", "the Hold says withheld; the gate lists give holds"),
}


@pytest.mark.parametrize("plant", sorted(STEP7))
def test_each_refusal_of_step_7(honest, tmp_path, plant):
    make, name, where, detail, *kind = STEP7[plant]          # the crate planted: the small one, unless one is named
    c = make(crate(honest, tmp_path, *kind))
    same(refusal(7, c), name, where, detail)


def test_the_withheld_plant_leaves_its_hold_saying_withheld(honest, tmp_path):
    """The plant on the mixed crate is the one its name says: the Hold still says `withheld`, which the gate lists
    still give, so the only fault is the broken list."""
    c = broken_law_gate_list(crate(honest, tmp_path, "mixed"))
    hold = next(e for e in read_md(c)["@graph"] if e["@id"] == SMALL_HOLD)
    named = p2_hold.read_manifest(small_files(c, "bundle/manifest.json"))
    files = {e["sha256"] for e in read_md(c)["@graph"] if isinstance(e.get("sha256"), str)}
    assert hold["qro:exactHold"] == p2_hold.claim(named, files) == "withheld"


def test_the_stated_limit_an_orphan_gate_list_is_read_by_no_step_of_p2s(honest, tmp_path):
    """P2's stated limit 16 (the first verifier's note): a gate-list File that no Compile lists in its object or
    result and no manifest names is no compile's gate list, and step 7 never reads it, so a broken one is accepted.
    Step 9 alone refuses such a crate, where its generator refuses a file it cannot place. The control: listed in the
    compile's result, the same file is refused."""
    c = crate(honest, tmp_path)
    doc = json.loads(small_files(c, "bundle/law.gates.json"))
    doc["gates"].insert(next(i for i, g in enumerate(doc["gates"]) if g[0] == "barrier"), ["x", [10], [], []])
    b = json.dumps(doc, indent=1, sort_keys=True).encode("ascii") + b"\n"
    assert sha(b) not in {n.gates_sha256 for n in p2_hold.read_manifest(small_files(c, "bundle/manifest.json"))}
    add_file(c, "orphan/law.gates.json", b)
    assert refusal(7, c) is None
    edit(c, lambda e: e[SMALL_COMPILE].update(result=sorted(e[SMALL_COMPILE]["result"] +
                                                            [{"@id": "orphan/law.gates.json"}], key=lambda r: r["@id"])))
    same(refusal(7, c), "compile-uncontrolled", f"{SMALL_COMPILE} result",
         "orphan/law.gates.json is a gate list its manifest does not name")


@pytest.mark.parametrize("kind, word", [("withheld", "withheld"), ("unexposed", "unexposed")])
def test_a_hold_that_claims_more_than_its_gate_lists_give_is_refused(honest, tmp_path, kind, word):
    c = edit(crate(honest, tmp_path, kind), set_term(SMALL_HOLD, qro__exactHold="holds"))
    same(refusal(7, c), "compile-uncontrolled", f"{SMALL_HOLD} qro:exactHold",
         f"the Hold says holds; the gate lists give {word}")


def test_a_file_the_crate_does_not_hold_carries_no_gate_list_whatever_digest_it_states(honest):
    """The claim and the hold count only the crate's own Files: four Files the crate does not hold, stating the four
    digests its manifest names, leave the withheld crate's word `withheld`, and step 7 accepts it as it is."""
    c = honest / "withheld"
    md = read_md(c)
    named = p2_hold.read_manifest((c / "bundle" / "manifest.json").read_bytes())
    assert len(named) == 4 and all(n.gates_sha256 for n in named)
    for i, n in enumerate(named):
        md["@graph"].append({"@id": f"https://example.org/gates-{i}.json", "@type": "File", "sha256": n.gates_sha256})
    assert refusal(7, c, md) is None


def test_law_role_circuits_with_no_question_law_are_refused(honest):
    """The lead's E2 (10): a law-role circuit is held to the question's `qro:law` where the crate carries one, and
    refused where it does not (step 7 alone; through the checker, step 6 refuses the question first)."""
    md = read_md(honest / "small")
    next(e for e in md["@graph"] if e["@id"] == "#question").pop("qro:law")
    same(refusal(7, honest / "small", md), "compile-uncontrolled", "bundle/law.gates.json",
         "the gate list of law cannot be held: a law circuit is held to the question's law, and the crate's question "
         "names none")


def test_two_questions_naming_a_law_are_refused_by_step_7(honest):
    md = read_md(honest / "small")
    q = next(e for e in md["@graph"] if e["@id"] == "#question")
    md["@graph"].append({**q, "@id": "#question-2"})
    same(refusal(7, honest / "small", md), "compile-uncontrolled", "bundle/law.gates.json", "2 questions name a law")


def test_the_real_crates_broken_gate_list_is_refused(honest, tmp_path):
    c = crate(honest, tmp_path, "real")
    doc = json.loads(small_files(c, "bundle/law.gates.json"))
    assert doc["gates"][303] == ["sx", [47], [], []]
    doc["gates"][303] = ["x", [47], [], []]
    b = json.dumps(doc).encode("ascii")
    rewrite(c, "bundle/law.gates.json", b)
    with_manifest(lambda d: circuit_named(d, "law").update(gates_sha256=sha(b)))(c)
    same(refusal(7, c), "compile-uncontrolled", "bundle/law.gates.json",
         "the gate list of law does not pass the exact hold: (a)")


def test_files_in_a_compile_that_are_no_gate_list_are_passed_over(honest, tmp_path):
    """Step 7 knows a gate list in a Compile's `object` or `result` by its name's ending, `.gates.json`, and passes over
    the other Files there whatever their digests: a QPY file and an ISA QASM 3 file, as P1's twin's Compiles list in
    their `result` (these bytes are neither; step 7 never reads them). The control: the same bytes named as a gate list
    are refused, a gate list its manifest does not name."""
    c = crate(honest, tmp_path)
    qpy, isa = b"QISKIT" + bytes(range(16)), b"OPENQASM 3.0;\n"
    add_file(c, "bundle/law.qpy", qpy, (SMALL_COMPILE, "result"))
    add_file(c, "bundle/law.isa.qasm3", isa, (SMALL_COMPILE, "result"))
    assert refusal(7, c) is None
    add_file(c, "bundle/law-qpy.gates.json", qpy, (SMALL_COMPILE, "result"))
    same(refusal(7, c), "compile-uncontrolled", f"{SMALL_COMPILE} result",
         "bundle/law-qpy.gates.json is a gate list its manifest does not name")


# -- the memo's keys, each held by a crate a key short of it would pass (the second verifier's D2) -------------------
def test_one_gate_list_named_for_two_logical_circuits_of_one_width_is_held_to_each(tmp_path):
    """The comparisons are memoised by the gate list's digest and the logical circuit's width and operations: one
    carried gate list, named first for the 7-qubit circuit it was made from and then for another 7-qubit circuit, is
    compared afresh the second time and refused (a). A key without the operations (K6), or with their count alone
    (S5), answers the second comparison from the first, and the crate passes."""
    p2_sim.clear()
    m = Model()
    m.contribute = False
    first, second = qasm(7, ["x q[0];"], measured=True), qasm(7, ["x q[1];"], measured=True)
    gates = transpile(first)
    m.file("bundle/c0.qasm", first)
    m.file("bundle/c1.qasm", second)
    m.file("bundle/c0.gates.json", gates)
    m.file("bundle/manifest.json", manifest([("job", "c0", "known-answer", "Z" * 7, first, gates),
                                             ("job", "c1", "known-answer", "Z" * 7, second, gates)]))
    compile_entity(m, "#compile-synth-x", [("bundle/c0.qasm", "bundle/c0.gates.json"), ("bundle/c1.qasm", None)])
    m.entity("#hold-synth-x", ["CreateAction", "qro:Hold"], **{
        "qro:heldCompile": {"@id": "#compile-synth-x"}, "qro:holdRule": "qro-exact-hold/1", "qro:exactHold": "holds"})
    c = m.write(tmp_path / "k6")
    same(refusal(7, c), "compile-uncontrolled", "bundle/c0.gates.json",
         "the gate list of c1 does not pass the exact hold: (a) its distribution differs from its logical circuit's by "
         "1.000e+00 at worst")


def law_named_as(basis, extra):
    """The small manifest's law entry given `basis`, and, with `extra`, named once more as `extra` asks."""
    def edit_doc(d):
        law = circuit_named(d, "law")
        law["basis"] = basis
        if extra:
            job_of(d, extra.pop("job"))["circuits"].append(dict(law, **extra))
    return with_manifest(edit_doc)


def test_the_law_circuit_named_again_as_a_coherence_circuit_is_judged_in_that_role(honest, tmp_path):
    """The judgements are memoised by the role too: the law circuit and its gate list, named again as a coherence
    circuit with the law entry's own basis string, are judged as a coherence circuit, and refused (b): the law lays one
    crystal in each pair of sites, so the Z parity of qubits 0 and 1 is -1, not the law's X0X1. A key without the role
    (K7) answers from the law circuit's judgement, and the crate passes. The control: the law entry's basis changed
    alone, the crate passes, as a law circuit's basis is never judged."""
    p2_sim.clear()
    c = law_named_as("XXZZ", {"job": "coherence-xx", "name": "law-as-coherence", "role": "coherence"})(
        crate(honest, tmp_path))
    same(refusal(7, c), "compile-uncontrolled", "bundle/law.gates.json",
         "the gate list of law-as-coherence does not pass the exact hold: (b) its logical circuit, a coherence circuit: "
         "the parity of qubits 0 and 1 is -1.000000000000, where the law's X0X1 is 4/5")
    assert refusal(7, law_named_as("XXZZ", None)(crate(honest, tmp_path / "control"))) is None


def another_law_entry(c, name, logical):
    """A logical circuit and its own gate list added to the small crate, and named in its manifest's law job as a law
    circuit, basis ZZZZ, after the law circuit."""
    gates = transpile(logical)
    add_file(c, f"bundle/{name}.qasm", logical)
    add_file(c, f"bundle/{name}.gates.json", gates)
    return with_manifest(lambda d: job_of(d, "law")["circuits"].append({
        "name": name, "role": "law", "basis": "ZZZZ", "circuit_sha256": sha(logical), "gates_sha256": sha(gates)}))(c)


def test_the_law_circuits_operations_on_five_qubits_are_judged_at_that_width(honest, tmp_path):
    """The judgements are memoised by the logical circuit's width too: the law circuit's operations on 5 qubits, with
    their own gate list, named as a law circuit after the 4-qubit one, hold (a) and are judged afresh, and refused:
    the law's tile has 4 sites. A key without the width (S4) answers from the 4-qubit circuit's judgement, and the
    crate passes."""
    p2_sim.clear()
    logical = qasm(5, small_gates(), measured=True)
    c = crate(honest, tmp_path)
    assert p2_sim.read_qasm(logical).ops == p2_sim.read_qasm(small_files(c, "bundle/law.qasm")).ops
    same(refusal(7, another_law_entry(c, "law5", logical)), "compile-uncontrolled", "bundle/law5.gates.json",
         "the gate list of law5 cannot be held: the circuit has 5 qubits; the law's tile has 4 sites")


def test_another_law_circuit_of_the_same_width_is_judged_by_its_own_operations(honest, tmp_path):
    """The judgements are memoised by the logical circuit's operations too: a second 4-qubit law circuit, its first
    Givens angle bent, with its own gate list, named as a law circuit after the law circuit, holds (a) and is judged
    afresh, and refused (b). A key without the operations answers from the law circuit's judgement, and the crate
    passes."""
    p2_sim.clear()
    c = another_law_entry(crate(honest, tmp_path), "bent", qasm(4, small_gates(t1=0.3), measured=True))
    same(refusal(7, c), "compile-uncontrolled", "bundle/bent.gates.json",
         "the gate list of bent does not pass the exact hold: (b) its logical circuit, a law circuit: it does not lay "
         "the law")


def test_a_coherence_circuit_named_again_in_another_basis_is_judged_in_that_basis(honest, tmp_path):
    """The judgements are memoised by the basis too: the coherence-xx circuit and its gate list, named again with the
    basis XZZX, are judged afresh, and refused: that basis reads X0X3, which the law does not name. A key without the
    basis (K8) answers from coherence-xx's own judgement, and the crate passes."""
    p2_sim.clear()
    c = with_manifest(lambda d: job_of(d, "coherence-xx")["circuits"].append(
        dict(circuit_named(d, "coherence-xx"), name="xx-in-xzzx", basis="XZZX")))(crate(honest, tmp_path))
    same(refusal(7, c), "compile-uncontrolled", "bundle/coherence-xx.gates.json",
         "the gate list of xx-in-xzzx cannot be held: the law names no observable X0X3, which the basis XZZX reads")


# -- Atlas -------------------------------------------------------------------------------------------------------------
def test_a_coherence_pub_on_an_atlas_raw_result_is_refused_by_step_6(tmp_path, monkeypatch):
    """P2's stated limit 10, held (the second verifier's note 4): Atlas's rule gives every Pub of a raw result the all-Z
    setting's layouts, so a coherence PUB on an Atlas raw result holds no outcome in its own basis. The generator's
    contract raises on it; and a crate whose x0x1 was measured anyway, from the all-Z layouts as P2.1's code before
    its second round measured it (here by the rule's lookup patched while the crate is written), is refused by step 6
    at the PUB."""
    with pytest.raises(p2_measures.MeasureError, match="P2 measures none of Atlas's coherences"):
        atlas_model(coherence=True).write(tmp_path / "contract")
    with monkeypatch.context() as patched:
        patched.setattr(p2_measures, "decode_rule", lambda md, pub: "a rule that reads a PUB in its own basis")
        c = atlas_model(coherence=True).write(tmp_path / "measured")
    assert "#measurement-acoh-0-x0x1" in {e["@id"] for e in read_md(c)["@graph"]}
    same(refusal(6, c), "measure-class", "#pub-acoh-0", "its raw result is read by quantum_film.atlas.decode/v1, which "
                                                         "gives every PUB the all-Z setting's layouts")


# -- as a process ------------------------------------------------------------------------------------------------------
def process(argv):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-m", "qro", *argv], capture_output=True, env=env, cwd=ROOT)


def test_as_a_process_the_honest_crate_passes_every_step_to_step_9(honest):
    p = process(["check", str(honest / "small")])
    assert (p.returncode, p.stderr) == (1, b"")
    assert p.stdout == f"REFUSED step-unbuilt at ./ qro:generator: no generator {GENERATOR} is built\n".encode("ascii")


@pytest.mark.parametrize("plant, line", [
    ("a class declared", "REFUSED measure-class at #contrast-x0x1-uniform qro:class: the crate says integrity"),
    ("a gate list broken",
     "REFUSED compile-uncontrolled at bundle/law.gates.json: the gate list of law does not pass")])
def test_as_a_process_a_plant_is_one_refused_line(honest, tmp_path, plant, line):
    make = {**STEP6, **STEP7}[plant][0]
    p = process(["check", str(make(crate(honest, tmp_path)))])
    assert (p.returncode, p.stderr) == (1, b"")
    assert p.stdout.startswith(line.encode("ascii")) and p.stdout.count(b"\n") == 1 and p.stdout.endswith(b"\n")
    assert p.stdout.isascii()


# -- the net -----------------------------------------------------------------------------------------------------------
def test_a_bug_inside_step_6_is_a_refusal_by_its_name(honest, monkeypatch):
    def broken(*args):
        raise ZeroDivisionError("planted")
    monkeypatch.setattr(p2_measures, "value", broken)
    same(refusal(6, honest / "small"), "measure-class", "#pub-jobcoh-0", "cannot be checked: ZeroDivisionError")


def test_a_bug_inside_step_7_is_a_refusal_by_its_name(honest, monkeypatch):
    def broken(*args):
        raise KeyError("planted")
    monkeypatch.setattr(p2_hold, "hold_circuit", broken)
    same(refusal(7, honest / "small"), "compile-uncontrolled", SMALL_COMPILE, "cannot be checked: KeyError")


def test_a_deep_recursion_inside_a_step_is_a_refusal(honest, monkeypatch):
    def deep(*args):
        raise RecursionError("planted")
    monkeypatch.setattr(p2_measures, "certify", deep)
    same(refusal(6, honest / "small"), "measure-class", "#measuring qro:family", "cannot be checked: RecursionError")


def run_main(argv):
    r_out, w_out = os.pipe()
    r_err, w_err = os.pipe()
    try:
        code = main(argv, w_out, w_err)
    finally:
        os.close(w_out)
        os.close(w_err)
    with os.fdopen(r_out, "rb") as o, os.fdopen(r_err, "rb") as e:
        return code, o.read(), e.read()


@pytest.mark.parametrize("step, target, raised, code", [
    (6, (p2_hold, "law_circuit_problem"), OSError("planted"), 3),
    (6, (p2_hold, "law_circuit_problem"), MemoryError(), 3),
    (6, (p2_hold, "law_circuit_problem"), PermissionError(13, "planted", "circuits/small-law.qasm"), 2),
    (7, (p2_hold, "hold_circuit"), OSError("planted"), 3),
    (7, (p2_hold, "hold_circuit"), MemoryError(), 3),
    (7, (p2_hold, "hold_circuit"), PermissionError(13, "planted", "bundle/law.gates.json"), 2)])
def test_the_hosts_failures_inside_p2s_steps_are_never_a_verdict(honest, loaded, monkeypatch, step, target, raised,
                                                                   code):
    """An OSError or a MemoryError raised inside step 6's or step 7's nets passes through them: the checker failing,
    exit 3; a PermissionError is the user's, exit 2. None is a refusal."""
    def failing(*args):
        raise raised
    monkeypatch.setattr(*target, failing)
    with pytest.raises(type(raised)):
        refusal(step, honest / "small")
    got, out, err = run_main(["check", str(honest / "small")])
    assert got == code and out == b""
    assert err.startswith(b"FAILED: the checker itself failed" if code == 3 else raised.filename.encode() +
                          b": cannot be read")


def test_the_steps_memos_never_change_a_verdict(honest, tmp_path):
    """Run cold and warm, the honest crates pass and a broken gate list is refused alike."""
    c = broken_law_gate_list(crate(honest, tmp_path))
    for _ in range(2):
        p2_sim.clear()
        assert refusal(7, honest / "small") is None and refusal(7, c) is not None
        assert refusal(7, honest / "small") is None and refusal(7, c) is not None
