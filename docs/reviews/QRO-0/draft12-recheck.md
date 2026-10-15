**1. Bottom line: READY.**

I found no defect. AD1 and AD2 are answered correctly, and I found no new contradiction. Two phrases of the new contract are broader than the gate on a literal reading (N1, N2). They are notes, not defects, for these reasons:
- Neither has an instance in the study.
- No design property depends on either.
- "It checks nothing else" already closes the world.

If the lead holds the literal reading, each is a phrase-level fix. Notes N5 to N8 are the ones worth acting on.

**2. Setup**
- All 26 hashes in `SHA256SUMS.txt` matched, before and after my runs.
- I used Python 3.12.9 with `-I` and the standard library, and git 2.45.2 with `--no-optional-locks`.
- The live tree is on `main` with no commits. It now holds 165 files. Its `QRO-0.md`, all 15 `qro0/` files, `.gitattributes`, both licences and the records README are byte-identical to the packet.
- moth-quantum is clean at 3a73823. Neither repository changed. Every plant, mutant and clone trial ran in scratch copies.
- For history I read the frozen packets of the draft 10 and draft 11 re-checks: the gate sources, diffs, reports and `plants.py`. I did not read those verifiers' own work directories.
- No identifiers were printed. I masked job-id and UUID shapes in all harness output.
- Two scratch snippets that edited my own mutation script, and the version check, ran without `-I`.
- I stopped two of my own processes: one mutation runner and one hung mutant gate.
- Line numbers below are the frozen draft 12's, unless marked "gate" or "plants".

**3. Defects**

None.

**4. Per item**

**Item 1: AD1**
- **AB1 row (3098) is right.**
  - I ran draft 10's gate (`2aac0bb2…`, from the r10 packet) on frozen draft 9. It refuses exactly two failures, section 13's and section 15's, which is AB1.
  - Its source tests `want in flat` over the whole text, so "wherever they stood" is true.
  - Draft 11's gate (`1a4ad904…`) reads six sentences, each scoped to its own place.
- **AC2's "where" cell (3154) is right.** The 10-to-11 diff shows draft 11 changed the header, section 15 and the gate for AC2, and not section 17. The section 17 fix is draft 12's, recorded as AD1's "17" (3212).
- **"Not changed" (3181-3183) is right.** Draft 10's line 2105 reads "The code's licence is decided: MIT (above)". The header said "Logan confirms at approval".
- **"Lead's checks" label (3185-3187) is right.** `plants.py` is in the draft 11 packet, and is not in `qro0/`. It has 30 runs, 26 faults and 4 variants.
- **Draft 11's re-check entry (3204-3208) is faithful** to the report.
- **Draft 12's in-place edits are all recorded.** I found four, in AD1 (3212), note 4 (3230) and note 8 (3236).

**Item 2: AD2 and the rewritten gate**
- **Audit.** The gate is 213 lines. It imports only `hashlib`, `re`, `sys` and `pathlib`, and is read-only. It has no network, no subprocess and no `assert`. It has an import guard and `backslashreplace` output. Its row (`105e6190…`) is right. The 11-to-12 gate diff matches the description.
- **Run.** The frozen draft, copied as `QRO-0.md` beside `qro0/`, prints `draft 12: 25 tables, 28 distinct sections cited, 10 instrument rows for 10 instruments` then `ACCEPTED`. The live path gives the same.
- **Independent table scan.** My own GFM-style scan finds the same 25 tables. It finds no ragged row and no pipe-led line outside a table. The study has no fenced code block.
- **AD2 is fixed.**
  - A right hash in an off form is refused as "does not parse". Forms tried: three dots, no ellipsis, upper case, dash, empty, two hashes, and a " (CRLF)" suffix.
  - Extra text, a bare name or a path prefix in the output cell is refused.
  - A swapped output hash is refused.
  - A wrong hash in the right form is refused as "hashes … the table says …".
