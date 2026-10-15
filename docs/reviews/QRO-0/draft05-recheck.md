**1. Bottom line: NOT READY.**

I found eight defects, X1 to X8. Six are text slips. Two need a stated scope or limit (X2, X3). None needs a redesign.

W1 to W5 and notes a to l are all answered correctly. The one exception is note b, which was not applied to section 15 (X6).

All five instrument outputs reproduce byte for byte. An independent reimplementation reproduces every figure of 9.1 that I recomputed (named in section 4).

**2. Setup**
- **Packet:** `sha256sum -c SHA256SUMS.txt` passes for all 16 files. Section 15's hash table also matches all 7 instruments, 5 outputs and both MANIFESTs.
- **Trees:** moth-quantum is at 3a73823 and HonestHarness at b69ed76. Both were clean before and after my runs. I edited no tracked file.
- **Live tree:** `docs/studies/qro0/*` and `records/2026-10-14/README.md` are identical to the frozen copies. `docs/studies/QRO-0.md` matched the freeze when I first checked. It was edited at 11:43:33 (sha256 now `25d60443…`), not by me. It appears to be draft 6 work, covering Logan's hold-off on a real run. I used only the frozen draft. All line numbers below are from frozen draft 5.
- **Work directory:** everything is under `<scratch>\verifier-QRO0-r5\work\`.
  - `moth-clone` is a `--no-hardlinks` clone at 3a73823, restored clean after the plants.
  - `qro-copy` and `qro-plant` are copies of `records/`.
  - `plantroot` and `inst_nopin` are the plant bench and the instrument copies with the git gate bypassed.
  - `plants` holds outputs. `scripts` holds my code (`indep_check.py`, `plant_ftu.py`, `plant_ftu2.py`, `plant_code.py`, `plant_cal.py`, `prop_beyond.py`, `privacy_scan.py`, `perjob.py`).

**3. Defects**

**X1. Line 179 (item 7): "Pooled units resolve the rest, with verdicts that stay valid however many units arrive."**
- It is false as written.
  - 9.1's own table (lines 1149-1153) has XEB at "&gt;100" for all three pairs.
  - Marrakesh against fez on the forbidden share is "&gt;100".
  - Kingston against marrakesh on ⟨Y0Y1⟩ beyond readout is "&gt;100".
  - Line 1155 itself says XEB "stays a per-device measure".
- It is also the one item-7 claim not marked as a projection.
- Fix: "Pooled units are projected to certify most of the rest in 2 to 9 units. XEB, marrakesh against fez on the forbidden share, and some beyond-readout cells stay unresolved at 100."

**X2. Lines 1167-1175 and 1199-1201: the anytime-validity claim is unscoped.**
- "Never raises the chance of a false claim" is true only for the declared pooled family on a nested pool.
  - That family is 27 intervals per look (15 pooled plus 12 readout bounds), on the first k units in arrival order.
  - I confirmed the spends sum to α (Σ1/(k(k+1)) telescopes to 1), and a union bound over looks then holds.
- 9.1 adds two more recomputations with no α, and the instrument computes neither.
  - **Leave-one-contributor-out** (lines 1199-1201) recomputes every pooled verdict once per contributor.
  - **The strong form at unit granularity** (lines 1173-1175) needs unit-mean intervals for every unit on every device (15k more intervals at look k).
- Also outside the schedule:
  - units or subsets chosen after seeing them;
  - arrival that depends on a unit's results;
  - a non-nested pool, such as a retraction;
  - any new measure or comparison.
- Fix: add a scope sentence. Say leave-one-out flags are uncertified cautions (or add them to the family). Say the unit-granularity strong form is uncertified until it has its own family and α. Say validity assumes arrival is independent of results.

**X3. Lines 1087-1093 (also line 173): "three devices" is labelled READ from docs/HARDWARE.md:15-19.**
- That file says "The owner's instance reaches ibm_kingston, ibm_fez and ibm_marrakesh" (:16-17), as of 2026-10-05.
- "Every Open Plan device, three today" and "anyone on it" therefore rest on an unread claim.
- The other two facts check out. Ten QPU-minutes per rolling 28 days in us-east is at :15. No sessions, with batch and job modes allowed, is at :18-19.
- Fix: label the device list BELIEVED for other instruments and dates. Say the standing pre-registration names the device list. Say what a unit is when a contributor reaches fewer devices.

**X4. Stale "in-job" readout wording contradicts the new level (lines 1061-1064), 9.1 and question 9.**
- Line 636: cause 5 is CONTROLLED "only by in-job controls". Fix to "in the job or the job just before it", as section 8 now does (lines 927-929).
- Lines 721-722 (v0's readout row): "no in-job control". The statement stays true but the term is stale.
- Line 1689 (16.2): "controls inside every job. Here: question 9". Question 9 now deliberately departs from this (lines 1482-1485). Move it to where the study differs from the paper.

**X5. Circular cost pointer.**
- Question 9 (lines 1499-1501) says the larger shot counts "and their cost, are in section 16.5".
- Section 16.5 (line 1785) says "What these would cost in QPU time is in question 9".
- Draft 4's seconds table was dropped from question 9. Only "17 to 21 QPU-minutes" survives, and it covers just one of the four M = 9 figures.
- Fix: restore the four M = 9 costs from `sufficiency_v0.out.txt` into 16.5. They are 17.4 to 21.1 min (three-way, ε = 0.05), 1.3 to 1.5 (three-way, 0.10), 49.1 to 60.2 (crystal count, 0.05) and 3.0 to 3.5 (crystal count, 0.10).

**X6. Section 15 is stale in two places.**
- Line 1580 still says base_primitive.py:150-178. Note b said to extend this, and section 3 now cites :155-208 as "All READ" (lines 343-346). The job-mode path is at :198 and :206.
- Line 1583 lists "draft 1's, and the re-checks of drafts 2 and 3". The text relies on draft 4's re-check (lines 498, 1952, section 17), which exists only as the lead's transcription.

**X7. Line 987 (and line 1541): "The unit is a campaign: what one pre-registration fixes."**
- This contradicts 9.1. A standing pre-registration fixes every later unit (lines 1185-1188), and pooling is "across crates" (lines 1164-1166). One pre-registration therefore fixes many crates.
- Fix: say a crate is a contribution of one or more units, a campaign is what one pre-registration fixes, and a comparison pools crates.

**X8. Lines 1126-1129: "16,384 is the largest design costed that fits twice … and fits now".**
- It is false as worded for the 15 designs the instrument costs.
- The split design NL = 24,576, NC = 8,192, Nc = 2,048 costs 153 to 207 s. It fits twice with 186 s spare, fits the 247 s, and has a larger law count. Its three-way planning ε is 0.099, so it decides the Hellinger {device} test at ε = 0.10 inside one unit. Its price is coherence: kingston against fez ⟨X0X1⟩ beyond readout is −0.0048.
- Film 16,384 with Nc = 4,096 (225 s, spare exactly a quarter) is also larger.
- "24,576 … does not fit now" is true of the film shape only.
- Fix: say "of the film designs", and add one sentence on the unequal split's trade.

**4. Per item**

**Item 1: W1 to W5 and notes a to l**
- **W1:** 0.0438 and 0.0040 match `isolation_v0.out.txt` (0.04380713 and 0.004011). They are applied at line 159 only.
- **W2:** `:1701` at line 1468 and in the instrument comment (line 57). VALIDATION.md:1701 reads "leaving 247 of the 600". The 65 charges sum to 353.
- **W3:** at M = 9 and M = 31, model (a) is highest at ε = 0.05 and model (c) at ε = 0.10 (`sufficiency_v0.out.txt`).
- **W4:** line 1367 is correct.
- **W5:** the output prints `('gate','rzz',(65, 66),'gate_error'), 0.0028724… -&gt; 1; not on the chain 0..15` for both orders, at both marrakesh snapshots. Marrakesh's chain is exactly 0 to 15. The README's appended line matches.
- **Notes a, c to g, i to l:** all applied. I checked the gate lists directly for note k: kingston's use (65, 66), marrakesh's and fez's do not. For note g, `general` shows 0 value differences, with 352 of 449 re-dated. `general_qlists` is identical.
- **Note b:** section 3 is correct. I read ibm_backend.py:141-165, :316 (configuration refresh) and :367 (history), and base_primitive.py:155-208 and api/rest/runtime.py:95 and 122-123. Section 15 was missed (X6).
- **The lead's transcription:** it matches draft 4's text on every line reference and number (W3's 8.7/22.3 s against 10.3/23.3 s included). No defect there.
- **Note h (the MANIFEST gate).** I planted an unlisted file, a listed file removed, a rename, and a file in a subdirectory. All were refused with the names listed. An edited snapshot or an edited MANIFEST is also refused. With the set test removed, an unlisted extra snapshot passes silently and a removal gives a bare FileNotFoundError, so the new test is what refuses them.

**Item 2: section 9.1**
- **(a) Costs.**
  - Charges are 2 s for 1,024 shots (31 jobs), 4 s for 8,192 (3 jobs) and 9 s for 24,576 (31 jobs). The models are (a) 0.366 ms a shot, (b) 1.687 s + 0.297 ms a shot, (c) 2 s + 0.35 ms a shot.
  - All 15 designs match the instrument exactly (180 to 216 s for the chosen one). Two a window leaves 168 s spare, and 216 ≤ 247.
  - Rounding up adds at most 12 s over unrounded sums. It is a conservative convention, not a worst case. The v0 data fit "charge = whole-second(circuit time + fixed overhead)" under ceil, nearest and floor alike, and every fit predicts 162 s for the unit.
  - The real uncertainty is the extrapolation: the 49,152-shot film job is twice v0's largest job (24,576 shots). Under the ceil reading, per-PUB overhead is at most 0.23 s.
  - HARDWARE.md:15-19 supports the first and third bullets but not "three devices" (X3).
- **(b) The recipe.**
  - The known answer plus its complement covers both readout directions on every chain qubit, and neither is its own mirror.
  - runtime 0.50.0's `sampler.py:129-136` warns only when PUB shot counts differ. One count per job respects it, and `validate_classical_registers` is per-PUB.
  - "Interleave by construction" is true of submission order when each job is awaited. Queue waits can stretch rounds to hours. A failed, retried or offline-device job breaks the K M F order. 9.1 never says how a unit shows its order afterwards (note N1).
  - The BELIEVED label on "compile can stay EQUAL" is honest, if understated. v0's 28 sheet bundles reproduced their gate lists on a pinned chain.
- **(c) Projections (independent Decimal reimplementation, own Bareiss weights).**
  - Kingston against fez ⟨X0X1⟩: certified difference 0.02816 (shown 0.0282). ρ = 0.05848 × 0.30441 + 0.00018 + 0.00029 = 0.01827, so beyond readout is +0.00989 (shown +0.0099).
  - The other two designs give 0.0229/+0.0044 and 0.0345/+0.0164. Planning ε is 0.126, 0.1136 and 0.0989 (three-way).
  - The pooled-k table matches for all cells, including the 24,576 block. For kingston against fez it reads 1, 2, &gt;100, 1 (1), 3 (16).
  - The family of 72 is right for what the instrument computes: 15 pooled, 45 job-level and 12 readout bounds. The Hellinger test is a separate α per object. A pooled look uses 27 intervals at α/2, a different family from the one-unit 72.
  - Every projected verdict is marked as a projection except X1.
- **(d) Anytime validity.** See X2. The per-unit α is labelled per unit, but nothing prevents unit-granularity claims from mixing them.
- **(e) Pooling.**
  - Hoeffding 1963 Thm 1 holds for independent, non-identical [0, 1] variables with μ the average of the means. "Applies unchanged" is correct, including conditional on in-scope counts.
  - What changes is the target: it becomes the mixture of the units that arrived. That needs complete units and EQUAL compiles to compare devices.
  - The strong form at unit granularity excludes between-unit separation failures. It does not exclude within-unit job movement. v0's job deviations (0.014 to 0.024) are comparable to the 0.0518 kingston–fez difference.
- **(f) Signed readout bound.**
  - I derived the claim and agree with it. The widening is (α_A − α_B) − (1 − φ_A)P_A + (1 − φ_B)P_B ≤ |α_A| + |α_B| + g_B·P_B, using P_A ≥ 0.
  - Positivity is computed correctly: `true_lo = lo − a_max &gt; 0`. The values of g_max and a_max follow from the certified upper bounds, because |a_q| ≤ max(up01, up10) and f_q ≥ 1 − up01 − up10.
  - A property test over 252,618 random certified cases found 0 unsound results, with a minimum slack of 0.0035. With the positivity guard removed, 154 of 359,266 cases were unsound.
  - "About half" is 51% for kingston against fez (0.0178 of 0.0350). That holds for v0's devices, not in general.
  - The kind `conditional` is stated at lines 1183-1184.
- **(g) Contributions from anyone.** The trust model is coherent with rule 1, rule 3 and section 8's fabricated-run limit. Leave-one-contributor-out flags verdict dependence on a handle. It does not bound a person (see N10).
- **(h) Standing pre-registration.** It removes `selector-late` only for what it names (N9). The planning ε for M = 9 with 16,384 shots and R = 0.0335 is 0.1136 (shown 0.114), so ε = 0.12 is supported for the three-way class only. The crystal count needs 0.161.

**Item 3: knock-on changes**
- **Consistent:**
  - the quantum-comparable level and the unit's control job;
  - section 8's ρ wording;
  - question 9's shape, cost and cost models, with the cited lines HARDWARE.md:28-29 and VALIDATION.md:1701 verified;
  - questions 15 and 16;
  - parcel P5;
  - the section 12 limit;
  - the header, including the `c43b0f51…` hash and "Next".
- **Inconsistent:** X4, X5, X6, X7. All section and question cross-references resolve, and the tables are well formed.
- **Levels' planning clause:** satisfied at ε = 0.12 for the three-way class only.
- **Section 8's ρ:** "takes only the shrinkage of the device that reads lower" omits the two offsets of about 0.0005. Also, "beyond readout" (difference less ρ) is not "isolated as quantum" (strong form less ρ). Neither 9.1 nor item 7 says so.

**Item 4: instruments**
- **Reproduction:** the five outputs are byte-identical on the original tree and on the fresh clone with copied `records/`. Python is 3.12.9, run with `-I`.
- **Git gate:** all five refuse on a dirty tree and on a moved HEAD.
- **Data plants (git gate bypassed in instrument copies).**

  | Plant | Result |
  |---|---|
  | law charge 9→10 | output changed (12 lines) |
  | law charge 9→8, known-answer 2→3, coherence 4→5 or 4→3 | one printed line changes each (the slope in model b) |
  | misfiled metrics, three variants | refused at the job-id tie |
  | a metrics file removed | refused by `len(points) == 65` |
  | freeze readout +0.01 or +0.0005 | output changed |
  | freeze readout +1e-6 | unchanged (below printed precision) |
  | coherence count, 1 or 5 shots moved | output changed |
  | law count, 3 shots moved | output changed |

- **Code plants.**
  - Changed the output: KL (7 variants), the α schedule (8 variants, in section 3 only), `beyond_readout` (8 variants), cost rounding (4 variants), and family size, R and shapes.
  - Unchanged: C5g was an equivalent mutation, not a fault.
- **Checks that cannot fail on this output:**
  - the `true_lo &lt;= 0` guard in `beyond_readout` (its removal changes nothing);
  - the B-above-A branch (its numbers are never visible);
  - the typed `LEFT_NOW = 247`, though Σ charges = 353 would give it;
  - the typed R_V0 values (0.0335, 0.0346);
  - the "on the chain" branch in the calibration instrument (hard-wiring "not on" leaves the output identical);
  - the `len(data) != bytes` test (redundant with the hash).
- **Audit:** the rest of `free_tier_unit_v0.py` and the changed parts of the calibration instrument are correct. The docstring-only changes to the other two cannot be diffed (no draft-4 copy), but their output hashes are unchanged.

**Item 5: sweep**
- No stale figure besides X5. The `isolation_v0.py` docstring still says "draft 3", which is accurate.

**Item 6: privacy**
- HonestHarness's `path`, `address` and `key` patterns, executed from the text of `tools/check.py`, give 0 hits across the draft, 7 instruments, 5 outputs, `records-README.md` and the 142 files of `records/2026-10-14/`. The CRN, token-shape and e-mail patterns also give 0 hits.
- `user_id` hits are key names only: draft lines 583 and 1014, README line 39, and one line in each of the 65 refetch job records (`ibm_job_omitted_keys`).
- `apikey` and `bearer` hits are the guard regex and a file name in `ibm_refetch_v0.py:74,142` and `ibm_results_refetch_v0.py:57,97`. No values.

**5. Notes**

- **N1 (interleaving).** Add a sentence: a unit shows its order from the jobs' created times (anchored for the owner). Name what a missing, retried or out-of-order job is called (`unit-incomplete`, `not-interleaved`) and add a section 11 control. A pooled "device's, not device's-and-time's" verdict depends on it.
- **N2 (readout model).**
  - The zero single-site-mean assumption is stated only for "the law" in `v0_timing_and_drift.py`.
  - v0's XX jobs measure single-site ⟨X⟩ of +0.07/+0.06 (kingston), +0.15/+0.13 (marrakesh) and +0.06/+0.08 (fez), with SE 0.016.
  - The dropped cross terms are about 5 to 10 times the a_a·a_b term the draft keeps.
  - My estimate puts kingston against fez at +0.0091 (plug-in |a|) down to +0.0042 (certified |a|, 0.03 slack), still positive.
  - The notation a_A and a_B is undefined. The model's formula appears only in the instruments, not in 6.1.
- **N3 (plug-in noise).**
  - The coherence plug-ins are single 4,096-shot jobs: SD 0.015 per parity, about 0.021 on a difference.
  - Several pooled cells rest on differences v0 cannot resolve, such as kingston against marrakesh ⟨X0X1⟩ at 0.018.
  - Under that noise the one-unit "+0.0099" has roughly 70% credibility. It is about 95% under unit sampling noise alone.
  - The Labels (lines 1079-1085) omit R = 0.0335 as a plug-in, and "Everything below is PROPOSED" sits beside a READ bullet.
- **N4 (strong form claims).**
  - The instrument prints strong forms for the law measures only. "No measure clears it" for coherence is true a fortiori (at most −0.065 even with zero drift) but not printed.
  - "Per-job statements would need far more shots" is unlabelled. My estimate is about 152,000 law shots per film job (9.3 times) for kingston against fez on the five-crystal share alone.
- **N5 (standing pre-registration).**
  - It also does not cover subsets (leave-one-out, by contributor or date), new measures, or the agreement tolerances (question 16).
  - Its git order is REPORTED, not anchored.
  - Name the Hellinger object. The crystal count needs 0.161 at 16,384 shots, so 0.12 supports the three-way class only.
- **N6 (leave-one-out and identity).**
  - A `withheld` unit has no grouping key.
  - A flip at small k is mostly a sample-size effect.
  - The handle is not in rule 3's Carried list, whose heading is "identify the run, not the person".
  - "Reference set" is undefined.
  - ANCHORED "for them" is a reader-relative kind that rule 5 cannot hold as data.
- **N7 (completeness).** Require complete units, or the kingston and fez pools average over different units.
- **N8 (P5).** Its "unit whose known answer fails" control is not in the section 11 table, and `bundle.py`'s PLAN and `check` hold v0's job shapes. The runtime's primary source for the shot rule (`sampler.py:129-136`) is not in section 15. State job mode.
- **N9 (mechanics and wording).**
  - "Under one calibration" (line 1099) is unlabelled.
  - The sentence "no difference either" (lines 496-498) holds for values only.
  - Section 15 does not mention the new file-set test.
  - The word "round" is used for both a work round and a unit's rounds.

**6. What I did not do**
- I did not contact IBM or Atlas, and I created no service or account object.
- I did not run the two refetch tools, and I opened no credential, key, token or account file. Under `.venvs` I read only the `qiskit_ibm_runtime/*.py` files you named.
- I did not run `tools/check.py` itself, only its patterns.
- I did not diff the draft-4 versions of the changed instruments (none in the packet).
- I did not re-derive unchanged sections (1 to 5, 7, 10 to 12, 16.1 to 16.4) beyond references, figures and stale-term greps.
- I did not check the external papers or Hoeffding against their texts (no network), and I did not run a coverage simulation of the α schedule.
- I did not plant faults in `v0_timing_and_drift.py`, `sufficiency_v0.py` or `isolation_v0.py` beyond the git gate.
- I tested Python 3.12.9 and CRLF output only.

**7. In the brief**
- It uses a_A and a_B for the device-level offsets, while the model uses a_a·a_b for qubits. The draft does the same. I read a_A as the instrument's `ra["a"]`.
- "An unlisted removal" is ambiguous. I planted a file absent from the MANIFEST, a listed file removed, a rename, and a file in a subdirectory.
- "Run tools/check.py's patterns" was done by executing the pattern text, not the script.
