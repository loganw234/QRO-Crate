"""A build removes only what it made (CLAUDE.md item 9; qro_kit/crate.py's `Made`, and `crate.build`'s cleanup): each file and
directory is listed as it is made, with its identity, and removed only if it is still that entry; a tree a program the build
started has filled is listed whole and removed entry by entry, a link unlinked and never entered; what another put in the way
stays, and every directory above it. Run without git or qiskit, so that a mutant of this code can run at low integrity."""
import os
import stat

import pytest
from p5_support import no_link_left_behind, no_network, twin  # noqa: F401

from qro import p5_generate
from qro_kit import crate
from qro_kit.crate import Made

pytestmark = pytest.mark.usefixtures("no_network", "no_link_left_behind")


def listing(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))


def test_clear_removes_each_file_and_directory_the_build_made_and_nothing_else(tmp_path):
    (tmp_path / "keep").mkdir()
    (tmp_path / "keep" / "mine.txt").write_bytes(b"not the build's\n")
    m = Made()
    m.write(tmp_path / "out" / "a" / "b.txt", b"b")
    m.write(tmp_path / "out" / "c.txt", b"c")
    assert m.bytes == 2 and len(m.files) == 2 and len(m.directories) == 2
    m.clear()
    assert not (tmp_path / "out").exists() and listing(tmp_path) == ["keep", "keep/mine.txt"]


def test_a_directory_that_was_there_is_never_listed_or_removed(tmp_path):
    (tmp_path / "out").mkdir()
    m = Made()
    m.write(tmp_path / "out" / "x.txt", b"x")
    assert [d for d, _ in m.directories] == []
    m.clear()
    assert (tmp_path / "out").is_dir() and listing(tmp_path) == ["out"]


def test_what_another_put_in_a_directory_the_build_made_stays_with_every_directory_above_it(tmp_path):
    m = Made()
    m.write(tmp_path / "out" / "a" / "b.txt", b"b")
    (tmp_path / "out" / "a" / "foreign.txt").write_bytes(b"another's\n")
    m.clear()
    assert listing(tmp_path) == ["out", "out/a", "out/a/foreign.txt"]


def test_a_file_replaced_after_it_was_made_is_not_the_builds_to_remove(tmp_path):
    m = Made()
    m.write(tmp_path / "x.txt", b"x")
    os.unlink(tmp_path / "x.txt")
    (tmp_path / "x.txt").write_bytes(b"another file under the same name\n")
    m.clear()
    assert (tmp_path / "x.txt").read_bytes() == b"another file under the same name\n"


def test_a_file_that_exists_is_an_error_and_is_never_overwritten_or_listed(tmp_path):
    (tmp_path / "x.txt").write_bytes(b"there first\n")
    m = Made()
    with pytest.raises(FileExistsError):
        m.write(tmp_path / "x.txt", b"x")
    m.clear()
    assert (tmp_path / "x.txt").read_bytes() == b"there first\n" and m.files == []


def test_a_tree_the_build_adopted_is_removed_entry_by_entry_read_only_files_included(tmp_path):
    (tmp_path / "other").mkdir()
    tree = tmp_path / "records"
    (tree / ".git" / "objects").mkdir(parents=True)
    obj = tree / ".git" / "objects" / "ab"
    obj.write_bytes(b"an object")
    os.chmod(obj, stat.S_IREAD)
    (tree / "unit").mkdir()
    (tree / "unit" / "UNIT.json").write_bytes(b"{}\n")
    m = Made()
    m.adopt(tree)
    m.clear()
    assert listing(tmp_path) == ["other"]


def test_an_empty_directory_replaced_after_it_was_made_is_not_the_builds_to_remove(tmp_path):
    m = Made()
    m.directory(tmp_path / "made")
    os.rmdir(tmp_path / "made")
    (tmp_path / "made").mkdir()                 # another's, empty: rmdir alone would remove it
    m.clear()
    assert (tmp_path / "made").is_dir()


def test_a_tree_replaced_by_another_directory_is_not_removed(tmp_path):
    tree = tmp_path / "records"
    tree.mkdir()
    m = Made()
    m.adopt(tree)
    os.rmdir(tree)
    tree.mkdir()
    (tree / "another.txt").write_bytes(b"another's\n")
    m.clear()
    assert (tree / "another.txt").is_file()


