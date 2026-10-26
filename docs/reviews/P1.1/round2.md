# P1.1, round 2: NOT READY

I found no crate that P1.1's steps get wrong. The fixes for D1, D2 and D3 and both of the lead's rulings hold, on the real records and on about 8,000 random step-8 crates, 15,000 relation rewirings and 400,000 reader mutations. NOT READY rests on the full bar, which counts a test that passes a fault it names and a false sentence in the tree. I found two such tests and three such false sentences. One of the sentences is false because step 4 keeps every parsed job line, so that one is about what the code does as well as about prose.

My scripts and logs are in `SCRATCH\verifier-P11-r2\check\s\` and `check\*.log`.

## The freeze, the base, the runner

- MEASURED (`sha256sum -c` over `tree\`): 281 files, 0 mismatches. SHA256SUMS.txt starts `2c8a5755a1f02589`, and the other six hashes match the brief's prefixes.
- MEASURED (hash of `git ls-files` plus untracked non-ignored files): P1.1's worktree equals the packet on all 281 files.
- MEASURED (`git archive 20d40e6`, 260 files): the packet adds exactly 21 files, the 7 `qro/` modules and 14 files in `tests/p1/`, and changes none. Item 8 is clean.
- MEASURED (a `git init` copy in `check\work`, `QRO_MOTH_ROOT=<repos>/moth-quantum`, Git Bash by full path, `verify/run.sh`): exit 0, passed 18, failed 0, skipped 6 by name (p2, p4, p1-crates, p2-crates, profile, p4-shacl). The p1 stage took 31 s.
- MEASURED (driver with node ids): the 1,018 p1 tests also pass in reverse order and in a shuffled order.

## Defects

**D1. Gate: `test_step_8_keeps_no_snapshot_document` passes the fault it names.** This is the snapshot half of D2.
- MEASURED (`s/mut2.py`, mutant 1; then `s/full_mutant_stage.py`): replace `{}` with `snap.doc` in `light = p1_forms.Snapshot(...)`, `p1_steps._snapshot8` line 356. All 1,018 tests pass.
- MEASURED (`s/survivors.py`, the 12 real snapshots, 11.5 MB): step 8's tracemalloc peak is 10.4 MB shipped and 49.2 MB with the mutant.
- READ: `tests/p1/test_p1_memory.py` lines 73-88 puts a weakref on the `Snapshot` that `parse_snapshot` returns. The mutant drops that object and keeps its dict. The tracemalloc ratio test uses a crate of one snapshot, so nothing else guards this.
- P1.1's own mutant for this fix was `light = snap`, which is killed. Mine is a different shape.
- MEASURED (`s/probe_g1_g2.py`, `s/run_probe.py`): a scratch test that watches the documents, using a dict subclass with a weakref, passes on the shipped code and fails on the mutant.

**D2. Gate: `test_each_step_runs_for_a_crate_that_holds_only_the_entities_of_its_own_type` covers step 8 only from the Job side.**
- MEASURED (mutant 43): `register_p1.step8` guarded by `_holds(md, "qro:Job")` alone passes all 1,018 tests.
- MEASURED (`s/survivors.py`): a crate of snapshots with a false `qro:valuesDigest` and a plain CreateAction instead of a Job is refused by shipped `register_p1.step8` (`calibration-link`) and accepted under the mutant.
- READ: the test at `tests/p1/test_p1_register.py` lines 84-107 says step 8 visits Jobs as well as Snapshots, but tests only "jobs, no snapshots". Steps 4 and 5 have their reverse cases; step 8 does not.
- A scratch test for the reverse case kills the mutant.

**D3. Code (memory) and prose: the MemoryError sentences are false, because step 4 keeps every parsed job line.**
- READ: `_visit`'s docstring (`p1_steps.py` lines 93-98) says a MemoryError "needs one result at the reader's cap on a host that cannot hold it". Ledger limit 17 says the same. Step 4 holds `lines` (line 119; filled at lines 203-206) for the whole step.
- MEASURED (`s/biglines.py` and `peakmem.py python -B -m qro check`): 10 valid jobs with 2.1 MB job lines each (a 21 MB crate) peak at 507 MB. The same crate with ordinary lines peaks at 15 MB.
- MEASURED (`s/lines_cause.py`): step 4's peak is 455.6 MB with the cache and 49.4 MB with that one cache removed. Step 5's 94.5 MB is transient.
- The ratio is about 22 times the line files' size, summed over all jobs. Real lines are 415 to 491 bytes (MEASURED, `stat` on 65 files), so real crates are not touched.
- BELIEVED, from the ratio: a hostile crate smaller than the real IBM crate (52.5 MB, READ in the design) can cost about 1 GB, and a smaller host fails with exit 3.
- This is D2's class on the job line instead of the raw result, at a ratio of about 22 instead of 1,000. The lead can have the cache keep only `commitments`, or rule it a stated limit and restate both sentences. Either way the two sentences must change.

**D4. Prose: limit 11 is stated by the instance the first verifier found, not by the behaviour.**
- MEASURED (`s/faults1.py`, whole checker with a pass-through step 9): the known-answer Pub alone is `none`, its record is resealed to name a mirrored circuit file, and the three Decodes declare `lsb-first`. It is ACCEPTED. The law and coherence Pubs stay committed and verified.
- The restated limit says "with every IBM Pub `none`". The behaviour conceded is that the bit order rests on whatever binds the known-answer Pub's record, and a `none` known-answer Pub binds nothing.

**D5. Prose: two more sentences in the tree are false as written.**
- READ and MEASURED (`s/hostile_names.py`): `p1_steps` lines 12-16 say a hostile file is refused "by the step's own name". A hostile raw handed to step 5 gives `raw-form`. Through the command line step 3 refuses it first, also as `raw-form`. This is the word the first verifier's D4 pointed at, so D4 is only partly fixed.
- MEASURED (`s/bigint.py`): `p1_forms` lines 17-18 and `load_json`'s docstring say "no number past binary64". That holds for floats only. An Atlas result with counts and shots of 10^400 is read. With `qro:shots` omitted, the whole checker accepts it. With 4096 stated it is `count-unpaid`.

## What held

- **D1 (Atlas `fetched_at`).**
  - MEASURED (`s/real_atlas_r2.py`): the six real law results parse, with 1,995, 2,006, 1,997, 2,026, 2,020 and 2,027 layouts. The vector gives worst |z| 2.154 under `atlas-register` and 172.96 under `circuit-order`.
  - MEASURED (`s/real_atlas_crate.py`): a crate of the six results plus the vector is accepted. The wrong order is `known-answer`.
  - MEASURED (`s/d1_edges.py`): thirteen odd `fetched_at` values are refused. Only `...22Z` and `...22.123Z` style times are accepted. The vector and any other wrapper key stay refused.
- **D2 (raw results).**
  - MEASURED (`s/bigvalid.py`, `peakmem.py`): valid crates of 1, 6 and 60 jobs, each raw 20 MB inflated, peak at 54, 53 and 53 MB.
  - MEASURED: 4 jobs at the reader's cap (33.5 million rows) peak at 143 MB and pass under a 512 MB process limit.
  - MEASURED (`s/negctl.py`): with round-1 `p1_forms.py` put back under the new tests, 31 tests fail. With round-1 `p1_steps.py`, 16 fail (7 memory, 1 step 5, 8 step 8).
- **D3 and the times ruling.**
  - MEASURED (`s/diff_step8.py`, seeds 1 to 3): 8,300 random crates, 40% with a second device entity of one name, against an oracle I wrote from the design's text. 0 disagreements.
  - MEASURED (`s/real_ibm_crate.py faults`): the real gap job claiming `history-at-first-shot` is refused, also with the gap snapshot on a second device entity.
  - MEASURED: a start time one microsecond off is refused. The first verifier's `cases1/2/3.py` give the ledger's answers.
- **Steps' verdicts.**
  - MEASURED (`s/real_ibm_crate.py`): a 65-job, 68-Pub crate assembled by hand from the real files, with link words computed by my own rule, is accepted in 5.8 s. 57 links are `history-at-first-shot` and 8 are `history-in-gap`.
  - MEASURED (`s/real_check_r1copy.py`): 68 of 68 echoes equal the recomputed commitment. 31 of 31 known answers hold `msb-first` and none holds `lsb-first`. The 12 snapshots give 6 digests grouped as the study has them.
  - MEASURED (`s/diff_verdict.py`): the decode, verdict and Atlas z-test functions agree with my string and Fraction oracles on about 26,000 random inputs.
  - MEASURED (`s/fuzz_rewire.py`, 15,000 trials, 1,986 accepted): every accepted crate binds each Pub to what the honest crate binds it to. The one exception names a different valid snapshot as C of a `history-in-gap`, which limit 4 concedes.
  - MEASURED (`s/fuzz_fields.py`): no CHECKED term of P1's survives a deletion or a swap.
- **Limits.** 9, 13, 20 and 21 are true as stated. Limit 9 was mapped by `s/fuzz_paths.py`: the steps ignore `code`, `counts`, `digest`, `law`, `source.commitment`, `fixed_at`, `job_id` and `submitted_at` of a record, and `backend`, `kind`, `program`, `route`, `stock`, `format`, `job_id` and `submitted_at` of a line. Limit 13 was run at 2^53+1 and its neighbours (`s/lim13.py`).
- **Readers.** MEASURED (`s/fuzz_real_readers.py`, 240 s each): mutations of the real files gave 374,871 IBM, 23,455 Atlas and 8,476 snapshot trials, with 0 escapes, and what parsed also decoded. Eleven hostile crates through the command line (`s/cli_hostile.py`) all gave exit 1 and one REFUSED line.
- **P0's fixture and registration.** MEASURED (`s/fixture_reg.py`): the fixture is accepted by the command line with P1 loaded, with the six `qro.p1_*` modules set to None, and with a raising finder, all giving the same digest. Blocking `register_p1` itself gives exit 3, as P0 intends. Only steps 4, 5 and 8 and the three raw forms register, and `load()` imports no `qro.p1_*` module. The whole check costs 6.788 ms with P1 loaded and 6.818 ms without (`s/cost0.py`).
- **The seam.** MEASURED (`s/seam_r2.py`): `pub_counts` equals Quantum-Film's record counts for all 68 Pubs, on file-read metadata and on bare shuffled entities. P2's design expects both (READ, ledger-P2.md "Found 2").
- **The design changes.** The six of 11:36:24Z and the five of 14:16:08Z each fill a silence or refuse what the reader already refuses. I built no crate the design accepts that they refuse.
- **Mutation.**
  - Mine: 83 hand mutants (`s/mut2_spec.py`, `mut2b_spec.py`), 76 killed. The survivors are mutants 1 and 43 (D1, D2), 14, 26, 29, 42 (notes below) and 15, which is equivalent.
  - P1.1's 212 hand mutants, re-run: 211 killed, 1 survived (the documented equivalent).
  - P1.1's automatic mutants of `p1_steps.py`: 268 of 268 killed.
  - The first verifier's 121: 104 killed, 4 survived, 13 no longer apply.

## Notes

These are below the bar.

- **Test reach, code right.**
  - Mutant 14: no test pins the ruling's half that step 5 compares a known answer's device by `@id`. The existing tests use a device of another name.
  - Mutant 26: `atlas_layouts` is not pinned to sorted order.
  - Mutant 29: the `law`-only layout accounting is not pinned against `coherence`.
  - Mutant 42: the set of Atlas wrapper keys is tested only with chosen key names.
- **The ruling "a test reads all six real results".** The tests read bytes made in the six results' shape (`p1_builder.atlas_result_in_real_shape`), with the measured layouts as literals. No gate reads the real bytes until `p1-crates` exists. I read them.
- **Nothing compares across jobs.** MEASURED (`s/faults1.py`): a job copied byte for byte under new ids is accepted. Step 9 is the cover, and no limit says so.
- **D3's by-name reading.** MEASURED: a snapshot hung on a second device entity of another kind, a simulator, is accepted. No link decision changes. I could not build a crate where the reading accepts a false link.
- **`pub_counts` and `Index` on malformed bare entities.** MEASURED (`s/seam_hostile.py`): an unhashable `qro:decodeRule`, `qro:bitOrder` or `qro:rawForm` gives `TypeError`, not one of the three ValueErrors the docstring lists. `Index` builds `by_id` and the type lookup at construction, not at first ask.
- **FORMAT.md item 16.** It says a crash in a parcel's step is exit 3 and never a verdict. P1's in-step net, taken by the lead, makes such a bug a REFUSED line. Item 16 could say so.
- **CPU.** At the cap each raw is inflated about four times and decoded once or twice. Four cap-sized jobs took 15 s. This is slow, not wrong.

## What I did not do

- I ran none of P1.2's parts: no `p1-crates`, no `docs/P1.md`, no step 9 against a real generator. My "whole checker" runs use a pass-through step 9.
- I re-ran 268 of P1.1's 843 automatic mutants (`p1_steps.py`), not the other 575.
- I did not fuzz the vector file itself, which shares code with the Atlas reader.
- I tested only Windows 11 and Python 3.12.9. I did not exhaust machine memory; I used job-object peaks and a 512 MB limit.
- I touched nothing in `frozen\`. I ran `git status`, `git log` and `git ls-files` in the P1.1 worktree to confirm the freeze, so git may have refreshed its index cache there, and `git archive 20d40e6` in the real repository.
- I used no key and no network, and opened no `~/.quantum-film`, `.atlas` directory or credential file. I copied nothing of Moth's or Quantum-Film's into the tree. The real files are read in place or copied under `check\tmp` only.
- Three slips of mine:
  - Two lines of my console output for the real-crate faults printed full IBM job ids before I added masking to my scripts. None was saved to a file, and none appears here.
  - I wrote eleven small hash-list files to Git Bash's `/tmp`, which is the system temp directory, outside `check\`. I deleted them.
  - The runner and my first mutation batch let pytest and P1.1's tests write temporary directories under the system temp. P1.1's `p1-*` directories are removed at exit and none remain. pytest keeps its last three base directories there. I redirected `TMP` under `check\` for the later runs.
