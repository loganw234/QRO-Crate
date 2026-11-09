"""The declaration, `qro-comparison/1` (qro/p3_declaration.py; P3's design, items 1 and 2): its one spelling, a hostile
matrix of declarations each refused for what is wrong and nothing escaping the reader, the plan's digest, which leaves
the pool out, and what this version does not build, refused `step-unbuilt`."""
import copy
import hashlib
import json
from fractions import Fraction

import pytest

from qro import canonical
from qro import p3_declaration as D
from qro.refusal import Refused

DIGEST_A, DIGEST_B = "a" * 64, "b" * 64
SELECTOR = {"device": "ibm_kingston"}


def plan(**kw):
    out = D.plan({"n-crystal-share": "0/1", "x0x1": "1/20"}, {"a": dict(SELECTOR), "b": {"device": "ibm_fez"}})
    out.update(kw)
    return out


def doc(**kw):
    out = {"crates": {"a": [DIGEST_A], "b": [DIGEST_B]}, "format": D.FORMAT, "plan": plan(), "preregistration": "none"}
    out.update(kw)
    return out


def data(d):
    return canonical.dumps(d)


def test_a_declaration_written_is_read_back_whole():
    d = D.read(D.write({"a": [DIGEST_A], "b": [DIGEST_B]}, plan(), "comparison/preregistration/plan.md"))
    assert d.crates == {"a": (DIGEST_A,), "b": (DIGEST_B,)}
    assert d.preregistration == "comparison/preregistration/plan.md"
    assert d.plan.alpha == Fraction(1, 20) and d.plan.kind == "real" and d.plan.question == "fixed"
    assert [(m.measure, m.distance, m.epsilon) for m in d.plan.measures] == [
        ("n-crystal-share", "abs-mean", Fraction(0)), ("x0x1", "abs-mean", Fraction(1, 20))]
    assert d.plan.runs["a"] == D.Selector("ibm_kingston", None, None, None, None)
    assert d.digest == hashlib.sha256(D.write({"a": [DIGEST_A], "b": [DIGEST_B]}, plan(),
                                              "comparison/preregistration/plan.md")).hexdigest()


def test_the_plan_digest_is_the_plans_canonical_compact_json_and_leaves_the_pool_out():
    p = plan()
    one = D.read(data(doc(plan=p)))
    other = D.read(data(doc(plan=p, crates={"a": [DIGEST_B], "b": [DIGEST_A, DIGEST_B]})))
    assert one.plan.digest == other.plan.digest == hashlib.sha256(canonical.compact(p)).hexdigest()
    assert one.digest != other.digest
    moved = D.read(data(doc(plan=plan(alpha="1/10"))))
    assert moved.plan.digest != one.plan.digest


def selector(**kw):
    return {"runs": {"a": {**SELECTOR, **kw}, "b": {"device": "ibm_fez"}}}


def edited(path, value):
    """The document with the value at `path` (keys) replaced, or deleted where value is DELETE."""
    d = doc()
    x = d
    for k in path[:-1]:
        x = x[k]
    if value is DELETE:
        del x[path[-1]]
    else:
        x[path[-1]] = value
    return d


