"""The decode rules, reimplemented, and what holds a bit order (P1's design, item 4; P1.1). Standard library only.

A decode rule reads a raw result's bytes into outcomes: for each shot, the set of logical qubits that read 1. It is
Quantum-Film's rule, written again here from its statement and held to the same facts, so that step 5 re-decodes
the raw bytes under the rule the crate names and never reads Quantum-Film's decoded counts or its verdict files.

RULES is keyed by the rule's name, which a decode carries as `qro:decodeRule`. A rule's name is its version: a
change to a rule is a new key, never an edit under the old name.

  quantum_film.ibm.decode/v1   reads `ibm-sampler-result/v1`. A shot is a 16-bit big-endian integer v.
      `msb-first` (the rule): logical qubit i read 1 iff bit i of v is set; the sampler's bitstring is written most
      significant bit first, so its leftmost character is classical bit 15. `lsb-first` (the mirror): iff bit
      15 - i is set.
  quantum_film.atlas.decode/v1   reads `atlas-tomography-result/v1` and `atlas-known-answer-vector/v1`. A count
      string is little-endian over [the setting's non-I qubits, ascending] + [every other qubit, ascending], while
      the setting's label is written in circuit order, qubit 0 rightmost (`atlas-register`, the rule); or it is
      the plain circuit order, position p holding qubit 15 - p (`circuit-order`).

A bit order is held by a known answer: a circuit whose result is known, whose decode under the declared order must
come out as the known result.
  - IBM: the expected set is read from the known-answer circuit's own text (never from Quantum-Film's verdict
    file, its manifest or its decoded counts), and the order holds iff the modal outcome is exactly that set and
    has strictly more shots than its mirror. A tie decides nothing. A set that is its own mirror tells no order
    from its mirror, so it is refused.
  - Atlas: the frozen vector's 128 Z-basis positions each read the frequency the vector's circuit prepares, within
    4 standard deviations, in exact integer arithmetic.
"""
import re
import struct
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from qro import p1_forms, reader, spelling
from qro.p1_graph import GraphError, Index

IBM_RULE = "quantum_film.ibm.decode/v1"
ATLAS_RULE = "quantum_film.atlas.decode/v1"
M = 16                                    # a v0 outcome is 16 qubits wide
CHUNK = 1 << 16                           # the rows tallied at a time
ATLAS_Z2_MAX = 16                         # a position passes iff its z squared is at most 16: |z| <= 4


class DecodeError(ValueError):
    """The bytes, or the graph, cannot be read under the rule named."""


class KnownAnswerError(ValueError):
    """A known-answer circuit, or a set of counts, that cannot tell one bit order from its mirror."""


@dataclass(frozen=True)
class Rule:
    name: str
    forms: frozenset            # the raw forms the rule reads
    order: str                  # the order the rule itself reads
    orders: frozenset           # the orders it admits: its own, and the one it is told apart from by a known answer


RULES = {
    IBM_RULE: Rule(IBM_RULE, frozenset({"ibm-sampler-result/v1"}), "msb-first", frozenset({"msb-first", "lsb-first"})),
    ATLAS_RULE: Rule(ATLAS_RULE, frozenset({"atlas-tomography-result/v1", "atlas-known-answer-vector/v1"}),
                     "atlas-register", frozenset({"atlas-register", "circuit-order"})),
}


# -- IBM -------------------------------------------------------------------------------------------------------
def _outcome(v, mirror):
    return tuple(i for i in range(M) if (v >> (M - 1 - i if mirror else i)) & 1)


