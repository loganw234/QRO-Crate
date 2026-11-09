"""The unit generator, `qro-p5-unit` (P5's design, item 8; qro/p5_generate.py): the twin is accepted by all nine steps and
regenerates to what was built; every guard GU1 to GU10 has a planted fault that trips it and no other first, and each of P1's
guards the generator calls (G2 to G9, imported from qro.p1_guards, never copied) has one that trips it with P1's letter, so that
a weakened guard fails this stage as well as P1's; one monkeypatch of p1_guards.hold switches them all off.

A fault is made on a copy of the built twin by the forger (controls.plants_p5.Forge), which recomputes every digest a record
holds over what it changed, so the guard decides and not a stale digest."""
import json

import pytest
from p5_support import forge, guard, letter, no_link_left_behind, no_network, twin  # noqa: F401

from controls import plants_p5 as P
from qro import canonical, checker, p1_guards, p5_generate as G, p5_unit as U, reader

pytestmark = pytest.mark.usefixtures("no_network", "no_link_left_behind")
KINGSTON, FEZ = "fake_kingston", "fake_fez"
checker.load()                                   # every parcel's steps, whichever test runs first
RUN = "unit/{}/run/{}"
QPU_FILMS = frozenset((d, f"film-{p}") for d in U.DEVICE_SETS["qpu"] for p in (1, 2, 3))


def metadata(crate):
    return reader.read((crate / canonical.DESCRIPTOR).read_bytes())


# -- the twin, whole ------------------------------------------------------------------------------------------------
def test_the_twin_is_accepted_by_all_nine_steps(tmp_path):
    crate = twin(tmp_path)
    checker.load()
    md = checker.check(crate)
    assert md["@graph"][1]["qro:generator"] == "qro-p5-unit"


def test_the_metadata_regenerates_to_what_was_built(tmp_path):
    crate = twin(tmp_path)
    built = metadata(crate)
    again = G.unit(crate)
    assert canonical.dumps(canonical.body(again)) == canonical.dumps(canonical.body(built))


def test_the_twin_has_the_unit_the_recipe_describes(tmp_path):
    md = metadata(twin(tmp_path))
    by_type = {}
    for e in md["@graph"]:
        for t in canonical.types(e):
            by_type.setdefault(t, []).append(e)
    assert len(by_type["qro:Job"]) == 18 and len(by_type["qro:Pub"]) == 3 * (3 * 2 + 3 * 3)
    assert len(by_type["qro:Decode"]) == 18 and len(by_type["qro:RawResult"]) == 18 and len(by_type["qro:Compile"]) == 3
    assert len(by_type["IndividualProduct"]) == 3 and {d["qro:deviceKind"] for d in by_type["IndividualProduct"]} == {"simulator"}
    (unit,) = by_type["qro:Unit"]
    assert unit["qro:recipe"] == U.recipe_sha256(128) and unit["qro:contributor"] == "withheld"
    assert unit["qro:kitTag"] == P.KIT_TAG and len(unit["qro:unitJobs"]) == 18
    assert {j["qro:kitCommit"] for j in by_type["qro:Job"]} == {P.KIT_COMMIT}
    assert {j["qro:calibrationLink"] for j in by_type["qro:Job"]} == {"unexposed"}
    assert {j["startTime"] for j in by_type["qro:Job"]} == {"unknown"} and {j["qro:clock"] for j in by_type["qro:Job"]} == {"local"}
    assert len(by_type["qro:Hold"]) == 3 and len(by_type["qro:Measurement"]) > 0


def test_every_decode_names_its_devices_first_control_pub_zero(tmp_path):
    md = metadata(twin(tmp_path))
    byid = {e["@id"]: e for e in md["@graph"]}
    for d in (e for e in md["@graph"] if "qro:Decode" in canonical.types(e)):
        known = byid[d["qro:knownAnswer"]["@id"]]
        assert known["qro:role"] == "known-answer" and known["@id"].endswith("-0")
        assert byid[d["object"][0]["@id"]]["@id"].split("/")[1] == known["qro:record"]["@id"].split("/")[1]


def test_a_qpu_twin_is_accepted_and_carries_execution_spans_and_no_calibration_without_a_read(tmp_path):
    crate = twin(tmp_path, kind="qpu")
    checker.load()
    md = checker.check(crate)
    jobs = [e for e in md["@graph"] if "qro:Job" in canonical.types(e)]
    assert {j["qro:calibrationLink"] for j in jobs} == {"unknown"} and all(j["startTime"] != "unknown" for j in jobs)
    assert {j["qro:clock"] for j in jobs} == {"provider"}
    assert U.read(crate).kind == "qpu"


