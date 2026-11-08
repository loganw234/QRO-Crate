"""P1's real IBM crate (P1's design, items 1 and 11), built from moth-quantum's records and the repository's read of
2026-10-14, outside the tree, by `python -m qro.p1_adapter` as a process, and checked by `python -m qro check` as one. The
measurements of the design's item 11 that P1.1 held only as literals hold here on the real bytes: 68 commitments held to
IBM's echo, 12 values-digests in six classes, the link rule's 57 / 8 / 1, 31 of 31 known answers, and the decoded counts
of Quantum-Film's records. Then the steps swept over every entity of the crate."""
import collections
import json
import re
from pathlib import Path

import pytest

import p1crates_support as S
from qro import canonical, p1_decode, p1_forms, p1_records as rec, p1_steps


@pytest.fixture(scope="module")
def crate():
    return S.built("ibm")[0]


@pytest.fixture(scope="module")
def md():
    return S.metadata("ibm")


def graph(md):
    return {e["@id"]: e for e in md["@graph"]}


def test_the_ibm_crate_is_built_outside_the_tree_and_the_command_line_accepts_it(crate):
    path, identity, line = S.built("ibm")
    assert re.fullmatch(r"BUILT ibm: 1074 files, [0-9]+ bytes, identity [0-9a-f]{64}", line), line
    assert S.ROOT not in path.parents and S.MOTH not in path.parents
    assert S.checked("ibm") == (0, f"ACCEPTED {identity}", "")


def test_the_crate_holds_the_files_and_entities_the_design_counts(crate, md):
    files = [p for p in crate.rglob("*") if p.is_file() and p.name != canonical.DESCRIPTOR]
    assert len(files) == 1073 and sum(p.stat().st_size for p in files) == 52_585_174       # the records, and P2's question/law.json
    kinds = {}
    for e in md["@graph"]:
        kinds[tuple(S.types_of(e))] = kinds.get(tuple(S.types_of(e)), 0) + 1
    # P1's entities, and P2's: the question/law.json File and its Dataset, the Measuring, the 20 Contrasts, the 161 Measurements
    # and one Hold for each of the 31 Compiles (the mentions: P1's 161 actions, the Measuring and the 31 Holds)
    assert kinds == {("File",): 996, ("Dataset",): 69, ("IndividualProduct",): 3, ("SoftwareApplication",): 3,
                     ("qro:Pub",): 68, ("CreateAction", "qro:Compile"): 31, ("CreateAction", "qro:Decode"): 65,
                     ("CreateAction", "qro:Job"): 65, ("CreativeWork", "Profile"): 2, ("CreativeWork", "qro:Question"): 1,
                     ("File", "qro:RawResult"): 65, ("File", "qro:Snapshot"): 12, ("CreativeWork",): 2,
                     ("CreateAction", "qro:Hold"): 31, ("CreateAction", "qro:Measuring"): 1, ("qro:Contrast",): 20,
                     ("qro:Measurement",): 161}
    assert len(md["@graph"]) == 1595 and len(md["@graph"][1]["mentions"]) == 193


def test_the_longest_in_crate_paths_are_77_characters_in_ten_files_and_76_in_eight(md):
    """Limit 14 and the paths section of docs/P1.md: the figure a Windows host's 260 is budgeted on."""
    files = sorted(e["@id"] for e in S.of_type(md, "File"))
    def sheets(device, n):
        return [f"2026-10-05/ibm/{device}/sheet-{k:02d}/run/known-answer-pub0-known-answer.json" for k in range(1, n + 1)]
    assert max(len(f) for f in files) == 77
    assert [f for f in files if len(f) == 77] == sheets("ibm_marrakesh", 10)
    assert [f for f in files if len(f) == 76] == sheets("ibm_kingston", 8)


def test_the_qpy_files_are_23_digests_in_2_to_11_copies_the_17_a_commitment_names_in_3_to_11_and_each_logical_circuit_in_31(crate, md):
    """Limit 15's figures, over every QPY digest of the crate and not only the ones a commitment names."""
    qpy = collections.defaultdict(list)
    logical = collections.Counter()
    for e in S.of_type(md, "File"):
        if e["@id"].endswith(".qpy"):
            qpy[e["sha256"]].append(e["@id"])
        elif e["@id"].endswith(".qasm") and "/bundle/" in e["@id"]:
            logical[e["sha256"]] += 1
    copies = sorted(len(v) for v in qpy.values())
    assert (sum(copies), len(qpy), copies[0], copies[-1]) == (124, 23, 2, 11)
    named = {json.loads(S.read(crate, p["qro:record"]["@id"]))["source"]["isa_sha256"] for p in S.of_type(md, "qro:Pub")}
    assert len(named) == 17 and named <= set(qpy)
    held = sorted(len(qpy[d]) for d in named)
    assert (held[0], held[-1]) == (3, 11)
    assert sorted(len(v) for d, v in qpy.items() if d not in named) == [2, 3, 3, 4, 5, 6]
    assert sorted(logical.values()) == [31, 31, 31, 31]


