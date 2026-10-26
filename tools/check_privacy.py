#!/usr/bin/env python3
"""The privacy gate: `python tools/check_privacy.py`, and `python tools/check_privacy.py --control` to watch it fail
on each planted fault. Copied from HonestHarness's tools/check.py, its privacy check and controls (study QRO-0,
section 13's floor). It adds IBM's and Moth's credential shapes, drops HonestHarness's own key shapes and other
checks, and splits every pattern into named alternatives, each with its own planted control (P0's verifier, P0-6).

Threat model: accidental publication. A provider key or token, an IBM instance's CRN or account, a personal address
or a home-directory path, written into a tracked file or a commit message the way pasted output or a careless note
carries one (rule 3). It does not guard against deliberate evasion, and it does not judge content.

It reads every file git would commit (tracked, or untracked and not ignored; `git ls-files -z`, so no name is
quoted away), its own source included, a symbolic link as its own text, which is what git commits; the staged
version of each tracked file whose index differs from the file on disk, which a plain `git commit` takes (P0.2's
verifier, round 4); every commit message on HEAD's history; and every blob that history holds and the index does
not, which a push sends with the commits that hold it: a key committed and deleted in a later commit is pushed
(P0.4's verifier, round 4, note 1). A finding in a blob already pushed, which no commit can take back, is listed as
known where KNOWN names its blob and its alternative, each read and judged no secret. Every git it runs on a
repository runs without the variables git lists as pointing it at a repository, GIT_DIR among them, with git's
configuration (P0.2's verifier, rounds 1 and 2), and with replace refs ignored, as a push ignores them (P0.4's
verifier, round 4, note 2). git log failing is a finding unless git says the branch has no commit yet: a commit
gone, a branch ref emptied or garbage, and packed-refs corrupt among the causes (rounds 2 and 3). git log is
asked for UTF-8, which overrides i18n.logOutputEncoding, and ends each message with a NUL, so a control byte such
as 0x01 no longer splits one (round 4). A message's bytes not in UTF-8 are replaced. A file with a byte-order mark
is read in its encoding, UTF-16 and UTF-32 included. A finding is printed masked.

What it cannot see (each limit stated by the behaviour it concedes):
  - a shape no alternative at ALTERNATIVES names passes; so does a value spelled out, split across lines, or
    encoded other than as a listed alternative says;
  - an IBM API key is 44 characters of [A-Za-z0-9_-] with no fixed prefix: it is caught only after one of the names
    listed, or inside a CRN, JWT or bearer header. A Moth key is caught bare only as moth_ and twenty or more letters
    and digits, one a digit; in any other shape, only after a listed name or in a bearer header;
  - after a listed name, the white space is bounded, so that the search stays linear (round 6). A value passes
    with more than 32 white-space characters between the name and its `=` or `:`; with a quote there, more than
    16 between the name and the quote, or between the quote and the separator; or more than 16 after the
    separator, or after `Bearer` or `apikey` (MEASURED by tests/tools/test_tools.py, at each place);
  - an address in an allowed or reserved domain passes, and so does one glued to the end of it by one of an
    address's characters (ALTERNATIVES, the comment above the address patterns);
  - a binary file, one with a NUL in its first 4,096 bytes and no byte-order mark, is not read. Each is listed by
    name in the summary, so none passes unseen;
  - commit authors' and committers' names and addresses are git's metadata, not messages: not read;
  - only HEAD's history is read: another branch, a tag, a stash or a note, which `git push` sends only when asked
    to, is not; nor is a blob of HEAD's history that is binary, which is listed by name;
  - the blobs of HEAD's history that the index does not hold are read into memory at once, at about 1.5 MB/s (P0.6's
    verifier, round 1, MEASURED: 120 versions of 1 MB took 78 s and 380 MB). This repository's history takes
    seconds; the cost grows with it. In a partial clone, git fetches each blob it lacks from the promisor remote,
    and the gate fails where that remote cannot be reached;
  - a message whose commit records an encoding of its own, as i18n.commitEncoding set to UTF-16 or IBM037 writes,
    git log converts from that encoding, which can garble it, and a key in it is then lost (MEASURED by P0.4's
    verifiers: IBM037 in both rounds, UTF-16 for a message not in ASCII); and git log writes a message only up to
    a NUL it holds, which `git commit` refuses and a commit built by hand can hold, so what follows the NUL is not
    read (P0.4's verifier, round 1, MEASURED, and the lead, git 2.45.2);
  - a file whose name is not UTF-8, which Linux allows, stops the gate with an error, never a pass, where git
    lists it among the files it would commit (P0.4's verifier, round 2, MEASURED); a path of HEAD's history that is
    not UTF-8 is read, its name decoded with replacement (P0.6's verifier, round 2, MEASURED);
  - in a copy with no .git, commit messages are not read, and a symbolic link to a directory is neither read nor
    named (P0.4's verifier, round 3, MEASURED); nor are messages read where HEAD names a ref git reads as a branch
    with no commit, a ref deleted or replaced by a directory, or an emptied packed-refs, among the shapes; nor where
    a ref names a tree or a blob, which git log reads as an empty history (P0.2's verifier, round 4, MEASURED);
  - a nested repository below the tree, which git commits as a gitlink and never as its files, is named in the
    summary and not read: one git lists untracked with a trailing slash, or one the index holds as a gitlink while
    a directory, or nothing, is at its path. A file or a symbolic link at a gitlink's path is read, as `git add -A`
    commits it in the gitlink's place (P0.4's verifier, round 2, R2-1).

    python tools/check_privacy.py              # 0 = nothing found; 1 = each finding, masked
    python tools/check_privacy.py --control    # 0 = every planted fault caught by its own alternative
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ALLOWED_ADDRESSES = {"noreply@anthropic.com"}
RESERVED = re.compile(r"(?i)(^|\.)(example\.(com|org|net)|invalid|test|localhost)$")
_NAME = r"[^\W_][\w.-]*"                    # a home directory's name: Unicode letters and digits first
_KEY = r"""\s{0,16}["']?\s{0,16}[=:]\s{0,16}["']?(?:Bearer\s{1,16}|apikey\s{1,16})?[A-Za-z0-9._~+/-]{24,}"""   # bounded: a long run of space backtracked quadratically (round 6)

# (kind, name, pattern): one alternative a row, so that each has its own control below.
ALTERNATIVES = [
    ("path", "windows-home", r"(?i)(?<![A-Za-z0-9])[a-z]:[\\/]+(users|documents and settings)[\\/]+" + _NAME),
    ("path", "driveless-home", r"(?i)(?<![A-Za-z0-9.:\\])\\users\\" + _NAME),
    ("path", "git-bash-home", r"(?i)(?<![A-Za-z0-9.])/[a-z]/users/" + _NAME),
    ("path", "wsl-mount-home", r"(?i)(?<![A-Za-z0-9.])/mnt/[a-z]/users/" + _NAME),
    ("path", "cygwin-home", r"(?i)(?<![A-Za-z0-9.])/cygdrive/[a-z]/users/" + _NAME),
    ("path", "docker-host-home", r"(?i)(?<![A-Za-z0-9.])(/host_mnt|/run/desktop/mnt/host)/[a-z]/users/" + _NAME),
    ("path", "posix-home", r"(?i)(?<![A-Za-z0-9.])/(users|home)/" + _NAME),
    ("path", "backslash-home", r"(?i)(?<![A-Za-z0-9.:\\])\\home\\" + _NAME),
    ("path", "wsl-unc", r"(?i)\\\\wsl(\$|\.localhost)\\"),
    # the same with forward slashes, as Path.as_posix writes it (P0.4's verifier, round 4, note 3); not after a
    # scheme's colon or a host's characters, so a URL whose host is named wsl is not one
    ("path", "wsl-unc-slash", r"(?i)(?<![A-Za-z0-9:./])//wsl(\$|\.localhost)/"),
    # a file URL to the WSL host's home, as a browser or Path.as_uri writes it (P0.6's verifier, round 1, note)
    ("path", "wsl-file-url", r"(?i)\bfile:/*wsl(\$|%24|\.localhost)/[^/\s]+/(home|users)/" + _NAME),
    ("path", "url-quoted-home", r"(?i)%2F(users|home)%2F|[a-z]%3A(%5C|%2F)users(%5C|%2F)"),
    # a drive path percent-encoded with its colon kept, as encodeURI leaves it (round 4, note 3), after no letter or
    # digit but an escape's, as `%20` before it is (P0.6's verifier, round 1, note)
    ("path", "url-quoted-drive", r"(?i)(?:(?<=%[0-9A-F]{2})|(?<![A-Za-z0-9]))[a-z]:(%5C|%2F)+users(%5C|%2F)+" + _NAME),
    ("path", "file-url-home", r"(?i)(?<![A-Za-z0-9])[a-z]%3a/+(users|documents%20and%20settings)/+" + _NAME),
    ("path", "var-home", r"(?i)(?<![A-Za-z0-9.])/var/home/" + _NAME),
    ("path", "unc-home", r"(?i)\\\\[^\\\s]+\\(home|users)\\" + _NAME),
    ("path", "remote-uri-home", r"(?i)\b(vscode-remote|ssh|sftp|scp|smb|nfs|rsync|ftps?|file)://[^/\s]*/(home|users)/"
     + _NAME),
    # An address starts only where a run of its characters starts: started at every character of a long run, the
    # search was quadratic, 77 s for one run of 100,000 letters (P0.1's verifier, round 1, note 4.1.3). A text's
    # first address starts there anyway, and is found as before. A stated limit: an address glued to the end of the
    # one before it by one of an address's characters, as in a@x.example.com-c@y.example.org, is not found, and
    # so it passes where the one before it is allowed or reserved (P0.1's verifier, round 2, note 4.2.2).
    ("address", "address", r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}"),
    ("address", "escaped-address",
     r"(?i)(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+(\\u0040|\[at\]|\(at\))([A-Za-z0-9-]+\.)+[A-Za-z]{2,}"),
    ("key", "crn", r"(?i)crn(:|%3a|\\u003a)v1(:|%3a|\\u003a)[A-Za-z0-9:%._/\\-]*"),
    ("key", "named:QISKIT_IBM_TOKEN", r"(?i)QISKIT_IBM_TOKEN" + _KEY),
    ("key", "named:IBM_QUANTUM_TOKEN", r"(?i)IBM_QUANTUM_TOKEN" + _KEY),
    ("key", "named:IBMQ_TOKEN", r"(?i)IBMQ_TOKEN" + _KEY),
    ("key", "named:QF_IBM_KEY", r"(?i)QF_IBM_KEY" + _KEY),
    ("key", "named:api-key", r"(?i)api[_-]?key" + _KEY),
    ("key", "named:token", r"(?i)(?<![A-Za-z0-9])token" + _KEY),   # access_token= too: "_" is a word character
    ("key", "named:camelToken", r"(?<=[a-z0-9])Token(?i:" + _KEY + ")"),   # accessToken, apiToken (round 3)
    ("key", "named:x-api-key", r"(?i)x-api-key" + _KEY),
    ("key", "named:authorization", r"(?i)authorization" + _KEY),
    ("key", "bearer", r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{24,}"),
    ("key", "jwt", r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("key", "ibm-id", r"\bIBMid-[A-Za-z0-9]{6,}"),
    ("key", "ibm-service-id", r"(?i)\biam-ServiceId-[0-9a-f-]{20,}"),
    ("key", "ibm-account", r"(?i)account_?id[\"':=\s]{1,6}[0-9a-f]{32}\b|\ba/[0-9a-f]{32}\b"),
    # A Moth key: moth_ and a token of twenty or more letters and digits, one a digit at least; so an identifier
    # such as moth_quantum_files_read, with underscores, is not one.
    ("key", "moth-key", r"\bmoth_(?=[A-Za-z0-9]*[0-9])[A-Za-z0-9]{20,}\b"),
    ("key", "presigned-url", r"(?i)(X-Amz-Signature|X-Amz-Credential|X-Goog-Signature|X-Goog-Credential)="
                             r"[A-Za-z0-9%/._-]{16,}"),
    ("key", "aws-key-id", r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
]
COMPILED = [(kind, name, re.compile(p)) for kind, name, p in ALTERNATIVES]
# A placeholder a document uses for a home, such as <name>, {user}, $USER or %USERNAME%, never matches: a home
# directory's name begins with a letter or a digit (_NAME). So no placeholder list is kept.
BOMS =((b"\x00\x00\xfe\xff", "utf-32-be"), (b"\xff\xfe\x00\x00", "utf-32-le"), (b"\xef\xbb\xbf", "utf-8-sig"),
        (b"\xfe\xff", "utf-16-be"), (b"\xff\xfe", "utf-16-le"))
CHECK_MODES = ("", "--control")


def git_env():
    """The process's environment without the variables that point git at a repository: those git itself lists
    (`git rev-parse --local-env-vars`) but its configuration's, GIT_CONFIG and those beginning GIT_CONFIG_, which
    say how git reads a repository, not which. With GIT_DIR and GIT_WORK_TREE naming another repository, the gate
    read that one's file list and commit messages (P0.2's verifier, round 1, G5); dropping the configuration's too
    made git refuse a checkout it trusted only through them (round 2). Every git here runs in this, with replace
    refs ignored, as a push ignores them: with one, git log showed another message than the one pushed (P0.4's
    verifier, round 4, note 2, MEASURED)."""
    local = subprocess.run(["git", "rev-parse", "--local-env-vars"], capture_output=True, text=True,
                           check=True).stdout.split()
    drop = {k for k in local if k != "GIT_CONFIG" and not k.startswith("GIT_CONFIG_")}
    return dict({k: v for k, v in os.environ.items() if k.upper() not in drop}, GIT_NO_REPLACE_OBJECTS="1")


def in_git(root):
    """Whether root is a git checkout: its .git a directory, or a file naming one, as a linked worktree's is, where
    the parcels build (P0.2's verifier, round 4). Every place here that asks, asks this (P0.4's verifier, round 1:
    four places asked it apart, and no test told a file from a directory at three)."""
    return (root / ".git").exists()


def index(root):
    """[(mode, object id, path)]: the index's entries, `git ls-files -z --stage`."""
    listing = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--stage"], capture_output=True,
                             check=True, env=git_env()).stdout
    out = []
    for record in listing.split(b"\0"):
        if record:
            meta, path = record.split(b"\t", 1)
            mode, oid = meta.split(b" ")[:2]
            out.append((mode, oid, path.decode("utf-8")))
    return out


def files(root):
    """(files, nested): every file git would commit, tracked or untracked and not ignored; and each nested
    repository, which git commits as a gitlink, never as its files. A nested repository is told by git's own marks:
    untracked, git lists it with a trailing slash; tracked, the index holds it as a gitlink, mode 160000. Its being
    a directory says nothing: a symbolic link to a directory is one too, and so is a tracked file a directory
    replaced (P0.4's verifier, round 1). Nor does the index's mark alone: where a file or a symbolic link is at a
    gitlink's path, `git add -A` and `git commit -a` commit it in the gitlink's place, so it is read (round 2,
    R2-1). With no .git, every file below the root but in .git and the caches, and no nested repository."""
    if in_git(root):
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "-co", "--exclude-standard"],
                             capture_output=True, check=True, env=git_env()).stdout
        listed = [p.decode("utf-8") for p in out.split(b"\0") if p]
        gitlinks = {path for mode, _, path in index(root) if mode == b"160000" and held(root / path)}
        nested = sorted({p[:-1] for p in listed if p.endswith("/")} | gitlinks)
        return [root / p for p in listed if not p.endswith("/") and p not in gitlinks], [root / p for p in nested]
    skip = {".git", "__pycache__", ".pytest_cache", ".gate-state", ".ruff_cache"}
    return [Path(d) / f for d, ds, fs in os.walk(root) for f in fs
            if not (set(Path(d).relative_to(root).parts) & skip)], []


def held(p):
    """Whether a gitlink's path still holds a nested repository's place: a directory that is no symbolic link, or
    nothing at all."""
    return not os.path.lexists(p) or (p.is_dir() and not p.is_symlink())


def committed(p):
    """The bytes git commits for the path p: a symbolic link's own text, never what it points to; else the file's
    bytes. The gate read through a symbolic link, so a home path one names passed, and one to a directory was taken
    for a nested repository (P0.4's verifier, round 1). A named pipe or a device, neither a file, a directory nor a
    link, is an OSError, unreadable: read, a pipe with no writer held the gate for ever (round 3, MEASURED under
    WSL), and git refuses to add one."""
    if p.is_symlink():
        return os.fsencode(os.readlink(p))
    if p.exists() and not p.is_file() and not p.is_dir():
        raise OSError(f"{p.name}: a named pipe or a device, not a file")
    return p.read_bytes()


def read(p):
    """(text, None), or (None, why it was not read)."""
    try:
        data = committed(p)
    except OSError as e:
        return None, f"unreadable: {type(e).__name__}"
    return decode(data)


def decode(data):
    """A file's bytes as text, in the encoding its byte-order mark names, else UTF-8; or (None, "binary")."""
    for bom, enc in BOMS:
        if data.startswith(bom):
            return data[len(bom):].decode(enc.replace("-sig", ""), errors="replace"), None
    if b"\0" in data[:4096]:
        return None, "binary"
    return data.decode("utf-8", errors="replace"), None


def staged(root):
    """[(path, bytes or None)]: each staged version that differs from its file on disk, or whose file is gone, its
    bytes None where its object is missing; or None where git cannot read the index's objects at all, a corrupt
    packed-refs among the causes, which check() makes a finding. A plain `git commit` takes the index, so a key
    staged and then edited out of its file would be committed though the file no longer shows it (P0.2's
    verifier, round 4). One `git cat-file --batch` reads them all."""
    # a gitlink names another repository's commit, and no blob here
    entries = [(path, oid) for mode, oid, path in index(root) if mode != b"160000"]
    if not entries:
        return []
    run = subprocess.run(["git", "-C", str(root), "cat-file", "--batch"],
                         input=b"".join(oid + b"\n" for _, oid in entries), capture_output=True, env=git_env())
    if run.returncode != 0:
        return None
    batch, out, at = run.stdout, [], 0
    for path, oid in entries:
        end = batch.index(b"\n", at)
        header = batch[at:end].split(b" ")
        if header[1:] == [b"missing"]:
            out.append((path, None))
            at = end + 1
            continue
        size = int(header[2])
        data, at = batch[end + 1:end + 1 + size], end + 1 + size + 1
        try:
            disk = committed(root / path)
        except OSError:
            disk = None
        if data != disk:
            out.append((path, data))
    return out


# Findings in blobs already pushed, which no commit can take back, each read and judged no secret: the blob's id and
# the alternative that finds it, and why. Reading earlier commits, the gate lists each as known, never as a failure.
# A file's current bytes have no such list, since a file can be changed. tests/tools holds that each entry's
# alternative finds something in its blob wherever git holds the blob; in a copy whose history does not reach the
# blob, a shallow clone or a fresh git init, an entry is inert (P0.6).
KNOWN = {
    ("7671e68acfe2ba1b0cd39a5b050e10523eb811c7", "wsl-unc-slash"):
        "P0.4's fourth verifier's example, in docs/reviews/P0.4/round4.md as pushed in 20d40e6, of a spelling the gate "
        "then missed: the name in it is the placeholder `name`",
    ("7671e68acfe2ba1b0cd39a5b050e10523eb811c7", "url-quoted-drive"):
        "P0.4's fourth verifier's example, in docs/reviews/P0.4/round4.md as pushed in 20d40e6, of a spelling the gate "
        "then missed: the name in it is the placeholder `name`",
}


def history(root):
    """[(path, object id, bytes or None)]: each blob HEAD's history holds that the index does not, by the first path git
    lists it at, its bytes None where git does not hold its object, which is a finding; or None where git cannot
    list or read the history. git rev-list fails on a blob whose object is missing, so it is a finding that way
    first (MEASURED); one git lists and then does not hold, as an object removed between the two calls, is read as
    missing, never passed over. A push sends every commit's tree, so a key committed and deleted in a later commit
    is pushed, though no file and no staged version holds it (P0.4's verifier, round 4, note 1, MEASURED). `git
    rev-list --objects` lists them, and `git cat-file --batch` reads them, once each. git lists a path cut at its
    first line feed, so a top-level name that begins with one is listed empty, as the root tree is, and is kept and
    named for what it is (P0.6's verifier, round 1, D1: such a blob was dropped with the root tree, and a key in it
    passed). The revision is ended by `--`, so that a file or a directory named HEAD at the root is no second
    reading of it (D2: git then refused the listing, and a clean tree failed)."""
    listing = subprocess.run(["git", "-C", str(root), "rev-list", "--objects", "HEAD", "--"], capture_output=True,
                             env=git_env())
    if listing.returncode != 0:
        return None
    named = {}
    for line in listing.stdout.split(b"\n"):          # `oid` for a commit; `oid path` for a tree or a blob, its
        oid, space, path = line.partition(b" ")         # path cut at its first line feed, so empty for the root
        if re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", oid) and space:     # tree and for a name beginning with one
            named.setdefault(oid, path.decode("utf-8", errors="replace") or "(a path beginning with a line feed)")
    indexed = {oid for _, oid, _ in index(root)}
    types = subprocess.run(["git", "-C", str(root), "cat-file", "--batch-check"],
                           input=b"".join(oid + b"\n" for oid in named), capture_output=True, env=git_env())
    if types.returncode != 0:
        return None
    blobs = [line.split(b" ")[0] for line in types.stdout.split(b"\n")
             if line.split(b" ")[1:2] in ([b"blob"], [b"missing"]) and line.split(b" ")[0] not in indexed]
    if not blobs:
        return []
    run = subprocess.run(["git", "-C", str(root), "cat-file", "--batch"], input=b"".join(o + b"\n" for o in blobs),
                         capture_output=True, env=git_env())
    if run.returncode != 0:
        return None
    batch, out, at = run.stdout, [], 0
    for oid in blobs:
        end = batch.index(b"\n", at)
        header = batch[at:end].split(b" ")
        if header[1:] == [b"missing"]:
            out.append((named[oid], oid.decode("ascii"), None))
            at = end + 1
            continue
        size = int(header[2])
        out.append((named[oid], oid.decode("ascii"), batch[end + 1:end + 1 + size]))
        at = end + 1 + size + 1
    return out


def mask(s):
    return s[:4] + "..." + f"[{len(s)} chars]"


def findings(text, alternatives=None):
    out = []
    for kind, name, pat in COMPILED:
        if alternatives is not None and name not in alternatives:
            continue
        for m in pat.finditer(text):
            s = m.group(0)
            if kind == "address":
                domain = re.split(r"@|\\u0040|\[at\]|\(at\)", s, flags=re.I)[-1].lower()
                if s.lower() in ALLOWED_ADDRESSES or RESERVED.search(domain):
                    continue
            out.append((kind, name, s))
    return out


def check(root):
    bad, unread, known, n, staged_read, history_read = [], [], [], 0, 0, 0
    listed, repositories = files(root)
    # a nested repository, which git commits as a gitlink (P0.2's verifier, round 4)
    nested = [f"{p.relative_to(root).as_posix()}/: a nested repository, committed as a gitlink, never as its files"
              for p in repositories]
    for p in listed:
        rel = p.relative_to(root).as_posix()
        text, why = read(p)
        if text is None:
            (unread if why == "binary" else bad).append(f"{rel}: {why}")
            continue
        n += 1
        for kind, name, s in findings(text):
            bad.append(f"{rel}: a {kind} ({name}), {mask(s)}")
    if in_git(root):
        versions = staged(root)
        if versions is None:
            bad.append("staged versions: unread, as git cat-file failed")
        for path, data in versions or []:
            text, why = (None, "unreadable: its object missing") if data is None else decode(data)
            if text is None:
                (unread if why == "binary" else bad).append(f"{path} (staged): {why}")
                continue
            staged_read += 1
            for kind, name, s in findings(text):
                bad.append(f"{path} (staged): a {kind} ({name}), {mask(s)}")
    msgs = 0
    if in_git(root):
        r = subprocess.run(["git", "-C", str(root), "log", "-z", "--encoding=UTF-8", "--format=%H%n%B"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(git_env(), LC_ALL="C"))
        # Only an unborn branch is no history, as git says it in the C locale; anything else that fails git log is
        # a finding (P0.2's verifier, round 3: HEAD's rev-parse fails for a broken ref as for an unborn one).
        if r.returncode != 0 and "does not have any commits yet" not in r.stderr:
            bad.append("commit messages: unread, as git log failed")
        for entry in r.stdout.split("\x00") if r.returncode == 0 else []:
            sha, line_feed, body = entry.partition("\n")
            if not line_feed:
                continue
            msgs += 1
            for kind, name, s in findings(body):
                bad.append(f"commit {sha.strip()[:7]}: a {kind} ({name}), {mask(s)}")
        if r.returncode == 0 and msgs:
            blobs = history(root)
            if blobs is None:
                bad.append("earlier commits' files: unread, as git could not list or read them")
            for path, oid, data in blobs or []:
                text, why = (None, "unreadable: its object missing") if data is None else decode(data)
                if text is None:
                    (unread if why == "binary" else bad).append(f"{path} (history {oid[:7]}): {why}")
                    continue
                history_read += 1
                for kind, name, s in findings(text):
                    if (oid, name) in KNOWN:
                        known.append(f"{path} (history {oid[:7]}): a {kind} ({name}), {mask(s)}: {KNOWN[oid, name]}")
                    else:
                        bad.append(f"{path} (history {oid[:7]}): a {kind} ({name}), {mask(s)}")
    summary = f"{n} files and {msgs} commit messages read; {len(unread)} binary files not read"
    if staged_read:
        summary += f"; {staged_read} staged versions that differ from their files read"
    if history_read:
        summary += f"; {history_read} versions in earlier commits read"
    return bad, summary + "".join(f"\n  not read: {u}" for u in unread + nested) + "".join(
        f"\n  known, in a pushed commit: {k}" for k in known)


# -- controls: each alternative, and each way of finding a file, watched to fail ---------------------------------
# Each plant is built at run time, so this file's own source holds none of them: the gate reads this file too.
H, S = "Ab3x" * 11, "0f" * 16
PLANTS = {
    "windows-home": "see " + "C:" + "\\" + "Users" + "\\" + "someone\\x.txt",
    "driveless-home": "see " + "\\" + "Users" + "\\" + "someone\\x",
    "git-bash-home": "see /c/" + "Users" + "/someone/x",
    "wsl-mount-home": "see /mnt/c/" + "Users" + "/someone/x",
    "cygwin-home": "see /cygdrive/c/" + "Users" + "/someone/x",
    "docker-host-home": "see /host_mnt/c/" + "Users" + "/someone/x",
    "posix-home": "see /" + "home" + "/someone/x",
    "backslash-home": "see " + "\\" + "home" + "\\" + "someone",
    "wsl-unc": "see " + "\\\\" + "wsl$" + "\\Ubuntu\\x",
    "wsl-unc-slash": "see " + "//" + "wsl$" + "/Ubuntu/home/someone",
    "url-quoted-home": "path=" + "%2F" + "Users" + "%2Fsomeone",
    "url-quoted-drive": "see C:" + "%5C" + "Users" + "%5Csomeone",
    "wsl-file-url": "see file:" + "//" + "wsl.localhost" + "/Ubuntu/" + "home" + "/someone",
    "file-url-home": "see file:///c" + "%3A" + "/" + "Users" + "/someone/x",
    "var-home": "see /var/" + "home" + "/someone/x",
    "unc-home": "see " + "\\\\" + "server" + "\\" + "home" + "\\" + "someone",
    "remote-uri-home": "see vscode-remote://ssh-remote+box" + "/" + "home" + "/someone/x",
    "address": "mail someone" + "@" + "personal-domain.net",
    "escaped-address": "mail someone" + "\\u0040" + "personal-domain.net",
    "crn": "instance " + "crn" + "%3Av1%3Abluemix%3Apublic",
    "named:QISKIT_IBM_TOKEN": "QISKIT_IBM_" + "TOKEN=" + H,
    "named:IBM_QUANTUM_TOKEN": "IBM_QUANTUM_" + "TOKEN: " + H,
    "named:IBMQ_TOKEN": "IBMQ_" + "TOKEN=" + H,
    "named:QF_IBM_KEY": "QF_IBM_" + "KEY=" + H,
    "named:api-key": '"api' + 'key": "' + H + '"',
    "named:token": "access_" + "token" + " = " + H,
    "named:camelToken": "access" + "Token: " + H,
    "named:x-api-key": "X-API" + "-Key: " + H,
    "named:authorization": "Authorization" + ": " + H,
    "bearer": "header: " + "Bearer " + H,
    "jwt": "eyJ" + "hbGciOiJSUzI1NiJ9" + "." + "eyJzdWIiOiJ4In0x" + "." + "c2lnbmF0dXJlMTIz",
    "ibm-id": "user " + "IBMid" + "-6600012345",
    "ibm-service-id": "iam-" + "ServiceId-" + "0123abcd-4567-89ef-0123-456789abcdef",
    "ibm-account": '"account' + '_id": "' + S + '"',
    "moth-key": "moth_" + "abcdef0123456789xyzQW",
    "presigned-url": "?X-Amz-" + "Signature=" + "0123456789abcdef0123",
    "aws-key-id": "AKIA" + "ABCDEFGHIJKLMNOP",
}


def _copy(root, dest):
    """What the gate reads of root, each file's committed bytes, a symbolic link's text among them, as a plain file;
    a nested repository, not read, is not copied. A copy made through a symbolic link, as a mutant of this made
    it, stops the controls with IsADirectoryError at one to a directory (P0.4's verifier, round 2, N4, MEASURED
    under WSL)."""
    for p in files(root)[0]:
        t = dest / p.relative_to(root)
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_bytes(committed(p))
    return dest


FILE_CONTROLS = [
    ("a key in a UTF-16 file with its byte-order mark", lambda r: (r / "notes.md").write_bytes(
        "﻿QISKIT_IBM_TOKEN=".encode("utf-16-le") + H.encode("utf-16-le"))),
    ("a key in a file whose name is not ASCII", lambda r: (r / "café.md").write_text(
        "QISKIT_IBM_" + "TOKEN=" + H + "\n", encoding="utf-8")),
    ("a home path pasted into the gate itself", lambda r: (r / "tools" / "check_privacy.py").write_text(
        (r / "tools" / "check_privacy.py").read_text(encoding="utf-8") + "# pasted: /home/" + "someone/x\n",
        encoding="utf-8")),
]


def control(root):
    if check(root)[0]:
        print("CONTROL REFUSED: the tree fails before any plant")
        return 1
    missing = sorted({n for _, n, _ in ALTERNATIVES} - set(PLANTS)) + sorted(set(PLANTS) - {n for _, n, _ in
                                                                                             ALTERNATIVES})
    for m in missing:
        print(f"control  {m:42} NO PLANT, or a plant naming no alternative")
    caught = 0
    for name, text in PLANTS.items():
        ok = any(n == name for _, n, _ in findings(text, {name}))
        print(f"control  {name:42} {'caught' if ok else 'NOT CAUGHT'}")
        caught += ok
    for what, plant in FILE_CONTROLS:
        with tempfile.TemporaryDirectory() as td:
            r = _copy(root, Path(td) / "copy")
            if in_git(root):
                subprocess.run(["git", "-C", str(r), "init", "-q"], check=True, env=git_env())
            plant(r)
            ok = any(": a " in b for b in check(r)[0])   # a key or a path found, never a file unread (P0.2's
            # verifier, round 3: with -z dropped, the name not in ASCII was unreadable, and that passed for caught)
        print(f"control  {what:42} {'caught' if ok else 'NOT CAUGHT'}")
        caught += ok
    total = len(PLANTS) + len(FILE_CONTROLS)
    print(f"controls: {caught} of {total} caught"
          + ("; every alternative has its own plant" if not missing else f"; {len(missing)} unpaired"))
    return 0 if caught == total and not missing else 1


def run(root):
    bad, summary = check(root)
    print(f"privacy {'ok' if not bad else 'FAIL'}: {summary}")
    for b in bad[:40]:
        print(f"  {b}")
    return 1 if bad else 0


if __name__ == "__main__":
    # a name the output's code page cannot write is written as its escape, never a crash. Before P0.6 only a file in
    # the tree could carry one; the history reader lets a file of an earlier commit carry one too (P0.6's verifier,
    # round 2, D1, MEASURED: a tree that 8afeede's gate passed failed, a binary file named in CJK characters listed
    # and stdout redirected in cp1252). Where stdout cannot be reconfigured, it is left as it is: None, under pythonw
    # or a closed descriptor, where print writes nothing, or a console's stream with no reconfigure (round 3, D1,
    # MEASURED: reconfiguring it raised AttributeError, and a clean tree failed)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    sys.exit(control(ROOT) if "--control" in sys.argv[1:] else run(ROOT))
