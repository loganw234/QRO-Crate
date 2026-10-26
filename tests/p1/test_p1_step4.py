"""Step 4: every `qro:Pub`'s commitment, recomputed from its record and held to its claim, to the job line, and to
IBM's own echo inside the raw bytes. Never to the manifest or to Quantum-Film's decoded record, which share a
producer with the recomputation. Each fault is planted in a small synthetic crate (p1_builder) and is refused
`commitment` at the entity it touches; the honest crate is accepted; and what step 4 cannot see is pinned as a
limit, accepted. A hostile file is a refusal by this step's name, never an exception."""
import json

import pytest
from p1_builder import (BUNDLE, IBM_FORM, KA, atlas_model, copy_job, entity, ibm_model, judge, ka_qasm, npy, outcome,
                        other_qasm, packed, read_md, refusal, sha)

from qro import p1_commit, p1_forms, p1_graph, p1_steps
from qro.refusal import Refused

JOBS = ("jobka", "joblaw", "jobcoh")
PUBS = ("#pub-jobka-0", "#pub-jobcoh-0", "#pub-jobcoh-1", "#pub-joblaw-0")
RAW = "run/jobka-raw.json"


def verdict(m, tmp_path, step=4):
    return judge(m, tmp_path / "crate", step)


def refused(m, tmp_path, where=None):
    r = verdict(m, tmp_path)
    assert r is not None, "accepted"
    assert r.name == "commitment", f"{r.name} at {r.where}: {r.detail}"
    if where is not None:
        assert where in r.where, f"{r.where}: {r.detail}"
    return r


def test_the_honest_crate_is_accepted(tmp_path):
    assert verdict(ibm_model(), tmp_path) is None


def test_the_crate_of_the_unit_tests_carries_what_the_design_says_it_does(tmp_path):
    md = read_md(ibm_model().write(tmp_path / "c"))
    kinds = {}
    for e in md["@graph"]:
        for t in (e["@type"] if isinstance(e["@type"], list) else [e["@type"]]):
            kinds[t] = kinds.get(t, 0) + 1
    assert (kinds["qro:Pub"], kinds["qro:Job"], kinds["qro:Decode"], kinds["qro:Snapshot"]) == (4, 3, 3, 4)


# -- the claim --------------------------------------------------------------------------------------------------------------
def test_a_claim_that_is_not_the_recomputed_commitment_is_refused(tmp_path):
    m = ibm_model()
    m.ents["#pub-jobka-0"]["qro:commitment"] = "0" * 64
    r = refused(m, tmp_path, "#pub-jobka-0 qro:commitment")
    assert "recomputes to" in r.detail


@pytest.mark.parametrize("claim", ["xyz", "A" * 64, "a" * 63, "", 7, [], {"@id": "x"}])
def test_a_claim_that_is_not_a_digest_or_none_is_refused_by_the_step_even_where_the_reader_is_not_asked(tmp_path, claim):
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    entity(md["@graph"], "#pub-jobka-0")["qro:commitment"] = claim
    r = refusal(4, crate, md)
    assert r is not None and r.name == "commitment" and "#pub-jobka-0" in r.where
    assert "64 lowercase hex digits, or `none`" in r.detail          # refused for its shape, before anything is read


def test_a_pub_that_states_no_commitment_is_refused(tmp_path):
    m = ibm_model()
    del m.ents["#pub-jobka-0"]["qro:commitment"]
    r = refused(m, tmp_path, "#pub-jobka-0 qro:commitment")
    assert "states its commitment" in r.detail


def test_every_pub_is_visited_and_the_first_by_id_is_the_one_named(tmp_path):
    for i, pub in enumerate(PUBS):
        m = ibm_model()
        m.ents[pub]["qro:commitment"] = "1" * 64
        refused(m, tmp_path / str(i), pub)
    m = ibm_model()
    for pub in ("#pub-jobka-0", "#pub-jobcoh-1"):
        m.ents[pub]["qro:commitment"] = "1" * 64
    refused(m, tmp_path / "two", "#pub-jobcoh-1")


def test_a_none_is_taken_at_its_word_on_a_pub_that_says_the_provider_held_none(tmp_path):
    """Atlas's Pubs, and the stated limit for an IBM Pub weakened to none: only step 9 refuses that one."""
    m = ibm_model()
    m.ents["#pub-jobka-0"]["qro:commitment"] = "none"
    assert verdict(m, tmp_path) is None
    assert verdict(atlas_model(), tmp_path / "atlas") is None


def mirrored_known_answer(m):
    """The known-answer Pub's record resealed to name a circuit that flips the mirror of the qubits, and every Decode told to read
    `lsb-first`: the order the data were not written in."""
    mirror = ka_qasm(tuple(sorted(15 - q for q in KA)))
    m.file("bundle/ka-mirror.qasm", mirror)
    m.edit_json(m.record("jobka"), lambda o: o["source"].update(circuit_sha256=sha(mirror)))
    for job in ("jobcoh", "jobka", "joblaw"):
        m.ents["#decode-" + job]["qro:bitOrder"] = "lsb-first"


