"""P2's two controls (study QRO-0, section 11; P2's design, item 11; P2.2), each planted in a copy of P1's twin with P1.2's
toolkit, controls/plants_p1.py. Each fault is a function of a built crate, so that P2's crate-level stage
(tests/p2crates) plants the second in a copy of v0's real IBM crate as well.

  class-declared   `#contrast-n-crystal-share-uniform`'s `qro:class`, `integrity`, made `signal` (asserted first): the
                   metadata edited with the toolkit's `patch` and nothing else. The law and the uniform twin both put
                   every shot on five crystals, so the share's expected value is 1 under each and its class is
                   integrity. Step 6 computes the class from the law's bytes and the twin's rule, never from the word,
                   and refuses the crate `measure-class` at that Contrast.
  compile-broken   in kingston's morning law gate list, `2026-10-05/ibm/ibm_kingston/bundle/law.gates.json`, gate 303,
                   `["sx", [47], [], []]` (asserted first), made `["x", [47], [], []]`, the file written in
                   Quantum-Film's own style; then every digest the records hold over it recomputed: every file of the
                   crate holding the old bytes given the new ones, every bundle manifest's `gates_sha256` of the old
                   bytes made the new digest, and the lines' and markers' digests of each manifest changed (the
                   toolkit's Forge); then `rebuild`, which regenerates the metadata and every File's digest. Step 7
                   simulates the gate list the new digest names and holds it to its logical circuit, which nothing
                   here changes, and refuses the crate `compile-uncontrolled` at that gate list.

A plant that does not find what it is written for (another class, another gate) raises PlantError and plants nothing
else: a control that planted some other fault would prove nothing about this one. Each control's twin is P1's twin,
accepted (plants_p1.twin_crate). This module builds nothing when it is imported, and has no command line: the plant
command and the runner call the plants, through controls/registry.py's plants().
"""
from controls import plants_p1 as toolkit
from qro import canonical

CONTRAST = "#contrast-n-crystal-share-uniform"
INTEGRITY, SIGNAL = "integrity", "signal"
LAW_GATES = f"{toolkit.MORNING_BUNDLE}/law.gates.json"
GATE = 303
SX, X = ["sx", [47], [], []], ["x", [47], [], []]
MANIFEST = "/bundle/manifest.json"


class PlantError(RuntimeError):
    """A crate that does not hold what a plant is written for: the plant refuses rather than plant another fault."""


def declare_class(crate, contrast=CONTRAST, was=INTEGRITY, now=SIGNAL):
    """The Contrast's `qro:class` changed from `was` to `now`, in the metadata alone; the crate is returned."""
    def edit(graph):
        found = [e for e in graph if e.get("@id") == contrast]
        if len(found) != 1 or found[0].get("qro:class") != was:
            raise PlantError(f"{contrast} does not say {was}: this crate is not the one the plant is written for")
        found[0]["qro:class"] = now
    return toolkit.patch(crate, edit)


def break_gate_list(crate, rel=LAW_GATES, gate=GATE, was=SX, now=X):
    """Gate `gate` of the gate list at `rel` changed from `was` to `now`, every digest the records hold over the list
    recomputed, and the metadata regenerated; the crate is returned."""
    forge = toolkit.Forge(crate)
    doc = forge.json(rel)
    gates = doc.get("gates") if isinstance(doc, dict) else None
    if not isinstance(gates, list) or not 0 <= gate < len(gates) or gates[gate] != was:
        raise PlantError(f"gate {gate} of {rel} is not {was}: this crate is not the one the plant is written for")
    old = forge.digest(rel)
    gates[gate] = now
    data = toolkit.STYLES[toolkit.style_of(rel)](doc)
    new = toolkit.sha(data)
    files = {e["@id"]: e["sha256"] for e in toolkit.graph_of(crate)["@graph"]
             if "File" in canonical.types(e) and isinstance(e.get("sha256"), str)}
    for path in sorted(p for p, digest in files.items() if digest == old):
        forge.write(path, data)

    def renamed(m):
        for job in m["jobs"]:
            for c in job["circuits"]:
                if c.get("gates_sha256") == old:
                    c["gates_sha256"] = new
    for path in sorted(p for p in files if p.endswith(MANIFEST)):
        if any(c.get("gates_sha256") == old for job in forge.json(path)["jobs"] for c in job["circuits"]):
            forge.edit_json(path, renamed)
            forge.reseal_bundle(path[:-len("/manifest.json")])
    return toolkit.rebuild(crate)


def class_declared(crate):
    return declare_class(crate)


def compile_broken(crate):
    return break_gate_list(crate)


FAULTS = {"class-declared": class_declared, "compile-broken": compile_broken}


def _plant(fault):
    def plant(d):
        return fault(toolkit.twin_crate(d))
    plant.__name__ = fault.__name__
    return plant


PLANTS = {name: _plant(fault) for name, fault in FAULTS.items()}
