"""P1.2's readers of Quantum-Film's records and of the read of 2026-10-14 (qro/p1_records.py), on the real files of the
twin and on the faults a record can have. A record that is not in its format is a refusal of the build (a RecordError),
never a crash; and what a reader returns is what the file says, checked against another file of the same job wherever
two files say one thing."""
import copy
import hashlib
import json

import pytest

from p1_support import IBM_DIR, MANIFEST, ROOT, TWIN
from qro import p1_commit
from qro import p1_records as rec

RUN = TWIN.joinpath("docs", "records", "2026-10-05", "ibm", "ibm_kingston", "run")
READ = ROOT / "records" / "2026-10-14"


def twin_file(rel):
    """The bytes of a file of Quantum-Film's, by its path in the crate."""
    return TWIN.joinpath("docs", "records", *rel.split("/")).read_bytes()


def run_file(name):
    return (RUN / name).read_bytes()


def line_of(job):
    return rec.line(run_file(f"{job}-line.json"), job)


# -- the manifest ---------------------------------------------------------------------------------------------------------
SURROGATE = chr(0xD800)                                         # a lone surrogate: JSON writes it as an escape, UTF-8 cannot


@pytest.mark.parametrize("doc, place", [
    ({"format": "x", "salt": SURROGATE}, "salt"),
    ({"body": {"params": {"circuit_qasm": SURROGATE}}}, "body.params.circuit_qasm"),
    ({"jobs": [{"circuits": [{"salt": "ok"}, {"salt": "a" + SURROGATE}]}]}, "jobs[0].circuits[1].salt"),
    ({"a": {SURROGATE: 1}}, "a key of a"),
    ({SURROGATE: 1}, "a key of the document"),
], ids=["a field", "a nested field", "a field in a list", "a key", "a key at the top"])
def test_a_record_holding_a_string_utf8_cannot_encode_is_refused_naming_its_field(doc, place):
    """P1.2's fourth verifier, D1: a string with a lone surrogate, written as an escape, passes the strict JSON reader and
    would crash a generator that encodes it (UnicodeEncodeError, which no guard catches). The records' reader refuses it,
    naming the record and the field, so that the build is refused, exit 1, never failing, exit 3."""
    data = json.dumps(doc).encode("ascii")                              # the surrogate as the escape \ud800
    assert b"\\ud800" in data
    with pytest.raises(rec.RecordError) as x:
        rec.parse(data, "the-record.json")
    assert str(x.value) == f"the-record.json: {place} holds a string UTF-8 cannot encode (a lone surrogate)"


def test_a_record_of_every_other_string_is_read_as_it_was():
    doc = {"a": "é中\U0001f600", "b": ["x", {"c": "\\ud800"}]}                # characters UTF-8 encodes, and a backslash
    assert rec.parse(json.dumps(doc).encode("ascii"), "r.json") == doc


def nested(shape, n, leaf):
    """{"a": ...} with `leaf` n levels below the top object: in n one-element arrays, or in n objects of one member "a"."""
    if shape == "arrays":
        return b'{"a":' + b"[" * n + leaf + b"]" * n + b"}"
    return b'{"a":' + b'{"a":' * n + leaf + b"}" * n + b"}"


def asked(data):
    """The reader's verdict on `data`: None for a record read, or its refusal's words. Every parse below is made from
    here, at one depth of the stack, so that the limit found is the reader's own where it is asked."""
    try:
        rec.parse(data, "the-record.json")
        return None
    except rec.RecordError as x:
        return str(x)


def reader_limit(shape):
    """The deepest nesting the strict reader admits here: the host's own (about 3,000 levels on this one), found by asking
    the reader, doubling and then halving, never written down."""
    lo, hi = 1, 2
    while asked(nested(shape, hi, b'"s"')) is None:
        lo, hi = hi, 2 * hi
        assert hi < 2 ** 24
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if asked(nested(shape, mid, b'"s"')) is None else (lo, mid)
    assert asked(nested(shape, hi, b'"s"')) == "the-record.json: nested deeper than the reader reads"
    return lo


