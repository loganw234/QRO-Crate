"""The law: pauli-4x4's table from its integer kernel, the law file's one spelling and its reader's refusals, and what
the measure set needs of a law (P2's design, items 2 and 8; the lead's E2 (6))."""
import hashlib
import itertools
import json
from fractions import Fraction

import pytest
from p2_builder import SMALL_LAYOUTS, SMALL_OBSERVABLES, SMALL_WEIGHTS, small_law_bytes

from qro import canonical, p2_law
from qro.p2_law import LawError

# The law file pauli-4x4's kernel makes, pinned: MEASURED at the build (P2.md, the build's entry).
LAW_SHA256 = "a242c4ded06168a7ee38d0b2d31e1b574c78c1cdf2633a4b2d6cecb5124ba3cd"


def v0():
    return p2_law.read(p2_law.law_bytes())


# -- the kernel and the table ------------------------------------------------------------------------------------------
def test_the_pauli_4x4_kernel_is_the_fermi_disc_on_the_4_by_4_torus():
    A = p2_law.kernel()
    assert len(A) == 16 and all(len(r) == 16 for r in A)
    assert all(A[i][i] == 5 for i in range(16)), "K_ii = 5/16: the disc |k|^2 <= 1 holds five momenta"
    assert A[0][1] == 3 and A[0][4] == 3, "nearest neighbours: K = 3/16"
    assert all(A[i][j] == A[j][i] for i in range(16) for j in range(16))


def test_the_table_from_the_kernel_is_1360_forbidden_of_4368_with_weights_0_1_4_9_over_4096():
    L, N, den, layouts, weights, observables = p2_law.law_parts()
    assert (L, N, den, len(layouts)) == (4, 5, 4096, 4368)
    assert layouts == tuple(itertools.combinations(range(16), 5))
    assert sorted(set(weights)) == [0, 1, 4, 9]
    assert sum(1 for w in weights if w == 0) == 1360 and sum(weights) == 4096
    assert {w: weights.count(w) for w in set(weights)} == {0: 1360, 1: 2672, 4: 320, 9: 16}
    assert observables == {"X0X1": Fraction(3, 8), "Y0Y1": Fraction(3, 8)}


def test_the_dets_are_held_independently_by_a_second_determinant():
    """Bareiss's elimination against plain cofactor expansion in Fractions, on a sample of layouts."""
    A = p2_law.kernel()

    def cofactor(m):
        if len(m) == 1:
            return m[0][0]
        return sum((-1) ** j * m[0][j] * cofactor([r[:j] + r[j + 1:] for r in m[1:]]) for j in range(len(m)))
    for Y in list(itertools.combinations(range(16), 5))[::97]:
        sub = [[A[i][j] for j in Y] for i in Y]
        assert p2_law._det(sub) == cofactor(sub)


def test_the_pair_occupations_of_the_law_are_the_determinantal_k_ii_k_jj_minus_k_ij_squared():
    """A fact of the law no line of P2 states: every pair's occupation is K_ii K_jj - K_ij^2 (the design, item 2)."""
    law, A = v0(), p2_law.kernel()
    e = p2_law.expected(p2_law.model_of("law", law), law)
    want = tuple(Fraction(A[i][i] * A[j][j] - A[i][j] ** 2, 256) for i, j in itertools.combinations(range(16), 2))
    assert e["pair-occupations"] == want
    assert e["one-site-occupations"] == (Fraction(5, 16),) * 16


def test_the_law_file_is_one_canonical_compact_line_and_its_digest_is_pinned():
    data = p2_law.law_bytes()
    assert data == canonical.compact(json.loads(data)) and data.endswith(b"}\n") and data.count(b"\n") == 1
    assert len(data) == 78482
    assert hashlib.sha256(data).hexdigest() == LAW_SHA256
    doc = json.loads(data)
    assert sorted(doc) == list(p2_law.KEYS) and doc["format"] == "qro-law/1" and doc["tile"] == [4, 4]
    assert doc["layouts"][0] == [[0, 1, 2, 3, 4], 0] and doc["observables"] == {"X0X1": "3/8", "Y0Y1": "3/8"}



