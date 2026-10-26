"""Step 5: every `qro:Decode`'s raw result re-decoded under the rule and the bit order the crate names, the order held
by a known answer read from the committed circuit. Never from Quantum-Film's verdict file, its manifest or its
decoded counts, none of which the step opens: an honest crate with a lying verdict file is accepted, and a mirrored
one whose verdict file says it holds is refused. Each fault is refused by this step's name (`known-answer`), or by
`step-unbuilt` for a rule not built and `raw-form` for bytes the rule's form does not read."""
import json

import pytest
from p1_builder import (ATLAS_FORM, ATLAS_RULE, JOBS, KA, LAYOUTS, atlas_model, atlas_result, atlas_string, atlas_vector,
                        entity, ibm_model, judge, ka_qasm, known_answer_rows, other_qasm, outcome, raw_ibm, read_md,
                        refusal, sha)

from qro import p1_steps
from qro.refusal import Refused

RAW = "run/jobka-raw.json"
DECODES = ("jobcoh", "jobka", "joblaw")                 # the order the step visits them in
MIRROR = (3, 8, 12, 14, 15)


def verdict(m, tmp_path):
    return judge(m, tmp_path / "crate", 5)


def refused(m, tmp_path, name="known-answer", where=None):
    r = verdict(m, tmp_path)
    assert r is not None, "accepted"
    assert r.name == name, f"{r.name} at {r.where}: {r.detail}"
    if where is not None:
        assert where in r.where, f"{r.where}: {r.detail}"
    return r


def set_all(m, term, value, jobs=DECODES):
    for j in jobs:
        m.ents["#decode-" + j][term] = value


def replace_ka_rows(m, rows):
    m.files[RAW] = raw_ibm([rows], [None], None)
    m.ents[RAW]["qro:shots"] = len(rows)


def test_the_honest_crates_are_accepted(tmp_path):
    assert verdict(ibm_model(), tmp_path / "ibm") is None
    assert verdict(atlas_model(), tmp_path / "atlas") is None


# -- what a Decode must carry -----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("term", ["qro:decodeRule", "qro:bitOrder", "qro:knownAnswer", "object"])
@pytest.mark.parametrize("job", DECODES)
def test_a_decode_missing_a_term_it_must_carry_is_refused(tmp_path, term, job):
    """At that decode, or at the first decode by id whose known answer it is: the known-answer job's decode is every
    other's check, so a term it lacks is found first at jobcoh, which is visited before it."""
    m = ibm_model()
    del m.ents["#decode-" + job][term]
    found_first_at_jobcoh = job == "jobka" and term != "qro:knownAnswer"
    r = refused(m, tmp_path, where="#decode-jobcoh" if found_first_at_jobcoh else f"#decode-{job}")
    if term == "object" and not found_first_at_jobcoh:
        assert "a Decode reads one raw result, and this one lists 0" in r.detail


def test_a_decode_that_reads_two_raw_results_is_refused(tmp_path):
    m = ibm_model()
    m.ents["#decode-jobka"]["object"] = [{"@id": RAW}, {"@id": "run/joblaw-raw.json"}]
    r = refused(m, tmp_path, where="#decode-jobka object")
    assert "lists 2" in r.detail


def test_a_decode_whose_raw_result_no_job_made_is_refused(tmp_path):
    m = ibm_model()
    m.ents["#job-joblaw"]["result"] = [{"@id": "run/joblaw-line.json"}]
    refused(m, tmp_path, where="#decode-joblaw")


# -- the rule and the order -------------------------------------------------------------------------------------------------------
def test_a_rule_that_is_not_built_is_step_unbuilt_by_its_name(tmp_path):
    m = ibm_model()
    m.ents["#decode-jobcoh"]["qro:decodeRule"] = "quantum_film.ibm.decode/v2"
    r = refused(m, tmp_path, "step-unbuilt", "#decode-jobcoh qro:decodeRule")
    assert "quantum_film.ibm.decode/v2" in r.detail


def test_a_rule_for_the_other_raw_form_is_refused_as_a_raw_form_it_does_not_read(tmp_path):
    m = ibm_model()
    set_all(m, "qro:decodeRule", ATLAS_RULE)
    set_all(m, "qro:bitOrder", "atlas-register")
    r = refused(m, tmp_path, "raw-form", "run/jobcoh-raw.json qro:rawForm")
    assert ATLAS_RULE in r.detail


