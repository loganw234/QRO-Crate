"""Each spelling's examples, accepted and refused, walked both ways, and its writers (study QRO-0, section 9: one
spelling per value). tests/format/test_sweep.py holds the string spellings to statements of their rules over
strings one change from its own examples, over the characters its docstring lists."""
import posixpath
import random
import re
from datetime import datetime, timezone
from fractions import Fraction
from urllib.parse import urljoin, urlsplit, urlunsplit

import pytest

from qro import spelling as S
from qro import vocabulary as V


@pytest.mark.parametrize("x, want", [(1.0, "1e+0"), (0.5, "5e-1"), (100.0, "1e+2"), (0.0, "0"), (-0.0, "-0"),
                                     (float("inf"), "inf"), (float("-inf"), "-inf"), (-2.5, "-2.5e+0"),
                                     (0.1, "1.000000000000000055511151231257827021181583404541015625e-1")])
def test_exact_decimal_is_cft_fp256s_spelling(x, want):
    assert S.binary64(x).split(" ")[1] == want
    assert S.problem("binary64", S.binary64(x)) is None


def test_a_binary64_whose_decimal_is_not_its_bits_is_refused():
    good = S.binary64(0.5)
    assert S.problem("binary64", good.replace("5e-1", "0.5")) is not None
    assert S.problem("binary64", good.replace("5e-1", "5e-01")) is not None
    assert S.problem("binary64", "7ff8000000000000 nan") == "a NaN"


@pytest.mark.parametrize("ok", ["1/3", "-1/2", "0/1", "5/16", "85/273"])
def test_rationals_in_lowest_terms(ok):
    assert S.problem("rational", ok) is None


@pytest.mark.parametrize("bad", ["2/4", "0/3", "-0/1", "+1/3", "1/-3", "01/3", "1/0", "1/A", "1/3 ", "1"])
def test_every_other_spelling_of_a_rational_is_refused(bad):
    """cft-fp256's refused spellings, in decimal (docs/CERTIFICATES.md:175-227)."""
    assert S.problem("rational", bad) is not None


def test_the_rational_writer_reduces():
    assert S.rational(Fraction(2, 4)) == "1/2" and S.rational(0) == "0/1" and S.rational(Fraction(-3, 6)) == "-1/2"


@pytest.mark.parametrize("value, ok", [(0, True), (8, True), (2**63 - 1, True), (2**63, False), (-1, False),
                                       (True, False), (8.0, False), ("8", False), (None, False)])
def test_integers(value, ok):
    assert (S.problem("integer", value) is None) is ok


@pytest.mark.parametrize("value, ok", [("2026-10-14T10:26:13Z", True), ("2026-10-14T10:26:13.5Z", True),
                                       ("2026-10-14T10:26:13.50Z", False), ("2026-10-14T10:26:13.0Z", False),
                                       ("2026-10-14T10:26:13+00:00", False), ("2026-10-14 10:26:13Z", False),
                                       ("2026-02-30T00:00:00Z", False), ("2026-10-14T24:00:00Z", False)])
def test_times(value, ok):
    assert (S.problem("time", value) is None) is ok


def test_the_time_writer_drops_a_zero_fraction_and_trailing_zeros():
    assert S.time(datetime(2026, 10, 14, 10, 26, 13, tzinfo=timezone.utc)) == "2026-10-14T10:26:13Z"
    assert S.time(datetime(2026, 10, 14, 10, 26, 13, 500000, tzinfo=timezone.utc)) == "2026-10-14T10:26:13.5Z"
    with pytest.raises(ValueError):
        S.time(datetime(2026, 10, 14))


