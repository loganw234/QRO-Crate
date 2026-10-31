# P0.8, round 2: the verifier's report

**Verdict: NOT READY.** There is one defect, and it is prose. FORMAT.md item 12 says the checker refuses `file-link` "any entry its directory lists that the host cannot open", which is wider than what the code does. The checker, the gates, the tests and every other restated sentence held. In every state I built there was no wrong acceptance, no wrong refusal name, no crash and no wrong exit code. P0.8 does not touch the privacy gate, and it let nothing through in any state I built.

Labels: READ means I read it. MEASURED gives the script or command. BELIEVED means I did not check it. SB is `<home>AppData\LocalLow\qro-sbx\p08-r2`, and my scripts are in `SB\scripts\`. The same report is saved in `<scratch>\verifier-P08-r2\check\notes-p08-r2.md`. I read, printed and wrote no IBM job id, key or CRN.

## Defect

### D1. Prose (the code is right): the new refusal is described wider than the code asks

**The sentences.**
- READ, docs/FORMAT.md item 12, lines 112 to 114: "So is any entry that is neither a regular file nor a directory, ..., and any entry its directory lists that the host cannot open." "So is" means refused `file-link`.
- READ, qro/checker.py: the `_unopenable` docstring ("Whether p's directory lists it and the host cannot open it") and the `UNOPENABLE` detail text use the same width.

**What the code asks.** READ, checker.py lines 169 to 182: does `os.lstat(p)` raise, and does the parent's listing name `p`. The ledger entry says so ("os.lstat raising"). FORMAT.md does not.

**The fault that shows it.** MEASURED, `bash sbx.sh python -I scripts/lock_probe.py tree lock1`. A listed file that another handle holds with no sharing is an entry the host lists and cannot open. `os.lstat` works on it, and the checker does not refuse it `file-link`:

```
lstat works on it: True
== a listed file held with no sharing
   in process : RAISED PermissionError: [Errno 13] Permission denied
   as process : exit 2: &lt;c&gt;\data\notes.txt: cannot be read here, Permission denied; usage: ...
