"""Custody logs and audit records (study QRO-0, section 9.2), and the custody check that holds them, beside the
checker's nine steps: `custody-chain` and `custody-head` (section 10).

A custody log is append-only and dated, one line per event, each line one canonical JSON object
(qro/canonical.py's compact(): sorted keys, no space, ASCII, LF). Its fields are qro/vocabulary.py's
CUSTODY_LINE. Each line's `prev` is the SHA-256 of the line before it, its LF included; the first line's is the
SHA-256 of the empty string, so dropping the first line shows too. The log's head is the SHA-256 of its last
line; an empty log's head is `none`, which pins nothing.

An audit record sits beside the crate it audits, never inside it: one canonical JSON object
(qro/canonical.py's dumps()) whose fields are qro/vocabulary.py's AUDIT_RECORD. Its `logHead` pins the auditor's
log up to that head, where someone other than the log's writer holds the record and the log is shown to a
checker; lines after the head stay uncovered, and a writer who rewrites its own log's tail and its own held
record shows nothing. Both are stated limits (section 9.2).

What the check does not hold, each a stated limit (P0's verifier's notes):
  - the order of `at`: a line may be dated before the line above it;
  - `at` against any clock: a line may be dated in the future (P0's verifier, round 2);
  - what the events say together: a withdrawal of a crate never received, or a crate received again after its
    withdrawal, is a whole chain;
  - free text: `from`, `reason` and `auditor` take any text; the privacy gate reads them only where the log is
    committed to a repository;
  - an audit record's `crate` against the log: the record names a crate, and the log need not hold it;
  - forks: a custodian who shows two auditors two different logs, each whole, shows nothing in either; only the
    two records, compared, can.
Hostile bytes are refused by name, never crash it. Stdlib only.
"""
import hashlib
import json

from qro import canonical, spelling
from qro import vocabulary as V
from qro.refusal import Refused

EMPTY = hashlib.sha256(b"").hexdigest()


def _strict(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("a key twice in one object")
    return dict(pairs)


def _no_constant(name):
    raise ValueError(f"{name} has no spelling")


def _load(data, where, canonical_form):
    """One JSON object in ASCII, in its canonical bytes, or Refused("spelling") - never a crash."""
    try:
        obj = json.loads(data.decode("ascii"), object_pairs_hook=_strict, parse_constant=_no_constant)
        again = canonical_form(obj)
    except (UnicodeDecodeError, ValueError, TypeError, RecursionError):
        raise Refused("spelling", where, "not one JSON object in ASCII, with a spelling for every value") from None
    if not isinstance(obj, dict) or again != data:
        raise Refused("spelling", where, "not its canonical bytes")
    return obj


def _fields(obj, fields, where):
    keys = [f.key for f in fields]
    if sorted(obj) != keys:
        raise Refused("spelling", where, f"the fields are {', '.join(keys)}, and no others")
    for f in fields:
        v = obj[f.key]
        if isinstance(v, str) and v in f.absent:
            continue
        values = v if f.many else [v]
        if f.many and (not isinstance(v, list) or not v or not all(isinstance(x, str) for x in v)
                       or v != sorted(set(v))):
            raise Refused("spelling", f"{where} {f.key}", "a sorted list of distinct values, one or more")
        for x in values:
            p = spelling.problem(f.spelling, x)
            if p:
                raise Refused("spelling", f"{where} {f.key}", p)


def lines(data):
    """A log's lines, each with its LF, refusing a log whose last byte is not an LF."""
    if data and not data.endswith(b"\n"):
        raise Refused("spelling", "the log's end", "every line ends in LF")
    return [line + b"\n" for line in data.split(b"\n")[:-1]]


def check_log(data):
    """The log's head, if every line is in its spelling and the chain holds; otherwise Refused."""
    prev = EMPTY
    for n, line in enumerate(lines(data), 1):
        where = f"log line {n}"
        obj = _load(line, where, canonical.compact)
        if not isinstance(obj.get("event"), str) or obj["event"] not in V.CUSTODY_LINE:
            raise Refused("spelling", f"{where} event", f"one of {sorted(V.CUSTODY_LINE)}")
        _fields(obj, V.CUSTODY_LINE[obj["event"]], where)
        if obj["prev"] != prev:
            raise Refused("custody-chain", where, "its prev is not the SHA-256 of the line before it")
        prev = hashlib.sha256(line).hexdigest()
    return "none" if prev == EMPTY else prev


def line(log_data, event, **fields):
    """The next line of a log whose bytes are `log_data`: a received or withdrawn event."""
    prev = hashlib.sha256(lines(log_data)[-1]).hexdigest() if log_data else EMPTY
    obj = dict(fields, event=event, prev=prev)
    _fields(obj, V.CUSTODY_LINE.get(event, ()), "the new line")
    return canonical.compact(obj)


def record(**fields):
    """An audit record's canonical bytes."""
    _fields(fields, V.AUDIT_RECORD, "the audit record")
    return canonical.dumps(fields)


def check_record(record_data, log_data):
    """Hold an audit record to its auditor's custody log: its logHead must be `none`, or the SHA-256 of one of the
    log's lines. Returns the record; otherwise Refused."""
    heads = {hashlib.sha256(x).hexdigest() for x in lines(log_data)}
    check_log(log_data)
    rec = _load(record_data, "the audit record", canonical.dumps)
    _fields(rec, V.AUDIT_RECORD, "the audit record")
    if rec["logHead"] != "none" and rec["logHead"] not in heads:
        raise Refused("custody-head", "the audit record logHead", "matches no line of the auditor's custody log")
    return rec
