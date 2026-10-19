"""The string spellings, the path rule, the @id rule and absolute(), each held to a statement of its rule, over
every string one change from their examples here: each substitution of a character, each deletion, and each
insertion (P0's verifier, round 4, R4-2: a pattern made a wildcard, a class made wider or a device list made
shorter passed every whole-string example).

What it holds, and no more:
  - the spellings size, digest, commit, rational, binary64, time, date, text and iri. A test holds that list to
    the string spellings in qro/vocabulary.py's SPELLINGS: `integer` and `ref` are not strings, and `slot` holds
    none;
  - the characters a change may bring: the 95 printable ASCII characters; every C0 and C1 control character, and
    DEL; the surrogates' edges, U+D800, U+DBFF, U+DC00 and U+DFFF; and U+00A0, U+00E9, U+0662, U+FF12, U+2028,
    U+3000 and one astral character, U+1F600 (round 5, R5-1: twelve characters left 53 controls untried);
  - the strings within one change of the examples here. A rule that departs from its statement only further
    away passes.
The statements are written from the rules' prose, in qro/vocabulary.py's SPELLINGS and FORMAT.md items 11 and 22,
without the patterns qro/spelling.py uses. Two lean on the code, and say so: binary64's decimal is compared with
qro/spelling.py's exact_decimal, which tests/format/test_spelling.py holds to nine values of cft-fp256's; and
text's white space at either end is Python's str.strip, as the prose says.
"""
import math
import string
import struct
import unicodedata
from datetime import date, datetime

import pytest

from qro import reader
from qro import spelling as S
from qro import vocabulary as V

DIGITS, HEX, MAX = set(string.digits), set("0123456789abcdef"), 2**63 - 1
LETTERS = set(string.ascii_letters)
SEGMENT = LETTERS | DIGITS | set("._~!$&'()+,;=@-")
DEVICES = {"con", "prn", "aux", "nul", "conin$", "conout$"} | {f"com{i}" for i in range(10)} | {f"lpt{i}" for i in
                                                                                             range(10)}
PRINTABLE = [chr(c) for c in range(0x20, 0x7f)]
ODD = ([chr(c) for c in range(0x00, 0x20)] + [chr(c) for c in range(0x7f, 0xa0)]
       + [chr(c) for c in (0xD800, 0xDBFF, 0xDC00, 0xDFFF, 0xA0, 0xE9, 0x662, 0xFF12, 0x2028, 0x3000, 0x1F600)])


def is_digits(s, n=None):
    return s != "" and set(s) <= DIGITS and (n is None or len(s) == n)


def size(v):
    return is_digits(v) and (v == "0" or v[0] != "0") and int(v) <= MAX


def digest(v, n=64):
    return len(v) == n and set(v) <= HEX


def rational(v):
    if v == "0/1":
        return True
    if v.count("/") != 1:
        return False
    n, d = v.split("/")
    n = n[1:] if n.startswith("-") else n
    if not (is_digits(n) and is_digits(d)) or n[0] == "0" or d[0] == "0" or len(n) > 1000 or len(d) > 1000:
        return False
    return math.gcd(int(n), int(d)) == 1


def binary64(v):
    if v.count(" ") != 1:
        return False
    bits, dec = v.split(" ")
    if not digest(bits, 16):
        return False
    x = struct.unpack(">d", int(bits, 16).to_bytes(8, "big"))[0]
    return x == x and dec == S.exact_decimal(int(bits, 16))


def time(v):
    if len(v) < 20 or v[-1] != "Z" or [v[i] for i in (4, 7, 10, 13, 16)] != ["-", "-", "T", ":", ":"]:
        return False
    fields = [v[0:4], v[5:7], v[8:10], v[11:13], v[14:16], v[17:19]]
    frac = v[19:-1]
    if not all(is_digits(f) for f in fields) or (frac and (frac[0] != "." or not is_digits(frac[1:])
                                                             or frac[-1] == "0")):
        return False
    try:
        datetime(*map(int, fields))
    except ValueError:
        return False
    return True


def day(v):
    if len(v) != 10 or v[4] != "-" or v[7] != "-" or not all(is_digits(f) for f in (v[:4], v[5:7], v[8:])):
        return False
    try:
        date(int(v[:4]), int(v[5:7]), int(v[8:]))
    except ValueError:
        return False
    return True


def text(v):
    return v != "" and v == v.strip() and all(c == "\n" or unicodedata.category(c) not in ("Cc", "Cs") for c in v)


def iri(v):
    scheme, colon, tail = v.partition(":")
    return (bool(colon) and len(scheme) >= 2 and scheme[0] in LETTERS
            and set(scheme[1:]) <= LETTERS | DIGITS | {"+", "-"} and tail != "" and all("!" <= c <= "~" for c in tail))


IRI_CHARS = LETTERS | DIGITS | set("._~!$&'()*+,;=:@/?-")        # a fragment's, and an absolute IRI's but its #
HEXES = set("0123456789abcdefABCDEF")
LOWER = set(string.ascii_lowercase)


def escaped(s):
    """`s` holds IRI_CHARS and escapes only, each % followed by two hex digits."""
    i = 0
    while i < len(s):
        if s[i] == "%" and len(s[i + 1:i + 3]) == 2 and set(s[i + 1:i + 3]) <= HEXES:
            i += 3
        elif s[i] in IRI_CHARS:
            i += 1
        else:
            return False
    return True


