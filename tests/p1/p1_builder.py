"""A test-only builder of small synthetic crates, by hand, for P1's checker steps (P1.1). It is not a generator: no
step runs it, it reads no record of Quantum-Film's or of IBM's, and it commits no provider's file. Everything it
writes is made here, from numbers chosen here.

A Model holds a crate as the steps see it: its files (path -> bytes) and its entities (id -> a dict of terms,
without the digests). write() computes every File's sha256 and contentSize from the bytes at that moment, lists
every file under the root, and writes the metadata with qro.canonical.write, which holds it to the strict reader.
So a test that replaces a file's bytes in the model has "resealed" it by construction; a test that wants a digest
left stale edits the written crate instead (edit() and rewrite() below).

ibm_model() is an IBM-shaped crate of three jobs on one device, as the entity model of P1's design (item 1.1)
has them: a known-answer job (one PUB), a law job (one PUB) and a coherence job (two PUBs); every PUB has its
commitment, its record and its job line, and IBM's echo of it inside its raw result; the three jobs share one
bundle; four calibration snapshots of the device, with the three jobs linked as the real records' three cases are:
a plain link, a link past a newer snapshot that was stamped and measured (`history-in-gap`), and a snapshot stamped
but still being measured at the first shot (which is no gap). atlas_model() is the Atlas-shaped crate: a law job
and the frozen-vector job, whose commitments are `none`.

The commitment a model writes is recomputed with p1_commit, and a snapshot's claims with p1_calibration, so a
mutant of either changes the builder and the step together and the honest crate still passes: the golden vectors of
test_p1_commit.py and test_p1_calibration.py, taken from Quantum-Film's real records, are what hold those two.
"""
import atexit
import base64
import hashlib
import itertools
import json
import random
import shutil
import tempfile
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

from qro import canonical, fixture, p1_calibration, p1_commit, p1_steps, reader, spelling
from qro import vocabulary as V
from qro.refusal import Refused

UTC = timezone.utc
GENERATOR = "qro-p1-test-builder"          # a name no parcel registers: a crate naming it stops at step 9
IBM_FORM, ATLAS_FORM, VECTOR_FORM = "ibm-sampler-result/v1", "atlas-tomography-result/v1", "atlas-known-answer-vector/v1"
IBM_RULE, ATLAS_RULE = "quantum_film.ibm.decode/v1", "quantum_film.atlas.decode/v1"
DEVICE, PROGRAM, STOCK, ROUTE = "ibm_synth", "sampler", "pauli-4x4", "ibm-direct"
OPTIONS = {"dynamical_decoupling": {"enable": False}, "twirling": {"enable_gates": False, "enable_measure": False}}
KA = (0, 1, 3, 7, 12)                                   # the qubits the known-answer circuit flips
ROWS = 40
BUNDLE = hashlib.sha256(b"a manifest that is not in this crate").hexdigest()
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def at(h, m, s, micro=0):
    return datetime(2026, 10, 5, h, m, s, micro, tzinfo=UTC)


def zoneless(dt):
    """IBM's span string: no zone, six fractional digits, trailing zeros kept."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + f".{dt.microsecond:06d}"


# -- IBM's result text ------------------------------------------------------------------------------------------------
def npy(rows):
    """A .npy v1.0 file of unsigned bytes, shape (len(rows), 2): one big-endian 16-bit outcome a row."""
    head = "{'descr': '|u1', 'fortran_order': False, 'shape': (%d, 2), }" % len(rows)
    head += " " * (-(10 + len(head) + 1) % 64) + "\n"
    return b"\x93NUMPY\x01\x00" + len(head).to_bytes(2, "little") + head.encode("ascii") \
        + b"".join(v.to_bytes(2, "big") for v in rows)


def packed(npy_bytes):
    """What IBM puts in a PUB's `array`: base64 of zlib of the .npy file."""
    return base64.b64encode(zlib.compress(npy_bytes)).decode("ascii")


