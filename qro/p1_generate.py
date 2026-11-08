"""P1's generators, `qro-p1-ibm` and `qro-p1-atlas`: step 9's regeneration of a crate's metadata from its records
(P1's design, item 6; P1.2). Standard library and P1's own modules only.

A generator reads the crate's files and nothing else: never `ro-crate-metadata.json`, which the walk skips, so that the
metadata a crate carries cannot move what is regenerated from its records (rule 5). It classifies every file by its
path into one of the adapter's layouts, a closed list (G12), parses Quantum-Film's records and the read of 2026-10-14,
holds them to each other and to the raw bytes (the guards G1 to G11, each a named raise: a build from records that
disagree fails loudly, and on a crate carrying such records step 9 refuses `metadata-generated`), and returns
`{"@context": ..., "@graph": [...]}` in no particular order (qro.canonical.arrange puts it in the one). The header
terms it writes are constants, which step 9 normalises away; the adapter replaces them.

No CHECKED value is copied from a record. Each is made by the function the step that checks it uses, so that the
generator and the step cannot drift apart in one place and a record's own claim cannot reach the output:
  qro:commitment                          p1_commit.commitment_of, from the record's fourteen inputs;
  qro:valuesDigest, qro:stamp,
  qro:newestValue                         p1_calibration.claims, from the snapshot's file;
  qro:calibrationLink, qro:calibration    p1_calibration.link_for, from the raw result's first shot and the snapshots;
  qro:decodeRule, qro:bitOrder            p1_decode.RULES, by the rule the manifest names;
  qro:knownAnswer                         the Pub of role known-answer of the Job's bundle, found by bundle_sha256;
  qro:shots, startTime, endTime           p1_forms, from the raw result's bytes.
Every record's claim that the output also states is a guard instead: a changed claim raises, and is never emitted.
Each guard goes through `p1_guards.hold`, looked up on that module when it is called, so that one monkeypatch of it
switches them all off and a test sees the producing function's value in the output (the sentinel test, T2); with the
guards on, the same sentinel raises (T3). G2's line half, G3 to G9 are the functions of qro/p1_guards.py, which P5's
unit generator calls as well; this module calls them with Quantum-Film's layout (the read's directories, G8's
committed path) and holds the rest (G1, G2's known-answer half, G10 to G12, the seam).

The guards:
  G1  each file a manifest names, where present, hashes as the manifest says; no bundle file is one it does not name;
      the source circuit the manifest names is in the crate; its options digest is the digest of its options;
  G2  a job's line holds its manifest's bundle digest, commitments (in PUB order), stock, kind, route, backend and
      program; its submitting marker names its job and bundle; a bundle's jobs have one known-answer job to hold
      their order;
  G3  a job has at most ten PUBs; each device-run record's digest is the SHA-256 of its body, and its source and role
      agree with the manifest entry and the line; every PUB has its record, and none has two;
  G4  the commitment recomputed from the record's fourteen inputs is the manifest's, the line's, the record's and
      IBM's echo inside the raw bytes;
  G5  the raw result holds one PUB for each commitment of the line, with the manifest's shots, and the counts of
      the decode under the manifest's rule and its order are the record's, exactly (a rule IBM's counts cannot read
      is a G5 raise, as a record that is not in its format is);
  G6  the metrics wrapper names the job and the device, holds the line's submitted time as IBM's created time, and
      the raw result's execution span lies in [running, finished];
  G7  the 2026-10-14 job record's flags hold; its first shot is the span's start and its running time the
      metrics'; the snapshots IBM's history returned are carried, whatever the span, and the first is valid for the
      first shot;
  G8  the 2026-10-14 result record's digests are the raw bytes', and its bytes are equal;
  G9  each MANIFEST of the read is carried wherever its directory holds files, and lists each file of that directory
      as it hashes; every snapshot they list of a device the crate carries jobs of is carried;
  G10 each snapshot is in the closed form, of its device, and stamped as its file is named;
  G11 (Atlas) every commitments line recomputes (v2), names Atlas's decode and a commit, whether or not its job's
      files are in the crate, and a line whose job has none is refused; each job's submit, status, result and score
      files agree with its line, the circuit it names, and its shots;
  G12 every file classifies.
And no @id is written twice (`_Entities`: G2 on the IBM path, G11 on Atlas's), so that two records that make the same
@id cannot overwrite one another.
And the seam with P2 (qro.p2_measures, its contract in docs/P1.md): present without both of its functions, or
contributing what collides with P1's, is a `seam` raise; so is a raise of either function but the host's (OSError,
MemoryError). A crate that holds no files under question/ is one P2 has no law for: `contribute` is not called, and it
carries none of P2's terms.
"""
import copy
import hashlib
import importlib
import importlib.util
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from qro import canonical, p1_calibration as cal, p1_commit, p1_decode, p1_forms, p1_guards, p1_records as rec, spelling
from qro import vocabulary as V

IBM_GENERATOR = "qro-p1-ibm"
ATLAS_GENERATOR = "qro-p1-atlas"
CC_BY = "https://creativecommons.org/licenses/by/4.0/"
LICENSE_QF = "LICENSE-quantum-film"
IBM_LICENCE, MOTH_LICENCE = "#licence-ibm-data", "#licence-moth-data"
HEADER = {"datePublished": "2026-10-26", "qro:writer": "qro, the P1 generator",
          "qro:writtenAt": "2026-10-26T00:00:00Z", "qro:signature": "none", "qro:trustedTime": "none"}
