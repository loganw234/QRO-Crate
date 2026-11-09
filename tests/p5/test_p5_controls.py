"""P5's four controls (study QRO-0, section 11; controls/plants_p5.py): each comes out as the study says through the
controls' runner and the plant command, its twin is accepted, and `kit-dirty` is refused before anything is made or any
service is called. The kit's command line: its misuse, and its refusals as lines."""
import subprocess
import sys

import pytest
from p5_support import ROOT, no_link_left_behind, no_network, twin  # noqa: F401

from controls import plants_p5 as P
from controls import registry, run
from qro import checker, p5_unit as U
from qro.refusal import Refused
from qro_kit import __main__ as cli
from qro_kit import crate, drive, freeze

pytestmark = pytest.mark.usefixtures("no_network", "no_link_left_behind")
checker.load()                                   # every parcel's steps, whichever test runs first
CONTROLS = ("unit-known-answer", "unit-incomplete", "not-interleaved", "kit-dirty")


def test_the_four_rows_are_p5s_and_have_plants_statements_and_twins():
    assert {c.name for c in registry.CONTROLS if c.owner == "P5"} == set(CONTROLS)
    assert set(P.PLANTS) == set(CONTROLS) and set(P.STATEMENTS) == set(P.TWINS) == {"unit-incomplete", "not-interleaved"}
    assert set(registry.plants()) >= set(CONTROLS)
    assert registry.sentence(registry.CONTROL["unit-incomplete"]) == "unit-incomplete"
    assert registry.sentence(registry.CONTROL["not-interleaved"]) == U.NOT_INTERLEAVED


def test_each_control_comes_out_as_section_11_says():
    for name in CONTROLS:
        c = registry.CONTROL[name]
        got, refusal, where = run.outcome(name)
        assert (got, refusal) == (c.expected, c.refusal), (name, got, refusal, where)


def test_the_unit_known_answer_is_refused_by_the_checker_at_the_decode_with_the_pub_named(tmp_path):
    with pytest.raises(Refused) as caught:
        checker.check(P.unit_known_answer(tmp_path))
    r = caught.value
    assert r.name == "known-answer" and r.where.startswith("#decode-dryrun-") and "does not hold the known answer" in r.detail
    assert "has 0 of 16 shots" in r.detail and "#pub-dryrun-" in r.detail


def test_the_twin_of_each_states_row_is_accepted_and_says_nothing(tmp_path):
    for name, make in P.TWINS.items():
        crate_dir = make(tmp_path / name)
        checker.check(crate_dir)
        assert P.STATEMENTS[name](crate_dir) == frozenset()


def test_the_states_rows_are_met_when_their_sentence_is_in_the_set_and_the_twins_is_not(tmp_path):
    for name in ("unit-incomplete", "not-interleaved"):
        planted = P.PLANTS[name](tmp_path / name)
        want = registry.sentence(registry.CONTROL[name])
        assert want in P.STATEMENTS[name](planted)


def test_kit_dirty_is_the_plants_own_refusal_and_the_plant_command_writes_it(tmp_path):
    with pytest.raises(Refused) as caught:
        P.kit_dirty(tmp_path)
    assert caught.value.name == "kit-dirty" and caught.value.where == "kit.py"
    p = subprocess.run([sys.executable, "-m", "controls.plant", "kit-dirty"], capture_output=True, cwd=ROOT)
    assert p.returncode == 1 and p.stdout.startswith(b"REFUSED kit-dirty at kit.py:"), (p.stdout, p.stderr[-300:])


def test_the_plant_command_refuses_the_unit_known_answer_and_accepts_nothing_it_should_not():
    p = subprocess.run([sys.executable, "-m", "controls.plant", "unit-known-answer"], capture_output=True, cwd=ROOT)
    assert p.returncode == 1 and p.stdout.startswith(b"REFUSED known-answer at "), (p.stdout, p.stderr[-300:])
    p = subprocess.run([sys.executable, "-m", "controls.plant", "unit-incomplete"], capture_output=True, cwd=ROOT)
    assert p.returncode == 0 and p.stdout.startswith(b"ACCEPTED "), (p.stdout, p.stderr[-300:])


# -- kit-dirty is first of everything, before anything is made or any service is called ----------------------------------------
def dirty():
    raise Refused("kit-dirty", "a.txt", "the bytes on disk are not HEAD's blob for this path")


class Service:
    def __init__(self):
        self.calls = 0

    def __getattr__(self, name):
        self.calls += 1
        raise AssertionError(f"the service was called: {name}")


