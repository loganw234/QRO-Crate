"""The sweeps that hold the shapes' claims (P4's verifier, round 1, defects 1 and 2): crates one edit away from the fixture,
each judged by steps 1 to 3 of the checker and by the evaluator.

  A. a must shape fails while steps 1 to 3 accept the crate: a shape stricter than the checker;
  B. a must shape fails and the checker's refusal is not claimed by any shape that fails: a claim that is not true.

The pool of edits and the alias-key crates are the first verifier's (its singleedits.py and aliaskeys.py, in the report of
2026-10-16), kept as the verifier wrote them so that a change of the pool is a change that shows. The three families are the
second verifier's (its report of 2026-10-26, defect 1; the lead's ruling of 2026-10-26T11:18:27Z, defect 2): crates it found
with a must shape failing where the checker refuses by a name the claims did not hold, which the pool never made, because it
deletes, sets, retypes and renames what the fixture has and adds no entity under an old @id, no File and no top-level key:
  1. `duplicates`: an @id that the graph already has, added again with a term of its own (RDF merges the nodes, so a single-valued
     term has two values), and the paths the reader holds as another's (a case clash, a file and a directory): `graph-form`;
  2. `contexts`: each of the verifier's variants of the top-level @context, and the top-level keys (`@reverse` among them):
     the evaluator abstains from these and a real engine reads them its own way (`context`, `graph-form`);
  3. `added_files`: a File entity added, listed in the root or not, with and without a digest and a size, with its file on
     disk or not, and at the path of a link: step 2 refuses what the disk lacks before the digest and the listing
     (`file-missing`), and its walk refuses a link before it looks at any entity's file, after step 1 has read the
     metadata (`file-link`).
Nothing here is a test: pytest's naming decides what is one, and a helper under tests/ names no function `test*` and no
class `Test*` (CLAUDE.md). The tests that call it: tests/p4/test_p4_sweeps.py (every 6th edit, the 21 classes of the report
and five edits of P4's own, the alias crates), tests/p4/test_p4_families.py (the three families) and
tests/p4shacl/test_p4shacl_sweeps.py (every edit; the alias crates and the families through a real engine).

Cost, MEASURED on one host beside other work: 12,591 edits 12 s; every 6th 2 s; the 124 alias crates 0.2 s (3 s for the
whole test file); the families, 469 crates, 1.3 s (6 s for tests/p4/test_p4_families.py, its link crates and its staged copies
of the crate among them), and 213 of them through pyshacl 23 s (50 s for all 469).
"""
import copy
import hashlib
import itertools
import json
import os

from p4_helpers import early_verdict
from qro import canonical
from qro import p4_examples as X
from qro import p4_expand as E
from qro import p4_shapes as H
from qro import vocabulary as V

VALUES = ["", " x", "x ", "x\n", "none", "unknown", "x", "0", "1", "a" * 64, "a" * 40, "2026-10-14", "1/2", 0, 1, -1, 9, True,
          ["x"], [], ["a", "b"], {"@id": "#nowhere"}, {"@id": "data/notes.txt"}, {"@id": "data/raw.counts.json"},
          {"@id": "https://example.org/x"}, {"@id": "./"}, {"@id": "ro-crate-metadata.json"}, {"@id": "x y"},
          [{"@id": "data/notes.txt"}], [{"@id": "https://example.org/x"}, {"@id": "data/notes.txt"}]]
KEYS = [t.key for t in V.TERMS] + ["schema:name", "madeUp", "keywords", "dct:conformsTo", "@context"]
IDS = ["#x", "data/x", "x", "data/", "schema:x", "urn:x:y", "./x", "x/", "DATA/notes.txt", "data/NOTES.txt", "data/notes.txt/", "a b",
       "ro-crate-metadata.json/"]
TYPES = ["File", "Dataset", "CreativeWork", "Profile", "CreateAction", "qro:RawResult", "qro:Job", "Person", "MediaObject",
         ["File", "qro:RawResult"], ["CreativeWork", "Profile"], ["Dataset", "File"], "foo", "schema:Dataset"]


