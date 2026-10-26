"""P1's steps inside the checker, and the command line as a process (FORMAT.md, item 16): the steps run in their order
after steps 1 to 3 and before step 9; a refusal is exit 1 and its REFUSED line, by P1's own names; a hostile file is
a refusal and never exit 3; misuse (a path the user may not read) is exit 2; and the checker itself failing, an exit
or an interrupt inside a step, or a host error that is not the user's, is exit 3 and no verdict.

The small crates name a generator no parcel registers, so as a process they stop at step 9 for want of one: that
refusal, `step-unbuilt` at the root's `qro:generator`, is how a process shows steps 1 to 8 accepted. In process, a
pass-through generator is registered by the test (it makes step 9 trivially true, and nothing here reads step 9)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from p1_builder import (GENERATOR, KA, LAYOUTS, SNAPS, atlas_model, atlas_result, copy_job, ibm_model, judge, ka_qasm,
                        outcome, raw_ibm, sha, snapshot_path)

from qro import canonical, checker, p1_steps
from qro.__main__ import main
from qro.refusal import Refused

ROOT = Path(__file__).resolve().parents[2]
RAW = "run/jobka-raw.json"
S1221 = snapshot_path(SNAPS["s1221"][0])


@pytest.fixture
def loaded(monkeypatch):
    """The registries fresh, P1's declarations loaded as the command line loads them, and a pass-through generator."""
    monkeypatch.setattr(checker, "STEPS", {n: None for n in range(4, 9)})
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    monkeypatch.setattr(checker, "GENERATORS", {GENERATOR: lambda crate: json.loads(
        (Path(crate) / canonical.DESCRIPTOR).read_bytes())})
    monkeypatch.setattr(checker, "COUNTS", [])
    checker.load()


def check(m, tmp_path):
    return checker.check(m.write(tmp_path / "crate"))


def refused(m, tmp_path):
    with pytest.raises(Refused) as r:
        check(m, tmp_path)
    return r.value


def test_the_honest_crates_pass_all_nine_steps(loaded, tmp_path):
    for name, m in (("ibm", ibm_model()), ("atlas", atlas_model())):
        md = check(m, tmp_path / name)
        assert md["@graph"][1]["qro:generator"] == GENERATOR


# -- the controls, through the whole checker ------------------------------------------------------------------------------------
def test_job_reattributed_is_commitment_when_the_two_jobs_hold_as_many_shots(loaded, tmp_path):
    m = ibm_model()
    m.files[RAW] = m.files["run/joblaw-raw.json"]
    r = refused(m, tmp_path)
    assert (r.name, r.where) == ("commitment", "run/jobka-raw.json pub_results[0]")


def test_job_reattributed_is_count_unpaid_first_where_the_two_jobs_hold_different_shot_counts(loaded, tmp_path):
    m = ibm_model()
    m.files[RAW] = raw_ibm([[outcome((1, 2))] * 41], [None])
    r = refused(m, tmp_path)
    assert (r.name, r.where) == ("count-unpaid", "run/jobka-raw.json qro:shots")


def test_bits_mirrored_is_known_answer(loaded, tmp_path):
    m = ibm_model()
    for j in ("jobcoh", "jobka", "joblaw"):
        m.ents["#decode-" + j]["qro:bitOrder"] = "lsb-first"
    assert refused(m, tmp_path).name == "known-answer"


def test_calibration_late_and_gap_are_calibration_link(loaded, tmp_path):
    m = ibm_model()
    m.ents["#job-jobka"]["qro:calibration"] = [{"@id": S1221}]
    assert refused(m, tmp_path / "late").name == "calibration-link"
    m = ibm_model()
    m.ents["#job-joblaw"]["qro:calibrationLink"] = "history-at-first-shot"
    m.ents["#job-joblaw"]["qro:calibration"] = [m.ents["#job-joblaw"]["qro:calibration"][0]]
    r = refused(m, tmp_path / "gap")
    assert r.name == "calibration-link" and "history-in-gap" in r.detail


