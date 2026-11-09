"""v0's three devices compared as selections of one crate (P3's design, item 13; the study's seam test 2): kingston
against fez reproduces section 6.1 of the study, every figure of its table at its four places, every status and both
"isolated" columns, read from the study's own text and accepted by `python -m qro compare` as a process; the five-crystal
share's difference P2's pinned endpoints exactly; and kingston against marrakesh and marrakesh against fez pinned at the
design's figures, with each device's pooled values."""
import re
from fractions import Fraction

import pytest

import p3crates_support as S

STUDY = S.ROOT / "docs" / "studies" / "QRO-0.md"
LEFT, RIGHT, MINUS, DASH = chr(0x27E8), chr(0x27E9), chr(0x2212), chr(0x2014)   # the study's angle brackets, its
# minus and its dash, written by their codes so that this file stays ASCII, as P2's tests are (P2.2's N7)
LABELS = {"five-crystal share": "n-crystal-share", "forbidden share": "forbidden-share", "linear XEB": "linear-xeb",
          LEFT + "X0X1" + RIGHT: "x0x1", LEFT + "Y0Y1" + RIGHT: "y0y1"}
K, M, F = "ibm_kingston", "ibm_marrakesh", "ibm_fez"


def section_61_table():
    """Section 6.1's certified verdicts, row by row, as the study writes them."""
    text = STUDY.read_text(encoding="utf-8").split("### 6.1 Worked example", 1)[1].split("## 7.", 1)[0]
    rows = [line for line in text.splitlines() if line.startswith("| ")]
    head = rows[0]
    assert head.startswith("| measure | class (uniform / dephased twin) | day means, certified |")
    return [[c.strip() for c in r.split(" | ")] for r in rows[1:]]


def signed(x):
    return S.four(x).replace("-", MINUS)


def unsigned(x):
    return f"{float(Fraction(x)):.4f}"


@pytest.fixture(scope="module")
def kf():
    return S.comparison(S.device(K), S.device(F))


def test_kingston_against_fez_is_accepted_by_the_command_as_a_process(kf):
    out, record = kf
    ibm = S.built("ibm")
    p = S.process(["compare", str(out), str(ibm)], module="qro")
    assert (p.returncode, p.stderr) == (0, ""), (S.mask(p.stdout[-300:]), S.mask(p.stderr[-300:]))
    assert p.stdout.strip().endswith(": declared real; exploratory (selector-late); 5 measures")
    assert record["family"] == 70 and record["late"] == "selector-late" and record["kind"] == "real"


def test_kingston_against_fez_is_section_61s_table_figure_for_figure(kf):
    _, record = kf
    rows = section_61_table()
    assert [LABELS[r[0].lstrip("| ")] for r in rows] == ["n-crystal-share", "forbidden-share", "linear-xeb", "x0x1",
                                                          "y0y1"]
    for r in rows:
        m = S.measure(record, LABELS[r[0].lstrip("| ")])
        uniform, dephased = r[1].split(" / ")
        assert (m["classes"]["a"]["uniform"], m["classes"]["a"]["dephased"]) == (uniform, dephased)
        word = re.match(r"\*\*(differ|agree|unresolved)\*\*", r[2]).group(1)
        lo, hi = re.search(r"\[([^,]+), ([^\]]+)\]", r[2]).groups()
        assert (m["means"], signed(m["difference"][0]), signed(m["difference"][1])) == (word, lo, hi), r[0]
        if r[3].startswith("UNMEASURED"):
            assert (m["a"]["drift"], m["b"]["drift"], m["strongForm"]) == ("none", "none", "none")
            assert r[4] == DASH
        else:
            assert f"{unsigned(m['a']['drift'])} / {unsigned(m['b']['drift'])}" == r[3]
            assert r[4].split(":")[0] == signed(m["strongForm"])


def test_section_61s_statuses_and_isolated_columns_are_the_records(kf):
    _, record = kf
    for r in section_61_table():
        m = S.measure(record, LABELS[r[0].lstrip("| ")])
        c = m["causes"]
        assert (c["question"], c["compile"], c["hold"], c["submitted"], c["commit"], c["sampling"], c["device"]) == (
            "EQUAL", "DIFFERS", "holds", "EQUAL", "unknown", "CONTROLLED", "DIFFERS")
        assert m["readout"] == {"bound": "none", "status": "UNMEASURED"}
        words = set(m["statements"])
        pipeline, quantum = r[5], r[6]
        if "strong form not above" in pipeline:
            assert {"strong-form-short", "commit-unknown"} <= words and c["drift"] == "CONTROLLED"
        else:
            assert "drift UNMEASURED" in pipeline and {"drift-unmeasured", "commit-unknown"} <= words
        assert pipeline.startswith("no:") and "isolated-pipeline" not in words
        assert quantum.startswith("no: not isolated from the pipeline; readout UNMEASURED")
        assert {"quantum-unpiped", "readout-unbounded", "device-and-time"} <= words
        if "integrity against both twins" in quantum:
            assert {"integrity-dephased", "integrity-uniform"} <= words
        elif "signal against the uniform twin only" in quantum:
            assert "integrity-dephased" in words and "integrity-uniform" not in words
        else:
            assert not {"integrity-dephased", "integrity-uniform"} & words
        assert m["unseen"] == ["question", "submitted", "decode", "known-answer", "date"]


