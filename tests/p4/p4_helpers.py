"""The p4 stage's helpers: the gates of P4's design (item 4.6) as functions, so that the same code that holds the real
shapes is shown failing on shapes planted wrong (test_p4_gates.py); the corpus of plants judged once; a seeded fuzz of
mutations; and a copy of the tree small enough for the command line to run in. Nothing here is a test: pytest's naming
decides what is one, and a helper under tests/ names no function `test*` and no class `Test*` (CLAUDE.md).

A gate returns a list of problems in a few words each, empty if it holds. The gates:
  1. soundness: if a must shape fails, the checker refuses (steps 1 to 3), by a name in the union of the failing shapes'
     claims; and a plant's own refusal is one a failing shape mirrors itself (own_name_problems). The sweeps, which hold
     the same of crates one edit from the fixture, are in p4_sweeps.py;
  2. the spelling differential: no shape refuses a value the checker's spelling accepts;
  3. coverage: every must shape is made to fail by some plant;
  4. the positive example conforms to every must shape and is accepted.
"""
import builtins
import copy
import functools
import importlib.util
import io
import json
import os
import random
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import types
from dataclasses import dataclass
from pathlib import Path

import pytest

from qro import canonical, checker, fixture, reader
from qro import p4_eval, p4_examples, p4_expand, p4_shapes
from qro import spelling as S
from qro import vocabulary as V
from qro.refusal import Refused

ROOT = Path(__file__).resolve().parents[2]
TERMS_AT_IMPORT = V.TERMS          # a test that mutates the table must not be the one that builds the shared corpus


def prepare(monkeypatch):
    """The checker as the command line has it with --fixtures: fresh registries, the fixture's raw form and generator,
    and every parcel's steps (checker.load). The registries are restored when the test ends."""
    monkeypatch.setattr(checker, "STEPS", {n: None for n in range(4, 9)})
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    monkeypatch.setattr(checker, "COUNTS", [])
    monkeypatch.setattr(checker, "GENERATORS", {})
    fixture.register()
    checker.load()


@dataclass(frozen=True)
class Case:
    """One crate judged once: what does not depend on the shapes, so that a gate can be run on many sets of them."""
    name: str
    checker: str                 # the full checker's verdict
    early: str                   # the first refusal of steps 1 to 3, or "ok": what the shapes mirror
    triples: tuple
    declared: tuple              # the must shapes the plant declares failing
    unreadable: str
    family: str


def early_verdict(crate, md_bytes):
    """Steps 1 to 3 alone, which the shapes mirror and which no later parcel's step changes."""
    try:
        md = reader.read(md_bytes)
        checker.files(Path(crate), md)
        checker.counts(Path(crate), md)
    except Refused as r:
        return r.name
    return "ok"


def case_of(work, plant):
    md = work.of_plant(plant)
    with work.staged(md, plant.files) as crate:
        full = p4_examples.checker_verdict(crate)
        early = early_verdict(crate, canonical.dumps(md))
    try:
        triples, why = tuple(p4_expand.expand(md)), ""
    except p4_expand.ExpandError as x:
        triples, why = (), str(x)
    return Case(plant.name, full, early, triples, plant.shapes, why, plant.family)


def corpus(work, plants=None):
    """Every plant judged once, as Cases, in the order of p4_examples.every_plant()."""
    return [case_of(work, p) for p in (p4_examples.every_plant() if plants is None else plants)]


@functools.lru_cache(maxsize=1)
def session_corpus():
    """(cases, shapes) for every plant, judged once for the whole session, under the checker as the command line has it.
    Built from the table as it is, so a test that has changed the table in memory must not be the first to ask."""
    assert V.TERMS is TERMS_AT_IMPORT, "the shared corpus is built from the unmodified table"
    with pytest.MonkeyPatch.context() as mp:
        prepare(mp)
        with p4_examples.Workspace() as work:
            return tuple(corpus(work)), tuple(work.shapes)


def claims_of(shapes):
    return {p4_examples.local(s.id): s.claims for s in shapes}


def must_failing(shapes, triples):
    """The local names of the must shapes that fail on `triples`."""
    return {p4_examples.local(i) for i in p4_eval.failing(p4_eval.validate(shapes, p4_eval.Graph(triples)), "must")}


def soundness_problems(shapes, cases):
    """Gate 1, and the plants' own declarations: for each readable case, the declared shapes fail; a case that declares
    none has none failing; and any failing must shape claims the checker's refusal. A case the expansion refuses to read
    is never skipped: the evaluator abstains from it, so the checker has to have refused it, at steps 1 to 3 (P4's
    verifier, round 1, defect 1, after P0.5; the lead's ruling of 2026-10-16T14:58:58Z)."""
    out = []
    claims = claims_of(shapes)
    known = set(claims)
    for c in cases:
        if c.unreadable:
            if c.early == "ok":
                out.append(f"{c.name}: the expansion refuses it ({c.unreadable}) and steps 1 to 3 accept it")
            continue
        failing = must_failing(shapes, c.triples)
        for name in c.declared:
            if name not in known:
                out.append(f"{c.name}: declares {name}, which is no shape")
            elif name not in failing:
                out.append(f"{c.name}: {name} does not fail")
        if not c.declared and failing:
            out.append(f"{c.name}: declares no failing shape, and {sorted(failing)} fail")
        if failing:
            names = {x for s in failing for x in claims[s]}
            if c.early not in names:
                out.append(f"{c.name}: {sorted(failing)} fail and claim {sorted(names)}; steps 1 to 3 say {c.early}")
    return out


def own_name_problems(shapes, cases, own):
    """The plants against what each shape mirrors itself. `own` is {local name: claims} before the six of FORM are added
    (H.build(widen=False)). For each readable case on which a must shape fails and the checker refuses at steps 1 to 3, a
    failing shape mirrors the refusal itself: the six of FORM (spelling, term-unknown, graph-form, context, file-missing,
    file-link) are claimed by every must shape so that the sweeps are true, and would otherwise hide a shape whose own claim is
    wrong. A case the expansion cannot read has no triples and no shape to ask; that the checker refused it is
    soundness_problems', which skips none."""
    out = []
    for c in cases:
        if c.unreadable or c.early == "ok":
            continue
        failing = must_failing(shapes, c.triples)
        if failing and c.early not in {x for s in failing for x in own.get(s, ())}:
            out.append(f"{c.name}: steps 1 to 3 say {c.early}, and {sorted(failing)} fail and mirror {sorted({x for s in failing for x in own.get(s, ())})}")
    return out


def uncovered(shapes, cases):
    """Gate 3: the must shapes that no case makes fail."""
    seen = set()
    for c in cases:
        if not c.unreadable:
            seen |= must_failing(shapes, c.triples)
    return sorted(p4_examples.local(s.id) for s in shapes if s.level == "must" and p4_examples.local(s.id) not in seen)


def positive_problems(shapes, md):
    """Gate 4: the metadata conforms to every shape of every level."""
    results = p4_eval.validate(shapes, p4_expand.expand(md))
    return [f"{r.shape} ({r.level}) fails at {p4_eval.focus_name(r.focus)}: {r.reason}" for r in results]


