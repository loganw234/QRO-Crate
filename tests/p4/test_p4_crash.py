"""A crash of tools/gen_profile.py is never exit 1, which is the drift verdict's code and Python's for an uncaught exception (the
fourth verifier's `python -OO` finding, MEASURED, and the lead's ruling of 2026-10-26T18:56:48Z): python -OO strips the docstring
the argument parser took its description from, and the tool died with a traceback and exit 1. Anything that goes wrong as the tool
starts (a module it imports will not import), before the work, or in it (an exit or an interrupt raised among the rest) is exit
3 and one escaped line; the arguments' own exits, 2 and --help's 0, are argparse's and stay; and where a stream is closed the exit
code still carries the verdict, and a failure to say a failure is no crash."""
import argparse
import sys

import pytest
from p4_helpers import ROOT, load_tool, run_patched, run_tool, tree
from qro import p4_profile as P

gen = load_tool()
RENDERED = P.render()


def test_python_dash_OO_runs_the_tool_in_both_modes_and_the_help(tmp_path):
    """The docstring is gone under -OO (and so are the asserts): the tool needs neither to do its work."""
    root = tree(tmp_path / "t")
    done = run_tool(["--check"], tmp_path, root, opts=["-OO"])
    assert done.returncode == 0 and done.stderr == "" and len(done.stdout.splitlines()) == len(RENDERED), done.stderr[-300:]
    (root / "profile" / "README.md").unlink()
    done = run_tool(["--write"], tmp_path, root, opts=["-OO"])
    assert done.returncode == 0 and "wrote README.md" in done.stdout.splitlines(), done.stderr[-300:]
    assert run_tool(["--check"], tmp_path, root).returncode == 0
    done = run_tool(["--help"], tmp_path, root, opts=["-OO"])
    assert done.returncode == 0 and done.stdout.startswith("usage:")


def test_the_help_says_what_the_tool_is_and_exits_0(tmp_path):
    done = run_tool(["--help"], tmp_path, tree(tmp_path / "t"))
    assert done.returncode == 0 and done.stdout.startswith("usage:") and "Generate the profile directory's files" in done.stdout


def test_a_crash_before_the_work_is_exit_3_one_escaped_line_and_never_the_exit_1_of_an_uncaught_exception(capsys, monkeypatch):
    def parser(*args, **kwargs):
        raise RuntimeError("no parser" + chr(10) + chr(0x2603))
    monkeypatch.setattr(argparse, "ArgumentParser", parser)
    assert gen.main(["--check"]) == 3
    said = capsys.readouterr()
    assert said.out == "" and said.err.isascii() and said.err.count("\n") == 1
    assert said.err == "FAILED: the generator itself failed, RuntimeError: no parser" + chr(92) + "n" + chr(92) + "u2603; this is not a verdict\n"


@pytest.mark.parametrize("raised", [SystemExit(1), SystemExit(0), KeyboardInterrupt()], ids=["exit 1", "exit 0", "interrupt"])
def test_an_exit_or_an_interrupt_raised_in_the_work_is_exit_3_and_not_the_exit_it_asks_for(capsys, monkeypatch, raised):
    def render(root=None):
        raise raised
    monkeypatch.setattr(P, "render", render)
    for mode in ("--check", "--write"):
        assert gen.main([mode]) == 3
        err = capsys.readouterr().err
        assert err.count("\n") == 1 and err.startswith(f"FAILED: the generator itself failed, {type(raised).__name__}")


def test_the_arguments_own_exits_stay_argparses_2_for_misuse_and_0_for_help(capsys):
    for argv, code in (([], 2), (["--check", "--write"], 2), (["--nonesuch"], 2), (["--help"], 0)):
        with pytest.raises(SystemExit) as stop:
            gen.main(argv)
        assert stop.value.code == code, argv
    assert capsys.readouterr().out.startswith("usage:")


@pytest.mark.parametrize("breaks, line", [
    (b"\ndef (:\n", "SyntaxError"),
    (b"\nraise RuntimeError('will not import ' + chr(10) + chr(0x2603))\n",
     "RuntimeError: will not import " + chr(92) + "n" + chr(92) + "u2603"),
], ids=["a syntax error", "an error raised at import, whose text has a line feed in it"])
def test_as_a_process_a_module_the_tool_imports_that_will_not_import_is_exit_3_and_not_pythons_1(tmp_path, breaks, line):
    root = tree(tmp_path / "t")
    module = root / "qro" / "p4_profile.py"
    module.write_bytes(module.read_bytes() + breaks)
    done = run_tool(["--check"], tmp_path, root)
    assert done.returncode == 3 and done.stdout == "" and done.stderr.count("\n") == 1 and done.stderr.isascii(), done.stderr[-300:]
    assert done.stderr.startswith("FAILED: the generator itself failed, " + line) and done.stderr.endswith("; this is not a verdict\n")


