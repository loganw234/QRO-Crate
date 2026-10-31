"""The exact hold, `qro-exact-hold/1`: a compile's gate lists held to their logical circuits, and each logical
circuit to its role (P2's design, item 7; P2.1). Standard library and qro only. Step 7 (qro.p2_steps) walks the
crate; this module holds bytes.

THE MANIFEST, Quantum-Film's `quantum-film/hardware-bundle/v1` (the lead's E2 (2)): read strictly, by P1.1's
p1_forms.load_json; an object whose `format` is that, with a non-empty list `jobs` of objects, each with a non-empty
list `circuits` of objects, each holding `name` (text), `role` (a word of the vocabulary's `role` set), `basis` (letters
X, Y and Z), `circuit_sha256` (its logical circuit) and `gates_sha256` (its gate list), each 64 lowercase hex.
`gates_sha256` may be absent, a circuit that names no gate list. Nothing else of the manifest is read: not its `isa`
block, whose verdicts are Quantum-Film's, nor its esp, commitments or salts.

THE HOLD of one circuit whose gate list the crate carries:
  (a) the gate list's distribution over its clbits against its logical circuit's over its bits: the largest
      difference, over every outcome, at most TOLERANCE;
  (b) the logical circuit against its role: `law`, every N-site layout within TOLERANCE of the law's P(Y), and the
      mass outside them at most TOLERANCE; `coherence`, the parity of the basis's two qubits read out of Z, in one
      letter X or Y, within TOLERANCE of the law's observable of that name; `known-answer`, one outcome with
      probability at least 1 - TOLERANCE.
THE CLAIM, from presence (the generator's; step 7 recomputes it): `holds` where every gate list the manifest names is
carried, `withheld` where a File of the crate has none of one's digest, `unexposed` where the manifest names none.

WHAT IT CANNOT SEE (P2's stated limit 1; isa.py's own, READ): a change that leaves every Z-basis probability alone, an
rz on a qubit still in a basis state or after its last two-qubit gate, before its measurement. Only digests refuse it.
"""
import hashlib
from dataclasses import dataclass

from qro import p1_forms, p2_sim, spelling
from qro import vocabulary as V
from qro.p2_law import observable_pair

RULE = "qro-exact-hold/1"
BUNDLE_FORMAT = "quantum-film/hardware-bundle/v1"
TOLERANCE = 1e-10
HOLDS, WITHHELD, UNEXPOSED = "holds", "withheld", "unexposed"


class HoldError(ValueError):
    """A manifest the hold does not read, or a circuit that does not hold."""


@dataclass(frozen=True)
class Named:
    """One circuit a manifest names."""
    name: str
    role: str
    basis: str
    circuit_sha256: str
    gates_sha256: object       # a digest, or None where the circuit names no gate list


def read_manifest(data):
    """The circuits a manifest names, in its order, or HoldError, as the module docstring states the form."""
    doc = p1_forms.load_json(bytes(data), "the manifest", HoldError)
    if not isinstance(doc, dict) or doc.get("format") != BUNDLE_FORMAT:
        raise HoldError(f"the manifest is not {BUNDLE_FORMAT}")
    jobs = doc.get("jobs")
    if not isinstance(jobs, list) or not jobs or not all(isinstance(j, dict) for j in jobs):
        raise HoldError("the manifest's jobs are a non-empty list of objects")
    out = []
    for i, job in enumerate(jobs):
        circuits = job.get("circuits")
        if not isinstance(circuits, list) or not circuits or not all(isinstance(c, dict) for c in circuits):
            raise HoldError(f"jobs[{i}]: its circuits are a non-empty list of objects")
        for j, c in enumerate(circuits):
            where = f"jobs[{i}].circuits[{j}]"
            name, role, basis = c.get("name"), c.get("role"), c.get("basis")
            if spelling.problem("text", name):
                raise HoldError(f"{where}: its name is not text")
            if not isinstance(role, str) or role not in V.WORDS["role"]:
                raise HoldError(f"{where}: the role {role!r} is not one the hold holds ({', '.join(V.WORDS['role'])})")
            if not isinstance(basis, str) or not basis or set(basis) - set("XYZ"):
                raise HoldError(f"{where}: its basis is not letters X, Y and Z")
            for key in ("circuit_sha256", "gates_sha256"):
                if (key in c or key == "circuit_sha256") and spelling.problem("digest", c.get(key)):
                    raise HoldError(f"{where}: its {key} is not 64 lowercase hex digits")
            out.append(Named(name, role, basis, c["circuit_sha256"], c.get("gates_sha256")))
    return tuple(out)


def claim(named, carried):
    """The word the gate lists give a compile, from presence: `carried` is the digests the crate's Files state."""
    digests = [c.gates_sha256 for c in named if c.gates_sha256 is not None]
    if not digests:
        return UNEXPOSED
    return HOLDS if all(d in carried for d in digests) else WITHHELD


# -- the holds ---------------------------------------------------------------------------------------------------------
def biggest_difference(p, q):
    """max over every outcome of |p - q|, for two distributions of one width."""
    if len(p) != len(q):
        raise HoldError("two distributions of different widths")
    return max(abs(x - y) for x, y in zip(p, q))


