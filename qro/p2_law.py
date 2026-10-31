"""The law, its twins, every measure's expected value under each, and each measure's class (P2's design, items 2, 3
and 8; P2.1). Standard library and qro only.

THE LAW FILE, `qro-law/1` (`question/law.json` in a crate): one line of canonical compact JSON (qro.canonical.compact:
sorted keys, no space, ASCII) and a line feed, with exactly these keys:
    format       "qro-law/1"
    tile         [L, L], L >= 2 and M = L * L <= 20 (the simulator's bound); site = x * L + y, as Quantum-Film's
    crystals     N, 1 <= N <= M
    denominator  a positive whole number
    layouts      every N-site layout of the M sites exactly once, in itertools.combinations order, each as
                 [[sites...], weight], the weights whole numbers >= 0 summing to the denominator: P(Y) = weight / den
    observables  {name: rational}: a pair observable, a letter X or Y, a qubit, the same letter and a greater qubit,
                 both below M ("X0X1"), its value a rational in the profile's spelling within [-1, 1]
    stock, source  text: which stock the law is, and how it was made
`read` refuses (LawError) any other bytes, so a hostile law file is a refusal, never a crash. The file's digest is the
crate's File's `sha256`, which step 2 holds; step 6 holds the table to the question's own law circuit (P2's design,
item 6.4). The checker never derives a law from a kernel (study QRO-0, section 10).

WHAT `qro-measures/1` NEEDS OF A LAW (`needs`; the lead's note on E2 (6)): its observables exactly X0X1 and Y0Y1, the
set's two coherence measures; every site occupied with positive probability, else the nearest-neighbour correlation
has no expected value; and the sum of P(Y)^2 above 1/D, else linear XEB has no norm. v0's law meets all three.

THE PRODUCER'S SIDE, `law_bytes()`: the law of Quantum-Film's pauli-4x4 shelf from its integer kernel A = 16 K, K(x, y)
= (1/16) sum over the Fermi disc |k|^2 <= 1 of cos(2 pi k.(x - y) / 4), exactly: P(Y) = det(A_Y) / 16^5, in lowest
terms over 4,096; 1,360 of the 4,368 layouts are forbidden. Its two coherences are 2 K_01 = 3/8, with the sign the
source circuit ed767c01bd4b851d... fixes (Quantum-Film, pauli_tile.engine_observables's docstring, READ), and step 6
holds both to that circuit. Only qro.p2_measures.question_files calls it.

THE TWINS (item 2): a model is a distribution over the law's N-site layouts, as whole-number weights over a
denominator, and each named observable's expectation. `law`: the file's table and coherences. `uniform`: 1/D on every
N-site layout, every coherence 0. `dephased`: the law's layouts, every coherence 0. One function, `expected`, gives
every measure's value under any model; no twin is special-cased by name.

THE CLASS (item 3): `integrity` where the law's expected value equals the twin's exactly (a vector measure
componentwise), else `signal`. Computed from the law's bytes and the twin's rule, never read from a crate; memoised by
the law's SHA-256.
"""
import hashlib
import itertools
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from functools import cached_property

from qro import canonical, p1_forms, spelling
from qro import vocabulary as V

FORMAT = "qro-law/1"
MEASURE_SET = "qro-measures/1"
STOCK = "pauli-4x4"
# The source circuit of Quantum-Film's pauli-4x4 shelf, as run (Quantum-Film's compare.py, SOURCE_CIRCUIT, READ):
# the one law circuit this version of P2 knows how to write a law for.
SOURCE_CIRCUIT = "ed767c01bd4b851d08993da80f715676e345fc95a10f3bda05400f738e400b36"
KEYS = ("crystals", "denominator", "format", "layouts", "observables", "source", "stock", "tile")
MAX_SITES = 20                                   # 2^20 amplitudes: past this a dense statevector is the wrong tool
TWINS = tuple(sorted(V.WORDS["twin"]))           # ("dephased", "uniform"): the measure set's twins
MEASURES = tuple(V.WORDS["measure"])             # the measure set's ten measures, in the vocabulary's order
SCALAR = ("n-crystal-share", "forbidden-share", "linear-xeb", "tvd", "nn-pair-correlation", "x0x1", "y0y1")
VECTOR = ("crystals-per-shot", "one-site-occupations", "pair-occupations")
CERTIFIED = ("n-crystal-share", "forbidden-share", "linear-xeb", "x0x1", "y0y1")
COHERENCE = {"x0x1": "X0X1", "y0y1": "Y0Y1"}     # each coherence measure's observable
INTEGRITY, SIGNAL = "integrity", "signal"
_OBSERVABLE = re.compile(r"([XY])(0|[1-9][0-9]*)\1(0|[1-9][0-9]*)", re.ASCII)