# -- the spelling differential (gate 2) --------------------------------------------------------------------------
D = "d" * 64
SAMPLES = {
    "integer": [0, 1, 2 ** 63 - 1, 2 ** 63, -1, "1", 1.5, True, False],
    "size": ["0", "1", "53", "007", "-1", "9223372036854775807", "9223372036854775808", "1 ", " 1", "١٢",
             "", "1\n", "9223372036854775807\n"],
    "digest": [D, D.upper(), D[:63], D + "0", "g" * 64, D + "\n", "", "٠" * 64],
    "commit": ["a" * 40, "A" * 40, "a" * 39, "a" * 41, "a" * 40 + "\n"],
    "rational": ["0/1", "1/2", "-1/2", "5/16", "2/4", "0/2", "1/0", "01/2", "+1/2", "1/-2", "1/2\n", "-0/1", "1/1",
                 "3", "1" * 1001 + "/1", "1" * 1000 + "/1", "-" + "1" * 1000 + "/1", "-" + "1" * 1001 + "/1",
                 "-" + "1" * 1000 + "/" + "1" * 999 + "2", "-" + "1" * 1000 + "/" + "1" * 1000 + "\n"],
    "binary64": [S.binary64(0.5), S.binary64(0.0), S.binary64(-0.0), S.binary64(1e300), "3fe0000000000000 0.5",
                 "3fe0000000000000 0.6", "3FE0000000000000 5e-1", "3fe0000000000000 ", "3fe000000000000 5e-1",
                 S.binary64(0.5) + "\n"],
    "time": ["2026-10-14T00:00:00Z", "2026-10-14T00:00:00.5Z", "2026-10-14T00:00:00.50Z", "2026-10-14T00:00:00",
             "2026-10-14T00:00:00+00:00", "2026-02-30T00:00:00Z", "2026-10-14T00:00:60Z", "2026-10-14T24:00:00Z",
             "2026-10-14T00:00:00.Z", "2026-10-14 00:00:00Z", "٢026-10-14T00:00:00Z", "2026-10-14T00:00:00Z\n"],
    "date": ["2026-10-14", "2026-13-01", "2026-02-30", "20261014", "2026-1-4", "2026-10-14\n", ""],
    "text": ["x", "a b", "a\nb", "", " x", "x ", "x\t", " x", "x ", "a\x00b", "a\x01b", "a\x7fb", "a\x85b",
             "\ud800", "multi\nline\ntext", "\n", "x\n", "é", "中"],
    "iri": ["https://x.org/a", "urn:x:y", "x", "a:b", "http:", "https://x y", "a.b:c", "https://x.org/a\n", "https://x.org/é", ""],
    "ref": [{"@id": "#a"}, {"@id": "https://example.org/x"}, {"@id": "x y"}, {"@id": ""}, {"@id": "a", "x": 1},
            {"x": "a"}, "a plain string", 5, ["a"], {}],
    "slot": ["none", "filled", "", 1],
    "word:device-kind": ["qpu", "simulator", "QPU", "toaster", "", "qpu ", 1],
}
# Every word of every set the table has, and the ways to miss one: an absence word (never a member of a set), nothing,
# another case, a space at an end. So a word dropped from any set, now or when the table has grown, is a stricter shape.
for _set, _words in V.WORDS.items():
    _first = next(iter(_words))
    SAMPLES.setdefault("word:" + _set, []).extend(
        [w for w in list(_words) if w not in SAMPLES.get("word:" + _set, [])]
        + ["", _first.upper(), _first + " ", " " + _first, "unknown", "none", "zz-not-a-word"])


# The values a shape takes that the checker's spelling refuses: the stated limit 3, each with its reason. A value that
# moves in or out of this table is a shape that got looser or stricter.
LOOSER = {
    ("size", "9223372036854775808"): "above 2^63 - 1 in the same nineteen digits",
    ("size", "1\n"): "a trailing line feed: `$` lets one by",
    ("rational", "2/4"): "not in lowest terms",
    ("rational", "1/2\n"): "a trailing line feed: `$` lets one by",
    ("rational", "1" * 1001 + "/1"): "a term of more than 1,000 digits, inside the length cap",
    ("rational", "-" + "1" * 1001 + "/1"): "a term of more than 1,000 digits, inside the length cap",
    ("binary64", "3fe0000000000000 0.5"): "a decimal that is not the bits' exact one",
    ("binary64", "3fe0000000000000 0.6"): "a decimal that is not the bits' exact one",
    ("binary64", S.binary64(0.5) + "\n"): "a trailing line feed: `$` lets one by",
    ("iri", "https://x.org/a\n"): "a trailing line feed: `$` lets one by",
    ("time", "2026-02-30T00:00:00Z"): "not a real time",
    ("time", "2026-10-14T00:00:60Z"): "not a real time: a leap second",
    ("time", "2026-10-14T24:00:00Z"): "not a real time",
    ("time", "2026-10-14T00:00:00Z\n"): "a trailing line feed: `$` lets one by",
    ("date", "2026-13-01"): "not a real date",
    ("date", "2026-02-30"): "not a real date",
    ("text", "a\x00b"): "a control character",
    ("text", "a\x01b"): "a control character",
    ("text", "a\x7fb"): "a control character",
    ("text", "a\x85b"): "a control character",
    ("text", "\ud800"): "a lone surrogate",
    ("text", "x\n"): "a trailing line feed: `$` lets one by",
}


def object_of(sp, value):
    """The RDF object the expansion would make of `value` (qro/p4_expand.py), or None where it would refuse the value."""
    try:
        if isinstance(value, dict):
            if sorted(value) != ["@id"]:
                return None
            return p4_expand.iri_of_id(value["@id"])
        return p4_expand.literal(value)
    except p4_expand.ExpandError:
        return None


def shape_accepts(sp, value):
    """Whether the shape of a spelling takes `value`, read on a one-triple graph; None where the expansion would refuse
    the value (so the shapes never see it, as in a crate)."""
    obj = object_of(sp, value)
    if obj is None:
        return None
    constraints = p4_shapes.spelling_constraints(sp)
    prop = p4_shapes.Shape(path="urn:p", **constraints) if constraints is not None else p4_shapes.Shape(path="urn:p",
                                                                                                         in_=())
    return not p4_eval.property_reasons(p4_eval.Graph([("urn:s", "urn:p", obj)]), prop, "urn:s")


def differential(constraints_of=None):
    """Gate 2: [(spelling, value, who)] for each sample the shape refuses and the checker's spelling accepts (who
    "stricter": the violation), each the shape accepts and the checker refuses ("looser": a stated limit), and each the
    expansion cannot read though the checker's spelling accepts it ("unread": the shapes would never see it; after P0.5 it
    is a violation too, and no value is skipped unseen)."""
    out = []
    for sp, values in SAMPLES.items():
        for value in values:
            mine = shape_accepts(sp, value)
            theirs = S.problem(sp, value) is None
            if mine is None:
                if theirs:
                    out.append((sp, value, "unread"))
                continue
            if theirs and not mine:
                out.append((sp, value, "stricter"))
            elif mine and not theirs:
                out.append((sp, value, "looser"))
    return out


# -- a fuzz of mutations -------------------------------------------------------------------------------------------
def pick(rng, items):
    items = list(items)
    return items[rng.randrange(len(items))]


def entities(g, skip=()):
    return [e for e in g if e["@id"] not in skip]


def m_drop_key(g, rng):
    e = pick(rng, [e for e in g if len(e) > 1])
    del e[pick(rng, [k for k in e if k != "@id"])]


def m_drop_entity(g, rng):
    g.remove(pick(rng, entities(g, (V.DESC, V.ROOT))))