def law_problem(dist, width, law):
    """Why a distribution over `width` bits does not lay the law, or None."""
    if width != law.M:
        raise HoldError(f"the circuit has {width} qubits; the law's tile has {law.M} sites")
    worst = max(abs(dist[sum(1 << q for q in Y)] - w / law.den) for Y, w in zip(law.layouts, law.weights))
    outside = sum(p for o, p in enumerate(dist) if o.bit_count() != law.N)
    if worst > TOLERANCE or outside > TOLERANCE:
        return (f"it does not lay the law: its worst layout is off by {worst:.3e}, and {outside:.3e} of its mass lies "
                f"outside the law's {law.D} layouts, against {TOLERANCE:g}")
    return None


def coherence_pair(basis, width):
    """(letter, a, b): the two qubits a basis reads out of Z, in one letter X or Y; HoldError for any other basis."""
    off = [(q, x) for q, x in enumerate(basis) if x != "Z"]
    if len(basis) != width or len(off) != 2 or off[0][1] != off[1][1] or off[0][1] not in "XY":
        raise HoldError(f"the basis {basis} does not read exactly two of its {width} qubits out of Z, both in X or "
                        "both in Y")
    return off[0][1], off[0][0], off[1][0]


def parity(dist, a, b):
    """The expectation of (-1)^(b_a + b_b) under a distribution."""
    return sum(p if not ((o >> a) ^ (o >> b)) & 1 else -p for o, p in enumerate(dist) if p)


def role_problem(named, dist, width, law):
    """Why a logical circuit does not do what its role says, or None; HoldError where the role cannot be judged."""
    if named.role == "known-answer":
        best = max(dist)
        if best < 1 - TOLERANCE:
            return f"its most likely outcome has probability {best:.6f}, not 1: no known answer"
        return None
    if law is None:
        raise HoldError(f"a {named.role} circuit is held to the question's law, and the crate's question names none")
    if named.role == "law":
        return law_problem(dist, width, law)
    letter, a, b = coherence_pair(named.basis, width)
    name = f"{letter}{a}{letter}{b}"
    if name not in law.observables:
        raise HoldError(f"the law names no observable {name}, which the basis {named.basis} reads")
    got, want = parity(dist, a, b), law.observables[name]
    if abs(got - float(want)) > TOLERANCE:
        return f"the parity of qubits {a} and {b} is {got:+.12f}, where the law's {name} is {want}"
    return None


COMPARED = p2_sim.Memo()      # (gate digest, logical n, logical ops) -> the biggest difference between them
JUDGED = p2_sim.Memo()        # (logical n, logical ops, role, basis, law digest) -> the role's problem or ""
LAW_CIRCUITS = p2_sim.Memo()  # (circuit digest, law digest) -> the law circuit's problem or ""
p2_sim.MEMOS.extend([COMPARED, JUDGED, LAW_CIRCUITS])


def hold_circuit(named, gate_bytes, logical_bytes, law):
    """Why one circuit's gate list does not hold, (a) or (b), or None. SimError where the gate list or the logical
    circuit is not one the simulator reads; HoldError where the role cannot be judged."""
    width, dist_g = p2_sim.gate_list_distribution(gate_bytes)
    circuit = p2_sim.read_qasm(logical_bytes)
    _, dist_l = p2_sim.logical(circuit)
    if width != circuit.n:
        raise HoldError(f"the gate list measures {width} clbits; its logical circuit has {circuit.n} qubits")
    key = (hashlib.sha256(bytes(gate_bytes)).hexdigest(), circuit.n, circuit.ops)
    diff = COMPARED.get(key)
    if diff is None:
        diff = COMPARED.put(key, biggest_difference(dist_g, dist_l))
    if diff > TOLERANCE:
        return (f"(a) its distribution differs from its logical circuit's by {diff:.3e} at worst, against "
                f"{TOLERANCE:g}")
    jkey = (circuit.n, circuit.ops, named.role, named.basis, None if law is None else law.digest)
    problem = JUDGED.get(jkey)
    if problem is None:
        problem = JUDGED.put(jkey, role_problem(named, dist_l, circuit.n, law) or "")
    return f"(b) its logical circuit, a {named.role} circuit: {problem}" if problem else None


def law_circuit_problem(qasm_bytes, law):
    """Why the question's law circuit does not lay the law and its observables, or None (P2's design, item 6.4): every
    layout and the mass outside them, and each observable the law names by Pauli algebra on the final state, within
    TOLERANCE. SimError for a circuit the simulator does not read."""
    key = (hashlib.sha256(bytes(qasm_bytes)).hexdigest(), law.digest)
    got = LAW_CIRCUITS.get(key)
    if got is None:
        circuit = p2_sim.read_qasm(qasm_bytes)
        if circuit.n != law.M:
            got = f"the law circuit has {circuit.n} qubits; the law's tile has {law.M} sites"
        else:
            state, dist = p2_sim.logical(circuit)
            got = law_problem(dist, circuit.n, law) or ""
            for name, value in sorted(law.observables.items()):
                if got:
                    break
                letter, a, b = observable_pair(name, law.M)
                have = p2_sim.pair_expectation(state, letter, a, b)
                if abs(have - float(value)) > TOLERANCE:
                    got = f"its {name} is {have:+.12f}, where the law says {value}"
        LAW_CIRCUITS.put(key, got)
    return got or None
