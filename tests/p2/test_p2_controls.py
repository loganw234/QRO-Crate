"""P2's two controls (study QRO-0, section 11; P2's design, item 11), planted in P1's twin by controls/plants_p2.py with
P1.2's toolkit: each comes out through controls.run.outcome, as the runner and the registry's own test run it, refused by
its step's own name at the place it planted; each plant is the plant its row describes, and plants nothing else; a plant
that does not find what it is written for plants nothing; and, beside them, the design's variants: other classes
declared, other gate lists broken, and the phase plant, which the whole checker accepts (P2's stated limit 1).

The twin is built once in the process (plants_p1.pristine_twin) and copied for each plant; every check here is the whole
checker's, steps 1 to 9, P2's 6 and 7 among them."""
import json
import math
import re
from pathlib import Path

import pytest

from controls import plants_p1 as toolkit
from controls import plants_p2 as plants
from controls import registry
from controls.run import outcome
from qro import canonical, checker, register_p1, spelling
from qro.refusal import Refused

BUNDLE = toolkit.MORNING_BUNDLE
LAW, COH_XX, KA = f"{BUNDLE}/law.gates.json", f"{BUNDLE}/coherence-xx.gates.json", f"{BUNDLE}/known-answer.gates.json"
SHEETS = (f"{toolkit.IBM}/sheet-01", f"{toolkit.IBM}/sheet-02")


def read(crate, rel):
    return Path(crate).joinpath(*rel.split("/")).read_bytes()


def files_of(crate):
    return {p.relative_to(crate).as_posix(): p.read_bytes() for p in sorted(Path(crate).rglob("*")) if p.is_file()}


def graph_md(crate):
    return json.loads(read(crate, canonical.DESCRIPTOR))


def graph(crate):
    return {e["@id"]: e for e in graph_md(crate)["@graph"]}


def verdict(crate):
    """The whole checker's verdict: ("accepted", identity) or ("refused", name, where)."""
    checker.load()
    try:
        return "accepted", canonical.body_digest(checker.check(crate))
    except Refused as r:
        return "refused", r.name, r.where


@pytest.fixture(scope="module")
def twin(tmp_path_factory):
    """A copy of the twin as the tree builds it, never planted: the bytes every plant below starts from."""
    return toolkit.twin_crate(tmp_path_factory.mktemp("p2-twin"))


@pytest.fixture(scope="module")
def honest(twin):
    """The whole checker's verdict on the twin, once."""
    return verdict(twin)


@pytest.fixture(scope="module")
def declared(tmp_path_factory):
    """`class-declared`, planted once in its own copy of the twin, for the tests that read what it planted."""
    return plants.class_declared(toolkit.twin_crate(tmp_path_factory.mktemp("p2-declared")))


@pytest.fixture(scope="module")
def broken(tmp_path_factory):
    """`compile-broken`, planted once in its own copy of the twin, for the tests that read what it planted."""
    return plants.compile_broken(toolkit.twin_crate(tmp_path_factory.mktemp("p2-broken")))


# -- the two controls, as the runner runs them ---------------------------------------------------------------------------
def test_both_controls_are_p2s_rows_and_plants_joins_them_to_the_registrys():
    assert sorted(plants.PLANTS) == ["class-declared", "compile-broken"]
    every = registry.plants()
    for name in plants.PLANTS:
        c = registry.CONTROL[name]
        assert (c.owner, c.expected) == ("P2", "refused") and every[name] is plants.PLANTS[name]
    assert (registry.CONTROL["class-declared"].refusal, registry.CONTROL["compile-broken"].refusal) == (
        "measure-class", "compile-uncontrolled")


def test_class_declared_is_refused_measure_class_at_its_contrast():
    assert outcome("class-declared") == (
        "refused", "measure-class", "#contrast-n-crystal-share-uniform qro:class: the crate says signal; the law and "
                                    "the twin's rule give integrity")


def test_compile_broken_is_refused_compile_uncontrolled_at_the_law_gate_list():
    got, name, where = outcome("compile-broken")
    assert (got, name) == ("refused", "compile-uncontrolled")
    assert re.fullmatch(r"2026-10-05/ibm/ibm_kingston/bundle/law\.gates\.json: the gate list of law does not pass the "
                        r"exact hold: \(a\) its distribution differs from its logical circuit's by 2\.3[0-9]{2}e-03 at "
                        r"worst, against 1e-10", where), where


def test_each_controls_twin_is_p1s_twin_and_is_accepted(twin, honest):
    """The genuine crate every plant starts from: P1's twin, with P2's question terms and entities, accepted by every
    step, its identity the one its metadata gives."""
    assert honest[0] == "accepted" and honest[1] == canonical.body_digest(graph_md(twin))
    ids = graph(twin)
    assert ids[plants.CONTRAST]["qro:class"] == "integrity" and json.loads(read(twin, LAW))["gates"][plants.GATE] == \
        plants.SX


