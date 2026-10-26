"""P1's raw forms and its snapshot form: each reader on good bytes, and on hostile ones. A hostile file is a
refusal, never a crash (FORMAT.md, item 16): every shape below is refused as a RawFormError (a SnapshotError for a
snapshot) and nothing else escapes, a seeded sweep of single-byte corruptions and truncations asserts the same, and
the checker's step 3 turns each into `raw-form`. What a reader will inflate is bounded by its header and by a cap,
shown with a stream that would fill memory."""
import base64
import copy
import json
import math
import random
import re
import sys
import tracemalloc
import zlib
from datetime import timezone

import pytest
from p1_builder import (ATLAS_FORM, IBM_FORM, KA, VECTOR_FORM, at, atlas_result, atlas_vector, ibm_doc, ibm_model,
                        known_answer_rows, npy, outcome, packed, raw_ibm, read_md, snapshot_bytes, snapshot_doc,
                        zoneless)

from qro import checker, p1_forms
from qro.checker import RawFormError
from qro.p1_forms import SnapshotError
from qro.refusal import Refused

ECHO = "ab" * 32
ROWS = known_answer_rows(40)
SPAN = (at(10, 27, 0, 285375), at(10, 27, 1, 376976))


def good():
    return ibm_doc([ROWS, ROWS], [ECHO, None], SPAN)


def dumps(doc):
    return json.dumps(doc).encode("utf-8")


def mutated(fn):
    doc = copy.deepcopy(good())
    fn(doc)
    return dumps(doc)


def value(doc):
    return doc["__value__"]


def pub(doc, i=0):
    return doc["__value__"]["pub_results"][i]["__value__"]


def meas(doc, i=0):
    return pub(doc, i)["data"]["__value__"]["fields"]["meas"]["__value__"]


def span(doc):
    return doc["__value__"]["metadata"]["execution"]["execution_spans"]["__value__"]["spans"][0]["__value__"]


def with_array_text(text):
    """A one-PUB result whose array holds `text`: the array is the only fault, and no second PUB's row count can
    refuse it first."""
    doc = ibm_doc([ROWS], [ECHO], SPAN)
    meas(doc)["array"]["__value__"] = text
    return dumps(doc)


def with_npy(raw):
    return with_array_text(packed(raw))


# -- IBM's sampler result, good ---------------------------------------------------------------------------------------
def test_a_good_result_is_read_whole():
    r = p1_forms.parse_ibm_result(dumps(good()))
    assert (r.shots, len(r.pubs)) == (40, 2)
    assert [p.rows for p in r.pubs] == [40, 40] and [p.echo for p in r.pubs] == [ECHO, None]
    assert r.pubs[0].body == b"".join(v.to_bytes(2, "big") for v in ROWS)
    assert r.spans == ((SPAN[0], SPAN[1]),) and r.first_shot == SPAN[0] and r.last_shot == SPAN[1]
    assert r.first_shot.tzinfo is timezone.utc


def test_a_result_with_no_span_or_echo_is_read_and_says_so():
    doc = ibm_doc([ROWS], [None])
    r = p1_forms.parse_ibm_result(dumps(doc))
    assert (r.spans, r.first_shot, r.last_shot, r.pubs[0].echo) == ((), None, None, None)
    del value(doc)["metadata"]
    del pub(doc)["metadata"]
    assert p1_forms.parse_ibm_result(dumps(doc)).spans == ()


def test_the_span_is_the_earliest_start_and_the_latest_stop_of_many():
    doc = good()
    spans = value(doc)["metadata"]["execution"]["execution_spans"]["__value__"]["spans"]
    later = copy.deepcopy(spans[0])
    later["__value__"]["start"]["__value__"] = zoneless(at(10, 27, 0, 100))
    later["__value__"]["stop"]["__value__"] = zoneless(at(10, 27, 5))
    spans.append(later)
    r = p1_forms.parse_ibm_result(dumps(doc))
    assert (r.first_shot, r.last_shot) == (at(10, 27, 0, 100), at(10, 27, 5))


def test_shots_are_the_rows_never_a_number_beside_them():
    """The reader counts rows; a document that states shots anywhere is not asked."""
    doc = good()
    pub(doc)["metadata"]["shots"] = 999999
    value(doc)["metadata"]["shots"] = 12
    assert p1_forms.parse_ibm_result(dumps(doc)).shots == 40


def test_the_rows_are_ones_array_and_a_big_endian_pair_of_bytes():
    r = p1_forms.parse_ibm_result(raw_ibm([[outcome(KA), 1, 256]], [None]))
    assert r.pubs[0].body == bytes([0x10, 0x8B, 0x00, 0x01, 0x01, 0x00])


def test_a_span_that_stops_when_it_starts_is_a_span():
    doc = good()
    span(doc)["stop"]["__value__"] = span(doc)["start"]["__value__"]
    r = p1_forms.parse_ibm_result(dumps(doc))
    assert r.first_shot == r.last_shot == SPAN[0]


# -- IBM's sampler result, hostile ---------------------------------------------------------------------------------------
def deep(n):
    return b"[" * n + b"]" * n


# A key twice in an object, in a document valid in every other way: the repeated key is the only fault, so only the
# strict parse can refuse it (a document broken elsewhere is refused whatever the parse does with its keys).
TWICE = {"the result": (p1_forms.parse_ibm_result, dumps(good()), b'"num_bits": 16', b'"num_bits": 16, "num_bits": 16'),
         "an Atlas result": (p1_forms.parse_atlas_result, atlas_result({(0, 1, 2): 3}), b'"status": 200',
                             b'"status": 200, "status": 200'),
         "the vector": (p1_forms.parse_atlas_vector, atlas_vector(), b'"job": "synthetic-vector"',
                        b'"job": "synthetic-vector", "job": "synthetic-vector"')}


@pytest.mark.parametrize("what", TWICE)
def test_a_key_twice_in_an_otherwise_valid_document_is_refused(what):
    parse, data, old, new = TWICE[what]
    parse(data)
    assert old in data
    with pytest.raises(RawFormError, match="twice"):
        parse(data.replace(old, new, 1))


@pytest.mark.parametrize("what, old, new", [
    ("NaN", b'"num_bits": 16', b'"num_bits": 16, "x": NaN'), ("an infinity", b'"num_bits": 16', b'"num_bits": 16, "x": Infinity'),
    ("a number past binary64", b'"num_bits": 16', b'"num_bits": 16, "x": 1e999')])
def test_a_constant_or_a_number_past_binary64_in_an_otherwise_valid_document_is_refused(what, old, new):
    data = dumps(good())
    with pytest.raises(RawFormError):
        p1_forms.parse_ibm_result(data.replace(old, new))


@pytest.mark.parametrize("token, said", [(b"NaN", "NaN has no value"), (b"Infinity", "Infinity has no value"),
                                         (b"-Infinity", "-Infinity has no value"), (b"1e999", "past binary64"),
                                         (b"-1e999", "past binary64")])
def test_a_constant_or_a_number_past_binary64_where_any_value_would_do_is_refused_for_that(token, said):
    """A free place in the document, which takes any value: the constant is the only fault, so only the parse refuses
    it (read as null, or as a float, it would be accepted)."""
    doc = good()
    value(doc)["metadata"]["note"] = 12345678
    data = dumps(doc)
    assert p1_forms.parse_ibm_result(data).shots == 40
    with pytest.raises(RawFormError, match=said):
        p1_forms.parse_ibm_result(data.replace(b'"note": 12345678', b'"note": ' + token))
    atlas = atlas_result({(0, 1, 2): 3})
    assert p1_forms.parse_atlas_result(atlas).shots == 3
    assert b"-0.0009765625" in atlas
    with pytest.raises(RawFormError, match=said):
        p1_forms.parse_atlas_result(atlas.replace(b"-0.0009765625", token))


