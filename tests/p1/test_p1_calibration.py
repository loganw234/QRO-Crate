"""A calibration's identity and a job's link to one. The values-digest is held to the 2026-10-14 read's own
snapshots, which this repository carries in records/2026-10-14/ibm-refetch: seven of IBM's backend-properties texts,
whose digests fall in five classes exactly as study QRO-0's section 4.5 has them (the other five of the twelve are
Quantum-Film's and not in this repository; P1's crates stage holds all twelve). The literals below were computed by
a script that imports nothing of this package. The recipe is also written out by hand on a snapshot small enough to
read, and each way it could be wrong is a mutant here: a date kept, a number written as its text, a list sorted.
The link rule is held at every boundary of its two strict inequalities."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from p1_builder import at, snapshot_bytes, snapshot_doc

from qro import p1_calibration as cal
from qro import p1_forms

ROOT = Path(__file__).resolve().parents[2]
READ = ROOT / "records" / "2026-10-14" / "ibm-refetch"
REAL = {  # device, stamp -> the values-digest, computed independently of this package
    ("ibm_kingston", "20261005T090246Z"): "e96fd7d158270ae82c62aa22d2fc1020269ca266591f191eafb808cc5c5fc395",
    ("ibm_kingston", "20261005T112827Z"): "3b601e0caa583185871c2965c6a31fb8747b3d19154c26a31b92d7a78f23fc51",
    ("ibm_kingston", "20261005T122118Z"): "bfe4f0e88e22e327ed2ea76bfcb76866042c490242052b48b724033ac9ad6413",
    ("ibm_marrakesh", "20261005T095118Z"): "e670973633931a26246e715e890ac1c6314a61c31278748937ea9e848c1f0cd0",
    ("ibm_marrakesh", "20261005T112128Z"): "e670973633931a26246e715e890ac1c6314a61c31278748937ea9e848c1f0cd0",
    ("ibm_fez", "20261005T100831Z"): "d208cb2bff06dc14b779318913b144e3c9d2d3072ddfb9e7d789fe9bc5da759b",
    ("ibm_fez", "20261005T114447Z"): "d208cb2bff06dc14b779318913b144e3c9d2d3072ddfb9e7d789fe9bc5da759b",
}


def real(device, stamp):
    return p1_forms.parse_snapshot((READ / device / f"properties-{stamp}.json").read_bytes())


@pytest.fixture(scope="module")
def reals():
    return {k: real(*k) for k in REAL}


def test_the_read_snapshots_have_the_digests_computed_independently(reals):
    assert {k: cal.values_digest(s) for k, s in reals.items()} == REAL


def test_two_calibrations_with_equal_values_are_equal_whatever_their_stamps_and_dates(reals):
    """Marrakesh and fez: two stamps each, 2.2 hours and 1.6 hours apart, thousands of values re-dated, one digest."""
    for a, b in ((("ibm_marrakesh", "20261005T095118Z"), ("ibm_marrakesh", "20261005T112128Z")),
                 (("ibm_fez", "20261005T100831Z"), ("ibm_fez", "20261005T114447Z"))):
        x, y = reals[a], reals[b]
        assert x.stamp != y.stamp and x.newest != y.newest
        assert cal.values_digest(x) == cal.values_digest(y)


def test_kingstons_three_calibrations_differ(reals):
    ds = {cal.values_digest(reals[("ibm_kingston", s)]) for s in ("20261005T090246Z", "20261005T112827Z",
                                                                   "20261005T122118Z")}
    assert len(ds) == 3


def keeping_dates(snapshot):
    """The recipe with its one change that matters undone: every date left in (the stamp too)."""
    def spell(x):
        if type(x) in (int, float):
            return {"n": x.hex() if isinstance(x, float) else float(x).hex()}
        if isinstance(x, dict):
            return {k: spell(v) for k, v in x.items()}
        if isinstance(x, list):
            return [spell(v) for v in x]
        return x
    text = json.dumps(spell(snapshot.doc), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def test_the_control_of_the_control_keeping_the_dates_would_tell_the_equal_pairs_apart(reals):
    """So the equality above is the recipe's doing, not an accident of two files that happen to match."""
    for a, b in ((("ibm_marrakesh", "20261005T095118Z"), ("ibm_marrakesh", "20261005T112128Z")),
                 (("ibm_fez", "20261005T100831Z"), ("ibm_fez", "20261005T114447Z"))):
        assert keeping_dates(reals[a]) != keeping_dates(reals[b])


