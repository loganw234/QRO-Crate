"""tools/gen_profile.py against the states a tree can be in that nobody makes by accident (P4's fourth verifier, round 4, MEASURED,
and the lead's rulings of 2026-10-26T18:56:48Z): profile/ itself a link; a link or a directory where P0's context goes; a hard
link at a rendered path; a name that differs only by case from a rendered name or from P0's context; a directory where a file
goes; a directory the host cannot list; a read-only file. Each is held in process and, where it matters, as the process a user
runs, in both modes, with what is behind a link, byte for byte, as the witness that nothing behind it was read, changed or
removed, and with a spy (watch_below in p4_helpers.py) on the calls of os, os.path, open and pathlib.Path that could follow the link
or read through it, at profile/ itself and at each place a rendered directory goes. The spy notes every path a call is given, by
position or by keyword, and goes in before the tool is loaded, so that a name the tool binds as it is loaded (a from-import of a
function of os, a module-level alias, a default argument) is the spy's; a control makes every call it wraps, by position and by
keyword, and demands that it saw each. What it does not see: a DirEntry of a listing (os.walk asks one is_dir()), a handle already
open, ctypes, a process, a function another module bound before it went in, a path spelt as an 8.3 short name or reached through
another link to the same directory, and a module of the standard library that reaches the host some other way (nt, posix, _io,
shutil, glob...), which is why the tool imports only the modules it does and a test holds that
(test_the_tool_imports_only_the_modules_the_spy_covers). A link is a real junction, made without privilege, where the host makes
junctions (link_dir in p4_sweeps.py), and its target is there when the test ends: the module's fixture removes the links a failing
test strands (remove_links_under in p4_helpers.py).

A junction whose target is gone is made by no test: the owner's machine cannot open one (the stated limit, docs/P4.md), and one can
be taken away again only by making its target again (CLAUDE.md item 10), which a test that failed first would not do. Where a host
opens one, the tool must list it as a link, never enter it and remove it, and a test of that stands in for the junction by an entry
that is not there at all and that only its parent's listing shows, with the tool told that a link stands at its path (dangling_link
and tell_links in p4_helpers.py, and a control that each telling took). The stand-in tells three calls of its path:
os.unlink raises PermissionError, os.rmdir drops the entry from the listing, and os.access answers, yes as the owner's machine does
and no as another host might, so that each told test runs both ways. Told NotADirectoryError, the host's answer for a junction whose
target has become a file, it makes os.lstat, os.stat, os.scandir and os.listdir of its path raise that too, as its docstring says.
Where the host does not open one, a test tells the tool what the
owner's machine says of it. So these tests hold the tool's answer to what the host says, and not the host: what the owner's machine
says is the lead's measurement of 2026-10-30 and the verifiers' and P4.2's builder's of 2026-10-31, and nothing here would notice if
that machine opened such a junction again."""
import ast
import builtins
import io
import os
import shutil
import stat
import types
from pathlib import Path

import p4_helpers
import pytest
from p4_helpers import (ROOT, dangling_link, dangling_missed, load_file, load_tool, outside_dir, profile_copy, remove_links_under,
                        run_patched, run_tool, snapshot, spy_missed, tell_links, tree, watch_below)
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
    watch = watch_below(monkeypatch, root / "profile", load=True)               # the tool is loaded after the spy goes in
    assert spy_missed(watch, root / "profile") == []                            # the control: the spy took, every wrapper, by position and keyword
    assert watch.tool.main([mode], root=root) == 1
    said = capsys.readouterr()
    assert said.out == "" and said.err == gen.LINKED + "\n"
    assert watch.calls == [], watch.calls                                       # nothing under it was listed, walked, opened or asked of
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


ACCESS = pytest.mark.parametrize("access", [True, False], ids=["os.access says yes", "os.access says no"])


@ACCESS
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_profile_itself_a_link_to_nothing_is_a_link_too(tmp_path, capsys, monkeypatch, mode, access):
    """A junction whose target is gone leads nowhere, and a host that opens it calls it a link, so profile/ is refused as one that
    leads somewhere is (the tests above). The owner's machine opens none, and a junction it cannot open it cannot remove either
    (the stated limit, docs/P4.md): none is made. Nothing at all stands at profile/ and only the listing of its parent shows an
    entry there (dangling_link), the tool is told that a link stands at the path (tell_links), and it must refuse the tree by that
    answer before it reads anything: its sentence is the link's, and not that of a context that is not there, which is what a
    tree with nothing at profile/ gets from a tool that was not told (the first test of the stated limit, below, holds that). This
    holds the tool's answer to what a host that opens such a junction says, and not the host. It runs with os.access answering yes,
    as the owner's machine does, and no, as another host might: the tool decides by neither (P4.2's first verifier, note 2)."""
    root = tmp_path / "root"
    root.mkdir()
    (tmp_path / "elsewhere" / "profile").mkdir(parents=True)                               # the same name at another path: there, to the end
    profile = root / "profile"
    stand = dangling_link(monkeypatch, profile, access=access)
    assert os.access(profile, os.F_OK) is access                                          # the answer asked for is the answer told
    real = tell_links(monkeypatch, gen, profile)
    assert gen.is_link(profile) and not real(profile) and not os.path.lexists(profile)     # the controls: told, and not made
    assert not gen.is_link(root) and not gen.is_link(tmp_path / "elsewhere" / "profile")   # at that path alone, not at its name
    assert dangling_missed(stand, others=(root, tmp_path / "elsewhere" / "profile")) == []
    assert gen.main([mode], root=root) == 1
    said = capsys.readouterr()
    assert said.out == "" and said.err == gen.LINKED + "\n"
    assert stand.listed and stand.real_names() == []                # still shown, and nothing was made: no profile/, no file beside it


