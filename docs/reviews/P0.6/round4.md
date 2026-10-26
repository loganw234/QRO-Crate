# P0.6 verifier, round 4: READY

Paths are relative to CK, which is `SCRATCH\verifier-P06-r4\check\`. Probes are `CK\p_*.py`. Mutants are in `CK\mutants\`, and the lead's mutants I re-ran are in `CK\lead\`. Runner logs are `CK\run-*.out`. Labels are READ, MEASURED (script or command named) and BELIEVED.

Environment: Python 3.12.9 (3.13.5 for the gate alone), git 2.45.2.windows.1, Git Bash, ruff 0.11.9, pytest 9.1.1. Every key-shaped string and planted path was built in pieces at run time. No job id is in this report.

## Verdict

READY on the bar CLAUDE.md item 6 sets. I found no defect that P0.6's code introduced or changed. Round 3's D1 and D2 fixes hold.

I did find three defects in what older gate code does (O1 to O3) and one contrived crash in P0.6's new line (O4). O1 to O3 behave identically at 37640f0 and 8afeede (MEASURED), so P0.6 neither caused nor touched them. O4 needs a stream I know no real console or harness to provide. I do not count any of them against P0.6.

I list them first so the lead can rule otherwise. If the cap's wording is read to cover old code, O1 would block.

## Defects in what the code does, none from P0.6's change

**O1. A clean sparse checkout is refused (older).**
- MEASURED (`p_sparse.py`): a cone-mode sparse clone of the real history, with and without a sparse index, 14 files on disk. The P0.6, 37640f0 and 8afeede gates all exit 1.
- Each prints `controls/__init__.py: unreadable: FileNotFoundError`, and one such line for every file the sparse checkout leaves out.
- The staged reader already reads the index's version of a file gone from disk, so the file loop's finding is redundant for a tracked path.

**O2. A closed stdin crashes the gate (older).**
- MEASURED: `python tools/check_privacy.py &lt;&amp;-` in Git Bash. All three gates exit 1 with `OSError: [WinError 6] The handle is invalid`, raised inside `git_env()`'s first `subprocess.run`.
- This is round 3's D1 family, for stdin. Passing `stdin=subprocess.DEVNULL` to the gate's git calls would end it.
- Reach is small (BELIEVED): Git Bash's `&lt;&amp;-`, or a service with an invalid stdin handle.

**O3. The `jwt` alternative is quadratic on crafted input (older; the lead's round 2 note 10).**
- MEASURED (`p_perf.py`): 1 MB of `-eyJ` repeated took 534 s.
- Every other 1 MB shape I built took 0.6 to 1.0 s, including the worst cases I could build for the three new alternatives.
- P0.6 now applies this cost to every history blob as well as every file. It takes crafted input (BELIEVED), outside the threat model.

**O4. A stream whose `reconfigure` exists and raises crashes the gate (P0.6's line, contrived).**
- MEASURED (`p_d1.py`): streams of my own making whose `reconfigure` raises `io.UnsupportedOperation`, `ValueError` or `NotImplementedError`, or whose `__getattr__` raises, make P0.6's gate exit 1 where 37640f0's exits 0. The guard is `hasattr`, not a `try`.
- A closed `TextIOWrapper` exits 1 in all three gates. I know of no real stream that behaves like my contrived ones (BELIEVED).

## What held

**The freeze and the setup.**
- MEASURED: SHA256SUMS begins `cf449592719ce7c7`, and 295 of 295 files match at the start and at the end.
- The tree equals the 15 staged versions in the real repository byte for byte.
- Against 37640f0 it differs only in the 11 files the ledger names plus the 4 new review files.
- The placed round2.md differs from its source only in the three redactions its README states. The READMEs' hashes and escape counts match.

**The runner, in copies.**
- A `git init` copy (run `20261026-043210-39130-f27b808`) and a clone of the real history with the tree committed over it (run `20261026-043225-39312-612136d`) each gave 18 stages passed, 6 skipped by name, exit 0.
- Tests total 2,557: docs 179, tool-tests 184, vocab-tests 12, format 958, custody 23, p1 1,169, control-tests 32.
- The clone's privacy line reads 295 files, 8 messages (7 plus my overlay), 118 versions in earlier commits and 2 known. Controls: 40 of 40 caught in both.
- The quick budget in the `git init` copy: 15 passed, 3 skipped, exit 0.
- A no-.git export and a depth-1 clone each passed `--only lint,docs,tool-tests,privacy,privacy-controls`.

**Scope 1, D1.**
- In-process (`p_d1.py`, 12 stream shapes, both modes, three trees, three gates): stdout None, StringIO, and TextIOWrapper over BytesIO in cp1252, ascii-strict and utf-16 all exit 0. A tree with CJK names under cp1252 or ascii-strict exits 0 on P0.6's gate and 1 on the older two.
- Real processes (`p_d1b.py`): stdout to a file, an append file, NUL and a pipe; `&gt;&amp;-` and `&gt;&amp;- 2&gt;&amp;-` in Git Bash; 13 `PYTHONIOENCODING` values in both modes; UTF-8 mode, legacy stdio and unbuffered. All exit 0.
- Git Bash's `&gt;&amp;-` does give `sys.stdout is None` (MEASURED).
- A pipe whose reader has gone exits 120 in all three gates, so it is not P0.6's.
- With a finding in the tree, None and StringIO exit 1 in both modes (`p_d1c.py`).
- The Python 3.13.5 gate passes, as do `-W error` and `-X dev`.
- The new process test is killed by the lead's two D1 mutants (re-run) and by my `sys.stdout is not None` mutant, through its StringIO case.

**Scope 1, D2.**
- `env_unguarded` flags exactly the deletion of the instruments guard and nothing in the shipped runner.
- `not_simple` allows a variable read only as `"${NAME}"` or `"${NAME:-}"`, and the rule's regex reads both, so it misses nothing in an allowed command form.
- The lead's three D2 mutants are killed again, and so is my `${NAME}`-blind one.
- The three notes' tests are killed by the lead's mutants 2, 3 and 4 (re-run).

**Scope 2, the history reader.**
- Fuzz (`p_fuzz.py`, 400 repositories) against an independent oracle, `ls-tree` over every commit.
  - Repositories were built with plumbing: 20 exotic names (line feeds, carriage returns, non-UTF-8, tabs, quotes, backslashes, HEAD/head, `--`), gitlinks and merges.
  - Result: every pushed blob read, no overlap with the index, no extra blob, every text key found, every history-only binary listed. Problems: 0.
  - Round 1's D1 put back is flagged in 17 of 40 seeds.
- Differential (`p_diff.py`): 160 random repositories with random worktree states. The 37640f0 gate and P0.6's agree outside the history clauses. Differences: 0.
- Damage (`p_damage.py`): a deleted, cut or garbage key blob, and a deleted commit or tree, all exit 1 with a finding.
  - Pack, repack and a replace ref still find the key.
  - A graft or `.git/shallow` hiding the key's commit gives exit 0, and `git pack-objects --revs` does not send the key either (`p_graft.py`). A replace ref sends it, and the gate finds it.
  - A partial clone with its promisor gone fails closed in 10 s, as the docstring says.
- Shapes (`p_clones.py`, `p_depths.py`): depths 1 to 9 and after `--unshallow`; `--shared`; `--reference`; blobless partial clone; reftable; linked worktree; a non-ASCII directory name with spaces. All pass.
- Scale (`p_scale.py`): 500, 1,500 and 4,500 commits took 2.0, 3.6 and 7.9 s, which is linear.

**Scope 3, the known list.**
- Blob `7671e68` is round4.md as pushed in 20d40e6 (SHA-256 `d014f919…`).
- Over all 38 alternatives its only findings are two, both on line 94: `wsl-unc-slash` and `url-quoted-drive`. Each ends in the placeholder `name`.
- `KNOWN` holds exactly those two keys and is read only in the history loop (READ).
- Put-back (`p_known_putback.py`): the pushed bytes as an untracked file, or as a staged version, are findings. The bytes plus a key line are a finding. The same bytes under a new path, committed and deleted, stay excused. That is the same oid and the same judgment, so I take it as by design.

**Scope 4, replace refs.** Every git call in the gate takes `git_env()` (READ). The lead's three replace mutants are killed again, and the ledger's packed-refs side effect is true (`p_packedrefs.py`).

**Scope 5, the spellings.**
- Found (`p_enc.py`):
  - `Path.as_posix` and `Path.as_uri` of a WSL UNC path, with both hosts.
  - `quote(…, safe=':')` and an encodeURI-like encoding, also after `%20`.
  - JSON once and twice, `repr`, an 8.3 name, and `os.path` joins.
- The 40 plants are caught.
- The 19 spelling mutants of rounds 1 and 2 are killed again. Mine, except one over-match noted below, are killed.

**Scope 6, pipes and links.** Read, plus the lead's mutants 17 and 18 killed again. The real FIFO and symlink branches did not run here (see below).

**Scope 7 and 8, the runner, the registry and unintended changes.**
- The lint pin, the guard words, the tab-indented comment and the stage script's message all hold.
- pytest-stage.sh differs from moth-quantum's only as its header says (diff).
- The runner's header matches its code.
- In scratch copies the shipped runner exits correctly for skips, `--require-all`, an unknown or empty `--only`, and a negative control that passes, fails for another reason, or fails for the right one.
- 37640f0's two test files run against P0.6's code: 270 pass, 4 fail. All 4 failures are intended changes (the staged-arm assertion and the pinned stage-script hash).

## Notes

**Test gaps, shipped code right.** These are mutants that survive (`mutants\m4a.py`, `m4b.py`, run by `hm4.py`, which runs the targets unmutated first).
- **T1. Masking.**
  - No test anywhere checks that a finding is printed masked. Five mutants survive all 184 tools tests: the history, file, staged and message findings printed whole, and a mask 24 characters wide.
  - The shipped code does mask. P0.6 added a new print site, the history findings and the known lines, without a test. A test planting a key in a file, a staged version, a history blob and a message would hold the property.
- **T2. History framing.**
  - No test reads two history-only blobs in one batch. The mutant `at = end + 1 + size` survives all 184 tools tests.
  - It raises IndexError on a clone with real history (MEASURED). Only the privacy stage on a repository with history would catch it, not a `git init` copy or a shallow clone.
- **T3. Runner behaviours.**
  - Three runner mutants survive the 157 registry tests: `--require-all` ignored, a run of zero stages passing, and an uncounted negative control that passes.
  - The shipped runner is right (above). The new end-to-end test could carry them cheaply.
- **T4. Small ones.** A line reading two variables is held by no test (`env_unguarded` reading only the first survives). `url-quoted-drive` with the separator after `Users` optional also survives; that over-matches.
- Three more mutants survive and are equivalent or the stated limit: the comment strip in `env_unguarded`, the loose guard-call regex, and the lint pin's fourth word.

**Prose.**
- The ledger says the `missing` arm is "an arm no real repository reached", and the test docstring says rev-list fails first on a real missing blob. Both are true of a deleted object only.
  - MEASURED (`p_missingarm.py`): a history-only blob whose loose object is overwritten with garbage makes `rev-list` exit 0, and `cat-file --batch-check` and `--batch` each print `&lt;oid&gt; missing`.
  - The gate then prints `unreadable: its object missing`. The test could use a garbage object instead of simulating the listing.
- The registry docstring names two cases of `need_env`: a line that reads the variable is held, and a stage whose tests read it is not.
  - A third is unstated: a well-formed `need_env` in front of a stage that reads no variable passes every rule (`p_registry.py`: `need_env QRO_MOTH_ROOT` before p4). It would skip p4 by name wherever the variable is unset.
- The lead's `m_p06_r1.py` mutant 24 no longer applies: its text occurs twice since `env_unguarded` copied the line, so `hm_t.py` prints N/A. My `u1` covers the same fault and is killed.
- Spellings that pass (`p_enc.py`, `p_enc2.py`):
  - New: `<a home path>Ubuntu/home/name`, with a backslash host and slashes after.
  - Round 3's notes 5 and 7, still true: an encoded space before a POSIX, Git Bash or WSL-mount home path; `quote()` of an `as_posix` WSL path (`//wsl%24/…`); and a file URL through the WSL host's `/mnt/c`.
