"""The copies under tests/p2/data are what their README says (docs/P2.md, the files): every file but the README is a row
of its table, with its size and its SHA-256, and no row names a file that is not there; the sizes add up to the total
the README states; and the copies are LF, with no CR, as they are in moth-quantum. That they equal moth-quantum's at
3a73823, byte for byte, is held by no test of P2.1's: the first verifier measured it, and P2.2's crate-level stage,
which reads moth-quantum where QRO_MOTH_ROOT names it, is where a test can."""
import hashlib
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
ROW = re.compile(r"\| ([^ |]+) \| ([0-9,]+) \| `([0-9a-f]{64})` \|")


def rows():
    """{file: (bytes, SHA-256)}, from the README's table."""
    text = (DATA / "README.md").read_text(encoding="utf-8")
    return {m.group(1): (int(m.group(2).replace(",", "")), m.group(3)) for m in ROW.finditer(text)}


def test_every_copy_is_a_row_of_its_readme_with_its_size_and_digest():
    copies = sorted(p.name for p in DATA.iterdir() if p.name != "README.md")
    table = rows()
    assert sorted(table) == copies and len(copies) == 10
    for name in copies:
        data = (DATA / name).read_bytes()
        assert table[name] == (len(data), hashlib.sha256(data).hexdigest()), name
        assert b"\r" not in data, name


def test_the_readme_states_the_total_its_rows_add_up_to():
    assert sum(size for size, _ in rows().values()) == 157309
    assert "10 files, 157,309 bytes." in " ".join((DATA / "README.md").read_text(encoding="utf-8").split())


def test_the_table_reader_reads_a_row():
    """The control: the pattern reads a row as the README spells one, and nothing from a row out of that spelling."""
    good = "| x.json | 1,234 | `" + "a" * 64 + "` | moth-quantum `docs/x.json` |"
    assert [m.groups() for m in ROW.finditer(good)] == [("x.json", "1,234", "a" * 64)]
    assert not list(ROW.finditer(good.replace("`", "")))
