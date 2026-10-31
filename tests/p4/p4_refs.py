"""References outside the id rule, on each term of spelling `ref` (P4, after the lead's ruling of 2026-10-19T17:41:46Z: the
shapes of those terms claim `graph-form` too, which FORM has held for every must shape since 2026-10-26T11:18:27Z). A
reference whose id is outside FORMAT.md item 22's forms is refused `graph-form` by the checker where it is no absolute IRI,
since no entity's @id can then be it (`_:b0`, `./x`), and `spelling` where it reads as one (`schema:a`). A real engine reads
`_:b0` as a blank node, which a `ref` term's shape refuses on a crate the evaluator cannot read and the checker has refused
first. These helpers make the crates that hold the claim to that: the fixture's metadata with one reference of each kind
added, on each such term, on a host its domain admits. Nothing here is a test: pytest's naming decides what is one, and a
helper under tests/ names no function `test*` and no class `Test*` (CLAUDE.md).

  - `BAD`: the references, by kind, and `ACCEPTED`: those of them that are absolute IRIs, which the reader accepts as references;
  - `ref_terms()`: the table's terms of spelling `ref`;
  - `crate_with(pristine, term, reference)`: the metadata with the reference added to the term's valid values.

Used by tests/p4/test_p4_refs.py (a few of them, without an engine) and tests/p4shacl/test_p4shacl_refs.py (all of them, through
pyshacl).
"""
import copy

from qro import canonical
from qro import p4_examples as X
from qro import vocabulary as V

UNNAMED = ("_:b0", "./x", "a//b", "//x", "/x", "a/../b", "x?q", "@x", "#", "x y")   # no form of the rule: `graph-form`, it names no entity
NO_ENTITY = ("#nowhere", "nowhere/")                                             # a form of the rule that no entity holds: `graph-form`
IRI_LIKE = ("schema:a", "C:/x")                                                   # read as an IRI, which the reader refuses `spelling`
ACCEPTED = ("https://example.org/x", "urn:x:y")                                  # absolute IRIs: no must shape may fail on these
BAD = UNNAMED + NO_ENTITY + IRI_LIKE + ACCEPTED


def ref_terms():
    """The table's terms whose spelling is `ref`."""
    return [t for t in V.TERMS if t.spelling == "ref"]


def host_of(t, graph):
    """The entity a term of this table is put on: the one its domain names (the descriptor for `about`, the root for
    `conformsTo`), made if the crate has none."""
    where = X.ENTANGLED.get(t.key, ("spelling", t.domain[0]))[1]
    return X.host_for(where, graph, X.HOST)


def crate_with(pristine, t, reference):
    """`pristine`'s metadata with `{"@id": reference}` added to the term's valid references (several if it takes a list,
    else it is the term's value), in the graph's order again, as a plant's is."""
    md = copy.deepcopy(pristine)
    host = host_of(t, md["@graph"])
    have = host.get(t.key)
    if t.many:
        have = have if isinstance(have, list) else [] if have is None else [have]
        host[t.key] = sorted(have + [{"@id": reference}], key=canonical.sort_key)
    else:
        host[t.key] = {"@id": reference}
    return X.arranged(md)