@pytest.mark.parametrize("numeral, want", [("1e-999", 0.0), ("-1e-999", -0.0), ("1e-324", 0.0), ("5e-324", 5e-324),
                                           ("2.5e-324", 5e-324), ("1e-400", 0.0), ("0.0", 0.0), ("-0.0", -0.0)])
def test_a_float_that_underflows_is_read_as_zero_and_only_an_overflow_is_refused(numeral, want):
    """The verifier's note of round 3: `no float past binary64` held for overflow only. A numeral too small for binary64 is
    read by Python's own float() as 0.0 (or -0.0, or the least subnormal), in every reader that has a place for a float:
    the snapshot's parse, the IBM result's free place and the Atlas result's observables. One too big is refused (above)."""
    for error in (RawFormError, SnapshotError):
        got = p1_forms.load_json(b'{"a": ' + numeral.encode() + b"}", "x", error)["a"]
        assert got == want and math.copysign(1.0, got) == math.copysign(1.0, want)
    doc = good()
    value(doc)["metadata"]["note"] = 12345678
    data = dumps(doc)
    assert p1_forms.parse_ibm_result(data.replace(b'"note": 12345678', b'"note": ' + numeral.encode())).shots == 40
    atlas = atlas_result({(0, 1, 2): 3})
    assert p1_forms.parse_atlas_result(atlas.replace(b"-0.0009765625", numeral.encode())).shots == 3


def test_a_value_error_the_parser_raises_for_a_number_it_will_not_convert_is_a_refusal_too(monkeypatch):
    """CPython refuses an integer of more than 4,300 digits with a ValueError unless the host has lifted the limit
    (PYTHONINTMAXSTRDIGITS). Since round 2 an integer is held before it is converted, so no input is known to reach this
    clause; it holds the contract that a reader raises only its own error, whatever the parser does: the parser is made
    to raise a ValueError of its own."""
    def refuses(*args, **kwargs):
        raise ValueError("Exceeds the limit (4300 digits) for integer string conversion")
    monkeypatch.setattr(p1_forms.json, "loads", refuses)
    for error in (RawFormError, SnapshotError):
        with pytest.raises(error, match=r"x: not readable \(Exceeds the limit"):
            p1_forms.load_json(b"{}", "x", error)


BOUND = 2**63 - 1                      # the profile's own bound for an `integer`: qro.spelling.MAX


@pytest.mark.parametrize("numeral, read", [
    ("9223372036854775807", True), ("9223372036854775808", False), ("-9223372036854775807", True),
    ("-9223372036854775808", False), ("0", True), ("-0", True), ("1000000000000000000", True),
    ("9999999999999999999", False), ("10000000000000000000", False), ("1" + "0" * 399, False),
    ("-1" + "0" * 399, False), ("9" * 5000, False)],
    ids=["the bound", "one past", "minus the bound", "minus one past", "zero", "minus zero", "10^18", "19 nines",
         "10^19", "10^399", "minus 10^399", "5,000 nines"])
def test_an_integer_is_read_to_2_63_minus_1_on_either_side_of_zero_and_no_further(numeral, read):
    """The verifier's D5 of round 2: `no number past binary64` held for floats only, and counts and shots of 10^400 were
    read. The bound is the profile's, at the bound and one past it, either side of zero, and for a numeral too long for
    Python to convert (4,300 digits), which is refused as the others are, whatever the host's limit."""
    text = b'{"a": ' + numeral.encode() + b"}"
    for error in (RawFormError, SnapshotError):
        if read:
            assert p1_forms.load_json(text, "x", error)["a"] == int(numeral)
        else:
            with pytest.raises(error, match="an integer past 9223372036854775807"):
                p1_forms.load_json(text, "x", error)
    assert BOUND == 9223372036854775807


def test_an_integer_past_the_bound_is_a_refusal_in_every_reader_and_one_at_it_is_read():
    for form, parse, make in (
            ("an IBM result", p1_forms.parse_ibm_result, lambda n: with_note(n)),
            ("an Atlas result", p1_forms.parse_atlas_result, lambda n: tiny_atlas(n, n)),
            ("the vector", p1_forms.parse_atlas_vector, lambda n: tiny_vector(n))):
        assert parse(make(BOUND))
        with pytest.raises(RawFormError, match="an integer past 9223372036854775807"):
            parse(make(BOUND + 1))
    assert p1_forms.parse_atlas_result(tiny_atlas(BOUND, BOUND)).shots == BOUND


def test_a_numeral_past_the_bound_is_refused_as_that_whatever_the_hosts_limit_on_converting_integers_is():
    """The docstring of `_integer`: a numeral of more than nineteen digits is never converted, so the refusal does not depend on
    the host's limit on converting big integers (CPython's default is 4,300 digits; PYTHONINTMAXSTRDIGITS lowers or lifts it).
    The verifier's mutant 25 of round 3, a shortcut at that limit, was equivalent on a host with the default and not on one
    with less; the limit is lowered here to 640, the least CPython allows, and a numeral of 1,000 digits is still refused for
    being past the bound, not for what the parser could not convert."""
    old = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(640)
    try:
        for error in (RawFormError, SnapshotError):
            for numeral in (b"9" * 1000, b"-" + b"9" * 1000, b"1" + b"0" * 639):
                with pytest.raises(error, match="an integer past 9223372036854775807"):
                    p1_forms.load_json(b'{"a": ' + numeral + b"}", "x", error)
    finally:
        sys.set_int_max_str_digits(old)


def with_note(n):
    """An IBM result with a place that takes any value, holding the integer n."""
    doc = good()
    value(doc)["metadata"]["note"] = n
    return dumps(doc)


def tiny_vector(n):
    return json.dumps({"job": "j", "measurements": {"I" * 16: {"counts": {"0" * 16: n}, "shots": n}}}).encode()


def test_load_json_refuses_by_the_error_it_is_given():
    for text, said in ((b'{"a": NaN}', "NaN has no value"), (b'[1, Infinity]', "Infinity has no value"),
                       (b'{"a": 1, "a": 2}', "twice"), (b'{"a": 2e999}', "past binary64"), (b"\xff", "not UTF-8"),
                       (b"{", "not JSON"), (b"[" * 100000, "nested deeper"),
                       (b'{"a": 9223372036854775808}', "an integer past 9223372036854775807")):
        for error in (RawFormError, SnapshotError):
            with pytest.raises(error, match=said):
                p1_forms.load_json(text, "x", error)
    assert p1_forms.load_json(b'{"a": [1, 2.5, "x", null, true]}', "x") == {"a": [1, 2.5, "x", None, True]}


@pytest.mark.parametrize("bits", [0, 1, 8, 15, 17, 18, 32, 64, 1000, 16.0, "16", True, None, [16]])
def test_a_meas_that_is_not_sixteen_bits_wide_is_refused_whichever_side_of_sixteen_it_is(bits):
    """The verifier's note: `num_bits` above 16 was accepted by a mutant, and below was the only side held."""
    doc = good()
    meas(doc)["num_bits"] = bits
    with pytest.raises(RawFormError, match="not 16 bits"):
        p1_forms.parse_ibm_result(dumps(doc))


def test_sixteen_bits_is_the_one_width_read():
    assert p1_forms.parse_ibm_result(dumps(good())).shots == 40


