# P0 verifier, round 2: scoped re-check

The harness refused a file write from this agent, so `SCRATCH\verifier-P0-r2\report.md` does not exist. The report is this message. My scripts and logs are in `SCRATCH\verifier-P0-r2\check\`.

**1. Verdict: NOT READY.**

There are nine defects. None needs a redesign. Four change what a gate does or what a user sees. Five are sentences in the tree that are not true. By ParcelRound's rule, R2-2 and R2-3 are wrong answers, R2-1 and R2-4 are gates that do not hold, and R2-5 to R2-9 are sentences to restate.

- **R2-1.** The P0-5 fix is right in the code and held by no test. With the reader's path check removed, all 295 tests, the twin, the controls and the vocabulary check stay green, and `data/a%20b.txt` and its kind are accepted end to end. The ledger's "each fix is held by a test" is false for P0-5.
- **R2-2.** The command line still crashes with exit 1 on hostile input. A refusal that echoes a lone surrogate, or on a piped Windows stdout any non-cp1252 character, makes `print` raise inside the handler. That is P0-2's defect in a new spelling.
- **R2-3.** `reader.admits` lets an entity whose `@id` equals a domain token (`qro:RawResult`, `local-file`, `Dataset`) carry CHECKED terms that no step reads. FORMAT.md item 13 says none can.
- **R2-4.** The `format` stage cannot pass off Windows. One test skips there, and the runner fails a stage on any skip.
- **R2-5 to R2-9.**
  - `text` accepts C1 control characters its prose forbids.
  - FORMAT.md says "Seven refusal names" over a list of eight.
  - VALIDATION.md says FORMAT.md states a limit it does not.
  - The QRO-0 review README says "the only change" and is wrong.
  - Two "copied" docstrings say less than changed.

What holds up, against my own plants:
- The freeze, the runner (17 of 17 twice), and the commit: 234 of 234 files come back byte for byte from commit and clone under `core.autocrlf=true`.
- P0-1, P0-3, P0-4, P0-6 and most of P0-7.
- N1's new plants and golden bytes. Of round 1's 18 canonical mutants plus the vocabulary pin, 18 of 19 are killed and the one survivor is equivalent.
- The 14 review copies equal their originals apart from redactions.
- Every change to the study is one section 17 records.
- NOTICE.md matches the terms report.

## 2. Setup

- **Freeze.** MEASURED: `cd frozen/tree && sha256sum -c ../SHA256SUMS.txt` gives 234 OK. The file sets are equal and there is no `.pyc`. I re-ran it at the end: still 234 OK.
- **Live tree.** MEASURED (`check\live_vs_frozen.py`, read-only): the live repository's would-be-committed files are the same 234, byte for byte.
- **Host.** Windows 11, Git Bash, Python 3.12.9, pytest 9.1.1, ruff 0.11.9, git 2.45.2.
- **Copies.** I ran everything in copies, with `PYTHONDONTWRITEBYTECODE=1`. My scripts are stdlib only, and none contains a real key.
- **Runner.** MEASURED: `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` in a `git init` copy, run `20261014-210358-13716-nocommit+dirty`: passed 17, failed 0, skipped 0.
  - A second copy passed 17 of 17 in 63 s. `--budget quick` passed 14 of 14 in 15 s.
  - The stage counts equal VALIDATION.md's: docs 16, tool-tests 38, vocab-tests 7, format 207, custody 12, control-tests 15, controls-run 9 of 9 with 21 pending, study-plants 68 and 6, privacy 234 files with none binary, privacy-controls 32 of 32, instruments 5 of 5, twin `ff3fe486…`, check-docs 10 documents.
- **Strict warnings.** MEASURED: `python -X dev -W error -m pytest -q tests` gives 295 passed. `ruff check qro controls tools tests` is clean.
- **Commit trial.** MEASURED (`check\clone_trial.sh`): I committed the 234 files in a scratch repository with `core.autocrlf=true` and cloned it with the same setting. 234 of 234 files are identical. With `.gitattributes` removed, 225 of 233 differ. The privacy gate on that committed copy reads 234 files and 1 commit message and finds nothing. The quick runner there passes 14 of 14.
- **A packet note.** The "sources" given for the study's twelve (`reviews\QRO-0-reviews\`) are the lead's already-redacted staging. I took the true originals from the paths in the lead's `reviews\stage_reviews.py`, and used those in section 4.4.

## 3. Defects

### R2-1. P0-5's path rules, and N8's stream rule, are held by no test

- **Where.** `qro/reader.py:146-149` (the check), `qro/spelling.py:149-160` (`path_problem`), `tests/format/test_hostile.py:129-138` (the test meant to hold it).
- **READ.** The test appends its entity at the end of an unsorted graph and accepts either `spelling` or `graph-form` (line 138). The reader's order refusal therefore satisfies it. No test calls `path_problem`.
- **MEASURED** (`check\mut_r2.py`, mutating `if local_file(e):` at `reader.py:146` to `if False:`): all 295 tests pass. `python -m controls.plant twin`, `python -m controls.run` and `tools/gen_vocabulary.py --check` also pass.
- **MEASURED** (`check\exp_p05.py` on that mutant): a real file named `data/a%20b.txt`, `a#b.txt`, ``a`b.txt``, `a^b.txt`, `a{b}.txt`, `a[b].txt` or `CON.txt`, listed with its true digest, is ACCEPTED by `checker.check`. The original refuses each as `spelling`.
- **MEASURED** (`check\exp_vacuous.py`): on the mutant, the test's nine names get `graph-form`, which the test accepts. With the graph sorted, as a careful plant would leave it, they get `file-missing`.
- **Also surviving** (MEASURED, `check\mut_r2.py` and `check\mut_canon_r2.py`):
  - the `if p:` at `reader.py:148`, and the name `spelling` at `:149` swapped to `graph-form`;
  - the three branches inside `path_problem` (`spelling.py:154`, `:156`, `:158`);
  - the path alphabet losing `=`, `@` or `~`, or gaining `%`, `:` or `#`;
  - the device list losing `aux`, `com` or `lpt`, or matching case-sensitively, or matching without an extension;
  - `absolute()` made true for a colon anywhere, which removes N8's rule that a listed `data/notes.txt:hidden` is refused.
