"""The command line, in process and as the process a user runs (P0's verifier, rounds 2 to 5: R2-2, R3-1, R3-2's rows
2 to 5, R4-1, R5-3, R5-5b). What it holds, and nothing more:
  - each verdict: an acceptance and its identity, a refusal, a log and its records;
  - each misuse planted here: the wrong arguments, an empty name, a path not there, a path of the wrong kind, a
    path the host raises on, and a log, record, metadata file, listed file or directory the user may not read;
  - the fixture refused `step-unbuilt` without `--fixtures`, for its raw form and, with none, for its generator;
  - the line printable ASCII, and read back whole by `unicode_escape`, for every code point, and cut at LINE_MAX
    with the count of what it left (P0.7);
  - a write the descriptor takes a few bytes at a time, whole; and a verdict that cannot be written, to a pipe nobody
    reads, a closed descriptor, or with both descriptors broken, exiting 3;
  - a crash, an exit and an interrupt inside the checker, exiting 3."""
import codecs
import hashlib
import shutil
import json
import os
import pathlib
import subprocess
import sys

import pytest

from qro import canonical, checker, custody, fixture
from qro.__main__ import LINE_MAX, USAGE, escape, main

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = "data/raw.counts.json"
A, B = "a" * 64, "b" * 64


@pytest.fixture(autouse=True)
def registered(monkeypatch):
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    monkeypatch.setattr(checker, "GENERATORS", {})


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


def crate(tmp_path, edit=None):
    c = fixture.make(tmp_path / "crate")
    if edit is not None:
        p = c / canonical.DESCRIPTOR
        md = json.loads(p.read_bytes())
        edit(md)
        p.write_bytes(canonical.dumps(md))
    return c


def custody_files(tmp_path, log_data, *records):
    (tmp_path / "custody.log").write_bytes(log_data)
    names = [str(tmp_path / "custody.log")]
    for i, rec in enumerate(records):
        (tmp_path / f"audit{i}.json").write_bytes(rec)
        names.append(str(tmp_path / f"audit{i}.json"))
    return names


def two_lines():
    first = custody.line(b"", "received", crate=A, at="2026-10-14T01:00:00Z", **{"from": "withheld"})
    return first + custody.line(first, "received", crate=B, at="2026-10-14T02:00:00Z", **{"from": "withheld"})


def record(head):
    return custody.record(auditor="withheld", checker="qro 0.1.0", checkerCommit="unknown", crate=A,
                          date="2026-10-14", independence="producer-build", logHead=head, signature="none",
                          stages=["crate-only"], trustedTime="none", verdict="accepted")


# -- the verdicts -----------------------------------------------------------------------------------------------
def test_an_accepted_crate_prints_its_identity(tmp_path):
    c = crate(tmp_path)
    want = canonical.body_digest(json.loads((c / canonical.DESCRIPTOR).read_bytes()))
    assert run(tmp_path, ["check", "--fixtures", str(c)]) == (0, f"ACCEPTED {want}\n".encode(), b"")


def test_a_refused_crate_prints_its_refusal(tmp_path):
    c = crate(tmp_path, lambda md: next(e for e in md["@graph"] if e["@id"] == RAW).update(sha256="0" * 64))
    code, out, err = run(tmp_path, ["check", "--fixtures", str(c)])
    assert (code, err) == (1, b"") and out.startswith(b"REFUSED raw-digest at data/raw.counts.json: ")


def test_an_accepted_log_and_record_print_the_head(tmp_path):
    data = two_lines()
    head = custody.check_log(data)
    code, out, err = run(tmp_path, ["custody", *custody_files(tmp_path, data, record(head))])
    assert (code, out, err) == (0, f"ACCEPTED head {head}, 1 audit records\n".encode(), b"")


def test_a_log_that_does_not_chain_is_refused(tmp_path):
    data = two_lines()
    second = json.loads(custody.lines(data)[1])
    broken = custody.lines(data)[0] + canonical.compact(dict(second, prev="c" * 64))
    code, out, _ = run(tmp_path, ["custody", *custody_files(tmp_path, broken)])
    assert code == 1 and out.startswith(b"REFUSED custody-chain at log line 2")


def test_a_record_whose_head_is_no_line_of_the_log_is_refused(tmp_path):
    code, out, _ = run(tmp_path, ["custody", *custody_files(tmp_path, two_lines(), record("c" * 64))])
    assert code == 1 and out.startswith(b"REFUSED custody-head")


