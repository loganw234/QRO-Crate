# P3.1 round 2: verdict READY

I found no defect against the bar. D1, the manifest rule, the pins and the survivors are all met as ruled. Nothing round 2 changed moved a verdict, a record or a figure of round 1's packet.

## Scope items

**Freeze (READ and MEASURED).**
- `sha256sum -c` over the packet's SHA256SUMS is clean, and the file's own SHA-256 begins `5de81e66112b2d45`.
- `diff -rq` against round 1's tree shows exactly the 9 files the lead named and no others.
- The real repository's `git status` is clean.

**1. D1 (READ, MEASURED).**
- Limit 18 of docs/P3.md now names both `submitted-differs` and `compile-unheld`. It says each reads "not shown EQUAL" where the record's own cause is `unexposed`, and that P3.2 closes both with words of their own.
- It names two tests. `test_member_pubs_with_no_manifest_circuit_leave_the_compile_and_what_was_submitted_unexposed` was already there and shows the cause. `test_its_twin_the_same_declared_a_rehearsal_is_computed_and_says_so` now asserts `causes["submitted"] == "unexposed"` next to `compile == "unexposed"` and both statements.
- The diff of qro/p3_runs.py is the only code change. p3_verdicts.py is byte-identical to round 1's.
- Every `test_` name the page cites exists. The one apparent miss is `test_p3_`, a glob in prose.

**2. The manifest rule.**
- **READ:** `_held_manifests` now calls `p2_measures.manifest_of`. That function and the old inline code select the same File: the Compile's `object` Files whose path ends in `manifest.json`, exactly one required.
- P3 only ever asks about Compiles a Hold names. Step 7 (`p2_steps._compile`) calls `manifest_of` on every Compile and refuses one without exactly one Hold or without one manifest. So on a crate the checker accepts, the two cannot differ. The new `except HoldError: continue` is unreachable for such a crate.
- **MEASURED, differential:** I ran round 1's tree and round 2's tree side by side with my own script, work\cmp_rec.py.
  - **Compared:** the crate digest, the record hash and the facts hash for three synthetic specs (two devices; an unheld Compile; a gate-variant with different options). Also the record hash for four of v0's real IBM comparisons: device, morning, morning law-only, and the kingston-against-itself `comparison-trivial` refusal.
  - **Result:** all identical. I did not build a third crate shape of my own beyond the three specs; the Atlas cases in my script errored in both trees on a malformed plan of my own, so Atlas is covered only by the stage run.
- **Spy test:** `test_a_held_compiles_manifest_is_read_by_p2s_own_manifest_of` calls `manifest_of` once per Compile, 3 of 3.

**3. The pins (MEASURED).**
- I ran four mutants of P1 and P2 against `test_p3_independence.py` only, copying the tree and running through sbx.sh:
  - `manifest_of` re-signed (extra parameter), killed;
  - `manifest_of` renamed, killed;
  - `Manifest.circuits` re-signed, killed;
  - `Index.pubs_of` re-signed, killed.
- I listed every public method of P1's and P2's classes that P3's modules call by name. The set is `Index.{decode_of, files_by_sha256, get, of_type, one, pubs_of, raw_of}` and `Manifest.circuits`. Each is pinned, or is `get`, taken as a dict's. The new walk test covers this class list, and I found no class it misses.

**4. Survivors and the new builder options (MEASURED).**
- Round 1's six survivors, with the hand harness, run against all of tests/p3:
  - what was submitted ignoring decode, route, program and kind (4 mutants), killed;
  - the pair using one qubit, killed;
  - the unseen decode factor ignoring bit order, killed.
- I added two more readout mutants (the other qubit only, and coverage always true). Both killed.
- I wrote 13 mutants of the new builder options and ran them against tests/p3 and tests/p3crates. All 13 killed.
  - **Mutated:** mirror ignored, bit order not written, manifest decode, route and program ignored, commitment route and program ignored, line route and program ignored, instrument program ignored, `without-0` and `without-1` swapped, `without-0` carried as the complement, and `pattern_counts` giving the wrong set.
- The builder at its defaults writes the same bytes as round 1's. The three specs' crate digests match across the two trees.

**5. What round 2 moved.**
- Only the 9 files differ. The only qro/ change is `_held_manifests`.
- The new crate shapes pass the checker's steps 1 to 8: the tests that build them check them, and tests/p3 and tests/p3crates passed. I did not run the steps separately on each shape.
- No v0 figure moved. The identical record hashes above include v0's real comparisons.

**6. The runs (MEASURED).**
- I ran the full runner on the packet in my copy, through sbx-mid.sh, with the Moth, SHACL and kit variables set. It ended `passed 26, failed 0, skipped 4`.
- The skips are lint-kit, p5, p5-kit and p5-crates, and only those.
- Every stage's count equals round 1's except p3, which went from 402 to 414 passed, +12. That is the new tests, for pins, the spy, the builder options and the readout case. p3-crates stays at 15.

**7. Junctions (READ).**
- A grep for junction, mklink, symlink and `os.link` in tests/p3 and tests/p3crates finds nothing, in both packets.
- The `garbage-*` folders are untouched.

**8. The slip (MEASURED).**
- `git status --short` in the real repository is clean.
- Only the builder's `date`, `sed`, `cat`, `ls` and copies ran there, so there is nothing to find.

**9. Prose (READ).**
- The changed passages of docs/P3.md match the code. That covers the manifest rule, the pin sentence, the builder options, the seven-of-eight unseen factors and the per-qubit coverage test.
- The page's "fields they read ... are pinned by name" is true for the fields P3 reads of P1's `Manifest`, `Circuit` and `Line` and P2's `Value` and `Contrast`.

## Notes (below the bar)

- **Test reach, page prose (not code):**
  - `Index.refs_of_type` stays in the pin list though P3 no longer calls it. This is harmless.
  - The method walk is by name, and the page says so honestly. A future P3 call named `get` on a P1 object would go unpinned.
- **A slip of my own:** my differential script's stdout (work\cmp1.out, inside my sandbox) holds one unmasked job-id-shaped string, inside a refusal message. It is not in this report, and I left the file in place.

## What I did not do
- I did not wait for or compare against the lead's run.
- I did not run the controls' run separately; the runner's controls stages passed.
- I did not build crates with two manifests or none to test the unreachable branch; that is argued from step 7's code, not measured.
- I did not touch IBM, Atlas, any key, frozen\, the worktrees, the lead's clones, the real repository or the ledger.
- I kept the `garbage-*` folders as they were, and ran nothing with `-S`.
- I wrote no report file; the scratch check directory is unused because that write was refused.
