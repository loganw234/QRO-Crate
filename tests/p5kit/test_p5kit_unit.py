"""A whole local unit, end to end, through the command line, on the fake backends (M1's stage 3; P5's design, item 15): from a
clean checkout at a tagged commit, `freeze`, `drive` and `crate` in the kit's own environment, the crate accepted by the checker
in the runner's interpreter, read through the seam P3 reads, and the four controls planted in it.

The unit runs at a shots divisor of 128 (control PUBs of 16 shots and film PUBs of 128), so that this stage's routine run takes
minutes and not the hour a full-shot unit takes on this machine (the film job's time was measured at 489 s: docs/P5.md); a
unit at full shots was built once, at the end, and its time is docs/P5.md's. A scaled unit is visibly another recipe: its
recipe digest, recorded as `shots_divisor`, is not the full recipe's."""
import hashlib
import json
import subprocess
import sys

import pytest
from p5kit_support import ROOT, TAG, git, kit_cli, no_network, tagged_copy  # noqa: F401

from controls import plants_p5 as P
from qro import canonical, checker, p5_unit as U
from qro.refusal import Refused

pytestmark = pytest.mark.usefixtures("no_network")
DIVISOR = 128


class Built:
    pass


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    b = Built()
    base = tmp_path_factory.mktemp("kit-unit")
    b.copy = tagged_copy(base / "kit")
    b.work = base / "work"
    b.freeze = kit_cli(b.copy, "freeze", "--route", "local", "--out", str(b.work), "--shots-divisor", str(DIVISOR),
                       "--contributor", "p5kit-test")
    assert b.freeze[0] == 0, b.freeze
    b.unit = b.work / "records" / "unit"
    b.drive = kit_cli(b.copy, "drive", str(b.unit), "--route", "local")
    assert b.drive[0] == 0, b.drive
    b.crate = base / "crate"
    b.build = kit_cli(b.copy, "crate", str(b.unit), "--out", str(b.crate))
    assert b.build[0] == 0, b.build
    return b


def test_freeze_prints_the_units_digest_and_its_first_12_hex_digits(built):
    code, out, err = built.freeze
    word = out.split()
    assert err == "" and word[:2] == ["FROZEN", "unit"] and word[3] == "confirm" and word[5] == "divisor" and word[6] == "128"
    digest = hashlib.sha256((built.unit / "UNIT.json").read_bytes()).hexdigest()
    assert word[2] == digest and word[4] == digest[:12]


def test_the_frozen_unit_names_the_recipe_the_kit_the_contributor_and_three_bundles(built):
    unit = json.loads((built.unit / "UNIT.json").read_bytes())
    assert unit["recipe"] == "qro-unit/1" and unit["recipe_sha256"] == U.recipe_sha256(DIVISOR) != U.recipe_sha256()
    assert unit["shots_divisor"] == DIVISOR and unit["kind"] == "simulator" and unit["devices"] == list(U.DEVICE_SETS["simulator"])
    assert unit["kit_tag"] == TAG and unit["kit_commit"] == git(built.copy, "rev-parse", "HEAD") and unit["contributor"] == "p5kit-test"
    for device, digest in zip(unit["devices"], unit["bundles"], strict=True):
        assert hashlib.sha256((built.unit / device / "bundle" / "manifest.json").read_bytes()).hexdigest() == digest


def test_every_bundle_names_its_options_its_defaults_and_the_devices_rep_delay(built):
    for device in U.DEVICE_SETS["simulator"]:
        m = json.loads((built.unit / device / "bundle" / "manifest.json").read_bytes())
        assert m["options"]["execution"] == {"init_qubits": True, "rep_delay": 0.00025}
        assert m["options"]["dynamical_decoupling"] == {"enable": False} and m["options"]["twirling"] == {
            "enable_gates": False, "enable_measure": False}
        defaulted = m["unit"]["options_defaulted"]
        assert defaulted == sorted(defaulted) and {"default_shots", "execution.meas_type"} <= set(defaulted)
        assert not {"dynamical_decoupling.enable", "twirling.enable_gates", "execution.init_qubits", "execution.rep_delay",
                    "max_execution_time"} & set(defaulted)
        assert m["kind"] == "simulator" and m["backend"] == device and m["unit"]["shots_divisor"] == DIVISOR
        chains = {tuple(c["chain"]) for j in m["jobs"] for c in j["circuits"]}
        assert len(chains) == 1 and len(next(iter(chains))) == 16
        assert len({c["salt"] for j in m["jobs"] for c in j["circuits"]}) == 15


def test_the_drive_ran_all_18_jobs_and_every_control_job_held(built):
    code, out, err = built.drive
    assert code == 0 and "DRIVEN: all 18 jobs ran and every control job held" in out and err == ""
    assert out.count("HOLDS: the device reads in decode's order") == 9 and out.count("submitted ") == 18
    assert out.count("line anchored") == 18 and "STOPPED" not in out


