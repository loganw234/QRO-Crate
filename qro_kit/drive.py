"""`drive`: the unit's 18 jobs, one at a time, in the recipe's order (P5's design, items 1, 3 and 6; P5.1).

    python -m qro_kit drive UNIT_DIR --route local
    python -m qro_kit drive UNIT_DIR --route real --confirm 12HEXDIGITS     # refused `route-unsafe` in this kit tag

Adapted from moth-quantum's tools/hw_run.py (main, 3a73823): the same calls, handed to the vendored runner, which does the
rest in its own eleven steps (quantum_film/ibm/runner.py): a job's marker, its submission, IBM's created time, the line
committed and pushed before any result is read, the raw bytes written first, the records fixed, the verdict. What is the
unit's own is the loop (18 jobs: pass by pass, device by device, a control job and then a film job), the gate (a film job is
submitted only after its pass's control job holds on both PUBs, the known answer's and its complement's, and a control job
that does not hold stops the unit with nothing more spent) and the spend and tree rules before any submission (submit.py).

THE LOCAL ROUTE runs `SamplerV2` on a fake backend through `QiskitRuntimeLocalService`, kind `simulator`, with a stand-in job
(an id `dryrun-<16 hex>`, a created time, the result as the runtime's own JSON encoding) that hands the raw result over only
once the line is anchored. Its anchor is the real one (git commit and push) against the throwaway origin `freeze` made. Its
metrics wrapper is Quantum-Film's real shape (created, running and finished times) marked `dry_run`, which the generator's
GU8 accepts for a simulator unit only; its times are the producer's machine's clock, so the unit's clock is `local`.

THE REAL ROUTE is present and refusing. `--route real` runs the fence (submit.fence: the flag, the confirmation, a pre-flight
under 24 hours old that holds, a clean tagged tree, S1 to S6) and refuses `route-unsafe` unless every condition holds; and
even then this kit tag builds no connection to IBM (P5.2), so it submits nothing: with no service it cannot show S2, S5 and
S6. No code here connects to IBM.

A drive that is refused before its first job makes nothing (it makes only the run directories it needs, and removes those it
made if it is refused first). The records of a job that ran are the unit's, kept: S1 (once only) refuses a second look at them,
and an incomplete unit is contributed as `unit-incomplete`.
"""
import contextlib
import datetime
import io
import json
import os
from pathlib import Path

from qro import p5_unit as U
from qro.refusal import Refused
from qro_kit import _qf, submit
from qro_kit.crate import CrateError

CODE_STOPPED, CODE_NOT_HOLDING = 4, 3


def utc(dt):
    if dt.tzinfo is None:
        raise ValueError("a time without a zone: refusing to guess whether it is local or UTC")
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def read_unit(unit_dir, source_text, divisor_hint=None):
    """(UNIT.json as a dict, its SHA-256, {device: (manifest, its SHA-256)}) with every bundle held (unit_bundle.check)."""
    q = _qf.load("bundle")
    from qro_kit import unit_bundle
    path = Path(unit_dir) / "UNIT.json"
    try:
        data = path.read_bytes()
        doc = q.bundle.load_json(data)
    except (OSError, UnicodeDecodeError, ValueError) as x:
        raise CrateError(f"{path}: unreadable ({type(x).__name__})") from None
    divisor = doc.get("shots_divisor")
    kind = doc.get("kind")
    if kind not in U.DEVICE_SETS or type(divisor) is not int:
        raise CrateError(f"{path}: names no kind or divisor the kit reads")
    bundles = {}
    for device in U.DEVICE_SETS[kind]:
        m, digest, problems = unit_bundle.check(Path(unit_dir) / device / "bundle", source_text, divisor, kind)
        if problems:
            raise Refused("metadata-generated", f"{device}/bundle", "the bundle does not hold: " + "; ".join(problems[:3]))
        bundles[device] = (m, digest)
    if doc.get("bundles") != [bundles[d][1] for d in U.DEVICE_SETS[kind]]:
        raise Refused("metadata-generated", "UNIT.json", "its bundle digests are not the manifests' SHA-256")
    return doc, q.bundle.sha256(data), bundles


