"""docs/P3.md names the tests that hold its claims: each name it gives is a test of the file it names, and each file of
P3's tests it names is there (P3.1; the brief's rule that every claim names the test that holds it, or says none
does)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / "docs" / "P3.md").read_text(encoding="utf-8")


def defined():
    """{a test file's short name, as the page writes it: the test functions it defines}."""
    out = {}
    for d, strip in (("p3", "test_p3_"), ("p3crates", "test_")):
        for f in sorted((ROOT / "tests" / d).glob("test_*.py")):
            out[f.stem[len(strip):]] = set(re.findall(r"^def (test_[A-Za-z0-9_]+)\(", f.read_text(encoding="utf-8"),
                                                      re.M))
    return out


def cited():
    """[(the short name of the file a parenthesis names, a test name it gives)] in the page's order: each `(file:` opens
    a run of names, which the next `file:` ends."""
    out, current = [], None
    for m in re.finditer(r"(?:\(|;\s+)([a-z0-9_]+):\s|`(test_[A-Za-z0-9_]*[A-Za-z0-9])`|\(([a-z0-9_]+)\)", PAGE):
        if m.group(1) or m.group(3):
            current = m.group(1) or m.group(3)
        else:
            out.append((current, m.group(2)))
    return out


def test_every_test_the_page_names_is_a_test_of_its_file():
    files = defined()
    names = cited()
    assert len(names) > 150
    missing = [(f, n) for f, n in names if f not in files or n not in files[f]]
    assert missing == []


def test_the_page_test_can_fail():
    files = defined()
    assert "test_no_such_test" not in files["declaration"]
    assert ("declaration", "test_no_such_test") not in cited()
