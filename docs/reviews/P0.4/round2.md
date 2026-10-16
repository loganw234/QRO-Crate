# P0.4 verifier, round 2: NOT READY

There is one defect, and it is about what the code does. The privacy gate's new listing treats every path the index holds as a gitlink (mode 160000) as "a nested repository" and never reads it, whatever is on disk there. If that path now holds a file or a link, git commits it, and a key in it passes the gate. This is a regression from 7f40400 and from round 1's packet. It came in with the fix to round 1's note on links and nested repositories. Round 1's D1 and D2 are fixed. The rest of what I tried holds, and all 28 of the lead's mutants die by their own tests.

`CHECK` below means `<scratch>\verifier-P04-r2\check`. My scripts are in `CHECK\scripts` and my logs in `CHECK\logs`.

## Freeze and setup
- MEASURED: `sha256sum -c` on frozen\tree gave 257 OK at the start, midway and at the end.
  - The sums file begins `fd810babf8954a19`, its file list equals the tree's, no file is newer than it, and no .pyc exists.
  - Nothing ran inside frozen\.
  - The real repository's working tree equals the packet byte for byte (`sha256sum -c`, run read-only from there).
- Versions: host Python 3.12.9, plus 3.13.5 for the gate alone (it has no pytest). pytest 9.1.1, ruff 0.11.9, git 2.45.2.windows.1. WSL has Python 3.10.12 and git 2.34.1.
- MEASURED: the full runner on a clone of the real repository plus the frozen files gave 17 passed, 7 skipped by name, 0 failed, in 200 s with other work on the machine (`CHECK\logs\run_clone_full.log`).
  - On a linked worktree of that clone, which is how the parcels build, it gave 17, 7 and 0 in 166 s.
  - docs 141, tool-tests 120, vocab-tests 11, format 678, custody 23, control-tests 32. That is 1,005 tests, 9 more than round 1's.
  - privacy read 257 files, 4 messages and 14 staged versions. privacy-controls caught 37 of 37. check-docs read 10, 39 and 35. The twin was ACCEPTED `21fafec5…`. The instruments reproduced 5 of 5.
  - Every figure equals the new entry's.

## The defect

