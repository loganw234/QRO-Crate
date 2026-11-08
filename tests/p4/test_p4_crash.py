"""A crash of tools/gen_profile.py is never exit 1, which is the drift verdict's code and Python's for an uncaught exception (the
fourth verifier's `python -OO` finding, MEASURED, and the lead's ruling of 2026-10-26T18:56:48Z): python -OO strips the docstring
the argument parser took its description from, and the tool died with a traceback and exit 1. Anything that goes wrong as the tool
starts (a module it imports will not import), before the work, or in it (an exit or an interrupt raised among the rest) is exit
3 and one escaped line; the arguments' own exits, 2 and --help's 0, are argparse's and stay; and where a stream is closed the exit
code still carries the verdict, and a failure to say a failure is no crash."""
import argparse
import ast
import sys
import textwrap

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


@pytest.mark.parametrize("opts", [(), ("-OO",)], ids=["python", "python -OO"])
def test_the_help_says_what_the_tool_is_what_each_mode_does_and_every_exit_and_exits_0(tmp_path, opts):
    """The fifth verifier's note: --help printed a cut sentence as the description ('... (P4's design, items 1 and 8;') and no
    help for --write and --check, and the ruling of P4.2 (C2) puts the exit-1 list in --help. The description, the two modes' help
    and the exits are constants of the tool and not its docstring, which python -OO strips: --help says all of it under -OO too,
    and the exit-1 sentence is the page's and the docstring's, word for word."""
    done = run_tool(["--help"], tmp_path, tree(tmp_path / "t"), opts=opts)
    assert done.returncode == 0 and done.stdout.startswith("usage:") and done.stderr == ""
    text = " ".join(done.stdout.split())
    assert "Generate the profile directory's files from the vocabulary table, and refuse drift." in text
    assert "(P4's design" not in text and not text.rstrip().endswith(";")                        # the cut sentence
    assert "--write regenerate every file under profile/ that the definitions render, and remove what they do not" in text
    assert "--check fail if a file under profile/ is not exactly what the definitions render" in text
    assert "exit codes: 0 every file is exactly what the definitions render" in text
    assert " ".join(gen.EXIT_ONE.split()) in text and "1 drift, a file missing or unexpected" in text
    assert "2 the definitions contradict themselves, or the arguments are wrong" in text
    assert "3 the generator itself failed, in one escaped line on stderr (never a verdict): a removal or a write that fails, a " \
           "directory the host cannot list, or a file it cannot read other than P0's context (a rendered file, a stray, the " \
           "fixture's)" in text
    assert "so is any other file" not in text                  # the sentence that did not parse (P4.2's first verifier, note 6)


def test_exit_3_names_a_directory_the_host_cannot_list_in_help_the_docstring_and_the_page(tmp_path):
    """P4.2's second verifier, note 4: the exit-3 sentence of --help named the files the tool cannot read and not the directory
    the host cannot list, which the docstring states (the tool raises it, exit 3, and names it). The three texts say it now."""
    done = run_tool(["--help"], tmp_path, tree(tmp_path / "t"))
    assert done.returncode == 0
    exit3 = " ".join(done.stdout.split()).partition(" 3 the generator itself failed")[2]
    assert exit3 and "a directory the host cannot list" in exit3
    doc = " ".join(ast.get_docstring(ast.parse((ROOT / "tools" / "gen_profile.py").read_text(encoding="utf-8"))).split())
    page = " ".join((ROOT / "docs" / "P4.md").read_text(encoding="utf-8").replace("`", "").split())
    for text in (doc, page):
        assert "So is a directory the host cannot list, which the tool names" in text, text[:80]


def help_lines(tmp_path, opts, columns):
    """The lines --help prints, run as a process in a terminal `columns` wide (argparse takes its width from COLUMNS)."""
    done = run_tool(["--help"], tmp_path, tree(tmp_path / "t"), opts=opts, env={"COLUMNS": str(columns)})
    assert done.returncode == 0 and done.stderr == ""
    return done.stdout.split("\n")


def layout_problems(lines, description, width=100):
    """What is wrong with the layout of a --help text (P4.2's first verifier, note 3: mutants B01 and B04 survived). The usage
    first; the description whole, on one line of its own, between blank lines, before the options; then the exits last, after a
    blank line and a line `exit codes:`; each exit beginning on a line of its own, `  N  `, in order; the rest of an exit
    indented five and filled to `width` as textwrap fills it (no line longer, and none that the next word would have fitted)."""
    found = []
    if not lines or not lines[0].startswith("usage:"):
        return ["the text does not begin with the usage"]
    if lines.count(description) != 1:
        return [f"the description is not whole on one line of its own: {description!r}"]
    d = lines.index(description)
    if lines[d - 1] != "" or lines[d + 1] != "" or lines[d + 2] != "options:":
        found.append("the description is not between blank lines, before the options")
    if lines.count("exit codes:") != 1:
        return found + ["there is not one line `exit codes:`"]
    e = lines.index("exit codes:")
    if e < d or lines[e - 1] != "" or lines[-1] != "":
        found.append("the exits are not last, after a blank line")
    if any(ln[:2] == "  " and ln[2:3].isdigit() and ln[3:5] == "  " for ln in lines[:e]):
        found.append("an exit is printed before the heading of the exits")
    exits = lines[e + 1:-1]
    starts = [i for i, ln in enumerate(exits) if ln[:2] == "  " and ln[2:3].isdigit() and ln[3:5] == "  "]
    if [exits[i][2] for i in starts] != ["0", "1", "2", "3"] or starts[0] != 0:
        found.append(f"the exits do not each begin on a line of their own, in order: {[exits[i][:6] for i in starts]}")
    for n, ln in enumerate(exits):
        if len(ln) > width:
            found.append(f"a line of {len(ln)} characters: {ln[:30]!r}")
        if n not in starts and not (ln.startswith("     ") and ln[5:6] not in ("", " ")):
            found.append(f"a continuation not indented five: {ln[:30]!r}")
        after = exits[n + 1] if n + 1 < len(exits) else None
        if after is not None and n + 1 not in starts and len(ln) + 1 + len(after.split()[0]) <= width:
            found.append(f"a line the next word would have fitted: {ln[:30]!r}")
    return found