class LawError(ValueError):
    """A law file that is not `qro-law/1`, or a law the measure set cannot measure against."""


def observable_pair(name, width):
    """(letter, a, b) of a pair observable's name, a < b < width; LawError for any other name."""
    m = _OBSERVABLE.fullmatch(name) if isinstance(name, str) else None
    if m is None:
        raise LawError(f"{name!r} is no pair observable: a letter X or Y, a qubit, the same letter, a greater qubit")
    a, b = int(m.group(2)), int(m.group(3))
    if not a < b < width:
        raise LawError(f"{name}: its qubits are not two of 0 to {width - 1}, the first below the second")
    return m.group(1), a, b


@dataclass(frozen=True)
class Law:
    L: int
    N: int
    den: int
    layouts: tuple             # every N-site layout, in itertools.combinations order
    weights: tuple             # each layout's weight over den
    observables: dict          # name -> Fraction
    stock: str
    source: str
    digest: str                # the SHA-256 of the file's bytes

    @property
    def M(self):
        return self.L * self.L

    @property
    def D(self):
        return len(self.layouts)

    @cached_property
    def w_max(self):
        return max(self.weights)

    @cached_property
    def weight(self):
        """{layout: weight}, for every N-site layout."""
        return dict(zip(self.layouts, self.weights))

    @cached_property
    def norm(self):
        """sum P(Y)^2 - 1/D, linear XEB's denominator."""
        return Fraction(sum(w * w for w in self.weights), self.den * self.den) - Fraction(1, self.D)

    @cached_property
    def nn_pairs(self):
        """The nearest-neighbour pairs (i, j), i < j, of the periodic L x L tile, site = x * L + y."""
        L = self.L
        return tuple(sorted({tuple(sorted((x * L + y, ((x + dx) % L) * L + (y + dy) % L)))
                             for x in range(L) for y in range(L) for dx, dy in ((1, 0), (0, 1))}))

    def probability(self, layout):
        """P(Y) exactly; 0 for an outcome that is no N-site layout of the tile."""
        return Fraction(self.weight.get(tuple(layout), 0), self.den)


