"""The driver's rules on stand-ins, run by tests/p5kit/test_p5kit_drive.py in the kit's interpreter (never collected: its name
is no test's). It freezes one local unit, then asks the real driver (qro_kit/drive.py, the vendored runner, the real bundle
checks) to go wrong in the ways S1 to S7 and the cleanups name, with a stand-in service and a counting `submit.send`, and prints
one JSON document: for each scenario the refusal (name, where, detail) and what changed in the unit's directory.

    python p5kit_standin.py ROOT WORK       # ROOT holds qro/ and qro_kit/; WORK does not exist yet

No network is reached and nothing connects to IBM: the stand-in service answers from memory."""
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT, WORK = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from qro import p5_generate  # noqa: E402
from qro.refusal import Refused  # noqa: E402
from qro_kit import crate, drive, freeze, submit, unit_bundle  # noqa: E402
from qro_kit.crate import CrateError  # noqa: E402

STATE = {"commit": "0123456789abcdef0123456789abcdef01234567", "tag": "qro-kit-v0.0.1", "tags": ["qro-kit-v0.0.1"]}
NOW = datetime(2026, 11, 8, 12, 0, 0, tzinfo=timezone.utc)
OUT = {}
SENT = []


def tree():
    return STATE


def listing(root):
    root = Path(root)
    return sorted((p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "dir")
                  for p in root.rglob("*") if ".git" not in p.relative_to(root).parts)


