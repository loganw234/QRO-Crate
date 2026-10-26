"""The hostile inputs planted here, each refused by the name given and none crashing the checker (P0's verifier,
P0-1, P0-2, P0-4, P0-5 and P0-7, and rounds 2 to 5). Most cases are one fault in a copy of the fixture crate, or
one line of a custody log. The rest show the right answer at a rule's edge: names of every character the path
alphabet admits, a Dataset nested two deep and a raw result of no shots, each accepted; and a directory the walk
cannot list, raised."""
import hashlib
import json
import os
import sys
import subprocess
import pathlib

import pytest

from qro import canonical, checker, custody, fixture, reader, spelling
from qro import vocabulary as V
from qro.refusal import Refused

RAW = "data/raw.counts.json"
DEEP = 100_000


@pytest.fixture(autouse=True)
def registered(monkeypatch):
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    monkeypatch.setattr(checker, "GENERATORS", {})
    fixture.register()


def crate(tmp_path):
    return fixture.make(tmp_path / "crate")


def rewrite(c, f):
    p = c / canonical.DESCRIPTOR
    md = json.loads(p.read_bytes())
    f(md)
    p.write_bytes(canonical.dumps(md))
    return c


def entity(md, i):
    return next(e for e in md["@graph"] if e["@id"] == i)


def refused(name, thunk):
    with pytest.raises(Refused) as r:
        thunk()
    assert r.value.name == name, f"{r.value.name} at {r.value.where}: {r.value.detail}"
    return r.value


# -- P0-1: one spelling, in ASCII digits only ---------------------------------------------------------------
UNICODE_TIMES = ["٢٠٢٦-١٠-١٤T00:00:00Z",       # Arabic-Indic
                 "２０２６-10-14T00:00:00Z"]                                  # fullwidth


@pytest.mark.parametrize("t", UNICODE_TIMES)
def test_a_time_in_other_digits_is_refused_in_a_crate(tmp_path, t):
    c = rewrite(crate(tmp_path), lambda md: md["@graph"][1].update({"qro:writtenAt": t}))
    refused("spelling", lambda: checker.check(c))


@pytest.mark.parametrize("t", UNICODE_TIMES)
def test_a_time_in_other_digits_is_refused_in_a_custody_line(t):
    line = canonical.compact({"at": t, "crate": "a" * 64, "event": "received", "from": "withheld",
                              "prev": custody.EMPTY})
    refused("spelling", lambda: custody.check_log(line))


def test_a_date_in_other_digits_is_refused(tmp_path):
    c = rewrite(crate(tmp_path), lambda md: md["@graph"][1].update(datePublished="٢026-10-14"))
    refused("spelling", lambda: checker.check(c))


# -- P0-2: refused by name, never a crash ---------------------------------------------------------------------
@pytest.mark.parametrize("data", [
    b'{"a": ' + b"9" * 4301 + b"}\n",                     # past the parser's integer reach
    b"[" * DEEP + b"]" * DEEP,                             # past its depth
    b'{"a": NaN}\n', b'{"a": Infinity}\n', b'{"a": 1e999}\n'],
    ids=["4301-digits", "deep", "nan", "infinity", "1e999"])
def test_hostile_metadata_is_spelling(data):
    refused("spelling", lambda: reader.read(data))


def test_a_huge_size_is_spelling(tmp_path):
    c = rewrite(crate(tmp_path), lambda md: entity(md, RAW).update(contentSize="9" * 5000))
    refused("spelling", lambda: checker.check(c))


@pytest.mark.parametrize("line", [
    b'{"at":"2026-10-14T00:00:00Z","crate":"' + b"a" * 64 + b'","event":["received"],"from":"withheld","prev":"'
    + custody.EMPTY.encode() + b'"}\n',
    b'{"at":NaN}\n', b"[" * DEEP + b"]" * DEEP + b"\n", b'{"a":' + b"9" * 4301 + b"}\n"],
    ids=["event-a-list", "nan", "deep", "4301-digits"])
def test_hostile_custody_lines_are_spelling(line):
    refused("spelling", lambda: custody.check_log(line))


def test_a_hostile_audit_record_is_spelling():
    refused("spelling", lambda: custody.check_record(b'{"logHead": NaN}\n', b""))


RAW_FORM_FAULTS = [   # each refused for the one rule it names (round 5, R5-5a: a plant missing its line feed
                      # was refused for that, and the rule it was named for went unwatched)
    (b'{"00":NaN}\n', "not JSON in ASCII"),
    (b"[" * DEEP + b"]" * DEEP, "not JSON in ASCII"),
    (b'{"00":1}', "not its one canonical line"),
    (b'{"00":1,"011":2}\n', "'011' is not a bitstring of the first one's length"),
    (b'{"0x":1}\n', "'0x' is not a bitstring of the first one's length"),
    (b'{"01x":1}\n', "'01x' is not a bitstring of the first one's length"),
    (b'{"0":-1}\n', "the count of 0 is not a non-negative integer"),
    (b'{}\n', "an object of one outcome or more"),
    (b'{"00":true}\n', "the count of 00 is not a non-negative integer"),
    (b'[]\n', "an object of one outcome or more"),
]


@pytest.mark.parametrize("raw, rule", RAW_FORM_FAULTS,
                         ids=["nan", "deep", "no-final-line-feed", "unequal-bitstrings", "a-non-bit-key",
                              "a-non-bit-tail", "a-negative-count", "no-outcome", "a-boolean-count",
                              "an-array"])
def test_a_raw_result_its_reader_cannot_read_is_raw_form(tmp_path, raw, rule):
    c = crate(tmp_path)
    (c / RAW).write_bytes(raw)
    rewrite(c, lambda md: entity(md, RAW).update(sha256=hashlib.sha256(raw).hexdigest(), contentSize=str(len(raw))))
    r = refused("raw-form", lambda: checker.check(c))
    assert rule in r.detail, r.detail