def test_a_qpu_twin_with_the_owners_read_is_accepted_and_its_links_are_history_links(tmp_path):
    crate = twin(tmp_path, kind="qpu", read=True, skip=QPU_FILMS)       # control jobs only: one role a job
    md = checker.check(crate)
    jobs = [e for e in md["@graph"] if "qro:Job" in canonical.types(e)]
    assert {j["qro:calibrationLink"] for j in jobs} == {"history-at-first-shot"} and all(j["qro:calibration"] for j in jobs)
    assert len([e for e in md["@graph"] if "qro:Snapshot" in canonical.types(e)]) == 3


def test_a_failed_job_is_a_job_with_a_status_file_and_no_result(tmp_path):
    crate = P.build_unit(tmp_path, failed=frozenset({(FEZ, "film-3")}))
    md = checker.check(crate)
    job = next(e for e in md["@graph"] if e["@id"].startswith("#job-") and e["name"] == f"film-3 job on {FEZ}")
    assert "object" not in job and any(r["@id"].endswith("-status.json") for r in job["result"])
    st = U.read(crate).status()
    assert st.complete == {"fake_kingston": True, "fake_marrakesh": True, FEZ: False}
    assert st.missing == ((FEZ, "film-3", "failed"),)


# -- GU10 -----------------------------------------------------------------------------------------------------------------
def test_gu10_a_file_that_fits_no_layout_is_refused(tmp_path):
    crate = twin(tmp_path)
    (crate / "unit" / FEZ / "notes.txt").write_bytes(b"a stray file\n")
    g = guard(crate)
    assert g.guard == "GU10" and "fits no layout" in g.detail


def test_gu10_an_id_written_twice_is_refused():
    entities = G._Entities()
    entities["#x"] = {"@id": "#x"}
    with pytest.raises(p1_guards.GuardError) as caught:
        entities["#x"] = {"@id": "#x"}
    assert caught.value.guard == "GU10"
    entities.shared({"@id": "#y", "v": 1})
    entities.shared({"@id": "#y", "v": 1})
    with pytest.raises(p1_guards.GuardError):
        entities.shared({"@id": "#y", "v": 2})
    with pytest.raises(TypeError):
        entities.setdefault("#z", {})


