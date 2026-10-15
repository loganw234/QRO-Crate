**1. Bottom line: NOT READY.**

There are eight defects. None needs a redesign. The three that matter most:

- **P0-1.** The `time` spelling accepts a second spelling of the same instant, through the whole checker.
- **P0-2.** Six kinds of input crash the reader, the custody check or the raw-form seam with a traceback. The exit status is 1, the same as a refusal. The contract says "refused by name".
- **P0-3.** The stage registry does not do what CLAUDE.md says it does.

What holds up:
- The vocabulary table and its four generated files.
- The byte-level canonical form. 121,852 mutants of the twin produced no second spelling and no crash.
- The custody chain and head. Both stated limits are true.
- The controls registry is a cell-for-cell copy of section 11's table.
- The nine built controls are each refused for the reason they plant.
- The runner passes 16 of 16, and the `nocommit` change is safe.

One finding is a note under your definitions, but it is below the bar "a gate, or a stated limit". My mutation test removed each of the 69 `if … raise Refused` checks in `reader`, `checker`, `custody` and `spelling`. For 34 of them all 137 tests stay green. For 30 of those the whole quick runner stays green; the other 4 are stopped only by ruff's unused-variable rule. Every one of these checks works today, because I planted each fault by hand. I would want plants for them before the re-check (N1).

**2. Setup**

- **Packet.**
  - `SHA256SUMS.txt` has 207 lines and all are OK.
  - The tree directory holds 208 files: the 206 hashed ones plus `qro/__pycache__/__init__` and `vocabulary` `.cpython-312.pyc`. They are not in the sums. They were written 5 s after the sums, and I dropped them from every copy.
  - A read-only hash compare shows the live tree equals the packet. HEAD is unborn and nothing is committed.
