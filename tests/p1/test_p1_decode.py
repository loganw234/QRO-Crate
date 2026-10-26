"""The decode rules, and what holds a bit order. Each rule is held to a statement of it written in the test from the
rule's own prose, apart from the code: IBM's over all 65,536 outcomes against Quantum-Film's bitstring reading, and
Atlas's against the encoder of p1_builder, which writes a count string from the setting's label as the rule's
docstring describes it. The known-answer verdicts are held at their boundaries: the strict inequality, the modal
tie-break, the self-mirror refusal, and the Atlas z test at exactly four standard deviations in exact integers.
pub_counts is held on a crate on disk and on the bare entities a generator builds while a crate is made."""
import json
from fractions import Fraction

import pytest
from p1_builder import (ATLAS_RULE, KA, LAYOUTS, atlas_model, atlas_result, atlas_string, atlas_vector, ibm_model,
                        ka_qasm, known_answer_rows, outcome, raw_ibm)

from qro import p1_decode, p1_forms
from qro.p1_graph import GraphError

IBM = p1_decode.IBM_RULE


def pub_of(values):
    return p1_forms.IbmPub(len(values), b"".join(v.to_bytes(2, "big") for v in values), None)


# -- IBM -------------------------------------------------------------------------------------------------------------
def test_ibm_counts_read_every_sixteen_bit_outcome_as_quantum_film_reads_its_bitstring():
    """Quantum-Film: a sampler bitstring is written most significant bit first, so its position p holds classical
    bit 15 - p; the qubits that read 1 are those whose bit is 1. Read in plain order, the mirror."""
    pub = pub_of(list(range(1 << 16)))
    msb, lsb = p1_decode.ibm_counts(pub, "msb-first"), p1_decode.ibm_counts(pub, "lsb-first")
    assert len(msb) == len(lsb) == 1 << 16
    for v in range(1 << 16):
        bits = format(v, "016b")
        want_msb = tuple(i for i in range(16) if bits[15 - i] == "1")
        want_lsb = tuple(i for i in range(16) if bits[i] == "1")
        assert msb[want_msb] == 1 and lsb[want_lsb] == 1


def test_ibm_counts_tally_repeats_and_sort_by_outcome():
    got = p1_decode.ibm_counts(pub_of([5, 5, 1, 5, 0, 1]), "msb-first")
    assert got == {(): 1, (0,): 2, (0, 2): 3} and list(got) == sorted(got)
    assert p1_decode.ibm_counts(pub_of([5, 5, 1, 5, 0, 1]), "lsb-first") == {(): 1, (15,): 2, (13, 15): 3}


@pytest.mark.parametrize("chunk", [1, 3, 7, 40, 41, 1 << 16])
def test_the_tally_is_the_same_whatever_the_chunk_it_is_made_in(monkeypatch, chunk):
    """Rows are tallied a chunk at a time so that a hostile result's memory does not grow with its shots; a chunk of
    one row, a chunk that divides the rows, one that does not, and one longer than the rows all give one tally."""
    rows = known_answer_rows(40) + [outcome((1, 2, 3))] * 5
    want = p1_decode.ibm_counts(pub_of(rows), "msb-first")
    monkeypatch.setattr(p1_decode, "CHUNK", chunk)
    assert p1_decode.ibm_counts(pub_of(rows), "msb-first") == want
    assert sum(want.values()) == 45 and p1_decode.ibm_counts(pub_of(rows), "lsb-first")


def test_the_known_answer_outcome_is_the_flipped_set_under_the_rule():
    pub = pub_of([outcome(KA)] * 3)
    assert p1_decode.ibm_counts(pub, "msb-first") == {KA: 3}
    assert p1_decode.ibm_counts(pub, "lsb-first") == {(3, 8, 12, 14, 15): 3}


@pytest.mark.parametrize("order", ["atlas-register", "circuit-order", "MSB-FIRST", "", None, "msb"])
def test_an_order_the_ibm_rule_does_not_admit_is_refused(order):
    with pytest.raises(p1_decode.DecodeError):
        p1_decode.ibm_counts(pub_of([1]), order)


def test_the_rules_are_named_with_the_forms_they_read_and_the_orders_they_admit():
    ibm, atlas = p1_decode.RULES[IBM], p1_decode.RULES[ATLAS_RULE]
    assert set(p1_decode.RULES) == {"quantum_film.ibm.decode/v1", "quantum_film.atlas.decode/v1"}
    assert (ibm.forms, ibm.order, ibm.orders) == (frozenset({"ibm-sampler-result/v1"}), "msb-first",
                                                  frozenset({"msb-first", "lsb-first"}))
    assert (atlas.forms, atlas.order, atlas.orders) == (
        frozenset({"atlas-tomography-result/v1", "atlas-known-answer-vector/v1"}), "atlas-register",
        frozenset({"atlas-register", "circuit-order"}))


