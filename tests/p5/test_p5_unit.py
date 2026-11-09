"""`qro.p5_unit`: reading a unit crate (the seam P3 reads units through), what it states of itself, and intake (P5's design,
items 8 and 9). The complement is held at intake and not by the checker, a stated limit; the four controls come out as
section 11 says; and `python -m qro.p5_unit intake` is held as a process (exit codes, the line written whole, a verdict that
cannot be written)."""
import json
import os
import subprocess
import sys

import pytest
from p5_support import ROOT, forge, no_link_left_behind, no_network, twin  # noqa: F401

from controls import plants_p5 as P
from qro import canonical, checker, p5_unit as U
from qro.refusal import Refused

pytestmark = pytest.mark.usefixtures("no_network", "no_link_left_behind")
checker.load()                                   # every parcel's steps, whichever test runs first
FEZ = "fake_fez"


# -- read: the seam P3 reads through ----------------------------------------------------------------------------------------
def test_read_gives_the_units_identity_and_devices(tmp_path):
    u = U.read(twin(tmp_path))
    assert u.kind == "simulator" and u.devices == ("fake_kingston", "fake_marrakesh", FEZ)
    assert u.recipe_sha256 == U.recipe_sha256(128) and u.contributor == "withheld" and u.kit_tag == P.KIT_TAG
    assert u.kit_commit == P.KIT_COMMIT and u.clock == "local"


def test_read_gives_every_job_with_its_pubs_in_the_recipes_order(tmp_path):
    u = U.read(twin(tmp_path))
    jobs = u.jobs()
    assert len(jobs) == 18 and [(j.pass_, j.device, j.kind) for j in jobs][:6] == [
        (1, "fake_kingston", "control"), (1, "fake_kingston", "film"), (1, "fake_marrakesh", "control"),
        (1, "fake_marrakesh", "film"), (1, FEZ, "control"), (1, FEZ, "film")]
    c = jobs[0]
    assert [p.name for p in c.pubs] == ["known-answer", "known-complement"] and [p.role for p in c.pubs] == ["known-answer"] * 2
    f = jobs[1]
    assert [p.name for p in f.pubs] == ["law", "coherence-xx", "coherence-yy"] and f.pubs[1].basis == "XX" + "Z" * 14
    assert c.raw.endswith("control-1-raw.json") and c.line.endswith("control-1-line.json") and c.start is None
    assert c.id.startswith("dryrun-") and c.submitted_at.endswith("Z")


def test_read_selects_by_device_role_pass_and_kind(tmp_path):
    u = U.read(twin(tmp_path))
    assert len(u.jobs(device=FEZ)) == 6 and len(u.jobs(role="law")) == 9 and len(u.jobs(role="coherence")) == 9
    assert len(u.jobs(role="known-answer")) == 9 and len(u.jobs(pass_=2)) == 6 and len(u.jobs(kind="control", device=FEZ)) == 3
    assert [j.name for j in u.jobs(device=FEZ, pass_=3)] == ["control-3", "film-3"]


def test_read_re_derives_the_counts_from_the_raw_bytes(tmp_path):
    crate = twin(tmp_path)
    u = U.read(crate)
    job = u.jobs(kind="film")[0]
    for pub in job.pubs:
        counts = u.counts(pub.id)
        assert sum(counts.values()) == 128 and all(isinstance(k, tuple) for k in counts)
    ka = u.counts(u.jobs(kind="control")[0].pubs[0].id)
    assert max(ka, key=ka.get) == U.KNOWN_ANSWER
    comp = u.counts(u.jobs(kind="control")[0].pubs[1].id)
    assert max(comp, key=comp.get) == U.KNOWN_COMPLEMENT


def test_read_gives_each_devices_chain_and_planned_jobs(tmp_path):
    u = U.read(twin(tmp_path))
    assert len(u.chain(FEZ)) == 16 and len(set(u.chain(FEZ))) == 16
    assert u.planned(FEZ) == ["control-1", "film-1", "control-2", "film-2", "control-3", "film-3"]


def test_a_qpu_unit_reads_as_qpu_with_provider_times(tmp_path):
    u = U.read(twin(tmp_path, kind="qpu"))
    assert u.kind == "qpu" and u.devices == U.DEVICE_SETS["qpu"] and u.clock == "provider"
    assert all(j.start is not None for j in u.jobs()) and u.status().clock == "provider" and u.status().interleaved