def test_freeze_with_a_dirty_tree_makes_nothing(tmp_path):
    out = tmp_path / "work"
    with pytest.raises(Refused) as caught:
        freeze.freeze(out, tree=dirty)
    assert caught.value.name == "kit-dirty" and not out.exists()


def test_crate_with_a_dirty_tree_makes_nothing(tmp_path):
    unit = tmp_path / "unit"
    unit.mkdir()
    out = tmp_path / "crate"
    with pytest.raises(Refused) as caught:
        crate.build(unit, out, tree=dirty)
    assert caught.value.name == "kit-dirty" and not out.exists()


@pytest.mark.parametrize("route", ["local", "real"])
def test_drive_with_a_dirty_tree_calls_no_service_and_makes_nothing(tmp_path, route):
    unit, service = tmp_path / "unit", Service()
    unit.mkdir()
    with pytest.raises(Refused) as caught:
        drive.drive(unit, route=route, flag=True, confirm="0" * 12, tree=dirty, service=service)
    assert caught.value.name == "kit-dirty" and service.calls == 0 and list(unit.iterdir()) == []


def test_the_command_line_writes_a_dirty_tree_as_a_refusal_line(tmp_path):
    for argv in (["freeze", "--route", "local", "--out", str(tmp_path / "w")],
                 ["drive", str(tmp_path), "--route", "real", "--confirm", "0" * 12], ["crate", str(tmp_path), "--out",
                                                                                        str(tmp_path / "c")]):
        out, err = tmp_path / "o", tmp_path / "e"
        for p in (out, err):
            p.unlink(missing_ok=True)
        with open(out, "wb") as o, open(err, "wb") as e:
            code = cli.main(argv, out=o.fileno(), err=e.fileno(), tree=dirty)
        assert code == 1 and err.read_bytes() == b""
        assert out.read_bytes() == b"REFUSED kit-dirty at a.txt: the bytes on disk are not HEAD's blob for this path\n"


@pytest.mark.parametrize("argv", [[], ["bogus"], ["freeze"], ["freeze", "--out"], ["freeze", "--route", "local"],
                                   ["freeze", "--out", "a", "--out", "b"], ["freeze", "--bogus", "x", "--out", "a"],
                                   ["freeze", "x", "--out", "a"], ["drive"], ["drive", "a", "b"], ["crate", "a"],
                                   ["crate", "--out", "a"], ["drive", "a", "--out", "b"]])
def test_misuse_of_the_command_line_is_exit_2_with_the_usage(tmp_path, argv):
    out, err = tmp_path / "o", tmp_path / "e"
    with open(out, "wb") as o, open(err, "wb") as e:
        code = cli.main(argv, out=o.fileno(), err=e.fileno(), tree=dirty)
    assert code == 2 and out.read_bytes() == b"" and b"usage: python -m qro_kit" in err.read_bytes()


def test_a_shots_divisor_that_is_no_number_is_misuse(tmp_path):
    out, err = tmp_path / "o", tmp_path / "e"
    with open(out, "wb") as o, open(err, "wb") as e:
        code = cli.main(["freeze", "--out", str(tmp_path / "w"), "--shots-divisor", "x"], out=o.fileno(), err=e.fileno(),
                        tree=dirty)
    assert code == 2 and b"--shots-divisor x: a positive whole number" in err.read_bytes()


def test_a_divisor_that_does_not_divide_the_shots_is_misuse_and_makes_nothing(tmp_path):
    out, err = tmp_path / "o", tmp_path / "e"
    ok = lambda: {"commit": "0" * 40, "tag": "qro-kit-v0.0.0", "tags": []}   # noqa: E731
    with open(out, "wb") as o, open(err, "wb") as e:
        code = cli.main(["freeze", "--out", str(tmp_path / "w"), "--shots-divisor", "3"], out=o.fileno(), err=e.fileno(),
                        tree=ok)
    assert code == 2 and b"divides 2048" in err.read_bytes() and not (tmp_path / "w").exists()


def test_the_real_route_of_freeze_is_not_built(tmp_path):
    ok = lambda: {"commit": "0" * 40, "tag": "qro-kit-v0.0.0", "tags": []}   # noqa: E731
    with pytest.raises(Refused) as caught:
        freeze.freeze(tmp_path / "w", route="real", tree=ok)
    assert caught.value.name == "route-unsafe" and not (tmp_path / "w").exists()


def test_the_twin_names_itself_synthetic():
    md = P.pristine()
    import json
    root = json.loads((md / "ro-crate-metadata.json").read_bytes())["@graph"][1]
    assert "twin" in root["qro:writer"] and "synthetic" in root["qro:writer"] and "fake devices" in root["name"]
