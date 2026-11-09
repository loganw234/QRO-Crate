"""The comparison check (qro/p3_compare.py's `check`; P3's design, item 7; FORMAT.md item 23), in process, on comparison
crates `make` writes of the builder's crates, whose own step 9 a stand-in holds (p3_support.builder_generator): the
ACCEPTED line; the carried record held byte for byte, refused `comparison-generated` at its first differing line and
column; the comparison crate's generator, which reads only the comparison crate's files and never the record's content;
and the misuse that is P3's: the comparison's own directory given again as a crate directory however it is spelt, a
directory that holds no comparison, a crate the declaration does not name, one it names that is not given, and two of
one identity; each crate's refusal at "crate <n>: <where>", and the comparison crate's own at its place, first."""
import hashlib
import json
import os
import shutil

import pytest

import p3_builder as B
import p3_support as S
from qro import canonical, checker, p3_compare, p3_record
from qro.refusal import Refused

T = "2026-11-01T10:"


@pytest.fixture(autouse=True)
def stand_in(monkeypatch):
    S.builder_generator(monkeypatch)
    S.fast_checks(monkeypatch)


@pytest.fixture(scope="module")
def crate(tmp_path_factory):
    d = tmp_path_factory.mktemp("compare")
    k = [B.ka(start=f"{T}00:00Z"), B.law("law-0", start=f"{T}01:00Z"), B.law("law-1", start=f"{T}03:00Z", five=40),
         B.coherence(start=f"{T}40:00Z")]
    f = [B.ka(start=f"{T}00:30Z"), B.law("law-0", start=f"{T}02:00Z", five=30), B.law("law-1", start=f"{T}04:00Z"),
         B.coherence(start=f"{T}41:00Z", agree=20)]
    return B.build(d, [B.Bundle("ibm_kingston", "morning", k), B.Bundle("ibm_fez", "morning", f)])


def made(tmp_path, crate, name="comparison", **kw):
    data, _ = S.declare(crate, crate, **kw)
    out = tmp_path / name
    p3_compare.make(data, out, [crate])
    return out


def test_a_made_comparison_is_accepted_with_its_one_line(tmp_path, crate):
    out = made(tmp_path, crate)
    summary = p3_compare.check(out, [crate])
    identity = canonical.body_digest(S.md_of(out))
    assert str(summary) == f"ACCEPTED comparison {identity}: declared real; exploratory (selector-late); 5 measures"


def test_the_line_says_a_rehearsal_and_the_measures_refused(tmp_path):
    crate = B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", [B.ka(), B.law()]),
                               B.Bundle("ibm_fez", "morning", [B.ka(), B.law()])])
    out = made(tmp_path, crate, kind="rehearsal")
    assert str(p3_compare.check(out, [crate])).endswith(
        ": a rehearsal, never cited as a result; exploratory (selector-late); 5 measures, 2 refused role-missing")


def test_a_pre_registration_holding_the_plans_digest_is_said_pre_registered(tmp_path, crate):
    data, decl = S.declare(crate, crate, preregistration="comparison/preregistration/plan.md")
    prereg = f"# The plan\n\nIts digest: {decl.plan.digest}\n".encode("ascii")
    out = tmp_path / "comparison"
    p3_compare.make(data, out, [crate], preregistration=prereg)
    assert (out / "comparison" / "preregistration" / "plan.md").read_bytes() == prereg
    assert "; pre-registered; " in str(p3_compare.check(out, [crate]))
    assert json.loads((out / "comparison" / "record.json").read_bytes())["late"] == "none"


def tampered(out, edit):
    """The record edited as JSON and the comparison crate's metadata regenerated, its header kept: the nine steps
    accept it, and only the comparison check can tell."""
    record = json.loads((out / "comparison" / "record.json").read_bytes())
    edit(record)
    (out / "comparison" / "record.json").write_bytes(p3_record.dumps(record))
    return regenerate(out)


def regenerate(out):
    old = S.md_of(out)["@graph"][1]
    md = p3_record.generate(out)
    md["@graph"][1].update({k: old[k] for k in ("datePublished", "qro:writer", "qro:writtenAt")})
    (out / canonical.DESCRIPTOR).write_bytes(canonical.write(md))
    return out


def refused(out, crates):
    with pytest.raises(Refused) as r:
        p3_compare.check(out, crates)
    return r.value


def test_a_record_that_is_not_the_computed_one_is_refused_at_its_first_differing_line(tmp_path, crate):
    out = made(tmp_path, crate)
    want = (out / "comparison" / "record.json").read_bytes()
    tampered(out, lambda r: r["measures"][2].update(means="agree"))
    have = (out / "comparison" / "record.json").read_bytes()
    checker.check(out)                                  # the nine steps accept it
    r = refused(out, [crate])
    assert (r.name, r.where) == ("comparison-generated",
                                 f"comparison/record.json {canonical.first_difference(have, want)}")
    assert "verdicts are computed only on the runs' data" in r.detail


