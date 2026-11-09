"""The kit's environment (P5's design, item 4; qro_kit/environment.lock; QRO_KIT_PYTHON): asserted first, loudly, as p4-shacl
asserts its engine's version; the vendored code imports in it and is the pinned code; and the offline gate of the kit's own
process: no network is reached by importing the kit or by building a bundle for a fake backend."""
import pytest
from p5kit_support import ROOT, assert_the_environment, kit_run, no_network  # noqa: F401

pytestmark = pytest.mark.usefixtures("no_network")


def test_the_kits_interpreter_holds_the_locks_pins_on_python_3_12():
    got = assert_the_environment()
    assert got["pins"]["qiskit"] == "2.5.2" and got["pins"]["qiskit-ibm-runtime"] == "0.50.0"


def test_the_sandboxs_hook_is_the_kit_interpreters_sitecustomize():
    """The kit's code is held to the sandbox whoever starts it (lead.md 2026-11-08T15:49:05Z): a write outside it is refused."""
    code = ("import sys, tempfile, os\n"
            "root = os.environ.get('QRO_SBX_ROOT')\n"
            "where = os.path.dirname(os.path.realpath(root)) if root else tempfile.gettempdir()\n"
            "try:\n    open(os.path.join(where, 'qro-p5-hook-probe.txt'), 'w')\n"
            "except PermissionError as e:\n    print('refused', 'QRO sandbox' in str(e))\n"
            "else:\n    print('WROTE')\n")
    p = kit_run(["-I", "-c", code])
    assert p.stdout.strip() == b"refused True", (p.stdout, p.stderr[-300:])


def test_the_vendored_code_imports_in_the_kit_environment_and_is_the_pinned_code():
    code = ("import sys\nsys.path.insert(0, %r)\nfrom qro_kit import _qf\n"
            "assert _qf.problems() == [], _qf.problems()\nq = _qf.load()\n"
            "import quantum_film\nprint(quantum_film.__version__, sorted(vars(q)), q.bundle.M, "
            "quantum_film.__file__.replace('\\\\', '/').split('qro_kit/')[-1])\n") % str(ROOT)
    p = kit_run(["-I", "-c", code])
    assert p.returncode == 0, p.stderr[-800:]
    assert p.stdout.decode().startswith("0.1.0 ['account', 'anchor', 'bundle', 'decode', 'fixer', 'isa', 'keyleak', 'raw', "
                                        "'runner'] 16 _vendor/quantum_film/__init__.py")


def test_importing_the_kit_and_loading_the_vendored_code_writes_no_bytecode_into_the_tree():
    before = {p for p in (ROOT / "qro_kit").rglob("__pycache__")}
    p = kit_run(["-I", "-c", "import sys; sys.path.insert(0, %r); from qro_kit import _qf, submit, unit_bundle; _qf.load()"
                 % str(ROOT)])
    assert p.returncode == 0, p.stderr[-500:]
    assert {q for q in (ROOT / "qro_kit").rglob("__pycache__")} == before
