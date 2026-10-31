**Verdict: NOT READY.** The one blocker is in a rewritten test, not in the tool. The tool's code is right.

I judged the packet as frozen (SHA256SUMS `8e6f1894d8183538`, 350 of 350 files OK). I re-checked it at the end and the real repository was untouched. Labels are MEASURED (run through `sbx.sh`, or `sbx-mid.sh` for the runner), READ and BELIEVED. My work is in `<home>AppData\LocalLow\qro-sbx\p4-r6\`, and my notes are in `SCRATCH\verifier-P4-r6\check\notes.md`.

## Defects

**D1. The rewritten test of "a link below `profile/` that leads nowhere" passes nine faults that the old test caught. It holds the tool's code, so this is the brief's blocking class: a rewritten test that a mutant of its code now survives.**

- **The cause (READ).** The stand-in is a real, existing empty directory. `leads_nowhere` patches only `os.scandir` and `Path.stat` for that one path.
- **The nine mutants (MEASURED).** I wrote mutants that decide "this link leads nowhere, so it is no link, or is not removed" with other APIs:
  - A03: the walk prunes a link only if `os.path.exists`.
  - A04: the same with `os.path.isdir`.
  - A05: `remove_link` returns early if `not os.path.exists`.
  - A06: the removal loop skips an entry `os.path.exists` denies.
  - A07: `drift` calls it a stray only if `os.path.exists`.
  - A09: `remove_link` raises FileNotFoundError if `not os.path.exists`.
  - A10: `remove_link` returns if `os.stat` fails.
  - A11: `remove_link` returns if `resolve(strict=True)` fails.
  - A12: the walk skips an entry `os.stat` cannot read.
- **They survive the new suite (MEASURED).**
  - All nine survive the told and limit tests.
  - All nine survive `test_p4_tree.py`, `test_p4_tool.py` and `test_p4_crash.py`.
  - A03, A05 and A09 survive all 925 tests of `tests/p4`.
- **The old test caught them (MEASURED).** `scripts\oldhost_emul.py` runs the old test's three steps in process on a real dangling junction. It tells the tool that the old host's two properties hold (the junction is recognised as a link, and it can be removed).
  - The unmutated tool passes the three steps (the control).
  - Each of the nine fails them. A03 and A04 exit 3 where 1 is held. A05, A06, A10 and A11 leave the link, and the second `--check` exits 1. A09 exits 3 on `--write`. A07 uses the stray's words. A12 reports no link.
  - That the old host recognised and removed such a junction is READ from the fifth verifier's run, where p4 passed 920.
- **The builder's own versions were killed only by spelling.** H2-08 to H2-11 use `Path.exists()`, which the `Path.stat` patch reaches. `os.path.exists` and the others are not reached.
- **A fix is validated (MEASURED, in my copy only).** In `tree-fix\tests\p4\test_p4_tree.py` I extended `leads_nowhere` to patch `os.stat`, `os.path.exists`, `os.path.isdir`, `os.path.isfile` and `os.path.realpath(strict=True)` for that path, about 15 lines. A03 to A07 and A09 to A12 are then killed, and the file still passes 52. A cheaper alternative is to make a real dangling symlink on POSIX, where it can be removed, and tell the tool only on Windows.
- **What is not part of D1.** A01 and A02 (the `profile/` itself first act) are killed by the new test. A08 (a link at a rendered path) is code the old test never reached.

I found no defect in what the tool does, in the evaluator, the engine stage, the shapes or the examples.

## What held (MEASURED unless marked)

- **Scope 3, what changed.**
  - Exactly four files differ from the fifth packet: `docs/P4.md`, `tests/p4/p4_helpers.py`, `tests/p4/test_p4_tree.py` and `tools/gen_profile.py`. `profile/`, `verify/`, `qro/` and every other test are byte-identical. The builder's line and byte counts are exact.
  - `gen_profile.py` is the same program once the module docstring is dropped (the only docstring that differs).
  - `tests/p4` collects 920 then 925: the five new items only, none removed or renamed.
- **Runner.** `20261030-215624-16986-17f3cd4`: 21 passed, 0 failed, 3 skipped by name (p2, p1-crates, p2-crates), exit 0. p4 925, p4-shacl 236, p1 1,169, format 958, docs 164 and tool-tests 129 equal the builder's numbers. Separately, p4-shacl passes 236 at low integrity.
- **Scope 2, the stated limit is true.** I made real dangling junctions in my own directory.
  - `os.lstat` and `os.stat` raise FileNotFoundError, and `checker._is_link` says False. The parent still lists the junction. `os.rmdir`, `unlink`, `rmtree`, `cmd rmdir` and `os.rename` all fail until the target is made again.
  - The tool was run as processes in 13 states, `--check`, `--write`, `--check`, with whole-directory snapshots: `profile/` itself, below it at two depths, at a rendered file, a rendered directory, `context.jsonld`, a `.tmp` name, a case variant, two at once, with drift and strays beside, a sibling outside `profile/`, a junction whose target became a file, and a chain. Nothing changed in any of them.
  - Results: `profile/` itself and `context.jsonld` exit 1, "is missing". Every other dangling state exits 3 "Unlistable". The sibling outside `profile/` exits 0.
  - An audit hook over ten of those states shows no event outside `profile/`, none below a link, and no write or removal.
- **Scope 1, the fifth-round and builder mutants.**
  - Of the fifth round's 37 link, walk, removal and listing mutants, 22 are killed by the told and limit tests alone. The other 15 are killed by the real-junction files. None survives.
  - The builder's H-group of 46 is killed 46 of 46 with my harness, so none of those survives either.
- **Scope 1, the rest.**
  - Each told answer is exact path equality, with controls for two other paths, and the controls show the patch took.
  - The three rewritten tests, and the five new ones (two limit tests in two modes each, plus the pin test), make no junction and would pass on a host that opens dangling junctions (READ).
  - A bounded Python 3.13.5 probe suggests `Path.exists()` still goes through `Path.stat` there.
- **Scope 4, junctions left behind.**
  - Passing runs leave none. All of `tests/p4` passed with a basetemp of my own, and a scan found no junction, live or dangling. The families' staging probe made one live junction and left none.
  - A failing run leaves live junctions. With `-x` off, mutant L01 failed 12 tests and left 10 junctions, G01 failed 24 and left 23, and G02 failed 10 and left 6. Two of 15 single-failure runs left one. None was dangling.

## Notes (not blocking)

1. **Failing runs strand junctions.** The real-junction tests remove their link as the last statement, not in a `finally` or a fixture. The mechanism that then strands a link is the lead's P0.8 D3 and the builder's note. I did not reproduce it in the shared temp folder. It is a candidate for P4.2.
2. **The limit tests hold the tool, not the host.**
   - They pass on any host. Nothing in the suite would notice if this host opened dangling junctions again, and the page and docstring would then be wrong.
   - The first limit test is satisfied by any empty root.
   - The gates-table row "a link like any other, where the host opens it" is held only by the told tests, so D1 applies to it.
3. **The limit's prose has two holes.** "With one below `profile/`, both fail, exit 3" is false for a dangling junction at `context.jsonld`, which exits 1 "is missing". The Links paragraph's "refused by a sentence that says which it is" is also untrue there on this host. A junction whose target became a file gives NotADirectoryError, and the limit names only FileNotFoundError.
4. **"This machine" is ambiguous in a published page and docstring.** "Nothing removes the junction" is measured for seven routes and BELIEVED for the rest, such as PowerShell.
5. **The pin test reads `gen.__doc__`.** It would error under `-OO`, which the stage does not use.
6. **The runner's own pytest warnings** (`rm_rf` errors on `garbage-*` folders in the shared temp) are the stranded folders of earlier runs, not mine.

## What I did not do

- I made no real dangling junction in any test. There was no host that opens one, no POSIX host, no symlink (WinError 1314), no real unlistable directory, and no Python other than 3.12.15 apart from the 3.13.5 probe.
- I did not run the quick budget separately; the full run covers its stages. I did not re-run the builder's 53 extra mutants, the engine mutants (T, N, Z), the stream mutants (G14 to G16) or the text mutants (O).
- I did not look inside the runner's default pytest basetemp, because the shared temp holds other agents' folders. All my scans used basetemps of my own.
- I used `scripts\hm6.py`, my variant of `hm_t.py`: same sandbox refusal, baseline first, a basetemp per run, and a sweep of live junctions only. I did not use `hm_t.py` itself.
- I touched nothing in `frozen\`, the real repository, the worktrees, the ledger, P4's scratch, the earlier verifiers' directories, the launchers or the engine environment.
- **Slips (mine):**
  - Four bare `python`/`python3` calls in my own shell, outside the launcher. Two were no-ops, and two only read my own logs or piped text. No project code ran and nothing was written.
  - One `sed -i` on my own harness.
  - One read-only `py -0p`.
  - One run of the owner's Python 3.13 through `sbx.sh` for a read-only probe.
  - No IBM job id was printed or written. No key, token or CRN was read.
- My 45 junctions were all restored and removed. The final scan found none under `p4-r6\`.

**Files (all under `<home>AppData\LocalLow\qro-sbx\p4-r6\`):**
- `scripts\defs_r6a.py`: the nine mutants plus A01, A02 and A08.
- `scripts\oldhost_emul.py`: the old-test emulation.
- `scripts\hm6.py`: the harness.
- `scripts\measure_host.py`, `scripts\measure_tool.py`, `scripts\audit_tool.py`: the host, tool and audit measurements.
- `logs\mutA.jsonl`, `logs\mutATT.jsonl`, `logs\mutAALL.jsonl`, `logs\mutAfix.jsonl`: the results.
- `tree-fix\tests\p4\test_p4_tree.py`: the validated widening.
