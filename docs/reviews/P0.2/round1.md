## P0.2 verifier, round 1: NOT READY

I found two small defects. The code of the notes P0.2 took holds, but the generator does not answer its own failure the way P0.2 says it does, and two sentences say more than the code does.

Labels: READ (in a file), MEASURED (I ran it; the script or log is named), BELIEVED (my inference). SCRATCH is `<scratch>`. CHECK is `SCRATCH\verifier-P02-r1\check`. Scripts are in `CHECK\scripts\` and logs in `CHECK\logs\`.

### 1. Defects

**D1. [code and prose] The generator's answer to its own failure is not "exit 3 and one line" in three cases.**
- **RuntimeError gives exit 2, not 3.**
  - Fault: a `controls/plants_p1.py` holding `raise RuntimeError("fixture file missing")`.
  - `python tools/gen_vocabulary.py --check` prints "the definitions contradict themselves:" and "  fixture file missing", and exits 2. The plant command and `controls.run` answer the same module as a FAILED line and exit 3. (MEASURED by hand in a full copy, `w_t1`, and by `probe_n4.py frozen`.)
  - In the runner, `vocabulary` fails with rc 2 and `twin` with rc 3.
  - Cause: `problems()` at `tools/gen_vocabulary.py:116-119` turns any RuntimeError from `C.plants()` into a contradiction. It was written for the registry's own name clash (round 2, note 4.3.5).
  - False text: the docstring P0.2 wrote ("3: the generator itself failed, a plants module that exits or fails as it loads among the causes") and the comment on the new `except BaseException`.
- **A line feed in the message makes two lines.**
  - Fault: `raise ValueError("fixture file missing" + chr(10) + "REFUSED forged at x: y")`.
  - The generator writes two stderr lines, the second starting `REFUSED forged at x: y`, and exits 3. The plant command writes one escaped line. (MEASURED, `probe_n4b.py` and by hand.)
  - The generator's FAILED line at `gen_vocabulary.py:152` is the only one of the three not passed through `escape`.
  - False text: the ledger's N4 bullet ("exit 3 and one line") and the docstring of `test_each_command_answers_a_plants_module_that_exits_0_as_its_own_failure`. That test checks only exit 0.
- **"Nothing was checked" is wrong after `--write` has written files.**
  - Fault: a read-only `docs/CONTROLS.md`. `--write` writes three files, then prints "…; nothing was checked" and exits 3. (MEASURED.)
- Both exit codes fail the stage. The harm is a wrong label and a forged-looking line.

**D2. [prose] Two sentences claim more than the code does. The code is right.**
- **CLAUDE.md lines 28-30 and the ledger's N2 bullet** say "tests in a module pytest does not collect" fail the registry.
  - The check reads only modules under `tests/`. `stray_tests`' own docstring says "under tests/".
  - A failing `def test_x` in `qro/register_p1.py`, a `class TestX` in `controls/plants_p1.py`, and a `def test_x` in `tools/helper.py` all pass the registry. (MEASURED, `probe_stray.py OUTSIDE`, `logs\probe_stray_outside.log`.)
  - The mutant that drops the `tests/` restriction survives.
- **`pyproject.toml` lines 13-14** say "pytest's warnings that a test is not held, as errors", then list three.
  - Four more of the same kind still pass; see note A. The ledger and CLAUDE.md say "three of" or name the three, so only this comment reads wider.
- Restate both: add "under tests/", and "three of pytest's warnings".

### 2. What held

- **Freeze (MEASURED, `sha256sum -c` at the start, middle and end).**
  - 247 files OK; the sums file hash is 4034d0104a4009a5…; no stray directories.
  - `diff -rq` of the frozen tree against the real working tree is empty.
- **The change.**
  - `git archive 8858978`, then `diff -rq`, gives exactly the 13 files you list.
  - The ledger edit is append-only: 0 lines removed, 77 added.
  - No CR bytes in the changed files, and the CRLF set is the same 8 files as before.
  - Nothing outside your files was touched.
  - Every test assertion that changed was strengthened.
- **Runner** (`QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh`, Python 3.12.9, pytest 9.1.1).
  - On a `git init` copy: 17 passed, 3 skipped by name (p1, p2, p4), exit 0.
  - On a fresh local clone of the real repository plus the 13 files: the same, and privacy reads 247 files and 2 commit messages.
  - Every figure in the ledger entry reproduces: 128, 89, 8, 663, 23 and 31 tests (942), 9 of 9 controls with 21 pending, 68 and 6 study plants, 37 of 37 privacy controls, 5 of 5 instruments, twin `ff3fe486…`, and `raw-digest at data/raw.counts.json`.
- **Stand-in parcels.**
  - Round 4's P1, P2 and P4 overlays on the frozen tree: 20 passed, 0 skipped.
  - Your `sim_parallel.py` on a copy: passes, p4 skipped by name.
  - The command line is unchanged. `controls.run` and the generator's `--check` give byte-identical output before and after, and all ten plants give the same exit code and first line before and after (MEASURED, `cmp`).
- **N1.**
  - I01, I08, an unknown mark, a class with `__new__` and a dataclass named `TestVector` now fail the stage (MEASURED, `probe_warn.py`, 22 probes on both trees; logs `probe_warn_base.log`, `probe_warn_frozen.log`).
  - Removing the pin, or any one of the three filters, is killed.
- **N2.**
  - I02 and I03 now fail `docs`, in a git copy, an untracked state, a staged state and a linked worktree.
  - Shapes caught: `def test` or `class Test` after imports, under CRLF, decorated, in `p2_tests.py` and `testsuite.py`, and a test file at the root, in `docs/`, `tools/`, `build/`.
  - I07 (`check_it`) still passes silently; see note F.
- **N3.**
  - End to end with a real plant carrying a key with a line feed and `≥` (MEASURED, `probe_n3.py`).
  - Base: exit 3 under a redirected stdout. Frozen: one ASCII line, escaped.
- **N4.**
  - A plants module that exits 0, exits 1, exits with a message, raises KeyboardInterrupt, ImportError, SyntaxError, OSError, ValueError, or whose `str` raises, now gives exit 3 from the plant command, `controls.run` and the generator (MEASURED, `probe_n4.py`, `probe_n4b.py`).
  - A plant that exits at run time is also exit 3.
  - `--help` still exits 0 and argparse misuse still exits 2.
  - D1 is the exception to all this.
- **N5.** `.venv/`, `venv/` and `*.egg-info/` are not read by the privacy gate. `.venv/` passes every stage I ran. `venv/` still fails `docs`; see note C.
- **N7.** The three new assertions are killed by their mutants: the misuse line naming the record, the order's refusal moved, and the WRONG line. Your 10 mutants: 10 of 10 killed (MEASURED, `hm2.py` on `m_lead_p02.py`).
- **N8 and the prose.** The `"QISKIT_IBM_" + "TOKEN="` example matches `tools/check_privacy.py:194`. The README status is true.
- **Injections** (MEASURED, 30 on the stand-in tree).
  - I01, I02, I03 and I08 went from passing silently to failing. I07 still passes. I16 now also fails `vocabulary` and `twin` (the N4 fix, seen at runner level).
  - 22 ran through the quick budget (I01–I17, I20–I23, I30). I18, I19, I28 and I29 ran as the single stage or test that refused them in round 4 (`inject_direct.py`).
  - Every other result is identical to round 4. I24 to I27 (documents and privacy) were not run.
- I found no wrong acceptance introduced by P0.2.

### 3. Notes (below the bar)

**Gate**
- **A. Other pytest warnings that mean a test is not held still pass the stage, with `2 passed, 1 warning` and rc 0** (MEASURED, `probe_warn.py`, same class as I08).
  - `assert (1 == 2, "msg")` (`PytestAssertRewriteWarning`, "assertion is always true"), an exception in a thread, an exception in `__del__`, and a coroutine never awaited.
  - A `@pytest.mark.filterwarnings("ignore")` mark or a module `pytestmark` lifts your three filters for that test.
  - No stage emits any warning today (the stage logs name none), and `-W error::pytest.PytestAssertRewriteWarning` makes the tuple assert fail (MEASURED). So that filter, at least, costs nothing now.
- **B. [test reach, code right] No test plants a stray test in a git repository.**
  - The registry's git branch is the production path. Mutants that disable it all survive, including one that lists nothing. (MEASURED, `hm2.py` with `mutants_p02.py` and `mutants_p02b.py`.)
  - With the dead branch, I02 and I03 planted in a git repo give `128 passed`, rc 0 (MEASURED, `w_deadgit`). The unmutated registry fails them (`w_livegit`).
  - Dropping `re.M` also survives, because the plants are one-liners, and so do `def test_` for `def test` and the `tests/` scoping.
  - A fix would be to init a repo in the tmp_path plant test and put the hidden test on line 3.
- **C. [gate] `venv/` still fails `docs`.**
  - `shape_problems` counts any non-dot directory holding Python, and the lint does not name it. A second failure is the shape tests that expect exactly one problem. (MEASURED, `probe_venv.py`.)
  - `env/`, `build/` and `.tox/` still trip the privacy gate (MEASURED). N5 named only three names.
- **D. [gate, by pytest's naming] The new rules refuse some correct code.**
  - A helper function named `testing_dir()`, a class `Testbed`, a shared base `TestBase` imported by a test module, and star-imported shared tests are all flagged. The message "never collects" is false for the last two, since their tests run through the importing module.
  - Any `*_test.py` or `test_*.py` outside `tests/` is flagged.
  - A data class named `Test*` imported into a test module now errors at collection. CLAUDE.md does not mention `__test__ = False`.
  - The existing suite has none of these: 0 `class Test*`, 0 helper modules, one mark (READ).
  - Names like `TestVector` or `ks_test.py` are plausible in P2 and P3 (BELIEVED).
- **E. [gate robustness, contrived]**
  - The registry raises a bare FileNotFoundError when a tracked helper under `tests/` is deleted before `git add`, and a UnicodeDecodeError on a `.py` that is not UTF-8. The privacy gate names such a file cleanly.
  - With `GIT_DIR` and `GIT_WORK_TREE` naming another repository, the stray check reads that repo and passes with a stray planted (MEASURED, `w_gitenv`). The privacy gate lists files the same way (READ).
- **F. I07 (`check_it`) still passes, and the ledger says nothing about it** under N2 or "Not taken".

**Test reach where the code is right**
- **G.** The escape in the plant command's FAILED line, and in `controls.run`'s `run()` FAILED line, is held by no test. Mutants that drop it with the import kept all survive. Three other mutants were killed only by the linter's unused-import error. The text after the exception type is not asserted either.
- **H.** `missing[0]` against `missing[-1]` in the misuse line is equivalent with one missing file. With two missing files, which one is named is still unasserted.

**Prose**
- The registry's module docstring does not describe the stray check or its limits. These stay silent (MEASURED, `probe_stray.py`): a BOM before a first-line `def test`, `async def test`, an indented or double-spaced `def`.
- The `controls.run` FAILED wording changed ("no control was judged" to "this is not a verdict on the controls") with no word in the ledger. The new wording is better.
- CLAUDE.md's "~45 s" and "~100 s" were last measured idle by round 4 (47 s and 99.9 s), before `docs` gained a few seconds. I cannot re-measure them idle. My timings are noisy: a full run took 124 s on a copy, and stages ran many times slower in the clone under the owner's load.

### 4. What I did not do, and my slips

- **Not done.**
  - No Linux, macOS or WSL. No Python 3.13 (pytest is not installed for it here). No other pytest version.
  - No idle timings.
  - I24 to I27 were not run.
  - I did not re-run rounds 1 to 4's large matrices.
  - I did not see P0.2's commit message.
  - I did not verify the quote of Logan's word.
  - I did not read the P1 worktree or the ledger directory.
  - No network, no IBM, no Atlas; the instruments stage read moth-quantum's checkout only through the runner.
  - I applied no fix.
- **Slips.**
  - Early on I wrote two file lists into Git Bash's `/tmp` and removed them.
  - I ran three read-only commands with the working directory inside `frozen\tree`, with bytecode off. I re-ran the sums afterwards: all 247 OK, nothing new.
  - I started too many shards at once. When asked to run lighter I stopped three injection shards and an orphaned stage, then ran at most two heavy processes.
  - A `printf` in Git Bash lost its backslash and made a broken plants module. I redid it with `chr(10)`.
  - My first `probe_stray.py` died on read-only git objects. I fixed my script, not the tree.
- **Mutation total.**
  - My own: 43 mutants gave 28 killed by pytest, 3 killed only by lint and 12 survived. A second set of 7 gave 4 killed and 3 survived.
  - Your 10: 10 killed.

Key files are in `CHECK\scripts\` and `CHECK\logs\`: `probe_warn.py`, `probe_stray.py`, `probe_n4.py`, `probe_n4b.py`, `probe_n3.py`, `probe_venv.py`, `hm2.py`, `mutants_p02.py`, `mutants_p02b.py`, `assemble.py`, `inject.py`, `inject_direct.py`; logs `baseline_full.log`, `run_clone_full.log`, `run_all3.log`, `inject_*.log`.
