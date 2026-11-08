"""P2 on P1's twin, the tree as merged (P2's design, items 9 and 12; P2.2): the twin as P1's adapter builds it with P2's
module present carries P2's question terms and entities and is accepted by the whole checker, steps 6 and 7 among its
steps; its two measurements are the coherence records' counts, which P2 never reads; P2's contract with P1's generator
is held with P1's real generator and the entities it really hands over, where P2.1 held it with stand-ins (T1 to T4);
step 9 holds the terms of P2's entities that steps 6 and 7 leave REPORTED; and step 7 passes over the files of a
Compile's `result` that are no gate list, the twin's QPY and ISA QASM 3 files, while a gate list there that its
manifest does not name is refused.

The twin is built once in the process (controls/plants_p1.py) and copied for each test that changes it."""
import copy
import json
from fractions import Fraction
from pathlib import Path

import pytest

from controls import plants_p1 as toolkit
from controls import plants_p2
from qro import canonical, checker, p2_hold, p2_interval, p2_law, p2_measures, p2_steps, reader, register_p1
from qro import register_p2, spelling
from qro.refusal import Refused

IBM = "qro-p1-ibm"
SOURCE = "2026-09-25/p3/circuit-ed767c01bd4b851d.qasm"
P2_TYPES = ("qro:Measuring", "qro:Contrast", "qro:Measurement", "qro:Hold")


def read(crate, rel):
    return Path(crate).joinpath(*rel.split("/")).read_bytes()


def metadata(crate):
    return json.loads(read(crate, canonical.DESCRIPTOR))


def by_id(md):
    return {e["@id"]: e for e in md["@graph"]}


def p2_part(md):
    """What P2 wrote in a metadata: the question's four terms and P2's entities, by @id."""
    ids = by_id(md)
    out = {t: ids["#question"].get(t) for t in p2_measures.QUESTION_TERMS}
    out.update({i: e for i, e in ids.items() if set(canonical.types(e)) & set(P2_TYPES)})
    return out


def generated(crate):
    return register_p1.GENERATORS[IBM](crate)


def body(md):
    return canonical.dumps(canonical.body(md))


@pytest.fixture(scope="module")
def twin(tmp_path_factory):
    crate = toolkit.twin_crate(tmp_path_factory.mktemp("p2-on-twin"))
    return crate, metadata(crate)


# -- the twin, with P2 -----------------------------------------------------------------------------------------------------
def test_the_twin_carries_p2s_question_terms_and_entities(twin):
    crate, md = twin
    ids = by_id(md)
    q = ids["#question"]
    assert (q["qro:law"], q["qro:lawCircuit"], q["qro:measureSet"], q["qro:twins"]) == (
        {"@id": "question/law.json"}, {"@id": SOURCE}, "qro-measures/1", ["dephased", "uniform"])
    assert read(crate, "question/law.json") == p2_law.law_bytes()
    kinds = {}
    for e in md["@graph"]:
        for t in set(canonical.types(e)) & set(P2_TYPES):
            kinds[t] = kinds.get(t, 0) + 1
    assert kinds == {"qro:Measuring": 1, "qro:Contrast": 20, "qro:Measurement": 2, "qro:Hold": 3}
    assert (ids["#measuring"]["qro:alpha"], ids["#measuring"]["qro:family"]) == ("1/20", 2)
    holds = sorted((e["qro:heldCompile"]["@id"], e["qro:exactHold"]) for e in ids.values()
                   if "qro:Hold" in canonical.types(e))
    assert holds ==[("#compile-ibm_kingston-morning", "holds"), ("#compile-ibm_kingston-sheet-01", "holds"),
                     ("#compile-ibm_kingston-sheet-02", "holds")]
    assert register_p2._enters(md, 6, ("qro:Measuring", "qro:Contrast", "qro:Measurement"))
    assert register_p2._enters(md, 7, ("qro:Hold",))


