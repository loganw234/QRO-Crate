# P0.4 verifier, round 1: NOT READY

The privacy gate's new code gave no wrong answer, and I found no way for a key to reach a commit or a commit message past it. The NOT READY rests on two small defects: a regression in the runner's engine fingerprint (code), and a false claim about the `need_env` rule (gate and prose). Several tests do not hold what the entry says they hold; those are notes.

CHECK below means `SCRATCH\verifier-P04-r1\check`. Scripts are in `CHECK\scripts\`, logs in `CHECK\logs\`, mutants in `CHECK\mut\`.

## Freeze and setup
- MEASURED: `sha256sum -c` gave 255 OK at the start and at the end. The sums file begins `5e299671396e27e2`, the file list equals the sums list, and nothing ran inside `frozen\`.
- MEASURED: the real working tree's 11 modified files equal the packet byte for byte.
- Versions: host Python 3.12.9, a second interpreter 3.13.5, pytest 9.1.1, ruff 0.11.9, git 2.45.2.windows.1. WSL (Python 3.10.12, git 2.34.1) was used for two probes only.

## Defects

**D1 [code, runner; regression from 7f40400, contrived trigger].** The new `shacl_engine` package expression `d.metadata["Name"] + "==" + d.version` raises `TypeError` when the engine's environment holds a distribution with no Name, such as a `dist-info` directory with no METADATA. The runner then hashes the traceback, so the engine's fingerprint stops depending on the engine's packages.
- MEASURED, `s12_resume.py` on the frozen tree: with such a directory present, adding a new valid package leaves the fingerprint unchanged and `--resume` continues ("passed earlier in this run", rc 0).
- MEASURED, the same script on 7f40400 (`s12_resume.py &lt;CHECK&gt;\base7f40400`): the same step is refused, rc 2, FATAL.
- Python 3.13.5 behaves the same (`s7_engine_expr.py`). The old f-string printed `None==`.
- MEASURED fix: `"%s==%s" % (d.metadata["Name"], d.version)`. It gives the host's same hash (`fbb6906946dda12b`), changes when a package is added, and runs on Python 3.10.12.
- Why it went unseen: no test holds this expression (mutants 21 to 23 below survive), and the lead's reason for not testing it predates the change.

**D2 [gate and prose].** The `need_env` rule drops only whole-line comments from "reads". A name in a trailing comment still counts as a read.
- The false claims: the code comment "no comment reads a variable", the test name `test_a_variable_the_runner_names_only_in_a_comment_is_read_nowhere`, and the entry's "no longer takes a name in a comment for a read".
- MEASURED, `s5_needenv.py`: a trailing comment after a no-op counts as a read.
- MEASURED, `s14_d2_stage.py`: with `QRO_SHACL_PYTHON` named only in trailing comments, the real `docs` stage passes (138 passed, rc 0). With the lead's whole-line plant it fails.
- Single-quoted text and a quoted here-document body also count as reads. That sits inside the stated limit "reads the runner's text, not its run"; the trailing comment does not.
- Fix: strip trailing comments, or restate the claim and the test name as "a comment line".

## What I tried and found right
- MEASURED: the full runner on a clone of the real repository plus the frozen files, `QRO_MOTH_ROOT=… bash verify/run.sh`: 17 passed, 7 skipped by name, 0 failed (stage times sum to about 135 s, with P1.1 and P4 building beside it).
  - Counts: docs 138, tool-tests 114, vocab-tests 11, format 678, custody 23, control-tests 32. That is 996 tests.
  - One pytest session over `tests/`: 996 passed in 67 s.
  - privacy-controls 37 of 37; check-docs 10, 37 and 35; twin ACCEPTED `21fafec5…`; instruments 5 of 5.
  - The privacy line reads 11 staged versions, not the entry's 10. The 11th is VALIDATION.md, which the entry's run did not yet include.
- The lead's 12 mutants reproduce: 12 killed, all by their targeted tests (`mut\lead_hm_t.py` with `lead_m_p04.py`).
- MEASURED, `s1_staged.py` (about 35 scenarios, new gate against base): a key staged and edited out, staged then deleted from disk, renamed, in a path with a space and non-ASCII, UTF-16 or UTF-8 BOM blobs, a packed blob, a SHA-256 repo, a reftable repo, a linked worktree, an unborn branch, a merge's second parent, a merge message, an unresolved merge, `add -N`, a missing or truncated staged object, a registered submodule, and `.gitmodules`. All are right. Python 3.13 gives an identical table.
- MEASURED, `s13_fuzz.py`: 525 random repositories (staging, edits, renames, deletions, `rm --cached`, `add -N`, odd blobs, random messages) against an oracle that does not use `cat-file --batch`. Zero mismatches. Staged-only findings were expected in 39 of them.
- MEASURED: the 47 history shapes of P0.2's round-4 probe (`s2_hist_copy.py`) are all as expected. They differ from base only in the two intended rows. 70 control characters before a key all find it; the base misses U+0001. 15 values of `i18n.logOutputEncoding` all find the key; the base misses 7.
- MEASURED, `s9_gitenv.py`: all 29 git repository variables, singly and together, leave the staged path reading its own repository. Three rows crashed because I gave git a path where it wants an integer or boolean; that is my input, not the gate.
- MEASURED, `s4_nested.py`: an untracked nested repository, a linked worktree inside the tree, and a registered submodule are named, not read, and `git add -A` stages each as a link. A repository with no commit stages nothing.
- MEASURED, `s6_reader.py` and `s6b_cli.py`: only non-text versions differ from base, now `graph-form`. The command line gives exit 1 and one ASCII REFUSED line for nine hostile versions.
- MEASURED, `s8_lifts_copy.py`: pyproject.toml's sentence is true on all four pins and five placements. READ, then checked with `git show` on moth-quantum at 3a73823: `bundle.py` line 7 and line 17 say what the study now cites. Under WSL Python 3.10.12 the old fingerprint expression is a SyntaxError and the new one works, as claimed.
- MEASURED: `staged()` is linear, about 0.5 ms per entry (`s11_scale.py`). The ledger edit is a pure append, and the changed files are LF with a final newline.

## Notes

**Test reach, code right (17 of my 25 mutants survived; `mut_my.log`).**
- **[test reach] The `.git`-as-file sites are mostly unpinned.** P0.2's note 5 named four sites. The new tests kill one (the commit-message block of `check()`). Survivors:
  - the new staged block as `.is_dir()` (so the staged check silently never runs in a linked worktree, where the parcels build);
  - `files()` as `.is_dir()`;
  - `control()` as `.is_dir()`;
  - the registry's `committed_files`.
- **[test reach] The new registry worktree test is vacuous for its target.** The non-git fallback also returns `[a.py, b.py]`, so the test passes against itself. A tracked dot-directory file or an ignored file would tell the branches apart.
- **[test reach] The arms of `staged()` that no test reaches:**
  - the gitlink skip (read as a blob, every submodule would be a finding);
  - the missing-object arm, and its two classifications;
  - a staged file gone from disk;
  - a binary staged version.
- **[test reach] The fingerprint line and its expression are held by no test** (mutants 21 to 23).
- **[test reach] Equivalent or trivial survivors:** `--encoding=ISO-8859-1`, dropping `.lstrip()`, floats as versions, and the resume message text.

**Code, not blocking.**
- **[code] Symlinks to directories.** `p.is_dir()` also matches a symlink to a directory. MEASURED under WSL (`s15_wsl_symlink.sh`): an untracked one whose target is a `/mnt/c/Users/…` path was refused by the base gate (`unreadable: IsADirectoryError`). The new gate accepts it, labelled "a nested repository", and reads the link text only once staged. The same blind spot already existed for untracked symlinks to files. A tracked file replaced by a directory gets the same wrong label on Windows.
- **[code, older than P0.4] A commit's own `encoding` header.** `--encoding=UTF-8` converts from the header's encoding. MEASURED, `s3_msg.py`: commits made under `i18n.commitEncoding` of UTF-16, UTF-16LE, UTF-16BE or IBM037 lose the key in the base gate and the new one alike. `git commit -F` refuses a NUL ("a NUL byte in commit log message not allowed"), but a hand-built commit with a NUL hides the key in both.
- **[prose] Two docstring sentences claim more than that.** "whatever the repository's configuration asks" and "no byte a message holds splits it" both overreach. Under the owner's accidental-publication threat model this is contrived.

**The lead's "Not taken" reasons.**
- Deleted or repointed `need_env` guard: the reason holds for deletion. It does not cover repointing, which gives a visible skip with the wrong reason, not a loud failure. It also rests on `tests/p1crates`, which does not exist yet (BELIEVED).
- Fingerprint test: the reason ("MEASURED by P0.3's second verifier") measured the old expression. P0.4 changed it, and nobody measured the new one before me.

**Prose and accounting.**
- The entry is silent on P0.3's note about CLAUDE.md's "~125 s", which the previous entry recorded as "to take". It is also silent on P0.3 notes 4, 6 (`qro:line` and `qro:measuredPub` wording) and 10 (reader.py line 16, 186 characters). None changes an answer.
- FORMAT.md item 21 and reader.py lines 15 and 214 say "one declaring another version is `context`" without "as text". That is not false.
- BELIEVED, not checked: "and its coherences" in `qro:lawCircuit`'s meaning, as P2's design wrote it, because I did not read P2's design.

## What I did not do
- No native Linux or macOS run. WSL was used for the symlink case and the fingerprint expression only, and git 2.34.1 only there. No other git versions elsewhere.
- No real pre-commit hook, partial clone or sparse checkout. No real pyshacl engine: the "engines" were empty venvs with hand-made `dist-info` directories, and I installed nothing.
- I did not read the worktrees, the ledger, `brief-r1.md`, P2's design, or P0.3's verifier's frozen tree.
- No network, IBM or Atlas contact. The instruments stage read moth-quantum read-only. No key, token or CRN was read or printed; every key was synthetic and built in pieces, and no job ids appeared.
- Slips:
  - My first command wrote two file lists to the OS temp directory; I removed them.
  - pytest's temp directories and the privacy-controls stage's temporary copies go to the OS temp directory by their own design.
  - Several probe slips changed no result: a print crash in my harness, a `.gitmodules` URL under a home directory making one submodule row a correct finding, a NUL in argv, MSYS rewriting a WSL path, CRLF in a script I rewrote, and a mis-sliced exec.
  - WSL created root-owned files under `CHECK\w\`.
