"""A comparison's declaration, `qro-comparison/1`: its runs' selectors, its plan and the plan's digest, and the rule
that labels a comparison exploratory (P3's design, items 1 and 2, with its entry of 2026-11-08T10:51:27Z: one selector
a run, fixed in the plan; P3.1). Standard library and qro only.

THE FORM. One spelling: canonical JSON as the metadata is written (qro.canonical.dumps: sorted keys, an indent of two,
ASCII, LF, a final LF), read strictly by P1.1's JSON reader and written again, so that any other bytes are refused.
Exactly these keys:
    crates           {"a": [body digests], "b": [body digests]}: the pool, the crates each run takes; each list
                     one digest or more, sorted, each once
    format           "qro-comparison/1"
    plan             everything a pre-registration can fix before any crate exists, with exactly these keys:
        alpha        a rational in (0, 1)
        family       text: the rule that counts the family M ("qro-family/1")
        granularity  a word of `granularity`
        inequality   text: the concentration inequality ("qro-hoeffding-kl/1")
        kind         a word of `comparison-kind`
        measureSet   text: the measure set ("qro-measures/1")
        measures     [{"distance": text ("abs-mean"), "epsilon": a rational >= 0, "measure": a word of `measure`}],
                     one or more, sorted by measure, each once
        question     "fixed", or "varied": the question is the factor the comparison varies
        runs         {"a": a selector, "b": a selector}
        sampling     text: the sampling model ("independent-shots-and-jobs")
    preregistration  "none", or the path of the copy of the pre-registration the comparison crate carries,
                     "comparison/preregistration/<name>", <name> one segment of a file's path
A SELECTOR, `qro-selector/1`: an object of `device` (text, which every selector names: one device a run) and any of
`bundles` (manifest digests) and `jobs` (job ids), each one or more, sorted, each once, and `from` and `until`
(times, the first before the second). It selects each Job of a crate that meets every key it gives: the name of the
Job's `qro:device`; its line's `bundle_sha256`; its `qro:jobId`; its time in [from, until). A job's time is its
`startTime` where the Job states one, else its line's `submitted_at` (qro.p3_runs); a job with neither is in no
window. `read` refuses any declaration out of this form (DeclarationError), so that a hostile one is a refusal, never a
crash: the comparison crate's generator raises it, and step 9 refuses the crate `metadata-generated`.

THE PLAN'S DIGEST is the SHA-256 of the plan in canonical compact JSON (qro.canonical.compact). The pool is outside it,
since a crate exists only after its results.

LATE: a comparison is labelled exploratory (`selector-late`, kept, never refused) unless the declaration names a copy
of a pre-registration whose bytes hold the plan's digest as a whole token: 64 lowercase hex digits, neither preceded
nor followed by a hex digit of either case. Where it does, the record says `none`; "declared before the data" is then
still REPORTED, the pre-registration's own date being its commit and push, outside every crate (study QRO-0, rule 1).

WHAT THIS VERSION DOES NOT BUILD is refused `step-unbuilt` by `unbuilt`, before any crate is read: a family rule, an
inequality, a sampling model or a measure set but the four named above; a distance but `abs-mean` (a Hellinger distance
on a declared outcome law among them); a measure with no certified interval in `qro-measures/1`; granularity `crate`;
and a run whose pool holds more than one crate, which pools across crates (P3.2's, with P5's units: the design's item 6).
"""
import hashlib
import re
from dataclasses import dataclass
from fractions import Fraction

from qro import canonical, p1_forms, p2_interval, p2_law, spelling
from qro.refusal import Refused

FORMAT = "qro-comparison/1"
FAMILY_RULE = "qro-family/1"
INEQUALITY = p2_interval.RULE                      # qro-hoeffding-kl/1
MEASURE_SET = p2_law.MEASURE_SET                   # qro-measures/1
SAMPLING = "independent-shots-and-jobs"
DISTANCE = "abs-mean"
QUESTION = ("fixed", "varied")
RUNS = ("a", "b")
PREREGISTRATION_DIR = "comparison/preregistration/"
KEYS = ("crates", "format", "plan", "preregistration")
PLAN_KEYS = ("alpha", "family", "granularity", "inequality", "kind", "measureSet", "measures", "question", "runs",
             "sampling")
MEASURE_KEYS = ("distance", "epsilon", "measure")
SELECTOR_KEYS = ("bundles", "device", "from", "jobs", "until")


class DeclarationError(ValueError):
    """A declaration that is not `qro-comparison/1`: where, and why."""


@dataclass(frozen=True)
class Selector:
    device: str
    bundles: tuple | None          # manifest digests, or None where the selector gives none
    jobs: tuple | None             # job ids, or None
    start: object | None           # an aware datetime, or None: `from`
    until: object | None

    def selects(self, device, bundle, job_id, time):
        """Whether a job of this device, bundle, id and time (an aware datetime, or None) meets every key given."""
        if device != self.device:
            return False
        if self.bundles is not None and bundle not in self.bundles:
            return False
        if self.jobs is not None and job_id not in self.jobs:
            return False
        if self.start is not None or self.until is not None:
            if time is None:
                return False
            if self.start is not None and time < self.start:
                return False
            if self.until is not None and not time < self.until:
                return False
        return True