EXAMPLES = {   # spelling: (accepted, refused); every spelling the vocabulary names, walked both ways (N7)
    "integer": ([0, 8, 2**63 - 1], [-1, 2**63, 8.0, True, "8"]),
    "size": (["0", "23"], ["023", "-1", 23, "9" * 20, "٢٣"]),
    "digest": (["a" * 64], ["A" * 64, "a" * 63, "g" * 64]),
    "commit": (["0" * 40], ["0" * 64, "G" * 40]),
    "rational": (["1/3", "-1/2", "0/1"], ["2/4", "0/3", "1/0", "+1/3", "1/3 "]),
    "binary64": (["3fe0000000000000 5e-1"], ["3fe0000000000000 0.5", "7ff8000000000000 nan", "zz",
                                            "3FE0000000000000 5e-1", "3fe0000000000000"]),
    "time": (["2026-10-14T10:26:13Z", "2026-10-14T10:26:13.5Z"],
             ["2026-10-14T10:26:13.50Z", "٢٠٢٦-10-14T00:00:00Z", "2026-10-14T24:00:00Z",
              "2016-12-31T23:59:60Z"]),
    "date": (["2026-10-14"], ["20261014", "2026-W42-3", "2026-13-01", "２０２６-10-14"]),
    "text": (["a name", "two\nlines", "caf\u00e9", "a \u2014 b", "a\u00a0b"],
             ["", " a", "a\x00b", "a\ud800b", "a\tb", "a\rb", "a\x0bb", "a\x0cb", "a\x1bb", "a\x1fb",
              "a\x7fb", "a\x80b", "a\x85b", "a\x9fb"]),
    "iri": (["https://w3id.org/ro/crate/1.3"], ["data/x.json", "https://example.org/café",
                                                "https://example.org/a b", "c:x", "a.b:x"]),
    "ref": ([{"@id": "./"}], [{"@id": "./", "name": "x"}, {"@id": "a b"}, "./"]),
    "slot": ([], ["anything"]),
}


def test_every_spelling_has_examples_both_ways():
    assert set(EXAMPLES) == set(V.SPELLINGS)
    for spelling, (ok, bad) in EXAMPLES.items():
        for v in ok:
            assert S.problem(spelling, v) is None, (spelling, v)
        for v in bad:
            assert S.problem(spelling, v) is not None, (spelling, v)


@pytest.mark.parametrize("spelling, value, ok", [
    ("digest", "a" * 64, True), ("digest", "A" * 64, False), ("digest", "a" * 63, False),
    ("commit", "0" * 40, True), ("commit", "0" * 64, False),
    ("size", "0", True), ("size", "23", True), ("size", "023", False), ("size", 23, False),
    ("date", "2026-10-14", True), ("date", "2026-13-01", False),
    ("text", "a name", True), ("text", " a name", False), ("text", "", False),
    ("iri", "https://w3id.org/ro/crate/1.3", True), ("iri", "data/x.json", False),
    ("ref", {"@id": "./"}, True), ("ref", {"@id": "./", "name": "x"}, False), ("ref", {"@id": "a b"}, False),
    ("word:device-kind", "qpu", True), ("word:device-kind", "QPU", False),
    ("slot", "anything", False),
])
def test_each_spelling(spelling, value, ok):
    assert (S.problem(spelling, value) is None) is ok


@pytest.mark.parametrize("value, ok", [("./", True), ("data/x.json", True), ("#frag", True), ("https://x.org/y", True),
                                       ("a b", False), ("a\x7fb", False), ("", False), ("caf\u00e9", False),
                                       ("a\tb", False), (5, False)])
def test_an_id_is_printable_ascii_with_no_space(value, ok):
    """The @id rule, which no term's spelling names (P0's verifier, round 2: DEL was let through unnoticed)."""
    assert (S.id_problem(value) is None) is ok