# -- the known-answer circuit --------------------------------------------------------------------------------------------
def test_the_expected_set_is_read_from_the_circuits_x_lines():
    assert p1_decode.expected_set(ka_qasm()) == KA
    assert p1_decode.expected_set(ka_qasm((2, 15))) == (2, 15)
    assert p1_decode.expected_set(ka_qasm(())) == ()
    assert p1_decode.expected_set(ka_qasm(tuple(range(16)))) == tuple(range(16))


def lines_of(qasm):
    return qasm.decode().split("\n")


def joined(lines):
    return "\n".join(lines).encode()


BAD_CIRCUITS = {
    "not ASCII": lambda t: t.replace(b"qelib1", b"qel\xc3\xa91"),
    "no final line feed": lambda t: t[:-1],
    "CRLF line ends": lambda t: t.replace(b"\n", b"\r\n"),
    "a header line missing": lambda t: joined(lines_of(t)[1:]),
    "another header": lambda t: t.replace(b"OPENQASM 2.0;", b"OPENQASM 3.0;"),
    "another register": lambda t: t.replace(b"qreg q[16];", b"qreg q[15];"),
    "another classical register": lambda t: t.replace(b"creg meas[16];", b"creg c[16];"),
    "an x line repeated": lambda t: t.replace(b"x q[1];\n", b"x q[1];\nx q[1];\n"),
    "x lines out of order": lambda t: t.replace(b"x q[0];\nx q[1];", b"x q[1];\nx q[0];"),
    "an x on qubit 16": lambda t: t.replace(b"x q[12];", b"x q[16];"),
    "an x with a leading zero": lambda t: t.replace(b"x q[3];", b"x q[03];"),
    "an x with a space": lambda t: t.replace(b"x q[3];", b"x  q[3];"),
    "a gate that is not x": lambda t: t.replace(b"x q[3];", b"h q[3];"),
    "an x after the barrier": lambda t: t.replace(b"measure q[0]", b"x q[13];\nmeasure q[0]"),
    "the barrier on fewer qubits": lambda t: t.replace(b",q[15];", b";"),
    "the barrier out of order": lambda t: t.replace(b"q[1],q[2]", b"q[2],q[1]"),
    "no barrier": lambda t: t.replace(b"barrier", b"// barrier"),
    "a measure missing": lambda t: t.replace(b"measure q[15] -> meas[15];\n", b""),
    "measures out of order": lambda t: t.replace(b"measure q[3] -> meas[3];\nmeasure q[4] -> meas[4];",
                                                 b"measure q[4] -> meas[4];\nmeasure q[3] -> meas[3];"),
    "a measure into another bit": lambda t: t.replace(b"measure q[5] -> meas[5];", b"measure q[5] -> meas[6];"),
    "a measure twice": lambda t: t + b"measure q[0] -> meas[0];\n",
    "the header and nothing after": lambda t: b"".join(line.encode() + b"\n" for line in lines_of(t)[:4]),
    "x lines and nothing after": lambda t: b"".join(line.encode() + b"\n" for line in lines_of(t)[:9]),
    "a trailing blank line": lambda t: t + b"\n",
    "a comment": lambda t: t + b"// the answer\n",
    "nothing": lambda t: b"",
}


@pytest.mark.parametrize("fn, said", [(lambda t: t[:-1], "does not end in a line feed"),
                                      (lambda t: t.replace(b"qelib1", b"qel\xc3\xa91"), "not ASCII"),
                                      (lambda t: t.replace(b"OPENQASM 2.0;", b"OPENQASM 3.0;"), "does not open with"),
                                      (lambda t: t + b"measure q[0] -> meas[0];\n", "x lines, a barrier")],
                         ids=["no final line feed", "not ASCII", "another header", "a measure twice"])
def test_a_circuit_is_refused_for_what_is_wrong_with_it(fn, said):
    with pytest.raises(p1_decode.KnownAnswerError, match=said):
        p1_decode.expected_set(fn(ka_qasm()))


def test_a_circuit_of_more_x_lines_than_qubits_is_refused_unread_however_long_it_runs():
    """A hostile circuit of 400,000 x lines: refused at the seventeenth, not scanned (and not re-copied per line)."""
    head = b"".join(line.encode() + b"\n" for line in lines_of(ka_qasm())[:4])
    with pytest.raises(p1_decode.KnownAnswerError, match="more x lines than qubits"):
        p1_decode.expected_set(head + b"x q[0];\n" * 400000)
    seventeen = head + b"".join(f"x q[{q}];\n".encode() for q in range(16)) + b"x q[15];\n"
    with pytest.raises(p1_decode.KnownAnswerError, match="more x lines than qubits"):
        p1_decode.expected_set(seventeen)