def test_every_record_named_is_checked_not_only_the_first(tmp_path):
    data = two_lines()
    good, bad = record(custody.check_log(data)), record("c" * 64)
    code, out, _ = run(tmp_path, ["custody", *custody_files(tmp_path, data, good, bad)])
    assert code == 1 and out.startswith(b"REFUSED custody-head")


# -- misuse -----------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("argv", [[], ["bogus"], ["check"], ["check", "--fixtures"], ["custody"],
                                  ["check", "a", "b"], ["check", "--fixtures", "a", "b"], ["--fixtures", "check"],
                                  ["check", "a", "--fixtures"]],
                         ids=lambda a: " ".join(a) or "nothing")
def test_misuse_exits_2_and_says_how(tmp_path, argv):
    assert run(tmp_path, argv) == (2, b"", b"usage: python -m qro check [--fixtures] CRATE_DIR, or python -m qro "
                                           b"custody LOG [AUDIT_RECORD ...]\n")


def test_two_crates_are_misuse_even_when_the_first_is_accepted(tmp_path):
    c = crate(tmp_path)
    code, out, _ = run(tmp_path, ["check", "--fixtures", str(c), str(c)])
    assert (code, out) == (2, b"")


@pytest.mark.parametrize("what", ["a crate", "a log", "a record", "a log and a record"])
def test_a_path_that_is_not_there_is_misuse(tmp_path, what):
    """The line names the path that is not there (P0.1's verifier, round 4, N7: which one it named was unasserted);
    of two, the first (P0.2's verifier, round 1, T4)."""
    from qro.__main__ import escape
    data = two_lines()
    argv = {"a crate": ["check", str(tmp_path / "nowhere")],
            "a log": ["custody", str(tmp_path / "no.log")],
            "a record": ["custody", *custody_files(tmp_path, data), str(tmp_path / "no.json")],
            "a log and a record": ["custody", str(tmp_path / "no.log"), str(tmp_path / "no.json")]}[what]
    named = argv[1] if what == "a log and a record" else argv[-1]
    code, out, err = run(tmp_path, argv)
    assert (code, out) == (2, b"") and err.decode("ascii").startswith(escape(named) + ": no such"), err


# -- the line: printable ASCII, whatever the crate holds --------------------------------------------------------
@pytest.mark.parametrize("key, shown", [
    ("\ud800", b"\\ud800"), ("中", b"\\u4e2d"), ("café", b"caf\\xe9"),
    ("x\nACCEPTED " + "0" * 64, b"x\\nACCEPTED " + b"0" * 64), ("a\x1b[2Jb", b"a\\x1b[2Jb"), ("a\rb", b"a\\rb"),
    ("a\x00b", b"a\\x00b"), ("a\x7fb", b"a\\x7fb"), ("a\\nb", b"a\\\\nb")],
    ids=["a lone surrogate", "a CJK character", "a latin-1 character", "a forged second line", "an escape sequence",
         "a carriage return", "a NUL", "a DEL", "a backslash"])
def test_a_refusal_echoing_the_crates_text_is_one_line_of_printable_ascii(tmp_path, key, shown):
    """R3-1: a key holding a line feed printed a second line beginning ACCEPTED, under a refusal's exit."""
    c = crate(tmp_path, lambda md: md["@graph"][1].update({key: "x"}))
    code, out, err = run(tmp_path, ["check", "--fixtures", str(c)])
    assert (code, err) == (1, b"")
    assert out.startswith(b"REFUSED term-unknown at ./ " + shown + b":") and out.count(b"\n") == 1
    assert all(0x20 <= b <= 0x7e for b in out[:-1])


def test_escape_is_printable_ascii_for_every_code_point():
    for cp in range(0x110000):
        s = escape(chr(cp))
        assert s.isascii() and s.isprintable() and (s == chr(cp)) == (0x20 <= cp <= 0x7e and cp != 0x5c), cp


# -- a verdict that does not arrive -----------------------------------------------------------------------------
def closed_pipe():
    r, w = os.pipe()
    os.close(r)
    return w


