"""The strict reader: checker step 1 (study QRO-0, sections 9 and 10).

It takes the metadata's bytes, and returns them parsed, or refuses at the first failure, by name and location,
in this order (cft-fp256's strict reader, docs/CERTIFICATES.md:852-899, READ, adapted to JSON-LD):
  1. the bytes are the canonical bytes of what they parse to (qro/canonical.py): ASCII, no key twice in an
     object, no NaN or infinity, no number past the parser's reach, no nesting past its depth: `spelling`;
  2. the top level holds @context and @graph only: `graph-form`;
  3. the @context is this profile version's: `context`;
  4. @graph is a list of entities, each with an @id and an @type in their spellings (`spelling`); a file's @id is
     its path in the crate, in the path spelling (`spelling`); no @id twice, no two paths, a file's directories
     and the descriptor among them, whose names differ only by case, nor a path both a file and a directory,
     the graph in its order, the descriptor and the root as this profile states them, the root a Dataset and
     never an action, the root carrying every term it must, each profile the root conformsTo having its contextual
     entity as the table states it (one declaring another version, as text, is `context`: this reader reads one
     version of each, P0.3), the root mentioning every action, and every reference to a relative @id naming an
     entity: `graph-form`. A reference whose @id is not in the `iri` spelling is relative, so one that only looks
     like an IRI (`http:`, a space or a control character in it) names no entity, and is `graph-form` too;
  5. every key is a term: `term-unknown` if neither the vocabulary nor RO-Crate 1.3's context names it,
     `field-kind` if RO-Crate's context defines it but the vocabulary gives it no kind; every type is listed:
     `term-unknown`; and every term stands on an entity its domain admits: `graph-form`;
  6. every value is in its term's one spelling, or is an absence word its term allows; a list-valued term holds
     a sorted list of distinct values, and a single-valued one never a list: `spelling`.
Hostile bytes are refused by name, never crash it (P0's verifier, P0-2). Stdlib only.
"""
import json
from functools import lru_cache

from qro import canonical, spelling
from qro import vocabulary as V
from qro.refusal import Refused


class _Twice(Exception):
    pass


def _pairs(pairs):
    seen = set()
    for k, _ in pairs:
        if k in seen:
            raise _Twice(k)
        seen.add(k)
    return dict(pairs)


def _constant(name):
    raise _Twice(name)


@lru_cache(maxsize=1)
def rocrate_terms():
    """The keys RO-Crate 1.3's context defines, from the copy whose digest the vocabulary pins (V.rocrate_context,
    which reads it, P0.7)."""
    return frozenset(V.rocrate_context())


def absolute(ref_id):
    """An absolute IRI, as against a path in the crate or a fragment: the `iri` spelling exactly, qro/spelling.py's
    IRI, so the reader and the spelling have one meaning of it (P0's verifier, round 4). Its scheme is two
    characters or more with no dot, then ':' and something after it. So a drive letter (`C:/x`), a stream on a name
    with a dot (`notes.txt:hidden`) and a bare scheme (`http:`) stay paths, and a file's path holds no ':' (round 2).
    A stated limit (round 3): a stream on a top-level name that is itself a lowercase scheme (`readme:hidden`) reads
    as an IRI; since P0.5 one in another case (`README:hidden`) is refused as an @id (FORMAT.md items 11 and 22). It
    is then no file the crate holds, so no digest stands on it and no step reads its bytes."""
    return spelling.IRI.fullmatch(ref_id) is not None


def local_file(entity):
    """A File the crate holds: its @id is a path in the crate, not an IRI and not a fragment."""
    return "File" in canonical.types(entity) and not absolute(entity["@id"]) and not entity["@id"].startswith("#")


def admits(term, entity):
    """Whether a term's domain admits an entity. Two tokens name an entity by its @id, the root and the
    descriptor; every other names a type, or a File the crate holds. So an entity whose @id merely spells a type's
    name is not of that type (P0's verifier, round 2, R2-3)."""
    for s in term.domain:
        if s == "*" or (s in (V.ROOT, V.DESC) and s == entity["@id"]) or (s == V.LOCAL and local_file(entity)) \
                or s in canonical.types(entity):
            return True
    return False


