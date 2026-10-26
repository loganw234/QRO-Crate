# P0.4 verifier, round 4: READY, on the relaxed bar

I found no defect in what the shipped code does. Both of round 3's fixes hold, and the round's other changes gave no wrong answer, crash, hang or wrong exit under anything I tried.

Below, paths are relative to `SCRATCH\verifier-P04-r4\check\`; scripts are in `scripts\` and logs in `logs\`. Labels: READ, MEASURED (with the script or log) and BELIEVED.

## Freeze and setup
- MEASURED: `sha256sum -c` gave 259 OK at the start and at the end. SHA256SUMS begins `c45241c98b980ed1`, and there is no `.pyc` under `frozen\`.
- MEASURED: the real repository's working tree equals the packet. I ran `sha256sum -c` from there, read-only. HEAD is 7f40400.
- Environment:
  - Host: Python 3.12.9 (also 3.13.5), git 2.45.2.windows.1, Git Bash 5.2.26, ruff 0.11.9, pytest 9.1.1.
  - WSL as root: Python 3.10.12, git 2.34.1, bash 5.1.16.
- MEASURED: full runner on a clone of the real repository plus the frozen files (`logs\run_clone_full.log`): 17 passed, 0 failed, 7 skipped by name, 146 s wall.
  - docs 164, tool-tests 129, vocab-tests 11, format 679, custody 23, control-tests 32, so 1,038 tests.
  - privacy: 259 files, 4 messages, 14 staged versions.
  - privacy-controls 37 of 37; check-docs 10, 41 and 35; the twin ACCEPTED `21fafec5…`; instruments 5 of 5.
  - Every figure equals the entry's. The time is 146 s against CLAUDE.md's ~125 s (see note 10).
- MEASURED: the change against round 3's packet is seven files plus the new `round3.md`.
  - VALIDATION.md is a pure append: round 3's bytes are an exact prefix.
  - Against 7f40400 the changed files are the 14 the ledger lists plus `docs/reviews/P0.4/`, with no mode change and no CR byte.
  - I found no unintended change.
- MEASURED: `round1.md` and `round3.md` hash to the README's values. `round2.md` differs, as its row says (one redaction).

## Defects in what the code does
None.

## Round 3's two defects
- **R3-1, the guard-form rule's comment stripping.**
  - MEASURED: round 3's own fuzzer, with bash as ground truth (`scripts\fz_guard_forms_r3.py`, seeds 1 to 3, under WSL), gave 7,068 distinct chunks and 4,951 that make bash call a guard. All 4,951 were either flagged or in the exact form: 0 MISS. Round 3 found 564 misses with the same script on its tree.
  - MEASURED: the lead's 13 new mutants all die by their own tests.
  - My mutant that strips only space-indented comment lines survives (note 7).
- **R3-2, the engine test on POSIX.**
  - MEASURED (`logs\wsl_all.log`): the whole suite passes under WSL with round 3's two shims, 1,038 passed in 13 s.
  - MEASURED: `tests\docs` and `tests\tools` pass on Python 3.13.5, 293 passed. I borrowed pure-Python pytest from the 3.12 install through PYTHONPATH and downloaded nothing.

## The round's other changes
- **`packages`, a failing listing hashed uniquely.**
  - MEASURED (`scripts\t_resume.sh`, `logs\t_resume.log`), end to end with the real runner on a committed scratch copy and a stand-in SHACL engine:
    - Unchanged: `--resume` continues.
    - A package added: refused.
    - The package removed again: continues, same hash.
    - A nameless distribution: refused.
    - A METADATA not in UTF-8: the fresh run runs, and `--resume` of it is refused.
    - An engine path that names nothing: refused.
    - The main interpreter's own listing failing: refused.
  - The engine line and the interpreter line are both hashed through `packages`.
- **A named pipe or device unreadable.** MEASURED under WSL (`scripts\t_special_files.sh`, `logs\t_special_files.log`), round 3's gate against this packet's:

| State | Round 3 gate | This packet |
|---|---|---|
| FIFO at a tracked path | hangs | finding, exit 1 |
| FIFO at a gitlink's path | hangs | finding, exit 1 |
| /dev/zero (char device) at a tracked path | hangs | finding, exit 1 |
| Socket at a tracked path | finding | finding |
| Copy with no `.git` holding a FIFO, a socket and a device | hangs | three findings |
| Key staged, then the file replaced by a FIFO | hangs | finds the staged key |
| Untracked FIFO or socket | not listed by git | not listed by git |

  - MEASURED (`scripts\t_link_to_special.sh`): a link to a pipe, a device or a socket is read as its own text, with no hang and no false finding.
- **`need` removed and named by the rule.** READ and MEASURED by the guard fuzz and mutants. The only non-comment lines holding the word `need` are guard definitions and calls.
- **The reader's `isinstance` change.** MEASURED (`scripts\fz_profile.py`): 400 random edits of the Profile entity gave 28 accepted, 314 `graph-form`, 51 `spelling` and 7 `context`. There was no exception other than `Refused`.

## The privacy gate, once more
- MEASURED: round 3's commit-based oracle (`scripts\oracle3_r3.py`) against this packet's gate, under WSL with real links.
  - 3,600 random repositories: seeds 101 to 104 at 500 each, and 1101 to 1104 at 400 each with directory-file conflicts.
  - 0 misses, 0 crashes.
  - The 20 extras are all on assume-unchanged, skip-worktree or intent-to-add paths, the safe direction.
- MEASURED: an independent leak scan of my own (`scripts\scan_independent.py`, `scan_classify.py`) with shapes broader than the gate's.
  - It covered the 259 files and the clone's whole history, 524,727 added lines, plus the messages.
  - No key-shaped run of the IBM key's shape, no CRN value, no home path with a real name, no machine or network name.
  - The 66 UUID-shaped strings are one constant usage-metric id, not an instance id.
  - The CRN hits are the guard regexes in the three `ibm_*.py` tools.
- MEASURED (`scripts\fz_redos.py`): 2,255 pump inputs built from every alternative's own plant, up to 500,000 characters, gave no slow or super-linear case.
- MEASURED: on a linked worktree of my clone the gate reads 259 files and exits 0, the controls catch 37 of 37, and a key in a file over a gitlink is found.
- MEASURED (`scripts\t_junction.sh`): on this host, git descends into a junction and stores its files, and the gate finds the key behind one.

## Mutation
- MEASURED: the lead's 58 mutants (`check_ids.py` first, then `hm_t.py` on my copy): all 58 killed by their own targets (`logs\mut_lead.log`).
- MEASURED: my 12 mutants of this round's code (`scripts\m_r4.py`, `logs\mut_my.log`): 4 killed, 8 survived the whole suite. All 8 are test-reach notes or equivalents (note 7).
- MEASURED: runner differential fuzz (`scripts\fz_runner.py`, `logs\fzr_s11.log` to `fzr_s16.log`).
  - It makes a random single edit to the runner's stage region and runs the mutated runner under bash. Stage commands are stubbed, under five configurations. A baseline command that stops running counts as lost, and I asked whether any registry rule flags the text.
  - 2,837 mutants; 1,127 changed behaviour; 851 lost a baseline command; 829 were flagged by a registry rule.
  - 22 of the lost ones fail loudly, where the runner's exit status moves. 5 were silent and unflagged: notes 4 and 6.
  - The other changes that no rule flags either add an extra command or fail loudly: a guard removed from a stage not yet built, or a stray duplicated command line that runs outside any stage. A swap of the negative control's command with the blank line after it also falls here, because the checks of its row tolerate the blank line, but the runner then fails loudly.

## Notes (none blocks)
1. **[older; a scope gap, not stated as a limit]** The gate reads HEAD's messages but not the blobs of earlier commits.
   - MEASURED (`scripts\t_scope_gaps.py`): a key committed in commit 2 and deleted in commit 3 gives "privacy ok: 2 files and 3 commit messages read", while `git log -p -S` finds it.
   - A push would publish commit 2's tree. The gate's text claims only files git would commit and messages, so this is consistent with it, but a reader may assume push safety.
2. **[contrived, older]** A `git replace` ref shows another message for a commit.
   - MEASURED: the gate exits 0 while the real message holds the key.
   - BELIEVED: `git push` ignores replace refs. `--no-replace-objects` would close this.
3. **[older; pattern coverage]** Two spellings pass.
   - MEASURED: the forward-slash UNC to WSL (`<a home path>`, which `Path.as_posix` produces), and an encodeURI drive path whose colon stays (`<a home path>`).
   - The JSON-twice-escaped and 8.3 forms are found.
4. **[test reach, older]** The registry pins the lint stage's directories, not its program.
   - MEASURED (`scripts\t_lint_typo.sh`, `logs\t_lint_typo.log`): in a scratch copy I changed `python -m ruff check …` to `python - ruff check …`.
   - All 142 tests of the registry file pass. The real runner, with stdin from /dev/null and an unused import planted, prints `lint ok`, because `python -` reads an empty program.
   - With stdin attached it hangs: my own by-hand variant of the command hung until I stopped it.
   - The registry claims only that the lint names the directories, which still holds. A pin like the one on the pytest line would close it.
5. **[test reach, older; with prose]** No test executes the runner. The negative control exercises only the MUST_FAIL branch.
   - MEASURED (`scripts\t_failure_accounting.sh`): in a copy, changing `FAILED=$((FAILED+1))` to `+0` in the final else of `stage()` leaves all 1,038 tests passing.
   - With one stage's command failing, the original runner exits 1, and the mutated one prints `lint FAIL rc=1`, `failed 0`, and exits 0.
   - The registry's own stated limits name the runner's exit status. Its sentence "the negative control shows on every run that the runner can still fail", and the runner header's section 3, overstate this.
6. **[test reach]** Guards of stages not yet built are not required.
   - MEASURED: a deleted, commented-out, joined or misspelt `need_file` or `need_env` of p1-crates, p2-crates, p4-shacl, profile or instruments is not flagged. Each fails loudly once its directory, tool or variable is missing.
   - `--check` dropped or misspelt on the profile stage is unflagged while `tools/gen_profile.py` does not exist.
   - MEASURED (`scripts\t_profile_stub.py`): with a stand-in tool in a scratch copy, the registry flags both.
7. **[test reach]** Survivors of my 8 mutants, the shipped code right in each:
   - The special-file check before the link check. The shipped order is right (see "The round's other changes"), and no test pins it.
   - `^ *#`: a tab-indented comment line naming a guard would be flagged falsely.
   - Dropping the look-behind in the guard word.
   - Dropping `2&gt;&amp;1` in `packages`.
   - A failure token without the pid, and one with only the pid. Two separate bash processes get different pids, so the test cannot tell the clock and `$RANDOM` apart.
   - Two mutants equivalent in effect: dropping the `exists()` or the `is_dir()` clause of `committed()` changes only the error's name.