@pytest.mark.parametrize("opts", [(), ("-OO",)], ids=["python", "python -OO"])
@pytest.mark.parametrize("columns", [40, 200])
def test_the_help_prints_the_description_whole_and_the_exits_each_on_a_line_of_its_own_in_a_terminal_of_any_width(tmp_path, opts, columns):
    """P4.2's first verifier, note 3 (its mutants B01 and B04, which this kills): the layout of --help is held. The formatter is
    argparse's raw one, so a narrow terminal re-wraps neither the description nor the exits, which are filled to 100 characters by
    the tool itself and not to the terminal."""
    lines = help_lines(tmp_path, opts, columns)
    assert layout_problems(lines, gen.DESCRIPTION) == []
    assert "\n".join(lines[lines.index("exit codes:"):]) == gen.EXITS         # and the exits are the constant, byte for byte


def test_the_layout_check_fails_the_layouts_it_is_for(tmp_path):
    """The check watched failing, on the help of a tool whose parser has the mutants of P4.2's first verifier: B01 (the default
    formatter, which folds the exits and the description into the terminal's width) and B04 (the exits filled at 20), and a
    description cut, an exit that shares a line, and an exit list that is not last."""
    good = help_lines(tmp_path, (), 40)
    assert layout_problems(good, gen.DESCRIPTION) == []
    default = argparse.ArgumentParser(description=gen.DESCRIPTION, epilog=gen.EXITS)
    default.add_argument("--write", action="store_true", help=gen.HELP_WRITE)
    b01 = default.format_help().split("\n")
    assert layout_problems(b01, gen.DESCRIPTION) != []
    narrow = "\n".join(good).replace("  1  drift, a file missing", "  1  drift,\n     a file missing").split("\n")
    assert layout_problems(narrow, gen.DESCRIPTION) != []
    b04 = good[:good.index("exit codes:") + 1]
    for code, text in (("0", "every file is exactly what the definitions render, and the Profile Crate holds the rules its check lists"),
                       ("1", gen.EXIT_ONE), ("2", "the definitions contradict themselves, or the arguments are wrong"),
                       ("3", "the generator itself failed")):
        b04 += textwrap.fill(f"{code}  {text}", width=20, initial_indent="  ", subsequent_indent="     ", break_on_hyphens=False,
                             break_long_words=False).split("\n")
    assert layout_problems(b04 + [""], gen.DESCRIPTION) != []
    assert layout_problems([ln.replace("Generate the profile", "Generate the") for ln in good], gen.DESCRIPTION) != []
    joined = good[:good.index("exit codes:")] + ["exit codes: " + " ".join(ln.strip() for ln in good[good.index("exit codes:") + 1:])]
    assert layout_problems(joined + [""], gen.DESCRIPTION) != []
    reordered = [ln for ln in good if ln != "exit codes:"]
    assert layout_problems(reordered, gen.DESCRIPTION) != []
    twice = [good[0], good[good.index("exit codes:") + 1]] + good[1:]                      # an exit printed before the heading
    assert layout_problems(twice, gen.DESCRIPTION) != []


def test_the_exit_1_sentence_is_the_same_in_help_the_docstring_and_the_page_and_names_p0s_context_missing_or_unreadable():
    """The fifth verifier's C2, ruled: the exit-1 list, on the page and in --help, names profile/context.jsonld missing or
    unreadable, a tree the tool refuses since P0's generator makes that file; another file it cannot read stays exit 3, the tool
    failing. The sentence is a constant of the tool, and the docstring and the page hold it word for word."""
    assert gen.EXIT_ONE.endswith("or P0's profile/context.jsonld missing or unreadable (a tree the tool refuses, since "
                                 "tools/gen_vocabulary.py makes that file)")
    doc = " ".join(ast.get_docstring(ast.parse((ROOT / "tools" / "gen_profile.py").read_text(encoding="utf-8"))).split())
    page = " ".join((ROOT / "docs" / "P4.md").read_text(encoding="utf-8").replace("`", "").split())
    for text in (doc, page):
        assert " ".join(gen.EXIT_ONE.split()) in text
        assert "Any other file it cannot read (a rendered file, a stray, the fixture's) is this exit too: the tool failing, where an " \
               "unreadable context is a tree refused." in text


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
