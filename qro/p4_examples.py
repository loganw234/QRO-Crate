"""P4's examples: the positive examples and P4's own plants (P4's design, item 6), and the judge that holds a crate to the
checker and to the shapes at once.

A plant is one fault planted in P0's fixture crate. It declares what the checker must say of it and which must shapes
must fail, and the tests run both: the checker on the crate, the evaluator on its metadata. Four kinds are here, and
the matrix of profile/EXAMPLES.md prints them in that order:
  - faults the shapes see: a must shape fails, and the checker refuses by one of the names the failing shapes claim (a
    plant is one fault, and the soundness gate holds that the name is claimed; the sweeps hold the same of the edits of
    the fixture they make, tests/p4/test_p4_sweeps.py and test_p4_families.py);
  - faults only the checker sees, which state the shapes' limits by example (the bytes, a key no context defines, the
    order of a list, a month 13, a compact IRI for an id): the shapes conform and the checker refuses;
  - edge cases the checker accepts at every step before the last (its verdict is `metadata-generated`, since step 9
    refuses any hand-edited metadata, and so also means that steps 1 to 8 held): every must shape must conform. These
    are where a shape stricter than the checker would show, and they were found by reading the checker's code, not by
    running the shapes;
  - crates whose id the reader refuses (FORMAT.md item 22) and the expansion refuses to read (an id RDF reads as another
    IRI, as a blank node or as the root), so that the checker has refused them and the evaluator abstains. A real engine does
    not abstain: it fails `entity` on a blank-node id, `term-name` on an id that begins with an at sign,
    `file-digest-present` on an absolute `file:` id and `term-haspart` on a reference to a blank node, on crates refused
    first, by a name the failing shape claims (every must shape claims `spelling`, which the checker refuses an id outside
    the rule, and `graph-form`, which it refuses a reference outside it: limit 19). The `engine` field says which, and
    tests/p4shacl/test_p4shacl_crates.py holds it against pyshacl.
Every other parcel's crate plants are held to the same soundness by tests/p4/test_p4_examples.py, and never listed
here: a generated page that every parcel's plants regenerate is a merge conflict (P0.1's verifier, round 1, D3).

The plants for each term of the table are generated from it, one that breaks the term's spelling and one that puts it
where its domain does not admit it, so a row that gains a shape gains its plants. Nothing here writes into the
repository: a crate is built in a temporary directory. Stdlib only.
"""
import copy
import dataclasses
import json
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from qro import canonical, checker, fixture
from qro import spelling as S
from qro import vocabulary as V
from qro.p4_eval import Graph, failing, validate
from qro.p4_expand import ExpandError, expand
from qro.p4_shapes import build, slug
from qro.refusal import Refused

NOTES, RAW, DESC, ROOT = "data/notes.txt", "data/raw.counts.json", V.DESC, V.ROOT
HOST = "#p4-host"                      # a fresh entity a plant adds: not a path in the crate, and not the root
GENERATED = "metadata-generated"       # step 9's name: what the checker says of a hand-edited fixture that steps 1 to 8 hold


@dataclass(frozen=True)
class Plant:
    """One fault in the fixture. `edit(graph)` changes the metadata's entities in place (the graph's order is made
    again after it); `files(crate)` may change the crate's files after the metadata is written."""
    name: str
    fault: str
    edit: object
    checker: str                       # the refusal the checker must give, GENERATED for an edge the checker accepts
    shapes: tuple = ()                 # the must shapes that must fail, by local name; () means every one conforms
    why: str = ""                      # for a fault the shapes cannot see: the sentence the matrix prints
    files: object = None
    family: str = ""
    unreadable: bool = False           # the expansion refuses it (an id it does not resolve): the evaluator abstains
    engine: tuple = ()                 # an unreadable plant's must shapes that a real engine fails: each is stricter than the checker