- The original refuses or accepts each of these inputs correctly (MEASURED, `check\exp_gaps_real.py`). Each survivor is a missing test, not an equivalent change.
- **Why it matters.** The code is right today. The gate is not there: the next edit to the alphabet moves nothing. VALIDATION.md:98-99, "each fix is held by a test", is false for P0-5 and for N8's stream rule.
- **Fix.** Sort the graph in the plant and assert `spelling`. Add accepted examples for the allowed sub-delimiters. Add refused ones for each device name, a dot segment and a colon in a later segment.

### R2-2. The command line crashes with exit 1 when a refusal echoes text it cannot print

- **Where.** `qro/__main__.py:20-22`. `except Refused as r: print(...)` runs inside the `try`, so the `except Exception` that returns 3 does not cover it. The refusal's `where` and `detail` carry the crate's own text: a key (`reader.py:196-198`), a type (`:201`), a generator name or raw form (`checker.py:117`, `:137`).
- **MEASURED** (`check\exp_print.py`; stdout piped; each plant is a fixture crate with one change):
  - In the default environment, six of seven plants exit 1 with a traceback and no verdict. The plants are a root key written as the escape for U+D800, a File type of U+D800, and a key, a type, a generator name or a raw form of one CJK character. The error is `UnicodeEncodeError` from the cp1252 codec.
  - With `PYTHONIOENCODING=utf-8`, which `verify/run.sh` exports, the two lone-surrogate plants still crash (`'utf-8' codec can't encode … surrogates not allowed`), rc 1.
  - A latin-1 character (`café`) prints correctly.
- **Why it matters.** A crash exits 1, the code of a refusal, with no name. P0-2's repair ("refused by name; exit 3 when the checker itself fails"), `qro/__main__.py`'s docstring and CLAUDE.md's "A crash is never a verdict" do not hold for this input. The crate is not accepted, so this is not a wrong accept.
- **Fix.** Print the echoed text through `ascii()` or `backslashreplace`, or send a failure in the handler to the exit-3 path.

### R2-3. `admits` conflates an id with a type, so a CHECKED term can sit where no step reads it

- **Where.** `qro/reader.py:67-72`. For every domain token it tests `s == entity["@id"]`, though only `./` and the descriptor's name are ids.
- **MEASURED** (`check\exp_p07.py`, part 1): 230 (term, entity) pairs through the reader, with every vocabulary term on nine kinds of entity. None is accepted off its declared domain. The matrix holds.
- **MEASURED** (part 2, with a generator that returns the crate's own body, as round 1's P0-7 plants did). `checker.check` ACCEPTS all four of these:
  - `{"@id": "local-file", "@type": "CreativeWork", "sha256": …, "contentSize": "1"}`;
  - `{"@id": "qro:RawResult", "@type": "CreativeWork", "qro:shots": 9}`;
  - the same with `qro:rawForm`;
  - `{"@id": "Dataset", "@type": "CreativeWork", "hasPart": […]}`.
