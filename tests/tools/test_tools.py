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
    global configuration and no system's (P0.1's verifier, rounds 1 and 2, notes 4.2 and 4.1.8)."""
    import os
    for k in [k for k in os.environ if k.upper().startswith("GIT_")]:
        monkeypatch.delenv(k)
    empty = tmp_path_factory.mktemp("git") / "gitconfig-empty"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


def hermetic_git(tmp_path):
    """The environment for a git, or a gate, this file starts: the process's own, which no_git_of_the_users has
    emptied of the user's git."""
    import os
    return dict(os.environ)


def test_the_tests_git_is_none_of_the_users():
    import os
    assert os.environ["GIT_CONFIG_NOSYSTEM"] == "1" and Path(os.environ["GIT_CONFIG_GLOBAL"]).read_text() == ""
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
    assert [b for b in bad if b.startswith("commit ")], bad
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
    """P0.1's verifier, round 2, note 4.3.5: it was a traceback, exit 1, where a contradiction is exit 2."""
    def twice():
        raise RuntimeError("controls.plants_zz plants ['shot-moved'], which another module already plants")
    monkeypatch.setattr(gen.C, "plants", twice)
    assert gen.problems() == ["controls.plants_zz plants ['shot-moved'], which another module already plants"]
    assert gen.main(["--check"]) == 2


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