@dataclass(frozen=True)
class Judgement:
    checker: str                       # "accepted", or a refusal's name
    must: tuple = ()                   # local names of the must shapes that fail
    should: tuple = ()
    unreadable: str = ""               # the expansion's reason, where the shapes could not read the metadata


def local(shape_id):
    return shape_id.split("#", 1)[1]


def entity(graph, i):
    return next(e for e in graph if e["@id"] == i)


def drop(i, key):
    return lambda g: entity(g, i).pop(key)


def setv(i, key, value):
    return lambda g: entity(g, i).__setitem__(key, value)


def add(*entities):
    return lambda g: g.extend(copy.deepcopy(list(entities)))


def refs(*ids):
    return sorted(({"@id": i} for i in ids), key=lambda r: r["@id"])


def root(g):
    return entity(g, ROOT)


def also(*edits):
    def run(g):
        for edit in edits:
            edit(g)
    return run


def mention(*ids):
    def run(g):
        root(g)["mentions"] = refs(*ids)
    return run


def part(*ids):
    def run(g):
        root(g)["hasPart"] = sorted(root(g)["hasPart"] + refs(*ids), key=lambda r: r["@id"])
    return run


def profile(i):
    return lambda g: next(e for e in g if e["@id"] == i)


def arranged(md):
    """The metadata with its graph in the one order the writer makes, and nothing else changed: a plant's fault is the
    edit, never the order (a list's order and the type order are plants of their own)."""
    g = md["@graph"]
    md["@graph"] = g[:2] + sorted(g[2:], key=lambda e: e.get("@id", ""))          # an entity with no id sorts first
    return md


def metadata_of(crate):
    return json.loads((Path(crate) / canonical.DESCRIPTOR).read_bytes())


def write_metadata(crate, md):
    (Path(crate) / canonical.DESCRIPTOR).write_bytes(canonical.dumps(md))


def prepare():
    """The checker as the command line has it with --fixtures: the fixture's raw form and generator, and every
    parcel's steps. A test calls this under monkeypatch, which restores the registries."""
    fixture.register()
    checker.load()


class Workspace:
    """The fixture crate in a temporary directory, into which plants are written one at a time and judged, and the
    shapes they are judged by. One crate is reused: a plant that changes a file is built in a copy."""

    def __init__(self, shapes=None):
        self.tmp = tempfile.TemporaryDirectory()
        self.crate = fixture.make(Path(self.tmp.name) / "crate")
        self.pristine = metadata_of(self.crate)
        self.shapes = build() if shapes is None else shapes

    def close(self):
        self.tmp.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def fresh(self):
        return copy.deepcopy(self.pristine)

    def of_plant(self, plant):
        md = self.fresh()
        plant.edit(md["@graph"])
        return arranged(md)

    @contextmanager
    def staged(self, md, files=None):
        """The crate with `md` as its metadata, and `files(crate)` applied if given, which is the reused crate or a copy
        of it; the reused crate's metadata is restored when the block ends."""
        if files is None:
            write_metadata(self.crate, md)
            try:
                yield self.crate
            finally:
                write_metadata(self.crate, self.pristine)
        else:
            with tempfile.TemporaryDirectory() as d:
                crate = Path(shutil.copytree(self.crate, Path(d) / "crate"))
                files(crate)
                write_metadata(crate, md)
                yield crate

    def judge_metadata(self, md, files=None):
        """The checker's verdict on the crate with `md` as its metadata, and the shapes' on `md` itself."""
        with self.staged(md, files) as crate:
            return judge(crate, md, self.shapes)

    def judge(self, plant):
        return self.judge_metadata(self.of_plant(plant), plant.files)


def checker_verdict(crate):
    try:
        checker.check(crate)
    except Refused as r:
        return r.name
    return "accepted"


def shapes_verdict(md, shapes):
    """(must, should, unreadable): the local names of the shapes that fail, or why the expansion would not read it."""
    try:
        triples = expand(md)
    except ExpandError as x:
        return (), (), str(x)
    results = validate(shapes, Graph(triples))
    return tuple(local(i) for i in failing(results, "must")), tuple(local(i) for i in failing(results, "should")), ""