@pytest.mark.parametrize("fn", BAD_CIRCUITS.values(), ids=BAD_CIRCUITS)
def test_a_circuit_that_is_not_quantum_films_known_answer_is_refused(fn):
    with pytest.raises(p1_decode.KnownAnswerError):
        p1_decode.expected_set(fn(ka_qasm()))


# -- IBM's verdict ----------------------------------------------------------------------------------------------------------
E, MIRROR = KA, (3, 8, 12, 14, 15)


def test_the_known_answer_holds_when_the_expected_set_is_modal_with_more_shots_than_its_mirror():
    v = p1_decode.known_answer_verdict({E: 930, (0, 1, 3, 7): 60, (): 34}, E)
    assert v.holds and (v.n_expected, v.n_mirror, v.shots, v.modal) == (930, 0, 1024, E)
    assert (v.share, v.mirror_share) == (Fraction(465, 512), Fraction(0, 1))
    assert v.expected == E and v.mirror == MIRROR


def test_a_tie_between_the_expected_set_and_its_mirror_decides_nothing():
    """E sorts before its mirror, so a tie makes E the modal outcome: only the strict inequality refuses it."""
    assert E < MIRROR
    v = p1_decode.known_answer_verdict({E: 10, MIRROR: 10}, E)
    assert v.modal == E and not v.holds
    assert p1_decode.known_answer_verdict({E: 11, MIRROR: 10}, E).holds
    assert not p1_decode.known_answer_verdict({E: 10, MIRROR: 11}, E).holds


def test_a_tie_for_the_most_shots_goes_to_the_smaller_outcome_and_may_still_hold():
    other = (0, 1)
    assert other < E
    v = p1_decode.known_answer_verdict({E: 10, other: 10, MIRROR: 1}, E)
    assert v.modal == other and not v.holds
    big = (15,)
    assert E < big
    v = p1_decode.known_answer_verdict({E: 10, big: 10}, E)
    assert v.modal == E and v.holds


@pytest.mark.parametrize("counts", [
    {(1, 2): 20, E: 15}, {MIRROR: 30, E: 5}, {(): 40}, {E: 5, (1,): 6, (2,): 6, (3,): 6}, {(0, 1, 3, 7): 100, E: 99},
], ids=["another outcome modal", "the mirror modal", "all zero", "no outcome modal enough", "one shot short"])
def test_the_known_answer_does_not_hold_when_the_expected_set_is_not_the_modal_outcome(counts):
    assert not p1_decode.known_answer_verdict(counts, E).holds


def test_the_expected_set_may_be_given_in_any_order():
    assert p1_decode.known_answer_verdict({E: 5}, [12, 3, 0, 7, 1]).holds


@pytest.mark.parametrize("expected", [(7, 8), (0, 15), (), (1, 2, 13, 14), tuple(range(16))])
def test_a_set_that_is_its_own_mirror_tells_no_order_from_its_mirror_and_is_refused(expected):
    with pytest.raises(p1_decode.KnownAnswerError, match="own mirror"):
        p1_decode.known_answer_verdict({expected: 5}, expected)


def test_no_shots_is_no_verdict():
    with pytest.raises(p1_decode.KnownAnswerError, match="no shots"):
        p1_decode.known_answer_verdict({}, E)
    with pytest.raises(p1_decode.KnownAnswerError, match="no shots"):
        p1_decode.known_answer_verdict({E: 0}, E)


def test_one_shot_is_judged_like_any_other_number():
    """A single shot that reads the expected set holds, and one that reads anything else does not."""
    v = p1_decode.known_answer_verdict({E: 1}, E)
    assert v.holds and (v.n_expected, v.n_mirror, v.shots) == (1, 0, 1) and v.share == 1
    absent = p1_decode.known_answer_verdict({(): 1}, E)
    assert not absent.holds and (absent.n_expected, absent.n_mirror, absent.modal) == (0, 0, ())
    assert f"{list(E)} has 0 of 1 shots (0/1), its mirror {list(MIRROR)} has 0 (0/1)" in absent.text()


def test_the_verdict_holds_for_another_width():
    assert p1_decode.known_answer_verdict({(0,): 5}, (0,), 4).mirror == (3,)
    with pytest.raises(p1_decode.KnownAnswerError):
        p1_decode.known_answer_verdict({(1,): 5}, (1,), 3)


def test_the_verdict_reads_its_shares_as_numbers_over_numbers():
    v = p1_decode.known_answer_verdict({E: 930, (): 94}, E)
    assert "465/512" in v.text() and "0/1" in v.text() and "930 of 1024" in v.text()


def test_a_known_answer_job_read_in_each_order_holds_in_one_only():
    rows = known_answer_rows(40)
    pub = pub_of(rows)
    assert p1_decode.known_answer_verdict(p1_decode.ibm_counts(pub, "msb-first"), E).holds
    assert not p1_decode.known_answer_verdict(p1_decode.ibm_counts(pub, "lsb-first"), E).holds


