"""What P2 registers with the checker (FORMAT.md, item 20; P2's design, item 12; P2.1): steps 6 and 7, and nothing
else: no raw form, no count rule, no generator.

`checker.load()` imports this module on every check, so it imports nothing at its top. Each step enters only where the
crate carries a term whose step, in the vocabulary, is the step's, or an entity of one of the step's own types (the
lead's decision on P2.1's escalation E1, 2026-10-26): step 6 on `qro:Measuring`, `qro:Contrast` and `qro:Measurement`,
step 7 on `qro:Hold`. It reads a term's step from qro.vocabulary, which the checker has already loaded, never from a
list of its own, and it imports qro.p2_* only once it enters. So a crate that carries none of P2's terms or types, P0's
fixture and P1's crates among them, costs P2 nothing and cannot fail on P2's code, whatever law or coherence Pubs and
Compiles it holds; step 9 alone refuses such a crate wherever its generator writes P2's entities (P2's stated limit).
"""


def _enters(md, step, types):
    from qro import vocabulary as V                    # loaded with the checker: a lookup, not a load
    for e in md["@graph"]:
        t = e.get("@type")
        if t in types or (isinstance(t, list) and any(x in types for x in t)):
            return True
        for k in e:
            term = V.TERM.get(k)
            if term is not None and term.step == step:
                return True
    return False


def step6(crate_dir, md):
    if _enters(md, 6, ("qro:Measuring", "qro:Contrast", "qro:Measurement")):
        from qro import p2_steps
        p2_steps.step6(crate_dir, md)


def step7(crate_dir, md):
    if _enters(md, 7, ("qro:Hold",)):
        from qro import p2_steps
        p2_steps.step7(crate_dir, md)


STEPS = {6: step6, 7: step7}
