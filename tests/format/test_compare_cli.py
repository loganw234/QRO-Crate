"""`python -m qro compare COMPARISON_DIR CRATE_DIR [CRATE_DIR ...]` (P0.10; P3's design, item 7; FORMAT.md item 23).
What it holds, in process and as the process a user runs:
  - the misuse that is P0's, exit 2: fewer than two arguments, each directory held to `check`'s rules (a path that is
    not there, of the wrong kind, an empty name, a name the host reads as another, a directory it will not list), a
    crate directory named twice however it is spelt, and each line beginning with the argument it is about;
  - where `qro.p3_compare` is not there: the comparison refused `step-unbuilt` at "comparison", exit 1, one line, and
    never exit 0 and never a crash. The absence is made in the test (a copy of the packages without the module, and
    in process a find_spec that does not find it), so the test holds after P3's module lands;
  - the dispatch to a stand-in module of the contract's shape, put in place only inside the test: the arguments as
    given and in order, an ACCEPTED line written with exit 0, a Refused as exit 1, the module's own `Misuse` as
    exit 2, and a module that breaks its contract (any other exception, a summary that is no ACCEPTED line, no
    `check`) as the checker failing, exit 3;
  - the line written whole to the descriptor, and a closed pipe exiting 3, never 120."""
import importlib
import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import types

import pytest

from qro import __main__ as cli
from qro.__main__ import COMPARE, USAGE, escape, main

ROOT = pathlib.Path(__file__).resolve().parents[2]
ACCEPTED = "ACCEPTED comparison "


def run(tmp_path, argv, out=None):
    """main() in process, its two descriptors files: (exit code, stdout's bytes, stderr's bytes)."""
    paths = [tmp_path / "out.bin", tmp_path / "err.bin"]
    fds = [os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_BINARY", 0)) for p in paths]
    try:
        code = main(argv, out=fds[0] if out is None else out, err=fds[1])
    finally:
        for fd in fds:
            os.close(fd)
    return code, paths[0].read_bytes(), paths[1].read_bytes()


def dirs(tmp_path, *names):
    out = []
    for n in names:
        (tmp_path / n).mkdir()
        out.append(str(tmp_path / n))
    return out


@pytest.fixture
def no_p3(monkeypatch):
    """qro.p3_compare is not there, whatever the tree holds: not loaded, and find_spec does not find it."""
    monkeypatch.delitem(sys.modules, COMPARE, raising=False)
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda name, *a: None if name == COMPARE else real(name, *a))


class Summary:
    def __init__(self, line):
        self.line = line

    def __str__(self):
        return self.line


def stand_in(monkeypatch, check=None):
    """A module of the contract's shape (a `check`, a Summary whose str() is the ACCEPTED line, a `Misuse`), in
    sys.modules only for this test. `check` defaults to one that accepts and says what it was given."""
    class Misuse(Exception):
        pass

    def accepting(comparison_dir, crate_dirs):
        names = [os.path.basename(comparison_dir)] + [os.path.basename(c) for c in crate_dirs]
        return Summary(ACCEPTED + "|".join(names))
    module = types.ModuleType(COMPARE)
    module.Misuse = Misuse
    if check is not False:
        module.check = check or accepting
    monkeypatch.setitem(sys.modules, COMPARE, module)
    return module


# -- misuse, P0's -----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("argv", [["compare"], ["compare", "a"]], ids=["no argument", "no crate"])
def test_fewer_than_two_arguments_is_misuse_with_the_usage(tmp_path, argv):
    assert run(tmp_path, argv) == (2, b"", USAGE.encode() + b"\n")


def test_the_usage_lists_the_three_commands():
    assert "check" in USAGE and "custody" in USAGE and "compare COMPARISON_DIR CRATE_DIR [CRATE_DIR ...]" in USAGE