def test_the_real_stamps_and_newest_dates_are_what_the_file_names_and_the_study_have(reals):
    for (device, stamp), s in reals.items():
        assert s.device == device and s.stamp.strftime("%Y%m%dT%H%M%SZ") == stamp
    k = reals[("ibm_kingston", "20261005T122118Z")]
    assert (k.stamp, k.newest) == (at(12, 21, 18), at(12, 24, 6, 734584))      # study section 4.5: about 3 minutes later


# -- the recipe, written out by hand --------------------------------------------------------------------------------
TINY = {"backend_name": "b", "backend_version": "v", "last_update_date": "2026-10-05T09:02:46Z",
        "gates": [], "general_qlists": [], "qubits": [],
        "general": [{"date": "2026-10-05T09:00:00Z", "name": "n", "unit": "u", "value": 1}]}
PREIMAGE = ('{"backend_name":"b","backend_version":"v","gates":[],"general":[{"name":"n","unit":"u","value":'
            '{"n":"3ff0000000000000"}}],"general_qlists":[],"qubits":[]}')


def tiny_digest(doc):
    return cal.values_digest(p1_forms.parse_snapshot(json.dumps(doc).encode()))


def test_the_preimage_is_the_values_alone_in_sorted_compact_ascii_json_with_numbers_as_their_bits():
    assert tiny_digest(TINY) == hashlib.sha256(PREIMAGE.encode("ascii")).hexdigest()


def test_non_ascii_text_digests_as_its_escape_whichever_way_the_file_spells_it():
    """The verifier's note. The preimage is ASCII (json.dumps escapes what is not): a unit of micro-seconds digests the
    same whether the file writes the escape or the character, and the digest is the recipe's, written out by hand."""
    micro, backslash = chr(0xB5), chr(92)
    doc = variant(general__0__unit=micro + "s")
    escaped = json.dumps(doc).encode("utf-8")
    spelt = json.dumps(doc, ensure_ascii=False).encode("utf-8")
    assert (backslash + "u00b5").encode() in escaped and micro.encode("utf-8") in spelt and spelt != escaped
    want = hashlib.sha256(PREIMAGE.replace('"unit":"u"', '"unit":"' + backslash + 'u00b5s"').encode("ascii")).hexdigest()
    assert cal.values_digest(p1_forms.parse_snapshot(escaped)) == cal.values_digest(p1_forms.parse_snapshot(spelt)) == want
    assert want != tiny_digest(TINY)


def test_the_digest_is_the_sha256_in_lowercase_hex():
    d = tiny_digest(TINY)
    assert len(d) == 64 and d == d.lower() and set(d) <= set("0123456789abcdef")


def variant(**changes):
    doc = json.loads(json.dumps(TINY))
    for path, value in changes.items():
        target = doc
        *route, last = path.split("__")
        for step in route:
            target = target[int(step)] if step.isdigit() else target[step]
        target[int(last) if last.isdigit() else last] = value
    return doc


def test_a_value_moves_the_digest_and_a_date_does_not():
    base = tiny_digest(TINY)
    assert tiny_digest(variant(general__0__value=2)) != base
    assert tiny_digest(variant(general__0__value=1.0000000000000002)) != base         # one ulp
    assert tiny_digest(variant(general__0__date="2026-10-05T10:00:00Z")) == base
    assert tiny_digest(variant(general__0__date="2026-10-05T10:00:00.5Z")) == base
    assert tiny_digest(variant(last_update_date="2026-10-05T23:59:59Z")) == base


def test_an_integer_and_the_equal_float_are_one_value_and_negative_zero_is_not_zero():
    one, zero = variant(general__0__value=1.0), variant(general__0__value=0)
    assert tiny_digest(one) == tiny_digest(TINY)
    assert tiny_digest(variant(general__0__value=0.0)) == tiny_digest(zero)
    assert tiny_digest(variant(general__0__value=-0.0)) != tiny_digest(zero)
    assert tiny_digest(variant(general__0__value=2**60)) == tiny_digest(variant(general__0__value=float(2**60)))


