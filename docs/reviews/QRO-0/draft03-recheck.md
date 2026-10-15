# Verifier report: QRO-0 draft 3

## 1. Bottom line

**NOT READY.** I found eight defects, V1 to V8. Each is a local correction. None needs a redesign.

These stand as written:
- The IBM reads (section 4.5).
- The certified intervals and the strong form (sections 6.1 and 8). I reimplemented them independently and got identical numbers.
- The section 16 readings of the paper.
- All four analysis outputs reproduce byte for byte.
- Privacy is clean.

## 2. Setup

**Hashes.**
- `sha256sum -c SHA256SUMS.txt` gives 13 of 13 OK.
- The live `QRO-0.md`, the six instruments and four outputs are byte-identical to the frozen copies.
- The two MANIFEST hashes equal the draft's `1761adbb…` and `59ac54a2…`.
- The paper's tarball, PDF and supplement hashes equal `d4c3ce3e…`, `59fb7293…` and `3d8a20cf…`.

**Trees.**

| Tree | State |
|---|---|
| moth-quantum | 3a73823, clean |
| HonestFramework | 65447fd, clean |
| ParcelRound | local 8767e23, `origin/main` f42242e, 37 commits behind, clean |
| HonestHarness | b69ed76, clean |
| QRO-Crate | no git; 153 files, `QRO-0.md` hash unchanged |
| cft-fp256 | see below |

cft-fp256 was at f22e8d2 when I started. It is now at c918cb3, committed 2026-10-14 09:40 -0700 by other activity, not by me. The tree is clean. `git diff --quiet f22e8d2 HEAD` shows every cft-fp256 file the draft cites is unchanged, so my citation checks hold at the pinned commit.