== the metadata file held with no sharing   -&gt; exit 2, the same
== control: nothing held                    -&gt; ACCEPTED
```

Exit 2 is right. READ, FORMAT.md item 16: a path the user may not read, the crate's own files among them, is misuse, exit 2. So item 12 now contradicts item 16 for this class. A second checker written from item 12 would refuse such a crate `file-link`, where this one answers exit 2.

**What closes it.** One clause. Item 12 should say "any entry its directory lists that `os.lstat` raises on", and that an entry the host can stat and cannot read is item 16's misuse. The docstring and the `UNOPENABLE` text should say "cannot stat" the same way. I found no other blocking item.

## What held

**The freeze.**
- MEASURED, `sha256sum` of SHA256SUMS.txt begins `bba2afb33ae155a9`. `sha256sum -c` over frozen\tree gave 301 of 301 OK with no extra file. `SB\tree` is byte-equal. The seven changed files are byte-equal to the lead's sandbox copy (hashes compared, read only).
- MEASURED, `diff -rq` against `SB\base`, a `git clone --no-hardlinks` of the real repository at 83503b0 with its remote removed (every object has link count 1), shows exactly seven files. They are CLAUDE.md, docs/FORMAT.md, docs/VALIDATION.md, qro/checker.py, tests/format/test_hostile.py, tests/format/test_refusals.py and tests/tools/test_tools.py.
- MEASURED, `scripts/added_text.py`: the added text is ASCII and LF, with no trailing white space and no line over 120 characters.

**The runner, in two copies.** MEASURED, through sbx-mid.sh with `QRO_MOTH_ROOT=<repos>/moth-quantum`.
- A `git init` copy (commit 4ebfc51), run 20261030-220629-18497-4ebfc51, and a copy of the real history with tree laid over it and committed (commit 1bb89b9), run 20261030-220631-18538-1bb89b9. Each gave 18 passed, 0 failed, and 6 skipped by name: p2, p4, p1-crates, p2-crates, profile, p4-shacl. Instruments ran and passed.
- In the history copy the privacy gate read 301 files, 10 commit messages and 147 earlier versions, and listed its three known findings. Privacy-controls caught 40 of 40.
- Each run passed 2,957 tests: format 1,327, p1 1,169, tool-tests 204, docs 190, control-tests 32, custody 23, vocab-tests 12. `pytest --collect-only` on the base clone gives 2,948 (format 1,318), so nine are new, as the entry says.
- Each pytest stage printed 196 warnings, and one format stage 88. The lead had 160. The count depends on the launchers' shared TEMP at the time.

**Round 1's fix, at every position, on this machine.** MEASURED, `scripts/checker_scenarios.py tree low-a` (sbx.sh) and `mid-a` (sbx-mid.sh), with identical rows.
- A dangling junction at `data/jct`, at the crate root, two levels down, in place of a listed file, below which a listed file is named, and with its target now a file: each is `REFUSED file-link` at its own place, in process and as a process (exit 1, one line).
- The metadata file replaced by a dangling junction is `file-link`; before it was `file-missing`.
- A live junction is unchanged. The fixture crate is accepted, exit 0.
- The crate directory itself as a dangling junction is exit 2 "no such crate directory", unchanged and right (item 16: a link to a crate is followed).
- MEASURED, `scripts/cli_args.py` and `cli_args2.py`: a dangling junction as a custody log, a record or a crate is exit 2 in base and in tree, never exit 3.

**Every other entry the walk meets.** MEASURED, `scripts/diffrun.py base dbase` and `tree dtree` over 23 crate shapes, in process and as a process, then `diff`. Seven rows changed. After the fix each is `file-link`. In base each crashed, named another place, gave another name, or gave another detail.
1. A dangling junction in the walk: exit 3 became `file-link`. This is the fix.
2. A dangling junction beside a live one that stands deeper, or earlier at one level: base named the live one, tree names the dangling one. READ: a host that opens dangling links names the same place, because both questions sit in one iteration of one loop. So "a refusal names the same place on every host" holds.
3. The metadata file replaced by a dangling junction: `file-missing` became `file-link`.
4. Files named `x.` and `y ` (trailing dot or space, made through the extended-length prefix): same name, new detail text.
5. A directory named `dd.` holding a file: exit 3 became `file-link`.

The other 16 rows are unchanged. They include the plain crate, an unlisted file, a missing listed file, an empty directory, no metadata file, wrong-case names, live junctions, a file named `aux`, a path over 260 characters, and an NTFS stream.

**D3: P0's tests leave no junction behind, passing or failing.**
- READ, `_pytest/pathlib.py` `maybe_delete_a_numbered_dir` renames the old folder to `garbage-&lt;uuid&gt;` and then removes it. MEASURED, `scripts/rename_cleanup.py` shows a live junction stranded that way.
- MEASURED, `tests/format/test_hostile.py` and `test_refusals.py`, five sessions in a row with `PYTEST_DEBUG_TEMPROOT` inside SB so that numbered cleanup runs: 5 x 414 passed, no warning, no `garbage-*`, and `scripts/scan_junctions.py` found 0 junctions in 2,216 directories.
- MEASURED, the whole of `tests/format` with its bash tests, through sbx-mid.sh, five sessions in a row (`scripts/five_format.sh`): 5 x 1,327 passed, no warning, no `garbage-*`, 0 junctions in 3,581 directories.
- MEASURED, with the checker's new question made always false (mutant MZ), the nine new tests fail and 0 junctions are left.
- MEASURED, control: the base tree's old link test over five sessions strands 2 dangling junctions in `garbage-*` and leaves 3 live ones in the kept folders. Sessions 4 and 5 print 8 and 12 warnings. So the method can see the fault. I cleared them by making their derived targets again.
- READ: the only junction-making tests are in test_hostile.py (through `links`) and test_refusals.py (through `link`), and nothing imports their helpers.

**The changed tests/tools test.** MEASURED, `scripts/runmut.sh PA|PB|PC|PD|PE tests/tools/test_tools.py -k "dangling or sparse or skip_worktree or passed_over or gitlink"`.
- `passed_over` with `exists` for `lexists` (PA), `return rel in gone` (PB) and `Path.exists` (PC) are each killed.
- PD, which adds `isjunction`, survives and is equivalent, on this machine and on an opening host.
- PE, `passed_over` always False, is killed by `test_a_sparse_checkout_passes_and_what_it_leaves_out_is_read` alone. So the docstring's claim that the other half is held there is true.
- The base tree's old test fails here at its own control, which is the entry's premise.

**The gate half of the first entry.** MEASURED, `scripts/gate_scenarios.py tree` under both launchers, with 64 identical lines.
- A tracked file (skip-worktree, or deleted) with a dangling junction at its path is passed over, and its index version is read. A keyed index version is found, exit 1, and after the commit the history blob is found.
- At a gitlink's path git adds and commits nothing and the gate reads nothing. An untracked junction is listed by neither. Nothing leaked.
- tools/check_privacy.py is not in the diff.

**The machine, re-measured.**
- The lead's probes reproduce item 10's facts and leave nothing behind.
- MEASURED, `scripts/nt_open.py`: the native `NtOpenFile`, with the narrowest access and four option sets, fails on a dangling junction with `STATUS_OBJECT_NAME_NOT_FOUND` (0xc0000034) each time, while the control directory opens. So "nothing can open it" holds below Win32 as well.
- MEASURED, "a restart did not change it": the last boot was 2026-10-30 20:15:07. The lead's failing run `20261030-200045` is before it (READ in the entry), and I measure the same behaviour two hours after it.
- MEASURED, the Defender platform folder 4.18.26100.4-0 is dated 2026-10-21, as the entry says.

**The walk's cost.** MEASURED, `scripts/timewalk.py`, `checker.walk` on 5,000 files, best of 5, alternating, machine quiet: base 3.72 to 4.04 s, tree 4.67 to 5.16 s. That is about +25%, from one more `lstat` per entry, on a machine where each stat costs about 0.2 ms. It is linear, as before. Not a defect.

## Notes (below the bar)

**1. Test reach where the code is right.** MEASURED, `scripts/runmut.sh ID &lt;four format test files&gt;`, 491 tests, all through sbx.sh.
- **Killed:** MJ (the metadata refusal given another name), ME (files only), MK (`_is_link` also asks the new question), MZ, and the lead's U1, U2, U4 and U5, which reproduce.
- **MB survives:** letting the `os.listdir` failure in `_unopenable` propagate. It shows only as `checker.check(&lt;missing directory&gt;)` raising in process instead of `file-missing`. No test checks that in process.
- **MC, MD and MH survive:** a case-folded name match; asking after `is_file`, which changes only the detail text for some entries; and any replacement of the detail text.
- **MA (narrowing `except OSError` to `FileNotFoundError`)** is killed only by the "target became a file" test, which needs this machine's `NotADirectoryError`. The planted tests raise only `FileNotFoundError`, so off this machine nothing pins "any" `OSError`. FORMAT.md's "any" rests on that.
- **The planted metadata case is answered by two questions,** `check()`'s and the walk's. It passes with either removed (U1 or U2), so `check()`'s own question is held only by the real-junction test, on this machine. The ledger's "held on every host, at ... the metadata file" is true of the refusal and not of each question. On an opening host `check()`'s question is dead code, since `_is_link` answers first.
- **TA (the `links` fixture removes nothing) and TB (`unlink_made` removes nothing) pass all 491 tests.** They leave 4 live and 6 dangling junctions (TA) and 1 live (TB). Nothing in the suite or the gates holds "a P0 test leaves no junction behind"; CLAUDE.md item 10 holds it by text. TC (the target not made again) is caught only because this machine cannot remove a dangling junction.

**2. A corner of the metadata position.** A crate with no metadata file, whose entry at that name is a dangling junction in another case (`Ro-Crate-Metadata.json`), is `file-missing` here and in base. A live one in that case is `file-link`. READ: on an opening host the dangling one would be `file-link`. The crate is refused either way and never accepted, but "the same name on every host" is not literally true for it. MEASURED, `diffrun.py` rows `dangling-wrongcase-meta` and `live-wrongcase-meta`.

**3. The first entry's false sentences stay in the ledger.** "P0.8: this machine's dangling junctions" still says os.walk lists the junction as a file and that the walk refuses it. The second entry says "This entry corrects them", and there is precedent (VALIDATION.md line 3686). The first entry also still says item 10 forbids a test ever making a dangling junction. Item 10 now allows it with the target made again.

**4. "Left as it is".** "Their junctions' targets cannot be read, so they cannot be made again" does not follow. A stranded junction's target is its folder's old numbered path, which `scripts/fix_stranded.py` derived and cleared in my control. "Harmless" holds in measurement: 50 simulated stranded folders in a temp root of my own (`scripts/strand_sim.py`, 200 warnings) cost a 12-test session 1.4 s against 0.27 s clean. A 12-test session on the shared TEMP took 19.6 to 25 s, so the stranded folders are not what makes it slow. I did not find the cause (BELIEVED: cleaning large old numbered folders; one cost 3.3 s in my root).

**5. Defender.** MEASURED, `Get-MpComputerStatus`: Defender's signatures were updated at 2026-10-30 11:11, inside the window in which the machine changed. The entry's "The cause is not known" is right. Its list of what is older than the change does not exclude Defender's definitions.

**6. P4's tool.** "`_is_link` is unchanged, and so is P4's tool, which asks it": `_is_link` is textually unchanged (READ, diff). That P4's tool asks it, and the P4, P2 and P1.2 figures in the first entry, I could not check, since their trees are off limits (BELIEVED).

**7. My runs** wrote 14 pytest sessions into the launchers' shared TEMP, as any run does. P0's tests leave nothing there, by the five-session measurements above. I did not read that folder.

## What I did not do

- I ran nothing on a host that opens dangling links, nor on Linux or macOS. The host cannot make a symbolic link (WinError 1314), and WSL's Python is 3.10, below the floor, and outside the sandbox. Every "on a host that opens it" statement is READ.
- I did not read or run P4's, P2's or P1.2's trees, so their figures and `p4_dangling.py` are unchecked. I did not re-measure the lead's earlier runs (`20261026-161022-21312`, `20261030-200045-29506`, `20261030-202241-992`, `20261030-202810-2526`, `20261030-214813-15810`).
- I did not read the launchers' shared TEMP, SCRATCH\p08 beyond the brief and `r2fix\`, other agents' directories, the worktrees or the ledger.
- I did not change an ACL; the unreadable-entry fault uses a held handle. I did not look for the machine's cause (a file system filter needs an elevated prompt), and I did not test what the machine does outside the sandbox's folders.
- I ran no mutant under sbx-mid.sh. Every mutant, including those of the fixtures' cleanup code, ran through sbx.sh.
- Every junction I made was removed with its target made again. A last scan of SB (23,193 directories) found 0 live and 0 dangling junctions.