@pytest.mark.parametrize("edit", [None, lambda md: md["@graph"][1].update(x="x")], ids=["an acceptance", "a refusal"])
@pytest.mark.parametrize("how", ["a pipe nobody reads", "a closed descriptor"])
def test_a_verdict_that_cannot_be_written_exits_3(tmp_path, edit, how):
    c = crate(tmp_path, edit)
    fd = closed_pipe() if how == "a pipe nobody reads" else 10**6
    try:
        code, out, err = run(tmp_path, ["check", "--fixtures", str(c)], out=fd)
    finally:
        if how == "a pipe nobody reads":
            os.close(fd)
    assert code == 3 and err == b"FAILED: the verdict could not be written; this is not a verdict\n"


def test_a_crash_is_not_a_verdict(tmp_path, monkeypatch):
    c = crate(tmp_path)
    monkeypatch.setattr(checker, "files", lambda *_: 1 / 0)
    code, out, err = run(tmp_path, ["check", "--fixtures", str(c)])
    assert (code, out) == (3, b"") and err.startswith(b"FAILED: the checker itself failed, ZeroDivisionError")


# -- as a process ----------------------------------------------------------------------------------------------
def process(argv, stdout=subprocess.PIPE, encoding="utf-8"):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING=encoding, PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-m", "qro", *argv], stdout=stdout, stderr=subprocess.PIPE, env=env,
                          cwd=ROOT)


@pytest.mark.parametrize("encoding", ["utf-8", "cp1252", "ascii"])
def test_the_process_writes_the_same_line_in_any_console_encoding(tmp_path, encoding):
    c = crate(tmp_path, lambda md: md["@graph"][1].update({"\ud800\n": "x"}))
    p = process(["check", "--fixtures", str(c)], encoding=encoding)
    assert (p.returncode, p.stderr) == (1, b""), p.stderr[-300:]
    assert p.stdout.startswith(b"REFUSED term-unknown at ./ \\ud800\\n:") and p.stdout.count(b"\n") == 1


@pytest.mark.parametrize("edit", [None, lambda md: md["@graph"][1].update(x="x")], ids=["an acceptance", "a refusal"])
def test_the_process_writing_to_a_pipe_nobody_reads_exits_3_and_never_120(tmp_path, edit):
    """R3-1: the verdict was buffered, the write failed at the interpreter's exit, and the exit code was 120."""
    c = crate(tmp_path, edit)
    w = closed_pipe()
    try:
        p = process(["check", "--fixtures", str(c)], stdout=w)
    finally:
        os.close(w)
    assert p.returncode == 3, p.stderr[-300:]
    assert p.stderr.replace(b"\r\n", b"\n") == b"FAILED: the verdict could not be written; this is not a verdict\n"


def test_the_process_accepts_the_twin_and_prints_its_identity(tmp_path):
    c = crate(tmp_path)
    p = process(["check", "--fixtures", str(c)])
    want = canonical.body_digest(json.loads((c / canonical.DESCRIPTOR).read_bytes()))
    assert (p.returncode, p.stdout, p.stderr) == (0, f"ACCEPTED {want}\n".encode(), b"")


def test_the_process_checks_a_custody_log_and_its_record(tmp_path):
    data = two_lines()
    p = process(["custody", *custody_files(tmp_path, data, record(custody.check_log(data)))])
    assert (p.returncode, p.stderr) == (0, b"")
    assert p.stdout == f"ACCEPTED head {hashlib.sha256(custody.lines(data)[-1]).hexdigest()}, 1 audit records\n".encode()


def test_the_process_calls_misuse_misuse():
    p = process(["bogus"])
    assert (p.returncode, p.stdout) == (2, b"") and p.stderr.startswith(b"usage: python -m qro")


# -- round 4, R4-1 ----------------------------------------------------------------------------------------------
def test_without_fixtures_the_fixture_is_refused_step_unbuilt(tmp_path):
    """Its raw form and generator are registered only by the flag: a real crate naming them names checks that do
    not exist."""
    c = crate(tmp_path)
    code, out, err = run(tmp_path, ["check", str(c)])
    assert (code, err) == (1, b"") and out.startswith(b"REFUSED step-unbuilt at ")
    p = process(["check", str(c)])
    assert p.returncode == 1 and p.stdout.startswith(b"REFUSED step-unbuilt at "), p.stderr[-300:]


@pytest.mark.parametrize("what", ["a file as a crate", "a directory as a log", "a directory as a record",
                                  "a name the host will not look at", "a pipe as a log"])
