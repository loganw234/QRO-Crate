"""P4's shapes as plain data: the SHACL Core subset QRO-Crate's shapes are written in (P4's design, item 4.1).

A shape is data first. Two readers read that data, the Turtle writer (qro/p4_turtle.py) and the evaluator
(qro/p4_eval.py), so the Turtle a tool reads and the verdicts this repository's tests hold are one design, not two.
Neither is the checker: a shape is a consequence of what the checker holds, never an authority beside it
(docs/P4.md). Only the constraint components the generated shapes use are here, so that the engine stage can hold
each one to a real SHACL engine, case by case (tests/p4shacl/). Stdlib only.

Terms of a graph, as the evaluator and the expansion (qro/p4_expand.py) use them: an IRI is a `str`, a blank node
is a `BNode`, a literal is a `Lit`. A triple is a (subject, predicate, object) tuple of these.
"""
import re
from dataclasses import dataclass

SH = "http://www.w3.org/ns/shacl#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDF_TYPE = RDF + "type"
XSD = "http://www.w3.org/2001/XMLSchema#"
XSD_STRING, XSD_INTEGER, XSD_BOOLEAN, XSD_DOUBLE = XSD + "string", XSD + "integer", XSD + "boolean", XSD + "double"

LEVELS = ("must", "should", "may")
# A shape's level is its severity: the folder rocrate-validator reads it from (must/, should/, may/), and the
# sh:severity a SHACL engine reads, are held equal by a test (P4's design, item 4.2).
SEVERITY = {"must": "Violation", "should": "Warning", "may": "Info"}
NODE_KINDS = ("IRI",)
TARGETS = ("class", "subjectsOf", "objectsOf", "node")


@dataclass(frozen=True)
class Lit:
    """A literal. A plain string is an xsd:string, as in RDF 1.1."""
    lexical: str
    datatype: str = XSD_STRING


class BNode:
    """A blank node, told apart by its number alone."""
    __slots__ = ("n",)

    def __init__(self, n):
        self.n = n

    def __eq__(self, other):
        return isinstance(other, BNode) and other.n == self.n

    def __hash__(self):
        return hash(("bnode", self.n))

    def __repr__(self):
        return f"_:b{self.n}"


# What an IRI written between angle brackets may not hold (Turtle's IRIREF), and anything outside printable ASCII: an
# IRI with any of these is neither written nor read here, so that the Turtle, the N-Triples and the expansion agree.
NOT_IN_AN_IRI = re.compile(r'[\x00-\x20<>"{}|^`\\\x7f-\U0010ffff]')


def iri_ok(iri):
    """Whether `iri` is a non-empty string every character of which may stand in an IRI as written."""
    return isinstance(iri, str) and iri != "" and NOT_IN_AN_IRI.search(iri) is None


def inv(path):
    """The inverse of a path: sh:inversePath."""
    return ("inv", path)


def one_or_more(path):
    """One step of a path or more: sh:oneOrMorePath."""
    return ("oneOrMore", path)


def direct(path):
    """Whether a path is one predicate, an IRI, which is what sh:closed counts."""
    return isinstance(path, str)


def path_ok(path):
    """The paths the model has: one predicate, its inverse, and one step of either or more."""
    if direct(path):
        return True
    if not isinstance(path, tuple) or len(path) != 2:
        return False
    kind, inner = path
    if kind == "inv":
        return direct(inner)
    return kind == "oneOrMore" and (direct(inner) or (isinstance(inner, tuple) and inner[0] == "inv"
                                                       and path_ok(inner)))