def judge(crate, md, shapes):
    must, should, unreadable = shapes_verdict(md, shapes)
    return Judgement(checker_verdict(crate), must, should, unreadable)


# -- the host and the value a term takes ---------------------------------------------------------------------------
def bad_value(t):
    """A value that is in no way in the term's spelling, in the shape of a value the term may hold."""
    base, _, rest = t.spelling.partition(":")
    value = {"integer": "not an integer", "size": 5, "digest": "XYZ", "commit": "XYZ", "rational": "1/2/3",
             "binary64": "xx", "time": "yesterday", "date": "yesterday", "text": "", "iri": "not an iri",
             "ref": "a plain string", "slot": "filled", "word": "zz-not-a-word"}[base]
    return [value] if t.many else value


def valid_values(t):
    """Two different values in the term's one spelling, or None where the spelling has no two (a slot, a word set of
    one word)."""
    base, _, rest = t.spelling.partition(":")
    if base == "word":
        words = list(V.WORDS[rest])
        return words[:2] if len(words) > 1 else None
    return {"integer": [1, 2], "size": ["1", "2"], "digest": ["a" * 64, "b" * 64], "commit": ["a" * 40, "b" * 40],
            "rational": ["1/2", "1/3"], "binary64": [S.binary64(0.5), S.binary64(0.25)],
            "time": ["2026-10-14T00:00:00Z", "2026-10-15T00:00:00Z"], "date": ["2026-10-14", "2026-10-15"],
            "text": ["x", "y"], "iri": ["https://example.org/x", "https://example.org/y"],
            "ref": [{"@id": "https://example.org/ref"}, {"@id": "https://example.org/ref2"}]}.get(base)


def valid_value(t):
    """A value in the term's one spelling, in the shape of a value the term may hold: for a term that is a list, two
    different values where there are two, sorted as the writer sorts them."""
    base, _, rest = t.spelling.partition(":")
    if t.many:
        two = valid_values(t)
        return sorted(two, key=canonical.sort_key) if two else [valid_value(dataclasses.replace(t, many=False))]
    value = {"integer": 1, "size": "1", "digest": "a" * 64, "commit": "a" * 40, "rational": "1/2",
             "binary64": S.binary64(0.5), "time": "2026-10-14T00:00:00Z", "date": "2026-10-14", "text": "x",
             "iri": "https://example.org/x", "ref": {"@id": "https://example.org/ref"},
             "slot": "none"}.get(base)
    if base == "word":
        value = next(iter(V.WORDS[rest]))
    return value


# The terms whose bad value is held first by another rule of the reader than their spelling: the refusal it gives, and
# the entity it is put on.
ENTANGLED = {"about": ("graph-form", DESC), "conformsTo": ("graph-form", ROOT), "version": ("context", V.PROFILE)}
# ... and for a term given two values: a profile's version that is a list is no text, a misshapen entity (P0.4)
ENTANGLED_MANY = {"version": ("graph-form", V.PROFILE)}


def actions():
    return [y.key for y in V.TYPES if y.action]


def host_for(token, g, fresh):
    """The entity a term of domain `token` is put on: an entity of the crate named by id, or the one the token names
    (the root, the descriptor, a File the crate holds, a raw result, a profile's), or else a fresh entity `fresh` of
    the type, which the root mentions if it is an action."""
    ids = {e["@id"] for e in g}
    token = {V.LOCAL: NOTES, "Profile": V.PROFILE, "qro:RawResult": RAW}.get(token, token)
    if token in ids:
        return entity(g, token)
    host = {"@id": fresh, "@type": "CreativeWork" if token == "*" else token}
    g.append(host)
    if token in actions():
        mention(*[e["@id"] for e in g if set(canonical.types(e)) & set(actions())])(g)
    return host


