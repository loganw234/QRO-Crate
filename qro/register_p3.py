"""What P3 registers with the checker (FORMAT.md, item 20; P3's design, items 1 and 12; P3.1): the comparison crate's
generator, `qro-p3-comparison`, which step 9 runs, and nothing else: no step, no raw form, no count rule. No term of
P3's is CHECKED, so no step of the nine is P3's: a comparison's record is re-derived by its own check, `python -m qro
compare` (qro.p3_compare), which needs its runs' crates.

`checker.load()` imports this module on every check, so it imports nothing at its top, and the generator imports P3's
modules only when step 9 runs it on a crate that names it. So a crate that is no comparison costs P3 nothing.
"""


def generate_comparison(crate_dir):
    from qro import p3_record
    return p3_record.generate(crate_dir)


GENERATORS = {"qro-p3-comparison": generate_comparison}
