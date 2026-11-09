"""Readout: which member jobs of a coherence measure have readout controls covering the measure's two qubits in both
directions (P3's design, item 4, with its correction 3 of 2026-11-08T10:50:42Z; P3.1). Standard library and qro only.
The readout bound rho, under section 9.1's confusion model, is P3.2's.

A member job's CONTROLS are the known-answer Pubs in the job itself, and those in the job just before it on its device,
where that job is of the same bundle (one pinned chain, so a logical qubit is one physical qubit). The job just before
is the one whose time is the latest before the member's among the crate's jobs on its device (qro.p3_runs.on_device),
where every job there has a time of one kind and no two share one; otherwise there is none. A control's prepared set
is the X set of its manifest circuit's known-answer text (qro.p1_decode.expected_set, read from the File of that
circuit's digest); a control with no such circuit the comparison can read prepares nothing it can count.

A qubit is COVERED when some control prepares it 1 (holds it in its X set) and some control prepares it 0 (leaves it
out). A coherence measure's readout is covered when both of its pair's qubits are covered for every member job of both
runs. Law measures have no confusion model in v1: their readout is UNMEASURED, `none`, always.

Covered, the readout is neither UNMEASURED (that is false) nor CONTROLLED (that is unchecked): P3.1 refuses such a
measure `step-unbuilt` at "<measure>: the readout bound", and P3.2 lifts it. Not covered, the readout is UNMEASURED,
`none`. v0's coherence jobs are preceded by their bundle's law job, so no control serves them; P1's twin's coherence job
is preceded by its known answer, one pattern, {0, 1, 3, 7, 12}, so qubits 0 and 1 are never read prepared 0.
"""
from qro import p2_hold, p2_law
from qro.p3_declaration import RUNS
from qro.p3_runs import KNOWN_ANSWER, on_device
from qro.refusal import Refused

UNMEASURED, CONTROLLED = "UNMEASURED", "CONTROLLED"


def controls(crate, job):
    """The known-answer Pubs serving a member job: its own, and those of the job just before it on its device where
    that job is of the same bundle."""
    out = [p for p in job.pubs if p.role == KNOWN_ANSWER]
    ordered = on_device(crate, job.device)
    if ordered is not None and job.bundle is not None:
        i = next(k for k, j in enumerate(ordered) if j.entity["@id"] == job.entity["@id"])
        if i > 0 and ordered[i - 1].bundle == job.bundle:
            out += [p for p in ordered[i - 1].pubs if p.role == KNOWN_ANSWER]
    return out


def prepared(crate, pubs):
    """The X sets the controls prepare, of those whose circuit the crate carries in Quantum-Film's known-answer form."""
    out = []
    for p in pubs:
        x = crate.known_answer_set(p.circuit.circuit_sha256) if p.circuit is not None else None
        if x is not None:
            out.append(x)
    return out


def job_covered(crate, job, pair):
    sets = prepared(crate, controls(crate, job))
    return all(any(q in s for s in sets) and any(q not in s for s in sets) for q in pair)


def pair_of(measure, pubs):
    """The two qubits a coherence measure's member Pubs read (P2's coherence_pair, at the basis's own width)."""
    pairs = {p2_hold.coherence_pair(p.basis, len(p.basis))[1:] for p in pubs}
    if len(pairs) != 1:
        raise ValueError(f"{measure}: its member Pubs read {len(pairs)} pairs of qubits")
    return next(iter(pairs))


def covered(crates, measure, by_side):
    """Whether a coherence measure's readout is covered: every member job of both runs covered. `crates` is
    {body digest: Crate}; `by_side` {side: [(job, its member Pubs)]}."""
    if measure not in p2_law.COHERENCE:
        return False
    for side in RUNS:
        for job, pubs in by_side[side]:
            if not job_covered(crates[job.crate], job, pair_of(measure, pubs)):
                return False
    return True


def unbuilt(crates, members, refused):
    """`step-unbuilt` at the first measure, in measure order, whose readout is covered: its bound is P3.2's."""
    for measure in sorted(members):
        if measure not in refused and covered(crates, measure, members[measure]):
            raise Refused("step-unbuilt", f"{measure}: the readout bound",
                          "the measure's readout is covered by controls in both directions, and its bound, rho, is not "
                          "built yet (P3.2's): covered, it is neither UNMEASURED nor CONTROLLED until rho is")


def status(measure):
    """The readout of a measure that is not refused, in P3.1: UNMEASURED, `none` (a covered one was refused)."""
    return {"bound": "none", "status": UNMEASURED}
