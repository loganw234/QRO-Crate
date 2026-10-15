**1. Bottom line: NOT READY.**

I found four defects, Y1 to Y4. All are text-level slips, and none needs a redesign. I recomputed every figure of 9.1 independently and they hold. The defects are:
- a stale figure left by the N2 change (Y1);
- a milestone gate that cannot be met as written (Y2);
- X7 not applied everywhere (Y3);
- a READ citation with the wrong date (Y4).

Separately, the live tree has moved since the freeze (setup, below). M1 stage 5 is already overtaken by those changes. That is not a defect of the frozen draft, but it should be folded in before Logan sees it.

**2. Setup**
- **Hashes:** `sha256sum -c` passes for all 16 files. Draft 6 is `b6c1515c…`. Section 15's table matches all 7 instrument hashes, all 5 output hashes and both MANIFEST hashes.
- **Trees:** moth-quantum was at 3a73823 and HonestHarness at b69ed76. Both were clean before and after, and I edited no tracked file. I made a throwaway commit only in my own `--no-hardlinks` clone, then reset it.
- **Live tree at start:** `QRO-0.md`, all 13 `qro0/` files and the records README were byte-identical to the frozen copies.
- **Live tree since the freeze (not from me, not in the packet):**
  - 12:37: a new `docs/studies/qro0/ibm_dryrun_v0.py`, and `records/2026-10-14/ibm-dryrun-probe/` with a log.
  - 12:37: the records README gained a section. It quotes Logan: "Dry runs are safe and clear to run anytime, only the real QPU runs are a hold point". It also reports that the account lists no `mock_*` backends, so IBM's dry run is unavailable today.
  - 12:38 and 13:07: `QRO-0.md` was edited again (now 137,244 bytes).
  - I read only that README section and `probe.json`. I did not read or run `ibm_dryrun_v0.py`.
