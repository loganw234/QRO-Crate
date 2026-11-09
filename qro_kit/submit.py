"""The one place a sampler is made and run, and the seven spend rules before any submission (P5's design, item 6; P5.1).

Every refusal here is `qro.refusal.Refused`, by a name of the vocabulary, raised BEFORE a job is sent. The rules, each
shown by a test that passes a stand-in service or backend and asserts that nothing was submitted (the counter is 0 and no
`-submitting.json` exists):
  S1  one unit, once: a records directory that already holds a `<job>-submitting.json` or `-line.json` of this unit, or a
      line holding a commitment of it, is refused `once-only` (the vendored runner.once_only);
  S2  the instance covers the unit: `usage_remaining_seconds >= 216` and `usage_limit_ru - usage_consumed_ru >= 216 x
      0.015434` from the service's usage(), else `spend-usage`;
  S3  a running ceiling: before each job, `charged so far + the job's highest-model estimate <= 270 s`; after each job, a
      charge past twice that estimate stops the unit (`spend-unit`): the model failed, and the unit is contributed
      incomplete;
  S4  caps: each job's max_execution_time is a whole number of seconds in 1 to 300, at least its highest-model estimate and
      the recipe's cap (15 s a control job, 60 s a film job), else `spend-cap`;
  S5  plan open: the instance's plan is `open`, else `plan-not-open`;
  S6  never a fake's job as the real unit's: the real route refuses a backend object that is not an IBMBackend obtained from
      the service, else `kind-mismatch`;
  S7  the fence: `--route real` needs the flag, `--confirm` the first 12 hex digits of the unit's digest, a pre-flight record
      for this unit under 24 hours old that holds, a clean tagged tree, and S1 to S6 clear; any one missing is
      `route-unsafe`. P5.1 builds no pre-flight and no connection: the acceptor of a pre-flight record is here, the
      writer is P5.2's, and with no service the fence refuses.

`sampler_for` and `send` are the only place in the kit a SamplerV2 is made and the only `.run(` on one (a test reads the
package by `ast`): `send` runs `permit`, which holds S1, S3 and S4 for the job, and takes the S-rule check for the route
as an argument it calls first. Standard library and `qro` at the module level; qiskit only inside functions.
"""
import json
import warnings
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

from qro import p5_tree, p5_unit as U
from qro.refusal import Refused

PREFLIGHT_FORMAT = "qro-crate/unit-preflight/v1"
PREFLIGHT_AGE = timedelta(hours=24)
CONFIRM_LENGTH = 12
MAX_CAP = 300


def _refuse(name, where, detail):
    return Refused(name, where, detail)


# -- S1 ----------------------------------------------------------------------------------------------------------------------
def check_once(runner, manifest, job_name, out_dir, roots=()):
    """S1. The vendored runner's own once-only check, a refusal `once-only` naming the job."""
    problems = runner.once_only(manifest, job_name, out_dir, roots)
    if problems:
        raise _refuse("once-only", job_name, "; ".join(problems))


# -- S2 ----------------------------------------------------------------------------------------------------------------------
def check_usage(usage):
    """S2. `usage` is the service's usage() dict: usage_remaining_seconds and the RU limit and consumed."""
    try:
        seconds = Fraction(usage["usage_remaining_seconds"])
        ru = Fraction(usage["usage_limit_ru"]) - Fraction(usage["usage_consumed_ru"])
    except (KeyError, TypeError, ValueError):
        raise _refuse("spend-usage", "usage()", "the service's usage names no remaining seconds or resource units") from None
    if seconds < U.UNIT_ESTIMATE:
        raise _refuse("spend-usage", "usage()", f"{seconds} s of the instance's time remain; a unit needs {U.UNIT_ESTIMATE} s")
    if ru < U.UNIT_RU:
        raise _refuse("spend-usage", "usage()", f"{float(ru):.3f} resource units remain; a unit needs {float(U.UNIT_RU):.3f}")


