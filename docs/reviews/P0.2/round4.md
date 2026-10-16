# P0.2 verifier, round 4: READY, on the relaxed bar

I found no defect in what the shipped code does. Round 3's defect is fixed, and every earlier fix still holds.

Labels used below: READ, MEASURED (the script or log is named) and BELIEVED. CHECK means SCRATCH\verifier-P02-r4\check, with `scripts\` and `logs\`. The environment was Python 3.12.9, pytest 9.1.1 and git 2.45.2.windows.1. P0.3's verifier ran beside me throughout, so my timings are loaded.

## The freeze

MEASURED: `sha256sum -c` gave 251 OK at the start and the end, with the sums file starting `c104d2b4d4255158`. There were no `.pyc` files and nothing ran inside `frozen\`.

## Defects in what the code does

None. The two closest candidates are notes 1 and 2 below. I judged both contrived, so they do not block. Note 1 is new in this round's change.

## Round 3's defect, and the gate on unreadable history (MEASURED)

- **47 history shapes.** `scripts\probe_hist4.py` (`logs\probe_hist4.log`) ran the gate as the runner runs it, on 47 shapes of a repository history.
  - The shipped gate gets 38 of the 39 shapes that carry an expectation right. The base commit's gate (8858978) gets 19 right.
  - Round 3's four missed shapes now exit 1 with "commit messages: unread, as git log failed": a branch ref emptied, garbage, or NUL-filled, and a corrupt `packed-refs`.
  - So do these: a ref cut at 30 digits or half-NUL, a ref naming a missing object, `packed-refs` cut or NUL-filled, a tip or parent object deleted, zero-byte or corrupt commit objects, packs deleted, truncated, or lacking their index, a symref to itself, and an invalid branch name in HEAD.
  - A fresh repository, one with files staged, and an orphan branch still exit 0.
  - A readable ref with CRLF still finds the key.
  - A missing, emptied or garbage `.git/HEAD`, a bad `.git/config` and a garbage index crash loudly with exit 1, as before.
- **Same rows elsewhere.** Python 3.13.5 gives the same row for every shape (`logs\probe_hist4_py313.log`). Reftable and SHA-256 repositories behave correctly (`probe_reftable4.py`).
- **Through the runner.** `scripts\runner_hist4.py` shows the privacy stage failing (rc 1) for the emptied ref, the garbage ref, the NUL ref and the corrupt `packed-refs`. The privacy-controls stage also fails on an emptied ref. A fresh repository passes. A deleted tip stops the runner earlier with rc 2, as at round 3.
- **Round 3's demonstrations.** Its `demo_history.py` (empty, packed, deleted) now exits 1 on all three.
- **File controls.** The lead's 9 round-4 mutants reproduce, all 9 killed by their targets. My mutants "counts a key only" and "counts any finding" were also killed.

## Every earlier fix still holds (MEASURED)

- **Full runner, git-initialised copy with no commit** (`logs\run_base_full.log`): 17 passed, 3 skipped by name (p1, p2, p4), 160 s.
  - Tests are 133 + 106 + 8 + 664 + 23 + 32 = 966.
  - controls-run is 9 of 9 with 21 pending, study-plants 68 and 6, privacy-controls 37 of 37, instruments 5 of 5, check-docs 10 / 33 / 35.
  - The twin is `ff3fe486a466…` and the negative control is refused `raw-digest`.
  - Every figure equals the ledger's.
- **Clone of the real repository plus the frozen files**, with its real 2-commit history (`logs\run_clone_full.log`): 17 passed, 3 skipped, 148 s. Privacy read 251 files and 2 commit messages.
- **Other layouts.** A linked worktree (where `.git` is a file) passed the quick budget: 14 passed, 3 skipped, 74 s. A copy with no git passed the quick budget in 60 s. One pytest session over all of `tests/` gave 966 passed.
- **Generator, plant command, controls' run.** Round 3's D1 matrix, run on my tree, flagged 4 cells of 264. They are the same four as rounds 2 and 3: `controls.run` prints its `ok` lines before the one FAILED line, with exit 3.
- **Accident injections.** Round 3's harness (`inject4.py`) ran 36 injections with the same results as round 3. Round 3's C3 and C4 (emptied ref, corrupt `packed-refs`) now fail privacy through the runner. W5 and W6 show "!!" only because the harness expectation is stale. A tuple assert under a `filterwarnings` mark does fail the stage, as the corrected pyproject sentence says.
- **Git variables.** The gate reads its own repository under 17 settings of git's repository variables, one at a time and all together, plus a lowercase spelling and variables naming nonexistent places. In each case it exits 0 in the clean repository and 1 in the keyed one (`probe_gitenv4.py`). The registry tests pass with `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and `GIT_OBJECT_DIRECTORY` naming another repository.
- **The tests' git.** The whole suite passes in this machine's real git environment, which has a global configuration.
- **The lead's mutant files** (round 2, 3 and 4): 56 killed, 0 survived, 5 not applicable because the mutated text has changed since.
- **My other probes.**
  - 59 repository configuration settings that could change `git log` hid no key (`probe_cfg4.py`).
  - A non-ASCII path with spaces works.
  - 70 control and separator characters before a key hid it only for U+0001 (`probe_msgchars4.py`).
  - A key behind the shipped `errors="replace"` is still found for ISO-8859-1, cp1252, GBK, Shift_JIS and EUC-KR output.

