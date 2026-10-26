"""Checker steps 4, 5 and 8: the commitments, the decode and the calibration links (P1's design, items 3 to 5;
P1.1). Standard library only. qro/register_p1.py hands these to the checker; it imports this module only when a
crate holds an entity these steps visit.

Every step visits every entity its CHECKED terms stand on, by type, in @id order, and refuses at the first failure,
with the entity and the term in the location and the reason in the detail. The names are the vocabulary's:
  step 4  `commitment`        every `qro:Pub`;
  step 5  `known-answer`      every `qro:Decode`, and `raw-form` where its raw result is not in a form its rule
                              reads or the rule cannot account for it, and `step-unbuilt` for a rule not built;
  step 8  `calibration-link`  every `qro:Snapshot` and every `qro:Job`, and `step-unbuilt` for a link word this
                              version does not build.
A file these steps read is a file the crate holds, whose digest step 2 has held. What a hostile file does to a
step is a refusal, never a crash (FORMAT.md, item 16): any exception the contents of a file or the shape of the graph
raise is caught and refused, with its text in the detail. The name is the step's own, `commitment`, `known-answer` or
`calibration-link`, but for a raw result: step 5 gives `raw-form` for one its reader cannot read or its rule cannot
account for. (Through the command line step 3 refuses the first of those before step 5 runs, also as `raw-form`; only
step 5 can tell the second.) In these three steps an OSError is the host's, not the crate's, and is not caught: a
PermissionError is misuse, exit 2, and the rest the checker failing, exit 3; a MemoryError is not caught either, exit 3.
Step 3 is P0's and reads every raw result before these run: what a MemoryError gives there is P0's (FORMAT.md, item 16).

What a step keeps of a file is what it needs of it, and never its bytes: of a raw result a count of rows and an echo
for each PUB (the echo to 65 characters), or a verdict on a known answer; of a job line a commitment for each PUB (to 64
characters); of a snapshot its device, stamp and newest value. A file is read when it is wanted and let go once read,
so that a crate of many files costs the memory of the largest one, with a few hundred bytes for each PUB and job beside
it, and not the sum of the files (the verifier's D2 of round 1 and D3 of round 2). What the largest costs is the parse
of it, and no bound that a file cannot exceed is known. The worst cases MEASURED, by shape, as a multiple of the file's
size, the bytes read counted (the P1.md entry that answers the verifier's round 3 has the table):
  - a JSON file (a job line, a record, a raw result's wrapper, a snapshot): 46 for nested one-element arrays, 39 for
    nested single-key objects, 26 for flat arrays or objects of them;
  - a snapshot that is valid, in step 8, where the digest spells each number again as an object: 147 for one list of
    small integers (the `qubits` of a gate or of an entry of `general_qlists`), 35 for many lists of one, 13 to 16 for
    its measured entries;
  - an IBM result's array: 6.7 times its inflated size when the data do not deflate (5.0 times the file: 447 MB at the
    reader's cap, 64 MiB inflated, from an 89 MB file), and 2.0 when they do (135 MB from 88 KB);
  - a known-answer circuit, which is refused after it is read: 21.7 for lines of two characters, 18.7 for blank ones.
Those are what was measured, not limits: a shape not tried may cost more.

Step 4 recomputes each commitment from its Pub's record and holds the result to the Pub's claim, to the job line,
and to IBM's own echo inside the raw bytes: never to the manifest, which the recomputation shares a producer with.
Step 5 re-decodes the raw bytes under the rule and bit order the crate names, and holds that order to a known
answer read from the committed circuit. Step 8 recomputes each snapshot's claims from its file and each job's link
from the snapshots the crate carries. None of them reads Quantum-Film's decoded counts, its verdict files or its
manifest.
"""
from pathlib import Path

from qro import p1_calibration as cal
from qro import p1_commit, p1_decode, p1_forms, spelling
from qro.checker import RawFormError, describe
from qro.p1_graph import GraphError, Index
from qro.refusal import Refused

