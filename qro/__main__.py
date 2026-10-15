"""QRO-Crate's command line. Exit 0 is accepted, 1 is refused (by name, at a location), 2 is misuse, and 3 is a
failure of the checker itself, which is never a verdict on the crate (P0's verifier, P0-2).

    python -m qro check [--fixtures] CRATE_DIR        the checker's nine steps (qro/checker.py)
    python -m qro custody LOG [AUDIT_RECORD ...]      the custody check (qro/custody.py)

--fixtures registers P0's fixture raw form and generator (qro/fixture.py), for the controls; never for a real
crate. Without it, a crate naming the fixture is refused `step-unbuilt`. Misuse, exit 2: an empty name; a crate that
is not a directory; a log or record that is not a regular file (a pipe among them); a path the host raises on when
asked what it is (a name too long, a parent the user cannot search); and a path the user may not read or list,
the crate's own files and directories among them (P0's verifier, round 5, R5-3). A link to a crate, a log or a
record is followed.

The verdict, or the misuse or failure, is one line, written to the descriptor itself (stdout's, or stderr's for 2
and 3), unbuffered, before the exit code is returned (P0's verifier, rounds 2 to 4: R2-2, R3-1, R4-1):
  - the line is printable ASCII. Every other character, a line feed, an escape, a lone surrogate or a CJK
    character among them, and the backslash, is written as its Python escape, which `unicode_escape` reads back.
    So a crate's own text, echoed in a refusal, can neither break the line nor forge another;
  - a verdict that cannot be written whole, to a closed pipe, a full disk or a closed descriptor, exits 3: it did
    not arrive. Nothing is left in a buffer for the interpreter's exit to fail on later, with an exit code of its
    own. A stated limit: a descriptor that takes part of the line and then fails has that part, under exit 3;
  - a crash, an exit or an interrupt raised inside the checker, a parcel's code among it, exits 3.
A stated limit: before this file runs, Python's own failure to start it (no `qro` on the path, a module that will
not import) exits 1, Python's code, with no line on stdout. A refusal is exit 1 and its REFUSED line.
"""
import os
import sys
from pathlib import Path

from qro import canonical, checker, custody, fixture
from qro.refusal import Refused

USAGE = "usage: python -m qro check [--fixtures] CRATE_DIR, or python -m qro custody LOG [AUDIT_RECORD ...]"


def escape(text):
    """`text` in printable ASCII: every other character, and the backslash, as its Python escape."""
    return "".join(c if " " <= c <= "~" and c != "\\" else c.encode("unicode_escape").decode("ascii") for c in text)


def write(fd, line):
    """One line, escaped, to a descriptor: all of it, now, however little each write takes."""
    data = (escape(line) + "\n").encode("ascii")
    while data:
        data = data[os.write(fd, data):]


def kind(path, test):
    """Whether `path` passes `test` (a directory, a regular file); a path the host will not look at does not."""
    try:
        return test(Path(path))
    except OSError:
        return False


def main(argv, out=1, err=2):
    try:
        code, line = _main(argv)
    except Refused as r:
        code, line = 1, f"REFUSED {r.name} at {r.where}: {r.detail}"
    except PermissionError as x:                            # the user's permissions, not the checker
        code, line = 2, f"{x.filename or 'a path'}: cannot be read here, {x.strerror}; {USAGE}"
    except BaseException as x:                              # a crash, an exit or an interrupt: never a refusal
        code, line = 3, f"FAILED: the checker itself failed, {type(x).__name__}: {x}; this is not a verdict"
    try:
        write(out if code in (0, 1) else err, line)
    except Exception:                                       # the verdict did not arrive, so it is not given as one
        if code != 3:
            try:
                write(err, "FAILED: the verdict could not be written; this is not a verdict")
            except Exception:
                pass                                        # nowhere left to say it; the exit code still does
        return 3
    return code


def _main(argv):
    if argv[:1] == ["check"]:
        args = argv[1:]
        if args[:1] == ["--fixtures"]:
            fixture.register()
            args = args[1:]
        if len(args) != 1:
            return 2, USAGE
        if not args[0] or not kind(args[0], Path.is_dir):
            return 2, f"{args[0]}: no such crate directory; {USAGE}"
        md = checker.check(args[0])
        return 0, f"ACCEPTED {canonical.body_digest(md)}"
    if argv[:1] == ["custody"] and len(argv) >= 2:
        missing = [a for a in argv[1:] if not a or not kind(a, Path.is_file)]
        if missing:
            return 2, f"{missing[0]}: no such file; {USAGE}"
        log = Path(argv[1]).read_bytes()
        head = custody.check_log(log)
        for rec in argv[2:]:
            custody.check_record(Path(rec).read_bytes(), log)
        return 0, f"ACCEPTED head {head}, {len(argv) - 2} audit records"
    return 2, USAGE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
