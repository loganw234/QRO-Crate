"""The recipe and its costs (P5's design, item 1; qro/p5_unit.py): 18 jobs, 479,232 shots, K M F three times; the control and
film jobs' PUBs; the digest and the divisor; the three cost models in exact arithmetic, 180 and 216 s; and the spend constants
Logan approved (270 s a unit, 15 s and 60 s a job)."""
import ast
import json
from fractions import Fraction
from pathlib import Path

import pytest
from p5_support import ROOT, no_network  # noqa: F401

from qro import p5_unit as U

pytestmark = pytest.mark.usefixtures("no_network")


def test_the_unit_is_18_jobs_and_479232_shots():
    jobs = [j for _, _, _, pubs in U.jobs_of_device() for j in pubs]
    per_device = sum(s for _n, _k, _p, pubs in U.jobs_of_device() for *_x, s in pubs)
    assert len(U.job_order()) == 18 and len(U.jobs_of_device()) == 6 and len(jobs) == 5 * 3
    assert 3 * per_device == 479_232 == U.TOTAL_SHOTS
    assert 9 * (2 * 2048 + 3 * 16384) == 479_232


def test_the_order_is_pass_by_pass_device_by_device_a_control_job_and_then_a_film_job():
    order = U.job_order()
    assert [d for _p, d, _k in order] == [0, 0, 1, 1, 2, 2] * 3
    assert [k for _p, _d, k in order] == ["control", "film"] * 9
    assert [p for p, _d, _k in order] == [1] * 6 + [2] * 6 + [3] * 6
    assert U.DEVICE_SETS["qpu"] == ("ibm_kingston", "ibm_marrakesh", "ibm_fez")
    assert U.DEVICE_SETS["simulator"] == ("fake_kingston", "fake_marrakesh", "fake_fez")


def test_a_control_job_has_the_known_answer_and_its_complement_and_a_film_job_the_law_and_the_pair():
    assert U.CIRCUITS["control"] == (("known-answer", "known-answer", "Z" * 16), ("known-complement", "known-answer", "Z" * 16))
    assert [n for n, _r, _b in U.CIRCUITS["film"]] == ["law", "coherence-xx", "coherence-yy"]
    assert [b for _n, _r, b in U.CIRCUITS["film"]][1:] == ["XX" + "Z" * 14, "YY" + "Z" * 14]
    assert U.KNOWN_ANSWER == (0, 1, 3, 7, 12) and len(U.KNOWN_COMPLEMENT) == 11
    assert sorted(U.KNOWN_ANSWER + U.KNOWN_COMPLEMENT) == list(range(16))
    assert U.SHOTS == {"control": 2048, "film": 16384} and U.CAPS == {"control": 15, "film": 60} and U.CEILING == 270


def test_each_job_names_its_pubs_in_order():
    for name, kind, p, pubs in U.jobs_of_device():
        assert name == f"{kind}-{p}" and [i for i, *_ in pubs] == list(range(len(pubs)))
        assert {s for *_x, s in pubs} == {U.SHOTS[kind]}                  # one shot count a job


def test_the_costs_are_exact_and_reproduce_the_designs_numbers():
    assert U.estimates("control") == {"a": 2, "b": 3, "c": 4} and U.estimates("film") == {"a": 18, "b": 17, "c": 20}
    assert U.JOB_ESTIMATE == {"control": 4, "film": 20} and U.UNIT_ESTIMATE == 216
    assert 9 * (2 + 18) == 180 and 9 * (3 + 17) == 180
    assert U.COST_MODELS["a"](49152) == 18 and isinstance(U.COST_MODELS["a"](1), Fraction)
    assert isinstance(U.COST_MODELS["b"](49152), Fraction) and isinstance(U.COST_MODELS["c"](49152), Fraction)
    assert U.RU_PER_SECOND == Fraction("0.015434") and U.UNIT_RU == 216 * Fraction("0.015434")
    assert abs(float(U.V0_RESOURCE_UNITS / U.V0_CHARGE_SECONDS) - float(U.RU_PER_SECOND)) < 1e-6


def test_the_cost_arithmetic_uses_no_float():
    """The cost constants and models are Fractions: no float literal in the functions that compute them."""
    tree = ast.parse((ROOT / "qro" / "p5_unit.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError(f"a float literal {node.value} at line {node.lineno}")


def test_the_recipe_digest_is_a_function_of_the_recipe_and_the_divisor():
    d1 = U.recipe_sha256()
    assert d1 == U.recipe_sha256(1) and len(d1) == 64
    assert U.recipe_sha256(128) != d1 and U.recipe_sha256(64) != U.recipe_sha256(128)
    body = json.dumps(U.recipe(), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    import hashlib
    assert hashlib.sha256(body).hexdigest() == d1
    assert U.recipe(128)["shots_divisor"] == 128 and U.RECIPE["jobs"][0]["circuits"][0]["shots"] == 2048
    assert U.recipe(128)["jobs"][1]["circuits"][0]["shots"] == 128


@pytest.mark.parametrize("bad", [0, -1, 3, 4096, 2.0, "2", True])
def test_a_divisor_must_divide_both_shot_counts(bad):
    with pytest.raises(ValueError):
        U.recipe(bad)


def test_the_options_are_the_recipes_and_state_every_switch():
    assert U.OPTIONS == {"dynamical_decoupling": {"enable": False}, "execution": {"init_qubits": True},
                         "twirling": {"enable_gates": False, "enable_measure": False}}


def test_the_source_circuit_text_is_derived_as_quantum_film_derives_it():
    src = (ROOT / "tests" / "p1" / "data" / "moth" / "docs" / "records" / "2026-09-25" / "p3"
           / "circuit-ed767c01bd4b851d.qasm").read_text(encoding="ascii")
    law = U.logical_qasm("law", src)
    assert law.startswith('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[16];\ncreg meas[16];\nx q[0];')
    assert law.endswith("measure q[15] -> meas[15];\n") and "barrier q[0],q[1]" in law
    assert "h q[0];\nh q[1];\nbarrier" in U.logical_qasm("coherence-xx", src)
    assert "sdg q[0];\nh q[0];\nsdg q[1];\nh q[1];\nbarrier" in U.logical_qasm("coherence-yy", src)
    comp = U.logical_qasm("known-complement", src)
    assert [ln for ln in comp.split("\n") if ln.startswith("x q[")] == [f"x q[{q}];" for q in U.KNOWN_COMPLEMENT]
    with pytest.raises(ValueError):
        U.logical_qasm("nothing", src)
    with pytest.raises(ValueError):
        U.logical_qasm("law", "not qasm\n")


@pytest.mark.parametrize("name, ok", [("control-1", True), ("film-3", True), ("film-4", False), ("film-0", False),
                                       ("film-01", False), ("law-1", False), ("film", False), ("control-٣", False)])
def test_a_job_name_parses_or_is_refused(name, ok):
    if ok:
        assert U.parse_job_name(name) == (name.split("-")[0], int(name.split("-")[1]))
    else:
        with pytest.raises(ValueError):
            U.parse_job_name(name)


def test_the_module_imports_nothing_of_the_kit_or_a_third_party():
    tree = ast.parse((Path(U.__file__)).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module.split(".")[0])
    stdlib = {"hashlib", "json", "math", "os", "sys", "dataclasses", "fractions", "pathlib", "qro"}
    assert names <= stdlib, sorted(names - stdlib)
