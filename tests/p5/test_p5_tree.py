"""`kit-dirty` (P5's design, item 7; qro/p5_tree.py): the kit starts only from the bytes of a tagged commit. Each case is a
throwaway git repository made in the test's own directory; each refusal has its twin that is accepted. Dirty is decided from the
bytes against HEAD's tree (D1, D2), never from `git status`, which an ignore rule, an exclude file, assume-unchanged,
skip-worktree, a `core.fsmonitor` hook, `git replace` and a text filter can each make say what is not so.

The `core.fsmonitor` case starts a hook through sh: it runs where the runner runs these tests (sbx-mid.sh), not at low
integrity (CLAUDE.md item 9)."""
import os
import subprocess
import sys

import pytest
from p5_support import no_link_left_behind, no_network  # noqa: F401

from qro import p5_tree
from qro.refusal import Refused

pytestmark = pytest.mark.usefixtures("no_network", "no_link_left_behind")
ENV = {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example.invalid"}


def git(repo, *args, check=True, env=None):
    r = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false", *args], cwd=repo,
                       capture_output=True, env=env or ENV, stdin=subprocess.DEVNULL)
    if check and r.returncode:
        raise AssertionError(f"git {args}: {r.stderr.decode(errors='replace')}")
    return r.stdout.decode("utf-8", "replace").strip()


def repo(tmp_path, tag="qro-kit-v1.2.3", name="kit"):
    """A clean tagged repository: a.txt, sub/b.txt, an executable-free tree, one commit and a tag."""
    r = tmp_path / name
    (r / "sub").mkdir(parents=True)
    git(r, "init", "-q", "--initial-branch=main")
    (r / "a.txt").write_bytes(b"alpha\n")
    (r / "sub" / "b.txt").write_bytes(b"beta\n")
    (r / ".gitattributes").write_bytes(b"* -text\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "one")
    if tag:
        git(r, "tag", tag)
    return r


def refused(root, **kw):
    with pytest.raises(Refused) as caught:
        p5_tree.tree_state(root, **kw)
    assert caught.value.name == "kit-dirty"
    return caught.value


def make_dir_link(link, target):
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)
    else:
        os.symlink(target, link)


def remove_dir_link(link):
    if os.name == "nt":
        os.rmdir(link)
    else:
        os.unlink(link)


# -- the clean tagged tree, and what must be true of it ---------------------------------------------------------
def test_a_clean_tagged_tree_is_accepted_and_names_its_commit_and_tag(tmp_path):
    r = repo(tmp_path)
    state = p5_tree.tree_state(r)
    assert state == {"commit": git(r, "rev-parse", "HEAD"), "tag": "qro-kit-v1.2.3", "tags": ["qro-kit-v1.2.3"]}
    assert len(state["commit"]) == 40


def test_the_highest_matching_tag_is_recorded(tmp_path):
    r = repo(tmp_path)
    for t in ("qro-kit-v1.10.0", "qro-kit-v1.9.9", "not-a-kit-tag"):
        git(r, "tag", t)
    state = p5_tree.tree_state(r)
    assert state["tag"] == "qro-kit-v1.10.0" and state["tags"] == ["qro-kit-v1.2.3", "qro-kit-v1.9.9", "qro-kit-v1.10.0"]


def test_pycache_and_the_repositorys_own_dot_git_are_not_walked(tmp_path):
    r = repo(tmp_path)
    (r / "sub" / "__pycache__").mkdir()
    (r / "sub" / "__pycache__" / "b.cpython-312.pyc").write_bytes(b"compiled")
    (r / "emptydir").mkdir()
    assert p5_tree.tree_state(r)["tag"] == "qro-kit-v1.2.3"


def test_an_executable_in_heads_tree_is_a_file(tmp_path):
    r = repo(tmp_path, tag=None)
    git(r, "update-index", "--chmod=+x", "a.txt")
    git(r, "commit", "-q", "-m", "mode")
    git(r, "tag", "qro-kit-v1.0.0")
    assert p5_tree.tree_state(r)["tag"] == "qro-kit-v1.0.0"