def same_circuit_checks(q, manifest, bundle_dir, entry):
    """Each QPY file loaded and held to its frozen gate list, its commitment put in its metadata, and the runtime's own JSON
    encoding of it held to the gate list too. -> [(circuit, None, shots)] in PUB order (hw_run.py's)."""
    from qiskit import qpy
    from qiskit_ibm_runtime import RuntimeDecoder, RuntimeEncoder
    pubs = []
    for e in entry["circuits"]:
        data = (bundle_dir / (e["name"] + q.bundle.SUFFIX["isa"])).read_bytes()
        if q.bundle.sha256(data) != e["isa_sha256"]:
            raise Refused("metadata-generated", e["name"], "the QPY file is not the manifest's")
        frozen = q.bundle.load_json((bundle_dir / (e["name"] + q.bundle.SUFFIX["gates"])).read_bytes())
        (c,) = qpy.load(io.BytesIO(data))
        if not q.bundle.same_json(q.isa.gate_list(c), frozen):
            raise Refused("metadata-generated", e["name"], "the QPY file and the gate list are not the same circuit")
        c.metadata = {q.runner.COMMITMENT_KEY: e["commitment"]}
        wire = json.loads(json.dumps({"circuit": c}, cls=RuntimeEncoder), cls=RuntimeDecoder)["circuit"]
        if not q.bundle.same_json(q.isa.gate_list(wire), frozen) or wire.metadata != c.metadata:
            raise Refused("metadata-generated", e["name"], "the runtime's encoding of the circuit is not the frozen one")
        pubs.append((c, None, e["shots"]))
    return pubs


def decode_library(raw_text):
    """The raw payload read by the library's own decoder: each PUB's strings from BitArray.get_bitstrings()."""
    from qiskit_ibm_runtime.decoders.result_decoder import ResultDecoder
    result = ResultDecoder.decode(raw_text)
    out = []
    for pub in result:
        if list(pub.data.keys()) != ["meas"]:
            raise ValueError(f"a PUB's data is {list(pub.data.keys())}, not the one register 'meas'")
        out.append((pub.data.meas.get_bitstrings(), dict(pub.metadata)))
    return out


class LocalJob:
    """The local route's stand-in for IBM's job around a local one: an id, a created time, and the raw result as the
    runtime's JSON encoding, handed over only once the job line is anchored."""

    def __init__(self, local, anchored):
        self.local = local
        self.anchored = anchored
        self.id = "dryrun-" + os.urandom(8).hex()
        self.created = datetime.datetime.now(datetime.timezone.utc)
        self.finished = None

    def job_id(self):
        return self.id

    def raw(self):
        if not self.anchored():
            raise RuntimeError("the stand-in job was asked for its result before the job line was committed and pushed: "
                               "the anchor's order is broken")
        from qiskit_ibm_runtime import RuntimeEncoder
        text = json.dumps(self.local.result(), cls=RuntimeEncoder)
        self.finished = datetime.datetime.now(datetime.timezone.utc)
        return text

    def state(self):
        try:
            self.local.result()
        except Exception:
            return "ERROR"
        return "DONE"


def local_calls(device):
    """The runner's calls for a local job."""
    def metrics(job, payload):
        finished = job.finished or job.created
        return {"backend": device, "dry_run": True, "job": {"created": utc(job.created)}, "job_id": job.job_id(),
                "metrics": {"timestamps": {"created": utc(job.created), "finished": utc(finished),
                                           "running": utc(job.created)}},
                "result_metadata": json.loads(payload)["__value__"].get("metadata")}
    return {"created_utc": lambda h: utc(h.created), "wait": lambda h: h.state(), "fetch_raw": lambda h: h.raw(),
            "decode_library": decode_library,
            "status_of": lambda h: {"state": {"status": h.state()}, "usage": None}, "metrics_of": metrics}


def check_cli(q):
    """The fixer's own command line, in process: (exit code, its output)."""
    def run(paths):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = q.fixer.main(["check", *paths])
        return rc, buf.getvalue()
    return run


