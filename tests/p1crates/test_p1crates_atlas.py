"""P1's real Atlas crate (P1's design, items 1.3 and 4), built from moth-quantum's records of 2026-09-25 and 2026-09-26 and
the known-answer vector, outside the tree, by the adapter as a process, and checked by the command line as one. This is the
gate that reads the real bytes: the six law results and the vector, which P1.1's tests hold only as measured literals and
bytes made in their shape (no Moth byte enters the tree, the lead's ruling of 2026-10-19T13:15:40Z). Each is read here,
whole, as the readers read it."""
import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path

import pytest

import p1crates_support as S
from qro import canonical, p1_decode, p1_forms, p1_records as rec, p1_steps


@pytest.fixture(scope="module")
def crate():
    return S.built("atlas")[0]


@pytest.fixture(scope="module")
def md():
    return S.metadata("atlas")


def graph(md):
    return {e["@id"]: e for e in md["@graph"]}


def results(md):
    return [e for e in S.of_type(md, "qro:RawResult") if e["qro:rawForm"] == "atlas-tomography-result/v1"]


def test_the_atlas_crate_is_built_outside_the_tree_and_the_command_line_accepts_it(crate):
    path, identity, line = S.built("atlas")
    assert re.fullmatch(r"BUILT atlas: 32 files, [0-9]+ bytes, identity [0-9a-f]{64}", line), line
    assert S.ROOT not in path.parents and S.MOTH not in path.parents
    assert S.checked("atlas") == (0, f"ACCEPTED {identity}", "")


def test_the_crate_holds_the_files_and_entities_the_design_counts(crate, md):
    files = [p for p in crate.rglob("*") if p.is_file() and p.name != canonical.DESCRIPTOR]
    assert len(files) == 31 and sum(p.stat().st_size for p in files) == 5_024_686       # the records, and P2's question/law.json
    kinds = {}
    for e in md["@graph"]:
        kinds[tuple(S.types_of(e))] = kinds.get(tuple(S.types_of(e)), 0) + 1
    # P1's entities and P2's: question/law.json and its Dataset, the Measuring, 20 Contrasts and 30 Measurements (no Hold: Atlas
    # runs no Compile)
    assert kinds == {("File",): 24, ("File", "qro:RawResult"): 7, ("Dataset",): 5, ("IndividualProduct",): 1,
                     ("SoftwareApplication",): 2, ("qro:Pub",): 7, ("CreateAction", "qro:Decode"): 7,
                     ("CreateAction", "qro:Job"): 7, ("CreativeWork", "Profile"): 2, ("CreativeWork", "qro:Question"): 1,
                     ("CreativeWork",): 2, ("CreateAction", "qro:Measuring"): 1, ("qro:Contrast",): 20,
                     ("qro:Measurement",): 30}
    assert len(md["@graph"]) == 116 and len(S.of_type(md, "qro:RawResult")) == 7


def test_nothing_left_out_is_in_the_crate_and_no_atlas_file_is_in_the_tree(crate):
    names = [p.name for p in crate.rglob("*") if p.is_file()]
    assert not [n for n in names if n.endswith(".platform.json")] and not [n for n in names if n.startswith("rolls-")]
    assert not [p for p in crate.rglob("*") if p.is_dir() and p.name.startswith("rolls-")]
    listing = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=S.ROOT,
                             capture_output=True).stdout.decode("utf-8", "replace").split("\0")
    leaked = [p for p in listing if re.search(r"atlas-[0-9a-f]{8}-(submit|status|result)\.json|tomography-bitorder", p)]
    assert leaked == []


def test_each_of_the_six_law_results_is_read_whole_with_its_nine_settings_and_its_layouts(crate, md):
    """Study section 4: nine settings of 4,096 shots each, the all-Z setting laying 1,995 to 2,027 distinct layouts of five
    sites; five of the six wrap a `fetched_at` (the 2026-09-26 results), and the 2026-09-25 one does not."""
    layouts, fetched = [], 0
    rows = results(md)
    assert len(rows) == 6
    for raw in rows:
        data = S.read(crate, raw["@id"])
        parsed = p1_forms.parse_atlas_result(data)
        assert parsed.shots == raw["qro:shots"] == 4096 and len(parsed.settings) == 9
        assert all(s.shots == 4096 and sum(s.counts.values()) == 4096 for s in parsed.settings.values())
        found = p1_decode.atlas_layouts(parsed, "atlas-register")
        assert sum(found.values()) == 4096 and {len(k) for k in found} == {5}
        layouts.append(len(found))
        fetched += "fetched_at" in json.loads(data)
        assert set(parsed.observables) and parsed.job
    assert sorted(layouts) == [1995, 1997, 2006, 2020, 2026, 2027] and fetched == 5