def test_a_comparison_or_crate_that_is_no_directory_is_misuse_naming_it(tmp_path):
    c, x = dirs(tmp_path, "c", "x")
    (tmp_path / "file").write_bytes(b"x")
    missing, afile = str(tmp_path / "nothing"), str(tmp_path / "file")
    for argv, what, arg in ((["compare", missing, x], "comparison", missing), (["compare", afile, x], "comparison", afile),
                            (["compare", c, missing], "crate", missing), (["compare", c, x, afile], "crate", afile),
                            (["compare", "", x], "comparison", ""), (["compare", c, ""], "crate", "")):
        code, out, err = run(tmp_path, argv)
        assert (code, out) == (2, b""), argv
        assert err.decode("ascii") == f"{escape(arg)}: no such {what} directory; {USAGE}\n", (argv, err)


def test_the_first_argument_in_error_is_the_one_named(tmp_path):
    c = dirs(tmp_path, "c")[0]
    code, _, err = run(tmp_path, ["compare", str(tmp_path / "a"), c, str(tmp_path / "b")])
    assert code == 2 and err.decode("ascii").startswith(escape(str(tmp_path / "a")) + ": no such comparison")


@pytest.mark.parametrize("tail", [" ", ".", ".."])
def test_a_name_the_host_reads_as_another_is_misuse_for_every_directory(tmp_path, tail):
    c, x = dirs(tmp_path, "c", "x")
    for argv, bad in ((["compare", c + tail, x], c + tail), (["compare", c, x + tail], x + tail)):
        code, out, err = run(tmp_path, argv)
        assert (code, out) == (2, b""), argv
        assert err.decode("ascii").startswith(escape(bad) + ": "), err


def test_a_directory_the_user_may_not_list_is_misuse_for_every_directory(tmp_path, monkeypatch):
    c, x = dirs(tmp_path, "c", "x")
    real = cli.unlistable
    monkeypatch.setattr(cli, "unlistable", lambda p: "Permission denied" if p == x else real(p))
    code, out, err = run(tmp_path, ["compare", c, x])
    assert (code, out) == (2, b"")
    assert err.decode("ascii") == f"{escape(x)}: cannot be read here, Permission denied; {USAGE}\n"
    monkeypatch.setattr(cli, "unlistable", lambda p: "Permission denied" if p == c else real(p))
    assert run(tmp_path, ["compare", c, x])[2].decode("ascii").startswith(escape(c) + ": cannot be read here")


@pytest.mark.parametrize("spell", [lambda p, n: p, lambda p, n: str(pathlib.Path(p).parent / "." / n),
                                   lambda p, n: str(pathlib.Path(p).parent / "x" / ".." / n)],
                         ids=["as given", "through a dot", "through a parent"])
def test_a_crate_directory_given_twice_is_misuse_however_it_is_spelt(tmp_path, spell):
    c, x, y = dirs(tmp_path, "c", "x", "y")
    again = spell(x, "x")
    for argv in (["compare", c, x, again], ["compare", c, x, y, again], ["compare", c, again, y, x]):
        code, out, err = run(tmp_path, argv)
        assert (code, out) == (2, b""), argv
        assert err.decode("ascii").endswith(f": a crate directory given twice; {USAGE}\n"), err


def test_a_crate_directory_given_twice_is_misuse_before_the_comparison_is_asked(tmp_path, monkeypatch):
    c, x = dirs(tmp_path, "c", "x")
    asked = []
    stand_in(monkeypatch, lambda cd, crates: asked.append(crates) or Summary(ACCEPTED + "x"))
    assert run(tmp_path, ["compare", c, x, x])[0] == 2 and asked == []


def test_distinct_directories_are_not_a_duplicate_and_the_comparison_may_be_a_crate_too(tmp_path, monkeypatch):
    """Only crate directories are told apart; the comparison's own may equal one (the module decides that)."""
    c, x, y = dirs(tmp_path, "c", "x", "y")
    stand_in(monkeypatch)
    assert run(tmp_path, ["compare", c, x, y])[0] == 0
    assert run(tmp_path, ["compare", x, x, y])[0] == 0


