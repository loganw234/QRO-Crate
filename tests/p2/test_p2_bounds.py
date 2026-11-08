"""Bounds where P2's code is right and, until P2.2, no test pinned them (P2.1's third verifier, N1 to N4), each held at
its edge, with the value just past it refused where the code refuses one:
  N1  a gate list of exactly 100,000 gates is read, and one of 100,001 refused;
  N2  in a logical circuit of n qubits, a cx (its control or its target), an ry and a barrier on qubit n are refused,
      and on qubit n - 1 read;
  N3  a gate list of one qubit and one clbit is read, and one of none refused;
  N4  in p2_law: one crystal, and as many as the tile's sites; a denominator of 1; an observable at -1 and at 1, and
      just past them; the classes' memo, at most 64 laws, the oldest dropped; a nearest-neighbour pair never
      co-occupied, which counts 0; and the determinant's pivot swap, with the law's own self-check."""
import itertools
import json
import random
import re
from fractions import Fraction

import pytest
from p2_builder import small_law_bytes

from qro import p2_law, p2_sim
from qro.p2_law import LawError
from qro.p2_sim import SimError

F = Fraction


def gate_list(n, m, gates):
    return json.dumps({"format": "quantum-film/isa-gates/v1", "num_qubits": n, "num_clbits": m, "global_phase": 0.0,
                       "layout": {"initial": list(range(m)), "final": list(range(m)),
                                  "routing_permutation": list(range(n))},
                       "gates": gates}).encode("ascii")


# -- N1 and N3: the gate list ------------------------------------------------------------------------------------------
def test_n1_a_gate_list_of_exactly_the_cap_is_read_and_one_more_gate_is_refused():
    assert p2_sim.MAX_GATES == 100_000
    gates = [["x", [0], [], []]] * (p2_sim.MAX_GATES - 1) + [["measure", [0], [0], []]]
    g = p2_sim.read_gate_list(gate_list(1, 1, gates))
    assert len(g.ops) == p2_sim.MAX_GATES - 1 and g.clbits == (0,)
    with pytest.raises(SimError, match="100001 gates; the exact hold reads at most 100000"):
        p2_sim.read_gate_list(gate_list(1, 1, [["x", [0], [], []]] + gates))


def test_n3_a_gate_list_of_one_qubit_and_one_clbit_is_read_and_one_of_none_refused():
    one = gate_list(1, 1, [["x", [0], [], []], ["measure", [0], [0], []]])
    g = p2_sim.read_gate_list(one)
    assert (g.num_qubits, g.num_clbits, g.clbits, len(g.ops)) == (1, 1, (0,), 1)
    p2_sim.clear()
    assert list(p2_sim.gate_list_distribution(one)[1]) == [0.0, 1.0]
    for n, m in ((0, 1), (1, 0), (0, 0)):
        with pytest.raises(SimError, match="num_qubits and num_clbits are positive whole numbers"):
            p2_sim.read_gate_list(gate_list(n, m, [["measure", [0], [0], []]]))


# -- N2: the logical circuit's qubit indices at the width ------------------------------------------------------------
def circuit(line, n=2):
    return f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[{n}];\n{line}\n'.encode("ascii")


@pytest.mark.parametrize("edge, inside, says", [
    ("cx q[0],q[2];", "cx q[0],q[1];", "line 4: cx on two distinct qubits of q[2]"),
    ("cx q[2],q[0];", "cx q[1],q[0];", "line 4: cx on two distinct qubits of q[2]"),
    ("ry(0.5) q[2];", "ry(0.5) q[1];", "line 4: ry of a finite angle on a qubit of q[2]"),
    ("barrier q[0],q[2];", "barrier q[0],q[1];", "line 4: a barrier on distinct qubits of q[2]"),
    ("barrier q[2];", "barrier q[1];", "line 4: a barrier on distinct qubits of q[2]"),
], ids=["a cx's target", "a cx's control", "an ry", "a barrier's last qubit", "a barrier of one qubit"])
def test_n2_a_qubit_index_equal_to_the_width_is_refused_and_one_less_is_read(edge, inside, says):
    assert p2_sim.read_qasm(circuit(inside)).n == 2
    with pytest.raises(SimError, match=re.escape(says)):
        p2_sim.read_qasm(circuit(edge))


# -- N4: the law -------------------------------------------------------------------------------------------------------
def law_of(L, N, den, weights, observables=()):
    layouts = tuple(itertools.combinations(range(L * L), N))
    return p2_law.write(L, N, den, layouts, weights, dict(observables), "bounds", "a law at an edge of the reader")


def test_n4_one_crystal_and_as_many_as_the_sites_are_read_and_none_or_one_more_refused():
    one = p2_law.read(law_of(2, 1, 4, (1, 1, 1, 1)))
    assert (one.N, one.D, one.layouts) == (1, 4, ((0,), (1,), (2,), (3,)))
    full = p2_law.read(law_of(2, 4, 1, (1,)))
    assert (full.N, full.D) == (4, 1)
    for N in (0, 5):
        with pytest.raises(LawError, match="crystals is a whole number from 1 to 4"):
            law_of(2, N, 1, (1,) + (0,) * (len(list(itertools.combinations(range(4), N))) - 1))


