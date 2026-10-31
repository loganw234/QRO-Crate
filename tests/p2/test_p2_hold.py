"""The exact hold, `qro-exact-hold/1` (P2's design, item 7): kingston's four morning gate lists held to their logical
circuits at 1e-10; plants that move a probability refused (a), and logical circuits that do not do their role refused
(b); the phase plant, a change no Z-basis probability sees, accepted and pinned as the stated limit; the manifest's
hostile matrix; the claim's three words, from presence; and the question's law circuit held to the law's layouts and
observables."""
import copy
import dataclasses
import hashlib
import json
import math
import re
from fractions import Fraction
from pathlib import Path

import pytest
from p2_builder import SMALL_T1, qasm, small_gates, small_law_bytes, transpile

from qro import p2_hold, p2_law, p2_sim
from qro.p2_hold import HoldError
from qro.p2_sim import SimError

DATA = Path(__file__).parent / "data"
F = Fraction
NAMES = ("known-answer", "law", "coherence-xx", "coherence-yy")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def data(name):
    return (DATA / name).read_bytes()


def v0():
    return p2_law.read(p2_law.law_bytes())


def small():
    return p2_law.read(small_law_bytes())


def named():
    return {c.name: c for c in p2_hold.read_manifest(data("manifest.json"))}


def test_the_rule_and_its_tolerance():
    assert (p2_hold.RULE, p2_hold.TOLERANCE) == ("qro-exact-hold/1", 1e-10)


# -- kingston's morning ------------------------------------------------------------------------------------------------
def test_the_manifest_names_the_four_circuits_the_copies_hold():
    got = named()
    assert sorted(got) == sorted(NAMES)
    for name in NAMES:
        assert got[name].circuit_sha256 == sha(data(f"{name}.qasm"))
        assert got[name].gates_sha256 == sha(data(f"{name}.gates.json"))
    assert [(got[n].role, got[n].basis) for n in NAMES] == [
        ("known-answer", "Z" * 16), ("law", "Z" * 16), ("coherence", "XX" + "Z" * 14), ("coherence", "YY" + "Z" * 14)]


@pytest.mark.parametrize("name", NAMES)
def test_kingstons_morning_gate_lists_hold(name):
    assert p2_hold.hold_circuit(named()[name], data(f"{name}.gates.json"), data(f"{name}.qasm"), v0()) is None


def test_the_real_holds_are_far_inside_the_tolerance():
    for name in NAMES:
        _, g = p2_sim.gate_list_distribution(data(f"{name}.gates.json"))
        _, lg = p2_sim.logical(p2_sim.read_qasm(data(f"{name}.qasm")))
        assert p2_hold.biggest_difference(g, lg) < 1e-14, name


# -- plants that move a probability: (a) -------------------------------------------------------------------------------
def planted(name, edit):
    doc = json.loads(data(f"{name}.gates.json"))
    edit(doc["gates"])
    return json.dumps(doc).encode("ascii")


def at(gates, i, want):
    assert gates[i] == want, (i, gates[i])
    return gates


def last(gates, name, qubit):
    return max(i for i, g in enumerate(gates) if g[0] == name and g[1] == [qubit])


PLANTS_A = {
    "law: gate 303's sx on 47 made an x": ("law", lambda g: at(g, 303, ["sx", [47], [], []]).__setitem__(
        303, ["x", [47], [], []])),
    "law: gate 317's rz on 47 turned a further pi/2": ("law", lambda g: at(g, 317, ["rz", [47], [], [g[317][3][0]]])[
        317][3].__setitem__(0, g[317][3][0] + math.pi / 2)),
    "law: gate 309's cz on 47 and 57 dropped": ("law", lambda g: at(g, 309, ["cz", [47, 57], [], []]).pop(309)),
    "coherence-xx: the h reading qubit 20 lost its sx": ("coherence-xx", lambda g: g.pop(last(g, "sx", 20))),
    "coherence-yy: the h reading qubit 21 lost its sx": ("coherence-yy", lambda g: g.pop(last(g, "sx", 21))),
    "known-answer: its first x dropped": ("known-answer", lambda g: g.pop(next(i for i, x in enumerate(g)
                                                                               if x[0] == "x"))),
}