def test_68_of_68_commitments_are_the_ones_ibm_echoed_inside_its_raw_results_and_the_job_lines_hold(crate, md):
    ids, seen = graph(md), 0
    for job in S.of_type(md, "qro:Job"):
        raw = next(r["@id"] for r in job["result"] if ids[r["@id"]].get("qro:rawForm"))
        parsed = p1_forms.parse_ibm_result(S.read(crate, raw))
        line = rec.line(S.read(crate, job["qro:line"]["@id"]), "line")
        pubs = sorted(job["object"], key=lambda r: r["@id"])
        assert len(pubs) == len(parsed.pubs) == len(line.commitments)
        for k, pub in enumerate(pubs):
            assert ids[pub["@id"]]["qro:commitment"] == parsed.pubs[k].echo == line.commitments[k]
            seen += 1
    assert seen == 68


def stamp_of(path):
    return re.search(r"properties-([0-9]{8}T[0-9]{6})Z", path).group(1)


def test_the_12_snapshots_fall_in_the_6_classes_of_the_study(md):
    """Study section 4.5: kingston's morning snapshot equals its freeze and its two later ones differ; marrakesh's two later
    ones differ from the freeze and equal each other; fez's four are equal. Six values, from twelve files."""
    classes = {}
    for e in S.of_type(md, "qro:Snapshot"):
        device = e["@id"].split("/")[2]
        classes.setdefault((device, e["qro:valuesDigest"]), set()).add(stamp_of(e["@id"]))
    got = sorted((d, tuple(sorted(s))) for (d, _), s in classes.items())
    assert len(classes) == 6
    assert got == [
        ("ibm_fez", ("20261005T081622", "20261005T083844", "20261005T100831", "20261005T114447")),
        ("ibm_kingston", ("20261005T065743", "20261005T090246")),
        ("ibm_kingston", ("20261005T112827",)),
        ("ibm_kingston", ("20261005T122118",)),
        ("ibm_marrakesh", ("20261005T073549", "20261005T083246")),
        ("ibm_marrakesh", ("20261005T095118", "20261005T112128")),
    ]


def test_the_link_rule_gives_57_history_at_first_shot_8_in_gap_and_1_job_whose_running_time_snapshot_differs(md):
    ids = graph(md)
    jobs = S.of_type(md, "qro:Job")
    words = [j["qro:calibrationLink"] for j in jobs]
    assert (words.count("history-at-first-shot"), words.count("history-in-gap"), len(jobs)) == (57, 8, 65)
    differ = 0
    for j in jobs:
        older = min((r["@id"] for r in j["qro:calibration"]), key=lambda i: ids[i]["qro:stamp"])
        differ += older != j["qro:historyAtRunning"]["@id"]
    assert differ == 1
    gap_jobs = [j for j in jobs if j["qro:calibrationLink"] == "history-in-gap"]
    assert {ids[j["qro:device"]["@id"]]["name"] for j in gap_jobs} == {"ibm_kingston"}
    assert {ids[r["@id"]]["qro:stamp"] for j in gap_jobs for r in j["qro:calibration"]} == {
        "2026-10-05T11:28:27Z", "2026-10-05T12:21:18Z"}


def test_every_known_answer_holds_most_significant_first_and_none_holds_the_mirror_way(crate, md):
    ids, held = graph(md), {"msb-first": 0, "lsb-first": 0}
    known = [p for p in S.of_type(md, "qro:Pub") if p.get("qro:role") == "known-answer"]
    for pub in known:
        record = json.loads(S.read(crate, pub["qro:record"]["@id"]))
        circuit = next(f for f in S.of_type(md, "File") if f["sha256"] == record["source"]["circuit_sha256"])
        expected = p1_decode.expected_set(S.read(crate, circuit["@id"]))
        job = next(j for j in S.of_type(md, "qro:Job") if {"@id": pub["@id"]} in j["object"])
        raw = next(r["@id"] for r in job["result"] if ids[r["@id"]].get("qro:rawForm"))
        result = p1_forms.parse_ibm_result(S.read(crate, raw))
        for order in held:
            counts = p1_decode.ibm_counts(result.pubs[0], order)
            held[order] += p1_decode.known_answer_verdict(counts, expected).holds
    assert (len(known), held) == (31, {"msb-first": 31, "lsb-first": 0})