def edits(base):
    """[(name, apply)] for every single edit of the metadata `base` the pool makes, in a fixed order: delete a key; delete an
    entity; set each key to each value; add each key to each entity; retype; rename an @id."""
    g = base["@graph"]
    out = []
    for i, e in enumerate(g):
        for k in list(e):
            if k in ("@id",):
                continue
            out.append((f"del {e['@id']}.{k}", (lambda md, i=i, k=k: md["@graph"][i].pop(k))))
        if i >= 2:
            out.append((f"del-entity {e['@id']}", (lambda md, i=i: md["@graph"].pop(i))))
        for k in KEYS + [k for k in e if k not in KEYS and k != "@id"]:
            if k == "@id":
                continue
            for v in VALUES:
                out.append((f"set {e['@id']}.{k}={json.dumps(v)[:30]}",
                            (lambda md, i=i, k=k, v=v: md["@graph"][i].__setitem__(k, copy.deepcopy(v)))))
        for t in TYPES:
            out.append((f"type {e['@id']}={json.dumps(t)}", (lambda md, i=i, t=t: md["@graph"][i].__setitem__("@type", t))))
        if i >= 2:
            for new in IDS:
                out.append((f"id {e['@id']}->{new}", (lambda md, i=i, new=new: md["@graph"][i].__setitem__("@id", new))))
    return out


def early(work, md, files=None):
    """The checker's verdict on `md` at steps 1 to 3, in the fixture's crate (or, where `files(crate)` changes the crate's
    files, in a copy of it): a refusal's name, "ok", or "unwritable"."""
    try:
        data = canonical.dumps(md)
    except (ValueError, TypeError, RecursionError):
        return "unwritable"
    if files is None:
        return early_verdict(work.crate, data)
    with work.staged(md, files) as crate:
        return early_verdict(crate, data)


def claims_of(shapes):
    return {X.local(s.id): s.claims for s in shapes}


def judge(work, shapes, md, claims, files=None):
    """('unreadable' | 'U' | 'conforms' | 'A' | 'B' | 'held', checker's early verdict, the must shapes that fail) for `md`.
    A crate the expansion refuses to read is never skipped: it is 'unreadable' when steps 1 to 3 refuse it too, and 'U'
    when they accept it (the evaluator abstains from a crate the checker holds fine: P4's verifier, round 1, defect 1)."""
    must, _, why = X.shapes_verdict(md, shapes)
    if why:
        e = early(work, md, files)
        return ("U" if e == "ok" else "unreadable"), e, ()
    if not must:
        return "conforms", None, ()
    e = early(work, md, files)
    if e == "ok":
        return "A", e, must
    if e not in {c for s in must for c in claims[s]}:
        return "B", e, must
    return "held", e, must


def crate_of(base, apply):
    """`base` with `apply` done to a copy of it and the graph in the writer's order, or None where the edit does not fit
    (an index or a key the metadata lacks, an @graph that is no list)."""
    md = copy.deepcopy(base)
    try:
        apply(md)
        return X.arranged(md)
    except (IndexError, KeyError, TypeError):
        return None


def sweep(work, shapes, stride=1, offset=0, only=None, pool=None):
    """The edits of `pool(base)` (the first verifier's `edits` by default) with index = offset (mod stride), or those whose
    names `only` lists, judged. An entry is (name, apply) or (name, apply, files): `files(crate)` changes the crate's files.
    Returns {"n": judged, "unreadable": n the expansion cannot read and steps 1 to 3 refuse, "U": [names the expansion cannot
    read and steps 1 to 3 accept], "A": [(name, must)], "B": {(refusal, must): [names]}, "held": n, "failing": {shapes that
    failed}}."""
    claims = claims_of(shapes)
    base = work.pristine
    out = {"n": 0, "unreadable": 0, "U": [], "A": [], "B": {}, "held": 0, "failing": set()}
    for k, (name, apply, *rest) in enumerate((pool or edits)(base)):
        if only is not None:
            if name not in only:
                continue
        elif k % stride != offset:
            continue
        md = crate_of(base, apply)
        if md is None:
            continue
        out["n"] += 1
        kind, e, must = judge(work, shapes, md, claims, rest[0] if rest else None)
        if kind == "unreadable":
            out["unreadable"] += 1
        elif kind == "U":
            out["U"].append(name)
        elif kind == "A":
            out["A"].append((name, must))
        elif kind == "B":
            out["B"].setdefault((e, must), []).append(name)
        elif kind == "held":
            out["held"] += 1
            out["failing"].update(must)
    return out