def test_the_twin_is_accepted_by_the_whole_checker_with_p2s_steps_registered(twin):
    crate, md = twin
    checker.load()
    assert checker.STEPS[6] is register_p2.step6 and checker.STEPS[7] is register_p2.step7
    assert canonical.body_digest(checker.check(crate)) == canonical.body_digest(md)
    assert p2_steps.step6(crate, md) is None and p2_steps.step7(crate, md) is None


def test_the_twins_two_measurements_are_the_coherence_records_counts(twin):
    """The morning coherence job's two PUBs, x0x1 and y0y1, measured from the raw bytes (through P1.1's pub_counts),
    equal the parities of Quantum-Film's device-run records' counts, which P2 never reads; each interval is the
    certified one at the crate's family of 2."""
    crate, md = twin
    ids = by_id(md)
    ms = sorted((e for e in ids.values() if "qro:Measurement" in canonical.types(e)), key=lambda e: e["qro:measure"])
    assert [m["qro:measure"] for m in ms] == ["x0x1", "y0y1"]
    for m in ms:
        pub = ids[m["qro:measuredPub"]["@id"]]
        assert pub["qro:role"] == "coherence" and pub["@id"].startswith("#pub-")
        record = json.loads(read(crate, pub["qro:record"]["@id"]))
        shots = sum(n for _, n in record["counts"])
        agree = sum(n for ones, n in record["counts"] if (0 in ones) == (1 in ones))
        assert m["qro:inScope"] == shots == 4096
        assert m["qro:value"] == spelling.rational(Fraction(2 * agree - shots, shots))
        lo, hi = p2_interval.mapped(p2_interval.interval(agree, shots, 2), p2_interval.PARITY)
        assert (m["qro:lower"], m["qro:upper"]) == (spelling.rational(lo), spelling.rational(hi))
    assert [round(float(Fraction(m["qro:value"])), 4) for m in ms] == [0.3315, 0.3296]


# -- the contract, with P1's real generator --------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def handed(twin):
    """What P1's real generator hands P2's `contribute` on the twin: the call's arguments, recorded by a wrapper of the
    real function, and what it returned."""
    crate, _ = twin
    calls, real = [], p2_measures.contribute

    def recorder(*args, **kwargs):
        got = real(*args, **kwargs)
        calls.append((args, kwargs, copy.deepcopy(got)))
        return got
    with pytest.MonkeyPatch.context() as m:
        m.setattr(p2_measures, "contribute", recorder)
        md = generated(crate)
    return calls, md


def test_p1s_generator_calls_contribute_once_with_two_arguments_and_p1s_entities_alone(twin, handed):
    crate, built = twin
    calls, md = handed
    assert len(calls) == 1
    (crate_dir, entities), kwargs, (terms, new) = calls[0]
    assert kwargs == {} and Path(crate_dir) == crate
    assert body(md) == body(built), "the generator, recorded, makes the twin's metadata"
    p1_ids = {e["@id"] for e in built["@graph"]} - {i for i in p2_part(built) if i.startswith("#")}
    p1_ids -= {canonical.DESCRIPTOR, canonical.ROOT} | {e["@id"] for e in built["@graph"] if "Profile" in canonical.types(e)}
    assert set(entities) == p1_ids
    assert not any(set(canonical.types(e)) & set(P2_TYPES) for e in entities.values())
    assert not any(t in entities["#question"] for t in p2_measures.QUESTION_TERMS)
    assert {**terms, **{e["@id"]: e for e in new}} == p2_part(built)


def test_t1_the_generators_p2_part_is_the_same_bytes_whatever_the_metadata_file_holds(twin, tmp_path):
    """The metadata file is never read: absent, garbage, the class-declared crate's own (saying signal), and the
    twin's own with the family, the Measuring's name and a Hold's word changed, P2's part of what P1's generator makes
    is the same, and so is the whole body."""
    _, built = twin
    crate = toolkit.twin_crate(tmp_path / "t1")
    meta = crate / canonical.DESCRIPTOR
    declared = plants_p2.class_declared(toolkit.twin_crate(tmp_path / "declared"))
    saying = metadata(crate)
    ids = by_id(saying)
    ids["#measuring"].update({"qro:family": 99, "name": "a name only the metadata file holds"})
    ids["#hold-ibm_kingston-morning"]["qro:exactHold"] = "withheld"
    for content in (b"garbage", read(declared, canonical.DESCRIPTOR), canonical.dumps(saying), None):
        if content is None:
            meta.unlink()
        else:
            meta.write_bytes(content)
        md = generated(crate)
        assert p2_part(md) == p2_part(built) and body(md) == body(built)


