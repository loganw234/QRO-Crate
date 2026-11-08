"""P1's seven controls (P1's design, item 10) planted in hard-linked copies of the real IBM crate: the faults of
tests/p1/test_p1_controls.py, on the 1,074 files of the real crate (the records, P2's question/law.json and the descriptor), each coming out as section 11 says through the whole
checker. A copy of 52 MB for each plant would be wasteful, so each plant works in a copy whose files are links to the real
crate's; every write of the plants' toolkit unlinks before it writes, and each test checks that the real crate's files, all
1,074 of them, are byte for byte what they were."""
import pytest

import p1crates_support as S
from controls import plants_p1 as plants
from controls import registry
from qro import canonical, checker
from qro.refusal import Refused

SEVEN = sorted(plants.FAULTS)


@pytest.fixture(scope="module")
def real():
    """The real crate, and the digest of each of its files before anything is planted."""
    crate = S.built("ibm")[0]
    return crate, S.digests(crate)


@pytest.fixture
def memo(monkeypatch):
    S.memo_parses(monkeypatch)


@pytest.mark.parametrize("name", SEVEN)
def test_each_control_planted_in_the_real_crate_comes_out_as_section_11_says(real, memo, tmp_path, name):
    crate, before = real
    checker.load()
    copy = plants.link_copy(crate, tmp_path)
    assert S.digests(copy) == before                                        # the copy is the crate
    planted = plants.FAULTS[name](copy)
    try:
        got, refusal = "accepted", None
        checker.check(planted)
    except Refused as r:
        got, refusal = "refused", r.name
    row = registry.CONTROL[name]
    assert (got, refusal) == (row.expected, row.refusal), (name, got, refusal)
    assert S.digests(crate) == before, "a plant wrote through a link into the real crate"


def test_a_forgery_is_another_crate_than_the_one_the_adapter_built_and_that_one_is_untouched(real, memo, tmp_path):
    crate, before = real
    checker.load()
    forged = plants.FAULTS["shot-moved-resealed"](plants.link_copy(crate, tmp_path))
    assert canonical.body_digest(checker.check(forged)) != S.built("ibm")[1]
    assert S.digests(crate) == before


def test_the_forgers_styles_write_each_json_file_of_the_real_crate_byte_for_byte(real):
    """The twin holds no snapshot of Quantum-Film's and no prediction: the styles' claims are held on the real bytes."""
    import json
    crate, _ = real
    seen = {}
    for p in sorted(crate.rglob("*.json")):
        rel = p.relative_to(crate).as_posix()
        if rel != canonical.DESCRIPTOR and not rel.startswith("question/"):     # question/law.json is P2's, in no style of the forger's
            style, data = plants.style_of(rel), p.read_bytes()
            assert plants.STYLES[style](json.loads(data)) == data, rel
            seen[style] = seen.get(style, 0) + 1
    assert set(seen) == {"raw", "snapshot", "record"} and seen["raw"] == 65 and seen["snapshot"] == 5


def test_the_links_are_links_where_the_host_links_and_the_plants_unlink_before_they_write(real, tmp_path):
    import os
    crate, before = real
    copy = plants.link_copy(crate, tmp_path)
    some = next(p for p in sorted(copy.rglob("*.json")) if p.name != canonical.DESCRIPTOR)
    original = crate.joinpath(*some.relative_to(copy).as_posix().split("/"))
    linked = os.stat(some).st_ino == os.stat(original).st_ino
    plants.write_file(copy, some.relative_to(copy).as_posix(), b"changed")
    assert some.read_bytes() == b"changed" and S.digests(crate) == before
    assert linked or os.stat(some).st_ino != os.stat(original).st_ino


# -- limit 21's two classes the real crate holds and the twin cannot (P1.2's third verifier, D1) ------------------------------------------
def resealed(copy, rel, data):
    """`rel` written whole as `data`, its old file unlinked first as every write of the toolkit's is, and only its own digest
    and size resealed in the metadata."""
    plants.write_file(copy, rel, data)
    plants.patch(copy, lambda g: None, reseal=[rel])


def test_a_prediction_file_changed_with_only_its_own_digest_resealed_is_accepted_by_every_step(real, memo, tmp_path):
    """Limit 21: the six prediction files are each held by their digest and size alone; nothing reads them."""
    crate, before = real
    checker.load()
    copy = plants.link_copy(crate, tmp_path)
    predictions = sorted(p.relative_to(copy).as_posix() for p in copy.rglob("prediction-*.json"))
    assert len(predictions) == 6
    rel = predictions[0]
    resealed(copy, rel, S.read(copy, rel) + b"x")
    assert canonical.body_digest(checker.check(copy)) != S.built("ibm")[1]      # accepted, and another crate than the built one
    assert S.digests(crate) == before


def dated(doc):
    """Every object of a snapshot that holds a `date`, at any depth."""
    if isinstance(doc, dict):
        if isinstance(doc.get("date"), str):
            yield doc
        for v in doc.values():
            yield from dated(v)
    elif isinstance(doc, list):
        for v in doc:
            yield from dated(v)


def test_a_date_below_the_newest_in_a_snapshot_of_quantum_films_own_moved_and_resealed_is_accepted_by_every_step(real, memo,
                                                                                                                 tmp_path):
    """Limit 21: in Quantum-Film's own snapshots, which no MANIFEST lists, the claims hold the stamp and the newest date and the
    values-digest leaves every date out, so a date below the newest, moved a second, is held by the file's digest alone."""
    import datetime
    import json
    crate, before = real
    checker.load()
    copy = plants.link_copy(crate, tmp_path)
    rel = "2026-10-05/ibm/ibm_fez/properties-20261005T081622Z.json"
    doc = json.loads(S.read(copy, rel))
    holders = list(dated(doc))
    oldest, newest = min(holders, key=lambda h: h["date"]), max(h["date"] for h in holders)
    spelt = "%Y-%m-%dT%H:%M:%SZ"
    moved = (datetime.datetime.strptime(oldest["date"], spelt) + datetime.timedelta(seconds=1)).strftime(spelt)
    assert oldest["date"] < moved < newest
    oldest["date"] = moved
    resealed(copy, rel, plants.STYLES[plants.style_of(rel)](doc))
    assert S.read(copy, rel) != S.read(crate, rel)
    assert canonical.body_digest(checker.check(copy)) != S.built("ibm")[1]
    assert S.digests(crate) == before


def test_a_snapshot_of_quantum_films_own_taken_out_of_the_real_crate_is_missed_by_everything_and_the_links_stay(real, memo, tmp_path):
    """Limit 4. The read's snapshots are named by the read's records and listed by its MANIFESTs, so the generator refuses a crate
    that lacks one of a device it carries. Quantum-Film's own five (2026-10-05/ibm/<device>/properties-*) are named by no record:
    taken out, the crate regenerates and is accepted, and no job's link moves (each predates the runs)."""
    import json
    crate, before = real
    checker.load()
    gone = "2026-10-05/ibm/ibm_kingston/properties-20261005T065743Z.json"
    copy = plants.link_copy(crate, tmp_path)
    copy.joinpath(*gone.split("/")).unlink()
    plants.rebuild(copy)
    def jobs(root):
        return {e["@id"]: (e["qro:calibrationLink"], e.get("qro:calibration")) for e in S.of_type(
            json.loads(S.read(root, canonical.DESCRIPTOR)), "qro:Job")}
    assert jobs(copy) == jobs(crate)
    assert canonical.body_digest(checker.check(copy)) != S.built("ibm")[1] and S.digests(crate) == before
