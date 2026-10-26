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
  - a negative control's stage, which the runner marks MUST_FAIL, runs no tool's check: it shows that the command
    line still refuses its plant, not that the runner counts a failure (below). So the twin's stage cannot be
    deleted with the control's line standing in for it;
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
the next stage the runner calls, which runs what it guards, a pytest stage its directory and a tool's stage its
script; each `need_env` names a variable the runner reads elsewhere, in no comment, and gives a reason naming it;
every guard is called in the one form these rules read (P0.3; P0.4); a stage that runs a directory or a tool the
tree does not hold yet is guarded by a `need_file` of it (P0.4's verifier, round 4, note 6); and the quick budget
is every stage but the six CLAUDE.md names (round 2, note 4.1.2; round 3, note 5; P0.3).
A test no stage runs is reported among the files git would commit (stray_tests; P0.1's verifier, round 4, N2): a
test file outside tests/, and a module under tests/ that pytest does not collect but that holds a line beginning
`def test` or `class Test`, pytest's own naming. git runs here as in the privacy gate, without the variables git
lists as pointing it at a repository, its configuration's kept (P0.2's verifier, rounds 1 and 2, G5); a file it
lists that is not there is not
read (G4); and the lint must name every top-level directory holding a .py file git would commit (G2).
Stated limits (P0's verifier, round 4, notes 1 to 3): this reads the runner's text, not its run. So it cannot see
a stage the shell never reaches (inside `if false`, after an `exit 0`), a tool's own flag that masks its exit
(`--exit-zero`, `--help`; ruff's own options are refused in the lint, whose words after `check` are names, each
once: P0.6's verifiers, rounds 1 and 2, and P0.7), or the runner's own exit status. Each run prints a line for
every stage it ran. The
negative control shows on every run that the command line still refuses its plant, not that the runner counts
a failure, since the control's verdict is inverted: so a test runs the runner itself on a copy whose one stage
fails, which it must count and exit 1 for (P0.4's verifier, round 4, note 5). While a stage's tool is absent,
which of its checks the stage runs is read by nothing here; once the tool exists, its own source says (note 6).
A stage whose own line reads a variable is held to its `need_env` (env_unguarded). One whose tests read the
variable, and whose line does not, is held by nothing here: p1-crates', p2-crates' and p4-shacl's. Deleting one of
those passes, and the stage then fails where the variable is unset, loudly, rather than skipping by name; the tests of
the guards' forms take p4-shacl's call as their text, so deleting that one fails them, though no rule asks for it
(P0.6's verifiers, round 2, note 6, and round 3, D2). Nor is a `need_env` caught before a stage that needs no
variable: it skips that stage by name wherever the variable is unset (round 4, a note, MEASURED).
And a test module is code pytest runs:
one written to reach into pytest's own state, past the stage script's refusal of `pytest_plugins`, can take
tests out of its stage, and no pin here can stop it (P0.1's verifier, round 3, G3). stray_tests reads lines, not
code: a test written `async def test`, `def  test` or after a byte-order mark on the first line is not seen; it
reads only tests/, since a module elsewhere may name a function test_* that is no test; and a helper module under
tests/ that names a function `test*` or a class `Test*`, as pytest names tests, is reported though it holds none
(P0.2's verifier, round 1, G3).
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


def git_env():
    """The process's environment without the variables that point git at a repository: those git itself lists
    (`git rev-parse --local-env-vars`) but its configuration's, GIT_CONFIG and those beginning GIT_CONFIG_. With
    GIT_DIR and GIT_WORK_TREE naming another repository, committed_files listed that one's files, and a stray test
    passed (P0.2's verifier, round 1, G5); dropping the configuration's too made git refuse a checkout it trusted
    only through them (round 2). As the privacy gate's, but for GIT_NO_REPLACE_OBJECTS, which the gate sets as it
    reads objects and `git ls-files`, reading the index, does not need (P0.6's verifier, round 2, note 14)."""
    import subprocess
    local = subprocess.run(["git", "rev-parse", "--local-env-vars"], capture_output=True, text=True,
                           check=True).stdout.split()
    drop = {k for k in local if k != "GIT_CONFIG" and not k.startswith("GIT_CONFIG_")}
    return {k: v for k, v in os.environ.items() if k.upper() not in drop}


def committed_files(root):
    """Every file git would commit, as the privacy gate reads them, but one git lists that is not there (P0.2's
    verifier, round 1, G4: a tracked helper deleted, its deletion not yet added); with no .git, every file below
    the root but those in a dot-directory or __pycache__."""
    import subprocess
    if (root / ".git").exists():
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "-co", "--exclude-standard"],
                             capture_output=True, check=True, env=git_env()).stdout
        return sorted(p for p in (root / q.decode("utf-8") for q in out.split(b"\0") if q) if p.is_file())
    return sorted(p for p in root.rglob("*") if p.is_file() and not any(
        part.startswith(".") or part == "__pycache__" for part in p.relative_to(root).parts))


TEST_FILE = re.compile(r"test_.*[.]py|.*_test[.]py")


def stray_tests(root):
    """Tests no stage runs, outside what orphans() reads (P0.1's verifier, round 4, N2): a test file outside
    tests/, in qro/ say, which no stage's directory holds; and, under tests/, test functions or classes in a module
    pytest never collects, a parcel's p2_*.py helper among them."""
    out = []
    for f in committed_files(root):
        rel = f.relative_to(root)
        if TEST_FILE.fullmatch(f.name) and rel.parts[0] != "tests":
            out.append(f"{rel.as_posix()}: a test file outside tests/, which no stage runs")
        elif f.suffix == ".py" and rel.parts[0] == "tests" and not TEST_FILE.fullmatch(f.name) and re.search(
                r"^(def test|class Test)", f.read_bytes().decode("utf-8", errors="replace"), re.M):
            out.append(f"{rel.as_posix()}: tests in a module pytest never collects")
    return out


def test_no_test_is_where_no_stage_runs_it():
    assert stray_tests(ROOT) == []


def test_a_test_where_no_stage_runs_it_is_caught(tmp_path):
    for rel, text in (("qro/test_x.py", ""), ("tools/y_test.py", ""), ("tests/p2/p2_hidden.py", "def test_a():"),
                      ("tests/p2/p2_cases.py", "class TestCases:"), ("tests/p2/p2_helpers.py", "def helper():"),
                      ("tests/p2/test_p2_ok.py", "def test_b():"), (".venv/Lib/site-packages/pkg/test_z.py", "")):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text + chr(10), encoding="utf-8")
    assert stray_tests(tmp_path) == ["qro/test_x.py: a test file outside tests/, which no stage runs",
                                     "tests/p2/p2_cases.py: tests in a module pytest never collects",
                                     "tests/p2/p2_hidden.py: tests in a module pytest never collects",
                                     "tools/y_test.py: a test file outside tests/, which no stage runs"]


def test_a_test_where_no_stage_runs_it_is_caught_in_a_repository_as_git_lists_its_files(tmp_path, monkeypatch):
    """P0.2's verifier, round 1: every plant above sits where there is no .git, so git's listing was held by none
    (T1), and each test was on its module's first line (T2). Here, in a repository: a test below an import; a test
    file git has not been told of; a tracked helper deleted, its deletion not added, and one not in UTF-8 (G4); an
    ignored environment holding Python, which the lint need not name (G2); and git's variables naming another
    repository and a broken index (G5). After round 2, the scan's own edges too: a test named `testing...`, a
    helper outside a parcel's directory, a test in a file that is no module, and one outside tests/. Its gits read
    none of the user's configuration or ignore files."""
    import subprocess
    empty = tmp_path / "gitconfig-empty"
    empty.write_text("", encoding="utf-8")
    for k, v in (("GIT_CONFIG_GLOBAL", str(empty)), ("GIT_CONFIG_NOSYSTEM", "1"),
                 ("XDG_CONFIG_HOME", str(tmp_path / "xdg"))):
        monkeypatch.setenv(k, v)
    repo, other = tmp_path / "repo", tmp_path / "other"
    for rel, text in (("tests/p2/p2_hidden.py", chr(10).join(["import os", "", "def test_a():", "    pass", ""])),
                      ("tests/p2/p2_gone.py", "def helper():" + chr(10)), (".gitignore", "/venv/" + chr(10)),
                      ("tests/p2/p2_latin.py", "# caf" + chr(0xE9) + chr(10)),
                      ("tests/p2/p2_named.py", "def testing_dir():" + chr(10)),
                      ("tests/p2/p2_notes.txt", "def test_a():" + chr(10)),
                      ("tests/helpers/common.py", "class TestBase:" + chr(10)),
                      ("qro/helper.py", "def test_x():" + chr(10)),
                      ("venv/Lib/site-packages/pkg/test_z.py", "def test_z():" + chr(10))):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_bytes(text.encode("latin-1"))
    other.mkdir()
    for r in (repo, other):
        subprocess.run(["git", "-C", str(r), "init", "-q"], check=True, env=git_env())
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, env=git_env())
    (repo / "tests" / "p2" / "p2_gone.py").unlink()
    (repo / "qro" / "test_x.py").write_text("", encoding="utf-8")
    (other / "garbage-index").write_bytes(b"not an index")
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    monkeypatch.setenv("GIT_INDEX_FILE", str(other / "garbage-index"))
    assert stray_tests(repo) == ["qro/test_x.py: a test file outside tests/, which no stage runs",
                                 "tests/helpers/common.py: tests in a module pytest never collects",
                                 "tests/p2/p2_hidden.py: tests in a module pytest never collects",
                                 "tests/p2/p2_named.py: tests in a module pytest never collects"]
    assert shape_problems(repo, RUNNER) == []


@pytest.mark.parametrize("given", [(("GIT_CONFIG_COUNT", "1"), ("GIT_CONFIG_KEY_0", "safe.directory"),
                                      ("GIT_CONFIG_VALUE_0", "*")),
                                     (("GIT_CONFIG_PARAMETERS", "'safe.directory'='*'"),)],
                         ids=["as a count", "as git -c gives it to a hook"])
def test_committed_files_keep_the_configuration_git_is_given_in_the_environment(tmp_path, monkeypatch, given):
    """P0.2's verifier, round 2: git_env dropped GIT_CONFIG_COUNT too, so a checkout git trusts only through a
    safe.directory given that way was refused, and the registry raised. GIT_TEST_ASSUME_DIFFERENT_OWNER is git's
    own switch for treating a checkout as another user's; no configuration of the user's trusts it here."""
    import subprocess
    empty = tmp_path / "gitconfig-empty"
    empty.write_text("", encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("", encoding="utf-8")
    for k, v in (("GIT_CONFIG_GLOBAL", str(empty)), ("GIT_CONFIG_NOSYSTEM", "1"),
                 ("XDG_CONFIG_HOME", str(tmp_path / "xdg"))):
        monkeypatch.setenv(k, v)
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True, env=git_env())
    for k, v in (("GIT_TEST_ASSUME_DIFFERENT_OWNER", "1"),) + given:
        monkeypatch.setenv(k, v)
    assert committed_files(repo) == [repo / "a.py"]


def test_committed_files_fail_loudly_where_git_cannot_list_them(tmp_path, monkeypatch):
    """A broken index is git's failure, raised, never an empty list that passes (P0.2's verifier, round 2). Its
    git reads none of the user's configuration or ignore files (round 3)."""
    import subprocess
    empty = tmp_path / "gitconfig-empty"
    empty.write_text("", encoding="utf-8")
    for k, v in (("GIT_CONFIG_GLOBAL", str(empty)), ("GIT_CONFIG_NOSYSTEM", "1"),
                 ("XDG_CONFIG_HOME", str(tmp_path / "xdg"))):
        monkeypatch.setenv(k, v)
    (tmp_path / "repo").mkdir()
    tmp_path = tmp_path / "repo"
    (tmp_path / "a.py").write_text("", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True, env=git_env())
    (tmp_path / ".git" / "index").write_bytes(b"not an index")
    with pytest.raises(subprocess.CalledProcessError):
        committed_files(tmp_path)


def test_committed_files_reads_a_linked_worktree_whose_git_is_a_file(tmp_path, monkeypatch):
    """P0.2's verifier, round 4: the parcels build in linked worktrees, and no test listed one's files. An ignored
    file tells git's listing from the walk a copy with no .git gets (P0.4's verifier, round 1)."""
    import subprocess
    empty = tmp_path / "gitconfig-empty"
    empty.write_text("", encoding="utf-8")
    for k, v in (("GIT_CONFIG_GLOBAL", str(empty)), ("GIT_CONFIG_NOSYSTEM", "1"),
                 ("XDG_CONFIG_HOME", str(tmp_path / "xdg"))):
        monkeypatch.setenv(k, v)
    repo, w = tmp_path / "repo", tmp_path / "linked"
    repo.mkdir()
    (repo / "a.py").write_text("", encoding="utf-8")
    (repo / ".gitignore").write_text("ignored.py" + chr(10), encoding="utf-8")
    git = ["git", "-C", str(repo), "-c", "user.name=x", "-c", "user.email=x@example.org"]
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "one"], ["worktree", "add", "-q", str(w)]):
        subprocess.run(git + args, check=True, env=git_env())
    (w / "b.py").write_text("", encoding="utf-8")
    (w / "ignored.py").write_text("", encoding="utf-8")
    assert (w / ".git").is_file() and committed_files(w) == [w / ".gitignore", w / "a.py", w / "b.py"]


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
    python_dirs = {f.relative_to(root).parts[0] for f in committed_files(root) if f.suffix == ".py"} - {"docs"}
    python_dirs = {d for d in python_dirs if not d.startswith(".")}
    if len(lint) != 1 or not python_dirs <= set(lint[0].split()):
        out.append(f"the lint does not name every directory holding Python: {sorted(python_dirs)}")
    elif lint[0].split()[:4] != ["python", "-m", "ruff", "check"]:      # P0.4's verifier, round 4, note 4: `python -`
        out.append(f"the lint is not `python -m ruff check`: {lint[0].strip()}")   # read an empty program, lint ok
    elif any(w.startswith("-") for w in lint[0].split()[4:]) or len(set(lint[0].split()[4:])) < len(lint[0].split()[4:]):
        out.append(f"the lint names directories, each once, and no option: {lint[0].strip()}")  # P0.6's verifier, round 1
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
NEED_ENV = 'need_env ()  { [ -n "${!1:-}" ] || STAGE_SKIP_REASON="$2"; }'
# A comment, as bash starts one: a `#` that begins a word, at a line's start or after a blank or a metacharacter
# (P0.4's verifiers, rounds 1 and 2). A quoted `#` there ends what is read too. For the need_env rule, which looks
# for a read, that can only flag more; guards_off_form, which looks for a call, strips only a comment that fills
# its line, since there stripping more hides a call (round 3, R3-1).
COMMENT = r"(^|[ \t;&|()<>])#.*$"
COMMENT_LINE = r"^[ \t]*#.*$"


def guard_problems(runner_text):
    """Each `need_file` guards the next stage the runner calls, as the runner reads it, whatever lines come between;
    that stage runs what it guards, a pytest stage its directory and a tool's stage its script (P0.3); and
    `need_file` skips only while its path is missing
    (P0.1's verifier, round 2, note 4.1.2: p1's guard naming tests/p2, or written with -f, skipped p1 by name after
    tests/p1 was built, and the run passed; round 3, note 5: a comment between a guard and its stage hid both).
    And each `need_env` names a variable the runner reads elsewhere, in no comment, so that a misspelt one cannot
    skip its stage by name for ever (P0.3's verifier, round 1); its reason names that variable, so that one
    repointed at another's skips with a reason that is not its own no longer (P0.4's verifier, round 1); and
    `need_env` skips only while its variable is empty or unset (round 2)."""
    out = [] if NEED_FILE in runner_text.splitlines() else ["need_file is not " + NEED_FILE]
    out += [] if NEED_ENV in runner_text.splitlines() else ["need_env is not " + NEED_ENV]
    for m in re.finditer(r'^need_file ([\w./-]+) "', runner_text, re.M):          # a call: a path and its reason
        nxt = re.compile(r'^stage ([a-z0-9-]+) "[^"]*" -- \\\n(.*)$', re.M).search(runner_text, m.end())
        if nxt is None:
            out.append(f"need_file {m.group(1)} guards no stage")
            continue
        name, words = nxt.group(1), nxt.group(2).split()
        ran = words[words.index("verify/pytest-stage.sh") + 1] if "verify/pytest-stage.sh" in words else None
        if ran is None and "python" in words:                       # a tool's stage: python [-I] TOOL ...
            ran = next((w for w in words[words.index("python") + 1:] if w != "-I"), None)
        if ran != m.group(1):
            out.append(f"stage {name} runs {ran}, and guards {m.group(1)}")
    elsewhere = chr(10).join(re.sub(COMMENT, "", line) for line in runner_text.splitlines()
                             if not line.startswith("need_env "))
    for m in re.finditer(r'^need_env ([A-Za-z_][A-Za-z0-9_]*) "(.*)$', runner_text, re.M):     # and its reason
        if not re.search(re.escape("$") + "[{]?" + m.group(1) + "(?![A-Za-z0-9_])", elsewhere):
            out.append(f"need_env {m.group(1)} names a variable the runner reads nowhere else")
        elif not re.search("(?<![A-Za-z0-9_])" + m.group(1) + "(?![A-Za-z0-9_])", m.group(2)):
            out.append(f"need_env {m.group(1)} gives a reason that does not name it")
    return out


GUARD_CALL = re.compile(r'need_env [A-Za-z_][A-Za-z0-9_]* "[^"]*"|need_file [\w./-]+ "[^"]*"')


def guards_off_form(runner_text):
    """Each line that names a guard, need_file, need_env or moth-quantum's need, outside a line that is a comment,
    and is not a call of need_file or need_env in the one form the rules above read: at the line's start, one blank
    apart, its reason in double quotes to the line's end. A call indented, tabbed, after another command, its reason
    quoted otherwise or bare, or continued, was read by none of them, so a misspelt variable in it passed (P0.4's
    verifier, round 2, N2); so was one after a quoted `#`, which the comment rule took for a comment (round 3,
    R3-1); and need, which the runner no longer defines, was read by no rule (round 3). The two definitions are no
    calls."""
    return [line for line in runner_text.splitlines() if line not in (NEED_FILE, NEED_ENV)
            and not GUARD_CALL.fullmatch(line)
            and re.search(r"(?<![\w-])need(_env|_file)?(?![\w-])", re.sub(COMMENT_LINE, "", line))]


def test_every_guard_is_called_in_the_one_form_the_rules_read():
    assert guards_off_form(RUNNER) == []


@pytest.mark.parametrize("new", ['  need_env QRO_SHACL_PYTHO "x"', 'need_env  QRO_SHACL_PYTHO "x"',
                                 "need_env" + chr(9) + 'QRO_SHACL_PYTHO "x"', "need_env QRO_SHACL_PYTHO 'x'",
                                 "need_env QRO_SHACL_PYTHO x", "need_env QRO_SHACL_PYTHO " + chr(92) + chr(10) + '  "x"',
                                 'true; need_file tests/p9 "x"', 'echo "a #b"; need_env QRO_SHACL_PYTHO "x"',
                                 'need_env QRO_SHACL_PYTHON "x"; need_env QRO_SHACL_PYTHO "y"',
                                 'need zz_no_such_command "x"'],
                         ids=["indented", "two blanks", "a tab", "single-quoted", "bare", "continued",
                              "a need_file after another command", "after a quoted #", "a second call on its line",
                              "need, which no rule reads"])
def test_a_guard_called_in_another_form_is_caught(new):
    """P0.4's verifier, round 2, N2: each of these passed every rule, a need_env's variable misspelt, and the
    need_file's path missing; round 3: and so did a call after a quoted `#` (R3-1), a second call on one line, and
    a call of need."""
    planted = RUNNER.replace('need_env QRO_SHACL_PYTHON "', new + chr(10) + 'need_env QRO_SHACL_PYTHON "', 1)
    assert planted != RUNNER and guards_off_form(planted) == [new.split(chr(10))[0]], guards_off_form(planted)


@pytest.mark.parametrize("indent", ["", "  ", chr(9), " " + chr(9) + " "], ids=["none", "blanks", "a tab",
                                                                             "blanks and a tab"])
def test_a_comment_line_naming_a_guard_is_no_call(indent):
    """P0.4's verifier, round 3: no comment of the runner names a guard, so the stripping of a comment line was
    held by nothing; round 4, note 7: a comment line indented by a tab was held by nothing either."""
    planted = RUNNER.replace('need_env QRO_SHACL_PYTHON "', indent + '# need_env QRO_SHACL_PYTHO "x"' + chr(10)
                             + 'need_env QRO_SHACL_PYTHON "', 1)
    assert planted != RUNNER and guards_off_form(planted) == []


def test_a_word_that_only_holds_a_guards_name_is_no_call():
    """P0.4's verifier, round 4, note 7: the guard word's look-behind was held by nothing, since the runner's own text
    holds no word ending in a guard's name; its look-ahead is held by `needs` in the runner's messages, and here."""
    line = ": xneed_env pre-need_file need_envx need_file-y unneed"
    planted = RUNNER.replace("stage study ", line + chr(10) + chr(10) + "stage study ", 1)
    assert planted != RUNNER and guards_off_form(planted) == []


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
                                      ('need_file tools/gen_profile.py "', 'need_file tools/gen_vocabulary.py "'),
                                      ('need_env QRO_SHACL_PYTHON "', 'need_env QRO_SHACL_PYTHO "'),
                                      ('need_env QRO_SHACL_PYTHON "', 'need_env QRO_MOTH_ROOT "'),
                                      ("tests/p1" + chr(10) + chr(10) + "need_file tests/p2",
                                       "tests/p2" + chr(10) + chr(10) + "need_file tests/p2"),
                                      ('[ -e "$1" ]', '[ -f "$1" ]'),
                                      ('[ -n "${!1:-}" ]', '[ -z "${!1:-}" ]'),
                                      ('need_file tests/p1 "P1, the adapter, is not built yet: there is no tests/p1"'
                                       + chr(10) + "stage p1 ",
                                       'need_file tests/p2 "another\'s"' + chr(10) + "# a comment between" + chr(10)
                                       + chr(10) + "stage p1 ")],
                         ids=["the guard another's", "a tool's guard another's", "a variable misspelt",
                              "a variable another stage's", "the stage another's", "files only",
                              "a variable's guard inverted", "a comment between"])
