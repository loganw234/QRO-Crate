"""What a comparison computes for each measure, and the verdicts and statements it draws (P3's design, items 4 and 5;
P3.1). Standard library and qro only. P2's line holds: P3 computes no interval but the vacuous one, and P2 decides no
verdict.

THE FAMILY, `qro-family/1`: M is the sum, over the measures not refused and the two runs, of 1 (the run's pooled
interval) and k (its members' intervals) where k >= 2; with one member, its interval is the pooled one, counted once.
It is structural, so fixed before any value is read. (A coherence measure whose readout is covered adds its readout
intervals in P3.2; in P3.1 such a measure is refused before M is counted.)

THE VALUES, from the raw bytes: each member Pub's Value by qro.p2_measures.pub_values, the function step 6 uses, with
its crate's own law; a member job's per-shot total and shots in scope summed over its Pubs, a run's over its members,
each total held to a whole number or a Fraction before it is summed (P2's N5). The intervals: qro.p2_interval.interval
at M and the plan's alpha, mapped by the measure's increasing affine map (p2_interval.mapped); a member or a run with no
shot in scope has the vacuous interval, (map(0), map(1)), and stays counted in M. Everything after the one outward
rounding inside P2's interval is exact Fraction arithmetic: the difference (p2_interval.difference), L(|diff|)
(p2_interval.abs_lower) and U(|diff|) = max(|L|, |U|), the drift bound U(D) (p2_interval.drift) for a run of two
members or more, and the strong form (p2_interval.strong_form) where both drifts are measured. No float and no `math`.

THE MEANS: `differ` if L(|diff|) > epsilon; `agree` if U(|diff|) <= epsilon; else `unresolved`.

THE CAUSES, one status a measure, read from the crates over every member Pub of both runs:
  question   EQUAL: one question digest and one logical circuit; DIFFERS where the plan's question is varied and they
             are not one (qro.p3_refusals.question; otherwise the comparison was refused);
  compile    EQUAL: one gate-list digest (each manifest circuit's `gates_sha256`); DIFFERS; `unexposed` where a member
             Pub has no manifest circuit. With it, `hold`: `holds` where every member Pub's gate list is carried in its
             crate and its manifest is a held Compile's (so step 7 held it against the same logical circuit: logically
             equivalent, by the exact hold), `withheld` where one is not, `unexposed` with the compile;
  submitted  EQUAL: one (program, route, kind, options digest, shots, decode), from the manifest; DIFFERS; `unexposed`;
  commit     EQUAL: every member Job's `qro:kitCommit` recorded and one; DIFFERS; `unknown` where any is `unknown`;
  sampling   CONTROLLED always: the plan's inequality at alpha over M, conditional on independent shots and jobs;
  device     EQUAL where the runs' selectors name one device, else DIFFERS;
  drift      CONTROLLED where both runs have two members or more, else UNMEASURED.
Bit order is a precondition, not a status: every accepted crate holds it (step 5).

INTERLEAVED (whose difference): the runs' devices differ; every crate holding members of either run holds members of
both, which with one crate a run means both runs take one crate; in it the members of the two runs, ordered by one kind
of time with no two times the same, alternate strictly; and each run has two members or more. Members on different
crates, a time missing, two kinds of time or a tie are not interleaved: the weaker statement is the one made.

THE STATEMENTS, each a word of the vocabulary's `statement` set, listed in the set's order, each said exactly when:
  isolated-pipeline   none of the seven below it is said: the question, what was submitted and the producing commit
                      EQUAL, the compile EQUAL or held, drift CONTROLLED and the strong form above epsilon;
  drift-unmeasured    a run has one member;
  strong-form-short   both drifts are measured and the strong form is not above epsilon;
  question-varied     the question DIFFERS;
  submitted-differs   what was submitted is not EQUAL (DIFFERS or `unexposed`, as the design's table has it);
  commit-unknown      the producing commit is `unknown`;
  commit-differs      it is DIFFERS;
  compile-unheld      the compile is `unexposed`, or DIFFERS and not held;
  device-alone        the devices differ, interleaved;
  device-and-time     the devices differ, not interleaved;
  one-device          the runs' selectors name one device;
  quantum-unpiped     not isolated from the pipeline;
  readout-unbounded   readout UNMEASURED;
  readout-short       readout CONTROLLED, and the strong form less the readout bound not above epsilon;
  integrity-dephased  the measure's class against the dephased twin is integrity (for either run's law);
  integrity-uniform   the same against the uniform twin;
  quantum-dephased    isolated from the pipeline, the class against the dephased twin signal for both runs' laws,
                      readout CONTROLLED and the strong form less the readout bound above epsilon;
  quantum-uniform     the same against the uniform twin.

UNSEEN: the factors both runs share, each a word of `factor`, in the set's order: `question`, `compile`, `submitted`,
`commit` and `device`, each where its cause is EQUAL; `decode`, one (rule, bit order) over every member Pub; `known-answer`,
where each run's X sets of every known-answer circuit its members' bundles name are known, one or more, and the same
set; `date`, every member's time known and on one UTC date.
"""
from fractions import Fraction

