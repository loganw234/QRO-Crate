"""The adapter's command line as a process, with a stand-in for P2's module that raises (the lead's ruling, 2026-11-08, on
the seam).

    python tests/p1/p1_standin.py FUNCTION RAISED -- ADAPTER-ARGUMENTS

runs the adapter's own main with `qro.p2_measures` put in sys.modules, where the generator finds a parcel's module, a stand-in
whose FUNCTION (`question_files` or `contribute`) raises RAISED (`value`: a ValueError; `os`: an OSError; `memory`: a
MemoryError; `none`: it does not raise) and whose other function answers as a module that serves the crate would: one file
under question/, and no term and no entity. The exit code is the adapter's. A helper: nothing here is a test."""
import sys
import types

MESSAGE = "P2 has no law for this crate é"
RAISES = {"value": ValueError(MESSAGE), "os": OSError(MESSAGE), "memory": MemoryError(MESSAGE)}


def module(function, raised):
    def fails(*args):
        raise RAISES[raised]

    def question_files(crate):
        return {"law.json": b"{}\n"}

    def contribute(crate, entities):
        return {}, []
    functions = {"question_files": question_files, "contribute": contribute}
    if raised != "none":
        functions[function] = fails
    return types.SimpleNamespace(**functions)


def main(argv):
    cut = argv.index("--")
    function, raised = argv[:cut]
    sys.modules["qro.p2_measures"] = module(function, raised)
    from qro import p1_adapter
    return p1_adapter.main(argv[cut + 1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