def _place(paths, path, at):
    """Hold a path of the crate in paths, a tree whose nodes are its segments casefolded, each with the name it was
    first written with, its kind and the nodes below it. Refused `graph-form` at `at` where a path's name differs
    from another's only by case, or where a path is both a file and a directory. A path costs what its characters
    do: built as a string at every prefix, a path of 50,000 segments took 149 s, its memory the square of its length
    (P0.5's fourth verifier, note 1). Casefolding a path segment by segment is casefolding it whole, since no
    character folds to or from `/`."""
    node, parts = paths, path.split("/")
    for n, part in enumerate(parts, 1):
        kind = "file" if n == len(parts) else "directory"
        name, other_kind, below = node.setdefault(part.casefold(), (part, kind, {}))
        if name != part:
            raise Refused("graph-form", at, f"a path, {'/'.join(parts[:n])}, whose name differs from "
                          f"{'/'.join(parts[:n - 1] + [name])}'s only by case")
        if other_kind != kind:
            raise Refused("graph-form", at, f"{'/'.join(parts[:n])} is both a file and a directory")
        node = below


def read(data):
    md = _parse(data)
    _top(md)
    _graph(md["@graph"])
    _terms(md["@graph"])
    _values(md["@graph"])
    return md


def _parse(data):
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as e:
        raise Refused("spelling", f"byte {e.start}", "a byte that is not ASCII") from None
    try:
        md = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except _Twice as e:
        raise Refused("spelling", "the bytes", f"{e.args[0]!r}: a key twice in one object, or a NaN or "
                                               "infinity") from None
    except json.JSONDecodeError as e:
        raise Refused("spelling", f"line {e.lineno} column {e.colno}", f"not JSON: {e.msg}") from None
    except ValueError as e:
        raise Refused("spelling", "the bytes", f"not readable: {e}") from None
    except RecursionError:
        raise Refused("spelling", "the bytes", "nested deeper than the reader reads") from None
    try:
        again = canonical.dumps(md)
    except ValueError:
        raise Refused("spelling", "the bytes", "a number with no finite value") from None
    except RecursionError:
        raise Refused("spelling", "the bytes", "nested deeper than the reader reads") from None
    if again != data:
        raise Refused("spelling", canonical.first_difference(data, again),
                      "not the canonical bytes: ASCII, sorted keys, an indent of two, LF, a final LF")
    return md


def _top(md):
    if not isinstance(md, dict) or list(md) != ["@context", "@graph"]:
        raise Refused("graph-form", "the top level", "it holds @context and @graph, and nothing else")
    if md["@context"] != V.context():
        raise Refused("context", "@context", "not this profile version's: RO-Crate 1.3's, then "
                                             f'{{"{V.PREFIX}": "{V.NAMESPACE}"}}')
    graph = md["@graph"]
    if not isinstance(graph, list) or len(graph) < 2 or not all(isinstance(e, dict) for e in graph):
        raise Refused("graph-form", "@graph", "a list of entities, the descriptor and the root among them")


def _refs(value):
    for v in value if isinstance(value, list) else [value]:
        if isinstance(v, dict) and isinstance(v.get("@id"), str):
            yield v["@id"]


