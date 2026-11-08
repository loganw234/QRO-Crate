"""P1.2's IBM generator (qro/p1_generate.py `ibm`), on the twin: what it writes, that it copies no CHECKED value (T1 to
T3 of P1's design, item 6), and its guards, each tripped by one planted fault and by no other first (G1 to G10 and G12;
G11, Atlas's, is test_p1_atlas_generate.py; the seam with P2 is test_p1_seam.py).

The twin is a slice of Quantum-Film's real IBM records, and the faults are planted in copies of it with the forger's
hand (controls/plants_p1.py), which rewrites a record in Quantum-Film's own style and recomputes every digest the
other records hold over it. So a fault trips the guard it is meant for and not an earlier one."""
import dataclasses
import hashlib
import shutil
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

import p1_builder
from controls import plants_p1 as plants
from p1_support import (BUNDLE, Sandbox, IBM_DIR, MANIFEST, MORNING_COH, MORNING_KA, SHEET1_BUNDLE, SHEET1_KA, SHEET2_KA,
                        entity_bytes, forge, generated, graph, guard, memo_parses, of_type, pin_p2, recommit)
from qro import canonical, fixture, p1_decode, p1_forms, p1_generate as G, p1_records as rec
from qro import reader

RUN = f"{IBM_DIR}/run"
KA_LINE, KA_RAW, KA_REC = f"{MORNING_KA}-line.json", f"{MORNING_KA}-raw.json", f"{MORNING_KA}-pub0-known-answer.json"
KA_METRICS, KA_MARKER = f"{MORNING_KA}-metrics.json", f"{MORNING_KA}-submitting.json"
COH_LINE, COH_RAW = f"{MORNING_COH}-line.json", f"{MORNING_COH}-raw.json"
COH_REC0 = f"{MORNING_COH}-pub0-coherence-xx.json"
S1_LINE, S2_LINE = f"{SHEET1_KA}-line.json", f"{SHEET2_KA}-line.json"
SNAP_0902, SNAP_1128, SNAP_1221 = plants.SNAP_0902, plants.SNAP_1128, plants.SNAP_1221
SOURCE = "2026-09-25/p3/circuit-ed767c01bd4b851d.qasm"
GOLDEN = {SNAP_0902: "e96fd7d158270ae82c62aa22d2fc1020269ca266591f191eafb808cc5c5fc395",
          SNAP_1128: "3b601e0caa583185871c2965c6a31fb8747b3d19154c26a31b92d7a78f23fc51",
          SNAP_1221: "bfe4f0e88e22e327ed2ea76bfcb76866042c490242052b48b724033ac9ad6413"}


@pytest.fixture(scope="module")
def working(tmp_path_factory):
    """The one hard-linked working copy of the twin the tests of this module share (a fresh copy costs the host's scan of 73
    new files), and the proof at the end that none was written through. The twin is P1's alone, built with P2's module absent,
    for tests that pin it absent for their generator (the lead's ruling, 2026-11-08: one tree each)."""
    box = Sandbox(tmp_path_factory.mktemp("sandbox"), alone=True)
    yield box
    box.verify_pristine()


@pytest.fixture
def quick(working, monkeypatch):
    """The working copy, as the twin is, with the seam pinned absent and the parses of identical bytes made once; restored
    after the test. A test that writes into it unlinks before it writes."""
    memo_parses(monkeypatch)
    pin_p2(monkeypatch, None)
    yield working.root
    working.restore()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def remove(crate, rel):
    Path(crate).joinpath(*rel.split("/")).unlink()


def job_of(md, line_rel):
    return next(e for e in of_type(md, "qro:Job") if e["qro:line"] == {"@id": line_rel})


def unlist(f, rel):
    """A file of the read taken out of its directory's MANIFEST, so that what the crate lacks it does not list either."""
    directory = rel.rsplit("/", 2)[0]
    name = rel[len(directory) + 1:]
    f.edit_json(f"{directory}/MANIFEST.json", lambda m: m.update(files=[e for e in m["files"] if e["path"] != name]))


def other_digit(text):
    """The text with its last character another one of the same kind: a digest or a time that is not the one it was."""
    return text[:-1] + ("0" if text[-1] != "0" else "1")


OTHER_JOB = "d" + "q" * 19             # the shape of an IBM job id that is nobody's


# -- what it writes ---------------------------------------------------------------------------------------------------------------
def test_the_twin_is_written_as_the_design_says(quick):
    md = generated(quick)
    kinds = {}
    for e in md["@graph"]:
        kinds[tuple(canonical.types(e))] = kinds.get(tuple(canonical.types(e)), 0) + 1
    assert kinds == {("File",): 65, ("Dataset",): 10, ("IndividualProduct",): 1, ("SoftwareApplication",): 3,
                     ("qro:Pub",): 5, ("CreateAction", "qro:Compile"): 3, ("CreateAction", "qro:Decode"): 4,
                     ("CreateAction", "qro:Job"): 4, ("CreativeWork", "Profile"): 2, ("CreativeWork", "qro:Question"): 1,
                     ("File", "qro:RawResult"): 4, ("File", "qro:Snapshot"): 3, ("CreativeWork",): 2}
    assert len(md["@graph"]) == 107
    ids = graph(md)
    assert {"#device-ibm_kingston", "#program-sampler", "#transpiler-qiskit-2.5.2", "#rule-quantum_film.ibm.decode.v1",
            "#licence-ibm-data", "#question", "#files-ibm_kingston", "#provider-ibm-refetch",
            "#provider-ibm-results-refetch", "LICENSE-quantum-film", SOURCE} <= set(ids)
    for label in ("morning", "sheet-01", "sheet-02"):
        assert {f"#bundle-ibm_kingston-{label}", f"#compile-ibm_kingston-{label}"} <= set(ids)
    assert {f"#runs-ibm_kingston-{label}" for label in ("morning", "sheet-01", "sheet-02")} <= set(ids)


def media_type(rel):
    """What a file of the twin is, by its name, written here and not read from the generator's table."""
    for suffix, media in ((".json", "application/json"), (".qpy", "application/octet-stream"), (".md", "text/markdown")):
        if rel.endswith(suffix):
            return media
    return "text/plain"             # the QASM circuits and the LICENSE


def test_every_file_of_the_crate_is_one_file_entity_that_holds_its_digest_and_size(quick):
    md = generated(quick)
    ids = graph(md)
    on_disk = sorted(p.relative_to(quick).as_posix() for p in quick.rglob("*") if p.is_file())
    assert on_disk.pop(on_disk.index(canonical.DESCRIPTOR)) == canonical.DESCRIPTOR
    files = sorted(e["@id"] for e in md["@graph"] if "File" in canonical.types(e))
    assert files == on_disk and len(files) == 72
    for rel in files:
        data = quick.joinpath(*rel.split("/")).read_bytes()
        assert (ids[rel]["sha256"], ids[rel]["contentSize"]) == (sha(data), str(len(data))), rel
        assert ids[rel]["encodingFormat"] == media_type(rel), rel
    assert ids[KA_RAW]["qro:shots"] == 1024 and ids[COH_RAW]["qro:shots"] == 4096
    assert ids[KA_RAW]["qro:rawForm"] == "ibm-sampler-result/v1"