# -- each plant is the plant its row describes ---------------------------------------------------------------------------
def test_class_declared_changes_that_one_word_and_nothing_else(twin, declared):
    crate = declared
    before, after = files_of(twin), files_of(crate)
    assert sorted(k for k in after if after[k] != before.get(k)) == [canonical.DESCRIPTOR] and set(after) == set(before)
    old, new = graph(twin), graph(crate)
    assert set(old) == set(new)
    assert [i for i in old if old[i] != new[i]] == [plants.CONTRAST]
    assert dict(new[plants.CONTRAST], **{"qro:class": "integrity"}) == old[plants.CONTRAST]
    assert new[plants.CONTRAST]["qro:class"] == "signal"


def test_compile_broken_changes_gate_303_and_recomputes_every_digest_held_over_it(twin, broken):
    """Gate 303 alone, in Quantum-Film's own style (its JSON written again gives its bytes); the three bundle manifests
    that name the law gate list's digest, the morning's and the two sheets', each in that one field; the lines and
    markers of each run in their bundle digest alone; and the metadata, regenerated by P1's generator."""
    crate = broken
    before, after = files_of(twin), files_of(crate)
    changed = sorted(k for k in after if after[k] != before.get(k))
    runs = [f"{BUNDLE[:-len('bundle')]}run"] + [f"{s}/run" for s in SHEETS]
    manifests = [f"{BUNDLE}/manifest.json"] + [f"{s}/bundle/manifest.json" for s in SHEETS]
    marks = sorted(f"{r}/{n}" for r in runs for n in (p.split("/")[-1] for p in before if p.startswith(r + "/"))
                   if n.endswith(("-line.json", "-submitting.json")))
    assert changed == sorted([LAW, canonical.DESCRIPTOR] + manifests + marks) and set(after) == set(before)
    assert len(marks) == 8, "the morning run's two jobs and each sheet's one, each a line and a marker"
    old_doc, new_doc = json.loads(before[LAW]), json.loads(after[LAW])
    assert old_doc["gates"][303] == ["sx", [47], [], []] and new_doc["gates"][303] == ["x", [47], [], []]
    new_doc["gates"][303] = old_doc["gates"][303]
    assert new_doc == old_doc
    style = toolkit.STYLES[toolkit.style_of(LAW)]
    assert style(json.loads(before[LAW])) == before[LAW] and style(json.loads(after[LAW])) == after[LAW]
    old_digest, new_digest = toolkit.sha(before[LAW]), toolkit.sha(after[LAW])
    for m in manifests:
        a, b = json.loads(before[m]), json.loads(after[m])
        for job_a, job_b in zip(a["jobs"], b["jobs"]):
            for ca, cb in zip(job_a["circuits"], job_b["circuits"]):
                if ca.get("gates_sha256") == old_digest:
                    assert cb.pop("gates_sha256") == new_digest
                    ca.pop("gates_sha256")
        assert a == b, m
    for mark in marks:
        a, b = json.loads(before[mark]), json.loads(after[mark])
        bundle = mark.rsplit("/run/", 1)[0] + "/bundle/manifest.json"
        assert b.pop("bundle_sha256") == toolkit.sha(after[bundle]) and a.pop("bundle_sha256") != toolkit.sha(after[bundle])
        assert a == b, mark
    md = json.loads(after[canonical.DESCRIPTOR])
    regenerated = register_p1.GENERATORS[md["@graph"][1]["qro:generator"]](crate)
    assert canonical.body_digest(regenerated) == canonical.body_digest(md), "the metadata is the generator's"


def test_the_holds_of_the_broken_crate_all_say_holds_so_only_the_hold_itself_refuses_it(broken):
    """The forger's crate claims every gate list held: each Hold says `holds`, from presence, as the generator writes
    it, and the manifests name the broken list's digest. Steps 1 to 6 hold; step 7 refuses it by simulating."""
    holds = {i: e["qro:exactHold"] for i, e in graph(broken).items() if "qro:Hold" in canonical.types(e)}
    assert holds == {"#hold-ibm_kingston-morning": "holds", "#hold-ibm_kingston-sheet-01": "holds",
                     "#hold-ibm_kingston-sheet-02": "holds"}
    assert verdict(broken) == ("refused", "compile-uncontrolled", LAW)


# -- a plant that is not planted ------------------------------------------------------------------------------------------
def test_each_plant_with_its_fault_taken_out_leaves_the_twin_as_it_was(twin, honest, tmp_path):
    """The control's own control: each plant run with the fault taken out (the word left as it is; gate 303 written as
    it was, every digest recomputed and the metadata regenerated all the same) gives the twin back, byte for byte, which
    the whole checker accepts: so each refusal above is the fault's and not the planting's."""
    same = plants.declare_class(toolkit.twin_crate(tmp_path / "a"), now=plants.INTEGRITY)
    assert files_of(same) == files_of(twin)
    kept = plants.break_gate_list(toolkit.twin_crate(tmp_path / "b"), now=plants.SX)
    assert files_of(kept) == files_of(twin) and honest[0] == "accepted"