def _graph(graph):
    ids = []
    for i, e in enumerate(graph):
        where = e.get("@id", f"@graph[{i}]")
        if "@id" not in e or "@type" not in e:
            raise Refused("graph-form", where if isinstance(where, str) else f"@graph[{i}]",
                          "an entity without @id or @type")
        p = spelling.id_problem(e["@id"])
        if p:
            raise Refused("spelling", f"@graph[{i}] @id", p)
        t = e["@type"]
        if isinstance(t, list):
            if len(t) < 2 or not all(isinstance(x, str) for x in t) or t != sorted(set(t)):
                raise Refused("spelling", f"{where} @type", "several types as a sorted list of distinct "
                                                           "strings; one type as a string")
        elif not isinstance(t, str):
            raise Refused("spelling", f"{where} @type", "a type is a string")
        if local_file(e):
            p = spelling.path_problem(e["@id"])
            if p:
                raise Refused("spelling", f"{where} @id", f"a file's @id is its path in the crate: {p}")
        ids.append(e["@id"])
    # Every path along a file, its directories and itself, against every other: two whose names differ only by
    # case are one path on a host that folds case, and so is a path that is a file and a directory at once
    # (P0's verifier, round 6: data/A/x and data/a/y were accepted where case is kept, and are one directory
    # where it is folded). The descriptor is a file too.
    seen, paths = set(), {}
    _place(paths, canonical.DESCRIPTOR, canonical.DESCRIPTOR)
    for e, i in zip(graph, ids):
        if i in seen:
            raise Refused("graph-form", i, "an @id twice in the graph")
        seen.add(i)
        if local_file(e):
            _place(paths, i, i)
    if ids[:2] != [canonical.DESCRIPTOR, canonical.ROOT]:
        raise Refused("graph-form", "@graph", "the descriptor first, then the root")
    if ids[2:] != sorted(ids[2:]):
        raise Refused("graph-form", "@graph", "after the descriptor and the root, the entities in @id order")
    descriptor, root = graph[0], graph[1]
    if descriptor != V.descriptor():
        raise Refused("graph-form", canonical.DESCRIPTOR,
                      "the descriptor is a CreativeWork about ./ that conformsTo RO-Crate 1.3, and nothing more")
    if "Dataset" not in canonical.types(root):
        raise Refused("graph-form", canonical.ROOT, "the root is a Dataset")
    if set(canonical.types(root)) & V.ACTION_TYPES:
        raise Refused("graph-form", canonical.ROOT, "the root is a Dataset, never an action")   # round 6
    for k in V.ROOT_REQUIRED:
        if k not in root:
            raise Refused("graph-form", f"{canonical.ROOT} {k}", "the root carries every term the profile requires "
                                                                f"of it: {', '.join(V.ROOT_REQUIRED)}")
    if root["conformsTo"] != sorted([{"@id": V.PROCESS_RUN_CRATE}, {"@id": V.PROFILE}], key=canonical.sort_key):
        raise Refused("graph-form", f"{canonical.ROOT} conformsTo", "Process Run Crate 0.6 and this profile")
    _profiles(graph)
    actions = sorted(e["@id"] for e in graph if set(canonical.types(e)) & V.ACTION_TYPES)
    mentioned = list(_refs(root.get("mentions", [])))
    if mentioned != actions:
        raise Refused("graph-form", f"{canonical.ROOT} mentions", "the root mentions every action, and only them")
    for e in graph:
        for k, v in e.items():
            if k in V.TERM and V.TERM[k].spelling == "ref":
                for r in _refs(v):
                    if not absolute(r) and r not in seen:
                        raise Refused("graph-form", f"{e['@id']} {k}", f"{r} names no entity in the graph")


def _profiles(graph):
    """Each profile the root conformsTo has its contextual entity, exactly as the table states it; one declaring
    another version, as text, is `context`, since this reader reads one version of each (P4's design, R3 and D10;
    P0.3). A version that is no text is a misshapen entity (P0.4)."""
    held = {e["@id"]: e for e in graph if "Profile" in canonical.types(e)}
    for want in V.profile_entities():
        have = held.pop(want["@id"], None)
        if have is None:
            raise Refused("graph-form", want["@id"], "each profile the root conformsTo has its contextual entity")
        if have != want and isinstance(have.get("version"), str) and {**have, "version": want["version"]} == want:
            raise Refused("context", f"{want['@id']} version",
                          f"the crate declares {have['version']}; this reader reads {want['version']}")
        if have != want:
            raise Refused("graph-form", want["@id"], "a profile's contextual entity is its @id, @type, name and "
                                                     "version as the table states them, and nothing more")
    for i in sorted(held):
        raise Refused("graph-form", i, "a Profile entity for no profile the root conformsTo")


def _terms(graph):
    known = rocrate_terms()
    for e in graph:
        for k in e:
            if k in ("@id", "@type") or k in V.TERM:
                continue
            if k in known:
                raise Refused("field-kind", f"{e['@id']} {k}", "RO-Crate defines this key; this profile gives "
                                                              "it no kind (rule 9)")
            raise Refused("term-unknown", f"{e['@id']} {k}", "a key that names no term")
        for t in canonical.types(e):
            if t not in V.TYPE:
                raise Refused("term-unknown", f"{e['@id']} @type", f"{t}: a type this profile does not list")
        for k in e:
            if k in V.TERM and not admits(V.TERM[k], e):
                raise Refused("graph-form", f"{e['@id']} {k}",
                              f"{k} stands only on {', '.join(V.TERM[k].domain)}")


def _values(graph):
    for e in graph:
        for k, v in e.items():
            if k in ("@id", "@type"):
                continue
            t = V.TERM[k]
            where = f"{e['@id']} {k}"
            if isinstance(v, str) and v in t.absent:
                continue
            if t.many:
                if not isinstance(v, list) or not v:
                    raise Refused("spelling", where, "a list of one value or more")
                for x in v:
                    p = spelling.problem(t.spelling, x)
                    if p:
                        raise Refused("spelling", where, p)
                keys = [canonical.sort_key(x) for x in v]
                if keys != sorted(set(keys)):
                    raise Refused("spelling", where, "a list sorted, each value once")
            else:
                if isinstance(v, list):
                    raise Refused("spelling", where, "one value, not a list")
                p = spelling.problem(t.spelling, v)
                if p:
                    raise Refused("spelling", where, p)
