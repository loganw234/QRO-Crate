#!/usr/bin/env python3
"""The study's five analysis instruments, re-run against moth-quantum, each held to its kept output (study QRO-0,
section 15). The study's figures rest on those outputs, so a figure the documents quote has a script in the tree
that still reproduces it (ParcelRound, METHOD.md section 2).

    python tools/check_instruments.py <moth-quantum checkout>    # 0 = every output reproduced; 1 = each one not

Each instrument refuses unless the checkout is a clean 3a73823, and that refusal fails this check too. The kept
outputs were written by Python on Windows, with CRLF line ends: on Windows the comparison is byte for byte, and
elsewhere it is with every CRLF read as LF, a stated limit. Stdlib only.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QRO0 = ROOT / "docs" / "studies" / "qro0"
INSTRUMENTS = ("sufficiency_v0", "v0_timing_and_drift", "isolation_v0", "calibration_at_execution_v0",
               "free_tier_unit_v0")


def main(argv):
    if len(argv) != 1 or not Path(argv[0]).is_dir():
        print("usage: python tools/check_instruments.py <moth-quantum checkout>", file=sys.stderr)
        return 2
    moth, bad = Path(argv[0]), 0
    for name in INSTRUMENTS:
        args = [str(ROOT), str(moth)] if name == "calibration_at_execution_v0" else [str(moth)]
        r = subprocess.run([sys.executable, "-I", str(QRO0 / f"{name}.py"), *args], capture_output=True)
        kept = (QRO0 / f"{name}.out.txt").read_bytes()
        got = r.stdout
        if os.name != "nt":
            got, kept = got.replace(b"\r\n", b"\n"), kept.replace(b"\r\n", b"\n")
        ok = r.returncode == 0 and got == kept
        bad += not ok
        tail = r.stderr.decode(errors="replace").strip().splitlines()[-1:] or [""]
        print(f"{'ok' if ok else 'FAIL':5} {name}: "
              + ("its kept output, reproduced" if ok else f"exit {r.returncode}, output differs: {tail[0]}"))
    print(f"{len(INSTRUMENTS) - bad} of {len(INSTRUMENTS)} instruments reproduced their kept outputs")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
