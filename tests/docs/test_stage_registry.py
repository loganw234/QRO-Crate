"""Every test file is run by some stage of the runner, and every tool's own checks are too (ParcelRound, METHOD.md
section 2, "Make the registry self-enforcing"; HonestFramework, METHOD.md section 4, "derive, don't re-list").
The stage directories come from moth-quantum's tests/docs/test_registry.py; the tools' checks are QRO-Crate's.

Nothing here is a hand-kept list (P0's verifier, P0-3):
  - the stages are the runner's `stage` calls, read as the runner reads them, so a commented-out stage runs nothing
    and counts for nothing;
  - the tools are every runnable .py under tools/ and controls/, and every check_*.py under docs/studies/qro0/
    (the study's other .py files are its instruments, below);
  - a tool's checks are read from its own source: each of "--check" and "--control" it names, in either quote,
    and its plain run unless its source makes a mode required;
  - a negative control's stage, which the runner marks MUST_FAIL, runs no tool's check: it proves the runner can
    say no. So the twin's stage cannot be deleted with the control's line standing in for it;
  - a stage runs a tool, or a test directory, only as its program, after an optional `env NAME=VALUE ...`:
    `python [-I] TOOL ...` or `bash verify/pytest-stage.sh DIR [--ignore=DIR ...]`. A line that only names one
    (`echo python TOOL`, `python -c pass TOOL`) runs nothing of it, and counts for nothing;
  - every stage's command is a simple command (P0's verifier, round 3, R3-3a, which planted a dozen masks past
    a list of them): words of letters, digits and `_ . / = : , + -`, or a quoted `${NAME:-}`, and nothing else.
    So no `||`, `&&`, `;`, pipe, redirect, comment, subshell, substitution or continuation can mask its exit;
  - the negative control's MUST_SAY is `REFUSED` and the very refusal its plant's row expects (round 4, R4-3b), a
    pytest stage takes a directory and
    `--ignore=` and no other option, the lint names every top-level directory that holds Python, and the twin's
    stage plants the twin (round 3, note 2).
Stated limits (P0's verifier, round 4, notes 1 to 3): this reads the runner's text, not its run. So it cannot see
a stage the shell never reaches (inside `if false`, after an `exit 0`), a tool's own flag that masks its exit
(`--exit-zero`, `--help`), or the runner's own exit status. Each run prints a line for every stage it ran, and
the negative control shows on every run that the runner can still fail.
The study's five analysis instruments are run by tools/check_instruments.py, which must name exactly them. Its
three IBM tools (ibm_*.py) need the owner's key, so no stage runs them: a stated limit.
"""
import pathlib
import re

import pytest

from controls.registry import CONTROLS

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNNER = (ROOT / "verify" / "run.sh").read_text(encoding="utf-8")


def stage_lines(runner_text, negative=False):
    """The command lines of the runner's stages: each `stage` call's continuation line, as the runner reads them
    (it derives its stage list from lines starting `stage NAME "`). Only the negative controls' with `negative`,
    and only the others' without it (P0's verifier, round 2, note 1)."""
    out = []
    for m in re.finditer(r"^(MUST_FAIL=1[^\n]*\n)?stage [a-z0-9-]+ \"[^\"]*\" -- \\\n(.*)$", runner_text, re.M):
        if bool(m.group(1)) == negative:
            out.append(m.group(2))
    return out


ENV = r"(?:env(?: [A-Za-z_][A-Za-z0-9_]*=[^ ]*)+ )?"     # `env NAME=VALUE ...` runs the program after it


def staged_dirs(runner_text):
    """(directory, the directories its line takes back out with --ignore=) for each pytest stage."""
    out, path = set(), r"tests/[A-Za-z0-9_/-]+"
    for line in stage_lines(runner_text):
        for m in re.finditer(rf"^{ENV}bash verify/pytest-stage\.sh ({path})((?: --ignore={path})*)$", line.strip()):
            ignored = frozenset(map(pathlib.PurePosixPath, re.findall(rf"--ignore=({path})", m.group(2))))
            out.add((pathlib.PurePosixPath(m.group(1)), ignored))
    return out


def orphans(root, dirs):
    """pytest collects both test_*.py and *_test.py; a registry that knew only the first missed the second
    (moth-quantum's verifier-P0 8d)."""
    out = []
    files = set((root / "tests").rglob("test_*.py")) | set((root / "tests").rglob("*_test.py"))
    for f in sorted(files):
        rel = pathlib.PurePosixPath(f.relative_to(root).as_posix())
        if not any(d in rel.parents and not any(i in rel.parents for i in ignored) for d, ignored in dirs):
            out.append(str(rel))
    return out