def test_the_bit_order_rests_on_whatever_binds_the_known_answers_record_and_a_none_binds_nothing(tmp_path):
    """The stated limit 11, by the behaviour it concedes (round 2, D4). The order a known answer is judged by is read from the
    circuit its Pub's record names, and what binds that record is the Pub's commitment. A Pub at `none` binds nothing: with
    the known-answer Pub alone at `none`, the record resealed to a mirrored circuit and the Decodes made to read `lsb-first`,
    steps 4, 5 and 8 accept the crate (the verifier's faults1.py). Step 9, which refuses a body the generator did not write,
    is the cover. The same with the Pub committed is refused at step 4, by the commitment."""
    m = ibm_model()
    mirrored_known_answer(m)
    m.ents["#pub-jobka-0"]["qro:commitment"] = "none"
    for step in (4, 5, 8):
        assert judge(m, tmp_path / str(step), step) is None
    m = ibm_model()
    mirrored_known_answer(m)
    refused(m, tmp_path / "committed", "#pub-jobka-0 qro:commitment")


def test_a_job_copied_under_new_ids_is_accepted_since_a_job_is_held_to_its_own_files_and_a_decode_to_its_known_answers(tmp_path):
    """A stated limit (round 2; round 3 restates it): a Pub is held to its own record, line and raw result, a Job to its own
    files and to the crate's snapshots, and no Pub or Job is compared with another job. A Decode is: step 5 holds it to the job
    of its known answer, the device entity by @id, the bundle, the rule and the order. A law job copied byte for byte under new
    ids (raw result, line, record, Pub, Job, Decode) is a second job of the same commitments and the same shots that names the
    same known answer, so steps 4, 5 and 8 accept it. Step 9, which refuses a body the generator did not write, is the cover."""
    m = ibm_model()
    assert copy_job(m, "joblaw") == "joblaw2"
    assert {"#pub-joblaw2-0", "#job-joblaw2", "#decode-joblaw2", "run/joblaw2-raw.json"} <= set(m.ents)
    assert m.ents["#pub-joblaw2-0"]["qro:commitment"] == m.ents["#pub-joblaw-0"]["qro:commitment"]
    for step in (4, 5, 8):
        assert judge(m, tmp_path / str(step), step) is None


def test_an_atlas_pub_is_taken_at_its_word_and_none_of_its_bytes_is_read(tmp_path):
    m = atlas_model()
    for path in ("law/result.json", "vector/vector.json"):
        m.files[path] = b"not read by step 4"
    assert verdict(m, tmp_path) is None


# -- the fourteen inputs, each changed in the record and the record re-sealed -----------------------------------------------
def source(field, value):
    return lambda r: r["source"].__setitem__(field, value)


def top(field, value):
    return lambda r: r.__setitem__(field, value)


INPUTS = {
    "stock": top("stock", "pauli-5x5"), "role": top("role", "law"), "basis": top("basis", "X" * 16),
    "kind": source("kind", "simulator"), "route": source("route", "ibm-runtime"),
    "backend": source("backend", "ibm_other"), "program": source("program", "estimator"),
    "pub": source("pub", 1), "circuit_sha256": source("circuit_sha256", "0" * 64),
    "isa_sha256": source("isa_sha256", "0" * 64), "shots": source("shots", 41),
    "options_sha256": source("options_sha256", "0" * 64), "decode": source("decode", "quantum_film.ibm.decode/v2"),
    "salt": source("salt", "0" * 64),
}


@pytest.mark.parametrize("name", INPUTS)
def test_each_of_the_fourteen_inputs_binds_the_claim_the_line_and_the_echo_untouched(tmp_path, name):
    m = ibm_model()
    m.edit_json(m.record("jobka"), INPUTS[name])
    refused(m, tmp_path, "#pub-jobka-0")


@pytest.mark.parametrize("name", ["stock", "route", "salt"])
def test_an_input_with_no_counterpart_is_bound_by_the_claim_alone(tmp_path, name):
    """Nothing else in the crate states a stock, a route or a salt: they are held by the commitment itself."""
    m = ibm_model()
    m.edit_json(m.record("jobka"), INPUTS[name])
    r = refused(m, tmp_path, "#pub-jobka-0 qro:commitment")
    assert "recomputes to" in r.detail


@pytest.mark.parametrize("name, term", [("role", "qro:role"), ("basis", "qro:basis"), ("kind", "qro:deviceKind"),
                                        ("backend", "name"), ("program", "name"), ("decode", "qro:decodeRule"),
                                        ("pub", "id"), ("shots", "rows")])
def test_an_input_with_a_counterpart_is_refused_by_name_against_it(tmp_path, name, term):
    m = ibm_model()
    m.edit_json(m.record("jobka"), INPUTS[name])
    r = refused(m, tmp_path, "#pub-jobka-0 qro:record")
    assert term in r.detail


@pytest.mark.parametrize("name", ["circuit_sha256", "isa_sha256"])
def test_a_circuit_digest_the_commitment_binds_is_a_file_of_the_crate_found_by_digest(tmp_path, name):
    m = ibm_model()
    m.edit_json(m.record("jobka"), INPUTS[name])
    r = refused(m, tmp_path, "#pub-jobka-0 qro:record")
    assert f"no file of the crate has the {name}" in r.detail


@pytest.mark.parametrize("name, other", [("circuit_sha256", "bundle/law.qasm"), ("isa_sha256", "bundle/law.qpy")])
def test_the_digest_of_another_file_of_the_crate_is_found_and_then_the_commitment_does_not_recompute(tmp_path, name,
                                                                                                    other):
    m = ibm_model()
    m.edit_json(m.record("jobka"), source(name, sha(m.files[other])))
    r = refused(m, tmp_path, "#pub-jobka-0 qro:commitment")
    assert "recomputes to" in r.detail


