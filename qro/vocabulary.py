"""The vocabulary table: the one place QRO-Crate writes its terms, types, kinds, spellings, words and refusals.

Study QRO-0 (docs/studies/QRO-0.md), rules 1, 2, 4 and 9, sections 9 to 11, and section 13's P0. Every other
part reads this module or is generated from it (HonestFramework, METHOD.md section 4):
  - qro/reader.py refuses a key this table does not name and RO-Crate 1.3's context does not define
    (`term-unknown`), a key RO-Crate defines but this table gives no kind (`field-kind`), and a value outside
    its term's spelling (`spelling`);
  - qro/checker.py holds each CHECKED term to the step that re-derives it, and refuses `step-unbuilt` where
    that step is not built yet;
  - tools/gen_vocabulary.py renders profile/context.jsonld, docs/VOCABULARY.md and docs/REFUSALS.md, and its
    --check refuses drift.

A parcel that needs a term asks the lead, who adds its row here: this file is P0's (ParcelRound, METHOD.md
section 2). Stdlib only.
"""
import re
from dataclasses import dataclass

PROFILE_VERSION = "0.1"
PREFIX = "qro"
# Provisional, by question 6: the generated vocabulary's own page, which resolves once the repository is public
# (question 10). One row to change when w3id.org's is made.
NAMESPACE = "https://github.com/loganw234/QRO-Crate/blob/main/docs/VOCABULARY.md#"
PROFILE = "https://github.com/loganw234/QRO-Crate/blob/main/docs/VOCABULARY.md"
ROCRATE = "https://w3id.org/ro/crate/1.3"
ROCRATE_CONTEXT = "https://w3id.org/ro/crate/1.3/context"
PROCESS_RUN_CRATE = "https://w3id.org/ro/wfrun/process/0.6"
# RO-Crate 1.3's context, CC0 1.0, fetched 2026-10-14 from ROCRATE_CONTEXT (qro/data/README.md), relative to
# the package.
ROCRATE_CONTEXT_FILE = "data/ro-crate-1.3-context.jsonld"
ROCRATE_CONTEXT_SHA256 = "5a3df1a43185501db4d45cdde5a478c57eeb1d673eedfe400488fc4c4b21dd91"

# Rule 1. The table gives each term one; ANCHORED here means "ANCHORED once the crate holds the provider's own
# record of it, REPORTED until then".
KINDS = {
    "CHECKED": "the checker re-derives it from the crate",
    "READ": "the checker's arithmetic takes it as given, so a false value fails its own re-derivation",
    "ANCHORED": "bound by a record the producer does not control, fetched from its holder; REPORTED until then",
    "REPORTED": "stated, not checked",
}

# Rule 2. A term names which of these may stand in place of its value.
ABSENCE = {
    "unknown": "not recorded",
    "none": "does not exist for this device or route",
    "withheld": "the producer has it and chose not to publish it",
    "unexposed": "the provider gives it to nobody",
}

# Section 9's "one spelling" for each kind of value. qro/spelling.py holds each to its rule.
SPELLINGS = {
    "integer": "a JSON number: a non-negative integer, at most 2^63 - 1, in decimal with no leading zero",
    "size": "a string: a byte count in decimal, no sign and no leading zero, at most 2^63 - 1",
    "digest": "a string: a SHA-256, as 64 lowercase hex digits",
    "commit": "a string: a git commit, as 40 lowercase hex digits",
    "rational": "a string N/D in decimal and lowest terms: the sign on N only, D positive, no leading zero, "
                "zero as 0/1, and at most 1,000 digits in either term",
    "binary64": "a string: the value's 16 lowercase hex digits, a space, and its exact decimal in "
                "cft-fp256's spelling ([-]D[.DDD]e[+-]X; 0, -0, inf, -inf); never a NaN",
    "time": "a string: RFC 3339 in UTC, YYYY-MM-DDTHH:MM:SS, a fraction only if nonzero and with no trailing "
            "zero, then Z; a real time, so no leap second's :60",
    "date": "a string: an ISO 8601 date, YYYY-MM-DD",
    "text": "a string: not empty, with no white space at either end (as Python's str.strip reads it), and no control "
            "character but the line feed (C0, DEL or C1), nor a lone surrogate",
    "iri": "a string: an absolute IRI in printable ASCII with no space: a scheme of two characters or more with no "
           "dot, then ':' and at least one character more",
    "ref": 'a JSON object {"@id": "..."} and nothing else',
    "slot": "a slot this profile version leaves empty: only its absence word stands in it",
}