BAD_BYTES = {
    "nothing": b"", "not UTF-8": b"\xff\xfe\x00", "a byte-order mark": b"\xef\xbb\xbf" + dumps(good()),
    "not JSON": b"hello", "a list": b"[]", "a number": b"7", "null": b"null",
    "a key twice": b'{"__type__": "PrimitiveResult", "__type__": "PrimitiveResult", "__value__": {}}',
    "a NaN": b'{"__type__": "PrimitiveResult", "__value__": NaN}',
    "an infinity": b'{"__type__": "PrimitiveResult", "__value__": -Infinity}',
    "a number past binary64": b'{"__type__": "PrimitiveResult", "__value__": 1e999}',
    "nesting past the parser": deep(100000),
    "an integer of 100,000 digits": b'{"__type__": "PrimitiveResult", "__value__": ' + b"9" * 100000 + b"}",
}


@pytest.mark.parametrize("data", BAD_BYTES.values(), ids=BAD_BYTES)
def test_bytes_that_are_no_result_are_refused(data):
    with pytest.raises(RawFormError):
        p1_forms.parse_ibm_result(data)


def spans_of(doc):
    return value(doc)["metadata"]["execution"]["execution_spans"]["__value__"]


def set_start(text):
    return lambda d: span(d)["start"].update({"__value__": text})


def make_wrong(doc):
    pub(doc)["data"]["__value__"]["fields"]["meas"]["__value__"]["array"]["__value__"] = 5


BAD_STRUCTURE = {
    "the wrong top type": lambda d: d.update({"__type__": "Result"}),
    "a third key at the top": lambda d: d.update({"extra": 1}),
    "no __value__": lambda d: d.pop("__value__"),
    "a value that is a list": lambda d: d.update({"__value__": []}),
    "no pub_results": lambda d: value(d).pop("pub_results"),
    "pub_results empty": lambda d: value(d).update({"pub_results": []}),
    "pub_results not a list": lambda d: value(d).update({"pub_results": {}}),
    "an unknown key in the value": lambda d: value(d).update({"extra": 1}),
    "a PUB that is a string": lambda d: value(d)["pub_results"].__setitem__(0, "x"),
    "a PUB of another type": lambda d: value(d)["pub_results"][0].update({"__type__": "PubResult"}),
    "a PUB without data": lambda d: pub(d).pop("data"),
    "a PUB with an unknown key": lambda d: pub(d).update({"extra": 1}),
    "data of another type": lambda d: pub(d)["data"].update({"__type__": "Data"}),
    "field_names that name another field": lambda d: pub(d)["data"]["__value__"].update({"field_names": ["c"]}),
    "no field_names": lambda d: pub(d)["data"]["__value__"].pop("field_names"),
    "a shape that is not empty": lambda d: pub(d)["data"]["__value__"].update({"shape": [2]}),
    "no shape": lambda d: pub(d)["data"]["__value__"].pop("shape"),
    "fields that are a list": lambda d: pub(d)["data"]["__value__"].update({"fields": []}),
    "a second field": lambda d: pub(d)["data"]["__value__"]["fields"].update({"c": {}}),
    "a field that is not meas": lambda d: pub(d)["data"]["__value__"].update(
        {"fields": {"c": pub(d)["data"]["__value__"]["fields"]["meas"]}}),
    "a meas that is not a BitArray": lambda d: pub(d)["data"]["__value__"]["fields"]["meas"].update(
        {"__type__": "Array"}),
    "a BitArray with a third key": lambda d: meas(d).update({"extra": 1}),
    "a BitArray without num_bits": lambda d: meas(d).pop("num_bits"),
    "num_bits 8": lambda d: meas(d).update({"num_bits": 8}),
    "num_bits as a string": lambda d: meas(d).update({"num_bits": "16"}),
    "num_bits as a bool": lambda d: meas(d).update({"num_bits": True}),
    "num_bits 16.0": lambda d: meas(d).update({"num_bits": 16.0}),
    "an array that is not an ndarray": lambda d: meas(d)["array"].update({"__type__": "list"}),
    "an array whose value is a number": make_wrong,
    "an array whose value is a list": lambda d: meas(d)["array"].update({"__value__": []}),
    "an echo that is a number": lambda d: pub(d)["metadata"]["circuit_metadata"].update({"qf_commitment": 5}),
    "metadata that is a list": lambda d: pub(d).update({"metadata": []}),
    "circuit_metadata that is null": lambda d: pub(d)["metadata"].update({"circuit_metadata": None}),
    "PUBs of different row counts": lambda d: value(d)["pub_results"].append(
        copy.deepcopy(value(d)["pub_results"][0])) or meas(d, 2)["array"].update({"__value__": packed(npy(ROWS[:5]))}),
    "result metadata that is a number": lambda d: value(d).update({"metadata": 5}),
    "execution that is a list": lambda d: value(d)["metadata"].update({"execution": []}),
    "execution_spans of another type": lambda d: value(d)["metadata"]["execution"]["execution_spans"].update(
        {"__type__": "Spans"}),
    "no spans": lambda d: spans_of(d).pop("spans"),
    "spans empty": lambda d: spans_of(d).update({"spans": []}),
    "spans not a list": lambda d: spans_of(d).update({"spans": {}}),
    "a span of another type": lambda d: spans_of(d)["spans"][0].update({"__type__": "Span"}),
    "a span without a stop": lambda d: span(d).pop("stop"),
    "a span with a fourth key": lambda d: span(d).update({"extra": 1}),
    "a start of another type": lambda d: span(d)["start"].update({"__type__": "date"}),
    "a start that is a number": lambda d: span(d)["start"].update({"__value__": 5}),
    "a start with a zone": set_start("2026-10-05T10:27:00.285375Z"),
    "a start with an offset": set_start("2026-10-05T10:27:00.285375+00:00"),
    "a start in month 13": set_start("2026-13-05T10:27:00.285375"),
    "a start at a leap second": set_start("2026-10-05T10:27:60"),
    "a start of seven fraction digits": set_start("2026-10-05T10:27:00.2853751"),
    "a start with a space": set_start("2026-10-05 10:27:00"),
    "a start in Arabic-Indic digits": set_start("٢٠٢٦-10-05T10:27:00"),
    "a stop before its start": lambda d: span(d)["stop"].update({"__value__": zoneless(at(10, 26, 0))}),
}


@pytest.mark.parametrize("fn", BAD_STRUCTURE.values(), ids=BAD_STRUCTURE)
def test_a_result_of_another_structure_is_refused(fn):
    with pytest.raises(RawFormError):
        p1_forms.parse_ibm_result(mutated(fn))


def header_of(rows=40, **changes):
    text = "{'descr': '|u1', 'fortran_order': False, 'shape': (%d, 2), }" % rows
    for old, new in changes.items():
        assert old in text, old
        text = text.replace(old, new)
    text += " " * (-(10 + len(text) + 1) % 64) + "\n"
    return b"\x93NUMPY\x01\x00" + len(text).to_bytes(2, "little") + text.encode("ascii")