def tools(root):
    """{token a stage line names it by: its checks}, for every tool in the tree."""
    out = {}
    for d, as_module in (("tools", False), ("controls", True)):
        for f in sorted((root / d).glob("*.py")):
            src = f.read_text(encoding="utf-8")
            if MAIN.search(src):
                token = f"-m {d}.{f.stem}" if as_module else f"{d}/{f.name}"
                out[token] = checks(src)
    for f in sorted((root / "docs" / "studies" / "qro0").glob("check_*.py")):
        out[f"docs/studies/qro0/{f.name}"] = checks(f.read_text(encoding="utf-8"))
    return out


MAIN = re.compile(r"""__name__\s*==\s*(['"])__main__\1""")


def checks(src):
    modes = {m for m in ("--check", "--control") if re.search(rf"""(['"]){m}\1""", src)}
    return modes | ({""} if "required=True" not in src else set())


def unstaged(root, runner_text):
    """Each tool check no stage runs, by name."""
    lines, out = stage_lines(runner_text), []
    for token, modes in tools(root).items():
        for mode in sorted(modes):
            hit = [line for line in lines if re.match(ENV + r"python (-I )?" + re.escape(token) + r"(\s|$)", line.strip())
                   and (mode in line.split() if mode else not ({"--check", "--control", "--write"} & set(line.split())))]
            if not hit:
                out.append(f"{token} {mode}".strip())
    return out


def instruments_named(root):
    src = (root / "tools" / "check_instruments.py").read_text(encoding="utf-8")
    return set(re.findall(r'"([a-z0-9_]+)"', re.search(r"INSTRUMENTS = \(([^)]*)\)", src).group(1)))


def test_every_test_file_is_run_by_a_stage():
    dirs = staged_dirs(RUNNER)
    assert dirs, "the runner names no pytest stage directory at all"
    assert orphans(ROOT, dirs) == []


def test_every_tool_check_is_run_by_a_stage():
    assert tools(ROOT), "no tools found"
    assert unstaged(ROOT, RUNNER) == []


WORD = re.compile(r'[A-Za-z0-9_./=:,+-]+|"\$\{[A-Za-z_][A-Za-z0-9_]*(:-)?\}"')


def not_simple(runner_text):
    """Every stage command that is not a simple command, which alone cannot mask its own exit."""
    return [line for line in stage_lines(runner_text) + stage_lines(runner_text, negative=True)
            if not all(WORD.fullmatch(w) for w in line.split())]


def test_every_stage_runs_a_simple_command():
    assert stage_lines(RUNNER, negative=True), "the runner has no negative control"
    assert not_simple(RUNNER) == []


def shape_problems(root, runner_text):
    """Round 3, note 2: four plants the registry did not see."""
    out = []
    rows = {c.name: c for c in CONTROLS}
    negatives = re.findall(r'^MUST_FAIL=.*\nstage ', runner_text, re.M)
    held = re.findall(r'^MUST_FAIL=1 MUST_SAY="([^"]*)"\nstage [a-z0-9-]+ "[^"]*" -- \\\n'
                      r"\s*python -m controls\.plant ([a-z0-9-]+)\s*$", runner_text, re.M)
    if not negatives or len(held) != len(negatives) or any(
            rows.get(plant) is None or rows[plant].expected != "refused" or say != f"REFUSED {rows[plant].refusal}"
            for say, plant in held):
        out.append("a negative control does not name, as REFUSED and a name, the refusal its plant's row expects")
    for line in stage_lines(runner_text):
        words = line.split()
        if "verify/pytest-stage.sh" in words:
            rest = words[words.index("verify/pytest-stage.sh") + 1:]
            if not rest or not rest[0].startswith("tests/") or any(not w.startswith("--ignore=tests/")
                                                                  for w in rest[1:]):
                out.append(f"a pytest stage with another option: {line.strip()}")
    lint = [line for line in stage_lines(runner_text) if "ruff check" in line]
    python_dirs = {f.relative_to(root).parts[0] for f in root.rglob("*.py")} - {"docs"}
    python_dirs = {d for d in python_dirs if not d.startswith(".")}
    if len(lint) != 1 or not python_dirs <= set(lint[0].split()):
        out.append(f"the lint does not name every directory holding Python: {sorted(python_dirs)}")
    twin = re.search(r'^stage twin "[^"]*" -- \\\n(.*)$', runner_text, re.M)
    if twin is None or twin.group(1).split()[-2:] != ["controls.plant", "twin"]:
        out.append("the twin's stage does not plant the twin")
    return out


def test_the_runners_shape_holds():
    assert shape_problems(ROOT, RUNNER) == []