# The fixed word sets a "word:<set>" spelling names.
WORDS = {
    "device-kind": {"qpu": "a quantum processor", "simulator": "anything else: an emulator, a fake backend"},
    "calibration-link": {
        "provider-linked": "the provider names the calibration the job ran under",
        "history-at-first-shot": "the snapshot the provider's history returns at the job's first shot",
        "history-in-gap": "as history-at-first-shot, but a newer carried snapshot was stamped and measured "
                          "before the shot",
        "read-before-run": "read at a freeze or before submission",
        "read-after-run": "read after the shots; never presented as the state at execution",
    },
    "clock": {"provider": "the provider's clock", "local": "the producer's machine's clock"},
    # Section 9.2: the custody log and the audit record.
    "custody-event": {"received": "a crate received, from where and when",
                      "withdrawn": "a crate withdrawn: its bytes removed, its received line kept"},
    "audit-stage": {"crate-only": "the checker's nine steps, on the crate alone",
                    "compile": "the compile, re-derived through the named qiskit",
                    "qpy": "each QPY's gate list, re-derived and held to the held one",
                    "exact-hold": "the exact hold, re-derived as a binary64 statevector",
                    "anchors": "the anchors, re-fetched from the provider with the owner's key"},
    "independence": {"producer-build": "the producer's own checker build",
                     "same-source": "the same checker source, built independently at a tagged commit",
                     "independent-implementation": "an independent implementation, written from this profile"},
}


@dataclass(frozen=True)
class Term:
    key: str              # as written in a crate: "sha256", "qro:shots"
    kind: str             # one of KINDS
    spelling: str         # one of SPELLINGS, or "word:<set>" naming one of WORDS
    many: bool            # True: always a list, sorted, of distinct values; False: never a list
    absent: tuple         # the absence words that may stand in place of a value
    part: str             # "body", or "header": what two writers of one crate make differently (rule 4)
    step: int | None      # a CHECKED term's checker step (section 10); None otherwise
    owner: str            # the parcel whose step checks it, or that first writes it
    meaning: str
    # The entities it may stand on (P0's verifier, P0-7): "*", the root "./", the descriptor, "local-file" (a File
    # the crate holds), or a type. A CHECKED term's step checks it on every entity its domain admits, and the
    # reader refuses it anywhere else, so no CHECKED field sits where no step reads it.
    domain: tuple = ("*",)


@dataclass(frozen=True)
class Type:
    key: str
    owner: str
    meaning: str
    action: bool = False  # an action: the root mentions every entity of an action type


@dataclass(frozen=True)
class Refusal:
    name: str
    where: str            # "step 1".."step 9", "seam", "comparison", "kit", "custody"
    effect: str           # "refused", or "kept": the record is kept and labelled
    owner: str
    meaning: str


