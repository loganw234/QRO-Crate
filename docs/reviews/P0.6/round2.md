# P0.6 verifier, round 2: NOT READY

One defect. It is narrow and the gate fails closed, but it shows up as a crash on a tree that 8afeede's gate passed. That is the case item 9 of the brief names, so I counted it. It is a code defect with a false sentence in the ledger beside it. Everything else I attacked held, and there are notes below. All paths below are under `<scratch>\verifier-P06-r2\check\` (called CK).

## Defects

### D1. [code, gate] A history-only file name outside the output's code page crashes the gate on a clean tree

- **The fault (MEASURED).**
  - Setup: a repository with `notes.md` and a binary file named with two Chinese characters, committed and then deleted in the next commit.
  - Run: `python tools/check_privacy.py &gt; out.txt` in Git Bash, with no `PYTHONIOENCODING` set. Redirected stdout takes the Windows code page, cp1252.
  - 8afeede's gate: exit 0, `privacy ok: 2 files and 2 commit messages read; 0 binary files not read`.
  - The frozen gate: exit 1, empty stdout, and `UnicodeEncodeError: 'charmap' codec can't encode characters in position 85-86`. The failing print is the `not read: &lt;name&gt; (history …): binary` line.
  - With `PYTHONIOENCODING=utf-8` the frozen gate passes and names the file.
  - Sources: `CK\probes\p_print.py` and the Git Bash run (`CK\w\pr_*.out`, `pr_*.err`).
- **What is P0.6's.**
  - The mechanism is older. On a tree whose current tracked file has such a name, both gates crash identically (MEASURED, `CK\w\pc_*.err`).
  - What P0.6 adds is that history-only names are now printed, as `not read:` lines for binary blobs and in every finding line. Trees that were right at 8afeede now fail.
  - This is the same footing as round 1's D2: a clean tree refused because of the new reader, failing closed, with an unusual name.
- **Limits of the fault.**
  - It fails closed.
  - The runner sets `PYTHONIOENCODING=utf-8`, so the runner is immune.
  - This repository's own history has no such name (0 binary blobs; the two known findings sit under an ASCII path), so no stranger's clone of it is affected.
- **Fix (BELIEVED).** A line or two in `run()`: write stdout with `errors="replace"` or `"backslashreplace"`. A process-level test with `PYTHONIOENCODING=cp1252` would hold it.

### D2. [prose] The ledger's "older than P0.6" is false for this case

- The "Not taken, for P0.7" bullet in `docs/VALIDATION.md` (last entry) says the last-print crash is "older than P0.6".
- That holds for a current file, but it is false for a history-only name: 8afeede passes that tree and P0.6 refuses it.
- Round 1's report said "The history reader widens it". The ledger dropped that.
- Fixing D1 settles this. Otherwise the sentence should say the reader widens it.

## What held

Labels: MEASURED comes with its probe or log under CK, READ means I read it, BELIEVED means I did not measure it.

