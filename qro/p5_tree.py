"""`kit-dirty`: the kit starts only from the bytes of a tagged commit (P5's design, item 7; P5.1). Standard library only.

`tree_state(root, code=())` is called by the kit's `freeze`, `drive` and `crate` before anything else, and returns
{"commit", "tag", "tags"} or raises `Refused("kit-dirty", ...)`. "Dirty" is decided from the bytes on disk against HEAD's
tree, never from `git status` (P1.2's lesson, docs/P1.md): `core.fsmonitor`, assume-unchanged, skip-worktree, ignore rules,
`core.excludesFile`, attributes and filters can each make `git status` say what is not so. The root is clean when:
  D1  every path of HEAD's tree (`git ls-tree -r -z --full-tree HEAD`) is a mode 100644 or 100755 entry (a link or a
      submodule is dirty) and a regular file on disk whose bytes hash as git's blob id (SHA-1 or SHA-256 by the id's
      length), each read once;
  D2  every other entry below the root, a directory aside, is a path of HEAD's tree, whatever an ignore rule,
      `.git/info/exclude`, `core.excludesFile` or `status.showUntrackedFiles` says. `.git` (the root's own) and any
      `__pycache__` directory are not walked: running Python compiles files, and the kit starts with
      `sys.dont_write_bytecode` set. A directory that is a link or a junction is an entry, so it is dirty;
  D3  `git ls-files -v` marks no file other than `H`: not assume-unchanged (lowercase), not skip-worktree (`S`);
  D4  every git call runs with `--no-optional-locks`, `--no-replace-objects` and `-c core.fsmonitor=false`, with every
      GIT_* variable removed from its environment (GIT_DIR, GIT_WORK_TREE and GIT_INDEX_FILE among them), stdin null, no
      console window, and its output read as bytes. The root must be the top of its work tree;
  D5  the code running is the tree's: each path in `code` (the kit passes `qro.__file__` and `qro_kit.__file__`) lies
      under the root;
  D6  tagged: `git tag --points-at HEAD` holds a name matching TAG_PATTERN (the lead's pattern); the highest such name is
      recorded.
A git that cannot be started is the tool failing (FileNotFoundError); a git that fails on the root (not a repository, an
unborn HEAD, a refusal for another owner) is a root the kit cannot show clean, so it is refused. Stated limits (design
item 14): a tag is a local ref, and a stranger can tag any commit; whether the tag is the project's is a reader's
comparison with the public repository. The `__pycache__` skip is the one place a file is ignored by name. SHA-256
repositories are held by the id's length (BELIEVED; none tried).
"""
import hashlib
import os
import re
import stat
import subprocess
from pathlib import Path

from qro.refusal import Refused

TAG_PATTERN = r"^qro-kit-v[0-9]+\.[0-9]+\.[0-9]+$"
FILE_MODES = ("100644", "100755")
GIT = ("git", "--no-optional-locks", "--no-replace-objects", "-c", "core.fsmonitor=false")


def _dirty(where, detail):
    return Refused("kit-dirty", where, detail)


def git(root, *args):
    """git's stdout in `root`, as bytes, under D4's rules. FileNotFoundError (no git) is the tool's failure; a failing git
    is a root the kit cannot show clean."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        r = subprocess.run([*GIT, *args], cwd=root, capture_output=True, env=env, stdin=subprocess.DEVNULL,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except FileNotFoundError:
        raise
    except OSError as x:
        raise _dirty(str(root), f"git cannot start in it ({type(x).__name__})") from None
    if r.returncode != 0:
        said = r.stderr.decode("utf-8", "replace").strip().split("\n", 1)[0][:200]
        raise _dirty(str(root), f"git {' '.join(args)} failed, so the tree cannot be shown clean (git said: {said})")
    return r.stdout


def blob_id(data, size):
    """git's id of a blob holding `data`: SHA-1 for an id of 40 characters, SHA-256 for 64; None for any other length."""
    name = {40: "sha1", 64: "sha256"}.get(size)
    if name is None:
        return None
    h = hashlib.new(name, b"blob %d\0" % len(data))
    h.update(data)
    return h.hexdigest()