- **The four positive claims are kept on their grammar.** Section 15's description (2308-2359) and the gate docstring mirror each other. In detail:
  - **Draft numbers.**
    - All six sentences are checked.
    - A moved or deleted sentence is refused as "no '…'".
    - A stale copy in its own place is refused.
    - A wrapped sentence is accepted.
  - **Tables.**
    - These are refused: a stray pipe-led line, one above a header, a blank or prose line inside a table, an escaped or lettered end, an extra or missing cell, and a delimiter cell with two hyphens, a lone colon, inner spaces or trailing text (in any cell).
    - These are accepted, as stated: a blockquote table, a table behind a list marker's continuation lines (refused), trailing spaces, `:---:` and `---:`.
  - **References.**
    - `Section`, `SECTION`, `sEcTiOn`, wrapped, tab and NBSP forms are read.
    - Joiners read: and, or, serial comma, "to", slash, hyphen and en dash.
    - A subsection is read too.
    - The `.md` skip works. The tightening works: "METHOD.md, and see section 99" and "METHOD.md; section 99" are refused. "METHOD.md (section 99)" is also refused, which fails safe.
    - "Where" cells: "99", "4.4, 99", "4.4 and 99", "header, 99" and later rows are refused. A "Where" header in any case is read. "where changed" and tables outside section 17 are not read.
  - **Instruments.**
    - Refused: duplicates, a row for a missing tool, a missing output, an unlisted file, a directory, a `.pyc`, a README, `__pycache__`.
    - Accepted: a new tool with a correct row, with or without an output.
- **Two literal-reading corners (N1, N2).**
- **Is "It checks nothing else", with its "Among" list, honest?** Yes.
  - I read every failure site; each falls under one of the four checks.
  - Every "Among" item is true by plant.
  - Unchecked cases that no positive claim covers are in N3, with a view on each.
- **False refusals a reasonable edit could trip** are in N4.

**Item 3: `check_study_plants.py`**
- **Audit.**
  - It is stdlib only (`locale`, `re`, `shutil`, `subprocess`, `sys`, `tempfile`, `pathlib`).
  - With TMP redirected into scratch, it left nothing behind. The base copy gained no files.
  - It writes only to its temporary copies.
- **Run.** It reports `51 faults refused by name, 4 right variants accepted, 0 unplaced, 0 wrong` and `ACCEPTED`. The output is byte-identical to `plants12.log`.
- **Docstring against code.** It matches one for one: 10 + 11 + 12 + 18 = 51 faults, plus 4 variants.
- **"At least one for each check above" is true** at the level of the four checks.
- **Can a plant pass for the wrong reason? Yes.**
  - The pass test is "exit 1 and any `REFUSED:` line" (plants 249-255), not the targeted check.
  - So "refused by name" means a failure was named, not that the targeted check fired.
  - I broke the gate at one point at a time in 55 copies and re-sealed its hash row each time. The instrument caught 38. Three of those were caught only because the break fails the draft itself. It missed 17, of which 3 are verdict-equivalent.
  - In every missed case I planted the fault against the real gate, and it refuses each one. These are gaps in the test, not in the gate.
  - Spot-checks against `plants12.log`:
    - Line 14, "two-hyphen delimiter": refused as "in no table". The plant hits the first cell, so a gate that dropped the later-cell hyphen count still passes it.
    - Line 12, "spaced delimiter, short row": a gate that cannot see spaced delimiters also refuses it.
    - Lines 5-6, the section 13 and 15 plants: a stale copy remains in the section, so a whole-text scope still refuses them. The own-place property is not isolated.
    - Lines 34-35 and 40-45: the row-parse and AD2 plants are refused with "(+1)". The extra failure is the collateral "unlisted output". The AD2 plants use a wrong hash (`deadbeef`), so loosening the parse still refuses them. The explicit parse check is therefore untested.
  - The table of survivors is in N5.

