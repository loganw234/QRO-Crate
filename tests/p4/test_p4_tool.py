"""tools/gen_profile.py, in process and as the process a user runs (P4's design, item 8; as tests/tools/test_tools.py holds
tools/gen_vocabulary.py): exit 0 when every file is what the definitions render and the Profile Crate holds, 1 on drift, a file
missing or unexpected, a link, or a Profile Crate that fails its check, 2 when the definitions contradict themselves or the
arguments are wrong, and 3 when the generator itself fails, with one escaped line. A link, a symbolic link or a directory
junction, is one thing in every walk, the checker's own test of one, and nothing behind it is read, written or removed (P4's
third verifier, D1, MEASURED: os.walk(followlinks=False) descends a junction, and --write removed the file it found through one,
outside the tree); a name the console's code page lacks is written as its escape, never a crash (its note 4). A command line is tested as a process too: it
writes its lines unbuffered to the descriptor itself (CLAUDE.md). Where its stdout's reader is gone, Python itself ends it
with exit 120, as gen_vocabulary.py's does: a stated limit. The states a tree can be in that nobody makes by accident (profile/
itself a link, a hard link, a name that differs only by case, a directory where a file goes, a directory the host cannot list, a
read-only file) are in test_p4_tree.py, and the exits of a tool that crashes (python -OO, a module that will not import, a closed
stream) in test_p4_crash.py."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from p4_helpers import ROOT, load_tool, outside_dir, profile_copy, remove_links_under, run_tool, tree
from p4_sweeps import link_dir
from qro import checker
from qro import p4_profile as P
from qro import vocabulary as V

gen = load_tool()
RENDERED = P.render()


@pytest.fixture(autouse=True)
def no_link_is_stranded(tmp_path):
    """Each test of this module that makes a junction ends, passed or failed, with the links under its folder removed while their
    targets are there (remove_links_under, whose docstring says why): a failing test would otherwise strand them."""
    yield
    remove_links_under(tmp_path)


def run(args, cwd, tree_root):
    return run_tool(args, cwd, tree_root)


# -- in process -------------------------------------------------------------------------------------------------------------------
def test_the_tree_is_clean(capsys):
    assert gen.problems() == [] and gen.main(["--check"]) == 0
    out = capsys.readouterr()
    assert out.err == "" and len(out.out.splitlines()) == len(RENDERED)
    assert all(line.endswith("is exactly what its definition renders") for line in out.out.splitlines())


def test_write_makes_the_files_the_definitions_render_and_says_each_and_a_second_write_changes_nothing(tmp_path, capsys):
    (tmp_path / "profile").mkdir()
    (tmp_path / "profile" / "context.jsonld").write_bytes((ROOT / "profile" / "context.jsonld").read_bytes())
    assert gen.main(["--write"], root=tmp_path) == 0
    said = capsys.readouterr().out.splitlines()
    assert said == [f"wrote {rel}" for rel in sorted(RENDERED)]
    on_disk = {p.relative_to(tmp_path / "profile").as_posix(): p.read_bytes() for p in (tmp_path / "profile").rglob("*")
               if p.is_file()}
    assert on_disk == {**RENDERED, "context.jsonld": (ROOT / "profile" / "context.jsonld").read_bytes()}
    assert gen.main(["--check"], root=tmp_path) == 0
    capsys.readouterr()
    assert gen.main(["--write"], root=tmp_path) == 0 and gen.main(["--check"], root=tmp_path) == 0


def test_each_walk_over_profile_says_followlinks_false(tmp_path, monkeypatch):
    """What this holds is the keyword and no more: each walk, the one that lists what is on disk, the one that finds the empty
    directories and the pass that removes them, says followlinks=False. On Windows that does not keep a walk out of a directory
    junction, which os.walk descends whatever the keyword says (P4's third verifier, D1): the tests below make a real one and
    hold the behaviour."""
    calls = []
    real = os.walk

    def spy(top, *args, **kwargs):
        if Path(top) == tmp_path / "profile":                  # the tool's walks, not another module's
            calls.append(kwargs.get("followlinks"))
        return real(top, *args, **kwargs)
    monkeypatch.setattr(os, "walk", spy)
    root = profile_copy(tmp_path)
    assert gen.on_disk(root) and gen.main(["--write"], root=root) == 0
    assert len(calls) >= 3 and all(c is False for c in calls), calls


# -- a link: a symbolic link or a directory junction, by the checker's own test ----------------------------------------------------
def held(outside):
    """What is in a directory, byte for byte: every file's bytes, and every directory, by its path."""
    return {p.relative_to(outside).as_posix(): (p.read_bytes() if p.is_file() else None) for p in sorted(outside.rglob("*"))}


def test_the_generator_asks_the_checker_whether_a_path_is_a_link_and_a_junction_is_one(tmp_path):
    """One test of a link in both: a symbolic link or a directory junction (FORMAT.md item 12). Path.is_symlink is false for a
    junction, which is why the generator's walks followed one."""
    outside = outside_dir(tmp_path)
    link_dir(tmp_path / "jct", outside)
    assert gen.is_link is checker._is_link and gen.is_link(tmp_path / "jct") and not gen.is_link(outside)
    assert not gen.is_link(outside / "victim.txt") and not gen.is_link(tmp_path / "nowhere")
    os.rmdir(tmp_path / "jct")                      # the link itself, never through it


def test_a_junction_in_profile_is_a_link_to_every_walk_check_lists_it_and_touches_nothing_behind_it(tmp_path, capsys):
    root = profile_copy(tmp_path / "root")
    outside = outside_dir(tmp_path)
    before = held(outside)
    link_dir(root / "profile" / "jct", outside)
    assert gen.on_disk(root)["jct"] == b"" and not [k for k in gen.on_disk(root) if k.startswith("jct/")]
    assert gen.empty_dirs(root) == []                                   # not descended: nor "emptydir", nor "jct" as an empty one
    assert [d for d, _, _, _ in gen.walk(root / "profile") if "jct" in Path(d).parts] == []
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert "profile" + "/jct is a link, which no definition renders; run --write removes the link, and nothing behind it" in err
    assert "victim" not in err and "emptydir" not in err and "profile" + "/jct/" not in err
    assert held(outside) == before and os.path.lexists(root / "profile" / "jct")
    os.rmdir(root / "profile" / "jct")


def test_write_removes_a_junction_itself_and_nothing_behind_it_and_then_the_tree_is_clean(tmp_path, capsys):
    """The choice, and why (docs/P4.md): --write removes the link and writes on. The link is something no definition renders, as
    a stray file is; a refusal would leave the tree stale until someone removed it by hand, with nothing gained, for in neither
    choice is anything behind a link read, written or removed. Held with a real junction from profile/ to a directory outside
    the tree that holds a file and an empty directory: after --check and after --write both are there, byte for byte."""
    root = profile_copy(tmp_path / "root")
    outside = outside_dir(tmp_path)
    before = held(outside)
    link_dir(root / "profile" / "jct", outside)
    assert gen.main(["--write"], root=root) == 0
    said = capsys.readouterr().out.splitlines()
    assert "removed jct" in said and not any("victim" in line or "emptydir" in line for line in said)
    assert not os.path.lexists(root / "profile" / "jct")                # the link itself is gone
    assert held(outside) == before and outside.is_dir() and (outside / "emptydir").is_dir()
    assert gen.main(["--check"], root=root) == 0 and gen.on_disk(root).keys() >= set(RENDERED)


def test_a_junction_to_an_empty_directory_is_a_link_and_not_a_directory_that_holds_no_file(tmp_path, capsys):
    root = profile_copy(tmp_path / "root")
    outside = tmp_path / "nothing"
    outside.mkdir()
    link_dir(root / "profile" / "jct", outside)
    assert gen.empty_dirs(root) == []
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert "profile" + "/jct is a link" in err and "holds no file" not in err
    assert gen.main(["--write"], root=root) == 0 and not os.path.lexists(root / "profile" / "jct") and outside.is_dir()
    assert os.listdir(outside) == []


def test_a_directory_that_holds_only_a_link_holds_something_and_write_then_removes_both(tmp_path, capsys):
    root = profile_copy(tmp_path / "root")
    outside = outside_dir(tmp_path)
    before = held(outside)
    (root / "profile" / "stale").mkdir()
    link_dir(root / "profile" / "stale" / "jct", outside)
    assert gen.empty_dirs(root) == []
    assert gen.main(["--check"], root=root) == 1
    assert "profile" + "/stale/jct is a link" in capsys.readouterr().err
    assert gen.main(["--write"], root=root) == 0
    assert not (root / "profile" / "stale").exists() and held(outside) == before          # the link, then the directory it left empty
    assert gen.main(["--check"], root=root) == 0


def test_remove_link_removes_a_link_itself_and_nothing_behind_it_and_refuses_a_path_that_is_none(tmp_path):
    """The removal alone: a junction goes, what it points to stays, byte for byte; and a file, an empty directory, a directory
    with a file in it and a path that is not there are none of them removed as a link, for the fallback to rmdir would take an
    empty directory."""
    outside = outside_dir(tmp_path)
    before = held(outside)
    link_dir(tmp_path / "jct", outside)
    gen.remove_link(tmp_path / "jct")
    assert not os.path.lexists(tmp_path / "jct") and held(outside) == before
    (tmp_path / "file.txt").write_bytes(b"x")
    (tmp_path / "empty").mkdir()
    for path in (tmp_path / "file.txt", tmp_path / "empty", outside, tmp_path / "nowhere"):
        with pytest.raises(ValueError, match="is no link"):
            gen.remove_link(path)
    assert (tmp_path / "file.txt").is_file() and (tmp_path / "empty").is_dir() and held(outside) == before


def test_the_pass_over_empty_directories_removes_the_empty_ones_it_walks_and_none_behind_a_link(tmp_path):
    """The pass alone, with a junction still in place (--write removes the link before it, so only this holds the pass): the
    directories under profile/ that are empty go, deepest first, and the empty directory behind the link, and the link, stay."""
    root = profile_copy(tmp_path / "root")
    outside = outside_dir(tmp_path)
    before = held(outside)
    (root / "profile" / "a" / "b").mkdir(parents=True)
    link_dir(root / "profile" / "jct", outside)
    gen.remove_empty_dirs(root / "profile")
    assert not (root / "profile" / "a").exists() and (root / "profile" / "validator").is_dir()
    assert os.path.lexists(root / "profile" / "jct") and held(outside) == before and (outside / "emptydir").is_dir()
    os.rmdir(root / "profile" / "jct")


def test_write_removes_a_link_at_the_path_of_a_file_it_has_to_write_and_never_p0s_context(tmp_path, capsys, monkeypatch):
    """A symbolic link to a file needs a privilege on Windows, so the walk's question is planted, as P0's test of the checker's
    walk plants it: README.md, which a definition renders, and context.jsonld, which P0 writes, are said to be links. The first is
    removed before it is written, so nothing is written through it; the second is P0's, and is not removed."""
    root = profile_copy(tmp_path / "root")
    real = gen.is_link
    monkeypatch.setattr(gen, "is_link", lambda p: p.name in ("README.md", "context.jsonld") or real(p))
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert "profile/README.md is a link, not the file its definition renders; run --write removes the link and writes the file" in err
    assert gen.main(["--write"], root=root) == 0
    said = capsys.readouterr().out.splitlines()
    assert "removed README.md" in said and "wrote README.md" in said and "removed context.jsonld" not in said
    assert said.index("removed README.md") < said.index("wrote README.md")
    assert (root / "profile" / "context.jsonld").is_file() and (root / "profile" / "README.md").read_bytes() == RENDERED["README.md"]


def test_write_writes_nothing_through_a_junction_where_it_has_files_to_write(tmp_path, capsys):
    """A junction in the place of a directory the tool writes into: the files go into a real directory, never behind the link."""
    root = profile_copy(tmp_path / "root")
    shutil.rmtree(root / "profile" / "validator")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_bytes(b"mine" + bytes([10]))
    before = held(outside)
    link_dir(root / "profile" / "validator", outside)
    assert gen.main(["--check"], root=root) == 1
    assert "profile/validator is a link, which no definition renders" in capsys.readouterr().err
    assert gen.main(["--write"], root=root) == 0
    assert held(outside) == before and not (outside / "qro-crate").exists()
    assert (root / "profile" / "validator" / "qro-crate" / "must" / "2_terms.ttl").read_bytes() == RENDERED["validator/qro-crate/must/2_terms.ttl"]
    assert not gen.is_link(root / "profile" / "validator") and gen.main(["--check"], root=root) == 0


def test_write_removes_what_no_definition_renders_and_the_directories_it_leaves_empty_and_never_p0s_context(tmp_path, capsys):
    root = profile_copy(tmp_path)
    (root / "profile" / "stale" / "deep").mkdir(parents=True)
    (root / "profile" / "stale" / "deep" / "old.txt").write_bytes(b"x")
    (root / "profile" / "validator" / "qro-crate" / "may").mkdir()
    (root / "profile" / "validator" / "qro-crate" / "may" / "1.ttl").write_bytes(b"x")
    assert gen.main(["--check"], root=root) == 1
    capsys.readouterr()
    assert gen.main(["--write"], root=root) == 0
    said = capsys.readouterr().out.splitlines()
    assert "removed stale/deep/old.txt" in said and "removed validator/qro-crate/may/1.ttl" in said
    assert not (root / "profile" / "stale").exists() and not (root / "profile" / "validator" / "qro-crate" / "may").exists()
    assert (root / "profile" / "context.jsonld").is_file() and gen.main(["--check"], root=root) == 0


def test_a_directory_that_holds_no_file_is_drift_however_deep_and_write_removes_it(tmp_path, capsys):
    """P4's verifier, round 1: --write removed an empty directory that --check did not notice (git cannot commit one)."""
    root = profile_copy(tmp_path)
    (root / "profile" / "validator" / "qro-crate" / "may").mkdir()
    (root / "profile" / "a" / "b").mkdir(parents=True)
    assert gen.empty_dirs(root) == ["a", "a/b", "validator/qro-crate/may"]
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    for rel in ("validator/qro-crate/may", "a", "a/b"):
        assert f"profile/{rel}/ is a directory that holds no file; run --write" in err, rel
    assert gen.main(["--write"], root=root) == 0
    assert not (root / "profile" / "a").exists() and not (root / "profile" / "validator" / "qro-crate" / "may").exists()
    assert gen.empty_dirs(root) == [] and gen.main(["--check"], root=root) == 0


@pytest.mark.parametrize("rel", sorted(RENDERED))
def test_a_changed_byte_in_a_generated_file_is_drift(tmp_path, capsys, rel):
    root = profile_copy(tmp_path)
    data = bytearray((root / "profile" / rel).read_bytes())
    data[len(data) // 2] ^= 1
    (root / "profile" / rel).write_bytes(bytes(data))
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert f"profile/{rel} DRIFTED from its definition:" in err and "committed" in err and "definition" in err
    assert "editing the file is never the fix" in err


def test_a_missing_file_is_drift_and_so_is_one_that_no_definition_renders(tmp_path, capsys):
    root = profile_copy(tmp_path)
    (root / "profile" / "README.md").unlink()
    assert gen.main(["--check"], root=root) == 1
    assert "profile/README.md missing; run --write" in capsys.readouterr().err
    (root / "profile" / "extra.txt").write_bytes(b"x")
    assert gen.main(["--check"], root=root) == 1
    assert "profile" + "/extra.txt is rendered by no definition; run --write" in capsys.readouterr().err


def test_p0s_context_missing_is_one_not_a_crash_and_write_then_writes_nothing(tmp_path, capsys):
    root = profile_copy(tmp_path)
    (root / "profile" / "context.jsonld").unlink()
    before = {p.relative_to(root).as_posix(): p.read_bytes() for p in (root / "profile").rglob("*") if p.is_file()}
    for mode in ("--check", "--write"):
        assert gen.main([mode], root=root) == 1
        assert "profile/context.jsonld is missing" in capsys.readouterr().err
    after = {p.relative_to(root).as_posix(): p.read_bytes() for p in (root / "profile").rglob("*") if p.is_file()}
    assert after == before and len(before) == len(RENDERED)            # every file as it was: none written, none removed
    empty = tmp_path / "empty"
    (empty / "profile").mkdir(parents=True)
    assert gen.main(["--write"], root=empty) == 1 and list((empty / "profile").iterdir()) == []


MISSHAPEN = {                        # edits of the Profile Crate on disk (the verifier's exit3.sh, and a few more)
    "an entity whose @id is a list": lambda g, md: g[3].__setitem__("@id", ["x"]),
    "an entity whose @id is an object": lambda g, md: g[3].__setitem__("@id", {"a": 1}),
    "an entity with no @id": lambda g, md: g[3].pop("@id"),
    "an artifact that is a number": lambda g, md: next(e for e in g if e["@id"] == "#hasSpecification").__setitem__(
        "hasArtifact", {"@id": 5}),
    "a graph that is a string": lambda g, md: md.__setitem__("@graph", "x"),
    "a null in the graph": lambda g, md: g.append(None),
    "a type that is a number": lambda g, md: g[4].__setitem__("@type", 5),
    "a hasPart that is a string": lambda g, md: g[1].__setitem__("hasPart", ["README.md"]),
    "a context that is a number": lambda g, md: md.__setitem__("@context", 5),
    "a metadata that is no object": lambda g, md: md.clear(),
}


def misshapen(tmp_path, why):
    root = profile_copy(tmp_path)
    path = root / "profile" / "ro-crate-metadata.json"
    md = json.loads(path.read_bytes())
    MISSHAPEN[why](md["@graph"], md)
    path.write_bytes(json.dumps(md, indent=2, sort_keys=True).encode("ascii") + b"\n")
    return root


@pytest.mark.parametrize("why", sorted(MISSHAPEN))
def test_a_misshapen_profile_crate_is_exit_1_with_a_problem_named_and_never_exit_3(tmp_path, capsys, why):
    root = misshapen(tmp_path, why)
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert "generator itself failed" not in err and "profile/ro-crate-metadata.json DRIFTED" in err
    named = [line for line in err.splitlines() if line.startswith("profile/ro-crate-metadata.json ") and "DRIFTED" not in line]
    assert named and not any(P.NET in line for line in named), err


def test_as_a_process_a_misshapen_profile_crate_is_exit_1_and_not_the_exit_3_of_a_generator_that_failed(tmp_path):
    root = tree(tmp_path / "t")
    path = root / "profile" / "ro-crate-metadata.json"
    md = json.loads(path.read_bytes())
    md["@graph"][3]["@id"] = ["x"]
    path.write_bytes(json.dumps(md, indent=2, sort_keys=True).encode("ascii") + b"\n")
    done = run(["--check"], tmp_path, root)
    assert done.returncode == 1 and "generator itself failed" not in done.stderr and "profile/ro-crate-metadata.json DRIFTED" in done.stderr


def test_a_long_diff_is_cut_and_says_how_many_lines_more(tmp_path, capsys):
    root = profile_copy(tmp_path)
    (root / "profile" / "README.md").write_bytes(b"x\n" * 400)
    assert gen.main(["--check"], root=root) == 1
    err = capsys.readouterr().err
    assert "more lines" in err and err.count("\n") < 120


def test_a_profile_crate_that_fails_its_check_is_a_failure_of_check_and_write_writes_nothing_then(tmp_path, capsys, monkeypatch):
    root = profile_copy(tmp_path)
    monkeypatch.setattr(P, "check_profile_crate", lambda files, context=None: ["a rule of RO-Crate broken"])
    assert gen.main(["--check"], root=root) == 1
    assert "profile/ro-crate-metadata.json a rule of RO-Crate broken" in capsys.readouterr().err
    empty = tmp_path / "empty"
    (empty / "profile").mkdir(parents=True)
    (empty / "profile" / "context.jsonld").write_bytes((ROOT / "profile" / "context.jsonld").read_bytes())
    assert gen.main(["--write"], root=empty) == 1
    err = capsys.readouterr().err
    assert "so nothing is written" in err and "a rule of RO-Crate broken" in err
    assert sorted(p.name for p in (empty / "profile").iterdir()) == ["context.jsonld"]


def test_the_definitions_that_contradict_themselves_are_exit_2_one_escaped_line_each(capsys, monkeypatch):
    monkeypatch.setattr(V, "TERMS", V.TERMS + (V.Term("qro:Shots", "REPORTED", "text", False, (), "body", None, "P0", "m"),))
    assert gen.main(["--check"]) == 2 and gen.main(["--write"]) == 2
    err = capsys.readouterr().err
    assert err.count("the definitions contradict themselves:") == 2
    assert err.count("qro:Shots: equal but for case to qro:shots, so the two share an anchor") == 2
    monkeypatch.undo()
    monkeypatch.setitem(V.SPELLINGS, "decimal", "x")
    assert gen.main(["--check"]) == 2 and "decimal: no shape constraint" in capsys.readouterr().err
    monkeypatch.undo()
    monkeypatch.setattr(V, "sanity", lambda: ["a line\nwith a feed and ☃"])
    assert gen.main(["--check"]) == 2
    lines = capsys.readouterr().err.splitlines()
    assert lines == ["the definitions contradict themselves:", "  a line\\nwith a feed and \\u2603"]


def test_wrong_arguments_are_exit_2(capsys):
    for argv in ([], ["--check", "--write"], ["--nonesuch"], ["check"]):
        with pytest.raises(SystemExit) as stop:
            gen.main(argv)
        assert stop.value.code == 2, argv
    capsys.readouterr()


def test_the_generator_failing_is_exit_3_with_one_escaped_line_that_is_not_a_verdict(capsys, monkeypatch):
    def boom(root=None):
        raise RuntimeError("it broke\nwith a feed and ☃")
    monkeypatch.setattr(P, "render", boom)
    assert gen.main(["--check"]) == 3
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.count("\n") == 1 and captured.err.isascii()
    assert captured.err == ("FAILED: the generator itself failed, RuntimeError: it broke\\nwith a feed and \\u2603; "
                            "this is not a verdict\n")


def test_a_write_that_fails_part_way_says_what_it_had_finished_and_leaves_no_temporary_file(tmp_path, capsys, monkeypatch):
    """Each file is written beside its place and put there by os.replace (docs/P4.md, "Regenerating"): the third put-in-place
    fails, and the temporary file it had written is removed again."""
    root = tmp_path
    (root / "profile").mkdir()
    (root / "profile" / "context.jsonld").write_bytes((ROOT / "profile" / "context.jsonld").read_bytes())
    real, calls = os.replace, []

    def failing(src, dst, *a, **k):
        if root in Path(dst).parents:                    # the files put in profile/, not another module's
            calls.append(Path(dst).name)
            if len(calls) == 3:
                raise OSError("the disk is full")
        return real(src, dst, *a, **k)
    monkeypatch.setattr(os, "replace", failing)
    assert gen.main(["--write"], root=root) == 3
    err = capsys.readouterr().err
    assert err.count("\n") == 1 and "OSError: the disk is full" in err
    assert "it had finished writing EXAMPLES.md, README.md" in err and "not a verdict" not in err
    assert [p for p in (root / "profile").rglob("*") if p.name.endswith(gen.TEMP)] == []


def test_write_renders_every_file_before_it_writes_any(tmp_path, capsys, monkeypatch):
    root = tmp_path
    (root / "profile").mkdir()
    (root / "profile" / "context.jsonld").write_bytes((ROOT / "profile" / "context.jsonld").read_bytes())
    monkeypatch.setattr(P, "fixture_files", lambda: (_ for _ in ()).throw(RuntimeError("no fixture")))
    assert gen.main(["--write"], root=root) == 3
    assert "it had finished writing no file" in capsys.readouterr().err
    assert sorted(p.name for p in (root / "profile").iterdir()) == ["context.jsonld"]


# -- as a process ---------------------------------------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def isolated(tmp_path_factory):
    """The package, the tool and profile/ in a directory of its own, which the command line is run in."""
    return tree(tmp_path_factory.mktemp("tree"))


def fresh(isolated, tmp_path):
    return tree(tmp_path / "t")


def test_as_a_process_a_clean_tree_is_exit_0_and_says_each_file_on_stdout_and_nothing_on_stderr(isolated, tmp_path):
    done = run(["--check"], tmp_path, isolated)
    assert done.returncode == 0 and done.stderr == ""
    assert sorted(done.stdout.splitlines()) == sorted(f"profile/{rel} is exactly what its definition renders"
                                                      for rel in RENDERED)


def test_as_a_process_a_changed_file_is_exit_1_with_the_diff_on_stderr_and_the_others_on_stdout(tmp_path):
    root = fresh(None, tmp_path)
    (root / "profile" / "EXAMPLES.md").write_bytes((root / "profile" / "EXAMPLES.md").read_bytes() + b"\nextra\n")
    done = run(["--check"], tmp_path, root)
    assert done.returncode == 1 and "profile/EXAMPLES.md DRIFTED" in done.stderr and "+extra" not in done.stdout
    assert "profile/EXAMPLES.md is exactly" not in done.stdout and "profile/README.md is exactly" in done.stdout


def test_as_a_process_write_then_check_is_a_round_trip_and_removing_a_file_is_mended(tmp_path):
    root = fresh(None, tmp_path)
    (root / "profile" / "validator" / "qro-crate" / "must" / "2_terms.ttl").unlink()
    assert run(["--check"], tmp_path, root).returncode == 1
    done = run(["--write"], tmp_path, root)
    assert done.returncode == 0 and "wrote validator/qro-crate/must/2_terms.ttl" in done.stdout
    assert run(["--check"], tmp_path, root).returncode == 0


def test_as_a_process_a_table_that_contradicts_itself_is_exit_2(tmp_path):
    root = fresh(None, tmp_path)
    vocab = root / "qro" / "vocabulary.py"
    vocab.write_bytes(vocab.read_bytes() + b"\nTERMS = TERMS + (Term('qro:Shots', 'REPORTED', 'text', False, (), 'body', "
                                           b"None, 'P0', 'a name equal but for case'),)\n")
    done = run(["--check"], tmp_path, root)
    assert done.returncode == 2 and done.stdout == ""
    lines = done.stderr.splitlines()
    assert lines[:2] == ["the definitions contradict themselves:",
                         "  qro:Shots: equal but for case to qro:shots, so the two share an anchor"]
    assert len(lines) == 3 and lines[2].startswith("  two shapes share the id ") and lines[2].endswith("#term-qro-shots")


def test_as_a_process_the_generator_failing_is_exit_3_and_one_line_with_nothing_unescaped(tmp_path):
    root = fresh(None, tmp_path)
    module = root / "qro" / "p4_profile.py"
    module.write_bytes(module.read_bytes() + b"\n\ndef render(root=None):\n    raise RuntimeError('boom ' + chr(0x2603) + "
                                             b"chr(10) + 'x')\n")
    done = run(["--check"], tmp_path, root)
    assert done.returncode == 3 and done.stdout == "" and done.stderr.count("\n") == 1 and done.stderr.isascii()
    assert done.stderr.startswith("FAILED: the generator itself failed, RuntimeError: boom \\u2603\\nx")


def test_as_a_process_the_wrong_arguments_are_exit_2_and_say_the_usage(tmp_path):
    root = fresh(None, tmp_path)
    for args in ([], ["--check", "--write"], ["--nonesuch"]):
        done = run(args, tmp_path, root)
        assert done.returncode == 2 and done.stdout == "" and "usage:" in done.stderr, args


def test_the_tool_changes_nothing_outside_profile(tmp_path):
    root = fresh(None, tmp_path)
    before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file() and "profile" not in p.parts}
    (root / "profile" / "README.md").unlink()
    assert run(["--write"], tmp_path, root).returncode == 0
    after = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file() and "profile" not in p.parts
             and "__pycache__" not in p.parts}
    assert after == {k: v for k, v in before.items() if "__pycache__" not in k}