@pytest.mark.parametrize("plant", sorted(PLANTS_A))
def test_a_plant_that_moves_a_probability_is_refused_a(plant):
    name, edit = PLANTS_A[plant]
    problem = p2_hold.hold_circuit(named()[name], planted(name, edit), data(f"{name}.qasm"), v0())
    assert problem is not None and problem.startswith("(a) its distribution differs from its logical circuit's by ")


def test_a_gate_list_one_angle_off_by_1e_8_is_refused_a_at_the_tolerance_not_looser():
    """(a) holds at 1e-10: the small law circuit's gate list with one ry's rz turned by 1e-8 moves some probability by
    more than 1e-10 and less than 1e-6, and is refused."""
    logical = qasm(4, small_gates(), measured=True)
    doc = json.loads(transpile(logical))
    i = next(i for i, g in enumerate(doc["gates"]) if g[0] == "rz" and g[3] == [SMALL_T1])
    doc["gates"][i][3] = [SMALL_T1 + 1e-8]
    bent = json.dumps(doc).encode("ascii")
    _, g = p2_sim.gate_list_distribution(bent)
    _, lg = p2_sim.logical(p2_sim.read_qasm(logical))
    assert 1e-10 < p2_hold.biggest_difference(g, lg) < 1e-6
    problem = p2_hold.hold_circuit(p2_hold.Named("law", "law", "ZZZZ", sha(logical), None), bent, logical, small())
    assert problem is not None and problem.startswith("(a)")


def test_the_phase_plants_are_accepted_the_stated_limit():
    """P2's stated limit 1 (isa.py's own): an rz on a qubit still in a basis state, or after its last two-qubit gate
    before its measurement, leaves every Z-basis probability alone. The hold accepts it; only the gate list's digest,
    which the manifest names, tells it from kingston's."""
    law = named()["law"]

    def before_43s_measurement(g):
        g.insert(g.index(["measure", [43], [5], []]), ["rz", [43], [], [0.7]])

    def at_the_start(g):
        g.insert(0, ["rz", [20], [], [1.1]])
    for edit in (before_43s_measurement, at_the_start):
        b = planted("law", edit)
        assert sha(b) != law.gates_sha256
        assert p2_hold.hold_circuit(law, b, data("law.qasm"), v0()) is None


# -- roles: (b) --------------------------------------------------------------------------------------------------------
def held(role, basis, logical, law):
    return p2_hold.hold_circuit(p2_hold.Named("c", role, basis, sha(logical), None), transpile(logical), logical, law)


def test_the_small_circuits_hold_and_do_their_roles():
    assert held("law", "ZZZZ", qasm(4, small_gates(), measured=True), small()) is None
    assert held("coherence", "XXZZ", qasm(4, small_gates(), "XXZZ", True), small()) is None
    assert held("coherence", "YYZZ", qasm(4, small_gates(), "YYZZ", True), small()) is None
    assert held("known-answer", "ZZ", qasm(2, ["x q[1];"], measured=True), None) is None


def test_a_known_answer_circuit_with_no_known_answer_is_refused_b():
    problem = held("known-answer", "ZZ", qasm(2, ["h q[0];"], measured=True), None)
    assert problem.startswith("(b) its logical circuit, a known-answer circuit: its most likely outcome has "
                              "probability 0.5")


def test_a_law_circuit_that_lays_another_table_is_refused_b():
    problem = held("law", "ZZZZ", qasm(4, small_gates(t1=0.3), measured=True), small())
    assert problem.startswith("(b) its logical circuit, a law circuit: it does not lay the law")