def m_add_term(g, rng):
    t = pick(rng, V.TERMS)
    pick(rng, g)[t.key] = p4_examples.valid_value(t)


def m_add_bad_term(g, rng):
    t = pick(rng, V.TERMS)
    pick(rng, g)[t.key] = p4_examples.bad_value(t)


def typed(types):
    """A type as the writer spells it: a string for one, else a sorted list of distinct strings."""
    types = sorted(set(types))
    return types[0] if len(types) == 1 else types


def m_retype(g, rng):
    e = pick(rng, entities(g, (V.DESC, V.ROOT)))
    e["@type"] = pick(rng, V.TYPES).key if rng.random() < 0.7 else pick(
        rng, ["Person", "Foo", "foo:Bar", "schema:Thing", "MediaObject"])


def m_add_type(g, rng):
    e = pick(rng, g)
    e["@type"] = typed(set(canonical.types(e)) | {pick(rng, V.TYPES).key})


def m_new_entity(g, rng):
    g.append({"@id": pick(rng, ["#n1", "#n2", "urn:x:y", "n/a/b", "foo:bar", "qro:thing", "schema:Thing", "#a%20b", "#a:b",
                                "_:b1", "./x", "a//b", "x?q", "file:///x", "@x", "a/../b"]),
              "@type": pick(rng, V.TYPES).key})


def m_wrap(g, rng):
    e = pick(rng, [e for e in g if len(e) > 2])
    k = pick(rng, [k for k in e if k not in ("@id", "@type")])
    e[k] = e[k] if isinstance(e[k], list) else [e[k]]


def m_unwrap(g, rng):
    lists = [(e, k) for e in g for k, v in e.items() if isinstance(v, list) and k != "@type"]
    if lists:
        e, k = pick(rng, lists)
        e[k] = e[k][0] if e[k] else "x"


def m_retarget(g, rng):
    refs = [(e, k) for e in g for k, v in e.items() if k not in ("@id", "@type") and (
        isinstance(v, dict) and "@id" in v or isinstance(v, list) and v and isinstance(v[0], dict))]
    if refs:
        e, k = pick(rng, refs)
        new = {"@id": pick(rng, [x["@id"] for x in g] + ["https://example.org/z", "#zz"])}
        e[k] = [new] if isinstance(e[k], list) else new


def m_rename(g, rng):
    e = pick(rng, entities(g, (V.DESC, V.ROOT)))
    e["@id"] = pick(rng, ["#renamed", "urn:renamed", "renamed/x", "foo:renamed", "qro:renamed", "_:renamed", "#re:named"])


def m_digest(g, rng):
    e = pick(rng, [e for e in g if "sha256" in e])
    e["sha256"] = pick(rng, ["0" * 64, "x", "A" * 64, e["sha256"]])


def m_size(g, rng):
    e = pick(rng, [e for e in g if "contentSize" in e])
    e["contentSize"] = pick(rng, ["0", "1", "007", 5, e["contentSize"]])


def m_dup(g, rng):
    lists = [(e, k) for e in g for k, v in e.items() if isinstance(v, list) and v]
    if lists:
        e, k = pick(rng, lists)
        e[k] = e[k] + [e[k][0]]


def m_haspart(g, rng):
    r = next(e for e in g if e["@id"] == V.ROOT)
    r["hasPart"] = sorted(r["hasPart"] + [{"@id": pick(rng, [x["@id"] for x in g] + ["https://example.org/q"])}],
                          key=lambda x: x["@id"])
    r["hasPart"] = [dict(t) for t in {tuple(x.items()) for x in r["hasPart"]}]
    r["hasPart"].sort(key=lambda x: x["@id"])


def m_mention(g, rng):
    r = next(e for e in g if e["@id"] == V.ROOT)
    acts = [e["@id"] for e in g if set(canonical.types(e)) & set(p4_examples.actions())]
    r["mentions"] = [{"@id": i} for i in sorted(acts)] if rng.random() < 0.6 else [{"@id": pick(rng, [
        x["@id"] for x in g] + ["https://example.org/m"])}]


def m_action(g, rng):
    g.append({"@id": pick(rng, ["#act1", "#act2"]), "@type": "CreateAction"})
    m_mention_all(g)


def m_mention_all(g):
    r = next(e for e in g if e["@id"] == V.ROOT)
    acts = sorted({e["@id"] for e in g if set(canonical.types(e)) & set(p4_examples.actions())})
    if acts:
        r["mentions"] = [{"@id": i} for i in acts]


# Ids the reader refuses (FORMAT.md item 22), most of them ones a JSON-LD reader reads otherwise or not at all, so that the
# expansion refuses the crate that holds one, and the gate holds that the checker refuses it too.
ODD_IDS = ("_:b1", "./x", "a//b", "x?q", "file:///x", "@x", "a/../b", "//h/x", "/x", "../x", "x#a", "HTTPS://x/y", "a b",
           "schema:a", "C:/x", "#", ".", "x;", "#a://b")


def m_odd_id(g, rng):
    """An entity under an id the reader refuses, or the root listing one."""
    i = pick(rng, ODD_IDS)
    g.append({"@id": i, "@type": "CreativeWork", "name": "x"})
    if rng.random() < 0.3:
        r = next(e for e in g if e["@id"] == V.ROOT)
        r["hasPart"] = sorted(r["hasPart"] + [{"@id": i}], key=lambda x: x["@id"])


MUTATIONS = (m_drop_key, m_drop_entity, m_add_term, m_add_bad_term, m_retype, m_add_type, m_new_entity, m_wrap,
             m_unwrap, m_retarget, m_rename, m_digest, m_size, m_dup, m_haspart, m_mention, m_action, m_odd_id)


def mutated(base, seed, rounds=None, trace=None):
    """The fixture's metadata with 1 to 3 of MUTATIONS applied, chosen by `seed` alone (random.Random(int) is the
    same on every host): the graph's order made again after them, as a plant's is. `trace` collects their names."""
    rng = random.Random(seed)
    md = copy.deepcopy(base)
    for _ in range(rounds or rng.randint(1, 3)):
        g = md["@graph"]
        try:
            m = pick(rng, MUTATIONS)
            if trace is not None:
                trace.append(m.__name__)
            m(g, rng)
        except (StopIteration, ValueError, IndexError, KeyError, TypeError, AttributeError):
            continue                       # a mutation with nothing to act on, or on what an earlier one left odd
    return p4_examples.arranged(md)


def valid_value_at(t, g, rng):
    """A value in the term's one spelling, chosen by `rng` among the samples the checker's spelling accepts, and for a
    reference among the ids the graph holds; a list of one to three distinct, sorted ones for a many term."""
    base = t.spelling
    if base == "ref":
        pool = [e["@id"] for e in g] + ["https://example.org/ref", "urn:x:y"]
        one = lambda: {"@id": pick(rng, pool)}                                       # noqa: E731
    else:
        pool = [v for v in SAMPLES.get(base, []) if S.problem(base, v) is None] or [p4_examples.valid_value(t)]
        if base.startswith("word:"):
            pool = list(V.WORDS[base[5:]])
        one = lambda: pick(rng, pool)                                                # noqa: E731
    if not t.many:
        return one()
    values = [one() for _ in range(rng.randint(1, 3))]
    unique = {json.dumps(v, sort_keys=True): v for v in values}
    return sorted(unique.values(), key=canonical.sort_key)