def test_the_study_instruments_are_run_or_stated():
    qro0 = {f.stem for f in (ROOT / "docs" / "studies" / "qro0").glob("*.py")}
    gates = {s for s in qro0 if s.startswith("check_")}
    ibm = {s for s in qro0 if s.startswith("ibm_")}
    assert instruments_named(ROOT) == qro0 - gates - ibm


# -- negative controls: each way the registry claims to fail, watched failing -----------------------------------
def test_a_test_file_outside_every_stage_is_caught(tmp_path):
    (tmp_path / "tests" / "format").mkdir(parents=True)
    (tmp_path / "tests" / "stray").mkdir()
    (tmp_path / "tests" / "format" / "test_ok.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "stray" / "test_lost.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "stray" / "law_test.py").write_text("", encoding="utf-8")
    dirs = staged_dirs('stage format "x" -- \\\n  bash verify/pytest-stage.sh tests/format\n')
    assert orphans(tmp_path, dirs) == ["tests/stray/law_test.py", "tests/stray/test_lost.py"]


def test_a_commented_out_stage_runs_nothing_and_its_tests_are_orphans():
    planted = RUNNER.replace('stage format "', '# stage format "', 1)
    assert planted != RUNNER
    assert any(o.startswith("tests/format/") for o in orphans(ROOT, staged_dirs(planted)))