# -- the 21 classes the verifier's sweep found (its report, defect 2): two edits of each, by name ---------------------------------
CLASSES = (
    'set ./.schema:name=""', 'set ./.schema:name=" x"',
    'set data/notes.txt.dct:conformsTo=""', 'set data/notes.txt.dct:conformsTo=" x"',
    'set ./.dct:conformsTo=""', 'set ./.dct:conformsTo=" x"',
    'set data/notes.txt.dct:conformsTo={"@id": "#nowhere"}', 'set data/notes.txt.dct:conformsTo={"@id": "data/notes.txt"}',
    'set ./.hasPart={"@id": "#nowhere"}', 'id data/notes.txt->#x',
    'set ./.hasPart={"@id": "data/notes.txt"}', 'set ./.hasPart={"@id": "data/raw.counts.json"',       # the name cuts at 30
    'set ./.license=[]', 'set ./.name=[]',
    'set ./.dct:conformsTo={"@id": "#nowhere"}', 'set ./.dct:conformsTo={"@id": "data/notes.txt"}',
    'type ./=["Dataset", "File"]', 'set data/notes.txt.sha256=[]',
    'set ro-crate-metadata.json.@type=["x"]', 'set ro-crate-metadata.json.@type=[]',
    'set ./.@type=["x"]', 'set ./.@type=[]',
    'set data/notes.txt.@type=["x"]', 'set data/notes.txt.@type=[]',
    'set data/raw.counts.json.@type=["x"]', 'set data/raw.counts.json.@type=[]',
    'set ./.hasPart=[]', 'type ./="File"', 'type ./=["File", "qro:RawResult"]',
    'type data/notes.txt="schema:Dataset"', 'set data/raw.counts.json.qro:rawForm=[]',
    'type data/raw.counts.json="MediaObject"', 'type data/raw.counts.json="schema:Dataset"',
    'set https://github.com/loganw234/QRO-Crate/blob/main/profile/README.md.@type=["x"]',
    'set https://github.com/loganw234/QRO-Crate/blob/main/profile/README.md.@type=[]',
)

# -- five more, P4's own: the edits of the pool that alone notice a claim, which the 21 classes and a sample of the pool leave
# unseen. Found by taking each claim of each must shape away in turn and asking which edits of the 12,591 and which of the
# 124 alias crates then have a refusal no failing shape claims: 3 of the 336 claims are seen by these and not by the sample.
MORE = (
    'set ./.hasPart=[{"@id": "data/notes.txt"}]',                                       # file-reached: file-unlisted
    'del data/notes.txt.contentSize', 'del data/notes.txt.sha256',                      # file-digest-present: file-digest
    'del data/raw.counts.json.contentSize', 'del data/raw.counts.json.sha256',          # file-digest-present: raw-digest
)


# -- the second verifier's three families (the head of this module says what each is) ---------------------------------------------
HELLO = b"hello" + bytes([10])


def add_entity(entity):
    return lambda md: md["@graph"].append(copy.deepcopy(entity))


def listed(ref_id):
    """The root's hasPart with one more reference, in the order the writer makes."""
    def run(md):
        root = md["@graph"][1]
        root["hasPart"] = sorted(root["hasPart"] + [{"@id": ref_id}], key=lambda r: r["@id"])
    return run