HEX = "0123456789abcdef"
DIGITS = "0123456789"
SCHEME = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-"
PRINTABLE = "".join(chr(c) for c in range(0x21, 0x7f))
ALNUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
SEGMENT_CHARS = ALNUM + "._~!$&'()+,;=@-"
FRAGMENT_CHARS = ALNUM + "._~!$&'()*+,;=:@/?-"        # and escapes; an absolute IRI's tail the same, one # too
IRI_TAIL_CHARS = ALNUM + "._~:/?@!$&'()*+,;=-"
ESCAPES = "%01%23%45%67%89%ab%cd%ef%AB%CD%EF"                 # every hex digit after a %, in both cases
LOWER_SCHEME = "abcdefghijklmnopqrstuvwxyz0123456789+-"
CLASS_ACCEPTED = {   # round 3, note 1: every character each rule admits, in an accepted value
    "digest": [HEX * 4],
    "commit": [(HEX * 3)[:40]],
    # every digit in every field: a class's members are each in some accepted value, at each place it stands
    "size": ["1234567890", "9223372036854775807"] + [str(d) for d in range(1, 10)],
    "rational": (["1234567890/1", "11/1", "1/1234567890", "1/11", "-987654321/2", "9" * 1000 + "/1", "1/" + "9" * 1000]
                 + [f"{d}/1" for d in range(1, 10)] + [f"1/{d}" for d in range(1, 10)]),
    "time": ([f"20{d}{d}-0{d}-0{d}T0{d}:0{d}:0{d}.{d}Z" for d in range(1, 10)]
             + [f"{y}-{m}-{dd}T{h}:{mi}:{sec}Z" for y, m, dd, h, mi, sec in
                [("1000", "10", "10", "10", "10", "10"), ("2000", "12", "19", "19", "59", "58"),
                 ("1987", "11", "28", "23", "47", "36"), ("2026", "10", "30", "20", "30", "40")]]
             + ["2000-01-01T00:00:00.0123456789Z", "2000-01-01T00:00:00.91Z"]),
    "date": [f"20{d}{d}-0{d}-0{d}" for d in range(1, 10)] + ["1000-10-10", "2000-12-19", "1987-11-28", "2026-10-30"],
    "iri": [SCHEME + ":" + PRINTABLE] + [f"{c}b:x" for c in SCHEME[:52]],
    "text": ["x " + PRINTABLE + "\n\u00a0\u2014\U0001f600 x"],
    # an @id's four forms, each with every character its form admits (P0.5)
    "ref": [{"@id": "./"}, {"@id": "x" + SEGMENT_CHARS + "/" + SEGMENT_CHARS + "/"},
            {"@id": "#" + FRAGMENT_CHARS + ESCAPES},
            {"@id": "urn:" + IRI_TAIL_CHARS + ESCAPES + "#" + IRI_TAIL_CHARS + ESCAPES},
            {"@id": LOWER_SCHEME + ":x"}],
}


@pytest.mark.parametrize("spelling", sorted(CLASS_ACCEPTED))
def test_every_character_a_spelling_admits_is_in_an_accepted_value(spelling):
    for v in CLASS_ACCEPTED[spelling]:
        assert S.problem(spelling, v) is None, (spelling, str(v)[:80])


@pytest.mark.parametrize("value", ["./", "ro-crate-metadata.json", "data/", "data/run1/", "x", "a/b/c.json",
                                   "data/.hidden", "a@b", "x/@y", "...", "a/.../b", "#a", "#a/b?c:d@e", "#a%20b",
                                   "#job-db1", "#a:/b", "#a//b", "#//b", "a;b.txt", "data/notes;v2.txt", ";x", "a/;x",
                                   "x;;", "x;y;", "a;/", "a;/b", "x;/", "#a%2Fb", "https://example.org/a",
                                   "https://example.org/a%20b?q=1#f", "ab:x#y", "ab:#", "http://example.org/a/../b",
                                   "https://example.org/x;", "ab:x;", "urn:uuid:0123", "ab:x", "name:x", "geo:x",
                                   "tag:x", "a+b-c9:x"])
def test_an_id_in_one_of_the_four_forms_is_accepted(value):
    """P0.5: the root, a path (a directory's ending in /), a fragment, or an absolute IRI whose scheme is no prefix
    of the context: `name` and `geo` are terms of RO-Crate's context whose IRIs end in no gen-delim, so no prefix
    (MEASURED, rdflib 7.6.0: `name:x` stays an IRI of the scheme `name`). A ; in a last segment is accepted where
    urllib keeps the params it splits there (`a;b.txt`, `;x`, `x;;`), and anywhere in a directory's path; a fragment
    may hold :// 's pieces apart (P0.5's verifier, round 1). A fragment and an absolute IRI may hold escapes, a % and
    two hex digits, and an absolute IRI one # (round 2, note 4)."""
    assert S.id_problem(value) is None and S.problem("ref", {"@id": value}) is None


