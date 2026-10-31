"""The exact hold's simulator: gate lists and logical circuits read strictly, and simulated in binary64 on the standard
library (P2's design, item 7; P2.1). Standard library and qro only: no numpy, no qiskit, no Quantum-Film.

THE GATE LIST, Quantum-Film's `quantum-film/isa-gates/v1`, read as its own check reads it (Quantum-Film's isa.py,
read() and _simulate(), READ; the lead's E2 (4)): exactly the keys format, num_qubits, num_clbits, global_phase, layout
and gates; positive whole widths; a finite float global_phase; layout {initial, final, routing_permutation}, lists of
whole numbers, initial and final each num_clbits distinct qubits in range; each gate [name, [qubits], [clbits],
[params]] with name one of rz, sx, x, cz, measure, barrier, in range, finite float parameters, rz one qubit and one
parameter, sx and x one qubit, cz two distinct, measure one qubit into one clbit, a barrier distinct qubits and
nothing else; a clbit measured once, no gate on a qubit after its measurement, every clbit measured; at most 20 active
qubits (those a gate other than a barrier touches) and at most 100,000 gates. Matrices are qiskit's, as isa.py states
them: rz(t) = diag(e^(-it/2), e^(it/2)), sx = [[1+i, 1-i], [1-i, 1+i]] / 2, x, cz = diag(1, 1, 1, -1).

THE LOGICAL CIRCUIT, a subset of OpenQASM 2 (the lead's E2 (5); all 126 of v0's QASM files, 5 distinct, fit it):
ASCII, LF, one final LF, no blank or comment line; `OPENQASM 2.0;`, `include "qelib1.inc";`, `qreg q[n];` with
1 <= n <= 20, then optionally `creg meas[n];`; then lines `x q[i];`, `h q[i];`, `sdg q[i];`, `cx q[i],q[j];` (i != j),
`ry(<numeral>) q[i];` (the numeral -?(0|[1-9][0-9]*)(.[0-9]+)?(e[-+]?[0-9]+)?, finite), at most 100,000 of these gates,
and `barrier` lines of distinct qubits, at most 100,000 of those; with the creg, after the last of them, exactly the n
lines `measure q[i] -> meas[i];` in order; without it no measure line, and qubit q is bit q. Anything else is a
SimError.

THE SIMULATION (V8 of the design): each run of gates confined to one pair of qubits is fused into one 4x4, a single-
qubit run into the next pair that holds its qubit, else one 2x2; and a light cone: a qubit is a classical bit until the
first block on it that is not a permutation of the basis with phases, tested exactly (a zero is 0.0, nothing smaller),
so the dense state holds only the qubits the circuit has spread to. A phase on a basis state is global and dropped,
which no probability and no Pauli expectation can see. Outcomes are indexed sum of clbit c * 2^c.

THE MEMO (the lead's E2 (11)): a pure function of the bytes read and hashed here (a gate list, by its SHA-256) or of a
logical circuit's width and parsed operations, in process only, an LRU of 64 entries for each kind, emptied by
`clear()`. A logical circuit is simulated in two parts, always: its core, every operation up to its last x, cx or ry,
and then its tail, the trailing h and sdg that change a measurement's basis. Cores are memoised by their operations,
so the coherence circuits, the law circuit's core with a tail, resume from the law circuit's core; and since the split
is the circuit's own, never the memo's, a circuit's distribution is the same bytes whatever the memo held before.
Nothing is read from disk here.
"""
import hashlib
import math
import re
from array import array
from collections import OrderedDict
from dataclasses import dataclass

from qro import p1_forms

GATE_FORMAT = "quantum-film/isa-gates/v1"
GATES = ("rz", "sx", "x", "cz", "measure", "barrier")
_ARITY = {"rz": (1, 0, 1), "sx": (1, 0, 0), "x": (1, 0, 0), "cz": (2, 0, 0), "measure": (1, 1, 0)}
_KEYS = {"format", "num_qubits", "num_clbits", "global_phase", "layout", "gates"}
MAX_ACTIVE = 20               # 2^20 amplitudes: past this a dense statevector is the wrong tool (isa.py's MAX_ACTIVE)
MAX_GATES = 100_000
MAX_QUBITS = 20


class SimError(ValueError):
    """A gate list or a logical circuit this simulator does not read."""


