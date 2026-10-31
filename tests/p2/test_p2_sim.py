"""The exact hold's simulator (P2's design, item 7): its matrices against their definitions; tiny circuits with exact
answers; random gate lists and logical circuits against a plain dense simulator written here, one gate at a time with
no fusion and no light cone; pair expectations; the light cone's bookkeeping; fusion; both readers' hostile matrices
and caps; and the memo, whose answer is the same bytes whatever it held before, and from whose core the coherence
circuits resume."""
import cmath
import copy
import json
import math
import random
import re
from pathlib import Path

import pytest

from qro import p2_hold, p2_sim
from qro.p2_sim import SimError

DATA = Path(__file__).parent / "data"
R2 = 1 / math.sqrt(2)
CLOSE = 1e-12

# -- a plain dense simulator: amplitudes indexed sum of bit q * 2^q, one gate at a time --------------------------------
PLAIN = {"x": ((0, 1), (1, 0)), "sx": ((0.5 + 0.5j, 0.5 - 0.5j), (0.5 - 0.5j, 0.5 + 0.5j)),
         "h": ((R2, R2), (R2, -R2)), "sdg": ((1, 0), (0, -1j)), "X": ((0, 1), (1, 0)), "Y": ((0, -1j), (1j, 0))}


def plain_rz(t):
    return (cmath.exp(-0.5j * t), 0), (0, cmath.exp(0.5j * t))


def plain_ry(t):
    return (math.cos(t / 2), -math.sin(t / 2)), (math.sin(t / 2), math.cos(t / 2))


def plain_one(psi, q, U):
    out = list(psi)
    for i in range(len(psi)):
        bit, base = (i >> q) & 1, i & ~(1 << q)
        out[i] = U[bit][0] * psi[base] + U[bit][1] * psi[base | (1 << q)]
    return out


def plain_run(n, gates):
    """gates: (name, qubits, angle or None)."""
    psi = [0j] * (1 << n)
    psi[0] = 1 + 0j
    for name, qs, t in gates:
        if name == "cz":
            psi = [-v if (i >> qs[0]) & 1 and (i >> qs[1]) & 1 else v for i, v in enumerate(psi)]
        elif name == "cx":
            psi = [psi[i ^ (1 << qs[1])] if (i >> qs[0]) & 1 else psi[i] for i in range(len(psi))]
        else:
            psi = plain_one(psi, qs[0], plain_rz(t) if name == "rz" else plain_ry(t) if name == "ry" else PLAIN[name])
    return psi


def plain_distribution(psi, clbit_qubits):
    out = [0.0] * (1 << len(clbit_qubits))
    for i, v in enumerate(psi):
        out[sum(((i >> q) & 1) << c for c, q in enumerate(clbit_qubits))] += abs(v) ** 2
    return out


def plain_pair(psi, letter, a, b):
    phi = plain_one(plain_one(psi, a, PLAIN[letter]), b, PLAIN[letter])
    return sum(x.conjugate() * y for x, y in zip(psi, phi)).real


def worst(p, q):
    assert len(p) == len(q)
    return max(abs(x - y) for x, y in zip(p, q))


# -- the forms ---------------------------------------------------------------------------------------------------------
def gate_list_doc(n, m, gates, layout=None):
    layout = list(range(m)) if layout is None else layout
    return {"format": p2_sim.GATE_FORMAT, "num_qubits": n, "num_clbits": m, "global_phase": 0.0,
            "layout": {"initial": layout, "final": layout, "routing_permutation": list(range(n))}, "gates": gates}


def dumps(doc):
    return json.dumps(doc).encode("ascii")


def random_gate_list(rng, n):
    gates, plain = [], []
    for _ in range(rng.randint(0, 40)):
        kind = rng.choice(("rz", "sx", "x", "cz", "barrier"))
        if kind == "rz":
            q, t = rng.randrange(n), rng.uniform(-7, 7)
            gates.append(["rz", [q], [], [t]])
            plain.append(("rz", (q,), t))
        elif kind == "cz":
            a, b = rng.sample(range(n), 2)
            gates.append(["cz", [a, b], [], []])
            plain.append(("cz", (a, b), None))
        elif kind == "barrier":
            gates.append(["barrier", sorted(rng.sample(range(n), rng.randint(1, n))), [], []])
        else:
            q = rng.randrange(n)
            gates.append([kind, [q], [], []])
            plain.append((kind, (q,), None))
    measured = rng.sample(range(n), rng.randint(1, n))            # clbit c reads qubit measured[c]
    for c in rng.sample(range(len(measured)), len(measured)):
        gates.append(["measure", [measured[c]], [c], []])
    return dumps(gate_list_doc(n, len(measured), gates, measured)), plain, measured