IBM_FORM, ATLAS_FORM, VECTOR_FORM = "ibm-sampler-result/v1", "atlas-tomography-result/v1", "atlas-known-answer-vector/v1"
P2_MODULE = "qro.p2_measures"
QUESTION_DIR = "question/"
READ = "2026-10-14"
RECORDS_DIR = "docs/records/"        # in Quantum-Film's tree; a path of its records, here, has this removed
MAX_PUBS = p1_guards.MAX_PUBS


GuardError = p1_guards.GuardError       # the same class: every raise of a guard, here or P5's, is one


class _Entities(dict):
    """The entities of a crate under construction, by @id, and the one guard of the generators that is not a record's
    claim: an @id is written once. A second write is a raise of the path's guard (G2 on the IBM path, G11 on Atlas's),
    whatever the entity, so that two records that make the same @id cannot overwrite one another and leave a file no
    entity reads. An entity every record that needs it makes the same (a program, a transpiler) is `shared`: it is
    written when it is first needed, and said again as no write, unless it is said differently."""

    def __init__(self, guard):
        super().__init__()
        self.guard = guard

    def __setitem__(self, i, entity):
        p1_guards.hold(i not in self, self.guard, i, "this @id is written twice: two of the records make an entity of it")
        super().__setitem__(i, entity)

    def update(self, *args, **kwargs):
        for i, entity in dict(*args, **kwargs).items():
            self[i] = entity

    def setdefault(self, i, default=None):
        raise TypeError("an entity is written with [] once, or said with shared()")

    def shared(self, entity):
        i = entity["@id"]
        if i in self:
            p1_guards.hold(self[i] == entity, self.guard, i, "two of the records make this entity differently")
        else:
            self[i] = entity


# -- the crate's files ----------------------------------------------------------------------------------------------
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


# -- the layouts: every file of a crate is one of these (G12) ---------------------------------------------------------
_DEV = r"(?P<device>ibm_[a-z0-9]+)"
_SHEET = r"(?:(?P<sheet>sheet-[0-9]{2})/)?"
_NAME = r"[a-z][a-z0-9-]*"
_STAMP = r"properties-[0-9]{8}T[0-9]{6}Z\.json"
IBM_LAYOUTS = (
    ("license", re.compile(LICENSE_QF)),
    ("source", re.compile(r"2026-09-25/p3/circuit-[0-9a-f]{16}\.qasm")),
    ("snapshot", re.compile(rf"2026-10-05/ibm/{_DEV}/{_STAMP}")),
    ("prediction", re.compile(rf"2026-10-05/ibm/{_DEV}/prediction-(?:backend|none)\.json")),
    ("bundle", re.compile(rf"2026-10-05/ibm/{_DEV}/{_SHEET}bundle/(?P<file>manifest\.json|README\.md|"
                          rf"(?P<circuit>{_NAME})\.(?P<ext>qasm|qpy|gates\.json|isa\.qasm3))")),
    ("job-file", re.compile(rf"2026-10-05/ibm/{_DEV}/{_SHEET}run/(?P<job>{_NAME}?)-(?P<part>line|metrics|raw|"
                            rf"submitting|verdict)\.json")),
    ("record", re.compile(rf"2026-10-05/ibm/{_DEV}/{_SHEET}run/(?P<job>{_NAME}?)-pub(?P<k>[0-9]+)-"
                          rf"(?P<circuit>{_NAME})\.json")),
    ("read-readme", re.compile(rf"{READ}/README\.md")),
    ("read-log", re.compile(rf"{READ}/ibm-(?:results-)?refetch\.log")),
    ("refetch-manifest", re.compile(rf"{READ}/ibm-refetch/MANIFEST\.json")),
    ("refetch-job", re.compile(rf"{READ}/ibm-refetch/{_DEV}/(?P<job_id>[A-Za-z0-9]+)\.json")),
    ("refetch-snapshot", re.compile(rf"{READ}/ibm-refetch/{_DEV}/{_STAMP}")),
    ("results-manifest", re.compile(rf"{READ}/ibm-results-refetch/MANIFEST\.json")),
    ("results-record", re.compile(rf"{READ}/ibm-results-refetch/{_DEV}/(?P<job_id>[A-Za-z0-9]+)\.json")),
)
_LISTED_SNAPSHOT = re.compile(rf"{_DEV}/{_STAMP}")      # how a MANIFEST of the read names a snapshot
_DAY = r"(?P<day>[0-9]{4}-[0-9]{2}-[0-9]{2})"
ATLAS_LAYOUTS = (
    ("license", re.compile(LICENSE_QF)),
    ("circuit", re.compile(rf"{_DAY}/p3/circuit-[0-9a-f]{{16}}\.qasm")),
    ("lines", re.compile(rf"{_DAY}/p3/commitments\.jsonl")),
    ("job-file", re.compile(rf"{_DAY}/p3/atlas-(?P<id8>[0-9a-f]{{8}})-(?P<part>submit|status|result)\.json")),
    ("score", re.compile(rf"{_DAY}/p3/score-(?P<id8>[0-9a-f]{{8}})\.json")),
    ("vector", re.compile(r"vectors/tomography-bitorder-2026-09-25\.json")),
)
FORMATS = ((".gates.json", "application/json"), (".jsonl", "application/x-ndjson"), (".json", "application/json"),
           (".qpy", "application/octet-stream"), (".md", "text/markdown"))


def encoding_format(rel):
    for suffix, media in FORMATS:
        if rel.endswith(suffix):
            return media
    return "text/plain"


