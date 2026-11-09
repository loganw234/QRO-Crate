"""No test of P5 reaches a network (P5's design, item 6): the autouse fixture of each stage's support module makes
`socket.socket.connect` and `socket.getaddrinfo` raise, and every test module of the three stages lists it (no conftest.py is
allowed, so a module imports the fixture and names it in `pytestmark`). The kit builds no way to connect to IBM in P5.1, and
the stand-in service answers from memory."""
import ast
import re
import socket
from pathlib import Path

import pytest
from p5_support import NetworkRefused, no_network  # noqa: F401

pytestmark = pytest.mark.usefixtures("no_network")
ROOT = Path(__file__).resolve().parents[2]


def test_the_gate_refuses_a_name_lookup_and_a_connection():
    with pytest.raises(NetworkRefused):
        socket.getaddrinfo("example.invalid", 80)
    with pytest.raises(NetworkRefused), socket.socket() as s:
        s.connect(("127.0.0.1", 9))


def test_every_test_module_of_the_three_stages_imports_the_gate_and_lists_it():
    modules = [p for d in ("p5", "p5kit", "p5crates") for p in sorted((ROOT / "tests" / d).glob(f"test_{d}_*.py"))]
    assert len(modules) >= 12
    for path in modules:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {a.name for n in tree.body if isinstance(n, ast.ImportFrom) for a in n.names}
        assert "no_network" in imported, f"{path.name} does not import the gate"
        marks = [n for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "pytestmark"
                                                                           for t in n.targets)]
        assert marks and "no_network" in ast.unparse(marks[0].value), f"{path.name} does not list the gate"


def test_no_conftest_and_no_pytest_plugins_line_in_the_three_stages():
    for d in ("p5", "p5kit", "p5crates"):
        assert not list((ROOT / "tests" / d).glob("conftest.py"))
        for p in (ROOT / "tests" / d).glob("*.py"):
            assert not re.search(r"^[ \t]*pytest_plugins[ \t]*[:=]", p.read_text(encoding="utf-8"), re.M), p.name
