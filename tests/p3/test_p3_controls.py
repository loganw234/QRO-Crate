"""P3's controls (controls/plants_p3.py; study QRO-0, section 11; P3's design, item 9, with its correction 1), through
the controls' runner's protocol (controls/run.py; FORMAT.md item 24): each built row comes out as section 11 says, by
the refusal's own name; `readout-unbounded` is planted, says its sentence, and is pending until P3.2 gives its twin; and
T2, the twin's re-identified copy, shares with the twin exactly its morning known-answer job and no member, and is
accepted by the whole checker. And the joint-omission's two tests besides its plant (the design's item 8)."""
import json
from fractions import Fraction

import pytest

import p3_support as S
from controls import plants_p1, plants_p3
from controls import registry as R
from controls import run as RUN
from qro import canonical, checker, p3_compare
from qro.p1_graph import Index
from qro.refusal import Refused


@pytest.fixture(autouse=True)
def once(monkeypatch):
    """Each crate's nine steps run once in the process, by its files' bytes: these tests are of the comparison."""
    S.fast_checks(monkeypatch)


@pytest.mark.parametrize("name", ["self-compare", "resealed-compare", "shared-control", "joint-omission"])
def test_each_built_row_comes_out_as_section_11_says(name):
    c = R.CONTROL[name]
    got = RUN.outcome(name)
    assert got[:2] == (c.expected, c.refusal), (S.mask(got[2]), c.text)


def test_the_self_comparison_and_the_resealed_one_are_trivial_by_the_same_job_id():
    for name in ("self-compare", "resealed-compare"):
        got = RUN.outcome(name)
        assert got[0:2] == ("refused", "comparison-trivial") and got[2].endswith(": the same job id"), S.mask(got[2])


def test_readout_unbounded_is_planted_says_its_sentence_and_is_pending_without_its_twin(tmp_path):
    c = R.CONTROL["readout-unbounded"]
    planted = plants_p3.readout_unbounded(tmp_path)
    assert isinstance(planted, R.Compared)
    assert R.sentence(c) in plants_p3.STATEMENTS["readout-unbounded"](planted)
    assert RUN.pending_reason(c, R.plants(), R.statements(), R.twins()) == \
        "its plants module has no TWINS entry for it"
    assert "readout-unbounded" not in R.twins()


def test_the_plants_say_only_of_the_measures_they_name(tmp_path):
    planted = plants_p3.readout_unbounded(tmp_path)
    assert plants_p3.said_of(planted, measures=("n-crystal-share",)) == frozenset()


@pytest.fixture(scope="module")
def twins(tmp_path_factory):
    d = tmp_path_factory.mktemp("twins")
    return plants_p1.twin_crate(d / "t"), plants_p3.t2_crate(d / "t2")


def jobs(crate):
    md = S.md_of(crate)
    idx = Index(md)
    out = {}
    for j in idx.of_type("qro:Job"):
        pubs = idx.pubs_of(j)
        out[j["@id"]] = {"id": j["qro:jobId"], "raw": idx.raw_of(j)["sha256"],
                         "commitments": {p["qro:commitment"] for p in pubs}, "roles": {p["qro:role"] for p in pubs},
                         "start": j["startTime"], "line": j["qro:line"]["@id"]}
    return out


def test_t2_shares_its_known_answer_jobs_whole_with_the_twin_and_nothing_else(twins):
    """The morning known answer, which the shared-control comparison's two runs both select, and the two sheets'."""
    t, t2 = (jobs(c) for c in twins)
    shared = []
    for a in t.values():
        for b in t2.values():
            if a["id"] == b["id"] or a["raw"] == b["raw"] or a["commitments"] & b["commitments"]:
                shared.append((a, b))
    assert len(shared) == 3 and all(a == b and a["roles"] == {"known-answer"} for a, b in shared)
    assert sum(1 for a, _ in shared if a["line"] == f"{plants_p1.MORNING_RUN}/known-answer-line.json") == 1
    coherence = [a for a in t.values() if a["roles"] == {"coherence"}]
    coherence2 = [b for b in t2.values() if b["roles"] == {"coherence"}]
    assert len(coherence) == len(coherence2) == 1
    a, b = coherence[0], coherence2[0]
    assert a["id"] != b["id"] and a["raw"] != b["raw"] and not a["commitments"] & b["commitments"]
    assert a["start"] == b["start"], "it ran when the twin's ran: only its identities are new"
    assert {x["roles"] == {"coherence"} for x, _ in shared} == {False}, "no member is shared"