def test_a_path_of_the_wrong_kind_is_misuse(tmp_path, what):
    data = two_lines()
    log, = custody_files(tmp_path, data)
    (tmp_path / "a-dir").mkdir()
    if what == "a pipe as a log":
        if hasattr(os, "mkfifo"):
            os.mkfifo(tmp_path / "fifo")
            argv = ["custody", str(tmp_path / "fifo")]
        else:                                                   # no named pipe in the file system here: a device
            argv = ["custody", "NUL" if os.name == "nt" else "/dev/null"]
    else:
        argv = {"a file as a crate": ["check", log],
                "a directory as a log": ["custody", str(tmp_path / "a-dir")],
                "a directory as a record": ["custody", log, str(tmp_path / "a-dir")],
                "a name the host will not look at": ["check", str(tmp_path / ("x" * 300))]}[what]
    code, out, err = run(tmp_path, argv)
    assert (code, out) == (2, b"") and b"no such" in err


def test_a_descriptor_that_takes_a_few_bytes_at_a_time_gets_the_whole_line(tmp_path, monkeypatch):
    c = crate(tmp_path)
    real = os.write
    with monkeypatch.context() as m:
        m.setattr(os, "write", lambda fd, b: real(fd, b[:3]))
        code, out, err = run(tmp_path, ["check", "--fixtures", str(c)])
    want = canonical.body_digest(json.loads((c / canonical.DESCRIPTOR).read_bytes()))
    assert (code, out, err) == (0, f"ACCEPTED {want}\n".encode(), b"")


def test_a_descriptor_that_takes_part_and_then_fails_exits_3_holding_that_part(tmp_path, monkeypatch):
    """The stated limit: what it took stays taken."""
    c = crate(tmp_path)
    real, taken = os.write, []

    def part_then_fail(fd, b):
        if taken:
            raise OSError("the pipe is closed")
        taken.append(b[:5])
        return real(fd, b[:5])
    with monkeypatch.context() as m:
        m.setattr(os, "write", part_then_fail)
        code, out, err = run(tmp_path, ["check", "--fixtures", str(c)])
    assert (code, out) == (3, b"ACCEP")


def test_both_descriptors_broken_exit_3_and_raise_nothing(tmp_path):
    c = crate(tmp_path)
    out, err = closed_pipe(), closed_pipe()
    try:
        assert main(["check", "--fixtures", str(c)], out=out, err=err) == 3
        assert main(["bogus"], out=out, err=err) == 3
    finally:
        os.close(out)
        os.close(err)


def test_a_line_past_line_max_is_cut_where_no_escape_is_split_and_says_what_it_left():
    """P1.1's third verifier, a note, MEASURED: six places in P1's readers quote a file's text whole, and a
    hostile file put 3 MB into one REFUSED line. The line is cut at LINE_MAX escaped characters (P0.7), which
    FORMAT.md item 16 states as 4,096: a LINE_MAX of 9,000 passed every test (P0.7's first verifier, a note)."""
    assert LINE_MAX == 4096
    assert escape("x" * (LINE_MAX + 1000), LINE_MAX) == "x" * LINE_MAX + " ... (1000 more characters)"
    assert escape("x" * LINE_MAX, LINE_MAX) == "x" * LINE_MAX, "a line of LINE_MAX characters is whole"
    cut = escape("a" * (LINE_MAX - 2) + chr(233) + "b", LINE_MAX)      # the escape of e acute is four characters
    assert cut == "a" * (LINE_MAX - 2) + " ... (2 more characters)", cut[-40:]
    # the count is of the text's characters, not the escapes' (P0.7's third verifier, T1: by the escaped length, the
    # count passed every test, each cut after ASCII, where the two are one; here it would say -2096)
    assert escape(chr(233) * 2000, LINE_MAX) == "\\xe9" * 1024 + " ... (976 more characters)"
    assert escape("x" * (LINE_MAX + 1000)) == "x" * (LINE_MAX + 1000), "with no limit, escape cuts nothing"