8. **[test reach]** The pipe test patches `is_file`. A POSIX host could make a real FIFO with `os.mkfifo`. The real hang is measured only by hand, above.
9. **[prose]** `verify/pytest-stage.sh`'s last message still says "(need/need_file/need_env in verify/run.sh)". `need` is gone. The script's command lines are pinned by hash, so an edit needs its pin changed. The runner header's list of departures from moth-quantum's runner omits the removal of `need`, which is told at the site. READ against moth-quantum 3a73823.
10. **[older]** CLAUDE.md's "~125 s" against 146 s measured on a shared machine; the lead noted this before, as not taken.

## What I did not do
- Native Linux or macOS (WSL only), Python 3.14, real symbolic links on the host (WinError 1314; I used a junction), a real pyshacl engine, hooks, sparse or partial clones, and the quick budget's timing.
- The full runner in a linked worktree this round (the gate and its controls only).
- The gate on moth-quantum's repository, because it might read a credential file. moth-quantum I read only for `bundle.py` lines 7 and 17, which match the study's edit, and for the runner's functions.
- The lead's WSL probes, `probe_listing.py` and `probe_nul.py`, and round 1 and 2's scripts. From round 3's I ran only `oracle3.py` and `fz_guard_forms.py`.
- P1's, P2's and P4's designs and worktrees, and the ledger.
- Slips:
  - **IBM job ids.** One listing of mine printed 66 file names under `records/`, which are IBM job ids. I should have masked them. Nothing was saved to a file, and I do not repeat them here.
  - **Host process list.** I listed host processes with their command lines once, to find my own hung child. That showed other parcels' command lines. I stopped only my own child.
  - **Harness order.** I ran the lead's harness before reading `m_p04.py`, `m_p04_r1.py` and `m_p04_r2.py`, which it loads. I read them afterwards: they hold only mutant definitions.
  - **Git Bash /tmp.** Two small list files went to Git Bash's /tmp early. I removed them.
- Cleanup and side effects:
  - WSL's `/tmp/qro-p04-r4v` is removed, which I checked.
  - In the real repository I ran only `git log` and `rev-parse` (with `--no-optional-locks`), `sha256sum -c`, and `git clone` from it. Nothing was written there.
- No key, token or CRN was read or printed whole. Every key was synthetic, built in pieces, and printed masked. Nothing was sent, nothing connected to IBM or Atlas, and nothing was pushed.