@pytest.mark.parametrize("value, why", [
    ("_:b0", "a blank node"), ("@x", "the root"), ("@x/y", "the root"), (".", "the root"), ("././", "the root"),
    ("./x", "x"), ("./#a", "#a"), ("//x", "a host"), ("//", "the root"), ("a//b", "a/b"), ("a/./b", "a/b"),
    ("a/../b", "b"), ("../a", "outside the crate"), ("data//", "an empty segment"), ("schema:a", "http://schema.org/a"),
    ("qro:x", "the vocabulary's IRI"), ("rdf:type", "rdf's"), ("dct:title", "dct's"), ("file:///crate/a", "the path a"),
    ("a?", "a, its empty query dropped"), ("?", "the root"), ("/x", "the host's /x, outside the crate"),
    ("@0", "the root"), ("@9/y", "the root"), ("schema:0", "http://schema.org/0"), ("rdf:_1", "rdf's _1"),
    ("schema:a#b", "http://schema.org/a#b"),
    ("https://example.org/a b", "no node"), ("a b", "no node"),
    ("#a://b", "a relative IRI"), ("#a:b://c", "a relative IRI"), ("#:://", "a relative IRI"),
    ("x;", "x at an http base"), ("data/notes.txt;", "data/notes.txt at an http base"), ("a/b;", "a/b at one"),
    (";", "the root at one"), (".;", "the root at one"), ("a/..;", "the root at one"), ("..;", "the crate's parent at one"),
    (".;x", ";x at one"), ("..;x", ";x in the crate's parent at one"), ("a/.;x", "a/;x at one")])
def test_an_id_a_json_ld_reader_reads_otherwise_is_refused(value, why):
    """P4's verifier, round 1, defect 1; the lead's measurement with rdflib 7.6.0 under the base file:///crate/; and
    P0.5's verifier, round 1, for the fragments holding :// (at every base) and the last segments ending in an
    empty ;params or beginning .; or ..; (at an http, https, ftp or like base); and round 2, for an empty query, a path from
    the host's root, and a space, which makes no node; round 3, for @ before a digit and compact IRIs whose tail is
    no letter's, or holds a #: each of these is read as another IRI, as a blank node, as no
    node, or not as the id it spells (`why`), so two entities the checker held apart could be one node in RDF, or
    one could vanish. A reference's @id is held to the same rule (P0.5)."""
    assert S.id_problem(value) is not None and S.problem("ref", {"@id": value}) is not None, why


@pytest.mark.parametrize("value, why", [
    ("@", "no @ first, JSON-LD's keywords' mark"), ("x#a", "a thing inside a file"), ("data/#a", "a thing inside a directory"),
    ("#", "an empty fragment"), ("#a#b", "a second #"), ("?q", "a query"), ("a?b", "a query"),
    ("HTTPS://example.org/a", "an uppercase scheme"), ("Https://example.org/a", "an uppercase scheme"),
    ("file:a", "a file: IRI"), ("C:/x", "a drive"), ("notes.txt:hidden", "a stream"),
    ("https://example.org/<a>", "no IRI's characters"), ("ab:%zz", "a % beginning no escape"),
    ("#a%2", "a % beginning no escape"), ("http://a/b#c#d", "a second #"),
    ("ab://[", "a bracket, which urllib's urlsplit raises on"), ("http://[::1]/x", "an IPv6 literal's brackets")])
def test_an_id_in_a_form_the_rule_does_not_offer_is_refused(value, why):
    """P0.5's verifiers, rounds 1 and 2: rdflib 7.6.0 makes of each of these the IRI it spells, so none is refused
    for a collision. Each is a form the four do not offer (`why`), refused so that an IRI has one spelling: the
    profile names nothing inside a file, and no query; a scheme is written in lowercase; a file: IRI cannot be told
    from a path in the crate; and a fragment or an absolute IRI holds RFC 3986's characters but brackets, each %
    beginning an escape, and one # at most, so that urllib's urlsplit, which raises on a bracket out of place,
    reads every accepted id (round 2, note 4)."""
    assert S.id_problem(value) is not None and S.problem("ref", {"@id": value}) is not None, why


@pytest.mark.parametrize("tail", ["x", "0", "_1", "a#b", "%41", "-"])
@pytest.mark.parametrize("prefix", sorted(V.CONTEXT_PREFIXES))
def test_every_prefix_of_the_context_makes_a_compact_iri_which_is_refused(prefix, tail):
    """Whatever its tail: rdflib expands schema:0, rdf:_1 and schema:a#b as it does schema:x (P0.5's verifier, round
    3, note 1: a rule that refused a compact IRI only when its tail began with a letter, or held no #, passed)."""
    assert "compact IRI" in S.id_problem(prefix + ":" + tail)


