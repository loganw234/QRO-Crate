"""P5's generator, `qro-p5-unit`: step 9's regeneration of a unit crate's metadata from its files (P5's design, item 8;
P5.1). Standard library and qro only.

A unit crate is not a crate of P1's adapter (design item 8, MEASURED): P1's layouts fix `ibm_*` devices and one known-answer
job a bundle, and a unit has three control jobs a device with two known-answer PUBs each, on fake devices as well. So the unit
has its own generator, on P1's public readers (p1_records, p1_forms, p1_decode, p1_commit, p1_calibration, p1_graph) and
P1's guards, imported from qro.p1_guards by the names of its `EXPORTS` and never copied: each rule has one place. The
entities are P1's shapes, so P1's steps 4, 5 and 8 and P2's steps 6 and 7 run on a unit unchanged. No CHECKED term is new.

Like P1's generator it reads the crate's files and never `ro-crate-metadata.json`; no CHECKED value is copied from a record
(each is made by the function its step uses: p1_commit.commitment_of, p1_calibration.claims and link_for, p1_decode.RULES,
p1_forms for shots and times); and the kit's own facts (the recipe digest, the device order, the contributor, the tag, the
commit) come only from `unit/UNIT.json`, a file of the crate. Every guard raises through `p1_guards.hold`, looked up on that
module when it is called, so one monkeypatch of it switches P1's guards and these off together.

The guards, `GuardError` naming the guard (step 9 refuses `metadata-generated`). A guard of P1's keeps P1's letter (G2 to
G9); these are P5's:
  GU1  each bundle file hashes as its manifest says, and no bundle file is one it does not name; the manifest's `unit`
       block, job table (names, PUBs, roles, bases, shots after the divisor, caps), known answer, options and source equal
       the recipe constant; the logical circuits are re-derived from the source text; salts and commitments are distinct;
       one chain throughout; the source circuit is in the crate and is ed767c01bd4b851d
  GU2  `unit/UNIT.json` names the recipe and its digest recomputed from the constant (and the divisor), the devices of its
       kind in the recipe's order, and the bundles' digests as they hash; one kind and one route throughout
  GU3  each line equals its manifest job: P1's G2 (`hold_line`); and no job id is two jobs'
  GU4  each commitment recomputes from the record's fourteen inputs and equals the manifest's, the line's, the record's and
       IBM's echo: P1's G4 (`hold_commitments_and_counts`), after P1's G3 (`hold_device_runs`)
  GU5  the raw result holds a PUB for each commitment with the manifest's shots, and the decode's counts are the record's:
       P1's G5; and a raw result that is no `ibm-sampler-result/v1` is a GU5 raise
  GU6  a control job's PUB 0 is `known-answer` and PUB 1 `known-complement`, both of role known-answer; the Decode of every
       job of a device names the device's first control job's PUB 0, and a device with a result has a control job with one
  GU7  a job with a status file has no raw result, no metrics and no records; a job with a raw result has no status file, and
       has its metrics and a record for each PUB
  GU8  the metrics wrapper is P1's G6 (`hold_metrics`); and a wrapper marked `dry_run` is a simulator unit's, only
  GU9  the read's records, where present, are held as P1's G7 to G9 (`hold_refetch_job`, `hold_refetch_result`,
       `hold_read_manifest`), all or none for a device, and only for a qpu unit
  GU10 every file classifies, and no @id is written twice
"""
import copy
import hashlib
import importlib
import importlib.util
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from qro import canonical, p1_calibration as cal, p1_commit, p1_decode, p1_forms, p1_guards, p1_records as rec, spelling
from qro import p5_unit as U
from qro import vocabulary as V

GENERATOR = "qro-p5-unit"
GuardError = p1_guards.GuardError                  # the same class: every raise of a guard, P1's or P5's, is one
CC_BY = "https://creativecommons.org/licenses/by/4.0/"
IBM_LICENCE = "#licence-ibm-data"
HEADER = {"datePublished": "2026-11-08", "qro:writer": "qro, the P5 generator",
          "qro:writtenAt": "2026-11-08T00:00:00Z", "qro:signature": "none", "qro:trustedTime": "none"}
IBM_FORM = "ibm-sampler-result/v1"
P2_MODULE = "qro.p2_measures"
QUESTION_DIR = "question/"
READ_DIR = "unit/read/"
MAX_PUBS = p1_guards.MAX_PUBS


def hold(ok, guard, where, detail):
    """A guard's raise, through P1's one switch, looked up now."""
    p1_guards.hold(ok, guard, where, detail)


def read_record(guard, where, fn, *args):
    return p1_guards.read_record(guard, where, fn, *args)


class _Entities(dict):
    """The entities of a crate under construction, by @id: an @id is written once (GU10)."""

    def __setitem__(self, i, entity):
        hold(i not in self, "GU10", i, "this @id is written twice: two of the records make an entity of it")
        super().__setitem__(i, entity)

    def update(self, *args, **kwargs):
        for i, entity in dict(*args, **kwargs).items():
            self[i] = entity

    def setdefault(self, i, default=None):
        raise TypeError("an entity is written with [] once, or said with shared()")

    def shared(self, entity):
        i = entity["@id"]
        if i in self:
            hold(self[i] == entity, "GU10", i, "two of the records make this entity differently")
        else:
            self[i] = entity