from qro import p2_interval, p2_measures
from qro import vocabulary as V
from qro.p3_declaration import RUNS

EQUAL, DIFFERS, CONTROLLED, UNMEASURED = "EQUAL", "DIFFERS", "CONTROLLED", "UNMEASURED"
STATEMENTS = tuple(V.WORDS["statement"])
FACTORS = tuple(V.WORDS["factor"])
TWINS = ("dephased", "uniform")


class ValueProblem(ValueError):
    """A member's values that are not as P2's measures give them: a total that is no whole number or Fraction, or Pubs
    of one measure on two maps. Never a verdict."""


def family(members, refused):
    """M, by `qro-family/1`, from {measure: {side: [(job, pubs)]}} and the measures refused."""
    out = 0
    for measure in sorted(members):
        if measure in refused:
            continue
        for side in RUNS:
            k = len(members[measure][side])
            out += 1 + (k if k >= 2 else 0)
    return out


def total_of(values):
    """(total, shots in scope, map) of a measure's Values on one job's Pubs, each total held to a whole number or a
    Fraction (never a float or a bool) before it is summed."""
    total, n, mapping = Fraction(0), 0, None
    for v in values:
        if type(v.total) is not int and not isinstance(v.total, Fraction):
            raise ValueProblem(f"{v.measure}: a total that is no whole number or Fraction ({type(v.total).__name__})")
        if type(v.in_scope) is not int or v.in_scope < 0:
            raise ValueProblem(f"{v.measure}: shots in scope that are no whole number")
        if mapping is not None and v.mapping != mapping:
            raise ValueProblem(f"{v.measure}: two Pubs of one job on two maps")
        total, n, mapping = total + v.total, n + v.in_scope, v.mapping
    if mapping is None:
        raise ValueProblem("a member with no certified Value")
    return total, n, mapping


def interval(total, n, M, alpha, mapping):
    """P2's certified interval at M, mapped; the vacuous (map(0), map(1)) where no shot is in scope."""
    if n == 0:
        return mapping(Fraction(0)), mapping(Fraction(1))
    return p2_interval.mapped(p2_interval.interval(total, n, M, alpha), mapping)


def run_of(tallies, M, alpha):
    """A run's members' intervals and its pooled figures, from [(member id, total, n, map)] in the members' order:
    {"members": [(id, n, interval)], "total", "n", "value", "interval", "drift"}."""
    total = sum((t for _, t, _, _ in tallies), Fraction(0))
    n = sum(k for _, _, k, _ in tallies)
    mappings = {mp for _, _, _, mp in tallies}
    if len(mappings) != 1:
        raise ValueProblem("one measure's members on two maps")
    mapping = next(iter(mappings))
    pooled = interval(total, n, M, alpha, mapping)
    if len(tallies) == 1:
        each = [(tallies[0][0], n, pooled)]
        drift = None
    else:
        each = [(i, k, interval(t, k, M, alpha, mp)) for i, t, k, mp in tallies]
        drift = p2_interval.drift([iv for _, _, iv in each], pooled)
    return {"members": each, "total": total, "n": n, "value": mapping(Fraction(total) / n) if n else None,
            "interval": pooled, "drift": drift, "map": mapping}


def abs_upper(diff):
    """U(|diff|) = max(|L|, |U|)."""
    return max(abs(diff[0]), abs(diff[1]))


def means(diff, epsilon):
    if p2_interval.abs_lower(diff) > epsilon:
        return "differ"
    if abs_upper(diff) <= epsilon:
        return "agree"
    return "unresolved"


def values_of(crate, pub, cache):
    """{measure: Value} of one member Pub, from its raw bytes by P2's pub_values with its crate's own law; once each."""
    key = (crate.digest, pub.id)
    if key not in cache:
        cache[key] = p2_measures.pub_values(crate.directory, crate.md, pub.entity, crate.law)
    return cache[key]


# -- the causes ---------------------------------------------------------------------------------------------------------
def causes(by_side, crates, question_status, devices, drifts):
    """The causes' statuses of one measure, from its members {side: [(job, pubs)]}."""
    pubs = [(job, p) for side in RUNS for job, ps in by_side[side] for p in ps]
    exposed = all(p.circuit is not None and job.manifest is not None for job, p in pubs)
    if not exposed:
        compile_, hold, submitted = "unexposed", "unexposed", "unexposed"
    else:
        compile_ = EQUAL if len({p.circuit.gates_sha256 for _, p in pubs}) == 1 else DIFFERS
        hold = "holds" if all(job.held and p.circuit.gates_sha256 in crates[job.crate].carried for job, p in pubs) \
            else "withheld"
        sent = {(job.manifest.program, job.manifest.route, job.manifest.kind, job.manifest.options_sha256,
                 p.circuit.shots, job.manifest.decode) for job, p in pubs}
        submitted = EQUAL if len(sent) == 1 else DIFFERS
    commits = {job.commit for side in RUNS for job, _ in by_side[side]}
    commit = "unknown" if "unknown" in commits else EQUAL if len(commits) == 1 else DIFFERS
    return {"commit": commit, "compile": compile_, "device": EQUAL if devices["a"] == devices["b"] else DIFFERS,
            "drift": CONTROLLED if all(drifts[side] is not None for side in RUNS) else UNMEASURED, "hold": hold,
            "question": question_status, "sampling": CONTROLLED, "submitted": submitted}


