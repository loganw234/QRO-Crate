"""Step 8: every `qro:Snapshot`'s stamp, newest value and values-digest recomputed from its file, and every `qro:Job`'s
calibration link recomputed from the job's first shot (the start of the execution span inside its raw result) and
the snapshots the crate carries of its device. The word a Job claims is never trusted. The small crate has the three
cases of the real records: a plain link (jobka), a link past a newer snapshot that was stamped and measured before
the shot (joblaw: `history-in-gap`), and a snapshot stamped before the shot but still being measured at it (jobcoh:
no gap). Each fault is refused `calibration-link`, or `step-unbuilt` for a link word no version builds."""
import copy
import json
from datetime import timedelta

import pytest
from p1_builder import (SNAPS, at, atlas_model, entity, ibm_doc, ibm_model, judge, known_answer_rows, read_md, refusal,
                        snapshot_bytes, snapshot_doc, snapshot_path, zoneless)

from qro import p1_calibration, p1_forms, p1_steps, spelling
from qro.refusal import Refused

S0657, S0902, S1128, S1221 = (snapshot_path(SNAPS[k][0]) for k in ("s0657", "s0902", "s1128", "s1221"))
DEVICE = "#device-ibm_synth"
FIRST = {"jobka": at(10, 27, 0, 285375), "joblaw": at(12, 26, 17, 34663), "jobcoh": at(12, 22, 0, 162000)}
AT, GAP = "history-at-first-shot", "history-in-gap"


def verdict(m, tmp_path):
    return judge(m, tmp_path / "crate", 8)


def refused(m, tmp_path, name="calibration-link", where=None, detail=None):
    r = verdict(m, tmp_path)
    assert r is not None, "accepted"
    assert r.name == name, f"{r.name} at {r.where}: {r.detail}"
    if where is not None:
        assert where in r.where, f"{r.where}: {r.detail}"
    if detail is not None:
        assert detail in r.detail, r.detail
    return r


def link(m, job, word, *snaps):
    m.ents["#job-" + job]["qro:calibrationLink"] = word
    if snaps:
        m.ents["#job-" + job]["qro:calibration"] = [{"@id": s} for s in snaps]
    else:
        m.ents["#job-" + job].pop("qro:calibration", None)


def shot(m, job, start, stop=None):
    """The job's first shot moved: its raw result's span and the times the Job states, together."""
    stop = start + timedelta(seconds=1) if stop is None else stop
    path = f"run/{job}-raw.json"

    def move(doc):
        span = doc["__value__"]["metadata"]["execution"]["execution_spans"]["__value__"]["spans"][0]["__value__"]
        span["start"]["__value__"], span["stop"]["__value__"] = zoneless(start), zoneless(stop)
    m.edit_json(path, move)
    m.ents["#job-" + job].update(startTime=spelling.time(start), endTime=spelling.time(stop))


def test_the_honest_crates_are_accepted(tmp_path):
    assert verdict(ibm_model(), tmp_path / "ibm") is None
    assert verdict(atlas_model(), tmp_path / "atlas") is None


# -- a snapshot's claims, recomputed from its file ----------------------------------------------------------------------------------
CLAIMS = {"qro:valuesDigest": "0" * 64, "qro:stamp": "2026-10-05T00:00:00Z", "qro:newestValue": "2026-10-05T00:00:01Z"}
SNAPSHOTS = (S0657, S0902, S1128, S1221)


@pytest.mark.parametrize("snap", SNAPSHOTS)
@pytest.mark.parametrize("term", CLAIMS)
def test_each_of_a_snapshots_three_claims_is_held_to_its_file_on_every_snapshot(tmp_path, snap, term):
    m = ibm_model()
    m.ents[snap][term] = CLAIMS[term]
    r = refused(m, tmp_path, where=f"{snap} {term}")
    assert "the file gives" in r.detail


@pytest.mark.parametrize("snap", SNAPSHOTS)
@pytest.mark.parametrize("term", CLAIMS)
def test_a_snapshot_that_states_none_of_a_claim_is_refused(tmp_path, snap, term):
    m = ibm_model()
    del m.ents[snap][term]
    refused(m, tmp_path, where=f"{snap} {term}", detail="states its")


