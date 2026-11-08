"""P1.2's adapter (qro/p1_adapter.py): `python -m qro.p1_adapter ibm|atlas --moth DIR --out DIR [--records DIR] [--slice]`.

It builds a crate outside the tree and writes nothing into it: it refuses an `--out` inside this repository or inside
the checkout, or not empty, a checkout that is not moth-quantum clean at 3a73823, and a file it would take from the checkout
that is not 3a73823's own (tests/p1/p1_pinned.py runs its command line as a process on a toy checkout, which is not
moth-quantum, and tests/p1/p1_hosts.py under a host a test simulates). Its command line is tested as
P0's is (tests/format/test_cli.py): in process with real descriptors, and as a process, for the exit codes (0 built, 1 and
one REFUSED line for records that disagree, 2 misuse, 3 the adapter itself failing), the one printable-ASCII line, and the
closed pipe that must exit 3 and never 120."""
import contextlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest

import p1_builder
import p1_hosts
from controls import plants_p1 as plants
from p1_support import (ATLAS_JOBS, BUNDLE, IBM_DIR, MANIFEST, ROOT, TWIN, jline, memo_parses, moth_of, pin_p2, recommit,
                        standin, synthetic_atlas, twin_copy)
from qro import canonical, checker, p1_adapter as A, p1_decode, p1_generate as G
from qro.__main__ import LINE_MAX, escape
from qro.refusal import Refused

USAGE = "usage: python -m qro.p1_adapter ibm|atlas --moth DIR --out DIR [--records DIR] [--slice]"
LINE = re.compile(r"BUILT (ibm|atlas): ([0-9]+) files, ([0-9]+) bytes, identity ([0-9a-f]{64})")


def run(tmp_path, argv, out=None):
    """main() in process, its two descriptors files: (exit code, stdout's bytes, stderr's bytes)."""
    paths = [tmp_path / "stdout.bin", tmp_path / "stderr.bin"]
    fds = [os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_BINARY", 0)) for p in paths]
    try:
        code = A.main(argv, out=fds[0] if out is None else out, err=fds[1])
    finally:
        for fd in fds:
            os.close(fd)
    return code, paths[0].read_bytes(), paths[1].read_bytes()


def process(argv, module="qro.p1_adapter", stdout=subprocess.PIPE, encoding="utf-8"):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING=encoding, PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-m", module, *argv], stdout=stdout, stderr=subprocess.PIPE, env=env, cwd=ROOT)


def tree():
    """What git sees of this repository: every change and every file it does not know. Nothing the adapter does may add one."""
    return subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT,
                          capture_output=True).stdout.decode("utf-8", "replace")


def twin_args(out, *more):
    return ["ibm", "--moth", str(TWIN), "--out", str(out), "--slice", *more]


@pytest.fixture
def quick(monkeypatch):
    memo_parses(monkeypatch)


# -- misuse, exit 2 ----------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("argv", [
    [], ["nothing"], ["ibm"], ["ibm", "--moth", "x"], ["ibm", "--out", "y"], ["ibm", "--moth", "x", "--out", "y", "--moth", "z"],
    ["ibm", "--moth"], ["ibm", "--bogus"], ["ibm", "--moth", "", "--out", "y"], ["ibm", "--moth", "x", "--out", ""],
    ["atlas", "--moth", "x", "--out", "y", "stray"], ["ibm", "--slice", "--slice"],
], ids=lambda a: " ".join(a) or "no arguments")
def test_a_command_line_that_is_not_the_commands_is_misuse_and_says_how(tmp_path, argv):
    code, out, err = run(tmp_path, argv)
    assert (code, out) == (2, b"")
    line = err.decode("ascii")
    assert line.count("\n") == 1 and USAGE in line


def test_a_moth_that_is_no_directory_is_misuse(tmp_path):
    code, out, err = run(tmp_path, ["ibm", "--moth", str(tmp_path / "nope"), "--out", str(tmp_path / "out"), "--slice"])
    assert (code, out) == (2, b"") and b"no such directory" in err and not (tmp_path / "out").exists()


def test_a_records_directory_without_the_read_of_2026_10_14_is_misuse(tmp_path):
    code, out, err = run(tmp_path, twin_args(tmp_path / "out", "--records", str(tmp_path)))
    assert (code, out) == (2, b"") and b"2026-10-14 is not here" in err and not (tmp_path / "out").exists()


@pytest.fixture
def own_repo(tmp_path, monkeypatch):
    """The adapter's repository pointed at a directory of the test's own, so that an out guard that regressed would build
    there and never into this repository (P1.2's fourth verifier saw its mutant C13a build a crate into its working copy).
    The control: the adapter's REPO is that directory, and this repository is not it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(A, "REPO", repo)
    assert A.REPO == repo and repo != ROOT and ROOT not in repo.parents
    return repo


def records_args(out):
    """The twin into `out`, the read taken from this repository by name, so that a regressed guard could build."""
    return twin_args(out, "--records", str(ROOT / "records"))


@pytest.mark.parametrize("where", ["inside the repository", "the repository", "inside it by a path through .."])
def test_an_out_inside_the_repository_is_misuse_and_nothing_is_created(tmp_path, own_repo, where):
    out = {"inside the repository": own_repo / "adapter-test-out", "the repository": own_repo,
           "inside it by a path through ..": tmp_path / "elsewhere" / ".." / "repo" / "adapter-test-out"}[where]
    before = tree()
    code, stdout, err = run(tmp_path, records_args(out))
    assert (code, stdout) == (2, b"") and b"inside this repository" in err
    assert list(own_repo.iterdir()) == [] and tree() == before


def test_an_out_inside_the_checkout_is_misuse(tmp_path):
    moth = tmp_path / "moth"
    moth.mkdir()
    code, out, err = run(tmp_path, ["ibm", "--moth", str(moth), "--out", str(moth / "crate"), "--slice"])
    assert (code, out) == (2, b"") and b"inside the checkout" in err and not (moth / "crate").exists()


# -- every spelling of a place inside either tree is inside it (P1.2's fourth verifier, D2) -------------------------------------------
def spellings(base, tail="newdir"):
    """Spellings of a new path in `base`, and of `base` itself: plain; and on Windows the fourth verifier's, the
    extended-length prefix in its forms, which os.path.realpath keeps as it had them."""
    b = str(base)
    out = {"plain": b + os.sep + tail}
    if os.name == "nt":
        out.update({
            "extended": "\\\\?\\" + b + "\\" + tail,
            "extended, the place itself": "\\\\?\\" + b,
            "extended, a lower-case drive": "\\\\?\\" + b[0].lower() + b[1:] + "\\" + tail,
            "extended, with forward slashes": "//?/" + b.replace("\\", "/") + "/" + tail,
            "extended, with a . component": "\\\\?\\" + b + "\\.\\" + tail,
            "extended, another case": "\\\\?\\" + b.upper() + "\\" + tail,
            "extended, two new levels deep": "\\\\?\\" + b + "\\" + tail + "\\sub",
        })
    return out


def test_every_spelling_of_a_place_in_the_repository_is_misuse_and_nothing_is_made(tmp_path, own_repo):
    for label, out in spellings(own_repo).items():
        code, stdout, err = run(tmp_path, records_args(out))
        assert (code, stdout) == (2, b"") and misuse_naming(err, Path(out), "inside this repository"), (label, err)
    assert list(own_repo.iterdir()) == []


def test_every_spelling_of_a_place_in_the_checkout_is_misuse_and_nothing_is_made(tmp_path):
    """The checkout is the test's own, a copy of the twin as a slice, so that a guard that regressed would build there."""
    moth = tmp_path / "moth"
    shutil.copytree(TWIN, moth)
    for label, out in spellings(moth).items():
        code, stdout, err = run(tmp_path, ["ibm", "--moth", str(moth), "--out", out, "--slice"])
        assert (code, stdout) == (2, b"") and misuse_naming(err, Path(out), "inside the checkout"), (label, err)
    assert sorted(p.name for p in moth.iterdir()) == sorted(p.name for p in TWIN.iterdir())


def test_a_checkout_named_by_the_extended_length_prefix_holds_a_plain_out_inside_it_too(tmp_path):
    """The prefix dropped on both sides: the checkout given extended, the out given plain."""
    moth = tmp_path / "moth"
    shutil.copytree(TWIN, moth)
    named = "\\\\?\\" + str(moth) if os.name == "nt" else str(moth)
    code, stdout, err = run(tmp_path, ["ibm", "--moth", named, "--out", str(moth / "newdir"), "--slice"])
    assert (code, stdout) == (2, b"") and misuse_naming(err, moth / "newdir", "inside the checkout"), err


def test_an_out_spelt_with_the_extended_length_prefix_inside_the_checkout_is_misuse_as_a_process(tmp_path):
    moth = tmp_path / "moth"
    shutil.copytree(TWIN, moth)
    out = spellings(moth)["extended" if os.name == "nt" else "plain"]
    p = process(["ibm", "--moth", str(moth), "--out", out, "--slice"])
    assert (p.returncode, p.stdout) == (2, b"") and b"inside the checkout" in p.stderr, (p.stdout, p.stderr[-300:])
    assert not (moth / "newdir").exists()


def test_a_place_outside_both_by_any_of_these_spellings_is_an_out_the_adapter_uses(tmp_path, own_repo, quick):
    """The control: the same spellings outside both trees pass the guard, and the extended one builds."""
    world = tmp_path / "world"
    world.mkdir()
    for label, out in spellings(world).items():
        A.check_out(out, TWIN)                                      # passes: the guard refuses nothing outside both
    out = spellings(world)["extended" if os.name == "nt" else "plain"]
    code, stdout, err = run(tmp_path, records_args(out))
    assert code == 0 and LINE.fullmatch(stdout.decode("ascii").rstrip("\n")), (stdout, err)
    assert (world / "newdir" / canonical.DESCRIPTOR).is_file() and list(own_repo.iterdir()) == []


def test_the_extended_length_prefix_is_dropped_as_the_sandboxs_guard_drops_it():
    assert A._plain("\\\\?\\C:\\a\\b") == "C:\\a\\b"
    assert A._plain("\\\\?\\UNC\\server\\share\\x") == "\\\\server\\share\\x"
    for kept in ("C:\\a\\b", "\\\\server\\share\\x", "\\\\?\\GLOBALROOT\\Device\\x", "/srv/a/b"):
        assert A._plain(kept) == kept


def test_an_out_that_is_not_empty_is_misuse_and_is_left_as_it_was(tmp_path):
    out = tmp_path / "out"
    (out / "sub").mkdir(parents=True)
    (out / "sub" / "keep.txt").write_bytes(b"mine")
    code, stdout, err = run(tmp_path, twin_args(out))
    assert (code, stdout) == (2, b"") and b"not an empty directory" in err
    assert [p.relative_to(out).as_posix() for p in out.rglob("*")] == ["sub", "sub/keep.txt"]
    assert (out / "sub" / "keep.txt").read_bytes() == b"mine"


def test_an_out_that_is_a_file_is_misuse(tmp_path):
    (tmp_path / "out").write_bytes(b"x")
    code, stdout, err = run(tmp_path, twin_args(tmp_path / "out"))
    assert (code, stdout) == (2, b"") and b"not an empty directory" in err


# -- the checkout -----------------------------------------------------------------------------------------------------------------------
def git_run(repo, *args, check=True):
    """git in `repo`, its stdout and stderr as the bytes git wrote them, as the adapter reads them (_git_bytes): a name git
    writes raw, as `core.quotePath false` has it, is UTF-8, which the host's code page may not decode."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t")
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, env=env, check=check)


def git(repo, *args):
    """git's stdout in `repo` as text, stripped: UTF-8, with a byte that is not replaced, as the adapter shows a name."""
    return git_run(repo, *args).stdout.decode("utf-8", "replace").strip()


@pytest.fixture
def toy(tmp_path):
    """A git checkout of something else, at a commit of its own, clean."""
    repo = tmp_path / "toy"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "a.txt").write_bytes(b"a")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "x")
    return repo


def test_a_checkout_at_another_commit_is_misuse_and_names_it(tmp_path, toy):
    head = git(toy, "rev-parse", "HEAD")
    code, out, err = run(tmp_path, ["ibm", "--moth", str(toy), "--out", str(tmp_path / "out")])
    assert (code, out) == (2, b"") and f"at {head[:7]}, and the adapter reads moth-quantum at 3a73823".encode() in err
    assert not (tmp_path / "out").exists()


def test_a_checkout_that_is_clean_at_its_commit_passes_and_every_kind_of_change_does_not(toy, monkeypatch):
    monkeypatch.setattr(A, "MOTH_COMMIT", git(toy, "rev-parse", "HEAD")[:7])
    A.check_moth(toy)
    (toy / "new.txt").write_bytes(b"untracked")
    with pytest.raises(A.AdapterError, match="changes that are not committed"):
        A.check_moth(toy)
    (toy / "new.txt").unlink()
    (toy / "a.txt").write_bytes(b"changed")
    with pytest.raises(A.AdapterError, match="changes that are not committed"):
        A.check_moth(toy)
    git(toy, "add", "-A")
    with pytest.raises(A.AdapterError, match="changes that are not committed"):
        A.check_moth(toy)
    git(toy, "commit", "-q", "-m", "y")
    monkeypatch.setattr(A, "MOTH_COMMIT", "0000000")
    with pytest.raises(A.AdapterError, match="the adapter reads moth-quantum at 0000000"):
        A.check_moth(toy)
    head = git(toy, "rev-parse", "HEAD")
    near = head[:6] + ("0" if head[6] != "0" else "1")             # the same six characters, and a seventh that is not its
    monkeypatch.setattr(A, "MOTH_COMMIT", near)
    with pytest.raises(A.AdapterError, match=f"the adapter reads moth-quantum at {near}"):
        A.check_moth(toy)
    monkeypatch.setattr(A, "MOTH_COMMIT", head[:7])
    A.check_moth(toy)


