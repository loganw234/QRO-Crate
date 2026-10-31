"""The micro cases: one small model, one small graph and the focus nodes that must fail, for each constraint component
of qro/p4_model.py and each outcome of it (P4's design, items 4.5 and 5). Two stages read them:
  - tests/p4/test_p4_eval.py holds the evaluator to the expectation written here, which is this repository's reading
    of the SHACL Recommendation, case by case;
  - tests/p4shacl/test_p4shacl_micro.py renders each as Turtle and N-Triples and holds a real engine to the same
    expectation, and to the evaluator. That is where a misreading of mine shows.
A case that is on both sides of a boundary has a case on each: a value one over, a value exactly at. Nothing here is a
test: pytest's naming decides what is one (CLAUDE.md).
"""
from dataclasses import dataclass

from qro.p4_model import RDF_TYPE, XSD, XSD_BOOLEAN, XSD_DOUBLE, XSD_INTEGER, XSD_STRING, BNode, Lit, Shape, inv, one_or_more

EX = "http://example.org/"
PREFIXES = (("sh", "http://www.w3.org/ns/shacl#"), ("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
            ("xsd", XSD), ("ex", EX), ("qs", EX + "shapes#"))
P, Q, R = EX + "p", EX + "q", EX + "r"
A, B, C, Z = EX + "a", EX + "b", EX + "c", EX + "z"
T1, T2, T3 = EX + "T1", EX + "T2", EX + "T3"
S = EX + "shapes#S"
MAX = 2 ** 63 - 1
BLANK = BNode(1)
DECIMAL, TOKEN = XSD + "decimal", XSD + "token"


@dataclass(frozen=True)
class Case:
    name: str
    shapes: tuple                # the shapes, each with an id
    data: tuple                  # the triples
    fails: tuple                 # (shape id, focus name) for each that must fail; focus names as p4_eval.focus_name makes them
    component: str = ""


CASES = []


def case(component, name, shape, data, *fails, level=None):
    """`fails`: the focus nodes (a name each) the shape's own id fails at, or (shape id, focus) pairs."""
    shapes = shape if isinstance(shape, tuple) else (shape,)
    expect = tuple(f if isinstance(f, tuple) else (shapes[0].id, f) for f in fails)
    CASES.append(Case(f"{component}: {name}", shapes, tuple(data), tuple(sorted(expect)), component))


def on_p(**kw):
    """A node shape for the subjects of ex:p with one property shape on ex:p."""
    return Shape(id=S, targets=(("subjectsOf", P),), props=(Shape(path=P, **kw),))


def one(value):
    return [(A, P, value)]


# -- sh:datatype ---------------------------------------------------------------------------------------------------
for label, value, string_ok, integer_ok in (
        ("a plain string", Lit("x"), True, False), ("an xsd:string", Lit("x", XSD_STRING), True, False),
        ("an integer", Lit("5", XSD_INTEGER), False, True), ("an IRI", B, False, False),
        ("a blank node", BLANK, False, False), ("an ill-typed integer", Lit("abc", XSD_INTEGER), False, False),
        ("a boolean", Lit("true", XSD_BOOLEAN), False, False), ("a double", Lit("5.0E0", XSD_DOUBLE), False, False),
        ("a decimal", Lit("5.0", DECIMAL), False, False), ("a typed token", Lit("x", TOKEN), False, False)):
    case("datatype", f"xsd:string, {label}", on_p(datatype=XSD_STRING), one(value), *(() if string_ok else (A,)))
    case("datatype", f"xsd:integer, {label}", on_p(datatype=XSD_INTEGER), one(value), *(() if integer_ok else (A,)))
case("datatype", "a value of each datatype among several fails once", on_p(datatype=XSD_STRING),
     [(A, P, Lit("x")), (A, P, Lit("5", XSD_INTEGER))], A)

# -- sh:minInclusive and sh:maxInclusive ---------------------------------------------------------------------------------
for label, value, ok in (
        ("zero", Lit("0", XSD_INTEGER), True), ("five", Lit("5", XSD_INTEGER), True), ("minus one", Lit("-1", XSD_INTEGER), False),
        ("the maximum", Lit(str(MAX), XSD_INTEGER), True), ("one over the maximum", Lit(str(MAX + 1), XSD_INTEGER), False),
        ("a huge negative", Lit("-9999999999999999999999", XSD_INTEGER), False),
        ("a string of digits", Lit("5"), False), ("a double of five", Lit("5.0E0", XSD_DOUBLE), True),
        ("a decimal", Lit("5.5", DECIMAL), True), ("a NaN", Lit("NaN", XSD_DOUBLE), False),
        ("an IRI", B, False), ("a blank node", BLANK, False), ("a boolean", Lit("true", XSD_BOOLEAN), False),
        ("an ill-typed integer", Lit("x", XSD_INTEGER), False)):
    case("bounds", f"0 to 2^63-1, {label}", on_p(min_inclusive=0, max_inclusive=MAX), one(value), *(() if ok else (A,)))
case("bounds", "only a minimum, a value at it", on_p(min_inclusive=5), one(Lit("5", XSD_INTEGER)))
case("bounds", "only a minimum, a value under it", on_p(min_inclusive=5), one(Lit("4", XSD_INTEGER)), A)
case("bounds", "only a maximum, a value at it", on_p(max_inclusive=5), one(Lit("5", XSD_INTEGER)))
case("bounds", "only a maximum, a value over it", on_p(max_inclusive=5), one(Lit("6", XSD_INTEGER)), A)

# -- sh:pattern and the lengths --------------------------------------------------------------------------------------------
HEX4 = "^[0-9a-f]{4}$"
for label, value, ok in (
        ("a match", Lit("abcd"), True), ("one character too many", Lit("abcde"), False),
        ("a match with a trailing line feed", Lit("abcd\n"), True), ("an uppercase letter", Lit("abcD"), False),
        ("empty", Lit(""), False), ("an IRI that does not match", B, False), ("a blank node", BLANK, False),
        ("a typed token that matches", Lit("abcd", TOKEN), True), ("an integer whose lexical form matches", Lit("1234", XSD_INTEGER), True)):
    case("pattern", f"{HEX4}, {label}", on_p(pattern=HEX4), one(value), *(() if ok else (A,)))
case("pattern", "a pattern is a search: unanchored, it finds its text inside", on_p(pattern="bc"), one(Lit("abcd")))
case("pattern", "unanchored, a text without it fails", on_p(pattern="bc"), one(Lit("xyz")), A)
case("pattern", "the text of an IRI is matched", on_p(pattern="example[.]org"), one(B))
case("pattern", "an alternation in a group", on_p(pattern="^(0/1|-?[1-9][0-9]*/[1-9][0-9]*)$"), one(Lit("-3/4")))
case("pattern", "an alternation in a group, a miss", on_p(pattern="^(0/1|-?[1-9][0-9]*/[1-9][0-9]*)$"), one(Lit("03/4")), A)
for label, value, ok in (
        ("two", Lit("ab"), True), ("three", Lit("abc"), True), ("one", Lit("a"), True), ("four", Lit("abcd"), False),
        ("none", Lit(""), False), ("an IRI, which is long", B, False), ("a blank node", BLANK, False),
        ("an integer of two digits", Lit("12", XSD_INTEGER), True)):
    case("length", f"1 to 3, {label}", on_p(min_length=1, max_length=3), one(value), *(() if ok else (A,)))
case("length", "only a minimum, one short", on_p(min_length=2), one(Lit("a")), A)
case("length", "only a minimum, at it", on_p(min_length=2), one(Lit("ab")))
case("length", "only a maximum, one over", on_p(max_length=2), one(Lit("abc")), A)

# -- sh:in ------------------------------------------------------------------------------------------------------------------
WORDS = (Lit("a"), Lit("b"))
for label, value, ok in (
        ("a member", Lit("a"), True), ("another member", Lit("b"), True), ("a non-member", Lit("c"), False),
        ("a member typed as a token", Lit("a", TOKEN), False), ("an IRI", B, False), ("an integer", Lit("1", XSD_INTEGER), False)):
    case("in", f"two strings, {label}", on_p(in_=WORDS), one(value), *(() if ok else (A,)))
case("in", "two IRIs, a member", on_p(in_=(B, C)), one(B))
case("in", "two IRIs, a non-member", on_p(in_=(B, C)), one(Z), A)
case("in", "a mix of an IRI and a literal, the literal", on_p(in_=(B, Lit("a"))), one(Lit("a")))
case("in", "an integer in the list, the integer", on_p(in_=(Lit("5", XSD_INTEGER),)), one(Lit("5", XSD_INTEGER)))
case("in", "an integer in the list, its string", on_p(in_=(Lit("5", XSD_INTEGER),)), one(Lit("5")), A)
case("in", "an empty list holds nothing", on_p(in_=()), one(Lit("a")), A)
case("in", "every value of several must be in it", on_p(in_=WORDS), [(A, P, Lit("a")), (A, P, Lit("c"))], A)

# -- sh:nodeKind and sh:class --------------------------------------------------------------------------------------------------
case("nodeKind", "IRI, an IRI", on_p(node_kind="IRI"), one(B))
case("nodeKind", "IRI, a blank node", on_p(node_kind="IRI"), one(BLANK), A)
case("nodeKind", "IRI, a literal", on_p(node_kind="IRI"), one(Lit("x")), A)
case("class", "an instance", on_p(classes=(T1,)), [(A, P, B), (B, RDF_TYPE, T1)])
case("class", "an instance of another class", on_p(classes=(T1,)), [(A, P, B), (B, RDF_TYPE, T2)], A)
case("class", "an instance of one of two types", on_p(classes=(T1,)), [(A, P, B), (B, RDF_TYPE, T1), (B, RDF_TYPE, T2)])
case("class", "two classes, an instance of both", on_p(classes=(T1, T2)),
     [(A, P, B), (B, RDF_TYPE, T1), (B, RDF_TYPE, T2)])
case("class", "two classes, an instance of one", on_p(classes=(T1, T2)), [(A, P, B), (B, RDF_TYPE, T1)], A)
case("class", "a literal is no instance", on_p(classes=(T1,)), one(Lit("x")), A)
case("class", "a node with no type", on_p(classes=(T1,)), one(B), A)
case("class", "a type is not inherited from the node's other triples", on_p(classes=(T1,)), [(A, P, B), (B, Q, T1)], A)

# -- sh:minCount and sh:maxCount ----------------------------------------------------------------------------------------------------
case("count", "one to one, one value", on_p(min_count=1, max_count=1), one(Lit("x")))
case("count", "one to one, two values", on_p(min_count=1, max_count=1), [(A, P, Lit("x")), (A, P, Lit("y"))], A)
case("count", "one to one, the same value twice is one triple", on_p(min_count=1, max_count=1),
     [(A, P, Lit("x")), (A, P, Lit("x"))])
case("count", "a minimum of two, one value", on_p(min_count=2), one(Lit("x")), A)
case("count", "a minimum of two, two values", on_p(min_count=2), [(A, P, Lit("x")), (A, P, Lit("y"))])
case("count", "a minimum of one, none", Shape(id=S, targets=(("subjectsOf", Q),), props=(Shape(path=P, min_count=1),)),
     [(A, Q, Lit("x"))], A)
case("count", "a maximum of zero, one value", on_p(max_count=0), one(Lit("x")), A)
case("count", "a maximum of two, two values", on_p(max_count=2), [(A, P, Lit("x")), (A, P, Lit("y"))])
case("count", "a maximum of two, three values", on_p(max_count=2),
     [(A, P, Lit("x")), (A, P, Lit("y")), (A, P, Lit("z"))], A)

# -- sh:hasValue -------------------------------------------------------------------------------------------------------------------
case("hasValue", "a property: the value among others", on_p(has_value=(B,)), [(A, P, B), (A, P, C)])
case("hasValue", "a property: the value missing", on_p(has_value=(B,)), [(A, P, C)], A)
case("hasValue", "a property: two values wanted, one there", on_p(has_value=(B, C)), [(A, P, B)], A)
case("hasValue", "a property: two values wanted, both there", on_p(has_value=(B, C)), [(A, P, B), (A, P, C)])
case("hasValue", "a property: a literal", on_p(has_value=(Lit("x"),)), one(Lit("x")))
case("hasValue", "a property: a literal of another datatype", on_p(has_value=(Lit("5", XSD_INTEGER),)), one(Lit("5")), A)
case("hasValue", "a node shape: the focus node is it", Shape(id=S, targets=(("class", T1),), has_value=(A,)),
     [(A, RDF_TYPE, T1)])
case("hasValue", "a node shape: the focus node is another", Shape(id=S, targets=(("class", T1),), has_value=(A,)),
     [(B, RDF_TYPE, T1)], B)

# -- sh:closed -------------------------------------------------------------------------------------------------------------------------
CLOSED = Shape(id=S, targets=(("subjectsOf", P),), closed=True, ignored=(RDF_TYPE,), props=(Shape(path=P), Shape(path=Q)))
case("closed", "only the declared properties", CLOSED, [(A, P, Lit("x")), (A, Q, Lit("y")), (A, RDF_TYPE, T1)])
case("closed", "a property not declared", CLOSED, [(A, P, Lit("x")), (A, R, Lit("y"))], A)
case("closed", "the type is ignored by name", CLOSED, [(A, P, Lit("x")), (A, RDF_TYPE, T1), (A, RDF_TYPE, T2)])
case("closed", "the type is a property too, unless ignored",
     Shape(id=S, targets=(("subjectsOf", P),), closed=True, props=(Shape(path=P),)), [(A, P, Lit("x")), (A, RDF_TYPE, T1)], A)
case("closed", "a path that is an inverse declares no property",
     Shape(id=S, targets=(("subjectsOf", P),), closed=True, props=(Shape(path=P), Shape(path=inv(Q)))),
     [(A, P, Lit("x")), (A, Q, Lit("y"))], A)
case("closed", "properties allowed by ignoredProperties alone",
     Shape(id=S, targets=(("subjectsOf", P),), closed=True, ignored=(P, Q, RDF_TYPE)), [(A, P, Lit("x")), (A, Q, Lit("y"))])
case("closed", "a property that is only another node's is no matter",
     CLOSED, [(A, P, Lit("x")), (B, R, Lit("y"))])
case("closed", "a shape that is not closed allows any property",
     Shape(id=S, targets=(("subjectsOf", P),), props=(Shape(path=P),)), [(A, P, Lit("x")), (A, R, Lit("y"))])

# -- sh:or and sh:not ----------------------------------------------------------------------------------------------------------------------
ALT = (Shape(classes=(T1,)), Shape(classes=(T2,)))
case("or", "the first alternative", Shape(id=S, targets=(("subjectsOf", P),), or_=ALT), [(A, P, Lit("x")), (A, RDF_TYPE, T1)])
case("or", "the second alternative", Shape(id=S, targets=(("subjectsOf", P),), or_=ALT), [(A, P, Lit("x")), (A, RDF_TYPE, T2)])
case("or", "neither alternative", Shape(id=S, targets=(("subjectsOf", P),), or_=ALT), [(A, P, Lit("x")), (A, RDF_TYPE, T3)], A)
case("or", "both alternatives", Shape(id=S, targets=(("subjectsOf", P),), or_=ALT),
     [(A, P, Lit("x")), (A, RDF_TYPE, T1), (A, RDF_TYPE, T2)])
case("or", "on a property, an IRI or a string", on_p(or_=(Shape(datatype=XSD_STRING), Shape(in_=(B,)))), one(B))
case("or", "on a property, neither", on_p(or_=(Shape(datatype=XSD_STRING), Shape(in_=(B,)))), one(C), A)
case("or", "an alternative that is a datatype and a pattern together",
     on_p(or_=(Shape(datatype=XSD_STRING, pattern="^a$"), Shape(in_=(Lit("none"),)))), one(Lit("none")))
case("or", "that alternative, a string that is neither",
     on_p(or_=(Shape(datatype=XSD_STRING, pattern="^a$"), Shape(in_=(Lit("none"),)))), one(Lit("b")), A)
case("or", "an alternative with a nested property shape",
     Shape(id=S, targets=(("subjectsOf", P),), or_=(Shape(props=(Shape(path=Q, min_count=1),)), Shape(classes=(T1,)))),
     [(A, P, Lit("x")), (A, Q, Lit("y"))])
case("or", "an alternative with a nested property shape, neither", Shape(
    id=S, targets=(("subjectsOf", P),), or_=(Shape(props=(Shape(path=Q, min_count=1),)), Shape(classes=(T1,)))),
     [(A, P, Lit("x"))], A)
case("not", "the shape holds", Shape(id=S, targets=(("subjectsOf", P),), not_=(Shape(classes=(T1,)),)),
     [(A, P, Lit("x")), (A, RDF_TYPE, T1)], A)
case("not", "the shape does not hold", Shape(id=S, targets=(("subjectsOf", P),), not_=(Shape(classes=(T1,)),)),
     [(A, P, Lit("x"))])
case("not", "of an alternative", Shape(id=S, targets=(("subjectsOf", P),), not_=(Shape(or_=ALT),)),
     [(A, P, Lit("x")), (A, RDF_TYPE, T3)])
case("not", "of an alternative that holds", Shape(id=S, targets=(("subjectsOf", P),), not_=(Shape(or_=ALT),)),
     [(A, P, Lit("x")), (A, RDF_TYPE, T2)], A)
case("not", "on a property, a pattern", on_p(not_=(Shape(pattern="^file:"),)), one(B))
case("not", "on a property, a pattern that matches", on_p(not_=(Shape(pattern="^file:"),)), one(Lit("file:///x")), A)

# -- paths: the inverse, and one step or more ---------------------------------------------------------------------------------------
case("path", "an inverse path", Shape(id=S, targets=(("class", T1),), props=(Shape(path=inv(P), min_count=1),)),
     [(A, RDF_TYPE, T1), (B, P, A)])
case("path", "an inverse path with nothing pointing at the node",
     Shape(id=S, targets=(("class", T1),), props=(Shape(path=inv(P), min_count=1),)), [(A, RDF_TYPE, T1)], A)
case("path", "an inverse path counts each pointing node once",
     Shape(id=S, targets=(("class", T1),), props=(Shape(path=inv(P), max_count=1),)),
     [(A, RDF_TYPE, T1), (B, P, A), (C, P, A)], A)
ROOTED = Shape(props=(Shape(path=inv(Q), min_count=1),))
REACH = Shape(id=S, targets=(("class", T1),), props=(Shape(path=one_or_more(inv(P)), qvs=((ROOTED, 1),)),))
case("path", "reached from a root by one step", REACH, [(A, RDF_TYPE, T1), (C, P, A), (B, Q, C)])
case("path", "reached from a root by two", REACH, [(A, RDF_TYPE, T1), (EX + "m", P, A), (C, P, EX + "m"), (B, Q, C)])
case("path", "reached from a root by three", REACH,
     [(A, RDF_TYPE, T1), (EX + "m", P, A), (EX + "n", P, EX + "m"), (C, P, EX + "n"), (B, Q, C)])
case("path", "not reached from a root", REACH, [(A, RDF_TYPE, T1), (C, P, EX + "other"), (B, Q, C)], A)
case("path", "a cycle that holds no root", REACH, [(A, RDF_TYPE, T1), (C, P, A), (A, P, C)], A)
case("path", "a cycle that holds a root", REACH, [(A, RDF_TYPE, T1), (C, P, A), (A, P, C), (B, Q, C)])
case("path", "the node itself is a root, which one step does not reach", REACH, [(A, RDF_TYPE, T1), (B, Q, A)], A)
case("path", "one step or more of a direct path",
     Shape(id=S, targets=(("class", T1),), props=(Shape(path=one_or_more(P), has_value=(Z,)),)),
     [(A, RDF_TYPE, T1), (A, P, B), (B, P, C), (C, P, Z)])
case("path", "one step or more, the value not reached",
     Shape(id=S, targets=(("class", T1),), props=(Shape(path=one_or_more(P), has_value=(Z,)),)),
     [(A, RDF_TYPE, T1), (A, P, B), (B, P, C)], A)
case("path", "a qualified value shape needs a minimum of two",
     Shape(id=S, targets=(("class", T1),), props=(Shape(path=P, qvs=((Shape(classes=(T2,)), 2),)),)),
     [(A, RDF_TYPE, T1), (A, P, B), (A, P, C), (B, RDF_TYPE, T2), (C, RDF_TYPE, T2)])
case("path", "a qualified value shape, one short",
     Shape(id=S, targets=(("class", T1),), props=(Shape(path=P, qvs=((Shape(classes=(T2,)), 2),)),)),
     [(A, RDF_TYPE, T1), (A, P, B), (A, P, C), (B, RDF_TYPE, T2)], A)

# -- targets ---------------------------------------------------------------------------------------------------------------------------
case("target", "a class: its instances are focus", Shape(id=S, targets=(("class", T1),), props=(Shape(path=P, min_count=1),)),
     [(A, RDF_TYPE, T1), (B, RDF_TYPE, T1), (B, P, Lit("x")), (C, RDF_TYPE, T2)], A)
case("target", "subjects of a property: a blank node is one",
     Shape(id=S, targets=(("subjectsOf", P),), node_kind="IRI"), [(BLANK, P, B)], "_:blank")
case("target", "objects of a property: an IRI", Shape(id=S, targets=(("objectsOf", P),), node_kind="IRI"), [(A, P, B)])
case("target", "objects of a property: a literal is a focus node",
     Shape(id=S, targets=(("objectsOf", P),), node_kind="IRI"), [(A, P, Lit("x"))], "x")
case("target", "objects of a property: a blank node is a focus node",
     Shape(id=S, targets=(("objectsOf", P),), node_kind="IRI"), [(A, P, BLANK)], "_:blank")
case("target", "a node the graph holds nothing of is a focus node",
     Shape(id=S, targets=(("node", Z),), props=(Shape(path=P, min_count=1),)), [(A, P, Lit("x"))], Z)
case("target", "a node the graph holds is a focus node",
     Shape(id=S, targets=(("node", A),), props=(Shape(path=P, min_count=1),)), [(A, P, Lit("x"))])
case("target", "a focus node reached by two targets is judged once",
     Shape(id=S, targets=(("subjectsOf", P), ("subjectsOf", Q)), props=(Shape(path=P, max_count=1),)),
     [(A, P, Lit("x")), (A, Q, Lit("y")), (A, P, Lit("z"))], A)
case("target", "a shape with no focus node has no result", Shape(id=S, targets=(("class", T3),), node_kind="IRI"),
     [(A, P, Lit("x"))])
case("target", "a shape with no target has no result", Shape(id=S, node_kind="IRI"), [(BLANK, P, Lit("x"))])
case("target", "two shapes are judged apart",
     (Shape(id=S, targets=(("subjectsOf", P),), props=(Shape(path=P, max_count=1),)),
      Shape(id=S + "2", targets=(("subjectsOf", Q),), props=(Shape(path=Q, min_count=2),))),
     [(A, P, Lit("x")), (A, P, Lit("y")), (B, Q, Lit("x"))], (S, A), (S + "2", B))

# -- levels ------------------------------------------------------------------------------------------------------------------------------
for level in ("must", "should", "may"):
    case("level", f"a {level}-level shape fails like any other",
         Shape(id=S, level=level, targets=(("subjectsOf", P),), props=(Shape(path=Q, min_count=1),)), [(A, P, Lit("x"))], A)

# -- a shape with several constraints holds all of them ---------------------------------------------------------------------------------------
case("several", "datatype, pattern and length together, all hold",
     on_p(datatype=XSD_STRING, pattern="^[a-z]+$", min_length=2, max_length=4), one(Lit("abc")))
case("several", "datatype, pattern and length together, the pattern fails",
     on_p(datatype=XSD_STRING, pattern="^[a-z]+$", min_length=2, max_length=4), one(Lit("ab1")), A)
case("several", "datatype, pattern and length together, the length fails",
     on_p(datatype=XSD_STRING, pattern="^[a-z]+$", min_length=2, max_length=4), one(Lit("abcde")), A)
case("several", "datatype, pattern and length together, the datatype fails",
     on_p(datatype=XSD_STRING, pattern="^[0-9]+$", min_length=1, max_length=4), one(Lit("12", XSD_INTEGER)), A)
case("several", "a node kind with a class", Shape(id=S, targets=(("class", T1),), node_kind="IRI", classes=(T1,)),
     [(A, RDF_TYPE, T1), (BLANK, RDF_TYPE, T1)], "_:blank")
