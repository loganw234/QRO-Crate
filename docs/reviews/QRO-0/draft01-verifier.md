# Verifier report on QRO-0 (frozen copy)

**Verdict: not READY.** Every count in section 4.1 reproduces exactly, and most READ citations say what the study says. But I found 13 defects and 6 small wrong statements. Five of them go to the central promise, that a comparison isolates the quantum difference reliably:

- **D1:** the comparison as specified cannot compare two devices of v0's single IBM crate.
- **D2:** "isolated" lets readout differences through into the coherence class.
- **D3:** the worked example marks the submission EQUAL although the study says its server defaults are `unknown`.
- **D4:** the compile control rests on a sample whose seed the producer picked, which the study's own rule 8 forbids.
- **D7:** the MEASURED "at least 1.7 s" clock bound ignores git's one-second resolution.

**Setup.** The frozen copy hashed `06dd0522…e71` (1,081 lines) at the start and at the end. Every tree was at its stated commit: moth-quantum 3a73823, cft-fp256 f22e8d2 (still HEAD), HonestFramework 65447fd. ParcelRound's METHOD.md was read with `git show f42242e` (that is `origin/main`; the local 8767e23 is 37 behind). All four working trees were clean before and after; I edited nothing tracked.

Scripts and outputs are in `<scratch>\verifier-QRO0\work\`. I used stdlib Python with `-I`, no credentials, and no IBM or Atlas API. Every recount below is complete; I sampled nothing.

## Defects

**D1. The comparison cannot address v0's own data** (lines 567, 576-580, 646-655, 449-453, 941-943). This is a false design property.
- Section 8 takes "Two crates, A and B" and refuses any pair that shares a raw result.
- Section 9 puts all three IBM devices into one campaign crate.
- So kingston against fez (6.1) and seam test 2 could only be made as A = B, which `comparison-trivial` refuses. No device or role selector is defined anywhere (grep confirms).

**D2. Readout passes through "isolated" into the coherence class** (167-168, 543-548, 608-611). The design claims more than it delivers.
- CONTROLLED means a control measured the factor, not that its effect was removed.
- Readout error on qubits 0 and 1 attenuates ⟨X0X1⟩ by roughly (1−p01−p10) per qubit.
- Scenario: two devices identical except a total flip rate of 2% against 10% on the pair. Every isolation condition holds, and the comparison reports an "isolated" coherence-class difference of about 0.056.
- So reading (c) does not avoid what section 2 says only (a) suffers, calling a readout fault a quantum difference.
- On v0 the effect is small. Snapshot readout errors give attenuations of 0.9728 (kingston) and 0.9637 (fez), about 0.003 of the 0.0625 difference.

**D3. The submission is marked EQUAL though part of it is `unknown`** (461, against 414 and 307). This is an internal inconsistency.
- Section 8 defines EQUAL as "byte-identical by digest", and a factor with an absence word as UNMEASURED.
- moth-quantum's research notes say rep_delay is 250 µs "on most backends" (`research/2026-09-25/notes/moth-and-hardware.md:208`), so server defaults can differ by device.
- So the 6.1 law-role comparison should read "not isolated: submission UNMEASURED", or the server defaults belong in factor 6.
- The headline claim, "the crate carries a control for every other way they could differ" (62-64, 146-147), is also untrue for the factors the study itself marks `unknown` or `unexposed`.

**D4. Rule 8 contradicts the compile control** (392-397, against 413, 458-460 and 673). This is an internal inconsistency.
- v0's compile CONTROLLED rests on Aer samples drawn with the producer's seed 20261003 (`prediction-none.json`). Section 9's prediction entity carries "the seed" as an input.
- Kingston's ideal TVD of 0.13314 sits 0.0018 under the p95 of 0.13497. My estimate of the replica SD, from the published mean and p95, is 0.00185.
- Scenario: a compile defect that raises the noiseless TVD by about 3 SD passes for roughly 1 seed in 11. Trying seeds until one passes yields "CONTROLLED".
- An exact check with no seed already exists in v0: isa.py:31-49 holds every compiled circuit to the law within 1e-10.

**D5. "A run's place in that range is its quantum signal" fails for distance measures** (497-498, 528). The design property is false for these measures.
- z-scores scale with √shots. The twin's 13.49 is "the twin's expected z at this many shots" (compare.py:617-632), at 24,576 shots.
- Sampled runs have floors above zero: TVD 0.1319, and pair max|z| of 2.71 to 3.08 for the noiseless predictions.
- On v0, pair max|z| on all shots is 26.67, 32.31 and 29.41 (HARDWARE-RESULTS.md:44). That is outside [0, 13.49], so every device gets a negative "quantum signal".
- The classes themselves do not depend on the shot count, since √N scaling keeps zero and non-zero apart. The rule should be stated on N-free expected values, with floors subtracted.

**D6. `comparison-trivial` checks digests only** (576-580, with 812).
- Scenario: compare A with A′, which is A with one shot moved and resealed. A′ passes its own check, as the `shot-moved-resealed` control requires.
- The two share no raw digest, but they share every job id and all 68 salted commitments.
- The result is an "isolated" difference of one shot between a run and itself. Shared commitments would catch this; the stated limit concedes only checks a crate alone can run.

**D7. The clock bound is wrong** (95-96, 320-321, 439-440, 845-846). The measurements reproduce; the inference does not.
- I tested git 2.45.2 on this machine: 12 commits made at fractional seconds .08 to .95 all recorded the whole second below. So git truncates.
- 1bb85c9 was therefore made at local time in [10:27:15, 10:27:16). With IBM's created time at 10:27:16.731672Z, the lag it proves is more than 0.73 s.
- No record reaches 1.7 s. Assuming a constant offset, the best of the 65 line commits gives more than 1.58 s, and the best `fixed_at` gives more than 1.68 s. On the job checked, `fixed_at` gives more than 0.94 s.

**D8. The ANCHORED kind and the "anchored" level** (351-357, 715-728).
- **(a) A truncated quote.** HARDWARE.md:79-83 continues "…server-set `created` time, unless the job is private or its owner deletes it." The omitted clause undercuts "a record the producer does not control": the owner can delete the job, and only the owner's key can read it.
- **(b) The checker cannot establish the level.** "Held by the provider" is visible only as the crate's own copy of the payload, which git alone binds. "Pushed before any result was read" is a git fact that rule 1 itself classes as REPORTED. A fabricated payload with the commitment copied in would still be stated "anchored".
- **(c) A wrong reason for Atlas.** Line 727-728 calls Atlas's local commit "its anchor", which rule 1 says a git commit is not. The real reason Atlas can only be "recorded" is stronger: its provider never held the commitment. It is in neither the submit body nor the result of job 8586f1cc.

**D9. The checker's steps and the controls' names disagree** (764-776, against 801 and 804).
- The seven ordered checker steps include no commitment check and no calibration-link check, yet two controls expect refusals named `commitment` and `calibration-link`.
- As written, `job-reattributed` is either refused at step 4 under the decode's name, or accepted if the records are regenerated.
- Atlas echoes no commitment, so P1's negative control (922-925) can only work on the IBM crate.

**D10. Rule 4 conflicts with rule 5 and checker step 7** (372-379, 677, 772).
- Rule 4 keeps "the writer's version and the time of writing" out of what is held byte for byte.
- Yet the metadata names "QRO-Crate's golden measures at its version", and step 7 compares the regenerated metadata byte for byte.
- RO-Crate 1.3 also requires `datePublished` on the root: it "MUST be a single string value in ISO 8601 date format".
- Scenario: a newer checker regenerating a genuine crate is refused at step 7, so the positive twin fails. No normalization rule is stated.

**D11. Section 14 is not complete** (960-961). "Each decision this study takes is here" is false. These decisions are taken in the body and never asked:
- the campaign as the crate unit;
- the isolation definition, the seven factors and the five states;
- that QRO-Crate does not re-derive the law (739-742);
- the canonical numbers and ASCII;
- RO-Crate 1.3 with Process Run Crate 0.6 as the base;
- ANCHORED and `unexposed`;
- validation in two layers.

**D12. An absence labelled READ from search snippets** (245-248). This claims more than was checked.
- QProv and QC-MM were read by search only.
- QC-MM's abstract says it "links compilation decisions to execution outcomes … under different optimization settings".
- For those two works the claim should be BELIEVED, or qualified.

**D13. compare.py's shares are not exact Fractions** (555-556).
- The shares are float divisions: `n / shots` and `on_forbidden / n` (compare.py:346-347).
- TVD is computed as a Fraction but stored as a float (357). Only XEB keeps its exact string.
- Lines 332-361 lie outside the 60-155 the lead lists as read (line 1052).

**D14. Six small wrong statements.**
- Line 443-444: "the corpus can inflate" is not in HonestFramework's METHOD.md. Its heading (523) reads "units the corpus cannot inflate".
- Line 864: "(question 5)" should be question 6.
- Line 304: the run clone's commit 82d5f67 also appears at VALIDATION.md:1689 and 1695, not only at 1614 and 1698. The substance, that no record carries it, holds.
- Line 918: ParcelRound says "the brief got wrong", not "this brief".
- Lines 231-234: Peltonen's association list omits `configuration_linked`, and the paper says the adapter "may select … and report", not "must".
- Lines 705-706: "Any RO-Crate tool can run them" is wrong. The shapes need a SHACL engine such as rocrate-validator.

## Item by item

**1. READ citations and counts. Confirmed, except D8(a), D13 and D14.**
- I ran:
  - `git ls-tree -r -l 3a73823 -- docs/records`;
  - `enum_ibm.py` and `analyse_ibm.py` over all 65 lines, with payloads decoded through base64, zlib and npy;
  - `git log --diff-filter=A` and `git merge-base --is-ancestor` for every line and raw file;
  - `atlas.py`, `manifests2.py` and `recompute.py` (a stdlib reimplementation of `stream`);
  - `sed -n` over every cited range.
- Everything below reproduces:
  - 13,114 files and 59,378,562 bytes;
  - 31 bundles;
  - 65 jobs (31, 31 and 3) and 68 records;
  - 12,071 rolls, one per distinct layout, at 4,096 shots each;
  - 5 snapshots (06:57:43Z to 08:38:44Z) and 6 predictions;
  - the sheet stamps (09:51:18Z, 10:08:31Z, 11:05:15Z), none with a snapshot;
  - `calibration_id` in 0 of 65 metrics files;
  - line commits 1.33 to 2.58 s before IBM's created time, in 65 of 65;
  - `fixed_at` before `finished` in 65 of 65 jobs and 68 of 68 records;
  - echoed commitments 68 of 68, with all commitments and salts distinct;
  - line commits strict ancestors of raw commits in 65 of 65;
  - "0.1.0" in all 68 records and all 12,071 rolls, `__version__` added once in 6caa176 and never changed;
  - all 68 digests, canonical texts and commitments recompute;
  - ESP 0.682 to 0.649;
  - gate lists identical per device and role across all bundles, QPY bytes not.
- Every other cited range in moth-quantum, cft-fp256 and HonestFramework says what the study says.
- Notes:
  - bundle.py:50-52 does not name `rep_delay` or `init_qubits`.
  - The PREREGISTRATION.md:215-218 quote drops ", at 4,096 or 24,576 shots" without marking the cut.
  - Nothing in the tree supports "per-shot bits in shot order" (293).
  - "85 earlier platform probes" counts files from about 22 submissions.

**2. Section 4.4. The measurements are confirmed; the inference is D7.**
- Every value reproduces: 1bb85c9 at 10:27:15Z (author and committer); `submitted_at` 10:27:16.731672Z; the metrics keys; `qiskit_version` "qiskit"; the record's `code`; the span (7.22 s, starting 164.8 s after `running`).
- "UTC (BELIEVED)" is reasonable and conservatively marked. IBM's ExecutionSpan reference says start and stop are "in UTC", and all 65 spans read as UTC fall inside [running, finished]. It could be READ and MEASURED.
- The commit carries the local clock by its code path: `anchor.commit_and_push` passes no date. The run's environment, including any `GIT_*_DATE` variables, is not recorded.

**3. Section 7. The rule is coherent as a classifier; defect D5.**
- The law and uniform-twin values match HARDWARE-RESULTS.md:35-47 and compare.py (16/25, 64/75, 85/273). The dephased-twin column is correct by definition.
- No class depends on the shot count.
- TVD is a fair but degenerate input: the law's value is 0 by construction, and a sampled run has a floor.
- "Nine measures" is right for the published table. compare.py also defines `crystals_per_shot`, which the rule would class as integrity.

**4. Section 6.1. Confirmed; a note.**
- Every number matches HARDWARE-RESULTS.md, and the records show exactly one coherence job per device.
- With the between-run SD instead of ranges (`drift_sd.py`), the conclusions hold:

| measure | difference of means | in pooled between-run SDs | Welch t on the means |
|---|---|---|---|
| five-crystal share | 0.0518 | 5.2 | 11.4 |
| forbidden share | 0.0085 | 3.5 | 8.1 |
| XEB | 0.0156 | 0.9 | 2.1 |

- The XEB verdict depends on the unstated threshold.
- The "9 times" drift figure is a range statistic. As SD over sampling error it is 3.5 (kingston) and 2.9 (fez).
- The excuse that "per-run deviations are not tabulated" is weak: the per-job rows (120-170) are tabulated.

**5. Factors and isolation. Defects D2 and D3.**
- "Isolated while the REPORTED state differs" is stated (lines 70-71, 635) and is the right design for reading (a).
- Notes:
  - The provider's server-side software version is a cause not named.
  - Noise-relevant compile choices, such as the chain, land in factor 6.
  - Two repeats give a one-degree-of-freedom SD.
  - Section 8 defines isolation per comparison, but 6.1 applies it per role.

**6. Controls.**
- `job-reattributed`: commitments are distinct, so it would be caught in principle (see D9).
- `calibration-late`: decidable, given IBM's UTC documentation, but it tests only a necessary condition. VALIDATION.md:1593 says IBM's history is keyed by storage time, which a stamp-based `before-span` does not address.
- `shot-moved-resealed`: confirmed accepted.
  - Commitment v3 takes no counts.
  - My control on a copy (`work\controls\`), one shot moved and the digest resealed, passes every record-alone check.
  - Payload metadata carries no content hash.
  - Section 12 states the limit by the behaviour it concedes. It concedes more than "a moved shot", and git's history can only tell changes made after the raw's commit.
- `adjusted-as-raw`: the refusal is real for a non-integer plant.
- `compile-broken`: it misses Z-invisible rotations (isa.py:50-52) if all digests are recomputed.
- The rest are consistent.

**7. Rules.**
- ANCHORED: D8.
- Rule 8: compare.py keys the floor `stream("compare-floor", stock, n, r)`, which the producer cannot pick, so v0's floor complies. The ideal controls do not (D4). The rule's key also includes "the measure set", which is a choice the producer makes.
- Rule 4: D10.

**8. RO-Crate.**
- Confirmed: `conformsTo` on the root, the MUST/SHOULD/MAY levels, and `IndividualProduct` (a SHOULD for equipment; RO-Crate's example makes the equipment the action's `instrument`).
- No conflict on `@graph` order ("not significant"), on ASCII, or on numbers.
- Conflict: `datePublished` (D10). The study fixes no single spelling for `contentSize`.

**9. Public claims. All confirmed, except the Peltonen details in D14.**
- Workflow Run 0.6.0 was published 2026-09-07T10:41:53Z. "Profile updates for RO-Crate 1.3" is change #104, not the release title.

**10. ParcelRound at f42242e.** Every quote and rule is confirmed, except the one-word misquote in D14.

**11. Section 14. D11 and D14.**
- Notes:
  - Q4: `properties()` is keyed on "the time the job started running", which section 4.4 says is the wrong moment.
  - Q8: one shot count per job (bundle.py:54-56) means a known answer inside the law job would take 24,576 shots.
  - Q6: RO-Crate says a profile URI "MUST resolve to a human-readable profile description", which applies to a provisional IRI too.
- Q5's submodules and Q9's licences are confirmed.

**12. Quantifiers.**
- D12.
- "Every line commit…" and "IBM echoes it in every PUB's result" hold for v0 (65 of 65; 68 of 68).
- "QRO-Crate has no other file yet" was consistent at the freeze. Two files have since appeared, at 07:38: `docs/studies/qro0/sufficiency_v0.py` and its output. The redraft must change the claim.
- "About 20 s earlier" is typical, not universal: up to 297 s by created time, and 184 s between shots for the job 4.4 checks.

**13. Privacy. Found nothing.**
- The study names only "Logan" and `loganw234/QRO-Crate`.
- The files a crate would copy contain no home paths, e-mail addresses or CRNs, and Atlas's presigned URLs are already removed.

**14. Anything else.** D1 and D6, plus notes:
- Atlas's ⟨X0X1⟩ in HARDWARE-RESULTS.md is the engine's derived observable, not a function of the shots, so seam test 1 would need it REPORTED.
- IBM against Atlas hits `question-differs` unless declared, because the decode rules differ.
- Atlas's job lines already carry `code_commit`, the precedent Q8 asks for.
- 17 of 28 sheet law circuits have QPY bytes that differ from the predicted circuit, so "carries an ideal control" must mean equal by gate list.
- The commitment is per PUB, not per job.

## What I did not do

- I did not read the working copy of QRO-0.md or the new files in the QRO-Crate tree.
- I did not run Quantum-Film's own code; I reimplemented the checks in stdlib Python. The replica SD in D4 is estimated from the published mean and p95.
- I did not contact IBM or Atlas, so job retention, push times and job privacy are not determined.
- I did not verify what the survey agents read or the lead's spot-checks.
- I read only the cited ranges of cft-fp256's CERTIFICATES.md.
- Public pages came through a summarising fetch tool. Peltonen's paper was read in two halves that way, not line by line.
- I built no QRO-Crate control, since nothing is built; the one control I made is the resealed-record copy.