# -- GU1 ------------------------------------------------------------------------------------------------------------------
def test_gu1_a_changed_bundle_file_is_refused(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    rel = f"unit/{KINGSTON}/bundle/law.gates.json"
    f.write(rel, f.read(rel)[:-2] + b" \n")
    assert letter(crate) == "GU1"


def test_gu1_a_bundle_file_the_manifest_does_not_name_is_refused(tmp_path):
    crate = twin(tmp_path)
    forge(crate).write(f"unit/{KINGSTON}/bundle/extra.qasm", b"OPENQASM 2.0;\n")
    g = guard(crate)
    assert g.guard == "GU1" and "names no circuit" in g.detail


@pytest.mark.parametrize("edit, why", [
    (lambda m: m["unit"].update(recipe_sha256="0" * 64), "unit.recipe_sha256"),
    (lambda m: m["unit"].update(shots_divisor=64), "unit.shots_divisor"),
    (lambda m: m["jobs"][1]["circuits"][0].update(shots=m["jobs"][1]["circuits"][0]["shots"] + 1), "job table"),
    (lambda m: m["jobs"][0].update(max_execution_time=16), "job table"),
    (lambda m: m["jobs"][0]["circuits"][1].update(name="known-answer"), "job table"),
    (lambda m: m.update(known_answer=[0, 1, 3, 7, 11]), "known answer"),
    (lambda m: m["options"]["twirling"].update(enable_gates=True), "options"),
    (lambda m: m.pop("unit"), "unit block"),
    (lambda m: m["source"].update(path="somewhere/else.qasm"), "source"),
    (lambda m: m["jobs"][3]["circuits"][0].update(chain=list(reversed(m["jobs"][3]["circuits"][0]["chain"]))), "one chain"),
], ids=["recipe digest", "divisor", "a shot count", "a cap", "a PUB name", "the known answer", "an option", "no unit block",
        "the source", "a second chain"])
def test_gu1_a_manifest_that_is_not_the_recipes_is_refused(tmp_path, edit, why):
    crate = twin(tmp_path)
    forge(crate).edit_manifest(FEZ, edit)
    assert letter(crate) == "GU1"


def test_gu1_options_that_are_not_the_recipes_but_digest_consistently_are_refused(tmp_path):
    """The options' digest is the manifest's own; the recipe's options are the recipe's: dynamical decoupling turned on, its
    digest recomputed, and the commitments unchanged (they bind the digest, so the forger recomputes nothing else here)."""
    from qro import p1_commit
    crate = twin(tmp_path)

    def on(m):
        m["options"]["dynamical_decoupling"]["enable"] = True
        m["options_sha256"] = p1_commit.options_digest(m["options"])
    forge(crate).edit_manifest(KINGSTON, on)
    g = guard(crate)
    assert g.guard == "GU1" and "not the recipe's" in g.detail


def test_gu1_two_pubs_sharing_a_salt_and_a_commitment_are_refused(tmp_path):
    crate = twin(tmp_path)

    def share(m):
        a, b = m["jobs"][0]["circuits"][0], m["jobs"][2]["circuits"][0]
        b["salt"], b["commitment"] = a["salt"], a["commitment"]
    forge(crate).edit_manifest(KINGSTON, share)
    g = guard(crate)
    assert g.guard == "GU1" and "salt" in g.detail


def test_gu1_a_logical_circuit_not_derived_from_the_source_is_refused(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    rel = f"unit/{KINGSTON}/bundle/law.qasm"
    new = f.read(rel).replace(b"h q[4];", b"h q[5];", 1)
    f.write(rel, new)
    digest = P.sha(new)
    f.edit_manifest(KINGSTON, lambda m: [c.update(circuit_sha256=digest) for j in m["jobs"] for c in j["circuits"]
                                         if c["name"] == "law"])
    g = guard(crate)
    assert g.guard == "GU1" and "derived from the source" in g.detail


def test_gu1_the_source_circuit_must_be_the_one_ed767c01(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    f.write(U.SOURCE_PATH, f.read(U.SOURCE_PATH) + b"x q[0];\n")
    g = guard(crate)
    assert g.guard == "GU1" and "is not ed767c01bd4b851d" in g.detail
    f.remove(U.SOURCE_PATH)
    g = guard(crate)
    assert g.guard in ("GU1", "GU10") and ("source" in g.detail or "fits no layout" in g.detail or "carries" in g.detail)


def test_gu1_a_bundle_missing_its_manifest_is_refused(tmp_path):
    crate = twin(tmp_path)
    forge(crate).remove(f"unit/{FEZ}/bundle/manifest.json")
    assert letter(crate) in ("GU1", "GU2")


# -- GU2 ------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("edit", [
    lambda u: u.update(recipe_sha256="1" * 64), lambda u: u.update(devices=list(reversed(u["devices"]))),
    lambda u: u.update(bundles=list(reversed(u["bundles"]))), lambda u: u.update(kind="qpu"),
    lambda u: u.update(route="moth"), lambda u: u.update(recipe="qro-unit/2"), lambda u: u.update(format="x/v1"),
    lambda u: u.update(shots_divisor=3), lambda u: u.pop("contributor"), lambda u: u.update(kit_commit="not a commit"),
], ids=["digest", "device order", "bundle order", "kind", "route", "recipe", "format", "divisor", "no contributor",
        "commit"])
def test_gu2_a_unit_file_that_is_not_the_recipes_is_refused(tmp_path, edit):
    crate = twin(tmp_path)
    f = forge(crate)
    u = f.json("unit/UNIT.json")
    edit(u)
    f.put("unit/UNIT.json", u)
    assert letter(crate) == "GU2"


def test_gu2_a_bundle_whose_manifest_is_another_kind_than_the_units_is_refused(tmp_path):
    crate = twin(tmp_path)
    forge(crate).edit_manifest(KINGSTON, lambda m: m.update(kind="qpu"))
    assert letter(crate) in ("GU1", "GU2")


def test_gu2_a_shots_divisor_belongs_to_the_local_route_only(tmp_path):
    with pytest.raises(p1_guards.GuardError) as caught:
        P.build_unit(tmp_path, kind="qpu", divisor=128)
    assert caught.value.guard == "GU2" and "local route" in caught.value.detail


# -- P1's guards, each reached through the generator --------------------------------------------------------------------------
def test_g2_a_line_whose_commitments_are_not_the_manifests_is_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    rel = RUN.format(KINGSTON, "control-1-line.json")
    line = f.json(rel)
    line["commitments"].reverse()
    f.put(rel, line)
    assert letter(crate) == "G2"


def test_g2_a_marker_that_names_another_job_is_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    rel = RUN.format(KINGSTON, "film-2-submitting.json")
    marker = f.json(rel)
    marker["job"] = "film-3"
    f.put(rel, marker)
    assert letter(crate) == "G2"


def test_g2_a_line_of_another_bundle_is_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    rel = RUN.format(FEZ, "film-3-line.json")
    line = f.json(rel)
    line["bundle_sha256"] = "2" * 64
    f.put(rel, line)
    assert letter(crate) == "G2"


def test_gu3_a_job_id_two_jobs_share_is_refused(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    first = f.json(RUN.format(KINGSTON, "control-1-line.json"))["job_id"]
    rel = RUN.format(KINGSTON, "film-1-line.json")
    line = f.json(rel)
    line["job_id"] = first
    f.put(rel, line)
    g = guard(crate)
    assert g.guard == "GU3" and "is also" in g.detail


def test_g3_a_pub_with_no_record_is_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path)
    forge(crate).remove(RUN.format(KINGSTON, "film-1-pub1-coherence-xx.json"))
    assert letter(crate) == "G3"


def test_g3_a_record_whose_source_is_not_the_manifests_is_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path)
    forge(crate).edit_record(KINGSTON, "film-1", 0, lambda r: r["source"].update(shots=r["source"]["shots"] + 1))
    assert letter(crate) == "G3"


