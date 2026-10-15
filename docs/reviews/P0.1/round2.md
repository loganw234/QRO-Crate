The freeze held at the end too. The harness refused my write of the report to `SCRATCH\verifier-P01-r2\report.md` ("Subagents should return findings as text"), so this message is the record.

# P0.1 verifier, round 2

Labels: READ (in a file), MEASURED (I ran it; the script or command is named) or BELIEVED (my inference). My scripts, stand-ins, logs and mutant sets are in `SCRATCH\verifier-P01-r2\check\` (`scripts\`, `overlays\`, `mut\`, `logs\`, `exp\`). Paths below are relative to that directory. I edited nothing in `frozen\` and nothing in the real repository.

## 1. Verdict: NOT READY

This is send-back 2 of 3, so the full bar applies. I found three defects. Each needs a fault the lead did not plant, and each has a small fix that I measured in scratch and did not apply.

| id | what it is | about |
|---|---|---|
| R2-1 | D1 is closed to every accidental way I tried. A one-line `tests/conftest.py` can still take 410 tests out of the full run, the registry's own among them, and the run passes. | a gate (needs a deliberate file) |
| R2-2 | The docs gate's `need_file` exemption never ends. Once a parcel's directory exists, a document naming a missing path below it passes. | a gate |
| R2-3 | `checker.load()` does not turn a parcel module's failure to import into the exit-3 failure that its docstring, FORMAT.md items 16 and 20, and `qro/__main__.py` all say it is. `Refused` at import gives exit 1, and `PermissionError` gives exit 2. | code, and three false sentences |

Section 4 is below the bar: test reach where the shipped code is right, prose, and design observations.

Otherwise D1, D2 and D3 hold:
- The configuration-file half of D1 is closed for all seven names pytest 9.1.1 reads, in all three places I planted.
- D2 holds in every fresh-process order.
- D3 holds for one parcel, for three at once, and for a git merge of three branches with no edit to a file of the lead's (section 3.3).

## 2. Defects

### R2-1. [gate] A conftest.py can erase the registry that pins conftest.py

**Claim (READ).** The registry's module docstring says no `conftest.py` sits where a stage reads one. The ledger says D1's test holds "no conftest.py where a stage reads one, the root or under tests/".

**Fault (MEASURED, `exp\d1_selferase`, `logs\d1_selferase_full.log`).** One file, `tests/conftest.py`, holding one line:

```
collect_ignore_glob = ["*test_stage_registry.py", "*test_hostile.py"]
```

- `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` ends `passed 17, failed 0, skipped 3` and `== PASSED, with 3 skipped by name above`.
- The `docs` stage ran 18 tests where it runs 97, and `format` ran 312 where it runs 643. That is 410 tests out of the run, and every test that would have flagged the file is among them.
- The same conftest without the registry's name in it is flagged: the docs stage fails.

**Why.** The pin is a test, and it runs in the session the conftest filters. A conftest is loaded before collection, so it can remove the pin.

**What is closed (MEASURED, `scripts\d1_matrix.py`, `logs\d1_matrix.log`).** 50 plants, each run through `bash verify/pytest-stage.sh` on the format stage, the docs stage and the registry file.
- **Configuration files.** Each of `pytest.toml`, `.pytest.toml`, `pytest.ini`, `.pytest.ini`, `pyproject.toml`, `tox.ini` and `setup.cfg` was planted at the root, under `tests/` and under `tests/format/` (20 plants; the root `pyproject.toml` is the real one). In all 20 the format stage keeps its 643 tests, and the docs stage fails because the registry reports the file.
- **Conftests.** I planted two kinds, `collect_ignore_glob` and a `pytest_collection_modifyitems` hook, at 15 places each. 8 of the 30 take 331 tests out of the format stage.
  - The registry flags every placement pytest reads: the root, `tests/`, `tests/format/`, `tests/format/golden/`, `tests/format/sub/`, `tests/docs/` and `tests/tools/`.
  - Where pytest reads none (`qro/`, `controls/`, `tools/`, `docs/`, `.hidden/`), nothing is flagged and nothing changes.
  - `verify/`, `profile/` and `records/` are flagged by the lint-shape tests, not the configuration test (`exp\lintshape`).
- **Above the root.** A conftest and a `pytest.ini` in the directory above the root change nothing, with or without `-c` (`exp\pdir`: 643 both ways).
- **The `pyproject.toml` itself.** A `[tool.pytest]` table beside `ini_options` makes pytest exit 4 ("Cannot use both"). A native `[tool.pytest]` table in place of `ini_options` takes 331 tests out of the format stage and fails the docs stage with a bare `KeyError` at `test_stage_registry.py:217` (20 tests down).
- **The environment.** `PYTEST_ADDOPTS=--ignore=... bash verify/pytest-stage.sh tests/format` gives 643, because the script unsets it.
- **A directory junction under `tests/`.** A `conftest.py` behind one is found by the registry's `rglob` (3.12, Windows) and read by pytest (`exp\junct`). I could not make symbolic links (WinError 1314).

**Candidate fix (MEASURED in scratch, `exp\noconf`; not applied).** Put `--noconftest` in the stage script's pytest line and in `STAGE_PYTEST`. No conftest is then ever loaded. The self-erasing file fails the docs stage (1 failed, 96 passed), and the format stage keeps its 643.

**Scope, plainly.** Only a conftest.py written to hide itself gets through. Every accidental placement I tried is caught.

### R2-2. [gate] The docs gate's `need_file` exemption never lapses

**Claim (READ).** `tools/check_docs.py`, item 3, exempts a path "the runner guards with `need_file`, and anything under it, whose stage it skips by name while the path is missing". The ledger says: "The docs gate leaves a path the runner guards with `need_file` unchecked."

**Code (READ).** `guarded()` returns every `need_file` path in `verify/run.sh`, whether or not it exists. The reason for the exemption, "while the path is missing", ends when a parcel lands. The exemption does not end.

**Fault (MEASURED, `exp\d3_docs`).** With the P1 stand-in in place, so `tests/p1/` exists, a `README.md` line names `tests/p1/test_p1_ghost.py`, `tests/p1/nowhere/also_missing.json` and `qro/register_p1_ghost.py`. None exists, but `python tools/check_docs.py` reports only the third. From the day P1, P2 and P4 land, every path named below `tests/p1`, `tests/p2` and `tests/p4`, in any document or source file, is unchecked for good. The lead's test creates no guarded directory, so it cannot see this.

**Candidate fix (MEASURED in scratch, `exp\fixes`).** Keep only the guarded paths that do not exist: `{g for g in ... if not (root / g).exists()}`. The lead's `tests/docs/test_docs.py` still passes, and the ghost paths are then reported.

### R2-3. [code, and three false sentences] `checker.load()` lets a failing import through as itself

**Claims (READ).**
- `load()`'s docstring says a key held by another function and a step that is not the parcel's "raise RegistrationError, as does a module that fails to import. The command line answers either as the checker itself failing, exit 3: never a verdict."
- FORMAT.md item 16 says the command line exits 3 for "a parcel's module that will not load or registers what is not its own (item 20)". Item 20 says the same.
- `qro/__main__.py`'s docstring says the same.
- CLAUDE.md says: "A crash inside the checker is never a verdict."

**Code (READ).** `module = importlib.import_module(name)` has no `try`. A module's own exception propagates unchanged. `main()` then maps `Refused` to exit 1, `PermissionError` to exit 2, and anything else to exit 3.

**Fault (MEASURED, `scripts\d3_cli_cases.py`, `logs\d3_cli_cases.log`).** A `qro/register_p1.py` that does the following at import, then `python -m qro check --fixtures CRATE`:

| the module at import | exit | the line |
|---|---|---|
| raises `Refused('commitment', 'x', 'y')` | **1** | `REFUSED commitment at x: y`, a verdict on a crate never read. `python -m controls.plant twin` is refused the same way. |
| raises `PermissionError` | **2** | `some-file: cannot be read here, denied; usage: ...`, which is misuse |
| raises `RuntimeError`, `ImportError`, `SyntaxError`, `OSError`, `sys.exit(0)`, `sys.exit(1)` or `KeyboardInterrupt` | 3 | `FAILED: the checker itself failed, ...` |

**Why it can happen.** The module is imported on every `check`. Any module-level call into `qro.reader`, `qro.canonical` or `qro.spelling` that refuses, or any file read the user may not make, reaches `main()` as a verdict or as misuse. Inside the runner the `twin` stage notices. A stranger running `python -m qro check` gets a refusal their crate did not earn.

**Candidate fix (MEASURED in scratch, `exp\fixes`).** Wrap the import and the registration in `try: ... except RegistrationError: raise; except Exception as x: raise RegistrationError(f"{name} will not load: {type(x).__name__}: {x}") from x`. All four cases then exit 3, and the lead's 16 loader tests still pass. The docstring is then true as written.

## 3. What held

### 3.0 Freeze and the runner
- **Freeze (MEASURED, `sha256sum -c`).** 244 files and no line but OK. The file list equals SHA256SUMS, and SHA256SUMS.txt starts `5cd010aa423dbf46`. It held at the start and at the end.
- **Runner (MEASURED, `logs\run_base_full.log`).** In a `git init` copy with one commit, `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` gave `passed 17, failed 0, skipped 3` (p1, p2, p4 by name). Counts equal the ledger's:
  - tests: docs 97, tool-tests 71, vocab-tests 8, format 643, custody 23, control-tests 22, which is 864;
  - controls-run 9 of 9 with 21 pending;
  - study-plants 68 refused and 6 accepted;
  - privacy 244 files and 1 commit message;
  - privacy-controls 37 of 37;
  - instruments 5 of 5, with moth-quantum at 3a73823 and 0 changes;
  - check-docs 10 documents, 26 other markdown files, 35 source files;
  - the twin `ff3fe486...`;
  - the negative control `raw-digest at data/raw.counts.json`.
- **Each changed test file passes alone (MEASURED).**
  - test_load 16, test_refusals 26, test_sites 51, test_hostile 331, test_control_registry 22.
  - test_tools 71, test_docs 18, test_stage_registry 79, test_vocabulary 8, test_custody 23.

### 3.1 D1
See R2-1 for the matrix. I also ran the stage script as the runner runs it, from the root, with each plant. The lead's own end-to-end test runs it with a `pytest.ini` under `tests/` and a `pytest.toml` at the root.

### 3.2 D2 (MEASURED, `exp\d2`, a fresh process each)
- A plants module imported before the registry (`from controls import plants_p1`; `from controls.plants_p1 import job_reattributed`) loads. So does one imported after it or together with `controls.run`, and one that imports the registry and `qro`. `registry.plants()` then holds P0's nine plants and the parcel's.
- `registry.PLANTS` stays P0's nine, so anything reading it directly sees no parcel's plant.
- Two modules planting one name, or a parcel planting a P0 name, raise `RuntimeError` ("which another module already plants"):
  - from `plants()`, `controls.run` and `controls.plant`;
  - from `gen_vocabulary --check`, as a traceback with exit 1;
  - from `tests/controls`, as a collection error.
- A plants module with a syntax error, or without `PLANTS`, gives a traceback and exit 1. The registry module alone still imports.
- A plants module that calls `plants()` while it is being imported gets the old "partially initialized module" error. That is its own cycle.

### 3.3 D3 (MEASURED)
- **One parcel (`scripts\assemble.sh`, `overlays\p1`).** The stand-in is:
  - `qro/register_p1.py` with steps 4, 5 and 8, a raw form, a generator and a count rule;
  - `controls/plants_p1.py` with three plants;
  - `tests/p1/`, whose test imports its plants module first and runs the command line in process, plus a helper.

  The full runner gave `passed 18, failed 0, skipped 2` (`logs\d3_p1_full.log`), and controls-run gave 12 of 12 built, 18 pending.
- **Three at once (`overlays\p1`, `p2`, `p4`).** The full runner gave `passed 20, failed 0, skipped 0` (`logs\d3_all_full.log`). controls-run was 13 of 13, with p1 at 5 tests, p2 at 1 and p4 at 1.
- **A git merge of three branches (`exp\d3_merge`).** Each branch only adds files (P1 four, P2 three, P4 one). The merges have no conflict, and no file of the base is edited. The quick budget on the merge gave `passed 17, failed 0, skipped 0` (`logs\d3_merge_quick.log`).
- **A single pytest session over `tests/` with all three (875 tests).** It passes in file order, reversed, and in six seeded shuffles (`scripts\plug\`, `logs\d3_shuffle.log`). Loading the parcels' steps into a long-lived process changes no P0 test's verdict.
- **The loader through the command line (`scripts\d3_cli_cases.py`).**
  - A parcel registering another's step gives exit 3. Cases: P2 for step 4, P1 for step 6, P0's steps 3 and 9, step 10, step `'4'` as a string, and `True`. Messages: "which is P1's / P2's / P0's / no parcel's".
  - A parcel registering the fixture's raw form or generator under `--fixtures` gives exit 3.
  - Two parcels registering one name with two functions give exit 3. With one shared function it is accepted.
  - A module with a syntax error, a missing import, an exception, `sys.exit` or a keyboard interrupt gives exit 3.
  - With `--fixtures`, `STEPS` as a list or `None`, `RAW_FORMS` as a list, `COUNTS` as a function or a list of strings, and a step that is not callable all give exit 3.
  - A step raising `PermissionError` gives exit 2. One raising `SystemExit` or `ZeroDivisionError` gives exit 3.
  - `python -m qro custody` is untouched by a broken module.
  - Loading three times in one process changes no registry.
- **The command line, r1 against r2 (MEASURED, `scripts\cli_diff.py`).** I ran 1,189 argument lists over four crates, a file, an empty directory and a missing path. 0 differ in exit code, stdout or stderr.

### 3.4 The privacy gate's changes
- **Address patterns, old against new (MEASURED, `scripts\priv_addr_inv.py`, 1.2 million random texts over address-like fragments).** The leftmost match of each pattern is the same old and new in every text. A text the old gate flagged and the new one does not always has an allowed or reserved address as its leftmost match; none has a real leftmost address. So the stated limit is exact. A second or later address glued to the previous match by one of an address's characters is lost, and nothing else is. In rare glued strings the new pattern also flags something the old did not (a different segmentation); I saw 2 in 300,000 texts.
- **Speed (MEASURED, `scripts\priv_perf2.py`).** I ran all 34 alternatives over 36 families of hostile text at 20,000 and 80,000 characters. None is superlinear, and the worst is 80 ms at 80,000. Two runs of 100,000 letters take 0.08 s, against the lead's bound of 3 s. 16,000 spaces after `token` take 9 ms.
- **The key pattern's bounds (MEASURED, `scripts\priv_key_bounds.py`).** For all nine named alternatives:
  - up to 32 white-space characters in one run between the name and `=` or `:`;
  - with a quote, up to 16 before it and up to 16 between it and the separator;
  - up to 16 after the separator;
  - up to 16 after `Bearer` or `apikey`.

  One more of each passes. The docstring's three conditions are all true, and it omits a fourth (4.2).
- **The new URI schemes (MEASURED).** None of `smb`, `nfs`, `rsync`, `ftp`, `ftps` or `file` matches a thing in the tree beyond the gate's own source and two earlier reports, and those pass.
- **Git in the test repositories (MEASURED, `exp\gitr1`, `exp\gitr2`).** With a global `.gitconfig` that signs commits with a failing signer, `tests/tools` fails 4 on round 1's tree and passes 71 on this one. Git does read that file: a commit outside the tests fails with "gpg failed to sign the data". See 4.1.8 for what the fix does not cover.

## 4. Notes (below the bar)

### 4.1 Test reach: the shipped code is right, a fault would pass
1. **The stage script's environment lines are held by no test (MEASURED, `exp\unsetmut`, `mut\shell_mutants.py`).**
   - Remove `unset PYTEST_ADDOPTS PYTEST_PLUGINS`: the registry passes (97), and `PYTEST_ADDOPTS=--ignore=tests/format/test_hostile.py` then gives a format stage that passes with 312 tests.
   - Removing `export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, or removing `skipped` from the refusal grep, also passes the docs stage.
   - The pin holds the pytest line and nothing else in the script.