def test_a_guard_that_is_not_its_stages_is_caught(old, new):
    planted = RUNNER.replace(old, new, 1)
    assert planted != RUNNER and len(guard_problems(planted)) == 1, guard_problems(planted)


def test_a_tools_stage_is_guarded_by_its_script_run_with_or_without_isolation():
    """P0.3: P4's profile stage runs a tool, and its guard names the tool's script, `python -I` or not."""
    isolated = RUNNER.replace("  python tools/gen_profile.py --check", "  python -I tools/gen_profile.py --check", 1)
    assert isolated != RUNNER and guard_problems(isolated) == []


@pytest.mark.parametrize("comment", ["# ", ": # ", ":" + chr(9) + "# ", "true;# ", "true&&# ", "true|# ", "(# ",
                                     "true)# ", "true<# ", "true># "],
                         ids=["a comment line", "a trailing comment", "after a tab", "after a semicolon",
                              "after two ampersands", "after a bar", "after an opening parenthesis",
                              "after a closing parenthesis", "after a less-than", "after a greater-than"])
def test_a_variable_the_runner_names_only_in_a_comment_is_read_nowhere(comment):
    """P0.3's verifier, round 2: the rule took the engine's name in a comment for a read of it; P0.4's, round 1: a
    trailing comment, after a command that does nothing, still counted; round 2, N1: so did one after a
    metacharacter with no blank, which bash takes for a comment too; round 3: each such metacharacter is held."""
    planted = chr(10).join((comment + line) if "QRO_SHACL_PYTHON" in line and not line.startswith("need_env ")
                           else line for line in RUNNER.splitlines())
    assert planted != RUNNER and guard_problems(planted) == [
        "need_env QRO_SHACL_PYTHON names a variable the runner reads nowhere else"]