def test_g3_a_record_whose_digest_is_not_its_bodys_is_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    rel = RUN.format(KINGSTON, "control-1-pub0-known-answer.json")
    doc = f.json(rel)
    doc["digest"] = "3" * 64
    f.put(rel, doc)
    assert letter(crate) == "G3"


def test_g4_a_commitment_that_does_not_recompute_from_the_records_inputs_is_refused_with_p1s_letter(tmp_path):
    """Manifest, line, record and IBM's echo all agree on a commitment the fourteen inputs do not give."""
    crate = twin(tmp_path)
    f = forge(crate)
    new = "ab" * 32
    old = f.json(f"unit/{KINGSTON}/bundle/manifest.json")["jobs"][0]["circuits"][0]["commitment"]
    f.edit_manifest(KINGSTON, lambda m: m["jobs"][0]["circuits"][0].update(commitment=new))
    rel = RUN.format(KINGSTON, "control-1-line.json")
    line = f.json(rel)
    line["commitments"][0] = new
    f.put(rel, line)
    f.edit_record(KINGSTON, "control-1", 0, lambda r: r["source"].update(commitment=new))
    raw = RUN.format(KINGSTON, "control-1-raw.json")
    f.write(raw, f.read(raw).replace(old.encode(), new.encode()))
    g = guard(crate)
    assert g.guard == "G4" and "recompute" in g.detail


def test_g4_ibms_echo_of_another_commitment_is_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    old = f.json(f"unit/{KINGSTON}/bundle/manifest.json")["jobs"][0]["circuits"][0]["commitment"]
    raw = RUN.format(KINGSTON, "control-1-raw.json")
    f.write(raw, f.read(raw).replace(old.encode(), ("cd" * 32).encode()))
    assert letter(crate) == "G4"


def test_g5_a_records_counts_that_are_not_the_raw_results_are_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path)

    def swap(r):
        r["counts"][0][1], r["counts"][-1][1] = r["counts"][-1][1] + 1, r["counts"][0][1] - 1
    forge(crate).edit_record(KINGSTON, "film-1", 0, swap)
    assert letter(crate) == "G5"


def test_g5_a_raw_result_with_other_shots_than_the_manifests_is_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    for pub in range(3):                                  # a job's PUBs share one shot count, so all three have 127 rows
        f.set_rows(KINGSTON, "film-1", pub, [P.outcome((0, 1, 2, 3, 4))] * 127)
    g = guard(crate)
    assert g.guard == "G5" and "holds 127 rows" in g.detail


def test_gu1_the_options_digest_must_be_the_digest_of_the_options(tmp_path):
    crate = twin(tmp_path)
    forge(crate).edit_manifest(KINGSTON, lambda m: m.update(options_sha256="7" * 64))
    g = guard(crate)
    assert g.guard == "GU1" and "options_sha256" in g.detail


def test_gu9_a_snapshot_whose_content_is_stamped_other_than_its_name_says_is_refused(tmp_path, qpu_read):
    crate = read_copy(tmp_path, qpu_read)
    f = forge(crate)
    snap = next((crate / "unit" / "read" / "ibm-refetch" / "ibm_kingston").glob("properties-*.json"))
    rel = snap.relative_to(crate).as_posix()
    new = rel.rsplit("/", 1)[0] + "/properties-20200101T000000Z.json"
    f.write(new, f.read(rel))
    f.remove(rel)
    reseal_read_manifest(f, "ibm-refetch")
    g = guard(crate)
    assert g.guard == "GU9" and "not as its name says" in g.detail


def test_gu5_a_raw_result_that_is_no_ibm_result_is_refused(tmp_path):
    crate = twin(tmp_path)
    forge(crate).write(RUN.format(KINGSTON, "film-1-raw.json"), b'{"not": "a result"}')
    g = guard(crate)
    assert g.guard == "GU5"