def classify(rel, layouts, question=False):
    """(kind, the layout's groups) of a path, or None where it fits no layout: a crate carries no file no entity
    describes (G12). Files under question/ are P2's, and fit only where P2's module is present."""
    for kind, pattern in layouts:
        m = pattern.fullmatch(rel)
        if m:
            return kind, m.groupdict()
    if question and rel.startswith(QUESTION_DIR) and len(rel) > len(QUESTION_DIR):
        return "question", {}
    return None


def _by_kind(crate, layouts, question):
    """{kind: [(path, groups)]} of the crate's files; a file that fits no layout is G12."""
    out = {}
    for rel in crate.paths:
        got = classify(rel, layouts, question)
        p1_guards.hold(got is not None, "G12", rel, "this file fits no layout of the adapter, so no entity describes it")
        out.setdefault(got[0], []).append((rel, got[1]))
    return out


# -- entities -----------------------------------------------------------------------------------------------------------------
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


# -- P2's seam ---------------------------------------------------------------------------------------------------------------------
def p2_module():
    """P2's module, if it is present: found as the checker finds a parcel's, and held to both of its functions."""
    if P2_MODULE not in sys.modules and importlib.util.find_spec(P2_MODULE) is None:
        return None
    module = importlib.import_module(P2_MODULE)
    for fn in ("question_files", "contribute"):
        p1_guards.hold(callable(getattr(module, fn, None)), "seam", P2_MODULE, f"the module is present without {fn}")
    return module


def call_p2(module, name, *args):
    """P2's function `name`, called. A raise of it is the records refused by the seam (the lead's ruling, 2026-11-08):
    a `seam` GuardError naming P2's module, the function and P2's own message, whatever P2 raised, but the host's: an
    OSError and a MemoryError pass as they are, to keep the rules of whoever called (the adapter's exit 3, a
    generator's step 9 refusal)."""
    try:
        return getattr(module, name)(*args)
    except (OSError, MemoryError):
        raise
    except Exception as x:
        raise GuardError("seam", P2_MODULE, f"{name} raised {type(x).__name__}: {x}") from None


def _merge_p2(module, crate_dir, entities):
    """P2's question terms and entities, added to P1's. A term or an @id P1 already holds is a raise. Called only for a
    crate that holds files under question/ (`_finish`): a crate P2 has no law for carries none of P2's terms."""
    got = call_p2(module, "contribute", Path(crate_dir), copy.deepcopy(dict(entities)))
    p1_guards.hold(isinstance(got, (tuple, list)) and len(got) == 2, "seam", P2_MODULE,
          "contribute returned something that is not (question terms, new entities)")
    terms, new = got
    p1_guards.hold(isinstance(terms, dict), "seam", P2_MODULE, "contribute returned question terms that are no dict")
    p1_guards.hold(isinstance(new, (dict, list, tuple)), "seam", P2_MODULE, "contribute returned new entities that are no list or dict")
    question = entities["#question"]
    for k in terms:
        p1_guards.hold(k not in question, "seam", P2_MODULE, f"contribute returned {k}, a term of #question that P1 holds")
    question.update(terms)
    for e in list(new.values()) if isinstance(new, dict) else list(new):
        p1_guards.hold(isinstance(e, dict) and isinstance(e.get("@id"), str) and e["@id"] not in entities, "seam", P2_MODULE,
              "contribute returned an entity that is no dict, or holds an @id P1 holds")
        entities[e["@id"]] = e


def _question_files(crate, by, entities):
    """P2's files, under question/: each a File of the root's licence, and a Dataset holding them. The ids."""
    files = [r for r, _ in by.get("question", [])]
    for r in files:
        entities[r] = file_entity(crate, r, licence=CC_BY)
    if files:
        entities["#question-files"] = dataset("#question-files", "The question's files",
                                              "The files of the question, written by the measure set that reads it.",
                                              files)
    return ["#question-files"] if files else []


def _question(entities, sources, rules):
    """The question: its name, description and object (the source circuit, one logical circuit for each distinct
    digest, the first by @id, and the decode rules). P2's terms are added by the seam."""
    logical = {}
    for rel in sorted(entities):
        if rel.endswith(".qasm") and "/bundle/" in rel:
            logical.setdefault(entities[rel]["sha256"], rel)
    return {"@id": "#question", "@type": ["CreativeWork", "qro:Question"], "name": "The question",
            "description": "The circuits and the decode rule of Quantum-Film's law, and the runs that ask them of a "
                           "device: what each run in this crate answers.",
            "object": refs(sorted({*sources, *logical.values(), *rules}))}


def _finish(crate_dir, generator, root, entities, parts, module, by):
    """The metadata: the descriptor, the profile entities, the root with its parts and mentions, and the entities.
    P2's `contribute` is called only where the module is present and the crate holds files under question/ (the lead's
    ruling, 2026-11-08): a crate with none is one P2 has no law for (`question_files` wrote none), and carries none of
    P2's terms."""
    if module is not None and by.get("question"):
        _merge_p2(module, crate_dir, entities)
    graph = list(entities.values())
    actions = sorted(e["@id"] for e in graph if set(canonical.types(e)) & V.ACTION_TYPES)
    top = {"@id": canonical.ROOT, "@type": "Dataset", "conformsTo": refs([V.PROCESS_RUN_CRATE, V.PROFILE]),
           "license": ref(CC_BY), "hasPart": refs(sorted(parts)), "mentions": refs(actions),
           "qro:generator": generator, **root, **HEADER}
    return {"@context": V.context(), "@graph": [V.descriptor(), top, *V.profile_entities(), *graph]}


