"""The one place Quantum-Film's code is put on the import path (P5's design, item 2; P5.1).

The kit carries 22 modules of Quantum-Film's runner, byte for byte, under `_vendor/quantum_film/`, with its licence and
`VENDORED.sha256`. A stranger has no moth-quantum checkout, so the kit never imports one: `load()` puts `_vendor/` on
`sys.path`, here and nowhere else, and imports the package from it. It refuses
  - a different `quantum_film` already imported (a moth checkout shadowing the pinned code would be run in its place),
  - and a vendored file that is missing or whose bytes are not the ones VENDORED.sha256 lists (a changed byte, or any file
    in `_vendor/quantum_film/` that the list does not name: a .pyd and a .pyc among them, not only a .py).
`load()` is called before any other module of the kit imports a vendored name, and imports numpy, mpmath and qiskit only
through the vendored modules that need them (the runner's callers import qiskit themselves, inside functions).
"""
import hashlib
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

VENDOR = Path(__file__).resolve().parent / "_vendor"
LIST = VENDOR / "VENDORED.sha256"
MODULES = {"fixer": "quantum_film.fixer", "bundle": "quantum_film.ibm.bundle", "runner": "quantum_film.ibm.runner",
           "account": "quantum_film.ibm.account", "anchor": "quantum_film.ibm.anchor", "decode": "quantum_film.ibm.decode",
           "isa": "quantum_film.ibm.isa", "keyleak": "quantum_film.ibm.keyleak", "raw": "quantum_film.ibm.raw"}


class VendoredError(RuntimeError):
    """The vendored code is not the code the kit pins."""


def entries():
    """[(SHA-256, size, path under _vendor/)] of VENDORED.sha256's lines."""
    out = []
    for line in LIST.read_text(encoding="ascii").splitlines():
        if line and not line.startswith(("#", "commit ")):
            sha, size, rel = line.split("  ")
            out.append((sha, int(size), rel))
    return out


def problems():
    """The named reasons the vendored files are not VENDORED.sha256's: a file missing, a byte changed, a Python module in
    the package that the list does not name."""
    out, listed = [], set()
    for sha, size, rel in entries():
        listed.add(rel)
        try:
            data = (VENDOR / rel).read_bytes()
        except OSError:
            out.append(f"{rel}: missing")
            continue
        if len(data) != size or hashlib.sha256(data).hexdigest() != sha:
            out.append(f"{rel}: its bytes are not the ones VENDORED.sha256 lists")
    for p in sorted((VENDOR / "quantum_film").rglob("*")):       # every file, not only *.py: a .pyd or a sourceless .pyc loads
        if p.is_dir() and not (p.is_symlink() or p.is_junction()):      # a link to a directory is an entry that is not listed
            continue
        rel = p.relative_to(VENDOR).as_posix()
        if rel not in listed:
            out.append(f"{rel}: a file VENDORED.sha256 does not list")
    return out


def load(*names):
    """The vendored modules asked for (all of MODULES when none is), as attributes of one namespace. VendoredError for the
    refusals of the module docstring."""
    sys.dont_write_bytecode = True
    shadow = sys.modules.get("quantum_film")
    if shadow is not None:
        try:
            Path(shadow.__file__).resolve().relative_to(VENDOR)
        except (AttributeError, TypeError, ValueError):
            raise VendoredError("a different quantum_film is already imported: the kit runs its own pinned copy "
                                "only") from None
    bad = problems()
    if bad:
        raise VendoredError("the vendored code is not the pinned code: " + "; ".join(bad[:3]))
    if str(VENDOR) not in sys.path:
        sys.path.insert(0, str(VENDOR))
    return SimpleNamespace(**{n: importlib.import_module(MODULES[n]) for n in (names or MODULES)})
