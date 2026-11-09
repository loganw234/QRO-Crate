"""What P3's modules import and call (P3's design, item 4, "Rounding", and the brief's rule: P1's and P2's functions
imported, never copied, and pinned): no float and no `math` in any of them, so every comparison with epsilon is exact;
only the standard library and qro; never P2's `pooled` (N5), `measurements` or `certify` (a crate's own family, P2's
limit 7), and no private name of another parcel's; and each name and signature P3 calls of P1's and P2's pinned here,
so that a change of theirs that would move P3's verdicts fails this stage in their own runs."""
import ast
import inspect
import sys
from pathlib import Path

import pytest

from qro import p1_decode, p1_forms, p1_graph, p1_records, p2_hold, p2_interval, p2_law, p2_measures

ROOT = Path(__file__).resolve().parents[2]
MODULES = ["p3_declaration", "p3_runs", "p3_refusals", "p3_verdicts", "p3_readout", "p3_record", "p3_compare",
           "register_p3"]


def tree(name):
    return ast.parse((ROOT / "qro" / f"{name}.py").read_text(encoding="utf-8"))


def test_p3_has_the_modules_its_design_and_the_brief_name():
    assert sorted(p.stem for p in (ROOT / "qro").glob("*p3*.py")) == sorted(MODULES)


@pytest.mark.parametrize("name", MODULES)
def test_no_float_and_no_math(name):
    for node in ast.walk(tree(name)):
        assert not (isinstance(node, ast.Constant) and isinstance(node.value, float)), (name, node.lineno)
        assert not (isinstance(node, ast.Name) and node.id in ("float", "math")), (name, node.lineno)
        if isinstance(node, ast.Import):
            assert all(a.name.split(".")[0] != "math" for a in node.names), name
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] != "math", name


