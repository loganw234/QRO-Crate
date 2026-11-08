"""QRO-Crate's command line. Exit 0 is accepted, 1 is refused (by name, at a location), 2 is misuse, and 3 is a
failure of the checker itself, which is never a verdict on the crate (P0's verifier, P0-2).

    python -m qro check [--fixtures] CRATE_DIR        the checker's nine steps (qro/checker.py)
    python -m qro custody LOG [AUDIT_RECORD ...]      the custody check (qro/custody.py)
    python -m qro compare COMPARISON_DIR CRATE_DIR [CRATE_DIR ...]
                                                      the comparison check (qro.p3_compare, P3's)

check first loads every parcel's registered steps, raw forms, count rules and generators (checker.load, P0.1).
--fixtures registers P0's fixture raw form and generator (qro/fixture.py), for the controls; never for a real
crate. Without it, a crate naming the fixture is refused `step-unbuilt`. Misuse, exit 2: an empty name; a crate that
is not a directory; a log or record that is not a regular file (a pipe among them); a path the host raises on when
asked what it is (a name too long, a character it refuses, a parent the user cannot search); a path the user may not
read or list, the crate's own files and directories among them, the crate directory itself too (P0's verifier,
round 5, R5-3; P0.9); and a name the host reads as another, which on Windows is a component ending in a space or a
dot, but `.` and `..` (reads_as_another; P0.9). A link to a crate, a log or a record is followed.

compare holds a comparison crate and the crates of its two runs (P0.10; FORMAT.md item 23). Its misuse, exit 2, is the
same rules for every directory it names, the comparison's among them (an empty name; not a directory; a name the host
reads as another; a directory the user may not list), fewer than two arguments, and a crate directory named twice,
however each is spelt (a link is followed). It then loads the parcels' steps and dispatches to
`qro.p3_compare.check(comparison_dir, crate_dirs)`, which returns a Summary whose `str()` is the ACCEPTED line, or
raises Refused (exit 1) or the module's own `Misuse` (exit 2). Where `qro.p3_compare` is not there, the comparison is
refused `step-unbuilt` at "comparison", exit 1, as a crate carrying a term of an unbuilt step is: the command never
accepts what no check has held. A module that is there and has no `check`, or whose summary is no ACCEPTED line, is
the checker failing, exit 3.

The verdict, or the misuse or failure, is one line, written to the descriptor itself (stdout's, or stderr's for 2
and 3), unbuffered, before the exit code is returned (P0's verifier, rounds 2 to 4: R2-2, R3-1, R4-1):
  - the line is printable ASCII. Every other character, a line feed, an escape, a lone surrogate or a CJK
    character among them, and the backslash, is written as its Python escape, which `unicode_escape` reads back.
    So a crate's own text, echoed in a refusal, can neither break the line nor forge another;
  - the line is cut at LINE_MAX escaped characters, where no escape is split, and says how many characters it did
    not write: a hostile file's text, quoted in a refusal, put megabytes into one line (P1.1's third verifier, a
    note; P0.7). What it writes `unicode_escape` reads back as the text's first characters, and the notice;
  - a verdict that cannot be written whole, to a closed pipe, a full disk or a closed descriptor, exits 3: it did
    not arrive. Nothing is left in a buffer for the interpreter's exit to fail on later, with an exit code of its
    own. A stated limit: a descriptor that takes part of the line and then fails has that part, under exit 3;
  - a crash, an exit or an interrupt raised inside the checker exits 3: in a parcel's step or count rule, and in a
    parcel's module that will not load or registers what is not its parcel's (checker.load), among others. Two
    exceptions (P0.1's verifier, round 1, note 4.3.1): a `PermissionError` from a step or a count rule is misuse,
    exit 2, as the user's own is; and a raw-form reader or a generator that raises an `Exception` on the crate's
    bytes has refused them, `raw-form` or `metadata-generated`, exit 1, but for a `MemoryError`, which is the
    host's, exit 3 (P1.1's third verifier, D1). A parcel's step may itself refuse by its step's name what its own
    reading of a crate raises, as P1's do; whatever else a step lets through is the checker failing, but a
    PermissionError, which is misuse.
A stated limit: before this file runs, Python's own failure to start it (no `qro` on the path, a module that will
not import) exits 1, Python's code, with no line on stdout. A refusal is exit 1 and its REFUSED line.
"""
import importlib
import importlib.util
import os
import sys
from pathlib import Path

