"""Quantum-Film's records and the 2026-10-14 read's, as P1's generators read them (P1's design, items 6 and 11; P1.2).
Standard library and P1.1's strict JSON reader only.

Each reader takes a file's bytes and its place in the crate (for the message), and returns the fields the generators
use, or raises RecordError naming the place and the reason: a record that is not in its format is a refusal of the
build, never a crash. Every record is read by `parse`, which also refuses a string UTF-8 cannot encode, at any depth
the strict reader admits, naming its field. The readers read what they need and ignore the rest of a record, which is
Quantum-Film's or the read's own: that a record agrees with the others, and with the raw result, is the generators'
guards (G1 to G11 of p1_generate), not these readers' business.

The formats, read from moth-quantum's quantum_film at 3a73823 and from the files themselves:
  - `quantum-film/hardware-bundle/v1`, a bundle's manifest: the device, stock, kind, route, program, decode and
    options every job of the bundle shares, the jobs and each job's circuits (name, role, basis, PUB index, shots,
    salt, commitment, and the digests of the logical circuit, the gate list, the QPY file and the ISA circuit),
    the compile's settings and versions, the README's digest, and the source circuit's path and digest;
  - `quantum-film/hardware-job/v1`, a job's line, written before any result was read: the job id, the bundle's
    digest, one commitment a PUB, and the fields the manifest also states;
  - `quantum-film/device-run/v1`, a PUB's decoded record, whose `digest` is the SHA-256 of the record without it
    as one line of sorted compact ASCII JSON (68 of 68 MEASURED);
  - Quantum-Film's metrics wrapper of IBM's job fields, which keeps IBM's `cost` and the rest verbatim;
  - `qro-crate/ibm-refetch/v0` and `qro-crate/ibm-results-refetch/v0`, the read of 2026-10-14 and its MANIFESTs.
And for Atlas: `commitments.jsonl`'s `quantum-film/commitment/v2` lines (v2 recomputed by commitment_v2) and the
provider's submit, status and score files.
"""
import hashlib
import json
import re
from dataclasses import dataclass

from qro import p1_commit, p1_forms

MANIFEST_FORMAT = "quantum-film/hardware-bundle/v1"
LINE_FORMAT = "quantum-film/hardware-job/v1"
DEVICE_RUN_FORMAT = "quantum-film/device-run/v1"
REFETCH_FORMAT = "qro-crate/ibm-refetch/v0"
RESULTS_FORMAT = "qro-crate/ibm-results-refetch/v0"
REFETCH_MANIFEST_FORMAT = "qro-crate/ibm-refetch-manifest/v0"
RESULTS_MANIFEST_FORMAT = "qro-crate/ibm-results-refetch-manifest/v0"
ATLAS_LINE_FORMAT = "quantum-film/commitment/v2"
COMMITMENT_V2 = "quantum-film/commitment/v2"
_NAMES = {str: "a string", int: "a whole number", list: "a list", dict: "an object", bool: "true or false"}


class RecordError(ValueError):
    """A record that is not in the shape a generator reads: where, and why."""


def _is(x, kind):
    return type(x) is kind if kind in (str, int, bool) else isinstance(x, kind)


def need(doc, what, *path, kind=str):
    """The value at `path` of nested objects in `doc`, which must be of `kind` (a bool is no int)."""
    x = doc
    for i, key in enumerate(path):
        if not isinstance(x, dict) or key not in x:
            raise RecordError(f"{what}: lacks {'.'.join(path[:i + 1])}")
        x = x[key]
    if not _is(x, kind):
        raise RecordError(f"{what}: {'.'.join(path)} is not {_NAMES[kind]}")
    return x


def parse(data, what):
    """A JSON object, strictly: no key twice, no NaN, no float past binary64, no integer past 2^63 - 1, nothing nested
    deeper than P1.1's reader reads, and no string, a key or a value, that UTF-8 cannot encode (a lone surrogate, which
    JSON can write as an escape and the generators would then fail to encode: a refusal of the record here, naming the
    field, never a crash there)."""
    doc = p1_forms.load_json(data, what, RecordError)
    if not isinstance(doc, dict):
        raise RecordError(f"{what}: not an object")
    place = _unencodable(doc)
    if place is not None:
        raise RecordError(f"{what}: {place} holds a string UTF-8 cannot encode (a lone surrogate)")
    return doc


_KEY = object()                     # a stack entry that asks a key of an object, before the key's value is asked


def _encodes(s):
    try:
        s.encode("utf-8")
        return True
    except UnicodeEncodeError:
        return False


