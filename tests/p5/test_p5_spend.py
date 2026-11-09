"""The spend rules S1 to S7 (P5's design, item 6; qro_kit/submit.py), each shown on a stand-in: a stand-in runner, service,
backend and sampler that count every call. A refusal is raised BEFORE a job is sent, so each test asserts that the counter is
zero. (The same rules at the driver, with the vendored runner and a stand-in service, and no `-submitting.json` made, are
tests/p5kit/test_p5kit_drive.py's.) The real route is present and refusing: no way to connect to IBM is built."""
import json
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from types import SimpleNamespace

import pytest
from p5_support import no_link_left_behind, no_network  # noqa: F401

from qro import p5_unit as U
from qro.refusal import Refused
from qro_kit import submit

pytestmark = pytest.mark.usefixtures("no_network", "no_link_left_behind")
NOW = datetime(2026, 11, 8, 12, 0, 0, tzinfo=timezone.utc)
DIGEST = "ab" * 32


class Runner:
    """A stand-in for the vendored runner: S1's own check and the backend kind, counting every call."""

    def __init__(self, problems=()):
        self.problems, self.calls = list(problems), 0

    def once_only(self, manifest, job, out_dir, roots):
        self.calls += 1
        return self.problems

    @staticmethod
    def kind_from(is_ibm_backend, from_service, simulator):
        return "qpu" if (is_ibm_backend is True and from_service is True and simulator is False) else "simulator"


class Sampler:
    def __init__(self):
        self.runs = 0

    def run(self, pubs):
        self.runs += 1
        return "a job"


def manifest(cap=60, name="film-1", kind="qpu", backend="ibm_fez"):
    return {"jobs": [{"job": name, "max_execution_time": cap, "circuits": []}], "kind": kind, "backend": backend}


def refusal(fn, *args, **kwargs):
    with pytest.raises(Refused) as caught:
        fn(*args, **kwargs)
    return caught.value


# -- S1 ----------------------------------------------------------------------------------------------------------------------
def test_s1_a_job_already_submitted_is_refused_once_only(tmp_path):
    r = Runner(["once only: film-1 already has a line in the output directory"])
    got = refusal(submit.check_once, r, manifest(), "film-1", tmp_path)
    assert got.name == "once-only" and "already has a line" in got.detail and r.calls == 1
    submit.check_once(Runner(), manifest(), "film-1", tmp_path)


def test_s1_the_permit_asks_it_before_a_job_and_send_does_not_ask_it_again(tmp_path):
    r, s = Runner(["once only: x"]), Sampler()
    got = refusal(submit.permit, r, manifest(), "film-1", tmp_path, 0)
    assert got.name == "once-only" and s.runs == 0
    submit.send(r, s, [], manifest(), "film-1", tmp_path, 0)           # the runner's own check, before its marker, is S1 here
    assert s.runs == 1 and r.calls == 1


def test_s1_a_job_the_bundle_does_not_have_is_refused(tmp_path):
    assert refusal(submit.permit, Runner(), manifest(), "film-2", tmp_path, 0).name == "once-only"


# -- S2 ----------------------------------------------------------------------------------------------------------------------
USAGE = {"usage_remaining_seconds": 216, "usage_limit_ru": Fraction("10"), "usage_consumed_ru": Fraction("6.6")}


def test_s2_an_instance_that_covers_the_unit_passes():
    submit.check_usage(USAGE)
    submit.check_usage(dict(USAGE, usage_remaining_seconds=600))


@pytest.mark.parametrize("change", [{"usage_remaining_seconds": 215}, {"usage_consumed_ru": Fraction("6.67")},
                                    {"usage_remaining_seconds": 0}, {"usage_limit_ru": Fraction("3")}])
def test_s2_an_instance_that_does_not_is_refused_spend_usage(change):
    got = refusal(submit.check_usage, dict(USAGE, **change))
    assert got.name == "spend-usage"


def test_s2_the_boundaries_are_the_units_estimate_in_seconds_and_resource_units():
    assert U.UNIT_ESTIMATE == 216 and U.UNIT_RU == 216 * Fraction("0.015434")
    submit.check_usage({"usage_remaining_seconds": 216, "usage_limit_ru": U.UNIT_RU, "usage_consumed_ru": 0})
    assert refusal(submit.check_usage, {"usage_remaining_seconds": 216, "usage_limit_ru": U.UNIT_RU - Fraction("0.001"),
                                         "usage_consumed_ru": 0}).name == "spend-usage"


