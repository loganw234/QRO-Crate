"""tools/gen_profile.py against the states a tree can be in that nobody makes by accident (P4's fourth verifier, round 4, MEASURED,
and the lead's rulings of 2026-10-26T18:56:48Z): profile/ itself a link; a link or a directory where P0's context goes; a hard
link at a rendered path; a name that differs only by case from a rendered name or from P0's context; a directory where a file
goes; a directory the host cannot list; a read-only file. Each is held in process and, where it matters, as the process a user
runs, in both modes, with what is behind a link, byte for byte, as the witness that nothing behind it was read, changed or
removed. A link is a real junction, made without privilege, where the host makes junctions (link_dir in p4_sweeps.py), and its
target is there when the test ends: the module's fixture removes the links a failing test strands (remove_links_under in
p4_helpers.py). A junction whose target is gone is made by no test: the owner's machine cannot open one (the stated limit,
docs/P4.md) and so cannot remove it, and a test of a link that leads nowhere tells the tool that a link stands at the path instead
(tell_links in p4_helpers.py), with a stand-in shown to lead nowhere to every call that could ask (leads_nowhere), and a control
that each telling took."""
import ast
import os
import shutil
import stat
from pathlib import Path

import pytest
from p4_helpers import (ROOT, load_tool, outside_dir, profile_copy, remove_links_under, run_patched, run_tool, snapshot, tell_links, tree,
                        watch_reads)
from p4_sweeps import link_dir
from qro import p4_profile as P

gen = load_tool()
RENDERED = P.render()


@pytest.fixture(autouse=True)
def no_link_is_stranded(tmp_path):
    """Each test of this module that makes a junction ends, passed or failed, with the links under its folder removed while their
    targets are there (remove_links_under, whose docstring says why): a failing test would otherwise strand them."""
    yield
    remove_links_under(tmp_path)


def tool_docstring():
    """The tool's module docstring, read from its source text: gen.__doc__ is empty under python -OO."""
    return ast.get_docstring(ast.parse((ROOT / "tools" / "gen_profile.py").read_text(encoding="utf-8")))


def linked_root(tmp_path, target, name="root"):
    """A root whose profile/ is a link (a junction) to `target`, and holds nothing else."""
    root = tmp_path / name
    root.mkdir()
    link_dir(root / "profile", target)
    return root


# -- profile/ itself a link (the fourth verifier's D1) ---------------------------------------------------------------------------------
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_profile_itself_a_junction_to_a_directory_outside_the_tree_is_refused_by_name_and_nothing_behind_it_is_read(
        tmp_path, capsys, monkeypatch, mode):
    """The state the verifier made: a file, an empty directory and a copy of the rendered files behind the link. It was walked,
    its stray named and removed, and the rendered files written there. Now the first thing either mode does is ask whether
    profile/ is a link, and it is refused, with exit 1, before anything under it is read, listed or walked."""
    outside = outside_dir(tmp_path, rendered=True)
    before = snapshot(outside)
    assert "victim.txt" in before and before["emptydir"] is None and "README.md" in before
    root = linked_root(tmp_path, outside)
    seen = watch_reads(monkeypatch, root / "profile")
    assert gen.main([mode], root=root) == 1
    said = capsys.readouterr()
    assert said.out == "" and said.err == gen.LINKED + "\n"
    assert seen == []                                                           # nothing under it was listed, walked or opened
    monkeypatch.undo()
    assert snapshot(outside) == before and gen.is_link(root / "profile")
    os.rmdir(root / "profile")


@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_profile_itself_a_junction_to_an_exact_copy_is_refused_too_it_was_once_clean(tmp_path, capsys, mode):
    outside = tmp_path / "copy"
    shutil.copytree(ROOT / "profile", outside)
    before = snapshot(outside)
    root = linked_root(tmp_path, outside)
    assert gen.main([mode], root=root) == 1
    said = capsys.readouterr()
    assert said.out == "" and said.err == gen.LINKED + "\n" and snapshot(outside) == before
    os.rmdir(root / "profile")


@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_profile_itself_a_junction_to_the_trees_own_root_changes_nothing_in_the_tree(tmp_path, capsys, mode):
    """The verifier's most dangerous case: --write removed two files of the tree, then the link, and failed. The files here sort
    before the link, as the verifier's did, and the link lists itself in its own target."""
    root = tmp_path / "root"
    (root / "a").mkdir(parents=True)
    (root / "aaa.txt").write_bytes(b"mine" + bytes([10]))
    (root / "a" / "keep.txt").write_bytes(b"keep" + bytes([10]))
    link_dir(root / "profile", root)
    before = snapshot(root)
    assert before["profile"] == "link" and before["aaa.txt"] == b"mine" + bytes([10])
    assert gen.main([mode], root=root) == 1
    said = capsys.readouterr()
    assert said.out == "" and said.err == gen.LINKED + "\n" and snapshot(root) == before
    os.rmdir(root / "profile")


@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_profile_itself_a_link_to_nothing_is_a_link_too(tmp_path, capsys, monkeypatch, mode):
    """A junction whose target is gone leads nowhere, and a host that opens it calls it a link, so profile/ is refused as one that
    leads somewhere is (the tests above). The owner's machine opens none, and a junction it cannot open it cannot remove either
    (the stated limit, docs/P4.md): none is made. Nothing at all stands at profile/, the tool is told that a link does (tell_links), and it
    must refuse the tree by that answer before it reads anything: its sentence is the link's, and not that of a context that is
    not there, which is what a tree with nothing at profile/ gets from a tool that was not told (the first test of the stated
    limit, below, holds that)."""
    root = tmp_path / "root"
    root.mkdir()
    profile = root / "profile"
    real = tell_links(monkeypatch, gen, profile)
    assert gen.is_link(profile) and not real(profile) and not os.path.lexists(profile)     # the control: told, and not made
    assert not gen.is_link(root) and not gen.is_link(tmp_path / "profile")                 # at that path alone, not at its name
    assert gen.main([mode], root=root) == 1
    said = capsys.readouterr()
    assert said.out == "" and said.err == gen.LINKED + "\n"
    assert os.listdir(root) == []                                   # and nothing was made: no profile/, no file beside it


