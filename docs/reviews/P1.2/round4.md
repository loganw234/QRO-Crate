# P1.2 verifier, round 4: report

## Verdict: NOT READY

I found two defects in what the code does, both in P1.2's own files and each reproducible in a few lines. I found none in a gate. Both are narrow. D1 needs a hostile record, and D2 needs a deliberately extended-length `--out`. Neither touches the real records or the real crates. Every round-3 fix holds, the cleanup held every attack I made, and the full runner passes.

Labels: MEASURED means I ran it, with the script named. READ means I read the code. BELIEVED means neither. All code ran through sbx.sh and the runner through sbx-mid.sh. My scripts are in `<home>AppData\LocalLow\qro-sbx\p12-r4\s\` and logs in `...\p12-r4\logs\`. IBM job ids are masked.

## Defects

### D1 (code: a crash and a wrong exit code). A lone surrogate in a record crashes the generator, and the adapter exits 3 ("not a verdict") where the records should be refused with exit 1

- **What happens.**
  - The strict reader accepts a JSON string holding a lone surrogate written as an escape (`\ud800`).
  - Three places then encode a record's string as UTF-8. The `UnicodeEncodeError` is a `ValueError` but not a `GuardError`, so it leaves the generator.
  - `main()` turns it into `FAILED: the adapter itself failed, UnicodeEncodeError ...; this is not a verdict`, exit 3.
- **The three sites (READ, each MEASURED below):**
  1. `qro/p1_generate.py:874`, G11: `qasm.encode("utf-8")` on an Atlas request's `body.params.circuit_qasm`.
  2. `qro/p1_commit.py:29`, P1.1's `stream`, reached from `_g4_g5` through `commitment_of`. G1 to G3 pass when the manifest, record and line agree on the value, so G4 is the first to touch it. It applies to `salt`, `stock`, `role`, `basis`, `kind`, `route` and `program`.
  3. The same `stream`, reached through `rec.commitment_v2` in `_atlas_lines` (G11). It applies to an Atlas commitments line's `salt` or `stock`. `engine` is caught first, as "more than one engine".
- **Faults that show it:**
  - Atlas (MEASURED, `h1_surrogates.py`): the real Atlas files laid out as a slice, with one submit file's `circuit_qasm` set to `\ud800`. `main(["atlas","--moth",slice,"--slice","--out",o])` gives exit 3. The unmodified slice gives exit 0, `BUILT atlas: 31 files ... f9c1a259...`.
  - IBM (MEASURED, `h1c_ibm_main.py`): a slice whose known-answer `salt` is `\ud800` in the manifest and the record, with the lines' and markers' manifest digest and the record's own digest recomputed. `main()` gives exit 3 and nothing is left behind. The control, an ASCII salt that disagrees, gives exit 1 `REFUSED metadata-generated ... G3`.
  - Atlas lines (MEASURED, `h1d_atlas_line.py`): `salt` or `stock` of a commitments line set to `\ud800` makes `G.atlas` raise `UnicodeEncodeError`.
- **The checker refuses the same crates with exit 1** (MEASURED, `h2_checker_on_surrogates.py`):
  - Atlas: step 9 `metadata-generated ... qro-p1-atlas failed on the records: UnicodeEncodeError`.
  - IBM: step 4 `commitment ... cannot be checked: UnicodeEncodeError`.
  - The lead's ledger entry 2026-10-19 already rules a lone surrogate "refused `commitment`" on the checker side.
  - Only the adapter turns it into "the adapter itself failed".
- **Claims it contradicts (READ):**
  - `qro/p1_records.py` docstring: "a record that is not in its format is a refusal of the build, never a crash".
  - `qro/p1_adapter.py`: exit 3 "is never a verdict on the records".
  - Round 1's D3 was this class.
- **Reach (MEASURED):**
  - My crash fuzz poisoned two leaves of each leaf class with a lone surrogate, "", NUL, "é", None, [], {}, true, 1.5, -1 and 2^62. The digests that other records hold were resealed to a fixpoint.
  - Twin: 6,175 trials, 0 crashes.
  - Atlas: 3,500 trials, 6 crashes, all of them `circuit_qasm` in each of the six law submit files.
  - Single-file poison cannot reach site 2, because G3 compares the value in two files. Writing it consistently in the manifest and the record reaches it (the faults above).
- **No test and no stated limit holds this.** The surrogate appears nowhere in the tests or in docs/P1.md.

### D2 (code: a wrong acceptance). An extended-length `--out` gets past "lies in neither this repository nor the checkout"

- **Fault (MEASURED, `outs3_bypass.py`).** My sandbox copy of the tree is the repository, since the adapter takes its `REPO` from its own file. The command was:
  ```
  python -m qro.p1_adapter ibm --moth tests/p1/data/moth --slice --out "\\?\&lt;repository&gt;\bypassC"
  ```
  It exited 0 with `BUILT ibm: 73 files, 4300007 bytes`, and the 73 files landed inside the repository. The plain spelling of the same path is refused, exit 2, "inside this repository".
- **Every extended-length spelling passes `check_out`** (MEASURED, `outs4.py`):
  - The forms tried were `\\?\C:\...`, `//?/C:/...`, a lower-case drive, a changed case, a `.` component, and two new levels deep.
  - They pass for the repository and for the checkout. The control outside both also passes.
  - Against the real moth-quantum path, read only, the plain form is refused and the extended one passes (`outs6_real_checkout.py`; nothing was created).