def test_each_class_of_file_carries_the_licence_the_design_gave_it(quick):
    """Quantum-Film's own files the MIT notice; IBM's result text, its metrics, its snapshots and the read's job records
    `#licence-ibm-data`; the read's other files Logan's, under the root's CC BY 4.0. The LICENSE carries none."""
    ids = graph(generated(quick))
    mit, ibm, by = {"@id": "LICENSE-quantum-film"}, {"@id": "#licence-ibm-data"}, {"@id": "https://creativecommons.org/licenses/by/4.0/"}
    seen = {}
    for rel, e in ids.items():
        if "File" not in canonical.types(e) or rel == "LICENSE-quantum-film":
            continue
        if rel.endswith(("-raw.json", "-metrics.json")) or "qro:Snapshot" in canonical.types(e):
            want, kind = ibm, "ibm"
        elif rel.startswith("2026-10-14/ibm-refetch/") and not rel.endswith("MANIFEST.json"):
            want, kind = ibm, "ibm"
        elif rel.startswith("2026-10-14/"):
            want, kind = by, "logan"
        else:
            want, kind = mit, "quantum-film"
        assert e["license"] == want, rel
        seen[kind] = seen.get(kind, 0) + 1
    assert seen == {"ibm": 4 + 4 + 3 + 4, "logan": 4 + 2 + 1 + 2, "quantum-film": 56 - 8 - 1}
    assert "license" not in ids["LICENSE-quantum-film"] and ids["./"]["license"] == by
    assert ids["#licence-ibm-data"]["@type"] == "CreativeWork"


def test_the_datasets_and_the_roots_loose_files_hold_every_file_once_and_reach_all_of_them(quick):
    """No file is a part of two Datasets, none of none: the groupings partition the files."""
    md = generated(quick)
    ids = graph(md)
    held = {}
    for e in md["@graph"]:
        if "Dataset" in canonical.types(e):
            for part in e["hasPart"]:
                if "File" in canonical.types(ids[part["@id"]]):
                    held.setdefault(part["@id"], []).append(e["@id"])
    files = sorted(i for i, e in ids.items() if "File" in canonical.types(e))
    assert sorted(held) == files and all(len(v) == 1 for v in held.values())
    assert held[KA_LINE] == ["#runs-ibm_kingston-morning"] and held[MANIFEST] == ["#bundle-ibm_kingston-morning"]
    assert held[SNAP_0902] == ["#files-ibm_kingston"] and held[f"{BUNDLE}/law.qpy"] == ["#bundle-ibm_kingston-morning"]
    assert held["2026-10-14/ibm-refetch/MANIFEST.json"] == ["#provider-ibm-refetch"]
    assert held["2026-10-14/ibm-results-refetch/MANIFEST.json"] == ["#provider-ibm-results-refetch"]
    assert held[f"{IBM_DIR}/sheet-01/run/known-answer-raw.json"] == ["#runs-ibm_kingston-sheet-01"]


def test_each_pubs_commitment_is_the_one_ibm_echoed_inside_its_raw_result(quick):
    """The independent oracle: IBM's echo read from the raw bytes by P1.1's reader, against what the generator wrote."""
    md = generated(quick)
    seen = 0
    for job in of_type(md, "qro:Job"):
        raw = next(r["@id"] for r in job["result"] if r["@id"].endswith("-raw.json"))
        parsed = p1_forms.parse_ibm_result(quick.joinpath(*raw.split("/")).read_bytes())
        for k, pub in enumerate(sorted(job["object"], key=lambda r: r["@id"])):
            e = graph(md)[pub["@id"]]
            assert e["qro:commitment"] == parsed.pubs[k].echo, pub["@id"]
            seen += 1
        line = rec.line(quick.joinpath(*job["qro:line"]["@id"].split("/")).read_bytes(), "line")
        assert [graph(md)[p["@id"]]["qro:commitment"] for p in sorted(job["object"], key=lambda r: r["@id"])] \
            == list(line.commitments)
    assert seen == 5


def test_the_three_snapshots_hold_the_values_digests_p1_1_computed_independently(quick):
    md = generated(quick)
    for rel, want in GOLDEN.items():
        e = graph(md)[rel]
        assert e["qro:valuesDigest"] == want
        assert e["qro:device"] == {"@id": "#device-ibm_kingston"} and e["qro:clock"] == "provider"
    assert graph(md)[SNAP_0902]["qro:stamp"] == "2026-10-05T09:02:46Z"
    assert graph(md)[SNAP_1221]["qro:stamp"] == "2026-10-05T12:21:18Z"
    assert graph(md)[SNAP_1221]["qro:newestValue"] > "2026-10-05T12:22:00Z"


def test_the_four_jobs_are_linked_as_the_real_records_are(quick):
    """The morning jobs under 09:02:46; sheet-01 under 11:28:27, where 12:21:18 was stamped and still being measured
    (no gap); sheet-02 in the gap, 12:21:18 having been stamped and measured before its first shot."""
    md = generated(quick)
    want = {KA_LINE: ("history-at-first-shot", [SNAP_0902]), COH_LINE: ("history-at-first-shot", [SNAP_0902]),
            S1_LINE: ("history-at-first-shot", [SNAP_1128]), S2_LINE: ("history-in-gap", [SNAP_1128, SNAP_1221])}
    for line, (word, snaps) in want.items():
        job = job_of(md, line)
        assert job["qro:calibrationLink"] == word
        assert sorted(r["@id"] for r in job["qro:calibration"]) == sorted(snaps)
        assert job["qro:clock"] == "provider" and job["qro:kitCommit"] == "unknown"
    assert job_of(md, KA_LINE)["qro:historyAtRunning"] == {"@id": SNAP_0902}


def test_a_jobs_times_are_its_raw_results_execution_span_in_the_profiles_spelling(quick):
    md = generated(quick)
    for job in of_type(md, "qro:Job"):
        raw = next(r["@id"] for r in job["result"] if r["@id"].endswith("-raw.json"))
        parsed = p1_forms.parse_ibm_result(quick.joinpath(*raw.split("/")).read_bytes())
        assert p1_forms.parse_time(job["startTime"], "Z") == parsed.first_shot
        assert p1_forms.parse_time(job["endTime"], "Z") == parsed.last_shot
        assert job["startTime"] < job["endTime"] and not job["startTime"].replace("Z", "").endswith("0")
    assert job_of(md, KA_LINE)["startTime"] == "2026-10-05T10:27:00.285375Z"
    assert job_of(md, KA_LINE)["endTime"] == "2026-10-05T10:27:01.376976Z"


def test_every_decode_names_its_bundles_one_known_answer_found_by_the_bundle_digest(quick):
    md = generated(quick)
    ka = {line: rec.line(quick.joinpath(*line.split("/")).read_bytes(), "line") for line in (KA_LINE, S1_LINE, S2_LINE)}
    pub = {line: f"#pub-{ka[line].job_id}-0" for line in ka}
    for jline, kline in ((KA_LINE, KA_LINE), (COH_LINE, KA_LINE), (S1_LINE, S1_LINE), (S2_LINE, S2_LINE)):
        job = job_of(md, jline)
        decode = graph(md)["#decode-" + job["qro:jobId"]]
        assert decode["qro:knownAnswer"] == {"@id": pub[kline]}, jline
        assert (decode["qro:decodeRule"], decode["qro:bitOrder"]) == ("quantum_film.ibm.decode/v1", "msb-first")
        assert decode["instrument"] == {"@id": "#rule-quantum_film.ibm.decode.v1"}
        assert decode["object"] == [next(r for r in job["result"] if r["@id"].endswith("-raw.json"))]