B, H = "body", "header"
DESC, ROOT, LOCAL = "ro-crate-metadata.json", "./", "local-file"
TERMS = (
    # The descriptor and the root (section 9, step 1).
    Term("about", "CHECKED", "ref", False, (), B, 1, "P0", "the metadata descriptor's subject: the root, ./",
         (DESC,)),
    Term("conformsTo", "CHECKED", "ref", True, (), B, 1, "P0",
         "the descriptor: RO-Crate 1.3; the root: Process Run Crate 0.6 and this profile", (DESC, ROOT)),
    Term("mentions", "CHECKED", "ref", True, (), B, 1, "P0", "the root's list of every action in the crate",
         (ROOT,)),
    Term("license", "REPORTED", "ref", False, (), B, None, "P0", "the crate's licence; CC BY 4.0 (question 18)"),
    Term("name", "REPORTED", "text", False, (), B, None, "P0", "a name for a person to read"),
    Term("description", "REPORTED", "text", False, (), B, None, "P0", "a description for a person to read"),
    # Files (step 2).
    Term("hasPart", "CHECKED", "ref", True, (), B, 2, "P0",
         "a Dataset's list of the files it holds; every file is reached from the root, and every listed file is "
         "there", ("Dataset",)),
    Term("sha256", "CHECKED", "digest", False, (), B, 2, "P0", "a file's SHA-256", (LOCAL,)),
    Term("contentSize", "CHECKED", "size", False, (), B, 2, "P0", "a file's length in bytes", (LOCAL,)),
    Term("encodingFormat", "REPORTED", "text", False, (), B, None, "P0", "a file's media type", ("File",)),
    # Raw results (step 3, rules 6 and 7).
    Term("qro:rawForm", "CHECKED", "text", False, (), B, 3, "P0",
         "the form a raw result's bytes take; the checker must know it to count them", ("qro:RawResult",)),
    Term("qro:shots", "CHECKED", "integer", False, (), B, 3, "P0",
         "the shots a raw result holds, counted from its bytes, never stated beside them (rule 7)",
         ("qro:RawResult",)),
    # The metadata, generated from the records (rule 5, step 9).
    Term("qro:generator", "CHECKED", "text", False, (), B, 9, "P0",
         "the generator that regenerates this metadata from the records", (ROOT,)),
    # The header (rule 4): what two writers of one crate make differently, on the root.
    Term("datePublished", "REPORTED", "date", False, (), H, None, "P0", "RO-Crate's publication date", (ROOT,)),
    Term("qro:writer", "REPORTED", "text", False, (), H, None, "P0", "the writer, and its version", (ROOT,)),
    Term("qro:writtenAt", "REPORTED", "time", False, (), H, None, "P0", "when the writer wrote the crate",
         (ROOT,)),
    Term("qro:implementation", "REPORTED", "text", True, (), H, None, "P0",
         "an implementation and its version, for a definition whose version is in the body"),
    Term("qro:signature", "REPORTED", "slot", False, ("none",), H, None, "P0",
         "the signature slot, `none` in v0 (section 9.2)", (ROOT,)),
    Term("qro:trustedTime", "REPORTED", "slot", False, ("none",), H, None, "P0",
         "the trusted-time slot, `none` in v0 (section 9.2)", (ROOT,)),
    # Some of the terms the study names, for the parcels that write them (section 6 and section 9's table). Their
    # domains are the parcels' to narrow; the rest, `qro:role` among them, come with their parcel's design.
    Term("qro:deviceKind", "REPORTED", "word:device-kind", False, (), B, None, "P1",
         "whether a device is a quantum processor"),
    Term("qro:device", "REPORTED", "ref", False, (), B, None, "P1", "the device a job ran on"),
    Term("qro:commitment", "CHECKED", "digest", False, (), B, 4, "P1",
         "a job's commitment, recomputed and held to the one the provider echoed"),
    Term("qro:calibrationLink", "CHECKED", "word:calibration-link", False, ("unknown",), B, 8, "P1",
         "how a job's calibration snapshot is tied to its shots (section 6)"),
    Term("qro:valuesDigest", "CHECKED", "digest", False, (), B, 8, "P1",
         "the SHA-256 of a calibration's values, every date excluded"),
    Term("qro:historyAtRunning", "REPORTED", "ref", False, ("unknown",), B, None, "P1",
         "the snapshot the history returns at the job's running time, carried beside the link"),
    Term("qro:clock", "REPORTED", "word:clock", False, (), B, None, "P1", "the clock an entity's times are on"),
    Term("startTime", "ANCHORED", "time", False, ("unknown",), B, None, "P1", "when a job's shots began"),
    Term("endTime", "ANCHORED", "time", False, ("unknown",), B, None, "P1", "when a job's shots ended"),
)

TYPES = (
    Type("Dataset", "P0", "the root, and a bundle"),
    Type("File", "P0", "a file the crate holds"),
    Type("CreativeWork", "P0", "the metadata descriptor, the question, a pre-registration"),
    Type("CreateAction", "P1", "a compile, a job, a prediction, a decode, the measures", action=True),
    Type("IndividualProduct", "P1", "a device"),
    Type("SoftwareApplication", "P1", "a program, a transpiler, a simulator"),
    Type("qro:Question", "P1", "the question: circuits, law, twins, decode rule and measure set"),
    Type("qro:RawResult", "P0", "a raw result: the provider's bytes, fixed before anything decodes them"),
)

