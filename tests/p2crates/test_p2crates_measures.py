"""P2's measures on v0's crates against Quantum-Film's printed figures (P2's design, items 1 and 4; P2.2), read at run time
from moth-quantum's docs/HARDWARE-RESULTS.md: the 21 morning cells (seven measures on each device's morning law and
coherence PUBs), each the CHECKED value of the accepted IBM crate's Measurement; every law run of the sheet tables, its
four measures; the exact columns, the law and its uniform twin, from P2's expected values; Atlas's pooled column, from the
Atlas crate's raw bytes; and the report functions, which no step reads: the perfect sampler's floor, the one-site and pair
max |z|, the nearest-neighbour correlation on N-crystal shots, and the errors printed beside linear XEB and the
coherences. Each figure is compared at the places the page prints it."""
from fractions import Fraction

import pytest

import p2crates_support as S
from qro import p2_law, p2_measures, p2_report
from qro.p1_graph import Index

ROWS = {"n-crystal-share": "N-crystal share", "forbidden-share": "forbidden share of N-crystal shots",
        "tvd": "TVD to the law", "linear-xeb": "linear XEB", "nn-pair-correlation": "NN pair correlation: all / N-crystal",
        "x0x1": "`<X0X1>`", "y0y1": "`<Y0Y1>`"}
FLOOR, ONE, PAIR = ("perfect sampler's TVD floor: mean / p95", "one-site max \\|z\\|: all / N-crystal",
                    "pair max \\|z\\|: all / N-crystal")
LAW_COLUMN, TWIN_COLUMN, ATLAS_COLUMN = "law (exact)", "twin (exact)", "emulator (Atlas, 24576 shots)"


@pytest.fixture(scope="module")
def page():
    return S.side_by_side()


@pytest.fixture(scope="module")
def ibm():
    assert S.checked("ibm")[0] == 0, "the crate is accepted before its measurements are read"
    md = S.metadata("ibm")
    return S.built("ibm")[0], md, S.pubs(md), p2_measures.measurements(md)


def test_the_page_names_the_columns_and_rows_read_here(page):
    assert set(ROWS.values()) | {FLOOR, ONE, PAIR} <= set(page)
    columns = {LAW_COLUMN, TWIN_COLUMN, ATLAS_COLUMN} | {f"qpu: {d}" for d in S.DEVICES}
    assert all(columns <= set(page[r]) for r in ROWS.values())


def test_the_21_morning_cells_are_the_ibm_crates_checked_measurements(page, ibm):
    _, _, pubs, checked = ibm
    cells = 0
    for device in S.DEVICES:
        for measure, row in ROWS.items():
            pub = pubs[(f"{device}/morning", "law" if measure in p2_measures.LAW_MEASURES else measure)]
            value = checked[(pub["@id"], measure)]["value"]
            assert S.printed(float(value)) == S.figure(page[row][f"qpu: {device}"]), (device, measure)
            cells += 1
    assert cells == 21


def test_every_law_run_of_the_sheet_tables_is_the_crates_checked_measurements(ibm):
    """Each device's sheet table prints its law runs, the morning's first, by their IBM job: the five-crystal share, the
    forbidden share, linear XEB and the TVD of each are the crate's CHECKED values for that job's law PUB."""
    _, md, pubs, checked = ibm
    runs = S.runs_by_job_id(md)
    seen = []
    for device in S.DEVICES:
        for job, *printed in S.sheets(device):
            run = runs[job]
            pub = pubs[(run, "law")]
            got = [checked[(pub["@id"], m)]["value"] for m in ("n-crystal-share", "forbidden-share", "linear-xeb", "tvd")]
            assert [S.printed(float(v)) for v in got] == [S.figure(p) for p in printed], run
            seen.append(run)
    assert len(seen) == len(set(seen)) == 31 and {r.split("/")[1] for r in seen} >= {"morning", "sheet-10"}


@pytest.mark.parametrize("column, model", [(LAW_COLUMN, "law"), (TWIN_COLUMN, "uniform")])
def test_the_exact_columns_are_p2s_expected_values(page, column, model):
    law = S.law()
    expected = p2_law.expected(p2_law.model_of(model, law), law)
    for measure, row in ROWS.items():
        assert S.printed(float(expected[measure])) == S.figure(page[row][column]), (column, measure)
    assert [S.printed(float(expected["nn-pair-correlation"]))] * 2 == S.figures(page[ROWS["nn-pair-correlation"]][column])