@pytest.mark.parametrize("path, make", [("bundle/known-answer.qasm", lambda: other_qasm("swapped")),
                                        ("bundle/known-answer.qpy", lambda: b"QPY swapped for other bytes")])
def test_a_circuit_swapped_for_other_bytes_and_resealed_no_longer_has_the_digest_the_commitment_binds(tmp_path, path,
                                                                                                      make):
    m = ibm_model()
    m.files[path] = make()
    refused(m, tmp_path, "#pub-jobka-0 qro:record")


def test_options_changed_together_with_their_digest_still_do_not_recompute(tmp_path):
    m = ibm_model()
    bumped = {"dynamical_decoupling": {"enable": True}}

    def edit(r):
        r["source"]["options"], r["source"]["options_sha256"] = bumped, p1_commit.options_digest(bumped)
    m.edit_json(m.record("jobka"), edit)
    r = refused(m, tmp_path, "#pub-jobka-0 qro:commitment")
    assert "recomputes to" in r.detail


def test_options_that_do_not_digest_to_their_digest_are_refused_by_name(tmp_path):
    m = ibm_model()
    m.edit_json(m.record("jobka"), lambda r: r["source"].__setitem__("options", {"twirling": {"enable_gates": True}}))
    r = refused(m, tmp_path, "#pub-jobka-0 qro:record")
    assert "options_sha256" in r.detail


# -- the counterparts the crate states of its own ---------------------------------------------------------------------------------
@pytest.mark.parametrize("entity_id, term, value", [
    ("#pub-jobka-0", "qro:role", "law"), ("#pub-jobka-0", "qro:basis", "XXZZZZZZZZZZZZZZ"),
    ("#device-ibm_synth", "qro:deviceKind", "simulator"), ("#device-ibm_synth", "name", "ibm_other"),
    ("#program-sampler", "name", "estimator"), ("#decode-jobka", "qro:decodeRule", "quantum_film.atlas.decode/v1")])
def test_a_term_the_crate_states_that_differs_from_what_the_commitment_binds_is_refused(tmp_path, entity_id, term, value):
    m = ibm_model()
    m.ents[entity_id][term] = value
    refused(m, tmp_path)


def test_a_pub_whose_id_says_another_index_than_the_commitment_binds_is_refused(tmp_path):
    m = ibm_model()
    pub = m.ents.pop("#pub-jobka-0")
    pub["@id"] = "#pub-jobka-1"
    m.ents["#pub-jobka-1"] = pub
    m.ents["#job-jobka"]["object"] = [{"@id": "#pub-jobka-1"}]
    for j in ("jobka", "joblaw", "jobcoh"):
        m.ents["#decode-" + j]["qro:knownAnswer"] = {"@id": "#pub-jobka-1"}
    r = refused(m, tmp_path, "#pub-jobka-1")
    assert "index" in r.detail


# -- the job line ------------------------------------------------------------------------------------------------------------------
def test_a_job_line_that_holds_another_commitment_is_refused(tmp_path):
    m = ibm_model()
    m.edit_json("run/jobka-line.json", lambda r: r.__setitem__("commitments", ["f" * 64]))
    r = refused(m, tmp_path, "run/jobka-line.json commitments")
    assert "does not hold" in r.detail


def test_a_job_whose_line_is_another_jobs_is_refused(tmp_path):
    m = ibm_model()
    m.ents["#job-jobka"]["qro:line"] = {"@id": "run/joblaw-line.json"}
    refused(m, tmp_path, "joblaw-line.json")


def test_a_job_line_that_lists_more_or_fewer_commitments_than_the_job_has_pubs_is_refused(tmp_path):
    """The line is the job's record, written before any result: one commitment for each PUB, no more and no fewer."""
    m = ibm_model()
    m.edit_json("run/jobka-line.json", lambda r: r["commitments"].append("f" * 64))
    r = refused(m, tmp_path / "more", "run/jobka-line.json commitments")
    assert "lists 2 commitments; the job has 1 PUBs" in r.detail
    m = ibm_model()
    m.edit_json("run/jobcoh-line.json", lambda r: r["commitments"].pop())
    r = refused(m, tmp_path / "fewer", "run/jobcoh-line.json commitments")
    assert "lists 1 commitments; the job has 2 PUBs" in r.detail
    m = ibm_model()
    m.edit_json("run/jobka-line.json", lambda r: r.__setitem__("commitments", "x"))
    assert "lists no commitments" in refused(m, tmp_path / "none", "run/jobka-line.json").detail


def test_the_line_of_a_coherence_job_holds_each_pub_at_its_own_index(tmp_path):
    m = ibm_model()
    m.edit_json("run/jobcoh-line.json", lambda r: r["commitments"].reverse())
    refused(m, tmp_path, "run/jobcoh-line.json")


@pytest.mark.parametrize("line", [
    b"", b"\xff", b"[]", b"7", b"null", b"{}", b'{"commitments": "x"}', b'{"commitments": []}',
    b'{"commitments": [5]}', b'{"commitments": {"0": "x"}}', b'{"commitments": ["' + b"a" * 64 + b'", "' + b"b" * 64 + b'"]}',
    b'{"a": 1, "a": 2}', b'{"commitments": NaN}', b"[" * 100000 + b"]" * 100000],
    ids=["nothing", "not UTF-8", "a list", "a number", "null", "no commitments", "commitments a string",
         "commitments empty", "a commitment a number", "commitments an object", "other commitments", "a key twice",
         "a NaN", "deep"])
