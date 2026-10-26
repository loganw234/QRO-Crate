**Verdict: NOT READY**, on one prose defect in CLAUDE.md item 9. I found no wrong answer, crash, hang or wrong exit code in the code, and no gate fault. Labels are READ, MEASURED (script) or BELIEVED. My scripts are in `<home>AppData\LocalLow\qro-sbx\p07-r3\mine\`, and my notes are in `<scratch>\verifier-P07-r3\check\notes.md`.

## Defect

**D1 (prose): item 9's first bullet says a low-integrity process can "write and delete only in low-labelled folders, the sandbox among them, and nowhere in the profile, the repositories or the system." The profile half is false.**
- READ (icacls): `AppData\LocalLow` is in the profile and carries the Low label with `(OI)(CI)`. `qro-sbx` inherits it, and so do all 57 other folders directly under LocalLow.
- A program Python starts (git, bash, rm, cmd, `os.system`, ctypes) can therefore write and delete throughout LocalLow and in every other agent's directory under `qro-sbx`. These are the programs the hook does not see, so the label is their only fence.
- The hook's root is the shared `qro-sbx`, not the agent's own directory (READ, `sitecustomize_v2.py`). "Outside the sandbox" therefore means outside the directory all agents share.
- The guard's own docstring claims only "outside a low-labelled folder". Item 9 says more, which is the same shape as round 2's D2.
- I did not write outside my directory to demonstrate this, since the brief forbids it. The actual write is BELIEVED, from the labels and from how the sandbox itself works.
- Fix: name `AppData\LocalLow` as low-labelled for every application, say the label is the only fence for a program the hook cannot see, and drop "nowhere in the profile".

## What held

- **Freeze (MEASURED):** all 299 files match `SHA256SUMS.txt`, and there are no extras.
- **Runner:** it ran through `sbx-mid.sh` in two copies. Each copy gave 18 stages passed, 6 skipped by name, and 2,946 tests.
  - Counts per stage: docs 190, tool-tests 204, vocab 12, format 1,316, custody 23, p1 1,169, control-tests 32.
  - The first copy is a `git init` copy. The gate read 299 files and 1 commit message there.
  - The second is a no-hardlink clone of the real history with the tree committed over cbdb6a3. The gate read 299 files, 9 messages and 140 earlier versions there, and listed the 3 known findings.
  - The five new tests are docs +1, tools +2 and format +2 against the second verifier's counts.
- **At low integrity (MEASURED):** 2,923 passed and 23 failed. The 23 are bash tests, 21 in `test_stage_registry.py` and 2 in `test_cli.py`, which is exactly item 9's file list.
- **Corrected D1 sentence:** true (`cli_cut.py`).
  - A 5,000-character name gives exit 2, a line beginning with the name, and "1029 more characters".
  - Exit 3 and exit 1 lines keep their fixed prefix.
- **Item 8's sentence:** true (`streams.py`, `streams2.py`).
  - With `&gt;&amp;-` through the launchers, `sys.stdout` is None, but a child started with `stdin=DEVNULL` starts, and its inherited stdout handle is valid.
  - `SetStdHandle(0xFFFFF0)` reproduces the old WinError 6.
- **Writer:** the shipped writer and the round-2 writer (the same tree minus the inner `MemoryError` arm) agree on 27,490 outcomes over 4,075 variants. They differ only where a `MemoryError` is injected at the fallback, in all 1,865 of 1,865 cases, and there the shipped one raises it.
  - The second verifier's two oracle matrices, run on this tree, give 0 flags over 9,234 variants.
- **New tests:** the five tests pass unmutated, and the lead's five mutants are each killed by their target (`hm_t.py`, `sbx.sh`).
  - By reading, the tests hold on a host with symlinks. The dangling-link test accepts either the "unreadable" finding or "2 files".
  - The gate reads a dangling junction as `unreadable: PermissionError` plus the staged version. With `exists` in place of `lexists`, it silently passes the path over.
- **Gate regression:** nothing moved. The 126 git states give 0 misses and 0 crashes, and the 716 stream states give 0 unexpected. The 4 false alarms are the known tracked-file-replaced-by-a-directory case, and the 1 build failure is the scenario's own `git rm` refusing a state.
- **Item 22:** rdflib 7.6.0 (blocked sockets) reproduces every new claim. That covers root and descriptor at both bases for `@x`, `.`, `././`, `//`, `?` and `;`, the third limit's `.#a:b`, the empty-path base, and the base's collapsed `//`, removed dot segments, dropped `;` and lowercase scheme.
- **IANA:**
  - The lead's CSV gives 3,069 terms, 333 scheme-shaped, 451 schemes, and exactly the six overlaps.
  - A WebFetch of IANA's live CSV (model-mediated, BELIEVED) returned the same rows and statuses for the six and for `http`, `https`, `urn`, `doi`, `mailto`, `tag`, `ftp` and `ark`.
  - 18,696 ids around all 3,070 terms agree with an independent restatement of the id rule.
