"""P1's steps swept over every entity of the twin that they check (P1's design, item 10: "a plant per CHECKED term per entity
type in its domain", and in `p1-crates` "swept over every entity of the type ... at the level of the step's per-entity
function, which kills a step that visits only some"). Two sweeps, on the twin here and on both real crates in the p1-crates
stage:
  - every entity of a type the step checks is visited, by the step as the checker runs it;
  - each entity, taken alone through the step's own per-entity function, is accepted as it is, and refused at itself,
    by the step's name, once its CHECKED claim is false.
The per-entity functions are P1.1's (`_pub4`, `_decode5`, `_snapshot8`, `_job8`): a step that checked only some of its
entities would pass the first sweep's honest crate and fail its visits."""
from datetime import timedelta

import pytest

from p1_support import twin_copy
from qro import canonical, checker, p1_forms, p1_steps, reader, spelling
from qro.p1_graph import Index
from qro.refusal import Refused


@pytest.fixture(scope="module")
def twin(tmp_path_factory):
    crate = twin_copy(tmp_path_factory.mktemp("sweep"))
    checker.load()
    return crate, reader.read((crate / canonical.DESCRIPTOR).read_bytes())


def visited(monkeypatch, names):
    """The ids each per-entity function of p1_steps is called with, recorded as the step calls them."""
    seen = {n: [] for n in names}
    for n in names:
        real = getattr(p1_steps, n)

        def wrapper(*args, _real=real, _n=n):
            seen[_n].append(args[-1]["@id"])
            return _real(*args)
        monkeypatch.setattr(p1_steps, n, wrapper)
    return seen


def ids_of(md, t):
    return sorted(e["@id"] for e in md["@graph"] if t in canonical.types(e))


def test_each_step_visits_every_entity_of_the_type_it_checks(twin, monkeypatch):
    crate, md = twin
    seen = visited(monkeypatch, ["_pub4", "_decode5", "_snapshot8", "_job8"])
    for step in (p1_steps.step4, p1_steps.step5, p1_steps.step8):
        step(crate, md)
    assert sorted(seen["_pub4"]) == ids_of(md, "qro:Pub") and len(seen["_pub4"]) == 5
    assert sorted(seen["_decode5"]) == ids_of(md, "qro:Decode") and len(seen["_decode5"]) == 4
    assert sorted(seen["_snapshot8"]) == ids_of(md, "qro:Snapshot") and len(seen["_snapshot8"]) == 3
    assert sorted(seen["_job8"]) == ids_of(md, "qro:Job") and len(seen["_job8"]) == 4


def test_the_snapshots_are_visited_before_any_job_and_each_in_id_order(twin, monkeypatch):
    crate, md = twin
    order = []
    for n in ("_snapshot8", "_job8"):
        real = getattr(p1_steps, n)

        def wrapper(*args, _real=real, _n=n):
            order.append((_n, args[-1]["@id"]))
            return _real(*args)
        monkeypatch.setattr(p1_steps, n, wrapper)
    p1_steps.step8(crate, md)
    kinds = [k for k, _ in order]
    assert kinds == ["_snapshot8"] * 3 + ["_job8"] * 4
    assert [i for k, i in order if k == "_job8"] == sorted(i for k, i in order if k == "_job8")


def other_digest(d):
    return ("0" if d[0] != "0" else "1") + d[1:]


def sweep_pubs(crate, md):
    idx, facts, lines, listings = Index(md), {}, {}, {}
    pubs = sorted(idx.of_type("qro:Pub"), key=lambda e: e["@id"])
    for pub in pubs:
        p1_steps._pub4(crate, idx, facts, lines, listings, pub)                      # as it is: accepted
        flipped = dict(pub, **{"qro:commitment": other_digest(pub["qro:commitment"])})
        with pytest.raises(Refused) as x:
            p1_steps._pub4(crate, idx, facts, lines, listings, flipped)
        assert (x.value.name, x.value.where) == ("commitment", f"{pub['@id']} qro:commitment"), pub["@id"]
        missing = {k: v for k, v in pub.items() if k != "qro:commitment"}
        with pytest.raises(Refused) as x:
            p1_steps._pub4(crate, idx, facts, lines, listings, missing)
        assert (x.value.name, x.value.where) == ("commitment", f"{pub['@id']} qro:commitment"), pub["@id"]
    return len(pubs)


