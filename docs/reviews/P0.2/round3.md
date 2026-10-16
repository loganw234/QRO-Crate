# P0.2 verifier, round 3: NOT READY

**Verdict: NOT READY, on one defect.** It is about what the code does, and it is narrow.

- The privacy gate accepts a repository whose history git cannot read when the cause is a broken branch ref or a corrupt `packed-refs`. Its docstring and the ledger say that case is a finding.
- Everything else I found is below the bar: test reach, prose, or contrived and older behaviour.
- Both round-2 defects are fixed. All eight notes the lead took hold, except that one is incomplete (the defect).

Labels: READ, MEASURED (the script and log are named), BELIEVED.

- CHECK is `SCRATCH\verifier-P02-r3\check`, with `scripts\` and `logs\`.
- Python 3.12.9, pytest 9.1.1, git 2.45.2.windows.1.
- P0.3's verifier was running beside me throughout.

## Defect

**1. [gate, code; three sentences are false with it] An unreadable history is read as "no commit yet" when the ref is broken.**

*The fault that shows it.* MEASURED: `python scripts\demo_history.py empty|packed|deleted`, log `logs\demo_history.log`. The setup is two commits with a synthetic key in the older message, then the gate run as the runner runs it (`python tools/check_privacy.py`).

| State | Gate | `git log` |
|---|---|---|
| Intact | exit 1, finds the key | exit 0 |
| `.git/refs/heads/main` emptied | exit 0, `privacy ok: 2 files and 0 commit messages read` | exit 128, "your current branch appears to be broken" |
| `.git/packed-refs` replaced by garbage | exit 0, same line | exit 128 |
| Emptied ref written back | exit 1 again | exit 0 |
| Tip commit object deleted (the lead's shape) | exit 1, "commit messages: unread, as git log failed" | exit 128 |

*The shape survey.* MEASURED: `scripts\probe_history.py` on a copy of the frozen gate, `logs\probe_history_r3.log`. The new rule fires for six shapes: tip gone, parent gone, a ref to a missing object, a detached HEAD at a missing object, a corrupt commit object, and all packs deleted. It misses four: an emptied branch ref, a garbage ref, a NUL-filled ref, and a corrupt `packed-refs`. A fresh repository and an orphan branch correctly read as "none".

*Cause.* READ: `tools/check_privacy.py` lines 177 to 180. `born` is `git rev-parse --verify --quiet HEAD` returning 0. That command returns 1 for a broken branch ref and 128 for a corrupt `packed-refs`, so both count as "no commit yet" and the failed `git log` is dropped. This is the exact condition of round 2's note ("git log fails and ls-files works"). The note is fixed for one shape of it.

*What is false.* READ: the gate docstring lines 14 to 15 ("A history git cannot read is a finding, never no messages"). The ledger bullet at `docs/VALIDATION.md:1729` says the same. The test name `test_a_history_git_cannot_read_is_a_finding_and_no_history_is_none` (`tests/tools/test_tools.py:212`) is also too wide, because it plants only the deleted tip. The wording is stated by the instance, not by the class conceded.

*Context.*
- MEASURED, `scripts\inject3.py` C2 to C4 (`logs\inject3.log`): the runner stamps these states `nocommit`, as `verify/run.sh` lines 132 to 139 do (READ). With an emptied ref or a corrupt `packed-refs` the whole runner passes (rc 0).
- A deleted tip object never reaches the gate through the runner. The runner dies first with "fatal: bad object HEAD / FATAL: git status failed", rc 2 (MEASURED). So the lead's new rule is live only when the gate runs alone.
- BELIEVED, narrow: a crash or a cloud-sync conflict can leave such a ref. Git then can neither log nor push, so there is no publication path while it stays broken.
- Why it still blocks: the gate says "ok" where its own text says "finding", which is a wrong acceptance and a false claim.

*Two ways to close it (not applied to the tree).*
- Code: tell an unborn branch from a broken one. I tried one in a scratch copy only (`scripts\cand_a.py`). It treats a failed `git log` as a finding unless its message, under `LC_ALL=C`, says "does not have any commits yet". Result: the 102 tools tests pass, the controls are 37 of 37, and all four missed shapes become findings.
- Prose: restate the three sentences as the class conceded ("a HEAD git cannot resolve reads as no commit yet") and add it to the gate's "cannot see" list.

A test should plant an emptied ref and a corrupt `packed-refs` either way.

## What held

- **Freeze.** MEASURED: `sha256sum -c` was 250 OK at start and end, with sums hash `c459136c02e8f6ff`. I made one slip (below) and undid it.
- **Runner, git-initialised copy.**
  - Command: `QRO_MOTH_ROOT=... bash verify/run.sh`, `logs\run_base_full.log`.
  - Result: 17 passed, 3 skipped by name (p1, p2, p4), 148 s.
  - Tests: docs 132, tool-tests 102, vocab 8, format 664, custody 23, control-tests 32, so 961.
  - Controls: 9 of 9 with 21 pending. Study plants: 68 and 6. Privacy controls: 37 of 37. Instruments: 5 of 5.
  - Twin `ff3fe486a466...`. Negative control: `raw-digest at data/raw.counts.json`. Check-docs: 10 / 32 / 35. Every figure equals the ledger's.
- **Runner, clone of the real repository plus the frozen files.** `logs\run_clone_full.log`: the same result, 143 s, privacy "250 files and 2 commit messages read".
- **Quick budget.** 14 passed, 3 skipped, 71 s. These are not idle timings, but they are consistent with CLAUDE.md's ~70 s and ~125 s.
- **Round-2 defect 1 (the sentence on marks) holds.**
  - `scripts\probe_lifts.py` (`logs\probe_lifts.log`): 5 faults times 10 lifts.
  - A test mark ("ignore", "default" or "always") or a module `pytestmark` lifts only the returned-value pin. The tuple, the unknown mark and the uncollectable class still fail the stage.
  - `PYTHONWARNINGS` in the environment lifts none of the four (`scripts\probe_envwarn.py`, 24 cells).
  - `inject3` W5 and W6 now fail p1, as the corrected sentence says. The "!!" there is my stale expectation.
- **Round-2 defect 2 (a global ignore file listing `build/`) holds.**
  - The literal fault now passes: `XDG_CONFIG_HOME` holding `git/ignore` with `build/`, then `--only tool-tests,docs`.
  - Hostile fake home (`scripts\probe_hostile_home.py`, `logs\hostile_r2.log`, `hostile_r3.log`):

    | Tree | Fake home with HOME, USERPROFILE and XDG variants | tools tests |
    |---|---|---|
    | round 2 | 12 failures | |
    | round 3 | | 0 failures |

  - The fake home holds a global config (`excludesFile`, `attributesFile`, `autocrlf`, `hooksPath`, `templateDir`, `gpgsign`, `useConfigOnly`), a default-place ignore file and an attributes file.
  - With a plausible global ignore (`build/`, `dist/`, `venv/`, `*.py[cod]` and so on), all 212 tools and registry tests pass. This holds at the default place, via XDG, via `core.excludesFile` through `GIT_CONFIG_COUNT`, and via `GIT_CONFIG_PARAMETERS`.
  - The whole runner under that environment passes (`scripts\hostile_runner.py`, 132 s).
- **Config kept, in the gate and the registry.**
  - `scripts\probe_gate_env3.py`: round 2's gate raises on a different-owner checkout trusted only through `GIT_CONFIG_COUNT` or `GIT_CONFIG_PARAMETERS`; round 3's reads it.
  - The runner's stages pass in three hook environments (`scripts\hook2.py`): plain, `git -c` with a temporary index, and the COUNT form.
  - I captured a real pre-commit hook environment. It carries `GIT_CONFIG_PARAMETERS` and `GIT_INDEX_FILE`, but no `GIT_CONFIG_COUNT`.
- **The generator's line.**
  - `scripts\probe_write3.py`: 7 failures times 3 stdout modes. The files the line names equal the files written in all 21 runs.
  - "No file" appears only where none was written.
  - A reader that has gone gives exit 120 after the line, as the docstring says.
- **Contradictions.** `scripts\probe_contra3.py`: 14 hostile plant names (LF, CR, VT, FF, NEL, LS, a backslash, NUL, ESC, a surrogate, é, an emoji, a 100,000-character run, and one starting REFUSED). Result: exit 2, exactly 15 lines, printable ASCII, no line starts with REFUSED, nothing written.
- **Round 1's D1.**
  - `probe_d1.py`: 264 cells, 4 flagged. They are the same 4 as round 2, where `controls.run` prints its `ok` lines first by design.
  - `probe_d1b.py`: 60 file-shape cells. The 5 flagged are a module that loads fine.
  - At runner level, `inject3` G1 to G3 give rc 3, 3, 3 and rc 2 for the clash.
- **No unintended change.**
  - `probe_registry3.py`: round 2's and round 3's registries give identical answers on all 27 repository states.
  - `inject3`: W1 to W9, R1 to R13, P1 to P5 and H1 all as expected. P2 is the runner itself refusing a foreign `GIT_DIR` with rc 2, the same as in round 2.
  - The diff against 8858978 is 17 files plus `docs/reviews/P0.2/`. The same 8 files hold CRLF as before.
- **Mutation.** The lead's 21 mutants reproduce: 21 killed by their targets (`logs\mut_lead.log`). My 15 are in the test-reach notes below.

## Notes (below the bar)

**Test reach, code right.** MEASURED with the lead's `hm_t.py` and my mutants `scripts\m_r3v.py` and `m_r3v2.py` (`logs\mut_v.log`, `mut_v2.log`). Eight of my 15 died; the survivors:
- Keeping only `GIT_CONFIG_COUNT` survives the whole suite, in the gate and in the registry. No test holds `GIT_CONFIG_PARAMETERS`, which is what `git -c` exports to a hook.
- The birth test run in the user's environment survives. The generator appending the file to `written` after its print survives; only a reader that has gone shows it. Anchoring `*.egg-info/` at the root survives, because only a root `pkg.egg-info` is planted.
- A filter that drops only the four variables the tests set passes the tests. Keeping `GIT_COMMON_DIR` passes everything. The first only dies because ruff flags the unused variable, which is luck.
- The registry's other two new tests are not hermetic. `test_committed_files_keep_...` sets no `XDG_CONFIG_HOME`, so a global ignore listing `*.py` fails it (MEASURED, one-line fault).
- `GIT_TEMPLATE_DIR` and an environment-injected `core.excludesFile` that hides the planted names also fail the registry's tests. Round 2's tree was immune to the injected form, because `git_env` dropped the variables. Only ignore patterns matching the planted names trigger any of this.

**Prose.**
- pyproject.toml's "Stated limits" omits an import-time `warnings.simplefilter("ignore")` or `filterwarnings("ignore")` in a test module or a helper it imports. MEASURED in `logs\probe_lifts.log`:
  - It lifts the unknown-mark and uncollectable-class pins for the rest of that module and every later one.
  - It lifts the tuple pin for every later module.
  - No test or module does this today.
  - By METHOD §6's test of a stated limit, this fault lies outside the listed limits. It needs one clause; the registry's "test module is code" caveat names tests leaving a stage, not pins lifting.
- `docs/VALIDATION.md:1739`, "so only dropping the whole list passes", is false (see the mutants above).
- The gate docstring's "Every git it runs" is literally untrue for its first call, `rev-parse --local-env-vars`, which must run in the ambient environment.
- README line 30 says P1's, P2's and P4's designs are "approved". I may not read the designs or the ledger, so I cannot check it. The brief says "finished".

**Other, contrived or older (not P0.2's changes).**
- A commit message that is not valid UTF-8 (for example under `i18n.logOutputEncoding=ISO-8859-1`) crashes the gate with a thread traceback and exit 1. It fails closed. MEASURED in the history probe's last row.
- `ls-files` failures raise `CalledProcessError` without git's own message, because stderr is captured. "Dubious ownership" would show no hint. The failure is loud and correct.
- In a copy with no `.git`, a root `venv/` is read by both the registry and the gate. This is documented.

## The lead's notes not taken

- **G6/I07:** the reason holds.
- **Generator drift and success lines unasserted:** the reason holds, since they are cosmetic.
- **`git init` in the gate's file controls:** the first half holds. MEASURED with `scripts\mut_noinit.py`: removing it leaves 37 of 37 caught and the 102 tools tests passing.
- The second half ("the gate's own tests exercise git's listing") fails for names git would quote. MEASURED with `scripts\mut_nz.py`: with `-z` dropped and the list split on line feeds, all 102 tools tests, the gate and 37 of 37 controls still pass. The non-ASCII control says "caught" because `ok = bool(check(r)[0])` accepts the spurious "unreadable" finding.
- That is the P0 gate's own gap; the shipped code is right.

## What I did not do

- No Linux, macOS or WSL (its Python is 3.10), no Python 3.13, no other git or pytest version. The history rule leans on git 2.45's `rev-parse --verify HEAD` not checking that the tip object exists.
- No idle timings.
- I did not read the worktrees, the ledger directory or the designs.
- I did not check round2.md's source SHA or its transcript.
- I did not re-run round 4's I18, I19 and I24 to I29.
- No network, IBM or Atlas. All key-shaped strings were synthetic and built in pieces, and printed masked. No job ids appeared.
- I applied no fix. Candidate A ran only in a scratch copy.

**My slips.**
- `scripts\probe_registry3.py` ran with `python -I`, which ignores `PYTHONDONTWRITEBYTECODE`. It wrote 12 `.pyc` files into `frozen\tree`, and the same 12 into round 2's `frozen\tree`. I removed exactly those 12 files and their `__pycache__` directories in both trees. `sha256sum -c` is clean (250 and 249 files, no `__pycache__`).
- My first probe_history run leaked two read-only temp directories (removed).
- A Git Bash heredoc lost a backslash once; I rewrote that script to a file.
