"""P5's unit: the recipe, what it costs, how a unit crate is read, what it states, and intake (P5's design, items 1, 8
and 9; P5.1). Standard library and qro only: the kit (qro_kit/) imports this module and this module imports nothing of the
kit, so that the checker's path never needs qiskit, numpy or mpmath.

THE RECIPE (`RECIPE`, `recipe(divisor)`): one free-tier unit is 18 jobs on three devices, in three passes. A pass runs on
each device in the order kingston, marrakesh, fez, and on a device a control job and then a film job, each submitted only
after the one before is final: K.control K.film M.control M.film F.control F.film, three times. A control job has two
PUBs at 2,048 shots (`known-answer`, X on 0, 1, 3, 7, 12, and `known-complement`, X on the other eleven of the sixteen),
a film job three at 16,384 (`law` in Z, `coherence-xx` and `coherence-yy`): 9 x (2 x 2,048 + 3 x 16,384) = 479,232 shots.
A film job is submitted only after its pass's control job holds on both PUBs. `recipe_sha256(divisor)` is the SHA-256 of
the recipe's canonical JSON, a unit's identity of kind: a unit built with `--shots-divisor N` (the local route only) has
the shots divided by N in its recipe and so another digest, recorded as `shots_divisor`, never a unit of the first recipe.

THE COST (`COST_MODELS`, exact Fractions, never float): v0's 65 jobs charged 353 s. Model (a) charges 9/24576 s a shot,
(b) 1.6871 s and 0.29741 ms a shot, (c) 2 s and 0.35 ms a shot; a job's estimate is the model's seconds for all its PUBs'
shots, rounded up to a whole second, and `JOB_ESTIMATE` is the highest of the three for each job: control 4 s, film 20 s,
and a unit 216 s (9 x 24). RU_PER_SECOND is v0's 5.448135 RU over 353 s, rounded to 0.015434. tests/p5crates recomputes
the three models and the ratio from v0's metrics. The spend ceiling (270 s a unit) and the caps (15 s a control job and 60
s a film job) are Logan's, approved 2026-11-08; qro_kit/submit.py holds them, and they are here so that a test needs no
qiskit to state them.

HOW A UNIT CRATE IS READ (`read`, the seam P3 reads units through): `read(crate_dir) -> Unit` from the crate's metadata
alone, as intake does. A Unit knows its kind (from its devices' `qro:deviceKind`), its recipe digest, its devices in the
recipe's order, its jobs with their PUBs and the raw counts (through p1_decode.pub_counts, so a reader re-derives and
never trusts), each device's chain, the kit's commit and tag and the contributor, and its `status()`.

WHAT A UNIT STATES (`status`, derived, never stored): `unit-incomplete` when a device lacks a planned job of its bundle's
manifest or holds one with no raw result (a status file instead), and `complete[device]` for each device; and
`not-interleaved` when the jobs present, in the order of their execution starts (the execution span of a real unit; the
line's `submitted_at` of a local one, which the unit's clock names), do not run the devices as the recipe orders them,
K M F three times, judged on the jobs present. Both are kept, not refused.

INTAKE (`intake`; `python -m qro.p5_unit intake CRATE [--record FILE]`): (1) the checker's nine steps with every parcel's
steps; (2) the complement and every control PUB: both PUBs of every control job decoded under the Decode's order and
judged by p1_decode.known_answer_verdict against their own X sets, a failure refused `known-answer` naming the PUB (the
checker holds only the one PUB each Decode names; the complement is held here: a stated limit); (3) the status. Exit 0
accepted (with any KEPT lines), 1 a refusal, 2 misuse, 3 the tool failing. `--record` writes one canonical JSON line,
`qro-crate/unit-intake/v1`, beside the crate and never in it.
"""
import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from qro import canonical, checker, p1_decode, p1_forms, p1_records as rec, reader
from qro.p1_graph import GraphError, Index
from qro.refusal import Refused