@pytest.mark.parametrize("usage", [{}, {"usage_remaining_seconds": 300}, {"usage_remaining_seconds": "lots", "usage_limit_ru": 1,
                                                                      "usage_consumed_ru": 0}, None])
def test_s2_a_usage_that_states_no_numbers_is_refused(usage):
    assert refusal(submit.check_usage, usage).name == "spend-usage"


# -- S3 ----------------------------------------------------------------------------------------------------------------------
def test_s3_the_ceiling_is_270_seconds_for_a_unit():
    assert U.CEILING == 270 == Fraction(5, 4) * 216
    submit.check_ceiling(0, "film")
    submit.check_ceiling(250, "film")                                   # 250 + 20 = 270
    assert refusal(submit.check_ceiling, 251, "film").name == "spend-unit"
    submit.check_ceiling(266, "control")                                # 266 + 4 = 270
    assert refusal(submit.check_ceiling, 267, "control").name == "spend-unit"
    assert refusal(submit.check_ceiling, Fraction(2501, 10), "film").name == "spend-unit"


def test_s3_a_charge_past_twice_the_estimate_stops_the_unit():
    submit.check_charge(8, "control")
    submit.check_charge(40, "film")
    assert refusal(submit.check_charge, 9, "control").name == "spend-unit"
    assert refusal(submit.check_charge, 41, "film").name == "spend-unit"
    assert refusal(submit.check_charge, Fraction(81, 2), "film").name == "spend-unit"


def test_s3_send_refuses_a_job_that_would_pass_the_ceiling_and_sends_nothing(tmp_path):
    s = Sampler()
    got = refusal(submit.send, Runner(), s, [], manifest(), "film-1", tmp_path, 251)
    assert got.name == "spend-unit" and s.runs == 0


# -- S4 ----------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("cap, kind", [(0, "film"), (301, "film"), (3, "film"), (19, "film"), (30, "film"), (3, "control"),
                                       (61, "film"), (16, "control"), (-1, "film"), (60.0, "film"), (True, "control"),
                                       ("60", "film"), (None, "film")])
def test_s4_a_cap_that_is_not_the_recipes_is_refused_spend_cap(cap, kind):
    assert refusal(submit.check_cap, cap, kind).name == "spend-cap"


def test_s4_the_recipes_caps_pass():
    submit.check_cap(15, "control")
    submit.check_cap(60, "film")
    assert U.CAPS == {"control": 15, "film": 60} and submit.MAX_CAP == 300 and U.JOB_ESTIMATE["film"] <= 60


def test_s4_send_refuses_a_job_whose_cap_is_not_the_recipes_and_sends_nothing(tmp_path):
    s = Sampler()
    for cap in (0, 301, 3):
        assert refusal(submit.send, Runner(), s, [], manifest(cap=cap), "film-1", tmp_path, 0).name == "spend-cap"
    assert s.runs == 0


# -- S5, S6 --------------------------------------------------------------------------------------------------------------------
def test_s5_only_the_open_plan_runs_a_free_tier_unit():
    submit.check_plan("open")
    for plan in ("pay-as-you-go", "premium", "Open", "", None):
        assert refusal(submit.check_plan, plan).name == "plan-not-open"


class Real:
    """A stand-in for an IBMBackend obtained from the service."""

    def __init__(self, name="ibm_fez", simulator=False):
        self.name, self._simulator = name, simulator

    def configuration(self):
        return SimpleNamespace(simulator=self._simulator)


class Fake:
    """A backend object that merely carries a device's name."""

    def __init__(self, name="ibm_fez"):
        self.name = name

    def configuration(self):
        return SimpleNamespace(simulator=False)


def test_s6_only_an_ibm_backend_from_the_service_is_a_qpu():
    m = manifest()
    submit.check_backend(Runner(), Real(), m, Real)
    got = refusal(submit.check_backend, Runner(), Fake(), m, Real)
    assert got.name == "kind-mismatch" and "'simulator'" in got.detail
    assert refusal(submit.check_backend, Runner(), Real(simulator=True), m, Real).name == "kind-mismatch"
    assert refusal(submit.check_backend, Runner(), Real("ibm_kingston"), m, Real).name == "kind-mismatch"
    assert refusal(submit.check_backend, Runner(), Real(), m, Real, from_service=False).name == "kind-mismatch"


def test_s6_a_simulator_unit_takes_a_fake_backend_by_kind_and_name():
    submit.check_backend(Runner(), Fake("fake_fez"), manifest(kind="simulator", backend="fake_fez"), Real, from_service=False)


