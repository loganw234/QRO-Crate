"""The tools' own checks, each watched to fail (HonestFramework, METHOD.md section 3; P0's verifier's notes): the
vocabulary's --check on a changed or missing file, the instruments' check on a wrong checkout, and the privacy
gate's alternatives walked both ways against their plants."""
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(rel):
    spec = importlib.util.spec_from_file_location(Path(rel).stem, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = load("tools/gen_vocabulary.py")
privacy = load("tools/check_privacy.py")


def copy_outputs(tmp_path):
    for rel in gen.OUTPUTS:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, tmp_path / rel)
    return tmp_path


def test_the_generated_files_are_what_their_definitions_render():
    assert gen.problems() == []
    assert gen.drift(ROOT) == []


@pytest.mark.parametrize("rel", sorted(gen.OUTPUTS))
def test_a_changed_byte_in_a_generated_file_is_drift(tmp_path, rel):
    root = copy_outputs(tmp_path)
    data = bytearray((root / rel).read_bytes())
    data[len(data) // 2] ^= 1
    (root / rel).write_bytes(bytes(data))
    assert [r for r, _ in gen.drift(root)] == [rel]
    assert gen.main(["--check"], root=root) == 1


def test_a_missing_generated_file_is_drift(tmp_path):
    root = copy_outputs(tmp_path)
    (root / "docs" / "REFUSALS.md").unlink()
    assert gen.drift(root) == [("docs/REFUSALS.md", "missing; run --write")]


def test_the_instruments_check_fails_on_a_wrong_checkout(tmp_path):
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "check_instruments.py"), str(tmp_path)],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "0 of 5 instruments reproduced" in r.stdout


def test_every_privacy_alternative_has_its_own_plant_and_every_plant_names_one():
    names = [n for _, n, _ in privacy.ALTERNATIVES]
    assert len(names) == len(set(names))
    assert set(names) == set(privacy.PLANTS)


@pytest.mark.parametrize("name", sorted(privacy.PLANTS))
def test_each_privacy_plant_is_caught_by_its_own_alternative(name):
    assert any(n == name for _, n, _ in privacy.findings(privacy.PLANTS[name], {name}))


@pytest.mark.parametrize("name, text", [
    ("wsl-unc-slash", "see " + "//" + "wsl.localhost" + "/Ubuntu/" + "home" + "/someone"),
    ("wsl-unc-slash", "(" + "//" + "wsl$" + "/Ubuntu/x)"),
    ("url-quoted-drive", "see C:" + "%5C%5C" + "Users" + "%5C%5C" + "someone"),
    ("url-quoted-drive", "see C:" + "%2F" + "Users" + "%2F" + "someone"),
    ("url-quoted-drive", "type%20C:" + "%5C" + "Users" + "%5C" + "someone"),
    ("wsl-file-url", "see file:" + "//" + "wsl$" + "/Ubuntu/" + "home" + "/someone"),
    ("wsl-file-url", "see file:" + "//" + "wsl%24" + "/Ubuntu/" + "home" + "/someone"),
    ("wsl-file-url", "see file:" + "//" + "wsl$" + "/Ubuntu/" + "users" + "/someone")],
    ids=["the .localhost form", "after a bracket", "doubled separators", "the encoded slash", "after an escape",
         "a file URL with the dollar", "a file URL with the dollar encoded", "a file URL to users"])
def test_each_spelling_p06_added_finds_its_forms(name, text):
    """P0.6's verifier, round 1, notes: the .localhost form Windows 11 shows, doubled separators, the %2F branch, a
    drive after an encoded space and a file URL to the WSL host's home were each held by no plant, or passed."""
    assert any(n == name for _, n, _ in privacy.findings(text, {name})), text


@pytest.mark.parametrize("name, text", [
    ("wsl-unc-slash", "x" + "//" + "wsl$" + "/a"), ("wsl-unc-slash", "1" + "//" + "wsl$" + "/a"),
    ("wsl-unc-slash", "." + "//" + "wsl$" + "/a"), ("wsl-unc-slash", "/" + "//" + "wsl$" + "/a"),
    ("wsl-unc-slash", "https:" + "//" + "wsl.localhost" + "/a"),
    ("url-quoted-drive", "see C:" + "%5C" + "Users" + "%5C" + "%3Cname%3E"),
    ("url-quoted-drive", "doc:" + "%5C" + "users" + "%5C" + "bob"),
    ("wsl-file-url", "see https:" + "//" + "wsl.localhost" + "/Ubuntu/" + "home" + "/someone"),
    ("wsl-unc-slash", "see " + "//" + "wsl.localhost" + ".example.org/x"),
    ("url-quoted-drive", "xAB" + "C:" + "%5C" + "Users" + "%5C" + "someone"),
    ("url-quoted-drive", "1" + "C:" + "%5C" + "Users" + "%5C" + "someone"),
    ("wsl-file-url", "see file:" + "//" + "wsl$" + "/Ubuntu/" + "home" + "/%3Cname%3E"),
    ("wsl-file-url", "xfile:" + "//" + "wsl$" + "/Ubuntu/" + "home" + "/someone"),
    ("wsl-file-url", "see file:" + "//" + "wsl$" + "//" + "home" + "/someone"),
    ("url-quoted-drive", "x%ZZ" + "C:" + "%5C" + "Users" + "%5C" + "someone")],
    ids=["after a letter", "after a digit", "after a dot", "after a slash", "a URL whose host is named wsl",
         "a placeholder for the name", "a scheme ending in a letter", "another scheme", "a longer host",
         "hex letters with no percent before", "a digit that is no escape's before", "a file URL's placeholder",
         "a file URL inside a word", "a file URL with no distribution", "a percent sign before no hex pair"])
def test_each_spelling_p06_added_keeps_its_edges(name, text):
    """P0.6's verifier, round 1, notes: each part of the two lookbehinds, and the name the drive's form requires,
    held by no test."""
    assert privacy.findings(text, {name}) == [], text


def test_the_privacy_gate_finds_nothing_in_text_without_a_plant():
    """And the two spellings P0.6 added keep their edges: a URL whose host is named wsl is no UNC path, and a scheme
    ending in a letter before an encoded path is no drive."""
    text = ("moth_quantum_files_read, /docs/studies/qro0/, noreply@anthropic.com, user@example.org, "
            "C:\\Users\\<name>\\x, /home/{user}/x, /c/Users/$USER/x, C:\\Users\\%USERNAME%\\x, "
            "https://wsl.localhost/docs, doc:%5Cusers%5Cbob")
    assert privacy.findings(text) == []


# -- the privacy gate's own verdicts, watched (P0's verifier, round 6, 8.1 items 1 to 3) ------------------------
@pytest.fixture(autouse=True)
def no_git_of_the_users(monkeypatch, tmp_path_factory):
    """Every test here, and every git it starts, runs with none of the user's git: no GIT_ variable (GIT_DIR, set by
    a hook, sent the test repositories' commits into the repository it named; GIT_CONFIG_COUNT set a signer), no
    global configuration and no system's (P0.1's verifier, rounds 1 and 2, notes 4.2 and 4.1.8), and no global
    ignore or attributes file, which git reads from XDG_CONFIG_HOME whatever GIT_CONFIG_GLOBAL names (P0.2's
    verifier, round 2: a global ignore file listing build/ failed a test here)."""
    import os
    for k in [k for k in os.environ if k.upper().startswith("GIT_")]:
        monkeypatch.delenv(k)
    empty = tmp_path_factory.mktemp("git") / "gitconfig-empty"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("xdg")))


def hermetic_git(tmp_path):
    """The environment for a git, or a gate, this file starts: the process's own, which no_git_of_the_users has
    emptied of the user's git."""
    import os
    return dict(os.environ)


def test_the_tests_git_is_none_of_the_users():
    import os
    assert os.environ["GIT_CONFIG_NOSYSTEM"] == "1" and Path(os.environ["GIT_CONFIG_GLOBAL"]).read_text() == ""
    assert not list(Path(os.environ["XDG_CONFIG_HOME"]).iterdir())
    assert not [k for k in os.environ if k.upper().startswith("GIT_") and k not in ("GIT_CONFIG_GLOBAL",
                                                                                    "GIT_CONFIG_NOSYSTEM")]


def git_tree(tmp_path, files, message="a clean commit"):
    """A small repository, one commit, its tracked files given; the address is in a reserved domain."""
    import subprocess
    r = tmp_path / "repo"
    r.mkdir(parents=True)
    for name, text in files.items():
        (r / name).parent.mkdir(parents=True, exist_ok=True)
        (r / name).write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))
    env = hermetic_git(tmp_path)
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    subprocess.run(["git", "-C", str(r), "init", "-q"], check=True, env=env)
    subprocess.run(git + ["add", "-A"], check=True, env=env)
    subprocess.run(git + ["commit", "-q", "-m", message], check=True, env=env)
    return r


def test_the_gate_exits_1_on_a_key_in_a_tracked_file_and_0_on_a_clean_tree(tmp_path):
    clean = git_tree(tmp_path / "a", {"notes.md": "nothing to see" + chr(10)})
    planted = git_tree(tmp_path / "b", {"notes.md": privacy.PLANTS["named:QISKIT_IBM_TOKEN"] + chr(10)})
    assert privacy.run(clean) == 0
    assert privacy.run(planted) == 1