def test_the_five_crystal_shares_difference_is_p2s_pinned_endpoints_exactly(kf):
    _, record = kf
    d = S.measure(record, "n-crystal-share")["difference"]
    assert [Fraction(x) * 2 ** 48 for x in d] == [12330612205551, 16819644152847]


PINNED = {  # the design's item 13: (family, {measure: (means, difference, drifts, strong form)})
    (K, M): (70, {"n-crystal-share": ("differ", ("+0.0611", "+0.0770"), ("0.0307", "0.0406"), "-0.0103"),
                  "forbidden-share": ("differ", ("-0.0133", "-0.0042"), ("0.0123", "0.0219"), "-0.0299"),
                  "linear-xeb": ("unresolved", ("-0.0490", "+0.0774"), ("0.1575", "0.1743"), "-0.3318"),
                  "x0x1": ("unresolved", ("-0.0997", "+0.1358"), None, None),
                  "y0y1": ("unresolved", ("-0.1313", "+0.1030"), None, None)}),
    (M, F): (76, {"n-crystal-share": ("differ", ("-0.0249", "-0.0096"), ("0.0407", "0.0324"), "-0.0636"),
                  "forbidden-share": ("unresolved", ("-0.0044", "+0.0049"), ("0.0219", "0.0138"), "-0.0358"),
                  "linear-xeb": ("unresolved", ("-0.0603", "+0.0631"), ("0.1750", "0.1656"), "-0.3406"),
                  "x0x1": ("unresolved", ("-0.0753", "+0.1639"), None, None),
                  "y0y1": ("unresolved", ("-0.0793", "+0.1572"), None, None)}),
    (K, F): (70, {"n-crystal-share": ("differ", ("+0.0438", "+0.0598"), ("0.0307", "0.0323"), "-0.0193"),
                  "forbidden-share": ("differ", ("-0.0130", "-0.0040"), ("0.0123", "0.0138"), "-0.0220"),
                  "linear-xeb": ("unresolved", ("-0.0471", "+0.0783"), ("0.1575", "0.1650"), "-0.3225"),
                  "x0x1": ("unresolved", ("-0.0562", "+0.1809"), None, None),
                  "y0y1": ("unresolved", ("-0.0931", "+0.1428"), None, None)})}


@pytest.mark.parametrize("pair", list(PINNED), ids=["kingston-marrakesh", "marrakesh-fez", "kingston-fez"])
def test_each_pair_is_pinned_at_the_designs_figures(pair):
    _, record = S.comparison(S.device(pair[0]), S.device(pair[1]))
    family, figures = PINNED[pair]
    assert record["family"] == family
    for name, (means, diff, drifts, strong) in figures.items():
        m = S.measure(record, name)
        assert (m["means"], S.four(m["difference"][0]), S.four(m["difference"][1])) == (means, *diff), name
        if drifts is None:
            assert (m["a"]["drift"], m["b"]["drift"], m["strongForm"]) == ("none",) * 3
        else:
            assert (unsigned(m["a"]["drift"]), unsigned(m["b"]["drift"]), S.four(m["strongForm"])) == (*drifts, strong)


VALUES = {K: ("+0.5957", "+0.0428", "+0.8567", "+0.3315", "+0.3296"),
          M: ("+0.5267", "+0.0516", "+0.8426", "+0.3135", "+0.3438"),
          F: ("+0.5439", "+0.0514", "+0.8411", "+0.2690", "+0.3047")}


def test_each_devices_pooled_values_are_the_designs_figures():
    """The design's item 13 READ these equal to moth-quantum's docs/HARDWARE-RESULTS.md; P2's p2-crates stage holds the
    crate's measurements to that page itself."""
    order = ("n-crystal-share", "forbidden-share", "linear-xeb", "x0x1", "y0y1")
    for a, b in ((K, M), (M, F)):
        _, record = S.comparison(S.device(a), S.device(b))
        for side, dev in (("a", a), ("b", b)):
            assert tuple(S.four(S.measure(record, m)[side]["value"]) for m in order) == VALUES[dev], dev
