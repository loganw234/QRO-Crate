"""The separation of the checker from the kit, and the kit's own gates, read by `ast` and run as processes (P5's design, items
4 and 6; P5.1): the checker's path never needs qiskit, numpy, mpmath or scipy; `qro` never imports `qro_kit`; the kit's
module-level imports are the standard library, `qro` and `qro_kit`; a sampler is made and run in one place, qro_kit/submit.py,
and the kit holds no way to connect to IBM; and nothing of the kit names a path of anyone's."""
import ast
import subprocess
import sys
from pathlib import Path

import pytest
from p5_support import ROOT, no_network, twin  # noqa: F401

pytestmark = pytest.mark.usefixtures("no_network")
KIT = sorted(p for p in (ROOT / "qro_kit").glob("*.py"))
FINDER = '''
import importlib.abc, sys
BAD = ("qiskit", "numpy", "mpmath", "scipy", "qiskit_ibm_runtime", "qiskit_aer", "quantum_film", "qro_kit")

class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in BAD:
            raise ImportError("the checker's path must not need " + name)
        return None

sys.meta_path.insert(0, Refuse())
sys.path.insert(0, {root!r})
'''


def module_level_imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            out += [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            out.append(node.module.split(".")[0])
    return out


def test_the_kits_module_level_imports_are_the_standard_library_qro_and_the_kit():
    allowed = set(sys.stdlib_module_names) | {"qro", "qro_kit"}
    for path in KIT:
        extra = sorted(set(module_level_imports(path)) - allowed)
        assert not extra, f"{path.name} imports {extra} outside a function"


def test_the_kit_imports_its_third_party_modules_inside_functions_only():
    seen = set()
    for path in KIT:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if isinstance(fn, ast.FunctionDef):
                for node in ast.walk(fn):
                    if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                        seen.add(node.module.split(".")[0])
                    elif isinstance(node, ast.Import):
                        seen |= {a.name.split(".")[0] for a in node.names}
    assert {"qiskit", "qiskit_ibm_runtime"} <= seen


def test_qro_and_the_controls_never_import_the_kit():
    for base in ("qro", "controls", "tools"):
        for path in (ROOT / base).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                    [node.module or ""] if isinstance(node, ast.ImportFrom) else []
                assert not [n for n in names if n.split(".")[0] == "qro_kit"], f"{path} imports the kit"


def receiver(node):
    """The dotted name a call's receiver is, or '' where it is not a plain chain of names."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def sites(pred):
    out = []
    for path in KIT:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
            for node in ast.walk(fn):
                if pred(node):
                    out.append((path.name, fn.name))
    return sorted(set(out))


def test_a_sampler_is_made_only_in_submit_sampler_for():
    made = sites(lambda n: isinstance(n, ast.Name) and n.id == "SamplerV2")
    assert made == [("submit.py", "sampler_for")]
    for path in KIT:                                         # nor imported under another name, nor reached by attribute
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
        assert "SamplerV2" not in names or path.name == "submit.py"
        assert not [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "SamplerV2"] or path.name == "submit.py"


def test_a_sampler_is_run_only_in_submit_send():
    """Every `.run(` of the kit but the standard library's (`subprocess.run`) and the vendored runner's (`q.runner.run`)."""
    def a_pass_manager(node):                              # generate_preset_pass_manager(...).run(circuit): the transpiler
        return isinstance(node, ast.Call) and getattr(node.func, "id", "") == "generate_preset_pass_manager"
    ran = sites(lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "run"
                and receiver(n.func.value) not in ("subprocess", "q.runner", "runner") and not a_pass_manager(n.func.value))
    assert ran == [("submit.py", "send")]


def test_send_runs_the_rules_of_the_job_before_it_runs_the_sampler():
    tree = ast.parse((ROOT / "qro_kit" / "submit.py").read_text(encoding="utf-8"))
    send = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "send")
    calls = [(n.lineno, receiver(n.func) or getattr(n.func, "id", "")) for n in ast.walk(send) if isinstance(n, ast.Call)]
    order = [name for _l, name in sorted(calls)]
    assert order.index("route_rules") < order.index("permit") < order.index("sampler.run")


def test_the_kit_holds_no_way_to_connect_to_ibm():
    """P5.1: the real route is present and refusing. No service class, connection call or credential read in the kit's own
    modules (the vendored account module is code the kit carries and does not call)."""
    for path in KIT:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree)
                                                                             if isinstance(n, ast.Attribute)}
        assert not names & {"QiskitRuntimeService", "connect", "save_account", "read_key", "read_crn", "apikey"}, path.name
        strings = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        assert not {s for s in strings if s.startswith("QF_IBM") or s in ("QISKIT_IBM_TOKEN", "ibm_quantum_platform")}, path.name


def test_the_kit_names_no_path_of_anyones_and_no_moth_checkout():
    forbidden = ("QRO_MOTH_ROOT", ".quantum-film", "AppData", "C:\\", "C:/", "/Users/", "/home/", "qf-ibm", "moth-quantum",
                 "keyleak.refusals(os.environ")
    for path in KIT:
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            if needle == "moth-quantum" and path.name in ("unit_bundle.py", "submit.py", "drive.py", "_qf.py", "freeze.py",
                                                         "crate.py", "__main__.py", "__init__.py"):
                continue                                    # prose naming the source of an adaptation, not a path
            assert needle not in text, f"{path.name} names {needle!r}"


def test_the_kit_starts_no_console_window_and_writes_no_bytecode():
    text = (ROOT / "qro_kit" / "__init__.py").read_text(encoding="utf-8")
    assert "sys.dont_write_bytecode = True" in text
    assert "creationflags" in (ROOT / "qro_kit" / "freeze.py").read_text(encoding="utf-8")
    assert "pythonw" not in "".join(p.read_text(encoding="utf-8") for p in KIT)


def test_p5_has_no_scrub_preflight_or_refetch_module_yet():
    """Those are P5.2's. Their absence is stated here so that a stray copy fails."""
    for name in ("scrub.py", "preflight.py", "refetch.py"):
        assert not (ROOT / "qro_kit" / name).exists()


# -- the checker's path, as a process ----------------------------------------------------------------------------------------------
def run_isolated(code):
    return subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, cwd=ROOT)