RECIPE_NAME = "qro-unit/1"
UNIT_FORMAT = "qro-crate/unit/v1"
INTAKE_FORMAT = "qro-crate/unit-intake/v1"
STOCK = "pauli-4x4"
PROGRAM = "sampler"
DECODE = "quantum_film.ibm.decode/v1"
ROUTE = "ibm-direct"
BUNDLE_FORMAT = "quantum-film/hardware-bundle/v1"
M = 16
KNOWN_ANSWER = (0, 1, 3, 7, 12)
KNOWN_COMPLEMENT = tuple(q for q in range(M) if q not in KNOWN_ANSWER)
PAIR = (0, 1)
SOURCE_SHA256 = "ed767c01bd4b851d08993da80f715676e345fc95a10f3bda05400f738e400b36"
SOURCE_PATH = "2026-09-25/p3/circuit-ed767c01bd4b851d.qasm"       # in a crate, where P2 finds it by digest
LICENSE_PATH = "LICENSE-quantum-film"
UNIT_DIR = "unit"
UNIT_FILE = "unit/UNIT.json"
DEVICE_SETS = {"qpu": ("ibm_kingston", "ibm_marrakesh", "ibm_fez"),
               "simulator": ("fake_kingston", "fake_marrakesh", "fake_fez")}
PASSES = 3
Z = "Z" * M
KINDS_OF_JOB = ("control", "film")
CIRCUITS = {"control": (("known-answer", "known-answer", Z), ("known-complement", "known-answer", Z)),
            "film": (("law", "law", Z), ("coherence-xx", "coherence", "XX" + "Z" * (M - 2)),
                     ("coherence-yy", "coherence", "YY" + "Z" * (M - 2)))}
SHOTS = {"control": 2048, "film": 16384}
CAPS = {"control": 15, "film": 60}                  # max_execution_time, whole seconds (S4; Logan, 2026-11-08)
CEILING = 270                                       # seconds a unit may be charged in all (S3; 1.25 x 216)
OPTIONS = {"dynamical_decoupling": {"enable": False}, "execution": {"init_qubits": True},
           "twirling": {"enable_gates": False, "enable_measure": False}}
TOTAL_SHOTS = PASSES * 3 * sum(SHOTS[k] * len(CIRCUITS[k]) for k in KINDS_OF_JOB)
NOT_INTERLEAVED = "the difference is the device's-and-its-time's"
INCOMPLETE, INTERLEAVED = "unit-incomplete", "not-interleaved"

# -- the cost, in exact arithmetic -------------------------------------------------------------------------------------
COST_MODELS = {"a": lambda shots: Fraction(9, 24576) * shots,
               "b": lambda shots: Fraction("1.6871") + Fraction("0.00029741") * shots,
               "c": lambda shots: Fraction(2) + Fraction("0.00035") * shots}
V0_CHARGE_SECONDS = 353
V0_RESOURCE_UNITS = Fraction("5.448135")
RU_PER_SECOND = Fraction("0.015434")


def job_shots(kind, divisor=1):
    """All the shots of one job of this kind: its PUBs' together."""
    return len(CIRCUITS[kind]) * shot_count(kind, divisor)


def shot_count(kind, divisor=1):
    """One PUB's shots in a job of this kind, after the divisor, which must divide it."""
    if type(divisor) is not int or divisor < 1 or SHOTS[kind] % divisor:
        raise ValueError(f"a shots divisor is a positive whole number that divides {SHOTS[kind]}, not {divisor!r}")
    return SHOTS[kind] // divisor


def estimates(kind, divisor=1):
    """{model: seconds} for one job, each rounded up to a whole second."""
    return {m: math.ceil(f(job_shots(kind, divisor))) for m, f in COST_MODELS.items()}


JOB_ESTIMATE = {k: max(estimates(k).values()) for k in KINDS_OF_JOB}          # control 4 s, film 20 s
UNIT_ESTIMATE = PASSES * 3 * sum(JOB_ESTIMATE.values())                       # 216 s
UNIT_RU = UNIT_ESTIMATE * RU_PER_SECOND


# -- the recipe --------------------------------------------------------------------------------------------------------
def job_name(kind, n):
    return f"{kind}-{n}"


def parse_job_name(name):
    """(kind, pass) of a job's name, or ValueError."""
    kind, _, n = str(name).rpartition("-")
    if kind not in KINDS_OF_JOB or not n.isascii() or not n.isdigit() or not 1 <= int(n) <= PASSES \
            or n != str(int(n)):
        raise ValueError(f"{name!r} is no job of the recipe")
    return kind, int(n)


def job_order():
    """[(pass, device slot, kind)] of the 18 jobs, in the order they are submitted."""
    return [(p, s, k) for p in range(1, PASSES + 1) for s in range(3) for k in KINDS_OF_JOB]