def ibm_counts(pub, order):
    """{the sorted tuple of qubits that read 1: shots} over one PUB's rows, under `order`, sorted by outcome."""
    if not isinstance(order, str) or order not in RULES[IBM_RULE].orders:
        raise DecodeError(f"{IBM_RULE} does not read the order {order}")
    mirror = order == "lsb-first"
    tally = Counter()
    for start in range(0, pub.rows, CHUNK):               # a chunk at a time: memory does not grow with the shots
        n = min(CHUNK, pub.rows - start)
        tally.update(struct.unpack(f">{n}H", pub.body[2 * start:2 * (start + n)]))
    out = {}
    for v, n in tally.items():
        key = _outcome(v, mirror)
        out[key] = out.get(key, 0) + n
    return dict(sorted(out.items()))


_X = re.compile(r"x q\[(0|[1-9][0-9]*)\];", re.ASCII)
_HEADER = ["OPENQASM 2.0;", 'include "qelib1.inc";', f"qreg q[{M}];", f"creg meas[{M}];"]
_BARRIER = "barrier " + ",".join(f"q[{i}]" for i in range(M)) + ";"
_MEASURES = [f"measure q[{i}] -> meas[{i}];" for i in range(M)]


def expected_set(qasm):
    """The qubits a known-answer circuit flips, read from its text: Quantum-Film's header, then `x q[i];` lines in
    strictly increasing order, then a barrier on all 16 qubits and a measure of each into its own bit. The bytes of
    any other circuit are refused: KnownAnswerError."""
    try:
        text = qasm.decode("ascii")
    except UnicodeDecodeError:
        raise KnownAnswerError("the known-answer circuit is not ASCII") from None
    if not text.endswith("\n"):
        raise KnownAnswerError("the known-answer circuit does not end in a line feed")
    lines = text[:-1].split("\n")
    if lines[:len(_HEADER)] != _HEADER:
        raise KnownAnswerError("the known-answer circuit does not open with Quantum-Film's header")
    flipped, i = [], len(_HEADER)
    while i < len(lines) and _X.fullmatch(lines[i]):
        if len(flipped) == M:                     # at most one x line a qubit: a longer run is refused unread
            raise KnownAnswerError("the known-answer circuit has more x lines than qubits")
        flipped.append(int(_X.fullmatch(lines[i]).group(1)))
        i += 1
    if lines[i:] != [_BARRIER] + _MEASURES:
        raise KnownAnswerError("the known-answer circuit is not x lines, a barrier on all 16 qubits, and 16 measures")
    if any(not 0 <= q < M for q in flipped) or any(a >= b for a, b in zip(flipped, flipped[1:])):
        raise KnownAnswerError("the known-answer circuit's x lines are not strictly increasing qubits of 0 to 15")
    return tuple(flipped)


@dataclass(frozen=True)
class Verdict:
    holds: bool
    expected: tuple             # the set the circuit flips
    mirror: tuple               # q -> 15 - q of it
    modal: tuple                # the outcome with the most shots, ties to the smaller tuple
    n_expected: int
    n_mirror: int
    shots: int

    @property
    def share(self):
        return Fraction(self.n_expected, self.shots)

    @property
    def mirror_share(self):
        return Fraction(self.n_mirror, self.shots)

    def text(self):
        return (f"the expected set {list(self.expected)} has {self.n_expected} of {self.shots} shots "
                f"({self.share.numerator}/{self.share.denominator}), its mirror {list(self.mirror)} has "
                f"{self.n_mirror} ({self.mirror_share.numerator}/{self.mirror_share.denominator}), and the modal "
                f"outcome is {list(self.modal)}")


def known_answer_verdict(counts, expected, width=M):
    """Did a known-answer run read in this order? It holds iff the most frequent outcome (ties to the smaller
    tuple) is exactly the expected set, with strictly more shots than its mirror q -> width - 1 - q. KnownAnswerError
    for a set that is its own mirror, and for no shots."""
    want = tuple(sorted(expected))
    mirror = tuple(sorted(width - 1 - q for q in want))
    if want == mirror:
        raise KnownAnswerError(f"{list(want)} is its own mirror: a known answer must tell the orders apart")
    total = sum(counts.values())
    if total < 1:
        raise KnownAnswerError("no shots to judge")
    modal = min(counts, key=lambda k: (-counts[k], k))
    n_want, n_mirror = counts.get(want, 0), counts.get(mirror, 0)
    return Verdict(modal == want and n_want > n_mirror, want, mirror, modal, n_want, n_mirror, total)