def test_every_pubs_decoded_counts_are_quantum_films_record_and_the_shots_total_818176(crate, md):
    total = 0
    pubs = S.of_type(md, "qro:Pub")
    for pub in pubs:
        counts = p1_decode.pub_counts(crate, md, pub["@id"])
        record = rec.device_run(S.read(crate, pub["qro:record"]["@id"]), "record")
        assert counts == record.counts, pub["@id"]
        total += sum(counts.values())
    assert (len(pubs), total) == (68, 818_176)


def test_every_jobs_times_are_its_raw_results_span_inside_what_ibm_reported_and_every_raw_result_is_counted(crate, md):
    inside, shots = 0, 0
    for job in S.of_type(md, "qro:Job"):
        line = rec.line(S.read(crate, job["qro:line"]["@id"]), "line")
        metrics = rec.metrics(S.read(crate, job["qro:line"]["@id"].replace("-line.json", "-metrics.json")), "metrics")
        start, end = (p1_forms.parse_time(job[k], "Z") for k in ("startTime", "endTime"))
        inside += metrics.running <= start <= end <= metrics.finished
        assert metrics.job_id == line.job_id == job["qro:jobId"]
    for raw in S.of_type(md, "qro:RawResult"):
        shots += raw["qro:shots"]
    assert (inside, shots) == (65, 31 * 1024 + 31 * 24576 + 3 * 4096)


def test_the_ibm_crate_carries_the_licences_the_design_gave_each_class_of_file(md):
    ids = graph(md)
    expect = {"-raw.json": "#licence-ibm-data", "-metrics.json": "#licence-ibm-data", "-line.json": "LICENSE-quantum-film",
              "manifest.json": "LICENSE-quantum-film", ".qpy": "LICENSE-quantum-film", "prediction-backend.json":
              "LICENSE-quantum-film"}
    seen = set()
    for i, e in ids.items():
        for suffix, lic in expect.items():
            if i.endswith(suffix):
                assert e["license"] == {"@id": lic}, i
                seen.add(suffix)
    assert seen == set(expect)
    for e in S.of_type(md, "qro:Snapshot"):
        assert e["license"] == {"@id": "#licence-ibm-data"}
    read_job = [e for i, e in ids.items() if re.fullmatch(r"2026-10-14/ibm-refetch/ibm_[a-z]+/[a-z0-9]+\.json", i)]
    assert len(read_job) == 65 and all(e["license"] == {"@id": "#licence-ibm-data"} for e in read_job)
    assert ids["./"]["license"] == {"@id": "https://creativecommons.org/licenses/by/4.0/"}
    assert "license" not in ids["LICENSE-quantum-film"]


# -- every entity the steps check ----------------------------------------------------------------------------------------------------------
def test_each_step_visits_every_entity_of_the_type_it_checks_in_the_real_crate(crate, md, monkeypatch):
    seen = S.visited(monkeypatch, ["_pub4", "_decode5", "_snapshot8", "_job8"])
    for step in (p1_steps.step4, p1_steps.step5, p1_steps.step8):
        step(Path(crate), md)
    for name, t, n in (("_pub4", "qro:Pub", 68), ("_decode5", "qro:Decode", 65), ("_snapshot8", "qro:Snapshot", 12),
                       ("_job8", "qro:Job", 65)):
        assert sorted(seen[name]) == [e["@id"] for e in S.of_type(md, t)] and len(seen[name]) == n, name


@pytest.fixture
def memo(monkeypatch):
    S.memo_parses(monkeypatch)


def test_every_pub_is_accepted_and_refused_at_itself_once_its_commitment_is_false(crate, md, memo):
    assert S.sweep_pubs(Path(crate), md) == 68


def test_every_decode_is_accepted_and_refused_at_itself_once_its_order_or_its_known_answer_is_false(crate, md, memo):
    assert S.sweep_decodes(Path(crate), md) == 65


def test_every_snapshot_and_job_is_accepted_and_refused_at_itself_once_a_claim_is_false(crate, md, memo):
    assert S.sweep_snapshots_and_jobs(Path(crate), md) == (12, 65)
