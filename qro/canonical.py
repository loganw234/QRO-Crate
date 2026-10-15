"""Canonical bytes (study QRO-0, section 9 and rule 4): the one byte string a crate's metadata has, its body, and
its digest, which is the crate's identity.

The metadata's one spelling, for a second implementation to match:
  - JSON in ASCII: every code point below U+0020 or above U+007E escaped as \\u and four lowercase hex digits
    (a surrogate pair above U+FFFF), except \\b \\f \\n \\r \\t; `"` and `\\` as \\" and \\\\; nothing else escaped;
  - object keys sorted by code point; each member and each item on its own line, indented two spaces a level,
    a comma ending every line but a container's last; ": " after a key; empty objects and lists as {} and [];
    LF line ends and a final LF;
  - no number but a non-negative integer, in decimal with no leading zero; no true, false or null;
  - the graph in its order: the descriptor, the root, then every other entity by @id, which is printable ASCII
    with no space, so the order is byte order;
  - a list-valued term's values sorted, references by @id, and each value once.
That is what Python 3.12's json.dumps(obj, ensure_ascii=True, sort_keys=True, indent=2, separators=(",", ": "))
writes, plus a final LF. Stdlib only.
"""
import hashlib
import json

from qro import vocabulary as V

DESCRIPTOR = "ro-crate-metadata.json"
ROOT = "./"


def dumps(obj):
    """The canonical bytes of a JSON value."""
    return (json.dumps(obj, ensure_ascii=True, sort_keys=True, indent=2, separators=(",", ": "),
                       allow_nan=False) + "\n").encode("ascii")


def compact(obj):
    """The canonical bytes of one JSON line: a custody-log line (section 9.2)."""
    return (json.dumps(obj, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n").encode("ascii")


def sort_key(value):
    return value["@id"] if isinstance(value, dict) else value


def types(entity):
    t = entity.get("@type")
    return [t] if isinstance(t, str) else list(t) if isinstance(t, list) else []


def arrange(metadata):
    """The metadata in its one order: the graph ordered, every list-valued term's values sorted, one type a
    string. The writer arranges; the reader refuses what is not arranged."""
    graph = []
    for e in metadata["@graph"]:
        e = dict(e)
        for k, v in e.items():
            t = V.TERM.get(k)
            if t is not None and t.many and isinstance(v, list):
                e[k] = sorted(v, key=sort_key)
        if isinstance(e.get("@type"), list):
            e["@type"] = e["@type"][0] if len(e["@type"]) == 1 else sorted(e["@type"])
        graph.append(e)
    head = [e for e in graph if e.get("@id") == DESCRIPTOR] + [e for e in graph if e.get("@id") == ROOT]
    rest = sorted((e for e in graph if e.get("@id") not in (DESCRIPTOR, ROOT)), key=lambda e: e["@id"])
    return {"@context": metadata["@context"], "@graph": head + rest}


def body(metadata):
    """The metadata arranged, with every header term removed (rule 4): what two writers of one crate must make
    alike, whatever order either wrote it in."""
    md = arrange(metadata)
    return {"@context": md["@context"],
            "@graph": [{k: v for k, v in e.items() if k not in V.HEADER_KEYS} for e in md["@graph"]]}


def body_digest(metadata):
    """A crate's identity: the SHA-256 of its metadata's body, in canonical bytes (section 9.2)."""
    return hashlib.sha256(dumps(body(metadata))).hexdigest()


def write(metadata):
    """The metadata's canonical bytes, held to the strict reader before they are returned: the writer never
    writes what the reader refuses."""
    from qro import reader
    data = dumps(arrange(metadata))
    reader.read(data)
    return data


def first_difference(a, b):
    """Where two byte strings first differ, as "line L column C" of the first."""
    n = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    nl = b"\n"
    return f"line {a.count(nl, 0, n) + 1} column {n - a.rfind(nl, 0, n)}"
