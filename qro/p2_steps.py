"""Checker steps 6 and 7: the measures and their classes, and the exact hold (P2's design, items 6 and 7; P2.1).
Standard library and qro only. qro/register_p2.py hands these to the checker, and imports this module only for a crate
that carries a term of the step's or an entity of its types (the lead's decision on E1, 2026-10-26).

STEP 6, `measure-class`, re-derives, in this order, refusing at the first failure with the entity and the term:
  1. exactly one `qro:Question`, carrying `qro:law`, `qro:lawCircuit`, `qro:twins` and `qro:measureSet`;
  2. the measure set is one this step builds, `qro-measures/1`, else `step-unbuilt`; its twins `dephased`, `uniform`;
  3. the law: a File of the crate in `qro-law/1`, read and held to its form (qro.p2_law), and the measure set's needs
     of it;
  4. the law against the question's own circuit: `qro:lawCircuit` a File in the question's `object`, in the QASM
     subset, simulated, laying every layout and its observables within 1e-10;
  5. the classes: the Contrasts exactly (measure, twin) over the set, each class and each value as computed from the
     law, whatever the crate says;
  6. the measurements: every `qro:Pub` of role `law` or `coherence` measured from its raw bytes through P1.1's
     pub_counts (a coherence Pub whose raw result Atlas's rule decodes is refused, qro.p2_measures.pub_values), and
     the crate's Measurements exactly that set, no other, each term as computed, each interval at alpha 1/20 over the
     family of every certified measurement that holds a value;
  7. exactly one `qro:Measuring`, its `qro:alpha` 1/20 and its `qro:family` that family. Its `name`, `object`,
     `result` and `qro:implementation` are REPORTED, and step 9 holds them.
STEP 7, `compile-uncontrolled`: every Hold names one Compile and the rule `qro-exact-hold/1` (any other is
`step-unbuilt`); every Compile has exactly one Hold; each Compile's manifest is read; every logical circuit it names is
carried; every gate list it names that the crate carries is held (qro.p2_hold), whatever any claim says; no gate list
(a File whose name ends `.gates.json`) in the Compile's `object` or `result` goes unnamed by its manifest; and the
Hold's word is the one the gate lists give.
Every entity is visited by its type, never by its id's pattern. What a hostile file or graph raises inside either step
is refused by the step's own name, with its type and text (FORMAT.md, item 16), but for an OSError, which is the host's
(a PermissionError, misuse: exit 2) and a MemoryError, neither caught: the checker failing, exit 3.
"""
from pathlib import Path

from qro import p1_decode, p2_hold, p2_law, p2_measures, p2_sim, reader, spelling
from qro.checker import RawFormError, describe
from qro.p1_graph import GraphError, Index
from qro.refusal import Refused

EXPECTED = (GraphError, RawFormError, p1_decode.DecodeError, p2_law.LawError, p2_sim.SimError, p2_hold.HoldError,
            p2_measures.MeasureError)


def _measure(where, detail):
    return Refused("measure-class", where, detail)


def _uncontrolled(where, detail):
    return Refused("compile-uncontrolled", where, detail)


def _net(refuse, where, fn, *args):
    """fn(*args) under the step's net: a Refused is the step's answer, an OSError and a MemoryError are the host's, and
    anything else a hostile input raised is a refusal by the step's own name."""
    try:
        return fn(*args)
    except Refused:
        raise
    except (OSError, MemoryError):
        raise
    except EXPECTED as x:
        raise refuse(where, str(x)) from None
    except Exception as x:
        raise refuse(where, f"cannot be checked: {describe(x)}") from None


def _index(md, refuse):
    try:
        return Index(md)
    except GraphError as x:
        raise refuse("@graph", str(x)) from None


def _local_file(idx, ref, where, what, refuse):
    """The File of the crate a reference names: refused where it names no File the crate holds."""
    e = idx.by_id.get(ref.get("@id")) if isinstance(ref, dict) else None
    if e is None or not reader.local_file(e):
        raise refuse(where, f"{what} names no File the crate holds")
    return e