def test_read_refuses_a_crate_that_is_no_unit(tmp_path):
    from qro import fixture
    crate = fixture.make(tmp_path / "fixture")
    with pytest.raises(Exception, match="qro:Unit"):
        U.read(crate)


# -- status ---------------------------------------------------------------------------------------------------------------
def test_the_twin_states_nothing_of_itself(tmp_path):
    st = U.read(twin(tmp_path)).status()
    assert st.complete == {"fake_kingston": True, "fake_marrakesh": True, FEZ: True} and st.missing == ()
    assert st.interleaved and st.lines() == [] and st.sentences() == frozenset() and not st.incomplete
    assert st.order == ("fake_kingston", "fake_marrakesh", FEZ) * 3


def test_a_unit_missing_a_film_job_is_kept_as_incomplete(tmp_path):
    crate = P.unit_incomplete(tmp_path)
    st = U.read(crate).status()
    assert st.complete == {"fake_kingston": True, "fake_marrakesh": True, FEZ: False}
    assert st.lines() == [f"KEPT unit-incomplete: {FEZ} film-3 missing"] and st.sentences() == {"unit-incomplete"}
    assert st.interleaved


def test_a_unit_whose_devices_ran_in_blocks_is_kept_as_not_interleaved_with_the_studys_sentence(tmp_path):
    crate = P.not_interleaved(tmp_path)
    st = U.read(crate).status()
    assert not st.interleaved and st.order == ("fake_kingston", "fake_marrakesh", FEZ)
    assert st.lines() == ['KEPT not-interleaved: "the difference is the device\'s-and-its-time\'s"']
    assert "the difference is the device's-and-its-time's" in st.sentences() and not st.incomplete


def test_the_edit_planted_controls_state_what_the_built_ones_do(tmp_path):
    """The same four controls as edits of a built unit (what the kit's p5-kit stage plants on a real local unit)."""
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    inc = P.plant_incomplete(P.copy_of(a))
    blk = P.plant_interleaved(P.copy_of(b))
    checker.load()
    for crate in (inc, blk):
        checker.check(crate)
    assert U.read(inc).status().lines() == [f"KEPT unit-incomplete: {FEZ} film-3 missing"]
    assert U.read(blk).status().lines() == ['KEPT not-interleaved: "the difference is the device\'s-and-its-time\'s"']


def test_a_failed_job_is_kept_as_incomplete_and_the_order_is_judged_on_the_jobs_present(tmp_path):
    crate = P.build_unit(tmp_path, failed=frozenset({(FEZ, "control-2"), (FEZ, "film-2")}))
    st = U.read(crate).status()
    assert st.missing == ((FEZ, "control-2", "failed"), (FEZ, "film-2", "failed")) and st.interleaved
    assert "KEPT unit-incomplete: fake_fez control-2 failed" in st.lines()


def test_a_unit_missing_its_first_jobs_is_still_judged_in_order(tmp_path):
    crate = P.build_unit(tmp_path, skip=frozenset({("fake_kingston", "control-1"), ("fake_kingston", "film-1")}))
    st = U.read(crate).status()
    assert st.interleaved and st.complete["fake_kingston"] is False


# -- intake ---------------------------------------------------------------------------------------------------------------
def test_intake_accepts_the_twin_with_no_kept_line(tmp_path):
    crate = twin(tmp_path)
    r = U.intake(crate)
    md = json.loads((crate / canonical.DESCRIPTOR).read_bytes())
    assert r.digest == canonical.body_digest(md) and r.lines() == [f"ACCEPTED {r.digest} unit scaled by shots divisor 128"]
    assert len(r.verdicts) == 18 and all(holds for _p, holds in r.verdicts)


def test_intake_names_a_scaled_unit_by_its_line_and_a_full_recipe_unit_plainly(tmp_path):
    """A unit built with --shots-divisor is never taken for a unit of the full recipe by its line (the first verifier,
    round 1): its ACCEPTED line says the divisor. A unit of the full recipe is `unit`, as before."""
    scaled = twin(tmp_path / "a")
    full = twin(tmp_path / "b", kind="qpu")
    assert U.read(scaled).shots_divisor == 128 and U.read(full).shots_divisor == 1
    assert U.intake(scaled).lines()[0].endswith(" unit scaled by shots divisor 128")
    assert U.intake(full).lines()[0].endswith(" unit") and U.intake(full).divisor == 1
    other = twin(tmp_path / "c", divisor=64)
    assert U.read(other).shots_divisor == 64 and U.intake(other).lines()[0].endswith(" unit scaled by shots divisor 64")