IBM_FORM = "ibm-sampler-result/v1"
ATLAS_VECTOR_FORM = "atlas-known-answer-vector/v1"
KNOWN_ANSWER = "known-answer"
# Link words this version does not build: a crate that uses one is refused `step-unbuilt` (P1's design, item 5).
UNBUILT_LINKS = ("read-before-run", "read-after-run", "provider-linked")
RECORD_FORMAT = "quantum-film/device-run/v1"
COMMITMENT_LENGTH = 64                        # a commitment is 64 lowercase hex digits
KINDS = {str: "a string", int: "a whole number (a float or a bool is none)"}      # how a record's field is described
# What a step's own helpers raise for a file or a graph that is not as the entity model says; each is refused by the
# step's name with its text. Any other exception a hostile input raises is refused with its type and text.
EXPECTED = (GraphError, RawFormError, p1_forms.SnapshotError, p1_decode.DecodeError, p1_decode.KnownAnswerError)


class RecordError(ValueError):
    """A record or line file of Quantum-Film's that is not in the shape step 4 reads."""


def _commitment(where, detail):
    return Refused("commitment", where, detail)


def _known(where, detail):
    return Refused("known-answer", where, detail)


def _link(where, detail):
    return Refused("calibration-link", where, detail)


def _failed(x):
    return str(x) if isinstance(x, EXPECTED + (RecordError,)) else describe(x)


def _hold(index_error, md):
    """An Index of the metadata, or the step's refusal where it cannot be one."""
    try:
        return Index(md)
    except GraphError as x:
        raise index_error("@graph", str(x)) from None


_bytes = p1_decode.crate_file                 # the bytes of a File of the crate; GraphError where the entity is not one


def _json(crate, entity, what):
    return p1_forms.load_json(_bytes(crate, entity, what), what)


def _parse(crate, raw):
    """The raw result entity's bytes parsed by the raw form it names. It is never kept here: the caller takes what it
    needs of it and lets it go."""
    form = raw.get("qro:rawForm")
    if form not in p1_forms.PARSERS:
        raise RawFormError(f"{raw['@id']}: no reader is built for the raw form {form}")
    return p1_forms.parse_raw(form, _bytes(crate, raw, "the raw result"))


def _visit(idx, type, step, refuse):
    """Each entity of a type, in @id order, each under the step's safety net: a Refused is the step's answer; an
    OSError is the host's (a PermissionError the user's) and a MemoryError is the host running out, neither a verdict
    on the crate, so neither is caught here (exit 3, and exit 2 for a PermissionError); and anything else a hostile
    input raised is a refusal by the step's name. No step keeps a file, or what a file parsed to, from one entity to
    the next (but a count of rows, an echo, a commitment, a verdict, and a snapshot's device, stamp and newest value),
    so the memory of a step is the parse of the largest file, with a few hundred bytes for each PUB and job beside it,
    not the sum of the files. What a parse costs is the module docstring's, by shape (up to 147 times a file, the
    worst measured); no bound that a file cannot exceed is known. A raw result is met first at step 3, which is P0's."""
    for e in sorted(idx.of_type(type), key=lambda e: e["@id"]):
        try:
            step(e)
        except Refused:
            raise
        except (OSError, MemoryError):
            raise
        except Exception as x:
            raise refuse(e["@id"], f"cannot be checked: {_failed(x)}") from None


def _held(have, want, where, what, refuse):
    if have != want:
        raise refuse(where, f"{what} is {have!r}; the commitment binds {want!r}")


# -- step 4 ----------------------------------------------------------------------------------------------------
def step4(crate_dir, md):
    """Every Pub's commitment, recomputed from its record and held to its claim, to its job line and to IBM's echo
    inside the raw result's bytes. A Pub that says `none` says the provider held none, and is taken at its word."""
    crate, idx, facts, lines, listings = Path(crate_dir), _hold(_commitment, md), {}, {}, {}

    def one(pub):
        _pub4(crate, idx, facts, lines, listings, pub)
    _visit(idx, "qro:Pub", one, _commitment)


def _facts4(crate, facts, raw):
    """(the rows each PUB of a raw result holds, the commitment IBM echoed for each): all that step 4 keeps of it, and an
    echo only to one character past the length of a commitment (a longer one is no commitment, and is not kept)."""
    if raw["@id"] not in facts:
        result = _parse(crate, raw)
        facts[raw["@id"]] = (tuple(p.rows for p in result.pubs),
                             tuple(None if p.echo is None else p.echo[:COMMITMENT_LENGTH + 1] for p in result.pubs))
    return facts[raw["@id"]]


def _commits4(doc):
    """What step 4 keeps of a job line: its `commitments` as a tuple, each a string of at most 64 characters or None for
    anything else; None where the line is no object or holds no list of them. Nothing else of the line is kept."""
    commits = doc.get("commitments") if isinstance(doc, dict) else None
    if not isinstance(commits, list):
        return None
    return tuple(c if type(c) is str and len(c) <= COMMITMENT_LENGTH else None for c in commits)