@pytest.mark.parametrize("order", ["circuit-order", "atlas-register"])
def test_an_order_the_rule_does_not_admit_is_refused(tmp_path, order):
    m = ibm_model()
    set_all(m, "qro:bitOrder", order)
    r = refused(m, tmp_path, where="qro:bitOrder")
    assert "does not read the order" in r.detail


def test_a_raw_result_whose_form_the_rule_does_not_read_is_refused(tmp_path):
    m = ibm_model()
    m.ents[RAW]["qro:rawForm"] = ATLAS_FORM
    refused(m, tmp_path, "raw-form", "run/jobka-raw.json qro:rawForm")


# -- the bit order is held by the known answer: bits-mirrored ------------------------------------------------------------------------
def test_the_decode_told_the_mirrored_order_everywhere_is_refused(tmp_path):
    """The control bits-mirrored: the known-answer job's decode, and every other, declared lsb-first. The raw bytes,
    the records and every digest are untouched; the known answer, read the mirror way, does not come out."""
    m = ibm_model()
    set_all(m, "qro:bitOrder", "lsb-first")
    r = refused(m, tmp_path, where="qro:bitOrder")
    assert "does not hold the known answer" in r.detail and "#pub-jobka-0" in r.detail


@pytest.mark.parametrize("flipped, where", [("jobka", "#decode-jobcoh"), ("joblaw", "#decode-joblaw"),
                                            ("jobcoh", "#decode-jobcoh")])
def test_a_decode_that_reads_its_known_answer_in_another_order_is_refused(tmp_path, flipped, where):
    m = ibm_model()
    m.ents["#decode-" + flipped]["qro:bitOrder"] = "lsb-first"
    refused(m, tmp_path, where=where)


def test_the_mirrored_order_with_the_records_and_manifest_made_to_agree_is_still_refused(tmp_path):
    """Mirroring what Quantum-Film's files say moves nothing: the verdict file says it holds, the manifest names the
    known answer, the record's counts are mirrored too. The step opens none of them."""
    m = ibm_model()
    set_all(m, "qro:bitOrder", "lsb-first")
    m.file("run/jobka-verdict.json", json.dumps({"expected": list(KA), "holds": True, "mirror_share": 0.0,
                                                 "modal": list(KA), "share": 0.9, "shots": 40}).encode())
    m.edit_json(m.record("jobka"), lambda r: r.__setitem__("counts", [[list(MIRROR), 40]]))
    m.file("bundle/manifest.json", json.dumps({"known_answer": list(MIRROR), "format": "x"}).encode())
    refused(m, tmp_path)


def test_an_honest_crate_with_a_verdict_file_that_lies_is_accepted(tmp_path):
    m = ibm_model()
    m.file("run/jobka-verdict.json", json.dumps({"expected": [2, 4], "holds": False, "mirror_share": 1.0,
                                                 "modal": [9], "share": 0.0, "shots": 40}).encode())
    m.edit_json(m.record("jobka"), lambda r: r.__setitem__("counts", [[[9], 40]]))
    m.file("bundle/manifest.json", json.dumps({"known_answer": [1, 2], "format": "x"}).encode())
    assert verdict(m, tmp_path) is None


@pytest.mark.parametrize("content", [b"\xff\xfe not even text", b"", b"{"], ids=["not UTF-8", "empty", "unfinished"])
def test_the_verdict_file_and_the_manifest_are_never_opened(tmp_path, content):
    """Quantum-Film's verdict file and bundle manifest are in the crate, listed and held by their digests, and the step
    reads neither: bytes that no JSON parser would take change nothing."""
    m = ibm_model()
    m.file("run/jobka-verdict.json", content)
    m.file("bundle/manifest.json", content)
    assert verdict(m, tmp_path) is None


# -- the known answer's own data ---------------------------------------------------------------------------------------------------------
E_V, MIRROR_V = outcome(KA), outcome(MIRROR)