def head_tree(root):
    """{path as text: (mode, object id)} of every entry of HEAD's tree."""
    out = {}
    for entry in git(root, "ls-tree", "-r", "-z", "--full-tree", "HEAD").split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        mode, _kind, oid = meta.decode("ascii").split(" ")
        try:
            out[path.decode("utf-8")] = (mode, oid)
        except UnicodeDecodeError:
            raise _dirty(path.decode("utf-8", "replace"), "a path of HEAD's tree that is not UTF-8") from None
    return out


def _regular(path):
    """Whether `path` is a regular file and no link: an lstat, no reparse point."""
    st = os.lstat(path)
    return stat.S_ISREG(st.st_mode) and not getattr(st, "st_file_attributes", 0) & getattr(
        stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)


def _is_link(path):
    st = os.lstat(path)
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & getattr(
        stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _held_to_head(root, tree):
    """D1: every tracked path is a regular file whose bytes are HEAD's blob."""
    for rel, (mode, oid) in sorted(tree.items()):
        if mode not in FILE_MODES:
            raise _dirty(rel, f"HEAD's tree holds this as mode {mode}: a link, a submodule or something else, not a file")
        path = root.joinpath(*rel.split("/"))
        try:
            if not _regular(path):
                raise _dirty(rel, "a tracked file that is not a regular file on disk")
            data = path.read_bytes()
        except FileNotFoundError:
            raise _dirty(rel, "a tracked file that is not on disk") from None
        have = blob_id(data, len(oid))
        if have != oid:
            raise _dirty(rel, "the bytes on disk are not HEAD's blob for this path")


def _nothing_else(root, tree):
    """D2: every entry below the root, but a directory, is a path of HEAD's tree."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        here = Path(dirpath)
        keep = []
        for d in sorted(dirnames):
            if d == "__pycache__" or (here == root and d == ".git"):
                continue
            if _is_link(here / d):
                rel = (here / d).relative_to(root).as_posix()
                raise _dirty(rel, "a link or a junction to a directory, which HEAD's tree does not hold")
            keep.append(d)
        dirnames[:] = keep
        for name in sorted(filenames):
            rel = (here / name).relative_to(root).as_posix()
            if rel not in tree:
                raise _dirty(rel, "a file on disk that HEAD's tree does not hold (untracked, whatever an ignore rule says)")


def _marks(root):
    """D3: `git ls-files -v` marks every file H."""
    for entry in git(root, "ls-files", "-v", "-z").split(b"\0"):
        if entry and entry[:2] != b"H ":
            raise _dirty(entry[2:].decode("utf-8", "replace"),
                         f"marked {entry[:1].decode('ascii', 'replace')!r} (assume-unchanged or skip-worktree), which "
                         "`git status` cannot see")


def _tags(root):
    """D6: the tags on HEAD that match the pattern, lowest to highest."""
    names = git(root, "tag", "--points-at", "HEAD").decode("utf-8", "replace").split("\n")
    found = [n for n in names if n and re.search(TAG_PATTERN, n, re.ASCII)]
    return sorted(found, key=lambda n: tuple(int(x) for x in n[len("qro-kit-v"):].split(".")))


def tree_state(root, code=()):
    """{"commit": the 40 (or 64) hex digits of HEAD, "tag": the highest matching tag, "tags": all of them}, or
    Refused("kit-dirty") at the first of D1 to D6 that fails."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise _dirty(str(root), "no such directory")
    top = git(root, "rev-parse", "--show-toplevel").decode("utf-8", "replace").strip()
    if Path(top).resolve() != root:
        raise _dirty(str(root), "not the top of a git work tree")
    commit = git(root, "rev-parse", "HEAD").decode("ascii", "replace").strip()
    tree = head_tree(root)
    _held_to_head(root, tree)
    _nothing_else(root, tree)
    _marks(root)
    for c in code:
        try:
            Path(c).resolve().relative_to(root)
        except ValueError:
            raise _dirty(str(c), "the code running is not the tree's: it lies outside the root") from None
    tags = _tags(root)
    if not tags:
        raise _dirty(commit[:12], "HEAD carries no tag matching " + TAG_PATTERN)
    return {"commit": commit, "tag": tags[-1], "tags": tags}
