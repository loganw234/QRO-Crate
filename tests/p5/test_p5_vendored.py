"""What the kit carries of Quantum-Film and of its environment (P5's design, item 2; qro_kit/_vendor, VENDORED.sha256,
environment.lock, NOTICE.md): the 22 modules, the licence and the source circuit are the bytes the list holds, nothing else
is vendored, the source circuit is the twin's copy byte for byte, and the loader refuses a changed byte or a shadowing
quantum_film. A changed vendored byte fails this stage; tests/p5crates holds the same files to a moth-quantum checkout."""
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
from p5_support import ROOT, no_network  # noqa: F401

from qro_kit import _qf

pytestmark = pytest.mark.usefixtures("no_network")
VENDOR = ROOT / "qro_kit" / "_vendor"
TWIN_CIRCUIT = ROOT / "tests" / "p1" / "data" / "moth" / "docs" / "records" / "2026-09-25" / "p3" / "circuit-ed767c01bd4b851d.qasm"


def listed():
    return _qf.entries()


def test_the_list_names_22_modules_the_licence_and_the_circuit():
    rels = [r for _s, _n, r in listed()]
    modules = [r for r in rels if r.startswith("quantum_film/")]
    assert len(modules) == 22 and sum(n for _s, n, r in listed() if r in modules) == 194_424
    assert sorted(set(rels) - set(modules)) == ["LICENSE-quantum-film", "circuit-ed767c01bd4b851d.qasm"]
    assert len(set(rels)) == len(rels)


@pytest.mark.parametrize("sha, size, rel", listed(), ids=[r for _s, _n, r in listed()])
def test_each_vendored_file_is_the_bytes_the_list_holds(sha, size, rel):
    data = (VENDOR / rel).read_bytes()
    assert len(data) == size and hashlib.sha256(data).hexdigest() == sha


def test_the_vendored_bytes_are_ascii_with_line_feeds_only():
    """Moth's bytes: pure ASCII, LF, no tab (a byte scan of moth-quantum at 3a73823); the kit keeps them as they are."""
    for _s, _n, rel in listed():
        data = (VENDOR / rel).read_bytes()
        assert data.isascii() and b"\r" not in data and b"\t" not in data, rel


def test_nothing_else_is_vendored():
    on_disk = {p.relative_to(VENDOR).as_posix() for p in (VENDOR / "quantum_film").rglob("*") if p.is_file()}
    assert on_disk == {r for _s, _n, r in listed() if r.startswith("quantum_film/")}
    assert {p.name for p in VENDOR.iterdir()} == {"quantum_film", "VENDORED.sha256", "LICENSE-quantum-film",
                                                   "circuit-ed767c01bd4b851d.qasm"}


def test_the_loader_finds_no_problem_in_the_tree():
    assert _qf.problems() == []


def test_the_source_circuit_is_the_one_ed767c01_and_the_twins_copy_byte_for_byte():
    data = (VENDOR / "circuit-ed767c01bd4b851d.qasm").read_bytes()
    assert hashlib.sha256(data).hexdigest().startswith("ed767c01bd4b851d") and data == TWIN_CIRCUIT.read_bytes()
    assert (VENDOR / "LICENSE-quantum-film").read_bytes() == (ROOT / "tests" / "p1" / "data" / "moth" / "LICENSE").read_bytes()


def test_the_loader_refuses_a_changed_byte(monkeypatch, tmp_path):
    copy = tmp_path / "_vendor"
    copy.mkdir()
    for _s, _n, rel in listed():
        (copy / rel).parent.mkdir(parents=True, exist_ok=True)
        (copy / rel).write_bytes((VENDOR / rel).read_bytes())
    (copy / "VENDORED.sha256").write_bytes((VENDOR / "VENDORED.sha256").read_bytes())
    monkeypatch.setattr(_qf, "VENDOR", copy)
    monkeypatch.setattr(_qf, "LIST", copy / "VENDORED.sha256")
    assert _qf.problems() == []
    target = copy / "quantum_film" / "ibm" / "decode.py"
    target.write_bytes(target.read_bytes().replace(b"M - 1 - p", b"p", 1))
    assert [p for p in _qf.problems() if "decode.py" in p] and _qf.problems() != []
    with pytest.raises(_qf.VendoredError, match="not the pinned code"):
        _qf.load("keyleak")