# -- step-unbuilt, while P3's module is not there ---------------------------------------------------------------
def test_without_the_module_the_comparison_is_refused_step_unbuilt_in_process(tmp_path, no_p3):
    c, x, y = dirs(tmp_path, "c", "x", "y")
    code, out, err = run(tmp_path, ["compare", c, x, y])
    assert (code, err) == (1, b"")
    assert out == b"REFUSED step-unbuilt at comparison: the comparison check, qro.p3_compare, is not built yet\n"


def test_without_the_module_the_misuse_is_still_misuse(tmp_path, no_p3):
    assert run(tmp_path, ["compare", str(tmp_path / "nothing"), str(tmp_path)])[0] == 2
    c = dirs(tmp_path, "c")[0]
    assert run(tmp_path, ["compare", c, c, c])[0] == 2 and run(tmp_path, ["compare", c])[0] == 2


def copy_of_packages(tmp_path, module=None):
    """A copy of qro/ with no p3_compare.py, and `module` as its source where one is given: a tree the command runs
    from, so that the module's presence is the test's, never the tree's."""
    dest = tmp_path / "tree"
    shutil.copytree(ROOT / "qro", dest / "qro", ignore=shutil.ignore_patterns("__pycache__", "p3_compare.py"))
    if module is not None:
        (dest / "qro" / "p3_compare.py").write_bytes(module.encode("ascii"))
    return dest


def process(tree, argv, stdout=subprocess.PIPE):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONSAFEPATH", "PYTHONPATH")}
    env.update(PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, "-m", "qro", *argv], stdout=stdout, stderr=subprocess.PIPE, env=env, cwd=tree)


def test_without_the_module_the_process_refuses_step_unbuilt_exit_1_with_one_line(tmp_path):
    tree = copy_of_packages(tmp_path)
    c, x, y = dirs(tmp_path, "c", "x", "y")
    p = process(tree, ["compare", c, x, y])
    assert (p.returncode, p.stderr) == (1, b""), p.stderr[-300:]
    assert p.stdout.replace(b"\r\n", b"\n") == (
        b"REFUSED step-unbuilt at comparison: the comparison check, qro.p3_compare, is not built yet\n")


def test_the_process_refusing_into_a_pipe_nobody_reads_exits_3_and_never_120(tmp_path):
    tree = copy_of_packages(tmp_path)
    c, x = dirs(tmp_path, "c", "x")
    r, w = os.pipe()
    os.close(r)
    try:
        p = process(tree, ["compare", c, x], stdout=w)
    finally:
        os.close(w)
    assert p.returncode == 3, p.stderr[-300:]
    assert p.stderr.replace(b"\r\n", b"\n") == b"FAILED: the verdict could not be written; this is not a verdict\n"


def test_the_process_calls_a_comparison_misuse_misuse(tmp_path):
    tree = copy_of_packages(tmp_path)
    p = process(tree, ["compare", str(tmp_path / "nothing"), str(tmp_path)])
    assert (p.returncode, p.stdout) == (2, b"") and p.stderr.startswith(escape(str(tmp_path / "nothing")).encode())


# -- the dispatch, to a stand-in of the contract's shape ----------------------------------------------------------
def test_the_arguments_reach_the_module_as_given_and_in_order_and_its_line_is_written(tmp_path, monkeypatch):
    c, x, y = dirs(tmp_path, "c", "x", "y")
    seen = []

    def check(comparison_dir, crate_dirs):
        seen.append((comparison_dir, crate_dirs))
        return Summary(ACCEPTED + "deadbeef: declared real; pre-registered; 2 measures")
    stand_in(monkeypatch, check)
    code, out, err = run(tmp_path, ["compare", c, y, x])
    assert (code, err) == (0, b"") and out == f"{ACCEPTED}deadbeef: declared real; pre-registered; 2 measures\n".encode()
    assert seen == [(c, [y, x])] and isinstance(seen[0][1], list)


