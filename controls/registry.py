"""The controls: study QRO-0's section 11, one row a control, each one planted fault, and the parcel that owns it.

A control belongs to the parcel whose step refuses it, or states it (section 13). The genuine crate is every
control's twin, and must be accepted. tests/controls/test_control_registry.py walks this table both ways (ParcelRound,
METHOD.md section 2): a row of P0's that no planted fault exercises fails by name, a builder that names no row
fails by name, and every other owner's row is printed by name as pending until its parcel lands.

PLANTS holds P0's builders. plants() merges them with each parcel's, from the parcel's own plants_<parcel>.py
beside this file (P0.1), so that parcels building at once never edit this file. It merges when called, never
while this module is being imported: a parcel's plants module imports this one, for twin(), RAW and the helpers,
and a merge made at import found that module half made whenever it was imported first (P0.1's verifier, round 1,
D2). Each plant takes an empty directory and returns what it planted: a crate directory for the checker, or a
(log, record) pair for the custody check. Stdlib only.
"""
import hashlib
import importlib
import json
from dataclasses import dataclass
from pathlib import Path

from qro import canonical, custody, fixture


@dataclass(frozen=True)
class Control:
    name: str
    fault: str
    expected: str         # "refused", "accepted" or "states": what must come of it
    refusal: str | None   # the refusal's name, where it is refused
    owner: str
    text: str             # section 11's expected cell, as the study words it


