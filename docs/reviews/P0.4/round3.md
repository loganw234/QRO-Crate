# P0.4 verifier, round 3: NOT READY

**Defects.** I found two. Both are small and have a measured one-line fix.
- R3-1 is a hole in the new registry rule that every guard is called in one form. A sentence in the tree is also false because of it.
- R3-2 is a new test that fails on POSIX. The suite was green there at 7f40400.

**The privacy gate.** I found no defect in it. R2-1's fix holds against everything I tried (details under "What holds").

Paths below are relative to `SCRATCH\verifier-P04-r3\check\`. Scripts are in `scripts\` and logs in `logs\`.

## Freeze and setup
- MEASURED: `sha256sum -c` gave 258 OK at the start and at the end. The sums file begins `7d55f20a65227d4f`, and its file list equals the tree's.
- MEASURED: the real repository's working tree equals the packet byte for byte. I ran `sha256sum -c` from there, read-only.
- Slip: two of my probes (`fz_guard_forms.py`, `fz_comment_reads.py`) imported modules from `frozen\tree` under `python -I`, which ignores PYTHONDONTWRITEBYTECODE. They wrote 12 `cpython-310` `.pyc` files there.
  - I removed all of them and re-ran the checks above afterwards.
  - Nothing else ran inside `frozen\`.
- MEASURED: the full runner (`scripts\run_full.sh`) gave 17 passed, 7 skipped by name, 0 failed.
  - On a clone plus the frozen files it took 160 s (`logs\run_clone_full.log`).
  - On a linked worktree of it, 142 s (`logs\run_wt_linked_full.log`).
  - Every figure equals the entry's:
    - docs 154, tool-tests 127, vocab-tests 11, format 679, custody 23, control-tests 32 (1,026 tests);
    - privacy 258 files, 4 messages, 14 staged versions;
    - privacy-controls 37 of 37;
    - check-docs 10, 40 and 35;
    - the twin ACCEPTED `21fafec5…`;
    - instruments 5 of 5.
  - `--budget quick` gave 14 passed, 4 skipped, 0 failed in 82 s. Its composition equals CLAUDE.md's list.
  - I neither confirm nor refute "~70 s" and "~125 s", because the machine was shared.

## Defects

### R3-1 [gate; the registry's guard-form rule, with a false sentence in the code]
The rule that every `need_file` or `need_env` call is in the one form the rules read has a hole. `guards_off_form` strips comments with the shared `COMMENT` pattern, and that pattern also strips a quoted ` #`. A guard called after any command on the same line that holds a blank and then `#` inside quotes is stripped out of sight. No rule then reads it.

- READ: `tests\docs\test_stage_registry.py` line 394 says a quoted `#` "ends what is read too, which can only flag more". That is true for the `need_env` read rule. It is false for `guards_off_form`, where stripping more hides more.
- READ: the false claims are the module docstring (line 36), the `guards_off_form` docstring (line 435), and the ledger entry ("A new rule fails every call… after another command", `docs\VALIDATION.md` line 2303).
- MEASURED fault, in `plant1` (a copy of the tree with one line added before run.sh line 365): `echo "see #1"; need_env QRO_SHACL_PYTHO "misspelt, so it skips p4-shacl by name for ever"`.
  - `guards_off_form` returns `[]` and `guard_problems` returns `[]`.
  - `bash verify/run.sh --only docs` in the copy prints `docs ok` and 154 passed.
  - With `tests\p4shacl\test_p4shacl_probe.py` added and `QRO_SHACL_PYTHON` set, `--only p4-shacl` prints `SKIP misspelt, so it skips p4-shacl by name for ever`. The same tree without the line (`ctl1`) prints `ok`.
- MEASURED extent, with bash as ground truth (`scripts\fz_guard_forms.py`, seeds 1 to 3, under WSL): 564 of 4,304 chunks that make bash call a guard pass every rule.
  - Every one of the 564 has a blank and then `#` earlier on the line, inside quotes.
  - I found no other family.
- The trigger is contrived. By the brief's definitions it is a gate passing a fault it claims to catch, and a false claim.
- MEASURED fix: in `guards_off_form`, strip only whole-line comments, `re.sub(r"^[ \t]*#.*$", "", line)`.
  - The 23 guard and comment tests still pass.
  - The fuzz then finds 0 misses in 3,035 chunks.
  - Add a plant such as `echo "a #b"; need_env QRO_SHACL_PYTHO "x"`, and correct line 394.
  - The alternative is to restate the claim as a limit.

