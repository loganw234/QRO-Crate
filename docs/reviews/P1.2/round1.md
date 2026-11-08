# P1.2 verifier, round 1: report

## Verdict: NOT READY

I found three defects in what the code does, all on the Atlas path or in the adapter's exit class. I also found three false claims in `docs/P1.md`. Nothing wrong with the IBM generator, the checker side, the controls or the twin turned up.

Every number below is MEASURED unless marked READ or BELIEVED. My scripts are in `SCRATCH\verifier-P12-r1\check\s\`, and I name the one that shows each fault. I masked all job ids as `&lt;job&gt;`.

## Defects

### D1. Code (a guard that does not fire where it claims): an Atlas commitments line is only recomputed if its job has files in the crate

- **Fault:**
  - On a copy of the real Atlas crate I appended one line to `2026-09-25/p3/commitments.jsonl`.
  - The line names a job the crate does not carry. Its commitment does not recompute, and it has `decode: "x"`, `shots: 5` and `code_commit: "not a commit"`.
  - I re-sealed the file's digest in the metadata.
  - `python -m qro check` exited 0 with ACCEPTED (`atlas_d1d2_cli.py`, `atlas_orphan.py`).
  - A duplicate line for a job that has files is refused, and so is a line naming a second engine, so only part of the guard fires.
- **Cause (READ):**
  - `qro/p1_generate.py` `atlas()` parses the lines at about line 716 but uses them only to collect engine names.
  - The recompute `rec.commitment_v2(...)` sits in `_atlas_laws` (about line 801), which iterates over job files, not over lines.
- **Claims it contradicts:**
  - The G11 row at `docs/P1.md:119` says "each commitments line recomputes under version 2".
  - The module docstring of `qro/p1_generate.py` says the same.
  - Design item 1.4 says the crate "cannot carry a line that does not hold together".

### D2. Code: the Atlas generator overwrites an entity when two jobs share an id, and the checker accepts the result

- **Fault:**
  - I set the vector's `job` to the id of a law job and regenerated with the generator (`P.rebuild`).
  - The crate went from 7 Jobs, 7 Pubs and 7 Decodes to 6 of each, while still holding 7 `qro:RawResult` files.
  - One law result is now read by no Decode, so step 5 never decodes it.
  - `python -m qro check` exited 0 with ACCEPTED (`atlas_vecid2.py`, `atlas_d1d2_cli.py`).
- **Cause (READ):** `atlas()` builds the vector's Job, Pub and Decode with the same keyed assignments as the law jobs (lines 742 to 757), with no duplicate-id guard. The IBM side is safe because G2 raises on a job id seen twice.

### D3. Code (wrong exit class): records or an `--out` the adapter cannot use give exit 3, "the adapter itself failed"

All three cases below were run as processes.

- **Unspellable text in the records:**
  - I put `versions.qiskit` = `2.5.2 x` in the morning manifest and re-sealed the manifest digest in the lines and markers.
  - The adapter exited 3 with `FAILED: the adapter itself failed, Refused: spelling at @graph[33] @id: an @id is printable ASCII with no space; this is not a verdict` (`h_qiskit_space.py`).
  - A `program` of `my program`, consistent in every record, gives the same exit 3.
- **A decode rule that is not IBM's:**
  - I set the manifest's decode to the Atlas rule, consistently in the manifests, lines, records, commitments, IBM's echo and the read's records.
  - G5 passes because `RULES.get(...)` finds the rule. `ibm_counts` then raises a `DecodeError`, which is not a `GuardError`.
  - The adapter exited 3 with `DecodeError: ... does not read the order atlas-register` (`h_decode_process.py`).
  - Step 9 refuses the same records as `metadata-generated`.
- **An `--out` that cannot be created:**
  - A wildcard, a colon, or a path under a file gives exit 3 with the host's OSError.
  - The `out.mkdir` at lines 178 to 179 sits outside the `try`.
- **Cause (READ):** `_verdict` (lines 242 to 251) catches only `AdapterError` and `GuardError`, and `main` sends everything else to 3. A writer `Refused` from `canonical.write` is a verdict on the records, so it should be exit 1.
- **Control:** a spellable program name `sampler2` builds with exit 0.

### D4. Prose (a stated limit that is false): limit 16 says "refused by step 9"

- **Wording:** `docs/P1.md:225-226` says a job copied byte for byte under new ids "is accepted by steps 4, 5 and 8, and refused by step 9".
- **Fault:**
  - On a copy of the twin, I made the manifest name a second coherence job with identical circuits.
  - I copied its line, marker, metrics, raw result and records to new names and a new job id, and added the read's two records for the new id and their MANIFEST entries.
  - I regenerated the metadata with `rebuild`.
  - All nine steps ACCEPTED it, and the crate holds 5 Jobs (`h_copy_job.py`).
- **Why it fails the limit test:** the fault passes every gate and falls outside the limit as worded. It also contradicts limit 1, which says "a fabricated run with fresh identities" is accepted.
- **Where the claim came from:** P1.1's limit 22 relied on step 9 as cover, but P1.1's tests stood a pass-through in for step 9. Nothing in the tree tests this limit against the real generator.

### D5. Prose (a claim that reaches too far): `docs/P1.md:122-123`

- **Claim:** the guards "are the cover ... a record the steps never read cannot be changed without the generator, and so step 9, noticing".
- **Fault:** these leaves can be changed, with only the file's own digest and size re-sealed in the metadata, and the crate is ACCEPTED:
  - every field of the verdict files;
  - the device-run records' `law.*`, `code.quantum_film` and `source.fixed_at`;
  - the metrics wrappers' `job.*`, `metrics.*` and `result_metadata.*`, including a second copy of the execution span that G6 does not compare with the raw's;
  - the submitting marker's `begun_at`;
  - the read's README, logs and MANIFEST header fields, and MANIFEST entries for files the crate does not carry;
  - for Atlas, most of the submit, status, score and result-envelope fields.
- **Scale:** 391 of 2,283 trials on the twin and 895 of 1,059 on the Atlas crate (`sweep_files.py`, `summ2.py`).
- **Why the narrower limit 9 does not rescue it:** limit 9 covers decoded records and verdicts only.

### D6. Prose (a false number): "The longest is 62 characters"

- **Where:** `docs/P1.md:38`, and limit 14 at `:220`.
- **Measured:** the longest in-crate path in the real IBM crate is 77 characters. Ten files have it, for example `2026-10-05/ibm/ibm_marrakesh/sheet-10/run/known-answer-pub0-known-answer.json`, and eight more have 76.
- **Source and test status:**
  - The 62 was copied from the design.
  - No test holds the claim.
  - The page says every claim "is held by a test or says it is not".
- **Effect:** the Windows 260-character budget in limit 14 is understated by 15 characters.

## What I ran and what held

- **Freeze.**
  - `SHA256SUMS` verified 366 of 366 over `tree\`, and its own digest begins `1b0a77ba1d79dd1b`.
  - The four ledger and brief digests match.
  - The worktree's 366 files equal the packet's hashes.
  - Against 37640f0 the tree adds 75 files and changes `docs/README.md` (one index line) and `qro/register_p1.py` (+15 -2).
  - Everything is inside P1.2's list and the files P1.1 owns are untouched.
- **Runner** (a throwaway git repository in `check\w`, commit e9e3dd5, `PYTHONDONTWRITEBYTECODE=1`).
  - The full runner with `QRO_MOTH_ROOT` passed 19, failed 0, skipped 5 by name (p2, p4, p2-crates, profile, p4-shacl). Stage seconds were p1 138, p1-crates 146, control-tests 56, controls-run 8, docs 31 and privacy 7.
  - The quick budget passed 15, failed 0, skipped 3 by name (p2, p4, profile), with a stage-time sum of 272 s.
  - Times are noisy because other work, including my own sweeps, was running.
  - The tree stayed clean after the adapter and runner ran. Test counts match the ledger: `tests/p1` 1,589 and `tests/p1crates` 36.
- **Real crates** (built with the adapter as a process outside the tree, checked with `python -m qro check`).
  - The IBM crate has 1,073 files and 1,380 entities. Its identity is `8ec4dc39...` at build and at check.
  - The Atlas crate has 31 files and 63 entities. Its identity is `f9c1a259...`.
  - Both are ACCEPTED, and the twin and Atlas crate also build and check identically under Python 3.13.14.
  - Every crate file equals its source byte for byte.
  - The only sources left out are the four dry-run probe files (IBM) and the two Atlas platform files.
- **Measurements, with my own code that imports no `qro`** (`measure_ibm.py`, `measure_atlas.py`).
  - 68 of 68 commitments recompute and equal the claim, the line, the record and IBM's echo.
  - 12 values-digests give 6 classes: kingston 3, marrakesh 2, fez 1.
  - The link rule gives 57 at-first-shot and 8 in-gap, and one job's snapshot at running time differs.
  - 31 of 31 known answers hold msb-first and 0 of 31 hold under the mirror.
  - The Atlas vector's worst |z| is 2.15 (plain order 172.96, mirrored 346.28), the six law results hold 1,995 to 2,027 layouts, and the numbers in the docs' crate tables match.
- **Seven controls, on hard-linked copies of the real IBM crate** (`controls_real.py`).
  - Each came out as its registry row says: `commitment`, `known-answer`, accepted, `calibration-link`, `calibration-link`, accepted, accepted.
  - No write went through a link. All 1,073 source files kept their digest, size and inode.
- **T1.**
  - The generator's output is byte-identical with the metadata file absent, garbage, empty, or another crate's, on the twin and the Atlas crate (`t1_independence.py`).
  - It is also identical across `PYTHONHASHSEED` 0, 1, 777 and random, and across working directories.
- **T2 and T3, by sweep** (two sampled leaves per leaf class).
  - Of the 2,283 leaf edits on the twin, 1,373 were refused by a `GuardError` at step 9 and 519 by steps 4, 5 or 8 (`commitment` 200, `calibration-link` 200, `raw-form` 113, `known-answer` 6). The other 391 were accepted: they are the unguarded leaves listed under D5.
  - For all 519 step-4/5/8 refusals, the generator alone also raised a `GuardError` (`replay_gen.py`).
  - Not one leaf edit made the generator emit a changed value, and not one made it raise anything but a `GuardError`.
  - Type-confusion fuzz (every node replaced by `None`, 0, a string, a list or an object): 2,886 trials on the twin and 338 on the Atlas crate gave 0 non-`GuardError` exceptions (`fuzz_types.py`).
- **Metadata sweep.**
  - 362 edits of every term of every entity of the twin, alone: 360 refused, each CHECKED term by the step that owns it (`sweep_meta.py`).
  - The two accepted are the root's header terms `qro:writer` and `qro:writtenAt`, which are normalised away by design.
- **Adapter.**
  - `--out` inside the repository, the repository itself, a parent of it, a path through a junction into it, a relative path into it, a file, and a non-empty directory all give exit 2, and nothing is created.
  - A modified, staged, untracked, or other-commit (HEAD~1) checkout gives exit 2 and leaves no `--out`.
  - Closed stdin gives 0, closed stdout or all three closed give 3, and a closed stderr on a build that succeeds gives 0. None gave 120, and a failing build leaves nothing in `--out`.
- **Twin.**
  - All 56 files equal `git show 3a73823:&lt;path&gt;` of moth-quantum, byte for byte (828,488 bytes).
  - The privacy stage passed, and my own scan of the twin, the added files and both real crates found no home path, address, CRN, token or key shape.
  - No Atlas byte is in the tree.
- **Seam, with a stand-in `qro.p2_measures` in `sys.modules`** (`seam1.py`, `seam_atlas.py`).
  - Absent module: nothing of P2's.
  - Present module: `question_files(Path)` runs after the records are copied. `contribute(Path, deepcopy of {@id: entity})` receives 105 IBM entities without the descriptor or root, with `question/law.json` and its sha256 present. P2's entities enter `mentions`.
  - A crate built with the module is refused `metadata-generated` without it, and a crate built without is refused with it.
  - A module missing either function raises a `seam` GuardError and leaves nothing in `--out`.
  - The Atlas path accepts a stand-in too.
- **Toolkit.** The documented `compile-broken` recipe (`Forge.change_bundle_file` then `rebuild`) works on a copy of the twin.
- **Readings.** All nine hold on both real crates, and none changes a verdict the design states about an honest crate.
- **Lead's four notes for P1.2.** All are present: the stamp-order test, limit 15, the cost table at `docs/P1.md:235` (with the pointer for `p1_steps.py` line 27 correct), and the 6.1 s figure. P1.2's `cap_time.py` backs the 6.1 s.
- **Mutation.**
  - I wrote 113 mutants of my own that weaken one link of a compound guard, plus adapter, plant and reader mutants. 80 were killed and 33 survived (`mut.py`, `mspec.py`).
  - Three survivors are equivalent or nearly so: the G5 count is implied by G2, the Atlas layout allows one vector, and a bundle digest already separates devices.
  - Twenty survivors were also run against the whole of `tests/p1`, and all survived. `tests/p1crates` was not run on them.

## Notes (below the bar)

- **Test reach, where the code is right (30 survivors):**
  - G2: the line's `kind`, `route` and `backend`.
  - G3: the record's `submitted_at`, `backend`, `kind`, `program`, `route`, `decode`, `options`, `options_sha256`, `pub`, `circuit_sha256`, `salt`, `stock` and `basis`.
  - G3: an extra PUB record file. The real code raises G3 for it, as I checked.
  - G6: `created` is compared with `==`, and a `&lt;=` mutant survives.
  - G7: the read's `pubs_in_line`, its list of pubs, its commitment in the line, its commitments against the line, and an extra read job record.
  - G8: the committed digest against the raw's, the size against the raw's, and an extra result record.
  - G9: the digest leg against the MANIFEST (the size leg is killed).
  - G11: id8 against the job id, and the status file's job id.
  - A plant: `calibration-gap` still comes out refused if it names another snapshot.
- **The adapter is more permissive than the checker.**
  - It builds, with exit 0, a crate that `qro check` then refuses.
  - Case one: an `options_sha256` that is not the digest of `options`, consistent everywhere else, is refused `commitment` at step 4 (`h_options.py`).
  - Case two: a checkout missing the only copies of a known-answer QPY is refused `commitment` (`h_missing_file.py`).
  - The checker stays safe. G1 holds "where present", and the generator has no options-digest guard.
- **A dropped snapshot hides a gap.**
  - Dropping the 12:21:18 snapshot from the twin, which the read's own MANIFEST still lists, turns sheet-02's `history-in-gap` into `history-at-first-shot`, and the regenerated crate is ACCEPTED (`h_drop_snapshot.py`).
  - Limit 4 words this as "only the snapshots the crate carries". G9 only checks that present files are listed, not that listed files are present, so the crate holds evidence the generator could use.
- **Limit 15's "3 to 11 of each QPY file"** is true of the 17 QPY digests a commitment names. Across all 23 digests it is 2 to 11.
- **Ten or eleven PUBs.** The generator would write `#pub-&lt;id&gt;-10`, which step 4 refuses. There is no generator-level guard or test for it.
- **The seam on the Atlas path** is not tested in `tests/p1` with a stand-in. P2.1's real `contribute` meeting Atlas entities (no Compile, no basis) is first exercised at the lead's merge.
- **Git state:**
  - `--slice` skips the git check by design.
  - A modified file hidden with `git update-index --assume-unchanged` passes the cleanliness check, because it relies on `git status`.
- **A successful build with a closed stdout** exits 3 and leaves the built crate in `--out`. The docs describe this as "a verdict that cannot be written".
- **`qro:implementation`** is a header key valid on any entity, and `canonical.body` strips it everywhere, so step 9 ignores it. That is P0's, not P1.2's.
- **CLAUDE.md's "~70 s"** for the quick budget is stale. The lead already has this: the stage sum here is 272 s.

## What I did not do

- I did not run P2's real module, which does not exist in the packet, or the merge onto cbdb6a3 or P0.7.
- I did not repeat P1.2's own 281 mutants. I ran my 113.
- Leaf sweeps sampled two leaves per class, at the level where only the file's own digest is re-sealed. I did not run the level where every dependent digest is also re-sealed, and I did not sweep the 1,380-entity IBM crate leaf by leaf. Its controls were run.
- Thirteen of the 33 survivors were not run against the whole stage.
- I did not measure the 6.1 s cap timing myself or probe P1.1's modules.
- I did not test a non-Windows host or a host that cannot hard-link.
- I made a local clone of moth-quantum, built the real crates and two mutation workspaces under `check\`, outside every repository. I did not touch the real repository, the worktrees, the ledger, moth-quantum itself, or any key, `.atlas` directory or credential file. I made no network connection.
