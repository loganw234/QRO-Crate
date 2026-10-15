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
# Text: no control character but the line feed (C0, DEL and C1: Unicode's category Cc), and no lone surrogate.
_TEXT_BAD = re.compile(r"[\x00-\x09\x0b-\x1f\x7f-\x9f\ud800-\udfff]")


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
    """The one spelling of an aware datetime, in UTC."""
    if dt.tzinfo is None or dt.utcoffset().total_seconds() != 0:
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
        return None if isinstance(value["@id"], str) and _ID.fullmatch(value["@id"]) else "not an @id spelling"
    if not isinstance(value, str):
        return "not a string"
    if spelling == "size":
        ok = _DECIMAL.fullmatch(value) and len(value) <= 19 and int(value) <= MAX
        return None if ok else "not a decimal byte count of at most 2^63 - 1"
    if spelling == "digest":
        return None if _HEX64.fullmatch(value) else "not 64 lowercase hex digits"
    if spelling == "commit":
        return None if _HEX40.fullmatch(value) else "not 40 lowercase hex digits"
    if spelling == "rational":
        if not _RATIONAL.fullmatch(value):
            return "not N/D in decimal"
        n, d = value.split("/")
        if len(n.lstrip("-")) > TERM_DIGITS or len(d) > TERM_DIGITS:
            return f"a term of more than {TERM_DIGITS} digits"
        return None if gcd(abs(int(n)), int(d)) == 1 else "not in lowest terms"
    if spelling == "binary64":
        m = _BINARY64.fullmatch(value)
        if not m:
            return "not 16 hex digits, a space and a decimal"
        try:
            return None if exact_decimal(int(m.group(1), 16)) == m.group(2) else "the decimal is not the bits' exact one"
        except ValueError:
            return "a NaN"
    if spelling == "time":
        m = _TIME.fullmatch(value)
        if not m:
            return "not RFC 3339 UTC, with Z and no trailing zero in a fraction"
        try:
            datetime(*(int(m.group(i)) for i in range(1, 7)))
        except ValueError:
            return "not a real time"
        return None
    if spelling == "date":
        if not _DATE.fullmatch(value):
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
        return None if IRI.fullmatch(value) else "not an absolute IRI"
    if spelling == "slot":
        return "a value in a slot this profile version leaves empty"
    if spelling.startswith("word:"):
        return None if value in V.WORDS[spelling[5:]] else f"not one of {sorted(V.WORDS[spelling[5:]])}"
    raise KeyError(spelling)


def id_problem(value):
    """None if `value` is an @id's spelling."""
    return None if isinstance(value, str) and _ID.fullmatch(value) else "an @id is printable ASCII with no space"


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