@pytest.mark.parametrize("rows", [
    [E_V] * 10 + [outcome((0, 1))] * 12 + [0] * 8,                  # another outcome modal
    [E_V] * 10 + [MIRROR_V] * 10,                                   # a tie with the mirror decides nothing
    [MIRROR_V] * 30 + [E_V] * 5,                                    # the mirror modal
    [0] * 40,                                                       # all zero
    [E_V] * 2 + [outcome((q,)) for q in range(16)] * 3,             # no outcome modal enough
], ids=["another outcome modal", "a tie with the mirror", "the mirror modal", "all zero", "nothing modal"])
def test_a_known_answer_whose_expected_set_is_not_the_modal_outcome_is_refused(tmp_path, rows):
    m = ibm_model()
    replace_ka_rows(m, rows)
    r = refused(m, tmp_path)
    assert "does not hold the known answer" in r.detail


def test_a_known_answer_won_by_a_single_shot_over_its_mirror_holds(tmp_path):
    m = ibm_model()
    replace_ka_rows(m, [E_V] * 6 + [MIRROR_V] * 5 + [0] * 3)
    assert verdict(m, tmp_path) is None


def test_the_expected_set_is_read_from_the_circuit_the_commitment_binds(tmp_path):
    """The same rows against a circuit that flips other qubits: the known answer no longer comes out."""
    m = ibm_model()
    flipped = ka_qasm((2, 5, 9, 14))
    m.files["bundle/known-answer.qasm"] = flipped
    m.edit_json(m.record("jobka"), lambda r: r["source"].__setitem__("circuit_sha256", sha(flipped)))
    refused(m, tmp_path)


def test_a_known_answer_circuit_that_is_its_own_mirror_is_refused(tmp_path):
    m = ibm_model()
    sym = ka_qasm((7, 8))
    m.files["bundle/known-answer.qasm"] = sym
    m.edit_json(m.record("jobka"), lambda r: r["source"].__setitem__("circuit_sha256", sha(sym)))
    replace_ka_rows(m, [outcome((7, 8))] * 40)
    r = refused(m, tmp_path)
    assert "own mirror" in r.detail


def test_a_circuit_that_is_not_quantum_films_known_answer_is_refused(tmp_path):
    m = ibm_model()
    other = other_qasm("not a known answer")
    m.files["bundle/known-answer.qasm"] = other
    m.edit_json(m.record("jobka"), lambda r: r["source"].__setitem__("circuit_sha256", sha(other)))
    refused(m, tmp_path)


def test_a_known_answers_circuit_the_crate_does_not_hold_is_refused(tmp_path):
    m = ibm_model()
    m.edit_json(m.record("jobka"), lambda r: r["source"].__setitem__("circuit_sha256", "0" * 64))
    r = refused(m, tmp_path)
    assert "no file of the crate has" in r.detail


@pytest.mark.parametrize("record", [b"", b"\xff", b"[]", b"{}", b'{"source": []}', b'{"source": {"circuit_sha256": 5}}',
                                    b'{"a": 1, "a": 2}', b"[" * 100000],
                         ids=["nothing", "not UTF-8", "a list", "empty", "source a list", "digest a number",
                              "a key twice", "deep"])
def test_a_hostile_known_answer_record_is_a_refusal_never_an_exception(tmp_path, record):
    m = ibm_model()
    m.files[m.record("jobka")] = record
    r = refused(m, tmp_path)
    if record in (b"{}", b'{"source": []}', b'{"source": {"circuit_sha256": 5}}'):
        assert "names no circuit_sha256" in r.detail       # refused for what it lacks, not by a later failure


def test_a_pub_that_has_no_record_cannot_name_its_circuit(tmp_path):
    m = ibm_model()
    del m.ents["#pub-jobka-0"]["qro:record"]
    refused(m, tmp_path)


# -- which Pub may be a Decode's known answer ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("named, why", [("#pub-joblaw-0", "role law"), ("#pub-jobcoh-0", "role coherence")])
def test_a_known_answer_of_another_role_is_refused(tmp_path, named, why):
    m = ibm_model()
    set_all(m, "qro:knownAnswer", {"@id": named})
    r = refused(m, tmp_path, where="qro:knownAnswer")
    assert "not known-answer" in r.detail