def test_the_gate_reads_every_commit_message(tmp_path):
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)},
                 message="a note" + chr(10) + chr(10) + privacy.PLANTS["named:QISKIT_IBM_TOKEN"])
    bad, summary = privacy.check(r)
    assert "1 commit messages read" in summary
    assert [b for b in bad if b.startswith("commit ") and ": a key (" in b], bad
    assert privacy.run(r) == 1


def test_the_controls_fail_when_one_alternative_misses_its_plant(tmp_path, monkeypatch):
    """The controls' own verdict, watched: one alternative made blind, and the run must say so and exit 1."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    (r / "tools").mkdir()
    (r / "tools" / "check_privacy.py").write_text("# a stand-in the controls write into" + chr(10), encoding="utf-8")
    assert privacy.control(r) == 0
    blind = [(k, n, re.compile("(?!)") if n == "var-home" else pat) for k, n, pat in privacy.COMPILED]
    monkeypatch.setattr(privacy, "COMPILED", blind)
    assert privacy.control(r) == 1


def test_an_unreadable_tracked_file_fails_the_gate(tmp_path):
    """A file git would commit and the gate cannot read is a finding, not a pass."""
    r = git_tree(tmp_path, {"notes.md": "nothing" + chr(10), "gone.md": "soon gone" + chr(10)})
    (r / "gone.md").unlink()
    bad, _ = privacy.check(r)
    assert [b for b in bad if b.startswith("gone.md: unreadable")], bad


def test_the_gate_reads_its_own_repository_whatever_repository_gits_variables_name(tmp_path, monkeypatch):
    """P0.2's verifier, round 1, G5: with GIT_DIR and GIT_WORK_TREE naming another repository, git listed that
    one's files, which the gate read in its own tree, and that one's commit messages: a key in a file the other
    does not hold, and in a message, passed."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    other = git_tree(tmp_path / "other", {"notes.md": "nothing to see" + chr(10)})
    planted = git_tree(tmp_path / "planted", {"notes.md": "nothing to see" + chr(10), "keys.md": key + chr(10)},
                       message="a note" + chr(10) + chr(10) + key)
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    (other / "garbage-index").write_bytes(b"not an index")
    monkeypatch.setenv("GIT_INDEX_FILE", str(other / "garbage-index"))         # round 2: more than the two
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", str(other / ".git" / "objects"))
    monkeypatch.setenv("GIT_COMMON_DIR", str(other / ".git"))
    bad, _ = privacy.check(planted)
    assert [b for b in bad if b.startswith("keys.md: ")] and [b for b in bad if b.startswith("commit ") and (
        ": a key (" in b)], bad      # a key found in a message, never "commit messages: unread" (round 3)


def test_the_gates_controls_init_their_own_copies_whatever_repository_gits_variables_name(tmp_path, monkeypatch):
    """P0.2's verifier, round 1, G5: the controls run `git init` in each copy they plant into. With GIT_DIR naming
    another repository, that init was the other's: git re-initialises it, and writes back a template file it lacks."""
    other = git_tree(tmp_path / "other", {"notes.md": "nothing to see" + chr(10)})
    r = git_tree(tmp_path / "planted", {"notes.md": "nothing to see" + chr(10),
                                        "tools/check_privacy.py": "# a stand-in" + chr(10)})
    (other / ".git" / "description").unlink()
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    assert privacy.control(r) == 0
    assert not (other / ".git" / "description").exists()


@pytest.mark.parametrize("given", [(("GIT_CONFIG_COUNT", "1"), ("GIT_CONFIG_KEY_0", "safe.directory"),
                                      ("GIT_CONFIG_VALUE_0", "*")),
                                     (("GIT_CONFIG_PARAMETERS", "'safe.directory'='*'"),)],
                         ids=["as a count", "as git -c gives it to a hook"])
def test_the_gate_keeps_the_configuration_git_is_given_in_the_environment(tmp_path, monkeypatch, given):
    """P0.2's verifier, round 2: git_env dropped GIT_CONFIG_COUNT too, so a checkout git trusts only through a
    safe.directory given that way was refused, and the gate raised. GIT_TEST_ASSUME_DIFFERENT_OWNER is git's own
    switch for treating a checkout as another user's."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    for k, v in (("GIT_TEST_ASSUME_DIFFERENT_OWNER", "1"),) + given:
        monkeypatch.setenv(k, v)
    bad, summary = privacy.check(r)
    assert bad == [] and summary.startswith("1 files and 1 commit messages read"), (bad, summary)


def test_the_gate_fails_loudly_where_git_cannot_list_its_files(tmp_path):
    """A broken index is git's failure, raised, never an empty list that passes (P0.2's verifier, round 2)."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    (r / ".git" / "index").write_bytes(b"not an index")
    with pytest.raises(subprocess.CalledProcessError):
        privacy.check(r)


def test_a_history_git_cannot_read_is_a_finding_and_no_history_is_none(tmp_path):
    """P0.2's verifier, round 2: with HEAD naming a commit whose object is gone, git log failed, and the gate said
    it read no message and passed; round 3: so it did for an emptied branch ref and a corrupt packed-refs. A
    repository with no commit yet has no message to read, and passes; so the controls' fresh copies are not
    caught by this."""
    import os
    import stat
    env = hermetic_git(tmp_path)

    def head_ref(r):
        return subprocess.run(["git", "-C", str(r), "symbolic-ref", "HEAD"], capture_output=True, text=True,
                              check=True, env=env).stdout.strip()

    def tip_gone(r):
        head = subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True, env=env).stdout.strip()
        obj = r / ".git" / "objects" / head[:2] / head[2:]
        os.chmod(obj, stat.S_IREAD | stat.S_IWRITE)
        obj.unlink()

    def ref_emptied(r):
        (r / ".git" / head_ref(r)).write_bytes(b"")

    def packed_refs_corrupt(r):
        subprocess.run(["git", "-C", str(r), "pack-refs", "--all"], check=True, env=env)
        assert not (r / ".git" / head_ref(r)).exists()
        (r / ".git" / "packed-refs").write_bytes(b"not a packed-refs file" + bytes([10]))
    for name, fault in (("a", tip_gone), ("b", ref_emptied), ("c", packed_refs_corrupt)):
        r = git_tree(tmp_path / name, {"notes.md": "nothing to see" + chr(10)})
        fault(r)
        bad = privacy.check(r)[0]
        assert "commit messages: unread, as git log failed" in bad, name
        # P0.4 found git reading no staged object with packed-refs corrupt, as it looked for replace refs; since
        # P0.6 the gate's git ignores replace refs, so the staged versions are read in every case
        assert "staged versions: unread, as git cat-file failed" not in bad, (name, bad)
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    (fresh / "notes.md").write_text("nothing to see" + chr(10), encoding="utf-8")
    subprocess.run(["git", "-C", str(fresh), "init", "-q"], check=True, env=hermetic_git(tmp_path))
    bad, summary = privacy.check(fresh)
    assert bad == [] and summary.startswith("1 files and 0 commit messages read"), (bad, summary)


def test_a_file_whose_name_is_not_ascii_is_read_by_its_name(tmp_path):
    """git quotes such a name unless asked for -z; the gate reads it by its own name (P0.2's verifier, round 3: with
    -z dropped, every test passed, the controls' caught by the file unread)."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path, {"caf" + chr(0xE9) + ".md": key + chr(10)})
    assert [b for b in privacy.check(r)[0] if b.startswith("caf" + chr(0xE9) + ".md: a key (")]


def test_a_commit_message_not_in_utf8_is_read_not_a_crash(tmp_path):
    """P0.2's verifier, round 3: with i18n.logOutputEncoding set, git log wrote a message the gate could not decode,
    and it raised. It reads the message, its bad bytes replaced."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)}, message="caf" + chr(0xE9))
    subprocess.run(["git", "-C", str(r), "config", "i18n.logOutputEncoding", "ISO-8859-1"], check=True,
                   env=hermetic_git(tmp_path))
    bad, summary = privacy.check(r)
    assert bad == [] and "1 commit messages read" in summary, (bad, summary)


def test_a_key_staged_and_edited_out_of_its_file_is_found(tmp_path):
    """P0.2's verifier, round 4: the gate read the file on disk, and a plain `git commit` takes what is staged."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    (r / "notes.md").write_text(key + chr(10), encoding="utf-8")
    subprocess.run(["git", "-C", str(r), "add", "notes.md"], check=True, env=hermetic_git(tmp_path))
    (r / "notes.md").write_text("nothing to see" + chr(10), encoding="utf-8")
    bad, summary = privacy.check(r)
    assert [b for b in bad if b.startswith("notes.md (staged): a key (")] and (
        "; 1 staged versions that differ from their files read" in summary), (bad, summary)


@pytest.mark.parametrize("encoding, lead", [(None, chr(1)), ("UTF-16", ""), ("UTF-16LE", ""), ("UTF-32", "")],
                         ids=["a 0x01 byte before the key", "UTF-16", "UTF-16LE", "UTF-32"])
def test_a_key_in_a_commit_message_is_found_whatever_leads_it_or_encoding_is_asked(tmp_path, encoding, lead):
    """P0.2's verifier, round 4: the gate split git log's output on a 0x01 byte, which a message may hold; and an
    i18n.logOutputEncoding of UTF-16 or its kin wrote what the gate's decoding read as no key. git log now writes
    UTF-8, and ends each message with a NUL."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)}, message="a note" + chr(10) + chr(10) + lead + key)
    if encoding:
        subprocess.run(["git", "-C", str(r), "config", "i18n.logOutputEncoding", encoding], check=True,
                       env=hermetic_git(tmp_path))
    bad, _ = privacy.check(r)
    assert [b for b in bad if b.startswith("commit ") and ": a key (" in b], bad


