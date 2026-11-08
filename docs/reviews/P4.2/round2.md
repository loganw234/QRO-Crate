**Verdict: READY.** I found no defect in the code, a gate or the prose, and only notes. Two stages, privacy-controls and instruments, had not printed when I stopped (see the end).

## Checks and results

- **Freeze.** The `SHA256SUMS.txt` prefix is `ef460445`, and `sha256sum -c` over `tree\` is clean (411 files). The worktree's `gen_profile.py`, `p4_profile.py`, `p4_helpers.py` and `test_p4_tree.py` are byte-equal to the packet's.
- **Scope.** The lead's diff against 8fe0268 is the same 16 files, all P4's. The only files that moved since round 1's packet are the tool, `p4_profile.py`, `docs/P4.md`, `p4_helpers.py`, five test files and the five regenerated profile files. The changed files have no carriage return (READ).
- **Full runner** (MEASURED: `sbx-mid.sh bash verify/run.sh` with both env variables, on my copy committed as `d1031db`, run `20261107-183307-34369-d1031db`):
  - These stages passed: lint, docs, check-docs, vocabulary, tool-tests, vocab-tests, format, custody, p1, p2, p4 (285 s), profile, p4-shacl (284 s), control-tests, controls-run, twin, controls, study, study-plants and privacy.
  - p1-crates and p2-crates skipped by name, as the brief says.
  - So the engine stage still agrees with the evaluator.
- **profile/ is the tool's own output.** `gen_profile.py --check` says every file is exactly what its definition renders, and `gen_vocabulary.py --check` and `check_study.py` pass. The shape files differ from main only in the banner line, "three of the nine shapes of must/1_structure.ttl", and 1_structure.ttl does hold 9 shapes (READ).

## Round 1's rulings

**D1, the spy.**
- Mutants (MEASURED, my `hm_r2.py`, through `sbx.sh`, baselines first):
  - `defs_r1c.py`: 10 of 10 killed.
  - `defs_r1b.py`, ported only in the text of `drift`'s line: 61 of 64 killed. The three survivors are `_io.open`, B01 and B04.
  - My own `defs_r2d.py` (spy lists, the keyword and positional reading, load order, guard sets, the shape of `behind_a_link`): 25 of 28 killed. The survivors are G12, H7 and H8, discussed below.
  - `defs_r2e.py` (mutants that decide by `os.access`, plus `_io.open`): 6 of 6 killed.
- **`_io.open` is killed by the import guard**, not the spy (`test_the_tool_imports_only_the_modules_the_spy_covers`). The guard also kills a planted `from os import stat`, `import shutil` and `__import__`.
- **The spy is in before the tool loads.** All three tests that watch the tool use `load=True`: profile itself, the seven places, and the case-variant link `Validator`. The C1 test passes at all 7 places in both modes (14 tests).
- **The spy reads every path a call is given.** The keyword and second-path tests pass, and mutants H1 to H3 are killed.

**The tool's one change (`behind_a_link`).**
- **Differential run** (MEASURED, `diff_tools.py` against main's tool at 8fe0268, as processes, `--check`, `--write`, `--check`):
  - 25 states are identical.
  - Six differ only where a link stands on the way to a rendered path (told "missing" instead of "is a directory"), in the case-clash advice (C4), and in the name escape (C6).
  - Nine more states of my own show the same pattern. These cover a file where a directory goes, a junction at a nested directory, a link spelt `Validator`, and a link spelt `DATA`. A directory spelt in another case at a rendered file's place gets main's line, "is a directory, not the file its definition renders; run --write removes it", in all three states I ran.
  - Exit codes and the tree left behind are identical in all of them.
- **Nothing below a link is asked.** G1 to G11 are killed.

**D2, limit 24** (MEASURED, `probe_digits.py`, at all 42 leaves of the fixture's `@graph`):

| Digits | `spelling` | `graph-form` |
|---|---|---|
| 20 | 34 | 8 |
| 4,300 | 34 | 8 |
| 4,301 | 42 | 0 |
| 5,000 | 42 | 0 |

- This matches the words. "Some of 19" digits being past 2^63 − 1 is true.
- The eval test uses four terms, two of them `graph-form`.

**Notes 2, 4 and 5 to 8.**
- Note 2: the `os.access` mutants E1 to E5 are killed, so the told tests run both ways.
- Note 4: the G11 plant is in `tests/p4shacl`.
- Note 5: the banner is right.
- Note 6: the `--help` exit-3 sentence parses.
- Note 7: "it could not be taken away again" is gone from the tree, and a test holds it gone.
- Note 8: the docstring names `os.unlink`, `os.rmdir` and `os.access`.

**Junctions left behind.**
- Every mutant run's basetemp sweep reported 0 links removed, which includes the failing runs.
- Scans of my sandbox directory and of the latest three `pytest-*` folders found no junction. No new `garbage-*` folder appeared (the newest is 31 October).
- The builder's slips: the files it wrote are LF with no stray encoding (READ). I cannot check what it ran outside the launcher.

## Notes (none reaches the bar)

1. **Test reach.** The list entries of `OS_CALLS` and `OS_PATH_CALLS` are not all pinned by the independent `named` set.
   - MEASURED: taking `isdevdrive` out of the list *and* making the tool call `os.path.isdevdrive` below a link, 21 selected tests pass (my copy `mwe`). The unmutated spy kills that tool mutant, so this is a mutant of the spy, not of the tool.
   - Removing `getmtime` from the list changes nothing here, because it goes through `os.stat`.
   - The unpinned names are `readlink`, `chmod`, `mkdir`, `rmdir`, `unlink`, `remove`, `symlink`, `truncate`, `lexists`, `islink`, `isjunction`, `ismount` and `isdevdrive`.
2. **Documented blind spots.** A tool mutant that uses `os.system`, `os.popen`, `os.startfile` or `os.spawn*` on a path below a link is seen by neither the spy nor the import guard. The page and docstring say "a process" is unseen. The guard reads imports only, not these uses of `os`. I did not run such a mutant.
3. **B01 and B04** (the layout of `--help`) survive, as note 3 ruled. G12 (`exists()` for `is_dir()`) is equivalent, because a file at that place is a clash that `drift` skips.
4. **Prose.**
   - The `test_p4_tree.py` docstring says the stand-in "tells three calls of its path and no more". With `NotADirectoryError`, `dangling_link` also tells `stat`, `lstat`, `scandir` and `listdir`, as its own docstring says.
   - `--help`'s exit-3 line lists causes after a colon but omits a directory the host cannot list.

## Not done

- **privacy-controls and instruments.** At about 40 minutes of heavy load, privacy-controls had not printed and instruments had not started. Neither is P4's. The builder's and the lead's runs passed them.
- **Dangling junctions.** I made none (item 10); the dangling cases rest on the stand-in tests and on the builder's earlier measurements.
- **Other mutants.** I did not run P4's 847 mutants again, and I ran no `os.system` mutant.
- **Other hosts.** I did not test a host that makes symbolic links (note 9, left by the ruling).

My notes are at `<scratch>\verifier-P42-r2\check\notes.md`, and my scripts are in `<home>AppData\LocalLow\qro-sbx\p42-r2\scripts\`.