# -- Atlas -----------------------------------------------------------------------------------------------------
def atlas_order(label, order):
    """For each string position p (0 = leftmost), the circuit qubit it holds, under `order`."""
    if not isinstance(order, str) or order not in RULES[ATLAS_RULE].orders:
        raise DecodeError(f"{ATLAS_RULE} does not read the order {order}")
    n = len(label)
    if order == "circuit-order":
        return [n - 1 - p for p in range(n)]
    active = sorted(n - 1 - p for p, ch in enumerate(label) if ch != "I")
    clbits = active + sorted(set(range(n)) - set(active))
    return [clbits[n - 1 - p] for p in range(n)]


def basis_of(label, q):
    """The basis circuit qubit q was measured in, in the setting `label`: I means Z, measured without a rotation."""
    ch = label[len(label) - 1 - q]
    return "Z" if ch == "I" else ch


def z_setting(result):
    """The one setting that measured every qubit in Z. DecodeError if there is not exactly one."""
    zs = [label for label in result.settings if set(label) <= {"Z", "I"}]
    if len(zs) != 1:
        raise DecodeError(f"expected exactly one all-Z setting, found {zs}")
    return zs[0]


def atlas_layouts(result, order="atlas-register"):
    """{the sorted tuple of occupied qubits: shots} from the all-Z setting of an Atlas result: whole-register
    crystal layouts, as Quantum-Film's layouts()."""
    label = z_setting(result)
    pos2q = atlas_order(label, order)
    out = {}
    for s, c in result.settings[label].counts.items():
        occ = tuple(sorted(pos2q[p] for p, ch in enumerate(s) if ch == "1"))
        out[occ] = out.get(occ, 0) + c
    return dict(sorted(out.items()))


@dataclass(frozen=True)
class VectorVerdict:
    holds: bool
    compared: int               # the Z-basis positions compared
    worst: Fraction             # the largest z squared among them, exact
    failed: tuple               # (label, position, qubit, z squared) of each position past the bound

    def text(self):
        if not self.compared:
            return "the vector has no Z-basis position to compare"
        w = self.worst
        return (f"{len(self.failed)} of {self.compared} Z-basis positions are past |z| = 4; the worst z squared is "
                f"{w.numerator}/{w.denominator}")


def atlas_vector_verdict(vector, order):
    """Is the frozen known-answer vector read right under `order`? Qubit q of the vector's circuit reads 1 with
    frequency (2q + 1)/32 (Quantum-Film's calibration of it). Each Z-basis position, in each setting, must read
    that frequency within 4 standard deviations, in exact integers: with c ones among n shots,
    (32c - n(2q + 1))^2 <= 16 n (2q + 1)(31 - 2q). X positions have an irrational expectation and Y positions read
    1/2 on every qubit: neither is compared, and each is a stated limit."""
    compared, failed, worst = 0, [], Fraction(0)
    for label, setting in vector.settings.items():
        pos2q = atlas_order(label, order)
        ones = [0] * len(label)
        for s, c in setting.counts.items():
            for p, ch in enumerate(s):
                if ch == "1":
                    ones[p] += c
        for p, q in enumerate(pos2q):
            if basis_of(label, q) != "Z":
                continue
            top = (32 * ones[p] - setting.shots * (2 * q + 1)) ** 2
            bottom = setting.shots * (2 * q + 1) * (31 - 2 * q)
            z2 = Fraction(top, bottom)
            compared += 1
            worst = max(worst, z2)
            if top > ATLAS_Z2_MAX * bottom:
                failed.append((label, p, q, z2))
    return VectorVerdict(compared > 0 and not failed, compared, worst, tuple(failed))


