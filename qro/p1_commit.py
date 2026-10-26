"""Quantum-Film's commitment v3, recomputed (P1's design, item 3; P1.1). Standard library only.

A PUB's commitment is the SHA-256 of one byte stream over fourteen defining fields. Quantum-Film puts it in the
circuit's metadata before submitting, and IBM echoes it back inside the result of every PUB. This module is the
recomputation; step 4 (qro/p1_steps.py) holds its result to the claim, the job line and IBM's echo, and holds each
field to a counterpart the crate has of its own.

The stream, read from Quantum-Film's fixer.py and golden/uniform.py: the version string and the fourteen fields, in
this order, each a str written `s<byte length>:<its UTF-8 bytes>` or an int written `i<decimal>`, joined by `|`.
A bool is refused (it is an int in Python, and no field is one), and so is anything but a str or an int. The
fourteen are FIELDS below, in order. Recomputing all 68 PUBs of Quantum-Film's 65 jobs gave IBM's echo for each of
them (P1's design, measurement 1).
"""
import hashlib
import json

COMMITMENT_V3 = "quantum-film/commitment/v3"
# The fields the stream binds after the version, in order, and the type each takes.
FIELDS = (("stock", str), ("role", str), ("basis", str), ("kind", str), ("route", str), ("backend", str),
          ("program", str), ("pub", int), ("circuit_sha256", str), ("isa_sha256", str), ("shots", int),
          ("options_sha256", str), ("decode", str), ("salt", str))


def stream(*parts):
    """Quantum-Film's byte stream of a list of strs and ints."""
    out = []
    for p in parts:
        if type(p) is str:
            b = p.encode("utf-8")
            out.append(b"s%d:%s" % (len(b), b))
        elif type(p) is int:
            out.append(b"i%d" % p)
        else:
            raise TypeError(f"a stream holds strs and ints, not {type(p).__name__}")
    return b"|".join(out)


def commitment_v3(stock, role, basis, kind, route, backend, program, pub, circuit_sha256, isa_sha256, shots,
                  options_sha256, decode, salt):
    """The commitment, as 64 lowercase hex digits, of the fourteen fields, each of the type FIELDS gives it."""
    return hashlib.sha256(stream(COMMITMENT_V3, stock, role, basis, kind, route, backend, program, pub,
                                 circuit_sha256, isa_sha256, shots, options_sha256, decode, salt)).hexdigest()


def options_digest(options):
    """The SHA-256 of a submission's options as Quantum-Film digests them: their JSON with sorted keys, no white
    space, ASCII."""
    return hashlib.sha256(json.dumps(options, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode("ascii")).hexdigest()


def commitment_of(fields):
    """The commitment of a mapping holding exactly FIELDS' fourteen names, each of its type: TypeError otherwise."""
    if set(fields) != {name for name, _ in FIELDS}:
        raise TypeError(f"the fourteen fields are {[n for n, _ in FIELDS]}")
    for name, kind in FIELDS:
        if type(fields[name]) is not kind:
            raise TypeError(f"{name} must be a {kind.__name__}, not a {type(fields[name]).__name__}")
    return commitment_v3(**fields)