def test_a_hostile_job_line_is_a_refusal_never_an_exception(tmp_path, line):
    m = ibm_model()
    m.files["run/jobka-line.json"] = line
    refused(m, tmp_path)


def test_a_job_with_no_line_is_refused(tmp_path):
    m = ibm_model()
    del m.ents["#job-jobka"]["qro:line"]
    r = refused(m, tmp_path, "#pub-jobka-0")
    assert "qro:line" in r.detail


# -- IBM's echo, inside the raw bytes ------------------------------------------------------------------------------------------------
def edit_raw(m, job, fn):
    path = f"run/{job}-raw.json"
    doc = json.loads(m.files[path])
    fn(doc)
    m.files[path] = json.dumps(doc).encode()


def pubs_of(doc):
    return doc["__value__"]["pub_results"]


def test_a_raw_result_with_no_echo_is_a_refusal_not_a_pass(tmp_path):
    m = ibm_model()
    edit_raw(m, "jobka", lambda d: pubs_of(d)[0]["__value__"]["metadata"]["circuit_metadata"].clear())
    r = refused(m, tmp_path, "run/jobka-raw.json pub_results[0]")
    assert "no echo" in r.detail


def test_an_echo_is_kept_and_quoted_to_one_character_past_the_length_of_a_commitment(tmp_path):
    """A megabyte where IBM's commitment should be: the step does not keep it, and the refusal does not quote it (the line
    the command line prints would be as long). One character past a commitment's 64 is enough to tell it is none."""
    m = ibm_model()
    edit_raw(m, "jobka", lambda d: pubs_of(d)[0]["__value__"]["metadata"]["circuit_metadata"].update(
        {"qf_commitment": "e" * 1_000_000}))
    r = refused(m, tmp_path, "run/jobka-raw.json pub_results[0]")
    assert "IBM echoed " + "e" * 65 + ";" in r.detail and len(r.detail) < 300


@pytest.mark.parametrize("entries, shown", [([{"a": 1}], "does not hold"), (["e" * 1_000_000], "does not hold"),
                                            ([None], "does not hold"), ([], "lists 0 commitments"),
                                            (["a", "b"], "lists 2 commitments")], ids=["an object", "a megabyte", "null",
                                                                                      "none", "two"])
def test_a_job_lines_commitments_that_are_not_the_one_the_pub_has_are_refused_without_quoting_them(tmp_path, entries, shown):
    m = ibm_model()
    m.edit_json("run/jobka-line.json", lambda o: o.__setitem__("commitments", entries))
    r = refused(m, tmp_path, "run/jobka-line.json commitments")
    assert shown in r.detail and len(r.detail) < 300


@pytest.mark.parametrize("more", ["0", "0" * 1_000_000, " ", "\n"], ids=["one more", "a megabyte more", "a space", "a newline"])
def test_an_echo_that_is_the_commitment_and_more_is_refused(tmp_path, more):
    """The echo is kept to 65 characters: the commitment and one character more is not the commitment, and a cap of 64 would
    take it for one."""
    m = ibm_model()
    right = m.ents["#pub-jobka-0"]["qro:commitment"]
    edit_raw(m, "jobka", lambda d: pubs_of(d)[0]["__value__"]["metadata"]["circuit_metadata"].update(
        {"qf_commitment": right + more}))
    r = refused(m, tmp_path, "run/jobka-raw.json pub_results[0]")
    assert "IBM echoed" in r.detail and len(r.detail) < 300


def test_what_step_4_keeps_of_a_job_line_is_its_commitments_each_to_the_length_of_one(tmp_path):
    """The round-2 fix of the verifier's D3: of a job line step 4 keeps a tuple, an entry for each of `commitments`, and an
    entry only if it is a string that could be a commitment (64 characters at most). A megabyte in a line's list is not
    kept: the entry that is not a commitment is None. The step keeps this for each job until it has visited every Pub (a
    crate whose Pubs are visited index by index keeps every job's line a while, and a line of megabytes in its list would
    cost the sum of them), so what it keeps of each is held to what it compares."""
    keep = p1_steps._commits4
    assert keep({"commitments": ["a" * 64, "b" * 3, "z" * 1_000_000, "c" * 65, 7, None, {"a": 1}, [], True]})         == ("a" * 64, "b" * 3, None, None, None, None, None, None, None)
    assert keep({"commitments": []}) == ()
    assert keep({"commitments": ["a" * 64], "padding": "x" * 1_000_000}) == ("a" * 64,)
    for line in ({}, {"commitments": "x"}, {"commitments": {"0": "x"}}, {"commitments": None}, [], "x", 7, None):
        assert keep(line) is None, line


@pytest.mark.parametrize("echo", ["0" * 64, "e" * 64, "", "x"])
def test_an_echo_that_is_not_the_recomputed_commitment_is_refused(tmp_path, echo):
    m = ibm_model()
    edit_raw(m, "jobka", lambda d: pubs_of(d)[0]["__value__"]["metadata"]["circuit_metadata"].update(
        {"qf_commitment": echo}))
    r = refused(m, tmp_path, "run/jobka-raw.json pub_results[0]")
    assert "IBM echoed" in r.detail


