"""`freeze`: the unit's three bundles, committed and pushed before the first job (P5's design, items 1 and 3; P5.1).

    python -m qro_kit freeze --route local --out WORK [--shots-divisor N] [--contributor HANDLE]

The local route (the only one P5.1 builds) rehearses the real anchor against a throwaway origin the kit makes inside WORK:
    WORK/origin.git      a bare repository, the stand-in for the contributor's records repository's origin
    WORK/records/        its work tree, with the unit in WORK/records/unit
and commits and pushes the unit before any job exists, so that the runner's anchor (a job's line committed and pushed before
any result is read) is the real one, git and all. The crate of a local unit claims no anchor. `freeze` prints the unit's
digest, the SHA-256 of UNIT.json, which is the unit's identity, and its first 12 hex digits, which `--route real` asks for
as `--confirm` (and which P5.1 never accepts: the real route is refused `route-unsafe`).

kit-dirty runs first of everything (qro/p5_tree.py): a tree that is not a tagged commit's own bytes freezes nothing. A freeze
that fails removes what it made, and nothing else (qro_kit/crate.py's `Made`: WORK, if the freeze made it, and the two trees
it made inside).

The fake backends are run from `QiskitRuntimeLocalService`; their snapshots are dated 2026-04-15 (kingston) and 2025-02-26
(marrakesh and fez), so a local unit tests the pipeline, not the devices (design item 14, limit 4). Chain pinning
(`--chain-file`) is not built in P5.1.
"""
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from qro import p5_unit as U
from qro.refusal import Refused
from qro_kit import _qf
from qro_kit.crate import CrateError, Made

SEED = 11
BRANCH = "main"
IDENTITY = ("-c", "user.name=qro-kit", "-c", "user.email=kit@example.invalid")


class GitFailed(RuntimeError):
    """git failed in the kit's own throwaway repository: the kit failing (exit 3, no verdict), never misuse (exit 2)."""


def git(cwd, *args):
    """git in `cwd`, no console window, stdin null, the environment without its GIT_* variables; a failure is a GitFailed
    naming git's first line."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    r = subprocess.run(["git", *IDENTITY, "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false", *args], cwd=cwd,
                       capture_output=True, env=env, stdin=subprocess.DEVNULL,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode != 0:
        said = r.stderr.decode("utf-8", "replace").strip().split("\n", 1)[0][:200]
        raise GitFailed(f"git {' '.join(args[:2])} failed in the throwaway repository ({said})")
    return r.stdout.decode("utf-8", "replace").strip()


def divisor_problem(divisor):
    try:
        for kind in U.KINDS_OF_JOB:
            U.shot_count(kind, divisor)
    except ValueError as x:
        return str(x)
    return None


def freeze(out, *, route="local", divisor=1, contributor="withheld", tree, seed=SEED, log=print):
    """Freeze the unit into `out`: {"unit_dir", "unit_sha256", "confirm", ...}. `tree` is the kit-dirty check."""
    state = tree()
    if route != "local":
        raise Refused("route-unsafe", "--route", f"freeze builds the local route only; {route!r} is not built in this kit tag")
    bad = divisor_problem(divisor)
    if bad:
        raise CrateError(bad)
    if not isinstance(contributor, str) or not contributor or len(contributor) > 64 or "\n" in contributor:
        raise CrateError("--contributor is one line of text of 64 characters or fewer, a public handle, or `withheld`")
    out = Path(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise CrateError(f"{out}: exists and is not an empty directory; a unit is frozen into a new directory")
    q = _qf.load()
    source = (_qf.VENDOR / "circuit-ed767c01bd4b851d.qasm").read_text(encoding="ascii")
    if q.bundle.sha256(source.encode("ascii")) != U.SOURCE_SHA256:
        raise CrateError("the shipped source circuit is not ed767c01bd4b851d")
    from qiskit_ibm_runtime.fake_provider.local_service import QiskitRuntimeLocalService

    from qro_kit import unit_bundle
    made = Made()
    try:
        made.directory(out)
        origin, records = out / "origin.git", out / "records"
        os.mkdir(origin)
        made.adopt(origin)
        os.mkdir(records)
        made.adopt(records)
        git(origin, "init", "--bare", f"--initial-branch={BRANCH}", "-q")
        git(records, "init", f"--initial-branch={BRANCH}", "-q")
        for key, value in (("user.name", "qro-kit"), ("user.email", "kit@example.invalid"), ("commit.gpgsign", "false"),
                           ("core.autocrlf", "false")):
            git(records, "config", key, value)           # the vendored anchor runs plain git in this repository
        git(records, "remote", "add", "origin", str(origin))
        (records / ".gitattributes").write_bytes(b"* -text\n")
        git(records, "add", ".gitattributes")
        git(records, "commit", "-q", "-m", "the throwaway records repository of a local unit")
        git(records, "push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")
        unit_dir = records / "unit"
        os.mkdir(unit_dir)
        service = QiskitRuntimeLocalService()
        digests = []
        for device in U.DEVICE_SETS["simulator"]:
            log(f"freezing {device}")
            _m, digest = unit_bundle.write(unit_dir / device / "bundle", service.backend(device), "simulator", divisor, seed,
                                           source)
            digests.append(digest)
        doc = {"bundles": digests, "contributor": contributor, "devices": list(U.DEVICE_SETS["simulator"]),
               "format": U.UNIT_FORMAT, "frozen_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
               "kind": "simulator", "kit_commit": state["commit"], "kit_tag": state["tag"], "recipe": U.RECIPE_NAME,
               "recipe_sha256": U.recipe_sha256(divisor), "route": U.ROUTE, "shots_divisor": divisor}
        data = q.bundle.text(doc).encode("ascii")
        (unit_dir / "UNIT.json").write_bytes(data)
        git(records, "add", "unit")
        git(records, "commit", "-q", "-m", f"the frozen unit {q.bundle.sha256(data)[:16]}, before any job")
        git(records, "push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")
    except BaseException:
        made.clear()
        raise
    digest = q.bundle.sha256(data)
    return {"unit_dir": unit_dir, "unit_sha256": digest, "confirm": digest[:12], "kit": state, "divisor": divisor}
