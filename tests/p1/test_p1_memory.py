"""What the steps keep of a file (the verifier's D2 of round 1, its D1 and D3 of round 2, its D2 of round 3). The first build's
caches kept every parsed raw result, body bytes included, so a crate of 60 small jobs (1.8 MB on disk, 20 MB of shots inflated
for each) drove the checker past 1 GB to a MemoryError, exit 3, and exit 3 is never a crate's fault. The fix kept of a result an
echo, a count of rows, a span and a verdict; round 2 found the same in the job line, which step 4 kept whole for the whole step
(ten lines of 2.1 MB peaked at 456 MB, and 49 MB without that cache), and a gate that did not watch the snapshot documents; round
3 found that the gates named kinds of file and parts of them, and a step that kept another part passed them all. A step keeps
what it needs of a file and never its bytes, so a crate of many files costs the memory of the largest.

The gates, on crates made by p1_builder in the verifier's bigcrate.py's way (a few kilobytes a job on disk). First, one per kind
and part: the peak memory of a step on 8 jobs is within a quarter of that on 1 (tracemalloc), for results (200 KB a job
inflated) and for job lines (180 KB a job, parsing to about 4 MB); no step has a parsed result, a parsed snapshot document or a
parsed job line alive when it parses the next (weak references, which do not depend on any size); and what is held by the time
step 8 reads its first job is the same with snapshots that are large and ones that are not. Then the class, from two sides, at the
end of this file: everything a step is handed of every file (its bytes, each object and array of its document, each parsed
result) is named by a weak reference and none is alive when the step visits the next entity; and each kind of file that can be
padded, and each key of a snapshot, is padded with text and the peak (or what is held) on one padded file is held against many."""
import gc
import json
import tracemalloc
import weakref

import pytest
from p1_builder import atlas_many_model, ibm_model, judge, ka_qasm, many_jobs_model, read_md, sha

from qro import p1_calibration, p1_forms, p1_steps

N, ROWS = 8, 100_000                         # 200 KB of shots inflated for each result, a few kilobytes on disk
PAD = 60_000                                 # entries of padding in a job line: `[[],[],...]`, 180 KB, about 4 MB parsed
STEPS = (4, 5, 8)


@pytest.fixture(scope="module")
def crates(tmp_path_factory):
    out = {}
    for n in (1, N):
        crate = many_jobs_model(n, ROWS).write(tmp_path_factory.mktemp(f"jobs{n}"))
        out[n] = (crate, read_md(crate))
    return out


def padded_lines(m, n, entries):
    """The model's n job lines, each with `entries` empty arrays beside its commitments."""
    for i in range(n):
        path = f"run/job{i:03d}-line.json"
        doc = json.loads(m.files[path])
        doc["pad"] = "PAD"
        text = json.dumps(doc, indent=1, sort_keys=True).replace('"PAD"', "[" + ",".join(["[]"] * entries) + "]")
        m.files[path] = text.encode("utf-8") + b"\n"
    return m


@pytest.fixture(scope="module")
def line_crates(tmp_path_factory):
    out = {}
    for n in (1, N):
        crate = padded_lines(many_jobs_model(n, 100), n, PAD).write(tmp_path_factory.mktemp(f"lines{n}"))
        out[n] = (crate, read_md(crate))
    return out


def peak(step, crate, md):
    gc.collect()
    tracemalloc.start()
    try:
        getattr(p1_steps, f"step{step}")(crate, md)
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


class Doc(dict):
    """A parsed document that can be watched: a plain dict cannot be weakly referenced."""


def watch_documents(monkeypatch, *names):
    """Make the documents p1_forms.load_json returns for these names watchable. Returns the list that gets, at each parse of
    one, the number of the documents parsed before it that are still alive."""
    docs, alive = [], []
    real = p1_forms.load_json

    def load_json(data, what, error=p1_forms.RawFormError):
        out = real(data, what, error)
        if what not in names:
            return out
        alive.append(sum(1 for r in docs if r() is not None))
        watched = Doc(out)
        docs.append(weakref.ref(watched))
        return watched
    monkeypatch.setattr(p1_forms, "load_json", load_json)
    return alive