def test_the_root_lists_the_datasets_and_loose_files_and_mentions_every_action(quick):
    md = generated(quick)
    root = md["@graph"][1]
    assert root["@id"] == "./" and root["qro:generator"] == "qro-p1-ibm" and root["@type"] == "Dataset"
    parts = {r["@id"] for r in root["hasPart"]}
    datasets = {e["@id"] for e in of_type(md, "Dataset") if e["@id"] != "./"}
    assert datasets <= parts and len(datasets) == 9
    assert parts - datasets == {"LICENSE-quantum-film", SOURCE, "2026-10-14/README.md", "2026-10-14/ibm-refetch.log",
                                "2026-10-14/ibm-results-refetch.log"}
    actions = {e["@id"] for e in md["@graph"] if {"CreateAction"} & set(canonical.types(e))}
    assert {r["@id"] for r in root["mentions"]} == actions and len(actions) == 11
    assert {"datePublished", "qro:writer", "qro:writtenAt", "qro:signature", "qro:trustedTime"} <= set(root)


def test_the_question_names_the_source_circuit_the_four_logical_circuits_and_the_rule(quick):
    q = graph(generated(quick))["#question"]
    assert sorted(r["@id"] for r in q["object"]) == sorted([
        "#rule-quantum_film.ibm.decode.v1", SOURCE, f"{BUNDLE}/coherence-xx.qasm", f"{BUNDLE}/coherence-yy.qasm",
        f"{BUNDLE}/known-answer.qasm", f"{BUNDLE}/law.qasm"])
    assert set(q) == {"@id", "@type", "name", "description", "object"}


def test_a_compile_holds_its_manifest_and_logical_circuits_and_the_files_it_made(quick):
    ids = graph(generated(quick))
    morning, sheet = ids["#compile-ibm_kingston-morning"], ids["#compile-ibm_kingston-sheet-01"]
    assert sorted(r["@id"] for r in morning["object"]) == sorted([MANIFEST] + [f"{BUNDLE}/{n}.qasm" for n in (
        "known-answer", "law", "coherence-xx", "coherence-yy")])
    assert len(morning["result"]) == 12 and all(r["@id"].startswith(BUNDLE) for r in morning["result"])
    assert sorted(r["@id"].rsplit("/", 1)[1] for r in sheet["result"]) == [
        "known-answer.gates.json", "known-answer.isa.qasm3", "known-answer.qpy"]
    assert morning["instrument"] == {"@id": "#transpiler-qiskit-2.5.2"}


def test_the_metadata_passes_the_strict_reader_and_is_what_the_whole_checker_regenerates(quick):
    md = generated(quick)
    data = canonical.write(md)
    assert reader.read(data)["@graph"][1]["qro:generator"] == "qro-p1-ibm"
    plants.write_file(quick, canonical.DESCRIPTOR, data)
    from qro import checker
    checker.load()
    assert canonical.body_digest(checker.check(quick))


# -- determinism, and the metadata file is not an input (T1) ----------------------------------------------------------------------
def test_two_runs_and_two_copies_in_other_places_write_the_same_bytes(quick, tmp_path_factory):
    first = entity_bytes(generated(quick))
    assert entity_bytes(generated(quick)) == first
    other = tmp_path_factory.mktemp("elsewhere") / "a-longer-name-for-the-crate-directory"
    shutil.copytree(quick, other)
    assert entity_bytes(generated(other)) == first


@pytest.mark.parametrize("how", ["absent", "garbage", "another crate's", "empty"])
def test_the_output_is_byte_identical_whatever_the_metadata_file_holds(quick, tmp_path, how):
    """T1: the generator never reads ro-crate-metadata.json."""
    want = entity_bytes(generated(quick))
    (quick / canonical.DESCRIPTOR).unlink()
    if how == "garbage":
        plants.write_file(quick, canonical.DESCRIPTOR, b"\xff\xfe not json at all {{{")
    elif how == "empty":
        plants.write_file(quick, canonical.DESCRIPTOR, b"")
    elif how != "absent":
        other = fixture.make(tmp_path / "fixture")
        plants.write_file(quick, canonical.DESCRIPTOR, (other / canonical.DESCRIPTOR).read_bytes())
    assert entity_bytes(generated(quick)) == want


def test_the_metadata_file_is_never_opened(quick, monkeypatch):
    opened = []
    real_read = G.Crate.read
    monkeypatch.setattr(G.Crate, "read", lambda self, rel: opened.append(rel) or real_read(self, rel))
    generated(quick)
    assert canonical.DESCRIPTOR not in opened and len(opened) > 40
    assert canonical.DESCRIPTOR not in G.Crate(quick).paths


# -- no CHECKED value is copied (T2): each is made by the function its step uses ------------------------------------------------------
SENTINEL = "5" * 64


def guards_off(monkeypatch):
    monkeypatch.setattr(G, "_hold", lambda *a: None)


def test_every_commitment_is_made_by_p1_commits_function_and_a_sentinel_there_is_refused_by_the_guard(quick, monkeypatch):
    with monkeypatch.context() as m:
        guards_off(m)
        m.setattr(G.p1_commit, "commitment_of", lambda fields: SENTINEL)
        assert {e["qro:commitment"] for e in of_type(generated(quick), "qro:Pub")} == {SENTINEL}
    monkeypatch.setattr(G.p1_commit, "commitment_of", lambda fields: SENTINEL)
    with pytest.raises(G.GuardError) as x:
        generated(quick)
    assert x.value.guard == "G4"


def test_a_snapshots_three_claims_are_made_by_p1_calibrations_function(quick, monkeypatch):
    sentinel = {"qro:valuesDigest": "6" * 64, "qro:stamp": "2000-01-01T00:00:00Z", "qro:newestValue": "2000-01-02T00:00:00Z"}
    monkeypatch.setattr(G.cal, "claims", lambda snapshot: dict(sentinel))
    snaps = of_type(generated(quick), "qro:Snapshot")
    assert len(snaps) == 3
    for e in snaps:
        assert {k: e[k] for k in sentinel} == sentinel


def test_a_jobs_link_word_and_snapshots_are_made_by_p1_calibrations_link_for(quick, monkeypatch):
    monkeypatch.setattr(G.cal, "link_for", lambda first, history, carried: ("history-in-gap", (SNAP_1221, SNAP_0902)))
    jobs = of_type(generated(quick), "qro:Job")
    assert len(jobs) == 4
    for job in jobs:
        assert job["qro:calibrationLink"] == "history-in-gap"
        assert sorted(r["@id"] for r in job["qro:calibration"]) == sorted([SNAP_0902, SNAP_1221])


def test_a_decodes_rule_and_bit_order_are_the_rules_of_p1_decode_and_a_sentinel_there_is_refused(quick, monkeypatch):
    fake = dataclasses.replace(p1_decode.RULES[p1_decode.IBM_RULE], name="zz.decode/v9", order="lsb-first")
    with monkeypatch.context() as m:
        guards_off(m)
        m.setattr(G.p1_decode, "RULES", {p1_decode.IBM_RULE: fake})
        decodes = of_type(generated(quick), "qro:Decode")
    assert {(d["qro:decodeRule"], d["qro:bitOrder"]) for d in decodes} == {("zz.decode/v9", "lsb-first")}
    monkeypatch.setattr(G.p1_decode, "RULES", {p1_decode.IBM_RULE: fake})
    with pytest.raises(G.GuardError) as x:
        generated(quick)
    assert x.value.guard == "G5" and "counts" in x.value.detail


def test_the_times_and_the_shots_are_read_from_the_raw_result_by_p1_forms(quick, monkeypatch):
    real = p1_forms.parse_ibm_result

    def shifted(data):
        r = real(data)
        return dataclasses.replace(r, spans=tuple((a + timedelta(days=1), b + timedelta(days=1)) for a, b in r.spans),
                                   shots=7)
    with monkeypatch.context() as m:
        guards_off(m)
        m.setattr(G.p1_forms, "parse_ibm_result", shifted)
        md = generated(quick)
    ka = job_of(md, KA_LINE)
    assert ka["startTime"] == "2026-10-06T10:27:00.285375Z" and ka["endTime"] == "2026-10-06T10:27:01.376976Z"
    assert {e["qro:shots"] for e in of_type(md, "qro:RawResult")} == {7}
    monkeypatch.setattr(G.p1_forms, "parse_ibm_result", shifted)
    with pytest.raises(G.GuardError):
        generated(quick)