def v_term(g, rng):
    """A valid value of a random term on an entity of a type its domain admits, fresh or the root's, a file's..."""
    t = pick(rng, V.TERMS)
    token = pick(rng, t.domain)
    if token == V.DESC or t.key == "conformsTo":
        return
    host = p4_examples.host_for(token, g, f"#v{rng.randrange(10 ** 6)}")
    host[t.key] = valid_value_at(t, g, rng)


def v_entity(g, rng):
    """A new entity of a type from the table, with a valid id."""
    i = pick(rng, [f"#e{rng.randrange(10 ** 6)}", f"urn:e:{rng.randrange(10 ** 6)}", f"#e:{rng.randrange(10 ** 6)}",
                   f"https://example.org/e{rng.randrange(10 ** 6)}", f"dir{rng.randrange(100)}/e{rng.randrange(100)}/"])
    t = pick(rng, [y for y in V.TYPES if y.key not in ("Profile", "qro:RawResult")]).key
    g.append({"@id": i, "@type": t})
    p4_examples.mention(*[e["@id"] for e in g if set(canonical.types(e)) & set(p4_examples.actions())])(g)         if t in p4_examples.actions() else None


def v_part(g, rng):
    """A new Dataset the root lists, which lists the files: files reached through a chain."""
    i = f"dir{rng.randrange(100)}/"
    if any(e["@id"] == i for e in g):
        return
    g.append({"@id": i, "@type": "Dataset", "hasPart": [{"@id": "data/notes.txt"}, {"@id": "data/raw.counts.json"}][
        :rng.randint(1, 2)]})
    r = next(e for e in g if e["@id"] == V.ROOT)
    r["hasPart"] = sorted(r["hasPart"] + [{"@id": i}], key=canonical.sort_key)


def v_remove_optional(g, rng):
    """Drop a key the checker does not require of its entity."""
    e = pick(rng, [e for e in g if e["@id"] not in (V.DESC,)])
    keys = [k for k in e if k not in ("@id", "@type") and k not in V.ROOT_REQUIRED and k not in ("sha256", "contentSize")
            and not (k == "qro:rawForm" or k in ("version",))]
    if keys:
        del e[pick(rng, keys)]


VALID_MUTATIONS = (v_term, v_term, v_term, v_entity, v_part, v_remove_optional)


def valid_mutated(base, seed, trace=None):
    """The fixture's metadata with 1 to 6 insertions of valid things, chosen by `seed` alone: nearly always accepted."""
    rng = random.Random(seed)
    md = copy.deepcopy(base)
    for _ in range(rng.randint(1, 6)):
        m = pick(rng, VALID_MUTATIONS)
        if trace is not None:
            trace.append(m.__name__)
        try:
            m(md["@graph"], rng)
        except (StopIteration, ValueError, IndexError, KeyError, TypeError, AttributeError):
            continue
    return p4_examples.arranged(md)


def fuzz_problems(work, shapes, seeds, make=mutated):
    """Gate 1, as far as a crate with several faults lets it be put: over `seeds` crates made by `make`, any must shape
    that fails while steps 1 to 3 accept, and any crate the expansion refuses to read that steps 1 to 3 accept (it is never
    skipped: the evaluator abstains from it, so the checker has to have refused it). With several faults the checker names
    the first and a shape another, so the claims are held by the single-fault plants alone. Returns (problems, how many
    crates steps 1 to 3 accepted, how many the expansion refused). A crate the writer cannot write at all (not JSON) is
    the one thing left out."""
    out, accepted, refused = [], 0, 0
    claims = claims_of(shapes)
    for seed in seeds:
        md = make(work.pristine, seed)
        try:
            data = canonical.dumps(md)
        except (TypeError, ValueError):             # not JSON the writer can write
            continue
        with work.staged(md) as crate:
            early = early_verdict(crate, data)
        accepted += early == "ok"
        try:
            triples = p4_expand.expand(md)
        except p4_expand.ExpandError as x:
            refused += 1
            if early == "ok":
                out.append(f"seed {seed}: the expansion refuses it ({x}) and steps 1 to 3 accept it")
            continue
        failing = must_failing(shapes, triples)
        if failing and early == "ok":
            out.append(f"seed {seed}: {sorted(failing)} fail where steps 1 to 3 accept, and claim "
                       f"{sorted({x for s in failing for x in claims[s]})}")
    return out, accepted, refused


# -- a copy of the tree the command line can run in ------------------------------------------------------------------
def tree(dest, profile=True):
    """What tools/gen_profile.py needs to run in `dest`: the package, the tool, and the profile directory (not with
    profile=False: for a test that puts something else in its place)."""
    dest = Path(dest)
    shutil.copytree(ROOT / "qro", dest / "qro", ignore=shutil.ignore_patterns("__pycache__"))
    (dest / "tools").mkdir()
    shutil.copy2(ROOT / "tools" / "gen_profile.py", dest / "tools" / "gen_profile.py")
    if profile:
        shutil.copytree(ROOT / "profile", dest / "profile")
    return dest