def test_the_crates_are_small_on_disk_and_every_step_accepts_them(crates, line_crates):
    for n, (crate, md) in crates.items():
        on_disk = sum(p.stat().st_size for p in crate.rglob("*") if p.is_file())
        assert on_disk < 40_000 * n + 20_000, (n, on_disk)             # a few kilobytes a job; inflated, megabytes a job
        for step in STEPS:
            getattr(p1_steps, f"step{step}")(crate, md)
    for n, (crate, md) in line_crates.items():
        on_disk = sum(p.stat().st_size for p in crate.rglob("*") if p.is_file())
        assert 3 * PAD * n < on_disk < 3 * PAD * n + 40_000 * n + 20_000, (n, on_disk)     # the padding is most of it
        for step in STEPS:
            getattr(p1_steps, f"step{step}")(crate, md)


# -- raw results ----------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("step", STEPS)
def test_a_step_costs_the_memory_of_one_raw_result_however_many_the_crate_holds(crates, step):
    one, many = peak(step, *crates[1]), peak(step, *crates[N])
    assert one > 2 * ROWS, f"step {step}: {one} bytes for a result of {2 * ROWS}: the result was not read"
    assert many < 1.25 * one, f"step {step}: {one} bytes for 1 job, {many} for {N}"


@pytest.mark.parametrize("step", STEPS)
def test_no_step_has_a_parsed_result_alive_when_it_parses_the_next(crates, monkeypatch, step):
    crate, md = crates[N]
    seen, alive = [], []
    real = p1_forms.parse_raw

    def parse_raw(form, data):
        alive.append(sum(1 for r in seen if r() is not None))
        result = real(form, data)
        seen.append(weakref.ref(result))
        return result
    monkeypatch.setattr(p1_forms, "parse_raw", parse_raw)
    getattr(p1_steps, f"step{step}")(crate, md)
    assert len(alive) == N and max(alive) == 0, alive


# -- job lines (round 2, D3) -----------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("step", (4, 5))
def test_a_step_costs_the_memory_of_one_job_line_however_many_the_crate_holds(line_crates, step):
    one, many = peak(step, *line_crates[1]), peak(step, *line_crates[N])
    assert one > 10 * 3 * PAD, f"step {step}: {one} bytes for a line of {3 * PAD}: the line was not parsed"
    assert many < 1.25 * one, f"step {step}: {one} bytes for 1 job, {many} for {N}"


@pytest.mark.parametrize("step", (4, 5))
def test_no_step_has_a_job_line_alive_when_it_reads_the_next(line_crates, monkeypatch, step):
    """Step 4 reads each job's line once, and keeps its commitments; step 5 reads two lines for each Decode, the job's and the
    known answer's, one after the other, and keeps the bundle of each."""
    crate, md = line_crates[N]
    alive = watch_documents(monkeypatch, "the job line", "the known answer's job line")
    getattr(p1_steps, f"step{step}")(crate, md)
    gc.collect()
    assert len(alive) == (N if step == 4 else 2 * N) and max(alive) == 0, alive


# -- snapshots (round 1, D2; round 2, D1) ------------------------------------------------------------------------------------------
def test_step_8_has_no_parsed_snapshot_alive_when_it_parses_the_next(tmp_path, monkeypatch):
    """What the link rule weighs of a snapshot is its device, its stamp and its newest value: not the object parse_snapshot built."""
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    seen, alive = [], []
    real = p1_forms.parse_snapshot

    def parse_snapshot(data):
        alive.append(sum(1 for r in seen if r() is not None))
        snapshot = real(data)
        seen.append(weakref.ref(snapshot))
        return snapshot
    monkeypatch.setattr(p1_forms, "parse_snapshot", parse_snapshot)
    p1_steps.step8(crate, md)
    assert len(alive) == 4 and max(alive) == 0, alive


def test_step_8_keeps_no_snapshot_document_itself(tmp_path, monkeypatch):
    """The verifier's D1 of round 2. The Snapshot that parse_snapshot returns can be let go and its document kept, and the
    test above passes that: the light copy built with `snap.doc` kept IBM's whole properties text for each snapshot. The
    documents are watched here, and the step must have none alive when it parses the next."""
    crate = ibm_model().write(tmp_path / "c")
    md = read_md(crate)
    alive = watch_documents(monkeypatch, "the snapshot")
    p1_steps.step8(crate, md)
    gc.collect()
    assert len(alive) == 4 and max(alive) == 0, alive


def padded_snapshots(m, rows):
    """The model's snapshots, each with `rows` qubits more, of measurements that move nothing the link rule reads, and the
    claims drawn from the files again."""
    for path in [p for p in m.files if p.startswith("snapshots/")]:
        doc = m.json(path)
        stamp = doc["qubits"][0][0]["date"]
        doc["qubits"] += [[{"date": stamp, "name": "T1", "unit": "us", "value": 100.5 + i % 7},
                           {"date": stamp, "name": "readout_error", "unit": "", "value": 0.01}] for i in range(rows)]
        m.put_json(path, doc)
        m.ents[path].update(p1_calibration.claims(p1_forms.parse_snapshot(m.files[path])))
    return m