# -- the IBM crate ---------------------------------------------------------------------------------------------------------------
def _label(sheet):
    return sheet or "morning"


@dataclass
class Job:
    device: str
    label: str
    name: str
    files: dict                  # part -> path: line, metrics, raw, submitting, and verdict where there is one
    manifest: object
    mpath: str
    mdigest: str
    spec: tuple                  # the manifest job's circuits, in PUB order
    line: object
    records: dict                # k -> (path, DeviceRun, Circuit)
    metrics: object
    first: object                # the execution span's start and stop, or None
    last: object
    shots: int

    @property
    def id(self):
        return self.line.job_id


def ibm(crate_dir):
    """The metadata of an IBM crate, or a GuardError."""
    crate = Crate(crate_dir)
    module = p2_module()
    by = _by_kind(crate, IBM_LAYOUTS, module is not None)
    entities = _Entities("G2")
    snapshots = _snapshots(crate, by, entities)
    manifests = _manifests(crate, by)
    jobs = _jobs(crate, by, manifests)
    reads = _reads(crate, by, jobs)
    known = _known_answers(jobs)
    for job in jobs:
        _job_entities(crate, job, snapshots, reads[job.id], known[(job.device, job.label)], entities)
    _bundle_entities(crate, by, manifests, jobs, entities)
    parts = {i for i, e in entities.items() if e["@type"] == "Dataset"}
    sources = []
    for rel, _ in by.get("license", []):
        entities[rel] = file_entity(crate, rel)
        parts.add(rel)
    for rel, _ in by.get("source", []):
        entities[rel] = file_entity(crate, rel, licence=LICENSE_QF)
        parts.add(rel)
        sources.append(rel)
    for kind in ("read-readme", "read-log"):
        for rel, _ in by.get(kind, []):
            entities[rel] = file_entity(crate, rel, licence=CC_BY)
            parts.add(rel)
    _devices(crate, by, manifests, jobs, entities, parts)
    _provider_datasets(crate, by, entities, parts)
    entities[IBM_LICENCE] = licence(
        IBM_LICENCE, "IBM's data", "IBM's calibration snapshots, result text and job fields, as IBM's service returned "
                                   "them to Quantum-Film's owner. No licence is claimed over them.")
    rules = {rule_id(m.decode) for _, m, _ in manifests.values()}
    for r in rules:
        entities[r] = software(r, next(m.decode for _, m, _ in manifests.values() if rule_id(m.decode) == r))
    entities["#question"] = _question(entities, sources, rules)
    parts.update(_question_files(crate, by, entities))
    root = {"name": "QRO-Crate P1: Quantum-Film's IBM runs of 2026-10-05",
            "description": "Quantum-Film's records of its IBM runs of 2026-10-05, with the read of 2026-10-14 of IBM's "
                           "own copies, regenerated from its files by qro-p1-ibm."}
    return _finish(crate_dir, IBM_GENERATOR, root, entities, parts, module, by)


def _devices(crate, by, manifests, jobs, entities, parts):
    """Each device, and the Dataset of its snapshots and predictions."""
    devices = {j.device for j in jobs} | {device for device, _ in manifests}
    kinds = ("snapshot", "prediction", "refetch-snapshot")
    devices |= {g["device"] for k in kinds for _, g in by.get(k, [])}
    for device in sorted(devices):
        entities[f"#device-{device}"] = {"@id": f"#device-{device}", "@type": "IndividualProduct", "name": device,
                                         "qro:deviceKind": "qpu"}
        held = [r for k in kinds for r, g in by.get(k, []) if g["device"] == device]
        for rel, g in by.get("prediction", []):       # the snapshots are entities already (_snapshots)
            if g["device"] == device:
                entities[rel] = file_entity(crate, rel, licence=LICENSE_QF)
        if held:
            i = f"#files-{device}"
            entities[i] = dataset(i, f"{device}: snapshots and predictions",
                                  f"The calibration snapshots and the seeded predictions of {device}.", held)
            parts.add(i)


def _provider_datasets(crate, by, entities, parts):
    """The read of 2026-10-14's two directories: job records (IBM's fields among Logan's comparisons) and result
    records, each directory with its MANIFEST."""
    for tag, kind, manifest_kind, licence_id in (("ibm-refetch", "refetch-job", "refetch-manifest", IBM_LICENCE),
                                                 ("ibm-results-refetch", "results-record", "results-manifest", CC_BY)):
        held = []
        for k in (kind, manifest_kind):
            for rel, _ in by.get(k, []):
                entities[rel] = file_entity(crate, rel, licence=licence_id if k == kind else CC_BY)
                held.append(rel)
        if held:
            i = f"#provider-{tag}"
            entities[i] = dataset(i, f"The read of 2026-10-14: {tag}",
                                  f"Logan's read of IBM's own copies of the jobs, {tag}: records and their MANIFEST.", held)
            parts.add(i)