@pytest.mark.parametrize("named", ["#job-jobka", "#device-ibm_synth", "run/jobka-raw.json"])
def test_a_known_answer_that_is_no_pub_is_refused(tmp_path, named):
    m = ibm_model()
    m.ents["#decode-joblaw"]["qro:knownAnswer"] = {"@id": named}
    refused(m, tmp_path, where="#decode-joblaw")


def test_a_known_answer_on_another_device_is_refused(tmp_path):
    m = ibm_model()
    other = m.device("ibm_other")
    m.ents["#job-joblaw"]["qro:device"] = {"@id": other}
    r = refused(m, tmp_path, where="#decode-joblaw qro:knownAnswer")
    assert "another device" in r.detail


def test_a_known_answer_on_a_second_device_entity_of_the_same_name_is_refused(tmp_path):
    """The lead's reading of 2026-10-19 (D3): at step 8 a second entity of the device's name is the same device, since a
    snapshot's file names its backend. Step 5 compares a known answer's device entity by @id, which refuses more and never
    less, and the tests used a device of another name: a step that compared by name passed them."""
    m = ibm_model()
    m.entity("#device-ibm_synth-b", "IndividualProduct", name="ibm_synth", **{"qro:deviceKind": "qpu"})
    m.ents["#job-jobcoh"]["qro:device"] = {"@id": "#device-ibm_synth-b"}
    r = refused(m, tmp_path, where="#decode-jobcoh qro:knownAnswer")
    assert "ran on another device" in r.detail


def test_a_known_answer_that_is_no_pub_is_refused_even_where_the_reader_is_not_asked(tmp_path):
    """The reader refuses a role on what is no Pub (step 1), so a crate cannot reach this; a step handed metadata the reader
    has not seen does not take an entity for a Pub because it is listed by a job and states the role."""
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    entity(md["@graph"], "#pub-jobka-0")["@type"] = "CreativeWork"
    r = refusal(5, crate, md)
    assert r is not None and r.name == "known-answer" and "not a qro:Pub" in r.detail


def test_a_known_answer_submitted_in_another_bundle_is_refused(tmp_path):
    m = ibm_model()
    m.edit_json("run/joblaw-line.json", lambda r: r.__setitem__("bundle_sha256", "e" * 64))
    r = refused(m, tmp_path, where="#decode-joblaw qro:knownAnswer")
    assert "another bundle" in r.detail


def test_the_bundle_is_compared_only_where_both_jobs_have_a_line(tmp_path):
    m = ibm_model()
    m.edit_json("run/joblaw-line.json", lambda r: r.__setitem__("bundle_sha256", "e" * 64))
    del m.ents["#job-joblaw"]["qro:line"]
    assert verdict(m, tmp_path) is None
    m = ibm_model()
    m.edit_json("run/jobka-line.json", lambda r: r.__setitem__("bundle_sha256", "e" * 64))
    del m.ents["#job-jobka"]["qro:line"]
    assert verdict(m, tmp_path / "other") is None


@pytest.mark.parametrize("line", [b"", b"\xff", b"[]", b"{}", b'{"bundle_sha256": 5}', b"[" * 100000],
                         ids=["nothing", "not UTF-8", "a list", "no bundle", "a bundle a number", "deep"])
def test_a_hostile_job_line_where_the_bundle_is_compared_is_a_refusal(tmp_path, line):
    m = ibm_model()
    m.files["run/joblaw-line.json"] = line
    refused(m, tmp_path, where="#decode-joblaw")


def test_two_job_lines_that_both_name_no_bundle_are_not_one_bundle(tmp_path):
    """The verifier's note: a bundle compared where neither line has one is no bundle held, so a mutant that counts two
    absent as equal passed. The known-answer job's line and the decode's job line both lack it."""
    m = ibm_model()
    for job in ("jobka", "jobcoh"):
        m.edit_json(f"run/{job}-line.json", lambda r: r.pop("bundle_sha256"))
    r = refused(m, tmp_path, where="#decode-jobcoh qro:knownAnswer")
    assert "another bundle" in r.detail