# -- the rules, by name ----------------------------------------------------------------------------------------
def decode_counts(rule, parsed, pub_index, order):
    """{outcome: shots} for one Pub of a parsed raw result, under the rule and the order a decode names."""
    if rule == IBM_RULE:
        if pub_index >= len(parsed.pubs):
            raise DecodeError(f"PUB {pub_index} is outside a result of {len(parsed.pubs)} PUBs")
        return ibm_counts(parsed.pubs[pub_index], order)
    if rule == ATLAS_RULE:
        return atlas_layouts(parsed, order)
    raise DecodeError(f"no decode rule {rule} is built")


def account(rule, parsed, order, roles):
    """The rule accounts for a whole raw result, or DecodeError: IBM, every PUB reads under the order (the caller has
    held the order to the ones the rule admits, and a result that parsed has PUBs of 16 bits, so this branch is a
    check that the rule can read what the form holds and has no refusal of its own to give today); Atlas, a law Pub's
    result has exactly one all-Z setting and its layouts read."""
    if rule == IBM_RULE:
        for pub in parsed.pubs:
            ibm_counts(pub, order)
    elif rule == ATLAS_RULE:
        if "law" in roles:
            atlas_layouts(parsed, order)
    else:
        raise DecodeError(f"no decode rule {rule} is built")


def crate_file(crate_dir, entity, what):
    """The bytes of a File the crate holds, named by its @id as a path in the crate. GraphError for any other entity:
    not a File of the crate, or an @id that is not a path (the reader holds every File's @id to that at step 1; a
    generator's entities and a caller's are held to it here, so that no @id reads a file outside the crate)."""
    i = entity["@id"]
    if not reader.local_file(entity) or spelling.path_problem(i):
        raise GraphError(f"{what} {i} is not a file the crate holds")
    return Path(crate_dir).joinpath(*i.split("/")).read_bytes()


def pub_counts(crate_dir, md, pub_id):
    """The decoded counts of one Pub, {the sorted tuple of qubits read 1: shots}, from its raw result's bytes alone:
    the Pub's job, that job's raw result, and the decode that reads it, found in the graph; the bytes read from the
    crate and parsed by the raw form they name; and the shots counted under the rule and the bit order the decode
    declares. `md` is the checker's parsed metadata, or `{"@graph": [entities]}` a generator has built while the
    crate is being made. It never opens Quantum-Film's record or verdict files, so a changed record cannot move a
    measure, and step 5 has held the order (P2's design, found 2). For the Atlas rule it returns the all-Z
    setting's layouts, in the same shape.

    GraphError for a relation the graph lacks, or an entity of the graph that is not as the model says; RawFormError
    for bytes not in their form; DecodeError for a rule, an order or a raw form not built, whatever the value a
    malformed entity gives it (a list or an object too): all three are ValueErrors, and nothing else of a graph or a
    value raises from here but the host's own: an OSError for a file the graph names and the crate lacks (or a user
    may not read), and a MemoryError."""
    idx = Index(md)
    pub = idx.get(pub_id, "qro:Pub")
    raw = idx.raw_of(idx.job_of(pub))
    decode = idx.decode_of(raw)
    rule, order, form = decode.get("qro:decodeRule"), decode.get("qro:bitOrder"), raw.get("qro:rawForm")
    if not isinstance(rule, str) or rule not in RULES:
        raise DecodeError(f"{decode['@id']}: no decode rule {rule} is built")
    if not isinstance(form, str) or form not in RULES[rule].forms:
        raise DecodeError(f"{raw['@id']}: the rule {rule} does not read the raw form {form}")
    parsed = p1_forms.parse_raw(form, crate_file(crate_dir, raw, "the raw result"))
    return decode_counts(rule, parsed, idx.pub_index(pub) if rule == IBM_RULE else None, order)