class Crate:
    """The files of a crate directory, read on demand, with their digests: never the metadata file."""

    def __init__(self, root):
        self.root = Path(root)
        self._info = {}
        found = []
        for dirpath, dirnames, filenames in os.walk(self.root, followlinks=False):
            dirnames.sort()
            for name in filenames:
                rel = Path(dirpath, name).relative_to(self.root).as_posix()
                if rel != canonical.DESCRIPTOR:
                    found.append(rel)
        self.paths = sorted(found)

    def read(self, rel):
        data = self.root.joinpath(*rel.split("/")).read_bytes()
        self._info[rel] = (hashlib.sha256(data).hexdigest(), len(data))
        return data

    def info(self, rel):
        """(the file's SHA-256, its size)."""
        if rel not in self._info:
            self.read(rel)
        return self._info[rel]


# -- the layouts: every file of a unit crate is one of these (GU10) ---------------------------------------------------------
_DEV = r"(?P<device>(?:ibm|fake)_[a-z0-9]+)"
_NAME = r"[a-z][a-z0-9-]*"
_STAMP = r"properties-[0-9]{8}T[0-9]{6}Z\.json"
LAYOUTS = (
    ("license", re.compile(re.escape(U.LICENSE_PATH))),
    ("source", re.compile(re.escape(U.SOURCE_PATH))),
    ("unit", re.compile(re.escape(U.UNIT_FILE))),
    ("bundle", re.compile(rf"unit/{_DEV}/bundle/(?P<file>manifest\.json|README\.md|"
                          rf"(?P<circuit>{_NAME})\.(?P<ext>qasm|qpy|gates\.json|isa\.qasm3))")),
    ("job-file", re.compile(rf"unit/{_DEV}/run/(?P<job>{_NAME}?)-(?P<part>line|metrics|raw|submitting|verdict|status)\.json")),
    ("record", re.compile(rf"unit/{_DEV}/run/(?P<job>{_NAME}?)-pub(?P<k>[0-9]+)-(?P<circuit>{_NAME})\.json")),
    ("refetch-manifest", re.compile(r"unit/read/ibm-refetch/MANIFEST\.json")),
    ("refetch-job", re.compile(rf"unit/read/ibm-refetch/{_DEV}/(?P<job_id>[A-Za-z0-9]+)\.json")),
    ("refetch-snapshot", re.compile(rf"unit/read/ibm-refetch/{_DEV}/{_STAMP}")),
    ("results-manifest", re.compile(r"unit/read/ibm-results-refetch/MANIFEST\.json")),
    ("results-record", re.compile(rf"unit/read/ibm-results-refetch/{_DEV}/(?P<job_id>[A-Za-z0-9]+)\.json")),
)
_LISTED_SNAPSHOT = re.compile(rf"{_DEV}/{_STAMP}")      # how a MANIFEST of the read names a snapshot
FORMATS = ((".gates.json", "application/json"), (".jsonl", "application/x-ndjson"), (".json", "application/json"),
           (".qpy", "application/octet-stream"), (".md", "text/markdown"))
_EXT = {"qasm": "circuit_sha256", "gates.json": "gates_sha256", "qpy": "isa_sha256", "isa.qasm3": "qasm3_sha256"}


def encoding_format(rel):
    for suffix, media in FORMATS:
        if rel.endswith(suffix):
            return media
    return "text/plain"


def classify(rel, question=False):
    """(kind, the layout's groups) of a path, or None where it fits no layout. Files under question/ are P2's, and fit only
    where P2's module is present."""
    for kind, pattern in LAYOUTS:
        m = pattern.fullmatch(rel)
        if m:
            return kind, m.groupdict()
    if question and rel.startswith(QUESTION_DIR) and len(rel) > len(QUESTION_DIR):
        return "question", {}
    return None


def _by_kind(crate, question):
    out = {}
    for rel in crate.paths:
        got = classify(rel, question)
        hold(got is not None, "GU10", rel, "this file fits no layout of the unit generator, so no entity describes it")
        out.setdefault(got[0], []).append((rel, got[1]))
    return out


# -- entities ---------------------------------------------------------------------------------------------------------------
def ref(i):
    return {"@id": i}


def refs(ids):
    return [ref(i) for i in ids]


def file_entity(crate, rel, types="File", licence=None, **terms):
    digest, size = crate.info(rel)
    e = {"@id": rel, "@type": types, "sha256": digest, "contentSize": str(size), "encodingFormat": encoding_format(rel),
         **terms}
    if licence is not None:
        e["license"] = ref(licence)
    return e


def dataset(i, name, description, parts):
    return {"@id": i, "@type": "Dataset", "name": name, "description": description, "hasPart": refs(sorted(parts))}


def software(i, name):
    return {"@id": i, "@type": "SoftwareApplication", "name": name}


def licence(i, name, description):
    return {"@id": i, "@type": "CreativeWork", "name": name, "description": description}


def rule_id(name):
    return "#rule-" + name.replace("/", ".")


# -- P2's seam (the same contract as P1's generator holds, qro/p1_generate.py) ----------------------------------------------
def p2_module():
    """P2's module, if it is present: found as the checker finds a parcel's, and held to both of its functions."""
    if P2_MODULE not in sys.modules and importlib.util.find_spec(P2_MODULE) is None:
        return None
    module = importlib.import_module(P2_MODULE)
    for fn in ("question_files", "contribute"):
        hold(callable(getattr(module, fn, None)), "seam", P2_MODULE, f"the module is present without {fn}")
    return module


