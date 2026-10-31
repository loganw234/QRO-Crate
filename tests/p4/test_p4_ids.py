"""The expansion against the reader's ids, without an engine (P4's verifier, round 1, defect 1, after P0.5; the lead's ruling of
2026-10-16T14:58:58Z). The reader (FORMAT.md item 22) admits an @id in four forms; the evaluator reads the triples of
qro/p4_expand.py. So that the evaluator's silence on a crate is never the checker's, held here:
  - the expansion reads every id the reader accepts, and makes distinct IRIs of distinct ids;
  - every id the expansion refuses to read, the reader refuses (so a crate it cannot read is a crate the checker has refused);
  - the prefixes it reads are the ones the reader refuses.
That the IRIs are the ones rdflib makes is the engine stage's (tests/p4shacl/test_p4shacl_ids.py). The ids are drawn by
tests/p4/p4_ids.py, and the reader's own function is the oracle."""
import re
from collections import Counter

import pytest
from p4_ids import IRI_CHARS, accepted, candidates, crate_of, drawn_ids, small, unread
from p4_ids import collisions as collided
from qro import p4_expand as E
from qro import spelling as S
from qro import vocabulary as V

DRAWN = 30000
STRINGS = candidates(3, DRAWN) + list(small())
IDS = accepted(STRINGS)


def test_the_draw_is_tens_of_thousands_of_strings_the_reader_accepts_and_as_many_it_refuses_by_a_character():
    assert len(IDS) >= 18000 and len(STRINGS) - len(IDS) >= 15000
    assert IDS == drawn_ids(DRAWN)
    assert all(S.id_problem(i) is None for i in IDS) and "./" in IDS


def test_the_draw_reaches_the_four_forms_every_character_of_an_iri_and_the_shapes_that_have_bitten():
    kinds = Counter("root" if i == "./" else "fragment" if i.startswith("#") else "absolute" if ":" in i else "path" for i in IDS)
    assert kinds["root"] == 1 and kinds["path"] >= 6000 and kinds["absolute"] >= 5000 and kinds["fragment"] >= 3000, kinds
    assert set(IRI_CHARS + "%#") <= set("".join(IDS))
    assert {"./", "#:", "#a:0", "#0:a", "a;a", ";a", "a@", "a/a/", "0.a"} <= set(IDS)      # short ones, from the small alphabet
    paths = [i for i in IDS if ":" not in i and not i.startswith("#")]
    assert sum(";" in i for i in paths) >= 1000 and sum("@" in i for i in paths) >= 1000 and sum(i.endswith("/") for i in paths) >= 1000
    assert sum(i.startswith("#") and ":" in i for i in IDS) >= 300                            # the gap the first run found
    assert sum(bool(re.search(r"%[0-9a-f]{2}", i)) for i in IDS) >= 1000 and sum(bool(re.search(r"%[0-9A-F]{2}", i)) for i in IDS) >= 1000
    assert sum("/../" in i or "/./" in i for i in IDS if ":" in i) >= 200                     # an absolute IRI keeps a dot segment
    assert {i.split(":")[0] for i in IDS if ":" in i and not i.startswith("#")} >= {"https", "http", "urn", "mailto", "tel", "ssh"}


def test_the_expansion_reads_every_id_the_reader_accepts():
    assert unread(IDS) == []


def test_distinct_ids_the_reader_accepts_are_distinct_iris_in_the_expansion():
    assert collided(IDS) == {}


def test_every_id_the_expansion_refuses_the_reader_refuses():
    refused = unread(STRINGS)
    assert len(refused) >= 5000                                         # the draw reaches what the expansion refuses
    assert [(i, why) for i, why in refused if S.id_problem(i) is None] == []


@pytest.mark.parametrize("given", [
    "_:b0", "//example.org/x", "a/../b", "a/./b", "../a", "a//b", "a?q", "x#", "#", "a b", "file:///elsewhere/x", "FILE:///x",
    "file:x", "1a:b", ":x", "a/b#c:d", "/abs/path", "a\b", "@x", "@", "@x/y", "@0", "./x", ".", "..", "x#a", "HTTPS://x/y"])
def test_an_id_rdflib_reads_otherwise_is_refused_by_the_reader_and_most_by_the_expansion_too(given):
    assert S.id_problem(given) is not None                              # the reader's, whatever the expansion makes of it
    if given not in ("x#a", "HTTPS://x/y"):          # these two it reads as JSON-LD does: a path and a fragment, an IRI as written
        with pytest.raises(E.ExpandError):
            E.iri_of_id(given)


def test_the_prefixes_the_expansion_reads_are_the_ones_the_reader_refuses():
    assert set(E.prefixes()) == set(V.CONTEXT_PREFIXES)
    for prefix in V.CONTEXT_PREFIXES:
        assert S.id_problem(f"{prefix}:x") is not None and S.id_problem(f"{prefix}://h/x") is not None, prefix
    for scheme in ("https", "urn", "mailto", "tel", "ssh"):             # a scheme that is no prefix is an absolute IRI: none of
        assert scheme not in E.context()                                 # these is a term of the context either, which a
        assert S.id_problem(f"{scheme}:x") is None and E.iri_of_id(f"{scheme}:x") == f"{scheme}:x"      # later rule may refuse


def test_a_crate_of_the_ids_is_a_node_under_each_and_a_node_that_refers_to_each():
    md = crate_of(IDS[:50])
    triples = E.expand(md)
    names = [t for t in triples if t[1] == "http://schema.org/name"]
    parts = [t for t in triples if t[1] == "http://schema.org/hasPart"]
    assert len(names) == 50 and len(parts) == 50 and len({t[0] for t in names}) == 50
    assert {t[0] for t in names} == {t[2] for t in parts}


# -- the checks, watched failing ----------------------------------------------------------------------------------------------------
def test_the_check_finds_an_id_the_reader_accepts_and_the_expansion_cannot_read(monkeypatch):
    """The first draft's gap, which the engine stage's first run found: a fragment with a colon was read as a compact IRI."""
    real = E.iri_of_id

    def gappy(value):
        return real(value.replace("#", "", 1)) if value.startswith("#") and ":" in value else real(value)
    monkeypatch.setattr(E, "iri_of_id", gappy)
    found = unread(IDS)
    assert found and all(i.startswith("#") and ":" in i for i, _ in found)


def test_the_check_finds_two_ids_the_expansion_makes_one_iri(monkeypatch):
    real = E.iri_of_id
    monkeypatch.setattr(E, "iri_of_id", lambda value: real(value.lower()) if value.startswith("#") else real(value))
    found = collided(IDS)
    assert found and all(len(v) > 1 for v in found.values())


def test_the_check_finds_an_id_the_expansion_refuses_and_the_reader_accepts(monkeypatch):
    real = E.iri_of_id

    def strict(value):
        if value.endswith("/") and value != "./":
            raise E.ExpandError("a directory, refused by the test")
        return real(value)
    monkeypatch.setattr(E, "iri_of_id", strict)
    refused = unread(STRINGS)
    assert [i for i, _ in refused if S.id_problem(i) is None], "the check does not see an id the reader accepts"