# -- step 6 ------------------------------------------------------------------------------------------------------------
def step6(crate_dir, md):
    _net(_measure, "@graph", _step6, Path(crate_dir), md)          # the last net; the inner ones name the place


def _step6(crate, md):
    idx = _index(md, _measure)
    question = _question(idx)
    qid = question["@id"]
    law = _net(_measure, f"{qid} qro:law", _law, crate, idx, question)
    _net(_measure, f"{qid} qro:lawCircuit", _law_circuit, crate, idx, question, law)
    _contrasts(idx, question, law)
    _measurements(crate, idx, md, law)


def _question(idx):
    questions = idx.of_type("qro:Question")
    if len(questions) != 1:
        raise _measure("@graph", f"a crate that carries P2's terms carries exactly one qro:Question; this one carries "
                                 f"{len(questions)}")
    q = questions[0]
    for term in p2_measures.QUESTION_TERMS:
        if term not in q:
            raise _measure(f"{q['@id']} {term}", "the question carries the law, its circuit, the twins and the measure "
                                                 "set")
    if q["qro:measureSet"] != p2_law.MEASURE_SET:
        raise Refused("step-unbuilt", f"{q['@id']} qro:measureSet", f"no measure set {q['qro:measureSet']} is built")
    if q["qro:twins"] != list(p2_law.TWINS):
        raise _measure(f"{q['@id']} qro:twins", f"the twins of {p2_law.MEASURE_SET} are {', '.join(p2_law.TWINS)}")
    return q


def _law(crate, idx, question):
    where = f"{question['@id']} qro:law"
    e = _local_file(idx, question["qro:law"], where, "the law", _measure)
    law = p2_law.read(p1_decode.crate_file(crate, e, "the law file"))
    p2_law.needs(law)
    return law


def _law_circuit(crate, idx, question, law):
    where = f"{question['@id']} qro:lawCircuit"
    ref = question["qro:lawCircuit"]
    if ref.get("@id") not in idx.refs(question, "object"):
        raise _measure(where, "the law circuit is one of the question's own circuits, in its object")
    e = _local_file(idx, ref, where, "the law circuit", _measure)
    problem = p2_hold.law_circuit_problem(p1_decode.crate_file(crate, e, "the law circuit"), law)
    if problem:
        raise _measure(where, f"the law is not the question's circuit's: {problem}")


def _contrasts(idx, question, law):
    computed = _net(_measure, f"{question['@id']} qro:law", p2_law.classes, law)
    seen = set()
    for e in sorted(idx.of_type("qro:Contrast"), key=lambda e: e["@id"]):
        cid = e["@id"]
        for term in ("qro:measure", "qro:twin", "qro:class"):
            if term not in e:
                raise _measure(f"{cid} {term}", "a Contrast states its measure, its twin and its class")
        key = (e["qro:measure"], e["qro:twin"])
        if key in seen:
            raise _measure(cid, f"a second Contrast of {key[0]} against {key[1]}")
        seen.add(key)
        c = computed.get(key)
        if c is None:
            raise _measure(f"{cid} qro:measure", f"{key[0]} against {key[1]} is no contrast of {p2_law.MEASURE_SET}")
        if e["qro:class"] != c.cls:
            raise _measure(f"{cid} qro:class", f"the crate says {e['qro:class']}; the law and the twin's rule give "
                                               f"{c.cls}")
        for term, want in (("qro:lawValue", c.law_value), ("qro:twinValue", c.twin_value)):
            if want is None:
                if term in e:
                    raise _measure(f"{cid} {term}", f"{key[0]} is a vector measure, which carries a class only")
            elif e.get(term) != spelling.rational(want):
                raise _measure(f"{cid} {term}", f"the crate says {e.get(term)}; it is {spelling.rational(want)}")
    for key in computed:
        if key not in seen:
            raise _measure(f"{question['@id']} qro:measureSet", f"no Contrast of {key[0]} against {key[1]}, which "
                                                               f"{p2_law.MEASURE_SET} holds")