def test_a_directory_its_stage_ignores_is_an_orphan_unless_another_stage_runs_it(tmp_path):
    """moth-quantum's control, kept: the predict stage's line deleted, as its verifier-P2 planted it."""
    for d in ("compare", "compare/predict"):
        (tmp_path / "tests" / d).mkdir(parents=True)
    (tmp_path / "tests" / "compare" / "test_measures.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "compare" / "predict" / "test_predict.py").write_text("", encoding="utf-8")
    compare = 'stage compare "x" -- \\\n  bash verify/pytest-stage.sh tests/compare --ignore=tests/compare/predict\n'
    assert orphans(tmp_path, staged_dirs(compare)) == ["tests/compare/predict/test_predict.py"]
    both = compare + 'stage predict "y" -- \\\n  env X=1 bash verify/pytest-stage.sh tests/compare/predict\n'
    assert orphans(tmp_path, staged_dirs(both)) == []


def test_a_deleted_tool_stage_is_caught():
    for stage, name in (("privacy-controls", "tools/check_privacy.py --control"),
                        ("instruments", "tools/check_instruments.py"),
                        ("vocabulary", "tools/gen_vocabulary.py --check"),
                        ("study-plants", "docs/studies/qro0/check_study_plants.py")):
        planted = re.sub(rf'^stage {stage} "[^"]*" -- \\\n.*\n', "", RUNNER, flags=re.M)
        assert planted != RUNNER, stage
        assert name in unstaged(ROOT, planted), stage


def test_a_deleted_twin_stage_is_caught_though_the_control_runs_the_same_tool():
    planted = re.sub(r'^stage twin "[^"]*" -- \\\n.*\n', "", RUNNER, flags=re.M)
    assert planted != RUNNER
    assert "-m controls.plant" in unstaged(ROOT, planted)


def test_a_tool_written_with_single_quotes_is_still_read(tmp_path):
    for d in ("tools", "controls", "docs/studies/qro0"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "tools" / "quiet_gate.py").write_text("import sys\nif '--check' in sys.argv: pass\n"
                                                      "if __name__ == '__main__': pass\n", encoding="utf-8")
    assert unstaged(tmp_path, RUNNER) == ["tools/quiet_gate.py", "tools/quiet_gate.py --check"]


MASKS = ["|| true", "|| :", "; true", ";true", "||true", "|| exit 0", "|| echo ok", "|| /bin/true", "|| (true)",
         "|| { true; }", "|| test 1", "|| [ 1 ]", "|| python -c pass", "&& true", "| tee /dev/null", "|| sh -c true",
         "|| true # fine", "# || true", "> /dev/null", "2>&1", "& wait", "$(true)", "`true`", "\\"]


@pytest.mark.parametrize("mask", MASKS)
def test_a_stage_that_could_mask_its_exit_is_caught(mask):
    """Round 3 (R3-3a): each of its masks, and more of the class, planted on a real stage's line."""
    planted = RUNNER.replace("python tools/check_docs.py\n", f"python tools/check_docs.py {mask}\n", 1)
    assert planted != RUNNER
    assert not_simple(planted) == [f"  python tools/check_docs.py {mask}"]


@pytest.mark.parametrize("line", ["echo python tools/check_docs.py", "python -c pass tools/check_docs.py",
                                  "python -m pytest tools/check_docs.py", "true tools/check_docs.py"])
def test_a_stage_that_names_a_tool_without_running_it_runs_nothing(line):
    planted = RUNNER.replace("  python tools/check_docs.py\n", f"  {line}\n", 1)
    assert planted != RUNNER and not_simple(planted) == []
    assert "tools/check_docs.py" in unstaged(ROOT, planted)


def test_a_test_directory_named_but_not_run_is_an_orphan():
    planted = RUNNER.replace("  bash verify/pytest-stage.sh tests/custody\n",
                             "  echo bash verify/pytest-stage.sh tests/custody\n", 1)
    assert planted != RUNNER
    assert any(o.startswith("tests/custody/") for o in orphans(ROOT, staged_dirs(planted)))


def test_a_mask_on_a_continuation_line_is_caught():
    planted = RUNNER.replace("python tools/check_docs.py\n", "python tools/check_docs.py \\\n  || true\n", 1)
    assert planted != RUNNER
    assert not_simple(planted) == ["  python tools/check_docs.py \\"]


def test_a_second_negative_control_is_held_too():
    """Round 5, note 8: the check read the first negative control alone."""
    second = ('MUST_FAIL=1 MUST_SAY=""\nstage control2 "a second control" -- \\\n'
              "  python -m controls.plant shot-moved\n\n")
    planted = RUNNER.replace("stage study ", second + "stage study ", 1)
    assert planted != RUNNER
    got = shape_problems(ROOT, planted)
    assert len(got) == 1 and "plant's row expects" in got[0], got


@pytest.mark.parametrize("plant, problem", [
    (('MUST_FAIL=1 MUST_SAY="REFUSED raw-digest"', 'MUST_FAIL=1 MUST_SAY=""'), "plant's row expects"),
    (('MUST_FAIL=1 MUST_SAY="REFUSED raw-digest"', 'MUST_FAIL=1 MUST_SAY="R"'), "plant's row expects"),
    (('MUST_FAIL=1 MUST_SAY="REFUSED raw-digest"', 'MUST_FAIL=1 MUST_SAY="REFUSED"'), "plant's row expects"),
    (('MUST_FAIL=1 MUST_SAY="REFUSED raw-digest"', 'MUST_FAIL=1 MUST_SAY="REFUSED file-digest"'),
     "plant's row expects"),
    (("bash verify/pytest-stage.sh tests/format\n", "bash verify/pytest-stage.sh tests/format -k spelling\n"),
     "another option"),
    (("bash verify/pytest-stage.sh tests/custody\n", "bash verify/pytest-stage.sh tests/custody --deselect x\n"),
     "another option"),
    (("ruff check qro controls tools tests", "ruff check qro"), "every directory holding Python"),
    (("python -m controls.plant twin", "python -m controls.plant shot-moved"), "does not plant the twin")],
    ids=["MUST_SAY emptied", "MUST_SAY a letter", "MUST_SAY no name", "MUST_SAY another name", "-k added", "--deselect added", "the lint cut to the package", "the twin made the control"])
def test_each_shape_plant_is_caught(plant, problem):
    planted = RUNNER.replace(*plant, 1)
    assert planted != RUNNER
    got = shape_problems(ROOT, planted)
    assert len(got) == 1 and problem in got[0], got


def test_a_new_tool_with_a_check_and_no_stage_is_caught(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "controls").mkdir()
    (tmp_path / "docs" / "studies" / "qro0").mkdir(parents=True)
    (tmp_path / "tools" / "new_gate.py").write_text('import sys\nif "--check" in sys.argv: pass\n'
                                                    'if __name__ == "__main__": pass\n', encoding="utf-8")
    assert unstaged(tmp_path, RUNNER) == ["tools/new_gate.py", "tools/new_gate.py --check"]


def clashes(root):
    """Test files that share a basename: pytest imports each under its bare basename, so two of one name stop a
    single session over tests/ at collection while each stage alone passes (moth-quantum, P1, 2026-09-26)."""
    seen = {}
    files = set((root / "tests").rglob("test_*.py")) | set((root / "tests").rglob("*_test.py"))
    for f in sorted(files):
        seen.setdefault(f.name, []).append(f.relative_to(root).as_posix())
    return {name: paths for name, paths in seen.items() if len(paths) > 1}


def test_no_two_test_files_share_a_basename():
    assert clashes(ROOT) == {}


def test_a_shared_basename_is_caught(tmp_path):
    """moth-quantum's control, kept."""
    for d in ("a", "b"):
        (tmp_path / "tests" / d).mkdir(parents=True)
        (tmp_path / "tests" / d / "test_same.py").write_text("", encoding="utf-8")
    assert clashes(tmp_path) == {"test_same.py": ["tests/a/test_same.py", "tests/b/test_same.py"]}
