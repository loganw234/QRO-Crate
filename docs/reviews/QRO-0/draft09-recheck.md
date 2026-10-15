**1. Bottom line: NOT READY.**

There is one defect, AB1: two stale draft numbers in sections 13 and 15. It is the same slip as W4, X6 and Z7, and the fix is two one-line edits. AA1 to AA3 are answered correctly and everywhere. I found no new contradiction in the design text.

**2. Setup**
- All 19 hashes in `SHA256SUMS.txt` match.
- The live draft, README and 13 `qro0/` files are byte-identical to the packet, before and after my runs.
- moth-quantum is clean at 3a73823 and HonestHarness is clean at b69ed76.
- I used Python 3.12.9 with `python -I` and the standard library only.
- I read all 2,946 lines once and concentrated on the 209 changed lines.
- Scratch directory: `<scratch>\verifier-QRO0-r9\work\`. It holds the scripts, `logs\`, `plants\` and `privacy_control\`. All plants are in copies.
- I made two in-memory GETs of public text (nothing saved or run): the Creative Commons FAQ, and Qiskit's GitHub source at tag 0.50.0 (`base_primitive.py`, `qiskit_runtime_service.py`). The installed runtime sits under a dot-directory my rules exclude. Disregard those two checks if you count them out of bounds.

**3. Defects**

**AB1. Stale draft numbers left by the version bump.**
- Lines 1787-1788 say "Drafts 1 to 7 went past verifiers, and draft 8 goes next". Lines 2200-2201 say "the re-checks of drafts 2 to 7". The header (30-35) says draft 9 is next and cites draft 8's re-check as a source (1993).
- Both passages are byte-identical to draft 8's (lines 1754 and 2143-2144). Section 17 records the same slip at W4 (2622), X6 (2687) and Z7 (2841).
- Fix: "Drafts 1 to 8 went past verifiers, and draft 9 goes next", and "re-checks of drafts 2 to 8". The second edit also puts the draft-8 re-check, the stated source of the CC FAQ reading, into section 15.
- It has now recurred four times by hand. A gate would stop it: have the doc check compare the "goes next" number and the "drafts 2 to N" bound with the header's draft number.

**4. Per item**

**Item 1: AA1 to AA3.**
- I modelled the log as written (`custody_model.py`, 35 cases, 0 mismatches):
  - An appended withdrawal keeps the chain valid, and earlier lines stay byte-identical.
  - An in-place edit or withdrawal of a line that has a successor is caught at the next line (lines 0 to 2 tested).
  - An edit, drop or tail truncation of the last line, or a forward rewrite with recomputed hashes, shows nothing in the log. Section 9.2 states this limit at 1502-1504.
  - With an audit record's head hash, 6,000 random edits, drops and rewrites at or before the audited head were all caught by the chain or the head check. Forward rewrites are never caught by the chain and always by the head.
- Everywhere check:
  - AA1 is in 9.2 (1495-1498, 1516-1520), section 11 (1717-1718), P0 (1960-1961), question 17 (2123-2125), the confirmation list (2172-2174) and section 17 (2898).
  - AA2 is in 9.2 (1491-1492, 1502-1507), section 11 (1716, 1719) and section 17 (2899).
  - AA3: line 2816 now says "six". Line 2746's "six" is correct for its draft.

**Item 2: the notes taken.**
- **`kind-not-qpu`:**
  - The numbering is 1 to 5, consecutive, and nothing else refers to refusal numbers.
  - It sits fourth, before `selector-late`.
  - Its scope ("unit or crate") matches `simulator-in-real` (1715) and stage 4 (1827-1828).
  - "IBM against Atlas is a rehearsal by kind, and `question-differs`" fits 944-947 and 2938-2939.
  - The Atlas `simulator` claim holds: all 20 tracked `"mode"` values in the 2026-09-25/26 records are `emu`.
- **Cause 3:** line 690 and 6.1 (775-778) agree with 4.3 (456). The IBM 2026-10-05 records have no `code_commit`, and VALIDATION.md 1614, 1689, 1695 and 1698 name the run-clone commits.
- **Root slots:** the header placement fits `datePublished` and the identity definition at 1467-1469, and `none` is a rule-2 word. Residuals are in N7.
- **Dry run unavailable:**
  - The header no longer carries the claim, so there is nothing to separate there.
  - Stage 5 (1841-1858) and question 9 (2029-2032) keep the two lookups (MEASURED) apart from the refusal path (READ).
  - At the source, `base_primitive.py` lines 133-138 contain the three earlier fragments and "may be restricted" (138) exactly. Lines 1102-1111 and 1004-1029 of `qiskit_runtime_service.py` are as described.
- **Licences:**
  - Logan's condition is on the confirmation list (2175-2176) and in 1994-1996.
  - Providers' terms are BELIEVED (2001-2004).
  - Documents' licence is recommended as CC BY 4.0 (2089-2090).
  - The CC quotation (1991-1993) is exact, and appears once in the FAQ page.
- **Coin toss:**
  - `description_md`'s Output section lists `output` (the majority), `heads`, `tails` and `shots`, so 1585-1586 is right.
  - The new quotation (1601-1602) is exact after whitespace normalisation: the source breaks the line between "random-number" and "service".
  - "Moth's own IBM account" (1551-1552) matches the `qpu_token` description exactly.
- **Tools:**
  - The diffs are two hunks in `free_tier_unit_v0.py` and three in `ibm_dryrun_v0.py`, as section 17 says.
  - The AST of the draft-8 dry-run tool, with the rename applied, equals draft 9's. That tool was parsed only, never run.
  - The sizing output is byte-identical (`a0d3f532…`, also under `-O`).
  - Plants on copies:
    - Bracket low end raised to 100,000: `REFUSED`, exit 1, also under `-O`.
    - The same plant on the draft-8 assert: `AssertionError`, but under `-O` it silently reports K-M as 100,001 shots.
    - Refusal condition inverted: fires on v0's good bracket, exit 1.
    - Refusal deleted: a bad bracket passes silently, and a good bracket gives byte-identical output (see N12).

**Item 3: sweep.**
- 314 section, question, rule and stage references resolve.
- All 21 tables are well formed. Section 11 now has 30 rows (27 plus the 3 new).
- Section 15 matches on all 8 instruments, 5 outputs, 4 record hashes and the header's draft-8 hash. `ef6aafa3…` is the draft-8 tool. `84a7d2d6…` is not in the packet, so I could not check it.
- No trailing whitespace, tabs or CRs. The non-ASCII set equals draft 8's. Backticks and `**` balance.

**Item 4: privacy.**
- HonestHarness's `findings()` (its source executed as-is) gives 0 hits over the draft, both tools and the README, and over the rest of the packet.
- Four planted faults in copies (Windows path, Git Bash path, address, key) were all caught.
- Added lines contain no value-shaped strings, only the word "token".

**5. Notes**
- **N1.** The `withdrawal-in-place` row (1717) lacks the "with a line after it" qualifier that `custody-chain` got (1716). On the last line the plant is accepted (model case S2b).
- **N2.** Cause 3 is "EQUAL in what was sent" (690, 775-778), but the verdict rule (984) just says "what was submitted ... EQUAL". Moot for v0, but a later verdict could pass with the kit's commit unrecorded. Add a clause: the commit is EQUAL where recorded, and the statement names `partial` or `unknown` otherwise.
- **N3.**
  - Section 8's "What a comparison declares" list (921-937) omits the real-or-rehearsal declaration, which appears only inside refusal 4 (951).
  - 6.1's declaration (763-767) is silent on it.
  - "Since Atlas is Moth's emulator" (955-956) is broader than the evidence, which is that v0's Atlas runs were `emu`.
- **N4.** The head hash (1491-1492, 1505-1507) has conditions the text does not state:
  - Lines after the head are uncovered.
  - The record must be held by someone other than the log's writer (model case: a writer who also rewrites its own record passes).
  - The log must be shown to a checker.
  - "Once a log has been audited" misnames what is audited, which is a crate.
  - An auditor with no custody log has no head hash and no absence word.
  - The first line's predecessor is unspecified, so dropping line 0 shows only if it is pinned.
- **N5.**
  - Section 12 (1732-1779) does not list the log-tail limit.
  - No M1 stage says when the four custody controls are met (1802-1805, 1864-1871).
  - Section 10 does not name the custody check.
- **N6.**
  - `partial` (690, 776) is not in rule 2's list (625-631). It is 4.3's state word.
  - The Atlas cell (690) is silent on the producing commit, though Atlas lines carry `code_commit` (2074-2075).
- **N7.**
  - Prose still says "empty" at 1555 and 1775, where the data say `none`.
  - Rule 4's header list (642-647) does not name the two slots.
- **N8.** "Moth's own description says as much" (1601) over-reads the quoted clause, which disclaims guarantees and does not address proving quantumness. "On two or more qubits" is unlabelled (BELIEVED).
- **N9.**
  - The bold line at 1841 and question 9's "So..." (2031-2032) are conclusions without their own label.
  - Draft-8 note 7b (the probe passes the instance; the runtime's lookup at line 1107 does not) is neither taken nor declined.
- **N10.**
  - The header (55-57) still says flatly that "the code's licence is MIT", while 1994-1996 says Logan confirms at approval.
  - "The usual choice for documentation" (2084-2085) is unlabelled.
- **N11.** "Unless its author fetched them" (1413-1415) is redundant with "made by anyone but its own author", and question 15 (2105-2106) is narrower.
- **N12.**
  - `-O` still strips 22 other asserts across five instruments. Only the bracket check was hardened, and the draft claims no more.
  - The new refusal cannot fire on v0's data, and no section 11 control plants it.
  - README line 195 still describes the first tool version's gate.

**6. What I did not do**
- I did not contact IBM Quantum or Moth's Atlas, run any of the three IBM tools, create a service or account object, or import qiskit.
- I did not open credential, key, token or account files, dot-directories under the home directory, or `.atlas/`.
- I did not print the engine record's owner id. I listed key names and lengths only.
- I did not re-derive figures in sections 4, 6.1, 9.1 or 16.5, which are unchanged and confirmed earlier.
- I did not re-run the other four analysis instruments. They are hash-identical to the packet.
- I did not check the header's draft hashes 1 to 7, the first probe's tool hash, or the README's 12:36 scratch-trial claim. None of those is in the packet.
- I did not test `--submit`.
- Brief points: the brief puts the "dry run unavailable" wording in the header, but draft 9's header no longer carries it. The brief also did not mention the draft-number lines where AB1 sits.
