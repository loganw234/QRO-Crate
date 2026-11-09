"""The contributor kit (P5; study QRO-0, section 9.1): the tool anyone uses to run one free-tier unit, 18 jobs on three
devices interleaved three times, and get a crate for it that qro's checker holds as it holds v0's.

    python -m qro_kit freeze --route local --out WORK [--shots-divisor N] [--contributor HANDLE]
    python -m qro_kit drive WORK/records/unit --route local
    python -m qro_kit crate WORK/records/unit --out CRATE

The kit is a package of its own, never imported by `qro`: the checker stays standard library, and this package's third-party
imports (numpy and mpmath through the vendored code; qiskit, qiskit-ibm-runtime and qiskit-aer) are made only inside
functions, after the vendored code is on the import path (`_qf`), so that the module-level imports of every module here are
the standard library, `qro`, and `qro_kit`. tests/p5/test_p5_kit_static.py reads them by `ast`.

P5.1 (this build) is the local route and the crate: the vendored Quantum-Film runner, the unit's bundle, the driver on the
fake backends, and the crate command. The real route is present and refusing (`submit.py`): no code of this package connects
to IBM. P5.2 adds the key, the scrub and the output scan, the pre-flight, the re-fetch and the dry-run probe.
"""
import sys

sys.dont_write_bytecode = True          # running the kit compiles nothing into the tree it was started from (kit-dirty D2)
