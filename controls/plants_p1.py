"""P1's seven controls (study QRO-0, section 11; P1's design, item 10; P1.2), each planted in a copy of the twin of the
IBM crate, and the toolkit that plants them, which P2's plants use as well (P2's design, item 11).

The twin is a slice of Quantum-Film's IBM records (tests/p1/data/moth), built outside the tree by the adapter from
files copied byte for byte, with the read of 2026-10-14's records of its jobs and the three kingston snapshots it
needs from this repository's records/. It is built once in a process and copied for each plant: a plant takes an
empty directory (controls/registry.py) and returns a crate directory the checker reads. This module builds nothing
when it is imported, and has no command line: the plant command and the runner call the plants.

A plant is a function of a built crate, so that the same fault is planted in a copy of the real IBM crate (the
`p1-crates` stage, on hard-linked copies, link_copy): every write below unlinks a file before it writes it, and so
never writes through a hard link into the crate it was linked from.

The toolkit:
  twin_crate(dest)     a fresh copy of the twin, in dest/crate (`alone=True`: the twin P1 builds with P2's module absent);
  link_copy(src, dest) a copy of any built crate whose files are hard links to src's (or copies, where the host will
                       not link), for the real crate;
  patch(crate, edit, reseal=())
                       the metadata edited by edit(graph) and written as P0's plants write it, not regenerated: for
                       a fault the crate must carry inconsistently; the digests of the files in `reseal` recomputed
                       from their bytes;
  rebuild(crate)       the metadata regenerated from the crate's records by the generator the root names, with its
                       header kept: for a forger who rewrote every digest, so that steps 1 to 9 hold;
  Forge(crate)         the forger's hand: it reads, edits and writes the records in Quantum-Film's own style, and
                       recomputes every digest a record holds over what it changed: change_bundle_file (the
                       manifest's digest of it, the lines' and markers' digest of the manifest), reseal_raw (the
                       result record's two digests), reseal_entry (a MANIFEST's entry), put_record (a device-run
                       record's own digest).
A regeneration that raises means the forger left a record inconsistent, which is a finding of the generator's guards.
"""
import atexit
import base64
import hashlib
import json
import os
import shutil
import tempfile
import zlib
from datetime import timedelta
from pathlib import Path

from qro import canonical, p1_adapter, p1_commit, p1_forms, p1_generate, p1_records, register_p1, spelling
from qro import vocabulary as V

ROOT = Path(__file__).resolve().parents[1]
TWIN = ROOT / "tests" / "p1" / "data" / "moth"
IBM = "2026-10-05/ibm/ibm_kingston"
MORNING_BUNDLE, MORNING_RUN = f"{IBM}/bundle", f"{IBM}/run"
KA_LINE = f"{MORNING_RUN}/known-answer-line.json"
KA_RAW = f"{MORNING_RUN}/known-answer-raw.json"
KA_RECORD = f"{MORNING_RUN}/known-answer-pub0-known-answer.json"
COHERENCE_RAW = f"{MORNING_RUN}/coherence-raw.json"
COHERENCE_RECORD = f"{MORNING_RUN}/coherence-pub0-coherence-xx.json"
SHEET1_LINE, SHEET2_LINE = (f"{IBM}/sheet-0{n}/run/known-answer-line.json" for n in (1, 2))
SHEET2_RAW = f"{IBM}/sheet-02/run/known-answer-raw.json"


def snapshot_path(hhmmss):
    """Kingston's snapshot of 2026-10-05 stamped at this time, in the read of 2026-10-14."""
    return f"2026-10-14/ibm-refetch/ibm_kingston/properties-20261005T{hhmmss}Z.json"


SNAP_0902, SNAP_1128, SNAP_1221 = snapshot_path("090246"), snapshot_path("112827"), snapshot_path("122118")
REFETCH, RESULTS = "2026-10-14/ibm-refetch", "2026-10-14/ibm-results-refetch"
LICENSE_NAME = p1_generate.LICENSE_QF


def sha(data):
    return hashlib.sha256(data).hexdigest()


# -- the twin, built once and copied ------------------------------------------------------------------------------------------
_PRISTINE = []


