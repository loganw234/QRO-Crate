"""The measures of a crate's PUBs, and P2's contract with P1's generator (P2's design, items 1 and 9; P2.1). Standard
library and qro only.

THE MEASURES of one PUB, from its decoded counts {the sorted tuple of qubits read 1: shots}, which P1.1's
qro.p1_decode.pub_counts reads from the raw bytes under the PUB's decode's rule and declared bit order (step 5 has held
the order). A `law` PUB, read in Z: n-crystal-share (all shots; the share holding exactly N crystals), forbidden-share
and linear-xeb (its N-crystal shots), tvd (its N-crystal shots; a statistic, no interval) and nn-pair-correlation (all
shots; a ratio, no interval). A `coherence` PUB, its basis reading two qubits out of Z in one letter: the parity of the
pair, x0x1 or y0y1, and only where its raw result was read in that basis: never on an Atlas raw result, whose rule
gives every PUB the all-Z setting's layouts. Each value is the exact ratio of whole counts in lowest terms; a domain
with no shot has none.
Crystals per shot and the one-site and pair occupations carry a class and no per-PUB value in v1.

THE INTERVALS: each certified measure's per-shot mean (n-crystal-share, forbidden-share: an indicator; linear-xeb:
w(Y) / w_max; a parity: the agree indicator) gets qro.p2_interval's interval at alpha = 1/20 over the crate's own
family M, the number of certified measurements that hold a value, mapped to the measure's units.

THE CONTRACT with P1's generator (item 9), by module name:
  question_files(crate_dir) -> {"law.json": bytes}: the pauli-4x4 law, made from its integer kernel, for a crate that
      holds the source circuit P2 knows (found by SHA-256 among its files); a crate without it raises.
  contribute(crate_dir, entities) -> (question_terms, new_entities): P2's four terms for the question, and P2's
      entities: `#measuring`, the twenty Contrasts, the Measurements and one Hold per Compile. It reads P1's entities,
      the crate's files (the law file, the law circuit, each Compile's manifest, the raw results through pub_counts and
      P1.1's Index on {"@graph": entities}) and never the metadata file, Quantum-Film's device-run records, verdicts or
      the manifest's `isa` block. A Hold's word comes from presence; step 7 is what holds the gate lists. Values,
      intervals, classes and claims come from the same functions the steps use: `value`, p2_interval.interval,
      p2_law.classes and p2_hold.claim, each looked up on its module when called.
  measurements(md) -> the crate's CHECKED measurement values, for a caller such as P3, once the checker has accepted
      the crate.
"""
import hashlib
import os
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from qro import canonical, p1_decode, p2_hold, p2_interval, p2_law, reader, spelling
from qro.p1_graph import Index

ALPHA = p2_interval.ALPHA
LAW_FILE = "question/law.json"
MEASURED_ROLES = ("law", "coherence")
LAW_MEASURES = ("n-crystal-share", "forbidden-share", "linear-xeb", "tvd", "nn-pair-correlation")
QUESTION_TERMS = ("qro:law", "qro:lawCircuit", "qro:measureSet", "qro:twins")
MEASURING_ID = "#measuring"


class MeasureError(ValueError):
    """A PUB that cannot be measured as the measure set says: its basis, or an outcome off the law's tile."""


@dataclass(frozen=True)
class Value:
    measure: str
    in_scope: int              # the shots in the measure's domain
    value: object              # a Fraction, or None where no shot is in scope
    total: object              # a certified measure's per-shot total (an int or a Fraction); None otherwise
    mapping: object            # a certified measure's affine map from the per-shot mean; None otherwise


def measures_of(role, basis, law):
    """The measures of a PUB of this role and basis, under the law; MeasureError where the basis is not the role's."""
    if role == "law":
        if basis is not None and basis != "Z" * law.M:
            raise MeasureError(f"a law PUB is read in Z on all {law.M} qubits, and this one's basis is {basis}")
        return LAW_MEASURES
    if role == "coherence":
        if not isinstance(basis, str):
            raise MeasureError("a coherence PUB states its basis")
        try:
            letter, a, b = p2_hold.coherence_pair(basis, law.M)
        except p2_hold.HoldError as x:
            raise MeasureError(str(x)) from None
        name = f"{letter}{a}{letter}{b}"
        measure = name.lower()
        if name not in law.observables or measure not in p2_law.COHERENCE:
            raise MeasureError(f"the basis {basis} reads {name}, which {p2_law.MEASURE_SET} does not measure")
        return (measure,)
    raise MeasureError(f"the role {role} is not measured")


