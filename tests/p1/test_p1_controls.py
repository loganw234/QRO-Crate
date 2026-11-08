"""P1's seven controls (study QRO-0, section 11; P1's design, item 10), planted in the twin of the IBM crate by
controls/plants_p1.py: each comes out as its row says, and the plant is the plant the row describes. Around them, what the
design said the controls would show: the study's first wording of `qpy-only` is refused, not accepted; the stated limits
(`qpy-only`, `shot-moved-resealed` and a copy of a file left unaltered) are limits and not holes; the plants' toolkit,
which P2's plants use, does what it says, and never writes through a hard link.

The seven are checked by the whole checker, once, in the fixture below (the registry's own test and the runner check them
too). The variants are checked by `p1_verdict`: the checker's steps 1 to 3, P1's 4, 5 and 8, and 9, without P2's 6 and 7."""
import copy
import hashlib
import json
import struct
from pathlib import Path

import pytest

from controls import plants_p1 as plants
from controls import registry
from p1_support import (BUNDLE, MANIFEST, MORNING_COH, MORNING_KA, SHEET1_KA, SHEET2_KA, Sandbox, forge, generated, graph, guard,
                        memo_parses, p1_verdict, read_json, types_of)
from qro import canonical, checker, p1_decode, p1_forms, p1_generate as G, p1_records as rec, p1_steps, reader
from qro.refusal import Refused