PACKAGES = re.search(r"^PACKAGES='([^']*)'$", RUNNER, re.M)


def test_the_package_list_reads_a_distribution_with_no_name(tmp_path):
    """P0.4's verifier, round 1, D1: the runner's expression for the engine's packages raised on a distribution with
    no METADATA, and the runner hashed the traceback, so a package added to the engine went unseen by --resume.
    The expression is read from the runner's own text, which both the interpreter's packages and the engine's
    read, and run on such a distribution."""
    import subprocess
    import sys
    assert PACKAGES, "the runner names no PACKAGES"
    body = re.search(r"^fingerprint \(\) \{\n(.*?)^\}", RUNNER, re.M | re.S).group(1)
    assert '  echo "packages=$(packages python)"' in body.splitlines(), body
    assert '  echo "shacl-engine=$(shacl_engine)"' in body.splitlines(), body
    (tmp_path / "nameless-1.0.dist-info").mkdir()
    code = "import sys; sys.path.insert(0, " + repr(str(tmp_path)) + "); " + PACKAGES.group(1)
    r = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
    assert r.returncode == 0 and "None==None" in r.stdout, (r.stdout, r.stderr)


def test_the_package_list_reads_metadata_that_raises_on_a_missing_key():
    """P0.4's verifier, round 2, N6: indexing a missing key returns None with a warning in Python 3.12 and 3.13, and
    raises KeyError in importlib_metadata 8, as the standard library is to; and a distribution's metadata may be
    None there. The expression reads each with .get, here on metadata of each kind."""
    import contextlib
    import email.message
    import io
    import types

    class Strict(email.message.Message):
        def __getitem__(self, key):
            if self.get(key) is None:
                raise KeyError(key)
            return self.get(key)

    named = Strict()
    named["Name"], named["Version"] = "a", "1.0"
    dists = [types.SimpleNamespace(metadata=md) for md in (named, Strict(), None)]
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        exec(PACKAGES.group(1).replace("import importlib.metadata as m; ", "", 1),
             {"m": types.SimpleNamespace(distributions=lambda: dists)})
    assert out.getvalue() == "['None==None', 'None==None', 'a==1.0']" + chr(10)