def pristine_twin():
    """The twin's one built crate in this process, in a directory of the system's temporary files that nothing writes
    to again; removed when the process ends."""
    if not _PRISTINE:
        if getattr(p1_generate.p2_module, "__module__", None) != p1_generate.__name__:
            raise RuntimeError("the twin is built while p1_generate.p2_module is replaced: ask for it before the pin, "
                               "or the copies of it would be built without P2's entities")
        d = Path(tempfile.mkdtemp(prefix="p1-twin-"))
        atexit.register(shutil.rmtree, str(d), True)
        p1_adapter.build("ibm", TWIN, d / "crate", sliced=True)
        _PRISTINE.append(d / "crate")
    return _PRISTINE[0]


_ALONE = []


def pristine_twin_alone():
    """The twin as P1 alone builds it, with qro.p2_measures absent for the build (the generator and the adapter see
    `p1_generate.p2_module` as None for the length of the call): no question/ file, none of P2's entities. For the tests
    that mean P1 alone, which pin the module absent for their generator as well, so that none builds with one tree and
    generates with the other (the lead's ruling, 2026-11-08). Built once in the process, in a directory of its own."""
    if not _ALONE:
        if getattr(p1_generate.p2_module, "__module__", None) != p1_generate.__name__:
            raise RuntimeError("the twin is built while p1_generate.p2_module is replaced: ask for it before the pin")
        d = Path(tempfile.mkdtemp(prefix="p1-twin-alone-"))
        atexit.register(shutil.rmtree, str(d), True)
        real = p1_generate.p2_module
        p1_generate.p2_module = lambda: None
        try:
            p1_adapter.build("ibm", TWIN, d / "crate", sliced=True)
        finally:
            p1_generate.p2_module = real
        _ALONE.append(d / "crate")
    return _ALONE[0]


def twin_crate(dest, alone=False):
    """A fresh copy of the twin, accepted by the checker, in dest/crate: the twin as the tree builds it, P2's module
    present when the tree holds it, or with `alone` the twin as P1 builds it without P2 (pristine_twin_alone)."""
    out = Path(dest) / "crate"
    shutil.copytree(pristine_twin_alone() if alone else pristine_twin(), out)
    return out


def link_copy(src, dest):
    """A copy of the built crate `src` in the empty directory `dest`/crate, each file a hard link to the original's
    where the host links (a copy where it does not). Nothing writes through such a link: see write_file."""
    out = Path(dest) / "crate"
    for dirpath, _, filenames in os.walk(src):
        target = out / Path(dirpath).relative_to(src)
        target.mkdir(parents=True, exist_ok=True)
        for name in filenames:
            try:
                os.link(Path(dirpath, name), target / name)
            except OSError:
                shutil.copyfile(Path(dirpath, name), target / name)
    return out


def write_file(crate, rel, data):
    """A file written whole, its old file unlinked first, so that a hard link to it elsewhere is not written through."""
    p = Path(crate).joinpath(*rel.split("/"))
    if p.exists():
        p.unlink()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def read_file(crate, rel):
    return Path(crate).joinpath(*rel.split("/")).read_bytes()


# -- the metadata -------------------------------------------------------------------------------------------------------------------
def graph_of(crate):
    return json.loads(read_file(crate, canonical.DESCRIPTOR))


def entity(graph, i):
    return next(e for e in graph if e["@id"] == i)


def patch(crate, edit, reseal=()):
    """The crate's metadata edited by edit(graph), and the digests and sizes of the Files in `reseal` recomputed from
    their bytes; written in the canonical bytes, with no step of the checker run. The crate is returned."""
    md = graph_of(crate)
    edit(md["@graph"])
    for rel in reseal:
        data = read_file(crate, rel)
        entity(md["@graph"], rel).update(sha256=sha(data), contentSize=str(len(data)))
    write_file(crate, canonical.DESCRIPTOR, canonical.dumps(md))
    return crate


def rebuild(crate):
    """The metadata regenerated from the crate's records by the generator its root names, the root's header kept, and
    written by the writer that holds it to the strict reader."""
    old = graph_of(crate)
    root = old["@graph"][1]
    md = register_p1.GENERATORS[root["qro:generator"]](crate)
    md["@graph"][1].update({k: root[k] for k in V.HEADER_KEYS if k in root})
    write_file(crate, canonical.DESCRIPTOR, canonical.write(md))
    return crate


