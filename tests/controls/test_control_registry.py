"""The controls' registry, walked both ways (ParcelRound, METHOD.md section 2; study QRO-0, section 11):
  - a row of P0's that no plant exercises fails, naming the row;
  - a plant naming no row fails, naming the plant;
  - each built control comes out as its row says, by the refusal's own name;
and the check is shown able to fail. Each row is held to the study's own section 11 table, cell for cell, and
each owner to section 13 where it names one (P0's verifier's notes)."""
import re
from pathlib import Path

import pytest

from controls import registry as R
from controls.run import outcome


def unexercised(controls, plants):
    return sorted(c.name for c in controls if c.owner == "P0" and c.name not in plants)


def orphaned(controls, plants):
    names = {c.name for c in controls}
    return sorted(p for p in plants if p not in names)


def test_every_p0_row_is_exercised_and_every_plant_names_a_row():
    assert unexercised(R.CONTROLS, R.plants()) == []
    assert orphaned(R.CONTROLS, R.plants()) == []


def test_the_registry_check_can_fail():
    """A dummy row and a dummy plant, each caught by name, then gone."""
    dummy = R.Control("dummy-row", "nothing", "refused", "spelling", "P0", "`spelling`")
    assert unexercised(R.CONTROLS + (dummy,), R.plants()) == ["dummy-row"]
    assert orphaned(R.CONTROLS, dict(R.plants(), **{"dummy-plant": None})) == ["dummy-plant"]


@pytest.mark.parametrize("name", sorted(R.plants()))
def test_each_built_control_comes_out_as_section_11_says(name):
    c = R.CONTROL[name]
    got, refusal, where = outcome(name)
    assert (got, refusal) == (c.expected, c.refusal), f"{got} {refusal} at {where}; section 11 says {c.text}"


STUDY = Path(__file__).resolve().parents[2] / "docs" / "studies" / "QRO-0.md"


def section(text, n):
    return re.search(rf"^## {n}\. .*?(?=^## \d+\. |\Z)", text, re.S | re.M).group(0)


def study_table():
    """Section 11's table, row by row: (control, planted fault, expected), each cell as the study writes it."""
    rows, inside = [], False
    for line in section(STUDY.read_text(encoding="utf-8"), 11).splitlines():
        if line.startswith("| control | planted fault | expected |"):
            inside = True
            continue
        if inside and line.startswith("|---"):
            continue
        if inside and line.startswith("|"):
            rows.append(tuple(c.strip() for c in re.split(r"(?<!\\)\|", line)[1:-1]))
        elif inside:
            break
    return rows


def test_the_registry_is_section_11s_table_cell_for_cell():
    table = study_table()
    assert len(table) == 30
    mine = [(c.name, c.fault, c.text) for c in R.CONTROLS]
    assert mine == [(a, b.replace("\\|", "|"), c.replace("\\|", "|")) for a, b, c in table]


def test_the_owners_are_section_13s_where_it_names_them():
    """Section 13 names some controls with their parcel; every one it names agrees with the registry."""
    s13 = section(STUDY.read_text(encoding="utf-8"), 13)
    parcels = s13.split("**The parcels.**", 1)[1].split("**Who owns each checker step**", 1)[0]
    named = 0
    for block in re.split(r"^- \*\*(?=P\d)", parcels, flags=re.M)[1:]:
        owner = block[:2]
        for name in re.findall(r"`([a-z]+(?:-[a-z]+)+)`", block):
            if name in R.CONTROL:
                named += 1
                assert R.CONTROL[name].owner == owner, f"{name}: section 13 gives it to {owner}"
    assert named >= 10, "section 13 names controls under P1, P2, P3 and P5"


def test_every_row_names_an_owner_and_a_consistent_outcome():
    for c in R.CONTROLS:
        assert c.owner in ("P0", "P1", "P2", "P3", "P4", "P5") and c.text and c.fault, c.name
        assert (c.expected == "refused") or c.refusal is None, c.name