def test_read_gives_back_what_write_wrote():
    law = p2_law.read(small_law_bytes())
    assert (law.L, law.M, law.N, law.den, law.D) == (2, 4, 2, 10, 6)
    assert law.layouts == SMALL_LAYOUTS and law.weights == SMALL_WEIGHTS and law.observables == SMALL_OBSERVABLES
    assert law.digest == hashlib.sha256(small_law_bytes()).hexdigest()
    assert law.probability((0, 2)) == Fraction(2, 5) and law.probability((0, 1)) == 0 and law.probability((0,)) == 0
    assert law.nn_pairs == ((0, 1), (0, 2), (1, 3), (2, 3)) and law.w_max == 4
    assert law.norm == Fraction(34, 100) - Fraction(1, 6)


def test_v0s_law_meets_the_measure_sets_three_needs():
    p2_law.needs(v0())
    p2_law.needs(p2_law.read(small_law_bytes()))


# -- the reader's refusals ---------------------------------------------------------------------------------------------
def doc():
    return json.loads(small_law_bytes())


def compact(d):
    return canonical.compact(d)


def setting(path, value):
    def plant():
        d = doc()
        target = d
        for k in path[:-1]:
            target = target[k]
        target[path[-1]] = value
        return compact(d)
    return plant


def dropping(key):
    def plant():
        d = doc()
        del d[key]
        return compact(d)
    return plant


