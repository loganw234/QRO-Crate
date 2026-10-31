# P0.8, round 1: the verifier's report

**Verdict: NOT READY.**

Three defects block it. D1 is what the checker does on this machine. D2 is the false sentence that goes with D1. D3 is also prose. No key reached a commit without a finding in any gate state I built, so the gate has no defect. The checker never accepted a crate in any state I built, so its central invariant holds. The changed test, the removal of `link_dir` and the entry's machine measurements hold.

Labels: READ means I read it. MEASURED gives the command. BELIEVED means I did not check it. The launchers `sbx.sh` and `sbx-mid.sh` are in `<home>AppData\Local\qro-crate\sbx\`. My scripts are in `<home>AppData\LocalLow\qro-sbx\p08-r1\scripts\`. I ran them from `p08-r1\` against `tree-init`, a copy byte-equal to the frozen tree.

The harness refused to let me write the report as a file. The only file I wrote to the check directory is the interim notes, `<scratch>\verifier-P08-r1\check\notes-p08-r1.md`.

## Defects

### D1. Code (the checker, on this machine): a crate holding a dangling junction exits 3, not 1 `REFUSED file-link`

**The fault.** Make a fixture crate. Put a junction at `data/jct`, make its target, then remove the target. Run `python -m qro check --fixtures CRATE`.

MEASURED, `sbx.sh python -I scripts\cli_streams.py tree-init cs1`. I ran it again as `cs2` after the lead's note, with the same result:

```
exit code : 3
stdout    : ''
stderr    : "FAILED: the checker itself failed, FileNotFoundError: [WinError 3] The system cannot find the path
             specified: '&lt;crate&gt;\data\jct'; this is not a verdict"