def jobs_of_device(divisor=1):
    """[(job name, kind, pass, [(pub, name, role, basis, shots)])]: one device's six jobs, in the recipe's order."""
    out = []
    for p in range(1, PASSES + 1):
        for k in KINDS_OF_JOB:
            out.append((job_name(k, p), k, p, [(i, *c, shot_count(k, divisor)) for i, c in enumerate(CIRCUITS[k])]))
    return out


def recipe(divisor=1):
    """The recipe as data: what recipe_sha256 digests."""
    return {"name": RECIPE_NAME, "stock": STOCK, "program": PROGRAM, "decode": DECODE, "route": ROUTE,
            "devices": ["kingston", "marrakesh", "fez"], "passes": PASSES,
            "order": "by pass, each device in turn, a control job and then a film job",
            "gate": "a film job is submitted only after its pass's control job holds on both PUBs",
            "known_answer": list(KNOWN_ANSWER), "known_complement": list(KNOWN_COMPLEMENT), "pair": list(PAIR),
            "options": OPTIONS, "shots_divisor": divisor,
            "jobs": [{"job": name, "kind": k, "pass": p, "max_execution_time": CAPS[k],
                      "circuits": [{"pub": pub, "name": n, "role": r, "basis": b, "shots": s}
                                   for pub, n, r, b, s in pubs]}
                     for name, k, p, pubs in jobs_of_device(divisor)]}


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def recipe_sha256(divisor=1):
    return hashlib.sha256(canonical_json(recipe(divisor))).hexdigest()


RECIPE = recipe()


_HEAD = ["OPENQASM 2.0;", 'include "qelib1.inc";', f"qreg q[{M}];"]
ROTATIONS = {"law": (), "coherence-xx": ("h q[0];", "h q[1];"),
             "coherence-yy": ("sdg q[0];", "h q[0];", "sdg q[1];", "h q[1];")}


def logical_qasm(name, source_text):
    """A logical circuit's OpenQASM 2 text, as Quantum-Film's bundle.logical_qasm derives it (quantum_film/ibm/bundle.py at
    3a73823), and for the complement the same rule with the other X set: the source's gates (or the X gates), the pair's
    rotations, a barrier on all sixteen and a measure of each into its own bit."""
    if name == "known-answer":
        body = [f"x q[{q}];" for q in KNOWN_ANSWER]
    elif name == "known-complement":
        body = [f"x q[{q}];" for q in KNOWN_COMPLEMENT]
    elif name in ROTATIONS:
        lines = source_text.split("\n")
        if lines[:3] != _HEAD or lines[-1] != "":
            raise ValueError("the source is not an OpenQASM 2 file of one 16-qubit register")
        body = lines[3:-1] + list(ROTATIONS[name])
    else:
        raise ValueError(f"no circuit {name!r} in the recipe")
    measure = ["barrier " + ",".join(f"q[{q}]" for q in range(M)) + ";"] + \
        [f"measure q[{q}] -> meas[{q}];" for q in range(M)]
    return "\n".join(_HEAD + [f"creg meas[{M}];"] + body + measure) + "\n"


def device_set(kind):
    if kind not in DEVICE_SETS:
        raise ValueError(f"{kind!r} is no kind of unit: {sorted(DEVICE_SETS)}")
    return DEVICE_SETS[kind]


# -- reading a unit ------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class PubView:
    id: str
    index: int
    name: str                   # the circuit's name: known-answer, known-complement, law, coherence-xx, coherence-yy
    role: str
    basis: str


@dataclass(frozen=True)
class JobView:
    id: str                     # the provider's job id
    entity: str                 # the Job's @id
    name: str                   # control-1 ... film-3
    kind: str                   # control or film
    pass_: int
    device: str
    pubs: tuple                 # of PubView, in PUB order; () for a job that made no result
    raw: object                 # the raw result's path in the crate, or None
    line: str                   # the line's path in the crate
    submitted_at: str           # the line's, on the unit's clock
    start: object               # the execution span's start (the profile's time spelling), or None


