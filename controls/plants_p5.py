"""P5's four controls (study QRO-0, section 11; P5's design, item 11; P5.1), each planted in a copy of the unit twin, and the
toolkit that builds the twin, which P5's tests use as well.

The unit twin is a SYNTHETIC unit crate: built by this module, in the crate's own layout, from the bundle files of P1's
twin (tests/p1/data/moth, kingston's morning bundle) re-labelled as three devices, with the complement's gate list derived
from the known answer's by flipping its X set, a salt and a commitment of its own for each of the 54 PUBs, and counts drawn by
a seeded `random` from the law's weights (and, for the known answers, a fixed readout flip). It proves the checker and the
kit's logic, not any device, and is never offered as data: the metadata's root says so in its name. It enters the checker
through the generator `qro-p5-unit`, written with qro.canonical.write, so every step of the nine runs on it. No qiskit and
none of Moth's data enters the repository beyond what P1's twin already holds.

`build_unit(dest, **options)` writes the unit's files and its metadata into `dest/crate` and returns the crate directory.
Options: `kind` ("simulator", the default, or "qpu": ibm_* devices, execution spans in the raw results, a real-shaped
metrics wrapper), `divisor` (the shots divisor, 128 by default: 16 shots a control PUB and 128 a film PUB), `order`
("interleaved", the recipe's, or "blocks": the devices' jobs run K x6, M x6, F x6), `skip` (a set of (device, job name) the
unit lacks), `failed` (a set of (device, job name) that ended with a status file), `read` (qpu only: the owner's read of the
provider's copies, one snapshot a device and a job record and a result record a job), `fault` (a name of FAULTS: a fault in
the counts of one job, written consistently into the raw result, the record and every digest, so that the generator holds
and the steps decide). This module builds nothing when it is imported.
"""
import atexit
import hashlib
import json
import random
import shutil
import tempfile
import zlib
from base64 import b64encode
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from qro import canonical, p1_commit, p2_law, p5_generate, p5_tree, p5_unit as U