def ibm_doc(pubs, echoes, span=None):
    """IBM's RuntimeEncoder document of a SamplerV2 result, as a dict: `pubs` is a list of lists of 16-bit outcomes,
    `echoes` the commitment IBM echoed for each (None: no echo), `span` a (start, stop) of datetimes."""
    results = []
    for rows, echo in zip(pubs, echoes):
        meta = {"circuit_metadata": {"qf_commitment": echo} if echo is not None else {}}
        results.append({"__type__": "SamplerPubResult", "__value__": {
            "data": {"__type__": "DataBin", "__value__": {
                "field_names": ["meas"], "field_types": ["<class 'qiskit.primitives.containers.bit_array.BitArray'>"],
                "shape": [], "fields": {"meas": {"__type__": "BitArray", "__value__": {
                    "array": {"__type__": "ndarray", "__value__": packed(npy(rows))}, "num_bits": 16}}}}},
            "metadata": meta}})
    value = {"pub_results": results, "metadata": {"version": 2}}
    if span is not None:
        value["metadata"]["execution"] = {"execution_spans": {"__type__": "ExecutionSpans", "__value__": {"spans": [{
            "__type__": "DoubleSliceSpan", "__value__": {
                "start": {"__type__": "datetime", "__value__": zoneless(span[0])},
                "stop": {"__type__": "datetime", "__value__": zoneless(span[1])},
                "data_slices": {"0": [[len(pubs[0])], 0, 1]}}}]}}}
    return {"__type__": "PrimitiveResult", "__value__": value}


def raw_ibm(pubs, echoes, span=None):
    """IBM's result text: json.dumps of ibm_doc, as runtime's encoder writes it."""
    return json.dumps(ibm_doc(pubs, echoes, span)).encode("utf-8")


def outcome(qubits):
    """The 16-bit shot whose set bits are the qubits that read 1 (the rule's order)."""
    return sum(1 << q for q in qubits)


def known_answer_rows(n=ROWS, want=KA):
    """n shots of a known-answer run: mostly the expected set, a few with one qubit wrong, one all zero."""
    e = outcome(want)
    return [e] * (n - 6) + [e ^ (1 << want[-1])] * 3 + [e | (1 << 5)] * 2 + [0]


def random_rows(seed, n=ROWS, sites=5):
    rng = random.Random(seed)
    return [outcome(rng.sample(range(16), sites)) for _ in range(n)]


def ka_qasm(flipped=KA):
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', "qreg q[16];", "creg meas[16];"]
    lines += [f"x q[{q}];" for q in flipped]
    lines.append("barrier " + ",".join(f"q[{i}]" for i in range(16)) + ";")
    lines += [f"measure q[{i}] -> meas[{i}];" for i in range(16)]
    return ("\n".join(lines) + "\n").encode("ascii")