def test_n4_a_denominator_of_one_is_read_and_of_none_refused():
    assert p2_law.read(law_of(2, 2, 1, (1, 0, 0, 0, 0, 0))).den == 1
    with pytest.raises(LawError, match="the denominator is a positive whole number"):
        law_of(2, 2, 0, (0, 0, 0, 0, 0, 0))


def test_n4_an_observable_at_minus_one_and_at_one_is_read_and_just_past_them_refused():
    law = p2_law.read(law_of(2, 2, 10, (0, 4, 4, 1, 1, 0), {"X0X1": F(1), "Y0Y1": F(-1)}))
    assert law.observables == {"X0X1": 1, "Y0Y1": -1}
    for value in (F(1000001, 1000000), F(-1000001, 1000000)):
        with pytest.raises(LawError, match=r"outside \[-1, 1\]"):
            law_of(2, 2, 10, (0, 4, 4, 1, 1, 0), {"X0X1": value})


def test_n4_the_classes_memo_holds_at_most_64_laws_and_drops_the_oldest():
    p2_law.clear()
    try:
        laws = [p2_law.read(small_law_bytes(stock=f"bound-{i}")) for i in range(65)]
        assert len({law.digest for law in laws}) == 65
        for law in laws:
            p2_law.classes(law)
        assert len(p2_law._CLASSES) == 64
        assert laws[0].digest not in p2_law._CLASSES
        assert all(law.digest in p2_law._CLASSES for law in laws[1:])
    finally:
        p2_law.clear()


def test_n4_a_nearest_neighbour_pair_never_co_occupied_counts_zero():
    """The small law never puts crystals on both sites of the neighbouring pairs (0, 1) and (2, 3) of its 2 x 2 tile;
    each counts 0 in the mean over the four pairs, and the other two count 1: the NN correlation is 1/2. The uniform
    twin co-occupies every pair, each 2/3 (the control: the default is reached only where a pair is never
    co-occupied)."""
    law = p2_law.read(small_law_bytes())
    assert law.nn_pairs == ((0, 1), (0, 2), (1, 3), (2, 3))
    assert [law.weight[p] for p in law.nn_pairs] == [0, 4, 1, 0]
    assert p2_law.expected(p2_law.model_of("law", law), law)["nn-pair-correlation"] == F(1, 2)
    assert p2_law.expected(p2_law.model_of("uniform", law), law)["nn-pair-correlation"] == F(2, 3)


def leibniz(m):
    """The determinant by the permutation expansion: independent of Bareiss's elimination and its pivot swap."""
    n, total = len(m), 0
    for perm in itertools.permutations(range(n)):
        sign = (-1) ** sum(1 for i in range(n) for j in range(i + 1, n) if perm[i] > perm[j])
        prod = 1
        for i in range(n):
            prod *= m[i][perm[i]]
        total += sign * prod
    return total


@pytest.mark.parametrize("rows, det", [
    ([[0, 1], [1, 0]], -1),
    ([[0, 2, 1], [1, 0, 0], [0, 0, 3]], -6),
    ([[1, 0, 0], [0, 0, 1], [0, 1, 0]], -1),
    ([[0, 1], [0, 2]], 0),
    ([[2, 1], [1, 1]], 1),
], ids=["a swap at the first pivot", "a swap and a scale", "a swap at the second pivot", "no row to swap",
        "no swap"])
def test_n4_the_determinant_swaps_a_zero_pivot(rows, det):
    assert p2_law._det(rows) == det == leibniz(rows)


def test_n4_the_determinant_agrees_with_the_permutation_expansion_on_sparse_matrices():
    """No minor of v0's kernel has a zero leading pivot, so the swap is held here, on 300 sparse integer matrices, a
    third of them with a zero first pivot."""
    rng = random.Random(22)
    zero_first = 0
    for _ in range(300):
        n = rng.randint(2, 5)
        m = [[rng.choice((0, 0, 0, rng.randint(-4, 4))) for _ in range(n)] for _ in range(n)]
        zero_first += m[0][0] == 0
        assert p2_law._det(m) == leibniz(m), m
    assert zero_first > 100


def test_n4_the_laws_own_self_check_refuses_a_kernel_whose_minors_are_not_a_projections(monkeypatch):
    """law_parts holds the minors to the kernel's own sum, 16^5, and to no negative minor: a kernel of 5 on its
    diagonal and nothing else gives every minor 5^5, whose sum is not 16^5."""
    monkeypatch.setattr(p2_law, "kernel", lambda: tuple(tuple(5 if i == j else 0 for j in range(16)) for i in range(16)))
    with pytest.raises(ArithmeticError, match="the minors are not a projection kernel's"):
        p2_law.law_parts()
