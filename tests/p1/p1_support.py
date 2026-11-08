"""Helpers for P1.2's tests (P1.2): a fresh copy of the twin, the generator run with its guard named, and the memo that
keeps the three big snapshot files from being parsed afresh by each of the many tests that run the generator on a twin
with one record altered. It names no function `test*` and no class `Test*`.

The twin is a crate controls/plants_p1.py builds once in a process; a test takes a copy of it. There are two, one
tree each (the lead's ruling, 2026-11-08): the twin as the tree builds it, with P2's module when the tree holds it, for a
test that means the tree as merged and pins nothing; and the twin as P1 builds it with the module absent
(`alone=True`), for a test that means P1 alone and pins the module absent (`pin_p2`) for its generator. Build either
before pinning anything: a test that pins `p1_generate.p2_module` and then asks for the first copy would build the twin
with the pin, and the helper refuses that (plants_p1.pristine_twin does).
"""
import hashlib
import json
import os
import shutil
import types
from pathlib import Path

import p1_builder
from controls import plants_p1
from qro import canonical, checker, p1_calibration, p1_commit, p1_forms, p1_generate, p1_records, p1_steps, reader
from qro.refusal import Refused

ROOT = Path(__file__).resolve().parents[2]
TWIN = plants_p1.TWIN
IBM_DIR = "2026-10-05/ibm/ibm_kingston"
MORNING_KA = f"{IBM_DIR}/run/known-answer"
MORNING_COH = f"{IBM_DIR}/run/coherence"
SHEET1_KA = f"{IBM_DIR}/sheet-01/run/known-answer"
SHEET2_KA = f"{IBM_DIR}/sheet-02/run/known-answer"
BUNDLE = f"{IBM_DIR}/bundle"
SHEET1_BUNDLE, SHEET2_BUNDLE = f"{IBM_DIR}/sheet-01/bundle", f"{IBM_DIR}/sheet-02/bundle"
MANIFEST = f"{BUNDLE}/manifest.json"


def twin_copy(tmp_path, alone=False):
    """A fresh copy of the twin, in tmp_path/crate: the twin as the tree builds it (P2's module present, its question/
    file and entities), or with `alone` the twin as P1 builds it with P2's module absent. A test that means P1 alone takes
    the second and pins P2's module absent for its generator (pin_p2); one that means the tree as merged takes the first
    and pins nothing: none builds with one tree and generates with the other."""
    return plants_p1.twin_crate(tmp_path, alone=alone)


def forge(crate):
    return plants_p1.Forge(crate)


def generated(crate, kind="ibm"):
    """The metadata the crate's generator makes of it: the dict, or a GuardError raised."""
    return (p1_generate.ibm if kind == "ibm" else p1_generate.atlas)(crate)


def guard(crate, kind="ibm"):
    """The GuardError the generator raises on the crate, or None."""
    try:
        generated(crate, kind)
    except p1_generate.GuardError as g:
        return g
    return None


def graph(md):
    return {e["@id"]: e for e in md["@graph"]}


def entity_bytes(md):
    """The canonical bytes of generated metadata, its header and all."""
    return canonical.dumps(canonical.arrange(md))


def pin_p2(monkeypatch, module=None):
    """P1's generators and the adapter see `module` as qro.p2_measures (None: it is absent), whatever the tree holds. A
    test that pins it builds nothing with the tree's own: a twin it takes is the twin_copy(alone=True), and an
    adapter run it makes is under the same pin."""
    monkeypatch.setattr(p1_generate, "p2_module", lambda: module)


def standin(question_files=None, contribute=None):
    """A stand-in for qro.p2_measures: a module object with the two functions P1 calls."""
    return types.SimpleNamespace(question_files=question_files or (lambda crate: {}),
                                 contribute=contribute or (lambda crate, entities: ({}, [])))