def load_file(path, name):
    """The Python file at `path` as a module of its own called `name`, executed afresh: what it binds as it is loaded is what the
    standard library is at that moment (a spy that is in by then is bound, one that is not is not)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_tool():
    """tools/gen_profile.py as a module of its own, loaded by its path."""
    return load_file(ROOT / "tools" / "gen_profile.py", "gen_profile_under_test")


def profile_copy(tmp_path):
    """A root holding profile/ as it is on disk."""
    shutil.copytree(ROOT / "profile", tmp_path / "profile")
    return tmp_path


def outside_dir(tmp_path, name="outside", rendered=False):
    """A directory outside the tree with a file and an empty directory in it: what no walk of the tool may touch. With
    rendered=True it holds a copy of the rendered files as well, so that through a link it would look like a profile/."""
    outside = tmp_path / name
    if rendered:
        shutil.copytree(ROOT / "profile", outside)
    else:
        outside.mkdir()
    (outside / "victim.txt").write_bytes(b"not a part of profile/" + bytes([10]))
    (outside / "emptydir").mkdir()
    return outside


def snapshot(path):
    """{path relative to `path`: bytes for a file, None for a directory, "link" for a link} for everything under it. A link is
    listed and never followed (os.walk descends a directory junction on Windows), so this is safe to take of a tree that holds
    one, even one that points at the tree itself."""
    path, out = Path(path), {}
    for dirpath, dirs, files in os.walk(path):
        for name in sorted(dirs + files):
            p = Path(dirpath, name)
            rel = p.relative_to(path).as_posix()
            out[rel] = "link" if checker._is_link(p) else (None if p.is_dir() else p.read_bytes())
        dirs[:] = [d for d in dirs if not checker._is_link(Path(dirpath, d))]
    return out


def run_tool(args, cwd, tree_root, opts=(), env=None):
    """tools/gen_profile.py of `tree_root` as a process (python `opts` the tool args), with its stdout and stderr as text."""
    return subprocess.run([sys.executable, *opts, str(Path(tree_root) / "tools" / "gen_profile.py"), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="ascii",
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **(env or {})))


def run_patched(tree_root, args, prelude, cwd, merge=False):
    """tools/gen_profile.py of `tree_root` as a process in whose interpreter `prelude` (Python source) has run first, as the tool's
    own `__main__`: what a test needs to make a host do what the host here will not (list no directory, give no stderr, a package
    that raises as it is imported). With `merge`, stderr goes to the same pipe as stdout, so that the order of the lines shows."""
    code = ("import runpy, sys\n" + prelude + "\nsys.argv = [sys.argv[1], *" + repr(list(args)) + "]\n"
            "runpy.run_path(sys.argv[0], run_name='__main__')")
    pipes = {"stdout": subprocess.PIPE, "stderr": subprocess.STDOUT} if merge else {"capture_output": True}
    return subprocess.run([sys.executable, "-c", code, str(Path(tree_root) / "tools" / "gen_profile.py")], cwd=cwd, text=True,
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), **pipes)


# -- a spy on every call that could follow a link ------------------------------------------------------------------------------------
OS_CALLS = ("stat", "lstat", "scandir", "listdir", "walk", "access", "readlink", "utime", "chmod", "chdir", "mkdir", "rmdir", "unlink",
            "remove", "rename", "replace", "link", "symlink", "truncate", "open")
OS_PATH_CALLS = ("exists", "lexists", "isdir", "isfile", "islink", "isjunction", "ismount", "isdevdrive", "getsize", "getmtime",
                 "getatime", "getctime", "realpath", "samefile")
# Every function Path defines itself, read from the class and not from a list: each asks the host something (the methods of the pure
# class beneath it, which do not, are not here). Path.is_block_device and the rest of its kind are a stat, which is wrapped too.
PATH_CALLS = tuple(sorted(n for n, v in vars(Path).items() if isinstance(v, types.FunctionType) and not n.startswith("_")))
# What the tool may ask of a link itself: whether it is one (an lstat), and to remove it. Everything else it could ask of a link
# follows it, and of a path below one reads through it.
OF_THE_LINK = frozenset(("os.lstat", "os.unlink", "os.remove", "os.rmdir", "os.path.lexists", "os.path.islink", "os.path.isjunction",
                         "Path.lstat", "Path.is_symlink", "Path.is_junction", "Path.unlink", "Path.rmdir"))
# The keyword by which each wrapped call takes its path, or its two, so that spy_missed makes every call by keyword as well as by
# position (the first verifier's D1: the spy read the positions alone, and a call given its path by keyword was not seen). A method of
# Path has its path as self and a keyword only for a second path; the other methods of Path are not here.
PATH_KEYWORDS = {
    "os.stat": ("path",), "os.lstat": ("path",), "os.scandir": ("path",), "os.listdir": ("path",), "os.walk": ("top",),
    "os.access": ("path",), "os.readlink": ("path",), "os.utime": ("path",), "os.chmod": ("path",), "os.chdir": ("path",),
    "os.mkdir": ("path",), "os.rmdir": ("path",), "os.unlink": ("path",), "os.remove": ("path",), "os.rename": ("src", "dst"),
    "os.replace": ("src", "dst"), "os.link": ("src", "dst"), "os.symlink": ("src", "dst"), "os.truncate": ("path",),
    "os.open": ("path",), "os.path.exists": ("path",), "os.path.lexists": ("path",), "os.path.isdir": ("s",),
    "os.path.isfile": ("path",), "os.path.islink": ("path",), "os.path.isjunction": ("path",), "os.path.ismount": ("path",),
    "os.path.isdevdrive": ("path",), "os.path.getsize": ("filename",), "os.path.getmtime": ("filename",),
    "os.path.getatime": ("filename",), "os.path.getctime": ("filename",), "os.path.realpath": ("path",),
    "os.path.samefile": ("f1", "f2"), "open": ("file",), "io.open": ("file",),
    "Path.rename": ("target",), "Path.replace": ("target",), "Path.samefile": ("other_path",), "Path.symlink_to": ("target",),
    "Path.hardlink_to": ("target",),
}
OTHER_ARGS = {"os.access": {"mode": 0}, "os.chmod": {"mode": 0o600}, "os.truncate": {"length": 0}, "os.open": {"flags": 0}}
# The calls that take a second path, which the spy must read as well as the first: spy_missed makes each with the first path apart from
# the link and the second below it, by position and by keyword. (os.symlink, Path.symlink_to and Path.hardlink_to are not here: made
# so, on a host that lets a test make a symbolic link, they would make one.)
SECOND_PATH = ("os.rename", "os.replace", "os.link", "os.path.samefile", "Path.rename", "Path.replace", "Path.samefile")


def plain(p):
    """A path as the spy compares it: absolute, normalised (case, separators, `.` and `..`), and with the extended-length prefix of
    Windows taken off, which names the same path. Not an 8.3 short name, nor a way to the same directory through another link."""
    s = os.fsdecode(p)
    if s.startswith("\\\\?\\") and not s.startswith("\\\\?\\UNC\\"):
        s = s[4:]
    return os.path.normcase(os.path.abspath(s))


class Watch:
    """The calls a spy (watch_below) has seen: `calls` is a list of (the call, the path). It sees a call only while `active`. `wrapped`
    is the set of calls it wraps and `where` says of each the (owner, name) it replaced; `tool` is the module watch_below loaded
    after the spy, if it was asked to."""

    def __init__(self, link):
        self.link = plain(link)
        self.calls, self.active, self.wrapped, self.where, self.tool = [], True, set(), {}, None

    def note(self, what, p, follows=True):
        if not self.active or not isinstance(p, (str, bytes, os.PathLike)):
            return
        s = plain(p)
        if s.startswith(self.link + os.sep) or (s == self.link and follows):
            self.calls.append((what, os.fsdecode(p)))


def watch_below(monkeypatch, link, load=False):
    """A spy on the link at `link`: a Watch whose `calls` fill, from now on, with the calls of os (OS_CALLS), os.path (OS_PATH_CALLS),
    open and io.open, and every function pathlib.Path defines itself (PATH_CALLS), that could follow the link or read through it,
    made with a path below it (or with it, where the call follows a link): the stats and the listings, the opens and the reads, the
    tests of a path (os.path.exists, isdir, Path.is_dir and the rest), a resolve, a walk, a change of working directory, a write or
    a removal. It notes every path a call is given, by position or by keyword (the first verifier's D1: it once read the positions
    alone). A call on the link itself that does not follow it (an lstat, is_symlink, is_junction, lexists, a removal of it) is
    allowed, for the tool must ask what it is and take it out.

    With `load`, the tool is loaded after the spy goes in (watch.tool, a module of its own), so that a name the tool binds as it is
    loaded (a from-import of a function of os, a module-level alias, a default argument) is the spy's; a name bound before the spy
    goes in is the standard library's own, and is not seen. And the watch ends when watch.tool.remove_link has removed the link:
    --write then writes where the link was, and those paths are the new directory's.

    It cannot see a DirEntry of a listing (os.walk asks one is_dir()), a handle already open, ctypes, a process, a function another
    module bound before it went in, a path spelt as an 8.3 short name or reached through another link to the same directory, or a
    module of the standard library that reaches the host some other way (nt, posix, _io, shutil, glob...): the tool imports none,
    which test_the_tool_imports_only_the_modules_the_spy_covers holds."""
    watch = Watch(link)

    def spy(owner, name, what):
        if not hasattr(owner, name):
            return
        real = getattr(owner, name)

        def watched(*a, **k):
            follows = what not in OF_THE_LINK and k.get("follow_symlinks", True) is not False
            for p in (*a[:2], *k.values()):                 # every path the call is given, by position or by keyword
                watch.note(what, p, follows)
            return real(*a, **k)
        monkeypatch.setattr(owner, name, watched)
        watch.wrapped.add(what)
        watch.where[what] = (owner, name)

    for name in OS_CALLS:
        spy(os, name, "os." + name)
    for name in OS_PATH_CALLS:
        spy(os.path, name, "os.path." + name)
    spy(builtins, "open", "open")
    spy(io, "open", "io.open")
    for name in PATH_CALLS:
        spy(Path, name, "Path." + name)
    if load:
        tool = watch.tool = load_tool()                     # after the spy: what it binds as it is loaded is the spy's
        real_remove = tool.remove_link

        def remove_link(path):
            try:
                return real_remove(path)
            finally:
                if plain(path) == watch.link:
                    watch.active = False
        monkeypatch.setattr(tool, "remove_link", remove_link)
    return watch


def spy_missed(watch, link):
    """The control that every wrapper of watch_below took, by position and by keyword: each call it wraps is made once with a path
    below the link that holds nothing (so that none can change a thing; most fail, and are meant to), and again with its path given
    by keyword (PATH_KEYWORDS: the first verifier's D1 was a spy that read the positions alone), and the names of those the spy did
    not see come back, which is none. A keyword that is not the call's comes back too, for the host raises TypeError for it and for
    nothing that a call below a link does otherwise. The calls that take a second path are made again with only the second below
    the link (SECOND_PATH), by position and by keyword. Then the rule for the link itself, by position and by keyword: calls that
    follow it are each seen, and the calls the tool may make of it are not. The spy's calls are cleared."""
    link = Path(link)
    below, other = link / "no such folder" / "x", link / "no such folder" / "y"
    assert watch.calls == [], "the control needs a spy that has seen nothing"
    assert not below.parent.exists(), "the control needs a folder below the link that is not there"
    watch.calls.clear()
    for owner, names in ((os, OS_CALLS), (os.path, OS_PATH_CALLS)):
        for name in names:
            if hasattr(owner, name):
                try:
                    getattr(owner, name)(below)
                except Exception:       # any: the question is whether the spy was told, and it is told before the host answers
                    pass
    for name in PATH_CALLS:
        if hasattr(Path, name):
            try:
                getattr(below, name)()
            except Exception:
                pass
    for opener in (builtins.open, io.open):
        try:
            opener(below, "rb")
        except Exception:
            pass
    missed = [f"{what} by position" for what in sorted(watch.wrapped - {what for what, _ in watch.calls})]
    watch.calls.clear()
    missed += [f"{what} has no keyword form in PATH_KEYWORDS" for what in sorted(watch.wrapped)
               if what not in PATH_KEYWORDS and not what.startswith("Path.")]
    for what in sorted(watch.wrapped & set(PATH_KEYWORDS)):
        owner, name = watch.where[what]
        names = PATH_KEYWORDS[what]
        kwargs = {keyword: (below, other)[i] for i, keyword in enumerate(names)} | OTHER_ARGS.get(what, {})
        args = (below,) if what.startswith("Path.") else ()
        try:
            getattr(owner, name)(*args, **kwargs)
        except TypeError as x:
            missed.append(f"{what}: the keywords {names} are not the call's ({x})")
        except Exception:
            pass
        if what not in {seen for seen, _ in watch.calls}:
            missed.append(f"{what} by keyword")
        watch.calls.clear()
    apart = link.parent / "no such folder apart from the link"
    for what in SECOND_PATH:                                    # the second path of a call that takes two, read as well as the first
        if what not in watch.wrapped:
            continue
        owner, name = watch.where[what]
        names = PATH_KEYWORDS[what]
        if what.startswith("Path."):
            calls = {"by position": ((Path(apart), below), {}), "by keyword": ((Path(apart),), {names[0]: below})}
        else:
            calls = {"by position": ((apart, below), {}), "by keyword": ((), {names[0]: apart, names[1]: below})}
        for how, (args, kwargs) in calls.items():
            try:
                getattr(owner, name)(*args, **kwargs)
            except TypeError as x:
                missed.append(f"{what}, its second path {how}: the call is not the call's ({x})")
            except Exception:
                pass
            if what not in {seen for seen, _ in watch.calls}:
                missed.append(f"{what}, its second path {how}")
            watch.calls.clear()
    for name, follows in (("os.stat", lambda p: os.stat(p)), ("os.listdir", lambda p: os.listdir(p)),
                          ("os.path.exists", lambda p: os.path.exists(p)), ("Path.is_dir", lambda p: Path(p).is_dir()),
                          ("Path.exists", lambda p: Path(p).exists()), ("Path.iterdir", lambda p: list(Path(p).iterdir())),
                          ("os.stat(path=)", lambda p: os.stat(path=p)), ("os.listdir(path=)", lambda p: os.listdir(path=p)),
                          ("os.scandir(path=)", lambda p: list(os.scandir(path=p))),
                          ("os.path.exists(path=)", lambda p: os.path.exists(path=p)), ("open(file=)", lambda p: open(file=p))):
        try:
            follows(link)
        except OSError:                 # opening a directory raises, once it has been told
            pass
        if not watch.calls:
            missed.append(f"{name} of the link itself")
        watch.calls.clear()
    link.is_symlink(), link.is_junction(), os.lstat(link), os.path.lexists(link), link.lstat()
    os.lstat(path=link), os.path.lexists(path=link), os.path.islink(path=link), os.stat(path=link, follow_symlinks=False)
    if watch.calls:
        missed.append(f"calls the tool may make of the link itself were seen: {watch.calls}")
    watch.calls.clear()
    return missed


def tell_links(monkeypatch, tool, *paths):
    """Tell the tool that a link stands at each of `paths`, and at no other path. Returns the test it had before, for a control.

    The tool asks one question of an entry, `tool.is_link`, which is the checker's own test (checker._is_link: a symbolic link or
    a directory junction). A junction whose target is gone is a link on a host that can open it, and the owner's machine cannot
    (found so on 2026-10-30: os.lstat of it raises FileNotFoundError, so that test says nothing is there, and removing it fails
    until its target is made again). A test of what the tool does with a link that leads nowhere therefore makes none (one can be
    taken away again only by making its target again, CLAUDE.md item 10, and a test that failed first would strand it), and tells
    the tool what a host that opens one answers, as tests/tools/test_tools.py's simulate_links tells the privacy gate of a symbolic
    link that the owner's machine may not make. What stands at the path, if anything, is no link: the control is that the told
    answer is true and the real one is false."""
    real = tool.is_link
    told = [Path(p) for p in paths]
    monkeypatch.setattr(tool, "is_link", lambda p: Path(p) in told or real(p))
    return real


def remove_links_under(top):
    """Remove every link under `top`, a junction or a symbolic link: the link itself and nothing behind it, while its target is
    there. None is entered, so a link to `top` itself or to a folder above it is no loop. Returns the links removed, by path.

    Why: a test that fails between the making of a junction and the removal of it strands it with its target, and on the owner's
    machine a junction whose target is gone cannot be removed (os.rmdir, os.unlink, shutil.rmtree, cmd's rmdir and a rename fail
    until the target is made again, MEASURED 2026-10-30 and 2026-10-31). A pytest that later clears an old temporary folder
    removes a folder before the junction that leads into it, in name order, and the junction is then one nothing removes, and the
    folder is renamed `garbage-*`. So every module of P4's tests that makes a junction ends each test, passed or failed, with this
    (a fixture's teardown), while the targets are there."""
    removed = []
    stack = [str(top)]
    while stack:
        here = stack.pop()
        try:
            entries = list(os.scandir(here))
        except OSError:
            continue
        for entry in entries:
            if entry.is_junction() or entry.is_symlink():
                try:
                    os.unlink(entry.path)
                except (IsADirectoryError, PermissionError):
                    os.rmdir(entry.path)
                removed.append(entry.path)
            elif entry.is_dir(follow_symlinks=False):
                stack.append(entry.path)
    return removed


# -- a junction whose target is gone, as a host that opens one shows it: an entry in its parent's listing, and nothing at its path -------
class Ghost:
    """What a directory listing shows of a junction whose target is gone: an entry that says it is a directory and a junction, and
    answers a stat from the listing's own data, as the DirEntry of the owner's machine does (MEASURED by P4.2's builder,
    2026-10-31: is_dir() and is_junction() true, is_symlink() false, stat() answers). Nothing stands at its path."""

    def __init__(self, parent, name):
        self.name, self.path = name, os.path.join(os.fspath(parent), name)

    def is_dir(self, *, follow_symlinks=True):
        return True

    def is_file(self, *, follow_symlinks=True):
        return False

    def is_symlink(self):
        return False

    def is_junction(self):
        return True

    def stat(self, *, follow_symlinks=True):
        return os.stat_result((stat.S_IFDIR | 0o777, 0, 0, 1, 0, 0, 0, 0, 0, 0))

    def inode(self):
        return 0

    def __fspath__(self):
        return self.path

    def __repr__(self):
        return f"<Ghost {self.name!r}>"


class Listing:
    """What os.scandir returns, over `entries`: an iterator and a context manager, as os.walk and the checker use it."""

    def __init__(self, entries):
        self.entries = iter(entries)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.entries)

    def close(self):
        pass


