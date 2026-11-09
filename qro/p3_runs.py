"""What a comparison reads of the crates its runs take (P3's design, items 2 to 4; P3.1). Standard library and qro only.

Every crate is read through P1's entity model (qro.p1_graph.Index: Jobs, Pubs, Decodes, raw results, devices, lines)
and P1's readers (qro.p1_records.line and .manifest; qro.p1_decode.crate_file for a File's bytes), once the checker's
nine steps have accepted it. Nothing here reads a count. What it reads is the graph, the lines, the manifests and the
times, so the selected jobs, the members and everything the refusals and the family rest on are fixed before any value
is read (the design's item 1, "How before is held").

A JOB, as the comparison reads it:
  - its device: the `name` of its `qro:device`, and that device's `qro:deviceKind`; a Job naming no device it can read
    has none, and no selector selects it;
  - its time: its `startTime` where the Job states one (v0's IBM crate: the execution span, on the provider's clock),
    else its line's `submitted_at` (a local unit's: the producer's clock, REPORTED), and which of the two it is; a job
    with neither has no time;
  - its bundle: its line's `bundle_sha256`, and the manifest of that digest the crate carries, read by P1's reader;
    none for a job with no line (Atlas's), whose manifest facts are then `unexposed`;
  - whether its manifest was held by step 7: it is the manifest of a Compile the crate holds a Hold of, as P2's
    qro.p2_measures.manifest_of reads a Compile's manifest (step 7 holds every gate list such a manifest names that
    the crate carries, and refuses one that does not hold);
  - its producing commit, its `qro:kitCommit` (`unknown` where it states none), and its raw result's `sha256`;
  - its Pubs, each with its role, basis and commitment, the rule and bit order of the Decode of its job's raw result,
    and its manifest circuit: the circuit of its job's manifest whose `commitment` is the Pub's (step 4 held the Pub's
    commitment to the line's, and step 9 the line's to the manifest's, P1's G2).
A relation a crate does not hold is read as absent, never guessed: a job with no raw result has no raw digest, a Pub
whose job's raw result no Decode reads has no rule. A member's own relations are held by step 6, which measured every
law and coherence Pub of a crate whose question carries P2's measure set, which the comparison requires
(qro.p3_refusals.question).

A MEMBER of a measure is a selected job holding a Pub the measure reads: role `law` for the law measures; for `x0x1`,
role `coherence` whose basis reads exactly qubits 0 and 1 out of Z, both in X, as P2's coherence_pair reads a basis of
its own width (`y0y1` the same in Y). A selected job holding no such Pub, a control job, is selected and is no member.
"""
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from qro import p1_decode, p1_forms, p1_records, p2_hold, p2_law, p2_measures, reader
from qro.p1_graph import GraphError, Index

LAW_ROLE, COHERENCE_ROLE, KNOWN_ANSWER = "law", "coherence", "known-answer"
START, SUBMITTED = "startTime", "submitted_at"     # the two kinds of a job's time


class ComparisonError(ValueError):
    """A crate the checker accepted that the comparison cannot read as P1's model says: never a verdict on it."""


@dataclass(frozen=True)
class Pub:
    id: str
    entity: dict
    role: object
    basis: object
    commitment: object             # a digest, "none", or None where the Pub states none
    rule: object                   # its Decode's qro:decodeRule, or None
    order: object                  # its Decode's qro:bitOrder, or None
    circuit: object                # its manifest circuit (qro.p1_records.Circuit), or None


@dataclass(frozen=True)
class Job:
    crate: str                     # the body digest of the crate that holds it
    id: object                     # its qro:jobId, or None
    entity: dict
    device: object                 # its device's name, or None
    kind: object                   # its device's qro:deviceKind, or None
    time: object                   # an aware datetime, or None
    clock: object                  # START or SUBMITTED: which time it is; None with no time
    bundle: object                 # its line's bundle_sha256, or None
    manifest: object               # its bundle's manifest (qro.p1_records.Manifest), or None
    held: bool                     # its manifest is a held Compile's
    commit: str                    # its qro:kitCommit, or "unknown"
    raw: object                    # its raw result's sha256, or None
    pubs: tuple                    # of Pub, in the order the Job lists them