@pytest.mark.parametrize("error", [IsADirectoryError, PermissionError])
def test_remove_link_falls_back_to_rmdir_where_unlink_will_not_take_a_directory_link_and_still_takes_nothing_behind_it(
        tmp_path, monkeypatch, error):
    """A symbolic link to a directory is removed with rmdir on Windows, which this host cannot make one of (WinError 1314): the
    fallback is held by a junction and an unlink that refuses it, as a host that wants rmdir refuses it."""
    outside = outside_dir(tmp_path)
    before = snapshot(outside)
    link_dir(tmp_path / "jct", outside)
    real = Path.unlink

    def refusing(self, *args, **kwargs):
        if self.name == "jct":
            raise error(13, "will not unlink a directory link")
        return real(self, *args, **kwargs)
    monkeypatch.setattr(Path, "unlink", refusing)
    gen.remove_link(tmp_path / "jct")
    assert not os.path.lexists(tmp_path / "jct") and snapshot(outside) == before


def test_write_removes_each_link_with_remove_link_and_never_with_a_plain_unlink(tmp_path, monkeypatch):
    """On a host where unlink alone takes a junction out, as this one, the two look alike; where a directory link wants rmdir
    (a symbolic link on Windows) only remove_link's fallback works. So the call is held: every link --write removes goes through it."""
    root = profile_copy(tmp_path / "root")
    outside = outside_dir(tmp_path)
    link_dir(root / "profile" / "jct", outside)
    link_dir(root / "profile" / "validator" / "jct2", outside)
    calls = []
    real = gen.remove_link
    monkeypatch.setattr(gen, "remove_link", lambda path: (calls.append(Path(path)), real(path))[1])
    assert gen.main(["--write"], root=root) == 0
    assert sorted(p.relative_to(root / "profile").as_posix() for p in calls) == ["jct", "validator/jct2"]


def test_a_link_below_profile_that_leads_nowhere_is_listed_and_removed_like_any_other(tmp_path, capsys, monkeypatch):
    """A junction whose target is gone is, in its parent's listing, an entry that cannot itself be listed (the host says
    FileNotFoundError), and a host that opens it calls it a link. None is made (see the test above): an empty directory stands in
    for it, shown as an entry that leads nowhere to every call by which the tool, or a mutant of it, could ask (leads_nowhere:
    P4's sixth verifier, D1, found nine mutants that asked by another call than the first two it told), and the tool is told that it
    is a link (tell_links). The tool must list it as a link, never enter it, and remove it, as it does a link that leads
    somewhere: entering it is what the stand-in would answer with exit 3, as the tests of the stated limit show of the same
    stand-in not told. Because lstat is told gone, os.path.lexists of the stand-in is false from the start: that it is gone after
    --write is read from its parent's listing."""
    root = profile_copy(tmp_path / "root")
    jct = root / "profile" / "jct"
    jct.mkdir()                                                     # the stand-in: an entry of profile/ that is no link
    (root / "jct").mkdir()                                          # the same name at another path: there, to the end
    real = tell_links(monkeypatch, gen, jct)
    leads_nowhere(monkeypatch, jct)
    assert gen.is_link(jct) and not real(jct)                       # the controls: told, and not made
    assert not gen.is_link(root / "profile") and not gen.is_link(root / "jct")                       # at that path alone
    assert_gone_to_every_call(jct)                                  # leading nowhere to every call it is told to, and still listed
    for there in (root / "jct", root / "profile", root / "profile" / "validator"):
        assert_there_to_every_call(there)                           # and to no other path, nor to its name
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert "profile" + "/jct is a link, which no definition renders" in err
    assert "holds no file" not in err and "cannot list" not in err  # it was not entered, nor taken for a directory
    assert gen.main(["--write"], root=root) == 0
    assert "jct" not in os.listdir(root / "profile")                # the link itself is gone
    assert gen.main(["--check"], root=root) == 0


def test_the_problem_says_what_is_refused_and_what_to_do():
    text = gen.LINKED
    assert text.startswith("profile/ is a link") and "never followed" in text and "FORMAT.md item 12" in text
    assert "nothing under it is read, walked, written or removed, in either mode" in text and "Remove the link by hand" in text
    assert text.isascii() and "\n" not in text


@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_as_a_process_profile_itself_a_link_is_exit_1_and_the_named_problem_and_nothing_behind_it_changes(tmp_path, mode):
    root = tree(tmp_path / "t", profile=False)
    outside = outside_dir(tmp_path, rendered=True)
    before = snapshot(outside)
    link_dir(root / "profile", outside)
    done = run_tool([mode], tmp_path, root)
    assert done.returncode == 1 and done.stdout == "" and done.stderr == gen.LINKED + "\n", done.stderr[-300:]
    assert snapshot(outside) == before and gen.is_link(root / "profile")
    os.rmdir(root / "profile")


@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_as_a_process_profile_itself_a_junction_to_the_trees_own_root_changes_nothing(tmp_path, mode):
    root = tree(tmp_path / "t", profile=False)
    (root / "a").mkdir()
    (root / "aaa.txt").write_bytes(b"mine" + bytes([10]))
    (root / "a" / "keep.txt").write_bytes(b"keep" + bytes([10]))
    link_dir(root / "profile", root)
    before = snapshot(root)
    done = run_tool([mode], tmp_path, root)
    assert done.returncode == 1 and done.stdout == "" and done.stderr == gen.LINKED + "\n", done.stderr[-300:]
    assert snapshot(root) == before
    os.rmdir(root / "profile")


