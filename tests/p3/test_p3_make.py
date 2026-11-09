"""`make`, the comparison's producer (qro/p3_compare.py; P3's design, item 1), in process on the builder's crates, whose
own step 9 a stand-in holds: it writes exactly the comparison crate's files, its record the computation's, a comparison
the check accepts; it refuses what the check would refuse, writing nothing, and an out it will not use as misuse; and a
make that fails removes what it made and nothing else, files then directories, never recursively, each only while it is
still what it made. Every test of the removal runs on a world made in its own temporary directory, which the sandbox's
launcher holds to the sandbox (CLAUDE.md item 9)."""
import os

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
    d = tmp_path_factory.mktemp("make")
    k = [B.ka(start=f"{T}00:00Z"), B.law("law-0", start=f"{T}01:00Z"), B.law("law-1", start=f"{T}03:00Z", five=40),
         B.coherence(start=f"{T}40:00Z")]
    f = [B.ka(start=f"{T}00:30Z"), B.law("law-0", start=f"{T}02:00Z", five=30), B.coherence(start=f"{T}41:00Z")]
    return B.build(d, [B.Bundle("ibm_kingston", "morning", k), B.Bundle("ibm_fez", "morning", f)])


def files(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def test_make_writes_the_comparison_crates_files_and_the_check_accepts_it(tmp_path, crate):
    data, decl = S.declare(crate, crate)
    out = tmp_path / "out"
    summary = p3_compare.make(data, out, [crate])
    assert files(out) == ["comparison/declaration.json", "comparison/record.json", "ro-crate-metadata.json"]
    assert (out / "comparison" / "declaration.json").read_bytes() == data
    record, _ = p3_compare.compute(decl, None, S.crates_of(crate))
    assert (out / "comparison" / "record.json").read_bytes() == p3_record.dumps(record)
    assert str(summary).startswith("MADE comparison ") and str(p3_compare.check(out, [crate])).startswith(
        "ACCEPTED comparison " + canonical.body_digest(S.md_of(out)))


def test_the_header_moves_and_the_identity_does_not(tmp_path, crate):
    from datetime import datetime, timezone
    data, _ = S.declare(crate, crate)
    one = p3_compare.make(data, tmp_path / "one", [crate], now=datetime(2026, 11, 8, tzinfo=timezone.utc))
    two = p3_compare.make(data, tmp_path / "two", [crate], now=datetime(2027, 1, 1, tzinfo=timezone.utc))
    assert one.identity == two.identity
    root = S.md_of(tmp_path / "two")["@graph"][1]
    assert (root["datePublished"], root["qro:writtenAt"], root["qro:writer"]) == (
        "2027-01-01", "2027-01-01T00:00:00Z", p3_compare.WRITER)


@pytest.mark.parametrize("plant, says", [
    (lambda out: (out.mkdir(), (out / "x").write_bytes(b"x")), "not an empty directory"),
    (lambda out: out.write_bytes(b"x"), "not an empty directory")], ids=["a directory holding a file", "a file"])
def test_an_out_that_is_not_empty_is_misuse_and_is_left_as_it_was(tmp_path, crate, plant, says):
    data, _ = S.declare(crate, crate)
    out = tmp_path / "out"
    plant(out)
    before = sorted(p.name for p in tmp_path.iterdir())
    with pytest.raises(p3_compare.Misuse, match=says):
        p3_compare.make(data, out, [crate])
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_an_out_in_this_repository_or_in_a_crate_is_misuse(crate):
    data, _ = S.declare(crate, crate)
    for out in (p3_compare.REPO / "a-comparison", crate / "comparison", crate):
        with pytest.raises(p3_compare.Misuse):
            p3_compare.make(data, out, [crate])
        assert not (p3_compare.REPO / "a-comparison").exists() and not (crate / "comparison").exists()


def test_a_declaration_out_of_form_and_a_pre_registration_that_does_not_match_are_misuse(tmp_path, crate):
    data, _ = S.declare(crate, crate)
    with pytest.raises(p3_compare.Misuse, match="the declaration is not qro-comparison/1"):
        p3_compare.make(data + b"\n", tmp_path / "out", [crate])
    with pytest.raises(p3_compare.Misuse, match="a pre-registration is given and the declaration names none"):
        p3_compare.make(data, tmp_path / "out", [crate], preregistration=b"plan\n")
    named, _ = S.declare(crate, crate, preregistration="comparison/preregistration/plan.md")
    with pytest.raises(p3_compare.Misuse, match="names a pre-registration and none is given"):
        p3_compare.make(named, tmp_path / "out", [crate])
    assert not (tmp_path / "out").exists()


def test_a_comparison_the_check_would_refuse_is_never_written(tmp_path, crate):
    data, _ = S.declare(crate, crate, device_b="ibm_kingston")
    with pytest.raises(Refused) as r:
        p3_compare.make(data, tmp_path / "out", [crate])
    assert r.value.name == "comparison-trivial" and not (tmp_path / "out").exists()


def test_a_refused_crate_is_refused_at_its_place_and_nothing_is_written(tmp_path, crate):
    import shutil
    copy = shutil.copytree(crate, tmp_path / "copy")
    (copy / "question" / "law.json").write_bytes(b"{}\n")
    data, _ = S.declare(crate, crate)
    with pytest.raises(Refused) as r:
        p3_compare.make(data, tmp_path / "out", [copy])
    assert (r.value.name, r.value.where) == ("file-digest", "crate 1: question/law.json")
    assert not (tmp_path / "out").exists()


# -- a make that fails removes what it made, and nothing else ----------------------------------------------------------
def failing(monkeypatch, before=None):
    """The comparison's generator made to fail once make has written its files, `before` run first."""
    def generate(out):
        if before:
            before(out)
        raise RuntimeError("the generator failed")
    monkeypatch.setattr(p3_record, "generate", generate)


def test_a_failed_make_removes_every_file_and_directory_it_made(tmp_path, crate, monkeypatch):
    data, _ = S.declare(crate, crate)
    out = tmp_path / "deep" / "er" / "out"
    failing(monkeypatch)
    with pytest.raises(RuntimeError, match="the generator failed"):
        p3_compare.make(data, out, [crate])
    assert not (tmp_path / "deep").exists() and sorted(p.name for p in tmp_path.iterdir()) == []


def test_an_out_that_was_there_stays_and_so_does_what_another_put_in_a_directory_make_made(tmp_path, crate,
                                                                                         monkeypatch):
    data, _ = S.declare(crate, crate)
    out = tmp_path / "out"
    out.mkdir()
    failing(monkeypatch, before=lambda o: (o / "comparison" / "theirs.txt").write_bytes(b"another's\n"))
    with pytest.raises(RuntimeError):
        p3_compare.make(data, out, [crate])
    assert files(out) == ["comparison/theirs.txt"], "make's own files gone; another's, and its directory, kept"


def test_an_empty_out_that_was_there_stays_empty_after_a_failed_make(tmp_path, crate, monkeypatch):
    data, _ = S.declare(crate, crate)
    out = tmp_path / "out"
    out.mkdir()
    failing(monkeypatch)
    with pytest.raises(RuntimeError):
        p3_compare.make(data, out, [crate])
    assert out.is_dir() and files(out) == [] and sorted(p.name for p in out.iterdir()) == []


def test_a_file_make_wrote_that_another_replaced_is_not_removed(tmp_path, crate, monkeypatch):
    data, _ = S.declare(crate, crate)
    out = tmp_path / "out"

    def replace(o):
        p = o / "comparison" / "record.json"
        p.unlink()
        p.write_bytes(b"another's record\n")
    failing(monkeypatch, before=replace)
    with pytest.raises(RuntimeError):
        p3_compare.make(data, out, [crate])
    assert files(out) == ["comparison/record.json"]
    assert (out / "comparison" / "record.json").read_bytes() == b"another's record\n"


def test_the_metadata_written_last_is_removed_when_the_self_check_fails(tmp_path, crate, monkeypatch):
    data, _ = S.declare(crate, crate)
    out = tmp_path / "out"
    real = checker.check

    def check(path):
        if out.exists() and os.path.samefile(path, out):
            raise Refused("metadata-generated", "./ qro:generator", "a check made to fail")
        return real(path)
    monkeypatch.setattr(checker, "check", check)
    with pytest.raises(Refused, match="a check made to fail"):
        p3_compare.make(data, out, [crate])
    assert not out.exists()


def test_clear_removes_only_what_the_list_holds_and_never_recursively(tmp_path):
    made = p3_compare._Made()
    made.directory(tmp_path / "a" / "b")
    made.write(tmp_path / "a" / "b" / "mine.txt", b"mine\n")
    (tmp_path / "a" / "b" / "theirs.txt").write_bytes(b"theirs\n")
    (tmp_path / "beside.txt").write_bytes(b"beside\n")
    p3_compare.clear(made)
    assert files(tmp_path) == ["a/b/theirs.txt", "beside.txt"]
