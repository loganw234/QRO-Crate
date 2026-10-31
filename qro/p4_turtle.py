"""The Turtle writer: P4's shapes (qro/p4_model.py) as the text a SHACL engine reads (P4's design, items 4.1 and 5).

It reads the model and nothing else, so the Turtle and the in-process evaluator are two readers of one design. Its
output is ASCII with LF line ends (every non-ASCII character of a string is a \\u or \\U escape), in one fixed order, so
two renders are the same bytes whatever the host, its locale or its hash seed. It writes SHACL Core and nothing
beyond: no SPARQL, no SHACL-AF.

A SHACL engine reports a result with the severity of the shape that produced it, and a node shape's severity does not
reach the property shapes inside it (MEASURED, pyshacl 0.40.1, experiment 1 of this build), so every property shape
that reports carries the level of the named shape that holds it. A shape nested in sh:or, sh:not or
sh:qualifiedValueShape produces no result of its own, and carries none. Stdlib only.
"""
import re

from qro.p4_model import SEVERITY, XSD_BOOLEAN, XSD_INTEGER, XSD_STRING, BNode, Lit, direct, iri_ok, problems

ANNOTATION_PREFIX = "qs"      # the prefix of the shapes' own annotations, qs:claims and qs:kind: it must be declared
_LOCAL = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*", re.ASCII)
_TARGET = {"class": "sh:targetClass", "subjectsOf": "sh:targetSubjectsOf", "objectsOf": "sh:targetObjectsOf",
           "node": "sh:targetNode"}
_INTEGER = re.compile(r"[+-]?[0-9]+", re.ASCII)
_NOT_IN_AN_IRI = re.compile(r'[\x00-\x20<>"{}|^`\\\x7f-\U0010ffff]')     # IRIREF's own exclusions, and all non-ASCII


def escape(text):
    """A string literal in Turtle's double quotes: ASCII, with \\u and \\U escapes for the rest."""
    out = []
    for c in text:
        n = ord(c)
        if c == "\\":
            out.append("\\\\")
        elif c == '"':
            out.append('\\"')
        elif c == "\n":
            out.append("\\n")
        elif c == "\t":
            out.append("\\t")
        elif c == "\r":
            out.append("\\r")
        elif n < 0x20 or n > 0x7E:
            out.append(f"\\u{n:04x}" if n <= 0xFFFF else f"\\U{n:08x}")
        else:
            out.append(c)
    return '"' + "".join(out) + '"'


def iriref(u):
    """An IRI between angle brackets, as written: refused where it holds a character Turtle's IRIREF does not allow
    or one outside printable ASCII."""
    if not iri_ok(u):
        raise ValueError(f"an IRI that cannot be written as it is: {u!r}")
    return f"<{u}>"