def test_each_commit_message_is_read_as_one(tmp_path):
    """P0.4: git log ends each message with a NUL, and the gate counts what it splits; two commits are two."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)}, message="the first")
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", "the second"], check=True, env=hermetic_git(tmp_path))
    bad, summary = privacy.check(r)
    assert bad == [] and "1 files and 2 commit messages read" in summary, (bad, summary)


def test_a_nested_repository_is_named_and_not_read(tmp_path):
    """P0.2's verifier, round 4: git lists an untracked nested repository as a directory, which the gate failed as
    unreadable. git commits it as a gitlink, never as its files: it is named, and not read, and the controls copy
    without it."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "tools/check_privacy.py": "# a stand-in" + chr(10)})
    git_tree(r / "nested", {"inner.md": "nothing" + chr(10)})
    bad, summary = privacy.check(r)
    assert bad == [] and "not read: nested/repo/: a nested repository" in summary, (bad, summary)
    assert privacy.control(r) == 0


def test_the_gate_reads_a_linked_worktree_whose_git_is_a_file(tmp_path):
    """P0.2's verifier, round 4: the parcels build in linked worktrees, where .git is a file, and no test ran the
    gate in one. P0.4's, round 1: each of git's three readings is held there, git's listing told from the walk a
    copy with no .git gets by a key in a file git ignores, and the staged versions by a key staged and edited out."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path / "main", {"notes.md": "nothing to see" + chr(10), ".gitignore": "ignored.md" + chr(10)},
                 message="a note" + chr(10) + chr(10) + key)
    w = tmp_path / "linked"
    subprocess.run(["git", "-C", str(r), "worktree", "add", "-q", str(w)], check=True, env=hermetic_git(tmp_path))
    (w / "keys.md").write_text(key + chr(10), encoding="utf-8")
    (w / "ignored.md").write_text(key + chr(10), encoding="utf-8")
    (w / "notes.md").write_text(key + chr(10), encoding="utf-8")
    subprocess.run(["git", "-C", str(w), "add", "notes.md"], check=True, env=hermetic_git(tmp_path))
    (w / "notes.md").write_text("nothing to see" + chr(10), encoding="utf-8")
    found = sorted({b.split(": a key (")[0] for b in privacy.check(w)[0]})        # two alternatives find each key
    assert (w / ".git").is_file() and found[1:] == ["keys.md", "notes.md (staged)"] and found[0].startswith(
        "commit "), found


def simulate_links(monkeypatch, texts):
    """Make each name in texts a symbolic link, with that text, as the gate sees it. This machine may not make one
    (Windows without Developer Mode refuses, WinError 1314), so the gate's is_symlink and readlink are told; the
    lead's run under WSL (docs/VALIDATION.md) holds what git and the system do with real ones."""
    is_symlink, readlink = privacy.Path.is_symlink, privacy.os.readlink
    monkeypatch.setattr(privacy.Path, "is_symlink", lambda p: p.name in texts or is_symlink(p))
    monkeypatch.setattr(privacy.os, "readlink", lambda p: texts.get(Path(p).name) or readlink(p))


@pytest.mark.parametrize("disk", ["an empty directory", "nothing"])
def test_a_gitlink_is_named_a_nested_repository_and_not_read_as_a_blob(tmp_path, disk):
    """P0.4's verifier, round 1: no test reached the staged reader's skip of a gitlink, which names another
    repository's commit and no blob here; read as a blob, every submodule would be an object missing. Staged by hand,
    it names a commit this repository does not hold, as a submodule's does. With a directory at its path, or nothing,
    it is named a nested repository."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    subprocess.run(["git", "-C", str(r), "update-index", "--add", "--cacheinfo", "160000," + "1" * 40 + ",linked"],
                   check=True, env=hermetic_git(tmp_path))
    if disk == "an empty directory":
        (r / "linked").mkdir()
    bad, summary = privacy.check(r)
    assert bad == [] and "not read: linked/: a nested repository" in summary, (bad, summary)


@pytest.mark.parametrize("disk", ["a file", "a symbolic link to a directory", "a dangling symbolic link"])
def test_a_gitlink_whose_path_holds_a_file_or_a_symbolic_link_is_read(tmp_path, monkeypatch, disk):
    """P0.4's verifier, round 2, R2-1: the gate named every gitlink a nested repository and read nothing at its path,
    so a file or a symbolic link there, which `git add -A` and `git commit -a` commit in the gitlink's place, passed
    with a key in it. A gitlink is a nested repository only while a directory that is no link, or nothing, is at
    its path. Round 3: a dangling link is something there, though it names nothing (`lexists`, never `exists`)."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    subprocess.run(["git", "-C", str(r), "update-index", "--add", "--cacheinfo", "160000," + "1" * 40 + ",sub"],
                   check=True, env=hermetic_git(tmp_path))
    if disk == "a file":
        (r / "sub").write_text(key + chr(10), encoding="utf-8")
    elif disk == "a symbolic link to a directory":
        (r / "sub").mkdir()
        simulate_links(monkeypatch, {"sub": key})
    else:
        lexists = privacy.os.path.lexists
        monkeypatch.setattr(privacy.os.path, "lexists", lambda p: Path(p).name == "sub" or lexists(p))
        simulate_links(monkeypatch, {"sub": key})
    bad, summary = privacy.check(r)
    assert [b for b in bad if b.startswith("sub: a key (")] and "nested repository" not in summary, (bad, summary)


@pytest.mark.parametrize("arm", ["an object missing", "a file gone from disk", "a binary version"])
def test_each_arm_of_the_staged_reader(tmp_path, arm):
    """P0.4's verifier, round 1: three arms of the staged reader no test reached. A staged version whose object git
    does not hold cannot be read: a finding. A key staged in a file then deleted is in the commit: found. A staged
    version that is binary is listed by name and not read, as a binary file is."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    git = ["git", "-C", str(r)]
    if arm == "an object missing":
        subprocess.run(git + ["update-index", "--add", "--cacheinfo", "100644," + "1" * 40 + ",ghost.md"], check=True,
                       env=hermetic_git(tmp_path))
    else:
        (r / "x.md").write_bytes((b"\0" if arm == "a binary version" else b"") + key.encode("ascii") + b"\n")
        subprocess.run(git + ["add", "x.md"], check=True, env=hermetic_git(tmp_path))
        if arm == "a file gone from disk":
            (r / "x.md").unlink()
        else:
            (r / "x.md").write_text("nothing to see" + chr(10), encoding="utf-8")
    bad, summary = privacy.check(r)
    if arm == "an object missing":
        assert "ghost.md (staged): unreadable: its object missing" in bad, bad
    elif arm == "a file gone from disk":
        assert [b for b in bad if b.startswith("x.md (staged): a key (")], bad
    else:
        assert bad == [] and "not read: x.md (staged): binary" in summary, (bad, summary)


def test_a_tracked_file_a_directory_replaced_is_unreadable_and_no_nested_repository(tmp_path):
    """P0.4's verifier, round 1: the gate took every directory git listed for a nested repository, so a tracked file
    a directory replaced was named one, and passed. Only git's own marks name one now, and the file git would take
    from disk cannot be read: a finding, as a tracked file deleted is."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "gone.md": "soon a directory" + chr(10)})
    (r / "gone.md").unlink()
    (r / "gone.md").mkdir()
    (r / "gone.md" / "inner.md").write_text("nothing to see" + chr(10), encoding="utf-8")
    bad, summary = privacy.check(r)
    assert [b for b in bad if b.startswith("gone.md: unreadable")] and "nested repository" not in summary, (
        bad, summary)


