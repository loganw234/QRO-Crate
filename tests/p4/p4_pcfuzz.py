"""A fuzz of the Profile Crate check (qro/p4_profile.py, `check_profile_crate`): random edits of the Profile Crate's
metadata and of the files beside it go into the check, which must return a list of problems and raise on none, and must
never need its safety net (the net's problem, `P.NET`, is a bug of the check, not a verdict).

The model is the verifier's pcfuzz.py (P4's verifier, round 1, defect 3), which found that 2,724 of 20,000 edits made the
check raise, and `tools/gen_profile.py --check` then answer exit 3 for a Profile Crate that was only misshapen. Nothing
here is a test: pytest's naming decides what is one, and a helper under tests/ names no function `test*` and no class
`Test*` (CLAUDE.md). The tests that call it are in test_p4_profile_crate.py (a few thousand edits, in the quick stage)
and in tests/p4shacl/test_p4shacl_sweeps.py (20,000, where the cost fits).
"""
import collections
import copy
import json
import random

from qro import canonical
from qro import p4_profile as P

VALUES = [None, True, False, 0, 1, -1, 1.5, "", "x", " ", [], {}, [None], [[]], {"@id": None}, {"@id": 5}, {"@id": ""},
          {"@id": "x"}, {"@id": "x", "name": "y"}, [{"@id": "x"}, 5], {"@id": "https://w3id.org/ro/crate/1.3"},
          {"@id": "README.md"}, [{"@id": "README.md"}, {"@id": "README.md"}], "File", ["File"], ["File", 5], {"a": 1},
          "2026-10-16", chr(0xE9), "text/html", "application/ld+json", {"@id": P.CONTEXT_IRI}, {"@id": P.JSONLD_CONTEXT}]
KEYS = ["@id", "@type", "hasPart", "hasResource", "hasRole", "hasArtifact", "about", "conformsTo", "isProfileOf", "license",
        "encodingFormat", "sha256", "contentSize", "name", "description", "version", "datePublished", "inDefinedTermSet",
        "sameAs", "termCode"]
RAW = [b"", b"null", b"[]", b"{}", b"1", b'"x"', b"\xff\xfe", b"{", b'{"@graph": []}', b'{"@context": 5, "@graph": 5}',
       b"[" * 100000 + b"]" * 100000, b'{"a":' * 50000 + b"1" + b"}" * 50000,
       None, 5, "text, not bytes", ["x"], {"@graph": []}]                                  # and what is no bytes at all


def value(rnd):
    """A fresh copy of a random value: the pool's own are never handed out, or an edit would change the next one's."""
    return copy.deepcopy(rnd.choice(VALUES))


def edit_graph(md, rnd):
    """One random edit of the parsed metadata `md`, in place."""
    g = md["@graph"] if isinstance(md.get("@graph"), list) else None
    e = rnd.choice(g) if g else None
    op = rnd.random()
    if op < 0.40 and isinstance(e, dict) and e:
        e[rnd.choice(list(e))] = value(rnd)
    elif op < 0.52 and isinstance(e, dict) and e:
        del e[rnd.choice(list(e))]
    elif op < 0.60 and g:
        g.remove(e)
    elif op < 0.68 and g is not None:
        g.append(value(rnd))
    elif op < 0.80 and isinstance(e, dict):
        e[rnd.choice(KEYS)] = value(rnd)
    elif op < 0.85 and g and isinstance(e, dict):
        g.append(dict(e))                                              # an entity twice
    elif op < 0.90 and g and isinstance(e, dict):
        other = rnd.choice(g)
        e["@id"] = other.get("@id") if isinstance(other, dict) else None                    # an id that is another's
    elif op < 0.93 and g:
        rnd.shuffle(g)
    else:
        md[rnd.choice(["@context", "@graph", "x"])] = value(rnd)


def edit_files(data, rnd):
    """One random edit of the files beside the metadata, in place."""
    others = sorted(k for k in data if k != canonical.DESCRIPTOR)
    op = rnd.random()
    if op < 0.4 and others:
        data[rnd.choice(others)] = rnd.choice([b"", b"x", b"changed\n"])
    elif op < 0.6 and others:
        del data[rnd.choice(others)]
    elif op < 0.75:
        data["extra/file.txt"] = b"an extra file\n"
    elif op < 0.85:
        data[rnd.choice([5, None, b"extra", ("a", "b")])] = b"a file whose path is no string\n"
    elif others:
        data[rnd.choice(others)] = "text, not bytes"


def run(n, seed=9, files=None, context=None):
    """Feed `n` random edits to the check. Returns a dict: `raised` (type: text, first few, of the edits that made it
    raise), `net` (how many made it need its safety net), `not_problems` (how many answers were no list of strings),
    `clean` (how many edits left no problem), `refused` (how many were refused by a problem), and what it did: `raw` values
    for the metadata (byte strings, and a few that are no bytes), `files` edits of the files beside it, `edited` edits of the
    parsed metadata. An answer is a problem list when it is a list of strings, each once."""
    rnd = random.Random(seed)
    files = P.render() if files is None else files
    context = P.read_context() if context is None else context
    text = files[canonical.DESCRIPTOR].decode("ascii")
    raised = collections.Counter()
    out = {"n": n, "net": 0, "not_problems": 0, "clean": 0, "refused": 0, "raw": 0, "files": 0, "edited": 0}
    for _ in range(n):
        data = dict(files)
        r = rnd.random()
        if r < 0.03:
            data[canonical.DESCRIPTOR] = rnd.choice(RAW)
            out["raw"] += 1
        else:
            md = json.loads(text)
            for _ in range(rnd.randint(1, 3)):
                edit_graph(md, rnd)
                out["edited"] += 1
            data[canonical.DESCRIPTOR] = json.dumps(md).encode("ascii", "replace")
            if r < 0.15:
                edit_files(data, rnd)
                out["files"] += 1
        try:
            found = P.check_profile_crate(data, context)
        except Exception as x:                                  # the point of the fuzz: nothing may escape
            raised[f"{type(x).__name__}: {str(x)[:60]}"] += 1
            continue
        if not (isinstance(found, list) and all(isinstance(p, str) for p in found) and len(found) == len(set(found))):
            out["not_problems"] += 1
        elif any(P.NET in p for p in found):
            out["net"] += 1
        out["refused" if found else "clean"] += 1
    out["raised"] = dict(raised)
    return out