def test_the_process_cuts_a_refusal_quoting_a_long_id(tmp_path):
    """The one line, as a user meets it: a refusal at an @id of 10,000 characters, which the line quotes."""
    long_id = "x" * 10_000
    c = crate(tmp_path, lambda md: md["@graph"].extend([{"@id": long_id, "@type": "Thing"}] * 2))
    p = process(["check", "--fixtures", str(c)])
    assert (p.returncode, p.stderr) == (1, b""), p.stderr[-300:]
    line = p.stdout.decode("ascii")
    assert line.startswith("REFUSED graph-form at xxx") and line.count(chr(10)) == 1, line[:100]
    assert line.endswith(" more characters)" + chr(10)) and len(line) < LINE_MAX + 40, len(line)
    assert line.index(" ... (") == 4096, line.index(" ... (")


def test_the_process_cuts_a_misuse_line_on_its_error_descriptor():
    """P0.7's third verifier, T2: the cut was held only on a REFUSED line at descriptor 1; misuse's line, exit 2, at
    descriptor 2, by no test. It begins with the user's own argument, so only the exit code says what it is
    (VALIDATION, the entry on P0.7's second verifier, D1)."""
    name = "x" * 5000
    p = process(["check", name])
    whole = f"{name}: no such crate directory; {USAGE}"
    assert (p.returncode, p.stdout) == (2, b""), p.stdout[:100]
    assert p.stderr.decode("ascii") == name[:LINE_MAX] + f" ... ({len(whole) - LINE_MAX} more characters)" + chr(10)


def test_the_checker_failing_has_its_line_cut_on_its_error_descriptor(tmp_path, monkeypatch):
    """P0.7's third verifier, T2: the cut on the line of the checker failing, exit 3, at descriptor 2, was held by no
    test. Its prefix still says what the line is."""
    import qro.__main__ as cli

    def crash(argv):
        raise RuntimeError("y" * 5000)
    monkeypatch.setattr(cli, "_verdict", crash)
    code, out, err = run(tmp_path, ["check", "x"])
    line = err.decode("ascii")
    assert (code, out) == (3, b"") and line.startswith("FAILED: the checker itself failed, "), line[:100]
    assert line.index(" ... (") == LINE_MAX and line.endswith(" more characters)" + chr(10)), line[-80:]


def test_escape_is_read_back_whole_by_unicode_escape():
    """So no two texts print alike: the escaped line says which text the crate held."""
    for cp in range(0x110000):
        s = chr(cp) + "x\\" + chr(cp)
        assert codecs.decode(escape(s).encode("ascii"), "unicode_escape") == s, cp


@pytest.mark.parametrize("raised", [SystemExit(0), SystemExit(1), KeyboardInterrupt(), MemoryError()],
                         ids=["exit 0", "exit 1", "an interrupt", "out of memory"])
def test_an_exit_or_interrupt_inside_the_checker_exits_3(tmp_path, monkeypatch, raised):
    """A parcel's code is the checker's: whatever it raises is not a verdict (round 4, note 10)."""
    c = crate(tmp_path)

    def boom(*_):
        raise raised
    monkeypatch.setattr(checker, "files", boom)
    code, out, err = run(tmp_path, ["check", "--fixtures", str(c)])
    assert (code, out) == (3, b"") and err.startswith(b"FAILED: the checker itself failed, ")


def runner_bash():
    """The bash the runner runs under: on Windows, Git's own, found beside git.exe, since a bare `bash` can be
    WSL's, and `which bash` finds WSL's from a shell other than Git Bash (P0's verifier, round 5, note 2)."""
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
def test_the_process_with_a_closed_descriptor_exits_3(tmp_path, redirect):
    """As a process, through a shell that closes the descriptor: the runner's own bash, by its full path (a bare
    `bash` from Python can be another one on Windows)."""
    bash = runner_bash()
    c = crate(tmp_path)
    py, crate_dir = sys.executable.replace("\\", "/"), str(c).replace("\\", "/")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONPATH=str(ROOT))
    p = subprocess.run([bash, "-c", f'"{py}" -m qro check --fixtures "{crate_dir}" {redirect}; echo "rc=$?"'],
                       capture_output=True, env=env, cwd=ROOT)
    assert p.stdout.strip().endswith(b"rc=3"), (p.stdout[-200:], p.stderr[-300:])


@pytest.mark.parametrize("command", ["check", "custody"])
def test_a_path_the_host_refuses_to_look_at_is_misuse(tmp_path, monkeypatch, command):
    """Where the host raises on the question (a parent the user cannot search; on Linux a name too long), the answer
    is misuse, not a crash. Planted, since Windows answers a long name without raising."""
    def refuse(self):
        raise PermissionError(13, "permission denied", str(self))
    monkeypatch.setattr(pathlib.Path, "is_dir", refuse)
    monkeypatch.setattr(pathlib.Path, "is_file", refuse)
    code, out, err = run(tmp_path, [command, str(tmp_path / "anything")])
    assert (code, out) == (2, b"") and b"no such" in err