# -- the forger's hand ----------------------------------------------------------------------------------------------------------------
STYLES = {"raw": lambda o: json.dumps(o).encode(),
          "snapshot": lambda o: json.dumps(o, sort_keys=True, separators=(",", ":")).encode() + b"\n",
          "record": lambda o: json.dumps(o, indent=1, sort_keys=True).encode() + b"\n"}


def style_of(rel):
    """The json.dumps style Quantum-Film wrote a file of this place in: IBM's result text as runtime wrote it, a
    snapshot compact, and every other record with an indent of one."""
    if rel.endswith("-raw.json"):
        return "raw"
    if rel.startswith("2026-10-05/ibm/") and rel.rsplit("/", 1)[-1].startswith("properties-"):
        return "snapshot"
    return "record"


class Forge:
    """What a producer who held every byte of a crate could do: rewrite any record, and recompute every digest the other
    records hold over what it changed. It never checks anything; rebuild() regenerates the metadata after."""

    def __init__(self, crate):
        self.crate = Path(crate)
        self.changed = []

    def read(self, rel):
        return read_file(self.crate, rel)

    def write(self, rel, data):
        write_file(self.crate, rel, data)
        if rel not in self.changed:
            self.changed.append(rel)
        return sha(data)

    def digest(self, rel):
        return sha(self.read(rel))

    def json(self, rel):
        return json.loads(self.read(rel))

    def put_json(self, rel, obj):
        """The JSON file rewritten in its own style; its new SHA-256."""
        data = STYLES[style_of(rel)](obj)
        return self.write(rel, data)

    def edit_json(self, rel, edit):
        obj = self.json(rel)
        edit(obj)
        return self.put_json(rel, obj)

    # -- the records that hold a digest of another file -----------------------------------------------------------------------
    def put_record(self, rel, obj):
        """A device-run record written with its own digest recomputed."""
        obj["digest"] = p1_records.record_digest(obj)
        return self.put_json(rel, obj)

    def reseal_bundle(self, bundle_dir):
        """The manifest of a bundle changed: every line and submitting marker of the runs from it holds its SHA-256."""
        digest = self.digest(f"{bundle_dir}/manifest.json")
        run = bundle_dir[:-len("bundle")] + "run"
        for p in sorted(Path(self.crate, *run.split("/")).glob("*")):
            if p.name.endswith(("-line.json", "-submitting.json")):
                self.edit_json(f"{run}/{p.name}", lambda o: o.update(bundle_sha256=digest))
        return digest

    def change_bundle_file(self, rel, data, field):
        """A file of a bundle replaced, its digest recomputed in the manifest (`field` of every circuit entry that holds
        the old one), and the manifest's in every line and marker of the runs from the bundle."""
        bundle_dir = rel.rsplit("/", 1)[0]
        old, new = self.digest(rel), self.write(rel, data)
        manifest = f"{bundle_dir}/manifest.json"

        def edit(m):
            for job in m["jobs"]:
                for c in job["circuits"]:
                    if c.get(field) == old:
                        c[field] = new
        self.edit_json(manifest, edit)
        return self.reseal_bundle(bundle_dir)

    def reseal_entry(self, rel):
        """A file of the read changed: its entry in the MANIFEST of its directory holds its new size and SHA-256."""
        top = rel.split("/")[1]
        manifest = f"{rel.split('/')[0]}/{top}/MANIFEST.json"
        name = rel[len(f"{rel.split('/')[0]}/{top}/"):]
        data = self.read(rel)

        def edit(m):
            for entry in m["files"]:
                if entry["path"] == name:
                    entry["bytes"], entry["sha256"] = len(data), sha(data)
        self.edit_json(manifest, edit)

    def job_id(self, line_rel):
        return self.json(line_rel)["job_id"]

    def result_record(self, line_rel):
        """The path of the read's result record, and of its job record, for the job whose line this is."""
        device = line_rel.split("/")[2]
        jid = self.job_id(line_rel)
        return f"{RESULTS}/{device}/{jid}.json", f"{REFETCH}/{device}/{jid}.json"

    def reseal_raw(self, line_rel, raw_rel):
        """A raw result changed: the read's result record holds its size and SHA-256 twice, and the MANIFEST its own."""
        data = self.read(raw_rel)
        result, _ = self.result_record(line_rel)

        def edit(r):
            for key in ("committed", "ibm_copy"):
                r[key]["bytes"], r[key]["sha256"] = len(data), sha(data)
        self.edit_json(result, edit)
        self.reseal_entry(result)