def test_the_engines_line_changes_with_its_packages(tmp_path):
    """P0.4's verifier, round 2, N7: the tests above hold the expression, and nothing held the pipeline that hashes
    what it prints, nor the interpreter run isolated (round 1, mutants 21 and 22). The runner's own packages and
    shacl_engine run here, in Git Bash, on an engine that is this interpreter, run only with -I, a directory of
    distributions first on its path: its line is the engine and 16 hexadecimal digits, which change as a
    distribution is added, one with no name among them. And a listing that fails, here a METADATA not in UTF-8,
    hashes differently each time, so --resume refuses it (round 3). The engine is written LF and executable, as a
    POSIX shell runs it (round 3, R3-2: written as text, it failed on POSIX, Permission denied)."""
    import subprocess
    import sys
    funcs = "".join(re.search(rf"^{name} \(\) \{{.*?\n^\}}\n", RUNNER, re.M | re.S).group(0)
                    for name in ("packages", "shacl_engine"))
    dists, engine = tmp_path / "dists", tmp_path / "engine"
    dists.mkdir()
    engine.write_bytes(chr(10).join([
        "#!/bin/sh", '[ "$1" = -I ] && [ "$2" = -c ] || exit 7',
        'exec "' + pathlib.Path(sys.executable).as_posix() + '" -I -c "import sys; sys.path.insert(0, '
        + repr(dists.as_posix()) + '); $3"', ""]).encode("utf-8"))     # LF: write_text writes CRLF on Windows
    engine.chmod(0o755)

    def line():
        r = subprocess.run([runner_bash(), "-c", PACKAGES.group(0) + chr(10) + funcs + "shacl_engine"],
                           capture_output=True, text=True, env=dict(os.environ, QRO_SHACL_PYTHON=engine.as_posix()))
        assert r.returncode == 0 and re.fullmatch(re.escape(engine.as_posix()) + " [0-9a-f]{16}", r.stdout.strip()), (
            r.stdout, r.stderr)
        return r.stdout
    seen = [line()]
    assert line() == seen[0], "a listing that holds the same packages hashes the same"
    for name in ("qro-probe-a-1.0", "qro-probe-b-1.0"):
        (dists / (name + ".dist-info")).mkdir()
        (dists / (name + ".dist-info") / "METADATA").write_text(
            "Metadata-Version: 2.1" + chr(10) + "Name: " + name[:-4] + chr(10) + "Version: 1.0" + chr(10),
            encoding="utf-8")
        seen.append(line())
    (dists / "nameless-1.0.dist-info").mkdir()
    seen.append(line())
    assert len(set(seen)) == 4, seen
    (dists / "latin-1.0.dist-info").mkdir()
    (dists / "latin-1.0.dist-info" / "METADATA").write_bytes(b"Name: latin\nVersion: 1.0\nAuthor: caf\xe9\n")
    failed = [line(), line()]
    assert failed[0] != failed[1] and not set(failed) & set(seen), failed


