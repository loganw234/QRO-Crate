"""P1's twin, the second positive example of the profile (P4's design, item 6, the example table's "P1's twin", and D8; P4.3).

The twin is built by P1.2's adapter through P1.2's toolkit (controls/plants_p1.py), at stage time, once in a process, in the
system's temporary files: it is never copied into profile/ (0.74 MB, and IBM's result text of four jobs: NOTICE.md). The checker
accepts it by the plain command line, which the `p1` stage holds and tests/p4/test_p4_twin.py holds again for the profile; the
shapes' half is here and in tests/p4shacl/test_p4shacl_twin.py: the evaluator and a real engine read its metadata, and every must
shape conforms.

There are two twins, because P1.2 merged with P2's module present (docs/P1.md, "The twin and the controls"):
  - `p1-twin`, as the tree builds it: P2's question/law.json and P2's entities (the measurements, the contrasts, the holds), so the
    first crate to carry P2's terms into P4's shapes outside a plant; it carries every term of the table;
  - `p1-twin-alone`, as P1 builds it with P2's module absent (`pristine_twin_alone`): no question file, none of P2's entities.
TWINS is the list of both, which the tests of both stages read; a test names the two again, so that a twin left out of it fails.

Nothing here is a test: pytest's naming decides what is one, and a helper under tests/ names no function `test*` and no class
`Test*` (CLAUDE.md)."""
import json
from pathlib import Path

from qro import canonical

TWINS = (("p1-twin", "pristine_twin"), ("p1-twin-alone", "pristine_twin_alone"))


def names():
    return [name for name, _ in TWINS]


def crate_of(name):
    """The built twin called `name` (one build in the process, in a directory nothing writes to again)."""
    from controls import plants_p1                      # imported as it is asked for: it builds nothing when imported
    return Path(getattr(plants_p1, dict(TWINS)[name])())


def metadata_of(name):
    return json.loads((crate_of(name) / canonical.DESCRIPTOR).read_bytes())


def file_count(name):
    return sum(1 for p in crate_of(name).rglob("*") if p.is_file())
