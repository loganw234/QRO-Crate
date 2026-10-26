"""A calibration's identity and a job's link to one (P1's design, item 5; P1.1). Standard library only.

The values-digest. A calibration is identified by the SHA-256 of its values with every date left out, so that two
snapshots whose values are equal are equal whatever their stamps and whatever dates their values carry (study
QRO-0, section 6). The bytes it hashes are these, exactly:
  1. the snapshot, parsed by p1_forms.parse_snapshot (the closed form);
  2. `last_update_date` deleted;
  3. every member named `date` deleted, at any depth, so no date of any kind is in the preimage;
  4. every JSON number replaced by the object {"n": "<the 16 lowercase hex digits of its binary64 bits, big-endian>"},
     an integer first converted to binary64 (the form refuses an integer binary64 cannot hold), so that 32 and
     32.0 are one value and -0.0 is not 0.0;
  5. serialised with json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True), encoded as ASCII;
  6. SHA-256, as 64 lowercase hex digits.
Lists keep the file's order: `qubits[i]` is qubit i, and sorting would hide a swap. A provider that re-ordered a
list between two fetches of one calibration would show two digests, a calibration missed as equal and never one
falsely taken for equal. MEASURED over the 12 snapshots of Quantum-Film's records and the 2026-10-14 read: kingston
three digests, marrakesh two, fez one, as study section 4.5's table has them (P1's design, measurement 2).

The link. A job's first shot S is the start of its raw result's execution span. A snapshot C is valid for S iff its
stamp and its newest measurement date are both strictly before S. The link a job may claim, for the snapshot C the
provider's history returned for a query at S, and the snapshots the crate carries of that device:
  history-at-first-shot [C]    C valid, and no carried D with a later stamp than C's that is also valid for S;
  history-in-gap [C, D]        C valid, and D the newest-stamped carried snapshot that is valid for S and stamped
                               after C: the history had not yet returned D, which was stamped and measured.
Anything else, C not valid above all, is not a link. Every `history-` link is a necessary condition for being in
force, not proof that it was (study section 6).
"""
import hashlib
import json
import struct

from qro import spelling
from qro.p1_forms import Snapshot, SnapshotError, parse_snapshot

__all__ = ["Snapshot", "SnapshotError", "parse_snapshot", "values_digest", "claims", "valid_for", "link_for",
           "LinkError", "AT_FIRST_SHOT", "IN_GAP"]

AT_FIRST_SHOT = "history-at-first-shot"
IN_GAP = "history-in-gap"


class LinkError(ValueError):
    """The snapshot the history returned is not valid for the job's first shot."""


def _spell(x):
    if type(x) in (int, float):
        return {"n": struct.pack(">d", float(x)).hex()}
    if isinstance(x, dict):
        return {k: _spell(v) for k, v in x.items() if k != "date"}
    if isinstance(x, list):
        return [_spell(v) for v in x]
    return x


def values_digest(snapshot):
    """The SHA-256 of a snapshot's values, every date left out: 64 lowercase hex digits."""
    doc = {k: v for k, v in snapshot.doc.items() if k != "last_update_date"}
    text = json.dumps(_spell(doc), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def claims(snapshot):
    """The three CHECKED terms a Snapshot entity states, as the profile spells them."""
    return {"qro:valuesDigest": values_digest(snapshot), "qro:stamp": spelling.time(snapshot.stamp),
            "qro:newestValue": spelling.time(snapshot.newest)}


def valid_for(snapshot, first_shot):
    """Whether a snapshot's stamp and its newest value date are both strictly before the first shot."""
    return snapshot.stamp < first_shot and snapshot.newest < first_shot


def link_for(first_shot, history, carried):
    """The link a job may claim: (word, (ids...)) with the history's snapshot first. `carried` is {id: snapshot} of
    every snapshot the crate carries of the job's device, the history's among them: step 8 takes them by the backend
    each snapshot's file is of, the device's name, whichever entities of the crate name them. `history` is the id of
    the snapshot the history returned. LinkError where it is not carried, or not valid for the first shot."""
    if history not in carried:
        raise LinkError(f"{history} is not a snapshot the crate carries of this device")
    c = carried[history]
    if not valid_for(c, first_shot):
        raise LinkError(f"{history} was stamped {spelling.time(c.stamp)} and last measured "
                        f"{spelling.time(c.newest)}, and is not entirely before the first shot at "
                        f"{spelling.time(first_shot)}")
    gaps = [(d.stamp, i) for i, d in carried.items() if d.stamp > c.stamp and valid_for(d, first_shot)]
    if not gaps:
        return AT_FIRST_SHOT, (history,)
    return IN_GAP, (history, max(gaps)[1])
