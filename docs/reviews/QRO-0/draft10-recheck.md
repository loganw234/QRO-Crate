**1. Bottom line: NOT READY.**

There are three defects, AC1 to AC3. All are small text slips that draft 10 introduced. AB1 itself is fixed. The gate refuses all five fault classes you named. The custody log behaves as now specified. After three one-line edits, a diff-only re-check should be enough.

**2. Setup**
- All 18 hashes in `SHA256SUMS.txt` match, before and after my runs. My base copy (draft 10 as `QRO-0.md` next to `qro0/`) is byte-identical to the packet.
- Python 3.12.9, `python -I`, standard library only.
- Scratch is `...\verifier-QRO0-r10\work\`. It holds `base/`, `plants/`, `d9/`, `logs/` and the scripts.
- moth-quantum is clean at 3a73823. I used `git --no-optional-locks` throughout.
- The live README and all 14 `qro0/` files match the packet.
- The live `docs/studies/QRO-0.md` does not match. It was edited at 15:34, after the freeze, and has 17 more lines: Logan's "MIT confirmed, docs CC BY 4.0, go ahead with git init". I did not verify those lines. That file still passes the gate.
- Line numbers below are the frozen draft's. Make the fixes on the live file.
- One slip of mine: my first masking regexp missed hyphenated UUIDs. About 20 Atlas job ids from tracked file names appeared once in my tool output while I located the `mode` values. I redacted the scratch log. No credential was involved.

**3. Defects**

**AC1. Rule 4, lines 647-651: "That last" now points at the wrong item.**
- The N7 edit added "and the signature and trusted-time slots (section 9)" after `datePublished`.
- The next sentence still reads `That last "MUST be a single string value in ISO 8601 date format"`. It now attaches to the slots. The quote is RO-Crate's rule for `datePublished`.
- Fix: "RO-Crate's `datePublished`, which "MUST be a single string value in ISO 8601 date format" (RO-Crate 1.3, READ by the re-check), and the signature and trusted-time slots (section 9)."

**AC2. The study says the gate does more than it does, and states no limit (lines 36-37, 2249-2250, 2981).**
- Line 2981 says it "refuses any draft whose numbers disagree with its header". The gate checks two sentences only.
- Plants on copies, all ACCEPTED:
  - Header lines 35 and 38 ("Draft 10 answers", "re-check of draft 10's changes") set to draft 9.
  - Section 17 labels ("what draft 10 changed", "The instruments, in draft 10") set to draft 9.
  - A stale section 13 with the right sentence quoted elsewhere. The gate looks for the sentence anywhere in the text, not in sections 13 and 15.
  - A section 15 row with a wrong hash plus a trailing space, or `...` for `…`. The row is skipped silently. The printed row count drops from 9 to 8 and is compared with nothing.
  - A deleted instrument row, and a new `.py` in `qro0/` with no row.
- Claims 36-37 and 2249-2250 are also too broad on "tables" and "section references". The full list of unchecked cases is in item 2 below.
- Fix: either narrow the three descriptions and add a limits paragraph to section 15, or strengthen the gate. Suggested gate changes:
  - Require the row count to equal the number of `qro0/*.py` files.
  - Read "Section" and wrapped references.
  - Treat any pipe-bearing line after a header as a row, and compare the delimiter row.
  - Scope the two draft-number sentences to sections 13 and 15, and add the header and section 17 labels.
- If the gate changes, update its hash row. The gate will catch you if you forget.

**AC3. Section 15, lines 2230-2231, is false for the gate (low).**
- It says "Except the three IBM tools, each refuses unless moth-quantum is a clean 3a73823." The gate is the ninth listed instrument and never reads moth-quantum.
- Header lines 96-98 also list only 5 + 3 instruments.
- Fix: "Except the three IBM tools and `check_study.py`, …".

**4. Per item**

**Item 1, AB1.**
- Line 1805 says "Drafts 1 to 9 … draft 10 goes next". Lines 2222-2223 say "the re-checks of drafts 2 to 9". Both agree with the header (line 3).
- The gate run on frozen draft 9 refuses exactly the two AB1 failures, so "refused draft 9 for exactly AB1" (2981) is true.
- I checked every "draft N" in draft 10. None is stale.

**Item 2, the gate.**
- **Audit.** It is 93 lines, standard library only, read-only, with no asserts and an ImportError guard. Its docstring is accurate. The study's descriptions are not (AC2).
- **Frozen draft 10:** "22 tables, 26 section references, 9 instrument rows", ACCEPTED, exit 0. "26" is distinct section numbers, not references. The live draft is also ACCEPTED.
- **Plants, each REFUSED by name:**

| Plant (on a copy) | Result |
|---|---|
| Section 13 left at "draft 9 goes next" | `section 13: wants 'Drafts 1 to 9 … draft 10 goes next', has '… draft 9 …'` |
| Section 15 left at "drafts 2 to 8" | `section 15: wants … 2 to 9, has … 2 to 8` |
| Header bumped to 11, nothing else | both refused |
| Table rows: short row (section 11), stray pipe (section 6), no trailing pipe (16.5) | `line 1705: 3 pipes, header 4`; `line 699: 7 vs 6`; `line 2444` |
| "section 18", "section 6.7", "sections 9 and 19" | `a reference to section N, which is not a heading` |
| One byte of `isolation_v0.py`, `ibm_refetch_v0.py`, or the gate | `isolation_v0.py hashes 9d5f84e4, the table says 3f63f1ae` (and the other two) |
| One byte of `isolation_v0.out.txt`, or `sufficiency_v0.out.txt` deleted | `hashes e0b64de7, the table says c6f042d2`; `hashes missing` |

- **What the gate does not check:**
  - **Draft numbers:**
    - Only the two sentences in 13 and 15 are checked, and they are matched anywhere in the text.
    - Other draft numbers are unchecked, including previous drafts' hashes.
  - **Tables:**
    - The delimiter row is not compared.
    - A `| --- |` delimiter makes the table invisible.
    - A table indented in a list is invisible. The draft has one, at line 494. It is well-formed by my own GFM scan, but the draft has 23 tables and the gate sees 22.
    - A row without its leading pipe ends the gate's view of the table.
  - **Section references:**
    - It reads only lowercase "section N" on one line.
    - It misses 19 capitalised and 9 line-wrapped references. All resolve today.
    - It reads only the first number in "sections 6 to 8".
    - It ignores question, rule, stage, refusal and cause numbers.
    - It cannot tell "METHOD.md section 7" from an internal reference. A plant to "section 21" gave a false refusal.
    - It cannot tell whether a cited section is the right one.
  - **Hash table:**
    - Rows that miss its exact pattern are skipped silently.
    - A missing row is accepted.
    - Four records hashes and two older tool hashes are unchecked. The four records hashes do match the live files and the README.
    - It checks its own hash, so it cannot vouch for itself.
  - **Prose:** It checks no prose or figures, and it does not re-run the instruments.
- **Section 15's description of the gate** does not match (AC2).
- **The table row** (line 2246) is honest in substance. The gate has no output file, and none could be hashed into a hashed study. Two small imprecisions: it also prints a count line, and it exits 1 on refusal.
- **Not recorded:** the two runs the study cites (draft 9 refused, draft 10 accepted) have no stored output. I reproduced both.

**Item 3, N1 to N12**
- **N1:** correct (line 1732).
- **N2:** correct (992-994). Knock-on: see note 1.
- **N3:**
  - The declaration list (930) and 6.1's "declared real" (770) are correct. All 31 IBM manifests are `kind: qpu`.
  - **Count:** 20 string `"mode"` values, all `emu`, none `qpu`, plus one object-valued `mode` (the coin-toss engine's parameter schema). Confirmed as a count. Scope note: see note 2.
- **N4:**
  - **Model:** I modelled the log as specified, with 6,000 random tampers and 0 mismatches.
  - **First line:** dropping it shows, via the empty-string predecessor (230 of 230).
  - **Edits and drops:** an edit or drop with a successor shows.
  - **Last line and rewrites:** an edit or drop of the last line, or a forward rewrite, shows nothing in the chain.
  - **Pinned head:** an edit, drop or rewrite at or before the pinned head shows (2,327 of 2,327). Truncating away the head line shows (781 of 781). Tails after the head stay uncovered.
  - **Who holds the record:** a writer who also rewrites its own held record passes. The same rewrite against a record held by someone else shows (750 of 750 each).
  - **`none`:** it pins nothing.
- **N5:** correct (1791-1793, 1888-1890). The third sub-point, that section 10 does not name the custody check, is neither taken nor declined.
- **N6:**
  - **IBM:** `unknown` per job is right. No file of 928 under 2026-10-05 holds `code_commit` or any commit-like key.
  - **Atlas:** 6 of 6 `commitments.jsonl` lines carry `code_commit`, each a 40-hex value.
- **N7:** `none` is applied at 1568-1571 and 1790, but see AC1.
- **N8, N10, N11, N12:** correct. The README bullet (262-265) is accurate against `ibm_dryrun_v0.py:166-168`.
- **N9:** applied at stage 5 (1859-1860) only. Question 9 (2051-2054) still has "So IBM's dry run is unavailable" under a MEASURED label.
- **Not taken, N9's instance note:**
  - **Held:** `account.connect` builds the service with `instance=crn` and refuses unless `active_instance()` equals it (`account.py:59-71`). The premise is true.
  - **Unchecked:** "they agree" is honestly BELIEVED. I did not read the runtime's source.
- **Not taken, N12's control:** the reason holds. Section 11 is crate, unit, comparison and custody controls under `controls/`. The verifiers did plant the instruments' faults.

**Item 4, sweep**
- 27 distinct section numbers are cited and all resolve. Question, rule, stage, refusal and cause numbers are all in range.
- All 23 tables are well-formed.
- The section 15 hashes match, and the gate covers 9 instruments and 5 outputs.
- The remaining `partial` are 4.3's own state word in four rows, plus history lines. `empty` survives only in "SHA-256 of the empty string" and N7's history line. No stale draft number.
- No secret-shaped strings in the draft, the gate or the README.

**5. Notes**
1. **N2 knock-on.** 6.1's "isolated from the pipeline?" cells (811-817) name only drift. By the new clause (992-994), the `unknown` commit is a second stopper and the rule says the statement names every one. Short answer 2 (138-140) is also unchanged.
2. **N3 scope.**
   - The 20 values sit in 14 files of 8 probe jobs, all under `2026-09-25/atlas`. They are not "20 records".
   - The six law jobs' exchanges, `commitments.jsonl` and the rolls carry no `mode`. They ran the tomography engine, whose default provider is `aer`.
   - `simulator` is right, but the support is `docs/VALIDATION.md:21` ("Every job ran on `emu` (Aer)") and `:250` ("All of it is `emu`"). Cite those.
3. **N4 wording.** In "four conditions" (1517-1522), only the first two are conditions. The third is the effect and the fourth is the limit. The head of an empty log is undefined. `none` pins nothing, and a checker cannot tell an honest `none` from a withheld head.
4. **Sub-points neither taken nor declined:** N5's third, N8's second ("on two or more qubits" is unlabelled, 1613-1615), and N11's question 15 remark. Section 17 claims only two were not taken.
5. **Line 2105 and the live file.** Line 2105 says "decided" while the header says "Logan confirms at approval". The live file has since resolved this.
6. **4.3's `partial`.** 4.3's four `partial` rows have no legend and are not rule 2 words. N6's summary reads as if `partial` is gone.
7. **Where the gate runs.** The study does not say when or by whom the gate is run.

**6. What I did not do**
- I did not contact IBM or Atlas, run any IBM tool, create a service or account object, or import qiskit.
- I read `ibm_dryrun_v0.py` and `account.py` as text only.
- I opened no credential, key, token or account file, and no dot-directory under home.
- I did not read the installed qiskit-ibm-runtime source and fetched nothing from the web.
- I edited no tracked file. Every plant is in a scratch copy. I made no writes in either repo.
- I did not re-run the analysis instruments or the sizing instrument (hash-identical) or test `--submit`.
- I did not re-derive figures in sections 4, 6.1, 9.1 or 16.5, or check the header's hashes for drafts 1 to 8 or `84a7d2d6…`/`ef6aafa3…`.
- I did not verify the live file's 17 post-freeze lines.
- I ran a small pattern scan, not HonestHarness's tool, for secrets.