# -- S3 ----------------------------------------------------------------------------------------------------------------------
def check_ceiling(charged, kind):
    """S3 before a job: the charge so far plus this job's highest-model estimate stays within the ceiling."""
    if Fraction(charged) + U.JOB_ESTIMATE[kind] > U.CEILING:
        raise _refuse("spend-unit", kind, f"{charged} s charged so far and {U.JOB_ESTIMATE[kind]} s for this job would pass "
                                          f"the unit's ceiling of {U.CEILING} s")


def check_charge(charge, kind):
    """S3 after a job: a charge past twice the job's estimate means the cost model failed; the unit stops."""
    if Fraction(charge) > 2 * U.JOB_ESTIMATE[kind]:
        raise _refuse("spend-unit", kind, f"the job was charged {charge} s, past twice its estimate of "
                                          f"{U.JOB_ESTIMATE[kind]} s: the model failed, and the unit stops here")


# -- S4 ----------------------------------------------------------------------------------------------------------------------
def check_cap(cap, kind, where="the job"):
    """S4 for one job: a whole number of seconds from 1 to 300, at least the estimate, and the recipe's."""
    if type(cap) is not int or not 1 <= cap <= MAX_CAP:
        raise _refuse("spend-cap", where, f"max_execution_time {cap!r} is not a whole number of seconds from 1 to {MAX_CAP}")
    if cap < U.JOB_ESTIMATE[kind]:
        raise _refuse("spend-cap", where, f"max_execution_time {cap} s is under the job's estimate of {U.JOB_ESTIMATE[kind]} s")
    if cap != U.CAPS[kind]:
        raise _refuse("spend-cap", where, f"max_execution_time {cap} s is not the recipe's {U.CAPS[kind]} s for a {kind} job")


# -- S5, S6 --------------------------------------------------------------------------------------------------------------------
def check_plan(plan):
    """S5. The instance's plan is `open`: a paid plan never runs a free-tier unit by mistake."""
    if plan != "open":
        raise _refuse("plan-not-open", "the instance", f"the instance's plan is {plan!r}, not 'open'")


def check_backend(runner, backend, manifest, ibm_backend_class, from_service=True):
    """S6. The kind of the backend OBJECT (runner.kind_from: qpu only for an IBMBackend from the service that is not a
    simulator) is the manifest's, and its name is the manifest's."""
    simulator = bool(getattr(getattr(backend, "configuration", lambda: None)(), "simulator", True))
    kind = runner.kind_from(isinstance(backend, ibm_backend_class), from_service, simulator)
    if kind != manifest["kind"] or getattr(backend, "name", None) != manifest["backend"]:
        raise _refuse("kind-mismatch", manifest["backend"], f"the backend object is {getattr(backend, 'name', None)!r} of "
                                                              f"kind {kind!r}; the bundle binds {manifest['backend']!r}, {manifest['kind']!r}")