def test_the_parcels_steps_are_loaded_before_the_module_is_asked(tmp_path, monkeypatch):
    c, x = dirs(tmp_path, "c", "x")
    order = []
    monkeypatch.setattr(cli.checker, "load", lambda: order.append("load"))
    stand_in(monkeypatch, lambda cd, crates: order.append("check") or Summary(ACCEPTED + "x"))
    assert run(tmp_path, ["compare", c, x])[0] == 0 and order == ["load", "check"]


def test_a_refusal_the_module_raises_is_exit_1_with_its_one_line(tmp_path, monkeypatch):
    from qro.refusal import Refused
    c, x = dirs(tmp_path, "c", "x")

    def check(cd, crates):
        raise Refused("comparison-trivial", "crate 1: ./", "the two runs share a job of a measured role")
    stand_in(monkeypatch, check)
    code, out, err = run(tmp_path, ["compare", c, x])
    assert (code, err) == (1, b"")
    assert out == b"REFUSED comparison-trivial at crate 1: ./: the two runs share a job of a measured role\n"


def test_the_modules_own_misuse_is_exit_2_with_its_message_and_the_usage(tmp_path, monkeypatch):
    c, x = dirs(tmp_path, "c", "x")
    module = stand_in(monkeypatch, lambda cd, crates: (_ for _ in ()).throw(module.Misuse("the declaration names no crate")))
    code, out, err = run(tmp_path, ["compare", c, x])
    assert (code, out) == (2, b"")
    assert err.decode("ascii") == f"the declaration names no crate; {USAGE}\n"


def test_a_misuse_class_that_is_not_the_modules_is_the_checker_failing(tmp_path, monkeypatch):
    c, x = dirs(tmp_path, "c", "x")
    stand_in(monkeypatch, lambda cd, crates: (_ for _ in ()).throw(ValueError("a bug")))
    code, out, err = run(tmp_path, ["compare", c, x])
    assert (code, out) == (3, b"") and err.startswith(b"FAILED: the checker itself failed, ValueError: a bug")


@pytest.mark.parametrize("returned", ["nothing", "REFUSED x at y: z", "ACCEPTED crate abc", "", None, 0],
                         ids=["text", "a refusal's text", "another command's line", "empty", "None", "zero"])
def test_a_summary_that_is_no_accepted_line_is_never_an_acceptance(tmp_path, monkeypatch, returned):
    c, x = dirs(tmp_path, "c", "x")
    stand_in(monkeypatch, lambda cd, crates: returned)
    code, out, err = run(tmp_path, ["compare", c, x])
    assert (code, out) == (3, b"") and b"no ACCEPTED line" in err, err


def test_a_module_with_no_check_is_the_checker_failing_never_an_acceptance(tmp_path, monkeypatch):
    c, x = dirs(tmp_path, "c", "x")
    stand_in(monkeypatch, False)
    code, out, err = run(tmp_path, ["compare", c, x])
    assert (code, out) == (3, b"") and err.startswith(b"FAILED: the checker itself failed, AttributeError")


def test_a_module_that_will_not_import_is_the_checker_failing(tmp_path, no_p3, monkeypatch):
    c, x = dirs(tmp_path, "c", "x")
    monkeypatch.setattr(importlib.util, "find_spec", lambda name, *a: object() if name == COMPARE else None)

    def boom(name):
        raise SyntaxError("a module that will not import")
    monkeypatch.setattr(importlib, "import_module", lambda name, *a: boom(name) if name == COMPARE else None)
    code, out, err = run(tmp_path, ["compare", c, x])
    assert (code, out) == (3, b"") and err.startswith(b"FAILED: the checker itself failed, SyntaxError")


