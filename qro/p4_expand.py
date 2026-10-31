"""A QRO crate's metadata as RDF triples: JSON-LD expansion, with RO-Crate 1.3's pinned context (P4's design, item 4.5).

The evaluator (qro/p4_eval.py) reads these triples. The engine stage reads the same metadata with rdflib's own
JSON-LD parser and holds the two triple sets equal, crate by crate (tests/p4shacl/), so this is not a second
reading of JSON-LD but a small one that a real parser checks.

It reads the forms of value the strict reader admits (qro/reader.py) and refuses the rest, so it never drops in silence a
value of another form: a value is a string, an integer (the shapes hold its bounds, not this), a reference {"@id": ...}
or a list of those, and anything else is an ExpandError. What JSON-LD itself drops stays dropped, as every parser drops
it: a key that is neither a term of the context nor an IRI. That is the shapes' stated limit 5 (a key no context
defines never reaches RDF).

An id is resolved against BASE, the one the engine runner is given, so both read the same IRIs. Every id the reader
accepts (FORMAT.md item 22: the root `./`, a path in the crate, a fragment, an absolute IRI) this module resolves as
rdflib does, and to an IRI of its own: held by tests/p4shacl/test_p4shacl_ids.py over tens of thousands of ids against a
real parser, and by tests/p4/test_p4_ids.py without one. It refuses the ids it knows rdflib reads otherwise, and never
guesses: a blank-node id, a network-path reference, a dot segment, an empty segment, a query, an empty fragment, an id that
begins with `@` (rdflib reads it as the root), an absolute `file:` IRI (it could not be told from a relative id) and a
colon that is neither a scheme nor a prefix of the context. The reader refuses each of them too, so a crate this module
cannot read is a crate the checker has refused, and the gates never skip one (tests/p4/p4_helpers.py). A compact IRI
(`schema:a`) it reads as JSON-LD does, as the IRI it expands to; the reader refuses those as well, being a second spelling.
What stays is item 22's own limits, which only another base brings (limit 19): an absolute IRI equal to the IRI a relative
id resolves to, where a crate is read at that IRI, is one node with it. At BASE no such IRI is an id, since `file:` ids are
refused. Stdlib only.
"""
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urljoin

from qro import vocabulary as V
from qro.p4_model import RDF_TYPE, XSD_INTEGER, BNode, Lit, iri_ok

BASE = "file:///crate/"
_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:", re.ASCII)
_SEG = r"(?![.]{1,2}(?:/|$))[A-Za-z0-9._~!$&'()*+,;=@%-]+"          # a path segment that is neither . nor ..
_FRAGMENT = r"#[A-Za-z0-9._~!$&'()*+,;=@%:/?-]+"
RELATIVE = re.compile(rf"(?:\./|{_SEG}(?:/{_SEG})*/?)?(?:{_FRAGMENT})?", re.ASCII)
_GEN_DELIMS = ":/?#[]@"


class ExpandError(ValueError):
    """The metadata holds a form the expansion does not read."""


@lru_cache(maxsize=1)
def context():
    """RO-Crate 1.3's term definitions, from the copy whose digest the vocabulary pins."""
    data = (Path(V.__file__).parent / V.ROCRATE_CONTEXT_FILE).read_bytes()
    if hashlib.sha256(data).hexdigest() != V.ROCRATE_CONTEXT_SHA256:
        raise RuntimeError(f"{V.ROCRATE_CONTEXT_FILE} is not the copy the vocabulary pins")
    terms = json.loads(data)["@context"]
    if not all(isinstance(v, str) for v in terms.values()):
        raise ExpandError("a term of RO-Crate's context that is not a plain IRI: the expansion reads plain ones")
    return terms


@lru_cache(maxsize=1)
def prefixes():
    """The prefixes a compact IRI may use: the context's terms whose IRI ends in a gen-delim (JSON-LD 1.1's rule for a
    simple term definition), and the crate's own, qro."""
    out = {k: v for k, v in context().items() if v and v[-1] in _GEN_DELIMS}
    out[V.PREFIX] = V.NAMESPACE
    return out


