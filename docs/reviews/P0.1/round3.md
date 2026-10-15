# P0.1 verifier, round 3

Labels: READ (in a file), MEASURED (I ran it; the script, log or command is named) or BELIEVED (my inference). Paths are relative to `SCRATCH\verifier-P01-r3\check\` unless they start `frozen\`. I edited nothing in `frozen\` or the real repository. I opened no `.quantum-film`, `.atlas` or credential file, contacted no one, and saw no key, token, CRN or job id.

**Report file.** I did not write `report.md`. My instructions here say to return findings as the final message and not to write report files. This message is the record.

## 1. Verdict: NOT READY

This is send-back 3 of 3, so the full bar applies. I found three gate defects, one contrived code defect and one prose defect. The fixes for G1, G2, C1 and P1 are each a few lines. I measured the fixes for G1, G2 and C1 in scratch and applied nothing.

| id | what | kind |
|---|---|---|
| G1 | A test file under a directory pytest skips by default (`build`, `dist`, `venv`, `node_modules`, `CVS`, `_darcs`, `{arch}`, `*.egg`, `.*`) is run by no stage. The registry counts it as run, and the run passes. | gate, reachable by accident |
| G2 | `FORCE_COLOR=1` or `PY_COLORS=1` still fails the `docs` stage on a good tree. Round 2's note 4.3.6 was marked taken. | gate |
| G3 | A test module's `pytest_plugins` line plus a plugin module takes tests out of their stage, the registry's own among them, and the run passes. | gate, deliberate, same class as R2-1 |
| C1 | An exception whose `__str__` raises `Refused` or `PermissionError` escapes `load()`'s conversion as exit 1 or 2. | code, contrived |
| P1 | The README says P0.1's verifier is "going to its second" round. Round 2 has happened. | prose |

- **About what the code does:** only C1, and it needs a hostile exception class. My verdict does not rest on it.
- **About gates:** G1, G2 and G3.
- **About prose or test reach where the code is right:** P1 and section 4.

**What held**, in short (details in section 3):
- R2-1 is closed for `conftest.py` and for every pytest configuration file I tried.
- R2-2 holds in all 21 cases.
- R2-3 holds for every ordinary way a parcel module can fail to load.
- The lead's numbers reproduce, and the command line is unchanged from round 2's tree.

## 2. Defects

### G1. [gate] A test directory pytest skips by default is "run" by the registry and by no stage

**Claim (READ).** The registry's docstring opens "Every test file is run by some stage of the runner". `orphans()` counts any `test_*.py` or `*_test.py` below a staged directory as run. CLAUDE.md sends parcels to that docstring for "what that reading cannot see". Neither it nor any other file in the tree mentions `norecursedirs` (MEASURED: `grep -rIn "norecurse" frozen\tree`, no hit).

**Fault.** pytest 9.1.1's default `norecursedirs` is `*.egg .* _darcs build CVS dist node_modules venv {arch}` (READ, `_pytest/main.py`). The pinned options do not override it.
- **At stage level** (MEASURED, `scripts\b_stage.py`, `logs\b_stage.log`):
  - I put `def test_zz_fails(): assert False` under `tests/format/<dir>/` for each of nine directory names.
  - Each time the format stage said `651 passed` and the docs stage said `113 passed`.
- **End to end** (MEASURED, `exp\all3`, which is round 2's three stand-in parcels on this tree):
  - The failing file at `tests/p1/test_p1_zz.py` fails the p1 stage (`1 failed, 5 passed`).
  - The same file at `tests/p1/build/test_p1_zz.py` gives p1 `5 passed` and docs `113 passed`.
  - check-docs and lint pass too. The runner ends `== PASSED`.
- With no other tests in the stage, the stage exits 5 ("no tests ran") and fails closed (`tests/p1` row of `b_stage.log`). The hole is silent only when the stage has other tests.

**Exposure (BELIEVED).** A parcel putting tests under a directory with one of those names is unlikely but not impossible, and when it happens nothing says so.

**Candidate fix (MEASURED in scratch, `exp\fixA`, `scripts\i_fixes.py`, `logs\i_fixes.log`).** Add `norecursedirs = []` to pyproject.toml's pytest options and to the registry's `PYTEST_OPTIONS`.
- Docs still passes 113 and format 651.
- Six of the nine placements, re-run, now fail the format stage.
- The old pyproject now fails the registry's pin.
- Alternative: have `orphans()` flag such files.

### G2. [gate] The colour fix reached the stage script and not the registry's own test

**Claim (READ).** The stage script's header and the ledger (4.3.6) say `--color=no` stops `FORCE_COLOR` or `PY_COLORS` making a passing run fail.

**Fault (MEASURED).**
- `FORCE_COLOR=1 bash verify/run.sh --budget quick` ends `passed 13, failed 1, skipped 3` and `== FAILED`. The failing stage is `docs`. `PY_COLORS=1` gives the same (`logs\run_quick_FORCE_COLOR=1.log`, `logs\run_quick_PY_COLORS=1.log`).
- `FORCE_COLOR=1 bash verify/pytest-stage.sh tests/docs` gives `3 failed, 110 passed`.
- The three failures are the three cases of `test_the_stage_script_reads_no_configuration_file_but_the_roots_and_no_conftest`.
- That test runs a nested `python -m pytest -q -p no:cacheprovider tests/x` with no `--color=no`, and asserts `.startswith("1 passed")` on a coloured line.
- The lead's colour test sets the variables only for the inner stage-script run, so it passes.

**Candidate fix (MEASURED in scratch, `exp\fixB`).** Add `--color=no` to the nested call. Docs then gives `113 passed` under `FORCE_COLOR`, `PY_COLORS` and both.

### G3. [gate, deliberate] `pytest_plugins` hides tests, as a `conftest.py` did in R2-1

**Fault (MEASURED, `scripts\b_stage.py`; through the runner in `base`, `logs\run_quick_pytest_plugins.log`).**
- Two files under `tests/docs/`:
  - `test_zz_plug.py` holds `pytest_plugins = ['zzplug']` and one passing test.
  - `zzplug.py` holds a `pytest_collection_modifyitems` hook that drops `test_stage_registry`.
- `bash verify/run.sh --budget quick` ends `== PASSED, with 3 skipped by name above`, and lint and check-docs pass.
- The docs stage ran 21 tests instead of 113. The registry removed itself from its own stage.
- With the plugin module under `tests/format/` the format stage ran 321 instead of 651.

**Why.** `--noconftest` blocks `conftest.py` only. pytest honours `pytest_plugins` in an ordinary test module, which any file under `tests/` can write.

**Scope.** This needs two deliberate files, as R2-1 needed one. Any file in `tests/` is code that pytest runs, so pinning cannot close the class.
- **Closing it:** a scan outside pytest for `pytest_plugins` and `def pytest_` under `tests/`, in the stage script or `check_docs.py`.
- **Or:** state it as a limit in the registry's docstring.

### C1. [code, contrived] `load()`'s conversion formats the exception's text unguarded

**Claim (READ).** `load()`'s docstring says any `Exception` a module raises is a `RegistrationError`, "a Refused or a PermissionError among them", and the command line answers it as exit 3. CLAUDE.md says a crash is never a verdict.

**Fault (MEASURED, `scripts\g_hostilestr.py`, `logs\g_hostilestr.log`).**
- A module raising `E()`, where `E.__str__` raises `Refused('commitment','x','y')`, gives exit 1 and `REFUSED commitment at x: y`. That is a verdict on a crate never read.
- With `__str__` raising `PermissionError` it gives exit 2.
- With `__str__` raising `ValueError`, or returning a non-string, it gives exit 3.
- The cause is `f"... {type(x).__name__}: {x}"` inside the `except Exception` clause.

**Reach.** Only a hostile exception class does this. The same unguarded formatting is in `main()`'s catch-all (P0 code): a step or count rule raising such an exception ends in a traceback and exit 1 (same log, "in a step" rows).

**Candidate fix (MEASURED in scratch, `exp\fixD`).** Build the text inside `try/except BaseException`. All six hostile variants then give exit 3 at import, and `tests/format/test_load.py` still passes (24 tests).

### P1. [prose] The README's status is stale

`README.md` lines 25–26 say P0.1's verifier "found three defects, fixed and going to its second (docs/VALIDATION.md)". The ledger's last entry records the second round (NOT READY, R2-1 to R2-3), and the third is this one. README.md is byte-identical in the round 2 and round 3 trees (`diff -rq`), so it was never updated. Other claims I checked hold (section 3).

## 3. What held

- **Freeze (MEASURED, `sha256sum -c`).**
  - 245 files OK, and the file list equals SHA256SUMS.
  - SHA256SUMS.txt begins `e25fade977f27b17`.
  - Same result at the start and the end.
- **Runner (MEASURED, `logs\run_base_full.log`).**
  - A `git init` copy with one commit, `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh`, gave `passed 17, failed 0, skipped 3` (p1, p2, p4 by name).
  - Every number equals the ledger's:
    - docs 113, tool-tests 84, vocab-tests 8, format 651, custody 23, control-tests 27: 906 tests;
    - controls-run 9 of 9 with 21 pending, study-plants 68 and 6, privacy 245 files and 1 commit message, privacy-controls 37 of 37, instruments 5 of 5;
    - check-docs 10, 27 and 35;
    - twin `ff3fe486…`, and the negative control's `raw-digest at data/raw.counts.json`.
  - Timing: the quick budget took 41 s and 43 s, the full run 94.7 s. CLAUDE.md says about 45 and 95.
- **Parcels at once (MEASURED, `logs\run_all3_full.log`).**
  - Round 2's stand-in p1, p2 and p4 on this tree gave `passed 20, failed 0, skipped 0`.
  - One pytest session over `tests/` gave 906 passed, and 917 with the stand-ins.
  - check-docs with `tests/p1` present gave no false report.
  - `exp\sp ace\QRO Crate café` (space and non-ASCII in the path) passed the quick budget.
- **Command line unchanged (MEASURED, round 2's `cli_diff.py` on `exp\cli_r2` and `exp\cli_r3`).** 1,189 argument lists, 0 differ in exit code, stdout or stderr.
- **R2-1.**
  - A `conftest.py` under `tests/`, round 2's plant, now leaves format at 651. Docs fails with the registry's report.
  - A stray `sitecustomize.py` or `usercustomize.py` at the root is flagged by the lint-shape test.
  - A `pyproject.toml` under `tests/format` and a root `tox.ini` are flagged.
  - Environment: `PYTEST_ADDOPTS`, `PYTEST_PLUGINS`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=0`, `NO_COLOR`, `COLUMNS`, `TERM=dumb`, `PYTHONWARNINGS=error`, `PYTHONOPTIMIZE`, `PYTHONSAFEPATH`, `PYTHONHASHSEED`, `PYTHONUTF8=0`, `PYTHONIOENCODING=ascii`, `PYTEST_DEBUG`, `LANG=C` and a decoy `qro/` on `PYTHONPATH` changed nothing (`logs\b_stage.log`).
  - pytest 9.1.1 reads these variables (READ, a scan of `_pytest`): `PYTEST_ADDOPTS`, `PYTEST_PLUGINS`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD`, `PYTEST_DEBUG`, `PYTEST_DEBUG_TEMPROOT`, `PYTEST_THEME(_MODE)`, `PYTEST_VERSION`, `PY_COLORS`, `NO_COLOR`, `FORCE_COLOR`, `TERM`, `TOX_ENV_DIR`, `PY_IGNORE_IMPORTMISMATCH`. The script handles the first three and the colour ones. The rest do not take a test out of a stage.
  - The script refuses `pytest.exit(returncode=0)` from a test, `os._exit(0)` and `xfail(run=False)` (`scripts\f_uncollectable.py`).
  - The header's claim "unchanged below this line but for three options" matches moth-quantum at 3a73823 (MEASURED: `git show 3a73823:verify/pytest-stage.sh` against the tree's, diffed).
  - The list of pytest configuration names equals pytest's `locate_config` (READ), so skipping note 4.1.7 is sound.
- **R2-2 (MEASURED, `scripts\c_docsgate.py`, 21 cases).**
  - A guard whose directory is absent exempts the guarded path and the paths below it, and nothing else.
  - A sibling like `tests/p1x/`, `tests/p10/` or `tests/p1.md` is reported.
  - Once `tests/p1` exists, `tests/p1/ghost.py` and `tests/p1/nowhere/x.json` are reported.
  - p2 and p4 stay exempt while absent. A guarded path existing as a file ends the exemption.
  - Minor: `tests/p2/../format/ghost.py` stays exempt under an absent guard (contrived).
- **R2-3 and the loader (MEASURED, `scripts\a_loader.py`, `logs\a_loader.log`).**
  - 74 module scenarios, each run as `check --fixtures`, `check`, `controls.run`, `controls.plant twin` and `controls.plant shot-moved`.
  - 54 give exit 3 on the command line and both plant commands. The exit-3 line is on stderr.
  - The 54 cover:
    - `Refused`, `PermissionError`, `OSError`, `RuntimeError`, `ImportError`, a syntax error and an indentation error;
    - `SystemExit(0)`, `SystemExit(1)` and `SystemExit('text')`, `KeyboardInterrupt`, `GeneratorExit` and `BaseException` subclasses;
    - `RecursionError`, `MemoryError`, a 1 MB message and non-ASCII or newline messages, all escaped to one line;
    - a failing `items()` or `__getattr__`, wrong-kind declarations, a P3 or P5 module, and a package that raises;
    - a step owned by another parcel, a clashing name, and a fixture name (`qro-fixture`, `qro-fixture-x`, `qro-fixtureX`) with and without `--fixtures`;
    - registries changed directly: `STEPS[4]`, `RAW_FORMS`, `GENERATORS`, `COUNTS.append`, `STEPS.update`, a rebind to a different dict, a call to `fixture.register()` without `--fixtures`, a deleted fixture entry, and another parcel's module doing it.
  - Accepted by design: a set-then-unset or an equal rebind of `STEPS`, `qro-fixtur`, capitals or a leading space in a name, and `fixture.register()` under `--fixtures`.
  - The 20 others are the benign cases plus C1, and `COUNTS` or a step given as a string, which fails at check time with exit 3.
- **4.1.8 (MEASURED, `scripts\d_gitenv.py`).** `tests/tools` gave 84 passed under 16 hostile git environments. These included `GIT_DIR`, `GIT_INDEX_FILE`, `GIT_CONFIG_COUNT` signing, a hostile `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `GIT_CONFIG_PARAMETERS` and a hostile `HOME`. The decoy repository's log and index never changed.
- **4.3.5 (MEASURED, `exp\j_dup`).** Two plants modules planting one name gave `gen_vocabulary --check` and `--write` exit 2 with the message, and `--write` wrote nothing.
- **Privacy gate prose (MEASURED, `scripts\e_privbounds.py`).**
  - The docstring's bounds hold for all nine named alternatives at all six places: 54 cases, 0 mismatches.
  - A real address glued to a reserved one by `- . _ % + 5` passes, and every other separator finds it.
  - The escaped pattern behaves the same for all six glue characters.
  - The comment's "found as before" is provable (READ): the old pattern's leftmost match never has an address character before it.