def test_t2_is_accepted_by_the_whole_checker_and_is_another_crate(twins):
    t, t2 = twins
    checker.load()
    md = checker.check(t2)
    assert canonical.body_digest(md) != canonical.body_digest(checker.check(t))


def test_the_comparison_of_the_twin_and_t2_reads_t2s_own_bytes(twins, tmp_path):
    """x0x1's moved shot flipped qubit 0, so T2's value is one shot from the twin's; y0y1's is the twin's."""
    t, t2 = twins
    out = tmp_path / "comparison"
    p3_compare.make(plants_p3.declaration(t, t2), out, [t, t2])
    record = json.loads((out / "comparison" / "record.json").read_bytes())
    xx, yy = S.measure(record, "x0x1"), S.measure(record, "y0y1")
    assert abs(Fraction(xx["a"]["value"]) - Fraction(xx["b"]["value"])) == Fraction(2, 4096)
    assert yy["a"]["value"] == yy["b"]["value"]
    assert record["family"] == 4 and {m["means"] for m in record["measures"]} == {"unresolved"}
    for m in (xx, yy):
        assert m["statements"] == ["drift-unmeasured", "commit-unknown", "one-device", "quantum-unpiped",
                                   "readout-unbounded"]
        assert m["causes"]["compile"] == "EQUAL" and m["causes"]["device"] == "EQUAL"


# -- joint-omission: its plant, and the design's two tests besides it ----------------------------------------------
def test_joint_omissions_plant_offers_per_cause_checks_and_a_composed_verdict_where_the_data_give_none(tmp_path):
    planted = plants_p3.joint_omission(tmp_path)
    record = json.loads((tmp_path / "comparison" / "comparison" / "record.json").read_bytes())
    xx = S.measure(record, "x0x1")
    assert xx["causeChecks"] == plants_p3.CAUSE_CHECKS and xx["means"] == "agree"
    checker.load()
    checker.check(planted.comparison_dir)               # the nine steps accept the forged comparison crate
    with pytest.raises(Refused) as r:
        p3_compare.check(planted.comparison_dir, planted.crate_dirs)
    assert r.value.name == "comparison-generated" and r.value.where.startswith("comparison/record.json line ")


def test_its_twin_the_record_make_wrote_is_accepted(tmp_path):
    out, t, t2 = plants_p3.made(tmp_path, epsilon="1/20")
    record = json.loads((out / "comparison" / "record.json").read_bytes())
    assert S.measure(record, "x0x1")["means"] == "unresolved", "the data give no verdict at epsilon 1/20"
    assert str(p3_compare.check(out, [t, t2])).startswith("ACCEPTED comparison ")


@pytest.mark.parametrize("edit", [lambda m: m.update(causeChecks=plants_p3.CAUSE_CHECKS),
                                  lambda m: m.update(means="agree")],
                         ids=["the per-cause field beside the data's own verdict", "the composed verdict alone"])
def test_each_half_of_the_omission_alone_is_refused(tmp_path, edit):
    out, t, t2 = plants_p3.made(tmp_path, epsilon="1/20")
    plants_p3.tamper(out, lambda m: edit(m) if m["measure"] == "x0x1" else None)
    with pytest.raises(Refused) as r:
        p3_compare.check(out, [t, t2])
    assert r.value.name == "comparison-generated"


def test_a_p3_plant_goes_through_the_plant_command_as_a_process():
    """The plant command hands a Compared to `python -m qro compare` and writes its verdict (here a refusal, the
    cheaper; an accepted comparison through that command as a process is test_p3_cli's)."""
    p = S.process(["self-compare"], module="controls.plant")
    assert p.returncode == 1, (S.mask(p.stdout[-300:]), S.mask(p.stderr[-300:]))
    assert p.stdout.count("\n") == 1 and p.stdout.startswith("REFUSED comparison-trivial at run a ")


def test_p3s_rows_and_plants_join_the_registrys():
    assert {c.name for c in R.CONTROLS if c.owner == "P3"} >= set(plants_p3.PLANTS)
    assert set(plants_p3.PLANTS) <= set(R.plants())
    assert R.CONTROL["joint-omission"].refusal == "comparison-generated"