_URI = re.compile(r"(?:([^:/?#]+):)?(?://([^/?#]*))?([^?#]*)(?:\?([^#]*))?(?:#(.*))?", re.S)


def rfc3986(base, ref):
    """RFC 3986's resolution of a relative reference against a base (section 5.2), strictly: what JSON-LD 1.1 asks
    of a relative @id (its API, section 5.2.2, READ)."""
    def dots(path):    # section 5.2.4
        out = []
        while path:
            if path.startswith(("../", "./")):
                path = path[path.index("/") + 1:]
            elif path.startswith("/./") or path == "/.":
                path = "/" + path[3:]
            elif path.startswith("/../") or path == "/..":
                path = "/" + path[4:]
                out = out[:-1]
            elif path in (".", ".."):
                path = ""
            else:
                i = path.find("/", 1)
                i = len(path) if i < 0 else i
                out, path = out + [path[:i]], path[i:]
        return "".join(out)
    bs, ba, bp, bq, _ = _URI.fullmatch(base).groups()
    s, a, p, q, f = _URI.fullmatch(ref).groups()
    if s is not None:
        bs, ba, path = s, a, dots(p)
    elif a is not None:
        path = dots(p)
    elif p == "":
        path, q = bp, (q if q is not None else bq)
    elif p.startswith("/"):
        path = dots(p)
    else:
        path = dots(("/" + p) if ba is not None and bp == "" else bp[:bp.rfind("/") + 1] + p)
    a = a if a is not None or s is not None else ba
    return (bs + ":" + ("//" + a if a is not None else "") + path + ("?" + q if q is not None else "")
            + ("#" + f if f is not None else ""))


def rdflib_reads(base, ref):
    """The IRI rdflib 7.6.0's JSON-LD reader makes of an @id at a base, as its norm_url makes it (rdflib/plugins/
    shared/jsonld/util.py, READ), modelled here, as rdflib is the engine's and not the checker's to import. Its
    Context.expand, which reads a compact IRI, a keyword's form, a blank node and a space first, is not modelled:
    the lists above hold those, and the model is exact on every id the rule accepts (P0.5's verifier, round 3, note
    3). An id holding :// is
    left as it is, and one with a scheme is itself; at a urn base the id's path is joined onto the URN's own;
    otherwise urllib's urljoin, its path then normalised as POSIX's normpath does, a directory's / kept; and an id
    ending in # keeps it (P0.5's verifier, round 2, note 2: the model had left that clause out, which no accepted id
    reaches). The model and rdflib itself make the same IRI of each of 300,000 ids at nine bases (MEASURED after
    P0.5's second round)."""
    if "://" in ref or urlsplit(ref).scheme:
        return ref
    b = urlsplit(base)
    if b.scheme in ("urn", "urn-x"):
        head, _, rest = b.path.partition("/")
        r = urlsplit(ref)
        iri = f"{b.scheme}:{head}{urljoin('/' + rest, r.path)}" + (f"#{r.fragment}" if r.fragment else "")
    else:
        parts = urlsplit(urljoin(base, ref))
        path = posixpath.normpath(parts.path)
        if parts.path.endswith("/") and not path.endswith("/"):
            path += "/"
        iri = urlunsplit(parts._replace(path=path))
    return iri + "#" if ref.endswith("#") and not iri.endswith("#") else iri


# Bases a crate is read at: P4's, a published crate's (https, http, ftp), one whose path holds ;params, and the
# metadata file's own URL, at each of which rdflib reads a relative id as RFC 3986 resolves it; and a urn, which
# rdflib joins otherwise.
BASES = ["file:///crate/", "https://example.org/crate/", "http://example.org/a/b/", "https://example.org/crate/x;p/",
         "ftp://example.org/crate/", "https://example.org/crate/ro-crate-metadata.json"]