def test_a_snapshot_whose_text_is_not_ascii_is_checked_like_any_other(tmp_path):
    """The verifier's note: IBM's properties text is UTF-8. The file here writes a unit of micro-seconds as the character
    itself, and the claims drawn from it are held; the digest is of the values, not of how the file spells them."""
    m = ibm_model()
    micro = chr(0xB5)
    doc = m.json(S1128)
    doc["qubits"][0][0]["unit"] = micro + "s"
    data = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False).encode("utf-8")
    assert micro.encode("utf-8") in data
    m.files[S1128] = data
    m.ents[S1128].update(p1_calibration.claims(p1_forms.parse_snapshot(data)))
    assert verdict(m, tmp_path / "claims drawn from the file") is None
    stale = ibm_model()
    stale.files[S1128] = data
    refused(stale, tmp_path / "stale", where=f"{S1128} qro:valuesDigest")


def test_qro_jobid_is_reported_and_compared_with_nothing_a_stated_limit(tmp_path):
    """The verifier's note, and a stated limit (round 1): `qro:jobId` is REPORTED. No step compares it with the job line's
    or the record's `job_id`, so two jobs' ids swapped, or an id no file names, pass steps 4, 5 and 8."""
    m = ibm_model()
    a, b = m.ents["#job-jobka"], m.ents["#job-joblaw"]
    a["qro:jobId"], b["qro:jobId"] = b["qro:jobId"], a["qro:jobId"]
    m.ents["#job-jobcoh"]["qro:jobId"] = "a job no file names"
    for step in (4, 5, 8):
        assert judge(m, tmp_path / str(step), step) is None


def test_a_value_changed_in_the_file_moves_the_digest_and_the_stale_claim_is_refused(tmp_path):
    m = ibm_model()
    m.edit_json(S1128, lambda d: d["qubits"][0][0].__setitem__("value", 555.5))
    refused(m, tmp_path, where=f"{S1128} qro:valuesDigest")


def test_a_date_changed_in_the_file_moves_the_newest_value_and_not_the_digest(tmp_path):
    m = ibm_model()
    m.edit_json(S1128, lambda d: d["general"][0].__setitem__("date", "2026-10-05T11:27:00Z"))
    refused(m, tmp_path, where=f"{S1128} qro:newestValue")
    got = p1_calibration.values_digest(p1_forms.parse_snapshot(m.files[S1128]))
    assert got == m.ents[S1128]["qro:valuesDigest"]


def test_the_stamp_changed_in_the_file_moves_the_stamp_and_not_the_digest(tmp_path):
    m = ibm_model()
    m.edit_json(S1128, lambda d: d.__setitem__("last_update_date", "2026-10-05T11:30:00Z"))
    refused(m, tmp_path, where=f"{S1128} qro:stamp")


def test_a_field_outside_the_snapshot_schema_is_refused_not_ignored(tmp_path):
    m = ibm_model()
    m.edit_json(S1128, lambda d: d.__setitem__("note", "x"))
    refused(m, tmp_path, where=S1128, detail="holds ['note']")


@pytest.mark.parametrize("data", [b"", b"\xff", b"[]", b"{}", b'{"a": 1, "a": 2}', b"NaN", b"[" * 100000],
                         ids=["nothing", "not UTF-8", "a list", "empty", "a key twice", "NaN", "deep"])
def test_a_hostile_snapshot_is_a_refusal_never_an_exception(tmp_path, data):
    m = ibm_model()
    m.files[S1128] = data
    refused(m, tmp_path, where=S1128, detail="cannot be checked")


def test_the_device_a_snapshot_names_is_the_one_its_file_is_of(tmp_path):
    m = ibm_model()
    m.ents[S1128]["qro:device"] = {"@id": m.device("ibm_other")}
    refused(m, tmp_path, where=f"{S1128} qro:device", detail="ibm_other")
    m = ibm_model()
    m.ents[S1128]["qro:device"] = {"@id": "#program-sampler"}
    refused(m, tmp_path / "b", where=f"{S1128} qro:device")
    m = ibm_model()
    del m.ents[S1128]["qro:device"]
    refused(m, tmp_path / "c", where=S1128)


def test_a_snapshot_that_is_not_a_file_the_crate_holds_is_refused(tmp_path):
    m = ibm_model()
    m.entity("#snapshot-elsewhere", ["File", "qro:Snapshot"], **{k: v for k, v in m.ents[S1128].items()
                                                                if k.startswith("qro:")})
    refused(m, tmp_path, where="#snapshot-elsewhere", detail="not a file the crate holds")


