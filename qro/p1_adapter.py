"""P1's adapter: Quantum-Film's records, and IBM's or Moth's, into a crate, built outside the tree (P1's design,
items 1 and 11; P1.2).

    python -m qro.p1_adapter ibm|atlas --moth DIR --out DIR [--records DIR] [--slice]

`--moth` is a checkout of moth-quantum, clean at 3a73823, or with `--slice` a directory laid out as one that holds
a part of its records (the committed twin, tests/p1/data/moth, which is not a checkout and is not asked to be one).
Clean is two things (P1.2's sixth verifier, D2). `git status` finds no change and no untracked file, whatever the
checkout's `status.showUntrackedFiles` says, and `git ls-files -v` marks no file assume-unchanged or skip-worktree
(`check_moth`). And every file the build takes from the checkout is 3a73823's own, whatever the checkout's own settings
say of what git shows of it (an ignore rule, an attribute, a filter): its path is a regular file of HEAD's tree (mode
100644 or 100755) and the bytes the build copies, from the one read it copies, are that blob's by git's own hash of a
blob (`head_tree`, `hold_to_head`). git's output is read as bytes and decoded as UTF-8, git's own spelling of a path on
every host, so that no name in the checkout, under any `core.quotePath`, and no error of git's decides the exit or adds
a line (P1.2's sixth verifier, D1); a git that fails shows the first line it said. A slice is taken as it is: it is not a checkout, and the adapter does not check what
it builds, the checker does (a slice that lacks a file a carried job's commitment binds builds a crate the checker
refuses, `commitment`). `--records` is this repository's records/, where the read of 2026-10-14 is; by default the
repository's own. `--out`
is a directory that does not hold anything yet and lies in neither this repository nor the checkout: Moth's data
never enters the tree, and IBM's calibration snapshots are not licensed to (a crate built in the tree could be
committed by a `git add -A`). The adapter copies the records the crate carries, byte for byte, to their paths in the
crate; asks P2's module, if it is present, for the files of the question (none, for a crate P2 has no law for: such a
crate carries none of P2's terms; a raise of P2's, but the host's, is the records refused by the seam, `metadata-generated`
at P2's module); generates the metadata with the crate's
generator (qro/p1_generate.py); and writes it with qro.canonical.write, which holds it to the strict reader. A build
that fails removes each file it wrote and each directory it made, and nothing else (`_clear`); what another put in
their way during the build stays, and with it every directory above it. The checkout is only read: its git calls take
no optional lock, so that not even its index is refreshed.

What is copied. The IBM crate: Quantum-Film's IBM records of 2026-10-05, its source circuit, its LICENSE as
LICENSE-quantum-film, and the read of 2026-10-14 but for the four files of its dry-run probes, which are the account's
plan and usage and no part of any run. The Atlas crate: the two days' files of Quantum-Film's Atlas runs but for the
platform descriptions, which carry a local path and a host's details, and the rolls directories, which the decode
re-derives; the known-answer vector; and the LICENSE. A slice takes of the read only the records of the jobs it
carries, and every snapshot of their devices.

The command line writes one line, as `python -m qro check` does. Exit 0 is a crate built; 1 and a REFUSED line is the
records refused: by `metadata-generated` and the guard's place and reason, or by the writer's own refusal of the text the
records make (a program name with a space in it); 2 is misuse, a command line that is not the command's (an option
given twice among it), a checkout, a `--records` or an `--out` the adapter will not use, among it a file the build would
take from the checkout that is not 3a73823's own (not a regular file of HEAD's tree, or not that blob's bytes), a
`--moth` or a `--records` the host will not let the adapter look at (asked what it is or holds, or
listed), an `--out` that names no directory an entry can be made in (a network, extended-length or device spelling
with no share or no name, or a root that is not there), and an `--out` the host cannot look at (one it cannot list),
or cannot make, or cannot make the first entry under (a last component ending in a space, which Windows makes without
it; a path too long, which Windows refuses with a ValueError); 3 is the adapter itself failing, which is never a verdict
on the records: among it no git on the PATH, a record the host will not let the adapter read once the build is under
way, the host refusing an entry after the first under the out, and another's file where the build writes.
"""
import contextlib
import hashlib
import os
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from qro import canonical, checker, p1_generate, p1_records as rec, spelling
from qro.__main__ import write
from qro.refusal import Refused