from qro import canonical, checker, custody, fixture
from qro.refusal import Refused

USAGE = ("usage: python -m qro check [--fixtures] CRATE_DIR, python -m qro custody LOG [AUDIT_RECORD ...], or "
         "python -m qro compare COMPARISON_DIR CRATE_DIR [CRATE_DIR ...]")
COMPARE = "qro.p3_compare"       # P3's module, which holds the comparison (P3's design, item 7)


LINE_MAX = 4096


def escape(text, limit=None):
    """`text` in printable ASCII: every other character, and the backslash, as its Python escape. Past `limit`
    escaped characters it is cut, where no escape is split, and the count of the characters not written follows."""
    out, n = [], 0
    for i, c in enumerate(text):
        e = c if " " <= c <= "~" and c != "\\" else c.encode("unicode_escape").decode("ascii")
        if limit is not None and n + len(e) > limit:
            out.append(f" ... ({len(text) - i} more characters)")
            break
        out.append(e)
        n += len(e)
    return "".join(out)


def write(fd, line):
    """One line, escaped and cut at LINE_MAX, to a descriptor: all of it, now, however little each write takes."""
    data = (escape(line, LINE_MAX) + "\n").encode("ascii")
    while data:
        data = data[os.write(fd, data):]


def kind(path, test):
    """Whether `path` passes `test` (a directory, a regular file); a path the host will not look at does not."""
    try:
        return test(Path(path))
    except OSError:
        return False


EXTENDED = "\\\\?\\"       # Windows' extended-length form, which the host reads as it is written
ANOTHER = "a name the host reads as another: it strips the spaces and dots a name ends in"


def reads_as_another(name, windows=None):
    """Whether the host reads `name` as another entry than the one it spells. Windows strips the spaces and dots a
    component of a path ends in, but the components `.` and `..`: `crate.` and `crate ` name `crate`, `crate.\\x`
    names `crate\\x`, and the host answered for the entry they strip to, ACCEPTED or REFUSED, or for neither (P0.9,
    MEASURED on Windows 11: `crate.` was accepted as `crate`, `crate ` and `crate..` refused `file-missing`). A drive
    designator (`C:`) is no part of the first component's name, so it is taken off before that is asked: `C:.` and
    `C:..\\x` are the drive's current directory and its parent's `x`, as `.` and `..\\x` are, and the host answered
    for what they name (P0.9's first verifier, D2), but `C:crate.` is `crate.` and is refused. Not in the
    extended-length form, which the host reads as it is written, and not on a host that reads every name as written
    (`windows` says which; the host's own is the default)."""
    if windows is None:
        windows = os.name == "nt"
    if not windows or name.startswith(EXTENDED):
        return False
    path = name.replace("/", "\\")
    if path[1:2] == ":" and path[0].isascii() and path[0].isalpha():
        path = path[2:]
    return any(part not in ("", ".", "..") and part[-1] in " ." for part in path.split("\\"))


def unlistable(path):
    """The host's reason, if it refuses to list the directory `path`, else None. A crate directory the user may not
    list was REFUSED `file-missing` when it held no metadata file, for the host answered the metadata file's name
    "not there" though it could not look (P0.9, MEASURED: the profile's `Application Data` junction)."""
    try:
        with os.scandir(path):
            return None
    except OSError as x:
        return x.strerror or type(x).__name__


class UsageError(Exception):
    """Misuse of the comparison check, from the module that holds it (its own `Misuse`): exit 2."""


