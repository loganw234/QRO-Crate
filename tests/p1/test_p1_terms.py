"""Every CHECKED term of P1's is checked on every entity its domain admits (CLAUDE.md; the bar). Registering a step
turns `step-unbuilt` off for its terms, so from then on only P1's step stands between a crate and an unchecked value.

This test walks the vocabulary, never a list kept here: for each term of owner P1 and kind CHECKED, and each type its
domain admits, a fault must be planted below, and every planted fault is run and must be refused by the step the
table gives that term, under the refusal name that step owns. A CHECKED term added to the table fails here until it
has its plant; a plant for a term the table does not have fails too. The plants are few and plain: each is a claim
the crate makes that its own files contradict. The per-entity sweeps, the boundaries and the hostile matrices are in
the step tests; this holds the registry."""
import pytest
from p1_builder import SNAPS, atlas_model, ibm_model, judge, snapshot_path

from qro import checker
from qro import vocabulary as V
from qro.p1_graph import types_of

STEP_REFUSAL = {4: "commitment", 5: "known-answer", 8: "calibration-link"}
BAD_DIGEST, BAD_TIME = "0" * 64, "2026-10-05T00:00:00Z"
S0657, S0902, S1128 = (snapshot_path(SNAPS[k][0]) for k in ("s0657", "s0902", "s1128"))


def claim(entity, term, value):
    def plant(m):
        m.ents[entity][term] = value
    return plant


def drop(entity, term):
    def plant(m):
        m.ents[entity].pop(term)
    return plant


PLANTS = {
    ("qro:commitment", "qro:Pub"): [claim("#pub-jobka-0", "qro:commitment", BAD_DIGEST),
                                    drop("#pub-jobka-0", "qro:commitment")],
    ("qro:decodeRule", "qro:Decode"): [claim("#decode-jobcoh", "qro:decodeRule", "quantum_film.ibm.decode/v2"),
                                       drop("#decode-jobcoh", "qro:decodeRule")],
    ("qro:knownAnswer", "qro:Decode"): [claim("#decode-jobcoh", "qro:knownAnswer", {"@id": "#pub-joblaw-0"}),
                                        drop("#decode-jobcoh", "qro:knownAnswer")],
    ("qro:calibrationLink", "qro:Job"): [claim("#job-jobka", "qro:calibrationLink", "history-in-gap"),
                                         drop("#job-jobka", "qro:calibrationLink")],
    ("qro:calibration", "qro:Job"): [claim("#job-joblaw", "qro:calibration", [{"@id": S1128}]),
                                     claim("#job-jobka", "qro:calibration", [{"@id": S0657}, {"@id": S0902}])],
    ("qro:valuesDigest", "qro:Snapshot"): [claim(S1128, "qro:valuesDigest", BAD_DIGEST),
                                           drop(S1128, "qro:valuesDigest")],
    ("qro:stamp", "qro:Snapshot"): [claim(S1128, "qro:stamp", BAD_TIME), drop(S1128, "qro:stamp")],
    ("qro:newestValue", "qro:Snapshot"): [claim(S1128, "qro:newestValue", BAD_TIME), drop(S1128, "qro:newestValue")],
}


def checked_terms():
    """(term, the types its domain admits) for each CHECKED term of P1's, from the vocabulary."""
    return [(t, [d for d in t.domain if d in V.TYPE]) for t in V.TERMS if t.owner == "P1" and t.kind == "CHECKED"]


def test_the_vocabulary_has_checked_terms_of_p1s_on_one_type_each_at_steps_4_5_and_8():
    terms = checked_terms()
    assert terms and {t.step for t, _ in terms} == {4, 5, 8}
    assert all(len(types) == 1 and types == list(t.domain) for t, types in terms), \
        "a CHECKED term stands on one type, every entity of which its step visits"


def test_every_checked_term_of_p1s_has_a_plant_on_every_type_of_its_domain_and_no_plant_is_for_another():
    want = {(t.key, d) for t, types in checked_terms() for d in types}
    assert want == set(PLANTS), sorted(want ^ set(PLANTS))


def test_the_steps_p1_registers_are_the_steps_of_those_terms_and_the_vocabulary_gives_them_to_p1():
    from qro import register_p1
    owners = checker.step_owners()
    steps = {t.step for t, _ in checked_terms()}
    assert {n for n, o in owners.items() if o == "P1"} == steps == set(register_p1.STEPS)
    assert {n: V.REFUSAL[STEP_REFUSAL[n]].owner for n in steps} == {n: "P1" for n in steps}


@pytest.mark.parametrize("key, type", sorted(PLANTS), ids=lambda x: str(x))
def test_each_planted_fault_is_refused_by_its_steps_own_name(tmp_path, key, type):
    step = V.TERM[key].step
    assert type in V.TERM[key].domain
    for i, plant in enumerate(PLANTS[(key, type)]):
        m = ibm_model()
        plant(m)
        r = judge(m, tmp_path / str(i), step)
        assert r is not None, f"{key}: plant {i} was accepted"
        assert r.name == STEP_REFUSAL[step] or (key, r.name) == ("qro:decodeRule", "step-unbuilt"), \
            f"{key}: plant {i} was refused {r.name} at {r.where}: {r.detail}"


def test_the_honest_crates_carry_each_checked_term_on_the_type_its_domain_admits(tmp_path):
    """So the plants plant into entities that carry the term: the small IBM crate holds every one."""
    md = ibm_model().md()
    seen = {(k, t) for e in md["@graph"] for k in e if k in V.TERM and V.TERM[k].owner == "P1"
            and V.TERM[k].kind == "CHECKED" for t in types_of(e)}
    assert {(k, t) for (k, t) in seen if t in V.TERM[k].domain} == set(PLANTS)
    assert judge(ibm_model(), tmp_path / "ibm", 4) is None
    atlas = atlas_model().md()
    assert {k for e in atlas["@graph"] for k in e if k in V.TERM and V.TERM[k].kind == "CHECKED"
            and V.TERM[k].owner == "P1"} >= {"qro:commitment", "qro:decodeRule", "qro:knownAnswer",
                                             "qro:calibrationLink"}