def test_two_snapshots_with_equal_values_and_other_stamps_are_accepted_and_their_digests_are_equal(tmp_path):
    """The control calibration-restamped: the 06:57:43 snapshot and the 09:02:46 one differ in stamp and in dates, not
    in values. Neither is a fault; their values-digests are equal."""
    m = ibm_model()
    assert m.ents[S0657]["qro:valuesDigest"] == m.ents[S0902]["qro:valuesDigest"]
    assert m.ents[S0657]["qro:stamp"] != m.ents[S0902]["qro:stamp"]
    assert m.ents[S0657]["qro:newestValue"] != m.ents[S0902]["qro:newestValue"]
    third = m.snapshot(at(7, 30, 0), at(7, 29, 0), seed=0)
    assert m.ents[third]["qro:valuesDigest"] == m.ents[S0902]["qro:valuesDigest"]
    assert verdict(m, tmp_path) is None


def test_every_snapshot_is_visited_before_any_job_and_the_first_by_id_is_named(tmp_path):
    m = ibm_model()
    m.ents[S1221]["qro:stamp"] = CLAIMS["qro:stamp"]
    m.ents[S0902]["qro:stamp"] = CLAIMS["qro:stamp"]
    m.ents["#job-jobka"].pop("qro:calibrationLink")
    refused(m, tmp_path, where=S0902)


# -- a job's link ------------------------------------------------------------------------------------------------------------------
def test_the_three_links_of_the_small_crate_are_the_ones_the_rule_recomputes(tmp_path):
    m = ibm_model()
    assert [(j, m.ents["#job-" + j]["qro:calibrationLink"]) for j in FIRST] == [
        ("jobka", AT), ("joblaw", GAP), ("jobcoh", AT)]
    assert verdict(m, tmp_path) is None


def test_a_job_that_states_no_link_is_refused(tmp_path):
    m = ibm_model()
    del m.ents["#job-jobka"]["qro:calibrationLink"]
    refused(m, tmp_path, where="#job-jobka qro:calibrationLink", detail="states how its calibration is linked")


def test_a_word_the_step_does_not_know_is_refused_even_where_the_reader_is_not_asked(tmp_path):
    """The reader holds the word set; the step does not rely on it, and refuses a word it has no rule for."""
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    entity(md["@graph"], "#job-jobka")["qro:calibrationLink"] = "history-at-last-shot"
    r = refusal(8, crate, md)
    assert r.name == "calibration-link" and "is not a link this step knows" in r.detail


@pytest.mark.parametrize("word", ["unknown", "unexposed"])
def test_a_link_that_claims_no_snapshot_names_none(tmp_path, word):
    m = ibm_model()
    link(m, "jobka", word)
    assert verdict(m, tmp_path) is None
    link(m, "jobka", word, S0902)
    refused(m, tmp_path / "b", where="#job-jobka qro:calibration", detail=f"whose link is {word} names no snapshot")


@pytest.mark.parametrize("word", ["read-before-run", "read-after-run", "provider-linked"])
def test_a_link_word_no_version_builds_is_step_unbuilt_and_names_the_word(tmp_path, word):
    m = ibm_model()
    link(m, "jobka", word, S0902)
    r = refused(m, tmp_path, "step-unbuilt", "#job-jobka qro:calibrationLink")
    assert word in r.detail
    link(m, "jobka", word)
    refused(m, tmp_path / "b", "step-unbuilt", "#job-jobka qro:calibrationLink")


# -- calibration-late ----------------------------------------------------------------------------------------------------------------
def test_a_snapshot_stamped_after_the_first_shot_is_not_a_link(tmp_path):
    """The control calibration-late: the morning job (first shot 10:27:00) claimed to have run under the 12:21:18
    snapshot, the word left history-at-first-shot."""
    m = ibm_model()
    link(m, "jobka", AT, S1221)
    refused(m, tmp_path, where="#job-jobka qro:calibration", detail="not entirely before the first shot")


def test_a_snapshot_stamped_before_the_first_shot_but_still_being_measured_is_not_a_link(tmp_path):
    """The second plant of the control: sheet-01's job (first shot 12:22:00.162) under the 12:21:18 snapshot, whose
    newest value is dated 12:24:06.73."""
    m = ibm_model()
    link(m, "jobcoh", AT, S1221)
    refused(m, tmp_path, where="#job-jobcoh qro:calibration", detail="not entirely before the first shot")