def test_a_checkout_is_asked_what_it_is_and_not_what_the_callers_environment_says_it_is(tmp_path, toy, monkeypatch):
    """A caller that has GIT_DIR set (a hook, a wrapper) must not make another repository the checkout's."""
    other = tmp_path / "other"
    other.mkdir()
    git(other, "init", "-q")
    (other / "b.txt").write_bytes(b"b")
    git(other, "add", "-A")
    git(other, "commit", "-q", "-m", "z")
    assert git(other, "rev-parse", "HEAD") != git(toy, "rev-parse", "HEAD")
    monkeypatch.setattr(A, "MOTH_COMMIT", git(toy, "rev-parse", "HEAD")[:7])
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    A.check_moth(toy)


def test_a_directory_below_the_top_of_a_checkout_and_a_directory_that_is_no_checkout_are_misuse(tmp_path, toy):
    (toy / "sub").mkdir()
    with pytest.raises(A.AdapterError, match="not the top of a git checkout"):
        A.check_moth(toy / "sub")
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(A.AdapterError, match="must be a git checkout of moth-quantum"):
        A.check_moth(plain)


def test_a_slice_is_not_asked_to_be_a_checkout(tmp_path, quick):
    assert A.build("ibm", TWIN, tmp_path / "out", sliced=True)["files"] >= 73


# -- a crate built, and the tree untouched ---------------------------------------------------------------------------------------------------
def test_the_twin_is_built_as_a_process_and_checked_as_one(tmp_path):
    out = tmp_path / "crate"
    before = tree()
    built = process(twin_args(out))
    assert (built.returncode, built.stderr) == (0, b""), built.stdout[-300:]
    m = LINE.fullmatch(built.stdout.decode("ascii").rstrip("\n"))
    assert m and built.stdout.count(b"\n") == 1
    files = [p for p in out.rglob("*") if p.is_file()]
    assert (int(m.group(2)), int(m.group(3))) == (len(files), sum(p.stat().st_size for p in files))
    checked = process(["check", str(out)], module="qro")
    assert (checked.returncode, checked.stdout, checked.stderr) == (0, f"ACCEPTED {m.group(4)}\n".encode(), b"")
    assert tree() == before                                      # nothing of it is in the tree


