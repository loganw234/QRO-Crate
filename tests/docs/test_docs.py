"""The documents' gate holds on the tree, and is watched to fail on each of the four faults its docstring names: a
broken link, an unindexed document, a missing index, and a missing path named. And FORMAT.md's item 8 names each
refusal of P0's that the study does not, names none the table lacks, and counts nothing before its first colon.
"""
import importlib.util
import re
from pathlib import Path

from qro import vocabulary as V

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("check_docs", ROOT / "tools" / "check_docs.py")
check_docs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_docs)


def tree(tmp_path, index, extra=None, source=None):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text(index, encoding="utf-8")
    (tmp_path / "docs" / "A.md").write_text("a document\n", encoding="utf-8")
    for name, text in (extra or {}).items():
        (tmp_path / "docs" / name).write_text(text, encoding="utf-8")
    if source is not None:
        (tmp_path / "qro").mkdir()
        (tmp_path / "qro" / "x.py").write_text(source, encoding="utf-8")
    return tmp_path


def test_the_tree_is_clean():
    assert check_docs.problems() == []


def test_a_clean_planted_tree_is_clean(tmp_path):
    assert check_docs.problems(tree(tmp_path, "[A](A.md)\n")) == []


def test_a_broken_link_is_caught(tmp_path):
    root = tree(tmp_path, "[A](A.md) [B](B.md)\n")
    assert check_docs.problems(root) == ["docs/README.md: link to B.md does not resolve"]


def test_an_unindexed_document_is_caught(tmp_path):
    root = tree(tmp_path, "[A](A.md)\n", extra={"C.md": "unindexed\n"})
    assert check_docs.problems(root) == ["docs/README.md does not index C.md"]


def test_a_missing_index_is_caught(tmp_path):
    root = tree(tmp_path, "[A](A.md)" + chr(10))
    (root / "docs" / "README.md").unlink()
    assert check_docs.problems(root) == ["docs/README.md, the index, is missing"]


def test_a_missing_path_named_in_source_is_caught(tmp_path):
    root = tree(tmp_path, "[A](A.md)\n", source='"""see qro/nowhere.py"""\n')
    assert check_docs.problems(root) == ["qro/x.py:1: names qro/nowhere.py, which does not exist"]


def test_a_path_on_a_line_naming_another_repository_is_not_checked(tmp_path):
    """A stated limit: the whole line is skipped, so a wrong path of this repository's on it passes."""
    root = tree(tmp_path, "[A](A.md)\n", source='"""moth-quantum names qro/nowhere.py"""\n')
    assert check_docs.problems(root) == []


def test_a_broken_link_in_a_report_under_docs_is_caught(tmp_path):
    """Round 3, note 14: a markdown file under docs/ that the index does not list is still link-checked."""
    root = tree(tmp_path, "[A](A.md)\n")
    (root / "docs" / "reviews" / "R").mkdir(parents=True)
    (root / "docs" / "reviews" / "R" / "README.md").write_text("[gone](gone.md)\n", encoding="utf-8")
    assert check_docs.problems(root) == ["docs/reviews/R/README.md: link to gone.md does not resolve"]


# -- FORMAT.md item 8: P0's own refusal names, derived, never counted by hand -----------------------------------
def p0_own_problems(format_text, study_text):
    """FORMAT.md's item 8 names every P0 refusal the study never names, names no refusal the table lacks, and
    counts nothing before its first colon: a count kept by hand went stale once already (P0's verifier, round 2,
    R2-6: "Seven" over a list of eight). A count further on, in a bullet, is not read (round 5, R5-2)."""
    m = re.search(r"^8\. (.*?)(?=^9\. )", format_text, re.M | re.S)
    if m is None:
        return ["FORMAT.md has no item 8"]
    item = m.group(1)
    own = [r.name for r in V.REFUSALS if r.owner == "P0" and f"`{r.name}`" not in study_text]
    out = [f"item 8 does not name {n}" for n in own if f"`{n}`" not in item]
    out += [f"item 8 names {n}, which the table lacks" for n in re.findall(r"`([a-z]+(?:-[a-z]+)+|[a-z]+)`", item)
            if n not in V.REFUSAL]
    lead = item.split(":", 1)[0]
    if re.search(r"(?i)\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen|[0-9]+)\b", lead):
        out.append("item 8 counts its names by hand")
    return out


def _texts():
    return ((ROOT / "docs" / "FORMAT.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "studies" / "QRO-0.md").read_text(encoding="utf-8"))


def test_format_names_every_refusal_that_is_p0s_own():
    assert p0_own_problems(*_texts()) == []


def test_a_p0_name_missing_from_item_8_is_caught():
    fmt, study = _texts()
    planted = fmt.replace("`step-unbuilt` is the seam's own", "the seam's refusal is its own", 1)
    assert planted != fmt
    assert p0_own_problems(planted, study) == ["item 8 does not name step-unbuilt"]


def test_a_count_in_item_8_is_caught():
    fmt, study = _texts()
    for count in ("Seven refusal names are P0's own", "These eight names are P0's own", "These 8 names are P0's own"):
        planted = fmt.replace("These refusal names are P0's own", count, 1)
        assert planted != fmt
        assert p0_own_problems(planted, study) == ["item 8 counts its names by hand"], count


def test_a_name_in_item_8_the_table_lacks_is_caught():
    fmt, study = _texts()
    planted = fmt.replace("`step-unbuilt` is the seam's own", "`step-unbuilt` and `seam-broken` are the seam's own", 1)
    assert planted != fmt
    assert p0_own_problems(planted, study) == ["item 8 names seam-broken, which the table lacks"]