def unguarded(root, runner_text):
    """Each stage that runs a directory or a tool the tree does not hold, with no `need_file` of it among the guards
    between it and the stage before: it would fail, not skip by name, until its parcel builds it (P0.4's verifier,
    round 4, note 6: a guard deleted was required by nothing). Derived from the tree, not listed: once a parcel's
    directory exists, its stage runs, guarded or not."""
    out, guards = [], []
    lines = runner_text.splitlines()
    for i, line in enumerate(lines):
        if GUARD_CALL.fullmatch(line):
            guards.append(line.split('"')[0].strip())
            continue
        m = re.match(r'stage ([a-z0-9-]+) "[^"]*" -- \\$', line)
        if m is None:
            continue
        words = lines[i + 1].split() if i + 1 < len(lines) else []
        if "verify/pytest-stage.sh" in words:
            ran = words[words.index("verify/pytest-stage.sh") + 1:][:1]
        elif "python" in words:
            ran = [w for w in words[words.index("python") + 1:] if w != "-I"][:1]
        else:
            ran = []
        for path in ran:
            if "/" in path and not path.startswith("-") and not (root / path).exists() \
                    and f"need_file {path}" not in guards:
                out.append(f"stage {m.group(1)} runs {path}, which the tree does not hold, and no need_file guards it")
        guards = []
    return out


