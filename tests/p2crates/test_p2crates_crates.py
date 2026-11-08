"""v0's two crates (P2's design, item 12; P2.2), built by P1's adapter from moth-quantum outside the tree and checked by the
command line as a process: both accepted, steps 6 and 7 among the steps that accept them, each carrying the P2 entities
its records give; the IBM crate's 124 references, to 12 distinct gate lists and 4 logical circuits, each gate list held
to its logical circuit and each logical circuit to its role far inside the tolerance, and the question's law circuit
laying the law; what the work budget counts on each crate; the Atlas crate, which measures no coherence; and the ten
files of P1's twin that P2's tests read, which are moth-quantum's, byte for byte."""
import hashlib
import re
from pathlib import Path

import pytest

import p2crates_support as S
from qro import canonical, p1_decode, p2_hold, p2_law, p2_measures, p2_sim, p2_steps, reader, register_p2
from qro.p1_graph import Index

SOURCE = "2026-09-25/p3/circuit-ed767c01bd4b851d.qasm"


def kinds(md):
    out = {}
    for e in md["@graph"]:
        for t in canonical.types(e):
            if t in ("qro:Measuring", "qro:Contrast", "qro:Measurement", "qro:Hold"):
                out[t] = out.get(t, 0) + 1
    return out


@pytest.mark.parametrize("kind, files, size", [("ibm", 1074, 53443198), ("atlas", 32, 5076857)])
def test_each_crate_is_built_outside_the_tree_and_accepted_by_the_command_line(kind, files, size):
    path, identity, line = S.built(kind)
    assert re.fullmatch(rf"BUILT {kind}: {files} files, {size} bytes, identity [0-9a-f]{{64}}", line), line
    assert S.ROOT not in path.parents and S.MOTH not in path.parents
    assert S.checked(kind) == (0, f"ACCEPTED {identity}", "")


def test_the_ibm_crate_carries_p2s_question_terms_and_entities():
    crate, md = S.built("ibm")[0], S.metadata("ibm")
    ids = Index(md).by_id
    q = ids["#question"]
    assert (q["qro:law"], q["qro:lawCircuit"], q["qro:measureSet"], q["qro:twins"]) == (
        {"@id": "question/law.json"}, {"@id": SOURCE}, "qro-measures/1", ["dephased", "uniform"])
    assert (crate / "question" / "law.json").read_bytes() == p2_law.law_bytes()
    assert kinds(md) == {"qro:Measuring": 1, "qro:Contrast": 20, "qro:Measurement": 31 * 5 + 6, "qro:Hold": 31}
    assert (ids["#measuring"]["qro:alpha"], ids["#measuring"]["qro:family"]) == ("1/20", 31 * 3 + 6)
    assert {e["qro:exactHold"] for e in ids.values() if "qro:Hold" in canonical.types(e)} == {"holds"}
    assert register_p2._enters(md, 6, ("qro:Measuring", "qro:Contrast", "qro:Measurement"))
    assert register_p2._enters(md, 7, ("qro:Hold",))
    assert p2_steps.step6(crate, md) is None and p2_steps.step7(crate, md) is None


def test_the_atlas_crate_carries_p2s_measures_and_no_hold_and_measures_no_coherence():
    """The Atlas crate runs no compile, so it carries no Hold and step 7 does not enter; its six law Pubs are measured,
    three certified measures each; and no Pub of it is a coherence Pub (P2's stated limit 10: its coherences are the
    engine's REPORTED floats, which P2 measures none of)."""
    crate, md = S.built("atlas")[0], S.metadata("atlas")
    idx = Index(md)
    assert kinds(md) == {"qro:Measuring": 1, "qro:Contrast": 20, "qro:Measurement": 6 * 5}
    assert idx.by_id["#measuring"]["qro:family"] == 6 * 3
    assert sorted(p["qro:role"] for p in idx.of_type("qro:Pub")) == ["known-answer"] + ["law"] * 6
    assert register_p2._enters(md, 6, ("qro:Measuring", "qro:Contrast", "qro:Measurement"))
    assert not register_p2._enters(md, 7, ("qro:Hold",))
    assert p2_steps.step6(crate, md) is None


