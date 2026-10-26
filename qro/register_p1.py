"""What P1 registers with the checker (FORMAT.md, item 20; P1's design, item 9; P1.1): steps 4, 5 and 8, and the
readers of P1's three raw forms. The producer's half, P1's generators, is registered when it lands.

`checker.load()` imports this module on every check, so it imports nothing but the standard library, and each
function it declares returns at once, before it imports any other module of P1's, when the metadata holds no entity
of a type its step visits. So a crate with none of P1's entities, P0's fixture among them, costs P1 nothing and
cannot fail on P1's code. A raw form's reader is called only for a raw result that names the form.
"""


def _holds(md, *types):
    for e in md["@graph"]:
        t = e.get("@type")
        if t in types or (isinstance(t, list) and any(x in types for x in t)):
            return True
    return False


def step4(crate_dir, md):
    if _holds(md, "qro:Pub"):
        from qro import p1_steps
        p1_steps.step4(crate_dir, md)


def step5(crate_dir, md):
    if _holds(md, "qro:Decode"):
        from qro import p1_steps
        p1_steps.step5(crate_dir, md)


def step8(crate_dir, md):
    if _holds(md, "qro:Snapshot", "qro:Job"):
        from qro import p1_steps
        p1_steps.step8(crate_dir, md)


def read_ibm_sampler_result(data):
    from qro import p1_forms
    return p1_forms.read_ibm(data)


def read_atlas_tomography_result(data):
    from qro import p1_forms
    return p1_forms.read_atlas_result(data)


def read_atlas_known_answer_vector(data):
    from qro import p1_forms
    return p1_forms.read_atlas_vector(data)


STEPS = {4: step4, 5: step5, 8: step8}
RAW_FORMS = {"ibm-sampler-result/v1": read_ibm_sampler_result,
             "atlas-tomography-result/v1": read_atlas_tomography_result,
             "atlas-known-answer-vector/v1": read_atlas_known_answer_vector}