URN_BASE = "urn:example:crate"
# Pieces spliced into drawn ids, so that the shapes a reader reads otherwise are drawn often, not by chance
# (P0.5's verifier, round 1: about 6,700 short fragments drew no ://).
SPLICES = ["://", ":/", "//", "/./", "/../", "./", "../", ";", ";/", "/;", "..;", ".;", ";.", "x;", "#", "?", "@", ":",
           "%", "..", "%2F", "%41", "["]


def drawn_ids(n, seed):
    """`n` ids drawn from the four forms' characters, pieces spliced in, and how many of each shape the rule refused."""
    rng, ids, refused = random.Random(seed), [], {"fragment holding ://": 0, "last segment ;": 0, "other": 0}

    def word(chars, lo=1, hi=8):
        s = "".join(rng.choice(chars) for _ in range(rng.randint(lo, hi)))
        for _ in range(rng.randint(0, 2)):
            k = rng.randint(0, len(s))
            s = s[:k] + rng.choice(SPLICES) + s[k:]
        return s
    while len(ids) < n:
        form = rng.randrange(5)
        if form < 2:
            v = "/".join(word(SEGMENT_CHARS, 0, 6) for _ in range(rng.randint(1, 3)))
            v += rng.choice(["", "", "/", ";", ";x", ".;"])     # a ; at the end, kept or not, often
        elif form < 4:
            v = "#" + word(FRAGMENT_CHARS)
        else:     # never under a base: an absolute IRI that is a path of the crate is item 22's stated limit
            v = rng.choice(["https://example.net/", "urn:", "ab:", "tag:x,", "ftp://example.net/"]) + word(IRI_TAIL_CHARS)
        p = S.id_problem(v)
        if p is None:
            ids.append(v)
        elif p.startswith("a fragment holding ://"):
            refused["fragment holding ://"] += 1
        elif p.startswith("a last segment"):
            refused["last segment ;"] += 1
        else:
            refused["other"] += 1
    return ["./"] + sorted(set(ids)), refused


def test_distinct_ids_resolve_to_distinct_iris():
    """P0.5: the property the rule is for, at several bases (P0.5's verifier, round 1: the test read one, where
    urllib agrees with RFC 3986 on ;). Ids drawn from the four forms, each with every character it admits and the
    shapes a reader reads otherwise spliced in, are read as rdflib reads them (`rdflib_reads`). At each base but the
    urn, each relative id's IRI is RFC 3986's resolution of it, and is the base, or its directory, with the id after
    it, so that no other spelling reads the same (round 2, note 1: without that, a leading ./ let through passed this
    test); an absolute id is itself; and at every base, no two distinct ids name one IRI. rdflib itself is the
    engine stage's, P4's, to hold."""
    ids, refused = drawn_ids(12000, 5)
    assert len(ids) > 11000 and refused["fragment holding ://"] > 300 and refused["last segment ;"] > 300, refused
    for base in BASES + [URN_BASE]:
        seen = {}
        for v in ids:
            iri = rdflib_reads(base, v)
            if base != URN_BASE:
                assert iri == (v if urlsplit(v).scheme else rfc3986(base, v)), (base, v, iri)
                if not urlsplit(v).scheme:
                    head = base if v.startswith("#") else base[:base.rfind("/") + 1]
                    assert iri == head + ("" if v == "./" else v), (base, v, iri)
            assert seen.setdefault(iri, v) == v, (base, seen[iri], v, iri)


@pytest.mark.parametrize("value", ["#a://b", "#:://", "x;", "a/b;", ";", ".;", "a/..;", ".;x", "..;x", "a/.;x"])
def test_the_model_of_rdflib_reads_each_shape_the_rule_refuses_otherwise(value):
    """The property test's model can fail: each shape P0.5's verifier found accepted and read otherwise, round 1, the
    model reads otherwise at an https base, where RFC 3986 reads it as its spelling. So were the rule to accept one,
    `test_distinct_ids_resolve_to_distinct_iris` would fail on it."""
    base = "https://example.org/crate/"
    assert rdflib_reads(base, value) != rfc3986(base, value) == base + value


def test_the_model_keeps_a_trailing_hash_as_rdflib_does():
    """P0.5's verifier, round 2, note 2, MEASURED with rdflib 7.6.0: `#` at file:///crate/ is file:///crate/#. No
    accepted relative id ends in #, and an absolute one that does (`ab:#`) is left as written before the clause, so
    this is the one test of it (P0.5's verifier, round 3, D2)."""
    assert rdflib_reads("file:///crate/", "#") == "file:///crate/#"
    assert rdflib_reads("https://example.org/crate/", "x#") == "https://example.org/crate/x#"


