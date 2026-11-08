# P1.2 verifier, round 2: report

## Verdict: NOT READY

I found four defects: one in what the code does (an exit code) and three in the prose of docs/P1.md. Each has a fault that shows it. I found no gate defect.

I attacked the cleanup above all, and it held against every attack. It never removed or wrote anything the build had not made, and it never went through a link at a directory the build made. Round 1's D1, D2, D3 (in the cases it named), D4 and D6 hold fixed. D5's restated list is still incomplete (defect 3).

Labels: MEASURED means I ran it; the script is in `<home>AppData\LocalLow\qro-sbx\p12-r2\s\`, and I name it. READ means I read the file. BELIEVED means neither.

## Defects

### 1. Code (exit class): an `--out` the adapter cannot use gives exit 3, where the docs put it at exit 2

This is the same family as round 1's D3, third bullet, which the lead took.

- **Trailing space.** `--out "&lt;existing dir&gt;/crate "` (a last component that ends in a space; a name of spaces only does the same) exits 3.
  - The message is `FAILED: the adapter itself failed, FileNotFoundError: [WinError 3] ...; this is not a verdict`.
  - Windows makes the directory without the space, and the next level is then looked for with it.
  - The cleanup removed the one directory it had made, so nothing is left.
  - MEASURED, as a process and in process (`ci_outs.py`). Of 41 shapes printed (the script's last print failed), these are the only ones that exit 3. A space inside or before a name, a trailing dot, 255 characters, reserved names, odd punctuation and non-ASCII all give 0 or 2.
- **Unlistable directory.** `--out "C:\System Volume Information"` exists and cannot be listed. It exits 3 with `PermissionError: [WinError 5]`. The adapter only stats and lists it. MEASURED as a process.
- **Cause.** READ: `qro/p1_adapter.py:165-173`.
  - `check_out` calls `out.exists()`, `out.is_dir()` and `any(out.iterdir())` under no `try`.
  - `build` (`:190-196`) turns only the OSError of `made.directory(out)` into exit 2.
  - The next level is made inside `_Made.write` (`:250-253`), after that `try` has ended.
- **Claims it contradicts.** The module docstring (`:25-28`: exit 2 is "an `--out` the adapter will not use, among it an `--out` that cannot be made") and docs/P1.md:144-146 ("a name the host will not take").
- **Suggested fix.** Put `check_out`'s filesystem calls under the same OSError-to-AdapterError conversion. Treat a failure of the first level made under `--out` as a failure of the out itself.

### 2. Prose (false numbers): docs/P1.md says 79 planted faults and 22 for G11; the tests have 108 and 31

- READ: docs/P1.md:104 (`79 faults; G11 in test_p1_atlas_generate.py, 22`) and :311 (`its 79 planted faults`).
- MEASURED (`pytest --collect-only` through sbx.sh): `test_each_planted_fault_trips_its_guard_and_no_other_first` has 108 cases (G1 12, G2 15, G3 24, G4 2, G5 3, G6 6, G7 20, G8 11, G9 6, G10 3, G12 6). The Atlas G11 test has 31.
- The old figures plus round 1's additions (29 and 9) are the new ones, so they went stale when the fixes landed. The page says every claim "is held by a test or says it is not". This is the same family as round 1's D6.

### 3. Prose (a stated limit that is incomplete): limit 21's list of carried classes omits the largest Atlas class and the licence texts

READ: docs/P1.md:129-131 and 255-264. The page says limit 21 "names the classes the checker holds by their digests alone" and that "a test holds a sample of each class as accepted".

- **Atlas result files.** MEASURED (`sweep_run.py` and `classify.py`, 548 of 1,059 trials of the real Atlas crate, only the file's own digest re-sealed).
  - 433 trials were accepted. None crashed, and every step-9 refusal was a `GuardError`.
  - Of 213 accepted leaves in result files, 198 are in no class of the list: `response/result/observables/**` and `response/result/density_matrices/**` (17 entries each), and the 2026-09-26 envelope's `fetched_at`.
  - They are about 0.7% of a result's bytes, but they are a whole class.
- **Counts.** MEASURED (`cg_atlas_counts.py`): one shot moved between two outcomes of one setting of a law result (sum kept), with only the file's digest re-sealed, is accepted.
  - That holds in a non-Z setting (8 of the 9 settings, which nothing reads past their sum) and in the all-Z setting (limit 1).
  - The page never says the eight settings' counts are held by the sum alone.
- **Licence.** MEASURED (twin, 2,279 trials, only the digest re-sealed): 389 leaves are accepted, all in the list but one. A byte appended to `LICENSE-quantum-film` is accepted; the Atlas crate carries the same file.
- **Over-reach.** The page names the metrics wrappers' `job` and `metrics` whole. G6 holds `job_id`, `backend`, `job.created` and `metrics.timestamps.created` and `.running`, and `.finished` as an inequality (MEASURED, same sweep).
- **Test.** READ: P1.2's Atlas samples (`ATLAS_CARRIED`, tests/p1/test_p1_atlas_generate.py:405-415) have none of the omitted classes. So "a sample of each class" is true of the listed classes only.

### 4. Prose, with a vacuous guard: "a snapshot dropped from the crate cannot move a link verdict" (docs/P1.md:119, the G9 row)

- **Fault.** MEASURED (`cj_manifest.py`, on the twin, regenerated with `rebuild`, then checked by every step).
  - I removed the 12:21:18 snapshot together with `2026-10-14/ibm-refetch/MANIFEST.json`. Every step ACCEPTED it, and sheet-02's job moved from `history-in-gap` to `history-at-first-shot`.
  - With the snapshot alone removed, G9 raises, as the page says.
  - With both MANIFESTs removed and no snapshot dropped, the crate is also accepted.
- **Cause.** READ: `_reads` in `qro/p1_generate.py` has `if not held: continue`. G9 is skipped whenever a MANIFEST is absent, so its own rule ("every present file is listed") is not applied.
- **Why I count it.** A producer who also drops or edits the MANIFEST holds every byte (limit 1). But round 1 held statements of what step 9 refuses to that reading (D4). The sentence is true of an honest omission and false of this one.
- **Suggested fix.** Require the MANIFEST whenever its directory has files, or reword the parenthetical. The lead may rule it a note.

## What held

- **Freeze.** MEASURED: `sha256sum -c` over `frozen\tree` gave 366 of 366, and the sums file's own digest begins `f155469ad6e5a943`.
  - The ledger and brief digests match the brief.
  - The worktree's 366 files hash identically to the packet.
  - Against 37640f0 the packet adds P1.2's files and changes only `docs/README.md` (the one P1.md line) and `qro/register_p1.py`. Nothing is outside CLAUDE.md item 7's list.
  - The twin's 56 files (828,488 bytes) each equal `git show 3a73823:&lt;path&gt;`.
  - My scan of P1.2's files for home paths, addresses and key shapes found none.
- **Runner.** MEASURED: the full runner through sbx-mid.sh on a git copy (commit 8cf06f1), run `20261026-123842-52446-8cf06f1`.
  - 19 passed, 0 failed, 5 skipped by name (p2, p4, p2-crates, profile, p4-shacl).
  - p1: 1,696 passed (219 s). p1-crates: 39 (246 s). control-tests: 39. controls-run: 16 of 16 built controls as section 11 says.
  - The tree stayed clean, and moth-quantum's `.git/index` kept its time (2026-10-15 20:43:39) before the runner, after it and after my crate builds.
  - I did not run the quick budget alone; its stages are a subset of the full run.
- **The two changes the lead did not ask for.** I find nothing wrong with either beyond defect 1's family.
  - `GIT_OPTIONAL_LOCKS=0`: a mutant that sets it to 1 is killed, and the index time did not move.
  - A file put where the build writes gives exit 3, the file stays with its ancestors and everything else is removed (`cd_process.py` F5).
- **Real crates.** MEASURED, built by the adapter as a process through sbx.sh into my directory and checked by `python -m qro check`:
  - IBM: `BUILT ibm: 1073 files, 53269160 bytes`, identity `8ec4dc39df52c0dc...`, ACCEPTED.
  - Atlas: 31 files, 4,975,638 bytes, `f9c1a259786e3e9a...`, ACCEPTED.
  - The design's measurements, by the first verifier's code (read first; it imports no `qro`):
    - 68 of 68 commitments equal the claim, the line, the record and IBM's echo.
    - 12 values-digests in 6 classes (kingston 3, marrakesh 2, fez 1).
    - Links: 57 at-first-shot and 8 in-gap, with the 8 partners agreeing.
    - 31 of 31 known answers hold msb-first and 0 of 31 hold under the mirror.
    - The Atlas vector's worst |z| is 2.15, against 172.96 and 346.28.
  - Every other count in docs/P1.md that I checked is right: entities, files, bytes, descriptors, the 161 actions, the 77/76-character paths, limit 15's copy counts, and the MANIFESTs listing nothing the crate lacks.
  - Limit 4: each of Quantum-Film's five own snapshots, taken out of the real IBM crate, regenerates, is accepted and moves no link (`ck_limit4.py`).
- **Round 1's fixes.**
  - D1: nine variants of the Atlas commitment lines are each refused `metadata-generated` by `qro check`, with G11 raised.
    - The variants: an orphan line that recomputes and one that does not, one digit off, other decode, bad commit, other shots, a duplicate, other engine, no final line feed.
    - My own version-2 recomputation reproduces all six real lines. The control is accepted (`cf_fixes.py`).
  - D2: a vector whose job is a law job's id is refused (G11, "written twice") by `qro check`, `rebuild` and the adapter.
  - D3: a qiskit version or program name with a space, an empty program name, and an Atlas or unbuilt decode rule in an IBM manifest each give exit 1 as a process (`cf_d3d4.py`).
  - D4: a copied job, regenerated and checked by all nine steps, is ACCEPTED with five jobs, as limit 16 now says.
  - D6: 77 characters in ten files, 76 in eight; 259 − 77 − 1 = 181.
- **The cleanup, all through sbx.sh.**
  - A failed build at every write (1 to 73), mid-file, and at the out, plan, question files, generator and writer, into a fresh nested out, an existing empty one and one whose parents it made: the world comes back exactly and the error that comes out is the injected one (`ca_inject.py`, 80 of 80).
  - A foreign file, a directory with a file, a junction to a decoy, and a hard link to an outside file, each put before, during (after write 1, 2, 36, 71) and after the build's writes: it and every ancestor stay, nothing else (`cb_foreign.py`, 28 of 28).
  - A listed directory swapped for a junction to a decoy of the same names, a real directory of the same names, or a file; a listed file swapped for a junction, another file or a hard link; the pre-existing out swapped for a junction to a decoy structure: everything left and every decoy intact.
  - A junction on the way to `--out`, or as `--out`, empty or not, dangling or not: the target is left as it was. One into the repository or the checkout is refused (`cb_foreign.py`, `cm_dangling.py`, `cl_relative.py`).
  - A cleanup that fails never replaces the build's error or its exit code: `_unchanged` raising, `os.unlink` or `os.rmdir` refused, a real held-open file, `_clear` raising (`cc_fail.py`, `cn_open.py`, `cd_process.py` F6).
  - Limit 22 and the docstrings are true as worded.
- **Exit codes.** MEASURED (`cd_process.py`).
  - 0 with one BUILT line.
  - 1 with one REFUSED line, empty stderr and nothing left.
  - 2 for six misuse shapes.
  - 3 for a failing P2 stand-in and for a foreign file in the way.
  - Never 120 over seven closed-pipe, NUL and stdout/stderr shapes.
  - Seventeen hostile P2 file names are all refused as `seam`. Lines that quote non-ASCII paths are escaped (`co_ascii.py`).
- **The generator copies no CHECKED value.**
  - T1: the output is byte-identical with the metadata file present, absent, garbage, empty, another crate's, `null`, or with another generator name, on the twin and the Atlas crate.
  - T2: with the guards off, each producing function patched to a sentinel puts it in the output (`ct_t1t2.py`).
  - T3 by sweep (twin, two leaves per leaf class, alter and delete):
    - Only the file's digest re-sealed (2,279 trials): no crash, every step-9 refusal a `GuardError`, and the 389 accepted leaves are the carried classes (defect 3).
    - Every dependent digest re-sealed to a fixpoint (2,279 trials): no crash, 704 `GuardError` refusals at step 9. Nine more were regeneration differences, all in the manifest's `optimization_level`, `seed_transpiler` or `qiskit` version, which the Compile's text states (REPORTED, limit 20).
  - Metadata edits (1,168: every term of every entity, altered and deleted): no crash. Only the root's `qro:writer` and `qro:writtenAt` are accepted (header terms). Each CHECKED term is refused by its owner: `file-digest` or `raw-digest`, `commitment`, `known-answer`, `calibration-link`, `count-unpaid`, `raw-form` or `step-unbuilt`, `file-unlisted`.
- **Controls, twin and seam.** The seven controls come out as their rows say in the runner. The seam, checked with my own stand-in `qro.p2_measures` in a copy of the tree (`ce_seam.py`, 11 checks): built and checked with and without the module, and a module missing a function or contributing what collides is a `seam` raise with nothing left.
- **My own mutants** (`mutants_r2.py`, `mutants_x.py`, `hm_p12.py` adapted from `hm_t.py`; each target run unmutated first). 58 real mutants, 56 killed by their targeted tests.
  - They cover the identity, kind, reparse-point and ancestor checks, the clearing's order and loops, the list-keeping, the error and exit mapping, the checkout checks, the Atlas lines, `_Entities`, and G1 to G9 and G12.
  - Four edits in the incident's class (`os.removedirs`, an ancestor `rmdir`) are all killed, by tests that run on a world inside the test's own temp directory.
  - The two survivors are B1 (a real gap, below) and A5 (my own void mutant, equivalent by construction).

## Notes (below the bar)

**Test reach, where the code is right**
- B1: changing `except BaseException:` to `except Exception:` in `build` survives the adapter tests and the whole of tests/p1. No test raises an interrupt or exit inside a build and asks for the clearing. My run (`cc_fail.py` E4) shows the code does clear it.
- `test_the_adapter_holds_no_recursive_delete` looks for three names only (`rmtree`, `shutil`, `os.remove`). An `os.removedirs` edit would pass it, but the cleanup tests catch that edit (my X1 to X4).
- Three `atexit` `shutil.rmtree` calls remove `tempfile.mkdtemp` directories the code made: `plants_p1.py:84`, `tests/p1crates/p1crates_support.py:41`, and P1.1's `p1_builder.py:571`. They remove only what they made; I note them against CLAUDE.md item 9's spirit.

**Cleanup reach (limit 22 words these exactly)**
- Only directories the build made are checked on the way to a file.
  - A pre-existing `--out`, or anything above it, swapped for a junction to where it was moved is followed. The build's own files, which still match their identities, are cleared through it (MEASURED, `cb_foreign.py` C8; decoys untouched).
  - Nothing is removed that the build did not make, but the ruling's "never through a link" holds only for directories the build made.
- The identity is taken by path after creation, not from the created handle. `os.fstat(f.fileno())` would close that window for files; `mkdir` has no handle.
- If the `lstat` fails right after a `mkdir`, that directory is left unlisted and its ancestors stay (MEASURED, E3).
- A swap between the check and the `os.unlink` or `os.rmdir` of a listed path is a window any path-based removal has. Simulated: the swapped-in junction itself is removed (the link, never its target).
- A KeyboardInterrupt raised during the clearing replaces the build's error (`suppress(Exception)` does not catch it).
- READ only: a failure of the final `rglob`/`stat` (lines 220-221) is outside the `try`. It would exit 3 with a complete crate left, like the documented closed-stdout case.
- BELIEVED, not testable here: on a volume whose `st_ino` is 0 the identity check checks nothing. The Atlas plan follows file symlinks (`is_file()`), where the IBM plan refuses links.

**Prose and other**
- docs/P1.md:31, "accepted by all nine steps": steps 6 and 7 are P2's and not built in this tree.
- With every digest re-sealed (level B, limit 1), 1,042 of 2,279 twin edits are accepted.
  - The classes: gate lists (P2's), bundle-manifest entries (28 of the real crate's 93 manifest jobs never ran, so their entries are carried), the read's copies of IBM's fields, raw-result fields no reader uses, snapshot measurement dates, and the classes in defect 3.
  - The page says this in limit 1 without the scale.
- `made.directory(out)` runs before `plan()`, so misuse found in the plan (a link in the records, the read missing) creates the out and then removes it. Harmless.
- P1.1's test name and CLAUDE.md's timings are the lead's.

## What I did not do

- I did not test a host without long-path support (LongPathsEnabled is 1 here), a non-Windows host, a volume whose file numbers are 0, or file symlinks.
- I did not run P2's real module or the merge onto cbdb6a3 or P0.7. The seam was checked with my own stand-in.
- I did not sweep the 1,380-entity IBM crate leaf by leaf, or the Atlas crate at level B. The Atlas sweep stopped at 548 of 1,059 trials and did not reach the vector, the licence or the last law jobs' files. All sweeps take two leaves per class.
- I did not repeat P1.2's own mutants (281 and 58). I did not mutate G10. I did not re-measure the 6.1 s timing or P1.1's cost table.
- I used no key, no network, and nothing of IBM's or Moth's service.
- The Write tool refused to save this report as a file. My working notes are in `<scratch>\verifier-P12-r2\check\notes.md`.

## Disclosures and slips

- **The /tmp rule.** After the coordinator's message I checked, read only, what the owner's Temp holds from my session.
  - Every redirect and heredoc of mine targets my sandbox directory, and the launchers point TEMP into the sandbox, so I believe I wrote nothing there.
  - What is there from the session: the harness's own output files for my seven background tasks, in `<home>AppData\Local\Temp\claude\C--Users-logan-source-repos-QRO-Crate\68c192ad-f27d-4ef4-8eb1-78fb1f4a9918\tasks\` (`blpos0hq6`, `b1lbyth2j`, `bkp39h3yy`, `bhdjzq0zl`, `bkrq8fo7h`, `b06a63lwv`, `b2o4ykz7t`, each `.output`, 10 or 22 bytes, no listing).
  - Also two empty folders I cannot attribute: `<home>AppData\Local\Temp\tmp` (13:26:56) and `<home>AppData\Local\Temp\.tmpBsL5U6` (13:23:55).
  - I deleted nothing there.
- Three times I typed a bare `python` into my plain shell with an empty script (`python - &lt;&lt;EOF` with nothing in it, or `python - 2&gt;/dev/null`). The interpreter started outside the launcher, ran no code and wrote nothing. A fourth, `python3 -`, found no interpreter. Every real run went through sbx.sh or sbx-mid.sh.
- I ran `git status --porcelain --ignored` (read only, `GIT_OPTIONAL_LOCKS=0`) in moth-quantum to see whether its ignore rules cover record files. It printed the first ten names of ignored files under `.atlas\responses\`, one with an Atlas job UUID. I opened no file there and no credential file.
- In two console listings I printed Atlas job-id prefixes (8 hex digits). I masked IBM job ids everywhere I printed.
- A shell loop of mine, with a quoting error, built a crate into a directory literally named `exitm$o` in my sandbox. I removed it by its literal path. I also removed two listing files of mine (`tree-files.txt`, `sums-files.txt`) that held unmasked job ids in file names, by literal path.
- A false alarm of mine, corrected: `grep -c $'\r'` counted every line, because the pattern arrives empty in Git Bash. With `tr -cd '\r'`, P1.2's text files and the base have no CR byte, as CLAUDE.md item 2 says.
