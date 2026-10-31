# P0.8, round 4: the verifier's report

**Verdict: NOT READY.** There is one defect, and it is in what the code does. The checker decides which failures of "what is this listed entry?" are refused `file-link` by relying on `Path.is_symlink()` to raise for every failure except those that mean "not there". That holds for pathlib in Python 3.12 and 3.13. It does not hold for Python 3.14, where `Path.is_symlink()` returns False for every `OSError`.

On 3.14 a listed entry whose stat is refused or fails is refused `REFUSED file-link` (exit 1) with the reason "the host says it is not there". FORMAT.md items 12 and 16 say exit 2 (a refused permission) or exit 3 (any other error). The six tests that round 3 added to hold exactly that fail there.

The defect is latent on this machine, which has no 3.14. I show it by emulation and by the 3.14 documentation and source, not by a run of 3.14.

On 3.12.15 and 3.13.5 I found no defect. Every fix of rounds 1 to 3 holds. No crate is accepted that should be refused, no refusal has a name that is not the fault's, and no exit code is wrong. The privacy gate is not in the diff and let nothing through. The cap is reached, so only a defect in what the code does blocks, and this is one. It is not prose. I found nothing else that blocks. The lead can close it three ways (below), one of them a pin of the Python version.

Labels: READ means I read it. MEASURED gives the command or script. BELIEVED means I did not check it. SB is `<home>AppData\LocalLow\qro-sbx\p08-r4`, and my scripts are in `SB\scripts\`. Every command that runs code ran from SB through `sbx.sh` (low integrity), or through `sbx-mid.sh` where it says so. I read, printed and wrote no IBM job id, key or CRN. The full report is saved at `<scratch>\verifier-P08-r4\check\notes-p08-r4.md`. Beside it are `emul314.py` (the emulation), `s3_planted.py` (the table below) and `FIX1-prototype.diff.txt` (the fix I tried).

## Defects

### D1. Code (Python 3.14 and later), with the tests and sentences that rest on the older behaviour

**What the code relies on.** READ, qro/checker.py. `walk()` and `check()` ask `_is_link(p)` first and `_listed_not_there(p)` second. The docstring of `_listed_not_there` says why that order is enough: `_is_link`'s `is_symlink` "already raises for every failure of that question but those that mean 'not there'", so only those reach it. Three things rest on the same premise:
- the walk's docstring ("an entry the host raises on otherwise, raises the host's error");
- FORMAT.md item 12 ("Any other failure of that question ... is no refusal": a refused permission is exit 2, any other error exit 3);
- the six tests `test_any_other_failure_of_asking_what_a_listed_entry_is_is_no_refusal`.

**Where the premise holds and where it stops.**
- READ, Python 3.12.15 (`Lib\pathlib.py`, `is_symlink` and `_ignore_error`) and 3.13.5 (`pathlib\_abc.py`, which `Path` inherits: `_local.py` defines neither `is_symlink` nor `_ignore_error`). `is_symlink()` returns False only for ENOENT, ENOTDIR, EBADF, ELOOP and Windows errors 21, 123 and 1921, and raises every other error. So the premise holds there. MEASURED on both: the tests pass (below).
- READ, Python 3.14, three public pages fetched with the web tool, no file saved:
  - The 3.14 pathlib documentation has a "Changed in version 3.14" note on "Querying file type and status". It says `exists`, `is_dir`, `is_file` and `is_symlink` now return False instead of raising any `OSError`.
  - The reST source of that page says the same, and adds that the new behaviour matches `os.path.exists` and `os.path.isdir`.
  - The 3.14 branch's `Lib/pathlib/__init__.py` defines `Path.is_symlink` as `return os.path.islink(self)`, and the name `_ignore_error` does not occur in it. `os.path.islink` answers False for every `OSError`.
  - Round 3's report listed 3.14 among the things it did not check.
- So on 3.14 `_is_link` never raises. Every failure of lstat on a listed entry reaches `_listed_not_there`. Its own `os.lstat` fails the same way, and the entry is refused `file-link` with the detail "listed by its directory, but the host says it is not there", whatever the host said.

**The fault that shows it.** I have no 3.14 interpreter and could not make one. What I ran is an emulation: `SB\scripts\emul314.py` makes 3.12.15's `Path.exists`, `is_dir`, `is_file`, `is_symlink`, `is_junction` and `lstat` answer as the 3.14 source does. It changes nothing else.
- The tree's own tests. MEASURED, from `SB\tree-s` (a copy of the tree): `PYTHONPATH=SB\scripts PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_DEBUG_TEMPROOT=&lt;dir in SB&gt; bash sbx.sh python -m pytest -c pyproject.toml --noconftest -p no:cacheprovider -p emul314 tests/format/test_hostile.py tests/format/test_refusals.py` gives `6 failed, 418 passed`.
  - The six are `test_any_other_failure_of_asking_what_a_listed_entry_is_is_no_refusal`, at the listed directory, the listed file and the metadata file, for the refused permission and for the other error.
  - The same plugin over tests/format, custody, vocabulary, controls and p1 (2,573 tests, through sbx-mid.sh) gives `6 failed, 2567 passed`: the same six and nothing else.
- The command line's own mapping. MEASURED, `bash sbx.sh python -I scripts/s3_planted.py tree-a &lt;label&gt; [emul]`. Both calls that ask what an entry is, `os.lstat` and `os.stat` with `follow_symlinks=False`, are made to raise one error for one listed entry, as the tree's tests plant them. `qro.__main__._verdict` is then asked. The rows are identical at the listed directory, the listed file and the metadata file:

| what the host answers when asked what the listed entry is | real 3.12.15 (3.13.5 passes the same assertions) | 3.14, emulated |
|---|---|---|
| FileNotFoundError, NotADirectoryError | `REFUSED file-link`, exit 1 | `REFUSED file-link`, exit 1 |
| PermissionError | exit 2, "cannot be read here, refused" | `REFUSED file-link`, exit 1 |
| OSError EIO, OSError EINVAL | exit 3, the checker itself failed | `REFUSED file-link`, exit 1 |

- A case a person would meet (BELIEVED, not run, since this host is Windows): on Linux or macOS, as a user who is not root, `chmod a-x` on a crate's `data` directory leaves its names listable and its entries unstattable. On 3.12 and 3.13 `python -m qro check` answers exit 2, "cannot be read here, Permission denied". On 3.14 it would answer `REFUSED file-link at data/notes.txt: listed by its directory, but the host says it is not there ...`. That is a verdict on the crate for a fault of the user's permissions, with a reason the host did not give.

**Why it blocks.** It is a wrong refusal, by a reason the host did not give, and a wrong exit code, against items 12 and 16. It happens on an interpreter that `requires-python = "&gt;=3.12"` includes, and the tree's own tests fail there. It is the safe direction: nothing is accepted that should be refused, so the checker's central invariant holds. But the brief counts a refusal by a name that is not the fault's, and a wrong exit code, as defects. FORMAT.md item 12 and the docstrings were written to say the opposite. The claim and its tests are P0.8's: before it, the walk had no such question.

**What closes it.** Any one of these, the lead's choice.
1. Classify the error in the question itself, so that it no longer depends on what pathlib raises.
   - I tried this in a throwaway copy (`SB\mut\FIX1-explicit-not-there`, diff in `FIX1-prototype.diff.txt`). In `_listed_not_there`, the first `except OSError as e` re-raises unless `e.errno` is ENOENT, ENOTDIR, EBADF or ELOOP, or `e.winerror` is 21, 123 or 1921. That is pathlib 3.12's own list, so nothing changes there.
   - MEASURED: the 424 tests of the two files pass on real 3.12.15, on real 3.13.5 and on 3.12.15 with `emul314`. The 2,573 tests of the wider run pass on real 3.12.15. `s3_planted.py ... emul` gives exit 1, 2 and 3 as item 12 says.
   - The docstring sentences "already raises" and "raises the host's error" then want rewording.
2. With the change in 1, the six tests still pass on 3.12 and 3.13 without it, since `_is_link` raises first there. To hold the premise on every interpreter, plant pathlib's 3.14 answers in them: patch `Path.is_symlink` and `Path.is_junction` to the `os.path` forms, as `emul314.py` does. MEASURED: with that plant they fail without the change and pass with it.
3. Or decline 3.14: pin `requires-python` below 3.14 and say in item 12 that its answers are those of pathlib in 3.12 and 3.13.

## What held (all MEASURED unless marked)

**The freeze.**
- `sha256sum SHA256SUMS.txt` begins `d78e1d1200cba1f3`. `sha256sum -c` over `frozen\tree` gave 301 of 301 OK with 301 files, at the start and at the end. `SB\tree-a`, my copy, gave the same, and has no `__pycache__`.
- `diff -rq` against `SB\base` (a `git clone --no-hardlinks` of the real repository at 83503b0, remote removed) shows exactly seven files: CLAUDE.md, docs/FORMAT.md, docs/VALIDATION.md, qro/checker.py, tests/format/test_hostile.py, tests/format/test_refusals.py and tests/tools/test_tools.py. tools/, controls/, verify/ and qro/vocabulary.py are untouched, so the privacy gate is the real one.
- `scripts/hygiene.py`: the lines added are LF and ASCII, with no tab and no trailing white space. One added line is 123 characters (note 5).

**The runner, in two copies,** through `sbx-mid.sh` with `QRO_MOTH_ROOT=<repos>/moth-quantum`.
- A `git init` copy (commit 56d06c4) and a copy of the real history with the tree laid over it (commit 9223e5c). Each gave 18 passed, 0 failed and 6 skipped by name (p2, p4, p1-crates, p2-crates, profile, p4-shacl). Exit 0.
- Each passed 2,967 tests, as the entry says: docs 190, tool-tests 204, vocab-tests 12, format 1,337, custody 23, p1 1,169, control-tests 32. Base is 2,948, so 19 are new (nine of round 1, four of round 2, six of round 3).
- In the history copy the privacy gate read 301 files, 10 commit messages and 147 earlier versions, with its three known findings. Privacy-controls caught 40 of 40. Instruments reproduced 5 of 5. Lint covers 54 files and passes.
- Each pytest stage that uses a temporary folder printed 292 `(rm_rf)` warnings, the same in all of them in both runs. They are a state of the launchers' shared temporary folder (note 6), not of the tree.

**Round 1's fix, at every place, on this machine.** `scripts/s1_shapes.py &lt;tree&gt; &lt;label&gt;`: 17 shapes, each asked in process and as three processes (absolute path with `--fixtures`, a relative path with `--fixtures`, and a trailing separator with no `--fixtures`). Run on `tree-a` and on `base`, then diffed.
- Each of these is `REFUSED file-link` at its own place, exit 1, one line, in every form:
  - a dangling junction at `data/jct`, at `data` itself (the directory the metadata lists), and six levels down;
  - one with the target's parent gone too (path not found);
  - two in one directory (the first by name is named);
  - 15 with odd names (spaces, `%`, `#`, `&amp;`, non-ASCII);
  - one beside an unlisted file, and one beside a listed file with a wrong digest;
  - the crate asked through a live junction.
