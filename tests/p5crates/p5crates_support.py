"""Helpers for P5's tests against moth-quantum (tests/p5crates; the runner's `p5-crates`, guarded by QRO_MOTH_ROOT): the
checkout, held to 3a73823 and clean, and read only. It names no function `test*` and no class `Test*`.

moth-quantum is read, never written: git runs with GIT_OPTIONAL_LOCKS=0 (not even its index is refreshed), with each call's
working directory the checkout and the variables git lists as pointing it at a repository removed."""
import os
import socket
import subprocess
from pathlib import Path

import pytest

MOTH_COMMIT = "3a73823"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("P5's tests reach no network")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    r = subprocess.run(["git", "--no-replace-objects", *args], cwd=root, capture_output=True, env=env,
                       stdin=subprocess.DEVNULL)
    assert r.returncode == 0, (args, r.stderr[-300:])
    return r.stdout


def moth_root():
    """The checkout QRO_MOTH_ROOT names, asserted to be moth-quantum at 3a73823 with nothing changed."""
    path = os.environ.get("QRO_MOTH_ROOT", "")
    assert path and Path(path).is_dir(), "QRO_MOTH_ROOT names no directory (the stage is guarded by it)"
    head = git(path, "rev-parse", "HEAD").decode().strip()
    assert head.startswith(MOTH_COMMIT), f"{path} is at {head[:7]}, and these tests read moth-quantum at {MOTH_COMMIT}"
    assert git(path, "status", "--porcelain", "--untracked-files=all") == b"", f"{path} has changes"
    return Path(path)


def committed(root, rel):
    """The bytes git holds for `rel` at HEAD: the checkout's settings (filters, attributes) are not in them."""
    return git(root, "cat-file", "blob", f"HEAD:{rel}")
