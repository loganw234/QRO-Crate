"""Each spelling in qro/vocabulary.py's SPELLINGS, held to its one rule, and the writers that make it.

A value has one spelling, and a reader refuses any other, including one that denotes the same value (cft-fp256,
docs/CERTIFICATES.md:175-227, READ). Departure from cft-fp256, stated: a rational is written in decimal, not hex,
since QRO-Crate's rationals are a law's probabilities, which a person reads. Stdlib only.
"""
import re
import struct
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction
from math import gcd

from qro import vocabulary as V

MAX = 2**63 - 1
TERM_DIGITS = 1000            # a rational's numerator and denominator each have at most this many digits
# Every pattern is ASCII: in Python, \d and \S match any Unicode digit or non-space, and int() reads Unicode
# digits, so "٢٠..." would be a second spelling of a time (P0's verifier, P0-1).
_DECIMAL = re.compile(r"(0|[1-9][0-9]*)", re.ASCII)
_HEX64 = re.compile(r"[0-9a-f]{64}", re.ASCII)
_HEX40 = re.compile(r"[0-9a-f]{40}", re.ASCII)
_RATIONAL = re.compile(r"0/1|-?[1-9][0-9]*/[1-9][0-9]*", re.ASCII)
_BINARY64 = re.compile(r"([0-9a-f]{16}) ([!-~]+)", re.ASCII)
_TIME = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(\.[0-9]*[1-9])?Z", re.ASCII)
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", re.ASCII)
# An IRI's scheme, here and in the reader's absolute(): two characters or more, and no dot, so that neither a drive
# letter (C:/x) nor a file's NTFS stream (notes.txt:hidden) reads as one (P0's verifier, rounds 2 and 3).
SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+-]+", re.ASCII)
IRI = re.compile(SCHEME.pattern + r":[!-~]+", re.ASCII)    # the `iri` spelling, and the reader's absolute()
_ID = re.compile(r"[!-~]+", re.ASCII)            # printable ASCII, no space: so the graph's order is byte order
# A file's @id is its path in the crate: segments of RFC 3986's unreserved characters and sub-delimiters but "*",
# which Windows refuses in a name, and @, joined by "/". No ":" (a drive, or an NTFS stream), no "%" (an
# encoding), no "#", "?", "\", space or other.
_SEGMENT = re.compile(r"[A-Za-z0-9._~!$&'()+,;=@-]+", re.ASCII)
SEGMENT_MAX = 255             # the longest name NTFS, ext4 and APFS each hold
# An @id, and a reference's, is one spelling of the IRI it names (P0.5; P4's verifier, round 1, defect 1): the
# root ./; a path in the crate, a directory's ending in /, of the path's characters, with no empty or dot segment
# and no @ first; a fragment #...; or an absolute IRI whose scheme is lowercase, two characters or more with no
# dot, and neither a prefix of the context nor file. A fragment and an absolute IRI hold RFC 3986's characters but
# [ and ], each % beginning an escape of two hex digits, and an absolute IRI one # at most: so no accepted id is
# one urllib's urlsplit raises on, as on an unbalanced bracket, which broke rdflib's defrag and its RDF/XML reader
# with a base (P0.5's verifier, round 2, note 4). A JSON-LD reader reads many other forms otherwise, so two
# entities the checker holds apart would be one node in RDF, or a blank one, or none (MEASURED, rdflib 7.6.0 under
# the base file:///crate/): _:b0 is a blank node; @x, @x/y, ., ././, // and ? are the root; ./x is x, ./#a is #a,
# and a? is a; a//b and a/./b are a/b; /x and ../a lie outside the crate, and //x is another host; schema:a is
# http://schema.org/a; file:///crate/a is the path a; and an id holding a space makes no node. Others it reads as
# written (x#a, #, ?q, HTTPS://x/y, C:/x, ab:%zz), and they are refused as forms the rule does not offer, so that
# an IRI has one spelling. Two shapes inside the forms are refused too, each read otherwise by rdflib (P0.5's
# verifier, round 1, MEASURED): a fragment holding ://, which rdflib leaves as written, a relative IRI, at every
# base; and a path whose last segment, the text after its final / (empty for a directory), ends at its first ;
# or begins .; or ..;. rdflib resolves with urllib's urljoin, which at an http, https, ftp or like base splits ;params
# off the last segment, drops them when empty, and reads a . or .. before them as a dot segment: x; is x, and ;
# the root. Other params it keeps, so a;b.txt is accepted. These patterns are not in PATTERNS: a shape sees an @id
# resolved, as an IRI, never its spelling.
_ID_SEGMENT = r"(?![.]{1,2}(?:/|$))[A-Za-z0-9._~!$&'()+,;=@-]+"
_PATH_ID = re.compile(rf"(?!@){_ID_SEGMENT}(?:/{_ID_SEGMENT})*/?", re.ASCII)
_IRI_CHAR = r"(?:[A-Za-z0-9._~!$&'()*+,;=:@/?-]|%[0-9A-Fa-f]{2})"   # a fragment's, a query's or a path's
_FRAGMENT_ID = re.compile(rf"#{_IRI_CHAR}+", re.ASCII)
_ABSOLUTE_ID = re.compile(rf"([a-z][a-z0-9+-]+):(?:{_IRI_CHAR}+(?:#{_IRI_CHAR}*)?|#{_IRI_CHAR}*)", re.ASCII)
# Text: no control character but the line feed (C0, DEL and C1: Unicode's category Cc), and no lone surrogate.
_TEXT_BAD = re.compile(r"[\x00-\x09\x0b-\x1f\x7f-\x9f\ud800-\udfff]")
# Each spelling's pattern, for those that have one: a value must match it whole, and problem() holds the
# rest (a size's bound, a rational's lowest terms, a binary64's exact decimal, a real time or date). P4's
# shapes are to read these, so that no pattern is written twice (P4's design, R-C; P0.3).
PATTERNS = {"size": _DECIMAL, "digest": _HEX64, "commit": _HEX40, "rational": _RATIONAL, "binary64": _BINARY64,
            "time": _TIME, "date": _DATE, "iri": IRI}


