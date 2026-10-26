# P1.1, round 1: NOT READY

Three defects are about what the code does (D1 to D3), and one is about prose (D4). Each is reproduced by a script in `SCRATCH\verifier-P11-r1\check\`. SCRATCH is `<scratch>`. IBM job ids are masked or left out below.

**The freeze.**
- MEASURED: `sha256sum -c` over `tree\` against SHA256SUMS.txt gave 274 files and 0 mismatches. SHA256SUMS.txt itself starts `9b59dcb31f2b57b8`, and the four copies' hashes match the prefixes you gave.
- MEASURED: `diff -rq` of `tree\` against the P1.1 worktree shows no difference.
- MEASURED: against `git archive 7f40400`, the tree adds only the seven modules (`qro/p1_forms.py`, `p1_commit.py`, `p1_decode.py`, `p1_calibration.py`, `p1_graph.py`, `p1_steps.py`, `register_p1.py`) and `tests/p1/`. Nothing else changed, so scope item 8 is clean.

**What held.**
- MEASURED: the full runner in my copy passed 18 stages, failed 0, and skipped 6 by name (p2, p4, p1-crates, p2-crates, profile, p4-shacl). `--budget quick` passed 15, failed 0, skipped 3, in 85 s beside other work. The p1 stage took 22 s (945 tests).
- MEASURED (`real_check.py`, with my own `.npy` reader, decode, expected-set parse and values-digest):
  - 68 of 68 echoes equal the recomputed commitment, the job line's, the record's and the manifest's.
  - P1.1's `ibm_counts` equals Quantum-Film's counts 68 of 68.
  - 31 of 31 known answers hold `msb-first` and 0 of 31 hold `lsb-first`.
  - The 12 snapshots give digests equal to my recipe's (kingston 3 classes, marrakesh 2, fez 1), and the test's 7 golden literals match mine 7 of 7.
  - The link rule gives 57 `history-at-first-shot` and 8 `history-in-gap`, with 1 job whose running-time snapshot differs.
  - The Atlas vector holds under `atlas-register` (128 positions, worst |z| 2.154) and fails under `circuit-order` (172.96).
- MEASURED (`real_crate.py`): the whole checker accepts a 65-job IBM crate I assembled from the real files, with link words from my own implementation of the rule.
  - Faults planted in real bytes (`real_faults.py`) are refused by the expected names:
    - bit order flipped;
    - two bundles' known-answer raws swapped;
    - a wrong link word;
    - `startTime` plus one microsecond;
    - one echo digit changed.
- MEASURED: P0's fixture is accepted through the command line, as a process, with P1 loaded, with `sys.modules` set to None for the six `qro.p1_*` modules, with a raising meta-path finder, and with a package copy lacking them. Only `register_p1.py` being unimportable gives exit 3, as P0 intends.
- MEASURED: `load()` registers steps 4, 5 and 8 and the three raw forms, no generators and no count rules, and imports no `qro.p1_*` module.
- MEASURED (`seam.py`): `pub_counts` equals Quantum-Film's record counts for all 68 Pubs on file-read metadata. It gives the same answer on bare entities (shuffled, no digests, no `@context`, no root or descriptor, one-element type lists, single refs).
- MEASURED: hostile bytes into the readers (`hostile1.py`), covering:
  - nesting from 10 to 100,000 levels;
  - a BOM, UTF-16, 5,000-digit integers, `1e999`, lone surrogates;
  - zlib and npy lies, trailing streams, gzip, a header declaring the cap and the cap plus one.
  - None escaped as anything but a refusal.
- MEASURED: structure-aware fuzz found no exit 3. `fuzz1.py` ran 210 trials of file mutations on the real crate. `fuzz2.py` ran about 3,500 trials re-pointing relations on the small crates.

## Defects

**D1 (code, and a gate that cannot see it): the Atlas reader refuses five of the six real Atlas law results.**
- READ: `parse_atlas_result` closes the top level to `{job_id, path, response, status, taken_from}`.
- MEASURED (`atlas_check.py`): the five results in `moth-quantum/docs/records/2026-09-26/p3/` (`atlas-3673f9fe`, `-579df87d`, `-5831ff5e`, `-933138bc`, `-d017540c`) each carry a top-level `fetched_at`. Each is refused: `RawFormError: the result: holds ['fetched_at'], which the form does not`. Only the 2026-09-25 result parses.
- MEASURED (`real_atlas.py`): the whole checker on the six real law results plus the vector is refused `raw-form` at step 3, at `2026-09-26/atlas-3673f9fe-result.json`.
  - With the key dropped, all six decode to 1,995, 2,006, 1,997, 2,026, 2,020 and 2,027 layouts, and the crate is accepted.
- Consequence: P1.2 cannot build the Atlas crate from the real records, and P2's `pub_counts` would raise on those Pubs. BELIEVED: the second follows from `pub_counts` calling the same parser.
- The design's table listed the wrapper without `fetched_at`, and the build followed it. The build's own real-record run covered one of six Atlas results (its "Atlas law job of 2026-09-25").
- The p1 stage and all 1,027 mutants build inputs only in the closed shape, so they cannot see this. The gate that could, `p1-crates`, is P1.2's.

**D2 (code): the steps keep every parsed raw result, so a small crate drives the checker to MemoryError and exit 3.**
- READ: the `cache` dicts in `step4`, `step5` and `step8` hold each parsed result, `body` bytes included. The 64 MiB cap is per result.
- MEASURED (`bigcrate.py build big60 60 10000000`): 60 honest-looking IBM jobs, each raw 26,931 bytes on disk and 20 MB inflated, 1,840,310 bytes for the whole crate.
- MEASURED (`peakmem.py`, job-object peak):
  - The command line's peak memory is 52 MB for 1 raw, 148 MB for 6 and 1,180 MB for 60.
  - Steps 1 to 3 alone peak at 52 MB, and step 4 alone at 1,180 MB.
- MEASURED (`memcap.py 1024 python -B -m qro check ..\big60`, run from `check\crate`): `FAILED: the checker itself failed, MemoryError ... this is not a verdict`, exit 3. A one-job crate of the same raw size is refused normally under 256 MB.
- BELIEVED: at the cap (about 64 MiB per result, roughly 90 KB on disk), a crate of a few hundred such results costs gigabytes.
- The brief says exit 3 is never a crate's fault. The docstring of `_visit` and limit 17 call MemoryError "the host's". Limit 12 holds only per result.

**D3 (code): step 8's "snapshots the crate carries of its device" is by device entity, so a carried snapshot on a second device entity of the same name is invisible to the gap rule.**
- READ: `_snapshot8` keys `by_device` by the entity's `@id`, and `_job8` uses `carried = by_device.get(device, {})`. A snapshot's `backend_name` is held to its entity's name, but never to the Job's device name.
- MEASURED (`cases3.py`, builder crate): the gap job names the 11:28:27 and 12:21:18 snapshots, and the 12:21:18 one is stamped and fully measured before the first shot.
  - Claiming `history-at-first-shot` [11:28:27] is refused, correctly, as "the link is history-in-gap".
  - Attach the 12:21:18 snapshot to a second `IndividualProduct` with the same `name`, and the same false claim is ACCEPTED by the whole checker.
- The crate carries the evidence of the gap and step 8 does not see it. Limit 4 concedes only snapshots the crate does not carry, so this lands outside it.
- BELIEVED: P1.2's step 9 would refuse such metadata, but that does not make step 8 right alone.
- The fix is small: take carried snapshots by `backend_name` equal to the Job's device `name`.

**D4 (prose): sentences in the tree that are false as written.**
- `qro/p1_graph.py` says an Index "holds no state a caller can change". MEASURED: after an entity is edited, `job_of` still answers from the stale `_holders` cache, and `by_id` is a public dict the caller can reassign.
- `p1_calibration.link_for` says `carried` holds "every snapshot the crate holds of the job's device". The step passes the entity-keyed subset (D3).
- The `p1_steps` docstring says steps refuse "by its own name". Step 5 also raises `step-unbuilt` and `raw-form`, and step 8 raises `step-unbuilt`.
- The `_visit` docstring says MemoryError is the host's (see D2).

## Notes

**Needs the lead's ruling.**
- The 14:16 "correction" holds `startTime` and `endTime` to the raw span only under `history-*` links. MEASURED (`cases1.py` B1): a Job linked `unknown`, with a raw span, and times years off, is accepted.
  - The approved design says in one paragraph that the step requires the times to equal the span whenever the Job has a raw result, and in its table that `unknown`/`unexposed` compare nothing.
  - The brief says to escalate design changes, and this was not escalated. The terms are ANCHORED, not CHECKED. I judge this a ruling, not a defect.

**Stated limits, each tested.**
- True as stated: 1, 2, 3, 5, 6, 7, 8, 10, 14, 15, 16, 18, 19.
- Limit 11 is under-stated. MEASURED (`cases1.py` A2; real bytes in `real_faults.py` #8): with every IBM Pub `none`, a mirrored known-answer circuit and `lsb-first` Decodes pass steps 1 to 8. Step 5 then reads its expected set from an unbound record.
  - Atlas Pubs have no commitment, so dropping or relabelling a law Pub's `qro:role` skips step 5's layout accounting (`cases2.py`, accepted).
  - Step 9 is the stated cover for both, so these are inside the limit. The limit should name the step 5 consequence.
- Limit 9 as worded is false. Steps 4 and 5 open each Pub's record file; only its counts and digest go unread.
- Limit 13's "(above 2^53)" is loose: integers above 2^53 that binary64 holds exactly are accepted.
- Limit 17's MemoryError sentence is false for a crate-caused one (D2).

**Test reach where the code is right.** My 121 hand mutants (`mymut.py` with `mymut_spec.py` and `mymut_spec2.py`, none of them P1.1's AST operators): 109 killed, 12 survived. Seven of the survivors are equivalent or controls. The other five are test gaps.
- A constant verdict-cache key in step 5 passes all 945 tests, because no crate has two known-answer Pubs. MEASURED (`k2_demo.py`): with a second bundle's known-answer data all zero, the shipped code refuses and the mutant accepts. Real crates have 31 known answers.
- Two job lines that both lack `bundle_sha256` are counted as one bundle by a mutant.
- `num_bits` above 16 is accepted by a mutant.
- Non-ASCII snapshot text is not covered.
- `files_by_sha256` over non-File entities matters only to non-checker callers.

**Other.**
- The in-step safety net turns a bug in P1's own step into a REFUSED verdict. FORMAT.md item 16 says a crash in a parcel's step is exit 3, never a verdict. This is disclosed and tested.
- No step compares `qro:jobId` with the line's or the record's `job_id`. `qro:jobId` is REPORTED, so swapped job ids are accepted (`cases1.py` C2).
- The IBM branch of `p1_decode.account` can never refuse.
- The ledger says "338 functions", and I count 336.

## What I did not do

- I did not run any of P1.2's parts, `p1-crates`, `docs/P1.md`, or step 9 against a real generator.
- I did not re-run P1.1's 826 automatic mutants.
- I did not demonstrate D2 by actually exhausting machine memory. I used a 1 GiB per-process job-object limit.
- I tested only Windows and Python 3.12.9.
- I did not fuzz metadata past the strict reader, which refuses first.
- I did not read the other worktrees, the live ledger or the other verifiers' directories. I did not open `~/.quantum-film`, any `.atlas` directory or credentials. I made no network connection and used no key.
- Early harness runs wrote temporary crates under the system temp directory before I moved them to `check\tmp`. I deleted those 23 directories and moved a stray `base\` under `check\`.