def spelling_plant(t):
    """The term's value in no spelling it has, on an entity its domain admits."""
    refusal, where = ENTANGLED.get(t.key, ("spelling", t.domain[0]))

    def edit(g):
        host_for(where, g, HOST)[t.key] = bad_value(t)
    return Plant("spell-" + slug(t.key), f"{t.key} given a value in none of its spelling ({t.spelling})", edit, refusal,
                 ("term-" + slug(t.key),), family="spelling")


def domain_plant(t):
    """The term, in its spelling, on an entity of a type its domain does not admit."""
    outside = next(c for c in ("CreativeWork", "IndividualProduct", "SoftwareApplication") if c not in t.domain)

    def edit(g):
        g.append({"@id": HOST, "@type": outside, t.key: valid_value(t)})
    return Plant("domain-" + slug(t.key), f"{t.key} on a {outside}, which its domain ({', '.join(t.domain)}) does not "
                 "admit", edit, "graph-form", ("domain-" + slug(t.key),), family="domain")


def cardinality_plant(t):
    """A single-valued term given two valid values: more than one value, though each is in the spelling."""
    refusal, where = {**ENTANGLED, **ENTANGLED_MANY}.get(t.key, ("spelling", t.domain[0]))

    def edit(g):
        host_for(where, g, HOST)[t.key] = sorted(valid_values(t), key=canonical.sort_key)
    return Plant("many-" + slug(t.key), f"{t.key}, which has one value, given two of its spelling", edit, refusal,
                 ("term-" + slug(t.key),), family="cardinality")


def generated():
    """The plants the table makes: a spelling fault and a domain fault a term, and for a term of one value, two."""
    out = [spelling_plant(t) for t in V.TERMS]
    out += [domain_plant(t) for t in V.TERMS if "*" not in t.domain]
    return out + [cardinality_plant(t) for t in V.TERMS if not t.many and valid_values(t) is not None]


# -- the handwritten plants ----------------------------------------------------------------------------------------
PRC = V.PROCESS_RUN_CRATE
JOB = {"@id": "#a1", "@type": "CreateAction"}
CC = "https://creativecommons.org/licenses/by/4.0/"


def bytes_changed(crate):
    (Path(crate) / NOTES).write_bytes(b"not the bytes the metadata names\n")


def raw_moved(crate):
    (Path(crate) / RAW).write_bytes(canonical.compact({"00": 2, "01": 2, "11": 4}))


def wrong_digest(g):
    entity(g, NOTES)["sha256"] = "f" * 64


def retype(i, *types):
    return setv(i, "@type", list(types) if len(types) > 1 else types[0])