def _snapshots(crate, by, entities):
    """{device: {path: Snapshot}} of every snapshot the crate carries, each File entity made (G10)."""
    out = {}
    for kind in ("snapshot", "refetch-snapshot"):
        for rel, groups in by.get(kind, []):
            snap = p1_guards.read_record("G10", rel, p1_forms.parse_snapshot, crate.read(rel))
            device = groups["device"]
            p1_guards.hold(snap.device == device, "G10", rel, f"the snapshot is of {snap.device!r}, in the place of {device}'s")
            stamped = p1_guards.read_record("G10", rel, rec.stamp_of, rel.rsplit("/", 1)[1], rel)
            p1_guards.hold(stamped == spelling.time(snap.stamp), "G10", rel,
                  f"the file is stamped {spelling.time(snap.stamp)}, not as its name says")
            out.setdefault(device, {})[rel] = snap
            entities[rel] = file_entity(crate, rel, ["File", "qro:Snapshot"], IBM_LICENCE, **cal.claims(snap), **{
                "qro:device": ref(f"#device-{device}"), "qro:clock": "provider"})
    return out


_EXT = {"qasm": "circuit_sha256", "gates.json": "gates_sha256", "qpy": "isa_sha256", "isa.qasm3": "qasm3_sha256"}


def _manifests(crate, by):
    """{(device, label): (path, Manifest, the manifest file's SHA-256)}; G1: each holds the files of its bundle."""
    held = {}
    for rel, g in by.get("bundle", []):
        held.setdefault((g["device"], _label(g["sheet"])), []).append((rel, g))
    out = {}
    for key, files in sorted(held.items()):
        device, label = key
        path = next((r for r, g in files if g["file"] == "manifest.json"), None)
        p1_guards.hold(path is not None, "G1", f"{device} {label}", "a bundle with files and no manifest.json")
        m = p1_guards.read_record("G1", path, rec.manifest, crate.read(path), path)
        p1_guards.hold(m.backend == device, "G1", path, f"the manifest is of {m.backend}, in the place of {device}'s")
        p1_guards.hold(p1_commit.options_digest(m.options) == m.options_sha256, "G1", path,
              "the manifest's options_sha256 is not the digest of its options")
        names = {c.name: c for c in m.circuits()}
        for rel, g in files:
            if g["file"] == "manifest.json":
                continue
            if g["file"] == "README.md":
                p1_guards.hold(crate.info(rel)[0] == m.readme_sha256, "G1", rel, "the README is not the one the manifest digests")
                continue
            c = names.get(g["circuit"])
            p1_guards.hold(c is not None, "G1", rel, f"the manifest names no circuit {g['circuit']}")
            p1_guards.hold(crate.info(rel)[0] == getattr(c, _EXT[g["ext"]]), "G1", rel,
                  f"the file is not the one the manifest digests as {_EXT[g['ext']]}")
        source = m.source_path[len(RECORDS_DIR):] if m.source_path.startswith(RECORDS_DIR) else m.source_path
        p1_guards.hold(source in crate.paths, "G1", source, "the source circuit the manifest names is not in the crate")
        p1_guards.hold(crate.info(source)[0] == m.source_sha256, "G1", source, "the source circuit is not the one the manifest digests")
        out[key] = (path, m, crate.info(path)[0])
    return out


def _jobs(crate, by, manifests):
    """The jobs of the crate, each with its files and records read and held (G2 to G6)."""
    runs = {}
    for kind in ("job-file", "record"):
        for rel, g in by.get(kind, []):
            slot = runs.setdefault((g["device"], _label(g["sheet"]), g["job"]), ({}, {}))
            if kind == "job-file":
                slot[0][g["part"]] = rel
            else:
                slot[1].setdefault(int(g["k"]), []).append((rel, g["circuit"]))
    jobs, seen = [], {}
    for (device, label, name), (files, found) in sorted(runs.items()):
        where = f"{device} {label} {name}"
        p1_guards.hold((device, label) in manifests, "G2", where, "a job in a bundle the crate carries no manifest of")
        mpath, manifest, mdigest = manifests[(device, label)]
        spec = dict(manifest.jobs).get(name)
        p1_guards.hold(spec is not None, "G2", where, f"the manifest {mpath} names no job {name}")
        for part in ("line", "metrics", "raw", "submitting"):
            p1_guards.hold(part in files, "G2", where, f"a job with no {part} file")
        line = p1_guards.read_record("G2", files["line"], rec.line, crate.read(files["line"]), files["line"])
        p1_guards.hold(line.job_id not in seen, "G2", files["line"], f"job {line.job_id} is also {seen.get(line.job_id)}")
        seen[line.job_id] = where
        p1_guards.hold_line(crate, name, files, manifest, mdigest, spec, line)
        records = p1_guards.hold_device_runs(crate, where, found, manifest, spec, line)
        raw = p1_guards.read_record("G5", files["raw"], p1_forms.parse_ibm_result, crate.read(files["raw"]))
        p1_guards.hold_commitments_and_counts(files, manifest, spec, line, records, raw)
        metrics = p1_guards.read_record("G6", files["metrics"], rec.metrics, crate.read(files["metrics"]), files["metrics"])
        p1_guards.hold_metrics(files, line, metrics, raw)
        jobs.append(Job(device, label, name, files, manifest, mpath, mdigest, spec, line, records, metrics,
                        raw.first_shot, raw.last_shot, raw.shots))
    return jobs


def _known_answers(jobs):
    """{(device, label): the id of the Pub every Decode of the bundle names as its known answer} (G2): the bundle's
    one known-answer job, found by the bundle digest its line holds."""
    out = {}
    for j in jobs:
        known = [k for k in jobs if (k.device, k.label) == (j.device, j.label)
                 and k.line.bundle_sha256 == j.line.bundle_sha256
                 and any(c.role == "known-answer" for c in k.spec)]
        p1_guards.hold(len(known) == 1, "G2", f"{j.device} {j.label}",
              f"the bundle's jobs hold {len(known)} known-answer jobs, and a bundle's order is held by one")
        k = known[0]
        pubs = [i for i, (_, run, _) in sorted(k.records.items()) if run.role == "known-answer"]
        p1_guards.hold(len(pubs) == 1, "G2", k.files["line"], "the known-answer job holds more than one known-answer PUB")
        out[(j.device, j.label)] = f"#pub-{k.id}-{pubs[0]}"
    return out