def test_intake_keeps_an_incomplete_unit_and_says_so(tmp_path):
    r = U.intake(P.unit_incomplete(tmp_path))
    assert r.lines()[1:] == [f"KEPT unit-incomplete: {FEZ} film-3 missing"] and len(r.verdicts) == 18


def test_a_known_answer_that_fails_is_refused_by_the_checker_before_intake(tmp_path):
    crate = P.unit_known_answer(tmp_path)
    with pytest.raises(Refused) as caught:
        U.intake(crate)
    assert caught.value.name == "known-answer" and "dryrun-" in caught.value.where


def test_a_complement_that_fails_alone_is_accepted_by_the_checker_and_refused_at_intake(tmp_path):
    """The stated limit (design item 14, 3): step 5 holds the one known-answer PUB each Decode names."""
    crate = P.plant_complement(P.copy_of(tmp_path))
    checker.load()
    checker.check(crate)                                   # the checker accepts it
    with pytest.raises(Refused) as caught:
        U.intake(crate)
    assert caught.value.name == "known-answer" and caught.value.where.endswith("-1") and "does not hold" in caught.value.detail


def test_the_edit_planted_known_answer_is_refused_by_the_checker(tmp_path):
    crate = P.plant_known_answer(P.copy_of(tmp_path))
    with pytest.raises(Refused) as caught:
        checker.check(crate)
    assert caught.value.name == "known-answer"


def test_a_complement_that_fails_in_a_later_control_job_is_refused_at_intake(tmp_path):
    crate = P.copy_of(tmp_path)
    f = forge(crate)
    shots = f.json(f"unit/{FEZ}/run/control-3-pub1-known-complement.json")["source"]["shots"]
    f.set_rows(FEZ, "control-3", 1, [P.outcome(U.KNOWN_ANSWER)] * shots)
    f.regenerate()
    with pytest.raises(Refused) as caught:
        U.intake(crate)
    assert caught.value.name == "known-answer"


def test_the_record_is_one_canonical_line_beside_the_crate(tmp_path):
    crate = P.unit_incomplete(tmp_path)
    r = U.intake(crate)
    line = U.record_of(r, unit_commit="c" * 40, tool="t")
    doc = json.loads(line)
    assert line.endswith(b"\n") and line.count(b"\n") == 1 and line == canonical.compact(doc)
    assert doc["format"] == "qro-crate/unit-intake/v1" and doc["crate"] == r.digest and doc["incomplete"] is True
    assert doc["complete"][FEZ] is False and doc["missing"] == [[FEZ, "film-3", "missing"]] and doc["interleaved"] is True


# -- the command, in process -------------------------------------------------------------------------------------------------
def run(tmp_path, argv):
    out, err = tmp_path / "stdout", tmp_path / "stderr"
    with open(out, "wb") as o, open(err, "wb") as e:
        code = U.main(argv, out=o.fileno(), err=e.fileno())
    return code, out.read_bytes().decode("ascii"), err.read_bytes().decode("ascii")


def test_the_command_accepts_and_writes_its_lines(tmp_path):
    crate = P.unit_incomplete(tmp_path / "w")
    code, out, err = run(tmp_path, ["intake", str(crate)])
    lines = out.splitlines()
    assert (code, err) == (0, "") and lines[0].startswith("ACCEPTED ") and lines[0].endswith(" unit scaled by shots divisor 128")
    assert lines[1:] == [f"KEPT unit-incomplete: {FEZ} film-3 missing"]


def test_the_command_refuses_with_one_line_and_exit_1(tmp_path):
    code, out, err = run(tmp_path, ["intake", str(P.unit_known_answer(tmp_path / "w"))])
    assert (code, err) == (1, "") and out.startswith("REFUSED known-answer at ") and out.count("\n") == 1


