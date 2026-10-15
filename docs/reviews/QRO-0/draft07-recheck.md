**1. Bottom line: NOT READY.**

I found twelve defects, Z1 to Z12. None needs a redesign.
- Z1 to Z5, Z10 and Z12 are claims that go beyond their evidence or contradict another part of the draft.
- Z6 to Z9 and Z11 are text slips.

Y1 to Y4 are answered correctly and applied everywhere. All five outputs reproduce byte for byte. The privacy scans are clean. A re-check of the fixes should be small.

**2. Setup**
- All 19 packet hashes match `SHA256SUMS.txt`.
- At the start the live tree matched the packet byte for byte: draft 7, the 13 `qro0/` files, and the records README. The live `docs/studies/QRO-0.md` was edited again at about 13:57, during my review (hash now `05511815…`). I did not read it. The frozen draft governs.
- `moth-quantum` (3a73823) and `HonestHarness` (b69ed76) were clean before and after. I read `HonestFramework`, `cft-fp256` and `ParcelRound` only through `git show` and `git log`. They are clean too.
- Python 3.12.9, `python -I`, standard library only. I set `GIT_OPTIONAL_LOCKS=0` so `git status` could not rewrite an index.
- Scratch is `…\scratchpad\verifier-QRO0-r7\work\`.
  - `scripts\`, `repro\orig\`, `repro\clone\`, `plants\`.
  - `clone\moth-quantum`, a `--no-hardlinks` clone.
  - `clone\QRO-Crate\records`, a copy of the live `records/` (144 files).

**3. Defects**

**Z1. M1 stage 4 pools units that the draft says no pool admits** (claim)
- Where: lines 1716-1717 against 1820, 1612 and 2606-2607.
- Evidence:
  - Stage 3 makes a local unit a `simulator` bundle (1709-1714). Stage 4 then says "Two local units are pooled".
  - P5 says "Pooled comparisons admit only `qpu` units". Control `dry-run-pooled` repeats it.
  - Draft 6's note c asked for this rule only for "a pooled real comparison". Draft 7 dropped "real".
  - A dry-run crate also fails `known-answer` at intake first (1816-1818, 1385-1386). So `dry-run-pooled` reaches its own refusal only with a unit that passes `known-answer`. That is a `simulator` unit, which is what stage 4 pools.
- Fix:
  - A comparison declared real admits only `qpu` units.
  - A comparison declared a rehearsal may pool `simulator` units, says so in its body, and is never cited as a result.
  - `dry-run-pooled` plants a `simulator` unit into a real comparison.
  - Give that refusal a name.

**Z2. "IBM's dry run is not available / unavailable to this account" is not what the probe measured** (claim)
- Where: lines 28, 1729 and 1875-1876. The README at 203-204 says "the runtime would refuse it".
- Evidence:
  - The probe measured the backend listing: `service.backends()`, `ibm_dryrun_v0.py:135-136`.
  - The runtime's dry-run path calls `self.backend(name="mock_&lt;x&gt;")`. That method warns that the listing may omit backends. When the name is not listed it makes a one-time by-name configuration request (`qiskit_runtime_service.py:1004-1029`, request at 787-793). A mock backend missing from the listing may still resolve.
  - The tool's own gate on the listing (148-150) means the question can never be tested. The runtime raises before any submission if the name does not resolve (1106-1111), and Logan cleared dry runs.
  - Q9 also puts the inference inside the "Decided" bullet.
- Fix:
  - Say "lists no mock backend; whether a by-name lookup resolves is untested" in all three places.
  - Add a read-only by-name configuration request to the probe, or simply try the dry run.
  - Keep the inference out of the Decided list.
- The tool itself is safe.

**Z3. "Only the last is an external authority in HonestFramework's sense"** (claim)
- Where: lines 1461-1463.
- Evidence:
  - METHOD.md §1 at 65447fd (lines 91-93 and 110-113) says two implementations on one input are not an external authority. The commit that sharpened the rule is titled "two parsers agreeing is not an authority".
  - The study says the same of the seam test (1538-1539).
  - An independent checker reads the same crate.
- Fix: say none of the three degrees is external in that sense. The third is the strongest check of the checker's code and of the profile's text. The external checks stay the provider's copies, the known answers, and a second group's records (1542-1545).
- The quotation itself is exact as a fragment.

**Z4. A provider's attestation is "ANCHORED"** (claim)
- Where: lines 233-234, 1464-1471 and 1964-1965.
- Evidence:
  - Rule 1 (599-615) requires a record the producer does not control, established by a fetch.
  - 9.2's own example is Moth recording its own coin-toss runs (1486-1487), so the provider is the producer.
  - The provider "re-fetches from itself", and v0 has no signatures (1447, 1472-1474).
  - Section 9.1 (1372-1375) counts anchors by anyone but the comparison's author as REPORTED.
- Fix: the attestation is ANCHORED only if the provider is not the producer and the auditor obtains it from the provider. An unsigned file handed over is REPORTED, with the holder named, which is rule 1's own fallback. Signatures in v1 can raise it. Change section 0 item 9 and Q17 to match.

**Z5. Note b: "Each step is linear in the confusion rates, so averaging is sound"** (claim)
- Where: lines 1351-1354.
- Evidence:
  - The shrinkage step is fine. g = s₁+s₂−s₁s₂ ≤ s₁+s₂, where s is p01+p10, so it is linear.
  - "Average of p01 + p10 over the pair's qubits" reads as a mean over the two qubits. That would halve the bound. It must be the sum over both qubits, then averaged over units.
  - The offset is a₁m′₂ + a₂m′₁ − a₁a₂. The cross term is a product of two unit-varying quantities, and an average of products is not the product of averages. Two units with |a| = 0.02 and 0 give 0.0002 against 0.0001.
  - At v0's rates the cross term is 4.6 to 8.7% of each offset (0.00018 to 0.00029). The numbers are safe. The sentence is not.
- Fix:
  - Say the shrinkage and the a·m′ terms are linear, with m′ bounded by the largest unit's certified bound.
  - The a₁a₂ term takes the average of one |a| times the largest unit's other |a|, or the worst unit.
  - Say "summed over the pair's qubits".

**Z6. Stale count "two IBM tools"** (slip)
- Where: lines 87 and 2043. Line 2060 already says "three". The new dry-run tool pins nothing either.

**Z7. Stale draft numbering** (slip)
- Where: lines 1680-1681 ("Drafts 1 to 5 went past verifiers, and draft 6 goes next") and 2035-2036 ("re-checks of drafts 2 to 5").
- Fix: 1 to 6 and draft 7; 2 to 6.

**Z8. Atlas runner citation** (slip)
- Where: lines 1761-1763.
- `tools/pauli_atlas_run.py:149-153` stops before the refusal. `preflight` is at 150, the test at 153, and the raise at 154-155. Cite 150-155.

**Z9. "IBM reported the same 247"** (slip)
- Where: line 1203. The README at 205-207 has it too.
- `usage()` computes `usage_remaining_seconds` client-side from IBM's limit and consumed figures (`qiskit_runtime_service.py:1316-1330`).
- IBM reported 600 and 353. Say that.
- The real cross-check survives: IBM's 353 equals the instrument's sum.

**Z10. Moth's records could lift the Atlas crate "above recorded"** (claim)
- Where: lines 1483-1485 and 1979-1980.
- Section 4.3 and line 1124 say the provider never held a commitment, and the seed does not exist. Those are `none`, not `unexposed`. Level `anchored` needs commitments found in the provider's copy.
- Fix: Moth could expose the compile and keep results. v0's Atlas crate stays "recorded". Future Atlas runs could carry a commitment the provider holds.

**Z11. "v0 names their slots" (a signature and a trusted time)** (slip)
- Where: lines 1472-1474 and 1668.
- The audit record names a signature slot (1447). No trusted-time slot is named anywhere. Sections 9.2 and 12 cite each other.

**Z12. The coin-toss paragraph contradicts material the study holds** (claim)
- Where: lines 235-237 and 1491-1507.
- Evidence:
  - The paragraph says "has not read the engine".
  - `moth-quantum` at 3a73823 has Moth's published description of `coin-toss-v1` in `docs/records/2026-09-25/atlas/20260925T173228348516Z_GET_api_v1_engines_coin-toss-v1.json:99`, and rows at `docs/ATLAS.md:32` and `docs/VALIDATION.md:57,63`.
  - It describes one qubit, a Hadamard gate, measured `shots` times. It returns heads and tails counts only. `mode` is `emu` (the default) or `qpu`, which submits to IBM.
  - So the equal-superposition premise is READ.
  - "Correlations between qubits" has no meaning for one qubit. "Between shots" and the shot-order bullet cannot be audited from counts.
- Fix: cite the description, keep the code unread, and drop or condition those two points. The physics is right.

**4. Per item**

**Item 1**
- **Y1:** answered correctly, in the only place it appeared (1342-1347).
  - The instrument prints the parts at line 34 of its output.
  - My independent derivation gives 0.018083, 0.005765, 0.023848 and 0.035487. That rounds to 0.0181, 0.0058, 0.0238 and 0.0355, and the shrinkage share is 51%.
- **Y2:** the partition holds. 14 of 26 rows are crate-level and meetable at stage 2. Z1 is the exception. Parcel ownership is a note.
- **Y3:** all uses of "campaign" and "crate" are consistent with 1038-1043. The nine-job "campaign" in 16.5 and Q9 is a hypothetical pre-registered run.
- **Y4:**
  - HARDWARE.md says "read and measured on 2026-10-01" at line 3, and lists the devices at 16-17.
  - The three dates in 0.7 and 9.1 are right.
  - Line 2519 is history.
- **Note b:** Z5. The family count is right.
  - 579 is 39×11 + 15×10.
  - 78 is 3 pairs × 2 devices × 13, so "up to twice the 39" holds.
- **Note c:**
  - `hw_run.py:255-261` is right.
  - `kind` and `route` are in `RUN_COMMITTED` (`fixer.py:145`).
  - A simulator run may not name an IBM device (`fixer.py:418-421`).
  - `--dry-run` is the local simulator (239-242).
  - Z1 remains.
- **Note d:**
  - The kit's commit is in the body (1066, 1758), and `kit-dirty` exists (1611).
  - The "this study's reading" label is applied in 0.7, 9.1 and Q9 but not M2 (1754-1757).
  - Z8.
- **Note f:**
  - 77,380 and 153,166 are exact. My own bisection gives strong(N−1) &lt; 0 &lt; strong(N) for both.
  - Fake-backend dates 2026-04-15, 2025-02-26 and 2025-02-26 are right (the JSON files).
  - A coherence plug-in is a PUB, and `qro:role` is per PUB.
  - The P5 duplicate was removed in draft 7, not "already".

**Item 2**
- **(a) The tool.** Line references are to `ibm_dryrun_v0.py`.
  - `--probe` submits nothing. The only `sampler.run` is at 170, after `sys.exit(0)` at 145-146.
  - `--submit` refuses without a mock backend (148-150). Any missing device refuses all.
  - The tool cancels and refuses if IBM records a non-mock backend (177-181). That is a backstop after submission. The runtime rename is the primary guard.
  - No account identifiers are written. Whitelists are at 75-78, `usage_of` keeps names only (117-125), and `write` filters and never overwrites (106-114).
  - `--submit` would also write job ids, calibration ids and error strings, filtered only by the four patterns. That path is untested.
  - Probe, README and draft agree on:
    - plan open/free and the three backends;
    - 353 of 600 s and 5.448 of 10 RU;
    - a 28-day period ending at the query;
    - roll-off on 2026-11-02.
  - The runtime citations hold: `1102-1111`, `base_primitive.py:155-164`, and `usage()` at 1316. See Z9.
  - 5.448135/353 = 0.01543. Times 216 s is 3.33 RU. Two units use 432 s and 6.7 RU, so both limits hold. Today only one fits (247 s, 4.55 RU).
  - Z2.
- **(b) Section 9.2.**
  - Rule 3: consistent for crates.
  - Rule 9: only the date has a kind (note).
  - Section 8: consistent. Only the owner's re-fetch exposes a fabricated run, and 1443-1444 says so.
  - Z3, Z4, Z12.
  - Nothing outward-facing is assigned to the study (1478-1479, 1983-1984).
  - I could not check the verbatim quote against Logan's message, which is not in the packet. The header excerpt equals the first sentence of 9.2.
- **(c) Knock-ons.**
  - Section 0 item 9 carries Z4 and Z12.
  - Section 12 carries Z11.
  - Stage 6 matches degree 2 and is honest ("mechanics, not independence").
  - P0, Q18 and the confirmation list are fine.
  - Q17 carries Z4, and Q19 carries Z10.
  - The header carries the Z2 "unavailable".

**Item 3**
- All five outputs are byte-identical to the frozen files on the original tree and on a fresh `--no-hardlinks` clone with a copy of `records/`.
  - sufficiency `61be0a65`
  - timing `3a383646`
  - isolation `c6f042d2`
  - calibration `89ac4b86`
  - free-tier `93435228`
- The git gate refuses an untracked file and a modified tracked file.
- `readout_parts` is correct. Swapping its two device arguments gives identical parts. The bound equals the certified difference minus `beyond_readout` in both orders.
- The bisection is correct. The strong form is monotone in N, with one switch for K-M and K-F and none for M-F.
- Plants (24 in copies):

| plant | result |
|---|---|
| bracket low → 100,000 | changed (K-M 100,001) |
| bracket high → 65,536 | changed |
| bracket high → 2,097,152 | changed (M-F follows the bracket) |
| bracket low → 1 | unchanged: any `lo` that fails finds the same boundary |
| test `&gt;` → `&gt; 0.001` | changed |
| test measure changed | changed |
| branch inverted | changed |
| loop bound `&gt; 2` | changed (77,381) |
| print `lo` | changed |
| test `&gt;` → `&gt;=` | unchanged: the strong form is never exactly 0 |
| control shots inside `clears` | unchanged: the five-crystal strong form takes none |
| midpoint rounded up | unchanged: equivalent split |
| devices swapped in the "more than" test | unchanged: symmetric |
| `readout_parts` device choice: swapped, or always the first | changed |
| `readout_parts`: always the second device | unchanged: on v0's data A reads above B in every certified case, so the else branch never prints |
| `readout_parts` guard, offsets, tuple, `true_hi`/`true_lo`, print order (7 plants) | changed |
| `readout_parts` positivity guards dropped | unchanged: `true_lo` &gt; 0 in every printed case |

**Item 4**
- Every "section N" and "question N" reference resolves.
- All 26 control names match the section 11 table.
- The section 15 table is right for all 8 rows. Draft 6's hash is right.
- Stale text: Z6 and Z7.

**Item 5**
- HonestHarness's three patterns (path, address, key), run from `check.py`'s text over 186 files, give 0 hits.
  - Files: the frozen and live draft, the 13 instruments and outputs (frozen and live), the packet's README, probe and log, all of live `records/2026-10-14/`, and my 10 reproduced outputs.
- Extra greps:
  - CRN: no values. 6 name hits are the guard regex in `ibm_dryrun_v0.py:72`, `ibm_refetch_v0.py:74` and `ibm_results_refetch_v0.py:57`.
  - E-mail, JWT and home paths: 0.
  - "API key" and key-file names: the same three tools (dry-run 72 and 130, refetch 74 and 142, results 57 and 97) and draft 628.
  - `token` is a word in line 1 of the three logs.
  - `user_id` is a bare name in draft 629 and 1068, README 39, and the 65 refetch job records. No value appears (checked).
  - `instance_id` and `plan_id` are names at `probe.json:34-35` and README 211.
  - A 56-character K run at `v0_timing_and_drift.out.txt:43` is the device-order string.

**5. Notes**
- The checker's steps 2 to 5 and 8 to 9, the decode, and 15 of the 26 controls have no named parcel. Stage 2 now leans on them.
- Stage 5 is "the last check before a real unit", but stage 6 follows.
- M1 stage 2 writes only the IBM crate. Section 9.2 and Q19 audit "v0's crates, among them the Atlas crate".
- The audit record's degree of independence is self-declared, so it should be REPORTED. Rule 3 should cover auditors' handles and the custody log's "where it came from".
- No control exercises 9.2's record or log mechanics. "Keep both" leaves no takedown path for a crate found to carry an identifier.
- "IBM gives no such attestation" is unlabelled (BELIEVED).
- For `mode: qpu`, Moth sits in front of IBM (QF's `route` is `moth`). Moth would be the job owner, which is a different case from a provider attesting about itself.
- "It is Logan's plan" covers sub-bullets that are the study's own: Atlas records, "author of an independent checker". "ASU" is never expanded.
- The "across units" routes add unit-level readout and single-site intervals to the look's family. The count of 579 excludes them.
- 0.0181 + 0.0058 prints as 0.0239 against 0.0238. The bound is for ⟨X0X1⟩.
- "Marrakesh against fez would need more than a million" is really "never under v0's drift". The limit as N→∞ is |Δ| − drifts = 0.0173 − 0.0399 = −0.0227.
- The bisection does not assert `clears(lo)` is false. The B1 plant shows the silent failure.
- The instrument docstring (lines 33-35) still uses a, b for qubits.
- `kit-dirty` covers "untagged commit", which the Atlas-runner cite does not support. Putting the kit's commit "under cause 3" extends cause 3's definition (section 6).
- "(section 9, rule 4)" at 1426 and 1991 reads as two cites. "(METHOD.md section 1, READ; section 10)" is ambiguous, because METHOD.md has its own unrelated §10. Write "this study's section 10".
- In 9.2, "uniform twin (section 7)" is the film's five-of-sixteen twin. For a coin the twin is the fair coin.

**6. What I did not do**
- I did not contact IBM or Atlas, and did not run any of the three IBM tools.
- I created no service or account object, and imported no qiskit code.
- I opened no credential, key, token or account file.
- `HARDWARE.md` lines 24-27 name the key folder. I did not open it.
- I read `account.py` as code.
- I ran a repo-wide `grep -l` in `moth-quantum`. It walked the git-ignored `.atlas/` response cache. I opened two engine-listing files there, public metadata, and left the engine owner's id out of this report.
- I did not read the live post-freeze `QRO-0.md`.
- I did not re-derive unchanged sections 1 to 8, 10 to 12 and 16 beyond the diff, references, figures and stale-term greps.
- I did not check draft hashes 1 to 5, the arXiv hashes, or run an α-schedule coverage simulation.
- I did not property-test the single-unit readout bound; the prior re-check did. I re-derived the algebra and the numbers.
- I did not run `tools/check.py`; I ran its patterns.
- `ibm_dryrun_v0.py --submit` is untested by design.

**7. Anything in this brief that was wrong or unclear**
- "Writes no identifiers": `--submit` writes job ids and calibration ids. I read it as account identifiers.
- "It cites METHOD.md section 1 through section 10" is ambiguous, as in the notes.
- Only the README and the probe from `records/2026-10-14/` are in the packet. I scanned the live directory and used its `records/` copy for the calibration instrument.
- The brief does not say how to supply the second root to the calibration instrument.
- The brief says the live tree is read-only. It moved during the review.
- Note d's "relabelled 'same kit'" is applied in 3 of 4 places.