2. **A parcel stage's guard is not compared with its directory (MEASURED, `exp\d3_guard`, `mut\shell_mutants.py`).**
   - With `tests/p1/` built, make p1's `need_file` name `tests/p2`. The registry passes (97) and check-docs passes. The runner SKIPs p1 with "there is no tests/p1" and ends `== PASSED, with 1 skipped`.
   - check-docs catches the same mistake only while `tests/p1` is missing.
   - `need_file` written with `-f` for `-e`, and p1's stage running `tests/p2`, also pass.
   - Dropping p1, p2 or p4 from `BUDGET_QUICK` passes the docs stage. No test reads the quick selection.
   - Deleting or renaming a stage line is caught only through the quick budget (`run.sh` exits 2, unknown stage).
3. **The address lookbehind's character class is pinned by one character (MEASURED, `mut\hand_priv.py`, `scripts\priv_lb_perf.py`, `priv_lb_perf_esc.py`).**
   - Dropping any of `.`, `_`, `%`, `+`, a digit or a capital from the `address` lookbehind passes every test and stage. So does dropping `-`, `.` or a digit from the `escaped-address` one.
   - Each is a real regression. On a 40,000-character run of that character, `address` takes 1.7 to 3.5 s and `escaped-address` 6.4 to 12.5 s, where the shipped patterns take 1 ms. The growth is quadratic, so 100,000 characters would take about six times longer (BELIEVED, from the growth).
   - The speed test uses letters only, and the glue test uses `-` only.
   - `apikey`'s bound moved to 15 or 17 also passes. Only `Bearer`'s is held.
   - Dropping `\b` from the remote-URI alternative passes. It only adds matches.
