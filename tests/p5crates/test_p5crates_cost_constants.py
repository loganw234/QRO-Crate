"""The cost constants against v0's 65 jobs (P5's design, items 1 and 6; qro/p5_unit.py's COST_MODELS, JOB_ESTIMATE, UNIT_ESTIMATE
and RU_PER_SECOND): recomputed here, in exact arithmetic, from the 65 jobs' metrics and records in moth-quantum at 3a73823, as
the design's cost_models.py computed them. v0's charges sum to 353 s; model (a) is 9/24576 s a shot (the largest charge of
the 24,576-shot jobs, 9 s), (b) the least-squares line of charge on shots, (c) 2 s and 0.35 ms a shot; the resource units are
5.448135 over the 353 s."""
import json
import math
from fractions import Fraction
from pathlib import Path

import pytest
from p5crates_support import committed, git, moth_root, no_network  # noqa: F401

from qro import p5_unit as U

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.usefixtures("no_network")


@pytest.fixture(scope="module")
def v0():
    root = moth_root()
    names = git(root, "ls-tree", "-r", "--name-only", "HEAD", "docs/records/2026-10-05/ibm"  # moth-quantum's tree
                ).decode().splitlines()
    points = []
    for rel in sorted(n for n in names if n.endswith("-metrics.json")):
        usage = json.loads(committed(root, rel))["metrics"]["usage"]
        shots = 0
        prefix = rel[:-len("-metrics.json")] + "-pub"
        for rec in (n for n in names if n.startswith(prefix)):
            shots += sum(c for _, c in json.loads(committed(root, rec))["counts"])
        points.append((shots, usage["qpu_charge_time_seconds"], Fraction(str(usage["value"]))))
    return points


def probe_usage():
    """The account's usage after v0's 65 jobs, as IBM's service reported it on 2026-10-14 (this repository's records)."""
    text = (ROOT / "records" / "2026-10-14" / "ibm-dryrun-probe" / "probe.json").read_text(encoding="ascii")
    kept = json.loads(text)["usage"]["kept"]
    return kept["usage_consumed_seconds"], Fraction(str(kept["usage_consumed_ru"]))


def test_v0_is_65_jobs_charged_353_seconds(v0):
    assert len(v0) == 65
    assert sum(q for _s, q, _ru in v0) == U.V0_CHARGE_SECONDS == 353


def test_the_account_consumed_5_448135_resource_units_over_those_353_seconds_and_the_jobs_values_agree_to_their_rounding(v0):
    seconds, ru = probe_usage()
    assert seconds == 353 == U.V0_CHARGE_SECONDS and ru == U.V0_RESOURCE_UNITS == Fraction("5.448135")
    total = sum(r for _s, _q, r in v0)
    assert abs(total - ru) < 65 * Fraction(5, 10 ** 5)           # each job's value is IBM's, to four decimals


def test_the_resource_unit_rate_is_the_accounts_ratio_to_six_places():
    seconds, ru = probe_usage()
    assert abs(ru / seconds - U.RU_PER_SECOND) < Fraction(1, 2 * 10 ** 6) and U.RU_PER_SECOND == Fraction("0.015434")


def test_model_a_is_the_largest_24576_shot_charge_per_shot(v0):
    law = [q for s, q, _ru in v0 if s == 24576]
    assert law and Fraction(max(law), 24576) == Fraction(9, 24576) == U.COST_MODELS["a"](1)


def test_model_b_is_the_least_squares_line_to_the_decimals_the_design_states(v0):
    n = len(v0)
    mx, my = Fraction(sum(s for s, *_x in v0), n), Fraction(sum(q for _s, q, _ru in v0), n)
    slope = sum((s - mx) * (q - my) for s, q, _ru in v0) / sum((s - mx) ** 2 for s, *_x in v0)
    icept = my - slope * mx
    assert round(float(icept), 4) == 1.6871 and round(float(slope), 8) == 0.00029741
    assert abs(icept - Fraction("1.6871")) < Fraction(5, 10 ** 5) and abs(slope - Fraction("0.00029741")) < Fraction(5, 10 ** 9)
    assert U.COST_MODELS["b"](0) == Fraction("1.6871") and U.COST_MODELS["b"](10 ** 6) - U.COST_MODELS["b"](0) == \
        Fraction("0.00029741") * 10 ** 6


def test_the_estimates_are_the_models_rounded_up_a_job_and_the_units_are_180_180_and_216(v0):
    n = len(v0)
    mx, my = Fraction(sum(s for s, *_x in v0), n), Fraction(sum(q for _s, q, _ru in v0), n)
    slope = sum((s - mx) * (q - my) for s, q, _ru in v0) / sum((s - mx) ** 2 for s, *_x in v0)
    icept = my - slope * mx
    models = {"a": lambda s: Fraction(9, 24576) * s, "b": lambda s: icept + slope * s, "c": lambda s: 2 + Fraction(35, 100000) * s}
    got = {m: (math.ceil(f(4096)), math.ceil(f(49152))) for m, f in models.items()}
    assert got == {"a": (2, 18), "b": (3, 17), "c": (4, 20)}
    assert {m: 9 * sum(c) for m, c in got.items()} == {"a": 180, "b": 180, "c": 216}
    assert U.estimates("control") == {m: c[0] for m, c in got.items()} and U.estimates("film") == {m: c[1] for m, c in got.items()}
    assert U.UNIT_ESTIMATE == 216 and U.JOB_ESTIMATE == {"control": 4, "film": 20}


def test_the_unit_costs_216_seconds_or_about_3_33_resource_units():
    assert abs(float(U.UNIT_RU) - 3.33) < 0.01 and U.UNIT_RU == 216 * U.RU_PER_SECOND


def test_a_float_ceiling_could_move_a_charge_and_the_arithmetic_here_is_exact():
    """The design's finding: law_rate * 49152 is exactly 18 only if law_rate is exactly 9/24576; in float it is not
    necessarily, and a ceiling of it could be 19. The constants are Fractions."""
    assert U.COST_MODELS["a"](49152) == 18 and math.ceil(U.COST_MODELS["a"](49152)) == 18