DELETE = object()
HOSTILE = [
    ("a top-level key missing", edited(("preregistration",), DELETE)),
    ("an extra top-level key", {**doc(), "extra": "x"}),
    ("another format", doc(format="qro-comparison/2")),
    ("crates without b", doc(crates={"a": [DIGEST_A]})),
    ("crates with a third run", doc(crates={"a": [DIGEST_A], "b": [DIGEST_B], "c": [DIGEST_A]})),
    ("an empty pool", doc(crates={"a": [], "b": [DIGEST_B]})),
    ("a pool that is no list", doc(crates={"a": DIGEST_A, "b": [DIGEST_B]})),
    ("a pool unsorted", doc(crates={"a": [DIGEST_B, DIGEST_A], "b": [DIGEST_B]})),
    ("a pool with a digest twice", doc(crates={"a": [DIGEST_A, DIGEST_A], "b": [DIGEST_B]})),
    ("a digest in upper case", doc(crates={"a": [DIGEST_A.upper()], "b": [DIGEST_B]})),
    ("a digest one short", doc(crates={"a": [DIGEST_A[:-1]], "b": [DIGEST_B]})),
    ("a plan key missing", edited(("plan", "sampling"), DELETE)),
    ("an extra plan key", doc(plan={**plan(), "extra": "x"})),
    ("alpha 0", doc(plan=plan(alpha="0/1"))),
    ("alpha 1", doc(plan=plan(alpha="1/1"))),
    ("alpha past 1", doc(plan=plan(alpha="3/2"))),
    ("alpha negative", doc(plan=plan(alpha="-1/20"))),
    ("alpha not in lowest terms", doc(plan=plan(alpha="2/40"))),
    ("alpha a float", doc(plan=plan(alpha=0.05))),
    ("alpha a decimal string", doc(plan=plan(alpha="0.05"))),
    ("a granularity that is no word", doc(plan=plan(granularity="pass"))),
    ("a kind that is no word", doc(plan=plan(kind="dry-run"))),
    ("a question neither fixed nor varied", doc(plan=plan(question="free"))),
    ("a family that is no text", doc(plan=plan(family=""))),
    ("an inequality with space at an end", doc(plan=plan(inequality="qro-hoeffding-kl/1 "))),
    ("a measure set that is no string", doc(plan=plan(measureSet=1))),
    ("a sampling model that is no text", doc(plan=plan(sampling=["x"]))),
    ("no measure", doc(plan=plan(measures=[]))),
    ("measures that are no list", doc(plan=plan(measures={"measure": "x0x1"}))),
    ("a measure that is no word", doc(plan=plan(measures=[{"distance": "abs-mean", "epsilon": "0/1",
                                                           "measure": "x2x3"}]))),
    ("a measure with a key missing", doc(plan=plan(measures=[{"distance": "abs-mean", "measure": "x0x1"}]))),
    ("a measure with an extra key", doc(plan=plan(measures=[{"distance": "abs-mean", "epsilon": "0/1",
                                                             "measure": "x0x1", "twin": "uniform"}]))),
    ("an epsilon below zero", doc(plan=plan(measures=[{"distance": "abs-mean", "epsilon": "-1/20",
                                                       "measure": "x0x1"}]))),
    ("an epsilon that is a number", doc(plan=plan(measures=[{"distance": "abs-mean", "epsilon": 0,
                                                             "measure": "x0x1"}]))),
    ("measures unsorted", doc(plan=plan(measures=list(reversed(plan()["measures"]))))),
    ("a measure twice", doc(plan=plan(measures=[plan()["measures"][1]] * 2))),
    ("runs without b", doc(plan=plan(runs={"a": SELECTOR}))),
    ("a selector with no device", doc(plan=plan(**selector(device=None)))),
    ("a selector that is no object", doc(plan=plan(runs={"a": "ibm_kingston", "b": {"device": "ibm_fez"}}))),
    ("a selector key the form has not", doc(plan=plan(**selector(role="law")))),
    ("a device that is no text", doc(plan=plan(**selector(device="")))),
    ("bundles empty", doc(plan=plan(**selector(bundles=[])))),
    ("bundles that are no digests", doc(plan=plan(**selector(bundles=["morning"])))),
    ("bundles unsorted", doc(plan=plan(**selector(bundles=[DIGEST_B, DIGEST_A])))),
    ("jobs that are no text", doc(plan=plan(**selector(jobs=[7])))),
    ("jobs twice", doc(plan=plan(**selector(jobs=["j", "j"])))),
    ("a from that is no time", doc(plan=plan(**selector(**{"from": "2026-11-01"})))),
    ("a from with seven digits of fraction", doc(plan=plan(**selector(**{"from": "2026-11-01T10:00:00.1234567Z"})))),
    ("a leap second", doc(plan=plan(**selector(until="2026-12-31T23:59:60Z")))),
    ("from not before until", doc(plan=plan(**selector(**{"from": "2026-11-01T10:00:00Z",
                                                          "until": "2026-11-01T10:00:00Z"})))),
    ("a pre-registration outside its directory", doc(preregistration="comparison/plan.md")),
    ("a pre-registration with two segments", doc(preregistration="comparison/preregistration/a/b.md")),
    ("a pre-registration named for nothing", doc(preregistration="comparison/preregistration/")),
    ("a pre-registration with a space", doc(preregistration="comparison/preregistration/my plan.md")),
    ("a pre-registration that is a device's name", doc(preregistration="comparison/preregistration/nul.txt")),
    ("a pre-registration that is no string", doc(preregistration=None)),
    ("a pre-registration of none in another case", doc(preregistration="None")),
]


@pytest.mark.parametrize("d", [d for _, d in HOSTILE], ids=[n for n, _ in HOSTILE])
def test_a_declaration_out_of_its_form_is_refused_and_nothing_escapes(d):
    with pytest.raises(D.DeclarationError):
        D.read(data(d))


def test_each_hostile_declaration_differs_from_the_good_one_and_the_good_one_reads():
    """The matrix's control: the declaration every plant edits is read, and each plant is a change of it."""
    D.read(data(doc()))
    for name, d in HOSTILE:
        assert data(d) != data(doc()), name


@pytest.mark.parametrize("raw", [
    b"", b"{", b"not json", b"\xff\xfe", data(doc()).replace(b"\n", b"\r\n"), data(doc())[:-1],
    data(doc()) + b"\n", json.dumps(doc(), sort_keys=True).encode("ascii"),
    json.dumps(dict(reversed(list(doc().items()))), indent=2).encode("ascii") + b"\n",
    data(doc()).replace(b'"format"', b'"format": "qro-comparison/1", "format"', 1),
    b'{"crates": NaN}\n', b"[]\n", b'"x"\n', b"1" * 5000, b"[" * 100000 + b"]" * 100000],
    ids=["empty", "truncated", "no JSON", "not UTF-8", "CRLF", "no final LF", "two final LFs", "compact",
         "keys unsorted", "a key twice", "NaN", "a list", "a string", "a huge integer", "nested past the reader"])