@pytest.mark.parametrize("shape", ["arrays", "objects"])
def test_a_string_utf8_cannot_encode_is_refused_at_any_depth_the_reader_admits_its_field_named_in_full(shape):
    """P1.2's fifth verifier, D1: round 4's walk recursed, and a lone surrogate 1,000 levels down raised RecursionError,
    the adapter failing, where the reader admits about 3,000. The walk keeps its own stack: at depth 1, 1,000 and the
    reader's own limit, the record is refused naming the field in full; one level deeper, the reader refuses it."""
    limit = reader_limit(shape)
    step = "[0]" if shape == "arrays" else ".a"
    assert limit >= 1000
    for n in (1, 1000, limit):
        assert asked(nested(shape, n, b'"\\ud800"')) == (
            f"the-record.json: a{step * n} holds a string UTF-8 cannot encode (a lone surrogate)"), n
    assert asked(nested(shape, limit + 1, b'"\\ud800"')) == "the-record.json: nested deeper than the reader reads"


def test_a_key_utf8_cannot_encode_deep_down_is_named_as_far_as_it_can_be():
    """A key with a lone surrogate cannot be written in the place: the object holding it is named instead."""
    data = nested("arrays", 1000, b'{"ok":1,"\\ud800":2}')
    assert asked(data) == f"the-record.json: a key of a{'[0]' * 1000} holds a string UTF-8 cannot encode (a lone surrogate)"


def test_the_first_string_utf8_cannot_encode_is_named_in_the_order_the_record_writes_them():
    """Keys before their values, and an earlier member's value, however deep, before a later member's key."""
    doc = {"a": [[{"b": "x" + SURROGATE}]], SURROGATE: 1, "c": {SURROGATE: "y"}}
    data = json.dumps(doc).encode("ascii")
    assert asked(data) == "the-record.json: a[0][0].b holds a string UTF-8 cannot encode (a lone surrogate)"
    doc = {"a": {"b": 1, SURROGATE + "k": [SURROGATE]}}
    assert asked(json.dumps(doc).encode("ascii")) == ("the-record.json: a key of a holds a string UTF-8 cannot encode "
                                                       "(a lone surrogate)")


def test_the_morning_manifest_is_read_whole():
    m = rec.manifest(twin_file(MANIFEST), "manifest")
    assert (m.backend, m.stock, m.kind, m.route, m.program) == ("ibm_kingston", "pauli-4x4", "qpu", "ibm-direct", "sampler")
    assert m.decode == "quantum_film.ibm.decode/v1"
    assert (m.qiskit, m.level, m.seed) == ("2.5.2", 2, 11)
    assert [name for name, _ in m.jobs] == ["known-answer", "law", "coherence"]
    assert [c.name for c in m.circuits()] == ["known-answer", "law", "coherence-xx", "coherence-yy"]
    assert [(c.pub, c.role, c.shots) for c in dict(m.jobs)["coherence"]] == [(0, "coherence", 4096), (1, "coherence", 4096)]
    assert m.source_path.startswith("docs/") and m.source_path.endswith("circuit-ed767c01bd4b851d.qasm")
    assert m.options == {"dynamical_decoupling": {"enable": False}, "twirling": {"enable_gates": False,
                                                                                "enable_measure": False}}
    for c in m.circuits():
        for digest in (c.circuit_sha256, c.gates_sha256, c.isa_sha256, c.qasm3_sha256, c.commitment, c.salt):
            assert len(digest) == 64 and digest == digest.lower()


def test_a_manifest_of_another_format_is_refused():
    doc = json.loads(twin_file(MANIFEST))
    doc["format"] = "quantum-film/hardware-bundle/v2"
    with pytest.raises(rec.RecordError, match="format is 'quantum-film/hardware-bundle/v2'"):
        rec.manifest(json.dumps(doc).encode(), "manifest")