def held_when_the_first_job_is_read(crate, md, monkeypatch):
    """The bytes tracemalloc holds when step 8 asks for the first raw result: the snapshots have all been read by then."""
    seen = []
    real = p1_forms.parse_raw

    def parse_raw(form, data):
        if not seen:
            seen.append(tracemalloc.get_traced_memory()[0])
        return real(form, data)
    gc.collect()
    tracemalloc.start()
    with monkeypatch.context() as mp:
        mp.setattr(p1_forms, "parse_raw", parse_raw)
        try:
            p1_steps.step8(crate, md)
        finally:
            tracemalloc.stop()
    return seen[0]


def test_step_8_holds_nothing_of_a_snapshot_by_the_time_it_reads_the_first_job(tmp_path, monkeypatch):
    """Whatever part of a document a step kept (the dict, a list in it, the text it came from), snapshots of 2,000
    measurements each would show: the crate of large snapshots holds no more at that moment than the crate of small ones."""
    plain = ibm_model().write(tmp_path / "plain")
    padded = padded_snapshots(ibm_model(), 1000).write(tmp_path / "padded")
    sizes = [p.stat().st_size for p in padded.glob("snapshots/*.json")]
    small = held_when_the_first_job_is_read(plain, read_md(plain), monkeypatch)
    large = held_when_the_first_job_is_read(padded, read_md(padded), monkeypatch)
    assert len(sizes) == 4 and min(sizes) > 200_000, sizes
    assert large - small < 200_000, (small, large)


# -- the class: whatever a step keeps of any file (round 3, D2) -------------------------------------------------------------------
# The gates above each name a kind of file and a part of it. A step could keep another part (a snapshot's `gates`, a record,
# a circuit's bytes) and pass them all. These two hold the class, from two sides. The first does not depend on any size: it
# names, by weak reference, everything a step is handed of every file it reads, and counts what is still alive when the step
# visits the next entity. The second does not depend on identity: it pads each kind of file and each key of a snapshot with
# text, and holds the peak (or what is held) on one padded file against many.
class Data(bytearray):
    """A file's bytes as a step reads them, which a weak reference can name (an instance of a subclass of bytes cannot be
    named; one of bytearray can, and a step reads it as it reads bytes)."""


class Dict(dict):
    """An object of a JSON document that a weak reference can name."""


class List(list):
    """An array of a JSON document that a weak reference can name."""


def watched(x, refs, what):
    """x with every object and every array in it made a Dict or a List (equal to the original in every way a step uses it),
    each named in refs by a weak reference."""
    if isinstance(x, dict):
        out = Dict((k, watched(v, refs, what)) for k, v in x.items())
    elif isinstance(x, list):
        out = List(watched(v, refs, what) for v in x)
    else:
        return x
    refs.append((what, weakref.ref(out)))
    return out


class Watch:
    """Weak references on everything a step is handed of a file: the bytes of each file it reads, every object and array of
    each JSON document, each parsed raw result and each parsed snapshot. `visits` has, for each entity the step visits, the
    kinds of those still alive when the visit began; `alive()` the kinds alive now."""

    def __init__(self, monkeypatch):
        self.refs, self.visits = [], []
        real_bytes, real_load, real_raw = p1_steps._bytes, p1_forms.load_json, p1_forms.parse_raw
        real_snapshot, real_visit = p1_forms.parse_snapshot, p1_steps._visit

        def read_bytes(crate, entity, what):
            data = Data(real_bytes(crate, entity, what))
            self.refs.append((f"the bytes of {what}", weakref.ref(data)))
            return data

        def load_json(data, what, error=p1_forms.RawFormError):
            return watched(real_load(data, what, error), self.refs, f"a document read as {what}")

        def parse_raw(form, data):
            out = real_raw(form, data)
            self.refs.append(("a parsed raw result", weakref.ref(out)))
            return out

        def parse_snapshot(data):
            out = real_snapshot(data)
            self.refs.append(("a parsed snapshot", weakref.ref(out)))
            return out

        def visit(idx, type, step, refuse):
            def counted(entity):
                self.visits.append((entity["@id"], self.alive()))
                return step(entity)
            return real_visit(idx, type, counted, refuse)
        for owner, name, fn in ((p1_steps, "_bytes", read_bytes), (p1_forms, "load_json", load_json),
                                (p1_forms, "parse_raw", parse_raw), (p1_forms, "parse_snapshot", parse_snapshot),
                                (p1_steps, "_visit", visit)):
            monkeypatch.setattr(owner, name, fn)

    def alive(self):
        gc.collect()
        return sorted({what for what, ref in self.refs if ref() is not None})


