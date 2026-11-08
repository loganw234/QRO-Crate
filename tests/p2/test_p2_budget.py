"""The exact hold's work budget (P2.2; the lead's ruling of 2026-11-08T07:36:59Z), part of `qro-exact-hold/1` for step 7
and of `qro-measures/1` for step 6, 2^28 amplitude passes each:
  - the simulator and the price ask one function whether a block enters the dense state, and the simulator's own count
    of its passes is the price's, on random gate lists, on hostile ones and on v0's;
  - a file's price and a pair's, worked by hand; v0's pairs and the twin's counts, pinned;
  - step 7 counts each Compile and each manifest entry 16, and each distinct pair its whole price, once, the first time
    the walk meets it, whatever the memo holds: the count is a pure function of the crate's bytes, cold and after
    another crate has warmed the memo, and a reference that repeats a pair costs its 16; the carried digests are found
    once a check and each distinct manifest read once; reading the metadata is not counted;
  - a crate whose count would pass the budget is refused by the step's name, where the spend would pass it, before any
    of what it prices is simulated; a hostile gate list past the budget is refused unsimulated;
  - step 6 prices the question's law circuit the same way, counting from zero apart from step 7, and refuses
    `measure-class` before any of it is simulated."""
import json
import math
import random
from pathlib import Path

import pytest
from p2_builder import (SOURCE_PATH, compile_entity, data, qasm, read_md, real_model, refusal, rewrite, sha,
                        small_model)

from controls import plants_p1 as toolkit
from qro import p2_hold, p2_law, p2_sim, p2_steps
from qro.p1_graph import Index

KINGSTON = ("known-answer", "law", "coherence-xx", "coherence-yy")


def gate_list(n, m, gates):
    return json.dumps({"format": "quantum-film/isa-gates/v1", "num_qubits": n, "num_clbits": m, "global_phase": 0.0,
                       "layout": {"initial": list(range(m)), "final": list(range(m)),
                                  "routing_permutation": list(range(n))},
                       "gates": gates}).encode("ascii")


def measures(m):
    return [["measure", [q], [q], []] for q in range(m)]


def counted(monkeypatch, module, name):
    """The module's function `name`, wrapped to count its calls: the list of their first arguments."""
    calls, real = [], getattr(module, name)

    def wrapper(*args, **kwargs):
        calls.append(args[0] if args else None)
        return real(*args, **kwargs)
    monkeypatch.setattr(module, name, wrapper)
    return calls


@pytest.fixture(scope="module")
def twin(tmp_path_factory):
    crate = toolkit.twin_crate(tmp_path_factory.mktemp("p2-budget-twin"))
    return crate, read_md(crate)


# -- the figures -------------------------------------------------------------------------------------------------------
def test_the_figures_are_the_rulings():
    assert p2_hold.BUDGET == p2_law.BUDGET == 2 ** 28 == 268_435_456
    assert (p2_hold.READ, p2_hold.PER_ENTRY, p2_hold.PER_COMPILE) == (256, 16, 16)
    assert (p2_hold.RULE, p2_law.MEASURE_SET) == ("qro-exact-hold/1", "qro-measures/1")


# -- one test of the light cone, two readers of it ---------------------------------------------------------------------
def test_the_simulator_and_the_price_ask_one_function_whether_a_block_enters(monkeypatch):
    """`simulate` asks `enters` of each block before it applies it, and `cost` of each block it prices: the same
    function, called once a block by each, so a change to either reader is a change to both."""
    blocks = p2_sim.fuse(p2_sim.read_gate_list(data("law.gates.json")).ops)
    calls = counted(monkeypatch, p2_sim, "enters")
    st = p2_sim.simulate(blocks)
    assert len(calls) == len(blocks) == 51
    passes, axes = p2_sim.cost(blocks)
    assert len(calls) == 2 * len(blocks) and passes == st.work == 789_756 and axes == set(st.axes)


def same_count(blocks, start=None):
    """The simulator's own count of its passes, from `start`'s state, and the price's, which must agree."""
    st = p2_sim.simulate(blocks, start)
    passes, axes = p2_sim.cost(blocks, set(start.axes) if start is not None else ())
    assert (st.work, set(st.axes)) == (passes, axes)
    return st