def test_the_steps_run_in_their_order_and_refuse_at_the_first_failure(loaded, tmp_path):
    m = ibm_model()
    m.ents["#pub-jobka-0"]["qro:commitment"] = "1" * 64
    m.ents["#decode-jobka"]["qro:bitOrder"] = "lsb-first"
    m.ents["#job-jobka"]["qro:calibrationLink"] = "history-in-gap"
    assert refused(m, tmp_path / "a").name == "commitment"
    m = ibm_model()
    m.ents["#decode-jobka"]["qro:bitOrder"] = "lsb-first"
    m.ents["#job-jobka"]["qro:calibrationLink"] = "history-in-gap"
    assert refused(m, tmp_path / "b").name == "known-answer"


def test_steps_1_to_3_come_before_p1s_steps(loaded, tmp_path):
    m = ibm_model()
    m.ents["#pub-jobka-0"]["qro:commitment"] = "1" * 64
    crate = m.write(tmp_path / "crate")
    (crate / "run" / "jobka-raw.json").write_bytes(b"{}")                  # digest left: step 2 first
    with pytest.raises(Refused) as r:
        checker.check(crate)
    assert r.value.name == "raw-digest"
    m.files[RAW] = b"{}"                                                   # resealed, but no result: step 3 next
    with pytest.raises(Refused) as r:
        checker.check(m.write(tmp_path / "again"))
    assert r.value.name == "raw-form"


def test_a_link_word_no_version_builds_is_step_unbuilt(loaded, tmp_path):
    m = ibm_model()
    m.ents["#job-jobka"]["qro:calibrationLink"] = "provider-linked"
    assert refused(m, tmp_path).name == "step-unbuilt"


def test_a_generator_the_crate_names_that_is_not_built_is_refused_after_p1s_steps_accept(loaded, tmp_path, monkeypatch):
    monkeypatch.delitem(checker.GENERATORS, GENERATOR)
    r = refused(ibm_model(), tmp_path)
    assert (r.name, r.where) == ("step-unbuilt", "./ qro:generator")


# -- the name each step gives a hostile file (round 2, D5) --------------------------------------------------------------------
GARBAGE = b"\xff{ not a document"
HOSTILE = {"a raw result": "run/jobka-raw.json", "a record": "run/jobka-pub0-known-answer.json",
           "a job line": "run/jobka-line.json", "a snapshot": snapshot_path(SNAPS["s0902"][0]),
           "the known-answer circuit": "bundle/known-answer.qasm"}
# (what, step): the name the step refuses it by, or None where the step never reads it
NAMES = {("a raw result", 4): "commitment", ("a raw result", 5): "raw-form", ("a raw result", 8): "calibration-link",
         ("a record", 4): "commitment", ("a record", 5): "known-answer", ("a record", 8): None,
         ("a job line", 4): "commitment", ("a job line", 5): "known-answer", ("a job line", 8): None,
         ("a snapshot", 4): None, ("a snapshot", 5): None, ("a snapshot", 8): "calibration-link",
         ("the known-answer circuit", 4): "commitment", ("the known-answer circuit", 5): "known-answer",
         ("the known-answer circuit", 8): None}


@pytest.mark.parametrize("what, step", sorted(NAMES))
def test_a_hostile_file_is_refused_by_the_steps_own_name_but_a_raw_result_is_raw_form_at_step_5(tmp_path, what, step):
    """The verifier's D5 of round 2 (hostile_names.py): the p1_steps docstring said every hostile file is refused by the
    step's own name, and step 5 gives `raw-form` for a raw result. Each kind of file, each step, files resealed, called direct."""
    m = ibm_model()
    m.files[HOSTILE[what]] = GARBAGE
    r = judge(m, tmp_path / "crate", step)
    if NAMES[(what, step)] is None:
        assert r is None
    else:
        assert r is not None and r.name == NAMES[(what, step)], r


def test_a_result_its_rule_cannot_account_for_is_read_by_step_3_and_refused_raw_form_by_step_5_alone(loaded, tmp_path):
    """The p1_steps docstring says step 5 gives `raw-form` for a raw its reader cannot read (step 3 refuses that one first,
    also as `raw-form`) and for one its rule cannot account for, which only step 5 can tell: an Atlas law result with no
    all-Z setting is a result the reader counts shots of, and the rule has no layouts to read in it."""
    data = atlas_result(LAYOUTS, label="IIIIIIIIIIIIIIXZ", other="IIIIIIIIIIIIIIXX")
    m = atlas_model(law=(data, sum(LAYOUTS.values())))
    assert judge(m, tmp_path / "s4", 4) is None and judge(m, tmp_path / "s8", 8) is None
    r = judge(m, tmp_path / "s5", 5)
    assert (r.name, r.where) == ("raw-form", "law/result.json") and "cannot account for it" in r.detail
    r = refused(m, tmp_path / "whole")
    assert (r.name, r.where) == ("raw-form", "law/result.json") and "cannot account for it" in r.detail