BODY = b"".join(v.to_bytes(2, "big") for v in ROWS)
NPY = {
    "not an array at all": b"hello",
    "an array of version 2": npy(ROWS).replace(b"\x93NUMPY\x01\x00", b"\x93NUMPY\x02\x00", 1),
    "a header that is not numpy's": header_of().replace(b"'descr'", b"'dtype'") + BODY,
    "signed bytes": header_of(**{"|u1": "|i1"}) + BODY,
    "16-bit elements": header_of(**{"|u1": "<u2"}) + BODY,
    "fortran order": header_of(**{"False": "True"}) + BODY,
    "a shape of one dimension": header_of(**{"(40, 2)": "(40,)"}) + BODY,
    "a width of three": header_of(**{", 2)": ", 3)"}) + BODY,
    "a width of one": header_of(**{", 2)": ", 1)"}) + BODY[:40],
    "no rows": header_of(0),
    "a row count with a leading zero": header_of(**{"(40,": "(040,"}) + BODY,
    "a row count in hex": header_of(**{"(40,": "(0x28,"}) + BODY,
    "a negative row count": header_of(**{"(40,": "(-40,"}) + BODY,
    "data one row short": npy(ROWS)[:-2],
    "data one byte short": npy(ROWS)[:-1],
    "data one row long": npy(ROWS) + b"\x00\x00",
    "no data": header_of(),
    "a header length past the stream": b"\x93NUMPY\x01\x00" + (60000).to_bytes(2, "little") + b"x" * 80,
    "a header too short to read": b"\x93NUMPY\x01\x00\x05\x00abc",
    "rows declared past the cap": header_of(10**12) + b"\x00" * 8,
    "rows declared beyond a whole number of bytes": header_of(10**40) + b"\x00",
    "nine bytes, a magic and one more": b"\x93NUMPY\x01\x00\x00",
    "ten bytes, a magic and a header length of nothing": b"\x93NUMPY\x01\x00\x00\x00",
    "a header shorter than its length field says": header_of()[:8] + (200).to_bytes(2, "little") + header_of()[10:],
}
NOT_NPY, SHAPE = "not a .npy v1.0 array", "a .npy header that is not unsigned bytes of shape (rows, 2) in C order"
NONE_OR_TOO_MANY, SHORT = "which is none, or more than the reader inflates", "the array holds"
NPY_SAID = {
    "not an array at all": NOT_NPY, "an array of version 2": NOT_NPY, "a header that is not numpy's": SHAPE,
    "signed bytes": SHAPE, "16-bit elements": SHAPE, "fortran order": SHAPE, "a shape of one dimension": SHAPE,
    "a width of three": SHAPE, "a width of one": SHAPE, "no rows": "0 rows, " + NONE_OR_TOO_MANY,
    "a row count with a leading zero": SHAPE, "a row count in hex": SHAPE, "a negative row count": SHAPE,
    "data one row short": "the array holds 78 bytes, not the 80 its header declares",
    "data one byte short": "the array holds 79 bytes, not the 80 its header declares",
    "data one row long": "the array holds more bytes than its header declares",
    "no data": "the array holds 0 bytes, not the 80 its header declares", "a header length past the stream": SHAPE,
    "a header too short to read": SHAPE, "rows declared past the cap": "1000000000000 rows, " + NONE_OR_TOO_MANY,
    "rows declared beyond a whole number of bytes": "10000000000000000000000000000000000000000 rows, " + NONE_OR_TOO_MANY,
    "nine bytes, a magic and one more": NOT_NPY, "ten bytes, a magic and a header length of nothing": SHAPE,
    "a header shorter than its length field says": SHAPE,
}


@pytest.mark.parametrize("name", NPY)
def test_an_array_that_is_not_a_npy_of_the_declared_shape_is_refused_for_that(name):
    assert set(NPY_SAID) == set(NPY)
    with pytest.raises(RawFormError, match=re.escape(NPY_SAID[name])):
        p1_forms.parse_ibm_result(with_npy(NPY[name]))


GOOD_STREAM = zlib.compress(npy(ROWS))
STREAMS = {
    "text that is not base64": "!!!!",
    "base64 with a line feed in it": base64.b64encode(GOOD_STREAM).decode()[:10] + "\n"
                                      + base64.b64encode(GOOD_STREAM).decode()[10:],
    "base64 with a space": base64.b64encode(GOOD_STREAM).decode()[:8] + " " + base64.b64encode(GOOD_STREAM).decode()[8:],
    "base64 that is not ASCII": "éééé",
    "base64 of nothing": "",
    "base64 of bytes that are not zlib": base64.b64encode(b"not a zlib stream at all").decode(),
    "a zlib stream cut short": base64.b64encode(GOOD_STREAM[:-6]).decode(),
    "a zlib stream without its checksum": base64.b64encode(GOOD_STREAM[:-4]).decode(),
    "a zlib stream with a bad checksum": base64.b64encode(GOOD_STREAM[:-1] + bytes([GOOD_STREAM[-1] ^ 1])).decode(),
    "a zlib stream with bytes after it": base64.b64encode(GOOD_STREAM + b"junk").decode(),
    "two zlib streams": base64.b64encode(GOOD_STREAM + GOOD_STREAM).decode(),
}


ENDS = "the zlib stream does not end where the array does"
STREAMS_SAID = {
    "text that is not base64": "not base64", "base64 with a line feed in it": "not base64",
    "base64 with a space": "not base64", "base64 that is not ASCII": "not base64", "base64 of nothing": NOT_NPY,
    "base64 of bytes that are not zlib": "not a zlib stream", "a zlib stream cut short": SHORT,
    "a zlib stream without its checksum": ENDS, "a zlib stream with a bad checksum": "not a zlib stream",
    "a zlib stream with bytes after it": ENDS, "two zlib streams": ENDS,
}


@pytest.mark.parametrize("name", STREAMS)
def test_an_array_that_is_not_one_zlib_stream_of_base64_is_refused_for_that(name):
    assert set(STREAMS_SAID) == set(STREAMS)
    with pytest.raises(RawFormError, match=re.escape(STREAMS_SAID[name])):
        p1_forms.parse_ibm_result(with_array_text(STREAMS[name]))


def values_of(n):
    return [(i * 2654435761) % 65536 for i in range(n)]


@pytest.mark.parametrize("n", [1, 63, 64, 65, 127, 1000, 24576])
def test_an_array_of_any_size_is_read_whole_whether_or_not_the_first_read_holds_all_of_it(n):
    """The first read takes 256 bytes: an array of 64 rows is 256 bytes with its header, and a real one is 49,152 bytes
    of rows and more."""
    r = p1_forms.parse_ibm_result(with_npy(npy(values_of(n))))
    assert r.pubs[0].rows == n and r.pubs[0].body == b"".join(v.to_bytes(2, "big") for v in values_of(n))


@pytest.mark.parametrize("fault, said", [
    (lambda z, n: z[:-1] + bytes([z[-1] ^ 1]), "not a zlib stream"), (lambda z, n: z[:-4], ENDS),
    (lambda z, n: z[:-8], "the array holds 597 bytes, not the 600 its header declares"), (lambda z, n: z + b"junk", ENDS)],
    ids=["a bad checksum", "no checksum", "cut short", "bytes after"])
def test_a_stream_of_300_rows_is_refused_for_the_fault_past_its_first_read(fault, said):
    stream = fault(zlib.compress(npy(values_of(300))), 300)
    with pytest.raises(RawFormError, match=re.escape(said)):
        p1_forms.parse_ibm_result(with_array_text(base64.b64encode(stream).decode()))


@pytest.mark.parametrize("rows, extra, said", [
    (300, 1, "601 bytes, not the 600"), (300, 3, "601 bytes, not the 600"), (64, 1, "129 bytes, not the 128"),
    (64, 3, "129 bytes, not the 128")])
def test_an_array_longer_than_its_header_says_is_read_one_byte_past_it_and_no_further(rows, extra, said):
    with pytest.raises(RawFormError, match=re.escape(said)):
        p1_forms.parse_ibm_result(with_npy(npy(values_of(rows)) + b"\x00" * extra))
    for short in (1, 2):
        with pytest.raises(RawFormError, match=re.escape(f"{2 * rows - short} bytes, not the {2 * rows}")):
            p1_forms.parse_ibm_result(with_npy(npy(values_of(rows))[:-short]))


def test_the_cap_is_64_mib():
    assert p1_forms.CAP == 64 * 1024 * 1024