- **Deep paths:** the whole command takes 0.27 s for 50,000 segments and 0.36 s for 100,000.
- **Prose and registry:** the reviews README's entity counts and source hashes check out. The lint rule plus `WORD` catches a quoted `"--exit-zero"`.
- **Coverage:** every line P0.7 changed in `qro/` is executed by some test.

## Notes

**About the guard (outside the tree; not counted):**
- **G1.** `shutil.copy2` is not refused. Python 3.12 calls `_winapi.CopyFile2`, and the hook has no branch for that event.
  - MEASURED: the hook allows the event with an outside destination.
  - MEASURED: a real `copy2` onto a two-named file inside the sandbox changed both names, while `open`, `copyfile` and `copy` onto it were refused.
  - Item 9's hook sentence and its hard-link clause are untrue for it.
- **G2.** `os.open(existing, O_RDONLY|O_TEMPORARY)` deletes the file on close. The hook sees flags 192 (`O_TEMPORARY|O_NOINHERIT`), counts that as a read, and allows it. I measured the delete inside the sandbox and the hook's answer for an outside path.
- Under `sbx.sh` the OS covers both gaps. Under `sbx-mid.sh`, which runs the runner and the bash tests, nothing does. Either the guard gets two branches or item 9 gets two exceptions.
- `python -I` ignores the launcher's `PYTHONDONTWRITEBYTECODE`.
- A junction to `C:\Windows` could not be made at low integrity (WinError 5).

**Test reach, where the shipped code is right:**
- **T1.** Mutating the cut's remaining count to use the escaped length `n` instead of the text index `i` survives the whole suite. On 2,000 "é" the shipped code says 976 more characters, and the mutant would say -2096.
- **T2.** Two mutants survive that cut only REFUSED lines, or only descriptor 1. No test holds the cut on exit-2 and exit-3 lines, though the corrected D1 sentence and item 16 rest on it.
- **T3.** With the second verifier's note-1 mutant applied, the "no .git" test fails under the default temp folder but passes when pytest's base temp is inside a git work tree (`--basetemp`).

**Prose and other:**
- FORMAT.md item 16's rewritten sentence reads badly: "as any `Exception` they raise is but a `MemoryError`".
- The mirror spelling `//wsl$\Ubuntu\home\x`, and the mixed forms `/\wsl$…`, `\/wsl$…` and `//wsl.localhost\…`, are found by no alternative (MEASURED, `wsl_forms.py`). This is older than P0.7 and below the key threat model.

## What I did not do

- I ran no P4 stages, since P4's files are not in the tree.
- I tested no other platform, no real symlink, no path past 260 characters and no non-NTFS volume. These I only read.
- I ran nothing under pythonw, detached, or in a new console.
- I did not re-run P0.5's 300,000-id sweep or the lead's 43 earlier mutants.
- I fetched IANA's registry only as a spot-check, not in full.
- I made no write outside my directory, so I have not demonstrated D1's write.
- I did not touch the real repository's objects or measure its hard-link counts.

## Deviations (you asked about /tmp)

- **Files in Git Bash's `/tmp`.** During the freeze check, before your rule reached me, I wrote `/tmp/_r3_sumcheck.txt`, `/tmp/_r3_tree_files.txt` and `/tmp/_r3_sum_files.txt`. They held file-name lists of the frozen tree, `records\` names included. I removed them by literal path in the same command and confirmed afterwards that none remain. I have written nothing else there.
- **Bare `python3`.** I made one `python3 --version` call in my own shell, outside the launcher, with output discarded.
- **Unset `$SBX`.** One command ran with `$SBX` unset, so bash tried `bash python …` and refused with "cannot execute binary file". Nothing executed.
- **Hung probe.** My `cli_cut.py` deadlocked on a pipe, and the harness moved it to the background at its default timeout. I stopped it and its five leftover processes by PID; all had `cli_cut.py` in their command line.
- **Deletions inside the sandbox.** I used `rm -f` on files named by a variable or a glob, non-recursive and inside `mine\`.
- **Bytecode.** My `python -I` runs wrote `__pycache__` into my sandbox copies `tree\` and `tree-low\`, because `-I` ignores `PYTHONDONTWRITEBYTECODE`.
- **Reads outside my directory.** I read the lead's IANA download folder (named in `SCRATCH\p07\iana_dir.txt`), made one WebFetch of IANA, and listed the names under the sandbox root once. I opened no other agent's directory.