# -- matrices: U[out][in], |0> at 0; a 4x4 on a pair (a, b) indexed 2 * bit_a + bit_b --------------------------------
I2 = ((1 + 0j, 0j), (0j, 1 + 0j))
X = ((0j, 1 + 0j), (1 + 0j, 0j))
SX = ((0.5 + 0.5j, 0.5 - 0.5j), (0.5 - 0.5j, 0.5 + 0.5j))
_R = 1 / math.sqrt(2)
H = ((_R + 0j, _R + 0j), (_R + 0j, -_R + 0j))
SDG = ((1 + 0j, 0j), (0j, -1j))
CZ = ((1 + 0j, 0j, 0j, 0j), (0j, 1 + 0j, 0j, 0j), (0j, 0j, 1 + 0j, 0j), (0j, 0j, 0j, -1 + 0j))
CX = ((1 + 0j, 0j, 0j, 0j), (0j, 1 + 0j, 0j, 0j), (0j, 0j, 0j, 1 + 0j), (0j, 0j, 1 + 0j, 0j))   # control a, target b


def rz(t):
    return ((complex(math.cos(t / 2), -math.sin(t / 2)), 0j), (0j, complex(math.cos(t / 2), math.sin(t / 2))))


def ry(t):
    c, s = math.cos(t / 2), math.sin(t / 2)
    return ((complex(c), complex(-s)), (complex(s), complex(c)))


def mul(a, b):
    n = len(a)
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(n)) for j in range(n)) for i in range(n))