def _reads(crate, by, jobs):
    """{job id: (RefetchJob, RefetchResult, the two paths)}: the read of 2026-10-14, held (G7 to G9)."""
    job_records = {(g["device"], g["job_id"]): r for r, g in by.get("refetch-job", [])}
    result_records = {(g["device"], g["job_id"]): r for r, g in by.get("results-record", [])}
    ids = {(j.device, j.id) for j in jobs}
    p1_guards.hold(set(job_records) == ids, "G7", READ, "the read's job records are not those of the jobs the crate carries")
    p1_guards.hold(set(result_records) == ids, "G8", READ, "the read's result records are not those of the jobs the crate carries")
    carried = {j.device for j in jobs}
    for kind, expect, root in (("refetch-manifest", rec.REFETCH_MANIFEST_FORMAT, f"{READ}/ibm-refetch/"),
                               ("results-manifest", rec.RESULTS_MANIFEST_FORMAT, f"{READ}/ibm-results-refetch/")):
        p1_guards.hold_read_manifest(crate, [r for r, _ in by.get(kind, [])], root, expect, carried, _LISTED_SNAPSHOT)
    out = {}
    for j in jobs:
        key = (j.device, j.id)
        raw = j.files["raw"]
        out[j.id] = (p1_guards.hold_refetch_job(crate, job_records[key], j),
                     p1_guards.hold_refetch_result(crate, result_records[key], j, raw, RECORDS_DIR + raw),
                     job_records[key], result_records[key])
    return out


def _job_entities(crate, job, snapshots, read, known, entities):
    device, jid, files = job.device, job.id, job.files
    manifest = job.manifest
    read_job, _, jpath, rpath = read
    rule = p1_decode.RULES[manifest.decode]
    program = f"#program-{manifest.program}"
    entities.shared(software(program, manifest.program))
    raw = files["raw"]
    entities[raw] = file_entity(crate, raw, ["File", "qro:RawResult"], IBM_LICENCE,
                                **{"qro:rawForm": IBM_FORM, "qro:shots": job.shots})
    entities[files["metrics"]] = file_entity(crate, files["metrics"], licence=IBM_LICENCE)
    for part in ("line", "submitting", "verdict"):
        if part in files:
            entities[files[part]] = file_entity(crate, files[part], licence=LICENSE_QF)
    results = [raw, *[files[p] for p in ("line", "metrics", "submitting", "verdict") if p in files], jpath, rpath]
    pubs, record_paths = [], []
    for k, (path, run, _) in sorted(job.records.items()):
        pid = f"#pub-{jid}-{k}"
        pubs.append(pid)
        record_paths.append(path)
        entities[path] = file_entity(crate, path, licence=LICENSE_QF)
        entities[pid] = {"@id": pid, "@type": "qro:Pub", "qro:role": run.role, "qro:basis": run.basis,
                         "qro:commitment": p1_commit.commitment_of(p1_guards.read_record("G4", path, run.fields, path)),
                         "qro:record": ref(path)}
    word, named = "unknown", ()
    history = f"{READ}/ibm-refetch/{read_job.at_first_shot}"
    carried = snapshots.get(device, {})
    p1_guards.hold(history in carried, "G7", jpath, f"the snapshot the history returned, {history}, is not carried")
    if job.first is not None:
        try:
            word, named = cal.link_for(job.first, history, carried)
        except cal.LinkError as x:
            raise GuardError("G7", jpath, f"the history's snapshot is no link: {x}") from None
    running = f"{READ}/ibm-refetch/{read_job.at_running}"
    p1_guards.hold(running in snapshots.get(device, {}), "G7", jpath, f"the snapshot at running time, {running}, is not carried")
    spanned = job.first is not None
    e = {"@id": f"#job-{jid}", "@type": ["CreateAction", "qro:Job"], "name": f"{job.name} job on {device}",
         "instrument": ref(program), "object": refs(pubs), "result": refs(results),
         "qro:device": ref(f"#device-{device}"), "qro:jobId": jid, "qro:line": ref(files["line"]),
         "startTime": spelling.time(job.first) if spanned else "unknown",
         "endTime": spelling.time(job.last) if spanned else "unknown", "qro:clock": "provider",
         "qro:calibrationLink": word, "qro:historyAtRunning": ref(running), "qro:kitCommit": "unknown"}
    if named:
        e["qro:calibration"] = refs(named)
    entities[e["@id"]] = e
    entities[f"#decode-{jid}"] = {
        "@id": f"#decode-{jid}", "@type": ["CreateAction", "qro:Decode"], "name": f"decode of {job.name} on {device}",
        "instrument": ref(rule_id(manifest.decode)), "object": refs([raw]), "result": refs(record_paths),
        "qro:decodeRule": rule.name, "qro:bitOrder": rule.order, "qro:knownAnswer": ref(known)}


