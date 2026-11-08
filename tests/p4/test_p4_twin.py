"""P1's twin as the profile's second positive example (P4's design, item 6, the example table's "P1's twin", and D8; P4.3): built by
P1.2's adapter through P1.2's toolkit at stage time (tests/p4/p4_twin.py), never copied into profile/, accepted by the plain command
line, and conforming to every must shape in the evaluator. The engine's half is tests/p4shacl/test_p4shacl_twin.py.

There are two twins: as the tree builds it, with P2's module present (74 files, the first crate to carry P2's terms into P4's shapes
outside a plant), and as P1 alone builds it (73). Both are held, each in the checker and in the shapes, and the shapes are held to
have looked: a shape that has no focus node on a crate conforms to it for nothing, so the test says which shapes the twin reaches.
With P2's module present, the twin reaches every shape of the profile (MEASURED at the build: 131 must shapes, 8 should, and every
one of the 63 terms of the table carried); without it, the shapes of the 20 terms it lacks have nothing to read (P2's 19, and P0's
`qro:implementation`, which only P2's entities carry)."""
import dataclasses
import os
import subprocess
import sys

import p4_twin
import pytest
from p4_helpers import ROOT, must_failing
from qro import checker, p4_eval, p4_expand
from qro import p4_examples as X
from qro import p4_shapes as H
from qro import vocabulary as V
from qro.p4_model import Shape

SHAPES = H.build()
OWNED_BY = {"P0", "P1", "P2"}                       # the parcels whose terms the twins can carry: a later parcel's shapes may have no focus


def triples_of(name):
    return p4_expand.expand(p4_twin.metadata_of(name))


def term_of(shape):
    """The term of the table a shape was made from (`term-`, `domain-` and `absence-` shapes), or None for a structural shape."""
    local = X.local(shape.id)
    for prefix in ("term-", "domain-", "absence-"):
        if local.startswith(prefix):
            rest = local[len(prefix):]
            for t in V.TERMS:
                if rest == H.slug(t.key) or (prefix == "absence-" and rest.startswith(H.slug(t.key) + "-")):
                    return t
    return None


def reached(name):
    """(the shapes with a focus node on twin `name`, the shapes with none), by local name."""
    g = p4_eval.Graph(triples_of(name))
    yes = sorted(X.local(s.id) for s in SHAPES if p4_eval.focus_nodes(g, s))
    no = sorted(X.local(s.id) for s in SHAPES if not p4_eval.focus_nodes(g, s))
    return yes, no


# -- which twins are examples ------------------------------------------------------------------------------------------------
def test_the_examples_are_the_twin_as_the_tree_builds_it_and_the_twin_as_p1_builds_it_alone():
    """Named again here, and not read from the list: a twin left out of TWINS, which both stages read, fails this."""
    assert p4_twin.names() == ["p1-twin", "p1-twin-alone"]
    assert dict(p4_twin.TWINS) == {"p1-twin": "pristine_twin", "p1-twin-alone": "pristine_twin_alone"}
    from controls import plants_p1
    for builder in dict(p4_twin.TWINS).values():
        assert callable(getattr(plants_p1, builder))


def test_the_twin_is_built_at_stage_time_and_nothing_of_it_is_under_profile():
    """D8: the twin is never committed under profile/ (0.74 MB, IBM's result text of four jobs, a NOTICE entry). It is built in the
    system's temporary files by the toolkit, so no copy of it is anywhere in the tree the generator renders."""
    crate = p4_twin.crate_of("p1-twin")
    assert crate.is_dir() and ROOT not in crate.parents and not (ROOT / "profile" / "examples" / "p1-twin").exists()
    assert sorted(p.name for p in (ROOT / "profile" / "examples").iterdir()) == ["fixture"]