def interleaved(by_side, devices):
    """Whether the runs' members interleave: as the module's docstring says."""
    if devices["a"] == devices["b"] or any(len(by_side[side]) < 2 for side in RUNS):
        return False
    crates = {side: {job.crate for job, _ in by_side[side]} for side in RUNS}
    if crates["a"] != crates["b"]:
        return False
    for crate in crates["a"]:
        seq = [(job.time, job.clock, side) for side in RUNS for job, _ in by_side[side] if job.crate == crate]
        if any(t is None for t, _, _ in seq) or len({c for _, c, _ in seq}) != 1:
            return False
        seq.sort(key=lambda x: x[0])
        if any(x[0] == y[0] or x[2] == y[2] for x, y in zip(seq, seq[1:])):
            return False
    return True


def statements(c):
    """The words said of a measure, in the set's order, from its conditions `c`: {"causes", "members" ({side: count}),
    "strongForm" (Fraction or None), "epsilon", "interleaved", "readout" (status), "rho" (Fraction or None),
    "classes" ({side: {twin: class}})}."""
    k, sf, eps = c["members"], c["strongForm"], c["epsilon"]
    causes_ = c["causes"]
    said = set()
    if any(k[side] == 1 for side in RUNS):
        said.add("drift-unmeasured")
    if all(k[side] >= 2 for side in RUNS) and sf is not None and not sf > eps:
        said.add("strong-form-short")
    if causes_["question"] == DIFFERS:
        said.add("question-varied")
    if causes_["submitted"] != EQUAL:
        said.add("submitted-differs")
    if causes_["commit"] == "unknown":
        said.add("commit-unknown")
    if causes_["commit"] == DIFFERS:
        said.add("commit-differs")
    if causes_["compile"] == "unexposed" or (causes_["compile"] == DIFFERS and causes_["hold"] != "holds"):
        said.add("compile-unheld")
    # The seven reasons are the failures of the design's conjunction, one each: with both drifts measured the strong
    # form exists, and strong-form-short is said where it is not above epsilon; with a run of one member,
    # drift-unmeasured is said. So isolated is the absence of every reason.
    reasons = {"drift-unmeasured", "strong-form-short", "question-varied", "submitted-differs", "commit-unknown",
               "commit-differs", "compile-unheld"}
    isolated = not (said & reasons)
    if isolated:
        said.add("isolated-pipeline")
    if causes_["device"] == EQUAL:
        said.add("one-device")
    else:
        said.add("device-alone" if c["interleaved"] else "device-and-time")
    if not isolated:
        said.add("quantum-unpiped")
    rho = c["rho"]
    beyond = c["readout"] == CONTROLLED and sf is not None and rho is not None and sf - rho > eps
    if c["readout"] == UNMEASURED:
        said.add("readout-unbounded")
    if c["readout"] == CONTROLLED and sf is not None and rho is not None and not sf - rho > eps:
        said.add("readout-short")
    for twin in TWINS:
        classes = [c["classes"][side][twin] for side in RUNS]
        if "integrity" in classes:
            said.add(f"integrity-{twin}")
        if isolated and all(x == "signal" for x in classes) and beyond:
            said.add(f"quantum-{twin}")
    return [w for w in STATEMENTS if w in said]


def unseen(by_side, causes_, crates):
    """The factors both runs share, in the set's order."""
    shared = {f for f in ("question", "compile", "submitted", "commit", "device") if causes_[f] == EQUAL}
    pubs = [p for side in RUNS for _, ps in by_side[side] for p in ps]
    if len({(p.rule, p.order) for p in pubs}) == 1 and all(isinstance(p.rule, str) for p in pubs):
        shared.add("decode")
    sets = {}
    for side in RUNS:
        found = set()
        for job, _ in by_side[side]:
            if job.manifest is None:
                found = None
                break
            for circ in job.manifest.circuits():
                if circ.role == "known-answer":
                    x = crates[job.crate].known_answer_set(circ.circuit_sha256)
                    if x is None:
                        found = None
                        break
                    found.add(x)
            if found is None:
                break
        sets[side] = found
    if all(sets[side] for side in RUNS) and sets["a"] == sets["b"]:
        shared.add("known-answer")
    times = [job.time for side in RUNS for job, _ in by_side[side]]
    if times and all(t is not None for t in times) and len({t.date() for t in times}) == 1:
        shared.add("date")
    return [f for f in FACTORS if f in shared]