def test_each_law_pubs_layouts_are_read_through_the_graph_alone_as_p2_reads_them(crate, md):
    ids = graph(md)
    for pub in (p for p in S.of_type(md, "qro:Pub") if p["qro:role"] == "law"):
        counts = p1_decode.pub_counts(crate, md, pub["@id"])
        job = next(j for j in S.of_type(md, "qro:Job") if {"@id": pub["@id"]} in j["object"])
        raw = next(r["@id"] for r in job["result"] if ids[r["@id"]].get("qro:rawForm"))
        assert sum(counts.values()) == 4096 and counts == p1_decode.atlas_layouts(
            p1_forms.parse_atlas_result(S.read(crate, raw)), "atlas-register")


def test_the_known_answer_vector_holds_under_the_decodes_order_and_fails_under_the_plain_one(crate, md):
    """The one thing that holds Atlas's bit order: 128 Z-basis positions each read the frequency the vector's circuit
    prepares, within four standard deviations (worst |z| 2.15 under the rule; 172.96 in plain circuit order)."""
    vector = p1_forms.parse_atlas_vector(S.read(crate, "vectors/tomography-bitorder-2026-09-25.json"))
    right = p1_decode.atlas_vector_verdict(vector, "atlas-register")
    wrong = p1_decode.atlas_vector_verdict(vector, "circuit-order")
    assert right.holds and right.compared == 128 and not right.failed
    assert Fraction(2) ** 2 < right.worst < Fraction(5)                   # |z| = 2.15, z squared 4.6
    assert not wrong.holds and wrong.compared == 128 and len(wrong.failed) == 88
    assert Fraction(172) ** 2 < wrong.worst < Fraction(174) ** 2          # |z| = 172.96
    assert vector.shots == 4096 and vector.job and len(vector.settings) == 9


def test_the_atlas_commitments_are_none_the_kit_commits_are_the_lines_and_the_decodes_name_the_vector(crate, md):
    ids = graph(md)
    lines = {}
    for day in ("2026-09-25", "2026-09-26"):
        lines.update(rec.atlas_lines(S.read(crate, f"{day}/p3/commitments.jsonl"), "commitments.jsonl"))
    assert len(lines) == 6
    pubs = S.of_type(md, "qro:Pub")
    assert {p["qro:commitment"] for p in pubs} == {"none"} and sorted(p["qro:role"] for p in pubs) == ["known-answer"] + ["law"] * 6
    vector_job = next(j for j in S.of_type(md, "qro:Job") if j["qro:jobId"] not in lines)
    assert vector_job["qro:kitCommit"] == "unknown"
    for job in S.of_type(md, "qro:Job"):
        if job["qro:jobId"] in lines:
            line = lines[job["qro:jobId"]]
            assert job["qro:kitCommit"] == line.code_commit and rec.commitment_v2(
                line.stock, line.circuit_sha256, line.engine, line.job_id, line.shots, line.decode,
                line.salt) == line.commitment
        assert (job["startTime"], job["endTime"], job["qro:calibrationLink"]) == ("unknown", "unknown", "unexposed")
    for decode in S.of_type(md, "qro:Decode"):
        assert decode["qro:knownAnswer"] == {"@id": f"#pub-{vector_job['qro:jobId']}-0"}
        assert (decode["qro:decodeRule"], decode["qro:bitOrder"]) == ("quantum_film.atlas.decode/v1", "atlas-register")
    assert ids["#device-moth-atlas-emu"]["qro:deviceKind"] == "simulator"


def test_moths_responses_carry_its_licence_and_the_nineteen_files_that_hold_them_are_those(md):
    moth = [e["@id"] for e in md["@graph"] if e.get("license") == {"@id": "#licence-moth-data"}]
    assert len(moth) == 19 and sum(i.endswith("-submit.json") for i in moth) == 6
    assert sum(i.endswith("-status.json") for i in moth) == 6 and sum(i.endswith("-result.json") for i in moth) == 6
    assert "vectors/tomography-bitorder-2026-09-25.json" in moth
    mit = [e["@id"] for e in md["@graph"] if e.get("license") == {"@id": "LICENSE-quantum-film"}]
    assert len(mit) == 10 and not set(mit) & set(moth)


def test_each_step_visits_every_entity_of_the_atlas_crate_and_the_sweeps_hold(crate, md, monkeypatch):
    seen = S.visited(monkeypatch, ["_pub4", "_decode5", "_job8"])
    for step in (p1_steps.step4, p1_steps.step5, p1_steps.step8):
        step(Path(crate), md)
    for name, t in (("_pub4", "qro:Pub"), ("_decode5", "qro:Decode"), ("_job8", "qro:Job")):
        assert sorted(seen[name]) == [e["@id"] for e in S.of_type(md, t)] and len(seen[name]) == 7, name
    monkeypatch.undo()
    assert S.sweep_pubs(Path(crate), md) == 7
    assert S.sweep_decodes(Path(crate), md) == 7
    assert S.sweep_snapshots_and_jobs(Path(crate), md) == (0, 7)


def test_the_atlas_crate_built_twice_is_one_crate(crate, tmp_path):
    again = S.process(["atlas", "--moth", str(S.MOTH), "--out", str(tmp_path / "again")])
    assert again.returncode == 0 and again.stdout.split()[-1] == S.built("atlas")[1]
