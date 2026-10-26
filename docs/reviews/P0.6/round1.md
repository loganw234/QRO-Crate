# P0.6 verifier, round 1: NOT READY

The privacy gate's new history reader has two defects. It silently drops blobs stored under a top-level name that begins with a line feed. It also refuses a clean repository that has a file or directory named `HEAD` at its root. Two claims in the tree are also false. Everything else I tried held, and I list that below.

Paths below are relative to `SCRATCH\verifier-P06-r1\check\` (scripts in `probes\`, logs in `logs\`). Labels are READ, MEASURED (script or log named) and BELIEVED. Every key and home path I planted was built in pieces at run time.

## Freeze and setup
- MEASURED: the brief hashes to `7a67a7725c9a3b8e`, and `SHA256SUMS.txt` begins `516a37128c8e8833`. 265 of 265 files are OK at the start and at the end. Nothing under `frozen\` holds bytecode or caches.
- MEASURED: `frozen\tree` equals the real repository's index, blob for blob. Same 265 paths. The nine changed files have no CR byte, a final line feed, no mode change, and `git diff --cached --check` is clean.
- MEASURED: the real repository ended as it began: HEAD 8afeede, nine staged paths, no lock file. moth-quantum stayed clean at 3a73823.
- Environment: Python 3.12.9, git 2.45.2.windows.1, Git Bash 5.2.26, ruff 0.11.9, pytest 9.1.1. WSL: Python 3.10.12, git 2.34.1.
- The runner passed (17 passed, 7 skipped by name, 1,342 tests) in all four trees below.
  - A `git init` copy: `logs\run_gi.log`, 229 s of stage time.
  - A clone of the real repository with tree laid over it and committed: `logs\run_clone.log`, 233 s.
  - Depth-1 and depth-2 shallow clones of that: `logs\run_shal1.log` and `logs\run_shal2.log`, about 370 s each, with four runs at once.
- The counts match the entry: docs 175, tool-tests 142, vocab-tests 12, format 958, custody 23, control-tests 32. The privacy line in the clone reads 265 files, 113 earlier versions and 2 known findings. In the real repository's staged state, the gate printed 6 messages, 113 versions and 2 known (read-only run).

## Defects

### D1. [code, gate] A key under a name that begins with a line feed passes the gate
- `git rev-list --objects` writes `oid name` with the name cut at its first line feed.
  - A top-level name that begins with a line feed comes out as `oid ` with an empty name.
  - `history()` keeps a line only `and path` (`tools/check_privacy.py:291`), so the blob is dropped before any read and before any listing.
  - The same happens to everything under a top-level directory whose name begins with a line feed.
- MEASURED, `probes\p_lf_pack.py`, for a synthetic key committed as `\nkeys.md` and deleted in the next commit:
  - `rev-list --objects HEAD` lists the blob.
  - `pack-objects --revs` of HEAD, unpacked into an empty bare repository, holds the blob. A push sends it.
  - The gate run as a process printed `privacy ok: 2 files and 2 commit messages read; 0 binary files not read` and exited 0.
- MEASURED, `probes\p_oddnames.py`: a leading-line-feed name and a name that is only a line feed give 0 key findings (the plain name gives 2). A line feed in the middle is cut at that point and still found.
- MEASURED, `probes\p_history_fuzz.py 4 80 --odd --lf`, `logs\fuzz_s4_oddlf.log`: 42 of 80 repositories had a miss, every one at a name that begins with a line feed.
  - Under WSL (git 2.34.1): 27 of 60.
  - With the condition dropped (patched copy in `gate-fixed\`): 0 of 80 and 0 of 60.
- Why it counts as a defect:
  - The brief names a path holding a line feed.
  - The docstring says "every blob that history holds and the index does not" (lines 14 and 277).
  - The comment at lines 289–290 says such a path "leaves a line that is no oid". Git does not do that; it cuts the name.
  - No test has a path holding a line feed.
  - The threat model is accidental publication, and a name like this is unlikely by accident.
- Fix, MEASURED on `gate-fixed\check_privacy.py`: drop `and path` and label an empty name, e.g. `path.decode(...) or "(a path beginning with a line feed)"`.

### D2. [code, gate] A clean tree with a file or directory named `HEAD` at its root is refused
- `history()` runs `git rev-list --objects HEAD` with no `--` (line 284).
  - When the root holds a file or directory with that name, git exits 128 with `ambiguous argument 'HEAD': both revision and filename`.
  - Case-insensitively here, `head` triggers it too.
  - The gate then reports `earlier commits' files: unread, as git could not list or read them` and exits 1, with nothing to find.