def test_the_accepted_line_is_escaped_and_cut_as_every_line_is(tmp_path, monkeypatch):
    c, x = dirs(tmp_path, "c", "x")
    stand_in(monkeypatch, lambda cd, crates: Summary(ACCEPTED + "a\nREFUSED forged at x: y" + "z" * 5000))
    code, out, _ = run(tmp_path, ["compare", c, x])
    assert code == 0 and out.count(b"\n") == 1 and b"\\nREFUSED forged" in out and b" more characters)" in out


STAND_IN_MODULE = """
import os
from qro.refusal import Refused


class Misuse(Exception):
    pass


class Summary:
    def __init__(self, line):
        self.line = line

    def __str__(self):
        return self.line


def check(comparison_dir, crate_dirs):
    mode = open(os.path.join(comparison_dir, "mode.txt")).read().strip()
    if mode == "refuse":
        raise Refused("comparison-trivial", "crate 1: ./", "the stand-in refuses")
    if mode == "misuse":
        raise Misuse("the stand-in is misused")
    if mode == "crash":
        raise RuntimeError("the stand-in crashed")
    return Summary("ACCEPTED comparison " + "|".join(os.path.basename(c) for c in crate_dirs))
"""


@pytest.mark.parametrize("mode, code, stream, says", [
    ("accept", 0, "out", "ACCEPTED comparison x|y\n"),
    ("refuse", 1, "out", "REFUSED comparison-trivial at crate 1: ./: the stand-in refuses\n"),
    ("misuse", 2, "err", "the stand-in is misused; " + USAGE + "\n"),
    ("crash", 3, "err", "FAILED: the checker itself failed, RuntimeError: the stand-in crashed; this is not a verdict\n")])
def test_the_process_dispatches_to_a_module_that_is_there(tmp_path, mode, code, stream, says):
    tree = copy_of_packages(tmp_path, STAND_IN_MODULE)
    c, x, y = dirs(tmp_path, "c", "x", "y")
    (tmp_path / "c" / "mode.txt").write_bytes(mode.encode("ascii"))
    p = process(tree, ["compare", c, x, y])
    got, other = (p.stdout, p.stderr) if stream == "out" else (p.stderr, p.stdout)
    assert (p.returncode, other) == (code, b""), (p.stdout, p.stderr)
    assert got.replace(b"\r\n", b"\n") == says.encode("ascii")


def runner_bash():
    """The bash the runner runs under (copied, as every test file here copies it: a bare `bash` can be WSL's on
    Windows, and a `tests` package in site-packages shadows a helper module under tests/)."""
    if os.name == "nt":
        git = shutil.which("git")
        assert git, "git is not on PATH"
        for up in pathlib.Path(git).resolve().parents:
            for rel in ("usr/bin/bash.exe", "bin/bash.exe"):
                if (up / rel).is_file():
                    return str(up / rel)
        raise AssertionError("no Git Bash beside git.exe")
    bash = shutil.which("bash")
    assert bash, "bash is not on PATH"
    return bash


@pytest.mark.parametrize("redirect", [">&-", ">&- 2>&-"], ids=["stdout closed", "both closed"])
def test_the_process_with_a_closed_descriptor_exits_3_and_never_120(tmp_path, redirect):
    """Through the runner's own bash, which closes the descriptor the line would go to (needs bash, so the runner runs
    it through sbx-mid.sh, as it does the same test of `check`)."""
    tree = copy_of_packages(tmp_path)
    c, x = dirs(tmp_path, "c", "x")
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONSAFEPATH", "PYTHONPATH")}
    py = sys.executable.replace("\\", "/")
    cd, c, x = (str(p).replace("\\", "/") for p in (tree, c, x))
    p = subprocess.run([runner_bash(), "-c", f'cd "{cd}" && "{py}" -m qro compare "{c}" "{x}" {redirect}; echo "rc=$?"'],
                       capture_output=True, env=env)
    assert p.stdout.strip().endswith(b"rc=3"), (p.stdout[-200:], p.stderr[-300:])
