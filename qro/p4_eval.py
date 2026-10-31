"""The in-process evaluator of P4's shapes (P4's design, items 4.5 and 4.6): the model (qro/p4_model.py) against a set
of triples (qro/p4_expand.py), with no third-party code, so that the gates of the design run in the quick budget.

It is not a SHACL engine and it gives no verdict on a crate: `python -m qro check` never calls it. It is this
repository's reading of the SHACL Recommendation for the Core components the model has, and the engine stage
(tests/p4shacl/) holds it to a real engine, case by case and crate by crate. Where a reading of mine differs from the
engine's, that stage is what finds it, and the case becomes a test here.

The reading, component by component:
  - targets: sh:targetClass, sh:targetSubjectsOf, sh:targetObjectsOf and sh:targetNode pick the focus nodes (a literal
    object is one, and a target node is one though the graph holds nothing of it);
  - a property shape's value nodes are the nodes at the end of its path from the focus node, each once; a node
    shape's value node is the focus node itself;
  - sh:pattern searches the string of an IRI or a literal's lexical form, and a blank node always violates it, as it
    does sh:minLength and sh:maxLength; sh:in compares terms exactly, a literal by lexical form and datatype;
  - sh:datatype wants a literal of that datatype that is well-formed for it, a plain string being an xsd:string;
  - sh:minInclusive and sh:maxInclusive want a numeric literal, and a value that is not one violates them;
  - sh:class wants an instance of the class by rdf:type, a literal never one; sh:hasValue on a property shape wants
    the value among the value nodes, on a node shape wants the focus node to be it;
  - sh:closed allows the properties of the shape's own property shapes whose path is one IRI, and its
    sh:ignoredProperties; sh:qualifiedValueShape counts the value nodes that conform to it;
  - a result carries the level of the shape that holds it, and a report that has only should-level results does not
    "conform" for an engine (the Recommendation), so a user filters by level.
Stdlib only.
"""
import re
from dataclasses import dataclass
from fractions import Fraction

from qro.p4_model import (RDF_TYPE, XSD, XSD_BOOLEAN, XSD_DOUBLE, XSD_INTEGER, BNode, Lit, direct)

_INTEGER = re.compile(r"[+-]?[0-9]+", re.ASCII)
_DECIMAL = re.compile(r"[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)", re.ASCII)
_DOUBLE = re.compile(r"([+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?|[+-]?INF|NaN)", re.ASCII)
XSD_DECIMAL = XSD + "decimal"


def node_key(t):
    """A total order on terms, so that everything here is deterministic whatever the host's hash seed."""
    if isinstance(t, str):
        return 0, t, ""
    if isinstance(t, BNode):
        return 1, str(t.n).zfill(12), ""
    return 2, t.lexical, t.datatype


class Graph:
    """A set of triples with the indexes the shapes' targets and paths use."""

    def __init__(self, triples):
        self.triples = frozenset(triples)
        self.sp, self.po, self.subjects_of, self.objects_of, self.instances = {}, {}, {}, {}, {}
        for s, p, o in sorted(self.triples, key=lambda t: tuple(node_key(x) for x in t)):
            self.sp.setdefault(s, {}).setdefault(p, []).append(o)
            self.po.setdefault(o, {}).setdefault(p, []).append(s)
            self.subjects_of.setdefault(p, {})[s] = None          # a dict is an ordered set
            self.objects_of.setdefault(p, {})[o] = None
            if p == RDF_TYPE and isinstance(o, str):
                self.instances.setdefault(o, {})[s] = None

    def values(self, focus, path):
        """The nodes at the end of `path` from `focus`, each once, in a fixed order."""
        if direct(path):
            return list(self.sp.get(focus, {}).get(path, []))
        kind, inner = path
        if kind == "inv":
            return list(self.po.get(focus, {}).get(inner, [])) if direct(inner) else self._inverse(focus, inner)
        seen, frontier, out = set(), [focus], []
        while frontier:                                   # oneOrMore: breadth first, each node once
            nxt = []
            for n in frontier:
                for v in self.values(n, inner):
                    if v not in seen:
                        seen.add(v)
                        out.append(v)
                        nxt.append(v)
            frontier = nxt
        return out

    def _inverse(self, focus, inner):
        raise ValueError(f"an inverse of {inner!r}: the model has the inverse of one predicate only")

    def types(self, node):
        return self.sp.get(node, {}).get(RDF_TYPE, [])

    def is_a(self, node, cls):
        return not isinstance(node, Lit) and cls in self.types(node)


def string_of(v):
    """The string a pattern or a length reads: an IRI, or a literal's lexical form; None for a blank node."""
    if isinstance(v, Lit):
        return v.lexical
    return v if isinstance(v, str) else None


def well_formed(lit):
    d = lit.datatype
    if d == XSD_INTEGER:
        return _INTEGER.fullmatch(lit.lexical) is not None
    if d == XSD_BOOLEAN:
        return lit.lexical in ("true", "false", "1", "0")
    if d == XSD_DECIMAL:
        return _DECIMAL.fullmatch(lit.lexical) is not None
    if d == XSD_DOUBLE:
        return _DOUBLE.fullmatch(lit.lexical) is not None
    return True