@pytest.mark.parametrize("name, first, ok", [
    ("at the stamp", SNAPS["s1128"][0], False), ("a microsecond after the stamp", SNAPS["s1128"][0]
                                                 + timedelta(microseconds=1), True),
    ("a microsecond before the stamp", SNAPS["s1128"][0] - timedelta(microseconds=1), False)])
def test_a_first_shot_at_a_snapshots_stamp_is_too_early_and_one_microsecond_later_is_not(tmp_path, name, first, ok):
    m = ibm_model()
    link(m, "jobka", AT, S1128)
    shot(m, "jobka", first)
    assert (verdict(m, tmp_path) is None) is ok


@pytest.mark.parametrize("name, first, ok", [
    ("at the newest value", at(12, 24, 6, 730000), False), ("a microsecond after it", at(12, 24, 6, 730001), True),
    ("a microsecond before it", at(12, 24, 6, 729999), False)])
def test_a_first_shot_at_a_snapshots_newest_value_is_too_early_and_one_microsecond_later_is_not(tmp_path, name,
                                                                                               first, ok):
    """The 12:21:18 snapshot, whose newest value is dated 12:24:06.73 (the real one's is .734584)."""
    m = ibm_model()
    link(m, "jobka", AT, S1221)
    shot(m, "jobka", first)
    r = verdict(m, tmp_path)
    assert (r is None) is ok, r and r.detail


# -- calibration-gap -----------------------------------------------------------------------------------------------------------------
def test_a_link_that_ignores_a_newer_snapshot_stamped_and_measured_before_the_shot_is_refused_as_a_gap(tmp_path):
    """The control calibration-gap: the law job (first shot 12:26:17.03, the history returned 11:28:27) claimed
    history-at-first-shot, when the 12:21:18 snapshot was stamped, and measured by 12:24:06."""
    m = ibm_model()
    link(m, "joblaw", AT, S1128)
    r = refused(m, tmp_path, where="#job-joblaw qro:calibrationLink")
    assert "the link is history-in-gap, not history-at-first-shot" in r.detail and S1221 in r.detail


def test_a_gap_that_is_no_gap_because_the_newer_snapshot_was_still_being_measured_is_refused_as_a_false_gap(tmp_path):
    m = ibm_model()
    link(m, "jobcoh", GAP, S1128, S1221)
    refused(m, tmp_path, where="#job-jobcoh qro:calibrationLink", detail="the link is history-at-first-shot")


def test_a_gap_with_no_newer_snapshot_to_name_is_refused(tmp_path):
    m = ibm_model()
    link(m, "jobka", GAP, S0902, S1128)                      # S1128 was stamped after the shot: no gap to name
    refused(m, tmp_path, where="#job-jobka qro:calibrationLink", detail="the link is history-at-first-shot")
    link(m, "jobka", GAP, S0657, S0902)                      # but S0902 is a newer snapshot than S0657: a gap
    assert verdict(m, tmp_path / "b") is None


def test_the_gap_names_the_newest_stamped_snapshot_that_qualifies(tmp_path):
    m = ibm_model()
    newer = m.snapshot(at(12, 24, 0), at(12, 24, 30), seed=3)
    r = refused(m, tmp_path, where="#job-joblaw qro:calibration")
    assert newer in r.detail
    link(m, "joblaw", GAP, S1128, newer)
    assert verdict(m, tmp_path / "newest") is None


def test_the_history_one_is_the_older_of_the_two_by_stamp_and_the_list_order_means_nothing(tmp_path):
    m = ibm_model()
    link(m, "joblaw", GAP, S1221, S1128)
    assert verdict(m, tmp_path) is None
    link(m, "joblaw", GAP, S0902, S1221)                    # C is the older, S0902; its gap is the newest, S1221
    assert verdict(m, tmp_path / "b") is None
    link(m, "joblaw", GAP, S0902, S1128)                    # but S1128 is not the newest stamped after S0902
    refused(m, tmp_path / "c", where="#job-joblaw qro:calibration", detail="the link names")