def test_rfc_3986s_own_examples_are_resolved_as_it_says():
    """The resolver the property test trusts, held to RFC 3986's section 5.4 examples, normal and abnormal."""
    base = "http://a/b/c/d;p?q"
    for ref, want in [("g:h", "g:h"), ("http:g", "http:g"), ("g", "http://a/b/c/g"), ("./g", "http://a/b/c/g"), ("g/", "http://a/b/c/g/"),
                      ("/g", "http://a/g"), ("//g", "http://g"), ("?y", "http://a/b/c/d;p?y"),
                      ("g?y", "http://a/b/c/g?y"), ("#s", "http://a/b/c/d;p?q#s"), ("g#s", "http://a/b/c/g#s"),
                      (";x", "http://a/b/c/;x"), ("g;x", "http://a/b/c/g;x"), ("", "http://a/b/c/d;p?q"),
                      (".", "http://a/b/c/"), ("./", "http://a/b/c/"), ("..", "http://a/b/"), ("../", "http://a/b/"),
                      ("../g", "http://a/b/g"), ("../..", "http://a/"), ("../../g", "http://a/g"),
                      ("../../../g", "http://a/g"), ("/./g", "http://a/g"), ("/../g", "http://a/g"),
                      ("g.", "http://a/b/c/g."), (".g", "http://a/b/c/.g"), ("g..", "http://a/b/c/g.."),
                      ("..g", "http://a/b/c/..g"), ("./../g", "http://a/b/g"), ("./g/.", "http://a/b/c/g/"),
                      ("g/./h", "http://a/b/c/g/h"), ("g/../h", "http://a/b/c/h"), ("g;x=1/./y", "http://a/b/c/g;x=1/y"),
                      ("g;x=1/../y", "http://a/b/c/y"), ("g?y/./x", "http://a/b/c/g?y/./x"),
                      ("g#s/../x", "http://a/b/c/g#s/../x")]:
        assert rfc3986(base, ref) == want, ref


def test_each_field_of_a_time_and_a_date_holds_every_digit_it_may():
    """Round 3, note 1, field by field: the rule's classes stand at each field, so each field's digits are held."""
    times = [t for t in CLASS_ACCEPTED["time"]]
    fields = {"year": (0, 4), "month": (5, 7), "day": (8, 10), "hour": (11, 13), "minute": (14, 16), "second": (17, 19)}
    for name, (a, b) in fields.items():
        assert set(DIGITS) <= set("".join(t[a:b] for t in times)), name
    fractions = [t[20:-1] for t in times if t[19] == "."]
    assert set(DIGITS) <= set("".join(f[:-1] for f in fractions)) and set("123456789") <= {f[-1] for f in fractions}
    dates = CLASS_ACCEPTED["date"]
    for name, (a, b) in list(fields.items())[:3]:
        assert set(DIGITS) <= set("".join(d[a:b] for d in dates)), name
    assert set("123456789") <= {v[0] for v in CLASS_ACCEPTED["size"]}
    rationals = [r.lstrip("-").split("/") for r in CLASS_ACCEPTED["rational"]]
    assert set("123456789") <= {n[0] for n, _ in rationals} and set("123456789") <= {d[0] for _, d in rationals}
    assert set(DIGITS) <= set("".join(n[1:] for n, _ in rationals)) and set(DIGITS) <= set("".join(d[1:] for _, d in
                                                                                                 rationals))


def test_the_class_examples_cover_their_classes():
    seen = lambda s: set("".join(CLASS_ACCEPTED[s]))                          # noqa: E731
    assert set(HEX) <= seen("digest") and set(HEX) <= seen("commit") and set(DIGITS) <= seen("size")
    assert set(DIGITS) <= seen("rational") and set(DIGITS) <= seen("time") and set(DIGITS) <= seen("date")
    assert set(SCHEME) | set(PRINTABLE) <= seen("iri") and set(PRINTABLE) <= seen("text")
    ids = "".join(v["@id"] for v in CLASS_ACCEPTED["ref"])
    assert set(SEGMENT_CHARS + FRAGMENT_CHARS + IRI_TAIL_CHARS + LOWER_SCHEME + ESCAPES + "#") <= set(ids)


