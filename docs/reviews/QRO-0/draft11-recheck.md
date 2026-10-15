**1. Bottom line: NOT READY.**

There are two defects, AD1 and AD2. Both are AC2's class: the study says more about the gate than the gate checks. Everything else I was asked to check holds.
- AC1 and AC3 are fixed.
- Notes 1 to 7 and N9 are right.
- Every Note 2 fact is at its cited place.
- The post-freeze lines match the live tree, and the 164-file trial reproduces.

AD1 is a one-line text edit. AD2 is a three-line gate edit, which I tested, or two text edits. A diff-only re-check should then be enough.

**2. Setup**
- All 25 hashes in `SHA256SUMS.txt` match, before and after my runs.
- Python 3.12.9 with `-I` and the standard library only. Git 2.45.2, `--no-optional-locks` throughout.
- The live `QRO-0.md` and all 14 live `qro0/` files are byte-identical to the packet.
- The live tree is on branch `main` with no commits and no remote. It holds 164 files, all untracked. moth-quantum was clean at 3a73823 before and after.
- Scratch is `...\verifier-QRO0-r11\check\`.
- Identifier slips, so you can judge them:
  - Five 8-hex Atlas job-id prefixes appeared once. They sit in a docstring in `quantum_film/atlas/pauli_tile.py`, and my first masker passed 8-hex tokens.
  - One 20-character IBM job id appeared once. It was a MANIFEST path I printed unmasked while checking the file's structure.
  - After those, the masker covered both kinds, and all later output from the records or moth-quantum went through it.
  - The study's own line 592 carries one IBM job id. I saw it only because I read the draft.
- A mistyped grep pattern matched every line, and the harness saved the oversized result under `~/.claude/projects/.../tool-results/`. I did not open that file.

**3. Defects**

**AD1. Line 3062: the AC2 overclaim survives in section 17.**
- The AB1 row still says "The new gate `check_study.py` refuses any draft whose numbers disagree with its header".
- This is draft 10's line 2981, the third place AC2 named, with 36-37 and 2249-2250.
- Draft 11 reworded the other two: header lines 35-39 and section 15, lines 2293-2330. It left this one.
- The claim is false for draft 10's gate, which read two sentences, and for draft 11's, which reads six.
- It also contradicts the AC2 row in the same section (line 3118), which lists the six sentences.
- The AC2 row's "where" cell is "15, the gate". It omits "header", and "17" if this line is fixed.
- Fix: "The new gate `check_study.py` read two sentences (sections 13 and 15) against the header's draft number, and refused draft 9 for exactly AB1; draft 11 reads six (section 15)." Then make the AC2 "where" cell "header, 15, 17, the gate".

**AD2. The gate skips an off-form output-hash cell without a word, so a wrong hash passes.**
- Gate lines 137-143 are `if out and oh:` with no else.
- Section 15, lines 2312-2313, says "each row's hashes match the files". The docstring, lines 15-16, says each row "names the SHA-256 prefix of its file, and of its output when the output is a file there".
- Plants on copies, with the output cell `isolation_v0.out.txt` untouched. The output hash was replaced by:
  - `deadbeef...` (three dots, AC2's own plant class);
  - `deadbeef` (no ellipsis);
  - `C6F042D2…` (upper case);
  - `—`;
  - the old hash plus a suffix such as " (CRLF)".

  All were ACCEPTED, exit 0.
- The same wrong hash in the right form is REFUSED ("hashes …, the table says deadbeef").
- The lead's `plants.py` tried the `...` fault on the first-hash cell only.
- Fix, tested on a scratch copy: after `oh = …` add
  `if out and not oh: failures.append(f"section 15: {name}: the output cell names {out.group(1)}, but its hash cell does not parse")`
  and then update the gate's hash row.
  - With that patch the draft is ACCEPTED, and the three form plants (`...`, no ellipsis, upper case) are REFUSED.
- Alternative, text only: say in the docstring and section 15 that an output hash not written as `` `xxxxxxxx…` `` is skipped. Narrow "each row's hashes" accordingly.

**4. Per item**

**Item 1. AC1 to AC3**
- AC1 is fixed. Lines 657-661 read as the report suggested, and line 1139 agrees.
- AC3 is fixed in both places, lines 2274-2275 and 100-103. I checked the nine instruments.
  - The five analysis tools carry the 3a73823 pin and call `git rev-parse` and `git status`.
  - The three IBM tools and the gate do neither.
  - 5 + 3 + 1 = 9 table rows.
- AC2 is answered for two of its three places. The third is AD1.

**Item 2. The gate**
- **Audit.**
  - The gate is about 150 lines. It uses the standard library only.
  - It is read-only, with no network, no subprocess and no assert.
  - It has an import guard and `backslashreplace` output.
  - Its hash row (`1a4ad904…`) is right, and the diff is as described.
- **Run on the frozen draft:** `draft 11: 24 tables, 26 distinct sections cited, 9 instrument rows for 9 instruments`, then `ACCEPTED`, exit 0. The live path gives the same.
  - My independent GFM scan finds the same 24 tables, with no malformed row.
  - All 223 pipe-leading lines lie inside those tables.
- **`plants.py` re-run on copies.**
  - The log is byte-identical to `plants.log` (SHA-256 `59280211…`).
  - It has 30 runs: 26 faults refused by name, and 4 right variants accepted. That matches lines 3149-3161.
- **My own plants:** 54 runs, plus 6 against a patched gate.
  - **Refused as designed:**
    - an Oxford-comma list ("6, 8, and 21"), a no-break space, "section 9.7";
    - an extra delimiter cell, an extra pipe in a row, a ghost row, an indented row, a hyphen-named `.py`;
    - two output hashes swapped, section 17's labels moved out, "Contents" renamed (it fails closed).
  - **Accepted, as the study states:**
    - a ".md" skip;
    - a two-hyphen delimiter, a table in a blockquote, a row without its leading pipe and the rows after it;
    - a neutered gate with its own row updated, and older drafts' hashes.
  - **Accepted, not stated:**
    - section-reference forms: "6–21", "6-21", "6 or 21", "9.1/21", "SECTION", and bare numbers in section 17's "where" column;
    - a header row directly below another pipe-leading line (the table becomes invisible, count 23);
    - a blank or prose line inside a table, which hides the rows after it;
    - a row missing its trailing pipe but with an extra cell (pipes are counted, not cells);
    - delimiter cells after the first, a duplicate instrument row, a non-`.py` instrument, an unlisted `.out.txt`, and a `.py` in a subdirectory;
    - a reworded stale copy of one of the six sentences (the "every copy" rule matches exact wording);
    - the output-hash forms above (AD2).
- **The three descriptions.**
  - **Section 15 (2293-2330) and the docstring.** They mirror each other.
    - They state, and the gate does not do:
      - "each row's hashes match the files" (AD2);
      - "as many cells" (it counts pipes);
      - "every reference to one of this study's sections" (only references introduced by the word "section" are read).
    - The "does not check" list omits the unstated gaps above.
    - Its stated limits are accurate. I confirmed each by plant.
  - **The "every copy must name it" rule** works for the header and sections 13 and 15. The lead's four stale-copy plants are refused. It holds for the exact wording only.
  - **The table rule's stated limits** hold. The unstated ones are in the list above.
  - **The ".md" skip.**
    - It skipped 10 references in the draft, all METHOD.md or CERT-V2.md.
    - It also skips ", and see section 99" after a ".md" name (up to 12 letters). "Just after" understates that.
    - The form "METHOD.md (section 99)" is refused, which fails safe.
  - **Row parsing.** AD2, plus duplicates and `.py` only.
  - **Section 17's AC2 row** (3118) matches the gate's six checks. Its "where" cell is incomplete (AD1).
  - **Docstring item 4** is false for an off-form cell (AD2).

**Item 3. Notes 1 to 7**
- **Note 1** is right.
  - Section 8 (1015-1022) counts the producing commit as EQUAL only where recorded.
  - All five 6.1 cells (823-827) name two stoppers. I re-derived them from the strong-form column: −0.0193, −0.0220, −0.3225, and two UNMEASURED. Compile and bit order pass.
  - Short answer 2 (143-146) agrees.
  - Other places still read as drift-only: note 5 below.
- **Note 2** is right, labelled ("by inference", 983) and sound. I checked each fact at its place in moth-quantum:
  - VALIDATION.md:19-27 has `features: []` and "So **no `run_quantum`** (hardware)".
  - :925 reads "One Atlas job of the six allowed was used". :1063-1064 reads "the throwaway key's last five jobs". :1097 reads "All six of the Atlas account's jobs are now used". :925 names no account itself. It ties in by 1 + 5 = 6.
  - `pauli_tile.py:143-145` is the request body and has no `provider_name`. The runner uses it (tools/pauli_atlas_run.py:172), and `provider_name` appears nowhere in the code or docs searched.
  - The `tomography-api-v2` description, fetched 2026-09-25T17:32Z, has `provider_name` default `aer`.
  - The two 2026-09-25 lines sit in the entries at VALIDATION.md lines 15 and 170 (both dated 2026-09-25). The law jobs' entries are 2026-09-26 (lines 870 and 1061).
  - **Count:** 20 string `mode` values, all `emu`, in 14 files from 8 distinct probe jobs, plus one object-valued `mode`. Zero files under `2026-09-25/p3` and `2026-09-26/p3` hold a `mode` key or an `emu`/`qpu` string.
  - **Caveat:** `features: []` was read on 09-25, and the law jobs ran on 09-26.
- **Note 3** is right (1526-1527, 1542-1552). It agrees with line 1769 (control `audit-head-mismatch`), 1826-1828 and 2191. "Four conditions" survives only as history (3071).
- **Note 4** is right.
  - Section 10 (1695-1698) matches 9.2 (control names at 1535 and 1562), section 11 (1766-1769) and section 13 (1923-1925, 2018-2019).
  - The Bell test is BELIEVED (1643-1644).
  - Question 15 (2171-2172) says the same as 9.1 (1448-1449).
- **Note 5.** The header and the decided list now agree.
- **Note 6.** The legend (462-464) names exactly the five words in the state column. `absent` and `partial` are not rule 2 words.
- **Note 7.** Lines 2293-2294 say who runs the gate and when.
- **N9 at question 9** (2095-2100) agrees with 1894-1895.

**Item 4. Post-freeze lines**
- `LICENSE` is MIT with "Copyright (c) 2026 Logan W.". `LICENSE-docs.md` grants CC BY 4.0 for documents and data and cites questions 10 and 18. `.gitattributes` is `* -text`. All three are identical to the packet copies.
- `git status` says "On branch main, No commits yet". `git log` has nothing. `check-attr` shows `text: unset` everywhere.
- The header (60-65), the decided list and question 10 (2047-2071, 2149-2155), the floor (1951-1952), the confirmation list (2241-2242) and section 17 (3101-3108) agree with each other and with the tree. I could not check Logan's verbatim words. I checked only that the copies agree.
- **Re-measured on a scratch copy**, committed and cloned with `core.autocrlf=true`: 164 files in the clone, 164 byte-identical, 8 CRLF files. That equals the lead's count.
  - The 8 CRLF files are the 5 `.out.txt` outputs and 3 `ibm-*.log` records logs.
  - **Control with no `.gitattributes`:** 155 of 163 files changed (every LF file, converted on checkout). So the trial discriminates.
  - **`autocrlf=input` without the attribute:** the 8 CRLF files changed. `autocrlf=false`: nothing changed either way.
  - **Why it may differ from the lead's:**
    - any file added to or removed from the tree;
    - a copy that included `.git`;
    - a different count of CRLF files, if an output or log is rewritten with other line ends.
  - Today's tree equals the frozen packet's, so I got the same numbers.

**Item 5. Sweep**
- All "section" references resolve. The question, rule, stage, cause, refusal and step numbers are in range.
- All 24 tables are well-formed.
- Section 15's 9 rows match the files. I re-ran the five analysis instruments with `GIT_OPTIONAL_LOCKS=0`. Each wrote its kept output byte for byte, which supports lines 3150-3151.
- Every mention of draft 9 or later is current. Line 3146 is the one exception (note 8).
- The new counts are supported: 26, 4, 164, 8, 20, 8, six sentences, four checks, nine instruments, 6,000 tampers.
- No secret-shaped strings in the added lines or the gate.

**5. Notes**
1. **Gate limits not stated (tables):** a header row directly below a pipe-leading line is invisible. A blank or prose line inside a table hides the rows after it. Only the delimiter's first cell is read. Pipes are counted, not cells.
2. **Gate limits not stated (references):**
   - dash, "or" and slash lists, and "SECTION";
   - bare numbers in section 17's "where" columns.
3. **Gate limits not stated (rows and numbers):**
   - duplicate rows (the count line shows 10 for 9, and nothing compares);
   - non-`.py` instruments and unlisted outputs;
   - reworded stale draft sentences.

   Nothing compares the table or section counts.
4. **MEASURED labels name no instrument:** the 26 plants (3149-3161) and the clone trial (2060-2061). The study defines MEASURED as "by an instrument named". `plants.py` is in the packet only.
5. **Drift named alone, after note 1:** lines 198-199, 843-845 and 1785-1790 give drift (and readout) as the reason and omit the `unknown` commit. The "isolated as quantum?" cells name at most one cause. XEB's cell says "strong form not above ε" where rows 1 and 2 say "drift not excluded".
6. **Lines 428 and 475** call the Atlas data "Moth's emulator" under section 4's READ. Section 8 now says the law jobs' emulator is inferred.
7. **Legend, 462-464:** "They are not a crate's field values" is true of `absent` and `partial`. `unknown`, `unexposed` and `none` are rule 2 words, and a crate does write them.
8. **Line 3146** cites "line 2105", which is draft 10's numbering. Draft 11 has nothing there to match.
9. **`.gitattributes`** is a repo file, not the study. Its comment says "the rest LF", but three records logs are CRLF. It also says the CRLF vector "failed its own hash in a fresh clone". moth-quantum's `.gitattributes` and VALIDATION.md:326-328 say it "would have failed" (re-frozen before the first commit).
   - Under `autocrlf=true` the 8 CRLF files survive even without the attribute. In that configuration it protects the 155 LF files.
10. `LICENSE-docs.md` grants CC BY 4.0 by URL and carries no legal code. That is Logan's call.

**6. What I did not do**
- I did not contact IBM or Atlas. I ran none of the three IBM tools, created no service or account object, and imported no qiskit.
- I opened no credential, key, token or account file, and no dot-directory. moth-quantum's `.atlas/` is untouched. Git's own reads aside.
- I edited no tracked file and wrote nothing in either repository. Plants and the clone trials are in scratch copies.
- I did not re-derive the figures in sections 4, 6.1, 9.1 or 16.5.
- I did not re-verify earlier-confirmed material: the RO-Crate quote, the Creative Commons FAQ quote, the other projects' LICENSE files, or the header hashes for drafts 1 to 8 and `84a7d2d6…`/`ef6aafa3…`.
- I did not check Logan's verbatim words, or the lead's `plants.py` against anything but its own log.
- I did not test the gate on another platform. The glob is case-insensitive on Windows.
