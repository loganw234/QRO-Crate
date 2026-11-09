"""A test-only builder of synthetic IBM-shaped crates for P3's tests (P3.1; P3's design, item 12): devices, bundles and
jobs with chosen counts, times, commits, kinds and controls, which steps 1 to 8 accept (test_p3_builder holds that), fed
to the comparison's computation directly. It is not a generator: its crates name GENERATOR, which no parcel registers,
and it reads no record of Quantum-Film's or IBM's but nine files of P1's twin, under tests/p1/data/moth (kingston's
morning bundle's four logical circuits, four gate lists and its known-answer QPY, Quantum-Film's, MIT) and v0's source
circuit there. It names no function `test*` and no class `Test*`.

A crate holds, for each Bundle (a device and a label), a manifest in Quantum-Film's `hardware-bundle/v1` form, and for
each of its Jobs a line in `hardware-job/v1`, a device-run record for each PUB, and IBM's result text with IBM's echo of
each PUB's commitment and no execution span, so that:
  - step 4 recomputes each commitment from its record's fourteen inputs and finds it in the line and the echo;
  - step 5 holds each Decode to the bundle's first known-answer Pub, whose counts read its X set;
  - step 6 holds P2's entities, which qro.p2_measures.contribute makes from the crate's files and P1's model;
  - step 7 holds each Compile's carried gate lists: kingston's, or one of them with a pair of x gates added on a
    qubit before anything else touches it (another digest, the same distribution: logically equivalent);
  - step 8 holds nothing of a Job whose link is `unknown` over a result with no span, so its times are the builder's.

A Bundle may vary what was submitted (round 2, item 4): its program and route, written in its manifest, its lines and
its records, and so in its commitments, the program also the name of its Jobs' instrument, which step 4 holds the
records to; its kind, its device's; and the decode its manifest names, its manifest alone, as no step reads a
manifest's decode and an IBM result decodes under one rule, which its records and Decodes keep. It may write its raw
results in the mirror order, which its Decodes then name (`lsb-first`), each read right. And a job may hold the known
answers that leave out qubit 0 or qubit 1 of the pair, `without-0` and `without-1`.
"""
import base64
import hashlib
import json
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from controls.plants_p1 import MORNING_BUNDLE, TWIN
from qro import canonical, p1_commit, p2_law, p2_measures
from qro import vocabulary as V

RECORDS = TWIN / "docs" / "records"
SOURCE_RECORD = "2026-09-25/p3/circuit-ed767c01bd4b851d.qasm"
GENERATOR = "qro-p3-test-builder"                # registered by no parcel: a crate naming it stops at step 9
IBM_FORM, IBM_RULE = "ibm-sampler-result/v1", "quantum_film.ibm.decode/v1"
PROGRAM, STOCK, ROUTE, QISKIT = "sampler", "pauli-4x4", "ibm-direct", "2.5.2"
KA = (0, 1, 3, 7, 12)                            # the qubits kingston's known-answer circuit flips
COMPLEMENT = tuple(q for q in range(16) if q not in KA)
PATTERNS = {"complement": COMPLEMENT, "without-0": (1, 3, 7, 12), "without-1": (0, 3, 7, 12)}   # the other X sets
OPTIONS = {"default_shots": 64, "execution": {"init_qubits": True, "rep_delay": 0.00025}}
CIRCUITS = {"known-answer": ("known-answer", "ZZZZZZZZZZZZZZZZ"), "law": ("law", "ZZZZZZZZZZZZZZZZ"),
            "coherence-xx": ("coherence", "XXZZZZZZZZZZZZZZ"), "coherence-yy": ("coherence", "YYZZZZZZZZZZZZZZ"),
            "complement": ("known-answer", "ZZZZZZZZZZZZZZZZ"), "without-0": ("known-answer", "ZZZZZZZZZZZZZZZZ"),
            "without-1": ("known-answer", "ZZZZZZZZZZZZZZZZ")}
def sha(data):
    return hashlib.sha256(data).hexdigest()


def twin_file(name):
    """One of the files of kingston's morning bundle of P1's twin, by its name there."""
    return RECORDS.joinpath(*f"{MORNING_BUNDLE}/{name}".split("/")).read_bytes()


def known_answer_qasm(qubits):
    """A known-answer circuit in Quantum-Film's text: its header, x on each qubit, a barrier on all 16, 16 measures."""
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', "qreg q[16];", "creg meas[16];"]
    lines += [f"x q[{q}];" for q in sorted(qubits)]
    lines += ["barrier " + ",".join(f"q[{i}]" for i in range(16)) + ";"]
    lines += [f"measure q[{i}] -> meas[{i}];" for i in range(16)]
    return ("\n".join(lines) + "\n").encode("ascii")