GATES = ("x", "sx", "rz", "rz-pi", "rz-0", "cz")


def random_gate_list(rng, n):
    """A random list on n qubits, many of its gates monomial (x, cz, rz), so that the light cone's test decides often:
    a fused block of monomial gates, or of two sx, stays classical."""
    out = []
    for _ in range(rng.randint(1, 50)):
        g = rng.choice(GATES)
        if g == "cz":
            a, b = rng.sample(range(n), 2)
            out.append(["cz", [a, b], [], []])
        else:
            q = rng.randrange(n)
            if g == "x" or g == "sx":
                out.append([g, [q], [], []])
            else:
                angle = {"rz": rng.uniform(-math.pi, math.pi), "rz-pi": math.pi, "rz-0": 0.0}[g]
                out.append(["rz", [q], [], [angle]])
    return gate_list(n, n, out + measures(n))


def test_the_simulators_own_count_of_its_passes_is_the_prices_on_random_gate_lists():
    rng = random.Random(28)
    entered = classical = 0
    for _ in range(300):
        b = random_gate_list(rng, rng.randint(2, 7))
        blocks = p2_sim.fuse(p2_sim.read_gate_list(b).ops)
        st = same_count(blocks)
        assert p2_sim.gate_list_cost(b).passes == st.work
        entered += st.work > 0
        classical += st.work == 0
    assert entered > 100 and classical > 20, "both sides of the light cone's test are reached"


HOSTILE = {
    "two sx fused into an x, which stays classical": [["sx", [0], [], []], ["sx", [0], [], []]],
    "an rz and a cz on classical bits, then an sx that spreads": [["x", [0], [], []], ["rz", [0], [], [0.7]],
                                                                   ["cz", [0, 1], [], []], ["sx", [1], [], []],
                                                                   ["cz", [1, 2], [], []]],
    "an x on every qubit, then a cz on each pair: no pass": [["x", [q], [], []] for q in range(4)]
    + [["cz", [a, b], [], []] for a in range(4) for b in range(a + 1, 4)],
    "a brick-work over eight qubits, its pairs alternating so that nothing fuses": [
        g for layer in range(6) for g in ([["sx", [q], [], []] for q in range(8)]
                                          + [["cz", [q, q + 1], [], []] for q in range(layer % 2, 7, 2)])],
    "a block that spreads, and then a monomial one that holds a qubit already in the state": [
        ["sx", [0], [], []], ["cz", [0, 1], [], []], ["x", [0], [], []], ["cz", [1, 2], [], []],
        ["rz", [2], [], [1.0]]],
}


@pytest.mark.parametrize("case", sorted(HOSTILE))
def test_the_simulators_own_count_of_its_passes_is_the_prices_on_hostile_gate_lists(case):
    n = 1 + max(q for g in HOSTILE[case] for q in g[1])
    b = gate_list(n, n, HOSTILE[case] + measures(n))
    st = same_count(p2_sim.fuse(p2_sim.read_gate_list(b).ops))
    assert p2_sim.gate_list_cost(b).passes == st.work
    if case.startswith("two sx") or case.startswith("an x on every"):
        assert st.work == 0 and not st.axes


def test_the_simulators_own_count_of_its_passes_is_the_prices_on_v0s_files():
    """Kingston's four gate lists and four logical circuits, as P1's twin carries them, and the question's law circuit:
    each logical circuit's core from |0...0> and its tail from the core's state, as `logical` simulates them."""
    for name in KINGSTON:
        b = data(f"{name}.gates.json")
        st = same_count(p2_sim.fuse(p2_sim.read_gate_list(b).ops))
        assert p2_sim.gate_list_cost(b).passes == st.work == (0 if name == "known-answer" else 789_756)
    for name in [f"{n}.qasm" for n in KINGSTON] + ["circuit-ed767c01bd4b851d.qasm"]:
        b = data(name)
        core, tail = p2_sim.split(p2_sim.read_qasm(b).ops)
        st = same_count(p2_sim.fuse([p2_sim._matrix(op) for op in core]))
        st2 = same_count(p2_sim.fuse([p2_sim._matrix(op) for op in tail]), st)
        assert p2_sim.logical_cost(b).passes == st.work + st2.work, name
        if name != "known-answer.qasm":
            assert st.work == 816_924, name