def both(*changes):
    def run(md):
        for change in changes:
            change(md)
    return run


# Paths the reader holds as one though RDF holds them as two (a case clash), or as a file and its own directory.
CLASHES = (
    ("case clash of a File", {"@id": "data/NOTES.txt", "@type": "File"}),
    ("case clash of a directory", {"@id": "DATA/notes.txt", "@type": "File"}),
    ("case clash of a CreativeWork", {"@id": "data/NOTES.txt", "@type": "CreativeWork", "name": "x"}),
    ("a File where a directory is", {"@id": "data", "@type": "File"}),
)


def duplicates(base):
    """Family 1: each @id of `base` added again, bare and with each term of the table in a valid value of its own (the second
    verifier's e5_dupid.py), and the paths of CLASHES (its f4_dupid.py)."""
    out = []
    for e in base["@graph"]:
        out.append((f"again {e['@id']}", add_entity({"@id": e["@id"], "@type": e["@type"]})))
        for t in V.TERMS:
            out.append((f"again {e['@id']} + {t.key}",
                        add_entity({"@id": e["@id"], "@type": e["@type"], t.key: X.valid_value(t)})))
    return out + [(name, add_entity(entity)) for name, entity in CLASHES]


def context_variants():
    """The second verifier's eight variants of the top-level @context (its f2_context.py). Each begins with RO-Crate's URL,
    as a real engine's runner keeps what follows it: the crate's own definitions."""
    url, ns = V.ROCRATE_CONTEXT, V.NAMESPACE
    return {
        "redefines name": [url, {V.PREFIX: ns, "name": "http://example.org/n"}],
        "sets @vocab": [url, {V.PREFIX: ns}, {"@vocab": "http://example.org/"}],
        "points qro elsewhere": [url, {V.PREFIX: "http://example.org/q#"}],
        "has no qro prefix": [url],
        "defines a term nobody uses": [url, {V.PREFIX: ns}, {"extra": "http://example.org/e"}],
        "redefines hasPart": [url, {V.PREFIX: ns, "hasPart": "http://example.org/hp"}],
        "redefines sha256": [url, {V.PREFIX: ns, "sha256": "http://example.org/sha"}],
        "redefines File": [url, {V.PREFIX: ns, "File": "http://example.org/F"}],
    }


# Keys at the top level of the metadata, beside @context and @graph (its f3_toplevel.py): the reader refuses them `graph-form`.
TOP_LEVEL = {"a name": {"name": "x"}, "a type": {"@type": "CreativeWork"}, "an @id": {"@id": "https://example.org/g"},
             "an @id and a name": {"@id": "https://example.org/g", "name": "x"},
             "an @reverse": {"@reverse": {"name": {"@id": "./"}}}}


def contexts(base):
    """Family 2: the variants of the @context, and the top-level keys."""
    out = [(f"context {label}", (lambda md, c=c: md.__setitem__("@context", copy.deepcopy(c))))
           for label, c in context_variants().items()]
    return out + [(f"top level {label}", (lambda md, kw=kw: md.update(copy.deepcopy(kw)))) for label, kw in TOP_LEVEL.items()]