@dataclass(frozen=True)
class Measure:
    measure: str
    distance: str
    epsilon: Fraction


@dataclass(frozen=True)
class Plan:
    alpha: Fraction
    family: str
    granularity: str
    inequality: str
    kind: str
    measure_set: str
    measures: tuple                # of Measure, sorted by measure
    question: str
    runs: dict                     # {"a": Selector, "b": Selector}
    sampling: str
    digest: str                    # the SHA-256 of the plan in canonical compact JSON


@dataclass(frozen=True)
class Declaration:
    crates: dict                   # {"a": (body digest, ...), "b": (...)}
    plan: Plan
    preregistration: str | None    # the copy's path in the comparison crate, or None for "none"
    digest: str                    # the SHA-256 of the declaration's bytes


def _keys(doc, where, keys, required=None):
    if not isinstance(doc, dict):
        raise DeclarationError(f"{where}: not an object")
    required = keys if required is None else required
    extra, missing = sorted(set(doc) - set(keys)), sorted(set(required) - set(doc))
    if extra or missing:
        raise DeclarationError(f"{where}: holds exactly the keys {', '.join(keys)}"
                               + (f"; it lacks {', '.join(missing)}" if missing else "")
                               + (f"; it holds {', '.join(extra)}" if extra else ""))


def _spelt(value, spelling_name, where):
    p = spelling.problem(spelling_name, value)
    if p:
        raise DeclarationError(f"{where}: {p}")
    return value


def _list(value, where, spelling_name):
    """A list of one value or more in a spelling, sorted and each once."""
    if not isinstance(value, list) or not value:
        raise DeclarationError(f"{where}: a list of one value or more")
    for i, v in enumerate(value):
        _spelt(v, spelling_name, f"{where}[{i}]")
    if value != sorted(set(value)):
        raise DeclarationError(f"{where}: sorted, each value once")
    return tuple(value)


def _rational(value, where):
    return Fraction(_spelt(value, "rational", where))


def _time(value, where):
    _spelt(value, "time", where)
    try:
        return p1_forms.parse_time(value, "Z")
    except ValueError as x:
        raise DeclarationError(f"{where}: {x}") from None


def _selector(doc, where):
    _keys(doc, where, SELECTOR_KEYS, required=("device",))
    device = _spelt(doc["device"], "text", f"{where} device")
    bundles = _list(doc["bundles"], f"{where} bundles", "digest") if "bundles" in doc else None
    jobs = _list(doc["jobs"], f"{where} jobs", "text") if "jobs" in doc else None
    start = _time(doc["from"], f"{where} from") if "from" in doc else None
    until = _time(doc["until"], f"{where} until") if "until" in doc else None
    if start is not None and until is not None and not start < until:
        raise DeclarationError(f"{where}: its window [from, until) holds no time: from is not before until")
    return Selector(device, bundles, jobs, start, until)


def _measures(value, where):
    if not isinstance(value, list) or not value:
        raise DeclarationError(f"{where}: a list of one measure or more")
    out = []
    for i, m in enumerate(value):
        at = f"{where}[{i}]"
        _keys(m, at, MEASURE_KEYS)
        name = _spelt(m["measure"], "word:measure", f"{at} measure")
        distance = _spelt(m["distance"], "text", f"{at} distance")
        epsilon = _rational(m["epsilon"], f"{at} epsilon")
        if epsilon < 0:
            raise DeclarationError(f"{at} epsilon: a tolerance is a rational of zero or more")
        out.append(Measure(name, distance, epsilon))
    names = [m.measure for m in out]
    if names != sorted(set(names)):
        raise DeclarationError(f"{where}: sorted by measure, each measure once")
    return tuple(out)


def _plan(doc, where="plan"):
    _keys(doc, where, PLAN_KEYS)
    alpha = _rational(doc["alpha"], f"{where} alpha")
    if not 0 < alpha < 1:
        raise DeclarationError(f"{where} alpha: a rational in (0, 1)")
    if doc["question"] not in QUESTION:
        raise DeclarationError(f"{where} question: {' or '.join(QUESTION)}")
    _keys(doc["runs"], f"{where} runs", RUNS)
    return Plan(alpha, _spelt(doc["family"], "text", f"{where} family"),
                _spelt(doc["granularity"], "word:granularity", f"{where} granularity"),
                _spelt(doc["inequality"], "text", f"{where} inequality"),
                _spelt(doc["kind"], "word:comparison-kind", f"{where} kind"),
                _spelt(doc["measureSet"], "text", f"{where} measureSet"),
                _measures(doc["measures"], f"{where} measures"), doc["question"],
                {side: _selector(doc["runs"][side], f"{where} runs {side}") for side in RUNS},
                _spelt(doc["sampling"], "text", f"{where} sampling"),
                plan_digest(doc))