@pytest.mark.parametrize("module, name, sentinel, seen", [
    (p2_measures, "value", lambda measure, counts, law, basis=None: p2_measures.Value(measure, 7, Fraction(12345, 67891),
                                                                                      None, None),
     lambda part: all(e["qro:value"] == "12345/67891" and e["qro:inScope"] == 7 for e in part.values()
                      if isinstance(e, dict) and e.get("@type") == "qro:Measurement")),
    (p2_interval, "interval", lambda total, n, family, alpha=None: (Fraction(1, 7777), Fraction(2, 7777)),
     lambda part: all((e["qro:lower"], e["qro:upper"]) == (spelling.rational(2 * Fraction(1, 7777) - 1),
                                                            spelling.rational(2 * Fraction(2, 7777) - 1))
                      for e in part.values() if isinstance(e, dict) and e.get("@type") == "qro:Measurement")),
    (p2_law, "classes", lambda law: {(m, t): p2_law.Contrast(m, t, "integrity", Fraction(31337, 1000) if m in
                                                             p2_law.SCALAR else None,
                                                             Fraction(-1, 3) if m in p2_law.SCALAR else None)
                                     for m in p2_law.MEASURES for t in p2_law.TWINS},
     lambda part: part["#contrast-x0x1-uniform"]["qro:lawValue"] == "31337/1000"
     and all(e["qro:class"] == "integrity" for e in part.values() if isinstance(e, dict) and e.get("@type") == "qro:Contrast")),
    (p2_hold, "claim", lambda named, carried: "unexposed",
     lambda part: all(e["qro:exactHold"] == "unexposed" for e in part.values()
                      if isinstance(e, dict) and "qro:Hold" in canonical.types(e))),
], ids=["value", "interval", "classes", "claim"])
def test_t2_each_producing_function_patched_to_a_sentinel_puts_it_in_the_generators_output(twin, monkeypatch, module,
                                                                                         name, sentinel, seen):
    """Each of P2's values in the twin's metadata is made by the function the steps use, looked up when it is called:
    patched to a sentinel, the sentinel is what P1's generator writes; so no value came from a record."""
    crate, built = twin
    assert not seen(p2_part(built)), "the sentinel is not what the honest twin holds"
    monkeypatch.setattr(module, name, sentinel)
    p2_law.clear()
    try:
        assert seen(p2_part(generated(crate)))
    finally:
        p2_law.clear()


def test_t3_a_records_own_claim_changes_nothing_of_p2s(twin, tmp_path):
    """Quantum-Film's own verdict on the compile, the manifest's `isa` block, said otherwise on every circuit (each of
    its figures, the law's error among them, made 0.25), the manifest's digest recomputed in the lines and markers that
    hold it: the crate is another (its manifest's bytes), and P2's part of it is the same."""
    _, built = twin
    crate = toolkit.twin_crate(tmp_path)
    forge = toolkit.Forge(crate)
    manifest = f"{toolkit.MORNING_BUNDLE}/manifest.json"
    figures = []

    def isa(m):
        for job in m["jobs"]:
            for c in job["circuits"]:
                figures.extend(c["isa"])
                c["isa"] = {k: 0.25 for k in c["isa"]}
    forge.edit_json(manifest, isa)
    forge.reseal_bundle(toolkit.MORNING_BUNDLE)
    assert "law_error" in figures
    md = generated(crate)
    assert body(md) != body(built) and p2_part(md) == p2_part(built)


