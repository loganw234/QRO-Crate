"""A test-only builder of synthetic crates for P2's steps (P2.1). It is not a generator: no step runs it, and it reads
no record of Quantum-Film's or IBM's but the copies under tests/p2/data/ (kingston's morning bundle, Quantum-Film's,
MIT; their README names them).

A Model holds a crate as its files (path -> bytes) and P1's entities (id -> terms). write() writes the files, gives
every File its digest and size, adds P2's terms and entities as qro.p2_measures.contribute makes them from those files,
then applies the model's `reseal` (files replaced after P2's entities were made, their digests made to agree) and its
`edits` (functions of the entities, by id), lists every file under the root, mentions every action, and writes the
metadata with qro.canonical.write, which holds it to the strict reader.

The crates are IBM-shaped, as P1's entity model has them, and pass P1.1's steps 4, 5 and 8: three jobs on one device,
a known-answer job, a law job and a coherence job of two PUBs; each Pub states `qro:commitment` `none` (step 4 takes it
at its word), the known answer's record names its circuit (step 5 reads its expected set there), and each Job's link is
`unknown` over a raw result with no execution span (step 8 compares nothing).
  small_model(): a question of a 2 x 2 tile with 2 crystals (a law made here, laid by two Givens rotations: (0,2) and
      (0,3) at 2/5, (1,2) and (1,3) at 1/10, X0X1 = Y0Y1 = 4/5), and a compile of four circuits: kingston's known
      answer (the copies) and the small law's law, XX and YY circuits, each with a gate list `transpile` makes. Fast.
      It can leave all of the gate lists uncarried, or some.
  sheet_model(): the small crate with a second compile in the shape of P1's sheets, whose law and coherence circuits
      and gate lists are the morning bundle's, found by digest.
  real_model(): v0's question (the pauli-4x4 law from p2_law, the source circuit's copy) and kingston's morning
      compile, its four gate lists and logical circuits and its manifest, copied byte for byte.
  atlas_model(): v0's question and Atlas-shaped jobs, their raw results tomography results that Atlas's rule decodes;
      no compile. It can hold a coherence PUB on an Atlas raw result, which P2 refuses.
"""
import base64
import hashlib
import itertools
import json
import math
import random
import re
import zlib
from fractions import Fraction
from pathlib import Path

from qro import canonical, fixture, p2_law, p2_measures, reader
from qro import vocabulary as V
from qro.refusal import Refused

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
GENERATOR = "qro-p2-test-builder"          # a name no parcel registers: as a process, a crate naming it stops at step 9
IBM_FORM, IBM_RULE = "ibm-sampler-result/v1", "quantum_film.ibm.decode/v1"
DEVICE, PROGRAM, STOCK = "ibm_synth", "sampler", "pauli-4x4"
KA = (0, 1, 3, 7, 12)                      # the qubits kingston's known-answer circuit flips
SOURCE_PATH = "circuits/circuit-ed767c01bd4b851d.qasm"
SMALL_CIRCUIT_PATH = "circuits/small-law.qasm"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def data(name):
    """The bytes of one of the copies under tests/p2/data/."""
    return (DATA / name).read_bytes()


def outcome(qubits):
    return sum(1 << q for q in qubits)


# -- IBM's result text, made here --------------------------------------------------------------------------------------
def npy(rows):
    """A .npy v1.0 file of unsigned bytes, shape (len(rows), 2): one big-endian 16-bit outcome a row."""
    head = "{'descr': '|u1', 'fortran_order': False, 'shape': (%d, 2), }" % len(rows)
    head += " " * (-(10 + len(head) + 1) % 64) + "\n"
    return b"\x93NUMPY\x01\x00" + len(head).to_bytes(2, "little") + head.encode("ascii") \
        + b"".join(v.to_bytes(2, "big") for v in rows)