REFUSALS = (
    Refusal("spelling", "step 1", "refused", "P0",
            "the bytes are not canonical JSON, or a value is not in its term's one spelling"),
    Refusal("context", "step 1", "refused", "P0", "the @context is not this profile version's"),
    Refusal("graph-form", "step 1; step 3", "refused", "P0",
            "the graph's shape: the top level; a @graph that is not a list of two entities or more; an entity "
            "without @id or @type; a repeated @id; two files, the descriptor among them, whose names differ only "
            "by case; the order; the descriptor; the root, its type and every term it must carry; the root's "
            "conformsTo, which is Process Run Crate 0.6 and this profile; the root's mentions; a reference that "
            "names no entity; a term on an entity its domain does not admit; and, at step 3, a raw result that is "
            "not a File the crate holds"),
    Refusal("term-unknown", "step 1", "refused", "P0",
            "a key that neither this vocabulary nor RO-Crate 1.3's context names, or a type this vocabulary does "
            "not list"),
    Refusal("field-kind", "step 1", "refused", "P0",
            "a key RO-Crate's context defines but this vocabulary gives no kind (rule 9)"),
    Refusal("file-missing", "step 2", "refused", "P0", "a listed file is not in the crate"),
    Refusal("file-unlisted", "step 2", "refused", "P0", "a file in the crate is not listed in hasPart"),
    Refusal("file-digest", "step 2", "refused", "P0", "a file's bytes do not match its sha256 or contentSize"),
    Refusal("raw-digest", "step 2", "refused", "P0", "a raw result's bytes do not match its sha256 or contentSize"),
    Refusal("file-link", "step 2", "refused", "P0",
            "a link in the crate, symbolic or a junction, or any entry neither a regular file nor a directory: a "
            "crate holds files, never a way out of itself"),
    Refusal("raw-form", "step 3", "refused", "P0", "a raw result's bytes are not in its raw form"),
    Refusal("count-unpaid", "step 3", "refused", "P0", "a stated count is not the count the raw bytes hold"),
    Refusal("commitment", "step 4", "refused", "P1",
            "a commitment does not recompute, or is not the one the provider echoed"),
    Refusal("known-answer", "step 5; kit intake", "refused", "P1",
            "the decode does not read the known answer: bit order is not held"),
    Refusal("measure-class", "step 6", "refused", "P2", "a measure's value or declared class does not re-derive"),
    Refusal("compile-uncontrolled", "step 7", "refused", "P2", "a gate list does not pass the exact hold"),
    Refusal("calibration-link", "step 8", "refused", "P1", "a calibration link or values-digest does not hold"),
    Refusal("metadata-generated", "step 9", "refused", "P0",
            "the metadata is not what its generator makes from the records, the header normalised"),
    Refusal("step-unbuilt", "seam", "refused", "P0",
            "a CHECKED field, a raw form or a generator whose checker step is not built yet"),
    Refusal("comparison-trivial", "comparison", "refused", "P3", "the two runs share a job of a measured role"),
    Refusal("question-differs", "comparison", "refused", "P3", "the two runs' questions differ by digest"),
    Refusal("role-missing", "comparison", "refused", "P3", "a measure needs a role one run lacks"),
    Refusal("kind-not-qpu", "comparison", "refused", "P3",
            "a comparison declared real, with a run holding a simulator unit"),
    Refusal("selector-late", "comparison", "kept", "P3",
            "a selector or tolerance declared after the data were read: labelled exploratory"),
    Refusal("kit-dirty", "kit", "refused", "P5", "the kit started from a dirty tree or an untagged commit"),
    Refusal("unit-incomplete", "kit", "kept", "P5", "a unit missing a job: left out of every pair with that device"),
    Refusal("not-interleaved", "kit", "kept", "P5",
            "a unit whose devices ran in blocks: the difference is the device's-and-its-time's"),
    Refusal("custody-chain", "custody", "refused", "P0",
            "a custody-log line's predecessor hash does not match the line before it"),
    Refusal("custody-head", "custody", "refused", "P0",
            "an audit record's log head matches no line of its auditor's custody log"),
)

