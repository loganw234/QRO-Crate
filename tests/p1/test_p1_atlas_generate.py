"""P1.2's Atlas generator (qro/p1_generate.py `atlas`), on a small crate made here in the adapter's layout (no Moth byte is
committed: the six real law results and the vector are read in the p1-crates stage), and its guard G11.

The crate has two law jobs, one on each day, the known-answer vector and the LICENSE, every record consistent: lines of
commitment v2 that recompute, requests that carry the circuit they name, results, statuses and scores of the job. None of
it is Moth's. P2 is pinned absent in every test that checks the crate whole, so that a crate built here is checked as it
is built, whatever the tree holds."""
import json

import pytest

import p1_builder
from controls import plants_p1 as plants
from p1_support import (ATLAS_CIRCUIT, ATLAS_COMMIT, ATLAS_JOBS, ATLAS_QASM, VECTOR, atlas_job_files, generated, graph, guard, jline,
                        of_type, p1_verdict, pin_p2, synthetic_atlas)
from qro import canonical, checker, p1_decode, p1_records as rec

DAY1, JOB1 = ATLAS_JOBS[0]
DAY2, JOB2 = ATLAS_JOBS[1]
ORPHAN = "cccccccc-1111-4222-8333-444444444444"          # a job the crate carries no files of
SHOTS = sum(p1_builder.LAYOUTS.values())
VECTOR_JOB = "synthetic-vector"


@pytest.fixture
def crate(tmp_path, monkeypatch):
    pin_p2(monkeypatch, None)
    return synthetic_atlas(tmp_path)


def at(day, name):
    return f"{day}/p3/{name}"


def set_vector_job(crate, job):
    p = crate.joinpath(*VECTOR.split("/"))
    doc = json.loads(p.read_bytes())
    doc["job"] = job
    p.write_bytes(json.dumps(doc, sort_keys=True).encode())


def edit_json(crate, rel, edit):
    p = crate.joinpath(*rel.split("/"))
    doc = json.loads(p.read_bytes())
    edit(doc)
    p.write_bytes(jline(doc))


def edit_line(crate, day, edit, recompute=True):
    """The day's one commitment line edited, and its commitment recomputed unless told not to."""
    p = crate.joinpath(*at(day, "commitments.jsonl").split("/"))
    line = json.loads(p.read_bytes())
    edit(line)
    if recompute:
        line["commitment"] = rec.commitment_v2(line["stock"], line["circuit_sha256"], line["engine"], line["job_id"],
                                               line["shots"], line["decode"], line["salt"])
    p.write_bytes(json.dumps(line, sort_keys=True, separators=(",", ":")).encode() + b"\n")


def add_line(crate, day, recompute=True, **changes):
    """A second line in the day's file, for a job the crate carries no files of: the day's line with another job id,
    then `changes`, and its commitment recomputed unless told not to."""
    p = crate.joinpath(*at(day, "commitments.jsonl").split("/"))
    data = p.read_bytes()
    line = json.loads(data.splitlines()[0])
    line.update(job_id=ORPHAN, **changes)
    if recompute:
        line["commitment"] = rec.commitment_v2(line["stock"], line["circuit_sha256"], line["engine"], line["job_id"],
                                               line["shots"], line["decode"], line["salt"])
    p.write_bytes(data + json.dumps(line, sort_keys=True, separators=(",", ":")).encode() + b"\n")


def write_md(crate, md=None):
    md = generated(crate, "atlas") if md is None else md
    (crate / canonical.DESCRIPTOR).write_bytes(canonical.write(md))
    return md