KA_LINE, KA_RAW, KA_REC = f"{MORNING_KA}-line.json", f"{MORNING_KA}-raw.json", f"{MORNING_KA}-pub0-known-answer.json"
COH_LINE, COH_RAW, COH_REC0 = f"{MORNING_COH}-line.json", f"{MORNING_COH}-raw.json", f"{MORNING_COH}-pub0-coherence-xx.json"
S1_LINE, S2_LINE = f"{SHEET1_KA}-line.json", f"{SHEET2_KA}-line.json"
SNAP_0902, SNAP_1128, SNAP_1221 = plants.SNAP_0902, plants.SNAP_1128, plants.SNAP_1221
SEVEN = ["bits-mirrored", "calibration-gap", "calibration-late", "calibration-restamped", "job-reattributed", "qpy-only",
         "shot-moved-resealed"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(crate, rel):
    return Path(crate).joinpath(*rel.split("/")).read_bytes()


def job_of(md, line_rel):
    return next(e for e in md["@graph"] if "qro:Job" in types_of(e) and e["qro:line"] == {"@id": line_rel})


@pytest.fixture(scope="module")
def honest(tmp_path_factory):
    """The twin as it is built, and its identity."""
    checker.load()
    crate = plants.twin_crate(tmp_path_factory.mktemp("honest"))
    return crate, canonical.body_digest(checker.check(crate)), json.loads(read(crate, canonical.DESCRIPTOR))


@pytest.fixture(scope="module")
def planted(tmp_path_factory, honest):
    """Each control planted in its own copy of the twin, and the whole checker's verdict on it: (crate, the Refused or None,
    the identity or None)."""
    out = {}
    with pytest.MonkeyPatch.context() as m:
        memo_parses(m)
        for name, plant in plants.PLANTS.items():
            crate = plant(tmp_path_factory.mktemp(name.replace("-", "_")))
            try:
                out[name] = (crate, None, canonical.body_digest(checker.check(crate)))
            except Refused as r:
                out[name] = (crate, r, None)
    return out


@pytest.fixture(scope="module")
def working(tmp_path_factory):
    box = Sandbox(tmp_path_factory.mktemp("sandbox"))
    yield box
    box.verify_pristine()


@pytest.fixture
def crate(working, monkeypatch):
    memo_parses(monkeypatch)
    yield working.root
    working.restore()


# -- the registry and the seven ---------------------------------------------------------------------------------------------------
def test_the_plants_are_the_seven_controls_p1_owns_and_the_registry_finds_them():
    assert sorted(plants.PLANTS) == SEVEN == sorted(c.name for c in registry.CONTROLS if c.owner == "P1")
    assert {name: registry.plants()[name] for name in SEVEN} == plants.PLANTS
    assert plants.FAULTS.keys() == plants.PLANTS.keys()


@pytest.mark.parametrize("name", SEVEN)
def test_each_control_comes_out_as_its_row_says(planted, name):
    _, refused, identity = planted[name]
    c = registry.CONTROL[name]
    assert ("refused" if refused else "accepted", refused.name if refused else None) == (c.expected, c.refusal), \
        refused and refused.detail
    assert (identity is not None) == (c.expected == "accepted")


def test_the_twin_is_accepted_and_each_accepted_forgery_is_another_crate(honest, planted):
    _, identity, _ = honest
    ids = {name: planted[name][2] for name in SEVEN if planted[name][2]}
    assert sorted(ids) == ["calibration-restamped", "qpy-only", "shot-moved-resealed"]
    assert len({identity, *ids.values()}) == 4


def test_job_reattributed_is_refused_by_the_echo_inside_another_jobs_raw_result(planted):
    refused = planted["job-reattributed"][1]
    assert refused.where == f"{KA_RAW} pub_results[0]" and "IBM echoed" in refused.detail


def test_bits_mirrored_changes_one_decode_and_nothing_else_of_the_metadata(planted, honest):
    crate, _, old = honest
    new = json.loads(read(planted["bits-mirrored"][0], canonical.DESCRIPTOR))
    before, after = graph(old), graph(new)
    changed = [i for i in before if before[i] != after[i]]
    assert changed == ["#decode-" + job_of(old, KA_LINE)["qro:jobId"]]          # the morning known-answer job's, and no other
    assert (before[changed[0]]["qro:bitOrder"], after[changed[0]]["qro:bitOrder"]) == ("msb-first", "lsb-first")
    assert planted["bits-mirrored"][1].where == f"{changed[0]} qro:bitOrder"
    for rel in (KA_REC, f"{MORNING_KA}-verdict.json", MANIFEST):
        assert read(planted["bits-mirrored"][0], rel) == read(crate, rel)


def test_calibration_late_links_the_morning_job_to_a_snapshot_stamped_after_its_first_shot(planted):
    refused = planted["calibration-late"][1]
    assert refused.where.endswith(" qro:calibration") and SNAP_1221 in refused.detail and "not entirely before" in refused.detail


def test_calibration_gap_is_the_gap_link_claimed_as_a_plain_one_and_refused_as_what_it_is(planted):
    refused = planted["calibration-gap"][1]
    assert refused.where.endswith(" qro:calibrationLink")
    assert refused.detail.startswith("the link is history-in-gap, not history-at-first-shot") and SNAP_1221 in refused.detail
    job = job_of(json.loads(read(planted["calibration-gap"][0], canonical.DESCRIPTOR)), S2_LINE)
    assert job["qro:calibrationLink"] == "history-at-first-shot" and job["qro:calibration"] == [{"@id": SNAP_1128}]


def known_answer_circuit(crate):
    """The morning manifest's entry for the known-answer circuit."""
    return next(c for j in json.loads(read(crate, MANIFEST))["jobs"] for c in j["circuits"] if c["name"] == "known-answer")


def test_qpy_only_is_the_forgery_the_registry_words_and_the_checker_accepts_it(planted, honest):
    """One QPY byte, with its digest, the commitment, IBM's echo inside the raw result and every digest recomputed; the gate
    list left."""
    crate, _, identity = planted["qpy-only"]
    old, qpy = honest[0], f"{BUNDLE}/known-answer.qpy"
    a, b = read(old, qpy), read(crate, qpy)
    assert len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1
    assert read(crate, f"{BUNDLE}/known-answer.gates.json") == read(old, f"{BUNDLE}/known-answer.gates.json")
    new = known_answer_circuit(crate)["commitment"]
    assert known_answer_circuit(crate)["isa_sha256"] == sha(b) and new != known_answer_circuit(old)["commitment"]
    record = json.loads(read(crate, KA_REC))
    assert (record["source"]["isa_sha256"], record["source"]["commitment"]) == (sha(b), new)
    assert record["digest"] == rec.record_digest(record)
    line = json.loads(read(crate, KA_LINE))
    assert line["commitments"] == [new]
    assert p1_forms.parse_ibm_result(read(crate, KA_RAW)).pubs[0].echo == new
    assert graph(json.loads(read(crate, canonical.DESCRIPTOR)))[f"#pub-{line['job_id']}-0"]["qro:commitment"] == new
    digest = sha(read(crate, MANIFEST))
    for name in ("known-answer", "coherence"):
        assert json.loads(read(crate, f"{plants.MORNING_RUN}/{name}-line.json"))["bundle_sha256"] == digest
        assert json.loads(read(crate, f"{plants.MORNING_RUN}/{name}-submitting.json"))["bundle_sha256"] == digest
    assert identity != honest[1]


def test_calibration_restamped_is_a_snapshot_of_equal_values_under_another_stamp_and_no_link_moves(planted, honest):
    crate, _, _ = planted["calibration-restamped"]
    new, old = json.loads(read(crate, canonical.DESCRIPTOR)), honest[2]
    added = sorted(set(graph(new)) - set(graph(old)))
    assert [i for i in added if "File" in types_of(graph(new)[i])] == [added[0]] and added[0].startswith(plants.IBM + "/properties-")
    snap = graph(new)[added[0]]
    assert snap["qro:valuesDigest"] == graph(new)[SNAP_0902]["qro:valuesDigest"]
    assert snap["qro:stamp"] < graph(new)[SNAP_0902]["qro:stamp"]
    for e in old["@graph"]:
        if "qro:Job" in types_of(e):
            n = graph(new)[e["@id"]]
            assert (n["qro:calibrationLink"], n["qro:calibration"]) == (e["qro:calibrationLink"], e["qro:calibration"])


def spelled(x, keep_dates):
    if type(x) in (int, float):
        return {"n": struct.pack(">d", float(x)).hex()}
    if isinstance(x, dict):
        return {k: spelled(v, keep_dates) for k, v in x.items() if keep_dates or k != "date"}
    return [spelled(v, keep_dates) for v in x] if isinstance(x, list) else x


def test_a_digest_that_kept_the_dates_would_tell_the_restamped_snapshot_from_its_original(planted):
    """The control of the control: it is the dates-left-out recipe that makes the two equal, not an accident of the values."""
    crate = planted["calibration-restamped"][0]
    new = next(p for p in Path(crate, *plants.IBM.split("/")).glob("properties-*.json"))
    one, two = json.loads(new.read_bytes()), json.loads(read(crate, SNAP_0902))
    moved = sum(a != b for a, b in zip(sorted(_dates(one)), sorted(_dates(two))))
    assert moved >= 400
    assert dates_digest(one, False) == dates_digest(two, False) and dates_digest(one, True) != dates_digest(two, True)
    assert one["last_update_date"] != two["last_update_date"]


def dates_digest(doc, keep_dates):
    """The values-digest's recipe, with the dates kept if asked: the stamp is left out either way."""
    body = {k: v for k, v in doc.items() if k != "last_update_date"}
    return sha(json.dumps(spelled(body, keep_dates), sort_keys=True, separators=(",", ":")).encode())


def _dates(x):
    if isinstance(x, dict):
        for k, v in x.items():
            if k == "date":
                yield v
            else:
                yield from _dates(v)
    elif isinstance(x, list):
        for v in x:
            yield from _dates(v)


def test_shot_moved_resealed_moves_exactly_one_shot_and_every_record_agrees_with_the_new_bytes(planted, honest):
    crate, _, identity = planted["shot-moved-resealed"]
    old, new = (p1_forms.parse_ibm_result(read(c, COH_RAW)) for c in (honest[0], crate))
    before, after = p1_decode.ibm_counts(old.pubs[0], "msb-first"), p1_decode.ibm_counts(new.pubs[0], "msb-first")
    gained = {k: after.get(k, 0) - before.get(k, 0) for k in set(before) | set(after) if after.get(k, 0) != before.get(k, 0)}
    assert sorted(gained.values()) == [-1, 1]
    assert p1_decode.ibm_counts(old.pubs[1], "msb-first") == p1_decode.ibm_counts(new.pubs[1], "msb-first")
    assert old.pubs[0].echo == new.pubs[0].echo and old.shots == new.shots
    run = rec.device_run(read(crate, COH_REC0), "record")
    assert run.counts == after and run.digest == rec.record_digest(run.doc)
    result = json.loads(read(crate, plants.Forge(crate).result_record(COH_LINE)[0]))
    assert result["committed"]["sha256"] == result["ibm_copy"]["sha256"] == sha(read(crate, COH_RAW))
    assert identity != honest[1]


# -- the study's first wording of `qpy-only`: refused, not accepted -------------------------------------------------------------------------
def test_qpy_only_as_the_study_first_worded_it_is_refused_because_the_echo_inside_the_raw_is_unchanged(crate):
    """Digests and commitment recomputed in every record the producer wrote, the gate list left, the raw result untouched:
    IBM's echo still holds the commitment the QPY had, and step 4 holds a commitment to that echo."""
    commitment, changed = plants.forge_qpy(crate, echo=False)

    def claim(g):
        for e in g:
            if e["@id"] == f"#pub-{json.loads(read(crate, KA_LINE))['job_id']}-0":
                e["qro:commitment"] = commitment
    plants.patch(crate, claim, reseal=changed)
    refused = p1_verdict(crate)
    assert refused.name == "commitment" and refused.where == f"{KA_RAW} pub_results[0]"
    assert f"the commitment recomputes to {commitment}" in refused.detail


def test_the_same_forgery_cannot_even_be_regenerated_since_the_generator_holds_the_echo_too(crate):
    plants.forge_qpy(crate, echo=False)
    g = guard(crate)
    assert g.guard == "G4" and "IBM's echo" in g.detail


# -- the variants of the controls ----------------------------------------------------------------------------------------------------------
def test_calibration_late_by_a_newest_value_the_snapshot_stamped_before_and_measured_after(crate):
    """Sheet-01's job (first shot 12:22:00) under 12:21:18, whose newest value date, 12:24:06, is after the shot."""
    plants.patch(crate, lambda g: next(e for e in g if e.get("qro:line") == {"@id": S1_LINE}).update(
        {"qro:calibration": [{"@id": SNAP_1221}]}))
    refused = p1_verdict(crate)
    assert refused.name == "calibration-link" and "last measured 2026-10-05T12:24:06" in refused.detail


def test_a_gap_that_is_not_one_is_refused_too_sheet_1s_12_21_18_was_still_being_measured(crate):
    def claim(g):
        job = next(e for e in g if e.get("qro:line") == {"@id": S1_LINE})
        job["qro:calibrationLink"], job["qro:calibration"] = "history-in-gap", [{"@id": SNAP_1128}, {"@id": SNAP_1221}]
    plants.patch(crate, claim)
    refused = p1_verdict(crate)
    assert refused.name == "calibration-link"
    assert refused.detail.startswith("the link is history-at-first-shot, not history-in-gap")


def test_an_honest_crate_with_a_verdict_file_that_lies_is_accepted(crate):
    """No step reads Quantum-Film's verdict: the known answer is held by the circuit and the raw bytes."""
    verdict = f"{MORNING_KA}-verdict.json"
    forge(crate).edit_json(verdict, lambda o: o.update(holds=False, modal=[], share=0.0))
    plants.patch(crate, lambda g: None, reseal=[verdict])
    assert p1_verdict(crate) is None


def test_the_manifests_known_answer_mirrored_with_the_order_changes_nothing(crate):
    f = forge(crate)
    f.edit_json(MANIFEST, lambda m: m.update(known_answer=[15 - q for q in m["known_answer"]]))
    f.reseal_bundle(plants.MORNING_BUNDLE)

    def decode(g):
        job = job_of({"@graph": g}, KA_LINE)
        next(e for e in g if e["@id"] == "#decode-" + job["qro:jobId"])["qro:bitOrder"] = "lsb-first"
    plants.patch(crate, decode, reseal=f.changed)
    assert p1_verdict(crate).name == "known-answer"


def test_a_raw_result_of_another_shot_count_filed_under_a_known_answers_id_is_count_unpaid_first(crate):
    plants.write_file(crate, KA_RAW, read(crate, COH_RAW))
    plants.patch(crate, lambda g: None, reseal=[KA_RAW])
    refused = p1_verdict(crate)
    assert refused.name == "count-unpaid" and refused.where == f"{KA_RAW} qro:shots"


def test_a_shot_moved_and_nothing_recomputed_is_the_digests_refusal(crate):
    data, _, _ = plants.moved_shot(read(crate, COH_RAW))
    plants.write_file(crate, COH_RAW, data)
    assert p1_verdict(crate).name == "raw-digest"


def test_a_shot_moved_and_only_the_files_digest_resealed_is_caught_by_step_9_since_the_record_says_otherwise(crate):
    """The producer who reseals the raw result and not the record: steps 4, 5 and 8 hold, the regenerated metadata does not."""
    data, _, _ = plants.moved_shot(read(crate, COH_RAW))
    plants.write_file(crate, COH_RAW, data)
    plants.patch(crate, lambda g: None, reseal=[COH_RAW])
    refused = p1_verdict(crate)
    assert refused.name == "metadata-generated"
    assert guard(crate).guard == "G5"


def test_altering_only_the_copy_a_job_ran_is_accepted_by_steps_4_5_and_8_while_another_copy_keeps_the_digest(crate):
    """The verifier's note on step 4: it finds a committed file by digest among the crate's copies. The morning bundle's
    known-answer QPY and sheet-01's are one file; alter the morning's alone, and the commitment's QPY is still in the crate.
    Step 9 refuses it: the manifest's digest of the morning's copy is no longer that file's."""
    qpy = f"{BUNDLE}/known-answer.qpy"
    assert read(crate, qpy) == read(crate, f"{plants.IBM}/sheet-01/bundle/known-answer.qpy")
    plants.write_file(crate, qpy, read(crate, qpy)[:-1] + bytes([read(crate, qpy)[-1] ^ 1]))
    plants.patch(crate, lambda g: None, reseal=[qpy])
    checker.load()
    md = reader.read(read(crate, canonical.DESCRIPTOR))
    for step in (p1_steps.step4, p1_steps.step5, p1_steps.step8):
        step(crate, md)                                    # none of them refuses
    assert p1_verdict(crate).name == "metadata-generated" and guard(crate).guard == "G1"


def with_stamp(data, stamp):
    doc = json.loads(data)
    doc["last_update_date"] = stamp
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def test_the_older_of_two_named_snapshots_is_told_by_stamp_where_their_ids_sort_the_other_way(crate):
    """The verifier's first note on step 8. A snapshot of Quantum-Film's own, stamped 12:25:00, after the 12:21:18 and before
    sheet-02's first shot (12:26:17), its values measured before it: the newest-stamped valid snapshot, so sheet-02's gap
    link is [11:28:27, 12:25:00]. Its id, in 2026-10-05's directory, sorts before 11:28:27's, in 2026-10-14's: the stored list
    names the later snapshot first."""
    late = f"{plants.IBM}/properties-20261005T122500Z.json"
    plants.write_file(crate, late, with_stamp(read(crate, SNAP_1221), "2026-10-05T12:25:00Z"))
    plants.rebuild(crate)
    job = job_of(json.loads(read(crate, canonical.DESCRIPTOR)), S2_LINE)
    named = [r["@id"] for r in job["qro:calibration"]]
    assert named == [late, SNAP_1128] and job["qro:calibrationLink"] == "history-in-gap"
    snaps = graph(json.loads(read(crate, canonical.DESCRIPTOR)))
    assert snaps[late]["qro:stamp"] > snaps[SNAP_1128]["qro:stamp"] and late < SNAP_1128
    assert p1_verdict(crate) is None


# -- the toolkit, which P2's plants use -----------------------------------------------------------------------------------------------------
def test_every_json_file_of_the_twin_is_written_in_the_style_the_forger_writes_it_in(honest):
    crate = honest[0]
    seen = 0
    for p in sorted(crate.rglob("*.json")):
        rel = p.relative_to(crate).as_posix()
        if rel != canonical.DESCRIPTOR and not rel.startswith("question/"):       # question/law.json is P2's, in no style of the forger's
            data = p.read_bytes()
            assert plants.STYLES[plants.style_of(rel)](json.loads(data)) == data, rel
            seen += 1
    assert seen > 40


def test_the_forgers_style_is_told_by_the_place_of_a_file_and_is_what_json_dumps_writes_in_it():
    ibm = "2026-10-05/ibm/ibm_kingston"
    assert plants.style_of(f"{ibm}/run/known-answer-raw.json") == "raw"
    assert plants.style_of(f"{ibm}/properties-20261005T090246Z.json") == "snapshot"
    assert plants.style_of("2026-10-14/ibm-refetch/ibm_kingston/properties-20261005T090246Z.json") == "record"
    assert plants.style_of(f"{ibm}/run/known-answer-line.json") == "record"
    doc = {"b": [1, {"d": 1, "c": 2}], "a": "\u00e9"}
    assert plants.STYLES["raw"](doc) == b'{"b": [1, {"d": 1, "c": 2}], "a": "\\u00e9"}'
    assert plants.STYLES["snapshot"](doc) == b'{"a":"\\u00e9","b":[1,{"c":2,"d":1}]}\n'
    assert plants.STYLES["record"](doc) == b'{\n "a": "\\u00e9",\n "b": [\n  1,\n  {\n   "c": 2,\n   "d": 1\n  }\n ]\n}\n'


def test_a_link_copy_is_made_of_links_where_the_host_links_and_of_copies_where_it_does_not(tmp_path):
    import os
    src = plants.pristine_twin()
    copy = plants.link_copy(src, tmp_path)
    try:                                    # whether this host links from the twin's place to this one is what link_copy meets
        os.link(next(p for p in sorted(src.rglob("*")) if p.is_file()), tmp_path / "probe")
        links = True
    except OSError:
        links = False
    names = sorted(p.relative_to(copy).as_posix() for p in copy.rglob("*") if p.is_file())
    assert names == sorted(p.relative_to(src).as_posix() for p in src.rglob("*") if p.is_file()) and len(names) == 74       # the twin's 72 records, the descriptor and P2's question/law.json
    for rel in names:
        assert read(copy, rel) == read(src, rel)
    some = rel.split("/")
    assert os.path.samefile(copy.joinpath(*some), src.joinpath(*some)) == links


def test_a_change_to_a_bundle_file_ripples_to_the_manifest_the_lines_and_the_markers_and_the_crate_regenerates(crate):
    """P2's compile-broken in one line: the law gate list altered, its digest recomputed everywhere the records hold it."""
    f = forge(crate)
    gates = f"{BUNDLE}/law.gates.json"
    old = sha(f.read(gates))
    f.change_bundle_file(gates, f.read(gates) + b"\n", "gates_sha256")
    manifest = json.loads(f.read(MANIFEST))
    held = [c["gates_sha256"] for j in manifest["jobs"] for c in j["circuits"] if c["name"] == "law"]
    assert held == [sha(f.read(gates))] != [old]
    assert sorted(f.changed) == sorted([gates, MANIFEST] + [f"{plants.MORNING_RUN}/{n}-{t}.json" for n in (
        "known-answer", "coherence") for t in ("line", "submitting")])
    plants.rebuild(crate)
    assert p1_verdict(crate) is None


def test_a_record_of_the_read_that_grew_has_its_manifest_entry_resealed_in_size_and_in_digest(crate):
    f = forge(crate)
    _, job_record = f.result_record(KA_LINE)
    before = len(f.read(job_record))
    f.edit_json(job_record, lambda o: o.update(note="x" * 40))
    f.reseal_entry(job_record)
    data = f.read(job_record)
    directory = "/".join(job_record.split("/")[:2])
    entry = next(e for e in json.loads(f.read(f"{directory}/MANIFEST.json"))["files"]
                 if e["path"] == job_record[len(directory) + 1:])
    assert len(data) > before and (entry["bytes"], entry["sha256"]) == (len(data), sha(data))


def test_patch_edits_the_metadata_and_reseals_only_the_files_named(crate):
    before = json.loads(read(crate, canonical.DESCRIPTOR))
    plants.write_file(crate, KA_RAW, read(crate, COH_RAW))
    plants.patch(crate, lambda g: g[1].update(name="renamed"), reseal=[KA_RAW])
    after = json.loads(read(crate, canonical.DESCRIPTOR))
    changed = [i for i in graph(before) if graph(before)[i] != graph(after)[i]]
    assert sorted(changed) == sorted(["./", KA_RAW]) and graph(after)[KA_RAW]["sha256"] == sha(read(crate, KA_RAW))


def test_rebuild_regenerates_from_the_records_and_keeps_the_header(crate):
    before = json.loads(read(crate, canonical.DESCRIPTOR))
    root = before["@graph"][1]
    plants.patch(crate, lambda g: g[1].update(name="a name the generator never wrote"))
    plants.rebuild(crate)
    after = json.loads(read(crate, canonical.DESCRIPTOR))
    assert after == before and after["@graph"][1]["qro:writtenAt"] == root["qro:writtenAt"]
    assert reader.read(read(crate, canonical.DESCRIPTOR))


def test_rebuild_of_a_crate_whose_records_disagree_raises_the_guard_rather_than_write_it(crate):
    plants.write_file(crate, f"{BUNDLE}/law.qasm", read(crate, f"{BUNDLE}/law.qasm") + b"//\n")
    with pytest.raises(G.GuardError) as x:
        plants.rebuild(crate)
    assert x.value.guard == "G1"


@pytest.mark.parametrize("name", SEVEN)
def test_a_control_planted_in_a_hard_linked_copy_writes_through_no_link(tmp_path, name):
    """What the real crate's plants rely on: the twin's pristine copy is linked into a working one, a fault is planted there,
    and the pristine files are as they were."""
    box = Sandbox(tmp_path)
    plants.FAULTS[name](box.root)
    box.verify_pristine()
    differs = [rel for rel in box.files if not box.root.joinpath(*rel.split("/")).is_file()
               or read(box.root, rel) != read(box.pristine, rel)]
    added = [p for p in box.root.rglob("*") if p.is_file() and p.relative_to(box.root).as_posix() not in box.files]
    assert differs or added, "the fault changed no file"


def test_a_control_is_a_function_of_a_built_crate_and_the_registered_plant_is_that_function_on_a_copy_of_the_twin(tmp_path):
    direct = plants.FAULTS["calibration-late"](plants.twin_crate(tmp_path / "a"))
    registered = plants.PLANTS["calibration-late"](tmp_path / "b")
    assert direct.name == registered.name == "crate" and direct != registered
    assert read(direct, canonical.DESCRIPTOR) == read(registered, canonical.DESCRIPTOR)


def test_the_pristine_twin_is_not_built_while_the_seam_is_pinned(monkeypatch):
    monkeypatch.setattr(plants, "_PRISTINE", [])
    monkeypatch.setattr(G, "p2_module", lambda: None)
    with pytest.raises(RuntimeError, match="before the pin"):
        plants.pristine_twin()


def test_the_p1_alone_twin_is_not_built_while_the_seam_is_pinned_and_holds_none_of_p2s(monkeypatch):
    """One tree each: the twin of the tests that pin P2's module absent is built with it absent for the build, and refuses to be
    built under a pin set earlier, and the twin of the tree as merged holds P2's file and the P1-alone twin does not."""
    monkeypatch.setattr(plants, "_ALONE", [])
    monkeypatch.setattr(G, "p2_module", lambda: None)
    with pytest.raises(RuntimeError, match="before the pin"):
        plants.pristine_twin_alone()
    monkeypatch.undo()
    alone, merged = plants.pristine_twin_alone(), plants.pristine_twin()
    assert not (alone / "question").exists() and (merged / "question" / "law.json").is_file()
    assert G.p2_module is not None and getattr(G.p2_module, "__module__", None) == G.__name__    # the build put it back


def test_the_twin_this_module_plants_in_is_the_one_the_generator_makes_of_its_copy(honest):
    crate, identity, md = honest
    assert canonical.body_digest(generated(crate)) == identity == canonical.body_digest(md)
    assert read_json(crate, KA_LINE)["job_id"]


# -- limit 16: a job copied under new ids is accepted by every step, the real generator included (the verifier's D4) ----------------------------
OTHER_JOB = "d" + "q" * 19             # the shape of an IBM job id that is nobody's


def test_a_job_copied_under_new_ids_is_accepted_by_every_step_the_real_generator_included(crate):
    """The manifest names a second coherence job with the same circuits. Its line, marker, metrics wrapper, raw result and
    records are the first's, copied under a new job id; so are the read's two records of it, with their MANIFEST entries. The
    metadata is regenerated by the real generator, which holds the records to one another, and they agree. Nothing compares one
    job with another: all nine steps accept a crate that holds five jobs, where the first held four."""
    f = forge(crate)
    run = f"{plants.IBM}/run"

    def second(m):
        job = copy.deepcopy(next(j for j in m["jobs"] if j["job"] == "coherence"))
        job["job"] = "coherence2"
        m["jobs"].append(job)
    f.edit_json(MANIFEST, second)

    def copy_as(src, dst, edit):
        doc = json.loads(f.read(src))
        edit(doc)
        f.put_json(dst, doc)
    copy_as(f"{run}/coherence-line.json", f"{run}/coherence2-line.json", lambda o: o.update(job_id=OTHER_JOB))
    copy_as(f"{run}/coherence-submitting.json", f"{run}/coherence2-submitting.json", lambda o: o.update(job="coherence2"))
    copy_as(f"{run}/coherence-metrics.json", f"{run}/coherence2-metrics.json", lambda o: o.update(job_id=OTHER_JOB))
    f.write(f"{run}/coherence2-raw.json", f.read(COH_RAW))
    for k, name in ((0, "coherence-xx"), (1, "coherence-yy")):
        record = f.json(f"{run}/coherence-pub{k}-{name}.json")
        record["source"]["job_id"] = OTHER_JOB
        f.put_record(f"{run}/coherence2-pub{k}-{name}.json", record)
    f.reseal_bundle(BUNDLE)
    result, job = f.result_record(COH_LINE)
    new_job = f"{plants.REFETCH}/ibm_kingston/{OTHER_JOB}.json"
    new_result = f"{plants.RESULTS}/ibm_kingston/{OTHER_JOB}.json"
    copy_as(job, new_job, lambda o: o.update(job_id=OTHER_JOB))
    copy_as(result, new_result, lambda o: (o.update(job_id=OTHER_JOB),
                                           o["committed"].update(path=G.RECORDS_DIR + f"{run}/coherence2-raw.json")))
    for rel in (new_job, new_result):
        directory = rel.rsplit("/", 2)[0]
        data = f.read(rel)
        f.edit_json(f"{directory}/MANIFEST.json", lambda m, rel=rel, directory=directory, data=data: m["files"].append(
            {"bytes": len(data), "path": rel[len(directory) + 1:], "sha256": sha(data)}))
    plants.rebuild(crate)                                  # the real generator holds them, and writes five jobs
    assert len([e for e in json.loads(read(crate, canonical.DESCRIPTOR))["@graph"] if "qro:Job" in types_of(e)]) == 5
    assert p1_verdict(crate) is None


# -- G9's limit: a snapshot of the read dropped, its MANIFEST edited to match (P1.2's third verifier, D2) -----------------------------------------------
def test_a_snapshot_of_the_read_dropped_and_its_manifest_entry_taken_out_moves_a_link_and_is_accepted(crate):
    """The G9 row: a snapshot of the read dropped from the crate cannot move a link verdict unless the read's MANIFEST is
    edited to match, which is limit 1's producer. The twin's 12:21:18 snapshot taken out, its entry taken out of the
    MANIFEST and the metadata regenerated: every step accepts the crate, and sheet-02's job moves from history-in-gap to
    history-at-first-shot. (On the real crate a job's read record names that snapshot, and G7 refuses the same edit.)"""
    before = job_of(json.loads(read(crate, canonical.DESCRIPTOR)), S2_LINE)["qro:calibrationLink"]
    name = SNAP_1221[len(plants.REFETCH) + 1:]
    forge(crate).edit_json(READ_MANIFEST, lambda m: m.update(files=[e for e in m["files"] if e["path"] != name]))
    crate.joinpath(*SNAP_1221.split("/")).unlink()
    plants.rebuild(crate)
    assert p1_verdict(crate) is None
    after = job_of(json.loads(read(crate, canonical.DESCRIPTOR)), S2_LINE)["qro:calibrationLink"]
    assert (before, after) == ("history-in-gap", "history-at-first-shot")


# -- the classes of carried bytes the checker holds by their digests alone (the verifier's D5) ---------------------------------------------------------
def span_stop(o):
    o["result_metadata"]["execution"]["execution_spans"]["__value__"]["spans"][0]["__value__"]["stop"]["__value__"] = \
        "2026-10-05T10:27:01.376977"


def an_uncarried_entry(o):
    next(e for e in o["files"] if e["path"].startswith("ibm_fez/")).update(bytes=1)


READ_MANIFEST = f"{plants.REFETCH}/MANIFEST.json"
CARRIED = [
    ("a verdict file's field", f"{MORNING_KA}-verdict.json", lambda o: o.update(share=0.5)),
    ("a device-run record's law", KA_REC, lambda o: o["law"].update(L=5)),
    ("a device-run record's code", KA_REC, lambda o: o["code"].update(quantum_film="0.2.0")),
    ("a device-run record's source.fixed_at", KA_REC, lambda o: o["source"].update(fixed_at="2026-10-05T10:27:09.310292Z")),
    ("a metrics wrapper's job, a field but its created time", f"{MORNING_KA}-metrics.json", lambda o: o["job"].update(cost=61)),
    ("a metrics wrapper's metrics, a field but its timestamps", f"{MORNING_KA}-metrics.json",
     lambda o: o["metrics"]["usage"].update(value=0.0329)),
    ("a metrics wrapper's finished time, later: held only as the span's upper bound", f"{MORNING_KA}-metrics.json",
     lambda o: o["metrics"]["timestamps"].update(finished="2026-10-05T10:31:03.702386Z")),
    ("a metrics wrapper's second copy of the execution span", f"{MORNING_KA}-metrics.json", span_stop),
    ("a submitting marker's begun_at", f"{MORNING_KA}-submitting.json",
     lambda o: o.update(begun_at="2026-10-05T10:26:53.177285Z")),
    ("the read's MANIFEST header", READ_MANIFEST, lambda o: o.update(selection="some")),
    ("the read's MANIFEST entry for a file the crate does not carry", READ_MANIFEST, an_uncarried_entry),
    ("the read's README", "2026-10-14/README.md", None),
    ("a log of the read", "2026-10-14/ibm-refetch.log", None),
    ("Quantum-Film's licence text", "LICENSE-quantum-film", None),
]


@pytest.mark.parametrize("label, rel, edit", CARRIED, ids=[c[0] for c in CARRIED])
def test_a_leaf_of_a_carried_file_changed_with_only_its_own_digest_resealed_is_accepted_by_every_step(crate, label, rel, edit):
    """Limit 21. The generator derives a value from a field and holds the other records to it; these fields it derives nothing
    from, and no step reads: the file is held by its digest and size alone, and a changed leaf, resealed, is a crate that
    passes. (Not a hole the guards left: the stated class of what is carried and not read.)"""
    f = forge(crate)
    assert p1_verdict(crate) is None
    before = read(crate, rel)
    if edit is None:
        f.write(rel, before + b"A line the producer added.\n")
    else:
        doc = f.json(rel)
        edit(doc)
        if doc.get("format", "").startswith("quantum-film/device-run"):
            f.put_record(rel, doc)                         # a record's own digest is part of the record
        else:
            f.put_json(rel, doc)
    assert read(crate, rel) != before
    plants.patch(crate, lambda g: None, reseal=[rel])
    assert p1_verdict(crate) is None, label