def test_the_study_comparison_can_fail():
    """One cell changed in the registry's copy is caught."""
    table = study_table()
    changed = [(c.name, c.fault + " ", c.text) for c in R.CONTROLS]
    assert changed != [(a, b, c) for a, b, c in table]


def test_the_controls_run_says_wrong_and_fails_when_a_plant_comes_out_otherwise(capsys):
    """Round 6, 8.1 item 17: the run's loop was held by no test."""
    from controls import run
    assert run.main(dict(R.plants(), **{"shot-moved": R.twin})) == 1
    line = next(x for x in capsys.readouterr().out.splitlines() if "shot-moved" in x)
    assert line == "WRONG     shot-moved             accepted; section 11 says `raw-digest`", line


def test_the_controls_run_fails_on_a_p0_row_with_no_plant(capsys):
    """P0.1's verifier, round 1, 4.2: a P0 row left unplanted was printed, and no test held the run's exit."""
    from controls import run
    every = R.plants()
    del every["count-unpaid"]
    assert run.main(every) == 1
    assert re.search(r"^WRONG +count-unpaid +P0's control, with no plant$", capsys.readouterr().out, re.M)


@pytest.mark.parametrize("name, code", [("custody-chain", 1), ("audit-head-mismatch", 1), ("withdrawal-appended", 0)])
def test_the_plant_command_runs_a_custody_control_through_the_command_line(name, code):
    """Round 6, 8.1 item 17: its custody branch was run by no stage."""
    from controls.plant import main
    assert main([name]) == code


@pytest.mark.parametrize("argv", [[], ["twin", "extra"], ["no-such-control"], [""]],
                         ids=["no argument", "two", "no such control", "an empty name"])
def test_the_plant_command_refuses_its_misuse_with_its_usage(argv, capsys):
    """P0.1's verifier, round 2, 4.1.4: the usage branch was held by no test."""
    from controls.plant import main
    assert main(argv) == 2
    assert capsys.readouterr().err == "usage: python -m controls.plant twin|" + "|".join(sorted(R.plants())) + chr(10)


def test_the_controls_run_as_a_process_says_each_control_and_each_pending_row():
    """Round 3, note 11: its lines, its labels and its __main__ were unasserted. Each line is derived from the
    registry, so a parcel's plant changes what is expected, not this test."""
    import subprocess
    import sys
    r = subprocess.run([sys.executable, "-m", "controls.run"], cwd=Path(__file__).resolve().parents[2],
                       capture_output=True, text=True)
    from qro.__main__ import escape
    assert r.returncode == 0, r.stdout[-800:]
    lines = r.stdout.splitlines()
    every = R.plants()
    for c in R.CONTROLS:
        if c.name in every:
            label = escape(f"ok        {c.name:22} {c.expected}" + (f" {c.refusal} at " if c.refusal else ""))
            assert any(line.startswith(label) for line in lines), (c.name, label)
        else:
            assert escape(f"pending   {c.name:22} {c.owner}: {c.text}") in lines, c.name


def test_the_controls_run_writes_each_line_as_printable_ascii(monkeypatch, capsys):
    """P0.1's verifier, round 4, N3: a refusal's detail holding a line feed made two lines, and a character the
    console could not encode broke the run. An outcome whose detail holds both is written as the command line
    writes its own."""
    from controls import run
    real = run.outcome
    hostile = "data/raw.counts.json: two" + chr(10) + "lines and " + chr(0x2265)
    monkeypatch.setattr(run, "outcome", lambda name, every=None: ("refused", "raw-digest", hostile)
                        if name == "shot-moved" else real(name, every))
    assert run.main() == 0
    out = capsys.readouterr().out
    line = next(x for x in out.splitlines() if "shot-moved" in x)
    assert line.endswith("two" + chr(92) + "nlines and " + chr(92) + "u2265") and out.isascii()