# -- prices worked by hand --------------------------------------------------------------------------------------------
def test_a_files_price_and_a_pairs_worked_by_hand():
    """One qubit, an x and its measure: two gates read (512), no pass (an x on a classical bit), and its distribution
    off a state of no qubit into 2 outcomes (1 + 2): 515. Two qubits, an sx then a cz and two measures: four gates
    (1,024), one fused block that enters a state of two qubits (4), and its distribution (4 + 4): 1,036. A logical
    circuit of one qubit and an h, four lines (1,024), its tail's one pass on one qubit (2), its distribution (2 + 2):
    1,030. The pair of the first and that circuit, as a known answer: 515 + 1,030, a comparison over 2 outcomes and a
    judgement over 2: 1,549; as a law circuit, the law's layouts too. As a question's law circuit, its reading alone,
    since a circuit not of the law's width is refused before anything of it is simulated."""
    one = gate_list(1, 1, [["x", [0], [], []]] + measures(1))
    two = gate_list(2, 2, [["sx", [0], [], []], ["cz", [0, 1], [], []]] + measures(2))
    h = b'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\nh q[0];\n'
    p2_sim.clear()
    assert p2_sim.gate_list_cost(one) == p2_sim.Cost(2, 0, 0, 1)
    assert p2_hold.file_price(p2_sim.gate_list_cost(one)) == 515
    assert p2_sim.gate_list_cost(two) == p2_sim.Cost(4, 4, 2, 2)
    assert p2_hold.file_price(p2_sim.gate_list_cost(two)) == 1036
    assert p2_sim.logical_cost(h) == p2_sim.Cost(4, 2, 1, 1)
    assert p2_hold.file_price(p2_sim.logical_cost(h)) == 1030
    ka = p2_hold.Named("c", "known-answer", "Z", sha(h), sha(one))
    assert p2_hold.pair_price(ka, one, h, None) == 1549
    law = p2_law.read(p2_law.law_bytes())
    assert p2_hold.pair_price(p2_hold.Named("c", "law", "Z", sha(h), sha(one)), one, h, law) == 1549 + law.D == 5917
    assert p2_hold.law_circuit_price(h, law) == 1024     # not the law's width: refused before it is simulated


# -- step 7's count on v0's twin ---------------------------------------------------------------------------------------
TWIN_PAIRS = {"known-answer": 274_434, "law": 2_316_584, "coherence-xx": 2_443_800, "coherence-yy": 2_444_312}
TWIN_COUNT = sum(TWIN_PAIRS.values()) + 16 * 12 + 16 * 3
LAW_CIRCUIT = 1_294_892


def test_v0s_pairs_and_the_twins_counts_are_pinned(twin):
    """The twin's three Compiles name the same four pairs, each priced once, 7,479,130 in all, and 16 for each of the
    twelve entries and of the three Compiles: 7,479,370. Step 6 counts the question's law circuit alone, from zero."""
    crate, md = twin
    named = {n.name: n for n in p2_hold.read_manifest(data("manifest.json"))}
    law = p2_law.read(p2_law.law_bytes())
    for name, price in TWIN_PAIRS.items():
        got = p2_hold.pair_price(named[name], data(f"{name}.gates.json"), data(f"{name}.qasm"),
                                 None if name == "known-answer" else law)
        assert got == price, name
    assert p2_steps._step7(Path(crate), md) == TWIN_COUNT == 7_479_370
    assert p2_steps._step6(Path(crate), md) == LAW_CIRCUIT == p2_hold.law_circuit_price(
        data("circuit-ed767c01bd4b851d.qasm"), law)


def test_the_count_is_a_pure_function_of_the_crates_bytes_cold_or_after_another_crate(twin, tmp_path):
    """The twin counted with every memo empty, then after P2's real crate, whose gate lists are the twin's own bytes,
    has warmed the memos, and again warm: the same count each time. The memo makes the work less, never the count."""
    crate, md = twin
    real = real_model().write(tmp_path / "real")
    p2_sim.clear()
    cold = p2_steps._step7(Path(crate), md)
    p2_sim.clear()
    assert p2_steps._step7(real, read_md(real)) > 0 and p2_sim.GATE_LISTS.entries
    assert p2_steps._step7(Path(crate), md) == cold == p2_steps._step7(Path(crate), md) == TWIN_COUNT