def compare(comparison_dir, crate_dirs):
    """The comparison's ACCEPTED line, or Refused. Loads every parcel's steps first, for the nine steps the module
    runs on each crate. Where `qro.p3_compare` is not there the comparison is refused `step-unbuilt`; a module that
    is there is held to its contract (`check`, a Summary whose `str()` begins `ACCEPTED comparison `), and one that
    breaks it is the checker failing, never an acceptance. Used by the command and by the controls' runner."""
    checker.load()
    if COMPARE not in sys.modules and importlib.util.find_spec(COMPARE) is None:
        raise Refused("step-unbuilt", "comparison", f"the comparison check, {COMPARE}, is not built yet")
    module = importlib.import_module(COMPARE)
    misuse = getattr(module, "Misuse", None)
    try:
        summary = module.check(comparison_dir, list(crate_dirs))
    except Exception as x:
        if isinstance(misuse, type) and isinstance(x, misuse):
            raise UsageError(str(x)) from None
        raise
    line = str(summary)
    if not line.startswith("ACCEPTED comparison "):
        raise RuntimeError(f"{COMPARE}.check returned a summary that is no ACCEPTED line: {line[:80]!r}")
    return line


def _verdict(argv):
    """The exit code and its line. A refusal or a want of permission whose line cannot be written, its own text
    raising, is not answered as one: what it raises reaches main() as the checker failing (P0.1's verifier, round
    3, C1)."""
    try:
        return _main(argv)
    except Refused as r:
        return 1, f"REFUSED {r.name} at {r.where}: {r.detail}"
    except PermissionError as x:                            # the user's permissions, not the checker
        return 2, f"{x.filename or 'a path'}: cannot be read here, {x.strerror}; {USAGE}"
    except UsageError as x:                                 # the comparison module's own misuse
        return 2, f"{x}; {USAGE}"


def main(argv, out=1, err=2):
    try:
        code, line = _verdict(argv)
    except BaseException as x:                              # a crash, an exit or an interrupt: never a refusal
        code, line = 3, f"FAILED: the checker itself failed, {checker.describe(x)}; this is not a verdict"
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


def directory_misuse(arg, what="crate"):
    """The misuse line for a directory argument, or None: a name the host reads as another, an empty name or one that
    is no directory, a directory the user may not list."""
    if reads_as_another(arg):
        return f"{arg}: {ANOTHER}; {USAGE}"
    if not arg or not kind(arg, Path.is_dir):
        return f"{arg}: no such {what} directory; {USAGE}"
    reason = unlistable(arg)
    if reason is not None:
        return f"{arg}: cannot be read here, {reason}; {USAGE}"
    return None


def same_directory(a, b):
    """Whether two arguments name one directory, a link followed; two the host cannot compare are not one."""
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def _main(argv):
    if argv[:1] == ["compare"]:
        args = argv[1:]
        if len(args) < 2:
            return 2, USAGE
        for i, a in enumerate(args):
            line = directory_misuse(a, "comparison" if i == 0 else "crate")
            if line is not None:
                return 2, line
        for i, a in enumerate(args[2:], 2):
            if any(same_directory(a, b) for b in args[1:i]):
                return 2, f"{a}: a crate directory given twice; {USAGE}"
        return 0, compare(args[0], args[1:])
    if argv[:1] == ["check"]:
        fixtures = argv[1:2] == ["--fixtures"]
        args = argv[2:] if fixtures else argv[1:]
        if len(args) != 1:
            return 2, USAGE
        line = directory_misuse(args[0])
        if line is not None:
            return 2, line
        if fixtures:
            fixture.register()
        checker.load()                                      # every parcel's steps, before any crate is read
        md = checker.check(args[0])
        return 0, f"ACCEPTED {canonical.body_digest(md)}"
    if argv[:1] == ["custody"] and len(argv) >= 2:
        other = [a for a in argv[1:] if reads_as_another(a)]
        if other:
            return 2, f"{other[0]}: {ANOTHER}; {USAGE}"
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