def test_the_history_one_is_told_by_the_stamp_and_not_by_the_newest_value(tmp_path):
    """The verifier's mutant 18 of round 3: of the two snapshots a gap names the older is told by its newest value instead of
    its stamp, and every pair above has the two in one order. Here the snapshot stamped first was measured last (stamped 12:22:30,
    its newest value 12:25:30) and the one stamped later was measured before (stamped 12:25:00, newest 12:24:00), both before the
    shot at 12:26:17: the history one is the first, whatever order they are listed in."""
    m = ibm_model()
    older = m.snapshot(at(12, 22, 30), at(12, 25, 30), seed=4)
    newer = m.snapshot(at(12, 25, 0), at(12, 24, 0), seed=5)
    assert (older, newer) == (snapshot_path(at(12, 22, 30)), snapshot_path(at(12, 25, 0)))
    link(m, "joblaw", GAP, older, newer)
    assert verdict(m, tmp_path / "a") is None
    link(m, "joblaw", GAP, newer, older)
    assert verdict(m, tmp_path / "b") is None
    link(m, "joblaw", AT, older)                              # and the newer one is a gap that a plain link ignores
    refused(m, tmp_path / "c", where="#job-joblaw qro:calibrationLink", detail="the link is history-in-gap")


def test_two_snapshots_of_one_stamp_leave_neither_the_older(tmp_path):
    m = ibm_model()
    doc = snapshot_doc(SNAPS["s1128"][0], SNAPS["s1128"][1], seed=9)
    path = "snapshots/twin-of-1128.json"
    data = snapshot_bytes(doc)
    m.file(path, data, ["File", "qro:Snapshot"], **p1_calibration.claims(p1_forms.parse_snapshot(data)),
           **{"qro:device": {"@id": DEVICE}, "qro:clock": "provider"})
    link(m, "joblaw", GAP, S1128, path)
    refused(m, tmp_path, where="#job-joblaw qro:calibration", detail="one stamp")


def test_a_snapshot_of_another_device_makes_no_gap_and_is_no_link(tmp_path):
    m = ibm_model()
    other = m.device("ibm_other")
    elsewhere = m.snapshot(at(12, 24, 0), at(12, 24, 30), seed=5, device=other, name="ibm_other")
    assert verdict(m, tmp_path) is None                                    # joblaw's honest link is unchanged
    link(m, "jobka", AT, elsewhere)
    refused(m, tmp_path / "b", where="#job-jobka qro:calibration",
            detail="is a snapshot of 'ibm_other', not of 'ibm_synth'")


def test_a_gap_link_holds_each_of_its_two_references_to_be_a_snapshot_of_the_crate_and_of_the_device(tmp_path):
    """The verifier's mutants 19 and 20 of batch 2, round 3: only the first reference was checked, and the second fell to another
    sentence of the same verdict ("the link names ..."). A link of two names each as a snapshot of the crate and of the job's
    device, whichever place a bad one is in."""
    m = ibm_model()
    elsewhere = m.snapshot(at(12, 24, 0), at(12, 24, 30), seed=5, device=m.device("ibm_other"), name="ibm_other")
    for place, pair in enumerate(((S1128, "bundle/law.qasm"), ("bundle/law.qasm", S1221))):
        link(m, "joblaw", GAP, *pair)
        refused(m, tmp_path / f"no snapshot {place}", where="#job-joblaw qro:calibration",
                detail="bundle/law.qasm is not a Snapshot of the crate")
    for place, pair in enumerate(((S1128, elsewhere), (elsewhere, S1221))):
        link(m, "joblaw", GAP, *pair)
        refused(m, tmp_path / f"other device {place}", where="#job-joblaw qro:calibration",
                detail=f"{elsewhere} is a snapshot of 'ibm_other', not of 'ibm_synth'")


def second_entity(m, snapshot):
    """The snapshot hung on a second device entity that has the first's name."""
    m.entity(DEVICE + "-b", "IndividualProduct", name="ibm_synth", **{"qro:deviceKind": "qpu"})
    m.ents[snapshot]["qro:device"] = {"@id": DEVICE + "-b"}


def test_a_carried_snapshot_hung_on_a_second_device_entity_of_the_same_name_is_still_weighed(tmp_path):
    """The verifier's D3 (cases3.py). The gap job honestly names [11:28:27, 12:21:18], and the 12:21:18 snapshot was stamped
    and entirely measured before its first shot. Claiming history-at-first-shot past it is refused as a gap; and it is
    refused still when the 12:21:18 snapshot hangs on another entity named as the device is: the crate carries it."""
    m = ibm_model()
    link(m, "joblaw", AT, S1128)
    refused(m, tmp_path / "plain", where="#job-joblaw qro:calibrationLink", detail="the link is history-in-gap")
    second_entity(m, S1221)
    refused(m, tmp_path / "second", where="#job-joblaw qro:calibrationLink", detail="the link is history-in-gap")
    assert S1221 in m.ents and m.ents[S1221]["qro:device"] == {"@id": DEVICE + "-b"}