@dataclass(frozen=True)
class Shape:
    """One shape: a node shape when `path` is None, a property shape otherwise. Every constraint is optional, and a
    shape holds all it names. The last six fields annotate: they are not constraints, and no reader of the data
    evaluates them.

    targets   ("class", iri) | ("subjectsOf", iri) | ("objectsOf", iri) | ("node", iri); only a named shape that
              stands alone has any. A node target is a focus node whether or not the graph holds a triple of it
    classes   sh:class, each of them: a value must be an instance of every one
    in_       sh:in: IRIs (str) and Lit; None for no constraint (an empty tuple is a list nothing is in)
    has_value sh:hasValue: a property shape needs each among its value nodes; a node shape needs its focus node to be it
    pattern   sh:pattern: a search of the string of an IRI or a literal's lexical form; a blank node always violates
    props     nested property shapes: sh:property, applied to each value node
    or_       sh:or: node shapes, one of which each value node must conform to
    not_      sh:not: node shapes, none of which a value node may conform to
    qvs       sh:qualifiedValueShape with sh:qualifiedMinCount: (node shape, minimum) pairs, on a property shape
    level     "must", "should" or "may": the severity every result of the shape and of its property shapes carries
    claims    the checker's refusal names this shape mirrors (P4's design, item 4.2); the generator adds the six
              refusals of steps 1 and 2 that can come before a shape's own and that RDF cannot show to every must
              shape (qro/p4_shapes.py, FORM: `spelling`, `term-unknown`, `graph-form`, `context`, `file-missing`,
              `file-link`). When a must shape fails the checker refuses the crate, and when the crate is one fault from
              one it accepts, by a name a failing shape claims: held over plants, a fuzz and sweeps
              (tests/p4/test_p4_examples.py, test_p4_sweeps.py), not proved; a crate with several faults is refused too,
              but by a name no failing shape need claim
    kind      for a term's shape, the term's kind (CHECKED, READ, ANCHORED, REPORTED), which the description states
    """
    id: str | None = None
    path: object = None
    targets: tuple = ()
    node_kind: str | None = None
    datatype: str | None = None
    classes: tuple = ()
    in_: tuple | None = None
    has_value: tuple = ()
    pattern: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    min_inclusive: int | None = None
    max_inclusive: int | None = None
    min_count: int | None = None
    max_count: int | None = None
    closed: bool = False
    ignored: tuple = ()
    props: tuple = ()
    or_: tuple = ()
    not_: tuple = ()
    qvs: tuple = ()
    name: str = ""
    description: str = ""
    message: str = ""
    level: str = "must"
    claims: tuple = ()
    kind: str = ""


def problems(shape, nested=False):
    """The ways a shape is incoherent, in a few words each: what the data can say and no SHACL engine reads alike.
    The generator refuses a table whose shapes have any (exit 2), and the tests plant each."""
    out = []
    where = shape.id or "a nested shape"
    if shape.level not in LEVELS:
        out.append(f"{where}: level {shape.level}")
    if nested and (shape.id is not None or shape.targets):
        out.append(f"{where}: a nested shape is nameless and has no target")
    if not nested and shape.id is None:
        out.append("a shape that stands alone needs an id")
    for kind, iri in shape.targets:
        if kind not in TARGETS or not isinstance(iri, str):
            out.append(f"{where}: target {kind}")
    if shape.node_kind is not None and shape.node_kind not in NODE_KINDS:
        out.append(f"{where}: node kind {shape.node_kind}")
    if shape.path is not None and not path_ok(shape.path):
        out.append(f"{where}: a path the model does not have")
    if shape.path is None and (shape.min_count is not None or shape.max_count is not None or shape.qvs):
        out.append(f"{where}: a count, or a qualified value shape, needs a path")
    if shape.path is not None and shape.targets:
        out.append(f"{where}: a property shape is reached through a node shape, and has no target of its own")
    if shape.pattern is not None and not shape.pattern.isascii():
        out.append(f"{where}: a pattern in printable ASCII, so that every file is")
    for a in shape.ignored:
        if not isinstance(a, str):
            out.append(f"{where}: an ignored property is an IRI")
    if shape.ignored and not shape.closed:
        out.append(f"{where}: ignored properties without sh:closed")
    for child in shape.props + shape.or_ + shape.not_ + tuple(q for q, _ in shape.qvs):
        out += problems(child, nested=True)
    for p in shape.props:
        if p.path is None:
            out.append(f"{where}: sh:property takes property shapes, and this one has no path")
    for q, minimum in shape.qvs:
        if q.path is not None or not isinstance(minimum, int) or minimum < 1:
            out.append(f"{where}: a qualified value shape is a node shape with a minimum of one or more")
    for child in shape.or_ + shape.not_:
        if child.path is not None:
            out.append(f"{where}: an alternative is a node shape")
    return out


def walk(shape):
    """The shape, then every shape nested in it, depth first."""
    yield shape
    for child in shape.props + shape.or_ + shape.not_ + tuple(q for q, _ in shape.qvs):
        yield from walk(child)