def test_each_stage_of_what_the_tree_does_not_hold_is_guarded():
    assert unguarded(ROOT, RUNNER) == []


@pytest.mark.parametrize("command", ["bash verify/pytest-stage.sh tests/pzz", "python tools/gen_pzz.py --check",
                                     "python -I tools/gen_pzz.py --check"],
                         ids=["a pytest stage", "a tool's stage", "a tool's stage, isolated"])
def test_a_stage_of_what_the_tree_does_not_hold_without_its_guard_is_caught(command):
    """Note 6's plant, on a stage of its own, so that it holds whatever the parcels have built: unguarded, it is
    named; guarded by a need_file of what it runs, it is not; guarded by another's, it is named again."""
    path = command.split()[-2] if command.endswith("--check") else command.split()[-1]
    stage_text = 'stage pzz "a stage of what is not built" -- ' + chr(92) + chr(10) + "  " + command + chr(10) + chr(10)

    def runner_with(guard):
        return RUNNER.replace("stage control-tests ", guard + stage_text + "stage control-tests ", 1)
    want = [f"stage pzz runs {path}, which the tree does not hold, and no need_file guards it"]
    assert unguarded(ROOT, runner_with("")) == want
    assert unguarded(ROOT, runner_with(f'need_file {path} "not built"' + chr(10))) == []
    assert unguarded(ROOT, runner_with('need_file tests/pyy "not built"' + chr(10))) == want
    early = RUNNER.replace("stage lint ", f'need_file {path} "not built"' + chr(10) + "stage lint ", 1)
    assert unguarded(ROOT, early.replace("stage control-tests ", stage_text + "stage control-tests ", 1)) == want


def env_unguarded(runner_text):
    """Each stage whose own command reads a variable, with no `need_env` of it among the guards between it and the
    stage before: it would run on an empty value where the variable is unset, not skip by name (P0.6's verifier,
    round 3, D2: the instruments stage's line reads QRO_MOTH_ROOT, and deleting its guard passed every rule here). A
    stage whose tests read a variable, and whose line does not, is read by no rule here (the limits above)."""
    out, guards = [], []
    lines = runner_text.splitlines()
    for i, line in enumerate(lines):
        call = re.fullmatch(r'need_env ([A-Za-z_][A-Za-z0-9_]*) "[^"]*"', line)
        if call:
            guards.append(call.group(1))
            continue
        m = re.match(r'stage ([a-z0-9-]+) "[^"]*" -- \\$', line)
        if m is None:
            continue
        command = re.sub(COMMENT, "", lines[i + 1]) if i + 1 < len(lines) else ""
        out += [f"stage {m.group(1)} reads {name} with no need_env {name} before it"
                for name in re.findall(r"[$][{]?([A-Za-z_][A-Za-z0-9_]*)", command) if name not in guards]
        guards = []
    return out


def test_each_stage_that_reads_a_variable_is_guarded_by_it():
    assert env_unguarded(RUNNER) == []
    assert re.search(r'^need_env QRO_MOTH_ROOT "[^"]*"' + chr(10) + r'stage instruments ', RUNNER, re.M) \
        and '"${QRO_MOTH_ROOT:-}"' in RUNNER, "the instruments stage reads the variable it is guarded by"