# -- S7 ----------------------------------------------------------------------------------------------------------------------
def preflight_ok(unit_dir, unit_digest, now):
    """S7(c): a pre-flight record of this unit, under 24 hours old, that holds. Records are `preflight/<UTC>.json` beside the
    unit directory (P5.2 writes them); the newest that names this unit decides. (True, '') or (False, why)."""
    folder = Path(unit_dir).parent / "preflight"
    found, ahead = [], 0
    for p in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            doc = json.loads(p.read_bytes())
            at = datetime.strptime(doc["at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if isinstance(doc, dict) and doc.get("format") == PREFLIGHT_FORMAT and doc.get("unit_sha256") == unit_digest:
            if at > now:                    # dated ahead of now: not under 24 hours old, and never "the newest"
                ahead += 1
                continue
            found.append((at, doc))
    if not found:
        return False, ("no pre-flight record of this unit" if not ahead else
                       "no pre-flight record of this unit dated at or before now: each is dated ahead of now")
    at, doc = max(found, key=lambda f: f[0])
    if not 0 <= (now - at).total_seconds() < PREFLIGHT_AGE.total_seconds():
        return False, f"the newest pre-flight record is of {at:%Y-%m-%dT%H:%M:%SZ}, not under 24 hours old"
    if doc.get("holds") != "holds":
        return False, "the newest pre-flight record does not hold"
    return True, ""


def fence(unit_dir, unit_digest, *, flag, confirm, tree, now, rules):
    """S7: every one of the real route's conditions, or `route-unsafe` naming the first that fails. `flag` is the
    `--route real` flag as given, `confirm` the digest prefix typed, `tree` a callable that raises Refused('kit-dirty') or
    returns, `rules` a callable that raises Refused for S1 to S6 (or `route-unsafe` where it cannot be shown)."""
    if flag is not True:
        raise _refuse("route-unsafe", "--route real", "the real route is asked for without its flag")
    if not isinstance(confirm, str) or confirm != unit_digest[:CONFIRM_LENGTH]:
        raise _refuse("route-unsafe", "--confirm", f"the first {CONFIRM_LENGTH} hex digits of the unit's digest, "
                                                    "copied from freeze's output, are needed")
    ok, why = preflight_ok(unit_dir, unit_digest, now)
    if not ok:
        raise _refuse("route-unsafe", "preflight", why)
    try:
        tree()
    except Refused as r:
        raise _refuse("route-unsafe", r.where, f"the tree is not clean: {r.name}: {r.detail}") from None
    try:
        rules()
    except Refused as r:
        raise _refuse("route-unsafe", r.where, f"a spend rule is not clear: {r.name}: {r.detail}") from None


# -- the one place a sampler is made and run ------------------------------------------------------------------------------------------
def sampler_for(backend, max_execution_time, rep_delay):
    """(a SamplerV2 on `backend` with the unit's options set, the options it would send): dynamical decoupling and both
    twirlings off, init_qubits on, the device's rep_delay where it states one, max_execution_time a runtime option."""
    from dataclasses import asdict

    from qiskit_ibm_runtime.options import SamplerOptions
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from qiskit_ibm_runtime import SamplerV2
        sampler = SamplerV2(mode=backend)
    o = sampler.options
    o.dynamical_decoupling.enable = False
    o.twirling.enable_gates = False
    o.twirling.enable_measure = False
    o.execution.init_qubits = True
    if rep_delay is not None:
        o.execution.rep_delay = rep_delay
    o.max_execution_time = max_execution_time
    return sampler, SamplerOptions._get_program_inputs(asdict(o))["options"]


def permit(runner, manifest, job_name, out_dir, charged, once=True):
    """What every job passes before it is sent: S1 (unless `once` is off), S3 and S4 for this job. S2, S5 and S6 are the
    route's (a service's). The driver calls it before it makes anything for the job; the runner holds S1 again itself,
    immediately before it writes the job's marker, which `send` (called after the marker) therefore cannot ask again."""
    entry = next((j for j in manifest["jobs"] if j["job"] == job_name), None)
    if entry is None:
        raise _refuse("once-only", job_name, "the bundle has no such job")
    kind, _ = U.parse_job_name(job_name)
    check_cap(entry["max_execution_time"], kind, job_name)
    check_ceiling(charged, kind)
    if once:
        check_once(runner, manifest, job_name, out_dir)


def send(runner, sampler, pubs, manifest, job_name, out_dir, charged, route_rules=lambda: None):
    """Run one job's PUBs on the sampler, once its rules are clear: the route's (S2, S5, S6 and the fence for the real
    route), then S3 and S4 (S1 is the runner's, immediately before the marker that precedes this call). The only `.run(`
    on a sampler in the kit."""
    route_rules()
    permit(runner, manifest, job_name, out_dir, charged, once=False)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Options .* have no effect in local testing mode")
        return sampler.run(pubs)


def tree_of_kit():
    """The kit's own tree state: the root is the directory above qro_kit, and the code running must lie in it (D5)."""
    import qro
    import qro_kit
    root = Path(qro_kit.__file__).resolve().parents[1]
    return p5_tree.tree_state(root, code=(qro.__file__, qro_kit.__file__))