def call_p2(module, name, *args):
    """P2's function `name`, called. A raise of it is the records refused by the seam: a `seam` GuardError, whatever P2
    raised, but the host's (an OSError, a MemoryError), which pass as they are."""
    try:
        return getattr(module, name)(*args)
    except (OSError, MemoryError):
        raise
    except Exception as x:
        raise GuardError("seam", P2_MODULE, f"{name} raised {type(x).__name__}: {x}") from None


def _merge_p2(module, crate_dir, entities):
    got = call_p2(module, "contribute", Path(crate_dir), copy.deepcopy(dict(entities)))
    hold(isinstance(got, (tuple, list)) and len(got) == 2, "seam", P2_MODULE,
         "contribute returned something that is not (question terms, new entities)")
    terms, new = got
    hold(isinstance(terms, dict), "seam", P2_MODULE, "contribute returned question terms that are no dict")
    hold(isinstance(new, (dict, list, tuple)), "seam", P2_MODULE, "contribute returned new entities that are no list or dict")
    question = entities["#question"]
    for k in terms:
        hold(k not in question, "seam", P2_MODULE, f"contribute returned {k}, a term of #question that P5 holds")
    question.update(terms)
    for e in list(new.values()) if isinstance(new, dict) else list(new):
        hold(isinstance(e, dict) and isinstance(e.get("@id"), str) and e["@id"] not in entities, "seam", P2_MODULE,
             "contribute returned an entity that is no dict, or holds an @id P5 holds")
        entities[e["@id"]] = e


def _question_files(crate, by, entities):
    files = [r for r, _ in by.get("question", [])]
    for r in files:
        entities[r] = file_entity(crate, r, licence=CC_BY)
    if files:
        entities["#question-files"] = dataset("#question-files", "The question's files",
                                              "The files of the question, written by the measure set that reads it.",
                                              files)
    return ["#question-files"] if files else []


def _question(entities, sources, rules):
    logical = {}
    for rel in sorted(entities):
        if rel.endswith(".qasm") and "/bundle/" in rel:
            logical.setdefault(entities[rel]["sha256"], rel)
    return {"@id": "#question", "@type": ["CreativeWork", "qro:Question"], "name": "The question",
            "description": "The circuits and the decode rule of Quantum-Film's law, and the runs that ask them of a "
                           "device: what each run in this crate answers.",
            "object": refs(sorted({*sources, *logical.values(), *rules}))}


def _finish(crate_dir, root, entities, parts, module, by):
    if module is not None and by.get("question"):
        _merge_p2(module, crate_dir, entities)
    graph = list(entities.values())
    actions = sorted(e["@id"] for e in graph if set(canonical.types(e)) & V.ACTION_TYPES)
    top = {"@id": canonical.ROOT, "@type": "Dataset", "conformsTo": refs([V.PROCESS_RUN_CRATE, V.PROFILE]),
           "license": ref(CC_BY), "hasPart": refs(sorted(parts)), "mentions": refs(actions),
           "qro:generator": GENERATOR, **root, **HEADER}
    return {"@context": V.context(), "@graph": [V.descriptor(), top, *V.profile_entities(), *graph]}


# -- the unit file and the bundles (GU1, GU2) ---------------------------------------------------------------------------------
@dataclass
class Bundle:
    device: str
    path: str                    # the manifest's path
    digest: str                  # the manifest file's SHA-256
    manifest: object             # rec.Manifest
    doc: dict                    # the manifest as parsed


def _unit_file(crate, by):
    files = by.get("unit", [])
    hold(len(files) == 1, "GU2", U.UNIT_FILE, f"a unit crate holds one unit/UNIT.json, not {len(files)}")
    path = files[0][0]
    doc = read_record("GU2", path, rec.parse, crate.read(path), path)
    for term, kind in (("format", str), ("recipe", str), ("recipe_sha256", str), ("shots_divisor", int), ("kind", str),
                       ("route", str), ("devices", list), ("bundles", list), ("kit_commit", str), ("kit_tag", str),
                       ("contributor", str), ("frozen_at", str)):
        read_record("GU2", path, lambda d, w, t, k: rec.need(d, w, t, kind=k), doc, path, term, kind)
    hold(doc["format"] == U.UNIT_FORMAT, "GU2", path, f"the format is {doc['format']!r}, not {U.UNIT_FORMAT}")
    hold(doc["recipe"] == U.RECIPE_NAME, "GU2", path, f"the recipe is {doc['recipe']!r}, not {U.RECIPE_NAME}")
    hold(doc["kind"] in U.DEVICE_SETS, "GU2", path, f"the kind is {doc['kind']!r}, one of {sorted(U.DEVICE_SETS)}")
    hold(doc["route"] == U.ROUTE, "GU2", path, f"the route is {doc['route']!r}, not {U.ROUTE}")
    divisor = doc["shots_divisor"]
    try:
        want = U.recipe_sha256(divisor)
    except ValueError as x:
        raise GuardError("GU2", path, str(x)) from None
    hold(doc["recipe_sha256"] == want, "GU2", path,
         "the recipe digest is not the one the constant gives, for this divisor: the unit is of another recipe")
    hold(divisor == 1 or doc["kind"] == "simulator", "GU2", path, "a shots divisor belongs to the local route only")
    hold(doc["devices"] == list(U.DEVICE_SETS[doc["kind"]]), "GU2", path,
         f"the devices are {doc['devices']}, not {list(U.DEVICE_SETS[doc['kind']])}, in the recipe's order")
    for term in ("kit_commit", "kit_tag", "contributor"):
        hold(spelling.problem("text", doc[term]) is None, "GU2", path, f"{term} is not text")
    hold(doc["kit_commit"] == "unknown" or spelling.problem("commit", doc["kit_commit"]) is None, "GU2", path,
         "kit_commit is neither a commit nor `unknown`")
    return doc


