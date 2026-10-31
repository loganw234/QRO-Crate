"""Ids for holding the expansion to the reader (P4's verifier, round 1, defect 1, after P0.5): strings drawn from FORMAT.md
item 22's grammar and from every string over a small alphabet of the characters that have meant something, and kept
when the reader accepts them, whatever the draw intended. The reader's own function is the oracle, `qro.spelling.id_problem`,
so a change of the rule changes the ids drawn and not this file. Nothing here is a test: pytest's naming decides what is
one, and a helper under tests/ names no function `test*` and no class `Test*` (CLAUDE.md).

  - `candidates(seed, drawn)`: strings of the four forms of item 22 in their variants, and strings that miss them by one
    character, `drawn` of them;
  - `small(alphabet, longest)`: every string over `alphabet` up to `longest` characters;
  - `accepted(strings)`: the distinct ones the reader accepts, sorted;
  - `drawn_ids(drawn)`: the ids both stages use, the accepted ones among `drawn` candidates and every small string;
  - `crate_of(ids)`: metadata with an entity under each id, named by its index, and a node that refers to each;
  - `unread(ids)`: those the expansion refuses to read; `collisions(ids)`: the IRIs it makes of more than one.

Two uses: the quick stage holds that the expansion reads every id the reader accepts and makes distinct IRIs of distinct
ids, and that every id it refuses the reader refuses (tests/p4/test_p4_ids.py); the engine stage holds that rdflib makes
the IRIs the expansion makes of them (tests/p4shacl/test_p4shacl_ids.py).
"""
import itertools
import random

from qro import p4_expand
from qro import spelling as S
from qro import vocabulary as V

PATH_CHARS = "AaBb09._~!$&'()+,;=@-"            # the characters of a path segment (FORMAT.md item 11), with the ones that bite
IRI_CHARS = PATH_CHARS + "*:/?"                   # a fragment's, a query's, a path's after a scheme
SCHEMES = ("https", "http", "ftp", "sftp", "ssh", "urn", "mailto", "tel", "tag", "doi", "ni", "ws", "wss", "git+ssh", "a-b",
           "x1", "ab", "rtsp", "rtsps", "imap", "mms", "shttp", "prospero", "data", "geo", "isbn", "name", "orcid", "s3",
           "ldap", "news", "sip", "xmpp", "dns", "cid", "about", "file", "schema", "dct", "qro", "rdf", "prov", "HTTPS", "a", "1a")
SMALL_ALPHABET = "a.;@#:/%?0"                     # every string over these up to four characters is in `small()`
HEX = "0123456789abcdefABCDEF"


def _chars(rnd, alphabet, low, high):
    return "".join(rnd.choice(alphabet) for _ in range(rnd.randint(low, high)))


def _escape(rnd):
    return "%" + rnd.choice(HEX) + rnd.choice(HEX) if rnd.random() < 0.9 else "%" + rnd.choice("g%z ") + rnd.choice(HEX)


def _run(rnd, alphabet, low, high):
    """Characters of `alphabet` with an escape now and then."""
    out = []
    for _ in range(rnd.randint(low, high)):
        out.append(_escape(rnd) if rnd.random() < 0.08 else rnd.choice(alphabet))
    return "".join(out)


def path(rnd):
    segments = [_chars(rnd, PATH_CHARS, 1, 6) for _ in range(rnd.choice((1, 1, 2, 2, 3, 4)))]
    if rnd.random() < 0.15:
        segments[rnd.randrange(len(segments))] = rnd.choice((".", "..", "", ".;", "..;", ";", "x;", ";x", "a;b", "@a", ".a", "a.", "..a"))
    return "/".join(segments) + ("/" if rnd.random() < 0.25 else "")


def fragment(rnd):
    return "#" + _run(rnd, IRI_CHARS, 0, 8) + (rnd.choice(("://", "#", "%", "[", "]")) if rnd.random() < 0.05 else "")


def authority(rnd):
    host = _chars(rnd, "abcxyz09.-", 1, 8)
    user = _chars(rnd, "uv:;=%.", 1, 3) + "@" if rnd.random() < 0.2 else ""
    port = ":" + _chars(rnd, "0123456789", 0, 4) if rnd.random() < 0.3 else ""
    return user + host + port