def raw_ibm(pubs):
    """IBM's RuntimeEncoder text of a SamplerV2 result: `pubs` a list of lists of 16-bit outcomes; no echo, no span."""
    results = [{"__type__": "SamplerPubResult", "__value__": {
        "data": {"__type__": "DataBin", "__value__": {
            "field_names": ["meas"], "field_types": ["<class 'qiskit.primitives.containers.bit_array.BitArray'>"],
            "shape": [], "fields": {"meas": {"__type__": "BitArray", "__value__": {
                "array": {"__type__": "ndarray",
                          "__value__": base64.b64encode(zlib.compress(npy(rows))).decode("ascii")},
                "num_bits": 16}}}}},
        "metadata": {"circuit_metadata": {}}}} for rows in pubs]
    return json.dumps({"__type__": "PrimitiveResult",
                       "__value__": {"pub_results": results, "metadata": {"version": 2}}}).encode("utf-8")


def rows_of(counts):
    """The 16-bit outcomes of {tuple of qubits read 1: shots}, in a fixed order."""
    out = []
    for Y in sorted(counts):
        out += [outcome(Y)] * counts[Y]
    return out


# -- circuits ----------------------------------------------------------------------------------------------------------
QASM_HEAD = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n'
SMALL_T1, SMALL_T2 = math.atan(0.5), math.pi / 4


def givens(a, b, t):
    return [f"h q[{a}];", f"cx q[{a}],q[{b}];", f"ry({t!r}) q[{a}];", f"ry({t!r}) q[{b}];", f"cx q[{a}],q[{b}];",
            f"h q[{a}];"]


def small_gates(t1=SMALL_T1, t2=SMALL_T2):
    return ["x q[0];", "x q[2];"] + givens(0, 1, t1) + givens(2, 3, t2)


def qasm(n, gates, basis=None, measured=False):
    """A circuit in the subset: the header, `gates`, the basis change of `basis` (X: h; Y: sdg then h) and, if measured,
    a barrier on every qubit and the n measures."""
    lines = [f"qreg q[{n}];"] + ([f"creg meas[{n}];"] if measured else []) + list(gates)
    for q, b in enumerate(basis or ""):
        lines += {"X": [f"h q[{q}];"], "Y": [f"sdg q[{q}];", f"h q[{q}];"], "Z": []}[b]
    if measured:
        lines.append("barrier " + ",".join(f"q[{q}]" for q in range(n)) + ";")
        lines += [f"measure q[{q}] -> meas[{q}];" for q in range(n)]
    return (QASM_HEAD + "\n".join(lines) + "\n").encode("ascii")


SMALL_LAYOUTS = tuple(itertools.combinations(range(4), 2))
SMALL_WEIGHTS = (0, 4, 4, 1, 1, 0)
SMALL_OBSERVABLES = {"X0X1": Fraction(4, 5), "Y0Y1": Fraction(4, 5)}


def small_law_bytes(weights=SMALL_WEIGHTS, observables=None, den=10, stock="synthetic-2x2"):
    return p2_law.write(2, 2, den, SMALL_LAYOUTS, weights, observables or SMALL_OBSERVABLES, stock,
                        "a 2 x 2 tile with 2 crystals, laid by two Givens rotations: P2.1's test question")


_LINE = re.compile(r"(x|h|sdg) q\[([0-9]+)\];|cx q\[([0-9]+)\],q\[([0-9]+)\];|ry\(([^)]*)\) q\[([0-9]+)\];")