def _unencodable(doc):
    """The place, as `a.b[0].c`, of the first string of `doc` that UTF-8 cannot encode, a key or a value, in the order
    the record writes them (None: none is). Asked without recursion, from an explicit stack, so that every string is
    asked at any depth the reader admits (P1.2's fifth verifier, D1: a recursive walk failed 1,000 levels down, where
    the reader admits about 3,000 on this host). A key UTF-8 cannot encode cannot be written in the place: the place is
    named as far as it can be, `a key of a.b`."""
    stack = [(doc, None, None)]                     # (a value, the step to it from its parent, the parent's own entry)
    while stack:
        entry = stack.pop()
        x, step, parent = entry
        if x is _KEY:
            if not _encodes(step):
                return f"a key of {_place(parent) or 'the document'}"
        elif isinstance(x, str):
            if not _encodes(x):
                return _place(entry) or "the document"
        elif isinstance(x, dict):
            for k, v in reversed(x.items()):            # pushed last first, so that each key is asked, then its value
                stack.append((v, k, entry))
                stack.append((_KEY, k, entry))
        elif isinstance(x, list):
            stack.extend((x[i], i, entry) for i in range(len(x) - 1, -1, -1))
    return None


def _place(entry):
    """`a.b[0].c`: the steps from the document down to the value of a stack entry, followed up its parents, without
    recursion ("" for the document itself)."""
    steps = []
    while entry[2] is not None:
        steps.append(entry[1])
        entry = entry[2]
    parts = []
    for step in reversed(steps):
        parts.append(f"[{step}]" if isinstance(step, int) else (f".{step}" if parts else step))
    return "".join(parts)


def instant(text, what, zone="Z"):
    """A time of a record as an aware UTC datetime (a fraction of one to six digits, zeros allowed)."""
    try:
        return p1_forms.parse_time(text, zone)
    except ValueError as x:
        raise RecordError(f"{what}: {x}") from None


def formatted(doc, what, expect):
    got = need(doc, what, "format")
    if got != expect:
        raise RecordError(f"{what}: format is {got!r}, not {expect}")


# -- Quantum-Film's bundle manifest -----------------------------------------------------------------------------------
@dataclass(frozen=True)
class Circuit:
    name: str
    role: str
    basis: str
    pub: int
    shots: int
    salt: str
    commitment: str
    circuit_sha256: str          # the logical circuit's .qasm file
    gates_sha256: str            # the transpiled circuit's gate list
    isa_sha256: str              # the QPY file that was sent
    qasm3_sha256: str            # the ISA circuit in OpenQASM 3


@dataclass(frozen=True)
class Manifest:
    backend: str
    stock: str
    kind: str
    route: str
    program: str
    decode: str
    options: dict
    options_sha256: str
    readme_sha256: str
    source_path: str
    source_sha256: str
    qiskit: str
    level: int
    seed: int
    jobs: tuple                  # of (job name, tuple of Circuit in PUB order)

    def circuits(self):
        return [c for _, cs in self.jobs for c in cs]


def manifest(data, what):
    doc = parse(data, what)
    formatted(doc, what, MANIFEST_FORMAT)
    jobs = []
    for i, j in enumerate(need(doc, what, "jobs", kind=list)):
        at = f"{what} jobs[{i}]"
        if not isinstance(j, dict):
            raise RecordError(f"{at}: not an object")
        circuits = []
        for k, c in enumerate(need(j, at, "circuits", kind=list)):
            cat = f"{at} circuits[{k}]"
            if not isinstance(c, dict):
                raise RecordError(f"{cat}: not an object")
            circuits.append(Circuit(
                need(c, cat, "name"), need(c, cat, "role"), need(c, cat, "basis"), need(c, cat, "pub", kind=int),
                need(c, cat, "shots", kind=int), need(c, cat, "salt"), need(c, cat, "commitment"),
                need(c, cat, "circuit_sha256"), need(c, cat, "gates_sha256"), need(c, cat, "isa_sha256"),
                need(c, cat, "qasm3_sha256")))
        if [c.pub for c in circuits] != list(range(len(circuits))) or not circuits:
            raise RecordError(f"{at}: the PUB indexes of its circuits are not 0 to {len(circuits) - 1} in order")
        jobs.append((need(j, at, "job"), tuple(circuits)))
    names = [n for n, _ in jobs]
    if len(set(names)) != len(names) or not jobs:
        raise RecordError(f"{what}: job names are not one or more, each once")
    return Manifest(
        need(doc, what, "backend"), need(doc, what, "stock"), need(doc, what, "kind"), need(doc, what, "route"),
        need(doc, what, "program"), need(doc, what, "decode"), need(doc, what, "options", kind=dict),
        need(doc, what, "options_sha256"), need(doc, what, "readme_sha256"), need(doc, what, "source", "path"),
        need(doc, what, "source", "sha256"), need(doc, what, "versions", "qiskit"),
        need(doc, what, "compile", "optimization_level", kind=int), need(doc, what, "compile", "seed_transpiler",
                                                                          kind=int), tuple(jobs))


