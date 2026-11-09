"""What P5 registers with the checker (FORMAT.md, item 20; P5's design, item 8; P5.1): the generator `qro-p5-unit` that step
9 runs on a unit crate, and nothing else: no step, no raw form (a unit's raw results are P1's `ibm-sampler-result/v1`), no
count rule. No CHECKED term is new, so no step is P5's.

`checker.load()` imports this module on every check, so it imports nothing at its top. The generator returns to qro.p5_generate
only when step 9 runs it on a crate that names it, so a crate of P0's fixture, or of P1's, costs P5 nothing and cannot fail on
P5's code.
"""


def generate_unit(crate_dir):
    from qro import p5_generate
    return p5_generate.unit(crate_dir)


STEPS = {}
RAW_FORMS = {}
GENERATORS = {"qro-p5-unit": generate_unit}
