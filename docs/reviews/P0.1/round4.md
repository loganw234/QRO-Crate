# P0.1 verifier, round 4

Labels: READ (in a file), MEASURED (I ran it; the script, log or command is named) or BELIEVED (my inference).

`CHECK` means `<scratch>\verifier-P01-r4\check\`. Paths are relative to `CHECK` unless they start `frozen\`.

I edited nothing in `frozen\` or in the real repository. I opened no `.quantum-film`, `.atlas` or credential file. I contacted no one, pushed nothing, and saw no key, token, CRN or job id.

## 1. Verdict: READY

By this round's bar I found no blocking defect:
- No shipped code gives a wrong acceptance or refusal, a crash or a wrong exit code on an input an accident makes.
- Round 3's fixes (G1, G2, G3, C1 and note 1) hold.
- I found no regression from bb90d1d.
- ParcelRound's rule (READ, `frozen\ParcelRound-METHOD-origin-main.md` section 6) is that only a regression or a wrong answer sends work back. I found neither.

Two gate gaps sit near the line (N1 and N2). I put them below it for three reasons:
- Round 3 classed the same family as a note (its note 4), and the lead decided on it with a stated reason.
- No shipped code is wrong. The cost of each fault is one vacuous or missing test, which the next parcel's verifier finds by mutation.
- The fix for N1 is two lines of configuration, measured below.

If the lead reads the bar the other way, N1 is the one to take.

## 2. Blocking defects

None.

## 3. What I checked, and what held

**Freeze (MEASURED, `sha256sum -c` in `frozen\tree`, at the start and the end).**
- 246 files OK. The file list equals SHA256SUMS. SHA256SUMS.txt begins `dcd0ede6a68e4944`. `frozen\` holds no `__pycache__`.
- The real repository's 246 files (`git ls-files -co --exclude-standard`) are byte-identical to the packet, at the start and the end.

**Runner (MEASURED, `logs\run_base_full.log`).**
- In a `git init` copy (`base\`, one commit), `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` gave passed 17, failed 0, skipped 3 (p1, p2, p4, by name). It took 99.9 s.
- Every number in the ledger's last entry reproduces:
  - docs 123, tool-tests 88, vocab-tests 8, format 662, custody 23, control-tests 29 (933 tests);
  - controls-run 9 of 9 with 21 pending; study-plants 68 refused and 6 accepted;
  - privacy 246 files and 1 commit message; privacy-controls 37 of 37; instruments 5 of 5;
  - check-docs 10, 28 and 35; twin `ff3fe486…`; negative control `raw-digest at data/raw.counts.json`.
- The quick budget took 47 s, twice, on an idle host. CLAUDE.md says ~45.
- Python 3.13.5 (MEASURED, `logs\py313_tests.log`): all 933 tests pass in the six directories, with pytest 9.1.1 taken from Miniconda's site-packages on PYTHONPATH.
  - `controls.run`, both `controls.plant` modes, `gen_vocabulary --check`, `check_docs`, `check_privacy` (plain and `--control`), `check_study` and `check_instruments` give the same results.
  - The twin's digest is unchanged. Earlier rounds ran 3.12 only.

**Round 3's fixes.**
- **G1 holds** (MEASURED, `scripts\g1_matrix.py`, `logs\g1_matrix.log`).
  - A failing test below each of 25 directory names, at two depths, under `tests/custody`: 48 of 50 placements fail the stage.
  - The names include build, dist, venv, node_modules, CVS, _darcs, `{arch}`, `*.egg`, dot-directories, `.git`, `.tox`, `.venv`, env and site-packages.
  - The two placements that pass are below `__pycache__`, which pytest never enters. The registry reports a test file there.
  - Round 3's 41-row stage matrix on this tree (`logs\b_stage.log`) differs from round 3's log only in the G1 rows (now fail) and the G3 rows (now refused). The environment rows are unchanged.
- **G2 holds** (MEASURED, `scripts\g2_colour.sh`, `logs\g2_colour.log`).
  - The quick budget gives passed 14, failed 0 under each of: FORCE_COLOR=1; PY_COLORS=1; both; NO_COLOR=1 with FORCE_COLOR=1; PYTEST_ADDOPTS=--color=yes; TERM=xterm-256color with FORCE_COLOR=3; CLICOLOR_FORCE=1.
- **G3 holds for its accidents.**
  - It refuses a `pytest_plugins` line after a docstring (injection I29, `logs\inject.log`).
  - It also refuses the shapes in round 3's matrix.
  - What it does not see is in N6.
- **C1 holds** (MEASURED).
  - Round 3's `g_hostilestr.py` (`logs\g_hostilestr.log`): six hostile `__str__` variants at three places (module import, step, count rule) all exit 3.
  - Round 3's `a_loader.py` (`logs\a_loader.log`): 74 module scenarios, each through `check --fixtures`, `check`, `controls.run` and both `controls.plant` modes. The command-line and plant columns are unchanged from round 3 except the hostile-text rows, now exit 3.
  - `controls.run` (note 1) answers 56 of the 74 with exit 3 and one line.
    - Of the others, 16 are the benign cases.
    - One is a no-op checker correctly judged WRONG, exit 1.
    - One is the non-ASCII message, N3.
- **The lead's seven round-4 mutants** (`p01\m_p01_r4.py`, via `hm.py`, `mut\logs\lead_r4.log`): 7 of 7 killed.
  - Its earlier sets on this tree: r1 13 of 13; r3 25 of 26, the survivor being the command line's order of `fixture.register()` and `load()`.
  - r2: 25 killed, 2 survived, 5 not applicable because their text has since moved. The survivors are the plants-merge sort and the same order mutant.
- **Round 3's other checks re-run and unchanged:**
  - R2-2, 26 cases (`logs\c_docsgate.log`).
  - 17 hostile git environments, each `88 passed` (`logs\d_gitenv.log`).
  - Privacy bounds, 54 cases, 0 mismatches (`logs\e_privbounds.log`).
  - Tests pytest drops (`logs\f_uncollectable.log`).
- **Round 3's notes 5 and 6 are closed in the code** (MEASURED, `logs\h_registry_reading.log`): a guard naming the wrong directory is caught with a comment or a blank line between it and its stage.

**P0.1 as a whole against bb90d1d.**
- Command line (MEASURED, round 2's `cli_diff.py`): 1,189 argument lists over four crates, a file, an empty directory and a missing path. The round 3 tree against this one: 0 differ in exit code, stdout or stderr. bb90d1d against this tree: also 0 differ.
- Privacy gate on ordinary code (MEASURED, `scripts\priv_fp.py`): 3,421 `.py` files of numpy, scipy, sympy and networkx gave 78 findings:
  - 11 windows-home (build paths);
  - 19 posix-home (docstring examples);
  - 48 address (authors' emails).
  - All are shapes the gate means to refuse. I saw no matrix-multiply false positive.
- A `git worktree` (`.git` a file) runs the privacy gate, its controls, check-docs and the stages for twin and the controls (MEASURED, `wt_p1\`, since removed).

**The seams used as parcels would use them.**
- I wrote stand-ins for P1, P2 and P4 (`overlays\`, assembled by `scripts\assemble.py`), richer than round 2's:
  - helper modules under `qro/`;
  - a raw form, a generator and a count rule;
  - plants that use `controls.registry`'s helpers;
  - tests with data files, a prefixed helper module, parametrised cases, and in-process and process runs of the command line;
  - an example crate under `profile/`.
- The full runner passed on each alone (P1 18 stages, P2 18, P4 18) and on the three merged: passed 20, failed 0, skipped 0 (`logs\run_*.log`). Not one file of the lead's was edited.
  - My first P2 plant was wrong (`count-unpaid`). `control-tests` and `controls-run` named it at once.
- The lead's own `sim_parallel.py`, run on this tree, gave passed 19, skipped 1 (p4).
- One pytest session over all `tests/` with the stand-ins loaded gave 955 passed in the default order, the reverse, and three seeded shuffles (`logs\session_orders.log`).
- Thirty accident injections on the merged tree (`scripts\inject.py`, `logs\inject.log`), each followed by the quick budget. 25 were refused by the stage that should refuse them:
  - a failing test, an empty `parametrize`, `pytest.skip`, `xfail`;
  - a test below `tests/p2/build/`; a `pytest_plugins` line;
  - a `conftest.py`, an `__init__.py` in `tests/p1`, a shared test basename;
  - `tests/p3/` before its stage; a top-level directory holding Python;
  - a tool with no stage; an unindexed document; a docstring naming a missing path;
  - a home path; a key-shaped value; a duplicate test name;
  - `PLANT` for `PLANTS`; a stray `print` at import in a registration module and in a plants module;
  - a step of the wrong parcel; a step raising `KeyError`; an import that fails;
  - a count rule that refuses everything; a step that pops what it reads.
- Five passed silently: I01, I02, I03, I07 and I08, in N1 and N2.

**Mutation (scope 4).** I generated operators D and E over every region P0.1 changed: `checker.py` 56 to 183, `__main__.py`, `reader.py` 155 to 195, `spelling.time`, `controls/run.py`, `registry.py`, `plant.py`, `check_docs.guarded`, `gen_vocabulary.problems`.
- 441 mutants (D 224, E 217): 415 killed, 26 survived (`mut\logs\D_changed_*.log`, `E_changed_*.log`).
- The 26 survivors are in N7. None shows a wrong answer from the shipped code.

## 4. Notes (below the bar)

**N1. [other: gate reach; the one I would take first]** Two pytest warnings that mean a test is not doing what it says pass the stage as `N passed, 1 warning`.
- A `Test` class with an `__init__` collects none of its tests. I01 holds a failing test in one.
- A test that returns a comparison instead of asserting it passes. I08 does this.
- This is round 3's note 4, which the lead declined because a stage that refused every warning would fail on a library's.
- A narrow pin has no such cost. MEASURED (`work\ret`, `work\fixw`):
  - `filterwarnings = ["error::pytest.PytestCollectionWarning", "error::pytest.PytestReturnNotNoneWarning"]` in pyproject.toml makes the stage fail both cases (rc 1).
  - Every stage's tests also pass under `-W error` today, in all six directories (`work\a`). So even all warnings as errors would cost nothing now.
  - The registry's `PYTEST_OPTIONS` pin would need the same change. That is the only `docs` failure the extra key causes.

**N2. [other: gate reach, and a sentence that claims more than is true]** The registry reads `tests/` only.
- A `test_*.py` in `qro/`, `controls/` or `tools/` is run by no stage, and nothing says so. I03 puts a failing one in `qro/` and the runner passes.
- The registry's first docstring sentence ("Every test file is run by some stage") and CLAUDE.md's "fails a test file … that no stage runs" are wider than that.
- Also unrun and unflagged:
  - tests in a module named like a helper (`p2_hidden.py`, which the prefix rule allows; I02);
  - a function named `check_*` (I07). This is pytest's naming, and I list it only for completeness.

**N3. [other: `controls.run` prints raw text; its "exit 3 and one line" is wider than true]** The command line writes printable ASCII. `controls.run` prints the text as it is.
- A message with a line feed makes two lines. `a_loader.log`, scenario "message with a newline and a REFUSED line", shows `[2 lines]`.
- A character the stdout codec cannot encode breaks it when stdout is redirected on Windows without `PYTHONIOENCODING`. I MEASURED the two cases:
  - a module raising `RuntimeError("shots must be ≥ 1")`: exit 1 and a `UnicodeEncodeError` traceback, not exit 3 (`work\uni`);
  - a good run whose refusal detail holds `≥`: exit 3 "the controls' run itself failed", though all controls came out right (`work\uni2`).
- The runner sets `PYTHONIOENCODING=utf-8`, so the runner is unaffected. The same two cases give exit 3 and a clean pass under it (MEASURED).
- A direct run by a person or agent through a pipe is affected.
- Fix: pass the text through `qro.__main__.escape`. Not new: the print is P0's and `run()` only re-labels it.

**N4. [contrived]** A plants module that exits 0 at import is answered unevenly (MEASURED, `work\exit0`):
- `controls.run` exit 3 (the fix).
- `controls.plant twin` exit 0 with no output.
- `controls.plant shot-moved` exit 0.
- `gen_vocabulary.py --check` exit 0 with no output.
- The runner still fails, through the negative control, controls-run and control-tests (injection I16). But the `twin` and `vocabulary` stages pass without running.

**N5. [other: `.gitignore`]** It names no `.venv/`, `venv/` or `*.egg-info/`.
- A repo-local virtual environment, such as a parcel installing pytest or ruff in its worktree, is untracked and not ignored.
- The privacy stage then reads it and fails on a third-party author's address (MEASURED, `work\venvtest`).
- The gate is right by its own definition (git would commit those files). The omission is the lead's.

**N6. [deliberate]** The G3 scan is line-based. These pass and hide a test (MEASURED, `work\bom`):
- `x = pytest_plugins = [...]`;
- a UTF-8 byte-order mark before a first-line `pytest_plugins` (PowerShell 5.1's `Set-Content -Encoding utf8` writes one).
- Also BELIEVED, not measured: `globals()["pytest_plugins"]`, and a star-import of the name from a helper outside the stage directory.
- The registry already states the class as a limit.

**N7. [test reach]** The 26 mutation survivors.
- 17 are equivalent: `args[0]` to `args[-1]` where the list holds one item; `casefold` to `lower` on ASCII; `str()` dropped where the command line takes a `Path`; `lstrip` to `strip`; `"P0"` to `"P0x"`; `set(found)` dropped (speed only); the `code != 3` constant at `__main__.py:81` moved to 2 or 4; the `name = "an exception"` fallback.
- 3 are the plants merge's `sorted`, equivalent on NTFS, as the lead knows.
- 3 are unasserted behaviour:
  - which missing file a custody misuse names (`__main__.py:106`);
  - the raise "descriptor first, then the root" (`reader.py:181`). Its work is done by later checks under another location, and step 9 refuses the same graph by another name.
  - the "; section 11 says …" suffix of a WRONG line (`controls/run.py:55`).
- 3 more of the E set are killed only by the twin or negative-control stage, not by pytest (`controls/plant.py:20`, `:24`, `:26`).

**N8. [prose]**
- CLAUDE.md does not tell a parcel that a fixture shaped like a key, CRN or home path must be built at run time, as the gate's own PLANTS are. I27 shows a key-shaped data file fails the privacy stage (MEASURED).
- The two sentences to restate are in N2 and N3.

## 5. What I did not do, and my slips

**Not done.**
- No macOS, no Linux, no WSL (its Python is 3.10, below the floor), no Python 3.14.
- Python 3.13.5 ran the six pytest directories and the tools by hand, not the runner. Ruff is not installed for it.
- I made no symbolic links and tested no permission-denied case.
- I did not re-run rounds 1 to 3's large randomised matrices: the 239,467-graph oracle, the 4,500 on-disk crates, the 200,000 datetimes, the privacy fuzz.
- I did not review P1 to P5, the study, or P0.1's prose beyond the claims I tested.
- I did not scan moth-quantum with the privacy patterns. The false-positive scan used numpy, scipy, sympy and networkx.
- I applied no fix. The candidate fix for N1 was measured in a scratch copy only (`work\fixw`).

**Slips.**
- Scripts run with `python -I` ignore `PYTHONDONTWRITEBYTECODE`. One wrote a `__pycache__` into `check\tree\tools`, my copy. I removed it and re-ran the sums on the copy: all OK. `frozen\` was never run in and holds none.
- I wrote a few small files to the system temp directory, through Git Bash's `/tmp` and by absolute path, and removed them in the same commands: output captures and three file lists. pytest's own `pytest-of-logan` directories remain there, as in earlier rounds.
- In the real repository I ran only `git log`, `git archive`, `git ls-files` and, once, `git status --porcelain`. `status` may refresh the index's stat cache; no content changed.
- My injection I17 was first confounded by a lint error I introduced. I re-ran it clean (`work\i17`): `format` and `control-tests` fail.
- The 30 injections ran while the mutation shards were finishing, so their times mean nothing. The clean times are 47 s twice (quick) and 99.9 s (full).
- The harness moved one long wait to the background. I polled the logs.

Key files: `CHECK\logs\` (all logs), `CHECK\scripts\` (`g1_matrix.py`, `g2_colour.sh`, `assemble.py`, `inject.py`, `priv_fp.py`, `crlf_scan.py`), `CHECK\overlays\` (the stand-in parcels), `CHECK\mut\` (mutant sets and logs).