# -- D1: every tracked path is the blob ----------------------------------------------------------------------
def test_d1_a_modified_tracked_file_is_dirty(tmp_path):
    r = repo(tmp_path)
    (r / "a.txt").write_bytes(b"alpha, changed\n")
    assert refused(r).where == "a.txt"


def test_d1_a_tracked_file_deleted_is_dirty(tmp_path):
    r = repo(tmp_path)
    (r / "sub" / "b.txt").unlink()
    assert refused(r).where == "sub/b.txt"


def test_d1_a_tracked_file_replaced_by_one_of_the_same_size_is_dirty(tmp_path):
    r = repo(tmp_path)
    (r / "a.txt").write_bytes(b"omega\n")
    refused(r)


def test_d1_a_link_in_heads_tree_is_dirty(tmp_path):
    r = repo(tmp_path, tag=None)
    blob = git(r, "hash-object", "-w", "a.txt")
    git(r, "update-index", "--add", "--cacheinfo", f"120000,{blob},thelink")
    git(r, "commit", "-q", "-m", "a link")
    git(r, "tag", "qro-kit-v1.0.0")
    (r / "thelink").write_bytes(b"alpha\n")
    assert refused(r).where == "thelink"


def test_d1_a_clean_filter_that_makes_git_status_clean_over_changed_bytes_is_dirty(tmp_path):
    """A clean filter (here `echo alpha`, run through sh) turns any bytes of the file into the blob's; git compares what the
    filter makes, and (for a file of the same size, which it compares by content) says it is unchanged."""
    r = repo(tmp_path, tag=None)
    (r / ".gitattributes").write_bytes(b"a.txt filter=fix\n")
    git(r, "add", ".gitattributes")
    git(r, "commit", "-q", "-m", "attributes")
    git(r, "tag", "qro-kit-v1.0.0")
    git(r, "config", "filter.fix.clean", "echo alpha")
    (r / "a.txt").write_bytes(b"gamma\n")
    assert git(r, "status", "--porcelain") == ""
    assert refused(r).where == "a.txt"


def test_d1_git_replace_that_makes_another_tree_look_like_heads_is_dirty(tmp_path):
    r = repo(tmp_path, tag=None)
    first = git(r, "rev-parse", "HEAD")
    (r / "a.txt").write_bytes(b"two\n")
    git(r, "commit", "-q", "-am", "two")
    git(r, "tag", "qro-kit-v1.0.0")
    second = git(r, "rev-parse", "HEAD")
    (r / "a.txt").write_bytes(b"alpha\n")                            # the first commit's bytes on disk
    git(r, "replace", second, first)                                 # git, replacing, now sees the first commit as HEAD
    git(r, "read-tree", "HEAD")                                      # and the index as that commit's tree
    assert git(r, "status", "--porcelain") == ""
    assert refused(r).where == "a.txt"


# -- D2: nothing else is on disk ---------------------------------------------------------------------------------
def test_d2_an_untracked_file_is_dirty(tmp_path):
    r = repo(tmp_path)
    (r / "new.txt").write_bytes(b"new\n")
    assert refused(r).where == "new.txt"


def test_d2_an_untracked_file_in_a_subdirectory_is_dirty(tmp_path):
    r = repo(tmp_path)
    (r / "sub" / "deeper").mkdir()
    (r / "sub" / "deeper" / "c.txt").write_bytes(b"c\n")
    assert refused(r).where == "sub/deeper/c.txt"


def test_d2_an_untracked_file_hidden_by_info_exclude_is_dirty(tmp_path):
    r = repo(tmp_path)
    (r / ".git" / "info" / "exclude").write_bytes(b"hidden.txt\n")
    (r / "hidden.txt").write_bytes(b"x\n")
    assert git(r, "status", "--porcelain") == ""
    assert refused(r).where == "hidden.txt"