def test_with_no_guard_switched_off_the_honest_twin_raises_nothing(quick):
    assert guard(quick) is None


def test_the_guards_all_go_through_the_one_function_a_test_can_switch_off():
    import ast
    tree = ast.parse(Path(G.__file__).read_text(encoding="utf-8"))
    raisers = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call)
               and getattr(n.exc.func, "id", None) == "GuardError"]
    holds = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_hold"]
    assert len(holds) > 60 and len(raisers) == 4       # the one in _hold, the two where a LinkError is a G7 raise, and call_p2's, a raise of P2's made a `seam` one
    named = {n.args[1].value for n in holds if isinstance(n.args[1], ast.Constant)}
    assert named == {"G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11", "G12", "seam"}


# -- the guards, each tripped by one planted fault (T3: a record's own claim changed raises, and is never emitted) ---------------------------------
CASES = []


def case(name, guard_id, where):
    def register(fn):
        CASES.append(pytest.param(fn, guard_id, where, id=name))
        return fn
    return register


def job_records(f, line):
    return f.result_record(line)[1], f.result_record(line)[0]


@case("G1 a gate list is not the manifest's", "G1", "bundle/known-answer.gates.json")
def g1_gates(f, c):
    f.write(f"{BUNDLE}/known-answer.gates.json", f.read(f"{BUNDLE}/known-answer.gates.json") + b" ")


@case("G1 a logical circuit is not the manifest's", "G1", "bundle/law.qasm")
def g1_qasm(f, c):
    f.write(f"{BUNDLE}/law.qasm", f.read(f"{BUNDLE}/law.qasm") + b"// x\n")


@case("G1 a QPY file is not the manifest's", "G1", "bundle/known-answer.qpy")
def g1_qpy(f, c):
    f.write(f"{BUNDLE}/known-answer.qpy", f.read(f"{BUNDLE}/known-answer.qpy") + b"\0")


@case("G1 an ISA circuit is not the manifest's", "G1", "bundle/coherence-xx.isa.qasm3")
def g1_isa(f, c):
    f.write(f"{BUNDLE}/coherence-xx.isa.qasm3", f.read(f"{BUNDLE}/coherence-xx.isa.qasm3") + b"\n")


@case("G1 a README is not the manifest's", "G1", "bundle/README.md")
def g1_readme(f, c):
    f.write(f"{BUNDLE}/README.md", f.read(f"{BUNDLE}/README.md") + b"x")


@case("G1 a circuit file no manifest circuit names", "G1", "bundle/stray.qasm")
def g1_stray(f, c):
    f.write(f"{BUNDLE}/stray.qasm", b"OPENQASM 2.0;\n")


@case("G1 a bundle with files and no manifest", "G1", "ibm_kingston morning")
def g1_no_manifest(f, c):
    remove(c, MANIFEST)


@case("G1 a manifest of another device", "G1", "bundle/manifest.json")
def g1_device(f, c):
    f.edit_json(MANIFEST, lambda m: m.update(backend="ibm_fez"))


@case("G1 a manifest that is no manifest", "G1", "bundle/manifest.json")
def g1_not_a_manifest(f, c):
    f.write(MANIFEST, b"[]\n")


@case("G1 the manifest's options_sha256 is not the digest of its options", "G1", "bundle/manifest.json")
def g1_options(f, c):
    f.edit_json(MANIFEST, lambda m: m.update(options_sha256="ab" * 32))


@case("G1 the source circuit is missing", "G1", SOURCE)
def g1_source_missing(f, c):
    remove(c, SOURCE)


@case("G1 the source circuit is not the manifest's", "G1", SOURCE)
def g1_source_changed(f, c):
    f.write(SOURCE, f.read(SOURCE) + b"\n")


@case("G2 the line's bundle digest is not the manifest's", "G2", "known-answer-line.json")
def g2_bundle(f, c):
    f.edit_json(KA_LINE, lambda o: o.update(bundle_sha256="0" * 64))


@case("G2 the line's commitments are not the manifest's", "G2", "coherence-line.json")
def g2_commitments(f, c):
    f.edit_json(COH_LINE, lambda o: o.update(commitments=list(reversed(o["commitments"]))))


@case("G2 the line's stock is not the manifest's", "G2", "known-answer-line.json")
def g2_stock(f, c):
    f.edit_json(KA_LINE, lambda o: o.update(stock="pauli-3x3"))


@case("G2 the line's program is not the manifest's", "G2", "known-answer-line.json")
def g2_program(f, c):
    f.edit_json(KA_LINE, lambda o: o.update(program="estimator"))


def line_term(term):
    def plant(f, c):
        f.edit_json(KA_LINE, lambda o: o.update({term: o[term] + "x"}))
    return plant


for _term in ("kind", "route", "backend"):
    CASES.append(pytest.param(line_term(_term), "G2", "known-answer-line.json", id=f"G2 the line's {_term} is not the manifest's"))


@case("G2 the marker names another job", "G2", "known-answer-submitting.json")
def g2_marker_job(f, c):
    f.edit_json(KA_MARKER, lambda o: o.update(job="law"))


@case("G2 the marker names another bundle", "G2", "known-answer-submitting.json")
def g2_marker_bundle(f, c):
    f.edit_json(KA_MARKER, lambda o: o.update(bundle_sha256="1" * 64))


@case("G2 a job with no line", "G2", "ibm_kingston morning known-answer")
def g2_no_line(f, c):
    remove(c, KA_LINE)


@case("G2 a job with no metrics wrapper", "G2", "ibm_kingston morning known-answer")
def g2_no_metrics(f, c):
    remove(c, KA_METRICS)


@case("G2 a job id two lines hold", "G2", "sheet-01/run/known-answer-line.json")
def g2_twice(f, c):
    f.edit_json(S1_LINE, lambda o: o.update(job_id=f.json(KA_LINE)["job_id"]))


@case("G2 a bundle with no known-answer job", "G2", "ibm_kingston morning")
def g2_no_known_answer(f, c):
    read = f.result_record(KA_LINE)
    for rel in (KA_LINE, KA_METRICS, KA_MARKER, KA_RAW, f"{MORNING_KA}-verdict.json", KA_REC, *read):
        remove(c, rel)


@case("G2 a job in a bundle the crate carries no manifest of", "G2", "ibm_kingston sheet-01 known-answer")
def g2_no_bundle(f, c):
    for p in sorted(Path(c).joinpath(*SHEET1_BUNDLE.split("/")).iterdir()):
        p.unlink()


@case("G2 a job the manifest does not name", "G2", "ibm_kingston morning coherence")
def g2_unnamed(f, c):
    def rename(m):
        for job in m["jobs"]:
            if job["job"] == "coherence":
                job["job"] = "coherence-renamed"
    f.edit_json(MANIFEST, rename)


@case("G3 a record's digest is not its body's", "G3", "known-answer-pub0-known-answer.json")
def g3_digest(f, c):
    f.edit_json(KA_REC, lambda o: o.update(digest="0" * 64))


@case("G3 a record's source field is of another type than the manifest's, though equal", "G3",
      "known-answer-pub0-known-answer.json")
def g3_type(f, c):
    record = f.json(KA_REC)
    record["source"]["shots"] = float(record["source"]["shots"])           # 1024.0 == 1024; the commitment is of an integer
    f.put_record(KA_REC, record)