def test_a_coherence_circuit_against_another_coherence_is_refused_b():
    law = p2_law.read(small_law_bytes(observables={"X0X1": F(1, 2), "Y0Y1": F(4, 5)}))
    problem = held("coherence", "XXZZ", qasm(4, small_gates(), "XXZZ", True), law)
    assert problem.startswith("(b) its logical circuit, a coherence circuit: the parity of qubits 0 and 1 is +0.8")
    assert held("coherence", "YYZZ", qasm(4, small_gates(), "YYZZ", True), law) is None


def test_a_coherence_circuit_of_the_wrong_sign_is_refused_b():
    """The parity's sign is held, not only its size (the first verifier's D4; this kills H20, which compared the two
    sizes): the small XX circuit with a Z on qubit 0 (two sdg) before its basis change reads -4/5, where the law says
    +4/5. The control: against a law that says -4/5, the same circuit holds, and the unflipped one does not."""
    flipped = qasm(4, small_gates() + ["sdg q[0];", "sdg q[0];"], "XXZZ", True)
    problem = held("coherence", "XXZZ", flipped, small())
    assert problem.startswith("(b) its logical circuit, a coherence circuit: the parity of qubits 0 and 1 is "
                              "-0.800000000000, where the law's X0X1 is 4/5")
    negative = p2_law.read(small_law_bytes(observables={"X0X1": F(-4, 5), "Y0Y1": F(4, 5)}))
    assert held("coherence", "XXZZ", flipped, negative) is None
    assert held("coherence", "XXZZ", qasm(4, small_gates(), "XXZZ", True), negative).startswith(
        "(b) its logical circuit, a coherence circuit: the parity of qubits 0 and 1 is +0.8")


@pytest.mark.parametrize("role, basis, law, reason", [
    ("law", "ZZZZ", None, "a law circuit is held to the question's law, and the crate's question names none"),
    ("coherence", "XXZZ", None, "a coherence circuit is held to the question's law"),
    ("coherence", "XYZZ", "small", "does not read exactly two of its 4 qubits out of Z"),
    ("coherence", "XXXZ", "small", "does not read exactly two"),
    ("coherence", "ZZXX", "small", "the law names no observable X2X3"),
    ("law", "ZZZZ", "v0", "the circuit has 4 qubits; the law's tile has 16 sites")])
def test_a_role_that_cannot_be_judged_is_a_hold_error(role, basis, law, reason):
    logical = qasm(4, small_gates(), basis if role == "coherence" and set(basis) <= set("XYZ") else None, True)
    with pytest.raises(HoldError, match=re.escape(reason)):
        held(role, basis, logical, {"small": small(), "v0": v0(), None: None}[law])


def test_a_gate_list_of_another_width_than_its_logical_circuit_is_a_hold_error():
    logical = qasm(3, ["x q[0];"], measured=True)
    with pytest.raises(HoldError, match="the gate list measures 4 clbits; its logical circuit has 3 qubits"):
        p2_hold.hold_circuit(p2_hold.Named("c", "known-answer", "ZZZ", sha(logical), None),
                             transpile(qasm(4, ["x q[0];"], measured=True)), logical, None)


def test_two_circuits_of_the_same_operations_are_each_held_at_their_own_width():
    p2_sim.clear()
    for n in (1, 2, 3):
        logical = qasm(n, ["x q[0];"], measured=True)
        assert held("known-answer", "Z" * n, logical, None) is None


def test_the_role_problems_at_the_tolerance():
    ka = p2_hold.Named("c", "known-answer", "ZZ", "0" * 64, None)
    assert p2_hold.role_problem(ka, [1 - 1e-10, 1e-10, 0, 0], 2, None) is None
    assert p2_hold.role_problem(ka, [1 - 2e-10, 2e-10, 0, 0], 2, None) is not None
    law = small()
    exact = [0.0] * 16
    for Y, w in zip(law.layouts, law.weights):
        exact[sum(1 << q for q in Y)] = w / law.den
    assert p2_hold.law_problem(exact, 4, law) is None
    moved = list(exact)
    moved[0b0101] -= 5e-11
    moved[0b0111] += 5e-11
    assert p2_hold.law_problem(moved, 4, law) is None, "within the tolerance"
    moved[0b0101] -= 1e-10
    moved[0b0111] += 1e-10
    assert "does not lay the law" in p2_hold.law_problem(moved, 4, law)
    with pytest.raises(HoldError):
        p2_hold.law_problem(exact, 5, law)