class Writer:
    def __init__(self, prefixes):
        self.prefixes = tuple(prefixes)
        self.longest = sorted(self.prefixes, key=lambda kv: (-len(kv[1]), kv[0]))
        names = [p for p, _ in self.prefixes]
        if len(set(names)) != len(names):
            raise ValueError("a prefix declared twice")

    def iri(self, u):
        for prefix, base in self.longest:
            if u.startswith(base) and _LOCAL.fullmatch(u[len(base):]):
                return f"{prefix}:{u[len(base):]}"
        return iriref(u)

    def literal(self, lit):
        if lit.datatype == XSD_STRING:
            return escape(lit.lexical)
        if lit.datatype == XSD_INTEGER and _INTEGER.fullmatch(lit.lexical):
            return lit.lexical
        if lit.datatype == XSD_BOOLEAN and lit.lexical in ("true", "false"):
            return lit.lexical
        return f"{escape(lit.lexical)}^^{self.iri(lit.datatype)}"

    def term(self, t):
        if isinstance(t, Lit):
            return self.literal(t)
        if isinstance(t, str):
            return self.iri(t)
        raise ValueError(f"a blank node cannot be written inside a shape: {t!r}")

    def path(self, p):
        if direct(p):
            return self.iri(p)
        kind, inner = p
        if kind == "inv":
            return f"[ sh:inversePath {self.path(inner)} ]"
        if kind == "oneOrMore":
            return f"[ sh:oneOrMorePath {self.path(inner)} ]"
        raise ValueError(f"a path of kind {kind}")

    # -- a shape's entries: [(predicate, object text)], the object text possibly over several lines ---------------
    def entries(self, s, depth, level, top, reports):
        """`top`: a named shape that stands alone. `reports`: its results reach a report, which is so for it and
        for the property shapes it holds through sh:property, and for nothing inside sh:or, sh:not or a qualified
        value shape."""
        e = []
        add = e.append
        if s.path is not None:
            add(("sh:path", self.path(s.path)))
        if top:
            for pred, text in (("sh:name", s.name), ("sh:description", s.description)):
                if text:
                    add((pred, escape(text)))
        if reports and s.message:
            add(("sh:message", escape(s.message)))
        if reports:
            add(("sh:severity", "sh:" + SEVERITY[level]))
        if top:
            if s.claims:
                add((f"{ANNOTATION_PREFIX}:claims", ", ".join(escape(c) for c in s.claims)))
            if s.kind:
                add((f"{ANNOTATION_PREFIX}:kind", escape(s.kind)))
            for kind, iri in s.targets:
                add((_TARGET[kind], self.iri(iri)))
        if s.node_kind:
            add(("sh:nodeKind", "sh:" + s.node_kind))
        if s.datatype:
            add(("sh:datatype", self.iri(s.datatype)))
        for c in s.classes:
            add(("sh:class", self.iri(c)))
        if s.in_ is not None:
            add(("sh:in", "( " + " ".join(self.term(t) for t in s.in_) + " )" if s.in_ else "( )"))
        for v in s.has_value:
            add(("sh:hasValue", self.term(v)))
        if s.pattern is not None:
            add(("sh:pattern", escape(s.pattern)))
        for pred, v in (("sh:minLength", s.min_length), ("sh:maxLength", s.max_length),
                        ("sh:minInclusive", s.min_inclusive), ("sh:maxInclusive", s.max_inclusive),
                        ("sh:minCount", s.min_count), ("sh:maxCount", s.max_count)):
            if v is not None:
                add((pred, str(v)))
        if s.closed:
            add(("sh:closed", "true"))
            if s.ignored:
                add(("sh:ignoredProperties", "( " + " ".join(self.iri(i) for i in s.ignored) + " )"))
        if s.or_:
            add(("sh:or", self.alternatives(s.or_, depth, level)))
        for n in s.not_:
            add(("sh:not", self.block(n, depth, level, reports=False)))
        for q, minimum in s.qvs:
            add(("sh:qualifiedValueShape", self.block(q, depth, level, reports=False)))
            add(("sh:qualifiedMinCount", str(minimum)))
        for p in s.props:
            add(("sh:property", self.block(p, depth, level, reports=reports)))
        return e

    @staticmethod
    def lines(entries, depth):
        pad = "    " * depth
        return [f"{pad}{pred} {obj}" + (" ;" if i < len(entries) - 1 else "") for i, (pred, obj) in enumerate(entries)]

    def block(self, s, depth, level, reports):
        """A blank node: the shape's entries between brackets, one level in."""
        inner = self.lines(self.entries(s, depth + 1, level, top=False, reports=reports), depth + 1)
        return "\n".join(["["] + inner + ["    " * depth + "]"])

    def alternatives(self, shapes, depth, level):
        pad = "    " * (depth + 1)
        return "\n".join(["("] + [pad + self.block(a, depth + 1, level, reports=False) for a in shapes]
                         + ["    " * depth + ")"])

    def shape(self, s):
        """A named shape as a Turtle statement."""
        kind = "sh:NodeShape" if s.path is None else "sh:PropertyShape"
        body = self.lines([("a", kind)] + self.entries(s, 1, s.level, top=True, reports=True), 1)
        body[-1] += " ."
        return "\n".join([self.iri(s.id)] + body)

    def header(self):
        return "".join(f"@prefix {p}: {iriref(u)} .\n" for p, u in self.prefixes)


def render(shapes, prefixes, banner):
    """The Turtle of `shapes`, in the order given: a comment banner, the prefixes, then one statement a shape. A
    shape the model calls incoherent is refused, never written."""
    found = [p for s in shapes for p in problems(s)]
    if found:
        raise ValueError("; ".join(found))
    if len({s.id for s in shapes}) != len(shapes):
        raise ValueError("two shapes share an id")
    if not all(line.isascii() and "\n" not in line for line in banner):
        raise ValueError("a banner line is one line of ASCII")
    w = Writer(prefixes)
    comment = "".join(f"# {line}\n" if line else "#\n" for line in banner)
    return comment + w.header() + "".join("\n" + w.shape(s) + "\n" for s in shapes)


# -- N-Triples, for the data a micro case hands an engine --------------------------------------------------------
def node(t):
    """One RDF term as N-Triples writes it."""
    if isinstance(t, str):
        return iriref(t)
    if isinstance(t, BNode):
        return f"_:b{t.n}"
    if isinstance(t, Lit):
        return escape(t.lexical) + ("" if t.datatype == XSD_STRING else f"^^{iriref(t.datatype)}")
    raise TypeError(f"not an RDF term: {t!r}")


def ntriples(triples):
    """N-Triples for a set of triples, sorted, one to a line, ASCII with LF line ends."""
    lines = sorted(f"{node(s)} {node(p)} {node(o)} ." for s, p, o in triples)
    return "".join(line + "\n" for line in lines)