# -- round 5 ---------------------------------------------------------------------------------------------------
def test_without_fixtures_a_crate_with_no_raw_result_is_refused_for_its_generator(tmp_path):
    """R5-5b: the twin holds a raw result, so a missing raw form refused it whatever the generator. A crate of the
    notes file alone names only the generator; as a process, so a registration made at import would show."""
    c = crate(tmp_path)
    (c / RAW).unlink()
    (c / canonical.DESCRIPTOR).write_bytes(canonical.write(fixture.generate(c)))
    p = process(["check", str(c)])
    assert p.returncode == 1, p.stderr[-300:]
    assert p.stdout.startswith(b"REFUSED step-unbuilt at ./ qro:generator: no generator "), p.stdout


def test_an_empty_directory_is_a_crate_with_no_metadata(tmp_path):
    (tmp_path / "empty").mkdir()
    code, out, _ = run(tmp_path, ["check", "--fixtures", str(tmp_path / "empty")])
    assert code == 1 and out.startswith(b"REFUSED file-missing at ro-crate-metadata.json")


@pytest.mark.parametrize("argv", [["check", ""], ["check", "--fixtures", ""], ["custody", ""]],
                         ids=["an empty crate name", "an empty crate name, with fixtures", "an empty log name"])
def test_an_empty_name_is_misuse(tmp_path, argv):
    """Round 5, note 10: an empty name was the current directory."""
    code, out, err = run(tmp_path, argv)
    assert (code, out) == (2, b"") and b"no such" in err


@pytest.mark.parametrize("error", [OSError(36, "File name too long"), PermissionError(13, "permission denied")],
                         ids=["a name too long", "a parent the user cannot search"])
def test_a_path_the_host_raises_on_is_misuse_whatever_it_raises(tmp_path, monkeypatch, error):
    """Round 5: a 300-character name raises on Linux, not on Windows; any OSError on the question is misuse."""
    def raising(self):
        raise error
    monkeypatch.setattr(pathlib.Path, "is_dir", raising)
    code, out, err = run(tmp_path, ["check", str(tmp_path / "anything")])
    assert (code, out) == (2, b"") and b"no such crate directory" in err


@pytest.mark.parametrize("what", ["the log", "a record", "the metadata", "a listed file"])
def test_a_path_the_user_may_not_read_is_misuse(tmp_path, monkeypatch, what):
    """R5-3: the user's permissions are not the checker failing. Planted, since Windows cannot be made to deny a
    read here without changing an ACL."""
    data = two_lines()
    log, rec = custody_files(tmp_path, data, record(custody.check_log(data)))
    c = crate(tmp_path)
    target = {"the log": log, "a record": rec, "the metadata": str(c / canonical.DESCRIPTOR),
              "a listed file": str(c / "data" / "notes.txt")}[what]
    real = pathlib.Path.read_bytes

    def read_bytes(self):
        if os.path.samefile(self, target):
            raise PermissionError(13, "Permission denied", str(self))
        return real(self)
    monkeypatch.setattr(pathlib.Path, "read_bytes", read_bytes)
    argv = ["custody", log, rec] if what in ("the log", "a record") else ["check", "--fixtures", str(c)]
    code, out, err = run(tmp_path, argv)
    assert (code, out) == (2, b"") and b"cannot be read here, Permission denied" in err, err


def test_a_directory_the_user_may_not_list_is_misuse(tmp_path, monkeypatch):
    """Round 5, note 1: the walk passed a directory it could not list, and the crate was accepted."""
    c = crate(tmp_path)
    (c / "hidden").mkdir()
    (c / "hidden" / "stray.txt").write_bytes(b"x")
    real = os.scandir

    def scandir(path="."):
        if os.path.basename(os.fspath(path)) == "hidden":
            raise PermissionError(13, "Permission denied", os.fspath(path))
        return real(path)
    monkeypatch.setattr(os, "scandir", scandir)
    code, out, err = run(tmp_path, ["check", "--fixtures", str(c)])
    assert (code, out) == (2, b"") and b"hidden: cannot be read here" in err, err