def test_mass_outside_the_layouts_is_refused_even_where_no_layout_moves_past_the_tolerance():
    """v0's law: 3e-11 taken from each of ten allowed layouts, none of them moved past 1e-10, and put on outcomes of
    four crystals: 3e-10 outside the law's layouts, refused."""
    law = v0()
    exact = {sum(1 << q for q in Y): w / law.den for Y, w in zip(law.layouts, law.weights)}
    dist = [0.0] * (1 << 16)
    for o, p in exact.items():
        dist[o] = p
    allowed = [sum(1 << q for q in Y) for Y, w in zip(law.layouts, law.weights) if w][:10]
    for o in allowed:
        dist[o] -= 3e-11
    dist[0b1111] += 3e-10
    assert p2_hold.law_problem(dist, 16, law).endswith("outside the law's 4368 layouts, against 1e-10")
    assert "its worst layout is off by 3.000e-11" in p2_hold.law_problem(dist, 16, law)


def test_parity_coherence_pair_and_the_biggest_difference():
    assert p2_hold.parity([0.1, 0.2, 0.3, 0.4], 0, 1) == pytest.approx(0.1 - 0.2 - 0.3 + 0.4)
    assert p2_hold.parity([0.1, 0.2, 0.3, 0.4, 0, 0, 0, 0], 0, 2) == pytest.approx(0.1 - 0.2 + 0.3 - 0.4)
    assert p2_hold.parity([0, 0.5, 0, 0, 0.5, 0, 0, 0], 0, 2) == -1.0, "outcomes 001 and 100 disagree on bits 0 and 2"
    assert p2_hold.coherence_pair("XXZZ", 4) == ("X", 0, 1) and p2_hold.coherence_pair("ZYZY", 4) == ("Y", 1, 3)
    for basis, width in (("XYZZ", 4), ("XXX", 3), ("XX", 4), ("ZZZZ", 4), ("XZZZ", 4)):
        with pytest.raises(HoldError):
            p2_hold.coherence_pair(basis, width)
    assert p2_hold.biggest_difference([0.5, 0.5], [0.25, 0.75]) == 0.25
    with pytest.raises(HoldError):
        p2_hold.biggest_difference([1.0], [0.5, 0.5])


def test_parity_reads_a_pair_that_does_not_start_at_qubit_0():
    """Each bit of the pair is read where it is (the first verifier's gap: a parity that shifted its first bit the
    wrong way survived, since every pair tried started at qubit 0). All the mass on 010 reads bits 1 and 2 as 1 and 0,
    which disagree: -1; on 110, which agree: +1. And the pair (1, 3) of four bits against its sum, made here by
    comparing the two bits."""
    for outcome, want in ((0b010, -1.0), (0b110, 1.0), (0b100, -1.0), (0b001, 1.0)):
        dist = [0.0] * 8
        dist[outcome] = 1.0
        assert p2_hold.parity(dist, 1, 2) == want, bin(outcome)
    dist = [(o + 1) / 136 for o in range(16)]
    want = sum(p if (o >> 1) & 1 == (o >> 3) & 1 else -p for o, p in enumerate(dist))
    assert p2_hold.parity(dist, 1, 3) == pytest.approx(want)


# -- the manifest ------------------------------------------------------------------------------------------------------
def circuit(i, key, value):
    def edit(d):
        c = d["jobs"][-1]["circuits"][i]
        if value is KeyError:
            del c[key]
        else:
            c[key] = value
    return edit


