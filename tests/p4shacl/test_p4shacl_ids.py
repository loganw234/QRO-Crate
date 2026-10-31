"""Every id the reader accepts, resolved as rdflib resolves it (P4's verifier, round 1, defect 1, after P0.5: the lead's ruling
of 2026-10-16T14:58:58Z). The reader (FORMAT.md item 22) now admits an @id and a reference's in four forms only, so that the
graph the checker holds is the graph a JSON-LD reader makes. This holds the other end: the expansion that the evaluator
reads (qro/p4_expand.py) makes of each of them the IRI rdflib makes, at the one base the engine stage reads crates at, and no
two of them the same.

The ids are the reader's own accepted ones (qro.spelling.id_problem is the oracle) among tens of thousands of strings drawn
from the four forms and their variants and every short string over an alphabet of the characters that have meant something
(tests/p4/p4_ids.py). Each chunk of them is a crate of entities, one under each id, named by its index, and a node that refers
to each, so that an id is read as a subject and as an object. The comparison is the whole triple set of the chunk, rdflib's
against the expansion's. It runs here and not in the quick stage because the engine is the only thing outside this repository
that says what a JSON-LD reader makes.

What it does not hold is another base, which item 22's own first limit says (an absolute IRI equal to the IRI a relative id
resolves to where a crate is read is one node with it) and limit 19 of the profile restates."""
import json

import pytest
from p4shacl_helpers import mine, quick_stage_module, run_engine, theirs
from qro import p4_expand

ids = quick_stage_module("p4_ids")
IDS = ids.drawn_ids()
CHUNKS = ids.chunks(IDS)


@pytest.fixture(scope="module")
def engine():
    jobs = [{"id": f"ids-{k}", "kind": "crate", "metadata": json.dumps(ids.crate_of(chunk)), "shapes": []}
            for k, chunk in enumerate(CHUNKS)]
    answers, _ = run_engine(jobs, timeout=1500)
    return answers


def first_differences(chunk, answer, limit=5):
    """The ids of a chunk whose IRI rdflib made is not the one the expansion makes (at most `limit`): (id, the expansion's,
    rdflib's, or None where rdflib made no node under its name)."""
    named = {o[1]: s for s, p, o in answer["triples"] if p == "http://schema.org/name"}
    out = []
    for k, i in enumerate(chunk):
        try:
            want = p4_expand.iri_of_id(i)
        except p4_expand.ExpandError as x:                       # an id the reader accepts and the expansion cannot read
            want = f"refused: {x}"
        got = named.get(f"n{k}")
        if got != ["iri", want]:
            out.append((i, want, got))
            if len(out) == limit:
                break
    return out


def test_the_ids_are_tens_of_thousands_and_of_each_of_the_four_forms():
    kinds = {"root": 0, "fragment": 0, "path": 0, "absolute": 0}
    for i in IDS:
        kinds["root" if i == "./" else "fragment" if i.startswith("#") else "absolute" if ":" in i else "path"] += 1
    assert len(IDS) >= 50000 and len(set(IDS)) == len(IDS), len(IDS)
    assert kinds["root"] == 1 and min(kinds["fragment"], kinds["path"], kinds["absolute"]) >= 10000, kinds
    assert len(CHUNKS) >= 30 and all(len(c) <= 1500 for c in CHUNKS)


def test_rdflib_makes_of_every_id_the_reader_accepts_the_iri_the_expansion_makes(engine):
    wrong = []
    for k, chunk in enumerate(CHUNKS):
        answer = engine[f"ids-{k}"]
        assert answer["ok"], answer.get("error")
        md = ids.crate_of(chunk)
        if theirs(answer["triples"]) != mine(p4_expand.expand(md)):
            wrong.append((k, first_differences(chunk, answer)))
    assert wrong == [], wrong[:3]


def test_distinct_ids_are_distinct_iris_in_the_expansion_and_in_rdflib(engine):
    made = [p4_expand.iri_of_id(i) for i in IDS]
    assert len(set(made)) == len(IDS), "two ids of the reader's make one IRI in the expansion"
    for k, chunk in enumerate(CHUNKS):
        names = {}
        for s, p, o in engine[f"ids-{k}"]["triples"]:
            if p == "http://schema.org/name":
                names.setdefault(o[1], set()).add(tuple(s))
        assert len(names) == len(chunk) and all(len(v) == 1 for v in names.values()), k      # a name on one subject each
        subjects = {next(iter(v)) for v in names.values()}
        assert len(subjects) == len(chunk) and all(s[0] == "iri" for s in subjects), k       # and no two the same, none blank


def test_an_expansion_that_resolved_an_id_otherwise_is_found(engine, monkeypatch):
    """The comparison is watched failing on three ways to read an id otherwise: the case of an IRI, a fragment's colon, and a
    `;` in a path read as parameters."""
    real = p4_expand.iri_of_id
    readings = {
        "lowercased": lambda i: real(i).lower(),
        "a fragment with a colon cut at it": lambda i: real(i.split(":")[0]) if i.startswith("#") else real(i),
        "parameters dropped": lambda i: real(i.replace(";", "")) if not i.startswith("#") and ":" not in i else real(i),
    }
    for why, reading in readings.items():
        monkeypatch.setattr(p4_expand, "iri_of_id", reading)
        found = [first_differences(chunk, engine[f"ids-{k}"]) for k, chunk in enumerate(CHUNKS)]
        assert any(found), why
        monkeypatch.setattr(p4_expand, "iri_of_id", real)
    assert not any(first_differences(chunk, engine[f"ids-{k}"]) for k, chunk in enumerate(CHUNKS))