def other_qasm(tag):
    return (f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[16];\ncreg meas[16];\nh q[0];\n// {tag}\n').encode("ascii")


# -- a calibration snapshot ----------------------------------------------------------------------------------------------
def snapshot_doc(stamp, newest, seed=0, device=DEVICE):
    """A snapshot in IBM's properties form, small: two gates, two qubits, and every date a minute before `newest`
    but one, which is `newest`: so the newest value date is `newest`, whatever the stamp."""
    d, early = spelling.time, spelling.time(newest - timedelta(minutes=1))
    return {
        "backend_name": device, "backend_version": "1.0.0", "last_update_date": d(stamp),
        "gates": [{"gate": "cz", "name": "cz0_1", "qubits": [0, 1], "parameters": [
            {"date": early, "name": "gate_error", "unit": "", "value": 0.0125 + seed * 0.001},
            {"date": early, "name": "gate_length", "unit": "ns", "value": 68}]},
            {"gate": "sx", "name": "sx0", "qubits": [0], "parameters": [
                {"date": d(newest), "name": "gate_error", "unit": "", "value": 0.0003}]}],
        "general": [{"date": early, "name": "zz_01", "unit": "GHz", "value": 5.5e-06}],
        "general_qlists": [{"name": "lf_2", "qubits": [0, 1]}],
        "qubits": [[{"date": early, "name": "T1", "unit": "us", "value": 100.5 + seed},
                    {"date": early, "name": "readout_error", "unit": "", "value": 0.0102}],
                   [{"date": early, "name": "T1", "unit": "us", "value": 97.25},
                    {"date": early, "name": "readout_error", "unit": "", "value": 0.0098}]]}


def snapshot_bytes(doc):
    return json.dumps(doc, indent=1, sort_keys=True).encode("utf-8") + b"\n"


def snapshot_path(stamp):
    return "snapshots/properties-" + stamp.strftime("%Y%m%dT%H%M%SZ") + ".json"


# -- a crate as a model ------------------------------------------------------------------------------------------------------
class Model:
    def __init__(self):
        self.files = {}              # path -> bytes
        self.ents = {}               # @id -> the entity's terms, a File's digests left to write()

    def entity(self, i, types, **terms):
        e = {"@id": i, "@type": types, **terms}
        self.ents[i] = e
        return e

    def file(self, path, data, types="File", **terms):
        self.files[path] = data
        return self.entity(path, types, encodingFormat="application/json" if path.endswith(".json") else "text/plain",
                           **terms)

    def md(self):
        graph = [V.descriptor(), self.root(), *[dict(e) for e in self.ents.values()], *V.profile_entities()]
        for e in graph:
            if e["@id"] in self.files:
                e["sha256"], e["contentSize"] = sha(self.files[e["@id"]]), str(len(self.files[e["@id"]]))
        return {"@context": V.context(), "@graph": graph}

    def root(self):
        actions = sorted(i for i, e in self.ents.items()
                         if "CreateAction" in (e["@type"] if isinstance(e["@type"], list) else [e["@type"]]))
        return {"@id": "./", "@type": "Dataset", "name": "P1.1's synthetic crate",
                "description": "A test-only crate made by hand, with no generator.",
                "conformsTo": [{"@id": V.PROCESS_RUN_CRATE}, {"@id": V.PROFILE}],
                "license": {"@id": "https://creativecommons.org/licenses/by/4.0/"},
                "hasPart": [{"@id": p} for p in sorted(self.files)], "mentions": [{"@id": a} for a in actions],
                "qro:generator": GENERATOR, **fixture.HEADER}

    def write(self, dest, strict=True):
        """The crate in `dest`: every file, then the metadata, held to the strict reader unless told not to."""
        dest = Path(dest)
        for path, data in self.files.items():
            target = dest.joinpath(*path.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        md = self.md()
        data = canonical.write(md) if strict else canonical.dumps(canonical.arrange(md))
        dest.mkdir(parents=True, exist_ok=True)
        (dest / canonical.DESCRIPTOR).write_bytes(data)
        return dest

    # -- handles ---------------------------------------------------------------------------------------------------------
    def json(self, path):
        return json.loads(self.files[path])

    def put_json(self, path, obj):
        self.files[path] = json.dumps(obj, indent=1, sort_keys=True).encode("utf-8") + b"\n"

    def edit_json(self, path, fn):
        """The JSON file at `path` edited by fn(object); its entity's digests are left to write()."""
        obj = self.json(path)
        fn(obj)
        self.put_json(path, obj)

    def record(self, job, k=0):
        """The path of a PUB's device-run record."""
        return next(p for p in self.files if p.startswith(f"run/{job}-pub{k}-"))

    def device(self, name, kind="qpu"):
        self.entity("#device-" + name, "IndividualProduct", name=name, **{"qro:deviceKind": kind})
        return "#device-" + name

    def snapshot(self, stamp, newest, seed=0, device="#device-" + DEVICE, name=DEVICE):
        """A snapshot file and its entity, with the claims its file gives."""
        data = snapshot_bytes(snapshot_doc(stamp, newest, seed, name))
        path = snapshot_path(stamp)
        self.file(path, data, ["File", "qro:Snapshot"], **p1_calibration.claims(p1_calibration.parse_snapshot(data)),
                  **{"qro:device": ref(device), "qro:clock": "provider"})
        return path


def refs(*ids):
    return [{"@id": i} for i in ids]


def ref(i):
    return {"@id": i}


# -- the IBM-shaped crate ---------------------------------------------------------------------------------------------------------
# job name -> (role, [(pub name, basis)], first shot, last shot)
JOBS = {"jobka": ("known-answer", [("known-answer", "Z" * 16)], at(10, 27, 0, 285375), at(10, 27, 1, 376976)),
        "joblaw": ("law", [("law", "Z" * 16)], at(12, 26, 17, 34663), at(12, 26, 18, 100000)),
        "jobcoh": ("coherence", [("coherence-xx", "XX" + "Z" * 14), ("coherence-yy", "YY" + "Z" * 14)],
                   at(12, 22, 0, 162000), at(12, 22, 1, 500000))}
# the four snapshots: (stamp, newest value date, the seed of its values)
SNAPS = {"s0657": (at(6, 57, 43), at(6, 57, 20), 0), "s0902": (at(9, 2, 46), at(9, 2, 30), 0),
         "s1128": (at(11, 28, 27), at(11, 25, 10), 1), "s1221": (at(12, 21, 18), at(12, 24, 6, 730000), 2)}
# job -> (link word, the snapshots it names): the history's answers, as the real records' three cases
LINKS = {"jobka": ("history-at-first-shot", ["s0902"]), "joblaw": ("history-in-gap", ["s1128", "s1221"]),
         "jobcoh": ("history-at-first-shot", ["s1128"])}


def ibm_model(rows=ROWS):
    m = Model()
    m.entity("#device-" + DEVICE, "IndividualProduct", name=DEVICE, **{"qro:deviceKind": "qpu"})
    m.entity("#program-" + PROGRAM, "SoftwareApplication", name=PROGRAM)
    m.entity("#rule-ibm", "SoftwareApplication", name=IBM_RULE)
    for name, circuit in (("known-answer", ka_qasm()), ("law", other_qasm("law")),
                          ("coherence-xx", other_qasm("xx")), ("coherence-yy", other_qasm("yy"))):
        m.file(f"bundle/{name}.qasm", circuit)
        m.file(f"bundle/{name}.qpy", b"QPY" + name.encode("ascii") + bytes(range(7)))
    snaps = {key: m.snapshot(stamp, newest, seed) for key, (stamp, newest, seed) in SNAPS.items()}
    for j, (role, pubs, first, last) in JOBS.items():
        commitments, records, pub_ids, echoes, row_sets = [], [], [], [], []
        for k, (name, basis) in enumerate(pubs):
            body = {"jobka": known_answer_rows(rows), "joblaw": random_rows(11, rows), "jobcoh": random_rows(20 + k, rows)}[j]
            circuit, qpy = m.files[f"bundle/{name}.qasm"], m.files[f"bundle/{name}.qpy"]
            source = {"backend": DEVICE, "circuit_sha256": sha(circuit), "decode": IBM_RULE, "isa_sha256": sha(qpy),
                      "job_id": j, "kind": "qpu", "options": OPTIONS, "options_sha256": p1_commit.options_digest(OPTIONS),
                      "program": PROGRAM, "pub": k, "route": ROUTE,
                      "salt": sha(f"salt of {j} {k}".encode("ascii")), "shots": rows,
                      "fixed_at": spelling.time(last), "submitted_at": spelling.time(first.replace(microsecond=0))}
            c = p1_commit.commitment_of({"stock": STOCK, "role": role, "basis": basis, **{
                n: source[n] for n in ("kind", "route", "backend", "program", "pub", "circuit_sha256", "isa_sha256",
                                       "shots", "options_sha256", "decode", "salt")}})
            source["commitment"] = c
            rec_path = f"run/{j}-pub{k}-{name}.json"
            m.file(rec_path, json.dumps({"basis": basis, "code": {"quantum_film": "0.1.0"}, "counts": [[[0], rows]],
                                         "digest": sha(b"not checked"), "format": "quantum-film/device-run/v1",
                                         "law": {"id": STOCK}, "role": role, "source": source, "stock": STOCK},
                                        indent=1, sort_keys=True).encode("utf-8") + b"\n")
            pid = f"#pub-{j}-{k}"
            m.entity(pid, "qro:Pub", **{"qro:role": role, "qro:basis": basis, "qro:commitment": c,
                                        "qro:record": ref(rec_path)})
            commitments.append(c)
            records.append(rec_path)
            pub_ids.append(pid)
            echoes.append(c)
            row_sets.append(body)
        raw_path, line_path = f"run/{j}-raw.json", f"run/{j}-line.json"
        m.file(raw_path, raw_ibm(row_sets, echoes, (first, last)), ["File", "qro:RawResult"],
               **{"qro:rawForm": IBM_FORM, "qro:shots": rows})
        m.file(line_path, json.dumps({"backend": DEVICE, "bundle_sha256": BUNDLE, "commitments": commitments,
                                      "format": "quantum-film/hardware-job/v1", "job_id": j, "kind": "qpu",
                                      "program": PROGRAM, "route": ROUTE, "stock": STOCK,
                                      "submitted_at": spelling.time(first.replace(microsecond=0))},
                                     indent=1, sort_keys=True).encode("utf-8") + b"\n")
        word, named = LINKS[j]
        job = {"instrument": ref("#program-" + PROGRAM), "object": refs(*pub_ids),
               "result": refs(raw_path, line_path, *records), "qro:device": ref("#device-" + DEVICE), "qro:jobId": j,
               "qro:line": ref(line_path), "startTime": spelling.time(first), "endTime": spelling.time(last),
               "qro:clock": "provider", "qro:calibrationLink": word, "qro:kitCommit": "unknown"}
        job["qro:calibration"] = refs(*[snaps[n] for n in named])
        m.entity("#job-" + j, ["CreateAction", "qro:Job"], name=f"job {j}", **job)
        m.entity("#decode-" + j, ["CreateAction", "qro:Decode"], instrument=ref("#rule-ibm"), object=refs(raw_path),
                 result=refs(*records), **{"qro:decodeRule": IBM_RULE, "qro:bitOrder": "msb-first",
                                           "qro:knownAnswer": ref("#pub-jobka-0")})
    return m


def npy_of(rows, value):
    """A .npy v1.0 file of `rows` rows of the one 16-bit outcome `value`, made without a list of the rows."""
    head = "{'descr': '|u1', 'fortran_order': False, 'shape': (%d, 2), }" % rows
    head += " " * (-(10 + len(head) + 1) % 64) + "\n"
    return b"\x93NUMPY\x01\x00" + len(head).to_bytes(2, "little") + head.encode("ascii") + value.to_bytes(2, "big") * rows


def many_jobs_model(n, rows, own_known_answers=False):
    """n IBM jobs of one PUB each, on one device and in one bundle. Every raw result holds `rows` shots of the known
    answer and deflates to a few kilobytes whatever `rows` is (as the verifier's bigcrate.py makes them), so a crate of
    them costs a step the memory of the results it keeps and nothing else. Job 0's Pub is the known answer every Decode
    names, or with `own_known_answers` each Decode names its own job's Pub (every Pub has the role known-answer, and
    the data hold in every job), so that step 5 reads n records, n circuits and n raw results to judge them; every
    Job's times are its raw result's span, and its link is `history-at-first-shot` to the one snapshot of the crate,
    stamped before the first shot (so that step 8 reads each result for its first shot)."""
    m = Model()
    m.entity("#device-" + DEVICE, "IndividualProduct", name=DEVICE, **{"qro:deviceKind": "qpu"})
    m.entity("#program-" + PROGRAM, "SoftwareApplication", name=PROGRAM)
    m.entity("#rule-ibm", "SoftwareApplication", name=IBM_RULE)
    circuit, qpy = ka_qasm(), b"QPY" + bytes(range(7))
    m.file("bundle/known-answer.qasm", circuit)
    m.file("bundle/known-answer.qpy", qpy)
    array = packed(npy_of(rows, outcome(KA)))
    first, last = at(10, 27, 0, 285375), at(10, 27, 1, 376976)
    snapshot = m.snapshot(at(9, 2, 46), at(9, 2, 30))
    for i in range(n):
        j = f"job{i:03d}"
        source = {"backend": DEVICE, "circuit_sha256": sha(circuit), "decode": IBM_RULE, "isa_sha256": sha(qpy),
                  "job_id": j, "kind": "qpu", "options": OPTIONS, "options_sha256": p1_commit.options_digest(OPTIONS),
                  "program": PROGRAM, "pub": 0, "route": ROUTE, "salt": sha(f"salt of {j}".encode("ascii")),
                  "shots": rows}
        c = p1_commit.commitment_of({"stock": STOCK, "role": "known-answer", "basis": "Z" * 16, **{
            k: source[k] for k in ("kind", "route", "backend", "program", "pub", "circuit_sha256", "isa_sha256", "shots",
                                   "options_sha256", "decode", "salt")}})
        source["commitment"] = c
        record, raw, line = f"run/{j}-pub0-known-answer.json", f"run/{j}-raw.json", f"run/{j}-line.json"
        m.file(record, json.dumps({"basis": "Z" * 16, "format": "quantum-film/device-run/v1", "role": "known-answer",
                                   "source": source, "stock": STOCK}, indent=1, sort_keys=True).encode("utf-8") + b"\n")
        doc = ibm_doc([[0]], [c], (first, last))
        doc["__value__"]["pub_results"][0]["__value__"]["data"]["__value__"]["fields"]["meas"]["__value__"]["array"][
            "__value__"] = array
        m.file(raw, json.dumps(doc).encode("utf-8"), ["File", "qro:RawResult"], **{"qro:rawForm": IBM_FORM,
                                                                                    "qro:shots": rows})
        m.file(line, json.dumps({"bundle_sha256": BUNDLE, "commitments": [c], "format": "quantum-film/hardware-job/v1",
                                 "job_id": j}, indent=1, sort_keys=True).encode("utf-8") + b"\n")
        m.entity(f"#pub-{j}-0", "qro:Pub", **{"qro:role": "known-answer", "qro:basis": "Z" * 16, "qro:commitment": c,
                                              "qro:record": ref(record)})
        m.entity("#job-" + j, ["CreateAction", "qro:Job"], name=f"job {j}", instrument=ref("#program-" + PROGRAM),
                 object=refs(f"#pub-{j}-0"), result=refs(raw, line, record), **{
                     "qro:device": ref("#device-" + DEVICE), "qro:jobId": j, "qro:line": ref(line),
                     "startTime": spelling.time(first), "endTime": spelling.time(last), "qro:clock": "provider",
                     "qro:calibrationLink": "history-at-first-shot", "qro:calibration": refs(snapshot),
                     "qro:kitCommit": "unknown"})
        m.entity("#decode-" + j, ["CreateAction", "qro:Decode"], instrument=ref("#rule-ibm"), object=refs(raw),
                 result=refs(record), **{"qro:decodeRule": IBM_RULE, "qro:bitOrder": "msb-first",
                                         "qro:knownAnswer": ref(f"#pub-{j}-0" if own_known_answers
                                                                else "#pub-job000-0")})
    return m


def copy_job(m, job="joblaw", suffix="2"):
    """The job copied byte for byte under new ids: its raw result, line and records are new files of the same bytes, and a new
    Pub for each record, a new Job and a new Decode name them, as the originals' do (the snapshots, the device and the
    known answer are shared). Returns the new job's name."""
    new = job + suffix

    def renamed(x):
        if isinstance(x, dict):
            return {k: (v.replace(job, new) if k == "@id" and isinstance(v, str) else renamed(v)) for k, v in x.items()}
        if isinstance(x, list):
            return [renamed(v) for v in x]
        return x
    for path in [p for p in m.files if job in p]:
        m.files[path.replace(job, new)] = m.files[path]
    for i in [i for i in m.ents if job in i]:
        m.ents[i.replace(job, new)] = renamed(m.ents[i])
    m.ents["#job-" + new]["qro:jobId"] = new
    return new


# -- the Atlas-shaped crate -------------------------------------------------------------------------------------------------------------
def atlas_string(label, occupied, order="atlas-register"):
    """The count string, position 0 leftmost, of a setting `label` in which exactly the qubits `occupied` read 1:
    written from Quantum-Film's statement of its rule (the string is little-endian over [the setting's non-I qubits,
    ascending] + [every other qubit, ascending]; the label is in circuit order, qubit 0 rightmost), independently of
    qro.p1_decode."""
    n = len(label)
    if order == "circuit-order":
        return "".join("1" if (n - 1 - p) in occupied else "0" for p in range(n))
    active = [q for q in range(n) if label[n - 1 - q] != "I"]
    register = active + [q for q in range(n) if q not in active]
    return "".join("1" if register[n - 1 - p] in occupied else "0" for p in range(n))


def atlas_vector(labels=("IIIIIIYIIIIIIXII", "IIIIIIZIIIIIIXII", "IXIIIIXIIIXIIXII"), order="atlas-register",
                 scale=128):
    """A known-answer vector in the frozen form: qubit q reads 1 on exactly (2q + 1) of every 32 shots, in every
    setting. The shots are 32 patterns, each `scale` times, pattern j setting qubit q iff j < 2q + 1; so every
    Z-basis position has its exact frequency and the z test is met with z = 0, under the order the strings are
    written in."""
    measurements = {}
    for label in labels:
        counts = {}
        for j in range(32):
            s = atlas_string(label, {q for q in range(16) if j < 2 * q + 1}, order)
            counts[s] = counts.get(s, 0) + scale            # patterns j and j + 1 can coincide
        measurements[label] = {"counts": counts, "shots": 32 * scale}
    return json.dumps({"job": "synthetic-vector", "measurements": measurements}, indent=1, sort_keys=True).encode()


def atlas_result(layouts, label="IIIIIIIIIIIIIIZZ", other="IIIIIIIIIIIIIIXX", order="atlas-register"):
    """A tomography result, in Quantum-Film's wrapper: the all-Z setting `label` holding `layouts` ({a tuple of
    occupied qubits: shots}), and one setting with an X in it, their strings written in `order`."""
    shots = sum(layouts.values())
    zs = {atlas_string(label, set(occ), order): n for occ, n in layouts.items()}
    xs = {atlas_string(other, set(occ), order): n for occ, n in layouts.items()}
    result = {"measurements": {label: {"counts": zs, "shots": shots}, other: {"counts": xs, "shots": shots}},
              "observables": {"0": {"X": -0.0009765625, "Y": 0.00634765625, "Z": 0.37939453125}},
              "density_matrices": {"0": {"imag": [[0, 0], [0, 0]], "real": [[1, 0], [0, 0]]}}}
    return json.dumps({"job_id": "synthetic-law", "path": "/api/v1/jobs/synthetic-law/result",
                       "response": {"result": result}, "status": 200, "taken_from": "/result"},
                      indent=1, sort_keys=True).encode()


LAYOUTS = {(0, 1, 2, 3, 4): 20, (1, 3, 5, 7, 9): 12, (2, 4, 6, 8, 15): 8}
# the nine settings of the real law results (2026-09-25 and 2026-09-26): one all-Z, and the engine's own others
REAL_LABELS = ("IIIIIIIIIIIIIIXY", "IIIIIIIIIIIIIIXZ", "IIIIIIIIIIIIIIYY", "IIIIIIIIIIIIIIYZ", "IIIIIIIIIIIIIIZY",
               "IIIIIIIIIIIIIIZZ", "XXXXXXXXXXXXXXXX", "YYYYYYYYYYYYYYYX", "ZZZZZZZZZZZZZZZX")
ALL_Z = "IIIIIIIIIIIIIIZZ"


def atlas_result_in_real_shape(layouts, fetched_at=None, seed=0):
    """A tomography result in the shape of a real law result, made here and holding no byte of one: the engine's nine
    settings of 4,096 shots each, the all-Z setting holding `layouts` distinct layouts of five occupied sites (a real
    one holds 1,995 to 2,027), eight others of 2,600 to 3,100 distinct outcomes each, the engine's observables and
    density matrices beside the counts, the wrapper's keys sorted and indented one space as Quantum-Film writes them,
    and a top-level `fetched_at` where one is given (five of the six real results carry it)."""
    rng = random.Random(seed)
    shots = 4096

    def weights(n):
        w = [1] * n
        for i in rng.choices(range(n), k=shots - n):
            w[i] += 1
        return w
    sites = rng.sample(list(itertools.combinations(range(16), 5)), layouts)
    measurements = {}
    for label in REAL_LABELS:
        if label == ALL_Z:
            counts = {atlas_string(label, set(occ)): w for occ, w in zip(sites, weights(layouts))}
        else:
            k = rng.randint(2600, 3100)
            counts = dict(zip((format(v, "016b") for v in rng.sample(range(1 << 16), k)), weights(k)))
        measurements[label] = {"counts": counts, "shots": shots}
    keys = [str(i) for i in range(16)] + ["0,1"]
    result = {"measurements": measurements,
              "observables": {k: {"X": 0.0009765625, "Y": -0.00634765625, "Z": 0.37939453125} for k in keys},
              "density_matrices": {k: {"imag": [[0, 0], [0, 0]], "real": [[0.697265625, 0], [0, 0.302734375]]}
                                   for k in keys}}
    top = {"job_id": f"synthetic-law-{seed}", "path": f"/api/v1/jobs/synthetic-law-{seed}/result",
           "response": {"result": result}, "status": 200, "taken_from": "/result"}
    if fetched_at is not None:
        top["fetched_at"] = fetched_at
    return json.dumps(top, indent=1, sort_keys=True).encode("utf-8")


def atlas_model(law=None):
    """The Atlas-shaped crate. `law` is (the bytes of a tomography result, the shots per setting it holds) to put where
    the small law result goes."""
    law_bytes, law_shots = law if law is not None else (atlas_result(LAYOUTS), sum(LAYOUTS.values()))
    m = Model()
    m.entity("#device-atlas", "IndividualProduct", name="atlas-emu", **{"qro:deviceKind": "simulator"})
    m.entity("#rule-atlas", "SoftwareApplication", name=ATLAS_RULE)
    m.file("law/result.json", law_bytes, ["File", "qro:RawResult"], **{"qro:rawForm": ATLAS_FORM, "qro:shots": law_shots})
    m.file("vector/vector.json", atlas_vector(), ["File", "qro:RawResult"], **{"qro:rawForm": VECTOR_FORM,
                                                                             "qro:shots": 32 * 128})
    for j, role, raw in (("alaw", "law", "law/result.json"), ("avec", "known-answer", "vector/vector.json")):
        m.entity(f"#pub-{j}-0", "qro:Pub", **{"qro:role": role, "qro:commitment": "none"})
        m.entity("#job-" + j, ["CreateAction", "qro:Job"], name=f"job {j}", instrument=ref("#rule-atlas"),
                 object=refs(f"#pub-{j}-0"), result=refs(raw), **{
                     "qro:device": ref("#device-atlas"), "qro:jobId": j, "startTime": "unknown", "endTime": "unknown",
                     "qro:calibrationLink": "unexposed", "qro:kitCommit": "unknown", "qro:clock": "provider"})
        m.entity("#decode-" + j, ["CreateAction", "qro:Decode"], instrument=ref("#rule-atlas"), object=refs(raw),
                 **{"qro:decodeRule": ATLAS_RULE, "qro:bitOrder": "atlas-register",
                    "qro:knownAnswer": ref("#pub-avec-0")})
    return m


def atlas_many_model(n, law=None):
    """n Atlas law jobs, each with a tomography result of its own, and the job of the frozen vector, which every Decode
    names for its known answer. `law(i)` is (the bytes of job i's result, the shots per setting it holds); by default the
    small result of atlas_model, n times in n files."""
    m = Model()
    m.entity("#device-atlas", "IndividualProduct", name="atlas-emu", **{"qro:deviceKind": "simulator"})
    m.entity("#rule-atlas", "SoftwareApplication", name=ATLAS_RULE)
    m.file("vector/vector.json", atlas_vector(), ["File", "qro:RawResult"], **{"qro:rawForm": VECTOR_FORM,
                                                                             "qro:shots": 32 * 128})
    jobs = [("avec", "known-answer", "vector/vector.json")]
    for i in range(n):
        data, shots = law(i) if law is not None else (atlas_result(LAYOUTS), sum(LAYOUTS.values()))
        m.file(f"law/result{i}.json", data, ["File", "qro:RawResult"], **{"qro:rawForm": ATLAS_FORM, "qro:shots": shots})
        jobs.append((f"alaw{i}", "law", f"law/result{i}.json"))
    for j, role, raw in jobs:
        m.entity(f"#pub-{j}-0", "qro:Pub", **{"qro:role": role, "qro:commitment": "none"})
        m.entity("#job-" + j, ["CreateAction", "qro:Job"], name=f"job {j}", instrument=ref("#rule-atlas"),
                 object=refs(f"#pub-{j}-0"), result=refs(raw), **{
                     "qro:device": ref("#device-atlas"), "qro:jobId": j, "startTime": "unknown", "endTime": "unknown",
                     "qro:calibrationLink": "unexposed", "qro:kitCommit": "unknown", "qro:clock": "provider"})
        m.entity("#decode-" + j, ["CreateAction", "qro:Decode"], instrument=ref("#rule-atlas"), object=refs(raw),
                 **{"qro:decodeRule": ATLAS_RULE, "qro:bitOrder": "atlas-register",
                    "qro:knownAnswer": ref("#pub-avec-0")})
    return m


# -- editing a written crate ------------------------------------------------------------------------------------------------------------
def read_md(crate):
    return reader.read((Path(crate) / canonical.DESCRIPTOR).read_bytes())


def edit(crate, fn, strict=True):
    """The written crate's metadata edited by fn(graph) and written again: held to the strict reader unless told not
    to, with no digest touched."""
    p = Path(crate) / canonical.DESCRIPTOR
    md = json.loads(p.read_bytes())
    fn(md["@graph"])
    p.write_bytes(canonical.write(md) if strict else canonical.dumps(canonical.arrange(md)))
    return crate


def entity(graph, i):
    return next(e for e in graph if e["@id"] == i)


def refusal(step, crate, md=None):
    """The Refused a P1 step raises on a written crate, or None where it accepts it. `md` may be a metadata the
    caller has edited after reading it; by default the crate's own, held to the strict reader."""
    try:
        getattr(p1_steps, f"step{step}")(Path(crate), read_md(crate) if md is None else md)
    except Refused as r:
        return r
    return None


_PRISTINE = {}


def pristine():
    """The two models as they come, each written once into a directory that nothing writes to again: {name: (the
    files, the directory)}. A fault that touches only the metadata runs against these (judge), so the many tests of
    such faults write no file; one that changes a file writes its own crate."""
    if not _PRISTINE:
        for name, make in (("ibm", ibm_model), ("atlas", atlas_model)):
            m = make()
            d = Path(tempfile.mkdtemp(prefix=f"p1-{name}-"))
            atexit.register(shutil.rmtree, str(d), True)
            for path, data in m.files.items():
                target = d.joinpath(*path.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            _PRISTINE[name] = (dict(m.files), d)
    return _PRISTINE


def judge(m, dest, step, strict=True):
    """Run one step on the model's crate: the Refused, or None. Where the model's files are a pristine model's, the
    metadata is held to the strict reader in memory and the step reads the pristine directory; otherwise the crate is
    written to `dest` first. The same verdict either way: the files are the same bytes."""
    for files, directory in pristine().values():
        if files == m.files:
            md = m.md()
            data = canonical.write(md) if strict else canonical.dumps(canonical.arrange(md))
            return refusal(step, directory, reader.read(data) if strict else json.loads(data))
    return refusal(step, m.write(dest, strict))


def rewrite(crate, rel, data):
    """A file's bytes replaced, and its entity's sha256 and contentSize with them, so step 2 holds."""
    Path(crate).joinpath(*rel.split("/")).write_bytes(data)
    return edit(crate, lambda g: entity(g, rel).update(sha256=sha(data), contentSize=str(len(data))))