CRATES = {"the small IBM crate": lambda: ibm_model(),
          "six jobs, each its own known answer": lambda: many_jobs_model(6, 50, own_known_answers=True),
          "four Atlas law jobs": lambda: atlas_many_model(4)}


@pytest.mark.parametrize("step", STEPS)
@pytest.mark.parametrize("name", CRATES)
def test_no_step_has_anything_of_a_file_alive_when_it_visits_the_next_entity(tmp_path, monkeypatch, name, step):
    """The class of round 2's D1 and round 3's D2: a step that kept the bytes of a file, a document, any object or array in
    one, a parsed result or a parsed snapshot, whatever the file's size, has it alive at the next entity (the verifier's
    mutants 1 to 3, 5, 7, 8 and 9 of round 3 each keep one). Where a step reads no file (step 4 on the Atlas crate, whose Pubs
    state `none`) there is nothing to watch."""
    crate = CRATES[name]().write(tmp_path / "c")
    md = read_md(crate)
    watch = Watch(monkeypatch)
    getattr(p1_steps, f"step{step}")(crate, md)
    assert watch.visits
    assert [(i, alive) for i, alive in watch.visits if alive] == []
    assert watch.alive() == []
    assert bool(watch.refs) == (name != "four Atlas law jobs" or step != 4), "the watch saw nothing, or too much"


def kept(monkeypatch, owner, name):
    """The function owner.name wrapped so that every result it returns is also kept in a list, which it returns."""
    real, keep = getattr(owner, name), []

    def wrapper(*args, **kwargs):
        out = real(*args, **kwargs)
        keep.append(out)
        return out
    monkeypatch.setattr(owner, name, wrapper)
    return keep


@pytest.mark.parametrize("owner, name", [(p1_steps, "_json"), (p1_steps, "_bytes"), (p1_steps, "_parse")],
                         ids=["a document", "a file's bytes", "a parsed result"])
def test_the_watch_sees_a_step_that_keeps_what_it_reads(tmp_path, monkeypatch, owner, name):
    """The control of the test above: a step made to keep each document, each file's bytes or each parsed result it reads
    is seen at once, on the crate the gate runs, so that a gate that watched nothing would not pass here."""
    crate = many_jobs_model(6, 50, own_known_answers=True).write(tmp_path / "c")
    md = read_md(crate)
    watch = Watch(monkeypatch)
    keep = kept(monkeypatch, owner, name)                # outside the watch, so that it keeps what the watch hands the step
    p1_steps.step5(crate, md)
    assert keep and [i for i, alive in watch.visits if alive], "a step that keeps what it reads was not seen"


# -- every kind of file padded, on one against many -------------------------------------------------------------------------------
TEXT = "x" * 120_000                            # what a file is padded with: cheap to parse, dear to keep, in bytes and as a string


def pad_line(m, i):
    m.edit_json(f"run/job{i:03d}-line.json", lambda doc: doc.__setitem__("pad", TEXT))


def pad_record(m, i):
    m.edit_json(f"run/job{i:03d}-pub0-known-answer.json", lambda doc: doc.__setitem__("pad", TEXT))


def pad_raw(m, i):
    m.edit_json(f"run/job{i:03d}-raw.json", lambda doc: doc["__value__"]["metadata"].__setitem__("note", TEXT))


def pad_atlas(m, i):
    m.edit_json(f"law/result{i}.json", lambda doc: doc.__setitem__("path", TEXT))


def ibm_jobs():
    return many_jobs_model(N, 100, own_known_answers=True)


# kind of file: (how one is padded, the steps that read it, the crate of N of them)
PADDED = {"a job line": (pad_line, (4, 5), ibm_jobs), "a Pub's record": (pad_record, (4, 5), ibm_jobs),
          "an IBM result's wrapper": (pad_raw, (4, 5, 8), ibm_jobs),
          "an Atlas result's wrapper": (pad_atlas, (5, 8), lambda: atlas_many_model(N))}