def test_a_pair_is_held_once_a_check_and_a_reference_that_repeats_it_costs_its_16(twin, monkeypatch):
    """The twin's twelve references are four distinct pairs: each held once in a check, and each repeat costs its
    entry's 16 and nothing more, the count being the four prices and 16 for each entry and Compile. A second check
    holds them again: the record of held pairs is the check's."""
    crate, md = twin
    held = counted(monkeypatch, p2_hold, "hold_circuit")
    priced = counted(monkeypatch, p2_hold, "pair_price")
    assert p2_steps._step7(Path(crate), md) == TWIN_COUNT
    assert len(held) == len(priced) == 4 and sorted(n.name for n in held) == sorted(KINGSTON)
    p2_steps._step7(Path(crate), md)
    assert len(held) == len(priced) == 8


def test_the_carried_digests_are_found_once_a_check_and_each_distinct_manifest_read_once(tmp_path, monkeypatch):
    """P2's small crate with a second Compile that lists the first one's manifest File: one look over the crate's Files
    for the carried digests, one reading of the manifest, its four pairs held once, and the second Compile adding 16
    for itself and 16 for each of its four entries, nothing more."""
    one = small_model().write(tmp_path / "one")
    alone = p2_steps._step7(one, read_md(one))
    m = small_model()
    compile_entity(m, "#compile-synth-again", [("bundle/law.qasm", "bundle/law.gates.json")])
    two = m.write(tmp_path / "two")
    looks, of_type = [], Index.of_type
    monkeypatch.setattr(Index, "of_type", lambda idx, t: looks.append(t) or of_type(idx, t))
    reads = counted(monkeypatch, p2_hold, "read_manifest")
    held = counted(monkeypatch, p2_hold, "hold_circuit")
    assert p2_steps._step7(two, read_md(two)) == alone + 16 + 4 * 16
    assert (looks.count("File"), len(reads), len(held)) == (1, 1, 4)


def test_every_entry_costs_its_16_whether_or_not_its_gate_list_is_carried(tmp_path, monkeypatch):
    """P2's small crate with none of its four gate lists carried counts 16 for its Compile and 16 for each entry, 80,
    and holds nothing; with the law's gate list alone withheld, 80 and the three carried pairs' prices."""
    held = counted(monkeypatch, p2_hold, "hold_circuit")
    none = small_model(gate_lists=False).write(tmp_path / "none")
    assert p2_steps._step7(none, read_md(none)) == 16 + 4 * 16 and held == []
    m = small_model(uncarried=("law",))
    some = m.write(tmp_path / "some")
    law = p2_law.read(m.files["question/law.json"])
    named = {n.name: n for n in p2_hold.read_manifest(m.files["bundle/manifest.json"])}
    prices = [p2_hold.pair_price(named[k], m.files[f"bundle/{k}.gates.json"], m.files[f"bundle/{k}.qasm"],
                                 None if k == "known-answer" else law)
              for k in ("known-answer", "coherence-xx", "coherence-yy")]
    assert p2_steps._step7(some, read_md(some)) == 16 + 4 * 16 + sum(prices)
    assert sorted(n.name for n in held) == ["coherence-xx", "coherence-yy", "known-answer"]