def test_a_link_is_read_as_its_own_text_which_git_commits(tmp_path, monkeypatch):
    """P0.4's verifier, round 1, MEASURED under WSL: an untracked symbolic link to a directory was taken for a nested
    repository and passed, where git commits the link's own text, and a home path is among what that text can be;
    one to a file was read as the file it names. The link is simulated (simulate_links)."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    (r / "link").write_text("nothing to see" + chr(10), encoding="utf-8")
    simulate_links(monkeypatch, {"link": "/" + "home" + "/someone/x"})
    bad, _ = privacy.check(r)
    assert [b for b in bad if b.startswith("link: a path (posix-home), ")], bad


def test_a_named_pipe_or_a_device_is_a_finding_and_never_read(tmp_path, monkeypatch):
    """P0.4's verifier, round 3, MEASURED under WSL: a named pipe at a tracked file's path, or at a gitlink's, held
    the gate for ever, read as a file. It is neither a file, a directory nor a link, so it is unreadable, a finding.
    Where the host makes a pipe, a real one stands at the path; where it makes none, Windows, the pipe is a file the
    gate's is_file calls none (P0.4's verifier, round 4, note 8)."""
    import os
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "pipe": "nothing to see" + chr(10)})
    if hasattr(os, "mkfifo"):
        (r / "pipe").unlink()
        os.mkfifo(r / "pipe")
    else:
        is_file = privacy.Path.is_file
        monkeypatch.setattr(privacy.Path, "is_file", lambda p: p.name != "pipe" and is_file(p))
    assert "pipe: unreadable: OSError" in privacy.check(r)[0]


def test_a_symbolic_link_to_a_pipe_is_read_as_its_text(tmp_path, monkeypatch):
    """P0.4's verifier, round 4, note 7: the link check comes before the pipe check, since a link to a pipe is no
    pipe and is committed as its text; no test held the order. The link and the pipe are simulated."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    (r / "link").write_text("what it names" + chr(10), encoding="utf-8")
    simulate_links(monkeypatch, {"link": "/" + "home" + "/someone/pipe"})
    is_file = privacy.Path.is_file
    monkeypatch.setattr(privacy.Path, "is_file", lambda p: p.name != "link" and is_file(p))
    assert [b for b in privacy.check(r)[0] if b.startswith("link: a path (posix-home)")]


def test_a_history_git_cannot_list_is_a_finding(tmp_path):
    """P0.6: git failing to list the history's objects is a finding, never a crash or a pass. A tree object made
    garbage is one git log, which reads commits alone, never opens, and `git rev-list --objects` cannot read."""
    import os
    import stat
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    oid = subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD^{tree}"], capture_output=True, text=True,
                         check=True, env=hermetic_git(tmp_path)).stdout.strip()
    obj = r / ".git" / "objects" / oid[:2] / oid[2:]
    os.chmod(obj, stat.S_IREAD | stat.S_IWRITE)
    obj.write_bytes(b"not an object")
    bad = privacy.check(r)[0]
    assert "earlier commits' files: unread, as git could not list or read them" in bad, bad


def test_git_failing_to_read_the_staged_objects_is_a_finding(tmp_path):
    """P0.4: git cat-file failing is a finding, never a crash or a pass. P0.6's verifier, round 1, D3, MEASURED: a
    staged version's loose object cut to half its length leaves git ls-files reading the index, and git cat-file
    --batch failing on the object (P0.6 had said no repository could reach the arm, and simulated it)."""
    import os
    import stat
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    env = hermetic_git(tmp_path)
    (r / "notes.md").write_bytes(b"a staged version" + bytes([10]))
    subprocess.run(["git", "-C", str(r), "add", "notes.md"], check=True, env=env)
    (r / "notes.md").write_bytes(b"the file on disk" + bytes([10]))
    oid = subprocess.run(["git", "-C", str(r), "rev-parse", ":notes.md"], capture_output=True, text=True,
                         check=True, env=env).stdout.strip()
    obj = r / ".git" / "objects" / oid[:2] / oid[2:]
    os.chmod(obj, stat.S_IREAD | stat.S_IWRITE)
    obj.write_bytes(obj.read_bytes()[:obj.stat().st_size // 2])
    listing = subprocess.run(["git", "-C", str(r), "ls-files", "-z", "--stage"], capture_output=True, env=env)
    assert listing.returncode == 0, "git ls-files still reads the index: the test's own control"
    bad = privacy.check(r)[0]
    assert "staged versions: unread, as git cat-file failed" in bad, bad


def test_a_key_committed_and_deleted_in_a_later_commit_is_found(tmp_path):
    """P0.4's verifier, round 4, note 1, MEASURED: the gate read HEAD's files and messages, and a key committed and
    then deleted passed, though a push sends the commit that holds it. It reads every blob of HEAD's history that
    the index does not hold, and names the commit's blob."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "keys.md": key + chr(10)})
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    subprocess.run(git + ["rm", "-q", "keys.md"], check=True, env=hermetic_git(tmp_path))
    subprocess.run(git + ["commit", "-q", "-m", "the key gone"], check=True, env=hermetic_git(tmp_path))
    bad, summary = privacy.check(r)
    assert [b for b in bad if b.startswith("keys.md (history ") and ": a key (" in b] and (
        "; 1 versions in earlier commits read" in summary), (bad, summary)


def test_a_key_under_a_name_beginning_with_a_line_feed_is_found(tmp_path):
    """P0.6's verifier, round 1, D1, MEASURED: git rev-list cuts a path at its first line feed, so a top-level name
    that begins with one is listed empty, as the root tree is, and the reader dropped it with that tree. A key
    committed under such a name and deleted in a later commit passed, though a push sends it. git's trees hold such a
    name where no file system here does, so the commits are made from objects."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    env = hermetic_git(tmp_path)
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]

    def out(*args, data=None):
        return subprocess.run(git + list(args), input=data, capture_output=True, check=True, env=env).stdout.strip()

    blob = out("hash-object", "-w", "--stdin", data=(key + chr(10)).encode("ascii"))
    entries = subprocess.run(git + ["ls-tree", "-z", "HEAD"], capture_output=True, check=True, env=env).stdout
    tree = out("mktree", "-z", data=entries + b"100644 blob " + blob + b"\t" + bytes([10]) + b"keys.md\0")
    first = out("commit-tree", tree.decode("ascii"), "-p", "HEAD", "-m", "a key under a name beginning with a feed")
    second = out("commit-tree", "HEAD^{tree}", "-p", first.decode("ascii"), "-m", "the key gone")
    out("update-ref", "HEAD", second.decode("ascii"))
    listed = subprocess.run(git + ["rev-list", "--objects", "HEAD", "--"], capture_output=True, check=True, env=env)
    assert blob + b" " + bytes([10]) in listed.stdout + bytes([10]), "git lists the name empty: the test's own control"
    bad = privacy.check(r)[0]
    assert [b for b in bad if b.startswith("(a path beginning with a line feed) (history ") and ": a key (" in b], bad


@pytest.mark.parametrize("files", [{"HEAD": "a file so named" + chr(10)}, {"head": "a file so named" + chr(10)},
                                   {"HEAD/notes.md": "a file so named" + chr(10)}],
                         ids=["a file named HEAD", "a file named head", "a directory named HEAD"])
def test_a_file_or_a_directory_named_head_at_the_root_is_no_finding(tmp_path, files):
    """P0.6's verifier, round 1, D2, MEASURED: git rev-list read HEAD as both a revision and a path at the root, and
    refused the listing, so a clean tree holding one failed the gate; `head` too, where the file system ignores case.
    The revision is ended by `--`. A second commit gives the history a blob the index does not hold."""
    r = git_tree(tmp_path, {**{"notes.md": "nothing to see" + chr(10)}, **files})
    (r / "notes.md").write_bytes(b"nothing else to see" + bytes([10]))
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    subprocess.run(git + ["commit", "-q", "-am", "a second version"], check=True, env=hermetic_git(tmp_path))
    bad, summary = privacy.check(r)
    assert bad == [] and "; 1 versions in earlier commits read" in summary, (bad, summary)


def test_a_replace_ref_hides_no_earlier_blob_from_the_gate(tmp_path):
    """P0.6's verifier, round 1, note: the history reader's gits ignore replace refs, which no test held, since the
    test of the messages reads git log alone. A key committed and deleted, its blob replaced by a clean one: a push
    sends the key, and the gate reads it."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "keys.md": key + chr(10)})
    env = hermetic_git(tmp_path)
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    blob = subprocess.run(git + ["rev-parse", "HEAD:keys.md"], capture_output=True, text=True, check=True,
                          env=env).stdout.strip()
    subprocess.run(git + ["rm", "-q", "keys.md"], check=True, env=env)
    subprocess.run(git + ["commit", "-q", "-m", "the key gone"], check=True, env=env)
    clean = subprocess.run(git + ["hash-object", "-w", "--stdin"], input=b"a clean stand-in" + bytes([10]),
                           capture_output=True, check=True, env=env).stdout.decode("ascii").strip()
    subprocess.run(git + ["replace", blob, clean], check=True, env=env)
    shown = subprocess.run(git + ["cat-file", "-p", blob], capture_output=True, check=True, env=env).stdout
    assert shown.startswith(b"a clean stand-in"), "the replace ref did not take: the test's own control"
    assert [b for b in privacy.check(r)[0] if b.startswith("keys.md (history ") and ": a key (" in b]


def test_the_gate_reads_its_own_history_whatever_repository_gits_variables_name(tmp_path, monkeypatch):
    """P0.6's verifier, round 1, note: the test of git's variables has one commit, so the history reader read
    nothing there, and its gits' cleaning of the variables was held by no test. A key committed and deleted in the
    gate's own repository is found, with every variable naming another."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    other = git_tree(tmp_path / "other", {"notes.md": "nothing to see" + chr(10)})
    planted = git_tree(tmp_path / "planted", {"notes.md": "nothing to see" + chr(10), "keys.md": key + chr(10)})
    git = ["git", "-C", str(planted), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    subprocess.run(git + ["rm", "-q", "keys.md"], check=True, env=hermetic_git(tmp_path))
    subprocess.run(git + ["commit", "-q", "-m", "the key gone"], check=True, env=hermetic_git(tmp_path))
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", str(other / ".git" / "objects"))
    monkeypatch.setenv("GIT_COMMON_DIR", str(other / ".git"))
    bad, _ = privacy.check(planted)
    assert [b for b in bad if b.startswith("keys.md (history ") and ": a key (" in b], bad


def test_a_key_in_an_earlier_commit_of_a_sha256_repository_is_found(tmp_path):
    """P0.6's verifier, round 1, note: the reader's arm for object ids of 64 hex digits was held by no test (the
    code worked, MEASURED by the verifier). git makes a SHA-256 repository on request, from git 2.29 (round 2, note
    9: the test needs it, and nothing else here does)."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = tmp_path / "repo"
    r.mkdir()
    env = hermetic_git(tmp_path)
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    subprocess.run(["git", "-C", str(r), "init", "-q", "--object-format=sha256"], check=True, env=env)
    (r / "notes.md").write_bytes(b"nothing to see" + bytes([10]))
    (r / "keys.md").write_bytes((key + chr(10)).encode("ascii"))
    subprocess.run(git + ["add", "-A"], check=True, env=env)
    subprocess.run(git + ["commit", "-q", "-m", "a clean commit"], check=True, env=env)
    subprocess.run(git + ["rm", "-q", "keys.md"], check=True, env=env)
    subprocess.run(git + ["commit", "-q", "-m", "the key gone"], check=True, env=env)
    head = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True, check=True, env=env).stdout
    assert len(head.strip()) == 64, "a SHA-256 repository: the test's own control"
    bad = privacy.check(r)[0]
    assert [b for b in bad if b.startswith("keys.md (history ") and ": a key (" in b], bad


@pytest.mark.parametrize("where", ["in the tree", "in an earlier commit only"])
def test_the_gate_writes_a_name_its_console_cannot_as_an_escape(tmp_path, where):
    """P0.6's verifier, round 2, D1, MEASURED: with stdout redirected in a code page that cannot write a file's name,
    a binary file named in CJK characters, which the summary lists by name, crashed the gate's last print. Before
    P0.6 only a file in the tree could; the history reader lets a file of an earlier commit do it too, so a tree that
    8afeede's gate passed failed. The name is written as its escape."""
    gate = (ROOT / "tools" / "check_privacy.py").read_bytes()
    name = chr(0x4E2D) + chr(0x6587) + ".bin"
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "tools/check_privacy.py": gate, name: b"\0" + b"x"})
    if where == "in an earlier commit only":
        git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]
        subprocess.run(git + ["rm", "-q", name], check=True, env=hermetic_git(tmp_path))
        subprocess.run(git + ["commit", "-q", "-m", "the file gone"], check=True, env=hermetic_git(tmp_path))
    p = subprocess.run([sys.executable, "tools/check_privacy.py"], cwd=r, capture_output=True,
                       env=dict(hermetic_git(tmp_path), PYTHONIOENCODING="cp1252"))
    assert p.returncode == 0, p.stderr[-400:]
    assert b"not read: " + "\\u4e2d\\u6587.bin".encode("ascii") in p.stdout, p.stdout[-400:]