def test_the_atlas_crate_is_written_as_the_design_says(crate):
    md = generated(crate, "atlas")
    ids = graph(md)
    kinds = {}
    for e in md["@graph"]:
        kinds[tuple(canonical.types(e))] = kinds.get(tuple(canonical.types(e)), 0) + 1
    assert kinds == {("File",): 11, ("File", "qro:RawResult"): 3, ("Dataset",): 4, ("IndividualProduct",): 1,
                     ("SoftwareApplication",): 2, ("qro:Pub",): 3, ("CreateAction", "qro:Job"): 3,
                     ("CreateAction", "qro:Decode"): 3, ("CreativeWork", "Profile"): 2, ("CreativeWork", "qro:Question"): 1,
                     ("CreativeWork",): 2}
    assert {"#device-moth-atlas-emu", "#engine-tomography-api-v2", "#rule-quantum_film.atlas.decode.v1", "#licence-moth-data",
            "#atlas-vectors", f"#atlas-{DAY1}", f"#atlas-{DAY2}", "#question", "LICENSE-quantum-film"} <= set(ids)
    device = ids["#device-moth-atlas-emu"]
    assert (device["qro:deviceKind"], device["name"]) == ("simulator", "moth-atlas-emu")
    root = md["@graph"][1]
    assert root["qro:generator"] == "qro-p1-atlas"
    assert {r["@id"] for r in root["hasPart"]} == {"#atlas-vectors", f"#atlas-{DAY1}", f"#atlas-{DAY2}", "LICENSE-quantum-film"}
    assert len(root["mentions"]) == 6


def test_a_law_job_a_pub_and_a_decode_of_atlas(crate):
    ids = graph(generated(crate, "atlas"))
    for day, jid in ATLAS_JOBS:
        job, pub, decode = ids[f"#job-{jid}"], ids[f"#pub-{jid}-0"], ids[f"#decode-{jid}"]
        assert (pub["qro:role"], pub["qro:commitment"]) == ("law", "none") and set(pub) == {"@id", "@type", "qro:role",
                                                                                         "qro:commitment"}
        assert (job["startTime"], job["endTime"], job["qro:calibrationLink"]) == ("unknown", "unknown", "unexposed")
        assert job["qro:kitCommit"] == ATLAS_COMMIT and job["qro:jobId"] == jid
        assert not {"qro:line", "qro:clock", "qro:calibration", "qro:historyAtRunning"} & set(job)
        assert job["instrument"] == {"@id": "#engine-tomography-api-v2"} and job["qro:device"] == {"@id": "#device-moth-atlas-emu"}
        raw = at(day, f"atlas-{jid[:8]}-result.json")
        assert ids[raw]["qro:rawForm"] == "atlas-tomography-result/v1" and ids[raw]["qro:shots"] == SHOTS
        assert sorted(r["@id"] for r in job["result"]) == sorted([raw, at(day, f"atlas-{jid[:8]}-submit.json"),
                                                                  at(day, f"atlas-{jid[:8]}-status.json"),
                                                                  at(day, f"score-{jid[:8]}.json")])
        assert (decode["qro:decodeRule"], decode["qro:bitOrder"]) == ("quantum_film.atlas.decode/v1", "atlas-register")
        assert decode["object"] == [{"@id": raw}] and decode["instrument"] == {"@id": "#rule-quantum_film.atlas.decode.v1"}
        assert decode["qro:knownAnswer"] == {"@id": f"#pub-{VECTOR_JOB}-0"}


def test_the_vectors_job_is_the_known_answer_and_its_result_the_vector(crate):
    ids = graph(generated(crate, "atlas"))
    job, pub = ids[f"#job-{VECTOR_JOB}"], ids[f"#pub-{VECTOR_JOB}-0"]
    assert pub["qro:role"] == "known-answer" and job["qro:kitCommit"] == "unknown"
    assert job["result"] == [{"@id": VECTOR}]
    assert ids[VECTOR]["qro:rawForm"] == "atlas-known-answer-vector/v1" and ids[VECTOR]["qro:shots"] == 32 * 128
    assert ids[f"#decode-{VECTOR_JOB}"]["qro:knownAnswer"] == {"@id": f"#pub-{VECTOR_JOB}-0"}


