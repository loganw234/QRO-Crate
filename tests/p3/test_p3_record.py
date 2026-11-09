"""The record, `qro-comparison-record/1` (qro/p3_record.py's form; qro/p3_compare.py's `compute`; P3's design, items 1,
5 and 8): a pure function of the declaration's bytes and the runs' crates' bytes, the same bytes computed twice and from
a crate whose P2 entities say otherwise in every term a reader of them would take (the trap of "a verdict computed from
declared values"); in its form, every rational in the profile's spelling and no JSON number but a whole count; and
holding no host path."""
import copy
import json
from fractions import Fraction

import pytest

import p3_builder as B
import p3_support as S
from qro import canonical, p2_measures, p3_compare, p3_record, spelling
from qro import p3_declaration as D
from qro import vocabulary as V

T = "2026-11-01T10:"


@pytest.fixture(scope="module")
def crate(tmp_path_factory):
    d = tmp_path_factory.mktemp("record")
    k = [B.ka(start=f"{T}00:00Z"), B.law("law-0", start=f"{T}01:00Z"), B.law("law-1", start=f"{T}03:00Z", five=40),
         B.coherence(start=f"{T}40:00Z")]
    f = [B.ka(start=f"{T}00:30Z"), B.law("law-0", start=f"{T}02:00Z", five=30), B.coherence(start=f"{T}41:00Z")]
    return B.build(d, [B.Bundle("ibm_kingston", "morning", k), B.Bundle("ibm_fez", "morning", f)])


def record_bytes(crate, md):
    d = canonical.body_digest(md)
    plan = D.plan({m: "1/50" for m in S.FIVE}, {"a": {"device": "ibm_kingston"}, "b": {"device": "ibm_fez"}})
    decl = D.read(D.write({"a": [d], "b": [d]}, plan))
    return p3_record.dumps(p3_compare.compute(decl, None, {d: (crate, md)})[0])


def test_the_record_is_the_same_bytes_computed_twice(crate):
    md = S.md_of(crate)
    assert record_bytes(crate, md) == record_bytes(crate, copy.deepcopy(md))


def lie(graph):
    """Every term of P2's entities a reader would take, said otherwise: the Measurements' values, intervals and shots in
    scope, the Contrasts' classes and values, the Measuring's alpha and family."""
    for e in graph:
        types = canonical.types(e)
        if "qro:Measurement" in types:
            e["qro:value"], e["qro:inScope"] = "1/3", 7
            if "qro:lower" in e:
                e["qro:lower"], e["qro:upper"] = "0/1", "1/1"
        elif "qro:Contrast" in types:
            e["qro:class"] = "signal" if e["qro:class"] == "integrity" else "integrity"
            if "qro:lawValue" in e:
                e["qro:lawValue"] = "1/7"
        elif "qro:Measuring" in types:
            e["qro:alpha"], e["qro:family"] = "1/2", 1


def test_the_record_reads_none_of_p2s_entities_the_trap_of_declared_values(crate):
    """The metadata's P2 entities each edited, the checker's steps bypassed: the record is the same bytes but for the
    crate's identity, which the record names."""
    md = S.md_of(crate)
    lied = copy.deepcopy(md)
    lie(lied["@graph"])
    one, other = json.loads(record_bytes(crate, md)), json.loads(record_bytes(crate, lied))
    for r in (one, other):
        for side in "ab":
            r["runs"][side]["crates"][0]["crate"] = None
        r["declaration"] = None
    assert one == other


def test_the_trap_is_able_to_fail(crate, monkeypatch):
    """The control: a computation that took a crate's Measurement values for its own would give other bytes."""
    md = S.md_of(crate)
    lied = copy.deepcopy(md)
    lie(lied["@graph"])
    real = p2_measures.pub_values

    def from_the_crate(crate_dir, md_, pub, law):
        out = real(crate_dir, md_, pub, law)
        said = {(e["qro:measuredPub"]["@id"], e["qro:measure"]): e for e in md_["@graph"]
                if "qro:Measurement" in canonical.types(e)}
        for m, v in out.items():
            e = said.get((pub["@id"], m))
            if e is not None and e["qro:inScope"] == 7 and v.mapping is not None:
                out[m] = p2_measures.Value(m, 7, Fraction(1, 3), 2, v.mapping)     # what the crate says, taken
        return out
    monkeypatch.setattr(p2_measures, "pub_values", from_the_crate)
    assert record_bytes(crate, md) != record_bytes(crate, lied)


def walk(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)
    else:
        yield x


def test_the_record_is_in_its_form(crate):
    data = record_bytes(crate, S.md_of(crate))
    assert data == canonical.dumps(json.loads(data)) and data.isascii() and data.endswith(b"}\n")
    r = json.loads(data)
    assert sorted(r) == ["alpha", "declaration", "family", "format", "kind", "late", "measures", "plan", "runs"]
    assert r["format"] == p3_record.RECORD_FORMAT
    for leaf in walk(r):
        assert isinstance(leaf, (str, int)) and not isinstance(leaf, bool), leaf
        if isinstance(leaf, int):
            assert leaf >= 0
    for m in r["measures"]:
        assert sorted(m) == ["a", "b", "causes", "classes", "difference", "epsilon", "means", "measure", "readout",
                             "refused", "statements", "strongForm", "unseen"]
        for side in "ab":
            assert sorted(m[side]) == ["drift", "inScope", "interval", "members", "value"]
            for x in m[side]["interval"] + [m[side]["value"], m[side]["drift"]]:
                assert x == "none" or spelling.problem("rational", x) is None, x
        assert m["means"] in V.WORDS["means"]
        assert [x for x in m["statements"] if x not in V.WORDS["statement"]] == []
        assert [x for x in m["unseen"] if x not in V.WORDS["factor"]] == []
    assert [m["measure"] for m in r["measures"]] == sorted(m["measure"] for m in r["measures"])


def test_the_record_holds_no_host_path(crate):
    data = record_bytes(crate, S.md_of(crate)).decode("ascii")
    for part in (str(crate), crate.as_posix(), crate.parent.name, "Users", "AppData"):
        assert part not in data, part
