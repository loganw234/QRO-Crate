"""Hosts the tests cannot make, simulated for P1.2's adapter (its fifth verifier's D2 and D3), in process or as a process.

  - `unreachable`: no path spelt with two separators at its head (a network, extended-length or device spelling) reaches
    the network. The host's calls on one are refused as an unreachable server's are, "The network path was not found",
    and os.path.realpath gives one back as it was given, as it does when the server is not there: so that no test asks
    the network, whatever the adapter does, a guard that regressed among it. Each call so refused is listed in `asked`.
  - `denied`: the host will not let the adapter look at the paths given, nor at anything under them: stat, lstat,
    listdir and scandir are refused, "Network access is denied", as this host refuses its own admin share.
  - `unreadable`: the host lets the adapter look at the paths given, and will not let it read a file under them.

As a process: python tests/p1/p1_hosts.py unreachable|denied|unreadable [PATH ...] -- ADAPTER-ARGUMENTS runs the adapter's
own main under that host, and exits with its code. A helper: nothing here is a test."""
import errno
import os
import sys
from pathlib import Path

TWO = ("\\" * 2, "/" * 2)
asked = []


def _text(p):
    try:
        s = os.fspath(p)
    except TypeError:
        return None
    return s if isinstance(s, str) else None


def far(p):
    """Whether `p` is spelt with two separators at its head."""
    s = _text(p)
    return s is not None and s[:2] in TWO


def _under(p, paths):
    s = _text(p)
    return s is not None and any(Path(s) == q or q in Path(s).parents for q in paths)


class _Set:
    """monkeypatch's setattr, for a process that has no monkeypatch."""

    @staticmethod
    def setattr(target, name, value, raising=True):
        setattr(target, name, value)


def install(kind, patch, adapter, paths=()):
    """Make the host `kind` for `adapter` (qro.p1_adapter), through `patch`, a monkeypatch or _Set."""
    paths = [Path(p) for p in paths]
    del asked[:]

    def refusing(real, when, error):
        def call(*a, **k):
            p = a[0] if a else k.get("path", k.get("file"))
            if p is not None and when(p):
                asked.append((real.__name__, _text(p)))
                raise error(_text(p))
            return real(*a, **k)
        call.__name__ = real.__name__
        return call

    if kind == "unreachable":
        def gone(s):
            return OSError(errno.ENOENT, "The network path was not found", s, 53)
        for name in ("stat", "lstat", "listdir", "scandir", "mkdir", "rmdir", "unlink"):
            patch.setattr(os, name, refusing(getattr(os, name), far, gone))
        patch.setattr(adapter, "open", refusing(open, far, gone), raising=False)
        real_realpath = os.path.realpath

        def realpath(p, *a, **k):
            if far(p):
                asked.append(("realpath", _text(p)))
                return _text(p)
            return real_realpath(p, *a, **k)
        patch.setattr(os.path, "realpath", realpath)
    elif kind == "denied":
        def refused(s):
            return OSError(errno.EACCES, "Network access is denied", s, 65)
        for name in ("stat", "lstat", "listdir", "scandir"):
            patch.setattr(os, name, refusing(getattr(os, name), lambda p: _under(p, paths), refused))
    elif kind == "unreadable":
        real_read = Path.read_bytes

        def read_bytes(self):
            if _under(self, paths):
                asked.append(("read_bytes", str(self)))
                raise PermissionError(errno.EACCES, "Access is denied", str(self))
            return real_read(self)
        patch.setattr(Path, "read_bytes", read_bytes)
    else:
        raise ValueError(f"{kind}: not a host of these")


def main(argv):
    cut = argv.index("--")
    kind, paths, args = argv[0], argv[1:cut], argv[cut + 1:]
    from qro import p1_adapter
    install(kind, _Set, p1_adapter, paths)
    return p1_adapter.main(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
