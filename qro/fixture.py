"""P0's fixture crate: the smallest crate that every one of P0's steps reads, with its own raw form and generator.

The controls under controls/ plant one fault each in it (study QRO-0, section 11), and the fixture itself is
their twin, which must be accepted. register() adds its raw form and generator to the checker. The command line
calls it only with --fixtures, and the controls and the tests call it in process; so a real crate that names them
is refused `step-unbuilt` by the command line run without --fixtures.

Its records are files under data/. A file ending .counts.json is a raw result in the fixture's raw form: one
canonical JSON line, an object from bitstrings, all of one length, to non-negative integer counts, whose shots
are the counts' sum. Stdlib only.
"""
import hashlib
import json
import re
from pathlib import Path

from qro import canonical, checker
from qro import vocabulary as V

RAW_FORM = "qro-fixture-counts"
GENERATOR = "qro-fixture"
HEADER = {"datePublished": "2026-10-14", "qro:writer": "qro 0.1.0, fixture", "qro:writtenAt": "2026-10-14T00:00:00Z",
          "qro:signature": "none", "qro:trustedTime": "none"}


def _no_constant(name):
    raise ValueError(f"{name} has no spelling")


def read_counts(data):
    try:
        obj = json.loads(data.decode("ascii"), parse_constant=_no_constant)
        line = canonical.compact(obj)
    except (UnicodeDecodeError, ValueError, TypeError, RecursionError):
        raise checker.RawFormError("not JSON in ASCII, with a spelling for every value") from None
    if not isinstance(obj, dict) or not obj:
        raise checker.RawFormError("an object of one outcome or more")
    if line != data:
        raise checker.RawFormError("not its one canonical line")
    width = len(next(iter(obj)))
    for k, v in obj.items():
        if not re.fullmatch("[01]+", k, re.ASCII) or len(k) != width:
            raise checker.RawFormError(f"{k!r} is not a bitstring of the first one's length")
        if type(v) is not int or v < 0:
            raise checker.RawFormError(f"the count of {k} is not a non-negative integer")
    return sum(obj.values())


def generate(crate):
    """The fixture's metadata, generated from its records, with the fixture's header."""
    crate = Path(crate)
    paths = sorted(p.relative_to(crate).as_posix() for p in crate.rglob("*")
                   if p.is_file() and p.name != canonical.DESCRIPTOR)
    graph = [V.descriptor(),
             dict({"@id": canonical.ROOT, "@type": "Dataset", "name": "QRO-Crate P0 fixture",
                   "description": "The smallest crate every one of P0's checker steps reads — the controls' "
                                  "twin.",
                   "conformsTo": [{"@id": V.PROCESS_RUN_CRATE}, {"@id": V.PROFILE}],
                   "license": {"@id": "https://creativecommons.org/licenses/by/4.0/"},
                   "hasPart": [{"@id": p} for p in paths], "qro:generator": GENERATOR}, **HEADER)]
    for p in paths:
        b = crate.joinpath(*p.split("/")).read_bytes()
        e = {"@id": p, "@type": "File", "sha256": hashlib.sha256(b).hexdigest(), "contentSize": str(len(b)),
             "encodingFormat": "application/json" if p.endswith(".json") else "text/plain"}
        if p.endswith(".counts.json"):
            e["@type"] = ["File", "qro:RawResult"]
            e["qro:rawForm"] = RAW_FORM
            try:
                e["qro:shots"] = read_counts(b)
            except checker.RawFormError:
                pass
        graph.append(e)
    graph[2:] = sorted(graph[2:] + V.profile_entities(), key=lambda e: e["@id"])   # P0.3: P4's design, R3
    return {"@context": V.context(), "@graph": graph}


def with_entity(md, entity):
    """The metadata with `entity` added in the graph's @id order: a test's carrier of a parcel's term, an entity
    of the type the term's domain admits (P0.3: a term narrowed to its type is refused anywhere else, at step 1)."""
    graph = md["@graph"]
    md["@graph"] = graph[:2] + sorted(graph[2:] + [entity], key=lambda e: e["@id"])
    return md


def register():
    checker.RAW_FORMS[RAW_FORM] = read_counts
    checker.GENERATORS[GENERATOR] = generate


def make(crate, counts=None, notes="QRO-Crate's P0 fixture: one raw result and one note.\n"):
    """Write a fixture crate into an empty directory: its records, then its generated metadata."""
    crate = Path(crate)
    records = crate / "data"
    records.mkdir(parents=True)
    (records / "raw.counts.json").write_bytes(canonical.compact(counts or {"00": 3, "01": 1, "11": 4}))
    (records / "notes.txt").write_bytes(notes.encode("ascii"))
    (crate / canonical.DESCRIPTOR).write_bytes(canonical.write(generate(crate)))
    return crate
