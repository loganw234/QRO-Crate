#!/usr/bin/env python3
"""The privacy gate: `python tools/check_privacy.py`, and `python tools/check_privacy.py --control` to watch it fail
on each planted fault. Copied from HonestHarness's tools/check.py, its privacy check and controls (study QRO-0,
section 13's floor). It adds IBM's and Moth's credential shapes, drops HonestHarness's own key shapes and other
checks, and splits every pattern into named alternatives, each with its own planted control (P0's verifier, P0-6).

Threat model: accidental publication. A provider key or token, an IBM instance's CRN or account, a personal address
or a home-directory path, written into a tracked file or a commit message the way pasted output or a careless note
carries one (rule 3). It does not guard against deliberate evasion, and it does not judge content.

It reads every file git would commit (tracked, or untracked and not ignored; `git ls-files -z`, so no name is
quoted away), its own source included, and every commit message on HEAD's history. A file with a byte-order mark
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
  - in a copy with no git history, commit messages are not read.

    python tools/check_privacy.py              # 0 = nothing found; 1 = each finding, masked
    python tools/check_privacy.py --control    # 0 = every planted fault caught by its own alternative
"""
import os
import re
import shutil
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
    ("path", "url-quoted-home", r"(?i)%2F(users|home)%2F|[a-z]%3A(%5C|%2F)users(%5C|%2F)"),
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


def files(root):
    if (root / ".git").exists():
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "-co", "--exclude-standard"],
                             capture_output=True, check=True).stdout
        return [root / p.decode("utf-8") for p in out.split(b"\0") if p]
    skip = {".git", "__pycache__", ".pytest_cache", ".gate-state", ".ruff_cache"}
    return [Path(d) / f for d, ds, fs in os.walk(root) for f in fs if not (set(Path(d).relative_to(root).parts) & skip)]


def read(p):
    """(text, None), or (None, why it was not read)."""
    try:
        data = p.read_bytes()
    except OSError as e:
        return None, f"unreadable: {type(e).__name__}"
    for bom, enc in BOMS:
        if data.startswith(bom):
            return data[len(bom):].decode(enc.replace("-sig", ""), errors="replace"), None
    if b"\0" in data[:4096]:
        return None, "binary"
    return data.decode("utf-8", errors="replace"), None


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
    bad, unread, n = [], [], 0
    for p in files(root):
        text, why = read(p)
        rel = p.relative_to(root).as_posix()
        if text is None:
            (unread if why == "binary" else bad).append(f"{rel}: {why}")
            continue
        n += 1
        for kind, name, s in findings(text):
            bad.append(f"{rel}: a {kind} ({name}), {mask(s)}")
    msgs = 0
    if (root / ".git").exists():
        r = subprocess.run(["git", "-C", str(root), "log", "--format=%H%x00%B%x01"], capture_output=True, text=True,
                           encoding="utf-8")
        for entry in r.stdout.split("\x01") if r.returncode == 0 else []:
            if "\x00" not in entry:
                continue
            sha, body = entry.split("\x00", 1)
            msgs += 1
            for kind, name, s in findings(body):
                bad.append(f"commit {sha.strip()[:7]}: a {kind} ({name}), {mask(s)}")
    summary = f"{n} files and {msgs} commit messages read; {len(unread)} binary files not read"
    return bad, summary + "".join(f"\n  not read: {u}" for u in unread)


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
    "url-quoted-home": "path=" + "%2F" + "Users" + "%2Fsomeone",
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
    for p in files(root):
        t = dest / p.relative_to(root)
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, t)
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
            if (root / ".git").exists():
                subprocess.run(["git", "-C", str(r), "init", "-q"], check=True)
            plant(r)
            ok = bool(check(r)[0])
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
    sys.exit(control(ROOT) if "--control" in sys.argv[1:] else run(ROOT))