MOTH_COMMIT = "3a73823"
USAGE = "usage: python -m qro.p1_adapter ibm|atlas --moth DIR --out DIR [--records DIR] [--slice]"
REPO = Path(__file__).resolve().parents[1]
RECORDS = ("docs", "records")                   # in moth-quantum, as a tuple so that no path is spelt in this text
IBM_DAY, ATLAS_DAYS = "2026-10-05", ("2026-09-25", "2026-09-26")
SOURCE_CIRCUIT = ("2026-09-25", "p3", "circuit-ed767c01bd4b851d.qasm")
VECTOR = (("tests", "vectors", "tomography-bitorder-2026-09-25.json"), "vectors/tomography-bitorder-2026-09-25.json")
WRITER = "qro 0.1.0, the P1 adapter"
PROBES = "ibm-dryrun-probe"                     # the dry-run probes: two directories and their two logs, by this prefix
FILE_MODES = ("100644", "100755")               # a regular file in a git tree, as `git ls-tree` writes its mode


class AdapterError(ValueError):
    """The invocation names something the adapter will not use: misuse, exit 2."""


def _no_link(p):
    """A link (a symbolic link or a junction) is refused: a crate holds files, and so does its source."""
    if p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()):
        raise AdapterError(f"{p}: a link in the records, which the adapter does not follow")


@contextlib.contextmanager
def _asking(option, given):
    """While the adapter asks what an input, `--moth` or `--records`, is or holds, and lists its directories: an OSError
    or a ValueError the host raises makes it an input the adapter will not use, misuse (AdapterError), the input named,
    and the place in it the host refused, as check_out names an out it will not let the adapter look at (P1.2's fifth
    verifier, D3). The adapter's own refusals pass as they are. Reading a record is not asked here: the build is under
    way by then, and a record the host will not let the adapter read is the adapter failing, exit 3."""
    try:
        yield
    except (AdapterError, p1_generate.GuardError, rec.RecordError):
        raise
    except (OSError, ValueError) as x:
        where = getattr(x, "filename", None)
        at = f": {where}" if isinstance(where, str) and Path(where) != Path(given) else ""
        raise AdapterError(f"{option} {given}: cannot be looked at{at} ({_why(x)})") from None


def _raise(error):
    raise error


def _files(base):
    """Every file under `base`, relative to it; a link is refused, and a directory the host will not list is the host's
    error, never passed over (os.walk's own way)."""
    out = []
    for dirpath, dirnames, filenames in os.walk(base, onerror=_raise, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames) + list(dirnames):
            _no_link(Path(dirpath, name))
        out += [Path(dirpath, n) for n in sorted(filenames)]
    return [(p, p.relative_to(base).as_posix()) for p in out]


def _file(p):
    """Whether `p` is a file the crate is to carry, where one may be absent; a link there is refused, as `_files`
    refuses one."""
    _no_link(p)
    return p.is_file()


def _present(moth):
    """{(device, job id)} of the jobs whose lines the records hold: what a slice carries. A line that cannot be read is
    the records refused, as the generator refuses it (G2), and not misuse; the lines are listed under _asking, and read
    after, so that one the host will not let the adapter read is the adapter failing."""
    base = Path(moth).joinpath(*RECORDS, IBM_DAY, "ibm")
    with _asking("--moth", moth):
        lines = [(p, rel) for p, rel in (_files(base) if base.is_dir() else []) if rel.endswith("-line.json")]
    out = set()
    for path, rel in lines:
        try:
            out.add((rel.split("/")[0], rec.line(path.read_bytes(), rel).job_id))
        except rec.RecordError as x:
            raise p1_generate.GuardError("G2", f"{IBM_DAY}/ibm/{rel}", str(x)) from None
    return out