@dataclass(frozen=True)
class Field:
    key: str
    kind: str
    spelling: str
    many: bool
    absent: tuple
    meaning: str


# Section 9.2. A custody log's line, by event; and an audit record. Neither is a crate, so neither is JSON-LD.
_AT = Field("at", "REPORTED", "time", False, (), "when, on the custodian's clock")
_CRATE = Field("crate", "REPORTED", "digest", False, (), "the crate's identity: its metadata-body digest")
_EVENT = Field("event", "REPORTED", "word:custody-event", False, (), "what happened")
_PREV = Field("prev", "CHECKED", "digest", False, (),
              "the SHA-256 of the line before, its LF included; the SHA-256 of the empty string for the first")
CUSTODY_LINE = {
    "received": (_AT, _CRATE, _EVENT,
                 Field("from", "REPORTED", "text", False, ("withheld",), "where it came from: a public handle"),
                 _PREV),
    "withdrawn": (_AT, _CRATE, _EVENT, _PREV,
                  Field("reason", "REPORTED", "text", False, (), "why, with no identifier rule 3 forbids")),
}
AUDIT_RECORD = (
    Field("auditor", "REPORTED", "text", False, ("withheld",), "the auditor's public handle (rule 3)"),
    Field("checker", "REPORTED", "text", False, (), "the checker's name and version"),
    Field("checkerCommit", "REPORTED", "commit", False, ("unknown",), "the commit the checker was built from"),
    Field("crate", "REPORTED", "digest", False, (), "the audited crate's metadata-body digest"),
    Field("date", "REPORTED", "date", False, (), "the date, on the auditor's clock"),
    Field("independence", "REPORTED", "word:independence", False, (), "the audit's degree of independence"),
    Field("logHead", "CHECKED", "digest", False, ("none",),
          "the auditor's custody-log head when it wrote the record; `none` with no log, which pins nothing"),
    Field("signature", "REPORTED", "slot", False, ("none",), "the signature slot, `none` in v0"),
    Field("stages", "REPORTED", "word:audit-stage", True, (), "which stages ran: crate-only, and any of the four"),
    Field("trustedTime", "REPORTED", "slot", False, ("none",), "the trusted-time slot, `none` in v0"),
    Field("verdict", "REPORTED", "word:verdict", False, (), "accepted, or the refusal's name"),
)

WORDS["verdict"] = {"accepted": "every stage that ran accepted the crate",
                    **{r.name: r.meaning for r in REFUSALS if r.effect == "refused"}}

TERM = {t.key: t for t in TERMS}
TYPE = {t.key: t for t in TYPES}
REFUSAL = {r.name: r for r in REFUSALS}
HEADER_KEYS = frozenset(t.key for t in TERMS if t.part == H)
ACTION_TYPES = frozenset(t.key for t in TYPES if t.action)
# What every root carries (section 9's table, sections 9.2 and 10, rule 5): the strict reader refuses a root
# without any of them (P0's verifier's notes).
ROOT_REQUIRED = ("conformsTo", "datePublished", "description", "hasPart", "license", "name", "qro:generator",
                 "qro:signature", "qro:trustedTime", "qro:writer", "qro:writtenAt")
OWNERS = ("P0", "P1", "P2", "P3", "P4", "P5")


def context():
    """The crate's @context: RO-Crate 1.3's, then this profile's one prefix."""
    return [ROCRATE_CONTEXT, {PREFIX: NAMESPACE}]


