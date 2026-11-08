"""The ten files of Quantum-Film's that P2's tests read are P1's twin's (the lead's decision 9 on P2's design; P2.2): each
name P2's tests read one under is a file of the twin's records, under tests/p1/data/moth, LF with no CR as it is in
moth-quantum; and P2 keeps no copy of any file of the twin, so each has one place in the tree. P2.1 kept ten copies
beside its tests; the twin carries the same bytes, so none stays. That the twin's files are moth-quantum's at 3a73823,
byte for byte, is held by P2's crate-level stage (tests/p2crates), which reads moth-quantum."""
import hashlib
from pathlib import Path

from p2_builder import RECORDS, SOURCE_RECORD, TWIN_FILES, data

from qro import p2_law

HERE = Path(__file__).resolve().parent


def sha(b):
    return hashlib.sha256(b).hexdigest()


def test_each_file_p2s_tests_read_is_a_file_of_p1s_twin_under_its_own_name():
    assert len(TWIN_FILES) == 10
    for name, rel in TWIN_FILES.items():
        path = RECORDS.joinpath(*rel.split("/"))
        assert path.is_file() and path.name == name, name
        assert data(name) == path.read_bytes() and b"\r" not in data(name), name


def test_the_source_circuit_p2_reads_is_the_one_its_law_is_written_for():
    assert TWIN_FILES["circuit-ed767c01bd4b851d.qasm"] == SOURCE_RECORD
    assert sha(data("circuit-ed767c01bd4b851d.qasm")) == p2_law.SOURCE_CIRCUIT


def test_p2_keeps_no_copy_of_a_file_of_the_twin():
    """No file under P2's tests holds the bytes of a file of the twin: one place for each fact. The control: the walk
    finds a twin file's bytes where they are."""
    twin = {sha(p.read_bytes()) for p in RECORDS.rglob("*") if p.is_file()}
    mine = [p for p in sorted(HERE.rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    assert mine and not [p.name for p in mine if sha(p.read_bytes()) in twin]
    assert not (HERE / "data").exists()
    assert sha(data("law.gates.json")) in twin