def variant(gates_bytes, k=1):
    """A gate list with k pairs of x gates added first on the qubit its first gate acts on: another digest, the same
    Z-basis distribution, so the exact hold holds it to the same logical circuit."""
    doc = json.loads(gates_bytes)
    q = doc["gates"][0][1][0]
    doc["gates"] = [["x", [q], [], []], ["x", [q], [], []]] * k + doc["gates"]
    return (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("ascii")


# -- IBM's result text, made here -------------------------------------------------------------------------------------
def npy(rows):
    head = "{'descr': '|u1', 'fortran_order': False, 'shape': (%d, 2), }" % len(rows)
    head += " " * (-(10 + len(head) + 1) % 64) + "\n"
    return b"\x93NUMPY\x01\x00" + len(head).to_bytes(2, "little") + head.encode("ascii") \
        + b"".join(v.to_bytes(2, "big") for v in rows)


def rows_of(counts, mirror=False):
    """Each shot as a 16-bit integer: qubit q is bit q (`msb-first`, the rule), or bit 15 - q (`lsb-first`)."""
    out = []
    for Y in sorted(counts):
        out += [sum(1 << (15 - q) if mirror else 1 << q for q in Y)] * counts[Y]
    return out


def raw_ibm(pubs, echoes):
    results = [{"__type__": "SamplerPubResult", "__value__": {
        "data": {"__type__": "DataBin", "__value__": {
            "field_names": ["meas"], "field_types": ["<class 'qiskit.primitives.containers.bit_array.BitArray'>"],
            "shape": [], "fields": {"meas": {"__type__": "BitArray", "__value__": {
                "array": {"__type__": "ndarray", "__value__": base64.b64encode(zlib.compress(npy(rows))).decode("ascii")},
                "num_bits": 16}}}}},
        "metadata": {"circuit_metadata": {"qf_commitment": echo}}}} for rows, echo in zip(pubs, echoes)]
    return json.dumps({"__type__": "PrimitiveResult",
                       "__value__": {"pub_results": results, "metadata": {"version": 2}}}).encode("utf-8")


# -- the specification --------------------------------------------------------------------------------------------------
def ka_counts(shots=64, wrong=6):
    """A known answer read right: its X set modal, a few shots one qubit short."""
    return {KA: shots - wrong, KA[:-1]: wrong}


def complement_counts(shots=64, wrong=6):
    return {COMPLEMENT: shots - wrong, COMPLEMENT[:-1]: wrong}


def pattern_counts(name, shots=64, wrong=6):
    """The known answer of PATTERNS[name] read right: its X set modal, a few shots one qubit short."""
    return {PATTERNS[name]: shots - wrong, PATTERNS[name][:-1]: wrong}


_LAW = []


def law_bytes():
    """v0's law file, made from its integer kernel once in the process, and read once."""
    if not _LAW:
        data = p2_law.law_bytes()
        _LAW.extend([data, p2_law.read(data)])
    return _LAW[0]


def the_law():
    law_bytes()
    return _LAW[1]


def law_counts(shots=64, five=48, forbidden=4):
    """`five` shots on five crystals, `forbidden` of them on a layout the law forbids and the rest on two it allows, and
    the others on four crystals."""
    law = the_law()
    allowed = [Y for Y, w in zip(law.layouts, law.weights) if w > 0][:2]
    banned = next(Y for Y, w in zip(law.layouts, law.weights) if w == 0)
    out = {allowed[0]: (five - forbidden + 1) // 2, allowed[1]: (five - forbidden) // 2, banned: forbidden,
           allowed[0][:4]: shots - five}
    return {Y: n for Y, n in out.items() if n}


def coherence_counts(shots=64, agree=40):
    """`agree` shots whose qubits 0 and 1 read alike (parity +1), the rest unalike."""
    out = {(0, 1, 4): agree // 2, (4,): agree - agree // 2, (0, 4): shots - agree}
    return {Y: n for Y, n in out.items() if n}


@dataclass
class Job:
    name: str                          # unique in its bundle, the file names' stem
    circuits: tuple                    # its PUBs' circuit names, in PUB order (CIRCUITS' keys)
    counts: tuple                      # each PUB's {outcome: shots}, all of one total
    start: object = None               # its startTime, or None for `unknown`
    submitted: str = "2026-11-01T09:00:00Z"
    commit: str = "unknown"
    job_id: object = None              # default: the device, the bundle's label and the name


@dataclass
class Bundle:
    device: str
    label: str
    jobs: list
    gates: dict = field(default_factory=dict)      # circuit name -> variant count (0: kingston's own gate list)
    kind: str = "qpu"
    options: dict = None
    held: bool = True                  # its Compile has P2's Hold
    logical: dict = field(default_factory=dict)    # circuit name -> k: another logical circuit, its text and a comment
    program: str = PROGRAM
    route: str = ROUTE
    decode: str = IBM_RULE             # the decode its manifest names; its records and Decodes keep IBM's rule
    order: str = "msb-first"           # its raw results' bit order, which its Decodes name


def ka(name="known-answer", start=None, shots=64, **kw):
    return Job(name, ("known-answer",), (ka_counts(shots),), start, **kw)


def control(name="control", start=None, shots=64, **kw):
    """A control job of two PUBs: the known answer and its complement (P5's unit's shape)."""
    return Job(name, ("known-answer", "complement"), (ka_counts(shots), complement_counts(shots)), start, **kw)


def law(name="law", start=None, shots=64, five=48, forbidden=4, **kw):
    return Job(name, ("law",), (law_counts(shots, five, forbidden),), start, **kw)


def coherence(name="coherence", start=None, shots=64, agree=40, agree_yy=None, **kw):
    return Job(name, ("coherence-xx", "coherence-yy"),
               (coherence_counts(shots, agree), coherence_counts(shots, agree if agree_yy is None else agree_yy)),
               start, **kw)


def job_id(bundle, job):
    return job.job_id or f"{bundle.device.replace('_', '')}{bundle.label.replace('-', '')}{job.name.replace('-', '')}"


# -- the crate ------------------------------------------------------------------------------------------------------------
def _file(rel, data, types="File"):
    return {"@id": rel, "@type": types, "sha256": sha(data), "contentSize": str(len(data)),
            "encodingFormat": "application/json" if rel.endswith(".json") else "text/plain"}


def build(dest, bundles, name="crate"):
    """A crate of these bundles in dest/name, written by qro.canonical.write; its directory."""
    crate = Path(dest) / name
    files, entities = {}, {}

    def put(rel, data, types="File", **terms):
        files[rel] = data
        entities[rel] = {**_file(rel, data, types), **terms}

    put("circuits/source.qasm", RECORDS.joinpath(*SOURCE_RECORD.split("/")).read_bytes())
    logical = {}
    for n in ("known-answer", "law", "coherence-xx", "coherence-yy"):
        put(f"circuits/{n}.qasm", twin_file(f"{n}.qasm"))
        logical[n] = sha(files[f"circuits/{n}.qasm"])
    put("circuits/complement.qasm", known_answer_qasm(COMPLEMENT))
    logical["complement"] = sha(files["circuits/complement.qasm"])
    for n in ("without-0", "without-1"):                 # carried only where a job holds them
        if any(n in job.circuits for b in bundles for job in b.jobs):
            put(f"circuits/{n}.qasm", known_answer_qasm(PATTERNS[n]))
            logical[n] = sha(files[f"circuits/{n}.qasm"])
    for b in bundles:
        for n, k in b.logical.items():
            if (n, k) not in logical:
                rel = f"circuits/{n}-alt{k}.qasm"
                put(rel, files[f"circuits/{n}.qasm"] + f"// another logical circuit, {k}\n".encode("ascii"))
                logical[(n, k)] = sha(files[rel])
    put("circuits/isa.qpy", twin_file("known-answer.qpy"))
    isa = sha(files["circuits/isa.qpy"])
    gate_files = {}
    for b in bundles:
        for n in ("known-answer", "law", "coherence-xx", "coherence-yy", *PATTERNS):
            k = b.gates.get(n, 0)
            if n in PATTERNS:
                gate_files[(n, k)] = None                  # a gate list the crate does not carry: withheld
            elif (n, k) not in gate_files:
                rel = f"gates/{n}.gates.json" if k == 0 else f"gates/{n}-variant{k}.gates.json"
                put(rel, twin_file(f"{n}.gates.json") if k == 0 else variant(twin_file(f"{n}.gates.json"), k))
                gate_files[(n, k)] = rel
    rule = "#rule-quantum_film.ibm.decode.v1"
    entities["#program-sampler"] = {"@id": "#program-sampler", "@type": "SoftwareApplication", "name": PROGRAM}
    for b in bundles:
        if b.program != PROGRAM:
            entities[f"#program-{b.program}"] = {"@id": f"#program-{b.program}", "@type": "SoftwareApplication",
                                                 "name": b.program}
    entities[rule] = {"@id": rule, "@type": "SoftwareApplication", "name": IBM_RULE}
    entities["#transpiler-qiskit-2.5.2"] = {"@id": "#transpiler-qiskit-2.5.2", "@type": "SoftwareApplication",
                                            "name": f"qiskit {QISKIT}"}
    for b in bundles:
        _bundle(b, put, entities, logical, gate_files, isa, files)
    entities["#question"] = {"@id": "#question", "@type": ["CreativeWork", "qro:Question"], "name": "The question",
                             "description": "v0's law, asked of synthetic devices.",
                             "object": sorted([{"@id": "circuits/source.qasm"}, {"@id": rule}]
                                              + [{"@id": f"circuits/{n}.qasm"}
                                                 for n in sorted(n for n in logical if isinstance(n, str))],
                                              key=lambda r: r["@id"])}
    put("question/law.json", law_bytes())
    crate.mkdir(parents=True)
    for rel, data in files.items():
        p = crate.joinpath(*rel.split("/"))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    terms, new = p2_measures.contribute(crate, {i: dict(e) for i, e in entities.items()})
    entities["#question"].update(terms)
    for e in new:
        entities[e["@id"]] = e
    graph = list(entities.values())
    actions = sorted(e["@id"] for e in graph if set(canonical.types(e)) & V.ACTION_TYPES)
    root = {"@id": canonical.ROOT, "@type": "Dataset", "name": "QRO-Crate P3: a synthetic crate",
            "description": "A crate P3's tests build: synthetic jobs on v0's law.",
            "conformsTo": [{"@id": V.PROCESS_RUN_CRATE}, {"@id": V.PROFILE}],
            "license": {"@id": "https://creativecommons.org/licenses/by/4.0/"},
            "hasPart": [{"@id": r} for r in sorted(files)], "mentions": [{"@id": a} for a in actions],
            "qro:generator": GENERATOR, "datePublished": "2026-11-08", "qro:writer": "P3's test builder",
            "qro:writtenAt": "2026-11-08T00:00:00Z", "qro:signature": "none", "qro:trustedTime": "none"}
    md = {"@context": V.context(), "@graph": [V.descriptor(), root, *V.profile_entities(), *graph]}
    (crate / canonical.DESCRIPTOR).write_bytes(canonical.write(md))
    return crate


def _bundle(b, put, entities, logical, gate_files, isa, files):
    base = f"{b.device}/{b.label}"
    options = b.options if b.options is not None else OPTIONS
    options_sha = p1_commit.options_digest(options)
    device = f"#device-{b.device}"
    entities[device] = {"@id": device, "@type": "IndividualProduct", "name": b.device, "qro:deviceKind": b.kind}
    jobs, commitments = [], {}
    for job in b.jobs:
        jid = job_id(b, job)
        circuits = []
        shots = sum(job.counts[0].values())
        for k, n in enumerate(job.circuits):
            role, basis = CIRCUITS[n]
            gates = gate_files[(n, b.gates.get(n, 0))]
            salt = sha(f"{base}/{job.name}/{k}".encode("ascii"))[:32]
            circuit = logical[(n, b.logical[n])] if n in b.logical else logical[n]
            fields = {"stock": STOCK, "role": role, "basis": basis, "kind": b.kind, "route": b.route,
                      "backend": b.device, "program": b.program, "pub": k, "circuit_sha256": circuit,
                      "isa_sha256": isa, "shots": shots, "options_sha256": options_sha, "decode": IBM_RULE,
                      "salt": salt}
            c = p1_commit.commitment_of(fields)
            commitments[(job.name, k)] = (c, fields)
            circuits.append({"basis": basis, "circuit_sha256": circuit, "commitment": c,
                             "gates_sha256": sha(files[gates]) if gates else sha(b"a gate list not carried: " +
                                                                                   n.encode("ascii")),
                             "isa_sha256": isa, "name": n, "pub": k, "qasm3_sha256": isa, "role": role,
                             "salt": salt, "shots": shots})
        jobs.append({"circuits": circuits, "job": job.name})
    manifest = {"backend": b.device, "compile": {"optimization_level": 3, "seed_transpiler": 7}, "decode": b.decode,
                "format": "quantum-film/hardware-bundle/v1", "jobs": jobs, "kind": b.kind, "options": options,
                "options_sha256": options_sha, "program": b.program, "readme_sha256": sha(b"no readme"),
                "route": b.route,
                "source": {"path": "circuits/source.qasm", "sha256": sha(files["circuits/source.qasm"])},
                "stock": STOCK, "versions": {"qiskit": QISKIT}}
    mrel = f"{base}/manifest.json"
    put(mrel, (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode("ascii"))
    mdigest = sha(files[mrel])
    known = None
    for job in b.jobs:
        jid = job_id(b, job)
        if "known-answer" in job.circuits and known is None:
            known = f"#pub-{jid}-{job.circuits.index('known-answer')}"
    if known is None:
        raise ValueError(f"{base}: a bundle needs a known-answer job, whose Pub holds its decodes' order")
    compile_files = [mrel]
    for job in b.jobs:
        jid = job_id(b, job)
        run = f"{base}/run/{job.name}"
        line = {"backend": b.device, "bundle_sha256": mdigest,
                "commitments": [commitments[(job.name, k)][0] for k in range(len(job.circuits))],
                "format": "quantum-film/hardware-job/v1", "job_id": jid, "kind": b.kind, "program": b.program,
                "route": b.route, "stock": STOCK, "submitted_at": job.submitted}
        put(f"{run}-line.json", (json.dumps(line, indent=1, sort_keys=True) + "\n").encode("ascii"))
        rows = [rows_of(c, b.order == "lsb-first") for c in job.counts]
        if len({len(r) for r in rows}) != 1:
            raise ValueError(f"{run}: a job's PUBs share one shot count")
        put(f"{run}-raw.json", raw_ibm(rows, [commitments[(job.name, k)][0] for k in range(len(job.circuits))]),
            ["File", "qro:RawResult"], **{"qro:rawForm": IBM_FORM, "qro:shots": len(rows[0])})
        pubs, records = [], []
        for k, n in enumerate(job.circuits):
            c, fields = commitments[(job.name, k)]
            source = {**{f: fields[f] for f in ("kind", "route", "backend", "program", "pub", "circuit_sha256",
                                                "isa_sha256", "shots", "options_sha256", "decode", "salt")},
                      "options": options, "commitment": c, "job_id": jid, "submitted_at": job.submitted}
            record = {"basis": fields["basis"], "format": "quantum-film/device-run/v1", "role": fields["role"],
                      "source": source, "stock": STOCK}
            rrel = f"{run}-pub{k}-{n}.json"
            put(rrel, (json.dumps(record, indent=1, sort_keys=True) + "\n").encode("ascii"))
            pid = f"#pub-{jid}-{k}"
            entities[pid] = {"@id": pid, "@type": "qro:Pub", "qro:role": fields["role"], "qro:basis": fields["basis"],
                             "qro:commitment": c, "qro:record": {"@id": rrel}}
            pubs.append(pid)
            records.append(rrel)
        entities[f"#job-{jid}"] = {
            "@id": f"#job-{jid}", "@type": ["CreateAction", "qro:Job"], "name": f"{job.name} on {b.device}",
            "instrument": {"@id": f"#program-{b.program}"}, "object": [{"@id": p} for p in pubs],
            "result": sorted([{"@id": f"{run}-raw.json"}, {"@id": f"{run}-line.json"}]
                             + [{"@id": r} for r in records], key=lambda r: r["@id"]),
            "qro:device": {"@id": f"#device-{b.device}"}, "qro:jobId": jid, "qro:line": {"@id": f"{run}-line.json"},
            "startTime": job.start or "unknown", "endTime": "unknown", "qro:clock": "provider",
            "qro:calibrationLink": "unknown", "qro:kitCommit": job.commit}
        entities[f"#decode-{jid}"] = {
            "@id": f"#decode-{jid}", "@type": ["CreateAction", "qro:Decode"], "name": f"decode of {job.name}",
            "instrument": {"@id": "#rule-quantum_film.ibm.decode.v1"}, "object": [{"@id": f"{run}-raw.json"}],
            "qro:decodeRule": IBM_RULE, "qro:bitOrder": b.order, "qro:knownAnswer": {"@id": known}}
    if b.held:
        logicals = sorted({f"circuits/{n}-alt{b.logical[n]}.qasm" if n in b.logical else f"circuits/{n}.qasm"
                           for job in b.jobs for n in job.circuits})
        made = sorted({gate_files[(n, b.gates.get(n, 0))] for job in b.jobs for n in job.circuits
                       if gate_files[(n, b.gates.get(n, 0))]})
        entities[f"#compile-{b.device}-{b.label}"] = {
            "@id": f"#compile-{b.device}-{b.label}", "@type": ["CreateAction", "qro:Compile"],
            "name": f"compile for {b.device}, {b.label}", "instrument": {"@id": "#transpiler-qiskit-2.5.2"},
            "object": [{"@id": r} for r in sorted(compile_files + logicals)],
            **({"result": [{"@id": r} for r in made]} if made else {})}
