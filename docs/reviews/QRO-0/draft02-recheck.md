# Verifier report: QRO-0 draft 2

**Bottom line:** by the standard "a gate, or a stated limit", draft 2 is not READY. I found 12 defects: wrong statements, or design properties that are false as written. None needs a redesign; each needs a correction or a stated limit. Nothing in the instruments or the Quantum-Film or paper numbers was wrong beyond the slips listed.

**Setup**
- All six frozen hashes match.
- Trees: moth-quantum is at 3a73823, cft-fp256 at f22e8d2, HonestFramework at 65447fd. ParcelRound `origin/main` is f42242e, and the local HEAD 8767e23 is 37 commits behind it. All trees were clean after my work.
- My work is under `<scratch>\verifier-QRO0-r2\work\`. That holds `scripts/`, `ctrl/`, `web/` and `mq/`, a `--no-hardlinks` clone of moth-quantum used for planting faults.
- Every script ran with `python -I`. The instruments and my checks use only the standard library, except where I ran Quantum-Film's own code. That code needs numpy 2.2.6, and I also used numpy for two checks of my own (`indep_suff.py` and `nn_bias.py`).

## Defects

**R1 (small).** Lines 404–405: "Its `fixed_at` against IBM's `finished` gives more than 0.94 s."
- The instrument prints 0.937854, and I recomputed it as 10:30:13.719333 − 10:30:12.781479.
- A lower bound rounded up is false. It should say 0.93.

**R2 (small).** Lines 1475–1476: `the authors call "not physical time bins"`.
- The supplement (S4, "Diagnostic limits", `supplementary-v2.txt:763–764`) says "These descriptive checks are neither physical time bins nor tests proving IID sampling." The quotation is not verbatim.

**R3.** Line 1217: "Each decision this study takes is here" is unchanged from draft 1 (the D11 finding).
- The new group at 1272–1284 lists six items.
- Still absent are rules 3 and 6–9, the calibration-link vocabulary and clock rule (549–575), and the drift statistic with the floor of three (577–583). Also absent are the refusal set and order (754–769) and the control list (1028–1045).

**R4.** Lines 913–930 contradict themselves.
- Each level begins "in addition", and the checker "states the level a crate reaches". That reads as a ladder, so "isolable from the pipeline" would include "anchored".
- Lines 927–930 then give v0's IBM crate as "recorded", anchors "not re-fetched", yet "isolable from the pipeline for the law role".
- On the ladder reading, 6.1's "yes" column cannot be produced for v0. On the other reading, "level" is the wrong word.

**R5.** The D2 lesson was applied to readout but not to drift.
- Lines 534–535 define CONTROLLED as "a control bounds the cause's effect on the measure".
- Lines 547 and 603–605 award CONTROLLED to drift for three or more repeats. Lines 828–830 then say the comparison does not prove that "one run's between-run drift bounds its drift at the job compared".
- Repeats estimate a spread; they do not bound an effect.

**R6.** The same property is false for the compile when the circuits differ across devices.
- Line 542 and 596–598 award CONTROLLED to kingston against fez, "DIFFERS … and CONTROLLED by the exact hold". The hold is noiseless (tolerance 1e-10 on ideal probabilities, `isa.py:39–48`). It shows that both circuits implement the law. It bounds nothing about what the differing circuits do on noisy hardware.
- I counted the committed gate lists:

| device | sx | rz | x | cz |
|---|---|---|---|---|
| kingston | 257 | 233 | 23 | 102 |
| fez | 249 | 226 | 24 | 102 |
| marrakesh | 251 | 223 | 24 | 102 |

- The qubits also differ. The effect is probably small, but "bounded" is not established.
- Line 772 offers "one of" the five statuses, and 6.1 gives two for the compile.

**R7.** Section 6.1 attributes the differences to the devices, but the data confound device with run block.
- Lines 615–617 say "yes", 626–628 say "These differences are the devices'", and 608–609 list "the day" as SHARED. The law jobs I tabulated from the job lines (created times, UTC) fall in disjoint blocks:
  - kingston sheets, 8 jobs: 12:22:18–12:37:20
  - marrakesh sheets, 10 jobs: 12:42:27–12:49:55
  - fez sheets, 10 jobs: 12:50:54–12:58:21
  - morning jobs, one per device: 10:27:16, 10:33:06 and 10:34:14
- Inside marrakesh's block the five-crystal share steps from 0.5133 at 12:45:00 to 0.5439 at 12:45:48. That is about +0.031, roughly 10 sampling errors, and it stays there. The kingston–fez gap is 0.0518. A step like that between 12:37 and 12:50 would look like a device difference, and within-block SDs would not show it.
- The three interleaved morning jobs point the same way: five-crystal share 0.6095 against 0.5310, forbidden share 0.0431 against 0.0544, XEB +0.8444 against +0.8064. That is one job per device, so it is support, not a control.

**R8.** Lines 78–80 (and 193–194): "It makes everything around the shots a function of the record."
- Section 4.3 records calibration in force, server settings, clock offset and code identity as absent, unknown or unexposed. The sentences that follow are fine; this one is the leftover of D3.

**R9.** Line 320 labels the absence claim READ for "Stirbu and Meijer van de Griend".
- Lines 306–309 and 1396 show that only the abstract was read ("abstract; page"). This is D12's flaw left in place for that paper.

**R10.** Overscope of the paper in the summaries, lines 115–116 and 162.
- Line 116 says "per-cause checks do not compose". Line 162 calls the QAOA-1 numbers "the proof that per-field checks do not compose".
- The paper says "a failure of independent full-tolerance thresholding, not of every single-field method" (main text, QAOA-1 paragraph). Its S1.4 adds "not an impossibility result for all single-field methods" and gives a valid summed bound on Cartesian support.
- 16.1 scopes it correctly; the summaries drop the scope.

**R11 (small).** Lines 663–665 list the NN correlation among "estimators … unbiased".
- It is a ratio of counts. I simulated 20,000 exact-law replicates at n=200 (bias −0.0011, −5.9 SE) and 4,000 at n=24,576 (+0.00002, +0.6 SE).
- Wrong as stated; no practical effect at the draft's shot counts.

**R12.** Line 542 says "each run's sent circuits simulated". `bundle.check` simulates `*.gates.json`; it only hashes the `.qpy` (`bundle.py:450–458`, `471–497`).
- I changed one bit of a bundle copy's `law.qpy` and re-sealed `isa_sha256` and the commitment. `bundle.check` returned ACCEPTED.
- The tie between QPY and gate list is made at submission by `tools/hw_run.py:197–201`, and needs qiskit. It is not among the three qiskit-needing stages at 1003–1015.
- A `compile-broken` plant in the QPY alone would not be refused.

## Item 1: D1–D14 and the notes

I read the code and ran things; commands are summarised.

**D4: confirmed.**
- I wrapped `audit.audit(RECORDS, ROOT, git_order=True)` (`scripts/run_audit.py`). It returned `([], 65)` in 19.4 s. `bundle.check` ran on 31 bundles. `hold_isa` was simulated 12 times: 3 devices × 4 circuits.
- The rest of the 124 bundle-circuit checks come from the in-process memo `_HELD`, keyed on the gate-list bytes' hash plus name, role, basis and known answer. The memo is sound: gate lists are byte-identical within a device.
- "65 of 65" means every line's bundle consults the hold, not 65 simulations. The draft does not claim otherwise.
- Planted gate-list changes, with the manifest's `gates_sha256` re-sealed (`scripts/plant_compile.py`):

| plant | result |
|---|---|
| `sx` made `x` | refused (`isa:`) |
| `rz` moved by π/2 | refused |
| `cz` dropped | refused |
| `rz(0.7)` inserted first on a qubit still in |0⟩ | ACCEPTED when digests are re-sealed |
| same `rz(0.7)` plant, digests not re-sealed | refused by digest |

  This matches 1057–1061 and 1092–1094.

**D2, answered directly.**
- Counting readout as "the device's own" is coherent as a definition (791–793).
- The two-layer statement still claims more than it delivers: R5 and R6 for layer 1.
- Layer 2 has a gap. "Its named twin" (794–796) is not fixed to the dephased twin. Against the uniform twin, XEB and the forbidden share are "signal", although section 7 says distribution measures cannot beat a classical sampler of the law's own distribution.
- Readout CONTROLLED is model-conditional (545), but the statement does not carry that.
- These two are notes, not defects.

**D1/D6: fixed in substance, with caveats.**
- Runs are a crate plus a selector, and kingston against fez no longer shares a job.
- A resealed copy that keeps job ids is refused.
- A copy with fresh ids, salts and commitments evades `comparison-trivial`. Section 12 states the general limit; section 8 does not.
- The widened rule refuses any shared job, including a shared known-answer control. No natural v0 pair hits that, since each bundle has its own known-answer job. Next-round bundles with several law repeats would.

**D7:** the truncation logic is right (see item 2); only R1 slipped.
**D3:** headline residue is R8. **D11:** R3. **D12:** R9.

**Confirmed fixed:** D5, D8, D9, D10, D13, and D14's six points.
- D14: the heading at METHOD.md:523 is exact; "question 6" at 1112; the 82d5f67 and 82989c5 commit mentions at VALIDATION.md 1614, 1689, 1695 and 1698, and in no record; "the brief" quoted correctly; Peltonen's associations and "may select … and record"; "or any SHACL engine".
- D8: the quote at HARDWARE.md:79–83 is now exact.
- D10: RO-Crate 1.3 says `datePublished` "MUST be a single string value in ISO 8601 date format".

**The first verifier's notes:** all 17 are in the text. I checked them against the data:
- 17 of 28 sheet QPY *files* differ (hashed myself; 0 gate lists differ).
- 85 files from 22 probes.
- 68 of 68 PUBs echo their commitment.
- The 297.3 s known-answer gap.

## Item 2: both instruments

**Commands**
- `python -I` on copies in `work\run1`, against the original tree, then again against a fresh clone.
- Stdlib-only reimplementations: `verify_clock.py`, `verify_spans.py`, `verify_ka.py`, `echo_count.py`.
- Reimplementations that use Quantum-Film's own modules or numpy: `indep_drift.py`, `indep_suff.py`, `law_vs_qf.py`.

**Reproduction**
- Both outputs are byte-identical (`cedd38e3…` and `4903b731…`), on the original tree and on a fresh clone.

**Code audit**
- XEB value, variance and standard error equal `compare.py:290–304`.
- `indep_drift.py` recomputed means, SDs, standard errors and SD/SE ratios through `compare.law_measures` and matched.
- The instruments' integer kernel gives the same probabilities as `compare.exact_law` on all 4,368 layouts, and the same 1,360 forbidden set.
- The Hellinger distance and radius formula match S1.5 and Eq. (12). They reproduce the paper's Table S1 (0.0438/0.0138/0.0044), 30,669 shots, 0.038915 and 0.015693.
- Pass/fail/unresolved matches S8/Eq. (11) with equal radii.
- `indep_suff.py` (numpy, Quantum-Film's own forbidden set) reproduces every number in the 16.5 table.
- The 65 line commits give bounds 0.3255 to 1.5838 (median 0.9218), and the 68 `fixed_at` bounds give 0.1919 to 1.6810.
- The 1.3–2.6 s range checks out.
- Spans parse as UTC: 65 of 65 sit inside [running, finished]. Under UTC−8, −7, −1, +1 and +2, 0 of 65 do.
- My own git test with commits made at fractional phases .02 to .995 shows `%ct` is the floor of the second, on 2.45.2.
- The readout closed form equals exact enumeration of the 2-qubit confusion: 0.3648, 0.3640, 0.3614, and +0.0034.

**Controls that fail**
- Sufficiency instrument:
  - Kernel plants (wrong cosines, disc radius 2, enlarged forbidden set) each exit 1 with an AssertionError.
  - Seven logic plants change the output: radius M, radius B, interval width, verdict rule, cell definition, H² reported as H, object classes.
  - Removing one shot trips the shot-count assertion.
  - Moving 1,500 shots in one record raises kingston's within-device H from 0.0242 to 0.0646 and flips the crystal-count {device} verdict at ε=0.10 from pass to unresolved.
- Timing instrument:
  - A kernel plant exits 1.
  - Ignoring git truncation reproduces draft 1's 2.58 s.
  - UTC−7 spans give 0 of 65.
  - A wrong coherence pair flips the model's sign to −0.0071.
  - `fixed_at` moved after `finished` gives "positive in 67 of 68".
  - A moved span gives 64 of 65.
  - A changed gate-list digest gives "gate lists differ in 1".
  - Raising fez qubit 140's readout error to 5% moves the model to +0.0169.

**Limits of the instruments**
- A plant in the XEB formula changes the printed "held to HARDWARE-RESULTS.md" line (+0.8528, or +0.4875) but exits 0. That line is a print, not an assertion.
- The scripts do not pin the commit or check a clean tree.
- Swapping p01 and p10 leaves the readout number unchanged, because a_a·a_b is invariant. That plant cannot fail.

**Verdict:** confirmed. The only defect on the instrument side is R1.

## Item 3: section 16 against the paper

**Commands**
- Read `manuscript.tex`, `generated/hardware_main.tex`, `hardware_rows.tex`, `data/finite/*.tex` and `supplementary-v2.txt`.
- `sha256sum`, plus `curl` on the arXiv abstract pages and the Enodo/VUO portal page.

**Confirmed**
- 0.0417, 0.0497 and 0.0514 are the paper's 0.0416650, 0.0496812 and 0.0514011.
- Hardware details: 29 September 2026, three jobs, IBM Kingston, two six-qubit layouts, 32,768 and 256 shots, controls 110001 and 001110, Qiskit 2.5.2, level 1, seed 271828, Runtime 0.47.0, dynamical decoupling and twirling off, no mitigation, ε=0.15.
- Hardware results: raw layout record passes (0.0333); decoded empty record passes (0.0272).
- Quarter diameters 0.0045 to 0.0158.
- Propositions 1 and 2, the section numbers, and the author list.
- The paper does not cite Peltonen (`references.bib`).
- Hashes: `d4c3ce3e…` is the source `.tar.gz`, `59fb7293…` the PDF, `3d8a20cf…` the supplement.
- arXiv dates (7 and 8 Oct 2026) and the CC BY 4.0 link.
- The Enodo/VUO page says "341 files", "20.00 MB (uncompressed)", "uploaded on 06/10/2026", and "Prepared release v12c".
- "Any hidden discrepancy is eventually detectable" is at S1.7.
- The "exact channel propagation evaluated in floating point" quote is exact.

**Defects:** R2 (the quotation) and R10 (summary scope).

**Notes**
- The page says "Its license is CC-BY-4.0 unless defined otherwise". The draft drops the qualifier at 1479 and 1324.
- "Non-matching records establish nothing" (1437–1438) differs from the paper's "do not establish disagreement".
- Lines 1556–1561 say the paper describes no commit, hash or commitment. I confirmed that for the paper and supplement, but the 341-file archive was not opened. The paper says it holds job identifiers and provider-returned spans.
- "None says which comparisons a record supports" (1484) is the draft's inference, not in the paper's section I.
- "As its certificate survey found" (1525–1527) is not in `CERT-V2.md`.
- 16.3(4)'s "both usable" (1536) sits against 16.5's "nothing resolves at ε = 0.05".
- "A radius small enough would need 50,019 … or 112,120" (1594–1596) uses the instrument's unstated criterion 4η ≤ 0.05, which assumes zero true risk. With the observed within-device risks, the paper's planning formula gives 459,339 (three-way) and 1,181,983 (crystal count) shots per job.
- α=0.05 is per object, not family-wise over the two objects.
- The 16.5 aggregate sentence is driven by marrakesh. For kingston against fez the crystal-count ranges separate: 0.0275–0.0648 across devices, against at most 0.0242 and 0.0236 within.
- "Certified sufficient … the job may be dropped" (1592–1593) covers the 31 observed jobs only, at 95%, under the stated sampling assumptions.

## Item 4: new claims in draft 2

**Confirmed**
- The 6.1 numbers: means, between-run SDs, d = +5.2 / −3.6 / +0.9, Welch t = +11.4 / −8.1 / +2.1.
- SD/SE ranges 2.9–5.3 and 1.2–2.9.
- The readout numbers.
- The known-answer-to-law gaps.
- Known-answer rates: kingston 90.33–92.09%, fez 86.43–90.62%, mirror shots 0.
- "A profile URI must resolve" holds. The profiles page says "The profile URI MUST resolve to a human-readable profile description"; it exists for 1.3 as well as 1.2.
- ExecutionSpan page: "The start time of the span, in UTC."
- `properties()`: "at the time the job started running".
- RO-Crate 1.3.0 (22 Jun 2026, "Recommendation", schema.org v30.0, "None of the new terms are used").
- WRROC 0.6.0 (07 Sep, #104).
- Process Run Crate 0.6 requirement levels.
- The `sha256`/`sha512` terms in the workflow-run context.
- rocrate-validator 0.12.2 (05 Oct) and its `profile.ttl` with `must/`, `should/`, `may/`.
- Peltonen's evidence statuses, associations, "may select … and record", and the "must not be presented" rule.
- QProv is "only quantum computers of IBMQ".
- QC-MM's abstract (search results; the MDPI page returned 403).

**Defects:** R4 for the levels and where v0 stands.

**Notes**
- The floor of three means two degrees of freedom. The 95% interval on the SD is [0.52, 6.29]×s; the draft states the degrees of freedom, which mitigates.
- Peltonen names "automated execution comparison" under "Long-term ecosystem use", not in its Future work list.
- Line 246 says the profiles page "shows the 1.2 text". A 1.3 page exists with the same MUST.

## Item 5: cross-references

- I extracted all 138 question and section references (`work\xrefs.txt`) and read each in context.
- Draft 1's section 14 maps to draft 2's as stated (1650–1657): 1→1, 2→2, 3→5, 4→4, 5→7, 6→6, 7→8, 8→9, 9→10; 11–13 are new.
- All point to the right place. **Confirmed.**
- Minor leftover: "Between two crates" at 80–81 and 194–195 predates the run-and-selector fix.

## Item 6: reach

**Defects:** R7, R10 and R11 are reach failures. R7 is the main one.

**Notes**
- The "differs by class" drift contrast (632–635) rests on one integrity measure against two distribution measures.
- The SD/SE ranges include marrakesh inside a two-device example.
- The "−3.6" depends on an unstated equal-weight pooled SD. The usual df-weighted pooling gives −3.50.
- The 6.1 header says "MEASURED by `v0_timing_and_drift.py`". The known-answer rates and chains are not in that output. They do reproduce.
- The "Does not prove" list (822–833) omits that the selector was not chosen after seeing the data.
- "Atlas returns counts only" (383): the result payload also carries `density_matrices` and `observables`. The decode was "inferred" from engine output and then held to a known-answer run (`decode.py:3–4`), not "inferred from known answers" (541).
- "Anchor" is used for git commits at 4.2 and 4.3, against line 460's "A git commit is never an anchor".

## Item 7: privacy

- Commands: HonestHarness's own `PATTERNS` (path, address, key) from `tools/check.py`, plus greps for CRN, token and API-key words, over the draft, the two instruments and their outputs.
- Found: **nothing.** The only hits are the handle `loganw234` (line 1311) and three IBM job ids.
- Note: all 31 bundle `README.md` files carry `github.com/loganw234/Quantum-Film`. Section 9 copies them byte for byte, against rule 3's "user names … never carried". The handle is public, but the rule as written conflicts.

## Item 8: anything else

**Defects:** R6, R7, R8, R12.

**Notes**
- The readout inputs are older than the snapshot stamps suggest.
  - Each snapshot value carries its own `date`.
  - The pair's readout errors were measured about 7.0–7.1 h (kingston), 7.8 h (marrakesh) and 10.5 h (fez) before the coherence jobs were created. The stamps are 3.55, 2.96 and 2.31 h before.
  - The kingston and fez model inputs differ in age by about 3.4 h.
  - The +0.0034 is insensitive to which of the two marrakesh or fez snapshots is used. As a rough empirical check, the known-answer jobs show the same order of magnitude for P(0|1).
- `job-reattributed` (1031) is refused by `commitment` only if the two jobs have equal shot counts. Otherwise `count-unpaid` fires first (979–981).
- Q9's "format has one [shot count] per job" is the plan and runtime. `bundle.py:53–56` says qiskit-ibm-runtime 0.50.0 deprecates different shots across PUBs; the paper used 0.47.0.
- The relationship to the paper's claims is otherwise fine.

## What I did not do

- I did not run the full Quantum-Film test suite, only `audit.audit`. I did not install qiskit or Aer, so I did not check the QPY-to-gate-list link or the Aer predictions.
- I did not call IBM or Atlas, re-fetch any job, or read the 341-file Enodo archive.
- I did not verify these:
  - the lead's and agents' readings;
  - Logan's permissions and words (Sonnet, "standing permission");
  - the negative that IBM does not document returned order as chronological;
  - QProv or QC-MM's full texts (MDPI returned 403);
  - HonestHarness beyond `tools/check.py`'s patterns.
- I did not read the draft 1 to draft 2 diff end to end. I checked every D-fix and note by locating it in draft 2.
- I spot-checked about 35 of the cited line ranges (cft-fp256, ParcelRound, HonestFramework, moth-quantum) and did not re-read all of them.
- Several public pages came through WebFetch, which summarises, so their strings are the tool's extraction and not byte-verified. Those are the RO-Crate release, profiles, root-data-entity and JSON-LD pages, the PRC page, the WRROC release, the rocrate-validator listing, the IBM pages, QProv, and arXiv 2608.05041.
- I cross-checked only the Enodo page, the arXiv abstract pages and the w3id context with `curl`.
- Transient outputs went to the shell's `/tmp` rather than the scratchpad. I edited no tracked file.