def test_g6_a_metrics_created_time_that_is_not_the_lines_is_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    rel = RUN.format(KINGSTON, "film-1-metrics.json")
    m = f.json(rel)
    m["job"]["created"] = m["metrics"]["timestamps"]["created"] = "2026-11-01T09:00:00.000000Z"
    f.put(rel, m)
    assert letter(crate) == "G6"


def test_g6_a_metrics_wrapper_of_another_job_is_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    rel = RUN.format(KINGSTON, "film-1-metrics.json")
    m = f.json(rel)
    m["job_id"] = "dryrun-" + "0" * 16
    f.put(rel, m)
    assert letter(crate) == "G6"


def test_g6_an_execution_span_outside_running_and_finished_is_refused_with_p1s_letter(tmp_path):
    crate = twin(tmp_path, kind="qpu")
    f = forge(crate)
    rel = RUN.format("ibm_kingston", "film-1-metrics.json")
    m = f.json(rel)
    m["metrics"]["timestamps"]["finished"] = m["metrics"]["timestamps"]["running"]
    f.put(rel, m)
    assert letter(crate) == "G6"


# -- GU6, GU7, GU8, GU9 ---------------------------------------------------------------------------------------------------
def test_gu6_a_device_with_results_and_no_control_job_with_one_is_refused(tmp_path):
    with pytest.raises(p1_guards.GuardError) as caught:           # the builder regenerates the metadata, and the guard refuses
        P.build_unit(tmp_path, skip=frozenset({(FEZ, "control-1"), (FEZ, "control-2"), (FEZ, "control-3")}))
    assert caught.value.guard == "GU6" and "bit order" in caught.value.detail


def test_gu6_the_known_answer_of_a_device_is_its_first_control_job_that_has_a_result(tmp_path):
    crate = P.build_unit(tmp_path, skip=frozenset({(FEZ, "control-1")}))
    checker.load()
    md = checker.check(crate)
    second = forge(crate).json(RUN.format(FEZ, "control-2-line.json"))["job_id"]
    decodes = [e for e in md["@graph"] if "qro:Decode" in canonical.types(e) and e["name"].endswith("on " + FEZ)]
    assert len(decodes) == 5 and {d["qro:knownAnswer"]["@id"] for d in decodes} == {f"#pub-{second}-0"}
    assert U.read(crate).status().missing == ((FEZ, "control-1", "missing"),)


def test_gu7_a_job_with_a_raw_result_and_a_status_file_is_refused(tmp_path):
    crate = twin(tmp_path)
    forge(crate).put(RUN.format(KINGSTON, "film-1-status.json"), {"state": {"status": "Cancelled"}})
    assert letter(crate) == "GU7"