def transpile(logical, offset=10, num_qubits=40):
    """A gate list in Quantum-Film's isa-gates/v1 form for a logical circuit, logical qubit q on physical qubit
    offset + q, each gate written in the ISA exactly up to a global phase: h = rz(pi/2) sx rz(pi/2); sdg = rz(-pi/2);
    cx c,t = h(t) cz(c,t) h(t); ry(t) = rz(-pi/2) h rz(t) h rz(pi/2), in time order. Parsed here, by its own pattern,
    not by qro.p2_sim's reader."""
    text = logical.decode("ascii")
    n = int(re.search(r"qreg q\[([0-9]+)\];", text).group(1))
    gates = []

    def one(name, q, *ps):
        gates.append([name, [offset + q], [], [float(p) for p in ps]])

    def h(q):
        one("rz", q, math.pi / 2)
        one("sx", q)
        one("rz", q, math.pi / 2)
    for line in text.splitlines():
        m = _LINE.fullmatch(line)
        if not m:
            continue
        if m.group(1) == "x":
            one("x", int(m.group(2)))
        elif m.group(1) == "h":
            h(int(m.group(2)))
        elif m.group(1) == "sdg":
            one("rz", int(m.group(2)), -math.pi / 2)
        elif m.group(3):
            c, t = int(m.group(3)), int(m.group(4))
            h(t)
            gates.append(["cz", [offset + c, offset + t], [], []])
            h(t)
        else:
            q, t = int(m.group(6)), float(m.group(5))
            one("rz", q, -math.pi / 2)
            h(q)
            one("rz", q, t)
            h(q)
            one("rz", q, math.pi / 2)
    gates.append(["barrier", [offset + q for q in range(n)], [], []])
    gates += [["measure", [offset + q], [q], []] for q in range(n)]
    chain = [offset + q for q in range(n)]
    doc = {"format": "quantum-film/isa-gates/v1", "gates": gates, "global_phase": 0.0,
           "layout": {"final": chain, "initial": chain, "routing_permutation": list(range(num_qubits))},
           "num_clbits": n, "num_qubits": num_qubits}
    return (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("ascii")


def manifest(circuits):
    """A hardware-bundle/v1 manifest naming circuits: [(job, name, role, basis, logical bytes, gate bytes or None)]."""
    jobs = {}
    for job, name, role, basis, logical, gate_list in circuits:
        c = {"basis": basis, "circuit_sha256": sha(logical), "name": name, "role": role}
        if gate_list is not None:
            c["gates_sha256"] = sha(gate_list)
        jobs.setdefault(job, []).append(c)
    doc = {"format": "quantum-film/hardware-bundle/v1", "stock": STOCK,
           "jobs": [{"job": j, "circuits": cs} for j, cs in jobs.items()]}
    return (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("ascii")


# -- a crate as a model ------------------------------------------------------------------------------------------------
def ref(i):
    return {"@id": i}


def refs(*ids):
    return [{"@id": i} for i in sorted(ids)]


class Model:
    def __init__(self, source=p2_law.SOURCE_CIRCUIT):
        self.files, self.ents, self.reseal, self.edits = {}, {}, {}, []
        self.source, self.contribute = source, True

    def entity(self, i, types, **terms):
        self.ents[i] = {"@id": i, "@type": types, **terms}
        return self.ents[i]

    def file(self, path, data, types="File", **terms):
        self.files[path] = data
        return self.entity(path, types, encodingFormat="application/json" if path.endswith(".json") else "text/plain",
                           **terms)

    def write(self, dest):
        dest = Path(dest)
        for path, b in self.files.items():
            target = dest.joinpath(*path.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b)
        ents = {i: dict(e) for i, e in self.ents.items()}
        for path, b in self.files.items():
            ents[path].update(sha256=sha(b), contentSize=str(len(b)))
        if self.contribute:
            terms, new = p2_measures.contribute(dest, ents, source=self.source)
            ents["#question"].update(terms)
            for e in new:
                ents[e["@id"]] = e
        for path, b in self.reseal.items():
            dest.joinpath(*path.split("/")).write_bytes(b)
            ents[path].update(sha256=sha(b), contentSize=str(len(b)))
        for edit in self.edits:
            edit(ents)
        on_disk = sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*")
                         if p.is_file() and p.name != canonical.DESCRIPTOR)
        actions = sorted(i for i, e in ents.items() if "CreateAction" in canonical.types(e))
        root = {"@id": "./", "@type": "Dataset", "name": "P2.1's synthetic crate",
                "description": "A test-only crate made by hand, with no generator.",
                "conformsTo": [{"@id": V.PROCESS_RUN_CRATE}, {"@id": V.PROFILE}],
                "license": {"@id": "https://creativecommons.org/licenses/by/4.0/"},
                "hasPart": [{"@id": p} for p in on_disk], "mentions": [{"@id": a} for a in actions],
                "qro:generator": GENERATOR, **fixture.HEADER}
        md = {"@context": V.context(), "@graph": [V.descriptor(), root, *ents.values(), *V.profile_entities()]}
        (dest / canonical.DESCRIPTOR).write_bytes(canonical.write(md))
        return dest


def p1_jobs(m, law_counts, coherence_counts, M, law_basis=None, coherence_bases=None):
    """The device, program, rule and the three jobs, with their Pubs, Decodes, raw results and records."""
    m.entity("#device-" + DEVICE, "IndividualProduct", name=DEVICE, **{"qro:deviceKind": "qpu"})
    m.entity("#program-" + PROGRAM, "SoftwareApplication", name=PROGRAM)
    m.entity("#rule-ibm", "SoftwareApplication", name=IBM_RULE)
    ka = data("known-answer.qasm")
    m.file("bundle/known-answer.qasm", ka)
    e = outcome(KA)
    ka_rows = [e] * 34 + [e ^ (1 << 12)] * 3 + [e | (1 << 5)] * 2 + [0]
    bases = coherence_bases or ("XX" + "Z" * (M - 2), "YY" + "Z" * (M - 2))
    jobs = {"jobka": ("known-answer", [("known-answer", "Z" * 16, ka_rows)]),
            "joblaw": ("law", [("law", law_basis if law_basis is not None else "Z" * M, rows_of(law_counts))]),
            "jobcoh": ("coherence", [("coherence-" + b[:2].lower(), b, rows_of(c))
                                     for b, c in zip(bases, coherence_counts)])}
    for j, (role, pubs) in jobs.items():
        pub_ids, records = [], []
        for k, (name, basis, rows) in enumerate(pubs):
            rec = f"run/{j}-pub{k}-{name}.json"
            m.file(rec, json.dumps({"basis": basis, "format": "quantum-film/device-run/v1", "role": role,
                                    "source": {"circuit_sha256": sha(ka) if role == "known-answer" else "0" * 64,
                                               "pub": k}, "stock": STOCK}, indent=1, sort_keys=True).encode() + b"\n")
            pid = f"#pub-{j}-{k}"
            m.entity(pid, "qro:Pub", **{"qro:role": role, "qro:basis": basis, "qro:commitment": "none",
                                        "qro:record": ref(rec)})
            pub_ids.append(pid)
            records.append(rec)
        raw = f"run/{j}-raw.json"
        m.file(raw, raw_ibm([p[2] for p in pubs]), ["File", "qro:RawResult"],
               **{"qro:rawForm": IBM_FORM, "qro:shots": len(pubs[0][2])})
        m.entity("#job-" + j, ["CreateAction", "qro:Job"], name=f"job {j}", instrument=ref("#program-" + PROGRAM),
                 object=refs(*pub_ids), result=refs(raw, *records), **{
                     "qro:device": ref("#device-" + DEVICE), "qro:jobId": j, "startTime": "unknown",
                     "endTime": "unknown", "qro:clock": "provider", "qro:calibrationLink": "unknown",
                     "qro:kitCommit": "unknown"})
        m.entity("#decode-" + j, ["CreateAction", "qro:Decode"], instrument=ref("#rule-ibm"), object=refs(raw),
                 result=refs(*records), **{"qro:decodeRule": IBM_RULE, "qro:bitOrder": "msb-first",
                                           "qro:knownAnswer": ref("#pub-jobka-0")})


def compile_entity(m, cid, circuits, manifest_path="bundle/manifest.json"):
    """The bundle's files and its Compile: circuits [(path of logical, path of gate list or None)]."""
    objs = [lp for lp, _ in circuits]
    res = [gp for _, gp in circuits if gp is not None]
    m.entity(cid, ["CreateAction", "qro:Compile"], name="the bundle's compile",
             object=refs(*(objs + [manifest_path])), **({"result": refs(*res)} if res else {}))


SMALL_LAW_COUNTS = {(0, 2): 15, (0, 3): 13, (1, 2): 4, (1, 3): 3, (0, 1): 2, (2, 3): 1, (0,): 1, (0, 1, 2): 1}
SMALL_XX = {(): 18, (0, 1): 18, (0,): 2, (1, 2): 2}            # 36 of 40 agree on qubits 0 and 1
SMALL_YY = {(2,): 17, (0, 1, 3): 18, (1,): 3, (0, 3): 2}        # 35 of 40 agree
# The small compile's four circuits, as its manifest names them: (job, name, role, basis).
SMALL_NAMED = (("known-answer", "known-answer", "known-answer", "Z" * 16), ("law", "law", "law", "ZZZZ"),
               ("coherence", "coherence-xx", "coherence", "XXZZ"), ("coherence", "coherence-yy", "coherence", "YYZZ"))


def small_model(law=None, circuit=None, gate_lists=True, uncarried=()):
    """The small question, its three jobs and its compile. `law` and `circuit` replace the law file and the law
    circuit. With `gate_lists` false the crate carries none of the compile's gate lists, and otherwise all but those
    `uncarried` names; its manifest names all four either way."""
    circuit = circuit if circuit is not None else qasm(4, small_gates())
    m = Model(source=sha(circuit))
    p1_jobs(m, SMALL_LAW_COUNTS, (SMALL_XX, SMALL_YY), 4)
    m.file("question/law.json", law if law is not None else small_law_bytes())
    m.file(SMALL_CIRCUIT_PATH, circuit)
    logical = {"law": qasm(4, small_gates(), measured=True),
               "coherence-xx": qasm(4, small_gates(), "XXZZ", True),
               "coherence-yy": qasm(4, small_gates(), "YYZZ", True)}
    gates = {k: transpile(v) for k, v in logical.items()}
    gates["known-answer"] = data("known-answer.gates.json")
    logical["known-answer"] = data("known-answer.qasm")
    for k in ("law", "coherence-xx", "coherence-yy"):
        m.file(f"bundle/{k}.qasm", logical[k])
    carried = [k for k in gates if gate_lists and k not in uncarried]
    for k in carried:
        m.file(f"bundle/{k}.gates.json", gates[k])
    m.file("bundle/manifest.json", manifest([(j, n, r, b, logical[n], gates[n]) for j, n, r, b in SMALL_NAMED]))
    compile_entity(m, "#compile-synth-morning",
                   [(f"bundle/{n}.qasm", f"bundle/{n}.gates.json" if n in carried else None) for _, n, _, _ in SMALL_NAMED])
    m.entity("#question", ["CreativeWork", "qro:Question"], name="the small question",
             object=refs(SMALL_CIRCUIT_PATH, "bundle/known-answer.qasm", "bundle/law.qasm", "#rule-ibm"))
    return m


def sheet_model(sheet="sheet-01"):
    """The small crate with a second compile in the shape of P1's sheets (P1.md, 2026-10-26T10:55:57Z): its bundle
    holds its own manifest and the known-answer circuit's two files, nothing else. Its manifest names the same four
    circuits as the morning's, so its law and coherence circuits and their gate lists are the morning bundle's, found
    by digest outside its own `object` and `result`."""
    m = small_model()
    names = [n for _, n, _, _ in SMALL_NAMED]
    logical = {n: m.files[f"bundle/{n}.qasm"] for n in names}
    gates = {n: m.files[f"bundle/{n}.gates.json"] for n in names}
    m.file(f"{sheet}/known-answer.qasm", logical["known-answer"])
    m.file(f"{sheet}/known-answer.gates.json", gates["known-answer"])
    m.file(f"{sheet}/manifest.json", manifest([(f"{sheet} {j}", n, r, b, logical[n], gates[n])
                                               for j, n, r, b in SMALL_NAMED]))
    compile_entity(m, f"#compile-synth-{sheet}", [(f"{sheet}/known-answer.qasm", f"{sheet}/known-answer.gates.json")],
                   manifest_path=f"{sheet}/manifest.json")
    return m


def real_counts(shots=200, seed=7):
    """Law counts drawn from v0's law, deterministically, with one shot of four crystals."""
    law = p2_law.read(p2_law.law_bytes())
    draws = random.Random(seed).choices(law.layouts, weights=law.weights, k=shots - 2)
    counts = {}
    for Y in draws + [next(Y for Y, w in zip(law.layouts, law.weights) if w == 0), (0, 1, 2, 3)]:
        counts[Y] = counts.get(Y, 0) + 1
    return counts


REAL_XX = {(): 20, (0, 1): 21, (0,): 9, (1, 5): 10}               # 41 of 60 agree
REAL_YY = {(4,): 20, (0, 1, 6): 20, (1,): 11, (0, 9): 9}          # 40 of 60 agree


def real_model():
    """v0's question and kingston's morning compile (the copies), with synthetic shots."""
    m = Model()
    p1_jobs(m, real_counts(), (REAL_XX, REAL_YY), 16)
    m.file("question/law.json", p2_law.law_bytes())
    m.file(SOURCE_PATH, data("circuit-ed767c01bd4b851d.qasm"))
    for k in ("law", "coherence-xx", "coherence-yy"):
        m.file(f"bundle/{k}.qasm", data(f"{k}.qasm"))
    for k in ("law", "coherence-xx", "coherence-yy", "known-answer"):
        m.file(f"bundle/{k}.gates.json", data(f"{k}.gates.json"))
    m.file("bundle/manifest.json", data("manifest.json"))
    names = ("known-answer", "law", "coherence-xx", "coherence-yy")
    compile_entity(m, "#compile-ibm_kingston-morning", [(f"bundle/{n}.qasm", f"bundle/{n}.gates.json") for n in names])
    m.entity("#question", ["CreativeWork", "qro:Question"], name="v0's question",
             object=refs(SOURCE_PATH, "bundle/known-answer.qasm", "bundle/law.qasm", "#rule-ibm"))
    return m


# -- an Atlas-shaped crate ---------------------------------------------------------------------------------------------
ATLAS_FORM, VECTOR_FORM = "atlas-tomography-result/v1", "atlas-known-answer-vector/v1"
ATLAS_RULE = "quantum_film.atlas.decode/v1"
ALL_Z, XX_SETTING = "IIIIIIIIIIIIIIZZ", "IIIIIIIIIIIIIIXX"


def atlas_string(label, occupied):
    """The count string, position 0 leftmost, of an Atlas setting `label` in which exactly the qubits `occupied` read
    1, under the rule's own order, `atlas-register`. Written from the rule's statement (qro/p1_decode.py's docstring),
    not from its code: the string is little-endian over [the setting's non-I qubits, ascending] + [every other qubit,
    ascending], and the label is in circuit order, qubit 0 rightmost."""
    n = len(label)
    active = [q for q in range(n) if label[n - 1 - q] != "I"]
    register = active + [q for q in range(n) if q not in active]
    return "".join("1" if register[n - 1 - p] in occupied else "0" for p in range(n))


def atlas_result(layouts, job):
    """A tomography result in Quantum-Film's wrapper: the all-Z setting holding `layouts` ({a tuple of occupied qubits:
    shots}), and an XX setting beside it, as the engine measures other settings than the all-Z one."""
    shots = sum(layouts.values())
    measurements = {label: {"counts": {atlas_string(label, set(occ)): n for occ, n in layouts.items()}, "shots": shots}
                    for label in (ALL_Z, XX_SETTING)}
    result = {"measurements": measurements, "observables": {}, "density_matrices": {}}
    return json.dumps({"job_id": job, "path": f"/api/v1/jobs/{job}/result", "response": {"result": result},
                       "status": 200, "taken_from": "/result"}, indent=1, sort_keys=True).encode("ascii") + b"\n"


def atlas_vector():
    """The frozen known-answer vector's form, one setting: 32 patterns, four shots each, pattern j setting qubit q iff
    j < 2q + 1. P2 never reads it; it is there as P1's model has it."""
    counts = {}
    for j in range(32):
        s = atlas_string(ALL_Z, {q for q in range(16) if j < 2 * q + 1})
        counts[s] = counts.get(s, 0) + 4
    return json.dumps({"job": "synthetic-vector", "measurements": {ALL_Z: {"counts": counts, "shots": 128}}},
                      indent=1, sort_keys=True).encode("ascii") + b"\n"


def atlas_model(coherence=False):
    """An Atlas-shaped crate, as P1's model has one (P1.md, item 1): v0's question; a law job whose raw result is a
    tomography result; the frozen vector's known-answer job; no compile. Each Pub has its job's raw result, decoded by
    Atlas's rule, which reads a result's all-Z setting alone. With `coherence`, a third job whose Pub reads qubits 0
    and 1 in X, its raw result a tomography result too: a coherence PUB on an Atlas raw result, which P2 does not
    measure (its stated limit 10)."""
    m = Model()
    m.file("question/law.json", p2_law.law_bytes())
    m.file(SOURCE_PATH, data("circuit-ed767c01bd4b851d.qasm"))
    m.entity("#question", ["CreativeWork", "qro:Question"], name="v0's question", object=refs(SOURCE_PATH, "#rule-atlas"))
    m.entity("#device-atlas", "IndividualProduct", name="atlas-emu", **{"qro:deviceKind": "simulator"})
    m.entity("#rule-atlas", "SoftwareApplication", name=ATLAS_RULE)
    counts = real_counts(shots=60, seed=11)
    shots = sum(counts.values())
    jobs = [("alaw", "law", None, "law/result.json", atlas_result(counts, "synthetic-law"), ATLAS_FORM, shots),
            ("avec", "known-answer", None, "vector/vector.json", atlas_vector(), VECTOR_FORM, 128)]
    if coherence:
        jobs.append(("acoh", "coherence", "XX" + "Z" * 14, "coherence/result.json",
                     atlas_result(counts, "synthetic-coherence"), ATLAS_FORM, shots))
    for j, role, basis, raw, b, form, n in jobs:
        m.file(raw, b, ["File", "qro:RawResult"], **{"qro:rawForm": form, "qro:shots": n})
        m.entity(f"#pub-{j}-0", "qro:Pub", **{"qro:role": role, "qro:commitment": "none",
                                               **({"qro:basis": basis} if basis else {})})
        m.entity("#job-" + j, ["CreateAction", "qro:Job"], name=f"job {j}", instrument=ref("#rule-atlas"),
                 object=refs(f"#pub-{j}-0"), result=refs(raw), **{
                     "qro:device": ref("#device-atlas"), "qro:jobId": j, "startTime": "unknown", "endTime": "unknown",
                     "qro:calibrationLink": "unexposed", "qro:kitCommit": "unknown", "qro:clock": "provider"})
        m.entity("#decode-" + j, ["CreateAction", "qro:Decode"], instrument=ref("#rule-atlas"), object=refs(raw),
                 **{"qro:decodeRule": ATLAS_RULE, "qro:bitOrder": "atlas-register",
                    "qro:knownAnswer": ref("#pub-avec-0")})
    return m


# -- reading and editing a written crate -------------------------------------------------------------------------------
def read_md(crate):
    return reader.read((Path(crate) / canonical.DESCRIPTOR).read_bytes())


def edit(crate, fn, strict=True):
    """The written crate's metadata edited by fn(entities by id) and written again, no digest touched."""
    p = Path(crate) / canonical.DESCRIPTOR
    md = json.loads(p.read_bytes())
    ents = {e["@id"]: e for e in md["@graph"]}
    fn(ents)
    md["@graph"] = list(ents.values())
    p.write_bytes(canonical.write(md) if strict else canonical.dumps(canonical.arrange(md)))
    return crate


def rewrite(crate, rel, b):
    """A file's bytes replaced, and its entity's digest and size with them, so step 2 holds."""
    Path(crate).joinpath(*rel.split("/")).write_bytes(b)
    return edit(crate, lambda ents: ents[rel].update(sha256=sha(b), contentSize=str(len(b))))


def refusal(step, crate, md=None):
    """The Refused a P2 step raises on a written crate, or None where it accepts it."""
    from qro import p2_steps
    try:
        getattr(p2_steps, f"step{step}")(Path(crate), read_md(crate) if md is None else md)
    except Refused as r:
        return r
    return None