_REAL_PARSE, _REAL_CLAIMS, _REAL_LOAD = p1_forms.parse_snapshot, p1_calibration.claims, p1_forms.load_json
_PARSED, _CLAIMED, _LOADED = {}, {}, {}     # by the bytes; by the identity of the snapshot parsed from them; by bytes and error


def memo_parses(monkeypatch):
    """What is parsed from identical bytes is parsed once in the process: the three big snapshot files (and their claims),
    and every JSON document the readers load. The tests that run the generator many times over a twin with one record
    altered would otherwise read each unaltered file again and again. A reader returns what it parsed and no caller changes
    it. (A test of a reader, the snapshot form or the claims does not use this. What fails to parse is never kept.)"""
    def parse(data):
        if data not in _PARSED:
            _PARSED[data] = _REAL_PARSE(data)
        return _PARSED[data]

    def claims(snapshot):
        if id(snapshot) not in _CLAIMED:
            _CLAIMED[id(snapshot)] = (snapshot, _REAL_CLAIMS(snapshot))
        return _CLAIMED[id(snapshot)][1]

    def load_json(data, what, error=p1_forms.RawFormError):
        if (data, error) not in _LOADED:
            _LOADED[(data, error)] = _REAL_LOAD(data, what, error)
        return _LOADED[(data, error)]
    monkeypatch.setattr(p1_forms, "parse_snapshot", parse)
    monkeypatch.setattr(p1_calibration, "claims", claims)
    monkeypatch.setattr(p1_forms, "load_json", load_json)


class Sandbox:
    """One working copy of the twin whose files are hard links to the pristine twin's, restored after each use. A fresh
    copy of the twin costs the host's scan of 73 new files (0.2 s on first opening), where a link is the file already
    scanned: the many tests that plant one fault and run the generator share one. A fault is planted with the forger's
    hand (controls/plants_p1.py), which unlinks a file before it writes it, or by unlinking or adding a file: never by
    writing through a link, which would change the pristine twin too (verify_pristine says so if anything did)."""

    def __init__(self, base, alone=False):
        self.pristine = plants_p1.pristine_twin_alone() if alone else plants_p1.pristine_twin()
        self.root = plants_p1.link_copy(self.pristine, base)
        self.files = {rel: os.stat(self.pristine.joinpath(*rel.split("/"))).st_ino for rel in self._listing(self.pristine)}
        self.digests = self.digest_all()

    @staticmethod
    def _listing(root):
        return sorted(p.relative_to(root).as_posix() for p in Path(root).rglob("*") if p.is_file())

    def digest_all(self):
        return {rel: hashlib.sha256(self.pristine.joinpath(*rel.split("/")).read_bytes()).hexdigest()
                for rel in self._listing(self.pristine)}

    def restore(self):
        """Every file as the pristine twin has it: an added file gone, a changed or removed file linked again."""
        for rel in set(self._listing(self.root)) - set(self.files):
            self.root.joinpath(*rel.split("/")).unlink()
        for rel, inode in self.files.items():
            p = self.root.joinpath(*rel.split("/"))
            if not p.is_file() or os.stat(p).st_ino != inode:
                if p.exists():
                    p.unlink()
                p.parent.mkdir(parents=True, exist_ok=True)
                os.link(self.pristine.joinpath(*rel.split("/")), p)
        for d in sorted((q for q in self.root.rglob("*") if q.is_dir()), reverse=True):
            if not any(d.iterdir()):
                d.rmdir()

    def verify_pristine(self):
        assert self.digest_all() == self.digests, "a test wrote through a link into the pristine twin"


def p1_verdict(crate):
    """The Refused of the checker's steps 1 to 3, P1's steps 4, 5 and 8, and step 9, in that order, or None: P2's steps 6
    and 7 are left out, which enter on P2's terms and answer for them. So what a test of P1's own limits says does not
    depend on whether P2 is merged."""
    crate = Path(crate)
    checker.load()
    try:
        md = reader.read((crate / canonical.DESCRIPTOR).read_bytes())
        checker.files(crate, md)
        checker.counts(crate, md)
        for step in (p1_steps.step4, p1_steps.step5, p1_steps.step8):
            step(crate, md)
        checker.regenerated(crate, md)
    except Refused as r:
        return r
    return None