def test_t3_a_raw_results_bytes_change_the_measurements(twin, tmp_path):
    """One shot of the coherence job's first PUB moved to the outcome with qubit 0 flipped, the raw text re-encoded and
    every digest held over it recomputed (the record's counts and own digest, the read's result record and its MANIFEST
    entry), as P1's `shot-moved-resealed` does: x0x1, read from the raw bytes, moves by 2 over the PUB's 4,096 shots, and
    nothing else of P2's does."""
    _, built = twin
    crate = toolkit.twin_crate(tmp_path)
    forge = toolkit.Forge(crate)
    raw = forge.read(toolkit.COHERENCE_RAW)
    old = toolkit.rows_of(toolkit.array_of(json.loads(raw), 0)["__value__"])[0][0]
    data, old, new = toolkit.moved_shot(raw, to=old ^ 1)
    forge.write(toolkit.COHERENCE_RAW, data)
    record = forge.json(toolkit.COHERENCE_RECORD)
    counts = {tuple(q): n for q, n in record["counts"]}
    counts[toolkit.outcome_of(old)] -= 1
    counts[toolkit.outcome_of(new)] = counts.get(toolkit.outcome_of(new), 0) + 1
    record["counts"] = [[list(q), n] for q, n in sorted(counts.items()) if n]
    forge.put_record(toolkit.COHERENCE_RECORD, record)
    forge.reseal_raw(f"{toolkit.MORNING_RUN}/coherence-line.json", toolkit.COHERENCE_RAW)
    before, after = p2_part(built), p2_part(generated(crate))
    moved = [i for i in before if before[i] != after.get(i)]
    x0x1 = next(i for i in before if i.startswith("#measurement-") and i.endswith("-0-x0x1"))
    assert moved == [x0x1] and set(after) == set(before)
    step = Fraction(after[x0x1]["qro:value"]) - Fraction(before[x0x1]["qro:value"])
    assert abs(step) == Fraction(2, 4096) and after[x0x1]["qro:inScope"] == 4096


def test_t4_two_generations_and_the_entities_in_another_order_give_the_same_bytes(twin, handed):
    crate, built = twin
    calls, md = handed
    assert body(generated(crate)) == body(md) == body(built)
    (crate_dir, entities), _, (terms, new) = calls[0]
    again = p2_measures.contribute(crate_dir, dict(reversed(list(copy.deepcopy(entities).items()))))
    assert json.dumps(again, sort_keys=True) == json.dumps((terms, new), sort_keys=True)


# -- step 9 holds P2's REPORTED terms of the body --------------------------------------------------------------------------
@pytest.mark.parametrize("term, edit", [
    ("name", lambda e: e.update(name="a measuring under another name")),
    ("object", lambda e: e.update(object=e["object"][:-1])),
    ("result", lambda e: e.update(result=e["result"][1:])),
], ids=["name", "object", "result"])
def test_a_reported_term_of_the_measuring_is_refused_by_step_9(tmp_path, term, edit):
    """Step 6 checks #measuring's alpha and family and leaves its name, object and result REPORTED: each edited in the
    twin's metadata, step 6 (and step 7) accept it, and step 9, regenerating, refuses the crate by its own name. (The
    whole checker's other steps read none of P2's entities: the controls above run it whole.)"""
    crate = toolkit.patch(toolkit.twin_crate(tmp_path), lambda g: edit(toolkit.entity(g, "#measuring")))
    md = reader.read(read(crate, canonical.DESCRIPTOR))
    assert p2_steps.step6(crate, md) is None and p2_steps.step7(crate, md) is None
    checker.load()
    with pytest.raises(Refused) as x:
        checker.regenerated(crate, md)
    assert x.value.name == "metadata-generated" and x.value.where.endswith(" of the body"), (term, x.value.where)