- One line, as the lead asked: the gate's git calls pass no CREATE_NO_WINDOW.

**Mutation.**
- The lead's mutants, re-run on the final tree with `hm_t.py`: round 3's 8 of 8 killed, round 2's 11 of 11 killed, round 1's 46 killed and 1 N/A.
- Mine: 23 mutants, 9 killed and 14 survived. The survivors are T1 to T4 plus the three equivalent ones.

## What I did not do

- I did not run `pythonw.exe` or a detached process again, on the lead's instruction. The stop came mid-run of my first `p_d1b.py`. Git Bash's `&gt;&amp;-` and the runpy shape give the gate the same `sys.stdout = None`.
- I ran no native Linux, macOS or WSL. Real FIFOs, real symlinks (`os.symlink` gives WinError 1314 here) and non-UTF-8 names on a real file system did not run. The simulated branches did.
- I had no console (TTY) stdout, no git hook and no real push. `git pack-objects --revs` stands in for a push.
- Python 3.13 ran the gate only. pytest is not installed there and I installed nothing.
- I did not re-measure CLAUDE.md's idle timings.
- I did not read the worktrees, the ledger, other verifiers' directories (apart from P0.6 r1 to r3), `~/.quantum-film`, any `.atlas` or any credential file. I did not contact IBM or Atlas, and pushed nothing.

## Slips

- **Stray file in frozen\.** `p_known.py` imported the gate from `frozen\tree` with `python -I`, which ignores `PYTHONDONTWRITEBYTECODE`.
  - It left `frozen\tree\tools\__pycache__\check_privacy.cpython-312.pyc`; the tree now has 296 files.
  - The 295 listed files still match SHA256SUMS. I did not delete the stray file, since the brief forbids writing in frozen\. Please delete that directory.
  - Every probe since imports from `CK\tree_plain`, a copy.
- I wrote one stray file to the system temp, outside CK, and removed it with my leftover probe temp directories.
- I deleted `CK\base_blobs.txt`, because it listed record names that carry job ids.
- I ran `git status --short` three times in the real repository, and git may refresh its index stat cache. At the end it was still at 37640f0 with the same 15 staged paths and no lock. moth-quantum was clean at 3a73823.