def read_json(crate, rel):
    return json.loads(Path(crate).joinpath(*rel.split("/")).read_bytes())


def types_of(e):
    return canonical.types(e)


def of_type(md, t):
    return sorted((e for e in md["@graph"] if t in types_of(e)), key=lambda e: e["@id"])


# -- a small Atlas-shaped crate, made here, in the adapter's layout ----------------------------------------------------------------------
ATLAS_JOBS = (("2026-09-25", "aaaaaaaa-1111-4222-8333-444444444444"), ("2026-09-26", "bbbbbbbb-1111-4222-8333-444444444444"))
ATLAS_COMMIT = "1" * 40
ATLAS_CIRCUIT = "circuit-0123456789abcdef.qasm"       # the one circuit all of a day's jobs share
ATLAS_QASM = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[16];\nx q[0];\n'
VECTOR = "vectors/tomography-bitorder-2026-09-25.json"


def jline(obj):
    """Quantum-Film's records: one JSON document, sorted keys, an indent of one, a final line feed."""
    return json.dumps(obj, indent=1, sort_keys=True).encode("utf-8") + b"\n"


def atlas_job_files(day, jid, shots, qasm=ATLAS_QASM):
    """The files of one law job of the Atlas crate, in their places: {path: bytes}."""
    id8 = jid[:8]
    qname = ATLAS_CIRCUIT
    qasm_bytes = qasm.encode("utf-8")
    digest = hashlib.sha256(qasm_bytes).hexdigest()
    salt = hashlib.sha256(b"salt " + jid.encode()).hexdigest()
    line = {"circuit_sha256": digest, "code_commit": ATLAS_COMMIT,
            "commitment": p1_records.commitment_v2("pauli-4x4", digest, "tomography-api-v2", jid, shots,
                                                   "quantum_film.atlas.decode/v1", salt),
            "decode": "quantum_film.atlas.decode/v1", "engine": "tomography-api-v2",
            "format": "quantum-film/commitment/v2", "job_id": jid, "qasm_file": qname, "salt": salt, "shots": shots,
            "stock": "pauli-4x4", "submitted_at": f"{day}T22:52:49Z"}
    result = json.loads(p1_builder.atlas_result(p1_builder.LAYOUTS))
    result["job_id"] = jid
    base = f"{day}/p3"
    return {f"{base}/{qname}": qasm_bytes,
            f"{base}/commitments.jsonl": json.dumps(line, sort_keys=True, separators=(",", ":")).encode() + b"\n",
            f"{base}/atlas-{id8}-submit.json": jline({"body": {"params": {"circuit_qasm": qasm, "shots": shots}},
                                                      "method": "POST", "response": {"job_id": jid, "status": "queued"},
                                                      "status": 202}),
            f"{base}/atlas-{id8}-status.json": jline({"job_id": jid, "status": "completed"}),
            f"{base}/atlas-{id8}-result.json": jline(result),
            f"{base}/score-{id8}.json": jline({"job_id": jid, "records": 3})}