def test_the_pub_indexes_of_a_job_are_zero_to_n_in_order_and_a_job_is_named_once():
    doc = json.loads(twin_file(MANIFEST))
    swapped = copy.deepcopy(doc)
    coherence = next(j for j in swapped["jobs"] if j["job"] == "coherence")
    coherence["circuits"].reverse()
    with pytest.raises(rec.RecordError, match="PUB indexes"):
        rec.manifest(json.dumps(swapped).encode(), "manifest")
    twice = copy.deepcopy(doc)
    twice["jobs"].append(copy.deepcopy(twice["jobs"][0]))
    with pytest.raises(rec.RecordError, match="job names"):
        rec.manifest(json.dumps(twice).encode(), "manifest")
    nothing = copy.deepcopy(doc)
    nothing["jobs"] = []
    with pytest.raises(rec.RecordError, match="job names"):
        rec.manifest(json.dumps(nothing).encode(), "manifest")


# -- a job's line, record and metrics --------------------------------------------------------------------------------------
def test_a_line_lists_a_commitment_a_pub_and_names_its_job():
    ka, coh = line_of("known-answer"), line_of("coherence")
    assert len(ka.commitments) == 1 and len(coh.commitments) == 2
    assert ka.job_id != coh.job_id and ka.bundle_sha256 == coh.bundle_sha256
    assert (ka.stock, ka.kind, ka.route, ka.backend, ka.program) == ("pauli-4x4", "qpu", "ibm-direct", "ibm_kingston",
                                                                      "sampler")
    assert ka.bundle_sha256 == hashlib.sha256(twin_file(MANIFEST)).hexdigest()


@pytest.mark.parametrize("commitments", [[], "e0b0", [1], [None], [["a"]]])
def test_a_line_whose_commitments_are_not_a_list_of_strings_is_refused(commitments):
    doc = json.loads(run_file("known-answer-line.json"))
    doc["commitments"] = commitments
    with pytest.raises(rec.RecordError):
        rec.line(json.dumps(doc).encode(), "line")


def test_a_device_run_record_is_read_with_its_counts_and_its_digest_is_its_bodys():
    for job, pubs in (("known-answer", [0]), ("coherence", [0, 1])):
        for k in pubs:
            path = next(p for p in RUN.glob(f"{job}-pub{k}-*.json"))
            run = rec.device_run(path.read_bytes(), path.name)
            assert run.digest == rec.record_digest(run.doc)
            assert sum(run.counts.values()) == run.source["shots"]
            assert all(list(q) == sorted(set(q)) for q in run.counts)
            fields = run.fields(path.name)
            assert len(fields) == 14 and fields["pub"] == k and fields["role"] == run.role
            assert type(fields["shots"]) is int and type(fields["salt"]) is str


def test_a_records_digest_ignores_its_own_digest_and_every_other_field_moves_it():
    path = next(RUN.glob("known-answer-pub0-*.json"))
    doc = json.loads(path.read_bytes())
    base = rec.record_digest(doc)
    assert base == doc["digest"]
    assert rec.record_digest({**doc, "digest": "0" * 64}) == base
    for key in doc:
        if key != "digest":
            changed = {**doc, key: "x" if not isinstance(doc[key], str) else doc[key] + "x"}
            assert rec.record_digest(changed) != base, key
    deeper = copy.deepcopy(doc)
    deeper["source"]["shots"] += 1
    assert rec.record_digest(deeper) != base
    # the body's keys sorted at every depth, no spaces, and anything not ASCII escaped, whatever order the dict holds them in
    assert rec.record_digest({"b": [1, 2], "a": {"d": 1, "c": 2}}) == hashlib.sha256(b'{"a":{"c":2,"d":1},"b":[1,2]}').hexdigest()
    assert rec.record_digest({"k": "é"}) == hashlib.sha256(b'{"k":"\\u00e9"}').hexdigest()