- **Why it matters.** The `qro:shots` entity is rule 7 broken: a stated count with no raw bytes under it. FORMAT.md item 13, "no CHECKED field sits where no step reads it", is false for these ids.
- **How far it reaches.** It needs a generator that emits such an entity, which a generator regenerating from records does not. That is the same dependence round 1's P0-7 had.
- **Fix.** Keep the id tokens (`./`, the descriptor) apart from type tokens in a term's domain.

### R2-4. The `format` stage cannot pass on a host that is not Windows

- **READ.** `tests/format/test_hostile.py:159` is `skipif(os.name != "nt")`. `verify/pytest-stage.sh` fails a stage whose pytest summary names a skip. CLAUDE.md says the same: "A skip happens only at stage level, by name."
- **MEASURED** (forcing that skip in a copy): `bash verify/pytest-stage.sh tests/format` prints `206 passed, 1 skipped` and `pytest-stage: the summary names a test this stage did not hold to a verdict`, and exits 1.
- **BELIEVED.** On Linux and macOS, `format` and so `bash verify/run.sh` fail on the first commit. I did not run it there (section 6).
- **Fix.** Plant the symlink in the same test on POSIX in place of the skip.

### R2-5. The `text` spelling accepts C1 control characters

- **READ.** `qro/vocabulary.py:63-64` and the generated `docs/VOCABULARY.md` say "no control character but the line feed". FORMAT.md item 15 says it too. `qro/spelling.py:33` excludes `\x00-\x09`, `\x0b-\x1f`, `\x7f` and surrogates only.
- **MEASURED** (`check\exp_spell.py`, `unicodedata.category`): U+0080 to U+009F are category Cc, and `text` accepts `a\x85b`, `a\x9fb` and `a\x80b`. It also accepts U+2028, U+2029 and U+FEFF inside.
- **MEASURED.** Removing `\x0b-\x1f` from the class, which includes CR, leaves every test green. The new examples cover NUL, tab, DEL and a surrogate.
- **Why it matters.** This is N7's pair of statements (prose and rule) coming apart in a class the examples do not reach.
- **Fix.** Add U+0080 to U+009F to the class, or say "ASCII control".

### R2-6. FORMAT.md item 8 says seven names and lists eight

- **READ.** `docs/FORMAT.md:50`, "Seven refusal names are P0's own". Its list holds `file-missing`, `file-unlisted`, `file-digest`, `file-link`, `context`, `graph-form`, `metadata-generated` and `step-unbuilt`.
- **MEASURED** (`qro.vocabulary.REFUSALS`): 16 refusals are P0's. Eight are named by the study: `spelling`, `field-kind`, `term-unknown`, `raw-digest`, `raw-form`, `count-unpaid`, `custody-chain` and `custody-head`. The other eight are the list above.
- **Origin.** The count went from seven to eight when P0-4's fix added `file-link`. The sentence P0-8 corrected kept the old number.

### R2-7. VALIDATION.md says FORMAT.md states a limit that it does not

- **READ.** `docs/VALIDATION.md:206-209`: "Not taken, as stated limits in docs/FORMAT.md: … the Process Run Crate terms (`instrument`, `object`, `result`, `agent`)".
- **READ.** FORMAT.md's "Stated limits" (lines 116-126) hold three: `ro-crate-preview.html`, the profile's version, and the `Profile` type. A search of FORMAT.md finds none of the four terms.
- **Why it matters.** Round 1's N3 point stands, unstated: with those terms missing from the table, any CreateAction crate is refused `field-kind`.

### R2-8. The review READMEs overstate what was left alone

- **READ.** `docs/reviews/QRO-0/README.md` says "The only change: a home path is redacted".
- **MEASURED** (`check\diff_reviews2.py`, against the 14 true originals): all 14 copies equal their originals apart from the redactions and two other changes. Both changes hit 7 of the 12 QRO-0 files (draft02, 03, 05, 06, 07, 08 and 09).
  - Each lost a `<task-notification>` envelope (task id, output file, status, summary, note, usage).
  - Each had CRLF turned to LF (131 to 395 CRLF lines each).
  - Neither change is stated in the tree.
  - The P0 README does not say "only", but says "as its verifier returned it".
