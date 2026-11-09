"""The kit's command line (P5's design, item 13; P5.1).

    python -m qro_kit freeze --route local --out WORK [--shots-divisor N] [--contributor HANDLE]
    python -m qro_kit drive UNIT_DIR [--route local|real] [--confirm HEX12]
    python -m qro_kit crate UNIT_DIR --out CRATE

Run from the checkout's root, as `python -m qro.p1_adapter` is: the kit is the code of a tagged commit's own bytes, and
`kit-dirty` refuses to start from any other (qro/p5_tree.py), first of everything, before a single file is made. Exit codes,
as the checker's: 0 done; 1 a refusal, one line `REFUSED <name> at <where>: <detail>` (kit-dirty, route-unsafe, once-only, the
spend rules, and a crate the checker or intake refuses); 2 misuse, a command line or a directory the kit will not use; 3 the
kit itself failing, which is never a verdict (a crash, or a missing environment); 4 a drive that stopped after a job was sent,
with its records kept. Every line is printable ASCII, written whole to the descriptor, as `python -m qro check` writes its own;
an error is `ClassName: its text`, never a traceback.
"""
import sys
import warnings

from qro import checker
from qro.__main__ import write
from qro.refusal import Refused
from qro_kit import submit
from qro_kit.crate import CrateError

# qiskit-ibm-runtime warns, importing the fake backends, that one fake's properties are not typical: nothing of the kit's
warnings.filterwarnings("ignore", message="Properties of fake_nighthawk")
USAGE = ("usage: python -m qro_kit freeze --route local --out WORK [--shots-divisor N] [--contributor HANDLE] | "
         "drive UNIT_DIR [--route local|real] [--confirm HEX12] | crate UNIT_DIR --out CRATE")
OPTIONS = {"freeze": {"--route": "route", "--out": "out", "--shots-divisor": "divisor", "--contributor": "contributor"},
           "drive": {"--route": "route", "--confirm": "confirm"}, "crate": {"--out": "out"}}


class Misuse(ValueError):
    pass


def parse(argv):
    """(command, positional or None, {option: value}); Misuse for anything else."""
    if not argv or argv[0] not in OPTIONS:
        raise Misuse(USAGE)
    command, table = argv[0], OPTIONS[argv[0]]
    positional, got, i = None, {}, 1
    while i < len(argv):
        if argv[i] in table and table[argv[i]] not in got and i + 1 < len(argv):
            got[table[argv[i]]] = argv[i + 1]
            i += 2
        elif command != "freeze" and positional is None and not argv[i].startswith("--"):
            positional = argv[i]
            i += 1
        else:
            raise Misuse(f"{argv[i]}: not an option of this command, or given twice, or without its value; {USAGE}")
    if command == "freeze" and "out" not in got or command == "crate" and ("out" not in got or positional is None) \
            or command == "drive" and positional is None:
        raise Misuse(f"missing argument; {USAGE}")
    return command, positional, got


def _verdict(argv, tree):
    from qro_kit import crate, drive, freeze
    try:
        command, positional, got = parse(argv)
    except Misuse as x:
        return 2, [str(x)]
    try:
        if command == "freeze":
            divisor = 1
            if "divisor" in got:
                if not got["divisor"].isascii() or not got["divisor"].isdigit():
                    return 2, [f"--shots-divisor {got['divisor']}: a positive whole number; {USAGE}"]
                divisor = int(got["divisor"])
            done = freeze.freeze(got["out"], route=got.get("route", "local"), divisor=divisor, tree=tree,
                                 contributor=got.get("contributor", "withheld"), log=lambda s: None)
            return 0, [f"FROZEN unit {done['unit_sha256']} confirm {done['confirm']} divisor {done['divisor']} "
                       f"at {done['unit_dir']}"]
        if command == "drive":
            lines = []
            code = drive.drive(positional, route=got.get("route", "local"), flag=got.get("route") == "real",
                               confirm=got.get("confirm"), tree=tree, log=lines.append)
            lines.append("DRIVEN: all 18 jobs ran and every control job held" if code == 0 else
                         "STOPPED: the unit is incomplete; its records are kept")
            return code, lines
        done = crate.build(positional, got["out"], tree=tree)
        r = done["intake"]
        return 0, [f"BUILT unit: {done['files']} files, {done['bytes']} bytes, identity {done['identity']}", *r.lines()]
    except Refused as r:
        return 1, [f"REFUSED {r.name} at {r.where}: {r.detail}"]
    except CrateError as x:
        return 2, [f"{x}; {USAGE}"]
    except ModuleNotFoundError as x:
        return 3, [f"FAILED: the kit's environment lacks {x.name}: run it with the interpreter QRO_KIT_PYTHON names; "
                   "this is not a verdict"]


def main(argv, out=1, err=2, tree=None):
    """The exit code, after each line is written whole to a descriptor, unbuffered."""
    try:
        code, lines = _verdict(argv, tree or submit.tree_of_kit)
    except BaseException as x:                          # a crash, an exit or an interrupt: never a refusal
        code, lines = 3, [f"FAILED: the kit itself failed, {checker.describe(x)}; this is not a verdict"]
    try:
        for line in lines:
            write(out if code in (0, 1, 4) else err, line)
    except Exception:
        return 3
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