# -- the refusal, before the work it prices ----------------------------------------------------------------------------
def test_a_spend_past_the_budget_refuses_where_it_would_pass_before_anything_of_it_is_simulated(twin, monkeypatch):
    """With the budget made smaller: below the first Compile's 16, the twin is refused at that Compile, walking it,
    nothing held; below the count at the morning bundle's last pair, it is refused at that pair's gate list, holding
    it, the three pairs before it held and that one never; one short of the whole count, at the last Compile's last
    entry."""
    crate, md = twin
    held = counted(monkeypatch, p2_hold, "hold_circuit")
    morning = "#compile-ibm_kingston-morning"
    monkeypatch.setattr(p2_hold, "BUDGET", 15)
    r = refusal(7, crate, md)
    assert (r.name, r.where, held) == ("compile-uncontrolled", morning, [])
    assert r.detail == ("walking this Compile would bring this crate's exact hold to 16 amplitude passes, past the 15 "
                        "that qro-exact-hold/1 allows a crate; nothing past it is simulated")
    before_yy = 16 + 4 * 16 + TWIN_PAIRS["known-answer"] + TWIN_PAIRS["law"] + TWIN_PAIRS["coherence-xx"]
    monkeypatch.setattr(p2_hold, "BUDGET", before_yy + TWIN_PAIRS["coherence-yy"] - 1)
    r = refusal(7, crate, md)
    assert (r.name, r.where) == ("compile-uncontrolled", f"{toolkit.MORNING_BUNDLE}/coherence-yy.gates.json")
    over = before_yy + TWIN_PAIRS["coherence-yy"]
    assert r.detail.startswith(f"holding it would bring this crate's exact hold to {over} amplitude passes")
    assert [n.name for n in held] == ["known-answer", "law", "coherence-xx"]
    monkeypatch.setattr(p2_hold, "BUDGET", TWIN_COUNT - 1)
    r = refusal(7, crate, md)
    assert (r.name, r.where) == ("compile-uncontrolled", "#compile-ibm_kingston-sheet-02")
    assert r.detail.startswith(f"walking its manifest would bring this crate's exact hold to {TWIN_COUNT}")
    monkeypatch.setattr(p2_hold, "BUDGET", TWIN_COUNT)
    assert refusal(7, crate, md) is None


def hostile_list(active=20, layers=32):
    """A gate list that spreads over `active` qubits and then makes about `layers` times `active` / 2 blocks on the
    whole state, its pairs alternating so that no two blocks fuse; it measures four clbits, as the small crate's law
    circuit has four qubits. At its defaults, 988 gates whose price is 316,398,604 amplitude passes, past 2^28 (2^20
    passes a block, 300 blocks). The test never simulates it; by the rates measured for where its blocks sit, among
    them the slow placement on axes 0 and 1, that would take about 1.5 to 2 minutes here (BELIEVED, extrapolated)."""
    gates = [["sx", [q], [], []] for q in range(active)]
    gates += [["cz", [q, q + 1], [], []] for q in range(active - 1)]
    for layer in range(layers):
        gates += [["sx", [q], [], []] for q in range(active)]
        gates += [["cz", [q, q + 1], [], []] for q in range(layer % 2, active - 1, 2)]
    gates += [["barrier", list(range(active)), [], []]] + [["measure", [q], [q], []] for q in range(4)]
    doc = {"format": "quantum-film/isa-gates/v1", "num_qubits": active, "num_clbits": 4, "global_phase": 0.0,
           "layout": {"initial": [0, 1, 2, 3], "final": [0, 1, 2, 3], "routing_permutation": list(range(active))},
           "gates": gates}
    return json.dumps(doc).encode("ascii")


def test_a_hostile_gate_list_past_the_budget_is_refused_unsimulated(tmp_path, monkeypatch):
    """P2's small crate with its law gate list made one that would take step 7 past 2^28 amplitude passes on 20 active
    qubits (its digest made to agree in the manifest): refused at it, by the budget, with the known-answer pair before
    it held and it never simulated."""
    b = hostile_list()
    assert p2_sim.gate_list_cost(b) == p2_sim.Cost(988, 315_097_084, 20, 4)
    assert p2_hold.file_price(p2_sim.gate_list_cost(b)) == 316_398_604 > p2_hold.BUDGET
    c = small_model().write(tmp_path / "small")
    rewrite(c, "bundle/law.gates.json", b)
    doc = json.loads((c / "bundle" / "manifest.json").read_bytes())
    for job in doc["jobs"]:
        for x in job["circuits"]:
            if x["name"] == "law":
                x["gates_sha256"] = sha(b)
    rewrite(c, "bundle/manifest.json", json.dumps(doc, indent=1, sort_keys=True).encode("ascii") + b"\n")
    held = counted(monkeypatch, p2_hold, "hold_circuit")
    r = refusal(7, c)
    assert (r.name, r.where) == ("compile-uncontrolled", "bundle/law.gates.json")
    assert r.detail.endswith("past the 268435456 that qro-exact-hold/1 allows a crate; nothing past it is simulated")
    assert [n.name for n in held] == ["known-answer"]