HOSTILE_BYTES = {
    "not UTF-8": (lambda: b"\xff" + small_law_bytes(), "not UTF-8"),
    "not JSON": (lambda: b"{", "not JSON"),
    "a key twice": (lambda: small_law_bytes().replace(b'{"crystals":2,', b'{"crystals":2,"crystals":2,', 1), "twice"),
    "a NaN": (lambda: small_law_bytes().replace(b'"crystals":2', b'"crystals":NaN', 1), "no value"),
    "an integer past 2^63 - 1": (lambda: small_law_bytes().replace(b'"denominator":10', b'"denominator":' +
                                                                    b"9" * 30, 1), "past"),
    "a list at the top": (lambda: b"[]\n", "exactly the keys"),
    "pretty-printed": (lambda: (json.dumps(doc(), indent=1, sort_keys=True) + "\n").encode(), "one spelling"),
    "a space after a comma": (lambda: small_law_bytes().replace(b",", b", ", 1), "one spelling"),
    "no final line feed": (lambda: small_law_bytes()[:-1], "one spelling"),
    "a CR before the line feed": (lambda: small_law_bytes()[:-1] + b"\r\n", "one spelling"),
    "two line feeds": (lambda: small_law_bytes() + b"\n", "one spelling"),
    "keys unsorted": (lambda: (json.dumps(dict(reversed(list(doc().items()))), separators=(",", ":")) + "\n").encode(),
                      "one spelling"),
    "a non-ASCII escape spelt raw": (lambda: small_law_bytes().replace(b"Givens", "Gívens".encode("utf-8"), 1),
                                     "one spelling"),
}
HOSTILE_DOCS = {
    "a key missing": (dropping("stock"), "exactly the keys"),
    "an extra key": (lambda: compact({**doc(), "zz": 1}), "exactly the keys"),
    "another format": (setting(["format"], "qro-law/2"), "format"),
    "a tile not a list": (setting(["tile"], 4), "tile"),
    "a tile of one": (setting(["tile"], [2]), "tile"),
    "a tile not square": (setting(["tile"], [2, 3]), "tile"),
    "a tile of 1": (setting(["tile"], [1, 1]), "tile"),
    "a tile past 20 sites": (setting(["tile"], [5, 5]), "tile"),
    "a tile of strings": (setting(["tile"], ["2", "2"]), "tile"),
    "a tile of floats": (setting(["tile"], [2.0, 2.0]), "tile"),
    "a tile of bools": (setting(["tile"], [True, True]), "tile"),
    "no crystals": (setting(["crystals"], 0), "crystals"),
    "more crystals than sites": (setting(["crystals"], 5), "crystals"),
    "crystals a float": (setting(["crystals"], 2.0), "crystals"),
    "crystals a bool": (setting(["crystals"], True), "crystals"),
    "a zero denominator": (setting(["denominator"], 0), "the denominator is a positive whole number"),
    "a negative denominator": (setting(["denominator"], -10), "the denominator is a positive whole number"),
    "a denominator string": (setting(["denominator"], "10"), "the denominator is a positive whole number"),
    "layouts not a list": (setting(["layouts"], {}), "layouts is a list"),
    "a layout missing": (lambda: compact({**doc(), "layouts": doc()["layouts"][:-1]}), "of the 6 layouts"),
    "a layout extra": (lambda: compact({**doc(), "layouts": doc()["layouts"] + [[[2, 3], 0]]}), "more than the 6"),
    "two layouts swapped": (lambda: compact({**doc(), "layouts": [doc()["layouts"][1], doc()["layouts"][0]]
                                             + doc()["layouts"][2:]}), "layouts[0]"),
    "a site list wrong": (setting(["layouts", 0, 0], [0, 2]), "layouts[0]"),
    "a negative weight": (lambda: compact({**doc(), "layouts": [[[0, 1], -1], [[0, 2], 5]] + doc()["layouts"][2:]}),
                          "layouts[0]"),
    "a float weight": (setting(["layouts", 1, 1], 4.0), "layouts[1]"),
    "a bool weight": (setting(["layouts", 0, 1], False), "layouts[0]"),
    "a row of three": (setting(["layouts", 0], [[0, 1], 0, 0]), "layouts[0]"),
    "a row not a list": (setting(["layouts", 0], {"sites": [0, 1]}), "layouts[0]"),
    "weights not summing": (setting(["layouts", 1, 1], 5), "sum to 11"),
    "observables a list": (setting(["observables"], []), "observables is an object"),
    "an observable in Z": (setting(["observables"], {"Z0Z1": "1/2"}), "no pair observable"),
    "an observable mixing letters": (setting(["observables"], {"X0Y1": "1/2"}), "no pair observable"),
    "an observable in lowercase": (setting(["observables"], {"x0x1": "1/2"}), "no pair observable"),
    "an observable's qubits reversed": (setting(["observables"], {"X1X0": "1/2"}), "the first below"),
    "an observable off the tile": (setting(["observables"], {"X0X4": "1/2"}), "the first below"),
    "an observable with a leading zero": (setting(["observables"], {"X0X01": "1/2"}), "no pair observable"),
    "an observable as a number": (setting(["observables", "X0X1"], 0.8), "rational"),
    "an observable not in lowest terms": (setting(["observables", "X0X1"], "8/10"), "rational"),
    "an observable past 1": (setting(["observables", "X0X1"], "3/2"), "outside [-1, 1]"),
    "a stock that is empty": (setting(["stock"], ""), "stock"),
    "a source that is no text": (setting(["source"], 7), "source"),
    "a source with a control character": (setting(["source"], "a\tb"), "source"),
}


@pytest.mark.parametrize("case", sorted(HOSTILE_BYTES) + sorted(HOSTILE_DOCS))
def test_a_law_file_out_of_its_form_is_refused_for_what_is_wrong_and_nothing_escapes(case):
    plant, why = {**HOSTILE_BYTES, **HOSTILE_DOCS}[case]
    with pytest.raises(LawError) as r:
        p2_law.read(plant())
    assert why in str(r.value), str(r.value)


def test_a_law_that_is_not_bytes_is_refused():
    with pytest.raises(LawError):
        p2_law.read(small_law_bytes().decode())