def test_the_identity_is_the_crates_not_the_hour_it_was_built_in(tmp_path, quick):
    from datetime import datetime, timezone
    one = A.build("ibm", TWIN, tmp_path / "one", sliced=True, now=datetime(2026, 1, 2, 3, 4, 5, 678, tzinfo=timezone.utc))
    two = A.build("ibm", TWIN, tmp_path / "two", sliced=True, now=datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
    assert one["identity"] == two["identity"]
    root = json.loads((tmp_path / "one" / canonical.DESCRIPTOR).read_bytes())["@graph"][1]
    assert (root["datePublished"], root["qro:writtenAt"], root["qro:writer"]) == (
        "2026-01-02", "2026-01-02T03:04:05Z", A.WRITER)
    again = json.loads((tmp_path / "two" / canonical.DESCRIPTOR).read_bytes())["@graph"][1]
    assert again["qro:writtenAt"] == "2030-12-31T23:59:59Z" and again["datePublished"] == "2030-12-31"


def test_the_crate_is_the_records_copied_byte_for_byte(tmp_path, quick):
    out = tmp_path / "out"
    A.build("ibm", TWIN, out, sliced=True)
    for rel, src in A.plan("ibm", TWIN, ROOT / "records", True):
        assert out.joinpath(*rel.split("/")).read_bytes() == src.read_bytes(), rel
    assert out.joinpath("LICENSE-quantum-film").read_bytes() == (TWIN / "LICENSE").read_bytes()


# -- what is copied -----------------------------------------------------------------------------------------------------------------------------
def test_a_slice_takes_the_read_of_its_jobs_and_every_snapshot_of_their_devices_and_no_probe():
    plan = dict(A.plan("ibm", TWIN, ROOT / "records", True))
    read = [r for r in plan if r.startswith("2026-10-14/")]
    assert len(plan) == 72 and len(read) == 4 + 4 + 3 + 2 + 1 + 2
    assert sum(r.startswith("2026-10-14/ibm-refetch/ibm_kingston/properties-") for r in read) == 3
    assert not [r for r in plan if "dryrun" in r]
    assert {r for r in read if r.endswith("MANIFEST.json")} == {"2026-10-14/ibm-refetch/MANIFEST.json",
                                                              "2026-10-14/ibm-results-refetch/MANIFEST.json"}
    assert plan["LICENSE-quantum-film"] == TWIN / "LICENSE"


def test_a_crate_that_is_not_a_slice_takes_the_whole_read_but_the_probes():
    plan = dict(A.plan("ibm", TWIN, ROOT / "records", False))
    read = [r for r in plan if r.startswith("2026-10-14/")]
    assert len(read) == 65 + 65 + 7 + 2 + 1 + 2 and not [r for r in plan if "dryrun" in r]


@pytest.mark.parametrize("kind", ["is_symlink", "is_junction"])
def test_a_link_in_the_records_is_refused(monkeypatch, kind):
    """A symbolic link and, on Windows, a junction: neither is followed, as a crate holds files and so does its source."""
    from pathlib import Path
    real = getattr(Path, kind)
    monkeypatch.setattr(Path, kind, lambda self: self.name == "manifest.json" or real(self))
    with pytest.raises(A.AdapterError, match="a link in the records"):
        A.plan("ibm", TWIN, ROOT / "records", True)


def test_a_line_of_the_records_that_cannot_be_read_is_the_records_refused_and_not_misuse(tmp_path):
    """A slice is read for the jobs it carries before anything is copied: a line that is no line is G2's refusal, with the
    file named, exactly as the generator refuses it in a checkout, and the out is left as it was."""
    moth = tmp_path / "moth"
    shutil.copytree(TWIN, moth)
    line = next(moth.rglob("known-answer-line.json"))
    line.write_bytes(b"{")
    out = tmp_path / "out"
    code, stdout, err = run(tmp_path, ["ibm", "--moth", str(moth), "--out", str(out), "--slice"])
    rel = line.relative_to(moth / "docs" / "records").as_posix()
    assert code == 1 and err == b"" and not out.exists()
    assert stdout.decode("ascii").startswith(f"REFUSED metadata-generated at {rel}: G2: "), stdout


def test_two_sources_for_one_path_in_the_crate_are_refused(monkeypatch):
    """The licence is given the path of a file the records carry: the plan names the path rather than choose a source."""
    taken = sorted(r for r, _ in A.plan("ibm", TWIN, ROOT / "records", True) if r.startswith("2026-10-05/"))[0]
    monkeypatch.setattr(G, "LICENSE_QF", taken)
    with pytest.raises(A.AdapterError, match="two files would be " + re.escape(taken)):
        A.plan("ibm", TWIN, ROOT / "records", True)


def test_an_out_is_told_by_where_it_really_is_not_by_how_it_is_spelt(tmp_path, own_repo, monkeypatch):
    """A path that is a link into the repository is inside it, whatever its own spelling says."""
    linked, real = tmp_path / "linked", os.path.realpath
    monkeypatch.setattr(os.path, "realpath", lambda p: str(own_repo / "elsewhere") if str(p) == str(linked) else real(p))
    with pytest.raises(A.AdapterError, match="inside this repository"):
        A.check_out(linked, tmp_path / "moth")
    assert not (own_repo / "elsewhere").exists()


def test_an_unknown_kind_is_refused(tmp_path):
    with pytest.raises(A.AdapterError, match="not a crate this adapter builds"):
        A.build("qpu", TWIN, tmp_path / "out", sliced=True)


def synthetic_moth(tmp_path, with_extras=True):
    """A tree laid out as moth-quantum's, holding the Atlas files of the small synthetic crate (and, if asked, what the adapter
    leaves out: a platform description, a rolls directory)."""
    crate = synthetic_atlas(tmp_path / "src")
    moth = tmp_path / "moth"
    for p in sorted(q for q in crate.rglob("*") if q.is_file()):
        rel = p.relative_to(crate).as_posix()
        if rel == "LICENSE-quantum-film":
            dest = moth / "LICENSE"
        elif rel.startswith("vectors/"):
            dest = moth.joinpath("tests", *rel.split("/"))
        else:
            dest = moth.joinpath("docs", "records", *rel.split("/"))
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
    if with_extras:
        base = moth.joinpath("docs", "records", "2026-09-25", "p3")
        (base / "circuit-0123456789abcdef.platform.json").write_bytes(b"{}")
        (base / "rolls-aaaaaaaa").mkdir()
        (base / "rolls-aaaaaaaa" / "r1.json").write_bytes(b"{}")
    return crate, moth


def test_the_atlas_crate_takes_the_days_files_and_the_vector_but_not_the_platform_or_the_rolls(tmp_path, monkeypatch):
    pin_p2(monkeypatch, None)
    crate, moth = synthetic_moth(tmp_path)
    done = A.build("atlas", moth, tmp_path / "out", sliced=True)
    mine = sorted(p.relative_to(crate).as_posix() for p in crate.rglob("*") if p.is_file())
    built = sorted(p.relative_to(tmp_path / "out").as_posix() for p in (tmp_path / "out").rglob("*") if p.is_file())
    assert built == sorted(mine + [canonical.DESCRIPTOR]) and done["files"] == len(built)
    checker.load()
    assert canonical.body_digest(checker.check(tmp_path / "out")) == done["identity"]


# -- records that disagree: exit 1, one escaped line, nothing left --------------------------------------------------------------------------------
def moth_copy(tmp_path):
    moth = tmp_path / "moth"
    shutil.copytree(TWIN, moth)
    return moth


def test_records_that_disagree_are_refused_by_metadata_generated_in_one_line_and_leave_nothing(tmp_path, quick):
    moth = moth_copy(tmp_path)
    gates = next(moth.rglob("known-answer.gates.json"))
    gates.write_bytes(gates.read_bytes() + b" ")
    code, out, err = run(tmp_path, ["ibm", "--moth", str(moth), "--out", str(tmp_path / "out"), "--slice"])
    assert (code, err) == (1, b"")
    line = out.decode("ascii")
    assert line.count("\n") == 1 and line.startswith("REFUSED metadata-generated at 2026-10-05/ibm/ibm_kingston/")
    assert ": G1: " in line and not (tmp_path / "out").exists()


def test_a_failed_build_into_an_empty_directory_leaves_it_empty(tmp_path, quick, cleared):
    moth = moth_copy(tmp_path)
    next(moth.rglob("law.qasm")).write_bytes(b"x")
    out = tmp_path / "out"
    out.mkdir()
    code, _, _ = run(tmp_path, ["ibm", "--moth", str(moth), "--out", str(out), "--slice"])
    assert code == 1 and out.is_dir() and not any(out.iterdir())
    [(directories, files, _)] = cleared
    assert len(files) >= 72 and directories and all(out in d.parents for d in directories)    # it wrote; the out was not its own


def test_a_records_text_that_would_break_the_line_is_written_escaped(tmp_path, quick):
    """A manifest naming a device that holds a line feed, a forged REFUSED and a character past ASCII."""
    moth = moth_copy(tmp_path)
    manifest = next(moth.rglob("bundle/manifest.json"))
    doc = json.loads(manifest.read_bytes())
    doc["backend"] = "caf" + chr(0xE9) + chr(10) + "REFUSED forged at x: y"
    manifest.write_bytes(json.dumps(doc, indent=1, sort_keys=True).encode() + b"\n")
    code, out, err = run(tmp_path, ["ibm", "--moth", str(moth), "--out", str(tmp_path / "out"), "--slice"])
    assert code == 1 and err == b"" and out.count(b"\n") == 1 and out.isascii()
    text = out.decode("ascii")
    assert chr(92) + "xe9" in text and chr(92) + "nREFUSED forged" in text and not text.startswith("REFUSED forged")


# -- a record's string UTF-8 cannot encode is the records refused, exit 1, never the adapter failing (P1.2's fourth verifier, D1) ------------------
SURROGATE = chr(0xD800)                                     # a lone surrogate; json.dumps writes it as the escape \ud800


def surrogate_in_a_submit_file(moth):
    """The first Atlas day's submit file of a synthetic moth, its circuit_qasm a lone surrogate (G11's site)."""
    sub = next(moth.rglob("atlas-*-submit.json"))
    doc = json.loads(sub.read_bytes())
    doc["body"]["params"]["circuit_qasm"] = SURROGATE
    sub.write_bytes(jline(doc))
    return sub.relative_to(moth / "docs" / "records").as_posix(), "body.params.circuit_qasm", "G11"


def surrogate_in_a_commitments_line(moth):
    """The first Atlas day's commitments line, its salt a lone surrogate (the site of _atlas_lines' commitment_v2)."""
    p = moth.joinpath("docs", "records", ATLAS_JOBS[0][0], "p3", "commitments.jsonl")
    docs = [json.loads(x) for x in p.read_bytes().splitlines() if x]
    docs[0]["salt"] = SURROGATE
    p.write_bytes(b"".join(json.dumps(d, sort_keys=True, separators=(",", ":")).encode("ascii") + b"\n" for d in docs))
    return p.relative_to(moth / "docs" / "records").as_posix(), "salt", "G11"


def surrogate_in_a_salt_the_manifest_and_the_record_agree_on(moth):
    """The morning known-answer salt, a lone surrogate in the manifest and in the device-run record alike, the digests that
    hold them recomputed (the site of _g4_g5's commitment_of, which G1 to G3 would not reach first)."""
    f = plants.Forge(moth / "docs" / "records")

    def salt(m):
        for job in m["jobs"]:
            for c in job["circuits"]:
                if c["name"] == "known-answer":
                    c["salt"] = SURROGATE
    f.edit_json(MANIFEST, salt)
    f.reseal_bundle(BUNDLE)
    record = f.json(plants.KA_RECORD)
    record["source"]["salt"] = SURROGATE
    f.put_record(plants.KA_RECORD, record)
    return MANIFEST, "salt", "G1"


SITES = {"G11's circuit_qasm": ("atlas", surrogate_in_a_submit_file),
         "an Atlas commitments line": ("atlas", surrogate_in_a_commitments_line),
         "a salt the manifest and the record agree on": ("ibm", surrogate_in_a_salt_the_manifest_and_the_record_agree_on)}


def surrogate_moth(tmp_path, site):
    kind, plant = SITES[site]
    if kind == "atlas":
        _, moth = synthetic_moth(tmp_path)
    else:
        moth = moth_copy(tmp_path)
    rel, field, guard = plant(moth)
    return kind, moth, rel, field, guard


def refused_naming(line, rel, field, guard):
    return (line.startswith(f"REFUSED metadata-generated at {rel}: {guard}: ") and f"{field} holds a string UTF-8 cannot "
            "encode" in line and line.count("\n") == 1)


@pytest.mark.parametrize("site", sorted(SITES))
def test_a_records_string_utf8_cannot_encode_is_the_records_refused_and_never_the_adapter_failing(tmp_path, monkeypatch, site):
    pin_p2(monkeypatch, None)
    kind, moth, rel, field, guard = surrogate_moth(tmp_path, site)
    code, stdout, err = run(tmp_path, [kind, "--moth", str(moth), "--out", str(tmp_path / "out"), "--slice"])
    assert (code, err) == (1, b"") and refused_naming(stdout.decode("ascii"), rel, field, guard), (stdout, err)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("site", sorted(SITES))
def test_a_records_string_utf8_cannot_encode_is_the_records_refused_as_a_process(tmp_path, site):
    kind, moth, rel, field, guard = surrogate_moth(tmp_path, site)
    p = process([kind, "--moth", str(moth), "--out", str(tmp_path / "out"), "--slice"])
    assert (p.returncode, p.stderr) == (1, b"") and refused_naming(p.stdout.decode("ascii"), rel, field, guard), \
        (p.stdout[-300:], p.stderr[-300:])
    assert not (tmp_path / "out").exists()


# -- so is one nested as deep as the reader reads (P1.2's fifth verifier, D1: a recursive walk failed 1,000 levels down) ---------------------
DEEP_SITES = ["the IBM slice's job line", "an Atlas submit file"]


def deep_site(tmp_path, site):
    """(kind, moth, the record, the object it holds, its path in the crate): the known-answer job line of a copy of
    the twin, which the plan reads for the jobs a slice carries; or a submit file of a synthetic Atlas day, which the
    generator reads."""
    if site == "the IBM slice's job line":
        kind, moth = "ibm", moth_copy(tmp_path)
        path = next(moth.rglob("known-answer-line.json"))
    else:
        kind, (_, moth) = "atlas", synthetic_moth(tmp_path)
        path = next(moth.rglob("atlas-*-submit.json"))
    return kind, moth, path, json.loads(path.read_bytes()), path.relative_to(moth / "docs" / "records").as_posix()


def deepen(path, original, n):
    """`path` holding the object `original` and one member more, "deep": a lone surrogate n one-element arrays down,
    written as text, the surrogate as the escape (json.dumps of so deep a value would meet the host's own limit)."""
    text = json.dumps(original, sort_keys=True, separators=(",", ":"))
    assert "deep" not in original and text.endswith("}")
    path.write_bytes((text[:-1] + ',"deep":' + "[" * n + '"\\ud800"' + "]" * n + "}\n").encode("ascii"))


def deepest(admitted, lo=1000):
    """The largest n that `admitted` takes, it taking every n up to one and none above: from `lo`, which it must take,
    doubling, then halving. The reader's limit is the host's own, and its own in each process: it is found, never written
    down."""
    assert admitted(lo), lo
    hi = 2 * lo
    while admitted(hi):
        lo, hi = hi, 2 * hi
        assert hi < 2 ** 24
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if admitted(mid) else (lo, mid)
    return lo


def surrogate_or_too_deep(code, stdout, stderr, rel, n):
    """True for the surrogate's own refusal at depth n, the field named in full; False for the reader's refusal of a
    record nested deeper than it reads. Either is the records refused, exit 1 and one REFUSED line at the record; anything
    else, the adapter failing above all, fails the test. The surrogate's line is the refusal's whole text as the command
    line writes it: escaped and cut at LINE_MAX characters, where it says how many it did not write (P0.7: the field of a
    record nested past about 1,300 deep is longer than a line), so it is held to `escape(whole, LINE_MAX)`, never to a
    suffix the cut may have taken."""
    line = stdout.decode("ascii")
    assert (code, stderr) == (1, b"") and line.count("\n") == 1, (code, stdout[:200], stderr[-300:])
    prefix = f"REFUSED metadata-generated at {rel}: "
    assert line.startswith(prefix), line[:300]
    guard = re.match(r"(G[0-9]+: [^ ]*?): deep\[", line[len(prefix):])       # the guard, then the record's place in the records
    if guard:
        whole = f"{prefix}{guard.group(1)}: deep{'[0]' * n} holds a string UTF-8 cannot encode (a lone surrogate)"
        if line == escape(whole, LINE_MAX) + "\n":
            return True
    assert line.endswith(": nested deeper than the reader reads\n"), line[:300]
    return False


@pytest.mark.parametrize("site", DEEP_SITES)
def test_a_records_unencodable_string_at_any_depth_the_reader_admits_is_the_records_refused(tmp_path, monkeypatch, site):
    """At depth 1,000, where round 4's recursive walk failed, exit 3, and at the reader's own limit here, found by asking
    it: the records refused, exit 1, the field named in full, nothing left; one level deeper, the reader's own refusal,
    exit 1 still."""
    pin_p2(monkeypatch, None)
    kind, moth, path, original, rel = deep_site(tmp_path, site)
    out = tmp_path / "out"

    def admitted(n):
        deepen(path, original, n)
        code, stdout, err = run(tmp_path, [kind, "--moth", str(moth), "--out", str(out), "--slice"])
        assert not out.exists()
        return surrogate_or_too_deep(code, stdout, err, rel, n)
    assert deepest(admitted) >= 1000


@pytest.mark.parametrize("site", DEEP_SITES)
def test_a_records_unencodable_string_at_any_depth_the_reader_admits_is_the_records_refused_as_a_process(tmp_path, site):
    """The same of the adapter as a process, whose reader's limit is its own, found by asking it."""
    kind, moth, path, original, rel = deep_site(tmp_path, site)
    out = tmp_path / "out"

    def admitted(n):
        deepen(path, original, n)
        p = process([kind, "--moth", str(moth), "--out", str(out), "--slice"])
        assert not out.exists()
        return surrogate_or_too_deep(p.returncode, p.stdout, p.stderr, rel, n)
    assert deepest(admitted) >= 1000


# -- the adapter itself failing, exit 3, and a verdict that cannot be written ------------------------------------------------------------------------
def test_the_adapter_failing_is_not_a_verdict(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(A, "build", boom)
    code, out, err = run(tmp_path, twin_args(tmp_path / "out"))
    assert (code, out) == (3, b"")
    assert err == b"FAILED: the adapter itself failed, RuntimeError: boom; this is not a verdict\n"


@pytest.mark.parametrize("raised", [SystemExit(0), KeyboardInterrupt()], ids=["an exit", "an interrupt"])
def test_an_exit_or_an_interrupt_inside_the_adapter_is_exit_3(tmp_path, monkeypatch, raised):
    def boom(*a, **k):
        raise raised
    monkeypatch.setattr(A, "build", boom)
    code, out, err = run(tmp_path, twin_args(tmp_path / "out"))
    assert (code, out) == (3, b"") and err.startswith(b"FAILED: the adapter itself failed, ")


def closed_pipe():
    r, w = os.pipe()
    os.close(r)
    return w


@pytest.mark.parametrize("how", ["a pipe nobody reads", "a closed descriptor"])
def test_a_verdict_that_cannot_be_written_exits_3(tmp_path, quick, how):
    fd = closed_pipe() if how == "a pipe nobody reads" else 10**6
    try:
        code, out, err = run(tmp_path, twin_args(tmp_path / "out"), out=fd)
    finally:
        if how == "a pipe nobody reads":
            os.close(fd)
    assert code == 3 and (out, err) == (b"", b"")


def test_the_process_writing_to_a_pipe_nobody_reads_exits_3_and_never_120(tmp_path):
    w = closed_pipe()
    try:
        p = process(twin_args(tmp_path / "out"), stdout=w)
    finally:
        os.close(w)
    assert p.returncode == 3, p.stderr[-300:]


def test_the_process_calls_records_that_disagree_a_refusal_in_one_line_and_leaves_nothing(tmp_path):
    moth = moth_copy(tmp_path)
    gates = next(moth.rglob("known-answer.gates.json"))
    gates.write_bytes(gates.read_bytes() + b" ")
    p = process(["ibm", "--moth", str(moth), "--out", str(tmp_path / "out"), "--slice"])
    assert (p.returncode, p.stderr) == (1, b"") and p.stdout.count(b"\n") == 1, p.stdout[-300:]
    assert p.stdout.decode("ascii").startswith("REFUSED metadata-generated at 2026-10-05/ibm/ibm_kingston/")
    assert ": G1: " in p.stdout.decode("ascii") and not (tmp_path / "out").exists()


def test_the_process_calls_misuse_misuse():
    p = process(["ibm", "--moth", "x"])
    assert (p.returncode, p.stdout) == (2, b"") and USAGE.encode() in p.stderr


def test_the_synthetic_atlas_files_are_the_builders_own(tmp_path):
    """The Atlas crate of these tests holds the builder's results: layouts and a vector of P1.1's making."""
    crate = synthetic_atlas(tmp_path)
    assert (crate / "vectors" / "tomography-bitorder-2026-09-25.json").read_bytes() == p1_builder.atlas_vector()
    assert G.ATLAS_LAYOUTS and G.IBM_LAYOUTS


# -- the exits follow what failed (the verifier's D3): records the adapter cannot use are exit 1, an out it cannot make exit 2 ------------------
def built_as_process(tmp_path, moth, records=None):
    argv = ["ibm", "--moth", str(moth), "--out", str(tmp_path / "out"), "--slice"]
    return process(argv + ([] if records is None else ["--records", str(records)]))


def test_a_text_of_the_records_the_writer_refuses_is_a_verdict_on_the_records_as_a_process(tmp_path):
    """A qiskit version that holds a space is in an @id of the metadata, which the profile cannot spell: the writer's
    refusal, which is the records' (exit 1, one REFUSED line, nothing left), where it was exit 3, the adapter failing."""
    moth = moth_copy(tmp_path)
    f = plants.Forge(moth.joinpath("docs", "records"))
    f.edit_json(MANIFEST, lambda m: m["versions"].update(qiskit="2.5.2 x"))
    f.reseal_bundle(BUNDLE)
    p = built_as_process(tmp_path, moth)
    line = p.stdout.decode("ascii")
    assert (p.returncode, p.stderr) == (1, b"") and line.count("\n") == 1, (p.stdout[-300:], p.stderr[-300:])
    assert line.startswith("REFUSED spelling at @graph[") and "an @id is printable ASCII with no space" in line, line
    assert not (tmp_path / "out").exists()


def test_a_program_name_that_cannot_be_spelt_is_the_same_verdict_and_one_that_can_is_built(tmp_path):
    ok = tmp_path / "ok"
    crate = twin_copy(ok)
    recommit(crate, {"program": "sampler2"})
    moth, records = moth_of(crate, ok)
    assert built_as_process(ok, moth, records).returncode == 0
    bad = tmp_path / "bad"
    crate = twin_copy(bad)
    recommit(crate, {"program": "my program"})
    moth, records = moth_of(crate, bad)
    p = built_as_process(bad, moth, records)
    assert p.returncode == 1 and p.stdout.startswith(b"REFUSED spelling at @graph["), (p.stdout[-300:], p.stderr[-300:])


def test_a_decode_rule_ibms_counts_cannot_read_is_a_verdict_on_the_records_as_a_process(tmp_path):
    """The manifest names the Atlas rule, and every record agrees, down to IBM's echo: G5 refuses, as step 9 would."""
    crate = twin_copy(tmp_path)
    recommit(crate, {"decode": p1_decode.ATLAS_RULE})
    moth, records = moth_of(crate, tmp_path)
    p = built_as_process(tmp_path, moth, records)
    line = p.stdout.decode("ascii")
    assert (p.returncode, p.stderr) == (1, b"") and line.count("\n") == 1, (p.stdout[-300:], p.stderr[-300:])
    assert line.startswith("REFUSED metadata-generated at 2026-10-05/ibm/ibm_kingston/") and ": G5: " in line, line
    assert "does not read the order atlas-register" in line and not (tmp_path / "out").exists()


def test_a_manifests_options_digest_that_is_not_the_digest_of_its_options_is_refused_and_not_built_as_a_process(tmp_path):
    """Step 4 refuses the crate such records make; the adapter no longer builds it."""
    crate = twin_copy(tmp_path)
    recommit(crate, {"options_sha256": "ab" * 32})
    moth, records = moth_of(crate, tmp_path)
    p = built_as_process(tmp_path, moth, records)
    line = p.stdout.decode("ascii")
    assert (p.returncode, p.stderr) == (1, b"") and ": G1: " in line and "options_sha256" in line, (line, p.stderr[-300:])
    assert not (tmp_path / "out").exists()


def test_an_out_that_cannot_be_made_is_misuse_as_a_process_and_what_is_in_its_way_is_left(tmp_path):
    blocker = tmp_path / "afile"
    blocker.write_bytes(b"mine")
    p = process(twin_args(blocker / "out"))
    assert (p.returncode, p.stdout) == (2, b"") and b"cannot be made" in p.stderr, (p.stdout, p.stderr[-300:])
    assert blocker.read_bytes() == b"mine" and [q.name for q in tmp_path.iterdir()] == ["afile"]


# -- an --out the host cannot use is misuse, exit 2, the out named (the second verifier's D1) --------------------------------------------------------------
def misuse_naming(err, out, why):
    """The misuse line names the out as given, escaped as every line is, and says why."""
    return err.startswith(escape(str(out)).encode("ascii") + b": " + why.encode("ascii")) and err.count(b"\n") == 1


@pytest.mark.parametrize("name", ["crate ", "  "], ids=["a last component ending in a space", "a name of spaces only"])
def test_an_out_the_host_spells_otherwise_is_misuse_and_nothing_is_left(tmp_path, name):
    """Windows makes a last component that ends in a space without the space, and finds nothing under the name as given
    after; a name of spaces only is, to it, the directory above. Either is an out the adapter cannot use: exit 2, the out
    named, nothing left. A host that keeps the space builds into it (exit 0)."""
    world = tmp_path / "world"
    world.mkdir()
    out = str(world) + os.sep + name
    code, stdout, err = run(tmp_path, twin_args(out))
    if os.name == "nt":
        assert (code, stdout) == (2, b"") and (misuse_naming(err, out, "cannot be made") or
                                               misuse_naming(err, out, "cannot be used")), err
        assert list(world.iterdir()) == []
    else:
        assert code == 0, err


def test_an_out_whose_name_ends_in_a_space_is_misuse_as_a_process_too(tmp_path):
    world = tmp_path / "world"
    world.mkdir()
    p = process(twin_args(str(world) + os.sep + "crate "))
    assert (p.returncode, p.stdout) == ((2, b"") if os.name == "nt" else (0, p.stdout)), (p.stdout, p.stderr[-300:])
    if os.name == "nt":
        assert list(world.iterdir()) == [] and b"cannot be made" in p.stderr


def test_an_out_the_host_cannot_list_is_misuse_and_is_left_as_it_was(tmp_path, monkeypatch):
    """Simulated, as no directory in the sandbox can be made unlistable: the host refuses to list the out."""
    out = tmp_path / "out"
    out.mkdir()
    real = Path.iterdir

    def iterdir(self):
        if self == out:
            raise PermissionError(13, "Access is denied")
        return real(self)
    monkeypatch.setattr(Path, "iterdir", iterdir)
    code, stdout, err = run(tmp_path, twin_args(out))
    assert (code, stdout) == (2, b"") and misuse_naming(err, out, "cannot be used (Access is denied)"), err
    monkeypatch.undo()
    assert out.is_dir() and list(out.iterdir()) == []


def test_an_out_too_long_for_the_host_is_misuse_the_out_named_and_nothing_is_made(tmp_path):
    """Windows refuses a path of 32,768 characters or more with a ValueError, not an OSError (a host that limits a name's
    length refuses it with an OSError): either is an out the adapter cannot use, exit 2, the out named. In process only: no
    command line can carry such an argument."""
    world = tmp_path / "world"
    world.mkdir()
    out = str(world / ("z" * 40000))
    code, stdout, err = run(tmp_path, twin_args(out))
    assert (code, stdout) == (2, b"") and err.count(b"\n") == 1 and err.endswith(b" more characters)\n"), err[-300:]
    # the line is the misuse's text cut at LINE_MAX (P0.7): the out, 40,000 characters, fills it, so the reason is cut off
    # with the rest, and what is left is the out as far as the cap, then the count of the characters not written
    assert err.isascii() and err.startswith(escape(out[:1000]).encode("ascii")), err[:100]
    assert list(world.iterdir()) == []


def test_a_value_error_of_the_host_looking_at_the_out_is_misuse_too(tmp_path, monkeypatch):
    """check_out's look at the out refused by the host with a ValueError: the out cannot be used, exit 2."""
    out = tmp_path / "out"
    real = os.path.realpath

    def realpath(path, *a, **k):
        if str(path) == str(out):
            raise ValueError("realpath: path too long for Windows")
        return real(path, *a, **k)
    monkeypatch.setattr(os.path, "realpath", realpath)
    code, stdout, err = run(tmp_path, twin_args(out))
    assert (code, stdout) == (2, b"") and misuse_naming(err, out, "cannot be used (realpath: path too long"), err
    assert not out.exists()


def test_check_outs_own_refusals_pass_its_conversion_of_the_hosts_errors_as_they_are(tmp_path):
    """An AdapterError is a ValueError: check_out's own refusal is never taken for the host's, and keeps its words."""
    out = tmp_path / "out"
    (out / "sub").mkdir(parents=True)
    code, stdout, err = run(tmp_path, twin_args(out))
    assert (code, stdout) == (2, b"") and misuse_naming(err, out, "not an empty directory"), err


def test_a_value_error_of_the_host_at_the_first_entry_under_the_out_is_the_out_refused(tmp_path, monkeypatch):
    """The first entry under the out refused by the host with a ValueError, as one under a very long out is: misuse."""
    out = tmp_path / "world" / "out"
    real = os.mkdir

    def mkdir(path, *a, **k):
        if Path(path).parent == out:
            raise ValueError("mkdir: path too long for Windows")
        return real(path, *a, **k)
    monkeypatch.setattr(os, "mkdir", mkdir)
    code, stdout, err = run(tmp_path, twin_args(out))
    assert (code, stdout) == (2, b"") and misuse_naming(err, out, "cannot be made (mkdir: path too long for Windows)"), err
    assert not (tmp_path / "world").exists()


@pytest.mark.parametrize("depth, code", [(1, 2), (2, 3)], ids=["the first entry under the out", "an entry below it"])
def test_the_host_refusing_the_first_entry_under_the_out_is_misuse_and_one_below_it_the_adapter_failing(tmp_path,
                                                                                                        monkeypatch, depth,
                                                                                                        code):
    """The out is made; the host then refuses to make the first entry under it (misuse, exit 2, the out named), or an
    entry deeper down (the adapter failing, exit 3). Either way nothing is left."""
    out = tmp_path / "world" / "out"
    real = os.mkdir

    def mkdir(path, *a, **k):
        p = Path(path)
        if out in p.parents and len(p.relative_to(out).parts) == depth:
            raise PermissionError(13, "Access is denied")
        return real(path, *a, **k)
    monkeypatch.setattr(os, "mkdir", mkdir)
    c, stdout, err = run(tmp_path, twin_args(out))
    assert (c, stdout) == (code, b""), err
    if code == 2:
        assert misuse_naming(err, out, "cannot be made (Access is denied)"), err
    else:
        assert err.startswith(b"FAILED: the adapter itself failed, PermissionError"), err
    assert not (tmp_path / "world").exists()


def test_a_level_below_the_first_under_the_out_failing_is_the_adapter_failing_though_the_build_made_nothing_above_it(
        tmp_path, monkeypatch):
    """Another makes the directory where the build's first entry goes, just after the out is made, and the host then refuses
    the build's next level, below it: only the first level under the out is the out's, so this is the adapter failing,
    exit 3, though the build has made nothing under the out yet. The other's directory stays, and the out with it."""
    out, real_first_missing, real_mkdir = tmp_path / "out", A._first_missing, os.mkdir
    first = out / A.plan("ibm", TWIN, ROOT / "records", True)[0][0].split("/")[0]

    def first_missing(path):
        top = real_first_missing(path)
        if out in Path(path).parents and not first.exists():
            real_mkdir(first)                                   # another's, where the build's first entry goes
        return top

    def mkdir(path, *a, **k):
        if Path(path).parent == first:
            raise PermissionError(13, "Access is denied")
        return real_mkdir(path, *a, **k)
    monkeypatch.setattr(A, "_first_missing", first_missing)
    monkeypatch.setattr(os, "mkdir", mkdir)
    code, stdout, err = run(tmp_path, twin_args(out))
    assert (code, stdout) == (3, b"") and err.startswith(b"FAILED: the adapter itself failed, PermissionError"), err
    assert listing(out) == [first.name]


def test_only_the_first_entry_under_the_out_is_the_out_failing_a_later_one_is_the_hosts_error_as_it_is(tmp_path,
                                                                                                      monkeypatch):
    """A file the build makes as its first entry under the out: the host refusing it is the out refused; the same refusal
    of a second entry, once the first was made, is the host's error as it is."""
    out = tmp_path / "out"
    out.mkdir()
    real, refused = open, PermissionError(13, "Access is denied")

    def refusing(path, mode="r", *a, **k):
        if Path(path).name in ("first", "second"):
            raise refused
        return real(path, mode, *a, **k)
    made = A._Made(out)
    monkeypatch.setattr(A, "open", refusing, raising=False)
    with pytest.raises(A.AdapterError, match="cannot be made"):
        made.write(out / "first", b"1")
    monkeypatch.setattr(A, "open", real, raising=False)
    made.write(out / "ok", b"2")
    monkeypatch.setattr(A, "open", refusing, raising=False)
    with pytest.raises(PermissionError):
        made.write(out / "second", b"3")
    assert [p.name for p, _ in made.files] == ["ok"] and made.bytes == 1


def test_another_files_entry_in_the_way_of_the_first_entry_under_the_out_is_never_called_the_outs_fault(tmp_path,
                                                                                                      monkeypatch):
    """Another makes a file where the build's first directory under the out goes, after the out is made: that is another's
    entry in the way (the adapter failing, exit 3, as any of another's files in the build's way), never the out refused;
    the file is left."""
    out, real = tmp_path / "out", A._first_missing
    theirs = out / A.plan("ibm", TWIN, ROOT / "records", True)[0][0].split("/")[0]     # the build's first entry there

    def first_missing(path):
        top = real(path)                                    # found missing, then made by another before the build's mkdir
        if out in Path(path).parents and not theirs.exists():
            theirs.write_bytes(b"theirs")
        return top
    monkeypatch.setattr(A, "_first_missing", first_missing)
    code, stdout, err = run(tmp_path, twin_args(out))
    assert (code, stdout) == (3, b"") and b"FileExistsError" in err, err
    assert theirs.read_bytes() == b"theirs" and listing(out) == [theirs.name]


def test_a_failed_build_removes_the_directories_it_made_on_the_way_to_its_out_and_no_other(tmp_path, quick):
    moth = moth_copy(tmp_path)
    gates = next(moth.rglob("known-answer.gates.json"))
    gates.write_bytes(gates.read_bytes() + b" ")
    (tmp_path / "kept").mkdir()
    for out in (tmp_path / "kept" / "p" / "q" / "out", tmp_path / "r" / "out"):
        code, stdout, err = run(tmp_path, ["ibm", "--moth", str(moth), "--out", str(out), "--slice"])
        assert code == 1 and not out.exists()
    assert sorted(q.name for q in tmp_path.iterdir() if q.name != "moth" and not q.name.endswith(".bin")) == ["kept"]
    assert list((tmp_path / "kept").iterdir()) == []                 # what it had not made, it left; what it had, it removed


def test_first_missing_is_the_topmost_directory_a_build_makes_first(tmp_path):
    assert A._first_missing(tmp_path) is None
    assert A._first_missing(tmp_path / "a" / "b" / "c") == tmp_path / "a"
    (tmp_path / "a").mkdir()
    assert A._first_missing(tmp_path / "a" / "b" / "c") == tmp_path / "a" / "b"


# -- an --out that names no directory an entry can be made in is misuse, exit 2, the out named (P1.2's fifth verifier, D2). The host
#    reaches no network path in these tests (tests/p1/p1_hosts.py), whatever the guard does ----------------------------------------------------
DEGENERATE = ["\\\\", "//", "\\\\\\", "\\\\server", "\\\\server\\", "//server", "\\\\?\\", "\\\\.\\", "\\\\?\\UNC\\",
              "\\\\?\\UNC\\server", "\\\\wsl$", "\\\\?\\C:", "\\\\.\\C:", "\\\\?\\GLOBALROOT", "\\\\.\\pipe"]


@pytest.fixture
def unreachable(monkeypatch):
    """No network path reaches the network; the calls the host was asked on one, listed."""
    p1_hosts.install("unreachable", monkeypatch, A)
    return p1_hosts.asked


def hosted(kind, paths, argv):
    """The adapter's command line as a process, under a host tests/p1/p1_hosts.py simulates."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, str(Path(p1_hosts.__file__)), kind, *map(str, paths), "--", *argv],
                          capture_output=True, env=env, cwd=ROOT)


def test_an_out_spelt_with_no_share_or_no_name_is_misuse_told_before_the_host_is_asked(tmp_path, unreachable):
    """The verifier's spellings and their kin: a network, extended-length or device spelling onto which pathlib joins the
    build's entries as a server, a share or a device, not in it. Each is refused, exit 2, the out named, and the host is
    asked nothing of it."""
    assert os.name != "nt" or all((Path(s) / canonical.DESCRIPTOR).parent != Path(s) for s in DEGENERATE)
    for out in DEGENERATE if os.name == "nt" else []:
        code, stdout, err = run(tmp_path, records_args(out))
        assert (code, stdout) == (2, b"") and misuse_naming(err, Path(out), "names no directory an entry can be made in"), \
            (out, err)
    assert unreachable == [] and sorted(p.name for p in tmp_path.iterdir()) == ["stderr.bin", "stdout.bin"]


def test_an_out_spelt_with_no_share_or_no_name_is_misuse_as_a_process():
    for out in ["\\\\", "\\\\server", "\\\\?\\", "\\\\.\\", "\\\\?\\UNC\\server", "\\\\wsl$"] if os.name == "nt" else []:
        p = hosted("unreachable", [], records_args(out))
        assert (p.returncode, p.stdout) == (2, b"") and \
            misuse_naming(p.stderr, Path(out), "names no directory an entry can be made in"), (out, p.stderr[-300:])


def test_a_share_the_host_cannot_reach_is_misuse_and_a_drive_relative_or_a_relative_new_directory_is_built(
        tmp_path, monkeypatch, unreachable, quick):
    """The verifier's controls: a share the host cannot reach, a root that is not there, and a directory on it, which
    cannot be made, are misuse, exit 2, the out named; a drive-relative and a relative new directory are built, and so is
    `.`, a root to pathlib (its own parent) that is there, when it is empty."""
    world = tmp_path / "world"
    world.mkdir()
    monkeypatch.chdir(world)
    shares = [("\\\\server\\share", "a root that is not there"), ("\\\\?\\UNC\\server\\share", "a root that is not there"),
              ("\\\\server\\share\\x", "cannot be made (The network path was not found)")]
    for out, why in shares if os.name == "nt" else []:
        code, stdout, err = run(tmp_path, records_args(out))
        assert (code, stdout) == (2, b"") and misuse_naming(err, Path(out), why), (out, err)
    for out in (tmp_path.drive + "x", "relative-new"):
        code, stdout, err = run(tmp_path, records_args(out))
        assert code == 0 and LINE.fullmatch(stdout.decode("ascii").rstrip("\n")), (out, stdout, err)
    assert sorted(p.name for p in world.iterdir()) == ["relative-new", "x"]
    assert (world / "x" / canonical.DESCRIPTOR).is_file() and (world / "relative-new" / canonical.DESCRIPTOR).is_file()
    dot = tmp_path / "dot"
    dot.mkdir()
    monkeypatch.chdir(dot)
    assert Path(".").parent == Path(".")
    code, stdout, err = run(tmp_path, records_args("."))
    assert code == 0 and (dot / canonical.DESCRIPTOR).is_file(), (stdout, err)


# -- a --moth or a --records the host will not let the adapter look at is misuse, exit 2, the input named; a record it will not let the
#    adapter read once the build is under way is the adapter failing, exit 3 (P1.2's fifth verifier, D3). Simulated (p1_hosts) ---------
def looked_at(err, option, given, at=None, why="Network access is denied"):
    """The misuse line names the input, and the place in it the host refused, and says why."""
    head = f"{option} {given}: cannot be looked at" + (f": {at}" if at else "") + f" ({why})"
    return err.startswith(escape(head).encode("ascii")) and err.count(b"\n") == 1


@pytest.mark.parametrize("kind, sliced", [("ibm", False), ("ibm", True), ("atlas", True)], ids=["ibm", "an ibm slice", "atlas"])
def test_a_moth_the_host_will_not_let_the_adapter_look_at_is_misuse_the_input_named(tmp_path, monkeypatch, kind, sliced):
    moth = tmp_path / "moth"
    moth.mkdir()
    p1_hosts.install("denied", monkeypatch, A, [moth])
    out = tmp_path / "out"
    code, stdout, err = run(tmp_path, [kind, "--moth", str(moth), "--out", str(out)] + (["--slice"] if sliced else []))
    assert (code, stdout) == (2, b"") and looked_at(err, "--moth", moth), err
    assert not out.exists()


def test_a_records_the_host_will_not_let_the_adapter_look_at_is_misuse_the_input_and_the_place_named(tmp_path, monkeypatch):
    records = tmp_path / "records"
    records.mkdir()
    p1_hosts.install("denied", monkeypatch, A, [records])
    code, stdout, err = run(tmp_path, twin_args(tmp_path / "out", "--records", str(records)))
    assert (code, stdout) == (2, b"") and looked_at(err, "--records", records, at=records / G.READ), err
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("kind, inside", [("ibm", "2026-10-05/ibm/ibm_kingston/run"), ("atlas", "2026-09-25/p3")],
                         ids=["a directory of the IBM records", "an Atlas day's"])
def test_a_directory_in_the_moth_the_host_will_not_let_the_adapter_look_at_is_misuse_the_place_named(tmp_path, monkeypatch,
                                                                                                    kind, inside):
    """A directory of the records the plan lists that the host will not let the adapter look at: os.walk, the plan's
    walk, would have passed over it, as if it held nothing."""
    pin_p2(monkeypatch, None)
    moth = moth_copy(tmp_path) if kind == "ibm" else synthetic_moth(tmp_path)[1]
    place = moth.joinpath("docs", "records", *inside.split("/"))
    assert place.is_dir()
    p1_hosts.install("denied", monkeypatch, A, [place])
    code, stdout, err = run(tmp_path, [kind, "--moth", str(moth), "--out", str(tmp_path / "out"), "--slice"])
    assert (code, stdout) == (2, b"") and looked_at(err, "--moth", moth, at=place), err
    assert not (tmp_path / "out").exists()


def test_a_directory_the_host_will_not_list_is_never_passed_over(tmp_path, monkeypatch):
    """The listing alone refused, as os.scandir refuses it, where os.walk calls no handler of its own and goes on."""
    moth = moth_copy(tmp_path)
    run_dir = moth.joinpath("docs", "records", *IBM_DIR.split("/"), "run")
    real = os.scandir

    def scandir(*a, **k):
        if a and Path(a[0]) == run_dir:
            raise PermissionError(13, "Access is denied", str(run_dir))
        return real(*a, **k)
    monkeypatch.setattr(os, "scandir", scandir)
    with pytest.raises(A.AdapterError) as x:
        A.plan("ibm", moth, ROOT / "records", True)
    assert str(x.value) == f"--moth {moth}: cannot be looked at: {run_dir} (Access is denied)"


@pytest.mark.parametrize("record", ["bundle/manifest.json", "run/known-answer-line.json"],
                         ids=["a record the build copies", "a job line the slice reads"])
def test_a_record_the_host_will_not_let_the_adapter_read_once_the_build_is_under_way_is_the_adapter_failing(tmp_path,
                                                                                                         monkeypatch, record):
    moth = moth_copy(tmp_path)
    path = moth.joinpath("docs", "records", *IBM_DIR.split("/"), *record.split("/"))
    assert path.is_file()
    p1_hosts.install("unreadable", monkeypatch, A, [path])
    code, stdout, err = run(tmp_path, ["ibm", "--moth", str(moth), "--out", str(tmp_path / "out"), "--slice"])
    assert (code, stdout) == (3, b"") and err.startswith(b"FAILED: the adapter itself failed, PermissionError"), err
    assert not (tmp_path / "out").exists()


def test_inputs_the_host_will_not_let_the_adapter_look_at_are_misuse_and_a_record_it_will_not_read_the_adapter_failing_as_processes(
        tmp_path):
    moth = moth_copy(tmp_path)
    out = tmp_path / "out"
    p = hosted("denied", [moth], ["ibm", "--moth", str(moth), "--out", str(out), "--slice"])
    assert (p.returncode, p.stdout) == (2, b"") and looked_at(p.stderr, "--moth", moth), p.stderr[-300:]
    records = tmp_path / "records"
    records.mkdir()
    p = hosted("denied", [records], twin_args(out, "--records", str(records)))
    assert (p.returncode, p.stdout) == (2, b"") and looked_at(p.stderr, "--records", records, at=records / G.READ), \
        p.stderr[-300:]
    manifest = moth.joinpath("docs", "records", *MANIFEST.split("/"))
    p = hosted("unreadable", [manifest], ["ibm", "--moth", str(moth), "--out", str(out), "--slice"])
    assert (p.returncode, p.stdout) == (3, b"") and p.stderr.startswith(b"FAILED: the adapter itself failed, PermissionError"), \
        p.stderr[-300:]
    assert not out.exists()


def test_git_the_host_will_not_start_in_the_checkout_is_misuse_the_input_named(tmp_path, toy, monkeypatch):
    real = subprocess.run

    def refusing(args, *a, **k):
        if args[:1] == ["git"] and Path(k.get("cwd") or ".") == toy:
            raise PermissionError(13, "Access is denied", str(toy))
        return real(args, *a, **k)
    monkeypatch.setattr(subprocess, "run", refusing)
    code, stdout, err = run(tmp_path, ["ibm", "--moth", str(toy), "--out", str(tmp_path / "out")])
    assert (code, stdout) == (2, b"") and looked_at(err, "--moth", toy, why="git cannot start in it: Access is denied"), err
    assert not (tmp_path / "out").exists()


def test_no_git_on_the_path_is_the_adapter_failing_as_a_process(tmp_path, toy):
    """docs/P1.md's exit-3 list: git that cannot be found is not the checkout's fault, and is no misuse."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT), PATH=str(Path(sys.executable).parent))
    p = subprocess.run([sys.executable, "-m", "qro.p1_adapter", "ibm", "--moth", str(toy), "--out", str(tmp_path / "out")],
                       capture_output=True, env=env, cwd=ROOT)
    assert (p.returncode, p.stdout) == (3, b"") and p.stderr.startswith(b"FAILED: the adapter itself failed, FileNotFoundError"), \
        p.stderr[-300:]
    assert not (tmp_path / "out").exists()


# -- a failed build removes what it made and only that (the lead's ruling of 2026-10-26, after a mutant of the old cleanup ran rmtree
#    on the users folder). Each world below is built under the test's own tmp_path, and so is every path the cleanup is handed,
#    even one it is meant to leave ---------------------------------------------------------------------------------------------------
def disagreeing(tmp_path):
    """A copy of the twin at tmp_path/moth whose records disagree (G1): a build of it copies every file, then fails."""
    moth = moth_copy(tmp_path)
    gates = next(moth.rglob("known-answer.gates.json"))
    gates.write_bytes(gates.read_bytes() + b" ")
    return moth


def failed(tmp_path, moth, out, where="2026-10-05/ibm/ibm_kingston/", guard="G1"):
    """The adapter, in process, on `moth` into `out`: it must be the records refused, by G1 unless the test says which
    guard and where, whatever was cleared."""
    code, stdout, err = run(tmp_path, ["ibm", "--moth", str(moth), "--out", str(out), "--slice"])
    assert (code, err) == (1, b"") and stdout.startswith(f"REFUSED metadata-generated at {where}".encode()), stdout
    assert f": {guard}: ".encode() in stdout and stdout.count(b"\n") == 1, stdout


def listing(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))


def link_to(target, link):
    """A link at `link` to the directory `target`: a junction on Windows, which needs no privilege; a symbolic link elsewhere."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(target, link, target_is_directory=True)


def unlink_link(link):
    """The link `link_to` made, removed while its target is there: this host removes no junction whose target is gone."""
    if os.name == "nt":
        os.rmdir(link)                                          # a junction's rmdir removes the junction, never its target
    else:
        os.unlink(link)


@pytest.fixture
def cleared(monkeypatch, tmp_path):
    """What each failed build had listed as made when it was cleared, and what was then under tmp_path:
    [(its directories, its files, {path: is a directory})]."""
    seen, real = [], A._clear

    def spy(made):
        seen.append(([p for p, _ in made.directories], [p for p, _ in made.files],
                     {p: p.is_dir() for p in tmp_path.rglob("*")}))
        real(made)
    monkeypatch.setattr(A, "_clear", spy)
    return seen


def test_a_failed_build_into_a_fresh_nested_out_lists_exactly_what_it_made_and_leaves_none_of_it(tmp_path, quick, monkeypatch,
                                                                                                cleared):
    pin_p2(monkeypatch, None)
    moth, world = disagreeing(tmp_path), tmp_path / "world"
    world.mkdir()
    out = world / "a" / "b" / "out"
    failed(tmp_path, moth, out)
    [(directories, files, there)] = cleared
    made = {p: is_dir for p, is_dir in there.items() if world in p.parents}
    assert set(directories) == {p for p, is_dir in made.items() if is_dir} and len(directories) == len(set(directories))
    assert set(files) == {p for p, is_dir in made.items() if not is_dir} and len(files) == 72      # every copy, listed once
    assert directories[:3] == [world / "a", world / "a" / "b", out]                                 # one level at a time
    assert listing(world) == []                                                                     # and none of it is left


@pytest.mark.parametrize("how", ["through P2's seam", "in the generator's step"])
def test_a_file_another_puts_in_a_directory_the_build_made_stays_with_that_directory_and_every_one_above_it(tmp_path, quick,
                                                                                                         monkeypatch, how):
    moth, world = disagreeing(tmp_path), tmp_path / "world"
    out = world / "new" / "out"
    theirs = out / "2026-10-05" / "ibm" / "theirs.txt"

    def put():
        assert theirs.parent.is_dir() and not theirs.exists()                   # a directory the build has made
        theirs.write_bytes(b"not the build's")
    if how == "through P2's seam":
        pin_p2(monkeypatch, standin(question_files=lambda crate: put() or {}))
    else:
        pin_p2(monkeypatch, None)
        step = G.ibm
        monkeypatch.setattr(G, "ibm", lambda crate: put() or step(crate))
    failed(tmp_path, moth, out, where="2026-10-05/ibm/theirs.txt", guard="G12")        # the generator sees it as foreign, too
    assert theirs.read_bytes() == b"not the build's"
    assert listing(world) == ["new", "new/out", "new/out/2026-10-05", "new/out/2026-10-05/ibm",
                              "new/out/2026-10-05/ibm/theirs.txt"]


def test_a_file_another_put_in_the_place_of_one_the_build_wrote_is_left_and_so_is_its_directory(tmp_path, quick, monkeypatch):
    moth, world = disagreeing(tmp_path), tmp_path / "world"
    out = world / "out"
    licence = out / "LICENSE-quantum-film"

    def swap(crate):
        assert licence.is_file()
        (world / "theirs").write_bytes(b"theirs")
        os.replace(world / "theirs", licence)            # theirs is made while the build's still is, so never has its number
        return {}
    pin_p2(monkeypatch, standin(question_files=swap))
    failed(tmp_path, moth, out)
    assert licence.read_bytes() == b"theirs" and listing(world) == ["out", "out/LICENSE-quantum-film"]


@pytest.mark.parametrize("by", ["a directory", "a link to where it went"])
def test_a_directory_the_build_made_moved_away_and_replaced_is_left_and_nothing_is_reached_through_it(tmp_path, quick,
                                                                                                    monkeypatch, by):
    """Another moves a directory the build made out of the way, the build's files with it, and puts in its place a directory
    of its own or a link to where the first went: what is in its place stays, and nothing is removed through it."""
    moth, world = disagreeing(tmp_path), tmp_path / "world"
    out, went = world / "out", world / "went"
    read = out / "2026-10-14"
    seen = {}

    def swap(crate):
        read.rename(went)
        seen["went"] = listing(went)
        if by == "a directory":
            read.mkdir()
        else:
            link_to(went, read)
            seen["linked"] = True
        return {}
    pin_p2(monkeypatch, standin(question_files=swap))
    try:
        failed(tmp_path, moth, out)
        assert len(seen["went"]) > 10 and listing(went) == seen["went"]      # what the build made, moved: never reached
        assert sorted(p.name for p in world.iterdir()) == ["out", "went"] and [p.name for p in out.iterdir()] == ["2026-10-14"]
        if by == "a directory":
            assert read.is_dir() and not any(read.iterdir())
        else:
            assert os.path.samefile(read, went) and not read.joinpath("x").exists()
    finally:
        if seen.get("linked"):                                  # the junction this test made goes before the test ends,
            went.mkdir(exist_ok=True)                           # its target there (made again if it is gone): this host
            unlink_link(read)                                   # removes no junction whose target is gone
    if by != "a directory":
        assert not os.path.lexists(read) and listing(went) == seen["went"]       # the link gone, what it named intact


@pytest.mark.parametrize("held", ["a file", "nothing"])
def test_a_list_made_wrong_on_purpose_removes_nothing_that_holds_anything_nor_any_directory_that_was_there(tmp_path, quick,
                                                                                                         monkeypatch, cleared,
                                                                                                         held):
    """`_first_missing` made to name, for every path, a directory inside tmp_path that was there before the build and is an
    ancestor of the out: the build starts making there, finds it there, and does not list it, nor remove it."""
    pin_p2(monkeypatch, None)
    moth, world = disagreeing(tmp_path), tmp_path / "world"
    there = world / "there"
    there.mkdir(parents=True)
    if held == "a file":
        (there / "keep.txt").write_bytes(b"mine")
    monkeypatch.setattr(A, "_first_missing", lambda path: there)
    failed(tmp_path, moth, there / "p" / "q" / "out")
    [(directories, files, _)] = cleared
    assert directories[:3] == [there / "p", there / "p" / "q", there / "p" / "q" / "out"] and len(files) == 72
    assert listing(world) == ["there"] + (["there/keep.txt"] if held == "a file" else [])
    if held == "a file":
        assert (there / "keep.txt").read_bytes() == b"mine"


@pytest.mark.parametrize("fails", ["os.unlink", "os.rmdir", "_clear"])
def test_a_failure_to_clear_never_replaces_the_builds_own_verdict_and_what_could_not_be_removed_is_left(tmp_path, quick,
                                                                                                      monkeypatch, fails):
    pin_p2(monkeypatch, None)
    moth, world = disagreeing(tmp_path), tmp_path / "world"
    out = world / "out"

    def refused(*a, **k):
        raise RuntimeError("a fault in the clearing") if fails == "_clear" else PermissionError(13, "held by another")
    if fails == "_clear":
        monkeypatch.setattr(A, "_clear", refused)
    else:
        monkeypatch.setattr(os, fails.split(".")[1], refused)
    failed(tmp_path, moth, out)
    files = [p for p in world.rglob("*") if p.is_file()]
    if fails == "os.rmdir":
        assert out.is_dir() and files == []                     # every file unlinked, every directory left
    else:
        assert len(files) == 72                                 # nothing removed: every file the build wrote is left


def test_one_file_the_clearing_cannot_remove_is_left_with_its_directories_and_every_other_is_cleared(tmp_path, quick,
                                                                                                   monkeypatch):
    """One build file's unlink refused, that path alone (as a file another holds open is, on Windows): it stays, and so do
    the directories it is in, and every other file and directory the build made goes (P1.2's fourth verifier, C22)."""
    pin_p2(monkeypatch, None)
    moth, world = disagreeing(tmp_path), tmp_path / "world"
    out = world / "out"
    held = out / "2026-10-05" / "ibm" / "ibm_kingston" / "bundle" / "manifest.json"
    real = os.unlink

    def unlink(path, *a, **k):
        if Path(path) == held:
            raise PermissionError(13, "held by another")
        return real(path, *a, **k)
    monkeypatch.setattr(os, "unlink", unlink)
    failed(tmp_path, moth, out)
    monkeypatch.setattr(os, "unlink", real)
    assert listing(world) == ["out", "out/2026-10-05", "out/2026-10-05/ibm", "out/2026-10-05/ibm/ibm_kingston",
                              "out/2026-10-05/ibm/ibm_kingston/bundle", "out/2026-10-05/ibm/ibm_kingston/bundle/manifest.json"]


def test_a_failed_build_removes_the_files_of_the_question_it_wrote_too(tmp_path, quick, monkeypatch, cleared):
    pin_p2(monkeypatch, standin(question_files=lambda crate: {"law.json": b"{}\n", "more/x.json": b"[]\n"}))
    moth, world = disagreeing(tmp_path), tmp_path / "world"
    out = world / "out"
    failed(tmp_path, moth, out)
    [(directories, files, _)] = cleared
    assert {out / "question" / "law.json", out / "question" / "more" / "x.json"} <= set(files)
    assert {out / "question", out / "question" / "more"} <= set(directories) and listing(world) == []


def test_a_file_another_put_where_the_build_writes_is_never_overwritten_and_the_build_fails(tmp_path, quick, monkeypatch):
    out = tmp_path / "out"

    def question_files(crate):
        (crate / "question").mkdir()
        (crate / "question" / "law.json").write_bytes(b"theirs")
        return {"law.json": b"{}\n"}
    pin_p2(monkeypatch, standin(question_files=question_files))
    code, stdout, err = run(tmp_path, twin_args(out))
    assert (code, stdout) == (3, b"") and b"FileExistsError" in err, err
    assert (out / "question" / "law.json").read_bytes() == b"theirs"
    assert listing(out) == ["question", "question/law.json"]                    # and all the build had made is gone


def test_a_file_made_in_the_outs_place_as_the_build_makes_it_is_misuse_and_is_left(tmp_path, monkeypatch):
    """The out is found missing, and another makes a file of it before the build makes it: the build does not take that
    file for its directory, and it is left."""
    out, real = tmp_path / "out", A._first_missing

    def first_missing(path):
        top = real(path)
        if path == out:
            out.write_bytes(b"theirs")
        return top
    monkeypatch.setattr(A, "_first_missing", first_missing)
    code, stdout, err = run(tmp_path, twin_args(out))
    assert (code, stdout) == (2, b"") and b"cannot be made" in err and out.read_bytes() == b"theirs", err


def test_a_file_is_listed_before_a_byte_of_it_is_written_so_that_one_half_written_is_removed_too(tmp_path):
    made = A._Made(tmp_path)
    with pytest.raises(TypeError):
        made.write(tmp_path / "half", "not bytes")                              # created, then its write fails
    assert [p for p, _ in made.files] == [tmp_path / "half"] and (tmp_path / "half").exists()
    A._clear(made)
    assert listing(tmp_path) == []


@pytest.mark.parametrize("raised", [KeyboardInterrupt, SystemExit], ids=["an interrupt", "an exit"])
def test_an_interrupt_or_an_exit_inside_a_build_is_cleared_as_any_failure_is_and_still_raised(tmp_path, monkeypatch, raised):
    """The build clears on every BaseException, not only on an Exception: an interrupt in the middle leaves nothing made,
    and is raised as it came."""
    world = tmp_path / "world"
    real, n = A._Made.write, [0]

    def write(self, path, data):
        n[0] += 1
        if n[0] == 20:
            raise raised()
        return real(self, path, data)
    monkeypatch.setattr(A._Made, "write", write)
    with pytest.raises(raised):
        A.build("ibm", TWIN, world / "out", sliced=True)
    assert n[0] == 20 and not world.exists()


def test_a_files_identity_is_taken_from_the_handle_that_made_it_and_is_its_paths(tmp_path, monkeypatch):
    """The identity a written file is listed with is the open handle's (os.fstat), not its path's after the fact: the build
    lists it though the path cannot be looked at as it is written; and it is the identity its path has, which the
    clearing holds it to."""
    made = A._Made(tmp_path)
    real = os.lstat

    def lstat(path, *a, **k):
        if Path(path).name == "f":
            raise OSError(5, "the path cannot be looked at")
        return real(path, *a, **k)
    monkeypatch.setattr(os, "lstat", lstat)
    made.write(tmp_path / "f", b"bytes")
    monkeypatch.undo()
    [(path, identity)] = made.files
    assert path == tmp_path / "f" and identity == A._identity(path) and A._unchanged(path, identity, stat.S_ISREG)
    assert made.bytes == 5


def test_a_build_that_fails_while_it_says_what_it_built_is_cleared_too(tmp_path, monkeypatch, cleared):
    """What the build reports (its files, bytes and identity) is made inside the build: a failure there, with the crate
    complete, its descriptor written, clears it as any other failure does."""
    def boom(md):
        raise RuntimeError("the identity cannot be computed")
    monkeypatch.setattr(A.canonical, "body_digest", boom)              # the adapter is its only caller in a build
    out = tmp_path / "world" / "out"
    with pytest.raises(RuntimeError, match="cannot be computed"):
        A.build("ibm", TWIN, out, sliced=True)
    [(_, files, _)] = cleared
    assert files[-1] == out / canonical.DESCRIPTOR and not (tmp_path / "world").exists()


def test_the_counts_the_build_reports_are_what_it_wrote(tmp_path, quick):
    out = tmp_path / "out"
    done = A.build("ibm", TWIN, out, sliced=True)
    files = [p for p in out.rglob("*") if p.is_file()]
    assert (done["files"], done["bytes"]) == (len(files), sum(p.stat().st_size for p in files))


@pytest.mark.parametrize("name", ["LICENSE", "commitments.jsonl", "tomography-bitorder-2026-09-25.json"],
                         ids=["the licence", "an Atlas day's file", "the vector"])
def test_a_link_where_the_atlas_plan_takes_a_file_is_refused_as_the_ibm_plans_walk_refuses_one(tmp_path, monkeypatch, name):
    """The Atlas plan reads its files one by one, not by the IBM plan's walk; a link is refused there too."""
    pin_p2(monkeypatch, None)
    _, moth = synthetic_moth(tmp_path)
    real = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda self: self.name == name or real(self))
    code, stdout, err = run(tmp_path, ["atlas", "--moth", str(moth), "--out", str(tmp_path / "out"), "--slice"])
    assert (code, stdout) == (2, b"") and b"a link in the records" in err and name.encode() in err, err
    assert not (tmp_path / "out").exists()


def test_a_link_as_the_ibm_source_circuit_is_refused(tmp_path, monkeypatch):
    real = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda self: self.name == A.SOURCE_CIRCUIT[-1] or real(self))
    with pytest.raises(A.AdapterError, match="a link in the records"):
        A.plan("ibm", TWIN, ROOT / "records", True)