## Notes (none blocks)

1. **[behavior, contrived; changed by this round]** `errors="replace"` turned a loud crash into a silent pass when `i18n.logOutputEncoding` is ASCII-incompatible.
   - MEASURED: `scripts\probe_enc4.py`. With UTF-16, UTF-16LE, UTF-32 or UCS-2, the key in an older message is not found and the gate exits 0. The round-3 and base gates crashed with exit 1.
   - With `--encoding=UTF-8` added to the `git log` call, all eleven encodings I tried find the key.
   - No accident sets such a value, so I made this a note.
2. **[behavior, older than P0.2, contrived]** A 0x01 byte before a key in a commit message hides the key.
   - MEASURED: `probe_hist4.py` and `probe_msgchars4.py`. The gate splits the `git log` output on that byte. The base gate does the same.
   - MEASURED in a scratch copy (`probe_remedy4.py`): `git log -z --encoding=UTF-8 --format=%H%n%B`, split on NUL, closes notes 1 and 2 and breaks none of four other cases. Nothing was applied to the tree.
3. **[behavior, older]** An untracked nested repository below the tree is listed by git as a directory. The gate then fails with "unreadable: PermissionError", exit 1 (`probe_worktree4.py`, and the same on 8858978).
   - MEASURED: a worktree under `.claude/worktrees/` is listed the same way.
   - BELIEVED: it would fail the same way. The owner's worktrees are siblings, so they are not hit.
4. **[behavior, older]** The gate reads the working file, but a plain `git commit` takes the index. A key staged and then edited out of the working file passes. MEASURED: `probe_staged4.py`, base the same.
5. **[test reach]** Of my 16 mutants of the changed region, 7 died and 9 survived (`logs\mut4.log`).
   - Four survivors take `.git` only as a directory, in the gate's `check()`, `files()` and `control()` and in the registry's `committed_files`. No test uses a linked worktree, where parcels will build. The shipped code is right there (MEASURED above).
   - Dropping `LC_ALL=C`, weakening the phrase, testing `== 128`, and decoding in the locale encoding survive. They are equivalent here. I could not exercise a localized git: this git has no translations, and `LANGUAGE=de` still prints English.
   - The `--encoding=UTF-8` mutant survives. That is note 1, not equivalence.
6. **[prose]** pyproject.toml says an import-time warnings filter "lifts any of the four" pins.
   - MEASURED (`probe_lifts4.py`): it lifts three. The returned-value pin held in all five placements. The comment is stricter than the truth; the code is right.
7. **[prose]** The gate docstring's "whatever broke it" does not cover shapes where `git log` succeeds or reads an unborn branch.
   - A ref naming a tree or a blob gives exit 0 with nothing read; both need a hand-written ref.
   - A deleted ref, a ref replaced by a directory, and an emptied `packed-refs` all read as no commit yet (MEASURED).
8. I agree with the lead's "not taken" items. The `ls-files` failure shows no git message (MEASURED, a bad `.git/config`), but it is loud and exits 1.

## What I did not do

- I ran no Linux, macOS or WSL. WSL's Python is 3.10, below the floor.
- I used no other git version. The unborn rule's English sentence is MEASURED only on 2.45.2.windows.1.
- I did not run pytest on Python 3.13, since it is not installed there and I did not install it. Only the gate ran under 3.13.5.
- I took no idle timings.
- I did not run a real pre-commit hook this round. Round 3 did, and I ran the harness's hook-environment case H1.
- I did not read the worktrees, the ledger, the designs or P0.3's verifier's directory. I touched the real repository only to read it, with `git archive`, `git clone` and `git log` (`GIT_OPTIONAL_LOCKS=0` on the first and last).
- I made no network, IBM or Atlas contact. Every key-shaped string was synthetic, built in pieces, and printed masked by the gate. No job ids appeared.
- My own slips changed no result and touched nothing in `frozen\`:
  - One probe was first written through a Git Bash heredoc, which loses backslashes (CLAUDE.md trap 1). I rewrote it with the editor.
  - One probe first parsed the gate's 40-line print limit instead of calling `check()`. I fixed it.
  - One background launch lacked an exported variable. I relaunched it.