def _record_fields(crate, idx, pub, where):
    """The fourteen inputs of the commitment, as the Pub's record gives them: GraphError or RecordError where the
    record is not Quantum-Film's device-run/v1 with every one of them of its type."""
    rec = _json(crate, idx.one(pub, "qro:record"), "the Pub's record")
    if not isinstance(rec, dict) or rec.get("format") != RECORD_FORMAT:
        raise RecordError(f"the Pub's record is not {RECORD_FORMAT}")
    src = rec.get("source")
    if not isinstance(src, dict):
        raise RecordError("the record has no source")
    fields = {}
    for name, kind in p1_commit.FIELDS:
        owner = rec if name in ("stock", "role", "basis") else src
        value = owner.get(name)
        if type(value) is not kind:
            raise RecordError(f"the record's {name} is not {KINDS[kind]}")
        fields[name] = value
    if "options" not in src:
        raise RecordError("the record states no options")
    return fields, src["options"]


def _pub4(crate, idx, facts, lines, listings, pub):
    pid = pub["@id"]
    where = f"{pid} qro:commitment"
    claim = pub.get("qro:commitment")
    if claim is None:
        raise _commitment(where, "a Pub states its commitment, or `none` where the provider held none")
    if claim == "none":
        return
    if spelling.problem("digest", claim):
        raise _commitment(where, "a commitment is 64 lowercase hex digits, or `none`")
    k = idx.pub_index(pub)
    job = idx.job_of(pub)
    raw = idx.raw_of(job)
    decode = idx.decode_of(raw)
    fields, options = _record_fields(crate, idx, pub, where)
    # the inputs that have a counterpart the crate states of its own, each held to it
    device, program = idx.one(job, "qro:device"), idx.one(job, "instrument")
    for what, have, want in (("the Pub's qro:role", pub.get("qro:role"), fields["role"]),
                             ("the Pub's qro:basis", pub.get("qro:basis"), fields["basis"]),
                             ("the device's qro:deviceKind", device.get("qro:deviceKind"), fields["kind"]),
                             ("the device's name", device.get("name"), fields["backend"]),
                             ("the program's name", program.get("name"), fields["program"]),
                             ("the decode's qro:decodeRule", decode.get("qro:decodeRule"), fields["decode"]),
                             ("the Pub's index in its id", k, fields["pub"])):
        _held(have, want, f"{pid} qro:record", what, _commitment)
    if spelling.problem("digest", fields["options_sha256"]) or p1_commit.options_digest(options) \
            != fields["options_sha256"]:
        raise _commitment(f"{pid} qro:record", "the record's options do not digest to its options_sha256")
    for name in ("circuit_sha256", "isa_sha256"):
        if not idx.files_by_sha256(fields[name]):
            raise _commitment(f"{pid} qro:record", f"no file of the crate has the {name} the commitment binds, "
                                                   f"{fields[name]}")
    # the shots the raw result holds for this PUB, and the PUB the commitment is for
    if raw.get("qro:rawForm") != IBM_FORM:
        raise _commitment(f"{raw['@id']} qro:rawForm", f"only {IBM_FORM} carries IBM's echo of a commitment")
    rows, echoes = _facts4(crate, facts, raw)
    if job["@id"] not in listings:                    # once for each job, however many PUBs it lists
        listings[job["@id"]] = sorted(idx.pub_index(p) for p in idx.pubs_of(job))
    listed = listings[job["@id"]]
    if listed != list(range(len(rows))):
        raise _commitment(f"{job['@id']} object", f"the job lists the PUBs {listed}; its raw result holds "
                                                  f"{len(rows)}")
    if rows[k] != fields["shots"]:
        raise _commitment(f"{pid} qro:record", f"the record says {fields['shots']} shots; the raw result holds "
                                               f"{rows[k]} rows for PUB {k}")
    want = p1_commit.commitment_v3(**fields)
    if claim != want:
        raise _commitment(where, f"the claim is {claim}; the commitment recomputes to {want}")
    line = idx.one(job, "qro:line")
    if line["@id"] not in lines:
        lines[line["@id"]] = _commits4(_json(crate, line, "the job line"))
    commits = lines[line["@id"]]
    if commits is None or len(commits) != len(rows):
        raise _commitment(f"{line['@id']} commitments", f"the job line lists "
                                                        f"{'no' if commits is None else len(commits)} "
                                                        f"commitments; the job has {len(rows)} PUBs")
    if commits[k] != want:
        raise _commitment(f"{line['@id']} commitments", f"the job line does not hold {want} for PUB {k}")
    echo = echoes[k]
    if echo is None:
        raise _commitment(f"{raw['@id']} pub_results[{k}]", "the raw result carries no echo of the commitment: IBM "
                                                            "never held one, or the bytes are not IBM's")
    if echo != want:
        raise _commitment(f"{raw['@id']} pub_results[{k}]", f"IBM echoed {echo}; the commitment recomputes to {want}")