def test_the_runs_hold_every_file_of_every_job_in_the_throwaway_records_repository(built):
    for device in U.DEVICE_SETS["simulator"]:
        run = built.unit / device / "run"
        names = sorted(p.name for p in run.iterdir())
        assert len([n for n in names if n.endswith("-raw.json")]) == 6 and len([n for n in names if "-pub" in n]) == 15
        assert len([n for n in names if n.endswith("-verdict.json")]) == 3 and len([n for n in names if n.endswith("-line.json")]) == 6
    assert git(built.work / "records", "log", "--oneline").count("hardware job line") == 18
    assert git(built.work / "origin.git", "log", "--oneline", "main").count("hardware job line") == 18


def test_a_line_was_pushed_before_its_raw_result_was_written(built):
    """The anchor's order, in the files' own times: each line's commit precedes its raw result's file."""
    log = git(built.work / "records", "log", "--format=%ct %s", "--reverse").splitlines()
    assert len([ln for ln in log if "hardware job line" in ln]) == 18
    for device in U.DEVICE_SETS["simulator"]:
        for job in ("control-1", "film-1"):
            line_time = int(git(built.work / "records", "log", "-1", "--format=%ct", "--", f"unit/{device}/run/{job}-line.json"))
            raw_time = (built.unit / device / "run" / f"{job}-raw.json").stat().st_mtime
            assert line_time <= raw_time + 1


def test_the_crate_is_accepted_by_the_checker_in_the_runners_interpreter(built):
    code, out, err = built.build
    assert err == "" and out.splitlines()[0].startswith("BUILT unit: ")
    checker.load()
    md = checker.check(built.crate)
    identity = canonical.body_digest(md)
    assert f"identity {identity}" in out.splitlines()[0] and out.splitlines()[1] == f"ACCEPTED {identity} unit scaled by shots divisor 128"
    p = subprocess.run([sys.executable, "-m", "qro", "check", str(built.crate)], capture_output=True, cwd=ROOT)
    assert (p.returncode, p.stdout, p.stderr) == (0, f"ACCEPTED {identity}\n".encode(), b"")


def test_intake_accepts_it_with_no_kept_line_and_holds_all_18_control_pubs(built):
    result = U.intake(built.crate)
    line = f"ACCEPTED {result.digest} unit scaled by shots divisor 128"
    assert result.lines() == [line] and len(result.verdicts) == 18
    p = subprocess.run([sys.executable, "-m", "qro.p5_unit", "intake", str(built.crate)], capture_output=True, cwd=ROOT)
    assert (p.returncode, p.stdout, p.stderr) == (0, (line + "\n").encode(), b"")


def test_the_seam_p3_reads_gives_the_real_units_facts(built):
    u = U.read(built.crate)
    assert u.kind == "simulator" and u.recipe_sha256 == U.recipe_sha256(DIVISOR) and u.contributor == "p5kit-test"
    assert u.kit_tag == TAG and u.kit_commit == git(built.copy, "rev-parse", "HEAD") and u.clock == "local"
    st = u.status()
    assert st.interleaved and not st.incomplete and st.order == u.devices * 3
    law = u.jobs(role="law")
    assert len(law) == 9 and {len(j.pubs) for j in law} == {3} and all(j.id.startswith("dryrun-") for j in law)
    for device in u.devices:
        assert len(u.chain(device)) == 16
    pub = law[0].pubs[0]
    assert sum(u.counts(pub.id).values()) == 128


def test_the_crate_claims_no_anchor_and_no_provider_time(built):
    md = checker.check(built.crate)
    jobs = [e for e in md["@graph"] if "qro:Job" in canonical.types(e)]
    assert len(jobs) == 18 and {j["qro:calibrationLink"] for j in jobs} == {"unexposed"}
    assert {j["startTime"] for j in jobs} == {"unknown"} and {j["qro:clock"] for j in jobs} == {"local"}
    assert {d["qro:deviceKind"] for d in md["@graph"] if "IndividualProduct" in canonical.types(d)} == {"simulator"}


def test_the_crate_carries_the_shipped_source_circuit_and_the_licence_byte_for_byte(built):
    for rel, src in ((U.SOURCE_PATH, "circuit-ed767c01bd4b851d.qasm"), (U.LICENSE_PATH, "LICENSE-quantum-film")):
        assert (built.crate / rel).read_bytes() == (ROOT / "qro_kit" / "_vendor" / src).read_bytes()


def test_the_unit_is_a_regular_files_only_tree_and_no_link_is_left_behind(built):
    for root in (built.crate, built.unit):
        for p in root.rglob("*"):
            assert not p.is_symlink() and not (hasattr(p, "is_junction") and p.is_junction()), p


# -- the four controls, planted by the same functions in a copy of this unit's crate ---------------------------------------------
def copy_crate(built, tmp_path):
    import shutil
    out = tmp_path / "crate"
    shutil.copytree(built.crate, out)
    return out


def test_control_unit_incomplete_on_the_real_unit(built, tmp_path):
    crate = P.plant_incomplete(copy_crate(built, tmp_path))
    checker.load()
    checker.check(crate)
    r = U.intake(crate)
    assert r.lines()[1:] == ["KEPT unit-incomplete: fake_fez film-3 missing"]
    assert U.read(crate).status().complete == {"fake_kingston": True, "fake_marrakesh": True, "fake_fez": False}