def kron(a, b):
    """a on the pair's first qubit, b on its second, for the index 2 * bit_first + bit_second."""
    return tuple(tuple(a[i // 2][j // 2] * b[i % 2][j % 2] for j in range(4)) for i in range(4))


_SWAP = (0, 2, 1, 3)


def swapped(U):
    """A 4x4 on (a, b) re-indexed for (b, a)."""
    return tuple(tuple(U[_SWAP[i]][_SWAP[j]] for j in range(4)) for i in range(4))


def monomial(U):
    """Whether U permutes the basis with phases: one nonzero in every row and every column, exactly."""
    n = len(U)
    return all(sum(1 for u in row if u != 0) == 1 for row in U) and \
        all(sum(1 for r in range(n) if U[r][c] != 0) == 1 for c in range(n))


# -- the gate list -----------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class GateList:
    num_qubits: int
    num_clbits: int
    ops: tuple                 # ("1q", qubit, U) or ("2q", a, b, U), physical qubits
    clbits: tuple              # clbit c -> the physical qubit measured into it


def _whole(x):
    return type(x) is int


def _wholes(x):
    return isinstance(x, list) and all(_whole(v) for v in x)


def read_gate_list(data):
    """A GateList from a gate list's bytes, or SimError, as the module docstring states the form."""
    doc = p1_forms.load_json(bytes(data), "the gate list", SimError)
    if not isinstance(doc, dict) or set(doc) != _KEYS:
        raise SimError(f"a gate list carries exactly {sorted(_KEYS)}")
    if doc["format"] != GATE_FORMAT:
        raise SimError(f"the gate list's format is {doc['format']!r}, not {GATE_FORMAT}")
    n, m = doc["num_qubits"], doc["num_clbits"]
    if not (_whole(n) and n >= 1 and _whole(m) and m >= 1):
        raise SimError("num_qubits and num_clbits are positive whole numbers")
    if not (type(doc["global_phase"]) is float and math.isfinite(doc["global_phase"])):
        raise SimError("global_phase is a finite float")
    lay = doc["layout"]
    if not (isinstance(lay, dict) and set(lay) == {"initial", "final", "routing_permutation"}
            and all(_wholes(lay[k]) for k in lay)):
        raise SimError("layout is {initial, final, routing_permutation}, each a list of whole numbers")
    for k in ("initial", "final"):
        if len(lay[k]) != m or len(set(lay[k])) != m or not all(0 <= q < n for q in lay[k]):
            raise SimError(f"layout {k} names {m} distinct physical qubits of the circuit")
    gates = doc["gates"]
    if not isinstance(gates, list):
        raise SimError("gates is a list")
    if len(gates) > MAX_GATES:
        raise SimError(f"{len(gates)} gates; the exact hold reads at most {MAX_GATES}")
    ops, measured, clbit_of, active = [], set(), {}, set()
    for i, g in enumerate(gates):
        if not (isinstance(g, list) and len(g) == 4 and isinstance(g[0], str) and _wholes(g[1]) and _wholes(g[2])
                and isinstance(g[3], list)):
            raise SimError(f"gate {i}: not [name, [qubits], [clbits], [params]]")
        name, qs, cs, ps = g
        if name not in GATES:
            raise SimError(f"gate {i}: {name!r} is not one of the gates the exact hold reads, {', '.join(GATES)}")
        if not all(0 <= q < n for q in qs) or not all(0 <= c < m for c in cs):
            raise SimError(f"gate {i}: {name} on a qubit or clbit outside the circuit")
        if not all(type(p) is float and math.isfinite(p) for p in ps):
            raise SimError(f"gate {i}: {name} has a parameter that is not a finite float")
        if name == "barrier":
            if cs or ps or len(set(qs)) != len(qs):
                raise SimError(f"gate {i}: a barrier has distinct qubits, no clbits and no parameters")
            continue
        if (len(qs), len(cs), len(ps)) != _ARITY[name] or len(set(qs)) != len(qs):
            nq, nc, npar = _ARITY[name]
            raise SimError(f"gate {i}: {name} takes {nq} distinct qubit(s), {nc} clbit(s) and {npar} parameter(s)")
        for q in qs:
            if q in measured:
                raise SimError(f"gate {i}: {name} on qubit {q} after its measurement")
        active.update(qs)
        if name == "measure":
            if cs[0] in clbit_of:
                raise SimError(f"gate {i}: clbit {cs[0]} is measured twice")
            measured.add(qs[0])
            clbit_of[cs[0]] = qs[0]
        elif name == "cz":
            ops.append(("2q", qs[0], qs[1], CZ))
        else:
            ops.append(("1q", qs[0], {"sx": SX, "x": X}[name] if name != "rz" else rz(ps[0])))
    if len(active) > MAX_ACTIVE:
        raise SimError(f"{len(active)} active qubits; the exact hold simulates at most {MAX_ACTIVE}")
    missing = [c for c in range(m) if c not in clbit_of]
    if missing:
        raise SimError(f"the clbits {missing[:8]} are never measured")
    return GateList(n, m, tuple(ops), tuple(clbit_of[c] for c in range(m)))


# -- the logical circuit -----------------------------------------------------------------------------------------------
_INDEX = r"(0|[1-9][0-9]*)"
_HEAD = ("OPENQASM 2.0;", 'include "qelib1.inc";')
_QREG = re.compile(rf"qreg q\[{_INDEX}\];", re.ASCII)
_CREG = re.compile(rf"creg meas\[{_INDEX}\];", re.ASCII)
_ONE = re.compile(rf"(x|h|sdg) q\[{_INDEX}\];", re.ASCII)
_CX = re.compile(rf"cx q\[{_INDEX}\],q\[{_INDEX}\];", re.ASCII)
_RY = re.compile(rf"ry\((-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:e[-+]?[0-9]+)?)\) q\[{_INDEX}\];", re.ASCII)
_BARRIER = re.compile(rf"barrier q\[{_INDEX}\](?:,q\[{_INDEX}\])*;", re.ASCII)


@dataclass(frozen=True)
class Circuit:
    n: int
    ops: tuple                 # ("x", q), ("h", q), ("sdg", q), ("cx", c, t), ("ry", q, angle): the memo's key
    measured: bool


def read_qasm(data):
    """A Circuit from a logical circuit's bytes, or SimError, as the module docstring states the subset."""
    try:
        text = bytes(data).decode("ascii")
    except UnicodeDecodeError:
        raise SimError("the circuit is not ASCII") from None
    if not text.endswith("\n") or "\r" in text:
        raise SimError("the circuit's lines end in LF alone, the last one too")
    lines = text[:-1].split("\n")
    if tuple(lines[:2]) != _HEAD or len(lines) < 3 or not _QREG.fullmatch(lines[2]):
        raise SimError('the circuit does not open with OPENQASM 2.0;, include "qelib1.inc"; and qreg q[n];')
    n = int(_QREG.fullmatch(lines[2]).group(1))
    if not 1 <= n <= MAX_QUBITS:
        raise SimError(f"qreg q[{n}]: the exact hold reads 1 to {MAX_QUBITS} qubits")
    i, measured = 3, False
    if i < len(lines) and lines[i].startswith("creg"):
        m = _CREG.fullmatch(lines[i])
        if m is None or int(m.group(1)) != n:
            raise SimError(f"line {i + 1}: the only creg is creg meas[{n}];")
        measured, i = True, i + 1
    ops, barriers = [], 0
    while i < len(lines) and not lines[i].startswith("measure"):
        line, k = lines[i], i + 1
        m1, mc, mr, mb = _ONE.fullmatch(line), _CX.fullmatch(line), _RY.fullmatch(line), _BARRIER.fullmatch(line)
        if m1:
            q = int(m1.group(2))
            if q >= n:
                raise SimError(f"line {k}: qubit {q} is outside q[{n}]")
            ops.append((m1.group(1), q))
        elif mc:
            c, t = int(mc.group(1)), int(mc.group(2))
            if c >= n or t >= n or c == t:
                raise SimError(f"line {k}: cx on two distinct qubits of q[{n}]")
            ops.append(("cx", c, t))
        elif mr:
            angle, q = float(mr.group(1)), int(mr.group(2))
            if not math.isfinite(angle) or q >= n:
                raise SimError(f"line {k}: ry of a finite angle on a qubit of q[{n}]")
            ops.append(("ry", q, angle))
        elif mb:
            qs = [int(x[2:-1]) for x in line[len("barrier "):-1].split(",")]
            if len(set(qs)) != len(qs) or max(qs) >= n:
                raise SimError(f"line {k}: a barrier on distinct qubits of q[{n}]")
            barriers += 1
        else:
            raise SimError(f"line {k}: {line[:60]!r} is not in the subset the exact hold reads")
        if len(ops) > MAX_GATES:
            raise SimError(f"line {k}: more than {MAX_GATES} gates; the exact hold reads at most that")
        if barriers > MAX_GATES:
            raise SimError(f"line {k}: more than {MAX_GATES} barrier lines; the exact hold reads at most that many")
        i += 1
    rest = lines[i:]
    if measured:
        if rest != [f"measure q[{j}] -> meas[{j}];" for j in range(n)]:
            raise SimError(f"the circuit ends with measure q[j] -> meas[j]; for j = 0 to {n - 1}, in order, after its "
                           "last gate")
    elif rest:
        raise SimError(f"line {i + 1}: a measurement in a circuit that declares no creg")
    return Circuit(n, tuple(ops), measured)


def _matrix(op):
    name = op[0]
    if name == "cx":
        return ("2q", op[1], op[2], CX)
    if name == "ry":
        return ("1q", op[1], ry(op[2]))
    return ("1q", op[1], {"x": X, "h": H, "sdg": SDG}[name])


# -- fusion and the light cone ----------------------------------------------------------------------------------------
def fuse(ops):
    """Blocks to apply in order: ("1", q, U) or ("2", a, b, U). Each run of gates confined to one pair is one 4x4; a
    single-qubit run joins the next pair that holds its qubit, or is one 2x2. Pending blocks act on disjoint qubits."""
    out, one, two = [], {}, {}

    def close(q):
        for p in [p for p in two if q in p]:
            out.append(("2", p[0], p[1], two.pop(p)))

    for op in ops:
        if op[0] == "1q":
            q, U = op[1], op[2]
            pair = next((p for p in two if q in p), None)
            if pair is not None:
                two[pair] = mul(kron(U, I2) if q == pair[0] else kron(I2, U), two[pair])
            else:
                one[q] = mul(U, one[q]) if q in one else U
            continue
        a, b, U = op[1], op[2], op[3]
        if (a, b) in two:
            two[(a, b)] = mul(U, two[(a, b)])
        elif (b, a) in two:
            two[(b, a)] = mul(swapped(U), two[(b, a)])
        else:
            close(a)
            close(b)
            two[(a, b)] = mul(U, kron(one.pop(a, I2), one.pop(b, I2)))
    out += [("1", q, one[q]) for q in sorted(one)]
    out += [("2", p[0], p[1], two[p]) for p in sorted(two)]
    return out


class State:
    """A state as the light cone holds it: the qubits it has spread to, each an axis of the dense amplitudes `psi`
    (index sum of bit k * 2^k, axes in the order they entered), and every other qubit a classical bit (0 unless set)."""

    def __init__(self, axes=None, psi=None, bits=None):
        self.axes = dict(axes or {})
        self.psi = list(psi) if psi is not None else [1 + 0j]
        self.bits = dict(bits or {})

    def copy(self):
        return State(self.axes, self.psi, self.bits)

    def _enter(self, q):
        zero = [0j] * len(self.psi)
        self.psi = self.psi + zero if not self.bits.pop(q, 0) else zero + self.psi
        self.axes[q] = len(self.axes)


def _runs(n, k):
    size, s = 1 << n, 1 << k
    if k < n // 2:
        return [(slice(r, size, 2 * s), slice(r + s, size, 2 * s)) for r in range(s)]
    return [(slice(b, b + s), slice(b + s, b + 2 * s)) for b in range(0, size, 2 * s)]


def _within(base, length, low):
    s = 1 << low
    if length // (2 * s) > s:
        return [(slice(base + r, base + length, 2 * s), slice(base + r + s, base + length, 2 * s)) for r in range(s)]
    return [(slice(c, c + s), slice(c + s, c + 2 * s)) for c in range(base, base + length, 2 * s)]


def _quarters(n, high, low):
    out = ([], [], [], [])
    size, sh = 1 << n, 1 << high
    for b in range(0, size, 2 * sh):
        for hb in (0, 1):
            for lo_s, hi_s in _within(b + hb * sh, sh, low):
                out[2 * hb].append(lo_s)
                out[2 * hb + 1].append(hi_s)
    return out


def _apply1(psi, n, k, U):
    (a, b), (c, d) = U
    for lo_s, hi_s in _runs(n, k):
        lo, hi = psi[lo_s], psi[hi_s]
        psi[lo_s] = [a * x + b * y for x, y in zip(lo, hi)]
        psi[hi_s] = [c * x + d * y for x, y in zip(lo, hi)]


def _apply2(psi, n, high, low, U):
    """U indexed 2 * bit_high + bit_low, high > low."""
    rows = [[(j, u) for j, u in enumerate(row) if u != 0] for row in U]
    for s4 in zip(*_quarters(n, high, low)):
        v = [psi[s] for s in s4]
        new = []
        for row in rows:
            if not row:
                new.append([0j] * len(v[0]))
            elif len(row) == 1:
                (j, u), = row
                new.append([u * x for x in v[j]])
            elif len(row) == 2:
                (j1, u1), (j2, u2) = row
                new.append([u1 * x + u2 * y for x, y in zip(v[j1], v[j2])])
            elif len(row) == 3:
                (j1, u1), (j2, u2), (j3, u3) = row
                new.append([u1 * x + u2 * y + u3 * z for x, y, z in zip(v[j1], v[j2], v[j3])])
            else:
                (j1, u1), (j2, u2), (j3, u3), (j4, u4) = row
                new.append([u1 * w + u2 * x + u3 * y + u4 * z for w, x, y, z in zip(v[j1], v[j2], v[j3], v[j4])])
        for s, vals in zip(s4, new):
            psi[s] = vals


def simulate(blocks, start=None):
    """The State after `blocks` (from fuse), from |0...0> or a copy of `start`."""
    st = State() if start is None else start.copy()
    for blk in blocks:
        qs = (blk[1],) if blk[0] == "1" else (blk[1], blk[2])
        U = blk[2] if blk[0] == "1" else blk[3]
        if all(q not in st.axes for q in qs) and monomial(U):
            if blk[0] == "1":
                st.bits[qs[0]] = next(r for r in range(2) if U[r][st.bits.get(qs[0], 0)] != 0)
            else:
                c = 2 * st.bits.get(qs[0], 0) + st.bits.get(qs[1], 0)
                r = next(r for r in range(4) if U[r][c] != 0)
                st.bits[qs[0]], st.bits[qs[1]] = r >> 1, r & 1
            continue
        for q in qs:
            if q not in st.axes:
                st._enter(q)
        n = len(st.axes)
        if blk[0] == "1":
            _apply1(st.psi, n, st.axes[qs[0]], U)
        else:
            ka, kb = st.axes[qs[0]], st.axes[qs[1]]
            if ka > kb:
                _apply2(st.psi, n, ka, kb, U)
            else:
                _apply2(st.psi, n, kb, ka, swapped(U))
    return st


def distribution(state, clbits):
    """The probability of each outcome over the clbits, clbit c reading qubit clbits[c]: an array of 2^len(clbits)
    doubles, indexed sum of bit c * 2^c."""
    fixed, axis_bits = 0, [0] * len(state.axes)
    for c, q in enumerate(clbits):
        k = state.axes.get(q)
        if k is None:
            if state.bits.get(q, 0):
                fixed |= 1 << c
        else:
            axis_bits[k] |= 1 << c
    table = [fixed]
    for b in axis_bits:
        table += [t | b for t in table]
    out = array("d", bytes(8 << len(clbits)))
    for i, v in enumerate(state.psi):
        p = v.real * v.real + v.imag * v.imag
        if p:
            out[table[i]] += p
    return out


def pair_expectation(state, letter, a, b):
    """<P_a P_b> on the state, P being X or Y: Pauli algebra on the amplitudes. A qubit still a classical bit flips
    to an orthogonal state, so a pair holding one gives 0."""
    ka, kb = state.axes.get(a), state.axes.get(b)
    if ka is None or kb is None:
        return 0.0
    m, psi, total = (1 << ka) | (1 << kb), state.psi, 0j
    for i, v in enumerate(psi):
        if v:
            w = psi[i ^ m].conjugate() * v
            if letter == "Y":                       # Y Y |b_a b_b> = -(-1)^(b_a + b_b) |flipped>
                w = -w if not ((i >> ka) ^ (i >> kb)) & 1 else w
            total += w
    return total.real


# -- the memo ----------------------------------------------------------------------------------------------------------
class Memo:
    """An LRU of at most `size` entries."""

    def __init__(self, size=64):
        self.size, self.entries = size, OrderedDict()

    def get(self, key):
        got = self.entries.get(key)
        if got is not None:
            self.entries.move_to_end(key)
        return got

    def put(self, key, value):
        self.entries[key] = value
        self.entries.move_to_end(key)
        while len(self.entries) > self.size:
            self.entries.popitem(last=False)
        return value

    def clear(self):
        self.entries.clear()


GATE_LISTS = Memo()           # SHA-256 of a gate list's bytes -> (num_clbits, distribution)
CORES = Memo()                # a logical circuit's core operations -> the State after them
LOGICAL = Memo()              # (n, a logical circuit's ops) -> (its final State, its distribution over its n bits)
MEMOS = [GATE_LISTS, CORES, LOGICAL]
TAIL = ("h", "sdg")


def clear():
    """Empty every memo of the exact hold's: this module's three, and the three qro.p2_hold keeps beside them. The law's
    classes have their own, p2_law.clear()."""
    for memo in MEMOS:
        memo.clear()


def gate_list_distribution(data):
    """(num_clbits, the distribution over them) of a gate list's bytes, memoised by their SHA-256. SimError for
    bytes the simulator does not read."""
    key = hashlib.sha256(bytes(data)).hexdigest()
    got = GATE_LISTS.get(key)
    if got is None:
        g = read_gate_list(data)
        got = GATE_LISTS.put(key, (g.num_clbits, distribution(simulate(fuse(g.ops)), g.clbits)))
    return got


def split(ops):
    """(core, tail) of a logical circuit's operations: the tail is their trailing run of h and sdg, the core the
    rest."""
    k = len(ops)
    while k and ops[k - 1][0] in TAIL:
        k -= 1
    return ops[:k], ops[k:]


def logical(circuit):
    """(the final State, the distribution over its n bits) of a logical Circuit, memoised by its width and operations:
    its core's State, simulated or memoised, and then its tail, always."""
    key = (circuit.n, circuit.ops)
    got = LOGICAL.get(key)
    if got is None:
        core, tail = split(circuit.ops)
        st = CORES.get(core)
        if st is None:
            st = CORES.put(core, simulate(fuse([_matrix(op) for op in core])))
        st = simulate(fuse([_matrix(op) for op in tail]), st)
        got = LOGICAL.put(key, (st, distribution(st, tuple(range(circuit.n)))))
    return got