def _prefixed(value):
    """JSON-LD's reading of a value with a colon: the IRI it names, or None where it has none."""
    if ":" not in value:
        return None
    prefix, _, local = value.partition(":")
    if prefix == "_":
        raise ExpandError(f"{value!r}: a blank node identifier")
    if not local.startswith("//") and prefix in prefixes():
        found = prefixes()[prefix] + local
    elif _SCHEME.match(value):
        if value.lower().startswith("file:"):
            raise ExpandError(f"{value!r}: a file: IRI cannot be told from a relative id against {BASE}")
        found = value
    else:
        raise ExpandError(f"{value!r}: a colon that is neither a scheme nor a prefix of the context")
    if not iri_ok(found):
        raise ExpandError(f"{value!r}: an IRI with a space, a control character or one an IRI may not hold")
    return found


def iri_of_id(value):
    """The IRI an @id names: compact, absolute, or resolved against BASE."""
    if not isinstance(value, str) or not value:
        raise ExpandError(f"{value!r}: an @id is a string")
    if not value.startswith("#"):                # a fragment is document-relative, whatever follows its #: `#a:b` is no compact IRI
        got = _prefixed(value)
        if got is not None:
            return got
    if value.startswith("@"):
        raise ExpandError(f"{value!r}: an id that begins with @, which rdflib reads as the root")
    if not RELATIVE.fullmatch(value):
        raise ExpandError(f"{value!r}: a relative id the expansion does not resolve")
    return urljoin(BASE, value)


def _term(key):
    """A term of the context as an IRI. One of RO-Crate's is itself a compact IRI (HTML is rdf:HTML)."""
    value = context()[key]
    return _prefixed(value) or value


def iri_of_term(key):
    """The IRI RO-Crate's context gives a term or a type (KeyError for a name it does not define)."""
    return _term(key)


def iri_of_key(key):
    """The predicate a key names, or None where JSON-LD drops the key: it is neither a term nor an IRI."""
    if key in context():
        return _term(key)
    return _prefixed(key)


def iri_of_type(value):
    """The class a type names: a term, an IRI, or else relative to the base, as JSON-LD reads a type."""
    if not isinstance(value, str) or not value:
        raise ExpandError(f"{value!r}: a type is a string")
    if value in context():
        return _term(value)
    return iri_of_id(value)


def literal(value):
    """The literal of a JSON value, as rdflib's JSON-LD parser makes it."""
    if type(value) is int:
        return Lit(str(value), XSD_INTEGER)
    if isinstance(value, str):
        return Lit(value)
    raise ExpandError(f"{value!r}: a value is a string or an integer")


def _object(value):
    if isinstance(value, dict):
        if list(value) != ["@id"]:
            raise ExpandError(f"{value!r}: a reference is {{\"@id\": ...}} and nothing else")
        return iri_of_id(value["@id"])
    return literal(value)


def expand(md):
    """The triples of a QRO crate's metadata, as a list in graph order. ExpandError for anything the strict reader
    would not admit."""
    if not isinstance(md, dict) or list(md) != ["@context", "@graph"]:
        raise ExpandError("the top level holds @context and @graph, and nothing else")
    if md["@context"] != V.context():
        raise ExpandError("a @context other than the one the reader holds")
    if not isinstance(md["@graph"], list) or not all(isinstance(e, dict) for e in md["@graph"]):
        raise ExpandError("@graph is a list of entities")
    triples, blanks = [], 0
    for e in md["@graph"]:
        if "@id" in e:
            subject = iri_of_id(e["@id"])
        else:
            blanks += 1
            subject = BNode(blanks)
        for key, value in e.items():
            if key == "@id":
                continue
            if key == "@type":
                for t in value if isinstance(value, list) else [value]:
                    triples.append((subject, RDF_TYPE, iri_of_type(t)))
                continue
            if key.startswith("@"):
                raise ExpandError(f"{key}: a keyword the expansion does not read")
            predicate = iri_of_key(key)
            if predicate is None:
                continue                      # JSON-LD drops a key its context does not define
            for x in value if isinstance(value, list) else [value]:
                triples.append((subject, predicate, _object(x)))
    return triples
