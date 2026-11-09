"""Helpers for P5.1's kit stage (tests/p5kit; the runner's `p5-kit`, guarded by QRO_KIT_PYTHON): the kit's interpreter started
as a child, its packages asserted first, a tagged copy of the kit's tree for the command line, and the network gate every
module lists. It names no function `test*` and no class `Test*`.

The stage's tests run in the runner's interpreter, which has no qiskit; the kit's code runs in a child, in the kit's own
environment (qiskit 2.5.2, qiskit-ibm-runtime 0.50.0, qiskit-aer 0.17.2, numpy, mpmath), which carries the sandbox's audit hook
as its sitecustomize (lead.md 2026-11-08T15:49:05Z): so what the kit writes is held to the sandbox whoever starts it. Nothing
here removes the hook, copies the environment, installs into it or runs the kit's code in another interpreter. No test reaches
a network (the gate), and none connects to IBM: the kit builds no way to."""
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "qro_kit" / "environment.lock"
TAG = "qro-kit-v0.0.1"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("P5's tests reach no network")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)


def kit_python():
    path = os.environ.get("QRO_KIT_PYTHON", "")
    assert path and Path(path).is_file(), "QRO_KIT_PYTHON names no interpreter (the stage is guarded by it)"
    return path


def child_env(**extra):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONSAFEPATH", "PYTHONPATH") and not k.startswith("GIT_")}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", **extra)
    return env


def kit_run(args, cwd=None, timeout=1800, stdin=subprocess.DEVNULL):
    """The kit's interpreter with `args` (never -S: the sandbox's hook is its sitecustomize)."""
    assert "-S" not in args
    return subprocess.run([kit_python(), *args], cwd=cwd or ROOT, capture_output=True, env=child_env(), timeout=timeout,
                          stdin=stdin)


def versions():
    code = ("import json, platform, importlib.metadata as m; print(json.dumps({'python': platform.python_version(), "
            "'pins': {d: m.version(d) for d in ('qiskit', 'qiskit-ibm-runtime', 'qiskit-aer', 'numpy', 'mpmath')}}))")
    p = kit_run(["-I", "-c", code])
    assert p.returncode == 0, p.stderr[-500:]
    return json.loads(p.stdout)


def assert_the_environment():
    got = versions()
    lock = dict(ln.split("==") for ln in LOCK.read_text(encoding="ascii").splitlines() if ln and not ln.startswith("#"))
    want = {d: lock[d] for d in got["pins"]}
    assert got["pins"] == want, f"the kit's environment is {got['pins']}, the lock's pins are {want}"
    assert got["python"].startswith("3.12.")
    return got


def git(cwd, *args):
    env = child_env(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
                    GIT_COMMITTER_EMAIL="t@example.invalid")
    r = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false", *args], cwd=cwd, env=env,
                       capture_output=True, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, (args, r.stderr[-300:])
    return r.stdout.decode("utf-8", "replace").strip()


def tagged_copy(dest, tag=TAG):
    """A git repository at dest holding this tree's qro/ and qro_kit/ (byte for byte, no bytecode) and its .gitattributes, one
    commit, and the tag: the kit as a stranger has it, a clean checkout at a tagged commit."""
    dest = Path(dest)
    dest.mkdir(parents=True)
    for name in ("qro", "qro_kit"):
        shutil.copytree(ROOT / name, dest / name, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(ROOT / ".gitattributes", dest / ".gitattributes")
    git(dest, "init", "-q", "--initial-branch=main")
    git(dest, "add", "-A")
    git(dest, "commit", "-q", "-m", "the kit")
    if tag:
        git(dest, "tag", tag)
    return dest


def kit_cli(copy, *args, timeout=1800):
    """`python -m qro_kit ARGS` in the copy's root, as a stranger runs it (the kit needs its cwd on the path, so no -I)."""
    p = kit_run(["-m", "qro_kit", *args], cwd=copy, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
