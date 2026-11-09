"""`crate`: a unit directory into a crate, and the build that removes only what it made (P5's design, item 8; P5.1).

    python -m qro_kit crate UNIT_DIR --out DIR

The crate's layout is the unit generator's (qro/p5_generate.py): `unit/` holds the unit directory's files (UNIT.json, each
device's bundle and run directories), `2026-09-25/p3/circuit-ed767c01bd4b851d.qasm` and `LICENSE-quantum-film` are the kit's
shipped copies of the source circuit and Quantum-Film's licence, and the metadata is regenerated from those files by
`qro-p5-unit` and written by qro.canonical.write, which holds it to the strict reader. The kit runs the checker's nine steps
and intake on what it wrote before it says it is built (a crate the checker refuses is removed, as a build that fails is).

A build that fails, at any point before it returns, removes each file it wrote and each directory it made, and nothing else
(`Made`, adapted from qro/p1_adapter.py's `_Made` and `_clear` at 09ea417, P1.2's design): each entry is listed as it is made,
with its identity, and removed only if it is still that entry; nothing is removed because a function computed its path.
`Made.adopt` is the one addition: a directory the build created whose contents a program it started made (git's, in
`freeze`), listed as a tree; its contents are walked and each entry removed as an entry (a link is unlinked, never entered).
"""
import contextlib
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from qro import canonical, checker, p5_generate, p5_unit as U
from qro.refusal import Refused
from qro_kit import _qf

WRITER = "qro 0.1.0, the P5 kit's crate command"


class CrateError(ValueError):
    """The unit directory or the out is not one the kit will use: misuse (exit 2)."""


def _identity(path):
    st = os.lstat(path)
    return st.st_dev, st.st_ino


def _unchanged(path, identity, kind):
    st = os.lstat(path)
    return kind(st.st_mode) and not getattr(st, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0) \
        and (st.st_dev, st.st_ino) == identity


def _first_missing(path):
    top, here = None, Path(path)
    while not here.exists() and here != here.parent:
        top, here = here, here.parent
    return top


class Made:
    """What a build has made, listed as it makes it, so that a build that fails removes that and nothing else."""

    def __init__(self):
        self.directories, self.files, self.trees, self.bytes = [], [], [], 0

    def directory(self, path):
        """Make `path` and each directory above it that is missing, one level at a time, listing each this build made."""
        top = _first_missing(path)
        if top is None:
            return
        chain = [path, *Path(path).parents]
        for level in reversed(chain[:chain.index(top) + 1]):
            try:
                os.mkdir(level)
            except FileExistsError:
                if not level.is_dir():
                    raise
                continue
            self.directories.append((level, _identity(level)))

    def write(self, path, data):
        """Write `data` to a new file at `path`; a file already there is an error. The file is listed before a byte goes in."""
        path = Path(path)
        self.directory(path.parent)
        with open(path, "xb") as f:
            st = os.fstat(f.fileno())
            self.files.append((path, (st.st_dev, st.st_ino)))
            f.write(data)
        self.bytes += len(data)

    def adopt(self, path):
        """List a directory this build created and a program it started has filled (git's repositories)."""
        self.trees.append((Path(path), _identity(path)))

    def clear(self):
        """Remove what the build made and nothing else; what cannot be removed is left (a failure to clear never
        replaces the build's own error)."""
        directories = dict(self.directories)

        def still(path, identity, kind):
            return _unchanged(path, identity, kind) and all(
                _unchanged(d, directories[d], stat.S_ISDIR) for d in path.parents if d in directories)
        for path, identity in self.files:
            with contextlib.suppress(OSError):
                if still(path, identity, stat.S_ISREG):
                    os.unlink(path)
        for path, identity in self.trees:
            with contextlib.suppress(OSError):
                if still(path, identity, stat.S_ISDIR):
                    remove_listed_tree(path)
        for path, identity in sorted(self.directories, key=lambda d: len(d[0].parts), reverse=True):
            with contextlib.suppress(OSError):
                if still(path, identity, stat.S_ISDIR):
                    os.rmdir(path)


def remove_listed_tree(root):
    """Remove every entry under `root`, which a build created and listed, and `root` itself: files unlinked (a read-only
    file made writable first), directories removed after their contents, a link or junction unlinked and never entered.
    Each entry is asked what it is with an lstat before anything is done to it (os.walk does not do that for a junction,
    which it enters: found by tests/p5/test_p5_made.py, whose junction's target lost its file), and no path is computed
    but by joining a name a listing gave."""
    for name in os.listdir(root):
        p = os.path.join(root, name)
        if _is_link(p):
            if os.path.isdir(p) and os.name == "nt":
                os.rmdir(p)                     # a junction or a directory link: removed as itself, never entered
            else:
                os.unlink(p)
        elif stat.S_ISDIR(os.lstat(p).st_mode):
            remove_listed_tree(p)
        else:
            try:
                os.unlink(p)
            except PermissionError:
                os.chmod(p, stat.S_IWRITE)
                os.unlink(p)
    os.rmdir(root)


def _is_link(path):
    st = os.lstat(path)
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _no_link(p):
    if _is_link(p):
        raise CrateError(f"{p}: a link in the unit directory, which the kit does not follow")


def unit_files(unit_dir):
    """[(path on disk, path in the crate)] of the unit directory's files, a link refused; the crate's `unit/` prefix."""
    base = Path(unit_dir)
    out = []
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames) + list(dirnames):
            _no_link(Path(dirpath, name))
        for name in sorted(filenames):
            p = Path(dirpath, name)
            out.append((p, U.UNIT_DIR + "/" + p.relative_to(base).as_posix()))
    return out


def build(unit_dir, out, *, tree, now=None, log=print):
    """Build the crate of a unit directory into `out`; {"files", "bytes", "identity", "intake"}. `tree` is the kit-dirty
    check (it runs first of everything). Refused for records that disagree (metadata-generated), or a crate the checker or
    intake refuses; CrateError for an out or a unit directory the kit will not use."""
    state = tree()
    unit_dir, out = Path(unit_dir), Path(out)
    if not (unit_dir / "UNIT.json").is_file():
        raise CrateError(f"{unit_dir}: no UNIT.json: not a unit directory")
    if out.exists():
        raise CrateError(f"{out}: exists; a crate is built into a directory that is not there yet")
    here = out.resolve().parent
    if any(parent == unit_dir.resolve() for parent in (here, *here.parents)):
        raise CrateError(f"{out}: lies inside the unit directory")
    made = Made()
    try:
        made.directory(out)
        for src, rel in unit_files(unit_dir):
            made.write(out.joinpath(*rel.split("/")), src.read_bytes())
        made.write(out / U.SOURCE_PATH, (_qf.VENDOR / "circuit-ed767c01bd4b851d.qasm").read_bytes())
        made.write(out / U.LICENSE_PATH, (_qf.VENDOR / "LICENSE-quantum-film").read_bytes())
        when = (now or datetime.now(timezone.utc)).replace(microsecond=0)
        identity = p5_generate.finalize(out, made.write, now=when, writer=WRITER)
        checker.load()
        md = checker.check(out)
        if canonical.body_digest(md) != identity:
            raise Refused("metadata-generated", "the crate", "the checker read another crate than the one written")
        result = U.intake(out)
    except BaseException:
        with contextlib.suppress(Exception):
            made.clear()
        raise
    return {"files": len(made.files), "bytes": made.bytes, "identity": identity, "intake": result, "kit": state}
