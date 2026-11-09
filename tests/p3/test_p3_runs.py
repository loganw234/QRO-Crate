"""What a comparison reads of a crate, and what its selectors select (qro/p3_runs.py; P3's design, item 2), on the
builder's crates: selection by each key of a selector; a job's time, its startTime else its line's submitted_at, and a
job with neither in no window; members by role and basis, and a control job selected and no member."""
from pathlib import Path

import pytest

import p3_builder as B
import p3_support as S
from qro import p3_declaration as D
from qro import p3_runs as R
from qro.p1_forms import parse_time


@pytest.fixture(scope="module")
def crate(tmp_path_factory):
    d = tmp_path_factory.mktemp("runs")
    k = B.Bundle("ibm_kingston", "morning", [
        B.ka(start="2026-11-01T10:00:00Z"), B.law(start="2026-11-01T10:01:00Z"),
        B.law("law-late", start=None, submitted="2026-11-01T12:00:00Z"), B.coherence(start="2026-11-01T10:05:00Z")])
    k2 = B.Bundle("ibm_kingston", "sheet-01", [B.ka(start="2026-11-01T11:00:00Z"), B.law(start="2026-11-01T11:01:00Z")])
    f = B.Bundle("ibm_fez", "morning", [B.ka(start="2026-11-01T10:00:30Z"), B.law(start="2026-11-01T10:02:00Z")])
    path = B.build(d, [k, k2, f])
    return R.read(path, S.md_of(path), S.digest_of(path))


def ids(jobs):
    return sorted(j.id for j in jobs)


def sel(**kw):
    return D.Selector(kw.pop("device", "ibm_kingston"), kw.pop("bundles", None), kw.pop("jobs", None),
                      parse_time(kw["start"]) if kw.get("start") else None,
                      parse_time(kw["until"]) if kw.get("until") else None)


def test_a_device_alone_selects_every_job_of_that_device(crate):
    assert ids(R.selected(crate, sel())) == ["ibmkingstonmorningcoherence", "ibmkingstonmorningknownanswer",
                                             "ibmkingstonmorninglaw", "ibmkingstonmorninglawlate",
                                             "ibmkingstonsheet01knownanswer", "ibmkingstonsheet01law"]
    assert ids(R.selected(crate, sel(device="ibm_fez"))) == ["ibmfezmorningknownanswer", "ibmfezmorninglaw"]
    assert R.selected(crate, sel(device="ibm_marrakesh")) == ()


def test_bundles_select_by_the_lines_bundle_digest(crate):
    sheet = next(j.bundle for j in crate.jobs if j.id == "ibmkingstonsheet01law")
    assert ids(R.selected(crate, sel(bundles=(sheet,)))) == ["ibmkingstonsheet01knownanswer", "ibmkingstonsheet01law"]
    fez = next(j.bundle for j in crate.jobs if j.id == "ibmfezmorninglaw")
    assert R.selected(crate, sel(bundles=(fez,))) == (), "fez's bundle holds no job of kingston"


def test_jobs_select_by_job_id(crate):
    assert ids(R.selected(crate, sel(jobs=("ibmkingstonmorninglaw", "ibmfezmorninglaw")))) == ["ibmkingstonmorninglaw"]


def test_a_window_selects_by_time_from_inclusive_until_exclusive(crate):
    got = R.selected(crate, sel(start="2026-11-01T10:01:00Z", until="2026-11-01T11:00:00Z"))
    assert ids(got) == ["ibmkingstonmorningcoherence", "ibmkingstonmorninglaw"]


def test_a_jobs_time_is_its_start_else_its_lines_submitted_at(crate):
    by = {j.id: j for j in crate.jobs}
    assert (by["ibmkingstonmorninglaw"].time, by["ibmkingstonmorninglaw"].clock) == (
        parse_time("2026-11-01T10:01:00Z"), R.START)
    late = by["ibmkingstonmorninglawlate"]
    assert (late.time, late.clock) == (parse_time("2026-11-01T12:00:00Z"), R.SUBMITTED)
    assert ids(R.selected(crate, sel(start="2026-11-01T11:30:00Z"))) == ["ibmkingstonmorninglawlate"]


def test_a_job_with_no_time_is_in_no_window_and_selected_without_one(tmp_path):
    """A Job whose startTime is unknown and that has no line (Atlas's shape) has no time."""
    path = B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", [B.ka(start="2026-11-01T10:00:00Z"), B.law()])])
    md = S.md_of(path)
    for e in md["@graph"]:
        if e.get("qro:jobId") == "ibmkingstonmorninglaw":
            del e["qro:line"]
    crate = R.read(path, md, "x" * 64)
    law = next(j for j in crate.jobs if j.id == "ibmkingstonmorninglaw")
    assert (law.time, law.clock, law.bundle, law.manifest) == (None, None, None, None)
    assert all(p.circuit is None for p in law.pubs), "with no line, no manifest circuit: unexposed"
    assert ids(R.selected(crate, sel(start="2000-01-01T00:00:00Z"))) == ["ibmkingstonmorningknownanswer"]
    assert ids(R.selected(crate, sel())) == ["ibmkingstonmorningknownanswer", "ibmkingstonmorninglaw"]