PLANTS = (
    # the descriptor
    Plant("descriptor-extra-key", "a name added to the metadata descriptor", setv(DESC, "name", "x"), "graph-form",
          ("descriptor",), family="descriptor"),
    Plant("descriptor-other-profile", "the descriptor conforms to RO-Crate 1.2",
          setv(DESC, "conformsTo", [{"@id": "https://w3id.org/ro/crate/1.2"}]), "graph-form", ("descriptor",),
          family="descriptor"),
    Plant("descriptor-type-dataset", "the descriptor typed Dataset", retype(DESC, "Dataset"), "graph-form",
          ("descriptor",), family="descriptor"),
    Plant("descriptor-two-types", "the descriptor typed CreativeWork and Dataset", retype(DESC, "CreativeWork", "Dataset"),
          "graph-form", ("descriptor",), family="descriptor"),
    Plant("descriptor-about-a-file", "the descriptor about a file, not the root", setv(DESC, "about", {"@id": NOTES}),
          "graph-form", ("descriptor", "root"), family="descriptor"),
    # the root
    Plant("root-not-a-dataset", "the root typed CreativeWork", retype(ROOT, "CreativeWork"), "graph-form",
          ("root",), family="root"),
    Plant("root-is-an-action", "the root typed CreateAction as well as Dataset", retype(ROOT, "CreateAction", "Dataset"),
          "graph-form", ("root",), family="root"),
    Plant("root-no-license", "the root without its license", drop(ROOT, "license"), "graph-form", ("root",),
          family="root"),
    Plant("root-no-name", "the root without its name", drop(ROOT, "name"), "graph-form", ("root",), family="root"),
    Plant("root-no-signature", "the root without its signature slot", drop(ROOT, "qro:signature"), "graph-form",
          ("root",), family="root"),
    Plant("root-one-profile", "the root conforms to Process Run Crate alone", setv(ROOT, "conformsTo", refs(PRC)),
          "graph-form", ("root",), family="root"),
    Plant("root-third-profile", "the root conforms to a third profile as well",
          setv(ROOT, "conformsTo", refs(PRC, V.PROFILE, "https://example.org/profile")), "graph-form", ("root",),
          family="root"),
    # actions and mentions
    Plant("action-not-mentioned", "an action the root does not mention", add(JOB), "graph-form",
          ("action-mentioned",), family="actions"),
    Plant("mentions-a-file", "the root mentions a file, which is no action", mention(NOTES), "graph-form", ("root",),
          family="actions"),
    Plant("mentions-an-absolute-iri", "the root mentions an IRI that names no action",
          mention("https://example.org/x"), "graph-form", ("root",), family="actions"),
    # files
    Plant("file-no-sha256", "a file without its sha256", drop(NOTES, "sha256"), "file-digest",
          ("file-digest-present",), family="files"),
    Plant("file-no-size", "a file without its contentSize", drop(NOTES, "contentSize"), "file-digest",
          ("file-digest-present",), family="files"),
    Plant("raw-no-sha256", "a raw result without its sha256", drop(RAW, "sha256"), "raw-digest",
          ("file-digest-present",), family="files"),
    Plant("file-unlisted", "a file the root's hasPart does not reach", setv(ROOT, "hasPart", refs(RAW)),
          "file-unlisted", ("file-reached",), family="files"),
    Plant("raw-not-a-file", "a raw result that is not a File", retype(RAW, "qro:RawResult"), "graph-form",
          ("rawresult-form", "domain-sha256", "domain-contentsize"), family="files"),
    Plant("raw-bare-not-a-file", "a raw result that is no File and carries no File term, so that its file is listed by nothing",
          also(retype(RAW, "qro:RawResult"), drop(RAW, "sha256"), drop(RAW, "contentSize"), drop(RAW, "encodingFormat")),
          "file-unlisted", ("rawresult-form",), family="files"),
    Plant("raw-no-form", "a raw result that names no raw form", drop(RAW, "qro:rawForm"), "raw-form",
          ("rawresult-form",), family="files"),
    # the profiles' contextual entities
    Plant("profile-entity-missing", "this profile's contextual entity removed",
          lambda g: g.remove(entity(g, V.PROFILE)), "graph-form", ("profile-entities", "profile-version"),
          family="profiles"),
    Plant("profile-version-wrong", "this profile's version 0.2", setv(V.PROFILE, "version", "0.2"), "context",
          ("profile-version",), family="profiles"),
    Plant("prc-version-wrong", "Process Run Crate's version 0.5", setv(PRC, "version", "0.5"), "context",
          ("profile-version",), family="profiles"),
    Plant("profile-version-missing", "this profile's version removed", drop(V.PROFILE, "version"), "graph-form",
          ("profile-version",), family="profiles"),
    Plant("profile-name-wrong", "this profile's name changed", setv(V.PROFILE, "name", "Another"), "graph-form",
          ("profile-entities",), family="profiles"),
    Plant("profile-entity-extra-key", "a description on this profile's contextual entity",
          setv(V.PROFILE, "description", "x"), "graph-form", ("profile-entities",), family="profiles"),
    Plant("profile-type-incomplete", "this profile's entity typed Profile alone", retype(V.PROFILE, "Profile"),
          "graph-form", ("profile-entities",), family="profiles"),
    Plant("profile-type-extra", "this profile's entity typed Dataset as well",
          retype(V.PROFILE, "CreativeWork", "Dataset", "Profile"), "graph-form", ("profile-entities",), family="profiles"),
    Plant("profile-entity-extra", "a Profile entity for a profile the root does not conform to",
          add({"@id": V.ROCRATE, "@type": ["CreativeWork", "Profile"], "name": "RO-Crate", "version": "1.3"}),
          "graph-form", ("profile-entities",), family="profiles"),
    # the vocabulary and the types
    Plant("qro-term-unknown", "a qro: term the table does not name", setv(ROOT, "qro:nonesuch", "x"), "term-unknown",
          ("entity",), family="vocabulary"),
    Plant("rocrate-key-no-kind", "a key RO-Crate defines and the table gives no kind", setv(ROOT, "keywords", "x"),
          "field-kind", ("entity",), family="vocabulary"),
    Plant("type-unlisted-defined", "a type RO-Crate defines and the table does not list", retype(NOTES, "File", "Person"),
          "term-unknown", ("entity",), family="vocabulary"),
    Plant("type-unlisted-undefined", "a type no context defines", retype(NOTES, "File", "Foo"), "term-unknown",
          ("entity",), family="vocabulary"),
    Plant("entity-no-type", "an entity without a type", add({"@id": HOST, "name": "x"}), "graph-form", ("entity",),
          family="vocabulary"),
    Plant("entity-no-id", "an entity without an @id, which RDF reads as a blank node", add({"@type": "CreativeWork", "name": "x"}),
          "graph-form", ("entity",), family="vocabulary"),
    # faults only the checker sees: the shapes' limits, by example
    Plant("key-in-neither", "a key neither the table nor RO-Crate's context names", setv(ROOT, "madeUp", "x"),
          "term-unknown", why="JSON-LD drops a key its context does not define, so it never reaches RDF (limit 5)",
          family="limits"),
    Plant("name-a-list", "a single value written as a one-element list", setv(ROOT, "name", ["QRO-Crate P0 fixture"]),
          "spelling", why="a value and a one-element list are one triple (limit 6)", family="limits"),
    Plant("hasPart-unsorted", "the root's hasPart in the wrong order",
          setv(ROOT, "hasPart", refs(RAW, NOTES)[::-1]), "spelling",
          why="the order of a list is invisible to RDF (limit 6)", family="limits"),
    Plant("date-month-13", "a publication date in month 13", setv(ROOT, "datePublished", "2026-13-01"), "spelling",
          why="a pattern holds the form of a date, not that it is real (limit 3)", family="limits"),
    Plant("time-feb-30", "a time on 30 February", setv(ROOT, "qro:writtenAt", "2026-02-30T00:00:00Z"), "spelling",
          why="a pattern holds the form of a time, not that it is real (limit 3)", family="limits"),
    Plant("rational-not-lowest", "a rational not in lowest terms",
          add({"@id": HOST, "@type": "qro:Measuring", "qro:alpha": "2/4"}), "spelling",
          why="a pattern holds the form of a rational, not its lowest terms (limit 3)", family="limits"),
    Plant("file-bytes-changed", "a file's bytes changed under its digest", lambda g: None, "file-digest",
          why="the bytes of a file are the checker's alone (limit 7)", files=bytes_changed, family="limits"),
    Plant("file-digest-wrong", "a file's digest that is not its bytes'", wrong_digest, "file-digest",
          why="a digest of the right form is the checker's to compare with the bytes (limit 7)", family="limits"),
    Plant("shot-moved", "one shot of a raw result moved, its digest left", lambda g: None, "raw-digest",
          why="the bytes of a raw result are the checker's alone (limit 7)", files=raw_moved, family="limits"),
    Plant("count-unpaid", "a stated shot count one too high", lambda g: entity(g, RAW).__setitem__("qro:shots", 9),
          "count-unpaid", why="a count is re-derived from the bytes by the checker (limit 7)", family="limits"),
    Plant("compact-id-entity", "a contextual entity with a compact IRI for an id",
          add({"@id": "qro:thing", "@type": "CreativeWork", "name": "a thing"}), "spelling",
          why="a compact IRI and the IRI it expands to are one node in RDF, so the shapes read it and conform (limit 19)",
          family="limits"),
    # edge cases the checker accepts: every must shape conforms (steps 1 to 8 hold, step 9 refuses what it did not make)
    Plant("edge-hasPart-an-action", "the root's hasPart names an action",
          also(add(JOB), mention("#a1"), part("#a1")), GENERATED, family="edges"),
    Plant("edge-hasPart-an-absolute-iri", "the root's hasPart names an IRI outside the crate",
          part("https://example.org/x"), GENERATED, family="edges"),
    Plant("edge-file-absolute-scheme", "a File with an absolute id of another scheme, and no digest",
          also(add({"@id": "foo:bar", "@type": "File"}), part("foo:bar")), GENERATED, family="edges"),
    Plant("edge-file-fragment-id", "a File with a fragment id, and no digest",
          also(add({"@id": "#a-file", "@type": "File"}), part("#a-file")), GENERATED, family="edges"),
    Plant("edge-nested-dataset", "the files reached through a Dataset the root lists",
          also(add({"@id": "data/", "@type": "Dataset", "hasPart": refs(NOTES, RAW)}),
               setv(ROOT, "hasPart", refs("data/"))), GENERATED, family="edges"),
    Plant("edge-two-actions", "two actions, both mentioned",
          also(add(JOB, {"@id": "#a2", "@type": "CreateAction"}), mention("#a1", "#a2")), GENERATED, family="edges"),
    Plant("edge-action-with-refs", "an action with an instrument, an object and a result",
          also(add({"@id": "#a1", "@type": "CreateAction", "instrument": {"@id": "#tool"}, "object": refs(NOTES),
                    "result": refs(RAW)}, {"@id": "#tool", "@type": "SoftwareApplication", "name": "a tool"}),
               mention("#a1")), GENERATED, family="edges"),
    Plant("edge-license-an-entity", "a license that is an entity of the crate",
          also(add({"@id": "#licence", "@type": "CreativeWork", "name": "a licence"}),
               setv(ROOT, "license", {"@id": "#licence"})), GENERATED, family="edges"),
    Plant("edge-absolute-id-entity", "a contextual entity with an absolute id of another scheme",
          add({"@id": "urn:example:thing", "@type": "CreativeWork", "name": "a thing"}), GENERATED, family="edges"),
    Plant("edge-text-with-a-newline", "a description of two lines and a non-ASCII letter",
          setv(ROOT, "description", "line one\nline two, with an " + chr(0xE9)), GENERATED, family="edges"),
    Plant("edge-device", "a device and its kind", add({"@id": "#device", "@type": "IndividualProduct", "name": "d",
                                                        "qro:deviceKind": "qpu"}), GENERATED, family="edges"),
    Plant("edge-file-with-format", "a File with no encodingFormat",
          drop(NOTES, "encodingFormat"), GENERATED, family="edges"),
    Plant("edge-raw-without-shots", "a raw result that does not state its shots", drop(RAW, "qro:shots"), GENERATED,
          family="edges"),
    Plant("edge-id-unusual", "a contextual entity with an id of unusual characters",
          add({"@id": "#a%20b_(c)~d", "@type": "CreativeWork", "name": "x"}), GENERATED, family="edges"),
    # ids the reader refuses (FORMAT.md item 22) and the expansion refuses to read, because rdflib resolves them otherwise:
    # the checker refuses the crate, the evaluator abstains, and a real engine reads it its own way, which `engine` records
    # (MEASURED, pyshacl 0.40.1). That is harmless, since the crate is refused first (limit 19)
    Plant("abstains-blank-node-id", "an entity whose id is a blank-node label",
          add({"@id": "_:b0", "@type": "CreativeWork", "name": "x"}), "spelling", family="abstains", unreadable=True,
          engine=("entity",), why="RDF reads it as a blank node, which the entity shape refuses (limit 19)"),
    Plant("abstains-network-path-id", "an entity whose id is a network-path reference",
          add({"@id": "//example.org/x", "@type": "CreativeWork", "name": "x"}), "spelling", family="abstains",
          unreadable=True, why="rdflib resolves it to an IRI of another host; no must shape fails in it (limit 19)"),
    Plant("abstains-dot-segment-id", "an entity whose id has a dot segment",
          add({"@id": "a/../b", "@type": "CreativeWork", "name": "x"}), "spelling", family="abstains", unreadable=True,
          why="rdflib folds the dot segment away; no must shape fails in it (limit 19)"),
    Plant("abstains-at-sign-id", "an entity whose id begins with an at sign",
          add({"@id": "@x", "@type": "CreativeWork", "name": "x"}), "spelling", family="abstains", unreadable=True,
          engine=("term-name",), why="rdflib reads it as the root, which then has two names (limit 19)"),
    Plant("abstains-blank-node-reference", "the root lists a blank-node label, which names no entity",
          part("_:b0"), "graph-form", family="abstains", unreadable=True, engine=("term-haspart",),
          why="a reference is held to item 22's forms too: one that is no absolute IRI names no entity, and a real engine "
              "reads a blank node, which `term-haspart` refuses; every must shape claims the checker's `graph-form` "
              "(limit 19)"),
    Plant("abstains-absolute-file-id", "a File whose id is an absolute file: IRI",
          also(add({"@id": "file:///elsewhere/x", "@type": "File"}), part("file:///elsewhere/x")), "spelling",
          family="abstains", unreadable=True, engine=("file-digest-present",),
          why="a real engine reads a path in the crate and asks it a digest, which the checker asks of no such File "
              "(limits 4 and 19)"),
)


