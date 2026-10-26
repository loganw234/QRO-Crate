"""Quantum-Film's commitment v3, recomputed. Its oracle is IBM's: five real PUBs of Quantum-Film's 2026-10-05
campaign, each of whose fourteen fields is a literal here, taken from the device-run records of moth-quantum, and
each of whose commitment is the one IBM echoed inside its own result (the echo, read from the raw bytes). A mutant
of the stream's encoding, of the field order or of the version string moves them. The stream is also written out
by hand below, from its statement, so that two statements of it must agree."""
import hashlib

import pytest

from qro import p1_commit

OPTIONS = {"dynamical_decoupling": {"enable": False}, "twirling": {"enable_gates": False, "enable_measure": False}}
OPTIONS_SHA256 = "35fb34a85694fd897d4fb87a74acda7479b2145b2c15915fa8273d4c2ccbd6ad"
DECODE = "quantum_film.ibm.decode/v1"

# ibm_kingston's morning known-answer job, PUB 0; its law job; its coherence job's PUBs 0 and 1; and ibm_marrakesh's
# morning known-answer job: each with the commitment IBM echoed.
VECTORS = [
    ({"stock": "pauli-4x4", "role": "known-answer", "basis": "ZZZZZZZZZZZZZZZZ", "kind": "qpu", "route": "ibm-direct",
      "backend": "ibm_kingston", "program": "sampler", "pub": 0,
      "circuit_sha256": "60c78957bf47b2b2bb8053b2e2103fa2bf1373752b85acfdc4bd37037f22ff49",
      "isa_sha256": "b456ac0f2538ebe423fc9c76ad19115443d3a82c2b96478a96651030c76ceb3f", "shots": 1024,
      "options_sha256": OPTIONS_SHA256, "decode": DECODE,
      "salt": "5d70dfea19917af1299cd4d0a78754c514bff7070b1b50ba18241fddb2b2dfe6"},
     "e0b009ec2a9548e105589b74a545e3e610b1cf5321733a7e2156c7317a4569bd"),
    ({"stock": "pauli-4x4", "role": "law", "basis": "ZZZZZZZZZZZZZZZZ", "kind": "qpu", "route": "ibm-direct",
      "backend": "ibm_kingston", "program": "sampler", "pub": 0,
      "circuit_sha256": "33cfeaa15e5ab0af031531d6b0bdbaee4df311196ca422fe6b927ee783e35fc7",
      "isa_sha256": "8689e93c97b08b228f1927c0a5f36c39baf6ab739a6fb7802da316da8725b117", "shots": 24576,
      "options_sha256": OPTIONS_SHA256, "decode": DECODE,
      "salt": "950a46295cc7f94914133017f8c512a9b2b7b437e1a015bb351fce597ed92134"},
     "7616bc36de9ec35dbed90a1fe77735e764b702dad298a4f1e6ee1fb52661b11c"),
    ({"stock": "pauli-4x4", "role": "coherence", "basis": "XXZZZZZZZZZZZZZZ", "kind": "qpu", "route": "ibm-direct",
      "backend": "ibm_kingston", "program": "sampler", "pub": 0,
      "circuit_sha256": "bc4c3f12aa1f366abd28746ae7d22c8f6a7cfdb5ab6e926fe94b058e4072220f",
      "isa_sha256": "c492ca796d69ed20928c026d49cc647794ec08c3eb6058da88f9bf1a916e1014", "shots": 4096,
      "options_sha256": OPTIONS_SHA256, "decode": DECODE,
      "salt": "d744480e845e8552a7afd426a31db7745724fa6f3bf70d6cb02b680515c99f1d"},
     "1b4a6abd682874504756f89caf2acb40197dcf7e413c41016d887f9402b2a2fe"),
    ({"stock": "pauli-4x4", "role": "coherence", "basis": "YYZZZZZZZZZZZZZZ", "kind": "qpu", "route": "ibm-direct",
      "backend": "ibm_kingston", "program": "sampler", "pub": 1,
      "circuit_sha256": "0c57183b5e86c3091ceab22deb3f4cc3387a8379febe7ba22e1841e03d98b5f0",
      "isa_sha256": "7ba8a0acf37c66fe46e9e67641313d0d07b1ebb2fad8f84aa911ac2a8a34490f", "shots": 4096,
      "options_sha256": OPTIONS_SHA256, "decode": DECODE,
      "salt": "d7fe89cfe1ba66893d9a51a376e7a5b6870d6b9594b994d43b42d60daa4587cf"},
     "6cc7ca2c891e9551d71f3b17c48d2bb2016f5b7a7f4165306535ae3238950570"),
    ({"stock": "pauli-4x4", "role": "known-answer", "basis": "ZZZZZZZZZZZZZZZZ", "kind": "qpu", "route": "ibm-direct",
      "backend": "ibm_marrakesh", "program": "sampler", "pub": 0,
      "circuit_sha256": "60c78957bf47b2b2bb8053b2e2103fa2bf1373752b85acfdc4bd37037f22ff49",
      "isa_sha256": "619fe6b8a36ea3e059d54e697e350dabb4f531f33a098d57845cf0da1c5c6b9b", "shots": 1024,
      "options_sha256": OPTIONS_SHA256, "decode": DECODE,
      "salt": "84b5f7727cb832c72ada25f104078d474703be7f3d4d6afdd30e40dcb575d4f4"},
     "1d3b1ba636106296207b11680c0edc67f1d1c792c756bd436fdf1d9567b22378"),
]
IDS = ["kingston known-answer", "kingston law", "kingston coherence 0", "kingston coherence 1",
       "marrakesh known-answer"]