- **Cause (MEASURED, `outs5_realpath.py`).**
  - On CPython 3.12.15, `os.path.realpath` keeps the `\\?\` prefix that its input had, even for an existing directory.
  - `_inside` therefore compares `\\?\C:\...` with `C:\...`, and `parent in path.parents` is false.
  - A trial patch that strips the prefix after `realpath` in `_inside`, in my mutant copy only, refuses all 14 probes. The outside control still passes.
- **Claims it contradicts (READ):**
  - The `p1_adapter.py` module docstring, lines 8-11.
  - docs/P1.md:147-149, which says an `--out` "that lies in this repository or in the checkout" is refused with exit 2.
  - The code's purpose, which the docstring gives as: a crate built in the tree "could be committed by a `git add -A`".
- **No test covers an extended-length out.** The tests use plain spellings, `..` and links.

## Notes

These do not block. I report them plainly.

**Test reach, where the shipped code is right**
- Mutant C22 survives. It narrows the file loop's `suppress(OSError)` in `_clear` to `FileNotFoundError`, so one file that cannot be removed stops the clearing of every other file.
  - The shipped code is right. With a real open handle on one build file (`h6_open_handle.py`), exactly that file and its five ancestors were left, and everything else was cleared.
  - No test leaves exactly one file un-removable. The tests make every unlink fail.
  - The directory loop's twin, C23, is killed.
- Mutant B8b survives. It makes G7's two per-PUB gate-list flags `gate_list_equal` and `gates_equal` truthy tests instead of `is True`. The shipped code is right. B8's own mutant is killed by the new planted fault, but the sibling flags are not pinned.
- Mutant C10 survives (`stat` for `lstat` in `_identity`). It is equivalent unless another party swaps a link between `mkdir` and `lstat`.
- Two tests build a full crate into the real repository or checkout if their guard regresses.
  - Observed: in my mutant C13a, `test_an_out_inside_the_repository_is_misuse_and_nothing_is_created` built a crate into the working copy and left it behind.
  - `tests/p1crates/test_p1crates_adapter.py::test_the_adapter_will_not_build_into_the_checkout_or_into_this_repository` would do the same into the real moth-quantum checkout. Only the launcher holds that here.

**Prose**
- The sentence that is false because of D2 is docs/P1.md:147-149.
- docs/P1.md:158-159 lists exit 3 as only "another's file where the build writes" and "a verdict that cannot be written". Any host OSError at a later entry (a full disk, a name or path the host takes at the first entry but refuses later) is exit 3 too.
  - SIMULATED, `h4_late_oserror.py`: ENAMETOOLONG, ENOSPC and a WinError 3 each give exit 3 and the world is restored.
  - BELIEVED: on a host without long paths, an out of roughly 182 to 259 characters would behave this way. This host has long paths on (LongPathsEnabled=1).

**Other (BELIEVED)**
- A `\\localhost\C$\...` out is the same class as D2. Here it fails with "Network access is denied". On a host where the share opens, I believe it would pass `check_out` the same way.
- A volume whose file numbers are 0 would make the identity check check nothing (round 3's N4, still open).
- 196 PytestWarnings in each pytest stage are `rm_rf` errors on `garbage-*` folders in the shared temp (older runs). My runs stranded no junction. No entry named for the junction test was newer than my start.

## What held

- **Freeze (MEASURED).**
  - `sha256sum -c` over the packet's tree gave 367 of 367. `SHA256SUMS.txt` begins `ee302cc8af40ba56`. The ten packet digests equal the brief's.
  - The worktree has exactly 76 untracked files and the two changed ones. Its index time is unchanged.
  - Against 37640f0 the packet adds 76 files and changes only `docs/README.md` (the one index line) and `qro/register_p1.py` (`GENERATORS`).
  - The twin's 56 files (828,488 bytes) each equal `git show 3a73823:&lt;path&gt;`. No Atlas-named file, home path or address is in the added files. The only CR bytes are in 6 binary `.qpy` files.
- **Full runner** (MEASURED; my committed copy 94e019b, run `20261030-221940-21834-94e019b`).
  - 19 passed, 0 failed, 5 skipped by name.
  - p1 had 1,732 passed and p1-crates 41 passed, as the brief says. controls-run: "16 of 16 built controls came out as section 11 says".
  - moth-quantum's `.git/index` time (2026-10-15 20:43:39) was unchanged after my builds and the runner.
- **Real crates** (MEASURED, adapter as a process).
  - IBM: `BUILT ibm: 1073 files, 53269160 bytes, identity 8ec4dc39...`. Atlas: `31 files, 4975638 bytes, f9c1a259...`. Both are ACCEPTED by `qro check` with the same identities.
  - The page's counts hold: 1,072 and 30 files plus the descriptor, and the longest paths are 77 characters in 10 files and 76 in 8.
  - The second verifier's code that imports no `qro` gives 68/68 commitments, 12 digests in 6 classes, links 57 plus 8, 31/31 known answers msb-first, and Atlas |z| 2.15 / 172.96 / 346.28.
- **Round 3's fixes.**
  - **Limit 21.** The classes the real IBM crate has and the twin lacks are exactly the 6 prediction files and Quantum-Film's own 5 snapshots (`real_delta.py`).
    - One leaf of each of 20 classes of `ibm_fez/properties-20261005T081622Z.json` was altered, with only the file's digest resealed (`real_snap_classes.py`, whole checker). Exactly three date classes are ACCEPTED: `gates/*/parameters/*/date`, `general/*/date` and `qubits/*/*/date`. The other 17 are refused `calibration-link`.
    - A prediction file plus one byte is ACCEPTED. The Atlas accepted classes (3,068 of my 3,500 trials) all fall inside limit 21's Atlas list.
  - **G9 row.** On the real crate, the 12:21:18 snapshot dropped with its MANIFEST entry is refused by G7, "is not carried". On the twin it regenerates and the checker ACCEPTS (`g9_real.py`).
  - **N3.** Outs of 32,768 and 40,000 characters give exit 2 with nothing left. About 70 further `--out` shapes gave no exit 1 or 3 (`a1_outs.py`).
  - **B8.** The planted fault `commitments_equal=1` kills the truthy mutant.
  - **Hard-linked tests.** Every write of the toolkit unlinks first: `write_file`, `patch`, `rebuild` and `Forge.write`.
    - With `write_file` mutated to write in place, the new prediction test fails under the guard ("on a file with another name, a hard link").
    - The two new tests pass alone and in the runner. The real crate's digests were unchanged after each plant.
    - BELIEVED: without the guard, the tests' own digest checks would also fail.
  - **Junction test.** Passing, and with an assertion made to fail after the junction exists, it leaves no junction (`find_links.py`: 0 links).
- **Round 2 and round 1.**
  - Round 2's D1 to D4 hold:
    - The count test fails on a wrong count.
    - G9 refuses nothing honest: four honest slices of the real records, other than the twin, built and were ACCEPTED (`slice_honest.py`).
  - Round 1's D1 and D2 hold (`r1_checks.py`). The two changes the lead did not ask for hold: `GIT_OPTIONAL_LOCKS=0` (index time unchanged) and the foreign file giving exit 3.
- **Cleanup.**
  - The earlier verifiers' scripts, rerun on this tree:
    - ca_inject 80/80
    - cb_foreign 43/43
    - cc_fail 9/9
    - cd_process 37/37, exit codes 0, 1, 2 and 3, never 120
    - a2_swaps: its one "fail" is the simulated check-to-unlink window that limit 22 now states
  - My own: a junction, directory or file put at a name the build is about to make, 18 rows, nothing foreign touched (`h5_prejunction.py`).
  - Limit 22 and the docstrings are true as worded. The adapter's only deletes are `os.unlink` and `os.rmdir`, both behind `still()`.
- **Generator independence (T1).**
  - By audit events (`t1_open.py`), the generator opened 72, 30 and 1,072 files of the twin, Atlas and IBM crate. None was `ro-crate-metadata.json`, and nothing outside the crate.
  - The output is byte-identical with the descriptor removed, garbage, or with every CHECKED term changed.
  - A metadata sweep of the real IBM crate through the whole checker (`meta_sweep_real.py`, 45 edits, all 15 CHECKED terms, first/middle/last holder) found every edit refused by its owning step. None was accepted.
  - Whole-file garbage on every file with digests resealed: twin 1,292 trials and Atlas 540, 0 crashes.
- **Mutation** (46 of my own; all except C22, C10 and B8b killed).
  - Adapter, 25: 23 killed. C22 and C10 survive (see Notes).
  - Guards, 21 of 21 killed. They include the survivors the first verifier listed for G2, G3, G6, G9's digest leg and G11's id8 and status.
  - My first mutant driver gave false kills after C13a left a crate in the working copy. I reran those with a cleaning driver, and the record above is the rerun.

## What I did not do

- I did not run P2's real `qro/p2_measures.py` or the merge onto 83503b0. The seam was exercised only with the third verifier's stand-in, copied into a scratch tree.
- I did not test a host with long paths off, a non-Windows host, a volume with file numbers of 0, a host that opens dangling junctions, or a host where `\\localhost\C$` opens.
- I did not sweep the 1,380-entity IBM crate leaf by leaf. I covered its classes: 20 snapshot classes, the prediction file, 45 metadata edits, and 4 honest slices.
- Multi-file poison for IBM was tried only as the salt and the manifest-and-record pair, and not enumerated.
- I did not repeat P1.2's 364 mutants, and I did not run the quick budget alone. Its stages are a subset of the full run.
- I did not run the `GIT_OPTIONAL_LOCKS` mutant. A survivor would let git rewrite moth-quantum's index, which is not mine to risk. I checked the claim directly through the index time instead.
- I used no key, no network and nothing of IBM's or Moth's service.

## Disclosures

- Two of my console outputs showed IBM job ids unmasked: a pytest assertion message that listed twin files, and the runner's controls-run lines. Nothing with an id was written to my notes or to this report.
- Early on I ran a plain `git status` and `git log` in the P1 worktree. The index time shows nothing was rewritten.
- A half-used scratch world of mine (`worlds/msr`, hard links to my built real crate) was removed before I reran the script. No copy was ever made onto existing names.
- A final scan found 0 links in my directory and an empty `worlds\`. The directory holds about 425 MB of copies, crates, logs and mutant copies. I left them for the lead.
- My processes may have left entries in the shared `qro-sbx\tmp`, which I did not clean because it is outside my directory.
- My working notes are in `<scratch>\verifier-P12-r4\check\notes.md` and `notes2.md`. The tool refused a separate report file, so the report is this message.