def test_d2_an_untracked_file_hidden_by_gitignore_is_dirty(tmp_path):
    r = repo(tmp_path, tag=None)
    (r / ".gitignore").write_bytes(b"hidden.txt\n")
    git(r, "add", ".gitignore")
    git(r, "commit", "-q", "-m", "ignore")
    git(r, "tag", "qro-kit-v1.0.0")
    (r / "hidden.txt").write_bytes(b"x\n")
    assert git(r, "status", "--porcelain") == ""
    assert refused(r).where == "hidden.txt"


def test_d2_an_untracked_file_hidden_by_core_excludesfile_is_dirty(tmp_path):
    r = repo(tmp_path)
    excludes = tmp_path / "excludes"
    excludes.write_bytes(b"hidden.txt\n")
    git(r, "config", "core.excludesFile", str(excludes))
    (r / "hidden.txt").write_bytes(b"x\n")
    assert git(r, "status", "--porcelain") == ""
    assert refused(r).where == "hidden.txt"


def test_d2_status_showuntrackedfiles_no_does_not_hide_a_file(tmp_path):
    r = repo(tmp_path)
    git(r, "config", "status.showUntrackedFiles", "no")
    (r / "new.txt").write_bytes(b"new\n")
    assert git(r, "status", "--porcelain") == ""
    refused(r)


def test_d2_a_directory_link_or_junction_is_dirty(tmp_path):
    r = repo(tmp_path)
    target = tmp_path / "elsewhere"
    target.mkdir()
    make_dir_link(r / "linked", target)
    try:
        assert refused(r).where == "linked"
    finally:
        remove_dir_link(r / "linked")


# -- D3: no file is marked ------------------------------------------------------------------------------------------
def test_d3_assume_unchanged_on_an_unchanged_file_is_dirty(tmp_path):
    r = repo(tmp_path)
    git(r, "update-index", "--assume-unchanged", "a.txt")
    assert "assume-unchanged" in refused(r).detail and refused(r).where == "a.txt"


def test_d3_skip_worktree_on_an_unchanged_file_is_dirty(tmp_path):
    r = repo(tmp_path)
    git(r, "update-index", "--skip-worktree", "sub/b.txt")
    assert refused(r).where == "sub/b.txt"


def test_d3_assume_unchanged_hides_a_modified_file_from_status_and_not_from_the_bytes(tmp_path):
    r = repo(tmp_path)
    git(r, "update-index", "--assume-unchanged", "a.txt")
    (r / "a.txt").write_bytes(b"alpha, changed\n")
    assert git(r, "status", "--porcelain") == ""
    refused(r)


def test_d3_a_sparse_checkout_that_drops_a_file_is_dirty(tmp_path):
    r = repo(tmp_path)
    git(r, "sparse-checkout", "init", "--no-cone")
    git(r, "sparse-checkout", "set", "/a.txt", "/.gitattributes")
    assert not (r / "sub" / "b.txt").exists()
    refused(r)


def test_d1_a_core_fsmonitor_hook_that_reports_no_change_does_not_hide_a_change(tmp_path):
    r = repo(tmp_path)
    hook = tmp_path / "hook.sh"
    hook.write_bytes(b"#!/bin/sh\nprintf '\\0'\n")
    git(r, "config", "core.fsmonitor", hook.as_posix())
    (r / "a.txt").write_bytes(b"alpha, changed\n")
    assert refused(r).where == "a.txt"


# -- D4: git is asked as the gate says ---------------------------------------------------------------------------
def test_d4_git_dir_in_the_environment_does_not_move_the_question(tmp_path, monkeypatch):
    r = repo(tmp_path)
    other = repo(tmp_path, tag=None, name="other")
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    monkeypatch.setenv("GIT_INDEX_FILE", str(other / ".git" / "index"))
    assert p5_tree.tree_state(r)["tag"] == "qro-kit-v1.2.3"