# -- S7 ----------------------------------------------------------------------------------------------------------------------
def write_preflight(unit_dir, *, unit=DIGEST, holds="holds", at=NOW - timedelta(hours=1), name=None):
    folder = unit_dir.parent / "preflight"
    folder.mkdir(exist_ok=True)
    stamp = at.strftime("%Y-%m-%dT%H:%M:%SZ")
    safe = at.strftime("%Y%m%dT%H%M%SZ")            # a file name has no colon on Windows
    (folder / (name or f"{safe}.json")).write_bytes(json.dumps(
        {"format": submit.PREFLIGHT_FORMAT, "unit_sha256": unit, "holds": holds, "at": stamp}).encode("ascii"))


def clear():
    return None


def dirty():
    raise Refused("kit-dirty", "a.txt", "the bytes on disk are not HEAD's blob for this path")


def unclear():
    raise Refused("spend-usage", "usage()", "215 s remain")


def fence(unit_dir, **kw):
    args = dict(flag=True, confirm=DIGEST[:12], tree=clear, now=NOW, rules=clear)
    args.update(kw)
    return submit.fence(unit_dir, DIGEST, **args)


def test_s7_every_condition_held_passes_the_fence(tmp_path):
    unit = tmp_path / "records" / "unit"
    unit.mkdir(parents=True)
    write_preflight(unit)
    fence(unit)


@pytest.mark.parametrize("change, where", [
    ({"flag": False}, "--route real"), ({"flag": None}, "--route real"), ({"flag": 1}, "--route real"),
    ({"confirm": None}, "--confirm"), ({"confirm": "ab" * 5}, "--confirm"), ({"confirm": DIGEST}, "--confirm"),
    ({"confirm": "AB" * 6}, "--confirm"), ({"confirm": "cd" * 6}, "--confirm"),
    ({"tree": dirty}, "a.txt"), ({"rules": unclear}, "usage()")],
    ids=["no flag", "flag None", "flag 1", "no confirm", "short confirm", "the whole digest", "upper case", "another unit's",
         "a dirty tree", "a spend rule"])
def test_s7_each_missing_condition_is_route_unsafe(tmp_path, change, where):
    unit = tmp_path / "records" / "unit"
    unit.mkdir(parents=True)
    write_preflight(unit)
    got = refusal(fence, unit, **change)
    assert got.name == "route-unsafe" and got.where == where


@pytest.mark.parametrize("record, why", [
    (None, "no pre-flight record"), ({"at": NOW - timedelta(hours=24)}, "not under 24 hours old"),
    ({"at": NOW - timedelta(days=3)}, "not under 24 hours old"), ({"holds": "withheld"}, "does not hold"),
    ({"unit": "cd" * 32}, "no pre-flight record of this unit")], ids=["none", "24 hours", "3 days", "not holding", "another unit"])
def test_s7_a_preflight_that_is_missing_stale_failing_or_another_units_is_route_unsafe(tmp_path, record, why):
    unit = tmp_path / "records" / "unit"
    unit.mkdir(parents=True)
    if record is not None:
        write_preflight(unit, **record)
    got = refusal(fence, unit)
    assert got.name == "route-unsafe" and got.where == "preflight" and why in got.detail


def test_s7_a_preflight_just_under_a_day_old_that_holds_passes(tmp_path):
    unit = tmp_path / "records" / "unit"
    unit.mkdir(parents=True)
    write_preflight(unit, at=NOW - timedelta(hours=23, minutes=59))
    fence(unit)


def test_s7_a_preflight_dated_ahead_of_now_is_refused_and_never_the_newest(tmp_path):
    """The first verifier, round 1, D1: `now - at >= 24 hours` took a record of 2099 for ever, and a holding record dated
    ahead became 'the newest' and hid an older failing one. The rule is 0 <= now - at < 24 hours."""
    unit = tmp_path / "a" / "records" / "unit"
    unit.mkdir(parents=True)
    write_preflight(unit, at=NOW.replace(year=2099))
    ok, why = submit.preflight_ok(unit, DIGEST, NOW)
    assert not ok and "ahead of now" in why
    got = refusal(fence, unit)
    assert got.name == "route-unsafe" and got.where == "preflight" and "ahead of now" in got.detail
    # an older failing record beside a future holding one: the future one is not the newest, so the failing one decides
    unit = tmp_path / "b" / "records" / "unit"
    unit.mkdir(parents=True)
    write_preflight(unit, at=NOW - timedelta(hours=5), holds="withheld")
    write_preflight(unit, at=NOW.replace(year=2099), holds="holds")
    ok, why = submit.preflight_ok(unit, DIGEST, NOW)
    assert not ok and "does not hold" in why
    assert refusal(fence, unit).where == "preflight"
    # a future record does not hide an older holding one either, and a stale one beside a future one is stale
    unit = tmp_path / "c" / "records" / "unit"
    unit.mkdir(parents=True)
    write_preflight(unit, at=NOW - timedelta(hours=2), holds="holds")
    write_preflight(unit, at=NOW.replace(year=2099), holds="withheld")
    assert submit.preflight_ok(unit, DIGEST, NOW) == (True, "")
    unit = tmp_path / "e" / "records" / "unit"                # a record only an hour ahead is ahead too
    unit.mkdir(parents=True)
    write_preflight(unit, at=NOW - timedelta(hours=5), holds="withheld")
    write_preflight(unit, at=NOW + timedelta(hours=1), holds="holds")
    ok, why = submit.preflight_ok(unit, DIGEST, NOW)
    assert not ok and "does not hold" in why
    unit = tmp_path / "d" / "records" / "unit"
    unit.mkdir(parents=True)
    write_preflight(unit, at=NOW - timedelta(days=3), holds="holds")
    write_preflight(unit, at=NOW.replace(year=2099), holds="holds")
    ok, why = submit.preflight_ok(unit, DIGEST, NOW)
    assert not ok and "not under 24 hours old" in why