@pytest.mark.parametrize("counts, why", [
    ([[[0, 1], 3], [[0, 1], 2]], "repeats an outcome"),
    ([[[1, 0], 3]], "not sorted"),
    ([[[1, 1], 3]], "not sorted and distinct"),
    ([[[0], True]], "not \\[\\[qubits"),
    ([[[0], 1.5]], "not \\[\\[qubits"),
    ([[0, 1]], "not \\[\\[qubits"),
    ([[[0], 1, 2]], "not \\[\\[qubits"),
    ([[["a"], 1]], "not \\[\\[qubits"),
])
def test_counts_that_are_not_an_outcome_and_its_shots_are_refused(counts, why):
    path = next(RUN.glob("known-answer-pub0-*.json"))
    doc = json.loads(path.read_bytes())
    doc["counts"] = counts
    with pytest.raises(rec.RecordError, match=why):
        rec.device_run(json.dumps(doc).encode(), "record")


def test_a_record_whose_field_is_of_the_wrong_type_is_refused_naming_it():
    path = next(RUN.glob("known-answer-pub0-*.json"))
    doc = json.loads(path.read_bytes())
    run = rec.device_run(path.read_bytes(), "record")
    for name in ("shots", "pub"):
        bad = copy.deepcopy(doc)
        bad["source"][name] = float(bad["source"][name])
        with pytest.raises(rec.RecordError, match=f"{name} is not a whole number"):
            rec.device_run(json.dumps(bad).encode(), "record").fields("record")
        bad["source"][name] = True
        with pytest.raises(rec.RecordError, match=f"{name} is not a whole number"):
            rec.device_run(json.dumps(bad).encode(), "record").fields("record")
    bad = copy.deepcopy(doc)
    del bad["source"]["salt"]
    with pytest.raises(rec.RecordError, match="salt is not a string"):
        rec.device_run(json.dumps(bad).encode(), "record").fields("record")
    assert run.fields("record")["salt"] == doc["source"]["salt"]


def test_the_metrics_wrapper_gives_the_three_times_and_names_its_job():
    ka, m = line_of("known-answer"), rec.metrics(run_file("known-answer-metrics.json"), "metrics")
    assert (m.job_id, m.backend) == (ka.job_id, ka.backend)
    assert m.created == rec.instant(ka.submitted_at, "line")
    assert m.created <= m.running <= m.finished


def test_the_metrics_created_time_is_the_timestamps_and_a_time_is_a_real_one():
    doc = json.loads(run_file("known-answer-metrics.json"))
    skewed = copy.deepcopy(doc)
    skewed["metrics"]["timestamps"]["created"] = "2026-10-05T10:26:56.364970Z"
    with pytest.raises(rec.RecordError, match="created time is not the timestamps"):
        rec.metrics(json.dumps(skewed).encode(), "metrics")
    bad = copy.deepcopy(doc)
    bad["metrics"]["timestamps"]["running"] = "2026-13-05T10:26:58Z"
    with pytest.raises(rec.RecordError, match="not a real time"):
        rec.metrics(json.dumps(bad).encode(), "metrics")


@pytest.mark.parametrize("text, ok", [("2026-10-05T10:26:56.364971Z", True), ("2026-10-05T10:26:56Z", True),
                                      ("2026-10-05T10:26:56.3649710Z", False), ("2026-10-05T10:26:56", False),
                                      ("2026-10-05 10:26:56Z", False), ("", False), (5, False)])
def test_a_record_time_is_a_utc_time_of_up_to_six_fraction_digits(text, ok):
    if ok:
        assert rec.instant(text, "x").year == 2026
    else:
        with pytest.raises(rec.RecordError):
            rec.instant(text, "x")


# -- the read of 2026-10-14 ---------------------------------------------------------------------------------------------------
def read_records(job):
    jid = line_of(job).job_id
    return (READ / "ibm-refetch" / "ibm_kingston" / f"{jid}.json", READ / "ibm-results-refetch" / "ibm_kingston" / f"{jid}.json")