@pytest.mark.parametrize("name", MODULES)
def test_only_the_standard_library_and_qro(name):
    for node in ast.walk(tree(name)):
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
            [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 else []
        for n in names:
            top = n.split(".")[0]
            assert top == "qro" or top in sys.stdlib_module_names, (name, n)


def test_the_register_module_imports_nothing_at_its_top():
    t = tree("register_p3")
    assert not [n for n in t.body if isinstance(n, (ast.Import, ast.ImportFrom))]


FORBIDDEN = {("p2_interval", "pooled"), ("p2_measures", "measurements"), ("p2_measures", "certify")}


@pytest.mark.parametrize("name", MODULES)
def test_no_forbidden_call_and_no_private_name_of_another_parcels(name):
    for node in ast.walk(tree(name)):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            mod, attr = node.value.id, node.attr
            assert (mod, attr) not in FORBIDDEN, (name, mod, attr)
            if mod.startswith(("p1_", "p2_")):
                assert not attr.startswith("_"), (name, mod, attr)
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(("qro.p1_", "qro.p2_")):
            assert not any(a.name.startswith("_") for a in node.names), (name, node.module)


# -- the names and signatures P3 calls of P1's and P2's, pinned -----------------------------------------------------
PINNED = [
    (p2_law, "read", "(data)"), (p2_law, "classes", "(law)"),
    (p2_measures, "pub_values", "(crate_dir, md, pub, law)"), (p2_measures, "manifest_of", "(idx, compile_entity)"),
    (p2_hold, "coherence_pair", "(basis, width)"),
    (p2_interval, "interval", "(total, n, family, alpha=Fraction(1, 20), E=None, grid=48)"),
    (p2_interval, "mapped", "(bounds, mapping)"), (p2_interval, "difference", "(a, b)"),
    (p2_interval, "abs_lower", "(d)"), (p2_interval, "drift", "(job_intervals, pooled_interval)"),
    (p2_interval, "strong_form", "(diff, drift_a, drift_b)"), (p2_interval, "xeb", "(w_max, den, D, norm)"),
    (p1_decode, "expected_set", "(qasm)"), (p1_decode, "pub_counts", "(crate_dir, md, pub_id)"),
    (p1_decode, "crate_file", "(crate_dir, entity, what)"),
    (p1_records, "line", "(data, what)"), (p1_records, "manifest", "(data, what)"),
    (p1_records, "device_run", "(data, what)"),
    (p1_forms, "load_json", "(data, what, error=<class 'qro.checker.RawFormError'>)"),
    (p1_forms, "parse_time", "(text, zone='Z')"),
    (p1_graph.Index, "one", "(self, entity, key, type=None)"), (p1_graph.Index, "pubs_of", "(self, job)"),
    (p1_graph.Index, "raw_of", "(self, job)"), (p1_graph.Index, "decode_of", "(self, raw)"),
    (p1_graph.Index, "files_by_sha256", "(self, digest)"), (p1_graph.Index, "refs_of_type", "(self, entity, key, type)"),
    (p1_graph.Index, "of_type", "(self, t)"), (p1_records.Manifest, "circuits", "(self)")]


@pytest.mark.parametrize("owner, name, signature", PINNED, ids=[f"{getattr(o, '__name__', o)}.{n}" for o, n, _ in PINNED])
def test_each_name_p3_calls_of_p1s_and_p2s_is_pinned(owner, name, signature):
    assert str(inspect.signature(getattr(owner, name))) == signature


def test_the_constants_and_fields_p3_reads_of_p2s_are_pinned():
    assert p2_interval.RULE == "qro-hoeffding-kl/1" and p2_law.MEASURE_SET == "qro-measures/1"
    assert p2_law.CERTIFIED == ("n-crystal-share", "forbidden-share", "linear-xeb", "x0x1", "y0y1")
    assert p2_law.COHERENCE == {"x0x1": "X0X1", "y0y1": "Y0Y1"}
    assert [f.name for f in p2_measures.Value.__dataclass_fields__.values()] == ["measure", "in_scope", "value",
                                                                                  "total", "mapping"]
    assert [f.name for f in p2_law.Contrast.__dataclass_fields__.values()] == ["measure", "twin", "cls", "law_value",
                                                                               "twin_value"]
    circuit = [f.name for f in p1_records.Circuit.__dataclass_fields__.values()]
    assert {"role", "basis", "shots", "commitment", "circuit_sha256", "gates_sha256"} <= set(circuit)
    manifest = [f.name for f in p1_records.Manifest.__dataclass_fields__.values()]
    assert {"program", "route", "kind", "options_sha256", "decode"} <= set(manifest)
    assert {"bundle_sha256", "submitted_at", "job_id"} <= {f.name for f in p1_records.Line.__dataclass_fields__.values()}


def test_every_name_p3_calls_of_another_parcels_module_is_pinned_here():
    """The pins above are every attribute P3's modules take of a P1 or P2 module: one more call fails here first."""
    pinned = {(getattr(o, "__name__", "").split(".")[-1], n) for o, n, _ in PINNED}
    constants = {("p2_interval", "RULE"), ("p2_law", "MEASURE_SET"), ("p2_law", "CERTIFIED"), ("p2_law", "COHERENCE"),
                 ("p2_hold", "HoldError"), ("p1_decode", "KnownAnswerError"), ("p2_law", "LawError"),
                 ("p1_records", "RecordError"), ("p2_interval", "IDENTITY"), ("p2_interval", "PARITY")}
    used = set()
    for name in MODULES:
        for node in ast.walk(tree(name)):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and \
                    node.value.id.startswith(("p1_", "p2_")):
                used.add((node.value.id, node.attr))
    assert used - pinned - constants == set(), sorted(used - pinned - constants)


# The classes of P1's and P2's whose objects P3's modules hold: an Index they make, the records P1's readers return, the
# law P2's reader returns, and the contrasts and values P2's functions return.
HELD = (p1_graph.Index, p1_records.Line, p1_records.Manifest, p1_records.Circuit, p2_law.Law, p2_law.Contrast,
        p2_measures.Value)
DICTS = {"get"}            # a name P3's modules call on dicts alone, which P1's Index also has


def test_every_method_p3_calls_on_p1s_and_p2s_objects_is_pinned_here():
    """Every call `x.name(...)` in P3's modules whose name is a public method of one of those classes is pinned above
    for that class (round 2, item 3: `manifest.circuits()` was called and not pinned). The walk reads names, not types:
    a call named `get` is taken to be a dict's, as every one in P3's modules is; no test holds that."""
    pinned = {(o, n) for o, n, _ in PINNED}
    called = set()
    for name in MODULES:
        for node in ast.walk(tree(name)):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    missing = []
    for cls in HELD:
        methods = {n for n, v in vars(cls).items() if callable(v) and not n.startswith("_")}
        missing += [f"{cls.__name__}.{n}" for n in sorted(methods & called - DICTS) if (cls, n) not in pinned]
    assert missing == []
    assert ("circuits" in called) and (p1_records.Manifest, "circuits") in pinned, "the walk sees the call it was for"
