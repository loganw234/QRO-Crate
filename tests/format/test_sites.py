"""One planted fault for each check site of round 1's mutation test in the reader, the checker, the custody check
and the spellings: each `if ... raise Refused` and each returned problem (P0's verifier, N1: 34 of its 69 sites
survived their removal). Each plant is one fault in a fresh copy of the fixture crate, or one custody line or
record; each must be refused by the name given. What other faults the suite holds, and which survive, is the
ledger's to say, mutation operator by operator (docs/VALIDATION.md)."""
import hashlib
import json

import pytest

from qro import canonical, checker, custody, fixture, reader
from qro import vocabulary as V
from qro.refusal import Refused

RAW, NOTES = "data/raw.counts.json", "data/notes.txt"


@pytest.fixture(autouse=True)
def registered(monkeypatch):
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    monkeypatch.setattr(checker, "GENERATORS", {})
    monkeypatch.setattr(checker, "COUNTS", [])
    monkeypatch.setattr(checker, "STEPS", {4: None, 5: None, 6: None, 7: None, 8: None})
    fixture.register()


def crate(tmp_path):
    return fixture.make(tmp_path / "crate")


def rewrite(c, f, raw=False):
    p = c / canonical.DESCRIPTOR
    if raw:
        p.write_bytes(f(p.read_bytes()))
        return c
    md = json.loads(p.read_bytes())
    f(md)
    p.write_bytes(canonical.dumps(md))
    return c


def entity(md, i):
    return next(e for e in md["@graph"] if e["@id"] == i)


def add_file(md, e):
    md["@graph"].append(e)
    md["@graph"][2:] = sorted(md["@graph"][2:], key=lambda x: x["@id"])


def action(md, i="#job"):
    add_file(md, {"@id": i, "@type": "CreateAction"})


# -- the reader, site by site ---------------------------------------------------------------------------------
READER = {
    "not JSON": (lambda md: None, lambda b: b[:-2], "spelling"),
    "a third top-level key": (lambda md: md.update({"@extra": "x"}), None, "graph-form"),
    "@graph not a list": (lambda md: md.update({"@graph": {"a": 1}}), None, "graph-form"),
    "@graph of one entity": (lambda md: md.update({"@graph": md["@graph"][:1]}), None, "graph-form"),
    "an entity that is not an object": (lambda md: md["@graph"].append("x"), None, "graph-form"),
    "an entity without @type": (lambda md: md["@graph"][2].pop("@type"), None, "graph-form"),
    "an entity without @id": (lambda md: md["@graph"][2].pop("@id"), None, "graph-form"),
    "an @id with a space": (lambda md: entity(md, NOTES).update({"@id": "data/a b.txt"}), None, "spelling"),
    "an @id that is not a string": (lambda md: entity(md, NOTES).update({"@id": 7}), None, "spelling"),
    "one type in a list": (lambda md: entity(md, NOTES).update({"@type": ["File"]}), None, "spelling"),
    "types unsorted": (lambda md: entity(md, RAW).update({"@type": ["qro:RawResult", "File"]}), None, "spelling"),
    "a type that is not a string": (lambda md: entity(md, NOTES).update({"@type": 7}), None, "spelling"),
    "the root before the descriptor": (lambda md: md.update(
        {"@graph": [md["@graph"][1], md["@graph"][0]] + md["@graph"][2:]}), None, "graph-form"),
    "entities out of @id order": (lambda md: md.update(
        {"@graph": md["@graph"][:2] + list(reversed(md["@graph"][2:]))}), None, "graph-form"),
    "a descriptor with a key more": (lambda md: md["@graph"][0].update(name="x"), None, "graph-form"),
    "a descriptor about another": (lambda md: md["@graph"][0].update(about={"@id": NOTES}), None, "graph-form"),
    "a root that is not a Dataset": (lambda md: md["@graph"][1].update({"@type": "CreativeWork"}), None,
                                     "graph-form"),
    "a root conforming to RO-Crate only": (lambda md: md["@graph"][1].update(
        conformsTo=[{"@id": V.ROCRATE}]), None, "graph-form"),
    "an action the root does not mention": (lambda md: action(md), None, "graph-form"),
    "the root mentioning a non-action": (lambda md: md["@graph"][1].update(mentions=[{"@id": NOTES}]), None,
                                         "graph-form"),
    "a reference to no entity": (lambda md: md["@graph"][1].update(license={"@id": "#nowhere"}), None,
                                 "graph-form"),
    "a type RO-Crate knows and the profile does not": (lambda md: entity(md, NOTES).update(
        {"@type": ["File", "Person"]}), None, "term-unknown"),
    "an empty list": (lambda md: md["@graph"][1].update(hasPart=[]), None, "spelling"),
    "a list-valued term as one value": (lambda md: md["@graph"][1].update(
        hasPart=md["@graph"][1]["hasPart"][0]), None, "spelling"),
    "a list of the wrong spelling": (lambda md: md["@graph"][1].update(hasPart=[NOTES]), None, "spelling"),
    "a list unsorted": (lambda md: md["@graph"][1].update(hasPart=list(reversed(md["@graph"][1]["hasPart"]))),
                        None, "spelling"),
    "a list with a value twice": (lambda md: md["@graph"][1].update(
        hasPart=[md["@graph"][1]["hasPart"][0]] * 2), None, "spelling"),
    "a single-valued term as a list": (lambda md: md["@graph"][1].update(name=["a name"]), None, "spelling"),
    "an absence word a term does not allow": (lambda md: entity(md, RAW).update(sha256="unknown"), None,
                                              "spelling"),
}