@pytest.mark.parametrize("raised", [ZeroDivisionError("a parcel's bug"), RecursionError("too deep"), KeyError("x"),
                                    PermissionError(13, "denied")],
                         ids=["ZeroDivisionError", "RecursionError", "KeyError", "PermissionError"])
def test_a_reader_that_crashes_is_raw_form_and_a_generator_that_crashes_is_metadata_generated(tmp_path, raised):
    """Any Exception but a MemoryError, from a parcel's raw-form reader or its generator, is the crate refused by the
    step's name (FORMAT.md item 16): a net widened to let a RecursionError out as the host's passed every test
    (P0.7's first verifier, a note)."""
    c = crate(tmp_path)

    def boom(_):
        raise raised
    checker.RAW_FORMS[fixture.RAW_FORM] = boom
    refused("raw-form", lambda: checker.check(c))
    fixture.register()
    checker.GENERATORS[fixture.GENERATOR] = boom
    refused("metadata-generated", lambda: checker.check(c))


def test_a_memory_error_in_a_reader_or_a_generator_is_the_hosts_and_no_verdict(tmp_path):
    """P1.1's third verifier, D1, MEASURED: step 3 turned any exception from a parcel's raw-form reader, a
    MemoryError among them, into `REFUSED raw-form`, so a host short of memory gave a verdict on the crate. A
    MemoryError from a reader or a generator now reaches the command line, which answers it as the checker failing,
    exit 3 (P0.7; FORMAT.md item 16)."""
    c = crate(tmp_path)

    def short(_):
        raise MemoryError
    checker.RAW_FORMS[fixture.RAW_FORM] = short
    with pytest.raises(MemoryError):
        checker.check(c)
    fixture.register()
    checker.GENERATORS[fixture.GENERATOR] = short
    with pytest.raises(MemoryError):
        checker.check(c)


# -- P0-4 and P0-5: a file is the same file on every host -----------------------------------------------------
def listed(md, name, b=b""):
    """`md` with a File `name` listed from the root, holding `b`, the graph and hasPart left in their order: so the
    plant's one fault is its name. P0's verifier, round 2 (R2-1): a plant that left the graph unsorted was refused
    for its order, and the path rule it meant to watch could be deleted unnoticed."""
    md["@graph"].append({"@id": name, "@type": "File", "contentSize": str(len(b)), "encodingFormat": "text/plain",
                         "sha256": hashlib.sha256(b).hexdigest()})
    md["@graph"][1]["hasPart"].append({"@id": name})
    md["@graph"][2:] = sorted(md["@graph"][2:], key=lambda x: x["@id"])
    md["@graph"][1]["hasPart"].sort(key=canonical.sort_key)


SUB_DELIMITERS = "!$&'()+,;=@~-_."                       # RFC 3986's, but "*", which Windows refuses in a name
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" + SUB_DELIMITERS + "z"   # no end dot
DEVICES = ["CON", "con", "Con.txt", "PRN", "prn.json", "AUX", "aux.tar.gz", "NUL", "nul", "COM0", "com1", "COM9.txt",
           "LPT0", "lpt1", "LPT9.x", "CONIN$", "conout$", "CONOUT$.txt", "aux.1", "NUL.7z", "con.123", "com1._x",
           "Lpt5.-", "prn.~"]
PATHS_ACCEPTED = (["x", "data/x.txt", "data/.hidden", "data/con-notes.txt", "data/console.txt", "data/com10",
                   "data/lpt", "data/" + "a" * 255, "a/b/c/d.e", "data/" + ALPHABET, ALPHABET + "/x"]
                  + [f"data/a{ch}b.txt" for ch in SUB_DELIMITERS])
PATHS_REFUSED = (["", "/x", "data/", "data//x.txt", ".", "..", "data/.", "data/..", "data/./x", "data/../x",
                  "data/x.", "data/x..", "data/" + "a" * 256, "data/café.txt", "data/notes.txt:hidden", "C:/x.txt"]
                 + [f"data/a{ch}b.txt" for ch in "%:#*?\\ \"<>|`^{}[]\t"]
                 + [f"data/{d}" for d in DEVICES]
                 # round 3, row 9: each rule holds in every segment, not the last alone
                 + [f"data/{d}/x.txt" for d in ("aux", "CON.txt", "lpt1")] + ["con/y.txt", "data/x./y.txt",
                                                                              "a./b", "data/" + "a" * 256 + "/y.txt"]
                 + ["a" * 256, "a" * 256 + "/x"])                       # the length rule in the first segment too


@pytest.mark.parametrize("name", PATHS_ACCEPTED)
def test_the_path_spelling_accepts(name):
    assert spelling.path_problem(name) is None


@pytest.mark.parametrize("name", PATHS_REFUSED, ids=[repr(n)[:40] for n in PATHS_REFUSED])
def test_the_path_spelling_refuses(name):
    assert spelling.path_problem(name) is not None


PATHS_REFUSED_AS_PATHS = [n for n in PATHS_REFUSED if spelling.id_problem(n) is None]   # not first as an @id
PATHS_REFUSED_AS_IDS = [n for n in PATHS_REFUSED if spelling.id_problem(n) is not None]   # first as an @id