def plan(kind, moth, records, sliced):
    """[(path in the crate, source path)], sorted: what the crate carries. What `--moth` and `--records` are and hold is
    asked, and their directories listed, under _asking; only a slice's job lines are read here (_present)."""
    moth = Path(moth)
    out = {}

    def add(src, rel):
        if rel in out:
            raise AdapterError(f"two files would be {rel} in the crate")
        out[rel] = Path(src)
    with _asking("--moth", moth):
        licence = moth / "LICENSE"
        if _file(licence):
            add(licence, p1_generate.LICENSE_QF)
        base = moth.joinpath(*RECORDS)
        if kind == "ibm":
            for p, rel in _files(base / IBM_DAY / "ibm") if (base / IBM_DAY / "ibm").is_dir() else []:
                add(p, f"{IBM_DAY}/ibm/{rel}")
            source = base.joinpath(*SOURCE_CIRCUIT)
            if _file(source):
                add(source, "/".join(SOURCE_CIRCUIT))
        else:
            for day in ATLAS_DAYS:
                if (base / day / "p3").is_dir():
                    for p in sorted((base / day / "p3").iterdir()):
                        if p.name.endswith(".platform.json") or p.is_dir():     # left out, as the rolls directories are
                            continue
                        if _file(p):
                            add(p, f"{day}/p3/{p.name}")
            vector = moth.joinpath(*VECTOR[0])
            if _file(vector):
                add(vector, VECTOR[1])
    if kind == "ibm":
        read = Path(records) / p1_generate.READ
        present = _present(moth) if sliced else set()
        devices = {d for d, _ in present}
        with _asking("--records", records):
            if not read.is_dir():
                raise AdapterError(f"{read}: the read of {p1_generate.READ} is not here; --records names the records/ "
                                   "of this repository")
            listed = _files(read)
        for p, rel in listed:
            top = rel.split("/")[0]
            if top.startswith(PROBES):
                continue
            parts = rel.split("/")
            if sliced and len(parts) == 3 and parts[0] in ("ibm-refetch", "ibm-results-refetch"):
                job = parts[2][:-len(".json")]
                if parts[2].startswith("properties-"):
                    if parts[1] not in devices:
                        continue
                elif (parts[1], job) not in present:
                    continue
            add(p, f"{p1_generate.READ}/{rel}")
    return sorted(out.items())


def _git_bytes(moth, *args):
    """git's stdout in the checkout, the bytes git wrote. git's output, stdout and stderr, is read as bytes and is never
    decoded by the host's code page: a name git writes in UTF-8, as it does under `core.quotePath false`, that the code
    page cannot decode (U+0141 in cp1252) failed in subprocess's reader thread, whose traceback reached stderr and which
    gave no output at all, so that a checkout with a change was exit 3 and not exit 2 (P1.2's sixth verifier, D1). So no
    name in the checkout, whatever `core.quotePath` says, and no error of git's decides the exit or adds a line. git
    that cannot be found, FileNotFoundError, is the adapter failing (exit 3: no git on the PATH, as docs/P1.md lists it;
    the checkout was found a directory just before); any other OSError of starting it is the host refusing it the
    checkout, misuse (AdapterError), `--moth` named; git that fails is a checkout the adapter will not use, misuse, and the
    first line it said is shown (UTF-8, a byte that is not replaced: it may name a path). git is asked without replace
    objects: a ref of the checkout's own (`git replace`) would make git show another commit's tree and files where it is
    asked for HEAD's, and `git status` agree."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"                 # read only: `git status` refreshes no index as it looks
    try:
        r = subprocess.run(["git", "--no-replace-objects", *args], cwd=moth, capture_output=True, env=env)
    except FileNotFoundError:
        raise
    except OSError as x:
        raise AdapterError(f"--moth {moth}: cannot be looked at (git cannot start in it: {_why(x)})") from None
    if r.returncode != 0:
        said = _shown(r.stderr).strip().split("\n", 1)[0][:200]
        raise AdapterError(f"{moth}: git {' '.join(args)} failed; the checkout must be a git checkout of moth-quantum"
                           + (f" (git said: {said})" if said else ""))
    return r.stdout


def _shown(data):
    """Bytes git wrote, as text where a name is only shown: UTF-8, git's own spelling of a path on every host, a byte that
    is not UTF-8 replaced."""
    return data.decode("utf-8", "replace")


def _git(moth, *args):
    """git's output in the checkout as text, stripped, for what is only shown or asked whether it is empty (_shown)."""
    return _shown(_git_bytes(moth, *args)).strip()