# -- step 5 ----------------------------------------------------------------------------------------------------
def step5(crate_dir, md):
    """Every Decode's raw result re-decoded under the rule and the bit order it names, and the order held by a known
    answer: a Pub of role known-answer on the same device, under the same rule and order (and, where both jobs have
    a line, the same bundle), whose own raw result, decoded under that order, comes out as the circuit says."""
    crate, idx, verdicts = Path(crate_dir), _hold(_known, md), {}

    def one(decode):
        _decode5(crate, idx, verdicts, decode)
    _visit(idx, "qro:Decode", one, _known)


def _decode5(crate, idx, verdicts, d):
    did = d["@id"]
    rule, order = d.get("qro:decodeRule"), d.get("qro:bitOrder")
    for term, value in (("qro:decodeRule", rule), ("qro:bitOrder", order), ("qro:knownAnswer", d.get("qro:knownAnswer"))):
        if value is None:
            raise _known(f"{did} {term}", f"a Decode states its {term}")
    raws = idx.refs_of_type(d, "object", "qro:RawResult")
    if len(raws) != 1:
        raise _known(f"{did} object", f"a Decode reads one raw result, and this one lists {len(raws)}")
    raw = raws[0]
    if rule not in p1_decode.RULES:
        raise Refused("step-unbuilt", f"{did} qro:decodeRule", f"no decode rule {rule} is built")
    r = p1_decode.RULES[rule]
    if order not in r.orders:
        raise _known(f"{did} qro:bitOrder", f"{rule} does not read the order {order}: it reads {sorted(r.orders)}")
    if raw.get("qro:rawForm") not in r.forms:
        raise Refused("raw-form", f"{raw['@id']} qro:rawForm", f"{rule} does not read the raw form "
                                                              f"{raw.get('qro:rawForm')}")
    job = idx.job_of_raw(raw)
    # the known answer: a Pub of role known-answer, decoded the same way, on the same device, in the same bundle
    kid = idx.one(d, "qro:knownAnswer", "qro:Pub")["@id"]
    k = idx.by_id[kid]
    if k.get("qro:role") != KNOWN_ANSWER:
        raise _known(f"{did} qro:knownAnswer", f"{kid} has the role {k.get('qro:role')}, not {KNOWN_ANSWER}")
    kjob = idx.job_of(k)
    kraw = idx.raw_of(kjob)
    kd = idx.decode_of(kraw)
    if (kd.get("qro:decodeRule"), kd.get("qro:bitOrder")) != (rule, order):
        raise _known(f"{did} qro:knownAnswer", f"{kid} is decoded under {kd.get('qro:decodeRule')} and "
                                               f"{kd.get('qro:bitOrder')}, not {rule} and {order}")
    if idx.one(job, "qro:device")["@id"] != idx.one(kjob, "qro:device")["@id"]:
        raise _known(f"{did} qro:knownAnswer", f"{kid} ran on another device than {job['@id']}")
    if "qro:line" in job and "qro:line" in kjob:
        have = _bundle5(crate, idx.one(job, "qro:line"), "the job line")
        want = _bundle5(crate, idx.one(kjob, "qro:line"), "the known answer's job line")
        if not isinstance(have, str) or have != want:
            raise _known(f"{did} qro:knownAnswer", f"{kid} was submitted in another bundle than {job['@id']}")
    # a verdict is kept for each known answer, (holds, text), and never the result it was drawn from; where this
    # decode reads that very result, the one parse serves both
    parsed = None
    if kid not in verdicts:
        verdicts[kid], parsed = _verdict5(crate, idx, k, kraw, rule, order)
        if kraw["@id"] != raw["@id"]:
            parsed = None
    holds, text = verdicts[kid]
    if not holds:
        raise _known(f"{did} qro:bitOrder", f"{rule} read under {order} does not hold the known answer {kid}: {text}")
    # the raw result itself is accounted for by the rule
    if parsed is None:
        parsed = _raw5(crate, raw)
    try:
        p1_decode.account(rule, parsed, order, {p.get("qro:role") for p in idx.pubs_of(job)})
    except p1_decode.DecodeError as x:
        raise Refused("raw-form", raw["@id"], f"{rule} cannot account for it: {x}") from None