- **Host.** Windows 11, Git Bash, Python 3.12.9, pytest 9.1.1, ruff 0.11.9, git 2.45.2. I ran no Linux or macOS.
- **Rules.**
  - Everything was run in copies under `…\scratchpad\verifier-P0\check\`. My scripts are there: `harness.py`, `exp_*.py`, `fuzz_*.py`, `mutate*.py`, `plant_*.py`, `repro_p01.py`, `repro_p02.py`.
  - They are stdlib only and run under `python -I`.
  - I imported no qiskit and contacted neither IBM nor Atlas. I opened no credential, key or dot-directory.
- **Read-only sources.** I read them from git objects: moth-quantum 3a73823, HonestFramework 65447fd, HonestHarness b69ed76, and cft-fp256 at f22e8d2 (its checkout is now c918cb3). All were clean before and after. I set `GIT_OPTIONAL_LOCKS=0` for runs that reach moth-quantum, because the instruments call plain `git status` there.
- **One network read.** I streamed the RO-Crate context to `sha256sum` and saved nothing.
- **What I ran.**
  - The full runner and the quick runner. `pytest` over everything, which also passed under `-X dev -W error`.
  - About 450 hand plants.
  - A 121,852-mutant reader fuzz and a roughly 35,000-mutant custody and record fuzz.
  - A 69-site mutation test, plus 18 hand mutants of the canonical rules.
  - 24 drift variants for `gen_vocabulary`.
  - 31 `sanity()` probes.
  - 7 registry variants.
  - About 15 runner variants.
  - 48 credential and path shapes, and 15 file-level cases for the privacy gate.

**3. Defects**

**P0-1. `time` accepts non-ASCII digits, a second spelling.**
- **Where.** `qro/spelling.py:22`. `_TIME` uses `\d`, which matches every Unicode decimal digit in a `str` pattern, and `int()` then reads them. `:23` (`_DATE`) is safe only because CPython's `date.fromisoformat` happens to refuse them.
- **Plant.** Set `qro:writtenAt` to the Arabic-Indic digits of `2026-10-14T00:00:00Z`, written as `\u0662…`, so the bytes stay pure ASCII. `python -m qro check --fixtures` exits 0 with `ACCEPTED 631257cd…`, the twin's own digest, because the header is stripped.
- **Custody.** A log line whose `at` uses those digits passes `check_log`. Its head is `ead61c4b…`, against `817cd237…` for the ASCII spelling. Nothing regenerates a log, so nothing else would catch it.
- **Why it matters.** CLAUDE.md:42-43 says a second spelling of the same value is refused. For body terms (`startTime` and `endTime` will be P1's) the only backstop is whether P1's generator happens not to write the variant.
- **Fix.** Use `re.ASCII` or `[0-9]` in both patterns. Add Arabic-Indic and fullwidth digits to `test_spelling.py`. The `_DATE` regex has no test: `date.fromisoformat` accepts `20261014` and `2026-W42-3`, so the regex alone keeps `YYYY-MM-DD`.

**P0-2. Crash instead of a named refusal (exit 1, the same as a refusal).**

I reproduced each through `python -m qro` (`repro_p02.py`):
- An integer of 4,301 or more digits in the metadata gives `AttributeError: 'ValueError' object has no attribute 'lineno'` (`reader.py:78-79`).
- Deep nesting gives `RecursionError` (`reader.py:74`, `:81`; `custody.py:56`, `:90`; `fixture.py:27`).
- A `contentSize` or rational of 4,301 or more digits gives `ValueError` (`spelling.py:82`, `:91`).
- NaN or Infinity in a custody line, an audit record or the fixture's raw counts gives `ValueError` (`custody.py:59`, `:93`; `fixture.py:32`).
- A custody line whose `event` is a list or object gives `TypeError: unhashable` (`custody.py:61`).
- The seam, `checker.py:107-110`, catches only `RawFormError`. Any other exception from a parcel's raw-form reader escapes, which is how the two cases above reach the checker.

Fix:
- Catch `(ValueError, RecursionError)` around parse, compact and dumps in the reader, the custody line, the record and `read_counts`. Use `getattr(e, "lineno", …)`.
- Compare `len(value) &lt;= 19` before `int()`.
- Check `isinstance(event, str)` first.
- Turn any exception from a registered reader into `raw-form` in `checker.counts`.
- Add a sweep test that asserts `Refused` for all of these inputs.

**P0-3. The stage registry cannot fail as CLAUDE.md:17-18 says.**
- **Commented-out pytest stage.** `staged_dirs` (`tests/docs/test_stage_registry.py:24-31`) matches the raw text of `run.sh`, comments included. I commented out `stage format`. `--only format` then says "unknown stage", the format tests no longer run, and the registry test shows 11 passed. The tool checks use the anchored `stage_lines()` and do catch the same fault.
- **Hand-kept tool list.** `TOOL_CHECKS` (`:14-21`) is a hand-kept dict that omits `tools/check_instruments.py` and `check_privacy.py --control`. Deleting the `privacy-controls` stage, deleting the `instruments` stage, or adding a new `tools/check_new.py` with no stage all leave 11 passed. HonestFramework's rule is "derive, don't re-list".
- **What is caught.** A stray test directory and a stray `*_test.py` are caught.
- **Fix.** Take staged directories from `stage_lines()`. Derive the tool list from `tools/*.py`, `controls/run.py` and `docs/studies/qro0/check_*.py`. Require the `--check` and `--control` modes to appear in stage lines. The copy also dropped moth's negative controls for `--ignore=` handling and for `clashes()` (see Item 1).

**P0-4. Step 2 does not confine files to the crate. A file outside it is accepted end to end.**
- **Where.** `checker.py:61-75` tests presence with `is_file()` and containment with a textual `..` and `.` test. `:86` uses `rglob`.
- **(a) Junction.** `mklink /J crate\data\jct &lt;directory outside&gt;`, plus an entity `data/jct/secret.txt` with the right digest, gives `ACCEPTED`. The fixture generator follows the junction, so step 9 agrees.
- **(b) Alternate data stream.** An NTFS stream `data/notes.txt:hidden` listed as a file passes steps 1-3. It is refused only at step 9, and `rglob` cannot see it.
- **(c) Case alias.** A second entity `data/RAW.counts.json` for the existing `data/raw.counts.json` passes steps 1-3 and is refused only at step 9.
- **POSIX.** On POSIX, 3.12's `rglob` does not descend a symlinked directory, so an unlisted file behind one would be invisible. This is BELIEVED and I did not run it.
- **Fix.**
  - List the directory first with `lstat`.
  - Refuse anything that is not a regular file, and any link or reparse point.
  - Require each local entity id to be in that exact-case listing instead of calling `is_file()`.
  - Refuse `:` in a File id.

**P0-5. FORMAT.md item 11 (lines 57-59) is false as written.**
- **The claim.** "Printable ASCII with no space" does not give "no file whose name would need percent-encoding". `_ID = [!-~]+` (`spelling.py:25`) plus the backslash test (`checker.py:63`) accept `data/a%20b.txt`, `a#b.txt`, `a^b`, `` a`b ``, `a{b}` and `a[b].txt`. All were ACCEPTED end to end.
- **Interoperability.** RO-Crate tools write ids as URI references, so `my%20data.txt` for the file "my data.txt" is refused `file-missing`. A decoding reader and this checker would disagree on what `a%20b.txt` names.
- **Cost of fixing.** Quantum-Film's 13,411 tracked paths at 3a73823 all fit a stricter rule. Three contain `=`, and none contains a character that needs encoding.
- **Fix.** Restrict a File id to `[A-Za-z0-9._~!$&amp;'()*+,;=@/-]`, with no `%`, `#`, `?`, `:` or `\`. Then restate item 11.

**P0-6. The privacy gate does not read every file git would commit.**
- **The claim.** The docstring (`check_privacy.py:10`), CLAUDE.md:58-59 and the stage description at `run.sh:322` all say it does.
- **UTF-16.** A UTF-16LE file, which is what Windows PowerShell 5.1 `&gt;` writes, containing `QISKIT_IBM_…=&lt;44 chars&gt;` is MISSED. `read()` (`:66-73`) returns None on any NUL in the first 4 KB. The summary count does not move.
- **Non-ASCII names.** `café.md` is MISSED. `git ls-files` (`:59`) quotes it as `"caf\303\251.md"`, the open fails, and the file is skipped silently.
- **Stated limits.** NUL-first files, binaries and gzip are also skipped. The docstring's limit list does not state this class of skip.
- **Fix.** Use `git ls-files -z`. Decode UTF-16 when there is a BOM, otherwise fail closed with `unscanned: &lt;name&gt;`. Print the unscanned count.

**P0-7. CHECKED terms are checked only on the entity types a step visits.**
- **Where.** `checker.py:53-54`, `:57-90`, `:92-112`. VOCABULARY.md says a CHECKED term is re-derived by its step.
- **Plants.** I ran these with a stub generator that returns the crate's own body, as a parcel's generator could: `sha256="0"*64` plus `contentSize` on the root, on a Dataset directory entity and on an absolute-IRI File; `qro:rawForm` on the root or a plain File; `qro:generator` on a File. All were ACCEPTED.
- **Scope.** The fixture generator never emits these, so inside P0 only step 9 would matter. From P1 on, the property fails wherever a generator emits them. `qro:shots` already has the right rule: it is refused `count-unpaid` off raw results.
- **Fix.** Refuse these terms off the entities their step visits, or state the limit.

**P0-8. Wrong statements, each small.**
- CLAUDE.md:9 says quick is "~2 min". I measured 12 s for 13 stages; the full run is 71 s. The figure was copied from moth-quantum's CLAUDE.md.
- `run.sh:61` prints `sed -n '2,26p'`. The header grew two lines, so `-h` now omits `--require-all`, `--list` and `--resume`.
- FORMAT.md item 8 justifies the seven new names as "the study names a step and 'the like'". Only `file-missing`, `file-unlisted` and `file-digest` fit "`raw-digest` and the like". Step 1 lists exactly three names. Step 9 and the seam name nothing.
- `vocabulary.py:158` says "Terms the study fixes". The study's section 9 names `qro:role`, and it is not in the table.
- The `reader.py` docstring lists graph-form before context. The code checks context first.
- `fixture.py:4` says "nothing else does". `controls/run.py:20` also calls `register()`.
- The test `test_every_row_names_an_owner_and_section_11s_words` asserts only non-emptiness.
- README.md:21 and CLAUDE.md:35 say steps 4 to 8 refuse `step-unbuilt`. That is true only for a crate carrying a CHECKED term of that step. Steps 5, 6 and 7 have no such term.
- The `check_privacy.py` docstring says Atlas's shapes were added. No Atlas-specific alternative exists. `Authorization: Bearer moth_…` is caught by the generic bearer alternative that HonestHarness already had.
- VALIDATION.md says the digest moved from `93880b5c…` to `631257cd…` because the root gained a `description`. Removing it today gives `6b831632…`, and no subset of the root's body keys reproduces `93880b5c…`. Restate it as "that run's digest".

**4. Per item**

**Item 1. Section 13's list.**
- **Delivered.** The vocabulary table and its generated files, each with `--check`. The writer and reader. The custody and audit formats, writers and check. The runner. The controls and their registry. Steps 1-3 and 9. The custody check.
- **Not built.** Nothing in `python -m qro` writes an audit record from a verdict. That is M1 stage 6's work.
- **`run.sh` against moth 3a73823.**
  - The stated changes are all present: header, quick budget, fingerprint, stages and the `nocommit` case.
  - Unstated: `printf` widths and the `--list` layout changed. `platform.node()` was dropped from the fingerprint. The `-h` regression is in P0-8.
  - Moth's original runner refuses a repository with no commit ("git cannot read the repository"). I confirmed that.
- **`pytest-stage.sh`.** The only change is two header lines. "Unchanged below this line" is true.
- **`check_docs.py`.** The stated change is the directories. Unstated: an "index is missing" refusal, `.as_posix()` in a message, a new summary line, and a changed `FOREIGN` list. The new docstring's claim that the study under `docs/studies/` is unchecked is true by construction.
- **`check_privacy.py` against HonestHarness.**
  - Unstated: the `git log` call is guarded by `returncode == 0` (needed for a repository with no commit), `.as_posix()` was added, and the `sk-` and DEEPSEEK shapes were dropped.
  - Nine controls were adapted.
  - Result: 206 files, nothing found, 9 of 9 controls caught.
- **`test_stage_registry.py` against moth's `test_registry.py`.** The stated change is that the tools' checks were added. Unstated: two tests were removed, the `--ignore=` orphan control and the basename-clash control. The code they watched is retained. I probed both and they work, but now nothing watches them.
- **`gen_vocabulary.py` against `check_generated.py`.**
  - Same shape: `--write`/`--check` exclusive, sanity first, a diff on drift, exit 0/1/2.
  - Different: four outputs, a byte compare (stricter, and right under `* -text`), no `--out`, and sanity also covers the controls.
  - It refuses all 24 drift variants I planted, and `--write` heals them. No in-tree control watches it (N1).

**Item 2. Reader and writer.**
- **Refused as they should be.**
  - Byte level: whitespace, tabs, CRLF, BOM, final-LF variants, key order, `\/`, `\u0041`, uppercase hex, `\u000a`, raw UTF-8, duplicate keys, NaN, Infinity, `1e400`, `8.0`, `8e0`, `08`, `-0`, `-8`, `true`, `false`, `null` and 2^63.
  - Value level: one-element, unsorted and duplicate lists; a list for a single-valued term; a ref with extra keys; unknown keys, RO-Crate keys without a kind, and unknown types; graph order and duplicate `@id`s; the shape of the descriptor and root, `mentions`, and dangling refs.
  - Fuzz: 0 of 6,973 accepted mutants equal the original document, and 0 crashed.
- **Accepted faults.**
  - Non-ASCII digits in `time` (P0-1).
  - Percent-encodable ids (P0-5).
  - Files outside the crate (P0-4) and off-type CHECKED fields (P0-7).
  - `text` takes `\n`, `\u0000`, DEL and a lone surrogate `\ud800` as canonical escapes. The spelling says only "not empty, no edge space". An independent implementation cannot round-trip `\ud800`.
  - A root without `datePublished`, `qro:signature` or `qro:trustedTime` is ACCEPTED, because the header is stripped before step 9. The plan puts the slots on every root (section 9.2), and RO-Crate requires `datePublished`.
- **Refused though canonical and plausible.** Contextual `Profile` entities are `term-unknown`, although study section 3 says each declared profile has one. RO-Crate's optional `ro-crate-preview.html` is `file-unlisted`. RO-Crate-style `my%20data.txt` is `file-missing`.
- **`canonical.write`.** It cannot emit what the reader refuses, because it returns bytes only after `reader.read` accepted them (`canonical.py:82-84`). It checks step 1 only. It can fail with a non-`Refused` exception, for example NaN.

**Item 3. Checker.**
- **Step order.** The order is reader, files, counts, seam 4 to 8, then regeneration, as in section 10. `test_the_steps_run_in_order` agrees.
- **CHECKED field while its step is unbuilt.** No. Any term of step 4 or 8, even with the value `unknown` and on any entity, gives `step-unbuilt`. See P0-7 for the off-type case.
- **Files.**
  - Refused: an entity with no file, a stray file (deep, hidden, backup), an entity not reachable from the root, wrong bytes, wrong size, missing digest or size, and `..`, `.`, `//`, `/x` or `\` in an id.
  - Accepted: the junction, the alternate data stream and the case alias (P0-4).
- **Counts.**
  - Refused: a count on a non-raw entity, and a wrong count.
  - Accepted by design: an omitted count (nothing is stated), and `shot-moved-resealed` (the stated limit).
  - A reader that raises anything but `RawFormError` crashes (P0-2).
- **Step 9.** I mutated every key of every entity (36 mutations). Only header terms were accepted. Header terms are legal on any entity except the descriptor, and none is required.
- **`--fixtures`.**
  - Via the CLI it is the only route. Without it the fixture gives `step-unbuilt` at `qro:rawForm`, with exit 1.
  - `controls/run.py:20` also registers the fixture in-process, and the tests do too.

**Item 4. Custody.**
- **Formats.** Line and record fields match section 9.2: `received`, `withdrawn`, `prev`, `logHead`, the independence words and the stage words. An empty log gives head `none`.
- **Chain.**
  - Edits to lines 1 or 2: 0 of 17,520 mutants accepted.
  - Dropped line 1 or line 2: refused `custody-chain`.
  - Swapped lines: refused `custody-chain`.
  - First line's predecessor: `sha256("")`; anything else is refused.
  - A withdrawal in place: refused at the next line. A withdrawal appended: accepted.
  - `custody-head`: refused for an unrelated hash, and for `sha256("")` as a head.
- **Stated limits.** Both are true.
  - The last line, or a rewritten tail, passes the log alone. 475 last-line mutants were accepted.
  - A record pinning the old head caught all 369 distinct accepted last-line edits.
  - Lines after the head stay uncovered.
- **Unstated limits.**
  - `at` is unordered; a decreasing or future time is accepted.
  - A `withdrawn` for a crate never received is accepted, and so is a crate received again after it was withdrawn.
  - `from`, `reason` and `auditor` accept any text, including an e-mail address.
  - A record's `crate` is tied to nothing.
  - A record's head may name any earlier line.
  - A custodian can show different valid logs to different auditors (equivocation), though "no shared ledger" covers this.

**Item 5. Controls.**
- **Registry.** All 30 rows equal section 11's table by string, cell for cell. Owners fit section 13.
- **Nine built controls.** Each is refused by the expected name at the planted location.
  - `shot-moved` is `raw-digest`; `count-unpaid` is `count-unpaid`, "states 9; the bytes hold 8".
  - `float-spelt` is `spelling` at `contentSize`, "not a string"; `kind-missing` is `field-kind` at `keywords`.
  - `adjusted-as-raw` is `raw-form` at "count of 00".
  - `custody-chain` and `withdrawal-in-place` are `custody-chain` at line 2.
  - `withdrawal-appended` is accepted; `audit-head-mismatch` is `custody-head`.
  - `float-spelt` plants an integer in a string slot, not a float. Other tests cover floats.
- **Two-way test.**
  - It fails, and names the culprit, for a dummy row, a dummy plant, a dropped row, a wrong expected name and a no-op plant.
  - It cannot see an owner change from P0 to P1 (it passes, and `CONTROLS.md` drifts until `--write`).
  - It cannot see a change to a row's text.
  - `test_the_registry_check_can_fail` proves only the helper functions, with dummy arguments.
- **Pending.** All 21 pending rows are printed by name, with owner and the study's text.
- **Harness gap.** `outcome()` returns only accepted or refused, and `controls/run.py:57-58` compares `(got, name)` with `(c.expected, c.refusal)`. The 5 `states` rows and `joint-omission` cannot pass until P3 and P5 extend it.

**Item 6. Runner.**
- **Full run.**
  - Command: `QRO_MOTH_ROOT=…moth-quantum bash verify/run.sh`, in a copy with `git init`.
  - Run id `20261014-195030-40-nocommit+dirty`: 16 of 16 passed, none skipped, 71 s.
  - Tests: 137 passed (126 in the four stages, 11 in docs).
  - The instruments reproduced 5 of 5.
  - Study gates: `study` and `study-plants` both ACCEPTED.
- **Quick budget.** 13 of 13 in 12 s, on a committed copy.
- **Negative control.**
  - Log: `REFUSED raw-digest at data/raw.counts.json: the bytes are not the ones the metadata names`.
  - Twin: `ACCEPTED 631257cd…`.
  - A no-op plant gives "NEGATIVE CONTROL DID NOT FAIL".
  - A wrong-reason plant gives "failed, but not with REFUSED raw-digest".
- **Skips.**
  - `instruments` skips by name without `QRO_MOTH_ROOT`; `--require-all` makes it fail.
  - A wrong checkout fails the stage.
- **Other option behaviour.** `--only ""` is refused with exit 2. The runner works from a path containing a space.
- **`nocommit` is safe.**
  - `--resume` is refused (always dirty). A nocommit run id cannot match a committed tree: "was a different tree than 220cc8a".
  - A HEAD pointing at a missing object goes through the first branch and dies at `git status`.
- **Stage and tool coverage.** Every test file and tool check sits in a stage today. The registry catches the ways it can be broken only in part (P0-3).

**Item 7. P0's choices.**
- **1. Inline context.** Consistent. The profile version appears neither in the context nor in the profile IRI, so `context` ("this profile version's") cannot tell versions apart.
- **2. Namespace.** Consistent with question 6.
- **3. Kinds per term, with ANCHORED derived per instance.** Consistent with rule 1 and CERT-V2 §5. The derivation has no gate until P1's anchor stage.
- **4. `term-unknown` against `field-kind`.** Consistent with the pinned context.
- **5. Decimal rationals.** The study says only "N/D in lowest terms". cft-fp256 writes hex, so `12/25` means different values in the two formats.
- **6. No `true`, `false` or `null`.** Consistent with rule 2.
- **7. Header as a column.** Consistent with rule 4.
- **8. Seven refusal names.** Additive. The rationale needs restating (P0-8).
- **9. `qro:shots` on raw results.** Consistent with rule 7.
  - `checker.counts` has no hook for a parcel's count rule, so P1 must edit P0's file.
  - There is one integer per raw entity, so a job file with three PUBs has only a total.
- **10. Root names its generator.** Consistent with rule 5. The name carries no version.
- **11. File ids.** P0-5.
- **12. Fixture.** Consistent.
- **Undo.** No choice forces a parcel to undo P0. P1, P3, P4 and P5 will need edits to `checker.counts`, `controls/run.py` and `V.PROFILE`.

**Item 8. Vocabulary.**
- **Drift.** All 24 variants refused with exit 1 (a trailing space, CRLF, a dropped byte, deletion, emptying, a hand edit, and definition edits without `--write`).
- **`sanity()`.** It catches 21 of 31 contradictions. It misses:
  - owners and refusal `where`;
  - the form of type and refusal names;
  - `ANCHORED` without an absence word;
  - custody events against the word set;
  - a changed `prev` kind;
  - an unprefixed term outside RO-Crate's context (a test catches that one).
- **Raised names.** An AST scan finds 15 P0 names, all rows with raise sites. The one other literal is the test's deliberate `no-such-refusal`.
- **Pinned context.**
  - The pinned file is 196,942 bytes, SHA-256 `5a3df1a43185501db4d45cdde5a478c57eeb1d673eedfe400488fc4c4b21dd91`, with `license` @id CC0 1.0 and 3,069 terms.
  - w3id.org redirects to researchobject.org and serves the same bytes today.

**Item 9. Privacy gate.**
- **Result.** 206 files, nothing found. 9 of 9 controls caught.
- **Controls do not watch each alternative.** Deleting any one of these leaves all nine controls green: any single name in the named-variable list (including `api[_-]?key`, `token` and `x-api-key`), the standalone bearer, the drive-less `\Users\` form, or the Cygwin and Docker prefixes.
- **Records.** None of the shapes below occurs in the 146 files under `records/`. The only UUID is one IBM metric id repeated 65 times.
- **Missed shapes.** 29 of 48 shapes were missed; 19 caught. Most fall inside the stated limits ("a shape not listed", "encoded passes"). The misses that matter:
  - Atlas: the key `moth_…` outside Bearer or a named variable, and presigned URLs (`X-Amz-Signature`, `X-Amz-Credential`, `Signature=`). Moth's client says presigned URLs are bearer credentials.
  - IBM: `user_id: IBMid-…` or `iam-ServiceId-…` (the study's own rule-3 example), a bare account id, a bare JWT, a bare 44-character key, and a CRN with JSON-escaped colons.
  - Paths: URL-quoted `C%3A%5CUsers…`, `\home\…`, `<a home path>…`, and non-ASCII home names. A `%USERPROFILE%` form also passes.
  - Addresses: JSON-escaped `@` and `(at)`.
- **Outside the stated limits.** UTF-16 and non-ASCII-named files (P0-6).
- **Other.** `PLACEHOLDER` is dead code. Commit author and committer identity are not scanned.

**Item 10. Documents.**
- **False or imprecise.** Everything is under P0-1 to P0-8.
- **MEASURED figures reproduced.** All ledger figures reproduced except the digest attribution (P0-8). They are:
  - 126 passed, and 137 in total;
  - stage counts 11, 6, 96, 12 and 12;
  - 9 of 9 controls and 21 pending;
  - 16 of 16 stages;
  - 206 files and 9 of 9 caught;
  - 5 of 5 instruments;
  - twin digest `631257cd…`.
- **CRLF files.** CLAUDE.md's CRLF claim is exact: 5 instrument outputs and 3 records logs, everything else LF.
- **moth-quantum names.** The moth-quantum names it cites exist.

**5. Notes**

- **N1. Gates not watched.**
  - **Mutation test.** 34 of 69 check sites survive the suite: reader 19 of 26, checker 9 of 17, custody 3 of 9, spelling 3 of 17. 30 survive the whole quick runner; 4 are stopped only by ruff's unused-variable rule.
  - **Surviving sites.**
    - The reader: top-level shape, graph shape, descriptor, root `conformsTo`, `mentions`, dangling refs, the list rules.
    - The checker: the path-shape guard at `checker.py:63`, missing digest or size, unreachable entity, and shots on a non-raw entity.
    - The custody canonical-line and record checks.
    - The spelling `date` pattern and `id_problem`.
    - One site is dead code: `checker.py:65`.
  - **Plants already written.** `exp_values.py`, `exp_files.py` and `exp_custody.py` hold the plants, each refused today.
  - **Canonical rules.** 6 of 18 hand mutants survive the suite, the twin and `--check`: unsorted keys, `ensure_ascii=False`, indent 4, `", "` separators, `allow_nan=True`, and a reversed digest. Writer and reader move together, and no golden vector exists for the twin, a custody line, a head or a record.
  - **Unwatched gates.** Nothing in the tree plants drift for `gen_vocabulary --check`, and nothing tests `check_instruments.py` or the WRONG branch of `controls.run`. HonestFramework §3 says to list such a gate as unverified, in writing.
- **N2. Registry.** Faithful today. Only the count 30 is checked; owners and text are not.
- **N3. Parcel friction.** P1 must edit `counts()`. P3 and P5 must extend `controls/run.py`. `Profile` and other PRC terms (`instrument`, `object`, `result`, `agent`) are not in the table, so any CreateAction fails `field-kind`.
- **N4. Custody and audit format choices** are not listed among FORMAT.md's choices: compact JSON lines, `prev` hashing the LF, `logHead` matching any line, and the indented-JSON record.
- **N5. Static scan.** `raised_names` in the vocabulary test is a line-based scan. A reformatted call would hide a name from it.
- **N6. Term and type rows.** They are not walked both ways. Deleting `encodingFormat` or `qro:implementation` fails no test.
- **N7. Spelling and rules.** A spelling's prose (`SPELLINGS`) and its rule (`spelling.py`) are two statements of one fact. The examples are the only tie, and P0-1 slipped between them.
- **N8. Host dependence of step 2.** Case aliases and alternate data streams are refused at step 9 only.

**6. What I did not do**

- I ran nothing on Linux or macOS.
- I did not run the IBM tools, import qiskit, or contact IBM or Atlas.
- I did not run a JSON-LD processor or rocrate-validator.
- P0-5 rests on RFC 3986 reasoning, which is BELIEVED, not on a reading of RO-Crate 1.3.
- I did not verify the study's own figures. I only ran its two gates and the five instruments through the runner.
- I did not review P1 to P5, which do not exist yet.
- The mutation test covered check removals and 18 canonical mutants, not every operator.
- I did not measure performance on a 13,000-file crate.
- **Slip.** My first directory listing and my read of `records/2026-10-14/README.md` printed that tree's job identifiers into my own tool output. None appears here, and every later scan masked or hashed them.
- The harness changed my primary working directory to `…\QRO-Crate\records` mid-way. I wrote nothing there.

A scoped re-check after the fixes should cover P0-1 to P0-8 and the N1 plants. I will pick my own faults.