def test_a_number_is_its_bits_not_its_text():
    """1.0000000000000002 and 1.0000000000000004 are two floats; 0.1 + 0.2 is not 0.3: the bits tell them apart."""
    assert tiny_digest(variant(general__0__value=0.1 + 0.2)) != tiny_digest(variant(general__0__value=0.3))
    assert tiny_digest(variant(general__0__value=1e-7)) == tiny_digest(variant(general__0__value=0.0000001))


def test_every_string_of_the_values_moves_the_digest():
    base = tiny_digest(TINY)
    for change in (variant(backend_name="c"), variant(backend_version="w"), variant(general__0__name="m"),
                   variant(general__0__unit="v")):
        assert tiny_digest(change) != base


def test_list_order_is_part_of_the_digest():
    a = snapshot_doc(at(9, 2, 46), at(9, 2, 30))
    b = json.loads(json.dumps(a))
    b["qubits"].reverse()
    assert tiny_digest(a) != tiny_digest(b)
    c = json.loads(json.dumps(a))
    c["gates"].reverse()
    assert tiny_digest(a) != tiny_digest(c)
    d = json.loads(json.dumps(a))
    d["gates"][0]["qubits"].reverse()
    assert tiny_digest(a) != tiny_digest(d)


def test_the_stamp_and_the_dates_inside_can_all_move_and_the_digest_not():
    a = snapshot_doc(at(9, 2, 46), at(9, 2, 30), seed=3)
    b = snapshot_doc(at(23, 0, 0), at(22, 40, 0), seed=3)
    assert a != b and tiny_digest(a) == tiny_digest(b)
    assert tiny_digest(snapshot_doc(at(9, 2, 46), at(9, 2, 30), seed=4)) != tiny_digest(a)


def test_a_snapshot_of_another_device_is_another_calibration():
    assert tiny_digest(snapshot_doc(at(9, 2, 46), at(9, 2, 30), device="ibm_other")) != tiny_digest(
        snapshot_doc(at(9, 2, 46), at(9, 2, 30)))


def test_the_claims_are_the_three_checked_terms_spelt_as_the_profile_does():
    s = p1_forms.parse_snapshot(snapshot_bytes(snapshot_doc(at(12, 21, 18), at(12, 24, 6, 730000), seed=2)))
    got = cal.claims(s)
    assert got == {"qro:valuesDigest": cal.values_digest(s), "qro:stamp": "2026-10-05T12:21:18Z",
                   "qro:newestValue": "2026-10-05T12:24:06.73Z"}
    whole = p1_forms.parse_snapshot(snapshot_bytes(snapshot_doc(at(12, 21, 18, 500000), at(12, 24, 6))))
    assert cal.claims(whole)["qro:stamp"] == "2026-10-05T12:21:18.5Z"


# -- the link rule ----------------------------------------------------------------------------------------------------------
def snap(stamp, newest):
    return SimpleNamespace(stamp=stamp, newest=newest)


S = at(12, 26, 17, 34663)                                  # a first shot


def carried(**snaps):
    return dict(snaps)


def test_a_snapshot_valid_for_a_shot_is_entirely_before_it():
    assert cal.valid_for(snap(at(12, 21, 18), at(12, 21, 0)), S)
    assert not cal.valid_for(snap(S, at(12, 21, 0)), S)                          # stamped at the shot
    assert not cal.valid_for(snap(at(12, 21, 18), S), S)                         # last measured at the shot
    assert not cal.valid_for(snap(at(12, 26, 17, 34664), at(12, 21, 0)), S)      # one microsecond after
    assert not cal.valid_for(snap(at(12, 21, 18), at(12, 26, 17, 34664)), S)
    assert cal.valid_for(snap(at(12, 26, 17, 34662), at(12, 26, 17, 34662)), S)  # one microsecond before


def test_with_no_newer_valid_snapshot_the_link_is_at_the_first_shot():
    c = snap(at(11, 28, 27), at(11, 25, 0))
    assert cal.link_for(S, "c", carried(c=c)) == ("history-at-first-shot", ("c",))
    old = snap(at(9, 2, 46), at(9, 2, 30))
    assert cal.link_for(S, "c", carried(c=c, old=old)) == ("history-at-first-shot", ("c",))


