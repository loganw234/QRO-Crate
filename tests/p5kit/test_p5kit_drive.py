"""The driver's rules, on stand-ins, with the vendored runner and the real bundle checks (P5's design, items 6 and 7; qro_kit/
drive.py, submit.py, freeze.py, crate.py): the real route is refused `route-unsafe` for each condition it lacks and sends nothing;
S1 refuses a unit looked at twice before it makes anything; and a build that fails removes what it made and nothing else. The
child script (p5kit_standin.py) runs in the kit's interpreter; its one JSON document is read here.

Each scenario asserts that nothing was submitted (a counting `submit.send` that raises) and that the unit's directory is
byte-for-byte what `freeze` left."""
import json
from pathlib import Path

import pytest
from p5kit_support import ROOT, kit_run, no_network  # noqa: F401

pytestmark = pytest.mark.usefixtures("no_network")
SCRIPT = Path(__file__).resolve().parent / "p5kit_standin.py"


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    work = tmp_path_factory.mktemp("standin") / "work"
    p = kit_run([str(SCRIPT), str(ROOT), str(work)], timeout=900)
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")[-2000:]
    return json.loads(p.stdout.decode("utf-8").splitlines()[-1])


def test_the_unit_was_frozen_and_the_real_route_changed_nothing_and_sent_nothing(result):
    assert len(result["frozen"]["digest"]) == 64 and result["frozen"]["confirm"] == result["frozen"]["digest"][:12]
    assert result["sent after the real route"] == 0 and result["unit changed by the real route"] is False


@pytest.mark.parametrize("scene, where", [("no flag", "--route real"), ("no confirm", "--confirm"), ("wrong confirm", "--confirm"),
                                          ("no preflight", "preflight"), ("stale preflight", "preflight"),
                                          ("failing preflight", "preflight"), ("no service", "the service")])
def test_s7_each_missing_condition_of_the_real_route_is_route_unsafe(result, scene, where):
    got = result["real scenes"][scene]
    assert got["name"] == "route-unsafe" and got["where"] == where, got


@pytest.mark.parametrize("scene, rule", [("S2 seconds", "spend-usage"), ("S2 resource units", "spend-usage"),
                                         ("S5 plan", "plan-not-open"), ("S6 kind", "kind-mismatch")])
def test_s7_a_spend_rule_that_is_not_clear_is_route_unsafe_naming_the_rule(result, scene, rule):
    got = result["real scenes"][scene]
    assert got["name"] == "route-unsafe" and f"a spend rule is not clear: {rule}" in got["detail"], got


def test_s2_the_instance_is_asked_for_its_usage_and_nothing_else_first(result):
    assert result["S2 calls"] == ["usage"]


def test_even_with_every_condition_held_this_kit_tag_connects_to_nothing_and_submits_nothing(result):
    got = result["real scenes"]["all clear"]
    assert got["name"] == "route-unsafe" and "builds no connection to IBM" in got["detail"], got
    assert result["all clear calls"] == ["usage", "active_instance", "instances", "backend fake_kingston",
                                         "backend fake_marrakesh", "backend fake_fez"]


def test_a_dirty_tree_on_the_real_route_is_refused_before_the_fence(result):
    got = result["real scenes"]["dirty tree"]
    assert got["name"] == "kit-dirty" and got["where"] == "a.txt", got


def test_local_misuse_and_a_unit_frozen_by_another_commit_are_refused_and_change_nothing(result):
    scenes = result["local scenes"]
    assert "misuse" in scenes["unknown route"] and scenes["another commit"]["name"] == "kit-dirty"
    assert result["local after misuse"] == {"sent": 0, "unit changed": False}


def test_a_rule_that_refuses_the_first_job_leaves_no_run_directory_the_drive_made(result):
    assert result["local scenes"]["rule before the first job"] == {"name": "spend-unit", "where": "control",
                                                                   "detail": "a rule refuses"}
    assert result["local after a rule"] == {"sent": 0, "unit changed": False, "run dirs": []}


def test_s1_a_job_with_a_marker_is_refused_once_only_before_anything_is_made(result):
    got = result["local scenes"]["S1 once only"]
    assert got["name"] == "once-only" and got["where"] == "control-1" and "submitting.json exists" in got["detail"], got
    assert result["local S1"] == {"sent": 0, "unit unchanged": True, "run dirs": ["run"]}


def test_a_freeze_that_fails_removes_what_it_made_and_a_directory_that_was_there_stays(result):
    c = result["cleanup"]
    assert c["freeze raised"] == "the second bundle fails" and c["freeze made nothing that stays"] is True
    assert c["an existing empty directory stays, emptied"] is True


def test_a_freeze_into_a_directory_that_holds_anything_is_refused_and_touches_nothing(result):
    c = result["cleanup"]
    assert "misuse" in c["a non-empty directory is refused"] and c["and its file is untouched"] is True


def test_a_crate_build_that_fails_removes_its_own_files_and_leaves_what_another_put_there(result):
    c = result["cleanup"]
    assert c["a failed crate leaves only what another put there"] is True and c["its own files are gone"] is True