def _bundle_entities(crate, by, manifests, jobs, entities):
    """Each bundle's Dataset, files and Compile, and its run directory's Dataset."""
    held = {}
    for rel, g in by.get("bundle", []):
        held.setdefault((g["device"], _label(g["sheet"])), []).append((rel, g))
    for key, (mpath, manifest, _) in sorted(manifests.items()):
        device, label = key
        for rel, _g in held[key]:
            entities[rel] = file_entity(crate, rel, licence=LICENSE_QF)
        logical = [r for r, g in held[key] if g.get("ext") == "qasm"]
        made = [r for r, g in held[key] if g.get("ext") in ("qpy", "gates.json", "isa.qasm3")]
        transpiler = f"#transpiler-qiskit-{manifest.qiskit}"
        entities.shared(software(transpiler, f"qiskit {manifest.qiskit}"))
        i = f"#bundle-{device}-{label}"
        entities[i] = dataset(i, f"{device} {label}: the bundle",
                              f"The bundle Quantum-Film froze before it submitted the {label} jobs on {device}.",
                              [r for r, _g in held[key]])
        c = {"@id": f"#compile-{device}-{label}", "@type": ["CreateAction", "qro:Compile"],
             "name": f"compile for {device}, {label}",
             "description": f"The logical circuits transpiled for {device} by qiskit {manifest.qiskit} at optimization "
                            f"level {manifest.level}, seed {manifest.seed}, and frozen as this bundle.",
             "instrument": ref(transpiler), "object": refs([mpath, *logical])}
        if made:
            c["result"] = refs(made)
        entities[c["@id"]] = c
        files = sorted({f for j in jobs if (j.device, j.label) == key
                        for f in [*j.files.values(), *[p for p, _, _ in j.records.values()]]})
        if files:
            i = f"#runs-{device}-{label}"
            entities[i] = dataset(i, f"{device} {label}: the runs",
                                  f"The jobs Quantum-Film ran from the {label} bundle on {device}: lines, results, "
                                  "metrics and decoded records.", files)


# -- the Atlas crate -------------------------------------------------------------------------------------------------------------
def atlas(crate_dir):
    """The metadata of an Atlas crate, or a GuardError."""
    crate = Crate(crate_dir)
    module = p2_module()
    by = _by_kind(crate, ATLAS_LAYOUTS, module is not None)
    entities, parts = _Entities("G11"), set()
    for rel, _ in by.get("license", []):
        entities[rel] = file_entity(crate, rel)
        parts.add(rel)
    lines = {}
    for rel, g in by.get("lines", []):
        for jid, line in p1_guards.read_record("G11", rel, rec.atlas_lines, crate.read(rel), rel).items():
            p1_guards.hold(jid not in lines, "G11", rel, f"job {jid} has a line twice")
            lines[jid] = (g["day"], line, rel)
    engines = sorted({line.engine for _, line, _ in lines.values()})
    p1_guards.hold(len(engines) <= 1, "G11", "commitments.jsonl", f"the lines name more than one engine: {engines}")
    _atlas_lines(lines)
    rule = p1_decode.RULES[p1_decode.ATLAS_RULE]
    device, engine = "#device-moth-atlas-emu", f"#engine-{engines[0] if engines else 'unknown'}"
    entities[device] = {"@id": device, "@type": "IndividualProduct", "name": "moth-atlas-emu",
                        "qro:deviceKind": "simulator"}
    entities[engine] = software(engine, engines[0] if engines else "unknown")
    entities[rule_id(rule.name)] = software(rule_id(rule.name), rule.name)
    entities[MOTH_LICENCE] = licence(
        MOTH_LICENCE, "Moth Quantum's data",
        "Moth Quantum's responses, as its Atlas service returned them to Quantum-Film's owner. No terms were found on "
        "2026-10-14; Logan and Moth are to settle them, and no licence is claimed over them.")
    laws = _atlas_laws(crate, by, lines)
    orphans = sorted(set(lines) - set(laws))
    p1_guards.hold(not orphans, "G11", lines[orphans[0]][2] if orphans else "commitments.jsonl",
          f"the lines name jobs the crate carries no files of: {orphans}")
    vector = by.get("vector", [])
    p1_guards.hold(len(vector) == 1, "G11", "vectors", "an Atlas crate carries one known-answer vector, which holds its order")
    vpath = vector[0][0]
    vparsed = p1_guards.read_record("G11", vpath, p1_forms.parse_atlas_vector, crate.read(vpath))
    ka_pub = f"#pub-{vparsed.job}-0"
    jobs = [(jid, "law", law["result"], ATLAS_FORM, law["parsed"].shots, law["files"], law["commit"])
            for jid, law in sorted(laws.items())]
    jobs.append((vparsed.job, "known-answer", vpath, VECTOR_FORM, vparsed.shots, [], "unknown"))
    for jid, role, raw, form, shots, others, commit in jobs:
        entities[raw] = file_entity(crate, raw, ["File", "qro:RawResult"], MOTH_LICENCE,
                                    **{"qro:rawForm": form, "qro:shots": shots})
        for f in others:
            entities[f] = file_entity(crate, f, licence=LICENSE_QF if "/score-" in f else MOTH_LICENCE)
        entities[f"#pub-{jid}-0"] = {"@id": f"#pub-{jid}-0", "@type": "qro:Pub", "qro:role": role,
                                     "qro:commitment": "none"}
        entities[f"#job-{jid}"] = {
            "@id": f"#job-{jid}", "@type": ["CreateAction", "qro:Job"], "name": f"{role} job on the Atlas engine",
            "instrument": ref(engine), "object": refs([f"#pub-{jid}-0"]), "result": refs([raw, *others]),
            "qro:device": ref(device), "qro:jobId": jid, "startTime": "unknown", "endTime": "unknown",
            "qro:calibrationLink": "unexposed", "qro:kitCommit": commit}
        entities[f"#decode-{jid}"] = {
            "@id": f"#decode-{jid}", "@type": ["CreateAction", "qro:Decode"], "name": f"decode of the {role} job",
            "instrument": ref(rule_id(rule.name)), "object": refs([raw]), "qro:decodeRule": rule.name,
            "qro:bitOrder": rule.order, "qro:knownAnswer": ref(ka_pub)}
    days, sources = {}, []
    for kind in ("circuit", "lines", "job-file", "score"):
        for rel, g in by.get(kind, []):
            if kind in ("circuit", "lines"):          # the job files are entities already, one set for each law job
                entities[rel] = file_entity(crate, rel, licence=LICENSE_QF)
            days.setdefault(g["day"], []).append(rel)
            if kind == "circuit":
                sources.append(rel)
    for day, held in sorted(days.items()):
        entities[f"#atlas-{day}"] = dataset(f"#atlas-{day}", f"Atlas runs of {day}", f"Quantum-Film's Atlas runs of "
                                            f"{day}: circuit, commitment lines, requests, results and scores.", held)
        parts.add(f"#atlas-{day}")
    entities["#atlas-vectors"] = dataset("#atlas-vectors", "Atlas known-answer vector",
                                         "Quantum-Film's frozen known-answer run, which holds the Atlas decode's order.",
                                         [vpath])
    parts.add("#atlas-vectors")
    first = {}
    for rel in sorted(sources):
        first.setdefault(crate.info(rel)[0], rel)
    entities["#question"] = _question({}, sorted(first.values()), {rule_id(rule.name)})
    parts.update(_question_files(crate, by, entities))
    root = {"name": "QRO-Crate P1: Quantum-Film's Atlas runs of 2026-09-25 and 2026-09-26",
            "description": "Quantum-Film's records of its Atlas law runs and its frozen known-answer run, regenerated "
                           "from its files by qro-p1-atlas. The provider held no commitment: each Pub says none."}
    return _finish(crate_dir, ATLAS_GENERATOR, root, entities, parts, module, by)