def _measurements(crate, idx, md, law):
    values = {}
    for pub in p2_measures.measured_pubs(idx):
        pid = pub["@id"]
        got = _net(_measure, pid, p2_measures.pub_values, crate, md, pub, law)
        for m, v in got.items():
            values[(pid, m)] = v
    family, bounds = _net(_measure, "#measuring qro:family", p2_measures.certify, values)
    seen = set()
    for e in sorted(idx.of_type("qro:Measurement"), key=lambda e: e["@id"]):
        _measurement(idx, e, values, bounds, seen)
    for pid, m in sorted(values):
        if (pid, m) not in seen:
            raise _measure(pid, f"the PUB's {m} has no Measurement, and every measure of a law or coherence PUB has "
                                "one")
    measurings = idx.of_type("qro:Measuring")
    if len(measurings) != 1:
        raise _measure("@graph", f"a crate that carries P2's terms carries exactly one qro:Measuring; this one carries "
                                 f"{len(measurings)}")
    mid = measurings[0]["@id"]
    if measurings[0].get("qro:alpha") != spelling.rational(p2_measures.ALPHA):
        raise _measure(f"{mid} qro:alpha", f"the crate's intervals are at alpha {spelling.rational(p2_measures.ALPHA)}")
    if measurings[0].get("qro:family") != family:
        raise _measure(f"{mid} qro:family", f"the crate says {measurings[0].get('qro:family')}; it carries {family} "
                                            "certified intervals")


def _measurement(idx, e, values, bounds, seen):
    mid = e["@id"]
    for term in ("qro:measure", "qro:measuredPub", "qro:inScope", "qro:value"):
        if term not in e:
            raise _measure(f"{mid} {term}", "a Measurement states its measure, its PUB, its shots in scope and its "
                                            "value")
    pid = e["qro:measuredPub"].get("@id")
    pub = idx.by_id.get(pid)
    if pub is None or "qro:Pub" not in canonical_types(pub):
        raise _measure(f"{mid} qro:measuredPub", f"{pid} is no Pub of the crate")
    key = (pid, e["qro:measure"])
    if key in seen:
        raise _measure(mid, f"a second Measurement of {key[1]} on {pid}")
    v = values.get(key)
    if v is None:
        raise _measure(f"{mid} qro:measure", f"{pid}, a PUB of role {pub.get('qro:role')}, has no measure "
                                             f"{key[1]} in {p2_law.MEASURE_SET}")
    seen.add(key)
    if e["qro:inScope"] != v.in_scope:
        raise _measure(f"{mid} qro:inScope", f"the crate says {e['qro:inScope']}; the raw bytes hold {v.in_scope} "
                                             "shots in the measure's domain")
    want = "none" if v.value is None else spelling.rational(v.value)
    if e["qro:value"] != want:
        raise _measure(f"{mid} qro:value", f"the crate says {e['qro:value']}; the raw bytes give {want}")
    b = bounds.get(key)
    for term, i in (("qro:lower", 0), ("qro:upper", 1)):
        if b is None:
            if term in e:
                raise _measure(f"{mid} {term}", f"{key[1]} carries no interval here")
        elif e.get(term) != spelling.rational(b[i]):
            raise _measure(f"{mid} {term}", f"the crate says {e.get(term)}; the certified interval's end is "
                                            f"{spelling.rational(b[i])}")


def canonical_types(e):
    t = e.get("@type")
    return [t] if isinstance(t, str) else list(t) if isinstance(t, list) else []


# -- step 7 ------------------------------------------------------------------------------------------------------------
def step7(crate_dir, md):
    _net(_uncontrolled, "@graph", _step7, Path(crate_dir), md)     # the last net; the inner ones name the place


def _step7(crate, md):
    idx = _index(md, _uncontrolled)
    held = {}
    for h in sorted(idx.of_type("qro:Hold"), key=lambda e: e["@id"]):
        _net(_uncontrolled, h["@id"], _hold_entity, idx, h, held)
    law = []                                       # read once, when a circuit first needs it
    for c in sorted(idx.of_type("qro:Compile"), key=lambda e: e["@id"]):
        _net(_uncontrolled, c["@id"], _compile, crate, idx, c, held, law)