def _bundle5(crate, line, what):
    """The `bundle_sha256` of a job line, or None where it states none; the line itself is let go before the next is read."""
    doc = _json(crate, line, what)
    return doc.get("bundle_sha256") if isinstance(doc, dict) else None


def _raw5(crate, raw):
    """A raw result parsed, or the refusal `raw-form` where its bytes are not in the form it names."""
    try:
        return _parse(crate, raw)
    except RawFormError as x:
        raise Refused("raw-form", raw["@id"], f"not in the raw form {raw.get('qro:rawForm')}: {x}") from None


def _verdict5(crate, idx, k, kraw, rule, order):
    """((holds, text), the known answer's parsed result): the verdict on a known-answer Pub, its raw result decoded
    under the order a decode declares. The caller keeps the verdict and lets the result go."""
    form = kraw.get("qro:rawForm")
    if form not in p1_decode.RULES[rule].forms:
        raise Refused("raw-form", f"{kraw['@id']} qro:rawForm", f"{rule} does not read the raw form {form}")
    if rule == p1_decode.ATLAS_RULE and form != ATLAS_VECTOR_FORM:
        raise _known(f"{kraw['@id']} qro:rawForm", f"a known answer under {rule} is the frozen vector, "
                                                   f"{ATLAS_VECTOR_FORM}, not {form}")
    parsed = _raw5(crate, kraw)
    if rule == p1_decode.IBM_RULE:
        # the circuit the commitment binds, found by its digest, says which qubits the known answer flips
        record = _json(crate, idx.one(k, "qro:record"), "the known answer's record")
        source = record.get("source") if isinstance(record, dict) else None
        digest = source.get("circuit_sha256") if isinstance(source, dict) else None
        if not isinstance(digest, str):
            raise RecordError("the known answer's record names no circuit_sha256")
        files = idx.files_by_sha256(digest)
        if not files:
            raise p1_decode.KnownAnswerError(f"no file of the crate has the known answer's circuit {digest}")
        expected = p1_decode.expected_set(_bytes(crate, files[0], "the known-answer circuit"))
        v = p1_decode.known_answer_verdict(p1_decode.decode_counts(rule, parsed, idx.pub_index(k), order), expected)
        return (v.holds, v.text()), parsed
    v = p1_decode.atlas_vector_verdict(parsed, order)
    return (v.holds, v.text()), parsed


# -- step 8 ----------------------------------------------------------------------------------------------------
def step8(crate_dir, md):
    """Every snapshot's stamp, newest value and values-digest recomputed from its file, and every job's calibration
    link recomputed from its first shot, which is the start of the execution span in its raw result, and from the
    snapshots the crate carries of its device: those whose files are of a backend of its name, whichever entities of
    the crate name them. A job's start and end times are held to that span wherever its raw result carries one."""
    crate, idx = Path(crate_dir), _hold(_link, md)
    snaps, by_name = {}, {}

    def snapshot(e):
        _snapshot8(crate, idx, snaps, by_name, e)
    _visit(idx, "qro:Snapshot", snapshot, _link)

    def job(e):
        _job8(crate, idx, snaps, by_name, e)
    _visit(idx, "qro:Job", job, _link)


def _snapshot8(crate, idx, snaps, by_name, e):
    sid = e["@id"]
    snap = p1_forms.parse_snapshot(_bytes(crate, e, "the snapshot"))
    for term, want in cal.claims(snap).items():
        if term not in e:
            raise _link(f"{sid} {term}", f"a Snapshot states its {term}")
        if e[term] != want:
            raise _link(f"{sid} {term}", f"the claim is {e[term]}; the file gives {want}")
    device = idx.one(e, "qro:device")
    if device.get("name") != snap.device:
        raise _link(f"{sid} qro:device", f"the device is named {device.get('name')!r}; the file is of {snap.device!r}")
    # all that the link rule weighs of a snapshot is its device, its stamp and its newest value; the parsed document, which
    # the claims have just been drawn from, is not kept
    light = p1_forms.Snapshot(snap.device, snap.stamp, snap.newest, {})
    snaps[sid] = light
    by_name.setdefault(snap.device, {})[sid] = light