def check_moth(moth):
    """The checkout named is moth-quantum's own, clean, at 3a73823 (AdapterError otherwise): git sees no change and no
    untracked file that its settings do not ignore (`--untracked-files=all`, whatever `status.showUntrackedFiles` says),
    and marks no file assume-unchanged or skip-worktree, which `git status` cannot see either. What the checkout's own
    settings hide from `git status` is not asked here but of each file the build takes (head_tree, hold_to_head). It
    returns the commit's full id."""
    if _git(moth, "rev-parse", "--show-cdup"):
        raise AdapterError(f"{moth}: not the top of a git checkout")
    head = _git(moth, "rev-parse", "HEAD")
    if not head.startswith(MOTH_COMMIT):
        raise AdapterError(f"{moth}: at {head[:7]}, and the adapter reads moth-quantum at {MOTH_COMMIT}")
    if _git(moth, "status", "--porcelain", "--untracked-files=all"):
        raise AdapterError(f"{moth}: has changes that are not committed; the adapter reads moth-quantum clean at "
                           f"{MOTH_COMMIT}")
    for entry in _git_bytes(moth, "ls-files", "-v", "-z").split(b"\0"):     # -z: a name is never quoted, nor split
        if entry[:1] not in (b"", b"H"):        # H is a file as the index has it; h, s and S are marked, which status cannot see
            raise AdapterError(f"{moth}: marks a file assume-unchanged or skip-worktree ({_shown(entry[2:])}), which "
                               f"`git status` cannot see; the adapter reads moth-quantum clean at {MOTH_COMMIT}")
    return head


def head_tree(moth, head):
    """{path: (mode, object id)} of every entry of the tree of the commit `head` in the checkout, as `git ls-tree -r -z
    --full-tree` lists them: the path as the bytes git wrote it, never decoded (a name is matched, not shown), and the
    mode and the id as text. It is the commit's own: the checkout's settings (ignore rules, attributes, filters) are not
    in it."""
    tree = {}
    for entry in _git_bytes(moth, "ls-tree", "-r", "-z", "--full-tree", head).split(b"\0"):
        if entry:
            meta, path = entry.split(b"\t", 1)
            mode, _kind, oid = meta.split(b" ")
            tree[path] = (mode.decode("ascii"), oid.decode("ascii"))
    return tree


def _blob_id(data, size):
    """git's id of a blob that holds `data`, as git hashes one: the hash of "blob", the length, a NUL and the bytes, SHA-1
    for an id of 40 characters and SHA-256 for one of 64, the two object formats git has. None for any other length, which
    no bytes match."""
    name = {40: "sha1", 64: "sha256"}.get(size)
    if name is None:
        return None
    h = hashlib.new(name, usedforsecurity=False)
    h.update(b"blob %d\0" % len(data))
    h.update(data)
    return h.hexdigest()


def hold_to_head(moth, tree, rel, data):
    """The file at `rel` in the checkout, whose bytes are `data`, the one read the build copies, is 3a73823's own
    (AdapterError otherwise, `rel` named and which it is): its path is a regular file of the tree (mode 100644 or 100755;
    a link, mode 120000, is not, whatever bytes are checked out in its place), and the bytes are that blob's by git's own
    hash of a blob. `git status` cannot tell either where the checkout's own settings hide a file (`.git/info/exclude`, a
    `.gitignore`, a `core.excludesFile`) or make bytes compare equal to a blob's (an attribute or a filter: a line-ending
    conversion)."""
    entry = tree.get(os.fsencode(rel))
    if entry is None or entry[0] not in FILE_MODES:
        held = "the tree of that commit does not hold it" if entry is None else \
            f"the tree of that commit holds it as mode {entry[0]}, not as a regular file"
        raise AdapterError(f"{moth}: {rel} is not a file of moth-quantum at {MOTH_COMMIT} ({held}), and the build would "
                           f"take it; the adapter reads only moth-quantum's own files at {MOTH_COMMIT}")
    if _blob_id(data, len(entry[1])) != entry[1]:
        raise AdapterError(f"{moth}: {rel} is not moth-quantum's bytes at {MOTH_COMMIT} (they are not the bytes of its blob "
                           f"in the tree of that commit), and the build would copy them; the adapter reads only "
                           f"moth-quantum's own bytes at {MOTH_COMMIT}")


def _in_checkout(src, moth):
    """The path of `src` in the checkout, joined with `/`, if the plan took it from there (it lies under the path it was
    given, as the plan joined it); None for a file of this repository's records."""
    try:
        return Path(src).relative_to(moth).as_posix()
    except ValueError:
        return None