MIRROR = {"msb-first": "lsb-first", "atlas-register": "circuit-order"}


def sweep_decodes(crate, md):
    idx, verdicts = Index(md), {}
    decodes = sorted(idx.of_type("qro:Decode"), key=lambda e: e["@id"])
    for d in decodes:
        p1_steps._decode5(crate, idx, verdicts, d)
        mirrored = dict(d, **{"qro:bitOrder": MIRROR[d["qro:bitOrder"]]})
        with pytest.raises(Refused) as x:
            p1_steps._decode5(crate, idx, verdicts, mirrored)
        assert x.value.name == "known-answer" and x.value.where.startswith(d["@id"] + " "), d["@id"]
        elsewhere = dict(d, **{"qro:knownAnswer": {"@id": next(p["@id"] for p in idx.of_type("qro:Pub")
                                                             if p.get("qro:role") != "known-answer")}})
        with pytest.raises(Refused) as x:
            p1_steps._decode5(crate, idx, verdicts, elsewhere)
        assert (x.value.name, x.value.where) == ("known-answer", f"{d['@id']} qro:knownAnswer"), d["@id"]
    return len(decodes)


def sweep_snapshots_and_jobs(crate, md):
    idx, snaps, by_name = Index(md), {}, {}
    snapshots = sorted(idx.of_type("qro:Snapshot"), key=lambda e: e["@id"])
    for e in snapshots:
        p1_steps._snapshot8(crate, idx, snaps, by_name, e)
        for term in ("qro:valuesDigest", "qro:stamp", "qro:newestValue"):
            wrong = dict(e, **{term: other_digest(e[term]) if term == "qro:valuesDigest" else "2000-01-01T00:00:00Z"})
            with pytest.raises(Refused) as x:
                p1_steps._snapshot8(crate, idx, {}, {}, wrong)
            assert (x.value.name, x.value.where) == ("calibration-link", f"{e['@id']} {term}"), (e["@id"], term)
    jobs = sorted(idx.of_type("qro:Job"), key=lambda e: e["@id"])
    for job in jobs:
        p1_steps._job8(crate, idx, snaps, by_name, job)
        words = {"history-at-first-shot": "history-in-gap", "history-in-gap": "history-at-first-shot", "unexposed": "history-at-first-shot",
                 "unknown": "history-at-first-shot"}
        wrong = dict(job, **{"qro:calibrationLink": words[job["qro:calibrationLink"]]})
        with pytest.raises(Refused) as x:
            p1_steps._job8(crate, idx, snaps, by_name, wrong)
        assert x.value.name == "calibration-link" and x.value.where.startswith(job["@id"] + " "), job["@id"]
        if job["startTime"] != "unknown":
            later = dict(job, startTime=spelling.time(p1_forms.parse_time(job["startTime"], "Z") + timedelta(microseconds=1)))
            with pytest.raises(Refused) as x:
                p1_steps._job8(crate, idx, snaps, by_name, later)
            assert (x.value.name, x.value.where) == ("calibration-link", f"{job['@id']} startTime")
    return len(snapshots), len(jobs)


def test_every_pub_of_the_twin_is_accepted_and_refused_at_itself_once_its_claim_is_false(twin):
    assert sweep_pubs(*twin) == 5


def test_every_decode_of_the_twin_is_accepted_and_refused_at_itself_once_its_order_or_its_known_answer_is_false(twin):
    assert sweep_decodes(*twin) == 4


def test_every_snapshot_and_job_of_the_twin_is_accepted_and_refused_at_itself_once_a_claim_is_false(twin):
    assert sweep_snapshots_and_jobs(*twin) == (3, 4)


def test_the_sweep_is_not_vacuous_a_step_that_visited_only_the_first_entity_would_fail_the_visits(twin, monkeypatch):
    """The control of the sweep: step 4 made to stop after its first Pub is seen not to visit the other four."""
    crate, md = twin
    seen = visited(monkeypatch, ["_pub4"])

    def first_only(idx, type_, step, refuse):
        first = sorted(idx.of_type(type_), key=lambda e: e["@id"])[:1]
        for e in first:
            step(e)
    monkeypatch.setattr(p1_steps, "_visit", first_only)
    p1_steps.step4(crate, md)
    assert len(seen["_pub4"]) == 1 != len(ids_of(md, "qro:Pub"))
