# P0.8, round 5: the verifier's report

**Verdict: READY.** I found no defect in what the code does that a crate or the command line can reach. I found no gate, stage, test or registry that passes a fault it claims to catch, and none that fails a tree it should pass. The cap is reached, so only such a defect blocks. Below the bar I report two findings about the code (C1, C2) and some notes on prose and test reach where the code is right. None blocks.

Labels: READ (I read it), MEASURED (with the command or script), BELIEVED (not checked).
- SB is `<home>AppData\LocalLow\qro-sbx\p08-r5`. My scripts are in `SB\scripts\`.
- Everything that runs code ran from SB through `sbx.sh`, or through `sbx-mid.sh` where it starts bash. The stray calls are listed under "What I did not do".
- I read, printed and wrote no IBM job id, key or CRN.
- The detailed record is at `<scratch>\verifier-P08-r5\check\notes-p08-r5.md`. The harness refused a second file write, so this message is the only copy of the report.

## Defects

None that blocks. By kind:
- **Code:** none reachable. The one difference I could not call right (C1) cannot be reached by any crate or by the command line.
- **Gate:** none. The diff does not touch tools/check_privacy.py. It passed in both runs, with 40 of 40 controls caught.
- **Prose:** none that blocks. The loose sentences are notes 2 to 5.

## Two findings about the code, below the bar

**C1. Code, unreachable from a crate or the command line.** In process, `checker.check()` of a crate path holding a NUL character, or longer than 32,767 characters on Windows, now raises `ValueError`. Base answered `REFUSED file-missing`.
- **Cause:** pathlib's `is_symlink`, `is_junction` and `is_file`, the old first askers, answer False on `ValueError`. The new question calls `os.lstat` itself and catches only `OSError`.
- **Measured (`scripts/e_valueerror.py base` and `tree`):** base gives `REFUSED file-missing` for both paths. The tree gives `ValueError: lstat: embedded null character in path` and `ValueError: lstat: path too long for Windows`. Through `qro.__main__._verdict` both give exit 2. A directory that is not there is `file-missing` in both.
- **Why I do not block:** a listed entry's name cannot hold a NUL. The command line refuses a non-directory before it calls `check()`, and `kind()` swallows the ValueError there (exit 2, measured). A NUL cannot travel in a Windows command line (BELIEVED).
- **Closure:** it is the family the lead already pinned in process (a crate directory that is not there, and a crate path that is a file). The one-line closure is `except ValueError: return False` ahead of the `OSError` clause. My mutant P13 is that line; it gives `file-missing` for both paths (measured) and passes all 437 tests. No test would notice it either way.

**C2. Code, intended by item 12: a moved answer outside the dangling-junction class.** On Windows, a name ending in a dot or a space ("trail ", "trail.", "a..") is listed by its directory and cannot be stat'd, because `lstat` strips the trailing character. Measured with `scripts/d_build.py`, `d_build2.py` and `c_compare_v.py`; 8 of 142 odd-name crates differ from base.
- A file with such a name: `file-link` in both base and tree. Only the detail text differs.
- A directory named "trail ": base descended into it and refused `file-unlisted` at its inner file. The tree refuses `file-link` at the directory.
- A directory named "trail." or "a..": base failed with exit 3 (FileNotFoundError). The tree refuses `file-link`.
- Item 12's rule ("any entry its directory lists that the host says is not there") covers all of these, and the crate is refused in both. The ledger's "the other refusals in the same order" does not mention this class, so I name it.

## What I checked, by the brief's scope

**Freeze.**
- `SHA256SUMS.txt` begins `25c2a53f2c2ddf38`. Over `frozen\tree` and my copy `SB\tree`, `sha256sum -c` gives 301 of 301 OK and 301 files each, at the start and at the end.
- `diff -rq` against `SB\base` (a `git clone --no-hardlinks` of the real repository at 83503b0, remote removed) shows exactly the seven files the ledger names.
- The added lines are LF and ASCII, with no tab or trailing space. The longest is 119 characters.

**Runner, in two copies** (sbx-mid.sh, `QRO_MOTH_ROOT=<repos>/moth-quantum`, clean at 3a73823). Measured.

| Copy | Run id | Result |
|---|---|---|
| `git init` | `20261031-010211-10483-588708d` | 18 passed, 0 failed, 6 skipped by name (p2, p4, p1-crates, p2-crates, profile, p4-shacl), exit 0 |
| Real history with the tree laid over it | `20261031-010941-11417-377a34e` | the same |

- Both: 2,980 tests (docs 190, tool-tests 204, vocab-tests 12, format 1,350, custody 23, p1 1,169, control-tests 32). Base is 2,948 by `--collect-only`, so 32 are new, all in test_hostile.py.
- In the history copy the gate read 301 files, 10 commit messages and 147 earlier versions, with its three known findings. Privacy-controls caught 40 of 40, instruments reproduced 5 of 5, and lint passed.
- The 304 `(rm_rf)` warnings per stage are about old `garbage-*` folders named after pre-P0.8 tests. Both runs named the same 35 folders, so P0.8's tests added none.

**1. Round 4's fix holds.**
- **The list.** The question answers "not there" for exactly the errors item 12 names and raises every other one.
  - `scripts/a_classify.py` plants 2,301 errors as `os.lstat`'s answer for a listed file: every errno, and every Windows error from 0 to 2199 built the way the host builds them.
  - The question agrees with `pathlib._ignore_error` on all of them, on 3.12.15 and on 3.13.5 with the guard loaded. There were 0 mismatches.
  - The lists are READ in 3.12.15 `Lib/pathlib.py` lines 40-54 and 3.13.5 `Lib/pathlib/_abc.py` lines 26-40, and equal the tree's.
  - On this host 4 errno values and 15 Windows error numbers count as "not there".
  - On POSIX only ENOENT, ENOTDIR, EBADF and ELOOP count. A listed entry gives them only in a race (BELIEVED).
- **The command line as a process** (`scripts/b_planted_proc.py`, 51 rows).
  - Not-there errors give exit 1 `REFUSED file-link`.
  - PermissionError and Windows 5 and 32 give exit 2.
  - EIO, EINVAL, ENAMETOOLONG and Windows 87 and 1920 give exit 3.
  - The full text is identical under emulated 3.14 and under real pathlib.
- **Round 3's form of the question** (no classification, my copy P16) is identical to the tree on real pathlib. Under emulated 3.14 it answers exit 1 where items 12 and 16 say 2 or 3. So the fix moves nothing on 3.12 or 3.13.
- **3.14 itself.** No interpreter exists here (only 3.12.9, 3.12.15, 3.13.5).
  - I READ the 3.14 branch's `Lib/pathlib/__init__.py` (web read, nothing saved): `is_symlink` is `os.path.islink`, `is_junction` is `os.path.isjunction`, `exists`, `is_dir` and `is_file` are the `os.path` forms, `lstat` is `os.lstat`, and `_ignore_error` does not occur.
  - These are the six methods round 4's `emul314.py` models, so the emulation is faithful for what the checker asks.
- **Suites under the emulation** (`-p emul314`, sbx-mid): tests/format, custody, vocabulary and controls give 1,417 passed, and tests/p1 gives 1,169 passed.
- **Real interpreters.** Under 3.13.5, test_hostile, test_refusals, test_sites, test_canonical and test_sweep give 539 passed. Under 3.12.15, the two junction files give 437 passed, in three sessions.
- **The tests hold it.** P16 (classification removed) fails exactly the six `3.14` cases of `test_any_other_failure_of_asking_what_a_listed_entry_is_is_no_refusal`. P5 and P6 (EACCES or EIO taken for "not there") are killed by the `3.14` cases alone.

**2. Round 3's fixes hold.**
- The renamed question and the planted tests do what they name.
- The both-calls plant is no longer load-bearing. A plant of `os.lstat` alone (T3) passes everything, because the question calls only `os.lstat`. A plant of `os.stat` alone (T4) is killed.
- Nothing is accepted, refused by another name, or answered by another exit than before the rename. The question's code was the same from round 1 to round 4, and P16 is that code.

**3. Round 2's fixes hold.**
- Item 12, the docstring and the detail text agree with the code and with item 16, with one nuance (note 5).
- The crate-directory-not-there and crate-path-is-a-file tests are killed by P8 and P17.
- The wrong-case corner: `wrongcase-meta-dangling` is `file-missing` in base and tree (measured). The other rows are READ and true.
- The three corrected sentences are true.
  - Item 10 allows a test to make one if its target is made again and the junction removed (READ).
  - `scripts/g_stranded.py` reproduces a stranded junction. pytest's source renames the folder (READ, `_pytest/pathlib.py` lines 288-290). The junction's target is the old numbered path, which can be made again, after which `os.rmdir` works.
  - `Get-MpComputerStatus` shows signatures last updated 10/30/2026 11:11:56 AM.

**4. Round 1's fixes hold, here and by reading on an opening host.**
- **Shapes and fuzz.** Every shape is `REFUSED file-link` at its own place, in process and as a process.
  - `scripts/s1_shapes.py` (17 shapes, each in process and as three processes) gives round 4's rows.
  - `scripts/s2_fuzz.py` on fresh seeds 2001 to 2200 gave 200 run and 0 mismatches. Its oracle comes from item 12 and also checks the place named.
- **Path spellings.** `scripts/f_pathforms.py` tried the crate path in 11 spellings, for a plain crate and one with a dangling junction. All 22 rows were as expected: accepted with the same digest, or `file-link` at data/jct.
- **No junction left behind.** P0's tests leave none, passing or failing. About 40 sessions of mine ran, including mutants with 1 to 24 failing tests, with a temp root inside SB so pytest's numbered cleanup ran. A last `scripts/scan_junctions.py .` over all of SB found 0 links and no `garbage-*` folder.
- **Other hosts, by reading.** On a host that opens dangling junctions, or on POSIX, `_is_link` answers first, and the cases use `link_dir` and `os.path.exists` as their control. I found nothing that fails there (BELIEVED, not run).

**5. What the fixes could have moved: nothing wrong.**
- **Fuzz against base.** `scripts/c_build.py`, `c_batch.py`, `c_compare.py` and `c_clean.py` built 550 random crates. They cover dirs, unlisted and listed files, odd content, bad digests, deleted files, six kinds of changed metadata file, and junctions of four kinds.
  - The 315 crates without a dangling-style junction are identical to base in exit, stdout and stderr.
  - The 235 with one are all `file-link`, or refused first by a changed metadata file. None is left for review.
- **Odd names** made through `\\?\` gave identical answers in base and tree.
  - These were reserved device names, 255-character names, bidi and zero-width characters, emoji, lone surrogates, noncharacters, punctuation, case variants and all-dot names.
  - The one exception is the trailing dot or space class (C2).
- **P4's tool.** `_is_link` is textually unchanged (READ in the diff). That P4's tool asks it I could not check, since its tree is off limits.
- **Walk cost** (`scripts/timewalk.py`, 4,000 files, best of 4, twice): base 2.54 and 2.51 s, tree 3.17 and 3.20 s. That is about 26 percent more for one more `lstat` per entry, and it stays linear.
- **Stage counts:** reconciled above.

**6. The rest of P0.8.**
- The code the tests added deletes only literal paths the test made itself (READ). There are no skips, xfails, prints or debugger calls in the added code.
- The rewritten gate test in tests/tools kills its mutant (`exists` for `lexists`) and passes unmutated.
- The ledger figures 2,980, 437, the six failing cases without the fix, and the 32 new tests reproduce.

**7. Mutation.** I ran 32 mutants of my own (`scripts/mut5.py`, `runmut5.sh`), none of code that deletes; the table is in the notes.
- **Killed:**
  - the question always False (24 failures);
  - `except` narrowed (7);
  - `check()` not asking (5);
  - the grandparent's listing (18);
  - `or` for `and`;
  - EACCES or EIO added;
  - ENOTDIR dropped;
  - ENOENT alone;
  - the walk asking only of files, or only of directories;
  - `os.stat` for `os.lstat`;
  - the metadata question after the `file-missing` test;
  - an unlistable parent taken as "listed";
  - round 3's form.
- **Survivors** are notes 1 and 2.

## Notes (below the bar)

Each is about prose, or test reach where the code is right. None is about a gate.

1. **Test reach: the classification's constants are held only in part.**
   - P1 (EBADF dropped), P2 (ELOOP), P3 and P3b (Windows 21, 123, 1921), P7 and P7b (EINVAL or ENAMETOOLONG added) and P15 (only FileNotFoundError and NotADirectoryError count) each pass all 437 tests.
   - The tests plant ENOENT and ENOTDIR as "not there" and EACCES and EIO as "other".
   - Item 12's "and the like" and the docstring's "pathlib 3.12's own list" rest on nothing in the suite. A test comparing the tuples to `pathlib._ignore_error` on 3.12 and 3.13 would hold them.
2. **Prose in the ledger: "N4 and its twin are now killed by other tests than their target" is not true.**
   - Swapping the order of the link test and the question, in the walk (M2) and in `check()` (M3), passes all 1,417 tests of tests/format, custody, controls and vocabulary.
   - They are equivalent mutants now. The planted tables are identical for both orders, in real and emulated pathlib, because the question classifies by itself and a link and a "not there" answer cannot both hold.
   - So "eleven, each killed" counts two that nothing can kill.
3. **Prose in the ledger: "the format tests pass, 1,182".** That is five of the nine files of tests/format (canonical 25, hostile 397, refusals 40, spelling 694, sweep 26). The stage has 1,350.
4. **Prose in a test.** The docstring of `pathlib_answers` says that from 3.14 `is_symlink` "and `is_junction`" answer False for every error.
   - `is_junction` already did in 3.12 and 3.13 (READ: `ntpath.isjunction` catches OSError, ValueError and AttributeError; 3.13's is `os.path.isjunction`). So the helper's `is_junction` patch changes nothing.
   - On a 3.14 interpreter the `3.12 and 3.13` variants run 3.14's own pathlib.
5. **Prose: what the list takes in.** The list is pathlib's, and item 12 does not enumerate it.
   - Windows error 21 (not ready) is a Python `PermissionError` (errno 13) and is listed as "not there". At a listed entry it is `file-link`, exit 1. Item 12's "a refused permission is misuse, exit 2" and the docstring's matching sentence, read literally, say exit 2.
   - The list also takes in invalid handle (6), no more files (18), network path and name gone (53, 67), invalid target handle (114), direct disk access (130) and filename out of range (206). A transient host failure at a listed entry is therefore a verdict on the crate, as base gave for files through `is_file`.
   - Measured in `scripts/b_planted_proc.py` (rows `winerror:21` and `winerror:206`) and `scripts/a_classify.py`.
6. **At the commit.** The ledger cites round1.md to round4.md of P0.8's reviews "placed at its commit", and the tree holds no docs/reviews/P0.8/. When it does, docs/reviews/README.md and docs/README.md want P0.8's lines in the same change, since check_docs holds a page and its line together. Rounds 1, 3 and 4 said the same.
7. **Pre-existing and unchanged, so not P0.8's.**
   - An NTFS stream on a listed file is accepted (the lead's note).
   - Within one directory the walk asks directories before files, so with two link-like entries of different kinds the place named can differ by host (round 4's note 3, BELIEVED).
   - The module docstring of checker.py, step 2, does not mention the new refusal, though the name `file-link` is unchanged.
8. **The 304 warnings are a state of the shared temporary folder,** not a property of the tree. My own temp roots printed none.

## What I did not do

- **Hosts and interpreters.** I ran nothing on Python 3.14, on a host that opens dangling links, or on Linux or macOS. The host cannot make a symbolic link (WinError 1314), and WSL's Python is 3.10 and outside the sandbox. Every statement about those is READ, an emulation, or BELIEVED. I produced no real PermissionError at `lstat`; I planted errors and changed no ACL.
- **Off-limits and unread material.**
  - I did not read or run P4's, P2's or P1.2's trees, the worktrees, the lead's scratch under SCRATCH\p08 (so I made my own mutants), the ledger, or any other agent's directory.
  - I listed `qro-sbx\` and `qro-sbx\tmp` once for names and read nothing inside.
  - I read round 4's report in full and rounds 1 to 3 only for their notes and "did not do" sections. I read the fourth and third verifiers' scripts and the lead's probes.
  - I did not read the earlier verifiers' notes files or ParcelRound's METHOD.md.
- **Skipped on purpose.** I did not run the TA and TB mutants (the fixtures' removal deleted), which strand junctions; round 3 ran them. I did not run the third verifier's gate scenarios, since the gate is not in the diff; I ran the gate in both copies with its 40 controls. I did not look for the machine's cause, test the machine outside the sandbox's folders, or run `--budget quick`.
- **Stray calls, all by mistake and all inside SB.**
  - The host's `python` outside the launcher ran `scripts/c_compare.py` three times (once through `c_run.sh`) and one diff script, which only read my own files.
  - One `python - &lt;&lt;EOF` rewrote my own `scripts/mut5.py` and, through the heredoc backslash trap CLAUDE.md warns of, corrupted two lines. I repaired them with the Edit tool.
  - Nothing outside SB was written or deleted. I removed one folder by a literal path inside SB (a mutant copy made by a failed first attempt).
- **System state read only.** `Get-ItemProperty` for `LongPathsEnabled` (it is 1), `Get-MpComputerStatus`, and one failed `reg query`. One public page was fetched with the web tool (the 3.14 pathlib source). Nothing was downloaded to disk or sent.
- **Cleanup.** I contacted no one, accepted no banner and pushed nothing. My two repository copies have no remote. Every junction I made was removed with its target made again, and a last scan of SB found 0 links. SB still holds my copies, about 514 MB, which the lead may delete. They are `base`, `tree`, `run-init`, `run-hist`, `mut\`, `tree-e`, `tree-313`, the temp roots, `logs\` and `scripts\`.