class Dangling:
    """The stand-in dangling_link makes. `listed`: whether its parent still lists it (the os.rmdir of it ends that). `real` holds the
    functions it replaced, so that a test can ask the host what is really there."""

    def __init__(self, link, error, real, access=True):
        self.link, self.error, self.real, self.listed, self.access = Path(link), error, real, True, access
        self.parent, self.name = self.link.parent, self.link.name

    def real_names(self):
        """The names its parent really holds, whatever the listing shows."""
        return sorted(self.real["listdir"](self.parent))


def dangling_link(monkeypatch, link, error=FileNotFoundError, access=True):
    """A junction whose target is gone, as a host that opens one shows it, with NOTHING at its path: only the listing of its parent
    shows it (os.scandir and os.listdir, which Path.iterdir and os.walk go by), as an entry of a junction. Everything else is the
    host's own answer about a path where nothing stands: every stat, open, resolve and test of a path says it is not there, whatever
    the spelling of the path (a trailing separator, a `.` component, another case), and no call is told so. What is told, for that
    path alone, is what only a link has: os.unlink of it raises PermissionError, as of a directory link that wants rmdir, so that
    the tool's removal goes by its rmdir; os.rmdir of it drops the entry from its parent's listing; and os.access answers `access`,
    which is yes as the owner's machine says of a junction whose target is gone (MEASURED, 2026-10-31, F_OK) and no as a host that
    answered otherwise would (P4.2's first verifier, note 2: a tool that decided by os.access would behave the same on the owner's
    machine and on that host, and a test run both ways is what shows it). It stands in for a junction a host that opens one can
    remove, which the owner's machine cannot (the stated limit, docs/P4.md), so no test makes one.
    With `error` NotADirectoryError, the host's answer for a junction whose target has become a file, os.lstat, os.stat, os.scandir
    and os.listdir of it raise that too (MEASURED: errno 20, winerror 267). Returns the Dangling stand-in; tell_links tells the
    tool's own test of a link, which is a thing apart."""
    real = {n: getattr(os, n) for n in ("scandir", "listdir", "unlink", "remove", "rmdir", "access", "lstat", "stat")}
    stand = Dangling(link, error, real, access)
    asked = (error is NotADirectoryError)

    def key(p):
        return os.path.normcase(os.path.abspath(os.fsdecode(p))) if isinstance(p, (str, bytes, os.PathLike)) else None

    here, parent = key(stand.link), key(stand.parent)

    def at_link(p):
        return stand.listed and key(p) == here

    def scandir(path="."):
        if stand.listed and key(path) == parent:
            with real["scandir"](path) as listing:
                entries = list(listing)
            return Listing(entries + [Ghost(stand.parent, stand.name)])
        if asked and at_link(path):
            raise NotADirectoryError(20, "The directory name is invalid", os.fsdecode(path))
        return real["scandir"](path)

    def listdir(path=None):
        if path is None:
            path = "."
        if stand.listed and key(path) == parent:
            return list(real["listdir"](path)) + [stand.name]
        if asked and at_link(path):
            raise NotADirectoryError(20, "The directory name is invalid", os.fsdecode(path))
        return real["listdir"](path)

    def unlink(path, *args, **kwargs):
        if at_link(path):
            raise PermissionError(13, "Access is denied", os.fsdecode(path))
        return real["unlink"](path, *args, **kwargs)

    def rmdir(path, *args, **kwargs):
        if at_link(path):
            stand.listed = False
            return None
        return real["rmdir"](path, *args, **kwargs)

    def access(path, mode, *args, **kwargs):
        return stand.access if at_link(path) else real["access"](path, mode, *args, **kwargs)

    def raising(name):
        def call(path, *args, **kwargs):
            if asked and at_link(path):
                raise NotADirectoryError(20, "The directory name is invalid", os.fsdecode(path))
            return real[name](path, *args, **kwargs)
        return call

    for name, replacement in (("scandir", scandir), ("listdir", listdir), ("unlink", unlink), ("remove", unlink), ("rmdir", rmdir),
                              ("access", access), ("lstat", raising("lstat")), ("stat", raising("stat"))):
        monkeypatch.setattr(os, name, replacement)
    return stand