def absolute(rnd):
    scheme = rnd.choice(SCHEMES) if rnd.random() < 0.8 else rnd.choice("abxyz") + _chars(rnd, "abz09+-.", 0, 5)
    kind = rnd.randrange(7)
    if kind == 0:
        body = "//" + authority(rnd) + ("/" + _run(rnd, IRI_CHARS, 0, 12) if rnd.random() < 0.8 else "")
    elif kind == 1:
        body = _run(rnd, IRI_CHARS, 1, 12)
    elif kind == 2:
        body = "//" + authority(rnd) + "/" + "/".join(rnd.choice((".", "..", "a", "b", "", "%2e", "%2E")) for _ in range(rnd.randint(1, 5)))
    elif kind == 3:
        body = _run(rnd, IRI_CHARS, 1, 6) + "#" + _run(rnd, IRI_CHARS, 0, 5)
    elif kind == 4:
        body = "#" + _run(rnd, IRI_CHARS, 0, 5)
    elif kind == 5:
        body = "//" + authority(rnd) + "?" + _run(rnd, IRI_CHARS, 0, 6) + ("#" + _run(rnd, IRI_CHARS, 0, 4) if rnd.random() < 0.5 else "")
    else:
        body = "/" + _run(rnd, IRI_CHARS, 1, 8)
    return scheme + ":" + body


def one(rnd):
    r = rnd.random()
    if r < 0.02:
        return "./"
    if r < 0.40:
        return path(rnd)
    if r < 0.60:
        return fragment(rnd)
    return absolute(rnd)


def candidates(seed, drawn):
    """`drawn` strings from the four forms and a character or two off them, chosen by `seed` alone."""
    rnd = random.Random(seed)
    out = []
    for _ in range(drawn):
        s = one(rnd)
        if rnd.random() < 0.2 and s:                   # one character off: dropped, doubled, or another of the bites
            at = rnd.randrange(len(s))
            s = s[:at] + rnd.choice(("", s[at], ".", "/", "@", ";", "#", ":", "%", "?", "[", "]", " ", chr(0xE9))) + s[at + 1:]
        out.append(s)
    return out


def small(alphabet=SMALL_ALPHABET, longest=4):
    """Every string over `alphabet` of one to `longest` characters."""
    for n in range(1, longest + 1):
        for chars in itertools.product(alphabet, repeat=n):
            yield "".join(chars)


def accepted(strings):
    """The distinct strings the reader accepts as an @id, sorted."""
    return sorted({s for s in strings if S.id_problem(s) is None})


SEED, DRAWN = 3, 120000                           # the engine stage's draw: about 75,000 ids the reader accepts


def drawn_ids(drawn=DRAWN, seed=SEED):
    """The ids the reader accepts among `drawn` candidates and every short string over the small alphabet, sorted."""
    return accepted(candidates(seed, drawn) + list(small()))


REFS = "#refs"                                     # the node that refers to each id: no draw is this


def crate_of(ids):
    """Metadata in a QRO crate's form with an entity under each of `ids`, named by its index, and a node that refers to
    each of them: the id as a subject and as an object. Not a crate the checker accepts, and none is meant to be."""
    assert REFS not in ids
    graph = [{"@id": i, "@type": "CreativeWork", "name": f"n{k}"} for k, i in enumerate(ids)]
    graph.append({"@id": REFS, "@type": "CreativeWork", "hasPart": [{"@id": i} for i in ids]})
    return {"@context": V.context(), "@graph": graph}


def chunks(ids, size=1500):
    return [ids[b:b + size] for b in range(0, len(ids), size)]


def unread(ids):
    """[(id, why)] for each of `ids` the expansion refuses to read."""
    out = []
    for i in ids:
        try:
            p4_expand.iri_of_id(i)
        except p4_expand.ExpandError as x:
            out.append((i, str(x)))
    return out


def collisions(ids):
    """{IRI: [ids]} for each IRI the expansion makes of more than one of `ids` (those it refuses are left out)."""
    made = {}
    for i in ids:
        try:
            made.setdefault(p4_expand.iri_of_id(i), []).append(i)
        except p4_expand.ExpandError:
            continue
    return {iri: found for iri, found in made.items() if len(found) > 1}