def every_plant():
    """The handwritten plants and the generated ones, in a fixed order, no name twice."""
    out = list(PLANTS) + generated()
    names = [p.name for p in out]
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        raise ValueError(f"two plants share a name: {dup}")
    return out


FAMILIES = ("descriptor", "root", "actions", "files", "profiles", "vocabulary", "spelling", "domain", "cardinality",
            "limits", "edges", "abstains")


# -- the positive examples -----------------------------------------------------------------------------------------
def honest_metadata(md=None):
    """The fixture's metadata with, on an entity of each type its domain admits, every term of the table in a valid
    value: so that every term shape and every alternative of every domain shape is read once on a conforming graph.
    It is read by the strict reader and by nothing else: the checker's later steps for the parcels' terms re-derive
    values from files this graph does not have."""
    md = copy.deepcopy(md if md is not None else metadata_of(fixture.make(Path(tempfile.mkdtemp()) / "c")))
    g = md["@graph"]
    made = {}

    def host(token):
        if token not in made:
            made[token] = host_for(token, g, "#h-" + slug(token if token != "*" else "any"))
        return made[token]
    for t in V.TERMS:
        for token in t.domain:
            if token == V.DESC or t.key in ("conformsTo",):
                continue
            target = host(token)
            if t.key not in target:
                target[t.key] = valid_value(t)
    ids = sorted(e["@id"] for e in g if set(canonical.types(e)) & set(actions()))
    root(g)["mentions"] = refs(*ids)
    return arranged(md)


def matrix_rows():
    """[(family, name, fault, checker, shapes, why)] for the matrix of profile/EXAMPLES.md: the plants as declared.
    The generated ones are counted, not listed a row each: the table makes them."""
    out = []
    for p in PLANTS:
        shapes = (("the evaluator abstains; pyshacl fails " + (", ".join(p.engine) or "no must shape")) if p.unreadable
                  else ", ".join(p.shapes) or "none fail")
        out.append((p.family, p.name, p.fault, "accepted but for step 9" if p.checker == GENERATED else p.checker, shapes, p.why))
    return out