def _preregistration(value):
    if value == "none":
        return None
    where = "preregistration"
    if not isinstance(value, str) or not value.startswith(PREREGISTRATION_DIR):
        raise DeclarationError(f"{where}: none, or a path {PREREGISTRATION_DIR}<name>")
    name = value[len(PREREGISTRATION_DIR):]
    if not name or "/" in name or spelling.path_problem(value) or spelling.id_problem(value):
        raise DeclarationError(f"{where}: <name> is one segment of a file's path in the crate's spelling")
    return value


def plan_digest(plan):
    """The SHA-256 of a plan, as a dict, in canonical compact JSON."""
    return hashlib.sha256(canonical.compact(plan)).hexdigest()


def read(data):
    """The Declaration in a declaration's bytes, or DeclarationError: `qro-comparison/1` in its one spelling."""
    if not isinstance(data, (bytes, bytearray)):
        raise DeclarationError("a declaration is bytes")
    data = bytes(data)
    doc = p1_forms.load_json(data, "the declaration", DeclarationError)
    try:
        again = canonical.dumps(doc)
    except (TypeError, ValueError):
        raise DeclarationError("the declaration holds a value with no canonical spelling") from None
    if again != data:
        raise DeclarationError("the declaration is not in its one spelling: canonical JSON, sorted keys, an indent of "
                               "two, ASCII, LF and a final LF")
    _keys(doc, "the declaration", KEYS)
    if doc["format"] != FORMAT:
        raise DeclarationError(f"format: {FORMAT}")
    _keys(doc["crates"], "crates", RUNS)
    crates = {side: _list(doc["crates"][side], f"crates {side}", "digest") for side in RUNS}
    return Declaration(crates, _plan(doc["plan"]), _preregistration(doc["preregistration"]),
                       hashlib.sha256(data).hexdigest())


def write(crates, plan, preregistration="none"):
    """A declaration's bytes, from the pool ({"a": [digests], "b": [...]}), the plan (a dict in the form above) and the
    pre-registration's path or "none"; read back before they are returned, so nothing out of form is written."""
    data = canonical.dumps({"crates": crates, "format": FORMAT, "plan": plan, "preregistration": preregistration})
    read(data)
    return data


def late(digest, preregistration):
    """`selector-late`, or `none` where the pre-registration's bytes (None: there is none) hold the plan's digest as a
    whole token."""
    if preregistration is None:
        return "selector-late"
    token = re.compile(rb"(?<![0-9A-Fa-f])" + digest.encode("ascii") + rb"(?![0-9A-Fa-f])")
    return "none" if token.search(preregistration) else "selector-late"


def unbuilt(declaration):
    """Refused `step-unbuilt` at the first of what this version does not build, in the plan's key order, then the pool;
    None where it builds all of it."""
    plan = declaration.plan

    def refuse(where, detail):
        raise Refused("step-unbuilt", where, detail)
    if plan.family != FAMILY_RULE:
        refuse("plan family", f"the family rule {plan.family} is not built: {FAMILY_RULE} is")
    if plan.granularity != "job":
        refuse("plan granularity", f"granularity {plan.granularity} is not built yet (P3.2's, with P5's units): job is")
    if plan.inequality != INEQUALITY:
        refuse("plan inequality", f"the inequality {plan.inequality} is not built: {INEQUALITY} is")
    if plan.measure_set != MEASURE_SET:
        refuse("plan measureSet", f"the measure set {plan.measure_set} is not built: {MEASURE_SET} is")
    for m in plan.measures:
        if m.distance != DISTANCE:
            refuse(f"plan measures {m.measure} distance", f"the distance {m.distance} is not built: {DISTANCE} is, "
                                                          "the absolute difference of a bounded mean")
        if m.measure not in p2_law.CERTIFIED:
            refuse(f"plan measures {m.measure}", f"{m.measure} has no certified interval in {MEASURE_SET}, so "
                                                 f"{DISTANCE} cannot compare it")
    if plan.sampling != SAMPLING:
        refuse("plan sampling", f"the sampling model {plan.sampling} is not built: {SAMPLING} is")
    for side in RUNS:
        if len(declaration.crates[side]) > 1:
            refuse(f"crates {side}", f"a run of {len(declaration.crates[side])} crates: pooling across crates is not "
                                     "built yet (P3.2's, with P5's units); a run takes one crate")


def plan(measures, runs, kind="real", question="fixed", alpha="1/20", granularity="job"):
    """A plan, as a dict in the form above, of what this version builds: `measures` {measure: epsilon, spelt} and
    `runs` {"a": a selector, "b": a selector}, each a dict in the selector's form."""
    return {"alpha": alpha, "family": FAMILY_RULE, "granularity": granularity, "inequality": INEQUALITY, "kind": kind,
            "measureSet": MEASURE_SET,
            "measures": [{"distance": DISTANCE, "epsilon": e, "measure": m} for m, e in sorted(measures.items())],
            "question": question, "runs": runs, "sampling": SAMPLING}