def source_term(term, change):
    def plant(f, c):
        record = f.json(KA_REC)
        record["source"][term] = change(record["source"][term])
        f.put_record(KA_REC, record)
    return plant


def record_term(term):
    def plant(f, c):
        record = f.json(KA_REC)
        record[term] += "x"
        f.put_record(KA_REC, record)
    return plant


for _term, _change in (("submitted_at", lambda v: v + "x"), ("backend", lambda v: v + "x"), ("kind", lambda v: v + "x"),
                       ("program", lambda v: v + "x"), ("route", lambda v: v + "x"), ("decode", lambda v: v + "x"),
                       ("options", lambda v: {**v, "x": 1}), ("options_sha256", other_digit), ("pub", lambda v: v + 5),
                       ("circuit_sha256", other_digit), ("salt", other_digit)):
    CASES.append(pytest.param(source_term(_term, _change), "G3", "known-answer-pub0-known-answer.json",
                              id=f"G3 the record's source.{_term} is not the manifest's or the line's"))
for _term in ("stock", "basis"):
    CASES.append(pytest.param(record_term(_term), "G3", "known-answer-pub0-known-answer.json",
                              id=f"G3 the record's {_term} is not the manifest's"))


@case("G3 a record of a PUB the job lacks", "G3", "ibm_kingston morning known-answer")
def g3_extra(f, c):
    f.write(f"{RUN}/known-answer-pub1-extra.json", f.read(KA_REC))


@case("G3 a record's shots are not the manifest's", "G3", "known-answer-pub0-known-answer.json")
def g3_shots(f, c):
    o = f.json(KA_REC)
    o["source"]["shots"] += 1
    f.put_record(KA_REC, o)


@case("G3 a record's role is not the manifest's", "G3", "known-answer-pub0-known-answer.json")
def g3_role(f, c):
    o = f.json(KA_REC)
    o["role"] = "law"
    f.put_record(KA_REC, o)


@case("G3 a record's job id is not the line's", "G3", "known-answer-pub0-known-answer.json")
def g3_job_id(f, c):
    o = f.json(KA_REC)
    o["source"]["job_id"] = "zzzz"
    f.put_record(KA_REC, o)


@case("G3 a record's QPY digest is not the manifest's", "G3", "known-answer-pub0-known-answer.json")
def g3_isa(f, c):
    o = f.json(KA_REC)
    o["source"]["isa_sha256"] = "2" * 64
    f.put_record(KA_REC, o)


@case("G3 a record's commitment is not the manifest's", "G3", "known-answer-pub0-known-answer.json")
def g3_commitment(f, c):
    o = f.json(KA_REC)
    o["source"]["commitment"] = "3" * 64
    f.put_record(KA_REC, o)


@case("G3 a PUB with no record", "G3", "ibm_kingston morning known-answer")
def g3_missing(f, c):
    remove(c, KA_REC)


@case("G3 a record of another circuit than the manifest's PUB", "G3", "coherence-pub0-coherence-yy.json")
def g3_renamed(f, c):
    f.write(f"{MORNING_COH}-pub0-coherence-yy.json", f.read(COH_REC0))
    remove(c, COH_REC0)


@case("G3 a PUB with two records", "G3", "ibm_kingston morning coherence")
def g3_two(f, c):
    f.write(f"{MORNING_COH}-pub0-coherence-yy.json", f.read(COH_REC0))


@case("G4 IBM's echo is not the recomputed commitment", "G4", "known-answer-pub0-known-answer.json")
def g4_echo(f, c):
    def edit(doc):
        doc["__value__"]["pub_results"][0]["__value__"]["metadata"]["circuit_metadata"]["qf_commitment"] = "0" * 64
    f.edit_json(KA_RAW, edit)


@case("G4 a salt changed where the manifest and the record agree, the commitments not", "G4",
      "known-answer-pub0-known-answer.json")
def g4_salt(f, c):
    def manifest(m):
        for job in m["jobs"]:
            for circuit in job["circuits"]:
                if circuit["name"] == "known-answer":
                    circuit["salt"] = "4" * 64
    f.edit_json(MANIFEST, manifest)
    f.reseal_bundle(BUNDLE)
    o = f.json(KA_REC)
    o["source"]["salt"] = "4" * 64
    f.put_record(KA_REC, o)


@case("G5 the raw result holds fewer rows than the manifest's shots", "G5", "known-answer-raw.json")
def g5_rows(f, c):
    doc = f.json(KA_RAW)
    rows, _ = plants.rows_of(plants.array_of(doc, 0)["__value__"])
    plants.array_of(doc, 0)["__value__"] = p1_builder.packed(p1_builder.npy(rows[:-1]))
    f.put_json(KA_RAW, doc)


@case("G5 the raw result holds more PUBs than the line lists", "G5", "coherence-raw.json")
def g5_pubs(f, c):
    f.write(COH_RAW, p1_builder.raw_ibm([[0]] * 3, [None] * 3))


@case("G5 the record's counts are not the raw result's", "G5", "known-answer-pub0-known-answer.json")
def g5_counts(f, c):
    o = f.json(KA_REC)
    o["counts"][0][1] += 1
    f.put_record(KA_REC, o)


@case("G6 IBM's created time is not the line's submitted time", "G6", "known-answer-metrics.json")
def g6_created(f, c):
    def edit(o):
        o["job"]["created"] = o["metrics"]["timestamps"]["created"] = "2026-10-05T10:26:57Z"
    f.edit_json(KA_METRICS, edit)


@case("G6 IBM's created time is earlier than the line's submitted time", "G6", "known-answer-metrics.json")
def g6_created_earlier(f, c):
    def edit(o):
        o["job"]["created"] = o["metrics"]["timestamps"]["created"] = "2026-10-05T10:26:55Z"
    f.edit_json(KA_METRICS, edit)


@case("G6 the metrics wrapper is of another job", "G6", "known-answer-metrics.json")
def g6_job(f, c):
    f.edit_json(KA_METRICS, lambda o: o.update(job_id="zzzz"))


@case("G6 the metrics wrapper is of another device", "G6", "known-answer-metrics.json")
def g6_device(f, c):
    f.edit_json(KA_METRICS, lambda o: o.update(backend="ibm_fez"))


@case("G6 the execution span is not inside [running, finished]", "G6", "known-answer-metrics.json")
def g6_span(f, c):
    f.edit_json(KA_METRICS, lambda o: o["metrics"]["timestamps"].update(running="2026-10-05T10:27:30Z"))


@case("G6 the execution span ends after finished", "G6", "known-answer-metrics.json")
def g6_span_end(f, c):
    f.edit_json(KA_METRICS, lambda o: o["metrics"]["timestamps"].update(finished="2026-10-05T10:27:01Z"))


def edit_job_record(line, edit, seal=True):
    def mutate(f, c):
        _, path = f.result_record(line)
        f.edit_json(path, edit)
        if seal:
            f.reseal_entry(path)
    return mutate


