"""The vendored files against moth-quantum's checkout at 3a73823 (P5's design, item 2; the lead's move of `p5-crates`
forward): each of the 22 modules, the licence and the source circuit of qro_kit/_vendor is the bytes git holds for it in the
checkout, and the 22 are the transitive closure of the nine modules the kit's runner needs."""
import ast
import hashlib
from pathlib import Path

import pytest
from p5crates_support import committed, moth_root, no_network  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "qro_kit" / "_vendor"
SOURCE_IN_MOTH = {"LICENSE-quantum-film": "LICENSE",                    # moth-quantum's paths of the two extra files
                  "circuit-ed767c01bd4b851d.qasm": "docs/records/2026-09-25/p3/circuit-ed767c01bd4b851d.qasm"}  # moth-quantum
START = ("quantum_film.fixer", "quantum_film.ibm.bundle", "quantum_film.ibm.runner", "quantum_film.ibm.account",
         "quantum_film.ibm.keyleak", "quantum_film.ibm.anchor", "quantum_film.ibm.decode", "quantum_film.ibm.raw",
         "quantum_film.ibm.isa")
pytestmark = pytest.mark.usefixtures("no_network")


def entries():
    out = []
    for line in (VENDOR / "VENDORED.sha256").read_text(encoding="ascii").splitlines():
        if line and not line.startswith(("#", "commit ")):
            sha, size, rel = line.split("  ")
            out.append((sha, int(size), rel))
    return out


def test_the_list_names_the_checkout_commit():
    text = (VENDOR / "VENDORED.sha256").read_text(encoding="ascii")
    full = next(ln for ln in text.splitlines() if ln.startswith("commit ")).split()[1]
    from p5crates_support import git
    assert git(moth_root(), "rev-parse", "HEAD").decode().strip() == full


@pytest.mark.parametrize("sha, size, rel", entries(), ids=[r for _s, _n, r in entries()])
def test_each_vendored_file_is_the_bytes_the_checkout_holds(sha, size, rel):
    root = moth_root()
    theirs = committed(root, SOURCE_IN_MOTH.get(rel, rel))
    mine = (VENDOR / rel).read_bytes()
    assert mine == theirs and hashlib.sha256(theirs).hexdigest() == sha and len(theirs) == size


def closure(root):
    """The modules the nine start modules import, transitively, read by `ast` from the checkout's committed files (the
    design's imports.py): the names the vendoring must hold, and no other module of the package."""
    seen, todo = set(), list(START)
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        rel = name.replace(".", "/")
        for candidate in (rel + ".py", rel + "/__init__.py"):
            try:
                data = committed(root, candidate)
            except AssertionError:
                continue
            seen.add(name)
            package = name if candidate.endswith("__init__.py") else name.rpartition(".")[0]
            for node in ast.walk(ast.parse(data.decode("utf-8"))):
                if isinstance(node, ast.ImportFrom):
                    if node.level:
                        base = package.split(".")
                        base = base[:len(base) - (node.level - 1)]
                        mod = ".".join(base + ([node.module] if node.module else []))
                        todo.append(mod)
                        todo.extend(f"{mod}.{a.name}" for a in node.names)
                    elif node.module and node.module.startswith("quantum_film"):
                        todo.append(node.module)
                        todo.extend(f"{node.module}.{a.name}" for a in node.names)
                elif isinstance(node, ast.Import):
                    todo.extend(a.name for a in node.names if a.name.startswith("quantum_film"))
            break
    return seen


def test_the_vendored_modules_are_the_transitive_closure_of_the_runners_nine():
    got = closure(moth_root())
    paths = {m.replace(".", "/") + ".py" if (VENDOR / (m.replace(".", "/") + ".py")).exists()
             else m.replace(".", "/") + "/__init__.py" for m in got}
    listed = {r for _s, _n, r in entries() if r.startswith("quantum_film/")}
    assert len(got) == 22 and paths == listed


def test_the_closure_imports_no_vendor_atlas_film_and_only_numpy_and_mpmath_beyond_the_standard_library():
    root = moth_root()
    third = set()
    import sys
    for _s, _n, rel in entries():
        if not rel.startswith("quantum_film/"):
            continue
        for node in ast.walk(ast.parse(committed(root, rel).decode("utf-8"))):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module] if isinstance(node, ast.ImportFrom) and node.module and not node.level else []
            third |= {n.split(".")[0] for n in names} - set(sys.stdlib_module_names) - {"quantum_film"}
    assert third == {"numpy", "mpmath"}