- The metadata file as a dangling junction, or as one whose target became a file, is `file-link` (it was `file-missing` in base). With both the metadata file and `data/jct` dangling, the metadata file is named first.
- A live junction to a folder that itself holds a dangling junction, and a live junction to the crate itself (a cycle), are `file-link` at the live junction, never descended. The fixture crate is accepted. Without `--fixtures` it is `step-unbuilt`, and with a dangling junction the walk refuses first.
- Against base, every dangling shape moved from exit 3 (or `file-missing` at the metadata file) to `file-link`. The plain crate and the live-junction shapes did not move.
- The wrong-case corner: a dangling junction named `Ro-Crate-Metadata.json` with no metadata file is `file-missing`, a live one is `file-link`, and a dangling one named `Notes.txt` in place of the listed `notes.txt` is `file-link`. That is what the restated sentence says for a host that cannot stat a dangling link.
- Under real 3.13.5 (guard loaded, below) the rows are identical to 3.12.15's.

**A model-based fuzz.** `scripts/s2_fuzz.py tree-a &lt;label&gt; &lt;first&gt; &lt;count&gt;`: random trees under the fixture crate mixing directories, unlisted files and four kinds of junction (live, dangling, dangling with its target's parent gone, target now a file). An oracle written from item 12 says which refusal and which place: `file-link` at the first link-ish entry in the walk's order, else `file-unlisted` at the least unlisted file, else accepted.
- Seeds 1 to 600 on the tree, in process, with every eighth also as a process: 0 in-process mismatches. The script printed eight flags, all one artifact of my comparison: the command line writes `é` as `\xe9` by design (item 16) and my oracle did not. Each flagged line shows the right refusal at the right place. Under real 3.13.5, seeds 1 to 150: the same one flag, no mismatch.
- The same harness on base, seeds 1 to 60: 42 mismatches, so it does see the fault.

**Round 3's and round 2's fixes, on 3.12.15 and 3.13.5.**
- `s3_planted.py` on real 3.12.15 (table above): not-there errors are `file-link`, a refused permission is exit 2, any other error exit 3, at the directory, the file and the metadata file.
- The tests hold what they name. Mutants through `scripts/mut4.py` and `scripts/runmut4.sh` (sbx.sh) over the two test files (424 tests), in copies under `SB\mut\`:

| mutant | result |
|---|---|
| M1, the question always False | killed by 12 |
| M2, the walk asks the question before the link test (the third verifier's N4) | killed by 4 |
| M3, `check()` asks it before the link test (N4's twin) | killed by 2 |
| M4, `except OSError` narrowed to FileNotFoundError | killed by 4 |
| M6, the listing test replaced by True | killed by 1 in those two files; by 3 over all of tests/format (also `test_cli.py::test_an_empty_directory_is_a_crate_with_no_metadata` and `test_sites.py::test_no_metadata_file_is_file_missing`) |
| M7, `check()` does not ask | killed by 3 |
| M9, the listing is of the grandparent | killed by 12 |
| T1, the plant covers `os.lstat` only | killed by 6 |
| T2, the plant covers `os.stat` only | killed by 6 |
| M5, the listing's `except OSError` narrowed to FileNotFoundError | survives all 1,337 tests of tests/format (note 1) |
| M10, the question asked after `is_file` | survives; it changes only the detail text of file entries (the lead's "left for P0.9") |
| M8, files before directories in a directory's own entries | survives all 1,337; pre-existing order (note 3) |

- M5, M6 and M8 over all of tests/format ran through `sbx-mid.sh` (bash tests included). No mutant here changes code that deletes.
- Under real 3.13.5 the 424 tests pass. The guard loaded there: `PYTHONPATH` put the agent venv's site-packages (pytest 9.1.1 and the venv's `sitecustomize.py`) on 3.13.5's path, and a probe write outside the sandbox was refused (nothing written).
- No `_unopenable` or `UNOPENABLE` is left in code or tests; the ledger's earlier entries keep the old names as history.
- Of the three sentences the ledger corrected in round 2, the first is true (READ, CLAUDE.md item 10 and the `links` fixture). I did not repeat the other two, which round 3 measured: that a stranded junction's target is its folder's old numbered path, and the date of Defender's signatures.

**P0's tests leave no junction, passing or failing.**
- `scripts/six_sessions4.sh a`: six pytest sessions of test_hostile.py and test_refusals.py, temporary root inside SB so pytest's numbered cleanup ran. 424 passed each, no warning, no `garbage-*` folder.
- Failing runs leave none either: M1 (12 failing), M2, M3, M4, M7, M9, T1, T2 and the emulated 3.14 run (6 failing) all ran with a temporary root inside SB. A scan of all of SB at the end (`scripts/scan_junctions.py`, which never descends into a junction) found 17,628 directories, 0 live and 0 dangling junctions, and 0 `garbage-*` folders.

**The machine, re-measured** (`scripts/probe_machine.py`). Item 10's sentences hold now:
- A dangling junction is named by `os.listdir`. The scandir entry says `is_junction` True and `is_dir` True.
- `os.lstat` and `os.stat` raise FileNotFoundError (Windows error 2). `lexists`, `islink` and `isjunction` are False, and so are `Path.is_symlink()` and `is_junction()`.
- `os.readlink`, `os.rmdir` and `os.scandir` raise.
- Once the target is made again every call works and `os.rmdir` removes it.
- Base's checker still fails on one here with FileNotFoundError, exit 3, so the machine is as it was when the round began.

**The gate.** `scripts/gate_scenarios.py tree-a g1` (the third verifier's, read first and copied unchanged):
- A skip-worktree or deleted tracked file with a dangling junction at its path is passed over and its index version read. A keyed version is found (exit 1), a clean one passes, and after the commit the history blob is found.
- At a gitlink's path git stages and commits nothing and the gate reads nothing. An untracked junction is listed by neither.
- Nothing leaked. tools/check_privacy.py is not in the diff.

**The walk's cost.** `scripts/timewalk.py`, 4,000 files, best of 4, twice: base 2.35 and 2.30 s, tree 2.94 and 2.93 s. That is about 25 to 28 percent more (one more `lstat` an entry), linear as before.

**The sentences.** CLAUDE.md item 10 is true on this machine, in each sentence I could measure. FORMAT.md item 12 and the docstrings are true on 3.12 and 3.13 and not on 3.14 (D1). The ledger's entry for round 3 is accurate in its figures, 2,967 tests and the format stage's 1,337. Of its nine mutants I reproduced five under my own names (M1, M2, M3, M4, M7), each killed as it says; I did not repeat the other four.

## Notes (below the bar)

Each is about prose, or about test reach where the code is right, unless it says otherwise. None is about a gate.

1. **Test reach where the code is right: M5 survives.** Narrowing the listing's `except OSError` in `_listed_not_there` to FileNotFoundError passes all 1,337 tests of tests/format. It shows only for `checker.check(&lt;path of a file&gt;)` in process, where the listing raises NotADirectoryError. The command line refuses a non-directory first, so it is not reachable as a process.
2. **Prose in a test.** tests/format/test_hostile.py line 371, the docstring of the real-junction test, still says "by the walk's question of what the host cannot stat". The question is now "says is not there".
3. **Prose that rests on a pre-existing order (not P0.8's).** M8 shows no test pins directories before files within one directory's entries. FORMAT.md item 12 says "the walk descends in name order, so a refusal names the same place on every host".
   - On this machine a dangling junction is a directory to `os.walk`. On a host that opens dangling links, a dangling symlink to a directory is not (`DirEntry.is_dir()` is False for a broken link), so it sorts among the files.
   - With two link-ish entries of different kinds in one directory, the place named can differ by host, and the refusal's name cannot (BELIEVED, not run: this host cannot make a symbolic link).
4. **Test reach: nothing holds the premise of D1 on 3.12 and 3.13** (D1, what closes it, point 2). It is part of D1, listed so it is not lost if the lead closes D1 by pinning the version.
5. **Lint (prose).** One line added to test_hostile.py is 123 characters (the `parametrize` of `test_any_other_failure...`). Ruff does not select E501 in this project (244 lines in the linted files are over 120), so no gate fails. The earlier rounds' "no line over 120" was true of their trees, not of this one.
6. **The warnings are a state, not a property of the tree.** 292 `(rm_rf)` warnings per pytest stage in both of my runs (208 in round 3, 160 in the lead's), the same in every stage, so they were there before and did not grow during a run. My six sessions with a temporary root of my own printed none. I did not read the shared folder.
7. **At the commit.** The ledger cites `round1.md` to `round3.md` of P0.8's reviews "placed at its commit". The tree holds no docs/reviews/P0.8/. When it does, docs/reviews/README.md and docs/README.md want P0.8's lines in the same change, since check_docs holds a page and its line together. Rounds 1 and 3 said the same.
8. **Claims I could not check.**
   - "P4's tool asks `_is_link`": P4's tree is off limits. `_is_link` is textually unchanged (READ in the diff); on 3.14 it no longer raises for any error either.
   - The P4, P2 and P1.2 figures.
   - The lead's own runs (`20261026-161022-21312`, `20261030-200045`, `20261030-202241`, `20261030-202810`, `20261030-214813`, `20261030-225613`, `20261030-234824`) and mutant logs (SCRATCH\p08\r*fix).
9. **The emulation models only six `Path` methods.** Other changes in 3.14 (urllib, json and the rest) are not modelled, so I say nothing of whether the whole suite passes on 3.14. Under the emulation, the suites I ran fail only the six tests of D1.

## What I did not do

- I ran nothing on 3.14, on a host that opens dangling links, or on Linux or macOS. The host cannot make a symbolic link (WinError 1314), and WSL's Python is 3.10, below the floor and outside the sandbox. Every statement about those hosts is READ, or an emulation.
- I did not change an ACL, so I produced no real PermissionError at `lstat`; the errors are planted, as the tree's tests plant them. I did not look for the machine's cause, or test what it does outside the sandbox's folders.
- I did not read or run P4's, P2's or P1.2's trees, the worktrees, the lead's scratch under SCRATCH\p08, the launchers' shared temporary folder, the round's ledger, or any other agent's directory.
  - I read the three earlier reports in `frozen\` and the third verifier's scripts (`gate_scenarios.py`, `scan_junctions.py`, `timewalk.py`, `checker_scenarios.py`, `diffrun3.py`, `six_sessions.sh`, `runmut3.sh`). I copied `gate_scenarios.py`, `scan_junctions.py` and `timewalk.py` unchanged.
  - I did not read the earlier verifiers' notes, or ParcelRound's METHOD.md in `frozen\` (the brief states its section 6 in a sentence).
- I ran Python 3.13.5 through `sbx.sh` with the agent venv's site-packages on `PYTHONPATH`, so that the venv's `sitecustomize.py` guard loaded (checked: it refused an outside write). The launcher's own interpreter is the venv's 3.12.15; 3.13.5 is not what the launcher names.
- I ran no mutant of code that deletes: the `links` fixture's and `unlink_made`'s removal (the earlier TA and TB) is not re-mutated, since those mutants strand junctions.
- Two stray invocations of the host's `python` with an empty standard input, from my shell and outside the launcher, by mistake while I was editing a script. They ran no code and wrote nothing.
- I read three public pages with the web tool (the 3.14 pathlib documentation, its reST source, and the 3.14 branch's `Lib/pathlib/__init__.py` on raw.githubusercontent.com), plus two long 3.14 pages that held nothing relevant. Nothing was downloaded to disk, nothing was sent, and no account or banner was involved. The summaries came through a small model, so I cross-read them: three sources agree.
- I contacted no one, accepted no banner and pushed nothing. My two repository copies have no remote.
- Cleanup: every junction I made was removed with its target made again (the scripts do it, and a last scan found 17,628 directories with 0 junctions). SB still holds my copies (`base`, `tree-a`, `tree-s`, `run-init`, `repo-clone`, `mut\`, the temporary roots) and the runner's `.gate-state` folders, whose logs I masked when I printed them.