def _span8(crate, idx, job):
    """(the first shot, the last) of the execution span in the one raw result a job made; None where it made none or
    its result carries no span. The result itself is not kept."""
    raws = idx.refs_of_type(job, "result", "qro:RawResult")
    if not raws:
        return None
    if len(raws) != 1:
        raise GraphError(f"{job['@id']} result: {len(raws)} raw results, not one")
    result = _parse(crate, raws[0])
    return (result.first_shot, result.last_shot) if result.spans else None


def _job8(crate, idx, snaps, by_name, job):
    jid = job["@id"]
    word = job.get("qro:calibrationLink")
    if word is None:
        raise _link(f"{jid} qro:calibrationLink", "a Job states how its calibration is linked, or says unknown")
    if word in UNBUILT_LINKS:
        raise Refused("step-unbuilt", f"{jid} qro:calibrationLink", f"the link {word} is not built: no v0 crate uses it")
    refs = idx.refs(job, "qro:calibration")
    # the raw result carries the provider's own record of when the job ran, its execution span, and the times a Job
    # states are held to it wherever it carries one, whatever the link word (the lead's ruling, round 1; the design's
    # paragraph): the claim cannot differ from the record, nor from what the rule below uses
    span = _span8(crate, idx, job)
    if span is not None:
        for term, want in (("startTime", span[0]), ("endTime", span[1])):
            have = job.get(term)
            if have is None or have == "unknown" or p1_forms.parse_time(have, "Z") != want:
                raise _link(f"{jid} {term}", f"the Job states {have}; the execution span in its raw result gives "
                                             f"{spelling.time(want)}")
    if word in ("unknown", "unexposed"):
        if refs:
            raise _link(f"{jid} qro:calibration", f"a Job whose link is {word} names no snapshot")
        return
    if word not in (cal.AT_FIRST_SHOT, cal.IN_GAP):
        raise _link(f"{jid} qro:calibrationLink", f"{word} is not a link this step knows")
    if span is None:
        raise _link(f"{jid} qro:calibrationLink", f"{word} needs the Job's first shot, and its raw result holds none")
    first_shot = span[0]                  # the first shot is the span's, never the start time the Job states
    # the device is its backend's name: a snapshot is of the job's device when its file says it is of a backend of that
    # name, whichever entity of the crate names it (the verifier's D3, round 1)
    name = idx.one(job, "qro:device").get("name")
    for r in refs:
        if r not in snaps:
            raise _link(f"{jid} qro:calibration", f"{r} is not a Snapshot of the crate")
        if snaps[r].device != name:
            raise _link(f"{jid} qro:calibration", f"{r} is a snapshot of {snaps[r].device!r}, not of {name!r}")
    carried = by_name.get(name, {})
    if len(refs) != (1 if word == cal.AT_FIRST_SHOT else 2):
        raise _link(f"{jid} qro:calibration", f"{word} names {1 if word == cal.AT_FIRST_SHOT else 2} snapshots, "
                                              f"and this names {len(refs)}")
    # C is the one the history returned: the older of two, by stamp
    ordered = sorted(refs, key=lambda i: (snaps[i].stamp, i))
    if len(ordered) == 2 and snaps[ordered[0]].stamp == snaps[ordered[1]].stamp:
        raise _link(f"{jid} qro:calibration", "the two snapshots have one stamp, so neither is the older")
    try:
        got, ids = cal.link_for(first_shot, ordered[0], carried)
    except cal.LinkError as x:
        raise _link(f"{jid} qro:calibration", f"not {word}: {x}") from None
    if got != word:
        if got == cal.IN_GAP:
            raise _link(f"{jid} qro:calibrationLink", f"the link is {cal.IN_GAP}, not {word}: {ids[1]} was stamped "
                                                      "and entirely measured before the first shot")
        raise _link(f"{jid} qro:calibrationLink", f"the link is {got}, not {word}: no carried snapshot was stamped "
                                                  "and entirely measured between")
    if sorted(ids) != sorted(refs):
        raise _link(f"{jid} qro:calibration", f"the link names {sorted(ids)}; the Job names {sorted(refs)}")