def test_the_reads_job_record_gives_its_flags_pubs_times_and_the_snapshots_the_history_returned():
    mine, _ = read_records("coherence")
    r = rec.refetch_job(mine.read_bytes(), "job record")
    assert (r.device, r.role, r.pubs_in_ibm_copy, r.pubs_in_line) == ("ibm_kingston", "coherence", 2, 2)
    assert len(r.pubs) == 2 and all(p["gate_list_equal"] is True and p["gates_equal"] is True for p in r.pubs)
    assert r.holds["commitments_equal"] is True
    assert r.at_first_shot.startswith("ibm_kingston/properties-") and r.at_running.endswith("Z.json")
    assert r.first_shot >= r.running
    assert (READ / "ibm-refetch" / r.at_first_shot).is_file() and (READ / "ibm-refetch" / r.at_running).is_file()


def test_the_reads_result_record_holds_the_raw_results_digest_and_size_twice():
    _, mine = read_records("known-answer")
    r = rec.refetch_result(mine.read_bytes(), "result record")
    raw = run_file("known-answer-raw.json")
    assert r.bytes_equal is True and r.agree_at == "bytes"
    assert r.committed_sha256 == r.ibm_sha256 == hashlib.sha256(raw).hexdigest()
    assert r.committed_bytes == r.ibm_bytes == len(raw)
    assert r.committed_path.endswith(f"{IBM_DIR}/run/known-answer-raw.json")


@pytest.mark.parametrize("edit, why", [
    (lambda d: d.update(bytes_equal=1), "bytes_equal is not true or false"),
    (lambda d: d.update(bytes_equal="true"), "bytes_equal is not true or false"),
    (lambda d: d["committed"].update(bytes=True), "committed.bytes is not a whole number"),
    (lambda d: d["ibm_copy"].update(bytes=1.0), "ibm_copy.bytes is not a whole number"),
])
def test_a_boolean_is_not_a_whole_number_and_a_whole_number_is_not_a_boolean(edit, why):
    _, mine = read_records("known-answer")
    doc = json.loads(mine.read_bytes())
    edit(doc)
    with pytest.raises(rec.RecordError, match=why):
        rec.refetch_result(json.dumps(doc, indent=1, sort_keys=True).encode() + b"\n", "result record")


def test_a_manifest_of_the_read_lists_each_file_by_size_and_digest():
    listed = rec.read_manifest((READ / "ibm-refetch" / "MANIFEST.json").read_bytes(), "MANIFEST",
                               rec.REFETCH_MANIFEST_FORMAT)
    assert len(listed) == 72
    mine, _ = read_records("known-answer")
    size, digest = listed[f"ibm_kingston/{mine.name}"]
    assert (size, digest) == (mine.stat().st_size, hashlib.sha256(mine.read_bytes()).hexdigest())
    other = rec.read_manifest((READ / "ibm-results-refetch" / "MANIFEST.json").read_bytes(), "MANIFEST",
                              rec.RESULTS_MANIFEST_FORMAT)
    assert len(other) == 65
    with pytest.raises(rec.RecordError, match="format is"):
        rec.read_manifest((READ / "ibm-refetch" / "MANIFEST.json").read_bytes(), "MANIFEST", rec.RESULTS_MANIFEST_FORMAT)


def test_a_manifest_that_lists_a_file_twice_is_refused():
    doc = json.loads((READ / "ibm-refetch" / "MANIFEST.json").read_bytes())
    doc["files"].append(dict(doc["files"][0]))
    with pytest.raises(rec.RecordError, match="twice"):
        rec.read_manifest(json.dumps(doc).encode(), "MANIFEST", rec.REFETCH_MANIFEST_FORMAT)


def test_a_snapshots_stamp_is_the_one_its_file_name_states():
    assert rec.stamp_of("properties-20261005T090246Z.json", "x") == "2026-10-05T09:02:46Z"
    for bad in ("properties-20261005T090246.json", "properties-2026100T090246Z.json", "snapshot-20261005T090246Z.json",
                "properties-20261005T090246Z.json.bak", "properties-20261005t090246Z.json"):
        with pytest.raises(rec.RecordError, match="not named properties"):
            rec.stamp_of(bad, "x")