def test_a_blob_of_an_earlier_commit_git_cannot_read_is_a_finding(tmp_path):
    """P0.6's verifier, round 2, note 1, MEASURED: history()'s arm for `git cat-file --batch` failing was held by no
    test, though real damage reaches it. A blob of an earlier commit only, its loose object cut to half its length,
    leaves the listing and the types whole, and the batch read failing. The note is long enough that the object's
    header, its first bytes, survives the cut."""
    import os
    import stat
    note = "".join(f"line {n}, an old note{chr(10)}" for n in range(400))
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "old.md": note})
    env = hermetic_git(tmp_path)
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    oid = subprocess.run(git + ["rev-parse", "HEAD:old.md"], capture_output=True, text=True, check=True,
                         env=env).stdout.strip()
    subprocess.run(git + ["rm", "-q", "old.md"], check=True, env=env)
    subprocess.run(git + ["commit", "-q", "-m", "the note gone"], check=True, env=env)
    obj = r / ".git" / "objects" / oid[:2] / oid[2:]
    os.chmod(obj, stat.S_IREAD | stat.S_IWRITE)
    obj.write_bytes(obj.read_bytes()[:obj.stat().st_size // 2])
    checked = subprocess.run(git + ["cat-file", "--batch-check"], input=(oid + chr(10)).encode("ascii"),
                             capture_output=True, env=env)
    assert checked.returncode == 0 and b" blob " in checked.stdout, "its type still reads: the test's own control"
    bad = privacy.check(r)[0]
    assert "earlier commits' files: unread, as git could not list or read them" in bad, bad


@pytest.mark.parametrize("what", ["the commit", "the blob, by a tree"])
def test_a_replace_ref_hides_no_earlier_key_from_the_gate(tmp_path, what):
    """P0.6's verifier, round 2, note 2: the replace flag was held on `cat-file --batch` alone. A key committed and
    deleted, and then its commit replaced by one whose tree holds no key, or its blob by a tree: a git that honours
    replace refs walks the replacement, or calls the blob a tree, and reads no key. A push sends the original, and
    the gate reads it."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "keys.md": key + chr(10)})
    env = hermetic_git(tmp_path)
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]

    def out(*args):
        return subprocess.run(git + list(args), capture_output=True, text=True, check=True, env=env).stdout.strip()
    keyed, blob = out("rev-parse", "HEAD"), out("rev-parse", "HEAD:keys.md")
    out("rm", "-q", "keys.md")
    out("commit", "-q", "-m", "the key gone")
    clean_tree = out("rev-parse", "HEAD^{tree}")
    if what == "the commit":
        out("replace", keyed, out("commit-tree", clean_tree, "-m", "no key was here"))
        took = blob not in out("rev-list", "--objects", "HEAD", "--").split()
    else:
        out("replace", "-f", blob, clean_tree)
        took = out("cat-file", "-t", blob) == "tree"
    assert took, "the replace ref did not take: the test's own control"
    assert [b for b in privacy.check(r)[0] if b.startswith("keys.md (history ") and ": a key (" in b]


@pytest.mark.parametrize("mode", [[], ["--control"]], ids=["the run", "the controls"])
@pytest.mark.parametrize("stdout", ["None", "io.StringIO()"], ids=["no stdout", "a stream with no reconfigure"])
def test_the_gate_runs_where_there_is_no_stdout_to_reconfigure(tmp_path, stdout, mode):
    """P0.6's verifier, round 3, D1, MEASURED: round 2's fix reconfigured stdout on every run. Where stdout is None
    (pythonw, or a closed descriptor) or a stream with no reconfigure (a console's StringIO), it raised an
    AttributeError, and a clean tree that 37640f0's gate passed failed. The gate runs as `__main__` under each, as
    the verifier's portable shape runs it, in both modes."""
    gate = (ROOT / "tools" / "check_privacy.py").read_bytes()
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "tools/check_privacy.py": gate})
    code = ("import io, runpy, sys; sys.stdout = " + stdout + "; sys.argv = ['tools/check_privacy.py'] + "
            + repr(mode) + "; runpy.run_path('tools/check_privacy.py', run_name='__main__')")
    p = subprocess.run([sys.executable, "-I", "-c", code], cwd=r, capture_output=True, env=hermetic_git(tmp_path))
    assert p.returncode == 0, p.stderr[-400:]


def test_a_key_under_a_name_not_in_utf8_in_an_earlier_commit_is_found(tmp_path):
    """P0.6's verifiers, round 2, note 3, and round 3, note 1: a path of HEAD's history that is not UTF-8 is read, its
    name decoded with replacement, as the gate's docstring says, and no test held it: a strict decode survived. git's
    trees hold such a name where this file system does not, so the commits are made from objects."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    env = hermetic_git(tmp_path)
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]

    def out(*args, data=None):
        return subprocess.run(git + list(args), input=data, capture_output=True, check=True, env=env).stdout.strip()

    blob = out("hash-object", "-w", "--stdin", data=(key + chr(10)).encode("ascii"))
    entries = subprocess.run(git + ["ls-tree", "-z", "HEAD"], capture_output=True, check=True, env=env).stdout
    tree = out("mktree", "-z", data=entries + b"100644 blob " + blob + b"\tcaf" + bytes([0xE9]) + b".md\0")
    first = out("commit-tree", tree.decode("ascii"), "-p", "HEAD", "-m", "a key under a name in Latin-1")
    second = out("commit-tree", "HEAD^{tree}", "-p", first.decode("ascii"), "-m", "the key gone")
    out("update-ref", "HEAD", second.decode("ascii"))
    bad = privacy.check(r)[0]
    assert [b for b in bad if b.startswith("caf" + chr(0xFFFD) + ".md (history ") and ": a key (" in b], bad


def test_a_history_whose_types_git_cannot_read_is_a_finding(tmp_path, monkeypatch):
    """P0.6's verifiers, rounds 2 and 3, a note each: history()'s arm for `git cat-file --batch-check` failing was
    held by no test. No damage either verifier made reached it once the listing had passed, so the failure is
    simulated, on the history's call alone."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "old.md": "an old note" + chr(10)})
    env = hermetic_git(tmp_path)
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    subprocess.run(git + ["rm", "-q", "old.md"], check=True, env=env)
    subprocess.run(git + ["commit", "-q", "-m", "the note gone"], check=True, env=env)
    real = privacy.subprocess.run

    def run(cmd, *args, **kwargs):
        if list(cmd[-2:]) == ["cat-file", "--batch-check"]:
            return subprocess.CompletedProcess(cmd, 128, b"", b"fatal: simulated")
        return real(cmd, *args, **kwargs)
    monkeypatch.setattr(privacy.subprocess, "run", run)
    assert "earlier commits' files: unread, as git could not list or read them" in privacy.check(r)[0]


def test_a_binary_blob_in_an_earlier_commit_is_listed_by_name(tmp_path):
    """A stated limit, held: a binary blob of HEAD's history is not read, and is named in the summary; and no tree is
    read as a blob, which would list each directory as one (P0.6's mutants)."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "data/blob.bin": b"\0" + b"x",
                            "data/kept.md": "nothing to see" + chr(10)})
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    subprocess.run(git + ["rm", "-q", "data/blob.bin"], check=True, env=hermetic_git(tmp_path))
    subprocess.run(git + ["commit", "-q", "-m", "the blob gone"], check=True, env=hermetic_git(tmp_path))
    bad, summary = privacy.check(r)
    unread = [line for line in summary.splitlines() if line.startswith("  not read: ")]
    assert bad == [] and len(unread) == 1 and unread[0].startswith("  not read: data/blob.bin (history ") \
        and unread[0].endswith(": binary"), (bad, summary)


def test_a_blob_git_lists_in_the_history_and_does_not_hold_is_a_finding(tmp_path, monkeypatch):
    """P0.6's mutants: such a blob is read as missing, a finding, never passed over. git rev-list fails first on a
    real missing blob, a finding too (MEASURED), so the listing is simulated: git lists a blob id that names no
    object, as one removed between the two calls would."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    real, fake = privacy.subprocess.run, "1" * 40

    def run(cmd, *args, **kwargs):
        done = real(cmd, *args, **kwargs)
        if list(cmd[-4:]) == ["rev-list", "--objects", "HEAD", "--"] and done.returncode == 0:
            return subprocess.CompletedProcess(done.args, 0, done.stdout + fake.encode("ascii") + b" gone.md\n",
                                               done.stderr)
        return done
    monkeypatch.setattr(privacy.subprocess, "run", run)
    assert "gone.md (history 1111111): unreadable: its object missing" in privacy.check(r)[0]


def test_a_replace_ref_hides_no_message_from_the_gate(tmp_path):
    """P0.4's verifier, round 4, note 2, MEASURED: with a replace ref, git log showed another message than the one a
    push sends, and a key in the real one passed. The gate's git ignores replace refs, as a push does."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)}, message="a note" + chr(10) + chr(10) + key)
    env = hermetic_git(tmp_path)
    head = subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
                          env=env).stdout.strip()
    clean = subprocess.run(["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org", "commit-tree",
                            "-m", "a clean note", head + "^{tree}"], capture_output=True, text=True, check=True,
                           env=env).stdout.strip()
    subprocess.run(["git", "-C", str(r), "replace", head, clean], check=True, env=env)
    shown = subprocess.run(["git", "-C", str(r), "log", "--format=%B"], capture_output=True, text=True, check=True,
                           env=env).stdout
    assert "a clean note" in shown, "the replace ref did not take: the test's own control"
    assert [b for b in privacy.check(r)[0] if b.startswith("commit ") and ": a key (" in b]


def test_a_known_finding_in_a_pushed_blob_is_listed_and_no_other(tmp_path, monkeypatch):
    """P0.6: a finding in a blob of an earlier commit that KNOWN names, by its blob and its alternative, is listed as
    known and fails nothing; the same blob under another alternative, or another blob, still fails."""
    plant = privacy.PLANTS["posix-home"]
    r = git_tree(tmp_path, {"notes.md": plant + chr(10)})
    oid = subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD:notes.md"], capture_output=True, text=True,
                         check=True, env=hermetic_git(tmp_path)).stdout.strip()
    (r / "notes.md").write_text("nothing to see" + chr(10), encoding="utf-8")
    git = ["git", "-C", str(r), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    subprocess.run(git + ["commit", "-q", "-am", "the path gone"], check=True, env=hermetic_git(tmp_path))
    assert [b for b in privacy.check(r)[0] if b.startswith("notes.md (history ")]
    monkeypatch.setattr(privacy, "KNOWN", {(oid, "var-home"): "another alternative's"})
    assert [b for b in privacy.check(r)[0] if b.startswith("notes.md (history ")]
    monkeypatch.setattr(privacy, "KNOWN", {(oid, "posix-home"): "a test's own"})
    bad, summary = privacy.check(r)
    assert bad == [] and "known, in a pushed commit: notes.md (history " in summary and "a test's own" in summary
    # P0.6's verifier, round 1, note: the same bytes as the file now, and then staged, are each a finding
    (r / "notes.md").write_bytes((plant + chr(10)).encode("utf-8"))
    assert [b for b in privacy.check(r)[0] if b.startswith("notes.md: a path (posix-home)")]
    subprocess.run(["git", "-C", str(r), "add", "notes.md"], check=True, env=hermetic_git(tmp_path))
    (r / "notes.md").write_bytes(b"nothing to see" + bytes([10]))
    assert [b for b in privacy.check(r)[0] if b.startswith("notes.md (staged): a path (posix-home)")]


def known_problems(root):
    """KNOWN's entries that claim more than they hold. Each must be a blob id, an alternative and a reason; and where
    git at root holds the blob, its alternative must find something in it. A copy whose history does not reach the
    commit that pushed the blob, a shallow clone or a fresh git init, holds no such blob, and the gate reads none
    there. On this repository's own history, an entry whose blob or alternative is wrong leaves that blob's findings
    unknown, and the privacy stage fails."""
    import os
    names = {n for _, n, _ in privacy.ALTERNATIVES}
    out = []
    for (oid, name), why in privacy.KNOWN.items():
        if not (re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid) and name in names and why):
            out.append((oid, name, "no blob id, alternative and reason"))
        elif privacy.in_git(root):
            got = subprocess.run(["git", "-C", str(root), "cat-file", "blob", oid], capture_output=True,
                                 env=dict(os.environ, GIT_NO_REPLACE_OBJECTS="1"))
            if got.returncode == 0 and not privacy.findings(got.stdout.decode("utf-8", errors="replace"), {name}):
                out.append((oid, name, "its alternative finds nothing in its blob"))
    return out


def test_each_known_finding_is_found_in_its_blob_where_git_holds_it():
    """P0.6: the list holds only what it claims (known_problems)."""
    assert known_problems(ROOT) == []


def test_the_known_list_holds_in_a_copy_whose_history_lacks_its_blobs(tmp_path):
    """The lead, before P0.6's first round (MEASURED): the check asked git for each blob, and failed the tool-tests
    stage in a fresh git init of the tree, as it would in a shallow clone, where no such blob is. The gate reads no
    such blob there, so the list claims nothing there."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    assert known_problems(r) == []


def test_an_entry_whose_alternative_finds_nothing_in_its_blob_is_caught(tmp_path, monkeypatch):
    """known_problems' own control: a blob git holds, in which the entry's alternative finds nothing; and an entry
    that names no alternative."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    oid = subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD:notes.md"], capture_output=True, text=True,
                         check=True, env=hermetic_git(tmp_path)).stdout.strip()
    monkeypatch.setattr(privacy, "KNOWN", {(oid, "posix-home"): "a test's own"})
    assert known_problems(r) == [(oid, "posix-home", "its alternative finds nothing in its blob")]
    monkeypatch.setattr(privacy, "KNOWN", {(oid, "no-such-alternative"): "a test's own"})
    assert known_problems(r) == [(oid, "no-such-alternative", "no blob id, alternative and reason")]


def test_a_staged_symbolic_link_is_held_to_its_text_not_to_what_it_names(tmp_path, monkeypatch):
    """P0.4's verifier, round 2, N4: the staged reader holds a version to the bytes git would commit from disk, a
    symbolic link's own text. Held to what the link names, every tracked link would be read again, as a version
    that differs. git holds a link as mode 120000 and its text; the link is simulated."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    env = hermetic_git(tmp_path)
    oid = subprocess.run(["git", "-C", str(r), "hash-object", "-w", "--stdin"], input=b"elsewhere/x.md",
                         capture_output=True, check=True, env=env).stdout.decode("ascii").strip()
    subprocess.run(["git", "-C", str(r), "update-index", "--add", "--cacheinfo", "120000," + oid + ",link"],
                   check=True, env=env)
    (r / "link").write_text("what it names" + chr(10), encoding="utf-8")
    simulate_links(monkeypatch, {"link": "elsewhere/x.md"})
    bad, summary = privacy.check(r)
    assert bad == [] and "staged versions" not in summary, (bad, summary)


def test_the_controls_copy_a_symbolic_link_as_its_own_text(tmp_path, monkeypatch):
    """P0.4's verifier, round 2, N4: the controls copy what the gate reads. Through a symbolic link, a copy took
    what the link names, and one to a directory stopped the controls with IsADirectoryError (MEASURED under WSL).
    The link is simulated."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10)})
    (r / "link").write_text("what it names" + chr(10), encoding="utf-8")
    simulate_links(monkeypatch, {"link": "elsewhere/x.md"})
    assert (privacy._copy(r, tmp_path / "copy") / "link").read_bytes() == b"elsewhere/x.md"


def test_the_controls_copies_of_a_linked_worktree_are_repositories_of_their_own(tmp_path, monkeypatch):
    """P0.4's verifier, round 2, N4: where .git is a file, the controls still `git init` each copy. Else the file
    controls read the walk a copy with no .git gets, never git's listing, which the control of a name not in ASCII
    is there to hold."""
    r = git_tree(tmp_path / "main", {"notes.md": "nothing to see" + chr(10),
                                     "tools/check_privacy.py": "# a stand-in" + chr(10)})
    w = tmp_path / "linked"
    subprocess.run(["git", "-C", str(r), "worktree", "add", "-q", str(w)], check=True, env=hermetic_git(tmp_path))
    seen, check = [], privacy.check
    monkeypatch.setattr(privacy, "check", lambda root: seen.append((root / ".git").is_dir()) or check(root))
    assert privacy.control(w) == 0 and seen == [False] + [True] * len(privacy.FILE_CONTROLS), seen


def test_a_tree_with_no_git_is_walked_but_for_git_directories_and_caches(tmp_path):
    """P0.4's verifier, round 2, N3: no test ran the gate on a tree with no .git, as a copy is. The walk reads every
    file below the root, and finds a key in one, but for those in a .git, a nested repository's, and the caches."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"]
    r = tmp_path / "copy"
    for rel in ("notes.md", "sub/.git/config", "__pycache__/x.txt", ".pytest_cache/x.txt", ".ruff_cache/x.txt",
                ".gate-state/x.txt"):
        (r / rel).parent.mkdir(parents=True, exist_ok=True)
        (r / rel).write_text(key + chr(10), encoding="utf-8")
    bad, summary = privacy.check(r)
    assert {b.split(":")[0] for b in bad} == {"notes.md"} and summary.startswith("1 files and 0 commit messages"), (
        bad, summary)


def test_the_gates_command_line_exits_as_its_verdict_in_both_modes(tmp_path):
    """P0.1's verifier, round 1, 4.2: run() and control() were held, and the line the runner reads, `__main__`, was
    not. A copy of the gate in a small repository, run as the runner runs it."""
    gate = (ROOT / "tools" / "check_privacy.py").read_text(encoding="utf-8")
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "tools/check_privacy.py": gate})

    def run(*args):
        return subprocess.run([sys.executable, "tools/check_privacy.py", *args], cwd=r, capture_output=True,
                              text=True, env=hermetic_git(tmp_path))
    assert (run().returncode, run("--control").returncode) == (0, 0)
    old = '/var/home/" + _NAME'
    assert gate.count(old) == 1
    (r / "tools" / "check_privacy.py").write_text(gate.replace(old, '/var/home/(?!)" + _NAME'), encoding="utf-8")
    blind = run("--control")
    assert blind.returncode == 1 and re.search(r"control +var-home +NOT CAUGHT", blind.stdout), blind.stdout[-600:]
    (r / "keys.md").write_text(privacy.PLANTS["named:QISKIT_IBM_TOKEN"] + chr(10), encoding="utf-8")
    assert run().returncode == 1


