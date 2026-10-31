"""The three things the evaluator and pyshacl read differently (limit 23; the first two a note of P4's second verifier, round 2,
found by 28,000 random shapes over random graphs, of which these were the only disagreements; the third a note of the fourth
verifier, MEASURED). The generated shapes use neither of the first two (tests/p4/test_p4_shapes.py), and no crate reaches the
third's forms (the same file), so nothing the tests judge turns on them; this stage holds them as they are, so that an engine that
moves is noticed and the limit is restated, and holds every neighbour of them where the two agree:
  - `sh:minLength 0` on a blank node, as a node shape and as a property shape: the evaluator fails it, since a blank node has no
    string to measure (the Recommendation's section 4.4.1, READ in an extraction), and pyshacl 0.40.1 passes it; a bound of 1 or 2,
    and `sh:maxLength`, fail alike;
  - `sh:maxInclusive` with no `sh:minInclusive`, against a boolean literal, as a node shape and as a property shape: the
    evaluator fails it, and pyshacl passes it (BELIEVED the evaluator is right, from SPARQL's comparison rules, not re-read); with
    its pair, with `sh:minInclusive` alone, and against an integer, they agree;
  - the lexical form of an xsd:integer literal, on the committed shape of `qro:shots`, which uses `sh:datatype xsd:integer`: the
    evaluator calls a form ill-formed unless it is an optional sign and ASCII digits, and fails the shape; pyshacl accepts every
    form Python's int() reads (rdflib 7.6.0 maps an integer with int() and calls a literal well formed when it has a value, READ in
    rdflib/term.py): white space, an underscore between digits, the digits of other scripts. Every form int() does not read, and the
    forms in XSD's own lexical space, they judge alike."""
import pytest
from p4shacl_helpers import run_engine, shape_files
from qro import p4_eval, p4_turtle
from qro import p4_shapes as H
from qro.p4_model import XSD_BOOLEAN, XSD_INTEGER, BNode, Lit, Shape

EX = "http://example.org/"
P = EX + "p"
PREFIXES = (("sh", "http://www.w3.org/ns/shacl#"), ("ex", EX), ("qs", EX + "shapes#"))
INT_MAX = 9223372036854775807
VALUES = {"true": Lit("true", XSD_BOOLEAN), "false": Lit("false", XSD_BOOLEAN), "1 as a boolean": Lit("1", XSD_BOOLEAN),
          "a string": Lit("5"), "an integer in the bound": Lit("5", XSD_INTEGER), "an integer outside it": Lit("-5", XSD_INTEGER)}


def length_cases():
    out = []
    for where in ("node", "property"):
        for kw in ({"min_length": 0}, {"min_length": 1}, {"min_length": 2}, {"max_length": 0}, {"max_length": 5}):
            if where == "node":
                s, data = Shape(id=EX + "shapes#S", targets=(("subjectsOf", P),), **kw), [(BNode(1), P, Lit("v"))]
            else:
                s, data = Shape(id=EX + "shapes#S", targets=(("subjectsOf", P),), props=(Shape(path=P, **kw),)), [(EX + "a", P, BNode(1))]
            out.append((f"{where} {kw}", s, data))
    return out


def bound_cases():
    out = []
    for where in ("node", "property"):
        for kw in ({"min_inclusive": 0}, {"max_inclusive": INT_MAX}, {"min_inclusive": 0, "max_inclusive": 9}):
            for label, value in VALUES.items():
                if where == "node":
                    s = Shape(id=EX + "shapes#S", targets=(("objectsOf", P),), **kw)
                else:
                    s = Shape(id=EX + "shapes#S", targets=(("subjectsOf", P),), props=(Shape(path=P, **kw),))
                out.append((f"{where} {kw} against {label}", s, [(EX + "a", P, value)]))
    return out


CASES = length_cases() + bound_cases()


@pytest.fixture(scope="module")
def readings():
    """{case label: (the evaluator fails it, pyshacl fails it)}, one engine run for all."""
    jobs = [{"id": str(i), "kind": "graph", "shapes": p4_turtle.render([s], PREFIXES, ["x"]), "data": p4_turtle.ntriples(d)}
            for i, (_, s, d) in enumerate(CASES)]
    answers, versions = run_engine(jobs)
    assert versions == {"pyshacl": "0.40.1", "rdflib": "7.6.0"}
    out = {}
    for i, (label, s, d) in enumerate(CASES):
        assert answers[str(i)]["ok"], (label, answers[str(i)].get("error"))
        out[label] = (bool(p4_eval.validate([s], d)), bool(answers[str(i)]["results"]))
    return out


