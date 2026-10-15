**1. Bottom line: NOT READY.**

Z1 to Z12 are each answered correctly and applied everywhere I looked. Three defects remain: two in the new custody-log text (AA1, AA2) and one wrong count in untouched history (AA3). Each is a one-clause fix and none needs redesign. The second probe, the licences, the instruments, the sweep and the privacy scans are clean, so a re-check of draft 9 would be small.

**2. Setup**
- All 21 hashes in `SHA256SUMS.txt` match. The live draft, 13 `qro0/` files, README, probes and logs are byte-identical to the packet. I hashed the live draft and did not read it. The live tree was unchanged at the end.
- Repos, all clean before and after (`git status --porcelain` empty):
  - moth-quantum at 3a73823
  - HonestFramework at 65447fd
  - HonestHarness at b69ed76
  - ParcelRound local 8767e23 (origin/main f42242e, 37 behind, as the draft says)
  - cft-fp256 HEAD c918cb3, read at f22e8d2 through `git show`
- Python 3.12.9, `python -I`, standard library only, `GIT_OPTIONAL_LOCKS=0`.
- Scratch: `<scratch>\verifier-QRO0-r8\work\`. It holds scripts, `repro\orig`, `repro\clone`, `plants\ft` and `privacy`. It also holds a `--no-hardlinks` clone of moth-quantum plus a copy of `records/`.
- Beyond the packet, I read these from the session scratchpad:
  - the draft-6 and draft-7 verifiers' frozen packets, to diff the instruments between drafts (this packet carries only the draft-8 versions);
  - the unredacted original of the second probe's log, to test the redaction (I printed no trace id);
  - the structure only of an earlier probe trial.
- I made one WebFetch of creativecommons.org's FAQ.

**3. Defects**

**AA1. Withdrawal "marks" a line that an append-only, hash-chained log cannot alter.** Draft 8:1493-1494 against 1480 and 1483-1484 (control at 1686).
- Evidence: line 1493 says the custody-log line "stays, marked withdrawn with the reason". Line 1480 says the log is append-only. Line 1483 says each line carries the SHA-256 of the line before it.
- I modelled the draft's mechanics in `scripts\custody_chain_model.py`. Marking line 2 in place makes `custody-chain` fire at line 3, so an honest withdrawal trips the draft's own control. Appending a withdrawal line leaves the chain valid.
- Fix: "Its line stays unaltered; a later line records the withdrawal and the reason (no identifier, rule 3)." P0's log format needs a line kind for this.

**AA2. "An edited or dropped line shows" is false for the last line, and no limit is stated.** Draft 8:1483-1484 and 1686.
- Evidence, same model:
  - An edit or drop of a line that has a successor is caught at the successor.
  - An edit or drop of the last line shows nothing.
  - A custodian that rewrites the tail and recomputes its hashes also shows nothing.
- Fix: say "unless it is the last line" and state the limit. The audit record (1466-1478) could also carry the log's head hash, which closes the tail for audited logs.

**AA3. Wrong count in history text, untouched since draft 7.** Draft 8:2759, "The other five are unchanged since draft 6".
- Evidence: draft 6 had 7 instruments. Draft 7 changed `free_tier_unit_v0.py` and added `ibm_dryrun_v0.py`, so six are unchanged. I confirmed this by `cmp` on the draft-6 and draft-7 packets. Line 2689 does the same arithmetic correctly ("other six").
- Fix: "six".

**4. Per item**

**Item 1: Z1 to Z12.** All are right, applied everywhere the defect appeared, and add no contradiction beyond the notes below.
- **Z1:** the real-versus-rehearsal rule is in section 11 (1685), stage 4 (1790-1796), P5 (1907-1909) and the confirmation list (2118). `dry-run-pooled` survives only at 2715 and 2778, both in section 17. A dry-run crate still cannot be pooled, because it fails `known-answer` at intake.
- **Z2:**
  - The runtime read as text matches. `backends()` skips unlisted names (619-621). The by-name fallback is 1004-1029, the request 787-793 and the warning 799-800. The dry-run rename and refusal are 1102-1111.
  - `probe-2.json` shows three `QiskitBackendNotFoundError` and no mock backend listed.
  - The log has three 404 "device not found" warnings in the runtime's own format (`utils/logging.py:49`), in the code's order.
  - Nothing was submitted. In probe mode the tool exits at 163-164, and the only `sampler.run` is at 188.
  - Redaction: substituting the marker into the original and converting CRLF to LF reproduces the committed log byte for byte. So only three 36-character trace ids and the line endings changed.
  - The header, stage 5 and question 9 agree. The inference is out of the Decided list.
- **Z3:** the quotation is an exact fragment of METHOD.md:91-95, which is in §1 (lines 27-152).
- **Z4 and Z10:**
  - Section 9.2's provider rule (1509-1525) is consistent with rule 1 (614-615, 621-622). Section 0 item 9 (241-243) and question 17 (2074-2076) match.
  - Moth's `qpu` mode agrees with the engine description: leaving the token blank "use[s] Moth's own IBM account".
  - v0's Atlas crate stays "recorded" (1135-1136, 1541-1544, 2086-2087). Level `anchored` needs all three bullets, and the commitment never existed.
- **Z5:** I re-derived it.
  - g = s₁+s₂−s₁s₂ ≤ s₁+s₂.
  - The offset algebra checks from the confusion model.
  - An average of products is bounded by avg|a| times the other's maximum.
  - The 579 = 39×11+150, and per-unit intervals are outside it.
- **Z6, Z7, Z8:** right. Z6 at 95 and 2151; Z7 at 1754 and 2144; Z8 `pauli_atlas_run.py:150-155`.
- **Z9:** right. `usage()` computes the remaining seconds client-side (1316-1330). My own sum of the 65 `*-metrics.json` charges is 353 s (fez 125, kingston 103, marrakesh 125).
- **Z11:** both slots are named at 1069 and 1478, and section 12 (1742) is now true.
- **Z12:**
  - The quotation is exact, and the `qpu_token` and `qpu_instance` descriptions agree.
  - VALIDATION.md:63 says 410 twice.
  - The integrity and counts-only claims hold.
- **Notes taken:** all 16 are present. Two are only partly met: the custody log (AA1, AA2), and there is still no control for withdrawal or the audit record.
- **Parcel assignment:**
  - Section 10's nine steps are covered (P0: 1-3 and 9; P1: 4, 5 and 8; P2: 6 and 7).
  - 26 of 27 controls get a parcel by the rule at 1931.
  - `custody-chain` has no refusing step among the nine, so its owner is inferred (note 3).
- **Printed limit:** −0.0227 is right. My own code from the raw records gives K-M +0.0309, K-F +0.0219 and M-F −0.0227 (|Δ| 0.017260 − 0.024118 − 0.015825).
  - The strong form can never exceed its limit, because the interval widths are non-negative. So "never clears" is rigorous, not only "tends to".

**Item 2: licences.**
- moth-quantum and HonestFramework are MIT, © 2026 Logan W. (identical files). ParcelRound is MIT, © 2026 Logan.
- cft-fp256 is Apache-2.0 with a NOTICE. Draft 8 no longer mentions Apache, so no Apache claim is left to check.
- The header (55-58), decided questions (1952-1961), root row (1069), section 9.2 (1530-1531), question 10 (2036-2038), question 18 (2080-2082) and section 17 (2761-2771) agree with one another.
- See note 10 on the conditional in Logan's words.

**Item 3: instruments.**
- All five outputs are byte-identical to the frozen files on the original tree and on a clean clone.
- Plants in copies of `free_tier_unit_v0.py`:

| plant | result |
|---|---|
| limit: second drift term dropped; signed difference; wrong measure's drift; sign test inverted (4 plants) | output changes |
| bracket low end raised to 100,000, assertion kept | AssertionError, exit 1 |
| same, assertion removed | silent wrong answer: K-M "100,001" |
| assertion inverted | fires on a good bracket |
| assertion made a no-op | output unchanged: the guard cannot fail on v0's data |

- `ibm_dryrun_v0.py`: I audited it statically only and did not run it.
  - The new `FORBIDDEN` regex refuses plain and single URL-quoted CRNs in either case. The old pattern missed the quoted form. A double-quoted `%253A` passes, which was not claimed.
  - The `--submit` gate is at 166-168.

**Item 4: sweep.**
- All 21 tables are well formed. All 207 section references and 31 question references resolve. Backticks balance, with no trailing whitespace or tabs, and the non-ASCII set equals draft 7's.
- Every section 15 prefix matches: 8 instruments, 8 outputs, 2 MANIFESTs and both probes. Draft hashes 1 to 7 in the header match the earlier packets, and all four commit dates match git.
- No old defective phrase survives outside section 17. The only stale figure is AA3.

**Item 5: privacy.**
- I ran HonestHarness's path, address and key patterns, taken verbatim from `tools/check.py` at b69ed76. Result: 0 hits over 160 live files (the draft, 13 instrument files, and all 146 files of `records/2026-10-14/`, both probes included).
- The only packet hit is `draft7-recheck-report.txt:4`, a harness header with a scratch path under the home directory. It is not part of the study.
- Extra greps found names only, never values:
  - CRN patterns: only as guard regexes at `ibm_dryrun_v0.py:74`, `ibm_refetch_v0.py:74` and `ibm_results_refetch_v0.py:57`. The word "CRN" is at draft 505, 639 and 2830, and README 7 and 227.
  - API key: draft 639; tools at 74 and 133, 74 and 142, 57 and 97. Key-file names at `ibm_dryrun_v0.py:27, 132-134`, `ibm_refetch_v0.py:16, 141-143` and `ibm_results_refetch_v0.py:96-98`.
  - `token`: draft 1561, and line 1 of the four logs (the runtime's "given token" warning).
  - E-mail and JWT: 0.
  - `user_id`: draft 640 and 1079, README 39, and the bare key name in the omitted-keys list of all 65 `ibm-refetch/&lt;device&gt;/&lt;job&gt;.json` records.
  - `instance_id` and `plan_id`: names only, at probe-1 34-35, probe-2 48-49 and README 211.
  - One UUID per refetch record is IBM's `resource_units` metric id. It is identical in 65 of 65 and already in moth-quantum's tracked metrics files. It is not an account identifier.

**5. Notes**
1. Section 8 lacks the real/rehearsal declaration (919-935) and `kind-not-qpu` (937-954).
   - Its place in the refusal order and its scope (units or any crate) are unsaid.
   - The Atlas crate's `kind` is never stated. An IBM-against-Atlas comparison (944-945) would be refused if declared real.
2. P5 (1903), 9.1 (1228) and the `ibm_dryrun_v0.py` docstring (lines 6-7) still say "lists". Stage 5 (1826) and the tool's gate say "resolve".
3. `custody-chain` has no refusing step in section 10, and P0's ownership is inferred. No control exercises withdrawal or the audit record. P5's own bullets (1896-1921) omit `kit-dirty`.
4. Cause 3 now includes the kit's commit (691), but v0's cells and 6.1 (776) are silent on it, and 4.3 (457) says the code that ran is partial.
5. The two root slots (1069) have no header/body marker. In the body, v1 signing would change the crate's identity. "Empty" should be an absence word (rule 2) with a kind (rule 9).
6. "MEASURED" on "dry run unavailable" (33-34, 1985-1987) labels an inference from two lookups plus the READ refusal path. No dry run was tried.
   - The 404 is evidenced by the log only. `probe-2.json` carries a class the runtime raises for any failure (799-804).
   - base_primitive.py:138, "access to this feature may be restricted", could be cited.
7. In `ibm_dryrun_v0.py`:
   - Line 173 rebinds `by_name` as a dict in the `--submit` loop. This is harmless now.
   - The probe passes the instance; the runtime's dry-run lookup (1107) does not. They are equal for a one-instance or default-instance service. The log cannot show whether the service was built with `instance="auto"`, and I did not read `account.py`.
8. README:
   - The second log's CRLF-to-LF change is not mentioned.
   - Lines 202-204 still say "the runtime would refuse it", with no pointer.
   - The first probe's scratch trial of 12:36 is not listed, though the README lists trials elsewhere.
9. The new assertion cannot fail on v0's data, so only a bad bracket exercises it. `python -O` would strip it. `free_tier_unit_v0.py:256` still says `f_a f_b`.
10. Licences:
    - Logan's words are conditional ("unless it would be simpler to keep both CC BY 4.0"). The study closes the condition on the lead's advice, so he should confirm at approval.
    - CC's advice at 1955 is true (CC FAQ: "We recommend against using Creative Commons licenses for software") but unlabelled and not in section 15.
    - "Quantum-Film's files … are Logan's, under MIT" (1959) matches the LICENSE. But Atlas responses carry Moth-authored text and IBM's records are IBM's data, so the LICENSE does not settle them. The draft does not examine the providers' terms, so label it BELIEVED.
    - The licence of the profile text and of the study itself is not stated.
11. Smaller wording points:
    - "Moth is the IBM job's owner" (1524) should be BELIEVED.
    - Section 17 "where" cells: Z4's "17" and Z10's "19" are question numbers, in a column of section numbers.
    - Question 17 omits the hash chain and withdrawal.
    - 9.1 (1403) counts others' anchors REPORTED while 9.2 (1511-1514) lets an auditor hold ANCHORED. That works only because an audit record is not a comparison, which is unsaid.
    - Line 1558 "counts only" omits the majority label and `shots`. "Bell test" (1571) does not apply to a one-qubit engine.

**6. What I did not do**
- I did not contact IBM or Atlas, run any of the three IBM tools, create a service or account object, or import qiskit.
- I did not open credential, key, token or account files, `account.py`, `keyleak.py` or `.atlas/`.
- I read the runtime source as text under `.venvs\qf-ibm\...\qiskit_ibm_runtime\`, and listed `site-packages` (filtered) for the installed versions.
- I did not read the live draft.
- I did not re-review unchanged sections 1 to 8, 10, 12 and 16 beyond the diff and greps.
- I re-derived only the new figures: the three limits, the 353 s sum, and the resource-unit sum (5.449 against IBM's 5.448135, which is rounding).
- I did not re-derive 0.0181, 0.0058, 77,380 or 153,166, which earlier re-checks confirmed.
- I could not check Logan's verbatim licence quotes, which are not in the packet.
- I did not run `tools/check.py`. I ran its patterns.
- `--submit` is untested by design.

**7. Anything in this brief that was wrong or unclear**
- "Two dated sections were added" to the README: the diff shows one new dated section (the second run), with an undated correction paragraph inside it.
- "Apache claims": draft 8 makes none. I checked cft-fp256 anyway.
- The brief says a 404 appears in `probe-2.json`. Only the log carries it.
- The calibration instrument takes two arguments (QRO-Crate root, then moth-quantum), which the brief does not say.
- The packet lacks draft 7's instrument versions. I took them from an earlier verifier's packet.
- The confirmation list names the control `simulator-in-real` but not the refusal `kind-not-qpu`.
- "Read the engine description fields only": the record also holds an owner id. I did not print it.