def write_file(rel, data=HELLO):
    def run(crate):
        path = crate.joinpath(*rel.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return run


def link_dir(path, target):
    """A directory link: a junction on Windows, which needs no privilege; a symbolic link elsewhere (the way tests/format/
    test_hostile.py makes one). No skip: the runner fails a stage that skips a test."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(path))
    else:
        os.symlink(target, path, target_is_directory=True)


def link_at(rel):
    """`files` for a crate: a link at `rel`, to a directory outside the crate."""
    def run(crate):
        outside = crate.parent / "outside"
        outside.mkdir(exist_ok=True)
        link_dir(crate.joinpath(*rel.split("/")), outside)
    return run


LINK = "data/jct"


def added_files(base):
    """Family 3: a File entity added at a path the crate does not have, with and without a digest and a size, listed in the
    root or not, with its file on disk or not (the second verifier's f1_filemissing.py and e3_additions.py), as a File and as a
    raw result; and a File at the path of a link, where the host can make one."""
    digest, size = hashlib.sha256(HELLO).hexdigest(), str(len(HELLO))
    out = []
    for ident, typ, has_digest, has_size, in_root, on_disk in itertools.product(
            ("x.txt", "data/x.txt"), ("File", ["File", "qro:RawResult"]), (False, True), (False, True), (False, True), (False, True)):
        entity = {"@id": ident, "@type": copy.deepcopy(typ), **({"sha256": digest} if has_digest else {}),
                  **({"contentSize": size} if has_size else {})}
        edit = both(add_entity(entity), listed(ident)) if in_root else add_entity(entity)
        label = (f"added {json.dumps(typ)} {ident}{' with a digest' if has_digest else ''}{' with a size' if has_size else ''}"
                 f"{', listed' if in_root else ''}{', on disk' if on_disk else ''}")
        out.append((label, edit, write_file(ident) if on_disk else None))
    for has_digest, in_root in itertools.product((False, True), (False, True)):
        entity = {"@id": LINK, "@type": "File", **({"sha256": digest, "contentSize": size} if has_digest else {})}
        edit = both(add_entity(entity), listed(LINK)) if in_root else add_entity(entity)
        out.append((f"added File at a link {LINK}{' with a digest and a size' if has_digest else ''}{', listed' if in_root else ''}",
                    edit, link_at(LINK)))
    return out


def families(base):
    """The second verifier's three families, in this order: (name, apply, files), where `files(crate)` changes the crate's
    files or is None."""
    return [(name, apply, files[0] if files else None) for name, apply, *files in duplicates(base) + contexts(base) + added_files(base)]


# -- the alias-key crates -----------------------------------------------------------------------------------------------------
def prefixes_by_base():
    """{IRI base: the prefix RO-Crate's context gives it}."""
    return {v: k for k, v in E.context().items() if v and v[-1] in ":/?#[]@"}


def alias_of(key):
    """The key spelt another way for the same predicate: a compact IRI of RO-Crate's context, else the absolute IRI."""
    iri = H.term_iri(key)
    for base, prefix in sorted(prefixes_by_base().items(), key=lambda kv: -len(kv[0])):
        if iri.startswith(base) and iri != base:
            return f"{prefix}:{iri[len(base):]}"
    return iri


def alias_crates(work):
    """{name: (term, alias, metadata)}: for every term but `about`, its alias key with a valid value (a) on the host its
    domain admits, which already carries the term where the host does, and (b) on a CreativeWork."""
    out = {}
    for t in V.TERMS:
        if t.key == "about":
            continue
        a = alias_of(t.key)
        md = work.fresh()
        host = X.host_for(t.domain[0], md["@graph"], "#alias-host")
        host[a] = X.valid_value(t)
        out[f"a:{t.key}"] = (t, a, X.arranged(md))
        md = work.fresh()
        md["@graph"].append({"@id": "#alias-host", "@type": "CreativeWork", a: X.valid_value(t)})
        out[f"b:{t.key}"] = (t, a, X.arranged(md))
    return out


def alias_problems(work, shapes):
    """[problem]: an alias crate the checker accepts at steps 1 to 3, or on which a must shape fails and no failing shape
    claims the checker's refusal."""
    claims = claims_of(shapes)
    out = []
    for name, (t, a, md) in alias_crates(work).items():
        e = early(work, md)
        must, _, why = X.shapes_verdict(md, shapes)
        if e == "ok":
            out.append(f"{name}: the checker accepts {a}")
        if why:
            out.append(f"{name}: the expansion cannot read it: {why}")
        elif must and e not in {c for s in must for c in claims[s]}:
            out.append(f"{name}: {a} is refused {e}, and {list(must)} fail and claim {sorted({c for s in must for c in claims[s]})}")
    return out