def synthetic_atlas(dest):
    """A small Atlas crate in dest/crate: two law jobs, one a day, the vector and the LICENSE, every record consistent."""
    crate = Path(dest) / "crate"
    files = {plants_p1.LICENSE_NAME: b"MIT, as Quantum-Film's own.\n", VECTOR: p1_builder.atlas_vector()}
    for day, jid in ATLAS_JOBS:
        files.update(atlas_job_files(day, jid, sum(p1_builder.LAYOUTS.values())))
    for rel, data in files.items():
        target = crate.joinpath(*rel.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return crate


RUNS = {f"{IBM_DIR}/run": BUNDLE, f"{IBM_DIR}/sheet-01/run": SHEET1_BUNDLE, f"{IBM_DIR}/sheet-02/run": SHEET2_BUNDLE}


def recommit(crate, edits):
    """A forger who changes a commitment input everywhere it is held, in a copy of the twin: `edits` maps a name of the
    manifest, the line or the record's source (`decode`, `program`, `options_sha256`, ...) to its new value. Every record
    that holds the name is changed, the commitments are recomputed and put where they are held (the manifest, the record,
    the line, IBM's echo inside the raw result, the read's records and their MANIFEST entries), and every digest over what
    changed is recomputed. The metadata is not: patch or rebuild it after. (The crate then holds records that agree with
    one another about a value the generator may refuse.)"""
    f = plants_p1.Forge(crate)
    new_commit = {}                                  # (run directory, job, PUB) -> its commitment
    for run, bundle in RUNS.items():
        mpath = f"{bundle}/manifest.json"
        m = f.json(mpath)
        for k, v in edits.items():
            if k in m:
                m[k] = v
        if "options" in edits:
            m["options_sha256"] = p1_commit.options_digest(edits["options"])
        for job in m["jobs"]:
            for c in job["circuits"]:
                rpath = f"{run}/{job['job']}-pub{c['pub']}-{c['name']}.json"
                if not Path(crate, rpath).exists():
                    continue
                r = f.json(rpath)
                for k, v in edits.items():
                    if k in r["source"]:
                        r["source"][k] = v
                    if k == "stock":
                        r["stock"] = v
                if "options" in edits:
                    r["source"]["options_sha256"] = m["options_sha256"]
                fields = {n: (r if n in ("stock", "role", "basis") else r["source"])[n] for n, _ in p1_commit.FIELDS}
                c["commitment"] = r["source"]["commitment"] = p1_commit.commitment_of(fields)
                f.put_record(rpath, r)
                new_commit[(run, job["job"], c["pub"])] = c["commitment"]
        f.put_json(mpath, m)
        f.reseal_bundle(bundle)
        for job in m["jobs"]:
            lpath = f"{run}/{job['job']}-line.json"
            if not Path(crate, lpath).exists():
                continue
            commits = [new_commit[(run, job["job"], c["pub"])] for c in job["circuits"]]

            def edit_line(o, commits=commits):
                o["commitments"] = commits
                for k, v in edits.items():
                    if k in o:
                        o[k] = v

            def put_echo(doc, commits=commits):
                for i, pub in enumerate(doc["__value__"]["pub_results"]):
                    pub["__value__"]["metadata"]["circuit_metadata"]["qf_commitment"] = commits[i]

            def holds(o, commits=commits):
                for i, p in enumerate(o["holds"]["pubs"]):
                    p["commitment_in_ibm_copy"] = p["commitment_in_line"] = commits[i]
            f.edit_json(lpath, edit_line)
            raw = f"{run}/{job['job']}-raw.json"
            f.edit_json(raw, put_echo)
            f.reseal_raw(lpath, raw)
            _, job_record = f.result_record(lpath)
            f.edit_json(job_record, holds)
            f.reseal_entry(job_record)
    return f


def moth_of(crate, root):
    """A crate of the twin's layout, laid out as the adapter reads its input: a moth-quantum tree, `root`/moth, and the
    records of the read, `root`/records. For the adapter as a process, on records a test has altered."""
    moth, records = Path(root) / "moth", Path(root) / "records"
    for p in sorted(Path(crate).rglob("*")):
        if not p.is_file() or p.name == canonical.DESCRIPTOR:
            continue
        rel = p.relative_to(crate).as_posix()
        if rel == plants_p1.LICENSE_NAME:
            dest = moth / "LICENSE"
        elif rel.startswith("2026-10-14/"):
            dest = records / rel
        else:
            dest = moth / "docs" / "records" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
    return moth, records