def qasm(n, lines, creg=False):
    head = ["OPENQASM 2.0;", 'include "qelib1.inc";', f"qreg q[{n}];"] + ([f"creg meas[{n}];"] if creg else [])
    tail = [f"measure q[{j}] -> meas[{j}];" for j in range(n)] if creg else []
    return ("\n".join(head + list(lines) + tail) + "\n").encode("ascii")


def random_logical(rng, n):
    lines, plain = [], []
    for _ in range(rng.randint(0, 40)):
        kind = rng.choice(("x", "h", "sdg", "cx", "ry", "barrier") if n > 1 else ("x", "h", "sdg", "ry", "barrier"))
        if kind == "cx":
            a, b = rng.sample(range(n), 2)
            lines.append(f"cx q[{a}],q[{b}];")
            plain.append(("cx", (a, b), None))
        elif kind == "ry":
            q, t = rng.randrange(n), rng.uniform(-7, 7)
            lines.append(f"ry({t!r}) q[{q}];")
            plain.append(("ry", (q,), t))
        elif kind == "barrier":
            lines.append("barrier " + ",".join(f"q[{q}]" for q in rng.sample(range(n), rng.randint(1, n))) + ";")
        else:
            q = rng.randrange(n)
            lines.append(f"{kind} q[{q}];")
            plain.append((kind, (q,), None))
    return qasm(n, lines, creg=rng.random() < 0.5), plain


