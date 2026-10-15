# P0.1 verifier, round 1

I tried to write this to `SCRATCH\verifier-P01-r1\report.md`. The harness refused ("Subagents should return findings as text"), so this message is the record.

Labels: READ (in a file), MEASURED (I ran it, with the script or command named) or BELIEVED (my inference). My scripts, logs and mutant sets are in `SCRATCH\verifier-P01-r1\check\`. I edited nothing in `frozen\` or in the real repository.

## 1. Verdict: NOT READY

This is round 1 of the loose cap, so I applied the full bar. I found three defects:

- **D1 is about what a gate does.** The stage registry's pin on pytest's configuration passes ini files it says it refuses. The docstring and the ledger carry the same false sentence.
- **D2 is about what code does.** The new merge of `plants_<parcel>.py` modules crashes at import when a plants module is imported before the registry.
- **D3 is about the shared-files preparation as a whole.**
  - A parcel doing what CLAUDE.md item 7 says fails three quick-budget stages and must edit the lead's files.
  - The causes are one of P0.1's tests, one generated page, and what item 7 leaves out.
  - The merge code itself does what it was written to do.

Everything else I tried held. Every code change P0.1 made for round 6's notes gives the right answer. That covers the case rule over every path, the root that is never an action, the metadata file's link and exact-name checks, the walk's order, `time()`, and the privacy gate's four new forms and bounded key pattern. I found no wrong accept, wrong refusal, crash or wrong exit code in any of them (section 3).

| finding | about |
|---|---|
| D1, D2 | what code does (D1 is also a false claim) |
| D3 | what the prepared files do when used: one test, one generated page, and item 7's prose |
| 4.1 | what code does, below the bar |
| 4.2 | test reach: the shipped code is right and a fault would pass |
| 4.3 | prose |

## 2. Defects

### D1. [gate, and a false claim] The pinned pytest configuration passes ini files it claims to catch

**Claim (READ).**
- The docstring of `tests/docs/test_stage_registry.py` says: "pytest's own configuration is pinned: no conftest.py, no ini file, and exactly the options in pyproject.toml the stages assume".
- The function's own docstring says "a conftest.py, an ini file or an option could take a test file out of its stage unseen by the rest of this registry".
- The ledger's P0.1 entry says "There is no conftest.py, no ini file, and exactly the options the stages assume".

**What the check reads (READ).**
- Every `conftest.py` below the root.
- The names `pytest.ini`, `tox.ini` and `setup.cfg` at the root only.
- The `[tool.pytest.ini_options]` table of the root `pyproject.toml`.

**Fault (MEASURED, `check\pytest_cfg_probe.sh`, output `check\pytest_cfg_probe.out`, pytest 9.1.1).** Each of these files, holding `--ignore=tests/format/test_hostile.py`, makes `bash verify/pytest-stage.sh tests/format` print "296 passed" where it prints "623 passed". The registry test `-k pytests_own_configuration` still passes.
- Nested files: `tests/format/pytest.ini`, `tests/format/.pytest.ini`, `tests/setup.cfg`, `tests/tox.ini`, `tests/format/pyproject.toml`. pytest takes its ini file from the ancestors of the paths it is given, so a nested file wins over the root's. This does not depend on pytest's version.
- Root files: `pytest.toml`, `.pytest.toml`, `.pytest.ini`.

At the runner (`check\run_cfg_plant.log`), only `tests/format/pytest.ini` is planted, with `addopts = -p no:cacheprovider --ignore=tests/format/test_hostile.py` and `pythonpath = ../..`. Then `bash verify/run.sh --budget quick` ends `passed 14, failed 0` and `== PASSED`, and 327 tests of the `format` stage never ran. Under item 7 each parcel gets its own `tests/<parcel>/`, so a stray ini file there is plausible.

**Second face (MEASURED, `check\w_venv`).**
- The same function scans untracked and ignored directories.
- A repo-local virtual environment holding one third-party `conftest.py` (for example under `.venv\Lib\site-packages\somepkg\`) makes it fail on a correct tree.
- `shape_problems`, its neighbour, skips dot-directories. This function skips only `.git`.

**A way out, measured and not applied.** With `-c pyproject.toml` added to the pytest command, the root `pytest.toml` and the nested `pytest.ini` no longer change the count (623, `check\w_cfg3`).

### D2. [code] The plants merge crashes when a plants module is imported before the registry

**Fault (MEASURED, `check\w_imp`).** I wrote a stand-in `controls/plants_p1.py` the way P0's own plants are written: `from controls.registry import RAW, twin`, one function, and a `PLANTS` dict naming `job-reattributed`.
- `python -c "from controls import registry"` works, and the merged table holds the new name.
- `python -c "from controls import plants_p1"` and `python -c "from controls.plants_p1 import job_reattributed"` both end in `AttributeError: partially initialized module 'controls.plants_p1' has no attribute 'PLANTS' (most likely due to a circular import)`. It is raised at `controls/registry.py` line 217, in `merged`.
- A parcel's test file whose first import is its own plants module fails at collection (`pytest tests/p1`: "1 error during collection").

**Why.**
- The registry's last statement imports every `plants_*.py` while `controls.registry` is itself still being imported.
- A plants module that imports the registry, which is the natural way to reach `twin`, `RAW`, `_metadata` and `_reseal`, only works if the registry was imported first.
- Neither the registry's docstring nor item 7 says so.

**Why no test notices.** The new test hands `merged` fake modules, so no real file is ever discovered. These mutants survive every test and stage: the glob changed, the glob matching nothing, and the import naming the wrong package (`check\mut\logs\hand_*.log`, mutants 32 to 34).

### D3. [the prepared files fail their purpose on first use] A parcel following item 7 fails three quick-budget stages and edits the lead's files

The ledger says P0.1 prepares "the files that parcels building at once would share". ParcelRound's METHOD.md section 2 (READ) says what that is for. Anything several parcels touch "is the lead's", and the question is "what would make the seam disappear, not what would make it small". The ledger lists no files each parcel would touch.

**One parcel (MEASURED, `check\w_first`, log `check\run_first_parcel.log`).**
- The parcel does exactly what item 7 says: one plants module planting `job-reattributed` (with its step registered), a `tests/p1/` directory with a uniquely named test file, and one stage line.
- `bash verify/run.sh --budget quick` ends `passed 11, failed 3`.
- `controls-run` and `twin` pass, so the plant itself works.

| stage that fails | why |
|---|---|
| `control-tests` (1 test) | `test_a_parcels_plants_join_p0s_and_a_name_planted_twice_is_refused` uses `job-reattributed`, P1's own control, as its stand-in. The merge rightly raises "which another module already plants". The parcel must edit the lead's test. |
| `vocabulary`, and `tool-tests` (6 tests) | `docs/CONTROLS.md` is generated from the merged `PLANTS` (its `built` column). One plant turns a `pending` into `yes`, and `gen_vocabulary --check` reports drift. The parcel must regenerate a shared generated page, and two parcels regenerate adjacent rows. |

**Two parcels (MEASURED, `check\mergesim`).**
- P1 and P2 each add a plants module, a `tests/<parcel>/` directory, one stage line, and an import of their own module in `qro/__main__.py` so that their steps register.
- Merged, the plants modules and test directories do not conflict. These do:
  - `verify/run.sh`, the stage lines.
  - `qro/__main__.py`, the import that makes a parcel's steps register. Item 7 does not say where registration code is imported, and the command line imports none of a parcel's (READ: it imports `canonical, checker, custody, fixture`). Plants have a glob, but steps, raw forms, count rules and generators have none.
  - A test file name used by both parcels. `test_no_two_test_files_share_a_basename` refuses the pair, and item 7 does not say to prefix names.

**The registry cannot host six of the pending rows (MEASURED, `check\w_states`).**
- `controls.run.outcome` and the test over every built control know two outcomes: accepted, and refused by name.
- Five rows say `states`: P3's `single-runs`, `readout-unbounded` and `time-confounded`, and P5's `unit-incomplete` and `not-interleaved`.
- One row is `refused` with no name: `joint-omission`.
- With `single-runs` planted, `python -m controls.run` prints `WRONG single-runs accepted; section 11 says "not isolated from the pipeline…"`.
- So P3 and P5 must both change `controls/run.py` and the lead's test.

**Category.** The code behaves as written. The preparation does not do what the ledger says of it: "CLAUDE.md's item 7 says what else each parcel keeps to itself".

## 3. What held

**Freeze and run.**
- **Freeze (MEASURED).** `sha256sum -c` gives 241 OK and no other line, and the file list equals SHA256SUMS. The real repository's tracked files are byte-identical to `frozen\tree`. Both held at the start and at the end.
- **Runner (MEASURED, `check\run_full_1.log`).** I ran `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` in a `git init` copy with no commit. Run `20261015-073410-15961-nocommit+dirty` passed 17, failed 0, skipped 0.
  - Test counts: docs 76, tool-tests 49, vocab-tests 7, format 623, custody 21, control-tests 20.
  - controls-run: 9 of 9 with 21 pending.
  - study-plants: 68 faults refused, 6 right variants accepted.
  - privacy: 241 files and 0 commit messages (my copy has no commit).
  - privacy-controls: 37 of 37.
  - instruments: 5 of 5, with moth-quantum at 3a73823 and clean.
  - check-docs: 10 documents, 24 other markdown files, 34 source files.
  - The twin is `ff3fe486…`. The negative control is refused `raw-digest at data/raw.counts.json`.
  - Every count equals the ledger's.
- **Timing (MEASURED).**
  - Quick budget: 32.4, 31.3 and 31.7 s, 14 of 14 each. CLAUDE.md's "~30 s" holds.
  - Full run: 84.5, 86.5 and 83.8 s (see 4.3 for "~75 s").
- **Order independence (MEASURED, `check\w_order`).** All 796 tests pass with the test files in reversed order, and each changed test file passes alone. On WSL (Python 3.10, below the project's floor) 792 pass and 4 fail. All 4 are `ModuleNotFoundError: tomllib`, in the registry's new test.

**The round 6 code changes.**
- **Case rule.**
  - An independent oracle written from FORMAT.md item 11, against `reader._graph` (`check\scripts\fuzz_case.py`): 239,467 random graphs over three seeds, 0 disagreements on accept, refuse, or kind of refusal.
  - The old reader against the new on 105,698 structure-aware mutants (`gen_mutants.py`, `run_reader.py`, `classify.py`):
    - 81,664 are identical.
    - Old accepted and new refuses: 2,173 for case, 1,180 for a path that is both a file and a directory, 145 for an action root.
    - The other 20,536 were refused before and still are: 15,502 under the same name, 5,034 now under `graph-form` where they were `spelling`, `term-unknown` or `field-kind`.
    - None is unexplained.
  - On ext4 end to end (`case_e2e.sh`): `data/A/x` with `data/a/y`, and `data/A` with `data/a/b`, which the old tree accepts, are refused `graph-form` with exit 1. Two files in one lower-case directory keep their identity.
- **Root.** The only action type is `CreateAction` (`V.ACTION_TYPES`). All 4,962 mutants with a root typed `CreateAction` and `Dataset` are refused by the new reader, and 228 of them the old reader accepted.
- **Metadata file.**
  - On ext4, old against new (`probe_meta.sh`): a link to a file inside, a file outside, a dangling link, a loop, and a link to a directory were each `file-missing` and are now `file-link`. A directory, a pipe, capitals only, and capitals beside the real file are unchanged.
  - On NTFS (`probe_win_meta.py`): a junction is `file-link` now. Capitals are `file-missing` now where Windows said `file-unlisted`, as on Linux.
- **Walk.** On ext4 with a link in each of twenty directories (`probe_walk.sh`), the old tree refuses at a place the host chose and the new at `a/link`.
- **On-disk differential (MEASURED, `disk_diff.py`, `run_disk_diff.sh`).** 4,500 random crates on ext4 as `nobody`, with 1 to 3 random disk faults each.
  - 3,536 identical.
  - 656 changed from `file-missing` to `file-link` (the metadata link).
  - 246 kept the refusal and changed its place (the walk).
  - 54 changed from `file-link` to exit 2, and 8 from exit 2 to `file-link` (the walk's order, see 4.1).
  - Nothing else.
- **Random crates on Windows (MEASURED, `gen_crates_p01.py`).** 250 valid crates and 4,596 injected faults gave identical verdict logs for the old and new trees (4,845 verdicts).
- **`time()` (MEASURED, `time_diff.py`).** 200,000 datetimes covering UTC, offsets, naive, a tzinfo with no offset, and odd offsets. The only difference is the intended one: `AttributeError` became `ValueError` (24,913 cases).
- **Privacy gate.**
  - Old key pattern against new, across the nine named-key alternatives (`key_diff.py`): 2,700,000 comparisons, identical wherever every whitespace run is 16 or fewer.
  - The four new patterns over 75,162 files and 854,139,382 characters of the Python installation and its packages (`priv_corpus.py`): 0 hits, so no false positive found.
  - Each new pattern is linear on the pathological inputs I tried (`priv_perf.py`).
  - 16,000 spaces after `token`: 1.2 s old, 0.3 ms new.
- **The lead's 13 hand mutants, re-run by me** (`check\mut\m_p01.py`): 13 of 13 killed.

## 4. Notes (below the bar)

### 4.1 Code: what it does, below the bar

1. **An unlistable crate directory with bad metadata is now exit 2, and was exit 1 (MEASURED, `probe_perm.sh`, ext4 as `nobody`).**
   - A crate directory at mode 311 with non-JSON metadata used to give `REFUSED spelling`, exit 1. It now gives "cannot be read here", exit 2.
   - `check()` now lists the directory before reading the metadata.
   - FORMAT.md item 16 puts "the crate's own files and directories" under exit 2, so the new answer matches the text. No test holds the case.
2. **The walk's order changes which of two faults a crate reports (MEASURED, on-disk differential).** With a link in one directory and an unlistable directory in another, the exit class was chosen by the host's order. It is now chosen by name order, the same on every host. This is the fix, and it moved 62 of 4,500 crates between exit 1 and exit 2.
3. **The quadratic backtracking P0.1 fixed in the key pattern remains in `address` and `escaped-address` (MEASURED, `priv_perf.py`, `quad100k.py`).**
   - One search over a run of letters with no `@` takes 0.56 s and 3.1 s at 20,000 characters, and 13.9 s and 77.5 s at 100,000.
   - The longest such run in the tree is 101 characters.
   - Nothing holds the key pattern's bound either. The old unbounded pattern restored passes every test and stage (hand mutant 0).
4. **The key pattern's bound is 16 whitespace characters, and the gate's docstring does not name it (MEASURED, `key_diff.py`).** A name, 17 spaces, `=` and a key passes. The old pattern caught it. Layouts aligned beyond 16 columns are rare. The docstring's list of what it cannot see is the place to say so.
5. **Forms the privacy gate still misses (MEASURED, `priv_variants.py`, made-up names).** All fall under the docstring's "a shape no alternative names passes", so none is a defect:
   - `smb`, `nfs`, `rsync`, `ftp` and `file` URLs with a `/home/` path.
   - A UNC written with forward slashes, the extended `\\?\UNC\…` form, a UNC with a share before `Users`, and a UNC with doubled (JSON-escaped) backslashes.
   - FreeBSD's `/usr/home`, `/System/Volumes/Data/Users`, and `/Volumes/<disk>/Users`.
   - A file URL whose drive colon is encoded twice, and one whose user name begins with a percent-encoded non-ASCII letter.

### 4.2 Test reach: the shipped code is right, a fault would pass

I ran 631 mutants (section 5). The survivors that matter:

| survivor | what would pass |
|---|---|
| `sys.exit(0)` in `check_privacy.py`'s `__main__`; the two modes swapped; the flag never read | The privacy gate always exits 0. P0.1 holds `run()`'s return value but not the line the runner reads, and both privacy stages exit 0 on a healthy tree. This is round 6's 8.1 item 1, one line further out. |
| the controls' `and not missing`; the three file controls (`ok = True`); the binary-file listing; the summary text | An alternative with no plant, a file control that catches nothing, a binary file never listed, and a wrong summary all pass. P0.1 holds one half of the controls' verdict. |
| the key pattern's bound (six mutants, from `{0,16}` to `{0,1}` to unbounded) | Nothing holds the bound's value or its speed. |
| the registry's glob, `sorted` and import (five mutants) | See D2: no real module is ever discovered. |
| `sorted(filenames)` in the walk (three mutants) | The order of names within one directory. The test reverses directories, and each holds one entry. Round 6's 8.1 item 11 named "the four mutants of `sorted` on names". |
| `reader.py:174`, the file and directory labels inverted (two mutants) | A file below a directory named like the descriptor is accepted at the reader. No plant holds the seed's kind. The checker then refuses it by another name. |
| `checker.py:44`, `not meta.is_file()` dropped (MEASURED, `mut44.sh`, ext4) | A metadata file that is a directory exits 3 with `IsADirectoryError`. One that is a pipe blocks (killed by a 10 s timeout). The shipped code refuses both `file-missing`. |
| `custody.py:70`, `not isinstance(v, list)` dropped | A scalar in a list-valued field would crash. |
| `custody.py:71`, `sorted` changed to `list` | Unsorted detection becomes hash-order dependent, so the mutant survives by chance. |
| the stage registry's plants: `tox.ini` and `setup.cfg` dropped, and the conftest scan cut to `tests/` | One `pytest.ini` plant stands for three names, and the conftest plant sits in `tests/`. |
| the case refusal's `where` | No test reads it. |
| `gen_vocabulary.py`'s exit 2 on a contradiction; `controls.run`'s count of a P0 row with no plant | Each prints but does not change the exit status. |

**Equivalent survivors, with their arguments.**
- `.casefold()` dropped or swapped for `.lower()` on the descriptor's name (already lower case) and on a path (the path spelling is ASCII, where they agree).
- `sorted` in the clash message (order of names in a message only).
- `len(graph) < 2` to `< 1`, and the `where` test at `reader.py:145`: the same refusal name, another location.
- The "one value, not a list" raise removed: `spelling.problem` refuses a list by another detail.
- `v in t.absent` without `isinstance`: `absent` is a tuple, so nothing is hashed.
- `[0]` changed to `[-1]` on a one-item list.
- `hasattr(p, "is_junction")`: the floor, 3.12, has it.
- `UnicodeDecodeError` dropped from a tuple that holds its parent `ValueError`.
- The root-action test on the first type only: the one action type sorts before `Dataset`.
- The fixture's `isinstance(obj, dict)`: a non-empty array fails later as `raw-form` anyway.

**Two more test-reach items.**
- **The new git-using tests inherit the user's global git configuration (MEASURED, `check\w_git`).** With `commit.gpgsign=true` in the global config and a signer that fails, 4 of `tests/tools`' new tests fail (`git commit` exits 128). `tool-tests` is in the quick budget. The helper sets only `user.name` and `user.email`.
- **`test_a_metadata_file_named_in_another_case_is_file_missing_on_every_host` can only fail on a case-insensitive host (BELIEVED, from the code).** On Linux the file is missing without the new clause. The lead's mutant of that clause was killed on Windows.

### 4.3 Prose

1. **FORMAT.md item 16: "A `PermissionError` is the exception: it is misuse, exit 2, whoever raises it" (MEASURED, `probe_permerr.py`).**
   - A `PermissionError` raised by a parcel's count rule or step exits 2.
   - One raised by its raw-form reader or its generator is refused `raw-form` or `metadata-generated` with exit 1, as the bullet above it says. "Whoever raises it" is too wide.
   - `qro/__main__.py`'s docstring (round 6's 8.2 item 5) still says a crash inside the checker, a parcel's code among it, exits 3. It was not touched.
2. **The ledger on the controls' summary (MEASURED, `ctl_summary.py`).** "Claims every plant caught only when each was" is not what the code does. With one alternative blind it prints `controls: 36 of 37 caught; every alternative has its own plant` and exits 1. The exit status is the signal, as in round 6.
3. **The ledger's "Round 6's test gaps (8.1), each now planted" is wider than what follows.**
   - Items 12, 13 and 18 are not in the entry's list, which is fair.
   - Within the list, see 4.2 for the privacy gate's exit line, the controls' verdict (one half), the file controls, the binary listing, and the walk's file-name sort.
4. **README.md:** "Its notes on the tests and the prose come next" is stale once P0.1 lands.
5. **CLAUDE.md "~75 s" for the full run:** I measured 84.5, 86.5 and 83.8 s on an idle machine. Round 6 measured 78 s on the previous tree. The quick budget's "~30 s" holds.
6. **Two descriptions not updated.**
   - The `docs` stage description in `verify/run.sh` (shown by `--list`) lists the older checks and not the two P0.1 added.
   - FORMAT.md's "Where each rule is written" row for the controls still points at `controls/registry.py` alone.
7. **CLAUDE.md item 7 (see D3).** It should name the files that remain shared:
   - the stage line in `verify/run.sh`;
   - the place a parcel's registering code is imported;
   - the regeneration of `docs/CONTROLS.md`;
   - test file names unique across `tests/`.

## 5. Mutation

**Harness.**
- Round 5's and round 6's `hmp_t.py` and `hm2.py`, over the six directories the runner runs.
- A survivor then runs `controls.plant twin`, the negative control, `gen_vocabulary --check`, `controls.run`, `check_docs` and ruff. For the privacy gate it also runs the plain gate and `--control`.
- Operators D, E and G of rounds 5 and 6, restricted to P0.1's changed lines, plus my hand mutants.

| set | mutants | killed | survived | n/a |
|---|---|---|---|---|
| D, E and G over the changed lines of `reader`, `checker`, `spelling`, `controls/registry`, `check_privacy` | 104 | 88 | 16 (5 equivalent, 11 gaps at 5 sites) | 0 |
| my hand mutants: the key pattern and four new alternatives; the registry's discovery; the stage registry's plants; the privacy `__main__`; the walk, the root, the case refusal | 57 | 18 | 39 | 0 |
| hand mutants at the round 6 gaps P0.1 says it planted | 9 | 5 | 4 | 0 |
| hand mutants at round 6's 8.1 items 14 to 17 | 16 | 14 | 2 | 0 |
| D, E and G at round 6's guard sites (type confusion, writers, fixture, seam) | 432 | 415 | 16 (14 equivalent, 2 gaps) | 1 |
| the lead's 13 hand mutants | 13 | 13 | 0 | 0 |
| **total** | **631** | **553** | **77** | **1** |

Of the 39 hand-mutant survivors, 23 are the key pattern's bound (6) and sub-shapes of the four new alternatives (17: a slash count, a dropped alternative, a lookbehind or flag removed). The table's design is one plant per alternative, so no test holds sub-shapes or near misses. The other 16 are in 4.2.

## 6. What I did not do, and my slips

- **Hosts not covered.**
  - No macOS, no Windows ACL change, no symbolic link on Windows (error 1314, as in round 6), and no Python 3.13 or later.
  - The permission cases ran on WSL (Ubuntu, Python 3.10, ext4) as `nobody`, which is below the project's 3.12 floor.
- **No commit trial.** I ran the runner in a `git init` copy with no commit, so the privacy gate read 0 commit messages there. The commit-message branch is held only by the unit tests and my mutants.
- **Not done at all:** a real-repository run of the runner, `rocrate-validator`, a JSON-LD processor, and review of P1 to P5.
- **No IBM or Atlas contact, no sensitive values.**
  - I opened no `~/.quantum-film`, no `.atlas` directory and no credential file.
  - I saw no key, token, CRN or job id.
  - I scanned no part of moth-quantum with the privacy patterns. It was read only by the runner's instruments stage and its fingerprint (`git rev-parse` and `git status` there).
- **No re-run of round 5's class-member sets.** My mutation covers P0.1's changed lines and round 6's gap sites, not the whole package.
- **My stand-ins are scratch only:** the plants modules, stage lines and registering imports in `check\w_imp`, `w_first`, `w_states` and `mergesim`.
- **Files outside `check\`.** I used `/tmp/p01r1` in WSL and a few lists in Git Bash's `/tmp`. I removed them all. pytest's own temporary directories remain under the system temp, as in earlier rounds.
- **Slips.**
  - Two of my Python heredocs lost a backslash (CLAUDE.md item 1): a stage line written with a literal `\n`, and a script tail. I redid both from files.
  - A `grep` for carriage returns and one for trailing whitespace gave false counts in this shell. I recounted with Python: the changed files hold no CR, and P0.1 added no trailing whitespace.
  - I ran `git status`, `git diff`, `git ls-files`, `git log` and `git archive` in the real repository. They are read-only, and its tracked files were byte-identical to the frozen tree afterwards.
  - I could not make `sleep` wait, so I polled.