4. **`controls.plant`'s usage branch is held by no test (MEASURED, `exp\plantmut`).** Changing `or` to `and` makes an empty argument list raise `IndexError` and makes a second argument ignored (`twin extra` gives ACCEPTED). The usage line deleted and its `sorted` removed also survive. `controls.run`'s final count line is unasserted (`in` to `not in` survives). The `(new)` marker in `check_docs.py` has no test at all (three survivors).
5. **The prefix rule has no nested negative (mutant).** `rglob` to `glob` in `misnamed()` passes. The unit test plants a nested file that carries its prefix, and none that does not.
6. **The loader's order and de-duplication are unheld (mutants).**
   - Parcels loaded in reverse passes.
   - `COUNTS` de-duplicated by function name (a second parcel's same-named rule is dropped) passes.
   - The `need_file` regex without its `^` anchor, or without its trailing space, passes. A commented guard line would then exempt a path.
   - The `sorted` over `plants_*.py` survives, as the lead said. NTFS lists in order, and a test with the listing reversed, as the walk's has, would kill it.
7. **`PYTEST_FILES` is both the list checked and the list of plants.** Dropping `setup.cfg`, `tox.ini`, `.pytest.ini`, `.pytest.toml` or `pytest.toml` removes the name and its plant together, so nothing fails. Since `-c` makes all of them inert, only the hygiene report is affected.
8. **Git in the test repositories is hermetic for files, not for the environment (MEASURED, `exp\gitenv`, `exp\gd_repo`).**
   - `GIT_CONFIG_COUNT`/`KEY`/`VALUE` setting `commit.gpgsign` fails 8 tool-tests.
   - With `GIT_DIR` in the environment, as a git hook has it, `tests/tools` wrote seven test commits and index changes into the repository `GIT_DIR` names (a scratch repository; 4 tests failed).
   - If `verify/run.sh` is ever run from a hook, the quick budget would do that to the real repository (CLAUDE.md item 5).

### 4.2 Prose
1. `load()`'s docstring, FORMAT.md items 16 and 20, and `qro/__main__.py` (R2-3). `load()`'s docstring says a module that fails to import raises `RegistrationError`. It raises its own exception.
2. `tools/check_privacy.py` line 66, "A text's first address starts there anyway, so a text that held a finding still does", is false when the first address is allowed or reserved (MEASURED, `scripts\priv_one.py`).
   - Take `x`, an at-sign, `example.com`, a hyphen, `u`, an at-sign and `personal-domain.net`, with no space. The old pattern flagged the second address, and the shipped one flags nothing. The same holds with a dot for the hyphen. With a comma and a space both gates flag it.
   - The next clause states the limit, but the sentence before it overclaims. Its own example has both addresses in reserved domains, so it shows no loss.
3. The gate's docstring lists three ways a key passes: more than 32 between the name and the separator, more than 16 between a quote and it, and more than 16 after it or after `Bearer` or `apikey`. A fourth is true for all nine alternatives (MEASURED): 17 to 32 white-space characters between the name and a quote also pass.
4. The ledger says of the bounds, "A test holds each, one more passing". There is no such test for `apikey`.
5. `docs/README.md` still describes `reviews/` as "the study's and P0's".
6. CLAUDE.md says the quick budget is "~30 s".
   - The stage seconds sum to 35 on my quietest run and 41 to 45 on later ones (14 stages; other processes were running on this host).
   - It was 32 on the previous tree. This round added 68 tests (796 to 864).
   - The full run's "~85 s" holds: 88 s of stage seconds, `logs\run_base_full.log`.
7. CLAUDE.md item 7 gives "(P3's and P5's rows that state or keep)" as the outcomes the controls' run lacks. The ledger also names `joint-omission`, which is neither.
8. FORMAT.md item 20 says "Nothing else does in process, so P0's tests still plant into unbuilt steps". Every in-process command-line test loads. The tests now set the steps unbuilt themselves, and that is what holds them.

### 4.3 Design observations
1. **A module that sets the registry itself bypasses the checks (MEASURED, `exp\d3_direct`).** Ownership and clash are checked for the declared dictionaries only. A `qro/register_p2.py` doing `checker.STEPS[4] = f` replaced P1's step 4 silently, since it loads after P1's. The `job-reattributed` plant then came out `metadata-generated`. controls-run would say WRONG, but `load()` would not. Item 20 says a module "sets nothing itself", and the old CLAUDE.md told a parcel to register this way. A snapshot of the registries around each import would enforce it.
2. **The fixture's names are protected from a parcel only under `--fixtures` (MEASURED).** A module registering both of the fixture's names with the fixture's own functions makes the plain command line accept the fixture (exit 0). P0's `test_without_fixtures_the_fixture_is_refused_step_unbuilt` would fail in the format stage, so it is caught there.
3. **Every parcel module is imported on every check.** A heavy or optional import at module level becomes the checker's. Without it, every crate exits 3, P0's included (BELIEVED, from the code).
4. **Seams a parcel still meets that item 7 does not name (MEASURED, `exp\d3_seams`).**
   - A document directly under `docs/` fails check-docs until the lead's `docs/README.md` lists it.
   - Python in a new top-level directory fails the registry's lint-shape tests until the lead's lint line names it. In the probe 8 of the 9 shape tests failed.
   - A tool under `tools/` with a `__main__` fails the registry until `run.sh` has a stage for it.
   - Where the rest of a parcel's code lives under `qro/` is not said, and no rule keeps two parcels' names apart there. A generic `qro/qpy.py` passes everything.
5. **`tools/gen_vocabulary.py` has no message for a plant named twice.** It crashes with a traceback and exit 1. Its documented exit for a contradiction is 2.
6. **`FORCE_COLOR=1` or `PY_COLORS=1` makes the stage script refuse a passing run (MEASURED).** The summary line carries colour codes, and the script reads "no '<n> passed' summary line". It fails closed. It came from moth-quantum's copy and was not changed by this round.
7. **On a case-insensitive file system that is not Windows, `Conftest.py` is read by pytest and missed by the registry's `rglob` on 3.12 (BELIEVED, from pathlib's source).** Windows is consistent (MEASURED). A symbolic link to a directory under `tests/` is searched only one level deep by `rglob` and fully by pytest (BELIEVED; I could not make symbolic links).