def test_the_echo_is_the_one_inside_the_bytes_not_the_manifests_the_claims_or_the_lines(tmp_path):
    """The claim, the line and the record all agree and are right; only the echo differs: refused. The reverse: every
    copy the producer holds is changed together to another commitment and the echo kept, refused too."""
    m = ibm_model()
    edit_raw(m, "jobka", lambda d: pubs_of(d)[0]["__value__"]["metadata"]["circuit_metadata"].update(
        {"qf_commitment": "d" * 64}))
    refused(m, tmp_path / "a", "run/jobka-raw.json")
    m = ibm_model()
    m.ents["#pub-jobka-0"]["qro:commitment"] = "d" * 64
    m.edit_json("run/jobka-line.json", lambda r: r.__setitem__("commitments", ["d" * 64]))
    m.edit_json(m.record("jobka"), lambda r: r["source"].__setitem__("commitment", "d" * 64))
    refused(m, tmp_path / "b", "#pub-jobka-0 qro:commitment")


def test_the_echo_is_read_at_the_pubs_own_index(tmp_path):
    """Two PUBs' whole results swapped inside the coherence job's raw: each echo now stands at the other's index."""
    m = ibm_model()
    edit_raw(m, "jobcoh", lambda d: pubs_of(d).reverse())
    refused(m, tmp_path, "run/jobcoh-raw.json pub_results[0]")


def test_the_echoes_alone_swapped_between_two_pubs_are_refused(tmp_path):
    m = ibm_model()

    def swap(d):
        a, b = (pubs_of(d)[i]["__value__"]["metadata"]["circuit_metadata"] for i in (0, 1))
        a["qf_commitment"], b["qf_commitment"] = b["qf_commitment"], a["qf_commitment"]
    edit_raw(m, "jobcoh", swap)
    refused(m, tmp_path, "run/jobcoh-raw.json")


def test_the_data_of_two_pubs_swapped_under_their_echoes_is_not_a_commitment_matter(tmp_path):
    """The commitment binds the circuit and the shot count, not the data: the rows of PUB 0 and PUB 1 exchanged with
    their echoes left in place pass step 4 (and the decode's known answer is a different step's)."""
    m = ibm_model()

    def swap(d):
        a, b = (pubs_of(d)[i]["__value__"]["data"]["__value__"]["fields"]["meas"]["__value__"] for i in (0, 1))
        a["array"], b["array"] = b["array"], a["array"]
    edit_raw(m, "jobcoh", swap)
    assert verdict(m, tmp_path) is None


def test_a_job_reattributed_is_refused_because_the_echo_inside_the_raw_is_another_jobs(tmp_path):
    """The control job-reattributed: the known-answer job's raw result replaced by the law job's, which holds as
    many shots, so the count is paid and step 3 passes; the claim, line, record and digests all say the known-answer
    job. Only the echo inside the bytes is another's."""
    m = ibm_model()
    m.files[RAW] = m.files["run/joblaw-raw.json"]
    r = refused(m, tmp_path, "run/jobka-raw.json pub_results[0]")
    assert "IBM echoed" in r.detail


def test_a_raw_result_with_a_pub_more_than_the_job_lists_is_refused(tmp_path):
    m = ibm_model()
    edit_raw(m, "jobcoh", lambda d: pubs_of(d).append(json.loads(json.dumps(pubs_of(d)[0]))))
    r = refused(m, tmp_path, "#job-jobcoh object")
    assert "lists the PUBs [0, 1]; its raw result holds 3" in r.detail


def test_a_raw_result_with_a_pub_fewer_than_the_job_lists_is_refused(tmp_path):
    m = ibm_model()
    edit_raw(m, "jobcoh", lambda d: pubs_of(d).pop())
    refused(m, tmp_path, "#job-jobcoh object")


def test_a_job_that_lists_its_pubs_out_of_range_is_refused(tmp_path):
    m = ibm_model()
    pub = m.ents.pop("#pub-jobcoh-1")
    pub["@id"] = "#pub-jobcoh-2"
    m.ents["#pub-jobcoh-2"] = pub
    m.ents["#job-jobcoh"]["object"] = [{"@id": "#pub-jobcoh-0"}, {"@id": "#pub-jobcoh-2"}]
    refused(m, tmp_path, "#job-jobcoh object")


def test_a_job_whose_pubs_claim_one_index_twice_is_refused_for_the_listing(tmp_path):
    """As many PUBs listed as the raw holds, and both say index 0: PUB 1 of the raw would be bound by no Pub. The second Pub is a
    copy of the first, record and commitment too, so that nothing else is wrong with the crate."""
    m = ibm_model()
    m.ents.pop("#pub-jobcoh-1")
    m.ents["#pub-jobcoh-b-0"] = dict(m.ents["#pub-jobcoh-0"], **{"@id": "#pub-jobcoh-b-0"})
    m.ents["#job-jobcoh"]["object"] = [{"@id": "#pub-jobcoh-0"}, {"@id": "#pub-jobcoh-b-0"}]
    r = refused(m, tmp_path, "#job-jobcoh object")
    assert "the job lists the PUBs [0, 0]; its raw result holds 2" in r.detail


def test_the_shots_are_the_rows_the_raw_holds_for_the_pub_not_the_records(tmp_path):
    m = ibm_model()
    longer = [outcome(KA)] * 50
    edit_raw(m, "jobka", lambda d: pubs_of(d)[0]["__value__"]["data"]["__value__"]["fields"]["meas"]["__value__"][
        "array"].update({"__value__": packed(npy(longer))}))
    m.ents[RAW]["qro:shots"] = 50
    r = refused(m, tmp_path, "#pub-jobka-0 qro:record")
    assert "the record says 40 shots; the raw result holds 50 rows" in r.detail


