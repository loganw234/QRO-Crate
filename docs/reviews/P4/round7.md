**Verdict: READY**, on the relaxed bar (CLAUDE.md item 6: only a defect in what the code does blocks).

I found no defect in what the tool, the evaluator, the engine stage, the shapes or the examples do. I found no test that passes a fault by any call the ruling names, or by any natural way of asking. One test gap of the sixth verifier's kind is still open, at calls that are not questions (`os.utime`) and at two spellings of a path. I count it a note and say why in note 1, so the lead can rule otherwise.

Labels are MEASURED (a command run through `sbx.sh`, or `sbx-mid.sh` for the runner), READ and BELIEVED. My work is in `<home>AppData\LocalLow\qro-sbx\p4-r7\` (scripts\, logs\). My notes are in `<scratch>\verifier-P4-r7\check\notes.md`. The Write tool refused a `report.md` there, so this message is the report.

## 1. The freeze, and what changed (MEASURED)

- **Freeze.** `SHA256SUMS.txt` begins `ff5006d40f9b43e7`, and every packet file's hash is as the brief names it. `sha256sum -c` over `frozen\tree` gives 350 of 350 OK, with no extra file and no symlink. I re-checked at the end and it is unchanged. My copies `tree\` and `src\` are also 350 of 350 OK.
- **Diff against the sixth packet.** `diff -rq` shows exactly six files differ:
  - `docs/P4.md`
  - `tests/p4/p4_helpers.py`
  - `tests/p4/test_p4_files.py`
  - `tests/p4/test_p4_tool.py`
  - `tests/p4/test_p4_tree.py`
  - `tools/gen_profile.py`

  `profile/`, `qro/`, `verify/` and every other test are byte-identical. The builder's line and byte counts are exact.
- **The tool is the same program.** Its AST with every docstring dropped equals the sixth packet's (`scripts\ast_cmp7.py`). Only the module docstring differs, 6,056 to 6,268 characters.
- **Test count.** `tests/p4` collects 925, then 933. The unlistable limit test's two ids became four, because it now runs over both errors. Eight items were added: the guard, the teardown test, and the context test four times.
- **Runner.** `bash verify/run.sh` through `sbx-mid.sh` on my copy (`git init`, commit `bb8e432`, with `QRO_MOTH_ROOT` and `QRO_SHACL_PYTHON` set). Run `20261030-233618-986-bb8e432` gave 21 passed, 0 failed, 3 skipped by name (p2, p1-crates, p2-crates), exit 0.

  | Stage | Passed |
  |---|---|
  | p4 | 933 (89 s) |
  | p4-shacl | 236 (159 s) |
  | p1 | 1,169 |
  | format | 958 |
  | docs | 164 |
  | tool-tests | 129 |

  These equal the builder's numbers, and the `profile` stage passed. The 268 warnings in the runner's p4 log are all `rm_rf` errors on `garbage-*` folders in the shared temp, from older runs and not P4's. My own-basetemp run of all of `tests/p4` has none.

## 2. Defects in what the code does

None.

- **The host's facts.** I made real junctions in my directory and restored each one (`scripts\measure7.py host`).
  - For a junction whose target is gone, `os.lstat` and `os.stat` raise FileNotFoundError.
  - `lexists`, `exists`, `isdir`, `islink`, `isjunction`, `Path.is_junction` and `checker._is_link` all say False, while the parent's `scandir` entry still says junction.
  - `scandir` and `listdir` of it raise FileNotFoundError.
  - Every removal route fails while the target is gone: `os.rmdir`, `os.unlink`, `Path.unlink`, `Path.rmdir`, `shutil.rmtree`, `os.rename` and `cmd /c rmdir`.
  - With the target made a file, `lstat`, `stat`, `scandir`, `listdir`, `rmdir`, `unlink`, `rmtree` and `rename` raise NotADirectoryError.

  So the stated limit is true of this host.
- **The tool as a process in 15 real states** (`measure7.py tool`). I took a whole-root snapshot before and after each of `--check`, `--write` and `--check`. Nothing changed in any state, in any run.
  - The states were:
    - `profile/` itself
    - below it at two depths
    - at a rendered file
    - at a rendered directory
    - at `context.jsonld`
    - at a `.tmp` name
    - two at once
    - with drift and strays beside
    - a sibling outside `profile/`
    - a chain
    - the target made a file, at four places
  - `profile/` itself and `context.jsonld` (target gone): exit 1, "is missing".
  - Every other place below `profile/`: exit 3, `Unlistable`, naming FileNotFoundError, or NotADirectoryError where the target became a file.
  - The sibling outside `profile/`: exit 0.
  - One exception to the prose is note 5.
- **A fault I looked for and did not find** (`scripts\chain7.py`). `--write` takes its list of entries once and asks `is_link` per entry as it removes. If one link led to another, removing the first would leave the second dangling mid-run. But a junction made to a junction stores the final target, with `_winapi.CreateJunction` and with `mklink /J` alike. `--write` exits 0 in all four chain states, and no victim file changed.
- I ran no audit hook this round. The code is the program the sixth verifier audited with one.

## 3. Tests that pass a fault they claim to catch

None by the ruling's list. Every mutant ran through `sbx.sh` after a baseline, with my harness `scripts\hm7.py`. It is the sixth verifier's `hm6.py` with its refusal moved to my directory, and it counts any live junction a run leaves. All baselines passed and every worker was pristine afterwards. I audited all 448 kills: each names a failing test, and none is a stopped process.

- **The sixth verifier's twelve (D1).**
  - A01, A02, A03 to A07 and A09 to A12 are killed by the two told tests alone, and again on the two real-junction files whole.
  - A08 survives both, and survives all 925 tests of the other `tests/p4` modules, as the brief expects.
  - The old test, run on a real dangling junction with the old host's two properties told (`scripts\oldhost7.py`), passes the unmutated tool and kills A03, but passes A08. So A08 is not a regression.
- **My own mutants of the same kind** (`defs_r7a.py`). I wrote the decision "this link leads nowhere, so it is no link or is not removed" with 21 different calls at 7 sites: the walk, `remove_link`'s guard, its early return, the removal loop, the removal dispatch, `drift`'s stray branch, and the first act.
  - The calls were `exists`, `isdir`, `isfile`, `lexists`, `os.access`, `Path.exists`, `is_dir`, `is_file`, `os.walk`, `os.stat`, `os.lstat`, `os.listdir`, `os.scandir`, `Path.resolve(strict=True)`, `realpath(strict=True)`, `iterdir`, `Path.stat`, `getsize`, `samefile`, `open` and `os.utime`.
  - **20 of the 21 are killed at all 7 sites.** Only `os.utime` survives, at the six sites where something stands (note 1).
- **The builder's groups, re-run by me** (`defs_r7b.py`). H1 to H5 and the teardown's HT are 72 mutants, all killed but H5-10, which removes the explicit `Path.stat` patch. H5-10 is equivalent on 3.12 (READ: `Path.stat` is `os.stat(self, ...)` there). Each telling's control shows it took: removing any one patch in `leads_nowhere`, telling every path, telling by name, or giving the wrong error is killed by the told test's controls.
- **The fifth round's mutants against the new tests** (`defs_r7c.py`). All 83 tool mutants whose killers are the two changed files are killed (L, G, R, W, C, D, U, X10, X11, P, E, O05). None survives.
- **The new round's own targets** (`defs_r7d.py`). Killed: the walk's `onerror` passing over NotADirectoryError or FileNotFoundError, two mutants of the context read's error classes, and a third test module that calls `link_dir(` with no fixture. Two survive and are equivalent in practice: `remove_link` treating FileNotFoundError or NotADirectoryError from the unlink as "done", which is a robustness change.
- **Does the widened telling hide a fault behind a told answer? I found none.**
  - Where the stand-in answers differently from a real junction on the old host, the difference only makes a mutant die earlier. This holds for `lexists` and `lstat` (told "gone" where the old host said "there"), for `os.access`, and for `isjunction`.
  - The one direction that lets a mutant live is a call the stand-in answers as "there" (note 1).

## 4. Junctions left behind (scopes 2 and 6)

- **Passing runs.**
  - All of `tests/p4` with a basetemp of my own: 933 passed in 104 s. A scan of that basetemp finds 1,100 folders, 1,844 files and 0 links.
  - The two junction modules in reverse order (114 ids) passed with 0 links.
  - My whole directory at the end has 79,029 folders, 124,229 files and 0 links, live or dangling.
- **Failing runs.** I ran the fifth round's 39 link, walk, removal and listing mutants on the two junction files with every failing test running (`defs_r7b.py`, group B7).
  - Up to 24 tests fail in one run, and **no run left a junction.**
  - Mutants L01, G01 and G02 failed 12, 24 and 10 tests and left 10, 23 and 6 junctions in the sixth packet.
  - The only runs that left links are the four mutants of the teardown helper itself (15 links in all), where the broken helper cannot clean up either.
- **The families' staged crates** (`scripts\staged_probe7.py`). `Workspace.staged` with `link_at` leaves no junction on a normal exit or a failing one. READ: this holds because `shutil.rmtree` lists `crate` before `outside`, and that order is what keeps it so.
- **The guard.** It catches a module that loses its fixture, a fixture that is not autouse, and a third module that calls `link_dir(`. It reads that one text only (note 3).

## 5. Notes (none blocks; none is about what the code does)

**Test gaps**

1. **Calls and spellings the stand-in does not tell.** This is the one place a mutant of the sixth verifier's kind survives, so the lead may want to weigh it.
   - `os.utime` survives at the walk, `remove_link`'s guard and early return, the removal loop and dispatch, and `drift`'s stray branch (MEASURED, 6 of 147). Three of those survive all 925 other tests too.
   - A path spelled with a trailing separator, or with a "." component, is a different string to the stand-in, which tells by exact equality after `normcase`. These survive at the walk and at `remove_link` (6 of 16 spelled mutants). Forward slashes, upper case, `abspath`, non-strict `realpath` and `normpath` are killed.
   - The old test, on a real dangling junction, would kill all of these (`oldhost7.py`).
   - Why I count it a note: all 20 natural probes are killed everywhere, and the ruling's list is met in full, with `listdir` and `access` besides. The survivors need a call that follows a link without asking anything, or an odd spelling.
   - **A closure, validated in my copy only.** A stand-in that does not exist, shown only in its parent's listing by a patched `os.scandir`, with `os.unlink` raising PermissionError and `os.rmdir` dropping the entry, needs no call told. It kills 57 of 58 (the twelve but A08, and 8 calls at 6 sites, `utime` among them) and 16 of 16 spellings. See the last two tests of `poc-src\tests\p4\test_p4_tree.py`.
2. **A08** (a dangling link at a rendered path) is reached by no test of P4's. A told test of the same shape at `EXAMPLES.md` kills it, and A03, A05 and A06 too (MEASURED in the copy).
3. **The teardown guard reads `link_dir(` only.** A third module that makes a junction with `_winapi.CreateJunction(`, `link_at(` or `os.symlink(` and has no fixture passes it (MEASURED, 3 of 3). No such module exists today.
4. **The five limit tests, and the told tests, hold the tool and not the host.** None makes a junction, so they pass on a host that opens dangling ones too. This is the sixth verifier's note 2, ruled for P4.2.

**Prose**

5. **A false sentence about `context.jsonld` whose target became a file.**
   - The page (Stated limits, and the gates row), the docstring and the new context test's docstring say the read fails with NotADirectoryError and the tree is refused as "context is missing".
   - MEASURED: `open()` of such a junction raises `OSError` (errno 22), and the tool answers exit 1 "profile/context.jsonld cannot be read (OSError)". The exit code and the refusal are as stated.
   - The builder measured the file-target state below `profile/` (NotADirectoryError, true) but not at `context.jsonld`. The `[NotADirectoryError]` variant of that test tells a read error the host does not give. The real state reaches the generic OSError branch, which the unreadable-context test holds.
6. **`os.access` is told "no", but a real dangling junction here says yes** (MEASURED: `os.access(F_OK)` is True). `leads_nowhere`'s docstring ("shows what an entry whose target is gone shows of itself") and the page ("every call that could ask") say more than the ten calls told.
7. **"This host" remains in three older sentences of the page**: the hard-link paragraph twice, and the symbolic-link privilege line. They are about the guard and WinError 1314, not about junctions, but they are as ambiguous in a published page as "this machine" was.

## 6. What I did not do

- I made no real dangling junction inside any test, and had no host that opens one. The old host is emulated (`oldhost7.py`) and READ from the sixth verifier. No POSIX host, no symbolic link (WinError 1314), and no Python but 3.12.15.
- I did not run the quick budget separately, since the full runner covers its stages. I did not re-run the engine, limit-text and stream mutants (T, N, Z, G15, G16, X01 to X09, X12, O01 to O04, O06 to O09), whose code and tests did not change.
- I did not read the shared pytest folder in the sandbox's temp, which holds other agents' sessions. All my basetemps are in my directory. P0's `format` stage, which the runner runs, makes junctions in that shared temp, as the builder's scan says.
- I did not use `SCRATCH\p02\hm_t.py` itself but `hm7.py`, for the baseline, the per-run basetemp and the sweep count.
- I edited nothing in `frozen\`, the real repository, the worktrees, the ledgers, P4's scratch, the earlier verifiers' directories, the launchers or the engine's environment. I pushed nothing and contacted no one.

**Slips (mine).**
- One bare `python -c "print(1)"` and one `python3 --version` in my own shell, outside the launcher. Nothing of the project ran and nothing was written.
- One `sed -i` on my own mutant file.
- Several small scripts, and two tests added in my copy, written with Bash heredocs instead of the Write tool. All are inside my directory, none has a backslash, and all ran only through `sbx.sh`.
- One `tasklist` listing of process names.
- No IBM job id was printed or written. No key, token or CRN was read.

**Files** (all under `<home>AppData\LocalLow\qro-sbx\p4-r7\`):
- `scripts\hm7.py` (harness)
- `scripts\defs_r7a.py` to `defs_r7j.py` (mutants)
- `scripts\measure7.py`, `chain7.py`, `oldhost7.py`, `staged_probe7.py`, `audit7.py`, `scan7.py`
- `logs\mutA.jsonl` to `mutJ.jsonl`, `runner-full.log`, `measure-host.out`, `measure-tool.out`, `chain7.out`
- `poc-src\tests\p4\test_p4_tree.py` (the two tests added in the copy)