def test_moths_responses_carry_its_licence_and_quantum_films_own_files_the_mit_notice(crate):
    ids = graph(generated(crate, "atlas"))
    for day, jid in ATLAS_JOBS:
        for name in (f"atlas-{jid[:8]}-submit.json", f"atlas-{jid[:8]}-status.json", f"atlas-{jid[:8]}-result.json"):
            assert ids[at(day, name)]["license"] == {"@id": "#licence-moth-data"}, name
        for name in (f"score-{jid[:8]}.json", "commitments.jsonl", ATLAS_CIRCUIT):
            assert ids[at(day, name)]["license"] == {"@id": "LICENSE-quantum-film"}, name
    assert ids[VECTOR]["license"] == {"@id": "#licence-moth-data"} and "license" not in ids["LICENSE-quantum-film"]


def test_the_question_names_the_first_by_id_of_the_circuits_with_one_digest_and_the_rule(crate):
    q = graph(generated(crate, "atlas"))["#question"]
    assert sorted(r["@id"] for r in q["object"]) == sorted([at(DAY1, ATLAS_CIRCUIT),
                                                          "#rule-quantum_film.atlas.decode.v1"])


def test_the_steps_of_p1_accept_the_atlas_crate_and_step_9_regenerates_it(crate):
    md = write_md(crate)
    for step in (4, 5, 8):
        assert p1_builder.refusal(step, crate) is None, step
    checker.load()
    assert canonical.body_digest(checker.check(crate)) == canonical.body_digest(md)


def test_the_atlas_pubs_layouts_are_read_through_the_graph_alone_as_p2_will_read_them(crate):
    md = generated(crate, "atlas")
    for _, jid in ATLAS_JOBS:
        counts = p1_decode.pub_counts(crate, {"@graph": md["@graph"]}, f"#pub-{jid}-0")
        assert counts == {tuple(sorted(k)): v for k, v in p1_builder.LAYOUTS.items()}


def test_the_atlas_output_does_not_depend_on_the_metadata_file(crate):
    want = generated(crate, "atlas")
    (crate / canonical.DESCRIPTOR).write_bytes(b"\xff not json")
    assert generated(crate, "atlas") == want


# -- G11 and the other guards of this crate -------------------------------------------------------------------------------------------
CASES = []


def case(name, needle):
    def register(fn):
        CASES.append(pytest.param(fn, needle, id=name))
        return fn
    return register


@case("a commitment that does not recompute", "does not recompute")
def line_commitment(c):
    edit_line(c, DAY1, lambda line: line.update(commitment="0" * 64), recompute=False)


@case("a line's shots that are not the request's", "disagree on the shots")
def line_shots(c):
    edit_line(c, DAY1, lambda line: line.update(shots=SHOTS + 1))


@case("a line's circuit digest that is not the file's", "does not hash as the line says")
def line_circuit(c):
    edit_line(c, DAY1, lambda line: line.update(circuit_sha256="2" * 64))


@case("a line's decode that is not Atlas's rule", "line's decode is")
def line_decode(c):
    edit_line(c, DAY1, lambda line: line.update(decode="quantum_film.ibm.decode/v1"))


@case("lines that name two engines", "more than one engine")
def line_engine(c):
    edit_line(c, DAY2, lambda line: line.update(engine="another-engine"))


@case("a line of another job than the request's", "no line of its day")
def line_job(c):
    edit_line(c, DAY1, lambda line: line.update(job_id="cccccccc-1111-4222-8333-444444444444"))


@case("a line of the other day", "no line of its day")
def line_day(c):
    p1, p2 = (c.joinpath(*at(d, "commitments.jsonl").split("/")) for d in (DAY1, DAY2))
    first, second = p1.read_bytes(), p2.read_bytes()
    p1.write_bytes(second)
    p2.write_bytes(first)


@case("a line's code commit that is no commit", "no commit")
def line_commit(c):
    edit_line(c, DAY1, lambda line: line.update(code_commit="xyz"))


@case("a request whose circuit is not the file's", "request's circuit is not the file's")
def submit_circuit(c):
    edit_json(c, at(DAY1, f"atlas-{JOB1[:8]}-submit.json"),
              lambda doc: doc["body"]["params"].update(circuit_qasm=ATLAS_QASM + "x q[1];\n"))