def test_as_a_process_a_tree_with_no_package_is_exit_3_and_not_pythons_1(tmp_path):
    """Python's own failure to start the tool used to be exit 1 (a stated limit of the checker's command line too)."""
    root = tmp_path / "t"
    (root / "tools").mkdir(parents=True)
    (root / "tools" / "gen_profile.py").write_bytes((ROOT / "tools" / "gen_profile.py").read_bytes())
    done = run_tool(["--check"], tmp_path, root)
    assert done.returncode == 3 and done.stdout == "" and done.stderr.count("\n") == 1, done.stderr[-300:]
    assert done.stderr.startswith("FAILED: the generator itself failed, ModuleNotFoundError: No module named 'qro'")


def test_a_failure_to_say_a_failure_is_no_crash_the_exit_code_still_says_it(monkeypatch):
    class Refusing:
        def write(self, text):
            raise OSError("the pipe is gone")
    for stream in (None, Refusing()):
        monkeypatch.setattr(sys, "stderr", stream)
        assert gen.failed(RuntimeError("x"), False, []) == 3
        assert gen.failed(RuntimeError("x"), True, ["wrote a"]) == 3


def test_a_mute_stream_takes_whatever_is_written_and_keeps_none():
    mute = gen.Mute()
    assert mute.write("abc") == 3 and mute.flush() is None
    print("x", "y", file=mute, flush=True)


def test_as_a_process_with_no_stderr_a_drift_is_still_exit_1_and_a_clean_tree_exit_0(tmp_path):
    """The verdict is the exit code where there is nowhere to say it: a stream that is None (a closed descriptor, pythonw) is
    replaced by a mute one in the tool's own __main__, so that writing to it is no crash."""
    root = tree(tmp_path / "t")
    done = run_patched(root, ["--check"], "sys.stderr = None", tmp_path)
    assert done.returncode == 0 and done.stderr == "", done.stderr[-300:]
    (root / "profile" / "README.md").unlink()
    done = run_patched(root, ["--check"], "sys.stderr = None", tmp_path)
    assert done.returncode == 1 and done.stderr == "" and "profile/README.md is exactly what its definition renders" not in done.stdout
    done = run_patched(root, ["--check"], "sys.stderr = None\nsys.stdout = None", tmp_path)
    assert done.returncode == 1 and done.stdout == "" and done.stderr == ""
    done = run_patched(root, ["--write"], "sys.stderr = None\nsys.stdout = None", tmp_path)
    assert done.returncode == 0 and (root / "profile" / "README.md").is_file()


def test_as_a_process_a_stream_with_no_reconfigure_is_left_as_it_is_and_the_tool_runs(tmp_path):
    """A StringIO is a stream with no `reconfigure`: the tool, asked to tell its streams how to write a name they cannot, leaves it
    (the verdict is the exit code, as the stream is nowhere)."""
    root = tree(tmp_path / "t")
    done = run_patched(root, ["--check"], "import io\nsys.stdout = io.StringIO()\nsys.stderr = io.StringIO()", tmp_path)
    assert done.returncode == 0 and done.stdout == "" and done.stderr == "", done.stderr[-300:]
    (root / "profile" / "README.md").unlink()
    done = run_patched(root, ["--check"], "import io\nsys.stdout = io.StringIO()\nsys.stderr = io.StringIO()", tmp_path)
    assert done.returncode == 1 and done.stdout == "" and done.stderr == ""


def test_as_a_process_a_crash_with_no_stderr_is_exit_3_and_not_exit_1(tmp_path):
    root = tree(tmp_path / "t")
    prelude = (f"sys.path.insert(0, {str(root)!r})\n"
               "import qro.p4_profile as pp\n"
               "def render(root=None):\n"
               "    raise RuntimeError('boom')\n"
               "pp.render = render\n"
               "sys.stderr = None")
    done = run_patched(root, ["--check"], prelude, tmp_path)
    assert done.returncode == 3 and done.stdout == "" and done.stderr == "", done.stderr[-300:]
