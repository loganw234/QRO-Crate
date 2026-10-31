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
import subprocess
import sys
import tempfile
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


def load_tool():
    """tools/gen_profile.py as a module of its own, loaded by its path."""
    spec = importlib.util.spec_from_file_location("gen_profile_under_test", ROOT / "tools" / "gen_profile.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def run_patched(tree_root, args, prelude, cwd):
    """tools/gen_profile.py of `tree_root` as a process in whose interpreter `prelude` (Python source) has run first, as the tool's
    own `__main__`: what a test needs to make a host do what the host here will not (list no directory, give no stderr, a package
    that raises as it is imported)."""
    code = ("import runpy, sys\n" + prelude + "\nsys.argv = [sys.argv[1], *" + repr(list(args)) + "]\n"
            "runpy.run_path(sys.argv[0], run_name='__main__')")
    return subprocess.run([sys.executable, "-c", code, str(Path(tree_root) / "tools" / "gen_profile.py")], cwd=cwd,
                          capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))


def watch_reads(monkeypatch, base):
    """A list that fills with (what, path) for each path under `base` (or `base` itself) that the code lists, walks or opens
    from now on: the tree of a test whose profile/ is a link, where the tool may ask whether it is a link (an lstat, which
    this does not see) and nothing else."""
    seen, norm = [], os.path.normcase(str(base))

    def note(what, p):
        if isinstance(p, (str, bytes, os.PathLike)):
            s = os.path.normcase(os.fsdecode(p))
            if s == norm or s.startswith(norm + os.sep):
                seen.append((what, os.fsdecode(p)))

    def spy(module, name):
        real = getattr(module, name)

        def watched(*a, **k):
            note(name, a[0] if a else next(iter(k.values()), None))
            return real(*a, **k)
        monkeypatch.setattr(module, name, watched)

    for module, name in ((os, "walk"), (os, "scandir"), (os, "listdir"), (builtins, "open"), (io, "open")):
        spy(module, name)
    for name in ("read_bytes", "read_text", "open", "iterdir", "stat", "is_dir", "is_file", "exists"):
        real = getattr(Path, name)

        def watched_method(self, *a, _real=real, _name=name, **k):
            if not (_name == "stat" and k.get("follow_symlinks", True) is False):      # Path.lstat is that: it follows nothing
                note("Path." + _name, self)
            return _real(self, *a, **k)
        monkeypatch.setattr(Path, name, watched_method)
    return seen


def tell_links(monkeypatch, tool, *paths):
    """Tell the tool that a link stands at each of `paths`, and at no other path. Returns the test it had before, for a control.

    The tool asks one question of an entry, `tool.is_link`, which is the checker's own test (checker._is_link: a symbolic link or
    a directory junction). A junction whose target is gone is a link on a host that can open it, and the owner's machine cannot
    (found so on 2026-10-30: os.lstat of it raises FileNotFoundError, so that test says nothing is there, and removing it fails
    until its target is made again). A test of what the tool does with a link that leads nowhere therefore makes none, for it
    could not take it away again, and tells the tool what a host that opens one answers, as tests/tools/test_tools.py's
    simulate_links tells the privacy gate of a symbolic link that the owner's machine may not make. What stands at the path, if
    anything, is no link: the control is that the told answer is true and the real one is false."""
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