@case("a request that asks other shots than the line", "disagree on the shots")
def submit_shots(c):
    edit_json(c, at(DAY1, f"atlas-{JOB1[:8]}-submit.json"), lambda doc: doc["body"]["params"].update(shots=SHOTS + 1))


@case("a result of another job", "result is of another job")
def result_job(c):
    edit_json(c, at(DAY1, f"atlas-{JOB1[:8]}-result.json"), lambda doc: doc.update(job_id=JOB2))


@case("a status that is not completed", "completed")
def status(c):
    edit_json(c, at(DAY1, f"atlas-{JOB1[:8]}-status.json"), lambda doc: doc.update(status="failed"))


@case("a score of another job", "score file is of another job")
def score(c):
    edit_json(c, at(DAY1, f"score-{JOB1[:8]}.json"), lambda doc: doc.update(job_id=JOB2))


@case("a job with no status file", "no status file")
def no_status(c):
    c.joinpath(*at(DAY1, f"atlas-{JOB1[:8]}-status.json").split("/")).unlink()


@case("a crate with no vector", "one known-answer vector")
def no_vector(c):
    c.joinpath(*VECTOR.split("/")).unlink()


@case("a line twice in one file", "twice")
def twice(c):
    p = c.joinpath(*at(DAY1, "commitments.jsonl").split("/"))
    p.write_bytes(p.read_bytes() * 2)


@case("lines that do not end in a line feed", "does not end in a line feed")
def no_lf(c):
    p = c.joinpath(*at(DAY1, "commitments.jsonl").split("/"))
    p.write_bytes(p.read_bytes()[:-1])


@case("a vector that is no vector", "the vector")
def bad_vector(c):
    c.joinpath(*VECTOR.split("/")).write_bytes(b'{"job": 1}')


@case("a result that is no result", "the result")
def bad_result(c):
    c.joinpath(*at(DAY1, f"atlas-{JOB1[:8]}-result.json").split("/")).write_bytes(b"[]")


@case("one job's line in the files of two days", "has a line twice")
def line_twice_across_days(c):
    p1, p2 = (c.joinpath(*at(d, "commitments.jsonl").split("/")) for d in (DAY1, DAY2))
    p1.write_bytes(p1.read_bytes() + p2.read_bytes())


@case("a result whose shots are not the line's", "disagree on the shots")
def result_shots(c):
    def edit(doc):
        for setting in doc["response"]["result"]["measurements"].values():
            setting["counts"][next(iter(setting["counts"]))] += 1
            setting["shots"] += 1
    edit_json(c, at(DAY1, f"atlas-{JOB1[:8]}-result.json"), edit)


@case("a day with a second circuit file, which the line does not name", "is not the day's")
def second_circuit(c):
    one = c.joinpath(*at(DAY1, ATLAS_CIRCUIT).split("/"))
    c.joinpath(*at(DAY1, "circuit-ffffffffffffffff.qasm").split("/")).write_bytes(one.read_bytes())


@case("a job whose files are named by another id than its own", "an id that is not its files'")
def files_of_another_id(c):
    for name in ("submit", "status", "result"):
        c.joinpath(*at(DAY1, f"atlas-{JOB1[:8]}-{name}.json").split("/")).rename(
            c.joinpath(*at(DAY1, "atlas-cccccccc-" + name + ".json").split("/")))
    c.joinpath(*at(DAY1, f"score-{JOB1[:8]}.json").split("/")).rename(c.joinpath(*at(DAY1, "score-cccccccc.json").split("/")))


@case("a status file of another job", "not of this job")
def status_of_another_job(c):
    edit_json(c, at(DAY1, f"atlas-{JOB1[:8]}-status.json"), lambda doc: doc.update(job_id=JOB2))


@case("a line for a job the crate carries no files of", "carries no files of")
def orphan(c):
    add_line(c, DAY1)


@case("an orphan line whose commitment does not recompute", "does not recompute")
def orphan_commitment(c):
    add_line(c, DAY1, recompute=False, commitment="0" * 64)