def test_the_twin_with_p2_holds_p2s_files_and_entities_and_the_twin_alone_holds_none_of_them():
    with_p2, alone = p4_twin.metadata_of("p1-twin"), p4_twin.metadata_of("p1-twin-alone")

    def keys_and_types(md):
        from qro import canonical
        return ({k for e in md["@graph"] for k in e if k not in ("@id", "@type")}, {t for e in md["@graph"] for t in canonical.types(e)})
    keys, types = keys_and_types(with_p2)
    keys_alone, types_alone = keys_and_types(alone)
    p2_terms = {t.key for t in V.TERMS if t.owner == "P2"}
    p2_types = {t.key for t in V.TYPES if t.owner == "P2"}
    assert p2_terms and p2_types >= {"qro:Measurement", "qro:Contrast", "qro:Hold"}
    assert p2_terms <= keys and p2_types <= types                        # carried: the first crate to carry them outside a plant
    assert not (p2_terms & keys_alone) and not (p2_types & types_alone)  # and absent where P2's module is
    assert p4_twin.file_count("p1-twin") > p4_twin.file_count("p1-twin-alone") > 60


def test_the_matrix_and_the_description_name_both_twins_as_positive_examples_and_the_committed_files_are_the_rendered_ones():
    """The twin's place among the examples (docs/P4.md): a row for each of the two in the matrix of profile/EXAMPLES.md, under the
    positive examples and before the plants, and a sentence in the description; and the files committed under profile/ are the bytes
    the generator renders, so the rows are the committed ones."""
    from qro import p4_profile as P
    rendered = P.render()
    matrix = rendered["EXAMPLES.md"].decode("ascii")
    positive = matrix.split("## Positive examples", 1)[1].split("## Plants", 1)[0]
    for name in p4_twin.names():
        assert f"(`{name}`)" in positive, name
        assert sum(f"`{name}`" in line for line in positive.splitlines()) == 1
    assert "accepted by `python -m qro check`" in positive and "never kept here" in positive
    description = rendered["README.md"].decode("ascii")
    assert "P1's twin, a slice of real IBM records that P1's adapter builds at stage time and that is not kept here" in description
    assert (ROOT / "profile" / "EXAMPLES.md").read_bytes() == rendered["EXAMPLES.md"]
    assert (ROOT / "profile" / "README.md").read_bytes() == rendered["README.md"]


# -- the checker's half, held again for the profile ------------------------------------------------------------------------------
@pytest.mark.parametrize("name", p4_twin.names())
def test_the_plain_checker_accepts_the_twin(name):
    """In process, with every parcel's steps loaded and the fixture's raw form not (X.checker_verdict, the walk over the other
    parcels' plants has the same): `accepted`. The `p1` stage holds the same of the twin on its own; this is the profile's copy."""
    checker.load()
    assert X.checker_verdict(p4_twin.crate_of(name)) == "accepted"