@dataclass(frozen=True)
class Status:
    complete: dict              # {device: bool}
    missing: tuple              # of (device, job name, "missing" or "failed")
    interleaved: bool
    clock: str                  # the clock the order was read on: "provider" or "local"
    order: tuple                # the devices as the jobs present ran them, repeats collapsed

    @property
    def incomplete(self):
        return not all(self.complete.values())

    def lines(self):
        out = [f"KEPT {INCOMPLETE}: {d} {j} {why}" for d, j, why in self.missing]
        if not self.interleaved:
            out.append(f'KEPT {INTERLEAVED}: "{NOT_INTERLEAVED}"')
        return out

    def sentences(self):
        """What the unit states of itself, as the controls' runner compares it: the kept refusals' labels and the study's
        sentence."""
        got = set()
        if self.incomplete:
            got.add(INCOMPLETE)
        if not self.interleaved:
            got.add(NOT_INTERLEAVED)
            got.add(INTERLEAVED)
        return frozenset(got)


class Unit:
    """A unit crate, read from its metadata (and its files, where a count or a chain is asked for)."""

    def __init__(self, crate_dir, md):
        self.crate_dir, self.md = Path(crate_dir), md
        self.idx = Index(md)
        units = self.idx.of_type("qro:Unit")
        if len(units) != 1:
            raise GraphError(f"the crate holds {len(units)} qro:Unit entities, not one")
        self.entity = units[0]
        devices = self.idx.of_type("IndividualProduct")
        kinds = {d.get("qro:deviceKind") for d in devices}
        if len(kinds) != 1 or not kinds <= set(DEVICE_SETS):
            raise GraphError(f"the unit's devices are of kinds {sorted(map(str, kinds))}, not one of {sorted(DEVICE_SETS)}")
        self.kind = kinds.pop()
        names = {d["name"]: d for d in devices}
        self.devices = tuple(n for n in DEVICE_SETS[self.kind] if n in names)
        if set(names) != set(self.devices):
            raise GraphError(f"the unit's devices are {sorted(names)}, not {list(DEVICE_SETS[self.kind])}")
        self._jobs = None

    # the unit's own terms
    @property
    def recipe_sha256(self):
        return self.entity.get("qro:recipe")

    @property
    def shots_divisor(self):
        """The shots divisor of the unit's recipe: the divisor whose recipe digest the unit states, 1 for the full recipe;
        None where no divisor of the recipe's gives it (the generator refuses such a unit, GU2)."""
        for d in range(1, min(SHOTS.values()) + 1):
            if all(n % d == 0 for n in SHOTS.values()) and recipe_sha256(d) == self.recipe_sha256:
                return d
        return None

    @property
    def contributor(self):
        return self.entity.get("qro:contributor", "withheld")

    @property
    def kit_tag(self):
        return self.entity.get("qro:kitTag", "unknown")

    @property
    def kit_commit(self):
        commits = {j.get("qro:kitCommit", "unknown") for j in self.idx.of_type("qro:Job")}
        return commits.pop() if len(commits) == 1 else "unknown"

    @property
    def clock(self):
        clocks = {j.get("qro:clock") for j in self.idx.of_type("qro:Job")}
        return clocks.pop() if len(clocks) == 1 and None not in clocks else "local"

    def _manifest(self, device):
        return rec.manifest((self.crate_dir / f"{UNIT_DIR}/{device}/bundle/manifest.json").read_bytes(), device)

    def chain(self, device):
        """The physical qubits of logical qubits 0 to 15 the device's bundle fixed, from its manifest."""
        doc = rec.parse((self.crate_dir / f"{UNIT_DIR}/{device}/bundle/manifest.json").read_bytes(), device)
        return tuple(doc["jobs"][0]["circuits"][0]["chain"])

    def planned(self, device):
        """The job names the device's bundle plans, in its order."""
        return [name for name, _ in self._manifest(device).jobs]

    def _read_jobs(self):
        out = []
        for j in sorted(self.idx.of_type("qro:Job"), key=lambda e: e["@id"]):
            device = self.idx.one(j, "qro:device")["name"]
            line_ref = self.idx.one(j, "qro:line")["@id"]
            stem = line_ref.rsplit("/", 1)[-1]
            if not stem.endswith("-line.json"):
                raise GraphError(f"{j['@id']}: its line {line_ref} is no <job>-line.json")
            name = stem[:-len("-line.json")]
            kind, p = parse_job_name(name)
            line = rec.line((self.crate_dir / line_ref).read_bytes(), line_ref)
            pubs = tuple(sorted((PubView(e["@id"], self.idx.pub_index(e), self._circuit_name(e), e["qro:role"],
                                         e["qro:basis"])
                                 for e in self.idx.refs_of_type(j, "object", "qro:Pub")), key=lambda v: v.index))
            raws = self.idx.refs_of_type(j, "result", "qro:RawResult")
            start = j.get("startTime")
            out.append(JobView(line.job_id, j["@id"], name, kind, p, device, pubs, raws[0]["@id"] if raws else None,
                               line_ref, line.submitted_at, None if start in (None, "unknown") else start))
        return out

    def _circuit_name(self, pub):
        """A PUB's circuit name: the last part of its record's file name, <job>-pub<k>-<circuit>.json."""
        stem = self.idx.one(pub, "qro:record")["@id"].rsplit("/", 1)[-1]
        head, sep, circuit = stem[:-len(".json")].partition("-pub")
        return circuit.partition("-")[2] if sep else ""

    def jobs(self, device=None, role=None, pass_=None, kind=None):
        """The jobs the crate carries, by device, by the role of a PUB, by pass, by kind of job (control or film), in the
        order they were submitted (the recipe's), the failed ones included (`raw` is None)."""
        if self._jobs is None:
            order = {(p, s, k): i for i, (p, s, k) in enumerate(job_order())}
            slots = {d: i for i, d in enumerate(self.devices)}
            self._jobs = sorted(self._read_jobs(), key=lambda v: order[(v.pass_, slots[v.device], v.kind)])
        return [v for v in self._jobs if (device is None or v.device == device) and (pass_ is None or v.pass_ == pass_)
                and (kind is None or v.kind == kind) and (role is None or any(p.role == role for p in v.pubs))]

    def counts(self, pub_id):
        """The decoded counts of a PUB, {the sorted tuple of qubits read 1: shots}: re-derived from the raw bytes."""
        return p1_decode.pub_counts(self.crate_dir, self.md, pub_id)

    def status(self):
        """What the unit states of itself (the module docstring)."""
        jobs = self.jobs()
        have = {(v.device, v.name): v for v in jobs}
        missing, complete = [], {}
        for d in self.devices:
            ok = True
            for name in self.planned(d):
                v = have.get((d, name))
                if v is None or v.raw is None:
                    ok = False
                    missing.append((d, name, "missing" if v is None else "failed"))
            complete[d] = ok
        keyed = sorted(jobs, key=lambda v: (p1_forms.parse_time(v.start or v.submitted_at, "Z"),
                                            (v.pass_, self.devices.index(v.device), v.kind)))
        seq = [v.device for v in keyed]
        collapsed = tuple(d for i, d in enumerate(seq) if i == 0 or seq[i - 1] != d)
        wanted = [v.device for v in jobs]                      # the recipe's order, on the jobs present
        want = tuple(d for i, d in enumerate(wanted) if i == 0 or wanted[i - 1] != d)
        timed = all(v.start is not None for v in jobs) and bool(jobs)
        return Status(complete, tuple(missing), collapsed == want, "provider" if timed else "local", collapsed)