- **Freeze (MEASURED).**
  - `SHA256SUMS.txt` starts `dee0b595f15e0cfd`. 267 of 267 files are OK at the start and at the end, with no caches under `frozen\`.
  - `frozen\tree` equals the real repository's index blob for blob (267 entries, 0 mismatches, `CK\idx_vs_tree.py`).
  - At the end the real repository was HEAD 8afeede with 13 staged paths and no lock. moth-quantum was 3a73823 and clean.
- **The runner (MEASURED, `CK\logs\run_gi.log`, `run_clone.log`).**
  - Both copies passed: 17 stages passed, 7 skipped by name. Wall time was 224 s and 225 s; stage time was 220 s and 221 s, two runs at once beside other sessions.
  - 1,365 tests: docs 175, tool-tests 165, vocab-tests 12, format 958, custody 23, control-tests 32. This matches the entry.
  - In the clone the privacy line reads `267 files and 7 commit messages read; 0 binary files not read; 115 versions in earlier commits read`, plus the 2 known findings. The 7 messages are the real repository's 6 plus my overlay commit. Controls: 40 of 40 caught.
  - Depth-1 and depth-2 shallow clones pass docs, tool-tests, privacy and privacy-controls (`logs\run_shal1.log`, `run_shal2.log`). At depth 1 the known list is inert; at depth 2 it applies.
  - Under WSL (Python 3.10.12, git 2.34.1), tests/tools passes: 165 tests, including the real FIFO, SHA-256, line-feed and HEAD tests (`logs\wsl_tools.log`).
- **Round 1's fixes.**
  - D1: 44 awkward names, committed with a key and deleted. Each was found, and each key blob is in what `pack-objects --revs HEAD` sends (MEASURED, `probes\p_names.py`). The names cover leading, double and mid-path line feeds, non-UTF-8 bytes, `HEAD`, `--`, long names and 40-hex names.
  - D1 again: the first verifier's fuzz on fresh seeds. 100 random histories, 543 needle blobs of which 297 are history-only, with 0 misses, 0 extras and 0 crashes.
  - D2: 23 root names (HEAD, head, a directory HEAD, `--objects`, `HEAD~1`, and others), tracked and untracked, in-process and as a process, all pass (`probes\p_headfile.py`).
  - D3 and D4 are fixed. A sweep for the removed overclaim finds only history entries and the correctly scoped line in `run.sh`.
- **Objects.** 19 kinds of damage to a history-only key blob (loose and packed; truncated, flipped, deleted, garbage, alternates) give a finding or a blob that git still reads, never a crash. Three rows pass without a finding. In each of them the key's bytes are gone, or `pack-objects` itself fails with rc 128, so no readable key is pushed (`probes\p_corrupt.py`, `p_arms2.py`).
- **Replace refs (MEASURED, `probes\p_replace2.py`).** A replace of the commit, of its tree, or of the blob each hides the key from a git that honours replace refs. The push still sends the key, and the shipped gate names it.
- **Git configuration.** 40 injected configurations (colour, quote path, signatures, autocrlf, abbreviation, commit-graph and so on) all give the baseline answer (`probes\p_config.py`).
- **Old against new.** 60 random repositories are identical outside the history reader (`probes\p_diff_old_new.py`).
- **The known list (MEASURED, `probes\p_known2.py`, `p_known_mut.py`).**
  - `KNOWN` is read only in the history loop. Its key resolves to blob 7671e68, which is round4.md as pushed in 20d40e6 (SHA-256 `d014f919…`, as the P0.4 README says).
  - That blob has exactly two findings over all 37 alternatives, both on line 94 and both with the placeholder `name` (`<a home path>` before `Ubuntu/home/name`, and `<a home path>`).
  - No other blob among the 115 has a finding.
  - The pushed copy put back as a working file, or as a staged version, is still a failure.
  - A wrong alternative in an entry fails the gate and the known test; a wrong blob id fails the gate. This is what the entry says.
- **Spellings.**
  - A corpus built from each comment's own words, 44 must-find and 31 must-not-find samples, gave 0 disagreements for `wsl-unc-slash`, `url-quoted-drive` and `wsl-file-url` (`probes\p_spell2.py`).
  - `Path.as_posix` is found by `wsl-unc-slash` and `Path.as_uri` (with `%24`) by `wsl-file-url`, each only by its own alternative (`probes\p_asuri.py`).
  - A URL whose host is named wsl, and a scheme ending in a letter before an encoded path, are not found.
- **Pipes and links.** The order mutant is killed. The FIFO test passes under WSL.
- **Departures and timings.**
  - `pytest-stage.sh` differs from moth-quantum's 3a73823 only as its header lists.
  - `need` is in moth's runner and not in this one.
  - CLAUDE.md's 170 s is the lead's quick log: 165 s printed, plus the control.
  - 150 to 365 s is the lead's logs (195 s, 364 s) and P0.5's 151 s, and my 220 s fits.
  - `-h` prints 46 lines. The quick budget marks 18 of 24 stages.
- **The ten notes.** All ten are accounted for; note 6's `need_env` half is the gap in the notes below.
- **Mutation.**
  - The lead's 47 of 47 reproduce, each killed by its target. Their 29 target ids (92 tests) pass on the unmutated tree, so those kills mean something (`logs\mut_lead.log`).
  - My 18 (`CK\m_r2.py`, run with `hm_r2.py`, which adds a baseline and runs survivors against tests/docs, tests/tools and the cheap extras): 3 killed and 15 survived (`logs\mut_r2.log`). Every survivor is in test reach; see the notes. The four test directories not run (format, custody, controls, vocabulary) mention neither the gate nor the registry nor the runner.

## Notes

These are all below the bar. The code is right in each unless I say otherwise.

**Test reach, where the code is right (MEASURED mutants).**
1. `history()`'s `cat-file --batch` failure arm is held by no test. Replacing `return None` with `return []` survived. Real damage reaches the arm: a truncated loose object, a flipped byte in a loose object or in a pack (rc 128). The batch-check arm survived too, but 19 kinds of damage never made it fail after `rev-list` succeeded, so it is probably dead.
2. The replace-ref flag is held for `cat-file --batch` only. Losing it on `rev-list` (which hides a whole key commit or tree) or on `batch-check` survived. The test replaces a blob, which only `--batch` sees.
3. A strict UTF-8 decode of a history path survived. It would crash on a non-UTF-8 name, and my names probe shows the shipped code handles one. "The last path git lists, not the first" also survived.
4. Spelling edges. Survivors for `wsl-file-url`: only `/home/`, no name required, no `\b`, an empty distro. For `url-quoted-drive`: the lookbehind accepting any two hex digits, and a digit before the letter. For `wsl-unc-slash`: no trailing slash required.
5. The registry's `unguarded` is untested on the `env NAME=VALUE python TOOL` form. The lint pin's fourth word is near-equivalent.

**The registry and the runner.**
6. Note 6's `need_env` half is neither taken nor stated. Deleting or commenting out any of the four `need_env` calls (before p1-crates, p2-crates, p4-shacl and instruments) passes every registry function. Misspelt, joined or reason-less calls are caught. The entry and the registry docstring scope the new rule to `need_file`, but they do not state the residual. Without the variable the stage would fail loudly instead of skipping by name (`probes\p_registry.py` and the plant script in my session).
7. The registry's limit lists "ruff's options after the lint's directories". Options before the directories pass too (`--ignore=ALL`, `--select=E999`, `--isolated`, `--exit-zero`, `--config=…`). The generic words "a tool's own flag that masks its exit" cover them, so I read the limit as true. "Anywhere on the lint line" would say it exactly.
8. The new end-to-end runner test needs `ruff` in the interpreter, and no file declares it. The runner's lint stage already needs it.
9. The new SHA-256 test needs git 2.29 or newer, and no git floor is stated anywhere.

**The gate: older, or by design.**
10. `jwt` is quadratic on a run of `-eyJ`. 20,000 characters take 0.19 s, 80,000 take 3.1 s, 160,000 take 11.9 s and 320,000 take 51.7 s (MEASURED, `probes\p_regex.py`). The other 36 alternatives were linear on about 50 pump shapes. The regex is older than P0.6; the history reader exposes more bytes to it. I did not count it: the trigger is crafted content, outside the accidental-publication threat model. This is in contrast to D1, whose trigger is an ordinary file name.
11. A name that begins with a percent-encoded character passes every URL spelling: `file:///C:/Users/%C3%81lvaro/…`, `C:%5CUsers%5C%C3%81lvaro` and `file:///c%3A/Users/%C3%81lvaro` are all missed, while the plain-ASCII twins are found (MEASURED, `p_spell2.py`). `_NAME` wants a literal letter or digit. Older; it falls under "encoded other than as a listed alternative says". `url-quoted-drive` inherits it, and its comment "as encodeURI leaves it" is the one place a reader might expect otherwise.
12. The cost limit holds. 120 versions of 1 MB took 85.6 s with a 259 MB peak working set. Four other content shapes, 30 versions of 1 MB each, ran at about 1.2 MB/s (`logs\p_cost_*.log`). The docstring's 78 s and 380 MB is round 1's figure with a different memory measure.