def test_bytes_that_are_not_the_one_spelling_are_refused(raw):
    with pytest.raises(D.DeclarationError):
        D.read(raw)


def test_the_reader_takes_bytes_only():
    with pytest.raises(D.DeclarationError):
        D.read(data(doc()).decode("ascii"))


@pytest.mark.parametrize("key, value", [("bundles", [DIGEST_A]), ("jobs", ["j1", "j2"]),
                                        ("from", "2026-11-01T10:00:00Z"), ("until", "2026-11-01T10:00:00.5Z")])
def test_each_selector_key_is_read(key, value):
    s = D.read(data(doc(plan=plan(**selector(**{key: value}))))).plan.runs["a"]
    assert s.device == "ibm_kingston"
    got = {"bundles": s.bundles, "jobs": s.jobs, "from": s.start, "until": s.until}[key]
    assert got is not None


def test_write_refuses_what_read_refuses():
    with pytest.raises(D.DeclarationError):
        D.write({"a": [DIGEST_A], "b": [DIGEST_B]}, plan(alpha="0/1"))


# -- what is not built ----------------------------------------------------------------------------------------------
UNBUILT = [
    ("plan family", doc(plan=plan(family="qro-family/2"))),
    ("plan granularity", doc(plan=plan(granularity="crate"))),
    ("plan inequality", doc(plan=plan(inequality="agrawal-radius/1"))),
    ("plan measureSet", doc(plan=plan(measureSet="qro-measures/2"))),
    ("plan measures n-crystal-share distance", doc(plan=plan(measures=[{"distance": "hellinger", "epsilon": "0/1",
                                                                         "measure": "n-crystal-share"}]))),
    ("plan measures tvd", doc(plan=plan(measures=[{"distance": "abs-mean", "epsilon": "0/1", "measure": "tvd"}]))),
    ("plan sampling", doc(plan=plan(sampling="independent-shots"))),
    ("crates a", doc(crates={"a": [DIGEST_A, DIGEST_B], "b": [DIGEST_B]})),
    ("crates b", doc(crates={"a": [DIGEST_A], "b": [DIGEST_A, DIGEST_B]})),
]


@pytest.mark.parametrize("where, d", UNBUILT, ids=[w for w, _ in UNBUILT])
def test_what_this_version_does_not_build_is_read_and_refused_step_unbuilt_by_name(where, d):
    declaration = D.read(data(d))
    with pytest.raises(Refused) as r:
        D.unbuilt(declaration)
    assert (r.value.name, r.value.where) == ("step-unbuilt", where)


def test_what_this_version_builds_passes_unbuilt():
    assert D.unbuilt(D.read(data(doc()))) is None


def test_the_computation_refuses_what_is_not_built_before_it_reads_any_crate():
    from qro import p3_compare
    for where, d in UNBUILT:
        with pytest.raises(Refused) as r:
            p3_compare.compute(D.read(data(d)), None, {})
        assert (r.value.name, r.value.where) == ("step-unbuilt", where)


def test_the_first_unbuilt_thing_in_the_plans_key_order_is_the_one_refused():
    d = doc(plan=plan(sampling="x", family="y"), crates={"a": [DIGEST_A, DIGEST_B], "b": [DIGEST_B]})
    with pytest.raises(Refused) as r:
        D.unbuilt(D.read(data(d)))
    assert r.value.where == "plan family"


def test_a_selector_selects_by_every_key_it_gives():
    from qro.p1_forms import parse_time
    t = parse_time("2026-11-01T10:00:00Z")
    s = D.Selector("dev", ("b1",), ("j1",), parse_time("2026-11-01T09:00:00Z"), parse_time("2026-11-01T10:00:00Z"))
    assert not s.selects("dev", "b1", "j1", t), "until is outside the window"
    assert s.selects("dev", "b1", "j1", parse_time("2026-11-01T09:59:59.999999Z"))
    assert s.selects("dev", "b1", "j1", parse_time("2026-11-01T09:00:00Z")), "from is inside the window"
    for args in (("dev2", "b1", "j1"), ("dev", "b2", "j1"), ("dev", "b1", "j2"), ("dev", None, "j1")):
        assert not s.selects(*args, parse_time("2026-11-01T09:30:00Z")), args
    assert not s.selects("dev", "b1", "j1", None), "a job with no time is in no window"
    assert D.Selector("dev", None, None, None, None).selects("dev", None, None, None), "no window: time is not asked"


def test_the_hostile_matrix_is_held_whole():
    """Each plant of the matrix is its own document, so a plant cannot leak into the next."""
    assert len({json.dumps(d, sort_keys=True) for _, d in HOSTILE}) == len(HOSTILE)
    assert copy.deepcopy(doc()) == doc()