@pytest.mark.parametrize("plant", ["deleted", "moved before the stage before", "another variable's"])
def test_a_stage_that_reads_a_variable_without_its_guard_is_caught(plant):
    """D2's plant: the instruments stage's guard deleted, moved before the stage before, where it guards that stage
    instead, or naming another variable; and a stage of its own that reads one unguarded."""
    block = re.search(r'^need_env QRO_MOTH_ROOT "[^"]*"' + chr(10) + "stage instruments ", RUNNER, re.M).group(0)
    guard, stage = block[:-len("stage instruments ")], "stage instruments "
    if plant == "deleted":
        planted = RUNNER.replace(block, stage, 1)
    elif plant == "moved before the stage before":
        planted = RUNNER.replace(block, stage, 1).replace("stage privacy-controls ", guard + "stage privacy-controls ", 1)
    else:
        planted = RUNNER.replace(block, guard.replace("need_env QRO_MOTH_ROOT ", "need_env QRO_SHACL_PYTHON ") + stage, 1)
    assert planted != RUNNER
    assert env_unguarded(planted) == ["stage instruments reads QRO_MOTH_ROOT with no need_env QRO_MOTH_ROOT before it"]
    own = RUNNER.replace("stage study ", 'stage zzenv "a stage that reads a variable" -- ' + chr(92) + chr(10)
                         + '  python tools/zz.py "$ZZ_VAR"' + chr(10) + chr(10) + "stage study ", 1)
    assert env_unguarded(own) == ["stage zzenv reads ZZ_VAR with no need_env ZZ_VAR before it"]
    two = RUNNER.replace("stage study ", 'need_env ZZ_A "zz"' + chr(10) + 'stage zzenv "a stage that reads two" -- '
                         + chr(92) + chr(10) + '  python tools/zz.py "$ZZ_A" "${ZZ_B:-}"' + chr(10) + chr(10)
                         + "stage study ", 1)
    assert env_unguarded(two) == ["stage zzenv reads ZZ_B with no need_env ZZ_B before it"], "a line reading two"


def lint_copy(tmp_path, source):
    """A tree the runner's lint stage runs in: the runner, the root's pyproject.toml, and a Python file in each
    directory the lint names, read from the runner's own lint line, qro/x.py holding `source`. A list written here
    failed the clean case once the lint named another directory (P0.6's verifier, round 1, note)."""
    dirs = [line for line in stage_lines(RUNNER) if "ruff check" in line][0].split()[4:]
    assert "qro" in dirs, dirs
    for d in dirs:
        (tmp_path / d).mkdir(parents=True)
        (tmp_path / d / "__init__.py").write_bytes(b"")
    (tmp_path / "verify").mkdir(exist_ok=True)
    for rel in ("verify/run.sh", "pyproject.toml"):
        (tmp_path / rel).write_bytes((ROOT / rel).read_bytes())
    (tmp_path / "qro" / "x.py").write_bytes(source.encode("ascii"))
    return tmp_path


@pytest.mark.parametrize("source, rc, summary", [("X = 1" + chr(10), 0, "passed 1, failed 0"),
                                                 ("import os" + chr(10), 1, "passed 0, failed 1")],
                         ids=["clean", "a lint fault"])
def test_the_runner_counts_a_failing_stage_and_exits_one(tmp_path, source, rc, summary):
    """P0.4's verifier, round 4, note 5: with a stage's failure counted as none, every test here passed and the runner
    exited 0; the negative control did not see it, as its stage's verdict is inverted. So the runner itself runs, on a
    copy whose one stage fails: it must count the failure, say FAILED and exit 1. The same copy clean passes, so the
    test is no straw man. It needs ruff in the interpreter, as the lint stage does (P0.6's verifier, round 2,
    note 8)."""
    import subprocess
    import sys
    root = lint_copy(tmp_path, source)
    env = dict(os.environ, PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""))
    for k in ("QRO_MOTH_ROOT", "QRO_SHACL_PYTHON", "STATEROOT"):
        env.pop(k, None)
    r = subprocess.run([runner_bash(), "verify/run.sh", "--only", "lint"], cwd=root, capture_output=True, text=True,
                       env=env)
    assert r.returncode == rc and summary in r.stdout and ("== FAILED" in r.stdout) is bool(rc), r.stdout[-800:]


@pytest.mark.parametrize("args, plant, rc, says", [
    (["--only", "lint,p2"], None, 0, "== PASSED, with 1 skipped by name above"),
    (["--only", "lint,p2", "--require-all"], None, 1, "== FAILED"),
    (["--only", "p2"], None, 1, "== FAILED: no stage ran (a skip is not a run)"),
    (["--only", ""], None, 2, "a run of zero stages is not a pass"),
    (["--only", "lint,controls"], "", 1, "NEGATIVE CONTROL DID NOT FAIL"),
    (["--only", "lint,controls"], "print('REFUSED raw-digest at x')" + chr(10) + "raise SystemExit(1)", 0,
     "the negative control failed, as it must"),
    (["--only", "lint,controls"], "raise SystemExit(1)", 1, 'the control failed, but not with "REFUSED raw-digest"')],
    ids=["a skip, passing", "a skip under --require-all", "no stage run", "no stage named", "a control that passes",
         "a control that fails as it must", "a control that fails for another reason"])