HOSTILE_MANIFESTS = {
    "another format": (lambda d: d.update(format="quantum-film/hardware-bundle/v2"), "is not quantum-film/hardware"),
    "no format": (lambda d: d.pop("format"), "is not quantum-film/hardware"),
    "no jobs": (lambda d: d.pop("jobs"), "jobs are a non-empty list of objects"),
    "no job": (lambda d: d.update(jobs=[]), "jobs are a non-empty list of objects"),
    "jobs an object": (lambda d: d.update(jobs={}), "jobs are a non-empty list of objects"),
    "a job a list": (lambda d: d["jobs"].append([]), "jobs are a non-empty list of objects"),
    "no circuits": (lambda d: d["jobs"][0].pop("circuits"), "jobs[0]: its circuits are a non-empty list"),
    "no circuit": (lambda d: d["jobs"][0].update(circuits=[]), "jobs[0]: its circuits are a non-empty list"),
    "a circuit a string": (lambda d: d["jobs"][2]["circuits"].append("x"), "jobs[2]: its circuits are"),
    "a name a number": (circuit(0, "name", 3), "jobs[2].circuits[0]: its name is not text"),
    "an empty name": (circuit(1, "name", ""), "jobs[2].circuits[1]: its name is not text"),
    "no name": (circuit(1, "name", KeyError), "its name is not text"),
    "another role": (circuit(0, "role", "twin"), "the role 'twin' is not one the hold holds"),
    "a role a list": (circuit(0, "role", ["law"]), "the role ['law'] is not one"),
    "no role": (circuit(0, "role", KeyError), "the role None is not one"),
    "an empty basis": (circuit(0, "basis", ""), "its basis is not letters X, Y and Z"),
    "a basis of another letter": (circuit(0, "basis", "WX"), "its basis is not letters"),
    "a lower-case basis": (circuit(0, "basis", "xx"), "its basis is not letters"),
    "a basis a list": (circuit(0, "basis", ["X"]), "its basis is not letters"),
    "no circuit digest": (circuit(0, "circuit_sha256", KeyError), "its circuit_sha256 is not 64 lowercase hex"),
    "an upper-case digest": (lambda d: circuit(0, "circuit_sha256", d["jobs"][2]["circuits"][0][
        "circuit_sha256"].upper())(d), "its circuit_sha256 is not"),
    "a short gate digest": (lambda d: circuit(1, "gates_sha256", d["jobs"][2]["circuits"][1]["gates_sha256"][:63])(d),
                            "its gates_sha256 is not 64 lowercase hex"),
    "a null gate digest": (circuit(1, "gates_sha256", None), "its gates_sha256 is not"),
}


@pytest.mark.parametrize("case", sorted(HOSTILE_MANIFESTS))
def test_a_hostile_manifest_is_a_hold_error_never_a_crash(case):
    edit, reason = HOSTILE_MANIFESTS[case]
    doc = copy.deepcopy(json.loads(data("manifest.json")))
    edit(doc)
    with pytest.raises(HoldError, match=re.escape(reason)):
        p2_hold.read_manifest(json.dumps(doc).encode("ascii"))


@pytest.mark.parametrize("raw, reason", [(b"", "the manifest: not JSON"), (b'{"a": 1, "a": 1}', "twice"),
                                         (b"[]", "is not quantum-film/hardware-bundle/v1"),
                                         (b"\xef\xbb\xbf{}", "the manifest: not JSON")])
def test_bytes_that_are_no_manifest_are_a_hold_error(raw, reason):
    with pytest.raises(HoldError, match=re.escape(reason)):
        p2_hold.read_manifest(raw)


def test_a_circuit_may_name_no_gate_list_and_nothing_else_of_the_manifest_is_read():
    doc = json.loads(data("manifest.json"))
    del doc["jobs"][0]["circuits"][0]["gates_sha256"]
    for key in ("isa", "esp", "commitment", "chain"):
        doc["jobs"][1]["circuits"][0][key] = "anything"
    doc["extra"] = {"not": "read"}
    got = p2_hold.read_manifest(json.dumps(doc).encode("ascii"))
    assert [c.gates_sha256 is None for c in got] == [True, False, False, False]