def _manifests(crate, by, unit):
    """{device: Bundle}; GU1 for each, and GU2 for what ties them to UNIT.json."""
    held = {}
    for rel, g in by.get("bundle", []):
        held.setdefault(g["device"], []).append((rel, g))
    hold(list(sorted(held)) == sorted(unit["devices"]), "GU2", U.UNIT_FILE,
         f"the bundles are of {sorted(held)}; the unit names {unit['devices']}")
    source = _source_text(crate, by)
    out = {}
    for device in unit["devices"]:
        files = held[device]
        path = next((r for r, g in files if g["file"] == "manifest.json"), None)
        hold(path is not None, "GU1", device, "a bundle with files and no manifest.json")
        data = crate.read(path)
        m = read_record("GU1", path, rec.manifest, data, path)
        doc = rec.parse(data, path)
        _bundle_holds(crate, device, files, path, m, doc, unit, source)
        out[device] = Bundle(device, path, crate.info(path)[0], m, doc)
    hold(unit["bundles"] == [out[d].digest for d in unit["devices"]], "GU2", U.UNIT_FILE,
         "the bundles' digests are not the manifests' SHA-256, in the recipe's device order")
    salts = [c["salt"] for b in out.values() for j in b.doc["jobs"] for c in j["circuits"]]
    commitments = [c.commitment for b in out.values() for c in b.manifest.circuits()]
    hold(len(set(salts)) == len(salts) and len(set(commitments)) == len(commitments), "GU1", U.UNIT_FILE,
         "two PUBs of the unit share a salt or a commitment: every PUB has its own")
    return out


def _source_text(crate, by):
    sources = by.get("source", [])
    hold(len(sources) == 1, "GU1", U.SOURCE_PATH, "a unit crate carries the source circuit")
    rel = sources[0][0]
    hold(crate.info(rel)[0] == U.SOURCE_SHA256, "GU1", rel, "the source circuit is not ed767c01bd4b851d")
    try:
        return crate.read(rel).decode("ascii")
    except UnicodeDecodeError:
        raise GuardError("GU1", rel, "the source circuit is not ASCII") from None


def _bundle_holds(crate, device, files, path, m, doc, unit, source):
    kind = unit["kind"]
    hold(m.backend == device, "GU1", path, f"the manifest is of {m.backend}, in the place of {device}'s")
    hold((m.kind, m.route, m.stock, m.program, m.decode) == (kind, U.ROUTE, U.STOCK, U.PROGRAM, U.DECODE), "GU2", path,
         "the manifest's kind, route, stock, program or decode is not the unit's")
    hold(p1_commit.options_digest(m.options) == m.options_sha256, "GU1", path,
         "the manifest's options_sha256 is not the digest of its options")
    options = copy.deepcopy(m.options)
    delay = options.get("execution", {}).pop("rep_delay", None) if isinstance(options.get("execution"), dict) else None
    hold(options == U.OPTIONS and (delay is None or (type(delay) in (int, float) and delay > 0)), "GU1", path,
         "the manifest's options are not the recipe's (rep_delay aside, which is the device's own)")
    block = doc.get("unit")
    hold(isinstance(block, dict), "GU1", path, "the manifest has no `unit` block")
    for term, want in (("recipe", unit["recipe"]), ("recipe_sha256", unit["recipe_sha256"]),
                       ("shots_divisor", unit["shots_divisor"]), ("device_order", unit["devices"])):
        hold(block.get(term) == want and type(block.get(term)) is type(want), "GU1", path,
             f"the manifest's unit.{term} is not the unit's")
    hold(doc.get("known_answer") == list(U.KNOWN_ANSWER) and doc.get("pair") == list(U.PAIR), "GU1", path,
         "the manifest's known answer or pair is not the recipe's")
    hold(doc.get("source") == {"path": U.SOURCE_PATH, "sha256": U.SOURCE_SHA256}, "GU1", path,
         "the manifest's source is not the shipped circuit ed767c01bd4b851d at its path")
    planned = U.jobs_of_device(unit["shots_divisor"])
    jobs = doc["jobs"]
    shape = [(j.get("job"), j.get("max_execution_time"),
              [(c.get("pub"), c.get("name"), c.get("role"), c.get("basis"), c.get("shots")) for c in j.get("circuits", [])])
             for j in jobs]
    want = [(name, U.CAPS[k], [(pub, n, r, b, s) for pub, n, r, b, s in pubs]) for name, k, _p, pubs in planned]
    hold(all(type(j.get("max_execution_time")) is int for j in jobs), "GU1", path,
         "a job's max_execution_time is not a whole number (60.0 is a float, one value in two spellings: S4 refuses it too)")
    hold(shape == want, "GU1", path, "the manifest's job table (names, caps, PUBs, roles, bases, shots) is not the recipe's")
    chains = {tuple(c.get("chain", ())) for j in jobs for c in j["circuits"]}
    hold(len(chains) == 1 and len(next(iter(chains))) == U.M, "GU1", path,
         "the circuits are not all on one chain of 16 qubits")
    by_name = {}
    for j in jobs:
        for c in j["circuits"]:
            fixed = tuple(c.get(t) for t in ("circuit_sha256", "isa_sha256", "gates_sha256", "qasm3_sha256"))
            hold(by_name.setdefault(c["name"], fixed) == fixed, "GU1", path,
                 f"circuit {c['name']} has other files in one job than in another")
    names = {c.name: c for c in m.circuits()}
    for rel, g in files:
        if g["file"] == "manifest.json":
            continue
        if g["file"] == "README.md":
            hold(crate.info(rel)[0] == doc.get("readme_sha256"), "GU1", rel, "the README is not the one the manifest digests")
            continue
        c = names.get(g["circuit"])
        hold(c is not None, "GU1", rel, f"the manifest names no circuit {g['circuit']}")
        hold(crate.info(rel)[0] == getattr(c, _EXT[g["ext"]]), "GU1", rel,
             f"the file is not the one the manifest digests as {_EXT[g['ext']]}")
        if g["ext"] == "qasm":
            try:
                derived = U.logical_qasm(g["circuit"], source).encode("ascii")
            except ValueError as x:
                raise GuardError("GU1", rel, str(x)) from None
            hold(crate.read(rel) == derived, "GU1", rel, "the logical circuit is not the one derived from the source text")
    present = {g["circuit"] for _, g in files if g["file"] not in ("manifest.json", "README.md") and g["ext"] == "qasm"}
    hold(present == set(names), "GU1", path, "the bundle lacks a circuit file its manifest names")