## 5. Mutation

I used round 5's `hmp.py` (operators D and E, byte offsets) and round 3's `hm.py` (hand mutants). Each mutant runs the six test directories the runner runs, and a survivor then runs the twin, the negative control, `gen_vocabulary --check`, controls-run, check-docs and ruff. Mechanical mutants are kept to the lines this round changed (`mut\tools\filter_changed.py`).

| set | mutants | killed | survived | n/a |
|---|---|---|---|---|
| operator D, changed lines of `checker`, `__main__`, `vocabulary`, `controls/run`, `controls/plant`, `check_docs`, `gen_vocabulary` | 61 | 58 | 3 | 0 |
| operator E, the same files plus `controls/registry` | 55 | 42 | 13 | 0 |
| my hand mutants: registry pin, prefix rule, plants, loader, vocabulary, docs gate | 41 | 23 | 17 | 1 (mine, did not compile) |
| my hand mutants: privacy gate (lookbehind, URI schemes, key bounds) | 27 | 14 | 12 | 1 (text not found) |
| my hand mutants: the two shell scripts | 15 | 3 by the docs stage or check-docs; 2 only by the quick budget's name check | 10 | 0 |
| the lead's 32, re-run (`mut\lead_m.py`) | 32 | 31 | 1 (plants not sorted, as the lead said) | 0 |