def test_a_count_no_host_can_count_is_raw_form_whether_or_not_the_crate_states_the_shots(loaded, tmp_path):
    """The verifier's D5 of round 2 (bigint.py): counts and shots of 10^400 were read, accepted when the crate stated no
    `qro:shots`, and `count-unpaid` when it stated 4096. They are not read: step 3 gives `raw-form` either way."""
    big = 10 ** 400
    result = {"measurements": {"IIIIIIIIIIIIIIZZ": {"counts": {"0" * 14 + "01": big}, "shots": big}}, "observables": {},
              "density_matrices": {}}
    data = json.dumps({"job_id": "j", "path": "p", "response": {"result": result}, "status": 200,
                       "taken_from": "t"}).encode()
    for stated in (True, False):
        m = atlas_model(law=(data, 4096))
        if not stated:
            m.ents["law/result.json"].pop("qro:shots")
        r = refused(m, tmp_path / str(stated))
        assert (r.name, r.where) == ("raw-form", "law/result.json") and "an integer past 9223372036854775807" in r.detail


def test_the_known_answer_alone_at_none_with_a_mirrored_circuit_passes_every_step_of_the_checker_but_the_ninth(loaded, tmp_path):
    """The stated limit 11 through the whole checker (steps 1 to 8 and a pass-through step 9, which stands for the real one,
    that refuses a body the generator did not write)."""
    m = ibm_model()
    mirror = ka_qasm(tuple(sorted(15 - q for q in KA)))
    m.file("bundle/ka-mirror.qasm", mirror)
    m.edit_json(m.record("jobka"), lambda o: o["source"].update(circuit_sha256=sha(mirror)))
    m.ents["#pub-jobka-0"]["qro:commitment"] = "none"
    for job in ("jobcoh", "jobka", "joblaw"):
        m.ents["#decode-" + job]["qro:bitOrder"] = "lsb-first"
    assert check(m, tmp_path)


def test_a_job_copied_under_new_ids_passes_every_step_of_the_checker_but_the_ninth(loaded, tmp_path):
    m = ibm_model()
    copy_job(m, "joblaw")
    assert check(m, tmp_path)


# -- the command line, as a process ---------------------------------------------------------------------------------------------
def process(argv):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-m", "qro", *argv], capture_output=True, env=env, cwd=ROOT)


def faults():
    def commitment(m):
        m.ents["#pub-jobka-0"]["qro:commitment"] = "1" * 64

    def known_answer(m):
        for j in ("jobcoh", "jobka", "joblaw"):
            m.ents["#decode-" + j]["qro:bitOrder"] = "lsb-first"

    def link(m):
        m.ents["#job-jobka"]["qro:calibration"] = [{"@id": S1221}]

    def count(m):
        m.files[RAW] = raw_ibm([[outcome((1, 2))] * 41], [None])

    def raw_form(m):
        m.files[RAW] = b"{}"

    def hostile_raw(m):
        m.files[RAW] = b"\xff{ not a document"

    def unbuilt(m):
        m.ents["#job-jobka"]["qro:calibrationLink"] = "read-after-run"

    def hostile_record(m):
        m.files[m.record("jobka")] = b"\xff[" * 1000

    def hostile_snapshot(m):
        m.files[S1221] = b"{" * 100000

    def hostile_line(m):
        m.files["run/jobka-line.json"] = b"null"
    return {"commitment": ("commitment", commitment), "known-answer": ("known-answer", known_answer),
            "calibration-link": ("calibration-link", link), "count-unpaid": ("count-unpaid", count),
            "raw-form": ("raw-form", raw_form), "a hostile raw result": ("raw-form", hostile_raw),
            "step-unbuilt": ("step-unbuilt", unbuilt),
            "a hostile record": ("commitment", hostile_record), "a hostile snapshot": ("calibration-link",
                                                                                      hostile_snapshot),
            "a hostile line": ("commitment", hostile_line)}