# -- the jobs (GU3 to GU8) --------------------------------------------------------------------------------------------------------
@dataclass
class Job:
    device: str
    name: str
    kind: str                    # control or film
    pass_: int
    files: dict                  # part -> path
    manifest: object
    mpath: str
    mdigest: str
    spec: tuple                  # the manifest job's circuits, in PUB order
    line: object
    records: dict                # k -> (path, DeviceRun, Circuit); {} for a job that made no result
    metrics: object              # the metrics wrapper, or None
    first: object
    last: object
    shots: int

    @property
    def id(self):
        return self.line.job_id

    @property
    def done(self):
        return "raw" in self.files


def _jobs(crate, by, bundles, unit):
    runs = {}
    for kind in ("job-file", "record"):
        for rel, g in by.get(kind, []):
            slot = runs.setdefault((g["device"], g["job"]), ({}, {}))
            if kind == "job-file":
                slot[0][g["part"]] = rel
            else:
                slot[1].setdefault(int(g["k"]), []).append((rel, g["circuit"]))
    jobs, seen = [], {}
    for (device, name), (files, found) in sorted(runs.items()):
        where = f"{device} {name}"
        hold(device in bundles, "GU3", where, "a job on a device the unit holds no bundle of")
        b = bundles[device]
        spec = dict(b.manifest.jobs).get(name)
        hold(spec is not None, "GU3", where, f"the manifest {b.path} names no job {name}")
        kind, p = U.parse_job_name(name)
        for part in ("line", "submitting"):
            hold(part in files, "GU7", where, f"a job with no {part} file")
        done = "raw" in files
        hold(done != ("status" in files), "GU7", where,
             "a job has a raw result or a status file, one of the two: a job that did not complete has no result")
        if done:
            for part in ("metrics",):
                hold(part in files, "GU7", where, f"a job with a raw result and no {part} file")
        else:
            hold(not found and not {"metrics", "verdict"} & set(files), "GU7", where,
                 "a job with a status file has no records, metrics or verdict")
        line = read_record("GU3", files["line"], rec.line, crate.read(files["line"]), files["line"])
        hold(line.job_id not in seen, "GU3", files["line"], f"job {line.job_id} is also {seen.get(line.job_id)}")
        seen[line.job_id] = where
        p1_guards.hold_line(crate, name, files, b.manifest, b.digest, spec, line)
        if kind == "control":
            hold([(c.name, c.role) for c in spec] == [("known-answer", "known-answer"), ("known-complement", "known-answer")],
                 "GU6", where, "a control job's PUB 0 is known-answer and its PUB 1 known-complement, both of role known-answer")
        records, metrics, first, last, shots = {}, None, None, None, 0
        if done:
            records = p1_guards.hold_device_runs(crate, where, found, b.manifest, spec, line)
            raw = read_record("GU5", files["raw"], p1_forms.parse_ibm_result, crate.read(files["raw"]))
            p1_guards.hold_commitments_and_counts(files, b.manifest, spec, line, records, raw)
            metrics = read_record("GU8", files["metrics"], rec.metrics, crate.read(files["metrics"]), files["metrics"])
            dry = rec.parse(crate.read(files["metrics"]), files["metrics"]).get("dry_run")
            hold((dry is True) == (unit["kind"] == "simulator") and dry in (None, True), "GU8", files["metrics"],
                 "a metrics wrapper marked dry_run is a simulator unit's, and a simulator unit's is marked")
            p1_guards.hold_metrics(files, line, metrics, raw)
            first, last, shots = raw.first_shot, raw.last_shot, raw.shots
        jobs.append(Job(device, name, kind, p, files, b.manifest, b.path, b.digest, spec, line, records, metrics, first, last,
                        shots))
    return jobs