def test_the_measurings_implementation_is_a_header_term_which_no_step_holds(twin, tmp_path):
    """`qro:implementation` is a header term (P0's): step 9 compares the body, which holds no header term, so the
    implementation the twin names may be edited, and steps 6, 7 and 9 accept the crate with the same identity."""
    _, built = twin
    crate = toolkit.patch(toolkit.twin_crate(tmp_path),
                          lambda g: toolkit.entity(g, "#measuring").update({"qro:implementation": ["qro.p2_measures 9.9.9"]}))
    md = reader.read(read(crate, canonical.DESCRIPTOR))
    assert by_id(md)["#measuring"]["qro:implementation"] == ["qro.p2_measures 9.9.9"]
    checker.load()
    assert p2_steps.step6(crate, md) is None and p2_steps.step7(crate, md) is None
    assert checker.regenerated(crate, md) is None
    assert canonical.body_digest(md) == canonical.body_digest(built)


# -- P2's stated limit 15, as the seam leaves it ---------------------------------------------------------------------------
def test_the_stated_limit_the_twin_stripped_of_p2s_file_and_regenerated_is_accepted_claiming_no_measure(twin, tmp_path):
    """The lead's seam ruling (2026-11-08): P1's generators call `contribute` only for a crate that holds files under
    question/. So the twin with question/law.json taken out and its metadata regenerated carries none of P2's terms or
    entities, and every step accepts it: it claims no measure and no hold, and steps 6 and 7 do not enter."""
    _, built = twin
    crate = toolkit.twin_crate(tmp_path)
    (crate / "question" / "law.json").unlink()
    (crate / "question").rmdir()
    md = metadata(toolkit.rebuild(crate))
    assert all(v is None for k, v in p2_part(md).items() if k.startswith("qro:")) and len(p2_part(md)) == 4
    assert "#question-files" not in by_id(md)
    assert not register_p2._enters(md, 6, ("qro:Measuring", "qro:Contrast", "qro:Measurement"))
    assert not register_p2._enters(md, 7, ("qro:Hold",))
    checker.load()
    assert canonical.body_digest(checker.check(crate)) == canonical.body_digest(md) != canonical.body_digest(built)


# -- step 7 and the files of a Compile that are no gate list ---------------------------------------------------------------
def test_step_7_passes_over_the_twins_qpy_and_isa_files_in_each_compiles_result(twin):
    """Each of the twin's Compiles lists, in its `result`, QPY and ISA QASM 3 files beside its gate lists: the morning's
    four of each, each sheet's one. Step 7 asks only that a `.gates.json` there be named by the manifest, and passes over
    the others, whatever their digests: it accepts the twin."""
    crate, md = twin
    ids = by_id(md)
    for cid, n in (("#compile-ibm_kingston-morning", 4), ("#compile-ibm_kingston-sheet-01", 1),
                   ("#compile-ibm_kingston-sheet-02", 1)):
        result = [r["@id"] for r in ids[cid]["result"]]
        assert [sum(r.endswith(s) for r in result) for s in (".qpy", ".isa.qasm3", ".gates.json")] == [n, n, n], cid
        assert all(ids[r].get("sha256") for r in result)
    assert p2_steps.step7(crate, md) is None


def test_step_7_refuses_a_gate_list_in_a_compiles_result_its_manifest_does_not_name(twin):
    """The control: the morning law QPY's own File, listed again under a name ending `.gates.json` in the morning
    Compile's `result`, is a gate list the manifest does not name, and step 7 refuses it; under its own name it passed."""
    crate, md = twin
    md = copy.deepcopy(md)
    ids = by_id(md)
    qpy = f"{toolkit.MORNING_BUNDLE}/law.qpy"
    stray = dict(ids[qpy], **{"@id": f"{toolkit.MORNING_BUNDLE}/law.qpy.gates.json"})
    md["@graph"].append(stray)
    ids["#compile-ibm_kingston-morning"]["result"].append({"@id": stray["@id"]})
    with pytest.raises(Refused) as x:
        p2_steps.step7(crate, md)
    assert (x.value.name, x.value.where) == ("compile-uncontrolled", "#compile-ibm_kingston-morning result")
    assert "is a gate list its manifest does not name" in x.value.detail