def test_the_controls_fail_when_an_alternative_has_no_plant(tmp_path, monkeypatch, capsys):
    """P0.1's verifier, round 1, 4.2: half the controls' verdict, an alternative with no plant, was held by no test;
    and the summary says which way it went."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "tools/check_privacy.py": "# a stand-in" + chr(10)})
    assert privacy.control(r) == 0
    assert capsys.readouterr().out.rstrip().endswith("caught; every alternative has its own plant")
    plants = dict(privacy.PLANTS)
    del plants["var-home"]
    monkeypatch.setattr(privacy, "PLANTS", plants)
    assert privacy.control(r) == 1
    out = capsys.readouterr().out
    assert re.search(r"control +var-home +NO PLANT", out) and out.rstrip().endswith("caught; 1 unpaired"), out


def test_a_file_control_that_catches_nothing_fails_the_controls(tmp_path, monkeypatch, capsys):
    """P0.1's verifier, round 1, 4.2: no file control's verdict was ever watched failing."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "tools/check_privacy.py": "# a stand-in" + chr(10)})
    monkeypatch.setattr(privacy, "FILE_CONTROLS", privacy.FILE_CONTROLS + [("a plant that plants nothing",
                                                                           lambda root: None)])
    assert privacy.control(r) == 1
    assert re.search(r"control +a plant that plants nothing +NOT CAUGHT", capsys.readouterr().out)