def _plain(path):
    """The path an extended-length spelling names, as the sandbox's guard reads one: `\\\\?\\UNC\\server\\share\\x` is
    `\\\\server\\share\\x`, and `\\\\?\\C:\\x` is `C:\\x`; any other spelling as it is. os.path.realpath keeps the prefix its
    input had, so without this two spellings of one place would not compare equal."""
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path[8:]
    if path.startswith("\\\\?\\") and path[5:6] == ":":
        return path[4:]
    return path


def _inside(path, parent):
    """Whether `path` is `parent` or lies in it, each told by where it really is: links resolved, and either spelt with the
    extended-length prefix or without."""
    path, parent = (Path(_plain(os.path.realpath(p))) for p in (path, parent))
    return path == parent or parent in path.parents


def _why(x):
    """What the host said of a path it would not take: an OSError's own words, or a ValueError's (Windows refuses a path
    of 32,768 characters or more with one)."""
    return (x.strerror if isinstance(x, OSError) else str(x)) or type(x).__name__


def check_out(out, moth):
    """`out` holds nothing yet, lies in neither this repository nor the checkout, and names a directory an entry can
    be made in (AdapterError otherwise). Two kinds of spelling name none (P1.2's fifth verifier, D2): one onto which
    pathlib joins an entry as a part of a server, a share or a device, and not in it (a network, extended-length or
    device spelling with no share or no name: `\\\\`, `\\\\server`, `\\\\?\\`, `\\\\.\\`, `\\\\?\\UNC\\server`), told
    before the host is asked anything; and a root that is not there (a share that cannot be reached, a drive that is
    not), under which no directory can be made. An out the host cannot look at, an OSError or a ValueError of any of
    these calls (a directory it cannot list, a path too long), is one the adapter will not use: AdapterError too, the
    out named."""
    out = Path(out)
    entry = out / canonical.DESCRIPTOR                  # an entry every build makes, joined as the build joins its own
    if entry.parent != out:
        raise AdapterError(f"{out}: names no directory an entry can be made in; an entry joined to it is {entry}, not "
                           "one in it (a network, extended-length or device spelling with no share or no name)")
    try:
        for name, parent in (("this repository", REPO), ("the checkout", moth)):
            if _inside(out, parent):
                raise AdapterError(f"{out}: inside {name}; a crate is built outside the tree, so that nothing of it can "
                                   "be committed")
        if out.parent == out and not out.exists():
            raise AdapterError(f"{out}: a root that is not there, so that no directory can be made under it")
        if out.exists() and (not out.is_dir() or any(out.iterdir())):
            raise AdapterError(f"{out}: not an empty directory; the adapter builds into one that holds nothing")
    except AdapterError:
        raise
    except (OSError, ValueError) as x:
        raise AdapterError(f"{out}: cannot be used ({_why(x)})") from None