CASES += [
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"].update(commitments_equal=False)), "G7", "ibm-refetch",
                 id="G7 a flag of the read does not hold"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"].update(commitments_equal=1)), "G7", "ibm-refetch",
                 id="G7 a flag of the read is 1, not true"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"]["pubs"][0].update(gate_list_equal=1)), "G7", "ibm-refetch",
                 id="G7 a PUB's gate-list flag of the read is 1, not true"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"]["pubs"][0].update(gates_equal=1)), "G7", "ibm-refetch",
                 id="G7 a PUB's gates flag of the read is 1, not true"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["calibration"].update(first_shot="2026-10-05T10:27:00.285376Z")),
                 "G7", "ibm-refetch", id="G7 the read's first shot is not the span's start"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["calibration"].update(running="2026-10-05T10:26:58.584413Z")),
                 "G7", "ibm-refetch", id="G7 the read's running time is not the metrics'"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"].update(pubs_in_ibm_copy=2)), "G7", "ibm-refetch",
                 id="G7 IBM's copy holds other PUBs"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"]["pubs"][0].update(commitment_in_ibm_copy="0" * 64)), "G7",
                 "ibm-refetch", id="G7 IBM's copy holds another commitment"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"]["pubs"][0].update(gate_list_equal=False)), "G7",
                 "ibm-refetch", id="G7 a gate-list flag does not hold"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"]["pubs"][0].update(gates_equal=False)), "G7",
                 "ibm-refetch", id="G7 a gates flag does not hold"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"].update(created_equal_to_line=False)), "G7",
                 "ibm-refetch", id="G7 the created flag does not hold"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"].update(options_equal_to_manifest=False)), "G7",
                 "ibm-refetch", id="G7 the options flag does not hold"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"].update(pubs_in_line=2)), "G7", "ibm-refetch",
                 id="G7 the read counts other PUBs in the line"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"].update(pubs=[])), "G7", "ibm-refetch",
                 id="G7 the read lists none of the PUBs"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"]["pubs"][0].update(commitment_in_line="0" * 64)), "G7",
                 "ibm-refetch", id="G7 the read's commitment in the line is another"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["holds"]["pubs"][0].update(commitment_in_ibm_copy="0" * 64,
                                                                                  commitment_in_line="0" * 64)),
                 "G7", "ibm-refetch", id="G7 the read's two commitments agree with each other and not with the line's"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o.update(role="law")), "G7", "ibm-refetch",
                 id="G7 the read's role is not the job's"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o.update(device="ibm_fez")), "G7", "ibm-refetch",
                 id="G7 the read is of another device"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["calibration"]["before_first_shot"].update(
        file="ibm_kingston/properties-20261005T122118Z.json")), "G7", "ibm-refetch",
        id="G7 the snapshot the history returned is not valid for the first shot"),
    pytest.param(edit_job_record(KA_LINE, lambda o: o["calibration"]["before_running"].update(
        file="ibm_kingston/properties-20261005T000000Z.json")), "G7", "ibm-refetch",
        id="G7 the snapshot at running time is not carried"),
]


@case("G7 the snapshot the history returned is not carried", "G7", "ibm-refetch")
def g7_not_carried(f, c):
    remove(c, SNAP_0902)
    unlist(f, SNAP_0902)


@case("G7 a job record of the read for a job the crate lacks", "G7", "2026-10-14")
def g7_extra(f, c):
    f.write(f"{plants.REFETCH}/ibm_kingston/{OTHER_JOB}.json", f.read(f.result_record(KA_LINE)[1]))


@case("G7 a job with no job record of the read", "G7", "2026-10-14")
def g7_missing(f, c):
    remove(c, f.result_record(KA_LINE)[1])


def edit_result_record(line, edit, seal=True):
    def mutate(f, c):
        path, _ = f.result_record(line)
        f.edit_json(path, edit)
        if seal:
            f.reseal_entry(path)
    return mutate


CASES += [
    pytest.param(edit_result_record(KA_LINE, lambda o: o.update(bytes_equal=False)), "G8", "ibm-results-refetch",
                 id="G8 the read does not say IBM's copy is the bytes"),
    pytest.param(edit_result_record(KA_LINE, lambda o: o["committed"].update(sha256="0" * 64)), "G8",
                 "ibm-results-refetch", id="G8 the committed digest is not the raw result's"),
    pytest.param(edit_result_record(KA_LINE, lambda o: o["ibm_copy"].update(sha256="0" * 64)), "G8",
                 "ibm-results-refetch", id="G8 IBM's copy holds another digest"),
    pytest.param(edit_result_record(KA_LINE, lambda o: o["ibm_copy"].update(bytes=o["ibm_copy"]["bytes"] + 1)), "G8",
                 "ibm-results-refetch", id="G8 IBM's copy holds another size"),
    pytest.param(edit_result_record(KA_LINE, lambda o: o["committed"].update(path="x.json")), "G8",
                 "ibm-results-refetch", id="G8 the record names another file than the raw result"),
    pytest.param(edit_result_record(KA_LINE, lambda o: o.update(agree_at="text")), "G8", "ibm-results-refetch",
                 id="G8 the read agrees at another level than the bytes"),
]


def both(key, value):
    def edit(o):
        o["committed"][key] = o["ibm_copy"][key] = value(o)
    return edit


CASES += [
    pytest.param(edit_result_record(KA_LINE, both("sha256", lambda o: "0" * 64)), "G8", "ibm-results-refetch",
                 id="G8 the record's two digests agree with each other and not with the raw result's"),
    pytest.param(edit_result_record(KA_LINE, both("bytes", lambda o: o["committed"]["bytes"] + 1)), "G8",
                 "ibm-results-refetch", id="G8 the record's two sizes agree with each other and not with the raw result's"),
]


@case("G8 a result record for a job the crate lacks", "G8", "2026-10-14")
def g8_extra(f, c):
    f.write(f"{plants.RESULTS}/ibm_kingston/{OTHER_JOB}.json", f.read(f.result_record(KA_LINE)[0]))


@case("G8 a result record of another job", "G8", "ibm-results-refetch")
def g8_other_job(f, c):
    other = f.job_id(S1_LINE)
    path, _ = f.result_record(KA_LINE)
    f.edit_json(path, lambda o: o.update(job_id=other))
    f.reseal_entry(path)


@case("G8 a job with no result record of the read", "G8", "2026-10-14")
def g8_missing(f, c):
    remove(c, f.result_record(KA_LINE)[0])


@case("G9 a file of the read is not the digest its MANIFEST lists", "G9", "ibm-refetch")
def g9_digest(f, c):
    f.edit_json(f.result_record(KA_LINE)[1], lambda o: o["fetched_at"].update(value="2026-10-14T15:40:27Z"))


@case("G9 the MANIFEST lists another digest of a file of the size it has", "G9", "ibm-refetch")
def g9_digest_alone(f, c):
    name = f.result_record(KA_LINE)[1].split("/", 2)[2]

    def edit(m):
        for e in m["files"]:
            if e["path"] == name:
                e["sha256"] = other_digit(e["sha256"])
    f.edit_json("2026-10-14/ibm-refetch/MANIFEST.json", edit)


@case("G9 a snapshot the MANIFEST lists, of a device the crate carries, is not carried", "G9", "ibm-refetch/MANIFEST.json")
def g9_dropped(f, c):
    remove(c, SNAP_1221)


@case("G9 the snapshot dropped with the MANIFEST that lists it (the second verifier's crate)", "G9", "2026-10-14/ibm-refetch/")
def g9_dropped_with_its_manifest(f, c):
    remove(c, SNAP_1221)
    remove(c, "2026-10-14/ibm-refetch/MANIFEST.json")


@case("G9 the read's job records and snapshots without their MANIFEST", "G9", "2026-10-14/ibm-refetch/")
def g9_no_refetch_manifest(f, c):
    remove(c, "2026-10-14/ibm-refetch/MANIFEST.json")


@case("G9 the read's result records without their MANIFEST", "G9", "2026-10-14/ibm-results-refetch/")
def g9_no_results_manifest(f, c):
    remove(c, "2026-10-14/ibm-results-refetch/MANIFEST.json")


@case("G9 a file of the read is not in its MANIFEST", "G9", "ibm-refetch")
def g9_unlisted(f, c):
    name = f.result_record(KA_LINE)[1].split("/", 2)[2]
    f.edit_json("2026-10-14/ibm-refetch/MANIFEST.json",
                lambda m: m.update(files=[e for e in m["files"] if e["path"] != name]))