def sanity():
    """The contradictions the table can hold, refused before anything renders or reads it."""
    out = []
    for name, rows in (("term", [t.key for t in TERMS]), ("type", [t.key for t in TYPES]),
                       ("refusal", [r.name for r in REFUSALS])):
        seen = set()
        for k in rows:
            if k in seen:
                out.append(f"two {name} rows share {k}")
            seen.add(k)
    for t in TERMS:
        if t.kind not in KINDS:
            out.append(f"{t.key}: kind {t.kind} is not one of {sorted(KINDS)}")
        base = t.spelling.split(":", 1)
        if base[0] == "word":
            if len(base) != 2 or base[1] not in WORDS:
                out.append(f"{t.key}: spelling {t.spelling} names no word set")
        elif t.spelling not in SPELLINGS:
            out.append(f"{t.key}: spelling {t.spelling} is not one of SPELLINGS")
        if t.spelling == "slot" and not t.absent:
            out.append(f"{t.key}: a slot needs an absence word to stand in it")
        for a in t.absent:
            if a not in ABSENCE:
                out.append(f"{t.key}: {a} is not an absence word")
        if t.part not in (B, H):
            out.append(f"{t.key}: part {t.part}")
        if (t.kind == "CHECKED") != (t.step is not None):
            out.append(f"{t.key}: a CHECKED term names its step, and only a CHECKED term does")
        if t.step is not None and not 1 <= t.step <= 9:
            out.append(f"{t.key}: step {t.step} is not one of section 10's nine")
        if t.part == H and t.kind == "CHECKED":
            out.append(f"{t.key}: a header term is never CHECKED; the checker normalises the header")
        if not t.meaning:
            out.append(f"{t.key}: no meaning written down")
        if t.key.startswith(PREFIX + ":") and not t.key[len(PREFIX) + 1:].isidentifier():
            out.append(f"{t.key}: a {PREFIX} term's name must be one identifier")
        for s in t.domain:
            if s not in ("*", ROOT, DESC, LOCAL) and s not in {y.key for y in TYPES}:
                out.append(f"{t.key}: domain {s} is not *, the root, the descriptor, a local file or a type")
        if t.owner not in OWNERS:
            out.append(f"{t.key}: owner {t.owner}")
    for y in TYPES:
        if y.owner not in OWNERS:
            out.append(f"type {y.key}: owner {y.owner}")
        name = y.key[len(PREFIX) + 1:] if y.key.startswith(PREFIX + ":") else None
        if name is not None and not (name.isidentifier() and name[0].isupper()):
            out.append(f"type {y.key}: a {PREFIX} type's name is one identifier, capitalised")
    for k in ROOT_REQUIRED:                          # the root is always a Dataset, so "Dataset" admits it
        if k not in {t.key for t in TERMS} or not {"*", ROOT, "Dataset"} & set(
                next(t for t in TERMS if t.key == k).domain):
            out.append(f"root-required {k}: not a term the root may carry")
    for r in REFUSALS:
        if r.effect not in ("refused", "kept"):
            out.append(f"{r.name}: effect {r.effect}")
        if not r.meaning:
            out.append(f"{r.name}: no meaning written down")
        if not re.fullmatch(r"[a-z]+(-[a-z]+)*", r.name):
            out.append(f"refusal {r.name}: a name is lowercase words joined by hyphens")
        if not re.fullmatch(r"step [1-9](; step [1-9])*(; kit intake)?|seam|comparison|kit|custody", r.where):
            out.append(f"refusal {r.name}: where {r.where}")
        if r.owner not in OWNERS:
            out.append(f"refusal {r.name}: owner {r.owner}")
    if set(WORDS["custody-event"]) != set(CUSTODY_LINE):
        out.append("the custody-event words are not the custody line's events")
    for e, fields in CUSTODY_LINE.items():
        keys = {f.key: f for f in fields}
        if not {"at", "crate", "event", "prev"} <= set(keys) or keys["prev"].kind != "CHECKED":
            out.append(f"custody line {e}: at, crate, event and a CHECKED prev on every line")
    for name, fields in [("custody line " + e, fs) for e, fs in CUSTODY_LINE.items()] + [("audit record",
                                                                                         AUDIT_RECORD)]:
        keys = [f.key for f in fields]
        if keys != sorted(set(keys)):
            out.append(f"{name}: its fields are listed in key order, each once")
        for f in fields:
            base = f.spelling.split(":", 1)
            if (base[0] == "word" and base[1] not in WORDS) or (base[0] != "word" and f.spelling not in SPELLINGS):
                out.append(f"{name} {f.key}: spelling {f.spelling}")
            if f.kind not in KINDS or any(a not in ABSENCE for a in f.absent):
                out.append(f"{name} {f.key}: kind or absence word")
    words = [w for ws in WORDS.values() for w in ws]
    for w in ABSENCE:
        if w in words:
            out.append(f"{w} is an absence word and also a word of a set")
    return out