- **BELIEVED.** Every report holds `&lt;`, `&gt;` and `&amp;` where its verifier wrote `<`, `>` and `&`. MEASURED: none of the 14 originals holds a raw `<` or `>` at all, so the notification transport escaped them. A code span in a copy reads `len(value) &lt;= 19`.
- **Held.** All 14 SHA-256 prefixes in the two READMEs match the originals. All home-path counts match: seven QRO-0 files with 1, five with 0; P0 with 0 and 0, plus 4 and 1 strings redacted as `<a home path>`.

### R2-9. Two "copied" docstrings say less than changed

- **READ and MEASURED** (diff against `3a73823:verify/run.sh`, and against moth-quantum's `tools/check_docs.py`):
  - `verify/run.sh:4-7`: "Its framework is kept line for line". Besides the stated header, budget, fingerprint, stages and `nocommit` case, the `-h` handler changed. Seven `printf '%-10s'` widths in the stage notes became `%-17s`, and the `--list` format changed.
  - `tools/check_docs.py`: "with QRO-Crate's directories". It also adds an `index is missing` refusal, `.as_posix()` in a message, a new summary line, and a longer FOREIGN list.
- **Origin.** Round 1's Item 1 named these as unstated. The ledger does not take them.

## 4. Per scope item

### 4.1 P0-1 to P0-8, with my own plants

| item | verdict | evidence |
|---|---|---|
| P0-1, non-ASCII digits | holds | MEASURED (`check\fuzz_lookalike.py`): 14,768 look-alike mutants of spelled values (9,157 in the twin's metadata, 5,611 in a custody line). Each swaps one character for a Unicode digit or NFKC look-alike. 0 accepted, 0 crashed. Direct probes (`check\exp_spell.py`): superscript, fullwidth, Arabic-Indic and other-script digits in size, rational, digest, commit, time, date and binary64 are refused. In `qro/` and `controls/` the only `\d` is in a comment. |
| P0-2, crash for refusal | holds except R2-2 | MEASURED: 25 inputs through `python -m qro` (`check\exp_cli.py`) stay inside the contract (1 refused, 2 misuse, 3 the checker's own failure). Round 1's fuzzers on the new tree (`check\fz\`): 126,475 byte-level mutants of the twin, 0 crashes, 0 second spellings. Custody edits behave as the stated limit says: all 368 last-line edits the log accepts are caught by a pinning record. |
| P0-3, stage registry | holds | MEASURED (`check\plant_registry2.py`): 17 of my 21 plants fail `tests/docs`. They include a commented-out stage, each tool's stage deleted, a stage pointed at a missing directory, a stray test directory, a stray `*_test.py`, and a new tool in `tools/`, `controls/` or `docs/studies/qro0/`. Of the four survivors, one was an invalid plant of mine (an `--ignore` of a path with no tests). Three are real limits (note 1). |
| P0-4, links, streams, case | holds; see notes | MEASURED (`check\exp_files2.py`): a junction to an outside directory at the crate's top, in `data/`, and in an unlisted directory; a junction to the crate's own `data/`; a junction to an empty directory. All are `file-link`. A directory named like a listed file, and `data/` renamed `Data/`: `file-missing`. A listed `data/notes.txt:hidden`: refused by the reader (but see R2-1). A file symlink could not be created here. |
| P0-5, path alphabet | code holds, test vacuous | R2-1. |
| P0-6, privacy gate | holds | MEASURED (`check\plant_privacy2.py`, 32 plants). All 26 that should be caught are caught: UTF-16 LE and BE, UTF-32 LE and BE and UTF-8 with a byte-order mark; non-ASCII and CJK file and directory names; a key after 5,000 bytes; a NUL at byte 5,000; hidden and deep files; CRLF; home paths with forward slashes, JSON-escaped, as `file://`, with a non-ASCII user name, and macOS style; an address; a CRN, Moth key, presigned URL, AWS key id and JWT. The six that pass are the docstring's stated limits (BOM-less UTF-16, a NUL in the first 4,096 bytes, an ignored file, `__pycache__`, a bare 44-character key, base64). A named key and a home path in a commit message are caught; an author's address is not read, as stated. The tool's own 32 controls catch each plant by its own alternative alone. |
| P0-7, CHECKED domains | holds except R2-3 | MEASURED: 230 pairs, none off its domain. |
| P0-8, wrong statements | one not fixed (R2-6) | CLAUDE.md's "~15 s" quick: MEASURED 15 s for 14 stages. "~75 s" full: MEASURED 63 s, fine as an approximation. `-h` now prints every option. `--list` marks a budget. The reader docstring order, `vocabulary.py`'s comment, `fixture.py`'s docstring and the README's `step-unbuilt` sentence agree with the code. The `check_privacy` docstring is true: `moth-key` and `presigned-url` exist. VALIDATION.md's early digests reproduce (MEASURED, `check\exp_digest_history2.py`). With the files under `records/` and no `description` or `encodingFormat`, the body digest is `93880b5c…`. Under `data/` it is `6b831632…`. The present twin is `ff3fe486…`. |

### 4.2 N1, the unwatched checks

MEASURED. Every mutant ran against all six pytest directories the runner runs (295 tests). A survivor is one that left them all green. There are three operators.

**Operator A, a check made never to fire** (round 1's definition, `check\mut_r2.py`).

| count | round 1 | now |
|---|---|---|
| sites by round 1's definition | 69, of which 34 survived | 73, of which 7 survive |
| sites with `return f"…"` problems also counted | not counted | 77, of which 10 survive: reader 5 of 32, checker 1 of 16, custody 0 of 8, spelling 4 of 21 |

The same 7 survive with only round 1's four directories. The 10 survivors:

| mutant | verdict | argument or evidence |
|---|---|---|
| `reader.py:160`, descriptor and root first | equivalent | The descriptor must equal a fixed dict. Six required root terms have the root `./` as their only domain, so no other entity second can pass. MEASURED (`check\corpus_verdicts.py`): 3,224 structural documents, verdicts identical to the original's. |
| `reader.py:228`, single-valued term is a list | equivalent | `spelling.problem` refuses a list for every single-valued spelling, with the same name. 3,224 documents identical. |
| `reader.py:169`, root is a Dataset | accept and refuse equivalent; name differs | 0 of 3,224 newly accepted. 21 get `term-unknown` in place of `graph-form` (a root typed `Person`). A trivial gap. |
| `reader.py:146`, `:148`; `spelling.py:154`, `:156`, `:158` | real gap | R2-1. The `:146` mutant accepted 4 more of the 3,224 documents. |
| `checker.py:71`, neither file nor directory | real gap, not plantable here | No plant anywhere makes a FIFO or a socket. The link plants hit the earlier check. |
| `spelling.py:105`, `binary64` regex fails | real gap, harmless today | No term uses `binary64`, and both refused examples match the regex. The mutant would turn a refusal into an `AttributeError`. |

**Operator B, a refusal's name swapped** (`check\mut_names.py`, 61 sites in `reader.py`, `checker.py` and `custody.py`). 59 killed, 2 survive: `reader.py:149` (R2-1) and `checker.py:72` (as `:71`).

**Operator C, 67 hand mutants of the canonical rules and the spellings** (`check\mut_canon_r2.py`). 44 killed, 23 survive.

- Round 1's 18 canonical mutants plus the vocabulary pin: 18 killed, 1 survives. Round 1's six survivors are now five killed (unsorted keys, `ensure_ascii=False`, indent 4, `", "` separators, the reversed digest) and `allow_nan=True`.
- `allow_nan=True` is equivalent for everything the reader and checker see, as the lead says: the reader refuses every non-integer number either way. It would change only the writer's error on a NaN, from `ValueError` to `Refused`.
- The other 22 survivors are of my own making:
  - Equivalent (3): `compact`'s `allow_nan=True`; `size` allowing 20 digits (any 20-digit number exceeds 2^63 - 1 and is refused by the next test); `os.walk(followlinks=True)` (the link check on the parent's entries raises before any descent).
  - Host-limited (1): `_is_link` ignoring symlinks. The Windows plant is a junction. A POSIX run would kill it (BELIEVED).
  - Real gaps (18), each a missing test because the original refuses or normalises the input (MEASURED, `check\exp_gaps_real.py`):
    - the path alphabet and device rules (11, R2-1);
    - `absolute()` (1, R2-1);
    - `text` allowing CR, VT and FF (R2-5);
    - `_ID` allowing DEL;
    - `iri` allowing a space;
    - `contentSize` wrong with a right digest, which no plant makes;
    - `stages` repeating a value in an audit record;
    - the writer turning a one-element type list into a string.

**Golden bytes.** MEASURED: the six files under `tests/format/golden/` re-derive with `hashlib` and `json` alone, with no `qro` import. The body, the identity `ff3fe486…`, the three-line chain and its head all match. The em dash is stored as `\u2014`. All six files are LF.

### 4.3 N2 to N8

- **N2, registry against the study.** Holds as stated. MEASURED (`check\plant_registry_n2.py`, 8 plants): six are caught by `tests/controls` (a changed fault text, a changed expected cell, a changed section-13 owner, swapped rows, a deleted row, a changed study cell). An owner changed on a row section 13 does not name is caught only by `gen_vocabulary --check`, which `--write` heals; that is the "where it names them" limit. A pending row's structured `expected` and `refusal` are tied to nothing until its parcel builds it.
- **N3.** `COUNTS` exists and is run. `controls.run` runs two kinds of plant. Deleting a P0 plant makes `python -m controls.run` print `WRONG shot-moved … with no plant` and exit 1 (MEASURED). The PRC-terms half of the claim is R2-7.
- **N4.** Holds. FORMAT.md item 18 lists the log, `prev`, head and record choices, and each matches `qro/custody.py` and the golden bytes.
- **N5.** Holds as stated. MEASURED (`check\plant_n5.py`): five of six spellings of a bogus refusal name are caught by `tests/vocabulary` (one line, four lines, a conditional, a variable, `module.Refused`). An aliased constructor (`R = Refused`) is not seen by the static scan. The runtime `KeyError` would catch it only when that line runs.
- **N6.** Present, but the "exercised" test is a search for the quoted term name in any test file.
- **N7.** The examples are walked both ways, not branch by branch. `binary64`'s regex branch, `text`'s C1 range, `iri`'s space and `_ID`'s DEL have no refused example.
- **N8.** Holds for a case-renamed file and directory (`file-missing`) and for a stream name (`spelling`). The last is R2-1.

### 4.4 The review copies

See R2-8. MEASURED against the 14 true originals: nothing else changed. Each copy equals its original after (a) the placeholders, (b) CRLF to LF and (c) the removed envelope. I printed no source text that could be a home path.

### 4.5 The study's edits since its approval

- MEASURED (`diff` of `docs/studies/QRO-0.md` against `draft6\QRO-0.pre-amend.md`, whose SHA-256 begins `f8a983e9…`, the digest the study names): 23 hunks.
- Every hunk is covered by section 17:
  - the header and the "Next/Then" lines, which are the approval;
  - section 13's "It did: its re-check found it READY";
  - section 14's "confirmed by the approval" and "Open until the approval";
  - the question 10 lines with Logan's "A link is fine";
  - the draft 12 re-check's counts (N8);
  - section 4.1's READ against inferred (N7);
  - the gate and plants descriptions (N1 to N6) and the two changed instrument hashes;
  - section 15's sentence on where the reports are, with draft 12's re-check added to the list;
  - the `counts` word (N9);
  - section 17's new paragraphs: the approval, the amendment table, the lead's checks, the instruments, "Later the same day", the placeholder correction, and the providers' terms.
- MEASURED: the two hashes in section 15 match the files (`check_study.py` `660d7890…`, `check_study_plants.py` `282ddee1…`).
- MEASURED: the placeholder figures in section 17 match a run. `check_study_plants.py` prints "68 faults refused with the failure each targets, 6 right variants accepted, 0 unplaced, 0 wrong". `check_study.py` prints ACCEPTED.
- Section 17's figures from the draft 12 re-check (55 copies and 38 caught; 165 files and 156 of 164 changed without the attribute) match `docs/reviews/QRO-0/draft12-recheck.md`.
- Four edits are consequences of the approval and are not itemised in the amendment table (note 12).

### 4.6 The provider notice and the records

- **NOTICE.md against `terms-check-report.md`.**
  - Every document, version and date matches (Z126-6304 v13, Z126-6548 v13, Z126-6560 v09, i126-6605 v29, i126-9425 v10).
  - "Which of the two governs … was not determined" matches the report.
  - The four findings (inputs are Content; no clause limits publishing; no clause allocates outputs; none licenses IBM's data) match.
  - The Moth section matches: no terms found, the places searched, the sign-up terms not read.
  - LICENSE-docs.md follows the report's replacement text, and drops "circuits and measurements Logan holds rights in", a conservative cut.
- **The records.** MEASURED by key names and shapes (`check\agg_records.py`, `shape.py`, `records_check.py`):
  - There are 65 job records, all with one key set. There are 7 `properties-*.json` (fez 2, kingston 3, marrakesh 2), and the job counts per snapshot stamp equal the README's table.
  - Job records hold the backend, times, job and program ids, status, usage and options, `ibm_params_keys` (four names only), and Logan's `holds`, `calibration` and `fetched_at`. No circuit appears.
  - The omitted-key lists name `user_id`, `cost`, `estimated_running_time_seconds` and `circuits_execution_time_ns`. No value of any is present.
  - The probes hold the plan, pricing, backends and usage figures, with `instance_id` and `plan_id` as names only.
  - ibm-results-refetch holds digests, sizes, role, device and a relative path into Quantum-Film.
  - Both MANIFEST.json files list every other file with a right SHA-256 and size.
  - All README and tool hash prefixes match, except the dry-run tool's. The README says it changed later, and its current prefix is `6ca8b5ae`.
  - The logs are as described: three are CRLF. `ibm-dryrun-probe-2.log` is LF with three 404 bodies whose trace ids read `<redacted: IBM request trace id>`.
  - CLAUDE.md's "three records logs CRLF, everything else LF" is exact: exactly 8 CRLF files, none mixed.
- **Not described.**
  - Each of the 65 job records carries `ibm_metrics.usage.details[].metric.id`, a UUID, the same in all 65.
  - NOTICE.md and the records README describe "usage figures" and say the usage's instance and plan ids were left out. Neither says this identifier is kept.
  - The terms agent saw the same value and did not repeat it (its report, section 5).
  - I found nothing described wrongly.

### 4.7 The open question: what does the usage-metric id identify?

**UNKNOWN for the last step. The documentation points away from an account or instance id.**

- **READ.**
  - IBM's Qiskit Runtime REST documentation (Jobs, "Get job metrics") calls `usage.details[].metric.id` the identifier of the metric definition from which the usage was calculated, format uuid. It says each detail is one billable metric, with `metric.value` in seconds and `value` in resource units.
  - It does not say whether that definition belongs to an account, an instance or a plan.
  - `qiskit-ibm-runtime` 0.50.0's source says nothing. `RuntimeJobV2.metrics()` returns the server's JSON for `GET /jobs/{id}/metrics` untouched.
  - The strings `details`, `metric`, `resource_units`, `plan_id` and `instance_id` occur nowhere in the package. `usage()` is the account call that returns `instance_id` and `plan_id`.
- **MEASURED** (`check\metric_id_local.py`, which read the id into memory and never printed it).
  - It is a version-5 (name-based) UUID, and the same in all 65 records across three devices.
  - The same value is in 65 tracked files in Quantum-Film's records (`docs/records/2026-10-05/ibm/…/*-metrics.json`), committed 2026-10-05. Those files also hold `cost`, `estimated_running_time_seconds` and `circuits_execution_time_ns`, which NOTICE.md says QRO-Crate left out.
  - The terms report says Quantum-Film is public.
- **BELIEVED.** A name-based id, shared across devices and called a "definition", is more likely an id for the metric's definition on the plan than for the account. The documents do not rule out a definition scoped to one instance, so I cannot call it settled.
- **Recommendation.** NOTICE.md should list the id as kept and say what IBM's documentation calls it.
- **Sent out.** The id never left this machine. No search or fetch contained it.

## 5. Notes (below the bar of a defect)

1. **Registry limits.** MEASURED: `tests/docs` misses a tool written with a single-quoted `__main__` guard and `'--check'`. It cannot tell the `twin` stage from the negative control (both run `-m controls.plant`), so the twin stage can be deleted unnoticed. A stage ending `|| true` passes. Reading source text is the stated approach, but the quote spelling is not stated.
2. **Descriptor case alias.** MEASURED, reader alone: a File named `Ro-Crate-Metadata.json` beside the descriptor is not refused as a case alias, because the case rule looks at Files only. On this host the checker then refuses it `file-missing`. BELIEVED: a case-sensitive host would accept it. FORMAT.md item 11 says two files whose names differ only by case are refused.
3. **Invisible or ignored on disk.** MEASURED: an unlisted NTFS stream on a listed file, a hard link to a file outside the crate (held by its digest), and an empty directory are all accepted.
4. **Device names.** BELIEVED, not re-read: Microsoft's list also names `COM0`, `LPT0`, `CONIN$` and `CONOUT$`, and the rule accepts them. MEASURED: on this Windows 11 host `CON`, `AUX`, `COM1` and `LPT1` are ordinary files, and only `NUL` is special. A path segment of any length is accepted (`data/` plus 300 characters), though NTFS holds 255.
5. **`named:token` in the privacy gate.** MEASURED (`check\exp_token_names.py`): `token=…` is caught, but `access_token=`, `refresh_token=`, `id_token=`, `auth_token=`, `ibm_token=`, `IBM_TOKEN=` and `bearer_token=` pass. `\btoken` needs a boundary, and `_` is a word character. This is within the docstring's limit and probably unintended.
6. **NOTICE.md.**
   - It omits the report's list of use limits that do exist: research and development only, and exclusive use. These bear on the custody pilot.
   - The acknowledgement's second sentence is the lead's wording. The report advised copying IBM's own.
   - The trademark sentence, and "Qiskit" in it, is not from the report (BELIEVED consistent with IBM's page).
7. **REFUSALS.md.** The `graph-form` row lists some causes. It leaves out a term off its domain, a dangling reference, a case collision, a missing required root term, and a raw result that is not a held File.
8. **"51 plants".** VALIDATION.md's figure is the number of tests collected in `test_sites.py`. 29 of them come from the reader table, and a few are not plants.
9. **Where a spelling is written.** CLAUDE.md says `qro/vocabulary.py` is the one place. The file `@id` rule and the id rule are in `qro/spelling.py` and FORMAT.md only. The generated vocabulary page does not carry them.
10. **Time.** A leap second (`:60`) is refused, though the spelling says RFC 3339.
11. **Parcels' failures.** A bug in a parcel's generator or raw-form reader is reported as the crate being refused (`metadata-generated`, `raw-form`), by design (FORMAT.md item 16). CLAUDE.md says a crash is never a verdict, so a parcel's bug will look like a refused crate.
12. **Study status text.** Four approval-status edits (the header's status and "Then" lines, section 13's "It did", section 14's headings) are not itemised in the amendment table. The approval paragraph covers them.
13. **Custody.** The stated limits are true. A future-dated `at` is also accepted, which the docstring does not list.

## 6. What I did not do

- **No Linux or macOS run.** The only Linux here is a WSL Ubuntu with Python 3.10, outside `requires-python`, and I may write only under my own directory. I asked it for version numbers only. POSIX symlinks, FIFOs and case-sensitive behaviour are BELIEVED, not measured.
- **No IBM or Atlas contact; no qiskit import; nothing submitted.** I read `qiskit_ibm_runtime` as text under the qf-ibm virtualenv and opened no configuration or credential file. I fetched IBM's public API documentation with no identifier in any query. I did not re-read IBM's terms: NOTICE.md is checked against the terms report only.
- **My search for the metric id** read the bytes of every file under moth-quantum outside `.atlas`, `.git`, `.claude`, `.gate-state`, `.ruff_cache`, `node_modules` and `__pycache__`. It printed only file names. A names-only listing afterwards (`check\credname_scan.py`) shows one file in that tree with a credential-like name, an Arduino example header.
- **I did not open** `~/.quantum-film`, any `.atlas` directory, or any key, token or CRN. The key-shaped strings in my scripts are made up.
- **Slip.** One IBM job id appeared in my own tool output, once, as part of a truncated file name. It is not in this report. Every later print masked ids.
- **No `rocrate-validator` or JSON-LD processor.** No performance test on a 13,000-file crate.
- **No review of P1 to P5**, which do not exist yet.
- **The study's own figures** beyond its two gates, and the five instruments through the runner, are not re-derived.
- **The mutation test** has three operators over reader, checker, custody, canonical and spelling. It does not cover `controls/`, `tools/` or `qro/__main__.py` by mutation; I probed those by hand.
- **My own script errors.** My first mutation run aborted on `spelling.py` because of a non-ASCII comment. Two of my hand-mutant patterns first matched a docstring and a regex string wrongly. I fixed both and reran, and the totals above are from the clean reruns.
- **No one was contacted, and no banner accepted.** I edited nothing in `frozen\` or in the real repository.

A scoped re-check after the fixes should cover R2-1 to R2-9 and the survivors in section 4.2. I will pick my own faults.