- **Other prose checks.**
  - CLAUDE.md's line-ending claim: the 8 CRLF files are exactly the 5 instrument outputs and 3 records logs.
  - The reviews index's SHA-256 prefixes match round1.md (`1820c1a9`) and round2.md (`dbe9d5ee`).

## 4. Notes (below the bar)

**Code**
1. **`controls.run` and a failed load.**
   - It answers any load failure with a traceback and exit 1, not exit 3.
   - FORMAT.md item 20's "exit 3" concerns the command line, so this is not a false claim.
   - A `SystemExit(0)` raised by a parcel's module (or step) ends the run with exit 0 and no output, so the `controls-run` stage passes. The `twin` stage fails in that case (MEASURED, `a_loader.log`, "sys.exit(0)" row, entry C).
2. **A module directory without `__init__.py`.** `qro/register_p1/` loads as an empty namespace package: nothing registered, no error. It fails safe, because crates are then refused `step-unbuilt`.
3. **`PYTHONDEVMODE=1`.** It fails `test_the_process_with_a_closed_descriptor_exits_3[both closed]` (rc 1, not 3). I did not pursue it; it is the user's mode.
4. **Warnings pass.**
   - A test class with an `__init__` is dropped with a `PytestCollectionWarning` and the stage reports `1 passed, 1 warning` (`logs\f_uncollectable.log`).
   - `__test__ = False` and non-`test` names drop silently.
   - This comes from moth-quantum's script, not this round.