def build(kind, moth, out, records=None, sliced=False, now=None):
    """Build a crate of `kind`, "ibm" or "atlas", into `out`: {"files", "bytes", "identity"}, the files and bytes the
    build wrote. AdapterError for a checkout, a `--records` or an out the adapter will not use, and for a file it would
    take from a checkout that is not 3a73823's own (hold_to_head: each is held to HEAD's tree as it is read, before it is
    written; a slice is not a checkout and is not asked); GuardError (qro.p1_generate) for records that disagree. Every
    directory and file it makes is listed as it is made (_Made), and a build that fails, at any point before it returns,
    removes those, and nothing else (_clear)."""
    if kind not in ("ibm", "atlas"):
        raise AdapterError(f"{kind}: not a crate this adapter builds; {USAGE}")
    moth, out = Path(moth), Path(out)
    with _asking("--moth", moth):
        if not moth.is_dir():
            raise AdapterError(f"{moth}: no such directory")
    if not sliced:
        head = check_moth(moth)
    check_out(out, moth)
    tree = None if sliced else head_tree(moth, head)            # a slice is not a checkout and is not asked
    made = _Made(out)
    try:
        try:
            made.directory(out)
        except (OSError, ValueError) as x:
            raise AdapterError(f"{out}: cannot be made ({_why(x)})") from None
        for rel, src in plan(kind, moth, REPO / "records" if records is None else records, sliced):
            data = src.read_bytes()                             # the one read: the bytes held to the blob are the ones copied
            held = None if tree is None else _in_checkout(src, moth)
            if held is not None:
                hold_to_head(moth, tree, held, data)
            made.write(out.joinpath(*rel.split("/")), data)
        module = p1_generate.p2_module()
        if module is not None:
            named = p1_generate.call_p2(module, "question_files", out)
            if not isinstance(named, dict):
                raise p1_generate.GuardError("seam", p1_generate.P2_MODULE,
                                             "question_files returned something that is no dict")
            folded = {str(k).casefold() for k in named}
            if len(folded) != len(named):
                raise p1_generate.GuardError("seam", p1_generate.P2_MODULE, "question_files names two files whose names "
                                                                             "differ only by case")
            for rel, data in sorted(named.items()):
                if not isinstance(rel, str) or not isinstance(data, bytes) \
                        or spelling.path_problem(p1_generate.QUESTION_DIR + rel):
                    raise p1_generate.GuardError("seam", p1_generate.P2_MODULE,
                                                 f"question_files names {rel!r}: a path under question/ in the crate's "
                                                 "own spelling, and the file's bytes")
                made.write(out.joinpath(*(p1_generate.QUESTION_DIR + rel).split("/")), data)
        md = (p1_generate.ibm if kind == "ibm" else p1_generate.atlas)(out)
        when = (now or datetime.now(timezone.utc)).replace(microsecond=0)
        md["@graph"][1].update({"datePublished": when.strftime("%Y-%m-%d"), "qro:writer": WRITER,
                                "qro:writtenAt": spelling.time(when)})
        made.write(out / canonical.DESCRIPTOR, canonical.write(md))
        done = {"files": len(made.files), "bytes": made.bytes, "identity": canonical.body_digest(md)}
    except BaseException:
        with contextlib.suppress(Exception):            # a failure to clear never replaces the build's own error
            _clear(made)
        raise
    return done


class _Made:
    """What a build has made into `out`, listed as it makes it, so that a build that fails removes that and nothing
    else (_clear): each directory it made, from the first that was missing down to the out and each that a file's parent
    needed, made one level at a time so that one already there, another's, is never listed; and each file it wrote,
    created anew so that a file already there is never overwritten or listed. Each is listed with its identity, (device,
    file number): a directory's taken by its path as it was made, a file's from the handle that made it. `bytes` is the
    sum of what the files hold."""

    def __init__(self, out):
        self.out, self.directories, self.files, self.bytes = out, [], [], 0
        self.used = False                               # whether anything is made under the out yet

    def _first_under_out(self, path, make):
        """`make(path)`. The first entry the build makes under the out, a directory or a file, failing on the host (an
        OSError, but another's entry in its way, or a ValueError) is the out failing: one the host cannot use, misuse
        (AdapterError). So is a last component that ends in a space, which Windows makes without the space, finding
        nothing under it after."""
        if self.used or path.parent != self.out:
            return make(path)
        try:
            made = make(path)
        except FileExistsError:
            raise
        except (OSError, ValueError) as x:
            raise AdapterError(f"{self.out}: cannot be made ({_why(x)})") from None
        self.used = True
        return made

    def directory(self, path):
        """Make the directory `path` and each directory above it that is missing, from the first that is missing
        (_first_missing) down, listing each this build made."""
        top = _first_missing(path)
        if top is None:
            return
        chain = [path, *path.parents]
        for level in reversed(chain[:chain.index(top) + 1]):
            try:
                self._first_under_out(level, os.mkdir)
            except FileExistsError:                     # there already, another's: never this build's to remove
                if not level.is_dir():
                    raise
                continue
            self.directories.append((level, _identity(level)))

    def write(self, path, data):
        """Write `data` to a new file at `path`, its directory made as above; a file already there is an error, and is
        never overwritten. The file is listed before a byte is written, so that one half written is removed too."""
        self.directory(path.parent)
        with self._first_under_out(path, lambda p: open(p, "xb")) as f:
            st = os.fstat(f.fileno())
            self.files.append((path, (st.st_dev, st.st_ino)))
            f.write(data)
        self.bytes += len(data)


def _identity(path):
    """(device, file number) of the file or directory at `path` itself, a link not followed: what `_unchanged` holds a
    path to, and what `os.fstat` gives of the handle that made a file (a test holds the two the same)."""
    st = os.lstat(path)
    return st.st_dev, st.st_ino