@case("G9 a result record is not the size its MANIFEST lists", "G9", "ibm-results-refetch")
def g9_size(f, c):
    name = f.result_record(KA_LINE)[0].split("/", 2)[2]

    def edit(m):
        for e in m["files"]:
            if e["path"] == name:
                e["bytes"] += 1
    f.edit_json("2026-10-14/ibm-results-refetch/MANIFEST.json", edit)


@case("G9 a MANIFEST of another format", "G9", "ibm-refetch")
def g9_format(f, c):
    f.edit_json("2026-10-14/ibm-refetch/MANIFEST.json", lambda m: m.update(format="qro-crate/ibm-refetch-manifest/v1"))


@case("G10 a snapshot holds a key IBM's form does not", "G10", "ibm-refetch/ibm_kingston/properties-20261005T090246Z.json")
def g10_form(f, c):
    f.edit_json(SNAP_0902, lambda o: o.update(extra=1))


@case("G10 a snapshot is stamped other than its name says", "G10", "properties-20261005T090247Z.json")
def g10_stamp(f, c):
    new = SNAP_0902.replace("090246", "090247")
    f.write(new, f.read(SNAP_0902))
    remove(c, SNAP_0902)


@case("G10 a snapshot is of another device than its place", "G10", "ibm-refetch/ibm_kingston/properties-20261005T112827Z.json")
def g10_device(f, c):
    f.edit_json(SNAP_1128, lambda o: o.update(backend_name="ibm_fez"))


@case("G12 a file at the root", "G12", "README.txt")
def g12_root(f, c):
    f.write("README.txt", b"x")


@case("G12 a dry-run probe's log", "G12", "ibm-dryrun-probe.log")
def g12_probe(f, c):
    f.write("2026-10-14/ibm-dryrun-probe.log", b"x")


@case("G12 a file in a bundle that is no circuit's", "G12", "bundle/notes.txt")
def g12_bundle(f, c):
    f.write(f"{BUNDLE}/notes.txt", b"x")


@case("G12 a file in a run directory that is no job's", "G12", "run/known-answer-extra.json")
def g12_run(f, c):
    f.write(f"{RUN}/known-answer-extra.json", b"{}")


@case("G12 a file in a sheet's run directory that is no part of a run", "G12", "sheet-01/run/known-answer-x.json")
def g12_sheet_run(f, c):
    f.write(f"{IBM_DIR}/sheet-01/run/known-answer-x.json", b"{}")


@case("G12 a file of another day", "G12", "2026-10-06/x.json")
def g12_day(f, c):
    f.write("2026-10-06/x.json", b"{}")


@pytest.fixture
def sandbox(quick):
    return quick


@pytest.mark.parametrize("plant, guard_id, where", CASES)
def test_each_planted_fault_trips_its_guard_and_no_other_first(sandbox, plant, guard_id, where):
    plant(forge(sandbox), sandbox)
    g = guard(sandbox)
    assert g is not None, "the generator accepted a crate with a planted fault"
    assert (g.guard, where in g.where) == (guard_id, True), (g.guard, g.where, g.detail)


def test_every_guard_of_the_design_has_a_plant_that_trips_it_but_g11_which_is_atlas():
    ids = {p.values[1] for p in CASES}
    assert ids == {"G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G12"}


def test_an_unknown_decode_rule_is_a_g5_raise(quick, monkeypatch):
    monkeypatch.setattr(G.p1_decode, "RULES", {})
    g = guard(quick)
    assert g.guard == "G5" and "no decode rule quantum_film.ibm.decode/v1 is built" in g.detail


def g4_g5_arguments(quick):
    """What G._g4_g5 is given for the morning known-answer job, parsed from the twin's own records."""
    def read(rel):
        return plants.read_file(quick, rel)
    manifest = rec.manifest(read(MANIFEST), MANIFEST)
    spec = dict(manifest.jobs)["known-answer"]
    return ({"raw": KA_RAW}, manifest, spec, rec.line(read(KA_LINE), KA_LINE),
            {0: (KA_REC, rec.device_run(read(KA_REC), KA_REC), spec[0])}, p1_forms.parse_ibm_result(read(KA_RAW)))


def test_a_manifest_naming_a_decode_rule_that_is_not_built_is_a_g5_raise_at_the_raw_result(quick):
    files, manifest, spec, line, records, raw = g4_g5_arguments(quick)
    assert G._g4_g5(files, manifest, spec, line, records, raw) is None
    with pytest.raises(G.GuardError) as x:
        G._g4_g5(files, dataclasses.replace(manifest, decode="quantum_film.ibm.decode/v9"), spec, line, records, raw)
    assert (x.value.guard, x.value.where) == ("G5", KA_RAW) and "no decode rule" in x.value.detail


def test_g5_holds_the_raw_results_pubs_to_the_manifests_and_to_the_lines(quick):
    """G2 holds the line's commitments to the manifest job's before G5 looks, so a planted crate cannot tell the counts apart."""
    files, manifest, spec, line, records, raw = g4_g5_arguments(quick)
    with pytest.raises(G.GuardError) as manifest_longer:
        G._g4_g5(files, manifest, (spec[0], spec[0]), line, records, raw)
    with pytest.raises(G.GuardError) as line_longer:
        G._g4_g5(files, manifest, spec, dataclasses.replace(line, commitments=(line.commitments[0],) * 2), records, raw)
    for raised in (manifest_longer, line_longer):
        assert (raised.value.guard, raised.value.where) == ("G5", KA_RAW) and "holds 1 PUBs" in raised.value.detail


def test_g4_holds_the_manifests_the_lines_the_records_and_ibms_echo_each_to_the_recomputed_commitment(quick):
    """In a crate the manifest's, the line's and the record's commitments are one value by the time G4 looks (G2 and G3 hold
    them to each other), so a planted crate cannot tell which comparison is the guard: each is tried here alone."""
    files, manifest, spec, line, records, raw = g4_g5_arguments(quick)
    path, run, c = records[0]
    bad = "0" * 64
    other_pub = dataclasses.replace(raw.pubs[0], echo=bad)
    variants = {
        "the manifest's": (files, manifest, [dataclasses.replace(c, commitment=bad)], line,
                           {0: (path, run, dataclasses.replace(c, commitment=bad))}, raw),
        "the line's": (files, manifest, spec, dataclasses.replace(line, commitments=(bad,)), records, raw),
        "the record's": (files, manifest, spec, line,
                         {0: (path, dataclasses.replace(run, source={**run.source, "commitment": bad}), c)}, raw),
        "IBM's echo": (files, manifest, spec, line, records, dataclasses.replace(raw, pubs=(other_pub,))),
    }
    for name, args in variants.items():
        with pytest.raises(G.GuardError) as x:
            G._g4_g5(*args)
        assert (x.value.guard, x.value.where, x.value.detail.startswith(name)) == ("G4", path, True), name


def stand_in(label, digest, roles, jid, device="ibm_x"):
    """A job as _known_answers reads it: the bundle it ran from, the roles its manifest gives and its records hold."""
    return SimpleNamespace(device=device, label=label, id=jid, line=SimpleNamespace(bundle_sha256=digest),
                           spec=[SimpleNamespace(role=r) for r in roles],
                           records={i: (f"run/{jid}-{i}.json", SimpleNamespace(role=r), None) for i, r in enumerate(roles)},
                           files={"line": f"run/{jid}-line.json"})