CONTROLS = (
    Control("shot-moved", "one shot changed, its digest left", "refused", "raw-digest", "P0", "`raw-digest`"),
    Control("job-reattributed", "one IBM job's raw result filed under another's id", "refused", "commitment", "P1",
            "`commitment`; or `count-unpaid` first, where the two jobs' shot counts differ"),
    Control("bits-mirrored", "the decode told the mirrored order", "refused", "known-answer", "P1", "`known-answer`"),
    Control("compile-broken", "a gate-list change that moves a Z-basis probability, digests recomputed", "refused",
            "compile-uncontrolled", "P2", "`compile-uncontrolled`"),
    Control("qpy-only", "one QPY byte changed, with its digest, the commitment, IBM's echo of it inside the raw "
            "result and every digest recomputed, the gate list left", "accepted", None,
            "P1", "accepted by the crate-only checker. Refused by the QPY stage or by the anchor's re-fetch, where "
                  "the provider's copy differs"),
    Control("calibration-late", "a snapshot stamped or measured after the first shot, claimed "
            "`history-at-first-shot`", "refused", "calibration-link", "P1", "`calibration-link`"),
    Control("calibration-gap", "a job linked `history-at-first-shot` whose first shot falls after a newer carried "
            "snapshot's stamp and newest value date", "refused", "calibration-link", "P1",
            "`calibration-link`: the link is `history-in-gap`"),
    Control("calibration-restamped", "two snapshots with equal values and different stamps", "accepted", None, "P1",
            "not a refusal: their values-digests are EQUAL"),
    Control("count-unpaid", "`shots` stated one higher than held", "refused", "count-unpaid", "P0", "`count-unpaid`"),
    Control("self-compare", "a run against itself", "refused", "comparison-trivial", "P3", "`comparison-trivial`"),
    Control("resealed-compare", "a run against a copy with one shot moved and digests recomputed", "refused",
            "comparison-trivial", "P3", "`comparison-trivial`: the two share job ids and commitments"),
    Control("shared-control", "two runs sharing only a known-answer job", "accepted", None, "P3",
            "not refused (section 8)"),
    Control("class-declared", "a measure declared \"signal\" with equal law and twin values", "refused",
            "measure-class", "P2", "`measure-class`"),
    Control("float-spelt", "a value spelt as a JSON number", "refused", "spelling", "P0", "`spelling`"),
    Control("kind-missing", "a field with no kind", "refused", "field-kind", "P0", "`field-kind`"),
    Control("adjusted-as-raw", "a non-integer corrected count in the raw slot, digest recomputed", "refused",
            "raw-form", "P0", "`raw-form`"),
    Control("single-runs", "one law job a run", "states", None, "P3",
            "\"not isolated from the pipeline: drift UNMEASURED, `none`\""),
    Control("readout-unbounded", "runs whose only readout control is one known-answer pattern", "states", None, "P3",
            "\"isolated as quantum: no, readout's effect unbounded\""),
    Control("time-confounded", "runs on two devices in disjoint time blocks", "states", None, "P3",
            "\"the difference is the device's-and-its-time's\""),
    Control("joint-omission", "per-cause tolerance checks that each pass, offered in place of the data", "refused",
            None, "P3", "refused: verdicts are computed only on the runs' data"),
    Control("shot-moved-resealed", "one shot moved, every digest recomputed", "accepted", None, "P1",
            "accepted by the crate-only checker, a stated limit. Refused by the raw re-fetch, where the provider's "
            "copy differs"),
    Control("unit-known-answer", "a free-tier unit whose known answer fails on one device", "refused",
            "known-answer", "P5", "refused at intake: `known-answer`"),
    Control("unit-incomplete", "a unit missing one film job", "states", None, "P5",
            "kept as `unit-incomplete`, and left out of every pair with that device"),
    Control("not-interleaved", "a unit whose devices ran in blocks", "states", None, "P5",
            "kept as `not-interleaved`: \"the difference is the device's-and-its-time's\""),
    Control("kit-dirty", "the kit started from a tree with uncommitted changes, or from an untagged commit",
            "refused", "kit-dirty", "P5", "refused by the kit before any submission: `kit-dirty`"),
    Control("simulator-in-real", "a `simulator` unit that passes its known answer, offered to a comparison declared "
            "real", "refused", "kind-not-qpu", "P3", "refused: `kind-not-qpu`"),
    Control("custody-chain", "a custody-log line edited or dropped after the fact, with a line after it",
            "refused", "custody-chain", "P0",
            "refused: `custody-chain`, at the first line whose predecessor hash fails"),
    Control("withdrawal-in-place", "a withdrawal written by editing the crate's received line, with a line after it",
            "refused", "custody-chain", "P0", "refused: `custody-chain`, at the next line"),
    Control("withdrawal-appended", "a withdrawal written as a later line, with its reason", "accepted", None, "P0",
            "accepted: the chain stays whole"),
    Control("audit-head-mismatch", "an audit record whose log head hash matches no line of the auditor's custody log",
            "refused", "custody-head", "P0", "refused: `custody-head`"),
)
CONTROL = {c.name: c for c in CONTROLS}


# -- P0's plants: each on a fresh copy of the twin ----------------------------------------------------------
def twin(d):
    return fixture.make(Path(d) / "crate")


def _metadata(crate, edit):
    p = Path(crate) / canonical.DESCRIPTOR
    md = json.loads(p.read_bytes())
    edit(md["@graph"])
    p.write_bytes(canonical.dumps(md))
    return crate


def _entity(graph, i):
    return next(e for e in graph if e["@id"] == i)


def _reseal(crate, rel):
    b = (Path(crate) / rel).read_bytes()
    return _metadata(crate, lambda g: _entity(g, rel).update(sha256=hashlib.sha256(b).hexdigest(),
                                                             contentSize=str(len(b))))


RAW = "data/raw.counts.json"


def shot_moved(d):
    crate = twin(d)
    (crate / RAW).write_bytes(canonical.compact({"00": 2, "01": 2, "11": 4}))   # one shot moved, digest left
    return crate


def count_unpaid(d):
    crate = twin(d)
    return _metadata(crate, lambda g: _entity(g, RAW).update({"qro:shots": _entity(g, RAW)["qro:shots"] + 1}))


def float_spelt(d):
    """The file's size, a string of digits, spelt as a JSON float."""
    crate = twin(d)
    return _metadata(crate, lambda g: _entity(g, RAW).update(contentSize=float(_entity(g, RAW)["contentSize"])))