@pytest.mark.parametrize("edit", [
    lambda r: r["measures"][0].update(causeChecks=[{"cause": "routing alone", "within": "yes"}]),
    lambda r: r["measures"][0].update(means="agree" if r["measures"][0]["means"] != "agree" else "differ"),
    lambda r: r["measures"][0]["statements"].remove(r["measures"][0]["statements"][0]),
    lambda r: r.update(family=r["family"] + 1),
    lambda r: r.update(late="none"),
    lambda r: r["runs"]["a"]["crates"][0]["jobs"].pop()],
    ids=["a per-cause field beside the data's own verdict", "the composed verdict alone", "a statement dropped",
         "the family one more", "late said none", "a selected job left out"])
def test_a_record_offering_anything_but_the_datas_own_verdicts_is_refused(tmp_path, crate, edit):
    out = tampered(made(tmp_path, crate), edit)
    assert refused(out, [crate]).name == "comparison-generated"


def test_a_record_in_another_spelling_of_the_same_json_is_refused(tmp_path, crate):
    out = made(tmp_path, crate)
    record = json.loads((out / "comparison" / "record.json").read_bytes())
    (out / "comparison" / "record.json").write_bytes(canonical.compact(record))
    regenerate(out)
    r = refused(out, [crate])
    assert (r.name, r.where) == ("comparison-generated", "comparison/record.json line 1 column 2")


# -- the generator ------------------------------------------------------------------------------------------------------
def test_the_generator_never_reads_the_records_content(tmp_path, crate):
    out = made(tmp_path, crate)
    one = p3_record.generate(out)
    (out / "comparison" / "record.json").write_bytes(b"anything at all, of the same length? no: any bytes\n")
    other = p3_record.generate(out)
    rec = lambda md: next(e for e in md["@graph"] if e["@id"] == "comparison/record.json")  # noqa: E731
    assert rec(one) != rec(other)
    for md in (one, other):
        rec(md).pop("sha256")
        rec(md).pop("contentSize")
    assert one == other


def listed(out, rel, data=b"x\n"):
    """A file added to the comparison crate and listed in its metadata, so that steps 1 to 8 hold it."""
    p = out.joinpath(*rel.split("/"))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    md = S.md_of(out)
    md["@graph"].append({"@id": rel, "@type": "File", "sha256": hashlib.sha256(data).hexdigest(),
                         "contentSize": str(len(data))})
    md["@graph"][1]["hasPart"].append({"@id": rel})
    (out / canonical.DESCRIPTOR).write_bytes(canonical.write(md))


GENERATORS_OWN = ("./ qro:generator", "qro-p3-comparison failed on the records: LayoutError")


@pytest.mark.parametrize("plant, refusal, at", [
    (lambda out: listed(out, "comparison/notes.txt"), "metadata-generated", GENERATORS_OWN),
    (lambda out: listed(out, "comparison/preregistration/plan.md"), "metadata-generated", GENERATORS_OWN),
    (lambda out: (out / "comparison" / "notes.txt").write_bytes(b"x\n"), "file-unlisted", None),
    (lambda out: (out / "comparison" / "record.json").unlink(), "file-missing", None),
    (lambda out: (out / "comparison" / "declaration.json").write_bytes(b"{}\n"), "file-digest", None)],
    ids=["a file it cannot place, listed", "a pre-registration the declaration does not name, listed",
         "a file unlisted", "the record missing", "the declaration changed"])
def test_the_comparison_crate_holds_exactly_the_files_its_declaration_places(tmp_path, crate, plant, refusal, at):
    """A file the declaration does not place, listed so that steps 1 to 8 hold it, is the generator's own refusal, its
    LayoutError at step 9's place, never only metadata that differ."""
    out = made(tmp_path, crate)
    plant(out)
    with pytest.raises(Refused) as r:
        checker.check(out)
    assert r.value.name == refusal
    if at is not None:
        assert (r.value.where, r.value.detail) == at


def test_a_pre_registration_the_declaration_names_and_the_crate_lacks_is_the_generators_raise(tmp_path, crate):
    """The copy taken out of the crate and out of its metadata, so that steps 1 to 8 hold the rest."""
    rel = "comparison/preregistration/plan.md"
    data, _ = S.declare(crate, crate, preregistration=rel)
    out = tmp_path / "comparison"
    p3_compare.make(data, out, [crate], preregistration=b"a plan\n")
    out.joinpath(*rel.split("/")).unlink()
    md = S.md_of(out)
    md["@graph"] = [e for e in md["@graph"] if e["@id"] != rel]
    for e in md["@graph"]:
        for key in ("hasPart", "object"):
            if isinstance(e.get(key), list):
                e[key] = [r for r in e[key] if r["@id"] != rel]
    (out / canonical.DESCRIPTOR).write_bytes(canonical.write(md))
    with pytest.raises(Refused) as r:
        checker.check(out)
    assert (r.value.name, r.value.where, r.value.detail) == ("metadata-generated", *GENERATORS_OWN), "its LayoutError"