def test_the_checker_checks_a_unit_with_no_third_party_package_importable(tmp_path):
    crate = twin(tmp_path)
    code = FINDER.format(root=str(ROOT)) + f'''
from qro.__main__ import main
sys.exit(main(["check", {str(crate)!r}]))
'''
    p = run_isolated(code)
    assert p.returncode == 0 and p.stdout.startswith(b"ACCEPTED "), (p.stdout[-300:], p.stderr[-500:])


def test_every_module_of_qro_imports_with_no_third_party_package_importable():
    code = FINDER.format(root=str(ROOT)) + '''
import importlib, pkgutil
import qro
names = [m.name for m in pkgutil.iter_modules(qro.__path__)]
for name in names:
    importlib.import_module("qro." + name)
assert {"p5_unit", "p5_generate", "p5_tree", "register_p5"} <= set(names), names
print("imported", len(names))
'''
    p = run_isolated(code)
    assert p.returncode == 0 and p.stdout.startswith(b"imported "), (p.stdout[-300:], p.stderr[-500:])


def test_the_kits_own_stdlib_modules_import_with_no_third_party_package_importable():
    code = FINDER.format(root=str(ROOT)).replace('"qro_kit")', '"qiskit_aer")') + '''
import importlib
for name in ("submit", "crate", "freeze", "drive", "unit_bundle", "_qf", "__main__"):
    importlib.import_module("qro_kit." + name)
print("imported the kit")
'''
    p = run_isolated(code)
    assert p.returncode == 0 and p.stdout.startswith(b"imported the kit"), (p.stdout[-300:], p.stderr[-500:])


def test_this_file_names_the_tree_it_is_in():
    assert Path(__file__).resolve().is_relative_to(ROOT)