def test_the_command_writes_the_record_beside_the_crate(tmp_path):
    crate = twin(tmp_path / "w")
    record = tmp_path / "intake.jsonl"
    code, out, err = run(tmp_path, ["intake", str(crate), "--record", str(record)])
    assert (code, err) == (0, "") and json.loads(record.read_bytes())["crate"] == out.split()[1]
    assert not [p for p in crate.rglob("*") if p.name == "intake.jsonl"]


@pytest.mark.parametrize("argv", [[], ["intake"], ["bogus", "x"], ["intake", "a", "b"], ["intake", "--bogus", "x"],
                                   ["intake", "x", "--record"], ["intake", "x", "--record", "a", "--record", "b"]])
def test_misuse_is_exit_2_with_the_usage(tmp_path, argv):
    code, out, err = run(tmp_path, argv)
    assert (code, out) == (2, "") and "usage: python -m qro.p5_unit intake" in err


def test_a_crate_that_is_no_directory_is_misuse(tmp_path):
    code, out, err = run(tmp_path, ["intake", str(tmp_path / "not-there")])
    assert (code, out) == (2, "") and "no such crate directory" in err


def test_a_record_inside_the_crate_or_over_a_file_is_misuse(tmp_path):
    crate = twin(tmp_path / "w")
    code, out, err = run(tmp_path, ["intake", str(crate), "--record", str(crate / "intake.jsonl")])
    assert (code, out) == (2, "") and "beside the crate, never in it" in err
    taken = tmp_path / "taken"
    taken.write_bytes(b"x")
    code, out, err = run(tmp_path, ["intake", str(crate), "--record", str(taken)])
    assert (code, out) == (2, "") and taken.read_bytes() == b"x"


def test_the_tool_failing_is_exit_3_and_not_a_verdict(tmp_path, monkeypatch):
    crate = twin(tmp_path / "w")
    monkeypatch.setattr(U, "intake", lambda c: 1 / 0)
    code, out, err = run(tmp_path, ["intake", str(crate)])
    assert code == 3 and out == "" and err.startswith("FAILED: intake itself failed, ZeroDivisionError")


# -- the command, as a process ---------------------------------------------------------------------------------------------
def process(argv, stdout=subprocess.PIPE):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-m", "qro.p5_unit", *argv], stdout=stdout, stderr=subprocess.PIPE, env=env,
                          cwd=ROOT)


def closed_pipe():
    r, w = os.pipe()
    os.close(r)
    return w


def test_the_process_accepts_and_refuses_with_its_exit_codes(tmp_path):
    p = process(["intake", str(twin(tmp_path / "a"))])
    assert (p.returncode, p.stderr) == (0, b"") and p.stdout.startswith(b"ACCEPTED ") and p.stdout.count(b"\n") == 1
    p = process(["intake", str(P.unit_known_answer(tmp_path / "b"))])
    assert (p.returncode, p.stderr) == (1, b"") and p.stdout.startswith(b"REFUSED known-answer at ")
    p = process(["bogus"])
    assert (p.returncode, p.stdout) == (2, b"") and p.stderr.startswith(b"usage: python -m qro.p5_unit intake")


def test_the_process_writing_to_a_pipe_nobody_reads_exits_3_and_never_120(tmp_path):
    w = closed_pipe()
    try:
        p = process(["intake", str(twin(tmp_path / "w"))], stdout=w)
    finally:
        os.close(w)
    assert p.returncode == 3, p.stderr[-300:]


def runner_bash():
    import shutil
    git = shutil.which("git")
    if os.name == "nt":
        from pathlib import Path
        for up in Path(git).resolve().parents:
            for rel in ("usr/bin/bash.exe", "bin/bash.exe"):
                if (up / rel).is_file():
                    return str(up / rel)
        raise AssertionError("no Git Bash beside git.exe")
    return shutil.which("bash")


def test_the_process_with_a_closed_descriptor_exits_3(tmp_path):
    crate = str(twin(tmp_path / "w")).replace("\\", "/")
    py = sys.executable.replace("\\", "/")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONPATH=str(ROOT))
    p = subprocess.run([runner_bash(), "-c", f'"{py}" -m qro.p5_unit intake "{crate}" >&-; echo "rc=$?"'],
                       capture_output=True, env=env, cwd=ROOT)
    assert p.stdout.strip().endswith(b"rc=3"), (p.stdout[-200:], p.stderr[-300:])