**Survivors of operators D and E (16).**
- Equivalent (6):
  - `argv[0]` to `argv[-1]` at four sites in `controls/plant.py`. The list has one item when it is read.
  - `"P0"` to `"P0x"` in `load()`. There is no `qro/register_p0.py`, and P0 declares nothing.
  - `set()` dropped in `guarded()`. It is only iterated.
- Gaps (10):
  - the `controls/plant.py` usage branch (4);
  - the `controls/run.py:55` count line (1);
  - the `(new)` marker (3);
  - the plants merge's sort (2, the lead's).

**Survivors of my hand mutants.**
- Equivalent, or the test's own line:
  - five file names dropped from the list that is also their plants (4.1.7);
  - `p[0-9]+` to `p[0-9]`, since no `p10` exists;
  - identity to equality on functions;
  - first owner against last owner, since the sanity check allows one owner a step;
  - `split("; ")` to `split(";")`, since each step also appears first or alone in some row;
  - the fixture registered before the misuse checks, which has no observable difference;
  - the end-to-end test's own `"2 passed"` loosened;
  - P0's module not skipped.
- Gaps: 4.1.2 to 4.1.6, and the privacy survivors in 4.1.3, of which 9 of the 12 are real regressions.

## 6. What I did not do, and my slips
- **Hosts not covered.** I ran no macOS, no Linux file system, no Python 3.13 or later, and no WSL (its Python 3.10 is below the floor). I made no symbolic links on Windows (error 1314) and used a junction. The case-insensitivity and symbolic-link remarks in 4.3.7 are BELIEVED.
- **Not done at all.** A real-repository run of the runner, `rocrate-validator`, a JSON-LD processor, review of P1 to P5 or of the study, round 5's class-member mutation sets, and a commit-message trial of the privacy gate beyond the one message in my copy.
- **My stand-ins are scratch only.** They are `overlays\p1`, `p2` and `p4`, the plants and registration modules, and the plant conftests in `exp\`.
- **No IBM or Atlas contact, no sensitive values.** I opened no `.quantum-film`, no `.atlas` directory and no credential file. I saw no key, token, CRN or job id, and the key-bound probes used made-up values.
- **Slips.**
  - Two of my first address-fuzz helper scripts lost a backslash in a Git Bash heredoc (CLAUDE.md "What bites" item 1). Their "old" escaped-address pattern then matched plain addresses, and an anomaly (281,059 "violations") showed it. I redid them with the Write tool and report only the corrected runs.
  - My first `cli_diff.py` run used a relative work path under a different working directory. It wrote three data files into my pristine copy `work\`, which I removed and checked against `frozen\tree` (identical but for `.git`). Copies taken in between (the timing copy, the shell-mutant copies, one merge run) held those files. I redid the merge on a clean copy, and no number above depends on them.
  - I wrote three small items to the system temp directory outside `check\`: a probe home directory and two file lists. I removed them. pytest's own temporary directories remain there, as in earlier rounds.
  - The harness reports a `nohup` launch as "completed" when only the launcher has finished, so I polled the logs.
  - Other work was running on this host during my timings, so those are noisy.
