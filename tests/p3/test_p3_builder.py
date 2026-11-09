"""The builder's crates are valid crates (tests/p3/p3_builder.py; P3's design, item 12): the checker's steps 1 to 8
accept them, with a stand-in step 9 that holds nothing (the builder is no generator), P1's and P2's steps among them,
the compile's variant gate list held by the exact hold, and round 2's shapes (another program, route and decode, a
simulator, the mirror bit order, the known answers that leave out a qubit of the pair); so the tests that feed them to
the computation feed it what the checker accepts."""
import pytest

import p3_builder as B
import p3_support as S
from qro import checker
from qro.refusal import Refused

T = "2026-11-01T10:"


@pytest.fixture(autouse=True)
def stand_in(monkeypatch):
    S.builder_generator(monkeypatch)


def test_a_crate_of_two_devices_with_a_variant_compile_passes_steps_1_to_8(tmp_path):
    k = B.Bundle("ibm_kingston", "morning", [B.ka(start=f"{T}00:00Z"), B.law(start=f"{T}01:00Z"),
                                             B.coherence(start=f"{T}05:00Z", commit="a" * 40)])
    f = B.Bundle("ibm_fez", "morning", [B.control(start=f"{T}00:30Z"), B.law(start=f"{T}02:00Z", five=30),
                                        B.law("law-2", submitted=f"{T}03:00Z"), B.coherence(start=f"{T}06:00Z")],
                 gates={"law": 1, "coherence-xx": 1})
    s = B.Bundle("fake_fez", "morning", [B.ka(), B.law()], kind="simulator", held=False)
    checker.load()
    md = checker.check(B.build(tmp_path, [k, f, s]))
    holds = [e for e in md["@graph"] if e["@id"].startswith("#hold-")]
    assert sorted(h["qro:exactHold"] for h in holds) == ["holds", "withheld"], "fez's complement is not carried"


def test_a_crate_of_another_program_route_decode_and_bit_order_passes_steps_1_to_8(tmp_path):
    """Round 2's shapes: a program and a route of fez's own, the decode its manifest names, a simulator, raw results in
    the mirror order its Decodes name, and the known answers that leave out qubit 0 or 1."""
    k = B.Bundle("ibm_kingston", "morning", [
        B.Job("control", ("known-answer", "without-0"), (B.ka_counts(), B.pattern_counts("without-0")), f"{T}00:00Z"),
        B.coherence(start=f"{T}01:00Z")], order="lsb-first")
    f = B.Bundle("ibm_fez", "morning", [
        B.Job("control", ("known-answer", "without-1"), (B.ka_counts(), B.pattern_counts("without-1")), f"{T}00:30Z"),
        B.law(start=f"{T}02:00Z")], program="estimator", route="ibm-batch", decode="quantum_film.ibm.decode/v2")
    s = B.Bundle("fake_fez", "morning", [B.ka(), B.law()], kind="simulator")
    checker.load()
    md = checker.check(B.build(tmp_path, [k, f, s]))
    orders = {e["qro:bitOrder"] for e in md["@graph"] if e["@id"].startswith("#decode-ibmkingston")}
    assert orders == {"lsb-first"}
    assert any(e["@id"] == "#program-estimator" for e in md["@graph"])


def test_a_crate_with_a_broken_known_answer_is_refused_so_the_steps_do_hold_it(tmp_path):
    bad = B.Job("known-answer", ("known-answer",), ({B.KA[:-1]: 60, B.KA: 4},), f"{T}00:00Z")
    checker.load()
    with pytest.raises(Refused) as r:
        checker.check(B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", [bad, B.law()])]))
    assert r.value.name == "known-answer"