def test_gu7_a_job_with_a_status_file_and_a_record_is_refused(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    f.remove(RUN.format(KINGSTON, "film-1-raw.json"))
    f.put(RUN.format(KINGSTON, "film-1-status.json"), {"state": {"status": "Cancelled"}})
    g = guard(crate)
    assert g.guard == "GU7" and "no records" in g.detail


def status_job(crate, keep_metrics=False, verdict=False, keep_records=False):
    """film-1 on kingston as a job that did not complete: its raw result and its records removed, a status file put, and
    (as asked) its metrics kept or a verdict file added."""
    f = forge(crate)
    metrics = f.read(RUN.format(KINGSTON, "film-1-metrics.json"))
    f.remove(RUN.format(KINGSTON, "film-1-raw.json"))
    for rel in f.run_files(KINGSTON, "film-1"):
        if ("-pub" in rel and not keep_records) or rel.endswith("-metrics.json"):
            f.remove(rel)
    f.put(RUN.format(KINGSTON, "film-1-status.json"), {"state": {"status": "Cancelled"}})
    if keep_metrics:
        f.write(RUN.format(KINGSTON, "film-1-metrics.json"), metrics)
    if verdict:
        f.put(RUN.format(KINGSTON, "film-1-verdict.json"), {"verdict": "held"})
    return f


def test_gu7_a_status_job_with_nothing_else_is_not_refused_by_gu7(tmp_path):
    """The control of the two tests below: the same job without metrics or verdict passes GU7 (it may be refused later)."""
    crate = twin(tmp_path)
    status_job(crate)
    assert letter(crate) != "GU7"


def test_gu7_a_status_job_with_metrics_is_refused(tmp_path):
    """The first verifier, round 1: the check weakened to 'no records' left this uncaught."""
    crate = twin(tmp_path)
    status_job(crate, keep_metrics=True)
    g = guard(crate)
    assert g.guard == "GU7" and "no records, metrics or verdict" in g.detail


def test_gu7_a_status_job_with_records_alone_is_refused(tmp_path):
    """Records without metrics or a verdict: the check weakened to 'no metrics or verdict' left this uncaught."""
    crate = twin(tmp_path)
    status_job(crate, keep_records=True)
    g = guard(crate)
    assert g.guard == "GU7" and "no records, metrics or verdict" in g.detail


def test_gu7_a_status_job_with_a_verdict_is_refused(tmp_path):
    crate = twin(tmp_path)
    status_job(crate, verdict=True)
    g = guard(crate)
    assert g.guard == "GU7" and "no records, metrics or verdict" in g.detail


def test_gu1_a_float_cap_is_refused_though_it_equals_the_recipes(tmp_path):
    """60.0 == 60 in Python; the drive's cap check refuses it (S4), so the generator does too."""
    crate = twin(tmp_path)
    forge(crate).edit_manifest(FEZ, lambda m: m["jobs"][1].update(max_execution_time=float(m["jobs"][1]["max_execution_time"])))
    g = guard(crate)
    assert g.guard == "GU1" and "whole number" in g.detail


def test_gu7_a_job_with_neither_a_raw_result_nor_a_status_file_is_refused(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    f.remove(RUN.format(KINGSTON, "film-1-raw.json"))
    for rel in f.run_files(KINGSTON, "film-1"):
        if "-pub" in rel or rel.endswith("-metrics.json"):
            f.remove(rel)
    assert letter(crate) == "GU7"


def test_gu7_a_job_with_a_raw_result_and_no_metrics_is_refused(tmp_path):
    crate = twin(tmp_path)
    forge(crate).remove(RUN.format(KINGSTON, "film-1-metrics.json"))
    assert letter(crate) == "GU7"


def test_gu7_a_job_without_its_line_or_marker_is_refused(tmp_path):
    crate = twin(tmp_path)
    forge(crate).remove(RUN.format(KINGSTON, "film-1-submitting.json"))
    assert letter(crate) == "GU7"


def test_gu8_a_simulator_units_metrics_must_be_marked_dry_run(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    rel = RUN.format(KINGSTON, "film-1-metrics.json")
    m = f.json(rel)
    del m["dry_run"]
    f.put(rel, m)
    g = guard(crate)
    assert g.guard == "GU8" and "dry_run" in g.detail


def test_gu8_a_qpu_units_metrics_must_not_be_marked_dry_run(tmp_path):
    crate = twin(tmp_path, kind="qpu")
    f = forge(crate)
    rel = RUN.format("ibm_kingston", "film-1-metrics.json")
    m = f.json(rel)
    m["dry_run"] = True
    f.put(rel, m)
    assert letter(crate) == "GU8"


def test_gu9_a_read_in_a_simulator_unit_is_refused(tmp_path):
    crate = twin(tmp_path)
    f = forge(crate)
    f.path("unit/read/ibm-refetch").mkdir(parents=True)
    f.put("unit/read/ibm-refetch/MANIFEST.json", {"files": [], "format": "qro-crate/ibm-refetch-manifest/v0"})
    g = guard(crate)
    assert g.guard == "GU9" and "simulator" in g.detail


@pytest.fixture(scope="module")
def qpu_read(tmp_path_factory):
    return P.build_unit(tmp_path_factory.mktemp("qpu-read"), kind="qpu", read=True, skip=QPU_FILMS)


def read_copy(tmp_path, qpu_read):
    import shutil
    out = tmp_path / "crate"
    shutil.copytree(qpu_read, out)
    return out


def a_job_id(f, device="ibm_kingston"):
    return f.json(RUN.format(device, "control-1-line.json"))["job_id"]


def test_gu9_one_job_missing_its_read_records_is_refused(tmp_path, qpu_read):
    crate = read_copy(tmp_path, qpu_read)
    f = forge(crate)
    jid = a_job_id(f)
    f.remove(f"unit/read/ibm-refetch/ibm_kingston/{jid}.json")
    g = guard(crate)
    assert g.guard in ("GU9", "G9") and ("job records" in g.detail or "MANIFEST" in g.detail)


def test_g7_a_read_flag_that_does_not_hold_is_refused_with_p1s_letter(tmp_path, qpu_read):
    crate = read_copy(tmp_path, qpu_read)
    f = forge(crate)
    jid = a_job_id(f)
    rel = f"unit/read/ibm-refetch/ibm_kingston/{jid}.json"
    doc = f.json(rel)
    doc["holds"]["commitments_equal"] = False
    f.put(rel, doc)
    reseal_read_manifest(f, "ibm-refetch")
    assert letter(crate) == "G7"


@pytest.mark.parametrize("edit, why", [
    (lambda d: d["calibration"].update(first_shot="2026-11-01T09:00:00.000000Z"), "first shot"),
    (lambda d: d["calibration"].update(running="2026-11-01T09:00:00.000000Z"), "running time"),
    (lambda d: d["holds"]["pubs"][0].update(gate_list_equal=False), "gate-list flags"),
    (lambda d: d["holds"]["pubs"][0].update(commitment_in_line="6" * 64), "commitments"),
    (lambda d: d["holds"].update(pubs_in_ibm_copy=d["holds"]["pubs_in_ibm_copy"] + 1), "same PUBs"),
    (lambda d: d.update(device="ibm_fez"), "another job or device")],
    ids=["first shot", "running", "gate lists", "a commitment", "PUB counts", "another device"])
def test_g7_each_condition_of_a_read_job_record_is_held_with_p1s_letter(tmp_path, qpu_read, edit, why):
    crate = read_copy(tmp_path, qpu_read)
    f = forge(crate)
    jid = a_job_id(f)
    rel = f"unit/read/ibm-refetch/ibm_kingston/{jid}.json"
    doc = f.json(rel)
    edit(doc)
    f.put(rel, doc)
    reseal_read_manifest(f, "ibm-refetch")
    g = guard(crate)
    assert g.guard == "G7" and why in g.detail, (g.guard, g.detail)


def test_gu6_a_control_jobs_pubs_must_be_named_in_order_defence_in_depth(tmp_path):
    """GU1 holds the manifest's job table first, so no file reaches GU6's check; it is called with a bundle whose names alone
    differ (the commitments are the manifest's, so P1's G2 passes)."""
    import dataclasses
    crate = G.Crate(twin(tmp_path))
    by = G._by_kind(crate, G.p2_module() is not None)
    unit = G._unit_file(crate, by)
    bundles = G._manifests(crate, by, unit)
    b = bundles[KINGSTON]
    jobs = list(b.manifest.jobs)
    name, circuits = jobs[0]
    jobs[0] = (name, (circuits[0], dataclasses.replace(circuits[1], name="known-answer")))
    bundles[KINGSTON] = dataclasses.replace(b, manifest=dataclasses.replace(b.manifest, jobs=tuple(jobs)))
    with pytest.raises(p1_guards.GuardError) as caught:
        G._jobs(crate, by, bundles, unit)
    assert caught.value.guard == "GU6" and "known-complement" in caught.value.detail


def test_gu6_the_known_answer_must_be_a_control_jobs_pub_0_of_role_known_answer_defence_in_depth():
    from types import SimpleNamespace as S
    job = S(device=KINGSTON, done=True, kind="control", pass_=1, id="x", files={"line": "a-line.json"},
            records={0: ("a-path", S(role="law"), S(name="law"))})
    with pytest.raises(p1_guards.GuardError) as caught:
        G._known_answers([job], {"devices": [KINGSTON]})
    assert caught.value.guard == "GU6" and "not the known answer" in caught.value.detail


def test_g7_a_read_record_of_another_role_than_the_jobs_is_refused_with_p1s_letter(tmp_path, qpu_read):
    crate = read_copy(tmp_path, qpu_read)
    f = forge(crate)
    jid = a_job_id(f)
    rel = f"unit/read/ibm-refetch/ibm_kingston/{jid}.json"
    doc = f.json(rel)
    assert doc["role"] == "known-answer"
    doc["role"] = "law"
    f.put(rel, doc)
    reseal_read_manifest(f, "ibm-refetch")
    assert letter(crate) == "G7"


def test_gu9_a_read_record_of_a_job_whose_pubs_carry_more_than_one_role_is_refused_not_held_yet(tmp_path):
    """A film job (law and coherence) cannot be held by P1's G7, which holds one role; handing it some of the job's PUBs would
    pass the rest unchecked. So the record is refused, GU9, until P5.2 and P1 settle how it is held (docs/P5.md)."""
    with pytest.raises(p1_guards.GuardError) as caught:
        P.build_unit(tmp_path, kind="qpu", read=True)
    assert caught.value.guard == "GU9" and "more than one role is not held yet" in caught.value.detail


def test_g8_a_result_record_whose_digest_is_not_the_raw_results_is_refused_with_p1s_letter(tmp_path, qpu_read):
    crate = read_copy(tmp_path, qpu_read)
    f = forge(crate)
    jid = a_job_id(f)
    rel = f"unit/read/ibm-results-refetch/ibm_kingston/{jid}.json"
    doc = f.json(rel)
    doc["committed"]["sha256"] = "4" * 64
    f.put(rel, doc)
    reseal_read_manifest(f, "ibm-results-refetch")
    assert letter(crate) == "G8"


def test_g8_a_result_record_that_names_another_file_is_refused_with_p1s_letter(tmp_path, qpu_read):
    crate = read_copy(tmp_path, qpu_read)
    f = forge(crate)
    jid = a_job_id(f)
    rel = f"unit/read/ibm-results-refetch/ibm_kingston/{jid}.json"
    doc = f.json(rel)
    doc["committed"]["path"] = "/".join(("docs", "records", doc["committed"]["path"]))   # Quantum-Film's tree, not the crate's
    f.put(rel, doc)
    reseal_read_manifest(f, "ibm-results-refetch")
    assert letter(crate) == "G8"


def test_g9_a_manifest_that_lists_a_file_as_other_than_it_is_is_refused_with_p1s_letter(tmp_path, qpu_read):
    crate = read_copy(tmp_path, qpu_read)
    f = forge(crate)
    rel = "unit/read/ibm-refetch/MANIFEST.json"
    doc = f.json(rel)
    doc["files"][0]["sha256"] = "5" * 64
    f.put(rel, doc)
    assert letter(crate) == "G9"


def test_g9_a_read_directory_with_no_manifest_is_refused_with_p1s_letter(tmp_path, qpu_read):
    crate = read_copy(tmp_path, qpu_read)
    forge(crate).remove("unit/read/ibm-results-refetch/MANIFEST.json")
    assert letter(crate) == "G9"


def test_gu9_a_snapshot_that_is_not_the_devices_is_refused(tmp_path, qpu_read):
    crate = read_copy(tmp_path, qpu_read)
    f = forge(crate)
    snap = next(p for p in (crate / "unit" / "read" / "ibm-refetch" / "ibm_kingston").glob("properties-*.json"))
    rel = snap.relative_to(crate).as_posix()
    doc = json.loads(f.read(rel))
    doc["backend_name"] = "ibm_fez"
    data = json.dumps(doc, indent=1, sort_keys=True).encode("utf-8") + b"\n"
    f.write(rel, data)
    reseal_read_manifest(f, "ibm-refetch")
    assert letter(crate) == "GU9"


def reseal_read_manifest(f, tag):
    """The read's MANIFEST listing every file of its directory as it now hashes, so that G9 does not decide first."""
    rel = f"unit/read/{tag}/MANIFEST.json"
    base = f.path(f"unit/read/{tag}")
    files = []
    for p in sorted(base.rglob("*.json")):
        if p.name != "MANIFEST.json":
            data = p.read_bytes()
            files.append({"bytes": len(data), "path": p.relative_to(base).as_posix(), "sha256": P.sha(data)})
    doc = f.json(rel)
    doc["files"] = files
    f.put(rel, doc)


# -- the one switch -------------------------------------------------------------------------------------------------------
def test_one_monkeypatch_of_p1_guards_hold_switches_every_guard_off(tmp_path, monkeypatch):
    """The sentinel (P1.3's ruling): every raise of P5's guards and of the P1 guards it calls goes through
    p1_guards.hold, looked up when called, so the same faults that raise with it on do not raise a GuardError with it off."""
    def bytes_changed(f):
        f.write(f"unit/{KINGSTON}/bundle/law.gates.json", f.read(f"unit/{KINGSTON}/bundle/law.gates.json")[:-2] + b" \n")

    def counts_changed(f):
        f.edit_record(KINGSTON, "film-1", 0, lambda r: r["counts"][0].__setitem__(1, r["counts"][0][1] + 1))
    faults = []
    for n, change in enumerate([
            bytes_changed,                                                              # GU1
            lambda f: f.put("unit/UNIT.json", dict(f.json("unit/UNIT.json"), recipe_sha256="1" * 64)),   # GU2
            counts_changed,                                                             # G5
            lambda f: f.put(RUN.format(KINGSTON, "film-1-status.json"), {"state": 1})]):    # GU7
        (tmp_path / str(n)).mkdir()
        crate = twin(tmp_path / str(n))
        change(forge(crate))
        faults.append(crate)
    assert [guard(c).guard for c in faults] == ["GU1", "GU2", "G5", "GU7"]
    monkeypatch.setattr(p1_guards, "hold", lambda ok, guard, where, detail: None)
    for crate in faults:
        assert G.unit(crate)["@graph"], crate                # accepted: no guard is left to refuse the planted fault


def test_the_seam_with_p2_refuses_a_module_that_is_present_without_its_functions(tmp_path, monkeypatch):
    import sys
    import types
    fake = types.ModuleType("qro.p2_measures")
    monkeypatch.setitem(sys.modules, "qro.p2_measures", fake)
    with pytest.raises(p1_guards.GuardError) as caught:
        G.p2_module()
    assert caught.value.guard == "seam"