# -- a link or a directory where P0's context goes: the message is true ----------------------------------------------------------------
def test_a_junction_at_p0s_context_is_called_a_link_and_not_a_missing_file_and_nothing_behind_it_is_touched(tmp_path, capsys):
    root = profile_copy(tmp_path / "root")
    outside = outside_dir(tmp_path)
    before = snapshot(outside)
    context = root / "profile" / "context.jsonld"
    context.unlink()
    link_dir(context, outside)
    for mode in ("--check", "--write"):
        assert gen.main([mode], root=root) == 1
        err = capsys.readouterr().err
        assert err.count("\n") == 1 and "profile/context.jsonld is a link, not the file tools/gen_vocabulary.py --write writes" in err
        assert "never read through" in err and "missing" not in err and "not there" not in err
    assert snapshot(outside) == before and gen.is_link(context)
    os.rmdir(context)


def test_a_directory_at_p0s_context_is_called_a_directory_and_not_a_missing_file_and_is_not_removed(tmp_path, capsys):
    root = profile_copy(tmp_path)
    context = root / "profile" / "context.jsonld"
    context.unlink()
    context.mkdir()
    (context / "x.txt").write_bytes(b"x")
    before = snapshot(root / "profile")
    for mode in ("--check", "--write"):
        assert gen.main([mode], root=root) == 1
        err = capsys.readouterr().err
        assert err.count("\n") == 1 and "profile/context.jsonld is a directory, not the file tools/gen_vocabulary.py --write writes" in err
        assert "missing" not in err and "not there" not in err
    assert snapshot(root / "profile") == before


def test_a_context_the_user_may_not_read_is_named_for_what_it_is_and_not_called_missing(tmp_path, capsys, monkeypatch):
    root = profile_copy(tmp_path)
    real = Path.read_bytes

    def refusing(self):
        if self.name == "context.jsonld":
            raise PermissionError(13, "Access is denied")
        return real(self)
    monkeypatch.setattr(Path, "read_bytes", refusing)
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert err == "profile/context.jsonld cannot be read (PermissionError): tools/gen_vocabulary.py --write writes it\n"


def test_a_missing_context_still_says_it_is_missing_and_how_to_make_it(tmp_path, capsys):
    root = profile_copy(tmp_path)
    (root / "profile" / "context.jsonld").unlink()
    for mode in ("--check", "--write"):
        assert gen.main([mode], root=root) == 1
        assert capsys.readouterr().err == "profile/context.jsonld is missing: run tools/gen_vocabulary.py --write\n"


# -- a hard link at a rendered path: written beside and replaced, never written through ---------------------------------------------
def hard_link_at(root, rel, other):
    """The rendered file at `rel` made another name of the file `other`."""
    place = root / "profile" / rel
    place.unlink()
    os.link(other, place)
    return place


def test_write_never_writes_through_a_hard_link_the_other_name_keeps_its_bytes(tmp_path, capsys):
    root = profile_copy(tmp_path / "root")
    theirs = tmp_path / "theirs.md"
    theirs.write_bytes(b"theirs" + bytes([10]))
    place = hard_link_at(root, "README.md", theirs)
    assert os.stat(theirs).st_nlink == 2 and place.read_bytes() == b"theirs" + bytes([10])
    assert gen.main(["--check"], root=root) == 1 and "profile/README.md DRIFTED" in capsys.readouterr().err
    assert gen.main(["--write"], root=root) == 0
    assert theirs.read_bytes() == b"theirs" + bytes([10])                   # the other name keeps its bytes
    assert place.read_bytes() == RENDERED["README.md"]
    assert os.stat(theirs).st_nlink == 1 and os.stat(place).st_nlink == 1          # and the two are no longer one file
    assert gen.main(["--check"], root=root) == 0


def test_a_hard_link_that_holds_the_right_bytes_is_clean_to_check_and_write_still_breaks_it(tmp_path):
    """--check judges bytes, so a hard link with the rendered bytes is clean; --write always puts a new file in the place."""
    root = profile_copy(tmp_path / "root")
    theirs = tmp_path / "theirs.md"
    theirs.write_bytes(RENDERED["README.md"])
    place = hard_link_at(root, "README.md", theirs)
    assert gen.main(["--check"], root=root) == 0 and os.stat(theirs).st_nlink == 2
    assert gen.main(["--write"], root=root) == 0
    assert os.stat(theirs).st_nlink == 1 and theirs.read_bytes() == RENDERED["README.md"] and place.read_bytes() == RENDERED["README.md"]


def test_as_a_process_write_never_writes_through_a_hard_link(tmp_path):
    root = tree(tmp_path / "t")
    theirs = tmp_path / "theirs.md"
    theirs.write_bytes(b"theirs" + bytes([10]))
    place = hard_link_at(root, "EXAMPLES.md", theirs)
    done = run_tool(["--write"], tmp_path, root)
    assert done.returncode == 0, done.stderr[-300:]
    assert theirs.read_bytes() == b"theirs" + bytes([10]) and place.read_bytes() == RENDERED["EXAMPLES.md"]
    assert run_tool(["--check"], tmp_path, root).returncode == 0


