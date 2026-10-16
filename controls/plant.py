"""Plant one control, or the twin, in a temporary directory, and run QRO-Crate's own command line on it: the
runner's negative control and its positive twin go through the command a user runs (moth-quantum, verify/run.sh,
"the control and its twin").

    python -m controls.plant twin            # must exit 0: ACCEPTED
    python -m controls.plant shot-moved      # must exit 1, saying REFUSED raw-digest

Stdlib only.
"""
import sys
import tempfile
from pathlib import Path

from controls.registry import plants, twin
from qro import checker
from qro.__main__ import escape
from qro.__main__ import main as qro


def main(argv):
    every = plants()
    if len(argv) != 1 or (argv[0] != "twin" and argv[0] not in every):
        print(f"usage: python -m controls.plant twin|{'|'.join(sorted(every))}", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory() as d:
        planted = twin(d) if argv[0] == "twin" else every[argv[0]](d)
        if not isinstance(planted, tuple):
            return qro(["check", "--fixtures", str(planted)])
        log, rec = planted
        Path(d, "custody.log").write_bytes(log)
        args = ["custody", str(Path(d, "custody.log"))]
        if rec is not None:
            Path(d, "audit.json").write_bytes(rec)
            args.append(str(Path(d, "audit.json")))
        return qro(args)


def run(argv):
    """main(), with the command's own failure as exit 3 and one line on stderr: a plants module that raised
    SystemExit(0) as it loaded ended the command with exit 0, unrun, so the twin's stage passed (P0.1's verifier,
    round 4, N4). The line says "this is not a verdict", not "nothing was checked": the temporary directory's
    removal can fail after the checker has written its own line (P0.2)."""
    try:
        return main(argv)
    except BaseException as x:
        print(escape(f"FAILED: the plant command itself failed, {checker.describe(x)}; this is not a verdict"),
              file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
