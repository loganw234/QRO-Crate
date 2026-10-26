# P1.1, round 4: READY

I found no defect in what the shipped code does, and no gate, stage or registry defect. This round rests on the relaxed bar, so what I list below is notes.

I tried to make the steps wrong in five ways:
- a second, independent decision procedure for steps 4, 5 and 8;
- the real records;
- 75,802 mutated crates;
- hostile files through the command line;
- Python 3.13.

None of them produced a wrong verdict, a crash or a wrong exit code.

SCRATCH is the root named in the brief. My scripts and logs are in `SCRATCH\verifier-P11-r4\check\s\` and `check\*.log`. Every claim is MEASURED unless marked READ or BELIEVED.

## Freeze, base, runner

- **The freeze holds.** The brief's SHA-256 (`fa796edd7a764b80`) and the hashes of the packet's documents (`a74c3369…`, `18ec05d1…`, `7764e0d2…`, `2bbea75f…`, `1b752e36…`, `bab9c1b2…`, `2c28f8e4…`, `fd6805d9…`) all match. `sha256sum -c` over `tree\` found 281 files and 0 mismatches. It gave the same result again at the end.
- **P1.1's worktree equals the packet.** All 21 files match by hash, and the worktree is at 20d40e6.
- **Whose files.** `git archive 20d40e6` gives 260 files. The packet adds exactly 21 (7 in `qro/`, 14 in `tests/p1/`) and changes none. All 21 are LF with one final LF, with no tabs and no BOM. The seven modules import only the standard library and `qro`.
- **The runner passed.** In a `git init` copy, `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` gave exit 0, 18 passed, 0 failed, and 6 skipped by name (p2, p4, p1-crates, p2-crates, profile, p4-shacl). The p1 stage took 40 s, and the stages sum to about 226 s.
- **Python 3.13.5.** The 1,169 tests pass (38 s). I used pytest's pure-Python packages copied from the 3.12 site-packages, with nothing downloaded.
- **Line coverage.** Every executable line of the seven modules runs under the 1,169 tests. I measured it with a `sys.monitoring` collector of my own.

## The steps' verdicts

I wrote `audit.py` as a full decision procedure for steps 4, 5 and 8, from the design text (ledger-P1 items 3 to 5 and the build's clarifications). It imports nothing of `qro.p1_*`. I compared it with the steps in both directions.

- **Random mutations (`diff_steps.py`).** 75,802 trials on the builder's IBM, Atlas, many-jobs and `copy_job` crates:
  - 24,337 were accepted by both and 20,154 refused by both;
  - the other 31,311 were skipped because step 1 or 3 refuses them first;
  - 0 disagreements either way.
- **Link rule (`diff_links.py`).** 11,175 crates with random snapshot stamps and newest dates, and first shots at t-1µs, t and t+1µs. All four link words were accepted in many crates (4,843 accepted, 6,332 refused). 0 disagreements.
- **Net-exposing fuzz (`net_fuzz.py`).** `_visit`'s net turns every ordinary exception into a REFUSED line, so a plain accept-or-refuse fuzzer cannot see a masked bug. I hooked `_failed` and ran 142,038 trials. The only exception that was not one of the helpers' own was `UnicodeEncodeError` at `p1_commit.py:29`, from a lone surrogate in `stock`, `route` or `salt`. It is refused `commitment` with a generic detail, which is the right verdict.
- **Honest variants (`variants.py`).** Non-ASCII, astral, combining and punctuated names, and raw results with 2 to 4 spans in any order, were accepted by the steps, the auditor and the whole checker. Scale is linear: 800 jobs take 0.2 s per step.
- **The 65-job real crate (`real_faults.py`, built with round 3's mini adapter).** The honest crate is accepted in 8 s. I planted nine faults:

  | Fault | Refusal |
  |---|---|
  | a raw result swapped for another job's | `commitment` |
  | a Decode naming another bundle's known answer | `known-answer` |
  | one snapshot value changed | `calibration-link` |
  | a decoy snapshot that makes a gap | `calibration-link` |
  | a coherence job's PUB results swapped | `commitment` |
  | the span removed | `calibration-link` |
  | the span moved | `calibration-link` |
  | a Job without its Pub | `commitment` |
  | all copies of a QPY or circuit altered | `commitment` |

  I show only the first fault of each kind. The seven items in the table cover all nine runs, and the QPY-and-circuit row is two of them.

## Real records (scope 5, 2)

- **The design's measurements reproduce** (`real_battery.py`), with my independent oracle agreeing at every point, on Python 3.12.9 and 3.13.5:
  - 65 jobs and 68 PUBs: the commitment recomputed, IBM's echo, the job line and the record agree for all 68; rows and counts match;
  - 31 of 31 known answers hold `msb-first` and 0 of 31 hold `lsb-first`;
  - the 12 snapshots give 1, 3 and 2 digests for fez, kingston and marrakesh;
  - the links are 57 `history-at-first-shot` and 8 `history-in-gap`;
  - the six Atlas results give 1,995, 2,006, 1,997, 2,026, 2,020 and 2,027 layouts;
  - the vector's worst |z| is 2.154 under `atlas-register` and 172.960 under `circuit-order`.
- **The integer bound refuses nothing real** (`ints_scan.py`). Across 12,851 real JSON files, the largest integer in a file a reader reads is 24,576 in raw and PUB files, 2,720 in snapshots and 4,096 in Atlas files. None is past 2^63 - 1. No reader refuses any real raw, snapshot, job line or PUB record.
- **The bound holds wherever a JSON integer can sit** (`bound_everywhere.py`). I put nine out-of-bound numerals (19, 20, 25 and 5,000 digits, both signs) at every position of a valid IBM result (48 positions), Atlas result (41), vector (63) and snapshot (68), and added each as a new key to every object. Every case is refused with "integer past", by the reader's own error class. The bound itself is never the reason for a refusal.
- **The 24-digit shortcut** misreads nothing. The 19-digit cut is exact for numerals past the bound, and a numeral is quoted to 24 digits. READ and run in the same script.

## The readers (scope 4)

- **IBM array reader against numpy's own `.npy` reader** (`diff_array.py`), on about 57,000 valid and mutated blobs:
  - P1 never accepts what numpy refuses;
  - when both accept, rows and bytes are always equal;
  - P1 is stricter only on header spellings IBM does not write and on bytes after the zlib stream.
- **Circuit reader and verdict** (`diff_circuit.py`):
  - 40,000 circuits agree with my reader, end to end;
  - 60,000 count tables agree with my verdict.
  - The empty and the full x-set are refused in the verdict, not in `expected_set`.
- **Hostile crates through the command line** (`cli_hostile.py`, `cli_deep.py`): 31 cases plus 18 option nestings from 500 to 3,100 deep. All gave exit 1 and one REFUSED line by a step's name. None gave exit 3 or a traceback. Python 3.13 gives the same verdicts and differs only in how deep the parser reads.
- **Exit sentence of limit 17** (`memerr.py`). With a 100 MB memory cap, a padded job line gives exit 3 (`FAILED … MemoryError`). With a 400 MB cap, the same crate is accepted through step 8. When a raw result is the largest file, caps of 45 MB and 30 MB give `REFUSED raw-form … MemoryError` with exit 1. That is step 3, which is P0's, and limit 17 says so.

## Fixture, registration and seam

- **Fixture and registration** (`fixture_reg.py`):
  - P0's fixture is accepted (`ACCEPTED 21fafec5…`) through the command line with P1 loaded.
  - It gives the identical line with every `qro.p1_*` module made unimportable.
  - Without `--fixtures` it is refused `step-unbuilt`, as designed.
  - P1 registers only steps 4, 5 and 8 and the three raw forms, with no counts and no generators.
  - `checker.load()` imports no `qro.p1_*` module.
  - The fixture check costs 5.81 ms with P1 and 5.82 ms without.
- **The seam P2 reads** (`seam.py`, `seam_atlas.py`):
  - `pub_counts` equals my oracle for the IBM Pubs on file-read metadata and on three bare-entity variants (reversed, shuffled, no root or descriptor);
  - the same holds for the Atlas Pub;
  - the `Index` relations agree on all of them;
  - a matrix of 265 places × 19 values (unhashables among them) × 3 Pubs gave only `GraphError`, `DecodeError` or a result, and nothing escaped.

## Round 2 and 3 fixes, again (scope 1, 2)

- **Mutants of the earlier verifiers**, run unmodified through their `mut3.py` runner on the frozen tree:
  - round 3's 52 mutants: 52 killed;
  - round 2's 83: 81 killed, and the 2 that no longer apply are the two P1.1 reported.
  - Together they include the snapshot-document keepers (round 2 D1) and the Job-only guard on step 8 (D2).
- **My own mutants** (`mine_spec.py`, `mine2_spec.py`): 13 of them, 12 killed. The 4 memory-class ones are killed by the identity and size gates. Mutant 5 survives (note 1).
- **D3 and limit 17's costs** (`sumfiles.py`, `costs_step.py`, `cost_snap.py`):
  - step peaks on 1 job and 8 jobs have a ratio of 1.00 to 1.32 for every padded kind of file (record, line, raw wrapper, snapshot), so memory is the largest file and not the sum;
  - a 3 MB padded job line costs 46.0 times its size as nested arrays and 38.8 times as nested objects;
  - a snapshot costs 144.8 times its size for one long list and 34.2 times for many short ones.
  - The stated 46, 39, 147 and 35 hold within noise.
- **D5 and D4.**
  - The step-5 sentence holds (`hostile_names.py`): a hostile raw result is `commitment`, `raw-form` and `calibration-link` at steps 4, 5 and 8.
  - Limit 11 concedes the whole behaviour: a `none` Pub binds nothing.
  - Limit 13 holds at 2^53+1 and its neighbours, and at the 2^63 - 1 and 2^63 edges (`lim13.py`).
  - `p1_graph`'s `@type` sentence and limit 22's Decode sentence hold.

## Notes

None of these blocks, because none is a defect in what the code does.

1. **Test reach, code right.** My mutant 5 (`ordered = sorted(refs)` in step 8, telling the older of two named snapshots by id instead of by stamp) survives all 1,169 tests. Every snapshot id in the tests is named by its stamp, so id order equals stamp order.
   - The shipped code is right. In `idorder.py`, an honest `history-in-gap` crate whose two ids sort against their stamps is accepted by the steps, by the auditor and by the whole checker.
   - A step that sorted by id would refuse that honest crate.
2. **Design reading, other.** Step 4 finds the committed circuit and ISA files by digest among all files of the crate. The real crate holds 31 identical copies of each logical circuit and 3 to 11 copies of each QPY file (`twin_copies.py`).
   - Flipping one bit in the one bundle's QPY (the file the job actually ran), or mirroring its circuit, is accepted because another copy keeps the digest. With every copy altered, the refusal is `commitment`.
   - This is the design as written, and step 9 (P1.2) is the cover. It is not in any stated limit, and one sentence in limit 1 or `qpy-only` would state it.
3. **Prose in the tree.** `qro/p1_steps.py` line 27 sends the reader to "the P1.md entry that answers the verifier's round 3", which has the cost table. That is a ledger file outside the repository, so the table is not in the tree.
4. **Prose in the ledger only.** Limit 10 says "a job of ten PUBs needs a new rule". The code accepts ten PUBs (indices 0 to 9) and refuses the eleventh. `p1_graph.py` says "one decimal digit", which is right.
5. **The net, other.** A lone surrogate in `stock`, `route` or `salt` is refused `commitment` as "cannot be checked: UnicodeEncodeError…". The verdict is right and the detail is generic.
6. **Step 3, P0's, already ruled.** A host that cannot hold a raw result's parse gets exit 1 `REFUSED raw-form … MemoryError`, not exit 3 (P0.7 weighs it).
7. **Time, other.** A crate of 91,096 bytes on disk with one IBM result at the reader's cap (33,554,304 rows) takes 6.1 s in step 5 and 6.7 s through the command line (`cap_time.py`). Step 5 tallies the same rows for the verdict and again for every PUB. The cost is bounded per result and linear in the number of results. No limit states it, and I do not call it a hang.
8. **Python 3.13, informational.** The verdicts are identical. The parser reads deeper there (a 2,990-deep `options` is read on 3.13 and refused on 3.12), and the refusal is by name either way.
9. **Refusal details quoting hostile text whole** (nine places) stay as ruled.
10. **CLAUDE.md's timing figures are stale.** This is the lead's file, and the previous round noted it.

## What I did not do

- I ran none of P1.2's parts: no `p1-crates`, no step 9, no `docs/P1.md`.
- I did not run P1.1's tests on P0.6's second packet, because its directory is another verifier's. I rely on the lead's note.
- I did not re-run P1.1's own 275 hand and 873 automatic mutants. I ran the earlier verifiers' 135 and my 13.
- I did not fuzz the readers at P1.1's scale of 1.7 million mutants.
- I used job-object memory caps of 30 to 400 MB, not real exhaustion.
- I tested Windows 11 with Python 3.12.9 and 3.13.5 only, not Linux, macOS or 3.14.
- My auditor and the steps both come from the same design text. A shared misreading would not show, but the real data supports the bit-order and link-rule readings.

## Slips

- I wrote crates and workspaces to `%TEMP%\v4p11`, for path length, instead of under `check\`. I removed them, and they held no key or secret. The tests' own pytest base directories are in the system temp, as the project's tests put them.
- I ran read-only git commands (`status`, `log`, `rev-parse`, `archive`) in P1.1's worktree, the real repository and moth-quantum. They may have refreshed an index cache.
- A `find` over moth-quantum listed file names under its `.claude\worktrees\`. I read none of them.
- `ints_scan.py` read the integers of every JSON file under moth-quantum's `docs\records` (the `atlas\` probe responses among them), and printed one file name.
- I masked every IBM job id I printed.