def test_as_a_process_a_junction_in_profile_is_listed_then_removed_and_what_it_points_at_is_untouched(tmp_path):
    """D1 as a user meets it: a real junction made without privilege from profile/ to a directory outside the tree that holds
    a file and an empty directory. The third verifier's run removed the file and the junction; after --check and after --write
    both are there, byte for byte, but for the link, which --write removes."""
    root = fresh(None, tmp_path)
    outside = outside_dir(tmp_path)
    before = held(outside)
    link_dir(root / "profile" / "jct", outside)
    check = run(["--check"], tmp_path, root)
    assert check.returncode == 1 and "profile" + "/jct is a link, which no definition renders" in check.stderr
    assert "victim" not in check.stdout + check.stderr and "emptydir" not in check.stdout + check.stderr
    assert held(outside) == before and os.path.lexists(root / "profile" / "jct")
    write = run(["--write"], tmp_path, root)
    assert write.returncode == 0 and "removed jct" in write.stdout.splitlines() and "victim" not in write.stdout
    assert not os.path.lexists(root / "profile" / "jct") and held(outside) == before
    assert run(["--check"], tmp_path, root).returncode == 0


def test_as_a_process_a_stray_file_whose_name_the_console_cannot_write_is_written_as_its_escape_and_never_a_crash(tmp_path):
    """P4's third verifier, note 4, MEASURED: a stray file named in CJK characters with stdout in cp1252 made --write exit 3
    after it had removed the file and before it wrote anything. Both modes write the name as its escape, as P0.6's gate does."""
    root = fresh(None, tmp_path)
    name = chr(0x4E2D) + chr(0x6587) + ".txt"
    escaped = (chr(92) + "u4e2d" + chr(92) + "u6587.txt").encode("ascii")      # the name as the command line escapes its own
    (root / "profile" / name).write_bytes(b"x")
    cmd = [sys.executable, str(root / "tools" / "gen_profile.py")]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="cp1252")
    check = subprocess.run(cmd + ["--check"], cwd=tmp_path, capture_output=True, env=env)
    assert check.returncode == 1, check.stderr[-300:]
    assert b"profile/" + escaped + b" is rendered by no definition; run --write" in check.stderr, check.stderr[-300:]
    write = subprocess.run(cmd + ["--write"], cwd=tmp_path, capture_output=True, env=env)
    assert write.returncode == 0, write.stderr[-300:]
    assert b"removed " + escaped in write.stdout.splitlines(), write.stdout[-300:]
    assert not (root / "profile" / name).exists()
    assert subprocess.run(cmd + ["--check"], cwd=tmp_path, capture_output=True, env=env).returncode == 0


def test_as_a_process_with_no_stdout_the_generator_runs_and_says_its_verdict_by_its_exit(tmp_path):
    """Where stdout is None (pythonw, a closed descriptor) the streams are left as they are, and the tool neither crashes at
    the attempt to tell them how to write nor is made to open a window: the runpy shape of P0.6's tests, never pythonw."""
    root = fresh(None, tmp_path)
    tool = str(root / "tools" / "gen_profile.py")
    code = ("import runpy, sys; sys.stdout = None; sys.argv = [sys.argv[1], '--check']; "
            "runpy.run_path(sys.argv[0], run_name='__main__')")
    done = subprocess.run([sys.executable, "-c", code, tool], cwd=tmp_path, capture_output=True, text=True,
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    assert done.returncode == 0 and done.stderr == "", done.stderr[-300:]
    (root / "profile" / "extra.txt").write_bytes(b"x")
    done = subprocess.run([sys.executable, "-c", code, tool], cwd=tmp_path, capture_output=True, text=True,
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    assert done.returncode == 1 and "profile" + "/extra.txt is rendered by no definition" in done.stderr, done.stderr[-300:]