def test_the_device_is_the_backend_a_snapshots_file_is_of_whichever_entity_names_it(tmp_path):
    """The honest gap, whose second snapshot hangs on the second entity of the device's name, is the same link."""
    m = ibm_model()
    second_entity(m, S1221)
    assert verdict(m, tmp_path / "gap") is None
    second_entity(m, S0902)
    assert verdict(m, tmp_path / "plain") is None


def test_a_job_whose_device_entity_has_no_name_carries_no_snapshot_of_it(tmp_path):
    m = ibm_model()
    second_entity(m, S0902)
    second_entity(m, S1128)
    second_entity(m, S1221)
    second_entity(m, S0657)
    del m.ents[DEVICE]["name"]
    refused(m, tmp_path, where="#job-jobcoh qro:calibration", detail="is a snapshot of 'ibm_synth', not of None")


# -- the shape of the claim --------------------------------------------------------------------------------------------------------------
def test_a_link_names_the_number_of_snapshots_its_word_says(tmp_path):
    m = ibm_model()
    link(m, "jobka", AT)
    refused(m, tmp_path / "none", where="#job-jobka qro:calibration", detail="names 1 snapshots, and this names 0")
    m = ibm_model()
    link(m, "jobka", AT, S0657, S0902)
    refused(m, tmp_path / "two", where="#job-jobka qro:calibration", detail="names 1 snapshots, and this names 2")
    m = ibm_model()
    link(m, "joblaw", GAP, S1128)
    refused(m, tmp_path / "gap", where="#job-joblaw qro:calibration", detail="names 2 snapshots, and this names 1")


def test_a_reference_that_is_no_snapshot_of_the_crate_is_refused(tmp_path):
    m = ibm_model()
    link(m, "jobka", AT, "bundle/law.qasm")
    refused(m, tmp_path, where="#job-jobka qro:calibration", detail="is not a Snapshot of the crate")
    link(m, "jobka", AT, "https://example.org/a-snapshot")
    refused(m, tmp_path / "b", where="#job-jobka qro:calibration", detail="is not a Snapshot of the crate")


def test_a_history_link_needs_a_device_to_find_the_carried_snapshots_of(tmp_path):
    m = ibm_model()
    del m.ents["#job-jobka"]["qro:device"]
    refused(m, tmp_path, where="#job-jobka")


def test_the_history_at_running_is_reported_and_not_compared(tmp_path):
    m = ibm_model()
    m.ents["#job-jobka"]["qro:historyAtRunning"] = {"@id": S1221}
    assert verdict(m, tmp_path) is None


def test_the_clock_a_job_states_is_reported_and_not_compared(tmp_path):
    m = ibm_model()
    m.ents["#job-jobka"]["qro:clock"] = "local"
    assert verdict(m, tmp_path) is None


# -- the first shot is the raw result's span, and the Job's times are held to it ----------------------------------------------------------
def test_the_first_shot_is_read_from_the_raw_result_and_not_from_the_start_time_a_job_states(tmp_path):
    """The Job's startTime moved to a moment the snapshot would be valid at, the raw's span left: refused for the
    times differing, and the link is never judged on the claim."""
    m = ibm_model()
    link(m, "jobka", AT, S1221)
    m.ents["#job-jobka"]["startTime"] = "2026-10-05T13:00:00Z"
    r = refused(m, tmp_path, where="#job-jobka startTime")
    assert "the execution span in its raw result gives" in r.detail


@pytest.mark.parametrize("term, delta", [("startTime", 1), ("startTime", -1), ("endTime", 1), ("endTime", -1)])
def test_a_start_or_end_time_a_microsecond_off_the_span_is_refused(tmp_path, term, delta):
    m = ibm_model()
    have = p1_forms.parse_time(m.ents["#job-jobka"][term], "Z") + timedelta(microseconds=delta)
    m.ents["#job-jobka"][term] = spelling.time(have)
    refused(m, tmp_path, where=f"#job-jobka {term}")


@pytest.mark.parametrize("value", ["unknown", None])
@pytest.mark.parametrize("term", ["startTime", "endTime"])
def test_a_job_with_a_span_states_both_its_times(tmp_path, term, value):
    m = ibm_model()
    if value is None:
        del m.ents["#job-jobka"][term]
    else:
        m.ents["#job-jobka"][term] = value
    refused(m, tmp_path, where=f"#job-jobka {term}")