**Gate reading limits (MEASURED)**
5. **A comment or blank line between a `need_file` guard and its stage blinds `guard_problems`** (`logs\h_registry_reading.log`, cases i and i-b). p1's guard naming `tests/p2` then passes. The function says "directly before" and its plants are adjacent. The `== 3` count counts guards, not pairs.
6. **A stage written on one line is read by no registry function.**
   - `stage zzmask "a masked stage" -- bash -c 'false || true'`, added to `BUDGET_QUICK`, passes docs (113) and the runner runs it `ok` (`scripts\h2_oneline.py`, `exp\k_oneline`).
   - This contradicts the docstring's "no `||` … can mask its exit". It is pre-existing (P0, round 3, R3-3a).
   - A test that the stage-name count equals the command-line count would close it.
7. **The registry pins listed lines of the stage script, not the script.** After the `unset` line, `export PYTEST_ADDOPTS=--ignore=tests/format/test_hostile.py` passes docs (113), and the format stage then runs 320 (`exp\l_export`). This is a deliberate edit.
8. **CLAUDE.md does not tell a parcel** that a `conftest.py` is not read, that `pytest_plugins` hides tests, or that directory names like `build` are skipped. The registry flags a `conftest.py` with a clear message.

**Test reach, from mutation (section 5)**
9. The "changes the registries itself" refusal is planted for `STEPS` only. Dropping `RAW_FORMS`, `COUNTS` or `GENERATORS` from the snapshot, or holding them by reference, passes every test. The shipped code is right (`a_loader.log`).
10. Nothing pins a near-miss name's acceptance (`qro-` or `qro-fix` as the prefix survive), the `from x` cause chain, or a `(new)` marker that must follow its own path (accepting it anywhere on the line survives).
11. `controls.run`'s pending-row lines, its `ok`/`WRONG` labels, its location text and its `__main__` guard are unasserted. With a dead guard the stage exits 0 and prints nothing.
12. `check_docs.py`'s printed output and two `gen_vocabulary` sanity messages (lines 111 and 113) have no test. Both are pre-existing.