# -- a job's line -----------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Line:
    job_id: str
    bundle_sha256: str
    commitments: tuple
    stock: str
    kind: str
    route: str
    backend: str
    program: str
    submitted_at: str


def line(data, what):
    doc = parse(data, what)
    formatted(doc, what, LINE_FORMAT)
    commitments = need(doc, what, "commitments", kind=list)
    if not commitments or any(type(c) is not str for c in commitments):
        raise RecordError(f"{what}: commitments is not a list of one string or more")
    return Line(need(doc, what, "job_id"), need(doc, what, "bundle_sha256"), tuple(commitments),
                *[need(doc, what, k) for k in ("stock", "kind", "route", "backend", "program", "submitted_at")])


# -- a PUB's decoded record -------------------------------------------------------------------------------------------
def record_digest(doc):
    """The `digest` Quantum-Film writes in a device-run record: the SHA-256 of the record without it, as one line of
    sorted compact ASCII JSON."""
    body = {k: v for k, v in doc.items() if k != "digest"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
                          ).hexdigest()


@dataclass(frozen=True)
class DeviceRun:
    doc: dict
    digest: str
    stock: str
    role: str
    basis: str
    source: dict
    counts: dict                 # {the sorted tuple of qubits read 1: shots}

    def fields(self, what):
        """The fourteen inputs of the commitment, as this record gives them, each of its type (TypeError never: a
        wrong type is a RecordError)."""
        out = {}
        for name, kind in p1_commit.FIELDS:
            owner = self.doc if name in ("stock", "role", "basis") else self.source
            if name not in owner or type(owner[name]) is not kind:
                raise RecordError(f"{what}: {name} is not {_NAMES[kind]}")
            out[name] = owner[name]
        return out


def device_run(data, what):
    doc = parse(data, what)
    formatted(doc, what, DEVICE_RUN_FORMAT)
    source = need(doc, what, "source", kind=dict)
    counts = {}
    for i, entry in enumerate(need(doc, what, "counts", kind=list)):
        if not (isinstance(entry, list) and len(entry) == 2 and isinstance(entry[0], list)
                and all(type(q) is int for q in entry[0]) and type(entry[1]) is int):
            raise RecordError(f"{what}: counts[{i}] is not [[qubits...], shots]")
        key = tuple(entry[0])
        if key in counts or list(key) != sorted(set(key)):
            raise RecordError(f"{what}: counts[{i}] repeats an outcome, or its qubits are not sorted and distinct")
        counts[key] = entry[1]
    return DeviceRun(doc, need(doc, what, "digest"), need(doc, what, "stock"), need(doc, what, "role"),
                     need(doc, what, "basis"), source, counts)


# -- Quantum-Film's metrics wrapper of IBM's job fields ------------------------------------------------------------------
@dataclass(frozen=True)
class Metrics:
    job_id: str
    backend: str
    created: object              # aware UTC datetimes, from IBM's job and its timestamps
    running: object
    finished: object


def metrics(data, what):
    doc = parse(data, what)
    created = instant(need(doc, what, "job", "created"), f"{what} job.created")
    stamps = [instant(need(doc, what, "metrics", "timestamps", k), f"{what} metrics.timestamps.{k}")
              for k in ("created", "running", "finished")]
    if stamps[0] != created:
        raise RecordError(f"{what}: the job's created time is not the timestamps'")
    return Metrics(need(doc, what, "job_id"), need(doc, what, "backend"), created, stamps[1], stamps[2])


# -- the read of 2026-10-14 -------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class RefetchJob:
    device: str
    job_id: str
    role: str
    holds: dict                  # the read's comparison flags: commitments, created time and options
    pubs: tuple                  # each PUB's comparison, as an object
    pubs_in_ibm_copy: int
    pubs_in_line: int
    first_shot: object           # aware UTC datetimes the read recorded
    running: object
    at_first_shot: str           # the read's path of the snapshot IBM's history returned at the first shot
    at_running: str              # and at the time the job began running


def refetch_job(data, what):
    doc = parse(data, what)
    formatted(doc, what, REFETCH_FORMAT)
    holds = need(doc, what, "holds", kind=dict)
    pubs = need(holds, f"{what} holds", "pubs", kind=list)
    if not all(isinstance(p, dict) for p in pubs):
        raise RecordError(f"{what}: holds.pubs is not a list of objects")
    return RefetchJob(
        need(doc, what, "device"), need(doc, what, "job_id"), need(doc, what, "role"), holds, tuple(pubs),
        need(holds, f"{what} holds", "pubs_in_ibm_copy", kind=int), need(holds, f"{what} holds", "pubs_in_line",
                                                                           kind=int),
        instant(need(doc, what, "calibration", "first_shot"), f"{what} calibration.first_shot"),
        instant(need(doc, what, "calibration", "running"), f"{what} calibration.running"),
        need(doc, what, "calibration", "before_first_shot", "file"),
        need(doc, what, "calibration", "before_running", "file"))