def test_a_temporary_file_a_crash_left_is_a_stray_and_write_removes_it_before_it_writes(tmp_path, capsys):
    root = profile_copy(tmp_path)
    stale = root / "profile" / ("README.md" + gen.TEMP)
    stale.write_bytes(b"half a file")
    assert not any(r.endswith(gen.TEMP) for r in RENDERED)                     # no rendered path ends so
    assert gen.main(["--check"], root=root) == 1
    assert f"README.md{gen.TEMP} is rendered by no definition; run --write" in capsys.readouterr().err
    assert gen.main(["--write"], root=root) == 0
    assert f"removed README.md{gen.TEMP}" in capsys.readouterr().out.splitlines() and not stale.exists()
    assert gen.main(["--check"], root=root) == 0


def test_replace_file_makes_the_whole_file_and_leaves_no_temporary_one(tmp_path):
    place = tmp_path / "sub" / "a.txt"
    gen.replace_file(place, b"new")
    assert place.read_bytes() == b"new" and sorted(os.listdir(tmp_path / "sub")) == ["a.txt"]
    gen.replace_file(place, b"newer")
    assert place.read_bytes() == b"newer" and sorted(os.listdir(tmp_path / "sub")) == ["a.txt"]


def test_replace_file_removes_a_temporary_file_it_made_when_it_cannot_put_it_in_place(tmp_path, monkeypatch):
    place = tmp_path / "a.txt"
    place.write_bytes(b"old")

    def refusing(src, dst, *a, **k):
        raise OSError("not now")
    monkeypatch.setattr(os, "replace", refusing)
    with pytest.raises(OSError, match="not now"):
        gen.replace_file(place, b"new")
    assert place.read_bytes() == b"old" and sorted(os.listdir(tmp_path)) == ["a.txt"]


def test_replace_file_never_removes_or_overwrites_a_file_it_did_not_make(tmp_path):
    """A cleanup removes what it made (CLAUDE.md item 9): a file of someone else's stands where its temporary file would go. It is
    made exclusively, so the attempt fails, and the file is still there, with its bytes, as is the place."""
    place = tmp_path / "a.txt"
    place.write_bytes(b"old")
    theirs = tmp_path / ("a.txt" + gen.TEMP)
    theirs.write_bytes(b"mine")
    with pytest.raises(FileExistsError):
        gen.replace_file(place, b"new")
    assert place.read_bytes() == b"old" and theirs.read_bytes() == b"mine"


def test_the_pass_over_empty_directories_never_removes_the_base_itself_empty_as_it_is(tmp_path):
    base = tmp_path / "profile"
    (base / "a" / "b").mkdir(parents=True)
    gen.remove_empty_dirs(base)
    assert base.is_dir() and os.listdir(base) == []


# -- a name that differs only by case from a rendered name or from P0's context --------------------------------------------------------
CASES = [("README.md", "readme.md"), ("validator", "Validator"), ("examples", "Examples"), ("context.jsonld", "Context.jsonld"),
         ("ro-crate-metadata.json", "RO-Crate-Metadata.json")]       # the last is listed by no Profile Crate: the clash is the one problem


@pytest.mark.parametrize("old, new", CASES)
def test_a_name_that_differs_only_by_case_is_refused_by_name_in_both_modes_and_never_removed_or_written_over(
        tmp_path, capsys, old, new):
    root = profile_copy(tmp_path / "root")
    os.rename(root / "profile" / old, root / "profile" / new)
    before = snapshot(root / "profile")
    for mode in ("--check", "--write"):
        assert gen.main([mode], root=root) == 1
        said = capsys.readouterr()
        if old == "context.jsonld" and not (root / "profile" / old).exists():
            # a host that tells the two names apart finds no file of P0's by the right name: nothing is there to refuse, and it
            # says so, truly (the other hosts read the file and see the clash)
            assert said.err == "profile/context.jsonld is missing: run tools/gen_vocabulary.py --write\n"
        else:
            assert said.err.count("differs only by case") == 1, said.err
            assert f"profile/{new} differs only by case from {old}" in said.err
            assert "it is never removed or renamed here, and --write refuses while it is there" in said.err
            assert ("P0's file, which tools/gen_vocabulary.py writes" in said.err) == (old == "context.jsonld")
            assert "missing; run --write" not in said.err and "rendered by no definition" not in said.err   # said once, as a clash
        said_clean = [line for line in said.out.splitlines() if line.endswith("is exactly what its definition renders")
                      and line.startswith((f"profile/{old} ", f"profile/{old}/"))]
        assert said_clean == []                           # a file whose name is spelt another way on disk is not called exact
        if mode == "--write":
            assert said.out == ""
    assert snapshot(root / "profile") == before                                # nothing removed, nothing written, byte for byte


def test_a_directory_spelt_another_way_that_holds_only_strays_is_cleared_and_the_right_one_made(tmp_path, capsys):
    """No clash: the strays go, the empty directory goes with them, and only then is the rendered one made, in its own spelling
    (on a host that ignores case it would otherwise have been written into the old one, and --check would never be clean)."""
    root = profile_copy(tmp_path / "root")
    shutil.rmtree(root / "profile" / "validator")
    (root / "profile" / "Validator").mkdir()
    (root / "profile" / "Validator" / "zzz.txt").write_bytes(b"x")
    assert gen.main(["--check"], root=root) == 1
    assert gen.main(["--write"], root=root) == 0
    capsys.readouterr()
    names = os.listdir(root / "profile")
    assert "validator" in names and "Validator" not in names
    assert gen.main(["--check"], root=root) == 0 and capsys.readouterr().err == ""