def _known_answers(jobs, unit):
    """{device: the id of the Pub every Decode of the device names}: the first control job (the lowest pass) that has a
    result, its PUB 0 (GU6)."""
    out = {}
    for device in unit["devices"]:
        mine = [j for j in jobs if j.device == device and j.done]
        if not mine:
            continue
        control = sorted((j for j in mine if j.kind == "control"), key=lambda j: j.pass_)
        hold(bool(control), "GU6", device, "a device with a result has no control job with one: nothing holds its bit order")
        k = control[0]
        hold(0 in k.records and k.records[0][1].role == "known-answer" and k.records[0][2].name == "known-answer", "GU6",
             k.files["line"], "the control job's PUB 0 is not the known answer")
        out[device] = f"#pub-{k.id}-0"
    return out


# -- the read (GU9) -------------------------------------------------------------------------------------------------------------
def _reads(crate, by, jobs, unit):
    """{job id: (RefetchJob, RefetchResult, the two paths)}: the read's records, held, for the devices that have any."""
    job_records = {(g["device"], g["job_id"]): r for r, g in by.get("refetch-job", [])}
    result_records = {(g["device"], g["job_id"]): r for r, g in by.get("results-record", [])}
    anything = [rel for k in ("refetch-manifest", "refetch-job", "refetch-snapshot", "results-manifest", "results-record")
                for rel, _ in by.get(k, [])]
    if not anything:
        return {}
    hold(unit["kind"] == "qpu", "GU9", READ_DIR, "a simulator unit has no read of a provider's copies")
    devices = {d for d, _ in job_records} | {d for d, _ in result_records}
    for d in sorted(devices):
        ids = {j.id for j in jobs if j.device == d and j.done}
        hold({i for dd, i in job_records if dd == d} == ids, "GU9", READ_DIR,
             f"the read's job records of {d} are not those of the jobs the crate carries a result of")
        hold({i for dd, i in result_records if dd == d} == ids, "GU9", READ_DIR,
             f"the read's result records of {d} are not those of the jobs the crate carries a result of")
    carried = {j.device for j in jobs}
    for kind, expect, root in (("refetch-manifest", rec.REFETCH_MANIFEST_FORMAT, READ_DIR + "ibm-refetch/"),
                               ("results-manifest", rec.RESULTS_MANIFEST_FORMAT, READ_DIR + "ibm-results-refetch/")):
        p1_guards.hold_read_manifest(crate, [r for r, _ in by.get(kind, [])], root, expect, carried, _LISTED_SNAPSHOT)
    out = {}
    for j in jobs:
        key = (j.device, j.id)
        if key not in job_records:
            continue
        raw = j.files["raw"]
        # P1's G7 holds the record's one `role` to the set of roles of the job's PUBs, so it cannot hold a job whose PUBs
        # carry more than one (a film job: law and coherence). Handing it only some PUBs would pass the rest unchecked, so
        # such a record is refused until P5.2 and P1 settle how it is held (docs/P5.md).
        hold(len({c.role for c in j.spec}) == 1, "GU9", job_records[key],
             "a read record of a job whose PUBs carry more than one role is not held yet: how P1's one-role record holds "
             "such a job is for P5.2 and P1 to settle")
        out[j.id] = (p1_guards.hold_refetch_job(crate, job_records[key], j),
                     p1_guards.hold_refetch_result(crate, result_records[key], j, raw, raw),
                     job_records[key], result_records[key])
    return out


def _snapshots(crate, by, entities, unit):
    """{device: {path: Snapshot}} of every snapshot the crate carries, each File entity made (G10 of P1's generator, GU9
    here: a snapshot is the read's)."""
    out = {}
    for rel, groups in by.get("refetch-snapshot", []):
        snap = read_record("GU9", rel, p1_forms.parse_snapshot, crate.read(rel))
        device = groups["device"]
        hold(snap.device == device, "GU9", rel, f"the snapshot is of {snap.device!r}, in the place of {device}'s")
        stamped = read_record("GU9", rel, rec.stamp_of, rel.rsplit("/", 1)[1], rel)
        hold(stamped == spelling.time(snap.stamp), "GU9", rel, f"the file is stamped {spelling.time(snap.stamp)}, not as its name says")
        out.setdefault(device, {})[rel] = snap
        entities[rel] = file_entity(crate, rel, ["File", "qro:Snapshot"], IBM_LICENCE, **cal.claims(snap), **{
            "qro:device": ref(f"#device-{device}"), "qro:clock": "provider"})
    return out