**Prose.**
13. CLAUDE.md item 3, "A path committed and then deleted is still pushed", reads as a file path. It means a home path, and keys and addresses fail the same way.
14. The registry's `git_env` docstring ends "As the privacy gate's." The gate's now also pins `GIT_NO_REPLACE_OBJECTS`, which the registry's does not. This has no effect on `ls-files`.
15. The gate docstring's limit about names that are not UTF-8 ("stops the gate with an error") does not mention the history reader. History paths are decoded with replacement and read; only the final print can fail, which is D1.

## What I did not do
- I did not run native Linux or macOS, Python 3.13 or 3.14, the full runner under WSL (Python 3.10 has no ruff), a sparse checkout, or a partial clone against a live remote.
- I did not run a real push; `git pack-objects --revs --stdout` stands in for one.
- I did not run the quick budget myself; CLAUDE.md's 170 s is checked against the lead's logs.
- I did not read the worktrees, the ledger, the lead's state notes, or any verifier directory except P0.4-r4 and P0.6-r1.
- I did not check the entry's "P1.1's 21 files and P4's 51 hold no finding", because those files are off-limits to me (unverified).
- I did not run the gate on moth-quantum's records.

**Slips.**
- My first freeze command wrote two file lists into CK containing names from `records\` (IBM job ids). Nothing was printed, and I deleted both files at once.
- I tried to write `/tmp_files_r2.txt` and was denied.
- A setup one-liner of mine printed Chinese characters to a cp1252 pipe and crashed. That is my own script, not the gate.
- The real repository got only read-only commands with `--no-optional-locks`. My clone used `--no-local --single-branch --branch main` and had its remote removed before I committed in it.
- pytest's temporary directories under WSL fell in WSL's `/tmp`, as the project's tests do.
- I read three of the lead's run logs in `scratchpad\p06\` (quick, full, on-r4).

Nothing was pushed, nothing was contacted, and no key, token or CRN was read or printed. Every key-shaped string and home path I planted was built in pieces at run time.