# -- IBM's result text --------------------------------------------------------------------------------------------------------------------
def array_of(doc, pub):
    return doc["__value__"]["pub_results"][pub]["__value__"]["data"]["__value__"]["fields"]["meas"]["__value__"]["array"]


def rows_of(text):
    """The 16-bit outcomes of one PUB's array: base64 of zlib of a .npy v1.0 file of (rows, 2) unsigned bytes."""
    blob = zlib.decompress(base64.b64decode(text))
    head = 10 + int.from_bytes(blob[8:10], "little")
    body = blob[head:]
    return [int.from_bytes(body[i:i + 2], "big") for i in range(0, len(body), 2)], blob[:head]


def array_text(rows, head):
    return base64.b64encode(zlib.compress(head + b"".join(v.to_bytes(2, "big") for v in rows))).decode("ascii")


def outcome_of(v):
    """The qubits that read 1 in a shot, under the rule: qubit i iff bit i is set."""
    return tuple(i for i in range(16) if v >> i & 1)


# -- the seven controls, each a function of a built crate ----------------------------------------------------------------------------------
def job_reattributed(crate):
    """The morning known-answer job's raw result replaced by sheet-02's known-answer raw, which holds as many shots (so
    step 3 holds), its File's digest and size recomputed, nothing else: IBM's echo inside is another job's."""
    write_file(crate, KA_RAW, read_file(crate, SHEET2_RAW))
    return patch(crate, lambda g: None, reseal=[KA_RAW])


def _job(graph, line_rel):
    return next(e for e in graph if "qro:Job" in canonical.types(e) and e["qro:line"] == {"@id": line_rel})


def bits_mirrored(crate):
    """The morning known-answer job's Decode told the mirrored order. Its records, verdict and digests are untouched."""
    def edit(graph):
        job = _job(graph, KA_LINE)
        entity(graph, "#decode-" + job["qro:jobId"])["qro:bitOrder"] = "lsb-first"
    return patch(crate, edit)