def test_the_raw_result_of_another_form_carries_no_echo(tmp_path):
    m = ibm_model()
    m.ents[RAW]["qro:rawForm"] = "atlas-tomography-result/v1"
    r = refused(m, tmp_path, "run/jobka-raw.json qro:rawForm")
    assert IBM_FORM in r.detail


@pytest.mark.parametrize("data", [b"", b"\xff", b"{}", b"[]", b"7", b'{"__type__": "PrimitiveResult"}'],
                         ids=["nothing", "not UTF-8", "an object", "a list", "a number", "no value"])
def test_a_raw_result_that_is_no_result_is_a_refusal_here_whatever_step_3_would_say(tmp_path, data):
    m = ibm_model()
    m.files[RAW] = data
    r = refused(m, tmp_path, "#pub-jobka-0")
    assert "cannot be checked" in r.detail


# -- the record ----------------------------------------------------------------------------------------------------------------------
def test_a_pub_with_no_record_is_refused(tmp_path):
    m = ibm_model()
    del m.ents["#pub-jobka-0"]["qro:record"]
    refused(m, tmp_path, "#pub-jobka-0")


def test_a_record_that_is_not_a_file_the_crate_holds_is_refused(tmp_path):
    m = ibm_model()
    m.ents["#pub-jobka-0"]["qro:record"] = {"@id": "#device-ibm_synth"}
    r = refused(m, tmp_path, "#pub-jobka-0")
    assert "not a file the crate holds" in r.detail
    m = ibm_model()
    m.ents["#pub-jobka-0"]["qro:record"] = {"@id": "https://example.org/record.json"}
    refused(m, tmp_path / "b", "#pub-jobka-0")


@pytest.mark.parametrize("rid", ["../outside.json", "/outside.json", "run//jobka-pub0-known-answer.json",
                                 "C:/outside.json", "run/./jobka-pub0-known-answer.json"])
def test_a_record_whose_id_is_not_a_path_in_the_crate_is_not_read(tmp_path, rid):
    """The reader holds every File's @id to a path in the crate (step 1). A step handed metadata that was not read
    does not read a file on the strength of an @id that is not one: here a good record is where a sloppy join of the
    id would find it, inside the crate and beside it."""
    m = ibm_model()
    crate = m.write(tmp_path / "c")
    good = m.files[m.record("jobka")]
    (tmp_path / "outside.json").write_bytes(good)
    (crate / "outside.json").write_bytes(good)
    assert refusal(4, crate) is None
    md = read_md(crate)
    entity(md["@graph"], m.record("jobka"))["@id"] = rid
    entity(md["@graph"], "#pub-jobka-0")["qro:record"] = {"@id": rid}
    r = refusal(4, crate, md)
    assert r is not None and r.name == "commitment" and "#pub-jobka-0" in r.where
    assert "is not a file the crate holds" in r.detail


def test_an_entity_at_a_path_of_the_crate_that_is_no_file_is_not_read_for_one(tmp_path):
    """The record's @id is a clean path, and the file is there: the entity is not typed a File, so it is not one."""
    m = ibm_model()
    crate = m.write(tmp_path / "c")
    md = read_md(crate)
    entity(md["@graph"], m.record("jobka"))["@type"] = "CreativeWork"
    r = refusal(4, crate, md)
    assert r is not None and r.name == "commitment" and "not a file the crate holds" in r.detail


def test_the_circuit_a_commitment_binds_is_a_file_and_no_other_entity_that_states_its_digest(tmp_path):
    """Unread metadata (the reader refuses a sha256 on what is no File): the qasm entity is no File any more, and states
    the digest still. The crate holds no file of that digest, and the commitment binds one."""
    m = ibm_model()
    crate = m.write(tmp_path / "c")
    assert refusal(4, crate) is None
    md = read_md(crate)
    entity(md["@graph"], "bundle/known-answer.qasm")["@type"] = "CreativeWork"
    r = refusal(4, crate, md)
    assert r is not None and r.name == "commitment" and "no file of the crate has the circuit_sha256" in r.detail


def test_a_record_that_is_not_quantum_films_device_run_v1_is_refused(tmp_path):
    for i, (change, said) in enumerate(((lambda r: r.pop("format"), "is not quantum-film/device-run/v1"),
                                        (lambda r: r.__setitem__("format", "quantum-film/device-run/v2"),
                                         "is not quantum-film/device-run/v1"),
                                        (lambda r: r.pop("source"), "has no source"),
                                        (lambda r: r.__setitem__("source", [1]), "has no source"))):
        m = ibm_model()
        m.edit_json(m.record("jobka"), change)
        assert said in refused(m, tmp_path / str(i), "#pub-jobka-0").detail


@pytest.mark.parametrize("change", [
    lambda r: r.pop("stock"), lambda r: r.pop("role"), lambda r: r.pop("basis"), lambda r: r.__setitem__("stock", 7),
    lambda r: r["source"].__setitem__("shots", 40.0), lambda r: r["source"].__setitem__("shots", True),
    lambda r: r["source"].__setitem__("shots", "40"), lambda r: r["source"].__setitem__("pub", 0.0),
    lambda r: r["source"].__setitem__("pub", False), lambda r: r["source"].__setitem__("pub", "0"),
    lambda r: r["source"].pop("salt"), lambda r: r["source"].__setitem__("salt", None),
    lambda r: r["source"].pop("options"), lambda r: r["source"].pop("kind"),
    lambda r: r["source"].__setitem__("backend", ["ibm_synth"]), lambda r: r["source"].__setitem__("route", 1),
    lambda r: r["source"].__setitem__("decode", {}), lambda r: r["source"].pop("options_sha256")],
    ids=["no stock", "no role", "no basis", "stock a number", "shots a float", "shots a bool", "shots a string",
         "pub a float", "pub a bool", "pub a string", "no salt", "salt null", "no options", "no kind",
         "backend a list", "route a number", "decode an object", "no options_sha256"])