def with_a_second_known_answer(good):
    """The crate of three jobs and a fourth: a second known-answer job, jobka2, in the same bundle and on the same device,
    whose own decode names its own Pub. Its data are the known answer's where `good`, and another outcome's where not."""
    m = ibm_model()
    old = "jobka"
    rows = known_answer_rows() if good else [outcome((1, 2))] * 40
    first, last = m.ents["#job-jobka"]["startTime"], m.ents["#job-jobka"]["endTime"]
    commitment = m.ents["#pub-jobka-0"]["qro:commitment"]
    m.file("run/jobka2-pub0-known-answer.json", m.files[m.record(old)])
    m.file("run/jobka2-line.json", m.files["run/jobka-line.json"])
    m.file("run/jobka2-raw.json", raw_ibm([rows], [commitment], (JOBS[old][2], JOBS[old][3])), ["File", "qro:RawResult"],
           **{"qro:rawForm": "ibm-sampler-result/v1", "qro:shots": 40})
    pub = dict(m.ents["#pub-jobka-0"], **{"@id": "#pub-jobka2-0", "qro:record": {"@id": "run/jobka2-pub0-known-answer.json"}})
    m.ents["#pub-jobka2-0"] = pub
    job = dict(m.ents["#job-jobka"], **{"@id": "#job-jobka2", "qro:jobId": "jobka2", "object": [{"@id": "#pub-jobka2-0"}],
                                        "qro:line": {"@id": "run/jobka2-line.json"}, "startTime": first, "endTime": last,
                                        "result": [{"@id": "run/jobka2-raw.json"}, {"@id": "run/jobka2-line.json"},
                                                   {"@id": "run/jobka2-pub0-known-answer.json"}]})
    m.ents["#job-jobka2"] = job
    m.ents["#decode-jobka2"] = dict(m.ents["#decode-jobka"], **{
        "@id": "#decode-jobka2", "object": [{"@id": "run/jobka2-raw.json"}],
        "result": [{"@id": "run/jobka2-pub0-known-answer.json"}], "qro:knownAnswer": {"@id": "#pub-jobka2-0"}})
    return m


def test_two_known_answers_in_one_crate_are_each_judged_on_their_own_data(tmp_path):
    """The verifier's k2_demo.py. A verdict kept for the first known answer must not serve the second: with a second
    known-answer job whose data do not hold, its decode is refused, and with data that hold, the crate is accepted."""
    assert verdict(with_a_second_known_answer(good=True), tmp_path / "good") is None
    r = refused(with_a_second_known_answer(good=False), tmp_path / "bad", where="#decode-jobka2 qro:bitOrder")
    assert "#pub-jobka2-0" in r.detail and "does not hold" in r.detail


def test_a_decode_may_name_its_own_pub_as_its_known_answer(tmp_path):
    m = ibm_model()
    assert m.ents["#decode-jobka"]["qro:knownAnswer"] == {"@id": "#pub-jobka-0"}
    assert verdict(m, tmp_path) is None


def test_a_known_answer_pub_with_no_job_or_no_decode_is_refused(tmp_path):
    m = ibm_model()
    m.ents["#job-jobka"].pop("object")
    refused(m, tmp_path, where="#decode-")
    m = ibm_model()
    m.ents["#decode-jobka"].pop("object")
    refused(m, tmp_path / "b", where="#decode-")


def test_a_known_answer_is_judged_once_however_many_decodes_name_it_and_no_result_is_kept_for_it(tmp_path, monkeypatch):
    """All three decodes of the crate name the one known answer: the verdict, (holds, text), is drawn from its raw result
    once and kept; the result is not. The decode of jobcoh comes first by id and judges the known answer, then lets its
    result go; jobka's own decode parses it again to account for it; jobka's two uses are the only two of one result."""
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    judged, parsed = [], []
    real_verdict, real_parse = p1_steps._verdict5, p1_steps.p1_forms.parse_raw

    def verdict(crate_dir, idx, k, *rest):
        judged.append(k["@id"])
        return real_verdict(crate_dir, idx, k, *rest)

    def parse_raw(form, data):
        parsed.append(form)
        return real_parse(form, data)
    monkeypatch.setattr(p1_steps, "_verdict5", verdict)
    monkeypatch.setattr(p1_steps.p1_forms, "parse_raw", parse_raw)
    assert refusal(5, crate, md) is None
    assert judged == ["#pub-jobka-0"] and len(parsed) == 4


