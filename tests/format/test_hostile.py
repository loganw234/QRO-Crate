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
]


@pytest.mark.parametrize("raw, rule", RAW_FORM_FAULTS,
                         ids=["nan", "deep", "no-final-line-feed", "unequal-bitstrings", "a-non-bit-key",
                              "a-non-bit-tail", "a-negative-count", "no-outcome"])
def test_a_raw_result_its_reader_cannot_read_is_raw_form(tmp_path, raw, rule):
    c = crate(tmp_path)
    (c / RAW).write_bytes(raw)
    rewrite(c, lambda md: entity(md, RAW).update(sha256=hashlib.sha256(raw).hexdigest(), contentSize=str(len(raw))))
    r = refused("raw-form", lambda: checker.check(c))
    assert rule in r.detail, r.detail


def test_a_reader_that_crashes_is_raw_form_and_a_generator_that_crashes_is_metadata_generated(tmp_path):
    c = crate(tmp_path)

    def boom(_):
        raise ZeroDivisionError("a parcel's bug")
    checker.RAW_FORMS[fixture.RAW_FORM] = boom
    refused("raw-form", lambda: checker.check(c))
    fixture.register()
    checker.GENERATORS[fixture.GENERATOR] = boom
    refused("metadata-generated", lambda: checker.check(c))


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
    ("local-file", "sha256", "a" * 64), ("local-file", "contentSize", "1"), ("qro:RawResult", "qro:shots", 9),
    ("qro:RawResult", "qro:rawForm", "x"), ("Dataset", "hasPart", [{"@id": "data/notes.txt"}]),
    ("File", "encodingFormat", "text/plain")])
def test_an_entity_whose_id_spells_a_domain_is_not_of_it(tmp_path, ident, key, value):
    """P0's verifier, round 2 (R2-3): every domain token was matched against the @id too, so an entity named
    `qro:RawResult` could state a count no step reads. Only the root's and the descriptor's tokens are @ids."""
    def add(md):
        md["@graph"].append({"@id": ident, "@type": "CreativeWork", key: value})
        md["@graph"][2:] = sorted(md["@graph"][2:], key=lambda x: x["@id"])
    c = rewrite(crate(tmp_path), add)
    r = refused("graph-form", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == f"{ident} {key}"


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
        listed(md, "data/a%20b.counts.json")
        e = entity(md, "data/a%20b.counts.json")
        e["@type"] = ["File", "qro:RawResult"]
        e["qro:rawForm"] = fixture.RAW_FORM
    c = rewrite(crate(tmp_path), add)
    r = refused("spelling", lambda: reader.read((c / canonical.DESCRIPTOR).read_bytes()))
    assert r.where == "data/a%20b.counts.json @id"


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


def test_a_crate_of_the_descriptor_and_the_root_alone_is_accepted(tmp_path, monkeypatch):
    """Round 3, row 14: the smallest graph the reader takes is two entities."""
    own_generator(monkeypatch)

    def bare(md):
        md["@graph"] = md["@graph"][:2]
        md["@graph"][1]["hasPart"] = [{"@id": "https://example.org/remote.json"}]
    c = rewrite(crate(tmp_path), bare)
    for f in (c / "data").iterdir():
        f.unlink()
    (c / "data").rmdir()
    assert len(checker.check(c)["@graph"]) == 2


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
    """Round 5: qro/data/README.md says the reader refuses any other bytes; nothing held it."""
    from qro import vocabulary as V
    reader.rocrate_terms.cache_clear()
    monkeypatch.setattr(V, "ROCRATE_CONTEXT_SHA256", "0" * 64)
    try:
        with pytest.raises(RuntimeError, match="not the copy the vocabulary pins"):
            reader.rocrate_terms()
    finally:
        reader.rocrate_terms.cache_clear()


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