# -- the entities -----------------------------------------------------------------------------------------------------------------
def _job_entities(crate, job, unit, known, snapshots, read, entities, data_licence):
    device, jid, files = job.device, job.id, job.files
    manifest = job.manifest
    program = f"#program-{manifest.program}"
    entities.shared(software(program, manifest.program))
    for part in ("line", "submitting", "verdict"):
        if part in files:
            entities[files[part]] = file_entity(crate, files[part], licence=U.LICENSE_PATH)
    for part in ("metrics", "status"):
        if part in files:
            entities[files[part]] = file_entity(crate, files[part], licence=data_licence)
    results = [files[p] for p in ("raw", "line", "metrics", "submitting", "verdict", "status") if p in files]
    if read is not None:
        results += [read[2], read[3]]
    pubs, record_paths = [], []
    if job.done:
        raw = files["raw"]
        entities[raw] = file_entity(crate, raw, ["File", "qro:RawResult"], data_licence,
                                    **{"qro:rawForm": IBM_FORM, "qro:shots": job.shots})
        for k, (path, run, _) in sorted(job.records.items()):
            pid = f"#pub-{jid}-{k}"
            pubs.append(pid)
            record_paths.append(path)
            entities[path] = file_entity(crate, path, licence=U.LICENSE_PATH)
            entities[pid] = {"@id": pid, "@type": "qro:Pub", "qro:role": run.role, "qro:basis": run.basis,
                             "qro:commitment": p1_commit.commitment_of(read_record("G4", path, run.fields, path)),
                             "qro:record": ref(path)}
    spanned = job.first is not None
    qpu = unit["kind"] == "qpu"
    word, named, history_term = ("unexposed" if not qpu else "unknown"), (), {}
    if read is not None:
        read_job = read[0]
        history = f"{READ_DIR}ibm-refetch/{read_job.at_first_shot}"
        carried = snapshots.get(device, {})
        hold(history in carried, "GU9", read[2], f"the snapshot the history returned, {history}, is not carried")
        if spanned:
            try:
                word, named = cal.link_for(job.first, history, carried)
            except cal.LinkError as x:
                raise GuardError("GU9", read[2], f"the history's snapshot is no link: {x}") from None
        running = f"{READ_DIR}ibm-refetch/{read_job.at_running}"
        hold(running in carried, "GU9", read[2], f"the snapshot at running time, {running}, is not carried")
        history_term = {"qro:historyAtRunning": ref(running)}
    e = {"@id": f"#job-{jid}", "@type": ["CreateAction", "qro:Job"], "name": f"{job.name} job on {device}",
         "instrument": ref(program), "result": refs(results), "qro:device": ref(f"#device-{device}"), "qro:jobId": jid,
         "qro:line": ref(files["line"]), "startTime": spelling.time(job.first) if spanned else "unknown",
         "endTime": spelling.time(job.last) if spanned else "unknown", "qro:clock": "provider" if qpu else "local",
         "qro:calibrationLink": word, "qro:kitCommit": unit["kit_commit"], **history_term}
    if pubs:
        e["object"] = refs(pubs)
    if named:
        e["qro:calibration"] = refs(named)
    entities[e["@id"]] = e
    if job.done:
        rule = p1_decode.RULES[manifest.decode]
        entities[f"#decode-{jid}"] = {
            "@id": f"#decode-{jid}", "@type": ["CreateAction", "qro:Decode"], "name": f"decode of {job.name} on {device}",
            "instrument": ref(rule_id(manifest.decode)), "object": refs([files["raw"]]), "result": refs(record_paths),
            "qro:decodeRule": rule.name, "qro:bitOrder": rule.order, "qro:knownAnswer": ref(known[device])}


def _bundle_entities(crate, by, bundles, jobs, entities, data_licence):
    held = {}
    for rel, g in by.get("bundle", []):
        held.setdefault(g["device"], []).append((rel, g))
    for device, b in sorted(bundles.items()):
        for rel, _g in held[device]:
            entities[rel] = file_entity(crate, rel, licence=U.LICENSE_PATH)
        logical = [r for r, g in held[device] if g.get("ext") == "qasm"]
        made = [r for r, g in held[device] if g.get("ext") in ("qpy", "gates.json", "isa.qasm3")]
        transpiler = f"#transpiler-qiskit-{b.manifest.qiskit}"
        entities.shared(software(transpiler, f"qiskit {b.manifest.qiskit}"))
        i = f"#bundle-{device}-unit"
        entities[i] = dataset(i, f"{device}: the bundle",
                              f"The bundle the kit froze before it submitted the unit's jobs on {device}.",
                              [r for r, _g in held[device]])
        c = {"@id": f"#compile-{device}-unit", "@type": ["CreateAction", "qro:Compile"],
             "name": f"compile for {device}, the unit",
             "description": f"The logical circuits transpiled for {device} by qiskit {b.manifest.qiskit} at optimization "
                            f"level {b.manifest.level}, seed {b.manifest.seed}, and frozen as this bundle.",
             "instrument": ref(transpiler), "object": refs([b.path, *logical])}
        if made:
            c["result"] = refs(made)
        entities[c["@id"]] = c
        files = sorted({f for j in jobs if j.device == device
                        for f in [*j.files.values(), *[p for p, _, _ in j.records.values()]]})
        if files:
            i = f"#runs-{device}-unit"
            entities[i] = dataset(i, f"{device}: the runs",
                                  f"The jobs the kit ran from the bundle on {device}: lines, results, metrics and "
                                  "decoded records.", files)


def _read_datasets(crate, by, entities, parts):
    for tag, kind, manifest_kind, licence_id in (("ibm-refetch", "refetch-job", "refetch-manifest", IBM_LICENCE),
                                                 ("ibm-results-refetch", "results-record", "results-manifest", CC_BY)):
        held = []
        for k in (kind, manifest_kind):
            for rel, _ in by.get(k, []):
                entities[rel] = file_entity(crate, rel, licence=licence_id if k == kind else CC_BY)
                held.append(rel)
        if held:
            i = f"#provider-{tag}"
            entities[i] = dataset(i, f"The owner's read of the provider's copies: {tag}",
                                  f"The unit's owner's read of IBM's own copies of the jobs, {tag}: records and their MANIFEST.",
                                  held)
            parts.add(i)