# -- the IBM crate's gate lists -----------------------------------------------------------------------------------------
def references(crate, md):
    """[(manifest entry, its gate list's File, its logical circuit's File)]: every reference of the crate, each Compile's
    manifest in its order, as step 7 walks them."""
    idx = Index(md)
    out = []
    for c in sorted(idx.of_type("qro:Compile"), key=lambda e: e["@id"]):
        for n in p2_hold.read_manifest(p1_decode.crate_file(crate, p2_measures.manifest_of(idx, c), "the manifest")):
            g = [e for e in idx.files_by_sha256(n.gates_sha256) if reader.local_file(e)]
            c_ = [e for e in idx.files_by_sha256(n.circuit_sha256) if reader.local_file(e)]
            out.append((n, g[0], c_[0]))
    return out


def role_error(named, dist, width, law):
    """How far a logical circuit's distribution is from what its role says, as a number: the worst layout or the mass
    outside them (law), the parity's distance from the law's (coherence), 1 less the likeliest outcome (known answer)."""
    if named.role == "known-answer":
        return 1 - max(dist)
    if named.role == "law":
        worst = max(abs(dist[sum(1 << q for q in Y)] - w / law.den) for Y, w in zip(law.layouts, law.weights))
        return max(worst, sum(p for o, p in enumerate(dist) if o.bit_count() != law.N))
    letter, a, b = p2_hold.coherence_pair(named.basis, width)
    return abs(p2_hold.parity(dist, a, b) - float(law.observables[f"{letter}{a}{letter}{b}"]))


def test_the_124_references_are_12_gate_lists_and_4_logical_circuits_each_held_far_inside_the_tolerance():
    """Every carried gate list of v0, held as step 7 holds it, (a) against its logical circuit over all 2^16 outcomes and
    (b) its logical circuit against its role: the worst of either, over the 12, is below 1e-14, ten thousand times inside
    the hold's 1e-10 (the design measured 5.4e-17 for (a), and 5e-15 for a coherence's parity)."""
    crate, md = S.built("ibm")[0], S.metadata("ibm")
    law = S.law()
    refs = references(crate, md)
    assert len(refs) == 124 and len({n.role for n, _, _ in refs}) == 3
    gates = {g["sha256"]: (n, g, c) for n, g, c in refs}
    assert len(gates) == 12 and len({c["sha256"] for _, _, c in refs}) == 4
    p2_sim.clear()
    worst_a = worst_b = 0.0
    for digest, (n, g, c) in sorted(gates.items()):
        width, dist_g = p2_sim.gate_list_distribution(p1_decode.crate_file(crate, g, "the gate list"))
        circuit = p2_sim.read_qasm(p1_decode.crate_file(crate, c, "the logical circuit"))
        _, dist_l = p2_sim.logical(circuit)
        assert width == circuit.n == 16
        a = p2_hold.biggest_difference(dist_g, dist_l)
        b = role_error(n, dist_l, circuit.n, law)
        assert a < 1e-14 and b < 1e-14, (g["@id"], a, b)
        worst_a, worst_b = max(worst_a, a), max(worst_b, b)
    assert worst_a > 0 and worst_b > 0, "binary64 is not exact: a worst of 0 would be a hold that compared nothing"