@pytest.mark.parametrize("fault", faults())
def test_a_refusal_is_exit_1_and_its_one_line_by_p1s_name_and_a_hostile_file_is_never_exit_3(tmp_path, fault):
    name, plant = faults()[fault]
    m = ibm_model()
    plant(m)
    p = process(["check", str(m.write(tmp_path / "crate"))])
    assert p.returncode == 1 and p.stderr == b"", p.stderr[-300:]
    assert p.stdout.startswith(f"REFUSED {name} at ".encode()) and p.stdout.count(b"\n") == 1, p.stdout
    assert all(0x20 <= b < 0x7f for b in p.stdout[:-1])


@pytest.mark.parametrize("model", [ibm_model, atlas_model], ids=["ibm", "atlas"])
def test_an_honest_crate_passes_steps_1_to_8_as_a_process_and_stops_at_the_generator_it_names(tmp_path, model):
    p = process(["check", str(model().write(tmp_path / "crate"))])
    assert p.returncode == 1 and p.stderr == b""
    assert p.stdout.startswith(b"REFUSED step-unbuilt at ./ qro:generator: no generator " + GENERATOR.encode())


# -- misuse, and the checker failing -----------------------------------------------------------------------------------------------------
def run(tmp_path, argv):
    """main() in process, its two descriptors files: (exit code, stdout's bytes, stderr's bytes)."""
    paths = [tmp_path / "out.bin", tmp_path / "err.bin"]
    fds = [os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_BINARY", 0)) for p in paths]
    try:
        code = main(argv, out=fds[0], err=fds[1])
    finally:
        for fd in fds:
            os.close(fd)
    return code, paths[0].read_bytes(), paths[1].read_bytes()


def crate_for_main(tmp_path):
    return str(ibm_model().write(tmp_path / "crate"))


def test_a_file_the_user_may_not_read_in_a_step_is_misuse_exit_2(loaded, tmp_path, monkeypatch):
    crate = crate_for_main(tmp_path)

    def denied(*_):
        raise PermissionError(13, "Permission denied", "run/jobka-line.json")
    monkeypatch.setattr(p1_steps, "_bytes", denied)
    code, out, err = run(tmp_path, ["check", crate])
    assert (code, out) == (2, b"") and b"cannot be read here, Permission denied" in err, err


@pytest.mark.parametrize("raised", [OSError(5, "input/output error"), FileNotFoundError(2, "gone", "x"),
                                    MemoryError(), SystemExit(0), SystemExit(1), KeyboardInterrupt()],
                         ids=["an OSError", "a file vanished", "out of memory", "an exit 0", "an exit 1",
                              "an interrupt"])
def test_an_exit_an_interrupt_or_a_host_error_inside_a_step_is_the_checker_failing_exit_3(loaded, tmp_path, monkeypatch,
                                                                                         raised):
    crate = crate_for_main(tmp_path)

    def boom(*_):
        raise raised
    monkeypatch.setattr(p1_steps, "_bytes", boom)
    code, out, err = run(tmp_path, ["check", crate])
    assert (code, out) == (3, b"") and err.startswith(b"FAILED: the checker itself failed, ")


def test_a_bug_in_a_step_shows_as_a_refused_crate_naming_the_failure_as_a_readers_does(loaded, tmp_path, monkeypatch):
    """FORMAT.md item 16 says it of a reader or a generator; P1's steps do the same of any ordinary exception: it is
    caught where the entity is visited and refused by the step's name with its type and text in the detail, so an
    honest crate that meets a bug is seen refused, never silently accepted, and no hostile file is exit 3."""
    crate = crate_for_main(tmp_path)

    def bug(*_):
        raise ZeroDivisionError("division by zero")
    monkeypatch.setattr(p1_steps, "_pub4", bug)
    code, out, err = run(tmp_path, ["check", crate])
    assert (code, err) == (1, b"") and out.startswith(b"REFUSED commitment at #pub-")
    assert b"cannot be checked: ZeroDivisionError: division by zero" in out