# -- Atlas ---------------------------------------------------------------------------------------------------------------
def test_the_register_order_of_a_setting_is_the_non_i_qubits_then_the_rest_little_endian():
    """Worked by hand for IIIIIIYIIIIIIXII: Y on qubit 9, X on qubit 2. The register is [2, 9, 0, 1, 3, ...], the
    string's rightmost character its first slot."""
    assert p1_decode.atlas_order("IIIIIIYIIIIIIXII", "atlas-register") == [15, 14, 13, 12, 11, 10, 8, 7, 6, 5, 4, 3, 1,
                                                                          0, 9, 2]
    assert p1_decode.atlas_order("IIIIIIIIIIIIIIZZ", "atlas-register") == list(range(15, -1, -1))
    assert p1_decode.atlas_order("ZIIIIIIIIIIIIIII", "atlas-register") == [14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1,
                                                                          0, 15]
    assert p1_decode.atlas_order("IIIIIIYIIIIIIXII", "circuit-order") == list(range(15, -1, -1))


@pytest.mark.parametrize("order", ["msb-first", "lsb-first", "", None])
def test_an_order_the_atlas_rule_does_not_admit_is_refused(order):
    with pytest.raises(p1_decode.DecodeError):
        p1_decode.atlas_order("I" * 16, order)


def test_the_basis_a_qubit_was_measured_in_is_its_label_character_with_i_meaning_z():
    assert [p1_decode.basis_of("IIIIIIYIIIIIIXII", q) for q in (0, 1, 2, 3, 9, 10, 15)] == list("ZZXZYZZ")
    assert [p1_decode.basis_of("ZXYI" + "I" * 12, q) for q in (15, 14, 13, 12)] == list("ZXYZ")


def test_layouts_round_trip_through_the_encoder_written_from_the_rules_prose():
    for label in ("IIIIIIIIIIIIIIZZ", "ZIIIIIIIIIIIIIII", "IIZIIIIIIZIIIIII", "ZZZZZZZZZZZZZZZZ", "I" * 16):
        for order in ("atlas-register", "circuit-order"):
            res = p1_forms.parse_atlas_result(atlas_result(LAYOUTS, label=label, other="XIIIIIIIIIIIIIII", order=order))
            assert p1_decode.atlas_layouts(res, order) == LAYOUTS, (label, order)


def test_the_wrong_order_reads_other_layouts():
    res = p1_forms.parse_atlas_result(atlas_result(LAYOUTS, label="IIZIIIIIIZIIIIII"))
    assert p1_decode.atlas_layouts(res, "atlas-register") == LAYOUTS
    assert p1_decode.atlas_layouts(res, "circuit-order") != LAYOUTS


def result_with(labels):
    counts = {"0" * 16: 1}
    return p1_forms.AtlasResult("j", {label: p1_forms.AtlasSetting(1, counts) for label in labels}, {}, 1)


@pytest.mark.parametrize("labels", [["IIIIIIIIIIIIIIXX"], ["IIIIIIIIIIIIIIZZ", "IIIIIIIIIIIIIIZI"], []],
                         ids=["no all-Z setting", "two all-Z settings", "no setting"])
def test_a_result_without_exactly_one_all_z_setting_is_refused(labels):
    with pytest.raises(p1_decode.DecodeError, match="exactly one all-Z setting"):
        p1_decode.z_setting(result_with(labels))


def test_the_all_z_setting_may_hold_i_and_z_in_any_mix():
    assert p1_decode.z_setting(result_with(["ZIZIZIZIZIZIZIZI", "XIIIIIIIIIIIIIII"])) == "ZIZIZIZIZIZIZIZI"


def marginals(label, n, ones, order="atlas-register"):
    """A one-setting vector of n shots whose qubit q reads 1 in exactly ones[q] of them: shot j sets qubit q iff
    j < ones[q]."""
    counts = {}
    for j in range(n):
        s = atlas_string(label, {q for q in range(16) if j < ones[q]}, order)
        counts[s] = counts.get(s, 0) + 1
    return p1_forms.parse_atlas_vector(json.dumps({"job": "j", "measurements": {label: {"counts": counts,
                                                                                         "shots": n}}}).encode())