**Method.**
- I ran every script with `python -I`, standard library only. No virtualenv was needed.
- I set `GIT_OPTIONAL_LOCKS=0` for every git call, including the instruments' own `git status`.
- Everything I wrote is under `…\scratchpad\verifier-QRO0-r3\work\`:
  - `scripts\`: my scripts;
  - `out\`: my outputs;
  - `plants\`: the planted-fault copies;
  - `mq\` and `mq2\`: `--no-hardlinks` clones of moth-quantum;
  - `qro_copy\`: a copy of `records\`.

## 3. Defects

**V1. `before-first-shot` as defined is not what v0's links are** (575–582; also 568, 637, 438–447).
- The definition is "the newest snapshot stamped before the job's first shot, whose newest per-value measurement date also precedes that shot".
- The records link each job by IBM's history lookup at the first shot, `be.properties(datetime=first_shot)` (`ibm_refetch_v0.py:148–162`). That lookup is not keyed by stamp, and the draft says so at 579.
- I applied the written rule to the 7 carried snapshots (`scripts\link_def.py`). It selects 12:21:18Z for 8 kingston jobs whose recorded link is 11:28:27Z. Their first shots run 12:26:17 to 12:29:52Z:
  - `db1pd9ivog1s73fifp5g`, `db1peuivog1s73fifr1g`, `db1pfabid5ic73erg000`, `db1pfjivog1s73fifrr0`;
  - `db1pfrrid5ic73erg0og`, `db1pg26egvvc73bhvrig`, `db1pg9avog1s73fifspg`, `db1pgf3id5ic73erg1l0`.
- For those 8 jobs, 12:21:18Z has its stamp and its newest value date (12:24:06.7Z) before the shot. IBM returned it only for a query at 12:30:44.6, not at 12:30:20.6. Its history key therefore lies at least 9 minutes after its stamp. The guard "newest per-value date precedes" (2.2–4.0 minutes after the stamp) does not cover that lag.
- Consequences:
  - "v0's calibrations linked `before-first-shot`" (568, 637) is false for 8 of 65 jobs as defined.
  - "differs from `before-first-shot` on 1 of 65" (581–582) is 9 of 65 under the written rule. The ninth is the crossing job.
  - The 4.5 table's kingston counts, 10 and 6, would be 2 and 14.
  - No control exercises the "newest" clause. `calibration-late` (1044) covers only "stamped or measured after". A checker built to the definition would refuse v0's own IBM crate on 8 jobs.
- Fix: define the link as what the tool computes. For example: "the snapshot the provider's history returns for a query at the first shot, checked to have its stamp and newest value date before it; the history key lags the stamp by at least 9 minutes". Or relink the 8 jobs and add a control for the "newest" clause.

**V2. "The morning law jobs ran … interleaved" is false** (400–401; 568 "morning jobs interleaved"; 962 "its sheets are not interleaved").
- The nine morning jobs' created times, from the committed job lines (`scripts\order.py`):

| Device | Created times (UTC) |
|---|---|
| kingston | 10:26:56, 10:27:16, 10:30:29 |
| marrakesh | 10:32:42, 10:33:06, 10:33:33 |
| fez | 10:33:55, 10:34:14, 10:34:41 |

- The order is K K K M M M F F F. That is blocks, which Q9 (1192) defines as the opposite of "A B C A B C…, not blocks". The sheets are blocks too: K 12:21–12:37, M 12:38–12:49, F 12:50–12:58.
- Row 6 says "Device is separated from time only by interleaving" and then credits the morning jobs.
- The word is new in draft 3. It came in with the R7 fix.
- Fix: "one law job a device, each device in its own short block, K then M then F; they do not separate device from time either". Make the same change in 9 (962).

**V3. "One status per cause" does not hold in 6.1** (627–646; claimed at 559, 1178 and 1546–1549).
- Drift gets two statuses at 641–643: CONTROLLED for the law measures, UNMEASURED for the coherences.
- The SHARED bullet (644–646) lists the decode, the known-answer pattern and the date. They are not among the seven causes, and they sit inside causes that already carry a status: cause 1 is EQUAL, cause 5 is UNMEASURED, cause 6 is DIFFERS.
- Section 6 (559) and Q3 (1178) say "per comparison". Section 8 (802, 810) computes statuses "for each measure".
- Section 8 says UNMEASURED comes "with its absence word" (811). 6.1's UNMEASURED readout and drift give none.
- Fix: say "per cause per measure" everywhere. Give the per-measure drift statuses. Give UNMEASURED its word. Move the SHARED items to a separate unseen line.

**V4. "IBM's 0.50.0 interface does not [name the calibration a job ran under]" is broader than what was read** (575–576, cited to section 3).
- Section 3 (309–319) shows only that `properties()` is a client-side timestamp match.
- The runtime carries `calibration_id` in several places:
  - `ibm_backend.py:141,237`;
  - `qiskit_runtime_service.py:587`;
  - `base_primitive.py:155–175`;
  - `api/rest/runtime.py:95,122`, which posts it with the program.
- Peltonen et al., which the draft cites, tabulate "Calibration identifier … `calibration_id` when present" for IBM.
- The draft's own 4.3 row (368) and `ibm_refetch_v0.py:78` treat it as a metrics key that is absent in 0 of 65 jobs.
- Section 15 lists `base_runtime_job.py`, `ibm_backend.py` and `converters.py` as read. The files carrying `calibration_id` are not among them. The flat negative is BELIEVED, not READ.
- Fix: "`properties()` is a client-side timestamp match; IBM's metrics carry an optional `calibration_id`, present in none of v0's 65 jobs; whether a requested one is echoed was not tested". Add requesting and recording a calibration id to Q9.

**V5. The "moved" comparison has an unstated baseline, and the instrument mislabels it** (438–462; `calibration_at_execution_v0.py:5–6, 87, 97–98`).
- Every execution snapshot is compared with the device's morning-bundle freeze. The output prints it as "frozen against 06:57:43Z", and the docstring says "the snapshot its bundle was frozen against".
- The 56 sheet jobs belong to bundles whose manifests name other targets: kingston 11:05:15Z, marrakesh 09:51:18Z, fez 10:08:31Z.
- So "frozen against" is wrong for 56 of 65 jobs.
- "Kingston's sheets ran under a calibration that had moved" (459) is true against the morning freeze. Kingston's own sheet freeze (11:05:15Z) is in no record, so movement since it is unmeasurable.
- Line 462, "the calibration in force differs as well as the device", should say kingston's calibration changed during the day and fez's did not.
- Fix: state "since the morning freeze" and fix the docstring and print.

**V6. Four of the twelve inverted shot counts are one shot short of the stated rule** (1206–1207, 1454–1461; `sufficiency_v0.py:151–154`).
- The counts print with `{:,.0f}`, which rounds to nearest. The rule needs n ≥ c/(−ln(1−x²)), so the sufficient integer is the ceiling.
- `scripts\reimpl_suff.py` gives exact values and ceilings:

| Count | Exact value | Printed | Ceiling |
|---|---|---|---|
| crystal count, Eq. 13, ε = 0.05 | 294,579.25 | 294,579 | 294,580 |
| crystal count, planning rule, ε = 0.05 | 1,178,343.28 | 1,178,343 | 1,178,344 |
| crystal count, Eq. 13, ε = 0.10 | 16,364.11 | 16,364 | 16,365 |
| crystal count, zero-risk floor, ε = 0.10 | 28,023.36 | 28,023 | 28,024 |

- At the printed integers the inequality fails. For 1,178,343, 4η = 0.015423768, above the allowed 0.015423766.
- The other eight figures equal their ceilings. The instrument's own cost lines already use `math.ceil` (175–177).
- "Each rule is inverted exactly" (1452) holds for the real number, not for the count.
- Fix: print ceilings. In Q9, 1,178,343 becomes 1,178,344.

**V7. "Only the stamps had moved" and "only the stamp changed" are false in letter** (133–136, 476–477; records README 68–72).
- In the same paragraph, 2 of 6,230 marrakesh values changed. They are `rzz` `gate_error` on coupler (65,66), 0.00287 to 1, and not on the chain.
- Per-value dates moved on 1,922 to 1,984 values, which 4.5 (450–454) itself says. On kingston's morning snapshot, 1,956 dates moved and 0 values.
- The records README repeats the loose forms:
  - README 68–69, "the values did not move on any device", contradicts its own table, which shows marrakesh with 2 values changed.
  - README 70–71, "re-dates 1,900 to 3,300 of its values without changing them", is false for kingston's later snapshots. They re-date 2,640 and 3,316 values, and 342 and 680 of those changed (`scripts\redate_overlap.py`).
- Fix: "the reported values did not move on kingston or fez; two unused-coupler values moved on marrakesh; the stamps and 1,922–1,984 per-value dates moved".

**V8. A READ citation no longer supports its bullet** (1099–1100).
- The bullet is "Cover other providers or modalities, mid-circuit measurement or feed-forward (cft-fp256, docs/CERTIFICATES.md:3371–3376, READ)".
- Those lines say version 1 does not certify deposits, lane masks, index tables or streams that change from segment to segment.
- Draft 2 (1107–1109) said exactly that. Draft 3 compressed it, so the READ label now attaches to the whole bullet.
- Fix: restore "cft-fp256's certificates cannot yet express streams that change per segment (…, READ), and this design takes on no more".

## 4. Per item

### Item 1: R1 to R12 and the previous report's notes

- **R1.** Present and correct (388–393): 0.73, 0.93, 1.58, 1.68 against the instrument's 0.731672, 0.937854, 1.583829 and 1.680952.
- **R2.** Verbatim against `supplementary-v2.txt:763–764` (1356–1357).
- **R3.** The list (1240–1255) now covers the five groups R3 named. It omits draft 3's own new decisions (note N9).
- **R4.** The ladder and "where v0 stands" (937–964) are coherent. Nothing named "isolable" remains.
- **R5.** Present in 6 and 8. The U(D) mathematics is sound. See V3 and notes N3 and N8 on the wording around it.
- **R6.** DIFFERS (564, 629–631). I recounted the gate lists: sx 257, 251 and 249; cz 102 each; byte-identical across all 4 roles in every bundle of a device.
- **R7.** Present in 4.4, 6, 6.1, 8, 9 and 11. Its fix introduced V2.
- **R8.** Present (88–93, 196–199). See note N10.
- **R9.** Present (296–304).
- **R10.** Present in 8 and 16 (855–860, 1329–1335, 1406–1407). Section 0 no longer says anything on composition. The "0" in 1495 is stale (note N12).
- **R11.** Present (736–739).
- **R12.** Present in 4.2 (354), 4.5 (426–428), 10 (1021–1022) and 11 (1043).
  - The `qpy-only` control is refused through the commitment in IBM's copy, because a re-sealed commitment differs from IBM's.
  - The re-fetch ties IBM's executed circuit to the held gate list. The committed QPY file is tied to it only through the commitment's hash.
- **Notes.**
  - I located all 25 "taken" notes (1499–1536). None is unanswered.
  - I also checked these against sources: 598–601 (0.52 to 6.29, recomputed); 1359–1361 (Enodo page now: "CC-BY-4.0 unless defined otherwise", 341 files, 20.00 MB, uploaded 06/10/2026); the arXiv dates and licence; 1377–1385 (verbatim, and `SoilandReyes2022` is the RO-Crate paper); 287–288 (Peltonen).

### Item 2(a): the IBM reads (`scripts\recount_ibm.py`)

**What I recounted.**
- **MANIFESTs.** 72 and 65 files listed, equal to what is on disk. All hashes and sizes match.
- **Created times.** 65 of 65 equal the committed job lines. I compared instants, because IBM drops trailing zeros in its microsecond strings.
- **Commitments.** 68 of 68 are equal in IBM's copy, the line and the manifest.
- **Gate lists.** 68 of 68 PUB booleans are True, all noted "compared with layout".
- **Shots.** 68 of 68 equal the manifest.
- **Options.** 65 of 65 equal the manifest. The full options dict is equal, not just the three paths.
- **Raw results.** All 65 are recorded `bytes_equal`.
  - The recorded committed hash equals my own hash of moth-quantum's `*-raw.json`.
  - It also equals the git blob and the recorded IBM-copy hash, 65 of 65.
  - This machine has `core.autocrlf=true`, so I checked blob against working file explicitly.
- **Logs.** All 130 job lines in the two logs agree with the records.
- **`user_id`.** It appears in each of the 65 job records only as an omitted key's name.

**Was a gate list compared with IBM's copy of every circuit, or of some?**
- Every circuit IBM holds: 68 of 68, one per PUB.
- The 31 manifests list 124 circuits, 4 each. The 28 sheet bundles list coherence pairs that were never submitted, which is 56 circuits. IBM holds no copy of them.
- Their gate lists are byte-identical to the morning bundle's, which IBM's copies do equal. The draft's wording ("every circuit IBM holds") is exact.

**What the records establish.**
- IBM's copies as of 2026-10-14 contain the committed commitments, shots, options and raw bytes.
- IBM's circuits have the held gate lists.

**What they do not establish.**
- The records keep booleans, not IBM's gate list or a digest of it. The 68 of 68 cannot be re-derived offline.
- The MANIFEST field `moth_quantum_commit_files_read` is a path description, not a commit. The results MANIFEST has none. "3a73823" rests on the README.
- Nothing shows what the device measured.
- A third party without the owner's key cannot repeat the fetch.

### Item 2(b): calibration (`scripts\recount_cal.py`, `link_def.py`)

- **The 7-row table.** My counts equal the instrument's:
  - kingston: 3, 10 and 6 jobs, with 0, 342 and 680 values differing;
  - marrakesh: 3 and 20 jobs, 2 values each;
  - fez: 3 and 20 jobs, 0 values each.
  - I also compared the 449 `general` and 97 `general_qlists` entries: 0 value differences, and the key sets are equal.
- **Re-dating.** The counts are 1,956, 2,640, 3,316, 1,984, 1,984, 1,922 and 1,922. The five in force for morning jobs and for all marrakesh and fez jobs re-date 1,922 to 1,984 values each and change at most 2.
- **"2.2 to 4.0 minutes".** The newest value date minus the stamp is 2.21 to 4.04 minutes. The instrument prints the timestamps, not the minutes.
- **The crossing job.** `db1pgmjid5ic73erg1u0`: running 12:30:20.6 gets 11:28:27Z, first shot 12:30:44.6 gets 12:21:18Z. Correct.
- **Prediction snapshots.** The marrakesh (08:32:46Z) and fez (08:38:44Z) prediction snapshots are value-identical to their freezes. There are 0 value differences and about 1,980 and 1,922 re-dated entries.
- **Readout ages.** Kingston 7.03 to 7.11 h, marrakesh 7.77 h, fez 10.48 h. Correct.
- **Clauses of the link.** All 65 jobs satisfy both clauses of `before-first-shot` for the snapshot recorded, with a smallest margin of 6.6 minutes. Only the "newest" selection fails (V1).
- **Runtime 0.50.0 source.**
  - `RuntimeJobV2.properties()` takes `running`, or the creation date if `running` is missing, converts to local time, and calls `IBMBackend.properties(datetime=…)`.
  - That call sends `updated_before` to the REST endpoint (`api/rest/cloud_backend.py:74`).
  - The tool's `before_running` is therefore equivalent, though it was not called through `job.properties()`.
  - The citations 199–214 and 325–376 are right (the datetime path ends at 376).
  - "Keyed by storage time" is an inference from the history's behaviour, not something the source says.

### Item 2(c): the adopted standard and 6.1's verdicts

- **Hoeffding's KL form.**
  - Hoeffding 1963 Theorem 1 covers independent, non-identical [0,1] variables, with the true mean taken as the mean of the means.
  - I checked it exactly by Poisson-binomial convolution (`scripts\hoeffding_exact.py`). Of 5,739 tail events over 300 random non-identical mixtures, 0 violate P(X̄ beyond x) ≤ exp(−n·kl(x‖μ)). Reversing the arguments fails 1,485 times, so the instrument's orientation `kl(observed‖candidate)` is the valid one.
  - A Monte Carlo of pooled coverage (`scripts\mc_cover.py`) missed at 0.4% to 0.6% against 5%.
- **M = 70.**
  - M = 3×(9+11+2) + 2×2, and the budget is ln(2·70/0.05) = 7.9374, each interval two-sided at α/M. This is right.
  - The difference and the drift bound derive from intervals already in the family and add no new interval.
- **The maps.**
  - X = W/2304 lies in {0, 1/9, 4/9, 1}, because the maximum P is 9/4096.
  - The linear XEB F is affine in E[X].
  - The parity map X = [the two bits agree] with ⟨PP⟩ = 2E[X] − 1 is right.
- **U(D).** It is the corner maximum max(hi_j − μ_lo, μ_hi − lo_j). It is defined identically in 6, 6.1, 8 and the instrument.
- **The strong form.**
  - By the triangle inequality, if L(|diff|) − U(D_A) − U(D_B) &gt; ε then every job pair differs by more than ε. This holds on the event that all intervals cover.
  - It speaks of the jobs' true expected values, not their realised values.
  - For the measures over five-crystal shots, the pooled target weights jobs by their realised five-crystal counts. "The day's mean over its jobs" (776–778) is exact only for the all-shot measures. The weighted and unweighted means agree to 4 decimals here.
- **Independent reimplementation** (`scripts\reimpl_intervals.py`, Decimal at 60 digits and a Bareiss integer determinant). It reproduces every number in the 6.1 table: the five-crystal share, forbidden share and XEB intervals, the drift bounds, the strong forms, and the ⟨X0X1⟩ and ⟨Y0Y1⟩ intervals.
- **ε = 0.**
  - It is consistent with the verdict rules, but "agree" can never be certified at ε = 0, because U(|diff|) &gt; 0. The verdicts reduce to differ or unresolved.
  - `selector-late` (794–798) names only selectors. 6.1 (622–625) applies it to the tolerance.
- **Statuses.**
  - Sampling fits the definition of CONTROLLED.
  - Drift fits the definition (a certified bound exists). Row 7's "needs repeats and enough shots" suggests the bound must be informative. The draft should pick one reading (N3).

### Item 2(d): time-block consistency

| Section | Result |
|---|---|
| 0 (items 4 and 6), 2 (219–223), 6.1, 8 (823–824, 849–851), 11 (1056), 12 (1074–1081, 1092) | consistent |
| 4.4 (400–401), 6 row 6 (568) | V2 |
| 9 (961–963) | understates: no campaign job is interleaved |
| 8, fifth bullet of "isolated from the pipeline" | "interleaving, or the statement says …" is a qualifier that can never fail (N18) |

For "one status per cause" in 6.1, see V3.

### Item 2(e): QPU charge and planning figures

- **Charge.** `law-metrics.json` shows 9 s for all 31 law jobs. The repository holds three charge levels: 1,024 shots at 2 s (31 jobs), 8,192 shots at 4 s (3 jobs) and 24,576 shots at 9 s (31 jobs). Execution time is a steady 264 µs a shot.
- **The estimate's direction.**
  - The draft's through-origin scaling gives 167 s and 432 s.
  - A two-point line through the repository's data gives 137 s and 352 s.
  - `docs/HARDWARE.md:28` ("about 2 s plus about 0.35 ms a shot") gives 162 s and 414 s.
  - The draft's figures are the highest of the three, so the direction is safe.
- **Arithmetic.**
  - 9 × 167 = 25.1 minutes, which is two and a half windows.
  - At ε = 0.10, 9 × 10.3 s = 1.55 minutes.
  - Both are "about" correct under all three models: 20.6 to 25.1 minutes, and 1.5 to 1.8 minutes.
- **Quotation.** `docs/HARDWARE.md:15` is exact: "10 QPU-minutes per rolling 28 days".
- **Inversions.** Eq. 11, 12 and 13 are numbered right. The inversions are exact in the real number and follow the paper's rule (`reimpl_suff.py`). Rounding is V6.

### Item 2(f): question 14

- Unsupported for the morning run: confirmed.
  - The 09:02:46Z snapshot has 0 value differences against the freeze across qubits, gates, `general` and `general_qlists`.
  - It is the snapshot IBM returned for all three morning jobs.
  - "Overstates" is the right word. The stamp and 1,956 dates did move.
- The sentence at `HARDWARE-RESULTS.md:194` is true of kingston's sheets, where 342 and 680 values moved. Q14 should say so.
- Nothing else in that document's calibration claims is contradicted:
  - 57 (ESP order);
  - 56 ("kinder than its device");
  - 204 (`properties-&lt;stamp&gt;.json`).

### Item 3: the instruments

- **Reproduction.** The four outputs are identical to the frozen outputs, on the original tree and on a fresh `git clone --no-hardlinks` plus a copy of the records (`scripts\run_inst.sh`).
  - sufficiency: `12266ff3…`;
  - timing: `3d461f9f…`;
  - isolation: `c6f042d2…`;
  - calibration: `0d1a3c37…`.
- **Pins.** A dirty tree, an untracked file and HEAD~1 are each refused, exit 1, by all four instruments.
- **Plants.** I planted 58 faults in copies (`scripts\plant.py`):
  - 39 change the output;
  - 6 exit 1 (the kernel and cosine plants, a dropped sheet job, `usage["value"]` for the charge, the XEB formula against the HARDWARE-RESULTS hold, and a bad variable name);
  - 13 leave the output unchanged.
- **The 13 unchanged.**
  - Five are removals of assertions, which cannot change output.
  - Others are equivalent mutants or insensitive on v0's data:
    - **S15**, a `fail` boundary `&gt;` to `&gt;=` that never hits equality;
    - **S19**, a relabelling of the three-way classes;
    - **C12**, because the two inputs are equal on v0's data;
    - **C9**, because it falls below the print precision;
    - **S9**, `floor` against `ceil` in a whole-second print;
    - **S7**, `max` against `min` of the charges, which are all 9;
    - **C1**, the prediction baseline swapped for the freeze, unchanged because they are value-identical on v0's data;
    - **C8**, the stated p01/p10 swap.
- **Checks that cannot fail.**
  - `assert len(charges) == M` (`sufficiency_v0.py:168`) compares a count with itself. Both loops walk the same runs, so a missing file raises before it.
  - The `len(W) == 4368` conjunct (`sufficiency_v0.py:74`, `isolation_v0.py:81`) is the constant C(16,5). Its other conjuncts do fail.
  - The `max(charges)` aggregator is degenerate on this data.
- **The prediction-snapshot comparison.** It is insensitive to its baseline on v0's data.
- **Unpinned input.** The calibration instrument pins moth-quantum but not the 2026-10-14 records it reads.
  - A one-value edit to a snapshot changed the output (1 of 6,203 values differ) and exited 0.
  - The MANIFEST hashes would catch it.
- **Data plants in `mq2`.** I committed the plant and patched `want`. A law job charged 10 s changes the rate and costs. Removing a `law-metrics.json` crashes the run.
- **Static audit of the two IBM tools.** I found nothing wrong. They refuse to overwrite, scan for credential and address patterns before writing, and omit `user_id`.

### Item 4: section 16 against the paper

- Section I, as read in 16.2, is verbatim: "does not specify what agreement a second execution should achieve". It lists PROV, packaging, QProv, QC-MM and Qiskit tracking.
- The 16.2 paper-reading bullets (calibration as contextual metadata, missing fields represented, returned order, confounded factors, controls inside every job, prespecification) hold against S4, S5 and section VII.
- 16.3's radii are right: 0.918, 0.341, 0.027, 0.018.
- 16.5's tables reproduce, including the kingston-against-fez ranges 0.0275 to 0.0648 across devices against at most 0.0242 and 0.0236 within.
- The paper describes no commit, hash or timestamp establishing the prespecified order (checked by grep of the source and supplement).

### Item 5: cross-references

I checked all of the internal section and question references against the section structure. All are right. The two exceptions are in the 17 table's "where" column (N12).

### Item 6: reach

See notes N3, N5, N7, N10, N14, and the missing exploratory label on item 6 (N2).

### Item 7: privacy (`scripts\privacy.py`)

- I copied HonestHarness's `PATTERNS`, `ALLOWED_ADDRESSES`, `RESERVED` and `PLACEHOLDER` and ran them over 153 files: the draft, six instruments, four outputs, and all of `records/2026-10-14` including the logs and README.
- **HonestHarness patterns:** 0 hits.
- **Extra greps:**
  - **`user_id`.** It appears only as a key name in 65 job records (line 62 or 73), draft lines 518 and 910, and README line 40.
  - **`apikey` and key-file names.** `ibm_refetch_v0.py:74, 142` and `ibm_results_refetch_v0.py:57, 97`, regex and file names only.
  - **`token`.** `ibm-refetch.log:1` and `ibm-results-refetch.log:1`, a qiskit warning.
  - **`secret`.** Draft line 1133, "holding no secret".
  - **A 36-character UUID.** It appears in each job record (line 75, or 86 for coherence). It is IBM's resource-unit metric id, and it is also in Quantum-Film's committed metrics.
  - **CRN, account id, e-mail, IAM host.** None.
- **Quantum-Film files that sit outside the draft and the v0 records.**
  - `docs/HARDWARE.md:25` carries a home path (`C:\U…`) that the HonestHarness pattern flags. It is a Quantum-Film doc, not a v0 record.
  - The bundle READMEs carry the public repository URL with the owner's handle. Rule 3 now says that is carried.

### Item 8: anything else

See the notes below.

## 5. Notes

- **N1. Mathematics.** Everything in 2(c) above passes.
- **N2. Exploratory label.** Section 0 item 6 (139–150) omits the exploratory label (`selector-late`) that 6.1 and 8 require of this result.
- **N3. Drift wording.** "Every bound is wider than the difference it would have to clear" (642; also 569). For the five-crystal share each U(D), 0.0307 and 0.0323, is below the difference's lower end 0.0438. Only their sum, 0.0630, exceeds it.
- **N4. Planning assumptions.**
  - M = 31 is v0's family. For the planned nine law jobs the three-way counts are 23,771 at ε = 0.10 and 384,659 at ε = 0.05, about 16% lower. 23,771 is below v0's 24,576.
  - R is v0's observed maximum treated as the true risk.
  - Only the nine law jobs are costed.
  - `docs/VALIDATION.md:1700` records 247 of the 600 s left in the window opened on 2026-10-05.
- **N5. Headline shot counts.** Item 7's shot counts (151–163) belong to the Hellinger {device}-record test. They are not an isolation criterion in the semantic form; Q9 (1216–1218) admits that, and the headline should too. At ε = 0.10, v0's cross-device Hellinger distances (at most 0.0804) are already below ε.
- **N6. Records.**
  - README 68–72 is covered by V7.
  - The two MANIFESTs are the only record of the tool versions.
  - Hashes of the IBM-side gate lists are not kept (see 2(a)).
- **N7. Storage time.** "Keyed by storage time" (434–436, 579) is an inference. "`properties()` can name the wrong snapshot" (463) asserts a right answer the records cannot give; they give only a necessary condition.
- **N8. Instruments.**
  - The coherence values are hard-coded at `calibration_at_execution_v0.py:39` and `v0_timing_and_drift.py:197`, and are not asserted against the records.
  - `max(str(date))` at line 116 compares ISO strings. It is right here but would misorder a date with fractional seconds against one without at the same second.
  - A latent `or` in the CZ lookup at line 124 would drop an exact 0.0.
- **N9. The R3-style list (1240–1255)** omits draft 3's own decisions: the `certified` kind, the Hoeffding KL and union-bound family, the strong form, and the time-block qualifier.
- **N10. Headline reach.** "Only what is named as differing can explain a difference" (91–92): an `unknown` factor could differ. Say "is attributed".
- **N11. Atlas.** Atlas sampling CONTROLLED (566) against its sampler being `unexposed` (1096). It is conditional on the same independent-shots model as IBM.
- **N12. Section 17 "where" column.** R10 lists section 0, which has no composition text now. R7 omits sections 0, 2 and 12.
- **N13. "afternoon"** (136): the sheets ran 12:21 to 12:58Z.
- **N14. Item 3's "the values are READ"** (116): the dephased column is BELIEVED (725–729).
- **N15. Open Plan.** The Open Plan figure of 600 s is correct. The window has 247 s left until about 2026-11-02.
- **N16. 17 / 24.** Kingston's 11:05:15Z freeze snapshot is not kept (see V5).
- **N17. Absence words.** UNMEASURED in 6.1 carries none (see V3).
- **N18. The fifth bullet** of "isolated from the pipeline" (823–824) is a qualifier that cannot stop the statement.

## 6. What I did not do

- I did not contact IBM Quantum or Atlas. I did not run `ibm_refetch_v0.py` or `ibm_results_refetch_v0.py`, create a service object, or open any credential, key, token or account file. That includes `~/.quantum-film` and the memory file about the IBM key.
- Because I could not call IBM, I could not re-derive the 68 of 68 gate-list booleans or the byte equality on IBM's side. I verified the committed side and the records' internal consistency.
- I did not open the 341-file Enodo archive. I fetched only the landing page.
- I did not run Quantum-Film's test suite, and I did not install qiskit, Aer or numpy.
- I did not verify Logan's quoted words or permissions, or draft 1's hash and findings D1 to D14.
- I did not read the draft 2 to draft 3 diff end to end. It is a 2,200-line word diff. I located each R-finding and note instead.
- I spot-checked about 45 of the roughly 55 external line citations. I did not re-read all the cft-fp256 ones.
- I fetched only these public pages: the arXiv abstract page, the Enodo landing page, the RO-Crate profiles pages (1.2 and 1.3), Process Run Crate 0.6, and Peltonen's HTML. The RO-Crate release, WRROC, rocrate-validator and the IBM pages I did not re-fetch.
- I did not spawn subagents.

## 7. Anything in this brief that was wrong or unclear

- "gates.json in each moth-quantum bundle": the files are `&lt;circuit&gt;.gates.json`, four per bundle.
- "On a fresh clone": QRO-Crate has no git. I used a fresh `--no-hardlinks` clone of moth-quantum plus a copy of QRO-Crate's `records\`.
- "Not in /tmp": in Git Bash, `/tmp` maps to the Windows Temp tree that holds the scratchpad. I wrote only under the `work\` directory.
- The brief gives no commit for HonestHarness (b69ed76 here), and cft-fp256 moved mid-session (see Setup).
- The brief's question about gate lists compared "with IBM's copy of every circuit, or of some" is answered in 2(a).