**R2-1 [code, the privacy gate; a regression; the trigger is contrived, as round 1's D1 was]. A path the index holds as a gitlink is named a nested repository and never read, whatever is on disk there.**

- READ: `tools/check_privacy.py` lines 163 to 165.
  - `gitlinks` comes from the index alone, and `files()` drops those paths from what it reads and names them.
  - It never asks the disk what is at the path.
  - Round 1's packet used `p.is_dir()`, so it read a file there. The fix swapped that for the index's mark.
- The fault: the index holds `sub` as a gitlink, and `sub` on disk is a regular file holding a synthetic `QISKIT_IBM_TOKEN=` plus 44 characters. MEASURED with `CHECK\scripts\t1_gitlink_file.py`, with identical results on the host and under WSL:

| gate | findings | exit |
|---|---|---|
| 7f40400 | 2, in `sub` | 1 |
| round 1's packet | 2, in `sub` | 1 |
| this packet | 0 | 0 (summary reads `not read: sub/: a nested repository, committed as a link, never as its files`) |

- MEASURED: `git add -A`, `git add -u` and `git commit -a` each store `sub` as a 100644 blob holding the key. A plain `git commit` stores the gitlink.
- MEASURED, with a real submodule (`CHECK\scripts\t2_submodule_replaced.py`: `git submodule add`, commit, remove the directory, write the file): the same result. A home path in the file gives the same too.
- MEASURED under WSL: a link in the gitlink's place, its text a key or a home path. git stores a 120000 blob of that text. 7f40400 and round 1's packet exit 1, but only because they call the link unreadable. This packet exits 0 with no finding.
- MEASURED: `bash verify/run.sh --only privacy` on a linked worktree in that state prints `privacy ok` and `== PASSED`. `git add -A -n` says `add 'sub'`.
- How far it reaches: `CHECK\scripts\oracle.py` is a commit-based oracle.
  - It copies a repository, runs `git add -A` there, and reads every blob. It does not use `git ls-files -co`.
  - Over 3,100 random repositories (2,650 under WSL with real links, 450 on the Windows host), 138 had a miss at a gitlink path.
  - There were no other misses and no crashes.
  - The round-1 gate on one seed missed in 40 repositories, every one with a link. So the oracle is sensitive, and the lead's link fixes work.
- Why no test sees it: the gitlink test makes the path an empty directory (`(r / "linked").mkdir()`). The replaced-path test goes the other way, from file to directory.
- Claims it falsifies, until it is fixed: the gate's docstring (line 11, "reads every file git would commit"; lines 45 and 46, "or the index holds as a gitlink"), CLAUDE.md line 94, and the `privacy` stage text at run.sh:386.
- It blocks even under item 6's loosened bar, since it is a defect in what the code does.
- A fix I tried in a copy (the lead's call):
  - Count a gitlink as nested only where the path is absent or a directory that is not a link: `not os.path.lexists(p) or (p.is_dir() and not p.is_symlink())`.
  - With it, t1 and t2 find the key, for a file and for a link.
  - The empty-directory, directory-with-files and missing cases are unchanged.
  - Oracle seeds 2 and 3 (400 repositories each) show 0 misses and 0 gitlink-class misses.
  - All of tests/tools and tests/docs still pass. So a new plant is needed to hold it: a gitlink path as a file holding a key, and as a link (simulated, as the existing link test does).
  - The registry's own `committed_files` already asks the disk (`is_file()`).

## Round 1's defects, and the rule added beside D2's
- **D1, fixed.**
  - MEASURED: the new expression prints `None==None` for a nameless dist-info on Python 3.9.21, 3.12.9, 3.12.13, 3.13.5 and 3.13.12.
  - MEASURED: round 1's `s12_resume.py` on this tree now refuses `--resume` (rc 2) when a new valid package is added beside a nameless one. Round 1 continued.
  - One forward note is N6.
- **D2, fixed for the spellings it targeted.**
  - MEASURED: round 1's `s14_d2_stage.py` makes the real `docs` stage fail (rc 1) for both the whole-line plant and the trailing one.
  - One spelling is left, N1.
- **The rule that a `need_env`'s reason names its variable works as claimed.**
  - MEASURED (`CHECK\scripts\t4_guard_variants.py`, which cuts `guard_problems` out by its AST): a guard repointed at another variable with its old reason is caught, and so is a misspelt variable.
  - A guard repointed with its reason edited to match is not caught. The entry does not claim it is.
  - `QRO_MOTH_ROOT` and `QRO_SHACL_PYTHON` are the only variables the guards name. A deleted `instruments` guard still fails loudly (the existing 0-of-5 test).
  - The `p1-crates` and `p2-crates` claims are BELIEVED, as the entry says.

## Notes (below the bar)
- **N1 [gate, prose].** The comment rule is narrower than "in no comment".
  - MEASURED: `#` at a line's start, after a blank, after a tab and after `{ ` is dropped. A `#` after `;`, `&amp;&amp;`, `|` or `(` with no blank is taken for a read, though bash treats all of them as comments (`bash -c 'echo a;# echo b'` prints `a`).
  - The code comment states the real rule. The registry docstring ("in no comment") and the entry's correction ("none in a trailing comment") overreach.
  - Widen the pattern or narrow the words.
- **N2 [gate, older than P0.4].** The rule sees only a call spelled `need_env NAME "…`.
  - MEASURED: with the variable misspelt, a call with two spaces, a tab, a single-quoted or bare reason, a continuation line, or an indent passes unseen. `need_file` has the same shape.
  - There is no counterpart to `one_line_stages` for guards.
- **N3 [test reach].** No test or stage runs the gate on a tree with no `.git`.
  - MEASURED: `in_git` always true, the walk returning nothing, and the walk reading `.git` all survive tests/tools and tests/docs (mutants 5, 7, 8).
  - The walk is right on the real tree. A no-git copy of it gave 257 files, and the controls caught 37 of 37.
  - The stated limit "a link to a directory is neither read nor named there" is true (MEASURED under WSL, t5 and t6) but held by nothing.
  - This is older than P0.4, but P0.4 changed that branch's return.
- **N4 [test reach].** Three link-related sites are unheld.
  - The staged reader's disk read going through a link (mutant 13).
  - The controls' copy following a link (mutant 15). This is real: with it, `--control` dies with `IsADirectoryError` on a link to a directory (WSL, `CHECK\scripts\t13_m15.py`). The shipped code gives 37 of 37.
  - The `.git` test at `control()`'s own site (mutant 0). The function-level `in_git` mutants do die.
- **N5 [prose and test reach; the code is right].** One of the entry's "Not taken" reasons does not hold.
  - The entry says the survivors "change no answer: … a version given as a float".
  - The shipped reader refuses a float version `graph-form` (MEASURED: 0.1 and 1.0). The survivor, which also takes floats for "another version", refuses `context`, so it changes the answer.
  - No test plants a float. `version=1` is the only plant, and `canonical.dumps` accepts a float, so `version=0.1` is a one-line plant.
  - The other two reasons hold. The `ISO-8859-1` reason is MEASURED: the key is found in ASCII, Latin-1, CJK and emoji messages either way. The resume message's text is only text.
- **N6 [forward; BELIEVED beyond the measured Pythons].** D1's fix and the runner comment "never a traceback" lean on a behaviour the standard library deprecates.
  - MEASURED: Python 3.13.5 warns "will raise KeyErrors" on that expression.
  - MEASURED: the installed importlib_metadata 8.5.0 backport raises `KeyError: 'Name'` on the nameless distribution. `metadata.get("Name")` and `metadata.get("Version")` do not.
  - BELIEVED: Python 3.14's standard library behaves like the backport (none is on this machine). There the engine's line, and the host's `packages=` line, would hash a traceback again, and the new test would fail loudly in the docs stage.
- **N7 [test reach].** The new fingerprint test holds the expression, its call from `fingerprint()` and `-I`. It does not hold the pipeline: `| sha256sum | cut -c1-16` cut to nothing, and the dropped `sorted(`, both survive (mutants 22 and 23).
- **N8 [prose].** "Link" now means two things in the gate: git's gitlink (the variable `links`, "committed as a link") and a symbolic link ("a link as its own text").
- **N9 [other].**
  - Older than P0.4: a file name that is not UTF-8 crashes all three gates with `UnicodeDecodeError` (Linux, MEASURED, t14).
  - The commit-encoding limit is true as a possibility, not for every message. IBM037 lost the key in my probe. UTF-16 found it for `-m "a note KEY"`, where round 1 lost it for a "café" message.
  - docs/reviews/P0.4/round1.md holds `&amp;lt;CHECK&amp;gt;` as the notification carried it, and the README does not say so (P0.2's does for its own).
  - CLAUDE.md's "~125 s": my runs took 200 s and 166 s on a shared machine, so I neither confirm nor refute it.

## What I tried and found right
- The lead's 28 mutants (`CHECK\logs\mut_lead.log`).
  - My harness `CHECK\scripts\mut.py` lists the FAILED test names. All 28 die by their own target.
  - The lead's `hm_t.py` counts any non-zero exit as a kill, so a mistyped test id would count. None was mistyped.
- 30 mutants of my own on the changed code (`m_r2.py`, `m_r2b.py`).
  - 16 were killed, including every per-site `.git` mutant but one, the refactored `index()` without the git environment, and the OSError breadth of the staged reader.
  - 14 survived. N3, N4 and N7 name the five real gaps among them. The other six are equivalent or redundant: the trailing-slash mutant, tab comments, `need_env` lines counted as reads, and the three look-around variants (reason lookbehind, reason lookahead, variable prefix).
- Real links under WSL, all handled as their own text.
  - Link to a file, to a directory, broken, a loop, outside the tree, to a nested repository, with home or key text.
  - An untracked link to an existing directory with a home-path text: round 1's packet passed it as "nested". This packet finds it.
  - `--control` runs on a tree holding all of them.
- The gate and controls in a linked worktree: 37 of 37. Python 3.13.5 gives the same results. Junctions (Git for Windows lists their files, all gates read them) are handled.
- The gate's limits: a NUL in a message stops `git log` there (MEASURED, git 2.45.2). In a copy with no git, a directory link is neither read nor named (MEASURED).
- Edits, prose and accounting:
  - The review README's hash for round1.md is right.
  - The changed files are LF, with a final newline and no BOM.
  - reader.py has no line over 120 characters.
  - The reader, FORMAT.md item 21 and the two vocabulary meanings changed in prose or text only. The generated pages match, and no old wording remains elsewhere.
  - The entry's figures match.
- Two over-reads (a finding on an assume-unchanged or skip-worktree path that `git add -A` would not stage) are in the safe direction.

## What I did not do
- No native Linux or macOS. WSL served for links only, with git 2.34.1 and Python 3.10.12.
- No Python 3.14. No pytest on 3.13.5, so the gate alone ran there.
- No real pyshacl engine. The "engine" was a throwaway venv with hand-made dist-info (round 1's script).
- No real symbolic links on the host (WinError 1314, confirmed), and no hooks, sparse checkout or partial clone.
- I did not read the worktrees, the ledger, brief-r2.md, or P1's and P2's designs. So "as P1's and P2's designs do" for the two meanings is unchecked.
- I re-measured the lead's probes' facts with my own scripts and did not run theirs.
- Slips:
  - Five small file lists went to the OS temp directory (Git Bash's /tmp). Four probe directories (`c2_*`) also went there. I removed all of them.
  - pytest's own temp directories (`pytest-of-*`) and the privacy-controls copies are in the OS temp directory by design, shared with the parcels, and I left them.
  - In the real repository I ran only read-only git commands (`status`, `log`, `show`, `archive`, `ls-files`, `diff --stat`) and `sha256sum -c`. `git status` may refresh the index's stat cache. No content changed: HEAD is still 7f40400, the 14 modified files and the untracked directory are as they were, and moth-quantum is still clean at 3a73823.
  - I killed my own duplicate mutation process, and removed my WSL /tmp directory and my bytecode caches.
- No key, token or CRN was read or printed. Every key was synthetic and built in pieces, and no job id appeared. Nothing was sent anywhere, and nothing was pushed.