ORDER = ["stock", "role", "basis", "kind", "route", "backend", "program", "pub", "circuit_sha256", "isa_sha256", "shots",
         "options_sha256", "decode", "salt"]


@pytest.mark.parametrize("fields, echo", VECTORS, ids=IDS)
def test_the_commitment_recomputes_to_what_ibm_echoed(fields, echo):
    assert p1_commit.commitment_of(fields) == echo
    assert p1_commit.commitment_v3(**fields) == echo


@pytest.mark.parametrize("fields, echo", VECTORS, ids=IDS)
def test_the_stream_written_out_by_hand_from_its_statement_is_the_same(fields, echo):
    """`s<byte length>:<UTF-8>` for a str, `i<decimal>` for an int, joined by `|`, the version first."""
    parts = ["quantum-film/commitment/v3"] + [fields[name] for name in ORDER]
    pieces = [f"i{p}".encode() if isinstance(p, int) else b"s%d:" % len(p.encode("utf-8")) + p.encode("utf-8")
              for p in parts]
    assert hashlib.sha256(b"|".join(pieces)).hexdigest() == echo


def test_the_fourteen_fields_are_in_the_streams_order_with_their_types():
    assert [n for n, _ in p1_commit.FIELDS] == ORDER
    assert {n: k for n, k in p1_commit.FIELDS} == {n: (int if n in ("pub", "shots") else str) for n in ORDER}
    assert p1_commit.COMMITMENT_V3 == "quantum-film/commitment/v3"


def other(name, value):
    if isinstance(value, int):
        return value + 1
    return value[:-1] + ("0" if value[-1] != "0" else "1") if len(value) > 1 else value + "x"


@pytest.mark.parametrize("name", ORDER)
def test_each_of_the_fourteen_fields_binds(name):
    fields, echo = VECTORS[0]
    changed = dict(fields, **{name: other(name, fields[name])})
    assert changed[name] != fields[name]
    assert p1_commit.commitment_of(changed) != echo


@pytest.mark.parametrize("a, b", [("role", "basis"), ("circuit_sha256", "isa_sha256"), ("kind", "route"),
                                  ("backend", "program"), ("pub", "shots"), ("options_sha256", "salt")])
