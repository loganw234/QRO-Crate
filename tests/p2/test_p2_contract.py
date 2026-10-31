"""P2's contract with P1's generator (P2's design, item 9): `question_files` and `contribute` are pure functions of the
crate's files and P1's entities, held by T1 to T4 with stand-in entities (P1's real generator is P2.2's to hold):
(T1) the same bytes with the metadata file absent, garbage, another crate's, or the crate's own saying otherwise in
each term a contribute that read it would take; (T2) each producing function patched to a sentinel puts the sentinel
in the output, so no field came from a record; (T3) a Quantum-Film record's own claims change nothing, a raw result's
bytes change the measurements; (T4) two calls, and the entities in another order, the same bytes. And the call as
P1's generator makes it, with two arguments; the entities `contribute` writes, as docs/P2.md names them; and what each
function refuses."""
import json
from fractions import Fraction
from pathlib import Path

import pytest
from p2_builder import SMALL_LAW_COUNTS, SOURCE_PATH, data, raw_ibm, real_model, rows_of, sha, small_model

from qro import canonical, p2_hold, p2_interval, p2_law, p2_measures

F = Fraction


def p1_side(tmp_path, model=None, name="crate"):
    """A crate's files written, and the entities P1's generator would hand over: every entity of the model with each
    File's digest and size, and none of P2's."""
    m = model or small_model()
    dest = tmp_path / name
    for path, b in m.files.items():
        target = dest.joinpath(*path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b)
    ents = {i: json.loads(json.dumps(e)) for i, e in m.ents.items()}
    for path, b in m.files.items():
        ents[path].update(sha256=sha(b), contentSize=str(len(b)))
    return dest, ents, m


def output(dest, ents, m):
    terms, new = p2_measures.contribute(dest, ents, source=m.source)
    return json.dumps({"terms": terms, "new": new}, sort_keys=True).encode("ascii")


def by_id(out):
    return {e["@id"]: e for e in json.loads(out)["new"]}


def reseal(dest, ents, rel, b):
    dest.joinpath(*rel.split("/")).write_bytes(b)
    ents[rel].update(sha256=sha(b), contentSize=str(len(b)))


# -- T1 ----------------------------------------------------------------------------------------------------------------
def saying_otherwise(tmp_path):
    """The small crate's own metadata, as a whole build writes it, with `#measuring`'s family and name and the Hold's
    word changed: the three terms whose reading from the metadata the first verifier's C1, C3 and C2b planted."""
    md = json.loads((small_model().write(tmp_path / "whole") / canonical.DESCRIPTOR).read_bytes())
    ents = {e["@id"]: e for e in md["@graph"]}
    assert (ents["#measuring"]["qro:family"], ents["#hold-synth-morning"]["qro:exactHold"]) == (5, "holds")
    ents["#measuring"].update({"qro:family": 99, "name": "a name only the metadata file holds"})
    ents["#hold-synth-morning"]["qro:exactHold"] = "withheld"
    return canonical.write(md)


def test_t1_the_output_is_the_same_bytes_whatever_the_metadata_file_holds(tmp_path):
    """The metadata file is never read. Garbage; another crate's; this crate's own, saying otherwise in the family, the
    Measuring's name and the Hold's word, so that a contribute reading any of them would change its output (the first
    verifier's D5: C1, C2b and C3 each read one of them, and the other contents could not tell); and none."""
    dest, ents, m = p1_side(tmp_path)
    first = output(dest, ents, m)
    meta = dest / canonical.DESCRIPTOR
    other = real_model().write(tmp_path / "other")
    for content in (b"garbage", (other / canonical.DESCRIPTOR).read_bytes(), saying_otherwise(tmp_path), None):
        if content is None:
            meta.unlink()
        else:
            meta.write_bytes(content)
        assert output(dest, ents, m) == first


def test_contribute_called_as_p1s_generator_calls_it_takes_v0s_source_circuit(tmp_path):
    """P1's generator calls `contribute(crate_dir, entities)`, with two arguments (P1.md, 2026-10-26T10:55:57Z): the
    default `source` is v0's source circuit, so on a crate that holds it the law circuit is found, and the output is the
    same bytes as a call that names that circuit (the first verifier's D5: C7, the default changed, survived)."""
    dest, ents, m = p1_side(tmp_path, real_model())
    assert m.source == p2_law.SOURCE_CIRCUIT
    terms, new = p2_measures.contribute(dest, ents)
    assert terms["qro:lawCircuit"] == {"@id": SOURCE_PATH}
    assert json.dumps({"terms": terms, "new": new}, sort_keys=True).encode("ascii") == output(dest, ents, m)