**Prose**
13. Ledger 4.1.3 says a second address glued by each character is "held not found, for both patterns". The escaped pattern's glue test has 3 of the 6 characters. The lookbehind-structure test pins the rest, and the code is right.
14. The registry docstring's stated limits omit G1, G3, note 5 and note 6.

## 5. Mutation

I used round 5's `hmp.py` (operators D and E, byte offsets) and round 3's `hm.py` (hand mutants), each mutant against the six test directories the runner runs. A survivor then ran the twin, negative control, `gen_vocabulary --check`, controls-run, check-docs and ruff. Logs are in `mut\logs\`.

| set | mutants | killed | survived |
|---|---|---|---|
| D over the functions this round touched (`checker.py` 42–121, `check_docs.py` 77–110, `gen_vocabulary.py` 107–122) | 52 | 47 | 5 |
| E, same ranges | 51 | 46 | 5 |
| my hand mutants 1 (`m_r3.py`): loader, docs gate, stage script, registry pins | 47 | 29 | 18 |
| my hand mutants 2 (`m_r3b.py`): notes 4.1.4 to 4.1.8, privacy bounds | 25 | 24 | 1 |
| the lead's `m_p01_r3.py`, re-run | 26 | 25 | 1 |
| D on `controls/run.py` and `controls/plant.py` | 51 | 50 | 1 |
| E, same files | 46 | 36 | 10 |
| total | 298 | 257 | 41 |

The lead's tally reproduces: 25 of 26 killed, and the survivor is the command line's order of `fixture.register()` and `load()`.

**Equivalent survivors (19)**
- `"P0"` to `"P0x"` in `load()`. No `qro/register_p0.py` exists, and P0 declares nothing.
- `.lstrip` to `.strip` after a path in `missing_paths`. `startswith("(new)")` is unaffected by right-stripping.
- Fixture prefix tested on `key` rather than `str(key)`. Step keys are integers and names are strings.
- Fixture check after the clash check. Only the message differs, and both are `RegistrationError`.
- `guarded` with `.is_dir()`. Guards are directories.
- The guard regex allowing leading spaces. The runner's guards sit at column 0.
- Stage script mutants:
  - rc check loosened. The summary checks refuse every non-zero run I could make (`f_uncollectable.log`).
  - Summary read from the last two lines. This only refuses more.
  - `set -u` removed, and `pipefail` removed. No variable is unset and no pipeline's status is used.
- The registry's pytest-line filter changed to `startswith("e")`. Only `echo` lines begin so.
- `controls/plant.py`:
  - `argv[0]` to `argv[-1]` at four sites. The list has one item.
  - `str()` dropped at three sites. The command line accepts `Path` arguments.
- The lead's CLI-order mutant. No parcel may register a fixture name.

**Gaps (22)**
- Notes 9 and 10: 5 snapshot mutants (`RAW_FORMS`, `COUNTS` and `GENERATORS` ignored; `RAW_FORMS` and `GENERATORS` held by reference), the same for `COUNTS` by reference (E, `checker.py:73`), the two prefix mutants, the dropped cause, and the `(new)` anywhere mutant.
- `export PYTHONPATH=zz` added to the stage script. Harmless in itself, and it shows added lines are unpinned (note 7).
- Note 11: the pending-row print, the `ok`/`WRONG` labels (E, 1) and the location text (E, 1) in `controls/run.py`, and its `__main__` guard.
- Note 12: five survivors in `check_docs.py`'s printed output (D lines 106, 107, 108; E lines 107, 108) and two in `gen_vocabulary.py` (D lines 111, 113).

## 6. What I did not do, and my slips

**Not done**
- No macOS, Linux, Python 3.13 or later, or WSL. I ran Windows 11 with Git Bash, Python 3.12.9, pytest 9.1.1 and ruff 0.11.9.
- I made no symbolic links, and did not test a module file the user cannot read. I tested a module that raises `PermissionError`.
- I did not re-run round 2's whole 50-plant D1 matrix. I ran 34 plants in `b_stage.py`.
- I did not re-fuzz the privacy patterns (round 2 did) and mutated the gate only through the lead's 9 and my 4.
- I did not review P1 to P5 or the study.
- I applied no fix to the tree. The candidate fixes are in scratch only.

**Slips**
- I wrote three small files to the system temp directory through Git Bash's `/tmp` (`zz_fail.py`, `vr3_files.txt`, `vr3_sums.txt`) and removed them. pytest's own temp directories remain, as in earlier rounds.
- My first docs-gate script left a directory behind and crashed on its next case. I fixed the script and re-ran it.
- The harness reported my background launches "completed" when only the launcher shell had finished. `b_stage.py` also buffered its output, so I saw no progress until it ended. I polled the logs.
- Other work was running on this host, so my timings are noisy except the idle quick-budget runs above.