def control_holds(q, manifest, run_dir, job_name):
    """Both PUBs of a control job judged from the records written: (True, '') or (False, which does not hold)."""
    entry = q.bundle.job(manifest, job_name)
    for e in entry["circuits"]:
        record = json.loads(q.runner.record_path(run_dir, job_name, e).read_text(encoding="ascii"))
        counts = {tuple(ones): n for ones, n in record["counts"]}
        answer = U.KNOWN_COMPLEMENT if e["name"] == "known-complement" else U.KNOWN_ANSWER
        verdict = q.decode.known_answer(counts, answer, U.M)
        if not verdict["holds"]:
            return False, f"{e['name']}: the modal outcome is {verdict['modal']}, not {verdict['expected']}"
    return True, ""


def drive(unit_dir, *, route="local", flag=False, confirm=None, tree, service=None, now=None, log=print, only=None):
    """Run the unit's jobs. Returns 0 when all 18 ran and every control job held; CODE_NOT_HOLDING (3) when a control job did
    not hold (the unit stops, nothing more is spent); CODE_STOPPED (4) when a job stopped after its submission. Raises Refused
    before a job is sent (kit-dirty, route-unsafe, once-only, spend-cap, and the rest) and CrateError for a directory the kit
    will not use. `only` limits the jobs to a set of (device, job name), for tests."""
    state = tree()
    now = now or datetime.datetime.now(datetime.timezone.utc)
    unit_dir = Path(unit_dir)
    source = (_qf.VENDOR / "circuit-ed767c01bd4b851d.qasm").read_text(encoding="ascii")
    q = _qf.load()
    doc, unit_digest, bundles = read_unit(unit_dir, source)
    if route == "real":
        _real(unit_dir, unit_digest, bundles, flag=flag, confirm=confirm, tree=tree, now=now, service=service, q=q)
    elif route != "local":
        raise CrateError(f"{route!r} is no route of the kit: local or real")
    elif doc["kind"] != "simulator":
        raise Refused("kind-mismatch", "UNIT.json", f"the local route runs a simulator unit; this unit is {doc['kind']!r}")
    if doc["kit_commit"] != state["commit"]:
        raise Refused("kit-dirty", "UNIT.json", "the unit was frozen by another commit of the kit than the one running")
    for device, (m, _d) in bundles.items():
        for j in m["jobs"]:
            submit.check_cap(j["max_execution_time"], U.parse_job_name(j["job"])[0], f"{device} {j['job']}")
    import qiskit
    import qiskit_ibm_runtime
    from qiskit_ibm_runtime import IBMBackend
    from qiskit_ibm_runtime.fake_provider.local_service import QiskitRuntimeLocalService
    from qro_kit import unit_bundle
    if (qiskit.__version__, qiskit_ibm_runtime.__version__) != (unit_bundle.QISKIT, unit_bundle.RUNTIME):
        raise CrateError(f"qiskit {qiskit.__version__} and qiskit-ibm-runtime {qiskit_ibm_runtime.__version__}: the kit is "
                         f"pinned to {unit_bundle.QISKIT} and {unit_bundle.RUNTIME}")
    local = QiskitRuntimeLocalService()
    backends = {}
    for device, (m, _d) in bundles.items():
        backend = local.backend(device)
        simulator = bool(getattr(backend.configuration(), "simulator", True))
        kind = q.runner.kind_from(isinstance(backend, IBMBackend), False, simulator)
        if kind != m["kind"] or backend.name != m["backend"]:
            raise Refused("kind-mismatch", device, f"the backend object is of kind {kind!r}; the bundle binds {m['kind']!r}")
        backends[device] = backend
    made_dirs = []
    charged = 0                                     # a local job is charged nothing; a real route reads IBM's metrics
    try:
        for p, slot, kind in U.job_order():
            device = U.DEVICE_SETS[doc["kind"]][slot]
            name = U.job_name(kind, p)
            if only is not None and (device, name) not in only:
                continue
            manifest, mdigest = bundles[device]
            run_dir = unit_dir / device / "run"
            if not run_dir.is_dir():
                os.mkdir(run_dir)
                made_dirs.append(run_dir)
            entry = q.bundle.job(manifest, name)
            if kind == "film" and not (q.runner.files(run_dir, U.job_name("control", p))["verdict"].exists()):
                raise Refused("known-answer", f"{device} {name}", "a film job follows its pass's control job, and this "
                                                                    "one's verdict is not in the records")
            submit.permit(q.runner, manifest, name, run_dir, charged)
            pubs = same_circuit_checks(q, manifest, unit_dir / device / "bundle", entry)
            config = backends[device].configuration()
            delay = getattr(config, "default_rep_delay", None) if getattr(config, "dynamic_reprate_enabled", False) else None
            sampler, sent = submit.sampler_for(backends[device], entry["max_execution_time"], delay)
            if not q.bundle.same_json(sent, manifest["options"]):
                raise Refused("metadata-generated", f"{device} {name}",
                              f"SamplerV2 would send the options {sent}, not the manifest's {manifest['options']}")
            line_path = q.runner.files(run_dir, name)["line"]

            def submit_job(sampler=sampler, pubs=pubs, line_path=line_path, manifest=manifest, name=name, run_dir=run_dir):
                job = submit.send(q.runner, sampler, pubs, manifest, name, run_dir, charged)
                return LocalJob(job, lambda: q.anchor.anchored(line_path))

            def anchor_line(path, name=name, mdigest=mdigest, device=device):
                return q.anchor.commit_and_push(path, f"hardware job line: {name} of bundle {mdigest[:16]} on {device}, "
                                                      "before any result")
            not_ready = q.anchor.ready(unit_dir / device / "bundle", run_dir)
            if not_ready:
                raise Refused("once-only", f"{device} {name}", "; ".join(not_ready))
            log(f"{device} {name}: " + ", ".join(f"{e['name']} {e['shots']}" for e in entry["circuits"]))
            try:
                rc = q.runner.run(manifest, mdigest, name, run_dir, (), backend_name=backends[device].name,
                                  kind=manifest["kind"], submit=submit_job, job_id=lambda h: h.job_id(),
                                  anchor=anchor_line, check_cli=check_cli(q),
                                  now_utc=lambda: utc(datetime.datetime.now(datetime.timezone.utc)), log=log,
                                  **local_calls(device))
            except q.runner.Refused as x:
                raise Refused("once-only", f"{device} {name}", str(x)) from None
            except q.runner.Stopped as x:
                log(f"STOPPED: {x}")
                return CODE_STOPPED
            if rc != 0:
                log(f"STOPPED: {device} {name}: the known answer does not hold; nothing more is spent")
                return CODE_NOT_HOLDING
            if kind == "control":
                holds, why = control_holds(q, manifest, run_dir, name)
                if not holds:
                    log(f"STOPPED: {device} {name} does not hold ({why}); nothing more is spent")
                    return CODE_NOT_HOLDING
    except BaseException:
        if not _any_job(unit_dir, bundles):         # nothing was sent: the run directories this drive made go
            for d in reversed(made_dirs):
                with contextlib.suppress(OSError):
                    os.rmdir(d)
        raise
    return 0


def _any_job(unit_dir, bundles):
    """Whether any run directory of the unit holds a file: a drive that sent nothing leaves nothing."""
    return any(any((Path(unit_dir) / d / "run").glob("*")) for d in bundles if (Path(unit_dir) / d / "run").is_dir())


def _real(unit_dir, unit_digest, bundles, *, flag, confirm, tree, now, service, q):
    """The real route's fence, and then its stop: this kit tag has no way to connect to IBM."""
    def rules():
        if service is None:
            raise Refused("route-unsafe", "the service", "this kit tag builds no connection to IBM: S2, S5 and S6 cannot be "
                                                          "shown, and nothing is submitted")
        submit.check_usage(service.usage())
        submit.check_plan(q.account.plan_of(service)[0])
        from qiskit_ibm_runtime import IBMBackend
        for device, (m, _d) in bundles.items():
            submit.check_backend(q.runner, service.backend(device), m, IBMBackend)
    submit.fence(unit_dir, unit_digest, flag=flag, confirm=confirm, tree=tree, now=now, rules=rules)
    raise Refused("route-unsafe", "--route real", "this kit tag builds no connection to IBM: the real route submits nothing")