@dataclass
class Crate:
    digest: str                    # its body digest: its identity
    directory: Path
    md: dict
    index: Index
    jobs: tuple
    question: dict                 # the parts of its question the question digest covers (qro.p3_refusals)
    law: object                    # its law (qro.p2_law.Law), or None where its question names none
    carried: frozenset             # the sha256 of every File the crate holds
    units: bool                    # whether it holds a qro:Unit
    _texts: dict = field(default_factory=dict)

    def file_bytes(self, digest):
        """The bytes of the first File the crate holds with this sha256, or None."""
        for e in self.index.files_by_sha256(digest):
            if reader.local_file(e):
                return p1_decode.crate_file(self.directory, e, "a file")
        return None

    def known_answer_set(self, digest):
        """The X set of the known-answer circuit of this digest (qro.p1_decode.expected_set), or None where the crate
        carries no such circuit or it is not one Quantum-Film's known-answer form reads."""
        if digest not in self._texts:
            data = self.file_bytes(digest) if isinstance(digest, str) else None
            try:
                self._texts[digest] = None if data is None else frozenset(p1_decode.expected_set(data))
            except p1_decode.KnownAnswerError:
                self._texts[digest] = None
        return self._texts[digest]


def _ref(index, entity, key, type=None):
    """The one entity a single-valued reference names, or None where the term is absent or names none."""
    try:
        return index.one(entity, key, type)
    except GraphError:
        return None


def _time(text):
    try:
        return p1_forms.parse_time(text, "Z")
    except ValueError:
        return None


def _held_manifests(index):
    """The sha256 of the manifest of every Compile the crate holds a Hold of, each read by P2's own
    qro.p2_measures.manifest_of (the one File of the Compile's `object` named manifest.json), the reading step 7 holds:
    one place for P2's rule. A Compile with no one such File is passed over here; step 7 refuses it, so no crate the
    checker accepts holds one."""
    held = {h["qro:heldCompile"]["@id"] for h in index.of_type("qro:Hold")
            if isinstance(h.get("qro:heldCompile"), dict) and isinstance(h["qro:heldCompile"].get("@id"), str)}
    out = set()
    for c in index.of_type("qro:Compile"):
        if c["@id"] in held:
            try:
                manifest = p2_measures.manifest_of(index, c)
            except p2_hold.HoldError:
                continue
            if isinstance(manifest.get("sha256"), str):
                out.add(manifest["sha256"])
    return frozenset(out)


_LAWS = {}                     # the law file's SHA-256 -> its Law: P2's reader is a pure function of the bytes


def _law(data):
    digest = hashlib.sha256(data).hexdigest()
    if digest not in _LAWS:
        if len(_LAWS) >= 8:
            _LAWS.pop(next(iter(_LAWS)))
        _LAWS[digest] = p2_law.read(data)
    return _LAWS[digest]


def _question(index, directory):
    """(the parts of the question the digest covers, its law or None)."""
    questions = index.of_type("qro:Question")
    if len(questions) != 1:
        return {"law": "none", "lawCircuit": "none", "measureSet": "none", "twins": []}, None
    q = questions[0]
    law_file, circuit = _ref(index, q, "qro:law", "File"), _ref(index, q, "qro:lawCircuit", "File")
    parts = {"law": law_file.get("sha256", "none") if law_file else "none",
             "lawCircuit": circuit.get("sha256", "none") if circuit else "none",
             "measureSet": q.get("qro:measureSet", "none"),
             "twins": sorted(t for t in q.get("qro:twins", []) if isinstance(t, str))
             if isinstance(q.get("qro:twins"), list) else []}
    law = None
    if law_file is not None and reader.local_file(law_file):
        try:
            law = _law(p1_decode.crate_file(directory, law_file, "the question's law"))
        except p2_law.LawError as x:
            raise ComparisonError(f"the question's law {law_file['@id']} is not qro-law/1: {x}") from None
    return parts, law


def read(directory, md, digest):
    """The Crate of an accepted crate's directory, its parsed metadata and its body digest."""
    directory = Path(directory)
    index = Index(md)
    carried = frozenset(e["sha256"] for e in index.of_type("File")
                        if reader.local_file(e) and isinstance(e.get("sha256"), str))
    question, law = _question(index, directory)
    held = _held_manifests(index)
    manifests, jobs = {}, []
    for j in sorted(index.of_type("qro:Job"), key=lambda e: e["@id"]):
        jobs.append(_job(index, directory, digest, j, manifests, held))
    return Crate(digest, directory, md, index, tuple(jobs), question, law, carried,
                 bool(index.of_type("qro:Unit")))