def there_missed(path):
    """The calls dangling_link tells, asked of a path that really leads somewhere, answer as the host does: the problems found, none."""
    path, problems = Path(path), []
    try:
        os.stat(path), os.lstat(path), os.listdir(path), path.stat(), path.lstat(), list(path.iterdir())
        with os.scandir(path) as listing:
            list(listing)
        if not (os.path.realpath(path, strict=True) and path.resolve(strict=True)):
            problems.append("a strict resolve is empty")
    except Exception as x:
        problems.append(f"a call about {path.name} raised {type(x).__name__}")
    says = (os.path.exists(path), os.path.isdir(path), not os.path.isfile(path), os.path.lexists(path), os.access(path, os.F_OK),
            path.exists(), path.is_dir(), not path.is_file())
    if not all(says):
        problems.append(f"{path.name} is a directory that is there, and some test of it says otherwise: {says}")
    return problems


def dangling_missed(stand, others=()):
    """The control that each telling of dangling_link took, that nothing else is told, and that it took for that path alone: the
    problems found, which are none. `others` are paths that lead somewhere (the same name at another path, the parent itself):
    there_missed finds the host's own answers for each."""
    link, parent, name, error, problems = stand.link, stand.parent, stand.name, stand.error, []
    if not stand.listed:
        problems.append("the stand-in is no longer listed")
    for what, listed in (("os.listdir", os.listdir(parent)), ("os.scandir", [e.name for e in os.scandir(parent)]),
                         ("Path.iterdir", [p.name for p in parent.iterdir()])):
        if name not in listed:
            problems.append(f"{what} of its parent does not list it")
    if name in stand.real_names():
        problems.append("something really stands at its path")
    entry = next((e for e in os.scandir(parent) if e.name == name), None)
    if entry is None or not (entry.is_dir() and entry.is_junction() and not entry.is_symlink() and not entry.is_file()
                             and stat.S_ISDIR(entry.stat().st_mode)):
        problems.append("its entry does not say directory and junction, and answer a stat")
    calls = [("os.stat", lambda: os.stat(link)), ("os.lstat", lambda: os.lstat(link)), ("Path.stat", link.stat),
             ("Path.lstat", link.lstat), ("os.scandir", lambda: os.scandir(link)), ("os.listdir", lambda: os.listdir(link)),
             ("Path.iterdir", lambda: list(link.iterdir()))]
    if error is FileNotFoundError:            # nothing stands there, so the host's own answers, with no call told
        calls += [("os.path.realpath(strict)", lambda: os.path.realpath(link, strict=True)),
                  ("Path.resolve(strict)", lambda: link.resolve(strict=True)), ("os.utime", lambda: os.utime(link)),
                  ("open", lambda: open(link, "rb")), ("os.path.getsize", lambda: os.path.getsize(link)),
                  ("os.stat, spelt with a trailing separator", lambda: os.stat(str(link) + os.sep)),
                  ("os.stat, spelt with a dot", lambda: os.stat(os.path.join(str(link), ".")))]
    for what, call in calls:
        try:
            call()
            problems.append(f"{what} did not raise {error.__name__}")
        except error:
            pass
        except Exception as x:
            problems.append(f"{what} raised {type(x).__name__}, not {error.__name__}")
    says = {"os.path.exists": os.path.exists(link), "os.path.isdir": os.path.isdir(link), "os.path.isfile": os.path.isfile(link),
            "os.path.lexists": os.path.lexists(link), "Path.exists": link.exists(), "Path.is_dir": link.is_dir(),
            "Path.is_file": link.is_file()}
    problems += [f"{what} says yes" for what, yes in says.items() if yes]
    spellings = [link, str(link) + os.sep, os.path.join(str(link), ".")] + ([str(link).upper()] if os.name == "nt" else [])
    for spelling in spellings:                                    # told for the path, however it is spelt
        if os.access(spelling, os.F_OK) is not stand.access:
            problems.append(f"os.access of {str(spelling)!r} does not say {'yes' if stand.access else 'no'}")
    for what, call in (("os.unlink", lambda: os.unlink(link)), ("Path.unlink", link.unlink), ("os.remove", lambda: os.remove(link))):
        try:
            call()
            problems.append(f"{what} took it")
        except PermissionError:
            pass
    if not stand.listed:
        problems.append("a refused unlink dropped the entry")
    probe_file, probe_dir = parent / ".dangling-probe-file", parent / ".dangling-probe-dir"
    probe_file.write_bytes(b"")
    probe_dir.mkdir()
    try:                                       # another path in the same folder: the host's own removals, which take them
        os.unlink(probe_file)
        os.rmdir(probe_dir)
    except PermissionError:
        problems.append("a removal of another path in the stand-in's folder is told")
    finally:
        if probe_file.exists():
            stand.real["unlink"](probe_file)
        if probe_dir.exists():
            stand.real["rmdir"](probe_dir)
    if not stand.listed:
        problems.append("a removal of another path in the stand-in's folder dropped the entry")
    for other in others:
        problems += there_missed(other)
    return problems