- **Runtime:** Python 3.12.9, `python -I`, standard library only. Work files are in `<scratch>\verifier-QRO0-r6\work\`, with my code in `scripts\` and the plant results in `plants\`.

**3. Defects**

**Y1. Lines 1298-1299: "For kingston against fez that is about half the sum of both devices' shrinkage" is wrong after N2.**
- "That" is the bound g_B·P_B + o_A + o_B. My recomputation, from my own code and Decimal arithmetic, gives:

  | Quantity | Value |
  |---|---|
  | g_B·P_B (shrinkage term) | 0.0181 |
  | o_A + o_B (offsets) | 0.0058 |
  | Bound | 0.0238 |
  | Sum of both devices' certified shrinkage | 0.0355 |

- The bound is 67% of that sum. Only the shrinkage term alone is about half (51%).
- In draft 5 the bound was about 0.0183, which was "about half". N2 added the offsets and left the sentence unchanged.
- The instrument prints none of these pieces.
- Fix: replace the sentence with "that bound is 0.0238: the shrinkage term, 0.0181, is about half the sum of both devices' certified shrinkage (0.0355), and the offsets add 0.0058". Or drop it.

**Y2. Line 1517 (M1 stage 2): "The checker refuses every planted control of section 11" cannot be met.**
- Section 11 (lines 1408-1409) says a control is "refused by the name given, or stated as the table says". Nine of its 24 rows are not refusals by the table's own words:
  - qpy-only (1419);
  - calibration-restamped (1422);
  - shared-control (1426);
  - single-runs, readout-unbounded and time-confounded (1431-1433);
  - shot-moved-resealed (1435);
  - unit-incomplete and not-interleaved (1437-1438).
- Other rows need components that arrive in later stages:
  - self-compare, resealed-compare and joint-omission need the comparison (stage 4).
  - unit-known-answer needs the kit (stage 3).
  - class-declared is P2's own control (line 1582), and P2 is listed at stage 4 (line 1530).
  - The crate's measures and the exact hold are also P2's.
- Fix: "The checker refuses each crate-level control that section 11 says it refuses, and accepts or states the others as the table says. The unit's controls wait for stage 3 and the comparison's for stage 4." Also move P2's crate-side pieces to stage 2, or say that stage 2's checker skips steps 6 and 7.

**Y3. X7 is not applied everywhere.**
- Line 1011 calls the Atlas runs a campaign ("one of v0's two campaigns"). Line 1012 defines a campaign as what one pre-registration fixes, and lines 1019-1021 say the Atlas runs "had no pre-registration".
- Line 1085 (the comparable level) says "the campaign's devices are interleaved in time". Levels are properties of what a crate carries (line 1068). For a free-tier unit a campaign is now many crates, so a crate cannot carry that property.
- Line 882 still says each run is "a crate and a selector". Section 9.1 "extends" it, so this is a loose end rather than a contradiction.
- Fix: line 1011 becomes "v0's IBM campaign or its Atlas runs". Line 1085 becomes "the crate's devices are interleaved in time". Line 882 gains "or a set of crates (section 9.1)".

**Y4. Lines 1125-1127: "Logan's instance reached … on 2026-10-05 (docs/HARDWARE.md:16-17, READ)" has the wrong date for its source.**
- HARDWARE.md says at its head (lines 3-4) "Read and measured on 2026-10-01". Lines 16-17 are from that reading.
- The 2026-10-05 date comes from v0's records, where jobs ran on all three devices.
- Fix: "reached … (docs/HARDWARE.md:16-17, read 2026-10-01, READ); all three ran v0's jobs on 2026-10-05 (MEASURED)".

**4. Per item**

**Item 1: X1 to X8**
- **X1: answered correctly.**
  - Lines 188-194 match my independent pooled table.
  - The unresolved list (XEB on all pairs, marrakesh against fez on the forbidden share, kingston against marrakesh on both coherences beyond readout) is exactly the six cells above 100.
- **X2: answered correctly.**
  - The scope list is complete for complete units.
  - 579 rederives as 39 × (1 + 10) + 15 × 10. The 39 is 3 devices × 13 intervals (5 measures, 4 single-site means, 4 readout bounds). The 15 is 5 measures × 3 devices per unit's mean.
  - The projection uses it. `capacity(look=True)` takes `look_family` and α/(k(k+1)), and plants C01 to C06 all change the output.
  - Across 21 cells × 100 looks, certification never reverses.
  - Caveat (note b): the pair-pool rule.
- **X3:** labels, `unit-incomplete` and the pair-pool rule are right and agree with the control rows, except the date in Y4.
- **X4:** no "in-job" remains outside the X4 table row.
- **X5:** the four costs match `sufficiency_v0.out.txt`.
- **X6:** the line ranges are right. Note k covers one slip.
- **X7:** see Y3.
- **X8:**
  - I recomputed all 15 designs' costs with exact rationals and they match.
  - "Largest of the film designs leaving more than a quarter" is true: 168 s spare against 150 s.
  - The split-design and 4,096-shot-control statements are true.

**Item 2: N1 to N9 and ρ**
- N1, N3 to N9 and the ρ note are taken correctly.
- **N2 derivation.**
  - From E[z'|z] = a + f·z I get P' = a_a·a_b + a_a·f_b·⟨z_b⟩ + a_b·f_a·⟨z_a⟩ + f_a·f_b·P.
  - Substituting m' gives offset = a_a·m'_b + a_b·m'_a − a_a·a_b, which is the draft's formula.
  - The instrument (lines 253-266) bounds |a| by max(p01, p10) and |m'| by the interval endpoints. That is a valid triangle bound. The bound in `beyond_readout` matches my derivation.
- **N2 property test:** 300,000 random cases at each of two single-site ranges (±0.4 and ±0.15).
  - The closed form matched exact enumeration in every case, and the offset identity held.
  - The bound was never unsound with the cross terms kept (minimum slack +0.0074 and +0.0053).
  - It was unsound in 215 and 2 cases with the cross terms dropped.
- **+0.0034 has no cross terms:** the law's state is supported on weight-5 strings, so ⟨X_i⟩ and ⟨Y_i⟩ are exactly 0. Both instruments print +0.0034.
- **Independent reproductions:**
  - K−F ⟨X0X1⟩ certified difference 0.027834 and beyond-readout margin +0.003986. The offsets are 0.002432 (K), 0.005317 (M) and 0.003333 (F).
  - The full pooled table matches for both control sizes (2,048 and 4,096).
  - Strong-form shot needs: the exact minima are 77,380 and 153,166. On the instrument's 1,024 grid they are 77,824 and 153,600. Marrakesh against fez stays negative at 1,048,576.

**Item 3: the hold and M1**
- **Verbatim and applied:** the hold is quoted in full at lines 40-42, and in parts at 1507-1508 and 1545-1546. Nothing proposes a run in the current quota. The five mentions of "fits in 247 s" (lines 1170, 1179, 1189, 1195, 1660) are statements of fit.
- **Stage citations:**
  - The `dry_run` docstring is at `base_primitive.py:129-142`, inside the cited 127-142. All four quotes are verbatim. The same text is in `sampler.py:112-117`.
  - The mock-device behaviour is `qiskit_runtime_service.py:1077-1078` and `1102-1111`.
  - `last_update_date` is 2026-04-15 (kingston), 2025-02-26 (marrakesh) and 2025-02-26 (fez), as stated.
- **Stage 5 and M2:**
  - Stage 5 waits for Logan's word, as frozen (lines 1540-1541).
  - M2's "same kit" is only partly checkable (note d).
  - P5's three routes are consistent for the local route: the anchors are `none` per rule 2. The dry run and the route field are underspecified (note c).

**Item 4: the changed instrument**
- **Reproduction:** all five outputs are byte-identical on the original tree and on a fresh `--no-hardlinks` clone with a copy of `records/`.
- **Git gate:** the changed instrument refuses a dirty tree, a modified tracked file and a moved HEAD. The calibration instrument refuses an extra file, an edited listed file and a removed listed file.
- **Audit:** I found no error in the changed code.
- **Code plants (45):** 38 changed the output and 7 did not.
  - Changed: look family (C01 to C04), α schedule (C05, C06), unit family (C07, C08), the search step, end and test (C09, C11, C12), U(D) (C14, C15), the computed R (C16, C17), 247 s (C20, C21), KL swap, budget, offset, g_max, true_hi, bound variants, cost rounding and the rest.
  - Unchanged: C10 (step 2048, equivalent), C13 (control shots do not enter the five-crystal strong form), C18 and C19 (typed R and typed 247, equivalent), C32 (positivity guard removed), C34 (wrong device's shrinkage on the B-above-A branch), C43 (horizon cut to 50).
- **Data plants (22 runs):**
  - Refused by assertion: a misfiled metrics job id, a removed metrics file, a record's job id changed, a removed sheet, a duplicate sheet.
  - Changed the output: single-site counts (100 shots and 1 shot), a readout value (+0.01 and +0.0005), a swapped snapshot, a charge 9 to 10 (247 becomes 246), 300 and 500 law shots moved (the crystal-count R went from 0.0346 to 0.0367), and a changed manifest `pair`.
  - Unchanged: readout +1e-6 (below print precision), a non-pair qubit (expected), 3 shots moved among five-crystal layouts, and a changed `basis` string. One removed-sheet plant was a harness error and I redid it.
- **Checks that cannot fail** (instrument line numbers):
  - the positivity guard (283-284);
  - the B-above-A device choice (289);
  - the manifest `pair` is never tied to the records' `basis`, and no snapshot identity or 4,096-shot count is asserted;
  - typed R and typed 247 are indistinguishable by output, so "computed" holds only because the code reads them (lines 178-182 and 201) and because data plants propagate.

**Item 5: consistency sweep**
- All section and question cross-references resolve and all 18 tables are well-formed.
- Of 35 numeric tokens in 9.1, the instrument output contains all but five. Four of those are expected: +0.0034 (comes from the other instruments), 0.50 (the runtime version), the section numbers, and 49,152 (3 × 16,384). The fifth is "about half" (Y1).
- No stale draft-5 figure remains outside section 17's history.
- Section 15's hash table is right.

**Item 6: privacy**
- **HonestHarness patterns:** I executed the pattern code taken from `check.py`'s text. The path, address and key patterns found 0 hits over the draft, 7 instruments, 5 outputs, the README and `records/2026-10-14/`. That is 142 files as copied at the start and 144 live now.
- **Extra greps:** CRN, JWT, long-token and e-mail all give 0.
- **Name hits (no values):**
  - `user_id` appears in the draft (lines 602, 1041), the README (line 39) and once in each of the 65 refetch job records. Each of those lines is a bare key name in the omitted-keys list.
  - `apikey` or `bearer` hits are `ibm_refetch_v0.py` lines 74 and 142, and `ibm_results_refetch_v0.py` lines 57 and 97. These are a guard regex and a key-file name.
  - `token` is line 1 of two logs, a warning text.
  - The live probe adds `instance_id` and `plan_id` as names.

**5. Notes**
- **a. Live tree and stage 5.**
  - Logan's later word makes "waits for Logan's word" stale.
  - The probe says no `mock_*` backends exist on this account. The runtime renames the backend to `mock_&lt;device&gt;` and raises if it is absent, so the runtime would refuse a dry run here.
  - M1 has no stated exit if stage 5 is unavailable.
  - Section 15 lists the `dry_run` lines of `qiskit_runtime_service.py` as READ, but stage 5 does not state their consequence.
- **b. Family count.**
  - 579 assumes all units are complete. Under the pair-pool rule an incomplete unit makes the pooled part per pair, so the pooled intervals can reach 78 instead of 39 per computation.
  - At k = 1 the instrument also counts leave-outs of an empty pool, which is conservative.
  - The pooled readout bound treats a and f as constants across pooled units, and says so nowhere.
- **c. Routes.**
  - The word "route" collides with Quantum-Film's `route` (ibm-direct or moth) and `kind` (qpu or simulator). The commitments already bind `kind`.
  - QF refuses a fake backend for a qpu bundle (`tools/hw_run.py`), so a local unit is a second bundle.
  - Mock data cannot pass `known-answer`, so a dry-run crate would be refused. The draft does not say how the checker treats it.
  - Nothing says a pooled real comparison admits only `qpu`-kind units.
- **d. M2.**
  - No control tests the dirty-tree refusal or the tagged commit.
  - If the kit commit sits in the header, byte comparison normalises it away.
  - "As Quantum-Film's runner does" is true of the Atlas runner (`tools/pauli_atlas_run.py:151-154`). The IBM runner checks the bundle directory and that HEAD is on origin.
  - "Logan's units run through the same kit" is labelled decided (line 201), but Logan's words are the rationale ("helps keep our runs as similar to a strangers as possible"); the kit is an inference.
  - M1's five-stage scope is the lead's reading of "functional prototype". It is not on the confirmation list or in a question.
- **e. 247 s.** It holds only until v0's charges leave the window on 2026-11-02, which is the date the live probe's usage record gives.
- **f. Small items.**
  - "4,096-shot job" (line 1114) is a PUB. The coherence job holds two PUBs.
  - The subscripts a and b (qubits) and A and B (devices) collide with the parameter a.
  - P5 states its negative control twice (lines 1600 and 1607).
  - The shot search is on a 1,024 grid.
  - Section 15's "names under fake_provider/backends/" understates that the dates come from the JSON files.
  - `qro:role` is per job in the entity table (line 1039), but a film job holds three roles. This is from draft 5.

**6. What I did not do**
- I did not contact IBM or Atlas. I did not run `ibm_refetch_v0.py`, `ibm_results_refetch_v0.py` or the new `ibm_dryrun_v0.py`. I created no service or account object and imported no qiskit or fake-backend code.
- I read the runtime source as text and the fake-backend JSON with `json`. I opened no credential, key, token or account file.
- HARDWARE.md lines 10 to 32 incidentally printed a sentence naming the key folder's location. I did not open that folder.
- I did not run `tools/check.py` itself, only its patterns.
- I did not diff the draft-5 instrument (none in the packet), so I audited the final code.
- I did not re-derive unchanged sections 1 to 5, 7, 10 to 12 and 16.1 to 16.4 beyond references, figures and stale-term greps.
- I did not check draft hashes 1 to 4, the arXiv hashes or Hoeffding against their texts. I did not run a coverage simulation of the α schedule.
- I did not review the live post-freeze `QRO-0.md`.
- I planted faults only in `free_tier_unit_v0.py`, plus the git and MANIFEST gates elsewhere. I tested Python 3.12.9 and CRLF only.

**7. In the brief**
- It says the live tree is read-only and implies it is stable, but it moved during the review.
- "records/2026-10-14/" is not in the packet apart from its README. I scanned my copy from the start and the live directory.
- "A changed single-site count in a coherence record" is ambiguous. I moved shots so both single-site counts change and the parity does not.
- "Run tools/check.py's patterns" was done by executing the pattern code from the file text.
- It does not say how to supply two roots to the calibration instrument. I used the records copy and the clone.

**To reach READY:** fix Y1 to Y4, then fold the post-freeze stage-5 facts into section 13 and P5. A re-check of those edits should be small.