def test_a_bundle_holds_one_known_answer_job_and_that_job_one_known_answer_pub():
    one, law = stand_in("morning", "a" * 64, ["known-answer"], "j1"), stand_in("morning", "a" * 64, ["law"], "j2")
    assert G._known_answers([one, law]) == {("ibm_x", "morning"): "#pub-j1-0"}
    with pytest.raises(G.GuardError) as none:
        G._known_answers([law])
    assert (none.value.guard, "hold 0 known-answer jobs" in none.value.detail) == ("G2", True)
    with pytest.raises(G.GuardError) as two_jobs:
        G._known_answers([one, stand_in("morning", "a" * 64, ["known-answer"], "j3")])
    assert (two_jobs.value.guard, "hold 2 known-answer jobs" in two_jobs.value.detail) == ("G2", True)
    with pytest.raises(G.GuardError) as two_pubs:
        G._known_answers([stand_in("morning", "a" * 64, ["known-answer", "known-answer"], "j4")])
    assert (two_pubs.value.guard, two_pubs.value.where) == ("G2", "run/j4-line.json")
    assert "more than one known-answer PUB" in two_pubs.value.detail
    # a known-answer job that ran from another bundle (another digest) is not this bundle's
    assert G._known_answers([one, law, stand_in("morning", "b" * 64, ["known-answer"], "j5")])
    # nor is the bundle of another device, whatever its digest says: each device's bundle has its own
    other = stand_in("morning", "a" * 64, ["known-answer"], "j6", device="ibm_y")
    assert G._known_answers([one, law, other]) == {("ibm_x", "morning"): "#pub-j1-0", ("ibm_y", "morning"): "#pub-j6-0"}


def test_a_file_named_like_a_prediction_is_carried_by_its_devices_dataset_of_snapshots_and_predictions(quick):
    names = [f"{IBM_DIR}/prediction-backend.json", f"{IBM_DIR}/prediction-none.json"]
    other = "2026-10-05/ibm/ibm_fez/prediction-backend.json"            # a device the crate has no job of: its own Dataset
    for rel in names + [other]:
        forge(quick).write(rel, b"{}\n")
    ids = graph(generated(quick))
    held = {p["@id"] for p in ids["#files-ibm_kingston"]["hasPart"]}
    assert set(names) <= held and len(held) == 3 + 2 and other not in held
    assert [p["@id"] for p in ids["#files-ibm_fez"]["hasPart"]] == [other]
    assert all(ids[rel]["license"] == {"@id": "LICENSE-quantum-film"} for rel in names + [other])


def test_a_snapshot_the_history_returned_and_the_crate_does_not_carry_is_said_not_to_be_carried(quick):
    remove(quick, SNAP_0902)
    g = guard(quick)
    assert (g.guard, g.where) == ("G9", f"{plants.REFETCH}/MANIFEST.json"), (g.guard, g.where)      # the MANIFEST lists it
    unlist(forge(quick), SNAP_0902)
    g = guard(quick)
    assert g.guard == "G7" and "is not carried" in g.detail, g.detail


def test_an_id_is_written_once_a_shared_entity_is_said_again_as_it_was_and_no_other_way_round_the_guard_is_open():
    entities = G._Entities("G2")
    entities["#a"] = {"@id": "#a", "name": "one"}
    with pytest.raises(G.GuardError) as twice:
        entities["#a"] = {"@id": "#a", "name": "one"}
    assert (twice.value.guard, twice.value.where, "written twice" in twice.value.detail) == ("G2", "#a", True)
    with pytest.raises(G.GuardError) as update:
        entities.update({"#a": {"@id": "#a"}})
    assert update.value.guard == "G2"
    with pytest.raises(TypeError):
        entities.setdefault("#b", {})
    entities.update({"#b": {"@id": "#b"}})
    program = G.software("#program-sampler", "sampler")
    entities.shared(program)
    entities.shared(dict(program))                           # said again as it was: no write
    with pytest.raises(G.GuardError) as differently:
        entities.shared(G.software("#program-sampler", "another"))
    assert (differently.value.guard, differently.value.where) == ("G2", "#program-sampler")
    assert sorted(entities) == ["#a", "#b", "#program-sampler"] and entities["#a"]["name"] == "one"
    assert G._Entities("G11").guard == "G11"


def test_a_job_whose_entities_are_written_twice_is_a_g2_raise_on_the_ibm_path(quick, monkeypatch):
    real = G._job_entities
    done = []

    def twice(crate, job, snapshots, read, known, entities):
        real(crate, job, snapshots, read, known, entities)
        if not done:
            done.append(job.id)
            real(crate, job, snapshots, read, known, entities)
    monkeypatch.setattr(G, "_job_entities", twice)
    g = guard(quick)
    assert g.guard == "G2" and "written twice" in g.detail, g and g.detail


def test_the_programs_and_transpilers_of_many_jobs_and_bundles_are_written_once_each(quick):
    md = generated(quick)
    ids = [e["@id"] for e in md["@graph"]]
    assert len(ids) == len(set(ids)) and ids.count("#program-sampler") == 1
    assert sum(i.startswith("#transpiler-") for i in ids) == 1 and sum(i.startswith("#compile-") for i in ids) == 3


def test_a_job_of_more_than_ten_pubs_is_a_g3_raise_before_an_id_of_two_digits_is_written():
    with pytest.raises(G.GuardError) as eleven:
        G._g3(None, "w", {}, None, (None,) * 11, None)
    assert (eleven.value.guard, eleven.value.where, "11 PUBs" in eleven.value.detail) == ("G3", "w", True)
    with pytest.raises(G.GuardError) as ten:                 # ten pass the count, and lack their records
        G._g3(None, "w", {}, None, (None,) * 10, None)
    assert ten.value.guard == "G3" and "the records are of PUBs []" in ten.value.detail
    assert G.MAX_PUBS == 10


def spanless(f):
    """The coherence job's raw result with no execution span, and the read's first shot as its running time."""
    def nospan(doc):
        del doc["__value__"]["metadata"]["execution"]
    f.edit_json(COH_RAW, nospan)
    f.reseal_raw(COH_LINE, COH_RAW)
    f.edit_json(f.result_record(COH_LINE)[1], lambda o: o["calibration"].update(first_shot=o["calibration"]["running"]))
    f.reseal_entry(f.result_record(COH_LINE)[1])


def test_a_job_with_no_span_still_names_a_snapshot_the_crate_must_carry(quick):
    f = forge(quick)
    spanless(f)
    assert guard(quick) is None
    read = f.result_record(COH_LINE)[1]
    f.edit_json(read, lambda o: o["calibration"]["before_first_shot"].update(file="ibm_kingston/properties-20261005T000000Z.json"))
    f.reseal_entry(read)
    g = guard(quick)
    assert (g.guard, g.where, "is not carried" in g.detail) == ("G7", read, True), g and (g.guard, g.where, g.detail)


def test_a_decode_rule_ibms_counts_cannot_read_is_a_g5_raise_and_not_a_crash(quick):
    recommit(quick, {"decode": p1_decode.ATLAS_RULE})
    g = guard(quick)
    assert (g.guard, "does not read the order atlas-register" in g.detail) == ("G5", True), g and g.detail


def test_a_file_under_question_fits_no_layout_while_p2_is_absent(quick):
    forge(quick).write("question/law.json", b"{}")
    g = guard(quick)
    assert (g.guard, g.where) == ("G12", "question/law.json")


def test_the_jobs_of_a_crate_with_no_execution_span_are_unknown_and_unlinked(quick):
    """A raw result with no span gives startTime, endTime and the link `unknown` (the design's item 5)."""
    f = forge(quick)
    spanless(f)
    job = job_of(generated(quick), COH_LINE)
    assert (job["startTime"], job["endTime"], job["qro:calibrationLink"]) == ("unknown", "unknown", "unknown")
    assert "qro:calibration" not in job and job["qro:historyAtRunning"] == {"@id": SNAP_0902}