def test_what_a_result_may_inflate_is_capped_in_all_and_the_cap_itself_is_allowed(monkeypatch):
    rows = values_of(70)
    want = len(npy(rows))
    assert want == 268
    monkeypatch.setattr(p1_forms, "CAP", want)
    assert p1_forms.parse_ibm_result(raw_ibm([rows], [None])).shots == 70
    monkeypatch.setattr(p1_forms, "CAP", want - 1)
    with pytest.raises(RawFormError, match="70 rows, which is none, or more than the reader inflates"):
        p1_forms.parse_ibm_result(raw_ibm([rows], [None]))
    monkeypatch.setattr(p1_forms, "CAP", 280)                     # two PUBs spend 140 and 140 of it
    assert p1_forms.parse_ibm_result(raw_ibm([rows, rows], [None, None])).shots == 70
    with pytest.raises(RawFormError, match="more than the reader inflates"):
        p1_forms.parse_ibm_result(raw_ibm([rows] * 3, [None] * 3))
    monkeypatch.setattr(p1_forms, "CAP", 279)
    with pytest.raises(RawFormError, match="more than the reader inflates"):
        p1_forms.parse_ibm_result(raw_ibm([rows, rows], [None, None]))


def test_one_row_is_a_result():
    r = p1_forms.parse_ibm_result(raw_ibm([[7]], [None]))
    assert (r.shots, r.pubs[0].body) == (1, b"\x00\x07")


@pytest.mark.parametrize("results", [5, "abc", {"a": 1}, None, [], 1.5, True])
def test_pub_results_that_are_not_a_list_of_one_or_more_are_refused_for_that(results):
    doc = {"__type__": "PrimitiveResult", "__value__": {"pub_results": results}}
    with pytest.raises(RawFormError, match="pub_results: a list of one PUB or more"):
        p1_forms.parse_ibm_result(dumps(doc))


@pytest.mark.parametrize("measurements", [5, "abc", [], {}, None, [1], 1.5, True])
def test_measurements_that_are_not_an_object_of_one_setting_or_more_are_refused_for_that(measurements):
    with pytest.raises(RawFormError, match="measurements: an object of one setting or more"):
        p1_forms.parse_atlas_vector(dumps({"job": "j", "measurements": measurements}))


@pytest.mark.parametrize("counts", [5, "abc", [], {}, None, [["0" * 16, 1]], 1.5, True])
def test_counts_that_are_not_an_object_of_one_outcome_or_more_are_refused_for_that(counts):
    label = "I" * 16
    with pytest.raises(RawFormError, match="counts is an object of one outcome or more"):
        p1_forms.parse_atlas_vector(dumps({"job": "j", "measurements": {label: {"counts": counts, "shots": 1}}}))


def bomb(declared_rows, zeros):
    """A zlib stream that inflates to a .npy header declaring `declared_rows` and `zeros` bytes after it, built in
    chunks so that this test never holds the inflated bytes."""
    comp, out = zlib.compressobj(1), []
    out.append(comp.compress(header_of(declared_rows)))
    chunk = b"\x00" * (1 << 20)
    for _ in range(zeros >> 20):
        out.append(comp.compress(chunk))
    out.append(comp.flush())
    return base64.b64encode(b"".join(out)).decode("ascii")


@pytest.mark.parametrize("rows", [1, 100], ids=["rows the first 256 bytes already pass", "rows a stream is cut at"])
def test_a_stream_that_would_fill_memory_is_refused_having_inflated_only_what_its_header_declares(rows):
    text = bomb(rows, 40 << 20)
    assert len(text) < 500000
    tracemalloc.start()
    try:
        with pytest.raises(RawFormError, match="more bytes than its header declares|the array holds"):
            p1_forms.parse_ibm_result(with_array_text(text))
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < 8 << 20, peak