def test_the_evaluator_fails_minLength_0_on_a_blank_node_and_pyshacl_passes_it(readings):
    got = {label: pair for label, pair in readings.items() if "'min_length': 0" in label}
    assert got == {"node {'min_length': 0}": (True, False), "property {'min_length': 0}": (True, False)}


def test_the_evaluator_fails_maxInclusive_alone_against_a_boolean_and_pyshacl_passes_it(readings):
    got = {label: pair for label, pair in readings.items() if pair[0] != pair[1] and "min_length" not in label}
    booleans = ("true", "false", "1 as a boolean")
    assert got == {f"{where} {{'max_inclusive': {INT_MAX}}} against {value}": (True, False)
                   for where in ("node", "property") for value in booleans}


def test_everywhere_else_among_these_cases_the_two_agree_and_each_construct_is_failed_by_something(readings):
    other = {label: pair for label, pair in readings.items() if "'min_length': 0" not in label
             and not (f"{{'max_inclusive': {INT_MAX}}} against" in label and any(b in label for b in ("true", "false", "boolean")))}
    assert len(readings) == 10 + 36 and len(other) == len(readings) - 2 - 6
    assert [label for label, (ev, eng) in other.items() if ev != eng] == []
    assert sum(ev for ev, _ in other.values()) >= 25 and sum(not ev for ev, _ in other.values()) >= 6           # 30 and 8 when it was written


# -- the lexical form of an integer (limit 23, the third thing) -------------------------------------------------------------
SUBJECT = "file:///crate/x"
DIFFER = {                      # forms Python's int() reads and XSD's lexical space (an optional sign and ASCII digits) may not
    "a leading space": " 1", "a trailing space": "1 ", "a tab and a line feed around": chr(9) + "1" + chr(10),
    "an underscore between digits": "1_0", "an Arabic-Indic digit one": chr(0x661), "a fullwidth digit one": chr(0xFF11),
    "an Arabic-Indic digit zero": chr(0x660), "a Devanagari digit zero": chr(0x966), "a no-break space": chr(0xA0) + "1",
    "a carriage return": "1" + chr(13), "a vertical tab": chr(11) + "1"}
AGREE = {                       # in XSD's lexical space, or outside it and outside what int() reads: the two judge alike
    "1": "1", "0": "0", "a plus sign": "+1", "a leading zero": "01", "minus zero": "-0", "the largest": str(INT_MAX),
    "one more": str(INT_MAX + 1), "minus one": "-1", "a fraction": "1.0", "an exponent": "1e0", "nothing": "", "letters": "abc",
    "hex": "0x1", "two signs": "--1", "a plus and a minus": "+-1", "two underscores": "1__0", "a leading underscore": "_1",
    "a trailing underscore": "1_", "a zero width space": "1" + chr(0x200B)}


@pytest.fixture(scope="module")
def integer_readings():
    """{form: (the evaluator fails the committed shape of qro:shots on a literal of it, pyshacl does)}, one engine run for all."""
    shape = next(s for s in H.build() if s.id == H.shape_iri("term-qro-shots"))
    predicate = H.term_iri("qro:shots")
    forms = {**DIFFER, **AGREE}
    triples = {name: [(SUBJECT, predicate, Lit(form, XSD_INTEGER))] for name, form in forms.items()}
    jobs = [{"id": name, "kind": "graph", "shapes": shape_files(), "data": p4_turtle.ntriples(t), "use_shapes": [shape.id]}
            for name, t in triples.items()]
    answers, versions = run_engine(jobs)
    assert versions == {"pyshacl": "0.40.1", "rdflib": "7.6.0"}
    out = {}
    for name, t in triples.items():
        assert answers[name]["ok"], (name, answers[name].get("error"))
        out[name] = (bool(p4_eval.failing(p4_eval.validate([shape], t), "must")), not answers[name]["conforms"])
    return out


def test_the_evaluator_fails_an_integer_form_xsd_may_not_have_and_pyshacl_accepts_it(integer_readings):
    assert {name: integer_readings[name] for name in DIFFER} == {name: (True, False) for name in DIFFER}


def test_the_two_judge_alike_every_form_in_xsds_lexical_space_and_every_form_int_does_not_read(integer_readings):
    assert [name for name in AGREE if integer_readings[name][0] != integer_readings[name][1]] == []
    assert {name for name in AGREE if not integer_readings[name][0]} == {"1", "0", "a plus sign", "a leading zero", "minus zero",
                                                                          "the largest"}        # and these are the forms both accept
