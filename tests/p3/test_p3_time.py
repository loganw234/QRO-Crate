"""Whose difference: the interleaving rule (qro/p3_verdicts.py's `interleaved`; P3's design, item 5, approved with its
two-member floor and its sentence one-device), on the builder's crates: strict alternation within the crate, with two
members a run at least, is the device's; blocks, one member a run, a time unknown, two kinds of time, a tie and members
on different crates are the device's-and-its-time's; one device in both runs is its time's."""
import pytest

import p3_builder as B
import p3_support as S
from qro import canonical, p3_compare
from qro import p3_declaration as D

T = "2026-11-01T10:"


def law_jobs(minutes, ka_minute, start=True):
    out = [B.ka(start=f"{T}{ka_minute:02d}:00Z")]
    for i, m in enumerate(minutes):
        out.append(B.law(f"law-{i}", start=f"{T}{m:02d}:00Z" if start else None,
                         submitted=f"{T}{m:02d}:00Z"))
    return out


def said(tmp_path, k, f, measure="n-crystal-share", two_crates=False):
    if two_crates:
        a = B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", k), B.Bundle("ibm_fez", "morning",
                                                                                [B.ka(start=f"{T}59:00Z")])], "a")
        b = B.build(tmp_path, [B.Bundle("ibm_fez", "morning", f), B.Bundle("ibm_kingston", "morning",
                                                                           [B.ka(start=f"{T}59:00Z")])], "b")
        record, _ = S.computed(a, b, measures=(measure,))
    else:
        crate = B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", k), B.Bundle("ibm_fez", "morning", f)])
        record, _ = S.computed(crate, crate, measures=(measure,))
    words = S.measure(record, measure)["statements"]
    whose = [w for w in words if w in ("device-alone", "device-and-time", "one-device")]
    assert len(whose) == 1, words
    return whose[0]


@pytest.mark.parametrize("k, f, want", [
    ((1, 3), (2, 4), "device-alone"),
    ((2, 4), (1, 3), "device-alone"),
    ((1, 3, 5), (2, 4), "device-alone"),
    ((1, 5), (2, 4), "device-and-time"),
    ((1, 2), (3, 4), "device-and-time"),
    ((1, 3), (2, 4, 6, 8), "device-and-time"),
    ((1,), (2,), "device-and-time"),
    ((1, 3), (2,), "device-and-time"),
    ((1, 3), (3, 5), "device-and-time"),
    ((1, 3), (1, 4), "device-and-time")],
    ids=["a b a b", "b a b a", "a b a b a", "a b b a", "a a b b: blocks", "a b a b b b", "one member each, alternating",
         "one member in b", "a tie at 3", "a tie at 1 across the runs, alternating otherwise"])
def test_strict_alternation_with_two_members_a_run_is_the_devices(tmp_path, k, f, want):
    assert said(tmp_path, law_jobs(k, 0), law_jobs(f, 50)) == want


def test_a_time_unknown_is_not_interleaved(tmp_path):
    """Fez's law jobs state no startTime and have no line to say when they were sent: no time."""
    crate = B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", law_jobs((1, 3), 0)),
                               B.Bundle("ibm_fez", "morning", law_jobs((2, 4), 50))])
    md = S.md_of(crate)
    for e in md["@graph"]:
        if str(e.get("qro:jobId", "")).startswith("ibmfezmorninglaw"):
            e["startTime"] = "unknown"
            del e["qro:line"]
    d = canonical.body_digest(md)
    plan = D.plan({"n-crystal-share": "0/1"}, {"a": {"device": "ibm_kingston"}, "b": {"device": "ibm_fez"}},
                  question="varied")             # with no line, fez's law Pubs' logical circuit is unexposed
    record, _ = p3_compare.compute(D.read(D.write({"a": [d], "b": [d]}, plan)), None, {d: (crate, md)})
    m = S.measure(record, "n-crystal-share")
    assert "device-and-time" in m["statements"] and "date" not in m["unseen"]


def test_two_kinds_of_time_are_not_interleaved(tmp_path):
    """Fez's law jobs timed by their lines' submitted_at, kingston's by their start: alternating, and not one kind."""
    assert said(tmp_path, law_jobs((1, 3), 0), law_jobs((2, 4), 50, start=False)) == "device-and-time"


def test_one_kind_of_time_from_the_lines_alone_interleaves(tmp_path):
    assert said(tmp_path, law_jobs((1, 3), 0, start=False), law_jobs((2, 4), 50, start=False)) == "device-alone"


def test_members_on_different_crates_are_not_interleaved(tmp_path):
    assert said(tmp_path, law_jobs((1, 3), 0), law_jobs((2, 4), 50), two_crates=True) == "device-and-time"


def test_one_device_in_both_runs_is_its_times(tmp_path):
    crate = B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", law_jobs((1, 3), 0)),
                               B.Bundle("ibm_kingston", "sheet-01", law_jobs((2, 4), 50))])
    bundles = sorted({e["sha256"] for e in S.md_of(crate)["@graph"] if e["@id"].endswith("manifest.json")})
    record, _ = S.computed(crate, crate, measures=("n-crystal-share",),
                           runs={"a": {"bundles": [bundles[0]], "device": "ibm_kingston"},
                                 "b": {"bundles": [bundles[1]], "device": "ibm_kingston"}})
    assert "one-device" in S.measure(record, "n-crystal-share")["statements"]


def test_interleaving_is_read_per_measure(tmp_path):
    """The law jobs alternate and the coherence jobs, one a device, do not separate the device from its time."""
    k = law_jobs((1, 3), 0) + [B.coherence(start=f"{T}20:00Z")]
    f = law_jobs((2, 4), 50) + [B.coherence(start=f"{T}21:00Z")]
    crate = B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", k), B.Bundle("ibm_fez", "morning", f)])
    record, _ = S.computed(crate, crate, measures=("n-crystal-share", "x0x1"))
    assert "device-alone" in S.measure(record, "n-crystal-share")["statements"]
    assert "device-and-time" in S.measure(record, "x0x1")["statements"]