def _held(counts, law):
    """The counts, each outcome held to a strictly increasing tuple of the law's sites and a positive whole count."""
    for Y, c in counts.items():
        if not (isinstance(Y, tuple) and all(type(q) is int for q in Y) and all(a < b for a, b in zip(Y, Y[1:]))
                and (not Y or 0 <= Y[0] and Y[-1] < law.M)):
            raise MeasureError(f"the outcome {Y!r} is not a set of the law's {law.M} sites")
        if type(c) is not int or c < 1:
            raise MeasureError(f"the outcome {Y!r} has {c!r} shots")
    return counts


def value(measure, counts, law, basis=None):
    """One measure's Value on one PUB's counts."""
    shots = sum(counts.values())
    if measure in p2_law.COHERENCE:
        letter, a, b = p2_hold.coherence_pair(basis, law.M)
        agree = sum(c for Y, c in counts.items() if (a in Y) == (b in Y))
        return Value(measure, shots, Fraction(2 * agree - shots, shots) if shots else None, agree,
                     p2_interval.PARITY)
    if measure == "n-crystal-share":
        n_N = sum(c for Y, c in counts.items() if len(Y) == law.N)
        return Value(measure, shots, Fraction(n_N, shots) if shots else None, n_N, p2_interval.IDENTITY)
    if measure == "nn-pair-correlation":
        one, two = [0] * law.M, {}
        for Y, c in counts.items():
            for i in Y:
                one[i] += c
            for i in range(len(Y)):
                for j in range(i + 1, len(Y)):
                    two[(Y[i], Y[j])] = two.get((Y[i], Y[j]), 0) + c
        pairs = law.nn_pairs
        if not shots or any(not one[i] for p in pairs for i in p):
            return Value(measure, shots, None, None, None)
        v = sum((Fraction(two.get(p, 0) * shots, one[p[0]] * one[p[1]]) for p in pairs), Fraction(0)) / len(pairs)
        return Value(measure, shots, v, None, None)
    five = {Y: c for Y, c in counts.items() if len(Y) == law.N}
    n_N = sum(five.values())
    if measure == "forbidden-share":
        k = sum(c for Y, c in five.items() if law.weight[Y] == 0)
        return Value(measure, n_N, Fraction(k, n_N) if n_N else None, k, p2_interval.IDENTITY)
    if measure == "linear-xeb":
        s = sum(c * law.weight[Y] for Y, c in five.items())
        v = (Fraction(s, n_N * law.den) - Fraction(1, law.D)) / law.norm if n_N else None
        return Value(measure, n_N, v, Fraction(s, law.w_max),
                     p2_interval.xeb(law.w_max, law.den, law.D, law.norm))
    if measure == "tvd":
        if not n_N:
            return Value(measure, 0, None, None, None)
        num = sum(abs(five.get(Y, 0) * law.den - n_N * w) for Y, w in zip(law.layouts, law.weights))
        return Value(measure, n_N, Fraction(num, 2 * n_N * law.den), None, None)
    raise MeasureError(f"{measure} has no per-PUB value in {p2_law.MEASURE_SET}")


def measured_pubs(idx):
    """The Pubs of a measured role, in @id order."""
    return [p for p in sorted(idx.of_type("qro:Pub"), key=lambda e: e["@id"]) if p.get("qro:role") in MEASURED_ROLES]


def decode_rule(md, pub):
    """The rule that decodes a Pub's raw result: the `qro:decodeRule` of the Decode that reads it, found as P1.1's
    pub_counts finds it (GraphError where the graph lacks the relation)."""
    idx = Index(md)
    return idx.decode_of(idx.raw_of(idx.job_of(pub))).get("qro:decodeRule")