def exact_decimal(bits):
    """A binary64's exact decimal, in cft-fp256's one spelling. Refuses a NaN."""
    x = struct.unpack(">d", bits.to_bytes(8, "big"))[0]
    if x != x:
        raise ValueError("a NaN has no spelling")
    if x == 0:
        return "-0" if bits >> 63 else "0"
    if x in (float("inf"), float("-inf")):
        return "inf" if x > 0 else "-inf"
    sign, digits, exp = Decimal(x).as_tuple()
    digits = list(digits)
    while digits[-1] == 0:
        digits.pop()
        exp += 1
    weight = exp + len(digits) - 1
    head = str(digits[0]) + ("." + "".join(map(str, digits[1:])) if len(digits) > 1 else "")
    return ("-" if sign else "") + f"{head}e{'+' if weight >= 0 else '-'}{abs(weight)}"


def binary64(x):
    """The one spelling of a float."""
    bits = int.from_bytes(struct.pack(">d", x), "big")
    return f"{bits:016x} {exact_decimal(bits)}"


def rational(q):
    """The one spelling of a Fraction (or an int)."""
    q = Fraction(q)
    return f"{q.numerator}/{q.denominator}"


def time(dt):
    """The one spelling of an aware datetime, in UTC; ValueError for any other."""
    offset = dt.utcoffset() if dt.tzinfo is not None else None
    if offset is None or offset.total_seconds() != 0:
        raise ValueError("a time is written in UTC")
    s = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}T{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"   # not strftime:
    # glibc's %Y leaves a year below 1000 unpadded (P0's verifier, round 5)
    if dt.microsecond:
        s += ("." + f"{dt.microsecond:06d}").rstrip("0")
    return s + "Z"


def problem(spelling, value):
    """None if `value` is in `spelling`'s one form; otherwise why not, in a few words."""
    if spelling == "integer":
        if type(value) is not int or not 0 <= value <= MAX:
            return "not a non-negative integer of at most 2^63 - 1"
        return None
    if spelling == "ref":
        if not isinstance(value, dict) or list(value) != ["@id"]:
            return 'not a reference {"@id": ...} and nothing else'
        return None if id_problem(value["@id"]) is None else "not an @id spelling"
    if not isinstance(value, str):
        return "not a string"
    if spelling == "size":
        ok = PATTERNS["size"].fullmatch(value) and len(value) <= 19 and int(value) <= MAX
        return None if ok else "not a decimal byte count of at most 2^63 - 1"
    if spelling == "digest":
        return None if PATTERNS["digest"].fullmatch(value) else "not 64 lowercase hex digits"
    if spelling == "commit":
        return None if PATTERNS["commit"].fullmatch(value) else "not 40 lowercase hex digits"
    if spelling == "rational":
        if not PATTERNS["rational"].fullmatch(value):
            return "not N/D in decimal"
        n, d = value.split("/")
        if len(n.lstrip("-")) > TERM_DIGITS or len(d) > TERM_DIGITS:
            return f"a term of more than {TERM_DIGITS} digits"
        return None if gcd(abs(int(n)), int(d)) == 1 else "not in lowest terms"
    if spelling == "binary64":
        m = PATTERNS["binary64"].fullmatch(value)
        if not m:
            return "not 16 hex digits, a space and a decimal"
        try:
            return None if exact_decimal(int(m.group(1), 16)) == m.group(2) else "the decimal is not the bits' exact one"
        except ValueError:
            return "a NaN"
    if spelling == "time":
        m = PATTERNS["time"].fullmatch(value)
        if not m:
            return "not RFC 3339 UTC, with Z and no trailing zero in a fraction"
        try:
            datetime(*(int(m.group(i)) for i in range(1, 7)))
        except ValueError:
            return "not a real time"
        return None
    if spelling == "date":
        if not PATTERNS["date"].fullmatch(value):
            return "not YYYY-MM-DD"
        try:
            date.fromisoformat(value)
        except ValueError:
            return "not a real date"
        return None
    if spelling == "text":
        if not value or value != value.strip():
            return "empty, or with space at an end"
        return "a control character other than a line feed, or a lone surrogate" if _TEXT_BAD.search(value) else None
    if spelling == "iri":
        return None if PATTERNS["iri"].fullmatch(value) else "not an absolute IRI"
    if spelling == "slot":
        return "a value in a slot this profile version leaves empty"
    if spelling.startswith("word:"):
        return None if value in V.WORDS[spelling[5:]] else f"not one of {sorted(V.WORDS[spelling[5:]])}"
    raise KeyError(spelling)


def id_problem(value):
    """None if `value` is an @id's spelling: printable ASCII with no space, in one of the four forms above, and
    neither of the two shapes inside them that a JSON-LD reader reads otherwise."""
    if not isinstance(value, str) or not _ID.fullmatch(value):
        return "an @id is printable ASCII with no space"
    if value == V.ROOT:
        return None
    if _FRAGMENT_ID.fullmatch(value):
        return "a fragment holding ://, which a JSON-LD reader leaves a relative IRI" if "://" in value else None
    if _PATH_ID.fullmatch(value):
        head, semi, params = value.rsplit("/", 1)[-1].partition(";")
        if semi and (params == "" or head in (".", "..")):
            return ("a last segment whose first ; ends it, or which begins .; or ..;: at an http base a JSON-LD "
                    "reader reads x; as x, and ; as the root")
        return None
    m = _ABSOLUTE_ID.fullmatch(value)
    if m is None:
        return ("an @id is ./, a path with no empty or dot segment and no @ first, #..., or an absolute IRI with a "
                "lowercase scheme, and no other form (FORMAT.md item 22)")
    if m.group(1) in V.CONTEXT_PREFIXES:
        return f"a compact IRI, {m.group(1)}: being a prefix of the context: a second spelling of another IRI"
    if m.group(1) == "file":
        return "a file: IRI, which a reader cannot tell from a path in the crate"
    return None


# A device's name, with or without an extension, in any case: the names Windows reserves (CON, PRN, AUX, NUL,
# COM1-COM9, LPT1-LPT9), and four it treats as devices in some places (COM0, LPT0, CONIN$, CONOUT$): a safe superset
# (P0's verifier, rounds 2 and 3).
_DEVICE = re.compile(r"(?i)(con|prn|aux|nul|com[0-9]|lpt[0-9]|conin\$|conout\$)(\..*)?", re.ASCII)


def path_problem(value):
    """None if `value` is a file's @id: its path in the crate, the same file on every host (P0's verifier, P0-4
    and P0-5, and round 2). Segments of unreserved characters, sub-delimiters but *, and @, joined by /; none
    empty, none longer than SEGMENT_MAX, none . or .., none ending in a dot, and none a name Windows reserves for a
    device."""
    for seg in value.split("/"):
        if not _SEGMENT.fullmatch(seg):
            return f"a path segment {seg!r} outside A-Z a-z 0-9 . _ ~ ! $ & ' ( ) + , ; = @ -, or empty"
        if len(seg) > SEGMENT_MAX:
            return f"a path segment of {len(seg)} characters: a name holds at most {SEGMENT_MAX}"
        if seg in (".", "..") or seg.endswith("."):
            return f"a path segment {seg!r}: . or .., or ending in a dot"
        if _DEVICE.fullmatch(seg):
            return f"a path segment {seg!r}: a name Windows reserves for a device"
    return None
