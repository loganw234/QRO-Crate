"""What P5 imports of P1, pinned (P5's design, decision 9; the lead's ruling of 2026-11-08T15:33:03Z): each name and signature
of P1's guards (qro/p1_guards.py, by the names of its `EXPORTS`) and of P1's readers that qro/p5_generate.py and
qro/p5_unit.py use. A later change of P1's that would break P5 fails here, by name, and not silently in a unit crate.

The table is held both ways: every attribute of a P1 module that P5's two modules use (read from their source by `ast`) is
in the table, and every row of it is used. P1's guards are imported, never copied: no function of P5's modules is a copy of
one of P1's (no `hold_*`, `_g2` to `_g8`, `_hold` or `_read` is defined there)."""
import ast
import importlib
import inspect

import pytest
from p5_support import ROOT, no_network  # noqa: F401

from qro import p1_graph, p1_guards, p5_generate, p5_unit

pytestmark = pytest.mark.usefixtures("no_network")

PINNED = {
    "qro.p1_guards": {
        "GuardError": "class (guard, where, detail)", "MAX_PUBS": "value",
        "hold": "(ok, guard, where, detail)", "read_record": "(guard, where, fn, *args)",
        "hold_line": "(crate, name, files, manifest, mdigest, spec, line)",
        "hold_device_runs": "(crate, where, found, manifest, spec, line)",
        "hold_commitments_and_counts": "(files, manifest, spec, line, records, raw)",
        "hold_metrics": "(files, line, metrics, raw)", "hold_refetch_job": "(crate, path, job)",
        "hold_refetch_result": "(crate, path, job, raw_path, committed_path)",
        "hold_read_manifest": "(crate, held, root, expect, carried, snapshot)"},
    "qro.p1_records": {
        "line": "(data, what)", "manifest": "(data, what)", "metrics": "(data, what)",
        "need": "(doc, what, *path, kind=<class 'str'>)", "parse": "(data, what)", "stamp_of": "(name, what)",
        "RecordError": "class", "REFETCH_MANIFEST_FORMAT": "value", "RESULTS_MANIFEST_FORMAT": "value"},
    "qro.p1_forms": {"parse_ibm_result": "(data)", "parse_snapshot": "(data)", "parse_time": "(text, zone='Z')",
                     "RawFormError": "class"},
    "qro.p1_decode": {"RULES": "value", "expected_set": "(qasm)", "known_answer_verdict": "(counts, expected, width=16)",
                      "pub_counts": "(crate_dir, md, pub_id)", "DecodeError": "class", "KnownAnswerError": "class"},
    "qro.p1_commit": {"commitment_of": "(fields)", "options_digest": "(options)"},
    "qro.p1_calibration": {"claims": "(snapshot)", "link_for": "(first_shot, history, carried)", "LinkError": "class"},
    "qro.p1_graph": {"GraphError": "class", "Index": "class (md)"},
}
INDEX_METHODS = {"of_type": "(self, t)", "get": "(self, ref, type=None)", "one": "(self, entity, key, type=None)",
                 "refs_of_type": "(self, entity, key, type)", "pub_index": "(self, pub)", "files_by_sha256": "(self, digest)"}
ALIASES = {"p1_guards": "qro.p1_guards", "rec": "qro.p1_records", "p1_forms": "qro.p1_forms", "p1_decode": "qro.p1_decode",
           "p1_commit": "qro.p1_commit", "cal": "qro.p1_calibration", "p1_graph": "qro.p1_graph"}
MODULES = ("qro/p5_generate.py", "qro/p5_unit.py")


def shape(obj):
    if inspect.isclass(obj):
        return "class " + str(inspect.signature(obj)) if obj.__name__ in ("GuardError", "Index") else "class"
    return str(inspect.signature(obj)) if callable(obj) else "value"


@pytest.mark.parametrize("module, name, want", [(m, n, w) for m, t in PINNED.items() for n, w in t.items()],
                         ids=[f"{m}.{n}" for m, t in PINNED.items() for n in t])
def test_each_name_and_signature_p5_imports_is_pinned(module, name, want):
    obj = getattr(importlib.import_module(module), name)
    assert shape(obj) == want


def test_every_guard_p5_calls_is_one_p1_exports():
    for name in PINNED["qro.p1_guards"]:
        if name != "MAX_PUBS":
            assert name in p1_guards.EXPORTS
    assert "MAX_PUBS" in p1_guards.EXPORTS


def test_the_index_methods_p5_uses_are_pinned():
    for name, want in INDEX_METHODS.items():
        assert str(inspect.signature(getattr(p1_graph.Index, name))) == want


def uses():
    out = {}
    for rel in MODULES:
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in ALIASES:
                out.setdefault(ALIASES[n.value.id], set()).add(n.attr)
            if isinstance(n, ast.ImportFrom) and n.module in ALIASES.values():
                out.setdefault(n.module, set()).update(a.name for a in n.names)
    return out


def test_the_table_holds_every_p1_attribute_p5s_modules_use_and_only_those():
    found = uses()
    for module, names in found.items():
        assert names <= set(PINNED[module]), f"{module}: {sorted(names - set(PINNED[module]))} used, not pinned"
    for module, table in PINNED.items():
        assert set(table) <= found.get(module, set()), f"{module}: {sorted(set(table) - found.get(module, set()))} pinned, not used"


def test_p5_imports_p1s_guards_from_the_module_and_copies_none():
    tree = ast.parse((ROOT / "qro/p5_generate.py").read_text(encoding="utf-8"))
    defined = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert not {n for n in defined if n.startswith("hold_") or n in ("_g2", "_g3", "_g4", "_g5", "_g6", "_g7", "_g8", "_hold",
                                                                    "_read")}
    assert p5_generate.GuardError is p1_guards.GuardError
    imported = [a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "qro.p1_guards" for a in n.names]
    assert imported == []                                   # the module is imported, and its names looked up when called


def test_p5s_modules_never_import_p1s_generator_or_its_private_names():
    for rel in MODULES + ("qro/register_p5.py",):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "p1_generate" not in text.replace("qro/p1_generate.py", "").replace("P1's generator", ""), rel
        assert "p1_adapter" not in text.replace("qro/p1_adapter.py", ""), rel
    for rel in MODULES:
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in ALIASES:
                assert not n.attr.startswith("_"), f"{rel}: {n.value.id}.{n.attr}"


def test_the_p1_readers_p5_reads_units_through_are_the_modules_the_seam_names():
    assert p5_unit.p1_decode.pub_counts is importlib.import_module("qro.p1_decode").pub_counts