def pub_values(crate_dir, md, pub, law):
    """{measure: Value} for one measured Pub, its counts read from its raw result by pub_counts. A coherence PUB is
    measured only where its result was read in its own basis: Atlas's rule gives every Pub of a result the all-Z
    setting's layouts, so a coherence PUB on an Atlas raw result is a MeasureError (P2's stated limit 10)."""
    names = measures_of(pub.get("qro:role"), pub.get("qro:basis"), law)
    if pub.get("qro:role") == "coherence" and decode_rule(md, pub) == p1_decode.ATLAS_RULE:
        raise MeasureError(f"its raw result is read by {p1_decode.ATLAS_RULE}, which gives every PUB the all-Z "
                           "setting's layouts, so it holds no outcome in the PUB's own basis; P2 measures none of "
                           "Atlas's coherences")
    counts = _held(p1_decode.pub_counts(crate_dir, md, pub["@id"]), law)
    return {m: value(m, counts, law, pub.get("qro:basis")) for m in names}


def certify(values, alpha=ALPHA):
    """(family, {key: (lower, upper)}) for the Values of a crate: each certified measure that holds a value gets its
    interval at that family and alpha, mapped to its units."""
    keyed = {k: v for k, v in values.items() if v.mapping is not None and v.value is not None}
    family = len(keyed)
    out = {}
    for k, v in keyed.items():
        out[k] = p2_interval.mapped(p2_interval.interval(v.total, v.in_scope, family, alpha), v.mapping)
    return family, out


def rational(q):
    return spelling.rational(q)


def measurement_entity(pub_id, v, bounds):
    """The Measurement entity of one Value: its terms in their spellings."""
    if not pub_id.startswith("#pub-"):
        raise MeasureError(f"{pub_id}: a Pub's id is #pub-<job id>-<k>")
    e = {"@id": f"#measurement-{pub_id[len('#pub-'):]}-{v.measure}", "@type": "qro:Measurement",
         "qro:measure": v.measure, "qro:measuredPub": {"@id": pub_id}, "qro:inScope": v.in_scope,
         "qro:value": "none" if v.value is None else rational(v.value)}
    if bounds is not None:
        e["qro:lower"], e["qro:upper"] = rational(bounds[0]), rational(bounds[1])
    return e


def contrast_entity(c):
    e = {"@id": f"#contrast-{c.measure}-{c.twin}", "@type": "qro:Contrast", "qro:measure": c.measure,
         "qro:twin": c.twin, "qro:class": c.cls}
    if c.law_value is not None:
        e["qro:lawValue"], e["qro:twinValue"] = rational(c.law_value), rational(c.twin_value)
    return e


# -- the contract with P1's generator ---------------------------------------------------------------------------------
def question_files(crate_dir):
    """{"law.json": the pauli-4x4 law file}, for a crate that holds the source circuit P2 knows: keys relative to the
    crate's question/ directory. ValueError for a crate with no such circuit (P2 knows no other question's law)."""
    root = Path(crate_dir)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            if Path(dirpath) == root and name == canonical.DESCRIPTOR:
                continue                                    # the metadata is never read here
            data = Path(dirpath, name).read_bytes()
            if hashlib.sha256(data).hexdigest() == p2_law.SOURCE_CIRCUIT:
                return {"law.json": p2_law.law_bytes()}
    raise ValueError(f"no file of the crate is the source circuit {p2_law.SOURCE_CIRCUIT[:16]}..., the one law circuit "
                     f"{p2_law.MEASURE_SET} has a law for")


def _file_bytes(crate_dir, entity, what):
    return p1_decode.crate_file(crate_dir, entity, what)


def manifest_of(idx, compile_entity):
    """The one File among a Compile's `object` whose path's last segment is manifest.json (the lead's E2 (1))."""
    found = [e for e in idx.refs_of_type(compile_entity, "object", "File")
             if e["@id"].rsplit("/", 1)[-1] == "manifest.json"]
    if len(found) != 1:
        raise p2_hold.HoldError(f"{compile_entity['@id']}: its object holds {len(found)} manifest.json files, not one")
    return found[0]