@case("an orphan line whose decode is not Atlas's rule", "line's decode is")
def orphan_decode(c):
    add_line(c, DAY1, decode="x")


@case("an orphan line whose code commit is no commit", "no commit")
def orphan_commit(c):
    add_line(c, DAY1, code_commit="not a commit")


@case("an orphan line that names another engine", "more than one engine")
def orphan_engine(c):
    add_line(c, DAY1, engine="another-engine")


@case("an orphan line with the wrong shots, decode and code commit at once", "does not recompute")
def orphan_everything(c):
    add_line(c, DAY1, recompute=False, shots=5, decode="x", code_commit="not a commit")


@case("the vector's job is a law job", "written twice")
def vector_is_a_law_job(c):
    set_vector_job(c, JOB1)


@pytest.mark.parametrize("plant, needle", CASES)
def test_each_planted_fault_of_the_atlas_records_is_a_g11_raise(crate, plant, needle):
    plant(crate)
    g = guard(crate, "atlas")
    assert g is not None and g.guard == "G11" and needle in g.detail, (g and (g.guard, g.where, g.detail))


def test_an_orphan_line_is_the_generators_refusal_where_a_crate_carries_it_and_step_9_refuses_it(crate):
    """The crate as the adapter wrote it, with a line added for a job it carries no files of and its digest resealed:
    steps 1 to 8 accept it (none reads a line); the generator, which step 9 runs, does not."""
    write_md(crate)
    assert p1_verdict(crate) is None
    add_line(crate, DAY1)
    plants.patch(crate, lambda g: None, reseal=[at(DAY1, "commitments.jsonl")])
    refused = p1_verdict(crate)
    assert refused is not None and refused.name == "metadata-generated", refused
    assert "failed on the records: GuardError" in refused.detail, refused.detail


def test_a_vector_of_a_law_jobs_id_is_refused_at_step_9_and_not_regenerated_into_a_crate_that_reads_one_job_less(crate):
    write_md(crate)
    before = [e["@id"] for e in of_type(generated(crate, "atlas"), "qro:Job")]
    set_vector_job(crate, JOB1)
    plants.patch(crate, lambda g: None, reseal=[VECTOR])
    refused = p1_verdict(crate)
    assert refused is not None and refused.name == "metadata-generated" and "failed on the records: GuardError" in refused.detail, refused
    with pytest.raises(plants.p1_generate.GuardError) as raised:      # and the toolkit's rebuild does not write it either
        plants.rebuild(crate)
    assert raised.value.guard == "G11" and len(before) == 3


def test_a_file_that_fits_no_layout_of_the_atlas_crate_is_g12(crate):
    for rel in (at(DAY1, "circuit-0123456789abcdef.platform.json"), "extra.txt", at(DAY1, "rolls-aaaaaaaa/x.json")):
        crate.joinpath(*rel.split("/")).parent.mkdir(parents=True, exist_ok=True)
        crate.joinpath(*rel.split("/")).write_bytes(b"x")
        g = guard(crate, "atlas")
        assert (g.guard, g.where) == ("G12", rel)
        crate.joinpath(*rel.split("/")).unlink()


def test_a_day_with_several_jobs_shares_one_circuit_and_one_file_of_lines(crate):
    """As the real 2026-09-26 does: five jobs, one circuit file, five lines in one commitments.jsonl."""
    assert guard(crate, "atlas") is None
    jid = "dddddddd-1111-4222-8333-444444444444"
    for rel, data in atlas_job_files(DAY2, jid, SHOTS).items():
        p = crate.joinpath(*rel.split("/"))
        if p.name == "commitments.jsonl":
            data = p.read_bytes() + data
        p.write_bytes(data)
    md = generated(crate, "atlas")
    assert len(of_type(md, "qro:Job")) == 4 and f"#job-{jid}" in graph(md)
    write_md(crate, md)
    for step in (4, 5, 8):
        assert p1_builder.refusal(step, crate) is None, step


