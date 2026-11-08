"""tools/gen_vocabulary.py as a process under python -OO, each of its modes (P0.9; P4's fourth verifier, a note, and
the lead's ruling on it). -OO strips the module's docstring, and the tool read it outside its try for its --help
text, so every mode died with a traceback and exit 1, the drift verdict's code. A crash is exit 3, never 1.

Each test runs a copy of what the tool reads and writes, so that --write writes no file of the checkout. P0's other
tools (check_docs, check_instruments, check_privacy) and the controls' two commands read no docstring, and give the
same verdicts under -OO as without it (READ and MEASURED, P0.9), so only this tool has a test here."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ("profile/context.jsonld", "docs/VOCABULARY.md", "docs/REFUSALS.md", "docs/CONTROLS.md")
FLAGS = [(), ("-OO",)]
FLAG_IDS = ["without -OO", "-OO"]
CRASH = "a plants module that fails as it loads"


def tool_tree(tmp_path, outputs=True, crash=False):
    """A copy of the tool and of what it imports, with the four files it generates unless `outputs` is False."""
    t = tmp_path / "tree"
    for d in ("qro", "controls"):
        shutil.copytree(ROOT / d, t / d, ignore=shutil.ignore_patterns("__pycache__"))
    (t / "tools").mkdir()
    shutil.copy2(ROOT / "tools" / "gen_vocabulary.py", t / "tools" / "gen_vocabulary.py")
    if outputs:
        for rel in OUTPUTS:
            (t / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, t / rel)
    if crash:
        (t / "controls" / "plants_zz.py").write_text(f"raise RuntimeError({CRASH!r})\n", encoding="ascii")
    return t


def run(tree, flags, *args):
    """The tool as a process, isolated (-I) so that nothing but the copy is imported, writing no bytecode."""
    return subprocess.run([sys.executable, "-B", "-I", *flags, str(tree / "tools" / "gen_vocabulary.py"), *args],
                          capture_output=True, text=True, cwd=tree)


@pytest.mark.parametrize("flags", FLAGS, ids=FLAG_IDS)
def test_help_prints_the_usage_and_exits_0(tmp_path, flags):
    """Under -OO there is no description to print, and the usage is printed all the same."""
    p = run(tool_tree(tmp_path), flags, "--help")
    assert (p.returncode, p.stderr) == (0, ""), p.stderr[-400:]
    assert p.stdout.startswith("usage: gen_vocabulary.py"), p.stdout[:200]
    assert ("Generate the profile's context" in p.stdout) is (flags == ()), p.stdout


@pytest.mark.parametrize("flags", FLAGS, ids=FLAG_IDS)
def test_check_holds_the_committed_files_and_exits_0(tmp_path, flags):
    p = run(tool_tree(tmp_path), flags, "--check")
    assert (p.returncode, p.stderr) == (0, ""), p.stderr[-400:]
    assert p.stdout.splitlines() == [f"{rel} is exactly what its definition renders" for rel in OUTPUTS]


@pytest.mark.parametrize("flags", FLAGS, ids=FLAG_IDS)
def test_check_exits_1_on_drift_and_names_the_file(tmp_path, flags):
    """Exit 1 is the drift verdict, and under -OO it is only that."""
    t = tool_tree(tmp_path)
    with open(t / "docs" / "REFUSALS.md", "ab") as f:
        f.write(b"a line the definition does not render\n")
    p = run(t, flags, "--check")
    assert p.returncode == 1 and "docs/REFUSALS.md DRIFTED from its definition" in p.stderr, p.stderr[-400:]
    assert "Traceback" not in p.stderr


@pytest.mark.parametrize("flags", FLAGS, ids=FLAG_IDS)
def test_write_writes_exactly_the_committed_bytes(tmp_path, flags):
    t = tool_tree(tmp_path, outputs=False)
    p = run(t, flags, "--write")
    assert (p.returncode, p.stderr) == (0, ""), p.stderr[-400:]
    assert p.stdout.splitlines() == [f"wrote {rel}" for rel in OUTPUTS]
    for rel in OUTPUTS:
        assert (t / rel).read_bytes() == (ROOT / rel).read_bytes(), rel


@pytest.mark.parametrize("flags", FLAGS, ids=FLAG_IDS)
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_a_crash_is_exit_3_never_1(tmp_path, flags, mode):
    """A plants module that fails as it loads is the generator's own failure: one escaped line on stderr, nothing
    on stdout, exit 3, and after --write, no file written. Under -OO the tool died before it reached this, exit 1."""
    t = tool_tree(tmp_path, outputs=mode == "--check", crash=True)
    p = run(t, flags, mode)
    tail = "this is not a verdict" if mode == "--check" else "it had finished writing no file"
    assert (p.returncode, p.stdout) == (3, ""), p.stderr[-400:]
    assert p.stderr == f"FAILED: the generator itself failed, RuntimeError: {CRASH}; {tail}\n", p.stderr
    if mode == "--write":
        assert not any((t / rel).exists() for rel in OUTPUTS)


@pytest.mark.parametrize("flags", FLAGS, ids=FLAG_IDS)
@pytest.mark.parametrize("args", [[], ["--check", "--write"], ["--nonesuch"]],
                         ids=["no mode", "both modes", "no such mode"])
def test_wrong_arguments_are_exit_2(tmp_path, flags, args):
    p = run(tool_tree(tmp_path), flags, *args)
    assert (p.returncode, p.stdout) == (2, ""), p.stderr[-400:]
    assert p.stderr.startswith("usage: gen_vocabulary.py") and "Traceback" not in p.stderr, p.stderr[-400:]