def test_a_record_whose_field_is_missing_or_of_another_type_is_refused(tmp_path, change):
    m = ibm_model()
    m.edit_json(m.record("jobka"), change)
    r = refused(m, tmp_path, "#pub-jobka-0")
    assert "the record" in r.detail, r.detail           # refused for the record's shape, not by a later check


@pytest.mark.parametrize("field, value, said", [
    ("shots", 40.0, "a whole number"), ("shots", True, "a whole number"), ("shots", "40", "a whole number"),
    ("pub", 0.0, "a whole number"), ("pub", False, "a whole number"), ("pub", "0", "a whole number"),
    ("route", 1, "a string"), ("backend", ["ibm_synth"], "a string"), ("salt", None, "a string"),
    ("decode", {}, "a string")])
def test_a_field_of_another_type_is_refused_naming_the_field_and_the_type_it_should_be(tmp_path, field, value, said):
    m = ibm_model()
    m.edit_json(m.record("jobka"), lambda r: r["source"].__setitem__(field, value))
    r = refused(m, tmp_path, "#pub-jobka-0")
    assert f"the record's {field} is not {said}" in r.detail, r.detail


@pytest.mark.parametrize("record", [
    b"", b"\xff", b"[]", b"7", b"null", b"{}", b'{"a": 1, "a": 2}', b'{"format": NaN}', b"[" * 100000 + b"]" * 100000,
    b'{"format": "quantum-film/device-run/v1", "source": {"shots": 1e999}}', b"\xef\xbb\xbf{}",
    b'{"format": "quantum-film/device-run/v1", "source": {"options": ' + b"9" * 6000 + b"}}"],
    ids=["nothing", "not UTF-8", "a list", "a number", "null", "empty", "a key twice", "NaN", "deep",
         "a number past binary64", "a byte-order mark", "an integer of 6,000 digits"])
def test_a_hostile_record_is_a_refusal_never_an_exception(tmp_path, record):
    m = ibm_model()
    m.files[m.record("jobka")] = record
    refused(m, tmp_path, "#pub-jobka-0")


# -- the graph ------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name, fn", [
    ("a pub in no job", lambda m: m.ents["#job-jobka"].pop("object")),
    ("a job with no device", lambda m: m.ents["#job-jobka"].pop("qro:device")),
    ("a job with no program", lambda m: m.ents["#job-jobka"].pop("instrument")),
    ("a job with no raw result", lambda m: m.ents["#job-jobka"].update({"result": [{"@id": "run/jobka-line.json"}]})),
    ("a raw result no decode reads", lambda m: m.ents["#decode-jobka"].pop("object")),
    ("a raw result two decodes read", lambda m: m.ents.__setitem__("#decode-extra", {
        "@id": "#decode-extra", "@type": ["CreateAction", "qro:Decode"], "object": [{"@id": RAW}]})),
    ("a pub two jobs list", lambda m: m.ents.__setitem__("#job-extra", {
        "@id": "#job-extra", "@type": ["CreateAction", "qro:Job"], "object": [{"@id": "#pub-jobka-0"}]})),
    ("a job with two raw results", lambda m: m.ents["#job-jobka"].update({"result": [
        {"@id": RAW}, {"@id": "run/joblaw-raw.json"}, {"@id": "run/jobka-line.json"}]})),
    ("a job whose device is a file", lambda m: m.ents["#job-jobka"].update({"qro:device": {"@id": RAW}})),
], ids=lambda x: x if isinstance(x, str) else "")
def test_a_relation_the_step_needs_that_the_graph_lacks_or_holds_twice_is_a_refusal(tmp_path, name, fn):
    m = ibm_model()
    fn(m)
    refused(m, tmp_path, "#pub-jobka-0")


# -- the stated limits ------------------------------------------------------------------------------------------------------------------
def test_a_producer_who_holds_every_byte_can_change_a_qpy_and_the_crate_only_checker_accepts_it(tmp_path):
    """The stated limit of the control qpy-only, here on the small crate: one byte of the known-answer QPY changed,
    its digest, the commitment (in the claim, the line and the record), IBM's echo inside the raw, and every digest
    recomputed. Nothing in the crate disagrees: only the QPY stage, or the owner's re-fetch of IBM's copy, can."""
    m = ibm_model()
    forged = bytearray(m.files["bundle/known-answer.qpy"])
    forged[3] ^= 1
    m.files["bundle/known-answer.qpy"] = bytes(forged)
    rec_path = m.record("jobka")
    rec = m.json(rec_path)
    rec["source"]["isa_sha256"] = sha(bytes(forged))
    fields = {"stock": rec["stock"], "role": rec["role"], "basis": rec["basis"], **{
        n: rec["source"][n] for n in ("kind", "route", "backend", "program", "pub", "circuit_sha256", "isa_sha256",
                                      "shots", "options_sha256", "decode", "salt")}}
    c = p1_commit.commitment_of(fields)
    rec["source"]["commitment"] = c
    m.put_json(rec_path, rec)
    m.ents["#pub-jobka-0"]["qro:commitment"] = c
    m.edit_json("run/jobka-line.json", lambda r: r.__setitem__("commitments", [c]))
    edit_raw(m, "jobka", lambda d: pubs_of(d)[0]["__value__"]["metadata"]["circuit_metadata"].update(
        {"qf_commitment": c}))
    for step in (4, 5, 8):
        assert verdict(m, tmp_path / str(step), step) is None