def test_what_the_build_made_is_told_by_its_kind_its_identity_and_that_it_is_no_link(tmp_path, monkeypatch):
    f = tmp_path / "f"
    f.write_bytes(b"x")
    me = A._identity(f)
    assert A._unchanged(f, me, stat.S_ISREG)
    assert not A._unchanged(f, me, stat.S_ISDIR)                                # not of its kind
    assert not A._unchanged(f, (me[0], me[1] + 1), stat.S_ISREG)                # not the same file
    st = os.lstat(f)
    for mode, attributes in ((stat.S_IFLNK | 0o777, 0), (st.st_mode, stat.FILE_ATTRIBUTE_REPARSE_POINT)):
        seen = types.SimpleNamespace(st_mode=mode, st_dev=st.st_dev, st_ino=st.st_ino, st_file_attributes=attributes)
        monkeypatch.setattr(os, "lstat", lambda p, seen=seen: seen)
        assert not A._unchanged(f, me, stat.S_ISREG)            # a symbolic link, or a reparse point, with the same identity
        monkeypatch.undo()


def test_the_adapter_holds_no_recursive_delete():
    """Nothing in the adapter removes more than the one path it names: no rmtree, no removedirs (which climbs to every
    empty parent), and no shutil at all."""
    source = Path(A.__file__).read_text(encoding="utf-8")
    for name in ("rmtree", "removedirs", "shutil", "os.remove"):
        assert name not in source, name