# -- T2 ----------------------------------------------------------------------------------------------------------------
def test_t2_a_measured_value_is_the_one_value_gives(tmp_path, monkeypatch):
    dest, ents, m = p1_side(tmp_path)
    monkeypatch.setattr(p2_measures, "value",
                        lambda measure, counts, law, basis=None: p2_measures.Value(measure, 7, F(12345, 67891), None,
                                                                                   None))
    got = by_id(output(dest, ents, m))
    ms = [e for e in got.values() if e["@type"] == "qro:Measurement"]
    assert ms and all(e["qro:value"] == "12345/67891" and e["qro:inScope"] == 7 for e in ms)
    assert got["#measuring"]["qro:family"] == 0, "no certified interval: the sentinel carries no map"


def test_t2_an_interval_is_the_one_interval_gives(tmp_path, monkeypatch):
    dest, ents, m = p1_side(tmp_path)
    monkeypatch.setattr(p2_interval, "interval", lambda total, n, family, alpha=None: (F(1, 7777), F(2, 7777)))
    got = by_id(output(dest, ents, m))
    e = got["#measurement-joblaw-0-n-crystal-share"]
    assert (e["qro:lower"], e["qro:upper"]) == ("1/7777", "2/7777")
    e = got["#measurement-jobcoh-0-x0x1"]
    assert (e["qro:lower"], e["qro:upper"]) == (canonical_rational(2 * F(1, 7777) - 1),
                                                canonical_rational(2 * F(2, 7777) - 1))


def canonical_rational(q):
    from qro import spelling
    return spelling.rational(q)


def test_t2_a_class_is_the_one_classes_gives(tmp_path, monkeypatch):
    dest, ents, m = p1_side(tmp_path)
    sentinel = {(ms, t): p2_law.Contrast(ms, t, "integrity", F(31337, 1000) if ms in p2_law.SCALAR else None,
                                         F(-1, 3) if ms in p2_law.SCALAR else None)
                for ms in p2_law.MEASURES for t in p2_law.TWINS}
    monkeypatch.setattr(p2_law, "classes", lambda law: sentinel)
    got = by_id(output(dest, ents, m))
    cs = [e for e in got.values() if e["@type"] == "qro:Contrast"]
    assert len(cs) == 20 and all(e["qro:class"] == "integrity" for e in cs)
    assert got["#contrast-x0x1-uniform"]["qro:lawValue"] == "31337/1000"


def test_t2_a_holds_word_is_the_one_claim_gives(tmp_path, monkeypatch):
    dest, ents, m = p1_side(tmp_path)
    monkeypatch.setattr(p2_hold, "claim", lambda named, carried: "unexposed")
    assert by_id(output(dest, ents, m))["#hold-synth-morning"]["qro:exactHold"] == "unexposed"


# -- T3 ----------------------------------------------------------------------------------------------------------------
def test_t3_a_records_own_claims_change_nothing(tmp_path):
    dest, ents, m = p1_side(tmp_path)
    first = output(dest, ents, m)
    rec = json.loads((dest / "run" / "joblaw-pub0-law.json").read_bytes())
    rec["counts"] = [[[0, 1], 40]]
    reseal(dest, ents, "run/joblaw-pub0-law.json", json.dumps(rec).encode("ascii"))
    verdict = b'{"verdict": "pass", "law_error": 0.0}\n'
    dest.joinpath("bundle", "verdict.json").write_bytes(verdict)
    ents["bundle/verdict.json"] = {"@id": "bundle/verdict.json", "@type": "File", "sha256": sha(verdict),
                                   "contentSize": str(len(verdict)), "encodingFormat": "application/json"}
    doc = json.loads((dest / "bundle" / "manifest.json").read_bytes())
    for job in doc["jobs"]:
        for c in job["circuits"]:
            c["isa"] = {"law_error": 0.5, "verdict": "fail"}
    reseal(dest, ents, "bundle/manifest.json", json.dumps(doc).encode("ascii"))
    assert output(dest, ents, m) == first


def test_t3_a_raw_results_bytes_change_the_measurements(tmp_path):
    dest, ents, m = p1_side(tmp_path)
    first = by_id(output(dest, ents, m))
    counts = dict(SMALL_LAW_COUNTS)
    counts[(0, 2)] -= 1
    counts[(0, 1)] += 1
    reseal(dest, ents, "run/joblaw-raw.json", raw_ibm([rows_of(counts)]))
    second = by_id(output(dest, ents, m))
    i = "#measurement-joblaw-0-forbidden-share"
    assert (first[i]["qro:value"], second[i]["qro:value"]) == ("3/38", "2/19")


def test_t3_the_real_manifests_isa_block_changes_nothing(tmp_path):
    dest, ents, m = p1_side(tmp_path, real_model())
    first = output(dest, ents, m)
    doc = json.loads(data("manifest.json"))
    for job in doc["jobs"]:
        for c in job["circuits"]:
            c["isa"]["law_error"] = 0.25
    reseal(dest, ents, "bundle/manifest.json", json.dumps(doc).encode("ascii"))
    assert output(dest, ents, m) == first