def _manifest(index, directory, bundle, manifests):
    if bundle not in manifests:
        found = [e for e in index.files_by_sha256(bundle) if reader.local_file(e)]
        if not found:
            manifests[bundle] = None
        else:
            data = p1_decode.crate_file(directory, found[0], "the bundle's manifest")
            try:
                manifests[bundle] = p1_records.manifest(data, found[0]["@id"])
            except p1_records.RecordError as x:
                raise ComparisonError(f"{found[0]['@id']}: a job's bundle manifest P1's reader does not read: {x}") \
                    from None
    return manifests[bundle]


def _job(index, directory, digest, j, manifests, held):
    device = _ref(index, j, "qro:device")
    line_file = _ref(index, j, "qro:line", "File")
    line = None
    if line_file is not None:
        try:
            line = p1_records.line(p1_decode.crate_file(directory, line_file, "the job line"), line_file["@id"])
        except (p1_records.RecordError, GraphError) as x:
            raise ComparisonError(f"{j['@id']}: its line is not one P1's reader reads: {x}") from None
    time, clock = _time(j.get("startTime")), START
    if time is None and line is not None:
        time, clock = _time(line.submitted_at), SUBMITTED
    if time is None:
        clock = None
    bundle = line.bundle_sha256 if line is not None else None
    manifest = _manifest(index, directory, bundle, manifests) if bundle is not None else None
    try:
        raw = index.raw_of(j)
    except GraphError:
        raw = None
    try:
        decode = index.decode_of(raw) if raw is not None else None
    except GraphError:
        decode = None
    by_commitment = {c.commitment: c for c in manifest.circuits()} if manifest is not None else {}
    pubs = []
    for p in index.pubs_of(j):
        commitment = p.get("qro:commitment")
        pubs.append(Pub(p["@id"], p, p.get("qro:role"), p.get("qro:basis"), commitment,
                        decode.get("qro:decodeRule") if decode else None, decode.get("qro:bitOrder") if decode else None,
                        by_commitment.get(commitment) if isinstance(commitment, str) and commitment != "none"
                        else None))
    commit = j.get("qro:kitCommit")
    return Job(digest, j.get("qro:jobId") if isinstance(j.get("qro:jobId"), str) else None, j,
               device.get("name") if device else None, device.get("qro:deviceKind") if device else None,
               time, clock, bundle, manifest, bundle in held if bundle else False,
               commit if isinstance(commit, str) else "unknown",
               raw.get("sha256") if raw is not None and isinstance(raw.get("sha256"), str) else None, tuple(pubs))


def reads(pub, measure):
    """Whether a measure reads this Pub: role `law` for a law measure; for a coherence measure, role `coherence` and a
    basis reading exactly its two qubits out of Z, in its letter (P2's coherence_pair, at the basis's own width)."""
    if measure in p2_law.COHERENCE:
        if pub.role != COHERENCE_ROLE or not isinstance(pub.basis, str):
            return False
        try:
            letter, a, b = p2_hold.coherence_pair(pub.basis, len(pub.basis))
        except p2_hold.HoldError:
            return False
        return f"{letter}{a}{letter}{b}".lower() == measure
    return pub.role == LAW_ROLE


def selected(crate, selector):
    """The Jobs of a crate the selector selects, by @id."""
    return tuple(j for j in crate.jobs if selector.selects(j.device, j.bundle, j.id, j.time))


def members(jobs, measure):
    """[(job, the Pubs of it the measure reads)] of each job that holds one, in the jobs' order."""
    out = []
    for j in jobs:
        pubs = tuple(p for p in j.pubs if reads(p, measure))
        if pubs:
            out.append((j, pubs))
    return out


def on_device(crate, device):
    """The crate's jobs on a device, ordered by their time, where every one of them has a time of one kind and no two
    share one; None otherwise, where no job is the one just before another."""
    jobs = [j for j in crate.jobs if j.device == device]
    if not jobs or any(j.time is None for j in jobs) or len({j.clock for j in jobs}) != 1:
        return None
    ordered = sorted(jobs, key=lambda j: j.time)
    if any(a.time == b.time for a, b in zip(ordered, ordered[1:])):
        return None
    return ordered