### R3-2 [gate; the `docs` stage, in test code]
`test_the_engines_line_changes_with_its_packages` (line 562) fails on any POSIX host.
- READ: `engine.write_text(...)` at line 573 writes the stand-in engine without an execute bit.
- MEASURED (`scripts\t_engine_exec.sh`): `"$QRO_SHACL_PYTHON" -I -c …` then prints `Permission denied`. That text is what gets hashed, so the four lines are equal and `assert len(set(seen)) == 4` fails.
- MEASURED (`scripts\t_wsl_all2.sh`, WSL Ubuntu, Python 3.10.12, pytest 9.1.1, git 2.34.1, bash 5.1.16).
  - WSL's Python 3.10 lacks `tomllib` and WSL has no `python` command, so I used two shims: a `python` on PATH and a `tomllib` that re-exports `tomli`.
  - 7f40400 passes 984 of 984.
  - The frozen tree passes 1,025 and fails exactly this test (`logs\wsl_all_r3b.log`, `logs\wsl_all_base.log`).
- MEASURED fix: adding `engine.chmod(0o755)` makes it pass (`scripts\t_wsl_fix_engine.sh`).
- The suite has POSIX branches in five places (READ: grep for `os.name`), and the repository is public. No document claims Linux as a target. P0.4 is what turned the suite red there.

## What holds