def atlas_pooled():
    """The Atlas crate's six law PUBs' counts, pooled: the emulator's 24,576 shots."""
    crate, md = S.built("atlas")[0], S.metadata("atlas")
    pooled = {}
    for pub in Index(md).of_type("qro:Pub"):
        if pub["qro:role"] == "law":
            for Y, n in S.counts(crate, md, pub).items():
                pooled[Y] = pooled.get(Y, 0) + n
    return pooled


def test_atlas_pooled_law_measures_and_statistics_are_the_emulators_column(page):
    """The page's emulator column is the Atlas crate's six law jobs pooled. Its coherences are the engine's REPORTED
    floats, which P2 measures none of (its stated limit 10), and are not compared here."""
    law, counts = S.law(), atlas_pooled()
    assert sum(counts.values()) == 24576
    col = {r: page[r][ATLAS_COLUMN] for r in page}
    for measure in p2_measures.LAW_MEASURES:
        v = p2_measures.value(measure, counts, law)
        assert S.printed(float(v.value)) == S.figure(col[ROWS[measure]]), measure
    f5 = S.five(counts, law)
    assert S.printed(p2_report.xeb_se(f5, law)) == S.figures(col[ROWS["linear-xeb"]])[1]
    assert S.printed(float(p2_measures.value("nn-pair-correlation", f5, law).value)) == S.figures(
        col[ROWS["nn-pair-correlation"]])[1]
    A = p2_law.kernel()
    za, z5 = p2_report.z_scores(counts, A), p2_report.z_scores(f5, A)
    assert [S.printed(za["one_site"]["max_abs_z"], 2), S.printed(z5["one_site"]["max_abs_z"], 2)] == S.figures(col[ONE])
    assert [S.printed(za["pairs"]["max_abs_z"], 2), S.printed(z5["pairs"]["max_abs_z"], 2)] == S.figures(col[PAIR])


def test_the_floor_at_24576_shots_is_the_laws_and_the_emulators(page):
    floor = p2_report.floor(24576, S.law())
    want = [S.printed(floor["mean"]), S.printed(floor["upper"])]
    assert want == S.figures(page[FLOOR][LAW_COLUMN]) == S.figures(page[FLOOR][ATLAS_COLUMN]) == [0.1319, 0.135]


@pytest.mark.parametrize("device", S.DEVICES)
def test_the_report_functions_on_each_devices_morning_are_its_printed_figures(page, ibm, device):
    """On the device's morning PUBs, read from the raw bytes: the floor at its N-crystal shots (mean and the 95th
    percentile of 200 replicas), the one-site and pair max |z| over all shots and over the N-crystal shots, the
    nearest-neighbour correlation on the N-crystal shots, linear XEB's error, and each coherence's."""
    crate, md, pubs, checked = ibm
    law, col = S.law(), f"qpu: {device}"
    counts = S.counts(crate, md, pubs[(f"{device}/morning", "law")])
    f5 = S.five(counts, law)
    floor = p2_report.floor(sum(f5.values()), law)
    assert [S.printed(floor["mean"]), S.printed(floor["upper"])] == S.figures(page[FLOOR][col])
    A = p2_law.kernel()
    za, z5 = p2_report.z_scores(counts, A), p2_report.z_scores(f5, A)
    assert [S.printed(za["one_site"]["max_abs_z"], 2), S.printed(z5["one_site"]["max_abs_z"], 2)] == S.figures(page[ONE][col])
    assert [S.printed(za["pairs"]["max_abs_z"], 2), S.printed(z5["pairs"]["max_abs_z"], 2)] == S.figures(page[PAIR][col])
    nn5 = p2_measures.value("nn-pair-correlation", f5, law).value
    assert S.printed(float(nn5)) == S.figures(page[ROWS["nn-pair-correlation"]][col])[1]
    assert S.printed(p2_report.xeb_se(f5, law)) == S.figures(page[ROWS["linear-xeb"]][col])[1]
    for measure in ("x0x1", "y0y1"):
        m = checked[(pubs[(f"{device}/morning", measure)]["@id"], measure)]
        se = p2_report.coherence_se(float(m["value"]), m["in_scope"])
        assert S.printed(se) == S.figures(page[ROWS[measure]][col])[1], measure
    assert isinstance(m["value"], Fraction)
