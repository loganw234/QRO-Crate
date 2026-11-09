"""The comparison as the process a user runs (CLAUDE.md, "Test the command line as a process too"): `python -m qro
compare` (P0's command, dispatching to qro.p3_compare.check) and `python -m qro.p3_compare make`, on P1's twin T and
its re-identified copy T2 (controls/plants_p3.py), each verdict one line on its own stream with its exit: 0 and the
ACCEPTED (or MADE) line, 1 and one REFUSED line, 2 and the misuse with the usage, and 3, never 120, where the line
cannot be written, into a pipe nobody reads. The comparison's own directory given again as a crate directory is
misuse, as a process and in process (P0.10's verifier, its third note)."""
import json
import os
import shutil
import subprocess
import sys

import pytest

import p3_support as S
from controls import plants_p1, plants_p3
from qro import p3_compare, p3_record
from qro.__main__ import USAGE, main

ROOT = S.ROOT


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    """(the comparison of T against T2, made in process, T, T2, and a directory of the module's own)."""
    d = tmp_path_factory.mktemp("cli")
    t, t2 = plants_p1.twin_crate(d / "t"), plants_p3.t2_crate(d / "t2")
    out = d / "comparison"
    p3_compare.make(plants_p3.declaration(t, t2), out, [t, t2])
    return out, t, t2, d


def run(argv, module="qro", stdout=subprocess.PIPE):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONSAFEPATH",)}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT))
    p = subprocess.run([sys.executable, "-m", module, *argv], stdout=stdout, stderr=subprocess.PIPE, env=env, cwd=ROOT)
    return p.returncode, (p.stdout or b"").replace(b"\r\n", b"\n"), p.stderr.replace(b"\r\n", b"\n")


def test_compare_accepts_with_one_line_on_stdout_and_exit_0(world):
    out, t, t2, _ = world
    code, stdout, stderr = run(["compare", str(out), str(t), str(t2)])
    assert (code, stderr) == (0, b""), S.mask(stderr.decode()[-400:])
    assert stdout.count(b"\n") == 1 and stdout.startswith(b"ACCEPTED comparison ")
    assert stdout.endswith(b": declared real; exploratory (selector-late); 2 measures\n")


def test_compare_refuses_a_tampered_record_with_one_line_and_exit_1(world, tmp_path):
    out, t, t2, _ = world
    copy = shutil.copytree(out, tmp_path / "comparison")
    plants_p3.tamper(copy, lambda m: m.update(means="agree"))
    code, stdout, stderr = run(["compare", str(copy), str(t), str(t2)])
    assert (code, stderr) == (1, b""), S.mask(stderr.decode()[-400:])
    assert stdout.count(b"\n") == 1 and stdout.startswith(b"REFUSED comparison-generated at comparison/record.json line ")


@pytest.mark.parametrize("spell", [str, lambda p: str(p) + os.sep, lambda p: str(p).upper()],
                         ids=["as given", "a trailing separator", "in upper case"])
def test_the_comparisons_directory_given_again_as_a_crate_directory_is_misuse_as_a_process(world, spell):
    out, t, _, _ = world
    code, stdout, stderr = run(["compare", str(out), str(t), spell(out)])
    assert (code, stdout) == (2, b"")
    assert stderr.count(b"\n") == 1 and b"the comparison's own directory, given again as a crate directory; " in stderr
    assert stderr.endswith(USAGE.encode("ascii") + b"\n")


def test_the_same_misuse_in_process_is_exit_2_with_the_usage(world, tmp_path):
    out, t, _, _ = world
    paths = [tmp_path / "out.bin", tmp_path / "err.bin"]
    fds = [os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_BINARY", 0)) for p in paths]
    try:
        code = main(["compare", str(out), str(t), str(out)], out=fds[0], err=fds[1])
    finally:
        for fd in fds:
            os.close(fd)
    assert code == 2 and paths[0].read_bytes() == b""
    assert paths[1].read_bytes().endswith(USAGE.encode("ascii") + b"\n")


def test_compare_into_a_pipe_nobody_reads_exits_3_and_never_120(world):
    out, t, t2, _ = world
    r, w = os.pipe()
    os.close(r)
    try:
        code, _, stderr = run(["compare", str(out), str(t), str(t2)], stdout=w)
    finally:
        os.close(w)
    assert code == 3, S.mask(stderr.decode()[-300:])
    assert stderr == b"FAILED: the verdict could not be written; this is not a verdict\n"


def test_make_as_a_process_writes_a_comparison_the_command_accepts(world, tmp_path):
    out, t, t2, _ = world
    decl = tmp_path / "declaration.json"
    decl.write_bytes((out / "comparison" / "declaration.json").read_bytes())
    code, stdout, stderr = run(["make", "--declaration", str(decl), "--out", str(tmp_path / "made"), str(t), str(t2)],
                               module="qro.p3_compare")
    assert (code, stderr) == (0, b""), S.mask(stderr.decode()[-400:])
    assert stdout.startswith(b"MADE comparison ") and stdout.count(b"\n") == 1
    assert (tmp_path / "made" / "comparison" / "record.json").read_bytes() == (
        out / "comparison" / "record.json").read_bytes()
    identity = stdout.split()[2].rstrip(b":").decode("ascii")
    assert json.loads((tmp_path / "made" / "ro-crate-metadata.json").read_bytes())["@graph"][1][
        "qro:generator"] == p3_record.GENERATOR and len(identity) == 64


@pytest.mark.parametrize("argv, says", [
    ([], "the one command is make"), (["make"], "--declaration, --out and one crate directory or more are needed"),
    (["make", "--out"], "--out: given twice, or without its value"), (["make", "--frobnicate"], "not an option of make"),
    (["make", "--declaration", "no-such-file", "--out", "x", "."], "the declaration cannot be read")],
    ids=["no command", "nothing given", "an option without its value", "an unknown option", "no declaration file"])
def test_make_misuse_is_exit_2_with_the_usage(argv, says):
    code, stdout, stderr = run(argv, module="qro.p3_compare")
    assert (code, stdout) == (2, b"") and stderr.count(b"\n") == 1, stderr
    assert says.encode("ascii") in stderr and stderr.endswith(b"; " + p3_compare.USAGE.encode("ascii") + b"\n")


def test_make_refuses_a_trivial_comparison_with_one_line_and_writes_nothing(world, tmp_path):
    _, t, _, _ = world
    decl = tmp_path / "declaration.json"
    decl.write_bytes(plants_p3.declaration(t, t))
    code, stdout, stderr = run(["make", "--declaration", str(decl), "--out", str(tmp_path / "made"), str(t)],
                               module="qro.p3_compare")
    assert (code, stderr) == (1, b"") and stdout.count(b"\n") == 1
    assert stdout.startswith(b"REFUSED comparison-trivial at run a ") and not (tmp_path / "made").exists()


def test_make_into_a_pipe_nobody_reads_exits_3(world, tmp_path):
    out, t, t2, _ = world
    decl = tmp_path / "declaration.json"
    decl.write_bytes((out / "comparison" / "declaration.json").read_bytes())
    r, w = os.pipe()
    os.close(r)
    try:
        code, _, _ = run(["make", "--declaration", str(decl), "--out", str(tmp_path / "made"), str(t), str(t2)],
                         module="qro.p3_compare", stdout=w)
    finally:
        os.close(w)
    assert code == 3