def expected(n):
    return [n * (2 * q + 1) // 32 for q in range(16)]


def test_the_vector_holds_when_every_z_position_reads_the_frequency_the_circuit_prepares():
    v = p1_decode.atlas_vector_verdict(p1_forms.parse_atlas_vector(atlas_vector()), "atlas-register")
    assert v.holds and v.worst == 0 and v.failed == () and v.compared == 14 + 15 + 12
    assert "0 of 41" in v.text()


def test_the_vector_written_in_one_order_holds_under_that_order_only():
    for written, other in (("atlas-register", "circuit-order"), ("circuit-order", "atlas-register")):
        vec = p1_forms.parse_atlas_vector(atlas_vector(order=written))
        assert p1_decode.atlas_vector_verdict(vec, written).holds
        bad = p1_decode.atlas_vector_verdict(vec, other)
        assert not bad.holds and bad.failed and bad.worst > 16


def test_the_mirror_of_the_prepared_frequencies_does_not_hold():
    n = 4096
    mirrored = [expected(n)[15 - q] for q in range(16)]
    assert p1_decode.atlas_vector_verdict(marginals("I" * 16, n, expected(n)), "atlas-register").holds
    assert not p1_decode.atlas_vector_verdict(marginals("I" * 16, n, mirrored), "atlas-register").holds


def at_bound(n=496):
    ones = [round(n * (2 * q + 1) / 32) for q in range(16)]
    return ones


@pytest.mark.parametrize("q, c, holds", [(15, 465, True), (15, 464, False), (0, 31, True), (0, 32, False),
                                         (0, 0, True)])
def test_the_z_bound_is_four_standard_deviations_in_exact_integers_and_inclusive(q, c, holds):
    """n = 496: qubit 15 is expected at 480.5 of 496 with a standard deviation of 3.875, so 465 is exactly 4
    below; qubit 0 at 15.5 with the same, so 31 is exactly 4 above and 0 exactly 4 below."""
    n = 496
    ones = at_bound(n)
    ones[q] = c
    v = p1_decode.atlas_vector_verdict(marginals("I" * 16, n, ones), "atlas-register")
    assert v.holds is holds
    if holds and c in (465, 31, 0):
        assert v.worst == 16                                     # exactly four deviations, and still held
    if not holds:
        assert len(v.failed) == 1 and v.failed[0][2] == q and v.failed[0][3] > 16


@pytest.mark.parametrize("q, c", [(7, 188), (7, 277)])
def test_a_position_just_past_four_deviations_does_not_hold(q, c):
    """n = 496 and qubit 7 is expected at 232.5 of 496; 188 and 277 give a z squared of 16.03 and 16.76: past 16 and
    short of 17, so a bound of 17 would hold them."""
    n = 496
    ones = at_bound(n)
    ones[q] = c
    v = p1_decode.atlas_vector_verdict(marginals("I" * 16, n, ones), "atlas-register")
    assert not v.holds and 16 < v.worst < 17 and [f[2] for f in v.failed] == [q]


def test_x_and_y_positions_are_not_compared_and_junk_in_them_does_not_matter():
    n = 4096
    ones = expected(n)
    label = "IIIIIIYIIIIIIXII"                           # Y on qubit 9, X on qubit 2
    junk = list(ones)
    junk[2], junk[9] = 4000, 1
    good = p1_decode.atlas_vector_verdict(marginals(label, n, ones), "atlas-register")
    skew = p1_decode.atlas_vector_verdict(marginals(label, n, junk), "atlas-register")
    assert good.holds and skew.holds and good.compared == skew.compared == 14


def test_a_vector_with_one_z_position_is_judged_on_that_one():
    n = 4096
    label = "X" * 15 + "Z"                                   # only qubit 0 is measured in Z
    v = p1_decode.atlas_vector_verdict(marginals(label, n, expected(n)), "atlas-register")
    assert v.holds and v.compared == 1 and v.worst == 0
    skew = expected(n)
    skew[0] = n // 2
    v = p1_decode.atlas_vector_verdict(marginals(label, n, skew), "atlas-register")
    assert not v.holds and v.compared == 1 and [f[2] for f in v.failed] == [0]


def test_a_vector_with_no_z_position_has_nothing_to_hold_and_does_not():
    v = p1_decode.atlas_vector_verdict(marginals("X" * 16, 4096, expected(4096)), "atlas-register")
    assert not v.holds and v.compared == 0 and "no Z-basis position" in v.text()


# -- the rules by name, and a result accounted for -----------------------------------------------------------------------
def test_a_rule_that_is_not_built_is_an_error_to_decode_and_to_account_for():
    with pytest.raises(p1_decode.DecodeError, match="no decode rule"):
        p1_decode.decode_counts("quantum_film.ibm.decode/v2", None, 0, "msb-first")
    with pytest.raises(p1_decode.DecodeError, match="no decode rule"):
        p1_decode.account("quantum_film.ibm.decode/v2", None, "msb-first", set())


def test_a_pub_outside_a_result_is_an_error_to_decode():
    res = p1_forms.parse_ibm_result(raw_ibm([[1, 2]], [None]))
    assert p1_decode.decode_counts(IBM, res, 0, "msb-first") == {(0,): 1, (1,): 1}
    with pytest.raises(p1_decode.DecodeError, match="outside a result of 1 PUBs"):
        p1_decode.decode_counts(IBM, res, 1, "msb-first")


def test_an_atlas_law_result_is_accounted_for_only_with_its_one_all_z_setting():
    res = p1_forms.parse_atlas_result(atlas_result(LAYOUTS))
    p1_decode.account(ATLAS_RULE, res, "atlas-register", {"law"})
    bad = p1_forms.parse_atlas_result(atlas_result(LAYOUTS, label="IIIIIIIIIIIIIIXX", other="IIIIIIIIIIIIIIXY"))
    with pytest.raises(p1_decode.DecodeError):
        p1_decode.account(ATLAS_RULE, bad, "atlas-register", {"law"})
    p1_decode.account(ATLAS_RULE, bad, "atlas-register", {"known-answer"})        # no layouts asked of it


def test_only_a_law_pubs_atlas_result_is_accounted_for_by_its_layouts():
    """The verifier's mutant 29 accounted for a coherence Pub's result too. A result with no all-Z setting is a result
    for any role but the law's: the layouts are the law job's data."""
    bad = p1_forms.parse_atlas_result(atlas_result(LAYOUTS, label="IIIIIIIIIIIIIIXX", other="IIIIIIIIIIIIIIXY"))
    for roles in ({"coherence"}, {"known-answer"}, {"coherence", "known-answer"}, set(), {"coherence-xx"}):
        p1_decode.account(ATLAS_RULE, bad, "atlas-register", roles)
    for roles in ({"law"}, {"law", "coherence"}, {"law", "known-answer"}):
        with pytest.raises(p1_decode.DecodeError, match="all-Z setting"):
            p1_decode.account(ATLAS_RULE, bad, "atlas-register", roles)


def test_atlas_layouts_are_sorted_by_outcome_not_by_the_order_the_file_lists_the_counts():
    """The verifier's mutant 26. The counts are listed by their strings, and a layout's string does not sort as the layout
    does: (1,) comes before (0, 1) in the file, and after it as an outcome."""
    layouts = {(1,): 7, (0, 1): 5, (2,): 3, (0,): 1}
    res = p1_forms.parse_atlas_result(atlas_result(layouts))
    in_the_files_order = sorted(layouts, key=lambda occ: atlas_string("IIIIIIIIIIIIIIZZ", set(occ)))     # the builder sorts the keys
    assert in_the_files_order != sorted(in_the_files_order)                                                 # so the test has a fault to see
    got = p1_decode.atlas_layouts(res)
    assert list(got) == sorted(got) == [(0,), (0, 1), (1,), (2,)] and sum(got.values()) == 16


# -- pub_counts, on a crate on disk and on the entities a generator builds ---------------------------------------------------
@pytest.fixture(scope="module")
def ibm(tmp_path_factory):
    m = ibm_model()
    return m, m.write(tmp_path_factory.mktemp("ibm"))


def want_counts(m, raw, k=0):
    return p1_decode.ibm_counts(p1_forms.parse_ibm_result(m.files[raw]).pubs[k], "msb-first")


def test_pub_counts_decode_a_pubs_raw_bytes_under_its_decodes_rule_and_order(ibm):
    m, crate = ibm
    md = json.loads((crate / "ro-crate-metadata.json").read_bytes())
    assert p1_decode.pub_counts(crate, md, "#pub-jobka-0") == want_counts(m, "run/jobka-raw.json")
    assert p1_decode.pub_counts(crate, md, "#pub-joblaw-0") == want_counts(m, "run/joblaw-raw.json")
    assert p1_decode.pub_counts(crate, md, "#pub-jobcoh-0") == want_counts(m, "run/jobcoh-raw.json", 0)
    assert p1_decode.pub_counts(crate, md, "#pub-jobcoh-1") == want_counts(m, "run/jobcoh-raw.json", 1)
    assert p1_decode.pub_counts(crate, md, "#pub-jobcoh-0") != p1_decode.pub_counts(crate, md, "#pub-jobcoh-1")
    assert p1_decode.pub_counts(crate, md, "#pub-jobka-0")[KA] == 34


def test_pub_counts_read_the_graph_alone_so_a_generators_entities_serve_without_a_metadata_file(ibm):
    """P2's seam (P2's design, found 2): `{"@graph": entities}`, built while the crate is being made."""
    m, crate = ibm
    md = json.loads((crate / "ro-crate-metadata.json").read_bytes())
    bare = {"@graph": list(reversed(md["@graph"]))}
    for pub in ("#pub-jobka-0", "#pub-joblaw-0", "#pub-jobcoh-1"):
        assert p1_decode.pub_counts(crate, bare, pub) == p1_decode.pub_counts(crate, md, pub)
    bare = {"@graph": [e for e in md["@graph"] if e["@id"] not in ("./", "ro-crate-metadata.json")]}
    assert p1_decode.pub_counts(str(crate), bare, "#pub-jobka-0") == want_counts(m, "run/jobka-raw.json")


def test_pub_counts_follow_the_order_the_decode_declares(ibm):
    m, crate = ibm
    md = json.loads((crate / "ro-crate-metadata.json").read_bytes())
    for e in md["@graph"]:
        if e["@id"] == "#decode-jobka":
            e["qro:bitOrder"] = "lsb-first"
    got = p1_decode.pub_counts(crate, md, "#pub-jobka-0")
    assert got == p1_decode.ibm_counts(p1_forms.parse_ibm_result(m.files["run/jobka-raw.json"]).pubs[0], "lsb-first")
    assert KA not in got and (3, 8, 12, 14, 15) in got


def test_pub_counts_never_open_a_record_a_verdict_or_a_line(ibm, tmp_path):
    """The decoded records are REPORTED copies: a crate whose record, line or verdict files are gone or changed gives
    the same counts, so a changed record cannot move a measure."""
    m, crate = ibm
    md = json.loads((crate / "ro-crate-metadata.json").read_bytes())
    want = p1_decode.pub_counts(crate, md, "#pub-joblaw-0")
    bare = tmp_path / "bare"
    (bare / "run").mkdir(parents=True)
    (bare / "run" / "joblaw-raw.json").write_bytes(m.files["run/joblaw-raw.json"])
    assert p1_decode.pub_counts(bare, md, "#pub-joblaw-0") == want


def test_pub_counts_refuse_what_the_graph_or_the_bytes_cannot_give(ibm, tmp_path):
    m, crate = ibm
    md = json.loads((crate / "ro-crate-metadata.json").read_bytes())

    def edited(fn):
        copy = json.loads(json.dumps(md))
        fn(copy["@graph"], {e["@id"]: e for e in copy["@graph"]})
        return copy
    with pytest.raises(GraphError, match="names no entity"):
        p1_decode.pub_counts(crate, md, "#pub-nowhere-0")
    with pytest.raises(GraphError, match="not a qro:Pub"):
        p1_decode.pub_counts(crate, md, "#job-jobka")
    with pytest.raises(GraphError):
        p1_decode.pub_counts(crate, edited(lambda g, by: by["#job-jobka"].pop("object")), "#pub-jobka-0")
    with pytest.raises(GraphError):
        p1_decode.pub_counts(crate, edited(lambda g, by: by["#decode-jobka"].pop("object")), "#pub-jobka-0")
    def renamed(g, by):
        by["#pub-jobka-0"]["@id"] = "#pub-jobka-x"
        by["#job-jobka"]["object"] = [{"@id": "#pub-jobka-x"}]
    with pytest.raises(GraphError, match="its PUB index"):
        p1_decode.pub_counts(crate, edited(renamed), "#pub-jobka-x")
    with pytest.raises(p1_decode.DecodeError, match="no decode rule"):
        p1_decode.pub_counts(crate, edited(lambda g, by: by["#decode-jobka"].update(
            {"qro:decodeRule": "quantum_film.ibm.decode/v9"})), "#pub-jobka-0")
    with pytest.raises(p1_decode.DecodeError, match="does not read the raw form"):
        p1_decode.pub_counts(crate, edited(lambda g, by: by["run/jobka-raw.json"].update(
            {"qro:rawForm": "atlas-tomography-result/v1"})), "#pub-jobka-0")
    with pytest.raises(p1_decode.DecodeError, match="does not read the order"):
        p1_decode.pub_counts(crate, edited(lambda g, by: by["#decode-jobka"].update({"qro:bitOrder": "circuit-order"})),
                             "#pub-jobka-0")
    (tmp_path / "run").mkdir()
    (tmp_path / "run" / "jobka-raw.json").write_bytes(b"{not json")
    with pytest.raises(p1_forms.RawFormError):
        p1_decode.pub_counts(tmp_path, md, "#pub-jobka-0")


@pytest.mark.parametrize("raw_id", ["../outside.json", "run/../../outside.json", "/outside.json", "C:/outside.json",
                                    "run//jobka-raw.json", "run/./jobka-raw.json", "https://example.org/jobka-raw.json",
                                    "#jobka-raw"])
def test_pub_counts_read_no_file_whose_id_is_not_a_path_in_the_crate(ibm, tmp_path, raw_id):
    """The reader holds every File's @id to a path in the crate (step 1), but pub_counts also serves a generator's
    entities and a caller's. A good result is where a sloppy join of the id would find it, inside the crate and
    beside it; it is not read."""
    m, whole = ibm
    good = m.files["run/jobka-raw.json"]
    crate = tmp_path / "crate"
    for rel in ("run/jobka-raw.json", "outside.json"):
        (crate / rel).parent.mkdir(parents=True, exist_ok=True)
        (crate / rel).write_bytes(good)
    (tmp_path / "outside.json").write_bytes(good)
    md = json.loads((whole / "ro-crate-metadata.json").read_bytes())
    assert p1_decode.pub_counts(crate, md, "#pub-jobka-0") == want_counts(m, "run/jobka-raw.json")
    for e in md["@graph"]:
        if e["@id"] == "run/jobka-raw.json":
            e["@id"] = raw_id
        if e["@id"] in ("#job-jobka", "#decode-jobka"):
            for term in ("result", "object"):
                if term in e:
                    e[term] = [{"@id": raw_id} if r["@id"] == "run/jobka-raw.json" else r for r in e[term]]
    with pytest.raises(GraphError, match="is not a file the crate holds"):
        p1_decode.pub_counts(crate, md, "#pub-jobka-0")


def test_pub_counts_read_no_entity_that_is_no_file_even_at_a_path_of_the_crate(ibm):
    m, crate = ibm
    md = json.loads((crate / "ro-crate-metadata.json").read_bytes())
    for e in md["@graph"]:
        if e["@id"] == "run/jobka-raw.json":
            e["@type"] = "qro:RawResult"
    with pytest.raises(GraphError, match="is not a file the crate holds"):
        p1_decode.pub_counts(crate, md, "#pub-jobka-0")


SEAM_POOL = [None, 0, True, "x", ["a"], {"a": 1}, [], {}, [["a"]], 1.5]
SEAM_KEYS = (("#decode-jobka", "qro:decodeRule"), ("#decode-jobka", "qro:bitOrder"), ("run/jobka-raw.json", "qro:rawForm"),
             ("#decode-jobka", "object"), ("#job-jobka", "object"), ("#job-jobka", "result"), ("#pub-jobka-0", "@id"),
             ("#pub-jobka-0", "@type"), ("#job-jobka", "@type"), ("run/jobka-raw.json", "@type"),
             ("run/jobka-raw.json", "@id"), ("run/jobka-raw.json", "sha256"))
GONE = object()


def test_pub_counts_on_a_malformed_entity_gives_one_of_the_three_value_errors_its_docstring_names(ibm):
    """The verifier's seam_hostile.py (round 2): an unhashable rule, bit order or raw form gave a TypeError. Each key a
    generator or a caller might get wrong, given each kind of value or removed: a count, or GraphError, RawFormError or
    DecodeError, and nothing else."""
    m, crate = ibm
    md = json.loads((crate / "ro-crate-metadata.json").read_bytes())
    base = [e for e in md["@graph"] if e["@id"] not in ("./", "ro-crate-metadata.json")]
    outcomes = {}
    for entity_id, key in SEAM_KEYS:
        for value in SEAM_POOL + [GONE]:
            graph = json.loads(json.dumps(base))
            for e in graph:
                if e["@id"] == entity_id:
                    if value is GONE:
                        e.pop(key, None)
                    else:
                        e[key] = value
            try:
                p1_decode.pub_counts(crate, {"@graph": graph}, "#pub-jobka-0")
                got = "a count"
            except (GraphError, p1_forms.RawFormError, p1_decode.DecodeError) as x:
                got = type(x).__name__
            outcomes[(entity_id, key, repr(value)[:12])] = got
    assert set(outcomes.values()) <= {"a count", "GraphError", "RawFormError", "DecodeError"}
    for rule_like in (("#decode-jobka", "qro:decodeRule"), ("#decode-jobka", "qro:bitOrder"), ("run/jobka-raw.json", "qro:rawForm")):
        assert outcomes[rule_like + ("['a']",)] == "DecodeError" and outcomes[rule_like + ("{'a': 1}",)] == "DecodeError"


def test_a_bit_order_that_cannot_be_looked_up_is_a_decode_error_in_both_rules():
    pub = p1_forms.IbmPub(1, b"\x00\x01", None)
    for bad in (["msb-first"], {"a": 1}, None, 5):
        with pytest.raises(p1_decode.DecodeError):
            p1_decode.ibm_counts(pub, bad)
        with pytest.raises(p1_decode.DecodeError):
            p1_decode.atlas_order("I" * 16, bad)


def test_pub_counts_of_an_atlas_pub_are_the_all_z_settings_layouts(tmp_path):
    crate = atlas_model().write(tmp_path / "atlas")
    md = json.loads((crate / "ro-crate-metadata.json").read_bytes())
    assert p1_decode.pub_counts(crate, md, "#pub-alaw-0") == LAYOUTS
    assert p1_decode.pub_counts(crate, {"@graph": md["@graph"]}, "#pub-alaw-0") == LAYOUTS
    with pytest.raises(p1_decode.DecodeError, match="all-Z"):
        p1_decode.pub_counts(crate, md, "#pub-avec-0")           # the vector has no all-Z setting