**Item 4: notes 1 to 10**
- **Notes 1 to 3 are right** (3216-3229). Each listed refusal is confirmed by plant.
- **Note 4 is right** (3185-3187, 2070-2074), apart from the counts in N8. The trial reproduces on the current tree.
- **Note 5 is right.**
  - The producing commit is named at 204-206, 851-854 and 1799. These agree with section 8 (1026-1028).
  - The 6.1 table (829-835) is consistent with section 8's rule (1024-1036) and section 7's classes (894-903). Row by row:
    - Rows 1 to 3 read "strong form not above ε; producing commit `unknown`".
    - The coherence rows read "drift UNMEASURED, `none`".
    - Every "isolated as quantum?" cell names "not isolated from the pipeline" and "readout UNMEASURED, `none`".
    - The twin clause is right: "integrity against both twins" for five-crystal, "a signal against the uniform twin only" for forbidden share and XEB, and none for the coherences.
  - XEB's cell is now worded like rows 1 and 2.
- **Note 6** is addressed with a caveat (N7). The 4.3 row (483) now says "engine".
- **Note 7 is right** (469-472). The legend lists exactly the five state words. `unknown`, `unexposed` and `none` are rule 2's words (647-653); `absent` and `partial` are not.
- **Note 8 is right.**
- **Note 9 is right.**
  - The `.gitattributes` comment matches the tree: 8 CRLF files, being 5 outputs and 3 of the 4 records logs. The fourth log is LF, and the other 157 files are LF. Its "would have failed" matches moth-quantum's `.gitattributes`.
  - VALIDATION.md:326-330 is the "Found on the way" entry of 2026-09-25. It says the clone "would have" failed and that the vector was re-frozen as LF.
- **Note 10 is correctly left to Logan.** `LICENSE-docs.md` names CC BY 4.0 by URL only.

**Item 5: sweep**
- All "section" references resolve (the gate does this).
- There is no stale draft number. I read every "draft 9 to 13" mention.
- The tables are well formed, and section 15 has 10 rows for 10 tools: 5 + 3 + 2.
- 51 and 4 are supported. I found no other unsupported count except N8.
- The header's account of drafts 11 and 12 (35-46) is right. Hashes `8e5936b7…` and `f74f112a…` check.
- Secret-shaped scan of the added lines, both tools, `gitattributes.txt` and the plants log: nothing.

**5. Notes**

1. **N1: "where" cells and the serial comma.** The claim at 2331-2332 (gate docstring 17) reads bare numbers "between commas or 'and'".
   - The cell "4.4, 6, and 99" is ACCEPTED, so 99 is unread. "4.4 and 99" and "4.4, 6 and 99" are refused. The code is `re.split(r",\s*|\s+and\s+", cell)` at gate line 160.
   - Prose references do read ", and": `SEP` has `,? and `.
   - The study's own style has no serial comma, and the real cells use none.
   - Fix: split on `,\s*(?:and\s+)?|\s+and\s+`, or add "not after ', and'".
2. **N2: stale copies in another place.** The draft 12 wording (2318-2320, gate docstring 9) reads "every copy of these sentences" in the header and sections 13 and 15.
   - On its literal reading that is stronger than "own place". Planted and ACCEPTED: a stale section 13 sentence in the header, in section 15 or in section 17; a stale section 15 sentence in the header or section 13; a stale header sentence in section 13 or 15.
   - Draft 11's wording was unambiguous.
   - Fix: say "each in its own place", or scan all three scopes.
3. **N3: unchecked cases no positive claim covers.** Whether each belongs in the "Among" list:
   - The header's date (a stale date passes): add.
   - Which tool an output belongs to (outputs and hashes swapped between two rows pass): add, as the first bullet nearly covers it.
   - A stale copy in another place: add, unless N2 is fixed in the text.
   - Spaced dash or slash, "through", "and/or", "&amp;", "6,99": already "another form".
   - Contents against headings, and duplicate headings: optional.