# -- Atlas ------------------------------------------------------------------------------------------------------------------------
ATLAS_LINE = (b'{"circuit_sha256": "ed767c01bd4b851d08993da80f715676e345fc95a10f3bda05400f738e400b36", "code_commit": '
              b'"6130b39e054125f5d7cb15c31d52b16de11d708c", "commitment": "394300991b272221b4ca3a2ff4c5fa63cd8ea10bf66eec459'
              b'dae3cd9a22a93f4", "decode": "quantum_film.atlas.decode/v1", "engine": "tomography-api-v2", "format": '
              b'"quantum-film/commitment/v2", "job_id": "8586f1cc-a312-4ad4-8f4b-2ff2524676ae", "qasm_file": '
              b'"circuit-ed767c01bd4b851d.qasm", "salt": "e30eadf492fd67136f8becfda00004c5c8a5df08b5fcc946987e05ea599853e9", '
              b'"shots": 4096, "stock": "pauli-4x4", "submitted_at": "2026-09-25T22:52:49Z"}\n')


def test_an_atlas_commitment_line_recomputes_under_version_2_from_its_own_fields():
    """Quantum-Film's first Atlas line (a record of its own, MIT): the real commitment, from the seven fields."""
    (jid, line), = rec.atlas_lines(ATLAS_LINE, "commitments.jsonl").items()
    assert jid == line.job_id and line.shots == 4096 and line.engine == "tomography-api-v2"
    got = rec.commitment_v2(line.stock, line.circuit_sha256, line.engine, line.job_id, line.shots, line.decode, line.salt)
    assert got == line.commitment == "394300991b272221b4ca3a2ff4c5fa63cd8ea10bf66eec459dae3cd9a22a93f4"


def test_each_field_of_commitment_v2_binds_and_so_does_the_version():
    args = ("pauli-4x4", "a" * 64, "tomography-api-v2", "job", 4096, "quantum_film.atlas.decode/v1", "b" * 64)
    base = rec.commitment_v2(*args)
    for i, other in enumerate(("pauli-4x5", "c" * 64, "other", "jobs", 4097, "quantum_film.atlas.decode/v2", "d" * 64)):
        assert rec.commitment_v2(*args[:i], other, *args[i + 1:]) != base, i
    assert hashlib.sha256(p1_commit.stream("quantum-film/commitment/v3", *args)).hexdigest() != base
    assert hashlib.sha256(p1_commit.stream(rec.COMMITMENT_V2, *args)).hexdigest() == base
    for bad in (4096.0, True, None):
        with pytest.raises(TypeError):
            rec.commitment_v2(*args[:4], bad, *args[5:])


@pytest.mark.parametrize("data, why", [
    (ATLAS_LINE[:-1], "does not end in a line feed"),
    (ATLAS_LINE + ATLAS_LINE, "twice"),
    (ATLAS_LINE.replace(b"commitment/v2", b"commitment/v3"), "format is"),
    (ATLAS_LINE.replace(b'"shots": 4096', b'"shots": "4096"'), "shots is not a whole number"),
    (b"[]\n", "not an object"),
    (b"{}\n", "lacks format"),
    (ATLAS_LINE.replace(b'"stock"', b'"stock", "stock"'), "not JSON"),
])
def test_commitment_lines_that_are_not_lines_of_version_2_are_refused(data, why):
    with pytest.raises(rec.RecordError, match=why):
        rec.atlas_lines(data, "commitments.jsonl")


def test_atlas_submit_status_and_score_give_their_job_ids():
    submit = json.dumps({"body": {"params": {"circuit_qasm": "OPENQASM 2.0;\n", "shots": 4096}}, "response": {"job_id": "j"}})
    assert rec.atlas_submit(submit.encode(), "submit") == ("j", "OPENQASM 2.0;\n", 4096)
    assert rec.atlas_status(b'{"job_id": "j", "status": "completed"}', "status") == ("j", "completed")
    assert rec.atlas_score(b'{"job_id": "j", "chi2_per_dof": 0.9}', "score") == "j"
    for bad in (b"{}", b'{"body": {"params": {}}, "response": {"job_id": "j"}}'):
        with pytest.raises(rec.RecordError):
            rec.atlas_submit(bad, "submit")
    with pytest.raises(rec.RecordError):
        rec.atlas_status(b'{"job_id": "j"}', "status")