def test_each_plant_is_one_fault_in_bytes_the_reader_reads_otherwise():
    """The control of the matrix: the unplanted document, re-serialised the same way, reads."""
    assert compact(doc()) == small_law_bytes()
    p2_law.read(compact(doc()))


# -- the measure set's three needs, each its own refusal (the lead's note on E2 (6)) -----------------------------------
def test_a_law_whose_observables_are_not_exactly_x0x1_and_y0y1_cannot_be_measured():
    for obs in ({"X0X1": Fraction(4, 5)}, {**SMALL_OBSERVABLES, "X2X3": Fraction(1)}, {"X2X3": 1, "Y2Y3": 1}):
        with pytest.raises(LawError) as r:
            p2_law.needs(p2_law.read(small_law_bytes(observables=obs)))
        assert "exactly X0X1, Y0Y1" in str(r.value)


def test_a_law_that_never_occupies_a_site_cannot_be_measured():
    """Site 1 never occupied: the weights of (0, 1), (1, 2) and (1, 3) all zero."""
    law = p2_law.read(small_law_bytes(weights=(0, 4, 4, 0, 0, 2)))
    with pytest.raises(LawError) as r:
        p2_law.needs(law)
    assert "never occupies the sites [1]" in str(r.value)


def test_a_uniform_law_has_no_xeb_norm_and_cannot_be_measured():
    law = p2_law.read(small_law_bytes(weights=(1,) * 6, den=6))
    assert law.norm == 0
    with pytest.raises(LawError) as r:
        p2_law.needs(law)
    assert "no norm" in str(r.value)


def test_the_classes_are_refused_for_a_law_the_set_cannot_measure():
    with pytest.raises(LawError):
        p2_law.classes(p2_law.read(small_law_bytes(weights=(1,) * 6, den=6)))


def test_observable_pair_reads_a_name_or_refuses_it():
    assert p2_law.observable_pair("Y2Y3", 4) == ("Y", 2, 3)
    for bad in ("Y2Y3 ", "X0X1X2", 7, None, "X01X2"):
        with pytest.raises(LawError):
            p2_law.observable_pair(bad, 16)


def test_the_small_laws_expected_values_worked_by_hand():
    """Weights 0, 4, 4, 1, 1, 0 over 10 on the layouts (0,1) to (2,3): sites 0 to 3 occupied 8, 2, 5 and 5 of 10; the
    torus's neighbour pairs (0,1), (0,2), (1,3), (2,3) give P(ij) / (P(i) P(j)) = 0, 1, 1, 0. Every layout once: 2/3."""
    law = p2_law.read(small_law_bytes())
    F = Fraction
    e = p2_law.expected(p2_law.model_of("law", law), law)
    assert e["crystals-per-shot"] == (0, 0, 1, 0, 0)
    assert e["one-site-occupations"] == (F(4, 5), F(1, 5), F(1, 2), F(1, 2))
    assert e["pair-occupations"] == (0, F(2, 5), F(2, 5), F(1, 10), F(1, 10), 0)
    assert e["nn-pair-correlation"] == F(1, 2) and e["n-crystal-share"] == 1
    u = p2_law.expected(p2_law.model_of("uniform", law), law)
    assert u["nn-pair-correlation"] == F(2, 3) and u["crystals-per-shot"] == (0, 0, 1, 0, 0)
    assert u["one-site-occupations"] == (F(1, 2),) * 4 and u["pair-occupations"] == (F(1, 6),) * 6
    d = p2_law.expected(p2_law.model_of("dephased", law), law)
    assert d["nn-pair-correlation"] == F(1, 2) and (d["x0x1"], d["y0y1"]) == (0, 0)


def test_a_name_that_is_no_model_is_refused():
    with pytest.raises(LawError, match="'twin' is no model of qro-measures/1"):
        p2_law.model_of("twin", p2_law.read(small_law_bytes()))
