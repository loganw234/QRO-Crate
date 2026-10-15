## 1. Bottom line

**NOT READY.** I found seven defects, P0-1 to P0-7, and one group of text slips, P0-8. None touches the vocabulary table's design, the canonical bytes, the custody chain, the nine controls or the runner's framework, and every fix is small. A scoped re-check of the fixes will do.

## 2. Setup

- **Packet hashes.** `sha256sum -c SHA256SUMS.txt` reported all 207 lines OK. The tree holds 208 files: two `qro/__pycache__/*.pyc` files are not in the sums (written at 19:41:43, five seconds after them). I deleted them from my copies. A read-only hash comparison shows the live tree is the packet: 206 files, nothing extra, no commit.
- **Environment.** Windows 11, Python 3.12.9, pytest 9.1.1, ruff 0.11.9, git 2.45.2.windows.1. moth-quantum was a clean 3a73823 before and after. cft-fp256's HEAD is c918cb3, not the study's f22e8d2, so I read the cited lines with `git show f22e8d2:`. HonestFramework is at 65447fd and HonestHarness at b69ed76, both clean.
- **Copies.** `…\scratchpad\verifier-P0\check\` holds my copies and all my scripts. `tree` took the reader, checker, custody, privacy and vocabulary plants. `runA`, `runB` and `runC` took the runner runs, and `runC` the mutated runners. `runA` is `git init`'d with no commit, and `runB` has one scratch commit.
- **Full runner.** In `runA` with `QRO_MOTH_ROOT` set and `GIT_OPTIONAL_LOCKS=0`, so the instruments' `git status` could not refresh moth's index: **16 of 16 passed, none skipped, 71 s**. Run id `…-nocommit+dirty`, twin digest `631257cd…` as in the ledger. `--budget quick` ran 13 of 13 in 12 s.
- **Test suite.** `pytest` gives 137 passed, also under `-X dev -W error`. The ledger's 126 reproduces.
- **Plants.** About 500, all in copies: bytes, values, files, raw forms, custody, privacy, registry, runner and vocabulary.
- **Download.** I streamed RO-Crate's context once, straight into `sha256sum` and not saved, under Logan's standing permission for small downloads. It is 196,942 bytes and equals the pinned copy.
- **Slip.** My first file listing and my print of `records/2026-10-14/README.md` put job ids in my own tool output. None are in this report, and later output was hashed or masked.

## 3. Defects

**P0-1. The reader accepts a second spelling of a time.**
- `qro/spelling.py:22` (`_TIME`) uses `\d`, which matches any Unicode decimal digit, and `int()` reads it. `:23` (`_DATE`) is refused only because CPython's `date.fromisoformat` happens to reject such digits.
- Plant: the twin's `qro:writtenAt` rewritten in Arabic-Indic digits (still pure-ASCII bytes, `\u0662\u0660…`). `python -m qro check --fixtures` exits 0 and prints `ACCEPTED 631257cd…`, the twin's own digest, because the header is stripped. Fullwidth digits are accepted too.
- Same in a custody line's `at`: `check_log` accepts it, and the line's hash differs from the ASCII spelling's (heads `ead61c4b` against `817cd237`).
- This falsifies CLAUDE.md:43 and the "second implementation" story of 9.2.
- Fix: `re.ASCII` (or `[0-9]`) on both patterns, with Unicode-digit cases in `tests/format/test_spelling.py` and `test_refusals.py`.

**P0-2. Hostile input crashes the checker instead of being refused by name.** A crash exits 1, the same status as a refusal. This falsifies the `checker.check` docstring, `__main__.py`'s "1 is refused (by name, at a location)" and HonestFramework §2. Six crash classes, all reproduced through the CLI:
- `qro/reader.py:78-79`: an integer of 4301 or more digits raises `ValueError`, which is not a `JSONDecodeError`, so `e.lineno` gives `AttributeError`.
- `qro/reader.py:74`: `RecursionError` on deep nesting (100,000 levels; the threshold is near 1,000).
- `qro/spelling.py:82` and `:91`: a 4301-digit `contentSize` or rational makes `int()` raise `ValueError`.
- `qro/custody.py:61`: a list or object as `event` raises `TypeError: unhashable`.
- `qro/custody.py:59` and `:93`: NaN raises `ValueError` in `compact` or `dumps`. `:56` and `:90` also hit `RecursionError`.
- `qro/fixture.py:27-32` with `qro/checker.py:109`: NaN or deep nesting in a raw result crashes, because the seam catches only `RawFormError`. Every parcel's raw-form reader inherits this hole.

Fix:
- Catch `(ValueError, RecursionError)` in the reader and use `getattr(e, "lineno", None)`.
- Compare `len(value) &lt;= 19` before `int()`.
- Add `isinstance(event, str)` and wrap the custody parses.
- Catch `Exception` around the raw-form reader and refuse `raw-form`.
- Add a sweep test of these inputs.

**P0-3. The stage registry cannot fail as CLAUDE.md:17 claims ("fails a test file, or a tool's own check, that no stage runs").** I checked each of these in a copy. Stray test directories and `*_test.py` are caught, and so is deleting a pytest stage's lines outright.
- `tests/docs/test_stage_registry.py:24-31`, `staged_dirs`, scans the runner's raw text, comments included. I commented out `stage format` (two lines). `run.sh --only format` then says "unknown stage", yet the registry test passes (11 passed) and the quick run reports PASSED with no `tests/format` run. The tool check uses the anchored `stage_lines` (`:45-47`), so the two disagree inside one file.
- `:14-21`, `TOOL_CHECKS`, is a hand-kept list. It omits `tools/check_instruments.py` and `check_privacy.py --control`. Deleting the `privacy-controls` stage, deleting the `instruments` stage, or adding a new tool with its own `--check` and no stage all still pass (11 passed). HonestFramework §4 says "derive, don't re-list".
- Fix: take staged directories from `stage_lines`. Derive tools from `tools/*.py`, `controls/run.py` and `docs/studies/qro0/check_*.py`, requiring each tool and each `--check` or `--control` mode to appear in a stage line. Add a negative control for each.

**P0-4. Step 2 does not confine files to the crate, and its existence test is the host's.** The junction is accepted end to end; the other two pass steps 1 to 3 and only step 9 catches them.
- A directory junction `data/jct` pointing outside the crate, with `data/jct/secret.txt` listed and its digest right, gives `ACCEPTED`. The fixture's own generator also follows the link, so step 9 agrees. The check at `qro/checker.py:61-64` is textual: it refuses `..` and `.` parts, not links. Its own message says "its path inside the crate".
- An NTFS alternate data stream listed as a file passes steps 1 to 3 (`data/notes.txt:hidden`; `rglob` does not see it). A case-variant duplicate entity (`data/RAW.counts.json`) passes the same way. Both are refused only by `metadata-generated`.
- The same crate can get different verdicts on different hosts, which matters for federated custody. I believe POSIX `rglob` does not descend a symlinked directory, so an unlisted file could hide there. That is read from pathlib's behaviour, not run.
- Fix: refuse any listed or found path that is a link or reparse point, or whose `resolve()` leaves the crate (`graph-form`). Compare names exactly.

**P0-5. FORMAT.md:57-59 (item 11) is false.** It says a file `@id` in "printable ASCII with no space" means the crate holds "no file whose name would need percent-encoding".
- `qro/spelling.py:25` (`[!-~]+`) accepts `a%20b.txt`, `a#b.txt`, ``a`b``, `a^b`, `a{b}` and `a[b]` as files.
- RO-Crate tools write `my data.txt` as `my%20data.txt`. P0 looks for that literal name and refuses `file-missing`. Conversely, a file literally named `a%20b.txt` is accepted, so two implementations would disagree about which file an entity names.
- That `%` and `#` need encoding is RFC 3986 reasoning (BELIEVED), not read from the RO-Crate text.
- v0's 13,411 Quantum-Film file names all satisfy the rule, so no parcel is forced to undo it.
- Fix: restrict a File `@id` to `A-Za-z0-9-._~!$&amp;'()*+,;=:@/` (v0's three `=` names stay legal), or restate the item. Add tests.

**P0-6. `tools/check_privacy.py` does not read every file git would commit.** The claim is in its docstring at `:10`, CLAUDE.md:58-59 and `run.sh:322`. I checked in a `git init` copy:
- A UTF-16LE file (what Windows PowerShell 5.1's `&gt;` writes) holding `QISKIT_IBM_TOKEN=…` is MISSED. `read()` (`:66-73`) skips any file with a NUL in its first 4096 bytes. The file count drops from 207 to 206.
- A file named `café.md` is MISSED. `git ls-files` quotes the path as `"caf\303\251.md"`, the open fails, and `read()` returns None (`:57-63`).
- Neither is in the stated limits, which cover only "encoded" values.
- Fix: use `git ls-files -z`. Decode UTF-16 when there is a BOM. Report every unreadable or NUL file by name. State binaries as a limit.

**P0-7. CHECKED terms are checked only on the entity kinds a step visits.** Rule 1 and `KINDS["CHECKED"]` say the checker re-derives them.
- With the generator stubbed to the crate's own body, a fake `sha256` and `contentSize` on the root, on a Dataset, or on an absolute-IRI File is ACCEPTED. So is `qro:rawForm` on the root or on a plain File, and `qro:generator` on a File.
- Step 9 is the only backstop, and only against the producer's own generator.
- `qro:shots` already gets the right treatment: it is refused `count-unpaid` off raw results.
- This bites at P1: the study makes a bundle Dataset CHECKED and carrying `sha256`.
- Fix: per-term "applies to" in the table. Steps 2 and 3 should refuse these terms elsewhere (`graph-form`, or `step-unbuilt` until the owning step is built).

**P0-8. False statements and slips.** Each is small; restate or fix them.
- CLAUDE.md:9 says "~2 min" for quick. I measured 12 s, and 71 s for the full run. The figure was copied from moth's file.
- `run.sh:61`: `-h` prints `sed -n '2,26p'` of a header two lines longer than moth's, so it omits `--require-all`, `--list` and `--resume`.
- FORMAT.md:48 justifies all seven added refusal names as "the study names a step and 'the like'". Only `file-missing`, `file-unlisted` and `file-digest` fit "`raw-digest` and the like". Step 1's list is exactly three names, and step 9 and the seam have none.
- `qro/vocabulary.py:158` says "Terms the study fixes", but the table lacks `qro:role`, which section 9's table names twice.
- `qro/reader.py`'s docstring puts `graph-form` (2) before `context` (3). The code, in `_top`, checks the context between the key check and the graph check.
- `qro/fixture.py:4`: "nothing else" registers the fixture. `controls/run.py:20` also calls `register()`.
- The `test_every_row_names_an_owner_and_section_11s_words` docstring says it holds "section 11's words", but it only checks that text is non-empty.
- `tools/check_privacy.py` says it adds "Atlas's credential shapes". Nothing is Atlas-specific. Atlas's `Authorization: Bearer moth_…` is caught only by HonestHarness's generic bearer alternative.

## 4. Per item

**1. Section 13's list.** Delivered:
- the vocabulary table, with the context, vocabulary, refusal and control pages generated and `--check`ed;
- the canonical writer and strict reader;
- steps 1, 2, 3 and 9 and the custody check;
- the audit-record and custody-line formats, with `custody.record` and `custody.line` writers and a `custody` CLI that checks. Nothing writes a record from a check result; M1 stage 6 will.
- `run.sh`;
- `controls/` and its registry test;
- the floor.

The copied files, diffed against their sources:
- `verify/pytest-stage.sh`: only a two-line header added, as stated ("unchanged below this line").
- `verify/run.sh`: the stated changes are the header, quick budget, fingerprint, stages and the `nocommit` case. Unstated: `printf` column widths (cosmetic), the fingerprint dropping the host name and Atlas-key lines, and the `-h` regression (P0-8).
- `tools/check_docs.py`: stated "QRO-Crate's directories". Unstated: a new refusal when `docs/README.md` is missing, `.as_posix()` in messages, and the summary line. The new docstring sentence about the study holds, because `docs/*.md` is non-recursive.
- `tools/check_privacy.py` against HonestHarness's `check.py`: the privacy check and controls are kept, and the other four checks are dropped, as stated. Unstated: the `git log` return-code guard (needed with no commit), and the `sk-` and DEEPSEEK shapes dropped.
- `tests/docs/test_stage_registry.py` against moth's `test_registry.py`: only "tools' checks added" is stated. Unstated: two negative-control tests dropped (the `--ignore=` orphan control and the basename-clash control). I probed both pieces of code and they work, but nothing watches them now.
- `tools/gen_vocabulary.py` keeps the check_generated pattern: one definition, `--write`/`--check`, sanity first, a diff on drift, exit 1 for drift or a missing file, exit 2 for contradiction. It renders four files and compares bytes where the template compares text, which is right under `* -text`. It has no `--out`.

**2. Reader and writer.** About 150 byte-level and value-level plants.
- Refused with the right name:
  - whitespace, tabs, CRLF, a BOM, missing or doubled final LF, key order, `\/`, `\u0041`, UPPERCASE `\u00E9`, `\u000a` and raw UTF-8;
  - duplicate keys, NaN, Infinity, `1e400`, `8.0`, `8e0`, `08`, `-0`, true/false/null, 2^63, negatives;
  - single values in lists, unsorted or duplicated lists, one-element `@type` lists, refs with extra keys;
  - unknown keys, RO-Crate keys the table does not kind (`field-kind`), and unknown types;
  - graph order, duplicate `@id`s, a wrong descriptor or root, a bad `mentions`, and dangling refs.
- Accepted faults:
  - the Unicode-digit time (P0-1);
  - `text` takes control characters, NUL and a lone surrogate through canonical escapes. Those are one spelling each, but a second implementation cannot all represent `\ud800` (Notes).
- Crashes: P0-2.
- Canonical crates refused that a reasonable reading accepts:
  - a crate with Profile contextual entities: `Profile` is refused `term-unknown`, though section 3 says each declared profile has one;
  - RO-Crate's optional `ro-crate-preview.html`: refused `file-unlisted`;
  - the `%20` filename of P0-5.
- `canonical.write` cannot emit what the reader refuses, by construction. It returns only bytes that passed `reader.read`. It does raise non-Refused errors (NaN, TypeError, KeyError) and crashes wherever the reader does.

**3. Checker.**
- The step order is as section 10 states, in the code and in `test_the_steps_run_in_order`.
- Unbuilt steps: `qro:commitment` (step 4) and `qro:valuesDigest` (step 8) are refused `step-unbuilt` on any entity, with the absence word `unknown` too. Steps 5 to 7 have no CHECKED term, so nothing can trigger them.
- Files:
  - unlisted: a stray root file, a deep file, a hidden file and platform litter are all refused;
  - missing: `file-missing`;
  - wrong bytes: one byte changed, a wrong size, or a missing digest are refused `file-digest`/`raw-digest`;
  - but see P0-4 and P0-7.
- Step 3:
  - a count on a non-raw entity is refused `count-unpaid`;
  - a wrong count (±1) is refused;
  - an omitted count passes, since nothing is stated;
  - a moved shot with every digest resealed and the same total is accepted, which is the stated limit.
  - Wrong forms are refused only through the registered reader (crashes: P0-2). The fixture's reader accepts bitstrings of unequal lengths.
- Step 9:
  - I mutated every key of the twin by deleting it and by changing it. Only the six header terms were accepted.
  - Header terms can also sit on any entity except the descriptor.
  - A crate without `datePublished`, `qro:signature`, `qro:trustedTime` or the writer terms is accepted (Notes).
- `--fixtures`: without it, `python -m qro check` on the twin gives `REFUSED step-unbuilt … qro-fixture-counts` (exit 1). With it, `ACCEPTED 631257cd…`. It is the only CLI route. `controls/run.py:20` and the tests also call `register()` in process.

**4. Custody.** About 80 plants.
- The line format matches 9.2. Line-level plants are refused with the right names: unknown event, extra or missing field, uppercase digest, pretty-printed line, CRLF, no final LF, a 5000-digit integer.
- Chain: the first line's predecessor is the empty string's SHA-256. An edit, a drop, a reorder or a duplicate is refused `custody-chain` at the next line, and dropping line 1 is refused at line 1. A withdrawal in place is refused at the next line. A withdrawal appended is accepted, and so is a withdrawal in place of the last line, which is the stated tail limit.
- The record's head can name any line of the log and is held to it: a head of `none` pins nothing, an unrelated hash is `custody-head`, and a head edited or rewritten at or before it is refused.
- **Both stated limits are true as stated.** Editing or dropping the last line, and rewriting the tail, pass. Lines after the head pass.
- Unstated limits:
  - `at` is not required to be in order.
  - A withdrawal of a never-received crate, and a re-receipt after withdrawal, are accepted.
  - `from`, `reason` and `auditor` take any text, including an e-mail address.
  - A record's `crate` is not tied to the log.
  - Nothing detects a custodian showing two valid forks to different auditors; each is internally consistent.
  - FORMAT.md does not list the custody and audit format choices.
- The time-digit defect (P0-1) and the crashes (P0-2) apply here too.

**5. Controls.**
- `controls/registry.py` is a faithful copy: 30 of 30 rows identical in name, fault and expected cell. I parsed the study's table and compared string by string. The owners match section 13, which assigns P1 to `job-reattributed`, `shot-moved-resealed` and `qpy-only`, and P2 to `class-declared`. `unit-incomplete` and `not-interleaved` to P5, and `shared-control` and `simulator-in-real` to P3, are reasonable readings where section 13 is silent.
- Nothing in the tree holds that copy to the study; see Notes.
- All nine built controls come out as section 11 says, each by the planted reason with no collateral failure. Examples:
  - `shot-moved` is `raw-digest at data/raw.counts.json: the bytes are not the ones the metadata names`.
  - `adjusted-as-raw` is refused `raw-form` with the digest resealed.
  - `custody-chain` and `withdrawal-in-place` are refused at log line 2, `audit-head-mismatch` is `custody-head`, and `withdrawal-appended` is accepted.
- Planted in copies, the registry test fails by name on a dummy row, a dummy plant, a deleted row, a wrong expected name and a no-op plant. `controls.run` goes WRONG on the last two.
- Blind spots: moving a P0 row's owner to P1 passes `control-tests`, and only the generated page's drift flags it until `--write`. Changing a row's text passes everything the same way.
- All 21 pending rows are printed by name with owner and the study's text.

**6. Runner.**
- The full run is in section 2. The negative control fails for its stated reason (`REFUSED raw-digest at data/raw.counts.json`) and its twin passes (`ACCEPTED 631257cd…`).
- I planted a no-op and a wrong-reason control. The runner reports `NEGATIVE CONTROL DID NOT FAIL` and `the control failed, but not with "REFUSED raw-digest"`.
- Every test directory and every tool is in a stage today. The registry catches stray test files but not P0-3's cases.
- `nocommit` is safe:
  - `--resume`, with or without a run id, dies "refuses a dirty tree".
  - After a scratch commit, resuming the `nocommit` run dies with "different tree".
  - Moth's original refuses a no-commit repository with `git cannot read the repository`.
  - A HEAD pointing at a missing object still dies at `git status`.
  - A skipped `instruments` stage is printed by name, `--require-all` fails it, and a wrong checkout fails it.

**7. P0's choices (FORMAT items 1 to 12).** All are consistent with the plan except item 11 (P0-5); item 8's rationale is loose (P0-8). None forces a parcel to undo P0. Points to watch:
- **Item 1, inline prefix context.** Consistent. The profile version is in neither the context nor the profile IRI, and both are unversioned `blob/main` URLs, so the `context` refusal ("not this profile version's") cannot tell versions apart. Changing it is one constant.
- **Item 3, kinds per term and ANCHORED per instance.** Matches rule 1's "REPORTED until anchored". No term carries "holder named" yet.
- **Item 4, `term-unknown` against `field-kind`.** A sound reading of rule 9. `kind-missing` plants `keywords`, an RO-Crate term, so it watches the distinction.
- **Item 5, decimal rationals.** The study says "N/D in lowest terms", with no base. cft-fp256 writes hex, and its lowest-terms, sign and zero rules are kept. The same `N/D` text now means different values in the two formats, which touches "one format, one meaning". `rational`, `binary64` and `iri` have no term yet.
- **Item 9, `qro:shots` only on raw results.** Consistent with rule 7 and `job-reattributed`. `checker.counts()` has no hook, unlike `STEPS`, `RAW_FORMS` and `GENERATORS`, so a job- or PUB-level count rule means P1 edits P0's file.
- **Item 7, header as a table column.** Fine.
- **Item 12, the fixture.** Fine. `controls.run` also calls `register()` in process.
- **Item 10, `qro:generator`.** A bare name with no version, so a generator change alters a crate's body for the same records.

**8. Vocabulary and generated files.**
- `gen_vocabulary --check` refused all 24 drift plants (a trailing space, CRLF, a dropped byte, deleted, emptied, a hand edit, a definition edit with no `--write`, and the namespace and owner changed) with exit 1. `--write` heals it, and usage errors exit 2.
- `sanity()` caught 21 of 31 contradictions. It missed these:
  - an owner outside P0 to P5;
  - an unprefixed term unknown to RO-Crate (a test covers it);
  - a `qro:` type with a bad name;
  - a refusal named `Bad_Name` or placed at "step 12";
  - the custody-event word set drifting from `CUSTODY_LINE`;
  - a kind change on `prev`.
- Every name the code raises is a row. An AST scan finds 16 literal names: the 15 P0 rows plus the test's `no-such-refusal`. There are no dynamic names, and all P0 rows have raise sites.
- The pinned context matches the README:
  - It is 196,942 bytes, SHA-256 `5a3df1a4…21dd91`, with `license` CC0 1.0.
  - It is `@id` `https://w3id.org/ro/crate/1.3/context`, version 1.3.0, with 3,069 terms.
  - I streamed what w3id.org serves today (it redirects to researchobject.org) and got the same size and digest.

**9. Privacy gate.**
- It passes on the tree (206 files) and 9 of 9 controls are caught.
- The records hold none of the shapes below. My scan of the 146 files found no JWT, no CRN, no 32-hex account id, no e-mail and no `user_id` value. The only UUID-shaped value is one IBM metric id repeated 65 times, a service constant.
- Shapes it would miss: 29 of 48 shapes I constructed. By group:
  - IBM:
    - a `user_id` value (`IBMid-…` or `iam-ServiceId-…`), the study's own rule-3 example;
    - `account_id` or a bare `a/&lt;hex32&gt;`;
    - a bare 44-character key or a bare JWT;
    - a CRN with a JSON-escaped colon;
    - a bare 128-hex legacy token (BELIEVED).
  - Atlas:
    - a `moth_…` key outside Bearer/Authorization/api-key names, e.g. `QF_ATLAS_KEY=moth_…`;
    - presigned storage URLs (`X-Amz-Signature`, `X-Amz-Credential`, `Signature=`, `X-Goog-Signature`), which moth's own client calls bearer credentials that must not go into records unscrubbed;
    - AWS access-key ids.
  - Paths and addresses:
    - a URL-quoted home path or a `%2F` form;
    - `<a home path>` and `<a home path>…` or `<a home path>…`;
    - a home name that does not begin with an ASCII letter or digit (`<a home path>`);
    - `%USERPROFILE%`;
    - an e-mail with a JSON-escaped `@` or written "(at)".
- File-level, 6 of 15 missed: UTF-16 and NUL files, a gzip file, and a non-ASCII filename (P0-6).
- Commit author and committer identity is never scanned, only message bodies.
- Ablation: deleting any one name from `_NAMED` (including `api[_-]?key`, the IBM key's own name), the standalone bearer alternative, the drive-less `\Users\` alternative, or the Cygwin and Docker prefixes leaves all nine controls green. They watch the groups, not the alternatives.

**10. Documents.** All other claims hold: no dated claims were wrong, the ledger's 126, 137, 9 of 9, 21 pending, 16 of 16, 206 files, 5 of 5 and `631257cd…` reproduce, CRLF in exactly the 5 instrument outputs and 3 logs, and `quantum_film.ibm.account.connect` and `keyleak.refusals` exist. Problems:
- The false claims are CLAUDE.md:9, :17, :43 and :58-59 and FORMAT.md item 11 (P0-3, P0-1, P0-6, P0-5, P0-8).
- The ledger's `93880b5c…` cannot be reproduced from the current tree by removing the root's description; that gives `6b831632`. Other changes lie between the two runs, so the ledger's explanation that the description alone moved the digest is not confirmed.
- README's "steps 4 to 8 refuse `step-unbuilt`" holds only for crates carrying those steps' fields.

## 5. Notes

- No negative control exists in the tree for `gen_vocabulary --check`, for `check_instruments`, or for each privacy alternative, and HonestFramework §3 asks for unverified gates to be listed as such.
- Nothing gates the registry against section 11's text, the owners against section 13, or the hard-coded `30` against the study.
- The vocabulary's term and type rows are not walked both ways. Deleting `encodingFormat` or `qro:implementation` fails no test.
- The root's required header slots (`datePublished`, `qro:signature`, `qro:trustedTime`, and the writer terms) are not enforced by the reader, though section 9 and 9.2 put them on every root. The root's `license`, `name` and `description` are enforced only by the generator.
- `text` has no stated alphabet: C0 controls, DEL, NUL and lone surrogates are accepted.
- `float-spelt` plants an integer in a string slot, not a float. Other tests cover floats.
- Of the 21 pending rows, the five "states" rows and `joint-omission` cannot be expressed by `outcome()` or the `(expected, refusal)` comparison. P3 and P5 must extend `controls/run.py`, not undo it. `controls.run` prints any plant-less row as pending even when it is P0's, and only pytest catches that.
- The checker refuses RO-Crate's optional preview file and platform litter such as `.DS_Store`. That is strict, and unstated.
- Quantum-Film's 13,411 tracked file names all fit the `@id` rule.

## 6. What I did not do

- I ran only on Windows 11, so POSIX symlink and case behaviour are reasoned, not run.
- I did not run a JSON-LD processor on the crates, so the context's expansion is unshown.
- I did not re-verify the study's own claims or the instruments' logic. The runner reproduced the instrument outputs, and `check_study.py` and its plants returned ACCEPTED. I read the study's sections 5 and 9 to 13 closely and the rest more lightly.
- I did not run the three IBM tools or contact IBM or Atlas. I did not open `.atlas/` or any credential or account file, did not import qiskit, and wrote nothing in any repository.
- I did not attempt a scoped re-check; it is for after the fixes.