def test_case_clashes_are_the_files_spelt_otherwise_than_a_rendered_path_or_p0s_context():
    rendered = {"README.md": b"", "validator/qro-crate/profile.ttl": b""}
    have = {"README.md": b"", "readme.md": b"", "Validator/qro-crate/profile.ttl": b"", "Context.jsonld": b"",
            "context.jsonld": b"", "stray.txt": b"", "validator/zzz": b"", "Zzz.txt": b"", "zzz.txt": b""}
    assert gen.case_clashes(rendered, have) == {"Context.jsonld": "context.jsonld", "Validator/qro-crate/profile.ttl":
                                                "validator/qro-crate/profile.ttl", "readme.md": "README.md"}
    assert gen.case_clashes(rendered, {"README.md": b"", "context.jsonld": b"", "validator/qro-crate/profile.ttl": b""}) == {}
    said = dict(gen.clash_problems({"Validator/qro-crate/profile.ttl": "validator/qro-crate/profile.ttl",
                                    "Validator/qro-crate/must/1_structure.ttl": "validator/qro-crate/must/1_structure.ttl",
                                    "validator/QRO-crate/profile.ttl": "validator/qro-crate/profile.ttl",
                                    "Context.jsonld": "context.jsonld"}))
    assert sorted(said) == ["Context.jsonld", "Validator", "validator/QRO-crate"]            # one a name, as high as the spellings part
    assert "differs only by case from context.jsonld, P0's file, which tools/gen_vocabulary.py writes;" in said["Context.jsonld"]
    assert "differs only by case from validator, which a definition renders;" in said["Validator"]
    assert "differs only by case from validator/qro-crate, which a definition renders;" in said["validator/QRO-crate"]


# -- a directory where a rendered file goes ---------------------------------------------------------------------------------------------
def directory_at_readme(root, state, tmp_path):
    place = root / "profile" / "README.md"
    place.unlink()
    place.mkdir()
    outside = None
    if state in ("strays", "link"):
        (place / "sub").mkdir()
        (place / "stray.txt").write_bytes(b"x")
    if state == "link":
        outside = outside_dir(tmp_path)
        link_dir(place / "jct", outside)
    return place, outside


@pytest.mark.parametrize("state", ["empty", "strays", "link"])
def test_a_directory_where_a_file_goes_is_cleared_by_write_and_check_says_what_write_will_do(tmp_path, capsys, state):
    """The verifier's: --check said to run --write, which failed every time. It clears what stands where a file goes (the strays
    in it, a link in it, and then the directory), and --check says so."""
    root = profile_copy(tmp_path / "root")
    place, outside = directory_at_readme(root, state, tmp_path)
    before = snapshot(outside) if outside else None
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert "profile/README.md is a directory, not the file its definition renders; run --write removes it" in err
    assert "profile/README.md missing" not in err
    assert gen.main(["--write"], root=root) == 0
    assert place.is_file() and place.read_bytes() == RENDERED["README.md"]
    if outside:
        assert snapshot(outside) == before                                  # the link was removed, and nothing behind it
    assert gen.main(["--check"], root=root) == 0
    assert gen.main(["--write"], root=root) == 0 and gen.main(["--check"], root=root) == 0


def test_as_a_process_a_directory_where_a_file_goes_is_cleared_and_the_second_run_changes_nothing(tmp_path):
    root = tree(tmp_path / "t")
    place = root / "profile" / "validator" / "qro-crate" / "profile.ttl"
    place.unlink()
    place.mkdir()
    assert run_tool(["--check"], tmp_path, root).returncode == 1
    done = run_tool(["--write"], tmp_path, root)
    assert done.returncode == 0, done.stderr[-300:]
    assert place.is_file() and run_tool(["--check"], tmp_path, root).returncode == 0


# -- a directory the host cannot list ---------------------------------------------------------------------------------------------------------
def unlistable(monkeypatch, directory, error=PermissionError):
    """os.scandir, which os.walk lists a directory with, raises `error` for `directory`: a host that will not list one.
    (A real one cannot be made here: the sandbox's guard refuses the extended paths that would make it, and the verifier simulated
    it the same way. FileNotFoundError is what the owner's machine says of a junction whose target is gone, and NotADirectoryError
    of one whose target has become a file.)"""
    real = os.scandir
    said = {PermissionError: (13, "Access is denied"), FileNotFoundError: (2, "The system cannot find the file specified"),
            NotADirectoryError: (20, "The directory name is invalid")}[error]

    def scandir(path="."):
        if isinstance(path, (str, bytes, os.PathLike)) and os.path.normcase(os.fsdecode(path)) == os.path.normcase(str(directory)):
            raise error(*said, os.fsdecode(path))
        return real(path)                                     # a descriptor, which shutil's cleanup lists by, among the rest
    monkeypatch.setattr(os, "scandir", scandir)