def rows_of(m, job):
    body = p1_forms.parse_ibm_result(m.files[f"run/{job}-raw.json"]).pubs[0].body
    return [int.from_bytes(body[i:i + 2], "big") for i in range(0, len(body), 2)]


def test_a_shot_moved_and_every_digest_recomputed_is_accepted_by_the_crate_only_checker(tmp_path):
    """The stated limit of the control shot-moved-resealed, on the law job: no step re-derives a measure."""
    m = ibm_model()
    rows = rows_of(m, "joblaw")
    rows[0] = outcome((1, 2, 3, 4, 5))

    def move(d):
        pubs_of(d)[0]["__value__"]["data"]["__value__"]["fields"]["meas"]["__value__"]["array"][
            "__value__"] = packed(npy(rows))
    edit_raw(m, "joblaw", move)
    assert verdict(m, tmp_path) is None


def test_what_step_4_reads_of_the_manifest_is_nothing(tmp_path):
    """The bundle's digest sits in the line and is never opened: a line with another bundle_sha256 is step 5's
    matter (a known answer from another bundle), not step 4's."""
    m = ibm_model()
    m.edit_json("run/joblaw-line.json", lambda r: r.__setitem__("bundle_sha256", BUNDLE[::-1]))
    assert verdict(m, tmp_path) is None


@pytest.mark.parametrize("content", [b"\xff\xfe not even text", b"", b"{"], ids=["not UTF-8", "empty", "unfinished"])
def test_the_manifest_and_the_verdict_file_are_never_opened(tmp_path, content):
    m = ibm_model()
    m.file("bundle/manifest.json", content)
    m.file("run/jobka-verdict.json", content)
    assert verdict(m, tmp_path) is None


def test_nothing_in_a_record_but_its_fourteen_inputs_is_read(tmp_path):
    m = ibm_model()
    m.edit_json(m.record("jobka"), lambda r: r.update({"counts": [[[0], 1]], "digest": "0" * 64, "law": {"x": 1}}))
    assert verdict(m, tmp_path) is None


# -- the step as a function the checker calls ---------------------------------------------------------------------------------------------
def test_each_raw_result_and_each_job_line_is_read_once_however_many_pubs_it_holds(tmp_path, monkeypatch):
    """The coherence job's two PUBs share one raw result and one line: a crate of 65 jobs is read once a job, not once
    a PUB (an 800,000-shot result is not inflated again for each PUB that is in it)."""
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    parsed, lines = [], []
    real_parse, real_json = p1_forms.parse_raw, p1_steps._json

    def parse_raw(form, data):
        parsed.append(form)
        return real_parse(form, data)

    def json_of(c, e, what):
        if what == "the job line":
            lines.append(e["@id"])
        return real_json(c, e, what)
    monkeypatch.setattr(p1_forms, "parse_raw", parse_raw)
    monkeypatch.setattr(p1_steps, "_json", json_of)
    assert refusal(4, crate, md) is None
    assert parsed == [IBM_FORM] * 3 and sorted(lines) == ["run/jobcoh-line.json", "run/jobka-line.json",
                                                          "run/joblaw-line.json"]


def test_a_jobs_pubs_are_listed_once_however_many_pubs_it_has(tmp_path, monkeypatch):
    """So the cost of the step does not grow as the square of a job's PUBs (a hostile job may list a great many)."""
    calls = []
    real = p1_graph.Index.pubs_of

    def counting(self, job):
        calls.append(job["@id"])
        return real(self, job)
    monkeypatch.setattr(p1_graph.Index, "pubs_of", counting)
    crate = ibm_model().write(tmp_path / "c")
    assert refusal(4, crate) is None
    assert sorted(calls) == ["#job-jobcoh", "#job-jobka", "#job-joblaw"]          # jobcoh has two PUBs, listed once


def test_the_step_takes_a_path_or_a_string_and_a_metadata_it_has_not_seen(tmp_path):
    crate = ibm_model().write(tmp_path / "c")
    p1_steps.step4(str(crate), read_md(crate))
    p1_steps.step4(crate, read_md(crate))
    with pytest.raises(Refused):
        p1_steps.step4(crate, {"@graph": [{"@id": "#p", "@type": "qro:Pub", "qro:commitment": "1" * 64}]})


def test_a_graph_with_a_type_that_is_not_a_string_is_refused_by_the_step_that_is_handed_it(tmp_path):
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    entity(md["@graph"], "#job-jobka")["@type"] = ["CreateAction", {"@id": "qro:Job"}]
    r = refusal(4, crate, md)
    assert r.name == "commitment" and r.where == "@graph" and "a type that is not a string" in r.detail


def test_a_graph_with_an_id_twice_is_refused_by_the_step_that_is_handed_it(tmp_path):
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    md["@graph"].append(dict(md["@graph"][-1]))
    r = refusal(4, crate, md)
    assert r.name == "commitment" and "twice" in r.detail