4. **N4: false refusals a reasonable edit could trip.** All fail closed, naming the line.
   - "section 4.5, 65 jobs", "section 13, 2026-10-14" and "(section 4.4, 1.58 s)" read the following number as a section. "section 16.5, 77,824 shots" reads 77.
   - A pipe-led line inside a future code fence, such as a shell pipeline.
   - A trailing space after an instrument row's last pipe ("a row does not parse").
   - A hyphenated tool name gives "has no row" although a row exists.
   - ".out.txt" in an output cell's prose.
   - "METHOD.md's section 21" or "METHOD.md (section 21)".
   - A form feed or NEL inside a table row, because the gate uses `splitlines()`.
   - A `####` three-level reference such as "9.7.1" reads "9.7".
5. **N5: plants-instrument gaps.** The gate refuses each of these; the plants miss them.

   | Property | Why it survives |
   |---|---|
   | A missing or malformed header line | no plant |
   | Own place for the header, section 13 and section 17 labels | plants leave a stale copy that is refused anyway |
   | Hyphen count in a later delimiter cell | the plant hits the first cell |
   | "Where" cells in later rows | the plant edits the first row |
   | "Where" cells joined by "and" | the plant uses a comma |
   | "Where" scope limited to section 17 | no plant |
   | The tightened `.md` skip | only the right variant exists |
   | The explicit row-parse failure, and the strict output-hash parse | collateral failures refuse the plants |
   | A hyphenated name | no plant |
   | Spaced delimiters recognised | the plant is refused either way |
   | `backslashreplace` | dropped; see below |

   - Draft 11's `plants.py` had a "row-unencodable" plant (a U+2212 in a row). It was not carried over, and the gate's "a failure line must print, whatever it quotes" property is now untested. The gate keeps it (it prints `\u2212`), and 25 of the 26 old fault plants are kept. So "the plants are kept" (3231) holds by class only.
   - Suggested fix: give each plant an expected message substring and require a match, and add the plants above.
6. **N6: plants-instrument robustness.**
   - The subprocess call has no timeout. One of my mutants made the gate loop forever on indented tables, which would hang the instrument.
   - It assumes LF. On a CRLF study the gate accepts but the instrument dies with a bare `StopIteration`.
   - `locale.getencoding()` needs Python 3.11 or later, which is unstated.
7. **N7: line 435.** "on its emulator" still stands under section 4's "READ, unless marked", with only the pointer "section 8 gives the evidence". Section 8 (992) labels it an inference. Suggest "by inference". The 4.3 fix is clean.
8. **N8: Q10's counts (2070-2074).**
   - 164, 163 and 155 are draft 11's tree, and the study does not say so. The tree is now 165 files because of `check_study_plants.py`.
   - I repeated the trial on a scratch copy of the live tree. With `.gitattributes` and `autocrlf=true`, 165 of 165 files are byte-identical, with 8 CRLF among them. Without it, 156 of 164 files change, every LF one.
   - The finding holds; only the numbers are stale. Date them, or re-measure.
9. **N9: trivia.**
   - Note 9's "names" (3237) should read "counts": the comment says "three of the records' logs".
   - The header says draft 12 "answers … the re-check's notes" though note 10 is left (41, 3240).

**6. What I did not do**
- I contacted neither IBM nor Atlas, ran none of the three IBM tools, created no service or account object, and imported no qiskit.
- I opened no credential, key, token or account file, and no dot-directory. I read moth-quantum's tracked `.gitattributes` and `docs/VALIDATION.md` only.
- I did not re-run the five analysis instruments. Their files and outputs are hash-identical to the draft 11 packet, which the earlier re-check re-ran byte for byte.
- I did not re-derive figures in sections 4, 6.1, 9.1 or 16.5, or Logan's verbatim words.
- I did not verify "written on Windows" for the three logs.
- I did not run the old `plants.py` against the draft 12 gate, except its unencodable-character case.
- I did not test the gate on another platform.

Files are in `<scratch>\verifier-QRO0-r12\check\`. The harness is in `tools\` (`h.py`, `p1.py` to `p7.py`, `mutate.py`). The mutation logs are `mutation.log` and `mutA.log` to `mutD.log`.