def number(v):
    """The numeric value of a well-formed integer, decimal or double literal; None for anything else."""
    if not isinstance(v, Lit) or not well_formed(v):
        return None
    if v.datatype == XSD_INTEGER:
        return int(v.lexical)
    if v.datatype == XSD_DECIMAL:
        return Fraction(v.lexical)
    if v.datatype == XSD_DOUBLE:
        x = float(v.lexical.replace("INF", "inf"))
        return None if x != x else x
    return None


def value_reasons(g, s, v):
    """Why the value node `v` violates the value-level constraints of shape `s`: a list of a few words each."""
    out = []
    if s.node_kind == "IRI" and not isinstance(v, str):
        out.append("not an IRI")
    if s.datatype is not None and not (isinstance(v, Lit) and v.datatype == s.datatype and well_formed(v)):
        out.append(f"not a well-formed literal of {s.datatype.rsplit('#', 1)[-1]}")
    for c in s.classes:
        if not g.is_a(v, c):
            out.append(f"not an instance of {c.rsplit('/', 1)[-1].rsplit('#', 1)[-1]}")
    if s.in_ is not None and v not in s.in_:
        out.append("not one of the listed values")
    text = string_of(v)
    if s.pattern is not None and (text is None or re.search(s.pattern, text) is None):
        out.append("does not match the pattern")
    if s.min_length is not None and (text is None or len(text) < s.min_length):
        out.append("too short")
    if s.max_length is not None and (text is None or len(text) > s.max_length):
        out.append("too long")
    for bound, ok in ((s.min_inclusive, lambda x, b: x >= b), (s.max_inclusive, lambda x, b: x <= b)):
        if bound is not None:
            x = number(v)
            if x is None or not ok(x, bound):
                out.append("outside its bounds")
    if s.or_ and not any(not node_reasons(g, a, v) for a in s.or_):
        out.append("none of the alternatives holds")
    for n in s.not_:
        if not node_reasons(g, n, v):
            out.append("a shape it must not conform to holds")
    for p in s.props:
        out += property_reasons(g, p, v)
    if s.closed and not isinstance(v, Lit):
        allowed = set(s.ignored) | {p.path for p in s.props if direct(p.path)}
        for predicate in g.sp.get(v, {}):
            if predicate not in allowed:
                out.append(f"closed: {predicate.rsplit('/', 1)[-1].rsplit('#', 1)[-1]} is not allowed")
    return out


def node_reasons(g, s, focus):
    """Why `focus` does not conform to the node shape `s`."""
    out = value_reasons(g, s, focus)
    for hv in s.has_value:
        if hv != focus:
            out.append("is not the required value")
    return out


def property_reasons(g, s, focus):
    """Why `focus` does not conform to the property shape `s`: its path, its counts and its value nodes."""
    values = list(dict.fromkeys(g.values(focus, s.path)))
    out = []
    if s.min_count is not None and len(values) < s.min_count:
        out.append(f"fewer than {s.min_count} values")
    if s.max_count is not None and len(values) > s.max_count:
        out.append(f"more than {s.max_count} values")
    for hv in s.has_value:
        if hv not in values:
            out.append("a required value is missing")
    for q, minimum in s.qvs:
        if sum(1 for v in values if not node_reasons(g, q, v)) < minimum:
            out.append(f"fewer than {minimum} values conform to the qualified shape")
    for v in values:
        out += value_reasons(g, s, v)
    return out


def reasons(g, s, focus):
    return property_reasons(g, s, focus) if s.path is not None else node_reasons(g, s, focus)


def focus_nodes(g, s):
    """The focus nodes of a named shape, in a fixed order, each once."""
    out = []
    for kind, iri in s.targets:
        if kind == "class":
            out += g.instances.get(iri, ())
        elif kind == "subjectsOf":
            out += g.subjects_of.get(iri, ())
        elif kind == "objectsOf":
            out += g.objects_of.get(iri, ())
        elif kind == "node":
            out.append(iri)
    return sorted(dict.fromkeys(out), key=node_key)


@dataclass(frozen=True)
class Result:
    shape: str
    level: str
    focus: object
    reason: str


def validate(shapes, triples):
    """Every result of every shape that has a focus node, as a list of Result in shape order, then focus order."""
    g = triples if isinstance(triples, Graph) else Graph(triples)
    out = []
    for s in shapes:
        for focus in focus_nodes(g, s):
            out += [Result(s.id, s.level, focus, why) for why in reasons(g, s, focus)]
    return out


def failing(results, level=None):
    """The ids of the shapes that have a result, at `level` or at any level, sorted."""
    return sorted({r.shape for r in results if level is None or r.level == level})


def failing_pairs(results, level=None):
    """(shape id, focus node) for each, sorted: what the engine stage holds a real engine's report to."""
    return sorted({(r.shape, focus_name(r.focus)) for r in results if level is None or r.level == level})


def focus_name(focus):
    """A focus node as the engine runner names it: an IRI itself, a literal by its lexical form, a blank node as one."""
    return "_:blank" if isinstance(focus, BNode) else focus.lexical if isinstance(focus, Lit) else focus