# -- the matrices ------------------------------------------------------------------------------------------------------
def close_matrix(a, b, tol=1e-15):
    return all(abs(complex(x) - complex(y)) <= tol for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def test_the_gate_matrices_are_their_definitions():
    for t in (0.0, 0.3, -1.7, math.pi, 12.5):
        assert close_matrix(p2_sim.rz(t), plain_rz(t)) and close_matrix(p2_sim.ry(t), plain_ry(t))
    assert p2_sim.SX == PLAIN["sx"] and p2_sim.X == PLAIN["x"] and p2_sim.SDG == PLAIN["sdg"]
    assert p2_sim.mul(p2_sim.SX, p2_sim.SX) == p2_sim.X, "sx squared is x, exactly"
    assert close_matrix(p2_sim.H, PLAIN["h"]) and close_matrix(p2_sim.mul(p2_sim.H, p2_sim.H), p2_sim.I2)
    assert p2_sim.CZ == tuple(tuple(complex((-1 if i == 3 else 1) * (i == j)) for j in range(4)) for i in range(4))
    for i in range(4):                     # CX: control a, target b, index 2 bit_a + bit_b
        out = i ^ 1 if i >> 1 else i
        assert [p2_sim.CX[r][i] for r in range(4)] == [complex(r == out) for r in range(4)]


def test_kron_and_swapped_index_the_pair_as_stated():
    XI, IX = p2_sim.kron(p2_sim.X, p2_sim.I2), p2_sim.kron(p2_sim.I2, p2_sim.X)
    assert XI[2][0] == 1 and IX[1][0] == 1, "the pair's first qubit is the index's high bit"
    assert p2_sim.swapped(XI) == IX and p2_sim.swapped(p2_sim.swapped(p2_sim.CX)) == p2_sim.CX
    cx_ba = p2_sim.swapped(p2_sim.CX)      # control b, target a
    assert cx_ba[3][1] == 1 and cx_ba[1][1] == 0


def test_monomial_is_tested_exactly():
    assert p2_sim.monomial(p2_sim.X) and p2_sim.monomial(p2_sim.CZ) and p2_sim.monomial(p2_sim.rz(0.4))
    assert not p2_sim.monomial(p2_sim.SX) and not p2_sim.monomial(p2_sim.H)
    almost = ((1 + 0j, 1e-300 + 0j), (0j, 1 + 0j))
    assert not p2_sim.monomial(almost), "a zero is 0.0, nothing smaller"
    assert not p2_sim.monomial(((1 + 0j, 0j), (1 + 0j, 0j))), "a column with two nonzeros"


# -- exact answers -----------------------------------------------------------------------------------------------------
def run_qasm(text_lines, n, creg=False):
    p2_sim.clear()
    c = p2_sim.read_qasm(qasm(n, text_lines, creg))
    return c, p2_sim.logical(c)


def test_tiny_circuits_with_exact_answers():
    _, (st, dist) = run_qasm(["x q[0];"], 1)
    assert list(dist) == [0.0, 1.0]
    _, (st, dist) = run_qasm(["h q[0];", "cx q[0],q[1];"], 2, creg=True)
    assert worst(dist, [0.5, 0, 0, 0.5]) < 1e-15
    assert abs(p2_sim.pair_expectation(st, "X", 0, 1) - 1) < 1e-15
    assert abs(p2_sim.pair_expectation(st, "Y", 0, 1) + 1) < 1e-15
    _, (st, dist) = run_qasm(["ry(1.25) q[1];"], 2)
    assert worst(dist, [math.cos(0.625) ** 2, 0, math.sin(0.625) ** 2, 0]) < 1e-15
    width, dist = p2_sim.gate_list_distribution(dumps(gate_list_doc(3, 2, [
        ["x", [2], [], []], ["measure", [2], [0], []], ["measure", [0], [1], []]], [2, 0])))
    assert width == 2 and list(dist) == [0.0, 1.0, 0.0, 0.0], "clbit 0 reads qubit 2, set; clbit 1 reads qubit 0"


def test_random_gate_lists_hold_against_the_plain_simulator():
    rng = random.Random(8)
    for trial in range(150):
        n = rng.randint(2, 7)
        data, plain, measured = random_gate_list(rng, n)
        want = plain_distribution(plain_run(n, plain), measured)
        width, got = p2_sim.gate_list_distribution(data)
        assert width == len(measured) and worst(got, want) < CLOSE, trial


def test_random_logical_circuits_and_their_pair_expectations_hold_against_the_plain_simulator():
    rng = random.Random(9)
    for trial in range(150):
        n = rng.randint(1, 6)
        data, plain = random_logical(rng, n)
        c = p2_sim.read_qasm(data)
        st, got = p2_sim.logical(c)
        psi = plain_run(n, plain)
        assert worst(got, plain_distribution(psi, list(range(n)))) < CLOSE, trial
        for a in range(n):
            for b in range(n):
                if a != b:
                    for letter in "XY":
                        assert abs(p2_sim.pair_expectation(st, letter, a, b) - plain_pair(psi, letter, a, b)) < CLOSE


# -- the light cone and fusion -----------------------------------------------------------------------------------------
def test_the_light_cone_holds_classical_bits_until_a_block_spreads_the_state():
    _, (st, dist) = run_qasm(["x q[0];", "cx q[0],q[1];"], 4)
    assert st.axes == {} and st.psi == [1 + 0j] and st.bits == {0: 1, 1: 1}
    assert list(dist) == [float(o == 3) for o in range(16)]
    _, (st, dist) = run_qasm(["x q[0];", "cx q[0],q[1];", "h q[2];", "cx q[2],q[3];"], 4)
    assert st.axes == {2: 0, 3: 1} and len(st.psi) == 4 and st.bits == {0: 1, 1: 1}
    assert worst(dist, [0.5 * (o in (3, 15)) for o in range(16)]) < 1e-15
    assert p2_sim.pair_expectation(st, "X", 0, 2) == 0.0, "a classical bit flips to an orthogonal state"
    assert abs(p2_sim.pair_expectation(st, "X", 2, 3) - 1) < 1e-15
    _, (st, _) = run_qasm(["x q[0];", "cx q[0],q[1];", "cx q[1],q[2];", "ry(0.5) q[2];"], 3)
    assert st.axes == {1: 0, 2: 1} and st.bits == {0: 1}
    assert worst(st.psi, [0, -math.sin(0.25), 0, math.cos(0.25)]) < 1e-15, "a classical 1 enters as its axis's 1"
    _, (st, _) = run_qasm(["x q[0];", "cx q[0],q[1];", "cx q[1],q[2];", "h q[2];"], 3)
    assert st.axes == {2: 0} and st.bits == {0: 1, 1: 1}, "the core is classical; the tail's h spreads q[2] alone"
    assert worst(st.psi, [R2, -R2]) < 1e-15


def kinds(blocks):
    return [b[:2] if b[0] == "1" else b[:3] for b in blocks]


def test_fusion_merges_runs_and_keeps_pending_blocks_on_disjoint_qubits():
    X, SX, CZ, I2, mul, kron = p2_sim.X, p2_sim.SX, p2_sim.CZ, p2_sim.I2, p2_sim.mul, p2_sim.kron
    blocks = p2_sim.fuse([("1q", 0, X), ("1q", 0, SX), ("1q", 0, X)])
    assert kinds(blocks) == [("1", 0)] and close_matrix(blocks[0][2], mul(X, mul(SX, X)))
    blocks = p2_sim.fuse([("2q", 0, 1, CZ), ("1q", 0, SX), ("2q", 1, 0, CZ), ("1q", 2, X)])
    assert kinds(blocks) == [("1", 2), ("2", 0, 1)], "a pair's run is one 4x4, whichever way round its gates name it"
    assert close_matrix(blocks[1][3], mul(p2_sim.swapped(CZ), mul(kron(SX, I2), CZ)))
    blocks = p2_sim.fuse([("1q", 1, SX), ("2q", 0, 1, CZ), ("2q", 1, 2, CZ), ("1q", 0, X)])
    assert kinds(blocks) == [("2", 0, 1), ("1", 0), ("2", 1, 2)]
    assert close_matrix(blocks[0][3], mul(CZ, kron(I2, SX))), "a single-qubit run joins the next pair on its qubit"
    # a pair started on other qubits closes no pending pair (the second verifier's note 3: `fuse` closing the pairs
    # that do not hold the new pair's qubits gave the same distributions, so only the blocks tell it)
    blocks = p2_sim.fuse([("2q", 0, 1, CZ), ("2q", 2, 3, CZ), ("1q", 0, SX), ("2q", 0, 1, CZ)])
    assert kinds(blocks) == [("2", 0, 1), ("2", 2, 3)], "the pair on 0 and 1 stays open while 2 and 3 start"
    assert close_matrix(blocks[0][3], mul(CZ, mul(kron(SX, I2), CZ)))


def test_fused_and_unfused_runs_agree():
    rng = random.Random(10)
    for _ in range(40):
        n = rng.randint(2, 6)
        _, plain, measured = random_gate_list(rng, n)
        ops = [("2q", qs[0], qs[1], p2_sim.CZ) if name == "cz" else
               ("1q", qs[0], p2_sim.rz(t) if name == "rz" else {"sx": p2_sim.SX, "x": p2_sim.X}[name])
               for name, qs, t in plain]
        fused = p2_sim.distribution(p2_sim.simulate(p2_sim.fuse(ops)), tuple(measured))
        one_by_one = p2_sim.distribution(
            p2_sim.simulate([("1",) + op[1:] if op[0] == "1q" else ("2",) + op[1:] for op in ops]), tuple(measured))
        assert worst(fused, one_by_one) < CLOSE


# -- the readers' hostile matrices -------------------------------------------------------------------------------------
def base_gate_list():
    return gate_list_doc(2, 2, [["sx", [0], [], []], ["rz", [0], [], [0.5]], ["cz", [0, 1], [], []],
                                ["barrier", [0, 1], [], []], ["measure", [0], [0], []], ["measure", [1], [1], []]])


def gate(i, value):
    def edit(doc):
        doc["gates"][i] = value
    return edit


def put(path, value):
    def edit(doc):
        target = doc
        for k in path[:-1]:
            target = target[k]
        if value is KeyError:
            del target[path[-1]]
        else:
            target[path[-1]] = value
    return edit


HOSTILE_GATE_LISTS = {
    "a key missing": (put(["layout"], KeyError), "carries exactly"),
    "a key more": (put(["isa"], {}), "carries exactly"),
    "another format": (put(["format"], "quantum-film/isa-gates/v2"), "format"),
    "no qubits": (put(["num_qubits"], 0), "positive whole"),
    "a true width": (put(["num_qubits"], True), "positive whole"),
    "a float width": (put(["num_clbits"], 2.0), "positive whole"),
    "an integer phase": (put(["global_phase"], 0), "global_phase"),
    "a text phase": (put(["global_phase"], "0.0"), "global_phase"),
    "a layout key missing": (put(["layout", "final"], KeyError), "layout is"),
    "a layout of floats": (put(["layout", "initial"], [0.0, 1.0]), "layout is"),
    "a short layout": (put(["layout", "initial"], [0]), "layout initial names"),
    "a layout twice": (put(["layout", "final"], [1, 1]), "layout final names"),
    "a layout outside": (put(["layout", "initial"], [0, 2]), "layout initial names"),
    "gates an object": (put(["gates"], {}), "gates is a list"),
    "a gate of three": (gate(0, ["sx", [0], []]), "not [name"),
    "a gate's name a number": (gate(0, [1, [0], [], []]), "not [name"),
    "a true qubit": (gate(0, ["sx", [True], [], []]), "not [name"),
    "qubits not a list": (gate(0, ["sx", 0, [], []]), "not [name"),
    "params an object": (gate(0, ["sx", [0], [], {}]), "not [name"),
    "an h": (gate(0, ["h", [0], [], []]), "is not one of the gates"),
    "a qubit outside": (gate(0, ["sx", [2], [], []]), "outside the circuit"),
    "a negative qubit": (gate(0, ["sx", [-1], [], []]), "outside the circuit"),
    "a clbit outside": (gate(4, ["measure", [0], [2], []]), "outside the circuit"),
    "an integer angle": (gate(1, ["rz", [0], [], [1]]), "not a finite float"),
    "a true angle": (gate(1, ["rz", [0], [], [True]]), "not a finite float"),
    "a barrier with a clbit": (gate(3, ["barrier", [0], [0], []]), "a barrier has"),
    "a barrier with a parameter": (gate(3, ["barrier", [0], [], [0.0]]), "a barrier has"),
    "a barrier twice on a qubit": (gate(3, ["barrier", [0, 0], [], []]), "a barrier has"),
    "an rz without an angle": (gate(1, ["rz", [0], [], []]), "rz takes"),
    "an sx with an angle": (gate(0, ["sx", [0], [], [0.5]]), "sx takes"),
    "a cz on one qubit twice": (gate(2, ["cz", [0, 0], [], []]), "cz takes"),
    "a cz on one qubit": (gate(2, ["cz", [0], [], []]), "cz takes"),
    "a measure without a clbit": (gate(4, ["measure", [0], [], []]), "measure takes"),
    "an x with a clbit": (gate(0, ["x", [0], [0], []]), "x takes"),
    "a gate after its qubit's measurement": (lambda d: d["gates"].append(["x", [0], [], []]), "after its measurement"),
    "a clbit measured twice": (gate(5, ["measure", [1], [0], []]), "measured twice"),
    "a clbit never measured": (lambda d: d["gates"].pop(), "never measured"),
}


@pytest.mark.parametrize("case", sorted(HOSTILE_GATE_LISTS))
def test_a_hostile_gate_list_is_a_sim_error_never_a_crash(case):
    edit, reason = HOSTILE_GATE_LISTS[case]
    doc = copy.deepcopy(base_gate_list())
    edit(doc)
    with pytest.raises(SimError, match=re.escape(reason)):
        p2_sim.read_gate_list(dumps(doc))


def test_the_hostile_gate_lists_control_is_read():
    g = p2_sim.read_gate_list(dumps(base_gate_list()))
    assert (g.num_qubits, g.num_clbits, g.clbits, len(g.ops)) == (2, 2, (0, 1), 3)


NOT_A_GATE_LIST = {"empty": (b"", "the gate list: not JSON"), "words": (b"not json", "the gate list: not JSON"),
                   "a key twice": (b'{"a": 1, "a": 2}', "twice"), "a nan": (b"[1, NaN]", "has no value"),
                   "utf-16": (b"\xff\xfe", "not UTF-8"), "deep": (b"[" * 100000, "nested deeper"),
                   "an overflow": (b"[1e999]", "past binary64"), "a long integer": (b"[" + b"9" * 30 + b"]",
                                                                                  "an integer past"),
                   "a list": (b"[]", "carries exactly"), "a string": (b'"x"', "carries exactly")}


@pytest.mark.parametrize("case", sorted(NOT_A_GATE_LIST))
def test_bytes_that_are_no_gate_list_object_are_a_sim_error(case):
    data, reason = NOT_A_GATE_LIST[case]
    with pytest.raises(SimError, match=re.escape(reason)):
        p2_sim.read_gate_list(data)


def test_the_gate_lists_caps(monkeypatch):
    assert (p2_sim.MAX_GATES, p2_sim.MAX_ACTIVE, p2_sim.MAX_QUBITS) == (100_000, 20, 20), "the design's caps"
    wide = gate_list_doc(21, 1, [["x", [q], [], []] for q in range(21)] + [["measure", [0], [0], []]])
    with pytest.raises(SimError, match="21 active qubits"):
        p2_sim.read_gate_list(dumps(wide))
    wide["gates"] = wide["gates"][:20] + wide["gates"][21:]
    p2_sim.read_gate_list(dumps(wide))                                   # 20 active: read
    monkeypatch.setattr(p2_sim, "MAX_GATES", 5)
    with pytest.raises(SimError, match="6 gates"):
        p2_sim.read_gate_list(dumps(base_gate_list()))


HOSTILE_QASM = {
    "not ascii": ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nx q[0];\n'.replace("x", "é"), "not ASCII"),
    "crlf": ('OPENQASM 2.0;\r\ninclude "qelib1.inc";\r\nqreg q[2];\r\n', "end in LF"),
    "no final lf": ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];', "end in LF"),
    "openqasm 3": ('OPENQASM 3.0;\ninclude "qelib1.inc";\nqreg q[2];\n', "does not open"),
    "no include": ("OPENQASM 2.0;\nqreg q[2];\n", "does not open"),
    "no qreg": ('OPENQASM 2.0;\ninclude "qelib1.inc";\n', "does not open"),
    "a leading zero": ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[02];\n', "does not open"),
    "another register": ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg r[2];\n', "does not open"),
    "no qubits": ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[0];\n', "1 to 20"),
    "21 qubits": ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[21];\n', "1 to 20"),
    "another creg": ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n', "the only creg"),
    "a creg of another width": ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg meas[3];\n', "the only creg"),
}
LINES = {
    "a blank line": ("", "not in the subset"), "a comment": ("// x", "not in the subset"),
    "a y": ("y q[0];", "not in the subset"), "two spaces": ("x  q[0];", "not in the subset"),
    "a trailing space": ("x q[0]; ", "not in the subset"), "a qubit outside": ("x q[2];", "outside q[2]"),
    "a cx on one qubit": ("cx q[0],q[0];", "cx on two distinct"),
    "a cx outside": ("cx q[0],q[5];", "cx on two distinct"),
    "a cx whose control is outside": ("cx q[5],q[0];", "cx on two distinct"),
    "a cx with a space": ("cx q[0], q[1];", "not in the subset"), "a symbol": ("ry(pi/2) q[0];", "not in the subset"),
    "a plus": ("ry(+0.5) q[0];", "not in the subset"), "no leading digit": ("ry(.5) q[0];", "not in the subset"),
    "no fraction digit": ("ry(1.) q[0];", "not in the subset"), "a capital e": ("ry(1E5) q[0];", "not in the subset"),
    "an infinite angle": ("ry(1e999) q[0];", "finite angle"), "an ry outside": ("ry(0.5) q[3];", "finite angle"),
    "a barrier twice on a qubit": ("barrier q[0],q[0];", "a barrier on distinct"),
    "a barrier outside": ("barrier q[0],q[4];", "a barrier on distinct"),
    "a barrier with a space": ("barrier q[0], q[1];", "not in the subset"),
    "a measurement without a creg": ("measure q[0] -> meas[0];", "declares no creg"),
}
for _name, (_line, _reason) in LINES.items():
    HOSTILE_QASM[_name] = (f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nh q[0];\n{_line}\n', _reason)
_MEASURED = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg meas[2];\nh q[0];\n'
HOSTILE_QASM.update({
    "measures out of order": (_MEASURED + "measure q[1] -> meas[1];\nmeasure q[0] -> meas[0];\n", "ends with measure"),
    "a measure missing": (_MEASURED + "measure q[0] -> meas[0];\n", "ends with measure"),
    "a gate after the measures": (_MEASURED + "measure q[0] -> meas[0];\nmeasure q[1] -> meas[1];\nx q[0];\n",
                                  "ends with measure"),
    "a crossed measure": (_MEASURED + "measure q[0] -> meas[1];\nmeasure q[1] -> meas[0];\n", "ends with measure"),
    "a creg and no measure": (_MEASURED, "ends with measure"),
})


@pytest.mark.parametrize("case", sorted(HOSTILE_QASM))
def test_a_hostile_logical_circuit_is_a_sim_error_never_a_crash(case):
    text, reason = HOSTILE_QASM[case]
    with pytest.raises(SimError, match=re.escape(reason)):
        p2_sim.read_qasm(text.encode("utf-8"))


def test_a_refusal_names_the_line_it_found_in_the_circuit():
    text = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nh q[0];\nx q[2];\n'
    with pytest.raises(SimError, match=re.escape("line 5: qubit 2 is outside q[2]")):
        p2_sim.read_qasm(text.encode("ascii"))


def test_the_logical_readers_control_and_cap(monkeypatch):
    c = p2_sim.read_qasm(qasm(2, ["h q[0];", "ry(-0.0) q[1];", "barrier q[1],q[0];", "cx q[0],q[1];"], creg=True))
    assert c == p2_sim.Circuit(2, (("h", 0), ("ry", 1, -0.0), ("cx", 0, 1)), True)
    assert p2_sim.read_qasm(qasm(1, [])) == p2_sim.Circuit(1, (), False)
    monkeypatch.setattr(p2_sim, "MAX_GATES", 2)
    # the cap counts gates, not lines (the second verifier's note 5): the cap's gates exactly, with barrier lines among
    # them and after the last, read; one gate more is refused at its own line
    two = p2_sim.read_qasm(qasm(2, ["h q[0];", "barrier q[0];", "h q[1];", "barrier q[0],q[1];"], creg=True))
    assert two.ops == (("h", 0), ("h", 1))
    with pytest.raises(SimError, match=re.escape("line 6: more than 2 gates")):
        p2_sim.read_qasm(qasm(2, ["h q[0];", "h q[1];", "x q[0];"]))
    # barrier lines have a cap of their own, of the same number, so a line's cost is bounded by its 20 qubits at most
    p2_sim.read_qasm(qasm(2, ["barrier q[0];", "barrier q[1];"]))
    with pytest.raises(SimError, match=re.escape("line 6: more than 2 barrier lines")):
        p2_sim.read_qasm(qasm(2, ["barrier q[0];", "barrier q[1];", "barrier q[0],q[1];"]))


def test_the_logical_readers_cap_at_its_own_size():
    """Exactly 100,000 gates and then a barrier line read (the second verifier found them refused); the 100,001st gate
    is refused at its own line."""
    gates = ["x q[0];"] * 100_000
    assert len(p2_sim.read_qasm(qasm(1, gates + ["barrier q[0];"], creg=True)).ops) == 100_000
    with pytest.raises(SimError, match=re.escape("line 100004: more than 100000 gates")):
        p2_sim.read_qasm(qasm(1, gates + ["x q[0];", "barrier q[0];"]))


def test_v0s_circuits_read_and_share_one_core():
    read = {n: p2_sim.read_qasm((DATA / f"{n}.qasm").read_bytes())
            for n in ("law", "coherence-xx", "coherence-yy", "known-answer", "circuit-ed767c01bd4b851d")}
    source = read["circuit-ed767c01bd4b851d"]
    assert not source.measured and all(read[n].measured for n in ("law", "coherence-xx", "coherence-yy"))
    assert read["law"].ops == source.ops and len(source.ops) == 311 and source.n == 16
    core = p2_sim.split(source.ops)[0]
    assert core == source.ops[:-1], "the source circuit ends in h q[10]"
    assert p2_sim.split(read["coherence-xx"].ops) == (core, (("h", 10), ("h", 0), ("h", 1)))
    assert p2_sim.split(read["coherence-yy"].ops)[0] == core
    assert {op[0] for op in p2_sim.split(read["coherence-yy"].ops)[1]} == {"h", "sdg"}


# -- the memo ----------------------------------------------------------------------------------------------------------
def test_a_memo_is_an_lru_of_its_size():
    m = p2_sim.Memo(3)
    for k in "abc":
        m.put(k, k.upper())
    assert m.get("a") == "A"
    m.put("d", "D")
    assert list(m.entries) == ["c", "a", "d"] and m.get("b") is None
    big = p2_sim.Memo()
    for k in range(65):
        big.put(k, k)
    assert len(big.entries) == 64 and big.get(0) is None and big.get(64) == 64


def test_the_memo_answers_by_the_bytes_and_clear_empties_all_six():
    data = (DATA / "known-answer.gates.json").read_bytes()
    p2_sim.clear()
    first = p2_sim.gate_list_distribution(data)
    assert p2_sim.gate_list_distribution(bytes(data)) is first
    assert max(first[1]) == 1.0
    assert len(p2_sim.MEMOS) == 6 and {id(m) for m in p2_sim.MEMOS} >= {id(p2_hold.COMPARED), id(p2_hold.JUDGED),
                                                                        id(p2_hold.LAW_CIRCUITS)}
    for i, memo in enumerate(p2_sim.MEMOS):
        memo.put(("planted", i), "x")
    p2_sim.clear()
    assert all(not memo.entries for memo in p2_sim.MEMOS)
    again = p2_sim.gate_list_distribution(data)
    assert again is not first and again == first


def test_the_logical_memo_keys_on_the_width_too():
    p2_sim.clear()
    narrow = p2_sim.read_qasm(qasm(2, ["x q[0];"]))
    wide = p2_sim.read_qasm(qasm(3, ["x q[0];"]))
    assert narrow.ops == wide.ops
    assert len(p2_sim.logical(narrow)[1]) == 4 and len(p2_sim.logical(wide)[1]) == 8


def test_split_takes_the_trailing_h_and_sdg():
    ops = (("x", 0), ("h", 1), ("cx", 0, 1), ("sdg", 0), ("h", 0))
    assert p2_sim.split(ops) == (ops[:3], ops[3:])
    assert p2_sim.split(ops[:3]) == (ops[:3], ())
    assert p2_sim.split((("h", 0), ("sdg", 0))) == ((), (("h", 0), ("sdg", 0)))
    assert p2_sim.split(()) == ((), ())


@pytest.mark.parametrize("name", ["coherence-xx", "coherence-yy"])
def test_a_circuit_is_the_same_bytes_whether_or_not_its_core_was_memoised(name):
    law = p2_sim.read_qasm((DATA / "law.qasm").read_bytes())
    c = p2_sim.read_qasm((DATA / f"{name}.qasm").read_bytes())
    p2_sim.clear()
    _, scratch = p2_sim.logical(c)
    p2_sim.clear()
    p2_sim.logical(law)
    assert p2_sim.CORES.get(p2_sim.split(law.ops)[0]) is not None
    _, resumed = p2_sim.logical(c)
    assert resumed.tobytes() == scratch.tobytes()
    core, tail = p2_sim.split(c.ops)
    by_hand = p2_sim.simulate(p2_sim.fuse([p2_sim._matrix(op) for op in tail]),
                              p2_sim.simulate(p2_sim.fuse([p2_sim._matrix(op) for op in core])))
    assert p2_sim.distribution(by_hand, tuple(range(c.n))).tobytes() == scratch.tobytes()


def test_the_coherence_circuits_resume_from_the_law_circuits_memoised_core(monkeypatch):
    """What the page claims of the memos (the second verifier's note 3), seen in the simulator's runs: the law circuit
    runs its core from |0...0> and its tail from the core's State; each of v0's coherence circuits then runs its tail
    alone, from that same State, which the core memo holds; and each circuit asked for again runs nothing, the logical
    memo's answer."""
    law, xx, yy = (p2_sim.read_qasm((DATA / f"{n}.qasm").read_bytes()) for n in ("law", "coherence-xx", "coherence-yy"))
    starts, simulate = [], p2_sim.simulate

    def counted(blocks, start=None):
        starts.append(start)
        return simulate(blocks, start)
    monkeypatch.setattr(p2_sim, "simulate", counted)
    p2_sim.clear()
    p2_sim.logical(law)
    core = p2_sim.CORES.get(p2_sim.split(law.ops)[0])
    assert len(starts) == 2 and starts[0] is None and starts[1] is core
    for c in (xx, yy):
        starts.clear()
        p2_sim.logical(c)
        assert len(starts) == 1 and starts[0] is core, "its tail alone, from the law circuit's core"
    starts.clear()
    for c in (law, xx, yy):
        p2_sim.logical(c)
    assert starts == [], "asked again, each circuit is the logical memo's answer"
