# P1.1, round 3: NOT READY

I found no crate that the steps get wrong, and no reader escape. NOT READY rests on the full bar, which counts false stated limits and gates that pass a fault they claim to catch. I found one false limit, two gates, and two small false sentences. Where noted, one of the false sentences also traces to P0's code, which is not P1.1's to fix.

My scripts and logs are in `SCRATCH\verifier-P11-r3\check\s\` and `check\*.log`.

## The freeze, the base, the runner

- MEASURED (`sha256sum -c` over `tree\`): 281 files, 0 mismatches. SHA256SUMS.txt starts `074e6df0fd6de449`, and the six ledger and report hashes match the brief's.
- MEASURED (`git archive 20d40e6`, 260 files, compared by hash): the packet adds exactly P1.1's 21 files and changes none. Scope 8 is clean.
- MEASURED (hashes only, no git in the worktree): P1.1's worktree equals the packet.
- MEASURED (`verify/run.sh` in a `git init` copy, `QRO_MOTH_ROOT` set): 16 stages passed, 6 skipped by name, 2 failed. The two failures (`docs`, `tool-tests`) are Windows path-length failures from redirecting TMP under `check\`.
  - The scratch root is 148 characters deep, so git objects in pytest's temp directories exceed 260 characters.
  - The base commit's tree fails the same way. `tool-tests` gives the same 40 failures on the base and on the packet.
  - `docs` passes with a shorter TMP (32 s).
  - `tool-tests` cannot pass inside `check\`, because P0's tests hide the user's long-path git setting. I rely on the lead's passing run of the same files for that stage.
- MEASURED (`verify/run.sh --only p1`): 1,113 passed in 43.5 s. Also 1,113 passed in reverse and in a shuffled order.

## Defects

**D1. Prose: limit 17 and two docstrings state costs that files exceed.**

- The sentences are limit 17 (ledger, 15:09:12Z) and `qro/p1_steps.py` lines 25-26 and 108-109. They say "up to 25 times" for a JSON file, "twice" an array's inflated size, and "18 times" a circuit.
- JSON. A valid crate whose job line carries a 3 MB `pad` of nested one-element arrays is accepted through step 8.
  - MEASURED (`s/costs_step.py 3000000 arrays`): step 4's peak is 137.9 MB, which is 46.0 times the line.
  - MEASURED (`s/peakmem.py`): the command line peaks at 157 MB, against 14 MB for the same crate without the pad.
  - Nested single-key objects cost 38.8 times. Even the flat shape the sentence names costs 26.2 times in step 4.
- Array. An incompressible IBM array costs 6.67 times its inflated size, and 5.0 times its file (`s/costs_ibm.py work 33000000`).
  - At the reader's cap that is 440 MB from an 88 MB file. The compressible case that was measured gives 132 MB (2.01 times).
- Circuit. Two-character lines cost 21.7 times its size (`s/costs_circuit.py`). The blank-line figure is 18.7 times when the read bytes are counted.
- Exit code. Limit 17 says a host fails with exit 3 when it cannot parse the crate's largest file. That is false when the largest file is a raw result (`s/memerr.py`).
  - Step 3 reads it first. `checker.counts` is P0's code, and it turns any `Exception`, MemoryError included, into `REFUSED raw-form`.
  - For a raw result of 24 MB inflated and 30 KB on disk, the crate is accepted through step 8 at 400 MB. It exits 3 at 60 MB. It exits 1 `REFUSED raw-form ... failed: MemoryError` at 45 MB and at 30 MB.
  - A job line as the largest file does give exit 3 at 60 and 100 MB, as stated.
  - This part is not P1.1's file and P1.1 cannot fix it. The sentence must say so, or P0's catch-all must narrow.

**D2. Gate: the memory gates miss most of the class that round 2's D1 named.**

- The docstring of `test_step_8_holds_nothing_of_a_snapshot_by_the_time_it_reads_the_first_job` (`test_p1_memory.py` line 210) says "Whatever part of a document a step kept (the dict, a list in it, the text it came from) ... would show". The test pads only `qubits`.
- MEASURED (`s/mut3.py`, mutants 1 to 3): step 8 keeping each snapshot's `gates`, `general` or `general_qlists` passes all 1,113 tests. I confirmed the `gates` case by hand in a fresh copy.
- MEASURED (`s/snap_keep.py`, the 7 real snapshots, 7.8 MB): the table gives peak, then bytes held when the last snapshot is read.

| What step 8 keeps of each snapshot | Peak | Held |
|---|---|---|
| nothing (shipped) | 10.4 MB | 1.1 MB |
| the whole document (round 2's D1) | 31.5 MB | 22.3 MB |
| `gates` | 27.8 MB | 18.6 MB |
| `qubits` (caught by the test) | 12.6 MB | 3.4 MB |

- In a real snapshot `gates` is 654,685 of about 820,000 bytes, and `qubits` is 99,439.
- Also outside the gates (mutants 5, 7, 8, 9, all survive): step 4 keeping each Pub's parsed record, step 5 keeping a known answer's record, step 5 keeping the circuit's bytes, and every step keeping the bytes of each raw result.
- The shipped code keeps none of these. MEASURED (`s/sumfiles.py`): peaks on 1 and on 8 jobs match for padded records, lines, raw wrappers and snapshots. So these are test reach where the code is right.

**D3. Gate: step 5's registration is tested only with Jobs present.**

- `test_each_step_runs_for_a_crate_that_holds_only_the_entities_of_its_own_type` keeps the Jobs in its Decode crate.
- MEASURED (mutant 12, confirmed by hand with 1,113 passed): a step-5 guard on `qro:Job` instead of `qro:Decode` passes every test.
- MEASURED (`s/guard5.py`): a crate of Decodes with no Job is refused `known-answer` by the shipped step and would be accepted under the mutant.
- This is round 2's D2 on the next step. Steps 4 and 8 are held from both sides (mutants 11, 13 and 14 are killed).

**D4. Prose: two small sentences are false as written.**

- `qro/p1_graph.py` line 8 says "a type that is not a string" is a `GraphError` at construction. MEASURED (`s/index_types.py`): an `@type` of 5, 1.5, null, true or an object is taken as no type. Only a list holding a non-string raises.
- `test_nothing_compares_one_job_with_another...` (`test_p1_step4.py` line 117, and limit 22) says no Decode is held to another job. Step 5 holds a Decode to its known answer's job: the device by `@id`, the bundle, the rule and the order.

## What held

- **Real records** (`s/real_check_r1copy.py`, `s/real_ibm_crate.py faults`, `s/real_atlas_r2.py`, `s/seam_r2.py`): all reproduce.
  - 68 of 68 echoes and counts; 31 of 31 known answers `msb-first` and 0 `lsb-first`; the 12 digests as 3, 2 and 1.
  - Links 57 and 8, with 1 job whose running-time snapshot differs.
  - The vector's worst |z| is 2.154 under `atlas-register` and 172.96 under `circuit-order`. The six Atlas results give 1,995, 2,006, 1,997, 2,026, 2,020 and 2,027 layouts.
  - A hand-assembled 65-job, 68-Pub crate is accepted in 6.3 s. Four planted faults get the expected names.
  - `pub_counts` equals Quantum-Film's counts for 68 of 68 Pubs, on file-read metadata and on bare entities.
- **The integer bound** (scope 1, D5). No real record is near it: 12,846 JSON files hold 10,737,418,240 at most, and 24,576 in the files the steps read (`s/ints_scan.py`).
  - 27 numerals in 6 places in the snapshot, IBM and Atlas readers gave 162 refusals by the readers' own error class and no other class (`s/numerals.py`).
  - The 19-digit shortcut is exact for numerals past 2^63 - 1, on either side of zero, including unconverted 4,300-digit numerals.
  - The step-5 sentence holds as restated (`s/hostile_names.py`).
- **Steps with crates I built.**
  - Jobs of 1 to 10 PUBs are accepted, an 11th is refused as limit 10 says, and all 15 pairwise echo swaps are refused (`s/manypubs.py`).
  - `copy_job` crates: copies are accepted, and each tampering is refused by the expected name (`s/copies.py`).
- **Digest.** A digest written here from the recipe agrees with `values_digest` on 9,000 random snapshots, and moving every date never moves it (`s/digest_diff.py`).
- **Seam.** 17,759 single-value mutations of the metadata gave no exception beyond the documented ones (`s/fuzz_seam.py`).
- **Fixture and registration** (`s/fixture_reg.py`, `s/cost0.py`).
  - The fixture is accepted with P1 loaded, with the six modules set to None, and with a raising finder.
  - Only steps 4, 5 and 8 and the three raw forms register.
  - The extra cost is 0.12 ms on 6.38 ms.
- **Mutants.** My 52: 39 killed, 13 survived.
  - Three of the survivors are equivalent by verdict: 25 in batch 1 (`s/mut3_spec.py`), and 19 and 20 in batch 2 (`s/mut3b_spec.py`).
  - The other ten are test gaps, covered in D2, D3 and the notes below.
  - The second verifier's 83, re-run: 81 killed, 2 no longer apply, 0 survive.

## Notes

- **Ledger sentence, not in the tree.** "A hostile file can no longer put megabytes into the one REFUSED line" is false in general (`s/longline.py`).
  - Six sources each give a line of 2.9 to 3.0 MB: a 3 MB `backend` or `program` in a record, a duplicate key, a setting label, 200,000 extra keys on the wrapper, and an extra snapshot key.
  - Only the echo and the numeral are capped. The lead's reading 3 was taken on that sentence.
- **Test reach, code right.**
  - Mutant 18: the older of two named snapshots told by newest value instead of stamp survives.
  - Batch 2, mutant 9: a time fraction of up to nine digits survives, so `.0000001Z` would be read as 1 microsecond.
  - The shipped code is right on both.
- **Underflow.** `1e-999` is read as 0.0 in every reader. "No float is read past binary64" holds for overflow only.
- **A no-op in the second verifier's script.** Its `cli_hostile.py` case "snapshot with a 1e999" edits nothing, because the file holds 101.5 and not 100.5. My `numerals.py` covers it.
- **Stale figures in CLAUDE.md (the lead's file).** The quick ~70 s and full ~125 s figures predate the p1 stage, which takes 35 to 45 s here. BELIEVED.
- **The cap.** If the lead counts this as the third NOT READY, CLAUDE.md item 6 applies to the next round. None of D1 to D4 is a defect in what P1.1's code does.

## What I did not do

- I ran none of P1.2's parts: no `p1-crates`, no step 9 against a real generator, no `docs/P1.md`.
- I did not run `tool-tests` to a pass (see above), and I did not re-run P1.1's own 257 hand and 873 automatic mutants.
- I did not fuzz the readers at scale myself. I relied on the earlier 1.68 million and 400,000 mutants, and ran the batteries listed above.
- I did not exhaust machine memory. I used job-object limits of 30 to 400 MB.
- I tested only Windows 11 and Python 3.12.9.
- I read neither P0.5's packet nor any other verifier's directory, and I used no key, no network and no credential file.
- I wrote only under `check\`, with these slips:
  - An early `ls` of the real records printed five full IBM job ids to my console. None was saved or appears here.
  - One stray empty file, `/tmp/null_x` in the system temp, which I deleted.
  - One refused attempt to write `/tmp_wt_list.txt`, which wrote nothing.