def test_a_file_control_caught_only_by_a_file_unread_fails_the_controls(tmp_path, monkeypatch, capsys):
    """P0.2's verifier, round 3: a file control counted any finding as caught, so a name git quoted, which the gate
    could not open, passed for the key in it. A file listed and gone is such a plant: only a key or a path counts."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "tools/check_privacy.py": "# a stand-in" + chr(10)})

    def gone(root):
        (root / "gone.md").write_text("nothing" + chr(10), encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "gone.md"], check=True, env=hermetic_git(tmp_path))
        (root / "gone.md").unlink()
    monkeypatch.setattr(privacy, "FILE_CONTROLS", privacy.FILE_CONTROLS + [("a file listed and gone", gone)])
    assert privacy.control(r) == 1
    assert re.search(r"control +a file listed and gone +NOT CAUGHT", capsys.readouterr().out)


def test_a_virtual_environment_in_the_tree_is_not_read(tmp_path):
    """P0.1's verifier, round 4, N5: with the repository's .gitignore, a worktree's own environment is no file git
    would commit, so the gate does not read a third party's address in it; nor in what a build makes at the root
    (P0.2's verifier, round 1, G2). Below the root, a directory of those names is read."""
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), ".gitignore": (ROOT / ".gitignore").read_text(
        encoding="utf-8")})
    nested = ["sub/" + n for n in (".tox", ".venv", "build", "dist", "env", "venv")]
    for env in [".venv", "venv", "env", "build", "dist", ".tox"] + nested:
        (r / env / "Lib" / "pkg").mkdir(parents=True)
        (r / env / "Lib" / "pkg" / "about.py").write_text("author = 'someone" + "@" + "personal-domain.net'" + chr(10),
                                                          encoding="utf-8")
    for egg in ("pkg.egg-info", "sub/pkg.egg-info"):
        (r / egg).mkdir(parents=True, exist_ok=True)
        (r / egg / "PKG-INFO").write_text("Author-email: someone" + "@" + "personal-domain.net" + chr(10),
                                          encoding="utf-8")
    bad, summary = privacy.check(r)
    assert [b.split(":")[0] for b in bad] == [n + "/Lib/pkg/about.py" for n in nested] and summary.startswith(
        "8 files and"), (bad, summary)


def test_a_binary_file_is_listed_by_name_and_not_read(tmp_path):
    """A stated limit, held: a key inside a binary file passes, and the file is named in the summary."""
    key = privacy.PLANTS["named:QISKIT_IBM_TOKEN"].encode("ascii")
    r = git_tree(tmp_path, {"notes.md": "nothing to see" + chr(10), "blob.bin": b"\0" + key})
    bad, summary = privacy.check(r)
    assert bad == [] and "1 binary files not read" in summary and "not read: blob.bin: binary" in summary


KEY_PLACES = {"before the separator": (lambda w: "QISKIT_IBM_" + "TOKEN" + w + "=" + privacy.H, 32),
              "before a quote": (lambda w: "QISKIT_IBM_" + "TOKEN" + w + '"' + "=" + privacy.H, 16),
              "after a quote": (lambda w: "QISKIT_IBM_" + "TOKEN" + '"' + w + "=" + privacy.H, 16),
              "after the separator": (lambda w: "QISKIT_IBM_" + "TOKEN" + "=" + w + privacy.H, 16),
              "after Bearer": (lambda w: "QISKIT_IBM_" + "TOKEN" + "=Bearer" + w + privacy.H, 16),
              "after apikey": (lambda w: "QISKIT_IBM_" + "TOKEN" + "=apikey" + w + privacy.H, 16)}


@pytest.mark.parametrize("place", sorted(KEY_PLACES))
def test_the_key_patterns_white_space_is_bounded_as_its_docstring_says(place):
    """P0.1's verifier, round 1, notes 4.1.4 and 4.2: nothing held the bound. At most, a name's value is caught; one
    space more, it passes, a stated limit."""
    make, most = KEY_PLACES[place]

    def caught(n):
        return any(name == "named:QISKIT_IBM_TOKEN" for _, name, _ in privacy.findings(make(" " * n)))
    assert caught(0) and caught(most) and not caught(most + 1)