def forge_qpy(crate, echo=True):
    """One byte of the morning known-answer circuit's QPY changed, and everything that holds its digest recomputed: the
    manifest's, the record's, the commitment in the manifest, the line, the record and (with `echo`) IBM's echo inside
    the raw result, the record's own digest, the lines' and markers' digest of the manifest, and the read's records of
    the job with their MANIFEST entries. The gate list is left. Returns the new commitment and every path written."""
    f = Forge(crate)
    qpy = f"{MORNING_BUNDLE}/known-answer.qpy"
    data = bytearray(f.read(qpy))
    data[len(data) // 2] ^= 1
    new_isa = sha(bytes(data))
    run = p1_records.device_run(f.read(KA_RECORD), KA_RECORD)
    fields = run.fields(KA_RECORD)
    fields["isa_sha256"] = new_isa
    new_commitment = p1_commit.commitment_of(fields)
    assert new_commitment != run.source["commitment"]
    f.change_bundle_file(qpy, bytes(data), "isa_sha256")

    def manifest(m):
        for job in m["jobs"]:
            for c in job["circuits"]:
                if c["name"] == "known-answer":
                    c["commitment"] = new_commitment
    f.edit_json(f"{MORNING_BUNDLE}/manifest.json", manifest)
    f.reseal_bundle(MORNING_BUNDLE)
    record = f.json(KA_RECORD)
    record["source"]["isa_sha256"], record["source"]["commitment"] = new_isa, new_commitment
    f.put_record(KA_RECORD, record)
    f.edit_json(KA_LINE, lambda o: o.update(commitments=[new_commitment]))
    _, job_record = f.result_record(KA_LINE)
    if echo:
        def put_echo(doc):
            meta = doc["__value__"]["pub_results"][0]["__value__"]["metadata"]["circuit_metadata"]
            meta["qf_commitment"] = new_commitment
        f.edit_json(KA_RAW, put_echo)
        f.reseal_raw(KA_LINE, KA_RAW)

    def holds(o):
        for p in o["holds"]["pubs"]:
            p["commitment_in_ibm_copy"] = p["commitment_in_line"] = new_commitment
    f.edit_json(job_record, holds)
    f.reseal_entry(job_record)
    return new_commitment, f.changed


def qpy_only(crate):
    """The forgery of forge_qpy, the metadata regenerated. The checker, which holds only the crate, accepts it: a stated
    limit. (Without the echo rewritten, the crate is refused `commitment`, which is how the study first worded it.)"""
    forge_qpy(crate)
    return rebuild(crate)


def calibration_late(crate):
    """The morning known-answer job (its first shot at 10:27) linked `history-at-first-shot` to the snapshot stamped
    12:21:18, which is later than the shot."""
    def edit(graph):
        _job(graph, KA_LINE)["qro:calibration"] = [{"@id": SNAP_1221}]
    return patch(crate, edit)


def calibration_gap(crate):
    """Sheet-02's known-answer job (first shot 12:26:17) linked `history-at-first-shot` to 11:28:27, the snapshot the
    history returned, where 12:21:18 was stamped and measured before the shot: the link is `history-in-gap`."""
    def edit(graph):
        job = _job(graph, SHEET2_LINE)
        job["qro:calibrationLink"], job["qro:calibration"] = "history-at-first-shot", [{"@id": SNAP_1128}]
    return patch(crate, edit)


def restamped_snapshot(source_bytes, hours=1, moved=400):
    """A snapshot with the same values and other dates: `last_update_date` and the first `moved` `date` members, in
    document order, moved earlier by `hours`. (The bytes, and the stamp they carry.)"""
    doc = json.loads(source_bytes)
    dates = []

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "date":
                    dates.append((x, k))
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(doc)

    def earlier(text):
        return spelling.time(p1_forms.parse_time(text, "Z") - timedelta(hours=hours))
    for holder, key in dates[:moved]:
        holder[key] = earlier(holder[key])
    doc["last_update_date"] = earlier(doc["last_update_date"])
    return STYLES["snapshot"](doc), doc["last_update_date"]


def calibration_restamped(crate):
    """A copy of the 09:02:46 snapshot with its stamp and 400 of its dates moved earlier, added to Quantum-Film's own
    snapshots of the device: another stamp, equal values. No job's link changes. The metadata is regenerated."""
    data, stamp = restamped_snapshot(read_file(crate, SNAP_0902))
    name = "properties-" + stamp.replace("-", "").replace(":", "") + ".json"
    write_file(crate, f"{IBM}/{name}", data)
    return rebuild(crate)


def moved_shot(raw_bytes, pub=0, row=0, to=None):
    """IBM's result text with one shot of a PUB set to another outcome, and the old and new outcomes: the array
    re-encoded, the text as runtime writes it."""
    doc = json.loads(raw_bytes)
    rows, head = rows_of(array_of(doc, pub)["__value__"])
    old = rows[row]
    new = old ^ 4 if to is None else to
    rows[row] = new
    array_of(doc, pub)["__value__"] = array_text(rows, head)
    return json.dumps(doc).encode(), old, new


def shot_moved_resealed(crate):
    """One shot of the morning coherence job's first PUB set to another outcome, the raw text re-encoded, the record's
    counts and own digest, the result record's two digests and their MANIFEST entry recomputed; the metadata
    regenerated. The checker, which holds only the crate, accepts it: a stated limit."""
    f = Forge(crate)
    data, old, new = moved_shot(f.read(COHERENCE_RAW))
    f.write(COHERENCE_RAW, data)
    record = f.json(COHERENCE_RECORD)
    counts = {tuple(q): n for q, n in record["counts"]}
    counts[outcome_of(old)] -= 1
    counts[outcome_of(new)] = counts.get(outcome_of(new), 0) + 1
    record["counts"] = [[list(q), n] for q, n in sorted(counts.items()) if n]
    f.put_record(COHERENCE_RECORD, record)
    f.reseal_raw(f"{MORNING_RUN}/coherence-line.json", COHERENCE_RAW)
    return rebuild(crate)


FAULTS = {"job-reattributed": job_reattributed, "bits-mirrored": bits_mirrored, "qpy-only": qpy_only,
          "calibration-late": calibration_late, "calibration-gap": calibration_gap,
          "calibration-restamped": calibration_restamped, "shot-moved-resealed": shot_moved_resealed}


def _plant(fault):
    def plant(d):
        return fault(twin_crate(d))
    plant.__name__ = fault.__name__
    return plant


PLANTS = {name: _plant(fault) for name, fault in FAULTS.items()}