def test_members_are_the_selected_jobs_holding_a_pub_the_measure_reads(crate):
    jobs = R.selected(crate, sel())
    assert ids(j for j, _ in R.members(jobs, "n-crystal-share")) == [
        "ibmkingstonmorninglaw", "ibmkingstonmorninglawlate", "ibmkingstonsheet01law"]
    xx = R.members(jobs, "x0x1")
    assert ids(j for j, _ in xx) == ["ibmkingstonmorningcoherence"]
    assert [p.basis for p in xx[0][1]] == ["XXZZZZZZZZZZZZZZ"]
    assert [p.basis for p in R.members(jobs, "y0y1")[0][1]] == ["YYZZZZZZZZZZZZZZ"]
    controls = [j for j in jobs if all(p.role == "known-answer" for p in j.pubs)]
    assert controls and not any(j in [m for m, _ in R.members(jobs, m)] for j in controls for m in S.FIVE)


@pytest.mark.parametrize("role, basis, measure, reads", [
    ("coherence", "XXZZ", "x0x1", True), ("coherence", "YYZZ", "y0y1", True), ("coherence", "XXZZ", "y0y1", False),
    ("coherence", "ZXXZ", "x0x1", False), ("coherence", "XYZZ", "x0x1", False), ("coherence", "XXXZ", "x0x1", False),
    ("coherence", "ZZZZ", "x0x1", False), ("coherence", None, "x0x1", False), ("law", "XXZZ", "x0x1", False),
    ("law", "ZZZZ", "n-crystal-share", True), ("coherence", "XXZZ", "n-crystal-share", False),
    ("known-answer", "ZZZZ", "forbidden-share", False)])
def test_a_measure_reads_a_pub_by_its_role_and_basis(role, basis, measure, reads):
    pub = R.Pub("#p-0", {}, role, basis, "none", None, None, None)
    assert R.reads(pub, measure) is reads


def test_each_pub_is_mapped_to_its_manifest_circuit_by_its_commitment(crate):
    for job in crate.jobs:
        for p in job.pubs:
            assert p.circuit is not None and p.circuit.commitment == p.commitment
            assert p.circuit.role == p.role and p.circuit.basis == p.basis
    assert all(j.held for j in crate.jobs), "each bundle's Compile has P2's Hold"


def test_a_held_compiles_manifest_is_read_by_p2s_own_manifest_of(crate, monkeypatch):
    """One place for P2's rule (round 2, item 2): each Compile a Hold names has its manifest read by
    qro.p2_measures.manifest_of, called once for each, and a job is held where its line's bundle is one of them."""
    from qro import p2_measures
    real, seen = p2_measures.manifest_of, []

    def spy(idx, compile_entity):
        seen.append(compile_entity["@id"])
        return real(idx, compile_entity)
    monkeypatch.setattr(p2_measures, "manifest_of", spy)
    again = R.read(crate.directory, crate.md, crate.digest)
    compiles = sorted(e["@id"] for e in again.index.of_type("qro:Compile"))
    assert sorted(seen) == compiles == ["#compile-ibm_fez-morning", "#compile-ibm_kingston-morning",
                                        "#compile-ibm_kingston-sheet-01"]
    manifests = {real(again.index, c)["sha256"] for c in again.index.of_type("qro:Compile")}
    assert len(manifests) == 3 and all(j.held is (j.bundle in manifests) for j in again.jobs)


def test_a_crate_holding_no_hold_has_no_held_manifest(tmp_path):
    path = B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", [B.ka(), B.law()], held=False)])
    crate = R.read(path, S.md_of(path), "x" * 64)
    assert not any(j.held for j in crate.jobs)


def test_the_jobs_on_a_device_are_ordered_by_time_only_where_they_can_be(crate, tmp_path):
    ordered = R.on_device(crate, "ibm_fez")
    assert [j.id for j in ordered] == ["ibmfezmorningknownanswer", "ibmfezmorninglaw"]
    assert R.on_device(crate, "ibm_kingston") is None, "one of kingston's jobs is timed by its line: two kinds"
    tie = B.build(tmp_path, [B.Bundle("ibm_fez", "morning", [B.ka(start="2026-11-01T10:00:00Z"),
                                                              B.law(start="2026-11-01T10:00:00Z")])])
    assert R.on_device(R.read(tie, S.md_of(tie), "x" * 64), "ibm_fez") is None, "a tie orders nothing"
    assert R.on_device(crate, "ibm_marrakesh") is None


def test_reading_a_crate_reads_no_count(crate, monkeypatch):
    """What the runs read is structure: no raw result is parsed, so no count is read."""
    from qro import p1_decode, p1_forms

    def poisoned(*a, **k):
        raise AssertionError("a count was read")
    monkeypatch.setattr(p1_forms, "parse_raw", poisoned)
    monkeypatch.setattr(p1_decode, "pub_counts", poisoned)
    again = R.read(crate.directory, crate.md, crate.digest)
    assert [j.id for j in again.jobs] == [j.id for j in crate.jobs]
    assert Path(again.directory) == Path(crate.directory)