@pytest.mark.parametrize("site", sorted(READER))
def test_each_reader_site(tmp_path, site):
    f, raw, name = READER[site]
    c = crate(tmp_path)
    rewrite(c, raw, raw=True) if raw else rewrite(c, f)
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == name, f"{site}: {r.value.name} at {r.value.where}: {r.value.detail}"


def test_an_allowed_absence_word_is_accepted(tmp_path, monkeypatch):
    """The other side of the absence check: a term that allows `unknown` takes it."""
    c = crate(tmp_path)
    rewrite(c, lambda md: md["@graph"][1].update({"qro:signature": "none"}))
    checker.check(c)


def test_a_canonical_dump_that_cannot_finish_is_spelling(tmp_path, monkeypatch):
    data = (fixture.make(tmp_path / "c") / canonical.DESCRIPTOR).read_bytes()     # tmp_path: no directory left

    def deep(_):
        raise RecursionError
    monkeypatch.setattr(canonical, "dumps", deep)
    with pytest.raises(Refused) as r:
        reader.read(data)
    assert r.value.name == "spelling"


# -- the checker, site by site --------------------------------------------------------------------------------
def test_no_metadata_file_is_file_missing(tmp_path):
    c = crate(tmp_path)
    (c / canonical.DESCRIPTOR).unlink()
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == "file-missing"


@pytest.mark.parametrize("key, name", [("sha256", "raw-digest"), ("contentSize", "raw-digest")])
def test_a_raw_result_without_its_digest_or_size(tmp_path, key, name):
    c = rewrite(crate(tmp_path), lambda md: entity(md, RAW).pop(key))
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == name


def test_a_file_without_its_digest_is_file_digest(tmp_path):
    c = rewrite(crate(tmp_path), lambda md: entity(md, NOTES).pop("sha256"))
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == "file-digest"


def test_a_file_no_haspart_reaches_is_file_unlisted(tmp_path):
    c = rewrite(crate(tmp_path), lambda md: md["@graph"][1].update(
        hasPart=[x for x in md["@graph"][1]["hasPart"] if x["@id"] != NOTES]))
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert (r.value.name, r.value.where) == ("file-unlisted", NOTES)


def test_shots_off_a_raw_result_are_refused(tmp_path):
    """qro:shots stands only on a raw result, its domain: a count with no raw bytes beside it is refused at step 1."""
    c = rewrite(crate(tmp_path), lambda md: md["@graph"][1].update({"qro:shots": 8}))
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == "graph-form"