def test_the_times_are_the_earliest_start_and_the_latest_stop_of_many_spans(tmp_path):
    m = ibm_model()

    def more(doc):
        spans = doc["__value__"]["metadata"]["execution"]["execution_spans"]["__value__"]["spans"]
        extra = copy.deepcopy(spans[0])
        extra["__value__"]["start"]["__value__"] = zoneless(at(10, 26, 0))
        extra["__value__"]["stop"]["__value__"] = zoneless(at(10, 28, 0))
        spans.append(extra)
    m.edit_json("run/jobka-raw.json", more)
    refused(m, tmp_path, where="#job-jobka startTime")
    m.ents["#job-jobka"].update(startTime=spelling.time(at(10, 26, 0)), endTime=spelling.time(at(10, 28, 0)))
    assert verdict(m, tmp_path / "b") is None


def raw_without_a_span(m, job):
    m.files[f"run/{job}-raw.json"] = json.dumps(ibm_doc([known_answer_rows(40)], [None])).encode()


def test_a_job_whose_raw_result_has_no_span_says_unknown_and_needs_no_snapshot(tmp_path):
    m = ibm_model()
    raw_without_a_span(m, "jobka")
    refused(m, tmp_path, where="#job-jobka qro:calibrationLink", detail="needs the Job's first shot")
    link(m, "jobka", "unknown")
    m.ents["#job-jobka"].update(startTime="unknown", endTime="unknown")
    assert verdict(m, tmp_path / "b") is None


def test_a_history_link_whose_raw_result_has_no_span_has_no_first_shot_to_compare_with(tmp_path):
    m = ibm_model()
    raw_without_a_span(m, "jobka")
    m.ents["#job-jobka"].update(startTime="unknown", endTime="unknown")
    refused(m, tmp_path, where="#job-jobka qro:calibrationLink", detail="needs the Job's first shot")


def test_a_history_link_on_a_job_that_made_no_raw_result_has_no_first_shot_either(tmp_path):
    m = ibm_model()
    m.ents["#job-jobka"]["result"] = [{"@id": "run/jobka-line.json"}]
    m.ents["#job-jobka"].update(startTime="unknown", endTime="unknown")
    refused(m, tmp_path, where="#job-jobka qro:calibrationLink", detail="needs the Job's first shot")
    link(m, "jobka", "unexposed")
    assert verdict(m, tmp_path / "b") is None


def test_a_raw_result_in_a_form_no_reader_is_built_for_is_refused_by_name(tmp_path):
    """A history link needs the raw result's span, and a form this version has no reader for has none to give."""
    m = ibm_model()
    m.ents["run/jobka-raw.json"]["qro:rawForm"] = "some-other-sampler-result/v1"
    refused(m, tmp_path, where="#job-jobka", detail="no reader is built for the raw form some-other-sampler-result/v1")


def test_a_job_with_two_raw_results_is_refused(tmp_path):
    m = ibm_model()
    m.ents["#job-jobka"]["result"] = [{"@id": "run/jobka-raw.json"}, {"@id": "run/joblaw-raw.json"}]
    refused(m, tmp_path, where="#job-jobka", detail="2 raw results")


@pytest.mark.parametrize("data", [b"", b"{}", b"[]", b"\xff"], ids=["nothing", "empty", "a list", "not UTF-8"])
def test_a_raw_result_that_cannot_be_read_is_a_refusal_here_too(tmp_path, data):
    m = ibm_model()
    m.files["run/jobka-raw.json"] = data
    refused(m, tmp_path, where="#job-jobka", detail="cannot be checked")


@pytest.mark.parametrize("word", ["unknown", "unexposed"])
def test_for_a_link_that_names_no_snapshot_the_times_are_held_to_the_span_wherever_the_raw_carries_one(tmp_path, word):
    """The lead's ruling (round 1), as the design's paragraph says: whatever the link word, a Job's startTime and endTime
    are held to the execution span of its raw result, as instants, wherever the raw carries one. The verifier's B1: a Job
    linked unknown, its times years off its raw's span, was accepted."""
    first, last = spelling.time(FIRST["jobka"]), spelling.time(at(10, 27, 1, 376976))
    m = ibm_model()
    link(m, "jobka", word)
    assert verdict(m, tmp_path / "honest") is None
    off = {"B1, both years off": ("2020-01-01T00:00:00Z", "2020-01-01T00:00:01Z", "startTime"),
           "the end a microsecond off": (first, spelling.time(at(10, 27, 1, 376977)), "endTime"),
           "the start unknown": ("unknown", last, "startTime"), "the end unknown": (first, "unknown", "endTime")}
    for i, (name, (start, end, where)) in enumerate(off.items()):
        m = ibm_model()
        link(m, "jobka", word)
        m.ents["#job-jobka"].update(startTime=start, endTime=end)
        refused(m, tmp_path / str(i), where=f"#job-jobka {where}", detail="the execution span in its raw result gives")
    m = ibm_model()
    link(m, "jobka", word)
    del m.ents["#job-jobka"]["endTime"]
    refused(m, tmp_path / "no end", where="#job-jobka endTime", detail="the Job states None")