@pytest.fixture(scope="module")
def padded(tmp_path_factory):
    """padded(kind, count): a crate of N jobs, each its own known answer (the Atlas jobs name the one vector), of which `count`
    have a file of that kind padded."""
    made = {}

    def make(kind, count):
        if (kind, count) not in made:
            m = PADDED[kind][2]()
            for i in range(count):
                PADDED[kind][0](m, i)
            crate = m.write(tmp_path_factory.mktemp("padded"))
            made[kind, count] = (crate, read_md(crate))
        return made[kind, count]
    return make


@pytest.mark.parametrize("kind, step", [(kind, step) for kind, (_, steps, _) in PADDED.items() for step in steps],
                         ids=lambda x: str(x))
def test_a_step_costs_the_largest_file_of_a_kind_however_many_of_them_are_padded(padded, kind, step):
    """The verifier's sumfiles.py, for every kind of file the steps read that can be padded: the peak of a step on a crate
    with one file of the kind padded by 120 KB of text and on the same crate with all eight padded differ by under half
    of it. A step that keeps a file's bytes, its document or any part of one (a Pub's record, a raw result's wrapper, a job
    line) adds a padding for each file it keeps. An Atlas result is padded in its `path`, a string the reader reads for nothing.
    A known-answer circuit cannot be padded (below)."""
    one, many = peak(step, *padded(kind, 1)), peak(step, *padded(kind, N))
    assert one > len(TEXT), f"step {step}: {one} bytes for a file padded by {len(TEXT)}: the file was not read"
    assert many - one < len(TEXT) // 2, f"step {step}: {one} bytes for one padded {kind}, {many} for {N}"


def pad_snapshot(m, key):
    """Every snapshot of the model padded in `key` by TEXT, in a place the form lets hold any text, and the claims drawn from the
    files again."""
    for path in [p for p in m.files if p.startswith("snapshots/")]:
        doc = m.json(path)
        if key == "backend_version":
            doc[key] = TEXT
        elif key == "qubits":
            doc[key][0][0]["name"] = TEXT
        else:
            doc[key][0]["name"] = TEXT
        m.put_json(path, doc)
        m.ents[path].update(p1_calibration.claims(p1_forms.parse_snapshot(m.files[path])))
    return m


@pytest.mark.parametrize("key", ["gates", "general", "general_qlists", "qubits", "backend_version"])
def test_step_8_holds_nothing_of_any_key_of_a_snapshot_by_the_time_it_reads_the_first_job(tmp_path, monkeypatch, key):
    """Round 2's D1 named the class and tested one key. The verifier's mutants 1 to 3 of round 3, step 8 keeping a snapshot's
    `gates`, `general` or `general_qlists` (80 percent of a real file is `gates`), passed every test. Each key of the form is
    padded here, in each of the four snapshots, and what is held when step 8 reads its first raw result is held against the
    same crate unpadded."""
    plain = ibm_model().write(tmp_path / "plain")
    padded_crate = pad_snapshot(ibm_model(), key).write(tmp_path / "padded")
    sizes = [p.stat().st_size for p in padded_crate.glob("snapshots/*.json")]
    small = held_when_the_first_job_is_read(plain, read_md(plain), monkeypatch)
    large = held_when_the_first_job_is_read(padded_crate, read_md(padded_crate), monkeypatch)
    assert len(sizes) == 4 and min(sizes) > len(TEXT), sizes
    assert large - small < len(TEXT) // 2, (key, small, large)


def test_a_known_answer_circuit_cannot_be_padded_so_what_a_step_keeps_of_one_is_held_by_identity_alone(tmp_path):
    """Why no circuit is padded above. A circuit that step 5 accepts is Quantum-Film's: a header, at most sixteen x lines, a
    barrier and sixteen measures, under 800 bytes; one that is not is refused when the first Decode that reads it is visited,
    and the step ends there. So no crate has many large circuits for a step to keep, and the bytes a step keeps of a circuit
    are held by the test of weak references above (the verifier's mutant 9 of round 3 keeps them). What a large circuit
    costs is limit 17's."""
    assert len(ka_qasm(tuple(range(16)))) < 800
    m = many_jobs_model(3, 50, own_known_answers=True)
    m.files["bundle/known-answer.qasm"] = m.files["bundle/known-answer.qasm"] + b"\n" * 1_000_000
    for i in range(3):
        m.edit_json(f"run/job{i:03d}-pub0-known-answer.json",
                    lambda doc: doc["source"].__setitem__("circuit_sha256", sha(m.files["bundle/known-answer.qasm"])))
    r = judge(m, tmp_path / "c", 5)
    assert r is not None and r.name == "known-answer" and r.where.startswith("#decode-job000")