def test_the_controls_run_as_a_process_fails_when_a_parcels_module_exits_0_at_import(tmp_path):
    """Round 3, note 1, as the runner runs it: a copy of the packages holding a parcel's module that raises
    SystemExit(0) as it is imported. The run ended with exit 0 and no output; it is its own failure, exit 3."""
    import os
    import shutil
    import subprocess
    import sys
    for pkg in ("qro", "controls"):
        shutil.copytree(ROOT / pkg, tmp_path / pkg, ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / "qro" / "register_p1.py").write_text("import sys" + chr(10) + "sys.exit(0)" + chr(10),
                                                     encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    r = subprocess.run([sys.executable, "-m", "controls.run"], cwd=tmp_path, capture_output=True, text=True, env=env)
    assert r.returncode == 3 and r.stdout.startswith("FAILED: the controls' run itself failed, SystemExit"), \
        (r.returncode, r.stdout[-400:], r.stderr[-400:])


def test_each_command_answers_a_plants_module_that_exits_0_as_its_own_failure(tmp_path):
    """P0.1's verifier, round 4, N4: a plants module raising SystemExit(0) as it loaded ended the plant command and
    the generator with exit 0, unrun, so the twin's and the vocabulary's stages passed. In a copy of the packages,
    as the runner runs each: exit 3 and one line, held whole since round 2. The generator's --help still exits 0."""
    import os
    import shutil
    import subprocess
    import sys
    for pkg in ("qro", "controls", "tools"):
        shutil.copytree(ROOT / pkg, tmp_path / pkg, ignore=shutil.ignore_patterns("__pycache__"))
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}

    def run(*cmd):
        return subprocess.run([sys.executable, *cmd], cwd=tmp_path, capture_output=True, text=True, env=env)
    assert run("tools/gen_vocabulary.py", "--help").returncode == 0
    (tmp_path / "controls" / "plants_zz.py").write_text("import sys" + chr(10) + "sys.exit(0)" + chr(10),
                                                        encoding="utf-8")
    for cmd, says in ((["-m", "controls.plant", "twin"], "FAILED: the plant command itself failed, SystemExit"),
                      (["-m", "controls.plant", "shot-moved"], "FAILED: the plant command itself failed, SystemExit"),
                      (["tools/gen_vocabulary.py", "--check"], "FAILED: the generator itself failed, SystemExit")):
        r = run(*cmd)
        assert r.returncode == 3 and r.stderr.startswith(says) and (r.stdout + r.stderr).count(chr(10)) == 1, (
            cmd, r.returncode, r.stdout[-300:], r.stderr[-300:])
    r = run("-m", "controls.run")
    assert r.returncode == 3 and r.stdout.startswith("FAILED: the controls' run itself failed, SystemExit") and (
        r.stdout + r.stderr).count(chr(10)) == 1, r.stdout


def test_each_command_answers_any_other_failure_of_a_plants_module_in_one_escaped_line(tmp_path):
    """P0.2's verifier, round 1, D1: the generator took a plants module's RuntimeError for a contradiction, exit 2,
    and wrote a failure holding a line feed as two lines, the second free to begin REFUSED. Each command answers
    it as its own failure: exit 3 and exactly one line, escaped, on one stream; and --write writes nothing."""
    import os
    import shutil
    import subprocess
    import sys
    for pkg in ("qro", "controls", "tools"):
        shutil.copytree(ROOT / pkg, tmp_path / pkg, ignore=shutil.ignore_patterns("__pycache__"))
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    (tmp_path / "controls" / "plants_zz.py").write_text(
        "raise RuntimeError('fixture file missing' + chr(10) + 'REFUSED forged at x: y')" + chr(10), encoding="utf-8")
    said = "RuntimeError: fixture file missing" + chr(92) + "nREFUSED forged at x: y; "
    plant, gen = "FAILED: the plant command itself failed, ", "FAILED: the generator itself failed, "
    for cmd, says in ((["-m", "controls.plant", "twin"], plant + said + "this is not a verdict"),
                      (["-m", "controls.plant", "shot-moved"], plant + said + "this is not a verdict"),
                      (["tools/gen_vocabulary.py", "--check"], gen + said + "this is not a verdict"),
                      (["tools/gen_vocabulary.py", "--write"],
                       gen + said + "it had finished writing no file"),
                      (["-m", "controls.run"],
                       "FAILED: the controls' run itself failed, " + said + "this is not a verdict on the controls")):
        r = subprocess.run([sys.executable, *cmd], cwd=tmp_path, capture_output=True, text=True, env=env)
        assert (r.returncode, r.stdout + r.stderr) == (3, says + chr(10)), (cmd, r.returncode, r.stdout, r.stderr)
    assert not (tmp_path / "docs").exists() and not (tmp_path / "profile").exists()