def _unchanged(path, identity, kind):
    """`path` is still what the build made there: of its kind (stat.S_ISREG, stat.S_ISDIR), which a symbolic link is
    not; no reparse point, which a junction is; and the same file, by its identity."""
    st = os.lstat(path)
    return kind(st.st_mode) and not getattr(st, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT \
        and (st.st_dev, st.st_ino) == identity


def _first_missing(path):
    """The topmost directory of `path` that does not exist yet, where a build of it starts making (None: it exists).
    It says where to start, never what to remove: only what the build made is removed (_clear)."""
    top, here = None, Path(path)
    while not here.exists() and here != here.parent:
        top, here = here, here.parent
    return top


def _clear(made):
    """Remove what a failed build made, and nothing else; nothing is removed recursively, and nothing because a function
    computed its path, only because the build made it and listed it (_Made).

    First each file on the list is unlinked if it is still the regular file the build wrote and every directory the
    build made on the way to it is still the one it made (_unchanged): a path that is no longer what the build made is
    left, and no link put in the place of either is followed. Then each directory on the list, the deepest first, is
    removed by rmdir if it is still the one the build made; rmdir removes only an empty directory, so a directory that
    holds anything the build did not make stays, and so does everything in it and every directory above it. What
    cannot be removed is left; a failure to clear never replaces the build's own error.

    The checks are made at their time, not atomically. Another party who can write in the out while the build runs, and
    so could write or remove its files itself, can swap a directory the build made for a link: the build's later writes
    then follow that link, for the checks guard the removals and not the writes; and in the window between a path's
    check and its unlink, a file behind a link put there in that window can be removed. Closing the window needs
    handle-based calls, which Python's standard library lacks on Windows (limit 22 of docs/P1.md)."""
    directories = dict(made.directories)

    def still(path, identity, kind):
        return _unchanged(path, identity, kind) and all(
            _unchanged(d, directories[d], stat.S_ISDIR) for d in path.parents if d in directories)

    for path, identity in made.files:
        with contextlib.suppress(OSError):
            if still(path, identity, stat.S_ISREG):
                os.unlink(path)
    for path, identity in sorted(made.directories, key=lambda d: len(d[0].parts), reverse=True):
        with contextlib.suppress(OSError):
            if still(path, identity, stat.S_ISDIR):
                os.rmdir(path)


def _arguments(argv):
    if not argv or argv[0] not in ("ibm", "atlas"):
        raise AdapterError(USAGE)
    args = {"kind": argv[0], "sliced": False}
    names = {"--moth": "moth", "--out": "out", "--records": "records"}
    i = 1
    while i < len(argv):
        if argv[i] == "--slice" and not args["sliced"]:         # given twice is refused below, as any option given twice is
            args["sliced"] = True
            i += 1
        elif argv[i] in names and i + 1 < len(argv) and names[argv[i]] not in args:
            args[names[argv[i]]] = argv[i + 1]
            i += 2
        else:
            raise AdapterError(f"{argv[i]}: not an option of this command, or given twice, or without its value; {USAGE}")
    if "moth" not in args or "out" not in args or not args["moth"] or not args["out"]:
        raise AdapterError(f"--moth and --out are both needed; {USAGE}")
    return args


def _verdict(argv):
    try:
        args = _arguments(argv)
        done = build(args["kind"], args["moth"], args["out"], args.get("records"), args["sliced"])
    except AdapterError as x:
        return 2, str(x)
    except p1_generate.GuardError as g:
        r = Refused("metadata-generated", g.where, f"{g.guard}: {g.detail}")
        return 1, f"REFUSED {r.name} at {r.where}: {r.detail}"
    except Refused as r:                    # the writer's: the metadata the records make is not one it will write
        return 1, f"REFUSED {r.name} at {r.where}: {r.detail}"
    return 0, f"BUILT {argv[0]}: {done['files']} files, {done['bytes']} bytes, identity {done['identity']}"


def main(argv, out=1, err=2):
    """The exit code, after its one line is written to a descriptor, unbuffered, as `python -m qro check` writes its own."""
    try:
        code, line = _verdict(argv)
    except BaseException as x:                              # a crash, an exit or an interrupt: never a refusal
        code, line = 3, f"FAILED: the adapter itself failed, {checker.describe(x)}; this is not a verdict"
    try:
        write(out if code in (0, 1) else err, line)
    except Exception:
        return 3
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
