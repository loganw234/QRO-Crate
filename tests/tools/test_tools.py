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


def test_the_privacy_gate_finds_nothing_in_text_without_a_plant():
    text = ("moth_quantum_files_read, /docs/studies/qro0/, noreply@anthropic.com, user@example.org, "
            "C:\\Users\\<name>\\x, /home/{user}/x, /c/Users/$USER/x, C:\\Users\\%USERNAME%\\x")
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
        assert "commit messages: unread, as git log failed" in privacy.check(r)[0], name
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
