# P0.6 verifier, round 3: NOT READY

One defect in what the code does, and one false sentence. The code defect is a regression: the round-2 fix for D1 makes the gate crash when it has no stdout. Everything else I attacked held, and the notes below are all under the bar.

Paths are relative to CK, which is `SCRATCH\verifier-P06-r3\check\`. Scripts are in `CK\probes\` and `CK\mutants\`. Logs are `CK\run-*.out`. Labels are READ, MEASURED (the command or script is named) and BELIEVED. Environment: Python 3.12.9, git 2.45.2.windows.1, Git Bash 5.2.26, ruff 0.11.9, pytest 9.1.1. Every key-shaped string and home path I planted was built in pieces at run time.

## Defects

### D1. [code, gate; a regression] The round-2 fix crashes the gate when stdout does not exist

**The fault (MEASURED).** The new line `sys.stdout.reconfigure(errors="backslashreplace")` at `tools/check_privacy.py:527` runs on every invocation. When `sys.stdout` is `None`, it raises `AttributeError: 'NoneType' object has no attribute 'reconfigure'`. The process exits 1 on a clean tree where 37640f0's gate and 8afeede's exit 0.

- **Closed descriptor.**
  - Command: `python tools/check_privacy.py &gt;&amp;-` in Git Bash, run in CK\clone-real (the real 294-file tree with history).
  - P0.6's gate exits 1 with the traceback. 37640f0's gate on the same tree exits 0.
  - The same result holds on a one-file tree (CK\probe1\t).
- **No console.**
  - Script: `probes\p_noconsole.py`, running `pythonw.exe tools/check_privacy.py` and `... --control`.
  - P0.6's gate exits 1 on both. The 37640f0 and 8afeede gates exit 0 on both.
- **Stdout that is not a TextIOWrapper.** `probe1\run_in_host.py` runs the gate in-process with `sys.stdout` replaced by a `StringIO`, the way IDLE or an IPython console does. P0.6's gate raises `AttributeError: '_io.StringIO' object has no attribute 'reconfigure'`. 37640f0's gate exits 0.
- **Not affected.** A pipe whose reader has gone exits 120 in both gates (`probes\p_brokenpipe.py`). The runner redirects stdout to a file, so it is immune; the runs below prove it.

**Why it counts.**
- The brief names "closed" among the stdout conditions to check.
- The lead's process test (`PYTHONIOENCODING=cp1252`, stdout a pipe) cannot see this.
- The comment above the line says "never a crash", which this falsifies.

**Limits.**
- It fails closed: a clean tree is refused. A tree with findings still exits 1.
- Practical reach is small. No hook is installed here, and the runner is unaffected.

**Fix, MEASURED on a copy (`probes\p_fixtry.py`).**
- Guard the line with `if sys.stdout is not None:`, or use `getattr(sys.stdout, "reconfigure", None)`.
- A portable test shape tells the two apart: a process that sets `sys.stdout = None` and `runpy.run_path`s the gate as `__main__`. The shipped gate exits 1 in both modes; the guarded copy exits 0.

### D2. [prose] The reason given for leaving the `need_env` half undone is false for the `instruments` stage

**The claims.**
- The registry docstring says "the variable is read by the stage's tests, not on its line, so no rule here derives it".
- The third P0.6 ledger entry says "But no stage's line reads its variable; the stage's tests do."

**The fault (READ, then MEASURED).**
- `verify/run.sh` line 414 is the instruments stage's own command: `python tools/check_instruments.py "${QRO_MOTH_ROOT:-}"`. It reads the variable on its line.
- `probes\p_needenv_derive.py` implements the rule the lead "had meant": a stage whose line reads `${NAME:-}` needs a `need_env NAME` before it. It flags nothing on the shipped runner. It flags exactly the deletion of the `need_env QRO_MOTH_ROOT` before the instruments stage.
- The registry passes that deletion (mutant n3, all 153 registry tests pass). So the residual is narrower than stated: p1-crates, p2-crates and p4-shacl only. The instruments case was derivable.

**A second wrinkle (MEASURED, mutant n4).** "Deleting one passes here" is not true of the test run for `QRO_SHACL_PYTHON`. Deleting that call fails ten plants in `test_a_guard_called_in_another_form_is_caught`, but only because they use that line as their text anchor. No rule requires the guard.

## What held

1. **The freeze and the setup.**
   - MEASURED: `SHA256SUMS.txt` begins `dcb648d969b23969`. 294 of 294 files are OK at start and end, with no caches under `frozen\`.
   - MEASURED (`probes\p_idx_vs_tree.py`): `frozen\tree` equals the real repository's index blob for blob, 294 against 294.
   - MEASURED: the real repository ended at HEAD 37640f0 with the same 14 staged paths and no lock. moth-quantum ended clean at 3a73823.
2. **The runner, in three copies.**
   - Command: `QRO_MOTH_ROOT=&lt;moth-quantum&gt; bash verify/run.sh`.
   - Copy 1: the real repository cloned with `--no-local --no-hardlinks`, its remote removed, tree laid over it and committed (`run-clone.out`).
   - Copy 2: a `git init` copy with one commit (`run-gi.out`).
   - Copy 3: a `git init` copy with no commit, run as "nocommit+dirty" (`run-gi2.out`).
   - All three: 18 stages passed, 6 skipped by name (p2, p4, p1-crates, p2-crates, profile, p4-shacl), exit 0.
   - Test counts match the ledger exactly: docs 175, tool-tests 177, vocab-tests 12, format 958, custody 23, p1 1,169, control-tests 32, total 2,546.
   - The clone's privacy line reads 294 files, 8 commit messages (the ledger's 7 plus my overlay commit) and 118 versions in earlier commits, plus 2 known. Controls: 40 of 40 caught in all three copies.
3. **D1 and the code pages (MEASURED, `probes\p_stdout.py`).**
   - A binary file named in CJK and emoji characters, in the tree and in an earlier commit only.
   - `PYTHONIOENCODING` unset, ascii, cp437, cp850, cp932, cp936, cp1252, latin-1, utf-8, utf-16, utf-32, `cp1252:strict`, `utf-8:strict`, `ascii:replace`; stdout a pipe, a file, NUL; plain and `--control`.
   - Every run exits 0 and writes the escape.
   - 37640f0's gate crashes on the tree variant under every code page that cannot encode the name.
4. **The new process test against the fault it names (MEASURED, mutants g1 and g2).** Removing the reconfigure, or making it `errors="replace"`, each fails the test.
5. **The notes taken (MEASURED, mutants g3, g7b, g6b, g10b, g5).**
   - `history()`'s `cat-file --batch` failure arm returning no finding is killed.
   - Losing the replace flag on `rev-list`, on `cat-file --batch-check`, on `cat-file --batch`, or everywhere is killed in each case.
   - Two of my first replace mutants survived only because git reads `GIT_NO_REPLACE_OBJECTS` as set-or-unset, so `"0"` is not "off". My error; redone by removing the variable.
6. **The history reader.**
   - **Coverage (MEASURED, `p_pushset.py`).** A push of HEAD on the real clone sends 412 blobs. The gate reads 118 history blobs and 294 index blobs: 0 missed, 0 extra.
   - **Directed shapes (`p_shapes.py`).** An unrelated-histories merge, an octopus, `-s ours`, an annotated tag checked out detached, empty commits, a revert, a symbolic-link blob and a merge in progress. Every key blob is pushed and found. In the merge in progress the key is only in the working file and is found there.
   - **Names (`p_lfnames.py`, `p_badnames.py`).** Line feeds and carriage returns at every position, top level and nested: 17 key blobs, all pushed, read and found. Eleven non-UTF-8 and odd names are found, with no crash under cp1252 or utf-8.
   - **Encodings and size (`p_big.py`).**
     - Found: UTF-16 and UTF-16-BE with a byte-order mark, UTF-32, UTF-8 with a mark, cp1252, and a 20 MB text blob with the key at its end (13.9 s, about 1.4 MB/s).
     - Listed by name as binary, as the docstring says: UTF-16 without a mark, and a binary blob with the key in the clear after byte 4,096.
   - **Shallow clones (depth 1, 2, 3, 5).** All exit 0. The known list is inert at depth 1, as stated.
   - **The two `git init` copies.** Both pass the privacy stage.
7. **The known list (MEASURED, `p_known.py`, plus a put-back test).**
   - The key resolves to blob 7671e68, which is round4.md as pushed in 20d40e6.
   - Its SHA-256 is `d014f919…`, matching the P0.4 README. Undoing the two redactions in the current file reproduces it byte for byte.
   - Over all 118 history-only blobs, the only findings are its two. Both sit on line 94 of the blob, and each ends in the placeholder `name`: the forward-slash UNC to WSL and the encodeURI drive path. Neither is a secret.
   - `KNOWN` is read only in the history loop (READ).
   - I put the pushed bytes back as an unstaged working file, as a staged version, in a new commit, and as a file equal to the index. Each exits 1, with no known excuse.
8. **The three spellings.**
   - Real encoders (`p_encoders.py`):
     - `Path.as_posix` of a WSL UNC path is found by `wsl-unc-slash`.
     - `Path.as_uri` of a WSL UNC path is found by `wsl-file-url`.
     - `encodeURI` of a drive path, also after `%20`, and `quote(safe=':')` are found by `url-quoted-drive`.
   - A URL whose host is named wsl, and a scheme ending in a letter before an encoded path, are not found.
   - Edges (MEASURED, m3d): 21 of my 22 mutants of the three patterns are killed; the one survivor is note 3 below.
9. **Pipes and links.**
   - READ: `committed()` is unchanged.
   - MEASURED (mutants e1 and e2): moving the pipe check before the link check is killed, and removing the pipe check is killed.
10. **The runner and the registry.**
    - MEASURED (mutants e3 to e6): a failing stage counted as a pass, the runner exiting 0 on failure, the stage's return code lost, and the summary hiding the count are each killed by the end-to-end test.
    - MEASURED (mutants e8 and e9): the derived guard rule is held in both directions. `p_built.py` shows it silent once a parcel has built its directory, and naming the stage when nothing is built and the guard is gone.
    - The lint pin's fourth word is near-equivalent (mutant e7), because the finder needs "ruff check" on the line.
    - The tab-indented comment line and the guard-word tests are READ; the lead's runs pass them.
    - `verify/pytest-stage.sh` against moth-quantum 3a73823 (diff): differs only in the header, the `pytest_plugins` refusal, the three pytest options and the last message. `need` is in moth's runner and not here. The pinned hash changed because exactly one command line changed (the echo message).
    - The runner's header and the registry's docstring no longer carry "proves the runner can say no". The only remaining line is correctly scoped.
11. **Unintended changes (MEASURED, `p_diff_fuzz.py`).**
    - 37640f0's gate against P0.6's on 140 random repositories: working files, staged versions, odd names, UTF-16 and BOM files, messages, and history.
    - Outside the history reader and the three new spellings the two gates agree, in findings, summary clauses and the non-history `not read:` lines.
    - My first pass reported 13 false differences, all the history binary blobs the summary now counts by design. I corrected the comparison.
    - The only unintended change I found is D1.
12. **CLAUDE.md's timings (note 10).**
    - The quick budget ran in 172 s of stage time beside other work (`run-clone-quick.out`), against CLAUDE.md's "~170 s".
    - The full runs took 273, 248 and 267 s with two at once beside other sessions, inside "150 to 365 s".
    - I did not re-measure the idle figures.
13. **Prose.**
    - The review READMEs hold: both source SHA-256s match (`fcff311e…`, `ecbe14f2…`). `round1.md` holds no escape. `round2.md` holds `&amp;gt;` twice and `&amp;lt;` once. It holds one `&lt;scratch&gt;` and two `&lt;a home path&gt;`, and a character-level diff of the placed file against the source shows only those changes.
    - The ledger arithmetic holds: 2,546 is 59 more than 2,487, and the stage counts sum.
    - "No non-ASCII name in this repository's history" is true (0 of the history lines and 0 of the tracked paths).
    - The gate's docstring claims check against the code, except the one comment in D1.
    - I saw no TODO, skip, xfail, noqa or pragma among the added lines. The changed files have no CR bytes and no trailing-space lines.

## Notes (below the bar)

**Test reach, where the code is right**
1. No test holds that a history path that is not UTF-8 is read with its name decoded with replacement. The docstring states it, and the lead listed it as not taken. The code does it (`p_badnames.py`).
2. `history()`'s `if types.returncode != 0: return None` arm is held by nothing (mutant g9). No real damage reaches it; the second verifier said so too.
3. The lookbehind `%[0-9A-F]{2}` widened to any two letters survives (mutant s22). No test has a percent sign followed by a non-hex pair.
4. `privacy-controls`' 40 controls do not watch the history reader or the staged reader; `tool-tests` do (mutants g3 and g8 are killed there). No sentence claims otherwise.

**The gate: shapes that pass, all older or inside the docstring's "no alternative names it / encoded other than as a listed alternative says" (MEASURED, `p_gaps.py`, `p_encoders.py`)**

5. An encoded space (`%20`) directly before a POSIX, Git-Bash or WSL-mount home path passes. The lead lifted the digit lookbehind for the drive form only; `encodeURI` of a sentence produces this form.
6. A drive path percent-encoded with a name that begins with an encoded non-ASCII letter passes `url-quoted-drive`. This is the second verifier's older note 11, now also true of the new alternative.
7. `quote()` of an `as_posix` WSL path turns `$` into `%24`, which `wsl-unc-slash` does not accept, though `wsl-file-url` does. A file URL that runs through the WSL host's `/mnt/c` to a Windows profile also passes, since `wsl-file-url` wants `home` or `users` right after the distro.

**Other**

8. The new line replaces a user's explicit `PYTHONIOENCODING=…:strict` or `:replace` errors handler. This is by design and trivial.
9. CLAUDE.md dates the idle figures "(2026-10-16)". That matches the commit that carried them (ecb7e5e, 2026-10-16 03:35). The ledger's entry that measured them sits under a 2026-10-15 heading. The ledger's own headings are out of order, so I cannot say which day is right. Not counted.
10. Mutation summary: I wrote 45 valid mutants of my own (`mutants\m3a.py` to `m3e.py`, run by `hm3.py`, which runs the targets unmutated first). 39 were killed and 6 survived. The survivors are the dead arm (g9), the lookbehind (s22), the lint pin's fourth word (e7), and three `need_env` deletions (n1 to n3), which are D2. I did not re-run the lead's 58.

## What I did not do

- I did not run native Linux or macOS, WSL, Python 3.13 or later, a hook, a sparse checkout, or a partial clone (none this round).
- I did not run a real push. `git pack-objects --revs` stands in for one.
- I did not read or run the lead's scripts or mutants. I worked from the frozen tree and the real repository's index.
- I did not check the claim that P1.1's 21 files and P4's 51 hold no finding, because those files are off-limits to me.
- I did not re-measure the idle timings.
- I did not touch the worktrees, the ledger or the other verifiers' directories.

**Slips**

- A grep count of CR bytes was wrong from shell quoting. I recomputed with Python: 0 CR bytes.
- One in-process test printed an error message that included my scratch path in my own console. Nothing was saved to a file or put in this report.
- A write to a root-level temp file was refused. It had no effect.
- No IBM job id was printed, and no key, token or CRN was read or printed.

Nothing was pushed or contacted. My clones had their remotes removed before I committed in them.