@pytest.mark.parametrize("name", p4_twin.names())
def test_the_command_line_accepts_the_twin_as_a_process(name):
    """`python -m qro check` with no flag, as a process: exit 0 and no REFUSED line (the fixture, by contrast, is refused
    `step-unbuilt` without --fixtures)."""
    done = subprocess.run([sys.executable, "-m", "qro", "check", str(p4_twin.crate_of(name))], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    assert done.returncode == 0 and "REFUSED" not in done.stdout + done.stderr, (done.returncode, done.stdout[-300:], done.stderr[-300:])


# -- the shapes' half ----------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", p4_twin.names())
def test_the_expansion_reads_the_twin_and_every_must_and_should_shape_conforms(name):
    """The checker accepts the twin, so no must shape may fail on it (the rule of P4's shapes: a shape never claims more than the
    checker holds), and the should-level shapes, which say what a careful crate carries, are silent on it too."""
    triples = triples_of(name)
    assert len(triples) > 500
    results = p4_eval.validate(SHAPES, triples)
    assert [(r.shape, r.focus, r.reason) for r in results] == []
    assert must_failing(SHAPES, triples) == set()


def keys_of(name):
    return {k for e in p4_twin.metadata_of(name)["@graph"] for k in e if k not in ("@id", "@type")}


def test_the_twin_with_p2_gives_every_shape_a_node_to_read_and_the_twin_alone_lacks_the_shapes_of_the_terms_it_lacks():
    """A shape with no focus node conforms for nothing. With P2's module present the twin is read by every structural shape and by
    every shape made from a term of P0, P1 or P2, for it carries each of them. Alone, the shapes with nothing to read are the shapes
    (term, domain, absence) of the terms it does not carry, which include all of P2's, and no structural shape."""
    yes, no = reached("p1-twin")
    unread = [s for s in SHAPES if X.local(s.id) in no]
    assert yes and [X.local(s.id) for s in unread if term_of(s) is None or term_of(s).owner in OWNED_BY] == []
    yes_alone, no_alone = reached("p1-twin-alone")
    lacks = {t.key for t in V.TERMS} - keys_of("p1-twin-alone")
    assert {t.key for t in V.TERMS if t.owner == "P2"} <= lacks
    assert sorted(no_alone) == sorted(X.local(s.id) for s in SHAPES if term_of(s) is not None and term_of(s).key in lacks)
    assert len(no_alone) >= 39 and len(yes_alone) + len(no_alone) == len(SHAPES)


def test_the_twin_with_p2_carries_every_term_of_the_table():
    md = p4_twin.metadata_of("p1-twin")
    keys = {k for e in md["@graph"] for k in e if k not in ("@id", "@type")}
    missing = sorted(t.key for t in V.TERMS if t.owner in OWNED_BY and t.key not in keys)
    assert missing == []


def stricter_on(key):
    """The shapes with a must shape added that fails on any entity that carries term `key`: a shape that has gone stricter than the
    checker, on a term of the table."""
    iri = H.term_iri(key)
    never = Shape(id=H.shape_iri("twin-stricter-" + H.slug(key)), targets=(("subjectsOf", iri),),
                  props=(Shape(path=iri, max_count=0),), claims=("spelling",))
    return list(SHAPES) + [never], X.local(never.id)


@pytest.mark.parametrize("key", ["qro:value", "qro:exactHold", "qro:measure", "qro:rawForm", "name"])
def test_a_shape_gone_stricter_than_the_checker_on_a_term_the_twin_carries_is_found_on_it(key):
    """The control: the twin is read, not skipped. A must shape that forbids a term the twin carries fails on the twin with P2's
    module, for a term of P2's (`qro:value`, `qro:exactHold`, `qro:measure`) as for one of P1's and P0's."""
    shapes, local = stricter_on(key)
    assert local in must_failing(shapes, triples_of("p1-twin"))
    assert local not in must_failing(list(SHAPES), triples_of("p1-twin"))


def test_a_shape_made_stricter_on_a_term_of_p2_is_found_on_the_twin_with_p2_and_not_on_the_twin_alone():
    shapes, local = stricter_on("qro:value")
    assert local in must_failing(shapes, triples_of("p1-twin"))
    assert local not in must_failing(shapes, triples_of("p1-twin-alone"))


def test_a_term_shape_made_to_admit_nothing_is_found_on_the_twin_that_carries_the_term():
    """The shapes the twin reads are the shapes of the profile: one of them made to admit nothing (`qro:measure`'s list of words
    emptied, a list nothing is in) so that a value the twin carries no longer conforms fails the twin."""
    target = next(s for s in SHAPES if X.local(s.id) == "term-qro-measure")
    broken = dataclasses.replace(target, props=(dataclasses.replace(target.props[0], in_=()),) + target.props[1:])
    assert broken != target and target.props[0].in_
    shapes = [broken if s.id == target.id else s for s in SHAPES]
    assert "term-qro-measure" in must_failing(shapes, triples_of("p1-twin"))
    assert "term-qro-measure" not in must_failing(shapes, triples_of("p1-twin-alone"))