def refusal(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Refused as r:
        return {"name": r.name, "where": r.where, "detail": r.detail[:300]}
    except CrateError as x:
        return {"misuse": str(x)[:300]}
    return {"accepted": True}


class Service:
    """A stand-in service: answers from memory, counts every call, submits nothing."""

    def __init__(self, usage=None, plan="open", backend=None):
        self.calls = []
        self._usage = usage if usage is not None else {"usage_remaining_seconds": 400, "usage_limit_ru": 10,
                                                      "usage_consumed_ru": 5}
        self._plan, self._backend = plan, backend

    def usage(self):
        self.calls.append("usage")
        return self._usage

    def active_instance(self):
        self.calls.append("active_instance")
        return "an-instance"

    def instances(self):
        self.calls.append("instances")
        return [{"crn": "an-instance", "plan": self._plan, "pricing_type": "free"}]

    def backend(self, name):
        self.calls.append(f"backend {name}")
        return self._backend(name) if self._backend else SimpleNamespace(name=name, configuration=lambda: SimpleNamespace(
            simulator=True))


def counting_send(*args, **kwargs):
    SENT.append(1)
    raise AssertionError("a job was sent")


submit.send = counting_send


def write_preflight(unit, at, holds="holds", digest=None):
    folder = Path(unit).parent / "preflight"
    folder.mkdir(exist_ok=True)
    stamp = at.strftime("%Y-%m-%dT%H:%M:%SZ")
    (folder / (at.strftime("%Y%m%dT%H%M%SZ") + ".json")).write_bytes(json.dumps(
        {"format": submit.PREFLIGHT_FORMAT, "unit_sha256": digest, "holds": holds, "at": stamp}).encode("ascii"))


# -- freeze ---------------------------------------------------------------------------------------------------------------------------
done = freeze.freeze(WORK, divisor=128, tree=tree, log=lambda s: None)
UNIT, DIGEST = done["unit_dir"], done["unit_sha256"]
OUT["frozen"] = {"digest": DIGEST, "confirm": done["confirm"], "listing_before": len(listing(UNIT))}
BEFORE = listing(UNIT)

real_read_unit = drive.read_unit
cached = {}


def memo_read_unit(unit_dir, source, divisor_hint=None):
    if "r" not in cached:
        cached["r"] = real_read_unit(unit_dir, source, divisor_hint)
    return cached["r"]


drive.read_unit = memo_read_unit

# -- the real route, S7 and S1 to S6 ----------------------------------------------------------------------------------------------------
from qiskit_ibm_runtime import IBMBackend  # noqa: E402


class AnIbmBackend(IBMBackend):
    """An IBMBackend that is not one from the service: its kind is qpu, and a simulator unit binds simulator."""

    def __init__(self, name):
        self._the_name = name

    @property
    def name(self):
        return self._the_name

    def configuration(self):
        return SimpleNamespace(simulator=False)


def real(**kw):
    args = dict(route="real", flag=True, confirm=DIGEST[:12], tree=tree, now=NOW, service=None)
    args.update(kw)
    return refusal(drive.drive, UNIT, **args)


scenes = {}
scenes["no flag"] = real(flag=False)
scenes["no confirm"] = real(confirm=None)
scenes["wrong confirm"] = real(confirm="0" * 12)
scenes["no preflight"] = real()
write_preflight(UNIT, NOW - timedelta(hours=25), digest=DIGEST)
scenes["stale preflight"] = real()
write_preflight(UNIT, NOW - timedelta(hours=1), holds="withheld", digest=DIGEST)
scenes["failing preflight"] = real()
write_preflight(UNIT, NOW - timedelta(minutes=30), digest=DIGEST)         # the newest holds
scenes["no service"] = real()
svc = Service(usage={"usage_remaining_seconds": 215, "usage_limit_ru": 10, "usage_consumed_ru": 5})
scenes["S2 seconds"] = real(service=svc)
OUT["S2 calls"] = svc.calls
svc = Service(usage={"usage_remaining_seconds": 400, "usage_limit_ru": 10, "usage_consumed_ru": "6.7"})
scenes["S2 resource units"] = real(service=svc)
svc = Service(plan="pay-as-you-go")
scenes["S5 plan"] = real(service=svc)
svc = Service(backend=AnIbmBackend)
scenes["S6 kind"] = real(service=svc)
svc = Service()
scenes["all clear"] = real(service=svc)
OUT["all clear calls"] = svc.calls
scenes["dirty tree"] = refusal(drive.drive, UNIT, route="real", flag=True, confirm=DIGEST[:12], tree=lambda: (_ for _ in ()).throw(
    Refused("kit-dirty", "a.txt", "dirty")), service=Service(), now=NOW)
OUT["real scenes"] = scenes
OUT["sent after the real route"] = len(SENT)
OUT["unit changed by the real route"] = listing(UNIT) != BEFORE

# -- the local route's refusals -----------------------------------------------------------------------------------------------------------
local = {}
local["unknown route"] = refusal(drive.drive, UNIT, route="elsewhere", tree=tree)
local["another commit"] = refusal(drive.drive, UNIT, route="local", tree=lambda: dict(STATE, commit="f" * 40))
OUT["local after misuse"] = {"sent": len(SENT), "unit changed": listing(UNIT) != BEFORE}

real_permit = submit.permit
submit.permit = lambda *a, **kw: (_ for _ in ()).throw(Refused("spend-unit", "control", "a rule refuses"))
local["rule before the first job"] = refusal(drive.drive, UNIT, route="local", tree=tree)
submit.permit = real_permit
OUT["local after a rule"] = {"sent": len(SENT), "unit changed": listing(UNIT) != BEFORE,
                              "run dirs": sorted(p.name for p in UNIT.glob("*/run"))}

marker = UNIT / "fake_kingston" / "run"
marker.mkdir()
(marker / "control-1-submitting.json").write_bytes(b"{}\n")
before_marker = listing(UNIT)
local["S1 once only"] = refusal(drive.drive, UNIT, route="local", tree=tree)
OUT["local S1"] = {"sent": len(SENT), "unit unchanged": listing(UNIT) == before_marker,
                   "run dirs": sorted(p.name for p in UNIT.glob("*/run"))}
OUT["local scenes"] = local

# -- the builds that fail remove what they made, and nothing else ---------------------------------------------------------------------------------
clean = {}
real_write = unit_bundle.write
calls = []


def failing_write(*a, **kw):
    calls.append(1)
    if len(calls) == 2:
        raise RuntimeError("the second bundle fails")
    return real_write(*a, **kw)


unit_bundle.write = failing_write
failed = WORK.parent / (WORK.name + "-failed")
try:
    freeze.freeze(failed, divisor=128, tree=tree, log=lambda s: None)
except RuntimeError as x:
    clean["freeze raised"] = str(x)
clean["freeze made nothing that stays"] = not failed.exists()
calls.clear()
empty = WORK.parent / (WORK.name + "-empty")
empty.mkdir()
try:
    freeze.freeze(empty, divisor=128, tree=tree, log=lambda s: None)
except RuntimeError:
    pass
clean["an existing empty directory stays, emptied"] = empty.is_dir() and list(empty.iterdir()) == []
unit_bundle.write = real_write
taken = WORK.parent / (WORK.name + "-taken")
taken.mkdir()
(taken / "foreign.txt").write_bytes(b"not the kit's\n")
clean["a non-empty directory is refused"] = refusal(freeze.freeze, taken, divisor=128, tree=tree)
clean["and its file is untouched"] = (taken / "foreign.txt").read_bytes() == b"not the kit's\n"

crate_out = WORK.parent / (WORK.name + "-crate")
real_finalize = p5_generate.finalize


def finalize_then_fail(out, write, now=None, writer=None):
    (Path(out) / "unit" / "foreign.txt").write_bytes(b"another's, put there during the build\n")
    raise RuntimeError("the metadata fails")


p5_generate.finalize = finalize_then_fail
try:
    crate.build(UNIT, crate_out, tree=tree)
except RuntimeError:
    pass
p5_generate.finalize = real_finalize
left = sorted(p.relative_to(crate_out).as_posix() for p in crate_out.rglob("*")) if crate_out.exists() else None
clean["a failed crate leaves only what another put there"] = left == ["unit", "unit/foreign.txt"]
clean["its own files are gone"] = not (crate_out / "LICENSE-quantum-film").exists() and not (crate_out / "unit" / "UNIT.json").exists()
OUT["cleanup"] = clean

print(json.dumps(OUT, sort_keys=True))