def _hold_entity(idx, h, held):
    hid = h["@id"]
    refs = idx.refs(h, "qro:heldCompile")
    target = idx.by_id.get(refs[0]) if len(refs) == 1 else None
    if target is None or "qro:Compile" not in canonical_types(target):
        raise _uncontrolled(f"{hid} qro:heldCompile", "a Hold names one Compile of the crate")
    if "qro:holdRule" not in h:
        raise _uncontrolled(f"{hid} qro:holdRule", "a Hold names the rule it holds by")
    if h["qro:holdRule"] != p2_hold.RULE:
        raise Refused("step-unbuilt", f"{hid} qro:holdRule", f"no hold rule {h['qro:holdRule']} is built")
    if "qro:exactHold" not in h:
        raise _uncontrolled(f"{hid} qro:exactHold", "a Hold states what the compile's gate lists give")
    held.setdefault(target["@id"], []).append(h)


def _question_law(crate, idx, law):
    """The law of the question that names one, read once; None where none does."""
    if not law:
        carriers = [q for q in idx.of_type("qro:Question") if "qro:law" in q]
        if len(carriers) > 1:
            raise p2_hold.HoldError(f"{len(carriers)} questions name a law")
        if not carriers:
            law.append(None)
        else:
            e = _local_file(idx, carriers[0]["qro:law"], f"{carriers[0]['@id']} qro:law", "the law", _uncontrolled)
            law.append(p2_law.read(p1_decode.crate_file(crate, e, "the law file")))
    return law[0]


def _compile(crate, idx, c, held, law):
    cid = c["@id"]
    hs = held.get(cid, [])
    if len(hs) != 1:
        raise _uncontrolled(cid, f"a Compile has exactly one Hold; this one has {len(hs)}")
    manifest = p2_measures.manifest_of(idx, c)
    named = p2_hold.read_manifest(p1_decode.crate_file(crate, manifest, "the manifest"))
    gates = {n.gates_sha256 for n in named if n.gates_sha256 is not None}
    for term in ("object", "result"):
        for e in sorted(idx.refs_of_type(c, term, "File"), key=lambda e: e["@id"]):
            if e["@id"].endswith(".gates.json") and e.get("sha256") not in gates:
                raise _uncontrolled(f"{cid} {term}", f"{e['@id']} is a gate list its manifest does not name")
    for n in named:
        logicals = [e for e in idx.files_by_sha256(n.circuit_sha256) if reader.local_file(e)]
        if not logicals:
            raise _uncontrolled(manifest["@id"], f"the logical circuit of {n.name}, {n.circuit_sha256}, is not carried")
        if n.gates_sha256 is None:
            continue
        carried = [e for e in idx.files_by_sha256(n.gates_sha256) if reader.local_file(e)]
        if not carried:
            continue                                   # withheld: the claim must say so, below
        g = carried[0]
        try:
            problem = p2_hold.hold_circuit(n, p1_decode.crate_file(crate, g, "the gate list"),
                                           p1_decode.crate_file(crate, logicals[0], "the logical circuit"),
                                           None if n.role == "known-answer" else _question_law(crate, idx, law))
        except (p2_sim.SimError, p2_hold.HoldError, p2_law.LawError) as x:
            raise _uncontrolled(g["@id"], f"the gate list of {n.name} cannot be held: {x}") from None
        if problem:
            raise _uncontrolled(g["@id"], f"the gate list of {n.name} does not pass the exact hold: {problem}")
    files = {e["sha256"] for e in idx.of_type("File") if isinstance(e.get("sha256"), str) and reader.local_file(e)}
    word, h = p2_hold.claim(named, files), hs[0]
    if h["qro:exactHold"] != word:
        raise _uncontrolled(f"{h['@id']} qro:exactHold", f"the Hold says {h['qro:exactHold']}; the gate lists give "
                                                          f"{word}")