def test_the_order_of_the_fields_binds(a, b):
    """Two fields of one type swapped: the same bytes in another order are another commitment."""
    fields, echo = VECTORS[0]
    swapped = dict(fields, **{a: fields[b], b: fields[a]})
    assert p1_commit.commitment_of(swapped) != echo


def test_the_stream_is_quantum_films_encoding_of_strs_and_ints():
    assert p1_commit.stream("ab", 7, "") == b"s2:ab|i7|s0:"
    assert p1_commit.stream() == b""
    assert p1_commit.stream(0, -3) == b"i0|i-3"


def test_a_strs_length_is_its_bytes_not_its_characters():
    assert p1_commit.stream("é") == b"s2:\xc3\xa9"
    assert p1_commit.stream("中文") == b"s6:" + "中文".encode("utf-8")
    assert p1_commit.stream("a|b", "c") == b"s3:a|b|s1:c"


@pytest.mark.parametrize("part", [True, False, 1.0, None, b"x", ("a",), ["a"], {"a": 1}, 2.5],
                         ids=lambda p: type(p).__name__ + repr(p))
def test_the_stream_holds_strs_and_ints_and_nothing_else(part):
    with pytest.raises(TypeError):
        p1_commit.stream("quantum-film/commitment/v3", part)


@pytest.mark.parametrize("name, bad", [("shots", 1024.0), ("shots", True), ("shots", "1024"), ("pub", 0.0),
                                       ("pub", False), ("salt", b"x"), ("role", 7), ("basis", None)])
def test_a_field_of_the_wrong_type_is_a_typeerror_not_a_commitment(name, bad):
    """Refused by commitment_of for the field named and the types, not by the stream behind it (which refuses a bool
    too, for another reason: the verifier's equivalent mutant)."""
    fields, _ = VECTORS[0]
    kind = "int" if name in ("shots", "pub") else "str"
    with pytest.raises(TypeError, match=f"^{name} must be a {kind}, not a {type(bad).__name__}$"):
        p1_commit.commitment_of(dict(fields, **{name: bad}))


def test_the_fourteen_fields_are_exactly_the_ones_asked():
    fields, _ = VECTORS[0]
    with pytest.raises(TypeError):
        p1_commit.commitment_of({k: v for k, v in fields.items() if k != "salt"})
    with pytest.raises(TypeError):
        p1_commit.commitment_of(dict(fields, extra="x"))
    with pytest.raises(TypeError):
        p1_commit.commitment_v3(*list(fields.values())[:13])
    assert p1_commit.commitment_v3(*fields.values()) == VECTORS[0][1]      # positionally, in the stream's order


def test_the_options_digest_is_the_sha256_of_their_sorted_compact_ascii_json():
    assert p1_commit.options_digest(OPTIONS) == OPTIONS_SHA256
    text = '{"dynamical_decoupling":{"enable":false},"twirling":{"enable_gates":false,"enable_measure":false}}'
    assert hashlib.sha256(text.encode("ascii")).hexdigest() == OPTIONS_SHA256


def test_the_options_digest_ignores_the_order_the_keys_were_written_in_and_nothing_else():
    reordered = {"twirling": {"enable_measure": False, "enable_gates": False}, "dynamical_decoupling": {"enable": False}}
    assert p1_commit.options_digest(reordered) == OPTIONS_SHA256
    assert p1_commit.options_digest({**OPTIONS, "extra": 1}) != OPTIONS_SHA256
    assert p1_commit.options_digest({"dynamical_decoupling": {"enable": True},
                                     "twirling": OPTIONS["twirling"]}) != OPTIONS_SHA256
    assert p1_commit.options_digest({}) == hashlib.sha256(b"{}").hexdigest()


def test_the_options_digest_writes_non_ascii_as_escapes():
    assert p1_commit.options_digest({"a": "é"}) == hashlib.sha256(b'{"a":"\\u00e9"}').hexdigest()