# -- T4 ----------------------------------------------------------------------------------------------------------------
def test_t4_two_calls_and_the_entities_in_another_order_give_the_same_bytes(tmp_path):
    dest, ents, m = p1_side(tmp_path)
    first = output(dest, ents, m)
    assert output(dest, ents, m) == first
    assert output(dest, dict(reversed(list(ents.items()))), m) == first
    assert ents == p1_side(tmp_path, small_model(), "again")[1], "contribute changes no entity it is handed"


def floats_in(x):
    if isinstance(x, float):
        return [x]
    if isinstance(x, dict):
        return [f for v in x.values() for f in floats_in(v)]
    if isinstance(x, (list, tuple)):
        return [f for v in x for f in floats_in(v)]
    return []


def test_contribute_writes_the_entities_docs_p2_names(tmp_path):
    """docs/P2.md's table "What P2 writes", on the small crate: the question's four terms; `#measuring`, with its object
    the question and the measured Pubs, its result the Contrasts and the Measurements, alpha 1/20 and the family; a
    Contrast for each measure and twin, with values for a scalar measure only; a Measurement for each measure of each
    law and coherence Pub, its id from its Pub's and its interval for a certified measure only; one Hold per Compile."""
    dest, ents, m = p1_side(tmp_path)
    terms, new = p2_measures.contribute(dest, ents, source=m.source)
    assert terms == {"qro:law": {"@id": "question/law.json"}, "qro:lawCircuit": {"@id": "circuits/small-law.qasm"},
                     "qro:measureSet": "qro-measures/1", "qro:twins": ["dephased", "uniform"]}
    got = {e["@id"]: e for e in new}
    assert [e["@id"] for e in new] == sorted(got)
    contrasts = {f"#contrast-{ms}-{t}" for ms in p2_law.MEASURES for t in p2_law.TWINS}
    measured = {"#pub-joblaw-0": p2_measures.LAW_MEASURES, "#pub-jobcoh-0": ("x0x1",), "#pub-jobcoh-1": ("y0y1",)}
    measurements = {f"#measurement-{p[len('#pub-'):]}-{ms}" for p, mss in measured.items() for ms in mss}
    assert set(got) == {"#measuring", "#hold-synth-morning"} | contrasts | measurements and len(contrasts) == 20
    measuring = got["#measuring"]
    assert measuring["@type"] == ["CreateAction", "qro:Measuring"]
    assert (measuring["qro:alpha"], measuring["qro:family"]) == ("1/20", 5)
    assert measuring["qro:implementation"] == ["qro.p2_measures 0.1.0"] and measuring["name"]
    assert measuring["object"] == [{"@id": i} for i in sorted([*measured, "#question"])]
    assert measuring["result"] == [{"@id": i} for i in sorted(contrasts | measurements)]
    for i in contrasts:
        e = got[i]
        assert e["@type"] == "qro:Contrast" and i == f"#contrast-{e['qro:measure']}-{e['qro:twin']}"
        assert e["qro:class"] in ("signal", "integrity")
        assert ("qro:lawValue" in e) == ("qro:twinValue" in e) == (e["qro:measure"] in p2_law.SCALAR)
    for i in measurements:
        e = got[i]
        pub = e["qro:measuredPub"]["@id"]
        assert e["@type"] == "qro:Measurement" and i == f"#measurement-{pub[len('#pub-'):]}-{e['qro:measure']}"
        assert e["qro:measure"] in measured[pub] and type(e["qro:inScope"]) is int and e["qro:value"] != "none"
        assert ("qro:lower" in e) == ("qro:upper" in e) == (e["qro:measure"] in p2_law.CERTIFIED)
    assert got["#hold-synth-morning"] == {"@id": "#hold-synth-morning", "@type": ["CreateAction", "qro:Hold"],
                                          "qro:heldCompile": {"@id": "#compile-synth-morning"},
                                          "qro:holdRule": "qro-exact-hold/1", "qro:exactHold": "holds"}


def test_no_float_is_ever_written_to_a_crate(tmp_path):
    """Every value P2 writes is a rational in the profile's spelling, a whole number, a word or text."""
    for model, name in ((small_model(), "small"), (real_model(), "real")):
        dest, ents, m = p1_side(tmp_path, model, name)
        terms, new = p2_measures.contribute(dest, ents, source=m.source)
        assert floats_in(terms) == [] and floats_in(new) == []
    assert floats_in({"a": [1, {"b": 0.5}]}) == [0.5], "the control"