# -- Atlas through the adapter: the orphan line and the vector that is a law job are refused (the verifier's D1 and D2) ------------------------
def atlas_refusal(tmp_path, edit):
    crate, moth = synthetic_moth(tmp_path)
    edit(moth)
    code, out, err = run(tmp_path, ["atlas", "--moth", str(moth), "--out", str(tmp_path / "out"), "--slice"])
    return code, out.decode("ascii"), err, tmp_path / "out"


def test_an_atlas_line_for_a_job_the_crate_carries_no_files_of_is_refused_by_the_adapter(tmp_path, monkeypatch):
    pin_p2(monkeypatch, None)

    def edit(moth):
        lines = moth.joinpath("docs", "records", *ATLAS_JOBS[0][0].split("/"), "p3", "commitments.jsonl")
        first = json.loads(lines.read_bytes().splitlines()[0])
        first.update(job_id="cccccccc-1111-4222-8333-444444444444", decode="x", shots=5, code_commit="not a commit")
        lines.write_bytes(lines.read_bytes() + json.dumps(first, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    code, line, err, out = atlas_refusal(tmp_path, edit)
    assert (code, err) == (1, b"") and line.startswith("REFUSED metadata-generated at 2026-09-25/p3/commitments.jsonl: G11: ")
    assert not out.exists()


def test_an_atlas_vector_of_a_law_jobs_id_is_refused_by_the_adapter_and_not_built_one_job_short(tmp_path, monkeypatch):
    pin_p2(monkeypatch, None)

    def edit(moth):
        vector = moth.joinpath(*A.VECTOR[0])
        doc = json.loads(vector.read_bytes())
        doc["job"] = ATLAS_JOBS[0][1]
        vector.write_bytes(json.dumps(doc, sort_keys=True).encode())
    code, line, err, out = atlas_refusal(tmp_path, edit)
    assert (code, err) == (1, b"") and ": G11: " in line and "written twice" in line, line
    assert not out.exists()


def test_the_atlas_build_asks_p2_for_its_files_after_the_copy_and_gives_it_the_entities_it_made(tmp_path, monkeypatch):
    crate, moth = synthetic_moth(tmp_path)
    seen = {}

    def question_files(crate_dir):
        seen["copied"] = (crate_dir / "vectors" / "tomography-bitorder-2026-09-25.json").is_file()
        seen["no_metadata_yet"] = not (crate_dir / canonical.DESCRIPTOR).exists()
        return {"law.json": b"{}\n"}

    def contribute(crate_dir, entities):
        seen["jobs"] = sorted(i for i in entities if i.startswith("#job-"))
        return {"qro:law": {"@id": "question/law.json"}}, []
    pin_p2(monkeypatch, standin(question_files=question_files, contribute=contribute))
    done = A.build("atlas", moth, tmp_path / "out", sliced=True)
    out = tmp_path / "out"
    assert seen["copied"] and seen["no_metadata_yet"] and len(seen["jobs"]) == 3
    assert (out / "question" / "law.json").read_bytes() == b"{}\n"
    assert done["files"] == sum(q.is_file() for q in crate.rglob("*")) + 2               # its files, law.json, the descriptor
    md = json.loads((out / canonical.DESCRIPTOR).read_bytes())
    ids = {e["@id"]: e for e in md["@graph"]}
    assert ids["#question"]["qro:law"] == {"@id": "question/law.json"} and "#question-files" in ids


# -- a checkout git cannot see the state of (the verifier's note) ---------------------------------------------------------------------------------
def test_a_checkout_with_a_file_marked_assume_unchanged_or_skip_worktree_is_refused_though_status_is_clean(toy, monkeypatch):
    monkeypatch.setattr(A, "MOTH_COMMIT", git(toy, "rev-parse", "HEAD")[:7])
    A.check_moth(toy)
    for mark, unmark in (("--assume-unchanged", "--no-assume-unchanged"), ("--skip-worktree", "--no-skip-worktree")):
        git(toy, "update-index", mark, "a.txt")
        (toy / "a.txt").write_bytes(b"changed")
        assert git(toy, "status", "--porcelain") == ""                          # the premise: status cannot see it
        with pytest.raises(A.AdapterError, match="assume-unchanged or skip-worktree \\(a.txt\\)"):
            A.check_moth(toy)
        git(toy, "update-index", unmark, "a.txt")
        git(toy, "checkout", "-q", "--", "a.txt")
        A.check_moth(toy)


def test_check_moth_sees_an_untracked_file_though_the_checkouts_own_setting_has_status_hide_untracked_files(toy, monkeypatch):
    """What this holds is the one setting that changes what `git status` shows of an untracked file. A file the checkout's
    own settings ignore is not seen by `check_moth` at all: the build asks of each file it takes (below)."""
    monkeypatch.setattr(A, "MOTH_COMMIT", git(toy, "rev-parse", "HEAD")[:7])
    git(toy, "config", "status.showUntrackedFiles", "no")
    (toy / "new.txt").write_bytes(b"untracked")
    assert git(toy, "status", "--porcelain") == ""                              # the premise: this checkout hides it
    with pytest.raises(A.AdapterError, match="changes that are not committed"):
        A.check_moth(toy)


def test_the_checkout_is_only_read_and_not_even_its_index_is_refreshed(toy, monkeypatch):
    """A file whose times changed and whose bytes did not: `git status` refreshes the index as it looks, unless it is told to
    take no optional lock, as the adapter tells it."""
    monkeypatch.setattr(A, "MOTH_COMMIT", git(toy, "rev-parse", "HEAD")[:7])
    index = toy / ".git" / "index"
    os.utime(toy / "a.txt", ns=(10**18, 10**18))
    before = index.read_bytes()
    A.check_moth(toy)
    assert index.read_bytes() == before
    git(toy, "status", "--porcelain")                                           # the premise: a status that may lock does
    assert index.read_bytes() != before


# -- git's output is read as bytes and decoded as UTF-8, so that no name in the checkout and no error of git's decides the exit or adds a
#    line (P1.2's sixth verifier, D1). `core.quotePath false` is set in the toy's own config, so that git writes a name raw, as the UTF-8
#    it is: U+0141 and U+0150 hold a byte (0x81, 0x90) that this host's code page, cp1252, cannot decode; the other two decode there -------
PINNED = Path(__file__).with_name("p1_pinned.py")
NAMES = [pytest.param(chr(0x141) + "x.txt", id="U+0141"), pytest.param(chr(0x150) + "x.txt", id="U+0150"),
         pytest.param(chr(0xE9) + "x.txt", id="U+00E9"), pytest.param(chr(0x4E2D) + chr(0x6587) + ".txt", id="U+4E2D U+6587")]


def pin(monkeypatch, repo):
    """The adapter reads moth-quantum at 3a73823; the toy is at a commit of its own, which it is made to read."""
    monkeypatch.setattr(A, "MOTH_COMMIT", git(repo, "rev-parse", "HEAD")[:7])


def pinned(repo, argv):
    """The adapter's command line as a process, on a toy at its commit (tests/p1/p1_pinned.py): (the completed process)."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, str(PINNED), git(repo, "rev-parse", "HEAD")[:7], "--", *argv],
                          capture_output=True, env=env, cwd=ROOT)


def one_line(err, *words):
    """The misuse line is one line, printable ASCII, with no traceback before it or after, and holds each of `words`."""
    return err.count(b"\n") == 1 and err.isascii() and b"Traceback" not in err and all(w in err for w in words)


@contextlib.contextmanager
def thread_failures():
    """The exceptions of the threads that end inside the block, which is run in the test itself (pytest installs its own hook
    afresh for the call, and puts the one before it back after). When a code page cannot decode git's bytes, subprocess's
    reader thread ends with one: in a process its traceback reaches stderr, in process pytest only warns of it."""
    seen, was = [], threading.excepthook
    threading.excepthook = seen.append
    try:
        yield seen
    finally:
        threading.excepthook = was


@pytest.mark.parametrize("quote", ["false", "true"])
@pytest.mark.parametrize("name", NAMES)
def test_an_untracked_file_so_named_is_exit_2_in_one_line_with_no_traceback_whatever_core_quotepath_says(tmp_path, toy,
                                                                                                    monkeypatch, name, quote):
    git(toy, "config", "core.quotePath", quote)
    pin(monkeypatch, toy)
    (toy / name).write_bytes(b"untracked")
    raw = name.encode("utf-8") in git_run(toy, "status", "--porcelain", "--untracked-files=all").stdout
    assert raw == (quote == "false")                      # the premise: git writes the name raw under `false`, and quoted under `true`
    with thread_failures() as threads:
        code, stdout, err = run(tmp_path, ["ibm", "--moth", str(toy), "--out", str(tmp_path / "out")])
    assert (code, stdout) == (2, b"") and one_line(err, b"has changes that are not committed"), err
    assert threads == [] and not (tmp_path / "out").exists()


@pytest.mark.parametrize("name", NAMES)
def test_an_untracked_file_so_named_is_exit_2_in_one_line_with_no_traceback_as_a_process(tmp_path, toy, name):
    git(toy, "config", "core.quotePath", "false")
    (toy / name).write_bytes(b"untracked")
    p = pinned(toy, ["ibm", "--moth", str(toy), "--out", str(tmp_path / "out")])
    assert (p.returncode, p.stdout) == (2, b"") and one_line(p.stderr, b"has changes that are not committed"), p.stderr
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("quote", ["false", "true"])
@pytest.mark.parametrize("name", NAMES)
def test_a_file_so_named_marked_assume_unchanged_is_exit_2_with_its_name_in_the_line(tmp_path, toy, monkeypatch, name, quote):
    """`git ls-files -v` is asked with -z, so that its name is raw whatever `core.quotePath` says, and shown as it is."""
    (toy / name).write_bytes(b"tracked")
    git(toy, "add", "-A")
    git(toy, "commit", "-q", "-m", "named")
    git(toy, "config", "core.quotePath", quote)
    pin(monkeypatch, toy)
    git(toy, "update-index", "--assume-unchanged", name)
    (toy / name).write_bytes(b"changed")
    assert git(toy, "status", "--porcelain") == ""                              # the premise: status cannot see it
    with thread_failures() as threads:
        code, stdout, err = run(tmp_path, ["ibm", "--moth", str(toy), "--out", str(tmp_path / "out")])
    assert (code, stdout) == (2, b"")
    assert one_line(err, b"assume-unchanged or skip-worktree (" + escape(name).encode("ascii") + b")"), err
    assert threads == [] and not (tmp_path / "out").exists()


@pytest.mark.parametrize("name", NAMES)
def test_a_file_so_named_marked_assume_unchanged_is_exit_2_with_its_name_in_the_line_as_a_process(tmp_path, toy, name):
    (toy / name).write_bytes(b"tracked")
    git(toy, "add", "-A")
    git(toy, "commit", "-q", "-m", "named")
    git(toy, "config", "core.quotePath", "false")
    git(toy, "update-index", "--assume-unchanged", name)
    (toy / name).write_bytes(b"changed")
    p = pinned(toy, ["ibm", "--moth", str(toy), "--out", str(tmp_path / "out")])
    assert (p.returncode, p.stdout) == (2, b"")
    assert one_line(p.stderr, b"assume-unchanged or skip-worktree (" + escape(name).encode("ascii") + b")"), p.stderr


def gone_gitdir(tmp_path, name):
    """A directory whose `.git` file names a gitdir that is not there, its name holding `name`: git's own error names it."""
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / ".git").write_bytes(f"gitdir: {(tmp_path / ('gone' + name)).as_posix()}\n".encode("utf-8"))
    said = git_run(bad, "rev-parse", "--show-cdup", check=False)
    assert said.returncode != 0 and name.encode("utf-8") in said.stderr         # the premise: git fails, naming it as UTF-8
    return bad


@pytest.mark.parametrize("name", NAMES)
def test_git_failing_with_a_message_that_names_such_a_path_is_exit_2_in_one_line(tmp_path, name):
    bad = gone_gitdir(tmp_path, name)
    with thread_failures() as threads:
        code, stdout, err = run(tmp_path, ["ibm", "--moth", str(bad), "--out", str(tmp_path / "out")])
    assert (code, stdout) == (2, b"")
    assert one_line(err, b"must be a git checkout of moth-quantum (git said: ", escape("gone" + name).encode("ascii")), err
    assert threads == [] and not (tmp_path / "out").exists()


@pytest.mark.parametrize("name", NAMES)
def test_git_failing_with_a_message_that_names_such_a_path_is_exit_2_in_one_line_as_a_process(tmp_path, name):
    bad = gone_gitdir(tmp_path, name)
    p = process(["ibm", "--moth", str(bad), "--out", str(tmp_path / "out")])
    assert (p.returncode, p.stdout) == (2, b"")
    assert one_line(p.stderr, b"must be a git checkout of moth-quantum (git said: ", escape("gone" + name).encode("ascii")), p.stderr
    assert not (tmp_path / "out").exists()


def test_a_clean_checkout_whose_names_hold_a_separator_that_splitlines_splits_on_is_clean(toy, monkeypatch):
    """`git ls-files -v` is read by its NUL, not by lines: a name with U+0085, U+2028 or U+2029 in it, which git writes raw
    under `core.quotePath false` and which str.splitlines would cut in two, is one name."""
    git(toy, "config", "core.quotePath", "false")
    for separator in (0x85, 0x2028, 0x2029):
        (toy / f"a{chr(separator)}b.txt").write_bytes(b"x")
    git(toy, "add", "-A")
    git(toy, "commit", "-q", "-m", "separators")
    pin(monkeypatch, toy)
    assert "\u0085".encode("utf-8") in git_run(toy, "ls-files", "-v").stdout     # the premise: git writes it raw
    assert A.check_moth(toy) == git(toy, "rev-parse", "HEAD")


def test_a_name_git_wrote_that_is_not_utf_8_is_shown_replaced_and_decides_nothing_else(toy, monkeypatch):
    """A name is only shown: a byte that is not UTF-8 (a Linux host's Latin-1 file name) is replaced, and the refusal is the
    same one, exit 2 in one line, as it is for any other name."""
    pin(monkeypatch, toy)
    real = A._git_bytes
    monkeypatch.setattr(A, "_git_bytes", lambda moth, *args: b"H a.txt\0h \xff\xfeb.txt\0" if args[:2] == ("ls-files", "-v")
                        else real(moth, *args))
    with pytest.raises(A.AdapterError) as refused:
        A.check_moth(toy)
    assert f"skip-worktree ({chr(0xFFFD) * 2}b.txt)" in str(refused.value)
    assert A._shown(b"\xc5\x81") == chr(0x141) and A._shown(b"a\xffb") == "a" + chr(0xFFFD) + "b"


# -- every file the build takes from the checkout is 3a73823's own (P1.2's sixth verifier, D2). The checkout is the twin, committed:
#    a clean toy that the adapter builds as a checkout, and the crate is the slice's, byte for byte ------------------------------------------
def commit_checkout(moth, *init):
    """The tree `moth` as a checkout of its own: a git repository, committed. Its config is its own, so that no setting of the
    host's decides what git says of a line ending, a link or a mode."""
    git(moth, "init", "-q", *init)
    for key, value in (("core.autocrlf", "false"), ("core.symlinks", "false"), ("core.fileMode", "false"),
                       ("core.quotePath", "true")):
        git(moth, "config", key, value)
    git(moth, "add", "-A")
    git(moth, "commit", "-q", "-m", "the checkout")


def commit_twin(tmp_path, *init):
    """The twin as a checkout, laid out as moth-quantum's, with the records of the read for its jobs beside it: (moth, records)."""
    moth, records = moth_of(twin_copy(tmp_path, alone=True), tmp_path)       # P1 alone: no question/ file of P2's in the checkout
    commit_checkout(moth, *init)
    return moth, records


@pytest.fixture
def checkout(tmp_path, monkeypatch, quick):
    """A checkout of the twin, committed. These tests mean the adapter's rule on a checkout, P1 alone: P2's module is pinned
    absent for every build and generator here, so the counts are P1's (the lead's ruling, 2026-11-08)."""
    moth, records = commit_twin(tmp_path)          # the twin is asked for before the pin: the helper refuses to build it pinned
    pin_p2(monkeypatch, None)
    pin(monkeypatch, moth)
    return moth, records


def build_args(moth, records, out, *more):
    return ["ibm", "--moth", str(moth), "--out", str(out), "--records", str(records), *more]


def extra_snapshot(records):
    """A snapshot of the kind the control `calibration-restamped` adds: a real kingston snapshot with its stamp moved, named for
    the new stamp, in Quantum-Film's place for it in the checkout: (its path in the checkout, its bytes)."""
    data, stamp = plants.restamped_snapshot((records / plants.SNAP_0902).read_bytes())
    return "/".join((*A.RECORDS, plants.IBM, "properties-" + stamp.replace("-", "").replace(":", "") + ".json")), data


IGNORES = ["info/exclude", "a .gitignore that ignores itself", "core.excludesFile"]


def ignored_by(moth, tmp_path, rel, source):
    """The checkout's own settings ignore the file `rel`, by `source`."""
    if source == "info/exclude":
        (moth / ".git" / "info" / "exclude").write_bytes(f"{rel}\n".encode("ascii"))
    elif source == "a .gitignore that ignores itself":
        (moth / ".gitignore").write_bytes(f".gitignore\n{rel}\n".encode("ascii"))
    else:
        (tmp_path / "excludes").write_bytes(f"{rel}\n".encode("ascii"))
        git(moth, "config", "core.excludesFile", (tmp_path / "excludes").as_posix())


def test_a_clean_checkout_is_built_and_its_crate_is_the_slices_byte_for_byte(tmp_path, checkout):
    moth, records = checkout
    assert A.check_moth(moth) == git(moth, "rev-parse", "HEAD")
    when = datetime(2026, 11, 8, tzinfo=timezone.utc)         # the header's time: a second boundary between the two builds is no difference
    built = A.build("ibm", moth, tmp_path / "built", records=records, now=when)
    sliced = A.build("ibm", moth, tmp_path / "slice", records=records, sliced=True, now=when)       # a slice is not asked
    assert built == sliced and built["files"] == len(A.plan("ibm", moth, records, False)) + 1
    for rel, src in A.plan("ibm", moth, records, False):
        assert (tmp_path / "built").joinpath(*rel.split("/")).read_bytes() == src.read_bytes(), rel


@pytest.mark.parametrize("name", NAMES)
def test_a_name_is_matched_to_the_tree_by_the_bytes_git_wrote_never_decoded(toy, name):
    """The tree lists a path as the UTF-8 git wrote it; the plan names one as the host spells it. Held, the one is the other."""
    (toy / name).write_bytes(b"tracked bytes")
    git(toy, "add", "-A")
    git(toy, "commit", "-q", "-m", "named")
    tree = A.head_tree(toy, git(toy, "rev-parse", "HEAD"))
    assert name.encode("utf-8") in tree
    A.hold_to_head(toy, tree, name, b"tracked bytes")
    with pytest.raises(A.AdapterError, match="is not moth-quantum's bytes"):
        A.hold_to_head(toy, tree, name, b"other bytes")
    with pytest.raises(A.AdapterError, match="is not a file of moth-quantum"):
        A.hold_to_head(toy, tree, "other-" + name, b"tracked bytes")


def test_the_atlas_plan_holds_its_files_to_the_tree_too_a_clean_checkout_is_built_and_an_ignored_file_in_a_day_is_refused(
        tmp_path, monkeypatch):
    """The Atlas plan lists a day's directory itself; the rule is the build's, whatever the plan."""
    pin_p2(monkeypatch, None)
    crate, moth = synthetic_moth(tmp_path)
    commit_checkout(moth)
    pin(monkeypatch, moth)
    built = A.build("atlas", moth, tmp_path / "built")
    assert built == A.build("atlas", moth, tmp_path / "slice", sliced=True)
    extra = "/".join((*A.RECORDS, ATLAS_JOBS[0][0], "p3", "atlas-ffffffff-status.json"))
    (moth / extra).write_bytes(b"{}")
    ignored_by(moth, tmp_path, extra, "info/exclude")
    assert git(moth, "status", "--porcelain", "--untracked-files=all") == ""
    out = tmp_path / "out"
    code, stdout, err = run(tmp_path, ["atlas", "--moth", str(moth), "--out", str(out)])
    assert (code, stdout) == (2, b"") and one_line(err, escape(extra).encode("ascii"), b"is not a file of moth-quantum at"), err
    assert not out.exists()


@pytest.mark.parametrize("source", IGNORES)
def test_an_untracked_file_the_checkouts_own_settings_ignore_is_refused_where_the_build_would_take_it(tmp_path, checkout, source):
    """`git status` does not report it (the sixth verifier built, exit 0, a crate with it from a real checkout so ignored, and the
    checker accepted that crate): the build holds each file it takes to HEAD's tree."""
    moth, records = checkout
    honest = len(A.plan("ibm", moth, records, True)) + 1
    rel, data = extra_snapshot(records)
    (moth / rel).write_bytes(data)
    ignored_by(moth, tmp_path, rel, source)
    assert git(moth, "status", "--porcelain", "--untracked-files=all") == ""       # the premise: git does not see it ...
    assert rel in git(moth, "ls-files", "--others", "--ignored", "--exclude-standard").split("\n")   # ... for its settings ignore it
    assert A.check_moth(moth)                                                      # check_moth cannot see it
    assert A.build("ibm", moth, tmp_path / "slice", records=records, sliced=True)["files"] == honest + 1   # the control: it builds
    out = tmp_path / "out"
    code, stdout, err = run(tmp_path, build_args(moth, records, out))
    assert (code, stdout) == (2, b"")
    assert one_line(err, escape(rel).encode("ascii"), b"is not a file of moth-quantum at " + A.MOTH_COMMIT.encode("ascii"),
                    b"does not hold it"), err
    assert not out.exists()


def test_a_file_whose_bytes_are_not_its_blobs_while_status_is_clean_is_refused(tmp_path, checkout):
    """A line-ending conversion the checkout's own `.git/info/attributes` asks for: the checkout writes LICENSE with CRLF line
    endings, its index records that file, and `git status` has nothing to say. The bytes are not 3a73823's."""
    moth, records = checkout
    (moth / ".git" / "info" / "attributes").write_bytes(b"LICENSE text eol=crlf\n")
    (moth / "LICENSE").unlink()
    git(moth, "checkout", "--", "LICENSE")
    blob, on_disk = git_run(moth, "cat-file", "blob", "HEAD:LICENSE").stdout, (moth / "LICENSE").read_bytes()
    assert b"\r\n" in on_disk and on_disk.replace(b"\r\n", b"\n") == blob          # the premise: CRLF, from a blob with LF
    assert git(moth, "status", "--porcelain", "--untracked-files=all") == "" and A.check_moth(moth)   # git has nothing to say
    out = tmp_path / "out"
    code, stdout, err = run(tmp_path, build_args(moth, records, out))
    assert (code, stdout) == (2, b"")
    assert one_line(err, b"LICENSE is not moth-quantum's bytes at " + A.MOTH_COMMIT.encode("ascii")), err
    assert not out.exists()


def test_a_path_the_tree_holds_as_a_link_whose_checked_out_bytes_are_its_blobs_is_refused(tmp_path, checkout, monkeypatch):
    """Mode 120000, made with `git update-index --cacheinfo`; the file checked out in its place has the bytes of its blob (what a
    host that makes no links writes), and `git status` agrees. It is not a regular file of the tree."""
    moth, records = checkout
    git(moth, "update-index", "--cacheinfo", f"120000,{git(moth, 'hash-object', '-w', 'LICENSE')},LICENSE")
    git(moth, "commit", "-q", "-m", "LICENSE as a link")
    pin(monkeypatch, moth)
    assert git(moth, "ls-tree", "HEAD", "LICENSE").startswith("120000 blob ")      # the premise: a link in the tree ...
    assert git(moth, "status", "--porcelain", "--untracked-files=all") == "" and A.check_moth(moth)      # ... and a clean checkout
    out = tmp_path / "out"
    code, stdout, err = run(tmp_path, build_args(moth, records, out))
    assert (code, stdout) == (2, b"")
    assert one_line(err, b"LICENSE is not a file of moth-quantum at " + A.MOTH_COMMIT.encode("ascii"), b"mode 120000"), err
    assert not out.exists()


def test_a_replaced_commit_does_not_make_the_checkout_clean_at_the_commit_it_names(tmp_path, checkout):
    """`git replace` is a ref of the checkout's own that makes git read one commit as another: HEAD is still the commit the adapter
    reads, `git status` finds the checkout clean, and the tree git lists, and every blob in it, are the replacement's. The adapter
    asks git without replace objects, so what it sees is the commit's own tree, and the checkout differs from it."""
    moth, records = checkout
    honest, licence = git(moth, "rev-parse", "HEAD"), (moth / "LICENSE").read_bytes()
    (moth / "LICENSE").write_bytes(licence + b"Not Quantum-Film's licence.\n")
    git(moth, "commit", "-q", "-a", "-m", "another LICENSE")
    other = git(moth, "rev-parse", "HEAD")
    git(moth, "reset", "-q", "--hard", honest)
    git(moth, "replace", "--force", honest, other)
    git(moth, "reset", "-q", "--hard", "HEAD")                                     # the index and the files are the replacement's
    assert git(moth, "rev-parse", "HEAD") == honest and (moth / "LICENSE").read_bytes() != licence      # the premise ...
    assert git(moth, "status", "--porcelain", "--untracked-files=all") == ""       # ... and git, as it is asked, sees nothing
    with pytest.raises(A.AdapterError, match="changes that are not committed"):
        A.check_moth(moth)
    out = tmp_path / "out"
    code, stdout, err = run(tmp_path, build_args(moth, records, out))
    assert (code, stdout) == (2, b"") and one_line(err, b"has changes that are not committed"), err
    assert not out.exists()


def test_a_file_the_tree_holds_as_an_executable_is_a_regular_file_of_it(tmp_path, checkout, monkeypatch):
    moth, records = checkout
    git(moth, "update-index", "--chmod=+x", "LICENSE")
    git(moth, "commit", "-q", "-m", "LICENSE is executable")
    pin(monkeypatch, moth)
    assert git(moth, "ls-tree", "HEAD", "LICENSE").startswith("100755 blob ")
    assert A.build("ibm", moth, tmp_path / "built", records=records) == \
        A.build("ibm", moth, tmp_path / "slice", records=records, sliced=True)


def test_the_bytes_the_build_holds_to_the_blob_are_the_bytes_it_copies_from_the_one_read(tmp_path, checkout, monkeypatch):
    """A file that changes after the build reads it is not the build's concern; one that is read twice would be: the second read
    here is not the blob's, and what the crate holds must be the blob's all the same."""
    moth, records = checkout
    licence, reads, real = moth / "LICENSE", [], Path.read_bytes

    def read_bytes(self):
        data = real(self)
        if self == licence:
            reads.append(data)
            if len(reads) > 1:
                return data + b" changed after the first read"
        return data
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    A.build("ibm", moth, tmp_path / "built", records=records)
    assert len(reads) == 1 and (tmp_path / "built" / G.LICENSE_QF).read_bytes() == reads[0] == real(licence)


@pytest.mark.parametrize("fmt, size", [("sha1", 40), ("sha256", 64)])
def test_a_blobs_id_is_gits_own_in_each_object_format_and_no_other_length_is_one(tmp_path, fmt, size):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", f"--object-format={fmt}")
    for data in (b"", b"a", b"a\r\nb\n", bytes(range(256)) * 3, (chr(0x141) + "\n").encode("utf-8")):
        (repo / "f").write_bytes(data)
        assert A._blob_id(data, size) == git(repo, "hash-object", "--no-filters", "f"), data
    assert A._blob_id(b"a", size + 1) is None and A._blob_id(b"a", 0) is None


def test_a_checkout_in_gits_sha256_object_format_is_held_by_its_64_character_ids(tmp_path, monkeypatch, quick):
    """Needs git's SHA-256 object format (git 2.29 or later)."""
    moth, records = commit_twin(tmp_path, "--object-format=sha256")
    pin(monkeypatch, moth)
    assert len(git(moth, "rev-parse", "HEAD")) == 64
    assert A.build("ibm", moth, tmp_path / "built", records=records) == \
        A.build("ibm", moth, tmp_path / "slice", records=records, sliced=True)
    (moth / ".git" / "info" / "attributes").write_bytes(b"LICENSE text eol=crlf\n")
    (moth / "LICENSE").unlink()
    git(moth, "checkout", "--", "LICENSE")
    assert git(moth, "status", "--porcelain", "--untracked-files=all") == ""
    code, stdout, err = run(tmp_path, build_args(moth, records, tmp_path / "out"))
    assert (code, stdout) == (2, b"") and one_line(err, b"LICENSE is not moth-quantum's bytes at"), err


def test_a_file_the_checkouts_own_settings_ignore_is_refused_as_a_process(tmp_path, checkout):
    moth, records = checkout
    rel, data = extra_snapshot(records)
    (moth / rel).write_bytes(data)
    ignored_by(moth, tmp_path, rel, "info/exclude")
    out = tmp_path / "out"
    p = pinned(moth, build_args(moth, records, out))
    assert (p.returncode, p.stdout) == (2, b"")
    assert one_line(p.stderr, escape(rel).encode("ascii"), b"is not a file of moth-quantum at"), p.stderr
    assert not out.exists()


def test_a_clean_checkout_is_built_and_checked_as_a_process(tmp_path, checkout):
    moth, records = checkout
    out = tmp_path / "out"
    built = pinned(moth, build_args(moth, records, out))
    assert (built.returncode, built.stderr) == (0, b""), built.stdout[-300:]
    m = LINE.fullmatch(built.stdout.decode("ascii").rstrip("\n"))
    assert m and built.stdout.count(b"\n") == 1
    checked = process(["check", str(out)], module="qro")
    assert (checked.returncode, checked.stdout, checked.stderr) == (0, f"ACCEPTED {m.group(4)}\n".encode(), b"")


# -- a slice is taken as it is, and an option given twice is misuse (P1.2's sixth verifier, N1 and N2) ---------------------------------------------
def test_a_slice_is_taken_as_it_is_one_without_a_file_a_commitment_binds_builds_a_crate_the_checker_refuses(tmp_path, quick):
    """The adapter does not check what it builds; the checker does. The twin without coherence-xx.qasm, the circuit the morning
    coherence job's commitment binds, builds (exit 0), and the checker refuses that crate: `commitment`."""
    moth = moth_copy(tmp_path)
    next(moth.rglob("coherence-xx.qasm")).unlink()
    out = tmp_path / "out"
    code, stdout, err = run(tmp_path, ["ibm", "--moth", str(moth), "--out", str(out), "--slice"])
    assert (code, err) == (0, b"") and LINE.fullmatch(stdout.decode("ascii").rstrip("\n"))
    checker.load()
    with pytest.raises(Refused) as refused:
        checker.check(out)
    assert refused.value.name == "commitment" and "qro:record" in refused.value.where, refused.value


def test_slice_given_twice_is_misuse_as_every_other_option_given_twice_is(tmp_path):
    out = tmp_path / "out"
    code, stdout, err = run(tmp_path, twin_args(out, "--slice"))
    assert (code, stdout) == (2, b"") and err.startswith(b"--slice: not an option of this command, or given twice")
    assert USAGE.encode("ascii") in err and err.count(b"\n") == 1 and not out.exists()
    p = process(twin_args(tmp_path / "again", "--slice"))
    assert (p.returncode, p.stdout) == (2, b"") and p.stderr == err and not (tmp_path / "again").exists()