def test_the_decode_of_the_known_answers_own_job_is_served_by_the_one_parse_that_judged_it(tmp_path, monkeypatch):
    """Where a decode reads the very result its known answer's verdict is drawn from, the result is parsed once."""
    m = ibm_model()
    for job in ("jobcoh", "joblaw"):                               # leave jobka's own decode the only one
        del m.ents["#decode-" + job]
    crate = m.write(tmp_path / "c")
    md = read_md(crate)
    parsed = []
    real_parse = p1_steps.p1_forms.parse_raw
    monkeypatch.setattr(p1_steps.p1_forms, "parse_raw", lambda form, data: parsed.append(form) or real_parse(form, data))
    assert refusal(5, crate, md) is None and len(parsed) == 1


def test_every_decode_is_visited(tmp_path):
    for i, job in enumerate(DECODES):
        m = ibm_model()
        m.ents["#decode-" + job]["qro:knownAnswer"] = {"@id": "#pub-joblaw-0"}
        if job == "joblaw":
            m.ents["#decode-joblaw"]["qro:knownAnswer"] = {"@id": "#pub-jobcoh-0"}
        refused(m, tmp_path / str(i), where=f"#decode-{job}")


def test_the_first_decode_by_id_is_the_one_named(tmp_path):
    m = ibm_model()
    for j in ("jobcoh", "joblaw"):
        m.ents["#decode-" + j]["qro:knownAnswer"] = {"@id": "#pub-joblaw-0"}
    refused(m, tmp_path, where="#decode-jobcoh")


# -- a raw result that is not in its form -----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("job", ["jobka", "joblaw", "jobcoh"])
def test_a_raw_result_that_is_not_in_its_form_is_refused_raw_form(tmp_path, job):
    m = ibm_model()
    m.files[f"run/{job}-raw.json"] = b"not a result"
    r = refused(m, tmp_path, "raw-form")
    assert "not in the raw form" in r.detail


def test_a_known_answer_is_read_at_its_own_pub_index_in_a_job_of_two(tmp_path):
    """The known answer is PUB 1 of a two-PUB job here: its rows are read at index 1, not at 0."""
    m = ibm_model()
    m.files[RAW] = raw_ibm([[outcome((1, 2))] * 40, known_answer_rows(40)], [None, None], None)
    m.ents["#job-jobka"]["object"] = [{"@id": "#pub-jobka-0"}, {"@id": "#pub-jobka-1"}]
    m.ents["#pub-jobka-1"] = dict(m.ents["#pub-jobka-0"], **{"@id": "#pub-jobka-1"})
    set_all(m, "qro:knownAnswer", {"@id": "#pub-jobka-1"})
    assert verdict(m, tmp_path / "at1") is None
    set_all(m, "qro:knownAnswer", {"@id": "#pub-jobka-0"})
    refused(m, tmp_path / "at0")


# -- Atlas ------------------------------------------------------------------------------------------------------------------------------
ATLAS = ("alaw", "avec")


def a_refused(m, tmp_path, name="known-answer", where=None):
    r = judge(m, tmp_path / "crate", 5)
    assert r is not None and r.name == name, r and f"{r.name}: {r.detail}"
    if where:
        assert where in r.where, r.where
    return r


def test_the_vector_read_under_another_order_does_not_hold(tmp_path):
    m = atlas_model()
    for j in ATLAS:
        m.ents["#decode-" + j]["qro:bitOrder"] = "circuit-order"
    r = a_refused(m, tmp_path, where="qro:bitOrder")
    assert "Z-basis positions are past |z| = 4" in r.detail


def test_a_vector_written_in_the_plain_order_holds_under_it_only(tmp_path):
    m = atlas_model()
    m.files["vector/vector.json"] = atlas_vector(order="circuit-order")
    m.files["law/result.json"] = atlas_result(LAYOUTS, order="circuit-order")
    for j in ATLAS:
        m.ents["#decode-" + j]["qro:bitOrder"] = "circuit-order"
    assert judge(m, tmp_path / "plain", 5) is None
    a_refused(atlas_model_with(atlas_vector(order="circuit-order")), tmp_path / "register")


def atlas_model_with(vector):
    m = atlas_model()
    m.files["vector/vector.json"] = vector
    return m