@pytest.mark.parametrize("error", [IsADirectoryError, PermissionError])
def test_remove_link_falls_back_to_rmdir_where_unlink_will_not_take_a_directory_link_and_still_takes_nothing_behind_it(
        tmp_path, monkeypatch, error):
    """A symbolic link to a directory is removed with rmdir on Windows, which the owner's machine cannot make one of (WinError 1314): the
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


@ACCESS
def test_a_link_below_profile_that_leads_nowhere_is_listed_and_removed_like_any_other(tmp_path, capsys, monkeypatch, access):
    """A junction whose target is gone is, in its parent's listing, an entry that cannot itself be listed (the host says
    FileNotFoundError), and a host that opens it calls it a link. None is made (see the test above). Nothing at all stands at the
    path: the entry is shown by the listing of its parent alone, and every other call about the path is the host's own answer
    about a path where nothing is (dangling_link: P4's sixth verifier, D1, found nine mutants that decided "this link leads
    nowhere" by a call that the first stand-in did not tell, and its seventh, note 1, the calls and spellings that the ten told
    still missed; here no call is told but the three that only a link has, os.unlink and os.rmdir of it and os.access of it, so
    no other can be missed), and the tool is told that a link stands there (tell_links). The
    tool must list it as a link, never enter it, and remove it, as it does a link that leads somewhere: entering it is what the
    stand-in would answer with exit 3, as the tests of the stated limit show of the same stand-in not told. That it is gone
    after --write is read from its parent's listing. This holds the tool's answer to what a host that opens such a junction says,
    and not the host. It runs with os.access answering yes and no (P4.2's first verifier, note 2)."""
    root = profile_copy(tmp_path / "root")
    jct = root / "profile" / "jct"
    (root / "jct").mkdir()                                          # the same name at another path: there, to the end
    stand = dangling_link(monkeypatch, jct, access=access)
    assert os.access(jct, os.F_OK) is access                        # the answer asked for is the answer told
    real = tell_links(monkeypatch, gen, jct)
    assert gen.is_link(jct) and not real(jct)                       # the controls: told, and not made
    assert not gen.is_link(root / "profile") and not gen.is_link(root / "jct")                       # at that path alone
    assert dangling_missed(stand, others=(root / "jct", root / "profile", root / "profile" / "validator")) == []
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert "profile" + "/jct is a link, which no definition renders" in err
    assert "holds no file" not in err and "cannot list" not in err  # it was not entered, nor taken for a directory
    assert stand.listed
    assert gen.main(["--write"], root=root) == 0
    assert not stand.listed and "removed jct" in capsys.readouterr().out.splitlines()       # the link itself is gone
    assert "jct" not in os.listdir(root / "profile") and (root / "jct").is_dir()
    assert gen.main(["--check"], root=root) == 0


@ACCESS
def test_a_link_that_leads_nowhere_at_a_rendered_path_is_called_a_link_and_replaced_by_the_file(tmp_path, capsys, monkeypatch, access):
    """The seventh verifier's note 2: a mutant of drift() that calls a link at a rendered path a link only if it exists (the sixth
    verifier's A08) was reached by no test. The same stand-in as above, at the path of a file a definition renders: nothing stands
    there, its parent lists a junction, and the tool is told it is a link. --check says so in the words of a link at a rendered path
    (not that the file is missing, nor drifted, for the empty bytes a link is listed with are not the file's), and --write removes
    it, writes the file in its place and leaves the tree clean. The mutants that decide a link leads nowhere by what exists, in the
    walk, in the removal and in the loop (A03, A05, A06) are killed here too. This holds the tool's answer to what a host that
    opens such a junction says, and not the host. It runs with os.access answering yes and no (P4.2's first verifier, note 2)."""
    root = profile_copy(tmp_path / "root")
    place = root / "profile" / "EXAMPLES.md"
    place.unlink()                                                  # nothing stands at the rendered path ...
    stand = dangling_link(monkeypatch, place, access=access)        # ... but its parent lists a junction there
    assert os.access(place, os.F_OK) is access                      # the answer asked for is the answer told
    real = tell_links(monkeypatch, gen, place)
    assert gen.is_link(place) and not real(place) and dangling_missed(stand, others=(root / "profile",)) == []
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert "profile/EXAMPLES.md is a link, not the file its definition renders; run --write removes the link and writes the file" in err
    assert "EXAMPLES.md missing" not in err and "EXAMPLES.md DRIFTED" not in err and "EXAMPLES.md is a directory" not in err
    assert stand.listed and gen.main(["--write"], root=root) == 0
    said = capsys.readouterr().out.splitlines()
    assert not stand.listed and said.index("removed EXAMPLES.md") < said.index("wrote EXAMPLES.md")
    monkeypatch.undo()
    assert place.is_file() and place.read_bytes() == RENDERED["EXAMPLES.md"]
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


# -- a link where a rendered directory goes: the host is asked nothing below it (P4's fifth verifier, C1) ---------------------------------
PLACES = ["validator", "validator/qro-crate", "validator/qro-crate/must", "validator/qro-crate/should", "examples", "examples/fixture",
          "examples/fixture/data"]


def rendered_below(place):
    """The rendered paths below the directory `place`, relative to profile/."""
    return sorted(r for r in RENDERED if r.startswith(place + "/"))


def test_every_directory_a_rendered_file_goes_in_is_a_place_of_the_test_below():
    """The places of the next test are every directory the rendered files go in, however deep: a new one is a decision here."""
    directories = {"/".join(r.split("/")[:i]) for r in RENDERED for i in range(1, len(r.split("/")))}
    assert sorted(directories) == sorted(PLACES), sorted(directories)


@pytest.mark.parametrize("mode", ["--check", "--write"])
@pytest.mark.parametrize("place", PLACES)
def test_a_link_where_a_rendered_directory_goes_is_asked_nothing_below_it_and_the_rendered_paths_behind_it_are_told_missing(
        tmp_path, capsys, monkeypatch, place, mode):
    """The fifth verifier's C1: with a link at a place where a rendered directory goes, --check asked is_dir() of each rendered path
    behind it, five os.stat calls through the link at validator/, and said "is a directory, not the file its definition renders;
    run --write removes it" where the link's target held a directory at that path, though --write would remove the link and leave
    the directory. Now nothing below a link is asked of the host, in either mode: a real junction to a directory outside the tree,
    which holds a directory at each rendered path behind it (so that a stat through it would answer yes), and a spy (watch_below) on
    the calls of os, os.path, open and pathlib.Path that could follow it or read through it, which notes every path a call is given,
    by position or by keyword, and is in before the tool is loaded (so that a name the tool binds as it is loaded is the spy's),
    found to take by a control that makes each call both ways. The text is "missing" for each rendered path behind the link,
    whatever the link leads to, and what is behind the link is equal byte for byte after. The spy sees --write until the link is
    removed, after which the paths are the new directory's."""
    root = profile_copy(tmp_path / "root")
    below = rendered_below(place)
    assert below
    link = root / "profile" / place
    shutil.rmtree(link)                                                     # a real directory with no link in it
    outside = outside_dir(tmp_path)
    for rel in below:                                                       # behind the link: a directory at every rendered path under it
        (outside / rel[len(place) + 1:]).mkdir(parents=True, exist_ok=True)
    link_dir(link, outside)
    before = snapshot(outside)
    assert all(os.path.isdir(link / rel[len(place) + 1:]) for rel in below)                 # through the link each is a directory
    watch = watch_below(monkeypatch, link, load=True)                       # the tool is loaded after the spy goes in
    assert spy_missed(watch, link) == []                                    # the control: every wrapper of the spy took, by position and keyword
    code = watch.tool.main([mode], root=root)
    said = capsys.readouterr()
    assert watch.calls == [], watch.calls                                   # nothing below the link was listed, opened or asked of
    monkeypatch.undo()
    assert snapshot(outside) == before
    if mode == "--check":
        assert code == 1 and os.path.lexists(link)
        assert f"profile/{place} is a link, which no definition renders; run --write removes the link, and nothing behind it" in said.err
        for rel in below:
            assert f"profile/{rel} missing; run --write" in said.err, rel
        assert "is a directory, not the file" not in said.err
    else:
        assert code == 0 and said.out.splitlines()[0] == f"removed {place}"
        assert not gen.is_link(link) and link.is_dir()               # the link is gone, and a directory of the tool's own stands there
        assert gen.main(["--check"], root=root) == 0


def test_the_spy_finds_the_calls_the_old_drift_made_at_a_rendered_path_behind_a_link(tmp_path, monkeypatch):
    """The spy shown failing on its plant: the code C1 found, `(root / "profile" / rel).is_dir()` of a rendered path that is not on
    disk, is a stat through the link, and the spy finds it, one Path.is_dir and the os.stat it makes for each path."""
    outside = outside_dir(tmp_path)
    link_dir(tmp_path / "link", outside)
    watch = watch_below(monkeypatch, tmp_path / "link")
    for rel in ("qro-crate/profile.ttl", "qro-crate/must/1_structure.ttl"):
        (tmp_path / "link" / rel).is_dir()                          # what drift() once asked of a rendered path behind a link
    seen = [what for what, _ in watch.calls]
    monkeypatch.undo()
    assert seen.count("Path.is_dir") == 2 and "os.stat" in seen
    os.rmdir(tmp_path / "link")


def test_the_spy_wraps_every_call_the_ruling_names_and_the_ones_that_could_follow_a_link_like_them(tmp_path, monkeypatch):
    """P4.2's ruling 4 names the calls the spy is to see below a link: os.stat, os.lstat, os.scandir, os.listdir, open, Path.is_dir
    'and the like'. They are written here again, and not read from the spy's own lists, which a call left out of would also leave
    out of what the control of spy_missed checks."""
    named = {"os.stat", "os.lstat", "os.scandir", "os.listdir", "os.walk", "os.access", "os.open", "open", "io.open",
             "os.path.exists", "os.path.isdir", "os.path.isfile", "os.path.realpath", "os.path.getsize",
             "Path.stat", "Path.lstat", "Path.exists", "Path.is_dir", "Path.is_file", "Path.iterdir", "Path.glob", "Path.rglob",
             "Path.open", "Path.read_bytes", "Path.read_text", "Path.resolve", "Path.write_bytes", "Path.write_text", "Path.touch",
             "Path.mkdir", "Path.rmdir", "Path.unlink", "Path.rename"}
    watch = watch_below(monkeypatch, tmp_path / "link")
    assert named <= watch.wrapped, sorted(named - watch.wrapped)


def test_the_spy_reads_every_path_a_call_is_given_by_keyword_and_the_second_by_position_too(tmp_path, monkeypatch):
    """P4.2's first verifier, D1: the spy noted the first two positional arguments of a call and no keyword, so a call given its path
    by keyword was not seen: `os.listdir(path=...)`, `os.scandir(path=...)` and `open(file=...)` at profile/ itself, before the
    tool refused the link, were killed by main's test (which noted the first keyword value of a call with no positional one) and
    survived P4.2's, and twelve of the fourteen keyword calls at the seven places of C1. The calls are written here again, and not
    read from the table the control of spy_missed goes by: each is seen, by its own name, with the path it was given. So are the
    calls that take two paths, with the first apart from the link and the second below it, by position and by keyword."""
    outside = outside_dir(tmp_path)
    link = tmp_path / "link"
    link_dir(link, outside)
    below = link / "no such folder" / "x"
    apart = tmp_path / "no such folder apart"
    watch = watch_below(monkeypatch, link)
    calls = {"os.stat": lambda p: os.stat(path=p), "os.lstat": lambda p: os.lstat(path=p), "os.listdir": lambda p: os.listdir(path=p),
             "os.scandir": lambda p: os.scandir(path=p), "os.walk": lambda p: os.walk(top=p), "open": lambda p: open(file=p, mode="rb"),
             "io.open": lambda p: io.open(file=p, mode="rb"), "os.access": lambda p: os.access(path=p, mode=os.F_OK),
             "os.utime": lambda p: os.utime(path=p), "os.path.exists": lambda p: os.path.exists(path=p),
             "os.path.isdir": lambda p: os.path.isdir(s=p), "os.path.getsize": lambda p: os.path.getsize(filename=p),
             "os.path.realpath": lambda p: os.path.realpath(path=p), "os.chdir": lambda p: os.chdir(path=p),
             "Path.rename": lambda p: Path(tmp_path / "elsewhere").rename(target=p),
             # the second path alone below the link, by position and by keyword
             "os.rename": lambda p: os.rename(apart, p), "os.replace": lambda p: os.replace(src=apart, dst=p),
             "os.link": lambda p: os.link(apart, p), "os.path.samefile": lambda p: os.path.samefile(f1=apart, f2=p),
             "Path.replace": lambda p: Path(apart).replace(p), "Path.samefile": lambda p: Path(apart).samefile(other_path=p)}
    for what, call in calls.items():
        try:
            call(below)
        except OSError:                                             # nothing is there: the question is whether the spy was told first
            pass
        assert [path for seen, path in watch.calls if seen == what] == [os.fspath(below)], (what, watch.calls)
        watch.calls.clear()
    monkeypatch.undo()
    os.rmdir(link)


def test_the_spy_matches_a_path_however_it_is_spelt_that_names_the_same_path(tmp_path, monkeypatch):
    """The spy compares the path of a call with the link as absolute, normalised paths (case, separators, `.` and `..`, a trailing
    separator, the working directory a relative path is taken from) with the extended-length prefix of Windows taken off. The
    spellings a tool might use for a path below the link are each seen. Not an 8.3 short name, nor a way through another link."""
    outside = outside_dir(tmp_path)
    link = tmp_path / "link"
    link_dir(link, outside)
    below = link / "no such folder" / "x"
    spellings = {"a trailing separator": str(below) + os.sep, "a . component": os.path.join(str(link), ".", "no such folder", "x"),
                 "a .. component": os.path.join(str(link), "no such folder", "..", "no such folder", "x")}
    if os.path.splitdrive(str(below))[0].lower() == os.path.splitdrive(os.getcwd())[0].lower():       # a relative path needs one drive
        spellings["the working directory"] = os.path.relpath(below)
    if os.name == "nt":                                              # a host that ignores case, and has the extended-length prefix
        spellings.update({"upper case": str(below).upper(), "forward slashes": str(below).replace(os.sep, "/"),
                          "the extended-length prefix": "\\\\?\\" + str(below)})
    watch = watch_below(monkeypatch, link)
    for what, spelling in spellings.items():
        try:
            os.stat(spelling)
        except OSError:
            pass
        assert [seen for seen, _ in watch.calls] == ["os.stat"], (what, watch.calls)
        watch.calls.clear()
    monkeypatch.undo()
    os.rmdir(link)


BOUND_EARLY = """import os
from io import open as from_io_open
from os import listdir as from_os_listdir, scandir as from_os_scandir, stat as from_os_stat
from os.path import exists as from_path_exists, isdir as from_path_isdir

alias = os.stat


def with_a_default(path, call=os.lstat):
    return call(path)


def ask(path):
    for call in (from_os_stat, from_os_listdir, from_os_scandir, from_path_exists, from_path_isdir, alias, with_a_default):
        try:
            call(path)
        except OSError:
            pass
    try:
        from_io_open(path, "rb")
    except OSError:
        pass
"""


def test_the_spy_sees_a_name_a_module_binds_as_it_is_loaded_after_it_and_not_one_it_bound_before(tmp_path, monkeypatch):
    """P4.2's first verifier, D1: a name bound before the spy goes in is not seen at all (`from os import stat`, a module-level
    `alias = os.stat`, a default argument, `from io import open`). So the tests load the tool after the spy (watch_below(load=True)),
    and this is the control that the order is what matters: the same module, loaded before the spy and after it, asked about a path
    below a link. Before: nothing is seen, for each name is the standard library's own. After: each name is the spy's, and every
    call is seen."""
    plant = tmp_path / "plant_bound_early.py"
    plant.write_text(BOUND_EARLY, encoding="utf-8")
    outside = outside_dir(tmp_path)
    link = tmp_path / "link"
    link_dir(link, outside)
    below = link / "no such folder" / "x"
    before = load_file(plant, "plant_before_the_spy")
    watch = watch_below(monkeypatch, link)
    after = load_file(plant, "plant_after_the_spy")
    before.ask(below)
    assert watch.calls == [], watch.calls                           # bound before: the standard library's own functions
    after.ask(below)
    assert {what for what, _ in watch.calls} == {"os.stat", "os.lstat", "os.listdir", "os.scandir", "os.path.exists", "os.path.isdir",
                                                 "io.open"}, watch.calls
    assert len(watch.calls) == 8                                    # from os import stat and the alias are both os.stat
    monkeypatch.undo()
    os.rmdir(link)


def test_watch_below_loads_the_tool_after_the_spy_is_in_and_not_before(tmp_path, monkeypatch):
    """The order is the point of `load`, which the test above shows: watch_below(load=True) asks for the tool when the spy is in
    (every function it replaces is the spy's by then), so a name the tool binds as it is loaded is the spy's."""
    originals = (os.stat, os.listdir, os.path.exists, builtins.open, Path.is_dir)
    asked = []

    def probe():
        asked.append((os.stat, os.listdir, os.path.exists, builtins.open, Path.is_dir))
        return types.SimpleNamespace(remove_link=lambda path: None)
    monkeypatch.setattr(p4_helpers, "load_tool", probe)
    watch = watch_below(monkeypatch, tmp_path / "link", load=True)
    assert len(asked) == 1 and watch.tool is not None
    assert all(now is not before for now, before in zip(asked[0], originals)), "the tool was asked for before the spy was in"


# What the tool imports, all of it (P4.2's first verifier, D1). The spy sees os, os.path, open and pathlib.Path, and the tool is loaded
# after it, so a name the tool binds as it is loaded is the spy's; a module that reaches the host another way is one it does not see
# (nt, posix, _io, shutil, glob, ctypes, subprocess), so the tool imports none, and no way to one that is not an import by name. A new
# import is a decision here.
PLAIN_IMPORTS = {"argparse", "difflib", "os", "sys", "textwrap"}
FROM_IMPORTS = {("pathlib", "Path"), ("qro", "canonical"), ("qro", "checker"), ("qro", "p4_profile"), ("qro", "vocabulary"),
                ("qro.__main__", "escape")}
BY_NO_NAME = {"__import__", "eval", "exec"}


def imports_outside(source):
    """The imports of `source` that are not the tool's own, as `import x` or `from x import y`, and the ways to a module that is no
    import by name (__import__, eval, exec, sys.modules), however deep in the source they stand."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found += [f"import {a.name}" for a in node.names if a.name not in PLAIN_IMPORTS]
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            found += [f"from {module} import {a.name}" for a in node.names if (module, a.name) not in FROM_IMPORTS]
        elif isinstance(node, ast.Name) and node.id in BY_NO_NAME:
            found.append(node.id)
        elif isinstance(node, ast.Attribute) and node.attr == "modules":                    # sys.modules, or os.sys.modules
            found.append(".modules")
    return sorted(found)


def test_the_tool_imports_only_the_modules_the_spy_covers():
    assert imports_outside((ROOT / "tools" / "gen_profile.py").read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("line", ["import nt", "import posix", "import _io", "import io", "import shutil", "import glob", "import ctypes",
                                  "import subprocess", "import tempfile", "import importlib", "import os.path", "from os import stat",
                                  "from os import path", "from os.path import exists", "from io import open", "from shutil import rmtree",
                                  "from pathlib import PurePath", "from pathlib import Path as P, PurePath", "from . import checker",
                                  "from .qro import checker", "from qro import reader", "x = __import__('nt')", "exec('import nt')", "eval('1')",
                                  "import sys\nsys.modules['nt']", "x = os.sys.modules['nt']", "def f():\n    import nt",
                                  "def g():\n    from os import stat", "try:\n    import nt\nexcept ImportError:\n    pass"])
def test_the_import_guard_fails_a_planted_module_that_reaches_the_host_another_way(line):
    """The guard shown failing on its plants, each written here and not read from the guard's sets: a module of the standard
    library the spy does not wrap, a from-import of a function (which would bind a name before the spy), a name of the package that
    is not the tool's own, and the ways to a module that is no import by name. A module that imports what the tool does passes."""
    assert imports_outside("import os\nimport sys\n" + line + "\n") != [], line
    assert imports_outside("import os\nimport sys\nfrom pathlib import Path\nfrom qro import checker\nfrom qro.__main__ import escape\n") == []


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
            assert "missing; " not in said.err and "rendered by no definition" not in said.err   # said once, as a clash (with or without the C4 clause)
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


LONG_S = chr(0x17F)       # the long s: casefold() makes it an s, lower() leaves it, and NTFS keeps a name with it apart from a name with an s


@pytest.mark.parametrize("old, new", [("EXAMPLES.md", "EXAMPLE" + LONG_S + ".md"), ("context.jsonld", "context.j" + LONG_S + "onld")],
                         ids=["a rendered name", "P0's context"])
def test_two_names_that_casefold_equates_and_the_host_keeps_apart_are_a_clash_where_lower_would_call_one_a_stray(
        tmp_path, capsys, old, new):
    """The fifth verifier's gap (V06, `casefold` replaced by `lower`): `EXAMPLE` + the long s + `.md` and `context.j` + the long s +
    `onld` stand beside the rendered names on NTFS, and the tool refuses each as a clash, in both modes, and removes and writes
    nothing: the limit stated one way before ('a name the host calls the same and casefold does not is a stray') and now the other
    ('a name casefold equates and the host keeps apart is refused until one of the two is removed by hand'). With `lower`, the long
    s stays and the name is a stray, which --write would remove. Where a host does not keep the two apart (one that folds the long
    s), the second name cannot be made and this test makes the first."""
    root = profile_copy(tmp_path / "root")
    profile = root / "profile"
    (profile / new).write_bytes(b"a second name" + bytes([10]))
    names = os.listdir(profile)
    assert old in names and new in names, "the host takes the two names for one"        # a failure, not a skip: the stage fails a skip
    before = snapshot(profile)
    assert gen.fold(new) == gen.fold(old) and new.lower() != old.lower()
    for mode in ("--check", "--write"):
        assert gen.main([mode], root=root) == 1
        said = capsys.readouterr()
        assert said.err.count("differs only by case") == 1 and "it is never removed or renamed here" in said.err, said.err
        assert "rendered by no definition" not in said.err           # said once, as a clash, and not as a stray
        if mode == "--write":
            assert said.out == ""
    assert snapshot(profile) == before                              # nothing removed, nothing written, byte for byte


@pytest.mark.parametrize("old, new", [("examples", "Examples"), ("EXAMPLES.md", "examples.md")], ids=["a directory", "a file"])
def test_in_a_tree_with_a_case_clash_check_advises_the_hand_fix_first_wherever_it_would_say_run_write_and_that_fix_works(
        tmp_path, capsys, old, new):
    """The fifth verifier's C4: in a case-clash directory (`Examples/` for `examples/`, on a host that ignores case) --check told a
    stray in it 'run --write', where --write refuses that tree. --write refuses the whole tree while a clash is there, so no advice
    to run it is right without the hand fix first: every line of --check that says to run --write, of a stray, a missing file, a
    drifted one, a link, a directory where a file goes and one that holds no file, says 'once the case clash is resolved by hand,
    run --write', and the line after a diff says so too. The advice is held to work: --write refuses and changes nothing, the clash
    is renamed back by hand, and then --write succeeds."""
    root = profile_copy(tmp_path / "root")
    profile = root / "profile"
    os.rename(profile / old, profile / new)                         # the clash
    (profile / "stray.txt").write_bytes(b"x")                       # a stray
    if old == "examples":
        (profile / new / "zzz.txt").write_bytes(b"x")               # a stray in the clash directory itself (the verifier's)
    (profile / "README.md").write_bytes(RENDERED["README.md"] + b"extra" + bytes([10]))        # drift (the diff is the last lines)
    (profile / "validator" / "qro-crate" / "must" / "3_domains.ttl").unlink()      # a file missing
    (profile / "validator" / "qro-crate" / "profile.ttl").unlink()                 # a directory where a file goes
    (profile / "validator" / "qro-crate" / "profile.ttl").mkdir()
    (profile / "empty").mkdir()                                     # a directory that holds no file
    outside = outside_dir(tmp_path)
    link_dir(profile / "jct", outside)                              # a link
    (profile / "ro-crate-metadata.json").unlink()
    link_dir(profile / "ro-crate-metadata.json", outside)           # and a link where a file goes
    before, before_outside = snapshot(profile), snapshot(outside)
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    once = gen.ONCE + "run --write"
    advice = [ln for ln in err.splitlines() if "run --write" in ln or "running --write" in ln]
    assert len(advice) >= 8, err
    for line in advice:
        if line.startswith("  Fix by"):
            assert "running --write, once the case clash is resolved by hand;" in line, line
        else:
            assert once in line, line
    assert f"profile/{new}" in err and "differs only by case" in err
    for what in ("is rendered by no definition", "missing", "is a directory, not the file", "is a directory that holds no file",
                 "is a link, which no definition renders", "is a link, not the file its definition renders"):
        assert any(what in ln and once in ln for ln in advice), what
    assert snapshot(profile) == before
    assert gen.main(["--write"], root=root) == 1                    # --write refuses, and changes nothing ...
    assert "nothing is written or removed" in capsys.readouterr().err and snapshot(profile) == before
    os.rename(profile / new, profile / old)                         # ... until the clash is resolved by hand, which works
    assert gen.main(["--write"], root=root) == 0
    assert gen.main(["--check"], root=root) == 0
    assert snapshot(outside) == before_outside                      # and nothing behind either link was touched


def test_without_a_case_clash_the_advice_is_run_write_and_nothing_else(tmp_path, capsys):
    """The clause is for a tree with a clash only: the lines of a tree with none read as they did."""
    root = profile_copy(tmp_path)
    (root / "profile" / "stray.txt").write_bytes(b"x")
    (root / "profile" / "README.md").unlink()
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert "profile" "/stray.txt is rendered by no definition; run --write  Fix by" in err      # split: check_docs reads paths
    assert "profile/README.md missing; run --write  Fix by" in err
    assert gen.ONCE.strip(" ,") not in err and err.count(gen.FIX) == 2


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


@pytest.mark.parametrize("old, new, strays", [("README.md", "readme.md", False), ("README.md", "readme.md", True),
                                              ("validator/qro-crate/profile.ttl", "validator/qro-crate/PROFILE.TTL", True)],
                         ids=["at the top, empty", "at the top, with a stray", "below a directory, with a stray"])
def test_a_directory_spelt_in_another_case_at_a_rendered_files_place_is_told_what_the_host_says_it_is(
        tmp_path, capsys, old, new, strays):
    """P4.2's first verifier, note 1: a directory spelt in another case at the place of a rendered file (`readme.md/` for README.md,
    `PROFILE.TTL/` for profile.ttl) was told "is a directory, not the file its definition renders; run --write removes it" by main,
    which asked the host is_dir() of the rendered path, and "missing" by the first P4.2, which read the walk's own spellings alone.
    On a host whose lookup ignores case the directory is the rendered path (the host says so, and a file cannot be made there until
    it is gone), and the line is main's again; where the lookup keeps the two apart the path is missing, and the other name is a
    stray directory. The test asks the host first and holds the tool to what it says, so that it needs no host of its own and
    skips none. The exit, and what --write does, are the same either way."""
    root = profile_copy(tmp_path / "root")
    profile = root / "profile"
    (profile / old).unlink()
    (profile / new).mkdir()
    if strays:
        (profile / new / "x.txt").write_bytes(b"x")
    is_a_directory = os.path.isdir(profile / old)                   # the host's answer for the rendered path, not on disk by that spelling
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    if is_a_directory:
        assert f"profile/{old} is a directory, not the file its definition renders; run --write removes it" in err
        assert f"profile/{old} missing" not in err
    else:
        assert f"profile/{old} missing; run --write" in err
        assert f"profile/{old} is a directory" not in err
    assert gen.main(["--write"], root=root) == 0
    assert (profile / old).is_file() and (profile / old).read_bytes() == RENDERED[old]
    assert gen.main(["--check"], root=root) == 0


def test_a_link_spelt_in_another_case_than_the_directory_it_stands_for_is_asked_nothing_below_it_either(tmp_path, capsys, monkeypatch):
    """The way to a rendered path is asked from the top by the host's own lookup (behind_a_link), so a link spelt `Validator` stands
    on the way to validator/... on a host that ignores case and is found as the link it is, and nothing is asked below it; where
    the lookup keeps the two names apart the way does not lead through it, and there is nothing below it to ask. Either way the
    rendered paths that are not on disk are told missing, the link is listed as one no definition renders, and --write removes it,
    writes the directory in its place and touches nothing behind the link. A directory behind it holds a directory at every rendered
    path (so that a stat through it would answer yes); the spy is the one of the places of C1."""
    root = profile_copy(tmp_path / "root")
    profile = root / "profile"
    below = rendered_below("validator")
    assert below
    shutil.rmtree(profile / "validator")
    outside = outside_dir(tmp_path)
    for rel in below:
        (outside / rel[len("validator/"):]).mkdir(parents=True, exist_ok=True)
    link_dir(profile / "Validator", outside)
    before = snapshot(outside)
    watch = watch_below(monkeypatch, profile / "Validator", load=True)
    assert spy_missed(watch, profile / "Validator") == []
    code = watch.tool.main(["--check"], root=root)
    err = capsys.readouterr().err
    assert watch.calls == [], watch.calls
    monkeypatch.undo()
    assert code == 1 and "profile" "/Validator is a link, which no definition renders; run --write removes the link, and nothing behind it" in err
    for rel in below:
        assert f"profile/{rel} missing; run --write" in err, rel
    assert "is a directory, not the file" not in err
    assert gen.main(["--write"], root=root) == 0
    assert not gen.is_link(profile / "Validator") and (profile / "validator").is_dir()
    assert snapshot(outside) == before and gen.main(["--check"], root=root) == 0


# -- a directory the host cannot list ---------------------------------------------------------------------------------------------------------
def unlistable(monkeypatch, directory, error=PermissionError):
    """os.scandir, which os.walk lists a directory with, raises `error` for `directory`: a host that will not list one.
    (A real one cannot be made here: the sandbox's guard refuses the extended paths that would make it, and the verifier simulated
    it the same way.)"""
    real = os.scandir
    said = {PermissionError: (13, "Access is denied"), FileNotFoundError: (2, "The system cannot find the file specified"),
            NotADirectoryError: (20, "The directory name is invalid")}[error]

    def scandir(path="."):
        if isinstance(path, (str, bytes, os.PathLike)) and os.path.normcase(os.fsdecode(path)) == os.path.normcase(str(directory)):
            raise error(*said, os.fsdecode(path))
        return real(path)                                     # a descriptor, which shutil's cleanup lists by, among the rest
    monkeypatch.setattr(os, "scandir", scandir)


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
# What the owner's machine says (Windows 11 build 22631, Python 3.12), MEASURED by the lead on 2026-10-30 with real junctions that were
# then taken away by making their targets again, and again on 2026-10-31 by P4's builders and the sixth and seventh verifiers, and by
# P4.2's builder at profile/, at context.jsonld and below profile/:
#   target gone:       os.lstat and os.stat raise FileNotFoundError (winerror 2); os.scandir and os.listdir, FileNotFoundError
#                      (winerror 3); open() of it, FileNotFoundError; the checker's test of a link, is_symlink, is_junction, lexists,
#                      exists and isdir say no; os.access(F_OK) says yes; the parent's DirEntry says directory and junction.
#   target a file:     os.lstat, os.stat, os.scandir and os.listdir raise NotADirectoryError (winerror 267); open() of it raises OSError
#                      (errno 22, no winerror); open() of a name below it, FileNotFoundError; the tests say no as above.
# The checker's test of a link therefore finds none. What the tool then does is what these tests hold, with the host's answers told and
# no junction made. They hold the tool's answer to what the host says, and not the host: nothing here would notice if the owner's
# machine opened such a junction again.
@pytest.mark.parametrize("error", [FileNotFoundError, NotADirectoryError])
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_where_the_host_opens_no_dangling_junction_one_at_profile_is_a_tree_whose_context_is_missing_and_nothing_is_made(
        tmp_path, capsys, monkeypatch, mode, error):
    """The checker's test finds no link at profile/ and nothing can be read behind it, whether the target is gone or has become a
    file (the read of a name below it is FileNotFoundError either way): both modes refuse the tree as one whose context is missing,
    exit 1, and make, write and remove nothing. Held with nothing at profile/ and only the listing of the root showing an entry
    there, which is what every read of such a junction finds (dangling_link). This holds the tool's answer to what the host says,
    and not the host."""
    root = tmp_path / "root"
    root.mkdir()
    stand = dangling_link(monkeypatch, root / "profile", error)
    assert not gen.is_link(root / "profile") and dangling_missed(stand) == []
    assert gen.main([mode], root=root) == 1
    said = capsys.readouterr()
    assert said.out == "" and said.err == "profile/context.jsonld is missing: run tools/gen_vocabulary.py --write\n"
    assert stand.listed and stand.real_names() == []


def test_a_file_where_profile_goes_is_a_tree_whose_context_is_missing_in_both_modes_and_nothing_is_changed(tmp_path, capsys):
    """The fifth verifier's gap (V16): a regular file at profile/. The host says FileNotFoundError or NotADirectoryError of a read
    below it (Windows the first, POSIX the second), and the tool says the same sentence for both: P0's context is missing."""
    root = tmp_path / "root"
    root.mkdir()
    (root / "profile").write_bytes(b"not a directory" + bytes([10]))
    for mode in ("--check", "--write"):
        assert gen.main([mode], root=root) == 1
        said = capsys.readouterr()
        assert said.out == "" and said.err == "profile/context.jsonld is missing: run tools/gen_vocabulary.py --write\n"
    assert os.listdir(root) == ["profile"] and (root / "profile").read_bytes() == b"not a directory" + bytes([10])


# what a read of profile/context.jsonld meets, and the tool's sentence: a context that is missing, or that cannot be read
MISSING = "profile/context.jsonld is missing: run tools/gen_vocabulary.py --write\n"
UNREADABLE = "profile/context.jsonld cannot be read (OSError): tools/gen_vocabulary.py --write writes it\n"
CONTEXT_STATES = {
    # a junction whose target is gone: nothing there, FileNotFoundError (dangling_link, FileNotFoundError)
    "target-gone": (FileNotFoundError, None, MISSING),
    # a file where profile/ goes, on a host that says NotADirectoryError of a read below a file (POSIX): told, for the owner's machine
    # says the other; no stand-in, for no entry is there to show
    "a-file-where-profile-goes-on-a-posix-host": (None, NotADirectoryError(20, "Not a directory"), MISSING),
    # a junction whose target has become a file: open() raises OSError, errno 22 (MEASURED, P4.2, and the seventh verifier): told
    "target-became-a-file": (NotADirectoryError, OSError(22, "Invalid argument"), UNREADABLE),
}


@pytest.mark.parametrize("state", sorted(CONTEXT_STATES))
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_where_the_host_opens_no_dangling_junction_at_p0s_context_it_is_a_context_that_is_missing_or_cannot_be_read_and_nothing_is_written(
        tmp_path, capsys, monkeypatch, mode, state):
    """The one place below profile/ where the answer is not exit 3 (the sixth verifier, MEASURED with real junctions, target gone
    and target become a file; the seventh verifier's note 5, and P4.2's ruling 1): P0's context.jsonld is read, not listed. A
    read that fails with FileNotFoundError or NotADirectoryError is a context that is missing, and one that fails with any other
    OSError is a context that cannot be read, and the host's open() of a junction at context.jsonld whose target has become a file
    raises OSError, errno 22, so that tree is refused as one whose context cannot be read, not as one that is missing. Exit 1 in
    both modes either way, and nothing under profile/ is written, removed or made. Held with the entry shown by the listing of
    profile/ alone (dangling_link) and, where the host's open() raises something the stand-in does not, the read told that. This
    holds the tool's answer to what the host says, and not the host."""
    error, told, sentence = CONTEXT_STATES[state]
    root = profile_copy(tmp_path / "root")
    context = root / "profile" / "context.jsonld"
    context.unlink()                                                # nothing stands there, as at a junction that leads nowhere
    before = snapshot(root / "profile")
    stand = dangling_link(monkeypatch, context, error) if error is not None else None
    if told is not None:
        real = Path.read_bytes

        def refusing(self):
            if self == context:
                raise told
            return real(self)
        monkeypatch.setattr(Path, "read_bytes", refusing)
    assert not gen.is_link(context) and (stand is None or dangling_missed(stand) == [])
    assert gen.main([mode], root=root) == 1
    said = capsys.readouterr()
    assert said.out == "" and said.err == sentence, said.err
    assert stand is None or stand.listed
    monkeypatch.undo()
    assert snapshot(root / "profile") == before and not context.exists()


@pytest.mark.parametrize("error", [FileNotFoundError, NotADirectoryError])
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_where_the_host_opens_no_dangling_junction_one_below_profile_is_a_directory_it_cannot_list_and_both_modes_fail_naming_it(
        tmp_path, capsys, monkeypatch, mode, error):
    """The checker's test finds no link below profile/, so the walk takes the entry for a directory and lists it, and the host
    says FileNotFoundError, or NotADirectoryError where the target has become a file: both modes fail, exit 3, naming the
    directory and the error, before anything is removed or written. Held with the stand-in of the test of a link that leads
    nowhere, an entry shown by the listing of its parent with nothing at its path (dangling_link, with the error the host gives), and
    the tool not told that it is a link, so that its own test finds none, as the host's does: the same entry, told, is listed and
    removed. This holds the tool's answer to what the host says, and not the host."""
    root = profile_copy(tmp_path / "root")
    jct = root / "profile" / "jct"
    before = snapshot(root / "profile")
    stand = dangling_link(monkeypatch, jct, error)
    assert not gen.is_link(jct)                                     # no link to the tool: its lstat fails, as the host's does
    assert dangling_missed(stand, others=(root / "profile", root / "profile" / "validator")) == []
    assert gen.main([mode], root=root) == 3
    said = capsys.readouterr()
    assert said.out == "" and said.err.count("\n") == 1 and said.err.isascii()
    assert said.err.startswith("FAILED: the generator itself failed, Unlistable: profile" "/jct/ is a directory the host cannot "
                               f"list ({error.__name__}), so nothing under it can be checked or cleared; ")
    assert said.err.endswith("this is not a verdict\n" if mode == "--check" else "it had finished writing no file\n")
    assert stand.listed                                             # and nothing removed the entry
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
    """The rulings of 2026-10-31T03:38:50Z and 05:26:29Z, and P4.2's ruling 1 (the seventh verifier's note 5): on a host that opens no
    dangling junction, the checker's test of a link finds none there; with profile/ itself one, both modes refuse the tree, exit
    1, as one whose context is missing; with one at P0's context.jsonld, the same, as a context that is missing where the target
    is gone and as one that cannot be read (OSError, errno 22) where it has become a file; with any other below, both fail, exit 3,
    naming a directory the host cannot list; neither writes or removes anything; the owner's machine is the one it was found on,
    on 2026-10-30; and the tests hold the tool's answer to what the host says, not the host. The two places that state the tool's
    limits say it in these words, and the tests of the stated limit hold what it says. The docstring is read from the tool's
    source text, which python -OO does not empty."""
    page = " ".join((ROOT / "docs" / "P4.md").read_text(encoding="utf-8").replace("`", "").split())
    doc = " ".join(tool_docstring().split())
    for text in (page, doc):
        for words in ("A junction whose target is gone is a link only on a host that can open it, and the owner's machine cannot "
                      "(found so on 2026-10-30",
                      "NotADirectoryError",
                      "where its target has become a file",
                      "so the checker's test of a link finds none there",
                      "With profile/ itself one, both modes refuse the tree, exit 1, as one whose context is missing",
                      "or with one at P0's context.jsonld, both modes refuse it, exit 1, as a context that is missing where the "
                      "target is gone, and as one that cannot be read (OSError, errno 22, from open) where the target has become "
                      "a file",
                      "with any other below profile/, both fail, exit 3, naming a directory the host cannot list "
                      "(FileNotFoundError, or NotADirectoryError where the target has become a file",
                      "neither writes or removes anything",
                      "The tests make no such junction: one can be taken away again only by making its target again (CLAUDE.md "
                      "item 10), and a test that failed first would strand it",
                      "They hold the tool's answer to what the host says, and not the host",
                      "the lead's measurement of 2026-10-30",
                      "the stand-in is an entry that is not there at all, shown only by its parent's listing"):
            assert words in text, words
        assert "this machine" not in text and "this host" not in text           # a published page names the owner's, and the day
        assert "reads an empty directory" not in text
        assert "it could not be taken away again" not in text                   # P4.2's first verifier, note 7: it can, by its target


def test_the_page_and_the_docstring_state_what_p4_2_changed_in_the_tool_in_the_words_the_tests_hold():
    """P4.2's rulings 4, 6, 8 and the prose of 11 (C1, C4, C3, and the casefold limit stated both ways): each is on the page and in the
    docstring, in the words of what the tests above hold."""
    page = " ".join((ROOT / "docs" / "P4.md").read_text(encoding="utf-8").replace("`", "").split())
    doc = " ".join(tool_docstring().split())
    common = ("once the case clash is resolved by hand, run --write",
              "a name casefold equates and the host keeps apart",
              "a name the host calls the same and casefold does not is no clash",
              "before any file is written",
              "only when no link stands on the way to it, each directory above it asked from the top",
              "the asking stopped at the first link",
              "A directory spelt in another case at a rendered file's place is told the directory it is, as the host says on a host "
              "that ignores case")
    only_page = ("nothing below a link is listed, opened or asked of the host, in either mode",
                 "a rendered path below a link is told missing, whatever the link leads to",
                 "It notes every path a call is given, by position or by keyword",
                 "It goes in before the tool is loaded, so that a name the tool binds as it is loaded",
                 "A control makes every call it wraps, by position and by keyword, and demands that the spy saw each",
                 "It does not see a DirEntry of a listing",
                 "the tool imports none of those, and a test reads its imports and holds that",
                 "and no, in the same tests run again, as another host might: a tool that decided by it would behave alike on both",
                 "So a removal that fails fails the run, exit 3, before any file is written",
                 "A name is written as its escape, in printable ASCII, on every line of both modes")
    only_doc = ("nothing below it is listed, opened or asked of the host, in either mode",
                "A rendered path below a link is told missing by --check, whatever the link leads to",
                "a removal that fails (a file held open, a directory that is some process's working directory) fails the run, exit 3, "
                "before any file is written",
                "A name is written as its escape, in printable ASCII, on every line of every mode")
    for text, own in ((page, only_page), (doc, only_doc)):
        for words in common + own:
            assert words in text, words
    assert "a spy on every call of the standard library" not in page.lower()     # P4.2's first verifier, D1: it sees the calls it wraps
    helpers = ast.parse((ROOT / "tests" / "p4" / "p4_helpers.py").read_text(encoding="utf-8"))
    spy_doc = next(ast.get_docstring(n) for n in helpers.body if isinstance(n, ast.FunctionDef) and n.name == "watch_below")
    this_module = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    this = ast.get_docstring(this_module)
    told = ast.get_docstring(next(n for n in this_module.body if isinstance(n, ast.FunctionDef)
                                  and n.name == "test_a_link_below_profile_that_leads_nowhere_is_listed_and_removed_like_any_other"))
    told = " ".join(told.split())                                               # P4.2's first verifier, note 8: it names the calls that are told
    assert "os.unlink and os.rmdir of it and os.access of it" in told and "no call is told, so none can be missed" not in told
    for text in (" ".join(spy_doc.split()), " ".join(this.split())):             # and the two docstrings say what it sees and what it does not
        assert "by position or by keyword" in text and "a DirEntry of a listing" in text, text[:80]
        assert "a handle already open, ctypes, a process, a function another module bound before it went in" in text
        assert "every call of the standard library" not in text


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