def test_the_loader_refuses_a_python_file_the_list_does_not_name(monkeypatch, tmp_path):
    copy = tmp_path / "_vendor"
    for _s, _n, rel in listed():
        (copy / rel).parent.mkdir(parents=True, exist_ok=True)
        (copy / rel).write_bytes((VENDOR / rel).read_bytes())
    (copy / "VENDORED.sha256").write_bytes((VENDOR / "VENDORED.sha256").read_bytes())
    (copy / "quantum_film" / "extra.py").write_bytes(b"x = 1\n")
    monkeypatch.setattr(_qf, "VENDOR", copy)
    monkeypatch.setattr(_qf, "LIST", copy / "VENDORED.sha256")
    assert any("extra.py" in p for p in _qf.problems())


@pytest.mark.parametrize("name", ["ext.pyd", "ext.cp312-win_amd64.pyd", "ext.so", "ext.pyc", "__pycache__/decode.cpython-312.pyc",
                                  "data.txt", "extra", "ibm/extra.json"])
def test_the_loader_refuses_any_file_the_list_does_not_name_not_only_a_py(monkeypatch, tmp_path, name):
    """A .pyd or a sourceless .pyc loads ahead of the source (the first verifier, round 1): every unlisted file is refused."""
    copy = tmp_path / "_vendor"
    for _s, _n, rel in listed():
        (copy / rel).parent.mkdir(parents=True, exist_ok=True)
        (copy / rel).write_bytes((VENDOR / rel).read_bytes())
    (copy / "VENDORED.sha256").write_bytes((VENDOR / "VENDORED.sha256").read_bytes())
    monkeypatch.setattr(_qf, "VENDOR", copy)
    monkeypatch.setattr(_qf, "LIST", copy / "VENDORED.sha256")
    assert _qf.problems() == []
    planted = copy / "quantum_film" / name
    planted.parent.mkdir(parents=True, exist_ok=True)
    planted.write_bytes(b"not python\n")
    assert [p for p in _qf.problems() if planted.name in p and "does not list" in p]
    with pytest.raises(_qf.VendoredError, match="not the pinned code"):
        _qf.load("keyleak")


def test_the_loader_refuses_a_link_to_a_directory_the_list_does_not_name(monkeypatch, tmp_path):
    """A link (a junction on Windows) to an empty directory lists no file under it, so only the link itself can be refused."""
    import os
    copy = tmp_path / "_vendor"
    for _s, _n, rel in listed():
        (copy / rel).parent.mkdir(parents=True, exist_ok=True)
        (copy / rel).write_bytes((VENDOR / rel).read_bytes())
    (copy / "VENDORED.sha256").write_bytes((VENDOR / "VENDORED.sha256").read_bytes())
    monkeypatch.setattr(_qf, "VENDOR", copy)
    monkeypatch.setattr(_qf, "LIST", copy / "VENDORED.sha256")
    target = tmp_path / "empty"
    target.mkdir()
    link = copy / "quantum_film" / "linked"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)
    else:
        os.symlink(target, link)
    try:
        assert [p for p in _qf.problems() if "linked" in p and "does not list" in p]
    finally:
        os.rmdir(link) if os.name == "nt" else os.unlink(link)
    assert _qf.problems() == []


def test_the_loader_refuses_a_different_quantum_film_already_imported(monkeypatch, tmp_path):
    fake = type(sys)("quantum_film")
    fake.__file__ = str(tmp_path / "somewhere" / "quantum_film" / "__init__.py")
    monkeypatch.setitem(sys.modules, "quantum_film", fake)
    with pytest.raises(_qf.VendoredError, match="different quantum_film"):
        _qf.load("keyleak")


def test_the_environment_lock_is_the_leads_40_packages():
    lines = [ln for ln in (ROOT / "qro_kit" / "environment.lock").read_text(encoding="ascii").splitlines()
             if ln and not ln.startswith("#")]
    pins = dict(ln.split("==") for ln in lines)
    assert len(lines) == len(pins) == 40
    assert (pins["qiskit"], pins["qiskit-ibm-runtime"], pins["qiskit-aer"], pins["numpy"], pins["mpmath"]) == (
        "2.5.2", "0.50.0", "0.17.2", "2.5.3", "1.3.0")
    assert b"\r" not in (ROOT / "qro_kit" / "environment.lock").read_bytes()


def test_notice_names_the_vendored_code_and_its_licence():
    text = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
    assert "Quantum-Film" in text and "qro_kit/_vendor" in text
    for _s, _n, rel in listed():
        if rel.startswith("quantum_film/"):
            assert f"`{rel[len('quantum_film/'):]}`" in text, f"NOTICE.md does not name {rel}"
    assert "circuit-ed767c01bd4b851d.qasm" in text and "MIT" in text


def test_this_file_reads_the_tree_it_is_in():
    assert Path(_qf.__file__).resolve().is_relative_to(ROOT)