def read(crate_dir):
    """The Unit a crate holds (GraphError where it holds none), from its metadata file alone: `read` does not check the
    crate; intake does."""
    path = Path(crate_dir) / canonical.DESCRIPTOR
    return Unit(crate_dir, reader.read(path.read_bytes()))


# -- intake ----------------------------------------------------------------------------------------------------------------
def control_verdicts(unit):
    """[(pub id, Verdict)] for both PUBs of every control job that has a result, each judged under the Decode's order
    against the X set of its own circuit (found in the crate by the digest its record names)."""
    out = []
    for v in unit.jobs(kind="control"):
        for p in v.pubs:
            record = unit.idx.one(unit.idx.get(p.id), "qro:record")["@id"]
            digest = rec.parse((unit.crate_dir / record).read_bytes(), record)["source"]["circuit_sha256"]
            files = unit.idx.files_by_sha256(digest)
            if not files:
                raise p1_decode.KnownAnswerError(f"no file of the crate has the circuit {digest} of {p.id}")
            expected = p1_decode.expected_set((unit.crate_dir / files[0]["@id"]).read_bytes())
            out.append((p.id, p1_decode.known_answer_verdict(unit.counts(p.id), expected)))
    return out


@dataclass(frozen=True)
class Intake:
    digest: str                 # the crate's body digest
    status: Status
    verdicts: tuple             # of (pub id, holds)
    divisor: int = 1            # the shots divisor of the recipe the unit was built with; 1 is the full recipe

    def lines(self):
        """The first line says what was accepted: `unit`, or, for a unit built with `--shots-divisor N` (the local route),
        `unit scaled by shots divisor N`, so that a scaled unit is never taken for a unit of the full recipe by its line."""
        scaled = f" scaled by shots divisor {self.divisor}" if self.divisor != 1 else ""
        return [f"ACCEPTED {self.digest} unit{scaled}"] + self.status.lines()