**1. R2-1's fix.** MEASURED: `scripts\g1_gitlink_states.py` ran 28 states on the host (git 2.45.2, Python 3.12.9 and 3.13.5, `logs\g1_host.log`, `logs\g1_host_py313.log`) and under WSL (git 2.34.1, `logs\g1_wsl_links.log`, `logs\g1_wsl_dirs.log`). Each state was compared with what a real `git add -A` stores.
- A file at the gitlink's path (clean, with a key, with a home path, UTF-16, empty): read. The key and home path are found.
- A binary file there: listed by name, which is the stated limit.
- A symbolic link there (to a file, to a directory, dangling, a loop, to a nested repository): read as its own text.
- A directory there (empty, with files and no `.git`, with a repository, with no commit, with a `.git` file, with an empty or garbage `.git`): named nested, not read. git commits nothing from it, or only the gitlink, or stops with `fatal`.
- A junction there: treated as a directory. Nothing is nested wrongly.
- Nothing there: named nested. git removes `sub`.
- A gitlink `Sub` over a file `sub`, on the case-insensitive host: found.
- Round 2's gate misses the file and link cases in the same runs. This packet misses none.
- MEASURED: the random-repository oracle (`scripts\oracle3.py`, adapted from round 2's) commits with `git add -A` in a copy and reads every blob at any path.
  - It ran 1,870 repositories: 1,600 under WSL with real links, 150 on the host, and 120 on Python 3.13.5. The WSL runs included directory-file conflicts.
  - There were 0 misses and 0 crashes.
  - The 5 over-reads are all on assume-unchanged or skip-worktree paths, which is the safe direction.
  - The same oracle on round 2's gate, seed 201, finds 37 misses at gitlink paths. So the oracle is sensitive.
- MEASURED: the real `privacy` stage on a linked worktree fails (rc 1) with a key in a file over a gitlink.
- MEASURED: the 47 history shapes of round 1 (`logs\s2_hist_r3.log`) all come out as expected, with the same verdict rows as round 1's run.

**2. The notes taken.**
- N1: MEASURED (`scripts\fz_comment_reads.py`, 164 valid lines): the comment rule agrees with bash for every opener I tried.
- N2: the seven forms are caught. The hole is R3-1.
- N3 and N4: mutants of each site die by their own tests.
- N5: the float is planted and refused `graph-form`.
- N6 and N7: the old, the first-fix and the new expressions give the same hash on this host (`fbb6906946dda12b`).
- N8 and N9: the stated limits are true. MEASURED:
  - For commit encodings, `scripts\t_commit_enc.py` shows UTF-16, UTF-16LE and UTF-16BE with a non-ASCII word, and IBM037 and IBM500, lose the key. All of these lie inside the stated class.
  - A NUL in a message cuts it, by the lead's `probe_nul.py`.
  - A non-UTF-8 file name makes both modes exit 1 with a traceback, never a pass.
  - In a copy with no `.git`, a link to an existing directory is neither read nor named, and a dangling link is read.
- The reviews' README is right. MEASURED: round1.md's SHA equals the source's, round2.md differs from its source by one redacted home path, the escape claims match, and both files end in one line feed.
- MEASURED: the ledger edit is a pure append.

**3. Corrections and "Not taken".** They hold, with three small exceptions, which are in the notes below.

**4. Unintended changes.** I found none.
- The four gate versions agree on the real clone.
- 7f40400 passes the same oracle.
- The runner's `--resume` still refuses a newly named engine and an added package. This was on a committed copy, with a valid distribution as the control.

**5. Mutation.**
- MEASURED: the lead's 45 mutants, run with my harness (`scripts\mut.py`) that records which tests fail. All 45 are killed by their own target tests, and `check_ids.py` confirms each text occurs once.
- My own 19 mutants (`mut\m_r3.py`, `logs\mut_my.log`): 8 killed, 11 survive even `tests\tools` and `tests\docs`. The survivors are test-reach notes. The shipped code is right in each.

## Notes

**Test reach, with the code right.**
- `lexists` → `exists` in `held()` survives every test.
  - MEASURED under WSL (`logs\g1_wsl_mexists.log`): with the mutant, a dangling link at a gitlink's path whose text is a home path or a key exits 0 while git commits it.
  - The simulated links in the tests all have an existing target. A test could also patch `os.path.lexists`.
- In `COMMENT`, only the line start, the blank, `;` and `&amp;` are held. The arms for tab, `|`, `(`, `)`, `&lt;` and `&gt;` are unheld.
- The "to the line's end" arm of `GUARD_CALL` is unheld. A second call on the same line passes with `".*"`.
- The comment stripping in `guards_off_form` is unheld, because no runner comment names a guard.

**Gate, older than P0.4.**
- `need`, the command guard, is neither pinned nor read, and no call of it exists today.
  - MEASURED in `plant2`: `need zz_no_such_command "…"` passes both rules and skips `p4-shacl` by name even with the engine named.
  - The new rule's wording fits `need_file` and `need_env` only.

**Code, runner, older than P0.4 and the same class as D1 and N6.** `PACKAGES` still hashes a traceback for a distribution whose METADATA is not UTF-8, even only in an `Author` line.
- MEASURED on 3.12.9 and 3.13.5 (`logs\t_packages_expr.log`): rc 1, stdout empty.
- MEASURED end to end: with such a distribution on PYTHONPATH, `--resume` continues after a valid package is added, at this packet and at 7f40400. The control with valid distributions is refused.
- State it as a limit, or have the runner refuse when the listing exits non-zero.

**Code, older.** A FIFO at a gitlink's path or a tracked file's path hangs the gate (MEASURED, 8 s timeout, `scripts\t_fifo.sh` and `scripts\t_fifo2.sh`).
- Base, round 1 and this packet hang, and round 2 does not.
- git itself refuses to add a FIFO.

**Prose.**
- "As the entry before said: such a skip says its own reason" is not what that entry said. It said the reason was "not its own", before the new rule.
- "The six mutants… equivalent or redundant" includes the tab mutant, which is not equivalent. It survives and changes the answer for a comment after a tab.
- "Each of those seven is planted, its variable misspelt": the seventh plant is a `need_file` with a missing path, and has no variable.
- The runner comment on `PACKAGES` says a missing package "hides every package after it". It hides all of them.
- The same comment says "indexed, it raised TypeError". The raise came from adding None to a string, not from the indexing.
- "In a copy with no git history" in the gate's docstring means a copy with no `.git`. A repository with no commits reads links as text.
- Not checked: the two meanings ("the job", "the Pub") and "and its coherences". They rest on P1's and P2's designs, which I did not read.

## What I did not do
- Native Linux or macOS. WSL served for links and for the pytest comparison. It has git 2.34.1 and Python 3.10.12, and needed the two shims named under R3-2.
- Python 3.14, or pytest on 3.13.5.
- Real symbolic links on the host (WinError 1314).
- A real pyshacl engine.
- Hooks, sparse checkout or partial clones.
- The gate on moth-quantum's repository, because it might read a credential file.
- The lead's `hm_t.py` and WSL probes, and brief-r3.md. I used my own harness and states probe. I read the lead's `m_p04*.py` files, `check_ids.py` and `probe_nul.py` before running them, and ran `check_ids.py` and `probe_nul.py`.
- The worktrees, the ledger, and P1's and P2's designs.
- I read the tail of `s2_hist_copy.py` after I had run it. It only touches its own temporary directories.
- Other slips:
  - Small file lists went to Git Bash's `/tmp`, now removed.
  - My WSL `/tmp/qro-p04-r3` is removed. `/tmp/qro-p04-r2` there is round 2's and untouched.
  - In the real repository I ran only read-only commands (`git status`, `log`, `show`, `ls-files`, and `clone` from it). `git status` may refresh the index's stat cache. HEAD is still 7f40400.
- No key, token or CRN was read or printed. Every key was synthetic and built in pieces, and no job id appeared. Nothing was sent anywhere, and nothing was pushed.