def kind_missing(d):
    crate = twin(d)
    return _metadata(crate, lambda g: g[1].update(keywords="fixture"))


def adjusted_as_raw(d):
    crate = twin(d)
    (crate / RAW).write_bytes(canonical.compact({"00": 2.75, "01": 1, "11": 4}))   # a corrected count
    return _reseal(crate, RAW)


DIGEST_A, DIGEST_B = "a" * 64, "b" * 64


def _log(*events):
    data = b""
    for event, fields in events:
        data += custody.line(data, event, **fields)
    return data


def _received(crate, at, src="withheld"):
    return ("received", {"crate": crate, "at": at, "from": src})


def _record(log):
    head = custody.check_log(log)
    return custody.record(auditor="withheld", checker="qro 0.1.0", checkerCommit="unknown", crate=DIGEST_A,
                          date="2026-10-14", independence="producer-build", logHead=head, signature="none",
                          stages=["crate-only"], trustedTime="none", verdict="accepted")


def custody_chain(d):
    log = _log(_received(DIGEST_A, "2026-10-14T01:00:00Z"), _received(DIGEST_B, "2026-10-14T02:00:00Z"))
    first, rest = log.split(b"\n", 1)
    return first.replace(b"01:00:00", b"01:30:00") + b"\n" + rest, None       # the first line edited after the fact


def withdrawal_in_place(d):
    log = _log(_received(DIGEST_A, "2026-10-14T01:00:00Z"), _received(DIGEST_B, "2026-10-14T02:00:00Z"))
    first, rest = log.split(b"\n", 1)
    obj = json.loads(first)
    edited = {"at": obj["at"], "crate": obj["crate"], "event": "withdrawn", "prev": obj["prev"],
              "reason": "it carried an identifier rule 3 forbids"}
    return canonical.compact(edited) + rest, None


def withdrawal_appended(d):
    log = _log(_received(DIGEST_A, "2026-10-14T01:00:00Z"), _received(DIGEST_B, "2026-10-14T02:00:00Z"),
               ("withdrawn", {"crate": DIGEST_A, "at": "2026-10-14T03:00:00Z",
                              "reason": "it carried an identifier rule 3 forbids"}))
    return log, _record(log)


def audit_head_mismatch(d):
    log = _log(_received(DIGEST_A, "2026-10-14T01:00:00Z"))
    rec = json.loads(_record(log))
    rec["logHead"] = hashlib.sha256(b"a line this log never held\n").hexdigest()
    return log, canonical.dumps(rec)


PLANTS = {
    "shot-moved": shot_moved,
    "count-unpaid": count_unpaid,
    "float-spelt": float_spelt,
    "kind-missing": kind_missing,
    "adjusted-as-raw": adjusted_as_raw,
    "custody-chain": custody_chain,
    "withdrawal-in-place": withdrawal_in_place,
    "withdrawal-appended": withdrawal_appended,
    "audit-head-mismatch": audit_head_mismatch,
}


class PlantClash(RuntimeError):
    """A name two modules plant: the definitions contradict themselves. Its own class, so that the generator
    answers it alone as a contradiction, and any other failure as its own (P0.2's verifier, round 1, D1)."""


def merged(plants, modules):
    """P0's plants, and each parcel module's PLANTS dict. A name planted twice is refused, never overwritten."""
    out = dict(plants)
    for module in modules:
        clash = sorted(set(module.PLANTS) & set(out))
        if clash:
            raise PlantClash(f"{module.__name__} plants {clash}, which another module already plants")
        out.update(module.PLANTS)
    return out


def plants():
    """Every plant: P0's, then each parcel module's, plants_*.py beside this file in name order, merged now."""
    return merged(PLANTS, [importlib.import_module(f"controls.{p.stem}")
                           for p in sorted(Path(__file__).parent.glob("plants_*.py"))])