def test_remove_listed_tree_unlinks_a_link_and_never_enters_it(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_bytes(b"not in the tree\n")
    tree = tmp_path / "tree"
    tree.mkdir()
    if os.name == "nt":
        import subprocess
        subprocess.run(["cmd", "/c", "mklink", "/J", str(tree / "link"), str(outside)], check=True, capture_output=True)
    else:
        os.symlink(outside, tree / "link")
    crate.remove_listed_tree(str(tree))
    assert not tree.exists() and (outside / "precious.txt").read_bytes() == b"not in the tree\n"


def test_a_failed_git_in_freeze_is_the_kit_failing_exit_3_and_never_misuse(tmp_path, monkeypatch, capfd):
    """The first verifier, round 1: a git that fails in freeze's throwaway repository exited 2, which is misuse. It is the kit
    failing: a GitFailed, not a CrateError, and the command line's exit 3 with one FAILED line and no verdict."""
    import subprocess
    from types import SimpleNamespace

    from qro_kit import __main__ as cli, freeze
    monkeypatch.setattr(freeze.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=128, stdout=b"", stderr=b"fatal: unable to push to the throwaway origin\n"))
    with pytest.raises(freeze.GitFailed, match="git push -q failed in the throwaway repository"):
        freeze.git(tmp_path, "push", "-q")
    assert not issubclass(freeze.GitFailed, crate.CrateError) and subprocess is freeze.subprocess

    def failing(*a, **k):
        freeze.git(tmp_path, "push", "-q")
    monkeypatch.setattr(freeze, "freeze", failing)
    code = cli.main(["freeze", "--route", "local", "--out", str(tmp_path / "w")], tree=lambda: {})
    captured = capfd.readouterr()
    assert code == 3 and captured.out == "" and captured.err.startswith("FAILED: the kit itself failed, GitFailed")
    assert "this is not a verdict" in captured.err


def fake_unit(path):
    (path / "bundle").mkdir(parents=True)
    (path / "UNIT.json").write_bytes(b"{}\n")
    (path / "bundle" / "manifest.json").write_bytes(b"{}\n")
    return path


def test_crate_build_that_fails_removes_what_it_made_and_leaves_what_another_put_there(tmp_path, monkeypatch):
    unit, out = fake_unit(tmp_path / "unit"), tmp_path / "crate"

    def fail(path, write, now=None, writer=None):
        (path / "unit" / "foreign.txt").write_bytes(b"another's, put there during the build\n")
        raise RuntimeError("the metadata fails")
    monkeypatch.setattr(p5_generate, "finalize", fail)
    with pytest.raises(RuntimeError):
        crate.build(unit, out, tree=lambda: {})
    assert listing(out) == ["unit", "unit/foreign.txt"]
    assert listing(unit) == ["UNIT.json", "bundle", "bundle/manifest.json"]


def test_crate_build_that_fails_leaves_nothing_where_nothing_else_was(tmp_path, monkeypatch):
    unit, out = fake_unit(tmp_path / "unit"), tmp_path / "crate"
    monkeypatch.setattr(p5_generate, "finalize", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    with pytest.raises(RuntimeError):
        crate.build(unit, out, tree=lambda: {})
    assert not out.exists()


def test_crate_build_refuses_an_out_that_exists_or_lies_inside_the_unit_and_makes_nothing(tmp_path):
    unit = fake_unit(tmp_path / "unit")
    (tmp_path / "there").mkdir()
    for out in (tmp_path / "there", unit / "crate"):
        with pytest.raises(crate.CrateError):
            crate.build(unit, out, tree=lambda: {})
    assert listing(unit) == ["UNIT.json", "bundle", "bundle/manifest.json"] and listing(tmp_path / "there") == []


def test_crate_build_refuses_a_link_in_the_unit_directory(tmp_path):
    unit = fake_unit(tmp_path / "unit")
    other = tmp_path / "other"
    other.mkdir()
    if os.name == "nt":
        import subprocess
        subprocess.run(["cmd", "/c", "mklink", "/J", str(unit / "linked"), str(other)], check=True, capture_output=True)
    else:
        os.symlink(other, unit / "linked")
    try:
        with pytest.raises(crate.CrateError, match="a link"):
            crate.build(unit, tmp_path / "crate", tree=lambda: {})
        assert not (tmp_path / "crate").exists()
    finally:
        os.rmdir(unit / "linked") if os.name == "nt" else os.unlink(unit / "linked")


def test_a_real_twin_builds_a_crate_of_its_own_files_and_a_failed_second_build_removes_only_its_own(tmp_path):
    """The unit directory of a built twin (the crate's `unit/` files) through crate.build, then the same out again."""
    src = twin(tmp_path / "w")
    unit = src / "unit"
    out = tmp_path / "crate"
    done = crate.build(unit, out, tree=lambda: {"commit": "0" * 40})
    assert done["identity"] and (out / "ro-crate-metadata.json").is_file() and done["intake"].lines()[0].startswith("ACCEPTED ")
    with pytest.raises(crate.CrateError):
        crate.build(unit, out, tree=lambda: {})
    assert (out / "ro-crate-metadata.json").is_file()