# -- step 6 -----------------------------------------------------------------------------------------------------------
def test_step_6_counts_the_law_circuit_from_zero_and_refuses_before_simulating_it(twin, monkeypatch):
    """Step 6's count is the question's law circuit's price alone, apart from step 7's. With its budget one short of
    that price, the twin is refused `measure-class` at the question's law circuit, and the circuit's hold is never
    asked; with the budget at the price, it passes."""
    crate, md = twin
    assert p2_steps._step6(Path(crate), md) == LAW_CIRCUIT
    asked = counted(monkeypatch, p2_hold, "law_circuit_problem")
    monkeypatch.setattr(p2_law, "BUDGET", LAW_CIRCUIT - 1)
    r = refusal(6, crate, md)
    assert (r.name, r.where) == ("measure-class", "#question qro:lawCircuit") and asked == []
    assert r.detail == (f"simulating the law circuit would bring this crate's hold of its law circuit to {LAW_CIRCUIT} "
                        f"amplitude passes, past the {LAW_CIRCUIT - 1} that qro-measures/1 allows a crate; nothing "
                        "past it is simulated")
    monkeypatch.setattr(p2_law, "BUDGET", LAW_CIRCUIT)
    assert refusal(6, crate, md) is None and len(asked) == 1


def hostile_law_circuit(layers=600):
    """A 16-qubit circuit in the QASM subset: every qubit spread, then `layers` layers of an ry on each qubit and a cx
    on alternating pairs, so that no two blocks fuse. At its default, 14,134 lines whose price as a law circuit is
    298,698,508 amplitude passes, past 2^28 (about 4,500 blocks of 2^16 passes). The test never simulates it; by the
    rates measured for where its blocks sit, among them the slow placement on axes 0 and 1, that would take about 1.5
    to 2 minutes here (BELIEVED, extrapolated)."""
    lines = [f"ry(0.3) q[{q}];" for q in range(16)]
    lines += [f"cx q[{q}],q[{q + 1}];" for q in range(15)]
    for layer in range(layers):
        lines += [f"ry(0.{layer % 9 + 1}) q[{q}];" for q in range(16)]
        lines += [f"cx q[{q}],q[{q + 1}];" for q in range(layer % 2, 15, 2)]
    return qasm(16, lines)


def test_a_hostile_law_circuit_past_the_budget_is_refused_unsimulated(tmp_path, monkeypatch):
    """v0's question with its law circuit made one whose price is past 2^28 on its 16 qubits: step 6 refuses it by
    the measure set's budget, and the circuit's hold is never asked."""
    hostile = hostile_law_circuit()
    law = p2_law.read(p2_law.law_bytes())
    assert p2_sim.logical_cost(hostile) == p2_sim.Cost(14_134, 294_748_156, 16, 16)
    assert p2_hold.law_circuit_price(hostile, law) == 298_698_508 > p2_law.BUDGET
    m = real_model()
    m.files[SOURCE_PATH] = hostile
    m.source = sha(hostile)
    c = m.write(tmp_path / "real")
    asked = counted(monkeypatch, p2_hold, "law_circuit_problem")
    r = refusal(6, c)
    assert (r.name, r.where, asked) == ("measure-class", "#question qro:lawCircuit", [])
    assert r.detail.endswith("past the 268435456 that qro-measures/1 allows a crate; nothing past it is simulated")


def test_clear_empties_the_prices_too():
    p2_sim.gate_list_cost(data("known-answer.gates.json"))
    assert p2_sim.PRICES.entries
    p2_sim.clear()
    assert not p2_sim.PRICES.entries and all(not m.entries for m in p2_sim.MEMOS)


def test_reading_the_metadata_is_not_counted(twin):
    """The checker has read the metadata whole before step 7, and step 7's own reading of it, its index and its look at
    each Hold, is not counted: the twin's metadata with its three Compiles and three Holds taken out, every other entity
    kept, counts nothing. The count is the walk's alone: each Compile, each entry of its manifest, and each pair."""
    crate, md = twin
    graph = [e for e in md["@graph"] if not {"qro:Compile", "qro:Hold"} & set(p2_steps.canonical_types(e))]
    assert len(md["@graph"]) - len(graph) == 6
    assert p2_steps._step7(Path(crate), {**md, "@graph": graph}) == 0