def test_the_controls_run_counts_what_it_ran(capsys):
    """P0.1's verifier, round 2, 4.1.4: the run's last line was unasserted."""
    from controls import run
    assert run.main() == 0
    built = sum(c.name in R.plants() for c in R.CONTROLS)
    last = capsys.readouterr().out.rstrip().splitlines()[-1]
    assert last == (f"{built} of {built} built controls came out as section 11 says; "
                    f"{len(R.CONTROLS) - built} pending other parcels")


def test_a_parcels_plants_join_p0s_and_a_name_planted_twice_is_refused():
    """P0.1: parcels building at once add plants in their own modules, never in this registry's file. The stand-in
    names are no control's, so no parcel's real plant meets them (P0.1's verifier, round 1, D3)."""
    from types import SimpleNamespace
    mine = SimpleNamespace(__name__="controls.plants_zz", PLANTS={"zz-not-a-control": R.twin})
    merged = R.merged(R.PLANTS, [mine])
    assert merged["zz-not-a-control"] is R.twin and set(R.PLANTS) < set(merged)
    clash = SimpleNamespace(__name__="controls.plants_zz2", PLANTS={"shot-moved": R.twin})
    with pytest.raises(R.PlantClash, match="already plants"):
        R.merged(R.PLANTS, [clash])


ROOT = Path(__file__).resolve().parents[2]


def test_a_parcels_plants_module_is_found_and_imports_either_way(tmp_path):
    """P0.1's verifier, round 1, D2, end to end: a plants module written as a parcel writes one, importing the
    registry for twin(), in a copy of the packages. Imported before the registry or after it, it loads, and
    plants() finds it beside P0's; a second module planting its name is refused."""
    import os
    import shutil
    import subprocess
    import sys
    nl = chr(10)
    for pkg in ("qro", "controls"):
        shutil.copytree(ROOT / pkg, tmp_path / pkg, ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / "controls" / "plants_zz.py").write_text(nl.join([
        "from controls.registry import RAW, twin", "", "", "def zz_plant(d):", "    return twin(d) / RAW", "", "",
        'PLANTS = {"zz-plant": zz_plant}', ""]), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}

    def run(code):
        return subprocess.run([sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True, env=env)
    for code in ("import controls.plants_zz",
                 "from controls.plants_zz import zz_plant",
                 "from controls import plants_zz, registry; assert registry.plants()['zz-plant'] is plants_zz.zz_plant",
                 "from controls import registry; p = registry.plants(); assert 'zz-plant' in p and 'shot-moved' in p"):
        r = run(code)
        assert r.returncode == 0, (code, r.stderr[-800:])
    (tmp_path / "controls" / "plants_zz2.py").write_text(nl.join([
        "from controls.registry import twin", 'PLANTS = {"zz-plant": twin}', ""]), encoding="utf-8")
    r = run("from controls import registry; registry.plants()")
    assert r.returncode == 1 and "controls.plants_zz2 plants ['zz-plant'], which another module already plants" in \
        r.stderr, r.stderr[-800:]