def test_the_work_budget_counts_v0s_crates_a_tenth_of_it():
    """The work budget, 2^28 amplitude passes for each of steps 6 and 7 (docs/P2.md, "The work the hold may do"), on
    v0's crates. Step 7 counts the IBM crate's 31 Compiles and 124 references at 16 each and its 12 distinct pairs once
    each, 25,296,318 in all, a tenth of the budget; a device's four pairs cost 7,099,994 (marrakesh) to 10,714,714
    (fez), so the budget holds 25 to 37 of v0's device compiles. Step 6 counts the question's law circuit, 1,294,892,
    in each crate; the Atlas crate holds no Compile."""
    crate, md = S.built("ibm")[0], S.metadata("ibm")
    idx, law = Index(md), S.law()
    compiles = sorted(idx.of_type("qro:Compile"), key=lambda e: e["@id"])
    devices, seen, entries = {}, set(), 0
    for c in compiles:
        device = re.match(r"#compile-(ibm_[a-z]+)-", c["@id"]).group(1)
        for n in p2_hold.read_manifest(p1_decode.crate_file(crate, p2_measures.manifest_of(idx, c), "the manifest")):
            entries += 1
            pair = (n.gates_sha256, n.circuit_sha256, n.role, n.basis)
            if pair in seen:
                continue
            seen.add(pair)
            g = [e for e in idx.files_by_sha256(n.gates_sha256) if reader.local_file(e)][0]
            lc = [e for e in idx.files_by_sha256(n.circuit_sha256) if reader.local_file(e)][0]
            devices[device] = devices.get(device, 0) + p2_hold.pair_price(
                n, p1_decode.crate_file(crate, g, "the gate list"), p1_decode.crate_file(crate, lc, "the circuit"),
                None if n.role == "known-answer" else law)
    assert (len(compiles), entries, len(seen)) == (31, 124, 12)
    assert devices == {"ibm_fez": 10_714_714, "ibm_kingston": 7_479_130, "ibm_marrakesh": 7_099_994}
    assert [int(p2_hold.BUDGET / v) for v in sorted(devices.values())] == [37, 35, 25]
    count = p2_steps._step7(crate, md)
    assert count == sum(devices.values()) + 16 * (entries + len(compiles)) == 25_296_318
    assert 10 * count < p2_hold.BUDGET < 11 * count
    assert not Index(S.metadata("atlas")).of_type("qro:Compile")
    for kind in ("ibm", "atlas"):
        assert p2_steps._step6(S.built(kind)[0], S.metadata(kind)) == 1_294_892 < p2_law.BUDGET


def test_the_questions_law_circuit_lays_the_law_and_its_coherences_in_each_crate():
    """Step 6's hold of the law against the question's own circuit, on v0's source circuit in each crate: every
    layout, the mass outside them and both coherences within 1e-14 of the law file's."""
    law = S.law()
    for kind in ("ibm", "atlas"):
        crate, md = S.built(kind)[0], S.metadata(kind)
        idx = Index(md)
        e = idx.by_id[idx.by_id["#question"]["qro:lawCircuit"]["@id"]]
        data = p1_decode.crate_file(crate, e, "the law circuit")
        assert hashlib.sha256(data).hexdigest() == p2_law.SOURCE_CIRCUIT
        state, dist = p2_sim.logical(p2_sim.read_qasm(data))
        worst = max(abs(dist[sum(1 << q for q in Y)] - w / law.den) for Y, w in zip(law.layouts, law.weights))
        outside = sum(p for o, p in enumerate(dist) if o.bit_count() != law.N)
        pairs = [abs(p2_sim.pair_expectation(state, x, 0, 1) - 0.375) for x in "XY"]
        assert max(worst, outside, *pairs) < 1e-14, (kind, worst, outside, pairs)
        assert p2_hold.law_circuit_problem(data, law) is None


# -- the twin's files that P2 reads ---------------------------------------------------------------------------------------
BUNDLE = "2026-10-05/ibm/ibm_kingston/bundle"
READ = [SOURCE] + [f"{BUNDLE}/{n}" for n in ("manifest.json", "known-answer.qasm", "law.qasm", "coherence-xx.qasm",
                                             "coherence-yy.qasm", "known-answer.gates.json", "law.gates.json",
                                             "coherence-xx.gates.json", "coherence-yy.gates.json")]


def test_the_ten_twin_files_p2s_tests_read_are_moth_quantums_byte_for_byte():
    """tests/p2/p2_builder.py reads ten files of P1's twin (its TWIN_FILES): each is the file of the same path in
    moth-quantum's records at 3a73823, the checkout this stage reads (the adapter refuses any other), byte for byte."""
    S.built("ibm")
    twin = Path(S.ROOT, "tests", "p1", "data", "moth")
    assert len(READ) == 10
    for rel in READ:
        mine = (twin / "docs" / "records").joinpath(*rel.split("/")).read_bytes()
        theirs = (S.MOTH / "docs" / "records").joinpath(*rel.split("/")).read_bytes()
        assert mine == theirs, rel
