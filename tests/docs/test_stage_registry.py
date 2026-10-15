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
  - every stage is written in two lines, its `stage` line and then its command (P0.1's verifier, round 3, note
    6: one written on one line was read by nothing here), and that command is a simple command (P0's verifier,
    round 3, R3-3a, which planted a dozen masks past a list of them): words of letters, digits and
    `_ . / = : , + -`, or a quoted `${NAME:-}`, and nothing else. So no `||`, `&&`, `;`, pipe, redirect,
    comment, subshell, substitution or continuation can mask its exit;
  - every test file below a staged directory is run, but where pytest never looks, below __pycache__ or a
    virtual environment, which is reported (unreached; P0.1's verifier, round 3, G1);
  - the negative control's MUST_SAY is `REFUSED` and the very refusal its plant's row expects (round 4, R4-3b), a
    pytest stage takes a directory and
    `--ignore=` and no other option, the lint names every top-level directory that holds Python, and the twin's
    stage plants the twin (round 3, note 2).
No two stages share a name (round 6, 8.1 item 5). pytest's own configuration is pinned as
pytest_configuration_problems says (round 6, 8.1 item 4; P0.1's verifier, rounds 1 to 3, D1, R2-1 and G1): a
stage reads the root's pyproject.toml alone, with exactly the options the stages assume, norecursedirs empty
among them, and no conftest.py; none of either sits at the root or under tests/; and the stage script's command
lines are the pinned ones (round 3, note 7), its refusal of a `pytest_plugins` line among them (round 3, G3). A
parcel's test files carry its prefix, so two parcels' never share a name (round 1, D3). Each `need_file` guards
the next stage the runner calls, which runs the directory it guards, and the quick budget is every stage but the
three CLAUDE.md names (round 2, note 4.1.2; round 3, note 5).
Stated limits (P0's verifier, round 4, notes 1 to 3): this reads the runner's text, not its run. So it cannot see
a stage the shell never reaches (inside `if false`, after an `exit 0`), a tool's own flag that masks its exit
(`--exit-zero`, `--help`), or the runner's own exit status. Each run prints a line for every stage it ran, and
the negative control shows on every run that the runner can still fail. And a test module is code pytest runs:
one written to reach into pytest's own state, past the stage script's refusal of `pytest_plugins`, can take
tests out of its stage, and no pin here can stop it (P0.1's verifier, round 3, G3).
The study's five analysis instruments are run by tools/check_instruments.py, which must name exactly them. Its
three IBM tools (ibm_*.py) need the owner's key, so no stage runs them: a stated limit.
"""
import os
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


def unreached(root, f):
    """Whether pytest 9.1.1 collects nothing at f, whatever its options: below a directory named __pycache__, or one
    that holds a virtual environment's pyvenv.cfg or conda-meta/history (_pytest/main.py, pytest_ignore_collect
    and _in_venv, READ). Every other directory it recurses into, since pyproject.toml empties norecursedirs (P0.1's
    verifier, round 3, G1: build/, dist/, venv/ and their like were skipped, and counted as run)."""
    for d in [p for p in f.parents if root / "tests" in p.parents]:
        if d.name == "__pycache__" or (d / "pyvenv.cfg").is_file() or (d / "conda-meta" / "history").is_file():
            return True
    return False


def orphans(root, dirs):
    """pytest collects both test_*.py and *_test.py; a registry that knew only the first missed the second
    (moth-quantum's verifier-P0 8d). A file below a directory pytest never enters is run by no stage."""
    out = []
    files = set((root / "tests").rglob("test_*.py")) | set((root / "tests").rglob("*_test.py"))
    for f in sorted(files):
        rel = pathlib.PurePosixPath(f.relative_to(root).as_posix())
        if unreached(root, f) or not any(d in rel.parents and not any(i in rel.parents for i in ignored)
                                         for d, ignored in dirs):
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


def stage_names(runner_text):
    return re.findall(r'^stage ([a-z0-9-]+) "', runner_text, re.M)


def test_no_two_stages_share_a_name():
    """The name keys a stage's .ok marker: a second stage of one name passed on the first's (round 6, 8.1 item 5)."""
    names = stage_names(RUNNER)
    assert len(names) == len(set(names)), sorted(n for n in names if names.count(n) > 1)


def test_a_second_stage_of_one_name_is_caught():
    planted = RUNNER.replace("stage study ", 'stage docs "again" -- ' + chr(92) + chr(10) + "  false" + chr(10)
                             + chr(10) + "stage study ", 1)
    names = stage_names(planted)
    assert planted != RUNNER and len(names) != len(set(names))


NEED_FILE = 'need_file () { [ -e "$1" ] || STAGE_SKIP_REASON="$2"; }'


def guard_problems(runner_text):
    """Each `need_file` guards the next stage the runner calls, as the runner reads it, whatever lines come between;
    that stage, a pytest stage, runs the directory it guards; and `need_file` skips only while its path is missing
    (P0.1's verifier, round 2, note 4.1.2: p1's guard naming tests/p2, or written with -f, skipped p1 by name after
    tests/p1 was built, and the run passed; round 3, note 5: a comment between a guard and its stage hid both)."""
    out = [] if NEED_FILE in runner_text.splitlines() else ["need_file is not " + NEED_FILE]
    for m in re.finditer(r'^need_file ([\w./-]+) "', runner_text, re.M):          # a call: a path and its reason
        nxt = re.compile(r'^stage ([a-z0-9-]+) "[^"]*" -- \\\n(.*)$', re.M).search(runner_text, m.end())
        if nxt is None:
            out.append(f"need_file {m.group(1)} guards no stage")
            continue
        name, words = nxt.group(1), nxt.group(2).split()
        ran = words[words.index("verify/pytest-stage.sh") + 1] if "verify/pytest-stage.sh" in words else None
        if ran != m.group(1):
            out.append(f"stage {name} runs {ran}, and guards {m.group(1)}")
    return out


def one_line_stages(runner_text):
    """Stages not written in the two-line form every reading here takes, `stage NAME "..." -- \\` and then the
    command: one on one line was read by no function here, so a masked exit passed (round 3, note 6)."""
    return [line for line in runner_text.splitlines() if line.startswith("stage ") and not line.endswith(" -- \\")]


def test_every_stage_is_written_in_the_two_line_form():
    assert one_line_stages(RUNNER) == []
    planted = RUNNER.replace("stage study ", "stage zzmask \"a masked stage\" -- bash -c 'false || true'" + chr(10)
                             + chr(10) + "stage study ", 1)
    assert planted != RUNNER and one_line_stages(planted) == ["stage zzmask \"a masked stage\" -- bash -c 'false || "
                                                              "true'"]


def test_each_parcel_stage_guards_the_directory_it_runs():
    assert guard_problems(RUNNER) == []
    assert len(re.findall(r"^need_file tests/p[0-9]+ ", RUNNER, re.M)) == 3, "P1's, P2's and P4's stages"


@pytest.mark.parametrize("old, new", [('need_file tests/p1 "', 'need_file tests/p2 "'),
                                      ("tests/p1" + chr(10) + chr(10) + "need_file tests/p2",
                                       "tests/p2" + chr(10) + chr(10) + "need_file tests/p2"),
                                      ('[ -e "$1" ]', '[ -f "$1" ]'),
                                      ('need_file tests/p1 "P1, the adapter, is not built yet: there is no tests/p1"'
                                       + chr(10) + "stage p1 ",
                                       'need_file tests/p2 "another\'s"' + chr(10) + "# a comment between" + chr(10)
                                       + chr(10) + "stage p1 ")],
                         ids=["the guard another's", "the stage another's", "files only", "a comment between"])
def test_a_guard_that_is_not_its_stages_is_caught(old, new):
    planted = RUNNER.replace(old, new, 1)
    assert planted != RUNNER and len(guard_problems(planted)) == 1, guard_problems(planted)


def quick_problems(runner_text):
    """CLAUDE.md: the quick budget is "all but study-plants, privacy-controls and instruments" (round 2, note
    4.1.2: a parcel's stage dropped from it, or a stage renamed, was held by no test)."""
    quick = set(re.search(r"^BUDGET_QUICK=([a-z0-9,-]+)$", runner_text, re.M).group(1).split(","))
    want = set(stage_names(runner_text)) - {"study-plants", "privacy-controls", "instruments"}
    return sorted(quick ^ want)


def test_the_quick_budget_is_every_stage_but_three():
    assert quick_problems(RUNNER) == []


def test_a_stage_dropped_from_the_quick_budget_or_renamed_is_caught():
    assert quick_problems(RUNNER.replace(",p2,", ",", 1)) == ["p2"]
    assert quick_problems(RUNNER.replace("stage p4 ", "stage p44 ", 1)) == ["p4", "p44"]


PYTEST_OPTIONS = {"pythonpath": ["."], "testpaths": ["tests"], "addopts": "-p no:cacheprovider", "norecursedirs": []}
# pytest 9.1.1's own configuration file names, in the order it looks for them (_pytest/config/findpaths.py,
# locate_config, READ): the names refused below, and the plants.
PYTEST_FILES = ("pytest.toml", ".pytest.toml", "pytest.ini", ".pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg")
# The stage script's lines that make its verdict: pytest's own line, the two that take the environment's
# configuration away, and the summary's three checks (P0.1's verifier, rounds 1 and 2: D1, R2-1 and note 4.1.1).
STAGE_PYTEST = 'out=$(python -m pytest -c pyproject.toml --noconftest --color=no -q -rs "$@" 2>&1)'
STAGE_ENV = ("export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1", "unset PYTEST_ADDOPTS PYTEST_PLUGINS")
STAGE_GREPS = ["'^[1-9][0-9]* passed'", "'failed|error'", "'skipped|xpassed|deselected'"]


def pytest_configuration_problems(root):
    """pytest's own configuration, held to what the stages assume (round 6, 8.1 item 4; P0.1's verifier, round 1,
    D1, where a pytest.ini under tests/ took 327 tests out of their stage, which still passed; round 2, R2-1, where
    a conftest.py under tests/ took this test out with 409 others):
      - verify/pytest-stage.sh runs pytest as STAGE_PYTEST, with `-c pyproject.toml` and `--noconftest`: so a
        stage reads the root's pyproject.toml, no other configuration file wherever it sits, and no conftest.py;
      - it takes the environment's plugins and options away (STAGE_ENV), and holds the summary line to its three
        checks (STAGE_GREPS);
      - pyproject.toml's options are exactly the ones the stages assume;
      - no conftest.py, and no other pytest configuration file, sits at the root or under tests/. No stage reads
        one, though whoever put it there expected it read. One elsewhere, in a virtual environment say, is not
        reported."""
    import tomllib
    out = []
    stage = (root / "verify" / "pytest-stage.sh").read_text(encoding="utf-8")
    lines = [line.strip() for line in stage.splitlines() if not line.lstrip().startswith("#")]
    if [line for line in lines if "-m pytest" in line] != [STAGE_PYTEST]:
        out.append("verify/pytest-stage.sh does not run pytest as " + STAGE_PYTEST)
    out += [f"verify/pytest-stage.sh does not say {e}" for e in STAGE_ENV if e not in lines]
    if re.findall(r"grep -Eq ('[^']*')", stage) != STAGE_GREPS:
        out.append("verify/pytest-stage.sh does not hold the summary line to " + ", ".join(STAGE_GREPS))
    options = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["pytest"]["ini_options"]
    if options != PYTEST_OPTIONS:
        out.append(f"pytest's options are not the ones the stages assume: {options}")
    tests = root / "tests"
    for p in [root / "conftest.py"] + sorted(tests.rglob("conftest.py")):
        if p.is_file():
            out.append(f"a conftest.py no stage reads: {p.relative_to(root).as_posix()}")
    for name in PYTEST_FILES:
        for p in [root / name] + sorted(tests.rglob(name)):
            if p.is_file() and p != root / "pyproject.toml":
                out.append(f"a pytest configuration file no stage reads: {p.relative_to(root).as_posix()}")
    return out


def test_pytests_own_configuration_is_what_the_stages_assume():
    assert pytest_configuration_problems(ROOT) == []


# The SHA-256 of verify/pytest-stage.sh's command lines, comments and blank lines left out: any line added to the
# script, or changed, fails here until this is changed with it, on purpose (P0.1's verifier, round 3, note 7: an
# `export PYTEST_ADDOPTS=...` added after the unset passed every named pin).
STAGE_COMMANDS_SHA256 = "4b8df591bfad394a8a35a15acde5da9f35792a5f2b222b553e889e323f47d261"


def stage_commands(stage_text):
    return [line.strip() for line in stage_text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def stage_script_changed(root):
    import hashlib
    lines = stage_commands((root / "verify" / "pytest-stage.sh").read_text(encoding="utf-8"))
    digest = hashlib.sha256(chr(10).join(lines).encode("utf-8")).hexdigest()
    return [] if digest == STAGE_COMMANDS_SHA256 else [f"verify/pytest-stage.sh's command lines are not the pinned "
                                                       f"ones ({digest[:12]}): {lines}"]


def test_the_stage_scripts_command_lines_are_the_pinned_ones():
    assert stage_script_changed(ROOT) == []


@pytest.mark.parametrize("old, new", [("unset PYTEST_ADDOPTS PYTEST_PLUGINS",
                                       "unset PYTEST_ADDOPTS PYTEST_PLUGINS" + chr(10) + "export PYTEST_ADDOPTS=-x"),
                                      ("set -uo pipefail", "set -o pipefail")],
                         ids=["a line added", "a line changed"])
def test_a_line_added_to_the_stage_script_or_changed_is_caught(tmp_path, old, new):
    root = configured_tree(tmp_path)
    text = (root / "verify" / "pytest-stage.sh").read_text(encoding="utf-8")
    assert text.count(old) == 1
    (root / "verify" / "pytest-stage.sh").write_text(text.replace(old, new), encoding="utf-8")
    assert len(stage_script_changed(root)) == 1
    unchanged = text.replace("# Run pytest on the given paths", "# Run pytest, a comment changed,", 1)
    (root / "verify" / "pytest-stage.sh").write_text(unchanged, encoding="utf-8")
    assert unchanged != text and stage_script_changed(root) == []


def configured_tree(tmp_path):
    """The root's pyproject.toml and stage script, and an empty tests/."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "verify").mkdir()
    for rel in ("pyproject.toml", "verify/pytest-stage.sh"):
        (tmp_path / rel).write_bytes((ROOT / rel).read_bytes())
    return tmp_path


CONFIG_PLANTS = ([("conftest.py", "conftest"), ("tests/conftest.py", "conftest"),
                  ("tests/p1/deep/conftest.py", "conftest")]
                 + [(n, "configuration file") for n in PYTEST_FILES if n != "pyproject.toml"]
                 + [(f"tests/p1/{n}", "configuration file") for n in PYTEST_FILES])


@pytest.mark.parametrize("rel, problem", CONFIG_PLANTS, ids=[r for r, _ in CONFIG_PLANTS])
def test_each_pytest_configuration_plant_is_caught(tmp_path, rel, problem):
    root = configured_tree(tmp_path)
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text("[pytest]" + chr(10), encoding="utf-8")
    got = pytest_configuration_problems(root)
    assert len(got) == 1 and problem in got[0] and rel in got[0], got


PIN_PLANTS = [
    ("an option", "pyproject.toml", 'addopts = "-p no:cacheprovider"', 'addopts = "-p no:cacheprovider -x"'),
    ("the stage's -c", "verify/pytest-stage.sh", "-c pyproject.toml ", ""),
    ("the stage's --noconftest", "verify/pytest-stage.sh", "--noconftest ", ""),
    ("the plugins let in", "verify/pytest-stage.sh", "export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1", "true"),
    ("the environment's options let in", "verify/pytest-stage.sh", "unset PYTEST_ADDOPTS PYTEST_PLUGINS", "true"),
    ("a skip let through", "verify/pytest-stage.sh", "'skipped|xpassed|deselected'", "'xpassed|deselected'"),
    ("a failure let through", "verify/pytest-stage.sh", "'failed|error'", "'error'")]


@pytest.mark.parametrize("plant, rel, old, new", PIN_PLANTS, ids=[p for p, *_ in PIN_PLANTS])
def test_an_option_and_each_of_the_stages_pins_is_caught(tmp_path, plant, rel, old, new):
    root = configured_tree(tmp_path)
    text = (root / rel).read_text(encoding="utf-8")
    assert text.count(old) == 1
    (root / rel).write_text(text.replace(old, new), encoding="utf-8")
    assert len(pytest_configuration_problems(root)) == 1


def test_a_conftest_no_stage_reads_is_not_reported(tmp_path):
    """The verifier's second face: a virtual environment in the tree holds third-party conftest.py files."""
    root = configured_tree(tmp_path)
    for rel in (".venv/Lib/site-packages/somepkg/conftest.py", "qro/conftest.py"):
        (root / rel).parent.mkdir(parents=True)
        (root / rel).write_text("" + chr(10), encoding="utf-8")
    assert pytest_configuration_problems(root) == []


def runner_bash():
    """As tests/format/test_cli.py's runner_bash: on Windows, Git's own bash, beside git.exe, since a bare `bash` can
    be WSL's (P0's verifier, round 5, note 2). Copied, not imported: a `tests` package in site-packages shadows any
    helper module under tests/ (Miniconda's does, on the owner's desktop, 2026-10-15)."""
    import shutil
    if os.name == "nt":
        git = shutil.which("git")
        assert git, "git is not on PATH"
        for up in pathlib.Path(git).resolve().parents:
            for rel in ("usr/bin/bash.exe", "bin/bash.exe"):
                if (up / rel).is_file():
                    return str(up / rel)
        raise AssertionError("no Git Bash beside git.exe")
    bash = shutil.which("bash")
    assert bash, "bash is not on PATH"
    return bash


def two_tests(tmp_path):
    """A configured tree whose tests/x holds two passing tests, and the environment to run its stage script in:
    with colour forced on, so that every run here holds the script's --color=no, whatever the user's terminal sets
    (P0.1's verifier, round 3, G2: this test's own nested pytest read a coloured line under FORCE_COLOR)."""
    import sys
    root = configured_tree(tmp_path)
    (root / "tests" / "x").mkdir()
    for name in ("test_a.py", "test_b.py"):
        (root / "tests" / "x" / name).write_text("def test_it():" + chr(10) + "    pass" + chr(10), encoding="utf-8")
    return root, dict(os.environ, PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""),
                      FORCE_COLOR="1", PY_COLORS="1")


def stage(root, env):
    import subprocess
    return subprocess.run([runner_bash(), "verify/pytest-stage.sh", "tests/x"], cwd=root, capture_output=True,
                          text=True, env=env)


@pytest.mark.parametrize("rel, text", [
    ("tests/x/pytest.ini", "[pytest]" + chr(10) + "addopts = --ignore=tests/x/test_a.py" + chr(10)),
    ("pytest.toml", "[pytest]" + chr(10) + 'addopts = ["--ignore=tests/x/test_a.py"]' + chr(10)),
    ("tests/conftest.py", 'collect_ignore_glob = ["*test_a.py"]' + chr(10))],
    ids=["a pytest.ini under tests", "a pytest.toml at the root", "a conftest.py hiding a test"])
def test_the_stage_script_reads_no_configuration_file_but_the_roots_and_no_conftest(tmp_path, rel, text):
    """D1 and R2-1, watched end to end: the plant takes a test out when pytest finds it, and the stage script runs
    both. The conftest.py is round 2's, which hid the test that forbids it."""
    import subprocess
    import sys
    root, env = two_tests(tmp_path)
    (root / rel).write_text(text, encoding="utf-8")
    found = subprocess.run([sys.executable, "-m", "pytest", "--color=no", "-q", "-p", "no:cacheprovider", "tests/x"],
                           cwd=root, capture_output=True, text=True, env=env)
    assert found.stdout.strip().splitlines()[-1].startswith("1 passed"), found.stdout[-500:]
    staged = stage(root, env)
    assert staged.returncode == 0 and "2 passed" in staged.stdout, staged.stdout[-500:]


def test_the_stage_script_runs_a_test_below_a_directory_pytest_skips_by_default(tmp_path):
    """G1, end to end: with norecursedirs empty, a test below build/ is run, and fails its stage when it fails."""
    root, env = two_tests(tmp_path)
    (root / "tests" / "x" / "build").mkdir()
    (root / "tests" / "x" / "build" / "test_c.py").write_text("def test_it():" + chr(10) + "    assert False" + chr(10),
                                                               encoding="utf-8")
    staged = stage(root, env)
    assert staged.returncode == 1 and "1 failed, 2 passed" in staged.stdout, staged.stdout[-500:]


def test_the_stage_script_refuses_a_pytest_plugins_line_before_pytest_runs(tmp_path):
    """P0.1's verifier, round 3, G3: a test module's pytest_plugins line loaded a plugin that took tests out of their
    stage, this registry's own among them. The script refuses it before pytest starts, where no test can reach."""
    root, env = two_tests(tmp_path)
    (root / "tests" / "x" / "test_c.py").write_text("pytest_plugins = ['zzplug']" + chr(10), encoding="utf-8")
    (root / "tests" / "x" / "zzplug.py").write_text(chr(10).join([
        "def pytest_collection_modifyitems(items):", "    items[:] = [i for i in items if 'test_a' not in i.nodeid]",
        ""]), encoding="utf-8")
    staged = stage(root, env)
    assert staged.returncode == 1 and "pytest_plugins" in staged.stdout and "passed" not in staged.stdout, \
        staged.stdout[-500:]


def test_the_stage_script_takes_the_environments_options_and_colour_away(tmp_path):
    """Note 4.1.1: options from the environment, and colour in the summary line, are not the stage's."""
    root, env = two_tests(tmp_path)
    for extra in ({"PYTEST_ADDOPTS": "--ignore=tests/x/test_a.py"}, {"FORCE_COLOR": "1", "PY_COLORS": "1"}):
        staged = stage(root, dict(env, **extra))
        assert staged.returncode == 0 and "2 passed" in staged.stdout, (extra, staged.stdout[-500:])


def test_the_stage_script_fails_a_skip_inside_the_stage(tmp_path):
    root, env = two_tests(tmp_path)
    (root / "tests" / "x" / "test_b.py").write_text(
        "import pytest" + chr(10) + chr(10) + chr(10) + "def test_it():" + chr(10) + "    pytest.skip('no')" + chr(10),
        encoding="utf-8")
    staged = stage(root, env)
    assert staged.returncode == 1 and "did not hold to a verdict" in staged.stdout, staged.stdout[-500:]


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


def test_a_test_file_where_pytest_never_looks_is_an_orphan(tmp_path):
    """P0.1's verifier, round 3, G1: below __pycache__ or a virtual environment pytest collects nothing, whatever
    its options; below build/ or a dot-directory it does, with norecursedirs empty."""
    for rel in ("tests/format/test_ok.py", "tests/format/build/test_run.py", "tests/format/.hidden/test_run2.py",
                "tests/format/__pycache__/test_lost.py", "tests/format/env/test_lost2.py",
                "tests/format/conda/deep/test_lost3.py"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("", encoding="utf-8")
    (tmp_path / "tests" / "format" / "env" / "pyvenv.cfg").write_text("home = x" + chr(10), encoding="utf-8")
    (tmp_path / "tests" / "format" / "conda" / "conda-meta").mkdir()
    (tmp_path / "tests" / "format" / "conda" / "conda-meta" / "history").write_text("", encoding="utf-8")
    dirs = staged_dirs('stage format "x" -- \\\n  bash verify/pytest-stage.sh tests/format\n')
    assert orphans(tmp_path, dirs) == ["tests/format/__pycache__/test_lost.py",
                                       "tests/format/conda/deep/test_lost3.py", "tests/format/env/test_lost2.py"]


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


def misnamed(root):
    """Each .py file under a parcel's tests/<parcel>/ not named for it: test_<parcel>_*.py, or <parcel>_*.py for a
    helper. pytest imports every one of them under its bare basename, so two parcels building at once could each
    add a test_steps.py, or a helpers.py, and stop a session over tests/ at collection (P0.1's verifier, round 1,
    D3). With the prefix, two parcels' names never meet; P0's directories carry no parcel's name."""
    out = []
    for d in sorted(p for p in (root / "tests").iterdir() if p.is_dir() and re.fullmatch(r"p[0-9]+", p.name)):
        for f in sorted(d.rglob("*.py")):
            if not re.fullmatch(rf"(test_)?{d.name}_[A-Za-z0-9_]+\.py", f.name):
                out.append(f.relative_to(root).as_posix())
    return out


def test_each_parcels_python_files_carry_its_prefix():
    assert misnamed(ROOT) == []


def test_a_parcel_file_without_its_prefix_is_caught(tmp_path):
    """A nested file without the prefix too (P0.1's verifier, round 2, 4.1.5)."""
    for rel in ("tests/p1/test_p1_steps.py", "tests/p1/p1_helpers.py", "tests/p1/deep/test_p1_more.py",
                "tests/p1/test_steps.py", "tests/p1/helpers.py", "tests/p1/__init__.py", "tests/p2/test_p1_steps.py",
                "tests/p1/deep/helpers.py", "tests/format/test_steps.py"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("", encoding="utf-8")
    assert misnamed(tmp_path) == ["tests/p1/__init__.py", "tests/p1/deep/helpers.py", "tests/p1/helpers.py",
                                  "tests/p1/test_steps.py", "tests/p2/test_p1_steps.py"]