def finalize(out, write, now=None, writer="qro 0.1.0, the P5 kit"):
    """The files P2 asks of a unit crate and its metadata, written through `write(path, bytes)` (the kit's crate command
    hands the writer that lists what it makes, so that a failed build removes only that): the question's files under
    question/, where P2's module is present and knows a law for the source circuit; then the metadata, regenerated from
    the files by `unit` and written by qro.canonical.write, which holds it to the strict reader. Returns the crate's
    identity. GuardError for records that disagree, and a Refused of the writer for text it will not write."""
    out = Path(out)
    module = p2_module()
    if module is not None:
        named = call_p2(module, "question_files", out)
        hold(isinstance(named, dict), "seam", P2_MODULE, "question_files returned something that is no dict")
        hold(len({str(k).casefold() for k in named}) == len(named), "seam", P2_MODULE,
             "question_files names two files whose names differ only by case")
        for rel, data in sorted(named.items()):
            hold(isinstance(rel, str) and isinstance(data, bytes) and not spelling.path_problem(QUESTION_DIR + rel),
                 "seam", P2_MODULE, f"question_files names {rel!r}: a path under question/ in the crate's own spelling, "
                                    "and the file's bytes")
            write(out.joinpath(*(QUESTION_DIR + rel).split("/")), data)
    md = unit(out)
    when = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    md["@graph"][1].update({"datePublished": when.strftime("%Y-%m-%d"), "qro:writer": writer,
                            "qro:writtenAt": spelling.time(when)})
    write(out / canonical.DESCRIPTOR, canonical.write(md))
    return canonical.body_digest(md)


def unit(crate_dir):
    """The metadata of a unit crate, or a GuardError."""
    crate = Crate(crate_dir)
    module = p2_module()
    by = _by_kind(crate, module is not None)
    u = _unit_file(crate, by)
    bundles = _manifests(crate, by, u)
    jobs = _jobs(crate, by, bundles, u)
    known = _known_answers(jobs, u)
    reads = _reads(crate, by, jobs, u)
    qpu = u["kind"] == "qpu"
    data_licence = IBM_LICENCE if qpu else CC_BY
    entities = _Entities()
    snapshots = _snapshots(crate, by, entities, u)
    for job in jobs:
        _job_entities(crate, job, u, known, snapshots, reads.get(job.id), entities, data_licence)
    _bundle_entities(crate, by, bundles, jobs, entities, data_licence)
    parts = {i for i, e in entities.items() if e["@type"] == "Dataset"}
    for rel, _ in by.get("license", []):
        entities[rel] = file_entity(crate, rel)
        parts.add(rel)
    sources = []
    for rel, _ in by.get("source", []):
        entities[rel] = file_entity(crate, rel, licence=U.LICENSE_PATH)
        parts.add(rel)
        sources.append(rel)
    entities[U.UNIT_FILE] = file_entity(crate, U.UNIT_FILE, licence=CC_BY)
    parts.add(U.UNIT_FILE)
    for device in u["devices"]:
        entities[f"#device-{device}"] = {"@id": f"#device-{device}", "@type": "IndividualProduct", "name": device,
                                         "qro:deviceKind": u["kind"]}
    if reads or by.get("refetch-snapshot"):
        by_device = {}
        for rel, g in by.get("refetch-snapshot", []):
            by_device.setdefault(g["device"], []).append(rel)
        for device, held in sorted(by_device.items()):
            i = f"#files-{device}"
            entities[i] = dataset(i, f"{device}: snapshots", f"The calibration snapshots of {device} the read returned.", held)
            parts.add(i)
    _read_datasets(crate, by, entities, parts)
    if qpu:
        entities[IBM_LICENCE] = licence(
            IBM_LICENCE, "IBM's data", "IBM's calibration snapshots, result text and job fields, as IBM's service returned "
                                       "them to the unit's owner. No licence is claimed over them.")
    rules = {rule_id(b.manifest.decode) for b in bundles.values()}
    for r in rules:
        entities[r] = software(r, next(b.manifest.decode for b in bundles.values() if rule_id(b.manifest.decode) == r))
    entities["#question"] = _question(entities, sources, rules)
    parts.update(_question_files(crate, by, entities))
    entities["#unit"] = {
        "@id": "#unit", "@type": ["CreativeWork", "qro:Unit"], "name": "The free-tier unit",
        "description": f"One run of the recipe {u['recipe']} on {', '.join(u['devices'])}: three passes, a control job and "
                       "a film job a device in each, as the kit's bundles froze them.",
        "qro:recipe": u["recipe_sha256"], "qro:contributor": u["contributor"], "qro:kitTag": u["kit_tag"],
        "qro:unitJobs": refs(sorted(e["@id"] for e in entities.values() if "qro:Job" in canonical.types(e)))}
    root = {"name": "QRO-Crate P5: a free-tier unit on " + ("IBM's devices" if qpu else "fake devices (a local rehearsal)"),
            "description": "One free-tier unit, 18 jobs on three devices in three passes, regenerated from its files by "
                           "qro-p5-unit." + ("" if qpu else " The devices are fake backends run by a local simulator: this "
                                             "tests the pipeline, not the devices.")}
    return _finish(crate_dir, root, entities, parts, module, by)