def contribute(crate_dir, entities, source=p2_law.SOURCE_CIRCUIT):
    """(question_terms, new_entities): P2's terms for the question and P2's entities, a pure function of the crate's
    files and P1's entities ({@id: entity}). The law circuit is the first by @id of the question's `object` Files whose
    bytes have the SHA-256 `source`: P1's generator calls with two arguments, so v1's one source circuit; a test's
    synthetic question names its own. It raises where the crate holds no question, law or law circuit P2 can use, or a
    law or coherence Pub it cannot measure: a generator's failure, which step 9 refuses by name."""
    graph = [entities[i] for i in sorted(entities)]
    md = {"@graph": graph}
    idx = Index(md)
    questions = idx.of_type("qro:Question")
    if len(questions) != 1:
        raise ValueError(f"the crate holds {len(questions)} qro:Question entities, not one")
    question = questions[0]
    law = p2_law.read(Path(crate_dir).joinpath(*LAW_FILE.split("/")).read_bytes())
    circuits = [e for e in sorted(idx.refs_of_type(question, "object", "File"), key=lambda e: e["@id"])
                if hashlib.sha256(_file_bytes(crate_dir, e, "a question's circuit")).hexdigest() == source]
    if not circuits:
        raise ValueError(f"the question's object holds no source circuit {source[:16]}...")
    terms = {"qro:law": {"@id": LAW_FILE}, "qro:lawCircuit": {"@id": circuits[0]["@id"]},
             "qro:measureSet": p2_law.MEASURE_SET, "qro:twins": list(p2_law.TWINS)}
    contrasts = p2_law.classes(law)
    values = {}
    for pub in measured_pubs(idx):
        for m, v in pub_values(crate_dir, md, pub, law).items():
            values[(pub["@id"], m)] = v
    family, bounds = certify(values)
    measurements = [measurement_entity(pid, v, bounds.get((pid, m))) for (pid, m), v in sorted(values.items())]
    contrast_entities = [contrast_entity(contrasts[(m, t)]) for t in p2_law.TWINS for m in p2_law.MEASURES]
    measuring = {"@id": MEASURING_ID, "@type": ["CreateAction", "qro:Measuring"],
                 "name": f"the measuring of the crate's law and coherence PUBs by {p2_law.MEASURE_SET}",
                 "object": sorted([{"@id": question["@id"]}] + [{"@id": p["@id"]} for p in measured_pubs(idx)],
                                  key=lambda r: r["@id"]),
                 "result": sorted([{"@id": e["@id"]} for e in contrast_entities + measurements],
                                  key=lambda r: r["@id"]),
                 "qro:alpha": rational(ALPHA), "qro:family": family,
                 "qro:implementation": ["qro.p2_measures 0.1.0"]}
    holds = []
    carried = {e["sha256"] for e in idx.of_type("File") if isinstance(e.get("sha256"), str) and reader.local_file(e)}
    for comp in sorted(idx.of_type("qro:Compile"), key=lambda e: e["@id"]):
        cid = comp["@id"]
        if not cid.startswith("#compile-"):
            raise ValueError(f"{cid}: a Compile's id is #compile-<device>-<bundle>")
        named = p2_hold.read_manifest(_file_bytes(crate_dir, manifest_of(idx, comp), "the manifest"))
        holds.append({"@id": "#hold-" + cid[len("#compile-"):], "@type": ["CreateAction", "qro:Hold"],
                      "qro:heldCompile": {"@id": cid}, "qro:holdRule": p2_hold.RULE,
                      "qro:exactHold": p2_hold.claim(named, carried)})
    new = sorted([measuring] + contrast_entities + measurements + holds, key=lambda e: e["@id"])
    return terms, new


def measurements(md):
    """{(pub id, measure): {"in_scope": int, "value": Fraction or None, "lower": ..., "upper": ...}}: the measurement
    values a crate carries, read from its metadata. Each is CHECKED by step 6 once the checker has accepted the
    crate."""
    def frac(e, key):
        x = e.get(key)
        return None if x is None or x == "none" else Fraction(x)
    out = {}
    for e in Index(md).of_type("qro:Measurement"):
        out[(e["qro:measuredPub"]["@id"], e["qro:measure"])] = {
            "in_scope": e["qro:inScope"], "value": frac(e, "qro:value"), "lower": frac(e, "qro:lower"),
            "upper": frac(e, "qro:upper")}
    return out