def leads_nowhere(monkeypatch, path, error=FileNotFoundError):
    """`path`, a directory the test made, shows what an entry whose target is gone shows of itself, to every call by which the
    tool, or a mutant of it, could ask about it (P4's sixth verifier, D1: nine mutants that decided "this link leads nowhere" by
    another call than the two it was first told survived). It is listed in its parent, and for that path alone each of these fails
    with `error`, FileNotFoundError, or NotADirectoryError where the target has become a file: listing it (os.scandir,
    os.listdir), a stat (os.stat, os.lstat, Path.stat, which Path.exists, is_dir, is_file, lstat and iterdir go by), resolving it
    (os.path.realpath with strict, which Path.resolve(strict=True) calls); and these say no: os.path.exists, isdir and isfile,
    os.access. Not told, and so not reached: the DirEntry of a listing, a descriptor, open(). It stands in for a junction whose
    target is gone, which the owner's machine cannot make without being unable to remove it (its own lstat of such a junction
    fails too, and with it the checker's test of a link: the stated limit, and what tell_links is for). Because lstat is told gone,
    os.path.lexists of the stand-in is false (ntpath's is os.lstat), and a test asks the parent's listing whether it is there."""
    target = Path(path)
    said = (2, "The system cannot find the path specified") if error is FileNotFoundError else (20, "The directory name is invalid")

    def same(p):
        return isinstance(p, (str, bytes, os.PathLike)) and os.path.normcase(os.fsdecode(p)) == os.path.normcase(str(target))

    def gone(p):
        return error(*said, os.fsdecode(p))

    unlistable(monkeypatch, path, error)                                                       # os.scandir
    real_listdir, real_access, real_realpath, real_path_stat = os.listdir, os.access, os.path.realpath, Path.stat

    def raising(real):
        def call(p, *args, **kwargs):
            if same(p):
                raise gone(p)
            return real(p, *args, **kwargs)
        return call

    def listdir(p=None):
        if same(p):
            raise gone(p)
        return real_listdir() if p is None else real_listdir(p)

    def realpath(p, *args, **kwargs):
        if same(p) and kwargs.get("strict", False):
            raise gone(p)
        return real_realpath(p, *args, **kwargs)

    def path_stat(self, *args, **kwargs):
        if self == target:
            raise gone(self)
        return real_path_stat(self, *args, **kwargs)

    monkeypatch.setattr(os, "stat", raising(os.stat))
    monkeypatch.setattr(os, "lstat", raising(os.lstat))
    monkeypatch.setattr(os, "listdir", listdir)
    monkeypatch.setattr(os, "access", lambda p, *args, **kwargs: False if same(p) else real_access(p, *args, **kwargs))
    for name in ("exists", "isdir", "isfile"):
        monkeypatch.setattr(os.path, name, lambda p, _real=getattr(os.path, name): False if same(p) else _real(p))
    monkeypatch.setattr(os.path, "realpath", realpath)
    monkeypatch.setattr(Path, "stat", path_stat)


def assert_gone_to_every_call(path, error=FileNotFoundError):
    """The control that each patch of leads_nowhere took: every call it tells fails with `error`, or says no, for `path`, which is
    still listed in its parent, and answers a resolve that is not strict."""
    path = Path(path)
    calls = (("os.stat", lambda: os.stat(path)), ("os.lstat", lambda: os.lstat(path)), ("Path.stat", path.stat),
             ("Path.lstat", path.lstat), ("os.scandir", lambda: os.scandir(path)), ("os.listdir", lambda: os.listdir(path)),
             ("Path.iterdir", lambda: list(path.iterdir())), ("os.path.realpath", lambda: os.path.realpath(path, strict=True)),
             ("Path.resolve", lambda: path.resolve(strict=True)))
    for name, call in calls:
        try:
            call()
        except error:
            continue
        raise AssertionError(f"{name} of {path.name} did not raise {error.__name__}")
    says = {"os.path.exists": os.path.exists(path), "os.path.isdir": os.path.isdir(path), "os.path.isfile": os.path.isfile(path),
            "os.path.lexists": os.path.lexists(path), "os.access": os.access(path, os.F_OK), "Path.exists": path.exists(),
            "Path.is_dir": path.is_dir(), "Path.is_file": path.is_file()}
    assert not any(says.values()), [name for name, yes in says.items() if yes]
    assert os.path.realpath(path) and path.name in os.listdir(path.parent)


def assert_there_to_every_call(path):
    """The same calls, asked of a path that leads somewhere, answer as they do: leads_nowhere tells one path alone, and not its name."""
    path = Path(path)
    os.stat(path)
    os.lstat(path)
    os.listdir(path)
    path.stat()
    path.lstat()
    list(path.iterdir())
    with os.scandir(path) as listing:
        list(listing)
    assert os.path.realpath(path, strict=True) and path.resolve(strict=True)
    assert os.path.exists(path) and os.path.isdir(path) and not os.path.isfile(path) and os.path.lexists(path) and os.access(path, os.F_OK)
    assert path.exists() and path.is_dir() and not path.is_file()


@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_a_directory_the_host_cannot_list_is_never_passed_over_both_modes_fail_and_name_it(tmp_path, capsys, monkeypatch, mode):
    root = profile_copy(tmp_path / "root")
    stray = root / "profile" / "stray"
    (stray / "deeper").mkdir(parents=True)
    (stray / "x.txt").write_bytes(b"x")
    before = snapshot(root / "profile")
    unlistable(monkeypatch, stray)
    assert gen.main([mode], root=root) == 3
    said = capsys.readouterr()
    assert said.out == "" and said.err.count("\n") == 1 and said.err.isascii()
    assert said.err.startswith("FAILED: the generator itself failed, Unlistable: profile" "/stray/ is a directory the host cannot "
                               "list (PermissionError), so nothing under it can be checked or cleared; ")
    assert said.err.endswith("this is not a verdict\n" if mode == "--check" else "it had finished writing no file\n")
    monkeypatch.undo()
    assert snapshot(root / "profile") == before                              # nothing was removed or written


def test_the_walk_raises_for_a_directory_it_cannot_list_at_any_depth_and_for_profile_itself(tmp_path, monkeypatch):
    base = tmp_path / "profile"
    (base / "a" / "b").mkdir(parents=True)
    unlistable(monkeypatch, base / "a" / "b")
    with pytest.raises(gen.Unlistable, match=r"profile" r"/a/b/ is a directory the host cannot list \(PermissionError\)"):
        list(gen.walk(base))
    monkeypatch.undo()
    unlistable(monkeypatch, base)
    with pytest.raises(gen.Unlistable, match=r"profile/ is a directory the host cannot list \(PermissionError\)"):
        list(gen.walk(base))