def metadata_json(path):
    return json.loads(Path(path).read_bytes())


# -- a sanity check of the Turtle text, with no parser: what the quick stage can know before an engine reads it -----------
SH_NAMES = frozenset((
    "NodeShape", "PropertyShape", "name", "description", "message", "severity", "Violation", "Warning", "Info",
    "targetClass", "targetSubjectsOf", "targetObjectsOf", "targetNode", "nodeKind", "IRI", "datatype", "class", "in",
    "hasValue", "pattern", "minLength", "maxLength", "minInclusive", "maxInclusive", "minCount", "maxCount", "closed",
    "ignoredProperties", "or", "not", "qualifiedValueShape", "qualifiedMinCount", "property", "path", "inversePath",
    "oneOrMorePath"))
_STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
_IRIREF = re.compile(r"<[^<>\s]*>")


def strip_literals(text):
    """The Turtle without its comments, its string literals and its IRIs: what is left is names, brackets and dots."""
    lines = [ln for ln in text.splitlines() if not ln.startswith("#")]
    return _IRIREF.sub("<>", _STRING.sub('""', "\n".join(lines)))


def turtle_problems(text):
    """What is wrong with a Turtle text that a reader of it would stop at, found without one: an unbalanced bracket,
    a statement that does not end, a prefix used and not declared, an sh: name that SHACL Core does not have."""
    out = []
    if not text.isascii() or "\r" in text or "\t" in text or not text.endswith("\n"):
        out.append("not ASCII with LF line ends, no tab, and a final line feed")
    body = strip_literals(text)
    declared = set(re.findall(r"^@prefix (\w+): <", body, re.M))
    body = re.sub(r"^@prefix .*$", "", body, flags=re.M)
    for open_, close in (("[", "]"), ("(", ")")):
        if body.count(open_) != body.count(close):
            out.append(f"unbalanced {open_}{close}")
    depth = 0
    for ch in body:
        depth += (ch in "[(") - (ch in "])")
        if depth < 0:
            out.append("a bracket closed before it opened")
            break
    for prefix in sorted(set(re.findall(r"(?<![\w:])([A-Za-z]\w*):[A-Za-z]", body)) - declared):
        out.append(f"the prefix {prefix}: is used and not declared")
    for name in sorted(set(re.findall(r"\bsh:(\w+)", body)) - SH_NAMES):
        out.append(f"sh:{name} is no name SHACL Core has")
    statements = [s for s in re.split(r"\n\n", body) if s.strip()]
    for s in statements:
        if not s.rstrip().endswith(" ."):
            out.append(f"a statement that does not end in ' .': {s.strip()[:40]!r}")
    return out


# -- every crate plant of any parcel whose control row says it is accepted ---------------------------------------------------
def accepted_control_problems(shapes, controls=None, plants=None):
    """Gate 1 over the other parcels' plants: the checker accepts each crate plant whose control row says `accepted`, so
    every must shape must conform to it. Returns (problems, how many were examined). A plant that is a custody log, not
    a crate, is not one the shapes read."""
    from controls import registry
    controls = registry.CONTROLS if controls is None else controls
    made = registry.plants() if plants is None else plants
    problems, examined = [], 0
    for c in controls:
        if c.expected != "accepted" or c.name not in made:
            continue
        with tempfile.TemporaryDirectory() as d:
            planted = made[c.name](d)
            if isinstance(planted, tuple):
                continue
            examined += 1
            verdict = p4_examples.checker_verdict(planted)
            if verdict != "accepted":
                problems.append(f"{c.name}: the control row says accepted, and the checker says {verdict}")
                continue
            md = metadata_json(Path(planted) / canonical.DESCRIPTOR)
            try:
                triples = p4_expand.expand(md)
            except p4_expand.ExpandError as x:
                problems.append(f"{c.name}: the checker accepts it, and the expansion refuses it: {x}")
                continue
            failing = must_failing(shapes, triples)
            if failing:
                problems.append(f"{c.name}: the checker accepts it, and {sorted(failing)} fail")
    return problems, examined