def _atlas_lines(lines):
    """Every commitments line, whether or not its job's files are in the crate (G11): its commitment recomputes under
    version 2, its decode is Atlas's rule, and its code commit is a commit. (A line whose job has no files in the
    crate is refused after, by atlas(): the real records hold none.)"""
    for jid, (_, line, rel) in sorted(lines.items()):
        got = rec.commitment_v2(line.stock, line.circuit_sha256, line.engine, line.job_id, line.shots, line.decode,
                                line.salt)
        p1_guards.hold(got == line.commitment, "G11", rel, f"job {jid}: the line's commitment does not recompute (v2)")
        p1_guards.hold(line.decode == p1_decode.ATLAS_RULE, "G11", rel, f"job {jid}: the line's decode is {line.decode}")
        p1_guards.hold(not spelling.problem("commit", line.code_commit), "G11", rel,
              f"job {jid}: the line's code_commit is no commit")


def _atlas_laws(crate, by, lines):
    """{job id: {...}} of the law jobs (G11): each job's submit, status, result and score files held to its line."""
    files = {}
    for kind in ("job-file", "score"):
        for rel, g in by.get(kind, []):
            files.setdefault((g["day"], g["id8"]), {})[g.get("part", "score")] = rel
    circuits = {g["day"]: rel for rel, g in by.get("circuit", [])}
    out = {}
    for (day, id8), held in sorted(files.items()):
        where = f"{day} {id8}"
        for part in ("submit", "status", "result", "score"):
            p1_guards.hold(part in held, "G11", where, f"a job with no {part} file")
        jid, qasm, asked = p1_guards.read_record("G11", held["submit"], rec.atlas_submit, crate.read(held["submit"]), held["submit"])
        p1_guards.hold(jid in lines and lines[jid][0] == day and jid[:8] == id8, "G11", held["submit"],
              "the job has no line of its day, or an id that is not its files'")
        line = lines[jid][1]
        qrel = f"{day}/p3/{line.qasm_file}"
        p1_guards.hold(qrel in crate.paths and qrel == circuits.get(day) and crate.info(qrel)[0] == line.circuit_sha256, "G11",
              held["submit"], "the circuit the line names is not the day's, or does not hash as the line says")
        p1_guards.hold(qasm.encode("utf-8") == crate.read(qrel), "G11", held["submit"], "the request's circuit is not the file's")
        parsed = p1_guards.read_record("G11", held["result"], p1_forms.parse_atlas_result, crate.read(held["result"]))
        p1_guards.hold(parsed.job == jid, "G11", held["result"], "the result is of another job")
        p1_guards.hold(line.shots == asked == parsed.shots, "G11", held["submit"],
              "the line, the request and the result disagree on the shots")
        status = p1_guards.read_record("G11", held["status"], rec.atlas_status, crate.read(held["status"]), held["status"])
        p1_guards.hold(status == (jid, "completed"), "G11", held["status"], "the status file is not of this job, completed")
        score = p1_guards.read_record("G11", held["score"], rec.atlas_score, crate.read(held["score"]), held["score"])
        p1_guards.hold(score == jid, "G11", held["score"], "the score file is of another job")
        out[jid] = {"result": held["result"], "files": [held["submit"], held["status"], held["score"]],
                    "commit": line.code_commit, "parsed": parsed}
    return out
