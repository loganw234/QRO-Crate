# P1.2 verifier, round 3: report

## Verdict: NOT READY

I found two defects, both in the prose of docs/P1.md. I found none in what the code does and none in a gate. The cleanup held every attack except two race windows (N1 and N2 below). I filed them as notes, but the brief's "anything it touches through a link" may make them code defects, so they need the lead's ruling.

**Labels.** MEASURED means I ran it, and the script is named. Scripts are in `<home>AppData\LocalLow\qro-sbx\p12-r3\s\` and `s2\`, logs in `logs\`. All code ran through sbx.sh, and the runner through sbx-mid.sh. READ means I read the file. BELIEVED means neither. IBM job ids are masked as `&lt;job&gt;`.

## Defects

### D1. Prose (a stated limit that is incomplete): limit 21 does not name two classes of the real IBM crate that are held by their file's digest alone

- **Where.** docs/P1.md:268-283 (limit 21, "The classes: ...") and :132-134 ("limit 21 names the classes the checker holds by their digests alone").
- **Fault 1, the prediction files (MEASURED, `r1_repro.py`, as processes).**
  - I built the real IBM crate with the adapter: `BUILT ibm: 1073 files, 53269160 bytes, identity 8ec4dc39df52c0dc...`, ACCEPTED.
  - I appended one byte to `2026-10-05/ibm/ibm_fez/prediction-backend.json` and re-sealed only that file's `sha256` and `contentSize` in `ro-crate-metadata.json`.
  - `python -m qro check` exited 0 with `ACCEPTED 6e6b1490df5bb875...`.
  - All six prediction files, with a byte appended and with one JSON leaf altered (12 of 12), are ACCEPTED (`t2_real_classes.py`). They are 5,973,229 bytes, 11% of the crate.
  - READ: `_devices` in `qro/p1_generate.py` makes a File entity of each from its digest and size and reads nothing else.
- **Fault 2, Quantum-Film's own snapshots (MEASURED, `r1_repro.py`, as a process).**
  - In `2026-10-05/ibm/ibm_fez/properties-20261005T081622Z.json` I moved the date `gates[1105].parameters[0].date`, which is below the newest date, by one second. I re-sealed only the file's digest and size.
  - `python -m qro check` exited 0 with `ACCEPTED ca56913e09729d25...`.
  - In that file 6,632 of 6,652 dates are below the newest. The generator's claims from a snapshot hold only the stamp, the maximum date, and a digest that leaves every date out.
  - The read's own seven snapshots are held by the read's MANIFEST digests (G9 refuses an edit). A changed value, unit or `backend_version` in the same file is refused `calibration-link`.
- **Why no earlier sweep reached them.** The twin carries neither class: it takes its snapshots from the read and has no predictions. The second verifier's sweeps ran on the twin and the Atlas crate. This is round 2's D3 again, for the part of the crate the twin cannot reach.
- **Test.** `CARRIED` (tests/p1/test_p1_controls.py:538) has no sample of either. So docs/P1.md:282-283, "A test holds a sample of each class as accepted", is true of the listed classes only.
- **Suggested.** Name both classes in limit 21. Hold a sample of each on the real crate in p1-crates.

### D2. Prose: the G9 row's "cannot move a link verdict" is false where the MANIFEST is edited, on a slice such as the twin

- **Where.** docs/P1.md:122, "a snapshot of the read dropped from the crate, with its MANIFEST or without, cannot move a link verdict".
- **Fault (MEASURED, `r1_repro.py` part 2 as a process, and `t3_manifest_edit.py`).**
  - On the twin built by the adapter, I dropped `2026-10-14/ibm-refetch/ibm_kingston/properties-20261005T122118Z.json`.
  - I took its entry out of `2026-10-14/ibm-refetch/MANIFEST.json` (72 entries to 71, in the file's own style) and regenerated the metadata with the toolkit's `rebuild`.
  - `python -m qro check` exited 0 with `ACCEPTED a95a51c5bcccd770...`. The jobs' links were three `history-at-first-shot` and one `history-in-gap`. Now all four are `history-at-first-shot`.
  - Controls hold: dropping the snapshot alone, or with the MANIFEST file, is refused by G9 at regeneration.
- **What it is.** The producer edits a file whose digest no other record holds, which is limit 1's producer. Round 2's reason for its D4 named "drops or edits the MANIFEST"; the fix covers the drop, and the sentence still reads as unconditional.
- **Reach.** On the real IBM crate the same edit is refused: regeneration raises `G7 ... the snapshot the history returned, ...122118Z.json, is not carried`, because a job's read record names it (`t3_manifest_edit.py real`). I found no snapshot in the real crate whose drop would move a link. So D2 is a fact about slices and the guards, not about the real crates.
- **Test.** None pins the edited MANIFEST as accepted.
- **Suggested.** Say "cannot move a link verdict unless the MANIFEST is also edited (limit 1)", and pin it with a twin test.

D2 is the weaker of the two. If the lead takes it as limit 1's producer, D1 alone gives NOT READY.

## Notes (below the bar)

Findings about what the code does: N1 to N4. About a gate: none. About prose or test reach where the code is right: D1, D2 and the survivor B8.

- **N1. Later writes follow a directory swapped for a junction mid-build (`a2_swaps.py` S1, `a5_swap_empty.py`, MEASURED).**
  - After the 2nd write I moved `out/2026-10-05` away and put a junction to a decoy in its place, and the build went on.
  - With a decoy holding a file: 63 files went into the decoy through the junction. The clearing left them (their listed ancestor had changed). The generator walked through the junction and refused G12, exit 1.
  - With an empty decoy: `main()` printed `BUILT ibm: 73 files ...`, exit 0, after 53 files went through the junction. `python -m qro check` on that out then says `REFUSED file-link at 2026-10-05`.
  - Limit 22 and the docstrings speak of removal only. Nothing checks the listed directories before a write, and `Crate`'s `os.walk` descends into junctions on Windows.
  - This needs another party to swap a directory the build made. The cheap remedy is to refuse a link in the generator's walk and check the listed parent before each write. At minimum, limit 22 should state it.
- **N2. The check-to-unlink window reaches a foreign file (`a2_swaps.py` S2, simulated, MEASURED).**
  - After `_unchanged` returned, I swapped the listed `bundle` directory for a junction to a decoy holding a file of the same name. `os.unlink` removed the decoy's file through the junction.
  - The second verifier named this window for the listed path itself, where only the junction is removed (`cc_fail.py` E6 and E7 pass here).
  - Limit 22's "a link in the place of a directory, through which nothing is removed" is true at the time of the check, not in the window. BELIEVED: closing the window needs handle-based calls, which Python's stdlib lacks on Windows.
  - Strictly read, N1 and N2 are code defects under "anything it touches through a link". I did not count them because they need an adversarial swap inside the build and the window was already seen in round 2. The lead rules.
- **N3. An `--out` string of about 32,768 characters or more gives exit 3 in process (`a1_outs.py`, MEASURED).** `os.mkdir` raises `ValueError: mkdir: path too long for Windows`, not an `OSError`. A Windows command line holds 32,767 characters, so no process can carry it. Outs of 1,000 and 32,000 characters give exit 2.
- **N4. Round 2's notes stand.** A KeyboardInterrupt during the clearing replaces the build's error; the exit code is 3 either way. A volume whose `st_ino` is 0 would make the identity check check nothing (BELIEVED, untestable here).
- **Test reach, where the code is right.**
  - B8 survives all of `tests/p1`. It changes G7's `r.holds.get(flag) is True` to a truthiness test, so a read record with a flag of `1` instead of `true` would be accepted. The code is right; no test pins the strictness.
  - Two mutants survived a narrow `-k` selection of mine and are killed by tests whose names carry no guard name: G7a by `test_a_job_with_no_span_still_names_a_snapshot_the_crate_must_carry`, and B3 by `test_a_bundle_holds_one_known_answer_job_and_that_job_one_known_answer_pub`. That is my selection, not a gap.
  - `test_the_adapter_holds_no_recursive_delete` reads names in the source text. The behaviour is held by the cleanup tests, which kill my A7, A8 and A10 to A15.
- **CLAUDE.md item 6.** This is the third NOT READY and my defects are prose. The lead may weigh them under the cap. N1 and N2 are the only items about what the code does.

## What held

- **Freeze (MEASURED).**
  - `sha256sum -c` over `frozen\tree` gave 367 of 367. `SHA256SUMS.txt` begins `631e8593731581cc`. The eight packet digests match the brief, and the worktree's files hash as the packet's.
  - Against 37640f0 (`git archive`, read only) the packet adds 76 files and changes only `docs/README.md` (one index line) and `qro/register_p1.py` (`GENERATORS`).
  - The twin's 56 files (828,488 bytes) each equal `git show 3a73823:&lt;path&gt;`. No Atlas byte, home path or address shape is in the added files, and there are no CR bytes.
- **The runner (MEASURED).** `sbx-mid.sh bash verify/run.sh` with `QRO_MOTH_ROOT`, on my committed copy (a60865b): run `20261030-204517-5574-a60865b`.
  - 19 passed, 0 failed, 5 skipped by name (p2, p4, p2-crates, profile, p4-shacl).
  - p1: 1,726 passed in 256.65 s. p1-crates: 39 passed in 204.31 s.
  - controls-run: 16 of 16 built controls as section 11 says. The seven of P1 come out as their rows say: `job-reattributed` `commitment`, `bits-mirrored` `known-answer`, `qpy-only` accepted, `calibration-late` and `calibration-gap` `calibration-link`, `calibration-restamped` and `shot-moved-resealed` accepted.
  - moth-quantum's `.git/index` kept its time (2026-10-15 20:43:39) after the runner, my builds and my sweeps.
- **Real crates (item 4, MEASURED).**
  - Built as processes: IBM 1,073 files, `8ec4dc39df52c0dc...`; Atlas 31 files, 4,975,638 bytes, `f9c1a259786e3e9a...`. Both ACCEPTED with the same identity.
  - The page's counts hold: 1,380 entities, Dataset 68, File 995, Pub 68, 161 mentions, the longest path 77 characters in ten files and 76 in eight, Atlas 63 entities.
  - The design's measurements, by the second verifier's code that imports no `qro` (`measure_ibm.py`, `measure_atlas.py`):
    - 68 of 68 commitments equal the claim, the line, the record and IBM's echo.
    - 12 digests in 6 classes.
    - Links 57 and 8, my word equal to the claimed word for 65 of 65.
    - 31 of 31 known answers msb-first, 0 mirrored.
    - Atlas worst |z| 2.15 against 172.96 and 346.28.
  - Limit 4 holds: each of Quantum-Film's five snapshots dropped from the real crate regenerates, is ACCEPTED and moves no link (`r3_limit4.py`, 5 of 5).
- **Round 2's fixes.**
  - D1, exit class:
    - About 75 `--out` shapes in process, 23 argv shapes, and the process script (`cd_process.py`, 37 of 37). A last component ending in a space, spaces only, a real unlistable directory (`C:\System Volume Information`), a file, a path under a file, and a dangling junction as the out, below it and two below it, all give exit 2 with the out named and nothing made.
    - The only exit 3 I found is N3. The stated race (another party's file in the way) is exit 3 and the file stays.
  - D2, counts: `test_p1_page.py`, and 111 and 31 are the counted ones.
  - D3, limit 21: the Atlas side is complete (below). The IBM side is D1.
  - D4, G9: the requirement refuses nothing honest.
    - The repository's read has its MANIFEST in both directories (72 entries in `ibm-refetch`).
    - The packet's `records/2026-10-14` equals the live repository's, 146 files. The four dry-run probe files are listed by no MANIFEST.
    - The real crates and the twin are accepted. Dropping the MANIFEST is refused (see D2 for the edit).
  - Notes: the interrupt test kills `except BaseException` made `Exception` (my A9). The identity is taken from the handle (my A5 is killed). The Atlas plan refuses a link where it takes a file (my A11 is killed).
- **Round 1's fixes hold.** A byte appended to the real Atlas commitments file is refused `not what qro-p1-atlas makes`. The path figure is 77, and limit 16's test passes in the runner.
- **The cleanup (item 2).**
  - A failed build at every write (1 to 73), mid-file, and at the out, plan, question files, generator and writer, into a fresh nested out, an existing empty one and one whose parents it made: the world comes back exactly and the error out is the injected one (`ca_inject.py`, 80 of 80).
  - A foreign file, directory, junction or hard link put before, during and after the writes, and listed paths or the pre-existing out swapped for a junction, a directory, a file or a hard link (`cb_foreign.py`, 43 of 43). Each foreign object stays with its ancestors, and no decoy is touched.
  - A listed directory, a listed file, the deepest directory and the pre-existing out each swapped for a dangling junction at clearing time (S3 and S5; this host opens none). The build's own error comes out, entries beside the link are cleared, the moved tree and decoys are intact, and no target is recreated.
  - A hard link to a build file and a read-only build file are left as limit 22 says (S4).
  - A cleanup that fails never replaces the build's error or exit code: `cc_fail.py` 9 of 9, `cn_open.py`, and `cd_process.py` F6.
  - The two changes the lead did not ask for hold. `GIT_OPTIONAL_LOCKS=0` is held by the index test (my A12 is killed, and the index time did not move). A file put where the build writes gives exit 3 and stays (F5).
  - Limit 22 and the docstrings are true as worded, except where N1 and N2 apply.
- **The generator (item 3).**
  - T1 (`t1_independence.py`, 18 of 18): the output is byte-identical with the metadata file absent, empty, garbage, `null`, a list, another crate's, naming the other generator, or with zeroed digests, on the twin and the real Atlas crate, and across PYTHONHASHSEED 0, 1, 777 and random.
  - Complete Atlas leaf sweep (1,660 trials, every leaf class twice, altered, deleted and retyped, only the file's digest re-sealed):
    - No crash, and every step-9 refusal a `GuardError` (or the body mismatch for the commitments file).
    - 1,377 trials accepted, in 72 classes of five file kinds, all inside limit 21's Atlas list. The vector refuses 20 of 20 edits as `raw-form`.
  - READ: the generator reads no CHECKED value from a record (`_job_entities`, `_snapshots`, `atlas`).
  - The 111 and 31 planted faults and the honest crates pass in the runner.
- **Mutation (item 8).**
  - My harness `hm_r3.py` ran every target unmutated first. I ran 37 one-line mutants: A1 to A15 of the round-2 adapter code, G9a to G9f, G7a and G7b, and B1 to B14 of the guards.
  - 36 were killed. B8 survived (see the test-reach note above).
- **Controls, twin, seam, exit codes (item 5).**
  - The seam, with the second verifier's stand-in `qro.p2_measures` in a copy of the tree: a crate built with the module is ACCEPTED with it and REFUSED `metadata-generated` without it. A module that collides on an entity or term, or lacks `contribute`, is a `seam` raise with nothing left. The Atlas crate takes the stand-in too.
  - Exit codes as processes (`cd_process.py`): 0 with one BUILT line; 1 with one REFUSED line and empty stderr; 2 for six misuse shapes; 3 for a failing stand-in and for a foreign file in the way; 120 never, over seven closed-pipe and NUL shapes.
- **Whose files, and unintended changes (items 6 and 7).**
  - Nothing outside P1.2's list, and no earlier stage failed.
  - A junction in a crate is refused `file-link` by P0 before step 9 in three placements (`a4_junction_in_crate.py`).
  - An 8.3 alias (`TREE-S~1`) and dot-dot spellings of an out inside the repository are refused, exit 2.

## What I did not do

- I did not sweep the real IBM crate leaf by leaf (1,380 entities). I tried the classes the twin cannot reach (predictions, Quantum-Film's snapshots) and 15 more files by kind: 39 trials.
- I did not run P2's real module or the merge onto cbdb6a3 or P0.7. The seam was checked with a stand-in.
- I tested no host with long paths disabled, no non-Windows host, no volume whose file numbers are 0, and no host on which a dangling junction opens (that one by reading only).
- I did not repeat P1.2's own 364 mutants, only my 37. I did not run the quick budget alone; its stages are a subset of the full run.
- I used no key, no network, and nothing of IBM's or Moth's service.

## Disclosures

- Once I ran a bare `python3 -` in my plain shell with an empty heredoc. It ran no code and wrote nothing. Every other Python run went through sbx.sh or sbx-mid.sh.
- As shapes for the exit code I passed `C:\System Volume Information`, `C:\System Volume Information\x` and `C:\Windows\System32\config` as `--out`. Each was refused with exit 2, and the guard refused the `mkdir` below the first.
- I stopped my own redundant `mut4` harness (G7a and G7b against the whole suite) with a PowerShell filter that was too loose. It also stopped four of this session's Bash wrapper shells, one of them a wait loop of mine. No file was touched, and the other runs were unaffected.
- I made junctions only inside my directory, each pointing inside it, and removed each. The dangling ones were removed after remaking their targets. A final scan of my directory finds no reparse points and no leftover worlds.
- I masked every job id I printed. Console output named only device directories and snapshot stamps.
- The Write tool refused to save this report as a file. My working notes are in `<scratch>\verifier-P12-r3\check\notes.md`.