@pytest.mark.parametrize("name", PATHS_REFUSED_AS_IDS, ids=[repr(n)[:40] for n in PATHS_REFUSED_AS_IDS])
def test_a_listed_files_id_outside_the_id_spelling_is_refused_by_the_id_rule(tmp_path, name):
    """P0.5: a refused path the id rule refuses first, an empty or dot segment, or a character no path holds, which
    leaves it in none of the four forms, is refused at its @id, so every refused path is refused at the crate by one rule or the other. The id rule names
    the entity by its place in the graph, the path rule by its path, so the location tells which rule refused
    (P0.5's verifier, round 1: with Files let past the id rule, these tests still passed on the path rule)."""
    c = rewrite(crate(tmp_path), lambda md: listed(md, name))
    r = refused("spelling", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where.startswith("@graph[") and r.where.endswith(" @id"), r


ID_PATH_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._~!$&'()+,;=@-/")


def outside_the_ids_path_form(name):
    """FORMAT.md item 22's path form, stated here and not read from the code: a character it does not hold, @ first,
    an empty, . or .. segment, or a last segment that ends at its first ; or begins .; or ..;."""
    body = name[:-1] if name.endswith("/") else name
    head, semi, params = name.split("/")[-1].partition(";")
    return (not set(name) <= ID_PATH_CHARS or name.startswith("@")
            or any(s in ("", ".", "..") for s in body.split("/")) or bool(semi and (params == "" or head in (".", ".."))))


def test_every_refused_path_is_refused_by_one_rule_or_the_other():
    """The id rule refuses first exactly the paths item 22's path form leaves out, and the path rule the rest (P0.5's
    verifier, round 2, note 3: the split was read from the code it held, so its sum was a tautology)."""
    assert PATHS_REFUSED_AS_IDS == [n for n in PATHS_REFUSED if outside_the_ids_path_form(n)]
    assert PATHS_REFUSED_AS_IDS and PATHS_REFUSED_AS_PATHS


@pytest.mark.parametrize("name", PATHS_REFUSED_AS_PATHS, ids=[repr(n)[:40] for n in PATHS_REFUSED_AS_PATHS])
def test_a_listed_files_id_outside_the_path_spelling_is_refused_by_the_path_rule(tmp_path, name):
    """The graph in its order, so the path rule alone stands between the name and acceptance."""
    c = rewrite(crate(tmp_path), lambda md: listed(md, name))
    r = refused("spelling", lambda: checker.check(c))
    assert r.where == f"{name} @id" and "path" in r.detail, r.detail


def test_a_name_of_every_character_the_alphabet_admits_is_held_end_to_end(tmp_path):
    """Each character the path spelling admits, in a real file a crate holds, read through every step: one file a
    sub-delimiter, and one of the whole alphabet (round 3, row 11: a letter or digit dropped went unseen)."""
    c = crate(tmp_path)
    names = [f"a{ch}b.txt" for ch in SUB_DELIMITERS] + [ALPHABET]
    for n in names:
        (c / "data" / n).write_bytes(n.encode("ascii"))
    (c / canonical.DESCRIPTOR).write_bytes(canonical.write(fixture.generate(c)))
    md = checker.check(c)
    assert {f"data/{n}" for n in names} <= {e["@id"] for e in md["@graph"]}


@pytest.mark.parametrize("ref, absolute", [("https://w3id.org/ro/crate/1.3", True), ("urn:uuid:x", True),
                                           ("qro:RawResult", True), ("a+b-c:x", True), ("C:/x.txt", False),
                                           ("c:x", False), ("notes.txt:hidden", False), ("data/a:b", False),
                                           ("x", False), ("#frag", False), ("./", False)])
def test_an_absolute_iri_has_a_scheme_of_two_characters_or_more_and_no_dot(ref, absolute):
    """So neither a drive letter nor a file's stream reads as an IRI, and escapes the path rule."""
    assert reader.absolute(ref) is absolute


def test_two_files_whose_names_differ_by_case_are_refused(tmp_path):
    def add(md):
        e = dict(entity(md, RAW), **{"@id": "data/RAW.counts.json"})
        md["@graph"].append(e)
        md["@graph"][1]["hasPart"].append({"@id": "data/RAW.counts.json"})
        md["@graph"][2:] = sorted(md["@graph"][2:], key=lambda x: x["@id"])
        md["@graph"][1]["hasPart"].sort(key=lambda x: x["@id"])
    c = rewrite(crate(tmp_path), add)
    r = refused("graph-form", lambda: checker.check(c))
    assert "only by case" in r.detail


def test_a_file_named_as_the_descriptor_in_another_case_is_refused(tmp_path):
    """P0's verifier, round 2, note 2: the descriptor is a file too, though not a File entity."""
    c = rewrite(crate(tmp_path), lambda md: listed(md, "Ro-Crate-Metadata.json"))
    r = refused("graph-form", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == "Ro-Crate-Metadata.json" and "only by case" in r.detail


def test_a_listed_name_held_to_its_exact_name_on_disk(tmp_path):
    """On a host that folds case, the file opens under another case; the checker still wants the exact name."""
    c = crate(tmp_path)
    (c / "data" / "notes.txt").rename(c / "data" / "Notes.txt")
    refused("file-missing", lambda: checker.check(c))


def link_dir(path, target):
    """A directory link: a junction on Windows, which needs no privilege; a symbolic link elsewhere. No skip: the
    runner fails a stage that skips a test (P0's verifier, round 2, R2-4)."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(path))
    else:
        os.symlink(target, path, target_is_directory=True)


def test_a_directory_link_whose_files_are_listed_with_their_digests_is_still_refused(tmp_path):
    c = crate(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_bytes(b"outside\n")
    link_dir(c / "data" / "jct", outside)
    rewrite(c, lambda md: listed(md, "data/jct/secret.txt", b"outside\n"))
    refused("file-link", lambda: checker.check(c))


def test_a_file_link_is_refused_by_what_the_walk_asks_of_the_entry(tmp_path, monkeypatch):
    """A symbolic link to a file needs a privilege on Windows, so the walk's question is planted: an entry the host
    reports as a link is refused, whatever kind of link it is."""
    c = crate(tmp_path)
    monkeypatch.setattr(checker, "_is_link", lambda p: p.name == "notes.txt")
    r = refused("file-link", lambda: checker.check(c))
    assert r.where == "data/notes.txt"


def test_the_walk_asks_the_host_about_symbolic_links_and_junctions(tmp_path, monkeypatch):
    p = tmp_path / "x"
    p.write_bytes(b"x")
    assert checker._is_link(p) is False
    monkeypatch.setattr(type(p), "is_symlink", lambda self: True)
    assert checker._is_link(p) is True


def test_an_entry_neither_a_regular_file_nor_a_directory_is_refused(tmp_path, monkeypatch):
    """A named pipe or a socket, which a reader would block on. Neither can be made on Windows, so the walk's
    question is planted (P0's verifier, round 2: the check, and its name, were watched by nothing)."""
    c = crate(tmp_path)
    real = type(c).is_file
    monkeypatch.setattr(type(c), "is_file", lambda self: False if self.name == "notes.txt" else real(self))
    r = refused("file-link", lambda: checker.check(c))
    assert (r.where, r.detail) == ("data/notes.txt", "neither a regular file nor a directory")


# -- P0-7: a CHECKED term stands only where its step reads it -------------------------------------------------
@pytest.mark.parametrize("at, key, value", [
    ("./", "sha256", "a" * 64), ("./", "contentSize", "1"), ("./", "qro:rawForm", "x"),
    ("data/notes.txt", "qro:rawForm", "x"), ("data/notes.txt", "qro:generator", "x"),
    ("data/notes.txt", "datePublished", "2026-10-14"), ("data/notes.txt", "mentions", [{"@id": "./"}]),
    ("data/notes.txt", "about", {"@id": "./"})])
def test_a_term_off_its_domain_is_graph_form(tmp_path, at, key, value):
    c = rewrite(crate(tmp_path), lambda md: entity(md, at).update({key: value}))
    refused("graph-form", lambda: checker.check(c))


def test_a_remote_file_carrying_a_digest_is_graph_form(tmp_path):
    def add(md):
        md["@graph"].append({"@id": "https://example.org/x.json", "@type": "File", "sha256": "a" * 64})
    c = rewrite(crate(tmp_path), add)
    refused("graph-form", lambda: checker.check(c))


@pytest.mark.parametrize("key", ["datePublished", "qro:signature", "qro:trustedTime", "qro:writer", "qro:writtenAt",
                                 "license", "name", "description", "qro:generator", "hasPart"])
def test_a_root_without_a_required_term_is_graph_form(tmp_path, key):
    c = rewrite(crate(tmp_path), lambda md: md["@graph"][1].pop(key))
    refused("graph-form", lambda: checker.check(c))


@pytest.mark.parametrize("ident, key, value", [
    ("local-file", "sha256", "a" * 64), ("local-file", "contentSize", "1"),
    ("Dataset", "hasPart", [{"@id": "data/notes.txt"}]), ("File", "encodingFormat", "text/plain")])
def test_an_entity_whose_id_spells_a_domain_is_not_of_it(tmp_path, ident, key, value):
    """P0's verifier, round 2 (R2-3): every domain token was matched against the @id too, so an entity named
    `qro:RawResult` could state a count no step reads. Only the root's and the descriptor's tokens are @ids."""
    def add(md):
        md["@graph"].append({"@id": ident, "@type": "CreativeWork", key: value})
        md["@graph"][2:] = sorted(md["@graph"][2:], key=lambda x: x["@id"])
    c = rewrite(crate(tmp_path), add)
    r = refused("graph-form", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == f"{ident} {key}"


@pytest.mark.parametrize("key, value", [("qro:shots", 9), ("qro:rawForm", "x")])
def test_an_entity_whose_id_spells_a_qro_type_is_a_compact_iri_and_refused(tmp_path, key, value):
    """R2-3's own plant, `qro:RawResult` as an @id: since P0.5 a compact IRI, the vocabulary's own IRI to a JSON-LD
    reader, so it is refused by the id rule before its terms are read."""
    def add(md):
        md["@graph"].append({"@id": "qro:RawResult", "@type": "CreativeWork", key: value})
        md["@graph"][2:] = sorted(md["@graph"][2:], key=lambda x: x["@id"])
    c = rewrite(crate(tmp_path), add)
    r = refused("spelling", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where.endswith(" @id") and "compact IRI" in r.detail, r


def test_a_root_of_another_type_is_graph_form(tmp_path):
    """P0's verifier, round 2: with the root's type unchecked, a root typed Person was refused `term-unknown`, and
    nothing noticed the name change."""
    c = rewrite(crate(tmp_path), lambda md: md["@graph"][1].update({"@type": "Person"}))
    r = refused("graph-form", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == "./"


@pytest.mark.parametrize("at, name", [("data/notes.txt", "file-digest"), (RAW, "raw-digest")])
def test_a_size_off_by_one_beside_a_right_digest_is_refused(tmp_path, at, name):
    """P0's verifier, round 2: no plant made the size wrong and left the digest right."""
    def bump(md):
        e = entity(md, at)
        e["contentSize"] = str(int(e["contentSize"]) + 1)
    c = rewrite(crate(tmp_path), bump)
    r = refused(name, lambda: checker.check(c))
    assert r.where == at


# -- R3-2: a fault aimed at each check round 3 left unwatched --------------------------------------------------
def own_generator(monkeypatch):
    """A generator that returns the crate's own metadata, so a crate shaped as no fixture writes it reaches every
    step: the step under test decides, and step 9 agrees with whatever the crate says."""
    monkeypatch.setitem(checker.GENERATORS, fixture.GENERATOR,
                        lambda c: json.loads((c / canonical.DESCRIPTOR).read_bytes()))


@pytest.mark.parametrize("count, name", [(-1, "raw-form"), (True, "raw-form"), (2.0, "raw-form"), ("8", "raw-form")],
                         ids=["minus one", "True", "a float", "a string"])
def test_a_raw_form_reader_that_counts_no_whole_number_is_refused(tmp_path, monkeypatch, count, name):
    c = crate(tmp_path)
    monkeypatch.setitem(checker.RAW_FORMS, fixture.RAW_FORM, lambda b: count)
    r = refused(name, lambda: checker.check(c))
    assert r.where == RAW and "whole number" in r.detail


def test_a_raw_result_of_no_shots_is_counted_and_accepted(tmp_path):
    """Zero is a whole number of shots: the boundary below the refusal above."""
    c = fixture.make(tmp_path / "crate", counts={"0": 0})
    md = checker.check(c)
    assert entity(md, RAW)["qro:shots"] == 0


@pytest.mark.parametrize("graph", [7, None, True, 1.5, "x", {}, []], ids=lambda g: repr(g))
def test_a_graph_that_is_not_a_list_of_entities_is_graph_form(tmp_path, graph):
    """Round 3, row 7: with the guard's `or` made `and`, these crashed the reader."""
    c = rewrite(crate(tmp_path), lambda md: md.update({"@graph": graph}))
    r = refused("graph-form", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == "@graph"


def test_a_raw_result_at_a_path_outside_the_spelling_is_refused(tmp_path):
    """Round 3, row 8: the path rule reaches a File of two types, a raw result among them."""
    def add(md):
        listed(md, "data/con.counts.json")      # an @id, but no path: a device's name (since P0.5, % is in no path)
        e = entity(md, "data/con.counts.json")
        e["@type"] = ["File", "qro:RawResult"]
        e["qro:rawForm"] = fixture.RAW_FORM
    c = rewrite(crate(tmp_path), add)
    r = refused("spelling", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == "data/con.counts.json @id"


def two(md, first, second):
    """`md` with two CreativeWorks of one name each, `first` and `second`, in the graph's order."""
    for i in (first, second):
        md["@graph"].append({"@id": i, "@type": "CreativeWork", "name": "x"})
    md["@graph"][2:] = sorted(md["@graph"][2:], key=lambda x: x["@id"])


@pytest.mark.parametrize("first, second", [("#a", "./#a"), ("http://schema.org/a", "schema:a"), ("#b", "_:b0"),
                                           ("#c", "@x")])
def test_two_entities_a_json_ld_reader_would_make_one_are_refused(tmp_path, first, second):
    """P4's verifier, round 1, defect 1, MEASURED with pyshacl: each pair was accepted by the checker at every step,
    while RDF reads the second as the first (or as the root, or a blank node), so a must shape failed on a crate
    the checker accepted. The second's @id is refused, by the id rule (P0.5)."""
    c = rewrite(crate(tmp_path), lambda md: two(md, first, second))
    r = refused("spelling", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where.startswith("@graph[") and r.where.endswith(" @id"), r


def test_a_file_whose_id_begins_with_at_is_refused(tmp_path):
    """P4's verifier, round 1: a top-level File `@x` is the root's IRI to rdflib. FORMAT.md item 11 lets a path hold
    `@`; item 22 refuses one that begins with it."""
    c = rewrite(crate(tmp_path), lambda md: listed(md, "@x"))
    r = refused("spelling", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where.startswith("@graph[") and r.where.endswith(" @id"), r


def test_a_reference_to_a_compact_iri_is_refused(tmp_path):
    """A reference names an IRI as an @id does: `{"@id": "schema:a"}` is http://schema.org/a to a JSON-LD reader, and
    is refused `spelling` where the values are read (P0.5)."""
    c = rewrite(crate(tmp_path), lambda md: md["@graph"][1].update(license={"@id": "cc:by"}))
    r = refused("spelling", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == "./ license", r


@pytest.mark.parametrize("ident", ["#a://b", "#:://", "x;", ";", ".;", "a/..;", ".;x"])
def test_an_entity_a_json_ld_reader_reads_as_another_iri_is_refused(tmp_path, ident):
    """P0.5's verifier, round 1, its crates B and C: the fixture with a CreativeWork `#a://b`, a relative IRI to rdflib
    at every base, or `;`, the root to rdflib at an https base, was accepted at every step. Each is refused at its
    @id, by the id rule."""
    def add(md):
        md["@graph"].append({"@id": ident, "@type": "CreativeWork", "name": "x"})
        md["@graph"][2:] = sorted(md["@graph"][2:], key=lambda x: x["@id"])
    c = rewrite(crate(tmp_path), add)
    r = refused("spelling", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where.startswith("@graph[") and r.where.endswith(" @id"), r


def test_a_file_beside_its_own_name_ending_in_a_semicolon_is_refused(tmp_path):
    """P0.5's verifier, round 1, its crate A: Files data/x.txt and data/x.txt; were accepted at all nine steps, while
    at an https base RDF reads them as one node with two digests. The second is refused by the id rule. A ; that
    urllib keeps, in data/a;b.txt, is a name like any other, held end to end above."""
    def add(md):
        listed(md, "data/x.txt", b"one")
        listed(md, "data/x.txt;", b"two")
    c = rewrite(crate(tmp_path), add)
    (c / "data" / "x.txt").write_bytes(b"one")
    r = refused("spelling", lambda: checker.check(c))
    assert r.where.startswith("@graph[") and r.where.endswith(" @id") and "first ;" in r.detail, r


@pytest.mark.parametrize("ref, name", [("_:b0", "graph-form"), ("./x", "graph-form"), ("x#a", "graph-form"),
                                       ("#a://b", "graph-form"), ("x;", "graph-form"), ("schema:a", "spelling"),
                                       ("file:a", "spelling"), ("HTTPS://example.org/a", "spelling")])
def test_a_reference_outside_the_id_rule_is_refused_by_the_name_item_22_gives(tmp_path, ref, name):
    """FORMAT.md item 22 (P0.5's verifier, round 1, prose): a reference whose @id is no absolute IRI names no entity
    of the graph, since no entity's @id can be outside the rule, and is `graph-form`; one that reads as an absolute
    IRI is refused `spelling` where the values are read."""
    c = rewrite(crate(tmp_path), lambda md: md["@graph"][1].update(license={"@id": ref}))
    r = refused(name, lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == "./ license", r


def test_a_file_whose_id_is_a_fragment_is_not_a_file_the_crate_holds(tmp_path):
    """A `#` id names a contextual entity: no path rule applies, and no digest may stand on it."""
    def add(md, digest):
        e = {"@id": "#notes", "@type": "File"}
        if digest:
            e["sha256"] = "a" * 64
        md["@graph"].insert(2, e)
    plain = rewrite(crate(tmp_path / "a"), lambda md: add(md, False))
    assert reader.read((plain / canonical.DESCRIPTOR).read_bytes())["@graph"][2]["@id"] == "#notes"
    held = rewrite(crate(tmp_path / "b"), lambda md: add(md, True))
    refused("graph-form", lambda: reader.read((held / canonical.DESCRIPTOR).read_bytes()))


def test_a_dataset_nested_in_the_root_reaches_its_files(tmp_path, monkeypatch):
    """Round 3, row 12: RO-Crate profiles nest a directory's Dataset under the root; step 2 walks hasPart through
    it."""
    own_generator(monkeypatch)

    def nest(md):
        md["@graph"][1]["hasPart"] = [{"@id": "data/"}]
        md["@graph"].append({"@id": "data/", "@type": "Dataset", "hasPart": [{"@id": "data/notes.txt"},
                                                                             {"@id": RAW}]})
        md["@graph"][2:] = sorted(md["@graph"][2:], key=lambda x: x["@id"])
    c = rewrite(crate(tmp_path), nest)
    assert canonical.body_digest(checker.check(c))
    rewrite(c, lambda md: entity(md, "data/").update({"hasPart": [{"@id": RAW}]}))
    r = refused("file-unlisted", lambda: checker.check(c))
    assert r.where == "data/notes.txt"


def test_a_web_based_part_with_no_entity_is_passed_over_not_crashed_on(tmp_path, monkeypatch):
    """Round 3, row 13: the walk meets a part the graph does not describe."""
    own_generator(monkeypatch)
    c = rewrite(crate(tmp_path), lambda md: md["@graph"][1]["hasPart"].append(
        {"@id": "https://example.org/remote.json"}))
    assert canonical.body_digest(checker.check(c))


def test_a_crate_of_the_descriptor_the_root_and_the_profiles_alone_is_accepted(tmp_path, monkeypatch):
    """Round 3, row 14: the smallest graph the reader takes. It was the descriptor and the root; since P0.3 it
    holds each profile's contextual entity too (P4's design, R3), so four entities."""
    own_generator(monkeypatch)

    def bare(md):
        md["@graph"] = md["@graph"][:2] + V.profile_entities()
        md["@graph"][1]["hasPart"] = [{"@id": "https://example.org/remote.json"}]
    c = rewrite(crate(tmp_path), bare)
    for f in (c / "data").iterdir():
        f.unlink()
    (c / "data").rmdir()
    assert len(checker.check(c)["@graph"]) == 4


@pytest.mark.parametrize("c", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
def test_a_scheme_may_begin_with_every_letter(c):
    """Round 3, note 1: the scheme's first character, every member of its class."""
    assert reader.absolute(f"{c}b:x") and reader.absolute(f"{c}0123456789+-azAZ:x")


def test_a_dataset_two_levels_down_reaches_its_files(tmp_path, monkeypatch):
    """Round 4: a walk that followed only the root's own parts passed the one-level plant."""
    own_generator(monkeypatch)

    def nest(md):
        md["@graph"][1]["hasPart"] = [{"@id": "data/"}]
        md["@graph"] += [{"@id": "data/", "@type": "Dataset", "hasPart": [{"@id": "data/run1/"}]},
                         {"@id": "data/run1/", "@type": "Dataset", "hasPart": [{"@id": "data/notes.txt"},
                                                                              {"@id": RAW}]}]
        md["@graph"][2:] = sorted(md["@graph"][2:], key=lambda x: x["@id"])
    c = rewrite(crate(tmp_path), nest)
    assert canonical.body_digest(checker.check(c))
    rewrite(c, lambda md: entity(md, "data/run1/").update({"hasPart": [{"@id": RAW}]}))
    r = refused("file-unlisted", lambda: checker.check(c))
    assert r.where == "data/notes.txt"


def test_a_type_listed_twice_is_refused(tmp_path):
    """Round 5: one spelling of a list of types, sorted and each once, was held by no plant."""
    c = rewrite(crate(tmp_path), lambda md: entity(md, RAW).update({"@type": ["File", "File", "qro:RawResult"]}))
    r = refused("spelling", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == f"{RAW} @type"


def test_a_reference_that_only_looks_like_an_iri_names_no_entity(tmp_path):
    """Round 5: an @id outside the iri spelling is relative, so it must name an entity in the graph."""
    for ref in ("http:", "https:", "ab:"):
        c = rewrite(crate(tmp_path / ref.rstrip(":")), lambda md: md["@graph"][1]["hasPart"].append({"@id": ref}))
        r = refused("graph-form", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
        assert "names no entity" in r.detail, r.detail


def test_the_walk_reports_the_first_stray_file_in_name_order_under_any_hash_seed(tmp_path):
    """Round 5: the walk's sorting was held by nothing, so its refusal could name another file each run."""
    c = crate(tmp_path)
    for n in "edcba":
        (c / "data" / f"stray-{n}.txt").write_bytes(n.encode("ascii"))
    code = ("import sys; sys.path.insert(0, sys.argv[1]); from qro import checker, fixture; "
            "from qro.refusal import Refused; fixture.register()" + chr(10) +
            "try:" + chr(10) + "    checker.check(sys.argv[2])" + chr(10) +
            "except Refused as r:" + chr(10) + "    print(r.name, r.where)")
    root = str(pathlib.Path(__file__).resolve().parents[2])
    for seed in ("0", "1", "7", "42", "4242"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        p = subprocess.run([sys.executable, "-c", code, root, str(c)], capture_output=True, env=env)
        assert p.stdout.split() == [b"file-unlisted", b"data/stray-a.txt"], (seed, p.stdout, p.stderr[-300:])


def test_the_strict_reader_loads_only_the_pinned_copy_of_ro_crates_context(monkeypatch):
    """Round 5: qro/data/README.md says the reader refuses any other bytes; nothing held it. Since P0.7 the
    vocabulary loads the copy, for the reader's terms and the id rule's alike."""
    caches = (reader.rocrate_terms, V.rocrate_context, V.context_terms)
    for f in caches:
        f.cache_clear()
    monkeypatch.setattr(V, "ROCRATE_CONTEXT_SHA256", "0" * 64)
    try:
        for f in (reader.rocrate_terms, V.context_terms):
            with pytest.raises(RuntimeError, match="not the copy the vocabulary pins"):
                f()
    finally:
        for f in caches:
            f.cache_clear()


def test_a_directory_the_walk_cannot_list_is_raised_not_passed_over(tmp_path, monkeypatch):
    """Round 5, note 1: a directory the user could not list was walked past, and the crate accepted."""
    c = crate(tmp_path)
    (c / "hidden").mkdir()
    real = os.scandir

    def scandir(path="."):
        if os.path.basename(os.fspath(path)) == "hidden":
            raise PermissionError(13, "permission denied", os.fspath(path))
        return real(path)
    monkeypatch.setattr(os, "scandir", scandir)
    with pytest.raises(PermissionError):
        checker.check(c)


# -- P0.1: round 6's notes ------------------------------------------------------------------------------------
@pytest.mark.parametrize("names, detail, where", [
    (["data/A/x.txt", "data/a/y.txt"], "a path, data/a, whose name differs from data/A's only by case",
     "data/a/y.txt"),
    (["data/A", "data/a/b.txt"], "a path, data/a, whose name differs from data/A's only by case", "data/a/b.txt"),
    (["data/a", "data/a/b.txt"], "data/a is both a file and a directory", "data/a/b.txt"),
    (["Data/x.txt"], "a path, data, whose name differs from Data's only by case", "data/notes.txt"),
], ids=["two directories by case", "a file and a directory by case", "a file and a directory", "data/ by case"])
def test_paths_along_files_that_differ_only_by_case_are_refused(tmp_path, names, detail, where):
    """Round 6, 8.3 item 1: on a host that folds case, each pair is one path. Refused at the later entity in the
    graph's order (P0.1's verifier, round 1, 4.2: no test read the location)."""
    def add(md):
        for n in names:
            listed(md, n)
    c = rewrite(crate(tmp_path), add)
    r = refused("graph-form", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert (r.detail, r.where) == (detail, where)


def test_one_name_at_two_depths_is_two_paths(tmp_path):
    """A file named y.txt below x, and a directory named y.txt at the top, are two paths and accepted; so are a file
    and a directory whose names differ by case at two depths. A tree of the paths that never went down a level would
    refuse each (P0.7's mutants)."""
    c = rewrite(crate(tmp_path), lambda md: [listed(md, n) for n in ("x/y.txt", "y.txt/z.txt", "a/B", "b/c.txt")])
    reader.read((c / canonical.DESCRIPTOR).read_bytes())


def test_a_path_of_many_segments_costs_what_its_characters_do(tmp_path):
    """P0.5's fourth verifier, note 1, MEASURED: the reader built every prefix of a File's path as a string, so a
    path of 50,000 segments, 100 KB, took 149 s, its memory the square of its length. A tree of the paths' segments
    holds them now (P0.7). MEASURED by the lead: 10,000 segments peaked at 192 MB that way, and at 2.8 MB now."""
    import tracemalloc
    name = "/".join(["a"] * 10_000) + "/x.txt"
    data = (rewrite(crate(tmp_path), lambda md: listed(md, name)) / canonical.DESCRIPTOR).read_bytes()
    tracemalloc.start()
    try:
        reader.read(data)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < 32 * 2**20, peak


def test_the_root_before_the_descriptor_is_refused_at_the_graph(tmp_path):
    """P0.1's verifier, round 4, N7: the order's own refusal was unasserted, since later checks refuse the same graph
    elsewhere."""
    c = rewrite(crate(tmp_path), lambda md: md["@graph"].__setitem__(slice(0, 2), md["@graph"][1::-1]))
    r = refused("graph-form", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert (r.where, r.detail) == ("@graph", "the descriptor first, then the root")


def test_a_root_that_is_also_an_action_is_refused(tmp_path):
    """Round 6, 8.3 item 2."""
    c = rewrite(crate(tmp_path), lambda md: md["@graph"][1].update(
        {"@type": ["CreateAction", "Dataset"], "mentions": [{"@id": "./"}]}))
    r = refused("graph-form", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == "./" and "never an action" in r.detail


def test_a_metadata_file_that_is_a_link_is_file_link(tmp_path, monkeypatch):
    """Round 6, 8.3 item 5: it was refused file-missing, which said less. Its bytes are not metadata, so only the
    check made before any read can say file-link: a link is never followed to read what it points at."""
    c = crate(tmp_path)
    (c / canonical.DESCRIPTOR).write_bytes(b"not metadata")
    real = checker._is_link
    monkeypatch.setattr(checker, "_is_link", lambda p: p.name == canonical.DESCRIPTOR or real(p))
    r = refused("file-link", lambda: checker.check(c))
    assert r.where == canonical.DESCRIPTOR


def test_a_metadata_file_named_in_another_case_is_file_missing_on_every_host(tmp_path):
    """Round 6, 8.3 item 7: Windows said file-unlisted, Linux file-missing."""
    c = crate(tmp_path)
    (c / canonical.DESCRIPTOR).rename(c / "tmp.json")
    (c / "tmp.json").rename(c / canonical.DESCRIPTOR.upper())
    refused("file-missing", lambda: checker.check(c))


class _Reversed:
    """os.scandir's entries in reverse: a host whose listing order is not name order, on any host."""
    def __init__(self, it):
        self.entries = iter(list(it)[::-1])
        it.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.entries)

    def close(self):
        pass


def test_the_walk_descends_in_name_order(tmp_path, monkeypatch):
    """Round 6, 8.3 item 3: the walk sorted a copy of its directories, and descended in the host's order.
    NTFS lists names in order already, so the host's listing is reversed here."""
    real = os.scandir
    monkeypatch.setattr(os, "scandir", lambda path=".": _Reversed(real(path)))
    c = crate(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    for d in ("h", "a", "m"):
        (c / d).mkdir()
        link_dir(c / d / "link", outside)
    r = refused("file-link", lambda: checker.check(c))
    assert r.where == "a/link"


def test_a_registered_step_that_accepts_lets_the_crate_through(tmp_path, monkeypatch):
    """Round 6, 8.1 item 6: the seam's success path, the first thing a parcel uses."""
    own_generator(monkeypatch)
    ran = []
    monkeypatch.setitem(checker.STEPS, 4, lambda c, md: ran.append(4))
    c = rewrite(crate(tmp_path), lambda md: fixture.with_entity(md, {"@id": "#pub", "@type": "qro:Pub", "qro:commitment": "a" * 64}))
    assert canonical.body_digest(checker.check(c)) and ran == [4]
    monkeypatch.setitem(checker.STEPS, 4, None)
    refused("step-unbuilt", lambda: checker.check(c))


@pytest.mark.parametrize("error", [KeyError("k"), ValueError("v"), TypeError("t"), IndexError("i"), OSError("o")],
                         ids=["KeyError", "ValueError", "TypeError", "IndexError", "OSError"])
def test_a_parcels_reader_or_generator_raising_any_error_is_refused_by_its_steps_name(tmp_path, monkeypatch, error):
    """Round 6, 8.1 item 7: both plants raised ZeroDivisionError alone."""
    def boom(*_):
        raise error
    c = crate(tmp_path)
    monkeypatch.setitem(checker.RAW_FORMS, fixture.RAW_FORM, boom)
    refused("raw-form", lambda: checker.check(c))
    fixture.register()
    monkeypatch.setitem(checker.GENERATORS, fixture.GENERATOR, boom)
    refused("metadata-generated", lambda: checker.check(c))


def test_a_top_level_array_of_the_two_keys_is_graph_form(tmp_path):
    """Round 6, 8.1 item 8: type confusion, refused by name and never a crash."""
    c = crate(tmp_path)
    (c / canonical.DESCRIPTOR).write_bytes(canonical.dumps(["@context", "@graph"]))
    r = refused("graph-form", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == "the top level"


TYPE_CONFUSION = [
    ("an empty reference", lambda md: md["@graph"][1]["hasPart"].append({})),
    ("a reference to a number", lambda md: md["@graph"][1]["hasPart"].append({"@id": 5})),
    ("a list for a reference", lambda md: md["@graph"][1]["hasPart"].append(["@id"])),
    ("a type list with a number", lambda md: entity(md, RAW).update({"@type": ["File", 5]})),
    ("a reference for a name", lambda md: md["@graph"][1].update(name={"@id": "x"})),
    ("a string for a list", lambda md: md["@graph"][1].update({"qro:implementation": "x"})),
]


@pytest.mark.parametrize("plant", [p for _, p in TYPE_CONFUSION], ids=[n for n, _ in TYPE_CONFUSION])
def test_a_value_of_the_wrong_kind_is_spelling_and_never_a_crash(tmp_path, plant):
    c = rewrite(crate(tmp_path), plant)
    refused("spelling", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))


def test_a_raw_result_that_states_no_shots_is_accepted(tmp_path, monkeypatch):
    """Round 6, 8.1 item 11: a count is checked where it is stated, and need not be."""
    own_generator(monkeypatch)
    c = rewrite(crate(tmp_path), lambda md: entity(md, RAW).pop("qro:shots"))
    assert "qro:shots" not in entity(checker.check(c), RAW)


# -- P0.1's verifier, round 1: the test reach of its notes 4.1.1 and 4.2 -----------------------------------------
def test_the_walk_reports_the_first_of_one_directorys_files_by_name(tmp_path, monkeypatch):
    """The order of names within one directory: the host's listing reversed, three files the walk is told are
    links."""
    real_scandir, real_link = os.scandir, checker._is_link
    monkeypatch.setattr(os, "scandir", lambda path=".": _Reversed(real_scandir(path)))
    c = crate(tmp_path)
    for name in ("b.txt", "a.txt", "c.txt"):
        (c / "data" / name).write_bytes(b"x")
    monkeypatch.setattr(checker, "_is_link", lambda p: p.name in ("a.txt", "b.txt", "c.txt") or real_link(p))
    r = refused("file-link", lambda: checker.check(c))
    assert r.where == "data/a.txt"


def test_a_file_below_a_directory_named_as_the_descriptor_is_refused(tmp_path):
    """The descriptor is a file: a path through it as a directory is one the host cannot hold."""
    c = rewrite(crate(tmp_path), lambda md: listed(md, canonical.DESCRIPTOR + "/x.txt"))
    r = refused("graph-form", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert (r.detail, r.where) == (f"{canonical.DESCRIPTOR} is both a file and a directory",
                                   canonical.DESCRIPTOR + "/x.txt")


def test_a_metadata_file_that_is_a_directory_is_file_missing(tmp_path):
    """Without the regular-file test, the read raised: IsADirectoryError, exit 3, or on Windows PermissionError."""
    c = tmp_path / "crate"
    (c / canonical.DESCRIPTOR).mkdir(parents=True)
    r = refused("file-missing", lambda: checker.check(c))
    assert r.where == canonical.DESCRIPTOR


def test_a_crate_the_user_cannot_list_is_misuse_though_its_metadata_is_not_json(tmp_path, monkeypatch, capfd):
    """Note 4.1.1: check() lists the crate before it reads the metadata, so a crate the user cannot list is misuse,
    exit 2, whatever its metadata holds (FORMAT.md item 16). It was refused `spelling`, exit 1."""
    from qro.__main__ import main
    c = crate(tmp_path)
    (c / canonical.DESCRIPTOR).write_bytes(b"not metadata")
    real = os.listdir

    def listdir(path="."):
        if pathlib.Path(path) == c:
            raise PermissionError(13, "permission denied", os.fspath(path))
        return real(path)
    monkeypatch.setattr(os, "listdir", listdir)
    assert main(["check", "--fixtures", str(c)]) == 2
    assert "cannot be read here" in capfd.readouterr().err
