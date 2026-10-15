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

from controls.registry import PLANTS, twin
from qro.__main__ import main as qro


def main(argv):
    if len(argv) != 1 or (argv[0] != "twin" and argv[0] not in PLANTS):
        print(f"usage: python -m controls.plant twin|{'|'.join(sorted(PLANTS))}", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory() as d:
        planted = twin(d) if argv[0] == "twin" else PLANTS[argv[0]](d)
        if not isinstance(planted, tuple):
            return qro(["check", "--fixtures", str(planted)])
        log, rec = planted
        Path(d, "custody.log").write_bytes(log)
        args = ["custody", str(Path(d, "custody.log"))]
        if rec is not None:
            Path(d, "audit.json").write_bytes(rec)
            args.append(str(Path(d, "audit.json")))
        return qro(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