def test_a_plant_refuses_a_crate_it_is_not_written_for_and_writes_nothing(broken, declared):
    """Planted again on a crate it has planted, or on a gate or a Contrast that is not there, a plant raises PlantError
    and writes nothing."""
    once = files_of(broken)
    with pytest.raises(plants.PlantError, match=r"gate 303 of .*law\.gates\.json is not \['sx', \[47\], \[\], \[\]\]"):
        plants.compile_broken(broken)
    with pytest.raises(plants.PlantError, match="gate 9999 of "):
        plants.break_gate_list(broken, gate=9999)
    assert files_of(broken) == once
    twice = files_of(declared)
    with pytest.raises(plants.PlantError, match="#contrast-n-crystal-share-uniform does not say integrity"):
        plants.class_declared(declared)
    with pytest.raises(plants.PlantError, match="#contrast-no-such does not say integrity"):
        plants.declare_class(declared, "#contrast-no-such")
    assert files_of(declared) == twice


# -- beside them: the design's variants ----------------------------------------------------------------------------------
@pytest.mark.parametrize("contrast, was, now", [
    ("#contrast-linear-xeb-uniform", "signal", "integrity"),
    ("#contrast-forbidden-share-dephased", "integrity", "signal"),
    ("#contrast-x0x1-dephased", "signal", "integrity"),
], ids=["linear-xeb against uniform said integrity", "forbidden-share against dephased said signal",
        "x0x1 against dephased said integrity"])
def test_another_class_declared_is_refused_at_its_contrast(tmp_path, contrast, was, now):
    crate = plants.declare_class(toolkit.twin_crate(tmp_path), contrast, was, now)
    assert verdict(crate) == ("refused", "measure-class", f"{contrast} qro:class")


def test_a_class_declared_with_its_values_made_to_agree_is_refused_all_the_same(tmp_path):
    """A forger who declares the n-crystal share a signal against the uniform twin and edits the twin's value to look
    like one: the class, computed from the law's bytes and the twin's rule, still refuses it."""
    def edit(g):
        e = toolkit.entity(g, plants.CONTRAST)
        assert (e["qro:lawValue"], e["qro:twinValue"]) == (spelling.rational(1), spelling.rational(1))
        e.update({"qro:class": "signal", "qro:twinValue": spelling.rational(0)})
    crate = toolkit.patch(toolkit.twin_crate(tmp_path), edit)
    assert verdict(crate) == ("refused", "measure-class", f"{plants.CONTRAST} qro:class")


def gate(crate, rel, i):
    return json.loads(read(crate, rel))["gates"][i]


@pytest.mark.parametrize("rel, i, kind, now", [
    (LAW, 309, ["cz", [47, 57]], lambda g: ["barrier", g[1], [], []]),
    (LAW, 317, ["rz", [47]], lambda g: ["rz", g[1], [], [g[3][0] + math.pi / 2]]),
    (COH_XX, 60, ["sx", [20]], lambda g: ["barrier", g[1], [], []]),
    (KA, 0, ["x", [20]], lambda g: ["barrier", g[1], [], []]),
], ids=["law: gate 309's cz on 47 and 57 dropped", "law: gate 317's rz turned a further pi/2",
        "coherence-xx: the last sx on qubit 20 dropped", "known-answer: its first x dropped"])
def test_another_gate_list_broken_with_every_digest_recomputed_is_refused_at_it(tmp_path, rel, i, kind, now):
    """Dropping a gate is writing a barrier on its qubits in its place: a barrier does nothing. The known-answer gate list
    is carried in all three bundles of the twin, and every copy is broken."""
    crate = toolkit.twin_crate(tmp_path)
    was = gate(crate, rel, i)
    assert was[:2] == kind, was
    crate = plants.break_gate_list(crate, rel, i, was, now(was))
    assert verdict(crate) == ("refused", "compile-uncontrolled", rel)


def test_the_phase_plant_with_every_digest_recomputed_is_accepted_the_stated_limit(twin, honest, tmp_path):
    """P2's stated limit 1, on the whole crate: the law gate list's barrier made an rz(0.7) on qubit 43, just before its
    measurement. No Z-basis probability moves, so the exact hold passes it, and with every digest recomputed and the
    metadata regenerated the whole checker accepts a crate whose gate list is not the one that was compiled. Only
    another copy of the bytes, its digest unchanged, tells them apart."""
    crate = toolkit.twin_crate(tmp_path)
    was = gate(crate, LAW, 615)
    assert was[0] == "barrier" and len(was[1]) == 16 and gate(crate, LAW, 616)[0] == "measure"
    crate = plants.break_gate_list(crate, LAW, 615, was, ["rz", [43], [], [0.7]])
    assert read(crate, LAW) != read(twin, LAW)
    got = verdict(crate)
    assert got[0] == "accepted" and got != honest