@pytest.mark.parametrize("bad", ["9223372036854775808", "9" * 19 + "0", "1" + "0" * 19])
def test_a_size_past_two_to_the_63_minus_one_is_refused(bad):
    """Round 3, row 15, the other side: 2^63 - 1 is accepted above, and nothing past it."""
    assert S.problem("size", bad) is not None


@pytest.mark.parametrize("bad", ["9" * 1001 + "/1", "1/" + "9" * 1001, "-" + "9" * 1001 + "/1"])
def test_a_rational_term_past_its_cap_is_refused(bad):
    assert S.problem("rational", bad) == "a term of more than 1000 digits"


def test_every_binary64_spelling_is_its_own_and_uses_every_character():
    values = [i / 7 for i in range(-40, 41)] + [1e300, -1e-300, 2.0**-1074, 123456789.0]
    spelt = [S.binary64(x) for x in values]
    assert all(S.problem("binary64", v) is None for v in spelt)
    assert set(HEX) <= set("".join(v.split(" ")[0] for v in spelt))
    assert set(DIGITS + ".e+-") <= set("".join(v.split(" ")[1] for v in spelt))


@pytest.mark.parametrize("year", [1, 5, 99, 999, 1000, 9999])
def test_the_time_writer_pads_every_year_to_four_digits(year):
    """Round 5: strftime's %Y left a year below 1000 unpadded on glibc, so the writer wrote what the reader
    refuses."""
    t = S.time(datetime(year, 1, 2, 3, 4, 5, tzinfo=timezone.utc))
    assert t == f"{year:04d}-01-02T03:04:05Z" and S.problem("time", t) is None


def test_a_negative_numerator_of_exactly_the_cap_is_accepted():
    """Round 5: the sign does not count toward the 1,000 digits."""
    assert S.problem("rational", "-" + "9" * 1000 + "/1") is None


def test_every_lone_surrogate_is_refused_in_text():
    """The sweep tries the surrogates' edges; this tries all 2,048 (the lead's check of round 5's mutants: U+D83D,
    taken out of the deny list, went unseen)."""
    assert [hex(c) for c in range(0xD800, 0xE000) if S.problem("text", "a" + chr(c) + "b") is None] == []


def test_a_spelling_the_table_does_not_name_is_an_error_not_an_acceptance():
    with pytest.raises(KeyError):
        S.problem("no-such-spelling", "x")


def test_the_time_writer_refuses_every_time_not_in_utc():
    """Round 6, 8.1 item 9 and 8.2 item 10: an offset, and a tzinfo that gives none, are ValueError."""
    from datetime import timedelta, tzinfo

    class NoOffset(tzinfo):
        def utcoffset(self, dt):
            return None
    for tz in (timezone(timedelta(hours=1)), NoOffset()):
        with pytest.raises(ValueError):
            S.time(datetime(2026, 10, 14, tzinfo=tz))


def test_the_time_writer_keeps_every_microsecond():
    assert S.time(datetime(2026, 10, 14, 0, 0, 0, 5, tzinfo=timezone.utc)) == "2026-10-14T00:00:00.000005Z"


def test_each_pattern_the_profile_publishes_is_the_one_its_spelling_is_held_to(monkeypatch):
    """P4's design, R-C (P0.3): PATTERNS is each spelling's pattern, which P4's shapes read, and problem() reads the
    same: a pattern changed there changes the spelling, so no pattern is written twice."""
    good = {"size": "12", "digest": "a" * 64, "commit": "b" * 40, "rational": "1/3", "binary64": S.binary64(0.5),
            "time": "2026-10-14T01:00:00Z", "date": "2026-10-14", "iri": "https://example.org/x"}
    assert set(S.PATTERNS) == set(good) and set(good) <= set(V.SPELLINGS)
    for name, value in good.items():
        assert S.PATTERNS[name].fullmatch(value) and S.problem(name, value) is None, name
        monkeypatch.setitem(S.PATTERNS, name, re.compile("(?!)"))
        assert S.problem(name, value) is not None, name