@dataclass(frozen=True)
class RefetchResult:
    device: str
    job_id: str
    role: str
    agree_at: str
    bytes_equal: bool
    committed_path: str
    committed_bytes: int
    committed_sha256: str
    ibm_bytes: int
    ibm_sha256: str


def refetch_result(data, what):
    doc = parse(data, what)
    formatted(doc, what, RESULTS_FORMAT)
    return RefetchResult(
        need(doc, what, "device"), need(doc, what, "job_id"), need(doc, what, "role"), need(doc, what, "agree_at"),
        need(doc, what, "bytes_equal", kind=bool), need(doc, what, "committed", "path"),
        need(doc, what, "committed", "bytes", kind=int), need(doc, what, "committed", "sha256"),
        need(doc, what, "ibm_copy", "bytes", kind=int), need(doc, what, "ibm_copy", "sha256"))


def read_manifest(data, what, expect):
    """{path: (bytes, sha256)} of a MANIFEST of the read: the files it lists, relative to its own directory."""
    doc = parse(data, what)
    formatted(doc, what, expect)
    out = {}
    for i, f in enumerate(need(doc, what, "files", kind=list)):
        at = f"{what} files[{i}]"
        if not isinstance(f, dict):
            raise RecordError(f"{at}: not an object")
        path = need(f, at, "path")
        if path in out:
            raise RecordError(f"{at}: lists {path} twice")
        out[path] = (need(f, at, "bytes", kind=int), need(f, at, "sha256"))
    return out


_STAMPED = re.compile(r"properties-([0-9]{4})([0-9]{2})([0-9]{2})T([0-9]{2})([0-9]{2})([0-9]{2})Z\.json", re.ASCII)


def stamp_of(name, what):
    """The stamp a snapshot's file name states, as the profile spells a time: properties-20261005T090246Z.json."""
    m = _STAMPED.fullmatch(name)
    if not m:
        raise RecordError(f"{what}: not named properties-<YYYYMMDD>T<HHMMSS>Z.json")
    y, mo, d, h, mi, s = m.groups()
    return f"{y}-{mo}-{d}T{h}:{mi}:{s}Z"


# -- Atlas ------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class AtlasLine:
    job_id: str
    stock: str
    circuit_sha256: str
    engine: str
    shots: int
    decode: str
    salt: str
    commitment: str
    code_commit: str
    qasm_file: str
    submitted_at: str


def commitment_v2(stock, circuit_sha256, engine, job_id, shots, decode, salt):
    """Quantum-Film's commitment v2, which the Atlas provider never held: the SHA-256 of the stream of the version
    string and these seven fields."""
    return hashlib.sha256(p1_commit.stream(COMMITMENT_V2, stock, circuit_sha256, engine, job_id, shots, decode, salt)
                     ).hexdigest()


def atlas_lines(data, what):
    """{job id: AtlasLine} of a `commitments.jsonl`: one canonical line a job, each of format commitment/v2."""
    if not data.endswith(b"\n"):
        raise RecordError(f"{what}: does not end in a line feed")
    out = {}
    for n, raw in enumerate(data[:-1].split(b"\n"), 1):
        at = f"{what} line {n}"
        doc = parse(raw, at)
        formatted(doc, at, ATLAS_LINE_FORMAT)
        item = AtlasLine(need(doc, at, "job_id"), need(doc, at, "stock"), need(doc, at, "circuit_sha256"),
                         need(doc, at, "engine"), need(doc, at, "shots", kind=int), need(doc, at, "decode"),
                         need(doc, at, "salt"), need(doc, at, "commitment"), need(doc, at, "code_commit"),
                         need(doc, at, "qasm_file"), need(doc, at, "submitted_at"))
        if item.job_id in out:
            raise RecordError(f"{at}: job {item.job_id} twice")
        out[item.job_id] = item
    return out


def atlas_submit(data, what):
    """(the job id the provider gave, the circuit's text, the shots asked) of an Atlas job's submit file."""
    doc = parse(data, what)
    params = need(doc, what, "body", "params", kind=dict)
    return (need(doc, what, "response", "job_id"), need(params, f"{what} body.params", "circuit_qasm"),
            need(params, f"{what} body.params", "shots", kind=int))


def atlas_status(data, what):
    """(the job id, the status) of an Atlas job's status file."""
    doc = parse(data, what)
    return need(doc, what, "job_id"), need(doc, what, "status")


def atlas_score(data, what):
    """The job id of an Atlas job's score file."""
    return need(parse(data, what), what, "job_id")
