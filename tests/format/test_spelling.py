"""Each spelling's examples, accepted and refused, walked both ways, and its writers (study QRO-0, section 9: one
spelling per value). tests/format/test_sweep.py holds the string spellings to statements of their rules over
strings one change from its own examples, over the characters its docstring lists."""
import re
from datetime import datetime, timezone
from fractions import Fraction

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
    "ref": [{"@id": PRINTABLE}],
}


@pytest.mark.parametrize("spelling", sorted(CLASS_ACCEPTED))
def test_every_character_a_spelling_admits_is_in_an_accepted_value(spelling):
    for v in CLASS_ACCEPTED[spelling]:
        assert S.problem(spelling, v) is None, (spelling, str(v)[:80])


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