ROOT = Path(__file__).resolve().parents[1]
TWIN = ROOT / "tests" / "p1" / "data" / "moth" / "docs" / "records"
TWIN_BUNDLE = TWIN / "2026-10-05" / "ibm" / "ibm_kingston" / "bundle"
UTC = timezone.utc
START = datetime(2026, 11, 1, 10, 0, 0, tzinfo=UTC)
FAULTS = ("ka-fez-first-control", "complement-fez-first-control")
KIT_COMMIT = "0123456789abcdef0123456789abcdef01234567"
KIT_TAG = "qro-kit-v0.1.0"
IBM_LICENCE_NAME = "synthetic"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text(obj):
    """Quantum-Film's one file form of a manifest, a gate list or a record: sorted keys, a one-space indent, ASCII."""
    return (json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii")


def stamp(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def zoneless(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")


# -- IBM's result text (the shapes of tests/p1/p1_builder.py) -----------------------------------------------------------------------
def npy(rows):
    head = "{'descr': '|u1', 'fortran_order': False, 'shape': (%d, 2), }" % len(rows)
    head += " " * (-(10 + len(head) + 1) % 64) + "\n"
    return b"\x93NUMPY\x01\x00" + len(head).to_bytes(2, "little") + head.encode("ascii") \
        + b"".join(v.to_bytes(2, "big") for v in rows)


def raw_result(pubs, echoes, span=None):
    """IBM's SamplerV2 result text for `pubs` (lists of 16-bit outcomes), each PUB echoing its commitment."""
    results = []
    for rows, echo in zip(pubs, echoes, strict=True):
        packed = b64encode(zlib.compress(npy(rows))).decode("ascii")
        results.append({"__type__": "SamplerPubResult", "__value__": {
            "data": {"__type__": "DataBin", "__value__": {
                "field_names": ["meas"], "field_types": ["<class 'qiskit.primitives.containers.bit_array.BitArray'>"],
                "shape": [], "fields": {"meas": {"__type__": "BitArray", "__value__": {
                    "array": {"__type__": "ndarray", "__value__": packed}, "num_bits": 16}}}}},
            "metadata": {"circuit_metadata": {"qf_commitment": echo}}}})
    value = {"pub_results": results, "metadata": {"version": 2}}
    if span is not None:
        value["metadata"]["execution"] = {"execution_spans": {"__type__": "ExecutionSpans", "__value__": {"spans": [{
            "__type__": "DoubleSliceSpan", "__value__": {
                "start": {"__type__": "datetime", "__value__": zoneless(span[0])},
                "stop": {"__type__": "datetime", "__value__": zoneless(span[1])},
                "data_slices": {"0": [[len(pubs[0])], 0, 1]}}}]}}}
    return json.dumps({"__type__": "PrimitiveResult", "__value__": value}).encode("utf-8")


def outcome(qubits):
    return sum(1 << q for q in qubits)


def snapshot_bytes(device, when, newest):
    d = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")      # noqa: E731
    early = d(newest - timedelta(minutes=1))
    doc = {"backend_name": device, "backend_version": "1.0.0", "last_update_date": d(when),
           "gates": [{"gate": "cz", "name": "cz0_1", "qubits": [0, 1], "parameters": [
               {"date": early, "name": "gate_error", "unit": "", "value": 0.0125}]}],
           "general": [{"date": early, "name": "zz_01", "unit": "GHz", "value": 5.5e-06}],
           "general_qlists": [{"name": "lf_2", "qubits": [0, 1]}],
           "qubits": [[{"date": d(newest), "name": "T1", "unit": "us", "value": 100.5}]]}
    return json.dumps(doc, indent=1, sort_keys=True).encode("utf-8") + b"\n"


# -- the bundle ---------------------------------------------------------------------------------------------------------------------
def _twin_files():
    """{circuit: {extension: bytes}} of the twin's four circuits, with the complement derived."""
    files = {}
    for name in ("known-answer", "law", "coherence-xx", "coherence-yy"):
        files[name] = {ext: (TWIN_BUNDLE / f"{name}.{ext}").read_bytes() for ext in ("qasm", "qpy", "gates.json", "isa.qasm3")}
    source = (TWIN / "2026-09-25" / "p3" / "circuit-ed767c01bd4b851d.qasm").read_text(encoding="ascii")
    ka = json.loads(files["known-answer"]["gates.json"])
    chain = ka["layout"]["initial"]
    rest = [g for g in ka["gates"] if g[0] != "x"]
    comp = dict(ka, gates=[["x", [chain[q]], [], []] for q in U.KNOWN_COMPLEMENT] + rest)
    q3 = files["known-answer"]["isa.qasm3"].decode("ascii").split("\n")
    first = next(i for i, ln in enumerate(q3) if ln.startswith("x $"))
    last = max(i for i, ln in enumerate(q3) if ln.startswith("x $"))
    q3 = q3[:first] + [f"x ${chain[q]};" for q in U.KNOWN_COMPLEMENT] + q3[last + 1:]
    files["known-complement"] = {"qasm": U.logical_qasm("known-complement", source).encode("ascii"),
                                 "gates.json": text(comp), "isa.qasm3": "\n".join(q3).encode("ascii"),
                                 "qpy": b"a synthetic stand-in for the complement's QPY file: the twin has no qiskit\n"}
    for name in ("known-answer", "law", "coherence-xx", "coherence-yy"):
        assert files[name]["qasm"] == U.logical_qasm(name, source).encode("ascii"), name
    return files, json.loads((TWIN_BUNDLE / "manifest.json").read_bytes()), source


def _entry_isa(twin_manifest, name):
    for j in twin_manifest["jobs"]:
        for c in j["circuits"]:
            if c["name"] == name:
                return c
    return None


def _device_bundle(dest, device, kind, divisor, unit_digest, files, twin, order):
    """Write one device's bundle into dest/unit/<device>/bundle; return (manifest dict, its SHA-256)."""
    bdir = dest / "unit" / device / "bundle"
    bdir.mkdir(parents=True)
    for name, parts in files.items():
        for ext, data in parts.items():
            (bdir / f"{name}.{ext}").write_bytes(data)
    readme = (f"A synthetic twin of the unit's bundle for {device}: tests only, built from P1's twin by controls/plants_p5.py.\n"
              ).encode("ascii")
    (bdir / "README.md").write_bytes(readme)
    options = {"dynamical_decoupling": {"enable": False}, "execution": {"init_qubits": True, "rep_delay": 0.00025},
               "twirling": {"enable_gates": False, "enable_measure": False}}
    m = {"backend": device, "compile": twin["compile"], "decode": U.DECODE, "format": U.BUNDLE_FORMAT,
         "frozen_at": stamp(START - timedelta(hours=3)), "kind": kind, "known_answer": list(U.KNOWN_ANSWER),
         "options": options, "options_sha256": p1_commit.options_digest(options), "pair": list(U.PAIR), "program": U.PROGRAM,
         "readme_sha256": sha(readme), "route": U.ROUTE, "source": {"path": U.SOURCE_PATH, "sha256": U.SOURCE_SHA256},
         "stock": U.STOCK, "target": dict(twin["target"], name=device), "versions": twin["versions"],
         "unit": {"recipe": U.RECIPE_NAME, "recipe_sha256": U.recipe_sha256(divisor), "shots_divisor": divisor,
                  "device_order": list(U.DEVICE_SETS[kind]), "options_defaulted": []},
         "jobs": []}
    chain = twin["jobs"][0]["circuits"][0]["chain"]
    for name, k, p, pubs in U.jobs_of_device(divisor):
        entries = []
        for pub, cname, role, basis, shots in pubs:
            digest = {n: sha(files[cname][e]) for n, e in (("circuit_sha256", "qasm"), ("isa_sha256", "qpy"),
                                                            ("gates_sha256", "gates.json"), ("qasm3_sha256", "isa.qasm3"))}
            salt = sha(f"{device}|{name}|{pub}|{unit_digest}".encode())
            source_part = {"source_sha256": None if role == "known-answer" else U.SOURCE_SHA256}
            e = {"pub": pub, "name": cname, "role": role, "basis": basis, "shots": shots, **source_part, **digest,
                 "chain": chain, "esp": 0.5, "isa": {"max_abs_error": 0.0}, "salt": salt}
            e["commitment"] = p1_commit.commitment_v3(
                U.STOCK, role, basis, kind, U.ROUTE, device, U.PROGRAM, pub, e["circuit_sha256"], e["isa_sha256"], shots,
                m["options_sha256"], U.DECODE, salt)
            entries.append(e)
        m["jobs"].append({"job": name, "max_execution_time": U.CAPS[k], "circuits": entries})
    data = text(m)
    (bdir / "manifest.json").write_bytes(data)
    return m, sha(data)


# -- the runs -----------------------------------------------------------------------------------------------------------------------
def _job_id(kind, device, name, unit_digest):
    h = sha(f"{device}|{name}|{unit_digest}".encode())
    return ("dryrun-" + h[:16]) if kind == "simulator" else ("d" + h[:19])


def _rows(rng, role, cname, shots, law, fault):
    if role == "known-answer":
        want = U.KNOWN_ANSWER if cname == "known-answer" else U.KNOWN_COMPLEMENT
        if fault:
            return [outcome(U.KNOWN_COMPLEMENT if cname == "known-answer" else U.KNOWN_ANSWER)] * shots
        good = max(shots - max(1, shots // 8), 1)
        rows = [outcome(want)] * good
        for _ in range(shots - good):
            q = rng.choice(want)
            rows.append(outcome(want) ^ (1 << q))
        return rows
    if cname == "law":
        picks = rng.choices(range(len(law.layouts)), weights=law.weights, k=shots)
        return [outcome(law.layouts[i]) for i in picks]
    return [outcome(rng.sample(range(16), law.N)) for _ in range(shots)]


def _counts(rows):
    tally = Counter(rows)
    out = []
    for v in sorted(tally, key=lambda v: tuple(q for q in range(16) if v >> q & 1)):
        out.append([[q for q in range(16) if v >> q & 1], tally[v]])
    return sorted(out)


def build_unit(dest, kind="simulator", divisor=None, order="interleaved", skip=(), failed=(), read=False, fault=None,
               seed=7):
    """The twin unit crate, written into dest/crate (see the module docstring); the crate's directory. A simulator twin
    takes the divisor 128 unless it is given one; a qpu twin has the full shots (a divisor is the local route's)."""
    divisor = divisor or (128 if kind == "simulator" else 1)
    assert fault is None or fault in FAULTS
    assert not read or kind == "qpu", "the owner's read is of a provider's copies: a qpu unit's"
    dest = Path(dest)
    crate = dest / "crate"
    crate.mkdir(parents=True)
    files, twin, source = _twin_files()
    law = p2_law.read(p2_law.law_bytes())
    (crate / "2026-09-25" / "p3").mkdir(parents=True)
    (crate / U.SOURCE_PATH).write_bytes(source.encode("ascii"))
    (crate / U.LICENSE_PATH).write_bytes((ROOT / "tests" / "p1" / "data" / "moth" / "LICENSE").read_bytes())
    devices = U.DEVICE_SETS[kind]
    unit_digest = sha(f"{kind}|{divisor}|{order}|{seed}".encode())
    manifests = {}
    for d in devices:
        manifests[d] = _device_bundle(crate, d, kind, divisor, unit_digest, files, twin, order)
    rng = random.Random(seed)
    names = U.job_order()                                   # [(pass, slot, kind)] in the recipe's order
    index = {}
    for i, (p, s, k) in enumerate(names):
        index[(U.DEVICE_SETS[kind][s], U.job_name(k, p))] = i
    if order == "blocks":
        index = {key: U.DEVICE_SETS[kind].index(key[0]) * 6 + (U.parse_job_name(key[1])[1] - 1) * 2
                 + (U.parse_job_name(key[1])[0] == "film") for key in index}
    read_rows = {}
    for (device, name), i in sorted(index.items(), key=lambda kv: kv[1]):
        if (device, name) in skip:
            continue
        m, mdigest = manifests[device]
        job = next(j for j in m["jobs"] if j["job"] == name)
        k, p = U.parse_job_name(name)
        jid = _job_id(kind, device, name, unit_digest)
        run = crate / "unit" / device / "run"
        run.mkdir(parents=True, exist_ok=True)
        submitted = START + timedelta(minutes=10 * index[(device, name)])
        running, finished = submitted + timedelta(seconds=2), submitted + timedelta(seconds=6)
        span = (running + timedelta(seconds=1), running + timedelta(seconds=3)) if kind == "qpu" else None
        (run / f"{name}-submitting.json").write_bytes(text({"begun_at": stamp(submitted - timedelta(seconds=3)),
                                                            "bundle_sha256": mdigest, "job": name}))
        commitments = [c["commitment"] for c in job["circuits"]]
        (run / f"{name}-line.json").write_bytes(text({
            "backend": device, "bundle_sha256": mdigest, "commitments": commitments, "format": "quantum-film/hardware-job/v1",
            "job_id": jid, "kind": kind, "program": U.PROGRAM, "route": U.ROUTE, "stock": U.STOCK,
            "submitted_at": stamp(submitted)}))
        if (device, name) in failed:
            (run / f"{name}-status.json").write_bytes(text({"state": {"status": "Cancelled"}, "usage": None}))
            continue
        pubs, records = [], []
        for c in job["circuits"]:
            first_control = device == "fake_fez" and name == "control-1"
            wrong = first_control and ((fault == "ka-fez-first-control" and c["pub"] == 0)
                                       or (fault == "complement-fez-first-control" and c["pub"] == 1))
            pubs.append(_rows(rng, c["role"], c["name"], c["shots"], law, wrong))
        raw = raw_result(pubs, commitments, span)
        (run / f"{name}-raw.json").write_bytes(raw)
        for c, rows in zip(job["circuits"], pubs, strict=True):
            doc = {"basis": c["basis"], "code": {"quantum_film": "0.1.0"}, "counts": _counts(rows),
                   "format": "quantum-film/device-run/v1",
                   "law": {"L": 4, "M": 16, "N": 5, "borrows": "trix", "family": "determinantal", "fermi_r2": 1,
                           "id": "pauli-4x4"},
                   "role": c["role"], "stock": U.STOCK,
                   "source": {"backend": device, "circuit_sha256": c["circuit_sha256"], "commitment": c["commitment"],
                              "decode": U.DECODE, "fixed_at": stamp(finished + timedelta(seconds=1)),
                              "isa_sha256": c["isa_sha256"], "job_id": jid, "kind": kind, "options": m["options"],
                              "options_sha256": m["options_sha256"], "program": U.PROGRAM, "pub": c["pub"],
                              "route": U.ROUTE, "salt": c["salt"], "shots": c["shots"], "submitted_at": stamp(submitted)}}
            doc["digest"] = hashlib.sha256(json.dumps({k: v for k, v in doc.items()}, sort_keys=True, separators=(",", ":"),
                                                       ensure_ascii=True).encode("ascii")).hexdigest()
            (run / f"{name}-pub{c['pub']}-{c['name']}.json").write_bytes(text(doc))
            records.append(doc)
        stamps = {"created": stamp(submitted), "finished": stamp(finished), "running": stamp(running)}
        if kind == "simulator":
            metrics = {"backend": device, "dry_run": True, "job": {"created": stamp(submitted)}, "job_id": jid,
                       "metrics": {"timestamps": stamps}, "result_metadata": None}
        else:
            metrics = {"backend": device, "job": {"backend": device, "cost": 4, "created": stamp(submitted),
                                                  "program": {"id": "sampler"}, "state": {"status": "Completed"},
                                                  "status": "Completed"},
                       "job_id": jid, "metrics": {"circuits_execution_time_ns": 1, "qiskit_version": "qiskit",
                                                  "timestamps": stamps, "usage": {"qpu_charge_time_seconds": 2}},
                       "result_metadata": None}
        (run / f"{name}-metrics.json").write_bytes(text(metrics))
        if k == "control":
            first = records[0]
            ones = {tuple(c[0]): c[1] for c in first["counts"]}
            modal = min(ones, key=lambda t: (-ones[t], t))
            (run / f"{name}-verdict.json").write_bytes(text({
                "expected": list(U.KNOWN_ANSWER), "holds": modal == U.KNOWN_ANSWER, "mirror_share": 0.0, "modal": list(modal),
                "share": ones.get(U.KNOWN_ANSWER, 0) / job["circuits"][0]["shots"], "shots": job["circuits"][0]["shots"]}))
        read_rows[(device, jid)] = (name, job, span, running, raw, mdigest)
    unit = {"bundles": [manifests[d][1] for d in devices], "contributor": "withheld", "devices": list(devices),
            "format": U.UNIT_FORMAT, "frozen_at": stamp(START - timedelta(hours=2)), "kind": kind, "kit_commit": KIT_COMMIT,
            "kit_tag": KIT_TAG, "recipe": U.RECIPE_NAME, "recipe_sha256": U.recipe_sha256(divisor), "route": U.ROUTE,
            "shots_divisor": divisor}
    (crate / "unit" / "UNIT.json").write_bytes(text(unit))
    if read:
        _write_read(crate, devices, read_rows)
    finalize(crate)
    return crate


def _write_read(crate, devices, rows):
    """The owner's read: a snapshot a device, a job record and a result record a job, and the two MANIFESTs."""
    when = START - timedelta(hours=1)
    listed = {"ibm-refetch": {}, "ibm-results-refetch": {}}
    for d in devices:
        snap = f"properties-{when.strftime('%Y%m%dT%H%M%SZ')}.json"
        data = snapshot_bytes(d, when, when)
        base = crate / "unit" / "read"
        for tag in ("ibm-refetch", "ibm-results-refetch"):
            (base / tag / d).mkdir(parents=True, exist_ok=True)
        (base / "ibm-refetch" / d / snap).write_bytes(data)
        listed["ibm-refetch"][f"{d}/{snap}"] = data
    for (device, jid), (name, job, span, running, raw, mdigest) in sorted(rows.items()):
        base = crate / "unit" / "read"
        snap = f"{device}/properties-{(START - timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')}.json"
        n = len(job["circuits"])
        doc = {"format": "qro-crate/ibm-refetch/v0", "device": device, "job_id": jid, "role": job["circuits"][0]["role"],
               "holds": {"commitments_equal": True, "created_equal_to_line": True, "options_equal_to_manifest": True,
                         "pubs_in_ibm_copy": n, "pubs_in_line": n,
                         "pubs": [{"gate_list_equal": True, "gates_equal": True, "commitment_in_ibm_copy": c["commitment"],
                                   "commitment_in_line": c["commitment"]} for c in job["circuits"]]},
               "calibration": {"first_shot": stamp(span[0]), "running": stamp(running),
                               "before_first_shot": {"file": snap}, "before_running": {"file": snap}}}
        data = text(doc)
        (base / "ibm-refetch" / device / f"{jid}.json").write_bytes(data)
        listed["ibm-refetch"][f"{device}/{jid}.json"] = data
        rel = f"unit/{device}/run/{name}-raw.json"
        result = {"format": "qro-crate/ibm-results-refetch/v0", "device": device, "job_id": jid,
                  "role": job["circuits"][0]["role"], "agree_at": "bytes", "bytes_equal": True,
                  "committed": {"path": rel, "bytes": len(raw), "sha256": sha(raw)},
                  "ibm_copy": {"bytes": len(raw), "sha256": sha(raw)}}
        data = text(result)
        (base / "ibm-results-refetch" / device / f"{jid}.json").write_bytes(data)
        listed["ibm-results-refetch"][f"{device}/{jid}.json"] = data
    for tag, fmt in (("ibm-refetch", "qro-crate/ibm-refetch-manifest/v0"),
                     ("ibm-results-refetch", "qro-crate/ibm-results-refetch-manifest/v0")):
        files = [{"bytes": len(b), "path": p, "sha256": sha(b)} for p, b in sorted(listed[tag].items())]
        (crate / "unit" / "read" / tag / "MANIFEST.json").write_bytes(text({"files": files, "format": fmt}))


def finalize(crate):
    """The question's files (P2's, where its module is present) and the metadata, written as the kit's crate command writes
    them: regenerated from the files by `qro-p5-unit`, with the header the twin's builder states."""
    crate = Path(crate)
    meta = crate / canonical.DESCRIPTOR
    if meta.exists():
        meta.unlink()

    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    p5_generate.finalize(crate, write, now=START, writer="qro, the P5 unit twin's builder (synthetic, tests only)")


def twin_unit(dest):
    """The twin, accepted by the checker: a simulator unit of three fake devices."""
    return build_unit(dest)


# -- the forger's hand, and the controls as edits of any built unit crate (the twin's, or a real local unit's) ------------
class Forge:
    """Edits a built unit crate's records the way a forger would, recomputing every digest a record holds over what it
    changed, so that the generator's guards decide and not a stale digest: `seal_device` after a manifest changes, `put`
    for Quantum-Film's file form, `set_rows` for a PUB's shots (the raw result, the record's counts and its digest), and
    `regenerate` for the metadata, written as finalize writes it."""

    def __init__(self, crate):
        self.crate = Path(crate)

    def path(self, rel):
        return self.crate.joinpath(*rel.split("/"))

    def read(self, rel):
        return self.path(rel).read_bytes()

    def write(self, rel, data):
        self.path(rel).write_bytes(data)

    def remove(self, rel):
        self.path(rel).unlink()

    def json(self, rel):
        return json.loads(self.read(rel))

    def put(self, rel, doc):
        self.write(rel, text(doc))

    def run_files(self, device, job):
        """The relative paths of a job's files in the crate."""
        base = self.path(f"unit/{device}/run")
        return sorted(f"unit/{device}/run/{p.name}" for p in base.glob(f"{job}-*.json" if job else "*.json"))

    def seal_device(self, device):
        """The manifest's new digest into UNIT.json and into every line and marker of the device."""
        digest = sha(self.read(f"unit/{device}/bundle/manifest.json"))
        unit = self.json("unit/UNIT.json")
        unit["bundles"][unit["devices"].index(device)] = digest
        self.put("unit/UNIT.json", unit)
        for rel in self.run_files(device, ""):
            if rel.endswith(("-line.json", "-submitting.json")):
                doc = self.json(rel)
                doc["bundle_sha256"] = digest
                self.put(rel, doc)
        return digest

    def edit_manifest(self, device, edit):
        rel = f"unit/{device}/bundle/manifest.json"
        doc = self.json(rel)
        edit(doc)
        self.put(rel, doc)
        return self.seal_device(device)

    def edit_record(self, device, job, pub, edit):
        rel = next(r for r in self.run_files(device, job) if f"-pub{pub}-" in r)
        doc = self.json(rel)
        edit(doc)
        doc["digest"] = hashlib.sha256(json.dumps({k: v for k, v in doc.items() if k != "digest"}, sort_keys=True,
                                                   separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()
        self.put(rel, doc)
        return rel

    def set_rows(self, device, job, pub, rows):
        """PUB `pub` of the job holds exactly `rows` (16-bit outcomes), in its raw result, its record's counts and digest."""
        raw_rel = f"unit/{device}/run/{job}-raw.json"
        doc = json.loads(self.read(raw_rel))
        meas = doc["__value__"]["pub_results"][pub]["__value__"]["data"]["__value__"]["fields"]["meas"]["__value__"]
        meas["array"]["__value__"] = b64encode(zlib.compress(npy(rows))).decode("ascii")
        self.write(raw_rel, json.dumps(doc).encode("utf-8"))
        self.edit_record(device, job, pub, lambda r: r.update(counts=_counts(rows)))

    def regenerate(self):
        finalize(self.crate)
        return self.crate


def plant_known_answer(crate, device="fake_fez"):
    """The first control job of `device` read its known answer as the complement: every shot of PUB 0 the complement's
    outcome, the raw result, the record and every digest consistent, and the Decode still claiming msb-first."""
    f = Forge(crate)
    shots = f.json(f"unit/{device}/run/control-1-pub0-known-answer.json")["source"]["shots"]
    f.set_rows(device, "control-1", 0, [outcome(U.KNOWN_COMPLEMENT)] * shots)
    return f.regenerate()


def plant_complement(crate, device="fake_fez"):
    """The same fault in the complement's PUB alone: the checker's step 5 holds one PUB, so the checker accepts."""
    f = Forge(crate)
    shots = f.json(f"unit/{device}/run/control-1-pub1-known-complement.json")["source"]["shots"]
    f.set_rows(device, "control-1", 1, [outcome(U.KNOWN_ANSWER)] * shots)
    return f.regenerate()


def plant_incomplete(crate, device="fake_fez", job="film-3"):
    """The job's files removed (the manifest still plans it) and the metadata regenerated."""
    f = Forge(crate)
    for rel in f.run_files(device, job):
        f.remove(rel)
    return f.regenerate()


def plant_interleaved(crate):
    """The 18 lines' submitted times (and everything that repeats one) written in blocks, K x6, M x6, F x6."""
    f = Forge(crate)
    unit = f.json("unit/UNIT.json")
    for d, device in enumerate(unit["devices"]):
        for rel in f.run_files(device, ""):
            if not rel.endswith("-line.json"):
                continue
            job = rel.rsplit("/", 1)[1][:-len("-line.json")]
            kind, p = U.parse_job_name(job)
            when = START + timedelta(minutes=10 * (d * 6 + (p - 1) * 2 + (kind == "film")))
            line = f.json(rel)
            line["submitted_at"] = stamp(when)
            f.put(rel, line)
            metrics_rel = rel.replace("-line.json", "-metrics.json")
            if f.path(metrics_rel).exists():
                m = f.json(metrics_rel)
                m["job"]["created"] = m["metrics"]["timestamps"]["created"] = stamp(when)
                m["metrics"]["timestamps"]["running"] = stamp(when + timedelta(seconds=2))
                m["metrics"]["timestamps"]["finished"] = stamp(when + timedelta(seconds=6))
                f.put(metrics_rel, m)
            for pub in range(len(U.CIRCUITS[kind])):
                if any(f"-pub{pub}-" in r for r in f.run_files(device, job)):
                    f.edit_record(device, job, pub, lambda r, w=when: r["source"].update(
                        submitted_at=stamp(w), fixed_at=stamp(w + timedelta(seconds=7))))
    return f.regenerate()


_PRISTINE = []


def pristine(**options):
    """A built twin in this process, in a directory of the system's temporary files nothing writes to again."""
    key = tuple(sorted(options.items(), key=lambda kv: kv[0]))
    for k, path in _PRISTINE:
        if k == key:
            return path
    d = Path(tempfile.mkdtemp(prefix="qro-p5-twin-"))
    atexit.register(shutil.rmtree, d, True)              # the directory this process made, removed when it ends
    path = build_unit(d, **{k: (set(v) if isinstance(v, frozenset) else v) for k, v in options.items()})
    _PRISTINE.append((key, path))
    return path


def copy_of(dest, **options):
    """A fresh copy of a built twin in dest/crate."""
    src = pristine(**options)
    out = Path(dest) / "crate"
    shutil.copytree(src, out)
    return out


# -- the controls ----------------------------------------------------------------------------------------------------------------------
def unit_known_answer(d):
    """The first control job of fez: its known-answer PUB's shots all the complement's outcome, every digest consistent."""
    return build_unit(d, fault="ka-fez-first-control")


def unit_incomplete(d):
    """The unit without fez's third film job."""
    return build_unit(d, skip=frozenset({("fake_fez", "film-3")}))


def not_interleaved(d):
    """The unit whose jobs ran in blocks, K x6, M x6, F x6."""
    return build_unit(d, order="blocks")


def kit_dirty(d):
    """A throwaway repository with a tracked file modified, which tree_state refuses before anything is submitted. The
    refusal is the plant's own outcome (controls/registry.py)."""
    import subprocess
    repo = Path(d) / "kit"
    repo.mkdir()

    def git(*args):
        subprocess.run(["git", "-c", "user.name=twin", "-c", "user.email=twin@example.invalid", "-c", "core.autocrlf=false",
                        *args], cwd=repo, check=True, capture_output=True, stdin=subprocess.DEVNULL)
    git("init", "-q")
    (repo / "kit.py").write_bytes(b"print('the kit')\n")
    git("add", "kit.py")
    git("commit", "-q", "-m", "the kit")
    git("tag", "qro-kit-v0.0.1")
    (repo / "kit.py").write_bytes(b"print('the kit, changed')\n")
    p5_tree.tree_state(repo)
    raise AssertionError("tree_state accepted a tree with a modified tracked file")


def _says(planted):
    return U.read(planted).status().sentences()


PLANTS = {"unit-known-answer": unit_known_answer, "unit-incomplete": unit_incomplete, "not-interleaved": not_interleaved,
          "kit-dirty": kit_dirty}
STATEMENTS = {"unit-incomplete": _says, "not-interleaved": _says}
TWINS = {"unit-incomplete": twin_unit, "not-interleaved": twin_unit}