# -- the classes of carried bytes the checker holds by their digests alone (the verifier's D5) ------------------------------------------------------
def line_submitted(c):
    edit_line(c, DAY1, lambda line: line.update(submitted_at="2026-09-25T23:00:00Z"), recompute=False)


def a_shot_moved_in_a_setting_not_all_z(o):
    """One shot moved between two outcomes of a setting other than the all-Z one, their sum kept."""
    settings = o["response"]["result"]["measurements"]
    counts = settings[next(label for label in sorted(settings) if set(label) - set("IZ"))]["counts"]
    most, other = sorted(counts, key=lambda k: (-counts[k], k))[:2]
    counts[most] -= 1
    counts[other] += 1


RESULT = f"atlas-{JOB1[:8]}-result.json"
ATLAS_CARRIED = [
    ("a request's method", f"atlas-{JOB1[:8]}-submit.json", lambda o: o.update(method="PUT")),
    ("a request's HTTP status", f"atlas-{JOB1[:8]}-submit.json", lambda o: o.update(status=200)),
    ("a request's response status", f"atlas-{JOB1[:8]}-submit.json", lambda o: o["response"].update(status="running")),
    ("a status file's other field", f"atlas-{JOB1[:8]}-status.json", lambda o: o.update(updated_at="2026-09-25T23:59:59Z")),
    ("a score file's records", f"score-{JOB1[:8]}.json", lambda o: o.update(records=4)),
    ("a score file's own commitment", f"score-{JOB1[:8]}.json", lambda o: o.update(commitment="0" * 64)),
    ("a result envelope's path", RESULT, lambda o: o.update(path="/elsewhere")),
    ("a result envelope's taken_from", RESULT, lambda o: o.update(taken_from="elsewhere")),
    ("a result envelope's HTTP status", RESULT, lambda o: o.update(status=201)),
    ("a result envelope's fetched_at", RESULT, lambda o: o.update(fetched_at="2026-09-26T03:04:05Z")),
    ("a result's observables, the engine's numbers", RESULT,
     lambda o: o["response"]["result"]["observables"]["0"].update(X=0.5)),
    ("a result's density matrices, the engine's numbers", RESULT,
     lambda o: o["response"]["result"]["density_matrices"]["0"]["real"][0].__setitem__(0, 0.5)),
    ("a setting other than the all-Z one, a shot moved: its counts held by their sum alone", RESULT,
     a_shot_moved_in_a_setting_not_all_z),
    ("Quantum-Film's licence text", None, None),
]


@pytest.mark.parametrize("label, name, edit", ATLAS_CARRIED, ids=[c[0] for c in ATLAS_CARRIED])
def test_a_leaf_of_a_carried_atlas_file_changed_with_only_its_own_digest_resealed_is_accepted_by_every_step(crate, label, name, edit):
    """Limit 21, Atlas's side: the request, the result's envelope, the engine's numbers, the counts of a setting past their
    sum, the score and the licence are held by their digests but for the fields the generator derives a value from (the
    job's id, the circuit, the shots, the all-Z counts), and a changed leaf, resealed, passes."""
    write_md(crate)
    assert p1_verdict(crate) is None
    rel = plants.LICENSE_NAME if name is None else at(DAY1, name)
    path = crate.joinpath(*rel.split("/"))
    before = path.read_bytes()
    if edit is None:
        path.write_bytes(before + b"A line the producer added.\n")
    else:
        edit_json(crate, rel, edit)
    assert path.read_bytes() != before
    plants.patch(crate, lambda g: None, reseal=[rel])
    assert p1_verdict(crate) is None, label


def test_a_commitment_lines_submitted_time_changed_with_only_the_files_digest_resealed_is_accepted_by_every_step(crate):
    write_md(crate)
    rel = at(DAY1, "commitments.jsonl")
    before = crate.joinpath(*rel.split("/")).read_bytes()
    line_submitted(crate)
    assert crate.joinpath(*rel.split("/")).read_bytes() != before
    plants.patch(crate, lambda g: None, reseal=[rel])
    assert p1_verdict(crate) is None