@pytest.mark.parametrize("word", ["unknown", "unexposed"])
def test_where_the_raw_result_carries_no_span_no_time_is_compared(tmp_path, word):
    """The Job's times are the raw's to say, and a raw that says none leaves them uncompared: an Atlas result carries no
    span, and an IBM result may lack one."""
    m = atlas_model()
    m.ents["#job-alaw"].update({"qro:calibrationLink": word, "startTime": "2026-09-25T10:00:00Z", "endTime": "unknown"})
    assert verdict(m, tmp_path / "atlas") is None
    m = ibm_model()
    link(m, "jobka", word)
    raw_without_a_span(m, "jobka")
    m.ents["#job-jobka"].update(startTime="2026-10-04T00:00:00Z", endTime="unknown")
    assert verdict(m, tmp_path / "ibm") is None


@pytest.mark.parametrize("word", ["unknown", "unexposed"])
def test_a_raw_result_this_step_cannot_read_is_refused_whatever_the_link_since_its_span_cannot_be_told(tmp_path, word):
    """The raw is opened for every job, so one that is no result is refused here too (steps 2 and 3 hold the bytes
    before, and refuse such a crate first; this step is run alone)."""
    m = ibm_model()
    link(m, "jobka", word)
    m.files["run/jobka-raw.json"] = b"not a result at all"
    refused(m, tmp_path, where="#job-jobka", detail="cannot be checked")


def test_an_atlas_link_that_claims_a_snapshot_is_refused(tmp_path):
    m = atlas_model()
    m.ents["#job-alaw"]["qro:calibration"] = [{"@id": "#device-atlas"}]
    refused(m, tmp_path, where="#job-alaw qro:calibration")


# -- every entity is visited ----------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("job", ["jobka", "joblaw", "jobcoh"])
def test_every_job_is_visited_and_the_first_by_id_is_named(tmp_path, job):
    m = ibm_model()
    m.ents["#job-" + job]["qro:calibrationLink"] = "read-after-run"
    refused(m, tmp_path, "step-unbuilt", f"#job-{job}")


def test_the_first_job_by_id_is_the_one_named(tmp_path):
    m = ibm_model()
    for j in ("joblaw", "jobka"):
        m.ents["#job-" + j]["qro:calibrationLink"] = "read-after-run"
    refused(m, tmp_path, "step-unbuilt", "#job-jobka")


# -- the step as a function the checker calls ------------------------------------------------------------------------------------------------
def test_the_step_takes_a_path_or_a_string(tmp_path):
    crate = ibm_model().write(tmp_path / "c")
    p1_steps.step8(str(crate), read_md(crate))
    p1_steps.step8(crate, read_md(crate))


def test_a_graph_with_a_type_that_is_not_a_string_is_refused_by_the_step_that_is_handed_it(tmp_path):
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    entity(md["@graph"], "#job-jobka")["@type"] = ["CreateAction", {"@id": "qro:Job"}]
    r = refusal(8, crate, md)
    assert r.name == "calibration-link" and r.where == "@graph" and "a type that is not a string" in r.detail


def test_a_graph_with_an_id_twice_is_refused_by_the_step_that_is_handed_it(tmp_path):
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    md["@graph"].append(dict(md["@graph"][-1]))
    r = refusal(8, crate, md)
    assert r.name == "calibration-link" and "twice" in r.detail
    with pytest.raises(Refused):
        p1_steps.step8(crate, md)


def test_a_claim_edited_after_the_reader_has_read_the_metadata_is_still_refused(tmp_path):
    """The step does not trust that the reader has seen what it is handed."""
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    entity(md["@graph"], S1128)["qro:stamp"] = "2026-10-05T11:28:28Z"
    r = refusal(8, crate, md)
    assert r.name == "calibration-link" and S1128 in r.where