def test_a_raw_result_that_is_not_held_is_graph_form(tmp_path):
    def add(md):
        add_file(md, {"@id": "https://example.org/raw.json", "@type": ["File", "qro:RawResult"],
                      "qro:rawForm": fixture.RAW_FORM})
    c = rewrite(crate(tmp_path), add)
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == "graph-form"


def test_a_raw_result_naming_no_form_is_raw_form(tmp_path):
    c = rewrite(crate(tmp_path), lambda md: entity(md, RAW).pop("qro:rawForm"))
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == "raw-form"


def test_a_reader_counting_no_whole_number_is_raw_form(tmp_path):
    c = crate(tmp_path)
    checker.RAW_FORMS[fixture.RAW_FORM] = lambda b: "8"
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == "raw-form"


def test_a_registered_count_rule_is_run(tmp_path):
    c = crate(tmp_path)

    def rule(crate_dir, md):
        raise Refused("count-unpaid", "#job", "a job's stated shots")
    checker.COUNTS.append(rule)
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert (r.value.name, r.value.where) == ("count-unpaid", "#job")


def test_a_registered_step_is_run_in_place_of_step_unbuilt(tmp_path):
    c = rewrite(crate(tmp_path), lambda md: entity(md, RAW).update({"qro:commitment": "a" * 64}))

    def step4(crate_dir, md):
        raise Refused("commitment", RAW, "the provider echoed another")
    checker.STEPS[4] = step4
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == "commitment"


# -- the custody check, site by site --------------------------------------------------------------------------
LINE = {"at": "2026-10-14T00:00:00Z", "crate": "a" * 64, "event": "received", "from": "withheld",
        "prev": custody.EMPTY}


@pytest.mark.parametrize("data", [b"[1]\n", b'"a line"\n',
                                  canonical.compact(dict(LINE, crate="A" * 64)),
                                  canonical.compact(dict(LINE, at="2026-10-14 00:00:00Z"))],
                         ids=["an array", "a string", "an uppercase digest", "a time out of spelling"])
def test_each_custody_line_site(data):
    with pytest.raises(Refused) as r:
        custody.check_log(data)
    assert r.value.name == "spelling"


def test_a_record_with_stages_unsorted_or_not_canonical_is_spelling():
    rec = dict(auditor="withheld", checker="qro 0.1.0", checkerCommit="unknown", crate="a" * 64, date="2026-10-14",
               independence="producer-build", logHead="none", signature="none", stages=["qpy", "crate-only"],
               trustedTime="none", verdict="accepted")
    with pytest.raises(Refused) as r:
        custody.check_record(canonical.dumps(rec), b"")
    assert r.value.name == "spelling"
    rec["stages"] = ["crate-only"]
    with pytest.raises(Refused) as r:
        custody.check_record(canonical.dumps(rec).replace(b"\n", b"\r\n"), b"")
    assert r.value.name == "spelling"


def test_the_writers_refuse_what_the_check_would():
    with pytest.raises(Refused):
        custody.line(b"", "received", crate="a" * 64, at="not a time", **{"from": "withheld"})
    with pytest.raises(Refused):
        custody.record(crate="a" * 64)


# -- the spellings: every one with an accepted and a refused example ------------------------------------------
def test_a_rationals_terms_are_capped():
    from qro import spelling as S
    assert S.problem("rational", "1/" + "7" * 1000) is None
    assert S.problem("rational", "1/" + "7" * 1001) is not None


def test_text_refuses_control_characters_but_the_line_feed():
    from qro import spelling as S
    assert S.problem("text", "two\nlines") is None
    for bad in ("a\x00b", "a\tb", "a\x7fb", "a\ud800b"):
        assert S.problem("text", bad) is not None, repr(bad)


def test_the_raw_counts_digest_in_the_twin():
    data = canonical.compact({"00": 3, "01": 1, "11": 4})
    assert hashlib.sha256(data).hexdigest() == "5721802cb700ccbf26384808669e4be1ea6fcaaa23acdf602f7d1fb87a7fb73e"