def test_as_a_process_a_directory_the_host_cannot_list_is_exit_3_one_line_and_named(tmp_path):
    root = tree(tmp_path / "t")
    (root / "profile" / "stray").mkdir()
    prelude = ("import os\n"
               "real = os.scandir\n"
               "def scandir(path='.'):\n"
               "    if isinstance(path, str) and os.path.basename(path) == 'stray':\n"
               "        raise PermissionError(13, 'Access is denied', path)\n"
               "    return real(path)\n"
               "os.scandir = scandir")
    done = run_patched(root, ["--check"], prelude, tmp_path)
    assert done.returncode == 3 and done.stdout == "" and done.stderr.count("\n") == 1, done.stderr[-300:]
    assert "Unlistable: profile" "/stray/ is a directory the host cannot list (PermissionError)" in done.stderr


# -- a junction whose target is gone, on a host that opens none: the stated limit ---------------------------------------------------------
# MEASURED by the lead on 2026-10-30, with real junctions that were then taken away by making their targets again, and again by P4's
# builder and the sixth verifier on 2026-10-31: the host's lstat of such a junction raises FileNotFoundError (NotADirectoryError where
# its target has become a file), so the checker's test of a link says nothing is there. What the tool then does is what these tests
# hold, with the host's facts told and no junction made.
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_where_the_host_opens_no_dangling_junction_one_at_profile_is_a_tree_whose_context_is_missing_and_nothing_is_made(
        tmp_path, capsys, mode):
    """The checker's test finds no link at profile/ and nothing can be read behind it: both modes refuse the tree as one whose
    context is missing, exit 1, and make, write and remove nothing. Held with nothing at profile/, which is what every read of
    a junction that leads nowhere finds."""
    root = tmp_path / "root"
    root.mkdir()
    assert not gen.is_link(root / "profile")
    assert gen.main([mode], root=root) == 1
    said = capsys.readouterr()
    assert said.out == "" and said.err == "profile/context.jsonld is missing: run tools/gen_vocabulary.py --write\n"
    assert os.listdir(root) == []


@pytest.mark.parametrize("error", [FileNotFoundError, NotADirectoryError])
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_where_the_host_opens_no_dangling_junction_at_p0s_context_it_is_a_context_that_is_missing_and_nothing_is_written(
        tmp_path, capsys, monkeypatch, mode, error):
    """The one place below profile/ where the answer is not exit 3 (the sixth verifier, MEASURED with real junctions, target gone
    and target become a file): P0's context.jsonld is read, not listed, and a read that fails with FileNotFoundError or
    NotADirectoryError is a context that is missing, exit 1, in both modes. Held with no file there, which is what a read of a
    junction whose target is gone finds, and with a read that fails with NotADirectoryError, which is what a read of one whose
    target has become a file finds; nothing under profile/ is written, removed or made."""
    root = profile_copy(tmp_path / "root")
    context = root / "profile" / "context.jsonld"
    before = snapshot(root / "profile")
    if error is FileNotFoundError:
        context.unlink()
        before = snapshot(root / "profile")
    else:
        real = Path.read_bytes

        def refusing(self):
            if self == context:
                raise NotADirectoryError(20, "The directory name is invalid", str(self))
            return real(self)
        monkeypatch.setattr(Path, "read_bytes", refusing)
    assert not gen.is_link(context)
    assert gen.main([mode], root=root) == 1
    said = capsys.readouterr()
    assert said.out == "" and said.err == "profile/context.jsonld is missing: run tools/gen_vocabulary.py --write\n"
    monkeypatch.undo()
    assert snapshot(root / "profile") == before


@pytest.mark.parametrize("error", [FileNotFoundError, NotADirectoryError])
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_where_the_host_opens_no_dangling_junction_one_below_profile_is_a_directory_it_cannot_list_and_both_modes_fail_naming_it(
        tmp_path, capsys, monkeypatch, mode, error):
    """The checker's test finds no link below profile/, so the walk takes the entry for a directory and lists it, and the host
    says FileNotFoundError, or NotADirectoryError where the target has become a file: both modes fail, exit 3, naming the
    directory and the error, before anything is removed or written. Held with the stand-in of the test of a link that leads
    nowhere, an empty directory shown to lead nowhere to every call that could ask (leads_nowhere), and the tool not told that it
    is a link, so that its own test finds none, as the host's does: the same entry, told, is listed and removed."""
    root = profile_copy(tmp_path / "root")
    jct = root / "profile" / "jct"
    jct.mkdir()
    before = snapshot(root / "profile")
    leads_nowhere(monkeypatch, jct, error)
    assert not gen.is_link(jct)                                     # no link to the tool: its lstat fails, as the host's does
    assert_gone_to_every_call(jct, error)
    assert gen.main([mode], root=root) == 3
    said = capsys.readouterr()
    assert said.out == "" and said.err.count("\n") == 1 and said.err.isascii()
    assert said.err.startswith("FAILED: the generator itself failed, Unlistable: profile" "/jct/ is a directory the host cannot "
                               f"list ({error.__name__}), so nothing under it can be checked or cleared; ")
    assert said.err.endswith("this is not a verdict\n" if mode == "--check" else "it had finished writing no file\n")
    monkeypatch.undo()
    assert snapshot(root / "profile") == before                              # nothing was removed or written


# -- a read-only file: --write's exit 3 stays, a stated limit --------------------------------------------------------------------------------
def read_only(path):
    os.chmod(path, stat.S_IREAD)


def writable(path):
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)