def intake(crate_dir):
    """Intake of a unit crate: an Intake, or Refused (the checker's refusal, or `known-answer` naming the PUB whose
    verdict fails)."""
    checker.load()
    md = checker.check(crate_dir)
    unit = Unit(crate_dir, md)
    try:
        verdicts = control_verdicts(unit)
    except (GraphError, p1_decode.DecodeError, p1_decode.KnownAnswerError, rec.RecordError, p1_forms.RawFormError,
            KeyError, TypeError) as x:
        raise Refused("known-answer", "the unit's control jobs", f"{type(x).__name__}: {x}") from None
    for pub, v in verdicts:
        if not v.holds:
            raise Refused("known-answer", pub, f"a control PUB does not hold its answer: {v.text()}")
    return Intake(canonical.body_digest(md), unit.status(), tuple((p, v.holds) for p, v in verdicts), unit.shots_divisor)


def record_of(result, unit_commit="unknown", tool="unknown"):
    """The intake record, one canonical JSON line: `qro-crate/unit-intake/v1`."""
    s = result.status
    return canonical.compact({
        "format": INTAKE_FORMAT, "crate": result.digest, "verdict": "accepted",
        "complete": s.complete, "incomplete": s.incomplete, "missing": [list(m) for m in s.missing],
        "interleaved": s.interleaved, "interleave": "ok" if s.interleaved else NOT_INTERLEAVED,
        "order_clock": s.clock, "control_pubs_held": len(result.verdicts), "tool": tool, "unit_commit": unit_commit})


# -- the command line ------------------------------------------------------------------------------------------------
USAGE = "usage: python -m qro.p5_unit intake CRATE_DIR [--record FILE]"


class Misuse(ValueError):
    """The invocation is not the command's: exit 2."""


def _arguments(argv):
    if argv[:1] != ["intake"]:
        raise Misuse(USAGE)
    rest, crate, record = argv[1:], None, None
    i = 0
    while i < len(rest):
        if rest[i] == "--record" and record is None and i + 1 < len(rest):
            record = rest[i + 1]
            i += 2
        elif not rest[i].startswith("--") and crate is None:
            crate = rest[i]
            i += 1
        else:
            raise Misuse(f"{rest[i]}: not an option of this command, or given twice, or without its value; {USAGE}")
    if crate is None:
        raise Misuse(USAGE)
    return crate, record


def _inside(path, parent):
    try:
        return os.path.commonpath([os.path.realpath(path), os.path.realpath(parent)]) == os.path.realpath(parent)
    except ValueError:
        return False


def _verdict(argv):
    """(exit code, [lines])."""
    from qro.__main__ import directory_misuse
    try:
        crate, record = _arguments(argv)
        line = directory_misuse(crate)
        if line is not None:
            return 2, [line]
        if record is not None and (not record or _inside(record, crate) or os.path.lexists(record)):
            return 2, [f"{record}: the record is written beside the crate, never in it, and not over a file; {USAGE}"]
    except Misuse as x:
        return 2, [str(x)]
    try:
        result = intake(crate)
    except Refused as r:
        return 1, [f"REFUSED {r.name} at {r.where}: {r.detail}"]
    if record is not None:
        with open(record, "xb") as f:
            f.write(record_of(result))
    return 0, result.lines()


def main(argv, out=1, err=2):
    """The exit code, each line written whole to a descriptor, unbuffered, as `python -m qro check` writes its own."""
    from qro.__main__ import write
    try:
        code, lines = _verdict(argv)
    except BaseException as x:                              # a crash, an exit or an interrupt: never a refusal
        code, lines = 3, [f"FAILED: intake itself failed, {checker.describe(x)}; this is not a verdict"]
    try:
        for line in lines:
            write(out if code in (0, 1) else err, line)
    except Exception:
        return 3
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