# -- the claim ---------------------------------------------------------------------------------------------------------
def test_the_claim_is_computed_from_presence():
    ns = list(named().values())
    digests = {n.gates_sha256 for n in ns}
    assert p2_hold.claim(ns, digests) == "holds"
    assert p2_hold.claim(ns, digests - {ns[1].gates_sha256}) == "withheld"
    assert p2_hold.claim(ns, set()) == "withheld"
    assert p2_hold.claim([dataclasses.replace(n, gates_sha256=None) for n in ns], digests) == "unexposed"
    mixed = [ns[0], dataclasses.replace(ns[1], gates_sha256=None)]
    assert p2_hold.claim(mixed, {ns[0].gates_sha256}) == "holds", "a circuit naming no gate list withholds nothing"


# -- the question's law circuit ----------------------------------------------------------------------------------------
def law_with(weights=None, observables=None):
    L, N, den, layouts, w, obs = p2_law.law_parts()
    return p2_law.read(p2_law.write(L, N, den, layouts, weights or w, observables or obs, p2_law.STOCK,
                                    p2_law.SOURCE_TEXT))


def test_the_source_circuit_lays_v0s_law_and_its_coherences():
    assert p2_hold.law_circuit_problem(data("circuit-ed767c01bd4b851d.qasm"), v0()) is None
    assert p2_hold.law_circuit_problem(data("law.qasm"), v0()) is None


def test_a_law_with_one_weight_moved_is_not_what_the_circuit_lays():
    w = list(v0().weights)
    w[w.index(9)] -= 1
    w[w.index(0)] += 1
    problem = p2_hold.law_circuit_problem(data("circuit-ed767c01bd4b851d.qasm"), law_with(weights=tuple(w)))
    assert problem.startswith("it does not lay the law: its worst layout is off by 2.441e-04")


def test_a_law_with_one_coherence_edited_is_not_what_the_circuit_lays():
    law = law_with(observables={"X0X1": F(1, 3), "Y0Y1": F(3, 8)})
    assert p2_hold.law_circuit_problem(data("circuit-ed767c01bd4b851d.qasm"), law) == \
        "its X0X1 is +0.375000000000, where the law says 1/3"
    law = law_with(observables={"X0X1": F(3, 8), "Y0Y1": F(-3, 8)})
    assert p2_hold.law_circuit_problem(data("circuit-ed767c01bd4b851d.qasm"), law) == \
        "its Y0Y1 is +0.375000000000, where the law says -3/8"


def test_a_law_circuit_with_an_angle_changed_or_of_another_width_is_refused():
    text = data("circuit-ed767c01bd4b851d.qasm").decode("ascii")
    angle = re.search(r"ry\(([^)]*)\)", text).group(1)
    bent = text.replace(f"ry({angle})", f"ry({float(angle) + 0.01!r})", 1).encode("ascii")
    assert "does not lay the law" in p2_hold.law_circuit_problem(bent, v0())
    assert p2_hold.law_circuit_problem(qasm(4, small_gates()), v0()) == \
        "the law circuit has 4 qubits; the law's tile has 16 sites"
    assert p2_hold.law_circuit_problem(qasm(4, small_gates()), small()) is None
    with pytest.raises(SimError):
        p2_hold.law_circuit_problem(b"not a circuit\n", v0())


def test_the_law_circuits_memo_is_keyed_by_both_digests_and_cleared():
    p2_sim.clear()
    circuit_bytes = qasm(4, small_gates())
    assert p2_hold.law_circuit_problem(circuit_bytes, small()) is None
    assert len(p2_hold.LAW_CIRCUITS.entries) == 1
    other = p2_law.read(small_law_bytes(observables={"X0X1": F(1, 2), "Y0Y1": F(4, 5)}))
    assert p2_hold.law_circuit_problem(circuit_bytes, other).startswith("its X0X1 is +0.8")
    assert len(p2_hold.LAW_CIRCUITS.entries) == 2
    p2_sim.clear()
    assert not p2_hold.LAW_CIRCUITS.entries
