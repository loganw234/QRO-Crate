"""The refusals a comparison makes before it computes any value, in the study's order (QRO-0, section 8, items 1 to 5;
P3's design, item 3; P3.1). Standard library and qro only. Each reads structure alone, the graph, the lines, the
manifests and the declaration, and never a count, so each is decided before any value exists.

  1. `comparison-trivial`, the whole comparison: a member job of run a and one of run b share a `qro:jobId`, a PUB
     commitment other than `none`, or a raw result's `sha256`. A member job is a job either run's selector selects that
     holds a Pub a measure of the plan reads (qro.p3_runs.members). `none` is absence and never shared, and nor is a
     term a job does not state. A job both runs share that is no member, a control job, is no refusal
     (`shared-control`). Located "run a <job id> and run b <job id>", the detail "the same job id", "the same
     commitment" or "the same raw result", in that order, the pairs in the order of their job ids.
  2. `question-differs`, the whole comparison:
     - a crate whose question's measure set is not the plan's (no measure can be read in it under the plan: a crate that
       carries none of P2's terms, P0's fixture among them, has none);
     - unless the plan's question is `varied`: the two runs' question digests differ, a run's digest being the
       SHA-256 of canonical compact JSON of {"decodeRules": the sorted distinct decode rules of the Decodes of the
       run's member Pubs, over the measures both runs have members of, "law": the `sha256` of its crate's question's
       `qro:law` File, "lawCircuit": its `qro:lawCircuit` File's, "measureSet", "twins"} (absent parts `none`); or, for
       a measure both runs have members of, its member Pubs ran more than one logical circuit (each manifest circuit's
       `circuit_sha256`, `unexposed` for a Pub with no manifest circuit). The rules are read over the measures both
       runs have, as the circuits are, so that a run lacking a role is refused `role-missing` for it, not
       `question-differs` for the rules its absent members would have named.
     A run takes one crate in this version (qro.p3_declaration.unbuilt), so a run has one digest.
  3. `role-missing`, one measure: a run has no member of it. That measure is refused by name in the record, with the
     runs that lack it, and the comparison goes on; with no measure left the whole comparison is refused.
  4. `kind-not-qpu`, the whole comparison: the plan's kind is `real` and a job either run selects ran on a device whose
     `qro:deviceKind` is not `qpu`. Step 4 holds a device's kind to the commitment's `kind` wherever a commitment
     exists; v0's Atlas crate is `simulator`.
  5. `selector-late`, kept: qro.p3_declaration.late.
And `step-unbuilt`, before the first: a crate that holds a `qro:Unit`, whose left-out rule (P5's `unit-incomplete`,
from qro.p5_unit's status) P3.2 builds; and (qro.p3_readout) a coherence measure whose readout is covered, whose bound
P3.2 builds.
"""
import hashlib

from qro import canonical
from qro.p3_declaration import RUNS
from qro.refusal import Refused


def name(job):
    """A job as a refusal names it: its `qro:jobId`, or its @id where it states none."""
    return job.id if job.id is not None else job.entity["@id"]


def member_jobs(members, side):
    """The jobs of a run that are members of any measure, each once, in the order of their names."""
    seen = {}
    for by_side in members.values():
        for job, _ in by_side[side]:
            seen.setdefault((job.crate, job.entity["@id"]), job)
    return sorted(seen.values(), key=lambda j: (name(j), j.crate, j.entity["@id"]))


def _commitments(job):
    return {p.commitment for p in job.pubs if isinstance(p.commitment, str) and p.commitment != "none"}


def units(runs):
    """`step-unbuilt` for a crate a run takes that holds a qro:Unit."""
    for side in RUNS:
        for crate in runs[side].crates:
            if crate.units:
                raise Refused("step-unbuilt", f"run {side} crate {crate.digest}",
                              "a crate holding a qro:Unit: the unit's left-out rule (P5's unit-incomplete, from its "
                              "status) is not built yet (P3.2's)")