def test_a_read_only_rendered_file_is_not_replaced_where_the_host_will_not_and_write_fails_naming_the_files_it_finished(
        tmp_path, capsys):
    """The stated limit (docs/P4.md, the tool's docstring): on Windows a file with the read-only attribute is neither replaced
    nor removed, and --write fails, exit 3, after the files it had written; where the directory, not the file, decides, it is
    replaced. --check is not affected. The temporary file is gone either way."""
    root = profile_copy(tmp_path / "root")
    place = root / "profile" / "validator" / "qro-crate" / "must" / "2_terms.ttl"
    place.write_bytes(place.read_bytes() + b"# edited" + bytes([10]))
    read_only(place)
    try:
        assert gen.main(["--check"], root=root) == 1
        capsys.readouterr()
        code = gen.main(["--write"], root=root)
        err = capsys.readouterr().err
        if os.name == "nt":
            assert code == 3 and "PermissionError" in err and "it had finished writing EXAMPLES.md, README.md" in err, err
            assert place.read_bytes() != RENDERED["validator/qro-crate/must/2_terms.ttl"]
        else:
            assert code == 0 and place.read_bytes() == RENDERED["validator/qro-crate/must/2_terms.ttl"]
        assert [p for p in (root / "profile").rglob("*") if p.name.endswith(gen.TEMP)] == []
    finally:
        writable(place)


def test_a_read_only_stray_file_is_not_removed_where_the_host_will_not_and_write_fails(tmp_path, capsys):
    root = profile_copy(tmp_path / "root")
    stray = root / "profile" / "stray.txt"
    stray.write_bytes(b"x")
    read_only(stray)
    try:
        assert gen.main(["--check"], root=root) == 1
        capsys.readouterr()
        code = gen.main(["--write"], root=root)
        err = capsys.readouterr().err
        if os.name == "nt":
            assert code == 3 and "PermissionError" in err and "it had finished writing no file" in err, err
            assert stray.exists()
        else:
            assert code == 0 and not stray.exists()
    finally:
        if stray.exists():
            writable(stray)


def test_the_limits_of_the_tool_are_stated_on_the_page_and_in_its_docstring():
    """The ruling of 2026-10-26T18:56:48Z: a read-only file's exit 3 stays, stated as a limit. The two places that state the tool's
    limits say each of them, in the words the tests above hold."""
    page = " ".join((ROOT / "docs" / "P4.md").read_text(encoding="utf-8").split())
    doc = " ".join(tool_docstring().split())
    for text in (page, doc):
        assert "A file with the read-only attribute is neither removed nor replaced on Windows" in text
        assert ("--write fails on it, exit 3, and names the files it had finished writing" in text
                or "`--write` fails on it, exit 3, naming the files it had finished writing" in text)
        assert "pipe or a device" in text
    assert "compared by Python's `casefold`, not by the host's own table" in page


def test_the_limit_of_a_junction_whose_target_is_gone_is_stated_on_the_page_and_in_its_docstring():
    """The rulings of 2026-10-31T03:38:50Z and 05:26:29Z: on a host that opens no dangling junction, the checker's test of a link
    finds none there; with profile/ itself one, or at P0's context.jsonld, both modes refuse the tree, exit 1, as one whose
    context is missing; with any other below, both fail, exit 3, naming a directory the host cannot list; neither writes or
    removes anything; and the owner's machine is the one it was found on, on 2026-10-30. The two places that state the tool's
    limits say it in these words, and the tests of the stated limit hold what it says. The docstring is read from the tool's
    source text, which python -OO does not empty."""
    page = " ".join((ROOT / "docs" / "P4.md").read_text(encoding="utf-8").split())
    doc = " ".join(tool_docstring().split())
    for text in (page, doc):
        for words in ("A junction whose target is gone is a link only on a host that can open it, and the owner's machine cannot "
                      "(found so on 2026-10-30",
                      "NotADirectoryError",
                      "where its target has become a file",
                      "so the checker's test of a link finds none there",
                      "or with one at P0's",
                      "both modes refuse the tree, exit 1, as one whose context is missing",
                      "both fail, exit 3, naming a directory the host cannot list",
                      "neither writes or removes anything"):
            assert words in text, words
        assert "this machine" not in text                                       # a published page names the owner's, and the day


def test_the_teardown_removes_each_link_under_a_folder_and_nothing_behind_it_and_enters_none(tmp_path):
    """remove_links_under, which ends every test of this module that makes a junction (the autouse fixture above): the links go,
    at any depth and to the folder itself, and what they lead to stays, byte for byte; a link in a folder that only a link leads to
    is not found, since none is entered; no folder is removed; and a second call finds nothing."""
    top, elsewhere, third = tmp_path / "top", tmp_path / "elsewhere", tmp_path / "third"
    for folder in (top / "a" / "b", elsewhere, third):
        folder.mkdir(parents=True)
    (top / "keep.txt").write_bytes(b"kept" + bytes([10]))
    (top / "empty").mkdir()                                      # a folder is no link, empty as it is
    (elsewhere / "victim.txt").write_bytes(b"not under top" + bytes([10]))
    (third / "emptydir").mkdir()
    link_dir(elsewhere / "inner", third)                         # in a folder that only a link leads to: a walk through a link finds it
    link_dir(top / "a" / "jct", elsewhere)
    link_dir(top / "a" / "b" / "jct2", third)
    link_dir(top / "loop", top)                                  # to the folder itself: entering it would not end
    before_elsewhere, before_third = snapshot(elsewhere), snapshot(third)
    assert before_elsewhere["inner"] == "link"
    removed = remove_links_under(top)
    assert sorted(Path(p).relative_to(top).as_posix() for p in removed) == ["a/b/jct2", "a/jct", "loop"]
    assert sorted(os.listdir(top)) == ["a", "empty", "keep.txt"] and os.listdir(top / "a") == ["b"] and os.listdir(top / "a" / "b") == []
    assert os.listdir(top / "empty") == []
    assert (top / "keep.txt").read_bytes() == b"kept" + bytes([10])
    assert snapshot(elsewhere) == before_elsewhere and snapshot(third) == before_third      # nothing behind a link, "inner" still there
    assert remove_links_under(top) == []
    os.rmdir(elsewhere / "inner")                                # the fixture would, too