def test_the_runner_holds_its_skips_its_selection_and_its_control(tmp_path, args, plant, rc, says):
    """P0.6's fourth verifier, T3: `--require-all` ignored, a run of zero stages passing, and a negative control that
    passes uncounted each passed every test here, though the runner was right in each (MEASURED by it, in copies).
    The runner runs on the lint's copy, where p2 skips by name, and the control's command is a module made here; the
    lint runs beside the control, so that a control's verdict left uncounted shows as a pass."""
    import subprocess
    import sys
    root = lint_copy(tmp_path, "X = 1" + chr(10))
    if plant is not None:
        (root / "controls" / "plant.py").write_bytes((plant + chr(10)).encode("ascii"))
    env = dict(os.environ, PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""))
    for k in ("QRO_MOTH_ROOT", "QRO_SHACL_PYTHON", "STATEROOT"):
        env.pop(k, None)
    r = subprocess.run([runner_bash(), "verify/run.sh", *args], cwd=root, capture_output=True, text=True, env=env)
    assert r.returncode == rc and says in r.stdout + r.stderr, (r.stdout + r.stderr)[-800:]


def quick_problems(runner_text):
    """CLAUDE.md: the quick budget is "all but study-plants, privacy-controls, instruments, p1-crates, p2-crates and
    p4-shacl" (round 2, note
    4.1.2: a parcel's stage dropped from it, or a stage renamed, was held by no test)."""
    quick = set(re.search(r"^BUDGET_QUICK=([a-z0-9,-]+)$", runner_text, re.M).group(1).split(","))
    want = set(stage_names(runner_text)) - {"study-plants", "privacy-controls", "instruments", "p1-crates",
                                            "p2-crates", "p4-shacl"}
    return sorted(quick ^ want)


def test_the_quick_budget_is_every_stage_but_those_claude_md_names():
    assert quick_problems(RUNNER) == []


def test_a_stage_dropped_from_the_quick_budget_or_renamed_is_caught():
    assert quick_problems(RUNNER.replace(",p2,", ",", 1)) == ["p2"]
    assert quick_problems(RUNNER.replace("stage p4 ", "stage p44 ", 1)) == ["p4", "p44"]


PYTEST_OPTIONS = {"pythonpath": ["."], "testpaths": ["tests"], "addopts": "-p no:cacheprovider", "norecursedirs": [],
                  "filterwarnings": ["error::pytest.PytestCollectionWarning", "error::pytest.PytestReturnNotNoneWarning",
                                     "error::pytest.PytestUnknownMarkWarning",
                                     "error::pytest.PytestAssertRewriteWarning"]}
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
STAGE_COMMANDS_SHA256 = "591ed19eff1d3732cf21591e2eeeb22d6123244869759e626f5b08292b287774"


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


@pytest.mark.parametrize("name, text", [
    ("test_c.py", chr(10).join(["class TestHeld:", "    def __init__(self):", "        pass", "", "",
                                "    def test_it(self):", "        assert False", ""])),
    ("test_c.py", chr(10).join(["def test_it():", "    return 1 == 2", ""])),
    ("test_c.py", chr(10).join(["import pytest", "", "", "@pytest.mark.slowish", "def test_it():", "    pass", ""])),
    ("test_c.py", chr(10).join(["def test_it():", "    assert (1 == 2, 'always true')", ""]))],
    ids=["a class pytest cannot collect", "a test that returns where it should assert", "a mark unknown",
         "an assert on a tuple"])
def test_the_stage_fails_on_each_warning_that_a_test_is_not_held(tmp_path, name, text):
    """P0.1's verifier, round 4, N1: each passed its stage with "1 warning"; and P0.2's, round 1, G1, the tuple.
    Without pytest's warnings plugin, so with no filter, the same tree passes: the plant bites through the filter
    alone. That run writes no bytecode: pytest warns of the tuple only as it rewrites the module, and a rewrite
    cached by a run with no filter hides it from the stage (MEASURED, pytest 9.1.1; pyproject.toml says so)."""
    import subprocess
    import sys
    root, env = two_tests(tmp_path)
    (root / "tests" / "x" / name).write_text(text, encoding="utf-8")
    unfiltered = subprocess.run([sys.executable, "-m", "pytest", "-c", "pyproject.toml", "--noconftest", "--color=no",
                                 "-q", "-p", "no:warnings", "tests/x"], cwd=root, capture_output=True, text=True,
                                env=dict(env, PYTHONDONTWRITEBYTECODE="1"))
    assert unfiltered.returncode == 0, unfiltered.stdout[-500:]
    staged = stage(root, env)
    assert staged.returncode == 1, staged.stdout[-500:]


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
    (("python -m ruff check qro", "python - ruff check qro"), "is not `python -m ruff check`"),
    (("python -m controls.plant twin", "python -m controls.plant shot-moved"), "does not plant the twin"),
    (("ruff check qro controls tools tests", "ruff check qro controls tools tests --ignore=ALL"), "no option"),
    (("ruff check qro controls tools tests", "ruff check --isolated qro controls tools tests"), "no option"),
    (("ruff check qro controls tools tests", "ruff check qro controls tools tests tests"), "each once"),
    (("ruff check qro controls tools tests", "ruff check -q qro controls tools tests"), "no option")],
    ids=["MUST_SAY emptied", "MUST_SAY a letter", "MUST_SAY no name", "MUST_SAY another name", "-k added",
         "--deselect added", "the lint cut to the package", "the lint run as no program", "the twin made the control",
         "ruff told to ignore all", "ruff's option first", "a directory twice", "a short option"])
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
    for d in sorted(p for p in (root / "tests").iterdir() if p.is_dir() and re.fullmatch(r"p[0-9]+[a-z]*", p.name)):
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
                "tests/p1/deep/helpers.py", "tests/format/test_steps.py", "tests/p2crates/test_crates.py",
                "tests/p2crates/test_p2crates_ok.py"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("", encoding="utf-8")
    assert misnamed(tmp_path) == ["tests/p1/__init__.py", "tests/p1/deep/helpers.py", "tests/p1/helpers.py",
                                  "tests/p1/test_steps.py", "tests/p2/test_p1_steps.py", "tests/p2crates/test_crates.py"]