def an_id(v):
    """FORMAT.md item 22: ./; a fragment, of RFC 3986's characters but brackets, each % beginning an escape of two
    hex digits, and holding no ://; an absolute IRI, its scheme lowercase, two characters or more with no dot, and
    neither file nor a prefix of the context, its tail of the same characters and escapes with one # at most; or a
    path, no segment empty, . or .., none @ first, a directory's ending in /, and its last segment, the text after
    its final /, neither ending at its first ; nor beginning .; or ..;."""
    if v == "./":
        return True
    if v.startswith("#"):
        return len(v) > 1 and escaped(v[1:]) and "://" not in v
    scheme, colon, tail = v.partition(":")
    if colon and len(scheme) >= 2 and scheme[0] in LOWER and set(scheme[1:]) <= LOWER | DIGITS | {"+", "-"}:
        return (tail != "" and tail.count("#") <= 1 and all(escaped(t) for t in tail.split("#"))
                and scheme != "file" and scheme not in V.CONTEXT_PREFIXES)
    body = v[:-1] if v.endswith("/") else v
    head, semi, params = v.split("/")[-1].partition(";")
    return (body != "" and not v.startswith("@") and not (semi and (params == "" or head in (".", "..")))
            and all(s not in ("", ".", "..") and set(s) <= SEGMENT for s in body.split("/")))


def path(v):
    for seg in v.split("/"):
        if (seg == "" or len(seg) > 255 or not set(seg) <= SEGMENT or seg in (".", "..") or seg.endswith(".")
                or seg.lower().split(".", 1)[0] in DEVICES):
            return False
    return True


RULES = {   # name: (the rule under test, its statement, seed examples)
    "size": (lambda v: S.problem("size", v) is None, size, ["0", "23", "9223372036854775807", "1234567890"]),
    "digest": (lambda v: S.problem("digest", v) is None, digest, ["0123456789abcdef" * 4]),
    "commit": (lambda v: S.problem("commit", v) is None, lambda v: digest(v, 40), ["0123456789abcdef" * 2 + "01234567"]),
    "rational": (lambda v: S.problem("rational", v) is None, rational, ["0/1", "1/3", "-1/2", "85/273", "-987654321/2"]),
    "binary64": (lambda v: S.problem("binary64", v) is None, binary64,
                 [S.binary64(x) for x in (0.5, -2.5, 0.0, float("inf"), 123456789.0)]),
    "time": (lambda v: S.problem("time", v) is None, time,
             ["2026-10-14T10:26:13Z", "2026-10-14T10:26:13.5Z", "1987-06-25T23:59:40.123456789Z"]),
    "date": (lambda v: S.problem("date", v) is None, day, ["2026-10-14", "1987-06-25", "2034-11-30"]),
    "text": (lambda v: S.problem("text", v) is None, text, ["a name", "two\nlines", "café — x"]),
    "iri": (lambda v: S.problem("iri", v) is None, iri, ["https://w3id.org/ro/crate/1.3", "urn:x", "a+b-c9:!~"]),
    "absolute": (reader.absolute, iri, ["https://w3id.org/ro/crate/1.3", "urn:x", "c:x", "a.b:x", "notes.txt:x"]),
    "id": (lambda v: S.id_problem(v) is None, an_id, ["./", "data/x.json", "#frag", "a!~b", "data/run1/", "x",
                                                    "#a:b/c?d", "urn:x", "https://w3id.org/ro/crate/1.3",
                                                    "ab:x", "a@b/c", "#a%20b", "a;b", ";x", "x;;", "#a:/b",
                                                    "a/.;x", "a/..;x", "a;/", "urn:a%2Fb", "ab:x#y", "ab:#",
                                                    "#a%41"]),
    "path": (lambda v: S.path_problem(v) is None, path,
             ["data/x.txt", "a/b.c", "data/a!$&'()+,;=@~-_.b", "data/CON.txt", "data/aux", "data/com1", "data/lpt9.x",
              "data/conin$", "data/conout$.y", "prn", "nul.json", "data/com", "data/lpt", "data/con-x", "x."]),
}


def test_the_sweep_takes_every_string_spelling_the_table_has():
    assert {k for k in RULES if k in V.SPELLINGS} == set(V.SPELLINGS) - {"integer", "ref", "slot"}


def changes(v, alphabet):
    """Every string one substitution, one deletion or one insertion away from `v`, over `alphabet`."""
    for i in range(len(v)):
        yield v[:i] + v[i + 1:]
        for c in alphabet:
            yield v[:i] + c + v[i + 1:]
    for i in range(len(v) + 1):
        for c in alphabet:
            yield v[:i] + c + v[i:]


@pytest.mark.parametrize("name", sorted(RULES))
def test_every_change_to_an_example_gets_the_verdict_the_rule_states(name):
    rule, statement, seeds = RULES[name]
    for seed in seeds:
        assert rule(seed) == statement(seed), (name, seed)
    wrong = []
    for seed in seeds:
        for v in changes(seed, PRINTABLE + ODD):
            if rule(v) != statement(v):
                wrong.append(v)
    assert wrong == [], (name, len(wrong), [ascii(v) for v in wrong[:10]])


def test_every_device_name_is_refused_in_every_segment_and_case():
    """Round 4: COM2 to COM8 and LPT2 to LPT8 were held by no example."""
    for dev in sorted(DEVICES):
        for name in (dev, dev.upper(), dev.capitalize(), dev + ".txt", dev.upper() + ".tar.gz"):
            for p in (name, f"data/{name}", f"data/{name}/x.txt", f"{name}/x"):
                assert S.path_problem(p) is not None, p


@pytest.mark.parametrize("near", ["cox", "aux1.txt", "com10", "lpt", "conin", "conout$x", "nul_", "a-con", "comx.txt",
                                  "lpta", "prn1", "con-notes.txt"])
def test_a_name_near_a_device_is_not_one(near):
    assert S.path_problem(f"data/{near}") is None and S.path_problem(near) is None