def test_s7_a_preflight_at_the_edges_of_the_window(tmp_path):
    unit = tmp_path / "records" / "unit"
    unit.mkdir(parents=True)
    write_preflight(unit, at=NOW)                                       # now - at == 0: taken
    assert submit.preflight_ok(unit, DIGEST, NOW) == (True, "")
    assert submit.preflight_ok(unit, DIGEST, NOW - timedelta(seconds=1))[0] is False      # one second ahead: refused
    assert submit.preflight_ok(unit, DIGEST, NOW + timedelta(hours=24) - timedelta(seconds=1)) == (True, "")
    assert submit.preflight_ok(unit, DIGEST, NOW + timedelta(hours=24))[0] is False      # 24 hours exactly: refused


def test_s7_the_newest_preflight_of_the_unit_decides(tmp_path):
    unit = tmp_path / "records" / "unit"
    unit.mkdir(parents=True)
    write_preflight(unit, at=NOW - timedelta(hours=5), holds="holds")
    write_preflight(unit, at=NOW - timedelta(hours=2), holds="withheld")
    assert refusal(fence, unit).where == "preflight"


def test_s7_a_preflight_record_that_is_unreadable_or_of_another_format_counts_for_nothing(tmp_path):
    unit = tmp_path / "records" / "unit"
    unit.mkdir(parents=True)
    folder = unit.parent / "preflight"
    folder.mkdir()
    (folder / "20261108T110000Z.json").write_bytes(b"not json")
    (folder / "20261108T110001Z.json").write_bytes(json.dumps({"format": "other/v1", "unit_sha256": DIGEST}).encode())
    assert refusal(fence, unit).where == "preflight"


def test_s7_the_fence_runs_its_conditions_in_the_designs_order(tmp_path):
    unit = tmp_path / "records" / "unit"
    unit.mkdir(parents=True)
    got = refusal(fence, unit, flag=False, confirm=None, tree=dirty, rules=unclear)       # nothing holds: the first speaks
    assert got.where == "--route real"
    got = refusal(fence, unit, confirm=None, tree=dirty, rules=unclear)
    assert got.where == "--confirm"
    got = refusal(fence, unit, tree=dirty, rules=unclear)
    assert got.where == "preflight"


def test_the_real_route_builds_no_connection_to_ibm():
    """P5.1: the module names no service class and no connect call; the real route's fence has `rules` handed to it."""
    import ast
    from pathlib import Path
    text = Path(submit.__file__).read_text(encoding="utf-8")
    names = {n.id for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Name)} | \
        {n.attr for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Attribute)}
    assert not names & {"QiskitRuntimeService", "connect", "save_account", "account"}


# -- send, the one place a sampler runs --------------------------------------------------------------------------------------------
def test_send_runs_a_job_whose_rules_are_all_clear_exactly_once(tmp_path):
    s = Sampler()
    assert submit.send(Runner(), s, ["pub"], manifest(), "film-1", tmp_path, 0, route_rules=clear) == "a job"
    assert s.runs == 1


def test_send_asks_the_routes_rules_first_and_a_refusal_there_sends_nothing(tmp_path):
    s, r = Sampler(), Runner()
    got = refusal(submit.send, r, s, [], manifest(), "film-1", tmp_path, 0, route_rules=unclear)
    assert got.name == "spend-usage" and s.runs == 0 and r.calls == 0