```

MEASURED, `sbx.sh` and `sbx-mid.sh python -I scripts\checker_scenarios.py tree-init low1|mid1`. Both launchers gave identical rows:

| Where the junction stands | in process | as a process |
|---|---|---|
| `data/jct`, listed by nothing | `FileNotFoundError` (WinError 3) | exit 3 |
| the crate root | same | exit 3 |
| two levels down | same | exit 3 |
| a listed file (`data/notes.txt`) replaced by it | same | exit 3 |
| the metadata lists `data/jct/secret.txt` | same | exit 3 |
| a junction whose target is now a file | `NotADirectoryError` (WinError 267) | exit 3 |
| the metadata file replaced by it | `Refused file-missing` | exit 1, `REFUSED file-missing` |
| the crate directory itself | none | exit 2, "no such crate directory" |
| control: a live junction at `data/jct` | `Refused file-link` | exit 1, `REFUSED file-link` |
| control: the fixture crate | accepted | exit 0 |

**Why it is a defect.**
- READ, docs/FORMAT.md item 12: "A symbolic link or a junction anywhere in it is refused `file-link`, the metadata file among them ... on every host."
- READ, qro/__main__.py: exit 3 is the checker failing, "never a verdict on the crate".
- Of the eight dangling or junction positions above, six give exit 3. The metadata-file case gives `file-missing`, and the crate directory itself gives exit 2.
- It is not a wrong acceptance. It is a wrong exit code, and for six positions a refusal that does not exist. On a host that opens the junction, the same crate is refused `file-link` (READ of `_is_link`; I cannot reproduce that host).
- P0's code is unchanged. MEASURED: `diff -rq` of the frozen tree against a `--no-hardlinks` clone at 83503b0 shows only CLAUDE.md, docs/VALIDATION.md and tests/tools/test_tools.py differ. The machine moved, and P0.8 is the piece that was to find what the move did to the checker.

**Cause.** MEASURED, `sbx.sh python -I scripts\walk_states.py tree-init ws1`, and again as `ws2` under `sbx-mid.sh`:
- `os.walk` lists the dangling junction under **dirs**. The scandir entry says `is_dir()` True and `is_junction()` True.
- So `checker.walk` never reaches `name in filenames and not p.is_file()`.
- `_is_link(p)` is False, because `lstat` raises.
- `os.walk` descends and `scandir` fails. `onerror=_unlistable` (qro/checker.py:166) re-raises, and the command line answers exit 3.

**What closes it.** This is the lead's choice, and D2 needs a rewrite either way.
1. Fix it. I tried one shape in a sandbox copy only, `<home>AppData\LocalLow\qro-sbx\p08-r1\mut\fix1`; nothing real is changed. In `walk()`, before `_is_link`, `os.lstat(p)` each listed name and refuse `file-link` where the host lists a name it cannot stat. In that copy every position the walk reaches gave exit 1 `REFUSED file-link`. `tests/format/test_hostile.py` and `test_refusals.py` passed, 405 tests. The metadata-file case still gave `file-missing`, where FORMAT.md 12 says `file-link`.
2. Or restate it as a known limit, by the behaviour it concedes. On a host that lists a junction it cannot open, a crate holding one exits 3 and is never accepted, and the metadata-file case is `file-missing`. FORMAT.md 12 would then need the same sentence.

### D2. Prose: the entry's "The checker" bullet is false in each sentence

The entry (docs/VALIDATION.md, "What it means for P0's code", headed "MEASURED or READ") says:
- "os.walk lists a dangling junction in a crate as a file." MEASURED false: it is listed as a directory (`scripts\probe_dangling.py`, `walk_states.py`).
- "`_is_link` says no, and is_file says no, so walk refuses the crate `file-link`, 'neither a regular file nor a directory'." MEASURED false: the walk refuses nothing and raises (D1).
- "The name the crate is refused by is the same on both hosts." False here. The checker gives no refusal for a junction in the walk, and `file-missing` for one at the metadata file. A host that opens the junction gives `file-link` (READ).

"P0's code is unchanged" is true. It does not make the checker's behaviour right.

### D3. Prose: the entry and CLAUDE.md item 10 name the wrong source of the stranded `garbage-*` folders, and item 10's rule leaves P0's own tests doing it

**What the tree says.**
- The entry: "it cannot clear old temporary folders that hold dangling junctions, which P4's tests left (item 10)".
- Item 10: "One that makes one [a dangling junction] leaves it behind in the sandbox, where pytest names the folder it cannot clear `garbage-*`."

**What the warnings name.** MEASURED, `scripts\warn_kinds.py` over the stage logs of my runs. Each count is warnings naming a garbage folder of that test dir, summed over one run's stage logs. Run 1 named 362 and run 2B (`20261030-210412-8409-90e343c`) named 235.

| Test dir named | run 1 | run 2B |
|---|---|---|
| P0's `tests/format` junction tests (`test_the_walk_descends_in_name0`, `test_a_directory_link_whose_fi0`, `test_each_plant_is_refused_by_4`) | 275 | 187 |
| P4's three tests | 42 | 21 |
| P0.7's old version of this very test | 18 | 9 |
| a test not in this tree (`test_a_directory_the_build_mad1`) | 27 | 18 |

About three quarters or more of the named folders are P0's own tests'. I cannot see which folders the lead's 44 named.

**The mechanism.** MEASURED, `sbx.sh python -I scripts\rename_cleanup.py rn1`, again as `rn2`, using `_pytest.pathlib` from the agents' pytest:
- `rm_rf` on a folder holding a **live** junction (target beside it) is clean, with no warnings.
- `maybe_delete_a_numbered_dir`, which pytest runs on an old `pytest-N`, renames the folder to `garbage-&lt;uuid&gt;` first. The junction's absolute target then vanishes. The same layout gives four `(rm_rf) error removing` warnings, and the junction stays, listed with `lexists` False.
- The three `tests/format` tests make that layout. A junction in `crate/` points to an `outside/` beside it (READ in test_hostile.py and test_refusals.py).
- By the mechanism and the warnings, each runner run's format session becomes stuck folders once pytest cleans it, and every later session re-warns for each. This is BELIEVED; I did not follow one session through.
- Those three tests with `--basetemp` in my directory, cleared by the next session's `rm_rf`, left nothing (`p08-r1\bt-format`).

**Item 10's rule misses this.** "A test that needs a link whose target is gone ... never makes one" does not stop these three tests. Their junctions are live when made. "A junction whose target exists behaves as before" is true of the calls, not of what pytest later does to it.

**The count is a state, not a property of the tree.**
- MEASURED: my stage logs show 52 to 92 warnings in run 1 and 80 in each stage of run 2.
- `tests/tools/test_tools.py` alone with `--basetemp` in my directory gave `204 passed` and no warnings (`scripts\runmut.sh low-tree tests/tools/test_tools.py`, low integrity).

**What closes it.**
- Restate the attribution.
- Add the mechanism to item 10: pytest renames its temp folders, so a junction made in one is stranded.
- Say that a test which makes a junction removes it (`os.rmdir`, while the target exists) before it ends.
- Whether P0's three tests change now or wait for P0.9 is the lead's call. Item 10 should not read as though they are clean.

## What held (MEASURED)

**The freeze.**
- The `sha256sum` of SHA256SUMS.txt begins `c92510ecfbc924e7`.
- `sha256sum -c` over `frozen\tree` gave 301 of 301 OK, with 301 files and none extra. I re-checked this at the end.
- The added text is ASCII, LF, with no trailing white space.

**The runner**, through `sbx-mid.sh`, with `QRO_MOTH_ROOT=<repos>/moth-quantum`:
- A `git init` copy: run `20261030-204601-5843-7927df8`. 18 stages passed, 6 skipped by name, 2,948 tests, tool-tests 204.
- The real history with the tree laid over it and committed (`90e343c`): run in two parts, `20261030-205941-7448-90e343c` (7 stages) and `20261030-210412-8409-90e343c` (11 stages and the 6 skips). 18 passed, 6 skipped by name, 2,948 tests.
  - Privacy read 301 files, 10 commit messages and 143 earlier versions, with the three KNOWN findings listed.
  - Privacy-controls 40 of 40.
- `tests/tools/test_tools.py` alone at low integrity (`sbx.sh`): 204 passed.
- Output files: `p08-r1\run-init.out`, `run-hist-A.out`, `run-hist-B.out`, and the `.gate-state` folders under `run-init\` and `repo-clone\`.

**The machine bullets reproduce.**
- The lead's `junction_probe.py` (low only), `junction_probe2.py` (both launchers) and `junction_winapi.py` (both launchers) give the entry's results:
  - the `lstat`, `lexists`, `islink`, `isjunction`, `readlink` and `rmdir` results;
  - `NotADirectoryError` (WinError 267) for a junction to a file, and recovery once the directory is made again;
  - `CreateFileW` with `OPEN_REPARSE_POINT` failing with error 2;
  - `GetFileInformationByName` not exported.
- `scripts\mklink_probe.py`: a junction made by `mklink /J` behaves the same.
- `cmd dir` shows `&lt;JUNCTION&gt; conf.md [..]`, and `cmd rmdir` fails.
- `scripts\open_variants.py`: 24 `CreateFileW` variants (6 access rights times 4 flag sets) all fail with error 2. `RemoveDirectoryW`, `DeleteFileW` and `SetFileAttributesW` fail with error 2.
- Something the entry does not say: `GetFileAttributesW` (0x2410) and `FindFirstFileW` (tag 0xa0000003) both succeed on a dangling junction. Listing works, and only opening fails.

**The old test fails here.** MEASURED, 83503b0's test in a copy (`scripts\runmut.sh old-tree tests/tools/test_tools.py -k a_link_left_dangling`). It fails at its own control, `assert os.path.lexists(r / "conf.md")`, "a dangling link: the test's control". That is the entry's premise.

**The changed test.** MEASURED, mutants of `passed_over` made with `scripts\mutate.py` and run with `scripts\runmut.sh` against 14 related tests:
- `exists` for `lexists`, the mutant it was written for, is killed by the changed test alone.
- `return rel in gone` and `.is_symlink()` are each killed by the changed test and `test_a_skip_worktree_file_still_on_disk_is_read`.
- `Path.exists()`, `isjunction` plus `exists`, and `isfile` are each killed by the changed test alone.
- Mutants of `held()` against the unchanged gitlink tests are killed too: `exists` for `lexists`, `return True`, and dropping the symbolic-link test.
- `link_dir` had one caller at 83503b0. `git show 83503b0:tests/tools/test_tools.py | grep -n link_dir` gives its definition and line 988. tests/format has its own helper of that name. The removal is safe.
- `simulate_links` came in with 20d40e6 (P0.4), as the entry says.
- Telling `lexists` moves nothing else. The lambda answers for any path named `conf.md`. For this tree (no gitlink), the only call in `check` that reaches it is `passed_over`'s. The patch is on the global `ntpath` and is undone at teardown.

**The gate against git on this machine.** `scripts\gate_scenarios.py tree-init g1`, and again as `g2` under `sbx-mid.sh`. The key text is built in pieces. The skip-worktree cases were also run as a process, `python tools/check_privacy.py`.
- A skip-worktree file with a dangling junction at its path: git says `S`. The gate passes it over and reads the index version. A keyed version gives findings and exit 1; a clean one gives exit 0.
- A tracked file replaced by one: git says `R` and `D`, and `git add -A` stages the deletion. The gate reads the index version, and after the commit it reads the history blob.
- **A gitlink whose path holds one, which the entry left unmeasured:** git says `R sub` and `AD sub`. `git add -A` stages nothing for it, and `git commit` has nothing to commit. The gate's `held()` calls it a nested repository and finds nothing. Git and the gate agree, and nothing leaks.
- An untracked one: git warns and lists nothing, and the gate lists nothing.
- A copy with no `.git`: `os.walk` lists it under dirs, and the gate neither reads nor names it, as for a symbolic link to a directory (the gate's docstring).

**CLAUDE.md item 10, sentence by sentence.**
- True: "listed by its directory", "`os.scandir`'s entry calls it a junction", "`lstat` raises, so `lexists`, `islink` and `isjunction` find nothing", "`os.rmdir` cannot remove it until its target is made again", and "a junction whose target exists behaves as before".
- "Nothing can open it" is true for every Win32 open I tried, though not for the attribute and find calls.
- The last two sentences are true but incomplete (D3).

## Notes (below the bar)

1. **Width of item 10 (prose).**
   - Its heading, "This machine opens no dangling junction", drops the scope the entry keeps: "MEASURED in the sandbox's folders". I could measure only there.
   - "A restart did not change it" and "the machine's Defender platform (2026-10-21) and its drivers are older than the change" I did not check. They are BELIEVED.
   - The changed test's docstring says "since 2026-10-30". The evidence is only that the test passed on 2026-10-26 (BELIEVED, not checked) and failed on 2026-10-30, so the change came between.
2. **Test reach where the code is right.**
   - The new test holds only the half where a host sees the link. `lexists` is told True, so the gate reports `conf.md: unreadable: FileNotFoundError` (MEASURED by running its steps, `scripts\newtest_body.py`).
   - The half this machine shows, passed over plus the index version read, is held by no test. My harness measured it.
   - On a host that can make a real dangling link, as the old test did with `os.symlink` off Windows, no real link is exercised in this test any more.
   - The test is bound to the call `privacy.os.path.lexists`. A rewrite of `passed_over` to `os.lstat` would fail it.
   - Its last assertion has an `or` whose first branch (`summary.startswith("2 files")`) is dead here, as it was before P0.8.
3. **A figure that crossed into the documents.** The entry's "44 warnings" has no definition, and I could not reproduce it (D3).
4. **Not checked.**
   - The entry's other runs: `20261026-161022-21312-83503b0`, `20261030-200045-29506-83503b0+dirty`, `20261030-202241-992-57fec09` and `20261030-202810-2526-83503b0+dirty`. The P4, P2 and P1.2 figures are also unchecked.
   - The lead's `p4_dangling.py`, which needs P4's tree.
5. **The lead's probes (not in the tree).**
   - `junction_winapi.py` crashes at `FindClose` after printing its key lines (a ctypes argtypes bug).
   - `junction_probe.py` always ends with an uncaught `OSError` at `base.rmdir()`, leaving its junction.
6. **P0.7's entry** still says its notes "are P0.8's". The new entry moves them to P0.9. The earlier sentence is a stale record. docs/README.md's reviews line will want P0.8's directory once there is a report.
7. **A side effect of my runs.** The format stage of each of my three runner runs made live junctions in the shared sandbox TEMP (`qro-sbx\tmp`), which the launchers fix. Pytest's cleanup will strand them like the others. I cannot find their targets, and they are not mine alone, so I left them.

## What I did not do

- I did not check what the machine does outside `qro-sbx`. I could not write there.
- I did not test symbolic links (the host cannot make one), `NtCreateFile` directly, or a restart.
- I did not read the Defender or driver state, which needs elevation.
- I did not read SCRATCH\p08\ (the lead's notes and entry draft). I listed it once to find the brief.
- I listed `qro-sbx\` top level once, so I saw other agents' directory names. I did not read them, the worktrees, the ledger, or `qro-sbx\tmp`.
- I ran no tests that start bash at low integrity, by design. The runner ran through `sbx-mid.sh`.
- I ran no mutant of code that deletes. All mutants were of the gate and the checker's reading code.
- On the lead's note about a loose Stop-Process: I went through my commands and none ended abruptly. Every failure was explained (my `sed` and `grep -P` errors, the launcher path error under `MSYS_NO_PATHCONV`, the lead's probe tracebacks). Afterwards I re-ran the three scripts behind D1 to D3 (`cli_streams.py`, `walk_states.py`, `rename_cleanup.py`) with the same results. A final scan (`scripts\scan_junctions.py`) found no junction, live or dangling, below `p08-r1\`.