# -- the producer's side: Quantum-Film's pauli-4x4 law from its integer kernel -----------------------------------------
def _det(rows):
    """The determinant of an integer matrix, exactly (Bareiss's fraction-free elimination)."""
    m = [list(r) for r in rows]
    n, sign, prev = len(m), 1, 1
    for k in range(n - 1):
        if m[k][k] == 0:
            swap = next((r for r in range(k + 1, n) if m[r][k] != 0), None)
            if swap is None:
                return 0
            m[k], m[swap] = m[swap], m[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                m[i][j] = (m[i][j] * m[k][k] - m[i][k] * m[k][j]) // prev
        prev = m[k][k]
    return sign * m[n - 1][n - 1]


def kernel():
    """A = 16 K for pauli-4x4, as integers: K(x, y) = (1/16) sum over the disc |k|^2 <= 1 of cos(2 pi k.(x - y) / 4),
    site = x * 4 + y. Every cos(2 pi m / 4) is an integer, so A is exact."""
    L, cos = 4, (1, 0, -1, 0)
    ks = range(-L // 2, L - L // 2)
    disc = [(kx, ky) for kx in ks for ky in ks if kx * kx + ky * ky <= 1]
    sites = [divmod(s, L) for s in range(L * L)]
    return tuple(tuple(sum(cos[(kx * (xi - xj) + ky * (yi - yj)) % L] for kx, ky in disc) for xj, yj in sites)
                 for xi, yi in sites)


def law_parts():
    """(L, N, denominator, layouts, weights, observables) of pauli-4x4's law, exactly, from its integer kernel."""
    A = kernel()
    M = len(A)
    N = sum(A[i][i] for i in range(M)) // M          # the trace of K is N: each A_ii is the disc's size, 5
    layouts = tuple(itertools.combinations(range(M), N))
    dets = [_det([[A[i][j] for j in Y] for i in Y]) for Y in layouts]
    scale = M ** N
    if min(dets) < 0 or sum(dets) != scale:
        raise ArithmeticError(f"the minors are not a projection kernel's: sum {sum(dets)}, least {min(dets)}")
    g = math.gcd(scale, *dets)
    coherence = Fraction(2 * A[0][1], M)             # 2 K_01, with the source circuit's sign (held by step 6)
    return 4, N, scale // g, layouts, tuple(d // g for d in dets), {"X0X1": coherence, "Y0Y1": coherence}


def write(L, N, den, layouts, weights, observables, stock, source):
    """The bytes of a law file: canonical compact JSON and a line feed. They are read back by `read` before they are
    returned, so the writer never writes what the reader refuses."""
    data = canonical.compact({"crystals": N, "denominator": den, "format": FORMAT,
                              "layouts": [[list(Y), w] for Y, w in zip(layouts, weights)],
                              "observables": {k: spelling.rational(v) for k, v in observables.items()},
                              "source": source, "stock": stock, "tile": [L, L]})
    read(data)
    return data


SOURCE_TEXT = ("det(A_Y) of the integer kernel A = 16 K of Quantum-Film's pauli-4x4 shelf (the Fermi disc |k|^2 <= 1 "
               "on the periodic 4 x 4 tile, site = x * 4 + y), over 16^5 in lowest terms; the coherences 2 K_01, with "
               "the sign of the source circuit ed767c01bd4b851d")


def law_bytes():
    """The pauli-4x4 law file, made from its integer kernel: what qro.p2_measures.question_files writes."""
    L, N, den, layouts, weights, observables = law_parts()
    return write(L, N, den, layouts, weights, observables, STOCK, SOURCE_TEXT)


# -- the reader --------------------------------------------------------------------------------------------------------
def _whole(x):
    return type(x) is int


def read(data):
    """The Law in a law file's bytes, or LawError: the bytes are `qro-law/1` in canonical compact JSON, as the module
    docstring states the form."""
    if not isinstance(data, (bytes, bytearray)):
        raise LawError("a law file is bytes")
    doc = p1_forms.load_json(bytes(data), "the law file", LawError)
    if not isinstance(doc, dict) or sorted(doc) != list(KEYS):
        raise LawError(f"a law file holds exactly the keys {', '.join(KEYS)}")
    try:
        again = canonical.compact(doc)
    except (TypeError, ValueError):
        raise LawError("the law file holds a value with no canonical spelling") from None
    if again != data:
        raise LawError("the law file is not in its one spelling: canonical compact JSON, sorted keys, no space, "
                       "ASCII, one final line feed")
    if doc["format"] != FORMAT:
        raise LawError(f"the law file's format is {doc['format']!r}, not {FORMAT}")
    tile = doc["tile"]
    if not (isinstance(tile, list) and len(tile) == 2 and all(_whole(t) for t in tile) and tile[0] == tile[1]
            and tile[0] >= 2 and tile[0] * tile[0] <= MAX_SITES):
        raise LawError(f"the tile is [L, L], whole numbers, L >= 2 and L * L at most {MAX_SITES}")
    L = tile[0]
    M = L * L
    N = doc["crystals"]
    if not (_whole(N) and 1 <= N <= M):
        raise LawError(f"crystals is a whole number from 1 to {M}")
    den = doc["denominator"]
    if not (_whole(den) and den >= 1):
        raise LawError("the denominator is a positive whole number")
    rows = doc["layouts"]
    if not isinstance(rows, list):
        raise LawError("layouts is a list")
    layouts, weights = [], []
    expected = itertools.combinations(range(M), N)
    for i, row in enumerate(rows):
        Y = next(expected, None)
        if Y is None:
            raise LawError(f"layouts holds more than the {math.comb(M, N)} layouts of {N} of {M} sites")
        if not (isinstance(row, list) and len(row) == 2 and row[0] == list(Y)
                and all(_whole(s) for s in row[0]) and _whole(row[1]) and row[1] >= 0):
            raise LawError(f"layouts[{i}] is not [{list(Y)}, a whole weight]: every layout once, in combinations order")
        layouts.append(Y)
        weights.append(row[1])
    if next(expected, None) is not None:
        raise LawError(f"layouts holds {len(rows)} of the {math.comb(M, N)} layouts of {N} of {M} sites")
    if sum(weights) != den:
        raise LawError(f"the weights sum to {sum(weights)}, not the denominator {den}")
    obs = doc["observables"]
    if not isinstance(obs, dict):
        raise LawError("observables is an object")
    observables = {}
    for name, value in obs.items():
        observable_pair(name, M)
        if spelling.problem("rational", value):
            raise LawError(f"the observable {name} is not a rational in the profile's spelling")
        q = Fraction(value)
        if not -1 <= q <= 1:
            raise LawError(f"the observable {name} is {value}, outside [-1, 1]")
        observables[name] = q
    for key in ("stock", "source"):
        if spelling.problem("text", doc[key]):
            raise LawError(f"the law file's {key} is not text")
    return Law(L, N, den, tuple(layouts), tuple(weights), observables, doc["stock"], doc["source"],
               hashlib.sha256(data).hexdigest())


def needs(law):
    """LawError unless `qro-measures/1` can measure against the law: its observables exactly the set's two, every site
    occupied with positive probability, and a nonzero linear XEB norm (the lead's note on E2 (6))."""
    if sorted(law.observables) != sorted(COHERENCE.values()):
        raise LawError(f"{MEASURE_SET} measures against a law whose observables are exactly "
                       f"{', '.join(sorted(COHERENCE.values()))}; this one names "
                       f"{', '.join(sorted(law.observables)) or 'none'}")
    one = _sites(law.layouts, law.weights, law.M)
    empty = [i for i in range(law.M) if not one[i]]
    if empty:
        raise LawError(f"the law never occupies the sites {empty}, so the nearest-neighbour correlation has no "
                       "expected value under it")
    if law.norm <= 0:
        raise LawError("the sum of P(Y)^2 is not above 1/D, so linear XEB has no norm under this law")


# -- models, expected values, classes ----------------------------------------------------------------------------------
@dataclass(frozen=True)
class Model:
    weights: tuple             # aligned with the law's layouts, whole numbers
    den: int
    coherences: dict           # observable name -> Fraction


def model_of(name, law):
    """The model a name gives, from the law: the law itself, or one of the measure set's twins by its rule."""
    if name == "law":
        return Model(law.weights, law.den, dict(law.observables))
    if name == "uniform":
        return Model((1,) * law.D, law.D, {k: Fraction(0) for k in law.observables})
    if name == "dephased":
        return Model(law.weights, law.den, {k: Fraction(0) for k in law.observables})
    raise LawError(f"{name!r} is no model of {MEASURE_SET}")


def _sites(layouts, weights, M):
    one = [0] * M
    for Y, w in zip(layouts, weights):
        for i in Y:
            one[i] += w
    return one


def expected(model, law):
    """{measure: its expected value under the model}, for every measure of the set: a Fraction for a scalar measure, a
    tuple of Fractions for a vector one. One function for every model."""
    W, den, D, M = model.weights, model.den, law.D, law.M
    total = sum(W)
    one = _sites(law.layouts, W, M)
    pair = {}
    for Y, w in zip(law.layouts, W):
        if w:
            for p in itertools.combinations(Y, 2):
                pair[p] = pair.get(p, 0) + w
    out = {"n-crystal-share": Fraction(total, den),
           "forbidden-share": Fraction(sum(w for w, lw in zip(W, law.weights) if lw == 0), total),
           "linear-xeb": (Fraction(sum(w * lw for w, lw in zip(W, law.weights)), den * law.den) - Fraction(1, D))
           / law.norm,
           "tvd": Fraction(sum(abs(w * law.den - lw * den) for w, lw in zip(W, law.weights)), 2 * den * law.den),
           "nn-pair-correlation": sum((Fraction(pair.get(p, 0) * den, one[p[0]] * one[p[1]]) for p in law.nn_pairs),
                                      Fraction(0)) / len(law.nn_pairs),
           "crystals-per-shot": tuple(Fraction(total, den) if k == law.N else Fraction(0) for k in range(M + 1)),
           "one-site-occupations": tuple(Fraction(x, den) for x in one),
           "pair-occupations": tuple(Fraction(pair.get(p, 0), den) for p in itertools.combinations(range(M), 2))}
    for measure, name in COHERENCE.items():
        out[measure] = model.coherences[name]
    return out


def classify(law_value, twin_value):
    """`integrity` where the two expected values are equal exactly (a tuple componentwise), else `signal`."""
    return INTEGRITY if law_value == twin_value else SIGNAL


@dataclass(frozen=True)
class Contrast:
    measure: str
    twin: str
    cls: str
    law_value: object          # a Fraction for a scalar measure; None for a vector one, which carries a class only
    twin_value: object


_CLASSES = {}                  # the law's digest -> its contrasts; a pure function of the law's bytes


def classes(law):
    """{(measure, twin): Contrast} over the measure set and its twins, computed from the law alone and memoised by its
    digest (P2's design, item 3)."""
    got = _CLASSES.get(law.digest)
    if got is None:
        needs(law)
        e_law = expected(model_of("law", law), law)
        got = {}
        for twin in TWINS:
            e_twin = expected(model_of(twin, law), law)
            for m in MEASURES:
                scalar = m in SCALAR
                got[(m, twin)] = Contrast(m, twin, classify(e_law[m], e_twin[m]), e_law[m] if scalar else None,
                                          e_twin[m] if scalar else None)
        if len(_CLASSES) >= 64:
            _CLASSES.pop(next(iter(_CLASSES)))
        _CLASSES[law.digest] = got
    return got


def clear():
    _CLASSES.clear()