def test_a_newer_snapshot_stamped_and_measured_before_the_shot_makes_the_link_in_gap():
    c, d = snap(at(11, 28, 27), at(11, 25, 0)), snap(at(12, 21, 18), at(12, 24, 6, 730000))
    assert cal.link_for(S, "c", carried(c=c, d=d)) == ("history-in-gap", ("c", "d"))


def test_a_snapshot_stamped_before_the_shot_but_still_being_measured_is_no_gap():
    """The study's sheet-01 job: first shot 12:22:00.162, a snapshot stamped 12:21:18 with a value dated 12:24:06.73."""
    early = at(12, 22, 0, 162000)
    c, d = snap(at(11, 28, 27), at(11, 25, 0)), snap(at(12, 21, 18), at(12, 24, 6, 730000))
    assert cal.link_for(early, "c", carried(c=c, d=d)) == ("history-at-first-shot", ("c",))
    with pytest.raises(cal.LinkError):
        cal.link_for(early, "d", carried(c=c, d=d))


@pytest.mark.parametrize("name, stamp, newest, gap", [
    ("stamped after the shot", at(12, 26, 17, 34664), at(12, 20, 0), False),
    ("stamped at the shot", S, at(12, 20, 0), False),
    ("stamped a microsecond before", at(12, 26, 17, 34662), at(12, 20, 0), True),
    ("measured at the shot", at(12, 21, 18), S, False),
    ("measured a microsecond before", at(12, 21, 18), at(12, 26, 17, 34662), True),
    ("measured after the shot", at(12, 21, 18), at(12, 27, 0), False),
    ("stamped with C's own stamp", at(11, 28, 27), at(11, 26, 0), False),
    ("stamped a microsecond after C's", at(11, 28, 27, 1), at(11, 26, 0), True),
    ("stamped before C's", at(10, 0, 0), at(9, 59, 0), False)])
def test_a_second_snapshot_is_a_gap_only_inside_both_strict_bounds(name, stamp, newest, gap):
    c, d = snap(at(11, 28, 27), at(11, 25, 0)), snap(stamp, newest)
    want = ("history-in-gap", ("c", "d")) if gap else ("history-at-first-shot", ("c",))
    assert cal.link_for(S, "c", carried(c=c, d=d)) == want


@pytest.mark.parametrize("stamp, newest", [(S, at(11, 0, 0)), (at(11, 28, 27), S), (S, S),
                                           (at(12, 30, 0), at(11, 0, 0)), (at(11, 28, 27), at(12, 30, 0))])
def test_a_history_snapshot_not_entirely_before_the_shot_is_not_a_link(stamp, newest):
    with pytest.raises(cal.LinkError, match="not entirely before the first shot"):
        cal.link_for(S, "c", carried(c=snap(stamp, newest)))


def test_the_newest_stamped_valid_snapshot_is_the_gap_and_a_tie_goes_to_the_greater_id():
    c = snap(at(9, 0, 0), at(8, 59, 0))
    d1, d2, d3 = (snap(at(11, 0, 0), at(10, 59, 0)), snap(at(12, 0, 0), at(11, 59, 0)),
                  snap(at(12, 25, 0), at(12, 30, 0)))                            # d3 is not valid for the shot
    assert cal.link_for(S, "c", carried(c=c, d1=d1, d2=d2, d3=d3)) == ("history-in-gap", ("c", "d2"))
    e1, e2 = snap(at(12, 0, 0), at(11, 59, 0)), snap(at(12, 0, 0), at(11, 58, 0))
    assert cal.link_for(S, "c", carried(c=c, e1=e1, e2=e2)) == ("history-in-gap", ("c", "e2"))


def test_a_history_snapshot_the_crate_does_not_carry_is_not_a_link():
    with pytest.raises(cal.LinkError, match="not a snapshot the crate carries"):
        cal.link_for(S, "missing", carried(c=snap(at(9, 0, 0), at(8, 0, 0))))


def test_a_snapshot_stamped_before_the_history_one_is_never_the_gap():
    c, old = snap(at(11, 28, 27), at(11, 25, 0)), snap(at(9, 2, 46), at(9, 2, 30))
    assert cal.link_for(S, "c", carried(old=old, c=c)) == ("history-at-first-shot", ("c",))
    assert cal.link_for(S, "old", carried(old=old, c=c)) == ("history-in-gap", ("old", "c"))
