"""The golden model stands alone (P2's design, items 5 and 12): every module of P2's under qro, register_p2 among
them, imports only the standard library and qro, so no numpy, no qiskit and no Quantum-Film; qro/p2_interval.py, the
certified intervals, imports no math, names no logarithm and holds no float, so its endpoints are integer arithmetic
and the same bytes on every host (study section 10: a test reads its imports); no pattern of P2's says \\d; and no
module of the package calls the report functions."""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULES = sorted((ROOT / "qro").glob("p2_*.py")) + [ROOT / "qro" / "register_p2.py"]


def tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def imported(t):
    roots = {a.name.split(".")[0] for n in ast.walk(t) if isinstance(n, ast.Import) for a in n.names}
    roots |= {n.module.split(".")[0] for n in ast.walk(t) if isinstance(n, ast.ImportFrom) and n.level == 0}
    relative = [n for n in ast.walk(t) if isinstance(n, ast.ImportFrom) and n.level]
    return roots, relative


def test_p2_has_the_modules_its_design_names():
    assert [p.stem for p in MODULES] == ["p2_hold", "p2_interval", "p2_law", "p2_measures", "p2_report", "p2_sim",
                                         "p2_steps", "register_p2"]


def test_every_module_of_p2s_imports_only_the_standard_library_and_the_package():
    stdlib = set(sys.stdlib_module_names)
    for path in MODULES:
        roots, relative = imported(tree(path))
        assert roots <= stdlib | {"qro"} and not relative, (path.name, roots - stdlib)
        assert not roots & {"numpy", "scipy", "qiskit", "quantum_film"}


def test_the_intervals_module_imports_no_math_names_no_logarithm_and_holds_no_float():
    t = tree(ROOT / "qro" / "p2_interval.py")
    roots, _ = imported(t)
    assert roots == {"dataclasses", "fractions"}
    names = {n.id for n in ast.walk(t) if isinstance(n, ast.Name)}
    attrs = {n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)}
    for word in ("log", "log2", "log10", "log1p", "exp", "sqrt", "float", "math", "cmath", "decimal"):
        assert word not in names and word not in attrs, word
    floats = [n.value for n in ast.walk(t) if isinstance(n, ast.Constant) and type(n.value) in (float, complex)]
    assert floats == []


def test_the_intervals_module_check_bites():
    """The control: the same reading finds math.log where a module has it."""
    t = ast.parse("import math\nx = math.log(2.0)\n")
    assert imported(t)[0] == {"math"}
    assert "log" in {n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)}
    assert [n.value for n in ast.walk(t) if isinstance(n, ast.Constant) and type(n.value) is float] == [2.0]


def test_no_pattern_of_p2s_says_backslash_d():
    for path in MODULES:
        assert "\\d" not in path.read_text(encoding="utf-8"), path.name


def test_no_module_of_the_package_but_the_report_functions_own_names_them():
    """The report functions are read by no step and written to no crate (docs/P2.md): no module under qro/ but
    qro/p2_report.py names it, so no step, no generator and no reader of the package can call it. The control: the
    same search finds the module named where it is imported, in its tests."""
    naming = [p.name for p in sorted((ROOT / "qro").glob("*.py"))
              if p.name != "p2_report.py" and "p2_report" in p.read_text(encoding="utf-8")]
    assert naming == []
    assert "p2_report" in (ROOT / "tests" / "p2" / "test_p2_report.py").read_text(encoding="utf-8")