# -- hostile files, every reader ------------------------------------------------------------------------------------------------
READERS = {
    "manifest": (lambda: twin_file(MANIFEST), lambda d: rec.manifest(d, "x")),
    "line": (lambda: run_file("known-answer-line.json"), lambda d: rec.line(d, "x")),
    "record": (lambda: next(RUN.glob("known-answer-pub0-*.json")).read_bytes(), lambda d: rec.device_run(d, "x").fields("x")),
    "metrics": (lambda: run_file("known-answer-metrics.json"), lambda d: rec.metrics(d, "x")),
    "job record": (lambda: read_records("known-answer")[0].read_bytes(), lambda d: rec.refetch_job(d, "x")),
    "result record": (lambda: read_records("known-answer")[1].read_bytes(), lambda d: rec.refetch_result(d, "x")),
    "refetch MANIFEST": (lambda: (READ / "ibm-refetch" / "MANIFEST.json").read_bytes(),
                         lambda d: rec.read_manifest(d, "x", rec.REFETCH_MANIFEST_FORMAT)),
    "atlas lines": (lambda: ATLAS_LINE, lambda d: rec.atlas_lines(d, "x")),
}
LEAVES = (None, True, False, 0, -1, 2.5, "", "x", [], {}, [0], {"a": 1})


def leaf_paths(doc, skip=("coupling", "chain", "counts", "files")):
    """Every path to a value of a document (a dict's keys, a list's first three items), but into the long lists."""
    out = []

    def walk(x, path):
        if isinstance(x, dict):
            for k, v in x.items():
                if k not in skip:
                    out.append(path + (k,))
                    walk(v, path + (k,))
        elif isinstance(x, list):
            for i, v in enumerate(x[:3]):
                out.append(path + (i,))
                walk(v, path + (i,))
    walk(doc, ())
    return out


def replaced(doc, path, value):
    new = copy.deepcopy(doc)
    node = new
    for k in path[:-1]:
        node = node[k]
    if value is ...:
        del node[path[-1]]
    else:
        node[path[-1]] = value
    return new


@pytest.mark.parametrize("name", sorted(READERS))
def test_no_value_of_the_wrong_kind_in_any_place_of_a_record_crashes_its_reader(name):
    """Each place of each real record replaced by each kind of value, or deleted: the reader reads it or raises its
    RecordError, and raises nothing else."""
    data, read = READERS[name][0](), READERS[name][1]
    jsonl = name == "atlas lines"
    doc = json.loads(data.splitlines()[0] if jsonl else data)
    read(data)
    tried = 0
    for path in leaf_paths(doc):
        for value in (*LEAVES, ...):
            new = json.dumps(replaced(doc, path, value)).encode() + (b"\n" if jsonl else b"")
            try:
                read(new)
            except rec.RecordError:
                pass
            tried += 1
    assert tried > 100


@pytest.mark.parametrize("name", sorted(READERS))
@pytest.mark.parametrize("bytes_, why", [(b"", "not JSON"), (b"{", "not JSON"), (b"[1]", "not an object"),
                                         (b"\xff\xfe", "not UTF-8"), (b'{"a": NaN}', "no value"),
                                         (b'{"a": 1, "a": 2}', "twice"), (b'{"a": 1e999}', "past binary64"),
                                         (b'{"a": 99999999999999999999}', "past")])
def test_bytes_that_are_not_a_json_object_are_a_record_error_in_every_reader(name, bytes_, why):
    read = READERS[name][1]
    with pytest.raises(rec.RecordError, match=why):
        read(bytes_ + (b"\n" if name == "atlas lines" else b""))