@pytest.mark.parametrize("order", ["msb-first", "lsb-first"])
def test_an_ibm_order_is_not_one_the_atlas_rule_admits(tmp_path, order):
    m = atlas_model()
    for j in ATLAS:
        m.ents["#decode-" + j]["qro:bitOrder"] = order
    r = a_refused(m, tmp_path, where="qro:bitOrder")
    assert "does not read the order" in r.detail


def test_a_known_answer_that_is_not_the_frozen_vector_is_refused(tmp_path):
    m = atlas_model()
    m.files["vector/vector.json"] = atlas_result(LAYOUTS)
    m.ents["vector/vector.json"].update({"qro:rawForm": ATLAS_FORM, "qro:shots": 32})
    r = a_refused(m, tmp_path)
    assert "the frozen vector" in r.detail


def test_a_vector_that_drifts_past_four_deviations_at_one_position_is_refused(tmp_path):
    """Qubit 15 should read 1 on 31 of every 32 shots; here it reads 1 on all of them (z squared 4096/31)."""
    m = atlas_model()
    doc = json.loads(m.files["vector/vector.json"])
    label = "IIIIIIZIIIIIIXII"
    counts = doc["measurements"][label]["counts"]
    off, on = atlas_string(label, set()), atlas_string(label, {15})
    counts[on] = counts.get(on, 0) + counts.pop(off)
    assert sum(counts.values()) == 4096
    m.files["vector/vector.json"] = json.dumps(doc).encode()
    r = a_refused(m, tmp_path, where="qro:bitOrder")
    assert "1 of 41 Z-basis positions are past" in r.detail


def test_a_law_results_raw_without_exactly_one_all_z_setting_is_not_accounted_for(tmp_path):
    m = atlas_model()
    m.files["law/result.json"] = atlas_result(LAYOUTS, label="IIIIIIIIIIIIIIXX", other="IIIIIIIIIIIIIIXY")
    a_refused(m, tmp_path, "raw-form", "law/result.json")


def test_a_known_answer_on_another_device_is_refused_for_atlas_too(tmp_path):
    m = atlas_model()
    m.ents["#job-alaw"]["qro:device"] = {"@id": m.device("atlas-other", "simulator")}
    r = a_refused(m, tmp_path, where="#decode-alaw")
    assert "another device" in r.detail


def test_the_atlas_decode_that_names_a_law_pub_as_its_known_answer_is_refused(tmp_path):
    m = atlas_model()
    m.ents["#decode-alaw"]["qro:knownAnswer"] = {"@id": "#pub-alaw-0"}
    a_refused(m, tmp_path, where="#decode-alaw")


def test_a_raw_result_that_is_not_in_the_atlas_form_is_raw_form(tmp_path):
    m = atlas_model()
    m.files["vector/vector.json"] = b"{}"
    a_refused(m, tmp_path, "raw-form")
    m = atlas_model()
    m.files["law/result.json"] = b"{}"
    a_refused(m, tmp_path / "law", "raw-form")


def test_an_atlas_rule_over_an_ibm_form_is_raw_form(tmp_path):
    m = atlas_model()
    m.ents["law/result.json"]["qro:rawForm"] = "ibm-sampler-result/v1"
    a_refused(m, tmp_path, "raw-form", "law/result.json")


# -- the step as a function the checker calls --------------------------------------------------------------------------------------------
def test_the_step_takes_a_path_or_a_string(tmp_path):
    crate = ibm_model().write(tmp_path / "c")
    p1_steps.step5(str(crate), read_md(crate))
    p1_steps.step5(crate, read_md(crate))


def test_a_graph_with_a_type_that_is_not_a_string_is_refused_by_the_step_that_is_handed_it(tmp_path):
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    entity(md["@graph"], "#job-jobka")["@type"] = ["CreateAction", {"@id": "qro:Job"}]
    r = refusal(5, crate, md)
    assert r.name == "known-answer" and r.where == "@graph" and "a type that is not a string" in r.detail


def test_a_graph_with_an_id_twice_is_refused_by_the_step_that_is_handed_it(tmp_path):
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    md["@graph"].append(dict(md["@graph"][-1]))
    r = refusal(5, crate, md)
    assert r.name == "known-answer" and "twice" in r.detail
    with pytest.raises(Refused):
        p1_steps.step5(crate, md)