# -- question_files ----------------------------------------------------------------------------------------------------
def test_question_files_gives_v0s_law_for_a_crate_that_holds_the_source_circuit(tmp_path):
    (tmp_path / "deep" / "er").mkdir(parents=True)
    (tmp_path / "deep" / "er" / "c.qasm").write_bytes(data("circuit-ed767c01bd4b851d.qasm"))
    assert p2_measures.question_files(tmp_path) == {"law.json": p2_law.law_bytes()}


def test_question_files_never_reads_the_metadata_file_and_refuses_another_question(tmp_path):
    (tmp_path / canonical.DESCRIPTOR).write_bytes(data("circuit-ed767c01bd4b851d.qasm"))
    (tmp_path / "law.qasm").write_bytes(data("law.qasm"))
    with pytest.raises(ValueError, match="no file of the crate is the source circuit ed767c01bd4b851d"):
        p2_measures.question_files(tmp_path)


def test_question_files_skips_the_roots_metadata_file_alone(tmp_path):
    """The one file skipped is the root's metadata file (the first verifier's gap: the skip widened to every file of
    that name survived, and so did the skip widened to every file at the root). A file of that name below the root is
    a file of the crate like any other, and so is a file at the root: the source circuit in either is found."""
    below, flat = tmp_path / "below", tmp_path / "flat"
    (below / "sub").mkdir(parents=True)
    (below / "sub" / canonical.DESCRIPTOR).write_bytes(data("circuit-ed767c01bd4b851d.qasm"))
    assert p2_measures.question_files(below) == {"law.json": p2_law.law_bytes()}
    flat.mkdir()
    (flat / "circuit.qasm").write_bytes(data("circuit-ed767c01bd4b851d.qasm"))
    assert p2_measures.question_files(flat) == {"law.json": p2_law.law_bytes()}


# -- what contribute refuses -------------------------------------------------------------------------------------------
def test_contribute_raises_where_the_crate_holds_no_question_it_can_use(tmp_path):
    dest, ents, m = p1_side(tmp_path)
    q = ents.pop("#question")
    with pytest.raises(ValueError, match="holds 0 qro:Question entities"):
        p2_measures.contribute(dest, ents, source=m.source)
    ents["#question"] = q
    ents["#question-2"] = {**q, "@id": "#question-2"}
    with pytest.raises(ValueError, match="holds 2 qro:Question entities"):
        p2_measures.contribute(dest, ents, source=m.source)
    del ents["#question-2"]
    with pytest.raises(ValueError, match="the question's object holds no source circuit"):
        p2_measures.contribute(dest, ents)                       # v0's source circuit, which this crate lacks


def test_contribute_raises_on_a_law_or_a_manifest_it_cannot_read(tmp_path):
    dest, ents, m = p1_side(tmp_path)
    (dest / "question" / "law.json").write_bytes(b"{}\n")
    with pytest.raises(p2_law.LawError):
        p2_measures.contribute(dest, ents, source=m.source)
    dest, ents, m = p1_side(tmp_path, name="second")
    reseal(dest, ents, "bundle/manifest.json", b"[]\n")
    with pytest.raises(p2_hold.HoldError):
        p2_measures.contribute(dest, ents, source=m.source)
    (dest / "question" / "law.json").unlink()
    with pytest.raises(OSError):
        p2_measures.contribute(dest, ents, source=m.source)


def test_contribute_raises_on_a_compile_it_cannot_name(tmp_path):
    dest, ents, m = p1_side(tmp_path)
    ents["#bundle-compile"] = {**ents.pop("#compile-synth-morning"), "@id": "#bundle-compile"}
    with pytest.raises(ValueError, match="a Compile's id is #compile-<device>-<bundle>"):
        p2_measures.contribute(dest, ents, source=m.source)
    ents["#compile-synth-morning"] = ents.pop("#bundle-compile")
    ents["#compile-synth-morning"]["@id"] = "#compile-synth-morning"
    ents["#compile-synth-morning"]["object"] = [r for r in ents["#compile-synth-morning"]["object"]
                                                if r["@id"] != "bundle/manifest.json"]
    with pytest.raises(p2_hold.HoldError, match="0 manifest.json files"):
        p2_measures.contribute(dest, ents, source=m.source)


def test_contribute_reads_a_file_only_by_a_path_in_the_crate(tmp_path):
    dest, ents, m = p1_side(tmp_path)
    ents["#question"]["object"] = ents["#question"]["object"] + [{"@id": "../outside.qasm"}]
    ents["../outside.qasm"] = {"@id": "../outside.qasm", "@type": "File"}
    (tmp_path / "outside.qasm").write_bytes(Path(dest, "circuits", "small-law.qasm").read_bytes())
    with pytest.raises(ValueError):
        p2_measures.contribute(dest, ents, source=m.source)
