"""The adapter's command line as a process on a toy checkout, which is not moth-quantum (P1.2's sixth verifier, D1 and D2).

    python tests/p1/p1_pinned.py COMMIT -- ADAPTER-ARGUMENTS

runs the adapter's own main with the commit it reads set to COMMIT, the toy's, as tests/p1/p1_hosts.py runs it under a
host it simulates; the exit code is the adapter's. Without it a process would refuse the toy at once, for it is at a
commit of its own. A helper: nothing here is a test."""
import sys


def main(argv):
    cut = argv.index("--")
    from qro import p1_adapter
    p1_adapter.MOTH_COMMIT = argv[0]
    return p1_adapter.main(argv[cut + 1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