def test_d4_every_git_call_carries_the_gates_options(tmp_path, monkeypatch):
    r = repo(tmp_path)
    calls = []
    real = subprocess.run

    def spy(cmd, *a, **kw):
        calls.append((cmd, kw))
        return real(cmd, *a, **kw)
    monkeypatch.setattr(subprocess, "run", spy)
    p5_tree.tree_state(r)
    assert len(calls) >= 5
    for cmd, kw in calls:
        assert cmd[:6] == ["git", "--no-optional-locks", "--no-replace-objects", "-c", "core.fsmonitor=false", cmd[5]]
        assert kw["stdin"] is subprocess.DEVNULL and kw["capture_output"] is True
        assert not [k for k in kw["env"] if k.startswith("GIT_")]
        if sys.platform == "win32":
            assert kw["creationflags"] == subprocess.CREATE_NO_WINDOW


def test_d4_the_root_must_be_the_top_of_its_work_tree(tmp_path):
    r = repo(tmp_path)
    assert "top of a git work tree" in refused(r / "sub").detail


def test_d4_a_directory_that_is_no_repository_is_dirty(tmp_path):
    (tmp_path / "plain").mkdir()
    refused(tmp_path / "plain")
    refused(tmp_path / "nothing-here")


def test_d4_a_repository_with_no_commit_is_dirty(tmp_path):
    r = tmp_path / "empty"
    r.mkdir()
    git(r, "init", "-q", "--initial-branch=main")
    refused(r)


def test_d4_no_git_on_the_path_is_the_tools_failure_not_a_verdict(tmp_path, monkeypatch):
    r = repo(tmp_path)

    def gone(*a, **kw):
        raise FileNotFoundError("git")
    monkeypatch.setattr(subprocess, "run", gone)
    with pytest.raises(FileNotFoundError):
        p5_tree.tree_state(r)


# -- D5 and D6 -------------------------------------------------------------------------------------------------------
def test_d5_code_that_lies_under_the_root_is_the_trees_and_code_outside_it_is_not(tmp_path):
    r = repo(tmp_path)
    assert p5_tree.tree_state(r, code=(r / "a.txt", str(r / "sub" / "b.txt")))["tag"] == "qro-kit-v1.2.3"
    assert refused(r, code=(tmp_path / "other.py",)).where.endswith("other.py")


def test_d6_an_untagged_head_is_dirty(tmp_path):
    r = repo(tmp_path, tag=None)
    assert "no tag" in refused(r).detail


def test_d6_a_stale_tag_on_the_previous_commit_is_dirty(tmp_path):
    r = repo(tmp_path)
    (r / "a.txt").write_bytes(b"alpha two\n")
    git(r, "commit", "-q", "-am", "two")
    refused(r)


@pytest.mark.parametrize("tag", ["v1.2.3", "qro-kit-v1.2", "qro-kit-v1.2.3-rc1", "xqro-kit-v1.2.3", "qro-kit-v1.2.3x",
                                  "qro-kit-v.1.2", "qro-kit-v\u0661.0.0", "QRO-KIT-V1.2.3", "qro-kit-v1.2.3.4"])
def test_d6_a_tag_of_the_wrong_name_is_dirty(tmp_path, tag):
    r = repo(tmp_path, tag=tag)
    refused(r)


@pytest.mark.parametrize("tag", ["qro-kit-v0.0.0", "qro-kit-v10.20.30", "qro-kit-v1.0.0"])
def test_d6_a_tag_of_the_right_name_is_accepted(tmp_path, tag):
    assert p5_tree.tree_state(repo(tmp_path, tag=tag))["tag"] == tag


def test_the_tag_pattern_is_the_leads_and_never_writes_backslash_d():
    assert p5_tree.TAG_PATTERN == r"^qro-kit-v[0-9]+\.[0-9]+\.[0-9]+$"
    assert "\\d" not in p5_tree.TAG_PATTERN
    assert p5_tree.FILE_MODES == ("100644", "100755")