- MEASURED, `probes\p_headfile.py`. `git log` and `git rev-parse HEAD` are not affected. `rev-list --objects HEAD --` exits 0.
- It fails closed, so no key passes. It is a wrong refusal in a gate, and a root name like that is unusual.
- MEASURED, `fix-try\` (frozen tree with both fixes) and `logs\fixtry_tools.log`: with D1 and D2 fixed, tests/tools gives 141 passed and 1 failed. The one failure is `test_a_blob_git_lists_in_the_history_and_does_not_hold_is_a_finding`, which matches the exact `rev-list` arguments (`cmd[-3:]`) and needs updating when `--` is added.

### D3. [prose] The entry and a test docstring say a failure is unreachable; it is reachable
- `docs/VALIDATION.md` lines 2888–2890 say the staged reader's arm for a `cat-file` failure "is reached by no real repository now". The docstring of `test_git_failing_to_read_the_staged_objects_is_a_finding` (`tests/tools/test_tools.py` 487–490) says no broken repository the test can make has it fail where `git ls-files` does not first, "a failure no test can make".
- MEASURED, `probes\p_staged_arm.py`: cut a staged blob's loose object file to half its length.
  - `git ls-files --stage` exits 0.
  - `git cat-file --batch` exits 128.
  - The gate says `staged versions: unread, as git cat-file failed`.
- Corrupt packed-refs, the case the entry has in mind, does now read: rc 128 without the flag, 0 with it. The code is right; the claim is wrong, and a real test is easy.

### D4. [prose] The registry docstring still carries the claim the entry says is gone
- `docs/VALIDATION.md` 2906–2907 say the registry's docstring "no longer" says the negative control shows the runner can fail.
- `tests/docs/test_stage_registry.py` lines 12–13 still say a negative control's stage "proves the runner can say no". That is the claim note 5 asked to remove, and it contradicts the stated limit at lines 48–50.

## Notes (none of these alone blocks)

**Test reach where the code is right.** MEASURED with `mutants\m_my.py` and my harness `mutants\hm_mine.py`, which runs a baseline first (both directories pass). Of my 24 mutants, 10 were killed and 14 survived the whole of tests/tools or tests/docs. Log: `logs\mut_mine.log`.
- `history()`'s three gits can lose the replace-ref flag and the repository-variable cleaning, one at a time, unseen. The replace test covers `git log` only, and the `GIT_DIR` tests have one commit, so `history()` reads nothing there. The same loss in `staged()` and `index()` is killed.
- The 64-hex arm for SHA-256 repositories survives. The code works (`probes\p_sha256.py`).
- `KNOWN` excusing a staged version, or a current file, survives in both cases. The code excuses neither (READ; `probes\p_known.py`).
- The two spellings are thinly held.
  - `wsl-unc-slash` without `.localhost`, the form Windows 11 shows, survives. So does its lookbehind without the dot, the slash, or the letters and digits.
  - `url-quoted-drive` with one separator, with no name required (a placeholder would match) and without the `%2F` branch also survive.
- The lint pin's fourth word is held by nothing, but it is nearly equivalent.
- The lead's 30 mutants: 30 of 30 killed, reproduced with `hm_t.py` (`logs\mut_lead.log`).

**Known list.** MEASURED, `probes\p_known.py`.
- `KNOWN` has two entries, one blob, two alternatives. The id resolves to round4.md as pushed in 20d40e6.
- The blob has exactly those two findings. Both sit on one line with the placeholder `name`. Broad scans found no address, no drive path, and no owner name.
- The pushed copy put back as a working file, staged, or committed again is flagged each time.
- A wrong entry fails the gate on the clone's history (`probes\p_known_mut.py`).
- The README's claim is exact: undoing the two redactions reproduces the pushed blob (`d014f919…`).

**Spellings** (`probes\p_spell.py`).
- Both alternatives find their intended forms in many contexts. Neither finds a URL whose host is named wsl, nor a scheme ending in a letter before an encoded path. Pump inputs of up to 500,000 characters ran in under 0.8 s.
- Passing every alternative: a `file:` URL to the WSL host in the forms a browser or `as_uri` shows, and an encodeURI drive path after an encoded space (the digit before the letter blocks the lookbehind). The URL case is what the brief says to exclude. The encoded space is a gap in "as encodeURI leaves it".

**Prose.**
- CLAUDE.md item 3 and the runner's `privacy` stage description (`verify/run.sh:406`) do not say the gate now reads earlier commits' blobs. A contributor who commits a path and deletes it next gets a permanent failure and no hint.
- "Nothing in it touches P0.5's files" is loose: CLAUDE.md and docs/VALIDATION.md are files P0.5's commit changed too, in other regions.
- CLAUDE.md's "150 to 365 s" low end is not in the lead's P0.6 logs I may read (those show 194–364 s of stage time for full runs). My two simultaneous full runs took 229 and 233 s. The quick budget took 143 s on a shared machine (`logs\run_clone_quick.log`), which fits "about 170 s".
- Everything else in the entry that I could check held: the test arithmetic (1,318 + 24 = 1,342), `origin/main` at 8afeede, the shallow-clone figures, the 30-mutant list, and the stage script's and runner's departures from moth-quantum 3a73823 (diffed).

**Other.**
- Cost: the history is read at about 1.5 MB/s, and every history blob is held in memory at once (MEASURED, `probes\p_big.py`).

  | History | Time | Peak (Python) |
  |---|---|---|
  | 120 versions of 1 MB | 78 s | 380 MB |
  | 20,000 small blobs | 26 s | not measured |
  | one 100 MB blob | 62 s | not recorded (the figure was taken before the gate ran) |

  Fine today (4 s for this history), but it grows with history.
- In a blobless partial clone, `cat-file` fetches missing blobs from the promisor remote: 42 s from a local remote. It fails closed when the remote is gone (`probes\p_clones.py`).
- MEASURED: with stdout piped and no UTF-8, a Chinese-named binary file crashes the final print with a `UnicodeEncodeError`. This is older (8afeede's gate does the same for a current file). The history reader widens it, and the runner is protected by `PYTHONIOENCODING`.
- Nested-runner test, MEASURED: `lint_copy` hand-lists the lint's directories, and ruff exits 1 for a named directory that is missing, so a new top-level directory in the lint line fails the clean case until the list is updated.
- The registry still accepts lint options after the directories (`--ignore=ALL`, `--extend-exclude=qro`, `--isolated`, `--select=E999`), beyond the stated `--exit-zero` limit. The derived guard rule reads only `python [-I] PATH` and the pytest stage script. `-m` and other interpreter flags are unread, which matches the registry's own list of forms (`probes\p_unguarded.py`).
- BELIEVED: on POSIX, a mutant that reads the real FIFO would hang its test rather than fail it.

## What held (MEASURED unless noted)

**History reader.**
- My fuzz builds random histories with branches, merges, renames, deletes, links, gitlinks, odd names and several encodings. It checks them against an independent route (`rev-list`, then `ls-tree`, then `cat-file blob`). Over 460 repositories (400 on the host, 60 under WSL) and 2,744 needle blobs (1,359 only in history), it found 0 misses, 0 extras and 0 crashes. Names covered: spaces, non-UTF-8, quote, tab, colon, backslash, trailing dot, mid-line-feed, leading CR.
- Missing, truncated, garbage or deleted objects, a missing subtree or root commit, a pack without its index, and alternates all fail closed with a finding and exit 1 (`probes\p_objects.py`).
- Directories replaced by a gitlink or a symlink were found. SHA-256 repositories, linked worktrees, and shallow depth-1 and depth-2 clones all work.
- On the clone's real history a push of HEAD sends 378 blobs and 7 commits, and the gate reads all of them (`probes\p_coverage.py`).
- Random-byte blobs behind every byte-order mark never crashed the decoder (6,000 blobs).

**Replace refs and grafts.**
- Replace refs on a commit message, a blob, a graft-style cut and a tree each show the gate the same objects a push sends (`probes\p_replace.py`). `pack-objects` ignores replace refs, which confirms the BELIEVED claim in P0.4's report. `info/grafts` cuts the gate and the push alike.

**Old readers.**
- P0.4's commit-based oracle on the frozen gate (240 repositories) found 0 misses and 0 crashes. The 4 extras are correct findings in historical `.gitmodules` files.
- The old and new gates agree on everything outside the new history findings over 180 random repositories (`probes\p_diff_old_new.py`).

**Runner and registry.**
- Five runner mutants (return code read after the clock, fail only past one failure, exit 2, swapped labels, lint pointing at nothing) were all killed by the end-to-end test.
- The guard-form fuzz with bash as ground truth (WSL, seeds 7 and 8) found 0 misses over 3,293 chunks that call a guard.
- `-h` prints the whole header (46 lines), and `--list` under `--budget quick` marks the right stages.
- The new tests pass from a path with a space and an accent.

**Pipes and links.**
- tests/tools passes under WSL: 142 tests, including the real-FIFO pipe test.

## What I did not do
- I did not run native Linux or macOS beyond WSL, Python 3.13 or 3.14, a real GitHub clone, or hooks. Sparse checkouts and partial clones were tried only against a local remote.
- I did not run the full runner under WSL (its Python 3.10 has no `tomllib` and no ruff; the failing tests/docs there are that). I ran tests/tools, the guard fuzz and the history fuzz there.
- I did not re-measure idle timings, check the 187 s figure for P0.5's committed tree, or run the full test fallback for my survivors.
- I did not run the lead's patch scripts. I compared the frozen tree to the staged index instead. I did not read the lead's state notes, the ledger, other verifiers' directories (except verifier-P04-r4) or any worktree.
- I ran the lead's `probe_catfile.py` in an empty directory of mine. It shows a garbage pack leaves `cat-file` at rc 0. A truncated loose object does not, which is D3. My run of `probe_missing_blob.py` failed at import because I gave it the wrong tree argument; no effect.
- Slips:
  - **IBM job ids.** My first freeze check printed a listing that included IBM job ids as file names into the tool output. Nothing was saved to a file, and I do not repeat them here.
  - **Git Bash /tmp.** That same command wrote two list files there; I removed them.
  - **WSL /tmp.** I used a directory there and removed it.
  - **Read-only run on the real repository.** I ran the gate on the real repository's staged state through Python with optional locks off. It wrote nothing.
- Nothing was pushed, nothing was contacted, and no key, token or CRN was read or printed. My scratch clones had their remotes removed before any commit.