def test_a_header_declaring_more_rows_than_the_reader_inflates_is_refused_before_inflating_them():
    tracemalloc.start()
    try:
        with pytest.raises(RawFormError, match="more than the reader inflates"):
            p1_forms.parse_ibm_result(with_array_text(bomb(p1_forms.CAP // 2 + 1, 1 << 20)))
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < 8 << 20, peak


def test_the_cap_is_for_a_whole_result_not_for_each_pub(monkeypatch):
    """One PUB of 30 rows is a 188-byte array, 60 of them data; a cap of 200 admits three PUBs and refuses a fourth."""
    monkeypatch.setattr(p1_forms, "CAP", 200)
    assert p1_forms.parse_ibm_result(dumps(ibm_doc([ROWS[:30]], [None]))).shots == 30
    assert p1_forms.parse_ibm_result(dumps(ibm_doc([ROWS[:30]] * 3, [None] * 3))).shots == 30
    with pytest.raises(RawFormError, match="more than the reader inflates"):
        p1_forms.parse_ibm_result(dumps(ibm_doc([ROWS[:30]] * 4, [None] * 4)))


# -- Atlas ---------------------------------------------------------------------------------------------------------------
LAYOUTS = {(0, 1, 2, 3, 4): 20, (1, 3, 5, 7, 9): 12}


def atlas_doc():
    return json.loads(atlas_result(LAYOUTS))


def vector_doc():
    return json.loads(atlas_vector())


def settings(doc):
    return doc["response"]["result"]["measurements"]


def first_setting(doc):
    return next(iter(settings(doc).values()))


def test_a_good_atlas_result_is_read_whole():
    r = p1_forms.parse_atlas_result(atlas_result(LAYOUTS))
    assert r.shots == 32 and r.job == "synthetic-law" and len(r.settings) == 2
    assert set(r.settings) == {"IIIIIIIIIIIIIIZZ", "IIIIIIIIIIIIIIXX"}
    assert r.observables["0"]["Z"] == 0.37939453125 and r.spans == () and r.first_shot is None


def test_a_good_vector_is_read_whole():
    r = p1_forms.parse_atlas_vector(atlas_vector())
    assert r.shots == 4096 and r.job == "synthetic-vector" and r.observables is None and len(r.settings) == 3


FETCHED = "2026-09-26T11:51:22Z"


def with_fetched_at(value):
    doc = atlas_doc()
    doc["fetched_at"] = value
    return json.dumps(doc).encode()


def test_a_fetched_at_is_admitted_and_read_for_nothing():
    """Five of the six real law results carry a top-level `fetched_at` (the one of 2026-09-25 does not): the reader
    returns the same result with it, whatever time it names, as without."""
    plain = p1_forms.parse_atlas_result(atlas_result(LAYOUTS))
    for value in (FETCHED, "2026-09-26T11:51:22.5Z", "2026-09-26T11:51:22.123456Z", "1970-01-01T00:00:00Z"):
        assert p1_forms.parse_atlas_result(with_fetched_at(value)) == plain


FETCHED_BAD = {
    "a date": "2026-09-26", "no zone": "2026-09-26T11:51:22", "an offset": "2026-09-26T11:51:22+00:00",
    "a space": "2026-09-26 11:51:22Z", "a trailing zero in the fraction": "2026-09-26T11:51:22.50Z",
    "month 13": "2026-13-26T11:51:22Z", "a lowercase z": "2026-09-26T11:51:22z",
    "Arabic-Indic digits": "٢٠٢٦-09-26T11:51:22Z", "a leap second": "2026-09-26T11:51:60Z", "nothing": "",
    "a number": 5, "null": None, "a bool": True, "a list": [FETCHED], "an object": {"@id": FETCHED},
}


@pytest.mark.parametrize("name", FETCHED_BAD)
def test_a_fetched_at_that_is_not_a_time_in_the_profiles_spelling_is_refused_for_that(name):
    with pytest.raises(RawFormError, match=re.escape("fetched_at is not a time in the profile's spelling")):
        p1_forms.parse_atlas_result(with_fetched_at(FETCHED_BAD[name]))


def test_a_fetched_at_does_not_open_the_wrapper_or_the_vector_to_anything_else():
    doc = atlas_doc()
    doc.update({"fetched_at": FETCHED, "extra": 1})
    with pytest.raises(RawFormError, match="holds .*extra"):
        p1_forms.parse_atlas_result(json.dumps(doc).encode())
    vector = vector_doc()
    vector["fetched_at"] = FETCHED
    with pytest.raises(RawFormError, match="holds .*fetched_at"):
        p1_forms.parse_atlas_vector(json.dumps(vector).encode())


def test_no_key_but_the_five_and_fetched_at_is_admitted_on_the_atlas_wrapper():
    """The verifier's mutant 42 admitted `fetched_by` and `note`: the set was tried only with a key called `extra`. Every
    name a producer might add, and three hundred made up, are refused; the six are admitted (the five are required)."""
    names = ["fetched_by", "note", "fetched", "fetchedAt", "Fetched_at", "FETCHED_AT", "fetched_at ", " fetched_at", "taken_at",
             "taken_by", "source", "version", "meta", "metadata", "comment", "created", "updated", "_fetched_at", "fetched-at",
             "fetched_at2", "job", "result", "measurements", "extra", "", "status_text", "id", "jobId", "job_id2", "paths"]
    rng = random.Random(42)
    names += ["".join(rng.choice("abcdefghijklmnopqrstuvwxyz_") for _ in range(rng.randint(1, 12))) for _ in range(300)]
    admitted = {"job_id", "path", "response", "status", "taken_from", "fetched_at"}
    for name in dict.fromkeys(names):
        if name in admitted:
            continue
        doc = atlas_doc()
        doc[name] = 1
        with pytest.raises(RawFormError, match="which the form does not"):
            p1_forms.parse_atlas_result(json.dumps(doc).encode())
    for name in sorted(admitted - {"fetched_at"}):
        doc = atlas_doc()
        del doc[name]
        with pytest.raises(RawFormError, match="lacks"):
            p1_forms.parse_atlas_result(json.dumps(doc).encode())
    assert p1_forms.parse_atlas_result(with_fetched_at(FETCHED)).shots == 32


def rekey(d, bad, count=None, extra=0):
    """The first outcome of the first setting under the name `bad` (and with `count`, if given); `extra` added to the
    first outcome's own, so that the counts still sum to the shots and nothing but this fault stands."""
    counts = first_setting(d)["counts"]
    first = next(iter(counts))
    n = counts.pop(first)
    counts[bad] = n if count is None else count
    if extra:
        counts[first] = n + extra
    return counts


ATLAS_BAD = {
    "a wrapper key missing": lambda d: d.pop("status"),
    "a wrapper key more": lambda d: d.update({"extra": 1}),
    "a job id that is a number": lambda d: d.update({"job_id": 5}),
    "a path that is a number": lambda d: d.update({"path": 5}),
    "a status that is a string": lambda d: d.update({"status": "200"}),
    "a status that is a bool": lambda d: d.update({"status": True}),
    "a response that is a list": lambda d: d.update({"response": []}),
    "a response with a second key": lambda d: d["response"].update({"extra": 1}),
    "a result with a key more": lambda d: d["response"]["result"].update({"extra": 1}),
    "no observables": lambda d: d["response"]["result"].pop("observables"),
    "observables that are a list": lambda d: d["response"]["result"].update({"observables": []}),
    "density_matrices that are a number": lambda d: d["response"]["result"].update({"density_matrices": 5}),
    "measurements that are a list": lambda d: d["response"]["result"].update({"measurements": []}),
    "measurements empty": lambda d: d["response"]["result"].update({"measurements": {}}),
    "a label of fifteen letters": lambda d: settings(d).update({"I" * 15: first_setting(d)}),
    "a label of lowercase letters": lambda d: settings(d).update({"i" * 16: first_setting(d)}),
    "a label with a letter outside IXYZ": lambda d: settings(d).update({"IIIIIIIIIIIIIIIA": first_setting(d)}),
    "a setting that is a list": lambda d: settings(d).update({"IIIIIIIIIIIIIIII": []}),
    "a setting with a key more": lambda d: first_setting(d).update({"extra": 1}),
    "a setting without shots": lambda d: first_setting(d).pop("shots"),
    "shots 0": lambda d: first_setting(d).update({"shots": 0}),
    "shots as a bool": lambda d: first_setting(d).update({"shots": True}),
    "shots as a string": lambda d: first_setting(d).update({"shots": "32"}),
    "shots as a float": lambda d: first_setting(d).update({"shots": 32.0}),
    "counts that do not sum to the shots": lambda d: first_setting(d).update({"shots": 33}),
    "counts empty": lambda d: first_setting(d).update({"counts": {}}),
    "counts as a list": lambda d: first_setting(d).update({"counts": []}),
    "an outcome of fifteen characters": lambda d: rekey(d, "0" * 15),
    "an outcome that is not binary": lambda d: rekey(d, "2" * 16),
    "an outcome in fullwidth digits": lambda d: rekey(d, "０" * 16),
    "a count of 0": lambda d: first_setting(d)["counts"].update({"0" * 16: 0}),
    "a negative count": lambda d: rekey(d, "0" * 16, -1, extra=1),
    "a count of 0.0": lambda d: first_setting(d)["counts"].update({"0" * 16: 0.0}),
    "a count that is a bool": lambda d: first_setting(d)["counts"].update({"0" * 16: False}),
    "a count that is a string": lambda d: first_setting(d)["counts"].update({"0" * 16: "1"}),
    "settings that disagree on their shots": lambda d: list(settings(d).values())[1].update(
        {"shots": 33, "counts": {**list(settings(d).values())[1]["counts"], "0" * 16: 1}}),
}


@pytest.mark.parametrize("fn", ATLAS_BAD.values(), ids=ATLAS_BAD)
def test_an_atlas_result_of_another_structure_is_refused(fn):
    doc = atlas_doc()
    fn(doc)
    with pytest.raises(RawFormError):
        p1_forms.parse_atlas_result(json.dumps(doc).encode())


def tiny_atlas(shots, count):
    doc = atlas_doc()
    doc["response"]["result"]["measurements"] = {"IIIIIIIIIIIIIIZZ": {"counts": {"0" * 16: count}, "shots": shots}}
    return json.dumps(doc).encode()


def test_a_tiny_atlas_result_is_read_and_the_numbers_that_only_equal_a_whole_number_are_not():
    """shots 1 over one count of 1 is a result. True and 1.0 equal 1 and sum to it, so only the type refuses them:
    nothing else is wrong with these documents."""
    assert p1_forms.parse_atlas_result(tiny_atlas(1, 1)).shots == 1
    for shots, count in ((True, 1), (1.0, 1), (1, True), (1, 1.0)):
        with pytest.raises(RawFormError, match="whole number"):
            p1_forms.parse_atlas_result(tiny_atlas(shots, count))


def test_one_setting_whose_counts_do_not_sum_to_its_shots_is_refused_with_nothing_else_wrong():
    """Two settings with different shots are refused for disagreeing; one setting alone is refused for its sum."""
    for shots, count in ((2, 1), (1, 2), (100, 99)):
        with pytest.raises(RawFormError, match="do not sum"):
            p1_forms.parse_atlas_result(tiny_atlas(shots, count))


VECTOR_BAD = {
    "no job": lambda d: d.pop("job"), "a job that is a number": lambda d: d.update({"job": 5}),
    "a key more": lambda d: d.update({"extra": 1}), "no measurements": lambda d: d.pop("measurements"),
    "measurements empty": lambda d: d.update({"measurements": {}}),
    "a count that is zero": lambda d: next(iter(d["measurements"].values()))["counts"].update({"0" * 16: 0}),
    "shots that are not the sum": lambda d: next(iter(d["measurements"].values())).update({"shots": 1}),
}


@pytest.mark.parametrize("fn", VECTOR_BAD.values(), ids=VECTOR_BAD)
def test_a_vector_of_another_structure_is_refused(fn):
    doc = vector_doc()
    fn(doc)
    with pytest.raises(RawFormError):
        p1_forms.parse_atlas_vector(json.dumps(doc).encode())


@pytest.mark.parametrize("parse", [p1_forms.parse_atlas_result, p1_forms.parse_atlas_vector],
                         ids=["the result", "the vector"])
@pytest.mark.parametrize("data", [b"", b"\xff", b"[]", b'{"a": 1, "a": 2}', b"NaN", deep(100000), b"{}"],
                         ids=["nothing", "not UTF-8", "a list", "a key twice", "NaN", "deep", "empty"])
def test_atlas_bytes_that_are_no_json_object_are_refused(parse, data):
    with pytest.raises(RawFormError):
        parse(data)


def test_the_atlas_wrapper_is_not_a_vector_and_the_vector_is_not_the_wrapper():
    with pytest.raises(RawFormError):
        p1_forms.parse_atlas_vector(atlas_result(LAYOUTS))
    with pytest.raises(RawFormError):
        p1_forms.parse_atlas_result(atlas_vector())
    with pytest.raises(RawFormError):
        p1_forms.parse_ibm_result(atlas_vector())


# -- the corruptions and truncations a hostile file can be --------------------------------------------------------------
SWEEP = {
    "ibm": (p1_forms.parse_ibm_result, dumps(ibm_doc([ROWS[:8]], [ECHO], SPAN))),
    "atlas": (p1_forms.parse_atlas_result, atlas_result({(0, 1, 2): 3})),
    "vector": (p1_forms.parse_atlas_vector, atlas_vector(labels=("IIIIIIYIIIIIIXII",), scale=2)),
}


@pytest.mark.parametrize("form", SWEEP)
def test_no_single_corrupted_byte_and_no_truncation_escapes_as_anything_but_a_refusal(form):
    parse, data = SWEEP[form]
    parse(data)
    rng, refused = random.Random(20261016), 0
    for _ in range(600):
        b = bytearray(data)
        b[rng.randrange(len(b))] = rng.randrange(256)
        try:
            parse(bytes(b))
        except RawFormError:
            refused += 1
    for n in range(0, len(data), max(1, len(data) // 150)):
        with pytest.raises(RawFormError):
            parse(data[:n])
    assert refused > 100


@pytest.mark.parametrize("form", [IBM_FORM, ATLAS_FORM, VECTOR_FORM])
def test_each_form_reads_through_the_checkers_step_3_and_a_bad_file_is_raw_form(form, tmp_path, monkeypatch):
    for k, v in p1_forms.READERS.items():
        monkeypatch.setitem(checker.RAW_FORMS, k, v)
    m = ibm_model()
    raw = "run/jobka-raw.json"
    m.ents[raw]["qro:rawForm"] = form
    m.files[raw] = {IBM_FORM: m.files[raw], ATLAS_FORM: atlas_result(LAYOUTS), VECTOR_FORM: atlas_vector()}[form]
    shots = {IBM_FORM: 40, ATLAS_FORM: 32, VECTOR_FORM: 4096}[form]
    m.ents[raw]["qro:shots"] = shots
    crate = m.write(tmp_path / "ok")
    checker.counts(crate, read_md(crate))
    m.files[raw] = m.files[raw][:-7]
    crate = m.write(tmp_path / "bad")
    with pytest.raises(Refused) as r:
        checker.counts(crate, read_md(crate))
    assert (r.value.name, r.value.where) == ("raw-form", raw)


def test_a_form_the_module_does_not_read_is_a_keyerror_for_parse_raw():
    with pytest.raises(KeyError):
        p1_forms.parse_raw("ibm-sampler-result/v2", b"{}")
    assert set(p1_forms.PARSERS) == set(p1_forms.READERS) == {IBM_FORM, ATLAS_FORM, VECTOR_FORM}


# -- times -----------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text, zone, want", [
    ("2026-10-05T10:27:00.285375Z", "Z", at(10, 27, 0, 285375)), ("2026-10-05T10:27:00Z", "Z", at(10, 27, 0)),
    ("2026-10-05T10:27:00.5Z", "Z", at(10, 27, 0, 500000)),
    ("2026-10-05T10:27:00.380000Z", "Z", at(10, 27, 0, 380000)),
    ("2026-10-05T10:27:00.285375", "", at(10, 27, 0, 285375)), ("2026-10-05T10:27:00", "", at(10, 27, 0))])
def test_a_time_is_read_as_utc_with_one_to_six_fraction_digits(text, zone, want):
    got = p1_forms.parse_time(text, zone)
    assert got == want and got.utcoffset().total_seconds() == 0


@pytest.mark.parametrize("text, zone", [
    ("2026-10-05T10:27:00", "Z"), ("2026-10-05T10:27:00Z", ""), ("2026-10-05T10:27:00z", "Z"),
    ("2026-10-05T10:27:00.Z", "Z"), ("2026-10-05T10:27:00.1234567Z", "Z"), ("2026-10-05t10:27:00Z", "Z"),
    # a fraction of more than six digits is none, whatever its digits (a seventh of zeros would read as a microsecond or none)
    ("2026-10-05T10:27:00.0000001Z", "Z"), ("2026-10-05T10:27:00.0000000Z", "Z"), ("2026-10-05T10:27:00.000000001Z", "Z"),
    ("2026-10-05T10:27:00.0000001", ""), ("2026-10-05T10:27:00.000000001", ""),
    ("2026-10-05T10:27:60Z", "Z"), ("2026-13-05T10:27:00Z", "Z"), ("2026-02-30T10:27:00Z", "Z"),
    ("2026-10-05T24:00:00Z", "Z"), ("2026-10-05T10:27:00+00:00", ""), (" 2026-10-05T10:27:00Z", "Z"),
    ("2026-10-05T10:27:00Z\n", "Z"), ("٢٠٢٦-10-05T10:27:00Z", "Z"), ("", "Z"), (7, "Z"),
    ("2026-10-05T10:27:00Z", "Q")])
def test_a_time_that_is_not_one_of_the_two_spellings_is_refused(text, zone):
    with pytest.raises(ValueError):
        p1_forms.parse_time(text, zone)


# -- the snapshot form ------------------------------------------------------------------------------------------------------------
def snap():
    return snapshot_doc(at(9, 2, 46), at(9, 2, 30))


def snap_bytes(doc):
    return json.dumps(doc).encode("utf-8")


def test_a_good_snapshot_is_read_whole():
    s = p1_forms.parse_snapshot(snapshot_bytes(snap()))
    assert (s.device, s.stamp, s.newest) == ("ibm_synth", at(9, 2, 46), at(9, 2, 30))
    assert s.doc == snap()


def test_the_newest_value_is_the_newest_date_anywhere_inside_and_the_stamp_is_not_one_of_them():
    d = snap()
    d["general"][0]["date"] = "2026-10-05T11:00:00.5Z"
    assert p1_forms.parse_snapshot(snap_bytes(d)).newest == at(11, 0, 0, 500000)
    d = snap()
    d["last_update_date"] = "2026-10-05T23:00:00Z"
    assert p1_forms.parse_snapshot(snap_bytes(d)).newest == at(9, 2, 30)
    d = snap()
    d["qubits"][1][0]["date"] = "2026-10-05T10:00:00Z"
    assert p1_forms.parse_snapshot(snap_bytes(d)).newest == at(10, 0, 0)
    d = snap()
    d["gates"][0]["parameters"][0]["date"] = "2026-10-05T12:00:00Z"
    assert p1_forms.parse_snapshot(snap_bytes(d)).newest == at(12, 0, 0)


SNAP_BAD = {
    "a key missing": lambda d: d.pop("qubits"), "a key more": lambda d: d.update({"extra": 1}),
    "backend_name a number": lambda d: d.update({"backend_name": 7}),
    "backend_version null": lambda d: d.update({"backend_version": None}),
    "the stamp without its Z": lambda d: d.update({"last_update_date": "2026-10-05T09:02:46"}),
    "the stamp in month 13": lambda d: d.update({"last_update_date": "2026-13-05T09:02:46Z"}),
    "the stamp a number": lambda d: d.update({"last_update_date": 5}),
    "gates a dict": lambda d: d.update({"gates": {}}), "gates a string": lambda d: d.update({"gates": "x"}),
    "a gate a list": lambda d: d["gates"].__setitem__(0, []),
    "a gate with a key more": lambda d: d["gates"][0].update({"extra": 1}),
    "a gate without parameters": lambda d: d["gates"][0].pop("parameters"),
    "a gate name a number": lambda d: d["gates"][0].update({"name": 1}),
    "a gate's qubits a string": lambda d: d["gates"][0].update({"qubits": "01"}),
    "a gate's qubit a float": lambda d: d["gates"][0].update({"qubits": [0.5]}),
    "a gate's qubit a bool": lambda d: d["gates"][0].update({"qubits": [True]}),
    "a gate's qubit past binary64's integers": lambda d: d["gates"][0].update({"qubits": [2**53 + 1]}),
    "a gate's qubit past the profile's bound": lambda d: d["gates"][0].update({"qubits": [2**63]}),
    "a parameter with a key more": lambda d: d["gates"][0]["parameters"][0].update({"extra": 1}),
    "a parameter without a date": lambda d: d["gates"][0]["parameters"][0].pop("date"),
    "a parameter date without Z": lambda d: d["gates"][0]["parameters"][0].update({"date": "2026-10-05T06:23:09"}),
    "a parameter date a number": lambda d: d["gates"][0]["parameters"][0].update({"date": 5}),
    "a parameter date at a leap second": lambda d: d["gates"][0]["parameters"][0].update(
        {"date": "2026-10-05T06:23:60Z"}),
    "a parameter value a string": lambda d: d["gates"][0]["parameters"][0].update({"value": "0.1"}),
    "a parameter value a bool": lambda d: d["gates"][0]["parameters"][0].update({"value": True}),
    "a parameter value null": lambda d: d["gates"][0]["parameters"][0].update({"value": None}),
    "a parameter value a list": lambda d: d["gates"][0]["parameters"][0].update({"value": [1]}),
    "an integer binary64 cannot hold": lambda d: d["gates"][0]["parameters"][0].update({"value": 2**53 + 1}),
    "a negative integer binary64 cannot hold": lambda d: d["gates"][0]["parameters"][0].update({"value": -(2**53 + 1)}),
    "an integer binary64 holds, past the profile's bound": lambda d: d["gates"][0]["parameters"][0].update(
        {"value": 2**63}),
    "a negative integer past the profile's bound": lambda d: d["gates"][0]["parameters"][0].update({"value": -(2**63)}),
    "an integer past binary64's range": lambda d: d["gates"][0]["parameters"][0].update({"value": 10**400}),
    "a parameter unit a number": lambda d: d["gates"][0]["parameters"][0].update({"unit": 0}),
    "general a dict": lambda d: d.update({"general": {}}),
    "a general entry with a key more": lambda d: d["general"][0].update({"extra": 1}),
    "a general entry a list": lambda d: d["general"].__setitem__(0, [1]),
    "general_qlists a string": lambda d: d.update({"general_qlists": ""}),
    "a qlist with a date": lambda d: d["general_qlists"][0].update({"date": "2026-10-05T06:23:09Z"}),
    "a qlist's qubits null": lambda d: d["general_qlists"][0].update({"qubits": None}),
    "qubits a dict": lambda d: d.update({"qubits": {}}),
    "a qubit row a dict": lambda d: d["qubits"].__setitem__(0, {}),
    "a qubit entry a string": lambda d: d["qubits"][0].__setitem__(0, "x"),
    "a qubit entry with a key more": lambda d: d["qubits"][0][0].update({"extra": 1}),
    "no date anywhere": lambda d: d.update({"gates": [], "general": [], "qubits": []}),
}


@pytest.mark.parametrize("fn", SNAP_BAD.values(), ids=SNAP_BAD)
def test_a_snapshot_of_another_form_is_refused(fn):
    d = snap()
    fn(d)
    with pytest.raises(SnapshotError):
        p1_forms.parse_snapshot(snap_bytes(d))


@pytest.mark.parametrize("data", [b"", b"\xff", b"[]", b"7", b'{"a": 1, "a": 2}', b"NaN", deep(100000),
                                  snap_bytes(snap()).replace(b"0.0125", b"NaN"),
                                  snap_bytes(snap()).replace(b"0.0125", b"1e999"), b"{}"],
                         ids=["nothing", "not UTF-8", "a list", "a number", "a key twice", "NaN", "deep",
                              "a NaN value", "a value past binary64", "empty"])
def test_snapshot_bytes_that_are_no_json_object_are_refused(data):
    with pytest.raises(SnapshotError):
        p1_forms.parse_snapshot(data)


def test_a_key_twice_in_an_otherwise_valid_snapshot_is_refused():
    data = snapshot_bytes(snap())
    old = b'"backend_version": "1.0.0"'
    assert data.count(old) == 1
    p1_forms.parse_snapshot(data)
    with pytest.raises(SnapshotError, match="twice"):
        p1_forms.parse_snapshot(data.replace(old, old + b", " + old))
    with pytest.raises(SnapshotError):
        p1_forms.parse_snapshot(data.replace(old, old + b', "x": NaN'))


@pytest.mark.parametrize("value, held", [(2**53, True), (-(2**53), True), (2**53 + 1, False), (-(2**53 + 1), False),
                                         (2**62, True), (10**400, False), (-(10**400), False), (0, True),
                                         (0.1, True), (1e300, True), (-5, True)])
def test_an_integer_is_held_to_what_binary64_holds_exactly_by_the_helper_itself(value, held):
    """The snapshot reader's bound, 2^63 - 1, is met first for the biggest integers, so `10**400` never reaches the helper
    through `parse_snapshot` any more; it is handed one here, and an integer too big for `float` is a refusal and no
    OverflowError."""
    if held:
        p1_forms._exact_number(value, "x")
    else:
        with pytest.raises(SnapshotError, match="an integer binary64 cannot hold"):
            p1_forms._exact_number(value, "x")


@pytest.mark.parametrize("value", [True, False, None, "1", [1], {"a": 1}])
def test_a_value_that_is_no_number_is_no_number_to_the_helper(value):
    with pytest.raises(SnapshotError, match="not a number"):
        p1_forms._exact_number(value, "x")


def test_an_integer_binary64_holds_is_accepted_to_the_profiles_bound_and_the_snapshot_error_is_not_a_raw_form_error():
    d = snap()
    d["gates"][0]["parameters"][0]["value"] = 2**62
    assert p1_forms.parse_snapshot(snap_bytes(d)).device == "ibm_synth"
    d["gates"][0]["parameters"][0]["value"] = 2**63                 # binary64 holds it exactly, and it is past 2^63 - 1
    with pytest.raises(SnapshotError, match="an integer past 9223372036854775807"):
        p1_forms.parse_snapshot(snap_bytes(d))
    assert not issubclass(SnapshotError, RawFormError)


def test_no_corrupted_byte_of_a_snapshot_escapes_as_anything_but_a_refusal():
    data = snapshot_bytes(snap())
    rng = random.Random(7)
    for _ in range(500):
        b = bytearray(data)
        b[rng.randrange(len(b))] = rng.randrange(256)
        try:
            p1_forms.parse_snapshot(bytes(b))
        except SnapshotError:
            pass
    for n in range(0, len(data), 37):
        with pytest.raises(SnapshotError):
            p1_forms.parse_snapshot(data[:n])