def test_an_address_search_over_a_long_run_of_letters_is_quick():
    """P0.1's verifier, round 1, note 4.1.3: 77 s for one run of 100,000 letters, when every character began a
    search."""
    import time
    t0 = time.perf_counter()
    assert privacy.findings("a" * 100_000 + " " + "b" * 100_000) == []
    assert time.perf_counter() - t0 < 3


@pytest.mark.parametrize("glue", ["-", ".", "_", "%", "+", "5"])
def test_a_second_address_glued_to_the_first_is_not_found(glue):
    """The address pattern's stated limit, held for each character of an address that ends a domain: a text's first
    address is found, and a second glued to it by that character is not. A character dropped from the
    lookbehind finds the second (P0.1's verifier, round 2, 4.1.3)."""
    at = "@"                                                          # built here: the gate reads this file
    text = "mail a" + at + "personal-domain.net" + glue + "c" + at + "other-domain.org"
    assert [s for _, name, s in privacy.findings(text) if name == "address"] == ["a" + at + "personal-domain.net"]


@pytest.mark.parametrize("glue", ["-", ".", "_", "%", "+", "5"])
def test_a_second_escaped_address_glued_to_the_first_is_not_found(glue):
    text = "mail a" + "[at]" + "personal-domain.net" + glue + "c" + "[at]" + "other-domain.org"
    found = [s for _, name, s in privacy.findings(text) if name == "escaped-address"]
    assert found == ["a" + "[at]" + "personal-domain.net"]


def test_each_address_pattern_starts_only_where_a_run_of_its_own_characters_starts():
    """Note 4.1.3: the lookbehind is the local part's own class, which is what keeps the search linear; a character
    dropped from it, a capital say, let a run of that character be searched from each of its characters."""
    for name in ("address", "escaped-address"):
        pattern = next(p for _, n, p in privacy.ALTERNATIVES if n == name)
        local = "[A-Za-z0-9._%+-]"
        assert pattern.removeprefix("(?i)").startswith(f"(?<!{local}){local}+"), name


@pytest.mark.parametrize("scheme", ["vscode-remote", "ssh", "sftp", "scp", "smb", "nfs", "rsync", "ftp", "ftps",
                                    "file"])
def test_each_remote_uri_scheme_is_caught(scheme):
    text = "see " + scheme + "://host" + "/" + "home" + "/someone/x"
    assert any(name == "remote-uri-home" for _, name, _ in privacy.findings(text, {"remote-uri-home"}))


def test_the_instruments_check_compares_each_output_and_exit(tmp_path, monkeypatch):
    """Round 6, 8.1 item 15: a run whose output differs from the kept one, or which fails, is not reproduced."""
    instruments = load("tools/check_instruments.py")
    kept = {n: (instruments.QRO0 / f"{n}.out.txt").read_bytes() for n in instruments.INSTRUMENTS}

    def fake(differ=None, fail=None):
        def run(cmd, capture_output):
            name = Path(cmd[2]).stem
            out = kept[name] + (b"x" if name == differ else b"")
            return subprocess.CompletedProcess(cmd, 1 if name == fail else 0, stdout=out, stderr=b"")
        return run
    monkeypatch.setattr(instruments.subprocess, "run", fake())
    assert instruments.main([str(tmp_path)]) == 0
    monkeypatch.setattr(instruments.subprocess, "run", fake(differ="isolation_v0"))
    assert instruments.main([str(tmp_path)]) == 1
    monkeypatch.setattr(instruments.subprocess, "run", fake(fail="free_tier_unit_v0"))
    assert instruments.main([str(tmp_path)]) == 1


def test_a_parcels_plant_naming_no_control_is_a_contradiction(monkeypatch):
    """The generator reads every parcel's plants, as the controls' run does, not P0's alone (P0.1)."""
    every = dict(gen.C.plants(), **{"zz-not-a-control": None})
    monkeypatch.setattr(gen.C, "plants", lambda: every)
    assert gen.problems() == ["plant zz-not-a-control names no control"]


def test_a_control_naming_no_refusal_or_no_outcome_is_a_contradiction(monkeypatch):
    """Round 3, note 12: two of the generator's own sanity messages had no test."""
    bad = (gen.C.Control("zz-a", "a fault", "refused", "zz-no-such-refusal", "P0", "x"),
           gen.C.Control("zz-b", "a fault", "kept", None, "P0", "x"))
    monkeypatch.setattr(gen.C, "CONTROLS", gen.C.CONTROLS + bad)
    monkeypatch.setattr(gen.C, "CONTROL", dict(gen.C.CONTROL, **{c.name: c for c in bad}))
    assert gen.problems() == ["control zz-a: zz-no-such-refusal is not a refusal", "control zz-b: expected kept"]


def test_a_name_planted_twice_is_a_contradiction_not_a_crash(monkeypatch):
    """P0.1's verifier, round 2, note 4.3.5: it was a traceback, exit 1, where a contradiction is exit 2. The clash
    is the registry's own, raised by its merge."""
    from types import SimpleNamespace
    twice = SimpleNamespace(__name__="controls.plants_zz", PLANTS={"shot-moved": None})
    monkeypatch.setattr(gen.C, "plants", lambda: gen.C.merged(gen.C.PLANTS, [twice]))
    assert gen.problems() == ["controls.plants_zz plants ['shot-moved'], which another module already plants"]
    assert gen.main(["--check"]) == 2


@pytest.mark.parametrize("error", [RuntimeError, ImportError, SyntaxError, OSError, ValueError])
def test_any_other_failure_of_the_plants_is_the_generators_own_in_one_escaped_line(monkeypatch, capsys, error):
    """P0.2's verifier, round 1, D1: problems() took any RuntimeError out of the plants for a contradiction, exit 2,
    and the generator's line was not escaped. Only the registry's clash is a contradiction, whatever else a plants
    module raises (round 2: a bad import is the likeliest)."""
    def failing():
        raise error("fixture file missing" + chr(10) + "REFUSED forged at x: y")
    monkeypatch.setattr(gen.C, "plants", failing)
    assert gen.main(["--check"]) == 3
    assert capsys.readouterr() == ("", "FAILED: the generator itself failed, " + error.__name__ + ": fixture file "
                                   "missing" + chr(92) + "nREFUSED forged at x: y; this is not a verdict" + chr(10))


def test_each_contradiction_is_one_escaped_line(monkeypatch, capsys):
    """P0.2's verifier, round 2: a plant's name holding a line feed wrote a second line, free to begin REFUSED."""
    monkeypatch.setattr(gen.C, "plants", lambda: {"zz" + chr(10) + "REFUSED forged": None})
    assert gen.main(["--check"]) == 2
    assert capsys.readouterr().err == ("the definitions contradict themselves:" + chr(10) + "  plant zz" + chr(92)
                                       + "nREFUSED forged names no control" + chr(10))


def test_the_generators_failure_while_writing_names_the_files_it_wrote(tmp_path):
    """P0.2's verifier, round 1, D1: with docs/CONTROLS.md not writable, --write wrote three files and then said
    "nothing was checked". Here CONTROLS.md is a directory, which no write replaces on any host; and the generator
    runs as a process in a copy, its two streams in one, as the runner logs a stage. Its line names what it wrote
    itself, so it is true where its stdout is gone (round 2)."""
    import os
    for pkg in ("qro", "controls", "tools"):
        shutil.copytree(ROOT / pkg, tmp_path / pkg, ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / "docs" / "CONTROLS.md").mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    r = subprocess.run([sys.executable, "tools/gen_vocabulary.py", "--write"], cwd=tmp_path, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    *wrote, last = r.stdout.splitlines()
    before = list(gen.OUTPUTS)[:list(gen.OUTPUTS).index("docs/CONTROLS.md")]
    assert r.returncode == 3 and wrote == [f"wrote {rel}" for rel in before], r.stdout
    assert last.startswith("FAILED: the generator itself failed, ") and last.endswith(
        "; it had finished writing " + ", ".join(before)), last
    assert all((tmp_path / rel).is_file() for rel in before)


def test_write_renders_every_file_before_it_writes_any(tmp_path, monkeypatch, capsys):
    """P0.2: a definition that fails to render leaves every file as it was."""
    def broken():
        raise ValueError("a render that fails")
    monkeypatch.setitem(gen.OUTPUTS, "docs/CONTROLS.md", broken)
    assert gen.main(["--write"], tmp_path) == 3 and not list(tmp_path.iterdir())
    assert capsys.readouterr().out == ""


def test_the_vocabularys_contradiction_exits_2_and_writes_nothing(tmp_path, monkeypatch, capsys):
    """P0.1's verifier, round 1, 4.2: the exit on a contradiction was printed, and held by no test."""
    monkeypatch.setattr(gen, "problems", lambda: ["a planted contradiction"])
    assert gen.main(["--write"], tmp_path) == 2 and gen.main(["--check"], tmp_path) == 2
    assert "a planted contradiction" in capsys.readouterr().err and not list(tmp_path.iterdir())


def test_the_vocabularys_write_renders_what_its_check_holds(tmp_path):
    """Round 6, 8.1 item 16: --write had no test."""
    assert gen.main(["--write"], tmp_path) == 0
    assert gen.drift(tmp_path) == []
    for rel in gen.OUTPUTS:
        assert (tmp_path / rel).read_bytes() == (ROOT / rel).read_bytes(), rel