def test_control_not_interleaved_on_the_real_unit(built, tmp_path):
    crate = P.plant_interleaved(copy_crate(built, tmp_path))
    checker.load()
    checker.check(crate)
    r = U.intake(crate)
    assert r.lines()[1:] == ['KEPT not-interleaved: "the difference is the device\'s-and-its-time\'s"']
    assert U.read(crate).status().complete == dict.fromkeys(U.DEVICE_SETS["simulator"], True)


def test_control_unit_known_answer_on_the_real_unit(built, tmp_path):
    crate = P.plant_known_answer(copy_crate(built, tmp_path))
    with pytest.raises(Refused) as caught:
        checker.check(crate)
    assert caught.value.name == "known-answer" and "does not hold the known answer" in caught.value.detail


def test_the_complement_failing_alone_is_accepted_by_the_checker_and_refused_at_intake_on_the_real_unit(built, tmp_path):
    crate = P.plant_complement(copy_crate(built, tmp_path))
    checker.check(crate)
    with pytest.raises(Refused) as caught:
        U.intake(crate)
    assert caught.value.name == "known-answer" and caught.value.where.endswith("-1")


def test_the_real_unit_with_a_resealed_shot_is_accepted_the_crate_only_checkers_stated_limit(built, tmp_path):
    """P1.md limit 1: a producer holding every byte can reseal a unit; only the owner's re-fetch and the audit refuse it.
    The kit's crate, like v0's, is held by the checker to its records, and the records to each other."""
    crate = copy_crate(built, tmp_path)
    f = P.Forge(crate)
    shots = f.json("unit/fake_fez/run/film-2-pub0-law.json")["source"]["shots"]
    f.set_rows("fake_fez", "film-2", 0, [P.outcome((0, 1, 2, 3, 4))] * shots)
    f.regenerate()
    checker.check(crate)


# -- what the command line does when asked again, or from an unclean tree ----------------------------------------------------------
def tree_listing(root):
    return sorted((p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()) for p in root.rglob("*")
                  if p.is_file() and ".git" not in p.relative_to(root).parts)


def test_driving_a_unit_twice_is_refused_once_only_and_changes_nothing(built):
    before = tree_listing(built.unit)
    code, out, err = kit_cli(built.copy, "drive", str(built.unit), "--route", "local")
    assert code == 1 and err == "" and out.startswith("REFUSED once-only at ") and out.count("\n") == 1
    assert tree_listing(built.unit) == before


def test_a_crate_is_built_into_a_directory_that_is_not_there_yet(built):
    code, out, err = kit_cli(built.copy, "crate", str(built.unit), "--out", str(built.crate))
    assert code == 2 and out == "" and "exists" in err and (built.crate / canonical.DESCRIPTOR).is_file()


def test_the_real_route_is_refused_route_unsafe_and_sends_nothing(built, tmp_path):
    before = tree_listing(built.unit)
    digest = hashlib.sha256((built.unit / "UNIT.json").read_bytes()).hexdigest()
    for args, where in ((("--route", "real"), "--confirm"), (("--route", "real", "--confirm", "0" * 12), "--confirm"),
                        (("--route", "real", "--confirm", digest[:12]), "preflight")):
        code, out, err = kit_cli(built.copy, "drive", str(built.unit), *args)
        assert code == 1 and err == "" and out.startswith(f"REFUSED route-unsafe at {where}: "), (args, out, err)
    assert tree_listing(built.unit) == before


def test_a_modified_tracked_file_makes_every_command_refuse_kit_dirty_before_anything_is_made(built, tmp_path):
    copy = tagged_copy(tmp_path / "kit")
    with open(copy / "qro_kit" / "freeze.py", "ab") as f:
        f.write(b"# a change that is not committed\n")
    work = tmp_path / "work"
    for args in (("freeze", "--route", "local", "--out", str(work)), ("crate", str(built.unit), "--out", str(tmp_path / "c")),
                 ("drive", str(built.unit), "--route", "local")):
        code, out, err = kit_cli(copy, *args)
        assert code == 1 and err == "" and out.startswith("REFUSED kit-dirty at qro_kit/freeze.py: "), (args, out, err)
    assert not work.exists() and not (tmp_path / "c").exists()


def test_an_untagged_commit_makes_the_kit_refuse_kit_dirty(built, tmp_path):
    copy = tagged_copy(tmp_path / "kit", tag=None)
    code, out, err = kit_cli(copy, "freeze", "--route", "local", "--out", str(tmp_path / "work"))
    assert code == 1 and "HEAD carries no tag" in out and not (tmp_path / "work").exists()


def test_a_unit_frozen_by_another_commit_than_the_one_running_is_refused(built, tmp_path):
    copy = tagged_copy(tmp_path / "kit", tag=None)
    git(copy, "commit", "-q", "--allow-empty", "-m", "another")
    git(copy, "tag", "qro-kit-v0.0.2")
    code, out, err = kit_cli(copy, "drive", str(built.unit), "--route", "local")
    assert code == 1 and out.startswith("REFUSED kit-dirty at UNIT.json: ") and "another commit" in out