def test_a_declaration_out_of_form_in_a_comparison_crate_is_its_generators_raise(tmp_path, crate):
    out = made(tmp_path, crate)
    (out / "comparison" / "declaration.json").write_bytes(b"{}\n")
    with pytest.raises(Exception) as x:
        p3_record.generate(out)
    assert type(x.value).__name__ == "DeclarationError"
    md = S.md_of(out)
    e = next(e for e in md["@graph"] if e["@id"] == "comparison/declaration.json")
    e.update(sha256=hashlib.sha256(b"{}\n").hexdigest(), contentSize="3")
    (out / canonical.DESCRIPTOR).write_bytes(canonical.write(md))
    r = refused(out, [crate])
    assert (r.name, r.where) == ("metadata-generated", "./ qro:generator")


def test_the_root_says_whether_the_comparison_is_real_or_a_rehearsal(tmp_path, crate):
    for kind, said in (("real", "A comparison declared real."),
                       ("rehearsal", "A comparison declared a rehearsal: never cited as a result.")):
        out = made(tmp_path, crate, name=kind, kind=kind)
        md = S.md_of(out)
        assert md["@graph"][1]["description"] == said
        assert next(e for e in md["@graph"] if e["@id"] == "#comparison")["qro:comparisonKind"] == kind


# -- misuse ---------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("spell", [str, lambda p: str(p) + os.sep, lambda p: str(p).upper(),
                                   lambda p: os.path.join(str(p), "..", p.name), lambda p: p],
                         ids=["as given", "a trailing separator", "in upper case", "through its parent", "a Path"])
def test_the_comparisons_own_directory_given_again_as_a_crate_directory_is_misuse(tmp_path, crate, spell):
    out = made(tmp_path, crate)
    with pytest.raises(p3_compare.Misuse, match="the comparison's own directory, given again as a crate directory"):
        p3_compare.check(out, [crate, spell(out)])


def test_a_directory_holding_no_comparison_is_misuse(crate):
    with pytest.raises(p3_compare.Misuse, match="no comparison crate: its generator is qro-p3-test-builder"):
        p3_compare.check(crate, [crate.parent])


def test_a_crate_the_declaration_does_not_name_is_misuse(tmp_path, crate):
    out = made(tmp_path, crate)
    other = B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", [B.ka(), B.law()])], name="other")
    with pytest.raises(p3_compare.Misuse, match="a crate the declaration does not name"):
        p3_compare.check(out, [crate, other])


def test_a_crate_the_declaration_names_that_is_not_given_is_misuse(tmp_path, crate):
    other = B.build(tmp_path, [B.Bundle("ibm_kingston", "morning", [B.ka(), B.law()])], name="other")
    data, _ = S.declare(crate, other, device_b="ibm_kingston")
    p3_compare.make(data, tmp_path / "comparison", [crate, other])
    with pytest.raises(p3_compare.Misuse, match="the declaration names the crate .* which is not given"):
        p3_compare.check(tmp_path / "comparison", [crate])


def test_two_crates_of_one_identity_are_misuse(tmp_path, crate):
    out = made(tmp_path, crate)
    copy = shutil.copytree(crate, tmp_path / "copy")
    with pytest.raises(p3_compare.Misuse, match="a crate given twice: its body digest is that of"):
        p3_compare.check(out, [crate, copy])


def test_a_refused_crate_refuses_the_comparison_by_its_own_name_at_its_place(tmp_path, crate):
    out = made(tmp_path, crate)
    copy = shutil.copytree(crate, tmp_path / "copy")
    (copy / "circuits" / "source.qasm").write_bytes(b"another circuit\n")
    r = refused(out, [copy])
    assert (r.name, r.where) == ("file-digest", "crate 1: circuits/source.qasm")
    assert str(r) == f"file-digest at crate 1: circuits/source.qasm: {r.detail}", "its line says its new place too"


def test_the_comparison_crates_own_refusal_comes_first_at_its_place(tmp_path, crate):
    out = made(tmp_path, crate)
    copy = shutil.copytree(crate, tmp_path / "copy")
    (copy / "circuits" / "source.qasm").write_bytes(b"another circuit\n")
    (out / "comparison" / "record.json").write_bytes(b"{}\n")
    r = refused(out, [copy])
    assert (r.name, r.where) == ("file-digest", "comparison/record.json")


def test_check_returns_a_summary_whose_line_is_the_contracts(tmp_path, crate):
    from qro.__main__ import compare
    out = made(tmp_path, crate)
    assert compare(out, [crate]).startswith("ACCEPTED comparison ")