def trivial(members):
    """`comparison-trivial` where a member job of run a and one of run b share a job id, a commitment or a raw result."""
    b_jobs = member_jobs(members, "b")
    for ja in member_jobs(members, "a"):
        for jb in b_jobs:
            where = f"run a {name(ja)} and run b {name(jb)}"
            if ja.id is not None and ja.id == jb.id:
                raise Refused("comparison-trivial", where, "the same job id")
            if _commitments(ja) & _commitments(jb):
                raise Refused("comparison-trivial", where, "the same commitment")
            if ja.raw is not None and ja.raw == jb.raw:
                raise Refused("comparison-trivial", where, "the same raw result")


def question_digest(crate, member_pubs):
    """A crate's question digest, over its member Pubs' Decodes' rules."""
    rules = sorted({p.rule for p in member_pubs if isinstance(p.rule, str)})
    q = crate.question
    return hashlib.sha256(canonical.compact({"decodeRules": rules, "law": q["law"], "lawCircuit": q["lawCircuit"],
                                             "measureSet": q["measureSet"], "twins": q["twins"]})).hexdigest()


def circuit_of(pub):
    """The logical circuit a member Pub ran: its manifest circuit's circuit_sha256, or `unexposed`."""
    return pub.circuit.circuit_sha256 if pub.circuit is not None else "unexposed"


def question(runs, members, plan):
    """({side: its question digest}, {measure: EQUAL or DIFFERS}), or `question-differs`."""
    for side in RUNS:
        for crate in runs[side].crates:
            if crate.question["measureSet"] != plan.measure_set:
                raise Refused("question-differs", f"run {side} crate {crate.digest}",
                              f"its question's measure set is {crate.question['measureSet']}, and the plan's is "
                              f"{plan.measure_set}: no measure of the plan can be read in it")
    shared = [m for m, by_side in members.items() if by_side["a"] and by_side["b"]]
    digests = {}
    for side in RUNS:
        crate = runs[side].crates[0]
        pubs = [p for m in shared for _, ps in members[m][side] for p in ps]
        digests[side] = question_digest(crate, pubs)
    varied = plan.question == "varied"
    if digests["a"] != digests["b"] and not varied:
        raise Refused("question-differs", "the question",
                      f"run a asks the question {digests['a']}, and run b {digests['b']}; the plan's question is fixed")
    status = {}
    for measure, by_side in sorted(members.items()):
        if not (by_side["a"] and by_side["b"]):
            continue
        circuits = {circuit_of(p) for side in RUNS for _, ps in by_side[side] for p in ps}
        if len(circuits) > 1 and not varied:
            raise Refused("question-differs", measure,
                          f"its member Pubs ran {len(circuits)} logical circuits, and the plan's question is fixed")
        status[measure] = "EQUAL" if digests["a"] == digests["b"] and len(circuits) == 1 else "DIFFERS"
    return digests, status


def role_missing(members, plan):
    """{measure: the runs that have no member of it}, for each measure so refused; `role-missing`, the whole
    comparison, where every measure of the plan is."""
    refused = {m.measure: [side for side in RUNS if not members[m.measure][side]] for m in plan.measures}
    refused = {m: sides for m, sides in refused.items() if sides}
    if len(refused) == len(plan.measures):
        raise Refused("role-missing", "the plan's measures",
                      "; ".join(f"{m}: run {' and run '.join(sides)} has no member" for m, sides in sorted(refused.items())))
    return refused


def kind(runs, plan):
    """`kind-not-qpu` where the plan is real and a job a run selects ran on a device that is not a qpu."""
    if plan.kind != "real":
        return
    for side in RUNS:
        for job in sorted(runs[side].jobs, key=lambda j: (name(j), j.crate, j.entity["@id"])):
            if job.kind != "qpu":
                kind_ = f"of the kind {job.kind}" if job.kind is not None else "of no stated kind"
                raise Refused("kind-not-qpu", f"run {side} {name(job)}",
                              f"its device {job.device} is {kind_}, not qpu, and the comparison is declared real")
